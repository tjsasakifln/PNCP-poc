"""STORY-364: Excel Resilience — Backend tests for AC1, AC2, AC3, AC8.

Tests cover:
  AC1/AC9:  Status endpoint returns excel_url / excel_status from Redis job result
  AC2/AC11: Results endpoint merges Excel data when not already present
  AC3:      _update_results_excel_url() patches main Redis results key
  AC8/AC10: POST /v1/search/{id}/regenerate-excel (202, 404, inline fallback)

Follows project test conventions:
  - auth: app.dependency_overrides[require_auth]
  - job_queue: mock at job_queue.get_job_result (imported locally in routes)
  - status endpoint mocks: routes.search_status.get_tracker, routes.search_status.get_state_machine
  - redis direct tests: mock redis_pool.get_redis_pool (job_queue imports from redis_pool)
"""

import io
import json
import time
import uuid

import pytest
from unittest.mock import patch, Mock, AsyncMock

from fastapi.testclient import TestClient

from main import app
from auth import require_auth


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def mock_auth():
    """Override require_auth dependency for all tests."""
    mock_user = {
        "id": "test-user-id",
        "email": "test@example.com",
        "plan_type": "smartlic_pro",
    }
    app.dependency_overrides[require_auth] = lambda: mock_user
    yield mock_user
    app.dependency_overrides.pop(require_auth, None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tracker(uf_count=5, ufs_completed=3, is_complete=False, created_at=None):
    """Create a mock progress tracker with realistic attributes."""
    tracker = Mock()
    tracker.uf_count = uf_count
    tracker._ufs_completed = ufs_completed
    tracker._is_complete = is_complete
    tracker.created_at = created_at or time.time() - 15.0
    return tracker


def _make_state_machine(state_value="completed"):
    """Create a mock state machine with a current_state."""
    from models.search_state import SearchState
    sm = Mock()
    sm.current_state = SearchState(state_value)
    return sm


def _search_id():
    return str(uuid.uuid4())


def _status_fast_path_mocks(tracker, sm, bg_result=None, excel_job_result=None):
    """Context manager stack for status endpoint fast-path (in-memory) tests.

    Returns a dict of context managers for use with nested `with` statements.
    Mock get_job_result at the job_queue module level since the status endpoint
    does `from job_queue import get_job_result` at call time.
    """
    mocks = {
        "tracker": patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker),
        "state_machine": patch("routes.search_status.get_state_machine", return_value=sm),
    }
    if bg_result is not None:
        mocks["bg_results"] = patch("routes.search_status.get_background_results", return_value=bg_result)
    mocks["get_job_result"] = patch(
        "job_queue.get_job_result",
        new_callable=AsyncMock,
        return_value=excel_job_result,
    )
    return mocks


# ===========================================================================
# AC9: Status endpoint returns excel_url when Excel job result exists
# ===========================================================================

