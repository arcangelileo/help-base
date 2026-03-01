"""Analytics service — article view tracking and stats."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from helpbase.models.analytics import ArticleView
from helpbase.models.article import Article


async def track_article_view(
    db: AsyncSession,
    article_id: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
    referrer: str | None = None,
    search_query: str | None = None,
) -> None:
    """Record an article view and increment the article's view counter."""
    # Create view record
    view = ArticleView(
        article_id=article_id,
        ip_address=ip_address,
        user_agent=user_agent[:500] if user_agent else None,
        referrer=referrer[:500] if referrer else None,
        search_query=search_query[:500] if search_query else None,
    )
    db.add(view)

    # Increment article view_count
    result = await db.execute(
        select(Article).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()
    if article:
        article.view_count = (article.view_count or 0) + 1

    await db.flush()


async def get_popular_articles(
    db: AsyncSession,
    help_center_id: str,
    limit: int = 10,
) -> list[Article]:
    """Get the most viewed articles for a help center."""
    result = await db.execute(
        select(Article)
        .where(
            Article.help_center_id == help_center_id,
            Article.is_published.is_(True),
        )
        .order_by(Article.view_count.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_total_views_for_help_center(
    db: AsyncSession,
    help_center_id: str,
) -> int:
    """Get total article views for a help center."""
    result = await db.execute(
        select(func.coalesce(func.sum(Article.view_count), 0)).where(
            Article.help_center_id == help_center_id
        )
    )
    return result.scalar() or 0


async def get_views_over_time(
    db: AsyncSession,
    help_center_id: str,
    days: int = 30,
) -> list[dict]:
    """Get daily view counts for the last N days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        text(
            """
            SELECT date(av.viewed_at) as view_date, COUNT(*) as view_count
            FROM article_views av
            JOIN articles a ON a.id = av.article_id
            WHERE a.help_center_id = :hc_id
              AND av.viewed_at >= :since
            GROUP BY date(av.viewed_at)
            ORDER BY view_date
            """
        ),
        {"hc_id": help_center_id, "since": since},
    )
    return [{"date": row[0], "count": row[1]} for row in result.fetchall()]


async def get_top_search_queries(
    db: AsyncSession,
    help_center_id: str,
    limit: int = 10,
) -> list[dict]:
    """Get most common search queries that led to article views."""
    result = await db.execute(
        text(
            """
            SELECT av.search_query, COUNT(*) as query_count
            FROM article_views av
            JOIN articles a ON a.id = av.article_id
            WHERE a.help_center_id = :hc_id
              AND av.search_query IS NOT NULL
              AND av.search_query != ''
            GROUP BY av.search_query
            ORDER BY query_count DESC
            LIMIT :limit
            """
        ),
        {"hc_id": help_center_id, "limit": limit},
    )
    return [{"query": row[0], "count": row[1]} for row in result.fetchall()]


async def get_recent_views(
    db: AsyncSession,
    help_center_id: str,
    limit: int = 20,
) -> list[dict]:
    """Get recent article views with article info."""
    result = await db.execute(
        text(
            """
            SELECT a.title, a.slug, av.viewed_at, av.referrer, av.search_query
            FROM article_views av
            JOIN articles a ON a.id = av.article_id
            WHERE a.help_center_id = :hc_id
            ORDER BY av.viewed_at DESC
            LIMIT :limit
            """
        ),
        {"hc_id": help_center_id, "limit": limit},
    )
    return [
        {
            "title": row[0],
            "slug": row[1],
            "viewed_at": row[2],
            "referrer": row[3],
            "search_query": row[4],
        }
        for row in result.fetchall()
    ]
