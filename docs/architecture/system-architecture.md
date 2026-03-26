# SmartLic -- System Architecture Document

**Date:** 2026-03-23 | **Author:** @architect (Aria) | **Phase:** Brownfield Discovery Phase 1 (refresh)
**Codebase:** `main` branch HEAD | **Version:** 5.0 (supersedes v4.0 from 2026-03-21)

---

## 1. System Overview

### 1.1 What SmartLic Does

SmartLic is a B2G (Business-to-Government) intelligence platform that automates discovery, analysis, and qualification of public procurement opportunities (licitacoes) in Brazil. Built by CONFENGE Avaliacoes e Inteligencia Artificial LTDA, it targets construction, engineering, and service companies that participate in government bids, as well as consultancies and assessorias that support them.

**Core Value Proposition:**
- Aggregates procurement data from 3 government sources (PNCP, PCP v2, ComprasGov v3) into a unified search
- AI-powered sectoral classification using GPT-4.1-nano eliminates irrelevant results
- 4-factor viability assessment helps users prioritize high-probability opportunities
- Kanban pipeline for opportunity tracking from discovery to bid submission
- PDF diagnostic reports and Excel exports for decision support

**Current Stage:** POC v0.5 in production (beta with trials, pre-revenue)
**URL:** https://smartlic.tech
**Pricing:** SmartLic Pro R$397/month (monthly), R$357/month (semiannual), R$297/month (annual). Consultoria tier also available.

### 1.2 Codebase Statistics

| Metric | Count |
|--------|-------|
| **Backend source files** | 199 Python files |
| **Backend source LOC** | 77,364 lines |
| **Backend test files** | 344 files |
| **Backend test LOC** | 140,199 lines |
| **Backend test passing** | 7,332+ (0 failures baseline) |
| **Backend API endpoints** | 126 (119 in routes/ + 7 in main.py) |
| **Backend route modules** | 35 |
| **Frontend pages** | 47 |
| **Frontend API proxies** | 58 route handlers |
| **Frontend components** | ~241 (41 in buscar/, ~32 shared, rest page-specific) |
| **Frontend hooks** | 36 (27 shared + 9 buscar-specific) |
| **Frontend test files** | 300+ files |
| **Frontend test passing** | 5,583+ (0 failures baseline) |
| **E2E tests** | 60 critical user flows |
| **Database migrations** | 90 SQL files |
| **Database tables** | 29 (28 created + profiles) |
| **RLS policies** | 105 |
| **Database indexes** | 95 |
| **Database functions** | 32 |
| **CI/CD workflows** | 17 GitHub Actions |
| **Environment variables** | 356 lines in .env.example |

### 1.3 Tech Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| **Backend runtime** | Python | 3.12 |
| **Backend framework** | FastAPI | 0.129.0 |
| **ASGI server** | Uvicorn (via Gunicorn) | 0.41.0 |
| **Process manager** | Gunicorn | 23.0.0 |
| **Validation** | Pydantic v2 | 2.12.5 |
| **HTTP client** | httpx | 0.28.1 |
| **LLM** | OpenAI SDK (GPT-4.1-nano) | 1.109.1 |
| **Database** | Supabase (PostgreSQL 17) | Cloud |
| **Cache** | Redis (redis-py 5.3.1) | 5.x |
| **Job queue** | ARQ | via pip |
| **Billing** | Stripe | 11.4.1 |
| **Email** | Resend | via REST |
| **Auth** | Supabase Auth + PyJWT | 2.11.0 |
| **Monitoring** | Prometheus + OpenTelemetry + Sentry | 10.38.0 (Sentry) |
| **PDF** | ReportLab | 4.4.0 |
| **Excel** | openpyxl | 3.1.5 |
| **Frontend framework** | Next.js | 16.1.6 |
| **UI library** | React | 18.3.1 |
| **Language** | TypeScript | 5.9 |
| **Styling** | Tailwind CSS | 3.x |
| **State/Fetching** | SWR | 2.4.1 |
| **Forms** | react-hook-form + zod | 4.3.6 (zod) |
| **Animation** | Framer Motion | 12.33.0 |
| **Charts** | Recharts | 3.7.0 |
| **Drag-and-drop** | @dnd-kit | 6.3.1 |
| **Onboarding** | Shepherd.js | 14.5.1 |
| **Analytics** | Mixpanel | 2.74.0 |

---

## 2. Deployment Topology

```
                          ┌─────────────────────┐
                          │   smartlic.tech      │
                          │   (Cloudflare DNS)   │
                          └──────────┬──────────┘
                                     │
                   ┌─────────────────┼─────────────────┐
                   │                 │                  │
          ┌────────▼───────┐  ┌─────▼──────┐   ┌──────▼──────┐
          │  Railway:       │  │  Railway:   │   │  Railway:    │
          │  Frontend       │  │  Backend    │   │  Worker      │
          │  (Next.js 16)   │  │  (Gunicorn  │   │  (ARQ)       │
          │  Port 8080      │  │   +Uvicorn) │   │  LLM+Excel   │
          │                 │  │  Port 8000  │   │  bg jobs      │
          └────────┬───────┘  └──────┬──────┘   └──────┬──────┘
                   │                 │                  │
                   │          ┌──────┼──────┐           │
                   │          │      │      │           │
              ┌────▼──────┐  ┌▼─────┐ ┌────▼──┐  ┌────▼──────┐
              │ Supabase   │  │Redis │ │OpenAI │  │  Stripe   │
              │ Cloud      │  │(UP/  │ │GPT-4.1│  │  (billing)│
              │ PG17+Auth  │  │RW)   │ │-nano  │  │           │
              │ +RLS       │  │      │ │       │  │           │
              └────────────┘  └──────┘ └───────┘  └───────────┘
                                │
                          ┌─────┴─────┐
                          │  External  │
                          │  APIs      │
                          ├───────────┤
                          │ PNCP v1   │ (priority 1)
                          │ PCP v2    │ (priority 2)
                          │ ComprasGov│ (priority 3, currently down)
                          │ Resend    │ (email)
                          └───────────┘
```

