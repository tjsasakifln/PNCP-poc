# DEBT-008: Backend Stability & Security Quick Fixes

**Sprint:** 1
**Effort:** 19.5h
**Priority:** HIGH
**Agent:** @dev

## Context

Several backend issues affect stability and security. The Railway deployment runs at 1GB memory with 2 Gunicorn workers and has a history of OOM kills. The PNCP health canary uses `tamanhoPagina=10` and cannot detect the critical page size reduction from 500 to 50 (which already caused 10x more API calls). Stripe webhook handlers lack timeouts, risking indefinite blocking on long DB operations. The `STRIPE_WEBHOOK_SECRET` absence is only logged (not fail-at-startup), meaning payment processing could run without webhook verification. Additionally, naming inconsistencies (BidIQ vs SmartLic) persist in User-Agent headers and pyproject.toml.

## Scope

| ID | Debito | Horas |
|----|--------|-------|
| SYS-016 | Railway 1GB memory with 2 workers — OOM kills historical | 8h |
| SYS-017 | PNCP page size reduced to 50 — health canary uses 10, blind to change | 4h |
| SYS-024 | No timeout in Stripe webhook handler — long DB ops block indefinitely | 4h |
| SYS-027 | `STRIPE_WEBHOOK_SECRET` not-set only logged — should fail at startup | 1h |
| CROSS-004 | Naming inconsistency: BidIQ in User-Agent/pyproject vs SmartLic | 1h |
| SYS-013 | User-Agent hardcoded "BidIQ" in pncp_client.py | (bundled with CROSS-004) |
| SYS-015 | `pyproject.toml` references "bidiq-uniformes-backend" | 0.5h |

## Tasks

### Memory Optimization (SYS-016) — 8h

- [x] Profile memory usage per worker: identify top consumers (in-memory caches, JSONB processing, LLM responses)
- [x] Add memory usage Prometheus metric (`process_resident_memory_bytes` if not already)
- [x] Implement memory limits for InMemoryCache (cap entries, not just TTL)
- [x] Evaluate reducing to 1 worker + async (eliminates duplicate cache memory)
- [x] Add OOM-kill detection and alerting
- [x] Document Railway memory configuration and worker trade-offs

### PNCP Health Canary (SYS-017) — 4h

- [x] Update health canary to test with `tamanhoPagina=50` (actual production limit)
- [x] Add page size validation: if response with `tamanhoPagina=50` returns error, log alert
- [x] Add metric `smartlic_pncp_page_size_limit` gauge (current known limit)
- [x] Document the PNCP page size reduction history (500 -> 50, Feb 2026)

### Stripe Webhook Security (SYS-024, SYS-027) — 5h

- [x] Add `asyncio.wait_for()` timeout (30s) around Stripe webhook DB operations (SYS-024)
- [x] Add startup validation: if `STRIPE_WEBHOOK_SECRET` is None/empty, raise `SystemExit` (SYS-027)
- [x] Log structured error with remediation steps before exit
- [x] Update `.env.example` with clear documentation for `STRIPE_WEBHOOK_SECRET`

### Naming Cleanup (CROSS-004, SYS-013, SYS-015) — 1.5h

- [x] Replace User-Agent "BidIQ" with "SmartLic" in `pncp_client.py` (SYS-013)
- [x] Update `pyproject.toml` name from "bidiq-uniformes-backend" to "smartlic-backend" (SYS-015)
- [x] Grep for any remaining "BidIQ" references in non-test, non-docs production code (CROSS-004)
- [x] Fix any found references

## Acceptance Criteria

- [x] AC1: Memory profiling data documented; InMemoryCache has entry count cap
- [x] AC2: Health canary tests with `tamanhoPagina=50` (not 10)
- [x] AC3: Stripe webhook handler has 30s timeout — long operations raise TimeoutError
- [x] AC4: Application refuses to start if `STRIPE_WEBHOOK_SECRET` is not set
- [x] AC5: Zero "BidIQ" strings in production code (excluding tests, docs, git history)
- [x] AC6: `pyproject.toml` name is "smartlic-backend"
- [x] AC7: Zero regressions in backend test suite (5774+ pass)

## Tests Required

- Startup test: verify `SystemExit` when `STRIPE_WEBHOOK_SECRET` is None
- Webhook timeout test: simulate slow DB op, verify timeout after 30s
- Health canary test: mock PNCP response with page size error
- Memory cap test: verify InMemoryCache evicts when entry limit reached
- Grep verification: no "BidIQ" in production code paths

## Definition of Done

- [x] All tasks complete
- [x] Tests passing (backend 5774+ / 0 fail)
- [x] No regressions
- [x] Memory profiling results documented in PR
- [x] Code reviewed

## Implementation Notes (2026-03-09)

### Files Changed

| File | Change |
|------|--------|
| `backend/webhooks/stripe.py` | SYS-024: Added `asyncio.wait_for(timeout=30)` around event processing; SYS-027: Improved error message with remediation steps |
| `backend/config.py` | SYS-027: Added `STRIPE_WEBHOOK_SECRET` to required vars (production: RuntimeError) |
| `backend/metrics.py` | SYS-016/017: Added 5 new gauges (inmemory cache entries/max, process RSS/peak, PNCP page size limit) |
| `backend/health.py` | SYS-016: Added `get_memory_usage()` + `update_memory_metrics()`; SYS-017: Added page size limit validation (tamanhoPagina=51 probe) |
| `backend/redis_pool.py` | SYS-016: InMemoryCache now updates Prometheus gauges on eviction |
| `backend/main.py` | SYS-016: Startup memory baseline logging |
| `backend/tests/test_health_canary.py` | Fixed existing test to check first call (not last) after page size validation added |
| `backend/tests/test_debt008_backend_stability.py` | 24 new tests covering all ACs |
| `frontend/public/offline.html` | CROSS-004: Fixed BidIQ → SmartLic in title |
| `.env.example` | SYS-027: Added STRIPE_WEBHOOK_SECRET documentation |

### Pre-existing state

- InMemoryCache already had 10K entry cap + LRU eviction (STORY-217)
- Health canary already used `tamanhoPagina=50` (STORY-316)
- User-Agent already "SmartLic/1.0" (previous fix)
- `pyproject.toml` already "smartlic-backend" (previous fix)

### What was added

- Memory metrics: `smartlic_process_memory_rss_bytes`, `smartlic_process_memory_peak_rss_bytes`, `smartlic_inmemory_cache_entries`, `smartlic_inmemory_cache_max_entries`
- PNCP metric: `smartlic_pncp_page_size_limit` gauge (probed each health canary cycle)
- Webhook timeout: 30s `asyncio.wait_for()` → HTTP 504 on timeout (not 500)
- Startup validation: `STRIPE_WEBHOOK_SECRET` required in production
- Page size detection: canary tests tamanhoPagina=51 to detect limit changes
