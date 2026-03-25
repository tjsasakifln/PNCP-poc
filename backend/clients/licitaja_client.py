"""LicitaJá API client adapter (v1).

This module implements the SourceAdapter interface for the LicitaJá
procurement aggregator API (https://www.licitaja.com.br/api/v1).

API Characteristics (v1.1.3):
- REST API with JSON responses
- Authentication via X-API-KEY header
- Date format: YYYYmmdd (compact, no separators)
- Pagination: configurable items per page (max 25), `page` param
- UF filtering: server-side via `state` param (comma-separated)
- Value filtering: server-side via tender_value_min/tender_value_max
- Keyword filtering: server-side via `keyword` param

Docs: https://app.swaggerhub.com/apis-docs/bidhits/licitaja-br/1.1.3
Rate limit: 10 req/min (default)
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
    SourceAuthError,
    SourceRateLimitError,
    SourceTimeoutError,
    SourceParseError,
    UnifiedProcurement,
)

logger = logging.getLogger(__name__)


class LicitaJaAdapter(SourceAdapter):
    """Adapter for LicitaJá procurement aggregator API v1.

    LicitaJá is a commercial procurement aggregator that indexes data from
    multiple Brazilian government portals. It provides enriched search with
    keyword relevance, value filtering, and server-side UF filtering.

    Authentication is via X-API-KEY header. An API key is required for
    full results; requests without a key return partial data.

    The API has a rate limit of 10 requests per minute (configurable).
    """

    BASE_URL = "https://www.licitaja.com.br/api/v1"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    PAGE_SIZE = 25  # API max per page

    _metadata = SourceMetadata(
        name="LicitaJá",
        code="LICITAJA",
        base_url="https://www.licitaja.com.br/api/v1",
        documentation_url="https://app.swaggerhub.com/apis-docs/bidhits/licitaja-br/1.1.3",
        capabilities={
            SourceCapability.PAGINATION,
            SourceCapability.DATE_RANGE,
            SourceCapability.FILTER_BY_UF,
            SourceCapability.FILTER_BY_VALUE,
            SourceCapability.FILTER_BY_KEYWORD,
        },
        rate_limit_rps=0.17,  # ~10 req/min
        typical_response_ms=3000,
        priority=4,  # After PNCP(1), PCP(2), ComprasGov(3)
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
        rate_limit_rpm: Optional[int] = None,
        max_pages: int = 20,
    ):
        """Initialize LicitaJá adapter.

        Args:
            api_key: LicitaJá API key (X-API-KEY header).
            timeout: Request timeout in seconds.
            rate_limit_rpm: Rate limit in requests per minute (default: 10).
            max_pages: Maximum pages to fetch per search (default: 20).
        """
        import os
        self._api_key = api_key or os.getenv("LICITAJA_API_KEY", "")
        self._timeout = timeout or int(os.getenv("LICITAJA_TIMEOUT", str(self.DEFAULT_TIMEOUT)))
        self._rate_limit_rpm = rate_limit_rpm or int(os.getenv("LICITAJA_RATE_LIMIT_RPM", "10"))
        self._rate_limit_delay = 60.0 / max(self._rate_limit_rpm, 1)  # seconds between requests
        self._max_pages = max_pages
        self._client: Optional[httpx.AsyncClient] = None
        self._last_request_time = 0.0
        self._request_count = 0
        self.was_truncated: bool = False

    @property
    def metadata(self) -> SourceMetadata:
        return self._metadata

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with isolated connection pool."""
        if self._client is None or self._client.is_closed:
            headers: Dict[str, str] = {
                "Accept": "application/json",
                "User-Agent": "SmartLic/1.0 (procurement-aggregator)",
            }
            if self._api_key:
                headers["X-API-KEY"] = self._api_key

            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=httpx.Timeout(self._timeout),
                limits=httpx.Limits(
                    max_connections=5,
                    max_keepalive_connections=3,
                ),
                headers=headers,
            )
        return self._client

    async def _rate_limit(self) -> None:
        """Enforce rate limiting between requests (10 req/min default)."""
        now = asyncio.get_running_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self._rate_limit_delay:
            await asyncio.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = asyncio.get_running_loop().time()
        self._request_count += 1

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make HTTP request with retry logic and rate limiting.

        Args:
            method: HTTP method (GET/POST).
            path: API endpoint path.
            params: Query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            SourceAuthError: If API key is invalid (401).
            SourceRateLimitError: If rate limit exceeded (401 with limit message).
            SourceAPIError: If server returns an error.
            SourceTimeoutError: If request times out after retries.
        """
        await self._rate_limit()
        client = await self._get_client()

        if params is None:
            params = {}

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                logger.debug(
                    f"[LICITAJA] {method} {path} attempt={attempt + 1}/{self.MAX_RETRIES + 1}"
                )

                response = await client.request(method, path, params=params)

                if response.status_code == 401:
                    body = response.text[:200]
                    # LicitaJá uses 401 for both auth failures and rate limit exceeded
                    if "limit" in body.lower() or "exceeded" in body.lower():
                        retry_after = 60  # Wait full minute on rate limit
                        if attempt < self.MAX_RETRIES:
                            logger.warning(f"[LICITAJA] Rate limited. Waiting {retry_after}s")
                            await asyncio.sleep(retry_after)
                            continue
                        raise SourceRateLimitError(self.code, retry_after)
                    raise SourceAuthError(
                        self.code,
                        f"Authentication failed: {response.status_code} — check LICITAJA_API_KEY"
                    )

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < self.MAX_RETRIES:
                        logger.warning(f"[LICITAJA] Rate limited (429). Waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue
                    raise SourceRateLimitError(self.code, retry_after)

                if response.status_code in (403,):
                    raise SourceAuthError(
                        self.code,
                        f"Forbidden: {response.status_code}"
                    )

                if response.status_code == 200:
                    return response.json()

                if response.status_code == 204:
                    return {"results": [], "total_results": 0}

                if response.status_code >= 500:
                    if attempt < self.MAX_RETRIES:
                        delay = self._calculate_backoff(attempt)
                        logger.warning(
                            f"[LICITAJA] Server error {response.status_code}. "
                            f"Retrying in {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                        continue

                raise SourceAPIError(self.code, response.status_code, response.text[:200])

            except httpx.TimeoutException as e:
                if attempt < self.MAX_RETRIES:
                    delay = self._calculate_backoff(attempt)
                    logger.warning(f"[LICITAJA] Timeout. Retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                    continue
                raise SourceTimeoutError(self.code, self._timeout) from e

            except httpx.RequestError as e:
                if attempt < self.MAX_RETRIES:
                    delay = self._calculate_backoff(attempt)
                    logger.warning(f"[LICITAJA] Request error: {e}. Retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                    continue
                raise SourceAPIError(self.code, 0, str(e)) from e

        raise SourceAPIError(self.code, 0, "Exhausted retries")

    def _calculate_backoff(self, attempt: int) -> float:
        """Exponential backoff with jitter."""
        delay = min(2.0 * (2 ** attempt), 60.0)
        return delay * random.uniform(0.5, 1.5)

    async def health_check(self) -> SourceStatus:
        """Check LicitaJá API availability.

        Uses a minimal search (1 item, today's date) as health probe.
        """
        try:
            client = await self._get_client()
            start = asyncio.get_running_loop().time()

            today = datetime.now(timezone.utc).strftime("%Y%m%d")
            response = await client.request(
                "POST",
                "/tender/search",
                params={
                    "items": 1,
                    "page": 1,
                    "date": today,
                },
                timeout=5.0,
            )

            elapsed_ms = (asyncio.get_running_loop().time() - start) * 1000

            if response.status_code == 200:
                if elapsed_ms > 5000:
                    logger.info(f"[LICITAJA] Health check slow: {elapsed_ms:.0f}ms")
                    return SourceStatus.DEGRADED
                return SourceStatus.AVAILABLE

            if response.status_code == 401:
                logger.warning("[LICITAJA] Health check: invalid API key")
                return SourceStatus.UNAVAILABLE

            logger.warning(f"[LICITAJA] Health check returned {response.status_code}")
            return SourceStatus.DEGRADED

        except (httpx.TimeoutException, httpx.RequestError) as e:
            logger.warning(f"[LICITAJA] Health check failed: {e}")
            return SourceStatus.UNAVAILABLE
        except Exception as e:
            logger.error(f"[LICITAJA] Unexpected health check error: {e}")
            return SourceStatus.UNAVAILABLE

    @staticmethod
    def _format_date(iso_date: str) -> str:
        """Convert YYYY-MM-DD to YYYYmmdd (LicitaJá format).

        Args:
            iso_date: Date string in YYYY-MM-DD format.

        Returns:
            Date string in YYYYmmdd format.
        """
        return iso_date.replace("-", "")

    async def fetch(
        self,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[UnifiedProcurement, None]:
        """Fetch open procurement processes from LicitaJá API.

        Uses POST /tender/search with server-side UF and date filtering.

        Args:
            data_inicial: Start date YYYY-MM-DD.
            data_final: End date YYYY-MM-DD.
            ufs: Optional set of UF codes for server-side filtering.
            **kwargs: Additional params (keyword, tender_value_min, tender_value_max).
        """
        params: Dict[str, Any] = {
            "opening_date_from": self._format_date(data_inicial),
            "opening_date_to": self._format_date(data_final),
            "items": self.PAGE_SIZE,
            "page": 1,
            "smartsearch": 0,  # Disable AI suggestions — we do our own classification
            "order": 0,  # Sort by opening date
        }

        # Server-side UF filtering (comma-separated state codes)
        if ufs:
            params["state"] = ",".join(sorted(ufs))

        # Optional keyword filtering from kwargs
        keyword = kwargs.get("keyword")
        if keyword:
            params["keyword"] = keyword

        # Optional value range filtering from kwargs
        value_min = kwargs.get("tender_value_min")
        value_max = kwargs.get("tender_value_max")
        if value_min is not None:
            params["tender_value_min"] = int(value_min)
        if value_max is not None:
            params["tender_value_max"] = int(value_max)

        seen_ids: Set[str] = set()
        total_fetched = 0
        page = 1
        fetch_start = asyncio.get_running_loop().time()

        while True:
            params["page"] = page

            page_start = asyncio.get_running_loop().time()
            try:
                response = await self._request_with_retry(
                    "POST", "/tender/search", params
                )
            except SourceAuthError:
                raise
            except Exception as e:
                page_elapsed_ms = int((asyncio.get_running_loop().time() - page_start) * 1000)
                logger.error(
                    f"[LICITAJA] Error fetching page {page} after {page_elapsed_ms}ms: {e}"
                )
                if total_fetched > 0:
                    logger.warning(f"[LICITAJA] Returning {total_fetched} partial results")
                    return
                raise

            page_elapsed_ms = int((asyncio.get_running_loop().time() - page_start) * 1000)
            logger.debug(f"[LICITAJA] Page {page} fetched in {page_elapsed_ms}ms")

            # Response format: { page, total_results, results: [...] }
            if isinstance(response, dict):
                data = response.get("results", [])
                total_results = response.get("total_results", 0)
            else:
                data = []
                total_results = 0

            if page == 1 and total_results > 0:
                total_pages = (total_results + self.PAGE_SIZE - 1) // self.PAGE_SIZE
                effective_pages = min(total_pages, self._max_pages)
                logger.info(
                    f"[LICITAJA] {total_results} total records across ~{total_pages} pages "
                    f"(capped at {effective_pages})"
                )

            if not data:
                break

            for raw_record in data:
                try:
                    record = self.normalize(raw_record)
                except Exception as e:
                    logger.warning(f"[LICITAJA] Failed to normalize record: {e}")
                    continue

                if record.source_id in seen_ids:
                    continue
                seen_ids.add(record.source_id)

                total_fetched += 1
                yield record

            # Check for more pages
            if total_results <= page * self.PAGE_SIZE:
                break

            page += 1

            if page > self._max_pages:
                self.was_truncated = True
                logger.warning(
                    f"[LICITAJA] Reached page limit ({self._max_pages}). "
                    f"Total records ({total_results}) may exceed fetched ({total_fetched}). "
                    f"Results truncated."
                )
                break

        total_elapsed_ms = int((asyncio.get_running_loop().time() - fetch_start) * 1000)
        logger.info(
            f"[LICITAJA] Fetch complete: {total_fetched} records in {total_elapsed_ms}ms "
            f"({page} pages, truncated={self.was_truncated})"
        )

    def normalize(self, raw_record: Dict[str, Any]) -> UnifiedProcurement:
        """Convert LicitaJá record to UnifiedProcurement.

        LicitaJá field mapping:
        - tenderId → source_id (prefixed with licitaja_)
        - tender_object → objeto
        - value → valor_estimado
        - agency → orgao
        - state → uf
        - city → municipio
        - type → modalidade
        - catalog_date → data_publicacao
        - close_date → data_encerramento (proposal deadline)
        - url → link_portal
        """
        try:
            # Extract and prefix source ID
            tender_id = raw_record.get("tenderId")
            if not tender_id:
                raise SourceParseError(self.code, "tenderId", raw_record)
            source_id = f"licitaja_{tender_id}"

            # Object description
            objeto = raw_record.get("tender_object") or ""

            # Value (may be None or 0)
            raw_value = raw_record.get("value")
            valor: Optional[float] = None
            if raw_value is not None:
                try:
                    valor = float(raw_value)
                    if valor <= 0:
                        valor = None
                except (ValueError, TypeError):
                    valor = None

            # Agency / organ
            orgao = raw_record.get("agency") or ""

            # CNPJ: LicitaJá may not provide CNPJ directly
            cnpj = raw_record.get("cnpj") or ""

            # Location
            uf = raw_record.get("state") or ""
            municipio = raw_record.get("city") or ""
            # City may include state suffix like "São Paulo-SP" — strip it
            if municipio and "-" in municipio:
                parts = municipio.rsplit("-", 1)
                municipio = parts[0].strip()
                if not uf and len(parts) > 1 and len(parts[1].strip()) == 2:
                    uf = parts[1].strip()

            # Parse dates (LicitaJá uses YYYYmmdd or ISO formats)
            data_publicacao = self._parse_datetime(raw_record.get("catalog_date"))
            data_abertura = self._parse_datetime(raw_record.get("opening_date"))
            data_encerramento = self._parse_datetime(raw_record.get("close_date"))

            # Modality/type
            modalidade = raw_record.get("type") or ""

            # Status: LicitaJá may provide a status field
            situacao = raw_record.get("status") or ""

            # Portal link
            url = raw_record.get("url") or ""
            link_portal = url if url else f"https://www.licitaja.com.br/licitacao/{tender_id}"

            # Edital number — LicitaJá may embed it in tender_object or separate field
            numero_edital = raw_record.get("number") or raw_record.get("edital_number") or ""

            # Year
            ano = ""
            if data_publicacao:
                ano = str(data_publicacao.year)

            # Lots (for additional detail if available)
            lots = raw_record.get("lots")
            if isinstance(lots, list) and lots and not objeto:
                # Fallback: use first lot description if main object is empty
                first_lot = lots[0] if lots else {}
                if isinstance(first_lot, dict):
                    objeto = first_lot.get("description") or objeto

            return UnifiedProcurement(
                source_id=source_id,
                source_name=self.code,
                objeto=objeto,
                valor_estimado=valor,
                orgao=orgao,
                cnpj_orgao=cnpj,
                uf=uf,
                municipio=municipio,
                data_publicacao=data_publicacao,
                data_abertura=data_abertura,
                data_encerramento=data_encerramento,
                numero_edital=numero_edital,
                ano=ano,
                modalidade=modalidade,
                situacao=situacao,
                esfera="",
                poder="",
                link_edital="",
                link_portal=link_portal,
                fetched_at=datetime.now(timezone.utc),
                raw_data=raw_record,
            )

        except SourceParseError:
            raise
        except Exception as e:
            logger.error(f"[LICITAJA] Normalization error: {e}")
            raise SourceParseError(self.code, "record", str(e)) from e

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime from LicitaJá formats.

        Supports:
        - YYYYmmdd (compact date, e.g., "20260324")
        - YYYY-MM-DD (ISO date)
        - YYYY-MM-DDTHH:MM:SS (ISO datetime)
        - Unix timestamp (int/float)

        Always returns UTC-aware datetimes.
        """
        from datetime import timezone as _tz

        if not value:
            return None

        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=_tz.utc)
            return value

        if isinstance(value, (int, float)):
            try:
                # LicitaJá may use epoch seconds or milliseconds
                if value > 1e12:
                    value = value / 1000
                return datetime.fromtimestamp(value, tz=_tz.utc)
            except (ValueError, OSError):
                return None

        if isinstance(value, str):
            formats = [
                "%Y%m%d",  # LicitaJá compact: 20260324
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%d/%m/%Y %H:%M:%S",
                "%d/%m/%Y",
            ]

            cleaned = value.replace("+00:00", "Z").replace("+0000", "Z")
            for fmt in formats:
                try:
                    dt = datetime.strptime(cleaned.rstrip("Z"), fmt.rstrip("Z"))
                    return dt.replace(tzinfo=_tz.utc)
                except ValueError:
                    continue

            logger.debug(f"[LICITAJA] Failed to parse datetime: {value}")

        return None

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            logger.debug(f"[LICITAJA] Client closed. Total requests: {self._request_count}")
        self._client = None

    async def __aenter__(self) -> "LicitaJaAdapter":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