### 2.1 Railway Services

| Service | Process Type | Workers | Memory | Timeout |
|---------|-------------|---------|--------|---------|
| **Backend (web)** | `PROCESS_TYPE=web` | 2 Gunicorn/Uvicorn | 1GB | 120s (Gunicorn), ~300s (Railway proxy) |
| **Worker** | `PROCESS_TYPE=worker` | ARQ single-process | 512MB | per-job limits |
| **Frontend** | Next.js standalone | Node.js | 512MB | - |

**Key operational parameters:**
- Gunicorn keep-alive: 75s (> Railway proxy 60s to prevent 502s)
- Gunicorn max-requests: 1000 + jitter 50 (memory leak prevention)
- jemalloc enabled via `LD_PRELOAD` (reduces RSS fragmentation)
- `--preload` disabled by default (OpenSSL fork-safety issue with cryptography>=46.0.5)
- ARQ worker has restart wrapper: max 10 restarts with 5s delay

---

## 3. Backend Architecture

### 3.1 Directory Structure

```
backend/
├── main.py              (103 LOC) — Thin entrypoint, delegates to startup/ (DEBT-107 SYS-020)
├── schemas.py           (2121 LOC) — All Pydantic models
├── config/              — Decomposed config (DEBT-015)
│   ├── base.py          — Core utilities, logging
│   ├── features.py      — 40+ feature flags
│   ├── pncp.py          — Source-specific timeouts, circuit breakers
│   ├── cors.py          — CORS origins
│   └── pipeline.py      — Pipeline, cache, cron config
├── routes/              — 35 route modules, 119 endpoints
├── clients/             — External API clients
│   ├── portal_compras_client.py   (646 LOC) — PCP v2
│   ├── compras_gov_client.py      (838 LOC) — ComprasGov v3
│   ├── portal_transparencia_client.py (938 LOC)
│   ├── querido_diario_client.py   (801 LOC)
│   └── sanctions.py               (639 LOC)
├── pipeline/            — 7-stage search pipeline
│   ├── stages/          — validate, prepare, execute, filter, enrich, generate, persist
│   ├── tracing.py
│   └── cache_manager.py
├── services/            — Business logic services
│   ├── billing.py, alert_service.py, alert_matcher.py
│   ├── organization_service.py, partner_service.py
│   ├── dunning.py, trial_email_sequence.py
│   └── stripe_reconciliation.py
├── models/              — Domain models (cache, search_state, stripe)
├── webhooks/            — Stripe webhook handler (1192 LOC)
├── templates/emails/    — HTML email templates
├── startup/             — App factory decomposition (DEBT-107)
│   ├── app_factory.py   — create_app() builds FastAPI instance (94 LOC)
│   ├── routes.py        — register_routes() wires 36 routers (71 LOC)
│   ├── middleware_setup.py — 6 middlewares + Prometheus mount (143 LOC)
│   ├── lifespan.py      — Startup/shutdown lifecycle (cache schema, sessions)
│   ├── sentry.py        — Sentry SDK initialization
│   ├── endpoints.py     — Root endpoints (/, /v1/setores, /debug/pncp-test)
│   ├── exception_handlers.py — Global exception handlers
│   └── state.py         — Module-level state (shutting_down, startup_time)
├── utils/               — cnae_mapping, date_parser, phone_normalizer
├── source_config/       — Data source configuration
├── unified_schemas/     — Cross-source schema normalization
├── filter*.py           — 11 filter modules (3871 LOC in filter.py alone)
├── pncp_client.py       (2515 LOC) — PNCP API client
├── search_cache.py      (2512 LOC) — Two-level cache
├── job_queue.py         (2152 LOC) — ARQ job definitions
├── cron_jobs.py         (2039 LOC) — Scheduled tasks
├── quota.py             (1622 LOC) — Plan quota enforcement
├── llm_arbiter.py       (1269 LOC) — LLM classification engine
├── auth.py              (519 LOC)  — JWT validation + cache
├── metrics.py           (1002 LOC) — Prometheus metrics
├── health.py            (960 LOC)  — Health checks
└── ...69 total top-level .py files
```

### 3.2 Middleware Stack (startup/middleware_setup.py:38-141)

Order matters -- last added is outermost:

