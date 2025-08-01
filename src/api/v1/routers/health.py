"""Health check endpoints."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.api.dependencies import get_db_health

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response."""

    status: str


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    status: str
    timestamp: datetime
    checks: dict[str, bool]


@router.get("/health")
async def health_check() -> HealthResponse:
    """Check service health."""
    return HealthResponse(status="healthy")


@router.get("/ready")
async def readiness_check(
    db_healthy: Annotated[bool, Depends(get_db_health)],
) -> ReadinessResponse:
    """Check service readiness with dependency health."""
    checks = {
        "database": db_healthy,
    }

    return ReadinessResponse(
        status="ready" if all(checks.values()) else "not ready",
        timestamp=datetime.now(UTC),
        checks=checks,
    )
