"""Authentication router — registration, login, refresh, logout, me."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
)
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthTokens,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    UpdateProfileRequest,
    UserOut,
)
from app.schemas.response import error, success
from app.services.auth_service import (
    ERR_CONFLICT,
    ERR_FORBIDDEN,
    ERR_NOT_FOUND,
    ERR_UNAUTHORIZED,
    ERR_VALIDATION,
    authenticate,
    register_user,
    verify_refresh_token,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new user account."""
    try:
        user = await register_user(db, payload.email, payload.username, payload.password)
    except ValueError as exc:
        return error(ERR_CONFLICT, str(exc))
    except Exception as exc:
        return error(500, f"registration failed: {exc}")

    tokens = {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }
    return success(
        {"user": UserOut.model_validate(user).model_dump(), **tokens},
        "registered",
    )


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate a user and return JWTs."""
    user = await authenticate(db, payload.email_or_username, payload.password)
    if user is None:
        return error(ERR_UNAUTHORIZED, "invalid credentials")
    tokens = {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }
    return success(
        {"user": UserOut.model_validate(user).model_dump(), **tokens},
        "logged in",
    )


@router.post("/refresh")
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a new access token."""
    user = await verify_refresh_token(db, payload.refresh_token)
    if user is None:
        return error(ERR_UNAUTHORIZED, "invalid refresh token")
    return success(
        {
            "access_token": create_access_token(user.id),
            "token_type": "bearer",
        },
        "token refreshed",
    )


@router.post("/logout")
async def logout(authorization: Annotated[str | None, Header()] = None):
    """Invalidate the current session.

    Tokens are stateless JWTs; logout is advisory — clients should discard
    their tokens after this call.
    """
    return success(None, "logged out")


def _extract_user_id(authorization: str) -> str | None:
    """Parse a bearer token and return the subject id, or None."""
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer" or not token:
            return None
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        return payload.get("sub")
    except Exception:
        return None


async def _current_user_id(authorization: Annotated[str | None, Header()] = None) -> str:
    """FastAPI dependency: authenticated user id."""
    if not authorization:
        raise HTTPException(status_code=401, detail="missing authorization")
    uid = _extract_user_id(authorization)
    if uid is None:
        raise HTTPException(status_code=401, detail="invalid token")
    return uid


@router.get("/me")
async def me(
    user_id: Annotated[str, Depends(_current_user_id)],
    db: AsyncSession = Depends(get_db),
):
    """Return the currently authenticated user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        return error(ERR_NOT_FOUND, "user not found")
    return success(UserOut.model_validate(user).model_dump(), "ok")


@router.put("/me")
async def update_me(
    payload: UpdateProfileRequest,
    user_id: Annotated[str, Depends(_current_user_id)],
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's profile."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        return error(ERR_NOT_FOUND, "user not found")

    try:
        if payload.username is not None:
            existing = await db.execute(
                select(User).where(User.username == payload.username, User.id != user_id)
            )
            if existing.scalar_one_or_none() is not None:
                return error(ERR_CONFLICT, "username already exists")
            user.username = payload.username
        if payload.email is not None:
            existing = await db.execute(
                select(User).where(User.email == payload.email, User.id != user_id)
            )
            if existing.scalar_one_or_none() is not None:
                return error(ERR_CONFLICT, "email already exists")
            user.email = payload.email
        if payload.avatar_url is not None:
            user.avatar_url = payload.avatar_url
        if payload.password is not None:
            user.password_hash = hash_password(payload.password)
    except Exception as exc:
        return error(ERR_VALIDATION, str(exc))

    await db.flush()
    await db.refresh(user)
    return success(UserOut.model_validate(user).model_dump(), "profile updated")