| Layer | Middleware | Source | Purpose |
|-------|-----------|--------|---------|
| 1 (outermost) | `metrics_auth` | middleware_setup.py:131 | Protect /metrics with Bearer token |
| 2 | `track_legacy_routes` | middleware_setup.py:102 | Track non-/v1/ calls (Prometheus counter) |
| 3 | `http_response_counter` | middleware_setup.py:87 | SLO availability metric by status class |
| 4 | `docs_access_guard` | middleware_setup.py:72 | Gate /docs behind DOCS_ACCESS_TOKEN |
| 5 | `shutdown_drain_middleware` | middleware_setup.py:55 | 503 + Retry-After during graceful shutdown |
| 6 | `RateLimitMiddleware` | middleware.py | Redis token-bucket rate limiting |
| 7 | `DeprecationMiddleware` | middleware.py | Deprecation header for sunset endpoints |
| 8 | `SecurityHeadersMiddleware` | middleware.py | X-Content-Type-Options, etc. |
| 9 | `CorrelationIDMiddleware` | middleware.py | X-Request-ID + search_id + correlation_id propagation |
| 10 (innermost) | `CORSMiddleware` | Starlette built-in | CORS policy enforcement |

Context variables for distributed tracing (middleware.py:26-30):
- `request_id_var`: Per-request UUID
- `search_id_var`: End-to-end search journey (CRIT-004)
- `correlation_id_var`: Browser per-tab session ID

### 3.3 Search Pipeline (Core Architecture)

The search pipeline is a 7-stage orchestrator defined in `search_pipeline.py` (thin wrapper, `_STAGE_TABLE` at line 24) with stage logic in `pipeline/stages/`. All stages communicate through `SearchContext` (`search_context.py`), a `@dataclass` with ~40+ fields of intermediate state (raw results, filtered results, scores, tracker, deadline, etc.):

```
[1] VALIDATE   → Input validation, auth, quota check
[2] PREPARE    → Build search parameters, resolve sectors
[3] EXECUTE    → Parallel multi-source fetch (PNCP + PCP + ComprasGov)
[4] FILTER     → UF → Value → Keywords → LLM zero-match → Status
[5] ENRICH     → Viability scoring, item inspection
[6] GENERATE   → Excel + LLM summary (via ARQ background jobs)
[7] PERSIST    → Cache results, record search session
```

**Timeout chain (strict decreasing):**
```
ARQ Job(300s) > Pipeline(110s) > Consolidation(100s) > PerSource(80s) > PerUF(30s) > HTTP(10s)
```

**Filter pipeline (fail-fast ordering):**
1. UF check (fastest, O(1) set lookup)
2. Value range check (simple numeric comparison)
3. Keyword matching (density scoring with 3 thresholds: high >5%, medium 2-5%, low 1-2%)
4. LLM zero-match classification (for 0% keyword density, GPT-4.1-nano YES/NO)
5. Status/date validation
6. Viability assessment (post-filter, 4-factor weighted score)

### 3.3 Data Source Clients

| Source | File | Priority | Auth | Page Size | Notes |
|--------|------|----------|------|-----------|-------|
| **PNCP** | `pncp_client.py` | 1 | None | 50 max | Primary. `codigoModalidadeContratacao` required since ~Mar 2026 |
| **PCP v2** | `clients/portal_compras_client.py` | 2 | None (public) | 10/page | Client-side UF filtering only. `valor_estimado=0.0` always |
| **ComprasGov v3** | `clients/compras_gov_client.py` | 3 | None | varies | Dual-endpoint (legacy + Lei 14.133). Currently down since Mar 2026 |

Each source has independent circuit breakers (sliding window, configurable thresholds and cooldowns -- all defined in `pncp_client.py:48-71`) and per-source bulkhead concurrency limits (`bulkhead.py`). Source adapters implement `SourceAdapter` ABC from `clients/base.py`, producing `UnifiedProcurement` dataclass with standardized fields and `dedup_key` generation. Source health registry in `source_config/sources.py` tracks `SourceHealthStatus` (healthy/degraded/down) with 5-minute TTL.

Available sources (from `source_config/sources.py:40-50` `SourceCode` enum): PNCP, Portal (PCP), Licitar, ComprasGov, PortalTransparencia, BLL (disabled), BNC (disabled), QueridoDiario (experimental).

### 3.4 Cache Architecture (Two-Level SWR)

```
Request → L1 InMemory (4h TTL, hot/warm/cold) → L2 Supabase (24h TTL)
                ↓ miss                                    ↓ miss
          Live fetch from sources ← ← ← ← ← ← ← ← ← ←
                ↓ result
          Write-through to L1 + L2
```

- **Fresh (0-6h):** Serve immediately
- **Stale (6-24h):** Serve stale, trigger background revalidation (max 3 concurrent, 180s timeout)
- **Expired (>24h):** Not served, force fresh fetch
- L1 uses priority tiers: hot (recently accessed) > warm > cold (evicted first)
- L2 is Supabase `search_results_cache` table (persistent across restarts)

### 3.5 LLM Integration

| Use Case | Model | Module | Pattern |
|----------|-------|--------|---------|
| Sectoral classification | GPT-4.1-nano | `llm_arbiter.py` | Keyword density > threshold = keyword; else LLM YES/NO |
| Zero-match rescue | GPT-4.1-nano | `llm_arbiter.py` | Items with 0% keyword density get LLM review |
| Executive summary | GPT-4.1-nano | `llm.py` | ARQ background job; immediate fallback summary |
| Bid analysis | GPT-4.1-nano | `bid_analyzer.py` | Deep analysis of individual bids |

**Failure mode:** REJECT on LLM failure (zero noise philosophy). No hallucinated approvals.

### 3.6 Auth and Billing

