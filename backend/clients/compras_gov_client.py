"""ComprasGov API client adapter (v3 - Dados Abertos Federal).

This module implements the SourceAdapter interface for the ComprasGov
v3 open data API (https://dadosabertos.compras.gov.br/).

API Characteristics (v3):
- REST API with JSON responses
- No authentication required (open government data)
- Federal procurement data
- Dual-endpoint fetch: Legacy (pre-2024) + Lei 14.133 (new procurements)
- Rate limit: 5 req/s (200ms between requests)

Migration history:
- v1: compras.dados.gov.br — permanently unstable, disabled in GTM-FIX-025
- v3: dadosabertos.compras.gov.br — new stable API (GTM-FIX-027 T5)

Documentation: https://dadosabertos.compras.gov.br/
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


class ComprasGovAdapter(SourceAdapter):
    """Adapter for ComprasGov v3 Federal Open Data API.

    This adapter fetches procurement data from the Brazilian federal
    government's open data portal (v3). No authentication is required.

    Dual-endpoint strategy:
    - Legacy endpoint: /modulo-legado/1_consultarLicitacao
      For pre-2024 procurements. Supports server-side UF filtering.
    - Lei 14.133 endpoint: /modulo-contratacoes/1_consultarContratacoes_PNCP_14133
      For new procurements. UF filtering is client-side only.

    Both endpoints are queried in parallel and results are merged with
    deduplication.

    Attributes:
        BASE_URL: v3 API base URL
        DEFAULT_TIMEOUT: Request timeout in seconds
        MAX_RETRIES: Maximum number of retry attempts
        RATE_LIMIT_DELAY: Minimum delay between requests (seconds)
    """

    BASE_URL = "https://dadosabertos.compras.gov.br"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RATE_LIMIT_DELAY = 0.2  # 200ms between requests (5 req/s)
    DEFAULT_PAGE_SIZE = 500

    # Legacy endpoint paths
    LEGACY_ENDPOINT = "/modulo-legado/1_consultarLicitacao"
    LEI_14133_ENDPOINT = "/modulo-contratacoes/1_consultarContratacoes_PNCP_14133"

    _metadata = SourceMetadata(
        name="ComprasGov - Dados Abertos Federal",
        code="COMPRAS_GOV",
        base_url="https://dadosabertos.compras.gov.br",
        documentation_url="https://dadosabertos.compras.gov.br/",
        capabilities={
            SourceCapability.PAGINATION,
            SourceCapability.DATE_RANGE,
            SourceCapability.FILTER_BY_UF,  # Legacy endpoint supports server-side UF
        },
        rate_limit_rps=5.0,
        typical_response_ms=3000,
        priority=3,
    )

    def __init__(self, timeout: Optional[int] = None):
        """Initialize ComprasGov v3 adapter.

        Args:
            timeout: Request timeout in seconds. Defaults to DEFAULT_TIMEOUT.
        """
        self._timeout = timeout or self.DEFAULT_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None
        self._last_request_time = 0.0
        self._request_count = 0
        self.was_truncated: bool = False

    @property
    def metadata(self) -> SourceMetadata:
        """Return source metadata."""
        return self._metadata

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
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
        """Enforce rate limiting between requests."""
        now = asyncio.get_running_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = asyncio.get_running_loop().time()
        self._request_count += 1

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic and rate limiting.

        Args:
            method: HTTP method
            path: API path
            params: Query parameters

        Returns:
            Parsed JSON response

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
                    f"[COMPRAS_GOV] {method} {path} params={params} "
                    f"attempt={attempt + 1}/{self.MAX_RETRIES + 1}"
                )

                response = await client.request(method, path, params=params)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < self.MAX_RETRIES:
                        logger.warning(f"[COMPRAS_GOV] Rate limited. Waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue
                    raise SourceRateLimitError(self.code, retry_after)

                if response.status_code == 200:
                    return response.json()

                if response.status_code == 204:
                    return {"data": [], "totalRegistros": 0, "totalPaginas": 0, "paginasRestantes": 0}

                if response.status_code >= 500:
                    if attempt < self.MAX_RETRIES:
                        delay = self._calculate_backoff(attempt)
                        logger.warning(
                            f"[COMPRAS_GOV] Server error {response.status_code}. "
                            f"Retrying in {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                        continue

                raise SourceAPIError(self.code, response.status_code, response.text[:500])

            except httpx.TimeoutException as e:
                if attempt < self.MAX_RETRIES:
                    delay = self._calculate_backoff(attempt)
                    logger.warning(f"[COMPRAS_GOV] Timeout. Retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                    continue
                raise SourceTimeoutError(self.code, self._timeout) from e

            except httpx.RequestError as e:
                if attempt < self.MAX_RETRIES:
                    delay = self._calculate_backoff(attempt)
                    logger.warning(f"[COMPRAS_GOV] Request error: {e}. Retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                    continue
                raise SourceAPIError(self.code, 0, str(e)) from e

        raise SourceAPIError(self.code, 0, "Exhausted retries")

    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter."""
        delay = min(2.0 * (2 ** attempt), 60.0)
        delay *= random.uniform(0.5, 1.5)
        return delay

    async def health_check(self) -> SourceStatus:
        """Check if ComprasGov v3 API is available.

        Uses a minimal query to the legacy endpoint as health probe.

        Returns:
            SourceStatus indicating current health
        """
        try:
            client = await self._get_client()
            start = asyncio.get_running_loop().time()

            response = await client.get(
                self.LEGACY_ENDPOINT,
                params={"pagina": 1, "tamanhoPagina": 1},
                timeout=5.0,
            )

            elapsed_ms = (asyncio.get_running_loop().time() - start) * 1000

            if response.status_code == 200:
                if elapsed_ms > 4000:
                    logger.info(f"[COMPRAS_GOV] Health check slow: {elapsed_ms:.0f}ms")
                    return SourceStatus.DEGRADED
                return SourceStatus.AVAILABLE

            logger.warning(f"[COMPRAS_GOV] Health check returned {response.status_code}")
            return SourceStatus.DEGRADED

        except (httpx.TimeoutException, httpx.RequestError) as e:
            logger.warning(f"[COMPRAS_GOV] Health check failed: {e}")
            return SourceStatus.UNAVAILABLE
        except Exception as e:
            logger.error(f"[COMPRAS_GOV] Unexpected health check error: {e}")
            return SourceStatus.UNAVAILABLE

    async def fetch(
        self,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[UnifiedProcurement, None]:
        """Fetch procurement records from ComprasGov v3 (dual-endpoint).

        Queries both legacy and Lei 14.133 endpoints in parallel and
        merges results with deduplication.

        Args:
            data_inicial: Start date in YYYY-MM-DD format
            data_final: End date in YYYY-MM-DD format
            ufs: Optional set of Brazilian state codes to filter
            **kwargs: Additional parameters (max_pages supported)

        Yields:
            UnifiedProcurement records
        """
        max_pages = kwargs.get("max_pages", 50)
        seen_ids: Set[str] = set()
        total_fetched = 0

        # Run both endpoints in parallel
        legacy_records: List[UnifiedProcurement] = []
        lei_records: List[UnifiedProcurement] = []

        legacy_task = asyncio.create_task(
            self._fetch_legacy(data_inicial, data_final, ufs, max_pages)
        )
        lei_task = asyncio.create_task(
            self._fetch_lei_14133(data_inicial, data_final, ufs, max_pages)
        )

        # Gather results — tolerate individual endpoint failures
        results = await asyncio.gather(legacy_task, lei_task, return_exceptions=True)

        if isinstance(results[0], list):
            legacy_records = results[0]
        else:
            logger.warning(f"[COMPRAS_GOV] Legacy endpoint failed: {results[0]}")

        if isinstance(results[1], list):
            lei_records = results[1]
        else:
            logger.warning(f"[COMPRAS_GOV] Lei 14.133 endpoint failed: {results[1]}")

        if not legacy_records and not lei_records:
            # Both endpoints failed — re-raise the first exception if available
            for result in results:
                if isinstance(result, Exception):
                    raise result
            return

        # Merge and deduplicate: yield legacy first, then lei 14.133
        for record in legacy_records:
            if record.source_id not in seen_ids:
                seen_ids.add(record.source_id)
                total_fetched += 1
                yield record

        for record in lei_records:
            if record.source_id not in seen_ids:
                seen_ids.add(record.source_id)
                total_fetched += 1
                yield record

        logger.info(
            f"[COMPRAS_GOV] Fetch complete: {total_fetched} records "
            f"(legacy={len(legacy_records)}, lei14133={len(lei_records)}, "
            f"truncated={self.was_truncated})"
        )

    async def _fetch_legacy(
        self,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]] = None,
        max_pages: int = 50,
    ) -> List[UnifiedProcurement]:
        """Fetch from legacy endpoint (pre-2024 procurements).

        The legacy endpoint supports server-side UF filtering via the
        `uf` parameter, so we make one request per UF when UFs are provided.

        Args:
            data_inicial: Start date YYYY-MM-DD
            data_final: End date YYYY-MM-DD
            ufs: Optional set of UF codes
            max_pages: Maximum pages to fetch per UF

        Returns:
            List of UnifiedProcurement records
        """
        records: List[UnifiedProcurement] = []

        if ufs:
            # Server-side UF filtering: one set of paginated requests per UF
            for uf in sorted(ufs):
                uf_records = await self._fetch_legacy_paginated(
                    data_inicial, data_final, uf=uf, max_pages=max_pages
                )
                records.extend(uf_records)
        else:
            # No UF filter: fetch all
            records = await self._fetch_legacy_paginated(
                data_inicial, data_final, uf=None, max_pages=max_pages
            )

        return records

    async def _fetch_legacy_paginated(
        self,
        data_inicial: str,
        data_final: str,
        uf: Optional[str] = None,
        max_pages: int = 50,
    ) -> List[UnifiedProcurement]:
        """Paginated fetch from legacy endpoint.

        Args:
            data_inicial: Start date YYYY-MM-DD
            data_final: End date YYYY-MM-DD
            uf: Optional single UF code for server-side filtering
            max_pages: Maximum pages to fetch

        Returns:
            List of UnifiedProcurement records
        """
        records: List[UnifiedProcurement] = []
        pagina = 1

        while pagina <= max_pages:
            params: Dict[str, Any] = {
                "dataInicial": data_inicial,
                "dataFinal": data_final,
                "pagina": pagina,
                "tamanhoPagina": self.DEFAULT_PAGE_SIZE,
            }

            if uf:
                params["uf"] = uf

            try:
                response = await self._request_with_retry(
                    "GET", self.LEGACY_ENDPOINT, params
                )
            except Exception as e:
                logger.error(
                    f"[COMPRAS_GOV] Legacy endpoint error at page {pagina}: {e}"
                )
                if records:
                    logger.warning(
                        f"[COMPRAS_GOV] Returning {len(records)} partial legacy results"
                    )
                    return records
                raise

            data = response.get("data", [])
            total_registros = response.get("totalRegistros", 0)
            total_paginas = response.get("totalPaginas", 0)
            paginas_restantes = response.get("paginasRestantes", 0)

            if pagina == 1 and total_registros > 0:
                logger.info(
                    f"[COMPRAS_GOV] Legacy{' (' + uf + ')' if uf else ''}: "
                    f"{total_registros} records across {total_paginas} pages"
                )

            if not data:
                break

            for raw_record in data:
                try:
                    record = self._normalize_legacy(raw_record)
                    records.append(record)
                except Exception as e:
                    logger.warning(f"[COMPRAS_GOV] Failed to normalize legacy record: {e}")
                    continue

            if paginas_restantes <= 0:
                break

            if pagina >= max_pages:
                self.was_truncated = True
                logger.warning(
                    f"[COMPRAS_GOV] Legacy: reached max_pages ({max_pages}). "
                    f"Results may be incomplete."
                )
                break

            pagina += 1

        return records

    async def _fetch_lei_14133(
        self,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]] = None,
        max_pages: int = 50,
    ) -> List[UnifiedProcurement]:
        """Fetch from Lei 14.133 endpoint (new procurements).

        This endpoint does NOT support server-side UF filtering.
        UF filtering is done client-side.

        Args:
            data_inicial: Start date YYYY-MM-DD
            data_final: End date YYYY-MM-DD
            ufs: Optional set of UF codes for client-side filtering
            max_pages: Maximum pages to fetch

        Returns:
            List of UnifiedProcurement records
        """
        records: List[UnifiedProcurement] = []
        pagina = 1

        while pagina <= max_pages:
            params: Dict[str, Any] = {
                "dataInicial": data_inicial,
                "dataFinal": data_final,
                "pagina": pagina,
                "tamanhoPagina": self.DEFAULT_PAGE_SIZE,
            }

            try:
                response = await self._request_with_retry(
                    "GET", self.LEI_14133_ENDPOINT, params
                )
            except Exception as e:
                logger.error(
                    f"[COMPRAS_GOV] Lei 14.133 endpoint error at page {pagina}: {e}"
                )
                if records:
                    logger.warning(
                        f"[COMPRAS_GOV] Returning {len(records)} partial Lei 14.133 results"
                    )
                    return records
                raise

            data = response.get("data", [])
            total_registros = response.get("totalRegistros", 0)
            total_paginas = response.get("totalPaginas", 0)
            paginas_restantes = response.get("paginasRestantes", 0)

            if pagina == 1 and total_registros > 0:
                logger.info(
                    f"[COMPRAS_GOV] Lei 14.133: "
                    f"{total_registros} records across {total_paginas} pages"
                )

            if not data:
                break

            for raw_record in data:
                try:
                    record = self._normalize_lei_14133(raw_record)

                    # Client-side UF filtering for Lei 14.133
                    if ufs and record.uf and record.uf not in ufs:
                        continue

                    records.append(record)
                except Exception as e:
                    logger.warning(
                        f"[COMPRAS_GOV] Failed to normalize Lei 14.133 record: {e}"
                    )
                    continue

            if paginas_restantes <= 0:
                break

            if pagina >= max_pages:
                self.was_truncated = True
                logger.warning(
                    f"[COMPRAS_GOV] Lei 14.133: reached max_pages ({max_pages}). "
                    f"Results may be incomplete."
                )
                break

            pagina += 1

        return records

    def normalize(self, raw_record: Dict[str, Any]) -> UnifiedProcurement:
        """Convert a ComprasGov record to UnifiedProcurement.

        Auto-detects whether the record is from legacy or Lei 14.133 endpoint
        based on field presence and delegates accordingly.

        Args:
            raw_record: Raw record from API response

        Returns:
            Normalized UnifiedProcurement record
        """
        # Detect endpoint type by field presence
        if "numeroControlePNCP" in raw_record or "objetoCompra" in raw_record:
            return self._normalize_lei_14133(raw_record)
        return self._normalize_legacy(raw_record)

    def _normalize_legacy(self, raw_record: Dict[str, Any]) -> UnifiedProcurement:
        """Normalize a legacy endpoint record.

        Legacy field mapping:
        - numero_aviso -> source_id (prefixed with cg_leg_)
        - objeto -> objeto
        - uasg.nome -> orgao
        - uf -> uf
        - modalidade.descricao -> modalidade
        - situacao.descricao -> situacao
        - data_publicacao -> data_publicacao
        - data_entrega_proposta -> data_abertura

        Args:
            raw_record: Raw record from legacy endpoint

        Returns:
            UnifiedProcurement record
        """
        try:
            # Source ID
            source_id = str(
                raw_record.get("numero_aviso")
                or raw_record.get("identificador")
                or raw_record.get("id")
                or ""
            )
            if not source_id:
                raise SourceParseError(self.code, "source_id", raw_record)

            source_id = f"cg_leg_{source_id}"

            # Object description
            objeto = raw_record.get("objeto") or raw_record.get("descricao") or ""

            # Value
            valor = raw_record.get("valor_estimado") or raw_record.get("valor") or 0
            if isinstance(valor, str):
                try:
                    valor = float(valor.replace(".", "").replace(",", "."))
                except ValueError:
                    valor = 0.0

            # UASG / Orgao
            uasg = raw_record.get("uasg") or {}
            if isinstance(uasg, dict):
                orgao = uasg.get("nome") or raw_record.get("orgao_nome") or ""
                cnpj = uasg.get("cnpj") or raw_record.get("cnpj") or ""
            else:
                orgao = raw_record.get("orgao_nome") or ""
                cnpj = raw_record.get("cnpj") or ""

            # Location
            uf = raw_record.get("uf") or ""
            municipio = raw_record.get("municipio") or ""

            # Modalidade
            modalidade_obj = raw_record.get("modalidade") or {}
            if isinstance(modalidade_obj, dict):
                modalidade = modalidade_obj.get("descricao") or ""
            else:
                modalidade = str(modalidade_obj) if modalidade_obj else ""

            # Situacao
            situacao_obj = raw_record.get("situacao") or {}
            if isinstance(situacao_obj, dict):
                situacao = situacao_obj.get("descricao") or ""
            else:
                situacao = str(situacao_obj) if situacao_obj else ""

            # Dates
            data_publicacao = self._parse_datetime(raw_record.get("data_publicacao"))
            data_abertura = self._parse_datetime(raw_record.get("data_entrega_proposta"))

            # Edital info
            numero_edital = str(raw_record.get("numero_aviso") or "")
            ano = str(raw_record.get("ano") or "")
            if not ano and data_publicacao:
                ano = str(data_publicacao.year)

            # Link
            link = raw_record.get("link") or ""
            if not link and source_id:
                link = f"{self.BASE_URL}/modulo-legado/licitacao/{source_id}"

            return UnifiedProcurement(
                source_id=source_id,
                source_name=self.code,
                objeto=objeto,
                valor_estimado=float(valor),
                orgao=orgao,
                cnpj_orgao=cnpj,
                uf=uf,
                municipio=municipio,
                data_publicacao=data_publicacao,
                data_abertura=data_abertura,
                numero_edital=numero_edital,
                ano=ano,
                modalidade=modalidade,
                situacao=situacao,
                esfera="F",  # Federal
                link_edital=link,
                link_portal=link,
                fetched_at=datetime.now(timezone.utc),
                raw_data=raw_record,
            )

        except SourceParseError:
            raise
        except Exception as e:
            logger.error(f"[COMPRAS_GOV] Legacy normalization error: {e}")
            raise SourceParseError(self.code, "legacy_record", str(e)) from e

    def _normalize_lei_14133(self, raw_record: Dict[str, Any]) -> UnifiedProcurement:
        """Normalize a Lei 14.133 endpoint record.

        Lei 14.133 field mapping:
        - numeroControlePNCP -> source_id (prefixed with cg_14133_)
        - objetoCompra -> objeto
        - orgaoEntidade.razaoSocial -> orgao
        - uf -> uf
        - modalidadeNome -> modalidade
        - situacaoCompraNome -> situacao
        - dataPublicacaoPncp -> data_publicacao
        - dataEncerramentoProposta -> data_encerramento

        Args:
            raw_record: Raw record from Lei 14.133 endpoint

        Returns:
            UnifiedProcurement record
        """
        try:
            # Source ID
            source_id = str(
                raw_record.get("numeroControlePNCP")
                or raw_record.get("id")
                or ""
            )
            if not source_id:
                raise SourceParseError(self.code, "source_id", raw_record)

            source_id = f"cg_14133_{source_id}"

            # Object description
            objeto = raw_record.get("objetoCompra") or ""

            # Value
            valor = raw_record.get("valorTotalEstimado") or raw_record.get("valorEstimado") or 0
            if isinstance(valor, str):
                try:
                    valor = float(valor)
                except ValueError:
                    valor = 0.0

            # Orgao / Entity
            orgao_obj = raw_record.get("orgaoEntidade") or {}
            if isinstance(orgao_obj, dict):
                orgao = orgao_obj.get("razaoSocial") or ""
                cnpj = orgao_obj.get("cnpj") or ""
                municipio = orgao_obj.get("municipio") or ""
            else:
                orgao = str(orgao_obj) if orgao_obj else ""
                cnpj = ""
                municipio = ""

            # Location
            uf = raw_record.get("uf") or ""

            # Modalidade
            modalidade = raw_record.get("modalidadeNome") or ""

            # Situacao
            situacao = raw_record.get("situacaoCompraNome") or ""

            # Dates
            data_publicacao = self._parse_datetime(raw_record.get("dataPublicacaoPncp"))
            data_encerramento = self._parse_datetime(raw_record.get("dataEncerramentoProposta"))
            data_abertura = self._parse_datetime(raw_record.get("dataAberturaProposta"))

            # Edital info
            numero_edital = str(raw_record.get("numeroCompra") or raw_record.get("numero") or "")
            ano = str(raw_record.get("anoCompra") or "")
            if not ano and data_publicacao:
                ano = str(data_publicacao.year)

            # Link
            link = raw_record.get("link") or ""
            if not link and raw_record.get("numeroControlePNCP"):
                link = f"https://pncp.gov.br/app/editais/{raw_record['numeroControlePNCP']}"

            return UnifiedProcurement(
                source_id=source_id,
                source_name=self.code,
                objeto=objeto,
                valor_estimado=float(valor),
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
                esfera="F",  # Federal
                link_edital=link,
                link_portal=link,
                fetched_at=datetime.now(timezone.utc),
                raw_data=raw_record,
            )

        except SourceParseError:
            raise
        except Exception as e:
            logger.error(f"[COMPRAS_GOV] Lei 14.133 normalization error: {e}")
            raise SourceParseError(self.code, "lei_14133_record", str(e)) from e

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime from various formats."""
        if not value:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value / 1000)
            except (ValueError, OSError):
                return None

        if isinstance(value, str):
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
            value = value.replace("+00:00", "Z").replace("+0000", "Z")
            for fmt in formats:
                try:
                    return datetime.strptime(value.rstrip("Z"), fmt.rstrip("Z"))
                except ValueError:
                    continue
            logger.debug(f"[COMPRAS_GOV] Failed to parse datetime: {value}")

        return None

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            logger.debug(f"[COMPRAS_GOV] Client closed. Total requests: {self._request_count}")
        self._client = None

    async def __aenter__(self) -> "ComprasGovAdapter":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
