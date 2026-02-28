# HelpBase

Phase: DEVELOPMENT

## Project Spec
- **Repo**: https://github.com/arcangelileo/help-base
- **Idea**: HelpBase is a lightweight knowledge base and help center SaaS that lets businesses create beautiful, searchable help documentation for their customers. Users create a help center, organize articles into categories, and publish them on a branded public-facing site. Built-in analytics show which articles get the most views, what users search for, and where documentation gaps exist. An embeddable widget lets customers search help docs without leaving the product.
- **Target users**: SaaS companies, startups, and small businesses that need customer-facing documentation but don't want to pay $50+/mo for Zendesk Guide or Intercom Articles. Also freelancers and agencies managing docs for multiple clients.
- **Revenue model**: Freemium SaaS — Free tier (1 help center, 25 articles, HelpBase branding), Pro $12/mo (3 help centers, unlimited articles, custom branding, analytics), Business $29/mo (unlimited help centers, custom domain, embeddable widget, API access, priority support).
- **Tech stack**: Python 3.11+, FastAPI, SQLite (via async SQLAlchemy + aiosqlite), Jinja2 templates, Tailwind CSS via CDN, HTMX for interactivity, APScheduler for background jobs, Docker
- **MVP scope**:
  1. User auth (register, login, logout) with JWT httponly cookies
  2. Help center CRUD (name, slug, branding colors, logo)
  3. Category CRUD (name, description, display order)
  4. Article CRUD with Markdown editor and live preview
  5. Public-facing help center with article rendering, category navigation, and full-text search
  6. Article analytics (view counts, popular articles dashboard)
  7. Embeddable search widget (JS snippet)
  8. Admin dashboard with analytics overview

## Architecture Decisions
- **Markdown for articles**: Store raw Markdown, render to HTML on read. Use `markdown` + `pymdown-extensions` for rich formatting (code blocks, tables, callouts). This is simpler than a WYSIWYG editor and developers love Markdown.
- **Full-text search**: Use SQLite FTS5 for article search. Fast, zero-dependency, perfect for MVP scale. Upgrade path to PostgreSQL full-text or Elasticsearch later.
- **Public help center routing**: Each help center gets a slug-based URL (`/h/{slug}/`). Articles are accessed via `/h/{slug}/articles/{article-slug}`. Custom domains are a post-MVP feature.
- **Embeddable widget**: Simple JS snippet that creates an iframe with search functionality. Served from our domain. Minimal JS, no framework needed.
- **Article versioning**: Track last 10 revisions per article for undo/history. Simple JSON column or separate revisions table.
- **Async SQLAlchemy + aiosqlite**: Consistent with factory conventions. Alembic for migrations.
- **JWT auth with httponly cookies**: Consistent with factory conventions. bcrypt for password hashing.
- **Tailwind CSS via CDN + Inter font**: For both admin dashboard and public help center pages. Public pages get customizable accent colors.
- **APScheduler**: For periodic analytics aggregation (daily rollups of view counts).
- **Pydantic Settings**: Configuration via environment variables.

## Task Backlog
- [x] Create project structure (pyproject.toml, src layout, configs)
- [x] Set up FastAPI app skeleton with health check, config, and database
- [x] Set up Alembic migrations and create initial models (User, HelpCenter, Category, Article, ArticleView)
- [x] Implement user authentication (register, login, logout, JWT)
- [x] Build auth UI pages (login, register) with Tailwind styling
- [ ] Implement help center CRUD (API + dashboard UI)
- [ ] Implement category CRUD (API + dashboard UI)
- [ ] Implement article CRUD with Markdown editor and live preview
- [ ] Build public-facing help center (article rendering, category nav, search)
- [ ] Implement SQLite FTS5 search for articles
- [ ] Add article view tracking and analytics dashboard
- [ ] Build embeddable search widget (JS snippet + iframe endpoint)
- [ ] Write comprehensive tests (auth, CRUD, search, public pages)
- [ ] Write Dockerfile and docker-compose.yml
- [ ] Write README with setup and deploy instructions

