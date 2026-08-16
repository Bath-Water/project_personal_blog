"""Tag schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class TagOut(BaseModel):
    id: str
    name: str
    slug: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}