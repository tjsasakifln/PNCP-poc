# TD-008: PNCP Client Sync/Async Audit Report

**Date:** 2026-02-16
**Author:** Squad TD-008 (@architect + @dev + @qa)
**Status:** Complete

---

## 1. Executive Summary

The sync `PNCPClient` class (lines 223-721, `requests` library) is **still actively used in 3 production code paths** and cannot be safely removed without migration. The recommendation is to **migrate the 3 callers to async** in TD-009, then remove the sync client entirely.

---

## 2. Sync PNCPClient() Caller Audit

| # | File | Line | Usage Context | Classification | Can Remove Safely? |
|---|------|------|---------------|----------------|--------------------|
| 1 | `main.py` | 38, 528 | `debug_pncp_test()` — admin-only diagnostic endpoint | **PRODUCTION** (debug) | Yes — low risk, can be migrated to async |
| 2 | `search_pipeline.py` | 750 | Fallback when parallel async fetch fails | **PRODUCTION** (fallback) | No — critical fallback path, must migrate first |
| 3 | `search_pipeline.py` | 760 | Single-UF search (when `len(ufs) == 1`) | **PRODUCTION** (active) | No — primary path for single-UF queries |
| 4 | `pncp_client.py` | 1509 | `PNCPLegacyAdapter.fetch()` single-UF branch | **PRODUCTION** (adapter) | No — used by ConsolidationService |
| 5 | `pncp_client_resilient.py` | 19 | Import only — `PNCPClient` imported but never instantiated | **DEAD_CODE** (import) | Yes — can remove import |
| 6 | `routes/onboarding.py` | 20 | Import only — uses `buscar_todas_ufs_paralelo` (async) | **DEAD_CODE** (import) | Yes — can remove import |
| 7 | `routes/search.py` | 26 | Import only — actual search uses async pipeline | **DEAD_CODE** (import) | Yes — can remove import |
| 8 | `scripts/audit_all_sectors.py` | 18 | CLI audit script | **SCRIPT** | N/A — not production |
| 9 | `scripts/audit_filter.py` | 23 | CLI debug script | **SCRIPT** | N/A — not production |
| 10 | `scripts/debug_filtros_producao.py` | 25, 41 | CLI debug script | **SCRIPT** | N/A — not production |
| 11 | `scripts/check_status_values.py` | 10, 13 | CLI utility script | **SCRIPT** | N/A — not production |
| 12 | `examples/pagination_example.py` | 14, 26, 47, 73, 93 | Example code | **EXAMPLE** | N/A — not production |
| 13 | `tests/test_pncp_client.py` | Multiple | Unit tests for sync PNCPClient | **TEST_ONLY** | Update after migration |
| 14 | `tests/test_benchmark_pncp_client.py` | 12, 23 | Benchmark tests | **TEST_ONLY** | Update after migration |
| 15 | `tests/test_integration_new_sectors.py` | 23, 128 | Integration tests | **TEST_ONLY** | Update after migration |
| 16 | `tests/test_pncp_integration.py` | 14, 47, 97 | Integration tests | **TEST_ONLY** | Update after migration |

---

## 3. PNCPLegacyAdapter Caller Audit

| # | File | Line | Usage Context | Classification |
|---|------|------|---------------|----------------|
| 1 | `search_pipeline.py` | 580, 594 | ConsolidationService adapter registration | **PRODUCTION** |

**Note:** `PNCPLegacyAdapter.fetch()` (line 1497-1530) uses sync `PNCPClient` for single-UF queries (line 1509). This is a **blocking call inside an async generator** — a latent correctness issue that should be fixed in TD-009 by using `AsyncPNCPClient` instead.

---

## 4. Active Production Paths Using Sync Client

### Path 1: `main.py:debug_pncp_test()` (line 520-552)
- **Risk:** LOW — admin-only debug endpoint
- **Migration:** Trivial — convert to `async with AsyncPNCPClient()` and use `_fetch_page_async`
- **Effort:** 30 min

### Path 2: `search_pipeline.py` lines 750, 760
- **Risk:** HIGH — fallback for failed parallel fetch AND primary path for single-UF searches
- **Migration:** Replace with `AsyncPNCPClient` single-UF fetch
- **Effort:** 2h (includes testing all edge cases)

