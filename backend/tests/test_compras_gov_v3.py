"""Comprehensive tests for ComprasGovAdapter v3 (GTM-FIX-027 T5).

Tests cover:
- v3 base URL configuration (AC25)
- Legacy endpoint fetching and normalization (AC26, AC29)
- Lei 14.133 endpoint fetching and normalization (AC27, AC29)
- Dual-endpoint parallel execution
- Health check validation (AC28)
- Error handling and retry logic
- Pagination
- UF filtering (server-side legacy, client-side 14.133)
- Feature flag enable/disable (AC31)
- Truncation detection
- Close / context manager
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from typing import Any, Dict, List

import httpx
import pytest

from clients.base import (
    SourceAPIError,
    SourceCapability,
    SourceParseError,
    SourceRateLimitError,
    SourceStatus,
    SourceTimeoutError,
    UnifiedProcurement,
)
from clients.compras_gov_client import ComprasGovAdapter


# ============ Fixtures ============


@pytest.fixture
def adapter():
    """Adapter instance with short timeout for tests."""
    return ComprasGovAdapter(timeout=5)


# ============ Helpers ============


def _make_legacy_record(
    numero_aviso: str = "PE-001",
    objeto: str = "Aquisicao de uniformes",
    uf: str = "SP",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Helper to create a minimal legacy endpoint record."""
    record: Dict[str, Any] = {
        "numero_aviso": numero_aviso,
        "objeto": objeto,
        "uf": uf,
        "uasg": {"nome": "Prefeitura Municipal", "cnpj": "12345678000100"},
        "municipio": "Sao Paulo",
        "modalidade": {"descricao": "Pregao Eletronico"},
        "situacao": {"descricao": "Publicada"},
        "data_publicacao": "2026-02-01T10:00:00Z",
        "data_entrega_proposta": "2026-02-15T18:00:00Z",
        "valor_estimado": 150000.0,
        "ano": "2026",
    }
    record.update(kwargs)
    return record


