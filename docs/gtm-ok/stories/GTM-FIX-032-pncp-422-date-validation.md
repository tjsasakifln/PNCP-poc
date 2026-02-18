# GTM-FIX-032: PNCP 422 Date Validation Errors

**Priority:** P0 (causes full search failures)
**Origin:** Production logs 2026-02-18, originally GTM-FIX-030 T4 (deferred)
**Status:** OPEN

---

## Problem Statement

PNCP API returns HTTP 422 for multiple UFs/modalities with two distinct error messages:

### Error 1: "Data Inicial deve ser anterior ou igual à Data Final"
- Dates are arriving **swapped** at the PNCP API
- Seen on: SP mod=6, PR mod=12, PR mod=7, RS mod=12
- Impossible with correct 10-day range (data_inicial=2026-02-08, data_final=2026-02-18)

### Error 2: "Período inicial e final maior que 365 dias"
- Date range > 365 days being sent
- Seen on: MG mod=5, PR mod=1
- Impossible with 10-day range — suggests corrupt/malformed date string

### Impact
- UFs with 422 errors return 0 results (PNCP portion lost)
- When enough UFs fail, entire search returns "Não foi possível processar sua busca"
- Only PCP results survive (no PNCP)

---

## Evidence (Production Logs)

```
PNCP 422 for UF=SP mod=6 (attempt 1/2). Body: {"message":"Data Inicial deve ser anterior ou igual à Data Final","error":"422 UNPROCESSABLE_ENTITY"}
PNCP 422 for UF=MG mod=5 (attempt 1/2). Body: {"message":"Período inicial e final maior que 365 dias.","error":"422 UNPROCESSABLE_ENTITY"}
PNCP 422 for UF=PR mod=12 (attempt 1/2). Body: {"message":"Data Inicial deve ser anterior ou igual à Data Final","error":"422 UNPROCESSABLE_ENTITY"}
PNCP 422 for UF=PR mod=1 (attempt 1/2). Body: {"message":"Período inicial e final maior que 365 dias.","error":"422 UNPROCESSABLE_ENTITY"}
```

Note: All 422s share identical timestamp `2026-02-18T01:06:41.107-02:00` — suspicious batch behavior from PNCP.

---

## Root Cause Hypotheses

### H1: PNCP API yyyyMMdd format corruption
- `data_inicial.replace("-", "")` on non-standard input could produce malformed string
- If frontend sends `"2026-2-8"` (no zero-padding), `.replace("-","")` → `"202628"` (6 chars, not 8)
- PNCP interprets corrupt string as distant date → "maior que 365 dias"

### H2: Timezone boundary date flip
- Frontend computes dates in `America/Sao_Paulo` timezone (UTC-3)
- If request hits backend near midnight BRT, `date.today()` (UTC) could be +1 day ahead
- `data_final` (today UTC) could precede `data_inicial` (today-10 BRT) after timezone edge

### H3: PNCP API intermittent validation bug
- Same timestamp on all 422s suggests PNCP may batch-validate or cache error responses
- Some modalities may have different date validation rules
- Need to log actual `params` dict being sent to confirm

---

## Acceptance Criteria

### AC1 (P0): Add diagnostic logging
- [ ] Log the exact `params` dict (including formatted dates) on every 422 response
- [ ] Log the raw `data_inicial`/`data_final` received from frontend/pipeline

### AC2 (P0): Validate dates before sending to PNCP
- [ ] In `_fetch_page_async()` and `fetch_page()`: assert `data_inicial_fmt <= data_final_fmt` before API call
- [ ] If dates are swapped, swap them and log warning
- [ ] If date format is invalid (not 8 digits), raise clear error

### AC3 (P1): Normalize date inputs
- [ ] Ensure `data_inicial` and `data_final` are always zero-padded YYYY-MM-DD
- [ ] Add `date.fromisoformat()` validation at pipeline entry point
- [ ] Re-serialize with `.isoformat()` to guarantee format

### AC4 (P1): Graceful 422 handling
- [ ] 422 should NOT trigger circuit breaker (it's a request issue, not API down)
- [ ] 422 with "Data Inicial" message should swap dates and retry once
- [ ] 422 with "maior que 365 dias" should log error and skip modality (not crash)

### AC5 (P2): Timezone-safe date computation
- [ ] `stage_prepare()` abertas mode: use `datetime.now(timezone.utc).date()` explicitly
- [ ] Frontend: verify `toISOString().split("T")[0]` produces correct date for BRT timezone

---

## Secondary Issue: Excel 404 / Google Sheets

- First search generated Excel button ("Baixar Excel com 63 licitações") but clicking gave 404
- Google Sheets integration also failed silently (no backend logs)
- Needs separate investigation — may be download cache expiration or route issue

---

## Files to Investigate

- `backend/pncp_client.py` — `_fetch_page_async()` L944-946, `fetch_page()` L367-368
- `backend/search_pipeline.py` — `stage_prepare()` L404-408 (date computation)
- `frontend/app/buscar/hooks/useSearchFilters.ts` — date computation L206-214
- `backend/main.py` — `/buscar` endpoint date validation

## Test Plan

- [ ] Unit test: dates with single-digit month/day (e.g., "2026-2-8")
- [ ] Unit test: dates near midnight UTC (timezone boundary)
- [ ] Unit test: 422 response handling (swap vs skip)
- [ ] Integration test: full search with date validation logging
