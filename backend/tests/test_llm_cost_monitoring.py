"""DEBT-v3-S2 AC1-AC4: Tests for LLM cost monitoring.

Verifies that:
- AC1: smartlic_llm_api_cost_dollars counter incremented on each LLM call
- AC2: smartlic_llm_tokens_by_operation_total counter incremented with correct labels
- AC4: Cost alert fires when hourly threshold exceeded
"""

import time
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture(autouse=True)
def reset_cost_tracker():
    """Reset the hourly cost tracker between tests."""
    import llm_arbiter
    llm_arbiter.classification._hourly_cost_usd.clear()
    llm_arbiter.classification._cost_alert_fired = False
    yield
    llm_arbiter.classification._hourly_cost_usd.clear()
    llm_arbiter.classification._cost_alert_fired = False


class TestLLMCostCounters:
    """AC1+AC2: Prometheus counters for LLM cost and tokens."""

    def test_log_token_usage_increments_usd_counter(self):
        """AC1: LLM_COST_USD counter incremented on each call."""
        from llm_arbiter import _log_token_usage

        mock_cost_usd = MagicMock()
        mock_tokens = MagicMock()
        mock_cost_brl = MagicMock()

        with patch("metrics.LLM_COST_BRL", mock_cost_brl), \
             patch("metrics.LLM_COST_USD", mock_cost_usd), \
             patch("metrics.LLM_TOKENS_DETAILED", mock_tokens):
            _log_token_usage("test-search-001", input_tokens=1000, output_tokens=100, call_type="arbiter")

        # AC1: USD counter was called
        mock_cost_usd.labels.assert_called_with(model="gpt-4.1-nano", operation="arbiter")
        mock_cost_usd.labels().inc.assert_called_once()
        # Verify cost is reasonable (1000 input * 0.10/1M + 100 output * 0.40/1M)
        expected_cost = 1000 * 0.10 / 1_000_000 + 100 * 0.40 / 1_000_000
        actual_cost = mock_cost_usd.labels().inc.call_args[0][0]
        assert abs(actual_cost - expected_cost) < 1e-10

    def test_log_token_usage_increments_token_counters(self):
        """AC2: LLM_TOKENS_DETAILED counter incremented with model/operation/direction labels."""
        from llm_arbiter import _log_token_usage

        mock_tokens = MagicMock()
        mock_cost_usd = MagicMock()
        mock_cost_brl = MagicMock()

        with patch("metrics.LLM_COST_BRL", mock_cost_brl), \
             patch("metrics.LLM_COST_USD", mock_cost_usd), \
             patch("metrics.LLM_TOKENS_DETAILED", mock_tokens):
            _log_token_usage("test-search-002", input_tokens=500, output_tokens=50, call_type="zero_match")

        # AC2: Token counter called for both input and output
        calls = mock_tokens.labels.call_args_list
        label_args = [c[1] if c[1] else dict(zip(["model", "operation", "direction"], c[0])) for c in calls]
        assert any(
            a.get("model") == "gpt-4.1-nano" and a.get("operation") == "zero_match" and a.get("direction") == "input"
            for a in label_args
        )
        assert any(
            a.get("model") == "gpt-4.1-nano" and a.get("operation") == "zero_match" and a.get("direction") == "output"
            for a in label_args
        )


class TestLLMCostAlert:
    """AC4: Cost alert when hourly threshold exceeded."""

    def test_alert_fires_when_threshold_exceeded(self):
        """AC4: Warning logged when cumulative cost > threshold."""
        from llm_arbiter import _log_token_usage

        mock_cost_brl = MagicMock()
        mock_cost_usd = MagicMock()
        mock_tokens = MagicMock()

        with patch("metrics.LLM_COST_BRL", mock_cost_brl), \
             patch("metrics.LLM_COST_USD", mock_cost_usd), \
             patch("metrics.LLM_TOKENS_DETAILED", mock_tokens), \
             patch("config.features.LLM_COST_ALERT_THRESHOLD", 0.001), \
             patch("llm_arbiter.classification.logger") as mock_logger:
            # Generate enough calls to exceed $0.001 threshold
            # Each call: 10000 input * 0.10/1M + 1000 output * 0.40/1M = 0.001 + 0.0004 = 0.0014
            _log_token_usage("test-alert-001", input_tokens=10000, output_tokens=1000, call_type="arbiter")

        mock_logger.warning.assert_called()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "LLM cost alert" in warning_msg
        assert "exceeds threshold" in warning_msg

    def test_alert_does_not_fire_below_threshold(self):
        """AC4: No warning when cost is below threshold."""
        from llm_arbiter import _log_token_usage

        mock_cost_brl = MagicMock()
        mock_cost_usd = MagicMock()
        mock_tokens = MagicMock()

        with patch("metrics.LLM_COST_BRL", mock_cost_brl), \
             patch("metrics.LLM_COST_USD", mock_cost_usd), \
             patch("metrics.LLM_TOKENS_DETAILED", mock_tokens), \
             patch("config.features.LLM_COST_ALERT_THRESHOLD", 100.0), \
             patch("llm_arbiter.classification.logger") as mock_logger:
            _log_token_usage("test-alert-002", input_tokens=100, output_tokens=10, call_type="arbiter")

        # No warning should be logged (only debug/info calls)
        for call in mock_logger.warning.call_args_list:
            assert "LLM cost alert" not in str(call)

    def test_alert_fires_only_once_until_reset(self):
        """AC4: Alert fires once, doesn't spam logs."""
        from llm_arbiter import _log_token_usage

        mock_cost_brl = MagicMock()
        mock_cost_usd = MagicMock()
        mock_tokens = MagicMock()

        with patch("metrics.LLM_COST_BRL", mock_cost_brl), \
             patch("metrics.LLM_COST_USD", mock_cost_usd), \
             patch("metrics.LLM_TOKENS_DETAILED", mock_tokens), \
             patch("config.features.LLM_COST_ALERT_THRESHOLD", 0.0001), \
             patch("llm_arbiter.classification.logger") as mock_logger:
            # Two calls that both exceed threshold
            _log_token_usage("test-alert-003a", input_tokens=10000, output_tokens=1000, call_type="arbiter")
            _log_token_usage("test-alert-003b", input_tokens=10000, output_tokens=1000, call_type="arbiter")

        # Alert should fire only once
        alert_warnings = [
            c for c in mock_logger.warning.call_args_list
            if "LLM cost alert" in str(c)
        ]
        assert len(alert_warnings) == 1
