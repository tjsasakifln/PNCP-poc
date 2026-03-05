"""
STORY-252 Track 5 (AC25): Tests for /setores endpoint

Verifies that the sectors endpoint returns valid data for frontend consumption.
TD-004: Only versioned (/v1/setores) endpoint is tested. Legacy /setores removed.
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_setores_endpoint_returns_200():
    """Test that GET /v1/setores returns 200 OK."""
    response = client.get("/v1/setores")
    assert response.status_code == 200


def test_setores_v1_endpoint_returns_200():
    """Test that GET /v1/setores returns 200 OK (versioned endpoint)."""
    response = client.get("/v1/setores")
    assert response.status_code == 200


def test_setores_legacy_endpoint_removed():
    """TD-004: Legacy /setores (without /v1/) returns 404 after route cleanup."""
    legacy_response = client.get("/setores")
    assert legacy_response.status_code in (404, 405)


def test_setores_response_structure():
    """Test that response contains 'setores' key with list of sectors."""
    response = client.get("/v1/setores")
    data = response.json()

    assert "setores" in data
    assert isinstance(data["setores"], list)


def test_setores_minimum_count():
    """Test that at least 5 sectors are returned."""
    response = client.get("/v1/setores")
    data = response.json()

    assert len(data["setores"]) >= 5


def test_setores_schema_validation():
    """Test that each sector has required fields: id, name, description."""
    response = client.get("/v1/setores")
    data = response.json()

    for sector in data["setores"]:
        assert "id" in sector, f"Sector missing 'id': {sector}"
        assert "name" in sector, f"Sector missing 'name': {sector}"
        assert "description" in sector, f"Sector missing 'description': {sector}"

        # Validate types
        assert isinstance(sector["id"], str), f"Sector id should be string: {sector['id']}"
        assert isinstance(sector["name"], str), f"Sector name should be string: {sector['name']}"
        assert isinstance(sector["description"], str), f"Sector description should be string: {sector['description']}"


def test_setores_non_empty_fields():
    """Test that all sector fields have non-empty values."""
    response = client.get("/v1/setores")
    data = response.json()

    for sector in data["setores"]:
        assert sector["id"].strip(), f"Sector has empty id: {sector}"
        assert sector["name"].strip(), f"Sector has empty name: {sector}"
        assert sector["description"].strip(), f"Sector has empty description: {sector}"
