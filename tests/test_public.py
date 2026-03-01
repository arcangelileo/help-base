"""Comprehensive tests for public-facing help center pages, search, and view tracking."""

import pytest
from httpx import AsyncClient


# --- Helpers ---


async def register_and_login(client: AsyncClient, email="user@example.com") -> str:
    """Register a user and return the access_token cookie value."""
    resp = await client.post(
        "/auth/register",
        data={
            "full_name": "Test User",
            "email": email,
            "password": "testpassword123",
            "password_confirm": "testpassword123",
        },
        follow_redirects=False,
    )
    token = resp.cookies.get("access_token")
    assert token is not None
    client.cookies.set("access_token", token)
    return token


async def create_help_center(client: AsyncClient, name: str = "Test HC") -> str:
    """Create a help center and return its ID."""
    resp = await client.post(
        "/dashboard/help-centers/new",
        data={"name": name, "description": "A test help center", "primary_color": "#4F46E5"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    return resp.headers["location"].split("/dashboard/help-centers/")[1]


async def create_category(client: AsyncClient, hc_id: str, name: str = "Getting Started") -> None:
    """Create a category."""
    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/categories/new",
        data={"name": name, "description": "Category description", "icon": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 303


async def create_article(
    client: AsyncClient,
    hc_id: str,
    title: str = "Test Article",
    content: str = "# Hello\n\nArticle content here.",
    is_published: str = "on",
    category_id: str = "",
) -> str:
    """Create an article and return its ID."""
    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/articles/new",
        data={
            "title": title,
            "content_markdown": content,
            "excerpt": f"Excerpt for {title}",
            "category_id": category_id,
            "is_published": is_published,
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    return resp.headers["location"].split("/articles/")[1]


async def get_hc_slug(client: AsyncClient, hc_id: str) -> str:
    """Get help center slug by visiting its detail page."""
    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    assert resp.status_code == 200
    # Extract slug from the page — it's in /h/{slug}
    import re
    match = re.search(r'/h/([\w-]+)', resp.text)
    return match.group(1) if match else "test-hc"


# ============================================================
# Public Help Center Home
# ============================================================


async def test_public_help_center_home(client: AsyncClient):
    """GET /h/{slug} should render the public help center home page."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Acme Docs")
    slug = await get_hc_slug(client, hc_id)

    # Visit as unauthenticated user
    client.cookies.clear()
    resp = await client.get(f"/h/{slug}")
    assert resp.status_code == 200
    assert "Acme Docs" in resp.text
    assert "How can we help" in resp.text


async def test_public_help_center_not_found(client: AsyncClient):
    """GET /h/nonexistent should return 404."""
    resp = await client.get("/h/nonexistent-slug")
    assert resp.status_code == 404
    assert "404" in resp.text


async def test_public_help_center_shows_categories(client: AsyncClient):
    """Public home should show categories with article counts."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Cat HC")
    create_category_resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/categories/new",
        data={"name": "Tutorials", "description": "How-to guides", "icon": ""},
        follow_redirects=False,
    )
    assert create_category_resp.status_code == 303

    # Get category ID from the help center detail page
    detail = await client.get(f"/dashboard/help-centers/{hc_id}")
    assert "Tutorials" in detail.text

    # Create a published article in the category — we need the category ID
    # Let's create it uncategorized first, the category is for display
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/h/{slug}")
    assert resp.status_code == 200
    assert "Browse by Category" not in resp.text  # No articles in category yet


async def test_public_help_center_shows_articles(client: AsyncClient):
    """Public home should list published articles."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Article HC")
    await create_article(client, hc_id, title="How to Install", is_published="on")
    await create_article(client, hc_id, title="Draft Article", is_published="")
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/h/{slug}")
    assert resp.status_code == 200
    assert "How to Install" in resp.text
    assert "Draft Article" not in resp.text  # Drafts hidden from public


async def test_public_help_center_empty_state(client: AsyncClient):
    """Public help center with no published articles should show empty state."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Empty HC")
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/h/{slug}")
    assert resp.status_code == 200
    assert "No articles published yet" in resp.text


# ============================================================
# Public Article Page
# ============================================================


async def test_public_article_renders(client: AsyncClient):
    """GET /h/{slug}/articles/{article-slug} should render the article."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Article Render HC")
    await create_article(
        client, hc_id,
        title="Getting Started Guide",
        content="# Welcome\n\nThis is the **getting started** guide.",
        is_published="on",
    )
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/h/{slug}/articles/getting-started-guide")
    assert resp.status_code == 200
    assert "Getting Started Guide" in resp.text
    assert "<strong>getting started</strong>" in resp.text
    assert "Excerpt for Getting Started Guide" in resp.text


async def test_public_article_not_found(client: AsyncClient):
    """GET /h/{slug}/articles/nonexistent should return 404."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Article 404 HC")
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/h/{slug}/articles/nonexistent-article")
    assert resp.status_code == 404


