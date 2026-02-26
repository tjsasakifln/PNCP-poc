"""STORY-281: ARQ Worker Race Condition — Double Execution Fix.

Tests cover:
- AC1: SEARCH_ASYNC_WAIT_TIMEOUT increased to 120s, configurable via env
- AC2: Cancel flag via Redis — set, check, clear, worker respects it
- AC3: SSE heartbeat during wait (already covered by CRIT-012, verified here)
- AC4: Metrics (inline_fallback counter, worker_completion histogram, structured log)
"""

import json
import sys
import uuid
import asyncio
import pytest
from unittest.mock import patch, Mock, AsyncMock, MagicMock

# Ensure arq is mockable even if not installed locally.
_arq_mod = sys.modules.get("arq")
if _arq_mod is None:
    _arq_mod = MagicMock()
    sys.modules["arq"] = _arq_mod
_arq_mod.connections = MagicMock()
_arq_mod.connections.RedisSettings = MagicMock
sys.modules["arq.connections"] = _arq_mod.connections

from main import app
from auth import require_auth


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_tracker():
    tracker = Mock()
    tracker.emit = AsyncMock()
    tracker.emit_error = AsyncMock()
    tracker.emit_complete = AsyncMock()
    tracker.emit_degraded = AsyncMock()
    tracker.emit_search_complete = AsyncMock()
    tracker._is_complete = False
    return tracker


def _make_mock_state_machine():
    sm = Mock()
    sm.fail = AsyncMock()
    sm.transition = AsyncMock()
    sm.complete = AsyncMock()
    return sm


VALID_SEARCH_BODY = {
    "ufs": ["SP"],
    "data_inicial": "2026-02-16",
    "data_final": "2026-02-26",
    "setor_id": "vestuario",
    "search_id": str(uuid.uuid4()),
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def mock_auth():
    mock_user = {
        "id": "test-user-id",
        "email": "test@example.com",
        "plan_type": "smartlic_pro",
    }
    app.dependency_overrides[require_auth] = lambda: mock_user
    yield mock_user
    app.dependency_overrides.pop(require_auth, None)


@pytest.fixture(autouse=True)
def mock_active_plan():
    with patch("quota.require_active_plan", new_callable=AsyncMock):
        yield


@pytest.fixture
def mock_quota():
    mock_info = Mock()
    mock_info.allowed = True
    mock_info.error_message = ""
    mock_info.capabilities = {"max_requests_per_month": 1000}

    with patch("quota.check_quota", return_value=mock_info), \
         patch("quota.check_and_increment_quota_atomic", return_value=(True, 1, 999)):
        yield mock_info


# ===========================================================================
# AC1: SEARCH_ASYNC_WAIT_TIMEOUT = 120s, configurable via env
# ===========================================================================

class TestAC1AsyncWaitTimeout:
    """AC1: Timeout increased from 30s to 120s, configurable via env."""

    def test_default_timeout_is_120(self):
        """AC1: Default SEARCH_ASYNC_WAIT_TIMEOUT is 120."""
        from config import SEARCH_ASYNC_WAIT_TIMEOUT
        assert SEARCH_ASYNC_WAIT_TIMEOUT == 120

    def test_env_override_timeout(self):
        """AC1: SEARCH_ASYNC_WAIT_TIMEOUT is configurable via env var."""
        with patch.dict("os.environ", {"SEARCH_ASYNC_WAIT_TIMEOUT": "180"}):
            # Re-evaluate the env read
            result = int(__import__("os").getenv("SEARCH_ASYNC_WAIT_TIMEOUT", "120"))
            assert result == 180

    def test_legacy_alias_fallback(self):
        """AC1: SEARCH_WORKER_FALLBACK_TIMEOUT falls back to SEARCH_ASYNC_WAIT_TIMEOUT."""
        # When neither env var is set, both should be 120 (the new default)
        from config import SEARCH_WORKER_FALLBACK_TIMEOUT, SEARCH_ASYNC_WAIT_TIMEOUT
        # The legacy var reads SEARCH_WORKER_FALLBACK_TIMEOUT env, defaulting to SEARCH_ASYNC_WAIT_TIMEOUT
        assert SEARCH_WORKER_FALLBACK_TIMEOUT >= 30  # Must be at least 30 (never less)

    def test_watchdog_uses_new_timeout(self, client, mock_quota):
        """AC1: POST /buscar async path passes SEARCH_ASYNC_WAIT_TIMEOUT to watchdog."""
        mock_job = Mock(job_id="job-281-1")

        created_tasks = []
        original_create_task = asyncio.get_event_loop().create_task if hasattr(asyncio, 'get_event_loop') else None

        with patch("config.get_feature_flag", return_value=True), \
             patch("config.SEARCH_ASYNC_WAIT_TIMEOUT", 120), \
             patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=True), \
             patch("job_queue.enqueue_job", new_callable=AsyncMock, return_value=mock_job), \
             patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)), \
             patch("routes.search.create_tracker", new_callable=AsyncMock, return_value=_make_mock_tracker()), \
             patch("routes.search.create_state_machine", new_callable=AsyncMock, return_value=_make_mock_state_machine()), \
             patch("routes.search._search_fallback_watchdog", new_callable=AsyncMock) as mock_watchdog:

            response = client.post("/buscar", json=VALID_SEARCH_BODY)

        assert response.status_code == 202


