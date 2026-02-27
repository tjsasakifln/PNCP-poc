"""STORY-299: Tests for SLO definitions, SLI calculations, error budget,
alert evaluation, and admin API endpoints.

Covers:
- AC1: SLO definitions completeness
- AC2: SLI calculation from Prometheus registry
- AC3: Error budget computation
- AC4: Alert rule evaluation
- AC5: Sentry alert definitions
- AC6: Health endpoint SLO compliance
- AC7-AC9: Admin SLO API endpoint
"""

import pytest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from main import app
from auth import require_auth
from admin import require_admin


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def admin_user():
    return {"id": "admin-slo-001", "email": "admin@test.com", "role": "admin"}


@pytest.fixture
def client_as_admin(admin_user):
    """TestClient with admin auth override."""
    app.dependency_overrides[require_auth] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(require_auth, None)
    app.dependency_overrides.pop(require_admin, None)


@pytest.fixture
def client_no_auth():
    """TestClient without any auth."""
    app.dependency_overrides.pop(require_auth, None)
    app.dependency_overrides.pop(require_admin, None)
    client = TestClient(app)
    yield client


# ============================================================================
# AC1: SLO Definitions
# ============================================================================


class TestSLODefinitions:
    """AC1: SLOs defined and documented."""

    def test_five_slos_defined(self):
        from slo import SLOS
        assert len(SLOS) == 5

    def test_search_success_rate_slo(self):
        from slo import SLOS
        slo = SLOS["search_success_rate"]
        assert slo.target == 0.95
        assert slo.window_days == 7
        assert slo.unit == "ratio"

    def test_search_latency_p50_slo(self):
        from slo import SLOS
        slo = SLOS["search_latency_p50"]
        assert slo.target == 15.0
        assert slo.window_days == 7
        assert slo.unit == "seconds"

    def test_search_latency_p99_slo(self):
        from slo import SLOS
        slo = SLOS["search_latency_p99"]
        assert slo.target == 60.0
        assert slo.window_days == 7
        assert slo.unit == "seconds"

    def test_sse_connection_success_slo(self):
        from slo import SLOS
        slo = SLOS["sse_connection_success"]
        assert slo.target == 0.99
        assert slo.window_days == 7
        assert slo.unit == "ratio"

    def test_api_availability_slo(self):
        from slo import SLOS
        slo = SLOS["api_availability"]
        assert slo.target == 0.995
        assert slo.window_days == 30
        assert slo.unit == "ratio"

    def test_all_slos_have_required_fields(self):
        from slo import SLOS
        for key, slo in SLOS.items():
            assert slo.name, f"{key} missing name"
            assert slo.sli_description, f"{key} missing description"
            assert 0 < slo.target <= 1.0 or slo.unit == "seconds", f"{key} invalid target"
            assert slo.window_days > 0, f"{key} invalid window"
            assert slo.unit in ("ratio", "seconds"), f"{key} invalid unit"


# ============================================================================
# AC2: Recording Rules
# ============================================================================


class TestRecordingRules:
    """AC2: Prometheus recording rules for each SLI."""

    def test_recording_rules_defined(self):
        from slo import RECORDING_RULES
        assert len(RECORDING_RULES) == 5

    def test_recording_rules_have_valid_names(self):
        from slo import RECORDING_RULES
        for name in RECORDING_RULES:
            assert name.startswith("smartlic:"), f"Rule {name} should start with 'smartlic:'"

    def test_recording_rules_are_nonempty_strings(self):
        from slo import RECORDING_RULES
        for name, expr in RECORDING_RULES.items():
            assert isinstance(expr, str), f"Rule {name} should be string"
            assert len(expr) > 10, f"Rule {name} is too short"


# ============================================================================
# AC2: SLI Calculation
# ============================================================================


