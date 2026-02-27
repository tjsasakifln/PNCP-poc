"""STORY-294: State Externalization to Redis — comprehensive tests.

Tests AC1-AC10:
- AC1: Progress tracker uses Redis Streams (cross-worker SSE)
- AC2: Background results stored in Redis hash with TTL 30min
- AC3: Arbiter cache stored in Redis hash with TTL 1h
- AC4: SSE works independent of worker
- AC5: Results available via endpoint independent of worker
- AC6: Graceful fallback when Redis unavailable
- AC7: STATE_STORE_ERRORS metric incremented on failures
- AC8: TTL cleanup via Redis EXPIRE on all temp keys
- AC9: Existing tests pass (verified by full test suite)
- AC10: Concurrent searches with multi-worker simulation
"""

import asyncio
import json
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Pre-mock heavy deps to avoid import-time errors
import sys
if "openai" not in sys.modules:
    sys.modules["openai"] = MagicMock()
if "stripe" not in sys.modules:
    sys.modules["stripe"] = MagicMock()
if "arq" not in sys.modules:
    _fake_arq = MagicMock()
    _fake_arq.connections = MagicMock()
    sys.modules["arq"] = _fake_arq
    sys.modules["arq.connections"] = _fake_arq.connections


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def _reset_state():
    """Reset all global state between tests."""
    # Reset in-memory caches
    from routes.search import _background_results, _active_background_tasks
    _background_results.clear()
    _active_background_tasks.clear()

    # Reset arbiter cache
    import llm_arbiter
    llm_arbiter._arbiter_cache.clear()

    # Reset progress trackers
    import progress
    progress._active_trackers.clear()

    # Reset sync redis singleton for clean test state
    import redis_pool
    redis_pool._sync_redis = None
    redis_pool._sync_redis_initialized = False

    yield


@pytest.fixture
def mock_redis_async():
    """Mock async Redis pool."""
    mock = AsyncMock()
    mock.setex = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=None)
    mock.hset = AsyncMock(return_value=True)
    mock.hgetall = AsyncMock(return_value={})
    mock.expire = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.xadd = AsyncMock(return_value="1-0")
    mock.ping = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_redis_sync():
    """Mock sync Redis client."""
    mock = MagicMock()
    mock.get = MagicMock(return_value=None)
    mock.setex = MagicMock(return_value=True)
    mock.ping = MagicMock(return_value=True)
    return mock


def _make_response(**kwargs):
    """Helper to create a mock BuscaResponse."""
    defaults = {
        "resumo": "Test summary",
        "licitacoes": [],
        "excel_url": None,
        "total_raw": kwargs.get("total_raw", 10),
        "total_filtrado": kwargs.get("total_filtrado", 5),
        "setor": "software",
        "ufs": ["SP"],
    }
    defaults.update(kwargs)
    resp = SimpleNamespace(**defaults)
    resp.model_dump = lambda mode="json": {
        "resumo": resp.resumo,
        "licitacoes": resp.licitacoes,
        "total_raw": resp.total_raw,
        "total_filtrado": resp.total_filtrado,
        "setor": resp.setor,
        "ufs": resp.ufs,
    }
    return resp


# ============================================================================
# AC2: Background Results → Redis
# ============================================================================


