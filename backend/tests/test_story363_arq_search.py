"""STORY-363: Decouple Search Pipeline from HTTP Request via ARQ Worker.

Tests AC15-AC18:
- AC15: POST /buscar returns 202 with search_id in <3s
- AC16: Worker processes job and persists results (L2 Redis + L3 Supabase)
- AC17: SSE reconnect after disconnect receives current state
- AC18: Pipeline completes even if frontend disconnects

Also tests:
- AC2: ARQ Worker dispatch with fallback to asyncio.create_task
- AC13: Worker validates user_id
- AC14: Per-user concurrent search rate limiting
"""

import asyncio
import json
import time
import uuid
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_user():
    """Authenticated user dict."""
    return {"id": "user-363-001", "email": "story363@test.com", "role": "authenticated"}


@pytest.fixture
def mock_request_data():
    """Serializable BuscaRequest data for search_job."""
    return {
        "ufs": ["SP", "RJ"],
        "data_inicial": "2026-02-01",
        "data_final": "2026-02-10",
        "setor_id": "vestuario",
        "termos_busca": None,
        "search_id": "test-363-search",
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
    resp.resumo = MagicMock()
    resp.resumo.total_oportunidades = 42
    resp.model_dump.return_value = {
        "total_filtrado": 42,
        "total_raw": 100,
        "licitacoes": [],
        "resumo": {"total_oportunidades": 42},
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
    """Create a mock state machine."""
    sm = Mock()
    sm.fail = AsyncMock()
    sm.transition = AsyncMock()
    sm.complete = AsyncMock()
    return sm


VALID_SEARCH_BODY = {
    "ufs": ["SP", "RJ"],
    "data_inicial": "2026-02-14",
    "data_final": "2026-02-24",
    "setor_id": "vestuario",
    "search_id": str(uuid.uuid4()),
}


# ============================================================================
# AC15: POST /buscar returns 202 with search_id in <3s
# ============================================================================

class TestAC15PostReturns202:
    """AC15: POST /buscar returns 202 with search_id when async + ARQ available."""

    def test_arq_dispatch_returns_202(self):
        """AC15: POST returns 202 when ARQ worker is available."""
        from fastapi.testclient import TestClient
        from main import app
        from auth import require_auth

        mock_user = {"id": "user-363-015", "email": "ac15@test.com"}
        app.dependency_overrides[require_auth] = lambda: mock_user

        mock_job = MagicMock()
        mock_job.job_id = "arq-job-015"

        try:
            with patch("config.get_feature_flag", return_value=True), \
                 patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)), \
                 patch("routes.search.create_tracker", new_callable=AsyncMock, return_value=_make_mock_tracker()), \
                 patch("routes.search.create_state_machine", new_callable=AsyncMock, return_value=_make_mock_state_machine()), \
                 patch("quota.require_active_plan", new_callable=AsyncMock), \
                 patch("quota.check_quota", return_value=MagicMock(allowed=True, error_message="", capabilities={"max_requests_per_month": 1000})), \
                 patch("quota.check_and_increment_quota_atomic", return_value=(True, 1, 999)), \
                 patch("job_queue.acquire_search_slot", new_callable=AsyncMock, return_value=True), \
                 patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=True), \
                 patch("job_queue.enqueue_job", new_callable=AsyncMock, return_value=mock_job):

                client = TestClient(app, raise_server_exceptions=False)
                start = time.time()
                response = client.post("/v1/buscar", json=VALID_SEARCH_BODY)
                elapsed = time.time() - start

            assert response.status_code == 202
            data = response.json()
            assert data["status"] == "queued"
            assert "search_id" in data
            assert "status_url" in data
            assert "progress_url" in data
            assert elapsed < 3.0, f"POST took {elapsed:.1f}s, must be <3s"
        finally:
            app.dependency_overrides.pop(require_auth, None)

    def test_arq_unavailable_falls_back_to_create_task(self):
        """AC15: When ARQ unavailable, falls back to asyncio.create_task and still returns 202."""
        from fastapi.testclient import TestClient
        from main import app
        from auth import require_auth

        mock_user = {"id": "user-363-fb", "email": "fallback@test.com"}
        app.dependency_overrides[require_auth] = lambda: mock_user

        try:
            with patch("config.get_feature_flag", return_value=True), \
                 patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)), \
                 patch("routes.search.create_tracker", new_callable=AsyncMock, return_value=_make_mock_tracker()), \
                 patch("routes.search.create_state_machine", new_callable=AsyncMock, return_value=_make_mock_state_machine()), \
                 patch("quota.require_active_plan", new_callable=AsyncMock), \
                 patch("quota.check_quota", return_value=MagicMock(allowed=True, error_message="", capabilities={"max_requests_per_month": 1000})), \
                 patch("quota.check_and_increment_quota_atomic", return_value=(True, 1, 999)), \
                 patch("job_queue.acquire_search_slot", new_callable=AsyncMock, return_value=True), \
                 patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=False), \
                 patch("routes.search._run_async_search", new_callable=AsyncMock):

                client = TestClient(app, raise_server_exceptions=False)
                response = client.post("/v1/buscar", json=VALID_SEARCH_BODY)

            assert response.status_code == 202
            data = response.json()
            assert data["status"] == "queued"
        finally:
            app.dependency_overrides.pop(require_auth, None)


