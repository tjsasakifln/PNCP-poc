# Metrics Setup — Prometheus + Grafana Cloud

## Overview

SmartLic exposes application metrics via a Prometheus-compatible `/metrics` endpoint.
These metrics cover search pipeline performance, cache effectiveness, API error rates,
LLM arbiter usage, and circuit breaker state.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `METRICS_ENABLED` | `true` | Enable/disable the `/metrics` endpoint |
| `METRICS_TOKEN` | *(empty)* | Bearer token for authentication. Empty = open access |

## Local Development

```bash
# Start backend
cd backend && uvicorn main:app --reload --port 8000

# Verify metrics endpoint
curl http://localhost:8000/metrics

# With auth (if METRICS_TOKEN is set)
curl -H "Authorization: Bearer $METRICS_TOKEN" http://localhost:8000/metrics
```

## Available Metrics

### Histograms (Latency)

| Metric | Labels | Description |
|--------|--------|-------------|
| `smartlic_search_duration_seconds` | sector, uf_count, cache_status | Total search pipeline duration |
| `smartlic_fetch_duration_seconds` | source | Data source fetch duration (pncp, pcp, etc.) |
| `smartlic_llm_call_duration_seconds` | model, decision | LLM arbiter call duration |

### Counters

| Metric | Labels | Description |
|--------|--------|-------------|
| `smartlic_cache_hits_total` | level, freshness | Cache hits (level: supabase/memory/local, freshness: fresh/stale) |
| `smartlic_cache_misses_total` | level | Cache misses |
| `smartlic_api_errors_total` | source, error_type | API errors (error_type: timeout/429/422/500/connection) |
| `smartlic_filter_decisions_total` | stage, decision | Filter pass/reject by stage |
| `smartlic_llm_calls_total` | model, decision, zone | LLM invocations (zone: standard/conservative/zero_match/recovery) |
| `smartlic_searches_total` | sector, result_status | Total searches (result_status: success/partial/empty/error) |

### Gauges

| Metric | Labels | Description |
|--------|--------|-------------|
| `smartlic_circuit_breaker_degraded` | source | 1 = degraded, 0 = healthy |
| `smartlic_active_searches` | *(none)* | Currently running search pipelines |

## Useful PromQL Queries

### Search P95 Latency
```promql
histogram_quantile(0.95, rate(smartlic_search_duration_seconds_bucket[5m]))
```

### Cache Hit Rate
```promql
rate(smartlic_cache_hits_total[5m]) / (rate(smartlic_cache_hits_total[5m]) + rate(smartlic_cache_misses_total[5m]))
```

### Error Rate by Source
```promql
rate(smartlic_api_errors_total[5m])
```

### LLM Approval Rate (SIM / total)
```promql
rate(smartlic_llm_calls_total{decision="SIM"}[5m]) / rate(smartlic_llm_calls_total[5m])
```

### Active Searches
```promql
smartlic_active_searches
```

## Grafana Cloud Free Tier Setup

1. **Create account** at [grafana.com/auth/sign-up](https://grafana.com/auth/sign-up) (Free tier: 10K metrics, 14d retention)

2. **Get Prometheus remote write URL** from Grafana Cloud > Prometheus > Details:
   ```
   https://prometheus-prod-XX-prod-XX.grafana.net/api/prom/push
   ```

3. **Install Grafana Agent** or configure Prometheus to scrape the endpoint:

   ```yaml
   # prometheus.yml (or grafana-agent config)
   scrape_configs:
     - job_name: smartlic
       scrape_interval: 30s
       scheme: https
       authorization:
         credentials: YOUR_METRICS_TOKEN
       static_configs:
         - targets:
           - bidiq-backend-production.up.railway.app
       metrics_path: /metrics
   ```

4. **Import dashboard** — Create a new dashboard in Grafana with the PromQL queries above, or import from the community.

## Railway Configuration

Set these env vars in Railway:

```bash
railway variables set METRICS_ENABLED=true
railway variables set METRICS_TOKEN=<generate-a-secure-token>
```

The `/metrics` endpoint will be available at:
```
https://bidiq-backend-production.up.railway.app/metrics
```
