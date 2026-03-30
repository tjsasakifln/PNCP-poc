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
from datetime import datetime, timedelta, timezone
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
REASON_RED_FLAGS_SECTOR = "red_flags_sector"

ALL_REASON_CODES = [
    REASON_KEYWORD_MISS,
    REASON_EXCLUSION_HIT,
    REASON_LLM_REJECT,
    REASON_DENSITY_LOW,
    REASON_VALUE_EXCEED,
    REASON_UF_MISMATCH,
    REASON_STATUS_MISMATCH,
    REASON_CO_OCCURRENCE,
    REASON_RED_FLAGS_SECTOR,
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "sector": sector,
        }
        if description_preview:
            entry["preview"] = description_preview[:100]

        with self._lock:
            self._stats[reason].append(entry)

    def get_stats(self, days: int = 7) -> Dict:
        """Get rejection counts for the last *days* days.

        Returns a dict with each reason code mapped to its count, plus
        ``total_rejections`` and ``period_days``.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
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
        cutoff = datetime.now(timezone.utc) - timedelta(days=self._retention_days)
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
# STORY-351: Discard Rate Tracker (30-day moving average for /v1/metrics/discard-rate)
# ---------------------------------------------------------------------------


class DiscardRateTracker:
    """Tracks per-search filter input/output counts for discard rate computation.

    Used by the public ``GET /v1/metrics/discard-rate`` endpoint to serve
    a 30-day moving average of the filter discard rate (overall + per-sector).
    """

    def __init__(self, retention_days: int = 30) -> None:
        self._records: List[Dict] = []
        self._lock = Lock()
        self._retention_days = retention_days

    def record(
        self, input_count: int, output_count: int, sector: str, search_id: str = ""
    ) -> None:
        """Record a single search's filter input/output counts."""
        if input_count <= 0:
            return

        entry: Dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input": input_count,
            "output": output_count,
            "sector": sector or "unknown",
        }
        if search_id:
            entry["search_id"] = search_id

        with self._lock:
            self._records.append(entry)

        # AC9: Structured log
        discard_rate = round(1 - output_count / input_count, 4) if input_count > 0 else 0
        logger.info(
            "filter_stats",
            extra={
                "event": "filter_stats",
                "input": input_count,
                "output": output_count,
                "discard_rate": discard_rate,
                "sector": sector or "unknown",
                "search_id": search_id,
            },
        )

    def get_discard_rate(self, days: int = 30) -> Dict:
        """Compute the moving-average discard rate over the last *days* days.

        Returns:
            {
                "discard_rate_pct": float,  # overall percentage (e.g. 87.3)
                "sample_size": int,         # number of searches in window
                "total_input": int,
                "total_output": int,
                "period_days": int,
                "per_sector": { "sector_id": float, ... },
            }
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        with self._lock:
            recent = [r for r in self._records if r["timestamp"] >= cutoff]

        total_input = sum(r["input"] for r in recent)
        total_output = sum(r["output"] for r in recent)
        overall_rate = round((1 - total_output / total_input) * 100, 1) if total_input > 0 else 0.0

        # Per-sector aggregation
        sectors: Dict[str, Dict] = {}
        for r in recent:
            s = r["sector"]
            if s not in sectors:
                sectors[s] = {"input": 0, "output": 0}
            sectors[s]["input"] += r["input"]
            sectors[s]["output"] += r["output"]

        per_sector: Dict[str, float] = {}
        for s, data in sectors.items():
            per_sector[s] = (
                round((1 - data["output"] / data["input"]) * 100, 1)
                if data["input"] > 0
                else 0.0
            )

        return {
            "discard_rate_pct": overall_rate,
            "sample_size": len(recent),
            "total_input": total_input,
            "total_output": total_output,
            "period_days": days,
            "per_sector": per_sector,
        }

    def cleanup_old(self) -> int:
        """Remove entries older than the retention period."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=self._retention_days)).isoformat()
        with self._lock:
            before = len(self._records)
            self._records = [r for r in self._records if r["timestamp"] >= cutoff]
            removed = before - len(self._records)
        if removed > 0:
            logger.info(f"discard_rate_tracker cleanup: removed {removed} old entries")
        return removed


# ---------------------------------------------------------------------------
# Global singletons — imported by filter.py, admin.py, search_pipeline.py
# ---------------------------------------------------------------------------
filter_stats_tracker = FilterStatsTracker()
discard_rate_tracker = DiscardRateTracker()
