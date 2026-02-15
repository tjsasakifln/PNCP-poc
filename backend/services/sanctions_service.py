"""
Unified Sanctions Service — aggregates CEIS + CNEP + TCU checks.

This service wraps the low-level SanctionsChecker to provide:
- Single-company check with CompanySanctionsReport
- Batch check with rate-limit-aware concurrency
- 24h TTL cache (via SanctionsChecker's built-in cache)
- Graceful degradation when Portal da Transparência is unavailable

STORY-256 AC1-AC5.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Dict, List, Optional

from clients.sanctions import (
    SanctionsChecker,
    SanctionRecord,
    SanctionsResult,
    SanctionsAPIError,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models (AC1)
# ---------------------------------------------------------------------------

SEVERITY_RANK = {
    "Inidoneidade": 3,
    "Impedimento": 2,
    "Suspensão": 1,
    "Suspensao": 1,
}


@dataclass
class CompanySanctionsReport:
    """Full sanctions report for a single company (AC2)."""

    cnpj: str
    company_name: Optional[str]
    checked_at: datetime
    status: str  # "clean" | "sanctioned" | "unavailable"
    is_sanctioned: bool
    ceis_records: List[SanctionRecord]
    cnep_records: List[SanctionRecord]
    tcu_ineligible: bool  # Placeholder for future TCU integration
    total_active_sanctions: int
    most_severe_sanction: Optional[str]
    earliest_end_date: Optional[date]


@dataclass
class SanctionsSummary:
    """Lightweight sanctions summary for search results (AC11)."""

    is_clean: bool
    active_sanctions_count: int
    sanction_types: List[str]  # e.g. ["CEIS: Impedimento", "CNEP: Multa"]
    checked_at: datetime


# ---------------------------------------------------------------------------
# SanctionsService (AC1-AC5)
# ---------------------------------------------------------------------------


class SanctionsService:
    """
    High-level sanctions verification service.

    Wraps SanctionsChecker to provide:
    - CompanySanctionsReport for lead pipeline (AC2)
    - Batch checking with rate limiting (AC4)
    - Graceful degradation (AC5)

    Usage::

        service = SanctionsService()
        report = await service.check_company("12345678000100")
        if report.is_sanctioned:
            print(f"ALERT: {report.total_active_sanctions} active sanctions")

        # Batch
        reports = await service.check_companies(["12345678000100", "98765432000199"])

        # Cleanup
        await service.close()
    """

    # Max concurrent batch checks (respects 90 req/min via SanctionsChecker)
    BATCH_CONCURRENCY = 5

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> None:
        self._checker = SanctionsChecker(api_key=api_key, timeout=timeout)

    # ------------------------------------------------------------------
    # Single company check (AC2)
    # ------------------------------------------------------------------

    async def check_company(self, cnpj: str) -> CompanySanctionsReport:
        """
        Check a single company for CEIS + CNEP sanctions.

        AC2: Queries both databases in parallel, returns CompanySanctionsReport.
        AC3: Uses SanctionsChecker's 24h TTL cache.
        AC5: Returns status="unavailable" on API failure.

        Args:
            cnpj: CNPJ in any format.

        Returns:
            CompanySanctionsReport with aggregated data.
        """
        try:
            result: SanctionsResult = await self._checker.check_sanctions(cnpj)
        except (SanctionsAPIError, Exception) as exc:
            # AC5: Graceful degradation
            logger.warning(
                "[SANCTIONS_SERVICE] API unavailable for %s: %s", cnpj, exc,
            )
            return CompanySanctionsReport(
                cnpj=SanctionsChecker._clean_cnpj(cnpj),
                company_name=None,
                checked_at=datetime.now(timezone.utc),
                status="unavailable",
                is_sanctioned=False,
                ceis_records=[],
                cnep_records=[],
                tcu_ineligible=False,
                total_active_sanctions=0,
                most_severe_sanction=None,
                earliest_end_date=None,
            )

        return self._build_report(result)

    # ------------------------------------------------------------------
    # Batch check (AC4)
    # ------------------------------------------------------------------

    async def check_companies(
        self, cnpjs: List[str],
    ) -> Dict[str, CompanySanctionsReport]:
        """
        Check multiple companies with rate-limit-aware concurrency.

        AC4: Respects 90 req/min via semaphore-limited parallel checks.

        Args:
            cnpjs: List of CNPJs to check.

        Returns:
            Dict mapping cleaned CNPJ -> CompanySanctionsReport.
        """
        if not cnpjs:
            return {}

        semaphore = asyncio.Semaphore(self.BATCH_CONCURRENCY)
        results: Dict[str, CompanySanctionsReport] = {}

        async def _check_one(cnpj: str) -> None:
            async with semaphore:
                report = await self.check_company(cnpj)
                results[report.cnpj] = report

        tasks = [_check_one(cnpj) for cnpj in cnpjs]
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(
            "[SANCTIONS_SERVICE] Batch check complete: %d/%d CNPJs checked",
            len(results), len(cnpjs),
        )

        return results

    # ------------------------------------------------------------------
    # Summary builder (for search results — AC11)
    # ------------------------------------------------------------------

    @staticmethod
    def build_summary(report: CompanySanctionsReport) -> SanctionsSummary:
        """
        Build lightweight SanctionsSummary from full report.

        Used for search result enrichment (Track 3).
        """
        sanction_types = []
        for rec in report.ceis_records:
            if rec.is_active:
                label = f"CEIS: {rec.sanction_type}" if rec.sanction_type else "CEIS"
                if label not in sanction_types:
                    sanction_types.append(label)
        for rec in report.cnep_records:
            if rec.is_active:
                label = f"CNEP: {rec.sanction_type}" if rec.sanction_type else "CNEP"
                if label not in sanction_types:
                    sanction_types.append(label)

        return SanctionsSummary(
            is_clean=not report.is_sanctioned,
            active_sanctions_count=report.total_active_sanctions,
            sanction_types=sanction_types,
            checked_at=report.checked_at,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_report(self, result: SanctionsResult) -> CompanySanctionsReport:
        """Convert SanctionsResult to CompanySanctionsReport."""
        ceis = [s for s in result.sanctions if s.source == "CEIS"]
        cnep = [s for s in result.sanctions if s.source == "CNEP"]

        active_sanctions = [s for s in result.sanctions if s.is_active]
        total_active = len(active_sanctions)

        # Most severe sanction
        most_severe = None
        if active_sanctions:
            ranked = sorted(
                active_sanctions,
                key=lambda s: SEVERITY_RANK.get(s.sanction_type, 0),
                reverse=True,
            )
            most_severe = ranked[0].sanction_type

        # Earliest end date among active sanctions
        end_dates = [
            s.end_date for s in active_sanctions
            if s.end_date is not None
        ]
        earliest_end = min(end_dates) if end_dates else None

        # Company name from first record
        company_name = None
        if result.sanctions:
            company_name = result.sanctions[0].company_name or None

        status = "sanctioned" if result.is_sanctioned else "clean"

        return CompanySanctionsReport(
            cnpj=result.cnpj,
            company_name=company_name,
            checked_at=result.checked_at,
            status=status,
            is_sanctioned=result.is_sanctioned,
            ceis_records=ceis,
            cnep_records=cnep,
            tcu_ineligible=False,  # Future: TCU integration
            total_active_sanctions=total_active,
            most_severe_sanction=most_severe,
            earliest_end_date=earliest_end,
        )

    # ------------------------------------------------------------------
    # Cache delegation
    # ------------------------------------------------------------------

    def invalidate_cache(self, cnpj: Optional[str] = None) -> None:
        """Delegate cache invalidation to underlying checker."""
        self._checker.invalidate_cache(cnpj)

    @property
    def cache_size(self) -> int:
        """Return cache size from underlying checker."""
        return self._checker.cache_size

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close underlying HTTP client."""
        await self._checker.close()

    async def __aenter__(self) -> "SanctionsService":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
