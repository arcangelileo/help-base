"""HelpCenter model."""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from helpbase.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class HelpCenter(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "help_centers"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    primary_color: Mapped[str] = mapped_column(String(7), default="#4F46E5")  # Indigo
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    owner = relationship("User", back_populates="help_centers")
    categories = relationship(
        "Category", back_populates="help_center", cascade="all, delete-orphan",
        order_by="Category.display_order"
    )
    articles = relationship(
        "Article", back_populates="help_center", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<HelpCenter {self.slug}>"