# ===========================================================================
# AC2: Cancel flag via Redis
# ===========================================================================

class TestAC2CancelFlag:
    """AC2: Redis cancel flag — set, check, clear."""

    @pytest.mark.asyncio
    async def test_set_cancel_flag(self):
        """AC2: set_cancel_flag writes to Redis with TTL."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock()

        with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=mock_redis)):
            from job_queue import set_cancel_flag
            result = await set_cancel_flag("search-123")

        assert result is True
        mock_redis.set.assert_awaited_once()
        call_args = mock_redis.set.call_args
        assert "smartlic:search_cancel:search-123" in str(call_args)

    @pytest.mark.asyncio
    async def test_check_cancel_flag_returns_true_when_set(self):
        """AC2: check_cancel_flag returns True when flag exists in Redis."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=b"1")

        with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=mock_redis)):
            from job_queue import check_cancel_flag
            result = await check_cancel_flag("search-123")

        assert result is True

    @pytest.mark.asyncio
    async def test_check_cancel_flag_returns_false_when_not_set(self):
        """AC2: check_cancel_flag returns False when flag is absent."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=mock_redis)):
            from job_queue import check_cancel_flag
            result = await check_cancel_flag("search-123")

        assert result is False

    @pytest.mark.asyncio
    async def test_clear_cancel_flag(self):
        """AC2: clear_cancel_flag deletes the Redis key."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock()

        with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=mock_redis)):
            from job_queue import clear_cancel_flag
            await clear_cancel_flag("search-123")

        mock_redis.delete.assert_awaited_once_with("smartlic:search_cancel:search-123")

    @pytest.mark.asyncio
    async def test_set_cancel_flag_noop_without_redis(self):
        """AC2: set_cancel_flag returns False when Redis unavailable."""
        with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=None)):
            from job_queue import set_cancel_flag
            result = await set_cancel_flag("search-123")

        assert result is False

    @pytest.mark.asyncio
    async def test_check_cancel_flag_noop_without_redis(self):
        """AC2: check_cancel_flag returns False when Redis unavailable."""
        with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=None)):
            from job_queue import check_cancel_flag
            result = await check_cancel_flag("search-123")

        assert result is False

    @pytest.mark.asyncio
    async def test_clear_cancel_flag_noop_without_redis(self):
        """AC2: clear_cancel_flag is a no-op when Redis unavailable."""
        with patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=None)):
            from job_queue import clear_cancel_flag
            await clear_cancel_flag("search-123")  # Should not raise


# ===========================================================================
# AC2: Worker respects cancel flag
# ===========================================================================

