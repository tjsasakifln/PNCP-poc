"""OpenTelemetry distributed tracing for SmartLic backend.

GTM-RESILIENCE-F02: Provides tracing initialization, tracer factory, and helpers.

Design principles:
  - Zero overhead when OTEL_EXPORTER_OTLP_ENDPOINT is not set (no-op mode)
  - Graceful fallback when opentelemetry packages are not installed
  - Sampling rate configurable via OTEL_SAMPLING_RATE (default 0.1 = 10%)
  - Service name configurable via OTEL_SERVICE_NAME (default "smartlic-backend")

Usage:
    from telemetry import init_tracing, get_tracer, get_current_span

    # In lifespan():
    init_tracing()

    # In any module:
    tracer = get_tracer(__name__)
    with tracer.start_as_current_span("my_operation") as span:
        span.set_attribute("key", "value")
        ...
"""

import logging
import os
from contextlib import contextmanager
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Module-level state
_initialized = False
_tracer_provider = None
_noop = True  # True when tracing is disabled or packages unavailable


def _is_otel_available() -> bool:
    """Check if OpenTelemetry SDK packages are installed."""
    try:
        import opentelemetry.api  # noqa: F401
        import opentelemetry.sdk  # noqa: F401
        return True
    except ImportError:
        return False


def init_tracing() -> None:
    """Initialize OpenTelemetry tracing.

    AC2: Creates TracerProvider with OTLP exporter and configures sampling.
    AC8: Reads OTEL_EXPORTER_OTLP_ENDPOINT — if not set, tracing is no-op.
    AC9: No-op mode has zero overhead (no TracerProvider created).

    Called once during application lifespan startup (AC3).
    """
    global _initialized, _tracer_provider, _noop

    if _initialized:
        return

    _initialized = True
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()

    if not endpoint:
        logger.info("OTEL_EXPORTER_OTLP_ENDPOINT not set — tracing disabled (no-op)")
        _noop = True
        return

    if not _is_otel_available():
        logger.warning(
            "OpenTelemetry packages not installed — tracing disabled. "
            "Install: pip install opentelemetry-api opentelemetry-sdk "
            "opentelemetry-exporter-otlp-proto-grpc"
        )
        _noop = True
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

        # AC7: Service name from env
        service_name = os.getenv("OTEL_SERVICE_NAME", "smartlic-backend")

        # AC6: Sampling rate from env (default 10%)
        sampling_rate = float(os.getenv("OTEL_SAMPLING_RATE", "0.1"))
        sampler = TraceIdRatioBased(sampling_rate)

        resource = Resource.create({SERVICE_NAME: service_name})

        _tracer_provider = TracerProvider(
            resource=resource,
            sampler=sampler,
        )

        # Configure OTLP exporter
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        span_processor = BatchSpanProcessor(exporter)
        _tracer_provider.add_span_processor(span_processor)

        # Set as global TracerProvider
        trace.set_tracer_provider(_tracer_provider)
        _noop = False

        logger.info(
            f"OpenTelemetry tracing initialized: service={service_name}, "
            f"endpoint={endpoint}, sampling_rate={sampling_rate}"
        )

        # AC4: Auto-instrument FastAPI
        _instrument_fastapi()

        # AC5: Auto-instrument httpx
        _instrument_httpx()

    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")
        _noop = True


def _instrument_fastapi() -> None:
    """AC4: Auto-instrument FastAPI routes with spans."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument()
        logger.info("FastAPI auto-instrumentation enabled")
    except ImportError:
        logger.warning("opentelemetry-instrumentation-fastapi not installed — skipping")
    except Exception as e:
        logger.warning(f"FastAPI instrumentation failed: {e}")


def _instrument_httpx() -> None:
    """AC5: Auto-instrument httpx HTTP calls (PNCP, PCP, etc.)."""
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        HTTPXClientInstrumentor().instrument()
        logger.info("httpx auto-instrumentation enabled")
    except ImportError:
        logger.warning("opentelemetry-instrumentation-httpx not installed — skipping")
    except Exception as e:
        logger.warning(f"httpx instrumentation failed: {e}")


def shutdown_tracing() -> None:
    """Gracefully shut down the TracerProvider, flushing pending spans."""
    global _tracer_provider
    if _tracer_provider is not None:
        try:
            _tracer_provider.shutdown()
            logger.info("OpenTelemetry tracing shut down")
        except Exception as e:
            logger.warning(f"Error shutting down tracing: {e}")


def get_tracer(name: str = __name__) -> Any:
    """Get a tracer instance for creating spans.

    AC25: Returns a functional tracer that creates spans when tracing is active.
    Returns a no-op tracer when tracing is disabled (zero overhead).

    Args:
        name: Module name for the tracer (typically __name__).

    Returns:
        opentelemetry.trace.Tracer or NoopTracer
    """
    if _noop:
        return _NoopTracer()

    from opentelemetry import trace
    return trace.get_tracer(name)


def get_current_span() -> Any:
    """Get the currently active span, or a no-op span if tracing is disabled.

    Useful for adding attributes to the current span from any code location.
    """
    if _noop:
        return _NoopSpan()

    from opentelemetry import trace
    return trace.get_current_span()


def get_trace_id() -> Optional[str]:
    """Get the current trace ID as a hex string, or None if tracing is disabled.

    AC17: Used to include trace_id in SSE events and log records.
    """
    if _noop:
        return None

    from opentelemetry import trace
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx and ctx.trace_id != 0:
        return format(ctx.trace_id, "032x")
    return None


def get_span_id() -> Optional[str]:
    """Get the current span ID as a hex string, or None if tracing is disabled."""
    if _noop:
        return None

    from opentelemetry import trace
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx and ctx.span_id != 0:
        return format(ctx.span_id, "016x")
    return None


def is_tracing_enabled() -> bool:
    """AC21: Check if tracing is active (OTLP endpoint configured and SDK loaded)."""
    return not _noop


@contextmanager
def optional_span(tracer: Any, name: str, attributes: Optional[dict] = None):
    """Context manager that creates a span if tracing is active, or no-ops.

    Convenience wrapper for instrumenting code without checking _noop everywhere.

    Args:
        tracer: Tracer instance from get_tracer().
        name: Span name.
        attributes: Optional dict of span attributes.

    Yields:
        The span (or _NoopSpan if tracing is disabled).
    """
    if _noop:
        yield _NoopSpan()
        return

    with tracer.start_as_current_span(name, attributes=attributes or {}) as span:
        yield span


# ============================================================================
# No-op implementations for zero-overhead fallback
# ============================================================================

class _NoopSpan:
    """No-op span that silently accepts all operations."""

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def set_status(self, status: Any, description: str = "") -> None:
        pass

    def record_exception(self, exception: Exception, attributes: Optional[dict] = None) -> None:
        pass

    def add_event(self, name: str, attributes: Optional[dict] = None) -> None:
        pass

    def is_recording(self) -> bool:
        return False

    def get_span_context(self) -> "_NoopSpanContext":
        return _NoopSpanContext()

    def end(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class _NoopSpanContext:
    """No-op span context."""
    trace_id = 0
    span_id = 0


class _NoopTracer:
    """No-op tracer that returns _NoopSpan for all operations."""

    def start_span(self, name: str, **kwargs) -> _NoopSpan:
        return _NoopSpan()

    @contextmanager
    def start_as_current_span(self, name: str, **kwargs):
        yield _NoopSpan()