class TestStatusExcelUrlReady:
    """AC9: GET /v1/search/{id}/status includes excel_url when Excel is ready."""

    def test_status_returns_excel_url_when_ready(self, client):
        """Excel job result with download_url -> excel_url populated."""
        sid = _search_id()
        tracker = _make_tracker(is_complete=True, ufs_completed=5)
        sm = _make_state_machine("completed")

        excel_result = {
            "download_url": "https://storage.example.com/excel/test.xlsx",
            "excel_status": "ready",
        }
        mock_bg = Mock()
        mock_bg.total_filtrado = 10

        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_status.get_state_machine", return_value=sm), \
             patch("routes.search_status.get_background_results", return_value=mock_bg), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=excel_result):

            response = client.get(f"/v1/search/{sid}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["excel_url"] == "https://storage.example.com/excel/test.xlsx"
        assert data["excel_status"] == "ready"

    def test_status_returns_excel_url_on_db_fallback(self, client):
        """Slow path (DB fallback) also includes excel_url from job result."""
        sid = _search_id()
        db_status = {
            "search_id": sid,
            "status": "completed",
            "progress": 100,
            "started_at": "2026-03-01T10:00:00Z",
            "elapsed_ms": 45000,
        }
        excel_result = {
            "download_url": "https://storage.example.com/excel/fallback.xlsx",
            "excel_status": "ready",
        }

        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_status.get_state_machine", return_value=None), \
             patch("routes.search_status.get_search_status", new_callable=AsyncMock, return_value=db_status), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=excel_result):

            response = client.get(f"/v1/search/{sid}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["excel_url"] == "https://storage.example.com/excel/fallback.xlsx"
        assert data["excel_status"] == "ready"


# ===========================================================================
# AC9: Status endpoint returns excel_status when Excel is processing
# ===========================================================================

class TestStatusExcelProcessing:
    """AC9: excel_status=processing when Excel generation is in progress."""

    def test_status_shows_processing_excel(self, client):
        """Excel job result with excel_status=processing, no download_url yet."""
        sid = _search_id()
        tracker = _make_tracker(is_complete=True, ufs_completed=5)
        sm = _make_state_machine("completed")

        excel_result = {
            "excel_status": "processing",
        }
        mock_bg = Mock()
        mock_bg.total_filtrado = 5

        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_status.get_state_machine", return_value=sm), \
             patch("routes.search_status.get_background_results", return_value=mock_bg), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=excel_result):

            response = client.get(f"/v1/search/{sid}/status")

        data = response.json()
        assert data["excel_status"] == "processing"
        assert data["excel_url"] is None


# ===========================================================================
# AC9: Status returns null excel fields when no Excel result
# ===========================================================================

class TestStatusNoExcelResult:
    """AC9: excel_url and excel_status are null when no Excel job result exists."""

    def test_status_null_excel_when_no_result(self, client):
        """No Excel job result in Redis -> both fields null."""
        sid = _search_id()
        tracker = _make_tracker(is_complete=True, ufs_completed=5)
        sm = _make_state_machine("completed")

        mock_bg = Mock()
        mock_bg.total_filtrado = 3

        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_status.get_state_machine", return_value=sm), \
             patch("routes.search_status.get_background_results", return_value=mock_bg), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=None):

            response = client.get(f"/v1/search/{sid}/status")

        data = response.json()
        assert data["excel_url"] is None
        assert data["excel_status"] is None

    def test_status_null_excel_when_redis_unavailable(self, client):
        """Redis pool returns None (get_job_result returns None) -> excel fields null."""
        sid = _search_id()
        tracker = _make_tracker(is_complete=True, ufs_completed=5)
        sm = _make_state_machine("completed")

        mock_bg = Mock()
        mock_bg.total_filtrado = 2

        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_status.get_state_machine", return_value=sm), \
             patch("routes.search_status.get_background_results", return_value=mock_bg), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=None):

            response = client.get(f"/v1/search/{sid}/status")

        data = response.json()
        assert data["excel_url"] is None
        assert data["excel_status"] is None

    def test_status_running_search_has_null_excel(self, client):
        """While search is still running, excel fields are null."""
        sid = _search_id()
        tracker = _make_tracker(uf_count=5, ufs_completed=2, is_complete=False)
        sm = _make_state_machine("fetching")

        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_status.get_state_machine", return_value=sm), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=None):

            response = client.get(f"/v1/search/{sid}/status")

        data = response.json()
        assert data["status"] == "running"
        assert data["excel_url"] is None
        assert data["excel_status"] is None


# ===========================================================================
# AC9: SearchStatusResponse schema has excel fields
# ===========================================================================

class TestSearchStatusResponseExcelSchema:
    """AC9: SearchStatusResponse Pydantic model includes excel_url + excel_status."""

    def test_schema_accepts_excel_fields(self):
        from schemas import SearchStatusResponse

        resp = SearchStatusResponse(
            search_id="test-123",
            status="completed",
            progress_pct=100,
            excel_url="https://example.com/file.xlsx",
            excel_status="ready",
        )
        assert resp.excel_url == "https://example.com/file.xlsx"
        assert resp.excel_status == "ready"

    def test_schema_defaults_excel_fields_to_none(self):
        from schemas import SearchStatusResponse

        resp = SearchStatusResponse(
            search_id="test-456",
            status="running",
        )
        assert resp.excel_url is None
        assert resp.excel_status is None

    def test_schema_allows_processing_status(self):
        from schemas import SearchStatusResponse

        resp = SearchStatusResponse(
            search_id="test-789",
            status="completed",
            excel_status="processing",
        )
        assert resp.excel_status == "processing"
        assert resp.excel_url is None

    def test_schema_serializes_to_json(self):
        from schemas import SearchStatusResponse

        resp = SearchStatusResponse(
            search_id="json-test",
            status="completed",
            excel_url="https://example.com/file.xlsx",
            excel_status="ready",
        )
        data = resp.model_dump()
        assert "excel_url" in data
        assert "excel_status" in data
        assert data["excel_url"] == "https://example.com/file.xlsx"


# ===========================================================================
# AC10: Regenerate-excel returns 202 when results exist and ARQ available
# ===========================================================================

class TestRegenerateExcel202:
    """AC10: POST /v1/search/{id}/regenerate-excel returns 202 with ARQ."""

    def test_regenerate_returns_202_arq_available(self, client):
        """Results found + ARQ available -> 202 with processing status."""
        sid = _search_id()
        stored_result = {
            "total_filtrado": 5,
            "licitacoes": [
                {"objetoCompra": "Aquisicao de uniformes", "uf": "SP"},
                {"objetoCompra": "Servicos de engenharia", "uf": "RJ"},
            ],
        }

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=stored_result), \
             patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=True), \
             patch("job_queue.enqueue_job", new_callable=AsyncMock) as mock_enqueue:

            response = client.post(f"/v1/search/{sid}/regenerate-excel")

        assert response.status_code == 202
        data = response.json()
        assert data["excel_status"] == "processing"
        assert data["search_id"] == sid
        mock_enqueue.assert_called_once()
        # Verify the correct job name and kwargs
        call_args = mock_enqueue.call_args
        assert call_args[0][0] == "excel_generation_job"
        assert call_args[1]["search_id"] == sid
        assert len(call_args[1]["licitacoes"]) == 2

    def test_regenerate_extracts_licitacoes_from_dict(self, client):
        """Result as dict -> licitacoes extracted correctly."""
        sid = _search_id()
        stored_result = {
            "licitacoes": [{"objetoCompra": "Test bid", "uf": "MG"}],
        }

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=stored_result), \
             patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=True), \
             patch("job_queue.enqueue_job", new_callable=AsyncMock) as mock_enqueue:

            response = client.post(f"/v1/search/{sid}/regenerate-excel")

        assert response.status_code == 202
        assert mock_enqueue.call_args[1]["licitacoes"] == [{"objetoCompra": "Test bid", "uf": "MG"}]

    def test_regenerate_response_includes_message(self, client):
        """202 response includes a user-facing message."""
        sid = _search_id()
        stored_result = {
            "licitacoes": [{"objetoCompra": "Test", "uf": "SP"}],
        }

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=stored_result), \
             patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=True), \
             patch("job_queue.enqueue_job", new_callable=AsyncMock):

            response = client.post(f"/v1/search/{sid}/regenerate-excel")

        assert response.status_code == 202
        assert "message" in response.json()


