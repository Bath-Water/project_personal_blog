"""Category schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    sort_order: int = Field(default=0, ge=0)


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    sort_order: Optional[int] = Field(None, ge=0)


class CategoryOut(BaseModel):
    id: str
    name: str
    slug: str
    sort_order: int = 0
    post_count: int = 0
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}