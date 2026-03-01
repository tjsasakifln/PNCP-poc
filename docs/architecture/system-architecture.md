# System Architecture - SmartLic

**Version:** 3.0
**Date:** 2026-02-25
**Author:** @architect (Archon) - Brownfield Discovery Phase 1
**Status:** Comprehensive analysis of production codebase on `main` branch (commit `0c3de659`)
**Previous version:** v2.0 (2026-02-15, Helix)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Tech Stack Overview](#2-tech-stack-overview)
3. [Folder Structure](#3-folder-structure)
4. [Backend Architecture](#4-backend-architecture)
5. [Frontend Architecture](#5-frontend-architecture)
6. [Data Flow: Search Pipeline](#6-data-flow-search-pipeline)
7. [Database Architecture](#7-database-architecture)
8. [External Integrations](#8-external-integrations)
9. [Infrastructure and Deployment](#9-infrastructure-and-deployment)
10. [Key Architectural Patterns](#10-key-architectural-patterns)
11. [Configuration and Feature Flags](#11-configuration-and-feature-flags)
12. [Security Architecture](#12-security-architecture)
13. [Observability](#13-observability)
14. [Code Quality and Testing](#14-code-quality-and-testing)
15. [Technical Debt Registry](#15-technical-debt-registry)
16. [Appendix: Complete File Inventory](#appendix-complete-file-inventory)

---

## 1. Executive Summary

**SmartLic** (formerly BidIQ Uniformes) is a SaaS platform for automated government procurement opportunity discovery from Brazil's official data sources. It aggregates, classifies, and scores public bids (licitacoes) using AI-powered filtering and viability assessment.

### Key Characteristics

| Attribute | Value |
|---|---|
| **Architecture Style** | Monolithic API + SPA with BFF (Backend-for-Frontend) proxy layer |
| **Stage** | POC avancado (v0.5) in production, beta with trials, pre-revenue |
| **Production URL** | https://smartlic.tech |
| **Primary Data Sources** | PNCP (priority 1), PCP v2 (priority 2), ComprasGov v3 (priority 3) |
| **Revenue Model** | Single subscription (free trial 14d + SmartLic Pro R$397/mo) via Stripe |
| **AI Integration** | GPT-4.1-nano (classification + summaries via OpenAI SDK) |
| **Scale** | Dual-instance deployment (web + worker on Railway), Redis for distributed state |
| **Maturity** | 69 backend Python modules, 29 frontend pages, 43 Supabase migrations, 300+ test files |
| **Sectors** | 15 industry verticals with keyword-based classification |
| **Target Audience** | B2G companies (all sizes) + procurement consultancies |

### Architecture Risk Rating: MEDIUM

The system is functional in production with comprehensive resilience patterns. Primary risks:
- In-memory state (`_active_trackers` in `progress.py`, `_token_cache` in `auth.py`) complicates horizontal scaling beyond 2 instances
- `search_pipeline.py` is the central "god module" that orchestrates all 7 stages
- Dual HTTP client implementations (sync `requests` + async `httpx`) in `pncp_client.py` create maintenance burden
- 43 database migrations with naming convention inconsistencies suggest schema churn
- Routes mounted twice (versioned `/v1/` + legacy root) double the route table

---

## 2. Tech Stack Overview

### 2.1 Backend

| Layer | Technology | Version (Pinned) | Primary File(s) |
|---|---|---|---|
| Framework | FastAPI | 0.129.0 | `backend/main.py` |
| ASGI Server | Uvicorn | 0.41.0 | via Gunicorn workers |
| Process Manager | Gunicorn | 23.0.0 | `backend/start.sh`, `backend/gunicorn_conf.py` |
| Validation | Pydantic | 2.12.5 | `backend/schemas.py` |
| Settings | pydantic-settings | 2.10.1 | `backend/config.py` |
| ASGI Framework | Starlette | 0.52.1 | Middleware, routing |
| HTTP (sync) | requests | 2.32.3 | `backend/pncp_client.py` (PNCPClient) |
| HTTP (async) | httpx | 0.28.1 | `backend/pncp_client.py` (AsyncPNCPClient) |
| URL Parsing | urllib3 | 2.6.3 | Retry adapter |
| Excel | openpyxl | 3.1.5 | `backend/excel.py` |
| LLM | OpenAI SDK | 1.109.1 | `backend/llm.py`, `backend/llm_arbiter.py` |
| Auth/DB | supabase-py | 2.28.0 | `backend/supabase_client.py` |
| JWT | PyJWT | 2.11.0 | `backend/auth.py` (ES256/JWKS + HS256) |
| Cryptography | cryptography | 43.0.3 | ES256 JWT support |
| Payments | stripe | 11.4.1 | `backend/webhooks/stripe.py` |
| Cache | redis | 5.3.1 | `backend/redis_pool.py` |
| Job Queue | arq | >=0.26 | `backend/job_queue.py` |
| Google APIs | google-api-python-client | 2.190.0 | `backend/routes/export_sheets.py` |
| Google Auth | google-auth | 2.48.0 | `backend/oauth.py` |
| Email | resend | >=2.0.0 | `backend/email_service.py` |
| Config | PyYAML | >=6.0 | `backend/sectors.py` |
| Logging | python-json-logger | >=2.0.4 | `backend/config.py` |
| Error Tracking | sentry-sdk[fastapi] | >=2.0.0 | `backend/main.py` |
| Metrics | prometheus_client | >=0.20.0 | `backend/metrics.py` |
| Tracing | opentelemetry-api/sdk | >=1.25 | `backend/telemetry.py` |
| OTel Exporters | opentelemetry-exporter-otlp-proto-http | >=1.25 | Distributed tracing |
| OTel Instrumentation | opentelemetry-instrumentation-fastapi/httpx | >=0.46b0 | Auto-instrumentation |
| Runtime | Python | 3.12 (Dockerfile uses 3.11-slim) | `backend/pyproject.toml` |

### 2.2 Frontend

| Layer | Technology | Version | Primary File(s) |
|---|---|---|---|
| Framework | Next.js | ^16.1.6 | `frontend/next.config.js` |
| Language | TypeScript | ^5.9.3 | `frontend/tsconfig.json` |
| UI | React | ^18.3.1 | `frontend/app/` |
| React DOM | react-dom | ^18.3.1 | |
| Styling | Tailwind CSS | ^3.4.19 | `frontend/tailwind.config.ts` |
| Typography | @tailwindcss/typography | ^0.5.19 | Blog content styling |
| Auth | @supabase/ssr | ^0.8.0 | `frontend/middleware.ts` |
| Supabase JS | @supabase/supabase-js | ^2.95.3 | `frontend/lib/supabase.ts` |
| Charts | Recharts | ^3.7.0 | Dashboard page |
| Animation | Framer Motion | ^12.33.0 | Landing page, transitions |
| Icons | lucide-react | ^0.563.0 | Throughout app |
| Date | date-fns | ^4.1.0 | Date formatting/manipulation |
| Toast | Sonner | ^2.0.7 | `frontend/app/layout.tsx` |
| DnD (Core) | @dnd-kit/core | ^6.3.1 | Pipeline page |
| DnD (Sortable) | @dnd-kit/sortable | ^10.0.0 | Pipeline kanban |
| DnD (Utilities) | @dnd-kit/utilities | ^3.2.2 | DnD helper functions |
| Analytics | mixpanel-browser | ^2.74.0 | `AnalyticsProvider.tsx` |
| Error Tracking | @sentry/nextjs | ^10.38.0 | `next.config.js` |
| Onboarding | shepherd.js | ^14.5.1 | Onboarding tours |
| Date Picker | react-day-picker | ^9.13.0 | Search date selection |
| Progress Bar | nprogress | ^0.2.0 | Page transitions |
| Pull-to-Refresh | react-simple-pull-to-refresh | ^1.3.4 | Mobile UX |
| Debounce | use-debounce | ^10.1.0 | Search input debouncing |
| UUID | uuid | ^13.0.0 | Client-side ID generation |
| Testing | Jest | ^29.7.0 | `frontend/__tests__/` |
| Testing (React) | @testing-library/react | ^14.1.2 | Component tests |
| E2E Testing | Playwright | ^1.58.2 | `frontend/e2e-tests/` |
| Accessibility | @axe-core/playwright | ^4.11.1 | A11y E2E tests |
| Performance | @lhci/cli | ^0.15.0 | Lighthouse CI |
| Build | next-sitemap | ^4.2.3 | SEO sitemap generation |
| API Types | openapi-typescript | ^7.13.0 | Type generation from OpenAPI |
| PostCSS | postcss | ^8.5.6 | CSS processing |
| Node | >=18.0.0 | Required engine |

### 2.3 Infrastructure

| Service | Purpose |
|---|---|
| **Railway** | Backend (web + worker) + Frontend deployment |
| **Supabase Cloud** | PostgreSQL database, Auth (email + Google OAuth), Storage, RLS |
| **Redis** (Upstash/Railway) | Cache, SSE pub/sub, circuit breaker state, ARQ job queue |
| **Stripe** | Payment processing, subscription management, webhooks |
| **Resend** | Transactional email (welcome, quota, trial reminders) |
| **OpenAI** | GPT-4.1-nano for classification and summaries |
| **Sentry** | Error tracking (backend + frontend) |
| **Mixpanel** | Product analytics (frontend) |
| **Google Analytics** | Web analytics with LGPD compliance |
| **GitHub Actions** | CI/CD (16 workflow files) |

---

## 3. Folder Structure

### 3.1 Backend (`backend/`)

```
backend/
  main.py                       # FastAPI app entry point, lifespan, middleware, core endpoints
  config.py                     # Feature flags, CORS, logging, env validation, timeouts
  schemas.py                    # Pydantic request/response models
  schemas_lead_prospecting.py   # Lead prospecting schemas
  schemas_stats.py              # Statistics schemas
  search_pipeline.py            # 7-stage search pipeline (core business logic)
  search_context.py             # Mutable context dataclass for pipeline stages
  search_state_manager.py       # Search state machine (created/processing/completed/timed_out)
  search_cache.py               # Multi-level cache: Supabase > Redis > Local file
  consolidation.py              # Multi-source fetch orchestration + dedup
  pncp_client.py                # PNCP API client (sync + async + circuit breaker)
  pncp_client_resilient.py      # Resilient PNCP wrapper
  pncp_resilience.py            # PNCP-specific resilience patterns
  pncp_homologados_client.py    # PNCP homologados endpoint client
  filter.py                     # Keyword matching engine with density scoring
  filter_stats.py               # Per-filter rejection counters
  term_parser.py                # Search term parsing and normalization
  synonyms.py                   # Synonym expansion for search terms
  status_inference.py           # Bid status inference from dates/fields
  relevance.py                  # Relevance scoring and min-match calculation
  viability.py                  # 4-factor viability assessment (0-100 score)
  item_inspector.py             # Item-level inspection for gray-zone bids
  llm.py                        # GPT-4.1-nano summary generation
  llm_arbiter.py                # LLM classification (zero-match + uncertain zone)
  bid_analyzer.py               # Deep bid analysis service
  feedback_analyzer.py          # User feedback pattern analysis (bi-gram)
  excel.py                      # openpyxl Excel report generation
  report_generator.py           # Report generation orchestration
  google_sheets.py              # Google Sheets API integration
  storage.py                    # Supabase Storage upload (Excel files)
  auth.py                       # JWT validation (ES256/JWKS + HS256), token cache
  authorization.py              # Role-based access (admin, master)
  oauth.py                      # Google OAuth flow
  quota.py                      # Plan capabilities, monthly quota enforcement
  rate_limiter.py               # Redis token bucket rate limiter
  admin.py                      # Admin CRUD endpoints
  cache.py                      # InMemoryCache (LRU, 10K entries)
  redis_client.py               # Redis client utilities
  redis_pool.py                 # Redis connection pool + InMemoryCache fallback
  supabase_client.py            # Supabase admin client singleton
  progress.py                   # SSE progress tracker (Redis pub/sub or in-memory)
  job_queue.py                  # ARQ job queue (LLM + Excel background processing)
  cron_jobs.py                  # Periodic tasks (cache cleanup, session cleanup, trial reminders)
  worker_lifecycle.py           # Gunicorn worker lifecycle hooks
  email_service.py              # Resend transactional email service
  message_generator.py          # In-app message generation
  sectors.py                    # Sector loader from YAML
  sectors_data.yaml             # 15 sector definitions (keywords, exclusions, value ranges)
  exceptions.py                 # Custom exception hierarchy (PNCPAPIError, etc.)
  middleware.py                 # CorrelationID, SecurityHeaders, Deprecation middleware
  metrics.py                    # Prometheus metrics (histograms, counters, gauges)
  telemetry.py                  # OpenTelemetry tracing setup
  health.py                     # Health check utilities
  schema_contract.py            # Startup schema validation
  log_sanitizer.py              # PII masking (email, token, user ID, IP)
  analytics_events.py           # Analytics event definitions
  audit.py                      # Security audit logging
  database.py                   # SQLAlchemy database utilities (test compat)
  gunicorn_conf.py              # Gunicorn configuration with worker lifecycle
  locustfile.py                 # Load testing configuration
  seed_users.py                 # User seeding script
  contact_searcher.py           # Contact search utilities
  lead_prospecting.py           # Lead prospecting module
  lead_scorer.py                # Lead scoring algorithms
  lead_deduplicator.py          # Lead deduplication
  cli_acha_leads.py             # CLI tool for lead discovery
  receita_federal_client.py     # Receita Federal API client
  start.sh                      # Entrypoint: web (Gunicorn) or worker (ARQ) mode
  Dockerfile                    # Python 3.11-slim production image
  railway.toml                  # Railway deployment configuration
  railway-worker.toml           # Railway worker service configuration
  requirements.txt              # Production dependencies (32 packages, pinned)
  requirements-dev.txt          # Development dependencies
  pyproject.toml                # pytest, coverage, mypy, ruff configuration

  clients/                      # Multi-source procurement adapters
    base.py                     # Abstract SourceAdapter interface
    compras_gov_client.py       # ComprasGov v3 adapter
    portal_compras_client.py    # Portal de Compras Publicas v2 adapter
    portal_transparencia_client.py  # Portal Transparencia adapter
    querido_diario_client.py    # Querido Diario (municipal gazette) adapter
    licitar_client.py           # Licitar Digital adapter
    sanctions.py                # CEIS/CNEP sanctions registry client
    qd_extraction.py            # Querido Diario text extraction

  routes/                       # API endpoint modules (21 files)
    search.py                   # POST /buscar, GET /buscar-progress/{id} (SSE)
    user.py                     # GET /me, POST /change-password, PUT/GET /profile/context
    billing.py                  # POST /checkout, POST /billing-portal
    plans.py                    # GET /plans
    sessions.py                 # GET /sessions
    pipeline.py                 # CRUD /pipeline, GET /pipeline/alerts
    analytics.py                # GET /summary, /searches-over-time, /top-dimensions
    messages.py                 # CRUD /conversations, POST /{id}/reply
    feedback.py                 # POST/DELETE /feedback, GET /admin/feedback/patterns
    emails.py                   # Transactional email endpoints
    onboarding.py               # POST /first-analysis
    health.py                   # GET /health/cache
    features.py                 # Feature flag endpoints
    subscriptions.py            # Subscription management
    auth_oauth.py               # GET /google, /google/callback, DELETE /google
    auth_email.py               # Email confirmation recovery
    auth_check.py               # Email/phone pre-signup validation
    export_sheets.py            # Google Sheets export
    admin_trace.py              # GET /search-trace/{search_id}
    bid_analysis.py             # Deep bid analysis endpoints

  models/                       # Pydantic/dataclass models
    cache.py                    # SearchResultsCacheRow
    search_state.py             # SearchState enum and transitions
    stripe_webhook_event.py     # Stripe event dedup model
    user_subscription.py        # User subscription model

  services/                     # Business logic services
    base.py                     # Base service class
    billing.py                  # Stripe billing service
    exceptions.py               # Service-specific exceptions
    models.py                   # Service models
    sanctions_service.py        # Sanctions check orchestration
    trial_stats.py              # Trial statistics service

  webhooks/                     # Webhook handlers
    stripe.py                   # Stripe webhook (signature verification, event dedup)

  source_config/                # Data source configuration
    sources.py                  # Source health registry, source config loader

  unified_schemas/              # Cross-source unified data models
    unified.py                  # UnifiedProcurement schema

  utils/                        # Utility modules
    cnae_mapping.py             # CNAE (economic activity) code mapping
    date_parser.py              # Date parsing utilities
    disposable_emails.py        # Disposable email domain detection
    email_normalizer.py         # Email normalization
    error_reporting.py          # Centralized error emission
    ordenacao.py                # Result sorting algorithms
    phone_normalizer.py         # Phone number normalization

  templates/emails/             # Email HTML templates
    base.py                     # Base email template
    welcome.py                  # Welcome email
    billing.py                  # Billing-related emails
    quota.py                    # Quota warning/exhaustion emails
    trial.py                    # Trial reminder emails

  migrations/                   # Backend-specific SQL migrations (10 files)
  tests/                        # Test suite (214 entries)
  scripts/                      # Utility scripts
  docs/                         # Backend-specific documentation
  examples/                     # Example data/configurations
```

### 3.2 Frontend (`frontend/`)

```
frontend/
  app/                          # Next.js App Router
    page.tsx                    # Landing page (institutional, public)
    layout.tsx                  # Root layout: providers (Theme, Auth, Analytics, NProgress)
    globals.css                 # Global CSS with Tailwind + CSS custom properties
    error.tsx                   # Global error boundary
    global-error.tsx            # Root error boundary
    not-found.tsx               # 404 page
    types.ts                    # Shared TypeScript types
    api-types.generated.ts      # Auto-generated API types from OpenAPI
    sitemap.ts                  # Dynamic sitemap generator

    (protected)/                # Route group for authenticated pages
      layout.tsx                # Auth guard + AppHeader + Breadcrumbs

    buscar/                     # Core search page
      page.tsx                  # Main search interface
      error.tsx                 # Search error boundary
      components/               # 30 search-specific components
      hooks/                    # useSearch, useSearchFilters, useUfProgress
      utils/                    # dates.ts, reliability.ts

    dashboard/page.tsx          # User analytics dashboard
    historico/page.tsx          # Search history
    pipeline/page.tsx           # Opportunity pipeline (kanban)
    conta/page.tsx              # Account settings
    mensagens/page.tsx          # In-app messaging
    onboarding/page.tsx         # 3-step onboarding wizard
    planos/page.tsx             # Pricing/plans page
    planos/obrigado/page.tsx    # Post-purchase thank you
    login/page.tsx              # Login page
    signup/page.tsx             # Registration page
    admin/page.tsx              # Admin dashboard
    admin/cache/page.tsx        # Admin cache management
    ajuda/page.tsx              # Help/FAQ page
    features/page.tsx           # Feature showcase (marketing)
    pricing/page.tsx            # Alternative pricing page (marketing)
    termos/page.tsx             # Terms of service
    privacidade/page.tsx        # Privacy policy
    sobre/page.tsx              # About page
    recuperar-senha/page.tsx    # Password recovery
    redefinir-senha/page.tsx    # Password reset
    auth/callback/page.tsx      # OAuth callback handler
    blog/page.tsx               # Blog listing
    blog/[slug]/page.tsx        # Blog article (dynamic route)
    como-avaliar-licitacao/     # SEO content page
    como-evitar-prejuizo-licitacao/  # SEO content page
    como-filtrar-editais/       # SEO content page
    como-priorizar-oportunidades/   # SEO content page

    api/                        # 27 BFF API proxy routes
      buscar/route.ts           # POST proxy -> /v1/buscar
      buscar-progress/          # SSE progress streaming
      buscar-results/           # Search results fetch
      download/                 # Excel file download
      me/                       # User profile
      analytics/                # Usage analytics
      admin/                    # Admin API catch-all
      pipeline/                 # Pipeline CRUD
      sessions/                 # Search history
      search-history/           # Search history (alias)
      search-status/            # Search status polling
      setores/                  # Sector list
      feedback/                 # Feedback submission
      trial-status/             # Trial status check
      subscription-status/      # Subscription status
      subscriptions/            # Subscription management
      billing-portal/           # Stripe billing portal
      change-password/          # Password change
      profile-context/          # Onboarding context
      profile-completeness/     # Profile completion check
      first-analysis/           # First analysis endpoint
      messages/                 # Messaging
      health/                   # Frontend health
      export/                   # Google Sheets export
      auth/                     # Auth utilities
      bid-analysis/             # Deep bid analysis
      og/                       # Open Graph image generation

    components/                 # 48 shared components
      landing/                  # 12 landing page sections
      ui/                       # 6 reusable UI primitives
      (see Section 5.2 for full inventory)

    hooks/                      # App-level hooks
      useInView.ts              # Intersection Observer hook

  components/                   # Top-level shared components (outside app/)
    billing/                    # PaymentFailedBanner
    layout/                     # MobileMenu
    account/                    # Account management components
    subscriptions/              # Subscription management (7 components)
    NavigationShell.tsx         # Desktop sidebar + mobile bottom nav
    BackendStatusIndicator.tsx  # Backend health status
    BottomNav.tsx               # Mobile bottom navigation
    Sidebar.tsx                 # Desktop sidebar
    PageHeader.tsx              # Page header component
    EnhancedLoadingProgress.tsx # Enhanced loading with stages
    LoadingProgress.tsx         # Simple loading progress
    EmptyState.tsx              # Empty state display
    ErrorStateWithRetry.tsx     # Error with retry button
    AuthLoadingScreen.tsx       # Auth loading state
    ProfileCompletionPrompt.tsx # Profile completion nudge
    ProfileProgressBar.tsx      # Profile completion progress
    ProfileCongratulations.tsx  # Profile completion celebration
    GoogleSheetsExportButton.tsx # Google Sheets export
    MobileDrawer.tsx            # Mobile drawer component
    ModalidadeFilter.tsx        # Modality filter
    StatusFilter.tsx            # Status filter
    ValorFilter.tsx             # Value range filter

  lib/                          # Shared library modules
    supabase.ts                 # Supabase client (browser)
    supabase-server.ts          # Supabase client (server)
    serverAuth.ts               # Server-side token refresh
    fetchWithAuth.ts            # Authenticated fetch wrapper
    plans.ts                    # Plan definitions and utilities
    config.ts                   # Frontend configuration
    blog.ts                     # Blog utilities
    error-messages.ts           # Error message mapping
    proxy-error-handler.ts      # Proxy error sanitization
    savedSearches.ts            # Saved searches localStorage
    lastSearchCache.ts          # Last search result cache
    searchPartialCache.ts       # Partial search cache
    searchStatePersistence.ts   # Search state persistence
    constants/                  # Constant definitions
    copy/                       # Marketing copy
    data/                       # Static data
    icons/                      # Icon components
    animations/                 # Animation variants
    utils/                      # Utility functions
```

---

## 4. Backend Architecture

### 4.1 Module Dependency Graph

```
main.py (FastAPI app, lifespan, middleware, 22 router mounts)
  |
  +-- config.py (25+ feature flags, CORS, env validation, timeout chain)
  +-- middleware.py (CorrelationID, SecurityHeaders, Deprecation, RequestIDFilter)
  +-- telemetry.py (OpenTelemetry tracing, FastAPI/httpx instrumentation)
  +-- metrics.py (Prometheus: histograms, counters, gauges)
  +-- redis_pool.py (Redis pool lifecycle + InMemoryCache fallback)
  +-- schema_contract.py (startup schema validation)
  |
  +-- routes/search.py --> search_pipeline.py (7-stage pipeline)
  |     +-- search_context.py (mutable pipeline context)
  |     +-- search_state_manager.py (state machine: created/processing/completed)
  |     +-- pncp_client.py (PNCP API: PNCPClient + AsyncPNCPClient + CircuitBreaker)
  |     +-- consolidation.py (multi-source orchestration + dedup)
  |     +-- clients/*.py (6 source adapters + sanctions)
  |     +-- filter.py (keyword engine + density scoring + LLM integration)
  |     +-- filter_stats.py (per-filter rejection counters)
  |     +-- llm_arbiter.py (GPT-4.1-nano classification: uncertain + zero-match)
  |     +-- item_inspector.py (item-level inspection for gray-zone bids)
  |     +-- relevance.py (scoring, min-match, phrase matching)
  |     +-- viability.py (4-factor assessment: modality/timeline/value/geography)
  |     +-- term_parser.py (search term parsing, stopword removal)
  |     +-- synonyms.py (synonym expansion)
  |     +-- status_inference.py (bid status inference from dates)
  |     +-- llm.py (GPT-4.1-nano summaries + fallback)
  |     +-- excel.py (openpyxl report generation)
  |     +-- storage.py (Supabase Storage upload)
  |     +-- progress.py (SSE tracker: Redis pub/sub or asyncio.Queue)
  |     +-- search_cache.py (3-level: Supabase > Redis > Local file)
  |     +-- quota.py (plan capabilities, atomic quota increment)
  |     +-- job_queue.py (ARQ: enqueue LLM + Excel background jobs)
  |     +-- email_service.py (quota warning/exhaustion emails)
  |
  +-- routes/user.py (profile, password, trial status, profile context)
  +-- routes/billing.py (Stripe checkout, billing portal)
  +-- routes/plans.py (plan listing)
  +-- routes/sessions.py (search history)
  +-- routes/pipeline.py (opportunity pipeline CRUD + alerts)
  +-- routes/messages.py (in-app messaging conversations)
  +-- routes/analytics.py (usage analytics: summary, trends, dimensions)
  +-- routes/feedback.py (user feedback + admin pattern analysis)
  +-- routes/emails.py (transactional email endpoints)
  +-- routes/onboarding.py (first analysis after onboarding)
  +-- routes/health.py (cache health endpoint)
  +-- routes/features.py (feature flag management)
  +-- routes/subscriptions.py (subscription management)
  +-- routes/auth_oauth.py (Google OAuth: /google, /google/callback)
  +-- routes/auth_email.py (email confirmation recovery)
  +-- routes/auth_check.py (email/phone pre-signup validation)
  +-- routes/export_sheets.py (Google Sheets export)
  +-- routes/admin_trace.py (search trace for debugging)
  +-- routes/bid_analysis.py (deep bid analysis)
  +-- admin.py (admin CRUD endpoints)
  +-- webhooks/stripe.py (Stripe webhook handler)
  |
  +-- auth.py (JWT: ES256/JWKS + HS256, token cache with SHA256 keys)
  +-- authorization.py (role checks: admin, master)
  +-- rate_limiter.py (Redis token bucket: PNCP + PCP rate limiters)
  +-- supabase_client.py (service role admin client singleton)
  +-- log_sanitizer.py (PII masking: email, token, user ID, IP)
  +-- sectors.py + sectors_data.yaml (15 sector configurations)
  +-- exceptions.py (PNCPAPIError, PNCPRateLimitError, PNCPDegradedError)
  +-- cron_jobs.py (5 periodic tasks: cache/session cleanup, trial reminders, warmup)
```

### 4.2 API Versioning

The API uses a **dual-mount strategy** (defined in `main.py` lines 554-602):

- **Versioned:** All 22 routers mounted under `/v1/` prefix
- **Legacy:** Same 22 routers also mounted at root (no prefix) for backward compatibility
- **Deprecation:** `DeprecationMiddleware` adds RFC 8594 headers to legacy routes (`Sunset: 2026-06-01`)
- **Impact:** Doubles the route table size (~100+ endpoints total)

### 4.3 All Backend Modules (69 Python files)

| Category | Module | Purpose |
|---|---|---|
| **Entry** | `main.py` | FastAPI app, lifespan, middleware registration, core endpoints (/health, /setores) |
| **Entry** | `config.py` | 25+ feature flags, CORS config, env validation, timeout chain, retry config |
| **Entry** | `schemas.py` | Pydantic request/response models for all endpoints |
| **Entry** | `schemas_stats.py` | Statistics-specific Pydantic models |
| **Entry** | `schemas_lead_prospecting.py` | Lead prospecting Pydantic models |
| **Pipeline** | `search_pipeline.py` | 7-stage search pipeline (validate, prepare, execute, filter, enrich, output, persist) |
| **Pipeline** | `search_context.py` | Mutable dataclass shared across pipeline stages |
| **Pipeline** | `search_state_manager.py` | State machine for search lifecycle (created -> processing -> completed/timed_out) |
| **Data Sources** | `pncp_client.py` | PNCP API: sync PNCPClient, async AsyncPNCPClient, CircuitBreaker, ParallelFetchResult |
| **Data Sources** | `pncp_client_resilient.py` | Resilient PNCP wrapper with additional fallback logic |
| **Data Sources** | `pncp_resilience.py` | PNCP-specific resilience patterns (health canary, degraded mode) |
| **Data Sources** | `pncp_homologados_client.py` | PNCP homologados (awarded contracts) endpoint |
| **Data Sources** | `consolidation.py` | Multi-source fetch orchestration, priority-based dedup, ConsolidationResult |
| **Data Sources** | `clients/base.py` | Abstract SourceAdapter, SourceMetadata, SourceCapability, UnifiedProcurement |
| **Data Sources** | `clients/compras_gov_client.py` | ComprasGov v3 dual-endpoint adapter |
| **Data Sources** | `clients/portal_compras_client.py` | Portal de Compras Publicas v2 adapter |
| **Data Sources** | `clients/portal_transparencia_client.py` | Portal Transparencia adapter |
| **Data Sources** | `clients/querido_diario_client.py` | Querido Diario (municipal gazette) adapter |
| **Data Sources** | `clients/licitar_client.py` | Licitar Digital adapter |
| **Data Sources** | `clients/sanctions.py` | CEIS/CNEP sanctions registry check |
| **Data Sources** | `clients/qd_extraction.py` | Querido Diario text extraction |
| **Data Sources** | `source_config/sources.py` | Source health registry, config loader |
| **Filtering** | `filter.py` | Keyword matching, density scoring, stopwords, unicode normalization |
| **Filtering** | `filter_stats.py` | Per-filter rejection counters (transparency metrics) |
| **Filtering** | `term_parser.py` | Search term parsing, validation, multi-term support |
| **Filtering** | `synonyms.py` | Synonym expansion for Portuguese procurement terms |
| **Filtering** | `status_inference.py` | Bid status inference from dates and fields |
| **Filtering** | `relevance.py` | Relevance scoring, min-match calculation, phrase matching |
| **Filtering** | `item_inspector.py` | Item-level PNCP API inspection for gray-zone bids |
| **AI/LLM** | `llm.py` | GPT-4.1-nano executive summary generation + fallback heuristic |
| **AI/LLM** | `llm_arbiter.py` | LLM classification (uncertain zone 1-5% density + zero-match 0%) |
| **AI/LLM** | `viability.py` | 4-factor viability assessment (modality 30%, timeline 25%, value 25%, geography 20%) |
| **AI/LLM** | `bid_analyzer.py` | Deep bid analysis with structured LLM output |
| **AI/LLM** | `feedback_analyzer.py` | User feedback pattern analysis, bi-gram analysis |
| **Cache** | `search_cache.py` | 3-level cache: Supabase (24h) > Redis (4h) > Local file (24h) |
| **Cache** | `cache.py` | InMemoryCache (LRU, 10K entries, configurable TTL) |
| **Cache** | `redis_client.py` | Redis client utilities |
| **Cache** | `redis_pool.py` | Redis connection pool (20 max, 5s timeout) + InMemoryCache fallback |
| **Auth** | `auth.py` | JWT validation (ES256/JWKS + HS256), token cache (SHA256, 60s TTL) |
| **Auth** | `authorization.py` | Role-based access: admin, master, get_admin_ids |
| **Auth** | `oauth.py` | Google OAuth flow implementation |
| **Auth** | `quota.py` | Plan capabilities, monthly quota, atomic check+increment |
| **Auth** | `rate_limiter.py` | Redis token bucket rate limiter (PNCP + PCP instances) |
| **Billing** | `services/billing.py` | Stripe billing service |
| **Billing** | `services/trial_stats.py` | Trial statistics and metrics |
| **Billing** | `webhooks/stripe.py` | Stripe webhook (signature verify, event dedup, plan sync) |
| **Output** | `excel.py` | openpyxl styled Excel report generation |
| **Output** | `google_sheets.py` | Google Sheets API integration |
| **Output** | `report_generator.py` | Report generation orchestration |
| **Output** | `storage.py` | Supabase Storage file upload (signed URLs) |
| **Jobs** | `job_queue.py` | ARQ background processing (LLM summaries + Excel generation) |
| **Jobs** | `cron_jobs.py` | 5 periodic tasks: cache cleanup, session cleanup, cache refresh, trial reminders, warmup |
| **Jobs** | `worker_lifecycle.py` | Gunicorn worker lifecycle hooks (CRIT-034) |
| **Monitoring** | `metrics.py` | Prometheus: SEARCH_DURATION, FETCH_DURATION, CACHE_HITS, LLM_CALLS, etc. |
| **Monitoring** | `telemetry.py` | OpenTelemetry: TracerProvider, httpx + FastAPI instrumentation |
| **Monitoring** | `health.py` | Health check utilities |
| **Monitoring** | `audit.py` | Security audit event logging |
| **Monitoring** | `analytics_events.py` | Analytics event definitions |
| **Progress** | `progress.py` | SSE progress tracker: Redis pub/sub or in-memory asyncio.Queue |
| **Email** | `email_service.py` | Resend integration with retry (3x, exponential backoff) |
| **Email** | `message_generator.py` | In-app message generation |
| **Config** | `sectors.py` | YAML sector loader (15 sectors) |
| **Config** | `schema_contract.py` | Startup schema validation against expected columns |
| **Infra** | `middleware.py` | CorrelationID, SecurityHeaders, Deprecation middleware + RequestIDFilter |
| **Infra** | `log_sanitizer.py` | PII masking (email, token, user ID, IP, dict/string) |
| **Infra** | `exceptions.py` | PNCPAPIError, PNCPRateLimitError hierarchy |
| **Infra** | `supabase_client.py` | Supabase service role client singleton |
| **Infra** | `database.py` | SQLAlchemy utilities (test backward compat) |
| **Infra** | `gunicorn_conf.py` | Gunicorn configuration with worker hooks |
| **Leads** | `lead_prospecting.py`, `lead_scorer.py`, `lead_deduplicator.py`, `contact_searcher.py`, `cli_acha_leads.py` | Lead discovery subsystem (5 modules) |
| **External** | `receita_federal_client.py` | Receita Federal API client |
| **Unified** | `unified_schemas/unified.py` | Cross-source unified procurement schema |
| **Utils** | `utils/cnae_mapping.py`, `date_parser.py`, `disposable_emails.py`, `email_normalizer.py`, `error_reporting.py`, `ordenacao.py`, `phone_normalizer.py` | 7 utility modules |

### 4.4 Routes (21 modules, 50+ endpoints)

| Module | Key Endpoints | Purpose |
|---|---|---|
| `search.py` | `POST /buscar`, `GET /buscar-progress/{id}` (SSE), `GET /v1/search/{id}/status`, `POST /v1/search/{id}/retry` | Core search + real-time progress |
| `user.py` | `GET /me`, `POST /change-password`, `GET /trial-status`, `PUT/GET /profile/context` | User profile management |
| `billing.py` | `POST /checkout`, `POST /billing-portal`, `GET /subscription/status` | Stripe billing |
| `plans.py` | `GET /plans` | Plan catalog |
| `sessions.py` | `GET /sessions` | Search history |
| `pipeline.py` | `POST/GET/PATCH/DELETE /pipeline`, `GET /pipeline/alerts` | Opportunity pipeline CRUD |
| `analytics.py` | `GET /summary`, `/searches-over-time`, `/top-dimensions`, `/trial-value` | Usage analytics |
| `messages.py` | `POST/GET /conversations`, `POST /{id}/reply`, `PATCH /{id}/status` | In-app messaging |
| `feedback.py` | `POST/DELETE /feedback`, `GET /admin/feedback/patterns` | User feedback loop |
| `emails.py` | Transactional email endpoints | Email sending |
| `onboarding.py` | `POST /first-analysis` | First search after onboarding |
| `health.py` | `GET /health/cache` | Cache health metrics |
| `features.py` | Feature flag management | Runtime feature control |
| `subscriptions.py` | Subscription management | Plan changes |
| `auth_oauth.py` | `GET /google`, `/google/callback`, `DELETE /google` | Google OAuth |
| `auth_email.py` | Email confirmation recovery | Email verification |
| `auth_check.py` | Email/phone pre-signup validation | Duplicate detection |
| `export_sheets.py` | Google Sheets export | Data export |
| `admin_trace.py` | `GET /search-trace/{search_id}` | Search debugging |
| `bid_analysis.py` | Deep bid analysis | AI-powered bid analysis |
| `admin.py` (not in routes/) | Admin CRUD | User management |

---

## 5. Frontend Architecture

### 5.1 Pages (29 pages across App Router)

| Route | Purpose | Auth Required |
|---|---|---|
| `/` | Landing page (institutional, SEO-optimized) | No |
| `/login` | Login page | No |
| `/signup` | Registration page | No |
| `/auth/callback` | OAuth callback handler | No |
| `/recuperar-senha` | Password recovery request | No |
| `/redefinir-senha` | Password reset form | No |
| `/onboarding` | 3-step wizard (CNAE, UFs, Confirmation) | Yes |
| `/buscar` | **Core search page** -- filters, results, SSE progress | Yes |
| `/dashboard` | User analytics dashboard with Recharts charts | Yes |
| `/historico` | Search history with session details | Yes |
| `/pipeline` | Opportunity pipeline (kanban with @dnd-kit) | Yes |
| `/mensagens` | In-app messaging system | Yes |
| `/conta` | Account settings and profile | Yes |
| `/planos` | Pricing/plans page | Yes |
| `/planos/obrigado` | Post-purchase thank you | Yes |
| `/admin` | Admin dashboard | Yes (admin) |
| `/admin/cache` | Admin cache management | Yes (admin) |
| `/pricing` | Marketing pricing page | No |
| `/features` | Feature showcase (marketing) | No |
| `/ajuda` | Help center/FAQ | No |
| `/termos` | Terms of service | No |
| `/privacidade` | Privacy policy | No |
| `/sobre` | About page | No |
| `/blog` | Blog listing | No |
| `/blog/[slug]` | Blog article (dynamic) | No |
| `/como-avaliar-licitacao` | SEO content page | No |
| `/como-evitar-prejuizo-licitacao` | SEO content page | No |
| `/como-filtrar-editais` | SEO content page | No |
| `/como-priorizar-oportunidades` | SEO content page | No |

### 5.2 Component Inventory (80+ components)

**Search UI (`app/buscar/components/` -- 30 components):**
- `SearchForm.tsx` -- Main search form (UFs, dates, sector, terms)
- `SearchResults.tsx` -- Results list with pagination
- `FilterPanel.tsx` -- Advanced filter sidebar
- `UfProgressGrid.tsx` -- Real-time UF fetch progress grid
- `CacheBanner.tsx` -- Cached results indicator
- `DegradationBanner.tsx` -- Source degradation warning
- `PartialResultsPrompt.tsx` -- Partial results notification
- `SourcesUnavailable.tsx` -- All sources failed state
- `ErrorDetail.tsx` -- Detailed error information
- `SearchErrorBanner.tsx` -- Search error display
- `SearchErrorBoundary.tsx` -- React error boundary for search
- `LlmSourceBadge.tsx` -- LLM classification source indicator
- `ViabilityBadge.tsx` -- Viability score badge (alta/media/baixa)
- `CompatibilityBadge.tsx` -- Compatibility indicator
- `ReliabilityBadge.tsx` -- Data reliability indicator
- `FeedbackButtons.tsx` -- Thumbs up/down feedback
- `FreshnessIndicator.tsx` -- Cache freshness display
- `CoverageBar.tsx` -- UF coverage progress bar
- `FilterStatsBreakdown.tsx` -- Filter statistics display
- `FilterRelaxedBanner.tsx` -- Relaxed filter notification
- `DataQualityBanner.tsx` -- Data quality indicator
- `ExpiredCacheBanner.tsx` -- Expired cache warning
- `OperationalStateBanner.tsx` -- Operational state display
- `PartialTimeoutBanner.tsx` -- Partial timeout warning
- `RefreshBanner.tsx` -- Cache refresh prompt
- `TruncationWarningBanner.tsx` -- Truncated results warning
- `UfFailureDetail.tsx` -- Per-UF failure details
- `ZeroResultsSuggestions.tsx` -- Suggestions when no results
- `ActionLabel.tsx` -- Action label component
- `DeepAnalysisModal.tsx` -- Deep bid analysis modal

**Shared Components (`app/components/` -- 48 components):**
- `AppHeader.tsx` -- Authenticated page header
- `UserMenu.tsx` -- User dropdown with plan/quota info
- `Footer.tsx` -- Site-wide footer
- `Breadcrumbs.tsx` -- Navigation breadcrumbs
- `ThemeProvider.tsx` -- Dark/light theme (localStorage persistence)
- `ThemeToggle.tsx` -- Theme switch button
- `AuthProvider.tsx` -- Supabase auth context
- `AnalyticsProvider.tsx` -- Mixpanel tracking context
- `NProgressProvider.tsx` -- Page transition progress bar
- `CookieConsentBanner.tsx` -- LGPD consent banner
- `SessionExpiredBanner.tsx` -- Re-auth prompt
- `StructuredData.tsx` -- Schema.org JSON-LD
- `GoogleAnalytics.tsx` -- GA4 with consent gating
- `RegionSelector.tsx` -- UF multi-select with region grouping
- `CustomDateInput.tsx` -- Date range picker
- `CustomSelect.tsx` -- Sector dropdown
- `EsferaFilter.tsx` -- Government sphere filter
- `OrgaoFilter.tsx` -- Agency name filter
- `MunicipioFilter.tsx` -- Municipality filter
- `OrdenacaoSelect.tsx` -- Sort order selector
- `PaginacaoSelect.tsx` -- Items per page selector
- `SavedSearchesDropdown.tsx` -- Saved search management
- `LoadingProgress.tsx` -- SSE-powered progress bar
- `LoadingResultsSkeleton.tsx` -- Results loading skeleton
- `LicitacaoCard.tsx` -- Individual bid result card
- `LicitacoesPreview.tsx` -- Results preview (blurred for free)
- `EmptyState.tsx` -- No results guidance
- `AddToPipelineButton.tsx` -- Add bid to pipeline
- `PipelineAlerts.tsx` -- Deadline alert badges
- `PlanBadge.tsx` -- Current plan indicator
- `QuotaBadge.tsx` -- Quota usage indicator
- `QuotaCounter.tsx` -- Detailed quota display
- `UpgradeModal.tsx` -- Plan upgrade dialog
- `TrialConversionScreen.tsx` -- Trial expiration CTA
- `TrialCountdown.tsx` -- Trial days remaining
- `TrialExpiringBanner.tsx` -- Trial expiring warning
- `MessageBadge.tsx` -- Unread message count
- `StatusBadge.tsx` -- Status indicator
- `Countdown.tsx` -- Timer countdown
- `Dialog.tsx` -- Modal dialog
- `ContentPageLayout.tsx` -- Content page layout
- `BlogArticleLayout.tsx` -- Blog article layout
- `InstitutionalSidebar.tsx` -- Marketing sidebar
- `ValuePropSection.tsx` -- Value proposition section

**Landing Page (`app/components/landing/` -- 12 components):**
- `LandingNavbar.tsx`, `HeroSection.tsx`, `OpportunityCost.tsx`, `BeforeAfter.tsx`, `DifferentialsGrid.tsx`, `HowItWorks.tsx`, `StatsSection.tsx`, `DataSourcesSection.tsx`, `SectorsGrid.tsx`, `ProofOfValue.tsx`, `FinalCTA.tsx`, `TrustCriteria.tsx`, `AnalysisExamplesCarousel.tsx`

**UI Primitives (`app/components/ui/` -- 6 components):**
- `BentoGrid.tsx`, `CategoryBadge.tsx`, `GlassCard.tsx`, `GradientButton.tsx`, `ScoreBar.tsx`, `Tooltip.tsx`

**Top-Level Components (`components/` -- 22 components):**
- `NavigationShell.tsx` -- Desktop sidebar + mobile bottom nav
- `BackendStatusIndicator.tsx` -- Backend health status
- `BottomNav.tsx` -- Mobile bottom navigation
- `Sidebar.tsx` -- Desktop sidebar
- `billing/PaymentFailedBanner.tsx` -- Failed payment warning
- `subscriptions/` -- 7 subscription management components (CancelSubscriptionModal, PlanCard, PlanToggle, FeatureBadge, AnnualBenefits, DowngradeModal, TrustSignals)

### 5.3 API Proxy Layer (BFF Pattern)

The frontend uses **27 Next.js API routes** as a Backend-for-Frontend proxy layer. Each route:
1. Extracts the auth token (server-side refresh via `getRefreshedToken()` or header fallback)
2. Forwards the request to the backend API at the configured `NEXT_PUBLIC_API_URL`
3. Sanitizes errors via `proxy-error-handler.ts` before returning to the client
4. Returns Portuguese-language error messages for user-facing errors

### 5.4 State Management

- **No external state library** -- React `useState`/`useEffect`/`useRef` hooks only
- **Custom hooks:**
  - `useSearch.ts` -- Search execution, SSE connection, result management
  - `useSearchFilters.ts` -- Filter state management (UFs, dates, sector, modalities, values)
  - `useUfProgress.ts` -- Per-UF real-time progress tracking
  - `useInView.ts` -- Intersection Observer for lazy loading
- **Server-side auth:** `@supabase/ssr` with `getAll/setAll` cookie pattern in `middleware.ts`
- **localStorage:**
  - `smartlic-theme` -- Theme preference (dark/light/system)
  - `smartlic-onboarding-completed` -- Onboarding completion flag
  - `smartlic-profile-context` -- Cached profile context
  - Plan cache (1hr TTL) -- Prevents UI plan downgrades during Supabase outages
  - Saved searches, last search cache, partial search cache
- **SSE:** Dual-connection pattern (`GET /buscar-progress/{search_id}` + `POST /buscar`)

### 5.5 Build and Output

- `output: 'standalone'` in `next.config.js` for Docker/Railway deployment
- Custom `postbuild` script: `next-sitemap && cp -r public .next/standalone/ && cp -r .next/static .next/standalone/.next/`
- Dynamic build IDs: `build-${Date.now()}-${random}` to prevent stale cache issues
- Sentry source map upload via `@sentry/nextjs` wrapper with `tunnelRoute: "/monitoring"`
- Security headers: CSP, HSTS, X-Frame-Options, X-Content-Type-Options (via `next.config.js`)

---

## 6. Data Flow: Search Pipeline

### 6.1 High-Level Flow

```
User (Next.js)
  |
  +--> POST /api/buscar (Next.js BFF proxy)
  |      |
  |      +--> POST /v1/buscar (FastAPI backend)
  |             |
  |             +-- Stage 1: ValidateRequest
  |             |     - Input validation (Pydantic)
  |             |     - Auth check (JWT)
  |             |     - Quota check (atomic increment)
  |             |     - Plan resolution
  |             |
  |             +-- Stage 2: PrepareSearch
  |             |     - Term parsing (stopwords, normalization)
  |             |     - Sector config loading (YAML)
  |             |     - Query parameter construction
  |             |     - Cache key generation (MD5)
  |             |
  |             +-- Stage 3: ExecuteSearch
  |             |     - Check cache (Supabase > Redis > Local)
  |             |     - If MISS: Parallel multi-source fetch
  |             |       +-- PNCP API (priority 1)
  |             |       |     - Phased UF batching (5 UFs/batch, 2s delay)
  |             |       |     - Per-modality parallel fetch (4 modalities)
  |             |       |     - Circuit breaker protection
  |             |       |     - Rate limiting (10 req/s)
  |             |       +-- PCP v2 API (priority 2)
  |             |       +-- ComprasGov v3 (priority 3)
  |             |     - Consolidation + priority-based dedup
  |             |     - Early return if >80% UFs responded after 80s
  |             |
  |             +-- Stage 4: FilterResults
  |             |     1. UF check (fastest, fail-fast)
  |             |     2. Value range check
  |             |     3. Max contract value (sector ceiling)
  |             |     4. Red flag keywords
  |             |     5. Keyword matching + density scoring
  |             |        - density > 5%: Auto-ACCEPT
  |             |        - 2-5%: LLM standard prompt
  |             |        - 1-2%: LLM conservative prompt
  |             |        - < 1%: Auto-REJECT
  |             |     6. Zero-match LLM (0% density, GPT-4.1-nano YES/NO)
  |             |     7. Item inspection (gray zone, 0-5% density)
  |             |     8. Status/deadline validation
  |             |
  |             +-- Stage 5: EnrichResults
  |             |     - Relevance scoring
  |             |     - Viability assessment (4 factors, 0-100 score)
  |             |     - Status inference
  |             |     - Sorting (by viability, relevance, value, date)
  |             |
  |             +-- Stage 6: GenerateOutput
  |             |     - LLM executive summary (GPT-4.1-nano or fallback)
  |             |     - Excel report generation (openpyxl)
  |             |     - Dispatched via ARQ job queue (background)
  |             |     - Immediate fallback response if queue unavailable
  |             |
  |             +-- Stage 7: Persist
  |                   - Save session to Supabase
  |                   - Save to cache (Supabase > Redis > Local)
  |                   - Build BuscaResponse
  |                   - Emit final SSE event
  |
  +--> GET /api/buscar-progress/{id} (SSE stream)
         |
         +--> GET /v1/buscar-progress/{id} (SSE)
                - Stage events: connecting, fetching, filtering, llm, excel, complete
                - Detail: per-UF progress, per-source status
                - Events: llm_ready, excel_ready (from ARQ jobs)
                - Fallback: time-based simulation if SSE fails
```

### 6.2 Timeout Chain (strict decreasing)

```
Frontend Proxy (110s PIPELINE_TIMEOUT aligned) >
  Pipeline (110s PIPELINE_TIMEOUT) >
    Consolidation (100s CONSOLIDATION_TIMEOUT) >
      Per-Source (80s PNCP_TIMEOUT_PER_SOURCE) >
        Per-UF (30s PNCP_TIMEOUT_PER_UF, 15s degraded) >
          Per-Modality (20s PNCP_TIMEOUT_PER_MODALITY) >
            HTTP request (10s httpx timeout)
```

Additional time-based safeguards:
- `PIPELINE_SKIP_LLM_AFTER_S=90`: Skip LLM calls if pipeline already running 90s+
- `PIPELINE_SKIP_VIABILITY_AFTER_S=100`: Skip viability if running 100s+
- `EARLY_RETURN_THRESHOLD_PCT=0.8`: Return partial results when 80% UFs responded
- `EARLY_RETURN_TIME_S=80.0`: After 80s, return whatever is available

### 6.3 Fallback Cascade

```
Live search (all sources) -->
  Partial results (some UFs/sources failed) -->
    Fresh cache (0-6h, serve directly) -->
      Stale cache (6-24h, serve + background refresh) -->
        Expired cache (>24h, last resort when allow_expired=True) -->
          Empty response with degradation reason
```

---

## 7. Database Architecture

### 7.1 Supabase PostgreSQL Schema

**43 migrations** in `supabase/migrations/` (35 numbered 001-033 + 8 timestamped 20260220-20260224).

| Table | Migration | Purpose | RLS |
|---|---|---|---|
| `profiles` | 001 | User profiles (extends `auth.users`): full_name, plan_type, is_admin, is_master | Yes |
| `plans` | 001 | Plan catalog (free_trial, consultor_agil, maquina, sala_guerra) | No |
| `user_subscriptions` | 001 | Active subscriptions, Stripe refs, billing period | Yes |
| `search_sessions` | 001, 20260220, 20260221 | Search history: params, results count, status, error_message, search_id | Yes |
| `monthly_quota` | 002 | Monthly search usage tracking (quota_used, month_year) | Yes |
| `plan_features` | 009 | Feature flags per plan (boolean capabilities) | No |
| `stripe_webhook_events` | 010 | Idempotent webhook processing (event dedup by event_id) | No* |
| `messages_conversations` | 012 | In-app support conversations (subject, status) | Yes |
| `messages_messages` | 012 | Individual messages in threads (content, sender_type) | Yes |
| `google_oauth_tokens` | 013 | OAuth refresh tokens for Google integration | Yes |
| `google_sheets_exports` | 014 | Google Sheets export history (spreadsheet_id, title) | Yes |
| `audit_events` | 023 | Security audit log (event_type, actor_id, details) | No |
| `profile_context` | 024 | Onboarding business context (JSONB: cnae, ufs, sectors) | Yes |
| `pipeline_items` | 025 | Opportunity pipeline (status, notes, user_id+pncp_id unique) | Yes |
| `search_results_cache` | 026-033 | Cached search results (cache_key, data, sources, priority, access_count) | No |
| `search_state_transitions` | 20260221 | Search state machine audit trail | Yes |
| `trial_email_log` | 20260224 | Trial reminder email tracking (prevent duplicates) | No |

### 7.2 Key Relationships

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
  |     |-- profile_context (1:1)
  |     |-- search_state_transitions (1:many)
  |     +-- trial_email_log (1:many)
  |
  +-- plans (referenced by user_subscriptions.plan_id and profiles.plan_type)
```

### 7.3 Database Functions and Triggers

| Function | Purpose |
|---|---|
| `handle_new_user()` | Auto-create profile on signup (trigger on auth.users INSERT) |
| `increment_quota_atomic()` | Atomic quota increment with limit check |
| `check_and_increment_quota()` | Combined check+increment (TOCTOU prevention) |
| `increment_existing_quota()` | Fallback atomic increment for existing rows |
| `sync_plan_type_on_subscription()` | Keep profiles.plan_type in sync with subscriptions (trigger) |
| `update_pipeline_updated_at()` | Auto-update pipeline_items.updated_at (trigger) |
| `get_table_columns_simple()` | RPC for startup schema validation |

### 7.4 Backend Migrations (10 files)

`backend/migrations/` contains migrations managed by the backend directly (not through Supabase CLI):
- 002: Monthly quota schema
- 003: Atomic quota increment
- 004-005: Google OAuth tokens and Sheets exports
- 006: Classification feedback
- 007-010: Search session lifecycle, state transitions, search_id, array normalization

---

## 8. External Integrations

### 8.1 PNCP API (Priority 1 -- Primary Data Source)

| Attribute | Value |
|---|---|
| Base URL | `https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao` |
| Auth | None (public API) |
| Max Page Size | **50** (reduced from 500 in Feb 2026; >50 returns HTTP 400 silently) |
| Rate Limit | 10 req/s (self-imposed) |
| Retry | 3 attempts, exponential backoff (1.5s base, 15s max) |
| Circuit Breaker | 15 failures threshold, 60s cooldown |
| UF Batching | 5 UFs per batch, 2s delay between batches |
| Per-UF Timeout | 30s normal, 15s degraded mode |
| Per-Modality Timeout | 20s |
| Modalities Queried | 4 (Concorrencia Eletronica), 5 (Presencial), 6 (Pregao Eletronico), 7 (Presencial) |
| Excluded Modalities | 9 (Inexigibilidade), 14 (Inaplicabilidade) |
| Health Canary | `tamanhoPagina=10` probe before full search |
| Retryable Codes | 408, 422, 429, 500, 502, 503, 504 |

### 8.2 PCP v2 API (Priority 2 -- Secondary)

| Attribute | Value |
|---|---|
| Base URL | `https://compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos` |
| Auth | None (fully public) |
| Pagination | Fixed 10/page (`pageCount`/`nextPage`) |
| UF Filtering | Client-side only (no server-side param) |
| Value Data | Not available (`valor_estimado=0.0`) |
| Circuit Breaker | 30 failures threshold, 120s cooldown |

### 8.3 ComprasGov v3 API (Priority 3 -- Tertiary)

| Attribute | Value |
|---|---|
| Base URL | `https://dadosabertos.compras.gov.br` |
| Endpoints | Dual: legacy + Lei 14.133 |

### 8.4 OpenAI (GPT-4.1-nano)

| Use Case | Model | Max Tokens | Temperature | Cost |
|---|---|---|---|---|
| LLM Arbiter (classification) | gpt-4.1-nano | 1 (binary) or 150 (structured) | 0 | ~R$0.00003-0.00007/call |
| Executive Summary | gpt-4.1-nano | 500-1200 | 0.3 | ~R$0.005/summary |
| Deep Bid Analysis | gpt-4.1-nano | Variable | 0.3 | Variable |

- **Structured output:** When `LLM_STRUCTURED_OUTPUT_ENABLED=true`, returns JSON with confidence (0-100), evidence, rejection reason
- **Fallback:** `gerar_resumo_fallback()` generates heuristic summary without API call
- **Cache:** In-memory MD5-based cache for repeated LLM decisions
- **ThreadPoolExecutor:** max_workers=10 for parallel LLM calls

### 8.5 Stripe

| Attribute | Value |
|---|---|
| Webhook Endpoint | `POST /v1/webhooks/stripe` |
| Events Handled | `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_succeeded`, `invoice.payment_failed` |
| Security | Signature verification via `STRIPE_WEBHOOK_SECRET` |
| Idempotency | Event dedup via `stripe_webhook_events` table |
| Plan Sync | Updates `profiles.plan_type` on every webhook |
| Grace Period | 3-day subscription gap grace (`SUBSCRIPTION_GRACE_DAYS`) |
| Proration | Handled automatically by Stripe (no custom code) |

### 8.6 Supabase

- **Database:** PostgreSQL with RLS on all user-facing tables
- **Auth:** Email/password + Google OAuth (ES256 JWT with JWKS)
- **Storage:** Excel file upload for signed URL download
- **Client:** Service role key (admin privileges) in `supabase_client.py`
- **RPC:** Custom functions via `db.rpc()` (schema validation, quota increment)

### 8.7 Redis

- **Connection Pool:** 20 max connections, 5s timeout via `redis_pool.py`
- **Fallback:** `InMemoryCache` (LRU, 10K entries) when Redis unavailable
- **Uses:**
  - Search result cache (L2, 4h TTL by priority: HOT=2h, WARM=6h, COLD=1h)
  - SSE progress pub/sub (cross-instance event sharing)
  - Circuit breaker state persistence (cross-restart survival)
  - ARQ job queue backend (LLM + Excel background jobs)
  - Rate limiter token buckets (PNCP + PCP)
  - Feature flag cache

### 8.8 Resend (Transactional Email)

| Email Type | Template | Trigger |
|---|---|---|
| Welcome | `templates/emails/welcome.py` | New user signup |
| Quota Warning (80%) | `templates/emails/quota.py` | 80% quota usage |
| Quota Exhausted (100%) | `templates/emails/quota.py` | 100% quota usage |
| Trial Reminder | `templates/emails/trial.py` | 3 days before trial expiry |
| Billing | `templates/emails/billing.py` | Payment events |

- **Fire-and-forget:** Never blocks the caller (threading-based async)
- **Retry:** 3 attempts with exponential backoff
- **Feature flag:** `EMAIL_ENABLED` can disable all sending (dev mode)

### 8.9 Other Integrations

| Integration | Client Module | Status |
|---|---|---|
| Portal Transparencia | `clients/portal_transparencia_client.py` | Adapter exists, varying maturity |
| Querido Diario | `clients/querido_diario_client.py` | Adapter exists |
| Licitar Digital | `clients/licitar_client.py` | Adapter exists |
| BLL/BNC | Referenced in health endpoint | Adapters planned |
| CEIS/CNEP Sanctions | `clients/sanctions.py` | Production (STORY-256) |
| Receita Federal | `receita_federal_client.py` | Discovery/experimental |
| Google Sheets | `google_sheets.py` | Production (STORY-180) |
| Google Analytics | Frontend `GoogleAnalytics.tsx` | Production (LGPD-gated) |
| Mixpanel | Frontend `AnalyticsProvider.tsx` | Production |

---

## 9. Infrastructure and Deployment

### 9.1 Railway Deployment Architecture

```
Railway Project
  |
  +-- Service: smartlic-backend (web)
  |     - Dockerfile: backend/Dockerfile (Python 3.11-slim)
  |     - Entry: start.sh with PROCESS_TYPE=web
  |     - Process: Gunicorn + UvicornWorker
  |     - Workers: 2 (WEB_CONCURRENCY=2, Railway 1GB limit)
  |     - Timeout: 120s (GUNICORN_TIMEOUT)
  |     - Max Requests: 1000 + jitter 50 (memory leak prevention)
  |     - Keep-Alive: 75s (> Railway proxy 60s)
  |     - Health: GET /health/ready (300s timeout)
  |     - Overlap: 45s (zero-downtime deploys)
  |     - Drain: 120s (in-flight request completion)
  |     - Restart: ON_FAILURE, max 10 retries
  |
  +-- Service: smartlic-worker
  |     - Same Dockerfile, PROCESS_TYPE=worker
  |     - Process: ARQ worker (arq job_queue.WorkerSettings)
  |     - Restart: Loop with 5s delay, max 10 restarts
  |     - Jobs: LLM summaries, Excel generation, cache refresh
  |
  +-- Service: smartlic-frontend
        - Next.js standalone output
        - Entry: node .next/standalone/server.js
        - Build: next build && next-sitemap && copy static assets
```

### 9.2 CI/CD (GitHub Actions -- 16 workflows)

| Workflow | File | Trigger | Purpose |
|---|---|---|---|
| Backend Tests | `backend-tests.yml` | push/PR | pytest (exit 0 required for merge) |
| Backend CI | `backend-ci.yml` | push/PR | Backend-specific CI pipeline |
| Frontend Tests | `frontend-tests.yml` | push/PR | npm test (exit 0 required for merge) |
| E2E Tests | `e2e.yml` | push/PR | Playwright E2E tests |
| Combined Tests | `tests.yml` | push/PR | Backend + Frontend + Integration |
| Deploy | `deploy.yml` | push to main | Production deployment |
| Staging | `staging-deploy.yml` | push to develop | Staging deployment |
| PR Validation | `pr-validation.yml` | PR | PR quality checks |
| CodeQL | `codeql.yml` | schedule/PR | Security analysis |
| Lighthouse | `lighthouse.yml` | PR | Performance audit |
| Load Test | `load-test.yml` | manual | Locust load testing |
| Migration Check | `migration-check.yml` | PR (supabase/) | Verify migrations applied to production |
| Sync Sectors | `sync-sectors.yml` | schedule | Frontend sector fallback sync |
| Cleanup | `cleanup.yml` | schedule | Artifact cleanup |
| Dependabot Auto-Merge | `dependabot-auto-merge.yml` | PR | Auto-merge minor dependency updates |
| Docs | `README.md` | -- | Workflow documentation |

### 9.3 Docker

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["/app/start.sh"]
```

---

## 10. Key Architectural Patterns

### 10.1 Multi-Source Pipeline with Priority Dedup

Three data sources fetched in parallel, deduplicated by `numeroControlePNCP` or constructed composite key. Priority-based: PNCP (1) wins over PCP (2) which wins over ComprasGov (3). The `consolidation.py` module tracks per-source metrics (record count, duration, errors).

### 10.2 Two-Level Cache with SWR (Stale-While-Revalidate)

```
L1: Redis/InMemoryCache (4h TTL, priority-based: HOT=2h, WARM=6h, COLD=1h)
  - Proactive classification: access_count + recent_access determine priority
  - In-memory LRU (10K entries) when Redis unavailable

L2: Supabase search_results_cache (24h TTL, persistent across restarts)
  - Fresh (0-6h): Serve directly
  - Stale (6-24h): Serve + trigger background revalidation
  - Expired (>24h): Only served as last resort (allow_expired=True)

L3: Local file cache (/tmp/smartlic_cache, 24h TTL)
  - Emergency fallback when both Supabase and Redis fail
```

Background revalidation: max 3 concurrent, 180s timeout, 600s cooldown per key.

### 10.3 LLM Classification Pipeline

```
Contract description -> Keyword matching -> Density calculation
  |
  +-- density > 5%: AUTO-ACCEPT (high confidence, no LLM cost)
  +-- 2% < density <= 5%: LLM standard prompt (GPT-4.1-nano)
  +-- 1% <= density <= 2%: LLM conservative prompt + examples
  +-- density < 1% and > 0%: AUTO-REJECT (low confidence)
  +-- density == 0%: LLM zero-match classification (sector-aware YES/NO)

When LLM_STRUCTURED_OUTPUT_ENABLED=true:
  Returns: { classe: SIM/NAO, confianca: 0-100, evidencias: [...], motivo_exclusao: str }
  Enables: re-ranking by confidence, audit trail
```

Fallback: On LLM failure, always REJECT (zero noise philosophy).

### 10.4 SSE Progress Tracking

```
Frontend:
  1. Generate search_id (UUID)
  2. Open SSE: GET /api/buscar-progress/{search_id}
  3. Fire search: POST /api/buscar (includes search_id)
  4. Receive events: connecting(5%), fetching(10-50%), filtering(60%), llm(70%), excel(80%), complete(100%)
  5. Late events: llm_ready, excel_ready (from ARQ worker)

Backend:
  - ProgressTracker (progress.py): asyncio.Queue per search_id
  - Redis pub/sub mode: events shared across instances
  - In-memory mode: single-instance only (default fallback)
  - Events include: trace_id, search_id, request_id for correlation
```

### 10.5 ARQ Job Queue (Background Processing)

```
Web process:
  enqueue_job("llm_summary_job", search_id, bids_data) -> Redis
  enqueue_job("excel_generation_job", search_id, bids_data) -> Redis

Worker process:
  arq job_queue.WorkerSettings
  - Processes LLM summaries and Excel generation in background
  - Results communicated via SSE events (llm_ready, excel_ready)
  - Worker liveness check: 15s interval, automatic failover to inline execution

Fallback:
  If Redis/ARQ unavailable -> is_queue_available() returns False
  -> Pipeline executes LLM/Excel inline (zero regression)
```

### 10.6 Circuit Breaker (PNCP + PCP)

```
States: CLOSED -> OPEN (after threshold failures) -> HALF_OPEN (after cooldown)

PNCP: 15 failures threshold, 60s cooldown
PCP: 30 failures threshold, 120s cooldown

Degraded mode (OPEN/HALF_OPEN):
  - Reduced concurrency (fewer parallel UFs)
  - Shorter timeouts (15s per UF instead of 30s)
  - UF priority ordering by population
  - State persisted in Redis (survives restarts)
```

### 10.7 Viability Assessment

Four-factor deterministic scoring (no LLM, pure rules):

| Factor | Weight | Scoring Basis |
|---|---|---|
| Modalidade | 30% | Procurement modality accessibility (Pregao Eletronico=100, Inexigibilidade=0) |
| Timeline | 25% | Days until proposal deadline (>30d=100, <3d=20, past=0) |
| Value Fit | 25% | Bid value vs sector ideal range from `sectors_data.yaml` |
| Geography | 20% | Proximity to user's search UFs |

Result: 0-100 score mapped to levels -- Alta (>70), Media (40-70), Baixa (<40).

---

## 11. Configuration and Feature Flags

### 11.1 Environment Variables (Key Groups)

| Group | Variables | Purpose |
|---|---|---|
| **Database** | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET` | Required (fatal in production if missing) |
| **AI** | `OPENAI_API_KEY` | LLM classification and summaries |
| **Payments** | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` | Billing |
| **Cache** | `REDIS_URL` | Optional, graceful degradation |
| **Email** | `RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_ENABLED` | Transactional email |
| **Google** | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | OAuth + Sheets |
| **Monitoring** | `SENTRY_DSN`, `METRICS_TOKEN` | Error tracking, metrics |
| **Timeouts** | `PIPELINE_TIMEOUT`, `CONSOLIDATION_TIMEOUT`, `PNCP_TIMEOUT_PER_SOURCE`, `PNCP_TIMEOUT_PER_UF` | Timeout chain |
| **Server** | `PORT`, `ENVIRONMENT`, `LOG_LEVEL`, `LOG_FORMAT`, `WEB_CONCURRENCY`, `GUNICORN_TIMEOUT` | Runtime config |
| **CORS** | `CORS_ORIGINS` | Allowed origins |
| **Trial** | `TRIAL_DURATION_DAYS` (default 7) | Trial configuration |

### 11.2 Feature Flags (25+ flags)

All managed via environment variables with in-memory TTL cache (60s). Runtime-reloadable via `POST /v1/admin/feature-flags/reload`.

| Flag | Default | Purpose |
|---|---|---|
| `ENABLE_NEW_PRICING` | true | Plan-based capabilities and quota enforcement |
| `LLM_ARBITER_ENABLED` | true | LLM classification for uncertain-zone bids |
| `LLM_ZERO_MATCH_ENABLED` | true | LLM classification for 0% keyword density bids |
| `LLM_STRUCTURED_OUTPUT_ENABLED` | true | JSON output with confidence/evidence from LLM |
| `SYNONYM_MATCHING_ENABLED` | true | Synonym expansion for search terms |
| `ZERO_RESULTS_RELAXATION_ENABLED` | true | Relax filters when zero results |
| `ITEM_INSPECTION_ENABLED` | true | Item-level API inspection for gray-zone bids |
| `VIABILITY_ASSESSMENT_ENABLED` | true | 4-factor viability scoring |
| `USER_FEEDBACK_ENABLED` | true | User feedback loop (thumbs up/down) |
| `PROXIMITY_CONTEXT_ENABLED` | true | Proximity-context keyword filtering |
| `RATE_LIMITING_ENABLED` | true | Redis token bucket rate limiting |
| `SECTOR_RED_FLAGS_ENABLED` | true | Red flag keyword detection |
| `TRIAL_EMAILS_ENABLED` | true | Trial reminder emails |
| `BID_ANALYSIS_ENABLED` | true | Deep bid analysis feature |
| `METRICS_ENABLED` | true | Prometheus metrics collection |
| `CO_OCCURRENCE_RULES_ENABLED` | true | Keyword co-occurrence rules |
| `FILTER_DEBUG_MODE` | false | Log ALL contracts including approved |
| `SEARCH_ASYNC_ENABLED` | false | Async search via ARQ worker |
| `CACHE_REFRESH_ENABLED` | false | Periodic cache refresh cron |
| `CACHE_WARMING_ENABLED` | false | Proactive cache warming |
| `WARMUP_ENABLED` | true | Startup warm-up for top sector+UF combos |
| `TERM_SEARCH_LLM_AWARE` | false | LLM-aware term search (gradual rollout) |
| `TERM_SEARCH_SYNONYMS` | false | Synonym support for term search |
| `TERM_SEARCH_VIABILITY_GENERIC` | false | Generic viability for term search |
| `TERM_SEARCH_FILTER_CONTEXT` | false | Filter context for term search |

---

## 12. Security Architecture

### 12.1 Authentication Flow

```
Browser
  |
  +-- Next.js middleware (Supabase SSR cookie check)
  |     - Protected routes: redirect to /login
  |     - Domain redirect: railway.app -> smartlic.tech (301)
  |
  +-- API proxy route
  |     - getRefreshedToken() (server-side Supabase token refresh)
  |     - Fallback: Authorization header from request
  |
  +-- Backend: auth.py require_auth()
        - Attempt 1: JWKS (ES256) via PyJWKClient (5-min key cache)
        - Attempt 2: PEM public key (ES256) from SUPABASE_JWT_SECRET
        - Attempt 3: HS256 symmetric secret (backward compat)
        - Token cache: SHA256 hash key, 60s TTL
        - Return: { sub, email, role, aud, exp }
```

### 12.2 Authorization Model

| Level | Mechanism | Access |
|---|---|---|
| **require_auth** | JWT validation | All authenticated endpoints |
| **require_admin** | `app_metadata.role == 'admin'` or `is_admin=true` in profiles | Admin endpoints |
| **require_master** | `plan_type == 'sala_guerra'` | Master-only features |
| **RLS** | `auth.uid() = user_id` | Database row-level security |
| **Quota** | `check_and_increment_quota_atomic()` | Per-plan monthly limits |
| **Rate Limit** | Redis token bucket | Per-user request throttling |

### 12.3 Security Headers

Applied by both backend (`SecurityHeadersMiddleware`) and frontend (`next.config.js`):

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- Content Security Policy (frontend): strict allowlists for scripts, styles, connections

### 12.4 Input Validation

- **Backend:** Pydantic models with field validators, pattern validation for dates/UUIDs
- **UUID validation:** `validate_uuid()` with UUID v4 regex
- **Search sanitization:** `sanitize_search_query()` with safe character regex, SQL pattern escaping
- **Password policy:** 8+ chars, 1 uppercase, 1 digit
- **Plan ID validation:** Alphanumeric + underscore, 50 char max
- **Disposable email detection:** `utils/disposable_emails.py` blocks throwaway email services
- **Phone normalization:** `utils/phone_normalizer.py` validates Brazilian phone formats

### 12.5 PII Protection

- **Log sanitizer:** `log_sanitizer.py` masks emails (`j***@example.com`), tokens (`eyJ...***`), user IDs, IP addresses
- **Sentry scrubbing:** `scrub_pii()` in `main.py` strips PII from error events, breadcrumbs, exception values
- **Production logging:** DEBUG level forcibly elevated to INFO in production (Issue #168)
- **API docs disabled:** `docs_url=None`, `redoc_url=None` in production
- **Transient fingerprinting:** httpx timeouts and PNCP errors downgraded to warnings in Sentry

### 12.6 CORS Configuration

- **Development:** `localhost:3000`, `127.0.0.1:3000`
- **Production:** Railway app URLs + `smartlic.tech` + `www.smartlic.tech`
- **Security:** Wildcard `*` explicitly rejected, replaced with production defaults

### 12.7 Webhook Security

- **Stripe:** Signature verification via `stripe.Webhook.construct_event()` with `STRIPE_WEBHOOK_SECRET`
- **Idempotency:** Events deduplicated via `stripe_webhook_events` table (event_id unique constraint)

---

## 13. Observability

### 13.1 Error Tracking (Sentry)

- **Backend:** `sentry-sdk[fastapi]` with FastAPI + Starlette integrations
- **Frontend:** `@sentry/nextjs` with source map upload, tunnel route (`/monitoring`)
- **Sampling:** 10% traces, health checks excluded
- **PII scrubbing:** `before_send` callback strips emails, tokens, user IDs
- **Transient fingerprinting:** httpx timeouts grouped under custom fingerprints, downgraded to warnings
- **Release tracking:** `APP_VERSION` env var injected by CI/CD

### 13.2 Metrics (Prometheus)

Defined in `metrics.py` with graceful degradation (no-op if prometheus_client not installed):

| Metric | Type | Description |
|---|---|---|
| `SEARCH_DURATION` | Histogram | End-to-end search duration |
| `FETCH_DURATION` | Histogram | Per-source fetch duration |
| `CACHE_HITS` | Counter | Cache hit count by level |
| `CACHE_MISSES` | Counter | Cache miss count |
| `ACTIVE_SEARCHES` | Gauge | Currently active searches |
| `SEARCHES` | Counter | Total searches by status |
| `FILTER_DECISIONS` | Counter | Filter decisions by type (accept/reject/llm) |
| `LLM_CALLS` | Counter | LLM API calls by type |
| `LLM_DURATION` | Histogram | LLM call latency |
| `API_ERRORS` | Counter | API errors by source |
| `CIRCUIT_BREAKER_STATE` | Gauge | Circuit breaker state |
| `SEARCH_RESPONSE_STATE` | Counter | Search response state (fresh/stale/partial) |
| `SEARCH_ERROR_TYPE` | Counter | Error type distribution |
| `EVIDENCE_PREFIX_STRIPPED` | Counter | LLM evidence prefix corrections |

Endpoint: `GET /metrics` (protected by `METRICS_TOKEN` Bearer auth)

### 13.3 Distributed Tracing (OpenTelemetry)

- **TracerProvider:** Configured in `telemetry.py`
- **Exporters:** OTLP HTTP exporter (configurable endpoint)
- **Instrumentation:**
  - FastAPI (auto): request spans with route, method, status
  - httpx (auto): outgoing HTTP call spans
  - Manual: `optional_span()` decorator for pipeline stages
- **Trace correlation:** `trace_id` and `span_id` injected into log records and SSE events
- **Named tracers:** `search_pipeline`, `consolidation`, per-module isolation

### 13.4 Structured Logging

- **Production:** JSON format via `python-json-logger` (fields: timestamp, level, logger_name, message, module, funcName, lineno, request_id, search_id, correlation_id)
- **Development:** Pipe-delimited text format
- **Correlation IDs:**
  - `request_id`: UUID per HTTP request (CorrelationIDMiddleware)
  - `search_id`: UUID per search operation (set in search route)
  - `correlation_id`: Browser tab session ID (X-Correlation-ID header)
- **RequestIDFilter:** Ensures all log records have correlation fields (even startup logs)

---

## 14. Code Quality and Testing

### 14.1 Backend Test Suite

**214 entries** in `backend/tests/` (including `__pycache__`, `conftest.py`, `fixtures/`, `integration/`, `snapshots/`).

**Configuration:** `backend/pyproject.toml`
- Coverage threshold: **70%** (`fail_under = 70.0`)
- Branch coverage enabled
- Async mode: auto (`asyncio_mode = "auto"`)
- Markers: unit, integration, slow, asyncio

**Key Testing Patterns:**
- Auth: `app.dependency_overrides[require_auth]` (NOT `patch("routes.X.require_auth")`)
- Cache: Patch `supabase_client.get_supabase` (NOT `search_cache.get_supabase`)
- Config flags: `@patch("config.FLAG_NAME", False)` (NOT `os.environ`)
- LLM: Mock at `@patch("llm_arbiter._get_client")` level
- Quota: Tests mocking `/buscar` MUST also mock `check_and_increment_quota_atomic`
- ARQ: Mock with `sys.modules["arq"]` (not installed locally in test env)

**Test Categories:**
- Unit tests: `tests/test_*.py` (filtering, caching, auth, billing, pipeline, LLM, etc.)
- Integration tests: `tests/integration/` (real pipeline with mocked HTTP)
- Snapshot tests: `tests/snapshots/` (OpenAPI schema drift detection)
- Fixtures: `tests/fixtures/` (shared test data)

### 14.2 Frontend Test Suite

**88 entries** in `frontend/__tests__/` (including subdirectories).

**Configuration:** `frontend/jest.config.js`
- Coverage threshold: **60%**
- Environment: jsdom
- Polyfills: `crypto.randomUUID` + `EventSource` (jsdom lacks both)

**Test Subdirectories:**
- `__tests__/buscar/` -- Search page components
- `__tests__/api/` -- API proxy routes
- `__tests__/auth/` -- Authentication flows
- `__tests__/billing/` -- Billing components
- `__tests__/components/` -- Shared components
- `__tests__/account/` -- Account management
- `__tests__/data/` -- Data fixtures
- `__tests__/e2e/` -- E2E test utilities

### 14.3 E2E Tests (Playwright)

**Location:** `frontend/e2e-tests/`
- **Browsers:** Chromium (Desktop) + Mobile Safari (iPhone 13)
- **Critical Flows:** Search, Theme switching, Saved searches, Empty state, Error handling
- **Accessibility:** `@axe-core/playwright` for a11y testing
- **CI:** Runs headless, 15-min timeout
- **Commands:** `npm run test:e2e` (headless), `npm run test:e2e:headed` (debug)

### 14.4 Linting and Type Checking

| Tool | Configuration | CI Enforcement |
|---|---|---|
| Ruff (Python) | `pyproject.toml [tool.ruff]` | **Not enforced in CI** |
| Mypy (Python) | `pyproject.toml [tool.mypy]` (Python 3.12, ignore_missing_imports) | **Not enforced in CI** |
| ESLint (JS/TS) | `next lint` | Configured but enforcement unclear |
| TypeScript | `tsconfig.json` (strict null checks) | `npx tsc --noEmit` in CI |

### 14.5 Performance Testing

- **Locust:** `backend/locustfile.py` for load testing
- **Lighthouse CI:** `@lhci/cli` for frontend performance auditing
- **Load Test Workflow:** `.github/workflows/load-test.yml` (manual trigger)

---

## 15. Technical Debt Registry

### 15.1 Critical Severity (Must Fix)

| ID | Issue | Location | Impact | Effort |
|---|---|---|---|---|
| TD-C01 | **Dockerfile uses Python 3.11-slim but pyproject.toml targets 3.12** | `backend/Dockerfile` line 7 vs `backend/pyproject.toml` line 109 | Runtime version mismatch. The Dockerfile pins 3.11-slim while mypy and documentation target 3.12. Could lead to subtle compatibility issues with type hints and stdlib features. | Low |
| TD-C02 | **Dual HTTP client implementations** | `backend/pncp_client.py` | `PNCPClient` (sync, requests) and `AsyncPNCPClient` (async, httpx) duplicate retry logic, rate limiting, circuit breaker integration, and error handling. The sync client is only used as a legacy fallback wrapped in `asyncio.to_thread()`. Estimated 1500+ lines of duplicated logic. | High |
| TD-C03 | **Routes mounted twice (versioned + legacy)** | `backend/main.py` lines 554-602 | All 22 routers mounted at both `/v1/` and root. This doubles the route table (~100+ total endpoints), complicates debugging, and risks subtle behavior differences. Sunset date 2026-06-01 is set but no migration plan. | Medium |

### 15.2 High Severity (Should Fix)

| ID | Issue | Location | Impact | Effort |
|---|---|---|---|---|
| TD-H01 | **In-memory progress tracker not horizontally scalable** | `backend/progress.py` `_active_trackers` dict | Redis pub/sub mode exists but the in-memory asyncio.Queue is the primary mechanism. Two Railway web instances would have split progress state. This is the main blocker for scaling beyond 1 web instance. | Medium |
| TD-H02 | **In-memory auth token cache** | `backend/auth.py` `_token_cache` dict | Not shared across instances. With 2 Gunicorn workers, each has its own cache. Not a correctness issue (JWT self-validation is fast) but wastes memory and adds unnecessary complexity. | Low |
| TD-H03 | **search_pipeline.py is the new god module** | `backend/search_pipeline.py` | After STORY-216 decomposition from main.py, the search pipeline absorbed all business logic complexity. 7 stages with inline helpers create a large, tightly coupled module. | High |
| TD-H04 | **No backend linting enforcement in CI** | `.github/workflows/` | `ruff` and `mypy` are configured in `pyproject.toml` but not run in any CI workflow. Code quality regressions accumulate without automated checks. | Low |
| TD-H05 | **Hardcoded User-Agent references BidIQ** | `backend/pncp_client.py` | User-Agent string still says `"BidIQ/1.0 (procurement-search; contact@bidiq.com.br)"` instead of SmartLic. Also hardcoded in AsyncPNCPClient. Misleading for API providers. | Low |
| TD-H06 | **Migration naming inconsistency** | `supabase/migrations/` | Mixed naming: `001_profiles.sql` through `033_fix_missing.sql` (sequential) + `20260220120000_*` (timestamped). Makes migration ordering ambiguous. 43 total migrations suggest schema churn. | Medium |
| TD-H07 | **3 test files in backend/ root** | `backend/test_pncp_homologados_discovery.py`, `test_receita_federal_discovery.py`, `test_story_203_track2.py` | Test files outside the `tests/` directory break convention and may not be picked up by pytest's `testpaths` configuration. | Low |
| TD-H08 | **Excel base64 fallback in frontend proxy** | `frontend/app/api/buscar/route.ts` | Writes base64 Excel to filesystem `tmpdir()` as fallback when storage URL unavailable. Not scalable, not cleaned on crash, potential disk exhaustion. | Medium |
| TD-H09 | **100+ root-level markdown files** | Repository root | 70+ STORY-*, HOTFIX-*, DEPLOY-* markdown files clutter the repository root. Should be organized into `docs/sessions/` or removed. | Low |

### 15.3 Medium Severity (Plan to Fix)

| ID | Issue | Location | Impact | Effort |
|---|---|---|---|---|
| TD-M01 | **Feature flags in environment variables only** | `backend/config.py` | 25+ feature flags managed via env vars with in-memory 60s TTL cache. No UI for runtime toggling. Changing flags requires container restart or `POST /v1/admin/feature-flags/reload`. | Medium |
| TD-M02 | **No pre-commit hooks** | Repository root | No `.pre-commit-config.yaml` visible. Developers can commit code that fails linting, type checking, or tests. | Low |
| TD-M03 | **Frontend test quarantine growing** | `frontend/__tests__/quarantine/` | Quarantined tests indicate broken component contracts or flaky assertions. Tests moved to quarantine are effectively dead. | Medium |
| TD-M04 | **dotenv loaded before setup_logging** | `backend/main.py` line 38 | `load_dotenv()` called at module level before `setup_logging()`. Some env vars read at import time may use stale values if .env is changed during execution. | Low |
| TD-M05 | **No database connection pooling in Supabase client** | `backend/supabase_client.py` | Single global client instance with no explicit connection pool management. Relies on supabase-py internal handling, which may not be optimal for 2 Gunicorn workers + background jobs. | Medium |
| TD-M06 | **synchronous sleep in quota.py** | `backend/quota.py` | `time.sleep(0.3)` used for retry delay in `save_search_session`. Blocks the async event loop. Should use `asyncio.sleep()`. | Low |
| TD-M07 | **Lead prospecting modules not integrated** | `backend/lead_prospecting.py`, `lead_scorer.py`, `lead_deduplicator.py`, `contact_searcher.py`, `cli_acha_leads.py` | 5 lead-related modules exist but appear disconnected from the main search pipeline. May be dead code from an earlier feature exploration. | Low |
| TD-M08 | **Multiple HTTP client libraries** | `backend/requirements.txt` | Both `requests==2.32.3` and `httpx==0.28.1` are production dependencies. Should consolidate to httpx only (the async client already uses it). | Medium |
| TD-M09 | **No request timeout for Stripe webhooks** | `backend/webhooks/stripe.py` | Webhook handler has no explicit timeout. Long-running DB operations in webhook processing could block the worker indefinitely. | Low |
| TD-M10 | **OpenAPI schema drift detection only in snapshots** | `backend/tests/snapshots/` | Schema drift tests exist but are snapshot-based. No automated contract testing between frontend API types and backend schemas. `openapi-typescript` generates types but no CI step validates freshness. | Medium |

### 15.4 Low Severity (Nice to Fix)

| ID | Issue | Location | Impact | Effort |
|---|---|---|---|---|
| TD-L01 | **Screenshot/image files in git root** | Repository root | 18+ untracked `.png` files pollute the working tree. Should be in `docs/images/` or `.gitignore`d. | Low |
| TD-L02 | **Deprecated asyncio pattern** | `backend/pncp_client.py` | `asyncio.get_event_loop().time()` should use `asyncio.get_running_loop().time()` in Python 3.10+. | Low |
| TD-L03 | **format_resumo_html unused** | `backend/llm.py` | HTML summary generation function exists but frontend renders from JSON. Dead code. | Low |
| TD-L04 | **dangerouslySetInnerHTML for theme** | `frontend/app/layout.tsx` | Necessary for FOUC prevention but inline `<script>` with `dangerouslySetInnerHTML` merits a security comment. | Low |
| TD-L05 | **Commented-out route search.py.tmp** | `backend/routes/search.py.tmp` | Temporary/backup file committed alongside the real route file. Should be removed. | Low |
| TD-L06 | **pyproject.toml still references "bidiq-uniformes-backend"** | `backend/pyproject.toml` line 8 | Project name and description reference the old "BidIQ Uniformes" branding. Should be updated to "SmartLic". | Low |

### 15.5 Security Concerns

| ID | Issue | Location | Severity | Impact |
|---|---|---|---|---|
| TD-S01 | **`unsafe-inline` and `unsafe-eval` in CSP** | `frontend/next.config.js` line 57 | Medium | `script-src` includes both `'unsafe-inline'` and `'unsafe-eval'`, weakening the Content Security Policy. Required by Next.js and Stripe.js but should be reviewed for nonce-based approach. |
| TD-S02 | **Service role key used for all backend operations** | `backend/supabase_client.py` | Low | The backend uses `SUPABASE_SERVICE_ROLE_KEY` (bypasses RLS) for all operations. While intentional for server-to-server auth, any backend vulnerability could expose all user data. Consider per-user JWT forwarding for user-scoped operations. |
| TD-S03 | **Google verification code in public HTML** | `frontend/app/layout.tsx` line 112 | Low | Google site verification token is embedded in public metadata. Not a vulnerability per se, but could allow verification spoofing in staging/dev environments. |

### 15.6 Performance Concerns

| ID | Issue | Location | Severity | Impact |
|---|---|---|---|---|
| TD-P01 | **Railway 1GB memory limit with 2 workers** | `backend/start.sh` | High | Each Gunicorn worker maintains its own in-memory caches (auth tokens, LLM decisions, plan capabilities, feature flags). With 2 workers, memory is duplicated. OOM kills have been observed historically (leading to WEB_CONCURRENCY reduction from 4 to 2). |
| TD-P02 | **No CDN for static assets** | Infrastructure | Medium | Frontend static assets served directly from Railway without a CDN. No edge caching for global users. |
| TD-P03 | **PNCP page size reduced to 50** | `backend/pncp_client.py` | Medium | PNCP API reduced max `tamanhoPagina` from 500 to 50, requiring 10x more API calls for the same data volume. The health canary (tamanhoPagina=10) does not detect this limit. |

---

## Appendix: Complete File Inventory

### Backend Module Count

| Category | Count | Key Files |
|---|---|---|
| Core Python modules | 69 | main.py, config.py, search_pipeline.py, pncp_client.py, filter.py, llm.py, etc. |
| Route modules | 21 | routes/search.py, routes/user.py, routes/billing.py, etc. |
| Client adapters | 8 | clients/base.py, sanctions.py, compras_gov_client.py, etc. |
| Model modules | 4 | models/cache.py, search_state.py, etc. |
| Service modules | 6 | services/billing.py, trial_stats.py, etc. |
| Utility modules | 7 | utils/cnae_mapping.py, date_parser.py, etc. |
| Email templates | 5 | templates/emails/welcome.py, quota.py, trial.py, etc. |
| Test entries | 214 | tests/test_*.py, tests/integration/, tests/snapshots/ |
| Backend migrations | 10 | backend/migrations/002-010 |

### Frontend File Count

| Type | Count |
|---|---|
| Pages (app router) | 29 |
| API proxy routes | 27 |
| Search components (buscar/) | 30 |
| Shared components (app/components/) | 48 |
| Landing components | 12 |
| UI primitives | 6 |
| Top-level components (components/) | 22 |
| Custom hooks | 4 |
| Lib modules | 20+ |
| Test entries | 88 |

### Database

| Item | Count |
|---|---|
| Supabase migrations | 43 |
| Backend migrations | 10 |
| Tables | ~17 |
| RLS policies | ~25 |
| Functions/triggers | 7 |

### CI/CD

| Item | Count |
|---|---|
| GitHub Actions workflows | 16 |

### Sectors

| ID | Name | Keywords | Viability Range |
|---|---|---|---|
| vestuario | Vestuario e Uniformes | 50+ terms | R$50k-R$2M |
| alimentos | Alimentos e Merenda | Sector-specific | Sector-specific |
| informatica | Hardware e Equipamentos de TI | Sector-specific | Sector-specific |
| mobiliario | Mobiliario | Sector-specific | Sector-specific |
| papelaria | Papelaria e Material de Escritorio | Sector-specific | Sector-specific |
| engenharia | Engenharia, Projetos e Obras | Sector-specific | Sector-specific |
| software | Software e Sistemas | Sector-specific | Sector-specific |
| facilities | Facilities e Manutencao | Sector-specific | Sector-specific |
| saude | Saude | Sector-specific | Sector-specific |
| vigilancia | Vigilancia e Seguranca Patrimonial | Sector-specific | Sector-specific |
| transporte | Transporte e Veiculos | Sector-specific | Sector-specific |
| manutencao_predial | Manutencao e Conservacao Predial | Sector-specific | Sector-specific |
| engenharia_rodoviaria | Engenharia Rodoviaria e Infraestrutura Viaria | Sector-specific | Sector-specific |
| materiais_eletricos | Materiais Eletricos e Instalacoes | Sector-specific | Sector-specific |
| materiais_hidraulicos | Materiais Hidraulicos e Saneamento | Sector-specific | Sector-specific |

---

*End of System Architecture Document - SmartLic v3.0*
*Generated 2026-02-25 by @architect (Archon) during Brownfield Discovery Phase 1*
*Based on analysis of 69 backend modules, 29 frontend pages, 80+ components, 43 database migrations, 300+ test files*
