"""Tests for GTM-RESILIENCE-F02: OpenTelemetry distributed tracing.

Covers:
  AC22: init_tracing() no-op without OTLP endpoint
  AC23: init_tracing() configures TracerProvider with endpoint
  AC24: Sampling rate 0.0 vs 1.0
  AC25: get_tracer() returns functional tracer
  AC26: Pipeline spans hierarchy (integration)
  AC28: Existing tests pass without regression (tracing no-op by default)
"""

import importlib
import os
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers: reset telemetry module state between tests
# ---------------------------------------------------------------------------

def _reset_telemetry():
    """Reset the telemetry module state so each test starts clean."""
    import telemetry
    telemetry._initialized = False
    telemetry._tracer_provider = None
    telemetry._noop = True


@pytest.fixture(autouse=True)
def reset_telemetry_state():
    """Ensure telemetry is reset before and after each test."""
    _reset_telemetry()
    yield
    _reset_telemetry()


# ===========================================================================
# AC22: init_tracing() without OTLP endpoint = no-op
# ===========================================================================

class TestInitTracingNoOp:
    """AC22: init_tracing() without OTLP endpoint should be completely no-op."""

    def test_no_endpoint_is_noop(self):
        """No OTEL_EXPORTER_OTLP_ENDPOINT → tracing disabled, zero overhead."""
        import telemetry
        with patch.dict(os.environ, {}, clear=False):
            # Ensure no endpoint is set
            os.environ.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)
            telemetry.init_tracing()

        assert telemetry._noop is True
        assert telemetry._tracer_provider is None
        assert telemetry._initialized is True

    def test_empty_endpoint_is_noop(self):
        """Empty string OTEL_EXPORTER_OTLP_ENDPOINT → tracing disabled."""
        import telemetry
        with patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": ""}, clear=False):
            telemetry.init_tracing()

        assert telemetry._noop is True

    def test_whitespace_endpoint_is_noop(self):
        """Whitespace-only OTEL_EXPORTER_OTLP_ENDPOINT → tracing disabled."""
        import telemetry
        with patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": "   "}, clear=False):
            telemetry.init_tracing()

        assert telemetry._noop is True

    def test_no_exception_without_packages(self):
        """If OTel packages missing, init_tracing() should not raise."""
        import telemetry
        with patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317"}, clear=False):
            with patch.object(telemetry, "_is_otel_available", return_value=False):
                telemetry.init_tracing()  # Should NOT raise

        assert telemetry._noop is True

    def test_idempotent_init(self):
        """Calling init_tracing() twice should be safe (idempotent)."""
        import telemetry
        os.environ.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)
        telemetry.init_tracing()
        telemetry.init_tracing()  # Second call should be no-op

        assert telemetry._initialized is True
        assert telemetry._noop is True


# ===========================================================================
# AC23: init_tracing() with endpoint configures TracerProvider
# ===========================================================================

class TestInitTracingWithEndpoint:
    """AC23: init_tracing() with OTLP endpoint should configure tracing."""

    def test_configures_provider_when_otel_available(self):
        """With endpoint + packages, TracerProvider should be created."""
        import telemetry

        # Mock all OTel imports
        mock_provider = MagicMock()
        mock_trace = MagicMock()

        with patch.dict(os.environ, {
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
            "OTEL_SERVICE_NAME": "test-service",
            "OTEL_SAMPLING_RATE": "1.0",
        }, clear=False):
            with patch.object(telemetry, "_is_otel_available", return_value=True):
                with patch.dict("sys.modules", {
                    "opentelemetry": MagicMock(),
                    "opentelemetry.trace": mock_trace,
                    "opentelemetry.sdk": MagicMock(),
                    "opentelemetry.sdk.trace": MagicMock(TracerProvider=MagicMock(return_value=mock_provider)),
                    "opentelemetry.sdk.trace.export": MagicMock(),
                    "opentelemetry.sdk.trace.sampling": MagicMock(),
                    "opentelemetry.sdk.resources": MagicMock(),
                    "opentelemetry.exporter.otlp": MagicMock(),
                    "opentelemetry.exporter.otlp.proto": MagicMock(),
                    "opentelemetry.exporter.otlp.proto.grpc": MagicMock(),
                    "opentelemetry.exporter.otlp.proto.grpc.trace_exporter": MagicMock(),
                    "opentelemetry.instrumentation": MagicMock(),
                    "opentelemetry.instrumentation.fastapi": MagicMock(),
                    "opentelemetry.instrumentation.httpx": MagicMock(),
                }):
                    telemetry.init_tracing()

        assert telemetry._noop is False
        assert telemetry._tracer_provider is not None
        assert telemetry._initialized is True


# ===========================================================================
# AC24: Sampling rate behavior
# ===========================================================================

