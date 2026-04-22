"""
DEBT-115 Fase 1: Contract tests for search API endpoints.

AC1: Snapshot tests for POST /buscar response schema (JSON response)
AC2: Snapshot tests for SSE event format (/buscar-progress/{id})
AC3: Contract test for retry endpoint (POST /v1/search/{id}/retry)
AC4: Contract test for status endpoint (GET /v1/search/{id}/status)
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app():
    """Create a minimal FastAPI app with search routes for contract testing."""
    app = FastAPI()
    from routes.search import router
    app.include_router(router, prefix="/v1")
    return app


def _fake_user():
    return {"id": str(uuid.uuid4()), "email": "test@example.com"}


def _auth_override():
    """Override require_auth dependency."""
    user = _fake_user()

    async def _override():
        return user

    return user, _override


# ---------------------------------------------------------------------------
# AC1: POST /buscar response schema contract
# ---------------------------------------------------------------------------

class TestBuscarResponseContract:
    """Verify POST /buscar response conforms to BuscaResponse schema."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(15)
    @patch("config.ASYNC_SEARCH_DEFAULT", False)
    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_and_increment_quota_atomic", return_value=(True, 1, 99))
    @patch("quota.check_quota")
    @patch("routes.search.PNCPClient")
    async def test_buscar_200_response_has_required_fields(
        self, mock_pncp, mock_check_quota, mock_increment, mock_rl, *_
    ):
        """AC1: POST /buscar 200 response must contain required BuscaResponse fields."""
        from schemas import BuscaResponse

        # Setup mocks
        mock_rl.check_rate_limit = AsyncMock(return_value=(True, 0))
        mock_check_quota.return_value = MagicMock(
            allowed=True,
            quota_used=0,
            quota_remaining=100,
            error_message=None,
            capabilities={"max_requests_per_month": 100},
        )
        mock_instance = MagicMock()
        mock_instance.buscar_licitacoes = AsyncMock(return_value=[])
        mock_pncp.return_value = mock_instance

        app = _make_app()
        user, override = _auth_override()
        from auth import require_auth
        app.dependency_overrides[require_auth] = override

        # Patch pipeline to return minimal valid response
        from llm import gerar_resumo_fallback
        _resumo = gerar_resumo_fallback([])
        minimal_response = BuscaResponse(
            licitacoes=[],
            resumo=_resumo,
            excel_available=False,
            quota_used=1,
            quota_remaining=99,
            total_raw=0,
            total_filtrado=0,
        )

        with patch("search_pipeline.SearchPipeline.run", new_callable=AsyncMock, return_value=minimal_response):
            with patch("search_state_manager.create_state_machine", new_callable=AsyncMock) as mock_sm:
                mock_sm.return_value = MagicMock()
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    resp = await client.post(
                        "/v1/buscar",
                        json={
                            "setor_id": "tecnologia",
                            "ufs": ["SP"],
                            "data_inicial": "2026-03-01",
                            "data_final": "2026-03-10",
                        },
                        headers={"x-sync": "true"},
                    )

        assert resp.status_code == 200
        data = resp.json()

        # Contract: required top-level fields
        required_fields = [
            "licitacoes", "resumo", "excel_available",
            "quota_used", "quota_remaining",
            "total_raw", "total_filtrado",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Contract: licitacoes must be a list
        assert isinstance(data["licitacoes"], list)

        # Contract: resumo must have expected structure
        resumo = data["resumo"]
        assert "total_oportunidades" in resumo
        assert "valor_total" in resumo

    @pytest.mark.asyncio
    @pytest.mark.timeout(15)
    @patch("config.ASYNC_SEARCH_DEFAULT", True)
    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_and_increment_quota_atomic", return_value=(True, 1, 99))
    @patch("quota.check_quota")
    @patch("routes.search.PNCPClient")
    async def test_buscar_202_async_response_contract(
        self, mock_pncp, mock_check_quota, mock_increment, mock_rl, *_
    ):
        """AC1: POST /buscar 202 async response must contain search_id and status_url."""
        mock_rl.check_rate_limit = AsyncMock(return_value=(True, 0))
        mock_check_quota.return_value = MagicMock(
            allowed=True,
            quota_used=0,
            quota_remaining=100,
            error_message=None,
            capabilities={"max_requests_per_month": 100},
        )

        app = _make_app()
        user, override = _auth_override()
        from auth import require_auth
        app.dependency_overrides[require_auth] = override

        with patch("search_state_manager.create_state_machine", new_callable=AsyncMock) as mock_sm:
            mock_sm.return_value = MagicMock()
            with patch("job_queue.acquire_search_slot", new_callable=AsyncMock, return_value=True):
                with patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=False):
                    with patch("routes.search_state._run_async_search", new_callable=AsyncMock):
                        with patch("authorization.check_user_roles", new_callable=AsyncMock, return_value=(True, False)):
                            async with AsyncClient(
                                transport=ASGITransport(app=app),
                                base_url="http://test",
                            ) as client:
                                resp = await client.post(
                                    "/v1/buscar",
                                    json={
                                        "setor_id": "tecnologia",
                                        "ufs": ["SP"],
                                        "data_inicial": "2026-03-01",
                                        "data_final": "2026-03-10",
                                    },
                                )

        assert resp.status_code == 202
        data = resp.json()

        # Contract: 202 response required fields
        assert "search_id" in data
        assert "status" in data
        assert data["status"] == "queued"
        assert "status_url" in data
        assert "results_url" in data
        assert "progress_url" in data
        assert "estimated_duration_s" in data


