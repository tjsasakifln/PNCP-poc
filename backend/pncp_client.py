"""Resilient HTTP client for PNCP API."""

import asyncio
import json
import logging
import random
import time
from datetime import date, timedelta
from typing import Any, Callable, Dict, Generator, List

import httpx
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import RetryConfig, DEFAULT_MODALIDADES
from exceptions import PNCPAPIError

logger = logging.getLogger(__name__)


# ============================================================================
# Status Mapping for PNCP API
# ============================================================================

# Mapping from StatusLicitacao enum values to PNCP API parameter values
# Note: Import StatusLicitacao at runtime to avoid circular imports
STATUS_PNCP_MAP = {
    "recebendo_proposta": "recebendo_proposta",
    "em_julgamento": "propostas_encerradas",
    "encerrada": "encerrada",
    "todos": None,  # Don't send status parameter - return all
}


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
        config.base_delay * (config.exponential_base**attempt), config.max_delay
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
            raise_on_status=False,  # We'll handle status codes manually
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        # Set default headers
        session.headers.update({
            "User-Agent": "BidIQ/1.0 (procurement-search; contact@bidiq.com.br)",
            "Accept": "application/json",
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
        modalidade: int,
        uf: str | None = None,
        pagina: int = 1,
        tamanho: int = 20,
    ) -> Dict[str, Any]:
        """
        Fetch a single page of procurement data from PNCP API.

        Args:
            data_inicial: Start date in YYYY-MM-DD format
            data_final: End date in YYYY-MM-DD format
            modalidade: Modality code (codigoModalidadeContratacao), e.g., 6 for Pregão Eletrônico
            uf: Optional state code (e.g., "SP", "RJ")
            pagina: Page number (1-indexed)
            tamanho: Page size (default 20, PNCP API limit)

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

        # Convert dates from YYYY-MM-DD to yyyyMMdd (PNCP API format)
        data_inicial_fmt = data_inicial.replace("-", "")
        data_final_fmt = data_final.replace("-", "")

        params = {
            "dataInicial": data_inicial_fmt,
            "dataFinal": data_final_fmt,
            "codigoModalidadeContratacao": modalidade,
            "pagina": pagina,
            "tamanhoPagina": tamanho,
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
                    url, params=params, timeout=self.config.timeout
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
                    # Validate Content-Type before parsing JSON
                    content_type = response.headers.get("content-type", "")
                    if "json" not in content_type.lower():
                        logger.warning(
                            f"PNCP returned non-JSON response (content-type: {content_type}). "
                            f"Body preview: {response.text[:200]}. "
                            f"Attempt {attempt + 1}/{self.config.max_retries + 1}"
                        )
                        if attempt < self.config.max_retries:
                            delay = calculate_delay(attempt, self.config)
                            time.sleep(delay)
                            continue
                        else:
                            raise PNCPAPIError(
                                f"PNCP returned non-JSON after {self.config.max_retries + 1} attempts. "
                                f"Content-Type: {content_type}"
                            )

                    # Parse JSON with error handling
                    try:
                        data = response.json()
                    except json.JSONDecodeError as e:
                        logger.warning(
                            f"PNCP returned invalid JSON: {e}. "
                            f"Body preview: {response.text[:200]}. "
                            f"Attempt {attempt + 1}/{self.config.max_retries + 1}"
                        )
                        if attempt < self.config.max_retries:
                            delay = calculate_delay(attempt, self.config)
                            time.sleep(delay)
                            continue
                        else:
                            raise PNCPAPIError(
                                f"PNCP returned invalid JSON after {self.config.max_retries + 1} attempts: {e}"
                            ) from e

                    logger.debug(
                        f"Success: fetched page {pagina} "
                        f"({len(data.get('data', []))} items)"
                    )
                    return data

                # No content - empty results (valid response)
                if response.status_code == 204:
                    logger.debug(f"No content (204) for page {pagina} - no results")
                    return {
                        "data": [],
                        "totalRegistros": 0,
                        "totalPaginas": 0,
                        "paginaAtual": pagina,
                        "temProximaPagina": False,
                    }

                # Non-retryable errors - fail immediately
                if response.status_code not in self.config.retryable_status_codes:
                    logger.error(
                        f"PNCP API error: status={response.status_code} "
                        f"url={url} params={params} "
                        f"body={response.text[:500]}"
                    )
                    error_msg = (
                        f"API returned non-retryable status {response.status_code}: "
                        f"{response.text[:200]}"
                    )
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
        raise PNCPAPIError("Unexpected: exhausted retries without raising exception")

    @staticmethod
    def _chunk_date_range(
        data_inicial: str, data_final: str, max_days: int = 30
    ) -> list[tuple[str, str]]:
        """
        Split a date range into chunks of max_days.

        The PNCP API may return incomplete results for large date ranges.
        This method splits the range into smaller windows to ensure
        complete data retrieval.

        Args:
            data_inicial: Start date YYYY-MM-DD
            data_final: End date YYYY-MM-DD
            max_days: Maximum days per chunk (default 30)

        Returns:
            List of (start, end) date string tuples
        """
        d_start = date.fromisoformat(data_inicial)
        d_end = date.fromisoformat(data_final)
        chunks: list[tuple[str, str]] = []

        current = d_start
        while current <= d_end:
            chunk_end = min(current + timedelta(days=max_days - 1), d_end)
            chunks.append((current.isoformat(), chunk_end.isoformat()))
            current = chunk_end + timedelta(days=1)

        return chunks

    def fetch_all(
        self,
        data_inicial: str,
        data_final: str,
        ufs: list[str] | None = None,
        modalidades: list[int] | None = None,
        on_progress: Callable[[int, int, int], None] | None = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Fetch all procurement records with automatic pagination and date chunking.

        Automatically splits date ranges > 30 days into 30-day chunks to avoid
        PNCP API limitations with large ranges.

        Args:
            data_inicial: Start date in YYYY-MM-DD format
            data_final: End date in YYYY-MM-DD format
            ufs: Optional list of state codes (e.g., ["SP", "RJ"])
            modalidades: Optional list of modality codes
            on_progress: Optional callback(current_page, total_pages, items_fetched)

        Yields:
            Dict[str, Any]: Individual procurement record
        """
        # Split large date ranges into 30-day chunks
        date_chunks = self._chunk_date_range(data_inicial, data_final)
        if len(date_chunks) > 1:
            logger.info(
                f"Date range {data_inicial} to {data_final} split into "
                f"{len(date_chunks)} chunks of up to 30 days"
            )

        # Use default modalities if not specified
        modalidades_to_fetch = modalidades or DEFAULT_MODALIDADES

        # Track unique IDs to avoid duplicates across modalities and chunks
        seen_ids: set[str] = set()

        for chunk_idx, (chunk_start, chunk_end) in enumerate(date_chunks):
            if len(date_chunks) > 1:
                logger.info(
                    f"Processing date chunk {chunk_idx + 1}/{len(date_chunks)}: "
                    f"{chunk_start} to {chunk_end}"
                )

            for modalidade in modalidades_to_fetch:
                logger.info(f"Fetching modality {modalidade}")

                # If specific UFs provided, fetch each separately
                if ufs:
                    for uf in ufs:
                        logger.info(f"Fetching modalidade={modalidade}, UF={uf}")
                        try:
                            for item in self._fetch_by_uf(
                                chunk_start, chunk_end, modalidade, uf, on_progress
                            ):
                                normalized = self._normalize_item(item)
                                item_id = normalized.get("numeroControlePNCP", "")
                                if item_id and item_id not in seen_ids:
                                    seen_ids.add(item_id)
                                    yield normalized
                        except PNCPAPIError as e:
                            logger.warning(
                                f"Skipping modalidade={modalidade}, UF={uf}: {e}"
                            )
                            continue
                else:
                    logger.info(f"Fetching modalidade={modalidade}, all UFs")
                    try:
                        for item in self._fetch_by_uf(
                            chunk_start, chunk_end, modalidade, None, on_progress
                        ):
                            normalized = self._normalize_item(item)
                            item_id = normalized.get("numeroControlePNCP", "")
                            if item_id and item_id not in seen_ids:
                                seen_ids.add(item_id)
                                yield normalized
                    except PNCPAPIError as e:
                        logger.warning(
                            f"Skipping modalidade={modalidade}, all UFs: {e}"
                        )
                        continue

        logger.info(
            f"Fetch complete: {len(seen_ids)} unique records across "
            f"{len(modalidades_to_fetch)} modalities and {len(date_chunks)} date chunks"
        )

    @staticmethod
    def _normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten nested PNCP API response into the flat format expected by
        filter.py, excel.py and llm.py.

        The PNCP API nests org/location data inside ``orgaoEntidade`` and
        ``unidadeOrgao`` objects.  The rest of the codebase expects flat
        top-level keys: ``uf``, ``municipio``, ``nomeOrgao``, ``codigoCompra``.

        Also ensures linkSistemaOrigem and linkProcessoEletronico are preserved
        for Excel hyperlinks.
        """
        unidade = item.get("unidadeOrgao") or {}
        orgao = item.get("orgaoEntidade") or {}

        item["uf"] = unidade.get("ufSigla", "")
        item["municipio"] = unidade.get("municipioNome", "")
        item["nomeOrgao"] = orgao.get("razaoSocial", "") or unidade.get("nomeUnidade", "")
        item["codigoCompra"] = item.get("numeroControlePNCP", "")

        # Preserve link fields for Excel generation (already in root level from API)
        # No mapping needed - linkSistemaOrigem and linkProcessoEletronico are already at root

        return item

    def _fetch_by_uf(
        self,
        data_inicial: str,
        data_final: str,
        modalidade: int,
        uf: str | None,
        on_progress: Callable[[int, int, int], None] | None,
        max_pages: int = 500,  # HOTFIX STORY-183: Increased from 50 to 500 (10,000 records per UF+modality)
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Fetch all pages for a specific modality and UF combination.

        This helper method handles pagination for a single modality/UF by following
        the API's `temProximaPagina` flag. It continues fetching pages
        until no more pages are available OR max_pages is reached.

        Args:
            data_inicial: Start date in YYYY-MM-DD format
            data_final: End date in YYYY-MM-DD format
            modalidade: Modality code (codigoModalidadeContratacao)
            uf: State code (e.g., "SP") or None for all states
            on_progress: Optional progress callback
            max_pages: Maximum number of pages to fetch (prevents timeouts, default 500)

        Yields:
            Dict[str, Any]: Individual procurement record
        """
        pagina = 1
        items_fetched = 0
        total_pages = None

        while pagina <= max_pages:
            logger.debug(
                f"Fetching page {pagina} for modalidade={modalidade}, UF={uf or 'ALL'} "
                f"(date range: {data_inicial} to {data_final})"
            )

            response = self.fetch_page(
                data_inicial=data_inicial,
                data_final=data_final,
                modalidade=modalidade,
                uf=uf,
                pagina=pagina,
            )

            # Extract pagination metadata
            # PNCP API uses: numeroPagina, totalPaginas, paginasRestantes, empty
            data = response.get("data", [])
            total_pages = response.get("totalPaginas", 1)
            total_registros = response.get("totalRegistros", 0)
            paginas_restantes = response.get("paginasRestantes", 0)
            tem_proxima = paginas_restantes > 0

            # Log page info
            logger.info(
                f"Page {pagina}/{total_pages}: {len(data)} items "
                f"(total records: {total_registros})"
            )

            # Call progress callback if provided
            if on_progress:
                on_progress(pagina, total_pages, items_fetched + len(data))

            # Yield individual items
            for item in data:
                yield item
                items_fetched += 1

            # Check if there are more pages
            if not tem_proxima:
                logger.info(
                    f"[SUCCESS] Fetch complete for modalidade={modalidade}, UF={uf or 'ALL'}: "
                    f"{items_fetched} total items across {pagina} pages"
                )
                break

            # HOTFIX STORY-183: Enhanced warning when max_pages limit reached
            if pagina >= max_pages:
                logger.warning(
                    f"[WARN] MAX_PAGES ({max_pages}) ATINGIDO! "
                    f"UF={uf or 'ALL'}, modalidade={modalidade}. "
                    f"Fetched {items_fetched} items out of {total_registros} total. "
                    f"Remaining pages: {paginas_restantes}. "
                    f"Resultados podem estar incompletos. "
                    f"Considere aumentar max_pages ou otimizar filtros."
                )
                break

            # Move to next page
            pagina += 1

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


# ============================================================================
# Async Parallel Search Client
# ============================================================================

class AsyncPNCPClient:
    """
    Async HTTP client for PNCP API with parallel UF fetching.

    Uses httpx for async HTTP requests and asyncio.Semaphore for
    concurrency control. This enables fetching multiple UFs in parallel
    while respecting rate limits.

    Example:
        >>> async with AsyncPNCPClient() as client:
        ...     results = await client.buscar_todas_ufs_paralelo(
        ...         ufs=["SP", "RJ", "MG"],
        ...         data_inicial="2026-01-01",
        ...         data_final="2026-01-31"
        ...     )
    """

    BASE_URL = "https://pncp.gov.br/api/consulta/v1"

    def __init__(
        self,
        config: RetryConfig | None = None,
        max_concurrent: int = 10
    ):
        """
        Initialize async PNCP client.

        Args:
            config: Retry configuration (uses defaults if not provided)
            max_concurrent: Maximum concurrent requests (default 10)
        """
        self.config = config or RetryConfig()
        self.max_concurrent = max_concurrent
        self._semaphore: asyncio.Semaphore | None = None
        self._client: httpx.AsyncClient | None = None
        self._request_count = 0
        self._last_request_time = 0.0

    async def __aenter__(self) -> "AsyncPNCPClient":
        """Async context manager entry."""
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout),
            headers={
                "User-Agent": "BidIQ/1.0 (procurement-search; contact@bidiq.com.br)",
                "Accept": "application/json",
            },
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
        logger.debug(f"Async session closed. Total requests made: {self._request_count}")

    async def _rate_limit(self) -> None:
        """
        Enforce rate limiting: minimum 100ms between requests.

        This is applied per-request, not per-UF, to respect PNCP's rate limits
        even when making parallel requests.
        """
        MIN_INTERVAL = 0.1  # 100ms

        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - self._last_request_time
        if elapsed < MIN_INTERVAL:
            await asyncio.sleep(MIN_INTERVAL - elapsed)

        self._last_request_time = asyncio.get_event_loop().time()
        self._request_count += 1

    async def _fetch_page_async(
        self,
        data_inicial: str,
        data_final: str,
        modalidade: int,
        uf: str | None = None,
        pagina: int = 1,
        tamanho: int = 20,
        status: str | None = None,
    ) -> Dict[str, Any]:
        """
        Fetch a single page of procurement data asynchronously.

        Args:
            data_inicial: Start date in YYYY-MM-DD format
            data_final: End date in YYYY-MM-DD format
            modalidade: Modality code
            uf: Optional state code
            pagina: Page number
            tamanho: Page size
            status: Optional status filter (PNCP API value)

        Returns:
            API response dictionary
        """
        if self._client is None:
            raise RuntimeError("Client not initialized. Use async context manager.")

        await self._rate_limit()

        # Convert dates from YYYY-MM-DD to yyyyMMdd (PNCP API format)
        data_inicial_fmt = data_inicial.replace("-", "")
        data_final_fmt = data_final.replace("-", "")

        params = {
            "dataInicial": data_inicial_fmt,
            "dataFinal": data_final_fmt,
            "codigoModalidadeContratacao": modalidade,
            "pagina": pagina,
            "tamanhoPagina": tamanho,
        }

        if uf:
            params["uf"] = uf

        # Add status parameter if provided (not "todos")
        if status:
            params["situacaoCompra"] = status

        url = f"{self.BASE_URL}/contratacoes/publicacao"

        for attempt in range(self.config.max_retries + 1):
            try:
                logger.debug(
                    f"Async request {url} params={params} attempt={attempt + 1}/"
                    f"{self.config.max_retries + 1}"
                )

                response = await self._client.get(url, params=params)

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited (429). Waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue

                # Success
                if response.status_code == 200:
                    # Validate Content-Type before parsing JSON
                    content_type = response.headers.get("content-type", "")
                    if "json" not in content_type.lower():
                        logger.warning(
                            f"PNCP returned non-JSON response (content-type: {content_type}). "
                            f"Body preview: {response.text[:200]}. "
                            f"Attempt {attempt + 1}/{self.config.max_retries + 1}"
                        )
                        if attempt < self.config.max_retries:
                            delay = min(
                                self.config.base_delay * (self.config.exponential_base ** attempt),
                                self.config.max_delay
                            )
                            if self.config.jitter:
                                delay *= random.uniform(0.5, 1.5)
                            await asyncio.sleep(delay)
                            continue
                        else:
                            raise PNCPAPIError(
                                f"PNCP returned non-JSON after {self.config.max_retries + 1} attempts. "
                                f"Content-Type: {content_type}"
                            )

                    # Parse JSON with error handling
                    try:
                        data = response.json()
                    except json.JSONDecodeError as e:
                        logger.warning(
                            f"PNCP returned invalid JSON: {e}. "
                            f"Body preview: {response.text[:200]}. "
                            f"Attempt {attempt + 1}/{self.config.max_retries + 1}"
                        )
                        if attempt < self.config.max_retries:
                            delay = min(
                                self.config.base_delay * (self.config.exponential_base ** attempt),
                                self.config.max_delay
                            )
                            if self.config.jitter:
                                delay *= random.uniform(0.5, 1.5)
                            await asyncio.sleep(delay)
                            continue
                        else:
                            raise PNCPAPIError(
                                f"PNCP returned invalid JSON after {self.config.max_retries + 1} attempts: {e}"
                            ) from e

                    return data

                # No content
                if response.status_code == 204:
                    return {
                        "data": [],
                        "totalRegistros": 0,
                        "totalPaginas": 0,
                        "paginaAtual": pagina,
                        "temProximaPagina": False,
                    }

                # Non-retryable error
                if response.status_code not in self.config.retryable_status_codes:
                    raise PNCPAPIError(
                        f"API returned non-retryable status {response.status_code}"
                    )

                # Retryable error - wait and retry
                if attempt < self.config.max_retries:
                    delay = min(
                        self.config.base_delay * (self.config.exponential_base ** attempt),
                        self.config.max_delay
                    )
                    if self.config.jitter:
                        delay *= random.uniform(0.5, 1.5)
                    logger.warning(
                        f"Error {response.status_code}. Retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise PNCPAPIError(
                        f"Failed after {self.config.max_retries + 1} attempts"
                    )

            except httpx.TimeoutException as e:
                if attempt < self.config.max_retries:
                    delay = min(
                        self.config.base_delay * (self.config.exponential_base ** attempt),
                        self.config.max_delay
                    )
                    logger.warning(f"Timeout. Retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                else:
                    raise PNCPAPIError(f"Timeout after {self.config.max_retries + 1} attempts") from e

            except httpx.HTTPError as e:
                if attempt < self.config.max_retries:
                    delay = min(
                        self.config.base_delay * (self.config.exponential_base ** attempt),
                        self.config.max_delay
                    )
                    logger.warning(f"HTTP error: {e}. Retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                else:
                    raise PNCPAPIError(f"HTTP error after retries: {e}") from e

        raise PNCPAPIError("Unexpected: exhausted retries without result")

    async def _fetch_uf_all_pages(
        self,
        uf: str,
        data_inicial: str,
        data_final: str,
        modalidades: List[int],
        status: str | None = None,
        max_pages: int = 500,  # HOTFIX STORY-183: Increased from 50 to 500
    ) -> List[Dict[str, Any]]:
        """
        Fetch all pages for a single UF across all modalities.

        Args:
            uf: State code
            data_inicial: Start date
            data_final: End date
            modalidades: List of modality codes
            status: Optional status filter
            max_pages: Maximum pages to fetch per modality

        Returns:
            List of procurement records
        """
        async with self._semaphore:
            all_items: List[Dict[str, Any]] = []
            seen_ids: set = set()

            for modalidade in modalidades:
                pagina = 1

                while pagina <= max_pages:
                    try:
                        response = await self._fetch_page_async(
                            data_inicial=data_inicial,
                            data_final=data_final,
                            modalidade=modalidade,
                            uf=uf,
                            pagina=pagina,
                            status=status,
                        )

                        data = response.get("data", [])
                        paginas_restantes = response.get("paginasRestantes", 0)

                        for item in data:
                            item_id = item.get("numeroControlePNCP", "")
                            if item_id and item_id not in seen_ids:
                                seen_ids.add(item_id)
                                # Normalize item
                                normalized = PNCPClient._normalize_item(item)
                                all_items.append(normalized)

                        if paginas_restantes <= 0:
                            break

                        # HOTFIX STORY-183: Enhanced warning when approaching max_pages
                        if pagina >= max_pages and paginas_restantes > 0:
                            logger.warning(
                                f"⚠️ MAX_PAGES ({max_pages}) reached for UF={uf}, modalidade={modalidade}. "
                                f"Fetched {len([i for i in all_items if i.get('uf') == uf])} items. "
                                f"Remaining pages: {paginas_restantes}"
                            )

                        pagina += 1

                    except PNCPAPIError as e:
                        logger.warning(f"Error fetching UF={uf}, modalidade={modalidade}: {e}")
                        break

            logger.info(f"Fetched {len(all_items)} items for UF={uf}")
            return all_items

    async def buscar_todas_ufs_paralelo(
        self,
        ufs: List[str],
        data_inicial: str,
        data_final: str,
        modalidades: List[int] | None = None,
        status: str | None = None,
        max_pages_per_uf: int = 500,  # HOTFIX STORY-183: Increased from 50 to 500
        on_uf_complete: Callable[[str, int], Any] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Busca licitações em múltiplas UFs em paralelo com limite de concorrência.

        This is the main method for parallel UF fetching. It creates one task
        per UF and executes them concurrently (up to max_concurrent).

        Args:
            ufs: List of state codes (e.g., ["SP", "RJ", "MG"])
            data_inicial: Start date in YYYY-MM-DD format
            data_final: End date in YYYY-MM-DD format
            modalidades: List of modality codes (default: [6] - Pregão Eletrônico)
            status: Status filter (StatusLicitacao value or None)
            max_pages_per_uf: Maximum pages to fetch per UF/modality

        Returns:
            List of all procurement records (deduplicated)

        Example:
            >>> async with AsyncPNCPClient(max_concurrent=10) as client:
            ...     results = await client.buscar_todas_ufs_paralelo(
            ...         ufs=["SP", "RJ", "MG", "BA", "RS"],
            ...         data_inicial="2026-01-01",
            ...         data_final="2026-01-15",
            ...         status="recebendo_proposta"
            ...     )
            >>> len(results)
            1523
        """
        import time as sync_time
        start_time = sync_time.time()

        # Use default modalities if not specified
        modalidades = modalidades or DEFAULT_MODALIDADES

        # Map status to PNCP API value
        pncp_status = STATUS_PNCP_MAP.get(status) if status else None

        logger.info(
            f"Starting parallel fetch for {len(ufs)} UFs "
            f"(max_concurrent={self.max_concurrent}, status={status})"
        )

        # Per-UF timeout: 90s prevents one slow state from blocking everything
        PER_UF_TIMEOUT = 90  # seconds

        # Create tasks for each UF with optional progress callback
        async def _fetch_with_callback(uf: str) -> List[Dict[str, Any]]:
            try:
                result = await asyncio.wait_for(
                    self._fetch_uf_all_pages(
                        uf=uf,
                        data_inicial=data_inicial,
                        data_final=data_final,
                        modalidades=modalidades,
                        status=pncp_status,
                        max_pages=max_pages_per_uf,
                    ),
                    timeout=PER_UF_TIMEOUT,
                )
            except asyncio.TimeoutError:
                logger.warning(f"UF={uf} timed out after {PER_UF_TIMEOUT}s — skipping")
                result = []
            if on_uf_complete:
                try:
                    maybe_coro = on_uf_complete(uf, len(result))
                    if asyncio.iscoroutine(maybe_coro):
                        await maybe_coro
                except Exception as cb_err:
                    logger.warning(f"on_uf_complete callback error for UF={uf}: {cb_err}")
            return result

        tasks = [_fetch_with_callback(uf) for uf in ufs]

        # Execute all tasks concurrently (semaphore limits actual concurrency)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results and handle errors
        all_items: List[Dict[str, Any]] = []
        errors = 0

        for uf, result in zip(ufs, results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching UF={uf}: {result}")
                errors += 1
            else:
                all_items.extend(result)

        elapsed = sync_time.time() - start_time
        logger.info(
            f"Parallel fetch complete: {len(all_items)} items from {len(ufs)} UFs "
            f"in {elapsed:.2f}s ({errors} errors)"
        )

        return all_items


async def buscar_todas_ufs_paralelo(
    ufs: List[str],
    data_inicial: str,
    data_final: str,
    modalidades: List[int] | None = None,
    status: str | None = None,
    max_concurrent: int = 10,
    on_uf_complete: Callable[[str, int], Any] | None = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function for parallel UF search.

    Creates an AsyncPNCPClient and performs parallel search in a single call.
    Use this for simple cases where you don't need to reuse the client.

    Args:
        ufs: List of state codes
        data_inicial: Start date YYYY-MM-DD
        data_final: End date YYYY-MM-DD
        modalidades: Optional modality codes
        status: Optional status filter
        max_concurrent: Maximum concurrent requests (default 10)
        on_uf_complete: Optional async callback(uf, items_count) called per UF

    Returns:
        List of procurement records

    Example:
        >>> results = await buscar_todas_ufs_paralelo(
        ...     ufs=["SP", "RJ"],
        ...     data_inicial="2026-01-01",
        ...     data_final="2026-01-15"
        ... )
    """
    async with AsyncPNCPClient(max_concurrent=max_concurrent) as client:
        return await client.buscar_todas_ufs_paralelo(
            ufs=ufs,
            data_inicial=data_inicial,
            data_final=data_final,
            modalidades=modalidades,
            status=status,
            on_uf_complete=on_uf_complete,
        )