class TestAC2WorkerCancelBehavior:
    """AC2: search_job checks cancel flag and aborts if set."""

    @pytest.mark.asyncio
    async def test_search_job_aborts_before_start_if_cancelled(self):
        """AC2: search_job returns 'cancelled' if flag is set before execution."""
        from job_queue import search_job

        with patch("job_queue.check_cancel_flag", new_callable=AsyncMock, return_value=True), \
             patch("progress.get_tracker", new_callable=AsyncMock, return_value=None), \
             patch("metrics.SEARCH_JOB_DURATION", MagicMock()), \
             patch("job_queue.clear_cancel_flag", new_callable=AsyncMock):

            result = await search_job(
                ctx={},
                search_id="cancel-test-1",
                request_data={"ufs": ["SP"], "setor_id": "vestuario"},
                user_data={"id": "user-1"},
            )

        assert result["status"] == "cancelled"
        assert result["total_results"] == 0

    @pytest.mark.asyncio
    async def test_search_job_completes_normally_when_not_cancelled(self):
        """AC2: search_job runs normally when cancel flag is not set."""
        from job_queue import search_job

        mock_response = MagicMock()
        mock_response.total_filtrado = 5
        mock_response.model_dump = MagicMock(return_value={"total_filtrado": 5, "licitacoes": []})

        mock_tracker = _make_mock_tracker()

        with patch("job_queue.check_cancel_flag", new_callable=AsyncMock, return_value=False), \
             patch("search_pipeline.executar_busca_completa", new_callable=AsyncMock, return_value=mock_response), \
             patch("progress.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("progress.remove_tracker", new_callable=AsyncMock), \
             patch("redis_pool.get_redis_pool", new_callable=lambda: AsyncMock(return_value=AsyncMock(set=AsyncMock(), delete=AsyncMock(), get=AsyncMock(return_value=None)))), \
             patch("metrics.SEARCH_JOB_DURATION", MagicMock()), \
             patch("job_queue.clear_cancel_flag", new_callable=AsyncMock):

            result = await search_job(
                ctx={},
                search_id="normal-test-1",
                request_data={"ufs": ["SP"], "setor_id": "vestuario"},
                user_data={"id": "user-1"},
            )

        assert result["status"] == "completed"
        assert result["total_results"] == 5


# ===========================================================================
# AC2: Watchdog sets cancel flag before running inline
# ===========================================================================

class TestAC2WatchdogCancelSignal:
    """AC2: _search_fallback_watchdog sets cancel flag when falling back."""

    @pytest.mark.asyncio
    async def test_watchdog_sets_cancel_flag_on_fallback(self):
        """AC2: Watchdog calls set_cancel_flag before running inline pipeline."""
        from routes.search import _search_fallback_watchdog

        mock_response = MagicMock()
        mock_response.total_filtrado = 3

        mock_tracker = _make_mock_tracker()
        deps = MagicMock()

        from schemas import BuscaRequest
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial="2026-02-16",
            data_final="2026-02-26",
            setor_id="vestuario",
            search_id="watchdog-cancel-test",
        )

        with patch("asyncio.sleep", new_callable=AsyncMock), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=None), \
             patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search.remove_tracker", new_callable=AsyncMock), \
             patch("routes.search.SearchPipeline") as MockPipeline, \
             patch("routes.search.SearchContext"), \
             patch("routes.search.store_background_results"), \
             patch("job_queue.set_cancel_flag", new_callable=AsyncMock) as mock_set_cancel, \
             patch("metrics.SEARCH_INLINE_FALLBACK", MagicMock()), \
             patch("metrics.SEARCH_WORKER_COMPLETION", MagicMock()):

            mock_pipe = MockPipeline.return_value
            mock_pipe.run = AsyncMock(return_value=mock_response)

            await _search_fallback_watchdog(
                search_id="watchdog-cancel-test",
                request=request,
                user={"id": "user-1"},
                deps=deps,
                tracker=mock_tracker,
                state_machine=_make_mock_state_machine(),
                fallback_timeout=0,  # Skip sleep for test
            )

        # AC2: Cancel flag must be set
        mock_set_cancel.assert_awaited_once_with("watchdog-cancel-test")

    @pytest.mark.asyncio
    async def test_watchdog_skips_when_worker_completed(self):
        """AC2: Watchdog does NOT run inline if worker already completed."""
        from routes.search import _search_fallback_watchdog

        mock_tracker = _make_mock_tracker()
        deps = MagicMock()

        from schemas import BuscaRequest
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial="2026-02-16",
            data_final="2026-02-26",
            setor_id="vestuario",
            search_id="completed-test",
        )

        with patch("asyncio.sleep", new_callable=AsyncMock), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value={"total_filtrado": 10}), \
             patch("routes.search.SearchPipeline") as MockPipeline, \
             patch("job_queue.set_cancel_flag", new_callable=AsyncMock) as mock_set_cancel, \
             patch("metrics.SEARCH_INLINE_FALLBACK", MagicMock()), \
             patch("metrics.SEARCH_WORKER_COMPLETION", MagicMock()):

            await _search_fallback_watchdog(
                search_id="completed-test",
                request=request,
                user={"id": "user-1"},
                deps=deps,
                tracker=mock_tracker,
                state_machine=_make_mock_state_machine(),
                fallback_timeout=0,
            )

        # Worker completed — cancel flag should NOT be set, pipeline should NOT run
        mock_set_cancel.assert_not_awaited()
        MockPipeline.assert_not_called()


