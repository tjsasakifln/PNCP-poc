"""Unit tests for PNCP client with retry logic and rate limiting."""

import time
from unittest.mock import Mock, patch

import pytest

from config import RetryConfig, DEFAULT_MODALIDADES
from exceptions import PNCPAPIError
from pncp_client import PNCPClient, calculate_delay

# Default modalidade for tests (Pregão Eletrônico)
DEFAULT_MODALIDADE = 6


class TestCalculateDelay:
    """Test exponential backoff delay calculation."""

    def test_exponential_growth_without_jitter(self):
        """Test delay grows exponentially when jitter is disabled."""
        config = RetryConfig(base_delay=2.0, exponential_base=2, jitter=False)

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

        assert client.config.max_retries == 5
        assert client.config.base_delay == 2.0
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

        assert client.session.headers["User-Agent"] == "BidIQ/1.0 (procurement-search; contact@bidiq.com.br)"
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
        mock_response.json.return_value = {
            "data": [{"id": 1}, {"id": 2}],
            "totalRegistros": 2,
            "totalPaginas": 1,
            "paginaAtual": 1,
            "paginasRestantes": 0,
        }
        mock_get.return_value = mock_response

        client = PNCPClient()
        result = client.fetch_page("2024-01-01", "2024-01-30", modalidade=DEFAULT_MODALIDADE)

        assert result["data"] == [{"id": 1}, {"id": 2}]
        assert result["totalRegistros"] == 2
        assert mock_get.called

    @patch("pncp_client.requests.Session.get")
    def test_fetch_page_with_uf_parameter(self, mock_get):
        """Test fetch_page includes UF parameter when provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        client = PNCPClient()
        client.fetch_page("2024-01-01", "2024-01-30", modalidade=DEFAULT_MODALIDADE, uf="SP")

        # Check UF was included in params
        call_args = mock_get.call_args
        assert call_args[1]["params"]["uf"] == "SP"

    @patch("pncp_client.requests.Session.get")
    def test_fetch_page_modalidade_parameter(self, mock_get):
        """Test fetch_page includes modalidade parameter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        client = PNCPClient()
        client.fetch_page("2024-01-01", "2024-01-30", modalidade=6)

        # Check modalidade was included in params
        call_args = mock_get.call_args
        assert call_args[1]["params"]["codigoModalidadeContratacao"] == 6

    @patch("pncp_client.requests.Session.get")
    def test_fetch_page_pagination_parameters(self, mock_get):
        """Test fetch_page sends correct pagination parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        client = PNCPClient()
        client.fetch_page("2024-01-01", "2024-01-30", modalidade=DEFAULT_MODALIDADE, pagina=3, tamanho=100)

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
            Mock(status_code=200),
        ]
        mock_responses[1].json.return_value = {"data": []}
        mock_get.side_effect = mock_responses

        config = RetryConfig(max_retries=2)
        client = PNCPClient(config=config)
        client.fetch_page("2024-01-01", "2024-01-30", modalidade=DEFAULT_MODALIDADE)

        assert mock_get.call_count == 2
        assert mock_sleep.called

    @patch("pncp_client.requests.Session.get")
    @patch("time.sleep")
    def test_retry_on_503_unavailable(self, mock_sleep, mock_get):
        """Test client retries on 503 service unavailable."""
        mock_responses = [
            Mock(status_code=503, text="Service Unavailable"),
            Mock(status_code=200),
        ]
        mock_responses[1].json.return_value = {"data": []}
        mock_get.side_effect = mock_responses

        config = RetryConfig(max_retries=2)
        client = PNCPClient(config=config)
        client.fetch_page("2024-01-01", "2024-01-30", modalidade=DEFAULT_MODALIDADE)

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
            client.fetch_page("2024-01-01", "2024-01-30", modalidade=DEFAULT_MODALIDADE)

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
            Mock(status_code=200),
        ]
        mock_responses[1].json.return_value = {"data": []}
        mock_get.side_effect = mock_responses

        client = PNCPClient()
        client.fetch_page("2024-01-01", "2024-01-30", modalidade=DEFAULT_MODALIDADE)

        # Check that sleep was called with the Retry-After value
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert 5 in sleep_calls  # Should sleep for 5 seconds

    @patch("pncp_client.requests.Session.get")
    @patch("time.sleep")
    def test_429_uses_default_wait_without_retry_after(self, mock_sleep, mock_get):
        """Test 429 uses default 60s wait when Retry-After header missing."""
        mock_responses = [Mock(status_code=429, headers={}), Mock(status_code=200)]
        mock_responses[1].json.return_value = {"data": []}
        mock_get.side_effect = mock_responses

        client = PNCPClient()
        client.fetch_page("2024-01-01", "2024-01-30", modalidade=DEFAULT_MODALIDADE)

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
            client.fetch_page("2024-01-01", "2024-01-30", modalidade=DEFAULT_MODALIDADE)

        # Should only try once (no retries)
        assert mock_get.call_count == 1

    @patch("pncp_client.requests.Session.get")
    def test_404_not_found_fails_immediately(self, mock_get):
        """Test 404 Not Found fails immediately without retry."""
        mock_get.return_value = Mock(status_code=404, text="Not Found")

        client = PNCPClient()

        with pytest.raises(PNCPAPIError, match="non-retryable status 404"):
            client.fetch_page("2024-01-01", "2024-01-30", modalidade=DEFAULT_MODALIDADE)

        assert mock_get.call_count == 1


class TestFetchPageExceptionRetry:
    """Test retry logic for network exceptions."""

    @patch("pncp_client.requests.Session.get")
    @patch("time.sleep")
    def test_retry_on_connection_error(self, mock_sleep, mock_get):
        """Test client retries on ConnectionError."""
        # First call raises ConnectionError, second succeeds
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {"data": []}
        mock_get.side_effect = [ConnectionError("Network error"), mock_response]

        config = RetryConfig(max_retries=2)
        client = PNCPClient(config=config)
        client.fetch_page("2024-01-01", "2024-01-30", modalidade=DEFAULT_MODALIDADE)

        assert mock_get.call_count == 2

    @patch("pncp_client.requests.Session.get")
    @patch("time.sleep")
    def test_retry_on_timeout_error(self, mock_sleep, mock_get):
        """Test client retries on TimeoutError."""
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {"data": []}
        mock_get.side_effect = [TimeoutError("Request timeout"), mock_response]

        config = RetryConfig(max_retries=2)
        client = PNCPClient(config=config)
        client.fetch_page("2024-01-01", "2024-01-30", modalidade=DEFAULT_MODALIDADE)

        assert mock_get.call_count == 2

    @patch("pncp_client.requests.Session.get")
    @patch("time.sleep")
    def test_exception_after_max_retries_raises_error(self, mock_sleep, mock_get):
        """Test exception is raised after max retries for network errors."""
        mock_get.side_effect = ConnectionError("Network error")

        config = RetryConfig(max_retries=2)
        client = PNCPClient(config=config)

        with pytest.raises(PNCPAPIError, match="Failed after 3 attempts"):
            client.fetch_page("2024-01-01", "2024-01-30", modalidade=DEFAULT_MODALIDADE)

        assert mock_get.call_count == 3


class TestFetchAllPagination:
    """Test fetch_all() automatic pagination functionality."""

    @patch("pncp_client.requests.Session.get")
    def test_fetch_all_single_page_single_modalidade(self, mock_get):
        """Test fetch_all with single page and single modalidade returns all items."""
        # Mock single page response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"numeroControlePNCP": "001", "unidadeOrgao": {"ufSigla": "SP", "municipioNome": ""}, "orgaoEntidade": {"razaoSocial": ""}},
                {"numeroControlePNCP": "002", "unidadeOrgao": {"ufSigla": "SP", "municipioNome": ""}, "orgaoEntidade": {"razaoSocial": ""}},
                {"numeroControlePNCP": "003", "unidadeOrgao": {"ufSigla": "SP", "municipioNome": ""}, "orgaoEntidade": {"razaoSocial": ""}},
            ],
            "totalRegistros": 3,
            "totalPaginas": 1,
            "paginasRestantes": 0,
        }
        mock_get.return_value = mock_response

        client = PNCPClient()
        # Test with single modalidade to simplify test
        results = list(client.fetch_all("2024-01-01", "2024-01-30", ufs=["SP"], modalidades=[6]))

        assert len(results) == 3
        assert results[0]["codigoCompra"] == "001"
        assert results[2]["codigoCompra"] == "003"
        # Should only call API once for single page, single modalidade
        assert mock_get.call_count == 1

    @patch("pncp_client.requests.Session.get")
    def test_fetch_all_multiple_pages(self, mock_get):
        """Test fetch_all correctly handles multiple pages."""
        # Mock 3 pages of data
        page_1 = Mock(status_code=200)
        page_1.json.return_value = {
            "data": [{"numeroControlePNCP": "1"}, {"numeroControlePNCP": "2"}],
            "totalRegistros": 5,
            "totalPaginas": 3,
            "paginasRestantes": 2,
        }

        page_2 = Mock(status_code=200)
        page_2.json.return_value = {
            "data": [{"numeroControlePNCP": "3"}, {"numeroControlePNCP": "4"}],
            "totalRegistros": 5,
            "totalPaginas": 3,
            "paginasRestantes": 1,
        }

        page_3 = Mock(status_code=200)
        page_3.json.return_value = {
            "data": [{"numeroControlePNCP": "5"}],
            "totalRegistros": 5,
            "totalPaginas": 3,
            "paginasRestantes": 0,
        }

        mock_get.side_effect = [page_1, page_2, page_3]

        client = PNCPClient()
        results = list(client.fetch_all("2024-01-01", "2024-01-30", ufs=["SP"], modalidades=[6]))

        # Should fetch all 5 items across 3 pages
        assert len(results) == 5
        assert results[0]["codigoCompra"] == "1"
        assert results[4]["codigoCompra"] == "5"
        # Should call API 3 times (once per page)
        assert mock_get.call_count == 3

    @patch("pncp_client.requests.Session.get")
    def test_fetch_all_multiple_ufs(self, mock_get):
        """Test fetch_all handles multiple UFs sequentially."""
        # Mock responses for SP (2 items) and RJ (1 item)
        sp_response = Mock(status_code=200)
        sp_response.json.return_value = {
            "data": [
                {"numeroControlePNCP": "1", "unidadeOrgao": {"ufSigla": "SP", "municipioNome": ""}, "orgaoEntidade": {"razaoSocial": ""}},
                {"numeroControlePNCP": "2", "unidadeOrgao": {"ufSigla": "SP", "municipioNome": ""}, "orgaoEntidade": {"razaoSocial": ""}},
            ],
            "totalRegistros": 2,
            "totalPaginas": 1,
            "paginasRestantes": 0,
        }

        rj_response = Mock(status_code=200)
        rj_response.json.return_value = {
            "data": [{"numeroControlePNCP": "3", "unidadeOrgao": {"ufSigla": "RJ", "municipioNome": ""}, "orgaoEntidade": {"razaoSocial": ""}}],
            "totalRegistros": 1,
            "totalPaginas": 1,
            "paginasRestantes": 0,
        }

        mock_get.side_effect = [sp_response, rj_response]

        client = PNCPClient()
        results = list(client.fetch_all("2024-01-01", "2024-01-30", ufs=["SP", "RJ"], modalidades=[6]))

        # Should fetch 3 items total (2 from SP, 1 from RJ)
        assert len(results) == 3
        assert results[0]["uf"] == "SP"
        assert results[2]["uf"] == "RJ"
        # Should call API twice (once per UF)
        assert mock_get.call_count == 2

    @patch("pncp_client.requests.Session.get")
    def test_fetch_all_multiple_modalidades(self, mock_get):
        """Test fetch_all iterates over multiple modalidades."""
        # Mock responses for modalidade 6 and 7
        mod_6_response = Mock(status_code=200)
        mod_6_response.json.return_value = {
            "data": [{"numeroControlePNCP": "001", "modalidade": 6}],
            "totalRegistros": 1,
            "totalPaginas": 1,
            "paginasRestantes": 0,
        }

        mod_7_response = Mock(status_code=200)
        mod_7_response.json.return_value = {
            "data": [{"numeroControlePNCP": "002", "modalidade": 7}],
            "totalRegistros": 1,
            "totalPaginas": 1,
            "paginasRestantes": 0,
        }

        mock_get.side_effect = [mod_6_response, mod_7_response]

        client = PNCPClient()
        results = list(client.fetch_all("2024-01-01", "2024-01-30", ufs=["SP"], modalidades=[6, 7]))

        # Should fetch items from both modalidades
        assert len(results) == 2
        # Should call API twice (once per modalidade)
        assert mock_get.call_count == 2

    @patch("pncp_client.requests.Session.get")
    def test_fetch_all_deduplicates_by_codigo_compra(self, mock_get):
        """Test fetch_all removes duplicates based on codigoCompra."""
        # Mock responses with duplicate numeroControlePNCP across modalidades
        mod_6_response = Mock(status_code=200)
        mod_6_response.json.return_value = {
            "data": [{"numeroControlePNCP": "001"}, {"numeroControlePNCP": "002"}],
            "totalRegistros": 2,
            "totalPaginas": 1,
            "paginasRestantes": 0,
        }

        mod_7_response = Mock(status_code=200)
        mod_7_response.json.return_value = {
            "data": [{"numeroControlePNCP": "001"}, {"numeroControlePNCP": "003"}],  # 001 is duplicate
            "totalRegistros": 2,
            "totalPaginas": 1,
            "paginasRestantes": 0,
        }

        mock_get.side_effect = [mod_6_response, mod_7_response]

        client = PNCPClient()
        results = list(client.fetch_all("2024-01-01", "2024-01-30", ufs=["SP"], modalidades=[6, 7]))

        # Should have 3 unique items (001 deduplicated)
        assert len(results) == 3
        codigo_compras = [r["codigoCompra"] for r in results]
        assert "001" in codigo_compras
        assert "002" in codigo_compras
        assert "003" in codigo_compras

    @patch("pncp_client.requests.Session.get")
    def test_fetch_all_empty_results(self, mock_get):
        """Test fetch_all handles empty results gracefully."""
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {
            "data": [],
            "totalRegistros": 0,
            "totalPaginas": 1,
            "paginasRestantes": 0,
        }
        mock_get.return_value = mock_response

        client = PNCPClient()
        results = list(client.fetch_all("2024-01-01", "2024-01-30", ufs=["SP"], modalidades=[6]))

        assert len(results) == 0
        assert mock_get.call_count == 1

    @patch("pncp_client.requests.Session.get")
    def test_fetch_all_progress_callback(self, mock_get):
        """Test fetch_all calls progress callback with correct values."""
        # Mock 2 pages
        page_1 = Mock(status_code=200)
        page_1.json.return_value = {
            "data": [{"numeroControlePNCP": "1"}, {"numeroControlePNCP": "2"}, {"numeroControlePNCP": "3"}],
            "totalRegistros": 5,
            "totalPaginas": 2,
            "paginasRestantes": 1,
        }

        page_2 = Mock(status_code=200)
        page_2.json.return_value = {
            "data": [{"numeroControlePNCP": "4"}, {"numeroControlePNCP": "5"}],
            "totalRegistros": 5,
            "totalPaginas": 2,
            "paginasRestantes": 0,
        }

        mock_get.side_effect = [page_1, page_2]

        # Track progress callback calls
        progress_calls = []

        def on_progress(page, total_pages, items_fetched):
            progress_calls.append((page, total_pages, items_fetched))

        client = PNCPClient()
        list(
            client.fetch_all(
                "2024-01-01", "2024-01-30", ufs=["SP"], modalidades=[6], on_progress=on_progress
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
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {
            "data": [{"numeroControlePNCP": "1"}, {"numeroControlePNCP": "2"}],
            "totalRegistros": 2,
            "totalPaginas": 1,
            "paginasRestantes": 0,
        }
        mock_get.return_value = mock_response

        client = PNCPClient()
        generator = client.fetch_all("2024-01-01", "2024-01-30", ufs=["SP"], modalidades=[6])

        # Should be a generator
        import types

        assert isinstance(generator, types.GeneratorType)

        # Should yield individual dictionaries
        first_item = next(generator)
        assert isinstance(first_item, dict)
        assert first_item["codigoCompra"] == "1"

    @patch("pncp_client.requests.Session.get")
    def test_fetch_all_without_ufs(self, mock_get):
        """Test fetch_all works without specifying UFs (fetches all)."""
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {
            "data": [
                {"numeroControlePNCP": "1", "unidadeOrgao": {"ufSigla": "SP", "municipioNome": ""}, "orgaoEntidade": {"razaoSocial": ""}},
                {"numeroControlePNCP": "2", "unidadeOrgao": {"ufSigla": "RJ", "municipioNome": ""}, "orgaoEntidade": {"razaoSocial": ""}},
            ],
            "totalRegistros": 2,
            "totalPaginas": 1,
            "paginasRestantes": 0,
        }
        mock_get.return_value = mock_response

        client = PNCPClient()
        results = list(client.fetch_all("2024-01-01", "2024-01-30", modalidades=[6]))

        assert len(results) == 2
        # Check that UF parameter was NOT sent
        call_args = mock_get.call_args
        assert "uf" not in call_args[1]["params"]

    @patch("pncp_client.requests.Session.get")
    def test_fetch_all_uses_default_modalidades(self, mock_get):
        """Test fetch_all uses DEFAULT_MODALIDADES when none specified."""
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {
            "data": [],
            "totalRegistros": 0,
            "totalPaginas": 1,
            "paginasRestantes": 0,
        }
        mock_get.return_value = mock_response

        client = PNCPClient()
        list(client.fetch_all("2024-01-01", "2024-01-30", ufs=["SP"]))

        # Should call API once for each default modalidade
        assert mock_get.call_count == len(DEFAULT_MODALIDADES)


class TestFetchByUFHelper:
    """Test _fetch_by_uf() helper method."""

    @patch("pncp_client.requests.Session.get")
    def test_fetch_by_uf_stops_when_tem_proxima_false(self, mock_get):
        """Test _fetch_by_uf stops pagination when temProximaPagina is False."""
        # First page has temProximaPagina=True
        page_1 = Mock(status_code=200)
        page_1.json.return_value = {
            "data": [{"id": 1}],
            "totalRegistros": 2,
            "totalPaginas": 2,
            "paginaAtual": 1,
            "paginasRestantes": 1,
        }

        # Second page has temProximaPagina=False (last page)
        page_2 = Mock(status_code=200)
        page_2.json.return_value = {
            "data": [{"id": 2}],
            "totalRegistros": 2,
            "totalPaginas": 2,
            "paginaAtual": 2,
            "paginasRestantes": 0,
        }

        mock_get.side_effect = [page_1, page_2]

        client = PNCPClient()
        results = list(client._fetch_by_uf("2024-01-01", "2024-01-30", DEFAULT_MODALIDADE, "SP", None))

        assert len(results) == 2
        # Should stop after page 2 (not request page 3)
        assert mock_get.call_count == 2

    @patch("pncp_client.requests.Session.get")
    def test_fetch_by_uf_correct_page_numbers(self, mock_get):
        """Test _fetch_by_uf sends correct page numbers (1-indexed)."""
        # Mock 2 pages
        page_1 = Mock(status_code=200)
        page_1.json.return_value = {
            "data": [{"id": 1}],
            "totalRegistros": 2,
            "totalPaginas": 2,
            "paginaAtual": 1,
            "paginasRestantes": 1,
        }

        page_2 = Mock(status_code=200)
        page_2.json.return_value = {
            "data": [{"id": 2}],
            "totalRegistros": 2,
            "totalPaginas": 2,
            "paginaAtual": 2,
            "paginasRestantes": 0,
        }

        mock_get.side_effect = [page_1, page_2]

        client = PNCPClient()
        list(client._fetch_by_uf("2024-01-01", "2024-01-30", DEFAULT_MODALIDADE, "SP", None))

        # Check page numbers in API calls
        call_1_params = mock_get.call_args_list[0][1]["params"]
        call_2_params = mock_get.call_args_list[1][1]["params"]

        assert call_1_params["pagina"] == 1
        assert call_2_params["pagina"] == 2

    @patch("pncp_client.requests.Session.get")
    def test_fetch_by_uf_handles_uf_none(self, mock_get):
        """Test _fetch_by_uf works with uf=None (all UFs)."""
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {
            "data": [{"id": 1}],
            "totalRegistros": 1,
            "totalPaginas": 1,
            "paginaAtual": 1,
            "paginasRestantes": 0,
        }
        mock_get.return_value = mock_response

        client = PNCPClient()
        results = list(client._fetch_by_uf("2024-01-01", "2024-01-30", DEFAULT_MODALIDADE, None, None))

        assert len(results) == 1
        # Check that uf was not in params
        call_params = mock_get.call_args[1]["params"]
        assert "uf" not in call_params

    @patch("pncp_client.requests.Session.get")
    def test_fetch_by_uf_includes_modalidade(self, mock_get):
        """Test _fetch_by_uf includes modalidade in API calls."""
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {
            "data": [{"id": 1}],
            "totalRegistros": 1,
            "totalPaginas": 1,
            "paginaAtual": 1,
            "paginasRestantes": 0,
        }
        mock_get.return_value = mock_response

        client = PNCPClient()
        list(client._fetch_by_uf("2024-01-01", "2024-01-30", 6, "SP", None))

        # Check that modalidade was in params
        call_params = mock_get.call_args[1]["params"]
        assert call_params["codigoModalidadeContratacao"] == 6


class TestDateRangeChunking:
    """Test _chunk_date_range() date splitting logic."""

    def test_short_range_single_chunk(self):
        """A range <= 30 days should produce a single chunk."""
        chunks = PNCPClient._chunk_date_range("2024-01-01", "2024-01-30")
        assert len(chunks) == 1
        assert chunks[0] == ("2024-01-01", "2024-01-30")

    def test_31_days_produces_two_chunks(self):
        """A 31-day range should split into 2 chunks."""
        chunks = PNCPClient._chunk_date_range("2024-01-01", "2024-01-31")
        assert len(chunks) == 2
        assert chunks[0] == ("2024-01-01", "2024-01-30")
        assert chunks[1] == ("2024-01-31", "2024-01-31")

    def test_six_month_range(self):
        """A 6-month range (~180 days) should produce ~6 chunks."""
        chunks = PNCPClient._chunk_date_range("2025-08-01", "2026-01-28")
        # 181 days / 30 = ~7 chunks
        assert len(chunks) >= 6
        # First chunk starts at start date
        assert chunks[0][0] == "2025-08-01"
        # Last chunk ends at end date
        assert chunks[-1][1] == "2026-01-28"
        # No gaps between chunks
        from datetime import date, timedelta
        for i in range(len(chunks) - 1):
            end = date.fromisoformat(chunks[i][1])
            next_start = date.fromisoformat(chunks[i + 1][0])
            assert next_start - end == timedelta(days=1)

    def test_single_day_range(self):
        """A single-day range should produce exactly one chunk."""
        chunks = PNCPClient._chunk_date_range("2024-06-15", "2024-06-15")
        assert len(chunks) == 1
        assert chunks[0] == ("2024-06-15", "2024-06-15")
