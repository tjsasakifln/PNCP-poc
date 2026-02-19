"""GTM-RESILIENCE-B02: Tests for hot/warm/cold cache priority system.

Covers all 10 ACs:
  AC1:  CachePriority enum with 3 levels
  AC2:  classify_priority deterministic classification
  AC3:  Migration adds priority, access_count, last_accessed_at fields
  AC4:  access_count incremented on cache hit
  AC5:  Reclassification after access_count update
  AC6:  Redis TTL differentiated by priority
  AC7:  Smart eviction (cold → warm → hot)
  AC8:  cache_priority field in get_from_cache() return
  AC9:  Proactive refresh for hot keys near expiry
  AC10: priority_distribution in health endpoint
"""

import json
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock, MagicMock

from search_cache import (
    CachePriority,
    classify_priority,
    REDIS_TTL_BY_PRIORITY,
    CACHE_FRESH_HOURS,
    save_to_cache,
    get_from_cache,
    compute_search_hash,
    _save_to_redis,
    _process_cache_hit,
    CacheLevel,
)


# ============================================================================
# AC1: CachePriority enum with 3 levels
# ============================================================================


class TestCachePriorityEnum:
    """AC1: Verify CachePriority enum has correct values."""

    def test_enum_has_three_values(self):
        assert len(CachePriority) == 3

    def test_hot_value(self):
        assert CachePriority.HOT.value == "hot"

    def test_warm_value(self):
        assert CachePriority.WARM.value == "warm"

    def test_cold_value(self):
        assert CachePriority.COLD.value == "cold"

    def test_is_str_enum(self):
        assert isinstance(CachePriority.HOT, str)
        assert CachePriority.HOT == "hot"


# ============================================================================
# AC2: classify_priority deterministic classification
# ============================================================================


class TestClassifyPriority:
    """AC2: 6 scenarios for classify_priority."""

    def test_hot_by_frequency(self):
        """access_count >= 3 with recent access → HOT."""
        last = datetime.now(timezone.utc) - timedelta(hours=1)
        assert classify_priority(3, last) == CachePriority.HOT

    def test_hot_by_saved_search(self):
        """Saved search with recent access → HOT."""
        last = datetime.now(timezone.utc) - timedelta(hours=2)
        assert classify_priority(0, last, is_saved_search=True) == CachePriority.HOT

    def test_warm_one_access(self):
        """1 access in 24h → WARM."""
        last = datetime.now(timezone.utc) - timedelta(hours=12)
        assert classify_priority(1, last) == CachePriority.WARM

    def test_warm_two_accesses(self):
        """2 accesses in 24h → WARM."""
        last = datetime.now(timezone.utc) - timedelta(hours=6)
        assert classify_priority(2, last) == CachePriority.WARM

    def test_cold_no_access(self):
        """No access → COLD."""
        assert classify_priority(0, None) == CachePriority.COLD

    def test_cold_old_access(self):
        """Access older than 24h → COLD regardless of count."""
        old = datetime.now(timezone.utc) - timedelta(hours=25)
        assert classify_priority(10, old) == CachePriority.COLD

    def test_boundary_exactly_24h(self):
        """Access at exactly 24h boundary → still within window."""
        boundary = datetime.now(timezone.utc) - timedelta(hours=24)
        assert classify_priority(1, boundary) == CachePriority.WARM

    def test_saved_search_old_access_cold(self):
        """Saved search with old access → COLD (recent_access required)."""
        old = datetime.now(timezone.utc) - timedelta(hours=25)
        assert classify_priority(0, old, is_saved_search=True) == CachePriority.COLD

    def test_naive_datetime_treated_as_utc(self):
        """Naive datetime is treated as UTC."""
        last = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        assert classify_priority(3, last) == CachePriority.HOT


# ============================================================================
# AC3: Migration structure validation
# ============================================================================


