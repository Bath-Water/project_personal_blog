"""Comment schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    nickname: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = None
    content: str = Field(..., min_length=1)
    parent_id: Optional[str] = None


class CommentOut(BaseModel):
    id: str
    post_id: str
    user_id: Optional[str] = None
    nickname: Optional[str] = None
    email: Optional[str] = None
    content: str
    parent_id: Optional[str] = None
    is_approved: bool
    is_deleted: bool = False
    replies: Optional[list["CommentOut"]] = Field(default_factory=list)
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}