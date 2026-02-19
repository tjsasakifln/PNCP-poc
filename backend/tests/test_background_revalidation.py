"""B-01: Background Stale-While-Revalidate Tests.

Tests for all 10 ACs of GTM-RESILIENCE-B01.
"""

import asyncio
import json
import logging
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch, Mock

# Suppress unawaited coroutine warnings from mocked asyncio.create_task
pytestmark = pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")


# ---------------------------------------------------------------------------
# AC1 — Background task triggered after stale cache
# ---------------------------------------------------------------------------


class TestAC1_BackgroundTaskTriggered:
    """AC1: asyncio.create_task called when stale cache is served."""

    @pytest.mark.asyncio
    async def test_trigger_dispatches_task_on_stale(self):
        """When all pre-checks pass, asyncio.create_task is called."""
        mock_cb = MagicMock()
        mock_cb.is_degraded = False

        with (
            patch("search_cache.compute_search_hash", return_value="abc123hash"),
            patch("search_cache._mark_revalidating", new_callable=AsyncMock, return_value=True),
            patch("search_cache._get_revalidation_lock") as mock_lock,
            patch("pncp_client.get_circuit_breaker", return_value=mock_cb),
            patch("search_cache.asyncio") as mock_asyncio,
            patch("config.MAX_CONCURRENT_REVALIDATIONS", 3),
            patch("config.REVALIDATION_COOLDOWN_S", 600),
        ):
            lock_instance = AsyncMock()
            lock_instance.__aenter__ = AsyncMock(return_value=None)
            lock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_lock.return_value = lock_instance

            mock_asyncio.create_task = MagicMock()

            import search_cache
            search_cache._active_revalidations = 0
            try:
                result = await search_cache.trigger_background_revalidation(
                    user_id="user-1",
                    params={"setor_id": 1, "ufs": ["SP"]},
                    request_data={
                        "ufs": ["SP"],
                        "data_inicial": "2026-02-01",
                        "data_final": "2026-02-10",
                        "modalidades": [6],
                    },
                    search_id="search-abc",
                )

                assert result is True
                mock_asyncio.create_task.assert_called_once()
                # Close orphan coroutine created by mocked create_task
                coro = mock_asyncio.create_task.call_args[0][0]
                coro.close()
            finally:
                search_cache._active_revalidations = 0

    @pytest.mark.asyncio
    async def test_pipeline_helper_triggers_on_stale(self):
        """_maybe_trigger_revalidation calls trigger when stale_cache.is_stale=True."""
        mock_request = MagicMock()
        mock_request.ufs = ["SP"]
        mock_request.data_inicial = "2026-02-01"
        mock_request.data_final = "2026-02-10"
        mock_request.modalidades = [6]
        mock_request.setor_id = 1
        mock_request.status = None
        mock_request.modo_busca = "publicacao"
        mock_request.search_id = "search-1"

        stale_cache = {"is_stale": True, "results": [{"id": 1}]}

        with patch("search_cache.trigger_background_revalidation", new_callable=AsyncMock, return_value=True) as mock_trigger:
            from search_pipeline import _maybe_trigger_revalidation
            await _maybe_trigger_revalidation("user-1", mock_request, stale_cache)

            mock_trigger.assert_called_once()

    @pytest.mark.asyncio
    async def test_pipeline_helper_skips_fresh_cache(self):
        """_maybe_trigger_revalidation does nothing when cache is not stale."""
        stale_cache = {"is_stale": False, "results": []}

        with patch("search_cache.trigger_background_revalidation", new_callable=AsyncMock) as mock_trigger:
            from search_pipeline import _maybe_trigger_revalidation
            await _maybe_trigger_revalidation("user-1", MagicMock(), stale_cache)
            mock_trigger.assert_not_called()

    @pytest.mark.asyncio
    async def test_pipeline_helper_skips_none_cache(self):
        """_maybe_trigger_revalidation does nothing when no cache."""
        with patch("search_cache.trigger_background_revalidation", new_callable=AsyncMock) as mock_trigger:
            from search_pipeline import _maybe_trigger_revalidation
            await _maybe_trigger_revalidation("user-1", MagicMock(), None)
            mock_trigger.assert_not_called()


# ---------------------------------------------------------------------------
# AC2 — Revalidation updates cache at all levels
# ---------------------------------------------------------------------------


