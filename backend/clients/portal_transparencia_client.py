"""Portal da Transparencia (CGU) API client adapter.

This module implements the SourceAdapter interface for the Portal da
Transparencia API managed by CGU (Controladoria-Geral da Uniao).

API Characteristics:
- REST API with JSON responses
- Requires API key authentication (chave-api-dados header)
- Federal procurement data (licitacoes)
- Rate limit: 90 req/min (06h-24h), 300 req/min (00h-06h)
- Pagination: 1-indexed 'pagina' parameter, iterate until empty array
- Date format: DD/MM/AAAA
- Max query period: 1 month per request
- No server-side UF filter -- filter client-side from response

Documentation: https://api.portaldatransparencia.gov.br/swagger-ui/index.html
"""

import asyncio
import logging
import os
import random
import time
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional, Set, Tuple

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


class PortalTransparenciaAdapter(SourceAdapter):
    """
    Adapter for Portal da Transparencia (CGU) API.

    This adapter fetches federal procurement (licitacao) data from the
    Brazilian transparency portal. The API requires an API key and enforces
    strict rate limiting.

    Because the licitacoes endpoint requires a ``codigoOrgao`` parameter,
    this adapter pre-loads the top federal organs via the ``/orgaos-siafi``
    endpoint, caches them for 24 hours, and iterates over each organ when
    fetching procurement records.

    Attributes:
        BASE_URL: API base URL
        DEFAULT_TIMEOUT: Request timeout in seconds
        MAX_RETRIES: Maximum number of retry attempts
        RATE_LIMIT_DELAY: Minimum delay between requests (seconds)
        ORG_CACHE_TTL: Time-to-live for organ list cache (seconds)
        MAX_ORGS: Maximum number of federal organs to query
        MAX_MONTH_SPAN: Maximum months per single API query

    Environment Variables:
        PORTAL_TRANSPARENCIA_API_KEY: API key for authentication (required)

    Example:
        >>> async with PortalTransparenciaAdapter() as adapter:
        ...     status = await adapter.health_check()
        ...     async for record in adapter.fetch("2026-01-01", "2026-01-31", {"DF"}):
        ...         print(record.objeto)
    """

    BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RATE_LIMIT_DELAY = 0.667  # 667ms between requests (~90 req/min)
    ORG_CACHE_TTL = 86400  # 24 hours in seconds
    MAX_ORGS = 50
    MAX_MONTH_SPAN = 1  # Max 1 month per query chunk

    # Source metadata (constant)
    _metadata = SourceMetadata(
        name="Portal da Transparencia - CGU",
        code="PORTAL_TRANSPARENCIA",
        base_url="https://api.portaldatransparencia.gov.br/api-de-dados",
        documentation_url="https://api.portaldatransparencia.gov.br/swagger-ui/index.html",
        capabilities={SourceCapability.PAGINATION, SourceCapability.DATE_RANGE},
        rate_limit_rps=1.5,  # 90/min
        typical_response_ms=2000,
        priority=3,
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize Portal da Transparencia adapter.

        Args:
            api_key: API key for authentication. If not provided, reads from
                     PORTAL_TRANSPARENCIA_API_KEY environment variable.
            timeout: Request timeout in seconds. Defaults to DEFAULT_TIMEOUT.

        Raises:
            SourceAuthError: If API key is required but not configured
                             (raised lazily on first fetch, not in __init__).
        """
        self._api_key = api_key or os.environ.get("PORTAL_TRANSPARENCIA_API_KEY", "")
        self._timeout = timeout or self.DEFAULT_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None
        self._last_request_time = 0.0
        self._request_count = 0

        # Organ cache: list of (codigo_siafi, nome_orgao) tuples
        self._org_cache: List[Tuple[str, str]] = []
        self._org_cache_ts: float = 0.0

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
                    "chave-api-dados": self._api_key,
                },
            )
        return self._client

    async def _rate_limit(self) -> None:
        """Enforce rate limiting between requests (90 req/min = 667ms gap)."""
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
    ) -> Any:
        """
        Make HTTP request with retry logic and rate limiting.

        Retries on 429 (rate limit) and 5xx (server errors).
        Skips retries on 4xx (except 429) -- these are client errors.

        Args:
            method: HTTP method
            path: API path (relative to BASE_URL)
            params: Query parameters

        Returns:
            Parsed JSON response (list or dict)

        Raises:
            SourceTimeoutError: On timeout after retries
            SourceRateLimitError: On 429 after retries
            SourceAuthError: On 401/403
            SourceAPIError: On other API errors
        """
        await self._rate_limit()
        client = await self._get_client()

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                logger.debug(
                    f"[PORTAL_TRANSPARENCIA] {method} {path} params={params} "
                    f"attempt={attempt + 1}/{self.MAX_RETRIES + 1}"
                )

                response = await client.request(method, path, params=params)

                # --- Rate limit (429) --- retry with Retry-After
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < self.MAX_RETRIES:
                        logger.warning(
                            f"[PORTAL_TRANSPARENCIA] Rate limited. "
                            f"Waiting {retry_after}s"
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    raise SourceRateLimitError(self.code, retry_after)

                # --- Auth errors (401/403) --- no retry
                if response.status_code in (401, 403):
                    raise SourceAuthError(
                        self.code,
                        f"Authentication failed (HTTP {response.status_code}). "
                        f"Check PORTAL_TRANSPARENCIA_API_KEY. "
                        f"Body: {response.text[:200]}"
                    )

                # --- Success (200) ---
                if response.status_code == 200:
                    return response.json()

                # --- No content (204) ---
                if response.status_code == 204:
                    return []

                # --- Server errors (5xx) --- retry with backoff
                if response.status_code >= 500:
                    if attempt < self.MAX_RETRIES:
                        delay = self._calculate_backoff(attempt)
                        logger.warning(
                            f"[PORTAL_TRANSPARENCIA] Server error "
                            f"{response.status_code}. Retrying in {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                        continue

                # --- Other 4xx --- skip (no retry)
                raise SourceAPIError(
                    self.code, response.status_code, response.text[:500]
                )

            except httpx.TimeoutException as e:
                if attempt < self.MAX_RETRIES:
                    delay = self._calculate_backoff(attempt)
                    logger.warning(
                        f"[PORTAL_TRANSPARENCIA] Timeout. Retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                    continue
                raise SourceTimeoutError(self.code, self._timeout) from e

            except httpx.RequestError as e:
                if attempt < self.MAX_RETRIES:
                    delay = self._calculate_backoff(attempt)
                    logger.warning(
                        f"[PORTAL_TRANSPARENCIA] Request error: {e}. "
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
    # Date helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _to_api_date(iso_date: str) -> str:
        """
        Convert YYYY-MM-DD to DD/MM/AAAA for the API.

        Args:
            iso_date: Date string in YYYY-MM-DD format

        Returns:
            Date string in DD/MM/YYYY format
        """
        parts = iso_date.split("-")
        if len(parts) != 3:
            raise ValueError(f"Invalid date format (expected YYYY-MM-DD): {iso_date}")
        return f"{parts[2]}/{parts[1]}/{parts[0]}"

    @staticmethod
    def _from_api_date(api_date: str) -> Optional[datetime]:
        """
        Convert DD/MM/AAAA (or DD/MM/AAAA HH:MM:SS) to datetime.

        Args:
            api_date: Date string from API response

        Returns:
            Parsed datetime or None if parsing fails
        """
        if not api_date or not isinstance(api_date, str):
            return None

        api_date = api_date.strip()

        formats = [
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(api_date, fmt)
            except ValueError:
                continue

        logger.debug(f"[PORTAL_TRANSPARENCIA] Failed to parse date: {api_date}")
        return None

    @staticmethod
    def _chunk_date_range(
        data_inicial: str,
        data_final: str,
    ) -> List[Tuple[str, str]]:
        """
        Split a date range into monthly chunks (max 1 month each).

        The API enforces a maximum period of 1 month per query. This method
        splits longer ranges into sub-ranges that each span at most one
        calendar month.

        Args:
            data_inicial: Start date in YYYY-MM-DD format
            data_final: End date in YYYY-MM-DD format

        Returns:
            List of (start_date, end_date) tuples, each in YYYY-MM-DD format,
            spanning at most one month.
        """
        start = datetime.strptime(data_inicial, "%Y-%m-%d")
        end = datetime.strptime(data_final, "%Y-%m-%d")

        if start > end:
            return []

        chunks: List[Tuple[str, str]] = []
        current_start = start

        while current_start <= end:
            # Calculate end of current month
            year = current_start.year
            month = current_start.month

            # Move to first day of next month
            if month == 12:
                next_month_start = datetime(year + 1, 1, 1)
            else:
                next_month_start = datetime(year, month + 1, 1)

            # End of this chunk is min(end_of_month, overall_end)
            from datetime import timedelta
            chunk_end = min(next_month_start - timedelta(days=1), end)

            chunks.append((
                current_start.strftime("%Y-%m-%d"),
                chunk_end.strftime("%Y-%m-%d"),
            ))

            current_start = next_month_start

        return chunks

    # ------------------------------------------------------------------ #
    # Organ pre-loading (AC5)
    # ------------------------------------------------------------------ #

    async def _load_orgs(self) -> List[Tuple[str, str]]:
        """
        Load top federal organs from /orgaos-siafi with 24h caching.

        Returns:
            List of (codigo_siafi, nome_orgao) tuples

        Raises:
            SourceAPIError: If the organ list cannot be fetched
        """
        now = time.monotonic()
        if self._org_cache and (now - self._org_cache_ts) < self.ORG_CACHE_TTL:
            logger.debug(
                f"[PORTAL_TRANSPARENCIA] Using cached org list "
                f"({len(self._org_cache)} orgs)"
            )
            return self._org_cache

        logger.info("[PORTAL_TRANSPARENCIA] Loading federal organ list from /orgaos-siafi")

        try:
            response = await self._request_with_retry(
                "GET",
                "/orgaos-siafi",
                params={"pagina": 1},
            )
        except Exception as e:
            logger.error(f"[PORTAL_TRANSPARENCIA] Failed to load org list: {e}")
            # If we have a stale cache, use it as fallback
            if self._org_cache:
                logger.warning(
                    "[PORTAL_TRANSPARENCIA] Using stale org cache as fallback"
                )
                return self._org_cache
            raise

        # Parse organ list -- response is a list of objects
        orgs: List[Tuple[str, str]] = []
        records = response if isinstance(response, list) else response.get("data", [])

        for item in records:
            codigo = str(
                item.get("codigo")
                or item.get("codigoSiafi")
                or item.get("codigoOrgao")
                or ""
            )
            nome = str(
                item.get("descricao")
                or item.get("nome")
                or item.get("nomeOrgao")
                or ""
            )
            if codigo:
                orgs.append((codigo, nome))

        # Take top N orgs (sorted by codigo for determinism)
        orgs.sort(key=lambda x: x[0])
        orgs = orgs[: self.MAX_ORGS]

        if not orgs:
            logger.warning("[PORTAL_TRANSPARENCIA] No organs found in API response")
            # Provide a minimal fallback list of major federal organs
            orgs = [
                ("26000", "Ministerio da Educacao"),
                ("36000", "Ministerio da Saude"),
                ("52000", "Ministerio da Defesa"),
                ("30000", "Ministerio da Justica"),
                ("39000", "Ministerio da Fazenda"),
                ("25000", "Ministerio da Fazenda"),
                ("20000", "Presidencia da Republica"),
                ("44000", "Ministerio do Meio Ambiente"),
                ("54000", "Ministerio do Turismo"),
                ("53000", "Ministerio do Desenvolvimento"),
            ]

        self._org_cache = orgs
        self._org_cache_ts = now

        logger.info(
            f"[PORTAL_TRANSPARENCIA] Loaded {len(orgs)} federal organs "
            f"(cached for {self.ORG_CACHE_TTL}s)"
        )
        return orgs

    # ------------------------------------------------------------------ #
    # SourceAdapter interface implementation
    # ------------------------------------------------------------------ #

    async def health_check(self) -> SourceStatus:
        """
        Check if Portal da Transparencia API is available.

        Performs a lightweight query to a well-known organ (26000 = MEC)
        to verify connectivity and authentication.

        Returns:
            SourceStatus.AVAILABLE if API responds successfully
            SourceStatus.DEGRADED if API responds but slowly
            SourceStatus.UNAVAILABLE if API fails to respond
        """
        if not self._api_key:
            logger.warning(
                "[PORTAL_TRANSPARENCIA] No API key configured "
                "(set PORTAL_TRANSPARENCIA_API_KEY)"
            )
            return SourceStatus.UNAVAILABLE

        try:
            client = await self._get_client()
            start = asyncio.get_event_loop().time()

            response = await client.get(
                "/licitacoes",
                params={"codigoOrgao": "26000", "pagina": 1},
                timeout=5.0,
            )

            elapsed_ms = (asyncio.get_event_loop().time() - start) * 1000

            if response.status_code in (401, 403):
                logger.warning(
                    "[PORTAL_TRANSPARENCIA] Authentication failed in health check"
                )
                return SourceStatus.UNAVAILABLE

            if response.status_code == 200:
                if elapsed_ms > 4000:
                    logger.info(
                        f"[PORTAL_TRANSPARENCIA] Health check slow: "
                        f"{elapsed_ms:.0f}ms"
                    )
                    return SourceStatus.DEGRADED
                return SourceStatus.AVAILABLE

            logger.warning(
                f"[PORTAL_TRANSPARENCIA] Health check returned "
                f"{response.status_code}"
            )
            return SourceStatus.DEGRADED

        except (httpx.TimeoutException, httpx.RequestError) as e:
            logger.warning(f"[PORTAL_TRANSPARENCIA] Health check failed: {e}")
            return SourceStatus.UNAVAILABLE
        except Exception as e:
            logger.error(
                f"[PORTAL_TRANSPARENCIA] Unexpected health check error: {e}"
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
        Fetch procurement records from Portal da Transparencia.

        This method:
        1. Validates the API key
        2. Pre-loads the list of federal organs (cached 24h)
        3. Chunks the date range into monthly sub-ranges
        4. For each organ + date chunk, paginates through all results
        5. Normalizes records and applies client-side UF filtering

        Args:
            data_inicial: Start date in YYYY-MM-DD format
            data_final: End date in YYYY-MM-DD format
            ufs: Optional set of Brazilian state codes to filter (client-side)
            **kwargs: Additional parameters (unused)

        Yields:
            UnifiedProcurement records

        Raises:
            SourceAuthError: If API key is invalid or missing
            SourceTimeoutError: If requests timeout
            SourceAPIError: On other API errors
        """
        if not self._api_key:
            logger.warning(
                "[PORTAL_TRANSPARENCIA] No API key configured -- skipping fetch. "
                "Set PORTAL_TRANSPARENCIA_API_KEY environment variable."
            )
            return

        # Pre-load federal organs
        orgs = await self._load_orgs()

        # Chunk date range into monthly sub-ranges
        date_chunks = self._chunk_date_range(data_inicial, data_final)
        if not date_chunks:
            logger.warning(
                f"[PORTAL_TRANSPARENCIA] Invalid date range: "
                f"{data_inicial} to {data_final}"
            )
            return

        total_fetched = 0
        total_skipped_uf = 0
        seen_ids: Set[str] = set()

        logger.info(
            f"[PORTAL_TRANSPARENCIA] Starting fetch: {len(orgs)} orgs x "
            f"{len(date_chunks)} date chunks, UF filter={ufs or 'all'}"
        )

        for org_idx, (org_code, org_name) in enumerate(orgs):
            for chunk_start, chunk_end in date_chunks:
                api_start = self._to_api_date(chunk_start)
                api_end = self._to_api_date(chunk_end)

                pagina = 1
                empty_pages = 0

                while True:
                    params: Dict[str, Any] = {
                        "codigoOrgao": org_code,
                        "dataInicial": api_start,
                        "dataFinal": api_end,
                        "pagina": pagina,
                    }

                    try:
                        response = await self._request_with_retry(
                            "GET", "/licitacoes", params
                        )
                    except SourceAuthError:
                        raise
                    except SourceAPIError as e:
                        # On 4xx (except 429, already handled), skip this org/chunk
                        if 400 <= e.status_code < 500:
                            logger.debug(
                                f"[PORTAL_TRANSPARENCIA] Skipping org {org_code} "
                                f"chunk {chunk_start}-{chunk_end}: {e}"
                            )
                            break
                        # On other errors, log and continue if partial results
                        logger.error(
                            f"[PORTAL_TRANSPARENCIA] Error org={org_code} "
                            f"page={pagina}: {e}"
                        )
                        if total_fetched > 0:
                            break
                        raise
                    except Exception as e:
                        logger.error(
                            f"[PORTAL_TRANSPARENCIA] Error org={org_code} "
                            f"page={pagina}: {e}"
                        )
                        if total_fetched > 0:
                            break
                        raise

                    # Response is a list of records (or empty list)
                    records = (
                        response
                        if isinstance(response, list)
                        else response.get("data", [])
                    )

                    if not records:
                        empty_pages += 1
                        break

                    for raw_record in records:
                        try:
                            record = self.normalize(raw_record)

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

                        except Exception as e:
                            logger.warning(
                                f"[PORTAL_TRANSPARENCIA] Failed to normalize "
                                f"record: {e}"
                            )
                            continue

                    # If we got fewer records than expected, assume last page
                    # The API returns an empty array when there are no more pages
                    if len(records) == 0:
                        break

                    pagina += 1

                    # Safety limit to prevent infinite loops
                    if pagina > 200:
                        logger.warning(
                            f"[PORTAL_TRANSPARENCIA] Reached page limit (200) "
                            f"for org {org_code}"
                        )
                        break

            # Progress logging every 10 orgs
            if (org_idx + 1) % 10 == 0:
                logger.info(
                    f"[PORTAL_TRANSPARENCIA] Progress: {org_idx + 1}/{len(orgs)} "
                    f"orgs processed, {total_fetched} records so far"
                )

        logger.info(
            f"[PORTAL_TRANSPARENCIA] Fetch complete: {total_fetched} records "
            f"from {len(orgs)} orgs, {total_skipped_uf} skipped by UF filter"
        )

    def normalize(self, raw_record: Dict[str, Any]) -> UnifiedProcurement:
        """
        Convert Portal da Transparencia record to UnifiedProcurement.

        Field Mapping (based on API documentation):
            id / codigoLicitacao -> source_id
            objeto / descricao -> objeto
            valorLicitacao -> valor_estimado
            orgaoVinculado.nome / orgao.nome -> orgao
            orgaoVinculado.cnpj -> cnpj_orgao
            uf -> uf (from municipio or orgao fields)
            municipio -> municipio
            dataPublicacao -> data_publicacao (DD/MM/AAAA)
            dataAbertura -> data_abertura (DD/MM/AAAA)
            dataResultado -> data_encerramento (DD/MM/AAAA)
            modalidadeLicitacao -> modalidade
            situacao / situacaoLicitacao -> situacao
            numero -> numero_edital

        Args:
            raw_record: Raw record from API response

        Returns:
            Normalized UnifiedProcurement record

        Raises:
            SourceParseError: If critical fields cannot be parsed
        """
        try:
            # --- Source ID ---
            source_id = str(
                raw_record.get("id")
                or raw_record.get("codigoLicitacao")
                or raw_record.get("codigo")
                or ""
            )
            if not source_id:
                raise SourceParseError(self.code, "source_id", raw_record)

            # --- Object description ---
            objeto = (
                raw_record.get("objeto")
                or raw_record.get("descricao")
                or raw_record.get("informacaoGeral")
                or ""
            )

            # --- Value ---
            valor = (
                raw_record.get("valorLicitacao")
                or raw_record.get("valor")
                or raw_record.get("valorEstimado")
                or 0
            )
            if isinstance(valor, str):
                valor = valor.replace(".", "").replace(",", ".")
                try:
                    valor = float(valor)
                except ValueError:
                    valor = 0.0

            # --- Organ info ---
            orgao_data = raw_record.get("orgaoVinculado") or raw_record.get("orgao") or {}
            if isinstance(orgao_data, str):
                orgao_nome = orgao_data
                orgao_cnpj = ""
            elif isinstance(orgao_data, dict):
                orgao_nome = (
                    orgao_data.get("nome")
                    or orgao_data.get("descricao")
                    or orgao_data.get("nomeOrgao")
                    or ""
                )
                orgao_cnpj = (
                    orgao_data.get("cnpj")
                    or orgao_data.get("codigoCNPJ")
                    or ""
                )
            else:
                orgao_nome = ""
                orgao_cnpj = ""

            # Fallback for orgao name from top-level fields
            if not orgao_nome:
                orgao_nome = (
                    raw_record.get("nomeOrgao")
                    or raw_record.get("orgaoNome")
                    or ""
                )

            # --- Location ---
            # Try nested municipio object first, then flat fields
            municipio_data = raw_record.get("municipio") or {}
            if isinstance(municipio_data, dict):
                municipio = municipio_data.get("nomeIBGE") or municipio_data.get("nome") or ""
                uf = (
                    municipio_data.get("uf")
                    or municipio_data.get("codigoUF")
                    or ""
                )
                # If uf is nested further
                if isinstance(uf, dict):
                    uf = uf.get("sigla") or uf.get("codigo") or ""
            elif isinstance(municipio_data, str):
                municipio = municipio_data
                uf = ""
            else:
                municipio = ""
                uf = ""

            # Fallback to top-level UF
            if not uf:
                uf = raw_record.get("uf") or raw_record.get("siglaUf") or ""

            # --- Dates (DD/MM/AAAA -> datetime) ---
            data_publicacao = self._from_api_date(
                raw_record.get("dataPublicacao")
                or raw_record.get("dataResultadoCompra")
            )
            data_abertura = self._from_api_date(
                raw_record.get("dataAbertura")
                or raw_record.get("dataAberturaProposta")
            )
            data_encerramento = self._from_api_date(
                raw_record.get("dataResultado")
                or raw_record.get("dataEncerramento")
            )

            # --- Edital number and year ---
            numero_edital = str(
                raw_record.get("numero")
                or raw_record.get("numeroLicitacao")
                or raw_record.get("numeroEdital")
                or ""
            )
            ano = str(
                raw_record.get("ano")
                or raw_record.get("anoLicitacao")
                or ""
            )
            if not ano and data_publicacao:
                ano = str(data_publicacao.year)

            # --- Modalidade ---
            modalidade_raw = raw_record.get("modalidadeLicitacao") or {}
            if isinstance(modalidade_raw, dict):
                modalidade = (
                    modalidade_raw.get("descricao")
                    or modalidade_raw.get("nome")
                    or ""
                )
            elif isinstance(modalidade_raw, str):
                modalidade = modalidade_raw
            else:
                modalidade = raw_record.get("modalidade") or ""

            # --- Situacao ---
            situacao_raw = raw_record.get("situacaoLicitacao") or raw_record.get("situacao") or {}
            if isinstance(situacao_raw, dict):
                situacao = (
                    situacao_raw.get("descricao")
                    or situacao_raw.get("nome")
                    or ""
                )
            elif isinstance(situacao_raw, str):
                situacao = situacao_raw
            else:
                situacao = ""

            # --- Links ---
            link_portal = (
                raw_record.get("linkPortal")
                or raw_record.get("linkDetalhamento")
                or ""
            )
            if not link_portal and source_id:
                link_portal = (
                    f"https://portaldatransparencia.gov.br/licitacoes/"
                    f"{source_id}"
                )

            link_edital = (
                raw_record.get("linkEdital")
                or raw_record.get("linkDocumentos")
                or link_portal
            )

            return UnifiedProcurement(
                source_id=source_id,
                source_name=self.code,
                objeto=objeto,
                valor_estimado=float(valor),
                orgao=orgao_nome,
                cnpj_orgao=orgao_cnpj,
                uf=uf,
                municipio=municipio,
                data_publicacao=data_publicacao,
                data_abertura=data_abertura,
                data_encerramento=data_encerramento,
                numero_edital=numero_edital,
                ano=ano,
                modalidade=modalidade,
                situacao=situacao,
                esfera="F",  # Federal (Portal da Transparencia is federal-only)
                link_edital=link_edital,
                link_portal=link_portal,
                fetched_at=datetime.now(timezone.utc),
                raw_data=raw_record,
            )

        except SourceParseError:
            raise
        except Exception as e:
            logger.error(f"[PORTAL_TRANSPARENCIA] Normalization error: {e}")
            raise SourceParseError(self.code, "record", str(e)) from e

    # ------------------------------------------------------------------ #
    # Resource management
    # ------------------------------------------------------------------ #

    async def close(self) -> None:
        """Close HTTP client and release resources."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            logger.debug(
                f"[PORTAL_TRANSPARENCIA] Client closed. "
                f"Total requests: {self._request_count}"
            )
        self._client = None

    async def __aenter__(self) -> "PortalTransparenciaAdapter":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
