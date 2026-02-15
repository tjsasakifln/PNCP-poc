# System Architecture - SmartLic/BidIQ

**Version:** 2.0
**Date:** 2026-02-15
**Author:** @architect (Helix) - Brownfield Discovery Phase 1
**Status:** Comprehensive analysis of production codebase on `main` branch (commit `b80e64a`)
**Previous version:** Archived to `system-architecture.md.backup`

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Tech Stack Overview](#2-tech-stack-overview)
3. [Backend Architecture](#3-backend-architecture)
4. [Frontend Architecture](#4-frontend-architecture)
5. [Database Architecture](#5-database-architecture)
6. [External Integrations](#6-external-integrations)
7. [Infrastructure & Deployment](#7-infrastructure--deployment)
8. [Security Architecture](#8-security-architecture)
9. [Code Quality & Testing](#9-code-quality--testing)
10. [Performance Architecture](#10-performance-architecture)
11. [Technical Debt Registry](#11-technical-debt-registry)
12. [Appendix: File Inventory](#appendix-file-inventory)

---

## 1. Executive Summary

SmartLic (formerly BidIQ Uniformes) is a SaaS platform for automated procurement opportunity discovery from Brazil's PNCP (Portal Nacional de Contratacoes Publicas). The system is a two-tier web application with a Python FastAPI backend and a Next.js TypeScript frontend, deployed on Railway with Supabase as the database/auth layer.

### Key Characteristics

| Attribute | Value |
|---|---|
| **Architecture style** | Monolithic API + SPA with BFF (Backend-for-Frontend) proxy layer |
| **Primary data source** | PNCP public API (government procurement portal) |
| **Secondary sources** | ComprasGov, Portal Transparencia, Querido Diario, BLL, BNC, Licitar Digital (adapters exist, varying maturity) |
| **Revenue model** | Tiered subscription (free trial + 3 paid tiers) via Stripe |
| **AI integration** | GPT-4.1-nano (executive summaries), GPT-4o-mini (LLM Arbiter for contract classification) |
| **Scale** | Single-instance deployment (Railway), Redis optional for distributed state |
| **Maturity** | POC v0.3 with production users; 26 DB migrations, 100+ backend test files |
| **App version** | `0.2.0` (defined in `backend/main.py` line 78) |

### Architecture Risk Rating: MEDIUM

The system is functioning in production but carries measurable technical debt from rapid feature accretion. Primary risks:
- In-memory state (`_active_trackers` in `progress.py`, `_token_cache` in `auth.py`) complicates horizontal scaling
- Route decomposition (STORY-202) successfully extracted routes from main.py, but the search pipeline (`search_pipeline.py`) is now the new "god module"
- Dual HTTP client usage (synchronous `requests` in `PNCPClient`, async `httpx` in `AsyncPNCPClient`) creates maintenance burden
- 26 database migrations with some deprecation markers suggest schema churn

---

## 2. Tech Stack Overview

### 2.1 Backend

| Layer | Technology | Version | Primary File(s) |
|---|---|---|---|
| Framework | FastAPI | 0.115.9 | `backend/main.py` |
| ASGI Server | Uvicorn | 0.40.0 | Procfile / Railway |
| Validation | Pydantic | 2.12.5 | `backend/schemas.py` |
| HTTP (sync) | requests | 2.32.3 | `backend/pncp_client.py` (PNCPClient) |
| HTTP (async) | httpx | 0.28.1 | `backend/pncp_client.py` (AsyncPNCPClient) |
| Excel | openpyxl | 3.1.5 | `backend/excel.py` |
| LLM | OpenAI SDK | 1.109.1 | `backend/llm.py` |
| Auth/DB | supabase-py | 2.13.0 | `backend/supabase_client.py` |
| JWT | PyJWT | 2.9.0 | `backend/auth.py` |
| Payments | stripe | 11.4.1 | `backend/webhooks/stripe.py` |
| Cache | redis | 5.2.1 | `backend/redis_pool.py` |
| Google APIs | google-api-python-client | 2.150.0 | `backend/routes/export_sheets.py` |
| Email | resend | >=2.0.0 | `backend/routes/emails.py` |
| Logging | python-json-logger | >=2.0.4 | `backend/config.py` |
| Error tracking | sentry-sdk | >=2.0.0 | `backend/main.py` |
| Config | PyYAML | >=6.0 | `backend/sectors.py` (loads `sectors_data.yaml`) |

### 2.2 Frontend

| Layer | Technology | Version | Primary File(s) |
|---|---|---|---|
| Framework | Next.js | ^16.1.6 | `frontend/next.config.js` |
| Language | TypeScript | ^5.9.3 | `frontend/tsconfig.json` |
| UI | React | ^18.3.1 | `frontend/app/` |
| Styling | Tailwind CSS | ^3.4.19 | `frontend/tailwind.config.ts` |
| Auth | @supabase/ssr | ^0.8.0 | `frontend/middleware.ts` |
| Charts | recharts | ^3.7.0 | Dashboard page |
| Animation | framer-motion | ^12.33.0 | Landing page, transitions |
| Icons | lucide-react | ^0.563.0 | Throughout |
| Date | date-fns | ^4.1.0 | Date formatting |
| Toast | sonner | ^2.0.7 | `frontend/app/layout.tsx` |
| DnD | @dnd-kit | ^6.3.1 | Pipeline page |
| Analytics | mixpanel-browser | ^2.74.0 | `AnalyticsProvider.tsx` |
| Error tracking | @sentry/nextjs | ^10.38.0 | `next.config.js` |
| Onboarding | shepherd.js | ^14.5.1 | Onboarding wizard |
| Testing | Jest + Testing Library | ^29.7.0 | `frontend/__tests__/` |
| E2E | Playwright | ^1.58.1 | `frontend/e2e-tests/` |

### 2.3 Infrastructure

| Service | Purpose |
|---|---|
| **Railway** | Backend + Frontend deployment (standalone Node.js output) |
| **Supabase** | PostgreSQL database, Auth (email + Google OAuth), Storage |
| **Redis** | Optional: SSE progress pub/sub, feature flag cache, search result cache |
| **Stripe** | Payment processing, subscription management |
| **Sentry** | Error tracking (backend + frontend) |
| **Mixpanel** | Product analytics (frontend) |
| **GitHub Actions** | CI/CD (tests, e2e, deploy, CodeQL, Lighthouse) |

---

## 3. Backend Architecture

### 3.1 Module Dependency Graph

```
main.py (FastAPI app, lifespan, middleware, core endpoints)
  |
  +-- routes/search.py --> search_pipeline.py (7-stage pipeline)
  |     +-- search_context.py (mutable context object)
  |     +-- pncp_client.py (PNCP API: PNCPClient + AsyncPNCPClient)
  |     +-- clients/*.py (multi-source adapters)
  |     +-- consolidation.py (multi-source orchestration)
  |     +-- filter.py (keyword matching engine)
  |     +-- llm_arbiter.py (GPT-4o-mini false positive elimination)
  |     +-- relevance.py (scoring, min-match calculation)
  |     +-- term_parser.py (search term parsing)
  |     +-- llm.py (GPT-4.1-nano summaries)
  |     +-- excel.py (openpyxl report generation)
  |     +-- storage.py (Supabase Storage upload)
  |     +-- progress.py (SSE progress tracker, Redis pub/sub)
  |     +-- quota.py (plan capabilities, monthly quota)
  |
  +-- routes/user.py (profile, password change, account deletion)
  +-- routes/billing.py (checkout, plan management)
  +-- routes/plans.py (plan listing)
  +-- routes/sessions.py (search history)
  +-- routes/pipeline.py (opportunity pipeline CRUD)
  +-- routes/messages.py (in-app messaging)
  +-- routes/analytics.py (usage analytics)
  +-- routes/emails.py (transactional emails via Resend)
  +-- routes/auth_oauth.py (Google OAuth)
  +-- routes/export_sheets.py (Google Sheets export)
  +-- routes/subscriptions.py (subscription management)
  +-- routes/features.py (feature flags)
  +-- admin.py (admin CRUD endpoints)
  +-- webhooks/stripe.py (Stripe webhook handler)
  |
  +-- auth.py (JWT validation: HS256/ES256 + JWKS)
  +-- authorization.py (role-based access: admin, master)
  +-- rate_limiter.py (request rate limiting)
  +-- middleware.py (CorrelationID, SecurityHeaders, Deprecation)
  +-- config.py (feature flags, CORS, logging, env validation)
  +-- redis_pool.py (Redis connection pool + InMemoryCache fallback)
  +-- supabase_client.py (Supabase admin client singleton)
  +-- log_sanitizer.py (PII masking)
  +-- sectors.py + sectors_data.yaml (15 sector configurations)
  +-- exceptions.py (custom exception hierarchy)
```

### 3.2 API Versioning

The API uses dual-mount strategy (defined in `main.py` lines 242-278):

- **Versioned:** All routers mounted under `/v1/` prefix
- **Legacy:** Same routers also mounted at root (no prefix) for backward compatibility
- **Deprecation:** `DeprecationMiddleware` adds RFC 8594 headers to legacy routes (`Sunset: 2026-06-01`)

### 3.3 Search Pipeline (Core Business Logic)

File: `backend/search_pipeline.py` (STORY-216)

The search is decomposed into 7 stages:

| Stage | Name | Responsibility |
|---|---|---|
| 1 | ValidateRequest | Input validation, quota check, plan resolution |
| 2 | PrepareSearch | Term parsing, sector config, query param construction |
| 3 | ExecuteSearch | PNCP API calls (parallel UF fetch), multi-source consolidation |
| 4 | FilterResults | Keyword matching, value/status/modality/esfera filters |
| 5 | EnrichResults | Relevance scoring, sorting, status inference |
| 6 | GenerateOutput | LLM summary (GPT-4.1-nano or fallback), Excel generation |
| 7 | Persist | Session save, response construction |

Each stage operates on a `SearchContext` (mutable dataclass) and has independent error handling -- failure in Stage 6 preserves Stage 4 results.

### 3.4 PNCP Client (`pncp_client.py`)

Two implementations coexist:

**PNCPClient (synchronous, `requests`):**
- Used for single-UF sequential fetching
- urllib3 Retry adapter with configurable strategy
- Rate limiting: 100ms between requests (10 req/s)
- Date chunking: splits ranges >30 days into 30-day windows
- Deduplication via `seen_ids` set
- Lines 223-712

**AsyncPNCPClient (async, `httpx`):**
- Used for parallel multi-UF fetching (`buscar_todas_ufs_paralelo`)
- `asyncio.Semaphore` for concurrency control (default 10)
- Per-modality timeout (15s default, configurable via `PNCP_TIMEOUT_PER_MODALITY`)
- Per-UF timeout (30s normal, 45s degraded mode)
- Health canary probe before full search
- Circuit breaker integration
- Auto-retry failed UFs (1 round, 5s delay)
- Lines 727-1585

**Circuit Breaker (`PNCPCircuitBreaker`):**
- Singleton at module level (`_circuit_breaker`)
- Threshold: 8 consecutive failures (configurable via env)
- Cooldown: 120s (configurable)
- Degraded mode: reduces concurrency to 3 UFs, extends timeouts to 45s
- UF priority ordering by population in degraded mode
- Lines 70-176

### 3.5 Filtering Engine (`filter.py`)

The file is large (775+ lines) and handles:

1. **Keyword matching:** 50+ terms in `KEYWORDS_UNIFORMES` for the vestuario sector, plus sector-specific keywords loaded from `sectors_data.yaml`
2. **Exclusion keywords:** `KEYWORDS_EXCLUSAO` prevents false positives
3. **Context-required keywords:** Ambiguous terms (e.g., "mesa", "banco") only match if context keywords are also present
4. **Unicode normalization:** `normalize_text()` strips accents for matching
5. **Term validation:** Stopword removal, min-length (4 chars), special character filtering
6. **LLM Arbiter integration:** For ambiguous matches (2-5% term density), GPT-4o-mini classifies as relevant/irrelevant
7. **Filter stats tracking:** Per-filter rejection counters for transparency

Filter application order (fail-fast):
1. UF check (fastest)
2. Value range
3. Max contract value (sector ceiling)
4. Red flag keywords
5. Keyword matching + LLM arbiter
6. Status/deadline validation

### 3.6 Multi-Source Architecture

Directory: `backend/clients/`

| Client | File | Status |
|---|---|---|
| PNCP (primary) | `pncp_client.py` | Production |
| ComprasGov | `clients/compras_gov_client.py` | Adapter exists |
| Portal Compras | `clients/portal_compras_client.py` | Adapter exists |
| Portal Transparencia | `clients/portal_transparencia_client.py` | Adapter exists |
| Querido Diario | `clients/querido_diario_client.py` | Adapter exists |
| Licitar Digital | `clients/licitar_client.py` | Adapter exists |
| Sanctions (CEIS/CNEP) | `clients/sanctions.py` | Production (STORY-256) |

Base class: `clients/base.py` defines `SourceAdapter` interface with `SourceMetadata`, `SourceCapability`, `SourceStatus`, and `UnifiedProcurement` types.

`consolidation.py` orchestrates multi-source fetching with deduplication and priority-based merging.

### 3.7 Sector Configuration (`sectors.py` + `sectors_data.yaml`)

15 sectors defined in YAML, each with:
- `keywords`: Set of Portuguese terms for the sector
- `exclusions`: Terms that indicate false positives
- `context_required_keywords`: Ambiguous terms needing context verification
- `max_contract_value`: Ceiling above which contracts are likely multi-sector infrastructure (anti-false-positive)

Sectors: vestuario, alimentos, informatica, mobiliario, papelaria, engenharia, software, facilities, saude, vigilancia, transporte, manutencao_predial, engenharia_rodoviaria, materiais_eletricos, materiais_hidraulicos.

---

## 4. Frontend Architecture

### 4.1 App Router Structure

```
frontend/app/
  page.tsx              # Landing page (institutional, public)
  layout.tsx            # Root layout: providers (Theme, Auth, Analytics, NProgress)
  buscar/page.tsx       # Core search page (authenticated)
  dashboard/page.tsx    # Personal analytics dashboard
  historico/page.tsx    # Search history
  pipeline/page.tsx     # Opportunity pipeline (kanban-style)
  planos/page.tsx       # Pricing/plans page
  planos/obrigado/      # Post-purchase thank you
  login/page.tsx        # Login page
  signup/page.tsx       # Registration page
  conta/page.tsx        # Account settings
  admin/page.tsx        # Admin dashboard
  mensagens/page.tsx    # In-app messaging
  ajuda/page.tsx        # Help/FAQ page
  onboarding/page.tsx   # Onboarding wizard
  features/page.tsx     # Feature showcase
  pricing/page.tsx      # Alternative pricing page
  termos/page.tsx       # Terms of service
  privacidade/page.tsx  # Privacy policy
  recuperar-senha/      # Password recovery
  redefinir-senha/      # Password reset
  auth/callback/        # OAuth callback handler
```

### 4.2 Component Inventory (50+ components)

**Search UI:**
- `RegionSelector.tsx` - UF multi-select with region grouping
- `CustomDateInput.tsx` - Date range picker
- `CustomSelect.tsx` - Sector selector
- `EsferaFilter.tsx` - Government sphere filter (Federal/State/Municipal)
- `OrgaoFilter.tsx` - Agency name filter
- `MunicipioFilter.tsx` - Municipality filter
- `OrdenacaoSelect.tsx` - Sort order selector
- `PaginacaoSelect.tsx` - Items per page selector
- `SavedSearchesDropdown.tsx` - Saved search management
- `LoadingProgress.tsx` - SSE-powered progress bar
- `LicitacaoCard.tsx` - Individual bid result card
- `LicitacoesPreview.tsx` - Results preview (free tier blur)
- `EmptyState.tsx` - No results guidance

**Pipeline:**
- `AddToPipelineButton.tsx` - Add bid to pipeline
- `PipelineAlerts.tsx` - Deadline alert badges

**Billing/Plans:**
- `PlanBadge.tsx` - Current plan indicator
- `QuotaBadge.tsx` - Quota usage indicator
- `QuotaCounter.tsx` - Detailed quota display
- `UpgradeModal.tsx` - Plan upgrade dialog

**Layout:**
- `AppHeader.tsx` - Authenticated header
- `UserMenu.tsx` - User dropdown menu
- `Footer.tsx` - Site footer
- `Breadcrumbs.tsx` - Navigation breadcrumbs
- `InstitutionalSidebar.tsx` - Marketing sidebar

**Landing Page (7 sections):**
- `landing/LandingNavbar.tsx`, `HeroSection.tsx`, `OpportunityCost.tsx`, `BeforeAfter.tsx`, `DifferentialsGrid.tsx`, `HowItWorks.tsx`, `StatsSection.tsx`, `DataSourcesSection.tsx`, `SectorsGrid.tsx`, `FinalCTA.tsx`, `TestimonialsCarousel.tsx`

**System:**
- `ThemeProvider.tsx` - Dark/light theme with localStorage persistence
- `AuthProvider.tsx` - Supabase auth context
- `AnalyticsProvider.tsx` - Mixpanel tracking context
- `NProgressProvider.tsx` - Page transition progress bar
- `CookieConsentBanner.tsx` - LGPD compliance
- `SessionExpiredBanner.tsx` - Re-auth prompt

### 4.3 API Proxy Layer

The frontend uses Next.js API routes as a BFF (Backend-for-Frontend) proxy. 19 API routes in `frontend/app/api/`:

| Route | Method | Backend Target | Purpose |
|---|---|---|---|
| `/api/buscar` | POST | `/v1/buscar` | Search proxy with retry logic (2 attempts) |
| `/api/buscar-progress` | GET | `/v1/buscar-progress/{id}` | SSE progress streaming |
| `/api/download` | GET | Filesystem/Storage | Excel file download |
| `/api/me` | GET | `/v1/me` | User profile/plan info |
| `/api/me/export` | POST | `/v1/export/google-sheets` | Google Sheets export |
| `/api/sessions` | GET | `/v1/sessions` | Search history |
| `/api/search-history` | GET | `/v1/sessions` | Search history (alias) |
| `/api/pipeline` | GET/POST/PUT/DELETE | `/v1/pipeline` | Pipeline CRUD |
| `/api/setores` | GET | `/v1/setores` | Sector list |
| `/api/health` | GET | Direct | Frontend health check |
| `/api/analytics` | POST | `/v1/analytics` | Usage analytics |
| `/api/change-password` | POST | `/v1/change-password` | Password change |
| `/api/profile-context` | GET/POST | `/v1/profile/context` | Onboarding context |
| `/api/messages/*` | Various | `/v1/messages/*` | In-app messaging |
| `/api/admin/[...path]` | Various | `/v1/admin/*` | Admin catch-all proxy |

### 4.4 State Management

- **No external state library** -- React `useState`/`useEffect` hooks only
- **Custom hooks:** `useSavedSearches`, `useOnboarding`, `useKeyboardShortcuts`, `useSearchFilters`, `useAnalytics`, `useFeatureFlags`
- **Server-side auth:** `@supabase/ssr` with `getAll/setAll` cookie pattern in `middleware.ts`
- **localStorage:** Theme preference (`bidiq-theme`), plan cache (1hr TTL), saved searches
- **SSE:** Dual-connection pattern for search progress (`GET /buscar-progress/{search_id}` + `POST /buscar`)
- **Token refresh:** `lib/serverAuth.ts` handles server-side token refresh, falls back to header token

### 4.5 Build & Output

- `output: 'standalone'` in `next.config.js` for Docker-compatible production deployment
- Custom `postbuild` script copies `public/` and `.next/static/` into standalone directory
- Dynamic build IDs (`build-${Date.now()}-${random}`) to prevent stale cache issues
- Sentry source map upload via `@sentry/nextjs` wrapper

---

## 5. Database Architecture

### 5.1 Supabase PostgreSQL Schema

26 migrations in `supabase/migrations/`, establishing these core tables:

| Table | Migration | Purpose | RLS |
|---|---|---|---|
| `profiles` | 001 | User profiles (extends `auth.users`) | Yes |
| `plans` | 001 | Plan catalog (free, consultor_agil, maquina, sala_guerra) | No |
| `user_subscriptions` | 001 | Active subscriptions, Stripe refs | Yes |
| `search_sessions` | 001 | Search history per user | Yes |
| `monthly_quota` | 002 | Monthly search usage tracking | Yes |
| `plan_features` | 009 | Feature flags per plan | No |
| `stripe_webhook_events` | 010 | Idempotent webhook processing | No |
| `messages_conversations` | 012 | In-app support conversations | Yes |
| `messages_messages` | 012 | Individual messages in threads | Yes |
| `google_oauth_tokens` | 013 | OAuth refresh tokens for Google | Yes |
| `google_sheets_exports` | 014 | Google Sheets export history | Yes |
| `audit_events` | 023 | Security audit log | No |
| `profile_context` | 024 | Onboarding business context (JSONB) | Yes |
| `pipeline_items` | 025 | Opportunity pipeline tracking | Yes |
| `search_results_cache` | 026 | Cached search results (TTL-based) | No |

### 5.2 Key Relationships

```
auth.users (Supabase Auth)
  |-- profiles (1:1, on delete cascade)
  |     |-- user_subscriptions (1:many)
  |     |-- search_sessions (1:many)
  |     |-- monthly_quota (1:many, partitioned by month_year)
  |     |-- messages_conversations (1:many)
  |     |-- google_oauth_tokens (1:many)
  |     |-- google_sheets_exports (1:many)
  |     |-- pipeline_items (1:many, unique on user_id+pncp_id)
  |     +-- profile_context (1:1)
  |
  +-- plans (referenced by user_subscriptions.plan_id)
```

### 5.3 RLS (Row-Level Security) Policies

All user-facing tables have RLS enabled with policies:
- Users can only SELECT/INSERT/UPDATE/DELETE their own rows (`auth.uid() = user_id`)
- Service role (backend) has full access for admin operations
- `pipeline_items` (migration 025) has comprehensive RLS: separate policies for SELECT, INSERT, UPDATE, DELETE

### 5.4 Database Functions

| Function | Migration | Purpose |
|---|---|---|
| `handle_new_user()` | 001 | Auto-create profile on signup (trigger) |
| `increment_quota_atomic()` | 003 | Atomic quota increment with limit check |
| `check_and_increment_quota()` | 003 | Combined check+increment (TOCTOU prevention) |
| `increment_existing_quota()` | 003 | Fallback atomic increment |
| `sync_plan_type_on_subscription()` | 017 | Keep `profiles.plan_type` in sync with subscriptions |
| `update_pipeline_updated_at()` | 025 | Auto-update timestamp trigger |

### 5.5 Notable Migrations

- **006b (DEPRECATED):** Duplicate migration file exists with `_DUPLICATE` suffix -- should be cleaned up
- **020:** Tightened `plan_type` CHECK constraint to current tier names
- **026:** Search results cache table with TTL for the STORY-257A cache layer

---

## 6. External Integrations

### 6.1 PNCP API

- **Base URL:** `https://pncp.gov.br/api/consulta/v1`
- **Endpoint:** `/contratacoes/publicacao`
- **Auth:** None (public API)
- **Rate limit:** 10 req/s (self-imposed in `PNCPClient._rate_limit()`)
- **Pagination:** API returns `paginasRestantes` for next-page detection
- **Date format:** `yyyyMMdd` (converted from `YYYY-MM-DD` in client)
- **Resilience:** Retry (3 attempts), exponential backoff (1.5s base), circuit breaker (8 failures / 120s cooldown)
- **Modalities queried:** 4 (Concorrencia Eletronica), 5 (Concorrencia Presencial), 6 (Pregao Eletronico), 7 (Pregao Presencial)
- **Excluded modalities:** 9 (Inexigibilidade), 14 (Inaplicabilidade)

### 6.2 OpenAI

- **Summary model:** `gpt-4.1-nano` (500-1200 tokens, temp=0.3)
- **Arbiter model:** `gpt-4o-mini` (1 token, temp=0, deterministic SIM/NAO classification)
- **Structured output:** Pydantic `ResumoEstrategico` schema via `response_format` parameter
- **Fallback:** `gerar_resumo_fallback()` generates heuristic summary without API call
- **Input limit:** 50 bids max, 200-char truncation on `objetoCompra`
- **Cost estimate:** LLM Arbiter ~R$ 0.50/month for 10K classifications

### 6.3 Stripe

- **Webhook endpoint:** `POST /webhooks/stripe` (`backend/webhooks/stripe.py`)
- **Events handled:** `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_succeeded`
- **Security:** Signature verification via `STRIPE_WEBHOOK_SECRET`
- **Idempotency:** Event deduplication via `stripe_webhook_events` table
- **Plan sync:** Updates `profiles.plan_type` on every webhook for reliable fallback

### 6.4 Supabase

- **Database:** PostgreSQL with RLS
- **Auth:** Email/password + Google OAuth (STORY-180)
- **Storage:** Excel file upload for signed URL download
- **Client:** Service role key (admin privileges) in `supabase_client.py`
- **JWT:** ES256 (JWKS) with HS256 backward compatibility (`auth.py` STORY-227)

### 6.5 Google APIs

- **Google Sheets:** Export search results to user's Google Sheets (`routes/export_sheets.py`)
- **Google OAuth:** Login via Google account (`routes/auth_oauth.py`)
- **Token storage:** OAuth refresh tokens in `google_oauth_tokens` table

### 6.6 Resend (Transactional Email)

- **Route:** `routes/emails.py` (STORY-225)
- **Use cases:** Quota warning (80%), quota exhaustion (100%), welcome email

### 6.7 Sanctions Check (CEIS/CNEP)

- **Client:** `clients/sanctions.py` (STORY-256)
- **API:** Brazil's CEIS (Empresas Inidôneas e Suspensas) and CNEP (Empresas Punidas) registries
- **Optional:** Triggered by `check_sanctions: true` in `BuscaRequest`

---

## 7. Infrastructure & Deployment

### 7.1 Railway Deployment

- **Backend:** Python 3.11/3.12, Uvicorn ASGI server
- **Frontend:** Next.js standalone output (`node .next/standalone/server.js`)
- **Health check:** `GET /health` (backend), `GET /api/health` (frontend)
- **Environment:** Managed via Railway dashboard + `railway variables`
- **Custom domain:** `smartlic.tech` (STORY-210 AC14)
- **Domain redirect:** `middleware.ts` forces `railway.app` -> `smartlic.tech` (301)

### 7.2 CI/CD (GitHub Actions)

12 workflow files in `.github/workflows/`:

| Workflow | File | Trigger | Purpose |
|---|---|---|---|
| Tests | `tests.yml` | push/PR to main | Backend tests (Python 3.11+3.12), Frontend tests, Integration tests, E2E tests |
| Backend CI | `backend-ci.yml` | push/PR | Backend-specific CI |
| E2E | `e2e.yml` | push/PR | Playwright E2E tests |
| Deploy | `deploy.yml` | push to main | Production deployment |
| Staging | `staging-deploy.yml` | push to develop | Staging deployment |
| CodeQL | `codeql.yml` | schedule/PR | Security analysis |
| Lighthouse | `lighthouse.yml` | PR | Performance audit |
| Load Test | `load-test.yml` | manual | Load testing |
| PR Validation | `pr-validation.yml` | PR | PR quality checks |
| Sync Sectors | `sync-sectors.yml` | schedule | Frontend sector fallback sync |
| Cleanup | `cleanup.yml` | schedule | Artifact cleanup |
| Dependabot | `dependabot-auto-merge.yml` | PR | Auto-merge minor updates |

### 7.3 Redis (Optional Dependency)

- **Pool:** `redis_pool.py` with 20 max connections, 5s timeout
- **Fallback:** `InMemoryCache` (LRU, 10K entries) when Redis unavailable
- **Uses:** SSE progress pub/sub, feature flag cache, search result cache
- **Health:** Checked in `/health` endpoint; Redis being down = "degraded" not "unhealthy"

---

## 8. Security Architecture

### 8.1 Authentication Flow

```
Browser -> Next.js middleware (Supabase SSR cookie check)
   |
   +-- Protected route? -> Redirect to /login with reason code
   |
   +-- API route? -> Forward to BFF proxy
         |
         +-- getRefreshedToken() (server-side token refresh)
         |
         +-- Authorization: Bearer <JWT> -> Backend
               |
               +-- auth.py: require_auth()
                     |
                     +-- JWT decode (ES256/JWKS or HS256)
                     +-- Token cache (SHA256 hash, 60s TTL)
                     +-- Return user dict {sub, email, role}
```

### 8.2 Authorization Model

- **require_auth:** JWT validation, returns user dict (all authenticated routes)
- **require_admin:** Checks `app_metadata.role == 'admin'` or `user_metadata.role == 'admin'`
- **check_user_roles:** Returns admin/master status with retry (0.3s delay)
- **Admin IDs:** Loaded from `profiles` where `is_admin = true`
- **Master role:** Special plan (`sala_guerra`) with unlimited access

### 8.3 Security Headers

Applied by both backend (`SecurityHeadersMiddleware`) and frontend (`next.config.js`):

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (frontend only)
- Content Security Policy (frontend only, with specific domain allowlists)

### 8.4 Input Validation

- **Backend:** Pydantic models with field validators (`BuscaRequest`, `PipelineItemCreate`, etc.)
- **UUID validation:** `validate_uuid()` in `schemas.py` with UUID v4 regex
- **Search sanitization:** `sanitize_search_query()` with safe character regex, SQL pattern escaping
- **Password policy:** 8+ chars, 1 uppercase, 1 digit (`validate_password()`)
- **Plan ID validation:** Alphanumeric + underscore, 50 char max

### 8.5 PII Protection

- **Log sanitizer:** `log_sanitizer.py` with `mask_email()`, `mask_token()`, `mask_user_id()`, `mask_ip_address()`, `sanitize_dict()`, `sanitize_string()`
- **Sentry scrubbing:** `scrub_pii()` callback in `main.py` strips emails, tokens, user IDs from error events
- **Production logging:** DEBUG level elevated to INFO in production to prevent sensitive data exposure

### 8.6 API Documentation in Production

- **Disabled:** `docs_url=None`, `redoc_url=None`, `openapi_url=None` when `ENVIRONMENT=production` (`main.py` line 211)
- **Prevents:** API reconnaissance by unauthorized actors

### 8.7 CORS Configuration

- **Development:** `http://localhost:3000`, `http://127.0.0.1:3000`
- **Production:** Railway app URLs + `smartlic.tech` + `www.smartlic.tech`
- **Security:** Wildcard `*` explicitly rejected with warning

---

## 9. Code Quality & Testing

### 9.1 Backend Test Suite

**100+ test files** in `backend/tests/`:

Key test areas:
- `test_filter.py` - Keyword matching engine
- `test_pncp_resilience.py` - PNCP client retry/timeout behavior
- `test_llm.py`, `test_llm_fallback.py`, `test_llm_arbiter.py` - LLM integration
- `test_excel.py`, `test_excel_validation.py` - Excel generation
- `test_quota.py`, `test_quota_race_condition.py` - Quota management
- `test_auth.py`, `test_auth_cache.py`, `test_auth_es256.py` - Authentication
- `test_stripe_webhook.py` - Stripe integration
- `test_sanctions.py` - CEIS/CNEP sanctions
- `test_pipeline.py` - Pipeline CRUD
- `test_golden_samples.py` - Regression tests against known good outputs
- `test_security_story210.py`, `test_security_headers.py` - Security
- `test_structured_logging.py` - Log format verification

**Coverage:** Claimed 96.69% (from CLAUDE.md), threshold enforced at 70%.

### 9.2 Frontend Test Suite

**93+ test files** in `frontend/__tests__/`:

- Active tests: ~45 files across components, hooks, pages, API routes, pipeline
- Quarantined tests: ~20 files in `__tests__/quarantine/` (known flaky or broken)
- Coverage threshold: 60% (enforced in `jest.config.js`)
- Current coverage: ~49.46% (below threshold, CI will fail)

Notable test categories:
- Component tests: RegionSelector, CustomDateInput, LoadingProgress, LicitacaoCard, etc.
- Hook tests: useKeyboardShortcuts, useFeatureFlags, useAnalytics, useSearchFilters
- API route tests: buscar, download, health, analytics, messages
- Page tests: Login, Signup, Admin, Historico, Planos, Buscar
- Pipeline tests: AddToPipelineButton, PipelineCard, PipelineAlerts
- Landing page tests: HeroSection, BeforeAfter, DifferentialsGrid, OpportunityCost

### 9.3 E2E Tests

**Playwright** (`frontend/e2e-tests/`):
- Browsers: Chromium + Mobile Safari (iPhone 13)
- Critical flows: Search, Theme switching, Saved searches, Empty state, Error handling
- CI integration: Runs after unit tests pass, 15-min timeout

### 9.4 Type Safety

- **Backend:** Type hints on most functions; Pydantic models for API contracts
- **Frontend:** TypeScript strict mode; generated API types (`app/api-types.generated.ts`)
- **CI check:** `npx tsc --noEmit --pretty` in frontend CI

### 9.5 Linting & Code Quality

- Backend: `ruff` and `mypy` mentioned in CLAUDE.md but not enforced in CI
- Frontend: `next lint` configured but enforcement unclear
- No pre-commit hooks visible in repository

---

## 10. Performance Architecture

### 10.1 Rate Limiting

| Layer | Mechanism | Limit |
|---|---|---|
| PNCP API | `PNCPClient._rate_limit()` | 10 req/s (100ms min interval) |
| Backend per-user | `rate_limiter.py` | Plan-based (2-60 req/min) |
| Frontend proxy | Retry with backoff | 2 attempts, 3s delay |

### 10.2 Caching Strategy

| Cache | Storage | TTL | Purpose |
|---|---|---|---|
| Auth token | In-memory dict | 60s | Reduce JWT validation API calls |
| Plan capabilities | In-memory dict | 300s (5min) | Reduce DB lookups |
| Feature flags | In-memory dict | 60s | Runtime-reloadable config |
| Search results | Redis or InMemoryCache | Configurable | Avoid duplicate PNCP queries |
| JWKS keys | PyJWKClient internal | 300s (5min) | JWT public key caching |
| Frontend plan | localStorage | 1hr | Prevent instant UI downgrades |

### 10.3 Async Patterns

- **Parallel UF fetching:** `asyncio.gather()` with semaphore-controlled concurrency
- **Per-modality timeout:** `asyncio.wait_for()` wraps each modality fetch (15s)
- **SSE streaming:** `StreamingResponse` with `asyncio.Queue` or Redis pub/sub
- **Background callbacks:** `_safe_callback()` handles both sync and async callbacks

### 10.4 Pagination

- **PNCP API:** Server-side pagination (20 items/page, up to 500 pages max)
- **Search results:** Client-side pagination via `pagina` + `itens_por_pagina` (10/20/50/100)
- **Session history:** `limit` + `offset` parameters

---

## 11. Technical Debt Registry

### 11.1 Critical (Must Fix)

| ID | Issue | Location | Impact |
|---|---|---|---|
| TD-C01 | **Frontend test coverage below threshold** | `frontend/__tests__/` | CI fails; 49.46% vs 60% threshold. 20+ quarantined test files indicate systemic test quality issues. |
| TD-C02 | **Dual HTTP client implementations** | `backend/pncp_client.py` | `PNCPClient` (sync, requests) and `AsyncPNCPClient` (async, httpx) duplicate retry logic, rate limiting, and error handling. 1585 lines total. The sync client is only used in `PNCPLegacyAdapter.fetch()` single-UF fallback path. |
| TD-C03 | **LLM Arbiter hardcoded sector description** | `backend/llm_arbiter.py` lines 115-137 | Conservative prompt has hardcoded "Vestuario e Uniformes" sector description that is incorrectly applied to ALL 15 sectors. Acknowledged in `config.py` line 263. |

### 11.2 High (Should Fix)

| ID | Issue | Location | Impact |
|---|---|---|---|
| TD-H01 | **In-memory progress tracker not horizontally scalable** | `backend/progress.py` `_active_trackers` dict | Redis pub/sub mode exists but the in-memory tracker is still the primary registry. Two Railway instances would have split progress state. |
| TD-H02 | **Deprecated migration file not cleaned up** | `supabase/migrations/006b_DEPRECATED_search_sessions_service_role_policy_DUPLICATE.sql` | Confuses schema understanding; should be removed. |
| TD-H03 | **In-memory auth token cache** | `backend/auth.py` `_token_cache` dict | Not shared across instances. Redundant with JWT self-validation but still populated. |
| TD-H04 | **Legacy plan seeds in migration 001 vs current plan IDs** | `supabase/migrations/001` seeds `free`, `pack_5`, `pack_10`, `monthly`, `annual`, `master`; current code uses `free_trial`, `consultor_agil`, `maquina`, `sala_guerra` | Plan mapping logic in `quota.py` `get_plan_from_profile()` (lines 525-531) handles this translation, but it adds complexity. |
| TD-H05 | **`save_search_session` uses synchronous sleep** | `backend/quota.py` line 910 | `time.sleep(0.3)` blocks the async event loop on retry. Should use `asyncio.sleep()`. |
| TD-H06 | **Excel base64 fallback in frontend proxy** | `frontend/app/api/buscar/route.ts` lines 197-223 | Writes base64 Excel to filesystem `tmpdir()` as fallback. Not scalable, not cleaned on crash. Signed URL from storage is preferred path. |
| TD-H07 | **Backend routes mounted twice** | `backend/main.py` lines 242-278 | Every router mounted at both `/v1/` and root. Doubles route table size and complicates debugging. Sunset date 2026-06-01 set. |
| TD-H08 | **No backend linting enforcement in CI** | `.github/workflows/tests.yml` | `ruff` and `mypy` not run in CI pipeline despite being mentioned in CLAUDE.md. |

### 11.3 Medium (Plan to Fix)

| ID | Issue | Location | Impact |
|---|---|---|---|
| TD-M01 | **`search_pipeline.py` becoming a god module** | `backend/search_pipeline.py` | After STORY-216 decomposition, this file absorbed the complexity from `main.py`. 7 stages with inline helper functions. |
| TD-M02 | **Feature flags in environment variables** | `backend/config.py` | 7+ feature flags managed via env vars with in-memory TTL cache. No runtime toggle UI (admin can POST to reload, but flags require container restart to change). |
| TD-M03 | **`dotenv` loaded before FastAPI imports** | `backend/main.py` line 33 | `load_dotenv()` called at module level, before `setup_logging()`. Means some env vars read at import time may use stale values. |
| TD-M04 | **`AssertionError` typo** | `backend/filter.py` line 148 | `raise AssertionError(...)` -- typo for `AssertionError` (should be `AssertionError`). Actually this IS the correct Python built-in name, not a typo. Disregard. |
| TD-M05 | **Hardcoded User-Agent string** | `backend/pncp_client.py` line 264 | `"BidIQ/1.0 (procurement-search; contact@bidiq.com.br)"` -- still references BidIQ, not SmartLic. Also hardcoded in `AsyncPNCPClient`. |
| TD-M06 | **No database connection pooling in Supabase client** | `backend/supabase_client.py` | Single global client instance. No explicit connection pool management. Relies on supabase-py internal handling. |
| TD-M07 | **Integration tests placeholder** | `.github/workflows/tests.yml` lines 216-221 | Integration test job exists but just echoes a skip message. |
| TD-M08 | **Frontend quarantine tests growing** | `frontend/__tests__/quarantine/` | 20+ test files quarantined. Indicates either flaky tests or broken component contracts. |
| TD-M09 | **No request timeout for Stripe webhooks** | `backend/webhooks/stripe.py` | Webhook handler has no explicit timeout. Long-running DB operations could block the worker. |
| TD-M10 | **`datetime.now()` without timezone in `excel.py` and `llm.py`** | `backend/excel.py` line 227, `backend/llm.py` line 97 | Uses naive `datetime.now()` instead of `datetime.now(timezone.utc)`. Could cause issues in non-UTC server environments. |

### 11.4 Low (Nice to Fix)

| ID | Issue | Location | Impact |
|---|---|---|---|
| TD-L01 | **Screenshot files in git status** | Root directory | 18 untracked `.png` files in repository root. Should be gitignored. |
| TD-L02 | **`_request_count` never reset** | `backend/pncp_client.py` line 237 | Counter grows indefinitely per client instance. Only diagnostic, but could overflow in very long-lived processes. |
| TD-L03 | **`asyncio.get_event_loop().time()` deprecated pattern** | `backend/pncp_client.py` line 861 | Should use `asyncio.get_running_loop().time()` in Python 3.10+. |
| TD-L04 | **CSS class `sr-only` hardcoded inline** | `frontend/app/layout.tsx` line 96 | Skip navigation link styles inline rather than using Tailwind utility properly. |
| TD-L05 | **`format_resumo_html` function unused** | `backend/llm.py` lines 232-300 | Generates HTML for summaries but the frontend renders from JSON, not HTML. Dead code. |
| TD-L06 | **`dangerouslySetInnerHTML` for theme script** | `frontend/app/layout.tsx` lines 73-89 | Necessary for FOUC prevention but should have a comment explaining XSS safety. |

---

## Appendix: File Inventory

### Backend Module Count

| Category | Count | Key Files |
|---|---|---|
| Core modules | ~20 | main.py, pncp_client.py, filter.py, excel.py, llm.py, schemas.py, config.py, etc. |
| Route modules | 14 | routes/search.py, routes/user.py, routes/billing.py, etc. |
| Client adapters | 9 | clients/base.py, sanctions.py, compras_gov_client.py, etc. |
| Test files | 100+ | tests/test_*.py |
| Utility modules | ~10 | middleware.py, log_sanitizer.py, redis_pool.py, etc. |

### Frontend Page Count

| Type | Count |
|---|---|
| Pages (app router) | 21 |
| API routes | 19 |
| Components | 50+ |
| Test files | 93+ |
| Hooks | 6+ |

### Database

| Item | Count |
|---|---|
| Migrations | 26 |
| Tables | ~15 |
| RLS policies | ~20 |
| Functions/triggers | 6 |

### CI/CD Workflows

| Workflows | 12 |
|---|---|

---

*End of System Architecture Document - SmartLic/BidIQ v2.0*
*Generated 2026-02-15 by @architect (Helix) during Brownfield Discovery Phase 1*
