# AUDIT FRENTE 1 -- CODEBASE ARCHITECTURE

**Auditor:** @architect
**Date:** 2026-02-12
**Scope:** Full backend (Python) + frontend (TypeScript) codebase
**Methodology:** Line-by-line read of every source file, pattern-based grep, dependency analysis
**Files analyzed:** ~50 backend Python files, ~90 frontend TypeScript files

---

## Executive Summary

The SmartLic codebase is a functional product with strong domain logic (filtering, synonym matching, LLM arbiter) and good security practices (PII sanitization, JWT validation, input validation). However, **it carries significant structural debt** from rapid feature development that threatens GTM stability.

**Top 3 structural risks:**

1. **God Function** (`buscar_licitacoes` in `routes/search.py`) -- 860+ lines of sequential logic with 12+ inline imports, an inline class definition, and 4+ duplicated patterns. Any change to search flow requires modifying this single function, and a single exception anywhere corrupts the entire response.

2. **Dual Redis Clients** -- Three separate Redis connection strategies coexist: `redis_client.py` (async, for progress/pub-sub), `cache.py` (sync, for feature flags/Stripe), and `routes/features.py` (creates a new connection per request). This wastes connections, creates inconsistent fallback behavior, and risks subtle bugs.

3. **Backend-Frontend Contract Mismatch** -- The frontend API proxy (`api/buscar/route.ts`) cherry-picks fields from the backend response, silently dropping `source_stats`, `hidden_by_min_match`, and `filter_relaxed`. Any backend field additions are invisible to the frontend until manually added.

**Severity Distribution:**

| Severity | Count |
|----------|-------|
| CRITICAL | 3     |
| HIGH     | 8     |
| MEDIUM   | 12    |
| LOW      | 9     |
| **Total** | **32** |

---

## CRITICAL RISKS

### CRIT-01: God Function -- `buscar_licitacoes()` (routes/search.py)

**File:** `backend/routes/search.py`
**Lines:** ~130-990 (~860 lines)
**Impact:** Unmaintainable, untestable, single point of failure

This function handles the entire search lifecycle in one monolithic block:
- Request validation and quota checking (lines 130-250)
- Plan capability resolution with 4-level fallback (lines 251-405)
- Search term parsing and sector configuration (lines 406-539)
- Inline class definition `_PNCPLegacyAdapter` (lines 540-582)
- PNCP API calls with multi-source consolidation (lines 583-680)
- Filtering pipeline: keywords, status, modality, sphere, value (lines 681-780)
- LLM arbiter integration with density thresholds (lines 781-850)
- Relevance scoring and minimum match filtering (lines 851-890)
- Result sorting, deduplication, pagination (lines 891-920)
- Excel generation and storage upload (lines 921-960)
- LLM summary generation (lines 961-980)
- Session saving and response building (lines 981-990)

**Specific violations:**
- 12+ deferred imports inside the function body
- Inline class `_PNCPLegacyAdapter` defined mid-function
- Duplicated quota fallback logic (identical code in `routes/user.py` lines 62-85)
- Duplicated link building logic (also in `excel.py`)
- No intermediate error boundaries -- a failure at line 850 loses all prior computation
- Cyclomatic complexity estimated at 50+ (branching on plan type, sector, filter options, LLM flags)

**Proposed story:** REFACTOR-01 -- Decompose `buscar_licitacoes` into SearchPipeline with stage pattern

---

### CRIT-02: Dual/Triple Redis Client Architecture

**Files:** `backend/redis_client.py`, `backend/cache.py`, `backend/routes/features.py`
**Impact:** Connection pool exhaustion, inconsistent fallback, wasted resources

Three independent Redis connection strategies exist:

| File | Type | Purpose | Connection |
|------|------|---------|------------|
| `redis_client.py` | `redis.asyncio` | Progress pub/sub | Lazy singleton, async |
| `cache.py` | `redis` (sync) | Feature flags, Stripe cache | Eager singleton, sync, pool=10 |
| `routes/features.py` | `redis` (sync) | Feature flag cache | **New connection per request** |

