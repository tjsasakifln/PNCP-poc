"""Resilient HTTP client for PNCP API."""

import asyncio
import json
import logging
import os
import random
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Callable, Dict, Generator, List, Optional

import httpx
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import RetryConfig, DEFAULT_MODALIDADES, MODALIDADES_EXCLUIDAS
from exceptions import PNCPAPIError
from middleware import request_id_var

logger = logging.getLogger(__name__)


# ============================================================================
# PNCP Degraded Error (STORY-252 AC8)
# ============================================================================

class PNCPDegradedError(PNCPAPIError):
    """Raised when PNCP circuit breaker is in degraded state."""
    pass


# ============================================================================
# Circuit Breaker (STORY-252 AC8)
# ============================================================================

# Configurable via environment variables (GTM-FIX-005)
PNCP_CIRCUIT_BREAKER_THRESHOLD: int = int(
    os.environ.get("PNCP_CIRCUIT_BREAKER_THRESHOLD", "50")  # 27 UFs × 4 mods = 108 slots; 18% ≈ 20 → raised to 50
)
PNCP_CIRCUIT_BREAKER_COOLDOWN: int = int(
    os.environ.get("PNCP_CIRCUIT_BREAKER_COOLDOWN", "120")
)
PCP_CIRCUIT_BREAKER_THRESHOLD: int = int(
    os.environ.get("PCP_CIRCUIT_BREAKER_THRESHOLD", "30")  # Conservative: PCP API stability unknown
)
PCP_CIRCUIT_BREAKER_COOLDOWN: int = int(
    os.environ.get("PCP_CIRCUIT_BREAKER_COOLDOWN", "120")
)

# Per-modality timeout (STORY-252 AC6) — configurable
PNCP_TIMEOUT_PER_MODALITY: float = float(
    os.environ.get("PNCP_TIMEOUT_PER_MODALITY", "120")  # Raised from 15→120: tamanhoPagina=50 needs ~10x more pages
)

# Modality retry on timeout (STORY-252 AC9)
PNCP_MODALITY_RETRY_BACKOFF: float = float(
    os.environ.get("PNCP_MODALITY_RETRY_BACKOFF", "3.0")
)

# Per-UF timeout (GTM-FIX-029 AC1/AC5) — configurable
# Calculation: 4 modalities × ~15s/mod (with retry) = ~60s + 30s margin = 90s
PNCP_TIMEOUT_PER_UF: float = float(
    os.environ.get("PNCP_TIMEOUT_PER_UF", "90")
)
# Degraded mode per-UF timeout (GTM-FIX-029 AC2)
PNCP_TIMEOUT_PER_UF_DEGRADED: float = float(
    os.environ.get("PNCP_TIMEOUT_PER_UF_DEGRADED", "120")
)

# GTM-FIX-031: Phased UF batching — reduces PNCP API pressure
PNCP_BATCH_SIZE: int = int(os.environ.get("PNCP_BATCH_SIZE", "5"))
PNCP_BATCH_DELAY_S: float = float(os.environ.get("PNCP_BATCH_DELAY_S", "2.0"))

# UFs ordered by population for degraded priority (STORY-257A AC1)
UFS_BY_POPULATION = ["SP", "RJ", "MG", "BA", "PR", "RS", "PE", "CE", "SC", "GO",
                      "PA", "MA", "AM", "ES", "PB", "RN", "MT", "AL", "PI", "DF",
                      "MS", "SE", "RO", "TO", "AC", "AP", "RR"]


@dataclass
class ParallelFetchResult:
    """Structured return from buscar_todas_ufs_paralelo with per-UF metadata."""
    items: List[Dict[str, Any]]
    succeeded_ufs: List[str]
    failed_ufs: List[str]
    truncated_ufs: List[str] = field(default_factory=list)  # GTM-FIX-004: UFs that hit max_pages limit


