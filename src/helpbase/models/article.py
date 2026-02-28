"""Article and ArticleRevision models."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from helpbase.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class Article(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "articles"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    content_markdown: Mapped[str] = mapped_column(Text, default="")
    excerpt: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int] = mapped_column(Integer, default=0)

    help_center_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("help_centers.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    author_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    help_center = relationship("HelpCenter", back_populates="articles")
    category = relationship("Category", back_populates="articles")
    author = relationship("User")
    revisions = relationship(
        "ArticleRevision", back_populates="article", cascade="all, delete-orphan",
        order_by="ArticleRevision.created_at.desc()"
    )
    views = relationship("ArticleView", back_populates="article", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Article {self.slug}>"


class ArticleRevision(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "article_revisions"

    article_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    article = relationship("Article", back_populates="revisions")

    def __repr__(self) -> str:
        return f"<ArticleRevision {self.article_id}>"
