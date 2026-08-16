"""Search service — jieba segmentation + keyword matching."""

from __future__ import annotations

from sqlalchemy import or_, select, func

from app.models.post import Post

try:
    import jieba
except Exception:  # pragma: no cover
    jieba = None


def _segment(text: str) -> list[str]:
    """Return Chinese-aware keyword segments for *text*."""
    if jieba is not None:
        return [w.strip() for w in jieba.cut(text) if w.strip()]
    # Fallback: split on whitespace/punctuation.
    import re

    return [w for w in re.split(r"[\s\u3000,\.;:!?、，。！？]+", text) if w]


def _title_like_clause(term: str) -> bool:  # type: ignore[valid-type]
    """SQLite LIKE-based title/content match for a single term."""
    pattern = f"%{term}%"
    return or_(
        Post.title.ilike(pattern),
        Post.content.ilike(pattern),
    )


def build_search_conditions(query: str) -> tuple[list[str], bool]:
    """Return ``(keywords, has_query)`` where *keywords* is the segmented list."""
    keywords = [k for k in _segment(query) if len(k) >= 1]
    return keywords, bool(keywords)