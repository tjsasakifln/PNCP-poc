"""Portal de Compras Publicas API client adapter (v2 Public API).

This module implements the SourceAdapter interface for the Portal de Compras
Publicas v2 public API (https://compras.api.portaldecompraspublicas.com.br/).

API Characteristics (v2):
- REST API with JSON responses
- No authentication required (fully public)
- Date format: YYYY-MM-DD (ISO)
- Pagination: fixed 10 per page, use `pagina` param
- UF filtering: client-side only (API returns all UFs)
- Value: NOT included in listing endpoint

GTM-FIX-011: Original PCP integration.
GTM-FIX-012b: Migrated to v2 public API after old endpoint removal.
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


def calculate_total_value(lotes: List[Dict[str, Any]]) -> float:
    """Calculate total estimated value from PCP lots/items structure.

    PCP returns value per-item as VL_UNITARIO_ESTIMADO * QT_ITENS.
    This function sums across all items in all lots.

    AC8: Edge cases:
    - NULL values → skip with warning
    - QT_ITENS <= 0 → skip
    - Empty lotes → 0.0
    - Result rounded to 2 decimal places

    Args:
        lotes: List of lot dicts, each containing 'itens' list.

    Returns:
        Total estimated value rounded to 2 decimal places.
    """
    if not lotes:
        return 0.0

    total = 0.0
    for lote in lotes:
        itens = lote.get("itens") or []
        for item in itens:
            vl_unitario = item.get("VL_UNITARIO_ESTIMADO")
            qt_itens = item.get("QT_ITENS")

            if vl_unitario is None or qt_itens is None:
                logger.debug(
                    "[PCP] Skipping item with NULL value/qty: "
                    f"vl={vl_unitario}, qt={qt_itens}"
                )
                continue

            try:
                vl = float(vl_unitario)
                qt = float(qt_itens)
            except (ValueError, TypeError):
                logger.debug(
                    f"[PCP] Skipping item with non-numeric value: "
                    f"vl={vl_unitario!r}, qt={qt_itens!r}"
                )
                continue

            if qt <= 0:
                logger.debug(f"[PCP] Skipping item with qty <= 0: qt={qt}")
                continue

            total += vl * qt

    return round(total, 2)


class PortalComprasAdapter(SourceAdapter):
    """Adapter for Portal de Compras Publicas v2 public API.

    Uses the v2 public API which requires NO authentication.
    Fetches open procurement processes and normalizes to UnifiedProcurement.

    The v2 API does NOT support server-side UF filtering — filtering is done
    client-side after fetching all results.

    The v2 listing endpoint does NOT include value data (valor_estimado will
    be 0.0 for PCP records).
    """

    BASE_URL = "https://compras.api.portaldecompraspublicas.com.br"
    PORTAL_URL = "https://www.portaldecompraspublicas.com.br"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RATE_LIMIT_DELAY = 0.2  # 200ms = 5 req/s
    PAGE_SIZE = 10  # v2 API fixed at 10 per page

    _metadata = SourceMetadata(
        name="Portal de Compras Publicas",
        code="PORTAL_COMPRAS",
        base_url="https://compras.api.portaldecompraspublicas.com.br",
        documentation_url="https://compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos",
        capabilities={
            SourceCapability.PAGINATION,
            SourceCapability.DATE_RANGE,
        },
        rate_limit_rps=5.0,
        typical_response_ms=2500,
        priority=2,
    )

    def __init__(self, api_key: Optional[str] = None, timeout: Optional[int] = None):
        """Initialize Portal de Compras adapter.

        Args:
            api_key: Ignored for v2 API (kept for backward compatibility).
            timeout: Request timeout in seconds.
        """
        # api_key kept for backward compat but unused by v2 API
        self._api_key = api_key or ""
        self._timeout = timeout or self.DEFAULT_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None
        self._last_request_time = 0.0
        self._request_count = 0
        # GTM-FIX-004 AC11: Truncation detection for PCP source
        self.was_truncated: bool = False

    @property
    def metadata(self) -> SourceMetadata:
        return self._metadata

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=httpx.Timeout(self._timeout),
                headers={
                    "Accept": "application/json",
                    "User-Agent": "SmartLic/1.0 (procurement-aggregator)",
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
    ) -> Any:
        """Make HTTP request with retry logic and rate limiting.

        v2 API is public — no auth injection needed.
        """
        await self._rate_limit()
        client = await self._get_client()

        if params is None:
            params = {}

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                logger.debug(
                    f"[PCP] {method} {path} attempt={attempt + 1}/{self.MAX_RETRIES + 1}"
                )

                response = await client.request(method, path, params=params)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < self.MAX_RETRIES:
                        logger.warning(f"[PCP] Rate limited. Waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue
                    raise SourceRateLimitError(self.code, retry_after)

                if response.status_code in (401, 403):
                    raise SourceAuthError(
                        self.code,
                        f"Authentication failed: {response.status_code}"
                    )

                if response.status_code == 200:
                    return response.json()

                if response.status_code == 204:
                    return []

                if response.status_code >= 500:
                    if attempt < self.MAX_RETRIES:
                        delay = self._calculate_backoff(attempt)
                        logger.warning(
                            f"[PCP] Server error {response.status_code}. "
                            f"Retrying in {delay:.1f}s"
                        )
                        await asyncio.sleep(delay)
                        continue

                raise SourceAPIError(self.code, response.status_code, response.text[:200])

            except httpx.TimeoutException as e:
                if attempt < self.MAX_RETRIES:
                    delay = self._calculate_backoff(attempt)
                    logger.warning(f"[PCP] Timeout. Retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                    continue
                raise SourceTimeoutError(self.code, self._timeout) from e

            except httpx.RequestError as e:
                if attempt < self.MAX_RETRIES:
                    delay = self._calculate_backoff(attempt)
                    logger.warning(f"[PCP] Request error: {e}. Retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                    continue
                raise SourceAPIError(self.code, 0, str(e)) from e

        raise SourceAPIError(self.code, 0, "Exhausted retries")

    def _calculate_backoff(self, attempt: int) -> float:
        """Exponential backoff with jitter."""
        delay = min(2.0 * (2 ** attempt), 60.0)
        return delay * random.uniform(0.5, 1.5)

    async def health_check(self) -> SourceStatus:
        """Check PCP v2 API availability.

        Uses a minimal query (1 page, today's date) as health probe.
        No auth needed for v2.
        """
        try:
            client = await self._get_client()
            start = asyncio.get_running_loop().time()

            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            response = await client.get(
                "/v2/licitacao/processos",
                params={
                    "pagina": 1,
                    "dataInicial": today,
                    "dataFinal": today,
                    "tipoData": 1,
                },
                timeout=5.0,
            )

            elapsed_ms = (asyncio.get_running_loop().time() - start) * 1000

            if response.status_code == 200:
                if elapsed_ms > 3000:
                    logger.info(f"[PCP] Health check slow: {elapsed_ms:.0f}ms")
                    return SourceStatus.DEGRADED
                return SourceStatus.AVAILABLE

            logger.warning(f"[PCP] Health check returned {response.status_code}")
            return SourceStatus.DEGRADED

        except (httpx.TimeoutException, httpx.RequestError) as e:
            logger.warning(f"[PCP] Health check failed: {e}")
            return SourceStatus.UNAVAILABLE
        except Exception as e:
            logger.error(f"[PCP] Unexpected health check error: {e}")
            return SourceStatus.UNAVAILABLE

    async def fetch(
        self,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[UnifiedProcurement, None]:
        """Fetch open procurement processes from PCP v2 API.

        v2 API uses ISO dates directly and does NOT support server-side UF
        filtering. UF filtering is done client-side.

        Args:
            data_inicial: Start date YYYY-MM-DD.
            data_final: End date YYYY-MM-DD.
            ufs: Optional set of UF codes for client-side filtering.
        """
        # v2 API uses ISO dates directly — no conversion needed
        params: Dict[str, Any] = {
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "tipoData": 1,
            "pagina": 1,
        }

        seen_ids: Set[str] = set()
        total_fetched = 0
        pagina = 1

        while True:
            params["pagina"] = pagina

            try:
                response = await self._request_with_retry(
                    "GET", "/v2/licitacao/processos", params
                )
            except SourceAuthError:
                raise
            except Exception as e:
                logger.error(f"[PCP] Error fetching page {pagina}: {e}")
                if total_fetched > 0:
                    logger.warning(f"[PCP] Returning {total_fetched} partial results")
                    return
                raise

            # v2 response: { result: [...], total, pageCount, nextPage, ... }
            if isinstance(response, dict):
                data = response.get("result", [])
                total_count = response.get("total", 0)
                page_count = response.get("pageCount", 0)
                next_page = response.get("nextPage")
            elif isinstance(response, list):
                data = response
                total_count = len(data)
                page_count = 1
                next_page = None
            else:
                data = []
                total_count = 0
                page_count = 0
                next_page = None

            if pagina == 1 and total_count > 0:
                logger.info(
                    f"[PCP] {total_count} total records across {page_count} pages"
                )

            if not data:
                break

            for raw_record in data:
                try:
                    record = self.normalize(raw_record)
                except Exception as e:
                    logger.warning(f"[PCP] Failed to normalize record: {e}")
                    continue

                # Client-side UF filtering (v2 API has no server-side UF filter)
                if ufs and record.uf and record.uf not in ufs:
                    continue

                if record.source_id in seen_ids:
                    continue
                seen_ids.add(record.source_id)

                total_fetched += 1
                yield record

            # Check for more pages
            if next_page is None or pagina >= page_count:
                break

            pagina += 1

            if pagina > 100:
                # GTM-FIX-004 AC11: Detect truncation when page limit reached
                self.was_truncated = True
                logger.warning(
                    f"[PCP] Reached page limit (100). "
                    f"Total records ({total_count}) may exceed fetched. "
                    f"Results may be incomplete."
                )
                break

        logger.info(f"[PCP] Fetch complete: {total_fetched} records (truncated={self.was_truncated})")

    def normalize(self, raw_record: Dict[str, Any]) -> UnifiedProcurement:
        """Convert PCP v2 record to UnifiedProcurement.

        v2 field mapping:
        - codigoLicitacao → source_id (prefixed with pcp_)
        - resumo → objeto
        - razaoSocial / nomeUnidade → orgao
        - unidadeCompradora.uf → uf
        - unidadeCompradora.cidade → municipio
        - tipoLicitacao.modalidadeLicitacao → modalidade
        - statusProcessoPublico.descricao → situacao
        - urlReferencia → link_portal
        - dataHoraPublicacao → data_publicacao
        - dataHoraInicioPropostas → data_abertura
        - dataHoraFinalPropostas → data_encerramento
        - numero → numero_edital
        - Value: NOT available in v2 listing → 0.0
        """
        try:
            # Extract and prefix source ID
            codigo = raw_record.get("codigoLicitacao")
            if not codigo:
                raise SourceParseError(self.code, "codigoLicitacao", raw_record)
            source_id = f"pcp_{codigo}"

            # Object description from resumo
            objeto = raw_record.get("resumo") or ""

            # Value: v2 listing does not include value data
            valor = 0.0

            # Extract buyer/agency info from unidadeCompradora
            unidade = raw_record.get("unidadeCompradora") or {}
            if isinstance(unidade, dict):
                orgao = (
                    unidade.get("nomeUnidadeCompradora")
                    or raw_record.get("razaoSocial")
                    or raw_record.get("nomeUnidade")
                    or ""
                )
                cnpj = unidade.get("CNPJ") or unidade.get("cnpj") or ""
                municipio = unidade.get("cidade") or ""
                uf = unidade.get("uf") or ""
            else:
                orgao = raw_record.get("razaoSocial") or ""
                cnpj = ""
                municipio = ""
                uf = ""

            # Parse dates (v2 uses ISO format)
            data_publicacao = self._parse_datetime(raw_record.get("dataHoraPublicacao"))
            data_abertura = self._parse_datetime(raw_record.get("dataHoraInicioPropostas"))
            data_encerramento = self._parse_datetime(raw_record.get("dataHoraFinalPropostas"))

            # Extract edital number and year
            numero_edital = raw_record.get("numero") or raw_record.get("identificacao") or ""
            ano = ""
            if data_publicacao:
                ano = str(data_publicacao.year)

            # Modality from tipoLicitacao object
            tipo_lic = raw_record.get("tipoLicitacao") or {}
            if isinstance(tipo_lic, dict):
                modalidade = tipo_lic.get("modalidadeLicitacao") or tipo_lic.get("tipoLicitacao") or ""
            else:
                modalidade = str(tipo_lic) if tipo_lic else ""

            # Status from statusProcessoPublico
            status_obj = raw_record.get("statusProcessoPublico") or raw_record.get("status") or {}
            if isinstance(status_obj, dict):
                situacao = status_obj.get("descricao") or ""
            else:
                situacao = str(status_obj) if status_obj else ""

            # Portal link from urlReferencia
            url_ref = raw_record.get("urlReferencia") or ""
            if url_ref:
                link_portal = f"{self.PORTAL_URL}{url_ref}"
            else:
                link_portal = f"{self.PORTAL_URL}/processos/{codigo}"

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
            logger.error(f"[PCP] Normalization error: {e}")
            raise SourceParseError(self.code, "record", str(e)) from e

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime from PCP v2 ISO format."""
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

            cleaned = value.replace("+00:00", "Z").replace("+0000", "Z")
            for fmt in formats:
                try:
                    return datetime.strptime(cleaned.rstrip("Z"), fmt.rstrip("Z"))
                except ValueError:
                    continue

            logger.debug(f"[PCP] Failed to parse datetime: {value}")

        return None

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            logger.debug(f"[PCP] Client closed. Total requests: {self._request_count}")
        self._client = None

    async def __aenter__(self) -> "PortalComprasAdapter":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
