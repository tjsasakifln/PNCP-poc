# System Architecture — SmartLic

**Date:** 2026-03-31 | **Author:** @architect (Aria) | **Phase:** Brownfield Discovery Phase 1
**Codebase:** branch `main` HEAD | **Version:** 7.0

---

## 1. System Overview

SmartLic is a public procurement intelligence platform (B2G) that automates the discovery, analysis, and qualification of bidding opportunities for companies participating in Brazilian government purchases. Developed by CONFENGE Avaliacoes e Inteligencia Artificial LTDA, the system aggregates data from 4 government sources (PNCP, PCP v2, ComprasGov v3, LicitaJa), applies AI-based sector classification (GPT-4.1-nano), computes viability across 4 factors, and provides a kanban pipeline for opportunity management.

**Stage:** Advanced POC (v0.5) in production, beta with trials, pre-revenue.
**URL:** https://smartlic.tech

### Codebase Numbers

| Metric | Value |
|--------|-------|
| Python files (backend, excl. tests) | ~283 |
| LOC Python (backend, excl. tests) | ~77,576 |
| Backend test files | 369 |
| Frontend source files (TS/TSX, excl. tests) | ~502 |
| Frontend test files | 306 |
| E2E test files (Playwright) | 35 |
| Supabase migrations | 106 |
| Feature flags registered | 30+ |
| API endpoints | 60+ across 37 route modules |
| Frontend pages | 30+ |
| Route files (backend) | 37 modules, ~11,138 LOC total |

---

## 2. Backend Architecture

### 2.1 Core Modules

The backend is a FastAPI 0.129 application running on Python 3.12. The entry point (`backend/main.py`) is intentionally thin (~30 LOC) — it delegates to `startup/app_factory.py:create_app()` which orchestrates initialization.

**Startup Package (`backend/startup/`):**

| Module | Purpose |
|--------|---------|
| `app_factory.py` | FastAPI app construction, Sentry init, OTel init |
| `routes.py` | Router registration — 37 routers at `/v1/` prefix |
| `middleware_setup.py` | CORS, request ID, metrics endpoint, legacy route tracking |
| `lifespan.py` | Startup/shutdown: cache schema validation, session cleanup, signal handling |
| `exception_handlers.py` | Global exception handlers |
| `endpoints.py` | Root endpoints (version, health) |
| `sentry.py` | Sentry SDK initialization |
| `state.py` | Process-level state (startup_time, ready flag) |

**Config Package (`backend/config/`):**

| Module | Purpose |
|--------|---------|
| `base.py` | `str_to_bool()`, `setup_logging()`, `validate_env_vars()` |
| `pncp.py` | PNCP/PCP/ComprasGov source config: timeouts, circuit breakers, batch sizes, pipeline timeouts |
| `features.py` | 30+ feature flags: LLM, trial, viability, inspection, zero-match, pricing |
| `datalake.py` | Ingestion schedule, rate limits, retention config |

**Schemas Package (`backend/schemas/`):**

| Module | Purpose |
|--------|---------|
| `search.py` | `BuscaRequest`, `BuscaResponse`, `DataSourceStatus`, `SearchErrorCode` |
| `pipeline.py` | Pipeline CRUD models |
| `billing.py` | Checkout, subscription status |
| `user.py` | Profile, trial status |
| `common.py` | Shared base models |
| `stats.py` | Filter statistics models |
| `feedback.py` | Feedback submission models |
| `health.py` | Health check response models |
| `messages.py` | Conversation/message models |
| `admin.py` | Admin-specific models |
| `contract.py` | Contract analysis models |
| `export.py` | Export configuration models |

**Core Business Modules:**

| Module | LOC | Purpose |
|--------|-----|---------|
| `consolidation.py` | 1,394 | Multi-source parallel fetch, dedup, `ConsolidationResult` |
| `progress.py` | 888 | SSE progress tracking (Redis Streams + in-memory fallback) |
| `llm_arbiter.py` | ~600 | GPT-4.1-nano classification: uncertain zone + zero-match |
| `llm.py` | ~400 | LLM summary generation, `ResumoLicitacoes` schema |
| `datalake_query.py` | ~200 | Query `pncp_raw_bids` via `search_datalake` RPC |
| `viability.py` | ~300 | 4-factor viability assessment |
| `excel.py` | ~400 | Styled Excel export via openpyxl |
| `pdf_report.py` | ~500 | PDF diagnostic reports via ReportLab |
| `auth.py` | ~400 | JWT validation (ES256+JWKS), token cache L1/L2 |
| `authorization.py` | ~200 | Role checks (`is_admin`, `is_master`) |
| `quota.py` | ~700 | Plan-based quota management, atomic check-increment |
| `rate_limiter.py` | ~200 | Token bucket rate limiting (Redis + fallback) |
| `bulkhead.py` | ~200 | Per-source concurrency isolation (semaphore pattern) |
| `email_service.py` | ~300 | Transactional emails via Resend |
| `sectors.py` | ~200 | Sector definitions loader from `sectors_data.yaml` |
| `feedback_analyzer.py` | ~200 | User feedback pattern analysis, bi-gram scoring |
| `log_sanitizer.py` | ~150 | Token/PII masking in logs |
| `telemetry.py` | ~200 | OpenTelemetry distributed tracing |
| `metrics.py` | ~1,037 | Prometheus metrics (graceful no-op degradation) |
| `health.py` | ~200 | Health check logic (DB, cache, Redis, PNCP canary) |

### 2.2 API Routes (all endpoints)

Registered in `startup/routes.py`. All API routers mount at `/v1/` except health core (root) and Stripe webhook (root).

#### Search Routes

| Method | Route | Module | Purpose |
|--------|-------|--------|---------|
| POST | `/buscar` | `search.py` | Main procurement search |
| GET | `/buscar-progress/{id}` | `search_sse.py` | SSE progress stream |
| GET | `/v1/search/{id}/status` | `search_status.py` | Search status (polling) |
| GET | `/v1/search/{id}/results` | `search_status.py` | Search results |
| POST | `/v1/search/{id}/retry` | `search_status.py` | Retry failed search |
| POST | `/v1/search/{id}/cancel` | `search_status.py` | Cancel active search |
| GET | `/v1/search/{id}/state` | `search_state.py` | Search state machine |

#### Pipeline (Kanban)

| Method | Route | Module | Purpose |
|--------|-------|--------|---------|
| POST | `/pipeline` | `pipeline.py` | Add opportunity to pipeline |
| GET | `/pipeline` | `pipeline.py` | List pipeline items |
| PATCH | `/pipeline/{id}` | `pipeline.py` | Move/update item |
| DELETE | `/pipeline/{id}` | `pipeline.py` | Remove item |
| GET | `/pipeline/alerts` | `alerts.py` | Deadline/update alerts |