Problems:
- `routes/features.py` line 51 creates a **new Redis connection on every GET /api/features/me** call, ignoring the existing `cache.py` singleton entirely
- `redis_client.py` uses `asyncio.run()` inside `get_redis()` to test the connection (line 56), which will **crash if called from within an already-running event loop** (which FastAPI always has)
- `cache.py` and `redis_client.py` have incompatible client types (sync vs async) for what is logically the same Redis server
- Fallback behavior differs: `redis_client.py` falls back to None, `cache.py` falls back to `InMemoryCache`, `features.py` falls back to direct DB query

**Proposed story:** REFACTOR-02 -- Unify Redis into single async client with connection pool

---

### CRIT-03: Backend-Frontend Contract Mismatch

**Files:** `backend/routes/search.py` (response), `frontend/app/api/buscar/route.ts` (proxy), `frontend/app/types.ts` (types)
**Impact:** Silent data loss, debugging nightmares, feature breakage

The frontend API proxy at `frontend/app/api/buscar/route.ts` lines 216-229 manually constructs the response, cherry-picking only known fields:

```typescript
return NextResponse.json({
  resumo: data.resumo,
  licitacoes: data.licitacoes || [],
  download_id: downloadId,
  download_url: downloadUrl,
  total_raw: data.total_raw || 0,
  total_filtrado: data.total_filtrado || 0,
  filter_stats: data.filter_stats || null,
  termos_utilizados: data.termos_utilizados || null,
  stopwords_removidas: data.stopwords_removidas || null,
  excel_available: data.excel_available || false,
  upgrade_message: data.upgrade_message || null,
  ultima_atualizacao: data.ultima_atualizacao || null,
});
```

**Dropped fields** (present in backend response but silently discarded):
- `source_stats` (multi-source consolidation metrics)
- `hidden_by_min_match` (minimum match filtering count)
- `filter_relaxed` (whether zero-results relaxation was applied)
- `synonym_matches` (synonym-based recovery results)
- `llm_arbiter_stats` (LLM classification statistics)

Additionally, `frontend/app/types.ts` defines `Resumo.distribuicao_uf` which does NOT exist in the backend `ResumoLicitacoes` Pydantic model, causing potential runtime mismatches.

**Proposed story:** REFACTOR-03 -- Implement shared API contract with auto-generated TypeScript types from OpenAPI schema

---

## HIGH RISKS

### HIGH-01: Blocking `time.sleep()` in Async Context

**File:** `backend/authorization.py` line 87
**Impact:** Event loop blocking, request latency spikes

`_check_user_roles()` calls `time.sleep(0.3)` for retry delay inside a function that is invoked from async FastAPI route handlers. This blocks the entire async event loop for 300ms, affecting all concurrent requests.

```python
# authorization.py line 87
time.sleep(0.3)  # BLOCKS EVENT LOOP
```

Similarly, `pncp_client.py` uses `time.sleep()` throughout its sync client (lines 126, 200, 215, 234, 279, 297), but this is mitigated because the sync client is typically called via `asyncio.to_thread()` in the search pipeline.

**Proposed story:** FIX-01 -- Replace `time.sleep()` with `asyncio.sleep()` in all async-reachable code paths

---

### HIGH-02: Token Cache Hash Collision Risk

**File:** `backend/auth.py` line ~60
**Impact:** Cross-user authentication leaks

The JWT token cache uses only the first 16 characters of the token for the cache key:

```python
token_hash = hashlib.sha256(token[:16].encode()).hexdigest()
```

JWT tokens sharing the same first 16 characters (e.g., tokens from the same Supabase project during the same time window) would collide, causing one user to receive another user's cached auth result. Supabase JWTs start with `eyJhbGciOiJIUzI1NiIs` (always the same 20 chars for HS256), making collisions **guaranteed** for same-project tokens.

**Proposed story:** FIX-02 -- Hash full token for cache key (performance impact: negligible for SHA256)

---

### HIGH-03: Dead Code in Quota System

**File:** `backend/quota.py` line 402
**Impact:** Confusing maintainability, indicates incomplete refactoring

