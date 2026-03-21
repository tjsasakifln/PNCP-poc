# SmartLic -- System Architecture Document

**Date:** 2026-03-20 | **Author:** @architect (Atlas) | **Phase:** Brownfield Discovery Phase 1
**Codebase:** `main` branch HEAD | **Version:** 3.0 (supersedes GTM Readiness Assessment v2.0)

---

## 1. System Overview

### 1.1 What SmartLic Does

SmartLic is a B2G (Business-to-Government) intelligence platform that automates discovery, analysis, and qualification of public procurement opportunities (licitacoes) in Brazil. It targets construction, engineering, and service companies that participate in government bids.

**Core Value Proposition:**
- Aggregates procurement data from 3 government sources (PNCP, PCP v2, ComprasGov v3) into a unified search
- AI-powered sectoral classification using GPT-4.1-nano eliminates irrelevant results
- 4-factor viability assessment helps users prioritize high-probability opportunities
- Kanban pipeline for opportunity tracking from discovery to bid submission

**Current Stage:** POC v0.5 in production (beta with trials, pre-revenue)
**URL:** https://smartlic.tech
**Operator:** CONFENGE Avaliacoes e Inteligencia Artificial LTDA

### 1.2 Product Capabilities

| Capability | Description |
|------------|-------------|
| Multi-source search | PNCP + PCP v2 + ComprasGov v3 with dedup and fallback cascade |
| AI classification | LLM arbiter classifies sectoral relevance (keyword + zero-match) |
| Viability scoring | 4-factor deterministic score: modalidade (30%), timeline (25%), value (25%), geography (20%) |
| Opportunity pipeline | Kanban board with drag-and-drop stage management |
| Export | Styled Excel workbooks + AI executive summaries |
| Search history | Saved searches, sessions, analytics dashboard |
| Billing | Stripe subscriptions with 14-day free trial (no credit card) |

### 1.3 15 Sectors

Defined in `backend/sectors_data.yaml`. Each sector has keywords, exclusion terms, and a viability value range. Examples: vestuario, construcao_civil, informatica, alimentos, saude.

---

## 2. Architecture Diagram

```
                                    +-------------------+
                                    |   End User        |
                                    |   (Browser)       |
                                    +--------+----------+
                                             |
                                             | HTTPS
                                             v
                              +------------------------------+
                              |  Railway Frontend Service     |
                              |  Next.js 16 + React 18       |
                              |  (SSR + API Proxy Layer)      |
                              +------+-----------+-----------+
                                     |           |
                            SSE Stream  REST API Proxy
                            (progress)  (all endpoints)
                                     |           |
                                     v           v
                              +------------------------------+
                              |  Railway Backend Service      |
                              |  Gunicorn + Uvicorn Workers   |
                              |  FastAPI 0.129 + Python 3.12  |
                              +--+----+----+----+----+-------+
                                 |    |    |    |    |
         +-----------------------+    |    |    |    +---------------------+
         |                            |    |    |                         |
         v                            v    |    v                         v
+----------------+  +------------------+   |  +------------------+  +----------+
| PNCP API       |  | PCP v2 API       |   |  | OpenAI API       |  | Stripe   |
| (Priority 1)   |  | (Priority 2)     |   |  | GPT-4.1-nano     |  | Billing  |
| pncp.gov.br    |  | portaldecompras  |   |  |                  |  |          |
+----------------+  | publicas.com.br  |   |  +------------------+  +----------+
                    +------------------+   |
                                           v
                              +------------------------------+
                              |  Railway Worker Service       |
                              |  ARQ Background Jobs          |
                              |  (LLM Summaries + Excel Gen)  |
                              +------+-----------------------+
                                     |
                        +------------+------------+
                        |                         |
                        v                         v
               +-----------------+       +------------------+
               | Supabase Cloud  |       | Redis (Upstash)  |
               | PostgreSQL 17   |       | Cache + Streams  |
               | Auth + RLS      |       | Rate Limiting    |
               | L2 Cache        |       | L1 Cache         |
               +-----------------+       | SSE Pub/Sub      |
                                         | ARQ Queue        |
                                         +------------------+

     +-------------------+    +------------------+    +------------------+
     | GitHub Actions    |    | Sentry           |    | Prometheus       |
     | CI/CD (18 flows)  |    | Error Tracking   |    | Metrics          |
     +-------------------+    +------------------+    +------------------+
```

**Key Data Flows:**
1. User submits search -> Frontend proxies to Backend -> Backend fans out to 3 sources in parallel
2. Results filtered (UF, value, keywords, LLM) -> Viability scored -> Cached (3 levels) -> Returned
3. LLM summary + Excel generation dispatched as ARQ background jobs -> Delivered via SSE events
4. SSE progress stream provides real-time updates (per-UF completion, stage transitions)

---

## 3. Backend Architecture

### 3.1 Module Map

