"""GTM-STAB-009 AC3/AC4: Enriched search status + Cache-Control headers.

Tests:
1. Status returns all fields for running search (in-memory fast path)
2. Status returns results_count and results_url when completed
3. Status returns progress_pct from progress tracker
4. Status is lightweight (<50ms, no heavy queries)
5. Results endpoint has Cache-Control: max-age=300 when completed
6. Results endpoint has Cache-Control: no-cache when still running
7. Status returns "timeout" status for timed-out searches
8. Unknown search_id returns 404
"""

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

def _make_tracker(uf_count=5, ufs_completed=2, is_complete=False, created_at=None):
    """Create a mock progress tracker with realistic attributes."""
    tracker = Mock()
    tracker.uf_count = uf_count
    tracker._ufs_completed = ufs_completed
    tracker._is_complete = is_complete
    tracker.created_at = created_at or time.time() - 10.0  # 10s ago
    return tracker


def _make_state_machine(state_value="fetching"):
    """Create a mock state machine with a current_state."""
    from models.search_state import SearchState
    sm = Mock()
    sm.current_state = SearchState(state_value)
    return sm


# ===========================================================================
# Test 1: Status returns all fields for running search
# ===========================================================================

class TestStatusAllFieldsRunning:
    """AC3: Status endpoint returns all SearchStatusResponse fields for a running search."""

    def test_status_returns_all_fields(self, client):
        search_id = str(uuid.uuid4())
        tracker = _make_tracker(uf_count=5, ufs_completed=2)
        sm = _make_state_machine("fetching")

        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_status.get_state_machine", return_value=sm):

            response = client.get(f"/v1/search/{search_id}/status")

        assert response.status_code == 200
        data = response.json()

        # All required fields present
        assert data["search_id"] == search_id
        assert data["status"] == "running"
        assert "progress_pct" in data
        assert "ufs_completed" in data
        assert "ufs_pending" in data
        assert "results_count" in data
        assert "results_url" in data
        assert "elapsed_s" in data
        assert "created_at" in data

    def test_status_running_has_no_results_url(self, client):
        """While running, results_url should be None."""
        search_id = str(uuid.uuid4())
        tracker = _make_tracker(uf_count=3, ufs_completed=1)
        sm = _make_state_machine("filtering")

        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_status.get_state_machine", return_value=sm):

            response = client.get(f"/v1/search/{search_id}/status")

        data = response.json()
        assert data["status"] == "running"
        assert data["results_url"] is None
        assert data["results_count"] == 0


# ===========================================================================
# Test 2: Status returns results_count and results_url when completed
# ===========================================================================

class TestStatusCompletedResults:
    """AC3: When completed, status includes results_count and results_url."""

    def test_completed_has_results_url(self, client):
        search_id = str(uuid.uuid4())
        tracker = _make_tracker(uf_count=5, ufs_completed=5, is_complete=True)
        sm = _make_state_machine("completed")

        # Mock background results with total_filtrado
        mock_bg_result = Mock()
        mock_bg_result.total_filtrado = 23

        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_status.get_state_machine", return_value=sm), \
             patch("routes.search_status.get_background_results", return_value=mock_bg_result):

            response = client.get(f"/v1/search/{search_id}/status")

        data = response.json()
        assert data["status"] == "completed"
        assert data["results_url"] == f"/v1/search/{search_id}/results"
        assert data["results_count"] == 23

    def test_completed_progress_is_100(self, client):
        search_id = str(uuid.uuid4())
        tracker = _make_tracker(uf_count=3, ufs_completed=3, is_complete=True)
        sm = _make_state_machine("completed")

        mock_bg = Mock()
        mock_bg.total_filtrado = 5

        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_status.get_state_machine", return_value=sm), \
             patch("routes.search_status.get_background_results", return_value=mock_bg):

            response = client.get(f"/v1/search/{search_id}/status")

        data = response.json()
        assert data["progress_pct"] == 100


# ===========================================================================
# Test 3: Status returns progress_pct from progress tracker
# ===========================================================================

class TestStatusProgressPct:
    """AC3: progress_pct is calculated from tracker's UF completion count."""

    def test_progress_scales_with_ufs(self, client):
        """Progress should increase as more UFs complete."""
        search_id = str(uuid.uuid4())
        sm = _make_state_machine("fetching")

        # 0/5 UFs complete → ~10% (baseline)
        tracker_0 = _make_tracker(uf_count=5, ufs_completed=0)
        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker_0), \
             patch("routes.search_status.get_state_machine", return_value=sm):
            resp_0 = client.get(f"/v1/search/{search_id}/status")

        # 3/5 UFs complete → higher
        tracker_3 = _make_tracker(uf_count=5, ufs_completed=3)
        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker_3), \
             patch("routes.search_status.get_state_machine", return_value=sm):
            resp_3 = client.get(f"/v1/search/{search_id}/status")

        assert resp_3.json()["progress_pct"] > resp_0.json()["progress_pct"]

    def test_complete_tracker_shows_100(self, client):
        """When tracker._is_complete=True, progress_pct=100."""
        search_id = str(uuid.uuid4())
        tracker = _make_tracker(uf_count=3, ufs_completed=3, is_complete=True)
        sm = _make_state_machine("completed")

        mock_bg = Mock()
        mock_bg.total_filtrado = 0

        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_status.get_state_machine", return_value=sm), \
             patch("routes.search_status.get_background_results", return_value=mock_bg):

            response = client.get(f"/v1/search/{search_id}/status")

        assert response.json()["progress_pct"] == 100


# ===========================================================================
# Test 4: Status is lightweight (<50ms, no heavy queries)
# ===========================================================================

class TestStatusLightweight:
    """AC3: Status endpoint must be lightweight — uses in-memory only."""

    def test_status_fast_path_no_db_call(self, client):
        """When tracker and state machine exist, get_search_status (DB) is NOT called."""
        search_id = str(uuid.uuid4())
        tracker = _make_tracker()
        sm = _make_state_machine("fetching")

        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_status.get_state_machine", return_value=sm), \
             patch("routes.search_status.get_search_status", new_callable=AsyncMock) as mock_db:

            response = client.get(f"/v1/search/{search_id}/status")

        assert response.status_code == 200
        # DB function should NOT be called on the fast path
        mock_db.assert_not_called()

    def test_status_responds_under_50ms(self, client):
        """Endpoint should respond in under 50ms with in-memory data."""
        search_id = str(uuid.uuid4())
        tracker = _make_tracker()
        sm = _make_state_machine("fetching")

        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_status.get_state_machine", return_value=sm):

            start = time.monotonic()
            response = client.get(f"/v1/search/{search_id}/status")
            elapsed_ms = (time.monotonic() - start) * 1000

        assert response.status_code == 200
        # Should be well under 50ms (typically <5ms in test)
        assert elapsed_ms < 50, f"Status endpoint took {elapsed_ms:.1f}ms, expected <50ms"


# ===========================================================================
# Test 5: Results endpoint has Cache-Control: max-age=300 when completed
# ===========================================================================

class TestResultsCacheControlCompleted:
    """AC4: GET /search/{id}/results returns Cache-Control: max-age=300 when completed."""

    def test_results_ready_has_cache_control_300(self, client):
        mock_result = {"total_filtrado": 10, "licitacoes": []}

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=mock_result):
            response = client.get("/v1/search/test-id/results")

        assert response.status_code == 200
        cache_header = response.headers.get("cache-control", "")
        assert "max-age=300" in cache_header


# ===========================================================================
# Test 6: Results endpoint has Cache-Control: no-cache when still running
# ===========================================================================