# ===========================================================================
# AC10: Regenerate-excel returns 404 when results expired
# ===========================================================================

class TestRegenerateExcel404:
    """AC10: POST /v1/search/{id}/regenerate-excel returns 404 when results not found."""

    def test_regenerate_404_no_results(self, client):
        """Results expired or not found -> 404."""
        sid = _search_id()

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=None):
            response = client.post(f"/v1/search/{sid}/regenerate-excel")

        assert response.status_code == 404
        assert "detail" in response.json()

    def test_regenerate_404_empty_licitacoes(self, client):
        """Results found but with empty licitacoes list -> 404."""
        sid = _search_id()
        stored_result = {
            "total_filtrado": 0,
            "licitacoes": [],
        }

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=stored_result):
            response = client.post(f"/v1/search/{sid}/regenerate-excel")

        assert response.status_code == 404
        data = response.json()
        # Check the detail mentions licitacao (accent-safe check)
        detail_lower = data["detail"].lower()
        assert "licita" in detail_lower

    def test_regenerate_404_result_has_no_licitacoes_key(self, client):
        """Result dict without licitacoes key -> 404 (empty list fallback)."""
        sid = _search_id()
        stored_result = {"total_filtrado": 0}

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=stored_result):
            response = client.post(f"/v1/search/{sid}/regenerate-excel")

        assert response.status_code == 404