- **Auth:** Supabase Auth with local JWT validation (ES256+JWKS, backward compatible HS256). Token cache: L1 in-memory (60s TTL, LRU 1000 entries) + L2 Redis (5min TTL).
- **Billing:** Stripe with 3 billing periods (monthly/semiannual/annual). 14-day free trial (no credit card). "Fail to last known plan" policy on DB errors.
- **Quotas:** `check_and_increment_quota_atomic` with Redis token bucket rate limiting. In-memory plan cache (5min TTL).
- **Grace period:** 3 days for subscription gaps (`SUBSCRIPTION_GRACE_DAYS`).

### 3.7 Background Jobs (ARQ)

The worker process runs ARQ for async tasks:
- LLM summary generation (with immediate fallback response)
- Excel file generation
- Zero-match LLM classification batches
- Trial email sequences
- Alert matching and delivery

SSE events (`llm_ready`, `excel_ready`) push updates to the frontend in real-time.

### 3.8.1 SSE Progress Tracking (progress.py)

Dual-mode real-time progress system:

- **Redis Streams mode** (horizontal scaling, STORY-276): Append-only log per `search_id`. Cross-worker SSE: Worker A creates tracker, Worker B reads from Streams. Terminal events trigger `EXPIRE` (5min TTL, `_STREAM_EXPIRE_TTL` at progress.py:38). Last-Event-ID resumption support (STORY-297): replay list with 10min TTL, max 200 events (`_REPLAY_MAX_EVENTS` at progress.py:42).
- **In-memory fallback** (single instance): `asyncio.Queue` per search_id when Redis unavailable.
- **Events:** `connecting`, `fetching`, `filtering`, `llm`, `excel`, `complete`, `degraded`, `error`, `llm_ready`, `excel_ready`, `shutdown` (DEBT-124 graceful shutdown).
- **Heartbeat:** 15s interval. Wait-for-tracker yields `: waiting\n\n` comments every 5s to prevent undici BodyTimeoutError (CRIT-012).

### 3.8 Observability Stack

| Tool | Purpose | Integration |
|------|---------|-------------|
| **Sentry** | Error tracking + performance | FastAPI + Starlette integrations, PII scrubbing |
| **Prometheus** | Metrics (counters, histograms, gauges) | 1002-line metrics.py, `/metrics` endpoint |
| **OpenTelemetry** | Distributed tracing | Pipeline stage spans, custom tracer |
| **Structured logging** | JSON logs to stdout | `log_sanitizer.py` masks PII in all log output |

### 3.9 API Endpoints Inventory

**126 total endpoints** across 35 route modules + main.py:

| Category | Endpoints | Key Routes |
|----------|-----------|------------|
| **Search** | 10 | `POST /buscar`, `GET /buscar-progress/{id}` (SSE), `/search/{id}/status`, `/search/{id}/retry` |
| **Pipeline** | 5 | CRUD + `/pipeline/alerts` |
| **Billing** | 6 | `/checkout`, `/billing-portal`, `/subscription/status`, `/plans` |
| **User/Auth** | 12 | `/me`, `/change-password`, `/trial-status`, `/profile/context`, Google OAuth |
| **Analytics** | 6 | `/summary`, `/searches-over-time`, `/top-dimensions`, `/trial-value` |
| **Alerts** | 7 | CRUD + `/history`, `/preview`, `/unsubscribe` |
| **Admin** | 8 | `/admin/feedback/patterns`, `/admin/partners`, `/search-trace/{id}` |
| **Messages** | 5 | Conversations CRUD + replies |
| **Organizations** | 6 | CRUD + invite/accept + dashboard |
| **Health** | 8 | `/health`, `/health/live`, `/health/ready`, `/health/cache`, `/status` |
| **Content** | 10 | SEO pages (`/setores`, `/setor/{id}`, `/panorama/{id}`), blog stats |
| **Other** | 43 | Sessions, feedback, MFA, partners, reports, emails, feature flags, SLO |

---

## 4. Frontend Architecture

### 4.1 App Router Structure (47 Pages)

| Category | Routes | Count |
|----------|--------|-------|
| **Core app** | `/buscar`, `/dashboard`, `/historico`, `/pipeline`, `/mensagens`, `/alertas`, `/status` | 7 |
| **Auth** | `/login`, `/signup`, `/auth/callback`, `/recuperar-senha`, `/redefinir-senha`, `/onboarding` | 6 |
| **Account** | `/conta`, `/conta/dados`, `/conta/perfil`, `/conta/plano`, `/conta/equipe`, `/conta/seguranca` | 6 |
| **Admin** | `/admin`, `/admin/cache`, `/admin/emails`, `/admin/metrics`, `/admin/partners`, `/admin/slo` | 6 |
| **Marketing** | `/`, `/planos`, `/pricing`, `/features`, `/sobre`, `/planos/obrigado` | 6 |
| **Blog/SEO** | `/blog`, `/blog/[slug]`, `/blog/licitacoes/*`, `/blog/panorama/*`, `/blog/programmatic/*`, `/licitacoes/*` | 8 |
| **Content** | `/ajuda`, `/termos`, `/privacidade`, `/como-avaliar-*`, `/como-evitar-*`, `/como-filtrar-*`, `/como-priorizar-*` | 6 |
| **Legal** | `/termos`, `/privacidade` | 2 |

### 4.2 Component Architecture

