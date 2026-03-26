"""Tests for STORY-331 AC3: PGRST205 defensive guard on organization routes.

All 7 organization endpoints must return HTTP 503 "Feature not yet available"
when the underlying Supabase query raises a PGRST205 schema cache error,
instead of propagating as HTTP 500.
"""

import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport

from main import app
from auth import require_auth

_ORG_SVC_GET_SUPABASE = "services.organization_service.get_supabase"


def _pgrst205_error():
    """Create a realistic PGRST205 exception mimicking postgrest-py."""
    return Exception(
        "{'message': \"Could not find the table 'public.organization_members'\", "
        "'code': 'PGRST205', 'details': None, 'hint': None}"
    )


@pytest.fixture
def mock_user():
    return {"id": "user-001", "email": "test@test.com", "role": "authenticated", "aal": "aal1"}


@pytest.fixture(autouse=True)
def _auth_override(mock_user):
    app.dependency_overrides[require_auth] = lambda: mock_user
    yield
    app.dependency_overrides.clear()


class TestPGRST205Guard:
    """STORY-331 AC3: PGRST205 → HTTP 503 on all organization endpoints."""

    @pytest.mark.asyncio
    async def test_get_my_org_pgrst205_returns_503(self):
        """GET /v1/organizations/me — PGRST205 → 503."""
        with patch(_ORG_SVC_GET_SUPABASE) as mock_sb:
            mock_sb.return_value.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.side_effect = _pgrst205_error()
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/v1/organizations/me")

        assert response.status_code == 503
        assert response.json()["detail"] == "Feature not yet available"

    @pytest.mark.asyncio
    async def test_create_org_pgrst205_returns_503(self):
        """POST /v1/organizations — PGRST205 → 503."""
        with patch(_ORG_SVC_GET_SUPABASE) as mock_sb:
            mock_sb.return_value.table.return_value.insert.return_value.execute.side_effect = _pgrst205_error()
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/v1/organizations",
                    json={"name": "Test Org"},
                )

        assert response.status_code == 503
        assert response.json()["detail"] == "Feature not yet available"

    @pytest.mark.asyncio
    async def test_get_org_pgrst205_returns_503(self):
        """GET /v1/organizations/{id} — PGRST205 → 503."""
        with patch(_ORG_SVC_GET_SUPABASE) as mock_sb:
            mock_sb.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.side_effect = _pgrst205_error()
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/v1/organizations/org-abc")

        assert response.status_code == 503
        assert response.json()["detail"] == "Feature not yet available"

    @pytest.mark.asyncio
    async def test_invite_member_pgrst205_returns_503(self):
        """POST /v1/organizations/{id}/invite — PGRST205 → 503."""
        with patch(_ORG_SVC_GET_SUPABASE) as mock_sb:
            mock_sb.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.side_effect = _pgrst205_error()
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/v1/organizations/org-abc/invite",
                    json={"email": "member@test.com"},
                )

        assert response.status_code == 503
        assert response.json()["detail"] == "Feature not yet available"

    @pytest.mark.asyncio
    async def test_accept_invite_pgrst205_returns_503(self):
        """POST /v1/organizations/{id}/accept — PGRST205 → 503."""
        with patch(_ORG_SVC_GET_SUPABASE) as mock_sb:
            mock_sb.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.side_effect = _pgrst205_error()
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/v1/organizations/org-abc/accept")

        assert response.status_code == 503
        assert response.json()["detail"] == "Feature not yet available"

    @pytest.mark.asyncio
    async def test_remove_member_pgrst205_returns_503(self):
        """DELETE /v1/organizations/{id}/members/{user_id} — PGRST205 → 503."""
        with patch(_ORG_SVC_GET_SUPABASE) as mock_sb:
            mock_sb.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.side_effect = _pgrst205_error()
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete(
                    "/v1/organizations/org-abc/members/user-002"
                )

        assert response.status_code == 503
        assert response.json()["detail"] == "Feature not yet available"

    @pytest.mark.asyncio
    async def test_get_dashboard_pgrst205_returns_503(self):
        """GET /v1/organizations/{id}/dashboard — PGRST205 → 503."""
        with patch(_ORG_SVC_GET_SUPABASE) as mock_sb:
            mock_sb.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.side_effect = _pgrst205_error()
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/v1/organizations/org-abc/dashboard")

        assert response.status_code == 503
        assert response.json()["detail"] == "Feature not yet available"

    @pytest.mark.asyncio
    async def test_update_logo_pgrst205_returns_503(self):
        """PUT /v1/organizations/{id}/logo — PGRST205 → 503."""
        with patch(_ORG_SVC_GET_SUPABASE) as mock_sb:
            mock_sb.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.side_effect = _pgrst205_error()
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.put(
                    "/v1/organizations/org-abc/logo",
                    json={"logo_url": "https://example.com/logo.png"},
                )

        assert response.status_code == 503
        assert response.json()["detail"] == "Feature not yet available"


class TestNonSchemaErrorStillReturns500:
    """Verify non-PGRST205 errors still propagate as 500 (not 503)."""

    @pytest.mark.asyncio
    async def test_generic_error_returns_500_on_create(self):
        """POST /v1/organizations — generic error → 500 (not 503)."""
        with patch(_ORG_SVC_GET_SUPABASE) as mock_sb:
            mock_sb.return_value.table.return_value.insert.return_value.execute.side_effect = RuntimeError("connection refused")
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/v1/organizations",
                    json={"name": "Test Org"},
                )

        assert response.status_code == 500
