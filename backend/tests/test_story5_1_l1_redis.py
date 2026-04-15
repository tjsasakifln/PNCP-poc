"""tests/test_story5_1_l1_redis.py — STORY-5.1 (TD-SYS-010): L1 Cache Shared via Redis.

Tests that _save_to_redis / _get_from_redis use actual Redis when available,
fall back to InMemoryCache when Redis is None or raises, and correctly emit
Prometheus hit/miss counters with backend label.

Patching strategy:
- ``redis_pool.get_sync_redis``  → controls which Redis client is returned
- ``redis_pool.get_fallback_cache`` → controls the InMemoryCache fallback
- ``metrics.L1_CACHE_HITS_TOTAL`` / ``metrics.L1_CACHE_MISSES_TOTAL`` → spy on counters
"""
import json
from unittest.mock import MagicMock, patch, call, ANY

import pytest

from cache.redis import _save_to_redis, _get_from_redis
from cache.enums import CachePriority, REDIS_TTL_BY_PRIORITY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAMPLE_RESULTS = [{"id": "abc", "title": "Edital 1"}]
_SAMPLE_SOURCES = ["PNCP"]
_SAMPLE_CACHE_KEY = "deadbeef1234"


def _make_cached_json(results=None, sources=None):
    """Build the JSON string that the cache stores."""
    return json.dumps({
        "results": results or _SAMPLE_RESULTS,
        "sources_json": sources or _SAMPLE_SOURCES,
        "fetched_at": "2026-04-15T00:00:00+00:00",
    })


# ---------------------------------------------------------------------------
# _get_from_redis — Redis path
# ---------------------------------------------------------------------------

