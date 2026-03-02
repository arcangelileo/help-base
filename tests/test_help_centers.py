"""Comprehensive tests for help center CRUD."""

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


async def create_help_center_via_form(
    client: AsyncClient,
    name: str = "My Help Center",
    description: str = "Test desc",
    primary_color: str = "#4F46E5",
) -> str:
    """Create a help center via the form and return its ID extracted from redirect."""
    resp = await client.post(
        "/dashboard/help-centers/new",
        data={"name": name, "description": description, "primary_color": primary_color},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    # Redirect URL should be /dashboard/help-centers/{id}
    location = resp.headers["location"]
    assert location.startswith("/dashboard/help-centers/")
    hc_id = location.split("/dashboard/help-centers/")[1]
    return hc_id


# ============================================================
# Help Center create page
# ============================================================


async def test_new_help_center_page_requires_auth(client: AsyncClient):
    """GET /dashboard/help-centers/new without auth should redirect."""
    resp = await client.get("/dashboard/help-centers/new", follow_redirects=False)
    assert resp.status_code in (303, 401)


async def test_new_help_center_page_renders(client: AsyncClient):
    """GET /dashboard/help-centers/new should render the form."""
    await register_and_login(client)
    resp = await client.get("/dashboard/help-centers/new")
    assert resp.status_code == 200
    assert "Create a Help Center" in resp.text
    assert 'name="name"' in resp.text
    assert "Brand Color" in resp.text


# ============================================================
# Help Center creation
# ============================================================


async def test_create_help_center_success(client: AsyncClient):
    """POST /dashboard/help-centers/new should create and redirect."""
    await register_and_login(client)
    hc_id = await create_help_center_via_form(client, name="Acme Docs")

    # Visit detail page to verify
    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    assert resp.status_code == 200
    assert "Acme Docs" in resp.text
    assert "acme-docs" in resp.text  # slug


async def test_create_help_center_with_custom_color(client: AsyncClient):
    """Creating a help center with custom color should work."""
    await register_and_login(client)
    hc_id = await create_help_center_via_form(
        client, name="Colorful Docs", primary_color="#DC2626"
    )
    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    assert resp.status_code == 200
    assert "#DC2626" in resp.text


async def test_create_help_center_empty_name_fails(client: AsyncClient):
    """POST with empty name should return validation error."""
    await register_and_login(client)
    resp = await client.post(
        "/dashboard/help-centers/new",
        data={"name": "  ", "description": "", "primary_color": "#4F46E5"},
    )
    assert resp.status_code == 422
    assert "name is required" in resp.text


async def test_create_help_center_invalid_color_fails(client: AsyncClient):
    """POST with invalid color should return validation error."""
    await register_and_login(client)
    resp = await client.post(
        "/dashboard/help-centers/new",
        data={"name": "Test", "description": "", "primary_color": "notacolor"},
    )
    assert resp.status_code == 422
    assert "hex color" in resp.text


async def test_create_help_center_duplicate_slug_auto_resolves(client: AsyncClient):
    """Two help centers with same name should get unique slugs."""
    await register_and_login(client)
    hc_id1 = await create_help_center_via_form(client, name="My Docs")
    hc_id2 = await create_help_center_via_form(client, name="My Docs")

    resp1 = await client.get(f"/dashboard/help-centers/{hc_id1}")
    resp2 = await client.get(f"/dashboard/help-centers/{hc_id2}")
    assert "my-docs" in resp1.text
    # Second should have a different slug (my-docs-1)
    assert "my-docs-1" in resp2.text


async def test_dashboard_shows_created_help_center(client: AsyncClient):
    """After creating a help center, it should appear on the dashboard."""
    await register_and_login(client)
    await create_help_center_via_form(client, name="Dashboard Test HC")

    resp = await client.get("/dashboard")
    assert resp.status_code == 200
    assert "Dashboard Test HC" in resp.text
    assert "No help centers yet" not in resp.text


# ============================================================
# Help Center detail
# ============================================================


async def test_help_center_detail_shows_info(client: AsyncClient):
    """Detail page should show name, slug, description, stats."""
    await register_and_login(client)
    hc_id = await create_help_center_via_form(
        client, name="Detail Test", description="A test description"
    )
    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    assert resp.status_code == 200
    assert "Detail Test" in resp.text
    assert "detail-test" in resp.text  # slug
    assert "Categories" in resp.text
    assert "No categories yet" in resp.text


async def test_help_center_detail_nonexistent_redirects(client: AsyncClient):
    """Visiting a non-existent help center should redirect to dashboard."""
    await register_and_login(client)
    resp = await client.get("/dashboard/help-centers/nonexistent-id", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/dashboard"


async def test_help_center_detail_other_users_redirects(client: AsyncClient):
    """Can't view another user's help center."""
    # Register user 1 and create a help center
    await register_and_login(client, email="user1@example.com")
    hc_id = await create_help_center_via_form(client, name="User1 HC")

    # Register user 2
    client.cookies.clear()
    await register_and_login(client, email="user2@example.com")

    # Try to access user1's help center
    resp = await client.get(f"/dashboard/help-centers/{hc_id}", follow_redirects=False)
    assert resp.status_code == 303


# ============================================================
# Help Center edit
# ============================================================


async def test_edit_help_center_page_renders(client: AsyncClient):
    """GET /dashboard/help-centers/{id}/edit should render the edit form."""
    await register_and_login(client)
    hc_id = await create_help_center_via_form(client, name="Edit Me")

    resp = await client.get(f"/dashboard/help-centers/{hc_id}/edit")
    assert resp.status_code == 200
    assert "Help Center Settings" in resp.text
    assert 'value="Edit Me"' in resp.text


async def test_edit_help_center_update_name(client: AsyncClient):
    """POST edit should update the help center name."""
    await register_and_login(client)
    hc_id = await create_help_center_via_form(client, name="Old Name")

    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/edit",
        data={"name": "New Name", "description": "", "primary_color": "#4F46E5"},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    detail = await client.get(f"/dashboard/help-centers/{hc_id}")
    assert "New Name" in detail.text
    assert "new-name" in detail.text  # slug updated


async def test_edit_help_center_update_color(client: AsyncClient):
    """POST edit should update the primary color."""
    await register_and_login(client)
    hc_id = await create_help_center_via_form(client, name="Color Test")

    await client.post(
        f"/dashboard/help-centers/{hc_id}/edit",
        data={"name": "Color Test", "description": "", "primary_color": "#059669"},
        follow_redirects=False,
    )
    detail = await client.get(f"/dashboard/help-centers/{hc_id}")
    assert "#059669" in detail.text


async def test_edit_help_center_preserves_data_on_error(client: AsyncClient):
    """Edit form should preserve form data on validation error."""
    await register_and_login(client)
    hc_id = await create_help_center_via_form(client, name="Keep Data")

    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/edit",
        data={"name": "", "description": "Some desc", "primary_color": "#4F46E5"},
    )
    assert resp.status_code == 422
    assert "name is required" in resp.text


# ============================================================
# Help Center delete
# ============================================================


async def test_delete_help_center(client: AsyncClient):
    """POST /dashboard/help-centers/{id}/delete should remove it."""
    await register_and_login(client)
    hc_id = await create_help_center_via_form(client, name="Delete Me")

    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/delete", follow_redirects=False
    )
    assert resp.status_code == 303
    assert resp.headers["location"].startswith("/dashboard")

    # Verify it's gone
    detail = await client.get(f"/dashboard/help-centers/{hc_id}", follow_redirects=False)
    assert detail.status_code == 303  # redirects because not found


