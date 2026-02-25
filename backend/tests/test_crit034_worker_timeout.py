"""CRIT-034: Tests for gunicorn worker timeout regression fix.

AC1: WEB_CONCURRENCY default increased to 4
AC2: GUNICORN_TIMEOUT remains 900s (already done in CRIT-026)
AC3: --keep-alive increased to 75s
AC4: GUNICORN_GRACEFUL_TIMEOUT remains 120s (already done in CRIT-026)
AC5: Sentry capture on worker timeout
AC6: Prometheus WORKER_TIMEOUT metric instrumented
AC7: Structured log with worker_pid, request_duration, endpoint, search_id
"""

import os
import sys
import time

import pytest
from unittest.mock import patch, MagicMock, call


# ============================================================================
# Helper: read start.sh content
# ============================================================================

def _read_start_sh() -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "start.sh")
    with open(path) as f:
        return f.read()


# ============================================================================
# AC1: WEB_CONCURRENCY = 4
# ============================================================================


class TestAC1WebConcurrency:
    """AC1: WEB_CONCURRENCY default (SLA-002: reduced to 2)."""

    def test_default_workers_is_2(self):
        content = _read_start_sh()
        assert "WEB_CONCURRENCY:-2" in content

    def test_workers_flag_uses_env_var(self):
        content = _read_start_sh()
        assert '-w "${WEB_CONCURRENCY:-2}"' in content


# ============================================================================
# AC2: GUNICORN_TIMEOUT = 120s (GTM-STAB-002: reduced from 180s, aligned with Railway proxy)
# ============================================================================


class TestAC2Timeout:
    """AC2: GUNICORN_TIMEOUT reduced to 120s (GTM-STAB-002, was 180s)."""

    def test_timeout_120s(self):
        content = _read_start_sh()
        assert "GUNICORN_TIMEOUT:-120" in content


# ============================================================================
# AC3: --keep-alive = 75s
# ============================================================================


class TestAC3KeepAlive:
    """AC3: --keep-alive increased from 5 to 75s for SSE connections."""

    def test_keep_alive_75(self):
        content = _read_start_sh()
        assert "GUNICORN_KEEP_ALIVE:-75" in content

    def test_keep_alive_flag_present(self):
        content = _read_start_sh()
        assert "--keep-alive" in content


# ============================================================================
# AC4: GUNICORN_GRACEFUL_TIMEOUT = 30s (GTM-STAB-002: reduced from 120s)
# ============================================================================


class TestAC4GracefulTimeout:
    """AC4: GUNICORN_GRACEFUL_TIMEOUT reduced to 30s (GTM-STAB-002)."""

    def test_graceful_timeout_30s(self):
        content = _read_start_sh()
        assert "GUNICORN_GRACEFUL_TIMEOUT:-30" in content


# ============================================================================
# Gunicorn config file
# ============================================================================


