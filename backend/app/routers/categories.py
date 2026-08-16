"""Categories router."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.file_storage import generate_slug
from app.database import get_db
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut
from app.schemas.response import error, success

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("")
async def list_categories(db: AsyncSession = Depends(get_db)):
    """List all categories sorted by sort_order."""
    result = await db.execute(select(Category).order_by(Category.sort_order))
    items = [CategoryOut.model_validate(c).model_dump() for c in result.scalars()]
    return success(items, "ok")


@router.post("", status_code=201)
async def create(payload: CategoryCreate, db: AsyncSession = Depends(get_db)):
    """Create a category."""
    slug = generate_slug(payload.name)
    try:
        cat = Category(name=payload.name, slug=slug, sort_order=payload.sort_order)
        db.add(cat)
        await db.flush()
        await db.refresh(cat)
    except Exception as exc:
        msg = str(exc).lower()
        if "unique" in msg or "duplicate" in msg:
            return error(409, "category already exists")
        return error(500, f"failed to create category: {exc}")
    return success(CategoryOut.model_validate(cat).model_dump(), "created")


@router.put("/{category_id}")
async def update(
    payload: CategoryUpdate,
    category_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Update a category."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if cat is None:
        return error(404, "category not found")
    try:
        if payload.name is not None:
            cat.name = payload.name
            cat.slug = generate_slug(payload.name)
        if payload.sort_order is not None:
            cat.sort_order = payload.sort_order
        await db.flush()
        await db.refresh(cat)
    except Exception as exc:
        msg = str(exc).lower()
        if "unique" in msg or "duplicate" in msg:
            return error(409, "category name already used")
        return error(500, f"failed to update category: {exc}")
    return success(CategoryOut.model_validate(cat).model_dump(), "updated")


@router.delete("/{category_id}")
async def delete(category_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a category (hard delete)."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if cat is None:
        return error(404, "category not found")
    await db.delete(cat)
    await db.flush()
    return success(None, "deleted")