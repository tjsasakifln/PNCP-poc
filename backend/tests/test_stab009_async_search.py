"""GTM-STAB-009: Async search architecture tests.

Tests the async search flow end-to-end:
- POST /buscar returns 202 when SEARCH_ASYNC_ENABLED=true (asyncio.create_task)
- POST /buscar returns 200 when flag disabled (backward compat)
- X-Sync: true header forces sync even with async enabled
- Quota failure → falls back to sync pipeline
- GET /v1/search/{id}/status → current search state
- GET /search/{id}/results → 200 with results when ready, 202 when processing

STORY-292: Migrated from ARQ enqueue_job to asyncio.create_task.
"""

import uuid
import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient

from main import app
from auth import require_auth


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_tracker():
    """Create a mock tracker with async-compatible methods."""
    tracker = Mock()
    tracker.emit = AsyncMock()
    tracker.emit_error = AsyncMock()
    tracker.emit_complete = AsyncMock()
    tracker.emit_degraded = AsyncMock()
    tracker._is_complete = False
    return tracker


def _make_mock_state_machine():
    """Create a mock state machine with async-compatible methods."""
    sm = Mock()
    sm.fail = AsyncMock()
    sm.transition = AsyncMock()
    sm.complete = AsyncMock()
    return sm


def _make_sync_response():
    """Build a minimal valid BuscaResponse for sync path tests."""
    from schemas import BuscaResponse

    return BuscaResponse(
        resumo={
            "resumo_executivo": "Teste",
            "total_oportunidades": 0,
            "valor_total": 0.0,
            "destaques": [],
        },
        licitacoes=[],
        excel_available=False,
        quota_used=1,
        quota_remaining=999,
        total_raw=0,
        total_filtrado=0,
    )


VALID_SEARCH_BODY = {
    "ufs": ["SP", "RJ"],
    "data_inicial": "2026-02-14",
    "data_final": "2026-02-24",
    "setor_id": "vestuario",
    "search_id": str(uuid.uuid4()),
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def mock_auth():
    """Override require_auth dependency for all tests in this module."""
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
    """Bypass require_active_plan to avoid trial checks."""
    with patch("quota.require_active_plan", new_callable=AsyncMock):
        yield


@pytest.fixture
def mock_quota():
    """Mock quota check to always allow (1000/month, 1 used)."""
    mock_info = Mock()
    mock_info.allowed = True
    mock_info.error_message = ""
    mock_info.capabilities = {"max_requests_per_month": 1000}

    with patch("quota.check_quota", return_value=mock_info), \
         patch("quota.check_and_increment_quota_atomic", return_value=(True, 1, 999)):
        yield mock_info


# ---------------------------------------------------------------------------
# Shared patch context for the async POST /buscar path
# ---------------------------------------------------------------------------

def _common_async_patches():
    """Return a list of context manager patches used in async POST tests.

    STORY-292: No ARQ — uses asyncio.create_task in-process.
    """
    return [
        patch("config.get_feature_flag", return_value=True),
        patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)),
        patch("routes.search.create_tracker", new_callable=AsyncMock, return_value=_make_mock_tracker()),
        patch("routes.search.create_state_machine", new_callable=AsyncMock, return_value=_make_mock_state_machine()),
        patch("routes.search._run_async_search", new_callable=AsyncMock),
    ]


# ---------------------------------------------------------------------------
# T1: POST /buscar → 202 when async enabled and queue available
# ---------------------------------------------------------------------------

