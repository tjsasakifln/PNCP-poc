"""GTM-RESILIENCE-E03: Prometheus metrics exporter for SmartLic.

Defines all application metrics (histograms, counters, gauges) and exposes
them via a /metrics endpoint in Prometheus text exposition format.

Graceful degradation: if prometheus_client is not installed, all metric
operations become silent no-ops — the application works normally without
any error.

Metrics are in-memory only (no network push on hot path). The /metrics
endpoint is scraped on demand by Prometheus or Grafana Agent.
"""

import logging
import os

logger = logging.getLogger(__name__)

# Feature flag: disable metrics entirely via env var
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() in ("true", "1", "yes", "on")
METRICS_TOKEN = os.getenv("METRICS_TOKEN", "")

try:
    from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False
    logger.info("prometheus_client not installed — metrics disabled (no-op mode)")


def _noop(*args, **kwargs):
    """No-op function for when prometheus_client is unavailable."""
    pass


class _NoopMetric:
    """Drop-in replacement for Prometheus metrics when library is unavailable."""

    def inc(self, *args, **kwargs):
        pass

    def dec(self, *args, **kwargs):
        pass

    def set(self, *args, **kwargs):
        pass

    def observe(self, *args, **kwargs):
        pass

    def labels(self, *args, **kwargs):
        return self


def _create_histogram(name, documentation, labelnames=None, buckets=None):
    if not _PROMETHEUS_AVAILABLE or not METRICS_ENABLED:
        return _NoopMetric()
    kwargs = {}
    if labelnames:
        kwargs["labelnames"] = labelnames
    if buckets:
        kwargs["buckets"] = buckets
    return Histogram(name, documentation, **kwargs)


def _create_counter(name, documentation, labelnames=None):
    if not _PROMETHEUS_AVAILABLE or not METRICS_ENABLED:
        return _NoopMetric()
    kwargs = {}
    if labelnames:
        kwargs["labelnames"] = labelnames
    return Counter(name, documentation, **kwargs)


def _create_gauge(name, documentation, labelnames=None):
    if not _PROMETHEUS_AVAILABLE or not METRICS_ENABLED:
        return _NoopMetric()
    kwargs = {}
    if labelnames:
        kwargs["labelnames"] = labelnames
    return Gauge(name, documentation, **kwargs)


# ============================================================================
# Histograms (latency)
# ============================================================================

SEARCH_DURATION = _create_histogram(
    "smartlic_search_duration_seconds",
    "Total search pipeline duration",
    labelnames=["sector", "uf_count", "cache_status"],
    buckets=[1, 2, 5, 10, 20, 30, 60, 120, 300],
)

FETCH_DURATION = _create_histogram(
    "smartlic_fetch_duration_seconds",
    "Data source fetch duration",
    labelnames=["source"],
    buckets=[1, 2, 5, 10, 20, 30, 60, 120],
)

LLM_DURATION = _create_histogram(
    "smartlic_llm_call_duration_seconds",
    "LLM arbiter call duration",
    labelnames=["model", "decision"],
    buckets=[0.1, 0.25, 0.5, 1, 2, 5],
)

# CRIT-003 AC22: Time spent in each pipeline state
STATE_DURATION = _create_histogram(
    "smartlic_search_state_duration_seconds",
    "Time spent in each search state",
    labelnames=["state"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300],
)

# ============================================================================
# Counters
# ============================================================================

CACHE_HITS = _create_counter(
    "smartlic_cache_hits_total",
    "Cache hit count",
    labelnames=["level", "freshness"],
)

CACHE_MISSES = _create_counter(
    "smartlic_cache_misses_total",
    "Cache miss count",
    labelnames=["level"],
)

API_ERRORS = _create_counter(
    "smartlic_api_errors_total",
    "API error count by source and type",
    labelnames=["source", "error_type"],
)

FILTER_DECISIONS = _create_counter(
    "smartlic_filter_decisions_total",
    "Filter pass/reject decisions",
    labelnames=["stage", "decision"],
)

LLM_CALLS = _create_counter(
    "smartlic_llm_calls_total",
    "LLM arbiter invocations",
    labelnames=["model", "decision", "zone"],
)

SEARCHES = _create_counter(
    "smartlic_searches_total",
    "Total searches executed",
    labelnames=["sector", "result_status"],
)

# CRIT-002 AC21: Search session status transitions
SESSION_STATUS = _create_counter(
    "smartlic_search_session_status_total",
    "Search session status transitions",
    labelnames=["status"],
)

# D-02 AC9: LLM token usage tracking
LLM_TOKENS = _create_counter(
    "smartlic_llm_tokens_total",
    "LLM token usage by direction",
    labelnames=["direction"],  # "input" or "output"
)

# CRIT-005 AC3: Response state counter
SEARCH_RESPONSE_STATE = _create_counter(
    "smartlic_search_response_state_total",
    "Total search responses by semantic state",
    labelnames=["state"],
)

# CRIT-005 AC4: Error type counter
SEARCH_ERROR_TYPE = _create_counter(
    "smartlic_search_error_type_total",
    "Total search errors by type",
    labelnames=["type"],
)

# ============================================================================
# Gauges
# ============================================================================

CIRCUIT_BREAKER_STATE = _create_gauge(
    "smartlic_circuit_breaker_degraded",
    "Circuit breaker degraded state (1=degraded, 0=healthy)",
    labelnames=["source"],
)

ACTIVE_SEARCHES = _create_gauge(
    "smartlic_active_searches",
    "Number of currently running search pipelines",
)


# ============================================================================
# ASGI app factory for /metrics endpoint
# ============================================================================

def get_metrics_app():
    """Return the Prometheus ASGI app for mounting at /metrics.

    Returns None if prometheus_client is not available or metrics are disabled.
    """
    if not _PROMETHEUS_AVAILABLE or not METRICS_ENABLED:
        return None
    return make_asgi_app()


def is_available() -> bool:
    """Return True if Prometheus metrics are operational."""
    return _PROMETHEUS_AVAILABLE and METRICS_ENABLED
