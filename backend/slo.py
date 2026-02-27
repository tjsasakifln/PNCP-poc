"""STORY-299: SLO definitions, SLI calculations, error budget, and alert rules.

Implements Google SRE-style Service Level Objectives for SmartLic:
- SLO definitions with targets and rolling windows
- SLI calculation from in-process Prometheus registry
- Error budget computation
- Alert rule evaluation (burn rate alerts)

References:
- Google SRE — Service Level Objectives
- Google SRE — Alerting on SLOs
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# AC1: SLO Definitions
# ============================================================================


class SLOSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class SLODefinition:
    """A single SLO definition with its target and window."""

    name: str
    sli_description: str
    target: float  # e.g. 0.95 for 95%
    window_days: int  # rolling window in days
    unit: str  # "ratio", "seconds"

    @property
    def error_budget(self) -> float:
        """AC3: Error budget = 1 - SLO target."""
        return 1.0 - self.target


# AC1: Conservative SLOs — starting from ~0% to functional system
SLOS = {
    "search_success_rate": SLODefinition(
        name="Search Success Rate",
        sli_description="Proportion of searches completing successfully (success or partial)",
        target=0.95,
        window_days=7,
        unit="ratio",
    ),
    "search_latency_p50": SLODefinition(
        name="Search Latency p50",
        sli_description="50th percentile search pipeline duration",
        target=15.0,  # <15s
        window_days=7,
        unit="seconds",
    ),
    "search_latency_p99": SLODefinition(
        name="Search Latency p99",
        sli_description="99th percentile search pipeline duration",
        target=60.0,  # <60s
        window_days=7,
        unit="seconds",
    ),
    "sse_connection_success": SLODefinition(
        name="SSE Connection Success",
        sli_description="Proportion of SSE connections established without error",
        target=0.99,
        window_days=7,
        unit="ratio",
    ),
    "api_availability": SLODefinition(
        name="API Availability (non-5xx)",
        sli_description="Proportion of API requests not returning 5xx errors",
        target=0.995,
        window_days=30,
        unit="ratio",
    ),
}


# ============================================================================
# AC2: SLI Calculations (Prometheus recording rules)
# ============================================================================

# Prometheus recording rule expressions (for documentation / external Prometheus)
RECORDING_RULES = {
    "smartlic:search_success_rate": (
        'sum(rate(smartlic_searches_total{result_status=~"success|partial"}[7d])) '
        "/ sum(rate(smartlic_searches_total[7d]))"
    ),
    "smartlic:search_latency_p50": (
        "histogram_quantile(0.50, sum(rate(smartlic_search_duration_seconds_bucket[7d])) by (le))"
    ),
    "smartlic:search_latency_p99": (
        "histogram_quantile(0.99, sum(rate(smartlic_search_duration_seconds_bucket[7d])) by (le))"
    ),
    "smartlic:sse_connection_success_rate": (
        "1 - (sum(rate(smartlic_sse_connection_errors_total[7d])) "
        "/ sum(rate(smartlic_sse_connections_total[7d])))"
    ),
    "smartlic:api_availability": (
        '1 - (sum(rate(smartlic_http_responses_total{status=~"5.."}[30d])) '
        "/ sum(rate(smartlic_http_responses_total[30d])))"
    ),
}


def _get_counter_value(metric_name: str, label_filter: Optional[dict] = None) -> float:
    """Read a counter's current value from Prometheus REGISTRY."""
    try:
        from prometheus_client import REGISTRY

        for metric in REGISTRY.collect():
            if metric.name == metric_name:
                total = 0.0
                for sample in metric.samples:
                    if sample.name.endswith("_total") or sample.name == metric_name:
                        if label_filter:
                            if all(sample.labels.get(k) == v for k, v in label_filter.items()):
                                total += sample.value
                        else:
                            total += sample.value
                return total
    except ImportError:
        pass
    return 0.0


def _get_histogram_quantile(metric_name: str, quantile: float) -> Optional[float]:
    """Approximate a histogram quantile from bucket data in REGISTRY.

    Uses linear interpolation between bucket boundaries.
    """
    try:
        from prometheus_client import REGISTRY

        buckets: list[tuple[float, float]] = []  # (upper_bound, cumulative_count)
        total_count = 0.0

        for metric in REGISTRY.collect():
            if metric.name == metric_name:
                for sample in metric.samples:
                    if sample.name == f"{metric_name}_bucket":
                        le = float(sample.labels.get("le", "inf"))
                        buckets.append((le, sample.value))
                    elif sample.name == f"{metric_name}_count":
                        total_count += sample.value

        if not buckets or total_count == 0:
            return None

        # Sort by upper bound
        buckets.sort(key=lambda x: x[0])

        # Find the bucket containing the target quantile
        target = quantile * total_count
        prev_bound = 0.0
        prev_count = 0.0

        for upper_bound, cum_count in buckets:
            if cum_count >= target:
                if upper_bound == float("inf"):
                    return prev_bound  # Can't interpolate into +Inf
                # Linear interpolation
                if cum_count == prev_count:
                    return upper_bound
                fraction = (target - prev_count) / (cum_count - prev_count)
                return prev_bound + fraction * (upper_bound - prev_bound)
            prev_bound = upper_bound
            prev_count = cum_count

        return prev_bound  # All observations below last bucket
    except ImportError:
        pass
    return None


