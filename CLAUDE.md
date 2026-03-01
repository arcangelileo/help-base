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
- [x] Implement help center CRUD (API + dashboard UI)
- [x] Implement category CRUD (API + dashboard UI)
- [x] Implement article CRUD with Markdown editor and live preview
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

### Session 4 — HELP CENTER & CATEGORY CRUD
- Help center service: create, read, update, delete with auto-slugification and unique slug resolution
- Category service: create, read, update, delete, reorder with display_order tracking
- Help center router with full CRUD: new/create, detail, edit/update, delete
- Category router nested under help centers: new/create, edit/update, delete, reorder API
- Reusable dashboard layout template (shared nav, breadcrumbs across all dashboard pages)
- Help center create/edit forms: name, description, brand color picker with presets
- Help center detail page: stats cards (categories, articles, uncategorized), category list with article counts
- Category create/edit forms: name, description, emoji icon picker with presets
- Delete confirmation dialogs for both help centers and categories
- Authorization guards: users can only manage their own help centers and categories
- 18 help center tests + 16 category tests covering CRUD, validation, slugification, authorization, empty states
- All 68 tests passing

### Session 5 — ARTICLE CRUD
- Article service: create, read, update, delete with auto-slugification, unique slug resolution, markdown rendering (pymdown-extensions), revision tracking (last 10 revisions)
- Article router: list, create, detail (with rendered markdown), edit, delete, toggle publish/unpublish, markdown preview API
- Article list template: shows all articles with title, slug, category, publish status (Published/Draft badges), view count, empty state
- Article create template (new.html): Markdown editor with Write/Preview/Split view tabs, live client-side preview (marked.js), category select dropdown, excerpt field, publish checkbox, tab-key support in editor
- Article detail template: rendered markdown content with styled prose (headings, code blocks, tables, lists, blockquotes), excerpt display, publish/unpublish toggle button, edit/delete actions, breadcrumb navigation, empty content state
- Article edit template: pre-populated Markdown editor with same Write/Preview/Split functionality, danger zone with delete confirmation
- Help center detail page: added "New Article" and "Manage Articles" quick action buttons, articles stat card links to articles list
- Fixed routers/__init__.py to register the articles router
- Fixed bcrypt compatibility issue with Python 3.13 (downgraded to bcrypt 4.1.3)
- 31 new article tests: list (empty/populated/publish status), create (success, markdown rendering, published/draft, validation, slugification, duplicate slugs), detail (info, actions, nonexistent, empty content), edit (renders, update title/content, validation, preserve data on error), delete, toggle publish (both directions), markdown preview API, authorization (other user cannot access), help center detail articles link
- All 99 tests passing

## Known Issues
- bcrypt 5.0 incompatible with passlib on Python 3.13 — pinned to bcrypt 4.1.3

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
│       │   ├── articles.py         # Article CRUD routes + markdown preview API
│       │   ├── dashboard.py        # Dashboard routes (index with stats)
│       │   └── help_centers.py     # Help center + category CRUD routes
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── auth.py             # Auth Pydantic schemas
│       ├── services/
│       │   ├── __init__.py
│       │   ├── auth.py             # Auth service (password, JWT, user CRUD)
│       │   ├── article.py          # Article CRUD service + markdown rendering
│       │   ├── helpcenter.py       # Help center CRUD service
│       │   └── category.py         # Category CRUD service
│       ├── templates/
│       │   ├── layouts/
│       │   │   ├── base.html       # Base template (Tailwind + Inter + HTMX)
│       │   │   └── dashboard.html  # Shared dashboard layout (nav, user menu)
│       │   ├── auth/
│       │   │   ├── login.html      # Login page
│       │   │   └── register.html   # Registration page
│       │   ├── dashboard/
│       │   │   ├── index.html      # Dashboard with stats and help center list
│       │   │   └── help_centers/
│       │   │       ├── new.html    # Create help center form
│       │   │       ├── detail.html # Help center detail with categories
│       │   │       ├── edit.html   # Edit help center form + danger zone
│       │   │       ├── categories/
│       │   │       │   ├── new.html  # Create category form
│       │   │       │   └── edit.html # Edit category form + danger zone
│       │   │       └── articles/
│       │   │           ├── list.html   # Article list with status badges
│       │   │           ├── new.html    # Create article with Markdown editor
│       │   │           ├── detail.html # Article detail with rendered markdown
│       │   │           └── edit.html   # Edit article with Markdown editor
│       │   └── landing.html        # Landing page with hero, features, pricing
│       └── static/
│           ├── css/
│           ├── js/
│           └── img/
└── tests/
    ├── __init__.py
    ├── conftest.py                 # Async test fixtures (db, client)
    ├── test_articles.py             # Article CRUD tests (31)
    ├── test_auth.py                # Auth tests (27)
    ├── test_categories.py          # Category CRUD tests (16)
    ├── test_health.py              # Health check + landing page tests (4)
    ├── test_help_centers.py        # Help center CRUD tests (18)
    └── test_models.py              # Model CRUD tests (3)
```
