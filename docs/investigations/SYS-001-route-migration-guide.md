# SYS-001: Route Migration Guide — Legacy to /v1/ Prefix

**Date:** 2026-03-09
**Status:** Data Collection Phase (sunset pending 2+ weeks of metrics)

## Overview

All SmartLic API routes have been migrated to the `/v1/` prefix. Legacy root-level routes are being tracked via the `smartlic_legacy_route_calls_total` Prometheus metric.

## Current State

- **31 routers** mounted under `/v1/` prefix
- **1 root-level exception:** Stripe webhook (backward compatibility with configured callback URL)
- **Allowed root paths:** `/health`, `/health/live`, `/health/ready`, `/docs`, `/redoc`, `/metrics`, `/sources/health`, `/debug/pncp-test`, `/v1/setores`

## For External Consumers

If you are calling SmartLic API endpoints, update your base URL:

| Old Path | New Path | Notes |
|----------|----------|-------|
| `POST /buscar` | `POST /v1/buscar` | Main search endpoint |
| `GET /me` | `GET /v1/me` | User profile |
| `GET /plans` | `GET /v1/plans` | Plan listing |
| `POST /checkout` | `POST /v1/checkout` | Stripe checkout |
| `GET /pipeline` | `GET /v1/pipeline` | Opportunity pipeline |
| `GET /sessions` | `GET /v1/sessions` | Search sessions |
| `GET /health/cache` | `GET /v1/health/cache` | Cache health |

## Monitoring

The `smartlic_legacy_route_calls_total` counter (labels: `method`, `path`) tracks all calls to non-/v1/ routes that are not in the allowed root paths list. After 2+ weeks of data collection:

1. Query Prometheus: `sum by (path) (smartlic_legacy_route_calls_total)`
2. Identify routes with zero hits — safe to remove
3. Contact consumers of routes with hits — coordinate migration

## Timeline

- **Week 1-2 (current):** Data collection via Prometheus metric
- **Week 3:** Analyze metrics, identify zero-hit routes
- **Week 4+:** Remove zero-hit legacy routes (separate PR per batch)
- **2026-06-01:** Target sunset date for all legacy routes