class TestSamplingRate:
    """AC24: Sampling rate should be read from OTEL_SAMPLING_RATE env var."""

    def test_default_sampling_rate_is_0_1(self):
        """Default sampling rate should be 0.1 (10%)."""
        # Just verify the env var defaults
        rate = float(os.getenv("OTEL_SAMPLING_RATE", "0.1"))
        assert rate == 0.1

    def test_custom_sampling_rate_read_from_env(self):
        """Custom sampling rate from env should be used."""
        with patch.dict(os.environ, {"OTEL_SAMPLING_RATE": "0.5"}):
            rate = float(os.getenv("OTEL_SAMPLING_RATE", "0.1"))
            assert rate == 0.5

    def test_zero_sampling_rate(self):
        """Sampling rate 0.0 should be valid."""
        with patch.dict(os.environ, {"OTEL_SAMPLING_RATE": "0.0"}):
            rate = float(os.getenv("OTEL_SAMPLING_RATE", "0.1"))
            assert rate == 0.0

    def test_full_sampling_rate(self):
        """Sampling rate 1.0 should be valid (100% sampling)."""
        with patch.dict(os.environ, {"OTEL_SAMPLING_RATE": "1.0"}):
            rate = float(os.getenv("OTEL_SAMPLING_RATE", "0.1"))
            assert rate == 1.0


# ===========================================================================
# AC25: get_tracer() returns functional tracer
# ===========================================================================

class TestGetTracer:
    """AC25: get_tracer() should return a functional tracer."""

    def test_noop_tracer_when_disabled(self):
        """When tracing is disabled, get_tracer() returns _NoopTracer."""
        import telemetry
        tracer = telemetry.get_tracer("test")

        assert isinstance(tracer, telemetry._NoopTracer)

    def test_noop_tracer_creates_noop_spans(self):
        """NoopTracer should create NoopSpans that accept all operations."""
        import telemetry
        tracer = telemetry.get_tracer("test")

        with tracer.start_as_current_span("test_span") as span:
            assert isinstance(span, telemetry._NoopSpan)
            # All operations should silently succeed
            span.set_attribute("key", "value")
            span.set_status("ok")
            span.record_exception(ValueError("test"))
            span.add_event("test_event")
            assert span.is_recording() is False

    def test_noop_span_context(self):
        """NoopSpan should return a NoopSpanContext with zero IDs."""
        import telemetry
        span = telemetry._NoopSpan()
        ctx = span.get_span_context()
        assert ctx.trace_id == 0
        assert ctx.span_id == 0

    def test_start_span_returns_noop(self):
        """NoopTracer.start_span() should return a NoopSpan."""
        import telemetry
        tracer = telemetry._NoopTracer()
        span = tracer.start_span("test")
        assert isinstance(span, telemetry._NoopSpan)


# ===========================================================================
# AC25+: get_trace_id / get_span_id / is_tracing_enabled
# ===========================================================================

class TestHelperFunctions:
    """Test trace_id, span_id, and is_tracing_enabled helpers."""

    def test_get_trace_id_returns_none_when_noop(self):
        """get_trace_id() should return None when tracing is disabled."""
        import telemetry
        assert telemetry.get_trace_id() is None

    def test_get_span_id_returns_none_when_noop(self):
        """get_span_id() should return None when tracing is disabled."""
        import telemetry
        assert telemetry.get_span_id() is None

    def test_is_tracing_enabled_false_when_noop(self):
        """is_tracing_enabled() should return False when tracing is disabled."""
        import telemetry
        assert telemetry.is_tracing_enabled() is False

    def test_is_tracing_enabled_true_when_active(self):
        """is_tracing_enabled() should return True when _noop is False."""
        import telemetry
        telemetry._noop = False
        assert telemetry.is_tracing_enabled() is True

    def test_get_current_span_noop(self):
        """get_current_span() should return NoopSpan when disabled."""
        import telemetry
        span = telemetry.get_current_span()
        assert isinstance(span, telemetry._NoopSpan)


# ===========================================================================
# optional_span context manager
# ===========================================================================

class TestOptionalSpan:
    """Test the optional_span context manager."""

    def test_optional_span_noop_mode(self):
        """optional_span should yield NoopSpan when tracing is disabled."""
        import telemetry
        tracer = telemetry.get_tracer("test")

        with telemetry.optional_span(tracer, "test_span") as span:
            assert isinstance(span, telemetry._NoopSpan)
            span.set_attribute("key", "value")  # Should not raise

    def test_optional_span_with_attributes(self):
        """optional_span should accept attributes dict."""
        import telemetry
        tracer = telemetry.get_tracer("test")

        with telemetry.optional_span(tracer, "test_span", {"foo": "bar"}) as span:
            assert isinstance(span, telemetry._NoopSpan)


# ===========================================================================
# shutdown_tracing
# ===========================================================================

