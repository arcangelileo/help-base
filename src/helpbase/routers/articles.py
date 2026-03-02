"""Article CRUD router — create, read, update, delete articles with Markdown editor."""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from helpbase.config import settings
from helpbase.database import get_db
from helpbase.dependencies import get_current_user
from helpbase.models.user import User
from helpbase.services.article import (
    create_article,
    delete_article,
    get_article_by_id,
    get_article_revisions,
    get_articles_for_help_center,
    get_categories_for_select,
    render_markdown_to_html,
    update_article,
)
from helpbase.services.helpcenter import get_help_center_by_id

router = APIRouter(prefix="/dashboard/help-centers", tags=["articles"])

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ============================================================
# Article list
# ============================================================


@router.get("/{hc_id}/articles", response_class=HTMLResponse)
async def articles_list(
    request: Request,
    hc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    success: str = Query(default=""),
):
    """List all articles for a help center."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    articles = await get_articles_for_help_center(db, hc.id)
    categories = await get_categories_for_select(db, hc.id)

    # Build category lookup for display
    category_map = {cat.id: cat for cat in categories}

    return templates.TemplateResponse(
        request,
        "dashboard/help_centers/articles/list.html",
        {
            "settings": settings,
            "user": user,
            "hc": hc,
            "articles": articles,
            "category_map": category_map,
            "success": success,
        },
    )


# ============================================================
# Article create
# ============================================================


@router.get("/{hc_id}/articles/new", response_class=HTMLResponse)
async def new_article_page(
    request: Request,
    hc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Show the create article form with Markdown editor."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    categories = await get_categories_for_select(db, hc.id)

    return templates.TemplateResponse(
        request,
        "dashboard/help_centers/articles/new.html",
        {"settings": settings, "user": user, "hc": hc, "categories": categories},
    )


@router.post("/{hc_id}/articles/new", response_class=HTMLResponse)
async def create_article_submit(
    request: Request,
    hc_id: str,
    title: str = Form(...),
    content_markdown: str = Form(""),
    excerpt: str = Form(""),
    category_id: str = Form(""),
    is_published: str = Form(""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Handle article creation."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    errors = []
    title = title.strip()
    content_markdown = content_markdown.strip()
    excerpt = excerpt.strip() or None
    cat_id = category_id.strip() or None
    published = is_published == "on"

    if not title:
        errors.append("Article title is required.")
    if len(title) > 500:
        errors.append("Title must be 500 characters or fewer.")

    categories = await get_categories_for_select(db, hc.id)

    if errors:
        return templates.TemplateResponse(
            request,
            "dashboard/help_centers/articles/new.html",
            {
                "settings": settings,
                "user": user,
                "hc": hc,
                "categories": categories,
                "errors": errors,
                "form_data": {
                    "title": title,
                    "content_markdown": content_markdown,
                    "excerpt": excerpt or "",
                    "category_id": cat_id or "",
                    "is_published": published,
                },
            },
            status_code=422,
        )

    article = await create_article(
        db,
        title=title,
        help_center_id=hc.id,
        author_id=user.id,
        content_markdown=content_markdown,
        excerpt=excerpt,
        category_id=cat_id,
        is_published=published,
    )
    await db.commit()
    return RedirectResponse(
        url=f"/dashboard/help-centers/{hc.id}/articles/{article.id}", status_code=303
    )


# ============================================================
# Article detail
# ============================================================


@router.get("/{hc_id}/articles/{article_id}", response_class=HTMLResponse)
async def article_detail(
    request: Request,
    hc_id: str,
    article_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Article detail/preview page."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    article = await get_article_by_id(db, article_id, help_center_id=hc.id)
    if not article:
        return RedirectResponse(url=f"/dashboard/help-centers/{hc.id}/articles", status_code=303)

    # Render markdown to HTML
    content_html = render_markdown_to_html(article.content_markdown) if article.content_markdown else ""

    # Get category info
    categories = await get_categories_for_select(db, hc.id)
    category_map = {cat.id: cat for cat in categories}
    article_category = category_map.get(article.category_id) if article.category_id else None

    return templates.TemplateResponse(
        request,
        "dashboard/help_centers/articles/detail.html",
        {
            "settings": settings,
            "user": user,
            "hc": hc,
            "article": article,
            "content_html": content_html,
            "article_category": article_category,
        },
    )


# ============================================================
# Article edit
# ============================================================


@router.get("/{hc_id}/articles/{article_id}/edit", response_class=HTMLResponse)
async def edit_article_page(
    request: Request,
    hc_id: str,
    article_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Show the article edit form with Markdown editor."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    article = await get_article_by_id(db, article_id, help_center_id=hc.id)
    if not article:
        return RedirectResponse(url=f"/dashboard/help-centers/{hc.id}/articles", status_code=303)

    categories = await get_categories_for_select(db, hc.id)

    return templates.TemplateResponse(
        request,
        "dashboard/help_centers/articles/edit.html",
        {
            "settings": settings,
            "user": user,
            "hc": hc,
            "article": article,
            "categories": categories,
            "form_data": {
                "title": article.title,
                "content_markdown": article.content_markdown or "",
                "excerpt": article.excerpt or "",
                "category_id": article.category_id or "",
                "is_published": article.is_published,
            },
        },
    )


@router.post("/{hc_id}/articles/{article_id}/edit", response_class=HTMLResponse)
async def edit_article_submit(
    request: Request,
    hc_id: str,
    article_id: str,
    title: str = Form(""),
    content_markdown: str = Form(""),
    excerpt: str = Form(""),
    category_id: str = Form(""),
    is_published: str = Form(""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Handle article update."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    article = await get_article_by_id(db, article_id, help_center_id=hc.id)
    if not article:
        return RedirectResponse(url=f"/dashboard/help-centers/{hc.id}/articles", status_code=303)

    errors = []
    title = title.strip()
    content_markdown = content_markdown.strip()
    excerpt = excerpt.strip() or None
    cat_id = category_id.strip() or None
    published = is_published == "on"

    if not title:
        errors.append("Article title is required.")
    if len(title) > 500:
        errors.append("Title must be 500 characters or fewer.")

    categories = await get_categories_for_select(db, hc.id)

    if errors:
        return templates.TemplateResponse(
            request,
            "dashboard/help_centers/articles/edit.html",
            {
                "settings": settings,
                "user": user,
                "hc": hc,
                "article": article,
                "categories": categories,
                "errors": errors,
                "form_data": {
                    "title": title,
                    "content_markdown": content_markdown,
                    "excerpt": excerpt or "",
                    "category_id": cat_id or "",
                    "is_published": published,
                },
            },
            status_code=422,
        )

    await update_article(
        db,
        article,
        title=title,
        content_markdown=content_markdown,
        excerpt=excerpt,
        category_id=cat_id,
        is_published=published,
    )
    await db.commit()
    return RedirectResponse(
        url=f"/dashboard/help-centers/{hc.id}/articles/{article.id}", status_code=303
    )


# ============================================================
# Article delete
# ============================================================


@router.post("/{hc_id}/articles/{article_id}/delete")
async def delete_article_submit(
    hc_id: str,
    article_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an article."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    article = await get_article_by_id(db, article_id, help_center_id=hc.id)
    if not article:
        return RedirectResponse(url=f"/dashboard/help-centers/{hc.id}/articles", status_code=303)

    await delete_article(db, article)
    await db.commit()
    return RedirectResponse(url=f"/dashboard/help-centers/{hc.id}/articles?success=Article+deleted+successfully", status_code=303)


# ============================================================
# Article publish toggle
# ============================================================


@router.post("/{hc_id}/articles/{article_id}/toggle-publish")
async def toggle_publish_article(
    hc_id: str,
    article_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle article publish status."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    article = await get_article_by_id(db, article_id, help_center_id=hc.id)
    if not article:
        return RedirectResponse(url=f"/dashboard/help-centers/{hc.id}/articles", status_code=303)

    await update_article(db, article, is_published=not article.is_published)
    await db.commit()
    return RedirectResponse(
        url=f"/dashboard/help-centers/{hc.id}/articles/{article.id}", status_code=303
    )


# ============================================================
# Markdown preview API (for live editor preview)
# ============================================================


@router.post("/{hc_id}/articles/preview-markdown")
async def preview_markdown(
    request: Request,
    hc_id: str,
    user: User = Depends(get_current_user),
):
    """Render Markdown to HTML for live preview. Accepts JSON body with 'content' field."""
    body = await request.json()
    content = body.get("content", "")
    html = render_markdown_to_html(content) if content else ""
    return JSONResponse({"html": html})
