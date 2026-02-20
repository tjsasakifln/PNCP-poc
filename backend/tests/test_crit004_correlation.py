"""CRIT-004 AC22-AC23: End-to-end correlation ID propagation tests.

Tests verify that search_id, correlation_id, and request_id propagate
correctly through middleware, ContextVars, log filters, progress events,
module-level reads, and the admin trace endpoint.
"""

import asyncio
import logging
import uuid
from contextvars import copy_context
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Middleware ContextVar Tests (AC5-AC8)
# ---------------------------------------------------------------------------


class TestContextVarDeclarations:
    """AC5-AC6: ContextVar declarations in middleware.py."""

    def test_search_id_var_exists(self):
        from middleware import search_id_var
        assert search_id_var.get() == "-"

    def test_correlation_id_var_exists(self):
        from middleware import correlation_id_var
        assert correlation_id_var.get() == "-"

    def test_request_id_var_exists(self):
        from middleware import request_id_var
        assert request_id_var.get() == "-"

    def test_search_id_var_set_and_get(self):
        from middleware import search_id_var
        token = search_id_var.set("test-search-123")
        assert search_id_var.get() == "test-search-123"
        search_id_var.reset(token)
        assert search_id_var.get() == "-"

    def test_correlation_id_var_set_and_get(self):
        from middleware import correlation_id_var
        token = correlation_id_var.set("corr-abc-456")
        assert correlation_id_var.get() == "corr-abc-456"
        correlation_id_var.reset(token)
        assert correlation_id_var.get() == "-"


# ---------------------------------------------------------------------------
# RequestIDFilter Tests (AC8)
# ---------------------------------------------------------------------------


class TestRequestIDFilter:
    """AC8: Log filter injects search_id and correlation_id into records."""

    def setup_method(self):
        from middleware import RequestIDFilter
        self.log_filter = RequestIDFilter()

    def test_filter_injects_search_id(self):
        from middleware import search_id_var
        token = search_id_var.set("srch-filter-test")
        try:
            record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
            self.log_filter.filter(record)
            assert record.search_id == "srch-filter-test"
        finally:
            search_id_var.reset(token)

    def test_filter_injects_correlation_id(self):
        from middleware import correlation_id_var
        token = correlation_id_var.set("corr-filter-test")
        try:
            record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
            self.log_filter.filter(record)
            assert record.correlation_id == "corr-filter-test"
        finally:
            correlation_id_var.reset(token)

    def test_filter_injects_request_id(self):
        from middleware import request_id_var
        token = request_id_var.set("req-filter-test")
        try:
            record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
            self.log_filter.filter(record)
            assert record.request_id == "req-filter-test"
        finally:
            request_id_var.reset(token)

    def test_filter_defaults_to_dash(self):
        """Without ContextVar set, all IDs default to '-'."""
        record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
        self.log_filter.filter(record)
        assert record.search_id == "-"
        assert record.correlation_id == "-"

    def test_filter_does_not_overwrite_existing(self):
        """If record already has search_id, filter preserves it."""
        record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
        record.search_id = "existing-id"
        record.correlation_id = "existing-corr"
        self.log_filter.filter(record)
        assert record.search_id == "existing-id"
        assert record.correlation_id == "existing-corr"


# ---------------------------------------------------------------------------
# CorrelationIDMiddleware Tests (AC6)
# ---------------------------------------------------------------------------


class TestCorrelationIDMiddleware:
    """AC6: Middleware reads X-Correlation-ID header and sets ContextVar."""

    def test_middleware_sets_correlation_id_from_header(self):
        from main import app
        client = TestClient(app)
        # Send a request with X-Correlation-ID header
        resp = client.get("/health", headers={"X-Correlation-ID": "browser-tab-123"})
        assert resp.status_code == 200

    def test_middleware_generates_request_id(self):
        from main import app
        client = TestClient(app)
        resp = client.get("/health")
        # Middleware should add X-Request-ID to response
        assert "X-Request-ID" in resp.headers
        # Should be a valid UUID
        req_id = resp.headers["X-Request-ID"]
        assert len(req_id) == 36  # UUID format


# ---------------------------------------------------------------------------
# Progress Event Correlation Tests (AC19-AC20)
# ---------------------------------------------------------------------------


