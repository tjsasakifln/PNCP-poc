"""CRIT-083: Production Server Hardening — Tests.

Validates:
  AC1: railway.toml and start.sh use uvicorn spawn-based workers (not Gunicorn fork)
  AC5: WORKER_MEMORY_BYTES gauge exists in metrics
  AC6: Memory warning logged when worker exceeds 512MB RSS
  AC7: create_tracker uses Redis Streams when Redis is available (cross-worker SSE)
  AC8: SSE consumer on a different worker can discover tracker via Redis metadata
  AC9: graceful-timeout 120s configured in start.sh and railway.toml
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ============================================================================
# Helpers
# ============================================================================

def _backend_root() -> str:
    return os.path.join(os.path.dirname(__file__), "..")


def _read_start_sh() -> str:
    with open(os.path.join(_backend_root(), "start.sh")) as f:
        return f.read()


def _read_railway_toml() -> str:
    with open(os.path.join(_backend_root(), "railway.toml")) as f:
        return f.read()


# ============================================================================
# AC1: railway.toml startCommand uses uvicorn spawn workers
# ============================================================================


class TestAC1RailwayToml:
    """AC1: railway.toml startCommand uses uvicorn --workers (spawn-based)."""

    def test_startcommand_has_workers_flag(self):
        content = _read_railway_toml()
        assert "--workers ${WEB_CONCURRENCY:-2}" in content, (
            "railway.toml startCommand must use --workers ${WEB_CONCURRENCY:-2}"
        )

    def test_startcommand_uses_uvicorn_not_gunicorn(self):
        content = _read_railway_toml()
        lines = [ln for ln in content.splitlines() if "startCommand" in ln]
        assert lines, "startCommand not found in railway.toml"
        start_cmd = lines[0]
        assert "uvicorn" in start_cmd
        assert "gunicorn" not in start_cmd, (
            "startCommand must use uvicorn (spawn), not gunicorn (fork)"
        )

    def test_startcommand_has_default_2_workers(self):
        content = _read_railway_toml()
        assert "WEB_CONCURRENCY:-2" in content


# ============================================================================
# AC1: start.sh — uvicorn spawn is now the default runner
# ============================================================================


class TestAC1StartSh:
    """AC1: start.sh defaults to uvicorn spawn workers, keeps Gunicorn as opt-in."""

    def test_default_runner_is_uvicorn(self):
        content = _read_start_sh()
        assert 'RUNNER:-uvicorn' in content or '"${RUNNER:-uvicorn}"' in content, (
            "start.sh default RUNNER must be uvicorn (not gunicorn)"
        )

    def test_uvicorn_block_has_workers_flag(self):
        content = _read_start_sh()
        # --workers flag in uvicorn block
        assert '--workers "${WEB_CONCURRENCY:-2}"' in content or \
               '--workers "${WORKERS}"' in content, (
            "start.sh uvicorn block must use --workers for spawn-based multi-worker"
        )

    def test_gunicorn_remains_as_opt_in(self):
        """Gunicorn section stays for backward compat (tests check these strings)."""
        content = _read_start_sh()
        assert '-w "${WEB_CONCURRENCY:-2}"' in content, (
            "Gunicorn opt-in section must remain in start.sh"
        )
        assert "-c gunicorn_conf.py" in content


# ============================================================================
# AC5: WORKER_MEMORY_BYTES gauge exists
# ============================================================================


class TestAC5WorkerMemoryGauge:
    """AC5: WORKER_MEMORY_BYTES gauge defined in metrics module."""

    def test_worker_memory_bytes_gauge_exists(self):
        import metrics
        assert hasattr(metrics, "WORKER_MEMORY_BYTES"), (
            "metrics.WORKER_MEMORY_BYTES gauge must be defined (CRIT-083 AC5)"
        )

    def test_worker_memory_bytes_has_worker_pid_label(self):
        import metrics
        gauge = metrics.WORKER_MEMORY_BYTES
        # NoopMetric doesn't crash on .labels() — test it's callable
        try:
            labeled = gauge.labels(worker_pid="1234")
            labeled.set(1024 * 1024 * 100)  # 100MB — should not raise
        except Exception as e:
            pytest.fail(f"WORKER_MEMORY_BYTES.labels(worker_pid=...).set() raised: {e}")


# ============================================================================
# AC6: Memory warning at 512MB RSS
# ============================================================================


class TestAC6MemoryWarning:
    """AC6: Warning logged when worker RSS exceeds 512MB."""

    def test_lifespan_code_has_512mb_threshold(self):
        """Verify the 512MB threshold code is in startup/lifespan.py."""
        lifespan_path = os.path.join(
            _backend_root(), "startup", "lifespan.py"
        )
        with open(lifespan_path) as f:
            content = f.read()
        assert "512" in content, (
            "startup/lifespan.py must contain 512MB threshold for worker memory warning"
        )
        assert "AC6" in content, (
            "startup/lifespan.py must reference CRIT-083 AC6 in memory warning code"
        )

    @pytest.mark.asyncio
    async def test_memory_warning_logged_above_threshold(self):
        """_periodic_saturation_metrics emits WARNING when RSS > 512MB."""
        from startup.lifespan import _periodic_saturation_metrics

        # Patch at source module level (imports are local inside the function)
        mock_stats = {"used": 1, "max": 10}
        mock_mem = {"rss_mb": 600.0, "vms_mb": 800.0, "peak_rss_mb": 620.0}
        mock_metric = MagicMock()
        mock_metric.labels.return_value = mock_metric

        with patch("redis_pool.get_pool_stats", return_value=mock_stats), \
             patch("progress.get_active_tracker_count", return_value=0), \
             patch("routes.search.get_background_results_count", return_value=0), \
             patch("config.PNCP_BULKHEAD_CONCURRENCY", 5), \
             patch("config.PCP_BULKHEAD_CONCURRENCY", 5), \
             patch("config.COMPRASGOV_BULKHEAD_CONCURRENCY", 5), \
             patch("metrics.REDIS_POOL_CONNECTIONS_USED", mock_metric), \
             patch("metrics.REDIS_POOL_CONNECTIONS_MAX", mock_metric), \
             patch("metrics.HTTPX_POOL_CONNECTIONS_USED", mock_metric), \
             patch("metrics.TRACKER_ACTIVE_COUNT", mock_metric), \
             patch("metrics.BACKGROUND_RESULTS_COUNT", mock_metric), \
             patch("metrics.WORKER_MEMORY_BYTES", mock_metric), \
             patch("startup.lifespan._SATURATION_INTERVAL", 0), \
             patch("health.get_memory_usage", return_value=mock_mem), \
             patch("startup.lifespan.logger") as mock_logger:

            import asyncio
            task = asyncio.create_task(_periodic_saturation_metrics())
            await asyncio.sleep(0.05)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Check WARNING was logged for >512MB
        warning_calls = [
            call for call in mock_logger.warning.call_args_list
            if "512MB" in str(call) or "AC6" in str(call)
        ]
        assert warning_calls, (
            "Expected WARNING log for RSS > 512MB (CRIT-083 AC6)"
        )

    @pytest.mark.asyncio
    async def test_no_memory_warning_below_threshold(self):
        """No warning when RSS is below 512MB."""
        from startup.lifespan import _periodic_saturation_metrics

        mock_stats = {"used": 1, "max": 10}
        mock_mem = {"rss_mb": 200.0, "vms_mb": 300.0, "peak_rss_mb": 210.0}
        mock_metric = MagicMock()
        mock_metric.labels.return_value = mock_metric

        with patch("redis_pool.get_pool_stats", return_value=mock_stats), \
             patch("progress.get_active_tracker_count", return_value=0), \
             patch("routes.search.get_background_results_count", return_value=0), \
             patch("config.PNCP_BULKHEAD_CONCURRENCY", 5), \
             patch("config.PCP_BULKHEAD_CONCURRENCY", 5), \
             patch("config.COMPRASGOV_BULKHEAD_CONCURRENCY", 5), \
             patch("metrics.REDIS_POOL_CONNECTIONS_USED", mock_metric), \
             patch("metrics.REDIS_POOL_CONNECTIONS_MAX", mock_metric), \
             patch("metrics.HTTPX_POOL_CONNECTIONS_USED", mock_metric), \
             patch("metrics.TRACKER_ACTIVE_COUNT", mock_metric), \
             patch("metrics.BACKGROUND_RESULTS_COUNT", mock_metric), \
             patch("metrics.WORKER_MEMORY_BYTES", mock_metric), \
             patch("startup.lifespan._SATURATION_INTERVAL", 0), \
             patch("health.get_memory_usage", return_value=mock_mem), \
             patch("startup.lifespan.logger") as mock_logger:

            import asyncio
            task = asyncio.create_task(_periodic_saturation_metrics())
            await asyncio.sleep(0.05)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        warning_calls = [
            call for call in mock_logger.warning.call_args_list
            if "512MB" in str(call) or "AC6" in str(call)
        ]
        assert not warning_calls, (
            "Should NOT log 512MB warning when RSS is 200MB"
        )


# ============================================================================
# AC7: create_tracker uses Redis when available (cross-worker)
# ============================================================================


class TestAC7CrossWorkerTracker:
    """AC7: create_tracker automatically uses Redis Streams when Redis is available."""

    @pytest.mark.asyncio
    async def test_create_tracker_uses_redis_mode_when_available(self):
        """create_tracker() sets use_redis=True when Redis is available."""
        from progress import create_tracker, remove_tracker

        mock_redis = MagicMock()
        mock_redis.hset = AsyncMock(return_value=True)
        mock_redis.expire = AsyncMock(return_value=True)

        # Patch at progress module level — these are imported via `from redis_pool import`
        with patch("progress.is_redis_available", new=AsyncMock(return_value=True)), \
             patch("progress.get_redis_pool", new=AsyncMock(return_value=mock_redis)):
            tracker = await create_tracker("crit083-redis-test", uf_count=3)

        try:
            assert tracker._use_redis is True, (
                "Tracker must use Redis mode when Redis is available (CRIT-083 AC7)"
            )
        finally:
            with patch("progress.get_redis_pool", new=AsyncMock(return_value=mock_redis)):
                mock_redis.delete = AsyncMock(return_value=1)
                await remove_tracker("crit083-redis-test")

    @pytest.mark.asyncio
    async def test_create_tracker_falls_back_to_memory_without_redis(self):
        """create_tracker() falls back to in-memory when Redis is unavailable."""
        from progress import create_tracker, remove_tracker

        with patch("progress.is_redis_available", new=AsyncMock(return_value=False)):
            tracker = await create_tracker("crit083-memory-test", uf_count=2)

        try:
            assert tracker._use_redis is False, (
                "Tracker must fall back to in-memory when Redis unavailable"
            )
        finally:
            await remove_tracker("crit083-memory-test")

    @pytest.mark.asyncio
    async def test_tracker_metadata_stored_in_redis_for_cross_worker_discovery(self):
        """create_tracker() stores metadata in Redis for cross-worker SSE discovery."""
        from progress import create_tracker, remove_tracker

        mock_redis = MagicMock()
        hset_calls = []
        mock_redis.hset = AsyncMock(side_effect=lambda *a, **kw: hset_calls.append((a, kw)))
        mock_redis.expire = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=1)

        with patch("progress.is_redis_available", new=AsyncMock(return_value=True)), \
             patch("progress.get_redis_pool", new=AsyncMock(return_value=mock_redis)):
            await create_tracker("crit083-meta-test", uf_count=5)

        try:
            # Metadata must be stored so another worker can discover the tracker
            assert hset_calls, (
                "Redis hset must be called to store tracker metadata (CRIT-083 AC7)"
            )
            # Key should contain the search_id
            stored_keys = [str(call) for call in hset_calls]
            assert any("crit083-meta-test" in k for k in stored_keys)
        finally:
            with patch("progress.get_redis_pool", new=AsyncMock(return_value=mock_redis)):
                await remove_tracker("crit083-meta-test")


# ============================================================================
# AC8: Cross-worker SSE — worker B reads tracker via Redis metadata
# ============================================================================


class TestAC8CrossWorkerSSE:
    """AC8: SSE consumer on worker B can discover tracker created on worker A via Redis."""

    @pytest.mark.asyncio
    async def test_get_tracker_loads_from_redis_metadata(self):
        """get_tracker() returns a tracker loaded from Redis when not in local memory."""
        from progress import get_tracker, _active_trackers

        search_id = "crit083-cross-worker-sse"
        # Ensure not in local in-memory registry (simulates "worker B" scenario)
        _active_trackers.pop(search_id, None)

        # Simulate Redis metadata stored by "worker A"
        mock_redis = MagicMock()
        mock_redis.hgetall = AsyncMock(return_value={"uf_count": "4", "search_id": search_id})

        # Patch at progress module level
        with patch("progress.get_redis_pool", new=AsyncMock(return_value=mock_redis)):
            tracker = await get_tracker(search_id)

        try:
            assert tracker is not None, (
                "get_tracker() must recover tracker from Redis metadata (CRIT-083 AC8)"
            )
            assert tracker.search_id == search_id
            assert tracker.uf_count == 4
            assert tracker._use_redis is True, (
                "Recovered tracker must be in Redis mode for cross-worker SSE"
            )
        finally:
            _active_trackers.pop(search_id, None)

    @pytest.mark.asyncio
    async def test_get_tracker_returns_none_when_not_found(self):
        """get_tracker() returns None when tracker not in memory or Redis."""
        from progress import get_tracker, _active_trackers

        search_id = "crit083-not-found"
        _active_trackers.pop(search_id, None)

        mock_redis = MagicMock()
        mock_redis.hgetall = AsyncMock(return_value={})  # Empty — not found

        with patch("progress.get_redis_pool", new=AsyncMock(return_value=mock_redis)):
            tracker = await get_tracker(search_id)

        assert tracker is None


# ============================================================================
# AC9: graceful-timeout 120s aligned with drainingSeconds
# ============================================================================


class TestAC9GracefulTimeout:
    """AC9: graceful shutdown timeout aligned with Railway drainingSeconds=120s."""

    def test_start_sh_uvicorn_has_graceful_shutdown_120(self):
        content = _read_start_sh()
        assert "--timeout-graceful-shutdown 120" in content, (
            "start.sh uvicorn block must set --timeout-graceful-shutdown 120 "
            "to align with Railway drainingSeconds=120 (CRIT-083 AC9)"
        )

    def test_railway_toml_has_draining_120(self):
        content = _read_railway_toml()
        assert "drainingSeconds = 120" in content, (
            "railway.toml must have drainingSeconds = 120 (CRIT-083 AC9)"
        )

    def test_railway_toml_startcommand_has_graceful_shutdown_120(self):
        content = _read_railway_toml()
        assert "--timeout-graceful-shutdown 120" in content, (
            "railway.toml startCommand must include --timeout-graceful-shutdown 120"
        )


# ============================================================================
# AC10 (already done): SSE shutdown event is in terminal stages
# ============================================================================


class TestAC10SseShutdownEvent:
    """AC10: shutdown is a terminal stage (already implemented in DEBT-124)."""

    def test_shutdown_in_terminal_stages(self):
        from progress import _TERMINAL_STAGES
        assert "shutdown" in _TERMINAL_STAGES, (
            "'shutdown' must be a terminal SSE stage (CRIT-083 AC10, DEBT-124)"
        )


# ============================================================================
# Existing invariants preserved
# ============================================================================


class TestExistingInvariantsPreserved:
    """Existing tests must continue to pass — Gunicorn opt-in section preserved."""

    def test_web_concurrency_default_2_still_present(self):
        content = _read_start_sh()
        assert "WEB_CONCURRENCY:-2" in content

    def test_gunicorn_keep_alive_still_present(self):
        content = _read_start_sh()
        assert "GUNICORN_KEEP_ALIVE:-75" in content

    def test_gunicorn_graceful_timeout_still_present(self):
        """GUNICORN_GRACEFUL_TIMEOUT env var still used in Gunicorn opt-in section."""
        content = _read_start_sh()
        # The actual line: GUNICORN_GRACEFUL_TIMEOUT="${GUNICORN_GRACEFUL_TIMEOUT:-${GRACEFUL_SHUTDOWN_TIMEOUT:-30}}"
        assert "GUNICORN_GRACEFUL_TIMEOUT" in content

    def test_gunicorn_conf_reference_still_present(self):
        content = _read_start_sh()
        assert "-c gunicorn_conf.py" in content
