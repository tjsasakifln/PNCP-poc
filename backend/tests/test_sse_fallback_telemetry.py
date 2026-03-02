"""STORY-359 AC4: Tests for SSE fallback telemetry endpoint."""

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


class TestSseFallbackEndpoint:
    """POST /v1/metrics/sse-fallback"""

    def test_returns_204_and_increments_counter(self, client):
        # The endpoint uses `from metrics import SSE_FALLBACK_SIMULATED_TOTAL`
        # so we need to patch at the module where it's used after import
        import metrics
        original = metrics.SSE_FALLBACK_SIMULATED_TOTAL
        mock_counter = MagicMock()
        metrics.SSE_FALLBACK_SIMULATED_TOTAL = mock_counter
        try:
            resp = client.post("/v1/metrics/sse-fallback")
            assert resp.status_code == 204
            mock_counter.inc.assert_called_once()
        finally:
            metrics.SSE_FALLBACK_SIMULATED_TOTAL = original

    def test_returns_204_no_body(self, client):
        with patch("metrics.SSE_FALLBACK_SIMULATED_TOTAL"):
            resp = client.post("/v1/metrics/sse-fallback")
            assert resp.status_code == 204
            assert resp.content == b""

    def test_get_not_allowed(self, client):
        resp = client.get("/v1/metrics/sse-fallback")
        assert resp.status_code == 405

    def test_counter_registered_in_metrics(self):
        """Verify the counter exists in the metrics module."""
        from metrics import SSE_FALLBACK_SIMULATED_TOTAL
        assert SSE_FALLBACK_SIMULATED_TOTAL is not None
