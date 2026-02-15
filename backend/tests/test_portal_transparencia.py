"""Tests for PortalTransparenciaAdapter (STORY-254 AC14).

Comprehensive test suite covering metadata, date helpers, date chunking,
normalization, health checks, fetch orchestration, retry logic, rate
limiting, and resource lifecycle.
"""

import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from clients.base import (
    SourceAPIError,
    SourceAuthError,
    SourceCapability,
    SourceParseError,
    SourceRateLimitError,
    SourceStatus,
    SourceTimeoutError,
    UnifiedProcurement,
)
from clients.portal_transparencia_client import PortalTransparenciaAdapter


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #


@pytest.fixture
def adapter():
    """Adapter with a test API key."""
    return PortalTransparenciaAdapter(api_key="test-api-key-123", timeout=5)


@pytest.fixture
def adapter_no_key():
    """Adapter without an API key."""
    return PortalTransparenciaAdapter(api_key="", timeout=5)


@pytest.fixture
def sample_raw_record():
    """A complete raw API record for normalization tests."""
    return {
        "id": "12345",
        "objeto": "Aquisicao de uniformes escolares",
        "valorLicitacao": 150000.00,
        "orgaoVinculado": {
            "nome": "Ministerio da Educacao",
            "cnpj": "00394445000117",
        },
        "municipio": {
            "nomeIBGE": "Brasilia",
            "uf": {"sigla": "DF"},
        },
        "dataPublicacao": "15/01/2026",
        "dataAbertura": "25/01/2026",
        "numero": "001/2026",
        "ano": "2026",
        "modalidadeLicitacao": {"descricao": "Pregao Eletronico"},
        "situacaoLicitacao": {"descricao": "Publicada"},
    }


@pytest.fixture
def small_org_list():
    """A small list of orgs for mocking _load_orgs."""
    return [
        ("26000", "Ministerio da Educacao"),
        ("36000", "Ministerio da Saude"),
    ]


# ------------------------------------------------------------------ #
# TestMetadata
# ------------------------------------------------------------------ #


class TestMetadata:
    """Tests for source metadata property."""

    def test_metadata_code(self, adapter):
        assert adapter.metadata.code == "PORTAL_TRANSPARENCIA"

    def test_metadata_name(self, adapter):
        assert adapter.metadata.name == "Portal da Transparencia - CGU"

    def test_metadata_priority(self, adapter):
        assert adapter.metadata.priority == 3

    def test_metadata_base_url(self, adapter):
        assert "portaldatransparencia" in adapter.metadata.base_url

    def test_metadata_capabilities(self, adapter):
        caps = adapter.metadata.capabilities
        assert SourceCapability.PAGINATION in caps
        assert SourceCapability.DATE_RANGE in caps

    def test_metadata_rate_limit(self, adapter):
        assert adapter.metadata.rate_limit_rps == 1.5

    def test_code_shortcut(self, adapter):
        """SourceAdapter.code property delegates to metadata.code."""
        assert adapter.code == "PORTAL_TRANSPARENCIA"

    def test_name_shortcut(self, adapter):
        """SourceAdapter.name property delegates to metadata.name."""
        assert adapter.name == "Portal da Transparencia - CGU"


# ------------------------------------------------------------------ #
# TestDateHelpers
# ------------------------------------------------------------------ #


