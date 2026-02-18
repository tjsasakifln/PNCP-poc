"""GTM-FIX-032 AC7: Tests for PNCP 422 date validation and recovery.

Tests cover:
- AC2: Pre-flight date validation (_validate_date_params)
- AC2: Auto-swap of swapped dates
- AC4: Graceful 422 recovery (_handle_422_response)
- AC4: Circuit breaker NOT triggered on 422
- AC3: Pipeline date normalization (stage_prepare)
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import date, datetime, timezone, timedelta

from pncp_client import (
    _validate_date_params,
    _handle_422_response,
    AsyncPNCPClient,
)
from exceptions import PNCPAPIError


# ============================================================================
# AC2: Pre-flight date validation
# ============================================================================

class TestValidateDateParams:
    """AC7.1-AC7.3: Pre-flight date validation."""

    def test_valid_dates_pass(self):
        """AC7.1: Valid dates produce correct 8-digit format."""
        # Should not raise
        _validate_date_params("2026-02-08", "20260208", "2026-02-18", "20260218")

    def test_swapped_dates_detected_by_caller(self):
        """AC7.2: Validation itself doesn't swap — caller handles swap."""
        # _validate_date_params only checks format, not ordering
        # Swap detection is in fetch_page / _fetch_page_async
        _validate_date_params("2026-02-18", "20260218", "2026-02-08", "20260208")

    def test_malformed_data_inicial_raises(self):
        """AC7.3: Malformed data_inicial raises ValueError."""
        with pytest.raises(ValueError, match="Malformed data_inicial"):
            _validate_date_params("2026-2-8", "202628", "2026-02-18", "20260218")

    def test_malformed_data_final_raises(self):
        """AC7.3: Malformed data_final raises ValueError."""
        with pytest.raises(ValueError, match="Malformed data_final"):
            _validate_date_params("2026-02-08", "20260208", "2026-2-18", "2026218")

    def test_non_digit_data_inicial_raises(self):
        """AC7.3: Non-digit characters in formatted date raise ValueError."""
        with pytest.raises(ValueError, match="Malformed data_inicial"):
            _validate_date_params("abcd-ef-gh", "abcdefgh", "2026-02-18", "20260218")

    def test_non_digit_data_final_raises(self):
        """AC7.3: Non-digit characters in data_final raise ValueError."""
        with pytest.raises(ValueError, match="Malformed data_final"):
            _validate_date_params("2026-02-08", "20260208", "abcd-ef-gh", "abcdefgh")


# ============================================================================
# AC4: 422 Response Handling
# ============================================================================

class TestHandle422Response:
    """AC7.4-AC7.7: 422 response handling."""

    PARAMS = {
        "uf": "SP",
        "codigoModalidadeContratacao": 6,
        "dataInicial": "20260208",
        "dataFinal": "20260218",
        "pagina": 1,
    }

    def test_first_attempt_returns_retry_format(self):
        """First 422 attempt returns 'retry_format' for format rotation (UX-336)."""
        result = _handle_422_response(
            '{"message":"some error"}', self.PARAMS,
            "2026-02-08", "2026-02-18", attempt=0, max_retries=1
        )
        assert result == "retry_format"

    def test_date_swap_message_returns_empty(self):
        """AC7.4: 422 with 'Data Inicial' message returns empty result."""
        result = _handle_422_response(
            '{"message":"Data Inicial deve ser anterior ou igual à Data Final"}',
            self.PARAMS, "2026-02-08", "2026-02-18", attempt=1, max_retries=1
        )
        assert isinstance(result, dict)
        assert result["data"] == []
        assert result["totalRegistros"] == 0

    def test_365_dias_message_returns_empty(self):
        """AC7.5: 422 with '365 dias' message returns empty result."""
        result = _handle_422_response(
            '{"message":"Período inicial e final maior que 365 dias."}',
            self.PARAMS, "2026-02-08", "2026-02-18", attempt=1, max_retries=1
        )
        assert isinstance(result, dict)
        assert result["data"] == []
        assert result["totalRegistros"] == 0

    def test_unknown_422_returns_raise(self):
        """AC7.6: 422 with unknown message returns 'raise'."""
        result = _handle_422_response(
            '{"message":"Algum erro desconhecido"}',
            self.PARAMS, "2026-02-08", "2026-02-18", attempt=1, max_retries=1
        )
        assert result == "raise"

    def test_empty_body_returns_raise(self):
        """Unknown 422 with empty body returns 'raise'."""
        result = _handle_422_response(
            "", self.PARAMS, "2026-02-08", "2026-02-18", attempt=1, max_retries=1
        )
        assert result == "raise"