# ============================================================================
# AC16: Worker processes job and persists results
# ============================================================================

class TestAC16WorkerPersistsResults:
    """AC16: search_job processes pipeline and persists to L2 Redis + L3 Supabase."""

    @pytest.mark.asyncio
    async def test_search_job_persists_to_redis_and_supabase(
        self, mock_tracker, mock_busca_response, mock_user
    ):
        """AC16: search_job calls executar_busca_completa and persists to L2+L3."""
        from job_queue import search_job

        with patch("search_pipeline.executar_busca_completa", new_callable=AsyncMock, return_value=mock_busca_response), \
             patch("progress.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("progress.remove_tracker", new_callable=AsyncMock), \
             patch("job_queue.check_cancel_flag", new_callable=AsyncMock, return_value=False), \
             patch("job_queue.clear_cancel_flag", new_callable=AsyncMock), \
             patch("job_queue.persist_job_result", new_callable=AsyncMock) as mock_persist_arq, \
             patch("job_queue._persist_search_results_to_redis", new_callable=AsyncMock) as mock_persist_redis, \
             patch("job_queue._persist_search_results_to_supabase", new_callable=AsyncMock) as mock_persist_supa, \
             patch("job_queue._update_search_session", new_callable=AsyncMock), \
             patch("job_queue.release_search_slot", new_callable=AsyncMock), \
             patch("config.get_feature_flag", return_value=False):

            result = await search_job(
                ctx={},
                search_id="test-363-persist",
                request_data={"ufs": ["SP"], "setor_id": "vestuario"},
                user_data=mock_user,
            )

        assert result["status"] == "completed"
        assert result["total_results"] == 42

        # Verify L2 Redis persistence
        mock_persist_redis.assert_called_once()
        call_args = mock_persist_redis.call_args
        assert call_args[0][0] == "test-363-persist"

        # Verify L3 Supabase persistence
        mock_persist_supa.assert_called_once()

        # Verify ARQ job result persistence
        mock_persist_arq.assert_called_once()

        # Verify SSE terminal event
        mock_tracker.emit_search_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_job_emits_error_on_failure(self, mock_tracker, mock_user):
        """AC16: search_job emits error SSE event on pipeline failure."""
        from job_queue import search_job

        with patch("search_pipeline.executar_busca_completa", new_callable=AsyncMock, side_effect=RuntimeError("Pipeline boom")), \
             patch("progress.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("progress.remove_tracker", new_callable=AsyncMock), \
             patch("job_queue.check_cancel_flag", new_callable=AsyncMock, return_value=False), \
             patch("job_queue.clear_cancel_flag", new_callable=AsyncMock), \
             patch("job_queue.release_search_slot", new_callable=AsyncMock):

            with pytest.raises(RuntimeError, match="Pipeline boom"):
                await search_job(
                    ctx={},
                    search_id="test-363-fail",
                    request_data={"ufs": ["SP"], "setor_id": "vestuario"},
                    user_data=mock_user,
                )

        mock_tracker.emit_error.assert_called_once()


# ============================================================================
# AC13: Worker validates user_id
# ============================================================================

class TestAC13WorkerValidatesUser:
    """AC13: search_job validates user_id before processing."""

    @pytest.mark.asyncio
    async def test_search_job_rejects_missing_user_id(self):
        """AC13: search_job returns failed when user_id is missing."""
        from job_queue import search_job

        with patch("job_queue.release_search_slot", new_callable=AsyncMock), \
             patch("job_queue.clear_cancel_flag", new_callable=AsyncMock), \
             patch("progress.get_tracker", new_callable=AsyncMock, return_value=None):

            result = await search_job(
                ctx={},
                search_id="test-363-nouser",
                request_data={"ufs": ["SP"]},
                user_data={},  # No id
            )

        assert result["status"] == "failed"
        assert result["error"] == "invalid_user"


# ============================================================================
# AC14: Per-user concurrent search rate limiting
# ============================================================================

class TestAC14ConcurrentSearchLimiting:
    """AC14: Per-user concurrent search rate limiting (max 3)."""

    @pytest.mark.asyncio
    async def test_acquire_slot_succeeds_within_limit(self):
        """AC14: acquire_search_slot succeeds when under limit."""
        from job_queue import acquire_search_slot

        mock_redis = AsyncMock()
        mock_redis.zremrangebyscore = AsyncMock()
        mock_redis.zcard = AsyncMock(return_value=1)
        mock_redis.zadd = AsyncMock()
        mock_redis.expire = AsyncMock()

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("config.MAX_CONCURRENT_SEARCHES", 3):
            result = await acquire_search_slot("user-001", "search-001")

        assert result is True
        mock_redis.zadd.assert_called_once()

    @pytest.mark.asyncio
    async def test_acquire_slot_rejects_at_limit(self):
        """AC14: acquire_search_slot rejects when at limit."""
        from job_queue import acquire_search_slot

        mock_redis = AsyncMock()
        mock_redis.zremrangebyscore = AsyncMock()
        mock_redis.zcard = AsyncMock(return_value=3)  # At limit

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("config.MAX_CONCURRENT_SEARCHES", 3):
            result = await acquire_search_slot("user-001", "search-004")

        assert result is False
        mock_redis.zadd.assert_not_called()

    @pytest.mark.asyncio
    async def test_acquire_slot_allows_when_redis_unavailable(self):
        """AC14: acquire_search_slot allows through (fail-open) when Redis is down."""
        from job_queue import acquire_search_slot

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=None):
            result = await acquire_search_slot("user-001", "search-001")

        assert result is True

    @pytest.mark.asyncio
    async def test_release_slot_removes_from_set(self):
        """AC14: release_search_slot removes search_id from sorted set."""
        from job_queue import release_search_slot

        mock_redis = AsyncMock()
        mock_redis.zrem = AsyncMock()

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            await release_search_slot("user-001", "search-001")

        mock_redis.zrem.assert_called_once()

    def test_post_returns_429_when_concurrent_limit_exceeded(self):
        """AC14: POST /buscar returns 429 when user has too many concurrent searches."""
        from fastapi.testclient import TestClient
        from main import app
        from auth import require_auth

        mock_user = {"id": "user-363-rate", "email": "rate@test.com"}
        app.dependency_overrides[require_auth] = lambda: mock_user

        try:
            with patch("config.get_feature_flag", return_value=True), \
                 patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)), \
                 patch("routes.search.create_tracker", new_callable=AsyncMock, return_value=_make_mock_tracker()), \
                 patch("routes.search.create_state_machine", new_callable=AsyncMock, return_value=_make_mock_state_machine()), \
                 patch("quota.require_active_plan", new_callable=AsyncMock), \
                 patch("quota.check_quota", return_value=MagicMock(allowed=True, error_message="", capabilities={"max_requests_per_month": 1000})), \
                 patch("quota.check_and_increment_quota_atomic", return_value=(True, 1, 999)), \
                 patch("job_queue.acquire_search_slot", new_callable=AsyncMock, return_value=False), \
                 patch("routes.search.remove_tracker", new_callable=AsyncMock):

                client = TestClient(app, raise_server_exceptions=False)
                response = client.post("/v1/buscar", json=VALID_SEARCH_BODY)

            assert response.status_code == 429
        finally:
            app.dependency_overrides.pop(require_auth, None)


# ============================================================================
# AC17: SSE reconnect after disconnect receives current state
# ============================================================================

class TestAC17SSEReconnect:
    """AC17: SSE reconnect after disconnect receives current state via Redis."""

    @pytest.mark.asyncio
    async def test_replay_events_returns_events_after_id(self):
        """AC17: get_replay_events returns events after given ID from Redis."""
        from progress import get_replay_events

        mock_redis = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=[
            json.dumps({"id": 1, "data": {"stage": "connecting", "progress": 5}}),
            json.dumps({"id": 2, "data": {"stage": "fetching", "progress": 30}}),
            json.dumps({"id": 3, "data": {"stage": "filtering", "progress": 65}}),
        ])

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("progress._active_trackers", {}):
            events = await get_replay_events("test-search", after_id=1)

        assert len(events) == 2
        assert events[0][0] == 2
        assert events[1][0] == 3

    @pytest.mark.asyncio
    async def test_is_search_terminal_returns_terminal_event(self):
        """AC17: is_search_terminal detects completed searches for instant replay."""
        from progress import is_search_terminal

        mock_redis = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=[
            json.dumps({"id": 5, "data": {"stage": "search_complete", "progress": 100}}),
        ])

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("progress._active_trackers", {}):
            result = await is_search_terminal("test-search")

        assert result is not None
        assert result["stage"] == "search_complete"


# ============================================================================
# AC18: Pipeline completes even if frontend disconnects
# ============================================================================

class TestAC18PipelineCompletesIndependently:
    """AC18: Pipeline completes in ARQ Worker even if frontend disconnects."""

    @pytest.mark.asyncio
    async def test_search_job_completes_without_tracker(
        self, mock_busca_response, mock_user
    ):
        """AC18: search_job completes and persists even when no SSE tracker exists."""
        from job_queue import search_job

        with patch("search_pipeline.executar_busca_completa", new_callable=AsyncMock, return_value=mock_busca_response), \
             patch("progress.get_tracker", new_callable=AsyncMock, return_value=None), \
             patch("progress.remove_tracker", new_callable=AsyncMock), \
             patch("job_queue.check_cancel_flag", new_callable=AsyncMock, return_value=False), \
             patch("job_queue.clear_cancel_flag", new_callable=AsyncMock), \
             patch("job_queue.persist_job_result", new_callable=AsyncMock) as mock_persist, \
             patch("job_queue._persist_search_results_to_redis", new_callable=AsyncMock) as mock_redis, \
             patch("job_queue._persist_search_results_to_supabase", new_callable=AsyncMock) as mock_supa, \
             patch("job_queue._update_search_session", new_callable=AsyncMock), \
             patch("job_queue.release_search_slot", new_callable=AsyncMock), \
             patch("config.get_feature_flag", return_value=False):

            result = await search_job(
                ctx={},
                search_id="test-363-no-tracker",
                request_data={"ufs": ["SP"], "setor_id": "vestuario"},
                user_data=mock_user,
            )

        # Pipeline completed and persisted even without SSE connection
        assert result["status"] == "completed"
        assert result["total_results"] == 42
        mock_persist.assert_called_once()
        mock_redis.assert_called_once()
        mock_supa.assert_called_once()


# ============================================================================
# AC2: ARQ dispatch with fallback
# ============================================================================

class TestAC2ARQDispatchWithFallback:
    """AC2: Pipeline dispatches to ARQ Worker with in-process fallback."""

    def test_enqueue_job_called_when_arq_available(self):
        """AC2: enqueue_job is called when ARQ worker is available."""
        from fastapi.testclient import TestClient
        from main import app
        from auth import require_auth

        mock_user = {"id": "user-363-arq", "email": "arq@test.com"}
        app.dependency_overrides[require_auth] = lambda: mock_user

        mock_job = MagicMock()
        mock_job.job_id = "arq-job-002"

        try:
            with patch("config.get_feature_flag", return_value=True), \
                 patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)), \
                 patch("routes.search.create_tracker", new_callable=AsyncMock, return_value=_make_mock_tracker()), \
                 patch("routes.search.create_state_machine", new_callable=AsyncMock, return_value=_make_mock_state_machine()), \
                 patch("quota.require_active_plan", new_callable=AsyncMock), \
                 patch("quota.check_quota", return_value=MagicMock(allowed=True, error_message="", capabilities={"max_requests_per_month": 1000})), \
                 patch("quota.check_and_increment_quota_atomic", return_value=(True, 1, 999)), \
                 patch("job_queue.acquire_search_slot", new_callable=AsyncMock, return_value=True), \
                 patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=True), \
                 patch("job_queue.enqueue_job", new_callable=AsyncMock, return_value=mock_job) as mock_enqueue:

                client = TestClient(app, raise_server_exceptions=False)
                response = client.post("/v1/buscar", json=VALID_SEARCH_BODY)

            assert response.status_code == 202
            mock_enqueue.assert_called_once()
            # Verify the job function name is "search_job"
            assert mock_enqueue.call_args[0][0] == "search_job"
        finally:
            app.dependency_overrides.pop(require_auth, None)

    def test_fallback_to_create_task_when_arq_returns_none(self):
        """AC2: Falls back to asyncio.create_task when enqueue_job returns None."""
        from fastapi.testclient import TestClient
        from main import app
        from auth import require_auth

        mock_user = {"id": "user-363-fb2", "email": "fb2@test.com"}
        app.dependency_overrides[require_auth] = lambda: mock_user

        try:
            with patch("config.get_feature_flag", return_value=True), \
                 patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)), \
                 patch("routes.search.create_tracker", new_callable=AsyncMock, return_value=_make_mock_tracker()), \
                 patch("routes.search.create_state_machine", new_callable=AsyncMock, return_value=_make_mock_state_machine()), \
                 patch("quota.require_active_plan", new_callable=AsyncMock), \
                 patch("quota.check_quota", return_value=MagicMock(allowed=True, error_message="", capabilities={"max_requests_per_month": 1000})), \
                 patch("quota.check_and_increment_quota_atomic", return_value=(True, 1, 999)), \
                 patch("job_queue.acquire_search_slot", new_callable=AsyncMock, return_value=True), \
                 patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=True), \
                 patch("job_queue.enqueue_job", new_callable=AsyncMock, return_value=None), \
                 patch("routes.search._run_async_search", new_callable=AsyncMock) as mock_run:

                client = TestClient(app, raise_server_exceptions=False)
                response = client.post("/v1/buscar", json=VALID_SEARCH_BODY)

            assert response.status_code == 202
            # Fallback to asyncio.create_task was used
            mock_run.assert_called_once()
        finally:
            app.dependency_overrides.pop(require_auth, None)


# ============================================================================
# AC5: POST never exceeds Railway timeout
# ============================================================================

class TestAC5NeverExceedsTimeout:
    """AC5: POST /buscar never exceeds Railway timeout (~120s)."""

    def test_post_responds_under_3_seconds(self):
        """AC5: POST /buscar responds in <3s regardless of pipeline duration."""
        from fastapi.testclient import TestClient
        from main import app
        from auth import require_auth

        mock_user = {"id": "user-363-timeout", "email": "timeout@test.com"}
        app.dependency_overrides[require_auth] = lambda: mock_user

        mock_job = MagicMock()
        mock_job.job_id = "arq-job-timeout"

        try:
            with patch("config.get_feature_flag", return_value=True), \
                 patch("routes.search.check_user_roles", new_callable=AsyncMock, return_value=(False, False)), \
                 patch("routes.search.create_tracker", new_callable=AsyncMock, return_value=_make_mock_tracker()), \
                 patch("routes.search.create_state_machine", new_callable=AsyncMock, return_value=_make_mock_state_machine()), \
                 patch("quota.require_active_plan", new_callable=AsyncMock), \
                 patch("quota.check_quota", return_value=MagicMock(allowed=True, error_message="", capabilities={"max_requests_per_month": 1000})), \
                 patch("quota.check_and_increment_quota_atomic", return_value=(True, 1, 999)), \
                 patch("job_queue.acquire_search_slot", new_callable=AsyncMock, return_value=True), \
                 patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=True), \
                 patch("job_queue.enqueue_job", new_callable=AsyncMock, return_value=mock_job):

                client = TestClient(app, raise_server_exceptions=False)
                start = time.time()
                body = {**VALID_SEARCH_BODY, "ufs": ["SP", "RJ", "MG", "RS", "PR", "BA", "SC", "GO", "PE", "CE"]}
                response = client.post("/v1/buscar", json=body)
                elapsed = time.time() - start

            assert response.status_code == 202
            assert elapsed < 3.0, f"POST took {elapsed:.1f}s — must be <3s (AC5)"
        finally:
            app.dependency_overrides.pop(require_auth, None)


# ============================================================================
# Worker persistence helpers unit tests
# ============================================================================

class TestWorkerPersistenceHelpers:
    """Unit tests for STORY-363 persistence helpers in job_queue."""

    @pytest.mark.asyncio
    async def test_persist_search_results_to_redis(self, mock_busca_response):
        """L2 Redis persistence uses smartlic:results:{search_id} key format."""
        from job_queue import _persist_search_results_to_redis

        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("config.RESULTS_REDIS_TTL", 14400):
            await _persist_search_results_to_redis("test-search-redis", mock_busca_response)

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "smartlic:results:test-search-redis"
        assert call_args[0][1] == 14400

    @pytest.mark.asyncio
    async def test_persist_search_results_to_redis_graceful_on_failure(self, mock_busca_response):
        """L2 Redis persistence is fire-and-forget — never raises."""
        from job_queue import _persist_search_results_to_redis

        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(side_effect=ConnectionError("Redis down"))

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            # Should not raise
            await _persist_search_results_to_redis("test-search-fail", mock_busca_response)

    @pytest.mark.asyncio
    async def test_persist_search_results_to_supabase(self, mock_busca_response):
        """L3 Supabase persistence stores results with TTL."""
        from job_queue import _persist_search_results_to_supabase

        mock_db = MagicMock()
        mock_table = MagicMock()
        mock_upsert = MagicMock()
        mock_db.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert

        with patch("supabase_client.get_supabase", return_value=mock_db), \
             patch("supabase_client.sb_execute", new_callable=AsyncMock), \
             patch("config.RESULTS_SUPABASE_TTL_HOURS", 24):
            await _persist_search_results_to_supabase("test-search-supa", "user-001", mock_busca_response)

        mock_db.table.assert_called_once_with("search_results_l3")

    @pytest.mark.asyncio
    async def test_persist_search_results_to_supabase_graceful_on_failure(self, mock_busca_response):
        """L3 Supabase persistence is fire-and-forget — never raises."""
        from job_queue import _persist_search_results_to_supabase

        with patch("supabase_client.get_supabase", side_effect=Exception("Supabase down")):
            # Should not raise
            await _persist_search_results_to_supabase("test-fail", "user-001", mock_busca_response)