#### Billing & Subscriptions

| Method | Route | Module | Purpose |
|--------|-------|--------|---------|
| GET | `/plans` | `plans.py` | List available plans |
| POST | `/checkout` | `billing.py` | Create Stripe Checkout session |
| POST | `/billing-portal` | `billing.py` | Stripe billing portal |
| GET | `/subscription/status` | `subscriptions.py` | Active subscription status |
| POST | `/webhooks/stripe` | `stripe.py` | Stripe webhook handler |

#### User & Auth

| Method | Route | Module | Purpose |
|--------|-------|--------|---------|
| GET | `/me` | `user.py` | Authenticated user profile |
| POST | `/change-password` | `user.py` | Password change |
| GET | `/trial-status` | `user.py` | Trial status (days remaining) |
| PUT | `/profile/context` | `user.py` | Update context (sector, UFs) |
| GET | `/auth/google` | `auth_oauth.py` | Google OAuth initiation |
| GET | `/auth/google/callback` | `auth_oauth.py` | OAuth callback |
| POST | `/auth/email/login` | `auth_email.py` | Email login |
| POST | `/auth/email/signup` | `auth_email.py` | Email signup |
| POST | `/auth/mfa/setup` | `mfa.py` | MFA TOTP setup |
| POST | `/auth/mfa/verify` | `mfa.py` | MFA verification |
| GET | `/auth/check` | `auth_check.py` | Auth token validation |

#### Analytics & Feedback

| Method | Route | Module | Purpose |
|--------|-------|--------|---------|
| GET | `/analytics/summary` | `analytics.py` | Usage summary |
| GET | `/analytics/searches-over-time` | `analytics.py` | Search history chart |
| GET | `/analytics/top-dimensions` | `analytics.py` | Top UFs/sectors |
| GET | `/analytics/trial-value` | `analytics.py` | Trial value calculation |
| POST | `/feedback` | `feedback.py` | Relevance feedback |
| DELETE | `/feedback/{id}` | `feedback.py` | Remove feedback |
| GET | `/admin/feedback/patterns` | `feedback.py` | Pattern analysis |

#### Admin & Monitoring

| Method | Route | Module | Purpose |
|--------|-------|--------|---------|
| GET | `/health` | `health_core.py` | Health check (root, no /v1/) |
| GET | `/health/cache` | `health.py` | Cache status |
| GET | `/metrics` | middleware | Prometheus metrics (token auth) |
| GET | `/admin/search-trace/{id}` | `admin_trace.py` | Search trace (admin) |
| GET | `/admin/feature-flags` | `feature_flags.py` | Feature flags list |
| GET | `/admin/metrics` | `metrics_api.py` | Metrics API |
| GET | `/admin/slo` | `slo.py` | SLO dashboard |

#### Other

| Method | Route | Module | Purpose |
|--------|-------|--------|---------|
| GET | `/sessions` | `sessions.py` | Search history |
| POST | `/conversations` | `messages.py` | Create conversation |
| POST | `/{id}/reply` | `messages.py` | Reply to conversation |
| GET | `/setores` | `sectors_public.py` | Available sectors list |
| POST | `/onboarding/first-analysis` | `onboarding.py` | First trial analysis |
| GET | `/alert-preferences` | `alerts.py` | Alert preferences |
| POST | `/organizations` | `organizations.py` | Organization management |
| GET | `/partners` | `partners.py` | Partner management |
| POST | `/reports` | `reports.py` | Report generation |
| GET | `/blog/stats` | `blog_stats.py` | Blog statistics |
| POST | `/trial/emails` | `trial_emails.py` | Trial email triggers |
| POST | `/bid-analysis` | `bid_analysis.py` | Individual bid analysis |
| GET | `/export/sheets` | `export_sheets.py` | Google Sheets export |

### 2.3 Search Pipeline (multi-source orchestration)

The `SearchPipeline` is the core orchestrator, decomposed into 8 stages in `backend/pipeline/stages/`:

| Stage | Module | LOC | Responsibility |
|-------|--------|-----|----------------|
| 1. VALIDATE | `validate.py` | ~150 | Validate request (UFs, dates, sector), normalize inputs |
| 2. PREPARE | `prepare.py` | ~200 | Load sector config, keywords, prepare context |
| 3. EXECUTE | `execute.py` | ~400 | Fetch data: datalake query or multi-source API fetch |
| 4. FILTER | `filter_stage.py` | ~200 | Apply filters: UF, value, keywords, density scoring |
| 5. ENRICH | `enrich.py` | ~250 | Viability assessment, status inference, urgency |
| 6. POST_FILTER_LLM | `post_filter_llm.py` | ~300 | LLM zero-match classification for 0% density items |
| 7. GENERATE | `generate.py` | ~300 | LLM summary + Excel (inline or ARQ background job) |
| 8. PERSIST | `persist.py` | ~200 | Save results to cache + `search_results_cache` table |

**Supporting modules:**
- `pipeline/worker.py` — ARQ Worker entry point, builds default deps namespace
- `pipeline/cache_manager.py` — Cache key computation, read/write, SWR revalidation triggers
- `pipeline/helpers.py` — Shared utilities
- `pipeline/tracing.py` — OpenTelemetry span helpers

**Search Context (`search_context.py`):**
Mutable state object passed through all stages. Holds: `request`, `licitacoes_raw`, `licitacoes_filtered`, `filter_stats`, `session_id`, `search_id`, `deadline_ts`, `source_results`.

**State Machine (`search_state_manager.py`):**
Tracks search lifecycle transitions: `QUEUED -> RUNNING -> FILTERING -> ENRICHING -> GENERATING -> COMPLETE` (or `ERROR`/`CANCELLED`).

**Timeout Chain (most restrictive to broadest):**
```
Per-UF: 30s -> Per-Source: 80s -> Consolidation: 100s -> Pipeline: 110s -> ARQ Job: 300s
```

**Adaptive behavior:** After 90s elapsed, LLM classification is skipped. After 100s, viability assessment is skipped. This prevents pipeline timeout on slow API days.

### 2.4 Data Ingestion (ETL to pncp_raw_bids)

The `backend/ingestion/` package implements a complete ETL pipeline:

```
ingestion/
  config.py        — Feature flags, schedule, rate limits, retention
  crawler.py       — Orchestrates full/incremental crawls by UF x modalidade
  transformer.py   — Normalizes PNCP API data to pncp_raw_bids schema
  loader.py        — Bulk upsert via RPC (500 rows/batch, content_hash dedup)
  checkpoint.py    — Progress tracking: ingestion_checkpoints + ingestion_runs tables
  scheduler.py     — ARQ cron job registration
  metrics.py       — Prometheus counters for ingestion
```

