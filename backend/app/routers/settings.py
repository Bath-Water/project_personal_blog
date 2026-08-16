"""Settings router — get and update site-wide settings."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.setting import Setting
from app.models.user import User
from app.schemas.response import error, success
from app.schemas.setting import SettingsOut, SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["Settings"])

_SETTING_ID = "1"


@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)):
    """Return the current site settings (or defaults)."""
    row = await _ensure_default(db)
    return success(SettingsOut.model_validate(row).model_dump(), "ok")


@router.put("")
async def update_settings(
    payload: SettingsUpdate,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Update site settings (authenticated)."""
    row = await _ensure_default(db)
    data = payload.model_dump(exclude_unset=True)
    try:
        for k, v in data.items():
            setattr(row, k, v)
        await db.flush()
        await db.refresh(row)
    except Exception as exc:
        return error(500, f"failed to update settings: {exc}")
    return success(SettingsOut.model_validate(row).model_dump(), "updated")


async def _ensure_default(db: AsyncSession) -> Setting:
    """Return the setting row, creating a default row if absent."""
    result = await db.execute(select(Setting).where(Setting.id == _SETTING_ID))
    row = result.scalar_one_or_none()
    if row is None:
        row = Setting(
            id=_SETTING_ID,
            blog_name="My Blog",
            blog_description="",
            comment_enabled=True,
            comment_need_approval=False,
            nav_items=[],
            social_links=[],
        )
        db.add(row)
        await db.flush()
    return row