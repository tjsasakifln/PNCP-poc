"""Distributed progress tracking for SSE-based real-time search progress.

Supports two modes:
1. Redis pub/sub (horizontal scaling): Shares progress events across backend instances
2. In-memory fallback (single instance): Uses asyncio.Queue when Redis unavailable

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


@dataclass
class ProgressEvent:
    """A single progress update event."""
    stage: str           # "connecting", "fetching", "filtering", "llm", "excel", "complete", "degraded", "error"
    progress: int        # 0-100 (-1 for error)
    message: str         # Human-readable status message
    detail: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "progress": self.progress,
            "message": self.message,
            "detail": self.detail,
        }


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
        self.queue: asyncio.Queue[ProgressEvent] = asyncio.Queue()
        self.created_at = time.time()
        self._ufs_completed = 0
        self._is_complete = False
        self._use_redis = use_redis

    async def emit(self, stage: str, progress: int, message: str, **detail: Any) -> None:
        """Push a progress event to the queue and/or Redis pub/sub channel."""
        event = ProgressEvent(
            stage=stage,
            progress=min(100, max(0, progress)),
            message=message,
            detail=detail,
        )

        # Always put in local queue for backward compatibility
        await self.queue.put(event)

        # Also publish to Redis if enabled
        if self._use_redis:
            await self._publish_to_redis(event)

    async def _publish_to_redis(self, event: ProgressEvent) -> None:
        """Publish event to Redis pub/sub channel."""
        redis = await get_redis_pool()
        if redis is None:
            return

        channel = f"bidiq:progress:{self.search_id}:events"
        try:
            event_json = json.dumps(event.to_dict())
            await redis.publish(channel, event_json)
        except Exception as e:
            logger.warning(f"Failed to publish progress event to Redis: {e}")

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
        await self.queue.put(event)

        # Also publish to Redis if enabled
        if self._use_redis:
            await self._publish_to_redis(event)

    async def emit_complete(self) -> None:
        """Signal search completion."""
        self._is_complete = True
        event = ProgressEvent(
            stage="complete",
            progress=100,
            message="Busca concluida!",
        )
        await self.queue.put(event)

    async def emit_error(self, error_message: str) -> None:
        """Signal search error."""
        self._is_complete = True
        event = ProgressEvent(
            stage="error",
            progress=-1,
            message=error_message,
            detail={"error": error_message},
        )
        await self.queue.put(event)


# Global registry of active progress trackers (in-memory mode only)
_active_trackers: Dict[str, ProgressTracker] = {}
_TRACKER_TTL = 300  # 5 minutes


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
            key = f"bidiq:progress:{search_id}"
            metadata = await redis.hgetall(key)
            if metadata and "uf_count" in metadata:
                uf_count = int(metadata["uf_count"])
                # Recreate tracker from metadata (for SSE consumer on different instance)
                tracker = ProgressTracker(search_id, uf_count, use_redis=True)
                _active_trackers[search_id] = tracker
                logger.debug(f"Loaded tracker from Redis metadata: {search_id}")
                return tracker
        except Exception as e:
            logger.warning(f"Failed to load tracker from Redis: {e}")

    return None


async def remove_tracker(search_id: str) -> None:
    """Remove a tracker after search completes.

    Cleans up both in-memory and Redis state.
    """
    _active_trackers.pop(search_id, None)

    # Remove from Redis if available
    redis = await get_redis_pool()
    if redis:
        try:
            key = f"bidiq:progress:{search_id}"
            await redis.delete(key)
        except Exception as e:
            logger.warning(f"Failed to remove tracker from Redis: {e}")


def _cleanup_stale() -> None:
    """Remove trackers older than TTL (in-memory only)."""
    now = time.time()
    stale = [sid for sid, t in _active_trackers.items() if now - t.created_at > _TRACKER_TTL]
    for sid in stale:
        _active_trackers.pop(sid, None)
    if stale:
        logger.debug(f"Cleaned up {len(stale)} stale progress trackers")


async def _store_tracker_metadata(search_id: str, uf_count: int) -> None:
    """Store tracker metadata in Redis with TTL."""
    redis = await get_redis_pool()
    if redis is None:
        return

    try:
        key = f"bidiq:progress:{search_id}"
        metadata = {
            "uf_count": str(uf_count),
            "created_at": str(time.time()),
        }
        await redis.hset(key, mapping=metadata)
        await redis.expire(key, _TRACKER_TTL)
    except Exception as e:
        logger.warning(f"Failed to store tracker metadata in Redis: {e}")


async def subscribe_to_events(search_id: str) -> Optional["redis.asyncio.client.PubSub"]:  # noqa: F821
    """Subscribe to Redis pub/sub channel for progress events.

    Returns:
        redis.asyncio.client.PubSub instance or None if Redis unavailable.
    """
    redis = await get_redis_pool()
    if redis is None:
        return None

    try:
        pubsub = redis.pubsub()
        channel = f"bidiq:progress:{search_id}:events"
        await pubsub.subscribe(channel)
        logger.debug(f"Subscribed to Redis channel: {channel}")
        return pubsub
    except Exception as e:
        logger.warning(f"Failed to subscribe to Redis channel: {e}")
        return None
