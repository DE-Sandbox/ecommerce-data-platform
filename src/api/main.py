"""Main FastAPI application factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware import (
    APIVersionMiddleware,
    LoggingMiddleware,
    RequestIDMiddleware,
)
from src.api.v1.routers import health
from src.events import ensure_schemas_registered


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan events."""
    # Startup
    ensure_schemas_registered()

    yield

    # Shutdown


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="E-commerce Data Platform API",
        version="1.0.0",
        description="REST API for e-commerce data platform with synthetic data generation",
        lifespan=lifespan,
    )

    # Add middleware in reverse order (last added is first executed)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(
        APIVersionMiddleware,
        supported_versions=["1.0", "1.1"],
    )
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router)

    return app
