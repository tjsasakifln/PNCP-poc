# GTM-FIX-032: PNCP 422 Date Validation Errors

**Priority:** P0 (causes full search failures for affected UFs)
**Effort:** M (4-6h)
**Origin:** Production logs 2026-02-18, originally GTM-FIX-030 T4 (deferred)
**Status:** OPEN
**Assignee:** @dev
**Tracks:** Backend (5 ACs), Frontend (1 AC), Tests (1 AC)

---

## Problem Statement

PNCP API returns HTTP 422 (Unprocessable Entity) for multiple UF+modality combinations with two distinct error messages. This causes those UF/modality pairs to return 0 PNCP results, degrading search quality or triggering full search failure.

### Error 1: "Data Inicial deve ser anterior ou igual à Data Final"

- **Meaning:** PNCP sees `dataInicial > dataFinal` (dates swapped)
- **Affected:** SP mod=6, PR mod=12, PR mod=7, RS mod=12
- **Expected impossible** with correct 10-day range (`dataInicial=20260208`, `dataFinal=20260218`)

### Error 2: "Período inicial e final maior que 365 dias"

- **Meaning:** PNCP computes date range > 365 days
- **Affected:** MG mod=5, PR mod=1
- **Expected impossible** with 10-day range — implies corrupt/malformed date string reaching PNCP

### Impact

| Scenario | User-Visible Effect |
|----------|---------------------|
| Some UFs fail (partial) | Reduced result count, `is_partial=true` in response |
| Majority of UFs fail | "Não foi possível processar sua busca" error |
| Circuit breaker trips from 422s | ALL subsequent UFs fail (cascade) |
| Only PCP survives | Drastically fewer results (PCP covers ~5% of market) |

---

## Evidence (Production Logs)

All 422s from the same search request — timestamp `2026-02-18T01:06:41.107-02:00` (01:06 BRT):

```
PNCP 422 for UF=SP mod=6 (attempt 1/2). Body: {"message":"Data Inicial deve ser anterior ou igual à Data Final","error":"422 UNPROCESSABLE_ENTITY"}
PNCP 422 for UF=MG mod=5 (attempt 1/2). Body: {"message":"Período inicial e final maior que 365 dias.","error":"422 UNPROCESSABLE_ENTITY"}
PNCP 422 for UF=PR mod=12 (attempt 1/2). Body: {"message":"Data Inicial deve ser anterior ou igual à Data Final","error":"422 UNPROCESSABLE_ENTITY"}
PNCP 422 for UF=PR mod=1 (attempt 1/2). Body: {"message":"Período inicial e final maior que 365 dias.","error":"422 UNPROCESSABLE_ENTITY"}
PNCP 422 for UF=PR mod=7 (attempt 1/2). Body: {"message":"Data Inicial deve ser anterior ou igual à Data Final","error":"422 UNPROCESSABLE_ENTITY"}
PNCP 422 for UF=RS mod=12 (attempt 1/2). Body: {"message":"Data Inicial deve ser anterior ou igual à Data Final","error":"422 UNPROCESSABLE_ENTITY"}
```

**Key observation:** All 422s share the exact same timestamp — this is a single search whose UFs all hit the same PNCP validation issue. The request was at ~01:06 BRT (04:06 UTC), well away from midnight, ruling out simple timezone-boundary date flips.

---

## Root Cause Analysis

### Confirmed Code Flow

The date journey from frontend to PNCP API:

```
Frontend (useSearchFilters.ts L206-214)
  → new Date(new Date().toLocaleString("en-US", { timeZone: "America/Sao_Paulo" }))
  → .toISOString().split("T")[0]                      → "2026-02-08" / "2026-02-18"
  → POST /api/buscar (route.ts — passthrough)
  → Backend BuscaRequest (schemas.py L289-300)
    → Pydantic regex: r"^\d{4}-\d{2}-\d{2}$"          ✅ validated
    → date.fromisoformat() + d_ini <= d_fin check      ✅ validated
  → search_pipeline.py stage_prepare() L403-408
    → abertas mode: date.today().isoformat()           → "2026-02-18"
    → (today - timedelta(days=10)).isoformat()         → "2026-02-08"
  → pncp_client.py _fetch_page_async() L944-946
    → data_inicial.replace("-", "")                    → "20260208"
    → data_final.replace("-", "")                      → "20260218"
  → PNCP API params: dataInicial=20260208, dataFinal=20260218
```

### Hypothesis Ranking

| # | Hypothesis | Likelihood | Evidence |
|---|-----------|------------|----------|
| **H1** | **PNCP API transient validation bug** | **HIGH** | All 422s at identical timestamp; dates provably correct through our validation chain; some UFs+modalities work fine with identical dates; PNCP has history of silent behavior changes (tamanhoPagina 500→50) |
| H2 | Date format corruption via `.replace("-", "")` | LOW | Pydantic regex `^\d{4}-\d{2}-\d{2}$` guarantees exactly `YYYY-MM-DD` input; `replace("-","")` on valid input always produces 8-digit string |
| H3 | Timezone boundary flip (midnight edge) | LOW | Request was at 01:06 BRT (04:06 UTC), not near midnight; both backend `date.today()` and frontend BRT computation would agree on Feb 18 |
| H4 | Frontend double-conversion timezone bug | LOW | The `toLocaleString("en-US", {timeZone})` → `new Date()` → `toISOString()` pattern can shift by ±1 day for users in distant timezones, but backend re-validates and abertas mode recomputes |

### Most Likely Root Cause

**H1: PNCP API intermittent validation bug.** The PNCP server occasionally rejects valid date parameters for specific UF+modality combinations. Our dates pass multiple layers of validation before reaching PNCP. The identical timestamp across all failures suggests PNCP's validation layer had a transient issue.