class PNCPCircuitBreaker:
    """Circuit breaker for API sources to prevent cascading failures.

    After ``threshold`` consecutive timeouts, the circuit breaker marks the
    source as *degraded* for ``cooldown_seconds``. While degraded, callers
    should skip that source and use alternatives.

    Each source (PNCP, PCP, etc.) gets its own named instance so failures
    in one source don't cascade to others (GTM-FIX-005 AC9).

    Thread-safety: asyncio.Lock around state mutations.

    Attributes:
        name: Identifier for this circuit breaker instance (e.g. "pncp", "pcp").
        consecutive_failures: Running count of consecutive timeout failures.
        degraded_until: Unix timestamp until which source is considered degraded.
        threshold: Number of consecutive failures before tripping.
        cooldown_seconds: Duration in seconds to stay degraded after tripping.
    """

    def __init__(
        self,
        name: str = "pncp",
        threshold: int = PNCP_CIRCUIT_BREAKER_THRESHOLD,
        cooldown_seconds: int = PNCP_CIRCUIT_BREAKER_COOLDOWN,
    ):
        self.name = name
        self.threshold = threshold
        self.cooldown_seconds = cooldown_seconds
        self.consecutive_failures: int = 0
        self.degraded_until: Optional[float] = None
        self._lock = asyncio.Lock()

    @property
    def is_degraded(self) -> bool:
        """Return True if the circuit breaker is currently in degraded state.

        Read-only check — no side effects. Use try_recover() to actually reset.
        """
        if self.degraded_until is None:
            return False
        if time.time() >= self.degraded_until:
            return False  # Cooldown expired, but don't mutate here
        return True

    async def record_failure(self) -> None:
        """Record a timeout/failure. Trips the breaker after ``threshold`` consecutive failures."""
        async with self._lock:
            self.consecutive_failures += 1
            logger.debug(
                f"Circuit breaker [{self.name}]: failure #{self.consecutive_failures} "
                f"(threshold={self.threshold})"
            )
            if self.consecutive_failures >= self.threshold and not self.is_degraded:
                self.degraded_until = time.time() + self.cooldown_seconds
                logger.warning(
                    f"Circuit breaker [{self.name}] TRIPPED after {self.consecutive_failures} "
                    f"consecutive failures — degraded for {self.cooldown_seconds}s"
                )

    async def record_success(self) -> None:
        """Record a successful request. Resets the failure counter."""
        async with self._lock:
            if self.consecutive_failures > 0:
                logger.debug(
                    f"Circuit breaker [{self.name}]: success after {self.consecutive_failures} "
                    f"failures — resetting counter"
                )
            self.consecutive_failures = 0

    async def try_recover(self) -> bool:
        """Check if cooldown has expired and reset if so. Must be called with await.

        Returns True if the breaker was reset (recovered), False if still degraded.
        """
        if self.degraded_until is None:
            return True  # Already healthy

        if time.time() < self.degraded_until:
            return False  # Still in cooldown

        try:
            await asyncio.wait_for(self._lock.acquire(), timeout=1.0)
            try:
                # Double-check under lock
                if self.degraded_until is not None and time.time() >= self.degraded_until:
                    self.degraded_until = None
                    self.consecutive_failures = 0
                    logger.info(
                        f"Circuit breaker [{self.name}] cooldown expired — resetting to healthy"
                    )
                    return True
            finally:
                self._lock.release()
        except asyncio.TimeoutError:
            logger.warning(
                f"Circuit breaker [{self.name}] lock timeout in try_recover — "
                f"proceeding with current state"
            )

        return not self.is_degraded

    def reset(self) -> None:
        """Manually reset the circuit breaker (for testing or admin use)."""
        self.consecutive_failures = 0
        self.degraded_until = None


# Module-level singletons — one per data source (GTM-FIX-005 AC9)
_circuit_breaker = PNCPCircuitBreaker(
    name="pncp",
    threshold=PNCP_CIRCUIT_BREAKER_THRESHOLD,
    cooldown_seconds=PNCP_CIRCUIT_BREAKER_COOLDOWN,
)
_pcp_circuit_breaker = PNCPCircuitBreaker(
    name="pcp",
    threshold=PCP_CIRCUIT_BREAKER_THRESHOLD,
    cooldown_seconds=PCP_CIRCUIT_BREAKER_COOLDOWN,
)


