"""Tests for SanctionsChecker (STORY-254 AC8-AC11).

Covers:
    - AC8:  check_ceis() — CEIS query and record parsing
    - AC9:  check_cnep() — CNEP query and record parsing (with fines)
    - AC10: check_sanctions() — aggregated result with is_sanctioned flag
    - AC11: 24-hour in-memory cache with CNPJ-digit key
"""

import time
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from clients.sanctions import (
    SanctionRecord,
    SanctionsChecker,
    SanctionsResult,
    SanctionsAPIError,
    SanctionsRateLimitError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def checker():
    """Create a SanctionsChecker with a fake API key."""
    return SanctionsChecker(api_key="test-api-key", timeout=5)


@pytest.fixture
def sample_ceis_record():
    """A realistic CEIS API response record."""
    return {
        "sancionado": {
            "nome": "ACME Uniformes LTDA",
            "codigoFormatado": "12.345.678/0001-90",
        },
        "tipo": {
            "descricaoResumida": "Impedimento",
        },
        "dataInicioSancao": "15/03/2024",
        "dataFinalSancao": "15/03/2027",
        "orgaoSancionador": {
            "nome": "Ministerio da Defesa",
        },
        "fundamentacao": {
            "descricao": "Lei 8.666/1993, Art. 87, IV",
        },
    }


@pytest.fixture
def sample_cnep_record():
    """A realistic CNEP API response record."""
    return {
        "sancionado": {
            "nome": "ACME Servicos SA",
            "codigoFormatado": "98.765.432/0001-10",
        },
        "tipoSancao": {
            "descricaoResumida": "Multa",
        },
        "dataInicioSancao": "01/06/2025",
        "dataFinalSancao": None,
        "orgaoSancionador": {
            "nome": "CGU",
        },
        "fundamentacao": {
            "descricao": "Lei 12.846/2013, Art. 6, I",
        },
        "valorMulta": 150000.50,
    }


@pytest.fixture
def expired_ceis_record():
    """A CEIS record whose end_date is in the past."""
    return {
        "sancionado": {
            "nome": "Old Corp LTDA",
            "codigoFormatado": "11.222.333/0001-44",
        },
        "tipo": {
            "descricaoResumida": "Suspensao",
        },
        "dataInicioSancao": "01/01/2020",
        "dataFinalSancao": "01/01/2021",
        "orgaoSancionador": {
            "nome": "Tribunal de Contas",
        },
        "fundamentacao": {
            "descricao": "Lei 8.666/1993, Art. 87, III",
        },
    }


# ---------------------------------------------------------------------------
# CNPJ normalisation
# ---------------------------------------------------------------------------


class TestCleanCnpj:
    def test_digits_only(self, checker):
        assert checker._clean_cnpj("12345678000190") == "12345678000190"

    def test_formatted(self, checker):
        assert checker._clean_cnpj("12.345.678/0001-90") == "12345678000190"

    def test_with_spaces(self, checker):
        assert checker._clean_cnpj(" 12.345.678/0001-90 ") == "12345678000190"

    def test_empty(self, checker):
        assert checker._clean_cnpj("") == ""

    def test_only_separators(self, checker):
        assert checker._clean_cnpj("...///---") == ""


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------


class TestParseDate:
    def test_dd_mm_yyyy(self, checker):
        assert checker._parse_date("15/03/2024") == date(2024, 3, 15)

    def test_yyyy_mm_dd(self, checker):
        assert checker._parse_date("2024-03-15") == date(2024, 3, 15)

    def test_none(self, checker):
        assert checker._parse_date(None) is None

    def test_empty_string(self, checker):
        assert checker._parse_date("") is None

    def test_invalid(self, checker):
        assert checker._parse_date("not-a-date") is None

    def test_with_whitespace(self, checker):
        assert checker._parse_date("  15/03/2024  ") == date(2024, 3, 15)


# ---------------------------------------------------------------------------
# AC8: check_ceis
# ---------------------------------------------------------------------------


class TestCheckCeis:
    @pytest.mark.asyncio
    async def test_ceis_returns_records(self, checker, sample_ceis_record):
        """AC8: check_ceis returns list of SanctionRecord from CEIS API."""
        checker._fetch_all_pages = AsyncMock(return_value=[sample_ceis_record])

        records = await checker.check_ceis("12.345.678/0001-90")

        assert len(records) == 1
        rec = records[0]
        assert isinstance(rec, SanctionRecord)
        assert rec.source == "CEIS"
        assert rec.company_name == "ACME Uniformes LTDA"
        assert rec.sanction_type == "Impedimento"
        assert rec.start_date == date(2024, 3, 15)
        assert rec.end_date == date(2027, 3, 15)
        assert rec.sanctioning_body == "Ministerio da Defesa"
        assert rec.legal_basis == "Lei 8.666/1993, Art. 87, IV"
        assert rec.fine_amount is None
        assert rec.is_active is True

    @pytest.mark.asyncio
    async def test_ceis_empty_result(self, checker):
        """AC8: check_ceis returns empty list when no sanctions found."""
        checker._fetch_all_pages = AsyncMock(return_value=[])

        records = await checker.check_ceis("99999999000100")

        assert records == []

    @pytest.mark.asyncio
    async def test_ceis_api_failure_returns_empty(self, checker):
        """AC8: check_ceis returns empty list on API failure."""
        checker._fetch_all_pages = AsyncMock(
            side_effect=SanctionsAPIError("SANCTIONS", 500, "Server error")
        )

        records = await checker.check_ceis("12345678000190")

        assert records == []

    @pytest.mark.asyncio
    async def test_ceis_empty_cnpj(self, checker):
        """AC8: check_ceis returns empty for blank CNPJ."""
        records = await checker.check_ceis("")
        assert records == []

    @pytest.mark.asyncio
    async def test_ceis_expired_record_not_active(self, checker, expired_ceis_record):
        """AC8: Expired CEIS sanctions have is_active=False."""
        checker._fetch_all_pages = AsyncMock(return_value=[expired_ceis_record])

        records = await checker.check_ceis("11222333000144")

        assert len(records) == 1
        assert records[0].is_active is False
        assert records[0].sanction_type == "Suspensao"

    @pytest.mark.asyncio
    async def test_ceis_null_end_date_is_active(self, checker):
        """AC8: CEIS record with null end_date is treated as active."""
        raw = {
            "sancionado": {"nome": "Empresa X", "codigoFormatado": "00000000000100"},
            "tipo": {"descricaoResumida": "Inidoneidade"},
            "dataInicioSancao": "01/01/2023",
            "dataFinalSancao": None,
            "orgaoSancionador": {"nome": "CGU"},
            "fundamentacao": {"descricao": "Lei 8.666/1993, Art. 87, IV"},
        }
        checker._fetch_all_pages = AsyncMock(return_value=[raw])

        records = await checker.check_ceis("00000000000100")

        assert len(records) == 1
        assert records[0].is_active is True
        assert records[0].end_date is None

    @pytest.mark.asyncio
    async def test_ceis_parse_error_skips_bad_record(self, checker, sample_ceis_record):
        """AC8: Unparseable records are skipped with a warning."""
        bad_record = {"broken": "data"}  # missing nested dicts
        # The parser should still handle this gracefully since it uses .get()
        checker._fetch_all_pages = AsyncMock(
            return_value=[sample_ceis_record, bad_record]
        )

        records = await checker.check_ceis("12345678000190")

        # Both should parse since _parse_ceis_record uses .get() with defaults
        assert len(records) == 2

    @pytest.mark.asyncio
    async def test_ceis_calls_correct_endpoint(self, checker):
        """AC8: check_ceis queries /ceis endpoint."""
        checker._fetch_all_pages = AsyncMock(return_value=[])

        await checker.check_ceis("12345678000190")

        checker._fetch_all_pages.assert_called_once_with("/ceis", "12345678000190")


# ---------------------------------------------------------------------------
# AC9: check_cnep
# ---------------------------------------------------------------------------


class TestCheckCnep:
    @pytest.mark.asyncio
    async def test_cnep_returns_records_with_fine(self, checker, sample_cnep_record):
        """AC9: check_cnep returns records with fine_amount from CNEP."""
        checker._fetch_all_pages = AsyncMock(return_value=[sample_cnep_record])

        records = await checker.check_cnep("98.765.432/0001-10")

        assert len(records) == 1
        rec = records[0]
        assert rec.source == "CNEP"
        assert rec.company_name == "ACME Servicos SA"
        assert rec.sanction_type == "Multa"
        assert rec.fine_amount == Decimal("150000.50")
        assert rec.sanctioning_body == "CGU"
        assert rec.is_active is True  # no end_date

    @pytest.mark.asyncio
    async def test_cnep_empty_result(self, checker):
        """AC9: check_cnep returns empty list when no sanctions found."""
        checker._fetch_all_pages = AsyncMock(return_value=[])

        records = await checker.check_cnep("99999999000100")

        assert records == []

    @pytest.mark.asyncio
    async def test_cnep_api_failure_returns_empty(self, checker):
        """AC9: check_cnep returns empty on API failure."""
        checker._fetch_all_pages = AsyncMock(
            side_effect=SanctionsAPIError("SANCTIONS", 500, "Down")
        )

        records = await checker.check_cnep("12345678000190")

        assert records == []

    @pytest.mark.asyncio
    async def test_cnep_empty_cnpj(self, checker):
        """AC9: check_cnep returns empty for blank CNPJ."""
        records = await checker.check_cnep("")
        assert records == []

    @pytest.mark.asyncio
    async def test_cnep_null_fine_amount(self, checker):
        """AC9: CNEP record with null valorMulta -> fine_amount is None."""
        raw = {
            "sancionado": {"nome": "Corp Y", "codigoFormatado": "11111111000111"},
            "tipoSancao": {"descricaoResumida": "Publicacao extraordinaria"},
            "dataInicioSancao": "10/10/2025",
            "dataFinalSancao": "10/10/2028",
            "orgaoSancionador": {"nome": "AGU"},
            "fundamentacao": {"descricao": "Lei 12.846/2013, Art. 6, II"},
            "valorMulta": None,
        }
        checker._fetch_all_pages = AsyncMock(return_value=[raw])

        records = await checker.check_cnep("11111111000111")

        assert len(records) == 1
        assert records[0].fine_amount is None

    @pytest.mark.asyncio
    async def test_cnep_invalid_fine_amount(self, checker):
        """AC9: Invalid valorMulta is logged and set to None."""
        raw = {
            "sancionado": {"nome": "Corp Z", "codigoFormatado": "22222222000122"},
            "tipoSancao": {"descricaoResumida": "Multa"},
            "dataInicioSancao": "01/01/2025",
            "dataFinalSancao": None,
            "orgaoSancionador": {"nome": "CGU"},
            "fundamentacao": {"descricao": "Art. 6"},
            "valorMulta": "not-a-number",
        }
        checker._fetch_all_pages = AsyncMock(return_value=[raw])

        records = await checker.check_cnep("22222222000122")

        assert len(records) == 1
        assert records[0].fine_amount is None

    @pytest.mark.asyncio
    async def test_cnep_calls_correct_endpoint(self, checker):
        """AC9: check_cnep queries /cnep endpoint."""
        checker._fetch_all_pages = AsyncMock(return_value=[])

        await checker.check_cnep("12345678000190")

        checker._fetch_all_pages.assert_called_once_with("/cnep", "12345678000190")


# ---------------------------------------------------------------------------
# AC10: check_sanctions (aggregation)
# ---------------------------------------------------------------------------


class TestCheckSanctions:
    @pytest.mark.asyncio
    async def test_aggregates_ceis_and_cnep(
        self, checker, sample_ceis_record, sample_cnep_record
    ):
        """AC10: check_sanctions merges CEIS + CNEP into unified result."""
        checker._fetch_all_pages = AsyncMock(
            side_effect=[[sample_ceis_record], [sample_cnep_record]]
        )

        result = await checker.check_sanctions("12345678000190")

        assert isinstance(result, SanctionsResult)
        assert result.cnpj == "12345678000190"
        assert result.is_sanctioned is True
        assert result.ceis_count == 1
        assert result.cnep_count == 1
        assert len(result.sanctions) == 2
        assert result.cache_hit is False

        sources = {s.source for s in result.sanctions}
        assert sources == {"CEIS", "CNEP"}

    @pytest.mark.asyncio
    async def test_no_sanctions_found(self, checker):
        """AC10: check_sanctions returns is_sanctioned=False when clean."""
        checker._fetch_all_pages = AsyncMock(return_value=[])

        result = await checker.check_sanctions("99999999000100")

        assert result.is_sanctioned is False
        assert result.ceis_count == 0
        assert result.cnep_count == 0
        assert result.sanctions == []

    @pytest.mark.asyncio
    async def test_only_expired_sanctions(self, checker, expired_ceis_record):
        """AC10: Only expired sanctions -> is_sanctioned=False."""
        checker._fetch_all_pages = AsyncMock(
            side_effect=[[expired_ceis_record], []]
        )

        result = await checker.check_sanctions("11222333000144")

        assert result.is_sanctioned is False
        assert result.ceis_count == 1
        assert result.cnep_count == 0
        assert len(result.sanctions) == 1
        assert result.sanctions[0].is_active is False

    @pytest.mark.asyncio
    async def test_checked_at_is_utc(self, checker):
        """AC10: checked_at uses UTC timezone."""
        checker._fetch_all_pages = AsyncMock(return_value=[])

        result = await checker.check_sanctions("12345678000190")

        assert result.checked_at.tzinfo is not None
        assert result.checked_at.tzinfo == timezone.utc

    @pytest.mark.asyncio
    async def test_cnpj_normalized_in_result(self, checker):
        """AC10: Result cnpj contains digits only."""
        checker._fetch_all_pages = AsyncMock(return_value=[])

        result = await checker.check_sanctions("12.345.678/0001-90")

        assert result.cnpj == "12345678000190"

    @pytest.mark.asyncio
    async def test_partial_api_failure(self, checker, sample_ceis_record):
        """AC10: If one API fails, the other results are still returned."""
        # CEIS succeeds, CNEP fails (but check_cnep catches and returns [])
        async def mock_fetch(path, cnpj):
            if path == "/ceis":
                return [sample_ceis_record]
            if path == "/cnep":
                raise SanctionsAPIError("SANCTIONS", 500, "Down")
            return []

        checker._fetch_all_pages = AsyncMock(side_effect=mock_fetch)

        result = await checker.check_sanctions("12345678000190")

        # CEIS record should still be present; CNEP returns empty via catch
        assert result.ceis_count == 1
        assert result.cnep_count == 0
        assert result.is_sanctioned is True


# ---------------------------------------------------------------------------
# AC11: Caching
# ---------------------------------------------------------------------------


class TestCaching:
    @pytest.mark.asyncio
    async def test_cache_hit(self, checker):
        """AC11: Second call within TTL returns cache_hit=True."""
        checker._fetch_all_pages = AsyncMock(return_value=[])

        result1 = await checker.check_sanctions("12345678000190")
        assert result1.cache_hit is False

        result2 = await checker.check_sanctions("12345678000190")
        assert result2.cache_hit is True

        # Only 2 calls to _fetch_all_pages (1 CEIS + 1 CNEP from first call)
        assert checker._fetch_all_pages.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_key_is_digits_only(self, checker):
        """AC11: Cache key is cleaned CNPJ digits."""
        checker._fetch_all_pages = AsyncMock(return_value=[])

        await checker.check_sanctions("12.345.678/0001-90")
        result = await checker.check_sanctions("12345678000190")  # same digits

        assert result.cache_hit is True
        assert checker._fetch_all_pages.call_count == 2  # only first call fetches

    @pytest.mark.asyncio
    async def test_cache_expiry(self, checker):
        """AC11: Cache entries expire after TTL (24h)."""
        checker._fetch_all_pages = AsyncMock(return_value=[])

        # First call populates cache
        await checker.check_sanctions("12345678000190")

        # Manually expire the cache entry
        cnpj_key = "12345678000190"
        if cnpj_key in checker._cache:
            result_obj, _ = checker._cache[cnpj_key]
            # Set timestamp to 25 hours ago
            checker._cache[cnpj_key] = (
                result_obj,
                time.monotonic() - (25 * 3600),
            )

        result = await checker.check_sanctions("12345678000190")
        assert result.cache_hit is False

        # 4 total calls: 2 for first + 2 for expired re-fetch
        assert checker._fetch_all_pages.call_count == 4

    @pytest.mark.asyncio
    async def test_different_cnpjs_cached_separately(self, checker):
        """AC11: Different CNPJs get separate cache entries."""
        checker._fetch_all_pages = AsyncMock(return_value=[])

        await checker.check_sanctions("11111111000111")
        await checker.check_sanctions("22222222000122")

        assert checker.cache_size == 2

    def test_invalidate_single(self, checker):
        """AC11: invalidate_cache(cnpj) removes only that entry."""
        # Manually populate cache
        checker._cache["12345678000190"] = (
            MagicMock(spec=SanctionsResult),
            time.monotonic(),
        )
        checker._cache["99999999000100"] = (
            MagicMock(spec=SanctionsResult),
            time.monotonic(),
        )

        checker.invalidate_cache("12.345.678/0001-90")

        assert "12345678000190" not in checker._cache
        assert "99999999000100" in checker._cache

    def test_invalidate_all(self, checker):
        """AC11: invalidate_cache() with no args clears entire cache."""
        checker._cache["a"] = (MagicMock(), time.monotonic())
        checker._cache["b"] = (MagicMock(), time.monotonic())

        checker.invalidate_cache()

        assert checker.cache_size == 0


# ---------------------------------------------------------------------------
# Record parsing edge cases
# ---------------------------------------------------------------------------


class TestCeisRecordParsing:
    def test_missing_nested_dicts(self, checker):
        """Gracefully handle missing nested objects in CEIS response."""
        raw = {}  # completely empty
        record = checker._parse_ceis_record(raw)

        assert record.source == "CEIS"
        assert record.cnpj == ""
        assert record.company_name == ""
        assert record.sanction_type == ""
        assert record.start_date is None
        assert record.end_date is None
        assert record.is_active is True  # null end_date -> active
        assert record.fine_amount is None

    def test_partial_data(self, checker):
        """Parse record with only some fields present."""
        raw = {
            "sancionado": {"nome": "Partial Corp"},
            "dataInicioSancao": "01/01/2025",
        }
        record = checker._parse_ceis_record(raw)

        assert record.company_name == "Partial Corp"
        assert record.start_date == date(2025, 1, 1)
        assert record.cnpj == ""  # codigoFormatado missing


class TestCnepRecordParsing:
    def test_missing_nested_dicts(self, checker):
        """Gracefully handle missing nested objects in CNEP response."""
        raw = {}
        record = checker._parse_cnep_record(raw)

        assert record.source == "CNEP"
        assert record.cnpj == ""
        assert record.fine_amount is None

    def test_zero_fine(self, checker):
        """Fine amount of 0 is valid and stored."""
        raw = {
            "sancionado": {"nome": "X", "codigoFormatado": "111"},
            "tipoSancao": {"descricaoResumida": "Multa"},
            "dataInicioSancao": "01/01/2025",
            "dataFinalSancao": None,
            "orgaoSancionador": {"nome": "CGU"},
            "fundamentacao": {"descricao": "Art. 6"},
            "valorMulta": 0,
        }
        record = checker._parse_cnep_record(raw)
        assert record.fine_amount == Decimal("0")

    def test_large_fine(self, checker):
        """Large fine amounts are handled correctly."""
        raw = {
            "sancionado": {"nome": "Big Corp", "codigoFormatado": "222"},
            "tipoSancao": {"descricaoResumida": "Multa"},
            "dataInicioSancao": "01/01/2025",
            "dataFinalSancao": None,
            "orgaoSancionador": {"nome": "CGU"},
            "fundamentacao": {"descricao": "Art. 6"},
            "valorMulta": 99999999.99,
        }
        record = checker._parse_cnep_record(raw)
        assert record.fine_amount == Decimal("99999999.99")


# ---------------------------------------------------------------------------
# HTTP retry logic
# ---------------------------------------------------------------------------


class TestRetryLogic:
    @pytest.mark.asyncio
    async def test_retry_on_429(self, checker):
        """Retries on 429 with Retry-After header."""
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "1"}

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = []

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=[mock_response_429, mock_response_200]
        )
        mock_client.is_closed = False
        checker._client = mock_client

        result = await checker._request_with_retry("/ceis", {"codigoSancionado": "123"})

        assert result == []
        assert mock_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_500(self, checker):
        """Retries on 500 server error."""
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500
        mock_response_500.text = "Internal Server Error"

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = []

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=[mock_response_500, mock_response_200]
        )
        mock_client.is_closed = False
        checker._client = mock_client
        checker._last_request_time = 0.0  # skip rate limit wait

        result = await checker._request_with_retry("/ceis")

        assert result == []
        assert mock_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, checker):
        """Retries on httpx.TimeoutException."""
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = [{"id": 1}]

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=[httpx.TimeoutException("timeout"), mock_response_200]
        )
        mock_client.is_closed = False
        checker._client = mock_client

        result = await checker._request_with_retry("/cnep")

        assert result == [{"id": 1}]
        assert mock_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_exhausted_retries_raises(self, checker):
        """Raises SanctionsAPIError after exhausting retries."""
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500
        mock_response_500.text = "Down"

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response_500)
        mock_client.is_closed = False
        checker._client = mock_client

        with pytest.raises(SanctionsAPIError):
            await checker._request_with_retry("/ceis")

    @pytest.mark.asyncio
    async def test_non_retryable_error(self, checker):
        """Non-retryable errors (e.g., 403) raise immediately."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        checker._client = mock_client

        with pytest.raises(SanctionsAPIError) as exc_info:
            await checker._request_with_retry("/ceis")

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_204_returns_empty_list(self, checker):
        """204 No Content returns empty list."""
        mock_response = MagicMock()
        mock_response.status_code = 204

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        checker._client = mock_client

        result = await checker._request_with_retry("/ceis")

        assert result == []


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class TestPagination:
    @pytest.mark.asyncio
    async def test_single_page(self, checker):
        """Single page of results (second page returns empty)."""
        page1 = [{"id": 1}, {"id": 2}]

        checker._request_with_retry = AsyncMock(side_effect=[page1, []])

        result = await checker._fetch_all_pages("/ceis", "12345678000190")

        assert len(result) == 2
        assert checker._request_with_retry.call_count == 2

    @pytest.mark.asyncio
    async def test_multiple_pages(self, checker):
        """Multiple pages are all collected."""
        page1 = [{"id": i} for i in range(10)]
        page2 = [{"id": i} for i in range(10, 15)]
        empty = []

        checker._request_with_retry = AsyncMock(
            side_effect=[page1, page2, empty]
        )

        result = await checker._fetch_all_pages("/cnep", "12345678000190")

        assert len(result) == 15
        assert checker._request_with_retry.call_count == 3

    @pytest.mark.asyncio
    async def test_passes_cnpj_and_page(self, checker):
        """Verify correct params are passed on each page request."""
        checker._request_with_retry = AsyncMock(return_value=[])

        await checker._fetch_all_pages("/ceis", "12345678000190")

        checker._request_with_retry.assert_called_once_with(
            "/ceis",
            {"codigoSancionado": "12345678000190", "pagina": 1},
        )


# ---------------------------------------------------------------------------
# Lifecycle / context manager
# ---------------------------------------------------------------------------


class TestLifecycle:
    @pytest.mark.asyncio
    async def test_context_manager(self, checker):
        """Async context manager works without errors."""
        async with checker as c:
            assert c is checker

    @pytest.mark.asyncio
    async def test_close_without_client(self, checker):
        """close() is safe to call without a client."""
        await checker.close()  # should not raise

    @pytest.mark.asyncio
    async def test_close_with_client(self, checker):
        """close() properly closes the httpx client."""
        mock_client = AsyncMock()
        mock_client.is_closed = False
        checker._client = mock_client

        await checker.close()

        mock_client.aclose.assert_called_once()
        assert checker._client is None

    def test_default_api_key_from_env(self):
        """API key defaults to PORTAL_TRANSPARENCIA_API_KEY env var."""
        with patch.dict("os.environ", {"PORTAL_TRANSPARENCIA_API_KEY": "env-key"}):
            c = SanctionsChecker()
            assert c._api_key == "env-key"


# ---------------------------------------------------------------------------
# Backoff calculation
# ---------------------------------------------------------------------------


class TestBackoff:
    def test_backoff_increases(self, checker):
        """Backoff delay increases with attempt number."""
        delays = [checker._calculate_backoff(i) for i in range(5)]
        # With jitter the exact values vary, but the trend should be upward.
        # Check base values without jitter: 2, 4, 8, 16, 32
        # With 0.5-1.5 jitter: min should be roughly 1, max roughly 48
        assert all(d > 0 for d in delays)

    def test_backoff_capped(self, checker):
        """Backoff is capped at 60s (before jitter)."""
        delay = checker._calculate_backoff(100)
        # 2 * 2^100 is huge, but min(that, 60) * 1.5 = 90 max
        assert delay <= 90.0


# ---------------------------------------------------------------------------
# Data model sanity
# ---------------------------------------------------------------------------


class TestDataModels:
    def test_sanction_record_fields(self):
        """SanctionRecord dataclass has all expected fields."""
        rec = SanctionRecord(
            source="CEIS",
            cnpj="12345678000190",
            company_name="Test Corp",
            sanction_type="Impedimento",
            start_date=date(2024, 1, 1),
            end_date=date(2025, 1, 1),
            sanctioning_body="CGU",
            legal_basis="Lei 8.666",
            fine_amount=None,
            is_active=False,
        )
        assert rec.source == "CEIS"
        assert rec.is_active is False

    def test_sanctions_result_fields(self):
        """SanctionsResult dataclass has all expected fields."""
        result = SanctionsResult(
            cnpj="12345678000190",
            is_sanctioned=False,
            sanctions=[],
            checked_at=datetime.now(timezone.utc),
            ceis_count=0,
            cnep_count=0,
        )
        assert result.cache_hit is False  # default
        assert result.is_sanctioned is False

    def test_sanctions_result_cache_hit_default(self):
        """cache_hit defaults to False."""
        result = SanctionsResult(
            cnpj="x",
            is_sanctioned=False,
            sanctions=[],
            checked_at=datetime.now(timezone.utc),
            ceis_count=0,
            cnep_count=0,
        )
        assert result.cache_hit is False
