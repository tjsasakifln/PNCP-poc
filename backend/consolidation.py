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

from utils.error_reporting import report_error  # GTM-RESILIENCE-E02: centralized error emission
from clients.base import SourceAdapter, SourceStatus, UnifiedProcurement, SourceError
from source_config.sources import source_health_registry
from metrics import FETCH_DURATION, API_ERRORS
from telemetry import get_tracer, optional_span
from bulkhead import SourceBulkhead, get_bulkhead

logger = logging.getLogger(__name__)

# F-02 AC13: Tracer for per-source fetch spans
_tracer = get_tracer("consolidation")


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
    # GTM-STAB-003 AC3: UF tracking for early return
    ufs_completed: List[str] = field(default_factory=list)
    ufs_pending: List[str] = field(default_factory=list)


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

    # GTM-STAB: Failover timeout reduced from 120→80 — tighter per-source budget
    FAILOVER_TIMEOUT_PER_SOURCE = 80
    # STORY-271 AC2: Degraded global timeout 110→100 — 15s buffer before GUNICORN_TIMEOUT=115s
    DEGRADED_GLOBAL_TIMEOUT = 100
    # Timeout for ComprasGov last-resort fallback (AC15)
    FALLBACK_TIMEOUT = 40

    def __init__(
        self,
        adapters: Dict[str, SourceAdapter],
        timeout_per_source: int = 25,
        timeout_global: int = 60,
        fail_on_all_errors: bool = True,
        fallback_adapter: Optional[SourceAdapter] = None,
        bulkheads: Optional[Dict[str, SourceBulkhead]] = None,
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
            bulkheads: Optional dict mapping source code to SourceBulkhead.
                When provided, each source fetch is wrapped with the
                bulkhead's semaphore for concurrency isolation (STORY-296).
                Falls back to global registry if not provided.
        """
        # GTM-FIX-024 T5: Fail-fast contract validation
        required_attrs = ("code", "metadata", "fetch", "health_check", "close")
        for adapter_key, adapter in adapters.items():
            missing = [attr for attr in required_attrs if not hasattr(adapter, attr)]
            if missing:
                raise TypeError(
                    f"Adapter '{adapter_key}' ({type(adapter).__name__}) missing required "
                    f"attributes: {', '.join(missing)}. Must implement SourceAdapter interface."
                )
        if fallback_adapter is not None:
            missing = [attr for attr in required_attrs if not hasattr(fallback_adapter, attr)]
            if missing:
                raise TypeError(
                    f"Fallback adapter ({type(fallback_adapter).__name__}) missing required "
                    f"attributes: {', '.join(missing)}. Must implement SourceAdapter interface."
                )

        self._adapters = adapters
        self._timeout_per_source = timeout_per_source
        self._timeout_global = timeout_global
        self._fail_on_all_errors = fail_on_all_errors
        self._fallback_adapter = fallback_adapter
        # STORY-296: Per-source bulkheads for concurrency isolation
        self._bulkheads = bulkheads or {}
        # GTM-STAB-003 AC3: Exposes last effective global timeout for testing
        self._last_effective_global_timeout: Optional[int] = None

        # GTM-FIX-029 AC10: Warn if per-source timeout is dangerously close to global
        if timeout_per_source > timeout_global * 0.8:
            logger.warning(
                f"Timeout near-inversion: timeout_per_source ({timeout_per_source}s) > "
                f"80% of timeout_global ({timeout_global}s). Sources may starve each other."
            )

    async def fetch_all(
        self,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]] = None,
        on_source_complete: Optional[Callable] = None,
        on_early_return: Optional[Callable] = None,
    ) -> ConsolidationResult:
        """
        Fetch from all enabled sources in parallel, deduplicate, and return.

        Implements multi-source orchestration with:
        - Health-aware timeout adjustments (AC13, AC17)
        - Degraded mode with partial results (AC14)
        - ComprasGov last-resort fallback (AC15)
        - Detailed per-source status reporting (AC16)
        - GTM-STAB-003 AC3: Early return when >=80% UFs responded and elapsed >80s

        Args:
            data_inicial: Start date YYYY-MM-DD
            data_final: End date YYYY-MM-DD
            ufs: Optional set of UF codes
            on_source_complete: Callback(source_code, count, error) per source
            on_early_return: Optional async callback(ufs_completed, ufs_pending)
                called when early return triggers (e.g. to emit progress event)

        Returns:
            ConsolidationResult with deduplicated records in legacy format

        Raises:
            AllSourcesFailedError: If all sources fail (including fallback)
                and fail_on_all_errors=True
        """
        start_time = time.time()
        requested_ufs = set(ufs) if ufs else set()

        # CRIT-004 AC12: Log search_id from ContextVar for correlation
        from middleware import search_id_var
        _search_id = search_id_var.get("-")
        logger.info(f"Consolidation started [search={_search_id}] sources={list(self._adapters.keys())}")

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
            logger.debug(
                f"[CONSOLIDATION] PNCP is {pncp_status} — "
                f"global timeout increased to {effective_global_timeout}s"
            )
        # GTM-STAB-003 AC3: Store for testability
        self._last_effective_global_timeout = effective_global_timeout

        # Build per-source timeouts with health-aware adjustments (AC13)
        source_timeouts: Dict[str, int] = {}
        for code in self._adapters:
            if pncp_is_degraded and code != "PNCP":
                # AC13: Give alternative sources more time when PNCP is degraded
                source_timeouts[code] = self.FAILOVER_TIMEOUT_PER_SOURCE
            else:
                source_timeouts[code] = self._timeout_per_source

        # GTM-STAB-003 AC3: Early return config
        from config import EARLY_RETURN_THRESHOLD_PCT, EARLY_RETURN_TIME_S

        # Shared partial collectors per source — used for early return UF inspection
        source_partial_collectors: Dict[str, List[UnifiedProcurement]] = {
            code: [] for code in self._adapters
        }

        # Execute all sources in parallel with global timeout
        source_results_map: Dict[str, dict] = {}
        early_return_triggered = False

        # Create named tasks so we can track which source each task belongs to
        source_tasks: Dict[str, asyncio.Task] = {}
        for code, adapter in self._adapters.items():
            task = asyncio.create_task(
                self._wrap_source(
                    code, adapter,
                    data_inicial=data_inicial,
                    data_final=data_final,
                    ufs=ufs,
                    timeout=source_timeouts[code],
                    partial_collector_out=source_partial_collectors[code],
                ),
                name=f"source_{code}",
            )
            source_tasks[code] = task

        # Use asyncio.wait with periodic early return checks instead of gather
        pending_tasks = set(source_tasks.values())
        deadline = start_time + effective_global_timeout

        while pending_tasks:
            remaining_time = deadline - time.time()
            if remaining_time <= 0:
                # Global timeout — cancel remaining and collect partial
                logger.warning(
                    f"[CONSOLIDATION] Global timeout ({effective_global_timeout}s) reached — collecting partial results"
                )
                for task in pending_tasks:
                    task.cancel()
                # Wait briefly for cancellation to propagate
                await asyncio.gather(*pending_tasks, return_exceptions=True)
                break

            # Wait for at least one task to complete, or check every 2s for early return
            check_interval = min(2.0, remaining_time)
            done, pending_tasks = await asyncio.wait(
                pending_tasks, timeout=check_interval, return_when=asyncio.FIRST_COMPLETED,
            )

            # Collect results from completed tasks
            for task in done:
                try:
                    result = task.result()
                except (asyncio.CancelledError, Exception):
                    result = None
                if isinstance(result, dict):
                    code = result["code"]
                    source_results_map[code] = result
                elif result is not None:
                    logger.warning(
                        f"[CONSOLIDATION] Unexpected non-dict result from task: "
                        f"type={type(result).__name__} value={str(result)[:200]}"
                    )

            # GTM-STAB-003 AC3: Check early return condition
            if pending_tasks and requested_ufs and not early_return_triggered:
                elapsed_s = time.time() - start_time
                if elapsed_s >= EARLY_RETURN_TIME_S:
                    # Count UFs seen in all partial collectors so far
                    seen_ufs = set()
                    for collector in source_partial_collectors.values():
                        for record in collector:
                            uf = getattr(record, "uf", None) or ""
                            if uf:
                                seen_ufs.add(uf)
                    # Also count UFs from completed source results
                    for sr_data in source_results_map.values():
                        for record in sr_data.get("records", []):
                            uf = getattr(record, "uf", None) or ""
                            if uf:
                                seen_ufs.add(uf)

                    completed_ufs = seen_ufs & requested_ufs
                    total_requested = len(requested_ufs)
                    completion_pct = len(completed_ufs) / total_requested if total_requested > 0 else 0

                    if completion_pct >= EARLY_RETURN_THRESHOLD_PCT and completion_pct < 1.0:
                        pending_uf_list = sorted(requested_ufs - completed_ufs)
                        completed_uf_list = sorted(completed_ufs)
                        early_return_triggered = True

                        logger.info(
                            "early_return_triggered",
                            extra={
                                "ufs_completed": completed_uf_list,
                                "ufs_pending": pending_uf_list,
                                "elapsed_s": round(elapsed_s, 1),
                                "completion_pct": round(completion_pct * 100, 1),
                            },
                        )

                        # Cancel remaining tasks
                        for task in pending_tasks:
                            task.cancel()
                        # Wait briefly for cancellation to propagate
                        await asyncio.gather(*pending_tasks, return_exceptions=True)

                        # Emit progress event if callback provided
                        if on_early_return:
                            try:
                                cb_result = on_early_return(completed_uf_list, pending_uf_list)
                                if asyncio.iscoroutine(cb_result):
                                    await cb_result
                            except Exception:
                                pass
                        break

        # For any source without a result (timed out or cancelled), mark as timeout
        for code in self._adapters:
            if code not in source_results_map:
                source_results_map[code] = {
                    "code": code,
                    "records": [],
                    "duration_ms": int((time.time() - start_time) * 1000),
                    "status": "timeout",
                    "error": (
                        f"Early return (elapsed {time.time() - start_time:.0f}s)"
                        if early_return_triggered
                        else f"Global timeout ({effective_global_timeout}s)"
                    ),
                }

        # Collect results and metrics, update health registry (AC12)
        all_records: List[UnifiedProcurement] = []
        source_results: List[SourceResult] = []
        source_errors: Dict[str, str] = {}
        failed_sources: List[str] = []

        for code in self._adapters:
            result = source_results_map.get(code)
            result_status = result.get("status") if result else None
            has_records = result_status in ("success", "partial")

            if result and has_records:
                records = result["records"]
                all_records.extend(records)
                if result_status == "success":
                    source_health_registry.record_success(code)
                else:
                    # "partial" — some data but source didn't complete
                    source_health_registry.record_failure(code)
                    failed_sources.append(code)
                    source_errors[code] = result.get("error", "Partial timeout")
                sr = SourceResult(
                    source_code=code,
                    record_count=len(records),
                    duration_ms=result["duration_ms"],
                    error=result.get("error"),
                    status=result_status,
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
            fallback_code = getattr(self._fallback_adapter, "code", "unknown_fallback")
            # Only attempt fallback if it wasn't already tried as a primary source
            already_tried = fallback_code in self._adapters
            if not already_tried:
                logger.debug(
                    f"[CONSOLIDATION] All sources failed — attempting {fallback_code} "
                    f"as last-resort fallback (timeout={self.FALLBACK_TIMEOUT}s)"
                )
                fallback_result = await self._wrap_source(
                    fallback_code,
                    self._fallback_adapter,
                    data_inicial=data_inicial,
                    data_final=data_final,
                    ufs=ufs,
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
                    logger.debug(
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

        # GTM-STAB-003 AC3: Early return also marks as partial
        if early_return_triggered and has_data:
            is_partial = True

        degradation_reason: Optional[str] = None

        if early_return_triggered:
            degradation_reason = "early_return_timeout"
        elif is_partial:
            degradation_reason = (
                f"Partial results: sources failed: {', '.join(failed_sources)}"
            )

        if is_partial:
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

        # GTM-STAB-003 AC3: Build UF completion lists from collected records
        seen_ufs_in_results = set()
        for record in all_records:
            uf = getattr(record, "uf", None) or ""
            if uf:
                seen_ufs_in_results.add(uf)
        completed_ufs_list = sorted(seen_ufs_in_results & requested_ufs) if requested_ufs else sorted(seen_ufs_in_results)
        pending_ufs_list = sorted(requested_ufs - seen_ufs_in_results) if requested_ufs else []

        logger.info(
            f"[CONSOLIDATION] Complete: {total_before} raw -> {total_after} deduped "
            f"({total_before - total_after} duplicates removed) in {elapsed}ms"
            f"{' [PARTIAL]' if is_partial else ''}"
            f"{' [EARLY_RETURN]' if early_return_triggered else ''}"
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
            ufs_completed=completed_ufs_list,
            ufs_pending=pending_ufs_list,
        )

    async def _fetch_source(
        self,
        adapter: SourceAdapter,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]],
        partial_collector: Optional[List] = None,
    ) -> List[UnifiedProcurement]:
        """Fetch all records from a single source.

        Args:
            adapter: Source adapter to fetch from.
            data_inicial: Start date.
            data_final: End date.
            ufs: Optional UF filter.
            partial_collector: If provided, records are appended here as they
                arrive so that ``_wrap_source`` can salvage them on timeout.
        """
        records = [] if partial_collector is None else partial_collector
        async for record in adapter.fetch(data_inicial, data_final, ufs):
            records.append(record)
        return records

    async def _wrap_source(
        self, code: str, adapter: SourceAdapter,
        data_inicial: str, data_final: str,
        ufs: Optional[Set[str]] = None,
        timeout: Optional[int] = None,
        partial_collector_out: Optional[List] = None,
    ) -> Dict[str, Any]:
        """
        Wrap a source fetch with timeout and error handling.

        Preserves partial results on timeout: records that were already
        yielded by the adapter before the timeout fires are returned
        with status ``"partial"`` instead of being discarded.

        Args:
            code: Source identifier for logging/tracking.
            adapter: The source adapter to fetch from.
            data_inicial: Start date.
            data_final: End date.
            ufs: Optional UF filter set.
            timeout: Per-source timeout in seconds. Defaults to
                self._timeout_per_source if not provided.
            partial_collector_out: Optional external list that receives records
                as they arrive. Used by early return logic to inspect UF progress
                from in-progress sources (GTM-STAB-003 AC3).
        """
        effective_timeout = timeout if timeout is not None else self._timeout_per_source
        start = time.time()
        # Shared list: records accumulate here as the generator yields them.
        # On timeout we can still read whatever was collected.
        # GTM-STAB-003 AC3: If an external collector is provided, use it so
        # the early return logic can inspect records while fetch is in progress.
        partial_records: List[UnifiedProcurement] = (
            partial_collector_out if partial_collector_out is not None else []
        )
        # F-02 AC13: Sub-span per source (fetch.pncp, fetch.pcp, etc.)
        source_span_name = f"fetch.{code.lower()}"
        with optional_span(_tracer, source_span_name, {"source.code": code}) as src_span:
            return await self._wrap_source_inner(
                code, adapter, data_inicial, data_final, ufs,
                effective_timeout, start, partial_records, src_span,
            )

    async def _wrap_source_inner(
        self, code, adapter, data_inicial, data_final, ufs,
        effective_timeout, start, partial_records, src_span,
    ):
        try:
            fetch_coro = self._fetch_source(
                adapter, data_inicial, data_final, ufs,
                partial_collector=partial_records,
            )
            # STORY-296: Wrap with bulkhead semaphore if available
            bulkhead = self._bulkheads.get(code) or get_bulkhead(code)
            if bulkhead:
                fetch_coro = bulkhead.execute(fetch_coro)
            await asyncio.wait_for(fetch_coro, timeout=effective_timeout)
            duration = int((time.time() - start) * 1000)
            FETCH_DURATION.labels(source=code).observe(duration / 1000.0)
            src_span.set_attribute("duration_ms", duration)
            src_span.set_attribute("items_out", len(partial_records))
            src_span.set_attribute("status", "success")
            logger.debug(
                f"[CONSOLIDATION] {code}: {len(partial_records)} records in {duration}ms"
            )
            return {
                "code": code,
                "status": "success",
                "records": partial_records,
                "duration_ms": duration,
            }
        except asyncio.TimeoutError:
            duration = int((time.time() - start) * 1000)
            FETCH_DURATION.labels(source=code).observe(duration / 1000.0)
            API_ERRORS.labels(source=code, error_type="timeout").inc()
            salvaged = len(partial_records)
            if salvaged > 0:
                logger.warning(
                    f"[CONSOLIDATION] {code}: timeout after {duration}ms — "
                    f"salvaged {salvaged} partial records"
                )
                return {
                    "code": code,
                    "status": "partial",
                    "records": partial_records,
                    "duration_ms": duration,
                    "error": f"Timeout after {effective_timeout}s (salvaged {salvaged} records)",
                }
            else:
                logger.warning(
                    f"[CONSOLIDATION] {code}: timeout after {duration}ms — no records"
                )
                return {
                    "code": code,
                    "status": "timeout",
                    "records": [],
                    "duration_ms": duration,
                    "error": f"Timeout after {effective_timeout}s",
                }
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            FETCH_DURATION.labels(source=code).observe(duration / 1000.0)
            # Classify error type for metrics
            _err_type = "unknown"
            if "429" in str(e):
                _err_type = "429"
            elif "422" in str(e):
                _err_type = "422"
            elif "500" in str(e) or "502" in str(e) or "503" in str(e) or "504" in str(e):
                _err_type = "500"
            elif "timeout" in str(e).lower() or "Timeout" in type(e).__name__:
                _err_type = "timeout"
            elif "connect" in str(e).lower() or "Connection" in type(e).__name__:
                _err_type = "connection"
            API_ERRORS.labels(source=code, error_type=_err_type).inc()
            salvaged = len(partial_records)

            # GTM-RESILIENCE-E02: centralized reporting (no double stdout+Sentry)
            source_code = code
            if isinstance(e, SourceError):
                source_code = e.source_code

            if salvaged > 0:
                report_error(
                    e, f"[CONSOLIDATION] {code}: PARTIAL after {duration}ms — salvaged {salvaged} records",
                    expected=True, tags={"data_source": source_code}, log=logger,
                )
                return {
                    "code": code,
                    "status": "partial",
                    "records": partial_records,
                    "duration_ms": duration,
                    "error": f"{e} (salvaged {salvaged} records)",
                }
            report_error(
                e, f"[CONSOLIDATION] {code}: FAILED after {duration}ms",
                expected=True, tags={"data_source": source_code}, log=logger,
            )
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
            adapter_code = getattr(adapter, "code", code)
            adapter_meta = getattr(adapter, "metadata", None)
            if adapter_meta is not None:
                source_priority[adapter_code] = adapter_meta.priority

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
                # AC17: Log warning if same procurement has >5% value discrepancy
                if (
                    existing.source_name != record.source_name
                    and existing.valor_estimado > 0
                    and record.valor_estimado > 0
                ):
                    diff_pct = abs(existing.valor_estimado - record.valor_estimado) / max(
                        existing.valor_estimado, record.valor_estimado
                    )
                    if diff_pct > 0.05:
                        logger.warning(
                            f"[CONSOLIDATION] Value discrepancy >5% for dedup_key={key}: "
                            f"{existing.source_name}=R${existing.valor_estimado:,.2f} vs "
                            f"{record.source_name}=R${record.valor_estimado:,.2f} "
                            f"(diff={diff_pct:.1%})"
                        )

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
        """Close all adapters including fallback (STORY-257A AC12)."""
        for adapter in self._adapters.values():
            try:
                await adapter.close()
            except Exception:
                pass
        # AC12: Close fallback adapter to prevent HTTP client leak
        if self._fallback_adapter is not None:
            try:
                await self._fallback_adapter.close()
            except Exception:
                pass
