"""Tags router."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.file_storage import generate_slug
from app.database import get_db
from app.models.tag import Tag
from app.schemas.response import error, success
from app.schemas.tag import TagCreate, TagOut, TagUpdate

router = APIRouter(prefix="/api/tags", tags=["Tags"])


@router.get("")
async def list_tags(db: AsyncSession = Depends(get_db)):
    """List all tags alphabetically."""
    result = await db.execute(select(Tag).order_by(Tag.name))
    items = [TagOut.model_validate(t).model_dump() for t in result.scalars()]
    return success(items, "ok")


@router.post("", status_code=201)
async def create(payload: TagCreate, db: AsyncSession = Depends(get_db)):
    """Create a tag."""
    slug = generate_slug(payload.name)
    try:
        tag = Tag(name=payload.name, slug=slug)
        db.add(tag)
        await db.flush()
        await db.refresh(tag)
    except Exception as exc:
        msg = str(exc).lower()
        if "unique" in msg or "duplicate" in msg:
            return error(409, "tag already exists")
        return error(500, f"failed to create tag: {exc}")
    return success(TagOut.model_validate(tag).model_dump(), "created")


@router.put("/{tag_id}")
async def update(payload: TagUpdate, tag_id: str, db: AsyncSession = Depends(get_db)):
    """Update a tag's name."""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if tag is None:
        return error(404, "tag not found")
    try:
        if payload.name is not None:
            tag.name = payload.name
            tag.slug = generate_slug(payload.name)
        await db.flush()
        await db.refresh(tag)
    except Exception as exc:
        msg = str(exc).lower()
        if "unique" in msg or "duplicate" in msg:
            return error(409, "tag name already used")
        return error(500, f"failed to update tag: {exc}")
    return success(TagOut.model_validate(tag).model_dump(), "updated")


@router.delete("/{tag_id}")
async def delete(tag_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a tag (cascade removes post_tags)."""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if tag is None:
        return error(404, "tag not found")
    await db.delete(tag)
    await db.flush()
    return success(None, "deleted")