"""Analytics dashboard router — view tracking stats for help centers."""

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from helpbase.config import settings
from helpbase.database import get_db
from helpbase.dependencies import get_current_user
from helpbase.models.user import User
from helpbase.services.analytics import (
    get_popular_articles,
    get_recent_views,
    get_top_search_queries,
    get_total_views_for_help_center,
    get_views_over_time,
)
from helpbase.services.helpcenter import (
    get_article_count_for_help_center,
    get_help_center_by_id,
)

router = APIRouter(prefix="/dashboard/help-centers", tags=["analytics"])

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/{hc_id}/analytics", response_class=HTMLResponse)
async def analytics_dashboard(
    request: Request,
    hc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analytics dashboard for a help center."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    total_views = await get_total_views_for_help_center(db, hc.id)
    article_count = await get_article_count_for_help_center(db, hc.id)
    popular_articles = await get_popular_articles(db, hc.id, limit=10)
    views_over_time = await get_views_over_time(db, hc.id, days=30)
    top_searches = await get_top_search_queries(db, hc.id, limit=10)
    recent_views = await get_recent_views(db, hc.id, limit=20)

    return templates.TemplateResponse(
        request,
        "dashboard/help_centers/analytics.html",
        {
            "settings": settings,
            "user": user,
            "hc": hc,
            "total_views": total_views,
            "article_count": article_count,
            "popular_articles": popular_articles,
            "views_over_time": views_over_time,
            "top_searches": top_searches,
            "recent_views": recent_views,
        },
    )