class TestMigrationStructure:
    """AC3: Verify migration file exists and has correct structure."""

    def test_migration_file_exists(self):
        migration = Path(__file__).parent.parent.parent / "supabase" / "migrations" / "032_cache_priority_fields.sql"
        assert migration.exists(), "032_cache_priority_fields.sql missing"

    def test_migration_adds_priority_column(self):
        migration = Path(__file__).parent.parent.parent / "supabase" / "migrations" / "032_cache_priority_fields.sql"
        content = migration.read_text()
        assert "priority TEXT NOT NULL DEFAULT 'cold'" in content

    def test_migration_adds_access_count(self):
        migration = Path(__file__).parent.parent.parent / "supabase" / "migrations" / "032_cache_priority_fields.sql"
        content = migration.read_text()
        assert "access_count INTEGER NOT NULL DEFAULT 0" in content

    def test_migration_adds_last_accessed_at(self):
        migration = Path(__file__).parent.parent.parent / "supabase" / "migrations" / "032_cache_priority_fields.sql"
        content = migration.read_text()
        assert "last_accessed_at TIMESTAMPTZ" in content

    def test_migration_has_smart_eviction(self):
        migration = Path(__file__).parent.parent.parent / "supabase" / "migrations" / "032_cache_priority_fields.sql"
        content = migration.read_text()
        assert "OFFSET 5" not in content, "Old FIFO limit should be replaced"
        assert "entry_count - 10" in content or "LIMIT (entry_count - 10)" in content

    def test_migration_priority_ordering(self):
        migration = Path(__file__).parent.parent.parent / "supabase" / "migrations" / "032_cache_priority_fields.sql"
        content = migration.read_text()
        assert "'cold' THEN 0" in content
        assert "'warm' THEN 1" in content
        assert "'hot'  THEN 2" in content or "'hot' THEN 2" in content


# ============================================================================
# AC4: access_count incremented on cache hit
# ============================================================================


class TestAccessCountIncrement:
    """AC4: get_from_cache() updates access_count and last_accessed_at."""

    @pytest.mark.asyncio
    async def test_access_count_incremented_on_hit(self):
        """Supabase hit → access_count + 1, last_accessed_at updated."""
        now = datetime.now(timezone.utc)
        fetched_at = (now - timedelta(hours=1)).isoformat()

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.update.return_value = mock_sb
        mock_sb.gt.return_value = mock_sb

        # First call: _get_from_supabase (read)
        # Second call: _increment_and_reclassify (read current state)
        read_calls = [
            # _get_from_supabase response
            Mock(data=[{
                "results": [{"id": 1}],
                "total_results": 1,
                "sources_json": ["PNCP"],
                "fetched_at": fetched_at,
                "created_at": fetched_at,
                "priority": "cold",
                "access_count": 0,
                "last_accessed_at": None,
            }]),
            # _increment_and_reclassify read response
            Mock(data=[{
                "access_count": 0,
                "last_accessed_at": None,
                "priority": "cold",
            }]),
            # _increment_and_reclassify update response
            Mock(data=[{"id": "test"}]),
        ]
        mock_sb.execute.side_effect = read_calls

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await get_from_cache(
                user_id="user-b02",
                params={"setor_id": 1, "ufs": ["SP"]},
            )

        assert result is not None
        assert result["results"] == [{"id": 1}]

        # Verify update was called with incremented access_count
        update_calls = [c for c in mock_sb.update.call_args_list]
        assert len(update_calls) == 1
        update_data = update_calls[0][0][0]
        assert update_data["access_count"] == 1
        assert "last_accessed_at" in update_data

    @pytest.mark.asyncio
    async def test_three_accesses_promotes_to_warm(self):
        """After 3 accesses in 24h, priority should change."""
        now = datetime.now(timezone.utc)
        fetched_at = (now - timedelta(hours=1)).isoformat()

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.update.return_value = mock_sb
        mock_sb.gt.return_value = mock_sb

        read_calls = [
            Mock(data=[{
                "results": [{"id": 1}],
                "total_results": 1,
                "sources_json": ["PNCP"],
                "fetched_at": fetched_at,
                "created_at": fetched_at,
                "priority": "cold",
                "access_count": 2,  # Already accessed 2x
                "last_accessed_at": (now - timedelta(hours=1)).isoformat(),
            }]),
            Mock(data=[{
                "access_count": 2,
                "last_accessed_at": (now - timedelta(hours=1)).isoformat(),
                "priority": "cold",
            }]),
            Mock(data=[{"id": "test"}]),
        ]
        mock_sb.execute.side_effect = read_calls

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await get_from_cache(
                user_id="user-b02",
                params={"setor_id": 1, "ufs": ["SP"]},
            )

        assert result is not None
        # Should be reclassified to HOT (3 accesses)
        assert result["cache_priority"] == CachePriority.HOT

        update_data = mock_sb.update.call_args[0][0]
        assert update_data["access_count"] == 3
        assert update_data["priority"] == "hot"


# ============================================================================
# AC5: Reclassification after access_count update
# ============================================================================


