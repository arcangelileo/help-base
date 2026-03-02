"""Comprehensive tests for authentication system."""

from httpx import AsyncClient

from helpbase.services.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


# --- Password hashing tests ---


def test_hash_password():
    """Hashed password should not equal plaintext."""
    hashed = hash_password("mysecretpassword")
    assert hashed != "mysecretpassword"
    assert hashed.startswith("$2b$")  # bcrypt prefix


def test_verify_password_correct():
    """Correct password should verify successfully."""
    hashed = hash_password("mysecretpassword")
    assert verify_password("mysecretpassword", hashed) is True


def test_verify_password_incorrect():
    """Wrong password should fail verification."""
    hashed = hash_password("mysecretpassword")
    assert verify_password("wrongpassword", hashed) is False


# --- JWT token tests ---


def test_create_and_decode_token():
    """Token should encode and decode user data correctly."""
    token = create_access_token("user-123", "test@example.com")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["email"] == "test@example.com"
    assert "exp" in payload


def test_decode_invalid_token():
    """Invalid token should return None."""
    payload = decode_access_token("not-a-valid-token")
    assert payload is None


def test_decode_tampered_token():
    """Tampered token should return None."""
    token = create_access_token("user-123", "test@example.com")
    tampered = token[:-5] + "XXXXX"
    payload = decode_access_token(tampered)
    assert payload is None


# --- Registration page tests ---


async def test_register_page_renders(client: AsyncClient):
    """GET /auth/register should render the registration form."""
    response = await client.get("/auth/register")
    assert response.status_code == 200
    assert "Create your account" in response.text
    assert "Full name" in response.text
    assert "Email address" in response.text
    assert "Password" in response.text