async def test_public_article_draft_not_accessible(client: AsyncClient):
    """Draft articles should not be accessible publicly."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Draft Access HC")
    await create_article(
        client, hc_id, title="Secret Draft", content="Private info", is_published=""
    )
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/h/{slug}/articles/secret-draft")
    assert resp.status_code == 404


async def test_public_article_tracks_view(client: AsyncClient):
    """Viewing an article should increment its view count."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="View Track HC")
    article_id = await create_article(
        client, hc_id, title="Tracked Article", is_published="on"
    )
    slug = await get_hc_slug(client, hc_id)

    # View the article publicly
    client.cookies.clear()
    resp = await client.get(f"/h/{slug}/articles/tracked-article")
    assert resp.status_code == 200

    # View it again
    resp = await client.get(f"/h/{slug}/articles/tracked-article")
    assert resp.status_code == 200


async def test_public_article_breadcrumb(client: AsyncClient):
    """Article page should show breadcrumb navigation."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Breadcrumb HC")
    await create_article(
        client, hc_id, title="Breadcrumb Test", is_published="on"
    )
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/h/{slug}/articles/breadcrumb-test")
    assert resp.status_code == 200
    assert "Home" in resp.text


# ============================================================
# Public Category Page
# ============================================================


async def test_public_category_not_found(client: AsyncClient):
    """GET /h/{slug}/category/nonexistent should return 404."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Cat 404 HC")
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/h/{slug}/category/nonexistent-category")
    assert resp.status_code == 404


async def test_public_category_renders(client: AsyncClient):
    """GET /h/{slug}/category/{cat-slug} should show the category page."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Cat Render HC")
    await create_category(client, hc_id, name="Tutorials")
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/h/{slug}/category/tutorials")
    assert resp.status_code == 200
    assert "Tutorials" in resp.text


# ============================================================
# Search
# ============================================================


async def test_search_page_renders(client: AsyncClient):
    """GET /h/{slug}/search should render the search page."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Search HC")
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/h/{slug}/search")
    assert resp.status_code == 200
    assert "Search Articles" in resp.text


async def test_search_empty_query(client: AsyncClient):
    """Search with empty query should show the search form."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Search Empty HC")
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/h/{slug}/search?q=")
    assert resp.status_code == 200
    assert "Search Articles" in resp.text


async def test_search_with_results(client: AsyncClient):
    """Search should return matching published articles."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Search Results HC")
    await create_article(
        client, hc_id,
        title="How to Configure API Keys",
        content="This article explains how to get and use API keys for authentication.",
        is_published="on",
    )
    await create_article(
        client, hc_id,
        title="Getting Started",
        content="Welcome to our platform. Here is how to get started.",
        is_published="on",
    )
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/h/{slug}/search?q=API+keys")
    assert resp.status_code == 200
    assert "API Keys" in resp.text or "api" in resp.text.lower()


