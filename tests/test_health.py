"""Tests for health check and landing page."""

import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Health check returns 200 with status info."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "HelpBase"
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_landing_page(client):
    """Landing page returns 200 with HTML content."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "HelpBase" in response.text
    assert "Beautiful help centers" in response.text


@pytest.mark.asyncio
async def test_landing_page_has_pricing(client):
    """Landing page includes pricing section."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "$0" in response.text
    assert "$12" in response.text
    assert "$29" in response.text


@pytest.mark.asyncio
async def test_landing_page_has_features(client):
    """Landing page includes features section."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "Markdown Editor" in response.text
    assert "Full-Text Search" in response.text
    assert "Analytics" in response.text
