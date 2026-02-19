"""UX-303 AC10: Multi-level cache tests.

Covers:
  AC2:  3-level save fallback (Supabase → Redis → Local)
  AC2:  3-level read fallback (Supabase → Redis → Local)
  AC4:  CacheStatus classification (fresh/stale/expired)
  AC6:  Sentry alerting on cache failure
  AC7:  Cache health endpoint
  AC8:  Local cache cleanup
  AC3:  Mixpanel tracking (fire-and-forget)
"""

import json
import os
import pytest
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock, AsyncMock

from search_cache import (
    compute_search_hash,
    save_to_cache,
    get_from_cache,
    get_cache_status,
    cleanup_local_cache,
    get_local_cache_stats,
    CacheLevel,
    CacheStatus,
    CACHE_FRESH_HOURS,
    CACHE_STALE_HOURS,
    _save_to_redis,
    _get_from_redis,
    _save_to_local,
    _get_from_local,
    _process_cache_hit,
    LOCAL_CACHE_DIR,
)


# ============================================================================
# AC4: CacheStatus classification
# ============================================================================


class TestCacheStatus:
    """AC4: get_cache_status classifies age into Fresh/Stale/Expired."""

    def test_fresh_within_6_hours(self):
        fetched_at = datetime.now(timezone.utc) - timedelta(hours=2)
        assert get_cache_status(fetched_at) == CacheStatus.FRESH

    def test_stale_between_6_and_24_hours(self):
        fetched_at = datetime.now(timezone.utc) - timedelta(hours=12)
        assert get_cache_status(fetched_at) == CacheStatus.STALE

    def test_expired_after_24_hours(self):
        fetched_at = datetime.now(timezone.utc) - timedelta(hours=30)
        assert get_cache_status(fetched_at) == CacheStatus.EXPIRED

    def test_accepts_string_input(self):
        fetched_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        assert get_cache_status(fetched_at) == CacheStatus.FRESH

    def test_handles_naive_datetime(self):
        """Naive datetimes should be treated as UTC."""
        from datetime import datetime as dt
        fetched_at = dt.utcnow() - timedelta(hours=1)
        assert get_cache_status(fetched_at) == CacheStatus.FRESH

    def test_boundary_fresh_to_stale(self):
        """At exactly 6h, should be stale (> CACHE_FRESH_HOURS)."""
        fetched_at = datetime.now(timezone.utc) - timedelta(hours=6, minutes=1)
        assert get_cache_status(fetched_at) == CacheStatus.STALE


# ============================================================================
# AC2: Level 2 — Redis/InMemory
# ============================================================================


class TestRedisLevel:
    """AC2: Redis/InMemory cache save and read."""

    def test_save_and_read_redis(self):
        """Round-trip: save then read from InMemory cache."""
        cache_key = compute_search_hash({"setor_id": 1, "ufs": ["SP"]})
        _save_to_redis(cache_key, [{"id": 1}], ["PNCP"])
        data = _get_from_redis(cache_key)

        assert data is not None
        assert data["results"] == [{"id": 1}]
        assert data["sources_json"] == ["PNCP"]
        assert "fetched_at" in data

    def test_read_miss_returns_none(self):
        data = _get_from_redis("nonexistent_key_12345")
        assert data is None


# ============================================================================
# AC2: Level 3 — Local file
# ============================================================================


class TestLocalLevel:
    """AC2: Local file cache save and read."""

    def test_save_and_read_local(self, tmp_path):
        """Round-trip: save then read from local file."""
        with patch("search_cache.LOCAL_CACHE_DIR", tmp_path):
            cache_key = compute_search_hash({"setor_id": 1, "ufs": ["RJ"]})
            _save_to_local(cache_key, [{"id": 2}], ["PORTAL_COMPRAS"])
            data = _get_from_local(cache_key)

        assert data is not None
        assert data["results"] == [{"id": 2}]
        assert data["sources_json"] == ["PORTAL_COMPRAS"]

    def test_read_missing_file_returns_none(self, tmp_path):
        with patch("search_cache.LOCAL_CACHE_DIR", tmp_path):
            data = _get_from_local("nonexistent_key")
        assert data is None

    def test_read_corrupted_file_returns_none(self, tmp_path):
        with patch("search_cache.LOCAL_CACHE_DIR", tmp_path):
            # Write a corrupted file
            cache_file = tmp_path / "corrupted_key_12345678901.json"
            cache_file.write_text("not json", encoding="utf-8")
            data = _get_from_local("corrupted_key_1234567890123456")
        assert data is None


# ============================================================================
# AC2: Multi-level save fallback
# ============================================================================