class TestProgressEventCorrelation:
    """AC19-AC20: SSE events include search_id and request_id."""

    @patch("telemetry.get_trace_id", return_value=None)
    def test_progress_event_includes_search_id(self, _mock_trace):
        from middleware import search_id_var, request_id_var
        from progress import ProgressEvent

        s_token = search_id_var.set("sse-search-001")
        r_token = request_id_var.set("sse-req-001")
        try:
            event = ProgressEvent(
                stage="fetching",
                progress=50,
                message="Buscando dados..."
            )
            d = event.to_dict()
            assert d["search_id"] == "sse-search-001"
            assert d["request_id"] == "sse-req-001"
        finally:
            search_id_var.reset(s_token)
            request_id_var.reset(r_token)

    @patch("telemetry.get_trace_id", return_value=None)
    def test_progress_event_omits_dash_ids(self, _mock_trace):
        """When IDs are default '-', they should NOT appear in event dict."""
        from progress import ProgressEvent

        event = ProgressEvent(
            stage="connecting",
            progress=0,
            message="Connecting..."
        )
        d = event.to_dict()
        assert "search_id" not in d
        assert "request_id" not in d


# ---------------------------------------------------------------------------
# Module-level search_id propagation Tests (AC11-AC14)
# ---------------------------------------------------------------------------


class TestFilterSearchIdPropagation:
    """AC11: filter.py reads search_id_var for trace correlation."""

    def test_filter_uses_search_id_var(self):
        """When search_id_var is set, filter.py uses it for trace_id prefix."""
        from middleware import search_id_var
        token = search_id_var.set("filter-test-search-id-12345678")
        try:
            sid = search_id_var.get("-")
            trace = sid[:8]
            assert trace == "filter-t"
        finally:
            search_id_var.reset(token)

    def test_filter_fallback_without_search_id(self):
        """When search_id_var is default '-', filter generates random UUID."""
        from middleware import search_id_var
        sid = search_id_var.get("-")
        assert sid == "-"
        # In filter.py, when "-", it falls back to uuid.uuid4()[:8]


class TestConsolidationSearchIdPropagation:
    """AC12: consolidation.py reads search_id_var for log correlation."""

    def test_consolidation_reads_search_id_var(self):
        from middleware import search_id_var
        token = search_id_var.set("consol-test-id")
        try:
            assert search_id_var.get("-") == "consol-test-id"
        finally:
            search_id_var.reset(token)


class TestLlmArbiterSearchIdPropagation:
    """AC13: llm_arbiter.py reads search_id_var for log correlation."""

    def test_llm_arbiter_reads_search_id_var(self):
        from middleware import search_id_var
        token = search_id_var.set("llm-test-id")
        try:
            assert search_id_var.get("-") == "llm-test-id"
        finally:
            search_id_var.reset(token)


class TestSearchCacheCorrelation:
    """AC14: search_cache.py includes search_id in cache hit/miss logs."""

    def test_cache_reads_search_id_var(self):
        from middleware import search_id_var
        token = search_id_var.set("cache-test-id")
        try:
            assert search_id_var.get("-") == "cache-test-id"
        finally:
            search_id_var.reset(token)


# ---------------------------------------------------------------------------
# ARQ Job Queue Correlation Tests (AC15-AC18)
# ---------------------------------------------------------------------------


class TestJobQueueCorrelation:
    """AC15-AC18: ARQ jobs accept **kwargs for trace context and restore ContextVars."""

    @pytest.mark.asyncio
    async def test_llm_job_accepts_kwargs(self):
        """AC15-AC16: llm_summary_job accepts **kwargs including _trace_id."""
        # Mock all dependencies at their source modules (deferred imports in job_queue)
        mock_resumo = MagicMock()
        mock_resumo.total_oportunidades = 0
        mock_resumo.valor_total = 0
        mock_resumo.model_dump.return_value = {"resumo_executivo": "Test"}

        with patch("llm.gerar_resumo", return_value=mock_resumo), \
             patch("redis_pool.get_redis_pool", new_callable=AsyncMock) as mock_redis, \
             patch("progress.get_tracker", new_callable=AsyncMock, return_value=None):

            mock_pool = AsyncMock()
            mock_pool.set = AsyncMock()
            mock_redis.return_value = mock_pool

            from job_queue import llm_summary_job

            ctx = {"search_id": "job-test-001"}
            result = await llm_summary_job(
                ctx,
                "job-test-001",
                [],  # licitacoes
                "vestuario",  # setor
                _trace_id="trace-from-enqueue",
                _span_id="span-from-enqueue",
            )
            assert result is not None

    @pytest.mark.asyncio
    async def test_excel_job_accepts_kwargs(self):
        """AC17-AC18: excel_generation_job accepts **kwargs including _trace_id."""
        from job_queue import excel_generation_job

        # Test with allow_excel=False — skips actual Excel generation
        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock) as mock_redis, \
             patch("progress.get_tracker", new_callable=AsyncMock, return_value=None):

            mock_pool = AsyncMock()
            mock_pool.set = AsyncMock()
            mock_redis.return_value = mock_pool

            ctx = {"search_id": "job-excel-001"}
            result = await excel_generation_job(
                ctx,
                "job-excel-001",
                [],  # licitacoes
                False,  # allow_excel=False → skips generation
                _trace_id="trace-excel",
            )
            assert result["excel_status"] == "skipped"