class TestDateHelpers:
    """Tests for _to_api_date and _from_api_date static methods."""

    # _to_api_date

    def test_to_api_date_standard(self):
        assert PortalTransparenciaAdapter._to_api_date("2026-01-15") == "15/01/2026"

    def test_to_api_date_first_of_month(self):
        assert PortalTransparenciaAdapter._to_api_date("2026-03-01") == "01/03/2026"

    def test_to_api_date_last_of_year(self):
        assert PortalTransparenciaAdapter._to_api_date("2026-12-31") == "31/12/2026"

    def test_to_api_date_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            PortalTransparenciaAdapter._to_api_date("15/01/2026")

    def test_to_api_date_incomplete_raises(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            PortalTransparenciaAdapter._to_api_date("2026-01")

    # _from_api_date

    def test_from_api_date_dd_mm_yyyy(self):
        result = PortalTransparenciaAdapter._from_api_date("15/01/2026")
        assert result == datetime(2026, 1, 15)

    def test_from_api_date_dd_mm_yyyy_hms(self):
        result = PortalTransparenciaAdapter._from_api_date("15/01/2026 10:30:00")
        assert result == datetime(2026, 1, 15, 10, 30, 0)

    def test_from_api_date_iso_format(self):
        result = PortalTransparenciaAdapter._from_api_date("2026-01-15")
        assert result == datetime(2026, 1, 15)

    def test_from_api_date_iso_with_time(self):
        result = PortalTransparenciaAdapter._from_api_date("2026-01-15T10:30:00")
        assert result == datetime(2026, 1, 15, 10, 30, 0)

    def test_from_api_date_iso_with_z(self):
        result = PortalTransparenciaAdapter._from_api_date("2026-01-15T10:30:00Z")
        assert result == datetime(2026, 1, 15, 10, 30, 0)

    def test_from_api_date_iso_with_millis(self):
        result = PortalTransparenciaAdapter._from_api_date("2026-01-15T10:30:00.123Z")
        assert result is not None
        assert result.year == 2026

    def test_from_api_date_none_returns_none(self):
        assert PortalTransparenciaAdapter._from_api_date(None) is None

    def test_from_api_date_empty_string_returns_none(self):
        assert PortalTransparenciaAdapter._from_api_date("") is None

    def test_from_api_date_invalid_returns_none(self):
        assert PortalTransparenciaAdapter._from_api_date("not-a-date") is None

    def test_from_api_date_non_string_returns_none(self):
        assert PortalTransparenciaAdapter._from_api_date(12345) is None

    def test_from_api_date_whitespace_stripped(self):
        result = PortalTransparenciaAdapter._from_api_date("  15/01/2026  ")
        assert result == datetime(2026, 1, 15)


# ------------------------------------------------------------------ #
# TestDateChunking
# ------------------------------------------------------------------ #


class TestDateChunking:
    """Tests for _chunk_date_range static method."""

    def test_same_day(self):
        chunks = PortalTransparenciaAdapter._chunk_date_range("2026-01-15", "2026-01-15")
        assert chunks == [("2026-01-15", "2026-01-15")]

    def test_same_month(self):
        chunks = PortalTransparenciaAdapter._chunk_date_range("2026-01-05", "2026-01-25")
        assert len(chunks) == 1
        assert chunks[0] == ("2026-01-05", "2026-01-25")

    def test_two_months(self):
        chunks = PortalTransparenciaAdapter._chunk_date_range("2026-01-15", "2026-02-10")
        assert len(chunks) == 2
        assert chunks[0] == ("2026-01-15", "2026-01-31")
        assert chunks[1] == ("2026-02-01", "2026-02-10")

    def test_three_months(self):
        chunks = PortalTransparenciaAdapter._chunk_date_range("2026-01-15", "2026-03-10")
        assert len(chunks) == 3
        assert chunks[0][0] == "2026-01-15"
        assert chunks[1][0] == "2026-02-01"
        assert chunks[2][0] == "2026-03-01"
        assert chunks[2][1] == "2026-03-10"

    def test_start_after_end_returns_empty(self):
        chunks = PortalTransparenciaAdapter._chunk_date_range("2026-03-01", "2026-01-01")
        assert chunks == []

    def test_full_month(self):
        chunks = PortalTransparenciaAdapter._chunk_date_range("2026-01-01", "2026-01-31")
        assert len(chunks) == 1
        assert chunks[0] == ("2026-01-01", "2026-01-31")

    def test_cross_year_boundary(self):
        chunks = PortalTransparenciaAdapter._chunk_date_range("2025-12-15", "2026-01-10")
        assert len(chunks) == 2
        assert chunks[0] == ("2025-12-15", "2025-12-31")
        assert chunks[1] == ("2026-01-01", "2026-01-10")

    def test_february_non_leap(self):
        chunks = PortalTransparenciaAdapter._chunk_date_range("2026-02-01", "2026-02-28")
        assert len(chunks) == 1
        assert chunks[0] == ("2026-02-01", "2026-02-28")


# ------------------------------------------------------------------ #
# TestNormalize
# ------------------------------------------------------------------ #


class TestNormalize:
    """Tests for the normalize() method."""

    def test_complete_record(self, adapter, sample_raw_record):
        record = adapter.normalize(sample_raw_record)

        assert isinstance(record, UnifiedProcurement)
        assert record.source_id == "12345"
        assert record.source_name == "PORTAL_TRANSPARENCIA"
        assert record.objeto == "Aquisicao de uniformes escolares"
        assert record.valor_estimado == 150000.0
        assert record.orgao == "Ministerio da Educacao"
        assert record.cnpj_orgao == "00394445000117"
        assert record.uf == "DF"
        assert record.municipio == "Brasilia"
        assert record.esfera == "F"
        assert record.modalidade == "Pregao Eletronico"
        assert record.situacao == "Publicada"
        assert record.numero_edital == "001/2026"
        assert record.ano == "2026"

    def test_dates_parsed(self, adapter, sample_raw_record):
        record = adapter.normalize(sample_raw_record)
        assert record.data_publicacao == datetime(2026, 1, 15)
        assert record.data_abertura == datetime(2026, 1, 25)

    def test_missing_id_raises_parse_error(self, adapter):
        raw = {"objeto": "Something without an id"}
        with pytest.raises(SourceParseError):
            adapter.normalize(raw)

    def test_alternative_id_fields(self, adapter):
        """codigoLicitacao and codigo are fallback id fields."""
        raw1 = {"codigoLicitacao": "ALT-001", "objeto": "Test"}
        assert adapter.normalize(raw1).source_id == "ALT-001"

        raw2 = {"codigo": "ALT-002", "objeto": "Test"}
        assert adapter.normalize(raw2).source_id == "ALT-002"

    def test_alternative_objeto_fields(self, adapter):
        raw1 = {"id": "1", "descricao": "Description text"}
        assert adapter.normalize(raw1).objeto == "Description text"

        raw2 = {"id": "2", "informacaoGeral": "General info"}
        assert adapter.normalize(raw2).objeto == "General info"

    def test_missing_objeto_defaults_empty(self, adapter):
        raw = {"id": "1"}
        assert adapter.normalize(raw).objeto == ""

    def test_valor_from_string_with_comma(self, adapter):
        """Handle Brazilian numeric format: 1.500,00 -> 1500.0."""
        raw = {"id": "1", "valorLicitacao": "1.500,00"}
        record = adapter.normalize(raw)
        assert record.valor_estimado == 1500.0

    def test_valor_from_string_large(self, adapter):
        """Handle large values: 1.500.000,50 -> 1500000.5."""
        raw = {"id": "1", "valorLicitacao": "1.500.000,50"}
        record = adapter.normalize(raw)
        assert record.valor_estimado == 1500000.5

    def test_valor_fallback_fields(self, adapter):
        raw1 = {"id": "1", "valor": 200000.0}
        assert adapter.normalize(raw1).valor_estimado == 200000.0

        raw2 = {"id": "2", "valorEstimado": 300000.0}
        assert adapter.normalize(raw2).valor_estimado == 300000.0

    def test_valor_missing_defaults_zero(self, adapter):
        raw = {"id": "1"}
        assert adapter.normalize(raw).valor_estimado == 0.0

    def test_valor_invalid_string(self, adapter):
        raw = {"id": "1", "valorLicitacao": "N/A"}
        record = adapter.normalize(raw)
        assert record.valor_estimado == 0.0

    def test_orgao_as_string(self, adapter):
        raw = {"id": "1", "orgaoVinculado": "Orgao Direto"}
        record = adapter.normalize(raw)
        assert record.orgao == "Orgao Direto"
        assert record.cnpj_orgao == ""

    def test_orgao_fallback_to_orgao_field(self, adapter):
        raw = {"id": "1", "orgao": {"nome": "Fallback Orgao", "cnpj": "111"}}
        record = adapter.normalize(raw)
        assert record.orgao == "Fallback Orgao"
        assert record.cnpj_orgao == "111"

    def test_orgao_top_level_fallback(self, adapter):
        raw = {"id": "1", "nomeOrgao": "Top-Level Orgao"}
        record = adapter.normalize(raw)
        assert record.orgao == "Top-Level Orgao"

    def test_orgao_not_a_dict_or_string(self, adapter):
        """If orgaoVinculado is an unexpected type, defaults to empty."""
        raw = {"id": "1", "orgaoVinculado": 12345}
        record = adapter.normalize(raw)
        assert record.orgao == ""

    def test_municipio_as_string(self, adapter):
        raw = {"id": "1", "municipio": "Curitiba"}
        record = adapter.normalize(raw)
        assert record.municipio == "Curitiba"

    def test_uf_from_nested_dict(self, adapter, sample_raw_record):
        record = adapter.normalize(sample_raw_record)
        assert record.uf == "DF"

    def test_uf_from_flat_field(self, adapter):
        raw = {"id": "1", "uf": "SP"}
        record = adapter.normalize(raw)
        assert record.uf == "SP"

    def test_uf_from_sigla_uf(self, adapter):
        raw = {"id": "1", "siglaUf": "RJ"}
        record = adapter.normalize(raw)
        assert record.uf == "RJ"

    def test_uf_normalized_uppercase(self, adapter):
        raw = {"id": "1", "uf": "sp"}
        record = adapter.normalize(raw)
        assert record.uf == "SP"

    def test_modalidade_as_string(self, adapter):
        raw = {"id": "1", "modalidadeLicitacao": "Concorrencia"}
        record = adapter.normalize(raw)
        assert record.modalidade == "Concorrencia"

    def test_modalidade_missing(self, adapter):
        raw = {"id": "1"}
        record = adapter.normalize(raw)
        assert record.modalidade == ""

    def test_situacao_as_string(self, adapter):
        raw = {"id": "1", "situacaoLicitacao": "Encerrada"}
        record = adapter.normalize(raw)
        assert record.situacao == "Encerrada"

    def test_situacao_from_situacao_field(self, adapter):
        raw = {"id": "1", "situacao": {"descricao": "Em andamento"}}
        record = adapter.normalize(raw)
        assert record.situacao == "Em andamento"

    def test_link_portal_generated_when_missing(self, adapter):
        raw = {"id": "12345"}
        record = adapter.normalize(raw)
        assert "12345" in record.link_portal
        assert "portaldatransparencia.gov.br" in record.link_portal

    def test_link_portal_from_record(self, adapter):
        raw = {"id": "1", "linkPortal": "https://example.com/licitacao/1"}
        record = adapter.normalize(raw)
        assert record.link_portal == "https://example.com/licitacao/1"

    def test_link_edital_fallback_to_link_portal(self, adapter):
        raw = {"id": "1", "linkPortal": "https://example.com/1"}
        record = adapter.normalize(raw)
        assert record.link_edital == "https://example.com/1"

    def test_raw_data_preserved(self, adapter, sample_raw_record):
        record = adapter.normalize(sample_raw_record)
        assert record.raw_data == sample_raw_record

    def test_fetched_at_set(self, adapter, sample_raw_record):
        record = adapter.normalize(sample_raw_record)
        assert record.fetched_at is not None

    def test_ano_from_data_publicacao_when_missing(self, adapter):
        """If ano is missing, infer from data_publicacao."""
        raw = {"id": "1", "dataPublicacao": "20/03/2025"}
        record = adapter.normalize(raw)
        assert record.ano == "2025"

    def test_empty_record_minimal(self, adapter):
        """An id-only record does not crash."""
        raw = {"id": "minimal"}
        record = adapter.normalize(raw)
        assert record.source_id == "minimal"
        assert record.objeto == ""
        assert record.valor_estimado == 0.0
        assert record.orgao == ""
        assert record.uf == ""
        assert record.esfera == "F"


# ------------------------------------------------------------------ #
# TestHealthCheck
# ------------------------------------------------------------------ #


class TestHealthCheck:
    """Tests for the health_check() method."""

    @pytest.mark.asyncio
    async def test_no_api_key_returns_unavailable(self, adapter_no_key):
        status = await adapter_no_key.health_check()
        assert status == SourceStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_success_returns_available(self, adapter):
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        # Patch event loop time for fast elapsed calculation
        loop = asyncio.get_event_loop()
        with patch.object(loop, "time", side_effect=[100.0, 100.5]):
            status = await adapter.health_check()
        assert status == SourceStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_slow_response_returns_degraded(self, adapter):
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        # Simulate slow response (> 4000ms)
        loop = asyncio.get_event_loop()
        with patch.object(loop, "time", side_effect=[100.0, 104.5]):
            status = await adapter.health_check()
        assert status == SourceStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_auth_failure_returns_unavailable(self, adapter):
        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_403_returns_unavailable(self, adapter):
        mock_response = MagicMock()
        mock_response.status_code = 403

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_500_returns_degraded(self, adapter):
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_timeout_returns_unavailable(self, adapter):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_request_error_returns_unavailable(self, adapter):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.ConnectError("connection refused")
        )
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_unexpected_exception_returns_unavailable(self, adapter):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=RuntimeError("unexpected"))
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.UNAVAILABLE