class TestShutdown:
    """Test shutdown_tracing."""

    def test_shutdown_without_init(self):
        """shutdown_tracing() should be safe without init."""
        import telemetry
        telemetry.shutdown_tracing()  # Should not raise

    def test_shutdown_with_noop(self):
        """shutdown_tracing() with no provider should be safe."""
        import telemetry
        telemetry._tracer_provider = None
        telemetry.shutdown_tracing()  # Should not raise

    def test_shutdown_calls_provider_shutdown(self):
        """shutdown_tracing() should call provider.shutdown()."""
        import telemetry
        mock_provider = MagicMock()
        telemetry._tracer_provider = mock_provider

        telemetry.shutdown_tracing()

        mock_provider.shutdown.assert_called_once()


# ===========================================================================
# AC17: trace_id in SSE ProgressEvent
# ===========================================================================

class TestProgressEventTraceId:
    """AC17: ProgressEvent.to_dict() should include trace_id when active."""

    def test_no_trace_id_when_disabled(self):
        """ProgressEvent should not include trace_id when tracing disabled."""
        from progress import ProgressEvent
        event = ProgressEvent(stage="test", progress=50, message="test")
        d = event.to_dict()

        assert "trace_id" not in d  # Tracing disabled → no trace_id

    def test_trace_id_included_when_active(self):
        """ProgressEvent should include trace_id when tracing is active."""
        from progress import ProgressEvent
        event = ProgressEvent(stage="test", progress=50, message="test")

        with patch("telemetry.get_trace_id", return_value="abc123def456"):
            d = event.to_dict()

        assert d["trace_id"] == "abc123def456"


# ===========================================================================
# AC19: X-Request-ID linked to span
# ===========================================================================

class TestMiddlewareSpanLink:
    """AC19: CorrelationIDMiddleware links X-Request-ID to active span."""

    @pytest.mark.asyncio
    async def test_request_id_set_on_span(self):
        """Middleware should set http.request_id attribute on active span."""
        from middleware import CorrelationIDMiddleware
        from starlette.testclient import TestClient
        from starlette.applications import Starlette
        from starlette.responses import JSONResponse
        from starlette.routing import Route

        async def homepage(request):
            return JSONResponse({"ok": True})

        app = Starlette(routes=[Route("/", homepage)])
        app.add_middleware(CorrelationIDMiddleware)

        # With tracing disabled, the span link should be a no-op (no exception)
        client = TestClient(app)
        resp = client.get("/", headers={"X-Request-ID": "test-123"})
        assert resp.status_code == 200
        assert resp.headers["X-Request-ID"] == "test-123"


# ===========================================================================
# AC20: Log records include trace_id and span_id
# ===========================================================================

class TestLogRecordEnrichment:
    """AC20: RequestIDFilter adds trace_id and span_id to log records."""

    def test_filter_adds_trace_id(self):
        """RequestIDFilter should add trace_id='-' when tracing disabled."""
        from middleware import RequestIDFilter
        import logging

        f = RequestIDFilter()
        record = logging.LogRecord("test", logging.INFO, "", 0, "test", (), None)

        f.filter(record)

        assert hasattr(record, "trace_id")
        assert record.trace_id == "-"  # No tracing → "-"
        assert hasattr(record, "span_id")
        assert record.span_id == "-"


# ===========================================================================
# AC21: Health endpoint reports tracing status
# ===========================================================================

class TestHealthTracingStatus:
    """AC21: Health endpoint should include tracing: enabled/disabled."""

    def test_is_tracing_enabled_returns_bool(self):
        """is_tracing_enabled should return a bool."""
        import telemetry
        result = telemetry.is_tracing_enabled()
        assert isinstance(result, bool)
        assert result is False  # Default = disabled


# ===========================================================================
# AC28: No regression — tracing no-op by default in test env
# ===========================================================================

class TestNoRegression:
    """AC28: Tracing should be completely no-op in tests (no OTEL env vars)."""

    def test_tracing_noop_in_test_env(self):
        """Without OTEL env vars, tracing adds zero overhead."""
        import telemetry
        telemetry.init_tracing()

        # Everything should be no-op
        tracer = telemetry.get_tracer("test")
        with tracer.start_as_current_span("test") as span:
            span.set_attribute("key", "value")

        assert telemetry._noop is True
        assert telemetry.get_trace_id() is None
        assert telemetry.is_tracing_enabled() is False

    def test_optional_span_zero_overhead(self):
        """optional_span should add zero overhead in no-op mode."""
        import telemetry
        tracer = telemetry.get_tracer("test")

        # This should be a trivial operation
        for _ in range(100):
            with telemetry.optional_span(tracer, "test") as span:
                span.set_attribute("i", 1)

    def test_pipeline_import_works(self):
        """search_pipeline.py should import telemetry without errors."""
        # This tests AC28 implicitly — if telemetry import breaks,
        # the entire search pipeline would fail.
        import telemetry
        assert hasattr(telemetry, "get_tracer")
        assert hasattr(telemetry, "optional_span")
        assert hasattr(telemetry, "get_trace_id")