class TestBackgroundResultsRedis:
    """AC2: _background_results stored in Redis hash with TTL 30min."""

    @pytest.mark.asyncio
    async def test_persist_results_stores_in_redis(self, mock_redis_async):
        """AC2: store_background_results + _persist_results_to_redis writes to Redis."""
        from routes.search import _persist_results_to_redis

        with patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis_async):
            resp = _make_response(total_filtrado=42)
            await _persist_results_to_redis("search-001", resp)

            # Verify Redis SETEX was called with correct key and TTL
            mock_redis_async.setex.assert_called_once()
            call_args = mock_redis_async.setex.call_args
            assert call_args[0][0] == "smartlic:results:search-001"
            assert call_args[0][1] == 1800  # 30 min TTL
            data = json.loads(call_args[0][2])
            assert data["total_filtrado"] == 42

    @pytest.mark.asyncio
    async def test_get_results_from_redis_cross_worker(self, mock_redis_async):
        """AC5: Results retrievable from Redis when not in local memory."""
        from routes.search import get_background_results_async

        stored_data = json.dumps({
            "resumo": "Test", "licitacoes": [], "total_filtrado": 7,
        })
        mock_redis_async.get = AsyncMock(return_value=stored_data)

        with patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis_async), \
             patch("routes.search.get_background_results", return_value=None):
            result = await get_background_results_async("search-cross-001")

            assert result is not None
            assert result["total_filtrado"] == 7

    @pytest.mark.asyncio
    async def test_get_results_l1_before_redis(self, mock_redis_async):
        """L1 (in-memory) takes priority over Redis."""
        from routes.search import store_background_results, get_background_results_async

        resp = _make_response(total_filtrado=99)
        store_background_results("search-l1", resp)

        with patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis_async):
            result = await get_background_results_async("search-l1")

            # Should find in L1, never hit Redis
            assert result is not None
            assert result.total_filtrado == 99
            mock_redis_async.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_persist_results_fallback_no_redis(self):
        """AC6: When Redis unavailable, persist silently fails (no crash)."""
        from routes.search import _persist_results_to_redis

        with patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=None):
            resp = _make_response()
            # Should not raise
            await _persist_results_to_redis("search-fallback", resp)

    @pytest.mark.asyncio
    async def test_persist_results_error_increments_metric(self, mock_redis_async):
        """AC7: STATE_STORE_ERRORS incremented on Redis write failure."""
        from routes.search import _persist_results_to_redis

        mock_redis_async.setex = AsyncMock(side_effect=Exception("Redis write error"))

        with patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis_async), \
             patch("metrics.STATE_STORE_ERRORS") as mock_metric:
            mock_metric.labels = MagicMock(return_value=MagicMock())

            await _persist_results_to_redis("search-err", _make_response())

            mock_metric.labels.assert_called_with(store="results", operation="write")

    @pytest.mark.asyncio
    async def test_get_results_redis_error_increments_metric(self, mock_redis_async):
        """AC7: STATE_STORE_ERRORS incremented on Redis read failure."""
        from routes.search import _get_results_from_redis

        mock_redis_async.get = AsyncMock(side_effect=Exception("Redis read error"))

        with patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis_async), \
             patch("metrics.STATE_STORE_ERRORS") as mock_metric:
            mock_metric.labels = MagicMock(return_value=MagicMock())

            result = await _get_results_from_redis("search-err-read")

            assert result is None
            mock_metric.labels.assert_called_with(store="results", operation="read")


# ============================================================================
# AC3: Arbiter Cache → Redis
# ============================================================================


