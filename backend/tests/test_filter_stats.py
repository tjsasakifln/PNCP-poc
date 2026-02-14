"""Tests for STORY-248 filter stats tracking (AC9, AC10).

Tests the FilterStatsTracker class and the /admin/filter-stats endpoint.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from filter_stats import (
    FilterStatsTracker,
    filter_stats_tracker,
    REASON_KEYWORD_MISS,
    REASON_EXCLUSION_HIT,
    REASON_LLM_REJECT,
    REASON_DENSITY_LOW,
    REASON_VALUE_EXCEED,
    REASON_UF_MISMATCH,
    REASON_STATUS_MISMATCH,
    ALL_REASON_CODES,
)


class TestFilterStatsTracker:
    """Unit tests for the in-memory FilterStatsTracker."""

    def test_record_and_get_single(self):
        """Should record a single rejection and return correct count."""
        tracker = FilterStatsTracker()
        tracker.record_rejection(REASON_KEYWORD_MISS, sector="vestuario")

        stats = tracker.get_stats(days=7)
        assert stats[REASON_KEYWORD_MISS] == 1
        assert stats["total_rejections"] == 1

    def test_record_and_get_multiple_reasons(self):
        """Should track different reason codes independently."""
        tracker = FilterStatsTracker()
        tracker.record_rejection(REASON_KEYWORD_MISS, sector="vestuario")
        tracker.record_rejection(REASON_EXCLUSION_HIT, sector="alimentos")
        tracker.record_rejection(REASON_LLM_REJECT, sector="vestuario")

        stats = tracker.get_stats(days=7)
        assert stats[REASON_KEYWORD_MISS] == 1
        assert stats[REASON_EXCLUSION_HIT] == 1
        assert stats[REASON_LLM_REJECT] == 1
        assert stats["total_rejections"] == 3

    def test_empty_stats(self):
        """Should return zero counts when no rejections recorded."""
        tracker = FilterStatsTracker()
        stats = tracker.get_stats()

        assert stats["total_rejections"] == 0
        assert stats["period_days"] == 7
        for reason in ALL_REASON_CODES:
            assert stats[reason] == 0

    def test_all_reason_codes_present_in_stats(self):
        """Stats dict should always contain all defined reason codes."""
        tracker = FilterStatsTracker()
        stats = tracker.get_stats()

        for reason in ALL_REASON_CODES:
            assert reason in stats, f"Missing reason code: {reason}"
        assert "total_rejections" in stats
        assert "period_days" in stats

    def test_description_preview_truncated(self):
        """Should truncate description preview to 100 chars."""
        tracker = FilterStatsTracker()
        long_desc = "A" * 200
        tracker.record_rejection(REASON_KEYWORD_MISS, description_preview=long_desc)

        # Access internal state to verify truncation
        entries = tracker._stats[REASON_KEYWORD_MISS]
        assert len(entries) == 1
        assert len(entries[0]["preview"]) == 100

    def test_sector_stored(self):
        """Should store sector info in the rejection entry."""
        tracker = FilterStatsTracker()
        tracker.record_rejection(REASON_UF_MISMATCH, sector="tecnologia")

        entries = tracker._stats[REASON_UF_MISMATCH]
        assert len(entries) == 1
        assert entries[0]["sector"] == "tecnologia"

    def test_get_stats_respects_days_filter(self):
        """Should only count entries within the specified day range."""
        tracker = FilterStatsTracker()

        # Record one now
        tracker.record_rejection(REASON_KEYWORD_MISS)

        # Manually insert an old entry (8 days ago)
        old_timestamp = (datetime.utcnow() - timedelta(days=8)).isoformat()
        tracker._stats[REASON_EXCLUSION_HIT].append({
            "timestamp": old_timestamp,
            "reason": REASON_EXCLUSION_HIT,
            "sector": None,
        })

        stats = tracker.get_stats(days=7)
        assert stats[REASON_KEYWORD_MISS] == 1
        assert stats[REASON_EXCLUSION_HIT] == 0  # Too old
        assert stats["total_rejections"] == 1

    def test_get_stats_custom_days(self):
        """Should respect custom days parameter."""
        tracker = FilterStatsTracker()
        tracker.record_rejection(REASON_KEYWORD_MISS)

        stats = tracker.get_stats(days=30)
        assert stats["period_days"] == 30
        assert stats[REASON_KEYWORD_MISS] == 1

    def test_cleanup_old_removes_stale_entries(self):
        """cleanup_old should remove entries beyond retention period."""
        tracker = FilterStatsTracker(retention_days=7)

        # Add a current entry
        tracker.record_rejection(REASON_KEYWORD_MISS)

        # Manually insert an old entry (10 days ago)
        old_timestamp = (datetime.utcnow() - timedelta(days=10)).isoformat()
        tracker._stats[REASON_EXCLUSION_HIT].append({
            "timestamp": old_timestamp,
            "reason": REASON_EXCLUSION_HIT,
            "sector": None,
        })

        removed = tracker.cleanup_old()
        assert removed == 1

        # Current entry should still be there
        assert len(tracker._stats[REASON_KEYWORD_MISS]) == 1
        # Old entry should be gone
        assert len(tracker._stats[REASON_EXCLUSION_HIT]) == 0

    def test_cleanup_old_no_stale(self):
        """cleanup_old should return 0 when no stale entries exist."""
        tracker = FilterStatsTracker(retention_days=7)
        tracker.record_rejection(REASON_KEYWORD_MISS)

        removed = tracker.cleanup_old()
        assert removed == 0

    def test_multiple_entries_same_reason(self):
        """Should correctly count multiple entries for the same reason."""
        tracker = FilterStatsTracker()
        for _ in range(5):
            tracker.record_rejection(REASON_DENSITY_LOW)

        stats = tracker.get_stats()
        assert stats[REASON_DENSITY_LOW] == 5
        assert stats["total_rejections"] == 5

    def test_thread_safety_basic(self):
        """Basic test that concurrent access does not raise exceptions."""
        import threading

        tracker = FilterStatsTracker()
        errors = []

        def record_many():
            try:
                for _ in range(100):
                    tracker.record_rejection(REASON_KEYWORD_MISS)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=record_many) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        stats = tracker.get_stats()
        assert stats[REASON_KEYWORD_MISS] == 400

    def test_record_with_no_optional_fields(self):
        """Should work with only the required reason parameter."""
        tracker = FilterStatsTracker()
        tracker.record_rejection(REASON_VALUE_EXCEED)

        stats = tracker.get_stats()
        assert stats[REASON_VALUE_EXCEED] == 1

        entries = tracker._stats[REASON_VALUE_EXCEED]
        assert "preview" not in entries[0]
        assert entries[0]["sector"] is None


class TestGlobalTrackerSingleton:
    """Tests for the global filter_stats_tracker singleton."""

    def test_singleton_exists(self):
        """The module should export a pre-initialized tracker."""
        assert filter_stats_tracker is not None
        assert isinstance(filter_stats_tracker, FilterStatsTracker)

    def test_singleton_records(self):
        """The global tracker should accept record calls."""
        # Use a fresh tracker to avoid test pollution
        tracker = FilterStatsTracker()
        tracker.record_rejection(REASON_STATUS_MISMATCH)
        stats = tracker.get_stats()
        assert stats[REASON_STATUS_MISMATCH] == 1


class TestReasonCodeConstants:
    """Tests for reason code constants."""

    def test_all_reason_codes_are_strings(self):
        for code in ALL_REASON_CODES:
            assert isinstance(code, str)

    def test_all_reason_codes_unique(self):
        assert len(ALL_REASON_CODES) == len(set(ALL_REASON_CODES))

    def test_expected_codes_present(self):
        expected = {
            "keyword_miss",
            "exclusion_hit",
            "llm_reject",
            "density_low",
            "value_exceed",
            "uf_mismatch",
            "status_mismatch",
        }
        assert set(ALL_REASON_CODES) == expected