# ============================================================================
# AC4: Async client integration — no circuit breaker on 422
# ============================================================================

class TestAsyncClient422NoCB:
    """AC7.7: 422 does NOT trigger circuit breaker."""

    @pytest.mark.asyncio
    async def test_422_date_error_no_circuit_breaker(self):
        """AC7.7: Date-related 422 should NOT trigger circuit breaker."""
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.text = '{"message":"Data Inicial deve ser anterior ou igual à Data Final"}'

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        client = AsyncPNCPClient.__new__(AsyncPNCPClient)
        client._client = mock_client
        client.config = MagicMock()
        client.config.max_retries = 5  # UX-336: enough for 4 format rotations
        client.config.base_delay = 0.001
        client.config.retryable_status_codes = {500, 502, 503}
        client.config.exponential_base = 2
        client.config.jitter = False
        client.config.max_delay = 1
        client.BASE_URL = "https://pncp.gov.br/api/consulta/v1"
        client._last_request_time = 0
        client._rate_limit = AsyncMock()

        with patch("pncp_client._circuit_breaker") as mock_cb:
            result = await client._fetch_page_async(
                "2026-02-08", "2026-02-18", 6, uf="SP"
            )
            # Should return empty dict, NOT raise (date_swap is a known 422 type)
            assert result["data"] == []
            assert result["totalRegistros"] == 0
            # Circuit breaker should NOT have been called
            mock_cb.record_failure.assert_not_called()

    @pytest.mark.asyncio
    async def test_422_unknown_raises_no_circuit_breaker(self):
        """Unknown 422 raises PNCPAPIError but still no circuit breaker."""
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.text = '{"message":"Unknown validation error"}'

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        client = AsyncPNCPClient.__new__(AsyncPNCPClient)
        client._client = mock_client
        client.config = MagicMock()
        client.config.max_retries = 5  # UX-336: enough for 4 format rotations
        client.config.base_delay = 0.001
        client.config.retryable_status_codes = {500, 502, 503}
        client.config.exponential_base = 2
        client.config.jitter = False
        client.config.max_delay = 1
        client.BASE_URL = "https://pncp.gov.br/api/consulta/v1"
        client._last_request_time = 0
        client._rate_limit = AsyncMock()

        with patch("pncp_client._circuit_breaker") as mock_cb:
            with pytest.raises(PNCPAPIError, match="Reduza o período"):
                await client._fetch_page_async(
                    "2026-02-08", "2026-02-18", 6, uf="SP"
                )
            mock_cb.record_failure.assert_not_called()


# ============================================================================
# AC3: Pipeline date normalization
# ============================================================================