def _make_lei_14133_record(
    numero_controle: str = "PNCP-001-2026",
    objeto: str = "Contratacao de servicos de limpeza",
    uf: str = "RJ",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Helper to create a minimal Lei 14.133 endpoint record."""
    record: Dict[str, Any] = {
        "numeroControlePNCP": numero_controle,
        "objetoCompra": objeto,
        "uf": uf,
        "orgaoEntidade": {
            "razaoSocial": "Tribunal Regional Federal",
            "cnpj": "98765432000100",
            "municipio": "Rio de Janeiro",
        },
        "modalidadeNome": "Pregao Eletronico",
        "situacaoCompraNome": "Em andamento",
        "dataPublicacaoPncp": "2026-02-05T08:00:00Z",
        "dataEncerramentoProposta": "2026-02-20T18:00:00Z",
        "valorTotalEstimado": 250000.0,
        "anoCompra": "2026",
        "numeroCompra": "001/2026",
    }
    record.update(kwargs)
    return record


def _make_paginated_response(
    data: List[Dict[str, Any]],
    total_registros: int = 0,
    total_paginas: int = 1,
    paginas_restantes: int = 0,
) -> Dict[str, Any]:
    """Helper to create a v3 paginated response."""
    if total_registros == 0:
        total_registros = len(data)
    return {
        "data": data,
        "totalRegistros": total_registros,
        "totalPaginas": total_paginas,
        "paginasRestantes": paginas_restantes,
    }


# ============ TestV3BaseURL (AC25) ============


class TestV3BaseURL:
    """Test v3 base URL configuration."""

    def test_base_url_is_v3(self, adapter):
        """AC25: Base URL points to dadosabertos.compras.gov.br."""
        assert adapter.BASE_URL == "https://dadosabertos.compras.gov.br"

    def test_metadata_base_url_is_v3(self, adapter):
        """AC25: Metadata base_url matches v3."""
        assert adapter.metadata.base_url == "https://dadosabertos.compras.gov.br"

    def test_legacy_endpoint_path(self, adapter):
        """AC25: Legacy endpoint path is correct."""
        assert adapter.LEGACY_ENDPOINT == "/modulo-legado/1_consultarLicitacao"

    def test_lei_14133_endpoint_path(self, adapter):
        """AC25: Lei 14.133 endpoint path is correct."""
        assert adapter.LEI_14133_ENDPOINT == (
            "/modulo-contratacoes/1_consultarContratacoes_PNCP_14133"
        )


# ============ TestMetadata ============


class TestMetadata:
    """Test adapter metadata."""

    def test_metadata_code(self, adapter):
        assert adapter.metadata.code == "COMPRAS_GOV"

    def test_code_property(self, adapter):
        assert adapter.code == "COMPRAS_GOV"

    def test_name_property(self, adapter):
        assert "ComprasGov" in adapter.name

    def test_metadata_priority(self, adapter):
        """Priority should be 3 (PNCP=1, PCP=2, ComprasGov=3)."""
        assert adapter.metadata.priority == 3

    def test_metadata_rate_limit(self, adapter):
        assert adapter.metadata.rate_limit_rps == 5.0

    def test_metadata_capabilities(self, adapter):
        assert SourceCapability.PAGINATION in adapter.metadata.capabilities
        assert SourceCapability.DATE_RANGE in adapter.metadata.capabilities
        assert SourceCapability.FILTER_BY_UF in adapter.metadata.capabilities

    def test_rate_limit_delay(self, adapter):
        """200ms delay = 5 req/s."""
        assert adapter.RATE_LIMIT_DELAY == 0.2


# ============ TestHealthCheck (AC28) ============


class TestHealthCheck:
    """Test health_check against v3 legacy endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_available(self, adapter):
        """AC28: Health check 200 -> AVAILABLE."""
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
    async def test_health_check_slow_response(self, adapter):
        """AC28: Health check slow (>4s) -> DEGRADED."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch.object(asyncio, "get_running_loop") as mock_loop:
            mock_loop.return_value.time.side_effect = [0.0, 4.5]
            status = await adapter.health_check()

        assert status == SourceStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_health_check_server_error(self, adapter):
        """AC28: Health check 500 -> DEGRADED."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch.object(asyncio, "get_running_loop") as mock_loop:
            mock_loop.return_value.time.side_effect = [0.0, 1.0]
            status = await adapter.health_check()

        assert status == SourceStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_health_check_timeout(self, adapter):
        """AC28: Health check timeout -> UNAVAILABLE."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_health_check_request_error(self, adapter):
        """AC28: Health check connection error -> UNAVAILABLE."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.RequestError("Connection failed"))
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_health_check_uses_legacy_endpoint(self, adapter):
        """AC28: Health check probes the legacy endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch.object(asyncio, "get_running_loop") as mock_loop:
            mock_loop.return_value.time.side_effect = [0.0, 0.5]
            await adapter.health_check()

        call_args = mock_client.get.call_args
        assert call_args.args[0] == "/modulo-legado/1_consultarLicitacao"
        assert call_args.kwargs["params"]["pagina"] == 1
        assert call_args.kwargs["params"]["tamanhoPagina"] == 1


# ============ TestNormalizeLegacy (AC26, AC29) ============


class TestNormalizeLegacy:
    """Test legacy endpoint normalization."""

    def test_normalize_full_legacy_record(self, adapter):
        """AC26: Normalize complete legacy record."""
        raw = _make_legacy_record()
        record = adapter._normalize_legacy(raw)

        assert isinstance(record, UnifiedProcurement)
        assert record.source_id == "cg_leg_PE-001"
        assert record.source_name == "COMPRAS_GOV"
        assert record.objeto == "Aquisicao de uniformes"
        assert record.valor_estimado == 150000.0
        assert record.orgao == "Prefeitura Municipal"
        assert record.cnpj_orgao == "12345678000100"
        assert record.uf == "SP"
        assert record.municipio == "Sao Paulo"
        assert record.modalidade == "Pregao Eletronico"
        assert record.situacao == "Publicada"
        assert record.esfera == "F"
        assert record.numero_edital == "PE-001"
        assert record.ano == "2026"
        assert record.data_publicacao is not None
        assert record.data_abertura is not None

    def test_normalize_legacy_missing_optional_fields(self, adapter):
        """AC26: Normalize legacy record with missing optional fields."""
        raw = {"numero_aviso": "PE-002"}
        record = adapter._normalize_legacy(raw)

        assert record.source_id == "cg_leg_PE-002"
        assert record.objeto == ""
        assert record.valor_estimado == 0.0
        assert record.orgao == ""

    def test_normalize_legacy_no_id_raises(self, adapter):
        """AC26: Missing source_id raises SourceParseError."""
        raw = {"objeto": "Something"}
        with pytest.raises(SourceParseError):
            adapter._normalize_legacy(raw)

    def test_normalize_legacy_string_value(self, adapter):
        """AC29: Handle string value format in legacy records."""
        raw = _make_legacy_record(valor_estimado="250000")
        record = adapter._normalize_legacy(raw)
        assert record.valor_estimado == 250000.0

    def test_normalize_legacy_uasg_as_string(self, adapter):
        """AC26: Handle uasg as non-dict gracefully."""
        raw = _make_legacy_record()
        raw["uasg"] = "Some Agency"
        raw["orgao_nome"] = "Fallback Org"
        record = adapter._normalize_legacy(raw)
        assert record.orgao == "Fallback Org"

    def test_normalize_legacy_modalidade_as_string(self, adapter):
        """AC26: Handle modalidade as non-dict."""
        raw = _make_legacy_record()
        raw["modalidade"] = "Concorrencia"
        record = adapter._normalize_legacy(raw)
        assert record.modalidade == "Concorrencia"

    def test_normalize_legacy_situacao_as_string(self, adapter):
        """AC26: Handle situacao as non-dict."""
        raw = _make_legacy_record()
        raw["situacao"] = "Aberta"
        record = adapter._normalize_legacy(raw)
        assert record.situacao == "Aberta"

    def test_normalize_legacy_date_parsing(self, adapter):
        """AC29: Parse ISO dates from legacy endpoint."""
        raw = _make_legacy_record(
            data_publicacao="2026-02-10T14:30:00Z",
            data_entrega_proposta="2026-02-28T18:00:00Z",
        )
        record = adapter._normalize_legacy(raw)

        assert record.data_publicacao is not None
        assert record.data_publicacao.month == 2
        assert record.data_publicacao.day == 10

        assert record.data_abertura is not None
        assert record.data_abertura.day == 28

    def test_normalize_legacy_ano_from_date(self, adapter):
        """AC29: Extract year from data_publicacao when ano missing."""
        raw = _make_legacy_record()
        raw.pop("ano", None)
        raw["data_publicacao"] = "2025-06-15T10:00:00Z"
        record = adapter._normalize_legacy(raw)
        assert record.ano == "2025"

    def test_normalize_legacy_link_generation(self, adapter):
        """AC29: Generate link when not provided."""
        raw = _make_legacy_record(numero_aviso="PE-999")
        raw.pop("link", None)
        record = adapter._normalize_legacy(raw)
        assert "dadosabertos.compras.gov.br" in record.link_portal


# ============ TestNormalizeLei14133 (AC27, AC29) ============


class TestNormalizeLei14133:
    """Test Lei 14.133 endpoint normalization."""

    def test_normalize_full_lei_14133_record(self, adapter):
        """AC27: Normalize complete Lei 14.133 record."""
        raw = _make_lei_14133_record()
        record = adapter._normalize_lei_14133(raw)

        assert isinstance(record, UnifiedProcurement)
        assert record.source_id == "cg_14133_PNCP-001-2026"
        assert record.source_name == "COMPRAS_GOV"
        assert record.objeto == "Contratacao de servicos de limpeza"
        assert record.valor_estimado == 250000.0
        assert record.orgao == "Tribunal Regional Federal"
        assert record.cnpj_orgao == "98765432000100"
        assert record.uf == "RJ"
        assert record.municipio == "Rio de Janeiro"
        assert record.modalidade == "Pregao Eletronico"
        assert record.situacao == "Em andamento"
        assert record.esfera == "F"
        assert record.numero_edital == "001/2026"
        assert record.ano == "2026"
        assert record.data_publicacao is not None
        assert record.data_encerramento is not None

    def test_normalize_lei_14133_missing_optional_fields(self, adapter):
        """AC27: Normalize with missing optional fields."""
        raw = {"numeroControlePNCP": "CTRL-002"}
        record = adapter._normalize_lei_14133(raw)

        assert record.source_id == "cg_14133_CTRL-002"
        assert record.objeto == ""
        assert record.valor_estimado == 0.0

    def test_normalize_lei_14133_no_id_raises(self, adapter):
        """AC27: Missing source_id raises SourceParseError."""
        raw = {"objetoCompra": "Something"}
        with pytest.raises(SourceParseError):
            adapter._normalize_lei_14133(raw)

    def test_normalize_lei_14133_orgao_as_string(self, adapter):
        """AC27: Handle orgaoEntidade as non-dict."""
        raw = _make_lei_14133_record()
        raw["orgaoEntidade"] = "Some Entity"
        record = adapter._normalize_lei_14133(raw)
        assert record.orgao == "Some Entity"
        assert record.cnpj_orgao == ""

    def test_normalize_lei_14133_dates(self, adapter):
        """AC29: Parse Lei 14.133 dates."""
        raw = _make_lei_14133_record(
            dataPublicacaoPncp="2026-03-01T09:00:00Z",
            dataEncerramentoProposta="2026-03-15T18:00:00Z",
        )
        record = adapter._normalize_lei_14133(raw)

        assert record.data_publicacao is not None
        assert record.data_publicacao.month == 3
        assert record.data_publicacao.day == 1

        assert record.data_encerramento is not None
        assert record.data_encerramento.day == 15

    def test_normalize_lei_14133_link_generation(self, adapter):
        """AC29: Generate PNCP link from numeroControlePNCP."""
        raw = _make_lei_14133_record(numero_controle="12345-2026-PNCP")
        raw.pop("link", None)
        record = adapter._normalize_lei_14133(raw)
        assert "pncp.gov.br" in record.link_portal

    def test_normalize_lei_14133_string_value(self, adapter):
        """AC29: Handle string value in Lei 14.133 records."""
        raw = _make_lei_14133_record(valorTotalEstimado="500000.50")
        record = adapter._normalize_lei_14133(raw)
        assert record.valor_estimado == 500000.50

    def test_normalize_lei_14133_ano_from_date(self, adapter):
        """AC29: Extract ano from data_publicacao when anoCompra missing."""
        raw = _make_lei_14133_record()
        raw.pop("anoCompra", None)
        raw["dataPublicacaoPncp"] = "2025-11-20T10:00:00Z"
        record = adapter._normalize_lei_14133(raw)
        assert record.ano == "2025"


# ============ TestNormalizeAutoDetect ============


class TestNormalizeAutoDetect:
    """Test the normalize() auto-detection between legacy and Lei 14.133."""

    def test_auto_detect_lei_14133_by_numero_controle(self, adapter):
        """Detect Lei 14.133 record by presence of numeroControlePNCP."""
        raw = _make_lei_14133_record()
        record = adapter.normalize(raw)
        assert record.source_id.startswith("cg_14133_")

    def test_auto_detect_lei_14133_by_objeto_compra(self, adapter):
        """Detect Lei 14.133 record by presence of objetoCompra."""
        raw = {"objetoCompra": "Test", "id": "123"}
        record = adapter.normalize(raw)
        assert record.source_id.startswith("cg_14133_")

    def test_auto_detect_legacy(self, adapter):
        """Detect legacy record by absence of Lei 14.133 fields."""
        raw = _make_legacy_record()
        record = adapter.normalize(raw)
        assert record.source_id.startswith("cg_leg_")


# ============ TestFetchLegacy (AC26) ============


class TestFetchLegacy:
    """Test legacy endpoint fetch with pagination and UF filtering."""

    @pytest.mark.asyncio
    async def test_fetch_legacy_single_page(self, adapter):
        """AC26: Fetch single page from legacy endpoint."""
        records_data = [
            _make_legacy_record("PE-001"),
            _make_legacy_record("PE-002"),
        ]
        response = _make_paginated_response(records_data, total_registros=2, total_paginas=1, paginas_restantes=0)

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = response
            results = await adapter._fetch_legacy("2026-01-01", "2026-01-31")

        assert len(results) == 2
        assert results[0].source_id == "cg_leg_PE-001"
        assert results[1].source_id == "cg_leg_PE-002"

    @pytest.mark.asyncio
    async def test_fetch_legacy_server_side_uf_filtering(self, adapter):
        """AC26: Legacy endpoint uses server-side UF param."""
        response = _make_paginated_response(
            [_make_legacy_record("PE-001", uf="SP")],
            total_registros=1,
            paginas_restantes=0,
        )

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = response
            results = await adapter._fetch_legacy("2026-01-01", "2026-01-31", ufs={"SP"})

        # Verify UF param was passed
        call_args = mock_req.call_args
        params = call_args.args[2]  # 3rd positional arg
        assert params["uf"] == "SP"
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_fetch_legacy_multiple_ufs(self, adapter):
        """AC26: Fetch for multiple UFs makes separate requests per UF."""
        response_sp = _make_paginated_response(
            [_make_legacy_record("PE-SP", uf="SP")], paginas_restantes=0
        )
        response_rj = _make_paginated_response(
            [_make_legacy_record("PE-RJ", uf="RJ")], paginas_restantes=0
        )

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = [response_rj, response_sp]  # sorted: RJ, SP
            results = await adapter._fetch_legacy("2026-01-01", "2026-01-31", ufs={"SP", "RJ"})

        assert len(results) == 2
        assert mock_req.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_legacy_pagination(self, adapter):
        """AC26: Fetch multiple pages from legacy endpoint."""
        page1 = _make_paginated_response(
            [_make_legacy_record("PE-001")],
            total_registros=2,
            total_paginas=2,
            paginas_restantes=1,
        )
        page2 = _make_paginated_response(
            [_make_legacy_record("PE-002")],
            total_registros=2,
            total_paginas=2,
            paginas_restantes=0,
        )

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = [page1, page2]
            results = await adapter._fetch_legacy("2026-01-01", "2026-01-31")

        assert len(results) == 2
        assert mock_req.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_legacy_error_partial_results(self, adapter):
        """AC26: Return partial results if error occurs mid-pagination."""
        page1 = _make_paginated_response(
            [_make_legacy_record("PE-001")],
            total_registros=2,
            total_paginas=2,
            paginas_restantes=1,
        )

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = [
                page1,
                SourceAPIError("COMPRAS_GOV", 500, "Server error"),
            ]
            results = await adapter._fetch_legacy("2026-01-01", "2026-01-31")

        assert len(results) == 1
        assert results[0].source_id == "cg_leg_PE-001"

    @pytest.mark.asyncio
    async def test_fetch_legacy_error_no_results_raises(self, adapter):
        """AC26: Raise if error occurs on first page with no results."""
        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = SourceAPIError("COMPRAS_GOV", 500, "Server error")

            with pytest.raises(SourceAPIError):
                await adapter._fetch_legacy("2026-01-01", "2026-01-31")

    @pytest.mark.asyncio
    async def test_fetch_legacy_normalize_error_skips_record(self, adapter):
        """AC26: Skip record if normalization fails."""
        response = _make_paginated_response(
            [
                {"objeto": "No ID"},  # Will fail normalization
                _make_legacy_record("PE-002"),
            ],
            paginas_restantes=0,
        )

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = response
            results = await adapter._fetch_legacy("2026-01-01", "2026-01-31")

        assert len(results) == 1
        assert results[0].source_id == "cg_leg_PE-002"


# ============ TestFetchLei14133 (AC27) ============


class TestFetchLei14133:
    """Test Lei 14.133 endpoint fetch with pagination and client-side UF filtering."""

    @pytest.mark.asyncio
    async def test_fetch_lei_14133_single_page(self, adapter):
        """AC27: Fetch single page from Lei 14.133 endpoint."""
        records_data = [
            _make_lei_14133_record("PNCP-001"),
            _make_lei_14133_record("PNCP-002"),
        ]
        response = _make_paginated_response(records_data, total_registros=2, paginas_restantes=0)

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = response
            results = await adapter._fetch_lei_14133("2026-01-01", "2026-01-31")

        assert len(results) == 2
        assert results[0].source_id == "cg_14133_PNCP-001"

    @pytest.mark.asyncio
    async def test_fetch_lei_14133_client_side_uf_filtering(self, adapter):
        """AC27: Lei 14.133 uses client-side UF filtering."""
        records_data = [
            _make_lei_14133_record("PNCP-001", uf="SP"),
            _make_lei_14133_record("PNCP-002", uf="RJ"),
            _make_lei_14133_record("PNCP-003", uf="SP"),
        ]
        response = _make_paginated_response(records_data, paginas_restantes=0)

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = response
            results = await adapter._fetch_lei_14133("2026-01-01", "2026-01-31", ufs={"SP"})

        assert len(results) == 2
        assert all(r.uf == "SP" for r in results)

    @pytest.mark.asyncio
    async def test_fetch_lei_14133_no_uf_filter_returns_all(self, adapter):
        """AC27: Without UF filter, all records are returned."""
        records_data = [
            _make_lei_14133_record("PNCP-001", uf="SP"),
            _make_lei_14133_record("PNCP-002", uf="RJ"),
        ]
        response = _make_paginated_response(records_data, paginas_restantes=0)

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = response
            results = await adapter._fetch_lei_14133("2026-01-01", "2026-01-31")

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_fetch_lei_14133_pagination(self, adapter):
        """AC27: Fetch multiple pages from Lei 14.133 endpoint."""
        page1 = _make_paginated_response(
            [_make_lei_14133_record("PNCP-001")],
            total_registros=2,
            total_paginas=2,
            paginas_restantes=1,
        )
        page2 = _make_paginated_response(
            [_make_lei_14133_record("PNCP-002")],
            total_registros=2,
            total_paginas=2,
            paginas_restantes=0,
        )

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = [page1, page2]
            results = await adapter._fetch_lei_14133("2026-01-01", "2026-01-31")

        assert len(results) == 2


# ============ TestFetchDualEndpoint ============


class TestFetchDualEndpoint:
    """Test dual-endpoint parallel fetch."""

    @pytest.mark.asyncio
    async def test_fetch_merges_both_endpoints(self, adapter):
        """Fetch merges results from both legacy and Lei 14.133 endpoints."""
        legacy_records = [
            _make_legacy_record("PE-001"),
        ]
        lei_records = [
            _make_lei_14133_record("PNCP-001"),
        ]

        with patch.object(adapter, "_fetch_legacy", new_callable=AsyncMock) as mock_legacy, \
             patch.object(adapter, "_fetch_lei_14133", new_callable=AsyncMock) as mock_lei:
            mock_legacy.return_value = [adapter._normalize_legacy(r) for r in legacy_records]
            mock_lei.return_value = [adapter._normalize_lei_14133(r) for r in lei_records]

            records = [r async for r in adapter.fetch("2026-01-01", "2026-01-31")]

        assert len(records) == 2
        source_ids = {r.source_id for r in records}
        assert "cg_leg_PE-001" in source_ids
        assert "cg_14133_PNCP-001" in source_ids

    @pytest.mark.asyncio
    async def test_fetch_deduplicates_by_source_id(self, adapter):
        """Fetch deduplicates records with same source_id."""
        record = adapter._normalize_legacy(_make_legacy_record("PE-001"))

        with patch.object(adapter, "_fetch_legacy", new_callable=AsyncMock) as mock_legacy, \
             patch.object(adapter, "_fetch_lei_14133", new_callable=AsyncMock) as mock_lei:
            # Same record returned by both (edge case)
            mock_legacy.return_value = [record]
            mock_lei.return_value = [record]

            records = [r async for r in adapter.fetch("2026-01-01", "2026-01-31")]

        assert len(records) == 1

    @pytest.mark.asyncio
    async def test_fetch_legacy_fails_lei_succeeds(self, adapter):
        """If legacy endpoint fails, Lei 14.133 results are still returned."""
        lei_record = adapter._normalize_lei_14133(_make_lei_14133_record("PNCP-001"))

        with patch.object(adapter, "_fetch_legacy", new_callable=AsyncMock) as mock_legacy, \
             patch.object(adapter, "_fetch_lei_14133", new_callable=AsyncMock) as mock_lei:
            mock_legacy.side_effect = SourceAPIError("COMPRAS_GOV", 503, "Legacy down")
            mock_lei.return_value = [lei_record]

            records = [r async for r in adapter.fetch("2026-01-01", "2026-01-31")]

        assert len(records) == 1
        assert records[0].source_id == "cg_14133_PNCP-001"

    @pytest.mark.asyncio
    async def test_fetch_lei_fails_legacy_succeeds(self, adapter):
        """If Lei 14.133 endpoint fails, legacy results are still returned."""
        legacy_record = adapter._normalize_legacy(_make_legacy_record("PE-001"))

        with patch.object(adapter, "_fetch_legacy", new_callable=AsyncMock) as mock_legacy, \
             patch.object(adapter, "_fetch_lei_14133", new_callable=AsyncMock) as mock_lei:
            mock_legacy.return_value = [legacy_record]
            mock_lei.side_effect = SourceAPIError("COMPRAS_GOV", 503, "Lei 14133 down")

            records = [r async for r in adapter.fetch("2026-01-01", "2026-01-31")]

        assert len(records) == 1
        assert records[0].source_id == "cg_leg_PE-001"

    @pytest.mark.asyncio
    async def test_fetch_both_fail_raises(self, adapter):
        """If both endpoints fail, the first exception is re-raised."""
        with patch.object(adapter, "_fetch_legacy", new_callable=AsyncMock) as mock_legacy, \
             patch.object(adapter, "_fetch_lei_14133", new_callable=AsyncMock) as mock_lei:
            mock_legacy.side_effect = SourceAPIError("COMPRAS_GOV", 503, "Legacy down")
            mock_lei.side_effect = SourceAPIError("COMPRAS_GOV", 503, "Lei 14133 down")

            with pytest.raises(SourceAPIError):
                async for _ in adapter.fetch("2026-01-01", "2026-01-31"):
                    pass

    @pytest.mark.asyncio
    async def test_fetch_empty_results(self, adapter):
        """Fetch with empty results from both endpoints."""
        with patch.object(adapter, "_fetch_legacy", new_callable=AsyncMock) as mock_legacy, \
             patch.object(adapter, "_fetch_lei_14133", new_callable=AsyncMock) as mock_lei:
            mock_legacy.return_value = []
            mock_lei.return_value = []

            records = [r async for r in adapter.fetch("2026-01-01", "2026-01-31")]

        assert len(records) == 0


# ============ TestRequestRetry ============


class TestRequestRetry:
    """Test _request_with_retry retry logic and error handling."""

    @pytest.mark.asyncio
    async def test_request_success_on_first_attempt(self, adapter):
        """Successful request on first attempt."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        result = await adapter._request_with_retry("GET", "/test")
        assert result == {"data": []}

    @pytest.mark.asyncio
    async def test_request_429_retries(self, adapter):
        """429 rate limit retries with Retry-After."""
        mock_client = AsyncMock()
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "2"}

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"data": []}

        mock_client.request = AsyncMock(side_effect=[mock_response_429, mock_response_200])
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await adapter._request_with_retry("GET", "/test")

        assert result == {"data": []}
        mock_sleep.assert_any_call(2)

    @pytest.mark.asyncio
    async def test_request_429_exhausted_retries_raises(self, adapter):
        """429 after all retries raises SourceRateLimitError."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}

        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(SourceRateLimitError):
                await adapter._request_with_retry("GET", "/test")

    @pytest.mark.asyncio
    async def test_request_500_retries_with_backoff(self, adapter):
        """500 error retries with exponential backoff."""
        mock_client = AsyncMock()
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500
        mock_response_500.text = "Internal Server Error"

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"data": []}

        mock_client.request = AsyncMock(side_effect=[mock_response_500, mock_response_200])
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await adapter._request_with_retry("GET", "/test")

        assert result == {"data": []}

    @pytest.mark.asyncio
    async def test_request_timeout_retries_then_raises(self, adapter):
        """Timeout after all retries raises SourceTimeoutError."""
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(SourceTimeoutError):
                await adapter._request_with_retry("GET", "/test")

        assert mock_client.request.call_count == adapter.MAX_RETRIES + 1

    @pytest.mark.asyncio
    async def test_request_connection_error_retries(self, adapter):
        """Connection error retries then raises SourceAPIError."""
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(side_effect=httpx.RequestError("Connection refused"))
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(SourceAPIError):
                await adapter._request_with_retry("GET", "/test")

        assert mock_client.request.call_count == adapter.MAX_RETRIES + 1

    @pytest.mark.asyncio
    async def test_request_204_returns_empty(self, adapter):
        """204 No Content returns empty response structure."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        result = await adapter._request_with_retry("GET", "/test")
        assert result["data"] == []
        assert result["totalRegistros"] == 0

    @pytest.mark.asyncio
    async def test_request_4xx_raises_immediately(self, adapter):
        """4xx (non-429) errors raise immediately without retry."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        with pytest.raises(SourceAPIError) as excinfo:
            await adapter._request_with_retry("GET", "/test")

        assert excinfo.value.status_code == 404
        assert mock_client.request.call_count == 1  # No retry


# ============ TestTruncationDetection ============


class TestTruncationDetection:
    """Test truncation detection when max_pages is reached."""

    @pytest.mark.asyncio
    async def test_truncation_detected_on_max_pages_legacy(self, adapter):
        """Legacy endpoint sets was_truncated when max_pages reached."""
        # Create a response that indicates more pages remain
        response = _make_paginated_response(
            [_make_legacy_record("PE-001")],
            total_registros=1000,
            total_paginas=10,
            paginas_restantes=9,
        )

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = response
            # Set max_pages=1 to trigger truncation
            results = await adapter._fetch_legacy_paginated(
                "2026-01-01", "2026-01-31", max_pages=1
            )

        assert adapter.was_truncated is True
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_no_truncation_when_all_pages_fetched(self, adapter):
        """No truncation when all pages are fetched."""
        response = _make_paginated_response(
            [_make_legacy_record("PE-001")],
            total_registros=1,
            total_paginas=1,
            paginas_restantes=0,
        )

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = response
            await adapter._fetch_legacy_paginated("2026-01-01", "2026-01-31")

        assert adapter.was_truncated is False


# ============ TestDatetimeParsing ============


class TestDatetimeParsing:
    """Test _parse_datetime with various formats."""

    def test_parse_iso_with_z(self, adapter):
        result = adapter._parse_datetime("2026-02-10T14:30:00Z")
        assert result is not None
        assert result.year == 2026
        assert result.month == 2
        assert result.day == 10

    def test_parse_iso_with_milliseconds(self, adapter):
        result = adapter._parse_datetime("2026-02-10T14:30:00.123Z")
        assert result is not None
        assert result.day == 10

    def test_parse_date_only(self, adapter):
        result = adapter._parse_datetime("2026-02-10")
        assert result is not None
        assert result.day == 10

    def test_parse_iso_with_timezone_offset(self, adapter):
        result = adapter._parse_datetime("2026-02-10T14:30:00+00:00")
        assert result is not None

    def test_parse_br_date_format(self, adapter):
        result = adapter._parse_datetime("10/02/2026")
        assert result is not None
        assert result.day == 10

    def test_parse_none_returns_none(self, adapter):
        assert adapter._parse_datetime(None) is None

    def test_parse_empty_string_returns_none(self, adapter):
        assert adapter._parse_datetime("") is None

    def test_parse_datetime_object_returns_same(self, adapter):
        dt = datetime(2026, 2, 10, 14, 30)
        result = adapter._parse_datetime(dt)
        # _parse_datetime may add timezone info to naive datetimes
        assert result.year == dt.year and result.month == dt.month and result.day == dt.day
        assert result.hour == dt.hour and result.minute == dt.minute

    def test_parse_timestamp_ms(self, adapter):
        # 2026-02-10 in milliseconds
        ts = datetime(2026, 2, 10).timestamp() * 1000
        result = adapter._parse_datetime(ts)
        assert result is not None
        assert result.day == 10

    def test_parse_invalid_returns_none(self, adapter):
        assert adapter._parse_datetime("not-a-date") is None


# ============ TestFeatureFlag (AC31) ============


class TestFeatureFlag:
    """Test feature flag integration with source config."""

    def test_source_config_default_disabled(self):
        """AC31: ComprasGov defaults to disabled via ENABLE_SOURCE_COMPRAS_GOV=false."""
        from source_config.sources import SourceConfig

        with patch.dict("os.environ", {"ENABLE_SOURCE_COMPRAS_GOV": "false"}, clear=False):
            config = SourceConfig.from_env()
            assert config.compras_gov.enabled is False

    def test_source_config_enabled_via_env(self):
        """AC31: ComprasGov can be enabled via ENABLE_SOURCE_COMPRAS_GOV=true."""
        from source_config.sources import SourceConfig

        with patch.dict("os.environ", {"ENABLE_SOURCE_COMPRAS_GOV": "true"}, clear=False):
            config = SourceConfig.from_env()
            assert config.compras_gov.enabled is True

    def test_source_config_v3_base_url(self):
        """AC25: Source config uses v3 base URL."""
        from source_config.sources import SourceConfig

        config = SourceConfig()
        assert config.compras_gov.base_url == "https://dadosabertos.compras.gov.br"

    def test_source_config_priority(self):
        """AC25: Source config priority is 3."""
        from source_config.sources import SourceConfig

        config = SourceConfig()
        assert config.compras_gov.priority == 3

    def test_source_config_no_auth_required(self):
        """AC31: ComprasGov is available without API key."""
        from source_config.sources import SourceConfig

        config = SourceConfig()
        config.compras_gov.enabled = True
        assert config.compras_gov.is_available() is True


# ============ TestClose ============


class TestClose:
    """Test async context manager and close behavior."""

    @pytest.mark.asyncio
    async def test_close_closes_client(self, adapter):
        mock_client = AsyncMock()
        mock_client.is_closed = False
        mock_client.aclose = AsyncMock()
        adapter._client = mock_client

        await adapter.close()
        mock_client.aclose.assert_called_once()
        assert adapter._client is None

    @pytest.mark.asyncio
    async def test_close_without_client(self, adapter):
        """Close with no client does not raise."""
        await adapter.close()

    @pytest.mark.asyncio
    async def test_close_already_closed_client(self, adapter):
        """Close with already-closed client does not raise."""
        mock_client = AsyncMock()
        mock_client.is_closed = True
        adapter._client = mock_client

        await adapter.close()

    @pytest.mark.asyncio
    async def test_async_context_manager(self, adapter):
        async with adapter as a:
            assert a is adapter


# ============ TestBackoff ============


class TestBackoff:
    """Test exponential backoff calculation."""

    def test_backoff_attempt_0(self, adapter):
        """First attempt backoff should be ~2s (with jitter)."""
        delay = adapter._calculate_backoff(0)
        assert 1.0 <= delay <= 3.0

    def test_backoff_attempt_1(self, adapter):
        """Second attempt backoff should be ~4s (with jitter)."""
        delay = adapter._calculate_backoff(1)
        assert 2.0 <= delay <= 6.0

    def test_backoff_capped_at_60(self, adapter):
        """Backoff capped at 60s (with jitter)."""
        delay = adapter._calculate_backoff(10)
        assert delay <= 90.0  # 60 * 1.5 jitter
