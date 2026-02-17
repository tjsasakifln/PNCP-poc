# D01+D04: PNCP Data Pipeline Assessment

## Verdict: CONDITIONAL
## Score: D01 (Core Value Delivery): 6/10
## Score: D04 (Data Reliability): 5/10

---

## Executive Summary

The PNCP data pipeline demonstrates **significant engineering investment** in resilience (circuit breaker, retries, per-modality timeouts, degraded mode, health canary) but suffers from **four structural risks** that could silently deprive paying users of results or deliver incomplete data without adequate user notification.

The pipeline can deliver value under normal conditions but has failure modes where a paying user at R$1,999/month could receive zero results for a valid query with no mechanism to recover or even know data was lost. This is the critical GTM blocker.

---

## Evidence

### Architecture Summary (Traced End-to-End)

**Data Flow:**
1. Frontend `buscar/page.tsx` -> `app/api/buscar/route.ts` (Next.js proxy, 5-min timeout, 2 retries on 503)
2. Proxy -> `POST /v1/buscar` (FastAPI backend)
3. `routes/search.py:buscar_licitacoes()` -> `SearchPipeline.run(ctx)` (7 stages)
4. Stage 3 (`stage_execute`) -> `AsyncPNCPClient.buscar_todas_ufs_paralelo()`
5. Per UF: `_fetch_uf_all_pages()` -> per modality: `_fetch_modality_with_timeout()` -> `_fetch_single_modality()` -> `_fetch_page_async()`
6. Stage 4 (`stage_filter`) -> `aplicar_todos_filtros()` (8-stage filter pipeline)
7. Stage 6 (`stage_generate`) -> LLM summary + Excel generation
8. Response returned with `is_partial`, `failed_ufs`, `degradation_reason` metadata

**Key Parameters (from code):**
- Page size: **20 items** per API call (`pncp_client.py` L294, L876) -- NOT 500 as CLAUDE.md claims
- Max pages per UF+modality: **500** (`pncp_client.py` L625, L1058, L1187) = 10,000 items max per UF+modality combo
- Default modalities: **4** (codes 4, 5, 6, 7 -- `config.py` L32-37)
- Per-modality timeout: **15 seconds** (`pncp_client.py` L48)
- Per-UF timeout: **30 seconds** normal, **45 seconds** degraded (`pncp_client.py` L1324-1325)
- Global fetch timeout: **4 minutes** (`search_pipeline.py` L524)
- Max concurrent UFs: **10** (semaphore, `pncp_client.py` L759)
- Circuit breaker threshold: **20** consecutive failures (`pncp_client.py` L40)
- Circuit breaker cooldown: **120 seconds** (`pncp_client.py` L43)
- Retry config: **3 retries**, base delay 1.5s, max delay 15s, exponential backoff with jitter (`config.py` L48-56)
- Rate limit: **100ms minimum** between requests (`pncp_client.py` L859)
- Date chunking: **30-day** windows (`pncp_client.py` L474)
- Search cache TTL: **4 hours** in InMemoryCache (`search_pipeline.py` L206)

### Failure Mode Matrix

