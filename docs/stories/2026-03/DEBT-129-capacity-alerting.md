# DEBT-129: Capacity Limits Documentation + Alerting
**Priority:** P1
**Effort:** 4h
**Owner:** @devops
**Sprint:** Week 3

## Context

SmartLic has 50+ Prometheus metrics, Sentry error tracking, and OpenTelemetry tracing, but no alerting rules inventory. The assessment identified a single-instance ceiling of approximately 30 concurrent users. Without alerts on critical metrics, the team will discover capacity problems from customer complaints rather than dashboards. For a paid product, this is unacceptable -- we need to know before customers do.

## Acceptance Criteria

### Alerting Rules

- [ ] AC1: Alert configured for `smartlic_supabase_cb_state` when circuit breaker is OPEN (critical)
- [ ] AC2: Alert configured for `smartlic_sse_connection_errors_total` rate exceeding threshold (warning at 5/min, critical at 20/min)
- [ ] AC3: Alert configured for response latency p99 exceeding 10 seconds
- [ ] AC4: Alert configured for error rate exceeding 5% of requests
- [ ] AC5: Alert configured for memory/CPU approaching Railway container limits
- [ ] AC6: Alerts route to appropriate channel (Slack, email, or PagerDuty)

### Capacity Documentation

- [ ] AC7: Document current capacity limits: ~30 concurrent users, single instance, per-worker L1 cache implications
- [ ] AC8: Document the scaling path: what to do when approaching limits (horizontal scaling checklist)
- [ ] AC9: Document known bottlenecks: ThreadPoolExecutor(10) for LLM calls, asyncio.Queue for SSE, InMemoryCache per-worker

### Runbook

- [ ] AC10: Runbook for "circuit breaker open" scenario (what to check, how to recover)
- [ ] AC11: Runbook for "high error rate" scenario
- [ ] AC12: Runbook for "high latency" scenario

## Technical Notes

**Alerting implementation options:**
1. **Railway native alerts** -- CPU, memory, restart count (simplest, limited)
2. **Prometheus + Alertmanager** -- Full flexibility but requires hosting Alertmanager
3. **Grafana Cloud free tier** -- 10K metrics, built-in alerting, connects to Prometheus
4. **Sentry alerts** -- Already integrated, can alert on error rate/latency thresholds

**Recommended approach:** Start with Sentry alerts (already integrated, zero new infra) for error rate and latency. Add Railway native alerts for resource limits. Document Prometheus metrics for future Grafana integration.

**Key metrics to monitor (from `backend/metrics.py`):**
- `smartlic_supabase_cb_state` -- gauge (0=closed, 1=half-open, 2=open)
- `smartlic_sse_connection_errors_total` -- counter with labels
- `smartlic_search_duration_seconds` -- histogram
- `smartlic_search_errors_total` -- counter
- `smartlic_cache_hits_total` / `smartlic_cache_misses_total`

## Test Requirements

- [ ] Alert rules documented and applied (no code tests -- operational verification)
- [ ] Manual trigger test for at least one alert (verify notification arrives)

## Files to Modify

- `docs/operations/capacity-limits.md` -- New: capacity documentation
- `docs/operations/alerting-runbook.md` -- New: alerting rules + runbooks
- Sentry dashboard configuration (if using Sentry alerts)
- Railway dashboard configuration (if using Railway alerts)

## Definition of Done

- [ ] All ACs pass
- [ ] At least one alert verified via manual trigger
- [ ] Documentation reviewed by team
- [ ] Runbooks accessible to all team members