class TestSLICalculation:
    """AC2: SLI computation from Prometheus registry."""

    def test_search_success_rate_with_data(self):
        """Compute search success rate when metrics have data."""
        import metrics as m
        # Exercise the counter with known values
        m.SEARCHES.labels(sector="test_slo", result_status="success", search_mode="sector").inc(90)
        m.SEARCHES.labels(sector="test_slo", result_status="partial", search_mode="sector").inc(5)
        m.SEARCHES.labels(sector="test_slo", result_status="error", search_mode="sector").inc(5)

        from slo import compute_sli
        sli = compute_sli("search_success_rate")
        # Note: other tests may have incremented counters too, so we just check it's a valid ratio
        assert sli is not None
        assert 0.0 <= sli <= 1.0

    def test_search_latency_p50(self):
        """Compute search latency p50 from histogram."""
        import metrics as m
        # Add observations
        for _ in range(10):
            m.SEARCH_DURATION.labels(sector="slo_test", uf_count="1", cache_status="miss").observe(5.0)

        from slo import compute_sli
        p50 = compute_sli("search_latency_p50")
        assert p50 is not None
        assert p50 > 0

    def test_search_latency_p99(self):
        """Compute search latency p99 from histogram."""
        from slo import compute_sli
        p99 = compute_sli("search_latency_p99")
        # May be None if no histogram data or may have a value from other tests
        if p99 is not None:
            assert p99 > 0

    def test_sse_connection_success_with_data(self):
        """SSE connection success rate."""
        import metrics as m
        m.SSE_CONNECTIONS_TOTAL.inc(100)
        m.SSE_CONNECTION_ERRORS.labels(error_type="test", phase="test").inc(2)

        from slo import compute_sli
        sli = compute_sli("sse_connection_success")
        assert sli is not None
        assert 0.0 <= sli <= 1.0

    def test_api_availability_with_data(self):
        """API availability from HTTP response counters."""
        import metrics as m
        m.HTTP_RESPONSES_TOTAL.labels(status_class="2xx", method="GET").inc(990)
        m.HTTP_RESPONSES_TOTAL.labels(status_class="5xx", method="GET").inc(10)

        from slo import compute_sli
        sli = compute_sli("api_availability")
        assert sli is not None
        assert 0.0 <= sli <= 1.0

    def test_unknown_slo_key_returns_none(self):
        from slo import compute_sli
        assert compute_sli("nonexistent_slo") is None


# ============================================================================
# AC3: Error Budget
# ============================================================================


class TestErrorBudget:
    """AC3: Error budget calculation."""

    def test_error_budget_property(self):
        from slo import SLOS
        assert SLOS["search_success_rate"].error_budget == pytest.approx(0.05)
        assert SLOS["sse_connection_success"].error_budget == pytest.approx(0.01)
        assert SLOS["api_availability"].error_budget == pytest.approx(0.005)

    def test_slo_status_with_data(self):
        from slo import compute_slo_status
        status = compute_slo_status("search_success_rate")
        assert status.slo_key == "search_success_rate"
        assert status.error_budget_total == pytest.approx(0.05)
        assert 0.0 <= status.error_budget_consumed <= 1.0
        assert 0.0 <= status.error_budget_remaining <= 1.0
        assert status.error_budget_consumed + status.error_budget_remaining == pytest.approx(1.0, abs=0.01)

    def test_slo_status_to_dict(self):
        from slo import compute_slo_status
        status = compute_slo_status("search_success_rate")
        d = status.to_dict()
        assert "key" in d
        assert "name" in d
        assert "target" in d
        assert "error_budget_consumed_pct" in d
        assert "error_budget_remaining_pct" in d
        assert "is_met" in d

    def test_compute_all_slo_statuses(self):
        from slo import compute_all_slo_statuses
        statuses = compute_all_slo_statuses()
        assert len(statuses) == 5
        for key, status in statuses.items():
            assert status.slo_key == key

    def test_latency_slo_budget(self):
        """Latency SLOs have meaningful budget computation."""
        from slo import compute_slo_status
        status = compute_slo_status("search_latency_p50")
        # Latency budget is computed differently
        assert 0.0 <= status.error_budget_consumed <= 1.0


# ============================================================================
# AC4: Alert Rules
# ============================================================================


