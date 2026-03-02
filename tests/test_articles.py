"""Comprehensive tests for article CRUD."""

from httpx import AsyncClient


# --- Helper to register + get auth cookie ---


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
        data={"name": name, "description": "", "primary_color": "#4F46E5"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    location = resp.headers["location"]
    return location.split("/dashboard/help-centers/")[1]


async def create_category_via_form(
    client: AsyncClient,
    hc_id: str,
    name: str = "Getting Started",
) -> None:
    """Create a category via the form."""
    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/categories/new",
        data={"name": name, "description": "", "icon": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 303


async def create_article_via_form(
    client: AsyncClient,
    hc_id: str,
    title: str = "Test Article",
    content_markdown: str = "# Hello\n\nThis is a test article.",
    excerpt: str = "",
    category_id: str = "",
    is_published: str = "",
) -> str:
    """Create an article via the form and return its ID extracted from redirect."""
    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/articles/new",
        data={
            "title": title,
            "content_markdown": content_markdown,
            "excerpt": excerpt,
            "category_id": category_id,
            "is_published": is_published,
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    location = resp.headers["location"]
    # URL is /dashboard/help-centers/{hc_id}/articles/{article_id}
    article_id = location.split("/articles/")[1]
    return article_id


# ============================================================
# Article list page
# ============================================================


async def test_articles_list_requires_auth(client: AsyncClient):
    """GET articles list without auth should redirect."""
    resp = await client.get(
        "/dashboard/help-centers/fake-id/articles", follow_redirects=False
    )
    assert resp.status_code in (303, 401)


async def test_articles_list_empty_state(client: AsyncClient):
    """Articles list should show empty state when no articles exist."""
    await register_and_login(client)
    hc_id = await create_help_center(client)

    resp = await client.get(f"/dashboard/help-centers/{hc_id}/articles")
    assert resp.status_code == 200
    assert "No articles yet" in resp.text
    assert "Write Article" in resp.text


async def test_articles_list_shows_articles(client: AsyncClient):
    """Articles list should show created articles."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    await create_article_via_form(client, hc_id, title="My First Article")
    await create_article_via_form(client, hc_id, title="Second Article")

    resp = await client.get(f"/dashboard/help-centers/{hc_id}/articles")
    assert resp.status_code == 200
    assert "My First Article" in resp.text
    assert "Second Article" in resp.text
    assert "2 articles" in resp.text


async def test_articles_list_shows_publish_status(client: AsyncClient):
    """Articles list should show Draft/Published badges."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    await create_article_via_form(client, hc_id, title="Draft Article", is_published="")
    await create_article_via_form(
        client, hc_id, title="Published Article", is_published="on"
    )

    resp = await client.get(f"/dashboard/help-centers/{hc_id}/articles")
    assert resp.status_code == 200
    assert "Draft" in resp.text
    assert "Published" in resp.text


# ============================================================
# Article create page
# ============================================================


async def test_new_article_page_requires_auth(client: AsyncClient):
    """GET new article page without auth should redirect."""
    resp = await client.get(
        "/dashboard/help-centers/fake-id/articles/new", follow_redirects=False
    )
    assert resp.status_code in (303, 401)


async def test_new_article_page_renders(client: AsyncClient):
    """GET new article page should show the markdown editor form."""
    await register_and_login(client)
    hc_id = await create_help_center(client)

    resp = await client.get(f"/dashboard/help-centers/{hc_id}/articles/new")
    assert resp.status_code == 200
    assert "Write a New Article" in resp.text
    assert 'name="title"' in resp.text
    assert 'name="content_markdown"' in resp.text
    assert "Write" in resp.text  # Editor tab
    assert "Preview" in resp.text  # Editor tab


async def test_new_article_page_shows_categories(client: AsyncClient):
    """New article form should show category dropdown with existing categories."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    await create_category_via_form(client, hc_id, name="Tutorials")

    resp = await client.get(f"/dashboard/help-centers/{hc_id}/articles/new")
    assert resp.status_code == 200
    assert "Tutorials" in resp.text
    assert "Uncategorized" in resp.text


# ============================================================
# Article creation
# ============================================================


async def test_create_article_success(client: AsyncClient):
    """POST should create article and redirect to detail page."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    article_id = await create_article_via_form(
        client,
        hc_id,
        title="Getting Started Guide",
        content_markdown="# Welcome\n\nLearn how to get started.",
        excerpt="Quick start guide",
    )

    # Visit detail page
    resp = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}"
    )
    assert resp.status_code == 200
    assert "Getting Started Guide" in resp.text
    assert "Quick start guide" in resp.text