| # | Scenario | Code Path | User Experience | Severity |
|---|----------|-----------|-----------------|----------|
| F1 | PNCP API returns 500 | `_fetch_page_async()` L920-1049: 3 retries with exponential backoff (1.5s, 3s, 6s). After exhaustion raises `PNCPAPIError`. | `_fetch_single_modality()` L1116-1122: catches `PNCPAPIError`, records circuit breaker failure, **breaks page loop** (returns partial items for that modality). Other modalities continue. If entire UF fails, `_fetch_with_callback()` L1354-1358: returns empty list for that UF, emits "failed" status. Frontend shows `FailedUfsBanner` with retry option. | **MEDIUM** -- Graceful degradation works. User sees yellow banner naming failed UFs. Can retry. |
| F2 | PNCP API times out (30s per request) | `_fetch_page_async()` L1027-1036: httpx.TimeoutException caught, retried 3 times. On final failure raises `PNCPAPIError`. Per-modality timeout: `_fetch_modality_with_timeout()` L1126-1178: `asyncio.wait_for()` with 15s timeout + 1 retry after 3s backoff. Per-UF timeout: `_fetch_with_callback()` L1343-1358: 30s timeout. | **Each modality has independent 15s timeout, so one hanging modality does not block others (STORY-252 AC6). Good isolation.** However, circuit breaker fires per timeout occurrence. With 27 UFs x 4 modalities = 108 request slots, threshold of 20 means ~18% failure rate trips the breaker. | **MEDIUM-LOW** -- Well-isolated. Per-modality timeout prevents cascade. |
| F3 | PNCP returns empty for valid query | `_fetch_page_async()` L994-1002: HTTP 204 returns synthetic empty response. `_fetch_single_modality()` returns empty list normally. At pipeline level: `stage_generate()` L974-1023: if zero results after filtering, builds `BuscaResponse` with `resumo.total_oportunidades=0`. Frontend renders `EmptyState` component with "Ajustar busca" button. | **No mechanism to distinguish "PNCP genuinely has no data" from "PNCP returned empty due to transient issue."** For a paying user, a legitimate zero-result is indistinguishable from a silent failure. | **HIGH** -- Critical UX gap. No confidence signal. |
| F4 | PNCP returns 429 (rate limit) | Sync path (`fetch_page()` L357-364): reads `Retry-After` header (default 60s), sleeps, retries. Async path (`_fetch_page_async()` L937-942): same behavior. **No retry count limit on 429** -- the retry loop continues until `max_retries` exhausted. | User sees 503 with "Aguarde X segundos e tente novamente" if `PNCPRateLimitError` propagates. However, `PNCPRateLimitError` is **never raised** in the async path -- it is only declared in `exceptions.py` but never thrown by `_fetch_page_async()`. The 429 handling just sleeps and retries within the normal retry loop. If all 3 retries hit 429, it raises generic `PNCPAPIError`. | **LOW** -- Handled in practice but error type mapping is imprecise. |
| F5 | **Pagination hits max_pages=500** | `_fetch_single_modality()` L1080-1113: loops while `pagina <= max_pages`. At 20 items/page, max = 10,000 items per UF+modality. If exceeded, logs WARNING but **does not propagate truncation info to user**. The `is_partial` flag is only set by UF-level failures, not by pagination truncation. | **SILENT DATA TRUNCATION.** User receives 10,000 items and believes the search is complete. For high-volume UFs like SP with modality 6 (Pregao Eletronico) over 180 days, this cap could be reached. The pipeline log says "Resultados podem estar incompletos" but the user sees nothing. | **CRITICAL** -- Silent data loss for paying users. P0 fix required. |
| F6 | One UF fails, others succeed | `buscar_todas_ufs_paralelo()` L1370: `asyncio.gather(*tasks, return_exceptions=True)`. L1378-1388: failed UFs added to `failed_ufs` list. L1391-1437: **AC7 auto-retry** -- failed UFs retried once after 5s delay with 45s timeout. `ParallelFetchResult` carries `succeeded_ufs` and `failed_ufs`. Frontend shows `FailedUfsBanner` (L320-325 in SearchResults.tsx) and `PartialResultsBanner`. | **GOOD.** User sees explicit banner naming failed UFs with retry button. This is well-implemented. | **LOW** -- Properly handled with user notification and retry. |
| F7 | All UFs fail | If health canary fails: returns `ParallelFetchResult(items=[], succeeded_ufs=[], failed_ufs=list(ufs))` (L1317-1319). Pipeline sets `is_partial=True`. Frontend shows `SourcesUnavailable` component (SearchResults.tsx L267-274) with retry button and suggestion to try later. | **GOOD** for total PNCP failure. However, if canary passes but all UFs subsequently fail, the auto-retry logic (AC7) runs only if `failed_ufs and succeeded_ufs` (L1391) -- **if ALL UFs fail and succeeded_ufs is empty, no retry occurs**. | **MEDIUM** -- Edge case: canary passes but all UFs fail during fetch = no auto-retry. |
| F8 | Search takes >60 seconds | Frontend proxy: 5-minute AbortController timeout (route.ts L92). Backend: 4-minute `asyncio.wait_for()` on fetch (search_pipeline.py L524). SSE progress stream: 30s heartbeats (search.py L107-109). Frontend has `PartialResultsPrompt` at 15s (SearchResults.tsx L194) offering "Ver resultados parciais". | **GOOD UX.** User gets progress updates via SSE, can see partial results after 15s, and has clear timeout errors (504) if the search exceeds limits. | **LOW** -- Well-handled. |
| F9 | Concurrent searches from multiple users | Circuit breaker is a **module-level singleton** (`_circuit_breaker = PNCPCircuitBreaker()` at L170). All concurrent users share the same failure counter. With threshold=20, if user A's 27-UF search causes 20 timeouts, **user B's subsequent search sees the circuit breaker as degraded**. The canary check (`health_canary()` L784-850) would then fire and could return empty results for user B. | **The blast radius is GLOBAL.** One user's aggressive search (27 UFs x 4 modalities x 180 days) can trip the circuit breaker for ALL concurrent users for 120 seconds. The 120s cooldown + `try_recover()` pattern mitigates this, but the window is real. | **HIGH** -- Global circuit breaker cascade affects all users. |