class TestGetFromRedisRediPath:
    """AC1/AC4: When Redis is available, read from l1:search_cache:{key}."""

    def test_uses_redis_and_returns_parsed_dict(self):
        """Happy path: Redis returns data → parsed dict returned."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = _make_cached_json()

        with patch("redis_pool.get_sync_redis", return_value=mock_redis), \
             patch("metrics.L1_CACHE_HITS_TOTAL", MagicMock()), \
             patch("metrics.L1_CACHE_MISSES_TOTAL", MagicMock()):
            result = _get_from_redis(_SAMPLE_CACHE_KEY)

        assert result is not None
        assert result["results"] == _SAMPLE_RESULTS
        mock_redis.get.assert_called_once_with(f"l1:search_cache:{_SAMPLE_CACHE_KEY}")

    def test_returns_none_on_redis_miss(self):
        """Redis returns None → function returns None (no fallback to memory)."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        with patch("redis_pool.get_sync_redis", return_value=mock_redis), \
             patch("metrics.L1_CACHE_HITS_TOTAL", MagicMock()), \
             patch("metrics.L1_CACHE_MISSES_TOTAL", MagicMock()):
            result = _get_from_redis(_SAMPLE_CACHE_KEY)

        assert result is None
        # Should NOT fall through to memory when Redis explicitly returned None
        mock_redis.get.assert_called_once_with(f"l1:search_cache:{_SAMPLE_CACHE_KEY}")

    def test_uses_l1_namespace_prefix(self):
        """AC1: Redis key must start with l1: namespace."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        with patch("redis_pool.get_sync_redis", return_value=mock_redis), \
             patch("metrics.L1_CACHE_HITS_TOTAL", MagicMock()), \
             patch("metrics.L1_CACHE_MISSES_TOTAL", MagicMock()):
            _get_from_redis("somekey")

        called_key = mock_redis.get.call_args[0][0]
        assert called_key.startswith("l1:"), (
            f"Expected key to start with 'l1:' (AC1), got: {called_key!r}"
        )


# ---------------------------------------------------------------------------
# _get_from_redis — Fallback path
# ---------------------------------------------------------------------------

class TestGetFromRedisFallback:
    """AC4: Falls back to InMemoryCache when Redis is unavailable or raises."""

    def test_falls_back_to_memory_when_redis_none(self):
        """get_sync_redis() returns None → InMemoryCache is used."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = _make_cached_json()

        with patch("redis_pool.get_sync_redis", return_value=None), \
             patch("redis_pool.get_fallback_cache", return_value=mock_cache), \
             patch("metrics.L1_CACHE_HITS_TOTAL", MagicMock()), \
             patch("metrics.L1_CACHE_MISSES_TOTAL", MagicMock()):
            result = _get_from_redis(_SAMPLE_CACHE_KEY)

        assert result is not None
        # Must use legacy search_cache: prefix (AC4 backward compat)
        mock_cache.get.assert_called_once_with(f"search_cache:{_SAMPLE_CACHE_KEY}")

    def test_falls_back_to_memory_on_redis_error(self):
        """Redis raises an exception → falls back gracefully to InMemoryCache."""
        mock_redis = MagicMock()
        mock_redis.get.side_effect = ConnectionError("Redis is down")
        mock_cache = MagicMock()
        mock_cache.get.return_value = _make_cached_json()

        with patch("redis_pool.get_sync_redis", return_value=mock_redis), \
             patch("redis_pool.get_fallback_cache", return_value=mock_cache), \
             patch("metrics.L1_CACHE_HITS_TOTAL", MagicMock()), \
             patch("metrics.L1_CACHE_MISSES_TOTAL", MagicMock()):
            result = _get_from_redis(_SAMPLE_CACHE_KEY)

        # Fallback must succeed
        assert result is not None
        mock_cache.get.assert_called_once_with(f"search_cache:{_SAMPLE_CACHE_KEY}")

    def test_returns_none_on_memory_miss_too(self):
        """Both Redis None and InMemoryCache miss → returns None."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None

        with patch("redis_pool.get_sync_redis", return_value=None), \
             patch("redis_pool.get_fallback_cache", return_value=mock_cache), \
             patch("metrics.L1_CACHE_HITS_TOTAL", MagicMock()), \
             patch("metrics.L1_CACHE_MISSES_TOTAL", MagicMock()):
            result = _get_from_redis(_SAMPLE_CACHE_KEY)

        assert result is None


# ---------------------------------------------------------------------------
# _save_to_redis — Redis path
# ---------------------------------------------------------------------------

class TestSaveToRedisRedisPath:
    """AC1/AC2: When Redis is available, write with l1: prefix and correct TTL."""

    def test_writes_to_redis_with_l1_prefix(self):
        """Happy path: writes l1:search_cache:{key} to Redis."""
        mock_redis = MagicMock()

        with patch("redis_pool.get_sync_redis", return_value=mock_redis):
            _save_to_redis(_SAMPLE_CACHE_KEY, _SAMPLE_RESULTS, _SAMPLE_SOURCES)

        mock_redis.setex.assert_called_once()
        key_arg = mock_redis.setex.call_args[0][0]
        assert key_arg == f"l1:search_cache:{_SAMPLE_CACHE_KEY}"

    def test_json_payload_contains_results_and_sources(self):
        """Stored JSON includes results, sources_json, fetched_at."""
        mock_redis = MagicMock()

        with patch("redis_pool.get_sync_redis", return_value=mock_redis):
            _save_to_redis(_SAMPLE_CACHE_KEY, _SAMPLE_RESULTS, _SAMPLE_SOURCES)

        _, ttl_arg, data_arg = mock_redis.setex.call_args[0]
        payload = json.loads(data_arg)
        assert payload["results"] == _SAMPLE_RESULTS
        assert payload["sources_json"] == _SAMPLE_SOURCES
        assert "fetched_at" in payload

    def test_does_not_call_fallback_when_redis_succeeds(self):
        """When Redis write succeeds, InMemoryCache must NOT be touched."""
        mock_redis = MagicMock()
        mock_cache = MagicMock()

        with patch("redis_pool.get_sync_redis", return_value=mock_redis), \
             patch("redis_pool.get_fallback_cache", return_value=mock_cache):
            _save_to_redis(_SAMPLE_CACHE_KEY, _SAMPLE_RESULTS, _SAMPLE_SOURCES)

        mock_cache.setex.assert_not_called()


# ---------------------------------------------------------------------------
# _save_to_redis — Priority TTL (AC2)
# ---------------------------------------------------------------------------

class TestSavePriorityTTL:
    """AC2: hot/warm/cold priority maps to differentiated TTLs via Redis setex."""

    def test_hot_priority_ttl(self):
        """HOT priority → 7200s TTL in Redis setex."""
        mock_redis = MagicMock()
        with patch("redis_pool.get_sync_redis", return_value=mock_redis):
            _save_to_redis("key", [{}], [], priority=CachePriority.HOT)
        _, ttl, _ = mock_redis.setex.call_args[0]
        assert ttl == REDIS_TTL_BY_PRIORITY[CachePriority.HOT] == 7200

    def test_cold_priority_ttl(self):
        """COLD priority → 3600s TTL in Redis setex."""
        mock_redis = MagicMock()
        with patch("redis_pool.get_sync_redis", return_value=mock_redis):
            _save_to_redis("key", [{}], [], priority=CachePriority.COLD)
        _, ttl, _ = mock_redis.setex.call_args[0]
        assert ttl == REDIS_TTL_BY_PRIORITY[CachePriority.COLD] == 3600

    def test_warm_priority_ttl(self):
        """WARM priority → 21600s TTL in Redis setex."""
        mock_redis = MagicMock()
        with patch("redis_pool.get_sync_redis", return_value=mock_redis):
            _save_to_redis("key", [{}], [], priority=CachePriority.WARM)
        _, ttl, _ = mock_redis.setex.call_args[0]
        assert ttl == REDIS_TTL_BY_PRIORITY[CachePriority.WARM] == 21600

    def test_default_priority_is_cold(self):
        """No priority → defaults to COLD (3600s TTL)."""
        mock_redis = MagicMock()
        with patch("redis_pool.get_sync_redis", return_value=mock_redis):
            _save_to_redis("key", [{}], [])
        _, ttl, _ = mock_redis.setex.call_args[0]
        assert ttl == 3600


# ---------------------------------------------------------------------------
# _save_to_redis — Fallback path
# ---------------------------------------------------------------------------

class TestSaveToRedisFallback:
    """AC4: Falls back to InMemoryCache when Redis is unavailable."""

    def test_falls_back_to_memory_when_redis_none(self):
        """get_sync_redis() returns None → InMemoryCache.setex called."""
        mock_cache = MagicMock()

        with patch("redis_pool.get_sync_redis", return_value=None), \
             patch("redis_pool.get_fallback_cache", return_value=mock_cache):
            _save_to_redis(_SAMPLE_CACHE_KEY, _SAMPLE_RESULTS, _SAMPLE_SOURCES)

        mock_cache.setex.assert_called_once()
        key_arg, ttl_arg, _ = mock_cache.setex.call_args[0]
        # Legacy key format (no l1: prefix) for backward compat
        assert key_arg == f"search_cache:{_SAMPLE_CACHE_KEY}"

    def test_falls_back_to_memory_on_redis_error(self):
        """Redis raises → writes to InMemoryCache instead."""
        mock_redis = MagicMock()
        mock_redis.setex.side_effect = ConnectionError("Redis is down")
        mock_cache = MagicMock()

        with patch("redis_pool.get_sync_redis", return_value=mock_redis), \
             patch("redis_pool.get_fallback_cache", return_value=mock_cache):
            _save_to_redis(_SAMPLE_CACHE_KEY, _SAMPLE_RESULTS, _SAMPLE_SOURCES)

        mock_cache.setex.assert_called_once()

    def test_fallback_preserves_priority_ttl(self):
        """When falling back to InMemoryCache, priority TTL is still respected."""
        mock_cache = MagicMock()

        with patch("redis_pool.get_sync_redis", return_value=None), \
             patch("redis_pool.get_fallback_cache", return_value=mock_cache):
            _save_to_redis("key", [{}], [], priority=CachePriority.HOT)

        _, ttl, _ = mock_cache.setex.call_args[0]
        assert ttl == 7200


# ---------------------------------------------------------------------------
# Prometheus metrics (AC3)
# ---------------------------------------------------------------------------

class TestL1CacheMetrics:
    """AC3: Hit/miss counters are incremented with correct backend label."""

    def test_hit_metric_incremented_for_redis_hit(self):
        """Redis hit → L1_CACHE_HITS_TOTAL.labels(backend='redis').inc() called."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = _make_cached_json()
        mock_hits = MagicMock()
        mock_misses = MagicMock()

        with patch("redis_pool.get_sync_redis", return_value=mock_redis), \
             patch("metrics.L1_CACHE_HITS_TOTAL", mock_hits), \
             patch("metrics.L1_CACHE_MISSES_TOTAL", mock_misses):
            _get_from_redis(_SAMPLE_CACHE_KEY)

        mock_hits.labels.assert_called_once_with(backend="redis")
        mock_hits.labels.return_value.inc.assert_called_once()
        mock_misses.labels.assert_not_called()

    def test_miss_metric_incremented_for_redis_miss(self):
        """Redis miss → L1_CACHE_MISSES_TOTAL.labels(backend='redis').inc() called."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_hits = MagicMock()
        mock_misses = MagicMock()

        with patch("redis_pool.get_sync_redis", return_value=mock_redis), \
             patch("metrics.L1_CACHE_HITS_TOTAL", mock_hits), \
             patch("metrics.L1_CACHE_MISSES_TOTAL", mock_misses):
            _get_from_redis(_SAMPLE_CACHE_KEY)

        mock_misses.labels.assert_called_once_with(backend="redis")
        mock_misses.labels.return_value.inc.assert_called_once()
        mock_hits.labels.assert_not_called()

    def test_hit_metric_incremented_for_memory_fallback_hit(self):
        """Memory hit (Redis None) → L1_CACHE_HITS_TOTAL.labels(backend='memory').inc()."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = _make_cached_json()
        mock_hits = MagicMock()
        mock_misses = MagicMock()

        with patch("redis_pool.get_sync_redis", return_value=None), \
             patch("redis_pool.get_fallback_cache", return_value=mock_cache), \
             patch("metrics.L1_CACHE_HITS_TOTAL", mock_hits), \
             patch("metrics.L1_CACHE_MISSES_TOTAL", mock_misses):
            _get_from_redis(_SAMPLE_CACHE_KEY)

        mock_hits.labels.assert_called_once_with(backend="memory")
        mock_hits.labels.return_value.inc.assert_called_once()

    def test_miss_metric_incremented_for_memory_fallback_miss(self):
        """Memory miss (Redis None) → L1_CACHE_MISSES_TOTAL.labels(backend='memory').inc()."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_hits = MagicMock()
        mock_misses = MagicMock()

        with patch("redis_pool.get_sync_redis", return_value=None), \
             patch("redis_pool.get_fallback_cache", return_value=mock_cache), \
             patch("metrics.L1_CACHE_HITS_TOTAL", mock_hits), \
             patch("metrics.L1_CACHE_MISSES_TOTAL", mock_misses):
            _get_from_redis(_SAMPLE_CACHE_KEY)

        mock_misses.labels.assert_called_once_with(backend="memory")
        mock_misses.labels.return_value.inc.assert_called_once()


# ---------------------------------------------------------------------------
# Backward compat (AC4)
# ---------------------------------------------------------------------------

class TestBackwardCompat:
    """AC4: Public API of _save_to_redis and _get_from_redis is unchanged."""

    def test_save_to_redis_signature(self):
        """_save_to_redis(cache_key, results, sources, *, priority) still works."""
        import inspect
        sig = inspect.signature(_save_to_redis)
        params = list(sig.parameters.keys())
        assert "cache_key" in params
        assert "results" in params
        assert "sources" in params
        assert "priority" in params
        # priority must be keyword-only
        assert sig.parameters["priority"].kind == inspect.Parameter.KEYWORD_ONLY

    def test_get_from_redis_signature(self):
        """_get_from_redis(cache_key) -> Optional[dict] signature unchanged."""
        import inspect
        sig = inspect.signature(_get_from_redis)
        params = list(sig.parameters.keys())
        assert params == ["cache_key"]

    def test_importable_from_search_cache(self):
        """from search_cache import _save_to_redis, _get_from_redis still works."""
        from search_cache import _save_to_redis as s, _get_from_redis as g  # noqa: F401
        assert callable(s)
        assert callable(g)

    def test_patchable_at_cache_redis_namespace(self):
        """patch('cache.redis._get_from_redis') still works for existing tests."""
        with patch("cache.redis._get_from_redis", return_value={"results": []}) as mock:
            from cache import redis as _r
            result = _r._get_from_redis("any_key")
        assert result == {"results": []}
        mock.assert_called_once_with("any_key")
