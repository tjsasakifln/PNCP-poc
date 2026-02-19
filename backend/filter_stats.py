"""
STORY-248 AC9: Structured filter rejection tracking.

Tracks all filter rejections with reason codes for monitoring
and the /admin/filter-stats endpoint (AC10).

All rejection events are:
1. Recorded in-memory for the /admin/filter-stats endpoint
2. Logged with structured fields (reason_code, sector, event_type)
   so log aggregation tools can query by reason code.

Thread-safe via threading.Lock (FastAPI may use thread pools for sync deps).
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Reason codes — one per rejection path in filter.py / aplicar_todos_filtros
# ---------------------------------------------------------------------------
REASON_KEYWORD_MISS = "keyword_miss"
REASON_EXCLUSION_HIT = "exclusion_hit"
REASON_LLM_REJECT = "llm_reject"
REASON_DENSITY_LOW = "density_low"
REASON_VALUE_EXCEED = "value_exceed"
REASON_UF_MISMATCH = "uf_mismatch"
REASON_STATUS_MISMATCH = "status_mismatch"
REASON_CO_OCCURRENCE = "co_occurrence"

ALL_REASON_CODES = [
    REASON_KEYWORD_MISS,
    REASON_EXCLUSION_HIT,
    REASON_LLM_REJECT,
    REASON_DENSITY_LOW,
    REASON_VALUE_EXCEED,
    REASON_UF_MISMATCH,
    REASON_STATUS_MISMATCH,
    REASON_CO_OCCURRENCE,
]


class FilterStatsTracker:
    """In-memory tracker for filter rejection statistics.

    Stores rejection entries keyed by reason code. Each entry includes a
    UTC timestamp, the reason code, and optional sector / description preview.

    Old entries are lazily cleaned up when ``cleanup_old()`` is called.
    The ``get_stats()`` method filters by timestamp so stale data does not
    affect the counts returned to the admin endpoint.
    """

    def __init__(self, retention_days: int = 7) -> None:
        self._stats: Dict[str, List[Dict]] = defaultdict(list)
        self._lock = Lock()
        self._retention_days = retention_days

    def record_rejection(
        self,
        reason: str,
        sector: Optional[str] = None,
        description_preview: Optional[str] = None,
    ) -> None:
        """Record a filter rejection with reason code.

        Args:
            reason: One of the ``REASON_*`` constants defined above.
            sector: Optional sector ID that was being searched.
            description_preview: First 100 chars of the procurement object.
        """
        entry: Dict = {
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "sector": sector,
        }
        if description_preview:
            entry["preview"] = description_preview[:100]

        with self._lock:
            self._stats[reason].append(entry)

        # Structured log — queryable by log aggregation (e.g. Datadog, Loki)
        logger.info(
            "filter_rejection",
            extra={
                "reason_code": reason,
                "sector": sector,
                "event_type": "filter_reject",
            },
        )

    def get_stats(self, days: int = 7) -> Dict:
        """Get rejection counts for the last *days* days.

        Returns a dict with each reason code mapped to its count, plus
        ``total_rejections`` and ``period_days``.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_iso = cutoff.isoformat()

        result: Dict = {}
        with self._lock:
            for reason in ALL_REASON_CODES:
                entries = self._stats.get(reason, [])
                recent = [e for e in entries if e["timestamp"] >= cutoff_iso]
                result[reason] = len(recent)

        result["total_rejections"] = sum(
            result[r] for r in ALL_REASON_CODES
        )
        result["period_days"] = days
        return result

    def cleanup_old(self) -> int:
        """Remove entries older than the retention period.

        Returns the number of entries removed.
        """
        cutoff = datetime.utcnow() - timedelta(days=self._retention_days)
        cutoff_iso = cutoff.isoformat()
        removed = 0

        with self._lock:
            for reason in list(self._stats.keys()):
                before = len(self._stats[reason])
                self._stats[reason] = [
                    e for e in self._stats[reason]
                    if e["timestamp"] >= cutoff_iso
                ]
                removed += before - len(self._stats[reason])

        if removed > 0:
            logger.info(f"filter_stats cleanup: removed {removed} old entries")

        return removed


# ---------------------------------------------------------------------------
# Global singleton — imported by filter.py and admin.py
# ---------------------------------------------------------------------------
filter_stats_tracker = FilterStatsTracker()