### Data Completeness Risks

**Risk 1: Page Size of 20 with Max 500 Pages = 10,000 Items Cap Per UF+Modality**

- File: `pncp_client.py` L294: `tamanho: int = 20`
- File: `pncp_client.py` L625: `max_pages: int = 500`
- Maximum items per UF+modality combination: 500 pages x 20 items = **10,000 items**
- With 4 default modalities and 30-day date chunking: theoretical max per UF = 10,000 x 4 x N_chunks
- For `modo_busca="abertas"` (180 days): 6 date chunks x 4 modalities x 10,000 = 240,000 per UF (unlikely to hit in practice, but the per-modality cap of 10,000 could be hit for SP/RJ with modality 6)

**Risk 2: Silent Truncation -- No User Notification**

- File: `pncp_client.py` L694-703: When `max_pages` is reached, only a server-side WARNING log is emitted
- The `paginas_restantes` count is logged but **never propagated** to `ParallelFetchResult`, `SearchContext`, or `BuscaResponse`
- The `is_partial` flag in `SearchContext` is only set by UF-level failures (L788-789), NOT by pagination truncation
- **A user searching SP over 180 days could lose thousands of results silently**

**Risk 3: Deduplication Happens at Multiple Levels**

- `_fetch_single_modality()` L1077: deduplicates within a single modality fetch
- `_fetch_uf_all_pages()` L1225: deduplicates across modalities within a UF
- `fetch_all()` (sync) L539: deduplicates across modalities and date chunks
- Deduplication uses `numeroControlePNCP` / `codigoCompra` as key
- This is correct behavior but the dedup counts are not surfaced to the user

**Risk 4: Page Size Mismatch with Documentation**

- CLAUDE.md states "PNCP Pagination: 500 items/page (API max)" -- this is **INCORRECT**
- Actual page size in code: 20 items per page (L294, L876)
- This means 500 pages fetches 10,000 items, not 250,000 as the docs might suggest

### Minimum Result Guarantee

**Current State: NO GUARANTEE EXISTS**

1. **No local data lake or persistent cache**: The `InMemoryCache` (redis_pool.py) is process-local and volatile. It holds search results for 4 hours (search_pipeline.py L206) but is lost on server restart and is not shared across instances.

2. **No date-range expansion strategy**: When results are zero, the pipeline returns zero results. There is no logic to automatically widen the date range or relax filters to find nearby opportunities.

3. **No stale-while-revalidate pattern**: The cache (STORY-257A AC8-10) serves cached results if available and non-expired, but if cache is empty and PNCP is down, the user gets nothing.

4. **Min-match relaxation exists but is narrow**: `stage_filter()` L858-884 relaxes the `min_match_floor` from N to 1 if zero results pass, but only for custom term searches. This does not address the zero-raw-results scenario.

5. **`force_fresh` flag**: The user can opt out of cache (`request.force_fresh`), but there is no inverse -- no way to explicitly request "give me stale data if fresh is unavailable."

**What WOULD Help:**
- A persistent data lake (Supabase/PostgreSQL table) that accumulates PNCP results from every search
- SWR (stale-while-revalidate) cache pattern: serve stale data immediately while refreshing in background
- Date-range expansion: if zero results for 7 days, automatically try 14, 30, 90 days
- Minimum result threshold: if results < N, expand search parameters

### Performance Profile

**Normal Operation (estimated):**
- 1 UF, 7 days: ~4 modalities x ~2-3 pages each = 8-12 API calls x 100ms rate limit = ~2-3 seconds
- 5 UFs, 30 days: 5 UFs in parallel (semaphore permits 10) x 4 modalities x ~5-10 pages = 20-40 API calls per UF = ~5-10 seconds
- 27 UFs, 180 days (max): 27 UFs (batched by semaphore=10) x 4 modalities x 6 date chunks x variable pages. Could easily reach 60-120 seconds. The 4-minute global timeout is the hard limit.

**Theoretical Request Volume for Worst Case (27 UFs x 180 days):**
- 27 UFs x 4 modalities x 6 chunks x ~10 pages average = **6,480 API requests**
- At 100ms minimum interval = **648 seconds** (10.8 minutes) if sequential
- With semaphore=10 parallelism, reduced to ~65 seconds (if PNCP keeps up)
- BUT: per-modality timeout of 15s means many modalities will time out before completing
- **This search profile is likely to trigger the circuit breaker** (>20 timeouts across all UFs)

**Stress Scenario: 5 Concurrent Users Each Searching 10 UFs x 30 Days:**
- Each user: ~10 UFs x 4 mods x 1 chunk x ~5 pages = 200 API calls
- 5 users: 1,000 API calls competing for PNCP rate limit
- Rate limit enforced per-client-instance (not globally), so concurrent users could exceed PNCP's server-side rate limit
- Result: 429 responses, retries, potential circuit breaker trip

---

## Critical Gaps (CONDITIONAL Verdict Rationale)

### P0: Silent Data Truncation at max_pages=500

**Location:** `pncp_client.py` L694-703, L1106-1112
**Impact:** Paying users lose data silently. For SP over 180 days, modality 6 could have >10,000 results.
**Fix Required:** Propagate `paginas_restantes > 0` as a truncation flag through `ParallelFetchResult` -> `SearchContext` -> `BuscaResponse`. Show yellow banner in frontend: "Resultados limitados a 10.000 por estado/modalidade. Para resultados completos, reduza o periodo."
**Effort:** ~4 hours (backend field propagation + frontend banner)

### P0: Global Circuit Breaker Cascade

