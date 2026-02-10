"""Tests for export routes (routes/export_sheets.py).

Tests Google Sheets export endpoints: POST /api/export/google-sheets and history.
Uses mocked authentication, OAuth, and Google Sheets API.

STORY-180: Google Sheets Export - Export Routes Tests
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime, timezone


@pytest.fixture
def app():
    """Create test FastAPI app with export routes."""
    from fastapi import FastAPI
    from routes.export_sheets import router

    test_app = FastAPI()
    test_app.include_router(router)

    return test_app


@pytest.fixture
def client(app, mock_user):
    """Create test client with mocked authentication."""
    from auth import require_auth

    # Override require_auth dependency
    def mock_require_auth():
        return mock_user

    app.dependency_overrides[require_auth] = mock_require_auth

    client = TestClient(app)
    yield client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client(app):
    """Create test client WITHOUT authentication override."""
    return TestClient(app)


class TestExportToGoogleSheets:
    """Test suite for POST /api/export/google-sheets endpoint."""

    def test_requires_authentication(self, unauthenticated_client, mock_licitacoes):
        """Should return 401 when not authenticated."""
        response = unauthenticated_client.post(
            "/api/export/google-sheets",
            json={
                "licitacoes": mock_licitacoes,
                "title": "SmartLic - Test",
                "mode": "create"
            }
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_401_when_no_oauth_token(self, client, mock_user, mock_licitacoes):
        """Should return 401 when user hasn't authorized Google Sheets."""
        with patch("routes.export_sheets.get_user_google_token", new_callable=AsyncMock) as mock_get_token:
            mock_get_token.return_value = None  # No OAuth token

            response = client.post(
                "/api/export/google-sheets",
                json={
                    "licitacoes": mock_licitacoes,
                    "title": "SmartLic - Test",
                    "mode": "create"
                }
            )

            assert response.status_code == 401
            assert "não autorizado" in response.json()["detail"].lower() or "autorizado" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_creates_spreadsheet_successfully(self, client, mock_user, mock_licitacoes):
        """Should create spreadsheet and return URL."""
        mock_export_result = {
            "spreadsheet_id": "test-spreadsheet-id-123",
            "spreadsheet_url": "https://docs.google.com/spreadsheets/d/test-spreadsheet-id-123",
            "total_rows": 1
        }

        with patch("routes.export_sheets.get_user_google_token", new_callable=AsyncMock) as mock_get_token:
            mock_get_token.return_value = "ya29.access_token"

            with patch("routes.export_sheets.GoogleSheetsExporter") as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter.create_spreadsheet = AsyncMock(return_value=mock_export_result)
                mock_exporter_class.return_value = mock_exporter

                with patch("routes.export_sheets._save_export_history", new_callable=AsyncMock):
                    response = client.post(
                        "/api/export/google-sheets",
                        json={
                            "licitacoes": mock_licitacoes,
                            "title": "SmartLic - Uniformes - SP",
                            "mode": "create"
                        }
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data["spreadsheet_id"] == "test-spreadsheet-id-123"
                    assert data["spreadsheet_url"] == "https://docs.google.com/spreadsheets/d/test-spreadsheet-id-123"
                    assert data["total_rows"] == 1

    @pytest.mark.asyncio
    async def test_updates_spreadsheet_successfully(self, client, mock_user, mock_licitacoes):
        """Should update existing spreadsheet."""
        mock_update_result = {
            "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
            "spreadsheet_url": "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
            "total_rows": 1,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        with patch("routes.export_sheets.get_user_google_token", new_callable=AsyncMock) as mock_get_token:
            mock_get_token.return_value = "ya29.access_token"

            with patch("routes.export_sheets.GoogleSheetsExporter") as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter.update_spreadsheet = AsyncMock(return_value=mock_update_result)
                mock_exporter_class.return_value = mock_exporter

                with patch("routes.export_sheets._save_export_history", new_callable=AsyncMock):
                    response = client.post(
                        "/api/export/google-sheets",
                        json={
                            "licitacoes": mock_licitacoes,
                            "title": "SmartLic - Update",
                            "mode": "update",
                            "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
                        }
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data["spreadsheet_id"] == "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
                    assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_saves_export_history(self, client, mock_user, mock_licitacoes):
        """Should save export to history table."""
        mock_export_result = {
            "spreadsheet_id": "test-id",
            "spreadsheet_url": "https://docs.google.com/spreadsheets/d/test-id",
            "total_rows": 1
        }

        with patch("routes.export_sheets.get_user_google_token", new_callable=AsyncMock) as mock_get_token:
            mock_get_token.return_value = "ya29.access_token"

            with patch("routes.export_sheets.GoogleSheetsExporter") as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter.create_spreadsheet = AsyncMock(return_value=mock_export_result)
                mock_exporter_class.return_value = mock_exporter

                with patch("routes.export_sheets._save_export_history", new_callable=AsyncMock) as mock_save:
                    response = client.post(
                        "/api/export/google-sheets",
                        json={
                            "licitacoes": mock_licitacoes,
                            "title": "SmartLic - Test",
                            "mode": "create"
                        }
                    )

                    # Verify history was saved
                    mock_save.assert_called_once()
                    call_args = mock_save.call_args[1]
                    assert call_args["user_id"] == "user-123-uuid"
                    assert call_args["spreadsheet_id"] == "test-id"

    @pytest.mark.asyncio
    async def test_returns_403_on_permission_error(self, client, mock_user, mock_licitacoes):
        """Should return 403 when token is revoked or insufficient permissions."""
        from fastapi import HTTPException

        with patch("routes.export_sheets.get_user_google_token", new_callable=AsyncMock) as mock_get_token:
            mock_get_token.return_value = "ya29.access_token"

            with patch("routes.export_sheets.GoogleSheetsExporter") as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter.create_spreadsheet = AsyncMock(
                    side_effect=HTTPException(status_code=403, detail="Token revoked")
                )
                mock_exporter_class.return_value = mock_exporter

                response = client.post(
                    "/api/export/google-sheets",
                    json={
                        "licitacoes": mock_licitacoes,
                        "title": "SmartLic - Test",
                        "mode": "create"
                    }
                )

                assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_returns_429_on_rate_limit(self, client, mock_user, mock_licitacoes):
        """Should return 429 when Google API quota exceeded."""
        from fastapi import HTTPException

        with patch("routes.export_sheets.get_user_google_token", new_callable=AsyncMock) as mock_get_token:
            mock_get_token.return_value = "ya29.access_token"

            with patch("routes.export_sheets.GoogleSheetsExporter") as mock_exporter_class:
                mock_exporter = Mock()
                mock_exporter.create_spreadsheet = AsyncMock(
                    side_effect=HTTPException(status_code=429, detail="Rate limit exceeded")
                )
                mock_exporter_class.return_value = mock_exporter

                response = client.post(
                    "/api/export/google-sheets",
                    json={
                        "licitacoes": mock_licitacoes,
                        "title": "SmartLic - Test",
                        "mode": "create"
                    }
                )

                assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_validates_request_schema(self, client, mock_user):
        """Should validate request body against schema."""
        # Missing required field 'licitacoes'
        response = client.post(
            "/api/export/google-sheets",
            json={
                "title": "SmartLic - Test",
                "mode": "create"
            }
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_rejects_empty_licitacoes_list(self, client, mock_user):
        """Should reject empty licitacoes list."""
        response = client.post(
            "/api/export/google-sheets",
            json={
                "licitacoes": [],  # Empty list
                "title": "SmartLic - Test",
                "mode": "create"
            }
        )

        assert response.status_code == 422  # Validation error


class TestGetExportHistory:
    """Test suite for GET /api/export/google-sheets/history endpoint."""

    def test_requires_authentication(self, unauthenticated_client):
        """Should return 401 when not authenticated."""
        response = unauthenticated_client.get("/api/export/google-sheets/history")

        assert response.status_code == 401

    def test_returns_export_history(self, client, mock_user):
        """Should return user's export history."""
        mock_history_data = [
            {
                "id": "export-1",
                "spreadsheet_id": "sheet-1",
                "spreadsheet_url": "https://docs.google.com/spreadsheets/d/sheet-1",
                "search_params": {"ufs": ["SP"], "setor": "Uniformes"},
                "total_rows": 142,
                "created_at": "2026-02-09T15:30:00Z",
                "last_updated_at": "2026-02-09T15:30:00Z"
            },
            {
                "id": "export-2",
                "spreadsheet_id": "sheet-2",
                "spreadsheet_url": "https://docs.google.com/spreadsheets/d/sheet-2",
                "search_params": {"ufs": ["RJ"], "setor": "EPIs"},
                "total_rows": 89,
                "created_at": "2026-02-08T10:15:00Z",
                "last_updated_at": "2026-02-08T10:15:00Z"
            }
        ]

        mock_supabase = Mock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = Mock(
            data=mock_history_data
        )

        with patch("routes.export_sheets.get_supabase", return_value=mock_supabase):
            response = client.get("/api/export/google-sheets/history")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert len(data["exports"]) == 2
            assert data["exports"][0]["spreadsheet_id"] == "sheet-1"

    def test_respects_limit_parameter(self, client, mock_user):
        """Should respect limit query parameter."""
        mock_supabase = Mock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = Mock(
            data=[]
        )

        with patch("routes.export_sheets.get_supabase", return_value=mock_supabase):
            response = client.get("/api/export/google-sheets/history?limit=20")

            assert response.status_code == 200

            # Verify limit was passed to query
            mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.assert_called_with(20)

    def test_caps_limit_at_100(self, client, mock_user):
        """Should cap limit at 100 even if higher value requested."""
        mock_supabase = Mock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = Mock(
            data=[]
        )

        with patch("routes.export_sheets.get_supabase", return_value=mock_supabase):
            response = client.get("/api/export/google-sheets/history?limit=500")

            assert response.status_code == 200

            # Verify limit was capped at 100
            mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.assert_called_with(100)

    def test_returns_empty_list_when_no_history(self, client, mock_user):
        """Should return empty list when user has no export history."""
        mock_supabase = Mock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = Mock(
            data=[]
        )

        with patch("routes.export_sheets.get_supabase", return_value=mock_supabase):
            response = client.get("/api/export/google-sheets/history")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
            assert data["exports"] == []

    def test_handles_database_errors(self, client, mock_user):
        """Should return 500 on database errors."""
        mock_supabase = Mock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.side_effect = Exception("Database error")

        with patch("routes.export_sheets.get_supabase", return_value=mock_supabase):
            response = client.get("/api/export/google-sheets/history")

            assert response.status_code == 500
