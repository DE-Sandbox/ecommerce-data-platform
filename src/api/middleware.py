"""API middleware components."""

import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = structlog.get_logger()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to all requests."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Add request ID to request context and response headers."""
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Add to request state
        request.state.request_id = request_id

        # Add to correlation ID for responses
        request.state.correlation_id = request_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = request_id

        return response


class APIVersionMiddleware(BaseHTTPMiddleware):
    """Middleware to handle API versioning via headers."""

    def __init__(self, app: ASGIApp, supported_versions: list[str]) -> None:
        """Initialize with supported versions."""
        super().__init__(app)
        self.supported_versions = supported_versions

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Check API version header."""
        api_version = request.headers.get("X-API-Version")

        if api_version:
            if api_version not in self.supported_versions:
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": f"Unsupported API version: {api_version}. Supported versions: {', '.join(self.supported_versions)}"
                    },
                )
            request.state.api_version = api_version

        return await call_next(request)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Log request details and response status."""
        start_time = time.time()

        # Get request ID from state if available
        request_id = getattr(request.state, "request_id", None)

        # Log request start
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query_params=str(request.url.query),
            request_id=request_id,
        )

        try:
            response = await call_next(request)
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            logger.exception(
                "Request failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_ms=round(duration_ms, 2),
                request_id=request_id,
            )

            # Re-raise to let FastAPI handle the error
            raise
        else:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                request_id=request_id,
            )

            return response