```python
sb.rpc(...).execute() if False else None  # DEAD CODE
```

An entire RPC call branch is disabled with `if False`. This suggests an incomplete migration or abandoned feature. The dead code obscures the actual execution path and could confuse future developers.

Additionally, `decrement_credits()` function is still present but deprecated, and `save_search_session()` lives in `quota.py` despite having no relation to quota management (SRP violation).

**Proposed story:** CLEANUP-01 -- Remove dead code from quota.py, move `save_search_session` to sessions module

---

### HIGH-04: `asyncio.run()` Inside Async Event Loop

**File:** `backend/redis_client.py` line 56
**Impact:** RuntimeError crash in production

```python
asyncio.run(_redis_client.ping())  # CRASHES if event loop already running
```

`asyncio.run()` creates a new event loop and fails if one already exists. Since FastAPI runs inside uvicorn's event loop, calling `get_redis()` from any async context will raise `RuntimeError: This event loop is already running`. This only works during module import (before the event loop starts) and would crash if Redis reconnection is attempted during runtime.

**Proposed story:** FIX-03 -- Replace `asyncio.run()` with proper async initialization pattern

---

### HIGH-05: Stripe API Key Set at Module Level (Non-Thread-Safe)

**Files:** `backend/webhooks/stripe.py` line 44, `backend/routes/billing.py`
**Impact:** Race condition in concurrent webhook processing

```python
# webhooks/stripe.py line 44
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
```

Setting `stripe.api_key` as a global module attribute is not thread-safe. If multiple webhook handlers execute concurrently (e.g., in a multi-worker uvicorn), one could overwrite the key while another is mid-request. Additionally, `routes/billing.py` sets the API key per-request, creating inconsistency.

**Proposed story:** FIX-04 -- Use per-request Stripe client instances

---

### HIGH-06: Filesystem-Based Excel Download in Serverless Context

**File:** `frontend/app/api/buscar/route.ts` lines 180-213
**Impact:** Downloads fail in serverless/multi-instance deployments

The frontend writes Excel files to `/tmp/` filesystem and sets a 60-minute `setTimeout` for cleanup. This pattern:
- Fails when multiple frontend instances exist (download request hits different instance than the one that wrote the file)
- Leaks file handles in long-running processes (setTimeout cleanup is unreliable)
- Has no size limit enforcement (could fill tmp partition)
- Is already partially superseded by object storage (`download_url` field), but the filesystem path remains as fallback

**Proposed story:** CLEANUP-02 -- Remove filesystem Excel fallback, rely exclusively on object storage URLs

---

### HIGH-07: Deprecated FastAPI Patterns

**File:** `backend/main.py` line 136
**Impact:** Will break in future FastAPI versions

```python
@app.on_event("startup")  # DEPRECATED since FastAPI 0.103
```

`on_event("startup")` is deprecated in favor of the lifespan context manager. This will emit deprecation warnings and eventually be removed.

**Proposed story:** FIX-05 -- Migrate to FastAPI lifespan context manager

---

### HIGH-08: Dual Router Mounting Doubles Route Surface

**File:** `backend/main.py` lines 90-121
**Impact:** Doubled attack surface, confusion about canonical URLs

Every router is mounted twice -- once with `/v1/` prefix and once without:

```python
app.include_router(search_router, prefix="/v1")  # Versioned
app.include_router(search_router)                  # Legacy
```

This doubles the registered route count (from ~30 to ~60), doubles the attack surface, and creates ambiguity about which path is canonical. There is no deprecation header or logging on the legacy paths.

**Proposed story:** CLEANUP-03 -- Add deprecation warnings to legacy routes, plan migration timeline

---

## MEDIUM RISKS

### MED-01: 35 Deferred Supabase Imports Across 18 Files

Every file that uses Supabase does `from supabase_client import get_supabase` inside function bodies. While this prevents circular imports, it indicates a coupling problem. The Supabase client should be injected via FastAPI dependency injection.

**Files affected:** admin.py, quota.py, routes/search.py, routes/user.py, routes/billing.py, routes/sessions.py, routes/analytics.py, routes/plans.py, routes/features.py, routes/subscriptions.py, routes/messages.py, webhooks/stripe.py, authorization.py, and 5 others.

