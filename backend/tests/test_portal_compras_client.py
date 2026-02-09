"""Tests for PortalComprasAdapter (STORY-177 AC3)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from clients.portal_compras_client import PortalComprasAdapter
from clients.base import SourceStatus


@pytest.fixture
def adapter():
    return PortalComprasAdapter(api_key="test-key-123", timeout=5)


@pytest.fixture
def adapter_no_key():
    return PortalComprasAdapter(api_key="", timeout=5)


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_with_valid_key(self, adapter):
        """Test health_check with API key → AVAILABLE."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_health_check_no_key(self, adapter_no_key):
        """Test health_check without API key → UNAVAILABLE."""
        status = await adapter_no_key.health_check()
        assert status == SourceStatus.UNAVAILABLE


class TestFetch:
    @pytest.mark.asyncio
    async def test_fetch_with_mock_results(self, adapter):
        """Test fetch with mock results."""
        mock_response = {
            "data": [
                {
                    "codigo": "P001",
                    "objeto": "Uniformes escolares",
                    "valorEstimado": 50000.0,
                    "uf": "SP",
                    "municipio": "Campinas",
                    "orgao": {"nome": "Prefeitura", "cnpj": "111"},
                },
            ],
            "totalPaginas": 1,
            "total": 1,
        }

        adapter._request_with_retry = AsyncMock(return_value=mock_response)

        records = []
        async for record in adapter.fetch("2026-01-01", "2026-01-31", ufs={"SP"}):
            records.append(record)

        assert len(records) == 1
        assert records[0].source_id == "P001"
        assert records[0].uf == "SP"

    @pytest.mark.asyncio
    async def test_fetch_no_api_key_returns_empty(self, adapter_no_key):
        """Test that fetch with no API key returns empty (no crash)."""
        records = []
        async for record in adapter_no_key.fetch("2026-01-01", "2026-01-31"):
            records.append(record)

        assert len(records) == 0


class TestMetadata:
    def test_metadata(self, adapter):
        """Test adapter metadata."""
        assert adapter.metadata.code == "PORTAL_COMPRAS"
        assert adapter.metadata.priority == 2
