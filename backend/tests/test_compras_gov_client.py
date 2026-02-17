"""Tests for ComprasGovAdapter v3 (STORY-177 AC2, updated for GTM-FIX-027 T5).

These tests cover the basic ComprasGovAdapter interface after the v1 -> v3 migration.
For comprehensive v3 tests, see test_compras_gov_v3.py (87 tests).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

import httpx
from clients.compras_gov_client import ComprasGovAdapter
from clients.base import SourceStatus, UnifiedProcurement, SourceParseError


@pytest.fixture
def adapter():
    return ComprasGovAdapter(timeout=5)


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_available(self, adapter):
        """Test health_check with HTTP 200 -> AVAILABLE."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch.object(asyncio, "get_running_loop") as mock_loop:
            mock_loop.return_value.time.side_effect = [0.0, 0.5]
            status = await adapter.health_check()

        assert status == SourceStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_health_check_timeout(self, adapter):
        """Test health_check with timeout -> UNAVAILABLE."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.UNAVAILABLE


class TestNormalize:
    def test_normalize_complete_record(self, adapter):
        """Test normalize with a complete legacy API response record."""
        raw = {
            "numero_aviso": "PE-001",
            "objeto": "Aquisicao de uniformes escolares",
            "valor_estimado": 150000.0,
            "uasg": {"nome": "Prefeitura Municipal", "cnpj": "12345678000100"},
            "uf": "SP",
            "municipio": "Sao Paulo",
            "data_publicacao": "2026-01-15",
            "data_entrega_proposta": "2026-02-01",
            "ano": "2026",
            "modalidade": {"descricao": "Pregao Eletronico"},
            "situacao": {"descricao": "Publicada"},
        }

        record = adapter.normalize(raw)

        assert isinstance(record, UnifiedProcurement)
        assert record.source_id == "cg_leg_PE-001"
        assert record.source_name == "COMPRAS_GOV"
        assert record.objeto == "Aquisicao de uniformes escolares"
        assert record.valor_estimado == 150000.0
        assert record.orgao == "Prefeitura Municipal"
        assert record.uf == "SP"
        assert record.esfera == "F"  # Federal
        assert record.numero_edital == "PE-001"

    def test_normalize_missing_fields(self, adapter):
        """Test normalize with missing optional fields -> defaults without crash."""
        raw = {
            "numero_aviso": "99999",
        }

        record = adapter.normalize(raw)

        assert record.source_id == "cg_leg_99999"
        assert record.source_name == "COMPRAS_GOV"
        assert record.objeto == ""
        assert record.valor_estimado == 0.0
        assert record.orgao == ""

    def test_normalize_no_id_raises(self, adapter):
        """Test normalize with no source_id raises SourceParseError."""
        raw = {"objeto": "Something"}

        with pytest.raises(SourceParseError):
            adapter.normalize(raw)

    def test_normalize_string_value(self, adapter):
        """Test normalize handles string value format."""
        raw = {
            "numero_aviso": "123",
            "valor_estimado": "150000",
        }

        record = adapter.normalize(raw)
        assert record.valor_estimado == 150000.0

    def test_normalize_lei_14133_record(self, adapter):
        """Test normalize auto-detects Lei 14.133 records."""
        raw = {
            "numeroControlePNCP": "PNCP-001",
            "objetoCompra": "Servico de limpeza",
            "orgaoEntidade": {"razaoSocial": "Tribunal Regional", "cnpj": "98765432000100"},
            "uf": "RJ",
            "modalidadeNome": "Pregao Eletronico",
            "situacaoCompraNome": "Em andamento",
        }

        record = adapter.normalize(raw)
        assert record.source_id == "cg_14133_PNCP-001"
        assert record.objeto == "Servico de limpeza"
        assert record.orgao == "Tribunal Regional"
        assert record.cnpj_orgao == "98765432000100"
        assert record.uf == "RJ"


class TestFetch:
    @pytest.mark.asyncio
    async def test_fetch_single_page(self, adapter):
        """Test fetch yields records from both endpoints."""
        legacy_records = [
            UnifiedProcurement(
                source_id="cg_leg_1", source_name="COMPRAS_GOV", objeto="Test 1", uf="SP"
            ),
        ]
        lei_records = [
            UnifiedProcurement(
                source_id="cg_14133_2", source_name="COMPRAS_GOV", objeto="Test 2", uf="RJ"
            ),
        ]

        with patch.object(adapter, "_fetch_legacy", new_callable=AsyncMock) as mock_legacy, \
             patch.object(adapter, "_fetch_lei_14133", new_callable=AsyncMock) as mock_lei:
            mock_legacy.return_value = legacy_records
            mock_lei.return_value = lei_records

            records = []
            async for record in adapter.fetch("2026-01-01", "2026-01-31"):
                records.append(record)

        assert len(records) == 2
        assert records[0].source_id == "cg_leg_1"
        assert records[1].source_id == "cg_14133_2"

    @pytest.mark.asyncio
    async def test_fetch_with_uf_filter(self, adapter):
        """Test fetch passes UF filter to both endpoints."""
        with patch.object(adapter, "_fetch_legacy", new_callable=AsyncMock) as mock_legacy, \
             patch.object(adapter, "_fetch_lei_14133", new_callable=AsyncMock) as mock_lei:
            mock_legacy.return_value = [
                UnifiedProcurement(
                    source_id="cg_leg_1", source_name="COMPRAS_GOV", uf="SP"
                ),
            ]
            mock_lei.return_value = [
                UnifiedProcurement(
                    source_id="cg_14133_2", source_name="COMPRAS_GOV", uf="SP"
                ),
            ]

            records = []
            async for record in adapter.fetch("2026-01-01", "2026-01-31", ufs={"SP"}):
                records.append(record)

        assert len(records) == 2
        assert all(r.uf == "SP" for r in records)

        # Verify UFs were passed to both sub-fetches
        mock_legacy.assert_called_once()
        mock_lei.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_pagination(self, adapter):
        """Test fetch with multiple pages from legacy endpoint."""
        page1_response = {
            "data": [{"numero_aviso": str(i), "uf": "SP"} for i in range(500)],
            "totalRegistros": 600,
            "totalPaginas": 2,
            "paginasRestantes": 1,
        }
        page2_response = {
            "data": [{"numero_aviso": str(i + 500), "uf": "SP"} for i in range(100)],
            "totalRegistros": 600,
            "totalPaginas": 2,
            "paginasRestantes": 0,
        }

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [page1_response, page2_response]
            results = await adapter._fetch_legacy("2026-01-01", "2026-01-31")

        assert len(results) == 600
        assert mock_request.call_count == 2


class TestMetadata:
    def test_metadata(self, adapter):
        """Test adapter metadata is correct for v3."""
        assert adapter.metadata.code == "COMPRAS_GOV"
        assert adapter.metadata.priority == 3  # Promoted from 4 in v3
        assert adapter.metadata.rate_limit_rps == 5.0  # Upgraded from 2.0 in v3

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


class TestComprasGovV3Normalization:
    """Test v3 normalization: legacy uses modalidade.descricao, Lei 14.133 uses modalidadeNome."""

    def test_normalize_legacy_modalidade_from_dict(self, adapter):
        """Legacy records extract modalidade from dict descricao field."""
        raw = {
            "numero_aviso": "PE-001",
            "modalidade": {"descricao": "Pregao Eletronico"},
        }
        result = adapter.normalize(raw)
        assert result.modalidade == "Pregao Eletronico"

    def test_normalize_legacy_modalidade_as_string(self, adapter):
        """Legacy records handle modalidade as string."""
        raw = {
            "numero_aviso": "PE-001",
            "modalidade": "Concorrencia",
        }
        result = adapter.normalize(raw)
        assert result.modalidade == "Concorrencia"

    def test_normalize_lei_14133_modalidade(self, adapter):
        """Lei 14.133 records use modalidadeNome directly."""
        raw = {
            "numeroControlePNCP": "PNCP-001",
            "modalidadeNome": "Pregao Eletronico",
        }
        result = adapter.normalize(raw)
        assert result.modalidade == "Pregao Eletronico"

    def test_normalize_legacy_situacao_from_dict(self, adapter):
        """Legacy records extract situacao from dict descricao field."""
        raw = {
            "numero_aviso": "PE-001",
            "situacao": {"descricao": "Publicada"},
        }
        result = adapter.normalize(raw)
        assert result.situacao == "Publicada"

    def test_normalize_lei_14133_situacao(self, adapter):
        """Lei 14.133 records use situacaoCompraNome directly."""
        raw = {
            "numeroControlePNCP": "PNCP-001",
            "situacaoCompraNome": "Em andamento",
        }
        result = adapter.normalize(raw)
        assert result.situacao == "Em andamento"

    def test_normalize_all_modalities_in_legacy_records(self, adapter):
        """Legacy normalize handles various modalidade names from API."""
        modalities = [
            "Pregao Eletronico",
            "Pregao Presencial",
            "Concorrencia",
            "Concurso",
            "Leilao",
            "Dispensa de Licitacao",
            "Inexigibilidade",
            "Dialogo Competitivo",
        ]

        for mod in modalities:
            raw = {
                "numero_aviso": "test-id",
                "modalidade": {"descricao": mod},
            }
            result = adapter.normalize(raw)
            assert result.modalidade == mod, f"Failed for {mod}: got {result.modalidade}"

    def test_normalize_empty_modalidade_legacy(self, adapter):
        """Legacy records with empty/missing modalidade get empty string."""
        raw = {"numero_aviso": "test-id"}
        result = adapter.normalize(raw)
        assert result.modalidade == ""

    def test_normalize_empty_modalidade_lei_14133(self, adapter):
        """Lei 14.133 records with empty/missing modalidadeNome get empty string."""
        raw = {"numeroControlePNCP": "test-id"}
        result = adapter.normalize(raw)
        assert result.modalidade == ""
