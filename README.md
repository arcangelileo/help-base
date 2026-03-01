# HelpBase

Lightweight knowledge base and help center SaaS. Create beautiful, searchable help documentation for your customers — organized into categories, published on a branded public site, with built-in analytics and an embeddable search widget.

## Features

- **Help Center Management** — Create multiple help centers with custom branding (name, description, accent color)
- **Category Organization** — Organize articles into categories with icons, descriptions, and drag-to-reorder
- **Markdown Editor** — Write articles in Markdown with live preview, code highlighting, tables, and task lists
- **Public Help Center** — Branded public-facing site at `/h/{slug}` with category navigation and full-text search
- **Full-Text Search** — SQLite FTS5 with porter stemming, prefix matching, and highlighted snippets
- **Article Analytics** — View counts, popular articles, top search queries, and recent activity dashboard
- **Embeddable Widget** — Drop-in JavaScript snippet adds a floating search widget to any website
- **User Authentication** — JWT-based auth with httponly cookies, bcrypt password hashing
- **Docker Ready** — Single-command deployment with Docker Compose

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, async SQLAlchemy + aiosqlite
- **Database:** SQLite with FTS5 full-text search
- **Frontend:** Jinja2 templates, Tailwind CSS (CDN), HTMX
- **Auth:** JWT (python-jose) + bcrypt (passlib)
- **Markdown:** python-markdown + pymdown-extensions
- **Tests:** pytest + pytest-asyncio (148 tests)

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Local Development

```bash
# Clone the repository
git clone https://github.com/arcangelileo/help-base.git
cd help-base

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Pin bcrypt for Python 3.13 compatibility
uv pip install "bcrypt==4.1.3"

# Create a .env file (optional — defaults work for development)
cat > .env << 'EOF'
HELPBASE_SECRET_KEY=your-secret-key-here
HELPBASE_DEBUG=true
HELPBASE_BASE_URL=http://localhost:8000
EOF

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn helpbase.app:app --reload --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000](http://localhost:8000) to see the landing page. Register an account at `/auth/register` to start creating help centers.

### Docker

```bash
# Build and run with Docker Compose
docker compose up -d

# Or build manually
docker build -t helpbase .
docker run -p 8000:8000 -v helpbase-data:/app/data helpbase
```

The app will be available at [http://localhost:8000](http://localhost:8000).

## Configuration

All settings are configured via environment variables (prefix: `HELPBASE_`) or a `.env` file:

| Variable | Default | Description |
|---|---|---|
| `HELPBASE_SECRET_KEY` | `change-me-in-production-please` | JWT signing key — **change in production** |
| `HELPBASE_DEBUG` | `false` | Enable debug mode (Swagger docs at `/docs`) |
| `HELPBASE_BASE_URL` | `http://localhost:8000` | Public URL (used in widget embed code) |
| `HELPBASE_DATABASE_URL` | `sqlite+aiosqlite:///helpbase.db` | Database connection string |
| `HELPBASE_JWT_EXPIRE_MINUTES` | `10080` (7 days) | JWT token expiration |

## Running Tests

```bash
# Run all 148 tests
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=helpbase --cov-report=term-missing

# Run a specific test file
python -m pytest tests/test_widget.py -v
```

Test files:
- `test_auth.py` — Authentication (27 tests)
- `test_help_centers.py` — Help center CRUD (18 tests)
- `test_categories.py` — Category CRUD (16 tests)
- `test_articles.py` — Article CRUD (31 tests)
- `test_public.py` — Public pages, search, analytics (27 tests)
- `test_widget.py` — Embeddable widget (22 tests)
- `test_health.py` — Health check, landing page (4 tests)
- `test_models.py` — Model CRUD (3 tests)

## Project Structure

```
help-base/
├── src/helpbase/
│   ├── app.py              # FastAPI app, lifespan, routes
│   ├── config.py            # Pydantic settings
│   ├── database.py          # Async SQLAlchemy engine
│   ├── dependencies.py      # Auth dependencies
│   ├── models/              # SQLAlchemy models
│   ├── routers/             # API route handlers
│   ├── services/            # Business logic layer
│   └── templates/           # Jinja2 HTML templates
├── tests/                   # pytest test suite
├── alembic/                 # Database migrations
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Embeddable Widget

Add the search widget to any website with a single script tag:

```html
<!-- HelpBase Search Widget -->
<script src="https://your-domain.com/widget/your-slug/embed.js" async></script>
```

The widget creates a floating help button that opens a search panel. It automatically matches your help center's brand color, performs real-time search with debouncing, and links directly to your published articles.

## API Endpoints

### Public

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/h/{slug}` | Public help center home |
| `GET` | `/h/{slug}/articles/{article-slug}` | Public article page |
| `GET` | `/h/{slug}/category/{cat-slug}` | Public category page |
| `GET` | `/h/{slug}/search?q=` | Search page |
| `GET` | `/h/{slug}/search/api?q=` | JSON search API |
| `GET` | `/widget/{slug}/embed.js` | Widget JavaScript |
| `GET` | `/widget/{slug}/search?q=` | Widget search API (CORS) |

### Authenticated (Dashboard)

| Method | Path | Description |
|---|---|---|
| `GET/POST` | `/auth/register` | User registration |
| `GET/POST` | `/auth/login` | User login |
| `GET` | `/auth/logout` | User logout |
| `GET` | `/dashboard` | Dashboard home |
| `GET/POST` | `/dashboard/help-centers/new` | Create help center |
| `GET` | `/dashboard/help-centers/{id}` | Help center detail |
| `GET/POST` | `/dashboard/help-centers/{id}/edit` | Edit help center |
| `POST` | `/dashboard/help-centers/{id}/delete` | Delete help center |
| `GET` | `/dashboard/help-centers/{id}/analytics` | Analytics dashboard |
| `GET` | `/dashboard/help-centers/{id}/widget` | Widget embed code |
| `GET/POST` | `/dashboard/help-centers/{id}/categories/new` | Create category |
| `GET/POST` | `/dashboard/help-centers/{id}/categories/{cat-id}/edit` | Edit category |
| `GET/POST` | `/dashboard/help-centers/{id}/articles/new` | Create article |
| `GET` | `/dashboard/help-centers/{id}/articles/{art-id}` | Article detail |
| `GET/POST` | `/dashboard/help-centers/{id}/articles/{art-id}/edit` | Edit article |

## License

MIT