class TestMultiLevelSave:
    """AC2: save_to_cache cascades through 3 levels."""

    @pytest.mark.asyncio
    async def test_save_succeeds_at_supabase(self):
        """Level 1 success — should not try L2/L3."""
        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.upsert.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{"id": "ok"}])

        with patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("search_cache._track_cache_operation"):
            result = await save_to_cache(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
                results=[{"id": 1}],
                sources=["PNCP"],
            )

        assert result["level"] == CacheLevel.SUPABASE
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_save_falls_back_to_redis_on_supabase_failure(self):
        """L1 fails → L2 succeeds."""
        with patch("supabase_client.get_supabase", side_effect=Exception("DB down")), \
             patch("utils.error_reporting.sentry_sdk") as mock_sentry, \
             patch("search_cache._track_cache_operation"):
            result = await save_to_cache(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
                results=[{"id": 1}],
                sources=["PNCP"],
            )

        assert result["level"] == CacheLevel.REDIS
        assert result["success"] is True
        # AC6: Sentry should be called for Supabase failure
        mock_sentry.capture_exception.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_falls_back_to_local_on_all_volatile_failure(self, tmp_path):
        """L1 + L2 fail → L3 succeeds."""
        with patch("supabase_client.get_supabase", side_effect=Exception("DB down")), \
             patch("search_cache._save_to_redis", side_effect=Exception("Redis down")), \
             patch("search_cache.LOCAL_CACHE_DIR", tmp_path), \
             patch("utils.error_reporting.sentry_sdk"), \
             patch("search_cache._track_cache_operation"):
            result = await save_to_cache(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
                results=[{"id": 1}],
                sources=["PNCP"],
            )

        assert result["level"] == CacheLevel.LOCAL
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_save_returns_miss_when_all_levels_fail(self, tmp_path):
        """All 3 levels fail — returns miss without crashing."""
        with patch("supabase_client.get_supabase", side_effect=Exception("DB down")), \
             patch("search_cache._save_to_redis", side_effect=Exception("Redis down")), \
             patch("search_cache._save_to_local", side_effect=Exception("FS error")), \
             patch("utils.error_reporting.sentry_sdk"), \
             patch("search_cache._track_cache_operation"):
            result = await save_to_cache(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
                results=[{"id": 1}],
                sources=["PNCP"],
            )

        assert result["level"] == CacheLevel.MISS
        assert result["success"] is False


# ============================================================================
# AC2: Multi-level read fallback
# ============================================================================


class TestMultiLevelRead:
    """AC2: get_from_cache cascades through 3 levels."""

    @pytest.mark.asyncio
    async def test_read_from_supabase(self):
        """L1 has data — returns it."""
        now = datetime.now(timezone.utc)
        fetched_at = (now - timedelta(hours=2)).isoformat()

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{
            "results": [{"id": 1}],
            "total_results": 1,
            "sources_json": ["PNCP"],
            "fetched_at": fetched_at,
            "created_at": fetched_at,
        }])

        with patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("search_cache._track_cache_operation"):
            result = await get_from_cache(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
            )

        assert result is not None
        assert result["cache_level"] == CacheLevel.SUPABASE
        assert result["cache_status"] == CacheStatus.FRESH

    @pytest.mark.asyncio
    async def test_read_falls_back_to_redis(self):
        """L1 fails → L2 has data."""
        cache_key = compute_search_hash({"setor_id": 1, "ufs": ["SP"]})
        # Pre-seed Redis
        _save_to_redis(cache_key, [{"id": 2}], ["PNCP"])

        with patch("supabase_client.get_supabase", side_effect=Exception("DB down")), \
             patch("utils.error_reporting.sentry_sdk"), \
             patch("search_cache._track_cache_operation"):
            result = await get_from_cache(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
            )

        assert result is not None
        assert result["cache_level"] == CacheLevel.REDIS
        assert result["results"] == [{"id": 2}]

    @pytest.mark.asyncio
    async def test_read_falls_back_to_local(self, tmp_path):
        """L1 + L2 fail → L3 has data."""
        cache_key = compute_search_hash({"setor_id": 1, "ufs": ["MG"]})
        # Pre-seed local file
        with patch("search_cache.LOCAL_CACHE_DIR", tmp_path):
            _save_to_local(cache_key, [{"id": 3}], ["PORTAL_COMPRAS"])

        with patch("supabase_client.get_supabase", side_effect=Exception("DB down")), \
             patch("search_cache._get_from_redis", return_value=None), \
             patch("search_cache.LOCAL_CACHE_DIR", tmp_path), \
             patch("utils.error_reporting.sentry_sdk"), \
             patch("search_cache._track_cache_operation"):
            result = await get_from_cache(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["MG"]},
            )

        assert result is not None
        assert result["cache_level"] == CacheLevel.LOCAL
        assert result["results"] == [{"id": 3}]

    @pytest.mark.asyncio
    async def test_read_returns_none_when_all_miss(self):
        """All levels miss → returns None."""
        with patch("supabase_client.get_supabase", side_effect=Exception("DB down")), \
             patch("search_cache._get_from_redis", return_value=None), \
             patch("search_cache._get_from_local", return_value=None), \
             patch("utils.error_reporting.sentry_sdk"), \
             patch("search_cache._track_cache_operation"):
            result = await get_from_cache(
                user_id="user-1",
                params={"setor_id": 99, "ufs": ["XX"]},
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_expired_entry_not_served(self):
        """Expired entries at any level should return None."""
        now = datetime.now(timezone.utc)
        fetched_at = (now - timedelta(hours=30)).isoformat()

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{
            "results": [{"id": 1}],
            "total_results": 1,
            "sources_json": ["PNCP"],
            "fetched_at": fetched_at,
            "created_at": fetched_at,
        }])

        with patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("search_cache._get_from_redis", return_value=None), \
             patch("search_cache._get_from_local", return_value=None), \
             patch("search_cache._track_cache_operation"):
            result = await get_from_cache(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
            )

        assert result is None


