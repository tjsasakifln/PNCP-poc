"""Sanctions checker for Portal da Transparencia CEIS and CNEP APIs.

This module queries the Brazilian federal sanctions databases (CEIS and CNEP)
to determine whether a company (by CNPJ) has active sanctions that would
disqualify it from government procurement.

STORY-254 AC8-AC11.

API Details:
    - Base URL: https://api.portaldatransparencia.gov.br/api-de-dados
    - Auth: Header ``chave-api-dados: {API_KEY}``
    - Rate limit: 90 req/min (~667ms between requests)
    - CEIS: Cadastro de Empresas Inidooneas e Suspensas
    - CNEP: Cadastro Nacional de Empresas Punidas

Databases:
    - CEIS tracks companies barred from contracting with the government
      (impedimentos, suspensoes, declaracoes de inidoneidade).
    - CNEP tracks companies punished under the Anti-Corruption Law
      (Lei 12.846/2013), including fine amounts.
"""

import asyncio
import logging
import os
import re
import time
import random
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SanctionRecord:
    """A single sanction entry from CEIS or CNEP."""

    source: str  # "CEIS" | "CNEP"
    cnpj: str
    company_name: str
    sanction_type: str  # "Impedimento", "Inidoneidade", "Suspensao", etc.
    start_date: Optional[date]
    end_date: Optional[date]
    sanctioning_body: str  # "Ministerio da Defesa", etc.
    legal_basis: str  # "Lei 8.666/1993, Art. 87, IV"
    fine_amount: Optional[Decimal]  # CNEP only
    is_active: bool  # end_date is None or end_date > today


@dataclass
class SanctionsResult:
    """Aggregated result from checking both CEIS and CNEP for a CNPJ."""

    cnpj: str
    is_sanctioned: bool
    sanctions: List[SanctionRecord]
    checked_at: datetime
    ceis_count: int
    cnep_count: int
    cache_hit: bool = False


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SanctionsAPIError(Exception):
    """Error communicating with the Portal da Transparencia API."""

    def __init__(self, source: str, status_code: int, message: str = ""):
        self.source = source
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{source}] HTTP {status_code}: {message[:200]}")


class SanctionsRateLimitError(SanctionsAPIError):
    """Rate limit (429) from Portal da Transparencia."""

    def __init__(self, source: str, retry_after: Optional[int] = None):
        super().__init__(source, 429, "Rate limit exceeded")
        self.retry_after = retry_after


# ---------------------------------------------------------------------------
# SanctionsChecker
# ---------------------------------------------------------------------------