class TestAsyncEnabledReturns202:
    """T1: SEARCH_ASYNC_ENABLED=true → 202 Accepted (STORY-292: asyncio.create_task)."""

    def test_async_enabled_returns_202(self, client, mock_quota):
        """AC1: POST /buscar returns 202 with full enriched async response body."""
        with patch("config.get_feature_flag", return_value=True), \
             patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)), \
             patch("routes.search.create_tracker", new_callable=AsyncMock, return_value=_make_mock_tracker()), \
             patch("routes.search.create_state_machine", new_callable=AsyncMock, return_value=_make_mock_state_machine()), \
             patch("routes.search._run_async_search", new_callable=AsyncMock):

            response = client.post("/v1/buscar", json=VALID_SEARCH_BODY)

        assert response.status_code == 202
        data = response.json()

        # AC1: Required fields in 202 response
        assert data["status"] == "queued"
        assert "search_id" in data
        assert "status_url" in data
        assert "progress_url" in data
        assert "estimated_duration_s" in data

        # AC1: URL formats
        assert data["status_url"].startswith("/v1/search/")
        assert data["status_url"].endswith("/status")
        assert data["progress_url"].startswith("/buscar-progress/")

        # AC1: estimated_duration_s is a positive integer
        assert isinstance(data["estimated_duration_s"], int)
        assert data["estimated_duration_s"] > 0

    def test_async_enabled_duration_scales_with_ufs(self, client, mock_quota):
        """AC1: estimated_duration_s scales with number of UFs requested."""
        body_few_ufs = {**VALID_SEARCH_BODY, "ufs": ["SP"]}
        body_many_ufs = {**VALID_SEARCH_BODY, "ufs": ["SP", "RJ", "MG", "RS", "PR", "BA", "SC", "GO"]}

        with patch("config.get_feature_flag", return_value=True), \
             patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)), \
             patch("routes.search.create_tracker", new_callable=AsyncMock, return_value=_make_mock_tracker()), \
             patch("routes.search.create_state_machine", new_callable=AsyncMock, return_value=_make_mock_state_machine()), \
             patch("routes.search._run_async_search", new_callable=AsyncMock):

            resp_few = client.post("/v1/buscar", json=body_few_ufs)
            resp_many = client.post("/v1/buscar", json=body_many_ufs)

        assert resp_few.status_code == 202
        assert resp_many.status_code == 202
        # More UFs should have >= estimated duration as fewer UFs
        assert resp_many.json()["estimated_duration_s"] >= resp_few.json()["estimated_duration_s"]


# ---------------------------------------------------------------------------
# T2: POST /buscar → 200 when async disabled (flag=false)
# ---------------------------------------------------------------------------

class TestAsyncDisabledReturns200:
    """T2: SEARCH_ASYNC_ENABLED=false → standard sync 200 response."""

    def test_async_disabled_returns_200(self, client, mock_quota):
        """AC6: When both flags are off, sync pipeline runs and returns 200."""
        with patch("config.get_feature_flag", return_value=False), \
             patch("config.ASYNC_SEARCH_DEFAULT", False), \
             patch("routes.search.create_tracker", new_callable=AsyncMock, return_value=_make_mock_tracker()), \
             patch("routes.search.create_state_machine", new_callable=AsyncMock, return_value=_make_mock_state_machine()), \
             patch("routes.search.remove_tracker", new_callable=AsyncMock), \
             patch("routes.search.remove_state_machine"), \
             patch("routes.search.SearchPipeline") as MockPipeline, \
             patch("search_cache.get_from_cache_cascade", new_callable=AsyncMock, return_value=None):

            mock_pipe = MockPipeline.return_value
            mock_pipe.run = AsyncMock(return_value=_make_sync_response())

            response = client.post("/v1/buscar", json=VALID_SEARCH_BODY)

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# T3: X-Sync header forces sync mode
# ---------------------------------------------------------------------------

class TestXSyncHeaderForcesSyncMode:
    """T3: X-Sync: true header bypasses async even when flag=true + queue available."""

    def test_x_sync_header_forces_sync(self, client, mock_quota):
        """AC6: X-Sync: true → sync pipeline, HTTP 200 not 202."""
        with patch("config.get_feature_flag", return_value=True), \
             patch("routes.search.create_tracker", new_callable=AsyncMock, return_value=_make_mock_tracker()), \
             patch("routes.search.create_state_machine", new_callable=AsyncMock, return_value=_make_mock_state_machine()), \
             patch("routes.search.remove_tracker", new_callable=AsyncMock), \
             patch("routes.search.remove_state_machine"), \
             patch("routes.search.SearchPipeline") as MockPipeline, \
             patch("search_cache.get_from_cache_cascade", new_callable=AsyncMock, return_value=None):

            mock_pipe = MockPipeline.return_value
            mock_pipe.run = AsyncMock(return_value=_make_sync_response())

            response = client.post(
                "/v1/buscar",
                json=VALID_SEARCH_BODY,
                headers={"X-Sync": "true"},
            )

        # Must NOT be 202 — sync path was forced
        assert response.status_code != 202
        assert response.status_code == 200

    def test_sync_query_param_forces_sync(self, client, mock_quota):
        """AC6: ?sync=true query param also bypasses async path."""
        with patch("config.get_feature_flag", return_value=True), \
             patch("routes.search.create_tracker", new_callable=AsyncMock, return_value=_make_mock_tracker()), \
             patch("routes.search.create_state_machine", new_callable=AsyncMock, return_value=_make_mock_state_machine()), \
             patch("routes.search.remove_tracker", new_callable=AsyncMock), \
             patch("routes.search.remove_state_machine"), \
             patch("routes.search.SearchPipeline") as MockPipeline, \
             patch("search_cache.get_from_cache_cascade", new_callable=AsyncMock, return_value=None):

            mock_pipe = MockPipeline.return_value
            mock_pipe.run = AsyncMock(return_value=_make_sync_response())

            response = client.post("/v1/buscar?sync=true", json=VALID_SEARCH_BODY)

        assert response.status_code == 200

    def test_x_sync_false_does_not_force_sync(self, client, mock_quota):
        """AC6: X-Sync: false does NOT prevent async — async mode still used."""
        with patch("config.get_feature_flag", return_value=True), \
             patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)), \
             patch("routes.search.create_tracker", new_callable=AsyncMock, return_value=_make_mock_tracker()), \
             patch("routes.search.create_state_machine", new_callable=AsyncMock, return_value=_make_mock_state_machine()), \
             patch("routes.search._run_async_search", new_callable=AsyncMock):

            response = client.post(
                "/v1/buscar",
                json=VALID_SEARCH_BODY,
                headers={"X-Sync": "false"},
            )

        # X-Sync: false should still allow async (202)
        assert response.status_code == 202


