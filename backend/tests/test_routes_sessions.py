"""Tests for routes.sessions — GET /sessions endpoint.

STORY-224 Track 4 (AC22): Search session history route coverage.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from auth import require_auth
from routes.sessions import router


MOCK_USER = {"id": "user-123-uuid", "email": "test@example.com", "role": "authenticated"}


def _create_client():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth] = lambda: MOCK_USER
    return TestClient(app)


def _mock_sb(data=None, count=0):
    """Build a fluent-chainable Supabase mock."""
    sb = Mock()
    sb.table.return_value = sb
    sb.select.return_value = sb
    sb.eq.return_value = sb
    sb.order.return_value = sb
    sb.range.return_value = sb
    result = Mock(data=data or [], count=count)
    sb.execute.return_value = result
    return sb


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------

class TestGetSessions:
    """GET /sessions"""

    @patch("supabase_client.get_supabase")
    def test_empty_history(self, mock_get_sb):
        mock_get_sb.return_value = _mock_sb(data=[], count=0)
        client = _create_client()

        resp = client.get("/sessions")

        assert resp.status_code == 200
        body = resp.json()
        assert body["sessions"] == []
        assert body["total"] == 0
        assert body["limit"] == 20
        assert body["offset"] == 0

    @patch("supabase_client.get_supabase")
    def test_single_session(self, mock_get_sb):
        session_row = {
            "id": "sess-1",
            "user_id": "user-123-uuid",
            "created_at": "2026-02-01T10:00:00+00:00",
            "ufs": ["SP"],
            "total_filtered": 5,
            "valor_total": 100000.0,
        }
        mock_get_sb.return_value = _mock_sb(data=[session_row], count=1)
        client = _create_client()

        resp = client.get("/sessions")

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["sessions"]) == 1
        assert body["sessions"][0]["id"] == "sess-1"
        assert body["total"] == 1

    @patch("supabase_client.get_supabase")
    def test_pagination_params(self, mock_get_sb):
        sb = _mock_sb(data=[], count=50)
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/sessions?limit=10&offset=20")

        assert resp.status_code == 200
        body = resp.json()
        assert body["limit"] == 10
        assert body["offset"] == 20
        # Verify range call: offset=20, offset+limit-1=29
        sb.range.assert_called_once_with(20, 29)

    @patch("supabase_client.get_supabase")
    def test_default_limit_and_offset(self, mock_get_sb):
        sb = _mock_sb(data=[], count=0)
        mock_get_sb.return_value = sb
        client = _create_client()

        resp = client.get("/sessions")

        assert resp.status_code == 200
        body = resp.json()
        assert body["limit"] == 20
        assert body["offset"] == 0
        sb.range.assert_called_once_with(0, 19)

    def test_limit_validation_too_high(self):
        client = _create_client()
        resp = client.get("/sessions?limit=200")
        assert resp.status_code == 422  # Validation error: le=100

    def test_limit_validation_too_low(self):
        client = _create_client()
        resp = client.get("/sessions?limit=0")
        assert resp.status_code == 422  # Validation error: ge=1

    def test_offset_validation_negative(self):
        client = _create_client()
        resp = client.get("/sessions?offset=-1")
        assert resp.status_code == 422  # Validation error: ge=0

    @patch("supabase_client.get_supabase")
    def test_filters_by_authenticated_user_id(self, mock_get_sb):
        sb = _mock_sb(data=[], count=0)
        mock_get_sb.return_value = sb
        client = _create_client()

        client.get("/sessions")

        # The first .eq() call should filter by user_id
        sb.eq.assert_called_once_with("user_id", "user-123-uuid")

    @patch("supabase_client.get_supabase")
    def test_multiple_sessions_with_total(self, mock_get_sb):
        sessions = [
            {"id": f"sess-{i}", "user_id": "user-123-uuid", "created_at": f"2026-02-0{i}T10:00:00+00:00"}
            for i in range(1, 4)
        ]
        mock_get_sb.return_value = _mock_sb(data=sessions, count=25)
        client = _create_client()

        resp = client.get("/sessions")

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["sessions"]) == 3
        assert body["total"] == 25  # total from count, not len(data)
