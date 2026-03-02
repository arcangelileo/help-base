"""FastAPI application factory."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from helpbase.config import settings
from helpbase.database import engine
from helpbase.dependencies import get_optional_user
from helpbase.models.base import Base
from helpbase.models.user import User
from helpbase.routers import articles, auth, dashboard, help_centers
from helpbase.routers.analytics import router as analytics_router
from helpbase.routers.public import router as public_router
from helpbase.routers.widget import router as widget_router

TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables and FTS index on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Create FTS5 virtual table for search
        await conn.execute(
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
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url=None,
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(help_centers.router)
app.include_router(articles.router)
app.include_router(analytics_router)
app.include_router(public_router)
app.include_router(widget_router)


# --- Error Handlers ---


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Custom handler for HTTP exceptions (404, 500, etc.)."""
    if exc.status_code == 404:
        return templates.TemplateResponse(
            request,
            "public/404.html",
            {"settings": settings},
            status_code=404,
        )
    # For other HTTP errors, return a JSON response
    return HTMLResponse(
        content=f"<h1>Error {exc.status_code}</h1><p>{exc.detail}</p>",
        status_code=exc.status_code,
    )


# --- Health Check ---

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name, "version": "0.1.0"}


# --- Landing Page ---

@app.get("/", response_class=HTMLResponse)
async def landing_page(
    request: Request,
    current_user: User | None = Depends(get_optional_user),
):
    """Landing page."""
    return templates.TemplateResponse(
        request, "landing.html", {"settings": settings, "user": current_user}
    )
