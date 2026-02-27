# SmartLic — Service Level Objectives (SLOs)

**Version:** 1.0
**Effective:** 2026-02-27
**Owner:** Engineering Team (CONFENGE)
**Review Cadence:** Monthly

> Reference: [Google SRE — Service Level Objectives](https://sre.google/sre-book/service-level-objectives/), [Google SRE — Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)

## 1. SLO Definitions

SLOs are **conservative** (especially search success at 95%) because we are transitioning from ~0% reliability to a production-grade system. SLOs will be tightened as stability improves.

| SLI | SLO Target | Window | Rationale |
|-----|-----------|--------|-----------|
| Search Success Rate | 95% | 7 days rolling | Multi-source pipeline has external dependencies; 95% accounts for transient source failures |
| Search Latency p50 | <15s | 7 days rolling | Pipeline involves 3 sources + LLM classification; 15s is acceptable for batch search |
| Search Latency p99 | <60s | 7 days rolling | Tail latency driven by slow sources and LLM; 60s before Railway timeout (300s) |
| SSE Connection Success | 99% | 7 days rolling | SSE is critical for progress tracking; 99% allows for reconnection/retry |
| API Availability (non-5xx) | 99.5% | 30 days rolling | Longer window smooths deployment-related errors; 99.5% = ~3.6h downtime/month |

## 2. Service Level Indicators (SLIs)

### Search Success Rate

```
SLI = sum(searches{result_status in [success, partial]}) / sum(searches)
```

- **Source metric:** `smartlic_searches_total` (labels: `result_status`)
- **Success includes:** `success` (full results) + `partial` (degraded but useful)
- **Failure includes:** `error` + `empty` (no results found)

### Search Latency (p50, p99)

```
SLI_p50 = histogram_quantile(0.50, smartlic_search_duration_seconds_bucket)
SLI_p99 = histogram_quantile(0.99, smartlic_search_duration_seconds_bucket)
```

- **Source metric:** `smartlic_search_duration_seconds` (histogram)
- **Buckets:** 1, 2, 5, 10, 20, 30, 60, 120, 300 seconds

### SSE Connection Success

```
SLI = 1 - (smartlic_sse_connection_errors_total / smartlic_sse_connections_total)
```

- **Source metrics:** `smartlic_sse_connections_total` (counter), `smartlic_sse_connection_errors_total` (counter)

### API Availability

```
SLI = 1 - (smartlic_http_responses_total{status_class="5xx"} / smartlic_http_responses_total)
```

- **Source metric:** `smartlic_http_responses_total` (labels: `status_class`, `method`)
- **Excludes:** `/metrics` and `/health` endpoints (internal)

## 3. Prometheus Recording Rules

```yaml
groups:
  - name: smartlic_slo_recording
    interval: 60s
    rules:
      - record: smartlic:search_success_rate
        expr: >
          sum(rate(smartlic_searches_total{result_status=~"success|partial"}[7d]))
          / sum(rate(smartlic_searches_total[7d]))

      - record: smartlic:search_latency_p50
        expr: >
          histogram_quantile(0.50,
            sum(rate(smartlic_search_duration_seconds_bucket[7d])) by (le))

      - record: smartlic:search_latency_p99
        expr: >
          histogram_quantile(0.99,
            sum(rate(smartlic_search_duration_seconds_bucket[7d])) by (le))

      - record: smartlic:sse_connection_success_rate
        expr: >
          1 - (sum(rate(smartlic_sse_connection_errors_total[7d]))
          / sum(rate(smartlic_sse_connections_total[7d])))

      - record: smartlic:api_availability
        expr: >
          1 - (sum(rate(smartlic_http_responses_total{status_class="5xx"}[30d]))
          / sum(rate(smartlic_http_responses_total[30d])))
```

## 4. Error Budget

```
Error Budget = 1 - SLO Target
```

| SLO | Error Budget | Meaning |
|-----|-------------|---------|
| Search Success 95% | 5% | 5 out of 100 searches can fail |
| Search Latency p50 <15s | N/A (latency) | Budget expressed as headroom to target |
| Search Latency p99 <60s | N/A (latency) | Budget expressed as headroom to target |
| SSE Success 99% | 1% | 1 in 100 connections can fail |
| API Availability 99.5% | 0.5% | ~3.6h downtime per month |

### Burn Rate

```
Burn Rate = actual_error_rate / error_budget_rate
```

A burn rate of **1.0** means the budget is being consumed at exactly the rate allowed.
A burn rate of **14.4** means 1 day of budget consumed in 1 hour (critical alert threshold).

## 5. Alert Rules

| Alert | Condition | Severity | For Duration | Rationale |
|-------|-----------|----------|--------------|-----------|
| `SearchSuccessLow` | success rate <90% for 15min | critical | 15m | Well below SLO, likely systemic failure |
| `SearchLatencyHigh` | p99 >90s for 10min | warning | 10m | 50% over SLO target, approaching Railway timeout |
| `SSEDropRate` | >20% drops in 5min | warning | 5m | SSE is real-time; 20% drop impacts UX significantly |
| `ErrorBudgetBurn` | >50% budget consumed in 1h | critical | 1h | Unsustainable burn rate — needs immediate attention |
| `WorkerTimeout` | any SIGABRT in 5min | critical | 0m | Worker crash = lost in-flight requests |

### Prometheus Alert Rules

```yaml
groups:
  - name: smartlic_slo_alerts
    rules:
      - alert: SearchSuccessLow
        expr: smartlic:search_success_rate < 0.90
        for: 15m
        labels:
          severity: critical
        annotations:
          summary: "Search success rate critically low"

      - alert: SearchLatencyHigh
        expr: smartlic:search_latency_p99 > 90
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Search p99 latency exceeds 90s"

      - alert: SSEDropRate
        expr: >
          sum(rate(smartlic_sse_connection_errors_total[5m]))
          / sum(rate(smartlic_sse_connections_total[5m])) > 0.20
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "SSE connection drops exceed 20%"

      - alert: ErrorBudgetBurn
        expr: (1 - smartlic:search_success_rate) / (1 - 0.95) > 0.50
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "Error budget burn rate critically high"

      - alert: WorkerTimeout
        expr: increase(smartlic_worker_timeout_total[5m]) > 0
        labels:
          severity: critical
        annotations:
          summary: "Gunicorn worker timeout detected"
```

## 6. Sentry Alerts

| Alert | Trigger | Frequency |
|-------|---------|-----------|
| Worker Timeout (SIGABRT) | Error message contains "SIGABRT" | 5 min window |
| Circuit Breaker Open | `CircuitBreakerOpenError` raised | 5 min window |
| Search Pipeline Failure | Events with `search_error_code` tag | 15 min window |

## 7. Dashboard

The SLO dashboard is available at `/admin/slo` (admin-only). It shows:

- **SLO Compliance Gauges** — circular gauges showing current SLI vs target
- **Error Budget Bars** — horizontal bars showing budget consumption
- **Alert Rules Table** — current firing status for each alert rule
- **Recording Rules Reference** — Prometheus expressions for external monitoring

## 8. Implementation

- **Backend:** `backend/slo.py` — SLO definitions, SLI computation, alert evaluation
- **API:** `backend/routes/slo.py` — `GET /v1/admin/slo` endpoint
- **Health:** `backend/health.py` — SLO compliance in `GET /health` response
- **Frontend:** `frontend/app/admin/slo/page.tsx` — Dashboard UI
- **Metrics:** `backend/metrics.py` — `SSE_CONNECTIONS_TOTAL`, `HTTP_RESPONSES_TOTAL`

## 9. Future Improvements

- [ ] Deploy external Prometheus server for proper rolling window calculations
- [ ] Add Grafana dashboards using recording rules above
- [ ] Implement multi-window burn rate alerts (5m/1h/6h)
- [ ] Tighten SLOs as system stabilizes (target: 99% search success)
- [ ] Add per-source SLOs (PNCP, PCP, ComprasGov)
- [ ] PagerDuty/Slack integration for alert notifications
