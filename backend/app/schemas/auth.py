"""Auth-related schemas."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from app.config import settings


_MIN_LEN = settings.min_password_length


class RegisterRequest(BaseModel):
    """Payload for user registration."""

    username: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=_MIN_LEN)

    @field_validator("email")
    @classmethod
    def _email_format(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("invalid email address")
        return v

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        if len(v) < _MIN_LEN:
            raise ValueError(f"password must be at least {_MIN_LEN} chars")
        if not re.search(r"[A-Z]", v):
            raise ValueError("password must contain an uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("password must contain a lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("password must contain a digit")
        return v


class LoginRequest(BaseModel):
    """Payload for user login."""

    email_or_username: str = Field(..., min_length=1, max_length=255)
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    """Public user shape."""

    id: str
    email: str
    username: str
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    """Payload for ``PUT /api/auth/me``."""

    username: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, min_length=3, max_length=255)
    avatar_url: Optional[str] = None
    password: Optional[str] = None  # optional password reset

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) < _MIN_LEN:
            raise ValueError(f"password must be at least {_MIN_LEN} chars")
        if not re.search(r"[A-Z]", v):
            raise ValueError("password must contain an uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("password must contain a lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("password must contain a digit")
        return v