# ---------------------------------------------------------------------------
# T4: Quota failure → falls back to sync pipeline (STORY-292)
# ---------------------------------------------------------------------------

class TestQuotaFailureFallsBackToSync:
    """T4: STORY-292 — Quota check exception → graceful sync fallback.

    When the quota check raises an unexpected exception (e.g., Supabase down),
    the async path sets force_sync=True and falls through to the sync pipeline.
    """

    def test_quota_exception_falls_back_to_sync(self, client):
        """Quota check raises → force_sync=True → sync pipeline returns 200."""
        mock_info = Mock()
        mock_info.allowed = True
        mock_info.error_message = ""
        mock_info.capabilities = {"max_requests_per_month": 1000}

        with patch("config.get_feature_flag", return_value=True), \
             patch("routes.search.check_user_roles", new_callable=AsyncMock, side_effect=Exception("DB down")), \
             patch("routes.search.create_tracker", new_callable=AsyncMock, return_value=_make_mock_tracker()), \
             patch("routes.search.create_state_machine", new_callable=AsyncMock, return_value=_make_mock_state_machine()), \
             patch("routes.search.remove_tracker", new_callable=AsyncMock), \
             patch("routes.search.remove_state_machine"), \
             patch("routes.search.SearchPipeline") as MockPipeline, \
             patch("search_cache.get_from_cache_cascade", new_callable=AsyncMock, return_value=None), \
             patch("quota.check_quota", return_value=mock_info), \
             patch("quota.check_and_increment_quota_atomic", return_value=(True, 1, 999)):

            mock_pipe = MockPipeline.return_value
            mock_pipe.run = AsyncMock(return_value=_make_sync_response())

            response = client.post("/v1/buscar", json=VALID_SEARCH_BODY)

        # Quota check exception → sync fallback, must be 200 not 202
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# T5: GET /v1/search/{id}/status → current search state
# ---------------------------------------------------------------------------