**Location:** `pncp_client.py` L170 (singleton), L119-124 (threshold=20)
**Impact:** One user's aggressive search can block all users for 120 seconds.
**Fix Required:**
- Option A: Per-user circuit breaker (keyed by user_id)
- Option B: Raise threshold to ~50 (since 27 UFs x 4 modalities = 108 request slots, 20 is too low)
- Option C: Only count 5xx errors toward threshold (not timeouts from user's own aggressive parameters)
**Effort:** Option B = 5 minutes (env var change). Option A = ~8 hours.

### P1: No Minimum Result Guarantee

**Location:** `search_pipeline.py` stage_execute + stage_generate
**Impact:** Paying user gets "0 resultados" with no way to recover when PNCP is transiently empty.
**Fix Required:** Implement SWR pattern -- serve cached results with "dados de X horas atras" banner when fresh fetch returns empty. Already have InMemoryCache with 4h TTL; just need logic to prefer stale cache over empty fresh results.
**Effort:** ~4 hours

### P1: Zero-Result Ambiguity

**Location:** `search_pipeline.py` L974-1023
**Impact:** User cannot distinguish "genuinely no procurement in this sector/period" from "PNCP returned empty due to transient issue."
**Fix Required:** Add confidence signal. If PNCP returned HTTP 200 with data=[] (as opposed to failing), mark `confidence="high"`. If PNCP had errors/timeouts, mark `confidence="low"` with explanation.
**Effort:** ~2 hours

### P2: Page Size Inefficiency

**Location:** `pncp_client.py` L294, L876
**Impact:** Using page size 20 instead of the PNCP API maximum (likely 500 based on CLAUDE.md docs) means 25x more API calls than necessary, increasing latency and rate limit pressure.
**Investigation Required:** Verify PNCP API's actual maximum `tamanhoPagina`. If 500 is supported, changing from 20 to 500 would reduce API calls by 96% and dramatically improve performance and reliability.
**Effort:** ~1 hour (test + change)

---

## Positive Findings

1. **Circuit breaker pattern** is well-implemented with degraded mode, health canary, cooldown, and automatic recovery (STORY-252, STORY-257A). The engineering quality is high.

2. **Per-modality timeout isolation** (STORY-252 AC6) prevents one slow modality from blocking others. This is a strong resilience pattern.

3. **Auto-retry for failed UFs** (STORY-257A AC7) with population-priority ordering is thoughtful.

4. **Frontend degradation UI** (DegradationBanner, FailedUfsBanner, PartialResultsBanner, SourcesUnavailable) provides good user communication for detected failures.

5. **SSE progress tracking** gives users real-time feedback during long searches, with partial results prompt at 15 seconds.

6. **7-stage pipeline decomposition** (STORY-216) is clean and well-structured with independent error boundaries per stage.

7. **Search caching** (STORY-257A AC8-10) with 4h TTL and `force_fresh` flag reduces PNCP load for repeated queries.

8. **Exponential backoff with jitter** prevents thundering herd on retries.

---

## Conditions for PASS

The verdict upgrades to PASS when all P0 items are resolved:

1. [ ] Silent truncation is surfaced to the user (P0)
2. [ ] Circuit breaker cascade risk is mitigated (P0)
3. [ ] Page size is verified and optimized (P2 -- needed to validate truncation risk)

P1 items (minimum result guarantee, zero-result ambiguity) are recommended but not blocking for GTM.

---

## Files Referenced

| File | Lines | Evidence |
|------|-------|----------|
| `backend/pncp_client.py` | L39-44 | Circuit breaker config (threshold=20, cooldown=120s) |
| `backend/pncp_client.py` | L70-176 | PNCPCircuitBreaker class |
| `backend/pncp_client.py` | L287-295 | fetch_page: page_size=20 |
| `backend/pncp_client.py` | L618-707 | _fetch_by_uf: max_pages=500, silent truncation warning |
| `backend/pncp_client.py` | L869-1049 | _fetch_page_async: async retry logic |
| `backend/pncp_client.py` | L1051-1124 | _fetch_single_modality: per-modality pagination |
| `backend/pncp_client.py` | L1126-1178 | _fetch_modality_with_timeout: 15s timeout + 1 retry |
| `backend/pncp_client.py` | L1180-1242 | _fetch_uf_all_pages: parallel modalities per UF |
| `backend/pncp_client.py` | L1244-1449 | buscar_todas_ufs_paralelo: orchestration + auto-retry |
| `backend/search_pipeline.py` | L247-306 | SearchPipeline.run: 7-stage orchestration |
| `backend/search_pipeline.py` | L480-538 | stage_execute: PNCP fetch + cache |
| `backend/search_pipeline.py` | L714-815 | _execute_pncp_only: circuit breaker + timeout |
| `backend/search_pipeline.py` | L820-924 | stage_filter: aplicar_todos_filtros call |
| `backend/search_pipeline.py` | L959-1133 | stage_generate: LLM + Excel + response building |
| `backend/routes/search.py` | L147-245 | buscar_licitacoes wrapper: exception mapping |
| `backend/filter.py` | L682-814 | match_keywords: exclusion-first, context validation |
| `backend/filter.py` | L1736-1935 | aplicar_todos_filtros: 8-stage filter pipeline |
| `backend/config.py` | L32-37 | DEFAULT_MODALIDADES: [4, 5, 6, 7] |
| `backend/config.py` | L48-69 | RetryConfig: 3 retries, 1.5s base, 15s max, 30s timeout |
| `backend/redis_pool.py` | L1-80 | InMemoryCache with LRU eviction (10K max) |
| `backend/search_context.py` | L1-73 | SearchContext dataclass with partial result fields |
| `backend/exceptions.py` | L1-26 | Exception hierarchy (PNCPRateLimitError never raised in async) |
| `frontend/app/api/buscar/route.ts` | L1-249 | API proxy: 5-min timeout, 2 retries on 503 |
| `frontend/app/buscar/components/SearchResults.tsx` | L267-345 | Degradation UI: banners for partial/failed/empty states |

---

*Assessment prepared: 2026-02-16*
*Assessor: Claude Opus 4.6 (GTM-OK Phase 1, Dimension D01+D04)*