class TestReclassification:
    """AC5: Priority changes when access_count crosses threshold."""

    @pytest.mark.asyncio
    async def test_cold_to_warm_on_first_access(self):
        """Cold entry with 0 accesses → warm after first access."""
        now = datetime.now(timezone.utc)
        fetched_at = (now - timedelta(hours=2)).isoformat()

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.update.return_value = mock_sb
        mock_sb.gt.return_value = mock_sb

        read_calls = [
            Mock(data=[{
                "results": [{"id": 1}],
                "total_results": 1,
                "sources_json": ["PNCP"],
                "fetched_at": fetched_at,
                "created_at": fetched_at,
                "priority": "cold",
                "access_count": 0,
                "last_accessed_at": None,
            }]),
            Mock(data=[{
                "access_count": 0,
                "last_accessed_at": None,
                "priority": "cold",
            }]),
            Mock(data=[{"id": "test"}]),
        ]
        mock_sb.execute.side_effect = read_calls

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await get_from_cache(
                user_id="user-b02",
                params={"setor_id": 1, "ufs": ["RJ"]},
            )

        update_data = mock_sb.update.call_args[0][0]
        assert update_data["priority"] == "warm"

    @pytest.mark.asyncio
    async def test_no_reclassification_when_unchanged(self):
        """Warm entry stays warm → priority field NOT in update."""
        now = datetime.now(timezone.utc)
        fetched_at = (now - timedelta(hours=2)).isoformat()

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.update.return_value = mock_sb
        mock_sb.gt.return_value = mock_sb

        read_calls = [
            Mock(data=[{
                "results": [{"id": 1}],
                "total_results": 1,
                "sources_json": ["PNCP"],
                "fetched_at": fetched_at,
                "created_at": fetched_at,
                "priority": "warm",
                "access_count": 1,
                "last_accessed_at": (now - timedelta(hours=1)).isoformat(),
            }]),
            Mock(data=[{
                "access_count": 1,
                "last_accessed_at": (now - timedelta(hours=1)).isoformat(),
                "priority": "warm",
            }]),
            Mock(data=[{"id": "test"}]),
        ]
        mock_sb.execute.side_effect = read_calls

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await get_from_cache(
                user_id="user-b02",
                params={"setor_id": 1, "ufs": ["MG"]},
            )

        update_data = mock_sb.update.call_args[0][0]
        # access_count should be 2 (warm → still warm)
        assert update_data["access_count"] == 2
        assert "priority" not in update_data


# ============================================================================
# AC6: Redis TTL differentiated by priority
# ============================================================================


class TestRedisTTLByPriority:
    """AC6: _save_to_redis uses priority-based TTL."""

    def test_ttl_constants(self):
        assert REDIS_TTL_BY_PRIORITY[CachePriority.HOT] == 7200
        assert REDIS_TTL_BY_PRIORITY[CachePriority.WARM] == 21600
        assert REDIS_TTL_BY_PRIORITY[CachePriority.COLD] == 3600

    def test_hot_entry_gets_2h_ttl(self):
        """Saving with priority=HOT uses 7200s TTL."""
        mock_cache = MagicMock()
        with patch("redis_pool.get_fallback_cache", return_value=mock_cache):
            _save_to_redis("test_key", [{"id": 1}], ["PNCP"], priority=CachePriority.HOT)

        mock_cache.setex.assert_called_once()
        args = mock_cache.setex.call_args[0]
        assert args[1] == 7200  # TTL

    def test_cold_entry_gets_1h_ttl(self):
        """Saving with priority=COLD uses 3600s TTL."""
        mock_cache = MagicMock()
        with patch("redis_pool.get_fallback_cache", return_value=mock_cache):
            _save_to_redis("test_key", [{"id": 1}], ["PNCP"], priority=CachePriority.COLD)

        args = mock_cache.setex.call_args[0]
        assert args[1] == 3600

    def test_warm_entry_gets_6h_ttl(self):
        """Saving with priority=WARM uses 21600s TTL."""
        mock_cache = MagicMock()
        with patch("redis_pool.get_fallback_cache", return_value=mock_cache):
            _save_to_redis("test_key", [{"id": 1}], ["PNCP"], priority=CachePriority.WARM)

        args = mock_cache.setex.call_args[0]
        assert args[1] == 21600

    def test_default_priority_is_cold(self):
        """Default priority = COLD → 3600s TTL."""
        mock_cache = MagicMock()
        with patch("redis_pool.get_fallback_cache", return_value=mock_cache):
            _save_to_redis("test_key", [{"id": 1}], ["PNCP"])

        args = mock_cache.setex.call_args[0]
        assert args[1] == 3600