class TestSearchStatusEndpoint:
    """T5: GET /v1/search/{id}/status returns enriched SearchStatusResponse.

    STAB-009 AC3: Updated to test enriched response format.
    The endpoint now returns SearchStatusResponse with mapped status values
    (e.g., "fetching" → "running") and new field names (progress_pct, etc.).
    """

    def test_search_status_endpoint(self, client):
        """AC3: Status endpoint returns enriched response when search_id known (DB fallback)."""
        search_id = str(uuid.uuid4())
        mock_status = {
            "search_id": search_id,
            "status": "fetching",
            "progress": 30,
            "stage": "fetching",
            "started_at": "2026-02-25T10:00:00Z",
            "elapsed_ms": 5000,
            "ufs_completed": 2,
            "ufs_total": 5,
            "ufs_failed": 0,
            "llm_status": "pending",
            "excel_status": "pending",
            "error_message": None,
            "error_code": None,
        }

        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_status.get_state_machine", return_value=None), \
             patch("routes.search_status.get_search_status", new_callable=AsyncMock, return_value=mock_status):
            response = client.get(f"/v1/search/{search_id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["search_id"] == search_id
        # AC3: "fetching" maps to "running" in enriched response
        assert data["status"] == "running"
        assert data["progress_pct"] == 30
        assert data["elapsed_s"] == 5.0

    def test_search_status_endpoint_not_found(self, client):
        """AC3: Returns 404 when search_id unknown."""
        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_status.get_state_machine", return_value=None), \
             patch("routes.search_status.get_search_status", new_callable=AsyncMock, return_value=None):
            response = client.get("/v1/search/nonexistent-id/status")

        assert response.status_code == 404

    def test_search_status_endpoint_completed(self, client):
        """AC3: Status shows 'completed' after search finishes."""
        search_id = str(uuid.uuid4())
        mock_status = {
            "search_id": search_id,
            "status": "completed",
            "progress": 100,
            "stage": "persisting",
            "started_at": "2026-02-25T10:00:00Z",
            "elapsed_ms": 15000,
            "ufs_completed": 5,
            "ufs_total": 5,
            "ufs_failed": 0,
            "llm_status": "done",
            "excel_status": "done",
            "error_message": None,
            "error_code": None,
        }

        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_status.get_state_machine", return_value=None), \
             patch("routes.search_status.get_search_status", new_callable=AsyncMock, return_value=mock_status):
            response = client.get(f"/v1/search/{search_id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress_pct"] == 100
        assert data["results_url"] == f"/v1/search/{search_id}/results"

    def test_search_status_requires_auth(self):
        """Status endpoint requires authentication."""
        # Override autouse fixture — test without auth override
        app.dependency_overrides.pop(require_auth, None)

        # Restore the real require_auth (will reject missing token)
        test_client = TestClient(app, raise_server_exceptions=False)
        response = test_client.get("/v1/search/some-id/status")

        # 401 or 403 — unauthenticated request rejected
        assert response.status_code in (401, 403, 422)

        # Restore override for subsequent tests
        mock_user = {"id": "test-user-id", "email": "test@example.com", "plan_type": "smartlic_pro"}
        app.dependency_overrides[require_auth] = lambda: mock_user


# ---------------------------------------------------------------------------
# T6: GET /search/{id}/results → 200 with results when ready
# ---------------------------------------------------------------------------

class TestSearchResultsReady:
    """T6: GET /search/{id}/results returns 200 + result body when ready."""

    def test_search_results_ready(self, client):
        """AC4: Returns 200 with full result dict when results are available."""
        mock_result = {
            "total_filtrado": 10,
            "total_raw": 100,
            "licitacoes": [],
            "resumo": {
                "resumo_executivo": "Teste",
                "total_oportunidades": 10,
                "valor_total": 50000.0,
                "destaques": [],
            },
        }

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=mock_result):
            response = client.get("/v1/search/test-search-id/results")

        assert response.status_code == 200
        data = response.json()
        assert data["total_filtrado"] == 10
        assert "licitacoes" in data

    def test_search_results_ready_has_cache_control_header(self, client):
        """AC4: 200 response includes Cache-Control: max-age=300."""
        mock_result = {"total_filtrado": 5, "licitacoes": []}

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=mock_result):
            response = client.get("/v1/search/test-search-id/results")

        assert response.status_code == 200
        # Cache-Control header set on ready results (AC4)
        cache_header = response.headers.get("cache-control", "")
        assert "max-age=300" in cache_header

    def test_search_results_404_when_expired(self, client):
        """AC4: Returns 404 when search_id not found or expired."""
        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_status.get_search_status", new_callable=AsyncMock, return_value=None):

            response = client.get("/v1/search/expired-id/results")

        assert response.status_code == 404
        detail = response.json().get("detail", "")
        # Detail should be user-friendly (in Portuguese)
        assert len(detail) > 0


# ---------------------------------------------------------------------------
# T7: GET /search/{id}/results → 202 when still processing
# ---------------------------------------------------------------------------

class TestSearchResultsStillProcessing:
    """T7: GET /search/{id}/results returns 202 with status when not yet ready."""

    def test_search_results_still_processing(self, client):
        """AC4: Returns 202 with status dict when results are still in progress."""
        search_id = "in-progress-search-id"
        mock_status = {
            "search_id": search_id,
            "status": "fetching",
            "progress": 30,
        }

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_status.get_search_status", new_callable=AsyncMock, return_value=mock_status):

            response = client.get(f"/v1/search/{search_id}/results")

        assert response.status_code == 202
        data = response.json()
        assert data["search_id"] == search_id
        assert data["status"] == "fetching"
        assert data["progress"] == 30
        assert "message" in data

    def test_search_results_still_processing_has_message(self, client):
        """AC4: 202 response includes a user-facing message."""
        mock_status = {"search_id": "abc", "status": "filtering", "progress": 60}

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_status.get_search_status", new_callable=AsyncMock, return_value=mock_status):

            response = client.get("/v1/search/abc/results")

        assert response.status_code == 202
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 0

    def test_search_results_202_reflects_current_status(self, client):
        """AC4: 202 status field reflects the actual current state."""
        for state, expected_progress in [("validating", 5), ("filtering", 60), ("enriching", 70)]:
            mock_status = {
                "search_id": "check-state",
                "status": state,
                "progress": expected_progress,
            }

            with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=None), \
                 patch("routes.search_status.get_search_status", new_callable=AsyncMock, return_value=mock_status):

                response = client.get("/v1/search/check-state/results")

            assert response.status_code == 202
            assert response.json()["status"] == state