# ============================================================================
# AC2: _process_cache_hit
# ============================================================================


class TestProcessCacheHit:
    """Process raw cache data with TTL checks."""

    def test_fresh_hit(self):
        now = datetime.now(timezone.utc)
        data = {
            "results": [{"id": 1}],
            "sources_json": ["PNCP"],
            "fetched_at": (now - timedelta(hours=1)).isoformat(),
        }
        result = _process_cache_hit(data, "abc123", CacheLevel.SUPABASE)
        assert result is not None
        assert result["is_stale"] is False
        assert result["cache_status"] == CacheStatus.FRESH

    def test_stale_hit(self):
        now = datetime.now(timezone.utc)
        data = {
            "results": [{"id": 1}],
            "sources_json": ["PNCP"],
            "fetched_at": (now - timedelta(hours=10)).isoformat(),
        }
        result = _process_cache_hit(data, "abc123", CacheLevel.REDIS)
        assert result is not None
        assert result["is_stale"] is True
        assert result["cache_status"] == CacheStatus.STALE

    def test_expired_returns_none(self):
        now = datetime.now(timezone.utc)
        data = {
            "results": [{"id": 1}],
            "sources_json": None,
            "fetched_at": (now - timedelta(hours=25)).isoformat(),
        }
        result = _process_cache_hit(data, "abc123", CacheLevel.LOCAL)
        assert result is None

    def test_missing_fetched_at_returns_none(self):
        data = {"results": [{"id": 1}], "sources_json": ["PNCP"]}
        result = _process_cache_hit(data, "abc123", CacheLevel.SUPABASE)
        assert result is None


# ============================================================================
# AC8: Local cache cleanup
# ============================================================================


class TestLocalCacheCleanup:
    """AC8: cleanup_local_cache deletes old files."""

    def test_cleanup_deletes_old_files(self, tmp_path):
        """Files older than 24h should be deleted."""
        # Create a "young" file
        young_file = tmp_path / "young.json"
        young_file.write_text("{}", encoding="utf-8")

        # Create an "old" file — set mtime to 25h ago
        old_file = tmp_path / "old.json"
        old_file.write_text("{}", encoding="utf-8")
        old_mtime = (datetime.now(timezone.utc) - timedelta(hours=25)).timestamp()
        os.utime(old_file, (old_mtime, old_mtime))

        with patch("search_cache.LOCAL_CACHE_DIR", tmp_path):
            deleted = cleanup_local_cache()

        assert deleted == 1
        assert young_file.exists()
        assert not old_file.exists()

    def test_cleanup_returns_zero_when_no_old_files(self, tmp_path):
        young_file = tmp_path / "fresh.json"
        young_file.write_text("{}", encoding="utf-8")

        with patch("search_cache.LOCAL_CACHE_DIR", tmp_path):
            deleted = cleanup_local_cache()

        assert deleted == 0

    def test_cleanup_handles_nonexistent_dir(self, tmp_path):
        nonexistent = tmp_path / "does_not_exist"
        with patch("search_cache.LOCAL_CACHE_DIR", nonexistent):
            deleted = cleanup_local_cache()
        assert deleted == 0


# ============================================================================
# AC7: Local cache stats
# ============================================================================


