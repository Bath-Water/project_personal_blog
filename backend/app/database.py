"""Database engine, session factory and async helper."""

from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Ensure the data directory exists so SQLite can create the file.
Path(settings.db_dir).mkdir(parents=True, exist_ok=True)
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

_engine = create_async_engine(settings.db_url, echo=settings.debug, future=True)
_async_session_factory = async_sessionmaker(
    _engine, class_=AsyncSession, expire_on_commit=False, future=True
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for dependency injection."""
    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_engine() -> None:
    """Dispose the underlying engine (used on shutdown)."""
    await _engine.dispose()


async def init_db() -> None:
    """Create all ORM-managed tables (if not already present)."""
    from app.models import Base  # local import avoids circular deps

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)