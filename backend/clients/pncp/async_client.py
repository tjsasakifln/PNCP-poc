"""Async PNCP HTTP client: AsyncPNCPClient.

PNCPLegacyAdapter and the module-level buscar_todas_ufs_paralelo convenience
function live in clients.pncp.adapter (extracted to keep files ≤700 LOC).
The three parallel-fetch methods (_fetch_modality_with_timeout,
_fetch_uf_all_pages, buscar_todas_ufs_paralelo) live in
clients.pncp._parallel_mixin via _PNCPParallelMixin.
"""

import asyncio
import json
import logging
import random
import time
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional

import httpx

from config import (
    RetryConfig,
    DEFAULT_MODALIDADES,
    MODALIDADES_EXCLUIDAS,
    PNCP_TIMEOUT_PER_MODALITY,
    PNCP_MODALITY_RETRY_BACKOFF,
    PNCP_TIMEOUT_PER_UF,
    PNCP_TIMEOUT_PER_UF_DEGRADED,
    PNCP_BATCH_SIZE,
    PNCP_BATCH_DELAY_S,
)
from exceptions import PNCPAPIError
from middleware import request_id_var

from clients.pncp.circuit_breaker import _circuit_breaker  # noqa: F401
from clients.pncp.retry import (
    ParallelFetchResult,
    ModalityFetchState,
    DateFormat,
    UFS_BY_POPULATION,
    _get_format_rotation,
    _validate_date_params,
    _handle_422_response,
    _set_cached_date_format,
    calculate_delay,
    format_date,
)
from clients.pncp._parallel_mixin import _PNCPParallelMixin

logger = logging.getLogger(__name__)


# ============================================================================
# PNCP Degraded Error (moved from sync_client — DEBT-v3-S3 Phase 1.2)
# ============================================================================

class PNCPDegradedError(PNCPAPIError):
    """Raised when PNCP circuit breaker is in degraded state."""
    pass


# ============================================================================
# Status Mapping for PNCP API (moved from sync_client — DEBT-v3-S3 Phase 1.2)
# ============================================================================

# Mapping from StatusLicitacao enum values to PNCP API parameter values
# Note: Import StatusLicitacao at runtime to avoid circular imports
STATUS_PNCP_MAP = {
    "recebendo_proposta": "recebendo_proposta",
    "em_julgamento": "propostas_encerradas",
    "encerrada": "encerrada",
    "todos": None,  # Don't send status parameter - return all
}


# ============================================================================
# Normalize helper (moved from sync_client — DEBT-v3-S3 Phase 1.2)
# ============================================================================

def _normalize_item(item: Dict[str, Any], uf_hint: str | None = None) -> Dict[str, Any]:
    """
    Flatten nested PNCP API response into the flat format expected by
    filter.py, excel.py and llm.py.

    The PNCP API nests org/location data inside ``orgaoEntidade`` and
    ``unidadeOrgao`` objects.  The rest of the codebase expects flat
    top-level keys: ``uf``, ``municipio``, ``nomeOrgao``, ``codigoCompra``.

    Also ensures linkSistemaOrigem is preserved for Excel hyperlinks.
    Note: linkProcessoEletronico is always empty from PNCP API (CRIT-FLT-008).

    Args:
        item: Raw PNCP API response item.
        uf_hint: Fallback UF code when the API returns empty ufSigla
                 (common for federal agencies). Typically the UF that
                 was queried.
    """
    unidade = item.get("unidadeOrgao") or {}
    orgao = item.get("orgaoEntidade") or {}

    uf_from_api = unidade.get("ufSigla", "")
    # P0-FIX: Federal agencies often return empty ufSigla.
    # Use the queried UF as fallback so the item is not rejected by the UF filter.
    if not uf_from_api and uf_hint:
        uf_from_api = uf_hint
        item["_uf_from_hint"] = True
    item["uf"] = uf_from_api
    item["municipio"] = unidade.get("municipioNome", "")
    item["nomeOrgao"] = orgao.get("razaoSocial", "") or unidade.get("nomeUnidade", "")
    item["codigoCompra"] = item.get("numeroControlePNCP", "")

    # Preserve link fields (already in root level from API)
    # CRIT-FLT-008: linkSistemaOrigem is the primary link (86% populated).
    # linkProcessoEletronico is always empty from PNCP API but kept for other sources.

    return item