| Category | Key Modules | Purpose |
|----------|-------------|---------|
| **Entry** | `main.py` | FastAPI app init, CORS, root + health endpoints |
| **Config** | `config.py` | Environment loading, feature flags, timeout constants |
| **Schemas** | `schemas.py`, `error_response.py` | Pydantic v2 request/response models, error codes |
| **Pipeline** | `search_pipeline.py`, `search_context.py` | 7-stage orchestrator + typed context dataclass |
| **Pipeline Stages** | `pipeline/stages/{validate,prepare,execute,filter_stage,enrich,generate,persist}.py` | Individual stage implementations |
| **Consolidation** | `consolidation.py` | Multi-source parallel fetch, dedup, timeout |
| **Data Sources** | `pncp_client.py` (sync), `clients/{portal_compras_client,compras_gov_client,querido_diario_client,portal_transparencia_client,sanctions}.py` | Source adapters with circuit breakers |
| **Source Config** | `source_config/sources.py`, `clients/base.py` | Source registry, `SourceAdapter` ABC, `UnifiedProcurement` model |
| **Filtering** | `filter.py`, `filter_stats.py`, `term_parser.py`, `synonyms.py`, `status_inference.py` | Keyword matching, density scoring, term parsing |
| **AI/LLM** | `llm_arbiter.py`, `llm.py`, `relevance.py` | Classification (arbiter), summaries, relevance scoring |
| **Viability** | `viability.py` | 4-factor viability assessment (deterministic) |
| **Cache** | `search_cache.py` (3-level search cache), `cache.py` (Redis wrapper), `redis_pool.py` (connection pool) | L1 InMemory + L2 Redis + L3 Supabase, SWR pattern |
| **Auth** | `auth.py` | JWT validation (ES256+JWKS), token cache (L1 memory + L2 Redis) |
| **Authorization** | `authorization.py`, `quota.py` | Role checks, plan capabilities, atomic quota increment |
| **Billing** | `services/billing.py`, `webhooks/stripe.py` | Stripe checkout, portal, webhook handlers |
| **Jobs** | `job_queue.py` | ARQ worker config, job definitions, pool management |
| **Progress** | `progress.py` | SSE event tracking via Redis Streams + in-memory fallback |
| **Rate Limiting** | `rate_limiter.py` | Token bucket (Redis + in-memory), per-user and per-IP |
| **Bulkhead** | `bulkhead.py` | Per-source concurrency isolation (semaphore-based) |
| **Supabase** | `supabase_client.py` | Admin + user-scoped clients, circuit breaker, connection pool |
| **Monitoring** | `metrics.py`, `telemetry.py`, `health.py`, `audit.py` | Prometheus, OpenTelemetry, health checks |
| **Output** | `excel.py`, `google_sheets.py`, `report_generator.py` | Excel export, Google Sheets, PDF reports |
| **Email** | `email_service.py`, `templates/emails/` | Transactional emails via Resend |
| **Sectors** | `sectors.py`, `sectors_data.yaml` | 15 sector definitions with keywords and ranges |
| **Middleware** | `middleware.py` | Request ID, correlation, structured logging context |
| **Routes** | 38 modules in `routes/` | All API endpoints (see Section 3.7) |
| **Services** | 16 modules in `services/` | Business logic (billing, alerts, trials, organizations, partners) |
| **State Machine** | `search_state_manager.py`, `models/search_state.py` | Search lifecycle state machine |
| **Security** | `log_sanitizer.py`, `encryption.py` | PII masking, field encryption |

### 3.2 Search Pipeline Flow

The search pipeline is a 7-stage state machine orchestrated by `SearchPipeline` in `search_pipeline.py`. Each stage operates on a shared `SearchContext` dataclass.

```
Stage 1: VALIDATE    -> Auth check, quota verification, input validation
Stage 2: PREPARE     -> Sector lookup, keyword preparation, term parsing
Stage 3: FETCH       -> Multi-source parallel fetch (PNCP + PCP v2 + ComprasGov)
          |
          +---> ConsolidationService.consolidate()
          |     - asyncio.gather() across sources with per-source timeouts
          |     - Dedup by dedup_key (highest priority source wins: PNCP=1 > PCP=2)
          |     - Graceful degradation: partial results on partial failure
          |
Stage 4: FILTER      -> UF check, value range, keyword density scoring, LLM zero-match
          |
          [Time Budget Check: skip LLM/viability if elapsed > 90s]
          |
Stage 5: ENRICH      -> LLM arbiter classification, viability assessment
Stage 6: GENERATE    -> Excel generation, LLM summary (enqueued as ARQ jobs if available)
Stage 7: PERSIST     -> Cache write (3 levels), search history save
```

**Time Budget Chain (GTM-STAB-003):**
```
ARQ Job: 300s > Pipeline: 110s > Consolidation: 100s > Per-Source: 80s > Per-UF: 30s
If elapsed > 90s at stage boundary: skip LLM classification
If elapsed > 100s: skip viability assessment
```

### 3.3 Data Source Integration

#### PNCP (Priority 1) -- `pncp_client.py`

- **URL:** `https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao`
- **Client:** Synchronous `requests` library (wrapped in `asyncio.to_thread()`)
- **Page size:** Max 50 (reduced from 500 in Feb 2026; >50 causes HTTP 400 silently)
- **Rate limit:** 10 req/s client-side enforcement
- **Retry:** Exponential backoff with jitter, HTTP 422 retryable (max 1 retry)
- **Batching:** Phased UF batching (PNCP_BATCH_SIZE=5, PNCP_BATCH_DELAY_S=2.0)
- **Circuit breaker:** 15 failures threshold, 60s cooldown
- **Quirk:** `codigoModalidadeContratacao` now required (without it, HTTP 400)
- **Quirk:** Health canary uses `tamanhoPagina=10`, so it cannot detect the page size limit change

#### PCP v2 (Priority 2) -- `clients/portal_compras_client.py`

- **URL:** `https://compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos`
- **Auth:** None (fully public API)
- **Pagination:** Fixed 10/page (`pageCount`/`nextPage`)
- **Limitation:** No server-side UF filtering (client-side only)
- **Limitation:** `valor_estimado=0.0` (v2 has no value data)

#### ComprasGov v3 (Priority 3) -- `clients/compras_gov_client.py`

- **URL:** `https://dadosabertos.compras.gov.br`
- **Status:** API confirmed DOWN as of 2026-03-03 (returns JSON 404)
- **Architecture:** Dual-endpoint (legacy + Lei 14.133)
- **Priority:** Downgraded to 99 (effectively disabled)

