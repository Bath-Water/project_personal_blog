"""Search router — jieba-based keyword search."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.post import Post
from app.schemas.post import PostOut
from app.schemas.response import error, success
from app.services.search_service import build_search_conditions

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.get("")
async def search(
    q: str = Query(..., min_length=1, description="Search keyword"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Search posts by keyword (Chinese-aware segmentation)."""
    keywords, has_query = build_search_conditions(q)
    if not has_query:
        return success(
            {"items": [], "keywords": [], "total": 0},
            "ok",
        )

    # Build OR across title/content for each keyword
    conditions = []
    for kw in keywords:
        pattern = f"%{kw}%"
        conditions.append(Post.title.ilike(pattern))
        conditions.append(Post.content.ilike(pattern))

    base = (
        select(Post)
        .where(Post.is_deleted.is_(False), or_(*conditions))
        .options(selectinload(Post.category))
        .order_by(Post.created_at.desc())
    )

    result = await db.execute(base.offset((page - 1) * page_size).limit(page_size))
    posts = list(result.scalars())

    # Total count
    from sqlalchemy import func as sql_func

    total_result = await db.execute(
        select(sql_func.count()).select_from(base.subquery())
    )
    total = int(total_result.scalar_one() or 0)

    items = [PostOut.model_validate(p).model_dump() for p in posts]
    return success(
        {"items": items, "keywords": keywords, "total": total},
        "ok",
    )