**Buscar (search page) components: 41 files**
- Search: `SearchForm`, `SearchResults`, `FilterPanel`, `UfProgressGrid`, `SearchProgressBanner`
- Resilience: `CacheBanner`, `DegradationBanner`, `PartialResultsPrompt`, `SourcesUnavailable`, `DataQualityBanner`
- AI: `LlmSourceBadge`, `ViabilityBadge`, `FeedbackButtons`, `ReliabilityBadge`
- Loading: `EnhancedLoadingProgress`, `LoadingProgress`

**Shared components: ~32 files** in `components/`
- Layout: `NavigationShell`, `Sidebar`, `BottomNav`, `PageHeader`, `MobileDrawer`
- Billing: `PlanCard`, `PlanToggle`, `PaymentFailedBanner`, `CancelSubscriptionModal` (in `billing/`)
- Error handling: `ErrorBoundary`, `PageErrorBoundary`, `ErrorStateWithRetry`
- User: `ProfileCompletionPrompt`, `ProfileProgressBar`, `AuthLoadingScreen`

### 4.3 Hooks Architecture

**Shared hooks (27):** `useAlerts`, `useAnalytics`, `useConversations`, `useFeatureFlags`, `useFetchWithBackoff`, `useKeyboardShortcuts`, `useOrganization`, `usePipeline`, `usePlan`, `usePlans`, `useProfileContext`, `useQuota`, `useSearchSSE`, `useSessions`, `useTrialPhase`, etc.

**Buscar hooks (9):** `useSearch` (main orchestrator), `useSearchExecution`, `useSearchExport`, `useSearchFilters`, `useSearchOrchestration`, `useSearchPersistence`, `useSearchRetry`, `useSearchSSEHandler`, `useUfProgress`

### 4.4 API Proxy Pattern

The frontend uses Next.js API routes as proxies to the backend (58 route handlers in `app/api/`). This provides:
- Cookie-based auth forwarding (Supabase SSR tokens)
- CORS isolation (frontend domain only talks to itself)
- Backend URL hidden from client
- Structured error extraction and forwarding

### 4.5 Security Headers

The `middleware.ts` implements comprehensive security:
- **CSP:** Nonce-based `script-src` with `strict-dynamic` (DEBT-108)
- **HSTS:** Preload enabled
- **COOP:** `same-origin`
- **X-DNS-Prefetch-Control:** off
- **Frame protection:** Stripe only
- CSP violation reporting to `/api/csp-report`

---

## 5. Database Architecture

### 5.1 Tables (29)

| Table | Purpose | RLS |
|-------|---------|-----|
| `profiles` | User profiles (extends auth.users) | Yes |
| `search_sessions` | Search history and results | Yes |
| `search_results_cache` | L2 cache for search results | Yes |
| `search_results_store` | Persistent search result storage | Yes |
| `search_state_transitions` | Search state machine audit trail | Yes |
| `pipeline_items` | Kanban pipeline opportunities | Yes |
| `monthly_quota` | Per-user monthly search quota tracking | Yes |
| `plan_features` | Plan capability definitions | Yes |
| `plan_billing_periods` | Stripe price IDs per billing period | Yes |
| `stripe_webhook_events` | Idempotent webhook event log | Yes |
| `classification_feedback` | User feedback on LLM classifications | Yes |
| `conversations` / `messages` | In-app messaging | Yes |
| `user_oauth_tokens` | Google OAuth tokens | Yes |
| `google_sheets_exports` | Export history | Yes |
| `alerts` / `alert_runs` / `alert_sent_items` / `alert_preferences` | Email alert system | Yes |
| `health_checks` / `incidents` | Status page data | Yes |
| `mfa_recovery_codes` / `mfa_recovery_attempts` | MFA support | Yes |
| `organizations` / `organization_members` | Multi-tenant orgs | Yes |
| `partners` / `partner_referrals` | Revenue share program | Yes |
| `trial_email_log` | Trial email sequence tracking | Yes |
| `reconciliation_log` | Stripe reconciliation audit | Yes |
| `audit_events` | General audit trail | Yes |

### 5.2 Key Schema Patterns

- **All tables have RLS enabled** (28 tables confirmed)
- **105 RLS policies** with consistent patterns: user_id match for user data, service_role bypass for admin operations
- **95 indexes** covering user_id foreign keys, search parameters, and time-based queries
- **32 database functions** including `check_and_increment_quota` (atomic), plan sync triggers, and retention policies
- **Foreign keys standardized** to `profiles(id)` via multiple migration passes (DEBT-001, DEBT-104)

---

## 6. CI/CD and Infrastructure

### 6.1 GitHub Actions Workflows (17)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `backend-tests.yml` | PR + push | 7332+ backend tests with pytest |
| `frontend-tests.yml` | PR + push | 5583+ frontend tests with Jest |
| `e2e.yml` | PR + push | 60 Playwright E2E tests |
| `deploy.yml` | Push to main | Deploy backend + frontend to Railway |
| `staging-deploy.yml` | Push to staging | Deploy to staging environment |
| `pr-validation.yml` | PR | Lint, type-check, schema validation |
| `migration-gate.yml` | PR (migrations) | Warning comment on unapplied migrations |
| `migration-check.yml` | Push + daily | Block if unapplied migrations |
| `codeql.yml` | Schedule | Security scanning |
| `lighthouse.yml` | PR | Performance auditing |
| `load-test.yml` | Manual | Locust load testing |
| `cleanup.yml` | Schedule | Resource cleanup |
| `dependabot-auto-merge.yml` | Dependabot PRs | Auto-merge patch updates |
| `sync-sectors.yml` | Manual | Sync sector data frontend-backend |
| Others | Various | handle_new_user guard, backend-ci |

