"""Authentication service — user creation, token management."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User

# ---------- public error codes --------------------------------------------
ERR_VALIDATION = 400
ERR_UNAUTHORIZED = 401
ERR_FORBIDDEN = 403
ERR_NOT_FOUND = 404
ERR_CONFLICT = 409
ERR_INTERNAL = 500


async def register_user(
    db: AsyncSession,
    email: str,
    username: str,
    password: str,
) -> User:
    """Create a new user and return the persisted :class:`User`."""
    try:
        existing = await _find_by_email_or_username(db, email, username)
        if existing:
            raise ValueError(
                "email or username already exists" if "@" in (email or "")
                else "username already exists"
            )
        user = User(
            email=email,
            username=username,
            password_hash=hash_password(password),
            remember_token=uuid.uuid4().hex,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(f"registration failed: {exc}") from exc


async def authenticate(
    db: AsyncSession,
    email_or_username: str,
    password: str,
) -> User | None:
    """Return the :class:`User` if credentials match, else ``None``."""
    stmt = (
        select(User)
        .where(User.is_active.is_(True))
        .where(
            (User.email == email_or_username) | (User.username == email_or_username)
        )
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def issue_tokens(user: User) -> dict:
    """Create access + refresh JWTs for *user*."""
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
    }


async def verify_refresh_token(db: AsyncSession, token: str) -> User | None:
    """Decode a refresh token and return the user if valid."""
    try:
        payload = decode_token(token)
    except Exception:
        return None
    if payload.get("type") != "refresh":
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


def current_user_from_token(token: str) -> dict:
    """Decode an access JWT and return its payload (raises on failure)."""
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise ValueError("invalid token type")
    return payload


async def _find_by_email_or_username(
    db: AsyncSession, email: str | None, username: str | None
) -> User | None:
    """Return a user matching either identifier, if any."""
    result = await db.execute(
        select(User).where(
            (User.email == email) | (User.username == username)
        )
    )
    return result.scalar_one_or_none()