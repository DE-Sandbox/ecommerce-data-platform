"""Shared API dependencies."""

from collections.abc import AsyncGenerator

import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import get_settings

# Get settings
settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.debug,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_health() -> bool:
    """Check database health."""
    try:
        # Try to connect directly with asyncpg for a simple health check
        conn = await asyncpg.connect(settings.database_url)
        await conn.fetchval("SELECT 1")
        await conn.close()
    except (asyncpg.PostgresError, OSError):
        return False
    else:
        return True