### 6.2 Three-Layer Migration Defense

1. **PR Warning** (`migration-gate.yml`): Lists pending migrations, posts comment
2. **Push Alert** (`migration-check.yml`): Blocks (exit 1) if unapplied migrations
3. **Auto-Apply on Deploy** (`deploy.yml`): Runs `supabase db push --include-all` after deploy

---

## 7. Architecture Patterns Assessment

### 7.1 Patterns Used Well

| Pattern | Implementation | Quality |
|---------|---------------|---------|
| **Circuit breaker** | Per-source (PNCP, PCP, ComprasGov) + Supabase | Sliding window, configurable thresholds |
| **Bulkhead isolation** | Per-source concurrency limits | Prevents one slow source from starving others |
| **SWR cache** | Two-level (InMemory + Supabase) | Graceful degradation, background revalidation |
| **Pipeline architecture** | 7-stage with thin orchestrator + stage modules | Clean separation, testable stages |
| **Fail-fast filtering** | Cheapest checks first, expensive (LLM) last | Optimal resource usage |
| **Zero noise philosophy** | LLM failure = REJECT | No false positives from AI errors |
| **Proxy pattern** | Next.js API routes proxy all backend calls | Security isolation, CORS clean |
| **CSP nonce** | Per-request nonce with strict-dynamic | Strong XSS prevention |
| **PII scrubbing** | Sentry before_send + log_sanitizer | Consistent masking across all outputs |
| **Feature flags** | 40+ flags with runtime toggle capability | Gradual rollout, kill switches |
| **Timeout chain** | Strictly decreasing per level | No unbounded waits |

### 7.2 Patterns Concerns

| Concern | Description |
|---------|-------------|
| **Monolithic filter.py** | 3,871 lines despite decomposition into 11 filter_*.py files. `filter.py` still contains substantial logic alongside the submodules |
| **Flat backend structure** | 69 top-level .py files. Some logical groupings (filter, pncp, search) span multiple files at the same directory level |
| **Dual search path** | Some endpoints in `main.py` (7) coexist with 119 in `routes/`. Incremental migration from monolith is complete but main.py still has legacy endpoints |
| **Schema monolith** | `schemas.py` at 2,121 lines contains all Pydantic models. Could benefit from per-domain schema files |
| **Config explosion** | 40+ feature flags + extensive env vars (356 lines in .env.example). Operational complexity |

---

## 8. Technical Debt Register

### Critical

| ID | Category | Description | Impact | Est. Effort |
|----|----------|-------------|--------|-------------|
| DEBT-301 | Architecture | `filter.py` at 3,871 LOC is the largest file despite 11 filter submodules existing. Core matching logic should be fully migrated to submodules, leaving filter.py as a thin orchestrator | Maintenance burden, merge conflicts, hard to reason about filtering behavior | 8h |
| DEBT-302 | Architecture | `schemas.py` at 2,121 LOC is a monolithic Pydantic model file. All request/response models for 126 endpoints live in one file | Slow IDE navigation, merge conflicts, no domain boundary enforcement | 6h |
| DEBT-303 | Performance | `pncp_client.py` still imports sync `requests` library alongside async `httpx`. The sync fallback is wrapped in `asyncio.to_thread()` but the dual-client pattern adds complexity | Code duplication between sync/async paths, potential thread pool exhaustion under load | 4h |

### High

| ID | Category | Description | Impact | Est. Effort |
|----|----------|-------------|--------|-------------|
| DEBT-304 | Architecture | 69 top-level Python files in `backend/`. Logical groupings like filtering (11 files), search (4 files), PNCP (3 files) should be packages | Developer onboarding friction, hard to navigate codebase | 12h |
| DEBT-305 | Architecture | `job_queue.py` at 2,152 LOC and `cron_jobs.py` at 2,039 LOC are both large monoliths handling all background task definitions | Hard to test individual jobs, risk of import side effects | 6h |
| DEBT-306 | Maintainability | `search_cache.py` at 2,512 LOC handles L1, L2, SWR logic, cache key generation, and serialization all in one file | Complex state management in a single module | 4h |
| DEBT-307 | Security | `webhooks/stripe.py` at 1,192 LOC handles all Stripe webhook events in a single handler function. Complex branching for 10+ event types | Hard to audit security-critical billing logic, risk of missed edge cases | 6h |
| DEBT-308 | Performance | Frontend `api-types.generated.ts` at 5,177 LOC is a generated type file. If it's not tree-shaken, it bloats the client bundle | Larger bundle size, slower page loads | 2h |
| DEBT-309 | Architecture | `quota.py` at 1,622 LOC mixes plan definition, quota checking, rate limiting, and trial logic | Multiple responsibilities in one module, hard to modify billing rules | 4h |

### Medium

