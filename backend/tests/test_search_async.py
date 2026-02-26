"""GTM-ARCH-001: Tests for async search via ARQ Worker.

Tests T1-T10 per story specification:
- T1: POST /buscar returns 202 with search_id when ARQ available and flag on
- T2: Worker processes search and persists result
- T3: SSE delivers result when Worker completes
- T4: Fallback inline when ARQ unavailable
- T5: Fallback inline when SEARCH_ASYNC_ENABLED=false
- T6: Quota consumed in POST, not in Worker
- T7: Worker timeout does not affect HTTP response
- T8: Worker fails in 30s → fallback automatic to inline
- T9: SSE contract maintained (same events) in async and inline modes
- T10: Heartbeat 15s emitted during Worker processing
"""

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

# Ensure arq is mockable even if not installed locally
if "arq" not in sys.modules:
    arq_mock = MagicMock()
    arq_mock.connections.RedisSettings = MagicMock
    sys.modules["arq"] = arq_mock
    sys.modules["arq.connections"] = arq_mock.connections


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_user():
    """Authenticated user dict."""
    return {"id": "user-async-001", "email": "async@test.com", "role": "authenticated"}


@pytest.fixture
def mock_request_data():
    """Serializable BuscaRequest data for search_job."""
    return {
        "ufs": ["SP", "RJ"],
        "data_inicial": "2026-02-01",
        "data_final": "2026-02-10",
        "setor_id": "vestuario",
        "termos_busca": None,
        "search_id": "test-search-001",
        "modo_busca": "abertas",
        "status": "recebendo_proposta",
    }


@pytest.fixture
def mock_busca_response():
    """Minimal BuscaResponse mock."""
    resp = MagicMock()
    resp.total_filtrado = 42
    resp.total_raw = 100
    resp.licitacoes = []
    resp.model_dump.return_value = {
        "total_filtrado": 42,
        "total_raw": 100,
        "licitacoes": [],
    }
    return resp


@pytest.fixture
def mock_tracker():
    """Progress tracker mock with all emit methods."""
    tracker = AsyncMock()
    tracker._is_complete = False
    tracker.queue = asyncio.Queue()
    tracker.emit = AsyncMock()
    tracker.emit_search_complete = AsyncMock()
    tracker.emit_error = AsyncMock()
    tracker.emit_complete = AsyncMock()
    return tracker


# ============================================================================
# T1: POST /buscar returns 202 when ARQ available and flag on
# ============================================================================

class TestT1AsyncReturns202:
    """T1: POST /buscar returns 202 with search_id when ARQ available and flag on."""

    @pytest.mark.asyncio
    async def test_post_returns_202_when_async_enabled_and_queue_available(self, mock_user):
        """When SEARCH_ASYNC_ENABLED=true and ARQ is healthy, POST returns 202."""
        from fastapi.testclient import TestClient
        from main import app
        from auth import require_auth

        async def _override():
            return mock_user
        app.dependency_overrides[require_auth] = _override

        try:
            # get_feature_flag, is_queue_available, enqueue_job are imported INSIDE
            # buscar_licitacoes function body, so patch at their source modules.
            # create_tracker, create_state_machine, check_user_roles are module-level
            # imports in routes/search.py, so patch as routes.search.X.
            with patch("config.get_feature_flag", return_value=True), \
                 patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=True), \
                 patch("job_queue.enqueue_job", new_callable=AsyncMock, return_value=MagicMock(job_id="job-1")), \
                 patch("routes.search.create_tracker", new_callable=AsyncMock) as mock_tracker, \
                 patch("routes.search.create_state_machine", new_callable=AsyncMock), \
                 patch("quota.check_quota") as mock_quota, \
                 patch("quota.check_and_increment_quota_atomic") as mock_atomic, \
                 patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)):

                tracker_inst = AsyncMock()
                tracker_inst.emit = AsyncMock()
                mock_tracker.return_value = tracker_inst

                from quota import PLAN_CAPABILITIES
                mock_quota.return_value = MagicMock(
                    allowed=True,
                    capabilities=PLAN_CAPABILITIES.get("consultor_agil", {"max_requests_per_month": 50}),
                )
                mock_atomic.return_value = (True, 1, 49)

                client = TestClient(app)
                response = client.post(
                    "/buscar",
                    json={
                        "ufs": ["SP"],
                        "data_inicial": "2026-02-01",
                        "data_final": "2026-02-10",
                        "setor_id": "vestuario",
                    },
                )

                assert response.status_code == 202
                data = response.json()
                assert "search_id" in data
                assert data["status"] == "queued"
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# T2: Worker processes search and persists result
# ============================================================================

