"""Full-text search service using SQLite FTS5."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def ensure_fts_table(db: AsyncSession) -> None:
    """Create the FTS5 virtual table if it doesn't exist."""
    await db.execute(
        text(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
                article_id UNINDEXED,
                help_center_id UNINDEXED,
                title,
                content,
                excerpt,
                tokenize='porter unicode61'
            )
            """
        )
    )


async def index_article(
    db: AsyncSession,
    article_id: str,
    help_center_id: str,
    title: str,
    content: str,
    excerpt: str,
) -> None:
    """Add or update an article in the FTS index."""
    # Delete existing entry first (upsert pattern for FTS5)
    await db.execute(
        text("DELETE FROM articles_fts WHERE article_id = :article_id"),
        {"article_id": article_id},
    )
    await db.execute(
        text(
            """
            INSERT INTO articles_fts (article_id, help_center_id, title, content, excerpt)
            VALUES (:article_id, :help_center_id, :title, :content, :excerpt)
            """
        ),
        {
            "article_id": article_id,
            "help_center_id": help_center_id,
            "title": title,
            "content": content,
            "excerpt": excerpt or "",
        },
    )


async def remove_article_from_index(db: AsyncSession, article_id: str) -> None:
    """Remove an article from the FTS index."""
    await db.execute(
        text("DELETE FROM articles_fts WHERE article_id = :article_id"),
        {"article_id": article_id},
    )


async def search_articles(
    db: AsyncSession,
    help_center_id: str,
    query: str,
    limit: int = 20,
) -> list[dict]:
    """Search published articles using FTS5.

    Returns list of dicts with article_id, title, snippet, and rank.
    """
    if not query or not query.strip():
        return []

    # Clean query for FTS5 — escape special chars, use prefix matching
    cleaned = query.strip()
    # Add prefix matching for better UX (typing partial words)
    terms = cleaned.split()
    fts_query = " ".join(f'"{t}"*' for t in terms if t)

    if not fts_query:
        return []

    result = await db.execute(
        text(
            """
            SELECT
                f.article_id,
                f.title,
                snippet(articles_fts, 3, '<mark>', '</mark>', '...', 40) as snippet,
                rank
            FROM articles_fts f
            JOIN articles a ON a.id = f.article_id
            WHERE articles_fts MATCH :query
              AND f.help_center_id = :help_center_id
              AND a.is_published = 1
            ORDER BY rank
            LIMIT :limit
            """
        ),
        {"query": fts_query, "help_center_id": help_center_id, "limit": limit},
    )
    rows = result.fetchall()
    return [
        {
            "article_id": row[0],
            "title": row[1],
            "snippet": row[2],
            "rank": row[3],
        }
        for row in rows
    ]


async def rebuild_fts_index(db: AsyncSession, help_center_id: str | None = None) -> int:
    """Rebuild FTS index from article data. Returns count of indexed articles."""
    if help_center_id:
        # Delete FTS entries for this help center
        await db.execute(
            text("DELETE FROM articles_fts WHERE help_center_id = :hc_id"),
            {"hc_id": help_center_id},
        )
        result = await db.execute(
            text(
                """
                SELECT id, help_center_id, title, content_markdown, excerpt
                FROM articles
                WHERE help_center_id = :hc_id AND is_published = 1
                """
            ),
            {"hc_id": help_center_id},
        )
    else:
        # Full rebuild
        await db.execute(text("DELETE FROM articles_fts"))
        result = await db.execute(
            text(
                """
                SELECT id, help_center_id, title, content_markdown, excerpt
                FROM articles
                WHERE is_published = 1
                """
            )
        )

    rows = result.fetchall()
    for row in rows:
        await db.execute(
            text(
                """
                INSERT INTO articles_fts (article_id, help_center_id, title, content, excerpt)
                VALUES (:article_id, :help_center_id, :title, :content, :excerpt)
                """
            ),
            {
                "article_id": row[0],
                "help_center_id": row[1],
                "title": row[2],
                "content": row[3] or "",
                "excerpt": row[4] or "",
            },
        )
    return len(rows)
