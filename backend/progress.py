"""Distributed progress tracking for SSE-based real-time search progress.

Supports two modes:
1. Redis Streams (horizontal scaling): Append-only log with replay for cross-worker SSE
2. In-memory fallback (single instance): Uses asyncio.Queue when Redis unavailable

STORY-276: Migrated from Redis Pub/Sub to Redis Streams for at-least-once delivery.
Pub/Sub was fire-and-forget (at-most-once) — events published before subscriber connected
were permanently lost, causing "stuck at 10%" progress bars with multi-worker Gunicorn.
Redis Streams provides persistent append-only log with replay from any point.

STORY-294 AC1/AC4: Tracker metadata stored in Redis enables cross-worker SSE.
Worker A creates tracker + publishes to Streams, Worker B reads from Streams.
STATE_STORE_ERRORS metric tracks Redis operation failures (AC7).

The mode is determined by REDIS_URL environment variable and connection health.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from redis_pool import get_redis_pool, is_redis_available

logger = logging.getLogger(__name__)

# STORY-276: Terminal stages that trigger stream EXPIRE
_TERMINAL_STAGES = frozenset({
    "complete", "error", "degraded", "refresh_available", "search_complete",
})
# STORY-276 AC1: TTL for stream key after terminal event (5 minutes)
_STREAM_EXPIRE_TTL = 300

# STORY-297: SSE Last-Event-ID resumption constants
_REPLAY_LIST_TTL = 600       # 10 minutes TTL for replay list
_REPLAY_MAX_EVENTS = 200     # HARDEN-017 AC1: reduced from 1000 (ring buffer max)
_REPLAY_KEY_PREFIX = "sse_events:"  # Redis list key prefix


@dataclass
class ProgressEvent:
    """A single progress update event."""
    stage: str           # "connecting", "fetching", "filtering", "llm", "excel", "complete", "degraded", "error"
    progress: int        # 0-100 (-1 for error)
    message: str         # Human-readable status message
    detail: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "stage": self.stage,
            "progress": self.progress,
            "message": self.message,
            "detail": self.detail,
        }
        # F-02 AC17: Include trace_id in SSE events when tracing is active
        from telemetry import get_trace_id
        trace_id = get_trace_id()
        if trace_id:
            d["trace_id"] = trace_id
        # CRIT-004 AC19-AC20: Include search_id and request_id for correlation
        from middleware import search_id_var, request_id_var
        search_id = search_id_var.get("-")
        request_id = request_id_var.get("-")
        if search_id != "-":
            d["search_id"] = search_id
        if request_id != "-":
            d["request_id"] = request_id
        return d


class ProgressTracker:
    """
    Manages progress for a single search operation.

    Supports two modes:
    - Redis pub/sub: Publishes events to Redis channel for distributed SSE
    - In-memory queue: Uses asyncio.Queue as fallback for single-instance deployments
    """

    def __init__(self, search_id: str, uf_count: int, use_redis: bool = False):
        self.search_id = search_id
        self.uf_count = uf_count
        self.queue: asyncio.Queue[ProgressEvent] = asyncio.Queue(maxsize=500)
        self.created_at = time.time()
        self._ufs_completed = 0
        self._is_complete = False
        self._use_redis = use_redis
        # STORY-297: Monotonic event counter + local history for replay
        self._event_counter = 0
        self._event_history: list[tuple[int, dict]] = []
        # CRIT-071: Accumulated partial licitacoes for progressive SSE
        self.partial_licitacoes: list[dict] = []

    async def emit(self, stage: str, progress: int, message: str, **detail: Any) -> None:
        """Push a progress event to the queue and/or Redis pub/sub channel."""
        event = ProgressEvent(
            stage=stage,
            progress=min(100, max(0, progress)),
            message=message,
            detail=detail,
        )
        await self._emit_event(event)

    async def _publish_to_redis(self, event: ProgressEvent) -> None:
        """Publish event to Redis Stream (STORY-276 AC1).

        Uses XADD to append to an append-only log instead of Pub/Sub PUBLISH.
        This ensures events are persisted and can be replayed by late subscribers.
        """
        redis = await get_redis_pool()
        if redis is None:
            return

        stream_key = f"smartlic:progress:{self.search_id}:stream"
        try:
            event_dict = event.to_dict()
            fields: Dict[str, str] = {
                "stage": event.stage,
                "progress": str(event.progress),
                "message": event.message,
                "detail_json": json.dumps(event.detail),
            }
            # Preserve correlation fields
            for key in ("trace_id", "search_id", "request_id"):
                if key in event_dict:
                    fields[key] = event_dict[key]

            await redis.xadd(stream_key, fields)

            # AC1: Set EXPIRE after terminal events (5 min cleanup)
            if event.stage in _TERMINAL_STAGES:
                await redis.expire(stream_key, _STREAM_EXPIRE_TTL)

        except Exception as e:
            from metrics import STATE_STORE_ERRORS
            STATE_STORE_ERRORS.labels(store="tracker", operation="write").inc()
            logger.warning(f"Failed to publish progress event to Redis Stream: {e}")

    async def _store_replay_event(self, event_id: int, event_dict: dict) -> None:
        """STORY-297 AC2: Store event in Redis list for Last-Event-ID replay.

        Uses RPUSH + LTRIM (ring buffer) with 10min TTL.
        Graceful failure — replay is best-effort, not critical path.
        """
        redis = await get_redis_pool()
        if redis is None:
            return

        replay_key = f"{_REPLAY_KEY_PREFIX}{self.search_id}"
        try:
            entry = json.dumps({"id": event_id, "data": event_dict})
            await redis.rpush(replay_key, entry)
            # AC5: Ring buffer — keep max 1000 entries
            await redis.ltrim(replay_key, -_REPLAY_MAX_EVENTS, -1)
            # AC2: 10min TTL
            await redis.expire(replay_key, _REPLAY_LIST_TTL)
        except Exception as e:
            logger.warning(f"STORY-297: Failed to store replay event: {e}")

    def get_events_after(self, after_id: int) -> list[tuple[int, dict]]:
        """STORY-297 AC3: Get local events with id > after_id for replay."""
        return [(eid, data) for eid, data in self._event_history if eid > after_id]

    async def _emit_event(self, event: ProgressEvent) -> None:
        """STORY-297: Common event dispatch — counter, queue, replay storage, Redis stream.

        All emit_* methods that create ProgressEvent directly should call this
        instead of manually doing queue.put + _publish_to_redis.
        """
        self._event_counter += 1
        event_id = self._event_counter

        # HARDEN-003 AC2: Drop oldest event when queue is full (backpressure)
        if self.queue.full():
            try:
                self.queue.get_nowait()  # drop oldest
            except asyncio.QueueEmpty:
                pass
            from metrics import SSE_QUEUE_DROPS
            SSE_QUEUE_DROPS.inc()
            logger.debug(f"SSE queue full for {self.search_id}, dropped oldest event")

        await self.queue.put(event)

        # HARDEN-017 AC2/AC3: partial_data events are emitted via queue (real-time SSE)
        # but excluded from replay history (they are the largest events, 10KB+)
        if event.stage == "partial_data":
            if self._use_redis:
                await self._publish_to_redis(event)
            return

        event_dict = event.to_dict()
        self._event_history.append((event_id, event_dict))
        if len(self._event_history) > _REPLAY_MAX_EVENTS:
            self._event_history = self._event_history[-_REPLAY_MAX_EVENTS:]

        await self._store_replay_event(event_id, event_dict)

        if self._use_redis:
            await self._publish_to_redis(event)

    async def emit_uf_complete(self, uf: str, items_count: int) -> None:
        """Emit progress for a single UF completion."""
        self._ufs_completed += 1
        # Fetching phase spans 10-55% of total progress
        fetch_progress = 10 + int((self._ufs_completed / max(self.uf_count, 1)) * 45)
        await self.emit(
            stage="fetching",
            progress=fetch_progress,
            message=f"Buscando dados: {self._ufs_completed}/{self.uf_count} estados",
            uf=uf,
            uf_index=self._ufs_completed,
            uf_total=self.uf_count,
            items_found=items_count,
        )

    def add_partial_licitacoes(self, licitacoes: list[dict]) -> None:
        """CRIT-071: Append-only accumulation of partial bid data."""
        self.partial_licitacoes.extend(licitacoes)

    async def emit_partial_data(
        self,
        licitacoes: list[dict],
        batch_index: int,
        ufs_completed: list[str],
        is_final: bool = False,
    ) -> None:
        """CRIT-071: Emit partial_data SSE event with actual bid data.

        If the payload exceeds 500 items, sends a truncated event with count
        and metadata only to avoid oversized SSE frames.
        """
        _MAX_INLINE = 500
        detail: dict[str, Any] = {
            "batch_index": batch_index,
            "ufs_completed": ufs_completed,
            "is_final": is_final,
            "total_items": len(licitacoes),
        }

        if len(licitacoes) > _MAX_INLINE:
            detail["truncated"] = True
            detail["licitacoes"] = []
        else:
            detail["truncated"] = False
            detail["licitacoes"] = licitacoes

        event = ProgressEvent(
            stage="partial_data",
            progress=-1,
            message=f"Dados parciais: {len(licitacoes)} licitações (batch {batch_index})",
            detail=detail,
        )
        await self._emit_event(event)

    async def emit_uf_status(self, uf: str, status: str, **detail: Any) -> None:
        """Emit per-UF status event for real-time tracking grid.

        STORY-257A AC6: Individual UF status updates.

        Args:
            uf: State code (e.g., "SP")
            status: One of "pending", "fetching", "retrying", "success", "failed", "recovered"
            **detail: Additional details (count, attempt, max, reason)
        """
        await self.emit(
            stage="uf_status",
            progress=-1,  # UF status events don't map to overall progress
            message=f"UF {uf}: {status}",
            uf=uf,
            uf_status=status,
            **detail,
        )

    async def emit_batch_progress(
        self, batch_num: int, total_batches: int, ufs_in_batch: list[str]
    ) -> None:
        """GTM-FIX-031: Emit batch progress event for phased UF fetching.

        Args:
            batch_num: Current batch number (1-indexed)
            total_batches: Total number of batches
            ufs_in_batch: UF codes in this batch
        """
        batch_progress = 10 + int((batch_num / max(total_batches, 1)) * 45)
        await self.emit(
            stage="batch_progress",
            progress=batch_progress,
            message=f"Fase {batch_num} de {total_batches}",
            batch_num=batch_num,
            total_batches=total_batches,
            ufs_in_batch=ufs_in_batch,
        )

    async def emit_degraded(self, reason: str, detail: Optional[Dict[str, Any]] = None) -> None:
        """Signal search completed with degraded data (cache/partial).

        GTM-RESILIENCE-A02 AC1-AC2: Third terminal state between complete and error.
        Emits stage="degraded" with metadata about cache freshness and coverage.
        """
        self._is_complete = True
        merged_detail = {"reason": reason}
        if detail:
            merged_detail.update(detail)

        # Build human-readable message from metadata
        cache_age = merged_detail.get("cache_age_hours")
        if cache_age is not None:
            if cache_age < 1:
                age_text = f"{int(cache_age * 60)}min atrás"
            else:
                age_text = f"{cache_age:.0f}h atrás"
            message = f"Resultados disponíveis (dados de {age_text})"
        elif reason == "partial":
            coverage = merged_detail.get("coverage_pct", 0)
            message = f"Resultados parciais disponíveis ({coverage}% de cobertura)"
        else:
            message = "Resultados disponíveis com ressalvas"

        event = ProgressEvent(
            stage="degraded",
            progress=100,
            message=message,
            detail=merged_detail,
        )
        await self._emit_event(event)

    async def emit_complete(self) -> None:
        """Signal search completion."""
        self._is_complete = True
        event = ProgressEvent(
            stage="complete",
            progress=100,
            message="Busca concluida!",
        )
        await self._emit_event(event)

    async def emit_source_complete(
        self,
        source: str,
        status: str,
        record_count: int,
        duration_ms: int,
        error: str | None = None,
    ) -> None:
        """STORY-295 AC7: Emit source_complete when a data source finishes.

        Non-terminal event — SSE stream stays open.

        Args:
            source: Source identifier (e.g., "PNCP", "PORTAL_COMPRAS")
            status: "success", "timeout", "partial", "error"
            record_count: Number of records returned by this source
            duration_ms: How long the source took
            error: Error message if applicable
        """
        detail: dict = {
            "source": source,
            "source_status": status,
            "record_count": record_count,
            "duration_ms": duration_ms,
        }
        if error:
            detail["error"] = error

        event = ProgressEvent(
            stage="source_complete",
            progress=-1,  # Source events don't map to overall progress
            message=f"Fonte {source}: {status} ({record_count} resultados)",
            detail=detail,
        )
        await self._emit_event(event)

    async def emit_source_error(
        self,
        source: str,
        error: str,
        duration_ms: int,
    ) -> None:
        """STORY-295 AC8: Emit source_error when a data source fails.

        Non-terminal event — SSE stream stays open.
        """
        event = ProgressEvent(
            stage="source_error",
            progress=-1,
            message=f"Fonte {source}: falhou — {error}",
            detail={
                "source": source,
                "error": error,
                "duration_ms": duration_ms,
            },
        )
        await self._emit_event(event)

    async def emit_progressive_results(
        self,
        source: str,
        items_count: int,
        total_so_far: int,
        sources_completed: list[str],
        sources_pending: list[str],
    ) -> None:
        """STORY-295 AC1-AC2: Emit partial results as each source completes.

        Non-terminal event — SSE stream stays open.
        Frontend uses this to incrementally populate the results table.
        """
        total_sources = len(sources_completed) + len(sources_pending)
        progress_pct = min(55, 10 + int((len(sources_completed) / max(total_sources, 1)) * 45))

        event = ProgressEvent(
            stage="partial_results",
            progress=progress_pct,
            message=f"{len(sources_completed)} de {total_sources} fontes concluídas — {total_so_far} resultados até agora",
            detail={
                "source": source,
                "new_results_count": items_count,
                "total_so_far": total_so_far,
                "sources_completed": sources_completed,
                "sources_pending": sources_pending,
            },
        )
        await self._emit_event(event)

    async def emit_revalidated(self, total_results: int, fetched_at: str) -> None:
        """B-01 AC7: Notify connected user that background revalidation completed.

        Emitted when a stale-cache response was served and the background task
        successfully fetched fresh data. Frontend can optionally show a toast
        like "Updated data available".
        """
        event = ProgressEvent(
            stage="revalidated",
            progress=100,
            message=f"Dados atualizados: {total_results} resultados",
            detail={
                "total_results": total_results,
                "fetched_at": fetched_at,
            },
        )
        await self._emit_event(event)

    async def emit_partial_results(
        self,
        new_results_count: int,
        total_so_far: int,
        ufs_completed: list[str],
        ufs_pending: list[str],
    ) -> None:
        """A-04 AC3: Emit partial results event during background live fetch.

        Non-terminal event — SSE stream stays open after this.
        Debounced by caller (every 3 UFs or 10s).
        """
        progress_pct = min(95, 10 + int((len(ufs_completed) / max(len(ufs_completed) + len(ufs_pending), 1)) * 85))
        event = ProgressEvent(
            stage="partial_results",
            progress=progress_pct,
            message=f"{len(ufs_completed)} de {len(ufs_completed) + len(ufs_pending)} UFs processadas",
            detail={
                "new_results_count": new_results_count,
                "total_so_far": total_so_far,
                "ufs_completed": ufs_completed,
                "ufs_pending": ufs_pending,
            },
        )
        await self._emit_event(event)

    async def emit_refresh_available(
        self,
        total_live: int,
        total_cached: int,
        new_count: int,
        updated_count: int,
        removed_count: int,
    ) -> None:
        """A-04 AC4: Emit refresh available event when background fetch completes.

        Terminal event — SSE stream closes after this.
        """
        self._is_complete = True
        event = ProgressEvent(
            stage="refresh_available",
            progress=100,
            message=f"Dados atualizados disponíveis — {new_count} novas oportunidades",
            detail={
                "total_live": total_live,
                "total_cached": total_cached,
                "new_count": new_count,
                "updated_count": updated_count,
                "removed_count": removed_count,
            },
        )
        await self._emit_event(event)

    async def emit_search_complete(self, search_id: str, total_results: int, is_partial: bool = False) -> None:
        """GTM-ARCH-001 AC3 + CRIT-072 AC4: Signal async search completed.

        Emits stage="search_complete" with results_url so frontend can fetch full results.
        Terminal event — SSE stream closes after this.
        """
        self._is_complete = True
        event = ProgressEvent(
            stage="search_complete",
            progress=100,
            message=f"Busca concluída — {total_results} resultados",
            detail={
                "search_id": search_id,
                "total_results": total_results,
                "has_results": total_results > 0,
                "results_ready": True,
                "results_url": f"/v1/search/{search_id}/results",
                "is_partial": is_partial,
            },
        )
        await self._emit_event(event)

    async def emit_filter_summary(
        self,
        total_raw: int,
        total_filtered: int,
        rejected_keyword: int = 0,
        rejected_value: int = 0,
        rejected_llm: int = 0,
        filter_stats: dict | None = None,
    ) -> None:
        """STORY-327 AC5: Emit unified filter summary with raw vs filtered breakdown.

        Non-terminal event — SSE stream stays open after this.
        Frontend uses this to display "X relevantes de Y analisadas".
        """
        detail: dict = {
            "total_raw": total_raw,
            "total_filtered": total_filtered,
            "rejected_keyword": rejected_keyword,
            "rejected_value": rejected_value,
            "rejected_llm": rejected_llm,
        }
        if filter_stats:
            detail["rejected_uf"] = filter_stats.get("rejeitadas_uf", 0)
            detail["rejected_status"] = filter_stats.get("rejeitadas_status", 0)
            detail["rejected_outros"] = filter_stats.get("rejeitadas_outros", 0)

        event = ProgressEvent(
            stage="filter_summary",
            progress=70,
            message=f"{total_filtered} relevantes de {total_raw} analisadas",
            detail=detail,
        )
        await self._emit_event(event)

    async def emit_pending_review_complete(
        self,
        reclassified_count: int,
        accepted_count: int,
        rejected_count: int,
    ) -> None:
        """STORY-354 AC6: Signal that pending review bids have been reclassified.

        Non-terminal event — emitted when ARQ reclassify job completes.
        Frontend updates the pending review banner and optionally refreshes results.
        """
        event = ProgressEvent(
            stage="pending_review",
            progress=-1,
            message=f"Reclassificação concluída: {accepted_count} aprovadas, {rejected_count} rejeitadas",
            detail={
                "reclassified_count": reclassified_count,
                "accepted_count": accepted_count,
                "rejected_count": rejected_count,
            },
        )
        await self._emit_event(event)

    async def emit_error(self, error_message: str) -> None:
        """Signal search error."""
        self._is_complete = True
        event = ProgressEvent(
            stage="error",
            progress=-1,
            message=error_message,
            detail={"error": error_message},
        )
        await self._emit_event(event)


# Global registry of active progress trackers (in-memory mode only)
_active_trackers: Dict[str, ProgressTracker] = {}
_TRACKER_TTL = 420  # 7 minutes (AC14: >= FETCH_TIMEOUT 360s + margin)


async def get_replay_events(search_id: str, after_id: int) -> list[tuple[int, dict]]:
    """STORY-297 AC3: Get replay events after a given event ID.

    Tries local tracker history first, then Redis list.
    Returns list of (event_id, event_data) tuples.
    """
    # Try local tracker first (fastest)
    tracker = _active_trackers.get(search_id)
    if tracker and tracker._event_history:
        return tracker.get_events_after(after_id)

    # Fall back to Redis list
    redis = await get_redis_pool()
    if redis is None:
        return []

    replay_key = f"{_REPLAY_KEY_PREFIX}{search_id}"
    try:
        raw_entries = await redis.lrange(replay_key, 0, -1)
        if not raw_entries:
            return []

        events = []
        for entry in raw_entries:
            parsed = json.loads(entry)
            eid = parsed["id"]
            if eid > after_id:
                events.append((eid, parsed["data"]))
        return events
    except Exception as e:
        logger.warning(f"STORY-297: Failed to load replay events from Redis: {e}")
        return []


async def is_search_terminal(search_id: str) -> Optional[dict]:
    """STORY-297 AC4 + HARDEN-019: Check if search has reached a terminal state.

    Returns the terminal event data if found, None otherwise.
    Checks local tracker history first, then Redis list, then DB state machine.

    HARDEN-019: When Redis stream has expired (_STREAM_EXPIRE_TTL=300s) and client
    reconnects with Last-Event-ID, replay returns empty. Without DB fallback the
    client never receives a terminal event and the progress bar stays stuck at 90%.
    """
    # Check local tracker
    tracker = _active_trackers.get(search_id)
    if tracker and tracker._event_history:
        for _eid, data in reversed(tracker._event_history):
            if data.get("stage") in _TERMINAL_STAGES:
                return data
        return None

    # Check Redis list (last entry)
    redis = await get_redis_pool()
    if redis is not None:
        replay_key = f"{_REPLAY_KEY_PREFIX}{search_id}"
        try:
            last_entries = await redis.lrange(replay_key, -1, -1)
            if last_entries:
                parsed = json.loads(last_entries[0])
                data = parsed["data"]
                if data.get("stage") in _TERMINAL_STAGES:
                    return data
        except Exception as e:
            logger.warning(f"STORY-297: Failed to check terminal state: {e}")

    # HARDEN-019 AC1-AC3: Fallback to DB state machine when Redis is empty/expired
    return await _fallback_db_terminal(search_id)


# HARDEN-019 AC2: DB terminal states mapped to SSE terminal stages
_DB_STATE_TO_SSE_STAGE = {
    "completed": "complete",
    "failed": "error",
    "timed_out": "error",
    "rate_limited": "error",
}


async def _fallback_db_terminal(search_id: str) -> Optional[dict]:
    """HARDEN-019 AC1-AC3: Synthesize a terminal SSE event from DB state.

    Called when both local tracker and Redis replay list are empty (e.g. Redis
    stream expired after _STREAM_EXPIRE_TTL=300s). Queries search_state_transitions
    for the latest state and, if terminal, returns a synthetic SSE event so the
    client receives a proper terminal event instead of staying stuck.
    """
    try:
        from search_state_manager import get_current_state

        db_state = await get_current_state(search_id)
        if not db_state:
            return None

        to_state = db_state.get("to_state", "")
        sse_stage = _DB_STATE_TO_SSE_STAGE.get(to_state)
        if not sse_stage:
            return None

        # AC3: Build synthetic terminal event with DB data
        details = db_state.get("details") or {}
        if sse_stage == "complete":
            message = "Busca concluida!"
            progress = 100
        else:
            error_msg = details.get("error_message") or details.get("reason", "")
            message = error_msg or f"Busca finalizada com status: {to_state}"
            progress = -1

        synthetic_event: dict = {
            "stage": sse_stage,
            "progress": progress,
            "message": message,
            "detail": {
                "source": "db_fallback",
                "db_state": to_state,
                **details,
            },
        }
        logger.info(
            f"HARDEN-019: Synthesized terminal event from DB for {search_id} "
            f"(db_state={to_state}, sse_stage={sse_stage})"
        )
        return synthetic_event

    except Exception as e:
        logger.warning(f"HARDEN-019: DB fallback failed for {search_id}: {e}")
        return None


async def create_tracker(search_id: str, uf_count: int) -> ProgressTracker:
    """Create and register a progress tracker.

    Automatically selects Redis or in-memory mode based on availability.
    Stores tracker metadata in Redis for distributed access if available.
    """
    _cleanup_stale()

    # Check if Redis is available
    use_redis = await is_redis_available()

    tracker = ProgressTracker(search_id, uf_count, use_redis=use_redis)
    _active_trackers[search_id] = tracker

    # Store tracker metadata in Redis if available
    if use_redis:
        await _store_tracker_metadata(search_id, uf_count)

    logger.debug(
        f"Created progress tracker: {search_id} ({uf_count} UFs) "
        f"[mode: {'Redis' if use_redis else 'in-memory'}]"
    )
    return tracker


async def get_tracker(search_id: str) -> Optional[ProgressTracker]:
    """Get a progress tracker by search_id.

    Checks in-memory registry first, then falls back to Redis metadata.
    """
    # Check in-memory registry first
    tracker = _active_trackers.get(search_id)
    if tracker:
        return tracker

    # Try to load from Redis metadata
    redis = await get_redis_pool()
    if redis:
        try:
            key = f"smartlic:progress:{search_id}"
            metadata = await redis.hgetall(key)
            if metadata and "uf_count" in metadata:
                uf_count = int(metadata["uf_count"])
                # Recreate tracker from metadata (for SSE consumer on different instance)
                tracker = ProgressTracker(search_id, uf_count, use_redis=True)
                _active_trackers[search_id] = tracker
                logger.debug(f"Loaded tracker from Redis metadata: {search_id}")
                return tracker
        except Exception as e:
            from metrics import STATE_STORE_ERRORS
            STATE_STORE_ERRORS.labels(store="tracker", operation="read").inc()
            logger.warning(f"Failed to load tracker from Redis: {e}")

    return None


async def remove_tracker(search_id: str) -> None:
    """Remove a tracker after search completes.

    Cleans up both in-memory and Redis state (metadata + stream).
    """
    _active_trackers.pop(search_id, None)

    # Remove from Redis if available
    redis = await get_redis_pool()
    if redis:
        try:
            metadata_key = f"smartlic:progress:{search_id}"
            stream_key = f"smartlic:progress:{search_id}:stream"
            await redis.delete(metadata_key, stream_key)
        except Exception as e:
            from metrics import STATE_STORE_ERRORS
            STATE_STORE_ERRORS.labels(store="tracker", operation="delete").inc()
            logger.warning(f"Failed to remove tracker from Redis: {e}")


def _cleanup_stale() -> int:
    """Remove trackers older than TTL (in-memory only).

    AC15: Don't remove trackers with active searches still processing in DB.
    """
    now = time.time()
    stale_candidates = [sid for sid, t in _active_trackers.items() if now - t.created_at > _TRACKER_TTL]

    # AC15: Check if any stale candidates are still actively processing
    stale = []
    for sid in stale_candidates:
        tracker = _active_trackers.get(sid)
        if tracker and not tracker._is_complete:
            # Check if search is still processing in DB before removing
            try:
                from search_state_manager import get_state_machine
                machine = get_state_machine(sid)
                if machine and not machine.is_terminal:
                    logger.debug(f"Skipping cleanup of tracker {sid} — search still processing")
                    continue
            except Exception:
                pass
        stale.append(sid)

    for sid in stale:
        _active_trackers.pop(sid, None)
    if stale:
        logger.debug(f"Cleaned up {len(stale)} stale progress trackers")
    return len(stale)


_TRACKER_CLEANUP_INTERVAL = 120  # HARDEN-004 AC1: seconds between periodic cleanups


async def _periodic_tracker_cleanup() -> None:
    """HARDEN-004 AC1: Periodic cleanup of stale trackers every 120s.

    HARDEN-013 AC3: Also cleans up stale background results.
    """
    while True:
        await asyncio.sleep(_TRACKER_CLEANUP_INTERVAL)
        try:
            cleaned = _cleanup_stale()
            if cleaned > 0:
                from metrics import TRACKER_CLEANUP_COUNT
                TRACKER_CLEANUP_COUNT.inc(cleaned)
            # HARDEN-013 AC3: piggyback results cleanup on tracker cleanup cycle
            try:
                from routes.search import _cleanup_stale_results
                _cleanup_stale_results()
            except Exception as e:
                logger.warning(f"HARDEN-013: Background results cleanup error: {e}")
        except Exception as e:
            logger.warning(f"HARDEN-004: Tracker cleanup error: {e}")


async def _store_tracker_metadata(search_id: str, uf_count: int) -> None:
    """Store tracker metadata in Redis with TTL."""
    redis = await get_redis_pool()
    if redis is None:
        return

    try:
        key = f"smartlic:progress:{search_id}"
        metadata = {
            "uf_count": str(uf_count),
            "created_at": str(time.time()),
        }
        await redis.hset(key, mapping=metadata)
        await redis.expire(key, _TRACKER_TTL)
    except Exception as e:
        from metrics import STATE_STORE_ERRORS
        STATE_STORE_ERRORS.labels(store="tracker", operation="write").inc()
        logger.warning(f"Failed to store tracker metadata in Redis: {e}")


def get_active_tracker_count() -> int:
    """HARDEN-024 AC4: Return number of active progress trackers."""
    return len(_active_trackers)


# STORY-276 AC4: subscribe_to_events() removed — Redis Pub/Sub replaced by Streams.
# SSE consumer now uses XREAD BLOCK directly in routes/search.py.