#### Additional Sources (Intel/Report Scripts)

- **Querido Diario:** `clients/querido_diario_client.py` -- municipal gazette search
- **Portal da Transparencia:** `clients/portal_transparencia_client.py` -- sanctions check, contract history
- **Sanctions:** `clients/sanctions.py` -- CEIS/CNEP/CEPIM sanctions check

### 3.4 LLM Integration Pattern

**Model:** GPT-4.1-nano (`llm_arbiter.py`)

**Classification Tiers:**
1. **keyword** (>5% density): Direct keyword match, no LLM call needed
2. **llm_standard** (2-5% density): LLM confirms relevance (SIM/NAO)
3. **llm_conservative** (1-2% density): LLM with higher threshold
4. **llm_zero_match** (0% density): LLM decides if contract is relevant despite no keyword matches

**Structured Output (D-02):**
```json
{
  "classe": "SIM|NAO",
  "confianca": 0-100,
  "evidencias": ["literal citation 1", "..."],
  "motivo_exclusao": "reason if NAO"
}
```

**Fallback Philosophy:** REJECT on LLM failure (zero noise -- never show false positives).

**Caching:**
- L1: In-memory OrderedDict with LRU eviction (max 5000 entries, keyed by MD5 of input)
- L2: Redis hash with 1h TTL for cross-worker sharing

**Cost:** ~R$0.00007 per structured classification call.

**Client Config:**
- Timeout: 5s (configurable via `OPENAI_TIMEOUT_S`)
- Max retries: 1
- Lazy initialization (no import-time errors in tests)

### 3.5 Caching Strategy

Three-level cache with Stale-While-Revalidate (SWR) pattern:

```
+-------------------+--------+-------------+-------------------------------------+
| Layer             | TTL    | Status      | Behavior                            |
+-------------------+--------+-------------+-------------------------------------+
| L1 InMemory/Redis | 4h     | Fresh 0-4h  | Serve directly, fastest             |
| L2 Supabase       | 24h    | Stale 4-24h | Serve + trigger SWR revalidation    |
| L3 Local File     | 24h    | Emergency   | Serve only if Supabase down         |
+-------------------+--------+-------------+-------------------------------------+
```

**Cache Key:** Deterministic hash of ALL params that affect results (UFs, sector, dates, terms, filters). Date range now included in cache key (STORY-306).

**Hot/Warm/Cold Tiering (B-02):**
- HOT: 3+ accesses in 24h or saved search with recent access -> Redis TTL 2h
- WARM: 1+ access in 24h -> Redis TTL 6h
- COLD: No recent access -> Redis TTL 1h

**Progressive Delivery (A-04):** When cache exists, returns cached results immediately and spawns a background live fetch. Frontend receives updated results via SSE.

### 3.6 Auth + Billing Flow

**Authentication:**
- Supabase Auth with JWT (ES256 + JWKS, backward-compatible with HS256)
- Local JWT validation (no API call per request)
- Token cache: L1 in-memory (60s TTL, max 1000 entries LRU) + L2 Redis (5min TTL)
- Google OAuth support via `routes/auth_oauth.py`

**Authorization:**
- Row-Level Security (RLS) on all Supabase tables
- Admin client (`service_role` key, bypasses RLS) for system operations
- User-scoped client (`anon` key + user JWT) for user-facing operations
- Role checks: `is_admin`, `is_master` for admin endpoints
- MFA support via `routes/mfa.py`

**Billing:**
- Stripe subscriptions: SmartLic Pro R$397/mth, R$357/mth (semi), R$297/mth (annual)
- 14-day free trial (no credit card required)
- Atomic quota check+increment via PostgreSQL function (prevents TOCTOU)
- Plan capabilities loaded from DB with 5min in-memory cache
- "Fail to last known plan": never fall back to free_trial on transient DB errors
- 3-day grace period for subscription gaps
- All Stripe webhook handlers sync `profiles.plan_type`

### 3.7 API Routes (38 route modules)

| Module | Key Endpoints | Purpose |
|--------|--------------|---------|
| `search.py` | `POST /buscar` | Main search orchestration |
| `search_sse.py` | `GET /buscar-progress/{id}` | SSE progress stream |
| `search_status.py` | `GET /v1/search/{id}/status`, `POST /v1/search/{id}/retry` | Polling + retry |
| `pipeline.py` | CRUD `/pipeline` | Opportunity kanban |
| `billing.py` | `POST /checkout`, `POST /billing-portal` | Stripe integration |
| `user.py` | `GET /me`, `GET /trial-status` | User profile + trial |
| `analytics.py` | `GET /summary`, `GET /searches-over-time` | Dashboard analytics |
| `feedback.py` | `POST/DELETE /feedback` | Result feedback |
| `health.py` + `health_core.py` | `GET /health`, `GET /health/cache` | System health |
| `onboarding.py` | `POST /first-analysis` | Onboarding auto-search |
| `sessions.py` | `GET /sessions` | Search session history |
| `messages.py` | CRUD `/conversations` | In-app messaging |
| `auth_oauth.py` | `GET /google`, `GET /google/callback` | Google OAuth |
| `admin_trace.py` | `GET /search-trace/{id}` | Admin search debugging |
| `plans.py` | `GET /plans` | Plan listing |
| `subscriptions.py` | `GET /subscription/status` | Subscription status |
| `feature_flags.py` | Feature flag endpoints | Runtime toggles |
| `sectors_public.py` | `GET /setores` | Public sector list |
| `mfa.py` | MFA setup/verify | Multi-factor auth |
| `organizations.py` | Organization CRUD | Multi-tenant orgs |
| `partners.py` | Partner endpoints | Partner program |
| `alerts.py` | Alert preferences | Bid alert config |
| `reports.py` | Report generation | B2G intel reports |
| `bid_analysis.py` | Bid deep analysis | Competitor analysis |
| `slo.py` | SLO endpoints | Service level tracking |
| `metrics_api.py` | `GET /metrics` | Prometheus exposition |

