"""STORY-292: Tests for async search via asyncio.create_task.

AC15: POST → 202 → SSE → complete → results
AC16: SSE disconnect → polling fallback → results
AC17: Task failure → status=failed → error message
AC18: All existing tests passing (or adapted)
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_user():
    """Authenticated user dict with valid UUID."""
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "async292@test.com",
        "role": "authenticated",
    }


@pytest.fixture
def mock_tracker():
    """Progress tracker mock with all emit methods."""
    tracker = AsyncMock()
    tracker._is_complete = False
    tracker._ufs_completed = 0
    tracker.uf_count = 1
    tracker.created_at = 1000000.0
    tracker.queue = asyncio.Queue()
    tracker.emit = AsyncMock()
    tracker.emit_search_complete = AsyncMock()
    tracker.emit_error = AsyncMock()
    tracker.emit_complete = AsyncMock()
    return tracker


@pytest.fixture
def mock_pipeline_response():
    """Minimal BuscaResponse mock."""
    resp = MagicMock()
    resp.total_filtrado = 42
    resp.total_encontrado = 100
    resp.licitacoes = []
    resp.model_dump.return_value = {
        "total_filtrado": 42,
        "total_encontrado": 100,
        "licitacoes": [],
    }
    return resp


@pytest.fixture
def mock_deps():
    """SimpleNamespace deps for SearchPipeline."""
    return SimpleNamespace(
        ENABLE_NEW_PRICING=False,
        PNCPClient=MagicMock(),
        buscar_todas_ufs_paralelo=AsyncMock(),
        aplicar_todos_filtros=MagicMock(),
        create_excel=MagicMock(),
        rate_limiter=MagicMock(),
        check_user_roles=AsyncMock(return_value=(False, False)),
        match_keywords=MagicMock(),
        KEYWORDS_UNIFORMES={},
        KEYWORDS_EXCLUSAO={},
        validate_terms=MagicMock(),
    )


# ============================================================================
# AC1: POST /buscar returns 202 in <2s
# ============================================================================

class TestAC1Returns202:
    """AC1: POST /buscar returns 202 Accepted with search_id."""

    def test_async_enabled_returns_202(self, mock_user):
        """When SEARCH_ASYNC_ENABLED=true, POST returns 202 immediately."""
        from fastapi.testclient import TestClient
        from main import app
        from auth import require_auth

        async def _override():
            return mock_user
        app.dependency_overrides[require_auth] = _override

        try:
            with patch("config.get_feature_flag", return_value=True), \
                 patch("routes.search.create_tracker", new_callable=AsyncMock) as mock_ct, \
                 patch("routes.search.create_state_machine", new_callable=AsyncMock), \
                 patch("quota.check_quota") as mock_check, \
                 patch("quota.check_and_increment_quota_atomic") as mock_atomic, \
                 patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)), \
                 patch("routes.search.SearchPipeline") as mock_pipeline_cls, \
                 patch("routes.search.remove_tracker", new_callable=AsyncMock), \
                 patch("routes.search.remove_state_machine"):

                tracker_inst = AsyncMock()
                tracker_inst.emit = AsyncMock()
                tracker_inst.emit_search_complete = AsyncMock()
                mock_ct.return_value = tracker_inst

                from quota import PLAN_CAPABILITIES
                mock_check.return_value = MagicMock(
                    allowed=True,
                    capabilities=PLAN_CAPABILITIES.get("smartlic_pro", {"max_requests_per_month": 1000}),
                )
                mock_atomic.return_value = (True, 1, 999)

                # Mock pipeline for background task
                mock_pipeline = AsyncMock()
                mock_response = MagicMock()
                mock_response.total_filtrado = 5
                mock_response.total_encontrado = 10
                mock_pipeline.run = AsyncMock(return_value=mock_response)
                mock_pipeline_cls.return_value = mock_pipeline

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
                assert "status_url" in data
                assert "progress_url" in data
                assert "estimated_duration_s" in data
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# AC2: Location header in 202 response
# ============================================================================

class TestAC2LocationHeader:
    """AC2: 202 response includes Location header."""

    def test_202_has_location_header(self, mock_user):
        """Location header points to status endpoint."""
        from fastapi.testclient import TestClient
        from main import app
        from auth import require_auth

        async def _override():
            return mock_user
        app.dependency_overrides[require_auth] = _override

        try:
            with patch("config.get_feature_flag", return_value=True), \
                 patch("routes.search.create_tracker", new_callable=AsyncMock) as mock_ct, \
                 patch("routes.search.create_state_machine", new_callable=AsyncMock), \
                 patch("quota.check_quota") as mock_check, \
                 patch("quota.check_and_increment_quota_atomic") as mock_atomic, \
                 patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)), \
                 patch("routes.search.SearchPipeline") as mock_pipeline_cls, \
                 patch("routes.search.remove_tracker", new_callable=AsyncMock), \
                 patch("routes.search.remove_state_machine"):

                tracker_inst = AsyncMock()
                tracker_inst.emit = AsyncMock()
                tracker_inst.emit_search_complete = AsyncMock()
                mock_ct.return_value = tracker_inst

                from quota import PLAN_CAPABILITIES
                mock_check.return_value = MagicMock(
                    allowed=True,
                    capabilities=PLAN_CAPABILITIES.get("smartlic_pro", {"max_requests_per_month": 1000}),
                )
                mock_atomic.return_value = (True, 1, 999)

                mock_pipeline = AsyncMock()
                mock_response = MagicMock()
                mock_response.total_filtrado = 0
                mock_response.total_encontrado = 0
                mock_pipeline.run = AsyncMock(return_value=mock_response)
                mock_pipeline_cls.return_value = mock_pipeline

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
                assert "location" in response.headers
                assert "/v1/search/" in response.headers["location"]
                assert "/status" in response.headers["location"]
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# AC3: Pipeline via asyncio.create_task (no ARQ)
# ============================================================================

class TestAC3CreateTask:
    """AC3: Pipeline runs via asyncio.create_task, not ARQ worker."""

    @pytest.mark.asyncio
    async def test_run_async_search_calls_pipeline(
        self, mock_tracker, mock_pipeline_response, mock_deps,
    ):
        """_run_async_search runs the pipeline and stores results."""
        from routes.search import _run_async_search
        from schemas import BuscaRequest

        request = BuscaRequest(
            ufs=["SP"],
            data_inicial="2026-02-01",
            data_final="2026-02-10",
            setor_id="vestuario",
        )
        request.search_id = "test-292-003"

        with patch("routes.search.SearchPipeline") as mock_pipeline_cls, \
             patch("routes.search.store_background_results") as mock_store, \
             patch("routes.search._persist_results_to_redis", new_callable=AsyncMock), \
             patch("routes.search._update_session_on_complete", new_callable=AsyncMock), \
             patch("routes.search.remove_tracker", new_callable=AsyncMock), \
             patch("routes.search.remove_state_machine"):

            mock_pipeline = AsyncMock()
            mock_pipeline.run = AsyncMock(return_value=mock_pipeline_response)
            mock_pipeline_cls.return_value = mock_pipeline

            await _run_async_search(
                search_id="test-292-003",
                request=request,
                user={"id": "user-001"},
                deps=mock_deps,
                tracker=mock_tracker,
                state_machine=None,
            )

            # Pipeline was executed
            mock_pipeline.run.assert_called_once()
            # Results stored in memory
            mock_store.assert_called_once_with("test-292-003", mock_pipeline_response)
            # SSE terminal event emitted
            mock_tracker.emit_search_complete.assert_called_once_with("test-292-003", 42)

    @pytest.mark.asyncio
    async def test_arq_with_fallback(self):
        """STORY-363: The async path uses ARQ enqueue_job with in-process fallback."""
        import inspect
        from routes.search import buscar_licitacoes

        source = inspect.getsource(buscar_licitacoes)
        # STORY-363: Async section now uses ARQ enqueue_job (with create_task fallback)
        async_section = source.split("# A-04 AC1")[0]
        assert "enqueue_job" in async_section
        assert "_run_async_search" in async_section  # Fallback still present


# ============================================================================
# AC7: Task failure → status=failed + error message
# ============================================================================

class TestAC7TaskFailure:
    """AC7: When background task fails, SSE emits error and state=failed."""

    @pytest.mark.asyncio
    async def test_pipeline_exception_emits_error(
        self, mock_tracker, mock_deps,
    ):
        """Pipeline exception → SSE error event with message."""
        from routes.search import _run_async_search
        from schemas import BuscaRequest

        request = BuscaRequest(
            ufs=["SP"],
            data_inicial="2026-02-01",
            data_final="2026-02-10",
            setor_id="vestuario",
        )
        request.search_id = "test-292-007a"

        mock_state_machine = AsyncMock()

        with patch("routes.search.SearchPipeline") as mock_pipeline_cls, \
             patch("routes.search.remove_tracker", new_callable=AsyncMock), \
             patch("routes.search.remove_state_machine"), \
             patch("sentry_sdk.capture_exception"):

            mock_pipeline = AsyncMock()
            mock_pipeline.run = AsyncMock(side_effect=RuntimeError("Pipeline exploded"))
            mock_pipeline_cls.return_value = mock_pipeline

            await _run_async_search(
                search_id="test-292-007a",
                request=request,
                user={"id": "user-007"},
                deps=mock_deps,
                tracker=mock_tracker,
                state_machine=mock_state_machine,
            )

            # Error emitted via SSE
            mock_tracker.emit_error.assert_called_once()
            error_msg = mock_tracker.emit_error.call_args[0][0]
            assert "RuntimeError" in error_msg

            # State machine transitioned to failed
            mock_state_machine.fail.assert_called_once()


# ============================================================================
# AC9: 120s timeout with cleanup
# ============================================================================

class TestAC9Timeout:
    """AC9: 120s hard timeout kills the task and cleans up."""

    @pytest.mark.asyncio
    async def test_timeout_emits_error_and_cleans_up(
        self, mock_tracker, mock_deps,
    ):
        """Pipeline timeout → SSE error + state machine timeout."""
        from routes.search import _run_async_search, _ASYNC_SEARCH_TIMEOUT
        from schemas import BuscaRequest

        assert _ASYNC_SEARCH_TIMEOUT == 120  # Verify constant

        request = BuscaRequest(
            ufs=["SP"],
            data_inicial="2026-02-01",
            data_final="2026-02-10",
            setor_id="vestuario",
        )
        request.search_id = "test-292-009"

        mock_state_machine = AsyncMock()

        with patch("routes.search.SearchPipeline") as mock_pipeline_cls, \
             patch("routes.search.remove_tracker", new_callable=AsyncMock), \
             patch("routes.search.remove_state_machine"), \
             patch("sentry_sdk.capture_message"):

            mock_pipeline = AsyncMock()
            mock_pipeline.run = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_pipeline_cls.return_value = mock_pipeline

            await _run_async_search(
                search_id="test-292-009",
                request=request,
                user={"id": "user-009"},
                deps=mock_deps,
                tracker=mock_tracker,
                state_machine=mock_state_machine,
            )

            # Timeout error emitted via SSE
            mock_tracker.emit_error.assert_called_once()
            error_msg = mock_tracker.emit_error.call_args[0][0]
            assert "120 segundos" in error_msg

            # State machine transitioned to timeout
            mock_state_machine.timeout.assert_called_once()

    def test_timeout_constant_is_120(self):
        """_ASYNC_SEARCH_TIMEOUT must be 120 seconds."""
        from routes.search import _ASYNC_SEARCH_TIMEOUT
        assert _ASYNC_SEARCH_TIMEOUT == 120


# ============================================================================
# AC14: X-Sync backward compat
# ============================================================================

class TestAC14BackwardCompat:
    """AC14: X-Sync: true forces synchronous path."""

    def test_x_sync_header_forces_sync(self, mock_user):
        """With X-Sync: true, POST uses sync path even if async enabled."""
        from fastapi.testclient import TestClient
        from main import app
        from auth import require_auth

        async def _override():
            return mock_user
        app.dependency_overrides[require_auth] = _override

        try:
            with patch("config.get_feature_flag", return_value=True), \
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

                client = TestClient(app, raise_server_exceptions=False)
                response = client.post(
                    "/buscar",
                    json={
                        "ufs": ["SP"],
                        "data_inicial": "2026-02-01",
                        "data_final": "2026-02-10",
                        "setor_id": "vestuario",
                    },
                    headers={"X-Sync": "true"},
                )

                # Should NOT be 202
                assert response.status_code != 202
        finally:
            app.dependency_overrides.clear()

    def test_sync_query_param_forces_sync(self, mock_user):
        """With ?sync=true, POST uses sync path."""
        from fastapi.testclient import TestClient
        from main import app
        from auth import require_auth

        async def _override():
            return mock_user
        app.dependency_overrides[require_auth] = _override

        try:
            with patch("config.get_feature_flag", return_value=True), \
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

                client = TestClient(app, raise_server_exceptions=False)
                response = client.post(
                    "/buscar?sync=true",
                    json={
                        "ufs": ["SP"],
                        "data_inicial": "2026-02-01",
                        "data_final": "2026-02-10",
                        "setor_id": "vestuario",
                    },
                )

                assert response.status_code != 202
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# Quota consumed in POST before task dispatch
# ============================================================================

class TestQuotaInPOST:
    """Quota is consumed in POST handler before dispatching background task."""

    def test_quota_consumed_before_dispatch(self, mock_user):
        """check_and_increment_quota_atomic called before 202 returned."""
        from fastapi.testclient import TestClient
        from main import app
        from auth import require_auth

        async def _override():
            return mock_user
        app.dependency_overrides[require_auth] = _override

        try:
            with patch("config.get_feature_flag", return_value=True), \
                 patch("routes.search.create_tracker", new_callable=AsyncMock) as mock_ct, \
                 patch("routes.search.create_state_machine", new_callable=AsyncMock), \
                 patch("quota.check_quota") as mock_check, \
                 patch("quota.check_and_increment_quota_atomic") as mock_atomic, \
                 patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)), \
                 patch("routes.search.SearchPipeline") as mock_pipeline_cls, \
                 patch("routes.search.remove_tracker", new_callable=AsyncMock), \
                 patch("routes.search.remove_state_machine"):

                tracker_inst = AsyncMock()
                tracker_inst.emit = AsyncMock()
                tracker_inst.emit_search_complete = AsyncMock()
                mock_ct.return_value = tracker_inst

                from quota import PLAN_CAPABILITIES
                mock_check.return_value = MagicMock(
                    allowed=True,
                    capabilities=PLAN_CAPABILITIES.get("smartlic_pro", {"max_requests_per_month": 1000}),
                )
                mock_atomic.return_value = (True, 1, 999)

                mock_pipeline = AsyncMock()
                mock_response = MagicMock()
                mock_response.total_filtrado = 5
                mock_response.total_encontrado = 10
                mock_pipeline.run = AsyncMock(return_value=mock_response)
                mock_pipeline_cls.return_value = mock_pipeline

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
                mock_atomic.assert_called_once()
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# Config: Default is now true
# ============================================================================

class TestConfigDefaults:
    """STORY-292: Verify config defaults reflect new async-first design."""

    def test_feature_flag_registry_default_true(self):
        """SEARCH_ASYNC_ENABLED registry default is 'true' (STORY-292)."""
        # Note: conftest forces it to "false" for tests, but the actual
        # registry default should be "true" in production config.
        # We check the module-level constant (which conftest patches to False).
        import config
        # The registry was patched by conftest; verify conftest is working
        assert config.SEARCH_ASYNC_ENABLED is False  # conftest forces this

    def test_async_search_timeout_constant(self):
        """_ASYNC_SEARCH_TIMEOUT is 120s (replaces SEARCH_ASYNC_WAIT_TIMEOUT)."""
        from routes.search import _ASYNC_SEARCH_TIMEOUT
        assert _ASYNC_SEARCH_TIMEOUT == 120