class TestStagePrepareNormalization:
    """AC7.8-AC7.9: stage_prepare date handling."""

    @pytest.mark.asyncio
    async def test_abertas_mode_uses_utc(self):
        """AC7.8: stage_prepare abertas mode uses UTC date."""
        from search_pipeline import SearchPipeline

        # Mock a fixed UTC time: 2026-02-18 03:00 UTC (= 2026-02-18 00:00 BRT)
        fixed_now = datetime(2026, 2, 18, 3, 0, 0, tzinfo=timezone.utc)

        mock_request = MagicMock()
        mock_request.modo_busca = "abertas"
        mock_request.data_inicial = "2026-01-01"
        mock_request.data_final = "2026-01-10"
        mock_request.setor_id = "vestuario"
        mock_request.termos_busca = None
        mock_request.exclusion_terms = None
        mock_request.show_all_matches = False

        mock_ctx = MagicMock()
        mock_ctx.request = mock_request
        mock_ctx.tracker = None

        pipeline = SearchPipeline.__new__(SearchPipeline)
        pipeline.deps = MagicMock()

        with patch("search_pipeline.datetime") as mock_dt_module:
            # This won't work for deferred import — patch the right target
            pass

        # Use a more direct approach: mock at the deferred import level
        with patch("search_pipeline.get_sector") as mock_get_sector:
            mock_sector = MagicMock()
            mock_sector.name = "Vestuário"
            mock_sector.keywords = ["uniforme"]
            mock_sector.exclusions = set()
            mock_sector.context_required_keywords = None
            mock_get_sector.return_value = mock_sector

            # Since stage_prepare does `from datetime import ...` internally,
            # we need to verify the result instead of mocking datetime.now
            await pipeline.stage_prepare(mock_ctx)

            # Dates should be normalized and valid YYYY-MM-DD
            d_ini = date.fromisoformat(mock_ctx.request.data_inicial)
            d_fin = date.fromisoformat(mock_ctx.request.data_final)
            assert (d_fin - d_ini).days == 10
            # data_final should be today (UTC)
            assert d_fin == datetime.now(timezone.utc).date()

    @pytest.mark.asyncio
    async def test_custom_dates_normalized(self):
        """AC7.9: stage_prepare normalizes custom dates to zero-padded YYYY-MM-DD."""
        from search_pipeline import SearchPipeline

        mock_request = MagicMock()
        mock_request.modo_busca = "custom"
        mock_request.data_inicial = "2026-02-08"  # Already canonical
        mock_request.data_final = "2026-02-18"
        mock_request.setor_id = "vestuario"
        mock_request.termos_busca = None
        mock_request.exclusion_terms = None
        mock_request.show_all_matches = False

        mock_ctx = MagicMock()
        mock_ctx.request = mock_request
        mock_ctx.tracker = None

        pipeline = SearchPipeline.__new__(SearchPipeline)
        pipeline.deps = MagicMock()

        with patch("search_pipeline.get_sector") as mock_get_sector:
            mock_sector = MagicMock()
            mock_sector.name = "Vestuário"
            mock_sector.keywords = ["uniforme"]
            mock_sector.exclusions = set()
            mock_sector.context_required_keywords = None
            mock_get_sector.return_value = mock_sector

            await pipeline.stage_prepare(mock_ctx)

            assert mock_ctx.request.data_inicial == "2026-02-08"
            assert mock_ctx.request.data_final == "2026-02-18"


# ============================================================================
# AC2: Auto-swap in fetch flow
# ============================================================================

class TestDateAutoSwap:
    """AC7.2: Swapped dates are auto-corrected."""

    @pytest.mark.asyncio
    async def test_async_client_swaps_dates(self):
        """Swapped dates are auto-corrected before PNCP call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json = MagicMock(return_value={
            "data": [], "totalRegistros": 0, "totalPaginas": 0,
            "paginaAtual": 1, "temProximaPagina": False,
        })

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        client = AsyncPNCPClient.__new__(AsyncPNCPClient)
        client._client = mock_client
        client.config = MagicMock()
        client.config.max_retries = 3
        client.config.base_delay = 0.01
        client.config.retryable_status_codes = {500, 502, 503}
        client.BASE_URL = "https://pncp.gov.br/api/consulta/v1"
        client._last_request_time = 0
        client._rate_limit = AsyncMock()

        # Pass dates in WRONG order (final < inicial)
        result = await client._fetch_page_async(
            "2026-02-18", "2026-02-08", 6, uf="SP"
        )

        # Should succeed (auto-swapped)
        assert result["totalRegistros"] == 0

        # Verify the actual params sent to PNCP have correct order
        call_args = mock_client.get.call_args
        sent_params = call_args.kwargs.get("params") or call_args[1].get("params")
        assert sent_params["dataInicial"] == "20260208"
        assert sent_params["dataFinal"] == "20260218"
