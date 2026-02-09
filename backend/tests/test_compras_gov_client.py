"""Tests for ComprasGovAdapter (STORY-177 AC2)."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from clients.compras_gov_client import ComprasGovAdapter
from clients.base import SourceStatus, UnifiedProcurement


@pytest.fixture
def adapter():
    return ComprasGovAdapter(timeout=5)


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_available(self, adapter):
        """Test health_check with HTTP 200 → AVAILABLE."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_health_check_timeout(self, adapter):
        """Test health_check with timeout → UNAVAILABLE."""
        import httpx
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.UNAVAILABLE


class TestNormalize:
    def test_normalize_complete_record(self, adapter):
        """Test normalize with a complete API response record."""
        raw = {
            "identificador": "12345",
            "objeto": "Aquisicao de uniformes escolares",
            "valor_licitacao": 150000.0,
            "orgao_nome": "Prefeitura Municipal",
            "orgao_cnpj": "12.345.678/0001-00",
            "uf": "SP",
            "municipio": "Sao Paulo",
            "data_publicacao": "2026-01-15",
            "data_abertura": "2026-02-01",
            "numero_aviso": "PE-001",
            "ano": "2026",
            "modalidade_licitacao": "Pregao Eletronico",
            "situacao": "Publicada",
        }

        record = adapter.normalize(raw)

        assert isinstance(record, UnifiedProcurement)
        assert record.source_id == "12345"
        assert record.source_name == "COMPRAS_GOV"
        assert record.objeto == "Aquisicao de uniformes escolares"
        assert record.valor_estimado == 150000.0
        assert record.orgao == "Prefeitura Municipal"
        assert record.uf == "SP"
        assert record.esfera == "F"  # Federal
        assert record.numero_edital == "PE-001"

    def test_normalize_missing_fields(self, adapter):
        """Test normalize with missing optional fields → defaults without crash."""
        raw = {
            "identificador": "99999",
        }

        record = adapter.normalize(raw)

        assert record.source_id == "99999"
        assert record.source_name == "COMPRAS_GOV"
        assert record.objeto == ""
        assert record.valor_estimado == 0.0
        assert record.orgao == ""

    def test_normalize_no_id_raises(self, adapter):
        """Test normalize with no source_id raises SourceParseError."""
        from clients.base import SourceParseError
        raw = {"objeto": "Something"}

        with pytest.raises(SourceParseError):
            adapter.normalize(raw)

    def test_normalize_string_value(self, adapter):
        """Test normalize handles string value format."""
        raw = {
            "identificador": "123",
            "valor_licitacao": "150000",
        }

        record = adapter.normalize(raw)
        assert record.valor_estimado == 150000.0

    def test_normalize_alternative_field_names(self, adapter):
        """Test normalize tries alternative field names."""
        raw = {
            "id": "alt-001",
            "descricao": "Servico de limpeza",
            "nome_orgao": "Tribunal Regional",
            "cnpj": "98765432000100",
            "estado": "RJ",
            "cidade": "Rio de Janeiro",
        }

        record = adapter.normalize(raw)
        assert record.source_id == "alt-001"
        assert record.objeto == "Servico de limpeza"
        assert record.orgao == "Tribunal Regional"
        assert record.cnpj_orgao == "98765432000100"
        assert record.uf == "RJ"
        assert record.municipio == "Rio de Janeiro"


class TestFetch:
    @pytest.mark.asyncio
    async def test_fetch_single_page(self, adapter):
        """Test fetch with 1 page of results → yields correct records."""
        mock_response = {
            "_embedded": {
                "licitacoes": [
                    {"identificador": "1", "objeto": "Test 1", "uf": "SP"},
                    {"identificador": "2", "objeto": "Test 2", "uf": "RJ"},
                ]
            },
            "count": 2,
        }

        adapter._request_with_retry = AsyncMock(return_value=mock_response)

        records = []
        async for record in adapter.fetch("2026-01-01", "2026-01-31"):
            records.append(record)

        assert len(records) == 2
        assert records[0].source_id == "1"
        assert records[1].source_id == "2"

    @pytest.mark.asyncio
    async def test_fetch_with_uf_filter(self, adapter):
        """Test fetch with UF filter → excludes non-matching UFs."""
        mock_response = {
            "_embedded": {
                "licitacoes": [
                    {"identificador": "1", "objeto": "Test 1", "uf": "SP"},
                    {"identificador": "2", "objeto": "Test 2", "uf": "RJ"},
                    {"identificador": "3", "objeto": "Test 3", "uf": "SP"},
                ]
            },
            "count": 3,
        }

        adapter._request_with_retry = AsyncMock(return_value=mock_response)

        records = []
        async for record in adapter.fetch("2026-01-01", "2026-01-31", ufs={"SP"}):
            records.append(record)

        assert len(records) == 2
        assert all(r.uf == "SP" for r in records)

    @pytest.mark.asyncio
    async def test_fetch_pagination(self, adapter):
        """Test fetch with 2+ pages → yields all results."""
        page1 = {
            "_embedded": {
                "licitacoes": [{"identificador": str(i), "uf": "SP"} for i in range(500)]
            },
            "count": 600,
        }
        page2 = {
            "_embedded": {
                "licitacoes": [{"identificador": str(i + 500), "uf": "SP"} for i in range(100)]
            },
            "count": 600,
        }

        adapter._request_with_retry = AsyncMock(side_effect=[page1, page2])

        records = []
        async for record in adapter.fetch("2026-01-01", "2026-01-31"):
            records.append(record)

        assert len(records) == 600
        assert adapter._request_with_retry.call_count == 2


class TestMetadata:
    def test_metadata(self, adapter):
        """Test adapter metadata is correct."""
        assert adapter.metadata.code == "COMPRAS_GOV"
        assert adapter.metadata.priority == 4
        assert adapter.metadata.rate_limit_rps == 2.0

    def test_code_property(self, adapter):
        """Test code property."""
        assert adapter.code == "COMPRAS_GOV"

    def test_name_property(self, adapter):
        """Test name property."""
        assert "ComprasGov" in adapter.name


class TestCleanup:
    @pytest.mark.asyncio
    async def test_context_manager(self, adapter):
        """Test async context manager."""
        async with adapter as a:
            assert a is adapter

    @pytest.mark.asyncio
    async def test_close(self, adapter):
        """Test close without client."""
        await adapter.close()  # Should not raise
