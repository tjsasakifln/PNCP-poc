# Source Tree — SmartLic

**Atualizado:** 2026-02-20

## Backend (FastAPI)

```
backend/
├── main.py                     # FastAPI app, middleware, legacy endpoints
├── config.py                   # Env vars, feature flags, constants
├── schemas.py                  # Pydantic models (BuscaRequest, BuscaResponse, etc.)
│
├── # --- Search Pipeline ---
├── search_pipeline.py          # Orchestrator: multi-source search + consolidation
├── consolidation.py            # Source aggregation, dedup, timeout management
├── pncp_client.py              # PNCP API client (pagination, retry, circuit breaker)
├── pncp_client_resilient.py    # Enhanced PNCP client with degradation
├── pncp_resilience.py          # Circuit breaker + degradation state
├── search_context.py           # SearchContext dataclass for pipeline state
├── search_cache.py             # Two-level cache (InMemory + Supabase), SWR, priority
├── progress.py                 # SSE progress tracking (asyncio.Queue)
│
├── # --- Filtering & Classification ---
├── filter.py                   # Keyword matching, LLM zero-match dispatch
├── filter_stats.py             # Filter statistics tracking
├── llm_arbiter.py              # GPT-4.1-nano binary classification
├── relevance.py                # Relevance scoring
├── viability.py                # 4-factor viability assessment
├── feedback_analyzer.py        # Bi-gram analysis from user feedback
├── sectors.py                  # 15 sector definitions + keywords
├── synonyms.py                 # Keyword synonym expansion
├── term_parser.py              # Search term parsing
├── status_inference.py         # Bid status inference from dates
│
├── # --- Output Generation ---
├── excel.py                    # Excel report with openpyxl
├── llm.py                      # GPT-4.1-nano executive summaries
├── google_sheets.py            # Google Sheets export
├── report_generator.py         # Report orchestration
│
├── # --- Auth & Billing ---
├── auth.py                     # JWT auth, require_auth dependency
├── authorization.py            # Role-based access control
├── oauth.py                    # OAuth2 providers
├── quota.py                    # Usage quotas, grace period, plan enforcement
│
├── # --- Routes (decomposed from main.py) ---
├── routes/
│   ├── analytics.py            # GET /v1/analytics/*
│   ├── auth_email.py           # POST /v1/auth/email/*
│   ├── auth_oauth.py           # GET/POST /v1/auth/oauth/*
│   ├── billing.py              # POST /v1/billing/*
│   ├── emails.py               # POST /v1/emails/*
│   ├── export_sheets.py        # POST /v1/export/sheets
│   ├── features.py             # GET /v1/features
│   ├── feedback.py             # POST/DELETE /v1/feedback
│   ├── health.py               # GET /v1/health/*
│   ├── messages.py             # GET/POST /v1/messages/*
│   ├── onboarding.py           # POST /v1/first-analysis
│   ├── pipeline.py             # GET/POST /v1/pipeline/*
│   ├── plans.py                # GET /v1/plans/*
│   ├── search.py               # POST /buscar, GET /buscar-progress/*
│   ├── sessions.py             # GET/DELETE /v1/sessions/*
│   ├── subscriptions.py        # POST /v1/subscriptions/*
│   └── user.py                 # GET /v1/me, /v1/trial-status
│
├── # --- Infrastructure ---
├── admin.py                    # Admin endpoints (cache, feedback patterns)
├── database.py                 # Supabase connection helpers
├── supabase_client.py          # Supabase client singleton
├── redis_client.py             # Redis client
├── redis_pool.py               # Redis connection pool + InMemoryCache fallback
├── cache.py                    # Generic cache utilities
├── middleware.py                # CORS, rate limiting, error handling
├── rate_limiter.py             # Token bucket rate limiter
├── storage.py                  # File storage abstraction
├── email_service.py            # Transactional email service
│
├── # --- Observability ---
├── metrics.py                  # Prometheus metrics (11 metrics, /metrics endpoint)
├── telemetry.py                # OpenTelemetry tracing
├── job_queue.py                # ARQ background jobs (LLM, Excel)
├── health.py                   # Health check logic
├── analytics_events.py         # Mixpanel event tracking
├── log_sanitizer.py            # PII removal from logs
├── audit.py                    # Audit logging
│
├── # --- Lead Prospecting ---
├── lead_prospecting.py         # Lead discovery engine
├── lead_scorer.py              # Lead scoring model
├── lead_deduplicator.py        # Lead deduplication
├── contact_searcher.py         # Contact info lookup
├── schemas_lead_prospecting.py # Lead Pydantic models
│
├── # --- Utilities ---
├── utils/
│   ├── cnae_mapping.py         # CNAE code to sector mapping
│   ├── date_parser.py          # Date parsing utilities
│   ├── error_reporting.py      # Error reporting helpers
│   └── ordenacao.py            # Sort utilities
├── exceptions.py               # Custom exception classes
├── message_generator.py        # Message templates
├── item_inspector.py           # Bid item inspection
│
├── # --- External Clients ---
├── pncp_homologados_client.py  # PNCP homologated items client
├── receita_federal_client.py   # Receita Federal CNPJ lookup
│
├── # --- Config & Scripts ---
├── start.sh                    # Gunicorn launcher (PROCESS_TYPE=web|worker)
├── requirements.txt            # Python dependencies
├── pyproject.toml              # pytest + coverage config
├── Procfile                    # Railway process definition
├── sectors_data.yaml           # Sector keyword definitions
├── seed_users.py               # Database seeding
└── tests/                      # ~3966 tests
    ├── test_*.py               # Unit and integration tests
    └── snapshots/              # API schema snapshots
```