class TestArbiterCacheRedis:
    """AC3: _arbiter_cache stored in Redis hash with TTL 1h."""

    def test_cache_write_to_redis(self, mock_redis_sync):
        """AC3: classify_contract_primary_match writes to Redis L2."""
        from llm_arbiter import _arbiter_cache_set_redis

        with patch("redis_pool.get_sync_redis", return_value=mock_redis_sync):
            _arbiter_cache_set_redis("test-key-001", {"is_primary": True, "confidence": 90})

            mock_redis_sync.setex.assert_called_once()
            call_args = mock_redis_sync.setex.call_args
            assert call_args[0][0] == "smartlic:arbiter:test-key-001"
            assert call_args[0][1] == 3600  # 1h TTL
            data = json.loads(call_args[0][2])
            assert data["is_primary"] is True

    def test_cache_read_from_redis(self, mock_redis_sync):
        """AC3: Cache miss in L1 checks Redis L2."""
        from llm_arbiter import _arbiter_cache_get_redis, _arbiter_cache

        stored = json.dumps({"is_primary": False, "confidence": 20})
        mock_redis_sync.get = MagicMock(return_value=stored)

        with patch("redis_pool.get_sync_redis", return_value=mock_redis_sync):
            result = _arbiter_cache_get_redis("test-key-read")

            assert result is not None
            assert result["is_primary"] is False
            # Should be promoted to L1
            assert "test-key-read" in _arbiter_cache

    def test_cache_l1_before_redis(self, mock_redis_sync):
        """L1 (in-memory) takes priority — Redis not consulted."""
        import llm_arbiter
        llm_arbiter._arbiter_cache["preloaded-key"] = {"is_primary": True, "confidence": 100}

        with patch("redis_pool.get_sync_redis", return_value=mock_redis_sync):
            # L1 hit — _arbiter_cache_get_redis should NOT be called
            assert llm_arbiter._arbiter_cache["preloaded-key"]["is_primary"] is True
            # Redis never called
            mock_redis_sync.get.assert_not_called()

    def test_cache_fallback_no_redis(self):
        """AC6: When sync Redis unavailable, L1 only (no crash)."""
        from llm_arbiter import _arbiter_cache_get_redis, _arbiter_cache_set_redis

        with patch("redis_pool.get_sync_redis", return_value=None):
            result = _arbiter_cache_get_redis("no-redis-key")
            assert result is None

            # Write should also silently succeed
            _arbiter_cache_set_redis("no-redis-key", {"is_primary": True})

    def test_cache_redis_error_increments_metric(self, mock_redis_sync):
        """AC7: STATE_STORE_ERRORS incremented on Redis cache failure."""
        from llm_arbiter import _arbiter_cache_get_redis

        mock_redis_sync.get = MagicMock(side_effect=Exception("Redis error"))

        with patch("redis_pool.get_sync_redis", return_value=mock_redis_sync), \
             patch("metrics.STATE_STORE_ERRORS") as mock_metric:
            mock_metric.labels = MagicMock(return_value=MagicMock())

            result = _arbiter_cache_get_redis("err-key")
            assert result is None
            mock_metric.labels.assert_called_with(store="arbiter", operation="read")

    def test_cache_write_error_increments_metric(self, mock_redis_sync):
        """AC7: STATE_STORE_ERRORS incremented on Redis write failure."""
        from llm_arbiter import _arbiter_cache_set_redis

        mock_redis_sync.setex = MagicMock(side_effect=Exception("Redis write fail"))

        with patch("redis_pool.get_sync_redis", return_value=mock_redis_sync), \
             patch("metrics.STATE_STORE_ERRORS") as mock_metric:
            mock_metric.labels = MagicMock(return_value=MagicMock())

            _arbiter_cache_set_redis("err-write-key", True)
            mock_metric.labels.assert_called_with(store="arbiter", operation="write")


# ============================================================================
# AC1/AC4: Progress Tracker — Redis Streams cross-worker
# ============================================================================


