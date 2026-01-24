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
        config = RetryConfig(base_delay=2.0, exponential_base=2, jitter=False)

        assert calculate_delay(0, config) == 2.0
        assert calculate_delay(1, config) == 4.0
        assert calculate_delay(2, config) == 8.0
        assert calculate_delay(3, config) == 16.0
        assert calculate_delay(4, config) == 32.0

    def test_max_delay_cap(self):
        """Test delay is capped at max_delay."""
        config = RetryConfig(
            base_delay=2.0,
            exponential_base=2,
            max_delay=60.0,
            jitter=False
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

        assert client.session.headers["User-Agent"] == "BidIQ-POC/0.2"
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

    @patch('pncp_client.requests.Session.get')
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
            "temProximaPagina": False
        }
        mock_get.return_value = mock_response

        client = PNCPClient()
        result = client.fetch_page("2024-01-01", "2024-01-31")

        assert result["data"] == [{"id": 1}, {"id": 2}]
        assert result["totalRegistros"] == 2
        assert mock_get.called

    @patch('pncp_client.requests.Session.get')
    def test_fetch_page_with_uf_parameter(self, mock_get):
        """Test fetch_page includes UF parameter when provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        client = PNCPClient()
        client.fetch_page("2024-01-01", "2024-01-31", uf="SP")

        # Check UF was included in params
        call_args = mock_get.call_args
        assert call_args[1]["params"]["uf"] == "SP"

    @patch('pncp_client.requests.Session.get')
    def test_fetch_page_pagination_parameters(self, mock_get):
        """Test fetch_page sends correct pagination parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        client = PNCPClient()
        client.fetch_page("2024-01-01", "2024-01-31", pagina=3, tamanho=100)

        call_args = mock_get.call_args
        params = call_args[1]["params"]
        assert params["pagina"] == 3
        assert params["tamanhoPagina"] == 100


class TestFetchPageRetry:
    """Test retry logic for transient failures."""

    @patch('pncp_client.requests.Session.get')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_retry_on_500_server_error(self, mock_sleep, mock_get):
        """Test client retries on 500 server error."""
        # First call fails with 500, second succeeds
        mock_responses = [
            Mock(status_code=500, text="Internal Server Error"),
            Mock(status_code=200)
        ]
        mock_responses[1].json.return_value = {"data": []}
        mock_get.side_effect = mock_responses

        config = RetryConfig(max_retries=2)
        client = PNCPClient(config=config)
        client.fetch_page("2024-01-01", "2024-01-31")

        assert mock_get.call_count == 2
        assert mock_sleep.called

    @patch('pncp_client.requests.Session.get')
    @patch('time.sleep')
    def test_retry_on_503_unavailable(self, mock_sleep, mock_get):
        """Test client retries on 503 service unavailable."""
        mock_responses = [
            Mock(status_code=503, text="Service Unavailable"),
            Mock(status_code=200)
        ]
        mock_responses[1].json.return_value = {"data": []}
        mock_get.side_effect = mock_responses

        config = RetryConfig(max_retries=2)
        client = PNCPClient(config=config)
        client.fetch_page("2024-01-01", "2024-01-31")

        assert mock_get.call_count == 2

    @patch('pncp_client.requests.Session.get')
    @patch('time.sleep')
    def test_max_retries_exceeded_raises_error(self, mock_sleep, mock_get):
        """Test error is raised after max retries exceeded."""
        # Always return 500
        mock_get.return_value = Mock(status_code=500, text="Internal Server Error")

        config = RetryConfig(max_retries=2)
        client = PNCPClient(config=config)

        with pytest.raises(PNCPAPIError, match="Failed after 3 attempts"):
            client.fetch_page("2024-01-01", "2024-01-31")

        # Should try 3 times total (initial + 2 retries)
        assert mock_get.call_count == 3


