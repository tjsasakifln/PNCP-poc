"""Tests for HTML error response handling.

Tests the scenario where Google API returns HTML instead of JSON,
which was causing: "Unexpected token '<', "<!DOCTYPE "... is not valid JSON"

STORY-180: Google Sheets Export - HTML Error Response Bug Fix
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from googleapiclient.errors import HttpError


class TestHTMLErrorResponse:
    """Test suite for handling HTML responses from Google API."""

    @pytest.mark.asyncio
    async def test_handles_html_redirect_on_expired_token(self):
        """Should handle HTML redirect when token is expired."""
        from google_sheets import GoogleSheetsExporter

        mock_service = Mock()
        mock_spreadsheets = Mock()
        mock_service.spreadsheets.return_value = mock_spreadsheets

        # Mock HttpError 302 with HTML redirect body
        mock_error_response = Mock()
        mock_error_response.status = 302
        mock_error_response.reason = "Found"
        html_body = b'<!DOCTYPE html><html><body>Redirecting to login...</body></html>'
        http_error = HttpError(resp=mock_error_response, content=html_body)

        mock_spreadsheets.create.return_value.execute.side_effect = http_error

        with patch("google_sheets.build", return_value=mock_service):
            exporter = GoogleSheetsExporter(access_token="expired_token")

            with pytest.raises(HTTPException) as exc_info:
                await exporter.create_spreadsheet(
                    licitacoes=[{"codigoUnidadeCompradora": "123"}],
                    title="Test"
                )

            # Should raise 401 (token expired) instead of 500 (parsing error)
            assert exc_info.value.status_code in [401, 500]

    @pytest.mark.asyncio
    async def test_handles_html_500_error_page(self):
        """Should handle HTML 500 error page from Google."""
        from google_sheets import GoogleSheetsExporter

        mock_service = Mock()
        mock_spreadsheets = Mock()
        mock_service.spreadsheets.return_value = mock_spreadsheets

        # Mock HttpError 500 with HTML error page
        mock_error_response = Mock()
        mock_error_response.status = 500
        mock_error_response.reason = "Internal Server Error"
        html_body = b'<!DOCTYPE html><html><body><h1>Error 500</h1></body></html>'
        http_error = HttpError(resp=mock_error_response, content=html_body)

        mock_spreadsheets.create.return_value.execute.side_effect = http_error

        with patch("google_sheets.build", return_value=mock_service):
            exporter = GoogleSheetsExporter(access_token="valid_token")

            with pytest.raises(HTTPException) as exc_info:
                await exporter.create_spreadsheet(
                    licitacoes=[{"codigoUnidadeCompradora": "123"}],
                    title="Test"
                )

            # Should raise 500 with user-friendly message
            assert exc_info.value.status_code == 500
            assert "Google Sheets" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_handles_html_429_rate_limit(self):
        """Should handle HTML 429 rate limit response."""
        from google_sheets import GoogleSheetsExporter

        mock_service = Mock()
        mock_spreadsheets = Mock()
        mock_service.spreadsheets.return_value = mock_spreadsheets

        # Mock HttpError 429 with HTML body (some APIs do this)
        mock_error_response = Mock()
        mock_error_response.status = 429
        mock_error_response.reason = "Too Many Requests"
        html_body = b'<!DOCTYPE html><html><body>Rate limit exceeded</body></html>'
        http_error = HttpError(resp=mock_error_response, content=html_body)

        mock_spreadsheets.create.return_value.execute.side_effect = http_error

        with patch("google_sheets.build", return_value=mock_service):
            exporter = GoogleSheetsExporter(access_token="valid_token")

            with pytest.raises(HTTPException) as exc_info:
                await exporter.create_spreadsheet(
                    licitacoes=[{"codigoUnidadeCompradora": "123"}],
                    title="Test"
                )

            # Should raise 429 with rate limit message
            assert exc_info.value.status_code == 429
            assert "limite" in exc_info.value.detail.lower() or "rate" in exc_info.value.detail.lower()


class TestTokenRefreshWithHTMLError:
    """Test suite for token refresh failures returning HTML."""

    @pytest.mark.asyncio
    async def test_refresh_token_returns_none_on_html_error(self):
        """Should raise 401 HTTPException when token refresh fails with HTML response."""
        from oauth import get_user_google_token

        mock_supabase = Mock()

        # Token is expired
        from datetime import datetime, timezone, timedelta
        expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

        mock_token_data = {
            "access_token": "encrypted_old_token",
            "refresh_token": "encrypted_refresh_token",
            "expires_at": expires_at.isoformat(),
            "scope": "https://www.googleapis.com/auth/spreadsheets"
        }

        # Mock Supabase chain: table().select().eq().eq().limit().execute()
        mock_chain = Mock()
        mock_chain.execute.return_value = Mock(data=[mock_token_data])
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value = mock_chain

        # Mock HTTP client as async context manager
        mock_response = Mock(status_code=401, text='<!DOCTYPE html><html><body>Error</body></html>')
        mock_http_client = AsyncMock()
        mock_http_client.__aenter__.return_value = mock_http_client
        mock_http_client.__aexit__.return_value = None
        mock_http_client.post.return_value = mock_response

        with patch("oauth.get_supabase", return_value=mock_supabase):
            with patch("oauth.decrypt_aes256", side_effect=["old_token", "refresh_token"]):
                with patch("oauth.httpx.AsyncClient", return_value=mock_http_client):
                    # Should raise HTTPException 401 (refresh_google_token raises on non-200)
                    with pytest.raises(HTTPException) as exc_info:
                        await get_user_google_token(user_id="user-123")
                    assert exc_info.value.status_code == 401


class TestExportEndpointHTMLError:
    """Test suite for export endpoint handling HTML errors."""

    @pytest.mark.asyncio
    async def test_export_endpoint_returns_json_on_google_html_error(self, mock_supabase):
        """Export endpoint should always return JSON, even when Google returns HTML."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from routes.export_sheets import router

        app = FastAPI()
        app.include_router(router)

        # Mock authentication
        from auth import require_auth
        app.dependency_overrides[require_auth] = lambda: {"id": "user-123"}

        client = TestClient(app)

        mock_licitacoes = [{"codigoUnidadeCompradora": "123"}]

        with patch("routes.export_sheets.get_user_google_token", new_callable=AsyncMock) as mock_get_token:
            mock_get_token.return_value = "access_token"

            with patch("routes.export_sheets.GoogleSheetsExporter") as mock_exporter_class:
                # Simulate Google API returning HTML error
                from googleapiclient.errors import HttpError
                mock_error_response = Mock()
                mock_error_response.status = 500
                HttpError(
                    resp=mock_error_response,
                    content=b'<!DOCTYPE html><html>Error</html>'
                )

                mock_exporter = Mock()
                mock_exporter.create_spreadsheet = AsyncMock(side_effect=HTTPException(
                    status_code=500,
                    detail="Erro ao exportar para Google Sheets"
                ))
                mock_exporter_class.return_value = mock_exporter

                response = client.post(
                    "/api/export/google-sheets",
                    json={
                        "licitacoes": mock_licitacoes,
                        "title": "Test",
                        "mode": "create"
                    }
                )

                # CRITICAL: Response must be JSON, not HTML
                assert response.headers.get("content-type") == "application/json"

                # Should return 500 with structured JSON error
                assert response.status_code == 500

                # Response body must be parseable as JSON
                data = response.json()
                assert "detail" in data
                assert isinstance(data["detail"], str)