### MED-02: Duplicate Sync/Async Client Code in pncp_client.py

`backend/pncp_client.py` (1032 lines) contains both `PNCPClient` (sync) and `AsyncPNCPClient` (async) with ~150 lines of nearly identical retry logic duplicated between them. The `_fetch_page_async` method reimplements delay calculation instead of reusing the existing `calculate_delay()` utility.

### MED-03: `Optional[any]` Type Annotations in Backend

**Files:** `redis_client.py` (lines 14, 18), `rate_limiter.py` (line 31), `progress.py` (line 228)

Using `any` (lowercase) instead of `Any` (from typing) is technically valid Python but defeats the purpose of type annotations. These should use proper types (`redis.asyncio.Redis | None`).

### MED-04: Frontend `any` Types (8 occurrences)

| File | Line | Usage |
|------|------|-------|
| `dashboard/page.tsx` | 168 | `ChartTooltip({ active, payload, label }: any)` |
| `dashboard/page.tsx` | 173 | `payload.map((entry: any, ...)` |
| `dashboard/page.tsx` | 239 | `catch (err: any)` |
| `buscar/hooks/useSearch.ts` | 85 | `sseEvent: any` |
| `buscar/components/SearchResults.tsx` | 21 | `sseEvent: any` |
| `components/MunicipioFilter.tsx` | 40 | `(...args: any[]) => any` |
| `components/MunicipioFilter.tsx` | 113 | `data.map((m: any) => ...)` |
| `components/OrgaoFilter.tsx` | 37 | `(...args: any[]) => any` |

### MED-05: `dateDiffInDays` Duplicated Across Files

The function `dateDiffInDays` is defined in both `frontend/app/buscar/page.tsx` (line 26) and `frontend/app/buscar/hooks/useSearch.ts`. Should be extracted to a shared utility.

### MED-06: No Error Boundary Beyond Root

Only `frontend/app/error.tsx` exists (root-level error boundary). No route-specific error boundaries for `/buscar`, `/dashboard`, `/admin`, etc. A crash in the dashboard chart component takes down the entire page rather than showing a localized error.

### MED-07: InMemoryCache Has No Size Limit

**File:** `backend/cache.py` `InMemoryCache` class
Unlike `rate_limiter.py` which has LRU eviction at 10,000 entries, `InMemoryCache` in `cache.py` grows unbounded. In development mode (no Redis), this could lead to memory leaks over long-running sessions.

### MED-08: `_` Prefix Functions Used Cross-Module

**File:** `backend/authorization.py`
Functions `_check_user_roles()`, `_get_admin_ids()` use underscore prefix (Python convention for private), but are imported and used by `routes/search.py` and `admin.py`. This creates a false expectation that these are internal.

### MED-09: Plan Capabilities Hardcoded in If/Elif Chain

**File:** `backend/quota.py`, `_load_plan_capabilities_from_db()` function
Plan-specific logic is embedded in an if/elif chain:
```python
if plan_id == "consultor_agil":
    caps["allow_excel"] = True
elif plan_id == "maquina":
    ...
```
This violates Open-Closed Principle. Adding a new plan requires modifying this function.

### MED-10: `response.text()` on Already-Consumed Response Body

**File:** `frontend/app/api/buscar/route.ts` line 168
The response body is consumed by `response.json()` and then `response.text()` is called on error paths. Calling `.text()` after `.json()` on the same Response object will return empty string since the body stream is already consumed.

### MED-11: Module-Level Feature Flags Not Reloadable

**File:** `backend/config.py` lines 164-220
All feature flags (`ENABLE_NEW_PRICING`, `LLM_ARBITER_ENABLED`, etc.) are evaluated once at import time as module-level constants. Changing an environment variable requires a full application restart. For a GTM product, runtime feature flag toggling is valuable.

### MED-12: Sectors.py is 1600+ Lines of Static Data