# ===========================================================================
# AC10: Regenerate-excel inline fallback when ARQ unavailable
# ===========================================================================

class TestRegenerateExcelInlineFallback:
    """AC10: When ARQ is unavailable, regenerate-excel generates Excel inline."""

    def test_regenerate_inline_success(self, client):
        """ARQ unavailable + inline generation succeeds -> 200 with download_url."""
        sid = _search_id()
        stored_result = {
            "licitacoes": [{"objetoCompra": "Test bid", "uf": "SP"}],
        }
        mock_buffer = io.BytesIO(b"PK\x03\x04fake-xlsx-content")

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=stored_result), \
             patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=False), \
             patch("routes.search_status.create_excel", return_value=mock_buffer), \
             patch("storage.upload_excel", return_value={"signed_url": "https://storage.example.com/inline.xlsx"}), \
             patch("job_queue.persist_job_result", new_callable=AsyncMock):

            response = client.post(f"/v1/search/{sid}/regenerate-excel")

        assert response.status_code == 200
        data = response.json()
        assert data["excel_status"] == "ready"
        assert data["download_url"] == "https://storage.example.com/inline.xlsx"
        assert data["search_id"] == sid

    def test_regenerate_inline_persists_job_result(self, client):
        """Inline fallback persists the result via persist_job_result."""
        sid = _search_id()
        stored_result = {
            "licitacoes": [{"objetoCompra": "Test bid", "uf": "SP"}],
        }
        mock_buffer = io.BytesIO(b"PK\x03\x04fake-xlsx-content")

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=stored_result), \
             patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=False), \
             patch("routes.search_status.create_excel", return_value=mock_buffer), \
             patch("storage.upload_excel", return_value={"signed_url": "https://storage.example.com/persisted.xlsx"}), \
             patch("job_queue.persist_job_result", new_callable=AsyncMock) as mock_persist:

            response = client.post(f"/v1/search/{sid}/regenerate-excel")

        assert response.status_code == 200
        mock_persist.assert_called_once()
        persist_args = mock_persist.call_args
        assert persist_args[0][0] == sid
        assert persist_args[0][1] == "excel_result"
        assert persist_args[0][2]["excel_status"] == "ready"
        assert persist_args[0][2]["download_url"] == "https://storage.example.com/persisted.xlsx"

    def test_regenerate_inline_failure_returns_500(self, client):
        """ARQ unavailable + inline generation fails -> 500."""
        sid = _search_id()
        stored_result = {
            "licitacoes": [{"objetoCompra": "Test bid", "uf": "SP"}],
        }

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=stored_result), \
             patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=False), \
             patch("routes.search_status.create_excel", side_effect=Exception("Excel generation error")):

            response = client.post(f"/v1/search/{sid}/regenerate-excel")

        assert response.status_code == 500
        assert "detail" in response.json()

    def test_regenerate_inline_upload_failure_returns_500(self, client):
        """ARQ unavailable + upload returns None -> 500."""
        sid = _search_id()
        stored_result = {
            "licitacoes": [{"objetoCompra": "Test bid", "uf": "SP"}],
        }
        mock_buffer = io.BytesIO(b"PK\x03\x04fake-xlsx-content")

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=stored_result), \
             patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=False), \
             patch("routes.search_status.create_excel", return_value=mock_buffer), \
             patch("storage.upload_excel", return_value=None):

            response = client.post(f"/v1/search/{sid}/regenerate-excel")

        # upload_excel returns None -> no signed_url -> falls through to 500
        assert response.status_code == 500

    def test_regenerate_requires_auth(self, client):
        """Endpoint requires authentication."""
        # Remove auth override
        app.dependency_overrides.pop(require_auth, None)

        sid = _search_id()
        response = client.post(f"/v1/search/{sid}/regenerate-excel")

        # Without auth, should get 401 or 403
        assert response.status_code in (401, 403)

        # Restore for subsequent tests
        app.dependency_overrides[require_auth] = lambda: {
            "id": "test-user-id",
            "email": "test@example.com",
            "plan_type": "smartlic_pro",
        }