# ------------------------------------------------------------------ #
# TestLoadOrgs
# ------------------------------------------------------------------ #


class TestLoadOrgs:
    """Tests for _load_orgs() with caching and fallback."""

    @pytest.mark.asyncio
    async def test_loads_and_caches_orgs(self, adapter):
        mock_orgs = [
            {"codigo": "26000", "descricao": "MEC"},
            {"codigo": "36000", "descricao": "MS"},
        ]
        adapter._request_with_retry = AsyncMock(return_value=mock_orgs)

        orgs = await adapter._load_orgs()

        assert len(orgs) == 2
        assert ("26000", "MEC") in orgs
        adapter._request_with_retry.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_cached_within_ttl(self, adapter):
        adapter._org_cache = [("26000", "MEC")]
        adapter._org_cache_ts = time.monotonic()  # Fresh cache

        adapter._request_with_retry = AsyncMock()

        orgs = await adapter._load_orgs()

        assert orgs == [("26000", "MEC")]
        adapter._request_with_retry.assert_not_called()

    @pytest.mark.asyncio
    async def test_refreshes_after_ttl(self, adapter):
        adapter._org_cache = [("26000", "MEC")]
        adapter._org_cache_ts = time.monotonic() - 90000  # Expired

        mock_orgs = [{"codigo": "36000", "descricao": "MS"}]
        adapter._request_with_retry = AsyncMock(return_value=mock_orgs)

        orgs = await adapter._load_orgs()

        assert len(orgs) == 1
        assert orgs[0][0] == "36000"

    @pytest.mark.asyncio
    async def test_empty_response_uses_fallback(self, adapter):
        adapter._request_with_retry = AsyncMock(return_value=[])

        orgs = await adapter._load_orgs()

        # Should have the hardcoded fallback list
        assert len(orgs) >= 5
        org_codes = [code for code, _ in orgs]
        assert "26000" in org_codes  # MEC in fallback

    @pytest.mark.asyncio
    async def test_api_error_uses_stale_cache(self, adapter):
        adapter._org_cache = [("26000", "MEC")]
        adapter._org_cache_ts = time.monotonic() - 90000  # Expired

        adapter._request_with_retry = AsyncMock(
            side_effect=SourceAPIError("PORTAL_TRANSPARENCIA", 500, "Server error")
        )

        orgs = await adapter._load_orgs()

        assert orgs == [("26000", "MEC")]

    @pytest.mark.asyncio
    async def test_api_error_no_cache_raises(self, adapter):
        adapter._org_cache = []
        adapter._request_with_retry = AsyncMock(
            side_effect=SourceAPIError("PORTAL_TRANSPARENCIA", 500, "Server error")
        )

        with pytest.raises(SourceAPIError):
            await adapter._load_orgs()

    @pytest.mark.asyncio
    async def test_dict_response_with_data_key(self, adapter):
        """Handle response as dict with 'data' key."""
        mock_response = {
            "data": [
                {"codigo": "26000", "descricao": "MEC"},
            ]
        }
        adapter._request_with_retry = AsyncMock(return_value=mock_response)

        orgs = await adapter._load_orgs()

        assert len(orgs) == 1
        assert orgs[0] == ("26000", "MEC")

    @pytest.mark.asyncio
    async def test_alternative_field_names(self, adapter):
        """Orgs API may use codigoSiafi / nome instead of codigo / descricao."""
        mock_orgs = [
            {"codigoSiafi": "52000", "nome": "Ministerio da Defesa"},
        ]
        adapter._request_with_retry = AsyncMock(return_value=mock_orgs)

        orgs = await adapter._load_orgs()

        assert len(orgs) == 1
        assert orgs[0] == ("52000", "Ministerio da Defesa")

    @pytest.mark.asyncio
    async def test_max_orgs_limit(self, adapter):
        """Should limit to MAX_ORGS entries."""
        mock_orgs = [{"codigo": str(i), "descricao": f"Org-{i}"} for i in range(100)]
        adapter._request_with_retry = AsyncMock(return_value=mock_orgs)

        orgs = await adapter._load_orgs()

        assert len(orgs) == adapter.MAX_ORGS