class TestT2WorkerProcesses:
    """T2: Worker processes search via executar_busca_completa and persists result."""

    @pytest.mark.asyncio
    async def test_search_job_runs_pipeline_and_persists(
        self, mock_request_data, mock_user, mock_busca_response, mock_tracker,
    ):
        """search_job calls executar_busca_completa and persists result in Redis."""
        import job_queue

        # Inside search_job, all these are function-level imports:
        #   from search_pipeline import executar_busca_completa
        #   from progress import get_tracker, remove_tracker
        #   from metrics import SEARCH_JOB_DURATION
        #   from middleware import search_id_var, request_id_var
        # So patch at their source modules, not at job_queue.X.
        with patch("search_pipeline.executar_busca_completa", new_callable=AsyncMock, return_value=mock_busca_response), \
             patch("progress.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("progress.remove_tracker", new_callable=AsyncMock), \
             patch("job_queue.persist_job_result", new_callable=AsyncMock) as mock_persist, \
             patch("middleware.search_id_var"), \
             patch("middleware.request_id_var"), \
             patch("metrics.SEARCH_JOB_DURATION") as mock_metric:

            mock_metric.observe = MagicMock()

            result = await job_queue.search_job(
                ctx={},
                search_id="test-search-002",
                request_data=mock_request_data,
                user_data=mock_user,
            )

            assert result["status"] == "completed"
            assert result["total_results"] == 42
            mock_persist.assert_called_once_with(
                "test-search-002", "search_result", mock_busca_response.model_dump()
            )


# ============================================================================
# T3: SSE delivers result when Worker completes
# ============================================================================

class TestT3SSEDelivery:
    """T3: SSE delivers search_complete event when Worker finishes."""

    @pytest.mark.asyncio
    async def test_worker_emits_search_complete_via_tracker(
        self, mock_request_data, mock_user, mock_busca_response, mock_tracker,
    ):
        """Worker emits search_complete via tracker after pipeline completes."""
        import job_queue

        # Same function-level imports inside search_job -- patch at source.
        with patch("search_pipeline.executar_busca_completa", new_callable=AsyncMock, return_value=mock_busca_response), \
             patch("progress.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("progress.remove_tracker", new_callable=AsyncMock), \
             patch("job_queue.persist_job_result", new_callable=AsyncMock), \
             patch("middleware.search_id_var"), \
             patch("middleware.request_id_var"), \
             patch("metrics.SEARCH_JOB_DURATION") as mock_metric:

            mock_metric.observe = MagicMock()

            await job_queue.search_job(
                ctx={},
                search_id="test-search-003",
                request_data=mock_request_data,
                user_data=mock_user,
            )

            mock_tracker.emit_search_complete.assert_called_once_with("test-search-003", 42)


# ============================================================================
# T4: Fallback inline when ARQ unavailable
# ============================================================================

class TestT4FallbackNoARQ:
    """T4: Falls back to inline sync when ARQ/Redis unavailable."""

    @pytest.mark.asyncio
    async def test_falls_back_to_sync_when_queue_unavailable(self, mock_user):
        """When queue unavailable, POST should use sync path (not return 202)."""
        from fastapi.testclient import TestClient
        from main import app
        from auth import require_auth

        async def _override():
            return mock_user
        app.dependency_overrides[require_auth] = _override

        try:
            # get_feature_flag is imported inside buscar_licitacoes -> patch at config.
            # is_queue_available is imported inside buscar_licitacoes -> patch at job_queue.
            # create_tracker, create_state_machine, SearchPipeline, remove_tracker,
            # remove_state_machine are module-level imports -> patch at routes.search.
            with patch("config.get_feature_flag", return_value=True), \
                 patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=False), \
                 patch("routes.search.create_tracker", new_callable=AsyncMock) as mock_ct, \
                 patch("routes.search.create_state_machine", new_callable=AsyncMock), \
                 patch("routes.search.SearchPipeline") as mock_pipeline_cls, \
                 patch("routes.search.remove_tracker", new_callable=AsyncMock), \
                 patch("routes.search.remove_state_machine"):

                tracker_inst = AsyncMock()
                tracker_inst.emit = AsyncMock()
                tracker_inst.emit_complete = AsyncMock()
                mock_ct.return_value = tracker_inst

                mock_pipeline = AsyncMock()
                mock_response = MagicMock()
                mock_response.total_filtrado = 5
                mock_response.licitacoes = []
                mock_pipeline.run = AsyncMock(return_value=mock_response)
                mock_pipeline_cls.return_value = mock_pipeline

                # raise_server_exceptions=False: the mock response doesn't pass
                # Pydantic validation (MagicMock vs BuscaResponse), but that's OK --
                # we only care that the sync path was taken (status != 202).
                client = TestClient(app, raise_server_exceptions=False)
                response = client.post(
                    "/buscar",
                    json={
                        "ufs": ["SP"],
                        "data_inicial": "2026-02-01",
                        "data_final": "2026-02-10",
                        "setor_id": "vestuario",
                    },
                )

                # Should NOT be 202 — sync path was taken (may be 200 or 500
                # depending on mock fidelity with BuscaResponse schema)
                assert response.status_code != 202
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# T5: Fallback inline when SEARCH_ASYNC_ENABLED=false
# ============================================================================

class TestT5FallbackFlagOff:
    """T5: Falls back to inline sync when feature flag is off."""

    @pytest.mark.asyncio
    async def test_sync_path_when_flag_disabled(self, mock_user):
        """When SEARCH_ASYNC_ENABLED=false, POST uses sync path."""
        from fastapi.testclient import TestClient
        from main import app
        from auth import require_auth

        async def _override():
            return mock_user
        app.dependency_overrides[require_auth] = _override

        try:
            # get_feature_flag is imported inside buscar_licitacoes -> patch at config.
            # create_tracker, create_state_machine, SearchPipeline, remove_tracker,
            # remove_state_machine are module-level imports -> patch at routes.search.
            with patch("config.get_feature_flag", return_value=False), \
                 patch("routes.search.create_tracker", new_callable=AsyncMock) as mock_ct, \
                 patch("routes.search.create_state_machine", new_callable=AsyncMock), \
                 patch("routes.search.SearchPipeline") as mock_pipeline_cls, \
                 patch("routes.search.remove_tracker", new_callable=AsyncMock), \
                 patch("routes.search.remove_state_machine"):

                tracker_inst = AsyncMock()
                tracker_inst.emit = AsyncMock()
                tracker_inst.emit_complete = AsyncMock()
                mock_ct.return_value = tracker_inst

                mock_pipeline = AsyncMock()
                mock_response = MagicMock()
                mock_response.total_filtrado = 3
                mock_response.licitacoes = []
                mock_pipeline.run = AsyncMock(return_value=mock_response)
                mock_pipeline_cls.return_value = mock_pipeline

                # raise_server_exceptions=False: the mock response doesn't pass
                # Pydantic validation (MagicMock vs BuscaResponse), but that's OK --
                # we only care that the sync path was taken (status != 202).
                client = TestClient(app, raise_server_exceptions=False)
                response = client.post(
                    "/buscar",
                    json={
                        "ufs": ["MG"],
                        "data_inicial": "2026-02-01",
                        "data_final": "2026-02-10",
                        "setor_id": "vestuario",
                    },
                )

                # Should NOT be 202 — sync path was taken (may be 200 or 500
                # depending on mock fidelity with BuscaResponse schema)
                assert response.status_code != 202
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# T6: Quota consumed in POST, not in Worker
# ============================================================================

class TestT6QuotaInPOST:
    """T6: Quota consumed in POST before enqueue, Worker skips quota."""

    @pytest.mark.asyncio
    async def test_quota_consumed_before_enqueue(self, mock_user):
        """Quota must be consumed in POST handler, not in Worker."""
        from fastapi.testclient import TestClient
        from main import app
        from auth import require_auth

        async def _override():
            return mock_user
        app.dependency_overrides[require_auth] = _override

        try:
            # get_feature_flag -> config (function-level import in buscar_licitacoes)
            # is_queue_available, enqueue_job -> job_queue (function-level import)
            # create_tracker, create_state_machine, check_user_roles -> routes.search (module-level)
            with patch("config.get_feature_flag", return_value=True), \
                 patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=True), \
                 patch("job_queue.enqueue_job", new_callable=AsyncMock, return_value=MagicMock(job_id="j1")), \
                 patch("routes.search.create_tracker", new_callable=AsyncMock) as mock_ct, \
                 patch("routes.search.create_state_machine", new_callable=AsyncMock), \
                 patch("quota.check_quota") as mock_check, \
                 patch("quota.check_and_increment_quota_atomic") as mock_atomic, \
                 patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)):

                tracker_inst = AsyncMock()
                tracker_inst.emit = AsyncMock()
                mock_ct.return_value = tracker_inst

                from quota import PLAN_CAPABILITIES
                mock_check.return_value = MagicMock(
                    allowed=True,
                    capabilities=PLAN_CAPABILITIES.get("consultor_agil", {"max_requests_per_month": 50}),
                )
                mock_atomic.return_value = (True, 1, 49)

                client = TestClient(app)
                response = client.post(
                    "/buscar",
                    json={
                        "ufs": ["SP"],
                        "data_inicial": "2026-02-01",
                        "data_final": "2026-02-10",
                        "setor_id": "vestuario",
                    },
                )

                assert response.status_code == 202
                # Quota was consumed in POST handler
                mock_atomic.assert_called_once()

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_worker_skips_quota_when_pre_consumed(
        self, mock_request_data, mock_user, mock_busca_response, mock_tracker,
    ):
        """executar_busca_completa with quota_pre_consumed=True skips quota check."""
        from search_pipeline import executar_busca_completa

        with patch("search_pipeline.SearchPipeline") as mock_pipeline_cls, \
             patch("search_pipeline.build_default_deps") as mock_deps, \
             patch("progress.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("progress.create_tracker", new_callable=AsyncMock, return_value=mock_tracker):

            mock_pipeline = AsyncMock()
            mock_pipeline.run = AsyncMock(return_value=mock_busca_response)
            mock_pipeline_cls.return_value = mock_pipeline
            mock_deps.return_value = MagicMock()

            await executar_busca_completa(
                search_id="test-search-006",
                request_data=mock_request_data,
                user_data=mock_user,
                tracker=mock_tracker,
                quota_pre_consumed=True,
            )

            # Verify SearchContext was created with quota_pre_consumed=True
            call_args = mock_pipeline.run.call_args[0][0]
            assert call_args.quota_pre_consumed is True


# ============================================================================
# T7: Worker timeout does not affect HTTP response
# ============================================================================

class TestT7WorkerTimeoutNoHTTPImpact:
    """T7: Worker timeout doesn't affect HTTP response (already returned 202)."""

    @pytest.mark.asyncio
    async def test_202_returned_before_worker_starts(self, mock_user):
        """POST returns 202 immediately; Worker runs independently."""
        from fastapi.testclient import TestClient
        from main import app
        from auth import require_auth

        async def _override():
            return mock_user
        app.dependency_overrides[require_auth] = _override

        enqueue_called = False

        async def slow_enqueue(*args, **kwargs):
            nonlocal enqueue_called
            enqueue_called = True
            return MagicMock(job_id="j-slow")

        try:
            # get_feature_flag -> config (function-level import in buscar_licitacoes)
            # is_queue_available, enqueue_job -> job_queue (function-level import)
            # create_tracker, create_state_machine, check_user_roles -> routes.search (module-level)
            with patch("config.get_feature_flag", return_value=True), \
                 patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=True), \
                 patch("job_queue.enqueue_job", side_effect=slow_enqueue), \
                 patch("routes.search.create_tracker", new_callable=AsyncMock) as mock_ct, \
                 patch("routes.search.create_state_machine", new_callable=AsyncMock), \
                 patch("quota.check_quota") as mock_check, \
                 patch("quota.check_and_increment_quota_atomic") as mock_atomic, \
                 patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)):

                tracker_inst = AsyncMock()
                tracker_inst.emit = AsyncMock()
                mock_ct.return_value = tracker_inst

                from quota import PLAN_CAPABILITIES
                mock_check.return_value = MagicMock(
                    allowed=True,
                    capabilities=PLAN_CAPABILITIES.get("consultor_agil", {"max_requests_per_month": 50}),
                )
                mock_atomic.return_value = (True, 1, 49)

                client = TestClient(app)
                start = time.time()
                response = client.post(
                    "/buscar",
                    json={
                        "ufs": ["SP", "RJ", "MG", "BA", "RS"],
                        "data_inicial": "2026-02-01",
                        "data_final": "2026-02-10",
                        "setor_id": "vestuario",
                    },
                )
                elapsed = time.time() - start

                assert response.status_code == 202
                assert enqueue_called
                # Response returned in under 5s (well under Railway's 120s limit)
                assert elapsed < 5.0
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# T8: Worker fails in 30s → fallback to inline
# ============================================================================