# ===========================================================================
# AC11: Results endpoint merges Excel data when not already in response
# ===========================================================================

class TestResultsMergeExcel:
    """AC11: GET /search/{id}/results merges Excel job result into response."""

    def test_results_merges_excel_when_not_present(self, client):
        """Result has no download_url -> merge from Excel job result."""
        sid = _search_id()
        stored_result = {
            "total_filtrado": 3,
            "licitacoes": [{"objetoCompra": "Test", "uf": "SP"}],
            # No download_url
        }
        excel_job_result = {
            "download_url": "https://storage.example.com/merged.xlsx",
            "excel_status": "ready",
        }

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=stored_result), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=excel_job_result):

            response = client.get(f"/v1/search/{sid}/results")

        assert response.status_code == 200
        data = response.json()
        assert data["download_url"] == "https://storage.example.com/merged.xlsx"
        assert data["excel_status"] == "ready"

    def test_results_preserves_existing_download_url(self, client):
        """Result already has download_url -> do NOT overwrite."""
        sid = _search_id()
        stored_result = {
            "total_filtrado": 5,
            "licitacoes": [{"objetoCompra": "Test", "uf": "RJ"}],
            "download_url": "https://storage.example.com/original.xlsx",
        }
        excel_job_result = {
            "download_url": "https://storage.example.com/should-not-replace.xlsx",
            "excel_status": "ready",
        }

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=stored_result), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=excel_job_result):

            response = client.get(f"/v1/search/{sid}/results")

        assert response.status_code == 200
        data = response.json()
        # Original URL preserved, not overwritten
        assert data["download_url"] == "https://storage.example.com/original.xlsx"

    def test_results_no_excel_result_still_works(self, client):
        """No Excel job result -> response returned without download_url."""
        sid = _search_id()
        stored_result = {
            "total_filtrado": 2,
            "licitacoes": [{"objetoCompra": "Test", "uf": "MG"}],
        }

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=stored_result), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=None):

            response = client.get(f"/v1/search/{sid}/results")

        assert response.status_code == 200
        data = response.json()
        assert "download_url" not in data or data.get("download_url") is None

    def test_results_has_cache_control_when_completed(self, client):
        """Completed results -> Cache-Control: max-age=300."""
        sid = _search_id()
        stored_result = {
            "total_filtrado": 1,
            "licitacoes": [{"objetoCompra": "Test", "uf": "SP"}],
        }

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=stored_result), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=None):

            response = client.get(f"/v1/search/{sid}/results")

        assert response.status_code == 200
        cache_header = response.headers.get("cache-control", "")
        assert "max-age=300" in cache_header

    def test_results_excel_merge_defaults_excel_status_to_ready(self, client):
        """When Excel result has download_url but no excel_status, default to 'ready'."""
        sid = _search_id()
        stored_result = {
            "total_filtrado": 1,
            "licitacoes": [{"objetoCompra": "Test", "uf": "SP"}],
        }
        excel_job_result = {
            "download_url": "https://storage.example.com/default-status.xlsx",
            # No excel_status key
        }

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=stored_result), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=excel_job_result):

            response = client.get(f"/v1/search/{sid}/results")

        assert response.status_code == 200
        data = response.json()
        assert data["download_url"] == "https://storage.example.com/default-status.xlsx"
        assert data["excel_status"] == "ready"


