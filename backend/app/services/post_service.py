"""Post service — business logic for post CRUD, previews, publish."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func as sql_func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.file_storage import generate_slug
from app.models.post import Post
from app.models.post_tag import PostTag
from app.models.tag import Tag


async def create_post(
    db: AsyncSession,
    *,
    title: str,
    content: str,
    author_id: str,
    excerpt: Optional[str] = None,
    cover_url: Optional[str] = None,
    category_id: Optional[str] = None,
    tag_ids: list[str] | None = None,
    status: str = "draft",
) -> Post:
    """Persist a new post and associate tags."""
    slug = generate_slug(title)
    post = Post(
        title=title,
        slug=slug,
        content=content,
        excerpt=excerpt,
        cover_url=cover_url,
        category_id=category_id,
        author_id=author_id,
        status=status,
        published_at=datetime.now(timezone.utc) if status == "published" else None,
    )
    db.add(post)
    await db.flush()

    if tag_ids:
        for tid in tag_ids:
            tag_ref = PostTag(post_id=post.id, tag_id=tid)
            db.add(tag_ref)

    await db.refresh(post)
    return post


async def get_post(db: AsyncSession, post_id: str) -> Post | None:
    """Fetch a post with eager category, tags and author."""
    stmt = (
        select(Post)
        .options(
            selectinload(Post.category),
            selectinload(Post.author),
        )
        .where(Post.id == post_id, Post.is_deleted.is_(False))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_post(
    db: AsyncSession,
    post: Post,
    data: dict,
    tag_ids: list[str] | None = None,
) -> Post:
    """Apply a partial update to an existing post.

    *data* contains scalar field updates; *tag_ids* replaces tags.
    """
    if "title" in data and data["title"] is not None:
        post.title = data["title"]
        post.slug = generate_slug(data["title"])
    if data.get("content") is not None:
        post.content = data["content"]
    if data.get("excerpt") is not None:
        post.excerpt = data["excerpt"]
    if data.get("cover_url") is not None:
        post.cover_url = data["cover_url"]
    if data.get("category_id") is not None:
        post.category_id = data["category_id"]
    if data.get("status") is not None:
        old = post.status
        post.status = data["status"]
        if data["status"] == "published" and old != "published":
            post.published_at = datetime.now(timezone.utc)

    if tag_ids is not None:
        # Remove existing associations and re-insert.
        stmt = select(PostTag).where(PostTag.post_id == post.id)
        result = await db.execute(stmt)
        for row in result.scalars():
            await db.delete(row)
        for tid in tag_ids:
            db.add(PostTag(post_id=post.id, tag_id=tid))

    await db.flush()
    await db.refresh(post)
    return post


async def soft_delete_post(db: AsyncSession, post: Post) -> None:
    """Mark a post as deleted."""
    post.is_deleted = True


async def publish_post(db: AsyncSession, post: Post) -> Post:
    """Transition post from draft to published."""
    if post.status == "draft":
        post.status = "published"
        post.published_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(post)
    return post


async def list_posts(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 10,
    category_id: Optional[str] = None,
    tag_id: Optional[str] = None,
    status: Optional[str] = None,
) -> tuple[list[Post], int]:
    """Return ``(posts, total)`` for list pagination."""
    base = select(Post).where(Post.is_deleted.is_(False))
    if category_id:
        base = base.where(Post.category_id == category_id)
    if tag_id:
        base = base.join(PostTag, PostTag.post_id == Post.id).where(PostTag.tag_id == tag_id)
    if status:
        base = base.where(Post.status == status)

    total_stmt = select(sql_func.count()).select_from(base.subquery())
    total_result = await db.execute(total_stmt)
    total = int(total_result.scalar_one() or 0)

    stmt = (
        base
        .options(selectinload(Post.category))
        .order_by(Post.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    return list(result.scalars()), total


async def archives(db: AsyncSession) -> list[dict]:
    """Return posts grouped by year-month (YYYY-MM) with counts."""
    rows = (
        await db.execute(
            select(
                sql_func.strftime("%Y-%m", Post.created_at).label("ym"),
                sql_func.count().label("cnt"),
            )
            .where(Post.is_deleted.is_(False))
            .group_by("ym")
            .order_by(sql_func.strftime("%Y-%m", Post.created_at).desc())
        )
    ).all()
    return [{"year_month": r.ym, "count": int(r.cnt)} for r in rows]


def render_post_html(post: Post) -> str:
    """Return a minimal rendered HTML preview of a post."""
    excerpt = post.excerpt or ""
    meta_parts = []
    if post.published_at:
        meta_parts.append(post.published_at.strftime("%Y-%m-%d"))
    if post.category and post.category.name:
        meta_parts.append(f"Category: {post.category.name}")
    meta = " · ".join(meta_parts)
    cover_html = ""
    if post.cover_url:
        cover_html = '<img src="' + post.cover_url + '" class="cover" />'
    excerpt_html = ""
    if excerpt:
        excerpt_html = "<p>" + _html_escape(excerpt) + "</p>"
    return (
        "<div class='post-preview'>"
        "<h1>" + _html_escape(post.title) + "</h1>"
        "<div class='meta'>" + _html_escape(meta) + "</div>"
        + cover_html
        + "<div class='content'>" + post.content + "</div>"
        + excerpt_html
        + "</div>"
    )


def _html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )