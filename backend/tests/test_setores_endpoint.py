"""
STORY-252 Track 5 (AC25): Tests for /setores endpoint

Verifies that the sectors endpoint returns valid data for frontend consumption.
Both legacy (/setores) and versioned (/v1/setores) endpoints are tested.
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_setores_endpoint_returns_200():
    """Test that GET /setores returns 200 OK (legacy endpoint)."""
    response = client.get("/setores")
    assert response.status_code == 200


def test_setores_v1_endpoint_returns_200():
    """Test that GET /v1/setores returns 200 OK (versioned endpoint)."""
    response = client.get("/v1/setores")
    assert response.status_code == 200


def test_setores_both_endpoints_return_same_data():
    """Test that both /setores and /v1/setores return identical data."""
    legacy_response = client.get("/setores")
    versioned_response = client.get("/v1/setores")

    assert legacy_response.json() == versioned_response.json()


def test_setores_response_structure():
    """Test that response contains 'setores' key with list of sectors."""
    response = client.get("/setores")
    data = response.json()

    assert "setores" in data
    assert isinstance(data["setores"], list)


def test_setores_minimum_count():
    """Test that at least 5 sectors are returned."""
    response = client.get("/setores")
    data = response.json()

    assert len(data["setores"]) >= 5


def test_setores_schema_validation():
    """Test that each sector has required fields: id, name, description."""
    response = client.get("/setores")
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
    response = client.get("/setores")
    data = response.json()

    for sector in data["setores"]:
        assert sector["id"].strip(), f"Sector has empty id: {sector}"
        assert sector["name"].strip(), f"Sector has empty name: {sector}"
        assert sector["description"].strip(), f"Sector has empty description: {sector}"