# ===========================================================================
# AC3: _update_results_excel_url patches Redis results key
# ===========================================================================

class TestUpdateResultsExcelUrl:
    """AC3: _update_results_excel_url() writes download_url into main results key."""

    @pytest.mark.asyncio
    async def test_update_patches_existing_result(self):
        """Existing result in Redis is patched with download_url + excel_status."""
        sid = _search_id()
        existing_data = json.dumps({
            "total_filtrado": 5,
            "licitacoes": [{"objetoCompra": "Test"}],
        })

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=existing_data)
        mock_redis.set = AsyncMock()

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            from job_queue import _update_results_excel_url
            await _update_results_excel_url(sid, "https://example.com/excel.xlsx")

        # Verify Redis SET was called with the patched data
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        saved_key = call_args[0][0]
        saved_data = json.loads(call_args[0][1])

        assert saved_key == f"smartlic:results:{sid}"
        assert saved_data["download_url"] == "https://example.com/excel.xlsx"
        assert saved_data["excel_status"] == "ready"
        # Original fields preserved
        assert saved_data["total_filtrado"] == 5

    @pytest.mark.asyncio
    async def test_update_noop_when_no_existing_result(self):
        """No existing result in Redis -> no SET operation."""
        sid = _search_id()

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            from job_queue import _update_results_excel_url
            await _update_results_excel_url(sid, "https://example.com/unused.xlsx")

        mock_redis.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_noop_when_redis_unavailable(self):
        """Redis pool returns None -> graceful no-op."""
        sid = _search_id()

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=None):
            from job_queue import _update_results_excel_url
            # Should not raise
            await _update_results_excel_url(sid, "https://example.com/unused.xlsx")

    @pytest.mark.asyncio
    async def test_update_uses_keepttl(self):
        """SET call uses keepttl=True to preserve existing TTL."""
        sid = _search_id()
        existing_data = json.dumps({"total_filtrado": 1, "licitacoes": []})

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=existing_data)
        mock_redis.set = AsyncMock()

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            from job_queue import _update_results_excel_url
            await _update_results_excel_url(sid, "https://example.com/ttl-test.xlsx")

        call_kwargs = mock_redis.set.call_args[1]
        assert call_kwargs.get("keepttl") is True

    @pytest.mark.asyncio
    async def test_update_handles_redis_error_gracefully(self):
        """Redis error during SET -> logged, not raised."""
        sid = _search_id()
        existing_data = json.dumps({"total_filtrado": 1, "licitacoes": []})

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=existing_data)
        mock_redis.set = AsyncMock(side_effect=Exception("Redis connection lost"))

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            from job_queue import _update_results_excel_url
            # Should not raise
            await _update_results_excel_url(sid, "https://example.com/error-test.xlsx")


# ===========================================================================
# AC3: get_job_result retrieves persisted Excel job result
# ===========================================================================

class TestGetJobResult:
    """AC3: get_job_result() reads from Redis keyed by search_id + field."""

    @pytest.mark.asyncio
    async def test_get_job_result_returns_parsed_json(self):
        """Valid JSON in Redis -> returns parsed dict."""
        sid = _search_id()
        stored_value = json.dumps({
            "download_url": "https://example.com/test.xlsx",
            "excel_status": "ready",
        })

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=stored_value)

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            from job_queue import get_job_result
            result = await get_job_result(sid, "excel_result")

        assert result is not None
        assert result["download_url"] == "https://example.com/test.xlsx"
        assert result["excel_status"] == "ready"
        # Verify correct key pattern
        mock_redis.get.assert_called_once_with(f"smartlic:job_result:{sid}:excel_result")

    @pytest.mark.asyncio
    async def test_get_job_result_returns_none_when_missing(self):
        """No key in Redis -> returns None."""
        sid = _search_id()

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            from job_queue import get_job_result
            result = await get_job_result(sid, "excel_result")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_job_result_returns_none_when_redis_unavailable(self):
        """Redis pool returns None -> returns None."""
        sid = _search_id()

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=None):
            from job_queue import get_job_result
            result = await get_job_result(sid, "excel_result")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_job_result_handles_invalid_json(self):
        """Invalid JSON in Redis -> returns raw string."""
        sid = _search_id()

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="not-valid-json")

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            from job_queue import get_job_result
            result = await get_job_result(sid, "excel_result")

        # Returns raw string when JSON parsing fails
        assert result == "not-valid-json"

    @pytest.mark.asyncio
    async def test_get_job_result_handles_redis_error(self):
        """Redis error during GET -> returns None (graceful fallback)."""
        sid = _search_id()

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Connection refused"))

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            from job_queue import get_job_result
            result = await get_job_result(sid, "excel_result")

        assert result is None


