"""Comments router."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.comment import Comment
from app.models.post import Post
from app.schemas.comment import CommentCreate, CommentOut
from app.schemas.response import error, success
from app.schemas.setting import SettingsOut
from app.models.setting import Setting


router = APIRouter(tags=["Comments"])


@router.get("/api/posts/{post_id}/comments")
async def list_comments(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    parent_id: Optional[str] = None,
):
    """List comments for a post, optionally filtered by parent_id."""
    # Verify post exists
    post = await _get_post(db, post_id)
    if post is None:
        return error(404, "post not found")

    settings = await _get_settings(db)
    conditions = [
        Comment.post_id == post_id,
        Comment.is_deleted.is_(False),
    ]
    if settings and not settings.comment_enabled:
        return success([], "comments disabled")
    if parent_id:
        conditions.append(Comment.parent_id == parent_id)

    result = await db.execute(
        select(Comment)
        .where(and_(*conditions))
        .options(selectinload(Comment.replies))
        .order_by(Comment.created_at)
    )
    comments = list(result.scalars())
    items = [_comment_to_dict(c, settings) for c in comments]
    return success(items, "ok")


@router.post("/api/posts/{post_id}/comments", status_code=201)
async def create_comment(
    post_id: str,
    payload: CommentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new comment."""
    post = await _get_post(db, post_id)
    if post is None:
        return error(404, "post not found")

    settings = await _get_settings(db)
    if settings and not settings.comment_enabled:
        return error(403, "comments disabled")

    if payload.parent_id:
        parent = await db.get(Comment, payload.parent_id)
        if parent is None or parent.post_id != post_id:
            return error(404, "parent comment not found")

    try:
        comment = Comment(
            post_id=post_id,
            nickname=payload.nickname,
            email=payload.email,
            content=payload.content,
            parent_id=payload.parent_id,
            is_approved=not (settings and settings.comment_need_approval),
        )
        db.add(comment)
        await db.flush()
        await db.refresh(comment)
    except Exception as exc:
        return error(500, f"failed to create comment: {exc}")

    return success(_comment_to_dict(comment, settings), "created")


@router.delete("/api/comments/{comment_id}")
async def delete_comment(comment_id: str, db: AsyncSession = Depends(get_db)):
    """Soft-delete a comment."""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if comment is None:
        return error(404, "comment not found")
    comment.is_deleted = True
    await db.flush()
    return success(None, "deleted")


# ---------- helpers --------------------------------------------------------

async def _get_post(db: AsyncSession, post_id: str) -> Post | None:
    result = await db.execute(select(Post).where(Post.id == post_id, Post.is_deleted.is_(False)))
    return result.scalar_one_or_none()


async def _get_settings(db: AsyncSession) -> Setting | None:
    result = await db.execute(select(Setting).where(Setting.id == "1"))
    return result.scalar_one_or_none()


def _comment_to_dict(comment: Comment, settings: Setting | None) -> dict:
    approved = comment.is_approved
    if settings and settings.comment_need_approval and not approved:
        # Redact pending content for anonymous viewers
        content = "[pending approval]"
    else:
        content = comment.content
    d = CommentOut.model_validate(comment).model_dump()
    d["content"] = content
    d["is_approved"] = approved
    return d