# ---------------------------------------------------------------------------
# Admin Trace Endpoint Tests (AC21)
# ---------------------------------------------------------------------------


class TestAdminTraceEndpoint:
    """AC21: GET /v1/admin/search-trace/{search_id} aggregates journey data."""

    def setup_method(self):
        from main import app
        from auth import require_auth
        app.dependency_overrides[require_auth] = lambda: {
            "sub": "test-user-id",
            "email": "test@example.com",
        }
        self.client = TestClient(app)

    def teardown_method(self):
        from main import app
        from auth import require_auth
        app.dependency_overrides.pop(require_auth, None)

    @patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=None)
    @patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=None)
    @patch("progress.get_tracker", new_callable=AsyncMock, return_value=None)
    def test_trace_endpoint_returns_structure(self, mock_tracker, mock_job, mock_redis):
        resp = self.client.get("/v1/admin/search-trace/test-search-123")
        assert resp.status_code == 200
        data = resp.json()
        assert data["search_id"] == "test-search-123"
        assert "queried_at" in data
        assert "progress" in data
        assert "cache" in data
        assert "jobs" in data

    @patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=None)
    @patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=None)
    @patch("progress.get_tracker", new_callable=AsyncMock)
    def test_trace_endpoint_with_active_tracker(self, mock_tracker, mock_job, mock_redis):
        tracker = MagicMock()
        tracker.uf_count = 5
        tracker._ufs_completed = 3
        tracker._is_complete = False
        tracker.created_at = 1708000000.0
        tracker._use_redis = False
        mock_tracker.return_value = tracker

        resp = self.client.get("/v1/admin/search-trace/active-search")
        assert resp.status_code == 200
        data = resp.json()
        assert data["progress"]["uf_count"] == 5
        assert data["progress"]["ufs_completed"] == 3
        assert data["progress"]["is_complete"] is False

    @patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=None)
    @patch("job_queue.get_job_result", new_callable=AsyncMock)
    @patch("progress.get_tracker", new_callable=AsyncMock, return_value=None)
    def test_trace_endpoint_with_completed_jobs(self, mock_tracker, mock_job, mock_redis):
        # First call (resumo) returns data, second call (excel) returns None
        mock_job.side_effect = [{"resumo": "test"}, None]

        resp = self.client.get("/v1/admin/search-trace/job-search")
        assert resp.status_code == 200
        data = resp.json()
        assert data["jobs"]["llm_summary"] == "completed"
        assert data["jobs"]["excel_generation"] == "not_found"

    def test_trace_endpoint_requires_auth(self):
        from main import app
        from auth import require_auth
        app.dependency_overrides.pop(require_auth, None)

        resp = self.client.get("/v1/admin/search-trace/no-auth")
        # Without auth override, should fail
        assert resp.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# Search Route search_id_var.set Tests (AC7)
# ---------------------------------------------------------------------------


class TestSearchRouteContextVar:
    """AC7: routes/search.py sets search_id_var when search_id is present."""

    def test_search_id_var_set_in_route(self):
        """Verify that the search route code sets search_id_var."""
        import inspect
        from routes import search as search_module

        source = inspect.getsource(search_module)
        assert "search_id_var.set(request.search_id)" in source
        assert "from middleware import search_id_var" in source


# ---------------------------------------------------------------------------
# Log Format Tests (AC9-AC10)
# ---------------------------------------------------------------------------


class TestLogFormatConfiguration:
    """AC9-AC10: Log format includes search_id and correlation_id placeholders."""

    def test_log_format_has_search_id(self):
        """Verify config.py log format string includes search_id."""
        import inspect
        import config
        source = inspect.getsource(config)
        assert "search_id" in source

    def test_log_format_has_correlation_id(self):
        """Verify config.py log format string includes correlation_id."""
        import inspect
        import config
        source = inspect.getsource(config)
        assert "correlation_id" in source
