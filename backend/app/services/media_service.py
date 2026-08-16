"""Media (upload/delete) service."""

from __future__ import annotations

import os
from pathlib import Path

from app.config import settings
from app.core.file_storage import (
    MAX_FILE_SIZE,
    UPLOAD_DIR,
    delete_uploaded,
    save_uploaded,
    validate_file,
)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class MediaError(Exception):
    """Raised on media handling failures."""


async def handle_upload(filename: str, raw: bytes) -> dict:
    """Validate, persist and return metadata for an uploaded file.

    Returns a dict with ``file_url``, ``file_name``, ``mime_type``, ``size``.
    Raises :class:`MediaError` on validation failure.
    """
    try:
        mime = validate_file(raw, filename)
        relative_url = save_uploaded(raw, filename)
        return {
            "file_url": relative_url,
            "file_name": filename,
            "mime_type": mime,
            "size": len(raw),
        }
    except (ValueError, OSError) as exc:
        raise MediaError(str(exc)) from exc


async def get_upload(relative_url: str) -> tuple[bytes, str] | None:
    """Read a stored upload; returns ``(content, mime)`` or ``None``."""
    from app.core.file_storage import read_uploaded

    return read_uploaded(relative_url)


async def remove_upload(relative_url: str) -> bool:
    """Delete a stored upload; returns ``True`` if it existed."""
    return delete_uploaded(relative_url)


def parse_filename(relative_url: str) -> str:
    """Return the basename from a relative upload URL."""
    return Path(relative_url).name