"""In-memory progress tracking for SSE-based real-time search progress.

Manages ProgressTracker instances that use asyncio.Queue to communicate
between the search pipeline (producer) and the SSE endpoint (consumer).
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProgressEvent:
    """A single progress update event."""
    stage: str           # "connecting", "fetching", "filtering", "llm", "excel", "complete", "error"
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

    Uses asyncio.Queue to communicate between the search pipeline
    (producer) and the SSE endpoint (consumer).
    """

    def __init__(self, search_id: str, uf_count: int):
        self.search_id = search_id
        self.uf_count = uf_count
        self.queue: asyncio.Queue[ProgressEvent] = asyncio.Queue()
        self.created_at = time.time()
        self._ufs_completed = 0
        self._is_complete = False

    async def emit(self, stage: str, progress: int, message: str, **detail: Any) -> None:
        """Push a progress event to the queue."""
        event = ProgressEvent(
            stage=stage,
            progress=min(100, max(0, progress)),
            message=message,
            detail=detail,
        )
        await self.queue.put(event)

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


# Global registry of active progress trackers
_active_trackers: Dict[str, ProgressTracker] = {}
_TRACKER_TTL = 300  # 5 minutes


def create_tracker(search_id: str, uf_count: int) -> ProgressTracker:
    """Create and register a progress tracker."""
    _cleanup_stale()
    tracker = ProgressTracker(search_id, uf_count)
    _active_trackers[search_id] = tracker
    logger.debug(f"Created progress tracker: {search_id} ({uf_count} UFs)")
    return tracker


def get_tracker(search_id: str) -> Optional[ProgressTracker]:
    """Get a progress tracker by search_id."""
    return _active_trackers.get(search_id)


def remove_tracker(search_id: str) -> None:
    """Remove a tracker after search completes."""
    _active_trackers.pop(search_id, None)


def _cleanup_stale() -> None:
    """Remove trackers older than TTL."""
    now = time.time()
    stale = [sid for sid, t in _active_trackers.items() if now - t.created_at > _TRACKER_TTL]
    for sid in stale:
        _active_trackers.pop(sid, None)
    if stale:
        logger.debug(f"Cleaned up {len(stale)} stale progress trackers")