**Schedule (UTC):**
- Full crawl: 05:00 daily (2am BRT) — 27 UFs x 6 modalidades, 10-day window
- Incremental: 11:00, 17:00, 23:00 (8am, 2pm, 8pm BRT) — 3 days + 1-day overlap
- Purge: 07:00 daily (soft-delete `is_active=false`, 12-day retention)

**Concurrency:** 5 UFs parallel, 2s delay between batches, max 50 pages per (UF, modalidade).

**Tables:**
- `pncp_raw_bids` (~40K+ rows): GIN full-text index (Portuguese config), `content_hash` dedup
- `ingestion_checkpoints`: Per-(UF, modalidade) progress tracking for resumable crawls
- `ingestion_runs`: Audit log of each ingestion run (start, end, status, stats)

### 2.5 Cache Strategy (L1 InMemory + L2 Supabase + L3 File)

Implemented across the `backend/cache/` package (2,379 LOC total):

```
cache/
  core.py        — Re-exports from cache_module.py (backward compat)
  manager.py     — CacheManager orchestrating L1/L2/L3
  memory.py      — InMemoryCache with hot/warm/cold priority tiers
  redis.py       — Redis cache operations
  redis_pool.py  — Shared Redis connection pool
  supabase.py    — Supabase search_results_cache operations
  local_file.py  — Emergency file-based cache fallback
  swr.py         — Stale-While-Revalidate logic
  admin.py       — Admin cache management endpoints
  cascade.py     — Cascade read across L1/L2/L3
  enums.py       — Cache status enums
  _ops.py        — Low-level cache operations
```

**Three-Layer Model:**

| Layer | Storage | TTL | Status | Behavior |
|-------|---------|-----|--------|----------|
| L1 | InMemory/Redis | 4h | Fresh (0-4h) | Serve directly, fastest |
| L2 | Supabase `search_results_cache` | 24h | Stale (4-24h) | Serve + background revalidation |
| L3 | Local file | 24h | Emergency | Serve only if Supabase is down |

**SWR Policy:** Max 3 concurrent revalidations, 180s timeout per revalidation. Stale data served immediately while fresh data is fetched in background.

**Cache Key:** Includes `setor_id`, `ufs`, `date_from`, `date_to`, `modalidades`, additional filter params. Dates added to key (STORY-306) to prevent cross-period pollution.

### 2.6 LLM Integration (GPT-4.1-nano)

Two LLM modules handle classification and summarization:

**`llm_arbiter.py` — Classification:**
- 4-tier density-based classification:
  - >5% density: ACCEPT (source: "keyword")
  - 2-5%: LLM arbiter standard query
  - 1-2%: LLM arbiter conservative query
  - 0%: LLM zero-match YES/NO classification
- Model: GPT-4.1-nano (33% cheaper than gpt-4o-mini)
- Cost: ~R$0.00007/classification (structured output)
- Latency: ~60ms/call, timeout 5s (5x p99)
- Structured output: `{classe, confianca, evidencias, motivo_exclusao}`
- LRU in-memory cache (MD5-based) to avoid duplicate API calls
- Fallback: `PENDING_REVIEW` or hard `REJECT` based on `LLM_FALLBACK_PENDING_ENABLED` flag

**`llm.py` — Summarization:**
- Executive summary generation via GPT-4.1-nano
- `ResumoLicitacoes` Pydantic schema for structured output
- Dispatched as ARQ background job (`llm_summary_job`)
- Immediate fallback summary via `gerar_resumo_fallback()` when queue unavailable

**Item Inspection (`item_inspector.py`):**
- For "gray zone" items (1-5% density), inspects individual bid items via PNCP items API
- Concurrency: 5 simultaneous, 5s timeout per item, 15s phase timeout
- Feature flag: `ITEM_INSPECTION_ENABLED`

### 2.7 Background Jobs (ARQ)

Job processing is split across multiple modules:

**`backend/job_queue.py` (2,229 LOC):**
- ARQ WorkerSettings configuration
- Redis pool management for job queue
- `is_queue_available()` health check
- Inline fallback when ARQ/Redis unavailable

**`backend/jobs/` package:**

| Module | Purpose |
|--------|---------|
| `llm_jobs.py` | LLM summary generation job |
| `excel_jobs.py` | Excel export generation job |
| `search_jobs.py` | Background search execution |
| `zero_match_jobs.py` | Async zero-match classification |
| `cache_jobs.py` | Cache warming/cleanup jobs |
| `notification_jobs.py` | Notification delivery |
| `pool.py` | ThreadPoolExecutor management |
| `result_store.py` | Job result persistence |
| `queue.py` | Queue operations |
| `worker_lifecycle.py` | Worker startup/shutdown hooks |

**`backend/jobs/cron/` sub-package:**

| Module | Purpose |
|--------|---------|
| `scheduler.py` | Cron job registration in ARQ |
| `cache_cleanup.py` | Periodic cache cleanup |
| `canary.py` | PNCP API health canary |
| `session_cleanup.py` | Stale session cleanup |
| `trial_emails.py` | Trial email sequence |

**Web/Worker Separation:** Controlled by `PROCESS_TYPE` environment variable:
- `web`: Gunicorn/Uvicorn serving HTTP requests
- `worker`: ARQ worker consuming background jobs

### 2.8 Auth & Billing (Supabase Auth + Stripe)

**Authentication (`auth.py`):**
- Local JWT validation (ES256+JWKS) — no Supabase API call required
- Token cache: L1 OrderedDict LRU (1000 entries, 60s TTL) + L2 Redis (5min TTL)
- JWKS endpoint fetching with 5-minute cache for key rotation
- Backward compatible: accepts both HS256 and ES256

**Authorization (`authorization.py`):**
- Role-based access: `is_admin`, `is_master`
- Retry logic: retries once (0.3s delay) before failing
- RLS (Row Level Security) on all Supabase tables

**Quota Management (`quota.py`, ~700 LOC):**
- `check_and_increment_quota_atomic()`: Single DB transaction (TOCTOU prevention)
- Plan capabilities loaded from database with 5min in-memory cache
- Circuit breaker integration: fail-open on CB open (allow search, log for reconciliation)
- 3-day grace period for subscription gaps (`SUBSCRIPTION_GRACE_DAYS`)

**Billing (`billing/service.py`, `webhooks/stripe.py`):**
- Stripe subscription management: checkout, portal, webhook handling
- Webhook handlers in `webhooks/handlers/` sub-package
- ALL webhook handlers sync `profiles.plan_type` for reliable fallback
- Pricing: SmartLic Pro R$397/mes, Consultoria R$997/mes (with semester/annual discounts)
- Trial: 14 days free, no credit card required
- Trial paywall: after day 7, limits to 10 results and 5 pipeline items

