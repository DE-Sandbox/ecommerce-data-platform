"""Shared fixtures for model tests."""

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import get_database_url


@pytest_asyncio.fixture
async def async_engine():
    """Create async engine for testing."""
    url = get_database_url("test", async_driver=True)
    engine = create_async_engine(url, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine):
    """Create async session for testing."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session_maker() as session:
        # Start a transaction
        async with session.begin():
            yield session
            # Rollback the transaction after each test
            await session.rollback()
