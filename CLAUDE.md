# HelpBase

Phase: SCAFFOLDING

## Project Spec
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
- [ ] Create project structure (pyproject.toml, src layout, configs)
- [ ] Set up FastAPI app skeleton with health check, config, and database
- [ ] Set up Alembic migrations and create initial models (User, HelpCenter, Category, Article, ArticleView)
- [ ] Implement user authentication (register, login, logout, JWT)
- [ ] Build auth UI pages (login, register) with Tailwind styling
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

## Known Issues
(none yet)

## Files Structure
(will be updated as files are created)