### 2.9 Monitoring (Prometheus + OTel + Sentry)

**Prometheus Metrics (`metrics.py`, ~1,037 LOC):**
- Graceful degradation: `_NoopMetric` when `prometheus_client` not installed
- Feature flag: `METRICS_ENABLED` + `METRICS_TOKEN` for endpoint auth
- Categories: Search, Cache, LLM, Sources, Bulkhead, Ingestion, Auth, Rate Limit
- Endpoint: `GET /metrics` (scraped on demand)

**OpenTelemetry (`telemetry.py`):**
- Init before FastAPI app creation (in `app_factory.py`)
- Sampling: 10% default (`OTEL_SAMPLING_RATE`)
- Auto-instrumentation: FastAPI + httpx
- Custom spans per pipeline stage
- No-op mode when `OTEL_EXPORTER_OTLP_ENDPOINT` not set

**Sentry (`startup/sentry.py`):**
- `sentry-sdk[fastapi]` integration
- Centralized error reporting via `utils/error_reporting.py`
- Environment-aware sampling

**Structured Logging:**
- Production: JSON format via `python-json-logger`
- Development: Text format with request_id
- `RequestIDFilter` middleware injects UUID in all logs
- `log_sanitizer.py` masks tokens and PII automatically

**Health Checks (`health.py`, `health_core.py`):**
- `GET /health`: DB, cache, Redis, PNCP canary status
- PNCP cron canary: periodic connectivity test
- Recovery epoch tracking (CRIT-056)
- 3 states: `healthy`, `degraded`, `unhealthy`

---

## 3. Frontend Architecture

### 3.1 Pages & Routes

The frontend is a Next.js 16 application with React 18, TypeScript 5.9, and Tailwind CSS 3. Pages are organized in `frontend/app/`:

| Route | Directory | Purpose |
|-------|-----------|---------|
| `/` | `app/page.tsx` | Landing page |
| `/login` | `app/login/` | Authentication |
| `/signup` | `app/signup/` | Registration |
| `/auth/callback` | `app/auth/` | OAuth callback |
| `/recuperar-senha` | `app/recuperar-senha/` | Password recovery |
| `/redefinir-senha` | `app/redefinir-senha/` | Password reset |
| `/onboarding` | `app/onboarding/` | 3-step wizard (CNAE -> UFs -> Confirmation) |
| `/buscar` | `app/buscar/` | **Main search page** — filters, results, SSE progress |
| `/dashboard` | `app/dashboard/` | User dashboard with analytics |
| `/historico` | `app/historico/` | Search history |
| `/pipeline` | `app/pipeline/` | Opportunity pipeline (kanban) |
| `/mensagens` | `app/mensagens/` | Messaging system |
| `/conta` | `app/conta/` | Account settings |
| `/planos` | `app/planos/` | Pricing + thank you page |
| `/pricing` | `app/pricing/` | Marketing pricing page |
| `/features` | `app/features/` | Feature showcase |
| `/ajuda` | `app/ajuda/` | Help center |
| `/admin` | `app/admin/` | Admin dashboard |
| `/alertas` | `app/alertas/` | Alert management |
| `/sobre` | `app/sobre/` | About page |
| `/termos`, `/privacidade` | Legal pages | Terms & privacy |
| `/blog/*` | `app/blog/` | Blog with SEO content pages |
| `/licitacoes` | `app/licitacoes/` | Public procurement listings |
| `/como-*` | `app/como-*/` | SEO content pages (4 topics) |
| `/sitemap.ts` | | Dynamic sitemap generation |

### 3.2 Components

**Search-Specific Components (`app/buscar/components/`, 46 files):**

| Category | Components |
|----------|-----------|
| Search Form | `SearchForm`, `SearchFormHeader`, `SearchFormActions`, `FilterPanel`, `SearchCustomizePanel` |
| Filters | `ModalidadeFilter`, `ValorFilter`, `StatusFilter`, `EsferaFilter` (in `app/components/`) |
| Results | `SearchResults`, `search-results/` sub-directory, `EmptyResults`, `SearchEmptyState` |
| Progress | `EnhancedLoadingProgress`, `ProgressAnimation`, `ProgressBar`, `ProgressSteps`, `UfProgressGrid` |
| Banners | `BannerStack`, `CoverageBar`, `DataQualityBanner`, `ExpiredCacheBanner`, `FilterRelaxedBanner`, `OnboardingBanner`, `PartialResultsPrompt`, `PartialTimeoutBanner`, `RefreshBanner`, `SearchErrorBanner`, `TruncationWarningBanner` |
| AI/Quality | `LlmSourceBadge`, `ZeroMatchBadge`, `ReliabilityBadge`, `FreshnessIndicator`, `FilterStatsBreakdown` |
| Error | `ErrorDetail`, `SearchErrorBoundary`, `SourcesUnavailable`, `UfFailureDetail`, `ZeroResultsSuggestions` |
| State | `SearchStateManager`, `SourceStatusGrid`, `BuscarModals` |
| Export | `GoogleSheetsExportButton` |

**Shared Components (`app/components/`, 51 files):**

| Category | Components |
|----------|-----------|
| Navigation | `AppHeader`, `Footer`, `Sidebar`, `Breadcrumbs`, `BottomNav` |
| Auth | `AuthProvider`, `SessionExpiredBanner` |
| Billing | `PlanBadge`, `QuotaBadge`, `QuotaCounter`, `TrialConversionScreen`, `TrialCountdown`, `TrialExpiringBanner`, `UpgradeModal` |
| Data Display | `LicitacaoCard`, `LicitacoesPreview`, `ComparisonTable`, `StatusBadge` |
| Pipeline | `AddToPipelineButton`, `PipelineAlerts`, `AlertNotificationBell` |
| Infrastructure | `BackendStatusIndicator`, `LoadingProgress`, `LoadingResultsSkeleton`, `ThemeProvider`, `ThemeToggle` |
| Analytics | `AnalyticsProvider`, `GoogleAnalytics`, `ClarityAnalytics` |
| UX | `ContextualTutorialTooltip`, `CookieConsentBanner`, `Dialog`, `CustomSelect`, `CustomDateInput`, `Countdown` |
| Layout | `ContentPageLayout`, `BlogArticleLayout`, `InstitutionalSidebar` |
| SEO | `StructuredData`, `ValuePropSection` |

**Top-Level Components (`frontend/components/`, 30+ files):**