def compute_sli(slo_key: str) -> Optional[float]:
    """Compute current SLI value for a given SLO key.

    Returns float value:
    - For ratio SLOs: 0.0 to 1.0
    - For latency SLOs: seconds
    - None if insufficient data
    """
    if slo_key == "search_success_rate":
        success = _get_counter_value(
            "smartlic_searches", {"result_status": "success"}
        )
        partial = _get_counter_value(
            "smartlic_searches", {"result_status": "partial"}
        )
        total = _get_counter_value("smartlic_searches")
        if total == 0:
            return None
        return (success + partial) / total

    elif slo_key == "search_latency_p50":
        return _get_histogram_quantile("smartlic_search_duration_seconds", 0.50)

    elif slo_key == "search_latency_p99":
        return _get_histogram_quantile("smartlic_search_duration_seconds", 0.99)

    elif slo_key == "sse_connection_success":
        errors = _get_counter_value("smartlic_sse_connection_errors")
        total = _get_counter_value("smartlic_sse_connections")
        if total == 0:
            return None
        return 1.0 - (errors / total)

    elif slo_key == "api_availability":
        errors_5xx = _get_counter_value(
            "smartlic_http_responses", {"status_class": "5xx"}
        )
        total = _get_counter_value("smartlic_http_responses")
        if total == 0:
            return None
        return 1.0 - (errors_5xx / total)

    return None


# ============================================================================
# AC3: Error Budget
# ============================================================================


@dataclass
class SLOStatus:
    """Current status of an SLO including SLI value and error budget."""

    slo_key: str
    slo: SLODefinition
    sli_value: Optional[float]
    is_met: bool
    error_budget_total: float
    error_budget_consumed: float  # 0.0 to 1.0 (percentage consumed)
    error_budget_remaining: float  # 0.0 to 1.0 (percentage remaining)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.slo_key,
            "name": self.slo.name,
            "description": self.slo.sli_description,
            "target": self.slo.target,
            "window_days": self.slo.window_days,
            "unit": self.slo.unit,
            "sli_value": round(self.sli_value, 6) if self.sli_value is not None else None,
            "is_met": self.is_met,
            "error_budget_total": round(self.error_budget_total, 6),
            "error_budget_consumed_pct": round(self.error_budget_consumed * 100, 2),
            "error_budget_remaining_pct": round(self.error_budget_remaining * 100, 2),
        }


def compute_slo_status(slo_key: str) -> SLOStatus:
    """Compute full SLO status including error budget."""
    slo = SLOS[slo_key]
    sli_value = compute_sli(slo_key)

    error_budget_total = slo.error_budget

    if sli_value is None:
        # No data yet
        return SLOStatus(
            slo_key=slo_key,
            slo=slo,
            sli_value=None,
            is_met=True,  # Assume healthy when no data
            error_budget_total=error_budget_total,
            error_budget_consumed=0.0,
            error_budget_remaining=1.0,
        )

    if slo.unit == "ratio":
        # For ratio SLOs: error_rate = 1 - sli_value
        error_rate = 1.0 - sli_value
        is_met = sli_value >= slo.target
        # Budget consumed = error_rate / error_budget_total
        if error_budget_total > 0:
            consumed = min(error_rate / error_budget_total, 1.0)
        else:
            consumed = 0.0 if error_rate == 0 else 1.0
    else:
        # For latency SLOs: is_met if sli_value <= target
        is_met = sli_value <= slo.target
        # Budget consumed based on how far over target we are
        if is_met:
            consumed = sli_value / slo.target if slo.target > 0 else 0.0
        else:
            consumed = 1.0  # Over budget

    remaining = max(0.0, 1.0 - consumed)

    return SLOStatus(
        slo_key=slo_key,
        slo=slo,
        sli_value=sli_value,
        is_met=is_met,
        error_budget_total=error_budget_total,
        error_budget_consumed=consumed,
        error_budget_remaining=remaining,
    )


def compute_all_slo_statuses() -> dict[str, SLOStatus]:
    """Compute status for all defined SLOs."""
    return {key: compute_slo_status(key) for key in SLOS}


# ============================================================================
# AC4: Alert Rules
# ============================================================================


@dataclass(frozen=True)
class AlertRule:
    """Alert rule definition."""

    name: str
    condition_description: str
    condition_promql: str  # Prometheus expression (for documentation)
    severity: SLOSeverity
    for_duration: str  # e.g. "15m", "10m"
    summary: str
    slo_key: Optional[str] = None  # Linked SLO, if any