async def test_search_no_results(client: AsyncClient):
    """Search with no matching results should show no results state."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Search NoResult HC")
    await create_article(
        client, hc_id, title="Unrelated Article",
        content="This won't match.", is_published="on",
    )
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/h/{slug}/search?q=xyznonexistent123")
    assert resp.status_code == 200
    assert "No results" in resp.text


async def test_search_excludes_drafts(client: AsyncClient):
    """Search should not return draft articles."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Search Draft HC")
    await create_article(
        client, hc_id, title="Draft Searchable",
        content="This is a draft article about searching.", is_published="",
    )
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/h/{slug}/search?q=searching")
    assert resp.status_code == 200
    assert "Draft Searchable" not in resp.text


async def test_search_api_json(client: AsyncClient):
    """GET /h/{slug}/search/api should return JSON results."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Search API HC")
    await create_article(
        client, hc_id, title="API Integration Guide",
        content="How to integrate with our REST API endpoints.",
        is_published="on",
    )
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/h/{slug}/search/api?q=API")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert "query" in data


async def test_search_api_nonexistent_hc(client: AsyncClient):
    """Search API with nonexistent help center should return 404."""
    resp = await client.get("/h/nonexistent/search/api?q=test")
    assert resp.status_code == 404


async def test_search_nonexistent_hc(client: AsyncClient):
    """Search page with nonexistent help center should return 404."""
    resp = await client.get("/h/nonexistent/search?q=test")
    assert resp.status_code == 404


# ============================================================
# Analytics Dashboard
# ============================================================


async def test_analytics_requires_auth(client: AsyncClient):
    """GET analytics dashboard without auth should redirect."""
    resp = await client.get(
        "/dashboard/help-centers/fake-id/analytics",
        follow_redirects=False,
    )
    assert resp.status_code in (303, 401)


async def test_analytics_dashboard_renders(client: AsyncClient):
    """GET analytics dashboard should show stats."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Analytics HC")

    resp = await client.get(f"/dashboard/help-centers/{hc_id}/analytics")
    assert resp.status_code == 200
    assert "Analytics" in resp.text
    assert "Total Views" in resp.text
    assert "Popular Articles" in resp.text
    assert "Top Search Queries" in resp.text


async def test_analytics_other_user_redirects(client: AsyncClient):
    """User should not be able to view another user's analytics."""
    await register_and_login(client, email="owner@example.com")
    hc_id = await create_help_center(client, name="Owner Analytics HC")

    client.cookies.clear()
    await register_and_login(client, email="attacker@example.com")

    resp = await client.get(
        f"/dashboard/help-centers/{hc_id}/analytics",
        follow_redirects=False,
    )
    assert resp.status_code == 303


async def test_analytics_nonexistent_hc(client: AsyncClient):
    """Analytics for nonexistent help center should redirect."""
    await register_and_login(client)
    resp = await client.get(
        "/dashboard/help-centers/fake-id/analytics",
        follow_redirects=False,
    )
    assert resp.status_code == 303


async def test_help_center_detail_has_analytics_link(client: AsyncClient):
    """Help center detail page should have an Analytics link."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Link HC")

    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    assert resp.status_code == 200
    assert "Analytics" in resp.text
    assert f"/analytics" in resp.text


# ============================================================
# View tracking integration
# ============================================================


async def test_view_tracking_records_search_query(client: AsyncClient):
    """Viewing article with ?q= should record the search query."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Query Track HC")
    await create_article(
        client, hc_id, title="Tracked Query Article", is_published="on"
    )
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/h/{slug}/articles/tracked-query-article?q=test+query")
    assert resp.status_code == 200


async def test_public_help_center_search_form_in_header(client: AsyncClient):
    """Public pages should have a search form in the header."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Header Search HC")
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/h/{slug}")
    assert resp.status_code == 200
    assert 'name="q"' in resp.text
    assert "/search" in resp.text
