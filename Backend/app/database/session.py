"""
app/database/session.py
───────────────────────
Async SQLAlchemy engine, session factory, and pgvector registration.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

_settings = get_settings()

engine: AsyncEngine = create_async_engine(
    _settings.database_url_str,
    pool_size=_settings.DATABASE_POOL_SIZE,
    max_overflow=_settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=_settings.APP_DEBUG,
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


async def create_all_tables() -> None:
    """Create all tables (used in tests / dev; prod uses Alembic)."""
    async with engine.begin() as conn:
        # Register pgvector type
        await conn.execute(__import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
