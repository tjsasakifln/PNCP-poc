"""GTM-RESILIENCE-E03: Tests for Prometheus metrics instrumentation.

Tests cover:
- AC1: /metrics endpoint functional + auth
- AC2: SEARCH_DURATION histogram
- AC3: CACHE_HITS / CACHE_MISSES counters
- AC4: API_ERRORS counter
- AC5: FILTER_DECISIONS counter
- AC6: LLM_CALLS + LLM_DURATION
- AC7: CIRCUIT_BREAKER_STATE gauge
- AC8: Graceful degradation (no-op when disabled)
- AC9: All metrics appear in /metrics output
"""

import os
from unittest.mock import patch

import pytest
from prometheus_client import REGISTRY, generate_latest

import metrics as m


# ============================================================================
# AC1: /metrics endpoint functional + auth
# ============================================================================


class TestMetricsEndpoint:
    """AC1: GET /metrics returns Prometheus text exposition format."""

    def test_metrics_app_available(self):
        """Metrics ASGI app should be available."""
        app = m.get_metrics_app()
        assert app is not None

    def test_is_available(self):
        assert m.is_available() is True

    def test_metrics_auth_middleware_pattern(self):
        """AC1: Auth middleware blocks unauthorized, allows authorized."""
        from starlette.testclient import TestClient
        from starlette.applications import Starlette
        from starlette.responses import JSONResponse
        from starlette.routing import Mount
        from starlette.middleware import Middleware
        from starlette.middleware.base import BaseHTTPMiddleware

        metrics_asgi = m.get_metrics_app()
        if metrics_asgi is None:
            pytest.skip("metrics app not available")

        class MetricsAuthMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                if request.url.path.startswith("/metrics"):
                    token = request.headers.get("Authorization", "")
                    if token != "Bearer testtoken":
                        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
                return await call_next(request)

        app = Starlette(
            routes=[Mount("/metrics", app=metrics_asgi)],
            middleware=[Middleware(MetricsAuthMiddleware)],
        )
        client = TestClient(app)

        # No token → 401
        resp = client.get("/metrics")
        assert resp.status_code == 401

        # Wrong token → 401
        resp = client.get("/metrics", headers={"Authorization": "Bearer wrong"})
        assert resp.status_code == 401

        # Correct token → 200
        resp = client.get("/metrics", headers={"Authorization": "Bearer testtoken"})
        assert resp.status_code == 200
        body = resp.text
        assert "# HELP" in body or "# TYPE" in body


# ============================================================================
# AC2: Search duration histogram
# ============================================================================


class TestSearchDurationMetric:
    """AC2: smartlic_search_duration_seconds records pipeline duration."""

    def test_search_duration_observe(self):
        m.SEARCH_DURATION.labels(
            sector="facilities", uf_count="5", cache_status="miss"
        ).observe(12.5)

    def test_search_duration_multiple_labels(self):
        m.SEARCH_DURATION.labels(
            sector="uniformes", uf_count="3", cache_status="fresh"
        ).observe(2.5)
        m.SEARCH_DURATION.labels(
            sector="uniformes", uf_count="3", cache_status="stale"
        ).observe(8.0)


# ============================================================================
# AC3: Cache hit/miss rate
# ============================================================================


class TestCacheMetrics:
    """AC3: Cache hit/miss counters with level and freshness labels."""

    def test_cache_hit_counter(self):
        m.CACHE_HITS.labels(level="supabase", freshness="fresh").inc()
        m.CACHE_HITS.labels(level="memory", freshness="stale").inc()
        m.CACHE_HITS.labels(level="local", freshness="stale").inc()

    def test_cache_miss_counter(self):
        m.CACHE_MISSES.labels(level="cascade").inc()
        m.CACHE_MISSES.labels(level="all").inc()
        m.CACHE_MISSES.labels(level="memory").inc()


# ============================================================================
# AC4: Error rate per source
# ============================================================================


class TestApiErrorsMetric:
    """AC4: smartlic_api_errors_total tracks errors by source and type."""

    def test_api_errors_increment(self):
        m.API_ERRORS.labels(source="pncp", error_type="timeout").inc()
        m.API_ERRORS.labels(source="pcp", error_type="429").inc()
        m.API_ERRORS.labels(source="pncp", error_type="500").inc()
        m.API_ERRORS.labels(source="compras_gov", error_type="connection").inc()

    def test_api_errors_422(self):
        m.API_ERRORS.labels(source="pncp", error_type="422").inc()


# ============================================================================
# AC5: Filter pass/reject ratios
# ============================================================================


class TestFilterDecisionsMetric:
    """AC5: smartlic_filter_decisions_total by stage and decision."""

    def test_filter_decisions_increment(self):
        m.FILTER_DECISIONS.labels(stage="uf", decision="reject").inc(50)
        m.FILTER_DECISIONS.labels(stage="keyword", decision="reject").inc(30)
        m.FILTER_DECISIONS.labels(stage="valor", decision="reject").inc(10)
        m.FILTER_DECISIONS.labels(stage="final", decision="pass").inc(15)

    def test_filter_decisions_all_stages(self):
        for stage in ["uf", "status", "esfera", "modalidade", "municipio",
                       "valor", "keyword", "min_match", "prazo", "outros", "final"]:
            m.FILTER_DECISIONS.labels(stage=stage, decision="reject").inc()
            m.FILTER_DECISIONS.labels(stage=stage, decision="pass").inc()


