"""Tests for SQLAlchemy models."""

import pytest
from sqlalchemy import select

from helpbase.models import User, HelpCenter, Category, Article


@pytest.mark.asyncio
async def test_create_user(db_session):
    """Can create a user and read it back."""
    user = User(
        email="test@example.com",
        hashed_password="fakehash",
        full_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    found = result.scalar_one()
    assert found.full_name == "Test User"
    assert found.is_active is True
    assert found.id is not None


@pytest.mark.asyncio
async def test_create_help_center(db_session):
    """Can create a help center linked to a user."""
    user = User(email="owner@example.com", hashed_password="fakehash", full_name="Owner")
    db_session.add(user)
    await db_session.flush()

    hc = HelpCenter(name="My Docs", slug="my-docs", owner_id=user.id)
    db_session.add(hc)
    await db_session.commit()

    result = await db_session.execute(select(HelpCenter).where(HelpCenter.slug == "my-docs"))
    found = result.scalar_one()
    assert found.name == "My Docs"
    assert found.primary_color == "#4F46E5"


@pytest.mark.asyncio
async def test_create_category_and_article(db_session):
    """Can create a category with articles."""
    user = User(email="author@example.com", hashed_password="fakehash", full_name="Author")
    db_session.add(user)
    await db_session.flush()

    hc = HelpCenter(name="Docs", slug="docs", owner_id=user.id)
    db_session.add(hc)
    await db_session.flush()

    cat = Category(name="Getting Started", slug="getting-started", help_center_id=hc.id)
    db_session.add(cat)
    await db_session.flush()

    article = Article(
        title="Quick Start Guide",
        slug="quick-start-guide",
        content_markdown="# Quick Start\n\nWelcome!",
        help_center_id=hc.id,
        category_id=cat.id,
        author_id=user.id,
        is_published=True,
    )
    db_session.add(article)
    await db_session.commit()

    result = await db_session.execute(
        select(Article).where(Article.slug == "quick-start-guide")
    )
    found = result.scalar_one()
    assert found.title == "Quick Start Guide"
    assert found.is_published is True
    assert found.view_count == 0