### 3.8 Background Jobs (ARQ)

**Architecture:** Separate Railway service running `arq job_queue.WorkerSettings`.

**Jobs:**
- `llm_summary_job`: Generate AI executive summary for search results
- `excel_generation_job`: Create styled Excel workbook
- `email_jobs`: Trial email sequences, dunning

**Communication:** SSE events (`llm_ready`, `excel_ready`) delivered via ProgressTracker.

**Fallback:** When ARQ/Redis unavailable, `is_queue_available()` returns False and pipeline executes LLM/Excel inline (zero regression).

**Worker Resilience:**
- Restart wrapper in `start.sh`: max 10 restarts with 5s delay
- Redis retry: `retry_on_timeout=True`, `retry_on_error=[ConnectionError, TimeoutError]`
- Liveness check every 15s (CRIT-033)

### 3.9 SSE Progress Tracking

**Dual-Connection Pattern:**
1. `POST /buscar` -> Initiates search, returns `search_id`
2. `GET /buscar-progress/{search_id}` -> SSE stream with real-time progress

**Implementation (STORY-276):**
- Redis Streams for cross-worker delivery (persistent, append-only log with replay)
- In-memory asyncio.Queue fallback for single-instance deployments
- Last-Event-ID resumption (STORY-297): Replay from any point in stream
- Heartbeat: 15s interval (CRIT-012)
- Terminal events trigger stream EXPIRE (5min TTL)

**Event Types:**
```
connecting -> fetching (per-UF progress) -> filtering -> llm -> excel -> complete
                                                        |
                                                        +-> degraded / error
```

---

## 4. Frontend Architecture

### 4.1 Page Structure (22+ routes)

| Route | Purpose |
|-------|---------|
| `/` | Landing page |
| `/login`, `/signup` | Authentication |
| `/auth/callback` | OAuth callback |
| `/onboarding` | 3-step wizard (CNAE -> UFs -> Confirmation) |
| `/buscar` | **Main search page** -- filters, results, SSE progress |
| `/dashboard` | User dashboard with analytics |
| `/historico` | Search history |
| `/pipeline` | Opportunity kanban (drag-and-drop via @dnd-kit) |
| `/mensagens` | Messaging system |
| `/conta` | Account settings |
| `/planos`, `/pricing`, `/features` | Pricing and marketing |
| `/admin`, `/admin/cache` | Admin dashboards |
| `/ajuda` | Help center |
| `/alertas` | Bid alert preferences |
| `/blog` | Content marketing |
| `/sobre` | About page |
| `/termos`, `/privacidade` | Legal pages |
| SEO pages | `/como-avaliar-licitacao`, `/como-evitar-prejuizo-licitacao`, etc. |

### 4.2 API Proxy Pattern

All backend calls are proxied through Next.js API routes (`frontend/app/api/`). This:
- Hides the backend URL from the client
- Allows adding auth headers server-side
- Provides a CORS-free boundary
- Enables request/response transformation

**40+ proxy routes** including: buscar, buscar-progress, analytics, admin, feedback, trial-status, user, plans, pipeline, sessions, messages, billing-portal, export, metrics, organizations, reports, subscriptions, alerts, etc.

### 4.3 State Management

- **No global state library** (no Redux/Zustand). State managed via custom hooks.
- **SWR pattern:** `SWRProvider.tsx` wraps the app for data fetching with revalidation.
- **Search state:** Complex decomposition across 9 specialized hooks in `app/buscar/hooks/`:
  - `useSearchOrchestration.ts` -- Top-level orchestrator
  - `useSearch.ts` -- Core search state and execution
  - `useSearchExecution.ts` -- Search lifecycle management
  - `useSearchFilters.ts` -- Filter state with SWR sector loading
  - `useSearchSSEHandler.ts` -- SSE event processing
  - `useSearchExport.ts` -- Excel/Sheets export
  - `useSearchPersistence.ts` -- Search save/load
  - `useSearchRetry.ts` -- Auto-retry with exponential backoff
  - `useUfProgress.ts` -- Per-UF progress tracking

**Global hooks** (28 in `app/hooks/`): useAlerts, useAnalytics, usePipeline, usePlan, useQuota, useProfileContext, useSavedSearches, useOnboarding, useFeatureFlags, useFetchWithBackoff, etc.

### 4.4 Key Component Hierarchy (`app/buscar/`)

```
page.tsx (HomePageContent)
  |-- SearchForm (form inputs, sector select, date pickers)
  |-- SearchResults (result list with cards)
  |     |-- search-results/ (card components)
  |     |-- LlmSourceBadge, ZeroMatchBadge, ReliabilityBadge
  |     |-- ViabilityBadge, FeedbackButtons
  |-- FilterPanel (UF, value, status, modalidade filters)
  |-- EnhancedLoadingProgress (animated progress bar)
  |-- UfProgressGrid (per-UF status during fetch)
  |-- SourceStatusGrid (per-source health indicator)
  |-- BuscarModals (upgrade, export, detail modals)
  |-- ErrorDetail (structured error display)
  |-- Banners: ExpiredCache, FilterRelaxed, PartialTimeout, Refresh, SearchError
  |-- EmptyStates: SearchEmptyState, OnboardingEmptyState, ZeroResultsSuggestions
```