**File:** `backend/sectors.py`
Contains 12 sector configurations with hundreds of keywords and exclusions totaling 1600+ lines. This should be moved to a configuration file (YAML/JSON) loaded at startup, not hardcoded in Python source.

---

## DETAILED FINDINGS

### Backend Architecture

#### Module Dependency Map (Simplified)

```
main.py
  -> config.py -> middleware.py (circular: setup_logging imports RequestIDFilter)
  -> routes/search.py -> filter.py, relevance.py, term_parser.py, synonyms.py,
                          llm_arbiter.py, status_inference.py, pncp_client.py,
                          excel.py, llm.py, quota.py, progress.py, storage.py,
                          supabase_client.py, sectors.py
  -> routes/user.py -> quota.py, supabase_client.py
  -> routes/billing.py -> services/billing.py, supabase_client.py
  -> webhooks/stripe.py -> cache.py, supabase_client.py (imports at module level, not deferred)
  -> admin.py -> supabase_client.py, log_sanitizer.py, schemas.py
```

**Circular risk:** `config.py` imports `middleware.RequestIDFilter` at function call time (`setup_logging()`), and `middleware.py` uses `logging` which is configured by `config.setup_logging()`. This works only because `setup_logging()` is called after both modules are loaded.

#### SOLID Analysis

| Principle | Rating | Key Violations |
|-----------|--------|----------------|
| **S** - Single Responsibility | D | `routes/search.py`: search + filtering + Excel + LLM + quota + session save. `quota.py`: quota + session save + plan capabilities |
| **O** - Open/Closed | D | Plan capabilities hardcoded in if/elif chain. Adding sectors requires modifying `sectors.py` source code |
| **L** - Liskov Substitution | B | Good: `_PNCPLegacyAdapter` wraps sync client for async interface |
| **I** - Interface Segregation | C | No formal interfaces/protocols defined. Adapters in `clients/` inherit from `BaseClient` ABC (good) |
| **D** - Dependency Inversion | D | 35 deferred imports of concrete `get_supabase()`. No dependency injection. Global mutable state (`_supabase_client`, `_redis_client`, `_arbiter_cache`, `_active_trackers`, `rate_limiter`) |

#### Dead Code Identified

| File | Line | Description |
|------|------|-------------|
| `quota.py` | 402 | `if False else None` disables entire RPC branch |
| `quota.py` | ~600 | `decrement_credits()` -- deprecated, never called |
| `filter.py` | ~130 | `remove_stopwords()` -- superseded by `validate_terms()` |
| `pncp_client.py` | ~500 | `calculate_delay()` utility exists but `_fetch_page_async` reimplements delay inline |

#### Global Mutable State

| Variable | File | Risk |
|----------|------|------|
| `_supabase_client` | `supabase_client.py` | Singleton, acceptable |
| `_redis_client` | `redis_client.py` | Singleton with `asyncio.run()` crash risk |
| `redis_client` | `cache.py` | Eager global singleton |
| `rate_limiter` | `rate_limiter.py` | Eager global singleton |
| `_arbiter_cache` | `llm_arbiter.py` | Unbounded in-memory dict (no eviction) |
| `_active_trackers` | `progress.py` | Dict grows with active searches |
| `_client` (OpenAI) | `llm_arbiter.py` | Lazy singleton, acceptable |

---

### Frontend Architecture

#### Component Structure

The frontend follows a reasonable App Router structure:
```
app/
  page.tsx              (landing page)
  buscar/
    page.tsx            (main search page - large, ~500+ lines)
    hooks/useSearch.ts  (521 lines - search lifecycle hook)
    hooks/useSearchFilters.ts (filter state management)
    components/         (SearchForm, SearchResults, etc.)
  dashboard/page.tsx    (analytics dashboard)
  admin/page.tsx        (admin panel)
  components/           (shared components)
  api/buscar/route.ts   (API proxy - 239 lines)
```

#### State Management

- Uses React hooks + Context (AuthProvider, ThemeProvider)
- No external state library (Redux, Zustand) -- acceptable for current size
- `useSearch.ts` at 521 lines is approaching the threshold where a state machine (XState) or reducer would improve clarity
- Ref-based circular dependency break between `useSearchFilters` and `useSearch` (page.tsx line 53-56) is fragile