async def test_delete_help_center_other_user_fails(client: AsyncClient):
    """Can't delete another user's help center."""
    await register_and_login(client, email="owner@example.com")
    hc_id = await create_help_center_via_form(client, name="Owned HC")

    # Save owner token from the cookie jar
    owner_token = None
    for cookie in client.cookies.jar:
        if cookie.name == "access_token":
            owner_token = cookie.value
            break
    assert owner_token is not None

    client.cookies.clear()
    await register_and_login(client, email="attacker@example.com")

    resp = await client.post(
        f"/dashboard/help-centers/{hc_id}/delete", follow_redirects=False
    )
    assert resp.status_code == 303

    # Verify it still exists for the owner
    client.cookies.clear()
    client.cookies.set("access_token", owner_token)
    detail = await client.get(f"/dashboard/help-centers/{hc_id}")
    assert detail.status_code == 200
    assert "Owned HC" in detail.text


# ============================================================
# Slugify edge cases
# ============================================================


async def test_special_chars_in_name_are_slugified(client: AsyncClient):
    """Special characters should be stripped from the slug."""
    await register_and_login(client)
    hc_id = await create_help_center_via_form(client, name="Hello, World! (Test)")
    resp = await client.get(f"/dashboard/help-centers/{hc_id}")
    assert "hello-world-test" in resp.text