# ---------------------------------------------------------------------------
# T8: SearchQueuedResponse schema validation
# ---------------------------------------------------------------------------

class TestSearchQueuedResponseSchema:
    """T8: Validate the SearchQueuedResponse Pydantic schema (AC1 contract)."""

    def test_schema_has_required_fields(self):
        """AC1: SearchQueuedResponse schema has all required fields."""
        from schemas import SearchQueuedResponse

        resp = SearchQueuedResponse(
            search_id="abc-123",
            status_url="/v1/search/abc-123/status",
            progress_url="/buscar-progress/abc-123",
            estimated_duration_s=45,
        )
        assert resp.search_id == "abc-123"
        assert resp.status == "queued"
        assert resp.status_url == "/v1/search/abc-123/status"
        assert resp.progress_url == "/buscar-progress/abc-123"
        assert resp.estimated_duration_s == 45

    def test_schema_default_status_is_queued(self):
        """AC1: Default status is 'queued'."""
        from schemas import SearchQueuedResponse

        resp = SearchQueuedResponse(
            search_id="xyz",
            status_url="/v1/search/xyz/status",
            progress_url="/buscar-progress/xyz",
        )
        assert resp.status == "queued"

    def test_schema_default_estimated_duration(self):
        """AC1: Default estimated_duration_s is 45s."""
        from schemas import SearchQueuedResponse

        resp = SearchQueuedResponse(
            search_id="xyz",
            status_url="/v1/search/xyz/status",
            progress_url="/buscar-progress/xyz",
        )
        assert resp.estimated_duration_s == 45


# ---------------------------------------------------------------------------
# T9: Quota consumed in POST before dispatch (AC8) — STORY-292
# ---------------------------------------------------------------------------

class TestQuotaConsumedBeforeDispatch:
    """T9: Quota is consumed in POST before asyncio.create_task dispatch."""

    def test_quota_checked_on_async_path(self, client):
        """AC8: Quota check and increment happen before background task dispatched."""
        mock_info = Mock()
        mock_info.allowed = True
        mock_info.error_message = ""
        mock_info.capabilities = {"max_requests_per_month": 1000}

        with patch("quota.check_quota", return_value=mock_info) as mock_check, \
             patch("quota.check_and_increment_quota_atomic", return_value=(True, 1, 999)) as mock_atomic, \
             patch("config.get_feature_flag", return_value=True), \
             patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)), \
             patch("routes.search.create_tracker", new_callable=AsyncMock, return_value=_make_mock_tracker()), \
             patch("routes.search.create_state_machine", new_callable=AsyncMock, return_value=_make_mock_state_machine()), \
             patch("routes.search._run_async_search", new_callable=AsyncMock):

            response = client.post("/v1/buscar", json=VALID_SEARCH_BODY)

        assert response.status_code == 202
        # Both quota check and atomic increment should be called before task dispatched
        mock_check.assert_called_once()
        mock_atomic.assert_called_once()

    def test_quota_exceeded_blocks_async_dispatch(self, client):
        """AC8: Quota exceeded → 403, background task never dispatched."""
        mock_info = Mock()
        mock_info.allowed = False
        mock_info.error_message = "Limite de análises atingido."
        mock_info.capabilities = {"max_requests_per_month": 10}

        with patch("quota.check_quota", return_value=mock_info), \
             patch("config.get_feature_flag", return_value=True), \
             patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)), \
             patch("routes.search.create_tracker", new_callable=AsyncMock, return_value=_make_mock_tracker()), \
             patch("routes.search.create_state_machine", new_callable=AsyncMock, return_value=_make_mock_state_machine()), \
             patch("routes.search.remove_tracker", new_callable=AsyncMock), \
             patch("routes.search._run_async_search", new_callable=AsyncMock) as mock_run:

            response = client.post("/v1/buscar", json=VALID_SEARCH_BODY)

        assert response.status_code == 403
        mock_run.assert_not_called()