# ---------------------------------------------------------------------------
# AC2: SSE event format contract
# ---------------------------------------------------------------------------

class TestSSEEventFormatContract:
    """Verify SSE events from /buscar-progress/{id} conform to expected format."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_sse_event_has_data_field(self):
        """AC2: Every SSE event must have 'data:' prefix and valid JSON payload."""
        from progress import create_tracker, remove_tracker

        search_id = str(uuid.uuid4())
        tracker = await create_tracker(search_id, 3)

        # Emit a few events
        await tracker.emit("connecting", 5, "Iniciando...")
        await tracker.emit("fetching", 30, "Buscando SP...")
        await tracker.emit_complete()

        # Drain the queue and verify event format
        events_collected = []
        while not tracker.queue.empty():
            event = tracker.queue.get_nowait()
            event_dict = event.to_dict()
            events_collected.append(event_dict)

            # Contract: every event must have these fields
            assert "stage" in event_dict, f"Missing 'stage' in event: {event_dict}"
            assert "progress" in event_dict, f"Missing 'progress' in event: {event_dict}"
            assert "message" in event_dict, f"Missing 'message' in event: {event_dict}"

            # Contract: stage must be a known value
            valid_stages = {
                "connecting", "fetching", "filtering", "llm", "excel",
                "complete", "degraded", "error", "partial_results",
                "refresh_available", "search_complete",
            }
            assert event_dict["stage"] in valid_stages, (
                f"Unknown stage '{event_dict['stage']}' not in {valid_stages}"
            )

            # Contract: progress must be an integer
            assert isinstance(event_dict["progress"], int)

            # Contract: event must be JSON-serializable
            json.dumps(event_dict)  # Will raise if not serializable

        assert len(events_collected) >= 2, "Expected at least 2 events"
        await remove_tracker(search_id)

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_sse_terminal_events_have_correct_stage(self):
        """AC2: Terminal SSE events must use 'complete', 'error', or 'degraded'."""
        from progress import create_tracker, remove_tracker

        search_id = str(uuid.uuid4())
        tracker = await create_tracker(search_id, 1)

        # Test complete terminal event
        await tracker.emit_complete()

        event = tracker.queue.get_nowait()
        assert event.to_dict()["stage"] == "complete"
        assert event.to_dict()["progress"] == 100

        await remove_tracker(search_id)

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_sse_error_event_format(self):
        """AC2: Error SSE events must have stage='error' and descriptive message."""
        from progress import create_tracker, remove_tracker

        search_id = str(uuid.uuid4())
        tracker = await create_tracker(search_id, 1)

        await tracker.emit_error("Test error message")

        event = tracker.queue.get_nowait()
        event_dict = event.to_dict()
        assert event_dict["stage"] == "error"
        assert "Test error message" in event_dict["message"]

        await remove_tracker(search_id)


# ---------------------------------------------------------------------------
# AC3: POST /v1/search/{id}/retry contract
# ---------------------------------------------------------------------------

class TestRetryEndpointContract:
    """Verify POST /search/{id}/retry response schema."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_retry_response_has_required_fields(self):
        """AC3: Retry response must contain search_id, retry_ufs, preserved_ufs, status."""
        app = _make_app()
        user, override = _auth_override()
        from auth import require_auth
        app.dependency_overrides[require_auth] = override

        search_id = str(uuid.uuid4())

        mock_result = MagicMock()
        mock_result.data = {
            "failed_ufs": ["RJ", "MG"],
            "ufs": ["SP", "RJ", "MG"],
            "status": "failed",
        }

        with patch("supabase_client.sb_execute", new_callable=AsyncMock, return_value=mock_result):
            with patch("database.get_db") as mock_db:
                mock_table = MagicMock()
                mock_db.return_value = mock_table
                mock_table.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value = "query"

                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    resp = await client.post(f"/v1/search/{search_id}/retry")

        assert resp.status_code == 200
        data = resp.json()

        # Contract: required fields
        assert "search_id" in data
        assert "retry_ufs" in data
        assert "preserved_ufs" in data
        assert "status" in data
        assert data["search_id"] == search_id
        assert isinstance(data["retry_ufs"], list)
        assert isinstance(data["preserved_ufs"], list)
        assert data["status"] in ("retry_available", "no_retry_needed")

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_retry_404_when_not_found(self):
        """AC3: Retry returns 404 when search session not found."""
        app = _make_app()
        user, override = _auth_override()
        from auth import require_auth
        app.dependency_overrides[require_auth] = override

        search_id = str(uuid.uuid4())

        with patch("supabase_client.sb_execute", new_callable=AsyncMock, side_effect=Exception("not found")):
            with patch("database.get_db") as mock_db:
                mock_db.return_value = MagicMock()

                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    resp = await client.post(f"/v1/search/{search_id}/retry")

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# AC4: GET /v1/search/{id}/status contract
# ---------------------------------------------------------------------------

class TestStatusEndpointContract:
    """Verify GET /search/{id}/status response schema."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_status_response_has_required_fields(self):
        """AC4: Status response must conform to SearchStatusResponse schema."""
        app = _make_app()
        user, override = _auth_override()
        from auth import require_auth
        app.dependency_overrides[require_auth] = override

        search_id = str(uuid.uuid4())

        # Mock DB-based status (slow path)
        mock_status = {
            "status": "completed",
            "progress": 100,
            "elapsed_ms": 5000,
            "started_at": "2026-01-01T00:00:00Z",
        }

        with patch("routes.search_status._verify_search_ownership", new_callable=AsyncMock):
            with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=None):
                with patch("routes.search_status.get_state_machine", return_value=None):
                    with patch("routes.search_status.get_search_status", new_callable=AsyncMock, return_value=mock_status):
                        with patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=None):
                            async with AsyncClient(
                                transport=ASGITransport(app=app),
                                base_url="http://test",
                            ) as client:
                                resp = await client.get(f"/v1/search/{search_id}/status")

        assert resp.status_code == 200
        data = resp.json()

        # Contract: SearchStatusResponse required fields
        required_fields = [
            "search_id", "status", "progress_pct",
            "ufs_completed", "ufs_pending",
            "results_count", "elapsed_s",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        assert data["search_id"] == search_id
        assert data["status"] in ("running", "completed", "failed", "timeout")
        assert isinstance(data["progress_pct"], (int, float))
        assert isinstance(data["ufs_completed"], list)
        assert isinstance(data["ufs_pending"], list)

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_status_404_when_not_found(self):
        """AC4: Status returns 404 when search not found."""
        app = _make_app()
        user, override = _auth_override()
        from auth import require_auth
        app.dependency_overrides[require_auth] = override

        search_id = str(uuid.uuid4())

        with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=None):
            with patch("routes.search_status.get_state_machine", return_value=None):
                with patch("routes.search_status.get_search_status", new_callable=AsyncMock, return_value=None):
                    async with AsyncClient(
                        transport=ASGITransport(app=app),
                        base_url="http://test",
                    ) as client:
                        resp = await client.get(f"/v1/search/{search_id}/status")

        assert resp.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_status_with_excel_info(self):
        """AC4: Status response includes Excel status when available."""
        app = _make_app()
        user, override = _auth_override()
        from auth import require_auth
        app.dependency_overrides[require_auth] = override

        search_id = str(uuid.uuid4())

        mock_status = {
            "status": "completed",
            "progress": 100,
            "elapsed_ms": 3000,
            "started_at": "2026-01-01T00:00:00Z",
        }
        mock_excel = {
            "download_url": "https://example.com/excel.xlsx",
            "excel_status": "ready",
        }

        with patch("routes.search_status._verify_search_ownership", new_callable=AsyncMock):
            with patch("routes.search_status.get_tracker", new_callable=AsyncMock, return_value=None):
                with patch("routes.search_status.get_state_machine", return_value=None):
                    with patch("routes.search_status.get_search_status", new_callable=AsyncMock, return_value=mock_status):
                        with patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=mock_excel):
                            async with AsyncClient(
                                transport=ASGITransport(app=app),
                                base_url="http://test",
                            ) as client:
                                resp = await client.get(f"/v1/search/{search_id}/status")

        assert resp.status_code == 200
        data = resp.json()
        assert data.get("excel_url") == "https://example.com/excel.xlsx"
        assert data.get("excel_status") == "ready"


# ---------------------------------------------------------------------------
# AC10: Backward compatibility — imports from routes.search still work
# ---------------------------------------------------------------------------

class TestBackwardCompatImports:
    """Verify that all re-exports from routes.search work after decomposition."""

    def test_can_import_sse_constants(self):
        """AC10: SSE constants importable from routes.search."""
        from routes.search import _SSE_HEARTBEAT_INTERVAL, _SSE_POLL_INTERVAL
        assert isinstance(_SSE_HEARTBEAT_INTERVAL, float)
        assert isinstance(_SSE_POLL_INTERVAL, float)

    def test_can_import_background_results_functions(self):
        """AC10: Background results functions importable from routes.search."""
        from routes.search import (
            store_background_results,
            get_background_results,
        )
        assert callable(store_background_results)
        assert callable(get_background_results)

    def test_can_import_persistence_functions(self):
        """AC10: Persistence functions importable from routes.search."""
        from routes.search import (
            _persist_results_to_redis,
        )
        assert callable(_persist_results_to_redis)

    def test_can_import_async_search_functions(self):
        """AC10: Async search functions importable from routes.search.

        AC9: _ASYNC_SEARCH_TIMEOUT raised from 120s to 240s to accommodate
        tamanhoPagina=50 per-UF latency.
        """
        from routes.search import (
            _ASYNC_SEARCH_TIMEOUT,
        )
        assert _ASYNC_SEARCH_TIMEOUT == 240

    def test_can_import_status_endpoints(self):
        """AC10: Status endpoint functions importable from routes.search."""
        from routes.search import (
            search_status_endpoint,
        )
        assert callable(search_status_endpoint)

    def test_can_import_module_state(self):
        """AC10: Module-level state importable from routes.search."""
        from routes.search import (
            _background_results,
            _active_background_tasks,
        )
        assert isinstance(_background_results, dict)
        assert isinstance(_active_background_tasks, dict)

    def test_search_pipeline_reexports(self):
        """AC10: SearchPipeline helper re-exports still work."""
        from routes.search import (
            _build_pncp_link,
        )
        assert callable(_build_pncp_link)

    def test_get_correlation_id(self):
        """AC10: get_correlation_id still importable from routes.search."""
        from routes.search import get_correlation_id
        result = get_correlation_id()
        assert result is None or isinstance(result, str)