| Category | Components |
|----------|-----------|
| Account | `components/account/` |
| Auth | `components/auth/` |
| Billing | `components/billing/PaymentFailedBanner`, `CancelSubscriptionModal` |
| Blog | `components/blog/` |
| Layout | `NavigationShell`, `MobileDrawer`, `Sidebar`, `PageHeader` |
| Feedback | `FeedbackButtons`, `DeepAnalysisModal` |
| Error | `ErrorBoundary`, `PageErrorBoundary`, `ErrorStateWithRetry` |
| Profile | `ProfileCompletionPrompt`, `ProfileProgressBar`, `ProfileCongratulations` |
| Reports | `components/reports/` |
| Onboarding | `OnboardingTourButton` |
| Org | `components/org/` |
| Data Fetching | `SWRProvider` |

### 3.3 Hooks & State Management

**Custom Hooks:**
- `app/hooks/useInView.ts` — Intersection observer hook

**State Management Pattern:** The frontend uses a combination of:
1. **React Context** (`frontend/contexts/UserContext.tsx`) — User session, profile data
2. **SWR** (`SWRProvider`) — Server state with stale-while-revalidate
3. **localStorage** — Plan cache (1hr TTL), saved searches, last search cache
4. **URL state** — Search parameters in query string

**Key Libraries (`frontend/lib/`):**

| Module | Purpose |
|--------|---------|
| `config.ts` | App name, URLs, feature flags |
| `constants/` | Application constants |
| `error-messages.ts` | Error code mappings, `isTransientError()`, `getMessageFromErrorCode()` |
| `feature-gates.ts` | Feature flag evaluation |
| `fetcher.ts` | SWR fetcher with auth |
| `fetchWithAuth.ts` | Authenticated fetch wrapper |
| `format-currency.ts` | BRL currency formatting |
| `plans.ts` | Plan definitions and capabilities |
| `proxy-error-handler.ts` | API proxy error handling |
| `rate-limiter.ts` | Client-side rate limiting |
| `savedSearches.ts` | Saved search persistence |
| `lastSearchCache.ts` | Most recent search cache |
| `schemas/` | Zod validation schemas |
| `create-proxy-route.ts` | API proxy route factory |
| `programmatic.ts` | Programmatic navigation helpers |
| `copy/` | UI copy/text constants |
| `data/` | Static data |
| `icons/` | Icon components |
| `animations/` | Animation definitions |

### 3.4 API Proxy Pattern

The frontend uses Next.js API routes as proxies to the backend, implemented in `frontend/app/api/`. There are **40+ proxy routes**:

```
app/api/
  buscar/route.ts              — POST /buscar proxy
  buscar-progress/route.ts     — SSE proxy (bodyTimeout: 0, AbortController)
  buscar-results/route.ts      — GET results proxy
  analytics/route.ts           — Analytics proxy (multi-endpoint)
  pipeline/route.ts            — Pipeline CRUD proxy
  admin/route.ts               — Admin endpoints proxy
  feedback/route.ts            — Feedback proxy
  plans/route.ts               — Plans proxy
  billing-portal/route.ts      — Billing portal proxy
  subscription-status/route.ts — Subscription status proxy
  trial-status/route.ts        — Trial status proxy
  me/route.ts                  — User profile proxy
  sessions/route.ts            — Search history proxy
  health/route.ts              — Health check proxy
  setores/route.ts             — Sectors list proxy
  messages/route.ts            — Messaging proxy
  ... (25+ more)
```

**Proxy Pattern (`create-proxy-route.ts`):**
- All proxies forward Supabase auth token from cookies
- Add `X-Request-ID` header for correlation
- Handle timeouts with `AbortController`
- SSE proxy uses `undici.Agent({ bodyTimeout: 0 })` to prevent premature timeout
- Structured error responses with `error_code`, `correlation_id`

---

## 4. Infrastructure

### 4.1 Railway (deployment)

**Backend Service (`backend/railway.toml`):**
- Builder: Dockerfile (Python 3.12 slim)
- Start command: `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-keep-alive 75`
- Health check: `/health` with 300s timeout for cold starts
- Restart: ON_FAILURE, max 10 retries
- Zero-downtime deploys: 45s overlap, 120s drain
- **CRITICAL:** Single-process mode only (no `--workers` flag) — SIGSEGV with forked workers due to C extensions (cryptography, chardet, hiredis)
- **CRITICAL:** `WEB_CONCURRENCY` env var must NOT be set

**Backend Dockerfile:**
- Base: `python:3.12-slim`
- jemalloc installed but DISABLED (SIGSEGV with cryptography >= 46 OpenSSL bindings)
- Post-install cleanup: removes `grpcio`, `grpcio-status`, `httptools`, `uvloop` (all fork-unsafe)
- Cache bust via `LABEL build.timestamp` + `ARG CACHEBUST`

**Worker Service (`backend/railway-worker.toml`):**
- Same Dockerfile, different `PROCESS_TYPE=worker`
- Start command: `arq job_queue.WorkerSettings`

**Frontend Service (`frontend/Dockerfile`):**
- Multi-stage build: deps -> builder -> runner
- Base: `node:20.11-alpine3.19`
- Next.js standalone output mode
- Build-time env vars for Sentry/Mixpanel/Stripe via `ARG`

**Deployment Rules:**
- Prefer GitHub auto-deploy over `railway up`
- Never run `railway up` from inside `backend/` or `frontend/` — always from project root
- Watch patterns trigger deploys only when relevant files change
- `railway up` may fail with 413 Payload Too Large if repo > 300MB — use `.railwayignore`

### 4.2 CI/CD (GitHub Actions)