## Progress Log
### Session 1 — IDEATION
- Chose idea: HelpBase — Knowledge Base & Help Center SaaS
- Created spec and backlog
- Rationale: Every SaaS needs help docs, proven market (Zendesk Guide, Intercom Articles, HelpScout Docs), clear freemium model, mostly CRUD + search + rendering which fits well in 10-15 sessions

### Session 2 — SCAFFOLDING
- Created GitHub repo: https://github.com/arcangelileo/help-base
- Set up project structure: pyproject.toml with all dependencies, src/ layout
- Created all SQLAlchemy models: User, HelpCenter, Category, Article, ArticleRevision, ArticleView
- Set up async database layer (SQLAlchemy + aiosqlite)
- Created FastAPI app with health check endpoint and polished landing page (Tailwind CSS + Inter font, hero, features, pricing sections)
- Set up Alembic for async migrations, generated initial schema migration
- Created Jinja2 base template layout with Tailwind CDN
- Built test infrastructure: conftest with async fixtures, 7 tests all passing (health check, landing page, model CRUD)
- Python 3.13 environment with uv for package management

### Session 3 — AUTH
- Implemented full user authentication: register, login, logout with JWT httponly cookies
- Auth service: bcrypt password hashing, JWT token creation/validation, user lookup/create
- Auth dependencies: `get_current_user` (protected routes), `get_optional_user` (guest-friendly routes)
- Auth router: GET/POST register, GET/POST login, GET logout — all with form validation and error handling
- Dashboard router: authenticated dashboard page with stats (help centers, articles, views) and empty state
- Beautiful Tailwind-styled auth pages: register form (name, email, password, confirm), login form (email, password)
- Error display with preserved form data, auto-redirect when already logged in
- Landing page updated to show auth state (Dashboard/Sign out vs Sign in/Get Started)
- Added email-validator dependency for Pydantic EmailStr support
- 27 new auth tests (password hashing, JWT tokens, registration flows, login flows, logout, dashboard access, auth redirects, email normalization, landing page auth state)
- All 34 tests passing

## Known Issues
(none yet)

## Files Structure
```
help-base/
├── CLAUDE.md
├── pyproject.toml
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 2ae0792c0c24_initial_schema.py
├── src/
│   └── helpbase/
│       ├── __init__.py
│       ├── app.py                  # FastAPI app, health check, landing page
│       ├── config.py               # Pydantic settings
│       ├── database.py             # Async SQLAlchemy engine + session
│       ├── models/
│       │   ├── __init__.py
│       │   ├── base.py             # Base, TimestampMixin, UUIDPrimaryKeyMixin
│       │   ├── user.py             # User model
│       │   ├── helpcenter.py       # HelpCenter model
│       │   ├── category.py         # Category model
│       │   ├── article.py          # Article + ArticleRevision models
│       │   └── analytics.py        # ArticleView model
│       ├── dependencies.py          # Auth dependencies (get_current_user, get_optional_user)
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── auth.py             # Auth routes (register, login, logout)
│       │   └── dashboard.py        # Dashboard routes (index with stats)
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── auth.py             # Auth Pydantic schemas
│       ├── services/
│       │   ├── __init__.py
│       │   └── auth.py             # Auth service (password, JWT, user CRUD)
│       ├── templates/
│       │   ├── layouts/
│       │   │   └── base.html       # Base template (Tailwind + Inter + HTMX)
│       │   ├── auth/
│       │   │   ├── login.html      # Login page
│       │   │   └── register.html   # Registration page
│       │   ├── dashboard/
│       │   │   └── index.html      # Dashboard with stats and help center list
│       │   └── landing.html        # Landing page with hero, features, pricing
│       └── static/
│           ├── css/
│           ├── js/
│           └── img/
└── tests/
    ├── __init__.py
    ├── conftest.py                 # Async test fixtures (db, client)
    ├── test_auth.py                # Auth tests (27)
    ├── test_health.py              # Health check + landing page tests (4)
    └── test_models.py              # Model CRUD tests (3)
```
