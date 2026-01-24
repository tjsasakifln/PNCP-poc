"""Resilient HTTP client for PNCP API."""
import logging
import random
import time
from typing import Dict, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import RetryConfig
from exceptions import PNCPAPIError, PNCPRateLimitError

logger = logging.getLogger(__name__)


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """
    Calculate exponential backoff delay with optional jitter.

    Args:
        attempt: Current retry attempt number (0-indexed)
        config: Retry configuration

    Returns:
        Delay in seconds

    Example:
        With base_delay=2, exponential_base=2, max_delay=60:
        - Attempt 0: 2s
        - Attempt 1: 4s
        - Attempt 2: 8s
        - Attempt 3: 16s
        - Attempt 4: 32s
        - Attempt 5: 60s (capped)
    """
    delay = min(
        config.base_delay * (config.exponential_base ** attempt),
        config.max_delay
    )

    if config.jitter:
        # Add ±50% jitter to prevent thundering herd
        delay *= random.uniform(0.5, 1.5)

    return delay


class PNCPClient:
    """Resilient HTTP client for PNCP API with retry logic and rate limiting."""

    BASE_URL = "https://pncp.gov.br/api/consulta/v1"

    def __init__(self, config: RetryConfig | None = None):
        """
        Initialize PNCP client.

        Args:
            config: Retry configuration (uses defaults if not provided)
        """
        self.config = config or RetryConfig()
        self.session = self._create_session()
        self._request_count = 0
        self._last_request_time = 0.0

    def _create_session(self) -> requests.Session:
        """
        Create HTTP session with automatic retry strategy.

        Returns:
            Configured requests.Session with retry adapter
        """
        session = requests.Session()

        # Configure retry strategy using urllib3
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.base_delay,
            status_forcelist=self.config.retryable_status_codes,
            allowed_methods=["GET"],
            raise_on_status=False  # We'll handle status codes manually
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        # Set default headers
        session.headers.update({
            "User-Agent": "BidIQ-POC/0.2",
            "Accept": "application/json"
        })

        return session

    def _rate_limit(self) -> None:
        """
        Enforce rate limiting: maximum 10 requests per second.

        Sleeps if necessary to maintain minimum interval between requests.
        """
        MIN_INTERVAL = 0.1  # 100ms = 10 requests/second

        elapsed = time.time() - self._last_request_time
        if elapsed < MIN_INTERVAL:
            sleep_time = MIN_INTERVAL - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.3f}s")
            time.sleep(sleep_time)

        self._last_request_time = time.time()
        self._request_count += 1

    def fetch_page(
        self,
        data_inicial: str,
        data_final: str,
        uf: str | None = None,
        pagina: int = 1,
        tamanho: int = 500
    ) -> Dict[str, Any]:
        """
        Fetch a single page of procurement data from PNCP API.

        Args:
            data_inicial: Start date in YYYY-MM-DD format
            data_final: End date in YYYY-MM-DD format
            uf: Optional state code (e.g., "SP", "RJ")
            pagina: Page number (1-indexed)
            tamanho: Page size (max 500)

        Returns:
            API response as dictionary containing:
                - data: List of procurement records
                - totalRegistros: Total number of records
                - totalPaginas: Total number of pages
                - paginaAtual: Current page number
                - temProximaPagina: Boolean indicating if more pages exist

        Raises:
            PNCPAPIError: On non-retryable errors or after max retries
            PNCPRateLimitError: If rate limit persists after retries
        """
        self._rate_limit()

        params = {
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "pagina": pagina,
            "tamanhoPagina": tamanho
        }

        if uf:
            params["uf"] = uf

        url = f"{self.BASE_URL}/contratacoes/publicacao"

        for attempt in range(self.config.max_retries + 1):
            try:
                logger.debug(
                    f"Request {url} params={params} attempt={attempt + 1}/"
                    f"{self.config.max_retries + 1}"
                )

                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config.timeout
                )

                # Handle rate limiting specifically
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(
                        f"Rate limited (429). Waiting {retry_after}s "
                        f"(Retry-After header)"
                    )
                    time.sleep(retry_after)
                    continue

                # Success case
                if response.status_code == 200:
                    logger.debug(
                        f"Success: fetched page {pagina} "
                        f"({len(response.json().get('data', []))} items)"
                    )
                    return response.json()

                # Non-retryable errors - fail immediately
                if response.status_code not in self.config.retryable_status_codes:
                    error_msg = (
                        f"API returned non-retryable status {response.status_code}: "
                        f"{response.text[:200]}"
                    )
                    logger.error(error_msg)
                    raise PNCPAPIError(error_msg)

                # Retryable errors - wait and retry
                if attempt < self.config.max_retries:
                    delay = calculate_delay(attempt, self.config)
                    logger.warning(
                        f"Error {response.status_code}. "
                        f"Attempt {attempt + 1}/{self.config.max_retries + 1}. "
                        f"Retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)
                else:
                    # Last attempt failed
                    error_msg = (
                        f"Failed after {self.config.max_retries + 1} attempts. "
                        f"Last status: {response.status_code}"
                    )
                    logger.error(error_msg)
                    raise PNCPAPIError(error_msg)

            except self.config.retryable_exceptions as e:
                if attempt < self.config.max_retries:
                    delay = calculate_delay(attempt, self.config)
                    logger.warning(
                        f"Exception {type(e).__name__}: {e}. "
                        f"Attempt {attempt + 1}/{self.config.max_retries + 1}. "
                        f"Retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)
                else:
                    error_msg = (
                        f"Failed after {self.config.max_retries + 1} attempts. "
                        f"Last exception: {type(e).__name__}: {e}"
                    )
                    logger.error(error_msg)
                    raise PNCPAPIError(error_msg) from e

        # Should never reach here, but just in case
        raise PNCPAPIError(
            f"Unexpected: exhausted retries without raising exception"
        )

    def close(self) -> None:
        """Close the HTTP session and cleanup resources."""
        self.session.close()
        logger.debug(f"Session closed. Total requests made: {self._request_count}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session."""
        self.close()
