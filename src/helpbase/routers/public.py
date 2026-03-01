"""Public-facing help center router — renders published help centers for end users."""

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from helpbase.config import settings
from helpbase.database import get_db
from helpbase.models.article import Article
from helpbase.models.category import Category
from helpbase.models.helpcenter import HelpCenter
from helpbase.services.analytics import track_article_view
from helpbase.services.article import render_markdown_to_html
from helpbase.services.search import search_articles

router = APIRouter(prefix="/h", tags=["public"])

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ============================================================
# Helpers
# ============================================================


async def get_help_center_by_slug(db: AsyncSession, slug: str) -> HelpCenter | None:
    """Get a help center by its public slug."""
    result = await db.execute(
        select(HelpCenter).where(HelpCenter.slug == slug)
    )
    return result.scalar_one_or_none()


async def get_published_articles(
    db: AsyncSession,
    help_center_id: str,
    category_id: str | None = None,
) -> list[Article]:
    """Get published articles, optionally filtered by category."""
    query = select(Article).where(
        Article.help_center_id == help_center_id,
        Article.is_published.is_(True),
    )
    if category_id:
        query = query.where(Article.category_id == category_id)
    query = query.order_by(Article.display_order, Article.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_categories_with_article_counts(
    db: AsyncSession,
    help_center_id: str,
) -> list[dict]:
    """Get categories with count of published articles."""
    result = await db.execute(
        select(Category)
        .where(Category.help_center_id == help_center_id)
        .order_by(Category.display_order)
    )
    categories = list(result.scalars().all())

    cats_with_counts = []
    for cat in categories:
        count_result = await db.execute(
            select(Article.id).where(
                Article.category_id == cat.id,
                Article.is_published.is_(True),
            )
        )
        count = len(count_result.all())
        if count > 0:
            cats_with_counts.append({"category": cat, "count": count})

    return cats_with_counts


async def get_article_by_slug(
    db: AsyncSession,
    help_center_id: str,
    article_slug: str,
) -> Article | None:
    """Get a published article by slug within a help center."""
    result = await db.execute(
        select(Article).where(
            Article.help_center_id == help_center_id,
            Article.slug == article_slug,
            Article.is_published.is_(True),
        )
    )
    return result.scalar_one_or_none()


# ============================================================
# Public Help Center Home
# ============================================================


@router.get("/{slug}", response_class=HTMLResponse)
async def public_help_center(
    request: Request,
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Public help center homepage — categories + recent articles."""
    hc = await get_help_center_by_slug(db, slug)
    if not hc:
        return templates.TemplateResponse(
            request,
            "public/404.html",
            {"settings": settings},
            status_code=404,
        )

    categories = await get_categories_with_article_counts(db, hc.id)
    recent_articles = await get_published_articles(db, hc.id)

    return templates.TemplateResponse(
        request,
        "public/home.html",
        {
            "settings": settings,
            "hc": hc,
            "categories": categories,
            "articles": recent_articles[:10],
            "total_articles": len(recent_articles),
        },
    )


# ============================================================
# Category Page
# ============================================================


@router.get("/{slug}/category/{cat_slug}", response_class=HTMLResponse)
async def public_category(
    request: Request,
    slug: str,
    cat_slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Public category page — lists published articles in a category."""
    hc = await get_help_center_by_slug(db, slug)
    if not hc:
        return templates.TemplateResponse(
            request, "public/404.html", {"settings": settings}, status_code=404
        )

    # Find the category
    result = await db.execute(
        select(Category).where(
            Category.help_center_id == hc.id,
            Category.slug == cat_slug,
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        return templates.TemplateResponse(
            request, "public/404.html", {"settings": settings, "hc": hc}, status_code=404
        )

    articles = await get_published_articles(db, hc.id, category_id=category.id)
    all_categories = await get_categories_with_article_counts(db, hc.id)

    return templates.TemplateResponse(
        request,
        "public/category.html",
        {
            "settings": settings,
            "hc": hc,
            "category": category,
            "articles": articles,
            "categories": all_categories,
        },
    )


# ============================================================
# Article Page
# ============================================================


@router.get("/{slug}/articles/{article_slug}", response_class=HTMLResponse)
async def public_article(
    request: Request,
    slug: str,
    article_slug: str,
    q: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Public article page — renders full article with markdown."""
    hc = await get_help_center_by_slug(db, slug)
    if not hc:
        return templates.TemplateResponse(
            request, "public/404.html", {"settings": settings}, status_code=404
        )

    article = await get_article_by_slug(db, hc.id, article_slug)
    if not article:
        return templates.TemplateResponse(
            request, "public/404.html", {"settings": settings, "hc": hc}, status_code=404
        )

    # Render markdown
    content_html = render_markdown_to_html(article.content_markdown) if article.content_markdown else ""

    # Get category for breadcrumb
    article_category = None
    if article.category_id:
        cat_result = await db.execute(
            select(Category).where(Category.id == article.category_id)
        )
        article_category = cat_result.scalar_one_or_none()

    # Track view
    await track_article_view(
        db,
        article_id=article.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer"),
        search_query=q,
    )

    # Get sidebar categories
    all_categories = await get_categories_with_article_counts(db, hc.id)

    return templates.TemplateResponse(
        request,
        "public/article.html",
        {
            "settings": settings,
            "hc": hc,
            "article": article,
            "content_html": content_html,
            "article_category": article_category,
            "categories": all_categories,
        },
    )


# ============================================================
# Search
# ============================================================


@router.get("/{slug}/search", response_class=HTMLResponse)
async def public_search(
    request: Request,
    slug: str,
    q: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
):
    """Search articles within a help center."""
    hc = await get_help_center_by_slug(db, slug)
    if not hc:
        return templates.TemplateResponse(
            request, "public/404.html", {"settings": settings}, status_code=404
        )

    results = []
    if q.strip():
        raw_results = await search_articles(db, hc.id, q.strip())
        # Resolve article slugs for URLs
        for r in raw_results:
            slug_result = await db.execute(
                select(Article.slug).where(Article.id == r["article_id"])
            )
            art_slug = slug_result.scalar_one_or_none()
            r["slug"] = art_slug or r["article_id"]
        results = raw_results

    all_categories = await get_categories_with_article_counts(db, hc.id)

    return templates.TemplateResponse(
        request,
        "public/search.html",
        {
            "settings": settings,
            "hc": hc,
            "query": q,
            "results": results,
            "categories": all_categories,
        },
    )


@router.get("/{slug}/search/api", response_class=JSONResponse)
async def search_api(
    slug: str,
    q: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
):
    """JSON search API for AJAX / widget use."""
    hc = await get_help_center_by_slug(db, slug)
    if not hc:
        return JSONResponse({"error": "Help center not found"}, status_code=404)

    results = []
    if q.strip():
        results = await search_articles(db, hc.id, q.strip(), limit=10)
        # Add URLs to results
        for r in results:
            r["url"] = f"/h/{slug}/articles/{r['article_id']}?q={q.strip()}"
            # We need to get the article slug
            art_result = await db.execute(
                select(Article.slug).where(Article.id == r["article_id"])
            )
            art_slug = art_result.scalar_one_or_none()
            if art_slug:
                r["url"] = f"/h/{slug}/articles/{art_slug}?q={q.strip()}"

    return JSONResponse({"results": results, "query": q})