class TestFetchPageRateLimiting:
    """Test rate limit (429) handling."""

    @patch('pncp_client.requests.Session.get')
    @patch('time.sleep')
    def test_429_respects_retry_after_header(self, mock_sleep, mock_get):
        """Test 429 response respects Retry-After header."""
        mock_responses = [
            Mock(status_code=429, headers={"Retry-After": "5"}),
            Mock(status_code=200)
        ]
        mock_responses[1].json.return_value = {"data": []}
        mock_get.side_effect = mock_responses

        client = PNCPClient()
        client.fetch_page("2024-01-01", "2024-01-31")

        # Check that sleep was called with the Retry-After value
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert 5 in sleep_calls  # Should sleep for 5 seconds

    @patch('pncp_client.requests.Session.get')
    @patch('time.sleep')
    def test_429_uses_default_wait_without_retry_after(self, mock_sleep, mock_get):
        """Test 429 uses default 60s wait when Retry-After header missing."""
        mock_responses = [
            Mock(status_code=429, headers={}),
            Mock(status_code=200)
        ]
        mock_responses[1].json.return_value = {"data": []}
        mock_get.side_effect = mock_responses

        client = PNCPClient()
        client.fetch_page("2024-01-01", "2024-01-31")

        # Should use default 60 second wait
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert 60 in sleep_calls


class TestFetchPageNonRetryableErrors:
    """Test immediate failure for non-retryable errors."""

    @patch('pncp_client.requests.Session.get')
    def test_400_bad_request_fails_immediately(self, mock_get):
        """Test 400 Bad Request fails immediately without retry."""
        mock_get.return_value = Mock(status_code=400, text="Bad Request")

        client = PNCPClient()

        with pytest.raises(PNCPAPIError, match="non-retryable status 400"):
            client.fetch_page("2024-01-01", "2024-01-31")

        # Should only try once (no retries)
        assert mock_get.call_count == 1

    @patch('pncp_client.requests.Session.get')
    def test_404_not_found_fails_immediately(self, mock_get):
        """Test 404 Not Found fails immediately without retry."""
        mock_get.return_value = Mock(status_code=404, text="Not Found")

        client = PNCPClient()

        with pytest.raises(PNCPAPIError, match="non-retryable status 404"):
            client.fetch_page("2024-01-01", "2024-01-31")

        assert mock_get.call_count == 1


class TestFetchPageExceptionRetry:
    """Test retry logic for network exceptions."""

    @patch('pncp_client.requests.Session.get')
    @patch('time.sleep')
    def test_retry_on_connection_error(self, mock_sleep, mock_get):
        """Test client retries on ConnectionError."""
        # First call raises ConnectionError, second succeeds
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {"data": []}
        mock_get.side_effect = [ConnectionError("Network error"), mock_response]

        config = RetryConfig(max_retries=2)
        client = PNCPClient(config=config)
        client.fetch_page("2024-01-01", "2024-01-31")

        assert mock_get.call_count == 2

    @patch('pncp_client.requests.Session.get')
    @patch('time.sleep')
    def test_retry_on_timeout_error(self, mock_sleep, mock_get):
        """Test client retries on TimeoutError."""
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {"data": []}
        mock_get.side_effect = [TimeoutError("Request timeout"), mock_response]

        config = RetryConfig(max_retries=2)
        client = PNCPClient(config=config)
        client.fetch_page("2024-01-01", "2024-01-31")

        assert mock_get.call_count == 2

    @patch('pncp_client.requests.Session.get')
    @patch('time.sleep')
    def test_exception_after_max_retries_raises_error(self, mock_sleep, mock_get):
        """Test exception is raised after max retries for network errors."""
        mock_get.side_effect = ConnectionError("Network error")

        config = RetryConfig(max_retries=2)
        client = PNCPClient(config=config)

        with pytest.raises(PNCPAPIError, match="Failed after 3 attempts"):
            client.fetch_page("2024-01-01", "2024-01-31")

        assert mock_get.call_count == 3
