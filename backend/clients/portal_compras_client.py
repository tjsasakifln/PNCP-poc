"""Portal de Compras Publicas API client adapter.

This module implements the SourceAdapter interface for the Portal de Compras
Publicas API (https://apipcp.portaldecompraspublicas.com.br/).

API Characteristics:
- REST API with JSON responses
- Requires API key authentication (PublicKey header)
- Returns finalized/completed procurement processes
- Integrated with PNCP

Documentation: https://apipcp.portaldecompraspublicas.com.br/comprador/apidoc/
API Key Request: https://bibliotecapcp.zendesk.com/hc/pt-br/articles/4593549708570
"""

import asyncio
import logging
import os
import random
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional, Set

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


class PortalComprasAdapter(SourceAdapter):
    """
    Adapter for Portal de Compras Publicas API.

    This adapter fetches procurement data from Portal de Compras Publicas,
    which is 100% integrated with PNCP and provides access to finalized
    procurement processes.

    Attributes:
        BASE_URL: API base URL
        DEFAULT_TIMEOUT: Request timeout in seconds
        MAX_RETRIES: Maximum number of retry attempts
        RATE_LIMIT_DELAY: Minimum delay between requests (seconds)

    Environment Variables:
        PORTAL_COMPRAS_API_KEY: API key for authentication (required)

    Example:
        >>> async with PortalComprasAdapter() as adapter:
        ...     async for record in adapter.fetch("2026-01-01", "2026-01-31", {"SP"}):
        ...         print(record.objeto)
    """

    BASE_URL = "https://apipcp.portaldecompraspublicas.com.br"
    DEFAULT_TIMEOUT = 25  # seconds (slightly less than PNCP to allow aggregation time)
    MAX_RETRIES = 3
    RATE_LIMIT_DELAY = 0.15  # 150ms between requests (~6.7 req/s)
    PAGE_SIZE = 50  # Items per page

    # Source metadata (constant)
    _metadata = SourceMetadata(
        name="Portal de Compras Publicas",
        code="PORTAL_COMPRAS",
        base_url="https://apipcp.portaldecompraspublicas.com.br",
        documentation_url="https://apipcp.portaldecompraspublicas.com.br/comprador/apidoc/",
        capabilities={
            SourceCapability.PAGINATION,
            SourceCapability.DATE_RANGE,
            SourceCapability.FILTER_BY_UF,
        },
        rate_limit_rps=6.7,
        typical_response_ms=2500,
        priority=2,  # Second priority after PNCP (priority 1)
    )

    def __init__(self, api_key: Optional[str] = None, timeout: Optional[int] = None):
        """
        Initialize Portal de Compras adapter.

        Args:
            api_key: API key for authentication. If not provided, reads from
                     PORTAL_COMPRAS_API_KEY environment variable.
            timeout: Request timeout in seconds. Defaults to DEFAULT_TIMEOUT.
        """
        self._api_key = api_key or os.environ.get("PORTAL_COMPRAS_API_KEY", "")
        self._timeout = timeout or self.DEFAULT_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None
        self._last_request_time = 0.0
        self._request_count = 0

    @property
    def metadata(self) -> SourceMetadata:
        """Return source metadata."""
        return self._metadata

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with proper configuration."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=httpx.Timeout(self._timeout),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "SmartPNCP/1.0 (procurement-aggregator)",
                    # API key authentication
                    # TODO: Verify exact header name from API docs (may be "PublicKey", "X-API-Key", etc.)
                    "PublicKey": self._api_key,
                },
            )
        return self._client

    async def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = asyncio.get_running_loop().time() - self._last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            sleep_time = self.RATE_LIMIT_DELAY - elapsed
            await asyncio.sleep(sleep_time)
        self._last_request_time = asyncio.get_running_loop().time()
        self._request_count += 1

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and rate limiting.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g., "/processos")
            params: Query parameters

        Returns:
            Parsed JSON response

        Raises:
            SourceTimeoutError: On timeout after retries
            SourceRateLimitError: On 429 after retries
            SourceAuthError: On 401/403 authentication failure
            SourceAPIError: On other API errors
        """
        await self._rate_limit()
        client = await self._get_client()

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                logger.debug(
                    f"[PORTAL_COMPRAS] {method} {path} params={params} "
                    f"attempt={attempt + 1}/{self.MAX_RETRIES + 1}"
                )

                response = await client.request(method, path, params=params)

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < self.MAX_RETRIES:
                        logger.warning(
                            f"[PORTAL_COMPRAS] Rate limited. Waiting {retry_after}s"
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    raise SourceRateLimitError(self.code, retry_after)

                # Handle auth errors (no retry)
                if response.status_code in (401, 403):
                    raise SourceAuthError(
                        self.code,
                        f"Authentication failed: {response.text[:200]}"
                    )

                # Success
                if response.status_code == 200:
                    return response.json()

                # No content
                if response.status_code == 204:
                    return {"data": [], "total": 0, "pagina": 1, "totalPaginas": 0}

                # Other errors
                if response.status_code >= 500:
                    if attempt < self.MAX_RETRIES:
                        delay = self._calculate_backoff(attempt)
                        logger.warning(
                            f"[PORTAL_COMPRAS] Server error {response.status_code}. "
                            f"Retrying in {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                        continue

                raise SourceAPIError(self.code, response.status_code, response.text)

            except httpx.TimeoutException as e:
                if attempt < self.MAX_RETRIES:
                    delay = self._calculate_backoff(attempt)
                    logger.warning(
                        f"[PORTAL_COMPRAS] Timeout. Retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                    continue
                raise SourceTimeoutError(self.code, self._timeout) from e

            except httpx.RequestError as e:
                if attempt < self.MAX_RETRIES:
                    delay = self._calculate_backoff(attempt)
                    logger.warning(
                        f"[PORTAL_COMPRAS] Request error: {e}. Retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                    continue
                raise SourceAPIError(self.code, 0, str(e)) from e

        # Should not reach here
        raise SourceAPIError(self.code, 0, "Exhausted retries")

    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter."""
        delay = min(2.0 * (2**attempt), 60.0)
        # Add jitter (+/- 50%)
        delay *= random.uniform(0.5, 1.5)
        return delay

    async def health_check(self) -> SourceStatus:
        """
        Check if Portal de Compras API is available.

        Performs a lightweight request to verify API connectivity and
        authentication status.

        Returns:
            SourceStatus.AVAILABLE if API responds successfully
            SourceStatus.DEGRADED if API responds but slowly
            SourceStatus.UNAVAILABLE if API fails to respond
        """
        if not self._api_key:
            logger.warning("[PORTAL_COMPRAS] No API key configured")
            return SourceStatus.UNAVAILABLE

        try:
            client = await self._get_client()
            start = asyncio.get_running_loop().time()

            # TODO: Verify actual health check endpoint from API docs
            # Using a minimal query as health check
            response = await client.get(
                "/api/v1/processos",
                params={"pagina": 1, "tamanhoPagina": 1},
                timeout=5.0,
            )

            elapsed_ms = (asyncio.get_running_loop().time() - start) * 1000

            if response.status_code in (401, 403):
                logger.warning("[PORTAL_COMPRAS] Authentication failed in health check")
                return SourceStatus.UNAVAILABLE

            if response.status_code == 200:
                if elapsed_ms > 3000:
                    logger.info(
                        f"[PORTAL_COMPRAS] Health check slow: {elapsed_ms:.0f}ms"
                    )
                    return SourceStatus.DEGRADED
                return SourceStatus.AVAILABLE

            logger.warning(
                f"[PORTAL_COMPRAS] Health check returned {response.status_code}"
            )
            return SourceStatus.DEGRADED

        except (httpx.TimeoutException, httpx.RequestError) as e:
            logger.warning(f"[PORTAL_COMPRAS] Health check failed: {e}")
            return SourceStatus.UNAVAILABLE
        except Exception as e:
            logger.error(f"[PORTAL_COMPRAS] Unexpected health check error: {e}")
            return SourceStatus.UNAVAILABLE

    async def fetch(
        self,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[UnifiedProcurement, None]:
        """
        Fetch procurement records from Portal de Compras Publicas.

        Args:
            data_inicial: Start date in YYYY-MM-DD format
            data_final: End date in YYYY-MM-DD format
            ufs: Optional set of Brazilian state codes to filter
            **kwargs: Additional parameters (status, modalidade, etc.)

        Yields:
            UnifiedProcurement records

        Raises:
            SourceAuthError: If API key is invalid/missing
            SourceTimeoutError: If requests timeout
            SourceAPIError: On other API errors

        Note:
            This adapter fetches finalized/completed processes only,
            as per Portal de Compras API limitations.
        """
        if not self._api_key:
            logger.warning("[PORTAL_COMPRAS] No API key configured - skipping fetch")
            return

        # Build base parameters
        # TODO: Verify exact parameter names from API documentation
        params: Dict[str, Any] = {
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "tamanhoPagina": self.PAGE_SIZE,
        }

        # Add optional filters
        if ufs:
            # If API supports UF filter, add it
            # TODO: Verify if API supports multiple UFs or single UF
            # For now, we'll filter client-side if multiple UFs
            if len(ufs) == 1:
                params["uf"] = list(ufs)[0]
                filter_ufs_client_side = False
            else:
                filter_ufs_client_side = True
        else:
            filter_ufs_client_side = False

        # Fetch all pages
        pagina = 1
        total_fetched = 0
        seen_ids: Set[str] = set()

        while True:
            params["pagina"] = pagina

            try:
                # TODO: Verify actual endpoint path from API docs
                response = await self._request_with_retry("GET", "/api/v1/processos", params)
            except SourceAuthError:
                # Re-raise auth errors (no point retrying)
                raise
            except Exception as e:
                logger.error(f"[PORTAL_COMPRAS] Error fetching page {pagina}: {e}")
                if total_fetched > 0:
                    # Return partial results if we already have some
                    logger.warning(
                        f"[PORTAL_COMPRAS] Returning {total_fetched} partial results"
                    )
                    return
                raise

            # Extract data
            # TODO: Verify actual response structure from API docs
            data = response.get("data", response.get("processos", []))
            total_pages = response.get("totalPaginas", response.get("total_paginas", 1))
            total_records = response.get("total", response.get("totalRegistros", 0))

            if pagina == 1:
                logger.info(
                    f"[PORTAL_COMPRAS] Query returned {total_records} total records "
                    f"across {total_pages} pages"
                )

            if not data:
                logger.debug(f"[PORTAL_COMPRAS] No more data at page {pagina}")
                break

            # Process records
            for raw_record in data:
                try:
                    record = self.normalize(raw_record)

                    # Skip duplicates
                    if record.source_id in seen_ids:
                        continue
                    seen_ids.add(record.source_id)

                    # Client-side UF filtering if needed
                    if filter_ufs_client_side and record.uf not in ufs:
                        continue

                    total_fetched += 1
                    yield record

                except Exception as e:
                    logger.warning(
                        f"[PORTAL_COMPRAS] Failed to normalize record: {e}"
                    )
                    continue

            # Check for more pages
            if pagina >= total_pages:
                break

            pagina += 1

            # Safety limit to prevent infinite loops
            if pagina > 100:
                logger.warning("[PORTAL_COMPRAS] Reached page limit (100)")
                break

        logger.info(
            f"[PORTAL_COMPRAS] Fetch complete: {total_fetched} records "
            f"from {pagina} pages"
        )

    def normalize(self, raw_record: Dict[str, Any]) -> UnifiedProcurement:
        """
        Convert Portal de Compras record to UnifiedProcurement.

        Field Mapping (based on API research - TODO: verify with actual API):
            codigo -> source_id
            objeto -> objeto
            valorEstimado -> valor_estimado
            orgao.nome -> orgao
            orgao.cnpj -> cnpj_orgao
            uf -> uf
            municipio -> municipio
            dataPublicacao -> data_publicacao
            dataAbertura -> data_abertura
            tipoLicitacao -> modalidade
            situacao -> situacao
            linkDocumentos -> link_edital
            linkPortal -> link_portal

        Args:
            raw_record: Raw record from API response

        Returns:
            Normalized UnifiedProcurement record

        Raises:
            SourceParseError: If critical fields cannot be parsed
        """
        try:
            # Extract nested orgao data
            orgao_data = raw_record.get("orgao") or {}
            if isinstance(orgao_data, str):
                # Sometimes API returns orgao as string directly
                orgao_nome = orgao_data
                orgao_cnpj = ""
            else:
                orgao_nome = orgao_data.get("nome", "")
                orgao_cnpj = orgao_data.get("cnpj", "")

            # Parse dates
            data_publicacao = self._parse_datetime(
                raw_record.get("dataPublicacao")
                or raw_record.get("data_publicacao")
            )
            data_abertura = self._parse_datetime(
                raw_record.get("dataAbertura")
                or raw_record.get("data_abertura")
            )
            data_encerramento = self._parse_datetime(
                raw_record.get("dataEncerramento")
                or raw_record.get("data_encerramento")
            )

            # Extract source ID
            source_id = str(
                raw_record.get("codigo")
                or raw_record.get("id")
                or raw_record.get("processo_id")
                or ""
            )

            if not source_id:
                raise SourceParseError(self.code, "source_id", raw_record)

            # Extract value (handle different formats)
            valor = raw_record.get("valorEstimado") or raw_record.get("valor_estimado") or 0
            if isinstance(valor, str):
                # Handle string format (e.g., "1.234,56" or "1234.56")
                valor = valor.replace(".", "").replace(",", ".")
                try:
                    valor = float(valor)
                except ValueError:
                    valor = 0.0

            # Extract edital number and year
            numero_edital = raw_record.get("numeroEdital") or raw_record.get("numero_edital") or ""
            ano = raw_record.get("ano") or raw_record.get("anoProcesso") or ""

            # If ano not provided, try to extract from data_publicacao
            if not ano and data_publicacao:
                ano = str(data_publicacao.year)

            return UnifiedProcurement(
                # Identification
                source_id=source_id,
                source_name=self.code,
                # Core fields
                objeto=raw_record.get("objeto") or raw_record.get("descricao") or "",
                valor_estimado=float(valor),
                orgao=orgao_nome or raw_record.get("orgao_nome") or "",
                cnpj_orgao=orgao_cnpj or raw_record.get("cnpj") or "",
                uf=raw_record.get("uf") or raw_record.get("estado") or "",
                municipio=raw_record.get("municipio") or raw_record.get("cidade") or "",
                data_publicacao=data_publicacao,
                # Optional fields
                data_abertura=data_abertura,
                data_encerramento=data_encerramento,
                numero_edital=numero_edital,
                ano=str(ano) if ano else "",
                modalidade=raw_record.get("tipoLicitacao") or raw_record.get("modalidade") or "",
                situacao=raw_record.get("situacao") or raw_record.get("status") or "",
                esfera=raw_record.get("esfera") or "",
                poder=raw_record.get("poder") or "",
                # Links
                link_edital=raw_record.get("linkDocumentos") or raw_record.get("link_edital") or "",
                link_portal=raw_record.get("linkPortal") or raw_record.get("link") or "",
                # Metadata
                fetched_at=datetime.now(timezone.utc),
                raw_data=raw_record,
            )

        except SourceParseError:
            raise
        except Exception as e:
            logger.error(f"[PORTAL_COMPRAS] Normalization error: {e}")
            raise SourceParseError(self.code, "record", str(e)) from e

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """
        Parse datetime from various formats.

        Handles:
        - ISO 8601 strings (2026-01-15T10:30:00Z)
        - Date strings (2026-01-15)
        - Timestamps (milliseconds)
        - None/empty values

        Args:
            value: Datetime value in various formats

        Returns:
            Parsed datetime or None if parsing fails
        """
        if not value:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, (int, float)):
            # Assume milliseconds timestamp
            try:
                return datetime.fromtimestamp(value / 1000)
            except (ValueError, OSError):
                return None

        if isinstance(value, str):
            # Try various formats
            formats = [
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%d/%m/%Y %H:%M:%S",
                "%d/%m/%Y",
            ]

            # Handle timezone suffix
            value = value.replace("+00:00", "Z").replace("+0000", "Z")

            for fmt in formats:
                try:
                    return datetime.strptime(value.rstrip("Z"), fmt.rstrip("Z"))
                except ValueError:
                    continue

            logger.debug(f"[PORTAL_COMPRAS] Failed to parse datetime: {value}")

        return None

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            logger.debug(
                f"[PORTAL_COMPRAS] Client closed. Total requests: {self._request_count}"
            )
        self._client = None

    async def __aenter__(self) -> "PortalComprasAdapter":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit - close client."""
        await self.close()
