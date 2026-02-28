"""Authentication router — register, login, logout."""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from helpbase.config import settings
from helpbase.database import get_db
from helpbase.dependencies import get_optional_user
from helpbase.models.user import User
from helpbase.services.auth import (
    authenticate_user,
    create_access_token,
    create_user,
    get_user_by_email,
)

router = APIRouter(prefix="/auth", tags=["auth"])

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# --- Registration ---


@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    current_user: User | None = Depends(get_optional_user),
):
    """Show registration form."""
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(request, "auth/register.html", {"settings": settings})


@router.post("/register", response_class=HTMLResponse)
async def register_submit(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle registration form submission."""
    errors = []

    # Validate inputs
    full_name = full_name.strip()
    email = email.strip().lower()

    if not full_name:
        errors.append("Full name is required.")
    if not email or "@" not in email:
        errors.append("A valid email address is required.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if password != password_confirm:
        errors.append("Passwords do not match.")

    # Check for existing user
    if not errors:
        existing = await get_user_by_email(db, email)
        if existing:
            errors.append("An account with this email already exists.")

    if errors:
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            {
                "settings": settings,
                "errors": errors,
                "form_data": {"full_name": full_name, "email": email},
            },
            status_code=422,
        )

    # Create user
    user = await create_user(db, email=email, password=password, full_name=full_name)
    await db.commit()

    # Auto-login: set JWT cookie and redirect to dashboard
    token = create_access_token(user.id, user.email)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
        secure=not settings.debug,
    )
    return response


# --- Login ---


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    current_user: User | None = Depends(get_optional_user),
):
    """Show login form."""
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(request, "auth/login.html", {"settings": settings})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle login form submission."""
    email = email.strip().lower()
    user = await authenticate_user(db, email, password)

    if user is None:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "settings": settings,
                "errors": ["Invalid email or password."],
                "form_data": {"email": email},
            },
            status_code=401,
        )

    token = create_access_token(user.id, user.email)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
        secure=not settings.debug,
    )
    return response


# --- Logout ---


@router.get("/logout")
async def logout():
    """Log out by clearing the access token cookie."""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token")
    return response