# ------------------------------------------------------------------ #
# TestFetch
# ------------------------------------------------------------------ #


class TestFetch:
    """Tests for the fetch() async generator."""

    @pytest.mark.asyncio
    async def test_fetch_no_api_key_yields_nothing(self, adapter_no_key):
        results = [r async for r in adapter_no_key.fetch("2026-01-01", "2026-01-31")]
        assert results == []

    @pytest.mark.asyncio
    async def test_fetch_invalid_date_range_yields_nothing(self, adapter, small_org_list):
        adapter._load_orgs = AsyncMock(return_value=small_org_list)
        adapter._request_with_retry = AsyncMock()

        results = [r async for r in adapter.fetch("2026-03-01", "2026-01-01")]
        assert results == []
        adapter._request_with_retry.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_basic_records(self, adapter, small_org_list, sample_raw_record):
        adapter._load_orgs = AsyncMock(return_value=small_org_list)

        # First call returns data, second call returns empty (end of page)
        # For 2 orgs x 1 date chunk = pattern repeats
        call_count = 0

        async def mock_request(method, path, params=None):
            nonlocal call_count
            call_count += 1
            if params and params.get("pagina") == 1 and params.get("codigoOrgao") == "26000":
                return [sample_raw_record]
            return []

        adapter._request_with_retry = AsyncMock(side_effect=mock_request)

        results = [r async for r in adapter.fetch("2026-01-01", "2026-01-31")]

        assert len(results) == 1
        assert results[0].source_id == "12345"
        assert results[0].source_name == "PORTAL_TRANSPARENCIA"

    @pytest.mark.asyncio
    async def test_fetch_deduplicates_by_source_id(self, adapter, small_org_list, sample_raw_record):
        adapter._load_orgs = AsyncMock(return_value=small_org_list)

        # Both orgs return the same record
        async def mock_request(method, path, params=None):
            if params and params.get("pagina") == 1:
                return [sample_raw_record]
            return []

        adapter._request_with_retry = AsyncMock(side_effect=mock_request)

        results = [r async for r in adapter.fetch("2026-01-01", "2026-01-31")]

        # Should be deduplicated to 1 record despite 2 orgs returning it
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_fetch_uf_filter(self, adapter, small_org_list, sample_raw_record):
        adapter._load_orgs = AsyncMock(return_value=small_org_list)

        async def mock_request(method, path, params=None):
            if params and params.get("pagina") == 1 and params.get("codigoOrgao") == "26000":
                return [sample_raw_record]  # DF record
            return []

        adapter._request_with_retry = AsyncMock(side_effect=mock_request)

        # Filter for SP only -- should exclude DF record
        results = [r async for r in adapter.fetch("2026-01-01", "2026-01-31", ufs={"SP"})]
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_fetch_uf_filter_matches(self, adapter, small_org_list, sample_raw_record):
        adapter._load_orgs = AsyncMock(return_value=small_org_list)

        async def mock_request(method, path, params=None):
            if params and params.get("pagina") == 1 and params.get("codigoOrgao") == "26000":
                return [sample_raw_record]  # DF record
            return []

        adapter._request_with_retry = AsyncMock(side_effect=mock_request)

        # Filter for DF -- should include
        results = [r async for r in adapter.fetch("2026-01-01", "2026-01-31", ufs={"DF"})]
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_fetch_skips_empty_uf_when_filter_active(self, adapter, small_org_list):
        adapter._load_orgs = AsyncMock(return_value=small_org_list)

        raw_no_uf = {"id": "no-uf-001", "objeto": "Something"}

        async def mock_request(method, path, params=None):
            if params and params.get("pagina") == 1 and params.get("codigoOrgao") == "26000":
                return [raw_no_uf]
            return []

        adapter._request_with_retry = AsyncMock(side_effect=mock_request)

        results = [r async for r in adapter.fetch("2026-01-01", "2026-01-31", ufs={"SP"})]
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_fetch_no_uf_filter_includes_all(self, adapter, small_org_list, sample_raw_record):
        adapter._load_orgs = AsyncMock(return_value=small_org_list)

        async def mock_request(method, path, params=None):
            if params and params.get("pagina") == 1 and params.get("codigoOrgao") == "26000":
                return [sample_raw_record]
            return []

        adapter._request_with_retry = AsyncMock(side_effect=mock_request)

        results = [r async for r in adapter.fetch("2026-01-01", "2026-01-31", ufs=None)]
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_fetch_pagination(self, adapter, sample_raw_record):
        adapter._load_orgs = AsyncMock(return_value=[("26000", "MEC")])

        page2_record = dict(sample_raw_record)
        page2_record["id"] = "67890"

        async def mock_request(method, path, params=None):
            if params and params.get("pagina") == 1:
                return [sample_raw_record]
            elif params and params.get("pagina") == 2:
                return [page2_record]
            return []

        adapter._request_with_retry = AsyncMock(side_effect=mock_request)

        results = [r async for r in adapter.fetch("2026-01-01", "2026-01-31")]

        assert len(results) == 2
        ids = {r.source_id for r in results}
        assert ids == {"12345", "67890"}

    @pytest.mark.asyncio
    async def test_fetch_auth_error_propagates(self, adapter, small_org_list):
        adapter._load_orgs = AsyncMock(return_value=small_org_list)
        adapter._request_with_retry = AsyncMock(
            side_effect=SourceAuthError("PORTAL_TRANSPARENCIA", "Bad key")
        )

        with pytest.raises(SourceAuthError):
            results = [r async for r in adapter.fetch("2026-01-01", "2026-01-31")]

    @pytest.mark.asyncio
    async def test_fetch_4xx_skips_org(self, adapter, small_org_list, sample_raw_record):
        adapter._load_orgs = AsyncMock(return_value=small_org_list)

        async def mock_request(method, path, params=None):
            if params and params.get("codigoOrgao") == "26000":
                raise SourceAPIError("PORTAL_TRANSPARENCIA", 400, "Bad request")
            if params and params.get("pagina") == 1 and params.get("codigoOrgao") == "36000":
                return [sample_raw_record]
            return []

        adapter._request_with_retry = AsyncMock(side_effect=mock_request)

        results = [r async for r in adapter.fetch("2026-01-01", "2026-01-31")]
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_fetch_handles_normalize_errors_gracefully(self, adapter, small_org_list):
        adapter._load_orgs = AsyncMock(return_value=small_org_list)

        # A record that will fail normalization (no id)
        bad_record = {"objeto": "No ID here"}
        good_record = {"id": "good-1", "objeto": "Valid"}

        async def mock_request(method, path, params=None):
            if params and params.get("pagina") == 1 and params.get("codigoOrgao") == "26000":
                return [bad_record, good_record]
            return []

        adapter._request_with_retry = AsyncMock(side_effect=mock_request)

        results = [r async for r in adapter.fetch("2026-01-01", "2026-01-31")]
        assert len(results) == 1
        assert results[0].source_id == "good-1"

    @pytest.mark.asyncio
    async def test_fetch_dict_response_with_data_key(self, adapter, sample_raw_record):
        adapter._load_orgs = AsyncMock(return_value=[("26000", "MEC")])

        async def mock_request(method, path, params=None):
            if params and params.get("pagina") == 1:
                return {"data": [sample_raw_record]}
            return {"data": []}

        adapter._request_with_retry = AsyncMock(side_effect=mock_request)

        results = [r async for r in adapter.fetch("2026-01-01", "2026-01-31")]
        assert len(results) == 1