async def test_create_article_renders_markdown(client: AsyncClient):
    """Article detail should render markdown to HTML."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    article_id = await create_article_via_form(
        client,
        hc_id,
        title="Markdown Test",
        content_markdown="# Heading One\n\nSome **bold** text and *italic* too.",
    )

    resp = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}"
    )
    assert resp.status_code == 200
    assert "<h1" in resp.text  # rendered markdown heading
    assert "<strong>bold</strong>" in resp.text
    assert "<em>italic</em>" in resp.text


async def test_create_article_as_published(client: AsyncClient):
    """Creating an article with is_published=on should set it as published."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    article_id = await create_article_via_form(
        client, hc_id, title="Published Article", is_published="on"
    )

    resp = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}"
    )
    assert resp.status_code == 200
    assert "Published" in resp.text


async def test_create_article_as_draft(client: AsyncClient):
    """Creating an article without is_published should be draft."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    article_id = await create_article_via_form(
        client, hc_id, title="Draft Article", is_published=""
    )

    resp = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}"
    )
    assert resp.status_code == 200
    assert "Draft" in resp.text


async def test_create_article_empty_title_fails(client: AsyncClient):
    """POST with empty title should return validation error."""
    await register_and_login(client)
    hc_id = await create_help_center(client)

    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/articles/new",
        data={
            "title": "  ",
            "content_markdown": "Some content",
            "excerpt": "",
            "category_id": "",
            "is_published": "",
        },
    )
    assert resp.status_code == 422
    assert "title is required" in resp.text


async def test_create_article_slug_auto_generated(client: AsyncClient):
    """Article slug should be auto-generated from title."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    article_id = await create_article_via_form(
        client, hc_id, title="How to Install Our SDK"
    )

    resp = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}"
    )
    assert resp.status_code == 200
    assert "how-to-install-our-sdk" in resp.text


async def test_create_article_duplicate_slug_resolves(client: AsyncClient):
    """Two articles with the same title should get unique slugs."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    id1 = await create_article_via_form(client, hc_id, title="FAQ")
    id2 = await create_article_via_form(client, hc_id, title="FAQ")

    resp1 = await client.get(f"/dashboard/help-centers/{hc_id}/articles/{id1}")
    resp2 = await client.get(f"/dashboard/help-centers/{hc_id}/articles/{id2}")
    assert "/faq" in resp1.text
    assert "/faq-1" in resp2.text


# ============================================================
# Article detail
# ============================================================


async def test_article_detail_shows_info(client: AsyncClient):
    """Detail page should show title, slug, status, content."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    article_id = await create_article_via_form(
        client,
        hc_id,
        title="Detail Test Article",
        content_markdown="Content here",
        excerpt="Test excerpt",
    )

    resp = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}"
    )
    assert resp.status_code == 200
    assert "Detail Test Article" in resp.text
    assert "detail-test-article" in resp.text  # slug
    assert "Test excerpt" in resp.text
    assert "Draft" in resp.text  # default state


async def test_article_detail_has_action_buttons(client: AsyncClient):
    """Detail page should have Edit, Publish, and Delete buttons."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    article_id = await create_article_via_form(client, hc_id, title="Action Test")

    resp = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}"
    )
    assert resp.status_code == 200
    assert "Edit" in resp.text
    assert "Publish" in resp.text
    assert "Delete" in resp.text


async def test_article_detail_nonexistent_redirects(client: AsyncClient):
    """Visiting a nonexistent article should redirect to articles list."""
    await register_and_login(client)
    hc_id = await create_help_center(client)

    resp = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles/nonexistent-id",
        follow_redirects=False,
    )
    assert resp.status_code == 303


async def test_article_detail_empty_content(client: AsyncClient):
    """Detail page should show empty state when article has no content."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    article_id = await create_article_via_form(
        client, hc_id, title="Empty Article", content_markdown=""
    )

    resp = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}"
    )
    assert resp.status_code == 200
    assert "No content yet" in resp.text


# ============================================================
# Article edit
# ============================================================


async def test_edit_article_page_renders(client: AsyncClient):
    """GET edit page should show form with pre-populated values."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    article_id = await create_article_via_form(
        client,
        hc_id,
        title="Edit Me",
        content_markdown="# Original content",
        excerpt="Original excerpt",
    )

    resp = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}/edit"
    )
    assert resp.status_code == 200
    assert "Edit Article" in resp.text
    assert 'value="Edit Me"' in resp.text
    assert "# Original content" in resp.text
    assert 'value="Original excerpt"' in resp.text


async def test_edit_article_update_title(client: AsyncClient):
    """POST edit should update article title and slug."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    article_id = await create_article_via_form(client, hc_id, title="Old Title")

    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}/edit",
        data={
            "title": "New Title",
            "content_markdown": "Content",
            "excerpt": "",
            "category_id": "",
            "is_published": "",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303

    detail = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}"
    )
    assert "New Title" in detail.text
    assert "new-title" in detail.text


