"""
SQLAlchemy async engine, session factory, and declarative Base.
"""
from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ── Declarative base ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


# ── Helpers ───────────────────────────────────────────────────────────────────

async def init_db() -> None:
    """
    Create all tables that don't yet exist.
    Intended for development; production should use Alembic migrations.
    """
    async with engine.begin() as conn:
        # Import all models so Base.metadata is populated
        import app.models  # noqa: F401, PLC0415

        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialised successfully.")


async def close_db() -> None:
    """Dispose the engine connection pool on shutdown."""
    await engine.dispose()
    logger.info("Database engine disposed.")
