"""Category service — CRUD operations."""

import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from helpbase.models.article import Article
from helpbase.models.category import Category


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


async def ensure_unique_slug(
    db: AsyncSession, slug: str, help_center_id: str, exclude_id: str | None = None
) -> str:
    """Ensure a category slug is unique within a help center."""
    original = slug
    counter = 1
    while True:
        query = select(Category).where(
            Category.slug == slug, Category.help_center_id == help_center_id
        )
        if exclude_id:
            query = query.where(Category.id != exclude_id)
        result = await db.execute(query)
        if result.scalar_one_or_none() is None:
            return slug
        slug = f"{original}-{counter}"
        counter += 1


async def get_next_display_order(db: AsyncSession, help_center_id: str) -> int:
    """Get the next display order value for a new category."""
    result = await db.execute(
        select(func.coalesce(func.max(Category.display_order), -1)).where(
            Category.help_center_id == help_center_id
        )
    )
    return (result.scalar() or 0) + 1


async def create_category(
    db: AsyncSession,
    name: str,
    help_center_id: str,
    description: str | None = None,
    icon: str | None = None,
) -> Category:
    """Create a new category in a help center."""
    slug = slugify(name)
    if not slug:
        slug = "category"
    slug = await ensure_unique_slug(db, slug, help_center_id)
    display_order = await get_next_display_order(db, help_center_id)

    cat = Category(
        name=name,
        slug=slug,
        description=description,
        icon=icon,
        display_order=display_order,
        help_center_id=help_center_id,
    )
    db.add(cat)
    await db.flush()
    await db.refresh(cat)
    return cat


async def get_category_by_id(
    db: AsyncSession, cat_id: str, help_center_id: str | None = None
) -> Category | None:
    """Get a category by ID, optionally filtering by help center."""
    query = select(Category).where(Category.id == cat_id)
    if help_center_id:
        query = query.where(Category.help_center_id == help_center_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_categories_for_help_center(
    db: AsyncSession, help_center_id: str
) -> list[Category]:
    """Get all categories for a help center, ordered by display_order."""
    result = await db.execute(
        select(Category)
        .where(Category.help_center_id == help_center_id)
        .order_by(Category.display_order)
    )
    return list(result.scalars().all())


async def update_category(
    db: AsyncSession,
    cat: Category,
    name: str | None = None,
    description: str | None = None,
    icon: str | None = None,
) -> Category:
    """Update a category's fields."""
    if name is not None and name != cat.name:
        cat.name = name
        new_slug = slugify(name)
        if not new_slug:
            new_slug = "category"
        cat.slug = await ensure_unique_slug(
            db, new_slug, cat.help_center_id, exclude_id=cat.id
        )
    if description is not None:
        cat.description = description
    if icon is not None:
        cat.icon = icon
    await db.flush()
    await db.refresh(cat)
    return cat


async def delete_category(db: AsyncSession, cat: Category) -> None:
    """Delete a category. Articles in this category get category_id=NULL via ON DELETE SET NULL."""
    await db.delete(cat)
    await db.flush()


async def reorder_categories(
    db: AsyncSession, help_center_id: str, category_ids: list[str]
) -> None:
    """Reorder categories by updating their display_order to match the list order."""
    for i, cat_id in enumerate(category_ids):
        result = await db.execute(
            select(Category).where(
                Category.id == cat_id, Category.help_center_id == help_center_id
            )
        )
        cat = result.scalar_one_or_none()
        if cat:
            cat.display_order = i
    await db.flush()


async def get_article_count(db: AsyncSession, category_id: str) -> int:
    """Get article count for a category."""
    result = await db.execute(
        select(func.count(Article.id)).where(Article.category_id == category_id)
    )
    return result.scalar() or 0