class TestLocalCacheStats:
    """AC7: get_local_cache_stats returns file count and size."""

    def test_stats_with_files(self, tmp_path):
        (tmp_path / "a.json").write_text('{"x":1}', encoding="utf-8")
        (tmp_path / "b.json").write_text('{"y":2}', encoding="utf-8")

        with patch("search_cache.LOCAL_CACHE_DIR", tmp_path):
            stats = get_local_cache_stats()

        assert stats["files_count"] == 2
        assert stats["total_size_mb"] >= 0

    def test_stats_empty_dir(self, tmp_path):
        with patch("search_cache.LOCAL_CACHE_DIR", tmp_path):
            stats = get_local_cache_stats()

        assert stats["files_count"] == 0
        assert stats["total_size_mb"] == 0.0


# ============================================================================
# AC7: Health endpoint
# ============================================================================


class TestCacheHealthEndpoint:
    """AC7: /health/cache returns status of each level."""

    @pytest.mark.asyncio
    async def test_health_returns_all_levels(self):
        from routes.health import cache_health

        with patch("routes.health._check_supabase_cache", new_callable=AsyncMock) as mock_supa, \
             patch("routes.health._check_redis_cache") as mock_redis, \
             patch("routes.health._check_local_cache") as mock_local:

            mock_supa.return_value = {"status": "healthy", "latency_ms": 45, "total_entries": 10, "last_error": None}
            mock_redis.return_value = {"status": "healthy", "latency_ms": 1, "entries": 5, "last_error": None}
            mock_local.return_value = {"status": "healthy", "latency_ms": 0, "files_count": 3, "total_size_mb": 0.5, "last_error": None}

            result = await cache_health()

        assert result["overall"] == "healthy"
        assert "supabase" in result
        assert "redis" in result
        assert "local" in result

    @pytest.mark.asyncio
    async def test_health_degraded_when_supabase_down(self):
        from routes.health import cache_health

        with patch("routes.health._check_supabase_cache", new_callable=AsyncMock) as mock_supa, \
             patch("routes.health._check_redis_cache") as mock_redis, \
             patch("routes.health._check_local_cache") as mock_local:

            mock_supa.return_value = {"status": "down", "latency_ms": 100, "total_entries": 0, "last_error": "timeout"}
            mock_redis.return_value = {"status": "healthy", "latency_ms": 1, "entries": 5, "last_error": None}
            mock_local.return_value = {"status": "healthy", "latency_ms": 0, "files_count": 3, "total_size_mb": 0.5, "last_error": None}

            result = await cache_health()

        assert result["overall"] == "degraded"


# ============================================================================
# AC6: Sentry alerting
# ============================================================================


class TestSentryAlerting:
    """AC6: Sentry capture_exception on cache failures."""

    @pytest.mark.asyncio
    async def test_sentry_called_on_supabase_save_failure(self):
        with patch("supabase_client.get_supabase", side_effect=Exception("test error")), \
             patch("utils.error_reporting.sentry_sdk") as mock_sentry, \
             patch("search_cache._track_cache_operation"):
            await save_to_cache(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
                results=[{"id": 1}],
                sources=["PNCP"],
            )

        mock_sentry.capture_exception.assert_called_once()
        # GTM-RESILIENCE-E02: tags set via set_tag, not extras
        mock_sentry.set_tag.assert_any_call("cache_operation", "save")
        mock_sentry.set_tag.assert_any_call("cache_level", "supabase")

    @pytest.mark.asyncio
    async def test_sentry_called_on_supabase_read_failure(self):
        with patch("supabase_client.get_supabase", side_effect=Exception("read error")), \
             patch("search_cache._get_from_redis", return_value=None), \
             patch("search_cache._get_from_local", return_value=None), \
             patch("utils.error_reporting.sentry_sdk") as mock_sentry, \
             patch("search_cache._track_cache_operation"):
            await get_from_cache(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
            )

        mock_sentry.capture_exception.assert_called_once()


# ============================================================================
# Enum values
# ============================================================================


class TestEnums:
    """Verify enum string values for serialization."""

    def test_cache_level_values(self):
        assert CacheLevel.SUPABASE.value == "supabase"
        assert CacheLevel.REDIS.value == "redis"
        assert CacheLevel.LOCAL.value == "local"
        assert CacheLevel.MISS.value == "miss"

    def test_cache_status_values(self):
        assert CacheStatus.FRESH.value == "fresh"
        assert CacheStatus.STALE.value == "stale"
        assert CacheStatus.EXPIRED.value == "expired"


# ============================================================================
# Schema integration
# ============================================================================


class TestSchemaIntegration:
    """Verify new fields exist on BuscaResponse and SearchContext."""

    def test_busca_response_has_cache_fields(self):
        from schemas import BuscaResponse
        fields = BuscaResponse.model_fields
        assert "cache_status" in fields
        assert "cache_level" in fields

    def test_search_context_has_cache_fields(self):
        from search_context import SearchContext
        ctx = SearchContext(request=Mock(), user={})
        assert ctx.cache_status is None
        assert ctx.cache_level is None
