"""Help center CRUD router — create, read, update, delete help centers and categories."""

import re
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from helpbase.config import settings
from helpbase.database import get_db
from helpbase.dependencies import get_current_user
from helpbase.models.user import User
from helpbase.services.category import (
    create_category,
    delete_category,
    get_category_by_id,
    reorder_categories,
    update_category,
)
from helpbase.services.helpcenter import (
    create_help_center,
    delete_help_center,
    get_article_count_for_help_center,
    get_category_article_counts,
    get_help_center_by_id,
    get_help_center_with_categories,
    get_uncategorized_article_count,
    update_help_center,
)

router = APIRouter(prefix="/dashboard/help-centers", tags=["help-centers"])

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


# ============================================================
# Help Center CRUD
# ============================================================


@router.get("/new", response_class=HTMLResponse)
async def new_help_center_page(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Show the create help center form."""
    return templates.TemplateResponse(
        request,
        "dashboard/help_centers/new.html",
        {"settings": settings, "user": user},
    )


@router.post("/new", response_class=HTMLResponse)
async def create_help_center_submit(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    primary_color: str = Form("#4F46E5"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Handle help center creation."""
    errors = []
    name = name.strip()
    description = description.strip() or None
    primary_color = primary_color.strip()

    if not name:
        errors.append("Help center name is required.")
    if len(name) > 255:
        errors.append("Name must be 255 characters or fewer.")
    if not COLOR_PATTERN.match(primary_color):
        errors.append("Primary color must be a valid hex color (e.g. #4F46E5).")

    if errors:
        return templates.TemplateResponse(
            request,
            "dashboard/help_centers/new.html",
            {
                "settings": settings,
                "user": user,
                "errors": errors,
                "form_data": {"name": name, "description": description or "", "primary_color": primary_color},
            },
            status_code=422,
        )

    hc = await create_help_center(
        db, name=name, owner_id=user.id, description=description, primary_color=primary_color
    )
    await db.commit()
    return RedirectResponse(url=f"/dashboard/help-centers/{hc.id}", status_code=303)


@router.get("/{hc_id}", response_class=HTMLResponse)
async def help_center_detail(
    request: Request,
    hc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    success: str = Query(default=""),
):
    """Help center detail page — shows categories and article stats."""
    hc = await get_help_center_with_categories(db, hc_id, user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    article_count = await get_article_count_for_help_center(db, hc.id)
    category_article_counts = await get_category_article_counts(db, hc.id)
    uncategorized_count = await get_uncategorized_article_count(db, hc.id)

    return templates.TemplateResponse(
        request,
        "dashboard/help_centers/detail.html",
        {
            "settings": settings,
            "user": user,
            "hc": hc,
            "categories": hc.categories,
            "article_count": article_count,
            "category_article_counts": category_article_counts,
            "uncategorized_count": uncategorized_count,
            "success": success,
        },
    )


@router.get("/{hc_id}/edit", response_class=HTMLResponse)
async def edit_help_center_page(
    request: Request,
    hc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Show the edit help center form."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        request,
        "dashboard/help_centers/edit.html",
        {
            "settings": settings,
            "user": user,
            "hc": hc,
            "form_data": {
                "name": hc.name,
                "description": hc.description or "",
                "primary_color": hc.primary_color,
            },
        },
    )


@router.post("/{hc_id}/edit", response_class=HTMLResponse)
async def edit_help_center_submit(
    request: Request,
    hc_id: str,
    name: str = Form(""),
    description: str = Form(""),
    primary_color: str = Form("#4F46E5"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Handle help center update."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    errors = []
    name = name.strip()
    description = description.strip() or None
    primary_color = primary_color.strip()

    if not name:
        errors.append("Help center name is required.")
    if len(name) > 255:
        errors.append("Name must be 255 characters or fewer.")
    if not COLOR_PATTERN.match(primary_color):
        errors.append("Primary color must be a valid hex color (e.g. #4F46E5).")

    if errors:
        return templates.TemplateResponse(
            request,
            "dashboard/help_centers/edit.html",
            {
                "settings": settings,
                "user": user,
                "hc": hc,
                "errors": errors,
                "form_data": {"name": name, "description": description or "", "primary_color": primary_color},
            },
            status_code=422,
        )

    await update_help_center(db, hc, name=name, description=description, primary_color=primary_color)
    await db.commit()
    return RedirectResponse(url=f"/dashboard/help-centers/{hc.id}?success=Settings+updated+successfully", status_code=303)


@router.post("/{hc_id}/delete")
async def delete_help_center_submit(
    hc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a help center."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    await delete_help_center(db, hc)
    await db.commit()
    return RedirectResponse(url="/dashboard?success=Help+center+deleted+successfully", status_code=303)


# ============================================================
# Category CRUD (nested under help center)
# ============================================================


@router.get("/{hc_id}/categories/new", response_class=HTMLResponse)
async def new_category_page(
    request: Request,
    hc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Show the create category form."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        request,
        "dashboard/help_centers/categories/new.html",
        {"settings": settings, "user": user, "hc": hc},
    )


@router.post("/{hc_id}/categories/new", response_class=HTMLResponse)
async def create_category_submit(
    request: Request,
    hc_id: str,
    name: str = Form(...),
    description: str = Form(""),
    icon: str = Form(""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Handle category creation."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    errors = []
    name = name.strip()
    description = description.strip() or None
    icon = icon.strip() or None

    if not name:
        errors.append("Category name is required.")
    if len(name) > 255:
        errors.append("Name must be 255 characters or fewer.")

    if errors:
        return templates.TemplateResponse(
            request,
            "dashboard/help_centers/categories/new.html",
            {
                "settings": settings,
                "user": user,
                "hc": hc,
                "errors": errors,
                "form_data": {"name": name, "description": description or "", "icon": icon or ""},
            },
            status_code=422,
        )

    await create_category(db, name=name, help_center_id=hc.id, description=description, icon=icon)
    await db.commit()
    return RedirectResponse(url=f"/dashboard/help-centers/{hc.id}?success=Category+created+successfully", status_code=303)


@router.get("/{hc_id}/categories/{cat_id}/edit", response_class=HTMLResponse)
async def edit_category_page(
    request: Request,
    hc_id: str,
    cat_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Show the edit category form."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    cat = await get_category_by_id(db, cat_id, help_center_id=hc.id)
    if not cat:
        return RedirectResponse(url=f"/dashboard/help-centers/{hc.id}", status_code=303)

    return templates.TemplateResponse(
        request,
        "dashboard/help_centers/categories/edit.html",
        {
            "settings": settings,
            "user": user,
            "hc": hc,
            "cat": cat,
            "form_data": {
                "name": cat.name,
                "description": cat.description or "",
                "icon": cat.icon or "",
            },
        },
    )


@router.post("/{hc_id}/categories/{cat_id}/edit", response_class=HTMLResponse)
async def edit_category_submit(
    request: Request,
    hc_id: str,
    cat_id: str,
    name: str = Form(""),
    description: str = Form(""),
    icon: str = Form(""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Handle category update."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    cat = await get_category_by_id(db, cat_id, help_center_id=hc.id)
    if not cat:
        return RedirectResponse(url=f"/dashboard/help-centers/{hc.id}", status_code=303)

    errors = []
    name = name.strip()
    description = description.strip() or None
    icon = icon.strip() or None

    if not name:
        errors.append("Category name is required.")
    if len(name) > 255:
        errors.append("Name must be 255 characters or fewer.")

    if errors:
        return templates.TemplateResponse(
            request,
            "dashboard/help_centers/categories/edit.html",
            {
                "settings": settings,
                "user": user,
                "hc": hc,
                "cat": cat,
                "errors": errors,
                "form_data": {"name": name, "description": description or "", "icon": icon or ""},
            },
            status_code=422,
        )

    await update_category(db, cat, name=name, description=description, icon=icon)
    await db.commit()
    return RedirectResponse(url=f"/dashboard/help-centers/{hc.id}?success=Category+updated+successfully", status_code=303)


@router.post("/{hc_id}/categories/{cat_id}/delete")
async def delete_category_submit(
    hc_id: str,
    cat_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a category (articles in it become uncategorized)."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    cat = await get_category_by_id(db, cat_id, help_center_id=hc.id)
    if not cat:
        return RedirectResponse(url=f"/dashboard/help-centers/{hc.id}", status_code=303)

    await delete_category(db, cat)
    await db.commit()
    return RedirectResponse(url=f"/dashboard/help-centers/{hc.id}?success=Category+deleted+successfully", status_code=303)


@router.post("/{hc_id}/categories/reorder")
async def reorder_categories_submit(
    request: Request,
    hc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reorder categories via HTMX/AJAX. Expects JSON body with category_ids list."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return {"error": "Not found"}

    body = await request.json()
    category_ids = body.get("category_ids", [])
    if category_ids:
        await reorder_categories(db, hc.id, category_ids)
        await db.commit()
    return {"status": "ok"}


# ============================================================
# Embed Widget Page
# ============================================================


@router.get("/{hc_id}/widget", response_class=HTMLResponse)
async def widget_page(
    request: Request,
    hc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Show the embed widget code page."""
    hc = await get_help_center_by_id(db, hc_id, owner_id=user.id)
    if not hc:
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        request,
        "dashboard/help_centers/widget.html",
        {
            "settings": settings,
            "user": user,
            "hc": hc,
            "base_url": settings.base_url.rstrip("/"),
        },
    )
