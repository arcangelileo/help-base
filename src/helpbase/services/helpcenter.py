"""Help center service — CRUD operations."""

import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from helpbase.models.article import Article
from helpbase.models.category import Category
from helpbase.models.helpcenter import HelpCenter


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


async def ensure_unique_slug(db: AsyncSession, slug: str, exclude_id: str | None = None) -> str:
    """Ensure a help center slug is unique, appending a number if needed."""
    original = slug
    counter = 1
    while True:
        query = select(HelpCenter).where(HelpCenter.slug == slug)
        if exclude_id:
            query = query.where(HelpCenter.id != exclude_id)
        result = await db.execute(query)
        if result.scalar_one_or_none() is None:
            return slug
        slug = f"{original}-{counter}"
        counter += 1


async def create_help_center(
    db: AsyncSession,
    name: str,
    owner_id: str,
    description: str | None = None,
    primary_color: str = "#4F46E5",
) -> HelpCenter:
    """Create a new help center with a unique slug."""
    slug = slugify(name)
    if not slug:
        slug = "help-center"
    slug = await ensure_unique_slug(db, slug)

    hc = HelpCenter(
        name=name,
        slug=slug,
        description=description,
        primary_color=primary_color,
        owner_id=owner_id,
    )
    db.add(hc)
    await db.flush()
    await db.refresh(hc)
    return hc


async def get_help_center_by_id(
    db: AsyncSession, hc_id: str, owner_id: str | None = None
) -> HelpCenter | None:
    """Get a help center by ID, optionally filtering by owner."""
    query = select(HelpCenter).where(HelpCenter.id == hc_id)
    if owner_id:
        query = query.where(HelpCenter.owner_id == owner_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_help_center_with_categories(
    db: AsyncSession, hc_id: str, owner_id: str
) -> HelpCenter | None:
    """Get a help center with eagerly loaded categories."""
    query = (
        select(HelpCenter)
        .where(HelpCenter.id == hc_id, HelpCenter.owner_id == owner_id)
        .options(selectinload(HelpCenter.categories))
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_help_centers_for_user(db: AsyncSession, owner_id: str) -> list[HelpCenter]:
    """Get all help centers for a user, ordered by creation date."""
    result = await db.execute(
        select(HelpCenter)
        .where(HelpCenter.owner_id == owner_id)
        .order_by(HelpCenter.created_at.desc())
    )
    return list(result.scalars().all())


async def update_help_center(
    db: AsyncSession,
    hc: HelpCenter,
    name: str | None = None,
    description: str | None = None,
    primary_color: str | None = None,
) -> HelpCenter:
    """Update a help center's fields."""
    if name is not None and name != hc.name:
        hc.name = name
        new_slug = slugify(name)
        if not new_slug:
            new_slug = "help-center"
        hc.slug = await ensure_unique_slug(db, new_slug, exclude_id=hc.id)
    if description is not None:
        hc.description = description
    if primary_color is not None:
        hc.primary_color = primary_color
    await db.flush()
    await db.refresh(hc)
    return hc


async def delete_help_center(db: AsyncSession, hc: HelpCenter) -> None:
    """Delete a help center and all related data (via cascade)."""
    await db.delete(hc)
    await db.flush()


async def get_article_count_for_help_center(db: AsyncSession, hc_id: str) -> int:
    """Get the count of articles in a help center."""
    result = await db.execute(
        select(func.count(Article.id)).where(Article.help_center_id == hc_id)
    )
    return result.scalar() or 0


async def get_category_article_counts(db: AsyncSession, hc_id: str) -> dict[str, int]:
    """Get article count per category for a help center."""
    result = await db.execute(
        select(Article.category_id, func.count(Article.id))
        .where(Article.help_center_id == hc_id)
        .group_by(Article.category_id)
    )
    return {row[0]: row[1] for row in result.all() if row[0] is not None}


async def get_uncategorized_article_count(db: AsyncSession, hc_id: str) -> int:
    """Get count of articles without a category."""
    result = await db.execute(
        select(func.count(Article.id)).where(
            Article.help_center_id == hc_id, Article.category_id.is_(None)
        )
    )
    return result.scalar() or 0