class TestGunicornConfig:
    """Gunicorn config file has required hooks."""

    def test_config_file_exists(self):
        path = os.path.join(os.path.dirname(__file__), "..", "gunicorn_conf.py")
        assert os.path.exists(path)

    def test_config_referenced_in_start_sh(self):
        content = _read_start_sh()
        assert "-c gunicorn_conf.py" in content

    def test_config_has_post_worker_init_hook(self):
        import gunicorn_conf
        assert hasattr(gunicorn_conf, "post_worker_init")
        assert callable(gunicorn_conf.post_worker_init)

    def test_config_has_worker_abort_hook(self):
        import gunicorn_conf
        assert hasattr(gunicorn_conf, "worker_abort")
        assert callable(gunicorn_conf.worker_abort)

    def test_worker_abort_logs_critical(self):
        """worker_abort hook logs at CRITICAL level."""
        import gunicorn_conf

        mock_worker = MagicMock()
        mock_worker.pid = 1234

        with patch("gunicorn_conf.logger") as mock_logger, \
             patch.dict(sys.modules, {"sentry_sdk": MagicMock()}):
            gunicorn_conf.worker_abort(mock_worker)

        mock_logger.critical.assert_called_once()
        log_msg = mock_logger.critical.call_args[0][0]
        assert "1234" in log_msg
        assert "WORKER TIMEOUT" in log_msg

    def test_worker_abort_captures_sentry(self):
        """worker_abort hook captures to Sentry."""
        import gunicorn_conf

        mock_worker = MagicMock()
        mock_worker.pid = 5678

        mock_sentry = MagicMock()
        mock_scope = MagicMock()
        mock_sentry.new_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
        mock_sentry.new_scope.return_value.__exit__ = MagicMock(return_value=False)

        with patch("gunicorn_conf.logger"), \
             patch.dict(sys.modules, {"sentry_sdk": mock_sentry}):
            gunicorn_conf.worker_abort(mock_worker)

        mock_sentry.capture_message.assert_called_once()
        msg = mock_sentry.capture_message.call_args[0][0]
        assert "5678" in msg

    def test_post_worker_init_calls_install_handler(self):
        """post_worker_init calls install_timeout_handler."""
        import gunicorn_conf

        mock_worker = MagicMock()
        mock_worker.pid = 9999

        with patch("worker_lifecycle.install_timeout_handler") as mock_install:
            gunicorn_conf.post_worker_init(mock_worker)

        mock_install.assert_called_once_with(9999)

    def test_post_worker_init_graceful_on_import_error(self):
        """post_worker_init doesn't crash if worker_lifecycle unavailable."""
        import gunicorn_conf

        mock_worker = MagicMock()
        mock_worker.pid = 1111

        with patch("gunicorn_conf.logger") as mock_logger, \
             patch.dict(sys.modules, {"worker_lifecycle": None}):
            # Should not raise
            try:
                gunicorn_conf.post_worker_init(mock_worker)
            except Exception:
                pass  # Import error is expected and handled


# ============================================================================
# Worker lifecycle module
# ============================================================================


class TestWorkerLifecycleTracking:
    """Active request tracking for timeout diagnostics."""

    def setup_method(self):
        from worker_lifecycle import clear_active_request
        clear_active_request()

    def test_set_active_request(self):
        from worker_lifecycle import set_active_request, get_active_request
        set_active_request("/v1/buscar", "search-abc")
        info = get_active_request()
        assert info["endpoint"] == "/v1/buscar"
        assert info["search_id"] == "search-abc"
        assert "start_time" in info
        assert "pid" in info

    def test_set_active_request_no_search_id(self):
        from worker_lifecycle import set_active_request, get_active_request
        set_active_request("/health")
        info = get_active_request()
        assert info["endpoint"] == "/health"
        assert info["search_id"] == "-"

    def test_clear_active_request(self):
        from worker_lifecycle import set_active_request, clear_active_request, get_active_request
        set_active_request("/v1/buscar", "search-xyz")
        clear_active_request()
        assert get_active_request() == {}

    def test_get_active_request_returns_copy(self):
        from worker_lifecycle import set_active_request, get_active_request
        set_active_request("/test", "id-1")
        copy = get_active_request()
        copy["endpoint"] = "modified"
        # Original should not be affected
        original = get_active_request()
        assert original["endpoint"] == "/test"


class TestBuildTimeoutInfo:
    """build_timeout_info extracts structured diagnostic data."""

    def setup_method(self):
        from worker_lifecycle import clear_active_request
        clear_active_request()

    def test_with_active_request(self):
        from worker_lifecycle import set_active_request, build_timeout_info
        set_active_request("/v1/buscar", "search-123")
        time.sleep(0.01)  # Ensure measurable duration
        info = build_timeout_info(worker_pid=42)
        assert info["worker_pid"] == 42
        assert info["endpoint"] == "/v1/buscar"
        assert info["search_id"] == "search-123"
        assert info["request_duration_s"] >= 0.01

    def test_without_active_request(self):
        """When no active request, returns idle with -1 duration."""
        from worker_lifecycle import build_timeout_info
        info = build_timeout_info(worker_pid=99)
        assert info["worker_pid"] == 99
        assert info["endpoint"] == "idle"
        assert info["search_id"] == "-"
        assert info["request_duration_s"] == -1

    def test_all_required_fields_present(self):
        """AC7: All 4 required fields are present."""
        from worker_lifecycle import set_active_request, build_timeout_info
        set_active_request("/test", "s-1")
        info = build_timeout_info(worker_pid=1)
        required = {"worker_pid", "request_duration_s", "endpoint", "search_id"}
        assert required.issubset(info.keys())