### 4.5 Security (Frontend)

**Middleware (`middleware.ts`):**
- Route protection: `/buscar`, `/historico`, `/conta`, `/admin/*`, `/dashboard`, `/mensagens`
- Supabase SSR auth cookie management
- CSP nonce generation per request (DEBT-108)
- Security headers: HSTS, COOP, X-Content-Type-Options, X-Frame-Options, etc.
- CSP enforcement with nonce-based script-src + strict-dynamic

---

## 5. Infrastructure

### 5.1 Railway Deployment Topology

```
Railway Project
  |
  +-- Service: bidiq-backend (web)
  |     PROCESS_TYPE=web
  |     Gunicorn + Uvicorn workers (or uvicorn standalone via RUNNER=uvicorn)
  |     Workers: 2 (SLA-002: reduced from 4 for 1GB RAM)
  |     Timeout: 120s (Gunicorn), ~300s (Railway hard limit)
  |     Keep-alive: 75s (> Railway proxy 60s)
  |     Max-requests: 1000 + jitter 50 (memory leak prevention)
  |
  +-- Service: bidiq-worker
  |     PROCESS_TYPE=worker
  |     ARQ background job processor
  |     Restart wrapper: max 10 restarts, 5s delay
  |
  +-- Service: bidiq-frontend
        Next.js 16 production server
        PORT=8080
        Custom domain: smartlic.tech
```

### 5.2 CI/CD Pipelines (18 GitHub Actions Workflows)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `backend-tests.yml` | PR + push to main | pytest + coverage (>=70%) + ruff + mypy + pip-audit |
| `frontend-tests.yml` | PR + push to main | jest + coverage (>=60%) + lint + typecheck |
| `e2e.yml` | PR + schedule | Playwright E2E (60 critical flows) |
| `deploy.yml` | Push to main (backend/ or frontend/) | Railway deploy + migration apply |
| `staging-deploy.yml` | Manual | Staging environment deploy |
| `migration-gate.yml` | PR touching migrations | Warning comment on PR |
| `migration-check.yml` | Push to main + daily | Block if unapplied migrations |
| `pr-validation.yml` | PR | Label, size check, conventional commits |
| `codeql.yml` | Schedule | GitHub CodeQL security analysis |
| `lighthouse.yml` | Schedule | Lighthouse performance audit |
| `load-test.yml` | Manual | Load testing |
| `sync-sectors.yml` | Manual | Frontend sector fallback sync |
| `cleanup.yml` | Schedule | Stale branch/artifact cleanup |
| `dependabot-auto-merge.yml` | Dependabot PRs | Auto-merge minor updates |

**Migration CI (3-layer defense):**
1. PR Warning: migration-gate posts warning comment
2. Push Alert: migration-check blocks on unapplied migrations
3. Auto-Apply: deploy.yml runs `supabase db push --include-all` after deploy

### 5.3 Monitoring Stack

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Prometheus** | Metrics collection | In-memory metrics, `/metrics` endpoint, Bearer token auth |
| **OpenTelemetry** | Distributed tracing | Trace IDs in SSE events + logs, optional spans per pipeline stage |
| **Sentry** | Error tracking | Frontend + backend, structured context, breadcrumbs |
| **Mixpanel** | Product analytics | Frontend events, cache hit tracking |
| **Structured Logging** | Operational visibility | JSON format, request IDs, PII masking via `log_sanitizer.py` |

**Key Prometheus Metrics:**
- `smartlic_search_duration_seconds` (histogram, labels: sector, uf_count, cache_status)
- `smartlic_searches_total` (counter, labels: sector, result_status, search_mode)
- `smartlic_active_searches` (gauge)
- `smartlic_cache_hits_total` / `smartlic_cache_misses_total` (counters)
- `smartlic_llm_calls_total` / `smartlic_llm_duration_seconds` (histogram)
- `smartlic_fetch_duration_seconds` (per-source histogram)
- `smartlic_api_errors_total` (counter by source)
- `smartlic_sse_connection_errors_total` (counter by error_type, phase)
- Bulkhead, rate limiter, auth cache, connection pool metrics

---

## 6. Data Flow -- End-to-End Search Request Lifecycle

