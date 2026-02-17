"""Comprehensive tests for PortalComprasAdapter v2 and calculate_total_value.

Tests cover:
- calculate_total_value function (AC29, kept for backward compat)
- Health check with various scenarios (v2 public API)
- Fetch with pagination, client-side UF filtering (v2)
- Normalize v2 field mapping
- Metadata validation
- Request retry logic

GTM-FIX-012b: Updated for v2 public API migration.
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from clients.base import (
    SourceAuthError,
    SourceCapability,
    SourceParseError,
    SourceStatus,
    SourceTimeoutError,
)
from clients.portal_compras_client import PortalComprasAdapter, calculate_total_value


# ============ Fixtures ============


@pytest.fixture
def adapter():
    """Adapter instance (v2 API needs no key)."""
    return PortalComprasAdapter(timeout=5)


@pytest.fixture
def adapter_with_key():
    """Adapter with legacy key (backward compat)."""
    return PortalComprasAdapter(api_key="test-key-123", timeout=5)


@pytest.fixture
def sample_v2_record():
    """Sample PCP v2 API record for normalize tests."""
    return {
        "codigoLicitacao": 12345,
        "numeroLicitacao": None,
        "identificacao": "PE001/2026",
        "numero": "001/2026",
        "resumo": "Fornecimento de uniformes profissionais para servidores",
        "razaoSocial": "Prefeitura Municipal de Campinas",
        "nomeUnidade": "Secretaria de Administração",
        "status": {"codigo": 9, "descricao": "Sessão Pública Iniciada"},
        "situacao": {"codigo": 0, "descricao": None},
        "tipoLicitacao": {
            "codigoModalidadeLicitacao": 0,
            "modalidadeLicitacao": "Pregão",
            "codigoTipoLicitacao": 1,
            "siglaTipoLicitacao": "PE",
            "tipoLicitacao": "Pregão Eletrônico",
            "tipoRealizacao": "Eletrônico",
            "tipoJulgamento": "Menor Preço",
        },
        "dataHoraInicioLances": "2026-02-16T13:01:00Z",
        "dataHoraInicioPropostas": "2026-02-10T10:00:00Z",
        "dataHoraFinalPropostas": "2026-02-28T18:00:00Z",
        "dataHoraFinalLances": None,
        "dataHoraPublicacao": "2026-01-15T10:30:00Z",
        "isPublicado": False,
        "unidadeCompradora": {
            "codigoUnidadeCompradora": 1234,
            "nomeUnidadeCompradora": "Secretaria de Administração",
            "codigoComprador": 567,
            "nomeComprador": None,
            "cidade": "Campinas",
            "codigoMunicipioIbge": None,
            "uf": "SP",
        },
        "comprador": None,
        "urlReferencia": "/sp/prefeitura-municipal-de-campinas-567/pe-001-2026-2026-12345",
        "statusProcessoPublico": {"codigo": 9, "descricao": "Sessão Pública Iniciada"},
        "isExclusivoME": False,
        "isBeneficoLocal": False,
    }


def _make_v2_record(codigo, resumo="Objeto test", uf="SP", **kwargs):
    """Helper to create a minimal v2 record."""
    record = {
        "codigoLicitacao": codigo,
        "resumo": resumo,
        "unidadeCompradora": {"uf": uf, "cidade": "Test City", "nomeUnidadeCompradora": "Test Org"},
        "statusProcessoPublico": {"codigo": 9, "descricao": "Aberto"},
        "tipoLicitacao": {"modalidadeLicitacao": "Pregão"},
        "dataHoraPublicacao": "2026-02-01T10:00:00Z",
        "dataHoraInicioPropostas": "2026-02-10T10:00:00Z",
        "dataHoraFinalPropostas": "2026-02-20T18:00:00Z",
        "numero": "001/2026",
        "urlReferencia": f"/sp/test-{codigo}",
    }
    record.update(kwargs)
    return record


def _make_v2_response(records, total=None, page_count=None, next_page=None):
    """Helper to create a v2 paginated response."""
    if total is None:
        total = len(records)
    if page_count is None:
        page_count = max(1, -(-total // 10))
    return {
        "result": records,
        "offset": 1,
        "limit": 10,
        "total": total,
        "pageCount": page_count,
        "currentPage": 1,
        "nextPage": next_page,
        "previousPage": None,
    }


# ============ TestCalculateTotalValue (kept for backward compat) ============


class TestCalculateTotalValue:
    """Test calculate_total_value function with edge cases."""

    def test_normal_case_multiple_lots(self):
        lotes = [
            {"itens": [
                {"VL_UNITARIO_ESTIMADO": 10.0, "QT_ITENS": 5},
                {"VL_UNITARIO_ESTIMADO": 20.0, "QT_ITENS": 3},
            ]},
            {"itens": [
                {"VL_UNITARIO_ESTIMADO": 15.0, "QT_ITENS": 2},
            ]},
        ]
        assert calculate_total_value(lotes) == 140.0

    def test_null_quantity_skips_item(self):
        lotes = [{"itens": [
            {"VL_UNITARIO_ESTIMADO": 10.0, "QT_ITENS": None},
            {"VL_UNITARIO_ESTIMADO": 20.0, "QT_ITENS": 5},
        ]}]
        assert calculate_total_value(lotes) == 100.0

    def test_null_value_skips_item(self):
        lotes = [{"itens": [
            {"VL_UNITARIO_ESTIMADO": None, "QT_ITENS": 10},
            {"VL_UNITARIO_ESTIMADO": 15.0, "QT_ITENS": 2},
        ]}]
        assert calculate_total_value(lotes) == 30.0

    def test_zero_quantity_skips_item(self):
        lotes = [{"itens": [
            {"VL_UNITARIO_ESTIMADO": 10.0, "QT_ITENS": 0},
            {"VL_UNITARIO_ESTIMADO": 20.0, "QT_ITENS": 5},
        ]}]
        assert calculate_total_value(lotes) == 100.0

    def test_negative_quantity_skips_item(self):
        lotes = [{"itens": [
            {"VL_UNITARIO_ESTIMADO": 10.0, "QT_ITENS": -5},
            {"VL_UNITARIO_ESTIMADO": 20.0, "QT_ITENS": 3},
        ]}]
        assert calculate_total_value(lotes) == 60.0

    def test_empty_lotes_returns_zero(self):
        assert calculate_total_value([]) == 0.0

    def test_non_numeric_values_skipped(self):
        lotes = [{"itens": [
            {"VL_UNITARIO_ESTIMADO": "abc", "QT_ITENS": 10},
            {"VL_UNITARIO_ESTIMADO": 20.0, "QT_ITENS": "xyz"},
            {"VL_UNITARIO_ESTIMADO": 15.0, "QT_ITENS": 2},
        ]}]
        assert calculate_total_value(lotes) == 30.0

    def test_rounding_to_2_decimals(self):
        lotes = [{"itens": [
            {"VL_UNITARIO_ESTIMADO": 10.123, "QT_ITENS": 3},
        ]}]
        assert calculate_total_value(lotes) == 30.37

    def test_missing_itens_key(self):
        lotes = [{"numeroLote": "1"}]
        assert calculate_total_value(lotes) == 0.0

    def test_none_itens_value(self):
        lotes = [{"itens": None}]
        assert calculate_total_value(lotes) == 0.0


# ============ TestHealthCheck (v2 — no auth) ============


class TestHealthCheck:
    """Test health_check with v2 public API."""

    @pytest.mark.asyncio
    async def test_health_check_available(self, adapter):
        """Test health_check with 200 → AVAILABLE."""
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
        """Test health_check with timeout → UNAVAILABLE."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_health_check_slow_response(self, adapter):
        """Test health_check with >3s response → DEGRADED."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch.object(asyncio, "get_running_loop") as mock_loop:
            mock_loop.return_value.time.side_effect = [0.0, 3.5]
            status = await adapter.health_check()

        assert status == SourceStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_health_check_server_error(self, adapter):
        """Test health_check with 500 → DEGRADED."""
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
    async def test_health_check_request_error(self, adapter):
        """Test health_check with RequestError → UNAVAILABLE."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.RequestError("Connection failed"))
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_health_check_uses_v2_endpoint(self, adapter):
        """Test health_check calls v2 endpoint with correct params."""
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
        assert call_args.args[0] == "/v2/licitacao/processos"
        assert call_args.kwargs["params"]["tipoData"] == 1
        assert call_args.kwargs["params"]["pagina"] == 1