async def test_register_success(client: AsyncClient):
    """POST /auth/register with valid data should create user and redirect to dashboard."""
    response = await client.post(
        "/auth/register",
        data={
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    assert "access_token" in response.cookies


async def test_register_password_mismatch(client: AsyncClient):
    """POST /auth/register with mismatched passwords should show error."""
    response = await client.post(
        "/auth/register",
        data={
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "password": "securepassword123",
            "password_confirm": "differentpassword",
        },
    )
    assert response.status_code == 422
    assert "Passwords do not match" in response.text


async def test_register_short_password(client: AsyncClient):
    """POST /auth/register with short password should show error."""
    response = await client.post(
        "/auth/register",
        data={
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "password": "short",
            "password_confirm": "short",
        },
    )
    assert response.status_code == 422
    assert "at least 8 characters" in response.text


async def test_register_duplicate_email(client: AsyncClient):
    """POST /auth/register with existing email should show error."""
    # Register first user
    await client.post(
        "/auth/register",
        data={
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )
    # Try to register again with same email
    response = await client.post(
        "/auth/register",
        data={
            "full_name": "Jane Smith",
            "email": "jane@example.com",
            "password": "anotherpassword123",
            "password_confirm": "anotherpassword123",
        },
    )
    assert response.status_code == 422
    assert "already exists" in response.text


async def test_register_empty_name(client: AsyncClient):
    """POST /auth/register with empty name should show error."""
    response = await client.post(
        "/auth/register",
        data={
            "full_name": "   ",
            "email": "jane@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
    )
    assert response.status_code == 422
    assert "Full name is required" in response.text


async def test_register_preserves_form_data(client: AsyncClient):
    """After validation error, form should preserve entered data."""
    response = await client.post(
        "/auth/register",
        data={
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "password": "short",
            "password_confirm": "short",
        },
    )
    assert response.status_code == 422
    assert 'value="Jane Doe"' in response.text
    assert 'value="jane@example.com"' in response.text


# --- Login page tests ---


async def test_login_page_renders(client: AsyncClient):
    """GET /auth/login should render the login form."""
    response = await client.get("/auth/login")
    assert response.status_code == 200
    assert "Welcome back" in response.text
    assert "Email address" in response.text
    assert "Password" in response.text


async def test_login_success(client: AsyncClient):
    """POST /auth/login with valid credentials should set cookie and redirect."""
    # Register first
    await client.post(
        "/auth/register",
        data={
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )
    # Clear cookies to simulate fresh login
    client.cookies.clear()

    response = await client.post(
        "/auth/login",
        data={
            "email": "jane@example.com",
            "password": "securepassword123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    assert "access_token" in response.cookies


async def test_login_wrong_password(client: AsyncClient):
    """POST /auth/login with wrong password should show error."""
    # Register first
    await client.post(
        "/auth/register",
        data={
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )
    client.cookies.clear()

    response = await client.post(
        "/auth/login",
        data={
            "email": "jane@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.text


async def test_login_nonexistent_email(client: AsyncClient):
    """POST /auth/login with non-existent email should show error."""
    response = await client.post(
        "/auth/login",
        data={
            "email": "nobody@example.com",
            "password": "somepassword123",
        },
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.text


async def test_login_preserves_email(client: AsyncClient):
    """After login failure, form should preserve entered email."""
    response = await client.post(
        "/auth/login",
        data={
            "email": "jane@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert 'value="jane@example.com"' in response.text


# --- Logout tests ---


async def test_logout(client: AsyncClient):
    """GET /auth/logout should clear cookie and redirect to landing."""
    # Register and get cookie
    await client.post(
        "/auth/register",
        data={
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )
    assert "access_token" in client.cookies

    response = await client.get("/auth/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"


# --- Dashboard access tests ---


async def test_dashboard_requires_auth(client: AsyncClient):
    """GET /dashboard without auth should return 401 or redirect."""
    response = await client.get("/dashboard", follow_redirects=False)
    # Should get a 303 redirect to login or a 401
    assert response.status_code in (303, 401)


async def test_dashboard_accessible_when_authenticated(client: AsyncClient):
    """GET /dashboard with valid auth should return 200."""
    # Register (auto-login)
    reg_response = await client.post(
        "/auth/register",
        data={
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )
    # Extract the token cookie and set it on the client
    token = reg_response.cookies.get("access_token")
    assert token is not None
    client.cookies.set("access_token", token)

    response = await client.get("/dashboard")
    assert response.status_code == 200
    assert "Welcome back" in response.text
    assert "Jane" in response.text


async def test_dashboard_shows_empty_state(client: AsyncClient):
    """Dashboard for new user should show empty help centers state."""
    reg_response = await client.post(
        "/auth/register",
        data={
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )
    token = reg_response.cookies.get("access_token")
    client.cookies.set("access_token", token)

    response = await client.get("/dashboard")
    assert response.status_code == 200
    assert "No help centers yet" in response.text
    assert "Create Help Center" in response.text


# --- Auth redirect tests ---


async def test_register_page_redirects_when_logged_in(client: AsyncClient):
    """GET /auth/register when already authenticated should redirect to dashboard."""
    reg_response = await client.post(
        "/auth/register",
        data={
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )
    token = reg_response.cookies.get("access_token")
    client.cookies.set("access_token", token)

    response = await client.get("/auth/register", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"


async def test_login_page_redirects_when_logged_in(client: AsyncClient):
    """GET /auth/login when already authenticated should redirect to dashboard."""
    reg_response = await client.post(
        "/auth/register",
        data={
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )
    token = reg_response.cookies.get("access_token")
    client.cookies.set("access_token", token)

    response = await client.get("/auth/login", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"


# --- Email normalization ---


async def test_email_case_insensitive(client: AsyncClient):
    """Registration should normalize email to lowercase."""
    # Register with mixed case
    await client.post(
        "/auth/register",
        data={
            "full_name": "Jane Doe",
            "email": "Jane@Example.COM",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )
    client.cookies.clear()

    # Login with lowercase should work
    response = await client.post(
        "/auth/login",
        data={
            "email": "jane@example.com",
            "password": "securepassword123",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "access_token" in response.cookies


# --- Landing page auth state ---


async def test_landing_page_shows_sign_in_when_logged_out(client: AsyncClient):
    """Landing page should show Sign in/Get Started when not authenticated."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "Sign in" in response.text
    assert "Get Started Free" in response.text


async def test_landing_page_shows_dashboard_when_logged_in(client: AsyncClient):
    """Landing page should show Dashboard/Sign out when authenticated."""
    reg_response = await client.post(
        "/auth/register",
        data={
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "password": "securepassword123",
            "password_confirm": "securepassword123",
        },
        follow_redirects=False,
    )
    token = reg_response.cookies.get("access_token")
    client.cookies.set("access_token", token)

    response = await client.get("/")
    assert response.status_code == 200
    assert "Dashboard" in response.text
    assert "Sign out" in response.text