# ============================================================================
# AC7: Smart eviction (validated via migration — see TestMigrationStructure)
# ============================================================================


class TestSmartEviction:
    """AC7: Eviction logic is in the trigger (tested via migration structure above).
    These tests verify the Python-side expectations.
    """

    def test_eviction_limit_is_10(self):
        """Migration evicts beyond 10 entries (not 5)."""
        migration = Path(__file__).parent.parent.parent / "supabase" / "migrations" / "032_cache_priority_fields.sql"
        content = migration.read_text()
        assert "entry_count > 10" in content
        assert "entry_count - 10" in content


# ============================================================================
# AC8: cache_priority field in return
# ============================================================================


class TestCachePriorityInReturn:
    """AC8: get_from_cache() result includes cache_priority."""

    def test_process_cache_hit_includes_priority(self):
        """_process_cache_hit returns cache_priority from data."""
        now = datetime.now(timezone.utc)
        data = {
            "results": [{"id": 1}],
            "sources_json": ["PNCP"],
            "fetched_at": (now - timedelta(hours=1)).isoformat(),
            "priority": "hot",
            "access_count": 5,
            "last_accessed_at": (now - timedelta(minutes=30)).isoformat(),
        }
        result = _process_cache_hit(data, "abc123hash", CacheLevel.SUPABASE)
        assert result is not None
        assert "cache_priority" in result
        assert result["cache_priority"] == CachePriority.HOT

    def test_process_cache_hit_defaults_to_cold(self):
        """Missing priority data → defaults to COLD."""
        now = datetime.now(timezone.utc)
        data = {
            "results": [{"id": 1}],
            "sources_json": ["PNCP"],
            "fetched_at": (now - timedelta(hours=1)).isoformat(),
        }
        result = _process_cache_hit(data, "abc123hash", CacheLevel.REDIS)
        assert result is not None
        assert result["cache_priority"] == CachePriority.COLD

    def test_process_cache_hit_warm_priority(self):
        """Priority=warm in data → CachePriority.WARM in result."""
        now = datetime.now(timezone.utc)
        data = {
            "results": [{"id": 1}],
            "sources_json": ["PNCP"],
            "fetched_at": (now - timedelta(hours=2)).isoformat(),
            "priority": "warm",
            "access_count": 2,
            "last_accessed_at": (now - timedelta(hours=1)).isoformat(),
        }
        result = _process_cache_hit(data, "abc123hash", CacheLevel.SUPABASE)
        assert result["cache_priority"] == CachePriority.WARM


# ============================================================================
# AC9: Proactive refresh for hot keys near expiry
# ============================================================================


