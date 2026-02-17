"""Portal de Compras Publicas API client adapter.

This module implements the SourceAdapter interface for the Portal de Compras
Publicas API (https://apipcp.portaldecompraspublicas.com.br/).

API Characteristics:
- REST API with JSON responses
- Auth via publicKey query parameter (NOT header)
- Date format: DD/MM/AAAA
- Pagination via quantidadeTotal + page calculation
- Value: sum of VL_UNITARIO_ESTIMADO * QT_ITENS per item across lots

GTM-FIX-011: Completed with real PCP API endpoints.
"""

import asyncio
import logging
import math
import os
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
from utils.date_parser import iso_to_br

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
    """Adapter for Portal de Compras Publicas API.

    Uses real PCP API endpoints with publicKey authentication.
    Fetches open procurement processes and normalizes to UnifiedProcurement.

    Environment Variables:
        PCP_PUBLIC_KEY: API key (preferred)
        PORTAL_COMPRAS_API_KEY: API key (legacy fallback)
    """

    BASE_URL = "https://apipcp.portaldecompraspublicas.com.br"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RATE_LIMIT_DELAY = 0.2  # 200ms = 5 req/s (AC5: conservative start)
    PAGE_SIZE = 50

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
        rate_limit_rps=5.0,
        typical_response_ms=2500,
        priority=2,
    )

    def __init__(self, api_key: Optional[str] = None, timeout: Optional[int] = None):
        """Initialize Portal de Compras adapter.

        Args:
            api_key: API key. Falls back to PCP_PUBLIC_KEY or PORTAL_COMPRAS_API_KEY env vars.
            timeout: Request timeout in seconds.
        """
        self._api_key = (
            api_key
            or os.environ.get("PCP_PUBLIC_KEY", "")
            or os.environ.get("PORTAL_COMPRAS_API_KEY", "")
        )
        self._timeout = timeout or self.DEFAULT_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None
        self._last_request_time = 0.0
        self._request_count = 0

    @property
    def metadata(self) -> SourceMetadata:
        return self._metadata

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client. Auth is via URL params, not headers."""
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

        AC4: Auth via publicKey param — NEVER hardcoded.
        """
        await self._rate_limit()
        client = await self._get_client()

        # AC4: Inject publicKey into every request
        if params is None:
            params = {}
        params["publicKey"] = self._api_key

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
                        f"Authentication failed (key may be expired): {response.status_code}"
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
        """Check PCP API availability.

        AC6: Returns UNAVAILABLE on 401 (key expired).
        Uses minimal query (page 1, 1 UF) as health probe.
        """
        if not self._api_key:
            logger.warning("[PCP] No API key configured")
            return SourceStatus.UNAVAILABLE

        try:
            client = await self._get_client()
            start = asyncio.get_running_loop().time()

            # Use processos abertos endpoint with minimal params
            response = await client.get(
                "/publico/obterprocessosabertos",
                params={
                    "publicKey": self._api_key,
                    "uf": "SP",
                    "pagina": 1,
                },
                timeout=5.0,
            )

            elapsed_ms = (asyncio.get_running_loop().time() - start) * 1000

            if response.status_code in (401, 403):
                logger.warning("[PCP] Auth failed in health check — key may be expired")
                return SourceStatus.UNAVAILABLE

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
        """Fetch open procurement processes from PCP.

        AC1: Uses /publico/obterprocessosabertos endpoint.
        AC2: Pagination via quantidadeTotal field.

        Args:
            data_inicial: Start date YYYY-MM-DD (converted to DD/MM/AAAA for PCP).
            data_final: End date YYYY-MM-DD.
            ufs: Optional set of UF codes. PCP supports single UF per request.
        """
        if not self._api_key:
            logger.warning("[PCP] No API key configured — skipping fetch")
            return

        # Convert dates from ISO to BR format for PCP API
        data_inicio_br = iso_to_br(data_inicial)
        data_fim_br = iso_to_br(data_final)

        if not data_inicio_br or not data_fim_br:
            logger.error(f"[PCP] Invalid date range: {data_inicial} to {data_final}")
            return

        # PCP API supports single UF filter. If multiple UFs, iterate per-UF.
        uf_list = sorted(ufs) if ufs else [None]

        seen_ids: Set[str] = set()
        total_fetched = 0

        for uf in uf_list:
            params: Dict[str, Any] = {
                "dataInicio": data_inicio_br,
                "dataFim": data_fim_br,
                "pagina": 1,
            }
            if uf:
                params["uf"] = uf

            pagina = 1
            total_pages: Optional[int] = None

            while True:
                params["pagina"] = pagina

                try:
                    response = await self._request_with_retry(
                        "GET", "/publico/obterprocessosabertos", params
                    )
                except SourceAuthError:
                    raise
                except Exception as e:
                    logger.error(f"[PCP] Error fetching page {pagina} UF={uf}: {e}")
                    if total_fetched > 0:
                        logger.warning(f"[PCP] Returning {total_fetched} partial results")
                        return
                    raise

                # PCP returns a list or object with quantidadeTotal
                if isinstance(response, list):
                    data = response
                    quantity_total = len(data)
                elif isinstance(response, dict):
                    data = response.get("processos", response.get("data", []))
                    if isinstance(data, list):
                        pass
                    else:
                        data = []
                    quantity_total = response.get("quantidadeTotal", len(data))
                else:
                    data = []
                    quantity_total = 0

                # Calculate total pages on first request
                if total_pages is None and quantity_total > 0:
                    total_pages = math.ceil(quantity_total / max(len(data), 1))
                    logger.info(
                        f"[PCP] UF={uf}: {quantity_total} total records, "
                        f"~{total_pages} pages"
                    )

                if not data:
                    break

                for raw_record in data:
                    try:
                        record = self.normalize(raw_record)
                    except Exception as e:
                        logger.warning(f"[PCP] Failed to normalize record: {e}")
                        continue

                    if record.source_id in seen_ids:
                        continue
                    seen_ids.add(record.source_id)

                    total_fetched += 1
                    yield record

                # Check for more pages
                if total_pages is not None and pagina >= total_pages:
                    break

                pagina += 1

                if pagina > 100:
                    logger.warning(f"[PCP] UF={uf}: Reached page limit (100)")
                    break

        logger.info(f"[PCP] Fetch complete: {total_fetched} records")

    def normalize(self, raw_record: Dict[str, Any]) -> UnifiedProcurement:
        """Convert PCP record to UnifiedProcurement.

        AC3: Proper field mapping from PCP API structure.
        AC8: Value calculated from lotes/itens.
        AC9: objeto = DS_OBJETO + all DS_ITEM concatenated.
        AC10: source_id prefixed with pcp_.
        AC11: link to Portal de Compras Publicas.
        AC12: source = PORTAL_COMPRAS (SourceCode.PORTAL).
        """
        try:
            # AC10: Extract and prefix source ID
            id_licitacao = raw_record.get("idLicitacao") or raw_record.get("id") or ""
            if not id_licitacao:
                raise SourceParseError(self.code, "idLicitacao", raw_record)
            source_id = f"pcp_{id_licitacao}"

            # AC9: Build objeto from DS_OBJETO + all DS_ITEM
            ds_objeto = raw_record.get("DS_OBJETO") or raw_record.get("objeto") or ""
            item_descriptions = []
            lotes = raw_record.get("lotes") or []
            for lote in lotes:
                for item in (lote.get("itens") or []):
                    ds_item = item.get("DS_ITEM") or ""
                    if ds_item:
                        item_descriptions.append(ds_item)
            # Concatenate object + items for keyword matching
            if item_descriptions:
                objeto = f"{ds_objeto} | {' | '.join(item_descriptions)}"
            else:
                objeto = ds_objeto

            # AC8: Calculate value from lots
            valor = calculate_total_value(lotes)

            # Also try direct value field as fallback
            if valor == 0.0:
                valor_direto = raw_record.get("valorEstimado") or raw_record.get("VL_ESTIMADO") or 0
                try:
                    valor = float(valor_direto)
                except (ValueError, TypeError):
                    valor = 0.0

            # Extract buyer/agency info
            unidade = raw_record.get("unidadeCompradora") or {}
            if isinstance(unidade, dict):
                orgao = unidade.get("nomeComprador") or unidade.get("nome") or ""
                cnpj = unidade.get("CNPJ") or unidade.get("cnpj") or ""
                municipio = unidade.get("Cidade") or unidade.get("cidade") or ""
                uf = unidade.get("UF") or unidade.get("uf") or ""
            else:
                orgao = str(unidade) if unidade else ""
                cnpj = ""
                municipio = ""
                uf = ""

            # Fallback UF from top-level
            if not uf:
                uf = raw_record.get("UF") or raw_record.get("uf") or ""

            # Parse dates (PCP uses DD/MM/AAAA)
            data_publicacao = self._parse_datetime(raw_record.get("dataPublicacao"))
            data_abertura = self._parse_datetime(raw_record.get("dataAbertura"))
            data_encerramento = self._parse_datetime(raw_record.get("dataEncerramento"))

            # Extract edital number and year for dedup
            numero_edital = raw_record.get("numeroEdital") or raw_record.get("numero") or ""
            ano = raw_record.get("ano") or ""
            if not ano and data_publicacao:
                ano = str(data_publicacao.year)

            # AC11: Portal link
            link_portal = f"https://www.portaldecompraspublicas.com.br/processos/{id_licitacao}"

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
                ano=str(ano) if ano else "",
                modalidade=raw_record.get("modalidade") or raw_record.get("tipoLicitacao") or "",
                situacao=raw_record.get("situacao") or raw_record.get("status") or "",
                esfera=raw_record.get("esfera") or "",
                poder=raw_record.get("poder") or "",
                link_edital=raw_record.get("linkDocumentos") or "",
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
        """Parse datetime from PCP formats (DD/MM/AAAA and ISO)."""
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
                "%d/%m/%Y %H:%M:%S",
                "%d/%m/%Y",
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
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
