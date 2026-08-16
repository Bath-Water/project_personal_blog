"""Media schemas."""

from __future__ import annotations

from pydantic import BaseModel


class MediaUploadResponse(BaseModel):
    """Response after a successful file upload."""

    file_url: str
    file_name: str
    mime_type: str
    size: int