class TestProactiveRefresh:
    """AC9: Hot keys within 30min of expiry trigger background revalidation."""

    @pytest.mark.asyncio
    async def test_hot_key_near_expiry_triggers_revalidation(self):
        """Hot key at 5.5h age (30min from fresh→stale) → proactive refresh."""
        now = datetime.now(timezone.utc)
        fetched_at = (now - timedelta(hours=5, minutes=31)).isoformat()

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.update.return_value = mock_sb
        mock_sb.gt.return_value = mock_sb

        read_calls = [
            Mock(data=[{
                "results": [{"id": 1}],
                "total_results": 1,
                "sources_json": ["PNCP"],
                "fetched_at": fetched_at,
                "created_at": fetched_at,
                "priority": "hot",
                "access_count": 5,
                "last_accessed_at": (now - timedelta(minutes=10)).isoformat(),
            }]),
            Mock(data=[{
                "access_count": 5,
                "last_accessed_at": (now - timedelta(minutes=10)).isoformat(),
                "priority": "hot",
            }]),
            Mock(data=[{"id": "test"}]),
        ]
        mock_sb.execute.side_effect = read_calls

        with patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("search_cache.trigger_background_revalidation", new_callable=AsyncMock, return_value=True) as mock_trigger:
            result = await get_from_cache(
                user_id="user-b02",
                params={"setor_id": 1, "ufs": ["SP"]},
            )

        assert result is not None
        mock_trigger.assert_called_once()

    @pytest.mark.asyncio
    async def test_cold_key_near_expiry_no_revalidation(self):
        """Cold key near expiry → no proactive refresh."""
        now = datetime.now(timezone.utc)
        fetched_at = (now - timedelta(hours=5, minutes=31)).isoformat()

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.update.return_value = mock_sb
        mock_sb.gt.return_value = mock_sb

        read_calls = [
            Mock(data=[{
                "results": [{"id": 1}],
                "total_results": 1,
                "sources_json": ["PNCP"],
                "fetched_at": fetched_at,
                "created_at": fetched_at,
                "priority": "cold",
                "access_count": 0,
                "last_accessed_at": None,
            }]),
            Mock(data=[{
                "access_count": 0,
                "last_accessed_at": None,
                "priority": "cold",
            }]),
            Mock(data=[{"id": "test"}]),
        ]
        mock_sb.execute.side_effect = read_calls

        with patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("search_cache.trigger_background_revalidation", new_callable=AsyncMock, return_value=True) as mock_trigger:
            result = await get_from_cache(
                user_id="user-b02",
                params={"setor_id": 1, "ufs": ["SP"]},
            )

        assert result is not None
        mock_trigger.assert_not_called()

    @pytest.mark.asyncio
    async def test_hot_key_fresh_no_revalidation(self):
        """Hot key at 2h age (far from expiry) → no proactive refresh."""
        now = datetime.now(timezone.utc)
        fetched_at = (now - timedelta(hours=2)).isoformat()

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.update.return_value = mock_sb
        mock_sb.gt.return_value = mock_sb

        read_calls = [
            Mock(data=[{
                "results": [{"id": 1}],
                "total_results": 1,
                "sources_json": ["PNCP"],
                "fetched_at": fetched_at,
                "created_at": fetched_at,
                "priority": "hot",
                "access_count": 5,
                "last_accessed_at": (now - timedelta(minutes=5)).isoformat(),
            }]),
            Mock(data=[{
                "access_count": 5,
                "last_accessed_at": (now - timedelta(minutes=5)).isoformat(),
                "priority": "hot",
            }]),
            Mock(data=[{"id": "test"}]),
        ]
        mock_sb.execute.side_effect = read_calls

        with patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("search_cache.trigger_background_revalidation", new_callable=AsyncMock, return_value=True) as mock_trigger:
            result = await get_from_cache(
                user_id="user-b02",
                params={"setor_id": 1, "ufs": ["SP"]},
            )

        assert result is not None
        mock_trigger.assert_not_called()


# ============================================================================
# AC10: priority_distribution in health endpoint
# ============================================================================


class TestHealthPriorityDistribution:
    """AC10: /v1/health/cache includes priority_distribution."""

    @pytest.mark.asyncio
    async def test_priority_distribution_counts(self):
        """Health endpoint returns correct hot/warm/cold counts."""
        from routes.health import _check_cache_degradation

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.gt.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb

        call_count = [0]

        def execute_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                # degraded_until query
                resp = Mock()
                resp.count = 0
                resp.data = []
                return resp
            elif call_count[0] == 2:
                # fail_streak query
                return Mock(data=[])
            elif call_count[0] == 3:
                # priority distribution query
                return Mock(data=[
                    {"priority": "hot"},
                    {"priority": "hot"},
                    {"priority": "warm"},
                    {"priority": "warm"},
                    {"priority": "warm"},
                    {"priority": "cold"},
                ])
            return Mock(data=[])

        mock_sb.execute.side_effect = execute_side_effect

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await _check_cache_degradation()

        assert "priority_distribution" in result
        assert result["priority_distribution"]["hot"] == 2
        assert result["priority_distribution"]["warm"] == 3
        assert result["priority_distribution"]["cold"] == 1

    @pytest.mark.asyncio
    async def test_priority_distribution_empty(self):
        """No cache entries → all zeros."""
        from routes.health import _check_cache_degradation

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.gt.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb

        call_count = [0]

        def execute_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                resp = Mock()
                resp.count = 0
                resp.data = []
                return resp
            return Mock(data=[])

        mock_sb.execute.side_effect = execute_side_effect

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await _check_cache_degradation()

        assert result["priority_distribution"] == {"hot": 0, "warm": 0, "cold": 0}

    @pytest.mark.asyncio
    async def test_priority_distribution_on_error(self):
        """On Supabase failure → returns zero counts with error."""
        from routes.health import _check_cache_degradation

        with patch("supabase_client.get_supabase", side_effect=Exception("DB down")):
            result = await _check_cache_degradation()

        assert result["priority_distribution"] == {"hot": 0, "warm": 0, "cold": 0}
        assert "error" in result
