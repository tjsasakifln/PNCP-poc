# SLI/SLO Definitions — SmartLic

**STORY-226 Track 5 (AC21-AC22)**
**Date:** 2026-02-13
**Owner:** Platform Engineering

---

## Overview

This document defines the Service Level Indicators (SLIs) and Service Level Objectives (SLOs) for the SmartLic platform. These metrics establish the reliability contract between the platform team and its users, and drive alerting thresholds for on-call response.

---

## 1. Search Latency

| Property | Value |
|---|---|
| **SLI** | Time from search request received to response delivered (p95) |
| **SLO** | p95 < 15 seconds |
| **Measurement** | Backend middleware logs `duration_ms` on `POST /buscar` responses. The p95 is computed over a rolling 1-hour window. |
| **Data source** | `CorrelationIDMiddleware` log lines: `POST /buscar -> {status} ({duration_ms}ms)` |
| **Includes** | PNCP API fetch time, filtering, LLM summary generation, Excel generation |
| **Excludes** | Frontend rendering time, network transit to user |
| **Alerting threshold** | WARN at p95 > 12s (80% of budget consumed). CRITICAL at p95 > 15s (SLO breached). |
| **Escalation** | CRITICAL triggers PagerDuty alert to on-call engineer. |

### Notes

- Searches with many UFs (>10) or wide date ranges (>30 days) may legitimately exceed 15s. These are tracked separately as "heavy queries" and excluded from the primary SLO if they represent less than 5% of total traffic.
- The per-UF timeout is 90 seconds, but the p95 SLO targets the aggregate user experience.

---

## 2. API Availability

| Property | Value |
|---|---|
| **SLI** | Percentage of non-5xx responses across all API endpoints over a rolling 30-day window |
| **SLO** | 99.5% availability |
| **Measurement** | `(total_requests - 5xx_responses) / total_requests * 100` |
| **Data source** | HTTP response status codes from middleware logs and/or Railway metrics |
| **Includes** | All endpoints: `/buscar`, `/api/*`, `/health`, `/setores`, etc. |
| **Excludes** | Planned maintenance windows (announced at least 24 hours in advance) |
| **Alerting threshold** | WARN at 99.7% (error budget 40% consumed). CRITICAL at 99.5% (SLO breached). |
| **Error budget** | 99.5% over 30 days = ~3.6 hours of allowed downtime per month |

### Interpretation

- A 99.5% target allows approximately 216 minutes of downtime per 30-day period.
- Individual 502/503 responses from PNCP API upstream failures count against availability unless the backend properly returns a user-friendly degraded response (e.g., partial results with a warning).

---

## 3. Error Rate

| Property | Value |
|---|---|
| **SLI** | Percentage of requests resulting in 5xx status codes over a rolling 1-hour window |
| **SLO** | < 1% error rate |
| **Measurement** | `5xx_responses / total_requests * 100` per rolling 1-hour window |
| **Data source** | HTTP response status codes from middleware logs |
| **Includes** | All 5xx responses (500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout) |
| **Excludes** | 4xx responses (client errors are not platform errors) |
| **Alerting threshold** | WARN at 0.5% (50% of budget). CRITICAL at 1.0% (SLO breached). |
| **Escalation** | CRITICAL sustained for >5 minutes triggers PagerDuty alert. |

### Breakdown

| Error type | Expected cause | Mitigation |
|---|---|---|
| 500 | Unhandled exception in backend | Fix bug, add error handling |
| 502 | PNCP API upstream failure | Retry logic, circuit breaker |
| 503 | Rate limit / overload | Queue/throttle, scale up |
| 504 | Request timeout (>5 min) | Optimize query, reduce scope |

---

## 4. Summary Table

| SLI | SLO Target | Alert (WARN) | Alert (CRITICAL) | Window |
|---|---|---|---|---|
| Search latency (p95) | < 15s | > 12s | > 15s | 1 hour rolling |
| API availability | 99.5% | < 99.7% | < 99.5% | 30 days rolling |
| Error rate (5xx) | < 1% | > 0.5% | > 1.0% | 1 hour rolling |

---

## 5. Measurement Implementation

### Current (Logs-based)

All SLIs are currently derived from structured log output produced by `backend/middleware.py` (`CorrelationIDMiddleware`). Each request generates a single log line containing:

```
{method} {path} -> {status_code} ({duration_ms}ms) [req_id={uuid}]
```

To compute SLIs from logs:

```bash
# p95 search latency (last hour)
grep "POST /buscar" backend.log | \
  awk -F'[()]' '{print $2}' | sed 's/ms//' | \
  sort -n | awk '{a[NR]=$1} END {print a[int(NR*0.95)]}'

# Error rate (last hour)
grep -c "-> 5[0-9][0-9]" backend.log  # numerator
wc -l backend.log                        # denominator

# Availability (30 days)
# Use Railway metrics dashboard or aggregate daily log counts
```

### Future (Metrics-based)

When a metrics system (Prometheus, Datadog, etc.) is adopted:

1. **Search latency**: Histogram metric `http_request_duration_seconds{method="POST",path="/buscar"}` with p95 quantile.
2. **Availability**: Counter metrics `http_requests_total` and `http_requests_5xx_total`.
3. **Error rate**: `rate(http_requests_5xx_total[1h]) / rate(http_requests_total[1h]) * 100`.

---

## 6. Review Cadence

- **Weekly**: Review SLI dashboards in team standup.
- **Monthly**: Formal SLO review with error budget burn-down analysis.
- **Quarterly**: Adjust SLO targets based on observed performance and business needs.

---

## Changelog

| Date | Change |
|---|---|
| 2026-02-13 | Initial SLI/SLO definitions (STORY-226 AC21-AC22) |