#### API Layer

- Backend URL comes from `NEXT_PUBLIC_BACKEND_URL` env var
- API proxy (`api/buscar/route.ts`) adds authentication header and proxies to backend
- **No request/response type validation** on the proxy layer -- raw `data = await response.json()` with manual field picking
- No retry logic on frontend API calls
- SSE connection for progress has graceful fallback to time-based simulation

#### Error Boundary Coverage

| Route | Error Boundary | Status |
|-------|---------------|--------|
| `/` (root) | `app/error.tsx` | Exists (generic) |
| `/buscar` | None | Missing |
| `/dashboard` | None | Missing |
| `/admin` | None | Missing |
| `/cadastro` | None | Missing |

#### Type Safety Score

- **Overall:** B-
- Strict mode enabled in tsconfig
- 8 `any` type occurrences in production code
- `BuscaResult.download_id` typed as `string` but can be `null`
- `Resumo.distribuicao_uf` exists in frontend types but not in backend schema
- Good type coverage in `types.ts` for API response interfaces

---

### Cross-Cutting Concerns

#### Environment Variable Inventory

| Variable | Backend | Frontend | Default | Notes |
|----------|---------|----------|---------|-------|
| `SUPABASE_URL` | Required | `NEXT_PUBLIC_` | None | Must match |
| `SUPABASE_SERVICE_ROLE_KEY` | Required | N/A | None | Backend only |
| `SUPABASE_ANON_KEY` | Optional | `NEXT_PUBLIC_` | None | JWT validation |
| `OPENAI_API_KEY` | Required | N/A | None | LLM features |
| `STRIPE_SECRET_KEY` | Required | N/A | None | Billing |
| `STRIPE_WEBHOOK_SECRET` | Required | N/A | None | Webhook auth |
| `REDIS_URL` | Optional | N/A | None | 3 different consumers |
| `CORS_ORIGINS` | Optional | N/A | localhost | Production domains auto-added |
| `LLM_ARBITER_ENABLED` | Optional | N/A | `true` | Feature flag |
| `ENABLE_NEW_PRICING` | Optional | N/A | `true` | Feature flag |
| `ADMIN_USER_IDS` | Optional | N/A | Empty | CSV of UUIDs |

**Risk:** No validation that required env vars are present at startup. Missing `OPENAI_API_KEY` only fails when LLM is first called, not at boot.

#### Dependency Health

**Backend (`requirements.txt`):**
- FastAPI 0.115.9 -- current stable
- Pydantic 2.12.5 -- current
- OpenAI 1.109.1 -- current
- Supabase 2.13.0 -- current
- httpx 0.28.1 -- current
- **Pinned versions** -- good for reproducibility

**Frontend (`package.json`):**
- Next.js 16.1.6 -- current
- React 18.3.1 -- current (React 19 available but risky to upgrade pre-GTM)
- 14 direct dependencies -- reasonable
- **Uses caret ranges** (`^`) -- could break on minor version bumps
- `@types/uuid` in dependencies (should be devDependencies)

#### Security Posture

| Category | Rating | Notes |
|----------|--------|-------|
| Input validation | A | Pydantic models, UUID validation, search sanitization |
| Authentication | B+ | JWT with local validation, 60s cache (collision risk HIGH-02) |
| Authorization | B | Admin/master role checks, but `_` prefix naming is misleading |
| PII protection | A | Comprehensive `log_sanitizer.py` with email, token, phone masking |
| SQL injection | A | PostgREST operator stripping, parameterized queries |
| CORS | B | Proper configuration, but wildcard only warned (not blocked) |
| Secret management | B | Env vars only, no validation at startup |
| XSS | C | `format_resumo_html()` in `llm.py` generates raw HTML strings |

---

## Proposed Stories

### Priority 1 (Pre-GTM Critical)

