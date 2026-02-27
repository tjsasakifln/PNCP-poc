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
    labelnames=["sector", "result_status", "search_mode"],
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

# GTM-GO-002: Rate limit exceeded counter
RATE_LIMIT_EXCEEDED = _create_counter(
    "smartlic_rate_limit_exceeded_total",
    "Rate limit exceeded events",
    labelnames=["endpoint", "limit_type"],
)

# CRIT-012 AC8: SSE connection errors
SSE_CONNECTION_ERRORS = _create_counter(
    "smartlic_sse_connection_errors_total",
    "SSE connection errors by type and phase",
    labelnames=["error_type", "phase"],
)

# CRIT-026 AC3: Worker timeout tracking
WORKER_TIMEOUT = _create_counter(
    "smartlic_worker_timeout_total",
    "Gunicorn worker timeout events",
    labelnames=["reason"],
)

# CRIT-035: Evidence prefix stripping counter
EVIDENCE_PREFIX_STRIPPED = _create_counter(
    "smartlic_filter_evidence_prefix_stripped_total",
    "Evidence prefix stripped before substring validation",
)

# CRIT-032: Periodic cache refresh metrics
# STORY-266: Trial email delivery tracking
TRIAL_EMAILS_SENT = _create_counter(
    "smartlic_trial_emails_sent_total",
    "Trial reminder emails sent",
    labelnames=["type"],  # midpoint, expiring, last_day, expired
)

CACHE_REFRESH_TOTAL = _create_counter(
    "smartlic_cache_refresh_total",
    "Cache refresh job outcomes",
    labelnames=["result"],  # success, skipped, failed, empty_retry
)

# GTM-INFRA-003 AC9: Quota skipped due to cache hit
CACHE_QUOTA_SKIPPED = _create_counter(
    "smartlic_cache_quota_skipped_total",
    "Times quota was skipped because response came from cache",
)

CACHE_REFRESH_DURATION = _create_histogram(
    "smartlic_cache_refresh_duration_seconds",
    "Cache refresh cycle duration",
    buckets=[10, 30, 60, 120, 300, 600],
)

# GTM-ARCH-001 AC18: Async search job duration histogram
SEARCH_JOB_DURATION = _create_histogram(
    "smartlic_search_job_duration_seconds",
    "Async search job duration in ARQ Worker",
    buckets=[5, 10, 15, 30, 60, 120, 300],
)

# STORY-267 AC16: Term search quality metrics
TERM_SEARCH_LLM_ACCEPTS = _create_counter(
    "smartlic_term_search_llm_accepts_total",
    "LLM accepts for term-based searches",
    labelnames=["zone"],  # zero_match, arbiter, recovery
)

TERM_SEARCH_LLM_REJECTS = _create_counter(
    "smartlic_term_search_llm_rejects_total",
    "LLM rejects for term-based searches",
    labelnames=["zone"],
)

TERM_SEARCH_SYNONYM_RECOVERIES = _create_counter(
    "smartlic_term_search_synonym_recoveries_total",
    "Synonym-based recoveries for term-based searches",
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

# STAB-007 AC4: Cache warming non-interference metrics
WARMING_COMBINATIONS_TOTAL = _create_counter(
    "smartlic_warming_combinations_total",
    "Cache warming outcomes per combination",
    labelnames=["result"],  # warmed, skipped_active, skipped_cb_open, skipped_rate_limit, failed, skipped_budget
)

WARMING_PAUSES_TOTAL = _create_counter(
    "smartlic_warming_pauses_total",
    "Times cache warming paused for active user searches",
)

# STORY-278 AC7: Daily digest email metrics
DIGEST_EMAILS_SENT = _create_counter(
    "smartlic_digest_emails_sent_total",
    "Daily digest emails sent",
    labelnames=["status"],  # success, failed, skipped
)

DIGEST_JOB_DURATION = _create_histogram(
    "smartlic_digest_job_duration_seconds",
    "Daily digest job duration",
    buckets=[10, 30, 60, 120, 300, 600, 1800],
)

# STORY-281 AC4: Inline fallback counter — tracks how often worker didn't complete in time
SEARCH_INLINE_FALLBACK = _create_counter(
    "smartlic_search_inline_fallback_total",
    "Inline fallback executions when ARQ worker did not complete in time",
)

# STORY-281 AC4: Worker completion time histogram — observe actual worker duration
SEARCH_WORKER_COMPLETION = _create_histogram(
    "smartlic_search_worker_completion_seconds",
    "Time for ARQ worker to complete search (observed by watchdog)",
    buckets=[5, 10, 15, 30, 60, 90, 120, 180, 300],
)

# STORY-290 AC5: Event loop blocking detection
EVENT_LOOP_BLOCKING_TOTAL = _create_counter(
    "smartlic_event_loop_blocking_total",
    "Detected event loop blocking events (asyncio slow callbacks)",
    labelnames=["source"],
)

# STORY-290: Supabase query offload duration tracking
SUPABASE_EXECUTE_DURATION = _create_histogram(
    "smartlic_supabase_execute_duration_seconds",
    "Duration of Supabase queries offloaded via sb_execute",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5],
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
