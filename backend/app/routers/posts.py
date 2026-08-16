"""Posts router — CRUD, preview, publish, archives, tag management."""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.database import get_db
from app.models.post import Post
from app.models.post_tag import PostTag
from app.models.tag import Tag
from app.models.user import User
from app.schemas.post import (
    PostCreate,
    PostDetailOut,
    PostOut,
    PostUpdate,
    SetTagsRequest,
)
from app.schemas.response import error, success
from app.services.post_service import (
    archives,
    create_post,
    list_posts,
    publish_post,
    render_post_html,
    soft_delete_post,
    update_post,
)

router = APIRouter(prefix="/api/posts", tags=["Posts"])


@router.get("")
async def list_posts_ep(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category_id: Optional[str] = None,
    tag_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
):
    """List posts with optional filters and pagination."""
    posts, total = await list_posts(
        db,
        page=page,
        page_size=page_size,
        category_id=category_id,
        tag_id=tag_id,
        status=status_filter,
    )
    items = [PostOut.model_validate(p).model_dump() for p in posts]
    return success(
        {"items": items, "page": page, "page_size": page_size, "total": total},
        "ok",
    )


@router.get("/archives")
async def get_archives(db: AsyncSession = Depends(get_db)):
    """Return posts grouped by year-month."""
    rows = await archives(db)
    return success(rows, "ok")


@router.get("/{post_id}")
async def get(post_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch a single post with its tags and author."""
    post = await _fetch_post_with_related(db, post_id)
    if post is None:
        return error(404, "post not found")

    post.view_count += 1
    await db.flush()

    tags = await _get_tags_for_post(db, post.id)
    author = post.author
    payload = PostDetailOut.model_validate(post).model_dump()
    payload["tags"] = [{"id": t.id, "name": t.name, "slug": t.slug} for t in tags]
    payload["author"] = (
        {"id": author.id, "username": author.username, "avatar_url": author.avatar_url}
        if author
        else None
    )
    return success(payload, "ok")


@router.post("", status_code=201)
async def create(
    payload: PostCreate,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Create a new post (authenticated)."""
    try:
        post = await create_post(
            db,
            title=payload.title,
            content=payload.content,
            author_id=current.id,
            excerpt=payload.excerpt,
            cover_url=payload.cover_url,
            category_id=payload.category_id,
            tag_ids=payload.tag_ids or [],
            status=payload.status,
        )
    except Exception as exc:
        return error(500, f"failed to create post: {exc}")
    tags = await _get_tags_for_post(db, post.id)
    out = PostOut.model_validate(post).model_dump()
    out["tags"] = [{"id": t.id, "name": t.name, "slug": t.slug} for t in tags]
    return success(out, "created")


@router.put("/{post_id}")
async def update(
    payload: PostUpdate,
    post_id: str,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Update a post (author only)."""
    post = await _fetch_post_by_id(db, post_id)
    if post is None:
        return error(404, "post not found")
    if post.author_id != current.id:
        return error(403, "not the author")

    data = payload.model_dump(exclude_unset=True)
    tag_ids = data.pop("tag_ids", None)
    try:
        updated = await update_post(db, post, data, tag_ids=tag_ids)
    except Exception as exc:
        return error(500, f"failed to update post: {exc}")

    tags = await _get_tags_for_post(db, updated.id)
    out = PostOut.model_validate(updated).model_dump()
    out["tags"] = [{"id": t.id, "name": t.name, "slug": t.slug} for t in tags]
    return success(out, "updated")


@router.delete("/{post_id}")
async def delete(
    post_id: str,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a post (author only)."""
    post = await _fetch_post_by_id(db, post_id)
    if post is None:
        return error(404, "post not found")
    if post.author_id != current.id:
        return error(403, "not the author")
    await soft_delete_post(db, post)
    return success(None, "deleted")


@router.post("/{post_id}/preview")
async def preview(post_id: str, db: AsyncSession = Depends(get_db)):
    """Return rendered HTML preview of a post."""
    post = await _fetch_post_with_related(db, post_id)
    if post is None:
        return error(404, "post not found")
    html = render_post_html(post)
    return success({"html": html}, "ok")


@router.post("/{post_id}/publish")
async def publish(
    post_id: str,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Promote a draft post to published (author only)."""
    post = await _fetch_post_by_id(db, post_id)
    if post is None:
        return error(404, "post not found")
    if post.author_id != current.id:
        return error(403, "not the author")
    try:
        updated = await publish_post(db, post)
    except Exception as exc:
        return error(500, f"failed to publish: {exc}")
    tags = await _get_tags_for_post(db, updated.id)
    out = PostOut.model_validate(updated).model_dump()
    out["tags"] = [{"id": t.id, "name": t.name, "slug": t.slug} for t in tags]
    return success(out, "published")


@router.patch("/{post_id}/tags")
async def set_tags(
    payload: SetTagsRequest,
    post_id: str,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Replace the tag list of a post (author only)."""
    post = await _fetch_post_by_id(db, post_id)
    if post is None:
        return error(404, "post not found")
    if post.author_id != current.id:
        return error(403, "not the author")
    try:
        await update_post(db, post, {}, tag_ids=payload.tag_ids)
    except Exception as exc:
        return error(500, f"failed to update tags: {exc}")
    tags = await _get_tags_for_post(db, post.id)
    return success(
        [{"id": t.id, "name": t.name, "slug": t.slug} for t in tags],
        "tags updated",
    )


# ---------- helpers --------------------------------------------------------

async def _fetch_post_by_id(db: AsyncSession, post_id: str) -> Post | None:
    result = await db.execute(select(Post).where(Post.id == post_id))
    return result.scalar_one_or_none()


async def _fetch_post_with_related(db: AsyncSession, post_id: str) -> Post | None:
    stmt = (
        select(Post)
        .options(selectinload(Post.category), selectinload(Post.author))
        .where(Post.id == post_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _get_tags_for_post(db: AsyncSession, post_id: str) -> list[Tag]:
    stmt = (
        select(Tag)
        .join(PostTag, PostTag.tag_id == Tag.id)
        .where(PostTag.post_id == post_id)
    )
    result = await db.execute(stmt)
    return list(result.scalars())