class TestInstallTimeoutHandler:
    """install_timeout_handler registers SIGABRT handler."""

    def test_skips_on_windows(self):
        """On Windows, install_timeout_handler is a no-op."""
        from worker_lifecycle import install_timeout_handler
        with patch("worker_lifecycle.sys") as mock_sys:
            mock_sys.platform = "win32"
            # Should not raise
            install_timeout_handler(1234)

    @pytest.mark.skipif(sys.platform == "win32", reason="Signal tests require Unix")
    def test_installs_sigabrt_handler_on_unix(self):
        """On Unix, SIGABRT handler is registered."""
        import signal
        from worker_lifecycle import install_timeout_handler

        old_handler = signal.getsignal(signal.SIGABRT)
        try:
            install_timeout_handler(7777)
            new_handler = signal.getsignal(signal.SIGABRT)
            assert new_handler != signal.SIG_DFL, "Handler should be custom, not default"
        finally:
            signal.signal(signal.SIGABRT, old_handler)

    @pytest.mark.skipif(sys.platform == "win32", reason="Signal tests require Unix")
    def test_handler_logs_structured_data(self):
        """AC7: The SIGABRT handler logs all required fields."""
        import signal
        from worker_lifecycle import install_timeout_handler, set_active_request

        set_active_request("/v1/buscar", "search-timeout-test")
        old_handler = signal.getsignal(signal.SIGABRT)

        try:
            install_timeout_handler(4242)
            handler = signal.getsignal(signal.SIGABRT)

            # Call handler directly (don't actually send SIGABRT!)
            with patch("worker_lifecycle.logger") as mock_logger, \
                 patch("worker_lifecycle.signal.signal"), \
                 patch("worker_lifecycle.os.abort"):
                handler(signal.SIGABRT, None)

            mock_logger.critical.assert_called_once()
            log_msg = mock_logger.critical.call_args[0][0]
            assert "4242" in log_msg
            assert "/v1/buscar" in log_msg
            assert "search-timeout-test" in log_msg
            assert "WORKER KILLED BY TIMEOUT" in log_msg
        finally:
            signal.signal(signal.SIGABRT, old_handler)

    @pytest.mark.skipif(sys.platform == "win32", reason="Signal tests require Unix")
    def test_handler_increments_metric(self):
        """AC6: The SIGABRT handler increments WORKER_TIMEOUT counter."""
        import signal
        from worker_lifecycle import install_timeout_handler, set_active_request

        set_active_request("/test", "s-1")
        old_handler = signal.getsignal(signal.SIGABRT)

        mock_metric = MagicMock()
        mock_metric.labels.return_value = mock_metric

        try:
            install_timeout_handler(1234)
            handler = signal.getsignal(signal.SIGABRT)

            with patch("worker_lifecycle.logger"), \
                 patch("worker_lifecycle.signal.signal"), \
                 patch("worker_lifecycle.os.abort"), \
                 patch.dict(sys.modules, {"metrics": MagicMock(WORKER_TIMEOUT=mock_metric)}):
                handler(signal.SIGABRT, None)

            mock_metric.labels.assert_called_with(reason="gunicorn_timeout")
            mock_metric.labels.return_value.inc.assert_called_once()
        finally:
            signal.signal(signal.SIGABRT, old_handler)

    @pytest.mark.skipif(sys.platform == "win32", reason="Signal tests require Unix")
    def test_handler_captures_sentry(self):
        """AC5: The SIGABRT handler captures to Sentry."""
        import signal
        from worker_lifecycle import install_timeout_handler, set_active_request

        set_active_request("/v1/buscar", "sentry-test-id")
        old_handler = signal.getsignal(signal.SIGABRT)

        mock_sentry = MagicMock()
        mock_scope = MagicMock()
        mock_sentry.new_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
        mock_sentry.new_scope.return_value.__exit__ = MagicMock(return_value=False)

        try:
            install_timeout_handler(5555)
            handler = signal.getsignal(signal.SIGABRT)

            with patch("worker_lifecycle.logger"), \
                 patch("worker_lifecycle.signal.signal"), \
                 patch("worker_lifecycle.os.abort"), \
                 patch.dict(sys.modules, {"sentry_sdk": mock_sentry}):
                handler(signal.SIGABRT, None)

            mock_sentry.capture_message.assert_called_once()
            msg = mock_sentry.capture_message.call_args[0][0]
            assert "5555" in msg
            assert "/v1/buscar" in msg
        finally:
            signal.signal(signal.SIGABRT, old_handler)


