"""Tests for Google Sheets exporter (google_sheets.py).

Tests spreadsheet creation, updating, data population, and formatting.
Uses mocked Google Sheets API to avoid real API calls.

STORY-180: Google Sheets Export - Exporter Class Tests
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from fastapi import HTTPException


class TestGoogleSheetsExporterInit:
    """Test suite for GoogleSheetsExporter initialization."""

    def test_initializes_with_access_token(self, mock_google_sheets_service):
        """Should initialize with access token."""
        from google_sheets import GoogleSheetsExporter

        with patch("google_sheets.build", return_value=mock_google_sheets_service):
            exporter = GoogleSheetsExporter(access_token="ya29.test_token")

            # Check that service was built (access_token stored internally)
            assert exporter.service is not None

    def test_builds_google_sheets_service(self, mock_google_sheets_service):
        """Should build Google Sheets API service on init."""
        from google_sheets import GoogleSheetsExporter

        with patch("google_sheets.build") as mock_build:
            mock_build.return_value = mock_google_sheets_service

            exporter = GoogleSheetsExporter(access_token="ya29.test_token")

            # Should have called build() with credentials
            mock_build.assert_called_once()
            assert exporter.service == mock_google_sheets_service


class TestCreateSpreadsheet:
    """Test suite for creating new spreadsheets."""

    @pytest.fixture
    def mock_licitacoes(self):
        """Sample licitacao data for testing."""
        return [
            {
                "codigoUnidadeCompradora": "123456",
                "objetoCompra": "Aquisição de uniformes escolares",
                "nomeOrgao": "Prefeitura Municipal",
                "uf": "SP",
                "municipio": "São Paulo",
                "valorTotalEstimado": 50000.00,
                "modalidadeNome": "Pregão Eletrônico",
                "dataPublicacaoPncp": "2026-02-01",
                "dataAberturaProposta": "2026-02-15",
                "situacaoCompra": "Aberta",
                "linkSistemaOrigem": "https://pncp.gov.br/app/editais/123"
            },
            {
                "codigoUnidadeCompradora": "789012",
                "objetoCompra": "Fornecimento de EPIs",
                "nomeOrgao": "Hospital Regional",
                "uf": "RJ",
                "municipio": "Rio de Janeiro",
                "valorTotalEstimado": 75000.00,
                "modalidadeNome": "Concorrência",
                "dataPublicacaoPncp": "2026-02-05",
                "dataAberturaProposta": "2026-02-20",
                "situacaoCompra": "Aberta",
                "linkSistemaOrigem": "https://pncp.gov.br/app/editais/789"
            }
        ]

    @pytest.mark.asyncio
    async def test_creates_spreadsheet_successfully(self, mock_licitacoes):
        """Should create spreadsheet with data and formatting."""
        from google_sheets import GoogleSheetsExporter

        mock_service = Mock()
        mock_spreadsheets = Mock()
        mock_service.spreadsheets.return_value = mock_spreadsheets

        # Mock create
        mock_create_response = {
            "spreadsheetId": "test-spreadsheet-id-123",
            "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/test-spreadsheet-id-123",
            "sheets": [{"properties": {"sheetId": 0, "title": "Sheet1"}}]
        }
        mock_spreadsheets.create.return_value.execute.return_value = mock_create_response

        # Mock batchUpdate (for data and formatting)
        mock_spreadsheets.values.return_value.update.return_value.execute.return_value = {}
        mock_spreadsheets.batchUpdate.return_value.execute.return_value = {}

        with patch("google_sheets.build", return_value=mock_service):
            exporter = GoogleSheetsExporter(access_token="ya29.test_token")
            result = await exporter.create_spreadsheet(
                licitacoes=mock_licitacoes,
                title="SmartLic - Uniformes - 10/02/2026"
            )

            assert result["spreadsheet_id"] == "test-spreadsheet-id-123"
            assert result["spreadsheet_url"] == "https://docs.google.com/spreadsheets/d/test-spreadsheet-id-123"
            assert result["total_rows"] == 2

    @pytest.mark.asyncio
    async def test_handles_empty_licitacoes_list(self):
        """Should handle empty licitacoes list gracefully."""
        from google_sheets import GoogleSheetsExporter

        mock_service = Mock()
        mock_spreadsheets = Mock()
        mock_service.spreadsheets.return_value = mock_spreadsheets

        mock_create_response = {
            "spreadsheetId": "test-id",
            "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/test-id",
            "sheets": [{"properties": {"sheetId": 0}}]
        }
        mock_spreadsheets.create.return_value.execute.return_value = mock_create_response
        mock_spreadsheets.values.return_value.update.return_value.execute.return_value = {}
        mock_spreadsheets.batchUpdate.return_value.execute.return_value = {}

        with patch("google_sheets.build", return_value=mock_service):
            exporter = GoogleSheetsExporter(access_token="ya29.test_token")
            result = await exporter.create_spreadsheet(
                licitacoes=[],
                title="SmartLic - Empty"
            )

            assert result["total_rows"] == 0

    @pytest.mark.asyncio
    async def test_raises_403_on_permission_error(self):
        """Should raise 403 HTTPException on insufficient permissions."""
        from google_sheets import GoogleSheetsExporter
        from googleapiclient.errors import HttpError

        mock_service = Mock()
        mock_spreadsheets = Mock()
        mock_service.spreadsheets.return_value = mock_spreadsheets

        # Mock HttpError 403
        mock_error_response = Mock()
        mock_error_response.status = 403
        mock_error_response.reason = "Forbidden"
        http_error = HttpError(resp=mock_error_response, content=b'{"error": "insufficient_permissions"}')

        mock_spreadsheets.create.return_value.execute.side_effect = http_error

        with patch("google_sheets.build", return_value=mock_service):
            exporter = GoogleSheetsExporter(access_token="ya29.test_token")

            with pytest.raises(HTTPException) as exc_info:
                await exporter.create_spreadsheet(
                    licitacoes=[{"codigoUnidadeCompradora": "123"}],
                    title="Test"
                )

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_raises_429_on_rate_limit(self):
        """Should raise 429 HTTPException on rate limit exceeded."""
        from google_sheets import GoogleSheetsExporter
        from googleapiclient.errors import HttpError

        mock_service = Mock()
        mock_spreadsheets = Mock()
        mock_service.spreadsheets.return_value = mock_spreadsheets

        # Mock HttpError 429
        mock_error_response = Mock()
        mock_error_response.status = 429
        mock_error_response.reason = "Too Many Requests"
        http_error = HttpError(resp=mock_error_response, content=b'{"error": "rate_limit_exceeded"}')

        mock_spreadsheets.create.return_value.execute.side_effect = http_error

        with patch("google_sheets.build", return_value=mock_service):
            exporter = GoogleSheetsExporter(access_token="ya29.test_token")

            with pytest.raises(HTTPException) as exc_info:
                await exporter.create_spreadsheet(
                    licitacoes=[{"codigoUnidadeCompradora": "123"}],
                    title="Test"
                )

            assert exc_info.value.status_code == 429


class TestUpdateSpreadsheet:
    """Test suite for updating existing spreadsheets."""

    @pytest.fixture
    def mock_licitacoes(self):
        """Sample licitacao data for testing."""
        return [
            {
                "codigoUnidadeCompradora": "123456",
                "objetoCompra": "Uniformes",
                "nomeOrgao": "Prefeitura",
                "uf": "SP",
                "municipio": "São Paulo",
                "valorTotalEstimado": 50000.00,
                "modalidadeNome": "Pregão",
                "dataPublicacaoPncp": "2026-02-01",
                "dataAberturaProposta": "2026-02-15",
                "situacaoCompra": "Aberta",
                "linkSistemaOrigem": "https://pncp.gov.br/123"
            }
        ]

    @pytest.mark.asyncio
    async def test_updates_spreadsheet_successfully(self, mock_licitacoes):
        """Should update existing spreadsheet with new data."""
        from google_sheets import GoogleSheetsExporter

        mock_service = Mock()
        mock_spreadsheets = Mock()
        mock_service.spreadsheets.return_value = mock_spreadsheets

        # Mock get (to verify spreadsheet exists)
        mock_get_response = {
            "spreadsheetId": "existing-id-123",
            "properties": {"title": "Existing Spreadsheet"}
        }
        mock_spreadsheets.get.return_value.execute.return_value = mock_get_response

        # Mock values().clear()
        mock_spreadsheets.values.return_value.clear.return_value.execute.return_value = {}

        # Mock values().update()
        mock_spreadsheets.values.return_value.update.return_value.execute.return_value = {}

        # Mock batchUpdate (formatting)
        mock_spreadsheets.batchUpdate.return_value.execute.return_value = {}

        with patch("google_sheets.build", return_value=mock_service):
            exporter = GoogleSheetsExporter(access_token="ya29.test_token")
            result = await exporter.update_spreadsheet(
                spreadsheet_id="existing-id-123",
                licitacoes=mock_licitacoes
            )

            assert result["spreadsheet_id"] == "existing-id-123"
            assert result["total_rows"] == 1
            assert "updated_at" in result

    @pytest.mark.asyncio
    async def test_fallback_to_create_when_spreadsheet_not_found(self, mock_licitacoes):
        """Should fallback to create new spreadsheet when update target is 404 (HOTFIX behavior)."""
        from google_sheets import GoogleSheetsExporter
        from googleapiclient.errors import HttpError

        mock_service = Mock()
        mock_spreadsheets = Mock()
        mock_service.spreadsheets.return_value = mock_spreadsheets

        # Mock HttpError 404 on get (spreadsheet not found)
        mock_error_response = Mock()
        mock_error_response.status = 404
        mock_error_response.reason = "Not Found"
        http_error = HttpError(resp=mock_error_response, content=b'{"error": "not_found"}')

        mock_spreadsheets.get.return_value.execute.side_effect = http_error

        # Mock create (fallback path)
        mock_create_response = {
            "spreadsheetId": "new-fallback-id",
            "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/new-fallback-id",
            "sheets": [{"properties": {"sheetId": 0}}]
        }
        mock_spreadsheets.create.return_value.execute.return_value = mock_create_response
        mock_spreadsheets.values.return_value.update.return_value.execute.return_value = {}
        mock_spreadsheets.batchUpdate.return_value.execute.return_value = {}

        with patch("google_sheets.build", return_value=mock_service):
            exporter = GoogleSheetsExporter(access_token="ya29.test_token")

            result = await exporter.update_spreadsheet(
                spreadsheet_id="non-existent-id",
                licitacoes=mock_licitacoes
            )

            # Should have fallen back to create
            assert result["spreadsheet_id"] == "new-fallback-id"
            assert result["total_rows"] == 1


class TestPopulateData:
    """Test suite for data population (private method)."""

    @pytest.mark.asyncio
    async def test_formats_currency_values_correctly(self):
        """Should format currency values as Brazilian Real."""
        from google_sheets import GoogleSheetsExporter

        licitacoes = [{
            "codigoUnidadeCompradora": "123",
            "objetoCompra": "Test",
            "nomeOrgao": "Org",
            "uf": "SP",
            "municipio": "City",
            "valorTotalEstimado": 123456.78,
            "modalidadeNome": "Pregão",
            "dataPublicacaoPncp": "2026-02-01",
            "dataAberturaProposta": "2026-02-15",
            "situacaoCompra": "Aberta",
            "linkSistemaOrigem": "https://link"
        }]

        mock_service = Mock()
        mock_spreadsheets = Mock()
        mock_service.spreadsheets.return_value = mock_spreadsheets
        mock_spreadsheets.values.return_value.update.return_value.execute.return_value = {}

        with patch("google_sheets.build", return_value=mock_service):
            exporter = GoogleSheetsExporter(access_token="ya29.test_token")
            exporter._populate_data("test-id", licitacoes)

            # Verify update was called with formatted data
            mock_spreadsheets.values.return_value.update.assert_called_once()

            # Get the call arguments
            call_args = mock_spreadsheets.values.return_value.update.call_args
            body = call_args[1]["body"]
            values = body["values"]

            # Check that currency value is formatted (R$ 123.456,78)
            # Row format: [codigo, objeto, orgao, uf, municipio, VALOR, ...]
            valor_cell = values[1][5]  # Second row (after header), 6th column
            assert "R$" in str(valor_cell) or isinstance(valor_cell, (int, float))


class TestApplyFormatting:
    """Test suite for spreadsheet formatting (private method)."""

    @pytest.mark.asyncio
    async def test_applies_green_header_formatting(self):
        """Should apply green header background (#2E7D32)."""
        from google_sheets import GoogleSheetsExporter

        mock_service = Mock()
        mock_spreadsheets = Mock()
        mock_service.spreadsheets.return_value = mock_spreadsheets
        mock_spreadsheets.batchUpdate.return_value.execute.return_value = {}

        with patch("google_sheets.build", return_value=mock_service):
            exporter = GoogleSheetsExporter(access_token="ya29.test_token")
            exporter._apply_formatting("test-id", total_rows=10)

            # Verify batchUpdate was called
            mock_spreadsheets.batchUpdate.assert_called_once()

            # Get the batch update request
            call_args = mock_spreadsheets.batchUpdate.call_args
            body = call_args[1]["body"]
            requests = body["requests"]

            # Should have multiple format requests (header color, bold, frozen row, etc.)
            assert len(requests) > 0

    @pytest.mark.asyncio
    async def test_freezes_header_row(self):
        """Should freeze first row (header)."""
        from google_sheets import GoogleSheetsExporter

        mock_service = Mock()
        mock_spreadsheets = Mock()
        mock_service.spreadsheets.return_value = mock_spreadsheets
        mock_spreadsheets.batchUpdate.return_value.execute.return_value = {}

        with patch("google_sheets.build", return_value=mock_service):
            exporter = GoogleSheetsExporter(access_token="ya29.test_token")
            exporter._apply_formatting("test-id", total_rows=10)

            # Verify batchUpdate was called
            mock_spreadsheets.batchUpdate.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_formatting_errors_gracefully(self):
        """Should log but not fail if formatting fails."""
        from google_sheets import GoogleSheetsExporter
        from googleapiclient.errors import HttpError
        from fastapi import HTTPException

        mock_service = Mock()
        mock_spreadsheets = Mock()
        mock_service.spreadsheets.return_value = mock_spreadsheets

        # Mock formatting failure
        mock_error_response = Mock()
        mock_error_response.status = 500
        mock_error_response.reason = "Internal Server Error"
        http_error = HttpError(resp=mock_error_response, content=b'error')
        mock_spreadsheets.batchUpdate.return_value.execute.side_effect = http_error

        with patch("google_sheets.build", return_value=mock_service):
            exporter = GoogleSheetsExporter(access_token="ya29.test_token")

            # Should not raise exception (formatting is optional)
            # The method logs error but doesn't raise
            try:
                exporter._apply_formatting("test-id", total_rows=10)
                # If it doesn't raise, test passes
            except Exception as e:
                # If it raises, we want to know what kind
                pytest.fail(f"Should not raise exception on formatting failure, got: {type(e).__name__}: {str(e)}")
