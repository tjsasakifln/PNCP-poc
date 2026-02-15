"""Tests for QueridoDiarioClient and qd_extraction pipeline (STORY-255 AC18-AC21).

Comprehensive test suite covering:
- AC18: Querystring builder, pagination, rate limiting
- AC19: LLM extraction with mock (sample text -> structured output)
- AC20: Regex fallback extraction (pregao number, R$ value, opening date)
- AC21: Integration test with real QD API
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

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
from clients.querido_diario_client import (
    PROCUREMENT_CONTEXT_TERMS,
    QueridoDiarioClient,
)
from clients.qd_extraction import (
    ExtractionResult,
    batch_extract_from_gazettes,
    extract_procurement_from_text,
    extract_procurement_regex_fallback,
    to_unified_procurement,
)
from schemas import ExtractedProcurement


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #


@pytest.fixture
def adapter():
    """Adapter with default timeout."""
    return QueridoDiarioClient(timeout=5)


@pytest.fixture
def sample_gazette():
    """A complete raw gazette result for normalization tests."""
    return {
        "territory_id": "3550308",
        "territory_name": "Sao Paulo",
        "state_code": "SP",
        "date": "2026-02-10",
        "url": "https://example.com/gazette/123",
        "txt_url": "https://example.com/gazette/123.txt",
        "excerpts": ["Pregao eletronico para uniformes escolares..."],
        "edition": "1234",
        "is_extra_edition": False,
    }


@pytest.fixture
def sample_gazette_extra():
    """A gazette result with is_extra_edition=True."""
    return {
        "territory_id": "3550308",
        "territory_name": "Sao Paulo",
        "state_code": "SP",
        "date": "2026-02-10",
        "url": "https://example.com/gazette/124",
        "txt_url": "https://example.com/gazette/124.txt",
        "excerpts": ["Edital de concorrencia publica..."],
        "edition": "1234",
        "is_extra_edition": True,
    }


# ------------------------------------------------------------------ #
# TestMetadata
# ------------------------------------------------------------------ #


class TestMetadata:
    """Tests for source metadata property."""

    def test_metadata_code(self, adapter):
        assert adapter.code == "QUERIDO_DIARIO"

    def test_metadata_name(self, adapter):
        assert "Querido" in adapter.name

    def test_metadata_priority(self, adapter):
        assert adapter.metadata.priority == 5

    def test_metadata_rate_limit(self, adapter):
        assert adapter.metadata.rate_limit_rps == 1.0

    def test_metadata_base_url(self, adapter):
        assert "queridodiario" in adapter.metadata.base_url

    def test_metadata_capabilities(self, adapter):
        caps = adapter.metadata.capabilities
        assert SourceCapability.FILTER_BY_KEYWORD in caps
        assert SourceCapability.PAGINATION in caps
        assert SourceCapability.DATE_RANGE in caps

    def test_code_shortcut(self, adapter):
        """SourceAdapter.code property delegates to metadata.code."""
        assert adapter.code == adapter.metadata.code

    def test_name_shortcut(self, adapter):
        """SourceAdapter.name property delegates to metadata.name."""
        assert adapter.name == adapter.metadata.name


# ------------------------------------------------------------------ #
# TestQuerystringBuilder (AC18)
# ------------------------------------------------------------------ #


class TestQuerystringBuilder:
    """Tests for build_querystring static method."""

    def test_empty_keywords(self):
        """Should return procurement context terms only."""
        qs = QueridoDiarioClient.build_querystring(set())
        assert "licitacao" in qs
        assert "pregao" in qs
        assert "edital" in qs
        # Should NOT contain the AND operator since no keywords group
        assert "+" not in qs

    def test_single_keyword(self):
        """Single keyword combined with context terms via AND."""
        qs = QueridoDiarioClient.build_querystring({"uniforme"})
        assert "uniforme" in qs
        assert "+" in qs  # AND operator between groups

    def test_multiple_keywords(self):
        """Multiple keywords joined with OR within their group."""
        qs = QueridoDiarioClient.build_querystring(
            {"uniforme", "fardamento", "jaleco"}
        )
        assert "|" in qs  # OR between keywords
        assert "+" in qs  # AND between groups
        assert "uniforme" in qs
        assert "fardamento" in qs
        assert "jaleco" in qs

    def test_multi_word_keywords_quoted(self):
        """Multi-word keywords should be wrapped in quotes."""
        qs = QueridoDiarioClient.build_querystring(
            {"servicos de limpeza", "manutencao predial"}
        )
        assert '"servicos de limpeza"' in qs or '"manutencao predial"' in qs

    def test_all_context_terms_present(self):
        """All procurement context terms should be included."""
        qs = QueridoDiarioClient.build_querystring({"uniforme"})
        for term in PROCUREMENT_CONTEXT_TERMS:
            assert term in qs, f"Missing context term: {term}"

    def test_whitespace_only_keywords_ignored(self):
        """Keywords that are only whitespace should be ignored."""
        qs = QueridoDiarioClient.build_querystring({"  ", ""})
        # Should fall back to context-only (no + operator)
        assert "+" not in qs

    def test_querystring_format_structure(self):
        """Output should follow (context) + (keywords) structure."""
        qs = QueridoDiarioClient.build_querystring({"uniforme"})
        # Should have two groups separated by +
        parts = qs.split("+")
        assert len(parts) == 2
        assert "(" in parts[0] and ")" in parts[0]
        assert "(" in parts[1] and ")" in parts[1]


# ------------------------------------------------------------------ #
# TestHealthCheck
# ------------------------------------------------------------------ #


class TestHealthCheck:
    """Tests for health_check method."""

    @pytest.mark.asyncio
    async def test_health_available(self, adapter):
        """Mock HTTP 200 with fast response -> AVAILABLE."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_health_unavailable_timeout(self, adapter):
        """Mock timeout -> UNAVAILABLE."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.TimeoutException("timeout")
        )
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_health_unavailable_request_error(self, adapter):
        """Mock request error -> UNAVAILABLE."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.RequestError("connection refused")
        )
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_health_degraded_non_200(self, adapter):
        """Mock HTTP non-200 response -> DEGRADED."""
        mock_response = MagicMock()
        mock_response.status_code = 503

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client

        status = await adapter.health_check()
        assert status == SourceStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_health_degraded_slow(self, adapter):
        """Mock HTTP 200 but slow (>4s) -> DEGRADED."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.is_closed = False
        adapter._client = mock_client

        call_count = 0

        # Simulate time progression: first call returns start, second returns start+5s
        original_time = asyncio.get_event_loop().time

        async def slow_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock_response

        mock_client.get = slow_get

        # Patch the event loop time to simulate slow response
        times = iter([100.0, 105.0])  # 5 second gap -> > 4s threshold

        with patch.object(
            asyncio.get_event_loop(), "time", side_effect=times
        ):
            status = await adapter.health_check()

        assert status == SourceStatus.DEGRADED


# ------------------------------------------------------------------ #
# TestNormalize
# ------------------------------------------------------------------ #


class TestNormalize:
    """Tests for normalize method."""

    def test_normalize_complete_record(self, adapter, sample_gazette):
        """Complete gazette record normalizes to correct UnifiedProcurement."""
        record = adapter.normalize(sample_gazette)

        assert isinstance(record, UnifiedProcurement)
        assert record.source_id == "QD-3550308-2026-02-10-1234"
        assert record.source_name == "QUERIDO_DIARIO"
        assert record.uf == "SP"
        assert record.municipio == "Sao Paulo"
        assert record.esfera == "M"
        assert "uniformes" in record.objeto

    def test_normalize_extra_edition(self, adapter, sample_gazette_extra):
        """is_extra_edition=True -> source_id includes '-extra'."""
        record = adapter.normalize(sample_gazette_extra)
        assert "-extra" in record.source_id
        assert record.source_id == "QD-3550308-2026-02-10-1234-extra"

    def test_normalize_missing_excerpts(self, adapter):
        """Empty excerpts list -> objeto is empty string."""
        raw = {
            "territory_id": "3550308",
            "territory_name": "Sao Paulo",
            "state_code": "SP",
            "date": "2026-02-10",
            "url": "https://example.com",
            "txt_url": "",
            "excerpts": [],
            "edition": "100",
            "is_extra_edition": False,
        }
        record = adapter.normalize(raw)
        assert record.objeto == ""

    def test_normalize_string_excerpt(self, adapter):
        """Excerpts as a string (not list) are handled gracefully."""
        raw = {
            "territory_id": "3550308",
            "territory_name": "Sao Paulo",
            "state_code": "SP",
            "date": "2026-02-10",
            "url": "https://example.com",
            "txt_url": "",
            "excerpts": "Pregao para materiais de escritorio",
            "edition": "100",
            "is_extra_edition": False,
        }
        record = adapter.normalize(raw)
        assert "materiais de escritorio" in record.objeto

    def test_normalize_missing_fields_raises(self, adapter):
        """Missing territory_id -> SourceParseError."""
        raw = {
            "territory_name": "Sao Paulo",
            "state_code": "SP",
            "date": "2026-02-10",
        }
        with pytest.raises(SourceParseError):
            adapter.normalize(raw)

    def test_normalize_missing_date_raises(self, adapter):
        """Missing date -> SourceParseError."""
        raw = {
            "territory_id": "3550308",
            "territory_name": "Sao Paulo",
            "state_code": "SP",
        }
        with pytest.raises(SourceParseError):
            adapter.normalize(raw)

    def test_normalize_default_edition(self, adapter):
        """Missing edition -> defaults to 'main'."""
        raw = {
            "territory_id": "3550308",
            "territory_name": "Sao Paulo",
            "state_code": "SP",
            "date": "2026-02-10",
            "url": "https://example.com",
            "txt_url": "",
            "excerpts": [],
            "is_extra_edition": False,
        }
        record = adapter.normalize(raw)
        assert "main" in record.source_id

    def test_normalize_data_publicacao_parsed(self, adapter, sample_gazette):
        """Date string is parsed to datetime object."""
        record = adapter.normalize(sample_gazette)
        assert record.data_publicacao is not None
        assert record.data_publicacao.year == 2026
        assert record.data_publicacao.month == 2
        assert record.data_publicacao.day == 10

    def test_normalize_link_fields(self, adapter, sample_gazette):
        """URL fields are mapped correctly."""
        record = adapter.normalize(sample_gazette)
        assert record.link_portal == "https://example.com/gazette/123"
        assert record.link_edital == "https://example.com/gazette/123.txt"

    def test_normalize_situacao_always_publicada(self, adapter, sample_gazette):
        """Gazette content is always 'Publicada'."""
        record = adapter.normalize(sample_gazette)
        assert record.situacao == "Publicada"

    def test_normalize_valor_estimado_zero(self, adapter, sample_gazette):
        """Gazette search has no value -> valor_estimado is 0.0."""
        record = adapter.normalize(sample_gazette)
        assert record.valor_estimado == 0.0

    def test_normalize_ano_extracted_from_date(self, adapter, sample_gazette):
        """Year is extracted from the date field."""
        record = adapter.normalize(sample_gazette)
        assert record.ano == "2026"

    def test_normalize_multiple_excerpts_joined(self, adapter):
        """Multiple excerpts are joined with separator."""
        raw = {
            "territory_id": "3550308",
            "territory_name": "Sao Paulo",
            "state_code": "SP",
            "date": "2026-02-10",
            "url": "https://example.com",
            "txt_url": "",
            "excerpts": [
                "Primeiro trecho do edital",
                "Segundo trecho com detalhes",
            ],
            "edition": "100",
            "is_extra_edition": False,
        }
        record = adapter.normalize(raw)
        assert "Primeiro trecho" in record.objeto
        assert "Segundo trecho" in record.objeto
        assert "[...]" in record.objeto


# ------------------------------------------------------------------ #
# TestFetch (AC18 - pagination)
# ------------------------------------------------------------------ #


class TestFetch:
    """Tests for fetch method including pagination."""

    @pytest.mark.asyncio
    async def test_fetch_yields_records(self, adapter):
        """Mock search_gazettes returns sample data -> records yielded."""
        mock_response = {
            "total_gazettes": 2,
            "gazettes": [
                {
                    "territory_id": "3550308",
                    "territory_name": "Sao Paulo",
                    "state_code": "SP",
                    "date": "2026-02-10",
                    "url": "https://example.com/1",
                    "txt_url": "https://example.com/1.txt",
                    "excerpts": ["Uniforme escolar"],
                    "edition": "100",
                    "is_extra_edition": False,
                },
                {
                    "territory_id": "3304557",
                    "territory_name": "Rio de Janeiro",
                    "state_code": "RJ",
                    "date": "2026-02-10",
                    "url": "https://example.com/2",
                    "txt_url": "https://example.com/2.txt",
                    "excerpts": ["Fardamento militar"],
                    "edition": "200",
                    "is_extra_edition": False,
                },
            ],
        }

        adapter.search_gazettes = AsyncMock(return_value=mock_response)

        records = []
        async for record in adapter.fetch("2026-02-01", "2026-02-14"):
            records.append(record)

        assert len(records) == 2
        assert records[0].uf == "SP"
        assert records[1].uf == "RJ"

    @pytest.mark.asyncio
    async def test_fetch_pagination(self, adapter):
        """Mock multiple pages -> all records collected."""
        page1 = {
            "total_gazettes": 40,
            "gazettes": [
                {
                    "territory_id": str(3550000 + i),
                    "territory_name": f"City {i}",
                    "state_code": "SP",
                    "date": "2026-02-10",
                    "url": f"https://example.com/{i}",
                    "txt_url": f"https://example.com/{i}.txt",
                    "excerpts": [f"Excerpt {i}"],
                    "edition": str(i),
                    "is_extra_edition": False,
                }
                for i in range(20)
            ],
        }
        page2 = {
            "total_gazettes": 40,
            "gazettes": [
                {
                    "territory_id": str(3550020 + i),
                    "territory_name": f"City {20 + i}",
                    "state_code": "SP",
                    "date": "2026-02-10",
                    "url": f"https://example.com/{20 + i}",
                    "txt_url": f"https://example.com/{20 + i}.txt",
                    "excerpts": [f"Excerpt {20 + i}"],
                    "edition": str(20 + i),
                    "is_extra_edition": False,
                }
                for i in range(20)
            ],
        }

        adapter.search_gazettes = AsyncMock(side_effect=[page1, page2])

        records = []
        async for record in adapter.fetch("2026-02-01", "2026-02-14"):
            records.append(record)

        assert len(records) == 40
        assert adapter.search_gazettes.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_uf_filter(self, adapter):
        """Mock results with mixed UFs -> only requested UFs yielded."""
        mock_response = {
            "total_gazettes": 3,
            "gazettes": [
                {
                    "territory_id": "3550308",
                    "territory_name": "Sao Paulo",
                    "state_code": "SP",
                    "date": "2026-02-10",
                    "url": "https://example.com/1",
                    "txt_url": "",
                    "excerpts": ["Edital SP"],
                    "edition": "100",
                    "is_extra_edition": False,
                },
                {
                    "territory_id": "3304557",
                    "territory_name": "Rio de Janeiro",
                    "state_code": "RJ",
                    "date": "2026-02-10",
                    "url": "https://example.com/2",
                    "txt_url": "",
                    "excerpts": ["Edital RJ"],
                    "edition": "200",
                    "is_extra_edition": False,
                },
                {
                    "territory_id": "2927408",
                    "territory_name": "Salvador",
                    "state_code": "BA",
                    "date": "2026-02-10",
                    "url": "https://example.com/3",
                    "txt_url": "",
                    "excerpts": ["Edital BA"],
                    "edition": "300",
                    "is_extra_edition": False,
                },
            ],
        }

        adapter.search_gazettes = AsyncMock(return_value=mock_response)

        records = []
        async for record in adapter.fetch(
            "2026-02-01", "2026-02-14", ufs={"SP", "RJ"}
        ):
            records.append(record)

        assert len(records) == 2
        ufs_found = {r.uf for r in records}
        assert ufs_found == {"SP", "RJ"}

    @pytest.mark.asyncio
    async def test_fetch_max_results_cap(self, adapter):
        """Verify stops at MAX_TOTAL_RESULTS (500) even if more available."""
        # Create a response that claims 1000 total but returns 100 per page
        def make_page(offset):
            return {
                "total_gazettes": 1000,
                "gazettes": [
                    {
                        "territory_id": str(3550000 + offset + i),
                        "territory_name": f"City {offset + i}",
                        "state_code": "SP",
                        "date": "2026-02-10",
                        "url": f"https://example.com/{offset + i}",
                        "txt_url": "",
                        "excerpts": [f"Excerpt {offset + i}"],
                        "edition": str(offset + i),
                        "is_extra_edition": False,
                    }
                    for i in range(20)
                ],
            }

        # Keep returning pages forever
        adapter.search_gazettes = AsyncMock(
            side_effect=lambda **kwargs: make_page(kwargs.get("offset", 0))
        )

        records = []
        async for record in adapter.fetch("2026-02-01", "2026-02-14"):
            records.append(record)

        # Should stop at 500 (MAX_TOTAL_RESULTS)
        assert len(records) == 500

    @pytest.mark.asyncio
    async def test_fetch_empty_results(self, adapter):
        """Mock empty response -> yields nothing."""
        mock_response = {
            "total_gazettes": 0,
            "gazettes": [],
        }

        adapter.search_gazettes = AsyncMock(return_value=mock_response)

        records = []
        async for record in adapter.fetch("2026-02-01", "2026-02-14"):
            records.append(record)

        assert len(records) == 0

    @pytest.mark.asyncio
    async def test_fetch_deduplicates(self, adapter):
        """Duplicate gazette records are skipped."""
        gazette = {
            "territory_id": "3550308",
            "territory_name": "Sao Paulo",
            "state_code": "SP",
            "date": "2026-02-10",
            "url": "https://example.com/1",
            "txt_url": "",
            "excerpts": ["Edital"],
            "edition": "100",
            "is_extra_edition": False,
        }
        mock_response = {
            "total_gazettes": 2,
            "gazettes": [gazette, gazette],  # Duplicate
        }

        adapter.search_gazettes = AsyncMock(return_value=mock_response)

        records = []
        async for record in adapter.fetch("2026-02-01", "2026-02-14"):
            records.append(record)

        assert len(records) == 1

    @pytest.mark.asyncio
    async def test_fetch_sector_keywords_passed(self, adapter):
        """sector_keywords kwarg is used in querystring building."""
        mock_response = {
            "total_gazettes": 0,
            "gazettes": [],
        }
        adapter.search_gazettes = AsyncMock(return_value=mock_response)

        records = []
        async for record in adapter.fetch(
            "2026-02-01",
            "2026-02-14",
            sector_keywords={"uniforme", "fardamento"},
        ):
            records.append(record)

        # Verify search was called with a querystring containing keywords
        call_kwargs = adapter.search_gazettes.call_args
        query = call_kwargs.kwargs.get("query", "") or call_kwargs[1].get(
            "query", ""
        )
        assert "uniforme" in query or "fardamento" in query


# ------------------------------------------------------------------ #
# TestRateLimiter (AC18)
# ------------------------------------------------------------------ #


class TestRateLimiter:
    """Tests for rate limiting between requests."""

    @pytest.mark.asyncio
    async def test_rate_limit_enforces_delay(self, adapter):
        """Patch asyncio.sleep, verify it's called with correct delay."""
        # Set _last_request_time to "just now" so rate limit must wait
        loop = asyncio.get_event_loop()
        current_time = loop.time()
        adapter._last_request_time = current_time

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            # Patch loop.time to return the same time (elapsed = 0)
            with patch.object(loop, "time", return_value=current_time):
                await adapter._rate_limit()

            # Should have been called with approximately RATE_LIMIT_DELAY
            mock_sleep.assert_called_once()
            delay_arg = mock_sleep.call_args[0][0]
            assert delay_arg > 0
            assert delay_arg <= adapter.RATE_LIMIT_DELAY

    @pytest.mark.asyncio
    async def test_rate_limit_no_delay_if_enough_elapsed(self, adapter):
        """No sleep if enough time has passed since last request."""
        loop = asyncio.get_event_loop()
        # Set last request time to 10 seconds ago
        adapter._last_request_time = loop.time() - 10.0

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await adapter._rate_limit()
            mock_sleep.assert_not_called()