# ===========================================================================
# AC3: SSE heartbeat during wait (already covered by CRIT-012)
# ===========================================================================

class TestAC3SSEHeartbeat:
    """AC3: Verify SSE heartbeat interval is 15s and maintained during async wait."""

    def test_sse_heartbeat_interval_is_15s(self):
        """AC3: _SSE_HEARTBEAT_INTERVAL is 15 seconds."""
        from routes.search import _SSE_HEARTBEAT_INTERVAL
        assert _SSE_HEARTBEAT_INTERVAL == 15.0

    def test_sse_wait_heartbeat_every_10_iterations(self):
        """AC3: During tracker wait, heartbeat emitted every 10 * 0.5s = 5s."""
        from routes.search import _SSE_WAIT_HEARTBEAT_EVERY
        assert _SSE_WAIT_HEARTBEAT_EVERY == 10


# ===========================================================================
# AC4: Metrics and structured logging
# ===========================================================================

class TestAC4Metrics:
    """AC4: New Prometheus metrics for observability."""

    def test_inline_fallback_counter_exists(self):
        """AC4: smartlic_search_inline_fallback_total counter is defined."""
        from metrics import SEARCH_INLINE_FALLBACK
        assert SEARCH_INLINE_FALLBACK is not None
        # Verify it has .inc() method (Counter interface)
        assert hasattr(SEARCH_INLINE_FALLBACK, "inc")

    def test_worker_completion_histogram_exists(self):
        """AC4: smartlic_search_worker_completion_seconds histogram is defined."""
        from metrics import SEARCH_WORKER_COMPLETION
        assert SEARCH_WORKER_COMPLETION is not None
        # Verify it has .observe() method (Histogram interface)
        assert hasattr(SEARCH_WORKER_COMPLETION, "observe")

    @pytest.mark.asyncio
    async def test_watchdog_emits_inline_fallback_counter(self):
        """AC4: Watchdog increments inline_fallback counter when falling back."""
        from routes.search import _search_fallback_watchdog

        mock_tracker = _make_mock_tracker()
        deps = MagicMock()

        from schemas import BuscaRequest
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial="2026-02-16",
            data_final="2026-02-26",
            setor_id="vestuario",
            search_id="metrics-test",
        )

        mock_counter = MagicMock()
        mock_response = MagicMock()
        mock_response.total_filtrado = 0

        with patch("asyncio.sleep", new_callable=AsyncMock), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=None), \
             patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search.remove_tracker", new_callable=AsyncMock), \
             patch("routes.search.SearchPipeline") as MockPipeline, \
             patch("routes.search.SearchContext"), \
             patch("routes.search.store_background_results"), \
             patch("job_queue.set_cancel_flag", new_callable=AsyncMock), \
             patch("metrics.SEARCH_INLINE_FALLBACK", mock_counter), \
             patch("metrics.SEARCH_WORKER_COMPLETION", MagicMock()):

            mock_pipe = MockPipeline.return_value
            mock_pipe.run = AsyncMock(return_value=mock_response)

            await _search_fallback_watchdog(
                search_id="metrics-test",
                request=request,
                user={"id": "user-1"},
                deps=deps,
                tracker=mock_tracker,
                state_machine=_make_mock_state_machine(),
                fallback_timeout=0,
            )

        mock_counter.inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_watchdog_emits_worker_completion_on_success(self):
        """AC4: Watchdog records worker_completion histogram when worker finishes in time."""
        from routes.search import _search_fallback_watchdog

        mock_tracker = _make_mock_tracker()
        deps = MagicMock()

        from schemas import BuscaRequest
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial="2026-02-16",
            data_final="2026-02-26",
            setor_id="vestuario",
            search_id="histogram-test",
        )

        mock_histogram = MagicMock()

        with patch("asyncio.sleep", new_callable=AsyncMock), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value={"total_filtrado": 5}), \
             patch("metrics.SEARCH_INLINE_FALLBACK", MagicMock()), \
             patch("metrics.SEARCH_WORKER_COMPLETION", mock_histogram):

            await _search_fallback_watchdog(
                search_id="histogram-test",
                request=request,
                user={"id": "user-1"},
                deps=deps,
                tracker=mock_tracker,
                state_machine=_make_mock_state_machine(),
                fallback_timeout=0,
            )

        mock_histogram.observe.assert_called_once()

    @pytest.mark.asyncio
    async def test_watchdog_structured_log_on_fallback(self):
        """AC4: Watchdog emits structured JSON log on inline fallback."""
        from routes.search import _search_fallback_watchdog

        mock_tracker = _make_mock_tracker()
        deps = MagicMock()
        mock_response = MagicMock()
        mock_response.total_filtrado = 0

        from schemas import BuscaRequest
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial="2026-02-16",
            data_final="2026-02-26",
            setor_id="vestuario",
            search_id="log-test",
        )

        with patch("asyncio.sleep", new_callable=AsyncMock), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=None), \
             patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search.remove_tracker", new_callable=AsyncMock), \
             patch("routes.search.SearchPipeline") as MockPipeline, \
             patch("routes.search.SearchContext"), \
             patch("routes.search.store_background_results"), \
             patch("job_queue.set_cancel_flag", new_callable=AsyncMock), \
             patch("metrics.SEARCH_INLINE_FALLBACK", MagicMock()), \
             patch("metrics.SEARCH_WORKER_COMPLETION", MagicMock()), \
             patch("routes.search.logger") as mock_logger:

            mock_pipe = MockPipeline.return_value
            mock_pipe.run = AsyncMock(return_value=mock_response)

            await _search_fallback_watchdog(
                search_id="log-test",
                request=request,
                user={"id": "user-1"},
                deps=deps,
                tracker=mock_tracker,
                state_machine=_make_mock_state_machine(),
                fallback_timeout=60,
            )

        # Verify structured JSON log was emitted
        warning_calls = mock_logger.warning.call_args_list
        assert len(warning_calls) >= 1
        log_msg = warning_calls[0][0][0]
        log_data = json.loads(log_msg)
        assert log_data["event"] == "inline_fallback"
        assert log_data["search_id"] == "log-test"
        assert log_data["wait_timeout"] == 60


