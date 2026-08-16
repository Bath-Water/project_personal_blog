"""Shared response wrappers and helpers."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class APIResponse(BaseModel):
    """Standard API response envelope."""

    code: int = 0
    data: Optional[Any] = None
    message: str = ""


class ErrorResponse(BaseModel):
    """Error variant of :class:`APIResponse`."""

    code: int
    data: None = None
    message: str


def success(data: Any = None, message: str = "ok") -> dict:
    """Return a success envelope dict."""
    return {"code": 0, "data": data, "message": message}


def error(code: int, message: str) -> dict:
    """Return an error envelope dict."""
    return {"code": code, "data": None, "message": message}