class TestAC2_CacheUpdated:
    """AC2: On success, save_to_cache is called with new results."""

    @pytest.mark.asyncio
    async def test_successful_revalidation_saves_to_cache(self):
        """Successful fetch calls save_to_cache with results and metadata."""
        mock_results = [{"id": 1}, {"id": 2}, {"id": 3}]

        import search_cache
        search_cache._active_revalidations = 1
        search_cache._revalidation_lock = None

        with (
            patch("search_cache.save_to_cache", new_callable=AsyncMock) as mock_save,
            patch("pncp_client.buscar_todas_ufs_paralelo", new_callable=AsyncMock, return_value=mock_results),
        ):
            await search_cache._do_revalidation(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
                params_hash="abc123",
                request_data={
                    "ufs": ["SP"],
                    "data_inicial": "2026-02-01",
                    "data_final": "2026-02-10",
                },
                search_id=None,
            )

            mock_save.assert_called_once()
            call_kwargs = mock_save.call_args[1]
            assert call_kwargs["user_id"] == "user-1"
            assert len(call_kwargs["results"]) == 3
            assert call_kwargs["sources"] == ["PNCP"]
            assert "fetch_duration_ms" in call_kwargs
            assert "coverage" in call_kwargs


# ---------------------------------------------------------------------------
# AC3 — Dedup concurrent revalidations
# ---------------------------------------------------------------------------


class TestAC3_Dedup:
    """AC3: Only 1 revalidation per params_hash at a time."""

    @pytest.mark.asyncio
    async def test_second_revalidation_skipped(self):
        """If _mark_revalidating returns False, trigger returns False."""
        mock_cb = MagicMock()
        mock_cb.is_degraded = False

        with (
            patch("search_cache.compute_search_hash", return_value="abc123"),
            patch("search_cache._mark_revalidating", new_callable=AsyncMock, return_value=False),
            patch("pncp_client.get_circuit_breaker", return_value=mock_cb),
            patch("config.REVALIDATION_COOLDOWN_S", 600),
        ):
            from search_cache import trigger_background_revalidation
            result = await trigger_background_revalidation(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
                request_data={"ufs": ["SP"], "data_inicial": "2026-02-01", "data_final": "2026-02-10"},
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_mark_revalidating_inmemory_dedup(self):
        """InMemory fallback prevents duplicate marks."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None  # First call: not revalidating

        with (
            patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=None),
            patch("redis_pool.get_fallback_cache", return_value=mock_cache),
        ):
            from search_cache import _mark_revalidating
            result = await _mark_revalidating("hash123", 600)
            assert result is True
            mock_cache.setex.assert_called_once_with("revalidating:hash123", 600, "1")

    @pytest.mark.asyncio
    async def test_mark_revalidating_already_marked(self):
        """If key exists in InMemory, _mark_revalidating returns False."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = "1"  # Already revalidating

        with (
            patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=None),
            patch("redis_pool.get_fallback_cache", return_value=mock_cache),
        ):
            from search_cache import _mark_revalidating
            result = await _mark_revalidating("hash123", 600)
            assert result is False


# ---------------------------------------------------------------------------
# AC4 — Budget limit for concurrent revalidations
# ---------------------------------------------------------------------------


class TestAC4_BudgetLimit:
    """AC4: Max 3 concurrent revalidations per worker."""

    @pytest.mark.asyncio
    async def test_budget_exceeded_skips_revalidation(self):
        """When _active_revalidations >= MAX, trigger returns False."""
        import search_cache
        original = search_cache._active_revalidations
        mock_cb = MagicMock()
        mock_cb.is_degraded = False

        try:
            search_cache._active_revalidations = 3

            with (
                patch("search_cache.compute_search_hash", return_value="abc123"),
                patch("search_cache._mark_revalidating", new_callable=AsyncMock, return_value=True),
                patch("search_cache._clear_revalidating", new_callable=AsyncMock),
                patch("pncp_client.get_circuit_breaker", return_value=mock_cb),
                patch("config.MAX_CONCURRENT_REVALIDATIONS", 3),
                patch("config.REVALIDATION_COOLDOWN_S", 600),
            ):
                result = await search_cache.trigger_background_revalidation(
                    user_id="user-1",
                    params={"setor_id": 1, "ufs": ["SP"]},
                    request_data={"ufs": ["SP"], "data_inicial": "2026-02-01", "data_final": "2026-02-10"},
                )

                assert result is False
        finally:
            search_cache._active_revalidations = original

    @pytest.mark.asyncio
    async def test_budget_slot_released_after_revalidation(self):
        """After _do_revalidation completes, _active_revalidations is decremented."""
        import search_cache
        search_cache._active_revalidations = 1
        search_cache._revalidation_lock = None

        with patch("pncp_client.buscar_todas_ufs_paralelo", new_callable=AsyncMock, return_value=[]):
            await search_cache._do_revalidation(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
                params_hash="abc123",
                request_data={"ufs": ["SP"], "data_inicial": "2026-02-01", "data_final": "2026-02-10"},
                search_id=None,
            )

            assert search_cache._active_revalidations == 0