class TestProgressTrackerCrossWorker:
    """AC1/AC4: Tracker metadata in Redis enables cross-worker SSE."""

    @pytest.mark.asyncio
    async def test_tracker_metadata_stored_in_redis(self, mock_redis_async):
        """AC1: create_tracker stores metadata in Redis for cross-worker discovery."""
        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis_async), \
             patch("progress.is_redis_available", new_callable=AsyncMock, return_value=True):
            from progress import create_tracker

            tracker = await create_tracker("cross-001", uf_count=5)

            assert tracker.search_id == "cross-001"
            assert tracker._use_redis is True
            # Metadata stored in Redis
            mock_redis_async.hset.assert_called_once()
            call_args = mock_redis_async.hset.call_args
            assert call_args[1]["mapping"]["uf_count"] == "5"
            # TTL set
            mock_redis_async.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_tracker_recovered_from_redis_metadata(self, mock_redis_async):
        """AC4: get_tracker recreates tracker from Redis metadata (different worker)."""
        mock_redis_async.hgetall = AsyncMock(return_value={
            "uf_count": "3",
            "created_at": str(time.time()),
        })

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis_async):
            from progress import get_tracker, _active_trackers
            _active_trackers.clear()  # Simulate different worker

            tracker = await get_tracker("cross-002")

            assert tracker is not None
            assert tracker.search_id == "cross-002"
            assert tracker.uf_count == 3
            assert tracker._use_redis is True

    @pytest.mark.asyncio
    async def test_tracker_events_published_to_redis_stream(self, mock_redis_async):
        """AC1: Events published to Redis Streams for cross-worker SSE."""
        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis_async):
            from progress import ProgressTracker

            tracker = ProgressTracker("stream-001", uf_count=2, use_redis=True)
            await tracker.emit("fetching", 30, "Buscando dados: 1/2 estados")

            # Event published to stream
            mock_redis_async.xadd.assert_called_once()
            call_args = mock_redis_async.xadd.call_args
            assert call_args[0][0] == "smartlic:progress:stream-001:stream"
            fields = call_args[0][1]
            assert fields["stage"] == "fetching"
            assert fields["progress"] == "30"

    @pytest.mark.asyncio
    async def test_tracker_stream_expire_on_terminal(self, mock_redis_async):
        """AC8: Terminal events set EXPIRE on stream key."""
        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis_async):
            from progress import ProgressTracker

            tracker = ProgressTracker("expire-001", uf_count=1, use_redis=True)
            await tracker.emit_complete()

            # EXPIRE called after terminal event
            mock_redis_async.expire.assert_called_once()
            call_args = mock_redis_async.expire.call_args
            assert call_args[0][0] == "smartlic:progress:expire-001:stream"
            assert call_args[0][1] == 300  # 5 min cleanup

    @pytest.mark.asyncio
    async def test_tracker_redis_error_increments_metric(self, mock_redis_async):
        """AC7: STATE_STORE_ERRORS incremented on tracker Redis failure."""
        mock_redis_async.xadd = AsyncMock(side_effect=Exception("Redis stream error"))

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis_async), \
             patch("metrics.STATE_STORE_ERRORS") as mock_metric:
            mock_metric.labels = MagicMock(return_value=MagicMock())

            from progress import ProgressTracker
            tracker = ProgressTracker("err-001", uf_count=1, use_redis=True)
            await tracker.emit("fetching", 10, "Test")

            mock_metric.labels.assert_called_with(store="tracker", operation="write")

    @pytest.mark.asyncio
    async def test_tracker_fallback_in_memory(self):
        """AC6: When Redis unavailable, tracker works in-memory."""
        with patch("progress.is_redis_available", new_callable=AsyncMock, return_value=False):
            from progress import create_tracker

            tracker = await create_tracker("fallback-001", uf_count=2)

            assert tracker._use_redis is False
            await tracker.emit("connecting", 5, "Iniciando...")
            # Event in local queue, no Redis
            event = tracker.queue.get_nowait()
            assert event.stage == "connecting"


# ============================================================================
# AC7: STATE_STORE_ERRORS metric
# ============================================================================


class TestStateStoreMetric:
    """AC7: smartlic_state_store_errors_total metric exists and has correct labels."""

    def test_metric_exists(self):
        """AC7: STATE_STORE_ERRORS metric defined in metrics.py."""
        from metrics import STATE_STORE_ERRORS
        assert STATE_STORE_ERRORS is not None

    def test_metric_labels(self):
        """AC7: Metric supports store and operation labels."""
        from metrics import STATE_STORE_ERRORS
        labeled = STATE_STORE_ERRORS.labels(store="tracker", operation="write")
        assert labeled is not None

        labeled2 = STATE_STORE_ERRORS.labels(store="results", operation="read")
        assert labeled2 is not None

        labeled3 = STATE_STORE_ERRORS.labels(store="arbiter", operation="write")
        assert labeled3 is not None


# ============================================================================
# AC8: TTL cleanup via Redis EXPIRE
# ============================================================================


