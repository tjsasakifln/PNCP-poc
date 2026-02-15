"""Querido Diario API client adapter (Municipal Gazette Search).

This module implements the SourceAdapter interface for the Querido Diario
open data API (https://api.queridodiario.ok.org.br).

API Characteristics:
- REST API with JSON responses
- No authentication required (open data by Open Knowledge Brasil)
- Municipal-only gazette data (Diarios Oficiais Municipais)
- Rate limit: conservative 1 req/s (no documented limit, being respectful)
- Full-text search via OpenSearch simple query string syntax
- Excerpt extraction for matching snippets

Documentation: https://queridodiario.ok.org.br/api/docs
"""

import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional, Set

import httpx

from clients.base import (
    SourceAdapter,
    SourceMetadata,
    SourceStatus,
    SourceCapability,
    SourceAPIError,
    SourceRateLimitError,
    SourceTimeoutError,
    SourceParseError,
    UnifiedProcurement,
)

logger = logging.getLogger(__name__)


# Procurement context terms always included in querystring building.
# These anchor the search to procurement-related gazette content.
PROCUREMENT_CONTEXT_TERMS: Set[str] = {
    "licitacao",
    "pregao",
    "edital",
    "contratacao",
    "tomada de precos",
    "concorrencia",
    "dispensa",
    "inexigibilidade",
}

# Maximum number of gazette full-text downloads per fetch() call.
# Prevents excessive bandwidth usage on the QD servers.
MAX_TEXT_DOWNLOADS = 10

# Maximum total results to collect across all pages.
MAX_TOTAL_RESULTS = 500

# Default page size for pagination.
DEFAULT_PAGE_SIZE = 20

# Maximum excerpt characters per gazette result.
DEFAULT_EXCERPT_SIZE = 500

# Number of excerpts to request per gazette.
DEFAULT_NUMBER_OF_EXCERPTS = 3