# ---------------------------------------------------------------------------
# AC5 — Independent revalidation timeout
# ---------------------------------------------------------------------------


class TestAC5_IndependentTimeout:
    """AC5: Revalidation has its own 180s timeout."""

    @pytest.mark.asyncio
    async def test_revalidation_times_out_independently(self):
        """Fetch taking too long is canceled by REVALIDATION_TIMEOUT."""
        import search_cache
        search_cache._active_revalidations = 1
        search_cache._revalidation_lock = None

        async def slow_fetch(**kwargs):
            await asyncio.sleep(10)  # Will be canceled by timeout
            return []

        with (
            patch("pncp_client.buscar_todas_ufs_paralelo", side_effect=slow_fetch),
            patch("config.REVALIDATION_TIMEOUT", 0.1),  # 100ms timeout
            patch("search_cache.record_cache_fetch_failure", new_callable=AsyncMock) as mock_fail,
        ):
            await search_cache._do_revalidation(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
                params_hash="timeout_hash",
                request_data={"ufs": ["SP"], "data_inicial": "2026-02-01", "data_final": "2026-02-10"},
                search_id=None,
            )

            # AC9: Timeout should record failure
            mock_fail.assert_called_once_with("user-1", "timeout_hash")
            assert search_cache._active_revalidations == 0


# ---------------------------------------------------------------------------
# AC6 — Circuit breaker check before revalidating
# ---------------------------------------------------------------------------


