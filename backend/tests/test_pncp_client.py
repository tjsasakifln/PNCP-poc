"""Unit tests for PNCP client with retry logic and rate limiting."""

import time
from unittest.mock import Mock, patch

import pytest

from config import RetryConfig
from exceptions import PNCPAPIError
from pncp_client import PNCPClient, calculate_delay


class TestCalculateDelay:
    """Test exponential backoff delay calculation."""

    def test_exponential_growth_without_jitter(self):
        """Test delay grows exponentially when jitter is disabled."""
        # max_delay default is 15.0, so attempt 3 (2^3 * 2 = 16) is capped at 15.0
        config = RetryConfig(base_delay=2.0, exponential_base=2, jitter=False, max_delay=60.0)

        assert calculate_delay(0, config) == 2.0
        assert calculate_delay(1, config) == 4.0
        assert calculate_delay(2, config) == 8.0
        assert calculate_delay(3, config) == 16.0
        assert calculate_delay(4, config) == 32.0

    def test_max_delay_cap(self):
        """Test delay is capped at max_delay."""
        config = RetryConfig(
            base_delay=2.0, exponential_base=2, max_delay=60.0, jitter=False
        )

        # 2^6 = 64, should be capped at 60
        assert calculate_delay(5, config) == 60.0
        assert calculate_delay(10, config) == 60.0

    def test_default_max_delay_caps_at_15(self):
        """Default max_delay=15.0 caps calculation: attempt 3 would be 16 but is capped."""
        config = RetryConfig(base_delay=2.0, exponential_base=2, jitter=False)
        # Default max_delay is 15.0, so attempt 3 (16.0) is capped at 15.0
        assert calculate_delay(3, config) == 15.0
        assert calculate_delay(4, config) == 15.0

    def test_jitter_adds_randomness(self):
        """Test jitter adds randomness within expected range."""
        config = RetryConfig(base_delay=10.0, exponential_base=1, jitter=True)

        # With jitter, delay should be between 5.0 and 15.0 (±50%)
        delays = [calculate_delay(0, config) for _ in range(100)]

        assert all(5.0 <= d <= 15.0 for d in delays)
        # Check there's actual variation (not all the same)
        assert len(set(delays)) > 10


class TestPNCPClient:
    """Test PNCPClient initialization and session configuration."""

    def test_client_initialization_default_config(self):
        """Test client initializes with default config."""
        client = PNCPClient()

        assert client.config.max_retries == 1
        assert client.config.base_delay == 1.5
        assert client.session is not None
        assert client._request_count == 0

    def test_client_initialization_custom_config(self):
        """Test client initializes with custom config."""
        custom_config = RetryConfig(max_retries=3, base_delay=1.0)
        client = PNCPClient(config=custom_config)

        assert client.config.max_retries == 3
        assert client.config.base_delay == 1.0

    def test_session_has_correct_headers(self):
        """Test session is configured with correct headers."""
        client = PNCPClient()

        assert "SmartLic" in client.session.headers["User-Agent"]
        assert client.session.headers["Accept"] == "application/json"

    def test_context_manager(self):
        """Test client can be used as context manager."""
        with PNCPClient() as client:
            assert client.session is not None

        # Session should be closed after context exit
        # We can't easily test this without mocking, but coverage is achieved


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiting_enforces_minimum_interval(self):
        """Test rate limiting enforces 100ms minimum between requests."""
        client = PNCPClient()

        # First request should not sleep
        start = time.time()
        client._rate_limit()
        first_duration = time.time() - start
        assert first_duration < 0.01  # Should be almost instant

        # Second request immediately after should sleep
        start = time.time()
        client._rate_limit()
        second_duration = time.time() - start
        assert second_duration >= 0.09  # Should sleep ~100ms

    def test_rate_limiting_tracks_request_count(self):
        """Test rate limiting tracks total request count."""
        client = PNCPClient()

        assert client._request_count == 0

        client._rate_limit()
        assert client._request_count == 1

        client._rate_limit()
        assert client._request_count == 2