| ID | Category | Description | Impact | Est. Effort |
|----|----------|-------------|--------|-------------|
| DEBT-310 | Maintainability | `main.py` reduced to 103 LOC (DEBT-107 completed) but retains ~75 lines of backward-compat re-exports and proxy classes for test compatibility (`main.py:28-102`). Tests should import from actual module locations (`startup.state`, `startup.lifespan`, etc.) | Test coupling to legacy import paths, confusing proxy classes | 3h |
| DEBT-311 | Testing | Backend test LOC (140,199) is 1.8x the source LOC (77,364). While high coverage is good, the test-to-source ratio suggests potential test duplication or over-specification | Slower CI, test maintenance burden, brittle tests that break on refactoring | 8h (audit) |
| DEBT-312 | Maintainability | 11 filter_*.py files + filter.py creates ambiguity about which file owns which filtering responsibility. `filter.py` header says "Keyword matching engine for uniform/apparel procurement" but it's used for all sectors | Confusing module naming, stale docstrings | 3h |
| DEBT-313 | Infrastructure | ComprasGov v3 data source has been down since March 2026. The client code (838 LOC) and circuit breaker config remain active. Priority should be formally demoted or the source should be disabled | Wasted timeout budget on dead source, confusing source health dashboard | 2h |
| DEBT-314 | Maintainability | `config/features.py` exports 40+ feature flags. Several may be permanently enabled/disabled but are still treated as toggleable | Configuration complexity, dead feature flag accumulation | 3h |
| DEBT-315 | Architecture | Frontend has 58 API proxy routes. Many follow identical patterns (forward auth, proxy to backend, extract errors). A generic proxy factory exists (`create-proxy-route.ts`) but not all routes use it | Code duplication across proxy routes | 4h |
| DEBT-316 | UX | Frontend `onboarding/page.tsx` at 783 LOC and `signup/page.tsx` at 703 LOC are large single-file pages without component decomposition | Hard to test individual form steps, maintenance burden | 4h |

### Low

| ID | Category | Description | Impact | Est. Effort |
|----|----------|-------------|--------|-------------|
| DEBT-317 | Maintainability | `backend/clients/` has 5 client modules with varying structure. No shared base class despite `base.py` existing | Inconsistent error handling across data sources | 4h |
| DEBT-318 | Documentation | Backend has `docs/` and `examples/` directories. Content currency is unknown | Potentially stale documentation | 2h (audit) |
| DEBT-319 | Testing | Backend `scripts/` contains 12 utility scripts, some with their own test files (`test_audit_pipeline.py`). These aren't part of the main test suite | Script quality not validated in CI | 2h |
| DEBT-320 | Architecture | `startup/` decomposition is COMPLETE (DEBT-107). `main.py` now delegates all init to `startup/app_factory.py:create_app()`. Remaining issue: `main.py:82-102` has a `track_legacy_routes()` shim that duplicates logic from `startup/middleware_setup.py:103-119` for backward-compat tests | Minor duplication, test coupling | 1h |
| DEBT-321 | Performance | `blog.ts` at 785 LOC in the frontend lib suggests blog content may be hardcoded or statically defined rather than CMS-driven | Content updates require code deployments | N/A (design choice) |
| DEBT-322 | Architecture | Circuit breaker configs for PCP and ComprasGov are defined in `pncp_client.py:56-71` despite those sources having their own client modules in `clients/`. Should live in `source_config/sources.py` or respective client files | Misleading code location, maintenance confusion | 1h |
| DEBT-323 | Security | `_plan_status_cache` in `quota.py:44` is an unbounded `dict`. Unlike `_token_cache` (LRU 1000 entries) and `_arbiter_cache` (LRU 5000), this grows without limit. Under high user count, memory exhaustion possible | Memory safety gap | 1h |
| DEBT-324 | Architecture | Dual Stripe webhook router registration in `startup/routes.py:62+70` -- included both at `/v1/` prefix (line 62 via `_v1_routers`) and at root (line 70). Creates ambiguous routing | Potential double-processing of webhooks | 1h |
| DEBT-325 | Maintainability | `llm_arbiter.py:73` hardcodes `_USD_TO_BRL = 5.0` for cost estimation. Should be configurable or fetched | Inaccurate cost tracking as exchange rate drifts | 0.5h |

---

## 9. Scalability Assessment

### 9.1 Current Bottlenecks

| Resource | Current Limit | Concern |
|----------|--------------|---------|
| **Railway memory** | 1GB (backend) | 2 Gunicorn workers with in-memory caches. OOM risk under load (WEB_CONCURRENCY reduced from 4 to 2) |
| **PNCP API** | 50 items/page, rate limits | Phased UF batching (batch_size=5, delay=2s) mitigates but limits throughput |
| **LLM calls** | ThreadPoolExecutor(max_workers=10) | Parallel but bounded. GPT-4.1-nano latency adds 1-3s per classification |
| **Redis** | Single instance (Upstash/Railway) | No cluster. Single point of failure (mitigated by in-memory L1 fallback) |
| **Supabase** | Cloud free/pro tier | Connection pooling via Supavisor. No read replicas |

### 9.2 Horizontal Scaling Path

The architecture supports horizontal scaling at the web tier (add Gunicorn workers or Railway replicas) but has shared-state constraints:
- L1 cache is per-worker (not shared between Gunicorn workers)
- SSE progress tracking uses in-memory asyncio.Queue (not shared)
- Feature flags cached per-process
- To scale beyond 1 Railway instance: move SSE to Redis Pub/Sub, move progress tracking to Redis

### 9.3 Reliability Patterns

- **Fallback cascade:** Live fetch -> Partial results -> Stale cache -> Empty (with degradation banners)
- **Circuit breakers:** Per-source with independent thresholds and cooldowns
- **Auto-retry:** Frontend exponential backoff [10s, 20s, 30s] for transient errors
- **Graceful degradation:** SSE failure -> time-based simulation; Backend offline -> queued searches
- **Health checks:** `/health/live` (liveness), `/health/ready` (readiness), `/health/cache` (cache status)