```
1. USER clicks "Buscar" in browser
   |
2. Frontend useSearchExecution builds BuscaRequest
   |  generates search_id (UUID)
   |
3. Frontend opens SSE connection: GET /api/buscar-progress/{search_id}
   |  Proxied to backend: GET /buscar-progress/{search_id}
   |
4. Frontend fires POST /api/buscar (Next.js proxy)
   |  Proxy adds auth token, forwards to backend
   |
5. BACKEND routes/search.py receives POST /buscar
   |  a. Auth check (JWT validation, cached)
   |  b. Rate limit check (Redis token bucket)
   |  c. Quota check + atomic increment (Supabase)
   |  d. Create ProgressTracker (Redis Streams or in-memory Queue)
   |  e. Create SearchContext
   |  f. Instantiate SearchPipeline with deps
   |
6. PIPELINE Stage 1: VALIDATE
   |  Validate dates, UFs, sector existence
   |
7. PIPELINE Stage 2: PREPARE
   |  Load sector keywords from sectors_data.yaml
   |  Parse custom terms (comma-delimited or space-delimited)
   |  Check cache -> if FRESH, return cached + skip to Stage 7
   |  If STALE, return cached + spawn background live fetch
   |
8. PIPELINE Stage 3: FETCH (ConsolidationService)
   |  a. For each source (PNCP, PCP v2):
   |     - Acquire bulkhead semaphore (concurrency isolation)
   |     - For each UF batch (PNCP: 5 UFs per batch):
   |       - Fetch pages (max 50/page for PNCP)
   |       - Emit SSE: per-UF progress
   |     - Convert to UnifiedProcurement format
   |  b. Dedup: by dedup_key, keep highest-priority source
   |  c. If all sources fail: serve stale cache or raise error
   |
9. PIPELINE Stage 4: FILTER (fail-fast order)
   |  a. UF check (fastest)
   |  b. Value range check
   |  c. Keyword density scoring
   |  d. Status/date validation
   |  e. LLM zero-match classification (for 0% density, if enabled)
   |
   [Time budget check: skip LLM if >90s elapsed]
   |
10. PIPELINE Stage 5: ENRICH
    |  a. LLM arbiter for "uncertain zone" (1-5% density)
    |  b. Viability assessment (4 factors, deterministic)
    |  c. PNCP link generation
    |
11. PIPELINE Stage 6: GENERATE
    |  a. Enqueue llm_summary_job to ARQ (or inline fallback)
    |  b. Enqueue excel_generation_job to ARQ (or inline fallback)
    |  c. Generate fallback summary immediately (gerar_resumo_fallback)
    |
12. PIPELINE Stage 7: PERSIST
    |  a. Save to L1 InMemory cache
    |  b. Save to L2 Redis cache
    |  c. Save to L3 Supabase cache
    |  d. Save search history record
    |
13. BACKEND returns BuscaResponse (JSON)
    |  Frontend receives via POST response
    |
14. ARQ WORKER (async):
    |  a. Generates AI summary via GPT-4.1-nano
    |  b. Creates styled Excel workbook
    |  c. Emits SSE events: llm_ready, excel_ready
    |
15. FRONTEND receives SSE events, updates UI:
    |  - Progress bar fills per stage
    |  - Results render incrementally
    |  - LLM summary appears when ready
    |  - Excel download button activates when ready
```

---

## 7. Security Architecture

### 7.1 Authentication

| Layer | Mechanism |
|-------|-----------|
| JWT Signing | ES256 (ECDSA) via JWKS endpoint, backward-compat HS256 |
| Token Validation | Local (no API call), cached 60s (L1) + 5min (L2 Redis) |
| Session | Supabase Auth cookies via @supabase/ssr |
| OAuth | Google OAuth via Supabase |
| MFA | TOTP-based multi-factor auth |

### 7.2 Authorization

| Layer | Mechanism |
|-------|-----------|
| Database | RLS on all Supabase tables |
| API | `require_auth` dependency, `check_user_roles` for admin |
| Quota | Atomic check+increment in PostgreSQL function |
| Plan | Database-driven capabilities with in-memory cache |

### 7.3 Input Validation

| Layer | Mechanism |
|-------|-----------|
| Request | Pydantic v2 models with field validators |
| UUID | Regex validation (UUID v4 format only) |
| Search Query | `SAFE_SEARCH_PATTERN` regex, max 100 chars, SQL pattern escaping |
| Plan ID | Alphanumeric + underscore, max 50 chars |
| Password | Min 8 chars, 1 uppercase, 1 digit |

### 7.4 Rate Limiting

| Endpoint | Limit |
|----------|-------|
| Search (`POST /buscar`) | 10/min per user (configurable) |
| Auth (login) | 5/5min per IP |
| Signup | 3/10min per IP |
| SSE connections | Max 3 concurrent per user |
| SSE reconnect | 10/60s per user |

### 7.5 Network Security (Frontend Middleware)

- **CSP:** Nonce-based script-src with strict-dynamic
- **HSTS:** max-age 1yr, includeSubDomains, preload
- **COOP:** same-origin
- **X-Frame-Options:** DENY
- **X-Content-Type-Options:** nosniff
- **Referrer-Policy:** strict-origin-when-cross-origin
- **Permissions-Policy:** camera=(), microphone=(), geolocation=()

### 7.6 Secrets Management

- All API keys in environment variables only (never committed)
- Log sanitization via `log_sanitizer.py` (PII masking)
- Field encryption for sensitive data (`encryption.py`)
- CORS configurable via `CORS_ORIGINS` (currently `*` -- see Debt section)
- Stripe webhook signature verification

---

## 8. Integration Points

### 8.1 External APIs and Constraints

| API | Purpose | Rate Limit | Key Constraints |
|-----|---------|------------|-----------------|
| PNCP | Primary procurement data | 10 req/s (self-imposed) | Max 50/page, `codigoModalidadeContratacao` required |
| PCP v2 | Secondary procurement data | None documented | 10/page fixed, no server-side UF filter, no value data |
| ComprasGov v3 | Tertiary procurement data | N/A | **OFFLINE since 2026-03-03** |
| OpenAI (GPT-4.1-nano) | Classification + summaries | Standard API limits | 5s timeout, max 1 retry, ~R$0.00007/call |
| Supabase | Database + Auth | Connection pool: 25/worker | Circuit breaker: 10 window, 50% threshold, 60s cooldown |
| Redis (Upstash) | Cache + Streams + Queue | 50 connections | 30s socket timeout, XREAD compatible |
| Stripe | Billing | Standard limits | Webhook signature verification |
| Resend | Transactional email | Free tier | 1 domain limit on free plan |
| Portal da Transparencia | Sanctions check | 90 req/min (06-01h) | `chave-api-dados` header, `codigoOrgao` required for some endpoints |
| BrasilAPI | Company data (Simples/MEI) | Public | Used in intel reports |
| IBGE SIDRA | Population/GDP data | Public | Used in intel reports |

### 8.2 Internal Integration Points