class SanctionsChecker:
    """
    Async client that queries Portal da Transparencia CEIS and CNEP APIs.

    Usage::

        async with SanctionsChecker() as checker:
            result = await checker.check_sanctions("12345678000100")
            if result.is_sanctioned:
                print(f"{result.cnpj} has {len(result.sanctions)} sanction(s)")

    Args:
        api_key: Portal da Transparencia API key. Falls back to the
            ``PORTAL_TRANSPARENCIA_API_KEY`` environment variable.
        timeout: HTTP request timeout in seconds.
    """

    BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados"
    DEFAULT_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    RATE_LIMIT_DELAY = 0.667  # ~90 req/min
    CACHE_TTL_SECONDS = 86_400  # 24 hours

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("PORTAL_TRANSPARENCIA_API_KEY", "")
        self._timeout = timeout or self.DEFAULT_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None
        self._last_request_time: float = 0.0
        self._request_count: int = 0

        # In-memory cache: cnpj_digits -> (SanctionsResult, timestamp)
        self._cache: Dict[str, Tuple[SanctionsResult, float]] = {}

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazily create (or re-create) the httpx async client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=httpx.Timeout(self._timeout),
                headers={
                    "Accept": "application/json",
                    "User-Agent": "SmartLic/1.0 (sanctions-checker)",
                    "chave-api-dados": self._api_key,
                },
            )
        return self._client

    async def _rate_limit(self) -> None:
        """Enforce minimum interval between requests."""
        now = asyncio.get_running_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = asyncio.get_running_loop().time()
        self._request_count += 1

    def _calculate_backoff(self, attempt: int) -> float:
        """Exponential backoff with jitter."""
        delay = min(2.0 * (2 ** attempt), 60.0)
        delay *= random.uniform(0.5, 1.5)
        return delay

    async def _request_with_retry(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        GET *path* with automatic retry on 429 / 5xx / network errors.

        Returns:
            Parsed JSON response (expected to be a list of records).

        Raises:
            SanctionsRateLimitError: After exhausting retries on 429.
            SanctionsAPIError: On non-retryable HTTP errors.
        """
        await self._rate_limit()
        client = await self._get_client()

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                logger.debug(
                    "[SANCTIONS] GET %s params=%s attempt=%d/%d",
                    path, params, attempt + 1, self.MAX_RETRIES + 1,
                )

                response = await client.get(path, params=params)

                # --- 429 Rate Limit ---
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < self.MAX_RETRIES:
                        logger.warning(
                            "[SANCTIONS] Rate limited. Waiting %ds", retry_after,
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    raise SanctionsRateLimitError("SANCTIONS", retry_after)

                # --- 200 OK ---
                if response.status_code == 200:
                    data = response.json()
                    # API may return a list directly or an empty list
                    if isinstance(data, list):
                        return data
                    # Defensive: some endpoints wrap in an object
                    if isinstance(data, dict):
                        return data.get("data", data.get("registros", []))
                    return []

                # --- 204 No Content ---
                if response.status_code == 204:
                    return []

                # --- 5xx Server Error ---
                if response.status_code >= 500:
                    if attempt < self.MAX_RETRIES:
                        delay = self._calculate_backoff(attempt)
                        logger.warning(
                            "[SANCTIONS] Server error %d. Retrying in %.1fs",
                            response.status_code, delay,
                        )
                        await asyncio.sleep(delay)
                        continue

                # Non-retryable error
                raise SanctionsAPIError(
                    "SANCTIONS", response.status_code, response.text[:500],
                )

            except httpx.TimeoutException:
                if attempt < self.MAX_RETRIES:
                    delay = self._calculate_backoff(attempt)
                    logger.warning(
                        "[SANCTIONS] Timeout. Retrying in %.1fs", delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                logger.error("[SANCTIONS] Timeout after %d retries", self.MAX_RETRIES)
                raise SanctionsAPIError("SANCTIONS", 0, "Timeout after retries")

            except httpx.RequestError as exc:
                if attempt < self.MAX_RETRIES:
                    delay = self._calculate_backoff(attempt)
                    logger.warning(
                        "[SANCTIONS] Request error: %s. Retrying in %.1fs",
                        exc, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                logger.error(
                    "[SANCTIONS] Request error after %d retries: %s",
                    self.MAX_RETRIES, exc,
                )
                raise SanctionsAPIError("SANCTIONS", 0, str(exc))

        # Should not reach here, but guard anyway
        raise SanctionsAPIError("SANCTIONS", 0, "Exhausted retries")

    # ------------------------------------------------------------------
    # CNPJ normalisation
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_cnpj(cnpj: str) -> str:
        """Strip everything except digits from a CNPJ string."""
        return re.sub(r"[^\d]", "", cnpj)

    # ------------------------------------------------------------------
    # Date parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[date]:
        """
        Parse a date string in DD/MM/YYYY format (Portal da Transparencia).

        Returns None for empty / unparseable values.
        """
        if not value:
            return None

        # Portal da Transparencia uses DD/MM/YYYY
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except (ValueError, AttributeError):
                continue

        logger.debug("[SANCTIONS] Failed to parse date: %s", value)
        return None

    # ------------------------------------------------------------------
    # Record parsers
    # ------------------------------------------------------------------

    def _parse_ceis_record(self, raw: Dict[str, Any]) -> SanctionRecord:
        """
        Parse a single CEIS API record into a SanctionRecord.

        CEIS response relevant fields:
            - tipo.descricaoResumida  -> sanction_type
            - sancionado.nome         -> company_name
            - sancionado.codigoFormatado -> cnpj
            - dataInicioSancao        -> start_date (DD/MM/YYYY)
            - dataFinalSancao         -> end_date (DD/MM/YYYY, may be null)
            - orgaoSancionador.nome   -> sanctioning_body
            - fundamentacao.descricao -> legal_basis
        """
        sancionado = raw.get("sancionado") or {}
        tipo = raw.get("tipo") or {}
        orgao = raw.get("orgaoSancionador") or {}
        fundamentacao = raw.get("fundamentacao") or {}

        start_date = self._parse_date(raw.get("dataInicioSancao"))
        end_date = self._parse_date(raw.get("dataFinalSancao"))

        today = date.today()
        is_active = end_date is None or end_date > today

        return SanctionRecord(
            source="CEIS",
            cnpj=sancionado.get("codigoFormatado", ""),
            company_name=sancionado.get("nome", ""),
            sanction_type=tipo.get("descricaoResumida", ""),
            start_date=start_date,
            end_date=end_date,
            sanctioning_body=orgao.get("nome", ""),
            legal_basis=fundamentacao.get("descricao", ""),
            fine_amount=None,  # CEIS does not have fine amounts
            is_active=is_active,
        )

    def _parse_cnep_record(self, raw: Dict[str, Any]) -> SanctionRecord:
        """
        Parse a single CNEP API record into a SanctionRecord.

        CNEP response relevant fields:
            - tipoSancao.descricaoResumida -> sanction_type
            - sancionado.nome              -> company_name
            - sancionado.codigoFormatado   -> cnpj
            - dataInicioSancao             -> start_date
            - dataFinalSancao              -> end_date
            - orgaoSancionador.nome        -> sanctioning_body
            - fundamentacao.descricao      -> legal_basis
            - valorMulta                   -> fine_amount (Decimal)
        """
        sancionado = raw.get("sancionado") or {}
        tipo_sancao = raw.get("tipoSancao") or {}
        orgao = raw.get("orgaoSancionador") or {}
        fundamentacao = raw.get("fundamentacao") or {}

        start_date = self._parse_date(raw.get("dataInicioSancao"))
        end_date = self._parse_date(raw.get("dataFinalSancao"))

        today = date.today()
        is_active = end_date is None or end_date > today

        # Parse fine amount
        fine_amount: Optional[Decimal] = None
        raw_fine = raw.get("valorMulta")
        if raw_fine is not None:
            try:
                fine_amount = Decimal(str(raw_fine))
            except (InvalidOperation, ValueError, TypeError):
                logger.warning(
                    "[SANCTIONS] Could not parse fine amount: %s", raw_fine,
                )

        return SanctionRecord(
            source="CNEP",
            cnpj=sancionado.get("codigoFormatado", ""),
            company_name=sancionado.get("nome", ""),
            sanction_type=tipo_sancao.get("descricaoResumida", ""),
            start_date=start_date,
            end_date=end_date,
            sanctioning_body=orgao.get("nome", ""),
            legal_basis=fundamentacao.get("descricao", ""),
            fine_amount=fine_amount,
            is_active=is_active,
        )

    # ------------------------------------------------------------------
    # Paginated fetcher
    # ------------------------------------------------------------------

    async def _fetch_all_pages(
        self,
        path: str,
        cnpj_digits: str,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all pages for a given endpoint / CNPJ.

        Portal da Transparencia uses ``pagina`` param (1-based).
        An empty page signals the end of data.
        """
        all_records: List[Dict[str, Any]] = []
        pagina = 1

        while True:
            params: Dict[str, Any] = {
                "codigoSancionado": cnpj_digits,
                "pagina": pagina,
            }

            page_data = await self._request_with_retry(path, params)

            if not page_data:
                break

            all_records.extend(page_data)
            pagina += 1

            # Safety limit to avoid infinite loops on misbehaving APIs
            if pagina > 50:
                logger.warning(
                    "[SANCTIONS] Reached page limit (50) for %s on %s",
                    cnpj_digits, path,
                )
                break

        return all_records

    # ------------------------------------------------------------------
    # Public API (AC8, AC9, AC10)
    # ------------------------------------------------------------------

    async def check_ceis(self, cnpj: str) -> List[SanctionRecord]:
        """
        Query CEIS (Cadastro de Empresas Inidoneas e Suspensas) for a CNPJ.

        AC8: Returns a list of active sanction records found in CEIS.

        Args:
            cnpj: CNPJ in any format (digits only, or with separators).

        Returns:
            List of SanctionRecord entries from CEIS.
            Returns an empty list on API failure (logs warning).
        """
        cnpj_digits = self._clean_cnpj(cnpj)

        if not cnpj_digits:
            logger.warning("[SANCTIONS] Empty CNPJ provided to check_ceis")
            return []

        try:
            raw_records = await self._fetch_all_pages("/ceis", cnpj_digits)
            records = []
            for raw in raw_records:
                try:
                    record = self._parse_ceis_record(raw)
                    records.append(record)
                except Exception as exc:
                    logger.warning(
                        "[SANCTIONS] Failed to parse CEIS record: %s", exc,
                    )
            logger.info(
                "[SANCTIONS] CEIS check for %s: %d record(s) found",
                cnpj_digits, len(records),
            )
            return records

        except Exception as exc:
            logger.warning(
                "[SANCTIONS] CEIS query failed for %s: %s", cnpj_digits, exc,
            )
            return []

    async def check_cnep(self, cnpj: str) -> List[SanctionRecord]:
        """
        Query CNEP (Cadastro Nacional de Empresas Punidas) for a CNPJ.

        AC9: Returns sanctions including fine amounts.

        Args:
            cnpj: CNPJ in any format (digits only, or with separators).

        Returns:
            List of SanctionRecord entries from CNEP.
            Returns an empty list on API failure (logs warning).
        """
        cnpj_digits = self._clean_cnpj(cnpj)

        if not cnpj_digits:
            logger.warning("[SANCTIONS] Empty CNPJ provided to check_cnep")
            return []

        try:
            raw_records = await self._fetch_all_pages("/cnep", cnpj_digits)
            records = []
            for raw in raw_records:
                try:
                    record = self._parse_cnep_record(raw)
                    records.append(record)
                except Exception as exc:
                    logger.warning(
                        "[SANCTIONS] Failed to parse CNEP record: %s", exc,
                    )
            logger.info(
                "[SANCTIONS] CNEP check for %s: %d record(s) found",
                cnpj_digits, len(records),
            )
            return records

        except Exception as exc:
            logger.warning(
                "[SANCTIONS] CNEP query failed for %s: %s", cnpj_digits, exc,
            )
            return []

    async def check_sanctions(self, cnpj: str) -> SanctionsResult:
        """
        Aggregate CEIS + CNEP results into a unified sanctions check.

        AC10: Returns SanctionsResult with ``is_sanctioned`` flag, merged
        sanctions list, and metadata.

        AC11: Uses 24-hour in-memory cache keyed by cleaned CNPJ digits.

        Args:
            cnpj: CNPJ in any format.

        Returns:
            SanctionsResult with aggregated data from both databases.
        """
        cnpj_digits = self._clean_cnpj(cnpj)

        # --- AC11: Check cache ---
        cached = self._cache.get(cnpj_digits)
        if cached is not None:
            result, cached_at = cached
            if (time.monotonic() - cached_at) < self.CACHE_TTL_SECONDS:
                logger.debug(
                    "[SANCTIONS] Cache hit for %s (age=%.0fs)",
                    cnpj_digits,
                    time.monotonic() - cached_at,
                )
                # Return a copy with cache_hit flag set
                return SanctionsResult(
                    cnpj=result.cnpj,
                    is_sanctioned=result.is_sanctioned,
                    sanctions=result.sanctions,
                    checked_at=result.checked_at,
                    ceis_count=result.ceis_count,
                    cnep_count=result.cnep_count,
                    cache_hit=True,
                )
            else:
                # Expired entry -- remove it
                del self._cache[cnpj_digits]

        # --- Fetch from both APIs concurrently ---
        ceis_records, cnep_records = await asyncio.gather(
            self.check_ceis(cnpj_digits),
            self.check_cnep(cnpj_digits),
        )

        all_sanctions = ceis_records + cnep_records
        has_active = any(s.is_active for s in all_sanctions)

        result = SanctionsResult(
            cnpj=cnpj_digits,
            is_sanctioned=has_active,
            sanctions=all_sanctions,
            checked_at=datetime.now(timezone.utc),
            ceis_count=len(ceis_records),
            cnep_count=len(cnep_records),
            cache_hit=False,
        )

        # --- AC11: Store in cache ---
        self._cache[cnpj_digits] = (result, time.monotonic())

        logger.info(
            "[SANCTIONS] Sanctions check for %s: sanctioned=%s "
            "(CEIS=%d, CNEP=%d)",
            cnpj_digits,
            result.is_sanctioned,
            result.ceis_count,
            result.cnep_count,
        )

        return result

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def invalidate_cache(self, cnpj: Optional[str] = None) -> None:
        """
        Invalidate cached sanctions results.

        Args:
            cnpj: If provided, only invalidate that CNPJ. Otherwise clear all.
        """
        if cnpj is not None:
            cnpj_digits = self._clean_cnpj(cnpj)
            self._cache.pop(cnpj_digits, None)
            logger.debug("[SANCTIONS] Cache invalidated for %s", cnpj_digits)
        else:
            self._cache.clear()
            logger.debug("[SANCTIONS] Cache fully cleared")

    @property
    def cache_size(self) -> int:
        """Return the number of entries currently in cache."""
        return len(self._cache)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            logger.debug(
                "[SANCTIONS] Client closed. Total requests: %d",
                self._request_count,
            )
        self._client = None

    async def __aenter__(self) -> "SanctionsChecker":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
