"""GTM-RESILIENCE-B03: Tests for cache health metadata per key.

Covers all 10 ACs:
  AC1:  Migration adds 6 fields (validated structurally)
  AC2:  Fields populated on successful fetch
  AC3:  fail_streak incremented on failure
  AC4:  Correct exponential backoff
  AC5:  degraded_until respected
  AC6:  Structured JSONB coverage
  AC7:  fetch_duration_ms populated
  AC8:  Total backward compatibility
  AC9:  Health endpoint shows aggregated fail_streak
  AC10: Index for degraded keys query (migration-level; tested structurally)
"""

import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, Mock, AsyncMock, MagicMock

from search_cache import (
    calculate_backoff_minutes,
    save_to_cache,
    record_cache_fetch_failure,
    is_cache_key_degraded,
    get_from_cache,
    compute_search_hash,
)


# ============================================================================
# AC4: Correct exponential backoff
# ============================================================================


class TestCalculateBackoffMinutes:
    """AC4: calculate_backoff_minutes returns 0, 1, 5, 15, 30."""

    def test_streak_0_returns_0(self):
        assert calculate_backoff_minutes(0) == 0

    def test_streak_1_returns_1(self):
        assert calculate_backoff_minutes(1) == 1

    def test_streak_2_returns_5(self):
        assert calculate_backoff_minutes(2) == 5

    def test_streak_3_returns_15(self):
        assert calculate_backoff_minutes(3) == 15

    def test_streak_4_returns_30(self):
        assert calculate_backoff_minutes(4) == 30

    def test_streak_10_caps_at_30(self):
        assert calculate_backoff_minutes(10) == 30

    def test_negative_returns_0(self):
        assert calculate_backoff_minutes(-1) == 0


# ============================================================================
# AC2: Fields populated on successful fetch
# ============================================================================


class TestSaveToCacheHealthMetadata:
    """AC2: save_to_cache writes health metadata on successful fetch."""

    @pytest.mark.asyncio
    async def test_save_includes_health_fields(self):
        """AC2: Verify last_success_at, last_attempt_at, fail_streak=0, degraded_until=None."""
        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.upsert.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{"id": "test"}])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            await save_to_cache(
                user_id="user-b03",
                params={"setor_id": 1, "ufs": ["SP"]},
                results=[{"id": 1}],
                sources=["PNCP"],
            )

        call_args = mock_sb.upsert.call_args
        row = call_args[0][0]

        # B-03 health metadata fields
        assert "last_success_at" in row
        assert "last_attempt_at" in row
        assert row["fail_streak"] == 0
        assert row["degraded_until"] is None

    @pytest.mark.asyncio
    async def test_save_includes_coverage(self):
        """AC6: coverage JSONB is persisted when provided."""
        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.upsert.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{"id": "test"}])

        coverage = {"succeeded_ufs": ["SP", "RJ"], "failed_ufs": ["MA"], "total_requested": 3}

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            await save_to_cache(
                user_id="user-b03",
                params={"setor_id": 1, "ufs": ["SP", "RJ", "MA"]},
                results=[{"id": 1}],
                sources=["PNCP"],
                coverage=coverage,
            )

        row = mock_sb.upsert.call_args[0][0]
        assert row["coverage"] == coverage

    @pytest.mark.asyncio
    async def test_save_includes_fetch_duration(self):
        """AC7: fetch_duration_ms is persisted when provided."""
        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.upsert.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{"id": "test"}])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            await save_to_cache(
                user_id="user-b03",
                params={"setor_id": 1, "ufs": ["SP"]},
                results=[{"id": 1}],
                sources=["PNCP"],
                fetch_duration_ms=1500,
            )

        row = mock_sb.upsert.call_args[0][0]
        assert row["fetch_duration_ms"] == 1500

    @pytest.mark.asyncio
    async def test_save_omits_optional_fields_when_none(self):
        """AC7/AC6: When not provided, coverage and fetch_duration_ms are not in row."""
        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.upsert.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{"id": "test"}])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            await save_to_cache(
                user_id="user-b03",
                params={"setor_id": 1, "ufs": ["SP"]},
                results=[{"id": 1}],
                sources=["PNCP"],
            )

        row = mock_sb.upsert.call_args[0][0]
        assert "coverage" not in row
        assert "fetch_duration_ms" not in row


# ============================================================================
# AC3: fail_streak incremented on failure
# ============================================================================