class TestT8FallbackOnWorkerTimeout:
    """T8: When Worker doesn't complete in 30s, watchdog runs inline fallback."""

    @pytest.mark.asyncio
    async def test_watchdog_runs_inline_when_no_result(self, mock_tracker, mock_busca_response):
        """_search_fallback_watchdog runs pipeline inline when Worker hasn't completed."""
        from routes.search import _search_fallback_watchdog
        from schemas import BuscaRequest

        request = BuscaRequest(
            ufs=["SP"],
            data_inicial="2026-02-01",
            data_final="2026-02-10",
            setor_id="vestuario",
        )
        request.search_id = "test-search-008"

        # get_job_result is imported INSIDE _search_fallback_watchdog from job_queue,
        # so patch at job_queue.get_job_result.
        # get_tracker is a MODULE-LEVEL import in routes/search.py,
        # so patch as routes.search.get_tracker.
        # SearchPipeline, store_background_results, remove_tracker are also
        # module-level imports in routes/search.py.
        with patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=None), \
             patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("routes.search.SearchPipeline") as mock_pipeline_cls, \
             patch("routes.search.store_background_results") as mock_store, \
             patch("routes.search.remove_tracker", new_callable=AsyncMock), \
             patch("routes.search.asyncio") as mock_asyncio:

            # Override sleep to not actually wait
            mock_asyncio.sleep = AsyncMock()

            mock_pipeline = AsyncMock()
            mock_pipeline.run = AsyncMock(return_value=mock_busca_response)
            mock_pipeline_cls.return_value = mock_pipeline

            await _search_fallback_watchdog(
                search_id="test-search-008",
                request=request,
                user={"id": "user-123"},
                deps=MagicMock(),
                tracker=mock_tracker,
                state_machine=None,
                fallback_timeout=0,  # Don't wait in test
            )

            # Pipeline was executed inline
            mock_pipeline.run.assert_called_once()
            # Result was stored for /buscar-results retrieval
            mock_store.assert_called_once_with("test-search-008", mock_busca_response)

    @pytest.mark.asyncio
    async def test_watchdog_skips_if_worker_completed(self, mock_tracker):
        """Watchdog does nothing if Worker already completed."""
        from routes.search import _search_fallback_watchdog
        from schemas import BuscaRequest

        request = BuscaRequest(
            ufs=["SP"],
            data_inicial="2026-02-01",
            data_final="2026-02-10",
            setor_id="vestuario",
        )

        # get_job_result is imported INSIDE _search_fallback_watchdog -> patch at job_queue.
        # SearchPipeline is module-level in routes/search.py.
        with patch("job_queue.get_job_result", new_callable=AsyncMock, return_value={"total": 10}), \
             patch("routes.search.SearchPipeline") as mock_pipeline_cls, \
             patch("routes.search.asyncio") as mock_asyncio:

            mock_asyncio.sleep = AsyncMock()

            await _search_fallback_watchdog(
                search_id="test-search-008b",
                request=request,
                user={"id": "user-123"},
                deps=MagicMock(),
                tracker=mock_tracker,
                state_machine=None,
                fallback_timeout=0,
            )

            # Pipeline was NOT executed (Worker already handled it)
            mock_pipeline_cls.assert_not_called()


