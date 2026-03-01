"""Tests for the embeddable search widget — JS snippet, search API, dashboard page."""

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


async def create_article(
    client: AsyncClient,
    hc_id: str,
    title: str = "Test Article",
    content: str = "# Hello\n\nArticle content here.",
    is_published: str = "on",
) -> str:
    """Create an article and return its ID."""
    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/articles/new",
        data={
            "title": title,
            "content_markdown": content,
            "excerpt": f"Excerpt for {title}",
            "category_id": "",
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
    import re
    match = re.search(r'/h/([\w-]+)', resp.text)
    return match.group(1) if match else "test-hc"


# ============================================================
# Widget JavaScript Snippet
# ============================================================


async def test_widget_js_serves_javascript(client: AsyncClient):
    """GET /widget/{slug}/embed.js should return JavaScript content."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Widget JS HC")
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/widget/{slug}/embed.js")
    assert resp.status_code == 200
    assert "application/javascript" in resp.headers["content-type"]
    assert "__helpbase_widget_loaded" in resp.text


async def test_widget_js_contains_slug(client: AsyncClient):
    """Widget JS should reference the correct help center slug."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Slug Widget HC")
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/widget/{slug}/embed.js")
    assert resp.status_code == 200
    assert slug in resp.text


async def test_widget_js_contains_brand_color(client: AsyncClient):
    """Widget JS should use the help center's brand color."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Color Widget HC")
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/widget/{slug}/embed.js")
    assert resp.status_code == 200
    assert "#4F46E5" in resp.text


async def test_widget_js_contains_hc_name(client: AsyncClient):
    """Widget JS should include the help center name."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Named Widget HC")
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/widget/{slug}/embed.js")
    assert resp.status_code == 200
    assert "Named Widget HC" in resp.text


async def test_widget_js_cors_headers(client: AsyncClient):
    """Widget JS should have CORS headers for cross-origin embedding."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="CORS Widget HC")
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/widget/{slug}/embed.js")
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "*"


async def test_widget_js_nonexistent_hc(client: AsyncClient):
    """Widget JS for nonexistent HC should return comment with 200."""
    resp = await client.get("/widget/nonexistent-slug/embed.js")
    assert resp.status_code == 200
    assert "Help center not found" in resp.text


async def test_widget_js_has_search_functionality(client: AsyncClient):
    """Widget JS should contain search event listener code."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Search Widget HC")
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/widget/{slug}/embed.js")
    assert resp.status_code == 200
    assert "addEventListener" in resp.text
    assert "helpbase-search-input" in resp.text
    assert "Escape" in resp.text


# ============================================================
# Widget Search API
# ============================================================


async def test_widget_search_returns_json(client: AsyncClient):
    """GET /widget/{slug}/search should return JSON results."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Widget Search HC")
    await create_article(
        client, hc_id,
        title="Widget Searchable Article",
        content="This article is about widget configuration.",
        is_published="on",
    )
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/widget/{slug}/search?q=widget")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert "query" in data


async def test_widget_search_cors_headers(client: AsyncClient):
    """Widget search API should include CORS headers."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="CORS Search HC")
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/widget/{slug}/search?q=test")
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "*"


async def test_widget_search_empty_query(client: AsyncClient):
    """Widget search with empty query should return empty results."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Empty Query HC")
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/widget/{slug}/search?q=")
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"] == []


async def test_widget_search_nonexistent_hc(client: AsyncClient):
    """Widget search for nonexistent help center should return 404."""
    resp = await client.get("/widget/nonexistent/search?q=test")
    assert resp.status_code == 404
    data = resp.json()
    assert "error" in data


async def test_widget_search_excludes_drafts(client: AsyncClient):
    """Widget search should not return draft articles."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Draft Search HC")
    await create_article(
        client, hc_id,
        title="Published Widget Article",
        content="This article about widgets is published.",
        is_published="on",
    )
    await create_article(
        client, hc_id,
        title="Draft Widget Article",
        content="This article about widgets is a draft.",
        is_published="",
    )
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/widget/{slug}/search?q=widgets")
    assert resp.status_code == 200
    data = resp.json()
    titles = [r["title"] for r in data["results"]]
    assert "Draft Widget Article" not in titles


