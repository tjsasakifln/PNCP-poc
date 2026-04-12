"""Tests for STORY-369: Trial Exit Survey endpoint."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from auth import require_auth


# ============================================================================
# Fixtures
# ============================================================================

MOCK_USER = {"id": "user-123", "email": "test@example.com"}


def override_auth():
    return MOCK_USER


@pytest.fixture(autouse=True)
def setup_auth():
    app.dependency_overrides[require_auth] = override_auth
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


# ============================================================================
# POST /v1/trial/exit-survey
# ============================================================================

class TestSubmitExitSurvey:
    def test_valid_submit(self, client):
        mock_db = MagicMock()
        # Call 1: check existing (empty) → no duplicate
        mock_existing = MagicMock()
        mock_existing.data = []
        # Call 2: insert (no data returned is fine)
        mock_inserted = MagicMock()
        mock_inserted.data = []
        # Call 3: fetch newly inserted row
        mock_fetched = MagicMock()
        mock_fetched.data = [{"id": "survey-abc", "created_at": "2026-04-11T00:00:00Z"}]

        call_count = 0

        async def mock_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_existing
            if call_count == 2:
                return mock_inserted
            return mock_fetched

        with patch("routes.user.sb_execute", side_effect=mock_sb_execute), \
             patch("routes.user.get_db", return_value=mock_db):
            resp = client.post("/v1/trial/exit-survey", json={"reason": "preco_alto"})
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert "created_at" in data

    def test_duplicate_returns_409(self, client):
        mock_db = MagicMock()
        mock_existing = MagicMock()
        mock_existing.data = [{"id": "existing-survey"}]

        async def mock_sb_execute(query):
            return mock_existing

        with patch("routes.user.sb_execute", side_effect=mock_sb_execute), \
             patch("routes.user.get_db", return_value=mock_db):
            resp = client.post("/v1/trial/exit-survey", json={"reason": "outro", "reason_text": "text"})
        assert resp.status_code == 409

    def test_invalid_reason_returns_422(self, client):
        resp = client.post("/v1/trial/exit-survey", json={"reason": "invalid_reason"})
        assert resp.status_code == 422

    def test_no_auth_returns_401(self):
        app.dependency_overrides.clear()
        c = TestClient(app)
        resp = c.post("/v1/trial/exit-survey", json={"reason": "preco_alto"})
        assert resp.status_code == 401
        app.dependency_overrides[require_auth] = override_auth


# ============================================================================
# GET /v1/admin/trial-exit-surveys
# ============================================================================

class TestAdminExitSurveys:
    def test_non_admin_returns_403(self, client):
        mock_db = MagicMock()

        async def mock_check_roles(user_id, db):
            return {"is_admin": False, "is_master": False}

        with patch("routes.user.check_user_roles", side_effect=mock_check_roles), \
             patch("routes.user.get_db", return_value=mock_db):
            resp = client.get("/v1/admin/trial-exit-surveys")
        assert resp.status_code == 403

    def test_admin_returns_grouped_results(self, client):
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [
            {"reason": "preco_alto", "created_at": "2026-04-11T00:00:00Z"},
            {"reason": "preco_alto", "created_at": "2026-04-10T00:00:00Z"},
            {"reason": "no_editais", "created_at": "2026-04-09T00:00:00Z"},
        ]

        async def mock_check_roles(user_id, db):
            return {"is_admin": True, "is_master": False}

        async def mock_sb_execute(query):
            return mock_result

        with patch("routes.user.check_user_roles", side_effect=mock_check_roles), \
             patch("routes.user.sb_execute", side_effect=mock_sb_execute), \
             patch("routes.user.get_db", return_value=mock_db):
            resp = client.get("/v1/admin/trial-exit-surveys")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        reasons = {item["reason"]: item["count"] for item in data["by_reason"]}
        assert reasons["preco_alto"] == 2
        assert reasons["no_editais"] == 1