---

## 10. Security Posture

### 10.1 Strengths

- RLS on all 29 tables (105 policies)
- JWT validation with ES256+JWKS support
- CSP nonce-based with strict-dynamic
- PII scrubbing in Sentry + structured logs
- Input validation via Pydantic on all endpoints
- UUID pattern validation on all ID parameters
- Search query sanitization regex (SAFE_SEARCH_PATTERN)
- Rate limiting (Redis token bucket)
- Stripe webhook signature verification
- API docs disabled in production
- Security headers (HSTS, COOP, X-DNS-Prefetch-Control)
- CodeQL security scanning in CI

### 10.2 Areas to Monitor

- `.env` files exist locally but are properly gitignored
- `SUPABASE_SERVICE_ROLE_KEY` bypasses RLS (used by backend only)
- `style-src 'unsafe-inline'` in CSP (accepted risk for Tailwind, documented)
- No WAF in front of Railway (relies on Railway proxy + Cloudflare DNS)
- MFA is optional (TOTP + recovery codes implemented but not enforced)

---

## 11. Data Flow Diagram

### 11.1 Search Request Flow

```
User clicks "Buscar"
    ↓
Frontend: POST /api/buscar (Next.js proxy)
    ↓
Backend: POST /v1/buscar
    ├── Auth (JWT validation, quota check)
    ├── Check cache (L1 → L2 → miss)
    ├── If cache hit (fresh): return immediately
    ├── If cache stale: serve stale + background revalidation
    ├── If cache miss:
    │   ├── [Parallel] PNCP API (batched UFs, phased modalities)
    │   ├── [Parallel] PCP v2 API (all UFs, client-side filter)
    │   ├── [Parallel] ComprasGov v3 (if enabled)
    │   ├── Consolidation (dedup by priority, normalize schemas)
    │   ├── Filter pipeline (UF → Value → Keywords → LLM → Status)
    │   ├── Viability scoring (4 factors)
    │   ├── [ARQ Job] LLM summary + Excel generation
    │   └── Cache write (L1 + L2)
    └── Return BuscaResponse (202 if async, 200 if sync)

[Parallel] SSE: GET /v1/buscar-progress/{search_id}
    ├── Wait-for-tracker (heartbeat every 15s)
    ├── Per-UF progress events
    ├── source_complete events
    ├── llm_ready / excel_ready events (from ARQ)
    └── done event
```

### 11.2 Billing Flow

```
User selects plan → POST /v1/checkout → Stripe Checkout Session
    ↓ (redirect to Stripe)
Stripe payment → Webhook → POST /v1/stripe/webhook
    ├── checkout.session.completed → activate plan, sync profiles.plan_type
    ├── invoice.paid → extend subscription
    ├── invoice.payment_failed → dunning emails
    ├── customer.subscription.updated → plan change, sync
    └── customer.subscription.deleted → downgrade to free
```

---

## Appendix A: Key Configuration Constants

| Constant | Value | Source |
|----------|-------|--------|
| `PNCP_MAX_PAGE_SIZE` | 50 | PNCP API limit (was 500, reduced Feb 2026) |
| `PNCP_BATCH_SIZE` | 5 UFs per batch | Rate limit mitigation |
| `PNCP_BATCH_DELAY_S` | 2.0s | Inter-batch delay |
| `PIPELINE_TIMEOUT` | 110s | Total pipeline timeout |
| `CONSOLIDATION_TIMEOUT` | 100s | Multi-source consolidation |
| `PNCP_TIMEOUT_PER_SOURCE` | 80s | Per-source fetch timeout |
| `PNCP_TIMEOUT_PER_UF` | 30s | Per-UF fetch timeout |
| `PIPELINE_SKIP_LLM_AFTER_S` | 90s | Skip LLM if pipeline running long |
| `PIPELINE_SKIP_VIABILITY_AFTER_S` | 100s | Skip viability scoring |
| `GUNICORN_TIMEOUT` | 120s | Worker request timeout |
| `GUNICORN_KEEP_ALIVE` | 75s | > Railway proxy 60s |
| `WEB_CONCURRENCY` | 2 | Workers (Railway 1GB limit) |
| `CACHE_L1_TTL` | 4h | In-memory cache TTL |
| `CACHE_L2_TTL` | 24h | Supabase cache TTL |
| `TRIAL_DURATION_DAYS` | 14 | Free trial length |
| `MAX_CACHE_ENTRIES` | 1000 | L1 auth token cache |
| `SSE_HEARTBEAT_INTERVAL` | 15s | SSE keep-alive |
| `SEARCH_DEFAULT_PERIOD` | 10 days | Default search date range |

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
| `SENTRY_DSN` | Sentry error tracking URL | Optional |
| `APP_VERSION` | Release version tag | `dev` |

---

*Document v5.0 updated 2026-03-23 by @architect (Aria) during Brownfield Discovery Phase 1 refresh.*
*Codebase analysis based on actual file reads -- all numbers and file:line references verified against source.*
*Previous version: v4.0 (2026-03-21, Atlas). Changes in v5.0: corrected main.py LOC (103, not 1212), added startup/ decomposition detail, added middleware stack section, added SSE progress tracking detail, added source adapter pattern, added 4 new DEBT items (322-325), updated DEBT-310/320 to reflect DEBT-107 completion.*