async def test_edit_article_update_content(client: AsyncClient):
    """POST edit should update article content and rendered output."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    article_id = await create_article_via_form(
        client, hc_id, title="Content Update", content_markdown="Old content"
    )

    await client.post(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}/edit",
        data={
            "title": "Content Update",
            "content_markdown": "# New heading\n\nUpdated **content**!",
            "excerpt": "",
            "category_id": "",
            "is_published": "",
        },
        follow_redirects=False,
    )

    detail = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}"
    )
    assert "<h1" in detail.text
    assert "<strong>content</strong>" in detail.text


async def test_edit_article_empty_title_fails(client: AsyncClient):
    """POST edit with empty title should return validation error."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    article_id = await create_article_via_form(client, hc_id, title="Valid Title")

    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}/edit",
        data={
            "title": "",
            "content_markdown": "Content",
            "excerpt": "",
            "category_id": "",
            "is_published": "",
        },
    )
    assert resp.status_code == 422
    assert "title is required" in resp.text


async def test_edit_article_preserves_data_on_error(client: AsyncClient):
    """Edit form should preserve submitted data on validation error."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    article_id = await create_article_via_form(client, hc_id, title="Keep Data")

    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}/edit",
        data={
            "title": "",
            "content_markdown": "Preserved content",
            "excerpt": "Preserved excerpt",
            "category_id": "",
            "is_published": "",
        },
    )
    assert resp.status_code == 422
    assert "Preserved content" in resp.text


# ============================================================
# Article delete
# ============================================================


async def test_delete_article(client: AsyncClient):
    """POST delete should remove article and redirect to list."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    article_id = await create_article_via_form(client, hc_id, title="Delete Me")

    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}/delete",
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "/articles" in resp.headers["location"]

    # Verify it's gone
    detail = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}",
        follow_redirects=False,
    )
    assert detail.status_code == 303


async def test_delete_article_nonexistent_redirects(client: AsyncClient):
    """Deleting a nonexistent article should redirect gracefully."""
    await register_and_login(client)
    hc_id = await create_help_center(client)

    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/articles/nonexistent/delete",
        follow_redirects=False,
    )
    assert resp.status_code == 303


# ============================================================
# Toggle publish
# ============================================================


async def test_toggle_publish_draft_to_published(client: AsyncClient):
    """Toggle publish should switch draft to published."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    article_id = await create_article_via_form(
        client, hc_id, title="Toggle Test", is_published=""
    )

    # Verify it's draft
    detail = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}"
    )
    assert "Draft" in detail.text

    # Toggle to published
    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}/toggle-publish",
        follow_redirects=False,
    )
    assert resp.status_code == 303

    # Verify it's published
    detail = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}"
    )
    assert "Published" in detail.text
    assert "Unpublish" in detail.text


async def test_toggle_publish_published_to_draft(client: AsyncClient):
    """Toggle publish should switch published to draft."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    article_id = await create_article_via_form(
        client, hc_id, title="Unpublish Test", is_published="on"
    )

    # Toggle to draft
    await client.post(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}/toggle-publish",
        follow_redirects=False,
    )

    detail = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}"
    )
    assert "Draft" in detail.text
    assert "Publish" in detail.text


# ============================================================
# Markdown preview API
# ============================================================


async def test_preview_markdown_api(client: AsyncClient):
    """POST preview-markdown should return rendered HTML."""
    await register_and_login(client)
    hc_id = await create_help_center(client)

    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/articles/preview-markdown",
        json={"content": "# Hello World\n\nSome **bold** text."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "<h1" in data["html"]
    assert "<strong>bold</strong>" in data["html"]


async def test_preview_markdown_empty(client: AsyncClient):
    """Preview with empty content should return empty HTML."""
    await register_and_login(client)
    hc_id = await create_help_center(client)

    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/articles/preview-markdown",
        json={"content": ""},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["html"] == ""


# ============================================================
# Authorization
# ============================================================


async def test_article_crud_other_user_cannot_access(client: AsyncClient):
    """User should not be able to access another user's articles."""
    # User 1 creates help center and article
    await register_and_login(client, email="user1@example.com")
    hc_id = await create_help_center(client, name="User1 HC")
    article_id = await create_article_via_form(
        client, hc_id, title="User1 Article"
    )

    # Switch to user 2
    client.cookies.clear()
    await register_and_login(client, email="user2@example.com")

    # User 2 cannot view articles list
    resp = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles", follow_redirects=False
    )
    assert resp.status_code == 303

    # User 2 cannot view article detail
    resp = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}",
        follow_redirects=False,
    )
    assert resp.status_code == 303

    # User 2 cannot edit article
    resp = await client.get(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}/edit",
        follow_redirects=False,
    )
    assert resp.status_code == 303

    # User 2 cannot delete article
    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/articles/{article_id}/delete",
        follow_redirects=False,
    )
    assert resp.status_code == 303


async def test_help_center_detail_shows_articles_link(client: AsyncClient):
    """Help center detail should have a link to manage articles."""
    await register_and_login(client)
    hc_id = await create_help_center(client)

    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    assert resp.status_code == 200
    assert "Manage Articles" in resp.text
    assert "New Article" in resp.text
    assert "/articles" in resp.text