# ===========================================================================
# Integration: Full flow — status -> results -> regenerate
# ===========================================================================

class TestExcelResilienceFullFlow:
    """Integration: Verify the full Excel resilience flow works end-to-end."""

    def test_status_then_results_consistency(self, client):
        """Status and results endpoints return consistent Excel data."""
        sid = _search_id()
        tracker = _make_tracker(is_complete=True, ufs_completed=5)
        sm = _make_state_machine("completed")
        mock_bg = Mock()
        mock_bg.total_filtrado = 3

        excel_data = {
            "download_url": "https://storage.example.com/consistent.xlsx",
            "excel_status": "ready",
        }

        stored_result = {
            "total_filtrado": 3,
            "licitacoes": [{"objetoCompra": "Test", "uf": "SP"}],
        }

        # Check status endpoint
        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_status.get_state_machine", return_value=sm), \
             patch("routes.search_status.get_background_results", return_value=mock_bg), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=excel_data):

            status_resp = client.get(f"/v1/search/{sid}/status")

        # Check results endpoint
        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=stored_result), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=excel_data):

            results_resp = client.get(f"/v1/search/{sid}/results")

        # Both should report the same Excel URL
        assert status_resp.json()["excel_url"] == results_resp.json()["download_url"]
        assert status_resp.json()["excel_status"] == "ready"
        assert results_resp.json()["excel_status"] == "ready"

    def test_regenerate_after_expired_excel(self, client):
        """After Excel expires, regenerate creates a new one."""
        sid = _search_id()
        stored_result = {
            "licitacoes": [{"objetoCompra": "Test bid", "uf": "SP"}],
        }

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=stored_result), \
             patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=True), \
             patch("job_queue.enqueue_job", new_callable=AsyncMock):

            response = client.post(f"/v1/search/{sid}/regenerate-excel")

        assert response.status_code == 202
        assert response.json()["excel_status"] == "processing"

    def test_full_lifecycle_status_to_regenerate(self, client):
        """Full lifecycle: status shows no Excel -> regenerate -> status shows processing."""
        sid = _search_id()
        tracker = _make_tracker(is_complete=True, ufs_completed=5)
        sm = _make_state_machine("completed")
        mock_bg = Mock()
        mock_bg.total_filtrado = 3

        # Step 1: Status with no Excel result
        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_status.get_state_machine", return_value=sm), \
             patch("routes.search_status.get_background_results", return_value=mock_bg), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=None):

            status1 = client.get(f"/v1/search/{sid}/status")

        assert status1.json()["excel_url"] is None
        assert status1.json()["excel_status"] is None

        # Step 2: Regenerate Excel
        stored_result = {
            "licitacoes": [{"objetoCompra": "Test", "uf": "SP"}],
        }
        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=stored_result), \
             patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=True), \
             patch("job_queue.enqueue_job", new_callable=AsyncMock):

            regen = client.post(f"/v1/search/{sid}/regenerate-excel")

        assert regen.status_code == 202
        assert regen.json()["excel_status"] == "processing"

        # Step 3: Status now shows Excel processing
        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_status.get_state_machine", return_value=sm), \
             patch("routes.search_status.get_background_results", return_value=mock_bg), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value={"excel_status": "processing"}):

            status2 = client.get(f"/v1/search/{sid}/status")

        assert status2.json()["excel_status"] == "processing"
        assert status2.json()["excel_url"] is None
