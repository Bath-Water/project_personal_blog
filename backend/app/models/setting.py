"""Site-wide settings model — single-row configuration."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, JSON, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Setting(Base):
    """Singleton-style row holding site settings."""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(String(1), primary_key=True)  # stored as '1'
    blog_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    blog_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    theme_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nav_items: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    social_links: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    comment_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    comment_need_approval: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Setting {self.blog_name or ''}>"