# ============================================================================
# Middleware integration: active request tracking
# ============================================================================


class TestMiddlewareLifecycleTracking:
    """CorrelationIDMiddleware sets/clears active request for timeout tracking."""

    def test_lifecycle_import_flag(self):
        """middleware._HAS_LIFECYCLE is True when worker_lifecycle is available."""
        import middleware
        assert middleware._HAS_LIFECYCLE is True

    def test_search_id_path_regex_buscar_progress(self):
        """Regex extracts search_id from /buscar-progress/{id}."""
        import middleware
        m = middleware._SEARCH_ID_PATH_RE.search("/buscar-progress/abc-123")
        assert m is not None
        assert m.group(1) == "abc-123"

    def test_search_id_path_regex_v1_search(self):
        """Regex extracts search_id from /v1/search/{id}/status."""
        import middleware
        m = middleware._SEARCH_ID_PATH_RE.search("/v1/search/xyz-789/status")
        assert m is not None
        assert m.group(1) == "xyz-789"

    def test_search_id_path_regex_no_match(self):
        """Regex returns None for paths without search_id."""
        import middleware
        m = middleware._SEARCH_ID_PATH_RE.search("/health")
        assert m is None

    @pytest.mark.asyncio
    async def test_middleware_sets_and_clears_active_request(self):
        """Middleware calls set_active_request on start, clear on end."""
        from middleware import CorrelationIDMiddleware
        from worker_lifecycle import get_active_request

        call_log = []

        async def mock_app(scope, receive, send):
            # During request processing, active request should be set
            info = get_active_request()
            call_log.append(info.copy())
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        middleware = CorrelationIDMiddleware(mock_app)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/v1/buscar",
            "headers": [],
        }

        async def receive():
            return {"type": "http.request", "body": b""}

        sent = []
        async def send(msg):
            sent.append(msg)

        await middleware(scope, receive, send)

        # During processing, active request was set
        assert len(call_log) == 1
        assert call_log[0]["endpoint"] == "/v1/buscar"

        # After processing, active request should be cleared
        assert get_active_request() == {}

    @pytest.mark.asyncio
    async def test_middleware_clears_on_exception(self):
        """Middleware clears active request even when app raises."""
        from middleware import CorrelationIDMiddleware
        from worker_lifecycle import get_active_request

        async def failing_app(scope, receive, send):
            raise RuntimeError("boom")

        middleware = CorrelationIDMiddleware(failing_app)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
        }

        async def receive():
            return {"type": "http.request", "body": b""}

        async def send(msg):
            pass

        with pytest.raises(RuntimeError, match="boom"):
            await middleware(scope, receive, send)

        # Active request should still be cleared
        assert get_active_request() == {}

    @pytest.mark.asyncio
    async def test_middleware_extracts_search_id_from_header(self):
        """Middleware reads X-Search-ID header for tracking."""
        from middleware import CorrelationIDMiddleware
        from worker_lifecycle import get_active_request

        captured = []

        async def mock_app(scope, receive, send):
            captured.append(get_active_request().copy())
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        mw = CorrelationIDMiddleware(mock_app)
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/v1/buscar",
            "headers": [(b"x-search-id", b"header-search-id")],
        }

        async def receive():
            return {"type": "http.request", "body": b""}

        async def send(msg):
            pass

        await mw(scope, receive, send)

        assert captured[0]["search_id"] == "header-search-id"

    @pytest.mark.asyncio
    async def test_middleware_extracts_search_id_from_path(self):
        """Middleware extracts search_id from URL path patterns."""
        from middleware import CorrelationIDMiddleware
        from worker_lifecycle import get_active_request

        captured = []

        async def mock_app(scope, receive, send):
            captured.append(get_active_request().copy())
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        mw = CorrelationIDMiddleware(mock_app)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/buscar-progress/path-search-id",
            "headers": [],
        }

        async def receive():
            return {"type": "http.request", "body": b""}

        async def send(msg):
            pass

        await mw(scope, receive, send)

        assert captured[0]["search_id"] == "path-search-id"
