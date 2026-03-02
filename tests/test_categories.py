"""Comprehensive tests for category CRUD."""

import pytest
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
    description: str = "",
    icon: str = "",
) -> None:
    """Create a category via the form. Returns after redirect."""
    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/categories/new",
        data={"name": name, "description": description, "icon": icon},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"].startswith(f"/dashboard/help-centers/{hc_id}")


# ============================================================
# Category create page
# ============================================================


async def test_new_category_page_requires_auth(client: AsyncClient):
    """GET new category page without auth should redirect."""
    resp = await client.get(
        "/dashboard/help-centers/fake-id/categories/new", follow_redirects=False
    )
    assert resp.status_code in (303, 401)


async def test_new_category_page_renders(client: AsyncClient):
    """GET new category form should show the form."""
    await register_and_login(client)
    hc_id = await create_help_center(client)

    resp = await client.get(f"/dashboard/help-centers/{hc_id}/categories/new")
    assert resp.status_code == 200
    assert "Create a Category" in resp.text
    assert 'name="name"' in resp.text
    assert "Icon" in resp.text


async def test_new_category_page_nonexistent_hc_redirects(client: AsyncClient):
    """GET new category for non-existent HC should redirect."""
    await register_and_login(client)
    resp = await client.get(
        "/dashboard/help-centers/nonexistent/categories/new", follow_redirects=False
    )
    assert resp.status_code == 303


# ============================================================
# Category creation
# ============================================================


async def test_create_category_success(client: AsyncClient):
    """POST should create a category and redirect to HC detail."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    await create_category_via_form(client, hc_id, name="Getting Started")

    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    assert "Getting Started" in resp.text
    assert "getting-started" in resp.text  # slug
    assert "No categories yet" not in resp.text


async def test_create_category_with_description_and_icon(client: AsyncClient):
    """Category with description and icon should be created."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    await create_category_via_form(
        client, hc_id, name="FAQ", description="Frequently asked questions", icon="❓"
    )

    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    assert "FAQ" in resp.text
    assert "Frequently asked" in resp.text


async def test_create_category_empty_name_fails(client: AsyncClient):
    """POST with empty name should show validation error."""
    await register_and_login(client)
    hc_id = await create_help_center(client)

    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/categories/new",
        data={"name": "  ", "description": "", "icon": ""},
    )
    assert resp.status_code == 422
    assert "name is required" in resp.text


async def test_create_multiple_categories_ordering(client: AsyncClient):
    """Categories should appear in creation order."""
    await register_and_login(client)
    hc_id = await create_help_center(client)

    await create_category_via_form(client, hc_id, name="First Category")
    await create_category_via_form(client, hc_id, name="Second Category")
    await create_category_via_form(client, hc_id, name="Third Category")

    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    text = resp.text
    # All three should be present
    assert "First Category" in text
    assert "Second Category" in text
    assert "Third Category" in text
    # Check ordering: First should appear before Second, Second before Third
    first_pos = text.index("First Category")
    second_pos = text.index("Second Category")
    third_pos = text.index("Third Category")
    assert first_pos < second_pos < third_pos


async def test_create_category_duplicate_slug_auto_resolves(client: AsyncClient):
    """Two categories with same name should get unique slugs."""
    await register_and_login(client)
    hc_id = await create_help_center(client)

    await create_category_via_form(client, hc_id, name="FAQ")
    await create_category_via_form(client, hc_id, name="FAQ")

    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    text = resp.text
    # Should have both faq and faq-1 slugs
    assert "/faq" in text
    assert "/faq-1" in text


# ============================================================
# Category edit
# ============================================================


async def test_edit_category_page_renders(client: AsyncClient):
    """GET edit category form should show the form with current data."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    await create_category_via_form(client, hc_id, name="Edit Me Cat")

    # Get the category ID from the detail page
    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    # Find the edit link
    import re

    edit_links = re.findall(
        rf"/dashboard/help-centers/{hc_id}/categories/([^/]+)/edit", resp.text
    )
    assert len(edit_links) >= 1
    cat_id = edit_links[0]

    resp = await client.get(
        f"/dashboard/help-centers/{hc_id}/categories/{cat_id}/edit"
    )
    assert resp.status_code == 200
    assert "Edit Category" in resp.text
    assert 'value="Edit Me Cat"' in resp.text


async def test_edit_category_update_name(client: AsyncClient):
    """POST edit should update the category name and slug."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    await create_category_via_form(client, hc_id, name="Old Cat")

    # Get category ID
    import re

    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    edit_links = re.findall(
        rf"/dashboard/help-centers/{hc_id}/categories/([^/]+)/edit", resp.text
    )
    cat_id = edit_links[0]

    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/categories/{cat_id}/edit",
        data={"name": "New Cat Name", "description": "Updated desc", "icon": "🔥"},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    detail = await client.get(f"/dashboard/help-centers/{hc_id}")
    assert "New Cat Name" in detail.text
    assert "new-cat-name" in detail.text  # slug updated