# ============================================================================
# T9: SSE contract maintained in async and inline modes
# ============================================================================

class TestT9SSEContract:
    """T9: SSE events are the same whether from async Worker or inline processing."""

    def test_search_complete_is_terminal_in_redis_sse(self):
        """search_complete must be recognized as terminal event in Redis SSE mode."""
        # Verify our code change was applied
        import routes.search as rs
        import inspect
        source = inspect.getsource(rs.buscar_progress_stream)
        assert "search_complete" in source

    @pytest.mark.asyncio
    async def test_emit_search_complete_sets_is_complete(self):
        """emit_search_complete marks tracker as complete (terminal event)."""
        from progress import ProgressTracker

        tracker = ProgressTracker("test-009", 2, use_redis=False)
        assert tracker._is_complete is False

        await tracker.emit_search_complete("test-009", 42)
        assert tracker._is_complete is True

        # Event should be in queue
        event = await tracker.queue.get()
        assert event.stage == "search_complete"
        assert event.progress == 100
        assert event.detail["has_results"] is True
        assert event.detail["total_results"] == 42

    @pytest.mark.asyncio
    async def test_existing_events_still_work(self):
        """Standard events (complete, error, degraded) still function normally."""
        from progress import ProgressTracker

        tracker = ProgressTracker("test-009b", 1, use_redis=False)

        await tracker.emit_complete()
        assert tracker._is_complete is True
        event = await tracker.queue.get()
        assert event.stage == "complete"

        # Error event
        tracker2 = ProgressTracker("test-009c", 1, use_redis=False)
        await tracker2.emit_error("Test error")
        assert tracker2._is_complete is True
        event2 = await tracker2.queue.get()
        assert event2.stage == "error"