# ------------------------------------------------------------------ #
# TestRequestWithRetry
# ------------------------------------------------------------------ #


class TestRequestWithRetry:
    """Tests for _request_with_retry retry logic."""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self, adapter):
        """HTTP 200 on first attempt -> returns parsed JSON."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"total_gazettes": 5, "gazettes": []}

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client
        adapter._last_request_time = 0  # Avoid rate limit delay

        result = await adapter._request_with_retry("GET", "/gazettes")
        assert result == {"total_gazettes": 5, "gazettes": []}

    @pytest.mark.asyncio
    async def test_retry_on_server_error(self, adapter):
        """HTTP 500 -> retries, then succeeds."""
        error_response = MagicMock()
        error_response.status_code = 500
        error_response.text = "Internal Server Error"

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"total_gazettes": 0, "gazettes": []}

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(
            side_effect=[error_response, success_response]
        )
        mock_client.is_closed = False
        adapter._client = mock_client
        adapter._last_request_time = 0

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await adapter._request_with_retry("GET", "/gazettes")

        assert result == {"total_gazettes": 0, "gazettes": []}

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, adapter):
        """Timeout -> retries, then succeeds."""
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"ok": True}

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(
            side_effect=[
                httpx.TimeoutException("timeout"),
                success_response,
            ]
        )
        mock_client.is_closed = False
        adapter._client = mock_client
        adapter._last_request_time = 0

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await adapter._request_with_retry("GET", "/gazettes")

        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_exhausted_retries_raises_timeout(self, adapter):
        """All retries timeout -> raises SourceTimeoutError."""
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(
            side_effect=httpx.TimeoutException("timeout")
        )
        mock_client.is_closed = False
        adapter._client = mock_client
        adapter._last_request_time = 0

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(SourceTimeoutError):
                await adapter._request_with_retry("GET", "/gazettes")

    @pytest.mark.asyncio
    async def test_rate_limit_429_retries(self, adapter):
        """HTTP 429 -> retries with Retry-After, then succeeds."""
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "2"}

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"total_gazettes": 0, "gazettes": []}

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(
            side_effect=[rate_limit_response, success_response]
        )
        mock_client.is_closed = False
        adapter._client = mock_client
        adapter._last_request_time = 0

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await adapter._request_with_retry("GET", "/gazettes")

        assert result == {"total_gazettes": 0, "gazettes": []}
        # Verify rate limit sleep was called with Retry-After value
        sleep_calls = [c[0][0] for c in mock_sleep.call_args_list]
        assert 2 in sleep_calls

    @pytest.mark.asyncio
    async def test_429_exhausted_raises_rate_limit_error(self, adapter):
        """All retries get 429 -> raises SourceRateLimitError."""
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "60"}

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=rate_limit_response)
        mock_client.is_closed = False
        adapter._client = mock_client
        adapter._last_request_time = 0

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(SourceRateLimitError):
                await adapter._request_with_retry("GET", "/gazettes")

    @pytest.mark.asyncio
    async def test_204_returns_empty(self, adapter):
        """HTTP 204 -> returns empty response dict."""
        mock_response = MagicMock()
        mock_response.status_code = 204

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        adapter._client = mock_client
        adapter._last_request_time = 0

        result = await adapter._request_with_retry("GET", "/gazettes")
        assert result == {"total_gazettes": 0, "gazettes": []}

    @pytest.mark.asyncio
    async def test_client_error_no_retry(self, adapter):
        """HTTP 400 (client error, not 429) -> no retry, raises immediately."""
        error_response = MagicMock()
        error_response.status_code = 400
        error_response.text = "Bad Request"

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=error_response)
        mock_client.is_closed = False
        adapter._client = mock_client
        adapter._last_request_time = 0

        with pytest.raises(SourceAPIError):
            await adapter._request_with_retry("GET", "/gazettes")

        # Should only be called once (no retry for 4xx)
        assert mock_client.request.call_count == 1


# ------------------------------------------------------------------ #
# TestRegexFallback (AC20)
# ------------------------------------------------------------------ #


class TestRegexFallback:
    """Tests for extract_procurement_regex_fallback."""

    def test_extract_pregao_number(self):
        """Extracts pregao number from text."""
        text = (
            "AVISO DE LICITACAO - PREGAO ELETRONICO N. 023/2026\n"
            "OBJETO: Aquisicao de uniformes escolares para a rede municipal."
        )
        results = extract_procurement_regex_fallback(
            text, "Sao Paulo", "SP", "https://example.com", "2026-02-10"
        )
        assert len(results) >= 1
        assert any(r.number == "023/2026" for r in results)

    def test_extract_value(self):
        """Extracts R$ value from text."""
        text = (
            "AVISO DE LICITACAO - PREGAO ELETRONICO N. 001/2026\n"
            "OBJETO: Uniformes. VALOR ESTIMADO: R$ 450.000,00"
        )
        results = extract_procurement_regex_fallback(
            text, "Sao Paulo", "SP", "https://example.com", "2026-02-10"
        )
        assert len(results) >= 1
        assert any(
            r.estimated_value is not None and abs(r.estimated_value - 450000.0) < 0.01
            for r in results
        )

    def test_extract_opening_date(self):
        """Extracts opening date from text."""
        text = (
            "AVISO DE LICITACAO - PREGAO ELETRONICO N. 001/2026\n"
            "OBJETO: Uniformes escolares.\n"
            "ABERTURA: 28/02/2026 as 09:00"
        )
        results = extract_procurement_regex_fallback(
            text, "Sao Paulo", "SP", "https://example.com", "2026-02-10"
        )
        assert len(results) >= 1
        assert any(r.opening_date == "2026-02-28" for r in results)

    def test_extract_modality(self):
        """Extracts modality from text."""
        text = (
            "Pregao Eletronico para aquisicao de materiais de escritorio.\n"
            "Processo N. 045/2026. Valor: R$ 80.000,00"
        )
        results = extract_procurement_regex_fallback(
            text, "Sao Paulo", "SP", "https://example.com", "2026-02-10"
        )
        assert len(results) >= 1
        assert any(
            r.modality is not None and "pregao" in r.modality.lower()
            for r in results
        )

    def test_extract_object_after_objeto(self):
        """Extracts object description from OBJETO: field."""
        text = (
            "AVISO DE LICITACAO\n"
            "OBJETO: Aquisicao de uniformes escolares para rede municipal.\n"
            "VALOR ESTIMADO: R$ 100.000,00"
        )
        results = extract_procurement_regex_fallback(
            text, "Sao Paulo", "SP", "https://example.com", "2026-02-10"
        )
        assert len(results) >= 1
        assert any("uniforme" in r.object_description.lower() for r in results)

    def test_confidence_is_low(self):
        """All regex-extracted results have confidence 0.3."""
        text = (
            "PREGAO ELETRONICO N. 001/2026\n"
            "OBJETO: Uniformes escolares. R$ 50.000,00"
        )
        results = extract_procurement_regex_fallback(
            text, "Sao Paulo", "SP", "https://example.com", "2026-02-10"
        )
        assert len(results) >= 1
        assert all(r.extraction_confidence == 0.3 for r in results)

    def test_no_procurement_returns_empty(self):
        """Non-procurement text that is short (<=50 chars) -> empty list.

        The implementation uses len(text.strip()) > 50 as a threshold for
        the whole-text fallback attempt. Text at or below 50 chars with
        no section boundaries yields nothing.
        """
        text = "O prefeito inaugurou escola."
        results = extract_procurement_regex_fallback(
            text, "Sao Paulo", "SP", "https://example.com", "2026-02-10"
        )
        assert results == []

    def test_municipality_and_uf_populated(self):
        """Municipality and UF are set from function arguments."""
        text = (
            "PREGAO ELETRONICO N. 001/2026\n"
            "OBJETO: Materiais de limpeza. R$ 50.000,00"
        )
        results = extract_procurement_regex_fallback(
            text, "Campinas", "SP", "https://example.com", "2026-02-10"
        )
        assert len(results) >= 1
        for r in results:
            assert r.municipality == "Campinas"
            assert r.uf == "SP"

    def test_source_url_populated(self):
        """Source URL is set from function argument."""
        text = (
            "PREGAO ELETRONICO N. 001/2026\n"
            "OBJETO: Servicos de vigilancia. R$ 200.000,00"
        )
        results = extract_procurement_regex_fallback(
            text, "Sao Paulo", "SP", "https://qd.example.com/gazette/456", "2026-02-10"
        )
        assert len(results) >= 1
        for r in results:
            assert r.source_url == "https://qd.example.com/gazette/456"

    def test_full_gazette_sample(self):
        """Complete gazette-like text with multiple procurements."""
        text = """
        AVISO DE LICITACAO - PREGAO ELETRONICO N. 023/2026
        OBJETO: Aquisicao de uniformes escolares para a rede municipal de ensino,
        compreendendo camisetas, bermudas e tenis, conforme especificacoes do
        Termo de Referencia. VALOR ESTIMADO: R$ 450.000,00. ABERTURA:
        28/02/2026 as 09:00. Edital disponivel em: compras.gov.br

        AVISO DE LICITACAO - PREGAO ELETRONICO N. 024/2026
        OBJETO: Contratacao de servicos de limpeza predial.
        VALOR ESTIMADO: R$ 120.000,00. ABERTURA: 01/03/2026.
        """
        results = extract_procurement_regex_fallback(
            text, "Sao Paulo", "SP", "https://example.com", "2026-02-10"
        )
        assert len(results) >= 2

        # Verify the first procurement details
        numbers = {r.number for r in results if r.number}
        assert "023/2026" in numbers
        assert "024/2026" in numbers

    def test_raw_excerpt_populated(self):
        """Raw excerpt field is populated with section text."""
        text = (
            "PREGAO ELETRONICO N. 099/2026\n"
            "OBJETO: Materiais hospitalares. R$ 300.000,00"
        )
        results = extract_procurement_regex_fallback(
            text, "Sao Paulo", "SP", "https://example.com", "2026-02-10"
        )
        assert len(results) >= 1
        assert len(results[0].raw_excerpt) > 0

    def test_value_largest_selected(self):
        """When multiple R$ values exist, the largest is used."""
        text = (
            "PREGAO ELETRONICO N. 001/2026\n"
            "OBJETO: Equipamentos de informatica.\n"
            "Lote 1: R$ 50.000,00\n"
            "Lote 2: R$ 150.000,00\n"
            "VALOR TOTAL ESTIMADO: R$ 200.000,00"
        )
        results = extract_procurement_regex_fallback(
            text, "Sao Paulo", "SP", "https://example.com", "2026-02-10"
        )
        assert len(results) >= 1
        # Should pick the largest value (200000.0)
        assert any(
            r.estimated_value is not None and abs(r.estimated_value - 200000.0) < 0.01
            for r in results
        )


# ------------------------------------------------------------------ #
# TestLLMExtraction (AC19)
# ------------------------------------------------------------------ #


class TestLLMExtraction:
    """Tests for LLM-based extraction with mocked OpenAI client."""

    @pytest.mark.asyncio
    async def test_llm_extraction_with_mock(self):
        """Mock OpenAI client returns structured data -> correct parsing."""
        mock_extracted = ExtractedProcurement(
            modality="Pregao Eletronico",
            number="023/2026",
            object_description="Uniformes escolares",
            estimated_value=450000.0,
            opening_date="2026-02-28",
            agency_name="Prefeitura de Sao Paulo",
            municipality="Sao Paulo",
            uf="SP",
            source_url="https://example.com",
            gazette_date="2026-02-10",
            extraction_confidence=0.85,
            raw_excerpt="Pregao para uniformes...",
        )

        mock_result = ExtractionResult(procurements=[mock_extracted])

        mock_parsed_message = MagicMock()
        mock_parsed_message.parsed = mock_result

        mock_choice = MagicMock()
        mock_choice.message = mock_parsed_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_parse = MagicMock(return_value=mock_response)
        mock_completions = MagicMock()
        mock_completions.parse = mock_parse

        mock_beta = MagicMock()
        mock_beta.chat = MagicMock()
        mock_beta.chat.completions = mock_completions

        mock_openai_client = MagicMock()
        mock_openai_client.beta = mock_beta

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key-123"}):
            with patch(
                "openai.OpenAI", return_value=mock_openai_client
            ):
                results = extract_procurement_from_text(
                    text="PREGAO ELETRONICO N. 023/2026 Uniformes escolares R$ 450.000,00",
                    municipality="Sao Paulo",
                    uf="SP",
                    source_url="https://example.com",
                    gazette_date="2026-02-10",
                )

        assert len(results) == 1
        assert results[0].number == "023/2026"
        assert results[0].estimated_value == 450000.0
        assert results[0].modality == "Pregao Eletronico"

    def test_no_api_key_falls_back_to_regex(self):
        """No OPENAI_API_KEY -> falls back to regex extraction."""
        with patch.dict("os.environ", {}, clear=True):
            # Remove the key entirely
            import os
            saved = os.environ.pop("OPENAI_API_KEY", None)
            try:
                results = extract_procurement_from_text(
                    text=(
                        "PREGAO ELETRONICO N. 001/2026\n"
                        "OBJETO: Uniformes escolares. R$ 50.000,00"
                    ),
                    municipality="Sao Paulo",
                    uf="SP",
                    source_url="https://example.com",
                    gazette_date="2026-02-10",
                )
                # Should return results from regex fallback
                assert isinstance(results, list)
                if results:
                    assert all(r.extraction_confidence == 0.3 for r in results)
            finally:
                if saved is not None:
                    os.environ["OPENAI_API_KEY"] = saved

    def test_llm_error_falls_back_to_regex(self):
        """LLM API error -> falls back to regex extraction."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key-123"}):
            with patch(
                "openai.OpenAI",
                side_effect=Exception("API connection error"),
            ):
                results = extract_procurement_from_text(
                    text=(
                        "PREGAO ELETRONICO N. 001/2026\n"
                        "OBJETO: Fardamentos militares. R$ 80.000,00"
                    ),
                    municipality="Sao Paulo",
                    uf="SP",
                    source_url="https://example.com",
                    gazette_date="2026-02-10",
                )
                # Should fall back to regex
                assert isinstance(results, list)

    def test_to_unified_procurement(self):
        """Conversion of ExtractedProcurement to UnifiedProcurement."""
        extracted = ExtractedProcurement(
            modality="Pregao Eletronico",
            number="023/2026",
            object_description="Uniformes escolares",
            estimated_value=450000.0,
            opening_date="2026-02-28",
            agency_name="Prefeitura de Sao Paulo",
            municipality="Sao Paulo",
            uf="SP",
            source_url="https://example.com",
            gazette_date="2026-02-10",
            extraction_confidence=0.85,
            raw_excerpt="Pregao para uniformes...",
        )

        unified = to_unified_procurement(extracted, "gazette-001")

        assert unified.source_name == "QUERIDO_DIARIO"
        assert unified.esfera == "M"
        assert unified.valor_estimado == 450000.0
        assert unified.municipio == "Sao Paulo"
        assert unified.uf == "SP"
        assert unified.modalidade == "Pregao Eletronico"
        assert unified.numero_edital == "023/2026"
        assert unified.orgao == "Prefeitura de Sao Paulo"
        assert unified.objeto == "Uniformes escolares"
        assert unified.link_edital == "https://example.com"
        assert unified.link_portal == "https://example.com"
        assert "QD-gazette-001" in unified.source_id
        assert unified.data_publicacao is not None
        assert unified.data_publicacao.year == 2026
        assert unified.data_publicacao.month == 2
        assert unified.data_publicacao.day == 10
        assert unified.data_abertura is not None
        assert unified.data_abertura.year == 2026
        assert unified.data_abertura.month == 2
        assert unified.data_abertura.day == 28

    def test_to_unified_procurement_minimal(self):
        """Conversion with minimal fields (no value, no number, no dates)."""
        extracted = ExtractedProcurement(
            object_description="Servicos gerais",
            municipality="Campinas",
            uf="SP",
            source_url="https://example.com",
            gazette_date="invalid-date",
        )

        unified = to_unified_procurement(extracted, "gazette-002")

        assert unified.source_name == "QUERIDO_DIARIO"
        assert unified.esfera == "M"
        assert unified.valor_estimado == 0.0
        assert unified.municipio == "Campinas"
        assert unified.numero_edital == ""
        assert unified.modalidade == ""
        assert unified.orgao == ""
        assert unified.data_publicacao is None  # Invalid date not parsed

    def test_to_unified_procurement_source_id_format(self):
        """Source ID follows QD-{gazette_id}-{number} format."""
        extracted = ExtractedProcurement(
            number="045/2026",
            object_description="Materiais",
            municipality="Sao Paulo",
            uf="SP",
            source_url="",
            gazette_date="2026-01-01",
        )

        unified = to_unified_procurement(extracted, "g123")
        assert unified.source_id == "QD-g123-045/2026"

    def test_to_unified_procurement_unknown_number(self):
        """No procurement number -> 'unknown' in source_id."""
        extracted = ExtractedProcurement(
            object_description="Materiais diversos",
            municipality="Sao Paulo",
            uf="SP",
            source_url="",
            gazette_date="2026-01-01",
        )

        unified = to_unified_procurement(extracted, "g456")
        assert unified.source_id == "QD-g456-unknown"