20 workflow files in `.github/workflows/`:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `deploy.yml` | Push to main (paths: backend/*, frontend/*) | Production deploy to Railway + migration auto-apply |
| `backend-tests.yml` | PR/push | Backend test suite |
| `frontend-tests.yml` | PR/push | Frontend test suite |
| `e2e.yml` | PR/push | Playwright E2E tests |
| `migration-gate.yml` | PR touching supabase/migrations/ | Warning comment on pending migrations |
| `migration-check.yml` | Push to main + daily schedule | Block if unapplied migrations |
| `migration-validate.yml` | PR | Validate migration SQL |
| `pr-validation.yml` | PR | PR title, branch naming, size checks |
| `backend-ci.yml` | PR | Lint, type check, security scan |
| `codeql.yml` | Schedule | CodeQL security analysis |
| `lighthouse.yml` | PR/schedule | Lighthouse performance audit |
| `load-test.yml` | Manual | Locust load testing |
| `staging-deploy.yml` | Manual/branch | Staging environment deploy |
| `sync-sectors.yml` | Manual | Sync frontend sector fallback |
| `cleanup.yml` | Schedule | Cleanup old artifacts |
| `dependabot-auto-merge.yml` | Dependabot PR | Auto-merge minor/patch updates |
| `ingest-licitaja.yml` | Manual | LicitaJa ingestion trigger |
| `handle-new-user-guard.yml` | Webhook | New user onboarding guard |
| `tests.yml` | PR | Combined test orchestration |

**Migration CI Flow (3-layer defense):**
1. **PR Warning** (`migration-gate.yml`) — Lists pending migrations, posts WARNING comment
2. **Push Alert** (`migration-check.yml`) — Blocks (`exit 1`) if unapplied migrations
3. **Auto-Apply** (`deploy.yml`) — After backend deploy, runs `supabase db push --include-all`, sends `NOTIFY pgrst, 'reload schema'`

### 4.3 Database (Supabase PostgreSQL)

**106 migrations** in `supabase/migrations/`, covering:

- Core tables: `profiles`, `search_sessions`, `search_results_cache`, `pipeline_items`
- Ingestion: `pncp_raw_bids`, `ingestion_checkpoints`, `ingestion_runs`
- Billing: `plan_billing_periods`, `subscription_events`
- Feedback: `search_feedback`, `bid_feedback`
- Messaging: `conversations`, `messages`
- Organizations: `organizations`, `org_members`
- Analytics: `search_analytics`, `user_analytics`
- Feature flags: `feature_flags`
- Monitoring: `bloat_monitoring`, `checkpoint_orphan_monitoring`

**RLS (Row Level Security):** Active on ALL tables. Users can only access their own data.

**RPC Functions:**
- `search_datalake` — Full-text search on `pncp_raw_bids`
- `upsert_pncp_raw_bids` — Batch upsert with `content_hash` dedup
- `check_and_increment_quota_atomic` — Atomic quota management
- `get_table_columns_simple` — Schema validation helper

**Indexes:**
- GIN full-text index on `pncp_raw_bids.tsv` (Portuguese configuration)
- Pre-computed `tsvector` column (DEBT-210) for faster searches
- B-tree indexes on foreign keys, date ranges, UF codes

---

## 5. Data Architecture

### 5.1 Three-Layer Model

```
+---------------------------------------------------------------+
|                  LAYER 1: INGESTION (ETL)                      |
|                                                                |
|  ARQ Cron Jobs --> PNCP API --> Transformer --> Loader          |
|  (full daily 2am BRT, incremental 3x/day)                     |
|                        |                                       |
|             pncp_raw_bids (~40K+ rows)                         |
|      GIN full-text index (Portuguese), 12-day retention        |
+---------------------------------------------------------------+
                         |
+---------------------------------------------------------------+
|                LAYER 2: SEARCH PIPELINE                        |
|                                                                |
|  POST /buscar --> SearchPipeline.run() --> 8 stages            |
|  VALIDATE -> PREPARE -> EXECUTE -> FILTER -> ENRICH ->         |
|  POST_FILTER_LLM -> GENERATE -> PERSIST                       |
|                                                                |
|  Execute: query_datalake() (tsquery PostgreSQL)                |
|  Fallback: live API fetch when datalake returns 0              |
+---------------------------------------------------------------+
                         |
+---------------------------------------------------------------+
|                  LAYER 3: CACHE (SWR)                          |
|                                                                |
|  L1: InMemory/Redis (4h TTL, hot/warm/cold priority)           |
|  L2: Supabase search_results_cache (24h TTL, persistent)       |
|  L3: Local File (24h TTL, emergency fallback)                  |
|                                                                |
|  SWR: serve stale + revalidate in background                   |
|  (max 3 concurrent, 180s timeout)                              |
+---------------------------------------------------------------+
```

### 5.2 Search Flow Diagram

```
User (Frontend)
    |
    +-- POST /buscar ----------------------------+
    |                                            v
    |   +---------- SearchPipeline ---------------------------+
    |   | 1. VALIDATE: UFs, dates, sector, rate limit         |
    |   | 2. PREPARE: sector keywords, config                 |
    |   | 3. EXECUTE:                                         |
    |   |    +-- Cache hit? -> serve + SWR background          |
    |   |    +-- DATALAKE_QUERY? -> query_datalake() (SQL)    |
    |   |    +-- Fallback -> multi-source API fetch           |
    |   |        +-- PNCP (priority 1, circuit breaker)       |
    |   |        +-- PCP v2 (priority 2, no auth)             |
    |   |        +-- ComprasGov (priority 3, dual-endpoint)   |
    |   |        +-- LicitaJa (priority 4, disabled default)  |
    |   | 4. FILTER: UF -> value -> keywords -> density       |
    |   | 5. ENRICH: viability, status, urgency               |
    |   | 6. POST_FILTER_LLM: zero-match classification       |
    |   | 7. GENERATE: LLM summary + Excel (or ARQ job)       |
    |   | 8. PERSIST: cache + DB                              |
    |   +-----------------------------------------------------+
    |                    |
    |                    v
    |              BuscaResponse (JSON)
    |
    +-- GET /buscar-progress/{id} (SSE) --> ProgressEvents
```

### 5.3 Ingestion Flow

```
ARQ Cron Scheduler
    |
    +-- 05:00 UTC (daily) --> ingestion_full_crawl_job
    |   |
    |   v
    |   crawl_full()
    |   +-- For each UF (5 parallel):
    |   |   +-- For each modalidade (6):
    |   |       +-- crawl_uf_modalidade()
    |   |           +-- AsyncPNCPClient._fetch_page_async() (up to 50 pages)
    |   |           +-- transform_batch() -> normalize to pncp_raw_bids schema
    |   |           +-- bulk_upsert() -> RPC upsert_pncp_raw_bids (500 rows/batch)
    |   +-- save_checkpoint() + complete_ingestion_run()
    |
    +-- 11/17/23 UTC --> ingestion_incremental_job
    |   +-- crawl_incremental() (same logic, 3 days + overlap)
    |
    +-- 07:00 UTC --> ingestion_purge_job
        +-- purge_old_bids() (soft-delete >12 days)
```

### 5.4 LLM Classification Flow

```
List of bids (post-fetch)
    |
    v
filter/pipeline.py: aplicar_todos_filtros()
    |
    +-- UF check (fail-fast)
    +-- Value range check
    +-- Keyword matching + density scoring
    |   |
    |   +-- density > 5% -> ACCEPT (source: "keyword")
    |   +-- density 2-5% -> LLM arbiter standard
    |   +-- density 1-2% -> LLM arbiter conservative
    |   +-- density 0% -> LLM zero-match (if enabled)
    |       |
    |       v
    |   llm_arbiter.py: classify_bid()
    |   +-- Check MD5 cache (in-memory LRU)
    |   +-- GPT-4.1-nano API call (5s timeout)
    |   |   +-- Structured output: {classe, confianca, evidencias, motivo_exclusao}
    |   +-- Success: SIM/NAO with confidence score
    |   +-- Failure: PENDING_REVIEW or REJECT (config)
    |
    +-- Status/date validation
    +-- Viability assessment (4 factors, post-filter)
```

---

## 6. Technical Debts Identified

### 6.1 Critical

| ID | Description | Impact | File(s) |
|----|-------------|--------|---------|
| DEBT-301 | `filter/pipeline.py` at 1,883 LOC + `filter/keywords.py` at 1,170 LOC — filter package totals 6,422 LOC | Difficult to maintain, test in isolation, and debug. Core filtering logic is the most complex business logic. | `backend/filter/` |
| CRIT-SIGSEGV | C extension restrictions due to intermittent SIGSEGV in production | Prevents uvloop usage, limits cryptography upgrades, requires manual fork-safety testing. Forces single-process mode (no horizontal scaling per instance). | `requirements.txt`, `Dockerfile`, `railway.toml` |

### 6.2 High

| ID | Description | Impact | File(s) |
|----|-------------|--------|---------|
| DEBT-115 | Cache package at 2,379 LOC across 14 files — complex multi-level logic | Cache key migration (STORY-306) added dual-read complexity. SWR logic interleaved with persistence. | `backend/cache/` |
| DEBT-015 | `pncp_client.py` (66 LOC re-export) + `clients/pncp/` (7 files) — sync + async coexistence | Legacy sync client still present alongside async. Circuit breaker and retry logic duplicated. | `backend/pncp_client.py`, `backend/clients/pncp/` |
| -- | `cron_jobs.py` at 2,251 LOC — multiple responsibilities | Cache cleanup, PNCP canary, session cleanup, cache warming, trial emails — all in one file | `backend/cron_jobs.py` |
| -- | `job_queue.py` at 2,229 LOC — pool management + worker settings + jobs | Mixes ARQ configuration, Redis pool management, and job definitions | `backend/job_queue.py` |
| -- | `consolidation.py` at 1,394 LOC — growing complexity | Multi-source orchestration with dedup, partial results, degradation tracking in single file | `backend/consolidation.py` |

### 6.3 Medium

| ID | Description | Impact | File(s) |
|----|-------------|--------|---------|
| -- | Duplication between root filter_*.py and filter/ package | Legacy root files (`filter_keywords.py`, etc.) coexist with `filter/` package. Imports via `filter/__init__.py` | Backend root |
| DEBT-103 | LLM timeout configuration spread across modules | OpenAI timeout in `llm_arbiter.py` + config in `config/features.py`. Not always consistent. | `llm_arbiter.py`, `config/features.py` |
| -- | 106 Supabase migrations | High volume suggests rapidly evolving schema. May impact deploy time. Consider squashing. | `supabase/migrations/` |
| -- | Feature flag sprawl: 30+ flags without governance | Flags accumulated over time. No deprecation/cleanup process. | `config/features.py` |
| -- | `schemas/` directory with 14 files + `schemas_stats.py` + `schema_contract.py` at root | Schemas scattered between directory and root | Backend root |
| -- | 40+ API proxy routes in frontend | Each proxy is a separate file. Pattern is consistent but volume creates maintenance burden. | `frontend/app/api/` |
| -- | Route files total 11,138 LOC across 37 modules | Some route files are large: `search.py` (784 LOC), `user.py` (698 LOC), `pipeline.py` (491 LOC), `analytics.py` (468 LOC) | `backend/routes/` |

### 6.4 Low

| ID | Description | Impact | File(s) |
|----|-------------|--------|---------|
| -- | Backward-compat shims in `main.py` | Re-exports for legacy tests. Functional but adds indirection. Already documented as removed (DEBT-SYS-012). | `backend/main.py` |
| -- | Experimental clients without active usage | `portal_transparencia_client.py`, `querido_diario_client.py`, `qd_extraction.py`, `licitaja_client.py` (disabled by default) | `backend/clients/` |
| -- | `sanctions.py` in clients/ | Sanctions checking client, unclear integration status | `backend/clients/sanctions.py` |
| -- | Dual-hash transition in `auth.py` | 1h window for cache key compatibility. Can be removed after stabilization. | `backend/auth.py` |
| -- | `search_cache.py` at root is now 118 LOC re-export | May confuse developers expecting the full implementation here | `backend/search_cache.py` |

---

## 7. Architectural Concerns

### 7.1 Single-Process Constraint

The SIGSEGV issue with C extensions (cryptography, chardet, hiredis) forces single-process mode on Railway. This means:
- No horizontal scaling within a single container
- All in-memory state (SSE queues, L1 cache, progress tracker) works only because there is one process
- If load increases, the only option is vertical scaling or multiple Railway services with Redis-based coordination

### 7.2 Feature Flag Governance

With 30+ feature flags and no lifecycle management:
- Flags from early stories (STORY-165, STORY-179) still present
- No expiration dates or cleanup process
- Configuration complexity grows with each feature
- Testing matrix expands combinatorially

### 7.3 Monorepo Without Workspace Tooling

Backend (Python) and Frontend (Node.js) share a repository but lack workspace-level tooling:
- No monorepo manager (nx, turborepo, lerna)
- Separate CI workflows that could share caching
- Deploy logic duplicated across services

### 7.4 Database Migration Volume

106 migrations with no squashing strategy. Each deploy must process the full migration chain. While Supabase handles this efficiently, the volume indicates rapid schema evolution that may benefit from periodic consolidation.

### 7.5 Cache Complexity

The 3-level cache with SWR, dual-read for migration, and hot/warm/cold tiering creates significant cognitive overhead. The 14-file `cache/` package plus `search_cache.py` and `cache_module.py` at root need consolidation.

### 7.6 SSE Reliability

Redis Streams solved the fire-and-forget problem of Pub/Sub, but the SSE chain remains fragile:
- `bodyTimeout(0)` in the frontend proxy disables all timeout protection
- Railway's ~120s idle timeout can kill SSE connections during slow searches
- Heartbeat (15s) must stay below Railway's idle threshold
- Last-Event-ID resumption (STORY-297) adds complexity for edge cases

### 7.7 LLM Cost at Scale

Current cost (~R$0.00007/classification) is minimal at POC scale, but:
- A single search can classify 200+ items (MAX_ZERO_MATCH_ITEMS)
- With 1000 searches/month per user and multiple users, costs will grow
- No LLM cost monitoring or budget alerts in place
- ThreadPoolExecutor(max_workers=10) could create burst costs

---

## 8. Dependencies & External Services

### 8.1 Runtime Dependencies

| Service | Criticality | Fallback |
|---------|------------|----------|
| Supabase (PostgreSQL) | CRITICAL | None — DB is single source of truth |
| Redis (Upstash/Railway) | HIGH | InMemoryCache fallback for cache; inline execution for jobs |
| OpenAI API (GPT-4.1-nano) | MEDIUM | `PENDING_REVIEW` or `REJECT` fallback; `gerar_resumo_fallback()` for summaries |
| PNCP API | MEDIUM | Datalake local query (if populated); degraded mode with partial results |
| PCP v2 API | LOW | Skipped if unavailable; PNCP is primary |
| ComprasGov v3 API | LOW | Skipped if unavailable; historically unreliable |
| Stripe | MEDIUM | 3-day grace period; fail-to-last-known-plan |
| Resend | LOW | Email failures are non-blocking |

### 8.2 Build Dependencies

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12 | Backend runtime |
| Node.js | 20.11 | Frontend build + runtime |
| Docker | Multi-stage | Container builds for Railway |
| GitHub Actions | v4 | CI/CD orchestration |
| Railway CLI | Latest | Deploy management |
| Supabase CLI | Latest | Migration management |

### 8.3 Key Python Packages

| Package | Version | Risk Notes |
|---------|---------|-----------|
| cryptography | >=46.0.5,<47.0 | PINNED — fork-safety with Gunicorn. Upgrading may reintroduce SIGSEGV. |
| uvicorn | 0.41.0 (no extras) | WITHOUT `[standard]` — uvloop/httptools removed for fork-safety |
| pydantic | 2.12.5 | v2 migration complete; all schemas use v2 syntax |
| httpx | 0.28.1 | Primary HTTP client for all external API calls |
| openai | 1.109.1 | GPT-4.1-nano — model availability depends on OpenAI |
| supabase | 2.28.0 | Python client for Supabase; relies on PostgREST |
| redis | 5.3.1 | Async Redis client; `ssl=True` works with `rediss://` URLs |
| arq | >=0.26 | No runtime reconnection (issue #386); restart wrapper is community standard |

### 8.4 Data Source Constraints

| Source | Constraint | Workaround |
|--------|-----------|------------|
| PNCP | Max `tamanhoPagina=50` (>50 -> HTTP 400 silent) | Pagination with 50 items/page |
| PNCP | Rate limiting with phased UF batching | 5 UFs parallel, 2s delay between batches |
| PCP v2 | No server-side UF filter | Client-side UF filtering after fetch |
| PCP v2 | `valor_estimado=0.0` always | No value data from this source |
| ComprasGov v3 | Historically unreliable (was completely down 2026-03-03) | Priority 3, disabled by default |
| LicitaJa | Experimental integration | Feature flag `LICITAJA_ENABLED` (default false) |

---

## 9. Architectural Strengths

### 9.1 Exemplary Resilience

The system demonstrates significant maturity in resilience patterns:
- **Circuit breakers** on all external sources with configurable cooldown
- **Bulkhead pattern** isolates data sources with independent semaphores
- **Graceful degradation** at all levels: cache fallback, LLM fallback, source fallback
- **Fail-open policy** for billing (CB open allows search with logging for reconciliation)
- **Multi-level cache** with SWR prevents transient failures from impacting users

### 9.2 Well-Structured Pipeline

- 8 clearly separated stages with single responsibility
- State machine for lifecycle tracking
- SSE real-time progress with Redis Streams (at-least-once delivery)
- Hierarchical timeout chain preventing cascading failures
- Adaptive behavior (skip LLM/viability under time pressure)

### 9.3 Complete Observability

- Full stack: Prometheus + OpenTelemetry + Sentry + structured logging
- Request ID propagated across all logs
- Granular metrics per source, per stage, per LLM operation
- Health checks with proactive PNCP canary
- SLO dashboard (`/admin/slo`)

### 9.4 Datalake Strategy

- Periodic ingestion decouples search from unstable external APIs
- PostgreSQL full-text search with GIN index eliminates API dependency for common searches
- Checkpoint tracking enables resumable crawls
- Transparent fallback to live API when datalake is empty

### 9.5 Robust Security

- Local JWT validation (no API call) with ES256+JWKS support
- RLS on all tables
- Atomic quota operations (TOCTOU prevention)
- Multi-layer rate limiting (Redis + in-memory fallback)
- Automatic log sanitization
- Stripe webhook signature verification
- MFA support with TOTP

### 9.6 Solid Test Coverage

- 369 backend test files, 306 frontend test files, 35 E2E test files
- Zero-failure policy strictly enforced
- Anti-hang rules with pytest-timeout on all tests
- Subprocess isolation for full-suite runs on Windows (`run_tests_safe.py`)
- Comprehensive mock patterns documented in CLAUDE.md

---

## 10. Recommendations

### 10.1 Priority: High

1. **Decompose filter package (6,422 LOC total):** `filter/pipeline.py` (1,883 LOC) and `filter/keywords.py` (1,170 LOC) are the largest files. Target: no module above 500 LOC. Extract keyword matching, density calculation, and batch processing into dedicated modules.

2. **Decompose `cron_jobs.py` (2,251 LOC) and `job_queue.py` (2,229 LOC):** The `jobs/cron/` sub-package already exists with partial extraction. Complete the migration by moving all cron logic into the sub-package and splitting `job_queue.py` into configuration, pool management, and job definitions.

3. **Address single-process scaling constraint:** Evaluate whether Redis-based session affinity and cache coordination would allow multi-process mode. Alternatively, document the scaling path (multiple Railway replicas with Redis coordination) and prepare the architecture.

### 10.2 Priority: Medium

4. **Feature flag governance:** Implement lifecycle (create -> active -> deprecated -> removed) with expiration dates. 30+ flags without cleanup creates "flag debt".

5. **Consolidate root-level legacy files:** Remove or convert root `filter_keywords.py`, `filter_llm.py`, `search_cache.py` (118 LOC re-export), `cache_module.py` into proper package re-exports. Reduce confusion about canonical import paths.

6. **Migration squashing:** Consider squashing the 106 migrations into periodic snapshots (e.g., quarterly). Keep full history in an archive branch.

7. **API proxy consolidation:** The 40+ frontend proxy routes follow a consistent pattern. Evaluate whether `create-proxy-route.ts` factory can reduce boilerplate further or whether a single catch-all proxy is appropriate.

### 10.3 Priority: Low

8. **Audit experimental clients:** Evaluate whether `portal_transparencia_client.py`, `querido_diario_client.py`, `licitaja_client.py`, and `sanctions.py` should remain in the main codebase or move to a feature branch.

9. **LLM cost monitoring:** Add Prometheus counters for LLM API costs (per classification, per summary) and configure alerts for unexpected spending.

10. **Monorepo tooling:** Consider lightweight monorepo tooling (e.g., `just`, `make`, or `nx`) to unify build/test/deploy commands across backend and frontend.