# ============ TestFetch (v2) ============


class TestFetch:
    """Test fetch with v2 pagination and client-side UF filtering."""

    @pytest.mark.asyncio
    async def test_fetch_single_page(self, adapter):
        """Test fetch with single page of 3 records."""
        records_data = [
            _make_v2_record(1, "Objeto 1"),
            _make_v2_record(2, "Objeto 2"),
            _make_v2_record(3, "Objeto 3"),
        ]
        mock_response = _make_v2_response(records_data, total=3, page_count=1, next_page=None)

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            records = [r async for r in adapter.fetch("2026-01-01", "2026-01-31")]

        assert len(records) == 3
        assert records[0].source_id == "pcp_1"
        assert records[1].source_id == "pcp_2"
        assert records[2].source_id == "pcp_3"

    @pytest.mark.asyncio
    async def test_fetch_pagination_two_pages(self, adapter):
        """Test fetch with pagination (2 pages via nextPage)."""
        page1 = _make_v2_response(
            [_make_v2_record(1)], total=2, page_count=2, next_page=2
        )
        page2 = _make_v2_response(
            [_make_v2_record(2)], total=2, page_count=2, next_page=None
        )

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [page1, page2]
            records = [r async for r in adapter.fetch("2026-01-01", "2026-01-31")]

        assert len(records) == 2
        assert records[0].source_id == "pcp_1"
        assert records[1].source_id == "pcp_2"

    @pytest.mark.asyncio
    async def test_fetch_client_side_uf_filtering(self, adapter):
        """Test fetch filters by UF client-side (v2 has no server-side filter)."""
        records_data = [
            _make_v2_record(1, uf="SP"),
            _make_v2_record(2, uf="RJ"),
            _make_v2_record(3, uf="SP"),
            _make_v2_record(4, uf="MG"),
        ]
        mock_response = _make_v2_response(records_data, total=4, page_count=1, next_page=None)

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            records = [r async for r in adapter.fetch("2026-01-01", "2026-01-31", ufs={"SP"})]

        assert len(records) == 2
        assert all(r.uf == "SP" for r in records)

    @pytest.mark.asyncio
    async def test_fetch_auth_error_raises(self, adapter):
        """Test fetch with auth error raises SourceAuthError."""
        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = SourceAuthError("PORTAL_COMPRAS", "Auth failed")

            with pytest.raises(SourceAuthError):
                async for _ in adapter.fetch("2026-01-01", "2026-01-31"):
                    pass

    @pytest.mark.asyncio
    async def test_fetch_empty_response(self, adapter):
        """Test fetch with empty result returns 0 records."""
        mock_response = _make_v2_response([], total=0, page_count=0, next_page=None)

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            records = [r async for r in adapter.fetch("2026-01-01", "2026-01-31")]

        assert len(records) == 0

    @pytest.mark.asyncio
    async def test_fetch_deduplication(self, adapter):
        """Test fetch deduplicates records with same codigoLicitacao."""
        records_data = [
            _make_v2_record(1, "Objeto 1"),
            _make_v2_record(1, "Objeto 1 duplicado"),  # Duplicate
        ]
        mock_response = _make_v2_response(records_data, total=2, page_count=1, next_page=None)

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            records = [r async for r in adapter.fetch("2026-01-01", "2026-01-31")]

        assert len(records) == 1
        assert records[0].source_id == "pcp_1"

    @pytest.mark.asyncio
    async def test_fetch_normalize_error_skips_record(self, adapter):
        """Test fetch skips record if normalize fails."""
        records_data = [
            {"resumo": "No codigoLicitacao"},  # Missing ID → normalize fails
            _make_v2_record(2, "Valid record"),
        ]
        mock_response = _make_v2_response(records_data, total=2, page_count=1, next_page=None)

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            records = [r async for r in adapter.fetch("2026-01-01", "2026-01-31")]

        assert len(records) == 1
        assert records[0].source_id == "pcp_2"

    @pytest.mark.asyncio
    async def test_fetch_uses_iso_dates_directly(self, adapter):
        """Test fetch passes ISO dates to v2 API without conversion."""
        mock_response = _make_v2_response([], total=0, page_count=0, next_page=None)

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            async for _ in adapter.fetch("2026-02-01", "2026-02-17"):
                pass

        call_args = mock_request.call_args
        params = call_args.args[2]  # 3rd positional arg is params
        assert params["dataInicial"] == "2026-02-01"
        assert params["dataFinal"] == "2026-02-17"
        assert params["tipoData"] == 1

    @pytest.mark.asyncio
    async def test_fetch_no_ufs_returns_all(self, adapter):
        """Test fetch without UF filter returns all records."""
        records_data = [
            _make_v2_record(1, uf="SP"),
            _make_v2_record(2, uf="RJ"),
            _make_v2_record(3, uf="MG"),
        ]
        mock_response = _make_v2_response(records_data, total=3, page_count=1, next_page=None)

        with patch.object(adapter, "_request_with_retry", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            records = [r async for r in adapter.fetch("2026-01-01", "2026-01-31")]

        assert len(records) == 3


# ============ TestNormalize (v2 field mapping) ============


class TestNormalize:
    """Test normalize with v2 record structure."""

    def test_normalize_full_v2_record(self, adapter, sample_v2_record):
        """Test normalize with full v2 record maps all fields correctly."""
        record = adapter.normalize(sample_v2_record)

        assert record.source_id == "pcp_12345"
        assert record.source_name == "PORTAL_COMPRAS"
        assert "uniformes profissionais" in record.objeto
        assert record.valor_estimado == 0.0  # v2 has no value data
        assert record.orgao == "Secretaria de Administração"
        assert record.uf == "SP"
        assert record.municipio == "Campinas"
        assert record.numero_edital == "001/2026"
        assert record.ano == "2026"
        assert record.modalidade == "Pregão"
        assert record.situacao == "Sessão Pública Iniciada"
        assert "/sp/prefeitura-municipal-de-campinas-567/" in record.link_portal

    def test_normalize_source_id_prefix(self, adapter):
        """Test normalize prefixes source_id with 'pcp_'."""
        raw = _make_v2_record(99999)
        record = adapter.normalize(raw)
        assert record.source_id == "pcp_99999"

    def test_normalize_resumo_as_objeto(self, adapter):
        """Test normalize uses resumo field as objeto."""
        raw = _make_v2_record(1, resumo="Aquisição de equipamentos de TI")
        record = adapter.normalize(raw)
        assert record.objeto == "Aquisição de equipamentos de TI"

    def test_normalize_value_is_zero(self, adapter):
        """Test normalize sets valor_estimado=0.0 (v2 has no value data)."""
        raw = _make_v2_record(1)
        record = adapter.normalize(raw)
        assert record.valor_estimado == 0.0

    def test_normalize_missing_id_raises_error(self, adapter):
        """Test normalize raises SourceParseError when codigoLicitacao missing."""
        raw = {"resumo": "Objeto sem ID", "unidadeCompradora": {}}
        with pytest.raises(SourceParseError) as excinfo:
            adapter.normalize(raw)
        assert "codigoLicitacao" in str(excinfo.value)

    def test_normalize_portal_link_from_url_referencia(self, adapter):
        """Test normalize creates portal link from urlReferencia."""
        raw = _make_v2_record(789, urlReferencia="/mg/test-789")
        record = adapter.normalize(raw)
        assert record.link_portal == "https://www.portaldecompraspublicas.com.br/mg/test-789"

    def test_normalize_portal_link_fallback(self, adapter):
        """Test normalize creates fallback portal link when no urlReferencia."""
        raw = _make_v2_record(789)
        raw.pop("urlReferencia", None)
        record = adapter.normalize(raw)
        assert record.link_portal == "https://www.portaldecompraspublicas.com.br/processos/789"

    def test_normalize_uf_from_unidade_compradora(self, adapter):
        """Test normalize extracts UF from unidadeCompradora."""
        raw = _make_v2_record(1, uf="MG")
        record = adapter.normalize(raw)
        assert record.uf == "MG"

    def test_normalize_orgao_from_razao_social(self, adapter):
        """Test normalize uses razaoSocial when unidadeCompradora has no name."""
        raw = _make_v2_record(1)
        raw["unidadeCompradora"] = {"uf": "SP", "cidade": "Test"}
        raw["razaoSocial"] = "Prefeitura de Teste"
        record = adapter.normalize(raw)
        assert record.orgao == "Prefeitura de Teste"

    def test_normalize_ano_from_data_publicacao(self, adapter):
        """Test normalize extracts ano from dataHoraPublicacao."""
        raw = _make_v2_record(1)
        raw["dataHoraPublicacao"] = "2025-03-15T10:30:00Z"
        record = adapter.normalize(raw)
        assert record.ano == "2025"

    def test_normalize_modalidade_from_tipo_licitacao(self, adapter):
        """Test normalize extracts modalidade from tipoLicitacao object."""
        raw = _make_v2_record(1)
        raw["tipoLicitacao"] = {
            "modalidadeLicitacao": "Concorrência",
            "tipoLicitacao": "Concorrência por Menor Preço",
        }
        record = adapter.normalize(raw)
        assert record.modalidade == "Concorrência"

    def test_normalize_situacao_from_status_processo(self, adapter):
        """Test normalize extracts situacao from statusProcessoPublico."""
        raw = _make_v2_record(1)
        raw["statusProcessoPublico"] = {"codigo": 11, "descricao": "Cancelado"}
        record = adapter.normalize(raw)
        assert record.situacao == "Cancelado"

    def test_normalize_dates_iso_format(self, adapter):
        """Test normalize parses ISO dates from v2 API."""
        raw = _make_v2_record(1)
        raw["dataHoraPublicacao"] = "2026-02-10T14:30:00Z"
        raw["dataHoraInicioPropostas"] = "2026-02-15T10:00:00Z"
        raw["dataHoraFinalPropostas"] = "2026-02-28T18:00:00Z"
        record = adapter.normalize(raw)

        assert record.data_publicacao is not None
        assert record.data_publicacao.day == 10
        assert record.data_publicacao.month == 2

        assert record.data_abertura is not None
        assert record.data_abertura.day == 15

        assert record.data_encerramento is not None
        assert record.data_encerramento.day == 28

    def test_normalize_unidade_compradora_as_string(self, adapter):
        """Test normalize handles unidadeCompradora as string."""
        raw = _make_v2_record(1)
        raw["unidadeCompradora"] = "Some Agency"
        raw["razaoSocial"] = "Prefeitura X"
        record = adapter.normalize(raw)
        assert record.orgao == "Prefeitura X"


# ============ TestMetadata ============


class TestMetadata:
    """Test adapter metadata for v2 API."""

    def test_metadata_code(self, adapter):
        assert adapter.metadata.code == "PORTAL_COMPRAS"

    def test_metadata_priority(self, adapter):
        assert adapter.metadata.priority == 2

    def test_metadata_name(self, adapter):
        assert adapter.metadata.name == "Portal de Compras Publicas"

    def test_metadata_base_url(self, adapter):
        assert adapter.metadata.base_url == "https://compras.api.portaldecompraspublicas.com.br"

    def test_metadata_rate_limit(self, adapter):
        assert adapter.metadata.rate_limit_rps == 5.0

    def test_metadata_capabilities(self, adapter):
        assert SourceCapability.PAGINATION in adapter.metadata.capabilities
        assert SourceCapability.DATE_RANGE in adapter.metadata.capabilities
        # v2 API does NOT support server-side UF filtering
        assert SourceCapability.FILTER_BY_UF not in adapter.metadata.capabilities


# ============ TestRequestWithRetry ============


class TestRequestWithRetry:
    """Test _request_with_retry retry logic and error handling."""

    @pytest.mark.asyncio
    async def test_request_no_public_key_in_v2(self, adapter):
        """Test v2 API does NOT inject publicKey into params."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": []}
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        await adapter._request_with_retry("GET", "/test", params={"foo": "bar"})

        call_args = mock_client.request.call_args
        assert "publicKey" not in call_args.kwargs["params"]
        assert call_args.kwargs["params"]["foo"] == "bar"

    @pytest.mark.asyncio
    async def test_request_429_retries_with_retry_after(self, adapter):
        mock_client = AsyncMock()
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "2"}

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"success": True}

        mock_client.request = AsyncMock(side_effect=[mock_response_429, mock_response_200])
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await adapter._request_with_retry("GET", "/test")

        assert result == {"success": True}
        mock_sleep.assert_called_once_with(2)

    @pytest.mark.asyncio
    async def test_request_500_retries_with_backoff(self, adapter):
        mock_client = AsyncMock()
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500
        mock_response_500.text = "Internal Server Error"

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"success": True}

        mock_client.request = AsyncMock(side_effect=[mock_response_500, mock_response_200])
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await adapter._request_with_retry("GET", "/test")

        assert result == {"success": True}

    @pytest.mark.asyncio
    async def test_request_timeout_retries_then_raises(self, adapter):
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(SourceTimeoutError):
                await adapter._request_with_retry("GET", "/test")

        assert mock_client.request.call_count == adapter.MAX_RETRIES + 1

    @pytest.mark.asyncio
    async def test_request_204_returns_empty_list(self, adapter):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        result = await adapter._request_with_retry("GET", "/test")
        assert result == []


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

    @pytest.mark.asyncio
    async def test_async_context_manager(self, adapter):
        async with adapter as a:
            assert a is adapter

        if adapter._client:
            assert adapter._client.is_closed or adapter._client is None