class AsyncPNCPClient(_PNCPParallelMixin):
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
        """Async context manager entry.

        STORY-282 AC1: Uses split connect/read timeouts for fail-fast behavior.
        STORY-296 AC2: Isolated connection pool via httpx.Limits.
        """
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=self.config.connect_timeout,
                read=self.config.read_timeout,
                write=self.config.read_timeout,
                pool=self.config.connect_timeout,
            ),
            limits=httpx.Limits(
                max_connections=self.max_concurrent + 2,
                max_keepalive_connections=self.max_concurrent,
            ),
            headers={
                "User-Agent": "SmartLic/1.0 (procurement-search; contato@smartlic.tech)",
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
                "tamanhoPagina": 50,
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

    async def fetch_bid_items(
        self,
        cnpj: str,
        ano: str,
        sequencial: str,
    ) -> List[Dict[str, Any]]:
        """Fetch individual items for a bid from PNCP API (GTM-RESILIENCE-D01 AC1).

        Endpoint: GET /v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens

        Args:
            cnpj: CNPJ of the contracting entity (digits only).
            ano: Year of the procurement (e.g., "2026").
            sequencial: Sequential number of the procurement.

        Returns:
            List of item dicts with keys: descricao, codigoNcm, unidadeMedida,
            quantidade, valorUnitario. Returns empty list on 404 or timeout.
        """
        from config import ITEM_INSPECTION_TIMEOUT

        if self._client is None:
            raise RuntimeError("Client not initialized. Use async context manager.")

        # Clean CNPJ — digits only
        cnpj_clean = "".join(c for c in cnpj if c.isdigit())
        url = f"{self.BASE_URL}/orgaos/{cnpj_clean}/compras/{ano}/{sequencial}/itens"

        for attempt in range(2):  # 1 initial + 1 retry
            try:
                response = await asyncio.wait_for(
                    self._client.get(url),
                    timeout=ITEM_INSPECTION_TIMEOUT,
                )

                if response.status_code == 200:
                    data = response.json()
                    # API may return list directly or nested
                    items = data if isinstance(data, list) else data.get("itens", data.get("data", []))
                    return [
                        {
                            "descricao": item.get("descricao", ""),
                            "codigoNcm": item.get("materialOuServico", {}).get("codigoNcm", "")
                                if isinstance(item.get("materialOuServico"), dict)
                                else item.get("codigoNcm", ""),
                            "unidadeMedida": item.get("unidadeMedida", ""),
                            "quantidade": item.get("quantidade", 0),
                            "valorUnitario": item.get("valorUnitarioEstimado", 0)
                                or item.get("valorUnitario", 0),
                        }
                        for item in items
                    ]

                if response.status_code == 404:
                    logger.debug(
                        f"PNCP items 404 for {cnpj_clean}/{ano}/{sequencial} — no items available"
                    )
                    return []

                # Retryable: 429/5xx
                if attempt == 0 and response.status_code in (429, 500, 502, 503, 504):
                    retry_after = float(response.headers.get("Retry-After", "1"))
                    logger.debug(
                        f"PNCP items {response.status_code} — retrying in {retry_after}s"
                    )
                    await asyncio.sleep(min(retry_after, 3.0))
                    continue

                logger.debug(
                    f"PNCP items unexpected {response.status_code} for "
                    f"{cnpj_clean}/{ano}/{sequencial}"
                )
                return []

            except (asyncio.TimeoutError, httpx.TimeoutException):
                if attempt == 0:
                    logger.debug("PNCP items timeout — retrying once")
                    continue
                logger.debug(
                    f"PNCP items timeout (2nd attempt) for {cnpj_clean}/{ano}/{sequencial}"
                )
                return []
            except (httpx.HTTPError, Exception) as exc:
                logger.debug(f"PNCP items fetch error: {type(exc).__name__}: {exc}")
                return []

        return []

    async def _rate_limit(self) -> None:
        """Enforce rate limiting — shared Redis when available, local fallback.

        B-06 AC7: Uses RedisRateLimiter for cross-worker coordination.
        Local sleep-based limiter always runs as baseline.
        """
        # Shared rate limiter (Redis-backed, cross-worker) — AC7
        from rate_limiter import pncp_rate_limiter
        await pncp_rate_limiter.acquire(timeout=5.0)

        # Local rate limiter (per-worker baseline, always active)
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

        Raises:
            ValueError: If modalidade is missing (PNCP API requires codigoModalidadeContratacao)
        """
        # CRIT-FLT-008 AC1: Guard — PNCP API requires codigoModalidadeContratacao (HTTP 400 without it)
        if not modalidade:
            raise ValueError(
                "codigoModalidadeContratacao is required by PNCP API. "
                "Sending a request without it will return HTTP 400."
            )

        if self._client is None:
            raise RuntimeError("Client not initialized. Use async context manager.")

        await self._rate_limit()

        # GTM-FIX-032 AC2: Pre-flight date validation + formatting
        data_inicial_fmt = data_inicial.replace("-", "")
        data_final_fmt = data_final.replace("-", "")
        _validate_date_params(data_inicial, data_inicial_fmt, data_final, data_final_fmt)
        if data_inicial_fmt > data_final_fmt:
            logger.warning(f"Dates swapped: {data_inicial_fmt} > {data_final_fmt}. Auto-swapping.")
            data_inicial_fmt, data_final_fmt = data_final_fmt, data_inicial_fmt

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

        # UX-336: Track format rotation for 422 recovery
        format_rotation = _get_format_rotation()
        format_idx = 0

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
                    logger.debug(f"Rate limited (429). Waiting {retry_after}s")
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

                    # UX-336 AC3+AC5: Cache successful format + telemetry
                    current_fmt = format_rotation[format_idx] if format_idx < len(format_rotation) else DateFormat.YYYYMMDD
                    if current_fmt != DateFormat.YYYYMMDD or format_idx > 0:
                        _set_cached_date_format(current_fmt)
                        logger.debug(f"pncp_date_format_accepted format={current_fmt}")

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

                # GTM-FIX-032 AC1+AC4 + UX-336 AC1: 422 handling with format rotation
                if response.status_code == 422:
                    # UX-336: Use format_idx to determine if more formats are available
                    has_more_formats = (format_idx + 1) < len(format_rotation)
                    effective_attempt = 0 if has_more_formats else 1
                    result = _handle_422_response(
                        response.text, params, data_inicial, data_final,
                        attempt=effective_attempt, max_retries=1
                    )
                    if result == "retry_format" and has_more_formats:
                        # UX-336: Try next date format
                        format_idx += 1
                        next_fmt = format_rotation[format_idx]
                        logger.debug(
                            f"UX-336: Retrying with format {next_fmt} "
                            f"(attempt {format_idx + 1}/{len(format_rotation)})"
                        )
                        params["dataInicial"] = format_date(data_inicial, next_fmt)
                        params["dataFinal"] = format_date(data_final, next_fmt)
                        await asyncio.sleep(self.config.base_delay)
                        continue
                    if isinstance(result, dict):
                        # AC4.3: Return empty instead of crashing for date-related 422s
                        return result
                    # UX-336 AC6: All formats failed
                    raise PNCPAPIError(
                        f"PNCP 422 after all {len(format_rotation)} date formats for "
                        f"UF={params.get('uf', '?')} mod={params.get('codigoModalidadeContratacao', '?')}. "
                        f"Reduza o período de busca."
                    )

                # Log 400 response body for diagnostics (page 1 = unexpected; page>1 = past-last-page)
                if response.status_code == 400:
                    logger.warning(
                        "[PNCP] HTTP 400 response body: %s (params: %s)",
                        response.text[:500] if response.text else "empty",
                        {k: v for k, v in params.items() if k != "pagina"},
                    )

                # CRIT-043 AC2: 400 on page>1 = past last page, return empty
                if response.status_code == 400 and pagina > 1:
                    logger.debug(
                        f"CRIT-043: HTTP 400 at page {pagina} — past last page, "
                        f"returning empty result"
                    )
                    return {
                        "data": [],
                        "totalRegistros": 0,
                        "totalPaginas": pagina - 1,
                        "paginaAtual": pagina,
                        "paginasRestantes": 0,
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
                    logger.debug(
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
                    logger.debug(f"Timeout. Retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                else:
                    raise PNCPAPIError(f"Timeout after {self.config.max_retries + 1} attempts") from e

            except httpx.HTTPError as e:
                if attempt < self.config.max_retries:
                    delay = min(
                        self.config.base_delay * (self.config.exponential_base ** attempt),
                        self.config.max_delay
                    )
                    logger.debug(f"HTTP error: {e}. Retrying in {delay:.1f}s")
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
        max_pages: int | None = None,
        state: ModalityFetchState | None = None,
    ) -> tuple[List[Dict[str, Any]], bool]:
        """Fetch all pages for a single UF + single modality.

        This is the inner loop extracted from ``_fetch_uf_all_pages`` so that
        each modality can be wrapped with its own timeout (STORY-252 AC6).

        Uses a shared ``ModalityFetchState`` when provided so that items
        accumulated before a timeout cancellation are preserved (partial
        accumulation pattern).

        Args:
            uf: State code (e.g. "SP").
            data_inicial: Start date YYYY-MM-DD.
            data_final: End date YYYY-MM-DD.
            modalidade: Modality code.
            status: Optional PNCP status filter value.
            max_pages: Maximum pages per modality (default from PNCP_MAX_PAGES env).
            state: Optional shared mutable state for partial accumulation.

        Returns:
            Tuple of (items, was_truncated). was_truncated is True when
            max_pages was hit while more pages remained (GTM-FIX-004),
            or when the fetch was interrupted by timeout with partial data.
        """
        from config import PNCP_MAX_PAGES
        if max_pages is None:
            max_pages = PNCP_MAX_PAGES

        # Use shared state if provided (for partial accumulation on timeout),
        # otherwise create local state (backward-compatible).
        if state is None:
            state = ModalityFetchState()

        pagina = state.pages_fetched + 1

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
                    if item_id and item_id not in state.seen_ids:
                        state.seen_ids.add(item_id)
                        normalized = _normalize_item(item, uf_hint=uf)
                        state.items.append(normalized)

                state.pages_fetched = pagina

                if paginas_restantes <= 0:
                    break

                # STORY-282 AC2 + GTM-FIX-004: Detect truncation when max_pages reached
                total_records = response.get("totalRegistros", 0)
                if pagina >= max_pages and paginas_restantes > 0:
                    state.was_truncated = True
                    logger.warning(
                        f"STORY-282: MAX_PAGES ({max_pages}) reached for UF={uf}, "
                        f"modalidade={modalidade}. Fetched {len(state.items)}/{total_records} items. "
                        f"Remaining pages: {paginas_restantes}. "
                        f"Truncating to cap latency (set PNCP_MAX_PAGES to increase)."
                    )

                pagina += 1

            except PNCPAPIError as e:
                # CRIT-043 AC1+AC4: Distinguish expected 400 (page>1) from real errors (page 1)
                error_str = str(e)
                is_expected_400 = "status 400" in error_str and pagina > 1
                if is_expected_400:
                    # AC1: Expected — past last page. No CB failure, DEBUG log.
                    logger.debug(
                        f"CRIT-043: Expected 400 at page {pagina} for UF={uf}, "
                        f"modalidade={modalidade} (past last page). Stopping pagination."
                    )
                else:
                    # AC4: Real error (page 1 or non-400). Record CB failure, WARNING.
                    await _circuit_breaker.record_failure()
                    logger.warning(
                        f"Error fetching UF={uf}, modalidade={modalidade}, "
                        f"page={pagina}: {e}"
                    )
                break

        return state.items, state.was_truncated
