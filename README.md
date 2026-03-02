# HelpBase

**Lightweight knowledge base and help center SaaS.** Create beautiful, searchable help documentation for your customers — organized into categories, published on a branded public site, with built-in analytics and an embeddable search widget.

Built for SaaS companies, startups, and small businesses that need customer-facing documentation without paying $50+/mo for Zendesk Guide or Intercom Articles.

---

## Features

- **Multiple Help Centers** — Create separate help centers for different products or brands, each with its own slug-based URL
- **Category Organization** — Group articles into categories with emoji icons, descriptions, and drag-to-reorder
- **Markdown Editor** — Write articles in Markdown with live preview (split-pane), code highlighting, tables, and task lists
- **Public Help Center** — Branded public site at `/h/{slug}` with category navigation, full-text search, and responsive design
- **Full-Text Search** — SQLite FTS5 with porter stemming, prefix matching, and highlighted result snippets
- **Article Analytics** — Track view counts, popular articles, top search queries, and recent activity
- **Embeddable Widget** — Drop a single `<script>` tag onto any website to add a floating help search widget
- **User Authentication** — JWT-based auth with httponly cookies and bcrypt password hashing
- **Custom Branding** — Per-help-center accent colors applied to both the public site and the embeddable widget
- **Article Revisions** — Automatic revision tracking (last 10 versions) for every article edit
- **Docker Ready** — One-command deployment with Docker Compose

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11+, FastAPI, async SQLAlchemy + aiosqlite |
| **Database** | SQLite with FTS5 full-text search |
| **Frontend** | Jinja2 templates, Tailwind CSS (CDN), HTMX |
| **Auth** | JWT (python-jose) + bcrypt (passlib) |
| **Markdown** | python-markdown + pymdown-extensions |
| **Tests** | pytest + pytest-asyncio (148 tests) |
| **Deployment** | Docker multi-stage build, Docker Compose |

---

## Quick Start

### Docker (recommended)

```bash
# Clone and run — that's it
git clone https://github.com/arcangelileo/help-base.git
cd help-base
docker compose up -d
```

The app is now running at **http://localhost:8000**. Register an account and start building your help center.

> **Production tip:** Set a real secret key before deploying:
> ```bash
> HELPBASE_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))") docker compose up -d
> ```

### Local Development

```bash
# Clone
git clone https://github.com/arcangelileo/help-base.git
cd help-base

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Pin bcrypt for Python 3.13 compatibility
uv pip install "bcrypt==4.1.3"

# Copy and edit environment variables
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start the dev server with auto-reload
uvicorn helpbase.app:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** to see the landing page. Register at `/auth/register` to start creating help centers.

---

## Configuration

All settings use environment variables with the `HELPBASE_` prefix. You can also place them in a `.env` file (see `.env.example`).

| Variable | Default | Description |
|---|---|---|
| `HELPBASE_SECRET_KEY` | `change-me-in-production-please` | JWT signing key — **must change in production** |
| `HELPBASE_DEBUG` | `false` | Enable debug mode (Swagger UI at `/docs`, SQL echo) |
| `HELPBASE_BASE_URL` | `http://localhost:8000` | Public URL used in widget embed snippets |
| `HELPBASE_DATABASE_URL` | `sqlite+aiosqlite:///helpbase.db` | Database connection string |
| `HELPBASE_JWT_EXPIRE_MINUTES` | `10080` (7 days) | JWT token lifetime |

---

## Running Tests

```bash
# Run all 148 tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=helpbase --cov-report=term-missing

# Single test file
python -m pytest tests/test_widget.py -v
```

**Test suite breakdown:**

| File | Tests | Coverage |
|---|---|---|
| `test_auth.py` | 27 | Registration, login, logout, JWT, password hashing |
| `test_articles.py` | 31 | Article CRUD, Markdown rendering, publish toggle, revisions |
| `test_public.py` | 27 | Public pages, search, analytics, view tracking |
| `test_widget.py` | 22 | Embeddable widget JS, search API, CORS |
| `test_help_centers.py` | 18 | Help center CRUD, slugification, authorization |
| `test_categories.py` | 16 | Category CRUD, reordering, authorization |
| `test_health.py` | 4 | Health check, landing page |
| `test_models.py` | 3 | SQLAlchemy model CRUD |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser / Client                      │
├──────────┬──────────────┬──────────────┬────────────────────┤
│  Landing │  Dashboard   │ Public Help  │  Embeddable Widget │
│  Page    │  (CRUD UI)   │ Center       │  (JS + iframe)     │
└──────────┴──────────────┴──────────────┴────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │    FastAPI App     │
                    │   (Jinja2 + HTMX) │
                    ├───────────────────┤
                    │     Routers       │
                    │  auth · dashboard │
                    │  articles · public│
                    │  analytics·widget │
                    ├───────────────────┤
                    │    Services       │
                    │  auth · article   │
                    │  helpcenter       │
                    │  category·search  │
                    │  analytics        │
                    ├───────────────────┤
                    │  SQLAlchemy ORM   │
                    │  (async + models) │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  SQLite + FTS5    │
                    │  (aiosqlite)      │
                    └───────────────────┘
