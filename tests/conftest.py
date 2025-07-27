"""Pytest configuration and shared fixtures."""

import os
import subprocess
import time
from collections.abc import Generator

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError

from src.core.config import get_database_url


def wait_for_postgres(engine: Engine, max_retries: int = 30) -> None:
    """Wait for PostgreSQL to be ready."""
    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                return
        except OperationalError:
            if i == max_retries - 1:
                raise
            time.sleep(2)


@pytest.fixture(scope="session")
def ensure_database_ready() -> Generator[None]:
    """Ensure database container is running before any tests.

    This runs once per test session (before ALL tests).
    """
    # Check if we're in CI or if postgres is already running
    if os.environ.get("CI") or os.environ.get("SKIP_DB_SETUP"):
        yield
        return

    # Check if postgres is already healthy
    try:
        url = get_database_url("test")
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
    except OperationalError:
        # Database not ready, will start it
        pass
    else:
        # Already running
        yield
        return

    # Start postgres if needed
    subprocess.run(["docker-compose", "up", "-d", "postgres"], check=True)  # noqa: S607

    # Wait for health
    max_wait = 60
    start_time = time.time()

    while time.time() - start_time < max_wait:
        result = subprocess.run(
            ["docker-compose", "ps", "postgres"],  # noqa: S607
            check=False,
            capture_output=True,
            text=True,
        )
        if "healthy" in result.stdout:
            # PostgreSQL is ready
            break
        time.sleep(2)
    else:
        msg = "PostgreSQL did not become healthy in time"
        raise TimeoutError(msg)

    yield

    # Cleanup handled elsewhere


@pytest.fixture(scope="session")
def db_engine_session(ensure_database_ready: None) -> Generator[Engine]:  # noqa: ARG001
    """Create a session-scoped database engine.

    This engine is shared across all tests in the session.
    """
    url = get_database_url("test")
    engine = create_engine(url, pool_pre_ping=True)

    # Ensure connection works
    wait_for_postgres(engine)

    yield engine
    engine.dispose()


# Make session engine available at module scope too
@pytest.fixture(scope="module")
def db_engine(db_engine_session: Engine) -> Engine:
    """Module-scoped database engine (reuses session engine)."""
    return db_engine_session
