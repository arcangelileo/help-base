"""Dashboard router — authenticated user area."""

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from helpbase.config import settings
from helpbase.database import get_db
from helpbase.dependencies import get_current_user
from helpbase.models.article import Article
from helpbase.models.helpcenter import HelpCenter
from helpbase.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
async def dashboard_index(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    success: str = Query(default=""),
):
    """Main dashboard page."""
    # Get user's help centers
    result = await db.execute(
        select(HelpCenter).where(HelpCenter.owner_id == user.id).order_by(HelpCenter.created_at.desc())
    )
    help_centers = result.scalars().all()

    # Get article count
    article_count_result = await db.execute(
        select(func.count(Article.id)).where(Article.author_id == user.id)
    )
    article_count = article_count_result.scalar() or 0

    # Get total views
    total_views_result = await db.execute(
        select(func.coalesce(func.sum(Article.view_count), 0)).where(Article.author_id == user.id)
    )
    total_views = total_views_result.scalar() or 0

    return templates.TemplateResponse(
        request,
        "dashboard/index.html",
        {
            "settings": settings,
            "user": user,
            "help_centers": help_centers,
            "help_center_count": len(help_centers),
            "article_count": article_count,
            "total_views": total_views,
            "success": success,
        },
    )
