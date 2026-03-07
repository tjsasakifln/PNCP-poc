"""HARDEN-024: Tests for saturation metrics (connection pools, queue depth).

Tests cover:
- AC1: Gauge smartlic_redis_pool_connections_used
- AC2: Gauge smartlic_redis_pool_connections_max
- AC3: Gauge smartlic_httpx_pool_connections_used per source
- AC4: Gauge smartlic_tracker_active_count
- AC5: Gauge smartlic_background_results_count
- AC6: Background task reports metrics every 30s
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

import metrics as m


# ============================================================================
# AC1/AC2: Redis pool gauges
# ============================================================================


class TestRedisPoolGauges:
    """AC1/AC2: Redis pool connection gauges are defined and functional."""

    def test_redis_pool_connections_used_exists(self):
        """AC1: smartlic_redis_pool_connections_used gauge exists."""
        assert hasattr(m, "REDIS_POOL_CONNECTIONS_USED")
        m.REDIS_POOL_CONNECTIONS_USED.set(5)

    def test_redis_pool_connections_max_exists(self):
        """AC2: smartlic_redis_pool_connections_max gauge exists."""
        assert hasattr(m, "REDIS_POOL_CONNECTIONS_MAX")
        m.REDIS_POOL_CONNECTIONS_MAX.set(50)


class TestGetPoolStats:
    """AC1/AC2: redis_pool.get_pool_stats() returns usage info."""

    def test_returns_zeros_when_no_redis(self):
        """Returns zeros when Redis is not initialized."""
        from redis_pool import get_pool_stats
        with patch("redis_pool._redis_pool", None):
            stats = get_pool_stats()
            assert stats == {"used": 0, "max": 0}

    def test_returns_stats_from_pool(self):
        """Returns actual pool stats when Redis is available."""
        from redis_pool import get_pool_stats

        mock_pool = MagicMock()
        mock_pool.connection_pool._in_use_connections = {"conn1", "conn2"}
        mock_pool.connection_pool.max_connections = 50

        with patch("redis_pool._redis_pool", mock_pool):
            stats = get_pool_stats()
            assert stats["used"] == 2
            assert stats["max"] == 50

    def test_handles_missing_attributes(self):
        """Gracefully handles pool objects without expected attributes."""
        from redis_pool import get_pool_stats

        mock_pool = MagicMock()
        # Remove the attributes
        del mock_pool.connection_pool._in_use_connections
        del mock_pool.connection_pool.max_connections

        with patch("redis_pool._redis_pool", mock_pool):
            stats = get_pool_stats()
            assert stats["used"] == 0
            assert stats["max"] == 0

    def test_handles_exception(self):
        """Returns zeros on any exception."""
        from redis_pool import get_pool_stats

        mock_pool = MagicMock()
        mock_pool.connection_pool = property(lambda self: (_ for _ in ()).throw(RuntimeError))

        with patch("redis_pool._redis_pool", mock_pool):
            stats = get_pool_stats()
            assert stats["used"] == 0
            assert stats["max"] == 0


# ============================================================================
# AC3: httpx pool connections per source
# ============================================================================


class TestHttpxPoolGauge:
    """AC3: httpx pool connections gauge with source labels."""

    def test_httpx_gauge_exists(self):
        """AC3: smartlic_httpx_pool_connections_used gauge exists."""
        assert hasattr(m, "HTTPX_POOL_CONNECTIONS_USED")

    def test_httpx_gauge_per_source(self):
        """AC3: Can set gauge for each data source."""
        m.HTTPX_POOL_CONNECTIONS_USED.labels(source="pncp").set(7)
        m.HTTPX_POOL_CONNECTIONS_USED.labels(source="pcp").set(5)
        m.HTTPX_POOL_CONNECTIONS_USED.labels(source="comprasgov").set(5)


# ============================================================================
# AC4: Tracker active count
# ============================================================================


class TestTrackerActiveCount:
    """AC4: Active progress tracker count gauge."""

    def test_tracker_gauge_exists(self):
        """AC4: smartlic_tracker_active_count gauge exists."""
        assert hasattr(m, "TRACKER_ACTIVE_COUNT")
        m.TRACKER_ACTIVE_COUNT.set(3)

    def test_get_active_tracker_count(self):
        """AC4: get_active_tracker_count returns tracker dict length."""
        from progress import get_active_tracker_count, _active_trackers

        original = dict(_active_trackers)
        try:
            _active_trackers.clear()
            assert get_active_tracker_count() == 0

            _active_trackers["search-1"] = MagicMock()
            _active_trackers["search-2"] = MagicMock()
            assert get_active_tracker_count() == 2
        finally:
            _active_trackers.clear()
            _active_trackers.update(original)


# ============================================================================
# AC5: Background results count
# ============================================================================


class TestBackgroundResultsCount:
    """AC5: Background results in-memory count gauge."""

    def test_background_gauge_exists(self):
        """AC5: smartlic_background_results_count gauge exists."""
        assert hasattr(m, "BACKGROUND_RESULTS_COUNT")
        m.BACKGROUND_RESULTS_COUNT.set(10)

    def test_get_background_results_count(self):
        """AC5: get_background_results_count returns dict length."""
        from routes.search import get_background_results_count, _background_results

        original = dict(_background_results)
        try:
            _background_results.clear()
            assert get_background_results_count() == 0

            _background_results["s1"] = {"response": None, "stored_at": 0}
            _background_results["s2"] = {"response": None, "stored_at": 0}
            _background_results["s3"] = {"response": None, "stored_at": 0}
            assert get_background_results_count() == 3
        finally:
            _background_results.clear()
            _background_results.update(original)


# ============================================================================
# AC6: Background task reports metrics periodically
# ============================================================================


class TestPeriodicSaturationMetrics:
    """AC6: Background task runs and reports all saturation metrics."""

    @pytest.mark.asyncio
    async def test_periodic_task_reports_metrics(self):
        """AC6: _periodic_saturation_metrics sets all gauges each cycle."""
        from main import _periodic_saturation_metrics, _SATURATION_INTERVAL

        # Verify interval is 30s
        assert _SATURATION_INTERVAL == 30

        gauges_set = {
            "redis_used": False,
            "redis_max": False,
            "httpx_pncp": False,
            "httpx_pcp": False,
            "httpx_comprasgov": False,
            "tracker": False,
            "background": False,
        }

        original_set = m.REDIS_POOL_CONNECTIONS_USED.set

        def track_redis_used(v):
            gauges_set["redis_used"] = True
            original_set(v)

        original_max_set = m.REDIS_POOL_CONNECTIONS_MAX.set

        def track_redis_max(v):
            gauges_set["redis_max"] = True
            original_max_set(v)

        original_tracker_set = m.TRACKER_ACTIVE_COUNT.set

        def track_tracker(v):
            gauges_set["tracker"] = True
            original_tracker_set(v)

        original_bg_set = m.BACKGROUND_RESULTS_COUNT.set

        def track_bg(v):
            gauges_set["background"] = True
            original_bg_set(v)

        with patch.object(m.REDIS_POOL_CONNECTIONS_USED, "set", side_effect=track_redis_used), \
             patch.object(m.REDIS_POOL_CONNECTIONS_MAX, "set", side_effect=track_redis_max), \
             patch.object(m.TRACKER_ACTIVE_COUNT, "set", side_effect=track_tracker), \
             patch.object(m.BACKGROUND_RESULTS_COUNT, "set", side_effect=track_bg), \
             patch("main._SATURATION_INTERVAL", 0.01), \
             patch("redis_pool.get_pool_stats", return_value={"used": 3, "max": 50}), \
             patch("progress.get_active_tracker_count", return_value=2), \
             patch("routes.search.get_background_results_count", return_value=5):

            task = asyncio.create_task(_periodic_saturation_metrics())
            await asyncio.sleep(0.05)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            assert gauges_set["redis_used"], "REDIS_POOL_CONNECTIONS_USED not set"
            assert gauges_set["redis_max"], "REDIS_POOL_CONNECTIONS_MAX not set"
            assert gauges_set["tracker"], "TRACKER_ACTIVE_COUNT not set"
            assert gauges_set["background"], "BACKGROUND_RESULTS_COUNT not set"

    @pytest.mark.asyncio
    async def test_periodic_task_handles_errors(self):
        """AC6: Task continues on errors (doesn't crash)."""
        from main import _periodic_saturation_metrics

        with patch("main._SATURATION_INTERVAL", 0.01), \
             patch("redis_pool.get_pool_stats", side_effect=RuntimeError("test")):

            task = asyncio.create_task(_periodic_saturation_metrics())
            await asyncio.sleep(0.05)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            # Should not have crashed — just logged warning

    @pytest.mark.asyncio
    async def test_periodic_task_cancellation(self):
        """AC6: Task exits cleanly on cancellation."""
        from main import _periodic_saturation_metrics

        with patch("main._SATURATION_INTERVAL", 0.01), \
             patch("redis_pool.get_pool_stats", return_value={"used": 0, "max": 0}), \
             patch("progress.get_active_tracker_count", return_value=0), \
             patch("routes.search.get_background_results_count", return_value=0):

            task = asyncio.create_task(_periodic_saturation_metrics())
            await asyncio.sleep(0.03)
            task.cancel()
            await task  # Should complete without raising (clean exit)


# ============================================================================
# Integration: All metrics appear in /metrics output
# ============================================================================


class TestSaturationMetricsInOutput:
    """Verify all HARDEN-024 metrics appear in Prometheus output."""

    def test_all_saturation_metrics_in_output(self):
        """All 5 saturation gauges appear in /metrics text."""
        from prometheus_client import generate_latest, REGISTRY

        # Set values so they appear in output
        m.REDIS_POOL_CONNECTIONS_USED.set(1)
        m.REDIS_POOL_CONNECTIONS_MAX.set(50)
        m.HTTPX_POOL_CONNECTIONS_USED.labels(source="pncp").set(7)
        m.TRACKER_ACTIVE_COUNT.set(0)
        m.BACKGROUND_RESULTS_COUNT.set(0)

        output = generate_latest(REGISTRY).decode("utf-8")

        assert "smartlic_redis_pool_connections_used" in output
        assert "smartlic_redis_pool_connections_max" in output
        assert "smartlic_httpx_pool_connections_used" in output
        assert "smartlic_tracker_active_count" in output
        assert "smartlic_background_results_count" in output
