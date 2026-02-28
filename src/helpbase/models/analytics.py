"""Analytics models."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from helpbase.models.base import Base, UUIDPrimaryKeyMixin, utcnow


class ArticleView(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "article_views"

    article_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    search_query: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    article = relationship("Article", back_populates="views")

    def __repr__(self) -> str:
        return f"<ArticleView {self.article_id} at {self.viewed_at}>"