async def test_widget_search_results_have_urls(client: AsyncClient):
    """Widget search results should include article URLs."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="URL Search HC")
    await create_article(
        client, hc_id,
        title="URL Test Article",
        content="Content about URL generation for search results.",
        is_published="on",
    )
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.get(f"/widget/{slug}/search?q=URL")
    assert resp.status_code == 200
    data = resp.json()
    if data["results"]:
        assert "url" in data["results"][0]
        assert f"/h/{slug}/articles/" in data["results"][0]["url"]


async def test_widget_cors_preflight(client: AsyncClient):
    """OPTIONS /widget/{slug}/search should handle CORS preflight."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Preflight HC")
    slug = await get_hc_slug(client, hc_id)

    client.cookies.clear()
    resp = await client.options(f"/widget/{slug}/search")
    assert resp.status_code == 204
    assert resp.headers.get("access-control-allow-origin") == "*"
    assert "GET" in resp.headers.get("access-control-allow-methods", "")


# ============================================================
# Widget Dashboard Page
# ============================================================


async def test_widget_page_requires_auth(client: AsyncClient):
    """Widget embed page should require authentication."""
    resp = await client.get(
        "/dashboard/help-centers/fake-id/widget",
        follow_redirects=False,
    )
    assert resp.status_code in (303, 401)


async def test_widget_page_renders(client: AsyncClient):
    """Widget embed page should render with embed code."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Widget Page HC")

    resp = await client.get(f"/dashboard/help-centers/{hc_id}/widget")
    assert resp.status_code == 200
    assert "Embed Widget" in resp.text or "Embeddable" in resp.text
    assert "embed.js" in resp.text
    assert "Installation" in resp.text


async def test_widget_page_shows_correct_snippet(client: AsyncClient):
    """Widget page should show the correct embed code for the help center."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Snippet HC")
    slug = await get_hc_slug(client, hc_id)

    resp = await client.get(f"/dashboard/help-centers/{hc_id}/widget")
    assert resp.status_code == 200
    assert slug in resp.text
    assert "embed.js" in resp.text


async def test_widget_page_other_user_redirects(client: AsyncClient):
    """User should not be able to view another user's widget page."""
    await register_and_login(client, email="owner@example.com")
    hc_id = await create_help_center(client, name="Owner Widget HC")

    client.cookies.clear()
    await register_and_login(client, email="attacker@example.com")

    resp = await client.get(
        f"/dashboard/help-centers/{hc_id}/widget",
        follow_redirects=False,
    )
    assert resp.status_code == 303


async def test_widget_page_nonexistent_hc(client: AsyncClient):
    """Widget page for nonexistent HC should redirect."""
    await register_and_login(client)
    resp = await client.get(
        "/dashboard/help-centers/fake-id/widget",
        follow_redirects=False,
    )
    assert resp.status_code == 303


async def test_help_center_detail_has_widget_link(client: AsyncClient):
    """Help center detail page should have an Embed Widget link."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Widget Link HC")

    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    assert resp.status_code == 200
    assert "Embed Widget" in resp.text
    assert f"/widget" in resp.text


async def test_widget_page_has_how_it_works(client: AsyncClient):
    """Widget page should have How It Works section."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="How It Works HC")

    resp = await client.get(f"/dashboard/help-centers/{hc_id}/widget")
    assert resp.status_code == 200
    assert "How It Works" in resp.text
    assert "Add the Script" in resp.text


async def test_widget_page_has_preview(client: AsyncClient):
    """Widget page should have a preview section."""
    await register_and_login(client)
    hc_id = await create_help_center(client, name="Preview HC")

    resp = await client.get(f"/dashboard/help-centers/{hc_id}/widget")
    assert resp.status_code == 200
    assert "Preview" in resp.text