class QueridoDiarioClient(SourceAdapter):
    """
    Adapter for Querido Diario Municipal Gazette API.

    This adapter searches Brazilian municipal official gazettes (Diarios
    Oficiais Municipais) for procurement-related content. It converts
    gazette search results into UnifiedProcurement records for downstream
    processing by the LLM extraction pipeline.

    Unlike structured procurement APIs (PNCP, ComprasGov), Querido Diario
    returns full-text gazette content. The adapter yields basic procurement
    records from excerpts; deeper extraction from full gazette text is
    handled by the qd_extraction.py pipeline.

    Attributes:
        BASE_URL: API base URL
        DEFAULT_TIMEOUT: Request timeout in seconds
        MAX_RETRIES: Maximum number of retry attempts
        RATE_LIMIT_DELAY: Minimum delay between requests (seconds)
    """

    BASE_URL = "https://api.queridodiario.ok.org.br"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RATE_LIMIT_DELAY = 1.0  # 1 req/s (conservative, no official limit)
    PAGE_SIZE = DEFAULT_PAGE_SIZE

    _metadata = SourceMetadata(
        name="Querido Diario - Diarios Oficiais Municipais",
        code="QUERIDO_DIARIO",
        base_url="https://api.queridodiario.ok.org.br",
        documentation_url="https://queridodiario.ok.org.br/api/docs",
        capabilities={
            SourceCapability.FILTER_BY_KEYWORD,
            SourceCapability.PAGINATION,
            SourceCapability.DATE_RANGE,
        },
        rate_limit_rps=1.0,
        typical_response_ms=3000,
        priority=5,  # Lowest -- experimental, complement to PNCP
    )

    def __init__(self, timeout: Optional[int] = None):
        """
        Initialize Querido Diario adapter.

        Args:
            timeout: Request timeout in seconds. Defaults to DEFAULT_TIMEOUT.
        """
        self._timeout = timeout or self.DEFAULT_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None
        self._last_request_time = 0.0
        self._request_count = 0

    @property
    def metadata(self) -> SourceMetadata:
        """Return source metadata."""
        return self._metadata

    # ------------------------------------------------------------------ #
    # HTTP infrastructure
    # ------------------------------------------------------------------ #

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with proper configuration."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=httpx.Timeout(self._timeout),
                headers={
                    "Accept": "application/json",
                    "User-Agent": "SmartLic/1.0 (contato@smartlic.com.br)",
                },
            )
        return self._client

    async def _rate_limit(self) -> None:
        """Enforce rate limiting between requests (1 req/s)."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()
        self._request_count += 1

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and rate limiting.

        Retries on 429 (rate limit) and 5xx (server errors).
        No retry on 4xx (client errors, except 429).

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (relative to BASE_URL)
            params: Query parameters

        Returns:
            Parsed JSON response as dict

        Raises:
            SourceTimeoutError: On timeout after retries
            SourceRateLimitError: On 429 after retries
            SourceAPIError: On other API errors
        """
        await self._rate_limit()
        client = await self._get_client()

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                logger.debug(
                    f"[QUERIDO_DIARIO] {method} {path} params={params} "
                    f"attempt={attempt + 1}/{self.MAX_RETRIES + 1}"
                )

                response = await client.request(method, path, params=params)

                # --- Rate limit (429) --- retry with Retry-After
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < self.MAX_RETRIES:
                        logger.warning(
                            f"[QUERIDO_DIARIO] Rate limited. Waiting {retry_after}s"
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    raise SourceRateLimitError(self.code, retry_after)

                # --- Success (200) ---
                if response.status_code == 200:
                    return response.json()

                # --- No content (204) ---
                if response.status_code == 204:
                    return {"total_gazettes": 0, "gazettes": []}

                # --- Server errors (5xx) --- retry with backoff
                if response.status_code >= 500:
                    if attempt < self.MAX_RETRIES:
                        delay = self._calculate_backoff(attempt)
                        logger.warning(
                            f"[QUERIDO_DIARIO] Server error {response.status_code}. "
                            f"Retrying in {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                        continue

                # --- Other errors --- no retry
                raise SourceAPIError(
                    self.code, response.status_code, response.text[:500]
                )

            except httpx.TimeoutException as e:
                if attempt < self.MAX_RETRIES:
                    delay = self._calculate_backoff(attempt)
                    logger.warning(
                        f"[QUERIDO_DIARIO] Timeout. Retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                    continue
                raise SourceTimeoutError(self.code, self._timeout) from e

            except httpx.RequestError as e:
                if attempt < self.MAX_RETRIES:
                    delay = self._calculate_backoff(attempt)
                    logger.warning(
                        f"[QUERIDO_DIARIO] Request error: {e}. "
                        f"Retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                    continue
                raise SourceAPIError(self.code, 0, str(e)) from e

        raise SourceAPIError(self.code, 0, "Exhausted retries")

    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter."""
        delay = min(2.0 * (2 ** attempt), 60.0)
        delay *= random.uniform(0.5, 1.5)
        return delay

    # ------------------------------------------------------------------ #
    # Querystring builder (AC3)
    # ------------------------------------------------------------------ #

    @staticmethod
    def build_querystring(sector_keywords: Set[str]) -> str:
        """
        Convert sector keywords into OpenSearch simple query string syntax.

        The querystring combines procurement context terms (licitacao, pregao,
        edital, etc.) with sector-specific keywords using AND (+) and OR (|)
        operators. This ensures gazette results are both procurement-related
        AND sector-relevant.

        Strategy:
            (procurement_term_1 | procurement_term_2 | ...) + (keyword_1 | keyword_2 | ...)

        Multi-word keywords are wrapped in quotes for exact phrase matching.

        Args:
            sector_keywords: Set of sector-specific keywords to search for.
                             Examples: {"uniforme", "fardamento", "jaleco"}

        Returns:
            OpenSearch simple query string.
            Example: '(licitacao | pregao | edital) + (uniforme | fardamento | jaleco)'
        """
        if not sector_keywords:
            # Fallback: just search for procurement terms
            context_parts = sorted(PROCUREMENT_CONTEXT_TERMS)
            return "(" + " | ".join(context_parts) + ")"

        # Build the procurement context group
        context_parts = sorted(PROCUREMENT_CONTEXT_TERMS)
        context_group = "(" + " | ".join(context_parts) + ")"

        # Build the sector keywords group
        # Multi-word terms get quoted for exact phrase matching
        keyword_parts: List[str] = []
        for kw in sorted(sector_keywords):
            kw = kw.strip()
            if not kw:
                continue
            if " " in kw:
                keyword_parts.append(f'"{kw}"')
            else:
                keyword_parts.append(kw)

        if not keyword_parts:
            return context_group

        keywords_group = "(" + " | ".join(keyword_parts) + ")"

        return f"{context_group} + {keywords_group}"

    # ------------------------------------------------------------------ #
    # Gazette search (AC2, AC4, AC5)
    # ------------------------------------------------------------------ #

    async def search_gazettes(
        self,
        query: str,
        territory_ids: Optional[List[str]] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        size: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Search municipal gazettes via GET /gazettes.

        Args:
            query: OpenSearch simple query string (built by build_querystring).
            territory_ids: List of 7-digit IBGE city codes to filter by.
                           Example: ["3550308"] for Sao Paulo.
            since: Published since date in YYYY-MM-DD format.
            until: Published until date in YYYY-MM-DD format.
            size: Number of results per page (default 20, max 100).
            offset: Number of results to skip for pagination.

        Returns:
            Raw API response dict with keys:
                - total_gazettes (int): Total matching gazettes
                - gazettes (list): List of gazette result objects

        Raises:
            SourceTimeoutError: On request timeout
            SourceRateLimitError: On rate limit exceeded
            SourceAPIError: On other API errors
        """
        params: Dict[str, Any] = {
            "querystring": query,
            "excerpt_size": DEFAULT_EXCERPT_SIZE,
            "number_of_excerpts": DEFAULT_NUMBER_OF_EXCERPTS,
            "sort_by": "relevance",
            "size": min(size, 100),
            "offset": offset,
        }

        if territory_ids:
            # The API accepts multiple territory_ids as repeated params.
            # httpx handles list values by repeating the key.
            params["territory_ids"] = territory_ids

        if since:
            params["published_since"] = since

        if until:
            params["published_until"] = until

        response = await self._request_with_retry("GET", "/gazettes", params)

        total = response.get("total_gazettes", 0)
        gazettes = response.get("gazettes", [])

        logger.debug(
            f"[QUERIDO_DIARIO] search_gazettes: {len(gazettes)} results "
            f"(total={total}, offset={offset})"
        )

        return response

    # ------------------------------------------------------------------ #
    # Full-text download (AC6)
    # ------------------------------------------------------------------ #

    async def fetch_gazette_text(self, txt_url: str) -> str:
        """
        Download the full plain-text content of a gazette.

        This method is called by the extraction pipeline (qd_extraction.py)
        to obtain the full gazette text for LLM-based procurement extraction.
        It is NOT called by fetch() directly.

        Args:
            txt_url: URL to the gazette plain-text file (from gazette.txt_url).

        Returns:
            Full gazette text as string. Returns empty string on failure.

        Note:
            This method enforces rate limiting and uses a separate timeout
            (60s) since gazette texts can be large.
        """
        if not txt_url:
            return ""

        await self._rate_limit()

        try:
            client = await self._get_client()

            logger.debug(f"[QUERIDO_DIARIO] Downloading gazette text: {txt_url}")

            # Use a longer timeout for full text downloads (can be large)
            response = await client.get(
                txt_url,
                timeout=httpx.Timeout(60.0),
            )

            if response.status_code == 200:
                text = response.text
                logger.debug(
                    f"[QUERIDO_DIARIO] Downloaded gazette text: "
                    f"{len(text)} chars from {txt_url}"
                )
                return text

            logger.warning(
                f"[QUERIDO_DIARIO] Failed to download gazette text "
                f"(HTTP {response.status_code}): {txt_url}"
            )
            return ""

        except httpx.TimeoutException:
            logger.warning(
                f"[QUERIDO_DIARIO] Timeout downloading gazette text: {txt_url}"
            )
            return ""
        except httpx.RequestError as e:
            logger.warning(
                f"[QUERIDO_DIARIO] Error downloading gazette text: {e}"
            )
            return ""

    # ------------------------------------------------------------------ #
    # SourceAdapter interface implementation
    # ------------------------------------------------------------------ #

    async def health_check(self) -> SourceStatus:
        """
        Check if Querido Diario API is available.

        Performs a lightweight query (size=1) to verify connectivity.

        Returns:
            SourceStatus.AVAILABLE if API responds successfully
            SourceStatus.DEGRADED if API responds but slowly (>4s)
            SourceStatus.UNAVAILABLE if API fails to respond
        """
        try:
            client = await self._get_client()
            start = asyncio.get_event_loop().time()

            response = await client.get(
                "/gazettes",
                params={"size": 1},
                timeout=5.0,
            )

            elapsed_ms = (asyncio.get_event_loop().time() - start) * 1000

            if response.status_code == 200:
                if elapsed_ms > 4000:
                    logger.info(
                        f"[QUERIDO_DIARIO] Health check slow: {elapsed_ms:.0f}ms"
                    )
                    return SourceStatus.DEGRADED
                return SourceStatus.AVAILABLE

            logger.warning(
                f"[QUERIDO_DIARIO] Health check returned {response.status_code}"
            )
            return SourceStatus.DEGRADED

        except (httpx.TimeoutException, httpx.RequestError) as e:
            logger.warning(f"[QUERIDO_DIARIO] Health check failed: {e}")
            return SourceStatus.UNAVAILABLE
        except Exception as e:
            logger.error(
                f"[QUERIDO_DIARIO] Unexpected health check error: {e}"
            )
            return SourceStatus.UNAVAILABLE

    async def fetch(
        self,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[UnifiedProcurement, None]:
        """
        Fetch procurement records from Querido Diario gazette search.

        This method:
        1. Builds a querystring from sector keywords (or defaults)
        2. Searches gazettes with automatic pagination (up to 500 results)
        3. Normalizes each gazette result into a UnifiedProcurement record
        4. Applies client-side UF filtering

        Unlike structured procurement APIs, gazette results contain excerpt
        text rather than structured procurement data. The yielded records
        use excerpts as the objeto field. Full text extraction for deeper
        procurement data parsing is handled by qd_extraction.py using
        fetch_gazette_text().

        Args:
            data_inicial: Start date in YYYY-MM-DD format (published_since)
            data_final: End date in YYYY-MM-DD format (published_until)
            ufs: Optional set of Brazilian state codes to filter (client-side).
                 Querido Diario does not support server-side UF filtering.
            **kwargs: Additional parameters:
                - sector_keywords (Set[str]): Keywords for querystring building.
                  If not provided, uses default procurement terms only.
                - territory_ids (List[str]): 7-digit IBGE city codes.

        Yields:
            UnifiedProcurement records (one per gazette with matching excerpt)
        """
        sector_keywords: Set[str] = kwargs.get("sector_keywords", set())
        territory_ids: Optional[List[str]] = kwargs.get("territory_ids", None)

        # Build the search querystring
        querystring = self.build_querystring(sector_keywords)
        logger.info(
            f"[QUERIDO_DIARIO] Starting fetch: querystring={querystring!r}, "
            f"dates={data_inicial} to {data_final}, UF filter={ufs or 'all'}"
        )

        offset = 0
        total_fetched = 0
        total_skipped_uf = 0
        seen_ids: Set[str] = set()

        while total_fetched < MAX_TOTAL_RESULTS:
            remaining = MAX_TOTAL_RESULTS - total_fetched
            page_size = min(self.PAGE_SIZE, remaining)

            try:
                response = await self.search_gazettes(
                    query=querystring,
                    territory_ids=territory_ids,
                    since=data_inicial,
                    until=data_final,
                    size=page_size,
                    offset=offset,
                )
            except Exception as e:
                logger.error(
                    f"[QUERIDO_DIARIO] Error fetching offset {offset}: {e}"
                )
                if total_fetched > 0:
                    logger.warning(
                        f"[QUERIDO_DIARIO] Returning {total_fetched} partial results"
                    )
                    return
                raise

            total_gazettes = response.get("total_gazettes", 0)
            gazettes = response.get("gazettes", [])

            if offset == 0:
                logger.info(
                    f"[QUERIDO_DIARIO] Query matched {total_gazettes} total gazettes"
                )

            if not gazettes:
                logger.debug(
                    f"[QUERIDO_DIARIO] No more results at offset {offset}"
                )
                break

            for gazette in gazettes:
                try:
                    record = self.normalize(gazette)

                    # Skip duplicates
                    if record.source_id in seen_ids:
                        continue
                    seen_ids.add(record.source_id)

                    # Client-side UF filtering
                    if ufs and record.uf and record.uf not in ufs:
                        total_skipped_uf += 1
                        continue

                    # Skip records with empty UF if UF filter is active
                    if ufs and not record.uf:
                        total_skipped_uf += 1
                        continue

                    total_fetched += 1
                    yield record

                    if total_fetched >= MAX_TOTAL_RESULTS:
                        break

                except Exception as e:
                    logger.warning(
                        f"[QUERIDO_DIARIO] Failed to normalize gazette: {e}"
                    )
                    continue

            # Progress logging every 100 records
            if total_fetched > 0 and total_fetched % 100 == 0:
                logger.info(
                    f"[QUERIDO_DIARIO] Progress: {total_fetched} records fetched"
                )

            # Check if we have reached the end of results
            if offset + len(gazettes) >= total_gazettes:
                break

            # Safety: if we got fewer results than requested, we are done
            if len(gazettes) < page_size:
                break

            offset += len(gazettes)

        logger.info(
            f"[QUERIDO_DIARIO] Fetch complete: {total_fetched} records, "
            f"{total_skipped_uf} skipped by UF filter, "
            f"{self._request_count} total API requests"
        )

    def normalize(self, raw_record: Dict[str, Any]) -> UnifiedProcurement:
        """
        Convert a Querido Diario gazette result to UnifiedProcurement.

        Field Mapping:
            territory_id + date + edition -> source_id (QD-{territory_id}-{date}-{edition})
            territory_name -> municipio
            state_code -> uf
            excerpts (joined, first 500 chars) -> objeto
            date -> data_publicacao
            url -> link_portal
            txt_url -> link_edital
            esfera -> always "M" (municipal)

        Args:
            raw_record: Raw gazette object from API response

        Returns:
            Normalized UnifiedProcurement record

        Raises:
            SourceParseError: If critical fields cannot be parsed
        """
        try:
            # --- Core identifiers ---
            territory_id = str(raw_record.get("territory_id", ""))
            date_str = str(raw_record.get("date", ""))
            edition = str(raw_record.get("edition", "")) or "main"
            is_extra = raw_record.get("is_extra_edition", False)

            if not territory_id or not date_str:
                raise SourceParseError(
                    self.code,
                    "territory_id/date",
                    raw_record,
                )

            # Build unique source_id
            edition_suffix = edition
            if is_extra:
                edition_suffix = f"{edition}-extra"
            source_id = f"QD-{territory_id}-{date_str}-{edition_suffix}"

            # --- Location ---
            territory_name = str(raw_record.get("territory_name", ""))
            state_code = str(raw_record.get("state_code", ""))

            # --- Excerpts -> objeto ---
            excerpts = raw_record.get("excerpts", [])
            if isinstance(excerpts, list):
                # Join excerpts with separator, limit to 500 chars
                joined_excerpts = " [...] ".join(
                    str(e).strip() for e in excerpts if e
                )
            elif isinstance(excerpts, str):
                joined_excerpts = excerpts.strip()
            else:
                joined_excerpts = ""

            objeto = joined_excerpts[:500] if joined_excerpts else ""

            # --- Date ---
            data_publicacao = self._parse_date(date_str)

            # --- Year ---
            ano = ""
            if data_publicacao:
                ano = str(data_publicacao.year)
            elif len(date_str) >= 4:
                ano = date_str[:4]

            # --- URLs ---
            url = str(raw_record.get("url", ""))
            txt_url = str(raw_record.get("txt_url", ""))

            return UnifiedProcurement(
                source_id=source_id,
                source_name=self.code,
                objeto=objeto,
                valor_estimado=0.0,  # Not available from gazette search
                orgao="",  # Not directly available; extracted by LLM later
                cnpj_orgao="",
                uf=state_code,
                municipio=territory_name,
                data_publicacao=data_publicacao,
                data_abertura=None,
                data_encerramento=None,
                numero_edital="",  # Not directly available; extracted by LLM later
                ano=ano,
                modalidade="",  # Not directly available; extracted by LLM later
                situacao="Publicada",  # Gazette content is always published
                esfera="M",  # Municipal only
                link_edital=txt_url,
                link_portal=url,
                fetched_at=datetime.now(timezone.utc),
                raw_data=raw_record,
            )

        except SourceParseError:
            raise
        except Exception as e:
            logger.error(f"[QUERIDO_DIARIO] Normalization error: {e}")
            raise SourceParseError(self.code, "record", str(e)) from e

    # ------------------------------------------------------------------ #
    # Date parsing helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_date(value: Any) -> Optional[datetime]:
        """
        Parse date from string in various formats.

        Querido Diario primarily uses YYYY-MM-DD format.

        Args:
            value: Date string or None

        Returns:
            Parsed datetime or None if parsing fails
        """
        if not value:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            formats = [
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y",
                "%d/%m/%Y %H:%M:%S",
            ]
            value_clean = value.strip().replace("+00:00", "Z").replace("+0000", "Z")
            for fmt in formats:
                try:
                    return datetime.strptime(
                        value_clean.rstrip("Z"), fmt.rstrip("Z")
                    )
                except ValueError:
                    continue
            logger.debug(f"[QUERIDO_DIARIO] Failed to parse date: {value}")

        return None

    # ------------------------------------------------------------------ #
    # Resource management
    # ------------------------------------------------------------------ #

    async def close(self) -> None:
        """Close HTTP client and release resources."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            logger.debug(
                f"[QUERIDO_DIARIO] Client closed. "
                f"Total requests: {self._request_count}"
            )
        self._client = None

    async def __aenter__(self) -> "QueridoDiarioClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