class TestResultsCacheControlRunning:
    """AC4: GET /search/{id}/results returns Cache-Control: no-cache when still processing."""

    def test_results_processing_has_no_cache(self, client):
        mock_status = {
            "search_id": "proc-id",
            "status": "fetching",
            "progress": 30,
        }

        with patch("routes.search_status.get_background_results_async", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_status.get_search_status", new_callable=AsyncMock, return_value=mock_status):

            response = client.get("/v1/search/proc-id/results")

        assert response.status_code == 202
        cache_header = response.headers.get("cache-control", "")
        assert "no-cache" in cache_header


# ===========================================================================
# Test 7: Status returns "timeout" for timed-out searches
# ===========================================================================

class TestStatusTimeout:
    """AC3: Timed-out searches report status='timeout'."""

    def test_timeout_status_in_memory(self, client):
        """In-memory state machine with TIMED_OUT → status='timeout'."""
        search_id = str(uuid.uuid4())
        tracker = _make_tracker(uf_count=5, ufs_completed=2, is_complete=True)
        sm = _make_state_machine("timed_out")

        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=tracker), \
             patch("routes.search_status.get_state_machine", return_value=sm):

            response = client.get(f"/v1/search/{search_id}/status")

        data = response.json()
        assert data["status"] == "timeout"

    def test_timeout_status_from_db_fallback(self, client):
        """DB fallback with status='timed_out' → mapped to 'timeout'."""
        search_id = str(uuid.uuid4())
        mock_db_status = {
            "search_id": search_id,
            "status": "timed_out",
            "progress": -1,
            "started_at": "2026-02-25T10:00:00Z",
            "elapsed_ms": 120000,
        }

        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_status.get_state_machine", return_value=None), \
             patch("routes.search_status.get_search_status", new_callable=AsyncMock, return_value=mock_db_status):

            response = client.get(f"/v1/search/{search_id}/status")

        data = response.json()
        assert data["status"] == "timeout"
        assert data["elapsed_s"] == 120.0


# ===========================================================================
# Test 8: Unknown search_id returns 404
# ===========================================================================

class TestStatusNotFound:
    """AC3: Unknown search_id returns 404."""

    def test_unknown_search_id_404(self, client):
        """No in-memory state AND no DB record → 404."""
        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_status.get_state_machine", return_value=None), \
             patch("routes.search_status.get_search_status", new_callable=AsyncMock, return_value=None):

            response = client.get("/v1/search/nonexistent-id/status")

        assert response.status_code == 404

    def test_404_has_detail_message(self, client):
        """404 response includes a detail message."""
        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=None), \
             patch("routes.search_status.get_state_machine", return_value=None), \
             patch("routes.search_status.get_search_status", new_callable=AsyncMock, return_value=None):

            response = client.get("/v1/search/unknown-xyz/status")

        assert response.status_code == 404
        assert "detail" in response.json()


# ===========================================================================
# Bonus: Schema validation
# ===========================================================================

class TestSearchStatusResponseSchema:
    """Validate SearchStatusResponse Pydantic schema."""

    def test_schema_all_fields(self):
        from schemas import SearchStatusResponse

        resp = SearchStatusResponse(
            search_id="abc-123",
            status="running",
            progress_pct=45,
            ufs_completed=["SP", "RJ"],
            ufs_pending=["MG"],
            results_count=0,
            results_url=None,
            elapsed_s=12.5,
            created_at="2026-02-25T10:00:00Z",
        )
        assert resp.search_id == "abc-123"
        assert resp.status == "running"
        assert resp.progress_pct == 45
        assert resp.ufs_completed == ["SP", "RJ"]
        assert resp.results_url is None

    def test_schema_defaults(self):
        from schemas import SearchStatusResponse

        resp = SearchStatusResponse(
            search_id="xyz",
            status="completed",
        )
        assert resp.progress_pct == 0
        assert resp.ufs_completed == []
        assert resp.ufs_pending == []
        assert resp.results_count == 0
        assert resp.results_url is None
        assert resp.elapsed_s == 0.0
        assert resp.created_at is None

    def test_schema_completed_with_results(self):
        from schemas import SearchStatusResponse

        resp = SearchStatusResponse(
            search_id="done-1",
            status="completed",
            progress_pct=100,
            results_count=42,
            results_url="/v1/search/done-1/results",
            elapsed_s=55.3,
        )
        assert resp.results_count == 42
        assert resp.results_url == "/v1/search/done-1/results"