# ------------------------------------------------------------------ #
# TestRetry
# ------------------------------------------------------------------ #


class TestRetry:
    """Tests for _request_with_retry() retry and error handling."""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self, adapter):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "1"}]

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        result = await adapter._request_with_retry("GET", "/test")
        assert result == [{"id": "1"}]

    @pytest.mark.asyncio
    async def test_204_returns_empty_list(self, adapter):
        mock_response = MagicMock()
        mock_response.status_code = 204

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        result = await adapter._request_with_retry("GET", "/test")
        assert result == []

    @pytest.mark.asyncio
    async def test_401_raises_auth_error_no_retry(self, adapter):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        with pytest.raises(SourceAuthError):
            await adapter._request_with_retry("GET", "/test")

        # Should NOT retry on 401
        assert mock_client.request.call_count == 1

    @pytest.mark.asyncio
    async def test_403_raises_auth_error(self, adapter):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        with pytest.raises(SourceAuthError):
            await adapter._request_with_retry("GET", "/test")

    @pytest.mark.asyncio
    async def test_429_retries_then_raises(self, adapter):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "1"}

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(SourceRateLimitError):
                await adapter._request_with_retry("GET", "/test")

        # Should have retried MAX_RETRIES times then raised
        assert mock_client.request.call_count == adapter.MAX_RETRIES + 1

    @pytest.mark.asyncio
    async def test_5xx_retries_then_raises(self, adapter):
        mock_response = MagicMock()
        mock_response.status_code = 502
        mock_response.text = "Bad Gateway"

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(SourceAPIError):
                await adapter._request_with_retry("GET", "/test")

        assert mock_client.request.call_count == adapter.MAX_RETRIES + 1

    @pytest.mark.asyncio
    async def test_5xx_recovers_on_retry(self, adapter):
        error_response = MagicMock()
        error_response.status_code = 500
        error_response.text = "Server Error"

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = [{"id": "ok"}]

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(
            side_effect=[error_response, success_response]
        )
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await adapter._request_with_retry("GET", "/test")

        assert result == [{"id": "ok"}]
        assert mock_client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_timeout_retries_then_raises(self, adapter):
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(
            side_effect=httpx.TimeoutException("timeout")
        )
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(SourceTimeoutError):
                await adapter._request_with_retry("GET", "/test")

        assert mock_client.request.call_count == adapter.MAX_RETRIES + 1

    @pytest.mark.asyncio
    async def test_request_error_retries_then_raises(self, adapter):
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(
            side_effect=httpx.ConnectError("connection refused")
        )
        mock_client.is_closed = False
        adapter._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(SourceAPIError):
                await adapter._request_with_retry("GET", "/test")

    @pytest.mark.asyncio
    async def test_4xx_no_retry(self, adapter):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        with pytest.raises(SourceAPIError):
            await adapter._request_with_retry("GET", "/test")

        # 4xx (except 429) should NOT retry
        assert mock_client.request.call_count == 1