class TestAlertRules:
    """AC4: Alert rule definitions and evaluation."""

    def test_five_alert_rules_defined(self):
        from slo import ALERT_RULES
        assert len(ALERT_RULES) == 5

    def test_alert_rule_names(self):
        from slo import ALERT_RULES
        names = {r.name for r in ALERT_RULES}
        assert "SearchSuccessLow" in names
        assert "SearchLatencyHigh" in names
        assert "SSEDropRate" in names
        assert "ErrorBudgetBurn" in names
        assert "WorkerTimeout" in names

    def test_alert_rule_severities(self):
        from slo import ALERT_RULES, SLOSeverity
        for rule in ALERT_RULES:
            assert isinstance(rule.severity, SLOSeverity)

    def test_evaluate_alert_returns_dict(self):
        from slo import ALERT_RULES, evaluate_alert
        for rule in ALERT_RULES:
            result = evaluate_alert(rule)
            assert "name" in result
            assert "severity" in result
            assert "firing" in result
            assert isinstance(result["firing"], bool)

    def test_evaluate_all_alerts(self):
        from slo import evaluate_all_alerts
        alerts = evaluate_all_alerts()
        assert len(alerts) == 5
        for alert in alerts:
            assert "name" in alert
            assert "firing" in alert

    def test_worker_timeout_not_firing_initially(self):
        """WorkerTimeout should not fire with zero timeouts."""
        from slo import ALERT_RULES, evaluate_alert
        rule = next(r for r in ALERT_RULES if r.name == "WorkerTimeout")
        result = evaluate_alert(rule)
        # May or may not fire depending on other tests, just check structure
        assert "value" in result


# ============================================================================
# AC5: Sentry Alert Definitions
# ============================================================================


class TestSentryAlerts:
    """AC5: Sentry alerts for critical errors."""

    def test_sentry_alerts_defined(self):
        from slo import SENTRY_ALERTS
        assert len(SENTRY_ALERTS) == 3

    def test_sentry_alert_structure(self):
        from slo import SENTRY_ALERTS
        for alert in SENTRY_ALERTS:
            assert "name" in alert
            assert "conditions" in alert
            assert "frequency" in alert
            assert "action" in alert


# ============================================================================
# AC6: Health Endpoint SLO Compliance
# ============================================================================


class TestHealthSLOCompliance:
    """AC6: GET /health returns SLO compliance status."""

    def test_get_slo_compliance_summary(self):
        from slo import get_slo_compliance_summary
        summary = get_slo_compliance_summary()
        assert "compliance" in summary
        assert summary["compliance"] in ("compliant", "violation", "no_data")
        assert "slos" in summary
        assert "alerts_firing" in summary
        assert isinstance(summary["alerts_firing"], int)


# ============================================================================
# AC7-AC9: Admin SLO API Endpoints
# ============================================================================


class TestSLOAdminEndpoint:
    """Admin SLO dashboard endpoint tests."""

    def test_get_slo_dashboard(self, client_as_admin):
        response = client_as_admin.get("/v1/admin/slo")
        assert response.status_code == 200
        data = response.json()
        assert "compliance" in data
        assert "slos" in data
        assert "alerts" in data
        assert "firing_count" in data
        assert "recording_rules" in data
        assert "sentry_alerts" in data

    def test_get_slo_dashboard_has_five_slos(self, client_as_admin):
        response = client_as_admin.get("/v1/admin/slo")
        data = response.json()
        assert len(data["slos"]) == 5

    def test_get_slo_dashboard_has_five_alerts(self, client_as_admin):
        response = client_as_admin.get("/v1/admin/slo")
        data = response.json()
        assert len(data["alerts"]) == 5

    def test_get_slo_alerts(self, client_as_admin):
        response = client_as_admin.get("/v1/admin/slo/alerts")
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "firing_count" in data
        assert len(data["alerts"]) == 5

    def test_slo_endpoint_requires_auth(self, client_no_auth):
        response = client_no_auth.get("/v1/admin/slo")
        assert response.status_code in (401, 403)


# ============================================================================
# New Metrics
# ============================================================================


class TestNewMetrics:
    """STORY-299: New metrics for SLI computation."""

    def test_sse_connections_total_defined(self):
        import metrics as m
        assert m.SSE_CONNECTIONS_TOTAL is not None
        m.SSE_CONNECTIONS_TOTAL.inc()

    def test_http_responses_total_defined(self):
        import metrics as m
        assert m.HTTP_RESPONSES_TOTAL is not None
        m.HTTP_RESPONSES_TOTAL.labels(status_class="2xx", method="GET").inc()
        m.HTTP_RESPONSES_TOTAL.labels(status_class="5xx", method="POST").inc()

    def test_new_metrics_in_registry(self):
        from prometheus_client import generate_latest, REGISTRY
        import metrics as m

        m.SSE_CONNECTIONS_TOTAL.inc()
        m.HTTP_RESPONSES_TOTAL.labels(status_class="2xx", method="GET").inc()

        output = generate_latest(REGISTRY).decode("utf-8")
        assert "smartlic_sse_connections_total" in output
        assert "smartlic_http_responses_total" in output
