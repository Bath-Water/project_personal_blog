"""Security helpers — password hashing, JWT creation/verification."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings

ALGORITHM = settings.algorithm
SECRET_KEY = settings.secret_key


def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return ``True`` when *plain* matches the stored hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(subject: str, *, expires_delta: int | None = None) -> str:
    """Encode an access JWT with the given *subject* (e.g. user id)."""
    expire = datetime.now(timezone.utc) + timedelta(
        seconds=expires_delta or settings.access_expire_delta
    )
    payload = {"sub": subject, "type": "access", "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(subject: str, *, expires_delta: int | None = None) -> str:
    """Encode a long-lived refresh JWT."""
    expire = datetime.now(timezone.utc) + timedelta(
        seconds=expires_delta or settings.refresh_expire_delta
    )
    payload = {"sub": subject, "type": "refresh", "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT, returning its payload.

    Raises ``JWTError`` if the token is invalid or expired.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])