class TestFetchPageSuccess:
    """Test successful fetch_page scenarios."""

    @patch("pncp_client.requests.Session.get")
    def test_fetch_page_success(self, mock_get):
        """Test successful page fetch returns correct data."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {
            "data": [{"id": 1}, {"id": 2}],
            "totalRegistros": 2,
            "totalPaginas": 1,
            "paginaAtual": 1,
            "temProximaPagina": False,
        }
        mock_get.return_value = mock_response

        client = PNCPClient()
        result = client.fetch_page("2024-01-01", "2024-01-31", modalidade=6)

        assert result["data"] == [{"id": 1}, {"id": 2}]
        assert result["totalRegistros"] == 2
        assert mock_get.called

    @patch("pncp_client.requests.Session.get")
    def test_fetch_page_with_uf_parameter(self, mock_get):
        """Test fetch_page includes UF parameter when provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        client = PNCPClient()
        client.fetch_page("2024-01-01", "2024-01-31", modalidade=6, uf="SP")

        # Check UF was included in params
        call_args = mock_get.call_args
        assert call_args[1]["params"]["uf"] == "SP"

    @patch("pncp_client.requests.Session.get")
    def test_fetch_page_pagination_parameters(self, mock_get):
        """Test fetch_page sends correct pagination parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        client = PNCPClient()
        client.fetch_page("2024-01-01", "2024-01-31", modalidade=6, pagina=3, tamanho=100)

        call_args = mock_get.call_args
        params = call_args[1]["params"]
        assert params["pagina"] == 3
        assert params["tamanhoPagina"] == 100


class TestFetchPageRetry:
    """Test retry logic for transient failures."""

    @patch("pncp_client.requests.Session.get")
    @patch("time.sleep")  # Mock sleep to speed up tests
    def test_retry_on_500_server_error(self, mock_sleep, mock_get):
        """Test client retries on 500 server error."""
        # First call fails with 500, second succeeds
        mock_responses = [
            Mock(status_code=500, text="Internal Server Error"),
            Mock(status_code=200, headers={"content-type": "application/json"}),
        ]
        mock_responses[1].json.return_value = {"data": []}
        mock_get.side_effect = mock_responses

        config = RetryConfig(max_retries=2)
        client = PNCPClient(config=config)
        client.fetch_page("2024-01-01", "2024-01-31", modalidade=6)

        assert mock_get.call_count == 2
        assert mock_sleep.called

    @patch("pncp_client.requests.Session.get")
    @patch("time.sleep")
    def test_retry_on_503_unavailable(self, mock_sleep, mock_get):
        """Test client retries on 503 service unavailable."""
        mock_responses = [
            Mock(status_code=503, text="Service Unavailable"),
            Mock(status_code=200, headers={"content-type": "application/json"}),
        ]
        mock_responses[1].json.return_value = {"data": []}
        mock_get.side_effect = mock_responses

        config = RetryConfig(max_retries=2)
        client = PNCPClient(config=config)
        client.fetch_page("2024-01-01", "2024-01-31", modalidade=6)

        assert mock_get.call_count == 2

    @patch("pncp_client.requests.Session.get")
    @patch("time.sleep")
    def test_max_retries_exceeded_raises_error(self, mock_sleep, mock_get):
        """Test error is raised after max retries exceeded."""
        # Always return 500
        mock_get.return_value = Mock(status_code=500, text="Internal Server Error")

        config = RetryConfig(max_retries=2)
        client = PNCPClient(config=config)

        with pytest.raises(PNCPAPIError, match="Failed after 3 attempts"):
            client.fetch_page("2024-01-01", "2024-01-31", modalidade=6)

        # Should try 3 times total (initial + 2 retries)
        assert mock_get.call_count == 3


class TestFetchPageRateLimiting:
    """Test rate limit (429) handling."""

    @patch("pncp_client.requests.Session.get")
    @patch("time.sleep")
    def test_429_respects_retry_after_header(self, mock_sleep, mock_get):
        """Test 429 response respects Retry-After header."""
        mock_responses = [
            Mock(status_code=429, headers={"Retry-After": "5"}),
            Mock(status_code=200, headers={"content-type": "application/json"}),
        ]
        mock_responses[1].json.return_value = {"data": []}
        mock_get.side_effect = mock_responses

        client = PNCPClient()
        client.fetch_page("2024-01-01", "2024-01-31", modalidade=6)

        # Check that sleep was called with the Retry-After value
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert 5 in sleep_calls  # Should sleep for 5 seconds

    @patch("pncp_client.requests.Session.get")
    @patch("time.sleep")
    def test_429_uses_default_wait_without_retry_after(self, mock_sleep, mock_get):
        """Test 429 uses default 60s wait when Retry-After header missing."""
        mock_responses = [Mock(status_code=429, headers={}), Mock(status_code=200, headers={"content-type": "application/json"})]
        mock_responses[1].json.return_value = {"data": []}
        mock_get.side_effect = mock_responses

        client = PNCPClient()
        client.fetch_page("2024-01-01", "2024-01-31", modalidade=6)

        # Should use default 60 second wait
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert 60 in sleep_calls


class TestFetchPageNonRetryableErrors:
    """Test immediate failure for non-retryable errors."""

    @patch("pncp_client.requests.Session.get")
    def test_400_bad_request_fails_immediately(self, mock_get):
        """Test 400 Bad Request fails immediately without retry."""
        mock_get.return_value = Mock(status_code=400, text="Bad Request")

        client = PNCPClient()

        with pytest.raises(PNCPAPIError, match="non-retryable status 400"):
            client.fetch_page("2024-01-01", "2024-01-31", modalidade=6)

        # Should only try once (no retries)
        assert mock_get.call_count == 1

    @patch("pncp_client.requests.Session.get")
    def test_404_not_found_fails_immediately(self, mock_get):
        """Test 404 Not Found fails immediately without retry."""
        mock_get.return_value = Mock(status_code=404, text="Not Found")

        client = PNCPClient()

        with pytest.raises(PNCPAPIError, match="non-retryable status 404"):
            client.fetch_page("2024-01-01", "2024-01-31", modalidade=6)

        assert mock_get.call_count == 1


class TestFetchPageExceptionRetry:
    """Test retry logic for network exceptions."""

    @patch("pncp_client.requests.Session.get")
    @patch("time.sleep")
    def test_retry_on_connection_error(self, mock_sleep, mock_get):
        """Test client retries on ConnectionError."""
        # First call raises ConnectionError, second succeeds
        mock_response = Mock(status_code=200, headers={"content-type": "application/json"})
        mock_response.json.return_value = {"data": []}
        mock_get.side_effect = [ConnectionError("Network error"), mock_response]

        config = RetryConfig(max_retries=2)
        client = PNCPClient(config=config)
        client.fetch_page("2024-01-01", "2024-01-31", modalidade=6)

        assert mock_get.call_count == 2

    @patch("pncp_client.requests.Session.get")
    @patch("time.sleep")
    def test_retry_on_timeout_error(self, mock_sleep, mock_get):
        """Test client retries on TimeoutError."""
        mock_response = Mock(status_code=200, headers={"content-type": "application/json"})
        mock_response.json.return_value = {"data": []}
        mock_get.side_effect = [TimeoutError("Request timeout"), mock_response]

        config = RetryConfig(max_retries=2)
        client = PNCPClient(config=config)
        client.fetch_page("2024-01-01", "2024-01-31", modalidade=6)

        assert mock_get.call_count == 2

    @patch("pncp_client.requests.Session.get")
    @patch("time.sleep")
    def test_exception_after_max_retries_raises_error(self, mock_sleep, mock_get):
        """Test exception is raised after max retries for network errors."""
        mock_get.side_effect = ConnectionError("Network error")

        config = RetryConfig(max_retries=2)
        client = PNCPClient(config=config)

        with pytest.raises(PNCPAPIError, match="Failed after 3 attempts"):
            client.fetch_page("2024-01-01", "2024-01-31", modalidade=6)

        assert mock_get.call_count == 3


class TestFetchAllPagination:
    """Test fetch_all() automatic pagination functionality.

    NOTE: fetch_all() iterates over modalidades internally (DEFAULT_MODALIDADES=[4,5,6,7]).
    To test single-modality behavior, pass modalidades=[6] explicitly.
    Items without 'numeroControlePNCP' are dropped by the dedup logic in fetch_all.
    """

    @patch("pncp_client.requests.Session.get")
    def test_fetch_all_single_page(self, mock_get):
        """Test fetch_all with single page returns all items."""
        # Mock single page response — items need numeroControlePNCP for dedup
        # NOTE: Production code uses paginasRestantes (not temProximaPagina) for pagination
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {
            "data": [
                {"numeroControlePNCP": "PNCP-001", "codigoCompra": "001", "uf": "SP"},
                {"numeroControlePNCP": "PNCP-002", "codigoCompra": "002", "uf": "SP"},
                {"numeroControlePNCP": "PNCP-003", "codigoCompra": "003", "uf": "SP"},
            ],
            "totalRegistros": 3,
            "totalPaginas": 1,
            "paginaAtual": 1,
            "paginasRestantes": 0,
        }
        mock_get.return_value = mock_response

        client = PNCPClient()
        # Use modalidades=[6] and a short date range (≤29 days = 1 chunk) to get 1 API call
        results = list(client.fetch_all("2024-01-01", "2024-01-10", ufs=["SP"], modalidades=[6]))

        assert len(results) == 3
        # codigoCompra is overwritten by _normalize_item with numeroControlePNCP
        assert results[0]["codigoCompra"] == "PNCP-001"
        assert results[2]["codigoCompra"] == "PNCP-003"
        # Should only call API once for single page
        assert mock_get.call_count == 1

    @patch("pncp_client.requests.Session.get")
    def test_fetch_all_multiple_pages(self, mock_get):
        """Test fetch_all correctly handles multiple pages."""
        # Mock 3 pages of data — items need numeroControlePNCP for dedup
        # NOTE: Production code uses paginasRestantes (not temProximaPagina) for pagination
        page_1 = Mock(status_code=200, headers={"content-type": "application/json"})
        page_1.json.return_value = {
            "data": [{"numeroControlePNCP": "P-1"}, {"numeroControlePNCP": "P-2"}],
            "totalRegistros": 5,
            "totalPaginas": 3,
            "paginaAtual": 1,
            "paginasRestantes": 2,
        }

        page_2 = Mock(status_code=200, headers={"content-type": "application/json"})
        page_2.json.return_value = {
            "data": [{"numeroControlePNCP": "P-3"}, {"numeroControlePNCP": "P-4"}],
            "totalRegistros": 5,
            "totalPaginas": 3,
            "paginaAtual": 2,
            "paginasRestantes": 1,
        }

        page_3 = Mock(status_code=200, headers={"content-type": "application/json"})
        page_3.json.return_value = {
            "data": [{"numeroControlePNCP": "P-5"}],
            "totalRegistros": 5,
            "totalPaginas": 3,
            "paginaAtual": 3,
            "paginasRestantes": 0,
        }

        mock_get.side_effect = [page_1, page_2, page_3]

        client = PNCPClient()
        # Use a short date range (≤29 days = 1 chunk) to avoid date-chunking extra calls
        results = list(client.fetch_all("2024-01-01", "2024-01-10", ufs=["SP"], modalidades=[6]))

        # Should fetch all 5 items across 3 pages
        assert len(results) == 5
        assert results[0]["numeroControlePNCP"] == "P-1"
        assert results[4]["numeroControlePNCP"] == "P-5"
        # Should call API 3 times (once per page)
        assert mock_get.call_count == 3

    @patch("pncp_client.requests.Session.get")
    def test_fetch_all_multiple_ufs(self, mock_get):
        """Test fetch_all handles multiple UFs sequentially."""
        # Mock responses for SP (2 items) and RJ (1 item)
        # NOTE: Production code uses paginasRestantes (not temProximaPagina) for pagination
        # NOTE: _normalize_item reads uf from unidadeOrgao.ufSigla, not top-level uf
        sp_response = Mock(status_code=200, headers={"content-type": "application/json"})
        sp_response.json.return_value = {
            "data": [
                {"numeroControlePNCP": "SP-1", "unidadeOrgao": {"ufSigla": "SP", "municipioNome": ""}},
                {"numeroControlePNCP": "SP-2", "unidadeOrgao": {"ufSigla": "SP", "municipioNome": ""}},
            ],
            "totalRegistros": 2,
            "totalPaginas": 1,
            "paginaAtual": 1,
            "paginasRestantes": 0,
        }

        rj_response = Mock(status_code=200, headers={"content-type": "application/json"})
        rj_response.json.return_value = {
            "data": [{"numeroControlePNCP": "RJ-3", "unidadeOrgao": {"ufSigla": "RJ", "municipioNome": ""}}],
            "totalRegistros": 1,
            "totalPaginas": 1,
            "paginaAtual": 1,
            "paginasRestantes": 0,
        }

        mock_get.side_effect = [sp_response, rj_response]

        client = PNCPClient()
        # Use short date range (≤29 days = 1 chunk) to avoid date-chunking extra calls
        results = list(client.fetch_all("2024-01-01", "2024-01-10", ufs=["SP", "RJ"], modalidades=[6]))

        # Should fetch 3 items total (2 from SP, 1 from RJ)
        assert len(results) == 3
        assert results[0]["uf"] == "SP"
        assert results[2]["uf"] == "RJ"
        # Should call API twice (once per UF)
        assert mock_get.call_count == 2

    @patch("pncp_client.requests.Session.get")
    def test_fetch_all_empty_results(self, mock_get):
        """Test fetch_all handles empty results gracefully."""
        mock_response = Mock(status_code=200, headers={"content-type": "application/json"})
        mock_response.json.return_value = {
            "data": [],
            "totalRegistros": 0,
            "totalPaginas": 1,
            "paginaAtual": 1,
            "paginasRestantes": 0,
        }
        mock_get.return_value = mock_response

        client = PNCPClient()
        # Use short date range (≤29 days = 1 chunk) to get exactly 1 API call
        results = list(client.fetch_all("2024-01-01", "2024-01-10", ufs=["SP"], modalidades=[6]))

        assert len(results) == 0
        assert mock_get.call_count == 1

    @patch("pncp_client.requests.Session.get")
    def test_fetch_all_progress_callback(self, mock_get):
        """Test fetch_all calls progress callback with correct values."""
        # Mock 2 pages — items need numeroControlePNCP for dedup
        # NOTE: Production code uses paginasRestantes (not temProximaPagina) for pagination
        page_1 = Mock(status_code=200, headers={"content-type": "application/json"})
        page_1.json.return_value = {
            "data": [
                {"numeroControlePNCP": "C-1"},
                {"numeroControlePNCP": "C-2"},
                {"numeroControlePNCP": "C-3"},
            ],
            "totalRegistros": 5,
            "totalPaginas": 2,
            "paginaAtual": 1,
            "paginasRestantes": 1,
        }

        page_2 = Mock(status_code=200, headers={"content-type": "application/json"})
        page_2.json.return_value = {
            "data": [{"numeroControlePNCP": "C-4"}, {"numeroControlePNCP": "C-5"}],
            "totalRegistros": 5,
            "totalPaginas": 2,
            "paginaAtual": 2,
            "paginasRestantes": 0,
        }

        mock_get.side_effect = [page_1, page_2]

        # Track progress callback calls
        progress_calls = []

        def on_progress(page, total_pages, items_fetched):
            progress_calls.append((page, total_pages, items_fetched))

        client = PNCPClient()
        # Use short date range (≤29 days = 1 chunk) to avoid extra calls from date chunking
        list(
            client.fetch_all(
                "2024-01-01", "2024-01-10", ufs=["SP"], modalidades=[6], on_progress=on_progress
            )
        )

        # Should have been called twice (once per page)
        assert len(progress_calls) == 2
        # First page: page 1/2, 3 items
        assert progress_calls[0] == (1, 2, 3)
        # Second page: page 2/2, 5 items total
        assert progress_calls[1] == (2, 2, 5)

    @patch("pncp_client.requests.Session.get")
    def test_fetch_all_yields_individual_items(self, mock_get):
        """Test fetch_all is a generator yielding individual items, not lists."""
        mock_response = Mock(status_code=200, headers={"content-type": "application/json"})
        mock_response.json.return_value = {
            "data": [
                {"numeroControlePNCP": "Y-1"},
                {"numeroControlePNCP": "Y-2"},
            ],
            "totalRegistros": 2,
            "totalPaginas": 1,
            "paginaAtual": 1,
            "paginasRestantes": 0,
        }
        mock_get.return_value = mock_response

        client = PNCPClient()
        # Use short date range (≤29 days = 1 chunk) to avoid extra calls from date chunking
        generator = client.fetch_all("2024-01-01", "2024-01-10", ufs=["SP"], modalidades=[6])

        # Should be a generator
        import types

        assert isinstance(generator, types.GeneratorType)

        # Should yield individual dictionaries
        first_item = next(generator)
        assert isinstance(first_item, dict)
        assert first_item["numeroControlePNCP"] == "Y-1"

    @patch("pncp_client.requests.Session.get")
    def test_fetch_all_without_ufs(self, mock_get):
        """Test fetch_all works without specifying UFs (fetches all)."""
        mock_response = Mock(status_code=200, headers={"content-type": "application/json"})
        mock_response.json.return_value = {
            "data": [
                {"numeroControlePNCP": "ALL-1", "uf": "SP"},
                {"numeroControlePNCP": "ALL-2", "uf": "RJ"},
            ],
            "totalRegistros": 2,
            "totalPaginas": 1,
            "paginaAtual": 1,
            "paginasRestantes": 0,
        }
        mock_get.return_value = mock_response

        client = PNCPClient()
        # Use short date range (≤29 days = 1 chunk) to avoid extra calls from date chunking
        results = list(client.fetch_all("2024-01-01", "2024-01-10", modalidades=[6]))

        assert len(results) == 2
        # Check that UF parameter was NOT sent
        call_args = mock_get.call_args
        assert "uf" not in call_args[1]["params"]


class TestFetchByUFHelper:
    """Test _fetch_by_uf() helper method."""

    @patch("pncp_client.requests.Session.get")
    def test_fetch_by_uf_stops_when_no_remaining_pages(self, mock_get):
        """Test _fetch_by_uf stops pagination when paginasRestantes is 0."""
        # NOTE: Production code uses paginasRestantes (not temProximaPagina) for pagination
        # First page has paginasRestantes=1 (more pages)
        page_1 = Mock(status_code=200, headers={"content-type": "application/json"})
        page_1.json.return_value = {
            "data": [{"id": 1}],
            "totalRegistros": 2,
            "totalPaginas": 2,
            "paginaAtual": 1,
            "paginasRestantes": 1,
        }

        # Second page has paginasRestantes=0 (last page)
        page_2 = Mock(status_code=200, headers={"content-type": "application/json"})
        page_2.json.return_value = {
            "data": [{"id": 2}],
            "totalRegistros": 2,
            "totalPaginas": 2,
            "paginaAtual": 2,
            "paginasRestantes": 0,
        }

        mock_get.side_effect = [page_1, page_2]

        client = PNCPClient()
        # Signature: _fetch_by_uf(data_inicial, data_final, modalidade, uf, on_progress)
        results = list(client._fetch_by_uf("2024-01-01", "2024-01-31", 6, "SP", None))

        assert len(results) == 2
        # Should stop after page 2 (not request page 3)
        assert mock_get.call_count == 2

    @patch("pncp_client.requests.Session.get")
    def test_fetch_by_uf_correct_page_numbers(self, mock_get):
        """Test _fetch_by_uf sends correct page numbers (1-indexed)."""
        # Mock 2 pages — NOTE: uses paginasRestantes for next-page detection
        page_1 = Mock(status_code=200, headers={"content-type": "application/json"})
        page_1.json.return_value = {
            "data": [{"id": 1}],
            "totalRegistros": 2,
            "totalPaginas": 2,
            "paginaAtual": 1,
            "paginasRestantes": 1,
        }

        page_2 = Mock(status_code=200, headers={"content-type": "application/json"})
        page_2.json.return_value = {
            "data": [{"id": 2}],
            "totalRegistros": 2,
            "totalPaginas": 2,
            "paginaAtual": 2,
            "paginasRestantes": 0,
        }

        mock_get.side_effect = [page_1, page_2]

        client = PNCPClient()
        list(client._fetch_by_uf("2024-01-01", "2024-01-31", 6, "SP", None))

        # Check page numbers in API calls
        call_1_params = mock_get.call_args_list[0][1]["params"]
        call_2_params = mock_get.call_args_list[1][1]["params"]

        assert call_1_params["pagina"] == 1
        assert call_2_params["pagina"] == 2

    @patch("pncp_client.requests.Session.get")
    def test_fetch_by_uf_handles_uf_none(self, mock_get):
        """Test _fetch_by_uf works with uf=None (all UFs)."""
        mock_response = Mock(status_code=200, headers={"content-type": "application/json"})
        mock_response.json.return_value = {
            "data": [{"id": 1}],
            "totalRegistros": 1,
            "totalPaginas": 1,
            "paginaAtual": 1,
            "paginasRestantes": 0,
        }
        mock_get.return_value = mock_response

        client = PNCPClient()
        results = list(client._fetch_by_uf("2024-01-01", "2024-01-31", 6, None, None))

        assert len(results) == 1
        # Check that uf was not in params
        call_params = mock_get.call_args[1]["params"]
        assert "uf" not in call_params
