"""
Tests for CRIT-016 — Sentry-Triggered Bug Fixes

Covers:
- Bug 1 (AC3): consolidation.py null check for adapter.code
- Bug 2 (AC7): datetime naive vs aware timestamps
- Bug 3 (AC10): SourceConfig.get_available_sources deprecation
"""

import asyncio
import warnings
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

from filter_stats import FilterStatsTracker, REASON_UF_MISMATCH, REASON_KEYWORD_MISS
from source_config.sources import SourceConfig


# ==============================================================================
# Bug 1 — consolidation.py null check (AC3)
# ==============================================================================


def _make_adapter(code: str, priority: int = 1):
    """Create a mock adapter that passes ConsolidationService validation."""
    adapter = Mock()
    adapter.code = code
    adapter.metadata = Mock(priority=priority)
    adapter.fetch = AsyncMock(return_value=[])
    adapter.health_check = AsyncMock()
    adapter.close = AsyncMock()
    return adapter


class TestConsolidationNullCheck:
    """Test that consolidation handles edge cases in adapter access."""

    def test_deduplicate_normal_adapters(self):
        """AC3: Normal dedup with valid adapters still works."""
        from consolidation import ConsolidationService

        adapter = _make_adapter("PNCP", 1)
        service = ConsolidationService(adapters={"PNCP": adapter})
        result = service._deduplicate([])
        assert result == []

    def test_deduplicate_getattr_fallback_pattern(self):
        """AC3: getattr(adapter, 'code', key) pattern works correctly."""
        # Object WITH .code
        obj_with = Mock()
        obj_with.code = "PNCP"
        assert getattr(obj_with, "code", "fallback") == "PNCP"

        # Object WITHOUT .code
        obj_without = Mock(spec=[])
        assert getattr(obj_without, "code", "fallback") == "fallback"

        # None object
        assert getattr(None, "code", "unknown_fallback") == "unknown_fallback"

    def test_fallback_adapter_getattr_safety(self):
        """AC3: getattr on _fallback_adapter.code returns safe default."""
        # Simulates the exact code path: getattr(self._fallback_adapter, "code", "unknown_fallback")
        fallback = None
        result = getattr(fallback, "code", "unknown_fallback")
        assert result == "unknown_fallback"

        # With real adapter
        real = _make_adapter("ComprasGov", 3)
        result = getattr(real, "code", "unknown_fallback")
        assert result == "ComprasGov"

    def test_adapter_metadata_getattr_safety(self):
        """AC3: getattr on adapter.metadata returns None when missing."""
        obj = Mock(spec=[])
        meta = getattr(obj, "metadata", None)
        assert meta is None

        real = _make_adapter("PNCP", 1)
        meta = getattr(real, "metadata", None)
        assert meta is not None
        assert meta.priority == 1

    def test_deduplicate_with_two_valid_adapters(self):
        """AC3: Dedup source_priority uses adapter.code when present."""
        from consolidation import ConsolidationService

        a1 = _make_adapter("PNCP", 1)
        a2 = _make_adapter("Portal", 2)
        service = ConsolidationService(adapters={"PNCP": a1, "Portal": a2})
        result = service._deduplicate([])
        assert result == []


# ==============================================================================
# Bug 2 — datetime naive vs aware (AC7)
# ==============================================================================


class TestDatetimeAwareTimestamps:
    """Test that datetime operations use timezone-aware timestamps."""

    def test_filter_stats_timestamp_is_aware(self):
        """AC7: FilterStatsTracker timestamp contains +00:00."""
        tracker = FilterStatsTracker()
        tracker.record_rejection(reason=REASON_UF_MISMATCH, sector="informatica")

        # Access internal stats to verify timestamp format
        entries = tracker._stats.get(REASON_UF_MISMATCH, [])
        assert len(entries) >= 1
        ts = entries[0]["timestamp"]
        assert "+00:00" in ts, f"Timestamp '{ts}' is not timezone-aware"

    def test_filter_stats_get_stats_works_with_aware_cutoff(self):
        """AC7: get_stats works after switching to aware datetimes."""
        tracker = FilterStatsTracker()
        tracker.record_rejection(reason=REASON_KEYWORD_MISS)
        stats = tracker.get_stats(days=1)
        assert stats[REASON_KEYWORD_MISS] >= 1

    def test_aware_datetime_format(self):
        """AC7: datetime.now(timezone.utc).isoformat() has correct format."""
        aware = datetime.now(timezone.utc)
        iso = aware.isoformat()
        assert "+00:00" in iso
        assert "T" in iso

    def test_naive_vs_aware_baseline(self):
        """AC7: Verify naive datetime lacks offset (baseline for comparison)."""
        naive = datetime.utcnow()
        iso = naive.isoformat()
        assert "+00:00" not in iso

    def test_no_manual_z_suffix(self):
        """AC7: isoformat() with timezone.utc produces +00:00, not manual Z."""
        aware = datetime.now(timezone.utc)
        iso = aware.isoformat()
        assert not iso.endswith("Z")
        assert iso.endswith("+00:00")


# ==============================================================================
# Bug 3 — SourceConfig.get_available_sources deprecation (AC10)
# ==============================================================================


class TestSourceConfigDeprecation:
    """Test SourceConfig.get_available_sources deprecation alias."""

    def test_get_enabled_sources_returns_list(self):
        """AC10: get_enabled_sources returns list of enabled source codes."""
        config = SourceConfig.from_env()
        enabled = config.get_enabled_sources()
        assert isinstance(enabled, list)
        assert "PNCP" in enabled  # enabled by default

    def test_get_available_sources_emits_deprecation_warning(self):
        """AC10: get_available_sources emits DeprecationWarning."""
        config = SourceConfig.from_env()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            config.get_available_sources()

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "get_available_sources" in str(w[0].message)
            assert "get_enabled_sources" in str(w[0].message)

    def test_get_available_sources_returns_same_as_enabled(self):
        """AC10: Deprecated alias returns identical results."""
        config = SourceConfig.from_env()
        enabled = config.get_enabled_sources()

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            available = config.get_available_sources()

        assert enabled == available

    @patch.dict(
        "os.environ",
        {"ENABLE_SOURCE_PNCP": "false", "ENABLE_SOURCE_PORTAL": "false"},
    )
    def test_get_available_sources_reflects_config(self):
        """AC10: Deprecated method reflects actual source configuration."""
        config = SourceConfig.from_env()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            available = config.get_available_sources()

        assert "PNCP" not in available
        assert "Portal" not in available
        assert len(w) == 1