# ------------------------------------------------------------------ #
# TestBackoff
# ------------------------------------------------------------------ #


class TestBackoff:
    """Tests for _calculate_backoff()."""

    def test_backoff_attempt_0(self, adapter):
        delay = adapter._calculate_backoff(0)
        # Base 2.0 * 2^0 = 2.0, with jitter 0.5-1.5 => 1.0-3.0
        assert 0.5 <= delay <= 4.0

    def test_backoff_attempt_1(self, adapter):
        delay = adapter._calculate_backoff(1)
        # Base 2.0 * 2^1 = 4.0, with jitter 0.5-1.5 => 2.0-6.0
        assert 1.0 <= delay <= 7.0

    def test_backoff_capped_at_60(self, adapter):
        delay = adapter._calculate_backoff(10)
        # 2.0 * 2^10 = 2048, capped at 60, with jitter => max 90
        assert delay <= 90.0


# ------------------------------------------------------------------ #
# TestRateLimit
# ------------------------------------------------------------------ #


class TestRateLimit:
    """Tests for _rate_limit() delay enforcement."""

    @pytest.mark.asyncio
    async def test_rate_limit_sleeps_when_too_fast(self, adapter):
        loop = asyncio.get_event_loop()
        # Simulate last request was just now
        adapter._last_request_time = loop.time()

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await adapter._rate_limit()
            # Should have slept for roughly RATE_LIMIT_DELAY
            if mock_sleep.called:
                sleep_time = mock_sleep.call_args[0][0]
                assert 0 < sleep_time <= adapter.RATE_LIMIT_DELAY

    @pytest.mark.asyncio
    async def test_rate_limit_no_sleep_when_enough_elapsed(self, adapter):
        loop = asyncio.get_event_loop()
        # Simulate last request was 2 seconds ago
        adapter._last_request_time = loop.time() - 2.0

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await adapter._rate_limit()
            mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_rate_limit_increments_request_count(self, adapter):
        adapter._last_request_time = 0.0  # Long ago
        initial_count = adapter._request_count

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await adapter._rate_limit()

        assert adapter._request_count == initial_count + 1


