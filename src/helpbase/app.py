"""FastAPI application factory."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from helpbase.config import settings
from helpbase.database import engine
from helpbase.dependencies import get_optional_user
from helpbase.models.base import Base
from helpbase.models.user import User
from helpbase.routers import auth, dashboard

TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