**However**, even if H1 is the true cause, we should still:
1. Add pre-flight date assertions (defense in depth)
2. Log the exact params on 422 to confirm H1 definitively
3. Improve 422 recovery (don't let transient PNCP bugs cascade)
4. Harden the frontend timezone computation

---

## Current State of 422 Handling

### Async Client (`_fetch_page_async()` — production path)

| Behavior | Status | Location |
|----------|--------|----------|
| 422 retried once | ✅ GTM-FIX-029 | `pncp_client.py:1049-1075` |
| Response body logged (500 chars) | ✅ GTM-FIX-029 | `pncp_client.py:1051` |
| Circuit breaker triggered after retry | ⚠️ **PROBLEM** | `pncp_client.py:1068` |
| Actual params dict logged | ❌ **MISSING** | — |
| Date swap auto-recovery | ❌ **MISSING** | — |
| Modality skip on persistent 422 | ❌ **MISSING** (raises PNCPAPIError) | — |

### Sync Client (`fetch_page()` — health check / legacy)

| Behavior | Status | Location |
|----------|--------|----------|
| 422 retried up to 3x (standard retryable) | ⚠️ No special limit | `pncp_client.py:466-495` |
| Response body logged | ❌ Only on non-retryable | `pncp_client.py:469` |
| Circuit breaker | ❌ Not triggered | — |
| Params dict logged | ❌ | — |

---

## Acceptance Criteria

### AC1 (P0): Diagnostic Logging on 422

**Goal:** Confirm whether our dates are correct when PNCP returns 422.

- [ ] **AC1.1:** In `_fetch_page_async()` L1049-1075: Log the full `params` dict (including formatted `dataInicial`/`dataFinal`, `uf`, `codigoModalidadeContratacao`, `pagina`) on every 422
- [ ] **AC1.2:** In `_fetch_page_async()`: Log the raw (pre-format) `data_inicial` and `data_final` strings alongside the formatted versions
- [ ] **AC1.3:** In `fetch_page()` L466-477 (sync client): Add equivalent 422 diagnostic logging with body preview

**Implementation:**

```python
# pncp_client.py L1049+ (async)
if response.status_code == 422:
    body_preview = response.text[:500] if response.text else "(empty)"
    uf_param = params.get("uf", "?")
    mod_param = params.get("codigoModalidadeContratacao", "?")
    logger.warning(
        f"PNCP 422 for UF={uf_param} mod={mod_param} "
        f"(attempt {attempt + 1}/2). Body: {body_preview}. "
        f"Params: {params}. "  # NEW: full params dict
        f"Raw dates: {data_inicial} → {data_final}"  # NEW: pre-format dates
    )
```

### AC2 (P0): Pre-flight Date Validation

**Goal:** Guarantee dates are valid BEFORE sending to PNCP. Defense in depth.

- [ ] **AC2.1:** In both `_fetch_page_async()` and `fetch_page()`, after L945-946 / L367-368 (date formatting), add assertions:
  1. `len(data_inicial_fmt) == 8` and `len(data_final_fmt) == 8`
  2. `data_inicial_fmt.isdigit()` and `data_final_fmt.isdigit()`
  3. `data_inicial_fmt <= data_final_fmt` (lexicographic comparison works for yyyyMMdd)
- [ ] **AC2.2:** If assertion (3) fails (dates swapped), **swap them** and log a warning (auto-recover)
- [ ] **AC2.3:** If assertions (1) or (2) fail (malformed), raise `ValueError` with descriptive message (don't send garbage to PNCP)

**Implementation:**

```python
# After date formatting (both sync + async)
data_inicial_fmt = data_inicial.replace("-", "")
data_final_fmt = data_final.replace("-", "")

# Pre-flight validation
if len(data_inicial_fmt) != 8 or not data_inicial_fmt.isdigit():
    raise ValueError(f"Malformed data_inicial: '{data_inicial}' → '{data_inicial_fmt}'")
if len(data_final_fmt) != 8 or not data_final_fmt.isdigit():
    raise ValueError(f"Malformed data_final: '{data_final}' → '{data_final_fmt}'")
if data_inicial_fmt > data_final_fmt:
    logger.warning(f"Dates swapped: {data_inicial_fmt} > {data_final_fmt}. Auto-swapping.")
    data_inicial_fmt, data_final_fmt = data_final_fmt, data_inicial_fmt
```

### AC3 (P1): Pipeline Date Normalization

**Goal:** Guarantee dates entering the pipeline are canonical `YYYY-MM-DD`.

- [ ] **AC3.1:** In `search_pipeline.py` `stage_prepare()`, after receiving `ctx.request.data_inicial` / `ctx.request.data_final`: re-parse with `date.fromisoformat()` and re-serialize with `.isoformat()` to guarantee zero-padded format
- [ ] **AC3.2:** In abertas mode (L406): use `datetime.now(timezone.utc).date()` instead of `date.today()` (explicit UTC, no server-timezone dependency)
- [ ] **AC3.3:** Log the normalized dates at INFO level in `stage_prepare()` for traceability

**Implementation:**

```python
# search_pipeline.py stage_prepare()
from datetime import date, timedelta, timezone, datetime

if ctx.request.modo_busca == "abertas":
    today = datetime.now(timezone.utc).date()  # AC3.2: explicit UTC
    ctx.request.data_inicial = (today - timedelta(days=10)).isoformat()
    ctx.request.data_final = today.isoformat()

# AC3.1: Normalize all dates (both abertas and custom)
d_ini = date.fromisoformat(ctx.request.data_inicial)
d_fin = date.fromisoformat(ctx.request.data_final)
ctx.request.data_inicial = d_ini.isoformat()  # Guaranteed YYYY-MM-DD
ctx.request.data_final = d_fin.isoformat()

logger.info(f"stage_prepare: dates normalized to {ctx.request.data_inicial} → {ctx.request.data_final}")
```

### AC4 (P1): Improved 422 Recovery

**Goal:** Don't let PNCP transient 422s cascade to full search failure.

- [ ] **AC4.1:** 422 should **NOT** trigger circuit breaker. Remove `_circuit_breaker.record_failure()` from the 422 handler (L1068). Rationale: 422 is a request-level validation issue (possibly transient on PNCP side), not an indicator that the PNCP API is down. Circuit breaker should only trip on 5xx/timeout patterns.
- [ ] **AC4.2:** After 422 retry exhausted: parse the error message to categorize:
  - `"Data Inicial"` → log + skip modality (return empty result, don't raise)
  - `"maior que 365 dias"` → log + skip modality (return empty result, don't raise)
  - Unknown 422 message → raise `PNCPAPIError` (existing behavior)
- [ ] **AC4.3:** When skipping a modality due to 422, return the standard empty response `{"data": [], "totalRegistros": 0, ...}` instead of raising an exception
- [ ] **AC4.4:** Add Sentry tag `pncp_422_type: date_swap | date_range | unknown` for monitoring

**Implementation:**

```python
# pncp_client.py _fetch_page_async() — after retry exhausted
else:
    logger.warning(
        f"PNCP 422 persisted for UF={uf_param} mod={mod_param} "
        f"after 1 retry. Body: {body_preview}. Params: {params}"
    )
    # AC4.1: NO circuit breaker for 422 (transient validation, not API down)
    # AC4.2: Categorize and handle gracefully
    if "Data Inicial" in body_preview or "365 dias" in body_preview:
        logger.info(
            f"pncp_422_date_skip uf={uf_param} modality={mod_param} "
            f"type={'date_swap' if 'Data Inicial' in body_preview else 'date_range'}"
        )
        # AC4.3: Return empty instead of crashing
        return {
            "data": [],
            "totalRegistros": 0,
            "totalPaginas": 0,
            "paginaAtual": pagina,
            "temProximaPagina": False,
        }
    # Unknown 422 — still raise
    raise PNCPAPIError(
        f"PNCP 422 after 1 retry for UF={uf_param} mod={mod_param}: {body_preview}"
    )
```

### AC5 (P2): Frontend Timezone Hardening

**Goal:** Eliminate the fragile double-conversion date computation pattern.

- [ ] **AC5.1:** In `useSearchFilters.ts` L206-214 and L217-226: Replace the `new Date(new Date().toLocaleString(...))` pattern with a robust approach:

**Current (fragile):**
```typescript
const now = new Date(new Date().toLocaleString("en-US", { timeZone: "America/Sao_Paulo" }));
now.setDate(now.getDate() - 10);
return now.toISOString().split("T")[0];
```

**Proposed (robust):**
```typescript
function getBrtDate(): string {
  // Get current date components in São Paulo timezone
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Sao_Paulo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  return formatter.format(new Date()); // Returns "YYYY-MM-DD" (en-CA locale)
}

function addDays(dateStr: string, days: number): string {
  const d = new Date(dateStr + "T12:00:00Z"); // noon UTC avoids DST edge
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().split("T")[0];
}

// Usage:
const dataFinal = getBrtDate();                // "2026-02-18"
const dataInicial = addDays(dataFinal, -10);   // "2026-02-08"
```

- [ ] **AC5.2:** Extract these helpers to a shared `utils/dates.ts` file (used in 2 places in `useSearchFilters.ts`)

### AC6 (P2): Sync Client 422 Parity

**Goal:** Give `fetch_page()` (sync) the same 422 handling as the async client.

- [ ] **AC6.1:** In `fetch_page()` L466-495: Add explicit 422 handling matching the async client (1 retry max, body logging, graceful skip for date errors, no circuit breaker)
- [ ] **AC6.2:** Extract shared 422 handling logic into a helper function `_handle_422_response(body_preview, uf, mod, attempt)` to avoid duplication

### AC7 (P0): Tests

- [ ] **AC7.1:** Unit test: `_fetch_page_async()` with valid dates → params contain correct `dataInicial`/`dataFinal` format (8 digits)
- [ ] **AC7.2:** Unit test: `_fetch_page_async()` with swapped dates → auto-swaps and logs warning
- [ ] **AC7.3:** Unit test: `_fetch_page_async()` with malformed date (e.g., `"2026-2-8"`) → `ValueError` raised before API call
- [ ] **AC7.4:** Unit test: 422 with "Data Inicial" message → returns empty result (no exception)
- [ ] **AC7.5:** Unit test: 422 with "365 dias" message → returns empty result (no exception)
- [ ] **AC7.6:** Unit test: 422 with unknown message → raises `PNCPAPIError`
- [ ] **AC7.7:** Unit test: 422 does NOT trigger circuit breaker
- [ ] **AC7.8:** Unit test: `stage_prepare()` abertas mode → uses UTC date (mock `datetime.now(timezone.utc)`)
- [ ] **AC7.9:** Unit test: `stage_prepare()` normalizes dates to zero-padded YYYY-MM-DD
- [ ] **AC7.10:** Frontend unit test: `getBrtDate()` returns YYYY-MM-DD format
- [ ] **AC7.11:** Frontend unit test: `addDays()` handles month/year boundaries correctly
- [ ] **AC7.12:** Integration test: full search with 422-returning modality → partial results (not full failure)

---

## Files to Modify

| File | Lines | Changes |
|------|-------|---------|
| `backend/pncp_client.py` | L367-368, L944-946 | AC2: Pre-flight date validation |
| `backend/pncp_client.py` | L1049-1075 | AC1, AC4: Diagnostic logging + graceful 422 recovery |
| `backend/pncp_client.py` | L466-495 | AC6: Sync client 422 parity |
| `backend/search_pipeline.py` | L403-412 | AC3: UTC date computation + normalization |
| `frontend/app/buscar/hooks/useSearchFilters.ts` | L206-226 | AC5: Robust timezone computation |
| `frontend/app/buscar/utils/dates.ts` | NEW | AC5: Shared date helpers |
| `backend/tests/test_pncp_422_dates.py` | NEW | AC7: All backend tests |
| `frontend/__tests__/utils/dates.test.ts` | NEW | AC7: Frontend date tests |

---

## Secondary Issue: Excel 404 / Google Sheets

**NOT in scope for GTM-FIX-032.** Tracked separately.

- First search generated Excel button ("Baixar Excel com 63 licitações") but clicking gave 404
- Google Sheets integration also failed silently (no backend logs)
- Likely download cache expiration or route issue — needs separate investigation

---

## Implementation Order

1. **AC1** (diagnostic logging) — ship first so next production 422 gives us definitive evidence
2. **AC2** (pre-flight validation) — defense in depth, catches any unexpected input
3. **AC4** (graceful 422 recovery) — stops 422 cascade via circuit breaker
4. **AC3** (pipeline date normalization) — eliminates timezone ambiguity
5. **AC6** (sync client parity) — consistency
6. **AC5** (frontend timezone) — hardens the date computation
7. **AC7** (tests) — written alongside each AC above

---

## Success Metrics

| Metric | Before | After |
|--------|--------|-------|
| `pncp_422_count` per search | 4-6 (cascading) | 0-2 (isolated) |
| Circuit breaker trips from 422 | Yes | No |
| Search failure from date 422s | Full failure possible | Graceful partial results |
| Date params logged on 422 | No | Yes (full params dict) |
| Timezone-safe date computation | Fragile (double-conversion) | Robust (Intl.DateTimeFormat) |

---

## Pre-existing Baselines

- **Backend:** ~47 fail / ~3405 pass
- **Frontend:** ~33 fail / ~1764 pass
- **Regressions allowed:** 0
