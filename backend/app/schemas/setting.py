"""Settings schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class SettingsUpdate(BaseModel):
    """Payload for PUT /api/settings."""

    blog_name: Optional[str] = None
    blog_description: Optional[str] = None
    theme_color: Optional[str] = None
    nav_items: Optional[list[dict[str, Any]]] = None
    social_links: Optional[list[dict[str, Any]]] = None
    comment_enabled: Optional[bool] = None
    comment_need_approval: Optional[bool] = None


class SettingsOut(BaseModel):
    id: str = "1"
    blog_name: Optional[str] = None
    blog_description: Optional[str] = None
    theme_color: Optional[str] = None
    nav_items: Optional[list[dict[str, Any]]] = None
    social_links: Optional[list[dict[str, Any]]] = None
    comment_enabled: bool = True
    comment_need_approval: bool = False
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}