from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.common.config import get_settings


class Base(DeclarativeBase):
    """Shared SQLAlchemy declarative base for all feature models."""


@lru_cache
def get_session_factory():
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    return async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    """Provide one async database session per request and close it after use."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session