```

**Key design decisions:**

- **Markdown storage** — Articles are stored as raw Markdown and rendered to HTML on read via `python-markdown` + `pymdown-extensions`
- **FTS5 search** — Zero-dependency full-text search using SQLite's FTS5 extension with porter stemmer and prefix matching
- **Slug-based routing** — Each help center gets `/h/{slug}/`, articles at `/h/{slug}/articles/{article-slug}`
- **JWT in httponly cookies** — Secure session management without localStorage, with bcrypt password hashing
- **Service layer** — Business logic is isolated in `services/`, keeping routers thin and testable
- **Async throughout** — async SQLAlchemy + aiosqlite for non-blocking I/O

---

## Embeddable Widget

Add a floating help search widget to any website with a single script tag:

```html
<script src="https://your-domain.com/widget/your-slug/embed.js" async></script>
```

The widget:
- Creates a floating help button matching your brand color
- Opens a search panel with real-time, debounced search
- Links directly to published articles on your help center
- Works cross-origin with CORS support
- Closes with Escape key, fully mobile-responsive

Get your embed code from **Dashboard → Help Center → Embed Widget**.

---

## API Endpoints

### Public

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Landing page |
| `GET` | `/health` | Health check (JSON) |
| `GET` | `/h/{slug}` | Public help center home |
| `GET` | `/h/{slug}/articles/{article-slug}` | Public article page (tracks views) |
| `GET` | `/h/{slug}/category/{cat-slug}` | Public category page |
| `GET` | `/h/{slug}/search?q=` | Search results page (HTML) |
| `GET` | `/h/{slug}/search/api?q=` | Search JSON API |
| `GET` | `/widget/{slug}/embed.js` | Widget JavaScript snippet (CORS) |
| `GET` | `/widget/{slug}/search?q=` | Widget search API (CORS) |

### Authentication

| Method | Path | Description |
|---|---|---|
| `GET` | `/auth/register` | Registration form |
| `POST` | `/auth/register` | Submit registration |
| `GET` | `/auth/login` | Login form |
| `POST` | `/auth/login` | Submit login |
| `GET` | `/auth/logout` | Logout (clears cookie) |

### Dashboard (authenticated)

| Method | Path | Description |
|---|---|---|
| `GET` | `/dashboard` | Dashboard home |
| `GET/POST` | `/dashboard/help-centers/new` | Create help center |
| `GET` | `/dashboard/help-centers/{id}` | Help center detail |
| `GET/POST` | `/dashboard/help-centers/{id}/edit` | Edit help center |
| `POST` | `/dashboard/help-centers/{id}/delete` | Delete help center |
| `GET` | `/dashboard/help-centers/{id}/analytics` | Analytics dashboard |
| `GET` | `/dashboard/help-centers/{id}/widget` | Widget embed code |
| `GET/POST` | `/dashboard/help-centers/{id}/categories/new` | Create category |
| `GET/POST` | `/dashboard/help-centers/{id}/categories/{cid}/edit` | Edit category |
| `POST` | `/dashboard/help-centers/{id}/categories/{cid}/delete` | Delete category |
| `POST` | `/dashboard/help-centers/{id}/categories/reorder` | Reorder categories (JSON) |
| `GET` | `/dashboard/help-centers/{id}/articles` | List articles |
| `GET/POST` | `/dashboard/help-centers/{id}/articles/new` | Create article |
| `GET` | `/dashboard/help-centers/{id}/articles/{aid}` | Article detail |
| `GET/POST` | `/dashboard/help-centers/{id}/articles/{aid}/edit` | Edit article |
| `POST` | `/dashboard/help-centers/{id}/articles/{aid}/delete` | Delete article |
| `POST` | `/dashboard/help-centers/{id}/articles/{aid}/toggle-publish` | Toggle publish status |
| `POST` | `/dashboard/help-centers/{id}/articles/preview-markdown` | Markdown preview (JSON) |

---

## Project Structure

```
help-base/
├── src/helpbase/
│   ├── app.py              # FastAPI app, lifespan, error handlers, routes
│   ├── config.py           # Pydantic settings (env vars)
│   ├── database.py         # Async SQLAlchemy engine + session
│   ├── dependencies.py     # Auth dependencies (get_current_user)
│   ├── models/             # SQLAlchemy models (User, HelpCenter, Category, Article, etc.)
│   ├── routers/            # Route handlers (auth, dashboard, articles, public, widget)
│   ├── schemas/            # Pydantic request/response schemas
│   ├── services/           # Business logic (auth, article, search, analytics, etc.)
│   └── templates/          # Jinja2 HTML templates (layouts, dashboard, public, auth)
├── tests/                  # 148 pytest tests
├── alembic/                # Database migrations
├── Dockerfile              # Multi-stage production build
├── docker-compose.yml      # Docker Compose config
├── .env.example            # Documented environment variables
└── pyproject.toml          # Dependencies and tool config
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Install dev dependencies: `uv pip install -e ".[dev]"`
4. Make your changes
5. Run the test suite: `python -m pytest tests/ -v`
6. Run the linter: `ruff check src/ tests/`
7. Commit and open a pull request

---

## License

MIT