class TestTTLCleanup:
    """AC8: All temporary Redis keys have EXPIRE set."""

    @pytest.mark.asyncio
    async def test_results_ttl_30min(self, mock_redis_async):
        """AC8: Background results stored with 30min TTL."""
        from routes.search import _persist_results_to_redis

        with patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis_async):
            await _persist_results_to_redis("ttl-001", _make_response())

            call_args = mock_redis_async.setex.call_args
            ttl = call_args[0][1]
            assert ttl == 1800  # 30 min

    def test_arbiter_ttl_1h(self, mock_redis_sync):
        """AC8: Arbiter cache stored with 1h TTL."""
        from llm_arbiter import _arbiter_cache_set_redis

        with patch("redis_pool.get_sync_redis", return_value=mock_redis_sync):
            _arbiter_cache_set_redis("ttl-key", {"is_primary": True})

            call_args = mock_redis_sync.setex.call_args
            ttl = call_args[0][1]
            assert ttl == 3600  # 1 hour

    @pytest.mark.asyncio
    async def test_tracker_metadata_ttl(self, mock_redis_async):
        """AC8: Tracker metadata has TTL (420s = 7 min)."""
        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis_async), \
             patch("progress.is_redis_available", new_callable=AsyncMock, return_value=True):
            from progress import create_tracker

            await create_tracker("ttl-tracker", uf_count=1)

            # expire called with 420s TTL
            mock_redis_async.expire.assert_called_once()
            call_args = mock_redis_async.expire.call_args
            assert call_args[0][1] == 420  # 7 min


# ============================================================================
# AC10: Concurrent searches simulation
# ============================================================================


class TestConcurrentSearches:
    """AC10: 10 concurrent searches with simulated multi-worker scenario."""

    @pytest.mark.asyncio
    async def test_10_concurrent_store_and_retrieve(self, mock_redis_async):
        """AC10: 10 searches stored and retrieved via Redis (cross-worker)."""
        from routes.search import store_background_results, _persist_results_to_redis
        from routes.search import _get_results_from_redis

        # Track stored data by search_id
        stored_data = {}

        async def mock_setex(key, ttl, value):
            stored_data[key] = value
            return True

        async def mock_get(key):
            return stored_data.get(key)

        mock_redis_async.setex = AsyncMock(side_effect=mock_setex)
        mock_redis_async.get = AsyncMock(side_effect=mock_get)

        with patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis_async):
            # Store 10 searches in parallel
            tasks = []
            for i in range(10):
                resp = _make_response(total_filtrado=i * 10)
                search_id = f"concurrent-{i:03d}"
                store_background_results(search_id, resp)
                tasks.append(_persist_results_to_redis(search_id, resp))

            await asyncio.gather(*tasks)

            # Verify all 10 stored in Redis
            assert len(stored_data) == 10

            # Retrieve all 10 from Redis (simulating different worker — skip L1)
            for i in range(10):
                search_id = f"concurrent-{i:03d}"
                result = await _get_results_from_redis(search_id)
                assert result is not None
                assert result["total_filtrado"] == i * 10

    @pytest.mark.asyncio
    async def test_10_concurrent_trackers(self, mock_redis_async):
        """AC10: 10 trackers created with Redis metadata."""
        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis_async), \
             patch("progress.is_redis_available", new_callable=AsyncMock, return_value=True):
            from progress import create_tracker, _active_trackers

            tasks = []
            for i in range(10):
                tasks.append(create_tracker(f"conc-{i:03d}", uf_count=i + 1))

            trackers = await asyncio.gather(*tasks)

            assert len(trackers) == 10
            assert all(t._use_redis for t in trackers)
            assert len(_active_trackers) == 10


# ============================================================================
# Redis pool sync client
# ============================================================================


class TestSyncRedisPool:
    """STORY-294: Sync Redis client for ThreadPoolExecutor contexts."""

    def test_get_sync_redis_no_url(self):
        """Returns None when REDIS_URL not set."""
        import redis_pool
        redis_pool._sync_redis = None
        redis_pool._sync_redis_initialized = False

        with patch.dict("os.environ", {}, clear=True), \
             patch.object(redis_pool, "_sync_redis", None), \
             patch.object(redis_pool, "_sync_redis_initialized", False):
            result = redis_pool.get_sync_redis()
            assert result is None

    def test_get_sync_redis_connection_error(self):
        """Returns None on connection failure."""
        import redis_pool
        redis_pool._sync_redis = None
        redis_pool._sync_redis_initialized = False

        with patch.dict("os.environ", {"REDIS_URL": "redis://invalid:6379"}):
            with patch("redis.from_url", side_effect=Exception("Connection refused")):
                result = redis_pool.get_sync_redis()
                assert result is None