# ------------------------------------------------------------------ #
# TestLifecycle
# ------------------------------------------------------------------ #


class TestLifecycle:
    """Tests for context manager and close()."""

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
    async def test_close_no_client_is_safe(self, adapter):
        adapter._client = None
        await adapter.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_close_already_closed_client(self, adapter):
        mock_client = AsyncMock()
        mock_client.is_closed = True
        adapter._client = mock_client

        await adapter.close()
        mock_client.aclose.assert_not_called()

    @pytest.mark.asyncio
    async def test_context_manager_enter(self, adapter):
        result = await adapter.__aenter__()
        assert result is adapter

    @pytest.mark.asyncio
    async def test_context_manager_exit_closes(self, adapter):
        mock_client = AsyncMock()
        mock_client.is_closed = False
        mock_client.aclose = AsyncMock()
        adapter._client = mock_client

        await adapter.__aexit__(None, None, None)

        mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_with_usage(self):
        async with PortalTransparenciaAdapter(api_key="test") as a:
            assert isinstance(a, PortalTransparenciaAdapter)
        # After exiting, client should be cleaned up
        assert a._client is None

    @pytest.mark.asyncio
    async def test_get_client_creates_client(self, adapter):
        assert adapter._client is None
        client = await adapter._get_client()
        assert client is not None
        assert isinstance(client, httpx.AsyncClient)
        # Clean up
        await adapter.close()

    @pytest.mark.asyncio
    async def test_get_client_reuses_existing(self, adapter):
        client1 = await adapter._get_client()
        client2 = await adapter._get_client()
        assert client1 is client2
        await adapter.close()

    @pytest.mark.asyncio
    async def test_get_client_recreates_after_close(self, adapter):
        client1 = await adapter._get_client()
        await adapter.close()
        client2 = await adapter._get_client()
        assert client1 is not client2
        await adapter.close()


# ------------------------------------------------------------------ #
# TestInit
# ------------------------------------------------------------------ #


class TestInit:
    """Tests for __init__ configuration."""

    def test_default_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("PORTAL_TRANSPARENCIA_API_KEY", "env-key-456")
        a = PortalTransparenciaAdapter()
        assert a._api_key == "env-key-456"

    def test_explicit_api_key_overrides_env(self, monkeypatch):
        monkeypatch.setenv("PORTAL_TRANSPARENCIA_API_KEY", "env-key")
        a = PortalTransparenciaAdapter(api_key="explicit-key")
        assert a._api_key == "explicit-key"

    def test_default_timeout(self):
        a = PortalTransparenciaAdapter(api_key="key")
        assert a._timeout == PortalTransparenciaAdapter.DEFAULT_TIMEOUT

    def test_custom_timeout(self):
        a = PortalTransparenciaAdapter(api_key="key", timeout=60)
        assert a._timeout == 60

    def test_initial_state(self):
        a = PortalTransparenciaAdapter(api_key="key")
        assert a._client is None
        assert a._request_count == 0
        assert a._org_cache == []
        assert a._last_request_time == 0.0
