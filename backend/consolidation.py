"""Multi-source consolidation service.

Orchestrates parallel fetching from multiple procurement sources,
deduplicates results, and returns consolidated data in legacy format
compatible with the existing filter/excel/llm pipeline.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

from clients.base import SourceAdapter, SourceStatus, UnifiedProcurement
from source_config.sources import source_health_registry

logger = logging.getLogger(__name__)


@dataclass
class SourceResult:
    """Result metrics from a single source fetch."""

    source_code: str
    record_count: int
    duration_ms: int
    error: Optional[str] = None
    status: str = "success"  # "success" | "error" | "timeout" | "skipped" | "disabled"


@dataclass
class ConsolidationResult:
    """Result of consolidated multi-source fetch."""

    records: List[Dict[str, Any]]  # Legacy format (already converted)
    total_before_dedup: int
    total_after_dedup: int
    duplicates_removed: int
    source_results: List[SourceResult]
    elapsed_ms: int
    is_partial: bool = False
    degradation_reason: Optional[str] = None


class AllSourcesFailedError(Exception):
    """Raised when all sources fail and fail_on_all_errors is True."""

    def __init__(self, source_errors: Dict[str, str]):
        self.source_errors = source_errors
        msg = "; ".join(f"{k}: {v}" for k, v in source_errors.items())
        super().__init__(f"All sources failed: {msg}")


class ConsolidationService:
    """
    Orchestrates parallel fetching from multiple procurement sources.

    Features:
    - Parallel fetch via asyncio.gather
    - Per-source and global timeouts
    - Deduplication by dedup_key (keeps highest-priority source)
    - Automatic conversion to legacy format
    - Graceful degradation (partial results on partial failure)
    - Progress callback support
    """

    # Timeout used for alternative sources when PNCP is degraded/down (AC13)
    FAILOVER_TIMEOUT_PER_SOURCE = 40
    # Global timeout when PNCP is degraded (AC17)
    DEGRADED_GLOBAL_TIMEOUT = 90
    # Timeout for ComprasGov last-resort fallback (AC15)
    FALLBACK_TIMEOUT = 40

    def __init__(
        self,
        adapters: Dict[str, SourceAdapter],
        timeout_per_source: int = 25,
        timeout_global: int = 60,
        fail_on_all_errors: bool = True,
        fallback_adapter: Optional[SourceAdapter] = None,
    ):
        """
        Initialize ConsolidationService.

        Args:
            adapters: Dict mapping source code to SourceAdapter instance
            timeout_per_source: Max seconds per source fetch
            timeout_global: Max seconds for entire consolidation
            fail_on_all_errors: Raise if all sources fail
            fallback_adapter: Optional ComprasGov adapter used as last-resort
                fallback when all other sources fail (AC15). This adapter is
                tried even if ComprasGov is disabled in env config.
        """
        self._adapters = adapters
        self._timeout_per_source = timeout_per_source
        self._timeout_global = timeout_global
        self._fail_on_all_errors = fail_on_all_errors
        self._fallback_adapter = fallback_adapter

    async def fetch_all(
        self,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]] = None,
        on_source_complete: Optional[Callable] = None,
    ) -> ConsolidationResult:
        """
        Fetch from all enabled sources in parallel, deduplicate, and return.

        Implements multi-source orchestration with:
        - Health-aware timeout adjustments (AC13, AC17)
        - Degraded mode with partial results (AC14)
        - ComprasGov last-resort fallback (AC15)
        - Detailed per-source status reporting (AC16)

        Args:
            data_inicial: Start date YYYY-MM-DD
            data_final: End date YYYY-MM-DD
            ufs: Optional set of UF codes
            on_source_complete: Callback(source_code, count, error) per source

        Returns:
            ConsolidationResult with deduplicated records in legacy format

        Raises:
            AllSourcesFailedError: If all sources fail (including fallback)
                and fail_on_all_errors=True
        """
        start_time = time.time()

        if not self._adapters:
            return ConsolidationResult(
                records=[],
                total_before_dedup=0,
                total_after_dedup=0,
                duplicates_removed=0,
                source_results=[],
                elapsed_ms=0,
            )

        # AC12/AC17: Check PNCP health to determine effective timeouts
        pncp_status = source_health_registry.get_status("PNCP")
        pncp_is_degraded = pncp_status in ("degraded", "down")

        effective_global_timeout = self._timeout_global
        if pncp_is_degraded:
            effective_global_timeout = max(
                self._timeout_global, self.DEGRADED_GLOBAL_TIMEOUT
            )
            logger.info(
                f"[CONSOLIDATION] PNCP is {pncp_status} — "
                f"global timeout increased to {effective_global_timeout}s"
            )

        # Build per-source fetch tasks with health-aware timeouts (AC13)
        tasks = {}
        source_timeouts: Dict[str, int] = {}
        for code, adapter in self._adapters.items():
            tasks[code] = self._fetch_source(
                adapter, data_inicial, data_final, ufs
            )
            if pncp_is_degraded and code != "PNCP":
                # AC13: Give alternative sources more time when PNCP is degraded
                source_timeouts[code] = self.FAILOVER_TIMEOUT_PER_SOURCE
            else:
                source_timeouts[code] = self._timeout_per_source

        # Execute all sources in parallel with global timeout
        source_results_map: Dict[str, dict] = {}
        try:
            results = await asyncio.wait_for(
                asyncio.gather(
                    *[
                        self._wrap_source(code, task, timeout=source_timeouts[code])
                        for code, task in tasks.items()
                    ],
                    return_exceptions=True,
                ),
                timeout=effective_global_timeout,
            )
            for result in results:
                if isinstance(result, dict):
                    code = result["code"]
                    source_results_map[code] = result
        except asyncio.TimeoutError:
            logger.warning(
                f"[CONSOLIDATION] Global timeout ({effective_global_timeout}s) reached"
            )

        # Collect results and metrics, update health registry (AC12)
        all_records: List[UnifiedProcurement] = []
        source_results: List[SourceResult] = []
        source_errors: Dict[str, str] = {}
        failed_sources: List[str] = []

        for code in self._adapters:
            result = source_results_map.get(code)
            if result and result.get("status") == "success":
                records = result["records"]
                all_records.extend(records)
                source_health_registry.record_success(code)
                sr = SourceResult(
                    source_code=code,
                    record_count=len(records),
                    duration_ms=result["duration_ms"],
                    status="success",
                )
                source_results.append(sr)
                if on_source_complete:
                    try:
                        on_source_complete(code, len(records), None)
                    except Exception:
                        pass
            else:
                error_msg = "Global timeout"
                status = "timeout"
                if result:
                    error_msg = result.get("error", "Unknown error")
                    status = result.get("status", "error")
                source_errors[code] = error_msg
                failed_sources.append(code)
                source_health_registry.record_failure(code)
                sr = SourceResult(
                    source_code=code,
                    record_count=0,
                    duration_ms=result["duration_ms"] if result else 0,
                    error=error_msg,
                    status=status,
                )
                source_results.append(sr)
                if on_source_complete:
                    try:
                        on_source_complete(code, 0, error_msg)
                    except Exception:
                        pass

        # AC15: ComprasGov last-resort fallback when ALL sources fail
        fallback_used = False
        if not all_records and source_errors and self._fallback_adapter is not None:
            fallback_code = self._fallback_adapter.code
            # Only attempt fallback if it wasn't already tried as a primary source
            already_tried = fallback_code in self._adapters
            if not already_tried:
                logger.info(
                    f"[CONSOLIDATION] All sources failed — attempting {fallback_code} "
                    f"as last-resort fallback (timeout={self.FALLBACK_TIMEOUT}s)"
                )
                fallback_result = await self._wrap_source(
                    fallback_code,
                    self._fetch_source(
                        self._fallback_adapter, data_inicial, data_final, ufs
                    ),
                    timeout=self.FALLBACK_TIMEOUT,
                )
                if fallback_result.get("status") == "success":
                    fb_records = fallback_result["records"]
                    all_records.extend(fb_records)
                    source_health_registry.record_success(fallback_code)
                    sr = SourceResult(
                        source_code=fallback_code,
                        record_count=len(fb_records),
                        duration_ms=fallback_result["duration_ms"],
                        status="success",
                    )
                    source_results.append(sr)
                    fallback_used = True
                    # Clear source_errors partially since we got data
                    logger.info(
                        f"[CONSOLIDATION] Fallback {fallback_code} returned "
                        f"{len(fb_records)} records"
                    )
                    if on_source_complete:
                        try:
                            on_source_complete(
                                fallback_code, len(fb_records), None
                            )
                        except Exception:
                            pass
                else:
                    fb_error = fallback_result.get("error", "Unknown error")
                    source_errors[fallback_code] = fb_error
                    source_health_registry.record_failure(fallback_code)
                    sr = SourceResult(
                        source_code=fallback_code,
                        record_count=0,
                        duration_ms=fallback_result.get("duration_ms", 0),
                        error=fb_error,
                        status=fallback_result.get("status", "error"),
                    )
                    source_results.append(sr)
                    logger.warning(
                        f"[CONSOLIDATION] Fallback {fallback_code} also failed: "
                        f"{fb_error}"
                    )

        # AC14: Determine partial/degradation state
        has_data = len(all_records) > 0
        has_failures = len(failed_sources) > 0
        is_partial = has_data and has_failures
        degradation_reason: Optional[str] = None

        if is_partial:
            degradation_reason = (
                f"Partial results: sources failed: {', '.join(failed_sources)}"
            )
            logger.warning(
                f"[CONSOLIDATION] Degraded mode — {degradation_reason}"
            )

        # AC14: If 0 sources return data, return explicit error (not "0 results")
        if not has_data and source_errors and self._fail_on_all_errors:
            raise AllSourcesFailedError(source_errors)

        # Deduplicate
        total_before = len(all_records)
        deduped = self._deduplicate(all_records)
        total_after = len(deduped)

        # Convert to legacy format
        legacy_records = [r.to_legacy_format() for r in deduped]

        elapsed = int((time.time() - start_time) * 1000)

        logger.info(
            f"[CONSOLIDATION] Complete: {total_before} raw -> {total_after} deduped "
            f"({total_before - total_after} duplicates removed) in {elapsed}ms"
            f"{' [PARTIAL]' if is_partial else ''}"
            f"{' [FALLBACK]' if fallback_used else ''}"
        )

        return ConsolidationResult(
            records=legacy_records,
            total_before_dedup=total_before,
            total_after_dedup=total_after,
            duplicates_removed=total_before - total_after,
            source_results=source_results,
            elapsed_ms=elapsed,
            is_partial=is_partial,
            degradation_reason=degradation_reason,
        )

    async def _fetch_source(
        self,
        adapter: SourceAdapter,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]],
    ) -> List[UnifiedProcurement]:
        """Fetch all records from a single source."""
        records = []
        async for record in adapter.fetch(data_inicial, data_final, ufs):
            records.append(record)
        return records

    async def _wrap_source(
        self, code: str, coro, timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Wrap a source fetch with timeout and error handling.

        Args:
            code: Source identifier for logging/tracking
            coro: Coroutine to execute (the actual fetch)
            timeout: Per-source timeout in seconds. Defaults to
                self._timeout_per_source if not provided.
        """
        effective_timeout = timeout if timeout is not None else self._timeout_per_source
        start = time.time()
        try:
            records = await asyncio.wait_for(coro, timeout=effective_timeout)
            duration = int((time.time() - start) * 1000)
            logger.info(
                f"[CONSOLIDATION] {code}: {len(records)} records in {duration}ms"
            )
            return {
                "code": code,
                "status": "success",
                "records": records,
                "duration_ms": duration,
            }
        except asyncio.TimeoutError:
            duration = int((time.time() - start) * 1000)
            logger.warning(f"[CONSOLIDATION] {code}: timeout after {duration}ms")
            return {
                "code": code,
                "status": "timeout",
                "records": [],
                "duration_ms": duration,
                "error": f"Timeout after {effective_timeout}s",
            }
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            logger.error(f"[CONSOLIDATION] {code}: error after {duration}ms - {e}")
            return {
                "code": code,
                "status": "error",
                "records": [],
                "duration_ms": duration,
                "error": str(e),
            }

    def _deduplicate(
        self, records: List[UnifiedProcurement]
    ) -> List[UnifiedProcurement]:
        """
        Deduplicate records by dedup_key, keeping the highest-priority source.

        Priority is determined by SourceMetadata.priority (lower = higher priority).
        """
        if not records:
            return []

        # Source priority lookup (lower number = higher priority)
        source_priority = {}
        for code, adapter in self._adapters.items():
            source_priority[adapter.code] = adapter.metadata.priority

        # Group by dedup_key, keep best priority
        seen: Dict[str, UnifiedProcurement] = {}
        for record in records:
            key = record.dedup_key
            if not key:
                # No dedup key - always include
                seen[f"_nokey_{id(record)}"] = record
                continue

            existing = seen.get(key)
            if existing is None:
                seen[key] = record
            else:
                # Keep the one from higher priority source (lower number)
                existing_priority = source_priority.get(existing.source_name, 999)
                new_priority = source_priority.get(record.source_name, 999)
                if new_priority < existing_priority:
                    seen[key] = record

        return list(seen.values())

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Run health checks on all adapters in parallel.

        Returns:
            Dict mapping source code to health status info
        """
        results = {}

        async def check_one(code: str, adapter: SourceAdapter):
            start = time.time()
            try:
                status = await asyncio.wait_for(adapter.health_check(), timeout=5.0)
                duration = int((time.time() - start) * 1000)
                return code, {
                    "status": status.value,
                    "response_ms": duration,
                    "priority": adapter.metadata.priority,
                }
            except asyncio.TimeoutError:
                return code, {
                    "status": SourceStatus.UNAVAILABLE.value,
                    "response_ms": 5000,
                    "priority": adapter.metadata.priority,
                }
            except Exception:
                return code, {
                    "status": SourceStatus.UNAVAILABLE.value,
                    "response_ms": int((time.time() - start) * 1000),
                    "priority": adapter.metadata.priority,
                }

        checks = [check_one(code, adapter) for code, adapter in self._adapters.items()]
        done = await asyncio.gather(*checks, return_exceptions=True)

        for item in done:
            if isinstance(item, tuple):
                code, info = item
                results[code] = info

        return results

    async def close(self) -> None:
        """Close all adapters."""
        for adapter in self._adapters.values():
            try:
                await adapter.close()
            except Exception:
                pass