class TestAC6_CircuitBreakerCheck:
    """AC6: Skip revalidation if PNCP circuit breaker is degraded."""

    @pytest.mark.asyncio
    async def test_degraded_cb_skips_revalidation(self):
        """When circuit breaker is_degraded=True, trigger returns False."""
        mock_cb = MagicMock()
        mock_cb.is_degraded = True

        with (
            patch("search_cache.compute_search_hash", return_value="abc123"),
            patch("pncp_client.get_circuit_breaker", return_value=mock_cb),
            patch("config.REVALIDATION_COOLDOWN_S", 600),
        ):
            from search_cache import trigger_background_revalidation
            result = await trigger_background_revalidation(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
                request_data={"ufs": ["SP"], "data_inicial": "2026-02-01", "data_final": "2026-02-10"},
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_healthy_cb_allows_revalidation(self):
        """When circuit breaker is healthy, revalidation proceeds."""
        mock_cb = MagicMock()
        mock_cb.is_degraded = False

        with (
            patch("search_cache.compute_search_hash", return_value="abc123"),
            patch("search_cache._mark_revalidating", new_callable=AsyncMock, return_value=True),
            patch("search_cache._get_revalidation_lock") as mock_lock,
            patch("pncp_client.get_circuit_breaker", return_value=mock_cb),
            patch("search_cache.asyncio") as mock_asyncio,
            patch("config.MAX_CONCURRENT_REVALIDATIONS", 3),
            patch("config.REVALIDATION_COOLDOWN_S", 600),
        ):
            lock_instance = AsyncMock()
            lock_instance.__aenter__ = AsyncMock(return_value=None)
            lock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_lock.return_value = lock_instance

            mock_asyncio.create_task = MagicMock()

            import search_cache
            search_cache._active_revalidations = 0
            try:
                result = await search_cache.trigger_background_revalidation(
                    user_id="user-1",
                    params={"setor_id": 1, "ufs": ["SP"]},
                    request_data={"ufs": ["SP"], "data_inicial": "2026-02-01", "data_final": "2026-02-10"},
                )

                assert result is True
                # Close orphan coroutine created by mocked create_task
                coro = mock_asyncio.create_task.call_args[0][0]
                coro.close()
            finally:
                search_cache._active_revalidations = 0


# ---------------------------------------------------------------------------
# AC7 — SSE notification when user connected
# ---------------------------------------------------------------------------


class TestAC7_SSENotification:
    """AC7: Emit 'revalidated' event if ProgressTracker still active."""

    @pytest.mark.asyncio
    async def test_emits_revalidated_when_tracker_active(self):
        """If tracker exists and not complete, emit_revalidated is called."""
        mock_tracker = AsyncMock()
        mock_tracker._is_complete = False
        mock_tracker.emit_revalidated = AsyncMock()

        import search_cache
        search_cache._active_revalidations = 1
        search_cache._revalidation_lock = None

        with (
            patch("pncp_client.buscar_todas_ufs_paralelo", new_callable=AsyncMock, return_value=[{"id": 1}]),
            patch("search_cache.save_to_cache", new_callable=AsyncMock),
            patch("progress.get_tracker", new_callable=AsyncMock, return_value=mock_tracker),
        ):
            await search_cache._do_revalidation(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
                params_hash="abc123",
                request_data={"ufs": ["SP"], "data_inicial": "2026-02-01", "data_final": "2026-02-10"},
                search_id="search-xyz",
            )

            mock_tracker.emit_revalidated.assert_called_once()
            call_kwargs = mock_tracker.emit_revalidated.call_args[1]
            assert call_kwargs["total_results"] == 1

    @pytest.mark.asyncio
    async def test_skips_sse_when_tracker_complete(self):
        """If tracker._is_complete=True, emit_revalidated is NOT called."""
        mock_tracker = AsyncMock()
        mock_tracker._is_complete = True
        mock_tracker.emit_revalidated = AsyncMock()

        import search_cache
        search_cache._active_revalidations = 1
        search_cache._revalidation_lock = None

        with (
            patch("pncp_client.buscar_todas_ufs_paralelo", new_callable=AsyncMock, return_value=[{"id": 1}]),
            patch("search_cache.save_to_cache", new_callable=AsyncMock),
            patch("progress.get_tracker", new_callable=AsyncMock, return_value=mock_tracker),
        ):
            await search_cache._do_revalidation(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
                params_hash="abc123",
                request_data={"ufs": ["SP"], "data_inicial": "2026-02-01", "data_final": "2026-02-10"},
                search_id="search-xyz",
            )

            mock_tracker.emit_revalidated.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_sse_when_no_search_id(self):
        """If search_id is None, SSE notification is skipped entirely."""
        import search_cache
        search_cache._active_revalidations = 1
        search_cache._revalidation_lock = None

        with (
            patch("pncp_client.buscar_todas_ufs_paralelo", new_callable=AsyncMock, return_value=[{"id": 1}]),
            patch("search_cache.save_to_cache", new_callable=AsyncMock),
            patch("progress.get_tracker", new_callable=AsyncMock) as mock_get_tracker,
        ):
            await search_cache._do_revalidation(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
                params_hash="abc123",
                request_data={"ufs": ["SP"], "data_inicial": "2026-02-01", "data_final": "2026-02-10"},
                search_id=None,
            )

            mock_get_tracker.assert_not_called()


# ---------------------------------------------------------------------------
# AC8 — Structured logging of revalidation
# ---------------------------------------------------------------------------


class TestAC8_StructuredLogging:
    """AC8: Each revalidation generates 1 JSON log with required fields."""

    @pytest.mark.asyncio
    async def test_revalidation_log_has_required_fields(self, caplog):
        """Log contains params_hash, trigger, duration_ms, result, new_results_count."""
        import search_cache
        search_cache._active_revalidations = 1
        search_cache._revalidation_lock = None

        with (
            patch("pncp_client.buscar_todas_ufs_paralelo", new_callable=AsyncMock, return_value=[{"id": 1}, {"id": 2}]),
            patch("search_cache.save_to_cache", new_callable=AsyncMock),
            caplog.at_level(logging.INFO, logger="search_cache"),
        ):
            await search_cache._do_revalidation(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
                params_hash="abc123hash45678",
                request_data={"ufs": ["SP"], "data_inicial": "2026-02-01", "data_final": "2026-02-10"},
                search_id=None,
            )

        # Find the revalidation_complete log
        complete_logs = [
            r for r in caplog.records
            if "revalidation_complete" in r.message
        ]
        assert len(complete_logs) == 1

        log_data = json.loads(complete_logs[0].message)
        assert log_data["event"] == "revalidation_complete"
        assert log_data["params_hash"] == "abc123hash45"  # First 12 chars
        assert log_data["trigger"] == "stale_served"
        assert isinstance(log_data["duration_ms"], int)
        assert log_data["result"] == "success"
        assert log_data["new_results_count"] == 2

    @pytest.mark.asyncio
    async def test_timeout_log_records_timeout_result(self, caplog):
        """Timeout revalidation logs result='timeout'."""
        import search_cache
        search_cache._active_revalidations = 1
        search_cache._revalidation_lock = None

        async def slow_fetch(**kwargs):
            await asyncio.sleep(10)
            return []

        with (
            patch("pncp_client.buscar_todas_ufs_paralelo", side_effect=slow_fetch),
            patch("config.REVALIDATION_TIMEOUT", 0.05),
            patch("search_cache.record_cache_fetch_failure", new_callable=AsyncMock),
            caplog.at_level(logging.INFO, logger="search_cache"),
        ):
            await search_cache._do_revalidation(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
                params_hash="abc123hash45678",
                request_data={"ufs": ["SP"], "data_inicial": "2026-02-01", "data_final": "2026-02-10"},
                search_id=None,
            )

        complete_logs = [
            r for r in caplog.records
            if "revalidation_complete" in r.message
        ]
        assert len(complete_logs) == 1
        log_data = json.loads(complete_logs[0].message)
        assert log_data["result"] == "timeout"


# ---------------------------------------------------------------------------
# AC9 — Health metadata updated
# ---------------------------------------------------------------------------


class TestAC9_HealthMetadata:
    """AC9: Success resets fail_streak; failure increments fail_streak."""

    @pytest.mark.asyncio
    async def test_successful_revalidation_resets_health(self):
        """save_to_cache is called (which resets fail_streak=0 internally)."""
        import search_cache
        search_cache._active_revalidations = 1
        search_cache._revalidation_lock = None

        with (
            patch("pncp_client.buscar_todas_ufs_paralelo", new_callable=AsyncMock, return_value=[{"id": 1}]),
            patch("search_cache.save_to_cache", new_callable=AsyncMock) as mock_save,
            patch("search_cache.record_cache_fetch_failure", new_callable=AsyncMock) as mock_fail,
        ):
            await search_cache._do_revalidation(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
                params_hash="abc123",
                request_data={"ufs": ["SP"], "data_inicial": "2026-02-01", "data_final": "2026-02-10"},
                search_id=None,
            )

            mock_save.assert_called_once()
            mock_fail.assert_not_called()

    @pytest.mark.asyncio
    async def test_failed_revalidation_records_failure(self):
        """On fetch error, record_cache_fetch_failure is called."""
        import search_cache
        search_cache._active_revalidations = 1
        search_cache._revalidation_lock = None

        with (
            patch("pncp_client.buscar_todas_ufs_paralelo", new_callable=AsyncMock, side_effect=ConnectionError("PNCP down")),
            patch("search_cache.save_to_cache", new_callable=AsyncMock) as mock_save,
            patch("search_cache.record_cache_fetch_failure", new_callable=AsyncMock) as mock_fail,
        ):
            await search_cache._do_revalidation(
                user_id="user-1",
                params={"setor_id": 1, "ufs": ["SP"]},
                params_hash="fail_hash",
                request_data={"ufs": ["SP"], "data_inicial": "2026-02-01", "data_final": "2026-02-10"},
                search_id=None,
            )

            mock_save.assert_not_called()
            mock_fail.assert_called_once_with("user-1", "fail_hash")


# ---------------------------------------------------------------------------
# AC10 — No regression in synchronous pipeline
# ---------------------------------------------------------------------------


class TestAC10_NoRegression:
    """AC10: _maybe_trigger_revalidation is fully non-blocking and non-fatal."""

    @pytest.mark.asyncio
    async def test_trigger_exception_does_not_propagate(self):
        """If trigger_background_revalidation raises, it's caught silently."""
        mock_request = MagicMock()
        mock_request.ufs = ["SP"]
        mock_request.data_inicial = "2026-02-01"
        mock_request.data_final = "2026-02-10"
        mock_request.modalidades = [6]
        mock_request.setor_id = 1
        mock_request.status = None
        mock_request.modo_busca = "publicacao"
        mock_request.search_id = "s-1"

        stale_cache = {"is_stale": True, "results": []}

        with patch(
            "search_cache.trigger_background_revalidation",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Unexpected error"),
        ):
            from search_pipeline import _maybe_trigger_revalidation
            # Should NOT raise
            await _maybe_trigger_revalidation("user-1", mock_request, stale_cache)


# ---------------------------------------------------------------------------
# ProgressTracker.emit_revalidated
# ---------------------------------------------------------------------------


class TestEmitRevalidated:
    """B-01 AC7: ProgressTracker.emit_revalidated method."""

    @pytest.mark.asyncio
    async def test_emit_revalidated_puts_event_in_queue(self):
        """emit_revalidated puts a 'revalidated' event in the queue."""
        from progress import ProgressTracker
        tracker = ProgressTracker(search_id="test-1", uf_count=3)

        await tracker.emit_revalidated(total_results=42, fetched_at="2026-02-19T12:00:00Z")

        event = tracker.queue.get_nowait()
        assert event.stage == "revalidated"
        assert event.progress == 100
        assert event.detail["total_results"] == 42
        assert event.detail["fetched_at"] == "2026-02-19T12:00:00Z"
        assert "Dados atualizados" in event.message
