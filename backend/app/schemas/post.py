"""Post schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TagOut(BaseModel):
    id: str
    name: str
    slug: str

    model_config = {"from_attributes": True}


class CategoryOut(BaseModel):
    id: str
    name: str
    slug: str
    post_count: int = 0

    model_config = {"from_attributes": True}


class PostCreate(BaseModel):
    """Payload for creating a post."""

    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., min_length=1)
    excerpt: Optional[str] = None
    cover_url: Optional[str] = None
    category_id: Optional[str] = None
    tag_ids: list[str] = Field(default_factory=list)
    status: str = Field(default="draft", pattern="^(draft|published)$")


class PostUpdate(BaseModel):
    """Payload for updating a post."""

    title: Optional[str] = Field(None, min_length=1, max_length=300)
    content: Optional[str] = None
    excerpt: Optional[str] = None
    cover_url: Optional[str] = None
    category_id: Optional[str] = None
    tag_ids: Optional[list[str]] = None
    status: Optional[str] = None


class UserOutRef(BaseModel):
    """Lightweight user ref for post details."""

    id: str
    username: str
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class PostOut(BaseModel):
    """Public post shape returned by list endpoints."""

    id: str
    title: str
    slug: str
    excerpt: Optional[str] = None
    cover_url: Optional[str] = None
    category: Optional[CategoryOut] = None
    tags: list[TagOut] = Field(default_factory=list)
    status: str
    is_deleted: bool = False
    view_count: int = 0
    author_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PostDetailOut(BaseModel):
    """Full post shape for detail endpoints."""

    id: str
    title: str
    slug: str
    content: str
    excerpt: Optional[str] = None
    cover_url: Optional[str] = None
    category: Optional[CategoryOut] = None
    tags: list[TagOut] = Field(default_factory=list)
    status: str
    view_count: int = 0
    author: Optional[UserOutRef] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SetTagsRequest(BaseModel):
    """Payload for PATCH /posts/{id}/tags."""

    tag_ids: list[str]