## Frontend (Next.js 14)

```
frontend/
├── app/
│   ├── page.tsx                # Landing page
│   ├── layout.tsx              # Root layout (providers, metadata)
│   ├── types.ts                # Shared TypeScript types
│   │
│   ├── # --- Core Pages ---
│   ├── buscar/
│   │   ├── page.tsx            # Search page (main SPA)
│   │   ├── components/         # Search-specific components
│   │   │   ├── CacheBanner.tsx
│   │   │   ├── CoverageBar.tsx
│   │   │   ├── DegradationBanner.tsx
│   │   │   ├── FeedbackButtons.tsx
│   │   │   ├── FilterPanel.tsx
│   │   │   ├── FreshnessIndicator.tsx
│   │   │   ├── SearchForm.tsx
│   │   │   ├── SearchResults.tsx
│   │   │   ├── ViabilityBadge.tsx
│   │   │   └── ... (14 components)
│   │   ├── hooks/
│   │   │   ├── useSearch.ts
│   │   │   ├── useSearchFilters.ts
│   │   │   └── useUfProgress.ts
│   │   └── utils/
│   │       ├── dates.ts
│   │       └── reliability.ts
│   │
│   ├── pipeline/               # Opportunity pipeline
│   ├── dashboard/              # User dashboard
│   ├── admin/                  # Admin pages (cache dashboard)
│   ├── conta/                  # Account settings
│   ├── historico/              # Search history
│   ├── mensagens/              # Messaging
│   ├── onboarding/             # 3-step onboarding wizard
│   ├── planos/                 # Pricing/plans
│   ├── login/                  # Login page
│   ├── signup/                 # Signup page
│   ├── features/               # Features page
│   ├── recuperar-senha/        # Password recovery
│   ├── redefinir-senha/        # Password reset
│   │
│   ├── # --- API Routes (proxy to backend) ---
│   ├── api/
│   │   ├── buscar/route.ts     # POST → /buscar
│   │   ├── buscar-progress/    # GET → /buscar-progress/{id}
│   │   ├── download/route.ts   # GET → Excel download
│   │   ├── feedback/route.ts   # POST/DELETE → /v1/feedback
│   │   ├── admin/[...path]/    # Dynamic admin proxy
│   │   ├── analytics/route.ts  # GET → /v1/analytics/*
│   │   ├── billing-portal/     # POST → /v1/billing
│   │   ├── trial-status/       # GET → /v1/trial-status
│   │   └── ... (20+ proxy routes)
│   │
│   ├── # --- Shared Components ---
│   ├── components/
│   │   ├── landing/            # Landing page sections (11 components)
│   │   ├── ui/                 # Design system (BentoGrid, GlassCard, etc.)
│   │   ├── AuthProvider.tsx
│   │   ├── AppHeader.tsx
│   │   ├── LoadingProgress.tsx
│   │   ├── RegionSelector.tsx
│   │   ├── TrialConversionScreen.tsx
│   │   └── ... (40+ components)
│   │
│   ├── # --- Static Pages ---
│   ├── privacidade/            # Privacy policy
│   ├── termos/                 # Terms of service
│   └── ajuda/                  # Help page
│
├── __tests__/                  # Jest tests (~1921 tests)
├── e2e-tests/                  # Playwright E2E tests
├── public/                     # Static assets
├── jest.config.js
├── jest.setup.js
├── tailwind.config.js
├── tsconfig.json
├── next.config.js
└── package.json
```

## Documentation

```
docs/
├── framework/
│   ├── source-tree.md          # This file
│   ├── tech-stack.md           # Technology choices
│   └── coding-standards.md     # Code style guide
├── architecture/               # ADRs and system design
├── guides/                     # Developer guides
├── reports/                    # Audit reports (pre-GTM)
├── stories/                    # Active stories (GTM-001/002, TD-*, UX-*, STORY-240+)
├── archive/                    # Archived completed/superseded docs
├── gtm-resilience-summary.md   # Consolidated 25-story summary
└── gtm-fixes-summary.md        # Consolidated 37-fix summary
```

## Data Flow

```
User (Next.js) → API Proxy → Backend API (FastAPI)
                                    │
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
              InMemoryCache    Supabase Cache    Live Search
                                                     │
                                    ┌────────────────┼────────────────┐
                                    ↓                ↓                ↓
                                PNCP API         PCP v2 API    ComprasGov v3
                                    │
                              Consolidation + Dedup
                                    │
                              Filter Engine
                              (Keywords + LLM Arbiter)
                                    │
                        ┌───────────┼───────────┐
                        ↓           ↓           ↓
                  Viability    Confidence    Ranking
                  Assessment   Scoring
                        │
                  ┌─────┼─────┐
                  ↓     ↓     ↓
              Results  Excel  LLM Summary
                  │     │     │
                  ↓ SSE ↓     ↓ (ARQ background job)
              Frontend receives progressively
```