| ID | Title | Risk Addressed | Effort |
|----|-------|---------------|--------|
| REFACTOR-01 | Decompose `buscar_licitacoes` into SearchPipeline | CRIT-01 | 3 days |
| REFACTOR-02 | Unify Redis into single async client | CRIT-02 | 2 days |
| FIX-02 | Hash full JWT token for cache key | HIGH-02 | 0.5 day |
| FIX-03 | Fix `asyncio.run()` in redis_client.py | HIGH-04 | 0.5 day |

### Priority 2 (Pre-GTM Important)

| ID | Title | Risk Addressed | Effort |
|----|-------|---------------|--------|
| REFACTOR-03 | Shared API contract (OpenAPI -> TypeScript) | CRIT-03 | 2 days |
| FIX-01 | Replace blocking `time.sleep()` in async code | HIGH-01 | 0.5 day |
| FIX-04 | Use per-request Stripe client instances | HIGH-05 | 0.5 day |
| FIX-05 | Migrate to FastAPI lifespan | HIGH-07 | 0.5 day |
| CLEANUP-01 | Remove dead code from quota.py | HIGH-03 | 0.5 day |

### Priority 3 (Post-GTM Polish)

| ID | Title | Risk Addressed | Effort |
|----|-------|---------------|--------|
| CLEANUP-02 | Remove filesystem Excel fallback | HIGH-06 | 1 day |
| CLEANUP-03 | Deprecation warnings on legacy routes | HIGH-08 | 1 day |
| REFACTOR-04 | Extract sectors to YAML configuration | MED-12 | 1 day |
| REFACTOR-05 | Add route-specific error boundaries | MED-06 | 1 day |
| REFACTOR-06 | Dependency injection for Supabase | MED-01 | 2 days |
| CLEANUP-04 | Eliminate `any` types in frontend | MED-04 | 0.5 day |
| CLEANUP-05 | Extract `dateDiffInDays` to shared util | MED-05 | 0.25 day |
| REFACTOR-07 | Data-driven plan capabilities (OCP) | MED-09 | 1 day |
| FIX-06 | Add size limit to InMemoryCache | MED-07 | 0.25 day |
| FIX-07 | Validate required env vars at startup | Cross-cutting | 0.5 day |

### Total Estimated Effort

| Priority | Stories | Days |
|----------|---------|------|
| P1 (Pre-GTM Critical) | 4 | 6 |
| P2 (Pre-GTM Important) | 5 | 4 |
| P3 (Post-GTM Polish) | 10 | 8.5 |
| **Total** | **19** | **18.5** |

---

## Appendix: Files Read

### Backend (50 files)
- `main.py`, `auth.py`, `quota.py`, `pncp_client.py`, `schemas.py`, `config.py`
- `excel.py`, `llm.py`, `progress.py`, `middleware.py`, `authorization.py`
- `filter.py` (1600+ lines, read in 3 chunks), `supabase_client.py`, `redis_client.py`
- `cache.py`, `sectors.py` (1631 lines), `rate_limiter.py`, `log_sanitizer.py`
- `relevance.py`, `llm_arbiter.py`, `term_parser.py`, `synonyms.py`, `status_inference.py`
- `admin.py`, `routes/search.py`, `routes/user.py`, `routes/billing.py`
- `routes/sessions.py`, `routes/analytics.py`, `routes/plans.py`, `routes/features.py`
- `routes/subscriptions.py`, `webhooks/stripe.py`
- `requirements.txt`

### Frontend (key files)
- `app/layout.tsx`, `app/error.tsx`
- `app/buscar/page.tsx`, `app/buscar/hooks/useSearch.ts`
- `app/api/buscar/route.ts`, `app/types.ts`
- `app/components/AuthProvider.tsx`
- `app/dashboard/page.tsx` (via grep)
- `package.json`

### Patterns Searched (via Grep)
- `from supabase_client import get_supabase` -- 35 occurrences across 18 files
- `: any` in frontend -- 8 occurrences
- `Optional[any]` in backend -- 4 occurrences
- `time.sleep` in backend -- 10+ occurrences in production code
- `asyncio.run()` -- 1 in production code, 14 in tests
- `from cache import` -- 2 files (cache.py docstring, webhooks/stripe.py)
- Error boundaries -- only `app/error.tsx`