| Integration | Mechanism |
|-------------|-----------|
| Backend <-> Frontend | REST + SSE via Next.js API proxy |
| Web <-> Worker | ARQ job queue via Redis |
| Backend <-> Supabase | supabase-py client (admin + user-scoped) |
| Backend <-> Redis | redis-py 5.x async pool |
| Cross-worker SSE | Redis Streams (STORY-276) |
| Metrics scraping | Prometheus `/metrics` endpoint |
| Error reporting | Sentry SDK (both frontend and backend) |
| Analytics events | Mixpanel (frontend), structured logs (backend) |

---

## 9. Technical Debt Identified

### CRITICAL

| ID | Issue | Impact | Location |
|----|-------|--------|----------|
| TD-001 | **CORS allows all origins (`*`)** | Any website can make authenticated API calls. In production with real users, this is a significant security risk. | `main.py:43` |
| TD-002 | **PNCP client uses synchronous `requests` library** | Blocks the event loop thread (mitigated via `asyncio.to_thread()` wrapper, but adds complexity and limits concurrency). All other clients use async httpx. | `pncp_client.py` |
| TD-003 | **ComprasGov v3 offline with no monitoring** | Third data source completely unavailable since 2026-03-03 with no automated health check or alert to detect recovery. Priority hardcoded to 99. | `clients/compras_gov_client.py` |

### HIGH

| ID | Issue | Impact | Location |
|----|-------|--------|----------|
| TD-004 | **Prometheus SLOs are ephemeral** | All Prometheus metrics reset on container restart (in-memory only). No persistent SLO tracking. Railway restarts containers on deploy. | `metrics.py` |
| TD-005 | **Health canary cannot detect PNCP page size limit** | Health canary uses `tamanhoPagina=10`, so it passes even when PNCP changed max from 500 to 50. A regression in page size limits would go undetected. | `health.py`, `pncp_client.py` |
| TD-006 | **main.py is minimal but route registration happens elsewhere** | `main.py` shows only root + health endpoints. Actual route registration (38 modules) is not visible from the entry point -- it is done via a registration pattern not shown in main.py. This hurts discoverability. | `main.py` |
| TD-007 | **API versioning inconsistent** | Some routes use `/v1/` prefix (search status, first-analysis), most do not. No version negotiation. Future breaking changes will be difficult. | `routes/*` |
| TD-008 | **No request timeout at the application level** | Gunicorn timeout is 120s, Railway is ~300s, but there is no application-level request timeout middleware. A slow downstream call could hold a worker for the full Gunicorn timeout. | `start.sh`, pipeline |
| TD-009 | **Worker liveness detection relies on Redis** | `_worker_alive_cache` checks via Redis key. If Redis is down, worker liveness cannot be determined, and inline fallback path activates (correct), but there is no alerting for prolonged worker absence. | `job_queue.py` |
| TD-010 | **Search decomposition has backward-compat re-exports** | DEBT-115 decomposed `routes/search.py` into 4 sub-modules, but the original module re-exports all symbols for backward compatibility. This creates a fragile import graph where tests and modules can import from either location. | `routes/search.py` |

### MEDIUM

| ID | Issue | Impact | Location |
|----|-------|--------|----------|
| TD-011 | **`filter.py` has hardcoded keyword sets** | The default `KEYWORDS_UNIFORMES` set is hardcoded alongside the sector-based keywords from YAML. The legacy keyword set should be fully migrated to `sectors_data.yaml`. | `filter.py` |
| TD-012 | **Multiple cache implementations** | `search_cache.py` (3-level search cache), `cache.py` (Redis wrapper), `redis_pool.py` (InMemoryCache fallback), `auth.py` (token cache), `llm_arbiter.py` (arbiter cache), `quota.py` (plan status cache). Each has its own eviction/TTL logic. | Multiple modules |
| TD-013 | **No database migration version tracking in code** | 35 Supabase migrations + 7 backend migrations, but no in-code schema version assertion. The migration-check CI catches unapplied migrations, but there is no runtime check. | `supabase/migrations/` |
| TD-014 | **Test pollution patterns documented but not eliminated** | MEMORY.md documents 8+ test pollution patterns (sys.modules, importlib.reload, MagicMock leakage, global singletons). These are mitigated by conftest fixtures but root causes remain. | `backend/tests/conftest.py` |
| TD-015 | **Frontend has no global state management** | All state is in custom hooks. The 9-hook search decomposition (`useSearchOrchestration` -> 8 sub-hooks) is complex. State synchronization across hooks relies on prop drilling and callback chains. | `app/buscar/hooks/` |
| TD-016 | **Dual connection pool management** | `supabase_client.py` manages its own httpx pool (25 connections, circuit breaker) while `redis_pool.py` manages Redis pool (50 connections). No unified pool budget or backpressure across both. | `supabase_client.py`, `redis_pool.py` |

### LOW

| ID | Issue | Impact | Location |
|----|-------|--------|----------|
| TD-017 | **App title still says "BidIQ Uniformes"** | `main.py` title and descriptions reference "BidIQ Uniformes" (original POC name), not "SmartLic". | `main.py` |
| TD-018 | **FastAPI version declared as 0.2.0** | `main.py` declares `version="0.2.0"` but product is at v0.5. | `main.py` |
| TD-019 | **Comment references Issue numbers** | Many code comments reference GitHub issue numbers (e.g., "Issue #168", "STORY-xxx", "CRIT-xxx") without links. Dense annotation aids archeology but hurts readability. | Throughout |
| TD-020 | **Frontend SEO pages hardcoded** | SEO content pages (`/como-avaliar-licitacao`, etc.) are static Next.js routes, not CMS-driven. Adding new SEO pages requires code deploys. | `frontend/app/` |

---

## 10. Resilience Patterns

### 10.1 Circuit Breakers