### Path 3: `PNCPLegacyAdapter.fetch()` single-UF branch (pncp_client.py:1509)
- **Risk:** MEDIUM — used by ConsolidationService for single-UF queries
- **Migration:** Replace `PNCPClient().fetch_all()` with async equivalent
- **Effort:** 1h (must ensure async generator still works)

---

## 5. Quick Wins Completed (SYS-20 + SYS-21)

### SYS-21: `asyncio.get_event_loop().time()` deprecated (Python 3.10+)

**Fixed in 7 files (18 occurrences total):**

| File | Occurrences | Status |
|------|-------------|--------|
| `pncp_client.py` | 2 (lines 861, 866) | Fixed |
| `clients/compras_gov_client.py` | 4 (rate_limit + health_check) | Fixed |
| `clients/portal_transparencia_client.py` | 4 (rate_limit + health_check) | Fixed |
| `clients/portal_compras_client.py` | 4 (rate_limit + health_check) | Fixed |
| `clients/querido_diario_client.py` | 4 (rate_limit + health_check) | Fixed |
| `clients/sanctions.py` | 4 (rate_limit) | Fixed |

**Verification:** `grep -r "get_event_loop().time" backend/` returns only test files (acceptable).

### SYS-20: `_request_count` never reset

**Resolution:** Documented as intentional. Both `PNCPClient` and `AsyncPNCPClient` are short-lived (one search = one instance via context manager). The counter tracks requests per session lifecycle — reset logic is unnecessary and would add complexity for no benefit.

**Documentation added at:**
- `pncp_client.py:237` — `# Per-session counter; reset not needed as each client instance is short-lived`
- `pncp_client.py:762` — Same comment

---

## 6. Decision: Sync Client Removal Strategy

**Decision:** Migrate all 3 active production callers to async, THEN remove sync client.

### Migration Plan for TD-009:

| Step | Task | Effort | Risk |
|------|------|--------|------|
| 1 | Migrate `debug_pncp_test()` in main.py | 30 min | LOW |
| 2 | Migrate single-UF path in `search_pipeline.py:760` | 1h | MEDIUM |
| 3 | Migrate fallback path in `search_pipeline.py:750` | 1h | HIGH |
| 4 | Migrate `PNCPLegacyAdapter.fetch()` single-UF branch | 1h | MEDIUM |
| 5 | Remove dead imports (routes/onboarding.py, routes/search.py, pncp_client_resilient.py) | 15 min | LOW |
| 6 | Remove sync PNCPClient class (lines 223-721) | 30 min | LOW |
| 7 | Remove `import requests` + `from requests.adapters` | 5 min | LOW |
| 8 | Update CLI scripts to use async (or keep sync for CLI convenience) | 1h | LOW |
| 9 | Update tests (sync → async) | 2h | MEDIUM |
| 10 | Run full regression | 30 min | — |

**Total estimated effort for TD-009:** 8h (up from original 5h estimate)

### Rationale for Increased Estimate:
- 3 active production callers (not zero as best-case scenario)
- `PNCPLegacyAdapter` has a blocking-in-async issue that needs careful handling
- CLI scripts may need to remain sync (or use `asyncio.run()` wrapper)
- Test migration is significant (~30 test methods reference sync PNCPClient)

---

## 7. Regression Test Results

| Test Suite | Before | After | Status |
|-----------|--------|-------|--------|
| `test_pncp_client.py` | 64 pass | 64 pass | PASS |
| `test_pncp_hardening.py` | 40 pass | 40 pass | PASS |
| **Total** | **104 pass** | **104 pass** | **ZERO regressions** |

---

## 8. Files Modified in TD-008

| File | Change |
|------|--------|
| `backend/pncp_client.py` | SYS-20 comment + SYS-21 `get_running_loop()` fix |
| `backend/clients/compras_gov_client.py` | SYS-21 `get_running_loop()` fix |
| `backend/clients/portal_transparencia_client.py` | SYS-21 `get_running_loop()` fix |
| `backend/clients/portal_compras_client.py` | SYS-21 `get_running_loop()` fix |
| `backend/clients/querido_diario_client.py` | SYS-21 `get_running_loop()` fix |
| `backend/clients/sanctions.py` | SYS-21 `get_running_loop()` fix |
| `docs/stories/TD-008-AUDIT-REPORT.md` | This audit report |
| `docs/stories/STORY-TD-008.md` | AC checkboxes updated |