# ------------------------------------------------------------------ #
# TestBatchExtraction (AC19)
# ------------------------------------------------------------------ #


class TestBatchExtraction:
    """Tests for batch_extract_from_gazettes."""

    @pytest.mark.asyncio
    async def test_batch_max_10_gazettes(self):
        """Only first 10 gazettes processed even if more provided."""
        gazettes = [
            {
                "txt_url": f"https://example.com/{i}.txt",
                "territory_name": "Sao Paulo",
                "state_code": "SP",
                "date": "2026-02-10",
                "id": f"gazette-{i}",
            }
            for i in range(15)
        ]

        call_count = 0

        async def mock_fetch(url: str) -> str:
            nonlocal call_count
            call_count += 1
            return (
                "PREGAO ELETRONICO N. 001/2026\n"
                "OBJETO: Uniformes escolares. R$ 50.000,00"
            )

        # Use regex fallback (no OPENAI_API_KEY)
        import os
        saved = os.environ.pop("OPENAI_API_KEY", None)
        try:
            results = await batch_extract_from_gazettes(gazettes, mock_fetch)
        finally:
            if saved is not None:
                os.environ["OPENAI_API_KEY"] = saved

        # Should only fetch text for 10 gazettes (DEFAULT_MAX_GAZETTES)
        assert call_count == 10

    @pytest.mark.asyncio
    async def test_batch_fallback_on_llm_error(self):
        """Regex fallback used when LLM fails."""
        gazettes = [
            {
                "txt_url": "https://example.com/1.txt",
                "territory_name": "Sao Paulo",
                "state_code": "SP",
                "date": "2026-02-10",
                "id": "gazette-1",
            }
        ]

        async def mock_fetch(url: str) -> str:
            return (
                "PREGAO ELETRONICO N. 042/2026\n"
                "OBJETO: Aquisicao de fardamentos. R$ 100.000,00"
            )

        # Force LLM to fail by setting key but making OpenAI raise
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch(
                "openai.OpenAI",
                side_effect=Exception("LLM unavailable"),
            ):
                results = await batch_extract_from_gazettes(
                    gazettes, mock_fetch
                )

        # Should still get results from regex fallback
        assert isinstance(results, list)
        assert len(results) >= 1
        assert results[0].source_name == "QUERIDO_DIARIO"

    @pytest.mark.asyncio
    async def test_batch_skips_empty_text(self):
        """Gazettes with empty/short text are skipped."""
        gazettes = [
            {
                "txt_url": "https://example.com/1.txt",
                "territory_name": "Sao Paulo",
                "state_code": "SP",
                "date": "2026-02-10",
                "id": "gazette-1",
            }
        ]

        async def mock_fetch(url: str) -> str:
            return ""  # Empty text

        import os
        saved = os.environ.pop("OPENAI_API_KEY", None)
        try:
            results = await batch_extract_from_gazettes(gazettes, mock_fetch)
        finally:
            if saved is not None:
                os.environ["OPENAI_API_KEY"] = saved

        assert results == []

    @pytest.mark.asyncio
    async def test_batch_skips_no_txt_url(self):
        """Gazettes without txt_url are skipped."""
        gazettes = [
            {
                "territory_name": "Sao Paulo",
                "state_code": "SP",
                "date": "2026-02-10",
                "id": "gazette-1",
                # No txt_url
            }
        ]

        async def mock_fetch(url: str) -> str:
            return "should not be called"

        import os
        saved = os.environ.pop("OPENAI_API_KEY", None)
        try:
            results = await batch_extract_from_gazettes(gazettes, mock_fetch)
        finally:
            if saved is not None:
                os.environ["OPENAI_API_KEY"] = saved

        assert results == []

    @pytest.mark.asyncio
    async def test_batch_continues_on_individual_failure(self):
        """One gazette failure does not block remaining gazettes."""
        gazettes = [
            {
                "txt_url": "https://example.com/1.txt",
                "territory_name": "Sao Paulo",
                "state_code": "SP",
                "date": "2026-02-10",
                "id": "gazette-1",
            },
            {
                "txt_url": "https://example.com/2.txt",
                "territory_name": "Campinas",
                "state_code": "SP",
                "date": "2026-02-10",
                "id": "gazette-2",
            },
        ]

        call_count = 0

        async def mock_fetch(url: str) -> str:
            nonlocal call_count
            call_count += 1
            if "1.txt" in url:
                raise ConnectionError("Network failure")
            return (
                "PREGAO ELETRONICO N. 099/2026\n"
                "OBJETO: Material de escritorio. R$ 30.000,00"
            )

        import os
        saved = os.environ.pop("OPENAI_API_KEY", None)
        try:
            results = await batch_extract_from_gazettes(gazettes, mock_fetch)
        finally:
            if saved is not None:
                os.environ["OPENAI_API_KEY"] = saved

        # Second gazette should still be processed
        assert call_count == 2
        assert len(results) >= 1