# ============================================================================
# AC6: LLM calls tracked
# ============================================================================


class TestLlmMetrics:
    """AC6: LLM call counter and duration histogram."""

    def test_llm_calls_counter(self):
        m.LLM_CALLS.labels(model="gpt-4.1-nano", decision="SIM", zone="standard").inc()
        m.LLM_CALLS.labels(model="gpt-4.1-nano", decision="NAO", zone="conservative").inc()
        m.LLM_CALLS.labels(model="gpt-4.1-nano", decision="ERROR", zone="zero_match").inc()

    def test_llm_duration_histogram(self):
        m.LLM_DURATION.labels(model="gpt-4.1-nano", decision="SIM").observe(0.15)
        m.LLM_DURATION.labels(model="gpt-4.1-nano", decision="NAO").observe(0.22)

    def test_llm_duration_range(self):
        for val in [0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]:
            m.LLM_DURATION.labels(model="test", decision="SIM").observe(val)


# ============================================================================
# AC7: Circuit breaker state exported
# ============================================================================


class TestCircuitBreakerMetric:
    """AC7: smartlic_circuit_breaker_degraded gauge."""

    def test_circuit_breaker_gauge_set(self):
        m.CIRCUIT_BREAKER_STATE.labels(source="pncp").set(1)
        m.CIRCUIT_BREAKER_STATE.labels(source="pcp").set(0)

    def test_circuit_breaker_toggle(self):
        gauge = m.CIRCUIT_BREAKER_STATE.labels(source="pncp")
        gauge.set(0)  # healthy
        gauge.set(1)  # tripped
        gauge.set(0)  # recovered


# ============================================================================
# AC8: Graceful degradation (no-op mode)
# ============================================================================


class TestGracefulDegradation:
    """AC8: When metrics disabled, all operations are silent no-ops."""

    def test_noop_metric_operations(self):
        from metrics import _NoopMetric
        noop = _NoopMetric()
        noop.inc()
        noop.inc(5)
        noop.dec()
        noop.set(42)
        noop.observe(1.5)
        labeled = noop.labels(foo="bar")
        labeled.inc()
        labeled.observe(0.5)

    def test_noop_returns_self_on_labels(self):
        """_NoopMetric.labels() returns self for chaining."""
        from metrics import _NoopMetric
        noop = _NoopMetric()
        result = noop.labels(a="1", b="2")
        assert result is noop


# ============================================================================
# AC9: Integration — all metrics appear in /metrics output
# ============================================================================


class TestMetricsIntegration:
    """AC9: All 11 metrics appear in /metrics output after instrumentation."""

    def test_all_metrics_registered(self):
        """After exercising all metrics, /metrics output contains all names."""
        m.SEARCH_DURATION.labels(sector="integ", uf_count="1", cache_status="miss").observe(5.0)
        m.FETCH_DURATION.labels(source="pncp").observe(3.0)
        m.LLM_DURATION.labels(model="integ", decision="SIM").observe(0.2)
        m.CACHE_HITS.labels(level="supabase", freshness="fresh").inc()
        m.CACHE_MISSES.labels(level="all").inc()
        m.API_ERRORS.labels(source="pncp", error_type="timeout").inc()
        m.FILTER_DECISIONS.labels(stage="uf", decision="reject").inc()
        m.LLM_CALLS.labels(model="integ", decision="SIM", zone="standard").inc()
        m.SEARCHES.labels(sector="integ", result_status="success").inc()
        m.CIRCUIT_BREAKER_STATE.labels(source="pncp").set(0)
        m.ACTIVE_SEARCHES.inc()

        output = generate_latest(REGISTRY).decode("utf-8")

        expected_metrics = [
            "smartlic_search_duration_seconds",
            "smartlic_fetch_duration_seconds",
            "smartlic_llm_call_duration_seconds",
            "smartlic_cache_hits_total",
            "smartlic_cache_misses_total",
            "smartlic_api_errors_total",
            "smartlic_filter_decisions_total",
            "smartlic_llm_calls_total",
            "smartlic_searches_total",
            "smartlic_circuit_breaker_degraded",
            "smartlic_active_searches",
        ]

        for metric_name in expected_metrics:
            assert metric_name in output, f"Metric {metric_name} not found in /metrics output"

    def test_active_searches_gauge(self):
        m.ACTIVE_SEARCHES.inc()
        m.ACTIVE_SEARCHES.inc()
        m.ACTIVE_SEARCHES.dec()

    def test_searches_counter_labels(self):
        m.SEARCHES.labels(sector="facilities", result_status="success").inc()
        m.SEARCHES.labels(sector="facilities", result_status="empty").inc()
        m.SEARCHES.labels(sector="facilities", result_status="partial").inc()
        m.SEARCHES.labels(sector="facilities", result_status="error").inc()

    def test_fetch_duration_per_source(self):
        """FETCH_DURATION tracks per-source latency."""
        m.FETCH_DURATION.labels(source="pncp").observe(10.0)
        m.FETCH_DURATION.labels(source="pcp").observe(5.0)
        m.FETCH_DURATION.labels(source="compras_gov").observe(3.0)
        m.FETCH_DURATION.labels(source="pipeline").observe(15.0)