| Target | Implementation | Config |
|--------|---------------|--------|
| Supabase | `SupabaseCircuitBreaker` in `supabase_client.py` | Sliding window 10, 50% threshold, 60s cooldown, 3 trial calls |
| Per-source (PNCP, PCP) | Circuit breakers in source adapters | 15 failures, 60s cooldown |
| OpenAI | Implicit via timeout + max_retries=1 | 5s timeout |

### 10.2 Timeouts

```
Railway hard limit:     ~300s (kills request)
Gunicorn worker:        120s (configurable via GUNICORN_TIMEOUT)
Gunicorn keep-alive:    75s (> Railway proxy 60s, prevents 502s)
Pipeline total:         110s
Consolidation:          100s
Per-source fetch:       80s
Per-UF fetch:           30s
LLM classification:     5s per call
Supabase pool:          30s
Redis socket:           30s
SSE heartbeat:          15s
SSE body timeout:       0 (disabled on frontend proxy, infinite wait)
```

### 10.3 Fallback Cascade

```
1. Live data from all sources
   |-- If source fails -> Partial results from remaining sources
   |-- If all sources fail -> Stale cache (if available)
   |-- If no cache -> Empty result with degradation guidance
   |
2. LLM classification
   |-- If LLM fails -> REJECT (zero noise philosophy)
   |-- If timeout -> Skip LLM, serve keyword-only results
   |
3. ARQ job queue
   |-- If Redis down -> Inline LLM/Excel execution
   |-- If worker down -> Inline fallback after 15s liveness check
   |
4. Search cache read
   |-- L1 InMemory/Redis -> L2 Supabase -> L3 Local file -> Cache miss
   |
5. Search cache write
   |-- Supabase -> Redis -> Local file (3-level save fallback)
   |
6. Auth token validation
   |-- L1 Memory -> L2 Redis -> JWT decode (no cache)
   |
7. Rate limiting
   |-- Redis -> In-memory fallback (per-worker only)
   |
8. Frontend
   |-- SSE fails -> Time-based progress simulation
   |-- Backend down -> Stale sector cache from localStorage
   |-- Auto-retry: [10s, 20s, 30s], max 3 attempts
```

### 10.4 Bulkhead Pattern

Each data source has its own asyncio.Semaphore (`bulkhead.py`). If PNCP exhausts its concurrency slots, PCP v2 continues unaffected.

### 10.5 Graceful Degradation

- **Partial results:** If some UFs or sources fail, results from successful ones are returned with `is_partial=True` and `degradation_reason`.
- **Progressive delivery (A-04):** Cached results returned immediately; live fetch spawns in background.
- **Time budget:** After 90s, LLM classification skipped. After 100s, viability assessment skipped.
- **Gunicorn worker recycling:** `max-requests=1000` with jitter prevents memory leaks.
- **SIGSEGV mitigation:** `--preload` disabled by default due to cryptography/OpenSSL fork-safety issues. Uvicorn standalone mode (`RUNNER=uvicorn`) available as alternative.

### 10.6 Stale-While-Revalidate (SWR)

- Fresh (0-4h): Serve directly
- Stale (4-24h): Serve immediately + trigger background revalidation (max 3 concurrent, 180s timeout)
- Expired (>24h): Not served (new fetch required)
- Emergency: Local file cache served only when Supabase and Redis both down

---

## Appendix A: File Counts and Test Baselines

| Metric | Value |
|--------|-------|
| Backend route modules | 38 |
| Backend service modules | 16 |
| Backend client modules | 9 |
| Pipeline stages | 7 |
| Supabase migrations | 35 |
| Backend tests | 7332 passing / 311 files |
| Frontend tests | 5583 passing / 135 files |
| E2E tests | 60 critical flows |
| GitHub Actions workflows | 18 |
| Frontend pages | 22+ |
| Frontend API proxies | 40+ |
| Frontend components (buscar) | 41 |
| Frontend shared components | 32+ |
| Frontend hooks (shared) | 28 |
| Frontend hooks (buscar) | 9 |

## Appendix B: Environment Variables (Key)

| Variable | Purpose | Default |
|----------|---------|---------|
| `SUPABASE_URL` | Supabase project URL | Required |
| `SUPABASE_SERVICE_ROLE_KEY` | Admin key (bypasses RLS) | Required |
| `OPENAI_API_KEY` | GPT-4.1-nano API key | Required |
| `REDIS_URL` | Redis connection URL | Optional (fallback to in-memory) |
| `STRIPE_SECRET_KEY` | Stripe billing | Required for billing |
| `RESEND_API_KEY` | Email sending | Required for emails |
| `PROCESS_TYPE` | `web` or `worker` | `web` |
| `RUNNER` | `gunicorn` or `uvicorn` | `gunicorn` |
| `WEB_CONCURRENCY` | Gunicorn workers | 2 |
| `GUNICORN_TIMEOUT` | Worker timeout | 120s |
| `GUNICORN_KEEP_ALIVE` | Keep-alive timeout | 75s |
| `LLM_ARBITER_ENABLED` | Enable LLM classification | `true` |
| `LLM_ZERO_MATCH_ENABLED` | Enable zero-match LLM | `true` |
| `VIABILITY_ASSESSMENT_ENABLED` | Enable viability scoring | `true` |
| `SEARCH_RATE_LIMIT_PER_MINUTE` | Per-user search rate limit | 10 |
| `SEARCH_ASYNC_ENABLED` | Enable async search via ARQ | `false` |
| `METRICS_ENABLED` | Enable Prometheus metrics | `true` |

---

*Document generated 2026-03-20 by @architect (Atlas) during Brownfield Discovery Phase 1.*
