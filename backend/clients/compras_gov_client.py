"""ComprasGov API client adapter (Federal Open Data).

This module implements the SourceAdapter interface for the ComprasGov
open data API (https://compras.dados.gov.br/).

API Characteristics:
- REST API with JSON responses
- No authentication required (open government data)
- Federal procurement data
- Rate limit: conservative 2 req/s

Documentation: https://compras.dados.gov.br/
"""

import asyncio
import logging
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
    SourceRateLimitError,
    SourceTimeoutError,
    SourceParseError,
    UnifiedProcurement,
)

logger = logging.getLogger(__name__)


class ComprasGovAdapter(SourceAdapter):
    """
    Adapter for ComprasGov Federal Open Data API.

    This adapter fetches procurement data from the Brazilian federal
    government's open data portal. No authentication is required.

    Attributes:
        BASE_URL: API base URL
        DEFAULT_TIMEOUT: Request timeout in seconds
        MAX_RETRIES: Maximum number of retry attempts
        RATE_LIMIT_DELAY: Minimum delay between requests (seconds)
    """

    BASE_URL = "https://compras.dados.gov.br"
    DEFAULT_TIMEOUT = 25
    MAX_RETRIES = 3
    RATE_LIMIT_DELAY = 0.5  # 500ms between requests (~2 req/s)
    PAGE_SIZE = 500

    # Modalidade name normalization mapping (Lei 14.133/2021)
    MODALIDADE_MAPPING = {
        # Exact Lei 14.133 names (preferred output)
        "Pregao Eletronico": "Pregao Eletronico",
        "Pregao Presencial": "Pregao Presencial",
        "Concorrencia": "Concorrencia",
        "Concurso": "Concurso",
        "Leilao": "Leilao",
        "Dispensa de Licitacao": "Dispensa de Licitacao",
        "Inexigibilidade": "Inexigibilidade",
        "Dialogo Competitivo": "Dialogo Competitivo",
        # Common variations (input normalization)
        "PREGAO ELETRONICO": "Pregao Eletronico",
        "PREGÃO ELETRÔNICO": "Pregao Eletronico",
        "Pregão Eletrônico": "Pregao Eletronico",
        "pregão eletrônico": "Pregao Eletronico",
        "Pregão - Eletrônico": "Pregao Eletronico",
        "PE": "Pregao Eletronico",
        "PREGAO PRESENCIAL": "Pregao Presencial",
        "PREGÃO PRESENCIAL": "Pregao Presencial",
        "Pregão Presencial": "Pregao Presencial",
        "pregão presencial": "Pregao Presencial",
        "Pregão - Presencial": "Pregao Presencial",
        "PP": "Pregao Presencial",
        "CONCORRENCIA": "Concorrencia",
        "CONCORRÊNCIA": "Concorrencia",
        "Concorrência": "Concorrencia",
        "concorrência": "Concorrencia",
        "CONCURSO": "Concurso",
        "concurso": "Concurso",
        "LEILAO": "Leilao",
        "LEILÃO": "Leilao",
        "Leilão": "Leilao",
        "leilão": "Leilao",
        "DISPENSA DE LICITACAO": "Dispensa de Licitacao",
        "DISPENSA DE LICITAÇÃO": "Dispensa de Licitacao",
        "Dispensa de Licitação": "Dispensa de Licitacao",
        "dispensa de licitação": "Dispensa de Licitacao",
        "Dispensa": "Dispensa de Licitacao",
        "DISPENSA": "Dispensa de Licitacao",
        "INEXIGIBILIDADE": "Inexigibilidade",
        "Inexigibilidade": "Inexigibilidade",
        "inexigibilidade": "Inexigibilidade",
        "Inexigível": "Inexigibilidade",
        "INEXIGIVEL": "Inexigibilidade",
        "DIALOGO COMPETITIVO": "Dialogo Competitivo",
        "DIÁLOGO COMPETITIVO": "Dialogo Competitivo",
        "Diálogo Competitivo": "Dialogo Competitivo",
        "diálogo competitivo": "Dialogo Competitivo",
        # Deprecated (Lei 8.666/93) - flag for logging
        "Tomada de Precos": "DEPRECATED_TOMADA_PRECOS",
        "TOMADA DE PREÇOS": "DEPRECATED_TOMADA_PRECOS",
        "Tomada de Preços": "DEPRECATED_TOMADA_PRECOS",
        "TP": "DEPRECATED_TOMADA_PRECOS",
        "Convite": "DEPRECATED_CONVITE",
        "CONVITE": "DEPRECATED_CONVITE",
        "convite": "DEPRECATED_CONVITE",
    }

    _metadata = SourceMetadata(
        name="ComprasGov - Dados Abertos Federal",
        code="COMPRAS_GOV",
        base_url="https://compras.dados.gov.br",
        documentation_url="https://compras.dados.gov.br/",
        capabilities={
            SourceCapability.PAGINATION,
            SourceCapability.DATE_RANGE,
        },
        rate_limit_rps=2.0,
        typical_response_ms=3000,
        priority=4,
    )

    def __init__(self, timeout: Optional[int] = None):
        """
        Initialize ComprasGov adapter.

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
                    return {"_embedded": {"licitacoes": []}, "count": 0}

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

    def _normalize_modalidade_name(self, raw_name: str) -> str:
        """
        Normalize modalidade name to Lei 14.133 standard.

        Args:
            raw_name: Raw modalidade name from API

        Returns:
            Normalized modalidade name or empty string
        """
        if not raw_name:
            return ""

        # Try direct mapping first
        normalized = self.MODALIDADE_MAPPING.get(raw_name)
        if normalized:
            if normalized.startswith("DEPRECATED_"):
                logger.warning(
                    f"[COMPRAS_GOV] Deprecated modalidade found: {raw_name}. "
                    "This modality was revoked by Lei 14.133/2021."
                )
                # Return normalized name without DEPRECATED_ prefix for legacy data
                return normalized.replace("DEPRECATED_", "").replace("_", " ").title()
            return normalized

        # Try case-insensitive match
        raw_upper = raw_name.upper()
        for key, value in self.MODALIDADE_MAPPING.items():
            if key.upper() == raw_upper:
                return value

        # Unknown modalidade - log warning
        logger.warning(
            f"[COMPRAS_GOV] Unknown modalidade name: {raw_name}. "
            "Please add to MODALIDADE_MAPPING if valid."
        )
        return raw_name  # Return as-is for debugging

    async def health_check(self) -> SourceStatus:
        """
        Check if ComprasGov API is available.

        Returns:
            SourceStatus indicating current health
        """
        try:
            client = await self._get_client()
            start = asyncio.get_event_loop().time()

            response = await client.get(
                "/licitacoes/v1/licitacoes.json",
                params={"offset": 0, "limit": 1},
                timeout=5.0,
            )

            elapsed_ms = (asyncio.get_event_loop().time() - start) * 1000

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
        """
        Fetch procurement records from ComprasGov.

        Args:
            data_inicial: Start date in YYYY-MM-DD format
            data_final: End date in YYYY-MM-DD format
            ufs: Optional set of Brazilian state codes to filter (client-side)
            **kwargs: Additional parameters

        Yields:
            UnifiedProcurement records
        """
        offset = 0
        total_fetched = 0
        seen_ids: Set[str] = set()

        while True:
            params: Dict[str, Any] = {
                "data_inicio": data_inicial,
                "data_fim": data_final,
                "offset": offset,
                "limit": self.PAGE_SIZE,
            }

            try:
                response = await self._request_with_retry(
                    "GET", "/licitacoes/v1/licitacoes.json", params
                )
            except Exception as e:
                logger.error(f"[COMPRAS_GOV] Error fetching offset {offset}: {e}")
                if total_fetched > 0:
                    logger.warning(f"[COMPRAS_GOV] Returning {total_fetched} partial results")
                    return
                raise

            # Extract data - ComprasGov uses _embedded pattern or direct list
            data = response.get("_embedded", {}).get("licitacoes", [])
            if not data:
                data = response.get("licitacoes", [])
            if not data:
                data = response.get("data", [])

            total_count = response.get("count", response.get("total", 0))

            if offset == 0:
                logger.info(
                    f"[COMPRAS_GOV] Query returned {total_count} total records"
                )

            if not data:
                logger.debug(f"[COMPRAS_GOV] No more data at offset {offset}")
                break

            for raw_record in data:
                try:
                    record = self.normalize(raw_record)

                    if record.source_id in seen_ids:
                        continue
                    seen_ids.add(record.source_id)

                    # Client-side UF filtering
                    if ufs and record.uf and record.uf not in ufs:
                        continue

                    total_fetched += 1
                    yield record

                except Exception as e:
                    logger.warning(f"[COMPRAS_GOV] Failed to normalize record: {e}")
                    continue

            if total_fetched % 100 == 0 and total_fetched > 0:
                logger.info(f"[COMPRAS_GOV] Progress: {total_fetched} records fetched")

            # Check if there are more results
            if len(data) < self.PAGE_SIZE:
                break

            offset += self.PAGE_SIZE

            # Safety limit
            if offset > 50000:
                logger.warning("[COMPRAS_GOV] Reached offset limit (50000)")
                break

        logger.info(f"[COMPRAS_GOV] Fetch complete: {total_fetched} records")

    def normalize(self, raw_record: Dict[str, Any]) -> UnifiedProcurement:
        """
        Convert ComprasGov record to UnifiedProcurement.

        The API field names may vary; this method tries multiple variations.

        Args:
            raw_record: Raw record from API response

        Returns:
            Normalized UnifiedProcurement record
        """
        try:
            # Extract source ID (try multiple field names)
            source_id = str(
                raw_record.get("identificador")
                or raw_record.get("id")
                or raw_record.get("numero")
                or ""
            )

            if not source_id:
                raise SourceParseError(self.code, "source_id", raw_record)

            # Extract value
            valor = (
                raw_record.get("valor_licitacao")
                or raw_record.get("valor")
                or raw_record.get("valor_estimado")
                or 0
            )
            if isinstance(valor, str):
                valor = valor.replace(".", "").replace(",", ".")
                try:
                    valor = float(valor)
                except ValueError:
                    valor = 0.0

            # Extract orgao info
            orgao_nome = (
                raw_record.get("orgao_nome")
                or raw_record.get("nome_orgao")
                or raw_record.get("uasg_nome")
                or ""
            )
            orgao_cnpj = (
                raw_record.get("orgao_cnpj")
                or raw_record.get("cnpj")
                or raw_record.get("uasg_cnpj")
                or ""
            )

            # Extract location
            uf = raw_record.get("uf") or raw_record.get("estado") or ""
            municipio = raw_record.get("municipio") or raw_record.get("cidade") or ""

            # Parse dates
            data_publicacao = self._parse_datetime(
                raw_record.get("data_publicacao")
                or raw_record.get("data_resultado_compra")
            )
            data_abertura = self._parse_datetime(
                raw_record.get("data_abertura")
                or raw_record.get("data_abertura_proposta")
            )

            # Extract edital info
            numero_edital = str(
                raw_record.get("numero_aviso")
                or raw_record.get("numero_edital")
                or raw_record.get("numero")
                or ""
            )
            ano = str(
                raw_record.get("ano")
                or raw_record.get("ano_compra")
                or ""
            )
            if not ano and data_publicacao:
                ano = str(data_publicacao.year)

            # Build link
            link = raw_record.get("link") or raw_record.get("url") or ""
            if not link and source_id:
                link = f"https://compras.dados.gov.br/licitacoes/id/licitacao/{source_id}"

            # Extract objeto
            objeto = (
                raw_record.get("objeto")
                or raw_record.get("descricao")
                or raw_record.get("informacao_geral")
                or ""
            )

            # Extract modalidade
            modalidade_raw = (
                raw_record.get("modalidade_licitacao")
                or raw_record.get("modalidade")
                or raw_record.get("tipo")
                or ""
            )

            # Normalize modalidade name
            modalidade = self._normalize_modalidade_name(modalidade_raw)

            # Extract situacao
            situacao = (
                raw_record.get("situacao")
                or raw_record.get("situacao_aviso")
                or raw_record.get("status")
                or ""
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
                numero_edital=numero_edital,
                ano=ano,
                modalidade=modalidade,
                situacao=situacao,
                esfera="F",  # Federal
                link_edital=link,
                link_portal=link,
                fetched_at=datetime.utcnow(),
                raw_data=raw_record,
            )

        except SourceParseError:
            raise
        except Exception as e:
            logger.error(f"[COMPRAS_GOV] Normalization error: {e}")
            raise SourceParseError(self.code, "record", str(e)) from e

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