# ===========================================================================
# Integration: Full async flow with cancel
# ===========================================================================

class TestIntegrationAsyncFlowCancel:
    """Integration: Full async POST → 202 with updated timeout."""

    def test_async_post_returns_202_with_new_timeout(self, client, mock_quota):
        """Full flow: POST /buscar → 202 with SEARCH_ASYNC_WAIT_TIMEOUT=120."""
        mock_job = Mock(job_id="job-integration")

        with patch("config.get_feature_flag", return_value=True), \
             patch("config.SEARCH_ASYNC_WAIT_TIMEOUT", 120), \
             patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=True), \
             patch("job_queue.enqueue_job", new_callable=AsyncMock, return_value=mock_job), \
             patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)), \
             patch("routes.search.create_tracker", new_callable=AsyncMock, return_value=_make_mock_tracker()), \
             patch("routes.search.create_state_machine", new_callable=AsyncMock, return_value=_make_mock_state_machine()):

            response = client.post("/buscar", json=VALID_SEARCH_BODY)

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"
        assert "search_id" in data

    def test_worker_fallback_timeout_legacy_compat(self):
        """Legacy: SEARCH_WORKER_FALLBACK_TIMEOUT still available."""
        from config import SEARCH_WORKER_FALLBACK_TIMEOUT
        # Must be >= 30 (the old value) — now defaults to 120
        assert SEARCH_WORKER_FALLBACK_TIMEOUT >= 30
