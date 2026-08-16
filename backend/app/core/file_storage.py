"""File storage helpers — upload, delete, magic-byte validation."""

from __future__ import annotations

import hashlib
import io
import os
import re
import shutil
import uuid
from pathlib import Path

from PIL import Image

from app.config import settings

UPLOAD_DIR = Path(settings.upload_dir).resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Magic bytes for common image types.
IMAGE_MAGIC: dict[tuple[bytes, ...], str] = {
    (b"\xff\xd8\xff",): "image/jpeg",
    (b"\x89PNG\r\n\x1a\n",): "image/png",
    (b"GIF87a", b"GIF89a"): "image/gif",
    (b"RIFF",): "image/webp",  # RIFF ... WEBP
    (b"\x00\x00\x01\x00",): "image/x-icon",
}

# Maximum file size: 20 MB
MAX_FILE_SIZE = 20 * 1024 * 1024


def _detect_mime(raw: bytes) -> str | None:
    """Return an image MIME type if *raw* looks like an image, else ``None``."""
    for sig, mime in IMAGE_MAGIC.items():
        if raw.startswith(sig):
            # RIFF needs further check for WEBP
            if mime == "image/webp":
                if raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
                    return mime
                return None
            return mime
    # Also try PIL as a fallback for odd images.
    try:
        img = Image.open(io.BytesIO(raw))
        img.verify()
        fmt = img.format
        if fmt:
            return f"image/{fmt.lower()}"
    except Exception:
        return None
    return None


def validate_file(raw: bytes, filename: str) -> str:
    """Validate uploaded bytes: size + magic bytes.

    Returns the resolved MIME type on success; raises ``ValueError`` otherwise.
    """
    if len(raw) > MAX_FILE_SIZE:
        raise ValueError("File too large (max 20MB)")
    if len(raw) == 0:
        raise ValueError("Empty file")

    # MIME sniff via magic bytes first
    mime = _detect_mime(raw)
    if not mime:
        # Fallback: trust extension for common text-like uploads only if it looks
        # like an image extension.
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        allowed_ext = {"jpg", "jpeg", "png", "gif", "webp", "svg", "ico"}
        if ext in allowed_ext:
            return f"image/{ext}"
        raise ValueError(f"Unsupported file type: {filename}")
    return mime


def save_uploaded(raw: bytes, original_name: str) -> str:
    """Persist *raw* with a UUID filename, return the relative URL path.

    Example returned value: ``/uploads/a1b2c3.jpg``
    """
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    new_name = f"{uuid.uuid4().hex}.{ext}"
    target = UPLOAD_DIR / new_name

    with target.open("wb") as fh:
        fh.write(raw)

    return f"/uploads/{new_name}"


def delete_uploaded(relative_url: str) -> bool:
    """Delete the file behind *relative_url* (e.g. ``/uploads/x.jpg``).

    Returns ``True`` when the file was removed, ``False`` if not found.
    """
    rel = relative_url.lstrip("/")
    target = UPLOAD_DIR / rel
    try:
        if target.exists():
            target.unlink()
            return True
        return False
    except OSError:
        return False


def read_uploaded(relative_url: str) -> tuple[bytes, str] | None:
    """Return ``(content, mime)`` for a stored upload, or ``None``."""
    rel = relative_url.lstrip("/")
    target = UPLOAD_DIR / rel
    if not target.exists():
        return None
    raw = target.read_bytes()
    mime = _detect_mime(raw) or "application/octet-stream"
    return raw, mime


def generate_slug(title: str) -> str:
    """Generate a URL-safe slug from *title*.

    Lowercases text, replaces whitespace with hyphens, strips non-alphanumeric
    chars except hyphens, collapses multiple hyphens, strips surrounding
    hyphens, and appends a short random suffix to avoid collisions.
    """
    slug = title.lower().strip()
    # Replace any whitespace run with a single hyphen.
    slug = re.sub(r"\s+", "-", slug)
    # Remove characters that aren't letters/digits/hyphens.
    slug = re.sub(r"[^\w\-]", "", slug, flags=re.UNICODE)
    # Collapse repeated hyphens and strip leading/trailing hyphens.
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        slug = "post"
    suffix = uuid.uuid4().hex[:6]
    return f"{slug}-{suffix}"