class TestRecordCacheFetchFailure:
    """AC3: record_cache_fetch_failure increments fail_streak."""

    def _mock_supabase(self, current_fail_streak: int = 0):
        """Create a mock Supabase client that returns current fail_streak on select."""
        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.gt.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.update.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{"fail_streak": current_fail_streak}])
        return mock_sb

    @pytest.mark.asyncio
    async def test_first_failure_sets_streak_1(self):
        """First failure: fail_streak=0→1, degraded_until=now+1min."""
        mock_sb = self._mock_supabase(current_fail_streak=0)

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await record_cache_fetch_failure("user-1", "hash123")

        assert result["fail_streak"] == 1
        # Verify update was called with streak=1
        update_args = mock_sb.update.call_args[0][0]
        assert update_args["fail_streak"] == 1
        assert update_args["degraded_until"] is not None

    @pytest.mark.asyncio
    async def test_third_failure_sets_streak_3(self):
        """Third failure: fail_streak=2→3, degraded for 15min."""
        mock_sb = self._mock_supabase(current_fail_streak=2)

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await record_cache_fetch_failure("user-1", "hash123")

        assert result["fail_streak"] == 3
        update_args = mock_sb.update.call_args[0][0]
        assert update_args["fail_streak"] == 3

    @pytest.mark.asyncio
    async def test_key_not_found_returns_empty(self):
        """No cache key → returns empty dict."""
        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await record_cache_fetch_failure("user-1", "nonexistent")

        assert result == {}

    @pytest.mark.asyncio
    async def test_multiple_failures_accumulate(self):
        """Simulate 3 sequential failures."""
        # Each call reads the streak and increments
        streaks = [0, 1, 2]
        call_idx = {"idx": 0}

        def make_execute():
            mock_resp = Mock()
            mock_resp.data = [{"fail_streak": streaks[call_idx["idx"]]}]
            call_idx["idx"] += 1
            return mock_resp

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.update.return_value = mock_sb
        mock_sb.execute.side_effect = [
            # Call 1: select returns 0, update succeeds
            Mock(data=[{"fail_streak": 0}]),  # select
            Mock(data=[]),  # update
            # Call 2: select returns 1, update succeeds
            Mock(data=[{"fail_streak": 1}]),  # select
            Mock(data=[]),  # update
            # Call 3: select returns 2, update succeeds
            Mock(data=[{"fail_streak": 2}]),  # select
            Mock(data=[]),  # update
        ]

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            r1 = await record_cache_fetch_failure("user-1", "hash123")
            r2 = await record_cache_fetch_failure("user-1", "hash123")
            r3 = await record_cache_fetch_failure("user-1", "hash123")

        assert r1["fail_streak"] == 1
        assert r2["fail_streak"] == 2
        assert r3["fail_streak"] == 3


# ============================================================================
# AC5: degraded_until respected
# ============================================================================


class TestIsCacheKeyDegraded:
    """AC5: is_cache_key_degraded returns True/False based on degraded_until."""

    @pytest.mark.asyncio
    async def test_degraded_in_future_returns_true(self):
        """degraded_until 10min in future → True."""
        future = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{"degraded_until": future}])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            assert await is_cache_key_degraded("user-1", "hash123") is True

    @pytest.mark.asyncio
    async def test_degraded_in_past_returns_false(self):
        """degraded_until 10min in past → False."""
        past = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{"degraded_until": past}])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            assert await is_cache_key_degraded("user-1", "hash123") is False

    @pytest.mark.asyncio
    async def test_no_degraded_until_returns_false(self):
        """No degraded_until field → False."""
        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{"degraded_until": None}])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            assert await is_cache_key_degraded("user-1", "hash123") is False

    @pytest.mark.asyncio
    async def test_key_not_found_returns_false(self):
        """No cache key → False (not degraded)."""
        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            assert await is_cache_key_degraded("user-1", "nonexistent") is False


# ============================================================================
# AC8: Total backward compatibility
# ============================================================================


class TestBackwardCompatibility:
    """AC8: Existing entries without new fields continue working."""

    @pytest.mark.asyncio
    async def test_get_from_cache_works_without_health_fields(self):
        """Pre-migration rows (no health fields) → get_from_cache returns valid data."""
        now = datetime.now(timezone.utc)
        fetched_at = (now - timedelta(hours=2)).isoformat()

        # Simulate pre-migration row — only original fields
        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{
            "results": [{"id": 1, "objeto": "Legacy bid"}],
            "total_results": 1,
            "sources_json": ["PNCP"],
            "fetched_at": fetched_at,
            "created_at": fetched_at,
            # NOTE: No last_success_at, last_attempt_at, fail_streak, etc.
        }])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await get_from_cache(
                user_id="user-legacy",
                params={"setor_id": 1, "ufs": ["SP"]},
            )

        assert result is not None
        assert result["results"] == [{"id": 1, "objeto": "Legacy bid"}]
        assert result["is_stale"] is False

    @pytest.mark.asyncio
    async def test_save_to_cache_compatible_with_old_schema(self):
        """save_to_cache without optional params still works (no crash on missing columns)."""
        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.upsert.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{"id": "test"}])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await save_to_cache(
                user_id="user-old",
                params={"setor_id": 1, "ufs": ["RJ"]},
                results=[{"id": 2}],
                sources=["PNCP"],
                # No fetch_duration_ms, no coverage
            )

        assert result["success"] is True
        row = mock_sb.upsert.call_args[0][0]
        # Health fields are still set (with defaults)
        assert row["fail_streak"] == 0
        assert row["degraded_until"] is None