def get_circuit_breaker(source: str = "pncp") -> PNCPCircuitBreaker:
    """Return the circuit breaker singleton for a given data source.

    Args:
        source: "pncp" (default) or "pcp".
    """
    if source == "pcp":
        return _pcp_circuit_breaker
    return _circuit_breaker


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
        self._request_count = 0  # Per-session counter; reset not needed as each client instance is short-lived
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

        # Set default headers (X-Request-ID is added per-request in fetch_page)
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
        tamanho: int = 50,  # PNCP API max (reduced from 500 to 50 by PNCP ~Feb 2026)
    ) -> Dict[str, Any]:
        """
        Fetch a single page of procurement data from PNCP API.

        Args:
            data_inicial: Start date in YYYY-MM-DD format
            data_final: End date in YYYY-MM-DD format
            modalidade: Modality code (codigoModalidadeContratacao), e.g., 6 for Pregão Eletrônico
            uf: Optional state code (e.g., "SP", "RJ")
            pagina: Page number (1-indexed)
            tamanho: Page size (default 50, PNCP API max as of Feb 2026)

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

        # STORY-226 AC23: Forward X-Request-ID for distributed tracing
        req_id = request_id_var.get("-")
        headers = {}
        if req_id and req_id != "-":
            headers["X-Request-ID"] = req_id

        for attempt in range(self.config.max_retries + 1):
            try:
                logger.debug(
                    f"Request {url} params={params} attempt={attempt + 1}/"
                    f"{self.config.max_retries + 1}"
                )

                response = self.session.get(
                    url, params=params, timeout=self.config.timeout,
                    headers=headers,
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

        # Use default modalities if not specified; always filter out excluded
        modalidades_to_fetch = modalidades or DEFAULT_MODALIDADES
        modalidades_to_fetch = [m for m in modalidades_to_fetch if m not in MODALIDADES_EXCLUIDAS]

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
        self._request_count = 0  # Per-session counter; reset not needed as each client instance is short-lived
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

    async def health_canary(self) -> bool:
        """Run a lightweight probe to verify PNCP API is responsive (STORY-252 AC10).

        Sends a single request for UF=SP, modality 6 (Pregao Eletronico),
        page 1 only, with a tight 5-second timeout.

        If the canary fails, the module-level circuit breaker is set to degraded
        and a warning is logged (AC11).

        Returns:
            ``True`` if PNCP responded successfully, ``False`` otherwise.
        """
        CANARY_TIMEOUT = 5.0  # seconds

        if self._client is None:
            raise RuntimeError("Client not initialized. Use async context manager.")

        try:
            params = {
                "dataInicial": date.today().strftime("%Y%m%d"),
                "dataFinal": date.today().strftime("%Y%m%d"),
                "codigoModalidadeContratacao": 6,
                "pagina": 1,
                "tamanhoPagina": 10,
                "uf": "SP",
            }
            url = f"{self.BASE_URL}/contratacoes/publicacao"

            response = await asyncio.wait_for(
                self._client.get(url, params=params),
                timeout=CANARY_TIMEOUT,
            )

            if response.status_code in (200, 204):
                logger.info("PNCP health canary: OK")
                await _circuit_breaker.record_success()
                return True

            # NEW: Distinguish 4xx from 5xx
            if 400 <= response.status_code < 500:
                # Client error — NOT a server issue, don't trip breaker
                logger.warning(
                    f"PNCP health canary: client error {response.status_code} "
                    f"body={response.text[:200]} — NOT tripping circuit breaker"
                )
                return True  # Proceed with normal search

            logger.warning(
                f"PNCP health canary: server error {response.status_code}"
            )
        except (asyncio.TimeoutError, httpx.TimeoutException):
            logger.warning(
                "WARNING: PNCP health check failed (timeout) "
                "— skipping PNCP for this search, using alternative sources"
            )
        except (httpx.HTTPError, Exception) as exc:
            logger.warning(
                f"WARNING: PNCP health check failed ({type(exc).__name__}: {exc}) "
                "— skipping PNCP for this search, using alternative sources"
            )

        # Canary failed — trip circuit breaker
        await _circuit_breaker.record_failure()
        logger.warning(
            "PNCP circuit breaker failure recorded due to health canary failure"
        )
        return False

    async def _rate_limit(self) -> None:
        """
        Enforce rate limiting: minimum 100ms between requests.

        This is applied per-request, not per-UF, to respect PNCP's rate limits
        even when making parallel requests.
        """
        MIN_INTERVAL = 0.1  # 100ms

        current_time = asyncio.get_running_loop().time()
        elapsed = current_time - self._last_request_time
        if elapsed < MIN_INTERVAL:
            await asyncio.sleep(MIN_INTERVAL - elapsed)

        self._last_request_time = asyncio.get_running_loop().time()
        self._request_count += 1

    async def _fetch_page_async(
        self,
        data_inicial: str,
        data_final: str,
        modalidade: int,
        uf: str | None = None,
        pagina: int = 1,
        tamanho: int = 50,  # PNCP API max (reduced from 500 to 50 by PNCP ~Feb 2026)
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
            tamanho: Page size (default 50, PNCP API max as of Feb 2026)
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

                # STORY-226 AC23: Forward X-Request-ID for distributed tracing
                req_id = request_id_var.get("-")
                extra_headers = {}
                if req_id and req_id != "-":
                    extra_headers["X-Request-ID"] = req_id

                response = await self._client.get(
                    url, params=params, headers=extra_headers
                )

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

                # GTM-FIX-029 AC12-AC15: Special 422 handling — max 1 retry, log body, circuit breaker
                if response.status_code == 422:
                    body_preview = response.text[:500] if response.text else "(empty)"
                    uf_param = params.get("uf", "?")
                    mod_param = params.get("codigoModalidadeContratacao", "?")
                    if attempt < 1:  # AC12: max 1 retry for 422 (not full max_retries)
                        logger.warning(
                            f"PNCP 422 for UF={uf_param} mod={mod_param} "
                            f"(attempt {attempt + 1}/2). Body: {body_preview}. Retrying once..."
                        )
                        await asyncio.sleep(self.config.base_delay)
                        continue
                    else:
                        # AC13: Log complete response after retry exhausted
                        logger.warning(
                            f"PNCP 422 persisted for UF={uf_param} mod={mod_param} "
                            f"after 1 retry. Body: {body_preview}"
                        )
                        # AC14: Count as circuit breaker failure
                        await _circuit_breaker.record_failure()
                        # AC15: Metric tag for diagnostics
                        logger.info(
                            f"pncp_422_count uf={uf_param} modality={mod_param}"
                        )
                        raise PNCPAPIError(
                            f"PNCP 422 after 1 retry for UF={uf_param} mod={mod_param}"
                        )

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

    async def _fetch_single_modality(
        self,
        uf: str,
        data_inicial: str,
        data_final: str,
        modalidade: int,
        status: str | None = None,
        max_pages: int = 500,
    ) -> tuple[List[Dict[str, Any]], bool]:
        """Fetch all pages for a single UF + single modality.

        This is the inner loop extracted from ``_fetch_uf_all_pages`` so that
        each modality can be wrapped with its own timeout (STORY-252 AC6).

        Args:
            uf: State code (e.g. "SP").
            data_inicial: Start date YYYY-MM-DD.
            data_final: End date YYYY-MM-DD.
            modalidade: Modality code.
            status: Optional PNCP status filter value.
            max_pages: Maximum pages per modality.

        Returns:
            Tuple of (items, was_truncated). was_truncated is True when
            max_pages was hit while more pages remained (GTM-FIX-004).
        """
        items: List[Dict[str, Any]] = []
        seen_ids: set[str] = set()
        pagina = 1
        was_truncated = False

        while pagina <= max_pages:
            try:
                response = await self._fetch_page_async(
                    data_inicial=data_inicial,
                    data_final=data_final,
                    modalidade=modalidade,
                    uf=uf,
                    pagina=pagina,
                    tamanho=50,  # PNCP API max reduced from 500→50 (~Feb 2026)
                    status=status,
                )

                await _circuit_breaker.record_success()

                data = response.get("data", [])
                paginas_restantes = response.get("paginasRestantes", 0)

                for item in data:
                    item_id = item.get("numeroControlePNCP", "")
                    if item_id and item_id not in seen_ids:
                        seen_ids.add(item_id)
                        normalized = PNCPClient._normalize_item(item)
                        items.append(normalized)

                if paginas_restantes <= 0:
                    break

                # GTM-FIX-004: Detect truncation when max_pages reached
                if pagina >= max_pages and paginas_restantes > 0:
                    was_truncated = True
                    logger.warning(
                        f"MAX_PAGES ({max_pages}) reached for UF={uf}, "
                        f"modalidade={modalidade}. Fetched {len(items)} items. "
                        f"Remaining pages: {paginas_restantes}"
                    )

                pagina += 1

            except PNCPAPIError as e:
                await _circuit_breaker.record_failure()
                logger.warning(
                    f"Error fetching UF={uf}, modalidade={modalidade}, "
                    f"page={pagina}: {e}"
                )
                break

        return items, was_truncated

    async def _fetch_modality_with_timeout(
        self,
        uf: str,
        data_inicial: str,
        data_final: str,
        modalidade: int,
        status: str | None = None,
        max_pages: int = 500,
    ) -> tuple[List[Dict[str, Any]], bool]:
        """Fetch a single modality with per-modality timeout and 1 retry (STORY-252 AC6/AC9).

        Wraps ``_fetch_single_modality`` with:
        - ``PNCP_TIMEOUT_PER_MODALITY`` second timeout (default 15s, AC6)
        - 1 retry after ``PNCP_MODALITY_RETRY_BACKOFF`` seconds on timeout (AC9)

        On final timeout the circuit breaker records a failure but other
        modalities continue independently.

        Returns:
            Tuple of (items, was_truncated). Empty list + False if timed out.
        """
        per_modality_timeout = PNCP_TIMEOUT_PER_MODALITY
        retry_backoff = PNCP_MODALITY_RETRY_BACKOFF

        for attempt in range(2):  # 0 = first try, 1 = retry
            try:
                result = await asyncio.wait_for(
                    self._fetch_single_modality(
                        uf=uf,
                        data_inicial=data_inicial,
                        data_final=data_final,
                        modalidade=modalidade,
                        status=status,
                        max_pages=max_pages,
                    ),
                    timeout=per_modality_timeout,
                )
                return result
            except asyncio.TimeoutError:
                await _circuit_breaker.record_failure()
                if attempt == 0:
                    logger.warning(
                        f"UF={uf} modalidade={modalidade} timed out after "
                        f"{per_modality_timeout}s — retrying in {retry_backoff}s "
                        f"(attempt 1/1)"
                    )
                    await asyncio.sleep(retry_backoff)
                else:
                    logger.warning(
                        f"UF={uf} modalidade={modalidade} timed out after retry "
                        f"— skipping this modality"
                    )
        return [], False

    async def _fetch_uf_all_pages(
        self,
        uf: str,
        data_inicial: str,
        data_final: str,
        modalidades: List[int],
        status: str | None = None,
        max_pages: int = 500,  # HOTFIX STORY-183: Increased from 50 to 500
    ) -> tuple[List[Dict[str, Any]], bool]:
        """Fetch all pages for a single UF across all modalities in parallel.

        STORY-252 AC6: Each modality runs with its own timeout so that one
        hanging modality does not block the others.

        Args:
            uf: State code.
            data_inicial: Start date.
            data_final: End date.
            modalidades: List of modality codes.
            status: Optional status filter.
            max_pages: Maximum pages to fetch per modality.

        Returns:
            Tuple of (items, was_truncated). was_truncated is True when any
            modality hit max_pages (GTM-FIX-004).
        """
        async with self._semaphore:
            # Launch all modalities in parallel with individual timeouts (AC6)
            modality_tasks = [
                self._fetch_modality_with_timeout(
                    uf=uf,
                    data_inicial=data_inicial,
                    data_final=data_final,
                    modalidade=mod,
                    status=status,
                    max_pages=max_pages,
                )
                for mod in modalidades
            ]

            modality_results = await asyncio.gather(
                *modality_tasks, return_exceptions=True
            )

            # Merge and deduplicate across modalities
            all_items: List[Dict[str, Any]] = []
            seen_ids: set[str] = set()
            uf_was_truncated = False

            for mod, result in zip(modalidades, modality_results):
                if isinstance(result, Exception):
                    logger.warning(
                        f"UF={uf} modalidade={mod} failed: {result}"
                    )
                    continue
                # GTM-FIX-004: result is now (items, was_truncated)
                items, was_truncated = result
                if was_truncated:
                    uf_was_truncated = True
                for item in items:
                    item_id = item.get("codigoCompra", "") or item.get(
                        "numeroControlePNCP", ""
                    )
                    if item_id and item_id not in seen_ids:
                        seen_ids.add(item_id)
                        all_items.append(item)

            logger.info(f"Fetched {len(all_items)} items for UF={uf} (truncated={uf_was_truncated})")
            return all_items, uf_was_truncated

    async def buscar_todas_ufs_paralelo(
        self,
        ufs: List[str],
        data_inicial: str,
        data_final: str,
        modalidades: List[int] | None = None,
        status: str | None = None,
        max_pages_per_uf: int = 500,  # HOTFIX STORY-183: Increased from 50 to 500
        on_uf_complete: Callable[[str, int], Any] | None = None,
        on_uf_status: Callable[..., Any] | None = None,
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

        # Use default modalities if not specified; always filter out excluded
        modalidades = modalidades or DEFAULT_MODALIDADES
        modalidades = [m for m in modalidades if m not in MODALIDADES_EXCLUIDAS]

        # Map status to PNCP API value
        pncp_status = STATUS_PNCP_MAP.get(status) if status else None

        logger.info(
            f"Starting parallel fetch for {len(ufs)} UFs "
            f"(max_concurrent={self.max_concurrent}, status={status})"
        )

        # Try to recover before checking degraded state (STORY-257A AC4)
        await _circuit_breaker.try_recover()

        # STORY-257A AC1: Degraded mode tries with reduced concurrency
        if _circuit_breaker.is_degraded:
            logger.warning(
                "PNCP circuit breaker degraded — trying with reduced concurrency "
                f"(3 UFs, {PNCP_TIMEOUT_PER_UF_DEGRADED}s timeout)"
            )
            # Reorder UFs by population priority
            ufs_ordered = sorted(ufs, key=lambda u: UFS_BY_POPULATION.index(u) if u in UFS_BY_POPULATION else 99)
            # Reduce concurrency
            self._semaphore = asyncio.Semaphore(3)
            # GTM-FIX-029 AC2: 120s in degraded mode (was 45s)
            PER_UF_TIMEOUT = PNCP_TIMEOUT_PER_UF_DEGRADED
        else:
            # STORY-252 AC10: Health canary — lightweight probe before full search
            canary_ok = await self.health_canary()
            if not canary_ok:
                logger.warning(
                    "PNCP health canary failed — returning empty results"
                )
                return ParallelFetchResult(items=[], succeeded_ufs=[], failed_ufs=list(ufs))

            # Normal mode
            ufs_ordered = ufs
            # GTM-FIX-029 AC1/AC3: PER_UF_TIMEOUT raised from 30s to 90s
            # With tamanhoPagina=50, each modality needs ~10x more pages than before.
            # Calculation: 4 mods × ~15s/mod (with retry) = ~60s + 30s margin = 90s
            PER_UF_TIMEOUT = PNCP_TIMEOUT_PER_UF

        # Helper to safely call async/sync callbacks
        async def _safe_callback(cb, *args, **kwargs):
            if cb is None:
                return
            try:
                maybe_coro = cb(*args, **kwargs)
                if asyncio.iscoroutine(maybe_coro):
                    await maybe_coro
            except Exception as cb_err:
                logger.warning(f"Callback error: {cb_err}")

        # Create tasks for each UF with optional progress callback
        # GTM-FIX-004: returns (items, was_truncated) tuple
        async def _fetch_with_callback(uf: str) -> tuple[List[Dict[str, Any]], bool]:
            # STORY-257A AC6: Emit "fetching" status when UF starts
            await _safe_callback(on_uf_status, uf, "fetching")
            try:
                items, was_truncated = await asyncio.wait_for(
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
                await _circuit_breaker.record_failure()
                logger.warning(f"UF={uf} timed out after {PER_UF_TIMEOUT}s — skipping")
                # AC6: Emit "failed" status
                await _safe_callback(on_uf_status, uf, "failed", reason="timeout")
                items, was_truncated = [], False
            else:
                # AC6: Emit "success" status with count
                await _safe_callback(on_uf_status, uf, "success", count=len(items))
            if on_uf_complete:
                await _safe_callback(on_uf_complete, uf, len(items))
            return items, was_truncated

        # GTM-FIX-031: Phased UF batching — execute in batches of PNCP_BATCH_SIZE
        # with PNCP_BATCH_DELAY_S between batches to reduce API pressure
        batch_size = PNCP_BATCH_SIZE
        batch_delay = PNCP_BATCH_DELAY_S
        all_items: List[Dict[str, Any]] = []
        errors = 0
        succeeded_ufs = []
        failed_ufs = []
        truncated_ufs = []  # GTM-FIX-004
        total_batches = (len(ufs_ordered) + batch_size - 1) // batch_size

        for batch_idx in range(0, len(ufs_ordered), batch_size):
            batch = ufs_ordered[batch_idx:batch_idx + batch_size]
            batch_num = batch_idx // batch_size + 1

            logger.info(
                f"Batch {batch_num}/{total_batches}: fetching {len(batch)} UFs: {batch}"
            )

            # Emit batch progress via SSE
            await _safe_callback(
                on_uf_status, batch[0], "batch_info",
                batch_num=batch_num, total_batches=total_batches,
                ufs_in_batch=batch,
            )

            batch_tasks = [_fetch_with_callback(uf) for uf in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for uf, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error fetching UF={uf}: {result}")
                    errors += 1
                    failed_ufs.append(uf)
                elif isinstance(result, tuple):
                    items, was_truncated = result
                    if was_truncated:
                        truncated_ufs.append(uf)
                    if len(items) == 0:
                        succeeded_ufs.append(uf)  # No data ≠ failure
                    else:
                        all_items.extend(items)
                        succeeded_ufs.append(uf)
                else:
                    # Backward compat: plain list (shouldn't happen with new code)
                    all_items.extend(result)
                    succeeded_ufs.append(uf)

            # Inter-batch delay (skip after last batch)
            if batch_idx + batch_size < len(ufs_ordered):
                logger.debug(f"Batch {batch_num} complete, waiting {batch_delay}s before next batch")
                await asyncio.sleep(batch_delay)

        # STORY-257A AC7: Auto-retry failed UFs (1 round, 5s delay)
        # GTM-FIX-029: Retry timeout matches degraded per-UF timeout (120s)
        if failed_ufs and succeeded_ufs:
            logger.info(
                f"AC7: {len(failed_ufs)} UFs failed, {len(succeeded_ufs)} succeeded — "
                f"retrying failed UFs in 5s with {PNCP_TIMEOUT_PER_UF_DEGRADED}s timeout"
            )
            await asyncio.sleep(5)

            RETRY_TIMEOUT = PNCP_TIMEOUT_PER_UF_DEGRADED

            async def _retry_uf(uf: str) -> tuple[List[Dict[str, Any]], bool]:
                await _safe_callback(on_uf_status, uf, "retrying", attempt=2, max=2)
                try:
                    items, was_truncated = await asyncio.wait_for(
                        self._fetch_uf_all_pages(
                            uf=uf,
                            data_inicial=data_inicial,
                            data_final=data_final,
                            modalidades=modalidades,
                            status=pncp_status,
                            max_pages=max_pages_per_uf,
                        ),
                        timeout=RETRY_TIMEOUT,
                    )
                    return items, was_truncated
                except (asyncio.TimeoutError, Exception) as e:
                    logger.warning(f"AC7: Retry for UF={uf} failed: {e}")
                    return [], False

            retry_tasks = [_retry_uf(uf) for uf in failed_ufs]
            retry_results = await asyncio.gather(*retry_tasks, return_exceptions=True)

            recovered_ufs = []
            for uf, result in zip(failed_ufs, retry_results):
                if isinstance(result, Exception):
                    await _safe_callback(on_uf_status, uf, "failed", reason="retry_failed")
                elif isinstance(result, tuple):
                    items, was_truncated = result
                    if not items:
                        await _safe_callback(on_uf_status, uf, "failed", reason="retry_failed")
                    else:
                        all_items.extend(items)
                        recovered_ufs.append(uf)
                        if was_truncated and uf not in truncated_ufs:
                            truncated_ufs.append(uf)
                        await _safe_callback(on_uf_status, uf, "recovered", count=len(items))
                        logger.info(f"AC7: UF={uf} recovered with {len(items)} items")
                else:
                    await _safe_callback(on_uf_status, uf, "failed", reason="retry_failed")

            if recovered_ufs:
                # Move recovered UFs from failed to succeeded
                for uf in recovered_ufs:
                    failed_ufs.remove(uf)
                    succeeded_ufs.append(uf)
                logger.info(f"AC7: Recovered {len(recovered_ufs)} UFs: {recovered_ufs}")

        elapsed = sync_time.time() - start_time
        if truncated_ufs:
            logger.warning(
                f"GTM-FIX-004: Truncated UFs: {truncated_ufs}. "
                f"Results may be incomplete for these states."
            )
        logger.info(
            f"Parallel fetch complete: {len(all_items)} items from {len(ufs)} UFs "
            f"in {elapsed:.2f}s ({errors} errors, {len(truncated_ufs)} truncated)"
        )

        return ParallelFetchResult(
            items=all_items,
            succeeded_ufs=succeeded_ufs,
            failed_ufs=failed_ufs,
            truncated_ufs=truncated_ufs,
        )


# ============================================================================
# PNCPLegacyAdapter — SourceAdapter wrapper for ConsolidationService (AC6)
# ============================================================================

class PNCPLegacyAdapter:
    """Wraps existing PNCPClient as a SourceAdapter for multi-source consolidation.

    STORY-216 AC6: Moved from inline class inside buscar_licitacoes() to module level.
    Accepts constructor parameters instead of capturing enclosing scope variables.

    This class conforms to the SourceAdapter interface (clients.base) but the import
    is deferred to avoid making pncp_client.py depend on clients.base at module level.
    The consolidation service only checks for the required methods at runtime.
    """

    def __init__(
        self,
        ufs: List[str],
        modalidades: List[int] | None = None,
        status: str | None = None,
        on_uf_complete: Callable | None = None,
        on_uf_status: Callable | None = None,
    ):
        self._ufs = ufs
        self._modalidades = modalidades
        self._status = status
        self._on_uf_complete = on_uf_complete
        self._on_uf_status = on_uf_status
        # GTM-FIX-004: Truncation detection for PNCP in multi-source mode
        self.was_truncated: bool = False
        self.truncated_ufs: List[str] = []

    @property
    def metadata(self):
        from clients.base import SourceMetadata, SourceCapability
        return SourceMetadata(
            name="PNCP", code="PNCP",
            base_url="https://pncp.gov.br/api/consulta/v1",
            capabilities={SourceCapability.PAGINATION, SourceCapability.DATE_RANGE, SourceCapability.FILTER_BY_UF},
            rate_limit_rps=10.0, priority=1,
        )

    @property
    def name(self) -> str:
        """Human-readable source name (GTM-FIX-024 T1)."""
        return self.metadata.name

    @property
    def code(self) -> str:
        """Short code for logs/metrics (GTM-FIX-024 T1)."""
        return self.metadata.code

    async def health_check(self):
        from clients.base import SourceStatus
        if _circuit_breaker.is_degraded:
            return SourceStatus.DEGRADED
        return SourceStatus.AVAILABLE

    async def fetch(self, data_inicial, data_final, ufs=None, **kwargs):
        from clients.base import UnifiedProcurement
        _ufs = list(ufs) if ufs else self._ufs
        if len(_ufs) > 1:
            fetch_result = await buscar_todas_ufs_paralelo(
                ufs=_ufs, data_inicial=data_inicial, data_final=data_final,
                modalidades=self._modalidades, status=self._status,
                max_concurrent=10, on_uf_complete=self._on_uf_complete,
                on_uf_status=self._on_uf_status,
            )
            if isinstance(fetch_result, ParallelFetchResult):
                results = fetch_result.items
                # GTM-FIX-004: Capture truncation state for multi-source propagation
                if fetch_result.truncated_ufs:
                    self.was_truncated = True
                    self.truncated_ufs = fetch_result.truncated_ufs
            else:
                results = fetch_result
        else:
            client = PNCPClient()
            results = list(client.fetch_all(
                data_inicial=data_inicial, data_final=data_final,
                ufs=_ufs, modalidades=self._modalidades,
            ))
        for item in results:
            # GTM-FIX-017: Parse date fields from PNCP response
            data_pub = None
            if item.get("dataPublicacaoPncp"):
                try:
                    data_pub = datetime.fromisoformat(item["dataPublicacaoPncp"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass

            data_enc = None
            if item.get("dataEncerramentoProposta"):
                try:
                    data_enc = datetime.fromisoformat(item["dataEncerramentoProposta"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass

            data_abertura = None
            if item.get("dataAberturaProposta"):
                try:
                    data_abertura = datetime.fromisoformat(item["dataAberturaProposta"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass

            yield UnifiedProcurement(
                source_id=item.get("codigoCompra", ""),
                source_name="PNCP",
                objeto=item.get("objetoCompra", ""),
                valor_estimado=item.get("valorTotalEstimado", 0) or 0,
                orgao=item.get("nomeOrgao", ""),
                cnpj_orgao=item.get("cnpjOrgao", ""),
                uf=item.get("uf", ""),
                municipio=item.get("municipio", ""),
                data_publicacao=data_pub,
                data_abertura=data_abertura,
                data_encerramento=data_enc,
                numero_edital=item.get("numeroEdital", ""),
                ano=item.get("anoCompra", ""),
                esfera=item.get("esferaId", ""),
                modalidade=item.get("modalidadeNome", ""),
                modalidade_id=item.get("modalidadeId"),
                situacao=item.get("situacaoCompraNome", ""),
                link_edital=item.get("linkSistemaOrigem", ""),
                link_portal=item.get("linkProcessoEletronico", ""),
                raw_data=item,
            )

    def normalize(self, raw_record):
        pass

    async def close(self):
        pass


async def buscar_todas_ufs_paralelo(
    ufs: List[str],
    data_inicial: str,
    data_final: str,
    modalidades: List[int] | None = None,
    status: str | None = None,
    max_concurrent: int = 10,
    on_uf_complete: Callable[[str, int], Any] | None = None,
    on_uf_status: Callable[..., Any] | None = None,
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
        on_uf_status: Optional async callback(uf, status, **detail) for per-UF status events

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
            on_uf_status=on_uf_status,
        )
