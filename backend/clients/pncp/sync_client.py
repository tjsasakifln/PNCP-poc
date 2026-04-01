"""Synchronous PNCP HTTP client (PNCPClient) with retry logic and rate limiting."""

import json
import logging
import time
from datetime import date, timedelta
from typing import Any, Callable, Dict, Generator, List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import (
    RetryConfig,
    DEFAULT_MODALIDADES,
    MODALIDADES_EXCLUIDAS,
)
from exceptions import PNCPAPIError
from middleware import request_id_var

from clients.pncp.retry import (
    DateFormat,
    _get_format_rotation,
    _validate_date_params,
    _handle_422_response,
    _set_cached_date_format,
    calculate_delay,
    format_date,
)

logger = logging.getLogger(__name__)


# ============================================================================
# PNCP Degraded Error + Status Map — re-exported from async_client
# (DEBT-v3-S3 Phase 1.2: canonical definitions moved to async_client.py)
# ============================================================================

from clients.pncp.async_client import PNCPDegradedError, STATUS_PNCP_MAP  # noqa: E402, F401


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

        STORY-282 AC1: Uses aggressive timeout defaults from config.

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
            "User-Agent": "SmartLic/1.0 (procurement-search; contato@smartlic.tech)",
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
            ValueError: If modalidade is missing (PNCP API requires codigoModalidadeContratacao)
            PNCPAPIError: On non-retryable errors or after max retries
            PNCPRateLimitError: If rate limit persists after retries
        """
        # CRIT-FLT-008 AC1: Guard — PNCP API requires codigoModalidadeContratacao (HTTP 400 without it)
        if not modalidade:
            raise ValueError(
                "codigoModalidadeContratacao is required by PNCP API. "
                "Sending a request without it will return HTTP 400."
            )

        self._rate_limit()

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

        url = f"{self.BASE_URL}/contratacoes/publicacao"

        # STORY-226 AC23: Forward X-Request-ID for distributed tracing
        req_id = request_id_var.get("-")
        headers = {}
        if req_id and req_id != "-":
            headers["X-Request-ID"] = req_id

        # UX-336: Track format rotation for 422 recovery
        format_rotation = _get_format_rotation()
        format_idx = 0

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
                    logger.debug(
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

                    # UX-336 AC3+AC5: Cache successful format + telemetry
                    current_fmt = format_rotation[format_idx] if format_idx < len(format_rotation) else DateFormat.YYYYMMDD
                    if current_fmt != DateFormat.YYYYMMDD or format_idx > 0:
                        _set_cached_date_format(current_fmt)
                        logger.debug(f"pncp_date_format_accepted format={current_fmt}")

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

                # GTM-FIX-032 AC6 + UX-336 AC1: 422 handling with format rotation
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
                        time.sleep(self.config.base_delay)
                        continue
                    if isinstance(result, dict):
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

                # CRIT-043 AC3+AC4: 400 on page>1 is expected (past last page)
                if response.status_code == 400 and pagina > 1:
                    logger.debug(
                        f"CRIT-043: HTTP 400 at page {pagina} — past last page. "
                        f"UF={params.get('uf', '?')}, mod={params.get('codigoModalidadeContratacao', '?')}"
                    )
                    return {
                        "data": [],
                        "totalRegistros": 0,
                        "totalPaginas": pagina - 1,
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
            logger.debug(
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
                logger.debug(
                    f"Processing date chunk {chunk_idx + 1}/{len(date_chunks)}: "
                    f"{chunk_start} to {chunk_end}"
                )

            for modalidade in modalidades_to_fetch:
                logger.debug(f"Fetching modality {modalidade}")

                # If specific UFs provided, fetch each separately
                if ufs:
                    for uf in ufs:
                        logger.debug(f"Fetching modalidade={modalidade}, UF={uf}")
                        try:
                            for item in self._fetch_by_uf(
                                chunk_start, chunk_end, modalidade, uf, on_progress
                            ):
                                normalized = self._normalize_item(item, uf_hint=uf)
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
                    logger.debug(f"Fetching modalidade={modalidade}, all UFs")
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

    def _fetch_by_uf(
        self,
        data_inicial: str,
        data_final: str,
        modalidade: int,
        uf: str | None,
        on_progress: Callable[[int, int, int], None] | None,
        max_pages: int | None = None,  # STORY-282 AC2: Defaults to PNCP_MAX_PAGES (5)
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
        from config import PNCP_MAX_PAGES
        if max_pages is None:
            max_pages = PNCP_MAX_PAGES
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
