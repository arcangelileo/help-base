"""Category model."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from helpbase.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Category(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    help_center_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("help_centers.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    help_center = relationship("HelpCenter", back_populates="categories")
    articles = relationship(
        "Article", back_populates="category", cascade="all, delete-orphan",
        order_by="Article.display_order"
    )

    def __repr__(self) -> str:
        return f"<Category {self.slug}>"