# ============================================================================
# AC9: Health endpoint shows aggregated fail_streak
# ============================================================================


class TestHealthEndpointDegradation:
    """AC9: GET /v1/health/cache includes degradation metrics."""

    @pytest.mark.asyncio
    async def test_health_includes_degradation_section(self):
        """Health response includes degraded_keys_count and avg_fail_streak."""
        from routes.health import _check_cache_degradation

        now_iso = datetime.now(timezone.utc).isoformat()

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.gt.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb

        # First call: count degraded keys (returns count=2)
        degraded_mock = Mock()
        degraded_mock.count = 2
        degraded_mock.data = []

        # Second call: get fail_streaks > 0 (returns 3 entries)
        streak_mock = Mock()
        streak_mock.data = [
            {"fail_streak": 1},
            {"fail_streak": 3},
            {"fail_streak": 5},
        ]

        # Third call: priority distribution (B-02 AC10)
        priority_mock = Mock()
        priority_mock.data = [
            {"priority": "hot"},
            {"priority": "cold"},
        ]

        mock_sb.execute.side_effect = [degraded_mock, streak_mock, priority_mock]

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await _check_cache_degradation()

        assert result["degraded_keys_count"] == 2
        assert result["avg_fail_streak"] == 3.0  # (1+3+5)/3
        assert result["keys_with_failures"] == 3
        assert "priority_distribution" in result

    @pytest.mark.asyncio
    async def test_health_degradation_handles_empty(self):
        """No degraded keys → zeroes."""
        from routes.health import _check_cache_degradation

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.gt.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb

        empty_count = Mock()
        empty_count.count = 0
        empty_count.data = []

        empty_streaks = Mock()
        empty_streaks.data = []

        # B-02 AC10: priority distribution (empty)
        empty_priority = Mock()
        empty_priority.data = []

        mock_sb.execute.side_effect = [empty_count, empty_streaks, empty_priority]

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await _check_cache_degradation()

        assert result["degraded_keys_count"] == 0
        assert result["avg_fail_streak"] == 0.0
        assert result["keys_with_failures"] == 0

    @pytest.mark.asyncio
    async def test_health_degradation_handles_db_error(self):
        """Supabase error → graceful fallback with zeroes."""
        from routes.health import _check_cache_degradation

        with patch("supabase_client.get_supabase", side_effect=Exception("DB unavailable")):
            result = await _check_cache_degradation()

        assert result["degraded_keys_count"] == 0
        assert result["avg_fail_streak"] == 0.0
        assert "error" in result


# ============================================================================
# AC6: Structured JSONB coverage (integration-level)
# ============================================================================


class TestCoverageStructure:
    """AC6: coverage field stores proper JSONB structure."""

    def test_coverage_structure_is_valid(self):
        """Verify coverage dict has expected shape."""
        coverage = {
            "succeeded_ufs": ["SP", "RJ"],
            "failed_ufs": ["MA"],
            "total_requested": 3,
        }

        # Validate JSON serializable
        serialized = json.dumps(coverage)
        deserialized = json.loads(serialized)

        assert deserialized["succeeded_ufs"] == ["SP", "RJ"]
        assert deserialized["failed_ufs"] == ["MA"]
        assert deserialized["total_requested"] == 3


# ============================================================================
# AC1/AC10: Migration structure validation
# ============================================================================


class TestMigrationStructure:
    """AC1/AC10: Validate migration SQL file exists and has correct content."""

    def test_migration_file_exists(self):
        """Migration 031 SQL file exists."""
        from pathlib import Path
        migration = Path("D:/pncp-poc/supabase/migrations/031_cache_health_metadata.sql")
        assert migration.exists(), "Migration file 031_cache_health_metadata.sql not found"

    def test_migration_contains_all_fields(self):
        """Migration adds all 6 required fields."""
        from pathlib import Path
        sql = Path("D:/pncp-poc/supabase/migrations/031_cache_health_metadata.sql").read_text()

        required_fields = [
            "last_success_at",
            "last_attempt_at",
            "fail_streak",
            "degraded_until",
            "coverage",
            "fetch_duration_ms",
        ]
        for field in required_fields:
            assert field in sql, f"Missing field '{field}' in migration"

    def test_migration_contains_index(self):
        """AC10: Migration creates degraded index."""
        from pathlib import Path
        sql = Path("D:/pncp-poc/supabase/migrations/031_cache_health_metadata.sql").read_text()
        assert "idx_search_cache_degraded" in sql
        assert "degraded_until" in sql
