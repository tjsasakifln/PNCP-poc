"""Multi-source consolidation service.

Orchestrates parallel fetching from multiple procurement sources,
deduplicates results, and returns consolidated data in legacy format
compatible with the existing filter/excel/llm pipeline.
"""

import asyncio
import hashlib
import logging
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

from utils.error_reporting import report_error  # GTM-RESILIENCE-E02: centralized error emission
from clients.base import SourceAdapter, SourceStatus, UnifiedProcurement, SourceError
from source_config.sources import source_health_registry
from metrics import FETCH_DURATION, API_ERRORS, SOURCES_BIDS_FETCHED, DEDUP_FIELDS_MERGED
from telemetry import get_tracer, optional_span
from bulkhead import BulkheadAcquireTimeoutError, SourceBulkhead, get_bulkhead

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
    status: str = "success"  # "success" | "error" | "timeout" | "skipped" | "disabled" | "degraded"
    # CRIT-053 AC3: Reason why source was skipped/degraded (e.g. "health_canary_timeout")
    skipped_reason: Optional[str] = None


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
        on_source_done: Optional[Callable] = None,
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
            on_source_done: STORY-295 AC1-AC8: Async callback(source_code, status,
                records_legacy, duration_ms, error) called when each source finishes.
                Enables progressive SSE delivery of partial results.

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

                    # STORY-295 AC1-AC8: Emit progressive results per source
                    if on_source_done:
                        try:
                            _status = result.get("status", "error")
                            _records = result.get("records", [])
                            # Convert records to legacy format for frontend consumption
                            _legacy = [r.to_legacy_format() for r in _records if hasattr(r, "to_legacy_format")]
                            _duration = result.get("duration_ms", 0)
                            _error = result.get("error")

                            cb_result = on_source_done(
                                code, _status, _legacy, _duration, _error,
                            )
                            if asyncio.iscoroutine(cb_result):
                                await cb_result
                        except Exception as cb_err:
                            logger.warning(
                                f"[CONSOLIDATION] on_source_done callback error for {code}: {cb_err}"
                            )
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
                            except Exception as e:
                                logger.warning(f"on_early_return callback error: {e}")
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
                    except Exception as e:
                        logger.warning(f"on_source_complete callback error for {code}: {e}")
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
                    except Exception as e:
                        logger.warning(f"on_source_complete callback error for {code}: {e}")

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
                        except Exception as e:
                            logger.warning(f"on_source_complete callback error for {fallback_code}: {e}")
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
            logger.info(
                f"[CONSOLIDATION] Degraded mode — {degradation_reason}"
            )

        # AC14: If 0 sources return data, return explicit error (not "0 results")
        if not has_data and source_errors and self._fail_on_all_errors:
            raise AllSourcesFailedError(source_errors)

        # Deduplicate: exact key match → fuzzy similarity → process-number
        total_before = len(all_records)
        deduped = self._deduplicate(all_records)
        deduped = self._deduplicate_fuzzy(deduped)
        deduped = self._deduplicate_by_process_number(deduped)
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

        # STORY-350 AC3: Increment per-source bids fetched counter
        for sr in source_results:
            if sr.record_count > 0:
                uf_counts: Dict[str, int] = {}
                for record in all_records:
                    src = getattr(record, "source_code", None) or getattr(record, "fonte", "")
                    if str(src).lower() == sr.source_code.lower():
                        uf = getattr(record, "uf", "") or "unknown"
                        uf_counts[uf] = uf_counts.get(uf, 0) + 1
                if uf_counts:
                    for uf, count in uf_counts.items():
                        SOURCES_BIDS_FETCHED.labels(source=sr.source_code, uf=uf).inc(count)
                else:
                    SOURCES_BIDS_FETCHED.labels(source=sr.source_code, uf="all").inc(sr.record_count)

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
        except BulkheadAcquireTimeoutError as bae:
            duration = int((time.time() - start) * 1000)
            FETCH_DURATION.labels(source=code).observe(duration / 1000.0)
            logger.warning(
                f"[CONSOLIDATION] {code}: bulkhead acquire timeout after {duration}ms — skipped"
            )
            return {
                "code": code,
                "status": "skipped",
                "records": [],
                "duration_ms": duration,
                "error": str(bae),
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
                logger.info(
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

    # HARDEN-006: Fields eligible for merge-enrichment from lower-priority duplicate
    _MERGE_FIELDS = ("valor_estimado", "modalidade", "orgao", "objeto")

    def _deduplicate(
        self, records: List[UnifiedProcurement]
    ) -> List[UnifiedProcurement]:
        """
        Deduplicate records by dedup_key with merge-enrichment.

        Priority is determined by SourceMetadata.priority (lower = higher priority).
        The winner record is enriched with non-empty fields from the loser when
        the winner's field is empty/zero (HARDEN-006).
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

        # Group by dedup_key, keep best priority + merge enrichment
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

                # Determine winner (higher priority = lower number) and loser
                existing_priority = source_priority.get(existing.source_name, 999)
                new_priority = source_priority.get(record.source_name, 999)
                if new_priority < existing_priority:
                    winner, loser = record, existing
                    seen[key] = record
                else:
                    winner, loser = existing, record

                # HARDEN-006 AC1/AC2: Merge empty fields from loser into winner
                self._merge_enrich(winner, loser, key)

        return list(seen.values())

    def _merge_enrich(
        self,
        winner: UnifiedProcurement,
        loser: UnifiedProcurement,
        dedup_key: str,
    ) -> None:
        """Enrich winner with non-empty fields from loser (HARDEN-006 AC1/AC2/AC3)."""
        for field_name in self._MERGE_FIELDS:
            winner_val = getattr(winner, field_name, None)
            loser_val = getattr(loser, field_name, None)

            # Check if winner field is empty/zero
            winner_empty = (
                winner_val is None
                or winner_val == ""
                or (isinstance(winner_val, (int, float)) and winner_val == 0)
            )
            # Check if loser field has data
            loser_has = (
                loser_val is not None
                and loser_val != ""
                and not (isinstance(loser_val, (int, float)) and loser_val == 0)
            )

            if winner_empty and loser_has:
                setattr(winner, field_name, loser_val)
                # AC3: Track which source filled the field
                winner.merged_from[field_name] = loser.source_name
                # AC4: Metric
                DEDUP_FIELDS_MERGED.labels(field=field_name).inc()
                logger.debug(
                    f"[DEDUP-MERGE] key={dedup_key} field={field_name} "
                    f"filled from {loser.source_name} (winner={winner.source_name})"
                )

    # --- Fuzzy dedup (ISSUE-027) ---

    # Portuguese stopwords irrelevant for tender object comparison
    _FUZZY_STOPWORDS = frozenset({
        "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
        "para", "por", "com", "e", "a", "o", "um", "uma", "ao", "pelo",
        "pela", "que", "se", "ou", "os", "as", "este", "esta", "essa",
    })

    @staticmethod
    def _tokenize_objeto(texto: str) -> frozenset:
        """Tokenize and normalize procurement object for Jaccard similarity."""
        texto = re.sub(r"[^\w\s]", " ", texto.lower())
        return frozenset(
            t for t in texto.split()
            if len(t) > 2 and t not in ConsolidationService._FUZZY_STOPWORDS
        )

    @staticmethod
    def _jaccard(a: frozenset, b: frozenset) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    @staticmethod
    def _extract_edital_number(source_id: str) -> int | None:
        """Extract numeric edital number from source_id for proximity comparison.

        ISSUE-027: Editals like '/000037/2026' and '/000039/2026' from same org
        are likely related procurements (same batch, different lots).
        """
        match = re.search(r"/(\d{4,6})/", source_id or "")
        if match:
            try:
                return int(match.group(1))
            except (ValueError, TypeError):
                return None
        return None

    _LOT_PATTERN = re.compile(
        r'\b(?:lote|item|grupo|lotes?)\s*(?:n[.ºo°]?\s*)?(\d+)\b',
        re.IGNORECASE,
    )

    @staticmethod
    def _extract_lot_number(obj_text: str) -> str | None:
        """Extract lot/item/group number from objetoCompra text.

        ISSUE-027: Bids with the same object but different lot numbers are
        legitimate separate procurements and must NOT be deduplicated.
        """
        m = ConsolidationService._LOT_PATTERN.search(obj_text or "")
        return m.group(1) if m else None

    def _deduplicate_fuzzy(
        self, records: List[UnifiedProcurement]
    ) -> List[UnifiedProcurement]:
        """Second dedup layer: same procurement with different edital numbers.

        Blocking: group by cnpj_orgao (avoids O(n²) global comparisons).
        Match: Jaccard >= 0.85 on objeto tokens AND valor within 5%.
        Winner: higher-priority source, or first encountered if same priority.

        ISSUE-027: Addresses duplicates like "Pavimentação da rua Reinhold
        Schroeder" appearing twice from the same orgão with different edital
        numbers (e.g., /000061/2026 vs /000059/2026).
        """
        if len(records) < 2:
            return records

        # Phase 1: Block by normalized CNPJ
        blocks: Dict[str, List[int]] = defaultdict(list)
        for idx, rec in enumerate(records):
            cnpj = re.sub(r"[^\d]", "", rec.cnpj_orgao or "")
            if cnpj and len(cnpj) < 14:
                cnpj = cnpj.zfill(14)
            if cnpj:
                blocks[cnpj].append(idx)

        # Phase 2: Intra-block pairwise comparison
        to_remove: set = set()
        removed_count = 0

        # Pre-compute tokens for all records (avoids recomputation)
        tokens_cache: Dict[int, frozenset] = {}

        for cnpj, indices in blocks.items():
            if len(indices) < 2:
                continue

            for i_pos in range(len(indices)):
                idx_a = indices[i_pos]
                if idx_a in to_remove:
                    continue

                if idx_a not in tokens_cache:
                    tokens_cache[idx_a] = self._tokenize_objeto(records[idx_a].objeto)

                for j_pos in range(i_pos + 1, len(indices)):
                    idx_b = indices[j_pos]
                    if idx_b in to_remove:
                        continue

                    if idx_b not in tokens_cache:
                        tokens_cache[idx_b] = self._tokenize_objeto(records[idx_b].objeto)

                    sim = self._jaccard(tokens_cache[idx_a], tokens_cache[idx_b])
                    if sim < 0.70:
                        continue

                    # Diagnostic log — help trace why high-sim pairs aren't deduped
                    lot_a_diag = self._extract_lot_number(records[idx_a].objeto)
                    lot_b_diag = self._extract_lot_number(records[idx_b].objeto)
                    logger.debug(
                        f"[FUZZY-DEDUP-DIAG] sim={sim:.3f} lot_a={lot_a_diag} lot_b={lot_b_diag} "
                        f"val_a={records[idx_a].valor_estimado} val_b={records[idx_b].valor_estimado} "
                        f"src_a={records[idx_a].source_id[:40]} src_b={records[idx_b].source_id[:40]}"
                    )

                    # ISSUE-027: Lot detection — same object with different lot numbers
                    # are legitimate separate procurements, never deduplicate them.
                    lot_a = lot_a_diag
                    lot_b = lot_b_diag
                    if sim >= 0.85 and lot_a is not None and lot_b is not None and lot_a != lot_b:
                        continue  # Different lots of the same procurement — keep both

                    # Annotate bids with lot info for future frontend grouping
                    if lot_a is not None:
                        records[idx_a]._lot_number = lot_a  # type: ignore[attr-defined]
                    if lot_b is not None:
                        records[idx_b]._lot_number = lot_b  # type: ignore[attr-defined]

                    # Value proximity check.
                    # For high-confidence matches (Jaccard >= 0.85, same/no lot): allow up to 20%.
                    # For lower-confidence matches (0.70-0.85): keep the stricter 5% threshold.
                    val_a = records[idx_a].valor_estimado or 0
                    val_b = records[idx_b].valor_estimado or 0
                    if val_a > 0 and val_b > 0:
                        diff = abs(val_a - val_b) / max(val_a, val_b)
                        value_threshold = 0.20 if sim >= 0.85 else 0.05
                        if diff > value_threshold:
                            continue  # Different values = likely different lots

                    # ISSUE-027: For Jaccard 0.70-0.85, require edital number proximity
                    if sim < 0.85:
                        num_a = self._extract_edital_number(records[idx_a].source_id)
                        num_b = self._extract_edital_number(records[idx_b].source_id)
                        if num_a is not None and num_b is not None:
                            if abs(num_a - num_b) > 5:
                                continue
                        else:
                            continue

                    # Match confirmed — remove the later one (keep first/higher-priority)
                    to_remove.add(idx_b)
                    removed_count += 1
                    logger.info(
                        f"[FUZZY-DEDUP] Merged duplicate (Jaccard={sim:.2f}): "
                        f"cnpj={cnpj}, kept={records[idx_a].source_id}, "
                        f"removed={records[idx_b].source_id}"
                    )

        if removed_count > 0:
            logger.info(
                f"[FUZZY-DEDUP] Removed {removed_count} fuzzy duplicates "
                f"from {len(records)} records"
            )

        return [rec for idx, rec in enumerate(records) if idx not in to_remove]

    # Process-number pattern — PNCP source_id format:
    # "{cnpj}-{seq}-{edital_number}/{year}" e.g. "12345678000195-2026-000065/2026"
    # We extract the numeric edital component before the year suffix as the
    # "process base" so that minor sequential gaps (000065 vs 000066) from the
    # same orgão can be collapsed.
    _PROCESS_NUMBER_PATTERN = re.compile(r"-(\d{4,6})/(\d{4})$")

    @staticmethod
    def _extract_process_base(source_id: str, cnpj: str) -> str | None:
        """Return a (cnpj, year) key if this source_id looks like a PNCP edital.

        Two records share the same process base when they have the same orgão
        CNPJ and the same publication year. The edital sequence number is NOT
        included so that adjacent numbers (000065 / 000066) from the same org
        in the same year are grouped and the lower-priority duplicate removed.

        Returns None when source_id doesn't match the expected PNCP pattern.
        """
        if not source_id or not cnpj:
            return None
        m = ConsolidationService._PROCESS_NUMBER_PATTERN.search(source_id)
        if m:
            year = m.group(2)
            return f"{cnpj}|{year}"
        return None

    def _deduplicate_by_process_number(
        self, records: List[UnifiedProcurement]
    ) -> List[UnifiedProcurement]:
        """Third dedup layer: same org + same year with very similar objects.

        ISSUE-027: Addresses cases like "Amparo ETA V" appearing twice because
        PNCP returned adjacent edital numbers (/000065 and /000066) for the same
        procurement. Fuzzy dedup handles high Jaccard pairs but may miss pairs
        that have slightly different description wording yet are the same process.

        Strategy:
        - Group by (cnpj, year) — same org, same publication year
        - Within each group compare objeto Jaccard (>= 0.80) + valor proximity (20%)
        - Keep the record from the highest-priority source; if same source keep first
        """
        if len(records) < 2:
            return records

        # Build process-base groups
        groups: Dict[str, List[int]] = defaultdict(list)
        for idx, rec in enumerate(records):
            cnpj = re.sub(r"[^\d]", "", rec.cnpj_orgao or "")
            if cnpj and len(cnpj) < 14:
                cnpj = cnpj.zfill(14)
            base = self._extract_process_base(rec.source_id or "", cnpj)
            if base:
                groups[base].append(idx)

        # Source priority for winner selection
        source_priority: Dict[str, int] = {}
        for code, adapter in self._adapters.items():
            adapter_code = getattr(adapter, "code", code)
            adapter_meta = getattr(adapter, "metadata", None)
            if adapter_meta is not None:
                source_priority[adapter_code] = adapter_meta.priority

        to_remove: set = set()
        removed_count = 0

        tokens_cache: Dict[int, frozenset] = {}

        for base, indices in groups.items():
            if len(indices) < 2:
                continue

            for i_pos in range(len(indices)):
                idx_a = indices[i_pos]
                if idx_a in to_remove:
                    continue

                if idx_a not in tokens_cache:
                    tokens_cache[idx_a] = self._tokenize_objeto(records[idx_a].objeto)

                for j_pos in range(i_pos + 1, len(indices)):
                    idx_b = indices[j_pos]
                    if idx_b in to_remove:
                        continue

                    if idx_b not in tokens_cache:
                        tokens_cache[idx_b] = self._tokenize_objeto(records[idx_b].objeto)

                    sim = self._jaccard(tokens_cache[idx_a], tokens_cache[idx_b])
                    if sim < 0.80:
                        continue

                    # Different lot numbers are distinct procurements — skip
                    lot_a = self._extract_lot_number(records[idx_a].objeto)
                    lot_b = self._extract_lot_number(records[idx_b].objeto)
                    if lot_a is not None and lot_b is not None and lot_a != lot_b:
                        continue

                    # Value proximity (20%)
                    val_a = records[idx_a].valor_estimado or 0
                    val_b = records[idx_b].valor_estimado or 0
                    if val_a > 0 and val_b > 0:
                        diff = abs(val_a - val_b) / max(val_a, val_b)
                        if diff > 0.20:
                            continue

                    # Decide winner: lower priority number wins; ties keep first
                    pri_a = source_priority.get(records[idx_a].source_name, 999)
                    pri_b = source_priority.get(records[idx_b].source_name, 999)
                    if pri_b < pri_a:
                        # b is higher-priority — remove a and keep b
                        to_remove.add(idx_a)
                        removed_count += 1
                        logger.info(
                            f"[PROCESS-DEDUP] Merged duplicate (Jaccard={sim:.2f}): "
                            f"base={base}, kept={records[idx_b].source_id}, "
                            f"removed={records[idx_a].source_id}"
                        )
                        break  # idx_a is gone, no need to compare further
                    else:
                        to_remove.add(idx_b)
                        removed_count += 1
                        logger.info(
                            f"[PROCESS-DEDUP] Merged duplicate (Jaccard={sim:.2f}): "
                            f"base={base}, kept={records[idx_a].source_id}, "
                            f"removed={records[idx_b].source_id}"
                        )

        if removed_count > 0:
            logger.info(
                f"[PROCESS-DEDUP] Removed {removed_count} process-number duplicates "
                f"from {len(records)} records"
            )

        return [rec for idx, rec in enumerate(records) if idx not in to_remove]

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
            except Exception as e:
                logger.debug(f"Adapter close error (non-critical): {e}")
        # AC12: Close fallback adapter to prevent HTTP client leak
        if self._fallback_adapter is not None:
            try:
                await self._fallback_adapter.close()
            except Exception as e:
                logger.debug(f"Fallback adapter close error (non-critical): {e}")