async def test_edit_category_empty_name_fails(client: AsyncClient):
    """POST edit with empty name should show error."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    await create_category_via_form(client, hc_id, name="Keep Name Cat")

    import re

    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    edit_links = re.findall(
        rf"/dashboard/help-centers/{hc_id}/categories/([^/]+)/edit", resp.text
    )
    cat_id = edit_links[0]

    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/categories/{cat_id}/edit",
        data={"name": "", "description": "", "icon": ""},
    )
    assert resp.status_code == 422
    assert "name is required" in resp.text


# ============================================================
# Category delete
# ============================================================


async def test_delete_category(client: AsyncClient):
    """POST delete should remove the category."""
    await register_and_login(client)
    hc_id = await create_help_center(client)
    await create_category_via_form(client, hc_id, name="Delete Me Cat")

    import re

    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    # Find the delete form action
    delete_links = re.findall(
        rf"/dashboard/help-centers/{hc_id}/categories/([^/]+)/delete", resp.text
    )
    assert len(delete_links) >= 1
    cat_id = delete_links[0]

    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/categories/{cat_id}/delete",
        follow_redirects=False,
    )
    assert resp.status_code == 303

    # Verify it's gone
    detail = await client.get(f"/dashboard/help-centers/{hc_id}")
    assert "Delete Me Cat" not in detail.text
    assert "No categories yet" in detail.text


async def test_delete_category_nonexistent_redirects(client: AsyncClient):
    """Deleting non-existent category should redirect gracefully."""
    await register_and_login(client)
    hc_id = await create_help_center(client)

    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/categories/nonexistent/delete",
        follow_redirects=False,
    )
    assert resp.status_code == 303


# ============================================================
# Authorization: other user can't access categories
# ============================================================


async def test_other_user_cannot_create_category(client: AsyncClient):
    """Another user can't create categories in someone else's help center."""
    await register_and_login(client, email="owner@example.com")
    hc_id = await create_help_center(client, name="Owner HC")

    client.cookies.clear()
    await register_and_login(client, email="other@example.com")

    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/categories/new",
        data={"name": "Hacked Category", "description": "", "icon": ""},
        follow_redirects=False,
    )
    # Should redirect to dashboard because HC not found for this user
    assert resp.status_code == 303
    assert resp.headers["location"] == "/dashboard"


async def test_other_user_cannot_edit_category(client: AsyncClient):
    """Another user can't edit categories in someone else's help center."""
    await register_and_login(client, email="owner@example.com")
    hc_id = await create_help_center(client, name="Owner HC")
    await create_category_via_form(client, hc_id, name="Locked Cat")

    import re

    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    edit_links = re.findall(
        rf"/dashboard/help-centers/{hc_id}/categories/([^/]+)/edit", resp.text
    )
    cat_id = edit_links[0]

    client.cookies.clear()
    await register_and_login(client, email="other@example.com")

    resp = await client.get(
        f"/dashboard/help-centers/{hc_id}/categories/{cat_id}/edit",
        follow_redirects=False,
    )
    assert resp.status_code == 303  # redirect because not authorized


# ============================================================
# Stats integration
# ============================================================


async def test_help_center_stats_reflect_categories(client: AsyncClient):
    """Stats cards on detail page should count categories correctly."""
    await register_and_login(client)
    hc_id = await create_help_center(client)

    # Start with 0 categories
    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    assert ">0<" in resp.text.replace(" ", "")  # 0 categories, articles

    # Add 2 categories
    await create_category_via_form(client, hc_id, name="Cat 1")
    await create_category_via_form(client, hc_id, name="Cat 2")

    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    # Should show 2 categories in the stats
    assert "Cat 1" in resp.text
    assert "Cat 2" in resp.text