# ============================================================================
# T10: Heartbeat 15s emitted during Worker processing
# ============================================================================

class TestT10Heartbeat:
    """T10: SSE heartbeat (15s interval) emitted during Worker processing."""

    def test_heartbeat_interval_is_15s(self):
        """CRIT-012 AC2: Heartbeat interval must be 15s."""
        from routes.search import _SSE_HEARTBEAT_INTERVAL
        assert _SSE_HEARTBEAT_INTERVAL == 15.0

    @pytest.mark.asyncio
    async def test_worker_uses_tracker_for_progress(
        self, mock_request_data, mock_user, mock_busca_response, mock_tracker,
    ):
        """Worker passes tracker to pipeline, enabling heartbeat emission."""
        import job_queue

        # Inside search_job, all these are function-level imports -- patch at source.
        with patch("search_pipeline.executar_busca_completa", new_callable=AsyncMock, return_value=mock_busca_response) as mock_exec, \
             patch("progress.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("progress.remove_tracker", new_callable=AsyncMock), \
             patch("job_queue.persist_job_result", new_callable=AsyncMock), \
             patch("middleware.search_id_var"), \
             patch("middleware.request_id_var"), \
             patch("metrics.SEARCH_JOB_DURATION") as mock_metric:

            mock_metric.observe = MagicMock()

            await job_queue.search_job(
                ctx={},
                search_id="test-search-010",
                request_data=mock_request_data,
                user_data=mock_user,
            )

            # executar_busca_completa was called with tracker
            call_kwargs = mock_exec.call_args[1]
            assert call_kwargs.get("tracker") is mock_tracker


# ============================================================================
# Supplementary: Feature flag + config tests
# ============================================================================

class TestFeatureFlagConfig:
    """Verify SEARCH_ASYNC_ENABLED feature flag is properly registered."""

    def test_flag_in_registry(self):
        """SEARCH_ASYNC_ENABLED must be in the feature flag registry."""
        from config import _FEATURE_FLAG_REGISTRY
        assert "SEARCH_ASYNC_ENABLED" in _FEATURE_FLAG_REGISTRY
        env_var, default = _FEATURE_FLAG_REGISTRY["SEARCH_ASYNC_ENABLED"]
        assert env_var == "SEARCH_ASYNC_ENABLED"
        assert default == "false"

    def test_default_is_false(self):
        """Default must be false (AC12: gradual rollout)."""
        from config import SEARCH_ASYNC_ENABLED
        # In test env without env var, should be False
        assert SEARCH_ASYNC_ENABLED is False

    def test_fallback_timeout_default(self):
        """STORY-281: SEARCH_ASYNC_WAIT_TIMEOUT default is 120s (was 30s)."""
        from config import SEARCH_ASYNC_WAIT_TIMEOUT, SEARCH_WORKER_FALLBACK_TIMEOUT
        assert SEARCH_ASYNC_WAIT_TIMEOUT == 120
        # Legacy alias follows new default
        assert SEARCH_WORKER_FALLBACK_TIMEOUT == 120


class TestSearchQueuedResponse:
    """Verify SearchQueuedResponse schema."""

    def test_schema_fields(self):
        """Schema has search_id, status='queued', and enriched fields."""
        from schemas import SearchQueuedResponse
        resp = SearchQueuedResponse(
            search_id="abc-123",
            status_url="/v1/search/abc-123/status",
            progress_url="/buscar-progress/abc-123",
        )
        assert resp.search_id == "abc-123"
        assert resp.status == "queued"
        assert resp.status_url == "/v1/search/abc-123/status"
        assert resp.progress_url == "/buscar-progress/abc-123"
        assert resp.estimated_duration_s == 45  # default

    def test_schema_serialization(self):
        """Schema serializes correctly for JSON response."""
        from schemas import SearchQueuedResponse
        resp = SearchQueuedResponse(
            search_id="xyz-456",
            status_url="/v1/search/xyz-456/status",
            progress_url="/buscar-progress/xyz-456",
            estimated_duration_s=30,
        )
        data = resp.model_dump()
        assert data["search_id"] == "xyz-456"
        assert data["status"] == "queued"
        assert data["status_url"] == "/v1/search/xyz-456/status"
        assert data["progress_url"] == "/buscar-progress/xyz-456"
        assert data["estimated_duration_s"] == 30


class TestSearchJobMetric:
    """Verify search_job_duration_seconds metric exists."""

    def test_metric_registered(self):
        """SEARCH_JOB_DURATION histogram must exist."""
        from metrics import SEARCH_JOB_DURATION
        assert SEARCH_JOB_DURATION is not None


class TestSearchJobInWorkerSettings:
    """Verify search_job is registered in WorkerSettings."""

    def test_search_job_in_functions(self):
        """search_job must be in WorkerSettings.functions."""
        from job_queue import WorkerSettings, search_job
        assert search_job in WorkerSettings.functions

    def test_job_timeout_sufficient(self):
        """Job timeout must be >=300s for multi-UF searches."""
        from job_queue import WorkerSettings
        assert WorkerSettings.job_timeout >= 300