# ------------------------------------------------------------------ #
# TestResourceManagement
# ------------------------------------------------------------------ #


class TestResourceManagement:
    """Tests for context manager and resource cleanup."""

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Async context manager closes client on exit."""
        async with QueridoDiarioClient(timeout=5) as client:
            assert client._client is None  # Lazy initialization

    @pytest.mark.asyncio
    async def test_close_with_active_client(self, adapter):
        """Close properly shuts down an active HTTP client."""
        mock_client = AsyncMock()
        mock_client.is_closed = False
        adapter._client = mock_client

        await adapter.close()

        mock_client.aclose.assert_called_once()
        assert adapter._client is None

    @pytest.mark.asyncio
    async def test_close_without_client(self, adapter):
        """Close when no client exists does not raise."""
        adapter._client = None
        await adapter.close()  # Should not raise


# ------------------------------------------------------------------ #
# TestIntegration (AC21)
# ------------------------------------------------------------------ #


class TestIntegration:
    """Integration tests with real Querido Diario API."""

    pytestmark = [
        pytest.mark.integration,
        pytest.mark.asyncio,
    ]

    async def test_real_search_licitacao_uniforme(self):
        """AC21: Integration test with real QD API."""
        async with QueridoDiarioClient() as client:
            response = await client.search_gazettes(
                query="licitacao + uniforme",
                since="2026-01-01",
                until="2026-02-14",
                size=5,
            )

            assert "total_gazettes" in response
            assert "gazettes" in response
            assert isinstance(response["gazettes"], list)

            # May or may not find results depending on API state
            if response["total_gazettes"] > 0:
                gazette = response["gazettes"][0]
                assert "territory_id" in gazette
                assert "state_code" in gazette
                assert "date" in gazette

    async def test_real_health_check(self):
        """Integration: health check returns AVAILABLE or DEGRADED."""
        async with QueridoDiarioClient() as client:
            status = await client.health_check()
            assert status in (SourceStatus.AVAILABLE, SourceStatus.DEGRADED)

    async def test_real_build_and_search(self):
        """Integration: build querystring then search."""
        qs = QueridoDiarioClient.build_querystring({"uniforme"})
        async with QueridoDiarioClient() as client:
            response = await client.search_gazettes(
                query=qs,
                since="2026-01-01",
                until="2026-02-14",
                size=3,
            )
            assert isinstance(response, dict)
            assert "total_gazettes" in response
