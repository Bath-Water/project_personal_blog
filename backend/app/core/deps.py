"""Reusable auth FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database import get_db
from app.models.user import User


def _extract_token(authorization: str | None) -> str | None:
    """Parse ``Authorization: Bearer <token>`` and return the token."""
    if not authorization:
        return None
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer" or not token:
            return None
        return token
    except ValueError:
        return None


async def _get_current_user_id(authorization: Annotated[str | None, Header()] = None) -> str:
    """Return the authenticated user id (or raise 401)."""
    token = _extract_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="missing bearer token")
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="invalid token type")
    return payload.get("sub", "")


async def _get_current_user(
    user_id: Annotated[str, Depends(_get_current_user_id)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """Return the authenticated :class:`User` (or raise 401)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="user not found")
    return user


# Export as dependency aliases for convenience in routers.
get_current_user_id = _get_current_user_id
get_current_user = _get_current_user