ALERT_RULES: list[AlertRule] = [
    AlertRule(
        name="SearchSuccessLow",
        condition_description="Search success rate below 90% for 15 minutes",
        condition_promql=(
            'sum(rate(smartlic_searches_total{result_status=~"success|partial"}[15m])) '
            "/ sum(rate(smartlic_searches_total[15m])) < 0.90"
        ),
        severity=SLOSeverity.CRITICAL,
        for_duration="15m",
        summary="Search success rate is critically low (<90%)",
        slo_key="search_success_rate",
    ),
    AlertRule(
        name="SearchLatencyHigh",
        condition_description="Search p99 latency above 90s for 10 minutes",
        condition_promql=(
            "histogram_quantile(0.99, sum(rate("
            "smartlic_search_duration_seconds_bucket[10m])) by (le)) > 90"
        ),
        severity=SLOSeverity.WARNING,
        for_duration="10m",
        summary="Search p99 latency exceeds 90s",
        slo_key="search_latency_p99",
    ),
    AlertRule(
        name="SSEDropRate",
        condition_description="SSE connection drop rate above 20% in 5 minutes",
        condition_promql=(
            "sum(rate(smartlic_sse_connection_errors_total[5m])) "
            "/ sum(rate(smartlic_sse_connections_total[5m])) > 0.20"
        ),
        severity=SLOSeverity.WARNING,
        for_duration="5m",
        summary="SSE connection drops exceed 20%",
        slo_key="sse_connection_success",
    ),
    AlertRule(
        name="ErrorBudgetBurn",
        condition_description="More than 50% of error budget consumed in 1 hour",
        condition_promql=(
            "(1 - smartlic:search_success_rate) / (1 - 0.95) > 0.50"
        ),
        severity=SLOSeverity.CRITICAL,
        for_duration="1h",
        summary="Error budget burn rate is critically high (>50% in 1h)",
        slo_key="search_success_rate",
    ),
    AlertRule(
        name="WorkerTimeout",
        condition_description="Any worker SIGABRT in 5 minutes",
        condition_promql=(
            "increase(smartlic_worker_timeout_total[5m]) > 0"
        ),
        severity=SLOSeverity.CRITICAL,
        for_duration="0m",
        summary="Gunicorn worker timeout (SIGABRT) detected",
    ),
]


def evaluate_alert(rule: AlertRule) -> dict[str, Any]:
    """Evaluate an alert rule against current metrics.

    Returns dict with alert status and context.
    """
    result: dict[str, Any] = {
        "name": rule.name,
        "severity": rule.severity.value,
        "for_duration": rule.for_duration,
        "summary": rule.summary,
        "firing": False,
        "value": None,
    }

    if rule.name == "SearchSuccessLow":
        sli = compute_sli("search_success_rate")
        if sli is not None:
            result["value"] = round(sli, 4)
            result["firing"] = sli < 0.90

    elif rule.name == "SearchLatencyHigh":
        p99 = compute_sli("search_latency_p99")
        if p99 is not None:
            result["value"] = round(p99, 2)
            result["firing"] = p99 > 90.0

    elif rule.name == "SSEDropRate":
        sli = compute_sli("sse_connection_success")
        if sli is not None:
            drop_rate = 1.0 - sli
            result["value"] = round(drop_rate, 4)
            result["firing"] = drop_rate > 0.20

    elif rule.name == "ErrorBudgetBurn":
        status = compute_slo_status("search_success_rate")
        if status.sli_value is not None:
            result["value"] = round(status.error_budget_consumed, 4)
            result["firing"] = status.error_budget_consumed > 0.50

    elif rule.name == "WorkerTimeout":
        timeouts = _get_counter_value("smartlic_worker_timeout")
        result["value"] = timeouts
        result["firing"] = timeouts > 0

    return result


def evaluate_all_alerts() -> list[dict[str, Any]]:
    """Evaluate all alert rules and return their statuses."""
    return [evaluate_alert(rule) for rule in ALERT_RULES]


# ============================================================================
# AC5: Sentry Alert Definitions (documentation/configuration reference)
# ============================================================================

SENTRY_ALERTS = [
    {
        "name": "Worker Timeout (SIGABRT)",
        "conditions": ["event.type:error", "event.message:*SIGABRT*"],
        "frequency": "5 minutes",
        "action": "Send notification to #smartlic-alerts",
    },
    {
        "name": "Circuit Breaker Open",
        "conditions": ["event.type:error", "event.message:*CircuitBreakerOpenError*"],
        "frequency": "5 minutes",
        "action": "Send notification to #smartlic-alerts",
    },
    {
        "name": "Search Pipeline Failure",
        "conditions": ["event.type:error", "event.tags.search_error_code:*"],
        "frequency": "15 minutes",
        "action": "Send notification to #smartlic-alerts",
    },
]


# ============================================================================
# Aggregate SLO compliance for health endpoint
# ============================================================================


def get_slo_compliance_summary() -> dict[str, Any]:
    """AC6: SLO compliance summary for /health endpoint."""
    statuses = compute_all_slo_statuses()

    all_met = all(s.is_met for s in statuses.values())
    any_data = any(s.sli_value is not None for s in statuses.values())

    if not any_data:
        compliance = "no_data"
    elif all_met:
        compliance = "compliant"
    else:
        compliance = "violation"

    return {
        "compliance": compliance,
        "slos": {key: s.to_dict() for key, s in statuses.items()},
        "alerts_firing": sum(
            1 for a in evaluate_all_alerts() if a["firing"]
        ),
        "computed_at": time.time(),
    }
