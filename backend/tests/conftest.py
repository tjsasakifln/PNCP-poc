"""Pytest configuration and shared fixtures for STORY-180 tests.

Provides common mocks for authentication, Supabase, and external APIs.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {
        "id": "user-123-uuid",
        "email": "test@example.com",
        "role": "authenticated"
    }


@pytest.fixture
def mock_supabase():
    """Mock Supabase client with common operations."""
    mock = Mock()

    # Mock table operations
    mock.table.return_value = mock
    mock.select.return_value = mock
    mock.insert.return_value = mock
    mock.upsert.return_value = mock
    mock.update.return_value = mock
    mock.delete.return_value = mock
    mock.eq.return_value = mock
    mock.order.return_value = mock
    mock.limit.return_value = mock
    mock.single.return_value = mock

    # Mock execute with default empty response
    mock.execute.return_value = Mock(data=[])

    return mock


@pytest.fixture
def mock_async_http_client():
    """Mock httpx.AsyncClient for OAuth requests."""
    mock_client = AsyncMock()

    # Mock context manager
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    # Mock post method
    mock_client.post = AsyncMock()

    return mock_client


@pytest.fixture
def mock_google_sheets_service():
    """Mock Google Sheets API service."""
    mock_service = Mock()
    mock_spreadsheets = Mock()

    # Mock spreadsheets operations
    mock_service.spreadsheets.return_value = mock_spreadsheets

    # Mock create
    mock_spreadsheets.create.return_value.execute.return_value = {
        "spreadsheetId": "test-spreadsheet-id",
        "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/test-spreadsheet-id",
        "sheets": [{"properties": {"sheetId": 0, "title": "Sheet1"}}]
    }

    # Mock get
    mock_spreadsheets.get.return_value.execute.return_value = {
        "spreadsheetId": "test-spreadsheet-id",
        "properties": {"title": "Test Spreadsheet"}
    }

    # Mock values operations
    mock_values = Mock()
    mock_spreadsheets.values.return_value = mock_values
    mock_values.update.return_value.execute.return_value = {}
    mock_values.clear.return_value.execute.return_value = {}

    # Mock batchUpdate
    mock_spreadsheets.batchUpdate.return_value.execute.return_value = {}

    return mock_service


@pytest.fixture
def override_require_auth(mock_user):
    """Override require_auth dependency for route tests."""
    from auth import require_auth

    def mock_auth():
        return mock_user

    # Store original for restoration
    original_auth = require_auth

    yield mock_auth

    # Restore original (if needed)
    # Note: FastAPI TestClient handles dependency overrides automatically


@pytest.fixture
def mock_licitacoes():
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
        }
    ]


@pytest.fixture
def mock_oauth_tokens():
    """Mock OAuth token response."""
    return {
        "access_token": "ya29.a0AfH6SMBxyz123_test_token",
        "refresh_token": "1//refresh_token_xyz",
        "expires_in": 3600,
        "scope": "https://www.googleapis.com/auth/spreadsheets",
        "token_type": "Bearer"
    }


@pytest.fixture
def mock_expires_at():
    """Mock token expiration time (1 hour from now)."""
    return datetime.now(timezone.utc) + timedelta(hours=1)


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("ENCRYPTION_KEY", "bzc732A921Puw9JN4lrzMo1nw0EjlcUdAyR6Z6N7Sqc=")  # Valid Fernet key for testing
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
