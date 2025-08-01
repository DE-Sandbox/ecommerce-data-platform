"""Shared fixtures for model tests."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import get_database_url
from src.models.base import Base


@pytest_asyncio.fixture
async def async_engine() -> AsyncGenerator[AsyncEngine]:
    """Create async engine for testing."""
    url = get_database_url("test", async_driver=True)
    engine = create_async_engine(url, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    """Create async session for testing."""
    # Create tables if they don't exist

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create a session for the test
    async with async_session_maker() as session:
        yield session
