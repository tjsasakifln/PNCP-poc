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
METRICS_TOKEN = os.getenv("METRICS_TOKEN", "").strip()

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

# UX-402 AC3: Total duration of zero-match batch classification
LLM_ZERO_MATCH_BATCH_DURATION = _create_histogram(
    "smartlic_llm_zero_match_batch_duration_seconds",
    "Total LLM zero-match batch classification duration",
    buckets=[0.1, 0.25, 0.5, 1, 2, 3, 5, 10],
)

# UX-402 AC8: Distribution of batch sizes sent to LLM
LLM_ZERO_MATCH_BATCH_SIZE = _create_histogram(
    "smartlic_llm_zero_match_batch_size",
    "Number of items per LLM zero-match batch call",
    buckets=[1, 5, 10, 15, 20, 25, 30, 40, 50],
)

# HARDEN-014 AC4: Per-future timeout counter for LLM batch classification
LLM_BATCH_TIMEOUT = _create_counter(
    "smartlic_llm_batch_timeout_total",
    "LLM batch futures that exceeded per-future timeout",
    labelnames=["phase"],  # "zero_match_batch", "zero_match_individual", "arbiter"
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

# DEBT-103 AC4: Arbiter LRU cache hit/miss/eviction counters
ARBITER_CACHE_HITS = _create_counter(
    "smartlic_arbiter_cache_hits_total",
    "Arbiter LRU cache hit count",
    labelnames=["level"],  # "l1" (in-memory), "l2" (redis)
)

ARBITER_CACHE_MISSES = _create_counter(
    "smartlic_arbiter_cache_misses_total",
    "Arbiter LRU cache miss count",
)

ARBITER_CACHE_EVICTIONS = _create_counter(
    "smartlic_arbiter_cache_evictions_total",
    "Arbiter LRU cache evictions when max size exceeded",
)

API_ERRORS = _create_counter(
    "smartlic_api_errors_total",
    "API error count by source and type",
    labelnames=["source", "error_type"],
)

# STORY-304 AC6: Bid conversion errors in response path
ITEMS_CONVERSION_ERRORS = _create_counter(
    "smartlic_items_conversion_errors_total",
    "Bid-to-LicitacaoItem conversion failures",
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

# HARDEN-003 AC3: SSE queue drops (backpressure when client disconnects)
SSE_QUEUE_DROPS = _create_counter(
    "smartlic_sse_queue_drops_total",
    "SSE queue events dropped due to full queue (backpressure)",
)

# HARDEN-004 AC5: Periodic tracker cleanup count
TRACKER_CLEANUP_COUNT = _create_counter(
    "smartlic_tracker_cleanup_count",
    "HARDEN-004: Number of stale trackers removed by periodic cleanup",
)

# HARDEN-005 AC3: Persist failures after retry exhaustion
PERSIST_FAILURES = _create_counter(
    "smartlic_persist_failures_total",
    "HARDEN-005: Persist results failures after retry exhaustion",
    labelnames=["store"],
)

# Datalake: possível truncamento silencioso pelo PostgREST (limite 1000 linhas por chamada RPC)
DATALAKE_TRUNCATION_SUSPECTED = _create_counter(
    "smartlic_datalake_truncation_suspected_total",
    "Datalake RPC queries that returned exactly 1000 rows — possible PostgREST silent truncation",
    labelnames=["uf"],
)

# HARDEN-006 AC4: Dedup merge-enrichment field counter
DEDUP_FIELDS_MERGED = _create_counter(
    "smartlic_dedup_fields_merged_total",
    "HARDEN-006: Fields merged from lower-priority duplicate into winner",
    labelnames=["field"],
)

# CRIT-012 AC8: SSE connection errors
SSE_CONNECTION_ERRORS = _create_counter(
    "smartlic_sse_connection_errors_total",
    "SSE connection errors by type and phase",
    labelnames=["error_type", "phase"],
)

# HARDEN-012 AC4: SSE client disconnects detected via request.is_disconnected()
SSE_DISCONNECTS_TOTAL = _create_counter(
    "smartlic_sse_disconnects_total",
    "SSE client disconnects detected server-side",
)

# STORY-359 AC4: Frontend SSE fallback to simulated progress
SSE_FALLBACK_SIMULATED_TOTAL = _create_counter(
    "smartlic_sse_fallback_simulated_total",
    "Times frontend fell back to simulated progress after SSE failure",
)

# TD-004 AC4: Legacy route deprecation tracking
LEGACY_ROUTE_CALLS = _create_counter(
    "smartlic_legacy_route_calls_total",
    "Calls to legacy (non-/v1/) routes that now return 404",
    labelnames=["method", "path"],
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

# HARDEN-009: Arbiter cache LRU size gauge
ARBITER_CACHE_SIZE = _create_gauge(
    "smartlic_arbiter_cache_size",
    "Current number of entries in the LLM arbiter in-memory cache",
)

# CRIT-032: Periodic cache refresh metrics
# STORY-266: Trial email delivery tracking
TRIAL_EMAILS_SENT = _create_counter(
    "smartlic_trial_emails_sent_total",
    "Trial reminder emails sent",
    labelnames=["type"],  # welcome, engagement_early, engagement, tips, urgency, expiring, last_day, expired
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

# CRIT-072 AC9: Async search queue + total time metrics
SEARCH_QUEUE_TIME = _create_histogram(
    "smartlic_search_queue_time_seconds",
    "Time spent in ARQ queue before worker picks up the job",
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60],
)

SEARCH_TOTAL_TIME = _create_histogram(
    "smartlic_search_total_time_seconds",
    "Total search time including queue wait + pipeline execution",
    buckets=[5, 10, 15, 30, 60, 120, 180, 300],
)

SEARCH_MODE_TOTAL = _create_counter(
    "smartlic_search_mode_total",
    "Total searches by mode (async vs sync)",
    labelnames=["mode"],
)

SYNC_FALLBACK_TOTAL = _create_counter(
    "smartlic_sync_fallback_total",
    "Searches that fell back to synchronous mode",
    ["reason"],
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
# STORY-296: Per-source bulkhead metrics
# ============================================================================

SOURCE_ACTIVE_REQUESTS = _create_gauge(
    "smartlic_source_active_requests",
    "Number of currently active requests per data source (bulkhead)",
    labelnames=["source"],
)

SOURCE_POOL_EXHAUSTED = _create_counter(
    "smartlic_source_pool_exhausted_total",
    "Times a source bulkhead pool was exhausted (caller had to wait)",
    labelnames=["source"],
)

SOURCE_SEMAPHORE_WAIT_SECONDS = _create_histogram(
    "smartlic_source_semaphore_wait_seconds",
    "Time spent waiting for a bulkhead semaphore slot",
    labelnames=["source"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10],
)

BULKHEAD_ACQUIRE_TIMEOUT = _create_counter(
    "smartlic_bulkhead_acquire_timeout_total",
    "Times a bulkhead semaphore acquire timed out (UF skipped)",
    labelnames=["source"],
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

# STORY-294 AC7: State store operation errors (Redis externalization)
STATE_STORE_ERRORS = _create_counter(
    "smartlic_state_store_errors_total",
    "State store operation errors by store and operation",
    labelnames=["store", "operation"],
)

# STORY-299 AC2: SSE connections total (for SLI: SSE connection success rate)
SSE_CONNECTIONS_TOTAL = _create_counter(
    "smartlic_sse_connections_total",
    "Total SSE connection attempts",
)

# STORY-299 AC2: HTTP response counter (for SLI: API availability)
HTTP_RESPONSES_TOTAL = _create_counter(
    "smartlic_http_responses_total",
    "Total HTTP responses by status class",
    labelnames=["status_class", "method"],
)

# CRIT-046 AC1: Supabase connection pool utilization
SUPABASE_POOL_ACTIVE = _create_gauge(
    "smartlic_supabase_pool_active_connections",
    "Number of currently active Supabase connections (via sb_execute)",
)

# CRIT-046 AC5: ConnectionError retries in sb_execute
SUPABASE_RETRY_TOTAL = _create_counter(
    "smartlic_supabase_retry_total",
    "Supabase sb_execute ConnectionError retries",
    labelnames=["outcome"],  # success, failure
)

# STORY-291 AC6: Supabase circuit breaker state gauge (0=closed, 1=open, 2=half_open)
SUPABASE_CB_STATE = _create_gauge(
    "smartlic_supabase_cb_state",
    "Supabase circuit breaker state (0=closed, 1=open, 2=half_open)",
)

# STORY-291 AC7 + CRIT-042 AC9: Supabase circuit breaker state transitions
SUPABASE_CB_TRANSITIONS = _create_counter(
    "smartlic_supabase_cb_transitions_total",
    "Supabase circuit breaker state transitions",
    labelnames=["from_state", "to_state", "source"],
)

# STORY-416: Per-category Supabase CB state gauge. The existing
# SUPABASE_CB_STATE stays as the legacy global signal, and this new
# gauge exposes the segregated read/write/rpc CBs so dashboards can
# pinpoint which category is flapping without deducing it from labels.
SUPABASE_CB_STATE_BY_CATEGORY = _create_gauge(
    "smartlic_supabase_cb_state_by_category",
    "Supabase CB state per category (0=closed, 1=open, 2=half_open)",
    labelnames=["category"],  # read, write, rpc, legacy
)

# STORY-426: Public query timeout observability
SUPABASE_QUERY_TIMEOUT_TOTAL = _create_counter(
    "smartlic_public_query_timeout_total",
    "Public endpoint queries that exceeded the statement timeout guard",
    labelnames=["endpoint"],
)

# STORY-427: CB internal error observability (RuntimeError in deque iteration)
SUPABASE_CB_INTERNAL_ERRORS = _create_counter(
    "smartlic_cb_internal_error_total",
    "RuntimeError inside SupabaseCircuitBreaker (deque mutation or similar)",
    labelnames=["cb_name"],
)

# STORY-418: Trial email DLQ observability
TRIAL_EMAIL_DLQ_ENQUEUED = _create_counter(
    "smartlic_trial_email_dlq_enqueued_total",
    "Trial emails routed into the dead-letter queue",
    labelnames=["email_type", "reason"],
)

TRIAL_EMAIL_DLQ_REPROCESSED = _create_counter(
    "smartlic_trial_email_dlq_reprocessed_total",
    "Trial emails successfully reprocessed from the dead-letter queue",
    labelnames=["email_type"],
)

TRIAL_EMAIL_DLQ_SIZE = _create_gauge(
    "smartlic_trial_email_dlq_size",
    "Current trial_email_dlq row count by state",
    labelnames=["state"],  # pending, abandoned
)

# ============================================================================
# STORY-309: Dunning metrics
# ============================================================================

DUNNING_EMAILS_SENT = _create_counter(
    "smartlic_dunning_emails_sent_total",
    "Dunning emails sent by sequence number and plan",
    labelnames=["email_number", "plan_type"],
)

DUNNING_RECOVERY = _create_counter(
    "smartlic_dunning_recovery_total",
    "Dunning recovery events by recovery channel",
    labelnames=["recovered_via"],  # email, in_app, self_service, webhook
)

DUNNING_CHURNED = _create_counter(
    "smartlic_dunning_churned_total",
    "Users churned after dunning sequence by decline type",
    labelnames=["decline_type"],  # soft, hard
)

SUBSCRIPTION_PAST_DUE = _create_gauge(
    "smartlic_subscription_past_due_gauge",
    "Current count of past_due subscriptions",
)

PAYMENT_FAILURE = _create_counter(
    "smartlic_payment_failure_total",
    "Payment failures by decline type and code",
    labelnames=["decline_type", "decline_code"],
)

# STORY-312 AC11: CTA conversion tracking (frontend reports via /v1/analytics/track-cta)
CTA_SHOWN = _create_counter(
    "smartlic_cta_shown_total",
    "Trial upsell CTAs shown by variant",
    labelnames=["variant"],
)

CTA_CLICKED = _create_counter(
    "smartlic_cta_clicked_total",
    "Trial upsell CTAs clicked by variant",
    labelnames=["variant"],
)

CTA_DISMISSED = _create_counter(
    "smartlic_cta_dismissed_total",
    "Trial upsell CTAs dismissed by variant",
    labelnames=["variant"],
)

# ============================================================================
# STORY-314: Stripe reconciliation metrics
# ============================================================================

RECONCILIATION_RUNS = _create_counter(
    "smartlic_reconciliation_runs_total",
    "Reconciliation job executions",
)

RECONCILIATION_DIVERGENCES = _create_counter(
    "smartlic_reconciliation_divergences_total",
    "Reconciliation divergences detected",
    labelnames=["field", "direction"],  # direction: stripe_ahead, db_ahead
)

RECONCILIATION_FIXES = _create_counter(
    "smartlic_reconciliation_fixes_total",
    "Reconciliation auto-fixes applied",
)

RECONCILIATION_DURATION = _create_histogram(
    "smartlic_reconciliation_duration_seconds",
    "Reconciliation job duration",
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
)

# STORY-313 AC18: Onboarding tour tracking
TOUR_COMPLETED = _create_counter(
    "smartlic_tour_completed_total",
    "Onboarding tours completed by tour_id",
    labelnames=["tour_id"],
)

TOUR_SKIPPED = _create_counter(
    "smartlic_tour_skipped_total",
    "Onboarding tours skipped by tour_id",
    labelnames=["tour_id"],
)

# ============================================================================
# STORY-315 AC20: Search Alert metrics
# ============================================================================

ALERTS_PROCESSED = _create_counter(
    "smartlic_alerts_processed_total",
    "Total alerts processed by outcome",
    labelnames=["outcome"],  # matched, skipped, error
)

ALERTS_ITEMS_MATCHED = _create_counter(
    "smartlic_alerts_items_matched_total",
    "Total items matched across all alerts",
)

ALERTS_EMAILS_SENT = _create_counter(
    "smartlic_alerts_emails_sent_total",
    "Alert digest emails sent",
    labelnames=["mode"],  # individual, consolidated
)

ALERTS_PROCESSING_DURATION = _create_histogram(
    "smartlic_alerts_processing_duration_seconds",
    "Total alert processing cycle duration",
    buckets=[5, 10, 30, 60, 120, 300, 600],
)

# ============================================================================
# STORY-351: Filter discard rate observability
# ============================================================================

FILTER_INPUT_TOTAL = _create_counter(
    "smartlic_filter_input_total",
    "Total bids entering the filter pipeline",
    labelnames=["sector", "source"],
)

FILTER_OUTPUT_TOTAL = _create_counter(
    "smartlic_filter_output_total",
    "Total bids passing the filter pipeline",
    labelnames=["sector", "source"],
)

FILTER_DISCARD_RATE = _create_histogram(
    "smartlic_filter_discard_rate",
    "Filter discard rate ratio (1 - output/input)",
    labelnames=["sector"],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0],
)

# STORY-358 AC1: Total bids processed through the search pipeline (per source)
BIDS_PROCESSED_TOTAL = _create_counter(
    "smartlic_bids_processed_total",
    "Total bids processed through the search pipeline",
    labelnames=["source"],
)

# CRIT-054 AC6: PCP v2 status mapping observability
PCP_STATUS_UNMAPPED_TOTAL = _create_counter(
    "smartlic_pcp_status_unmapped_total",
    "PCP v2 records with unmapped status (treated as desconhecido)",
)

# CRIT-057 AC3: Duration of zero-match classification block (with budget awareness)
FILTER_ZERO_MATCH_DURATION = _create_histogram(
    "smartlic_filter_zero_match_duration_seconds",
    "Total duration of zero-match LLM classification block",
    labelnames=["mode", "budget_exceeded"],
    buckets=[1, 2, 5, 10, 15, 20, 30, 45, 60, 90, 120, 180],
)

# CRIT-058 AC4: Zero-match cap metrics
ZERO_MATCH_CAP_APPLIED_TOTAL = _create_counter(
    "smartlic_zero_match_cap_applied_total",
    "CRIT-058: Times zero-match cap was applied (pool exceeded MAX_ZERO_MATCH_ITEMS)",
)

ZERO_MATCH_POOL_SIZE = _create_histogram(
    "smartlic_zero_match_pool_size",
    "CRIT-058: Size of zero-match pool before cap",
    buckets=[10, 25, 50, 100, 200, 300, 500, 750, 1000, 1500, 2000, 3000, 5000],
)

# CRIT-059: Async zero-match job metrics
ZERO_MATCH_JOB_DURATION = _create_histogram(
    "smartlic_zero_match_job_duration_seconds",
    "CRIT-059 AC8: Duration of async zero-match classification job",
    buckets=[1, 2, 5, 10, 15, 20, 30, 45, 60, 90, 120],
)

ZERO_MATCH_JOB_STATUS = _create_counter(
    "smartlic_zero_match_job_status_total",
    "CRIT-059 AC8: Async zero-match job outcomes",
    labelnames=["status"],  # completed, failed, timeout
)

ZERO_MATCH_JOB_QUEUE_TIME = _create_histogram(
    "smartlic_zero_match_job_queue_time_seconds",
    "CRIT-059 AC8: Time between enqueue and job start",
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60],
)

FILTER_PASSTHROUGH_TOTAL = _create_counter(
    "smartlic_filter_passthrough_total",
    "Filter pass-through decisions for non-standard records",
    labelnames=["reason"],
)

# STORY-350 AC3: Per-source bids fetched (enables future coverage measurement)
SOURCES_BIDS_FETCHED = _create_counter(
    "smartlic_sources_bids_fetched_total",
    "Total bids/items fetched per data source and UF",
    labelnames=["source", "uf"],
)

# STORY-328 AC25: Org context stripping metrics
ORG_CONTEXT_STRIPPED = _create_counter(
    "smartlic_org_context_stripped_total",
    "Bid descriptions where org context was stripped before keyword matching",
    labelnames=["sector"],
)

# STORY-354 AC5: LLM fallback to PENDING_REVIEW counter
LLM_FALLBACK_PENDING = _create_counter(
    "smartlic_llm_fallback_pending_total",
    "Bids classified as PENDING_REVIEW due to LLM unavailability",
    labelnames=["sector", "reason"],
)

# STORY-352 AC4: 30-day uptime percentage gauge (updated by health canary)
UPTIME_PCT_30D = _create_gauge(
    "smartlic_uptime_pct_30d",
    "30-day uptime percentage calculated from health checks",
)

# STORY-332 AC1: Redis availability gauge (1=connected, 0=fallback)
REDIS_AVAILABLE = _create_gauge(
    "smartlic_redis_available",
    "Redis availability (1=connected, 0=fallback/InMemoryCache)",
)

# STORY-332 AC2: How long Redis has been in fallback mode
REDIS_FALLBACK_DURATION = _create_gauge(
    "smartlic_redis_fallback_duration_seconds",
    "Seconds since Redis entered fallback mode (0 when connected)",
)

# STORY-353 AC5: Support SLA metrics
SUPPORT_PENDING_MESSAGES = _create_gauge(
    "smartlic_support_pending_messages",
    "Number of support conversations awaiting admin response",
)

SUPPORT_RESPONSE_TIME_HOURS = _create_histogram(
    "smartlic_support_response_time_hours",
    "Admin response time in business hours",
    buckets=[1, 2, 4, 8, 12, 16, 20, 24, 36, 48],
)


# ============================================================================
# STORY-316: Health Canary + Status Page metrics
# ============================================================================

HEALTH_CANARY_DURATION = _create_histogram(
    "smartlic_health_canary_duration_seconds",
    "Health canary check duration",
    buckets=[0.5, 1, 2, 5, 10, 15, 30],
)

HEALTH_CANARY_STATUS = _create_gauge(
    "smartlic_health_canary_status",
    "Health canary status (1=healthy, 0.5=degraded, 0=unhealthy)",
)

INCIDENTS_TOTAL = _create_counter(
    "smartlic_incidents_total",
    "Total incidents detected",
    labelnames=["source", "severity"],
)

# CRIT-053 AC7: Source degradation and partial results metrics
SOURCE_DEGRADATION_TOTAL = _create_counter(
    "smartlic_source_degradation_total",
    "CRIT-053: Times a source was marked as degraded",
    labelnames=["source", "reason"],
)

PARTIAL_RESULTS_SERVED_TOTAL = _create_counter(
    "smartlic_partial_results_served_total",
    "CRIT-053: Times partial results were served to users",
)

# CRIT-051 AC7: Cache composition metrics (per-UF composable cache)
CACHE_COMPOSITION_TOTAL = _create_counter(
    "smartlic_cache_composition_total",
    "CRIT-051: Cache composition outcomes for per-UF composable cache",
    labelnames=["result"],  # full_hit, partial_hit, miss
)

CACHE_COMPOSITION_COVERAGE = _create_histogram(
    "smartlic_cache_composition_coverage",
    "CRIT-051: Percentage of UFs found in cache during composition",
    buckets=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
)

# CRIT-055 AC5: Warmup coverage ratio (UFs cached / total UFs)
WARMUP_COVERAGE_RATIO = _create_gauge(
    "smartlic_warmup_coverage_ratio",
    "CRIT-055: Warmup UF coverage ratio (cached UFs / total UFs)",
)

# CRIT-056 AC5: Cache quality score metrics
CACHE_QUALITY_WRITE_TOTAL = _create_counter(
    "smartlic_cache_quality_write_total",
    "CRIT-056: Cache writes by quality bucket",
    labelnames=["quality_bucket"],  # full, partial, empty
)

CACHE_QUALITY_REVALIDATION_TOTAL = _create_counter(
    "smartlic_cache_quality_revalidation_total",
    "CRIT-056: Revalidations triggered by low cache quality score",
)

CACHE_QUALITY_SCORE = _create_histogram(
    "smartlic_cache_quality_score",
    "CRIT-056: Cache quality score distribution on writes",
    buckets=[0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9, 1.0],
)


# ============================================================================
# HARDEN-024: Saturation metrics (connection pools, queue depth)
# ============================================================================

# AC1: Redis pool connections currently in use
REDIS_POOL_CONNECTIONS_USED = _create_gauge(
    "smartlic_redis_pool_connections_used",
    "HARDEN-024: Redis pool connections currently in use",
)

# AC2: Redis pool max connections configured
REDIS_POOL_CONNECTIONS_MAX = _create_gauge(
    "smartlic_redis_pool_connections_max",
    "HARDEN-024: Redis pool max connections configured",
)

# AC3: httpx pool connections in use per data source
HTTPX_POOL_CONNECTIONS_USED = _create_gauge(
    "smartlic_httpx_pool_connections_used",
    "HARDEN-024: httpx pool connections in use per data source",
    labelnames=["source"],
)

# AC4: Active progress trackers count
TRACKER_ACTIVE_COUNT = _create_gauge(
    "smartlic_tracker_active_count",
    "HARDEN-024: Number of active progress trackers in memory",
)

# AC5: Background results stored in memory
BACKGROUND_RESULTS_COUNT = _create_gauge(
    "smartlic_background_results_count",
    "HARDEN-024: Number of search results stored in memory (L1 cache)",
)


# DEBT-008 SYS-017: PNCP page size limit gauge
PNCP_PAGE_SIZE_LIMIT = _create_gauge(
    "smartlic_pncp_page_size_limit",
    "Current known PNCP API page size limit (tamanhoPagina max)",
)


# ============================================================================
# DEBT-008 SYS-016: Memory monitoring
# ============================================================================

INMEMORY_CACHE_ENTRIES = _create_gauge(
    "smartlic_inmemory_cache_entries",
    "Current number of entries in InMemoryCache (L1 fallback)",
)

INMEMORY_CACHE_MAX_ENTRIES = _create_gauge(
    "smartlic_inmemory_cache_max_entries",
    "Maximum allowed entries in InMemoryCache",
)

PROCESS_MEMORY_RSS_BYTES = _create_gauge(
    "smartlic_process_memory_rss_bytes",
    "Process resident set size in bytes (RSS)",
)

PROCESS_MEMORY_PEAK_RSS_BYTES = _create_gauge(
    "smartlic_process_memory_peak_rss_bytes",
    "Peak process RSS in bytes (high-water mark)",
)


# ============================================================================
# DEBT-010 DB-031: Database table size monitoring
# ============================================================================

DB_TABLE_SIZE_BYTES = _create_gauge(
    "smartlic_table_size_bytes",
    "Table total size in bytes (pg_total_relation_size)",
    labelnames=["table_name"],
)

# DEBT-010 DB-015: Plan reconciliation metrics
PLAN_RECONCILIATION_RUNS = _create_counter(
    "smartlic_plan_reconciliation_runs_total",
    "Plan reconciliation job executions",
)

PLAN_RECONCILIATION_DRIFT = _create_counter(
    "smartlic_plan_reconciliation_drift_total",
    "Users with plan_type drift between profiles and user_subscriptions",
    labelnames=["direction"],
)


# DEBT-014 SYS-010/SYS-018: Auth token cache metrics
AUTH_CACHE_HITS = _create_counter(
    "smartlic_auth_cache_hits_total",
    "Auth token cache hits",
    labelnames=["level"],  # "memory" or "redis"
)

AUTH_CACHE_MISSES = _create_counter(
    "smartlic_auth_cache_misses_total",
    "Auth token cache misses (JWT validation required)",
)

AUTH_CACHE_SIZE = _create_gauge(
    "smartlic_auth_cache_size",
    "Current number of entries in auth in-memory cache",
)

AUTH_CACHE_EVICTIONS = _create_counter(
    "smartlic_auth_cache_evictions_total",
    "Auth cache LRU evictions when max size exceeded",
)

# DEBT-014 SYS-006: Task registry metrics
TASK_REGISTRY_HEALTHY = _create_gauge(
    "smartlic_task_registry_healthy",
    "Number of healthy background tasks in TaskRegistry",
)

TASK_REGISTRY_TOTAL = _create_gauge(
    "smartlic_task_registry_total",
    "Total registered background tasks in TaskRegistry",
)


# ============================================================================
# DEBT-110 AC14: LLM cost tracking
# ============================================================================

LLM_COST_BRL = _create_counter(
    "smartlic_llm_cost_brl_total",
    "Cumulative LLM cost in BRL",
    labelnames=["model", "call_type"],  # call_type: arbiter, summary, zero_match
)

# DEBT-v3-S2 AC1: LLM cost in USD (labels: model, operation)
LLM_COST_USD = _create_counter(
    "smartlic_llm_api_cost_dollars",
    "Cumulative LLM API cost in USD",
    labelnames=["model", "operation"],  # operation: arbiter, summary, zero_match
)

# DEBT-v3-S2 AC2: LLM token usage by model/operation/direction
LLM_TOKENS_DETAILED = _create_counter(
    "smartlic_llm_tokens_by_operation_total",
    "LLM token usage by model, operation, and direction",
    labelnames=["model", "operation", "direction"],  # direction: input, output
)

LLM_SUMMARY_CACHE_HITS = _create_counter(
    "smartlic_llm_summary_cache_hits_total",
    "LLM summary Redis cache hits (cross-worker sharing)",
)

LLM_SUMMARY_CACHE_MISSES = _create_counter(
    "smartlic_llm_summary_cache_misses_total",
    "LLM summary Redis cache misses",
)

# ============================================================================
# FN/FP observability (CTO Advisory Action Plan)
# ============================================================================

FILTER_DECISIONS_BY_SETOR = _create_counter(
    "smartlic_filter_decisions_by_setor_total",
    "Filter pipeline decisions by sector and outcome",
    labelnames=["setor", "decision"],  # decision: keyword_approved, keyword_rejected, llm_approved, llm_rejected
)

LLM_FALLBACK_REJECTS_TOTAL = _create_counter(
    "smartlic_llm_fallback_rejects_total",
    "Items rejected due to LLM failure (silent false negative risk)",
    labelnames=["setor", "reason"],  # reason: timeout, error, budget_exceeded
)

FEEDBACK_NEGATIVE_TOTAL = _create_counter(
    "smartlic_feedback_negative_total",
    "User negative feedback on search results (proxy for false positives)",
    labelnames=["setor"],
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
