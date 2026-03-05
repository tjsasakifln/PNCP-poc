# System Architecture — SmartLic v0.5

**Version:** 4.0
**Date:** 2026-03-04
**Author:** @architect (Atlas) — Brownfield Discovery Phase 2
**Status:** Comprehensive analysis of production codebase on `main` branch (commit `4da1d98`)
**Previous version:** v3.0 (2026-02-25, Archon)
**Delta since v3.0:** 1208 files changed, 190,735 insertions, 33,452 deletions (30+ stories shipped)

---

## Table of Contents

1. [Overview](#1-overview)
2. [System Diagram](#2-system-diagram)
3. [Backend Architecture](#3-backend-architecture)
4. [Frontend Architecture](#4-frontend-architecture)
5. [Infrastructure](#5-infrastructure)
6. [Data Flow](#6-data-flow)
7. [Technical Debt Identified](#7-technical-debt-identified)
8. [Dependencies and External Services](#8-dependencies-and-external-services)

---

## 1. Overview

**SmartLic** is a SaaS platform for automated government procurement opportunity discovery from Brazil's official data sources. It aggregates, classifies, and scores public bids (licitacoes) using AI-powered filtering and viability assessment.

### Key Characteristics

| Attribute | Value |
|---|---|
| **Architecture Style** | Monolithic API + SPA with BFF (Backend-for-Frontend) proxy layer |
| **Stage** | POC avancado (v0.5) in production, beta with trials, pre-revenue |
| **Production URL** | https://smartlic.tech |
| **Primary Data Sources** | PNCP (priority 1), PCP v2 (priority 2), ComprasGov v3 (priority 3, currently offline) |
| **Revenue Model** | SmartLic Pro R$397/mo (monthly), R$357/mo (semiannual), R$297/mo (annual) + Consultoria tier |
| **AI Integration** | GPT-4.1-nano (classification + summaries via OpenAI SDK) |
| **Scale** | Dual-instance deployment (web + worker on Railway), Redis for distributed state |
| **Maturity** | 73 backend Python modules, 31 route modules, 33 frontend pages, 73 Supabase migrations, 285 backend tests, 269 frontend tests |
| **Sectors** | 15 industry verticals with keyword-based classification |
| **Target Audience** | B2G companies (all sizes) + procurement consultancies |

### Tech Stack Summary

**Backend:** FastAPI 0.129, Python 3.12, Pydantic v2, httpx + requests, OpenAI SDK (GPT-4.1-nano), Supabase (PostgreSQL 17 + Auth + RLS), Redis 5.x (cache + circuit breaker + state + streams), ARQ (async job queue), Stripe (billing), Resend (email), Prometheus + OpenTelemetry + Sentry, openpyxl, ReportLab (PDF), PyYAML

**Frontend:** Next.js 16, React 18, TypeScript 5.9, Tailwind CSS 3, Framer Motion, Recharts, Supabase SSR (auth), Sentry, Mixpanel, @dnd-kit (pipeline), Shepherd.js (onboarding), Playwright (E2E)

**Infra:** Railway (web + worker + frontend), Supabase Cloud, Redis (Upstash/Railway), GitHub Actions (17 CI/CD workflows)

---

## 2. System Diagram

```
                                    External Data Sources
                                   +---------------------+
                                   | PNCP API (priority 1)|
                                   | PCP v2 API (priority 2)|
                                   | ComprasGov v3 (priority 3)|
                                   +----------+----------+
                                              |
  User Browser                                |
  +---------+                                 |
  |         |   HTTPS                         |
  |  React  +--------> +------------------+  |
  |  SPA    |          | Next.js 16        |  |    +------------------+
  |         |<--------+| (Railway Frontend)|  |    | OpenAI API       |
  +---------+  SSR +   | Port 8080         |  |    | GPT-4.1-nano     |
               HTML    +--------+---------+  |    +--------+---------+
                                |              |             |
                         API Proxy Routes      |             |
                         (/api/buscar, etc.)   |             |
                                |              |             |
                       +--------v---------+    |    +--------v---------+
                       | FastAPI Backend   +---+    |                  |
                       | (Railway Web)     +--------+ Supabase Cloud   |
                       | Port 8000         |        | PostgreSQL 17    |
                       | 2 Gunicorn Workers|        | Auth + RLS       |
                       +--------+---------+        | Storage           |
                                |                   +------------------+
                       +--------v---------+
                       | Redis             |
                       | (Upstash/Railway) |        +------------------+
                       | - Cache (SWR)     |        | Stripe           |
                       | - SSE Streams     |        | Payments         |
                       | - Circuit Breaker |        +------------------+
                       | - ARQ Job Queue   |
                       +--------+---------+        +------------------+
                                |                   | Resend           |
                       +--------v---------+        | Transactional    |
                       | ARQ Worker        |        | Email            |
                       | (Railway Worker)  +--------+------------------+
                       | LLM summaries     |
                       | Excel generation  |        +------------------+
                       | Email dispatch    |        | Sentry           |
                       +------------------+        | Error Tracking   |
                                                    +------------------+
```

### Request Flow (simplified)

```
Browser -> Next.js middleware (auth check)
        -> API route handler (/api/buscar/route.ts)
           -> getRefreshedToken() (Supabase SSR)
           -> fetch(BACKEND_URL/v1/buscar, { Authorization: Bearer ... })
              -> FastAPI require_auth (JWT validation)
              -> SearchPipeline.run() (7 stages)
              -> SSE progress via /buscar-progress/{search_id}
```

---

## 3. Backend Architecture

### 3.1 Entry Points and Configuration

**`main.py`** (820+ lines) — FastAPI application entry point. Responsibilities:
- Sentry SDK initialization with PII scrubbing
- FastAPI app creation with lifespan context manager
- Middleware stack (CORS, CorrelationID, SecurityHeaders, Deprecation, RateLimit)
- Router registration: 33 routers mounted at `/v1/` prefix AND at root (legacy compat)
- Global exception handlers (validation, RLS, Stripe, generic)
- Background task lifecycle management (10 tasks: cache cleanup, session cleanup, cache refresh, Stripe reconciliation, health canary, revenue share, sector stats, support SLA, daily volume, results cleanup, warmup)
- SIGTERM handler for graceful shutdown

**`config.py`** (500+ lines) — Configuration and feature flags:
- PNCP modality codes and defaults (4 competitive modalities)
- `RetryConfig` dataclass (max_retries, backoff, timeout)
- `PNCPConfig` dataclass (page size, batch size, timeouts)
- CORS origin builder with production/development modes
- Structured logging setup (JSON in production, text in development)
- 25+ feature flags loaded from environment with 60s in-memory cache
- Request-scoped ContextVars for correlation IDs

**`schemas.py`** (1800+ lines) — Pydantic v2 request/response models:
- `BuscaRequest` / `BuscaResponse` — core search contract
- `LicitacaoItem` — bid item with 25+ fields including viability and confidence
- `FilterStats` — per-filter rejection counters
- `DataSourceStatus`, `CoverageMetadata` — multi-source transparency
- Enums: `StatusLicitacao`, `ModalidadeContratacao`, `SearchErrorCode`

### 3.2 Search Pipeline (Core Business Logic)

**`search_pipeline.py`** (800+ lines) — 7-stage decomposition of the search flow:

| Stage | Name | Responsibility |
|-------|------|----------------|
| 1 | ValidateRequest | Input validation, quota check, plan resolution |
| 2 | PrepareSearch | Term parsing, sector config, keyword preparation |
| 3 | ExecuteSearch | Multi-source fetch via ConsolidationService, cache lookup |
| 4 | FilterResults | Keyword matching, status/modality/value/UF filtering, LLM zero-match |
| 5 | EnrichResults | Relevance scoring, viability assessment, sorting |
| 6 | GenerateOutput | LLM summary (via ARQ), Excel generation, item conversion |
| 7 | Persist | Session save, response building, cache write |

**`search_context.py`** — Typed `SearchContext` dataclass carrying intermediate state across all 7 stages. Contains ~30 fields organized by stage (input, validation outputs, search outputs, filter outputs, cache state, error tracking).

**`search_state_manager.py`** — State machine for search lifecycle: `created -> processing -> completed | timed_out | error`.

### 3.3 Data Sources (PNCP, PCP v2, ComprasGov)

All sources implement the `SourceAdapter` abstract base class (`clients/base.py`) with required methods: `fetch()`, `health_check()`, `close()`, and properties `code`, `metadata`.

**PNCP (Priority 1)** — `pncp_client.py` (1500+ lines):
- Dual implementation: `PNCPClient` (sync, requests) + `AsyncPNCPClient` (async, httpx)
- Per-modality fetching with configurable modality list
- Phased UF batching: `PNCP_BATCH_SIZE=5`, `PNCP_BATCH_DELAY_S=2.0s`
- Per-UF timeout: 30s normal, 15s degraded
- Per-modality timeout: 20s
- Circuit breaker: 15 failures threshold, 60s cooldown
- Max page size: 50 (API limit, reduced from 500 in Feb 2026)
- UFs ordered by population for degraded-mode priority

**PCP v2 (Priority 2)** — `clients/portal_compras_client.py`:
- Public API, no authentication required
- Fixed 10/page pagination with `pageCount`/`nextPage`
- Client-side UF filtering only (no server-side UF parameter)
- `valor_estimado=0.0` (v2 API provides no value data)
- Circuit breaker: 15 failures, 60s cooldown (aligned with PNCP)

**ComprasGov v3 (Priority 3)** — `clients/compras_gov_client.py`:
- Dual-endpoint: legacy + Lei 14.133
- Currently OFFLINE as of 2026-03-03 (returns JSON 404)
- Used as last-resort fallback adapter in ConsolidationService

**`consolidation.py`** (400+ lines) — Multi-source orchestration:
- `ConsolidationService` with per-source and global timeouts
- Priority-based deduplication (lower priority number wins)
- Health-aware timeout adjustments (degraded mode)
- Early return when >=80% UFs responded after 80s elapsed
- `AllSourcesFailedError` for cascade failure signaling
- Progressive SSE delivery via `on_source_done` callback

**`bulkhead.py`** — Per-source concurrency isolation:
- Each source gets an `asyncio.Semaphore` with configurable `max_concurrent`
- Prevents one slow source from starving others
- Prometheus metrics: `SOURCE_ACTIVE_REQUESTS`, `SOURCE_POOL_EXHAUSTED`

### 3.4 Filtering and Classification Chain

The filtering pipeline processes bids in a strict order (fail-fast):

```
Raw bids from all sources
  |
  v
1. UF check (fastest — skip if bid not in requested UFs)
  |
  v
2. Value range check (sector-defined min/max)
  |
  v
3. Keyword matching (density scoring via filter.py)
  |  - >5% density -> "keyword" source (ACCEPT)
  |  - 2-5% density -> "llm_standard" (uncertain, send to LLM)
  |  - 1-2% density -> "llm_conservative" (uncertain, send to LLM)
  |
  v
4. LLM zero-match classification (for 0% keyword density)
  |  - GPT-4.1-nano YES/NO decision
  |  - Batch classification for performance (~1.5s for batch vs 8s sequential)
  |  - Feature flag: LLM_ZERO_MATCH_ENABLED
  |
  v
5. Status/date validation
  |
  v
6. Viability assessment (post-filter, orthogonal to relevance)
```

**`filter.py`** (500+ lines) — Keyword matching engine:
- Portuguese stopword removal (100+ stopwords)
- Term validation (min 4 chars, no stopwords)
- Density scoring with phrase matching
- Synonym expansion (when enabled)
- Exclusion term support per sector

**`filter_stats.py`** — Per-filter rejection counters for debugging and analytics.

**`term_parser.py`** — Search term parsing and normalization.

**`relevance.py`** — Relevance scoring: `calculate_min_matches()`, `score_relevance()`, `count_phrase_matches()`.

### 3.5 AI/LLM Integration

**`llm_arbiter.py`** (400+ lines) — GPT-4.1-nano classification:
- Two modes: "uncertain zone" (1-5% density) and "zero-match" (0% density)
- Structured output: `classe (SIM/NAO), confianca (0-100), evidencias, motivo_exclusao`
- Two-level cache: L1 in-memory (MD5 hash key) + L2 Redis (1h TTL, `smartlic:arbiter:` prefix)
- Cost: ~R$0.00007 per structured classification
- Latency: ~60ms per call (structured)
- Fallback: REJECT on LLM failure (zero noise philosophy)
- UX-402: Batch classification for zero-match (~8s reduced to ~1.5s via concurrent calls)

**`llm.py`** — GPT-4.1-nano summary generation:
- `gerar_resumo()` — Full LLM summary with `ResumoLicitacoes` schema
- `gerar_resumo_fallback()` — Deterministic fallback when LLM unavailable
- Summary dispatched as ARQ background job (immediate fallback response)

**`viability.py`** — 4-factor deterministic viability assessment (0-100 score):
- Modalidade (30%): procurement modality accessibility
- Timeline (25%): days until proposal deadline
- Value Fit (25%): bid value vs sector ideal range
- Geography (20%): proximity to user's search regions
- Levels: Alta (>70), Media (40-70), Baixa (<40)

### 3.6 Cache Architecture (Two-Level SWR)

```
Request arrives
  |
  v
L1: InMemoryCache / Redis (4h TTL)
  |-- HIT (fresh, 0-4h) -> serve immediately
  |-- MISS -> check L2
  v
L2: Supabase (24h TTL)
  |-- HIT (stale, 4-24h) -> serve + trigger SWR background revalidation
  |-- MISS -> check L3
  v
L3: Local File (24h TTL, emergency only)
  |-- HIT -> serve (only if Supabase down)
  |-- MISS -> fetch from live sources
```

**`search_cache.py`** (500+ lines):
- 3-level save fallback: Supabase -> Redis -> Local file
- 3-level read fallback: Supabase -> Redis -> Local file
- Cache key includes `date_from`/`date_to` (STORY-306 correctness fix)
- Dual-read: exact key -> legacy key (thundering herd mitigation)
- Stale-While-Revalidate: max 3 concurrent background refreshes, 180s timeout
- Hot/Warm/Cold priority tiering (access frequency-based)

**`redis_pool.py`** (200+ lines):
- Unified async Redis connection pool: `max_connections=50`, `socket_timeout=30s`
- `InMemoryCache` LRU fallback: 10K entries, TTL support, OrderedDict-based
- `get_redis_pool()` / `get_fallback_cache()` — single entry points

**`cache.py`** — Async wrapper over `redis_pool` with automatic fallback.

**`redis_client.py`** — Deprecated shim, redirects to `redis_pool`.

### 3.7 Auth and Authorization

**`auth.py`** (200+ lines) — JWT validation:
- Three-attempt key detection: JWKS endpoint (ES256) -> PEM key (ES256) -> HS256 symmetric
- `PyJWKClient` with 5-minute JWKS cache
- Token validation cache: SHA256 hash key, 60s TTL (~95% reduction in Supabase Auth calls)
- `require_auth` dependency returns `{ sub, email, role, aud, exp }`

**`authorization.py`** — Role-based access:
- `check_user_roles(user_id)` -> `(is_admin, is_master)`
- Admin implies master privileges
- Circuit breaker integration: returns `(False, False)` when Supabase CB open

**`quota.py`** (400+ lines) — Plan-based quota enforcement:
- `PlanCapabilities` TypedDict: max_history_days, allow_excel, allow_pipeline, max_requests_per_month, etc.
- `check_and_increment_quota_atomic()` — atomic DB operation (prevents TOCTOU race)
- In-memory plan status cache with 5min TTL (fallback when Supabase CB open)
- Fail-open on circuit breaker: allow search, log for reconciliation
- Monthly quota reset with grace period (`SUBSCRIPTION_GRACE_DAYS=3`)

**`supabase_client.py`** — Supabase admin client singleton:
- Service role key (bypasses RLS)
- Connection pool: `max_connections=50`, `max_keepalive=20`
- `SupabaseCircuitBreaker`: sliding window 10, 50% threshold, 60s cooldown, 3 trial calls
- `CircuitBreakerOpenError` for fast-fail signaling
- `sb_execute()` wrapper with circuit breaker integration

### 3.8 Billing (Stripe)

**`services/billing.py`** — Subscription management:
- `update_stripe_subscription_billing_period()` — billing period changes
- Stripe handles proration automatically (`proration_behavior="create_prorations"`)
- No custom pro-rata code (removed in GTM-002)
- Billing periods: monthly, semiannual (`interval="month"`, `interval_count=6`), annual

**`webhooks/stripe.py`** — Webhook handlers:
- Signature verification via `stripe.Webhook.construct_event()`
- Idempotency via `stripe_webhook_events` table
- All handlers sync `profiles.plan_type` for fail-to-last-known-plan pattern

**Plans:**
- SmartLic Pro: R$397/mo, R$357/mo (semiannual, 10% off), R$297/mo (annual, 25% off)
- Consultoria: R$997/mo, R$897/mo (semiannual), R$797/mo (annual)
- Legacy plans: consultor_agil, maquina, sala_guerra (functional, marked "(legacy)")
- Free trial: 14 days, no credit card, full feature access

### 3.9 Background Jobs (ARQ)

**`job_queue.py`** (300+ lines):
- Web process enqueues via `get_arq_pool()` -> `enqueue_job()`
- Worker process via `arq job_queue.WorkerSettings`
- Communication: SSE events via `ProgressTracker` (Redis Streams or in-memory)
- Fallback: if Redis/ARQ unavailable, pipeline executes LLM/Excel inline
- Worker restart wrapper: max 10 restarts, 5s delay between attempts
- Worker liveness check: 15s interval, cached health status

**`start.sh`** — Entrypoint script:
- `PROCESS_TYPE=web`: Gunicorn + Uvicorn workers (2 workers, 120s timeout, 75s keep-alive, 1000 max-requests + jitter)
- `PROCESS_TYPE=worker`: ARQ worker with restart loop
- `RUNNER=uvicorn`: Alternative single-process mode (no fork, no SIGSEGV risk)

**`cron_jobs.py`** — Periodic background tasks (asyncio):
- Cache cleanup (6h interval)
- Session cleanup (stale >1h -> timeout, failed >7d -> delete)
- Cache refresh (4h interval, SWR proactive warming)
- Stripe reconciliation
- Health canary (periodic source health checks)
- Revenue share reports, sector stats, support SLA, daily volume, expired results cleanup

### 3.10 Monitoring and Observability

**`metrics.py`** (200+ lines) — Prometheus metrics:
- Graceful degradation: no-op if `prometheus_client` not installed
- Feature flag: `METRICS_ENABLED`
- Key metrics: `SEARCH_DURATION`, `FETCH_DURATION`, `CACHE_HITS/MISSES`, `ACTIVE_SEARCHES`, `LLM_CALLS/DURATION`, `API_ERRORS`, `CIRCUIT_BREAKER_STATE`, `HTTP_RESPONSES_TOTAL`
- Endpoint: `GET /metrics` (protected by `METRICS_TOKEN`)

**`telemetry.py`** — OpenTelemetry distributed tracing:
- Zero overhead when `OTEL_EXPORTER_OTLP_ENDPOINT` not set
- OTLP HTTP exporter (not gRPC, to avoid fork-unsafe C extensions)
- Auto-instrumentation: FastAPI + httpx
- Manual spans: `optional_span()` decorator for pipeline stages
- 10% sampling rate (configurable via `OTEL_SAMPLING_RATE`)

**`health.py`** — System health checks:
- Per-source availability status
- `HealthStatus` enum: healthy, degraded, unhealthy

**Sentry** — Error tracking:
- Backend: `sentry-sdk[fastapi]` with PII scrubbing (`before_send` callback)
- Frontend: `@sentry/nextjs` with source maps and tunnel route
- Transient error fingerprinting for httpx timeouts

**Structured Logging:**
- Production: JSON format via `python-json-logger`
- Correlation fields: `request_id`, `search_id`, `correlation_id`
- PII masking: `log_sanitizer.py` (email, token, user ID, IP)

### 3.11 API Routes (31 modules, 60+ endpoints)

| Module | Key Endpoints | Purpose |
|--------|--------------|---------|
| `search.py` | `POST /buscar`, `GET /buscar-progress/{id}` (SSE) | Core search + progress |
| `pipeline.py` | `POST/GET/PATCH/DELETE /pipeline` | Opportunity kanban |
| `billing.py` | `POST /checkout`, `POST /billing-portal` | Stripe checkout |
| `plans.py` | `GET /plans` | Plan listing with prices |
| `user.py` | `GET /me`, `PUT /profile/context`, `GET /trial-status` | User profile |
| `analytics.py` | `GET /summary`, `GET /trial-value` | Dashboard analytics |
| `feedback.py` | `POST/DELETE /feedback` | User feedback loop |
| `sessions.py` | `GET /sessions` | Search history |
| `messages.py` | `POST/GET /conversations`, `POST /{id}/reply` | Messaging |
| `auth_oauth.py` | `GET /google`, `GET /google/callback` | Google OAuth |
| `onboarding.py` | `POST /first-analysis` | Onboarding wizard |
| `pipeline.py` | `GET /pipeline/alerts` | Pipeline alerts |
| `alerts.py` | Email alert CRUD | Alert subscriptions |
| `bid_analysis.py` | Deep bid analysis | AI-powered bid analysis |
| `mfa.py` | TOTP + recovery codes | Multi-factor auth |
| `organizations.py` | Organization CRUD | Multi-user orgs |
| `partners.py` | Revenue share | Partner program |
| `reports.py` | PDF diagnostico | PDF report generation |
| `sectors_public.py` | Public sector listing | SEO landing pages |
| `slo.py` | SLO dashboard | Admin SLO metrics |
| `admin_trace.py` | Search trace | Admin debugging |
| `health.py` | Cache health | Admin cache inspection |
| `metrics_api.py` | Discard rate | Filter analytics |
| `subscriptions.py` | Subscription status | Subscription queries |
| `features.py` | Feature flags | Runtime flag management |
| `export_sheets.py` | Google Sheets export | Sheet integration |
| `emails.py` | Email management | Email preferences |
| `auth_email.py` | Email confirmation | Auth recovery |
| `auth_check.py` | Email/phone availability | Registration checks |
| `trial_emails.py` | Trial email sequence | Trial reminders |
| `blog_stats.py` | Blog stats | Programmatic SEO |

All routers mounted twice: `/v1/<path>` (versioned) + `/<path>` (legacy, deprecated with `Sunset: 2026-06-01` header).

---

## 4. Frontend Architecture

### 4.1 Pages and Routes

33 pages in `frontend/app/` (Next.js App Router):

| Route | Purpose |
|-------|---------|
| `/` | Landing page (marketing) |
| `/login`, `/signup` | Email/password + Google OAuth |
| `/auth/callback` | OAuth callback handler |
| `/recuperar-senha`, `/redefinir-senha` | Password reset flow |
| `/onboarding` | 3-step wizard (CNAE -> UFs -> Confirmation + auto-search) |
| `/buscar` | **Main search page** — filters, SSE progress, results |
| `/dashboard` | Analytics dashboard with charts |
| `/historico` | Search history list |
| `/pipeline` | Opportunity kanban (drag-and-drop) |
| `/mensagens` | Messaging system |
| `/conta` | Account settings |
| `/alertas` | Email alert preferences |
| `/planos`, `/planos/obrigado` | Pricing + thank you |
| `/pricing`, `/features` | Marketing pages |
| `/ajuda` | Help center |
| `/admin`, `/admin/cache` | Admin dashboards |
| `/termos`, `/privacidade` | Legal pages |
| `/blog` | Blog with programmatic SEO |
| `/licitacoes` | SEO sector landing pages |
| `/como-avaliar-licitacao`, `/como-evitar-prejuizo-licitacao`, etc. | SEO content pages |
| `/sitemap.ts` | Dynamic sitemap generation |

### 4.2 Key Components

**Search Components** (`app/buscar/components/`, 29 files):
- `SearchForm.tsx` — Main search form with UF selector, sector picker, date range
- `SearchResults.tsx` — Results list with pagination
- `FilterPanel.tsx` — Advanced filters (status, modality, value range, esfera)
- `UfProgressGrid.tsx` — Per-UF progress visualization
- `ErrorDetail.tsx` — Structured error display (7 error codes)
- `ViabilityBadge.tsx`, `LlmSourceBadge.tsx`, `ReliabilityBadge.tsx` — AI metadata badges
- `FeedbackButtons.tsx` — Thumbs up/down per result
- `SourceStatusGrid.tsx`, `SourcesUnavailable.tsx` — Multi-source transparency
- `CacheBanner.tsx` (via `RefreshBanner`, `ExpiredCacheBanner`) — Stale data indicators
- `PartialResultsPrompt.tsx`, `PartialTimeoutBanner.tsx` — Degraded mode UX
- `SearchStateManager.tsx` — Client-side state management for search lifecycle
- `ZeroResultsSuggestions.tsx` — Empathetic empty state with actionable suggestions

**Shared Components** (`components/`, 50+ files):
- `NavigationShell.tsx`, `Sidebar.tsx`, `BottomNav.tsx` — App layout
- `BackendStatusIndicator.tsx` — Backend health polling (30s, visibility-gated)
- `EnhancedLoadingProgress.tsx` — Educational B2G carousel during search
- `ErrorStateWithRetry.tsx` — Retry UI with exponential backoff
- `billing/PlanCard.tsx`, `PlanToggle.tsx` — Pricing components
- `landing/` — Marketing landing page components
- `ui/` — Primitive UI components

### 4.3 API Proxy Pattern

38 API proxy routes in `frontend/app/api/` proxy requests to the backend:

```
Browser -> /api/buscar (Next.js route handler)
        -> getRefreshedToken() (Supabase SSR, server-side)
        -> fetch(BACKEND_URL/v1/buscar, { Authorization: Bearer <refreshed_token> })
        -> parse response, add error context
        -> return to browser
```

Key proxies: `buscar`, `buscar-progress` (SSE), `analytics`, `pipeline`, `feedback`, `plans`, `billing-portal`, `sessions`, `trial-status`, `subscription-status`, `search-history`, `alert-preferences`, `organizations`, `reports`, `setores`, `mfa`, etc.

The proxy layer:
- Refreshes Supabase tokens server-side (prevents expired token errors)
- Translates backend error codes to Portuguese user messages
- Sanitizes error details (never exposes stack traces)
- Adds `X-Request-ID` header for correlation
- SSE proxy uses `undici.Agent({ bodyTimeout: 0 })` to prevent timeout on long streams
- AbortController linked to `request.signal` for client disconnect cleanup

### 4.4 State Management

No global state library (Redux, Zustand, etc.). State is managed via:

- **React hooks** — Component-local state with `useState`/`useReducer`
- **Custom hooks**:
  - `useSearch.ts` — Search lifecycle, SSE connection, retry logic (3 retries, exponential backoff)
  - `useSearchFilters.ts` — Sector/UF/modality filter state with localStorage persistence
  - `useUfProgress.ts` — Per-UF progress tracking from SSE events
  - `useInView.ts` — Intersection observer for lazy loading
- **Supabase SSR** — Auth state via `@supabase/ssr` (cookie-based, server-side refresh)
- **localStorage** — Plan cache (1hr TTL), filter preferences, theme, sector fallback

### 4.5 SSE Progress Tracking

Dual-connection pattern:
1. `GET /api/buscar-progress/{search_id}` — SSE stream for real-time progress
2. `POST /api/buscar` — JSON response with final results

```
Frontend                           Backend
  |                                  |
  |-- POST /buscar (search_id) ----->|  (starts pipeline)
  |-- GET /buscar-progress/{id} ---->|  (opens SSE stream)
  |                                  |
  |<-- SSE: connecting (10%) --------|
  |<-- SSE: fetching (30%) ----------|  (per-UF progress)
  |<-- SSE: filtering (60%) ---------|
  |<-- SSE: complete (100%) ---------|
  |<-- SSE: llm_ready --------------|  (background job done)
  |<-- SSE: excel_ready -------------|  (background job done)
  |                                  |
  |<-- JSON response (final) --------|
```

**Backend** (`progress.py`):
- `ProgressTracker` per search operation
- Redis Streams (at-least-once delivery, replay from any point)
- In-memory `asyncio.Queue` fallback when Redis unavailable
- Heartbeat: `: waiting\n\n` every 5s during tracker wait, `: heartbeat\n\n` every 15s
- Terminal stages trigger 5-minute stream EXPIRE

**Frontend** graceful fallback: if SSE connection fails, uses calibrated time-based simulation with educational carousel.

---

## 5. Infrastructure

### 5.1 Railway Deployment

Three Railway services from the same codebase:

| Service | Process Type | Port | Resources |
|---------|-------------|------|-----------|
| `bidiq-backend` (web) | `PROCESS_TYPE=web` | 8000 | 1GB RAM, 2 Gunicorn workers |
| `bidiq-worker` | `PROCESS_TYPE=worker` | N/A | ARQ worker (LLM + Excel) |
| `bidiq-frontend` | Next.js standalone | 8080 | Node.js server |

**Dockerfile** (`backend/Dockerfile`):
- Base: `python:3.12-slim`
- Aggressive removal of fork-unsafe C extensions: grpcio, httptools, uvloop
- Post-install verification: `pip list | grep -iE "grpc|uvloop|httptools"`

**Gunicorn Configuration** (`start.sh`):
- 2 workers (`WEB_CONCURRENCY=2`, reduced from 4 due to Railway 1GB OOM)
- Timeout: 120s (`GUNICORN_TIMEOUT`)
- Keep-alive: 75s (> Railway proxy 60s, prevents intermittent 502s)
- Max-requests: 1000 + jitter 50 (worker recycling for memory leak prevention)
- Graceful timeout: 30s
- `gunicorn_conf.py` for worker lifecycle hooks

**Railway specifics:**
- Hard timeout: ~300s (5 minutes, not 120s as originally assumed)
- Health check: `/health` with `healthcheckTimeout=300s`
- No container sleep (unlike Render/Heroku)
- `railway.toml` / `railway-worker.toml` for service configuration

### 5.2 CI/CD Pipelines

17 GitHub Actions workflows in `.github/workflows/`:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `backend-tests.yml` | PR/push | Backend pytest suite |
| `frontend-tests.yml` | PR/push | Frontend Jest suite |
| `e2e.yml` | PR/push | Playwright E2E tests |
| `deploy.yml` | Push to main | Production deployment + migration auto-apply |
| `staging-deploy.yml` | Push to staging | Staging deployment |
| `pr-validation.yml` | PR | PR validation checks |
| `migration-gate.yml` | PR (migrations) | Warning comment for pending migrations |
| `migration-check.yml` | Push to main + daily | Block if unapplied migrations |
| `backend-ci.yml` | Various | Backend CI checks |
| `codeql.yml` | Schedule | Security analysis |
| `cleanup.yml` | Schedule | Repository cleanup |
| `dependabot-auto-merge.yml` | Dependabot PR | Auto-merge minor/patch updates |
| `lighthouse.yml` | Manual | Lighthouse performance audit |
| `load-test.yml` | Manual | Locust load testing |
| `sync-sectors.yml` | Manual | Sector data synchronization |
| `tests.yml` | Various | Combined test runner |

**Deploy pipeline** (`deploy.yml`):
1. Run tests
2. Deploy backend to Railway
3. Auto-apply Supabase migrations (`supabase db push --include-all`)
4. Send `NOTIFY pgrst, 'reload schema'` for PostgREST cache refresh
5. Smoke test (verify no PGRST205 errors)

### 5.3 Environment Configuration

Key environment variables (from `config.py` and `.env.example`):

| Category | Variables |
|----------|-----------|
| **Core** | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET` |
| **Redis** | `REDIS_URL` |
| **OpenAI** | `OPENAI_API_KEY` |
| **Stripe** | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID_*` |
| **Email** | `RESEND_API_KEY` |
| **Sentry** | `SENTRY_DSN` |
| **Observability** | `OTEL_EXPORTER_OTLP_ENDPOINT`, `METRICS_TOKEN` |
| **PNCP Tuning** | `PNCP_BATCH_SIZE`, `PNCP_BATCH_DELAY_S`, `PNCP_TIMEOUT_PER_UF`, `PNCP_TIMEOUT_PER_MODALITY` |
| **Circuit Breakers** | `PNCP_CIRCUIT_BREAKER_THRESHOLD`, `PNCP_CIRCUIT_BREAKER_COOLDOWN` |
| **Feature Flags** | `LLM_ZERO_MATCH_ENABLED`, `LLM_ARBITER_ENABLED`, `VIABILITY_ASSESSMENT_ENABLED`, etc. |
| **Process** | `PROCESS_TYPE`, `PORT`, `WEB_CONCURRENCY`, `GUNICORN_TIMEOUT` |

---

## 6. Data Flow

### End-to-End Search Request

```
1. User enters search criteria (sector, UFs, date range) on /buscar
   |
2. Frontend generates search_id (UUID), opens SSE connection to /buscar-progress/{id}
   |
3. POST /api/buscar (Next.js proxy) -> refreshes token -> POST /v1/buscar (FastAPI)
   |
4. Stage 1 — ValidateRequest
   |  - JWT validation (auth.py)
   |  - Quota check (quota.py check_and_increment_quota_atomic)
   |  - Plan resolution (is_admin, is_master, capabilities)
   |
5. Stage 2 — PrepareSearch
   |  - Load sector config from sectors_data.yaml
   |  - Parse search terms (term_parser.py)
   |  - Build keyword sets (active_keywords, active_exclusions)
   |
6. Stage 3 — ExecuteSearch
   |  - Check L1/L2/L3 cache (search_cache.py)
   |  - If cache MISS: ConsolidationService.fetch_all()
   |    - Parallel fetch from PNCP + PCP v2 (+ ComprasGov if online)
   |    - Bulkhead isolation per source
   |    - Circuit breaker checks
   |    - Priority-based deduplication
   |    - SSE progress events per UF
   |  - If cache HIT (stale): serve + trigger SWR background revalidation
   |
7. Stage 4 — FilterResults
   |  - UF check -> Value range -> Keyword matching -> LLM zero-match -> Status validation
   |  - filter_stats tracking for each rejection reason
   |
8. Stage 5 — EnrichResults
   |  - Relevance scoring per bid
   |  - Viability assessment (4 factors, 0-100 score)
   |  - Sort by relevance (descending)
   |
9. Stage 6 — GenerateOutput
   |  - Convert to LicitacaoItem objects
   |  - Enqueue LLM summary job (ARQ, async)
   |  - Enqueue Excel generation job (ARQ, async)
   |  - Immediate response with gerar_resumo_fallback()
   |
10. Stage 7 — Persist
    |  - Save search session to Supabase
    |  - Write results to cache (L1 + L2)
    |  - Build BuscaResponse with coverage metadata
    |  - SSE: "complete" event
    |
11. Background (ARQ worker):
    |  - LLM summary generated -> SSE: "llm_ready" event
    |  - Excel file generated + uploaded to Supabase Storage -> SSE: "excel_ready" event
    |
12. Frontend receives JSON response + SSE events
    |  - Renders results with viability badges, confidence indicators
    |  - Updates UI when llm_ready/excel_ready arrive
```

### Timeout Chain (Strict Decreasing)

```
Railway Hard Timeout (300s)
  > Gunicorn Timeout (120s)
    > Pipeline Total (110s)
      > Consolidation Global (100s)
        > Per-Source (80s, degraded mode)
          > Per-UF (30s normal, 15s degraded)
            > Per-Modality (20s)
              > HTTP Request (10s)
```

Skip LLM after 90s elapsed, skip viability after 100s elapsed.

---

## 7. Technical Debt Identified

### 7.1 Architecture Debts

| ID | Severity | Issue | Location | Impact |
|---|---|---|---|---|
| TD-A01 | **High** | Routes mounted twice (versioned `/v1/` + legacy root) | `main.py` L710-778 | 61 `include_router` calls (33 versioned + 28 legacy). Doubles the route table to 120+ endpoints. Sunset date 2026-06-01 set but no migration plan exists. Frontend proxy routes all target versioned endpoints already; legacy mounts serve no known consumer. |
| TD-A02 | **High** | `search_pipeline.py` is the new god module | `search_pipeline.py` | After STORY-216 decomposition from main.py, absorbed all business logic. 800+ lines with inline helpers, cache logic, quota email logic, and item conversion. Each "stage" method is 50-100+ lines with nested try/catch. |
| TD-A03 | **High** | In-memory progress tracker not horizontally scalable | `progress.py` `_active_trackers` | Redis Streams mode exists but in-memory `asyncio.Queue` is the primary fallback. Two Railway web instances would have split progress state. Main blocker for horizontal scaling. |
| TD-A04 | **Medium** | 10 background tasks in lifespan | `main.py` L430-620 | cache_cleanup, session_cleanup, cache_refresh, stripe_reconciliation, health_canary, revenue_share, sector_stats, support_sla, daily_volume, results_cleanup, warmup. Each with its own cancel/await pattern. No task manager abstraction. |
| TD-A05 | **Medium** | Dual HTTP client (sync + async) for PNCP | `pncp_client.py` | `PNCPClient` (sync, `requests`) and `AsyncPNCPClient` (async, `httpx`) duplicate 1500+ lines of retry logic, circuit breaker integration, and error handling. Sync client used only as `asyncio.to_thread()` fallback. |
| TD-A06 | **Low** | Lead prospecting modules disconnected | `lead_prospecting.py`, `lead_scorer.py`, `lead_deduplicator.py`, `contact_searcher.py`, `cli_acha_leads.py` | 5 modules appear disconnected from the main search pipeline. Possibly dead code from feature exploration. |

### 7.2 Pattern Inconsistencies

| ID | Severity | Issue | Location |
|---|---|---|---|
| TD-P01 | **Medium** | Migration naming inconsistency | `supabase/migrations/` | Mixed: `001_profiles.sql` through `033_fix_missing.sql` (sequential) + `20260220120000_*` (timestamped). 73 total migrations. |
| TD-P02 | **Medium** | Feature flags only in env vars | `config.py` | 25+ flags with 60s in-memory cache. No UI for runtime toggling. Requires container restart or admin reload endpoint. |
| TD-P03 | **Low** | Hardcoded User-Agent references BidIQ | `pncp_client.py` | `"BidIQ/1.0 (procurement-search; contact@bidiq.com.br)"` — misleading for API providers. |
| TD-P04 | **Low** | `pyproject.toml` references "bidiq-uniformes-backend" | `backend/pyproject.toml` | Old branding not updated. |
| TD-P05 | **Low** | Test files in backend root | `backend/test_pncp_homologados_discovery.py`, etc. | Test files outside `tests/` directory break convention. |

### 7.3 Missing Abstractions

| ID | Severity | Issue | Location |
|---|---|---|---|
| TD-M01 | **Medium** | No background task lifecycle manager | `main.py` | 10 background tasks each with manual create/cancel/await. Should have a `TaskRegistry` or similar abstraction. |
| TD-M02 | **Medium** | No API contract validation in CI | CI | `openapi-typescript` generates frontend types but no CI step validates they match the backend OpenAPI schema. Drift detection only via snapshot tests. |
| TD-M03 | **Low** | No pre-commit hooks | Repository root | No `.pre-commit-config.yaml`. Developers can commit code failing lint/type checks. |
| TD-M04 | **Low** | No backend linting enforcement in CI | `.github/workflows/` | `ruff` and `mypy` configured in `pyproject.toml` but not enforced in any CI workflow. |

### 7.4 Scalability Concerns

| ID | Severity | Issue | Location |
|---|---|---|---|
| TD-S01 | **High** | Railway 1GB memory with 2 workers | `start.sh` | Each Gunicorn worker maintains its own in-memory caches (auth tokens, LLM decisions, plan capabilities, feature flags). OOM kills observed historically (WEB_CONCURRENCY reduced from 4 to 2). |
| TD-S02 | **High** | PNCP page size reduced to 50 | `pncp_client.py` | API limit change from 500 to 50 requires 10x more API calls. Health canary (`tamanhoPagina=10`) does not detect this limit. |
| TD-S03 | **Medium** | In-memory auth token cache not shared | `auth.py` `_token_cache` | Each Gunicorn worker has its own cache. Not a correctness issue but wastes memory. |
| TD-S04 | **Medium** | No CDN for static assets | Infrastructure | Frontend served directly from Railway without edge caching. |
| TD-S05 | **Medium** | `synchronous sleep` in quota.py | `quota.py` | `time.sleep(0.3)` for retry delay blocks the async event loop. Should use `asyncio.sleep()`. |

### 7.5 Security Observations

| ID | Severity | Issue | Location |
|---|---|---|---|
| TD-SEC01 | **Medium** | `unsafe-inline` and `unsafe-eval` in CSP | `frontend/next.config.js` | Required by Next.js + Stripe.js but weakens CSP. Should evaluate nonce-based approach. |
| TD-SEC02 | **Low** | Service role key for all backend ops | `supabase_client.py` | Backend bypasses RLS for all operations. Intentional for server-to-server but any backend vuln exposes all data. |
| TD-SEC03 | **Low** | No webhook request timeout | `webhooks/stripe.py` | Long-running DB operations in webhook handler could block indefinitely. |
| TD-SEC04 | **Low** | Excel temp files in frontend proxy | `frontend/app/api/buscar/route.ts` | Writes base64 Excel to `tmpdir()` as fallback. Not cleaned on crash, potential disk exhaustion. |

---

## 8. Dependencies and External Services

### 8.1 Backend Dependencies (Pinned)

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.129.0 | Web framework |
| uvicorn | 0.41.0 | ASGI server (without `[standard]` extras to avoid uvloop) |
| gunicorn | 23.0.0 | Process manager |
| pydantic[email] | 2.12.5 | Request/response validation |
| starlette | 0.52.1 | ASGI middleware |
| httpx | 0.28.1 | Async HTTP client |
| requests | 2.32.3 | Sync HTTP client (PNCP legacy) |
| openpyxl | 3.1.5 | Excel generation |
| reportlab | 4.4.0 | PDF generation |
| openai | 1.109.1 | GPT-4.1-nano SDK |
| supabase | 2.28.0 | Database + Auth |
| PyJWT | 2.11.0 | JWT validation (ES256/JWKS + HS256) |
| stripe | 11.4.1 | Payment processing |
| redis | 5.3.1 | Cache + job queue + SSE |
| arq | >=0.26 | Async job queue |
| resend | >=2.0.0 | Transactional email |
| cryptography | 46.0.5 | ES256 JWT support (pinned for fork-safety) |
| google-api-python-client | 2.190.0 | Google Sheets integration |
| sentry-sdk[fastapi] | >=2.0.0 | Error tracking |
| prometheus_client | >=0.20.0 | Metrics |
| opentelemetry-api/sdk | >=1.25 | Distributed tracing |
| PyYAML | >=6.0 | Sector config loading |
| python-json-logger | >=2.0.4 | Structured logging |
| bcrypt | >=4.0.0 | MFA recovery code hashing |

### 8.2 Frontend Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| next | ^16.1.6 | React framework |
| react / react-dom | ^18.3.1 | UI library |
| typescript | ^5.9.3 | Type safety |
| tailwindcss | ^3.4.19 | CSS utility framework |
| framer-motion | ^12.33.0 | Animations |
| recharts | ^3.7.0 | Dashboard charts |
| @supabase/ssr | ^0.8.0 | Server-side auth |
| @supabase/supabase-js | ^2.95.3 | Supabase client |
| @sentry/nextjs | ^10.38.0 | Error tracking |
| mixpanel-browser | ^2.74.0 | Product analytics |
| @dnd-kit/core | ^6.3.1 | Pipeline drag-and-drop |
| shepherd.js | ^14.5.1 | Onboarding tours |
| lucide-react | ^0.563.0 | Icons |
| date-fns | ^4.1.0 | Date formatting |
| sonner | ^2.0.7 | Toast notifications |
| @playwright/test | ^1.58.2 | E2E testing |
| jest | ^29.7.0 | Unit testing |

### 8.3 External Services

| Service | Purpose | Cost Model |
|---------|---------|------------|
| **Railway** | Backend (web + worker) + Frontend hosting | Usage-based |
| **Supabase Cloud** | PostgreSQL 17, Auth, Storage, RLS | Free tier -> Pro |
| **Redis** (Upstash/Railway) | Cache, SSE, circuit breaker, job queue | Usage-based |
| **OpenAI** | GPT-4.1-nano classification + summaries | ~R$0.00007/classification |
| **Stripe** | Subscriptions, checkout, webhooks | 2.9% + R$0.39/transaction |
| **Resend** | Transactional email | Free tier (1 domain) |
| **Sentry** | Error tracking (BE + FE) | Free tier -> Team |
| **Mixpanel** | Product analytics (FE) | Free tier |
| **Google Analytics** | Web analytics (LGPD compliant) | Free |
| **GitHub Actions** | CI/CD (17 workflows) | Free tier |

### 8.4 Data Sources

| Source | API URL | Priority | Auth | Status |
|--------|---------|----------|------|--------|
| PNCP | `pncp.gov.br/api/consulta/v1/contratacoes/publicacao` | 1 | None (public) | Active |
| PCP v2 | `compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos` | 2 | None (public) | Active |
| ComprasGov v3 | `dadosabertos.compras.gov.br` | 3 | None (public) | **OFFLINE** (since 2026-03-03) |

---

*End of System Architecture Document — SmartLic v4.0*
*Generated 2026-03-04 by @architect (Atlas) during Brownfield Discovery Phase 2*
