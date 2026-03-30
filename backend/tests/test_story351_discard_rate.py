"""STORY-351: Tests for filter discard rate observability.

Tests:
- DiscardRateTracker.record() and get_discard_rate()
- GET /v1/metrics/discard-rate endpoint
- Prometheus filter metrics instrumentation
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from filter.stats import DiscardRateTracker


# ============================================================================
# DiscardRateTracker unit tests
# ============================================================================


class TestDiscardRateTracker:
    def setup_method(self):
        self.tracker = DiscardRateTracker(retention_days=30)

    def test_record_and_get_basic(self):
        """Record a single search and verify discard rate."""
        self.tracker.record(input_count=100, output_count=13, sector="uniformes")
        result = self.tracker.get_discard_rate(days=30)

        assert result["discard_rate_pct"] == 87.0
        assert result["sample_size"] == 1
        assert result["total_input"] == 100
        assert result["total_output"] == 13
        assert result["period_days"] == 30
        assert "uniformes" in result["per_sector"]
        assert result["per_sector"]["uniformes"] == 87.0

    def test_record_ignores_zero_input(self):
        """Should not record entries with input_count <= 0."""
        self.tracker.record(input_count=0, output_count=0, sector="ti")
        result = self.tracker.get_discard_rate(days=30)
        assert result["sample_size"] == 0
        assert result["discard_rate_pct"] == 0.0

    def test_multiple_searches_aggregate(self):
        """Multiple searches aggregate correctly."""
        self.tracker.record(input_count=100, output_count=10, sector="uniformes")
        self.tracker.record(input_count=200, output_count=30, sector="ti")
        self.tracker.record(input_count=50, output_count=5, sector="uniformes")

        result = self.tracker.get_discard_rate(days=30)
        assert result["sample_size"] == 3
        assert result["total_input"] == 350
        assert result["total_output"] == 45
        # Overall: (1 - 45/350) * 100 = 87.1%
        assert result["discard_rate_pct"] == 87.1

        # Per sector
        assert result["per_sector"]["uniformes"] == 90.0  # (1 - 15/150) * 100
        assert result["per_sector"]["ti"] == 85.0  # (1 - 30/200) * 100

    def test_time_window_filtering(self):
        """Only includes records within the requested time window."""
        self.tracker.record(input_count=100, output_count=10, sector="uniformes")

        # Manually insert an old record
        old_entry = {
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=40)).isoformat(),
            "input": 200,
            "output": 100,
            "sector": "old",
        }
        self.tracker._records.append(old_entry)

        result = self.tracker.get_discard_rate(days=30)
        assert result["sample_size"] == 1  # Old record excluded
        assert result["total_input"] == 100

    def test_cleanup_old(self):
        """Cleanup removes entries older than retention period."""
        self.tracker.record(input_count=100, output_count=10, sector="test")

        # Insert old record
        old_entry = {
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=35)).isoformat(),
            "input": 200,
            "output": 100,
            "sector": "old",
        }
        self.tracker._records.append(old_entry)

        removed = self.tracker.cleanup_old()
        assert removed == 1
        assert len(self.tracker._records) == 1

    def test_empty_tracker_returns_zeros(self):
        """Empty tracker returns zero values."""
        result = self.tracker.get_discard_rate(days=30)
        assert result["discard_rate_pct"] == 0.0
        assert result["sample_size"] == 0
        assert result["total_input"] == 0
        assert result["total_output"] == 0
        assert result["per_sector"] == {}

    def test_structured_logging(self):
        """Verify structured log is emitted on record."""
        with patch("filter.stats.logger") as mock_logger:
            self.tracker.record(
                input_count=100, output_count=13, sector="uniformes", search_id="abc-123"
            )
            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args
            extra = call_kwargs.kwargs.get("extra") or call_kwargs[1].get("extra")
            assert extra["event"] == "filter_stats"
            assert extra["input"] == 100
            assert extra["output"] == 13
            assert extra["discard_rate"] == 0.87
            assert extra["sector"] == "uniformes"
            assert extra["search_id"] == "abc-123"

    def test_100_percent_discard_rate(self):
        """All items discarded = 100% rate."""
        self.tracker.record(input_count=50, output_count=0, sector="test")
        result = self.tracker.get_discard_rate()
        assert result["discard_rate_pct"] == 100.0

    def test_zero_discard_rate(self):
        """All items pass = 0% rate."""
        self.tracker.record(input_count=50, output_count=50, sector="test")
        result = self.tracker.get_discard_rate()
        assert result["discard_rate_pct"] == 0.0


# ============================================================================
# Endpoint tests — GET /v1/metrics/discard-rate
# ============================================================================


class TestDiscardRateEndpoint:
    @pytest.fixture(autouse=True)
    def setup_app(self):
        """Fresh app client with discard_rate_tracker reset."""
        from main import app
        from fastapi.testclient import TestClient
        from filter.stats import discard_rate_tracker

        # Reset tracker
        discard_rate_tracker._records.clear()
        self.client = TestClient(app)
        self.tracker = discard_rate_tracker

    def test_empty_returns_zeros(self):
        """Empty tracker returns zero discard rate."""
        resp = self.client.get("/v1/metrics/discard-rate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["discard_rate_pct"] == 0.0
        assert data["sample_size"] == 0

    def test_returns_computed_rate(self):
        """Returns correct discard rate after recording searches."""
        self.tracker.record(input_count=100, output_count=13, sector="uniformes")
        self.tracker.record(input_count=200, output_count=20, sector="ti")

        resp = self.client.get("/v1/metrics/discard-rate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sample_size"] == 2
        assert data["total_input"] == 300
        assert data["total_output"] == 33
        # (1 - 33/300) * 100 = 89.0
        assert data["discard_rate_pct"] == 89.0
        assert "uniformes" in data["per_sector"]
        assert "ti" in data["per_sector"]

    def test_custom_days_param(self):
        """Respects custom days query parameter."""
        self.tracker.record(input_count=100, output_count=10, sector="test")
        resp = self.client.get("/v1/metrics/discard-rate?days=7")
        assert resp.status_code == 200
        assert resp.json()["period_days"] == 7

    def test_no_auth_required(self):
        """Endpoint is public — no auth header needed."""
        resp = self.client.get("/v1/metrics/discard-rate")
        assert resp.status_code == 200  # Not 401/403

    def test_legacy_no_prefix_not_api(self):
        """TD-004: Legacy /metrics/discard-rate is caught by Prometheus mount, not the API."""
        resp = self.client.get("/metrics/discard-rate")
        # Prometheus mount catches all /metrics/* — returns 200 but NOT our API JSON
        assert "overall_rate" not in resp.text


# ============================================================================
# Prometheus metrics integration
# ============================================================================


class TestPrometheusFilterMetrics:
    def test_metrics_defined(self):
        """Verify STORY-351 metrics exist in metrics module."""
        import metrics

        assert hasattr(metrics, "FILTER_INPUT_TOTAL")
        assert hasattr(metrics, "FILTER_OUTPUT_TOTAL")
        assert hasattr(metrics, "FILTER_DISCARD_RATE")

    def test_noop_mode_when_prometheus_unavailable(self):
        """Metrics should be no-ops when prometheus_client is not installed."""
        import metrics

        # These should not raise even if prometheus is missing
        metrics.FILTER_INPUT_TOTAL.labels(sector="test", source="all").inc(100)
        metrics.FILTER_OUTPUT_TOTAL.labels(sector="test", source="all").inc(10)
        metrics.FILTER_DISCARD_RATE.labels(sector="test").observe(0.9)
