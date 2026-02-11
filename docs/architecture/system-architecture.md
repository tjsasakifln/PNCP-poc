# System Architecture - SmartLic/BidIQ

**Version:** 1.0
**Date:** 2026-02-11
**Author:** @architect (Aria)
**Status:** Complete analysis of production codebase on `main` branch (commit `808cd05`)

---

## 1. Executive Summary

SmartLic (formerly BidIQ Uniformes) is a SaaS platform for automated procurement opportunity discovery from Brazil's PNCP (Portal Nacional de Contratacoes Publicas). The system is a two-tier web application with a Python FastAPI backend and a Next.js TypeScript frontend, deployed on Railway with Supabase as the database/auth layer.

**Key characteristics:**
- **Architecture style:** Monolithic API + SPA frontend with BFF (Backend-for-Frontend) proxy layer
- **Primary data source:** PNCP public API (government procurement portal)
- **Revenue model:** Tiered subscription (free trial, 3 paid tiers) via Stripe
- **AI integration:** GPT-4.1-nano for executive summaries, GPT-4o-mini for contract classification (LLM Arbiter)
- **Scale:** Single-instance deployment (Railway), in-memory state for SSE progress tracking
- **Maturity:** POC v0.3 with production users; significant feature surface area for a proof-of-concept

**Architecture risk rating:** MEDIUM -- The system works in production but carries technical debt from rapid feature accretion. Critical concerns include in-memory state that prevents horizontal scaling, dual ORM usage (Supabase client + SQLAlchemy), and a growing monolithic main.py (1,959 lines).

---

## 2. Tech Stack Overview

### 2.1 Backend

| Layer | Technology | Version | File |
|-------|-----------|---------|------|
| Framework | FastAPI | 0.115.9 | `backend/requirements.txt:4` |
| Runtime | Python | 3.12 (target 3.11+) | `backend/pyproject.toml:9` |
| ASGI Server | Uvicorn | 0.40.0 | `backend/requirements.txt:5` |
| Validation | Pydantic | 2.12.5 | `backend/requirements.txt:6` |
| HTTP Client (sync) | requests | 2.32.3 | `backend/requirements.txt:12` |
| HTTP Client (async) | httpx | 0.28.1 | `backend/requirements.txt:11` |
| Excel Generation | openpyxl | 3.1.5 | `backend/requirements.txt:15` |
| LLM Integration | OpenAI SDK | 1.109.1 | `backend/requirements.txt:18` |
| Auth/Database | Supabase Python | 2.13.0 | `backend/requirements.txt:22` |
| Payments | Stripe | 11.4.1 | `backend/requirements.txt:23` |
| Caching | Redis | 5.2.1 | `backend/requirements.txt:24` |
| ORM | SQLAlchemy | 2.0.36 | `backend/requirements.txt:25` |
| DB Adapter | psycopg2-binary | 2.9.10 | `backend/requirements.txt:26` |
| Google Sheets | google-api-python-client | 2.150.0 | `backend/requirements.txt:29` |
| Linting | Ruff | 0.9.6 | `backend/requirements.txt:49` |
| Type Checking | mypy | 1.15.0 | `backend/requirements.txt:50` |
| Testing | pytest | 8.4.2 | `backend/requirements.txt:38` |
| Load Testing | Locust | 2.43.2 | `backend/requirements.txt:45` |

### 2.2 Frontend

| Layer | Technology | Version | File |
|-------|-----------|---------|------|
| Framework | Next.js (App Router) | 16.1.6 | `frontend/package.json:33` |
| Language | TypeScript | 5.9.3 | `frontend/package.json:61` |
| React | React | 18.3.1 | `frontend/package.json:34` |
| Styling | Tailwind CSS | 3.4.19 | `frontend/package.json:60` |
| Auth Client | @supabase/supabase-js | 2.93.3 | `frontend/package.json:27` |
| SSR Auth | @supabase/ssr | 0.8.0 | `frontend/package.json:26` |
| Animation | Framer Motion | 12.33.0 | `frontend/package.json:30` |
| Icons | Lucide React | 0.563.0 | `frontend/package.json:31` |
| Charts | Recharts | 3.7.0 | `frontend/package.json:37` |
| Analytics | Mixpanel | 2.74.0 | `frontend/package.json:32` |
| Onboarding | Shepherd.js | 14.5.1 | `frontend/package.json:38` |
| Toast | Sonner | 2.0.7 | `frontend/package.json:39` |
| Date Picker | react-day-picker | 9.13.0 | `frontend/package.json:35` |
| Testing | Jest + Testing Library | 29.7.0 / 14.1.2 | `frontend/package.json:56-57` |
| E2E Testing | Playwright | 1.58.1 | `frontend/package.json:47` |
| Performance | Lighthouse CI | 0.15.0 | `frontend/package.json:46` |

### 2.3 Infrastructure

| Service | Provider | Purpose |
|---------|----------|---------|
| Backend Hosting | Railway | FastAPI deployment (standalone container) |
| Frontend Hosting | Railway | Next.js standalone mode |
| Database | Supabase (PostgreSQL) | User data, subscriptions, search sessions |
| Authentication | Supabase Auth | JWT-based auth with email/password + Google OAuth |
| Payments | Stripe | Subscription billing (monthly/annual) |
| Caching | Redis (Railway) | Rate limiting, feature flag cache |
| Version Control | GitHub | Source code, CI/CD workflows |
| CI/CD | GitHub Actions | 11 workflow files |

### 2.4 External APIs

| API | Purpose | Rate Limit |
|-----|---------|------------|
| PNCP (pncp.gov.br) | Procurement data source | 10 req/s (self-imposed) |
| OpenAI GPT-4.1-nano | Executive summaries | Standard OpenAI limits |
| OpenAI GPT-4o-mini | LLM Arbiter (contract classification) | Standard OpenAI limits |
| Stripe API | Payment processing | Standard Stripe limits |
| Google Sheets API | Export functionality | Standard Google limits |

---

## 3. Backend Architecture

### 3.1 Module Map

The backend is located at `backend/` and consists of the following modules:

```
backend/
  main.py              (1959 lines) - Core FastAPI app, all main endpoints
  pncp_client.py       (1032 lines) - Sync + Async PNCP API clients
  filter.py            (800+ lines)  - Multi-criteria filtering engine
  excel.py             (290 lines)   - openpyxl Excel report generator
  llm.py               (370 lines)   - GPT-4.1-nano summary generation
  schemas.py           (946 lines)   - Pydantic request/response models
  auth.py              (118 lines)   - JWT authentication middleware
  config.py            (325 lines)   - Configuration, feature flags, CORS
  quota.py             (709 lines)   - Plan capabilities and quota management
  progress.py          (129 lines)   - SSE progress tracking (in-memory)
  rate_limiter.py      (110 lines)   - Redis + in-memory rate limiting
  sectors.py           (300+ lines)  - Multi-sector keyword configuration
  admin.py             (300+ lines)  - Admin user management endpoints
  supabase_client.py   (50 lines)    - Supabase singleton client
  log_sanitizer.py     (606 lines)   - PII masking and log sanitization
  exceptions.py        - Custom exception types
  status_inference.py  - Bid status enrichment from dates
  term_parser.py       - Search term parsing (comma/phrase support)
  relevance.py         - Relevance scoring for custom search terms
  consolidation.py     - Multi-source data consolidation
  database.py          - SQLAlchemy session management
  cache.py             - Redis cache client
  routes/
    subscriptions.py   - Billing period management
    features.py        - Feature flag endpoints
    messages.py        - InMail messaging system
    analytics.py       - Usage analytics endpoints
    auth_oauth.py      - Google OAuth routes (STORY-180)
    export_sheets.py   - Google Sheets export (STORY-180)
  webhooks/
    stripe.py          - Stripe webhook handler (idempotent)
  models/
    stripe_webhook_event.py - SQLAlchemy model
    user_subscription.py    - SQLAlchemy model
  clients/
    base.py            - Source adapter base class
    compras_gov_client.py   - ComprasGov adapter
    portal_compras_client.py - Portal Compras adapter
  source_config/
    sources.py         - Multi-source configuration
  services/
    billing.py         - Pro-rata credit calculation
  utils/
    ordenacao.py       - Result sorting utilities
```

### 3.2 API Endpoints

**Main Application Endpoints** (`backend/main.py`):

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/` | No | API root with documentation links |
| GET | `/health` | No | Health check with dependency status |
| GET | `/sources/health` | No | Multi-source health check |
| GET | `/setores` | No | List available procurement sectors |
| GET | `/debug/pncp-test` | No | PNCP API connectivity diagnostic |
| POST | `/buscar` | Yes | **Main search endpoint** (core pipeline) |
| GET | `/buscar-progress/{search_id}` | Yes | SSE stream for search progress |
| GET | `/me` | Yes | User profile with plan capabilities |
| GET | `/sessions` | Yes | Search session history |
| GET | `/plans` | No | Available subscription plans |
| POST | `/checkout` | Yes | Create Stripe checkout session |
| POST | `/change-password` | Yes | Password change |

**Router-based Endpoints**:

| Router | Prefix | File | Key Endpoints |
|--------|--------|------|---------------|
| Admin | `/admin` | `admin.py` | User CRUD, plan management, search |
| Subscriptions | `/api/subscriptions` | `routes/subscriptions.py` | Billing period updates |
| Features | (varies) | `routes/features.py` | Feature flag queries |
| Messages | (varies) | `routes/messages.py` | InMail conversations |
| Analytics | (varies) | `routes/analytics.py` | Usage analytics |
| OAuth | (varies) | `routes/auth_oauth.py` | Google OAuth flow |
| Export | (varies) | `routes/export_sheets.py` | Google Sheets export |
| Stripe Webhooks | `/webhooks/stripe` | `webhooks/stripe.py` | Stripe event processing |

### 3.3 Core Patterns

#### 3.3.1 Retry with Exponential Backoff

**File:** `backend/pncp_client.py:36-64`

The PNCP client implements configurable retry logic:
- **Base delay:** 1.5s (configurable via `RetryConfig`)
- **Max delay:** 15s cap
- **Exponential base:** 2x per attempt
- **Jitter:** +/-50% to prevent thundering herd
- **Max retries:** 3 (configurable)
- **Retryable codes:** 408, 429, 500, 502, 503, 504

```python
@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.5
    max_delay: float = 15.0
    exponential_base: int = 2
    jitter: bool = True
    timeout: int = 30
```

#### 3.3.2 Parallel UF Fetching

**File:** `backend/pncp_client.py:563-1032`

The `AsyncPNCPClient` enables parallel fetching across Brazilian states using `httpx.AsyncClient` + `asyncio.Semaphore`:
- Default concurrency: 10 simultaneous UFs
- Per-UF timeout: 90 seconds
- Global fetch timeout: 4 minutes
- Automatic fallback from parallel to sequential on failure

#### 3.3.3 Rate Limiting (Dual Layer)

**Layer 1 - PNCP API:** Self-imposed 10 req/s via `_rate_limit()` method with 100ms minimum interval (`pncp_client.py:114-129`).

**Layer 2 - User API:** Per-user, per-minute rate limiting via Redis (with in-memory fallback) based on plan tier (`rate_limiter.py`). Plan-based limits range from 2/min (free) to 60/min (sala_guerra).

#### 3.3.4 Fail-Fast Sequential Filtering

**File:** `backend/filter.py`

Filters are applied in order of computational cost (cheapest first):
1. UF check (O(1) set lookup)
2. Status filter
3. Esfera (government sphere) filter
4. Modalidade (procurement modality) filter
5. Municipio filter
6. Value range filter
7. Keyword matching (regex -- most expensive)
8. Minimum match floor (relevance threshold)

Each filter stage has counters in `FilterStats` for diagnostic transparency.

#### 3.3.5 LLM Arbiter Pattern (STORY-179)

**File:** `backend/config.py:159-212`

A two-tier classification system using term density thresholds:
- **High density (>5%):** Auto-accept (no LLM call)
- **Medium density (2-5%):** LLM classification via GPT-4o-mini
- **Low density (<1%):** Auto-reject (no LLM call)
- Cost: ~R$ 0.50/month for 10K contracts

#### 3.3.6 Feature Flags

**File:** `backend/config.py:121-220`

Runtime-configurable feature flags via environment variables:
- `ENABLE_NEW_PRICING` (default: true) -- Plan-based billing
- `LLM_ARBITER_ENABLED` (default: true) -- Contract classification
- `SYNONYM_MATCHING_ENABLED` (default: true) -- Keyword synonyms
- `ZERO_RESULTS_RELAXATION_ENABLED` (default: true) -- Graceful degradation
- `FILTER_DEBUG_MODE` (default: false) -- Debug logging
- `ENABLE_MULTI_SOURCE` (default: false) -- Multi-source consolidation

### 3.4 Authentication and Authorization

#### 3.4.1 Authentication Flow

**File:** `backend/auth.py`

Authentication uses Supabase JWT tokens with a performance-optimized cache:

1. Client sends `Authorization: Bearer <supabase_jwt>` header
2. `get_current_user()` checks a local token cache (60s TTL, keyed on first 16 chars hash)
3. On cache miss, validates token via `supabase.auth.get_user(token)` remote call
4. Returns `{"id": str, "email": str, "role": str}` dict

Cache reduces Supabase Auth API calls by ~95% and eliminates intermittent validation failures.

#### 3.4.2 Authorization (Role Hierarchy)

**File:** `backend/main.py:392-498`

Three-tier role hierarchy:
1. **Admin** -- Full system access, user management via `/admin/*`. Sources: `ADMIN_USER_IDS` env var OR `profiles.is_admin = true`
2. **Master** -- Full feature access (Excel, unlimited quota), no admin UI. Source: `profiles.plan_type = 'master'`
3. **Regular User** -- Plan-based access controlled by subscription tier

Admins and Masters bypass:
- Quota checks
- Rate limiting
- Date range restrictions
- Feature gating

The `_check_user_roles()` function retries once (0.3s delay) before giving up on DB errors.

### 3.5 Billing and Subscription System

#### 3.5.1 Plan Tiers

**File:** `backend/quota.py:62-127`

| Plan | Monthly Price | Searches/mo | Excel | History | RPM |
|------|-------------|-------------|-------|---------|-----|
| free_trial | Free | 3 | No | 7 days | 2 |
| consultor_agil | R$ 297 | 50 | No | 30 days | 10 |
| maquina | R$ 597 | 300 | Yes | 365 days | 30 |
| sala_guerra | R$ 1,497 | 1,000 | Yes | 5 years | 60 |

#### 3.5.2 Quota Management

**File:** `backend/quota.py:286-346`

Atomic quota check-and-increment via PostgreSQL RPC function `check_and_increment_quota`. This addresses Issue #189 (TOCTOU race condition):
- Performs check + increment in a single database transaction
- Falls back to in-process locking if RPC unavailable
- Monthly reset via `month_year` key (lazy reset pattern)

#### 3.5.3 Subscription Resilience (Multi-Layer Lookup)

**File:** `backend/quota.py:413-580`

Four-layer subscription resolution prevents paid users from being downgraded to free_trial:
1. **Active subscription** in `user_subscriptions` (primary)
2. **Grace-period subscription** (within 3 days of expiry)
3. **Profile fallback** via `profiles.plan_type` (last known plan)
4. **Absolute fallback** to `free_trial` (only for truly new users)

#### 3.5.4 Stripe Integration

**File:** `backend/webhooks/stripe.py`

Webhook handler with security features:
- Signature verification via `stripe.Webhook.construct_event()`
- Idempotency via `stripe_webhook_events` table
- Atomic DB updates via SQLAlchemy `on_conflict_do_update`
- Redis cache invalidation after subscription changes

Handled events: `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_succeeded`

#### 3.5.5 Checkout Flow

**File:** `backend/main.py:674-725`

1. Frontend calls `POST /checkout?plan_id=X&billing_period=monthly`
2. Backend looks up Stripe price ID from `plans` table
3. Creates Stripe Checkout Session (subscription mode)
4. Returns `checkout_url` for client redirect
5. On success, Stripe redirects to `/planos/obrigado?plan=X`
6. Webhook `checkout.session.completed` triggers `_activate_plan()`

---

## 4. Frontend Architecture

### 4.1 Page Structure

**File:** `frontend/next.config.js` -- Standalone output mode for Railway deployment

The frontend uses Next.js App Router with 16 pages:

| Path | File | Purpose | Auth |
|------|------|---------|------|
| `/` | `app/page.tsx` | Landing page (marketing) | No |
| `/login` | `app/login/page.tsx` | Email/password login | No |
| `/signup` | `app/signup/page.tsx` | Account registration | No |
| `/buscar` | `app/buscar/page.tsx` | **Main search interface** | Yes |
| `/dashboard` | `app/dashboard/page.tsx` | User dashboard | Yes |
| `/historico` | `app/historico/page.tsx` | Search history | Yes |
| `/planos` | `app/planos/page.tsx` | Pricing/plans display | No |
| `/planos/obrigado` | `app/planos/obrigado/page.tsx` | Post-payment thank you | Yes |
| `/pricing` | `app/pricing/page.tsx` | Alternative pricing page | No |
| `/conta` | `app/conta/page.tsx` | Account settings | Yes |
| `/admin` | `app/admin/page.tsx` | Admin panel | Yes (admin) |
| `/mensagens` | `app/mensagens/page.tsx` | InMail messaging | Yes |
| `/features` | `app/features/page.tsx` | Feature showcase | No |
| `/termos` | `app/termos/page.tsx` | Terms of service | No |
| `/privacidade` | `app/privacidade/page.tsx` | Privacy policy | No |
| `/auth/callback` | `app/auth/callback/page.tsx` | OAuth callback handler | No |

### 4.2 Component Architecture

**File:** `frontend/app/components/`

48 components organized in three categories:

**Core UI Components:**
- `ThemeProvider.tsx` / `ThemeToggle.tsx` -- Dark/light theme with localStorage persistence
- `AuthProvider.tsx` -- Supabase auth context provider
- `AnalyticsProvider.tsx` -- Mixpanel analytics wrapper
- `Footer.tsx` -- Site-wide footer
- `InstitutionalSidebar.tsx` -- Institutional page sidebar

**Search Components:**
- `RegionSelector.tsx` -- Multi-state (UF) selection
- `CustomDateInput.tsx` -- Date range picker
- `EsferaFilter.tsx` -- Government sphere filter
- `MunicipioFilter.tsx` -- Municipality filter
- `OrgaoFilter.tsx` -- Agency filter
- `OrdenacaoSelect.tsx` -- Sort order selector
- `PaginacaoSelect.tsx` -- Items per page selector
- `CustomSelect.tsx` -- Generic styled select
- `StatusBadge.tsx` -- Bid status indicator
- `SavedSearchesDropdown.tsx` -- Recent searches dropdown

**Results & Display Components:**
- `LicitacoesPreview.tsx` -- Bid results list with plan-based blur
- `LicitacaoCard.tsx` -- Individual bid card
- `LoadingProgress.tsx` -- SSE-connected progress indicator
- `LoadingResultsSkeleton.tsx` -- Skeleton loading state
- `EmptyState.tsx` -- Zero results illustration

**User & Billing Components:**
- `UserMenu.tsx` -- Authenticated user dropdown
- `PlanBadge.tsx` -- Current plan indicator
- `QuotaBadge.tsx` / `QuotaCounter.tsx` -- Quota usage display
- `UpgradeModal.tsx` -- Plan upgrade prompt
- `Countdown.tsx` -- Trial countdown timer
- `MessageBadge.tsx` -- Unread message indicator
- `ComparisonTable.tsx` -- Plan comparison table
- `ValuePropSection.tsx` -- Value proposition display

**Landing Page Components** (`components/landing/`):
- `HeroSection.tsx` -- Landing page hero
- `HowItWorks.tsx` -- Process explanation
- `SectorsGrid.tsx` -- Sector showcase
- `DifferentialsGrid.tsx` -- Feature differentiators
- `StatsSection.tsx` -- Platform statistics
- `TestimonialsCarousel.tsx` -- Customer testimonials
- `DataSourcesSection.tsx` -- Data source logos
- `FinalCTA.tsx` -- Call-to-action
- `OpportunityCost.tsx` -- Opportunity cost calculator
- `BeforeAfter.tsx` -- Before/after comparison
- `LandingNavbar.tsx` -- Landing page navigation

**Reusable UI Primitives** (`components/ui/`):
- `GlassCard.tsx` -- Glassmorphism card
- `GradientButton.tsx` -- Gradient animated button
- `BentoGrid.tsx` -- Bento-style layout
- `Tooltip.tsx` -- Tooltip component

**Onboarding:**
- `ContextualTutorialTooltip.tsx` -- Shepherd.js tutorial integration

### 4.3 State Management

The frontend uses React hooks exclusively (no external state library):

- **Authentication state:** `AuthProvider.tsx` with React Context wrapping `@supabase/ssr`
- **Theme state:** `ThemeProvider.tsx` with localStorage persistence (`bidiq-theme` key)
- **Search state:** Local `useState` in `buscar/page.tsx` (~480+ lines)
- **Plan cache:** localStorage with 1-hour TTL to prevent instant UI downgrades on transient errors
- **Analytics:** Mixpanel via `AnalyticsProvider.tsx`

### 4.4 API Integration Layer

**File:** `frontend/app/api/`

The frontend uses Next.js API routes as a BFF (Backend-for-Frontend) proxy layer:

| Frontend Route | Backend Proxy Target | Purpose |
|---------------|---------------------|---------|
| `POST /api/buscar` | `POST ${BACKEND_URL}/buscar` | Main search proxy |
| `GET /api/buscar-progress` | SSE proxy | Progress streaming |
| `GET /api/me` | `GET ${BACKEND_URL}/me` | Profile proxy |
| `GET /api/health` | `GET ${BACKEND_URL}/health` | Health proxy |
| `GET /api/setores` | `GET ${BACKEND_URL}/setores` | Sectors proxy |
| `GET /api/download` | Local filesystem | Excel file serving |
| `GET /api/analytics` | `GET ${BACKEND_URL}/analytics` | Analytics proxy |
| Messages routes | `${BACKEND_URL}/...` | Messaging proxy |

**Key proxy behaviors** (`frontend/app/api/buscar/route.ts`):
- Auth header forwarding (line 62-66)
- 5-minute timeout (line 84-85)
- Retry logic: 2 attempts with 3s delay, only retries 503 (line 68-72)
- Excel file saved to temp filesystem with 60-minute TTL (line 180-204)
- `BACKEND_URL` required (no localhost fallback in production)

---

## 5. External Integrations

### 5.1 PNCP API

**File:** `backend/pncp_client.py`

**Base URL:** `https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao`

**Request parameters:**
- `dataInicial` / `dataFinal` -- Date range (yyyyMMdd format)
- `codigoModalidadeContratacao` -- Modality code (default: 6 = Pregao Eletronico)
- `uf` -- Optional state filter
- `pagina` / `tamanhoPagina` -- Pagination (default page size: 20)
- `situacaoCompra` -- Optional status filter

**Response normalization:** The `_normalize_item()` method (line 428-452) flattens nested `orgaoEntidade` and `unidadeOrgao` objects into top-level keys expected by downstream modules.

**Resilience features:**
- Sync client (`PNCPClient`) using `requests.Session` with `urllib3.Retry`
- Async client (`AsyncPNCPClient`) using `httpx.AsyncClient` with semaphore-based concurrency
- Date range chunking for ranges > 30 days (`_chunk_date_range()`)
- Max 500 pages per UF+modality combination (STORY-183 hotfix)
- Non-JSON response detection and retry
- Per-UF timeout: 90s; global fetch timeout: 4 minutes

### 5.2 OpenAI / LLM

**File:** `backend/llm.py`

**Summary Generation (GPT-4.1-nano):**
- Model: `gpt-4.1-nano`
- Temperature: 0.3
- Max tokens: 500
- Input: max 50 bids, descriptions truncated to 200 chars
- Output: Pydantic structured output via `client.beta.chat.completions.parse()`
- Post-validation: Checks for ambiguous deadline terminology
- Fallback: `gerar_resumo_fallback()` generates statistical summary without LLM

**Contract Classification (GPT-4o-mini, LLM Arbiter):**
- Model: `gpt-4o-mini` (configurable via `LLM_ARBITER_MODEL`)
- Temperature: 0 (deterministic)
- Max tokens: 1 (forces YES/NO)
- Used in filter pipeline for medium-confidence classifications

### 5.3 Stripe

**Files:** `backend/main.py:674-920`, `backend/webhooks/stripe.py`, `backend/routes/subscriptions.py`

**Integration points:**
- `POST /checkout` -- Creates Stripe Checkout Sessions for subscription purchases
- `POST /webhooks/stripe` -- Receives Stripe events with signature verification
- Billing period switching (monthly/annual) with pro-rata credit calculation
- Three subscription plans mapped to Stripe Price IDs

**Database sync pattern:**
- Webhook updates `user_subscriptions` table AND `profiles.plan_type` column
- This dual-write ensures the profile-based fallback always reflects current plan

### 5.4 Supabase

**File:** `backend/supabase_client.py`

**Usage:** Singleton client using service role key (admin privileges).

**Tables used (inferred from code):**
- `profiles` -- User profiles with `is_admin`, `plan_type`, `email`
- `user_subscriptions` -- Active subscriptions with Stripe IDs
- `plans` -- Available plans with Stripe price IDs
- `monthly_quota` -- Per-user, per-month search counts
- `search_sessions` -- Search history records
- `stripe_webhook_events` -- Webhook idempotency tracking (via SQLAlchemy)
- `conversations` / `messages` -- InMail messaging tables

**Auth integration:** Supabase Auth handles email/password + Google OAuth. JWTs are validated server-side via `supabase.auth.get_user(token)`.

---

## 6. Data Flow Diagrams

### 6.1 Main Search Pipeline

```
User (Browser)
    |
    | POST /api/buscar (Next.js BFF)
    |     + Authorization: Bearer <jwt>
    |     + body: { ufs, data_inicial, data_final, setor_id, termos_busca, ... }
    |
    v
Next.js API Route (/api/buscar/route.ts)
    |
    | POST ${BACKEND_URL}/buscar
    |     + Forward auth header
    |     + 5-min timeout
    |     + 2 retries (503 only)
    |
    v
FastAPI Backend (main.py:buscar_licitacoes)
    |
    |-- [1] Auth Check (require_auth -> auth.py)
    |       JWT cache (60s) -> Supabase Auth API
    |
    |-- [2] Role Check (_check_user_roles)
    |       Admin/Master bypass all limits
    |
    |-- [3] Rate Limit Check (rate_limiter.py)
    |       Redis -> in-memory fallback
    |
    |-- [4] Quota Check + Atomic Increment (quota.py)
    |       4-layer subscription resolution
    |       PostgreSQL RPC: check_and_increment_quota
    |
    |-- [5] Sector Configuration (sectors.py)
    |       Load keywords, exclusions, context_required
    |
    |-- [6] Term Parsing (term_parser.py)
    |       Comma-delimited phrases, stopword removal
    |       Term validation (filter.py:validate_terms)
    |
    |-- [7] PNCP Fetch (pncp_client.py)
    |       |-- Parallel: AsyncPNCPClient (multi-UF)
    |       |-- Sequential: PNCPClient (single-UF)
    |       |-- Multi-source: ConsolidationService (if enabled)
    |       Timeout: 4 minutes
    |
    |-- [8] Status Enrichment (status_inference.py)
    |       Infer bid status from dates
    |
    |-- [9] Filter Pipeline (filter.py)
    |       UF -> Status -> Esfera -> Modalidade -> Municipio -> Valor -> Keywords
    |       Min match floor with graceful degradation
    |
    |-- [10] Relevance Scoring (relevance.py)
    |        Score 0.0-1.0 for custom terms
    |
    |-- [11] Sorting (utils/ordenacao.py)
    |        By date, value, deadline, or relevance
    |
    |-- [12] LLM Summary (llm.py)
    |        GPT-4.1-nano structured output
    |        Fallback: statistical summary
    |        Post-validation: override hallucinated counts
    |
    |-- [13] Excel Generation (excel.py)
    |        Only if plan allows (maquina+)
    |        openpyxl with styled headers
    |
    |-- [14] Save Session (quota.py:save_search_session)
    |        Persist to search_sessions table
    |
    v
BuscaResponse (JSON)
    |
    | { resumo, licitacoes[], excel_base64, quota_used, quota_remaining,
    |   total_raw, total_filtrado, filter_stats, termos_utilizados, ... }
    |
    v
Next.js API Route
    |
    | Save Excel to temp file (60min TTL)
    | Generate download_id (UUID)
    |
    v
Browser
    |
    | Display results, summary, download button
```

### 6.2 SSE Progress Tracking

```
Browser
    |
    |-- [A] GET /api/buscar-progress/{search_id}  (SSE connection)
    |       Opens before POST /api/buscar
    |
    |-- [B] POST /api/buscar  (with same search_id)
    |
    v
Backend
    |
    |-- SSE Endpoint (GET /buscar-progress/{search_id})
    |       Waits up to 30s for tracker creation
    |       Streams ProgressEvents from asyncio.Queue
    |       Heartbeat every 30s
    |
    |-- Search Pipeline (POST /buscar)
    |       Creates ProgressTracker with search_id
    |       Emits events at each stage:
    |         connecting (3-8%)
    |         fetching (10-55%, per-UF granularity)
    |         filtering (60-70%)
    |         llm (75-90%)
    |         excel (92-98%)
    |         complete (100%)
    |
    v
Browser
    |
    | LoadingProgress component renders real-time bar
    | Fallback: calibrated time-based simulation if SSE fails
```

### 6.3 Stripe Subscription Flow

```
User clicks "Assinar" on /planos
    |
    v
POST /checkout?plan_id=maquina&billing_period=monthly
    |
    v
Backend creates Stripe Checkout Session
    | mode: subscription
    | success_url: /planos/obrigado?plan=maquina
    | cancel_url: /planos?cancelled=true
    |
    v
User redirected to Stripe Checkout page
    |
    v
Payment succeeds -> Stripe sends webhook
    |
    v
POST /webhooks/stripe
    |
    |-- Verify signature (STRIPE_WEBHOOK_SECRET)
    |-- Idempotency check (stripe_webhook_events table)
    |-- customer.subscription.updated:
    |       Update user_subscriptions.billing_period
    |       Invalidate Redis cache
    |-- invoice.payment_succeeded:
    |       Extend subscription expiry
    |       Sync profiles.plan_type
    |-- customer.subscription.deleted:
    |       Deactivate subscription
    |       Reset profiles.plan_type to free_trial
```

---

## 7. Infrastructure and Deployment

### 7.1 Railway Deployment

**Backend:**
- FastAPI served by Uvicorn
- Port from `PORT` env var (Railway convention)
- No Dockerfile found (likely using Railway Nixpacks auto-detection)

**Frontend:**
- Next.js in standalone mode (`output: 'standalone'` in `next.config.js`)
- `npm run build` creates `.next/standalone/`
- `npm start` runs `node .next/standalone/server.js`
- Post-build copies public and static assets

**Production URL:** `https://bidiq-frontend-production.up.railway.app/`

### 7.2 CI/CD Workflows

**File:** `.github/workflows/` (11 workflow files)

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| Backend CI | `backend-ci.yml` | Push/PR | Backend linting, tests |
| Tests | `tests.yml` | Push/PR | Frontend Jest tests with coverage |
| E2E | `e2e.yml` | Push/PR | Playwright browser tests |
| CodeQL | `codeql.yml` | Schedule/PR | Security scanning |
| Deploy | `deploy.yml` | Push to main | Production deployment |
| Staging Deploy | `staging-deploy.yml` | Push to develop | Staging deployment |
| Lighthouse | `lighthouse.yml` | Schedule | Performance auditing |
| Load Test | `load-test.yml` | Manual | Locust load testing |
| PR Validation | `pr-validation.yml` | PR | PR quality gates |
| Cleanup | `cleanup.yml` | Schedule | Resource cleanup |
| Dependabot Auto-merge | `dependabot-auto-merge.yml` | Dependabot PR | Auto-merge minor updates |

### 7.3 Environment Configuration

**Critical environment variables** (from code analysis):

| Variable | Required | Used By | Purpose |
|----------|----------|---------|---------|
| `OPENAI_API_KEY` | Yes | Backend | LLM summaries + arbiter |
| `SUPABASE_URL` | Yes | Both | Database connection |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Backend | Admin DB access |
| `SUPABASE_ANON_KEY` | Yes | Frontend | Client-side auth |
| `STRIPE_SECRET_KEY` | Yes | Backend | Payment processing |
| `STRIPE_WEBHOOK_SECRET` | Yes | Backend | Webhook validation |
| `BACKEND_URL` | Yes | Frontend | API proxy target |
| `FRONTEND_URL` | Yes | Backend | Stripe redirect URLs |
| `REDIS_URL` | Optional | Backend | Rate limiting, feature cache |
| `CORS_ORIGINS` | Optional | Backend | CORS configuration |
| `ADMIN_USER_IDS` | Optional | Backend | Admin user override |
| `ENABLE_NEW_PRICING` | Optional | Backend | Feature flag (default: true) |
| `LLM_ARBITER_ENABLED` | Optional | Backend | Feature flag (default: true) |
| `ENABLE_MULTI_SOURCE` | Optional | Backend | Feature flag (default: false) |
| `LOG_LEVEL` | Optional | Backend | Logging verbosity |
| `ENVIRONMENT` | Optional | Backend | Production mode detection |
| `NEXT_PUBLIC_APP_NAME` | Optional | Frontend | Branding override |
| `NEXT_PUBLIC_SUPABASE_URL` | Yes | Frontend | Client Supabase URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Yes | Frontend | Client Supabase key |

---

## 8. Security Analysis

### 8.1 Authentication Security

**Strengths:**
- Supabase JWT validation with server-side token verification
- Token cache prevents repeated remote validation (DDoS resilience)
- No token content logged (Issue #168 remediation)
- `HTTPBearer` scheme with explicit `auto_error=False`

**Concerns:**
- Token cache keyed on `hash(token[:16])` -- potential collision risk (MEDIUM). A SHA-256 hash of the full token would be safer.
- 60s cache TTL means a revoked token remains valid for up to 60 seconds
- No token rotation or refresh token flow visible in backend code

### 8.2 Input Validation

**Strengths:**
- UUID v4 validation for all user IDs (Issue #203)
- Plan ID pattern validation
- Search query sanitization with character allowlist
- SQL pattern escaping (`%`, `_` removal)
- Modalidade codes validated against Lei 14.133/2021

**Concerns:**
- Admin search input sanitization in `admin.py:37+` is a custom implementation rather than parameterized queries (MEDIUM)
- The `SAFE_SEARCH_PATTERN` regex explicitly excludes `$` but allows quotes and parentheses

### 8.3 Log Sanitization (Issue #168)

**File:** `backend/log_sanitizer.py`

Comprehensive PII masking system:
- Email: `u***@domain.com`
- User IDs: `550e8400-***`
- API keys: `sk-***cdef`
- Tokens: `eyJ***[JWT]`
- IPs: `192.168.x.x`
- Passwords: `[PASSWORD_REDACTED]`
- Auto-detection via regex patterns
- `SanitizedLogAdapter` for automatic sanitization
- Production-enforced minimum INFO log level

### 8.4 CORS Configuration

**File:** `backend/config.py:222-325`

- Development: `localhost:3000` and `127.0.0.1:3000`
- Production: Hardcoded Railway URLs + any custom `CORS_ORIGINS`
- Wildcard (`*`) explicitly rejected with warning
- Production environment auto-detected via Railway env vars

### 8.5 Stripe Webhook Security

- Signature verification via `stripe.Webhook.construct_event()`
- Missing `stripe-signature` header returns 400
- Invalid signature returns 400
- Idempotency via database event tracking

### 8.6 Known Security Gaps

1. **No CSRF protection** on the API proxy layer (MEDIUM) -- The Next.js BFF forwards requests without CSRF tokens. Mitigated by JWT auth requirement.
2. **Service role key in backend** -- The backend uses `SUPABASE_SERVICE_ROLE_KEY` for all DB operations. A more granular approach with RLS policies would be safer.
3. **In-memory token cache not distributed** -- Token revocation only takes effect after cache TTL on the specific instance.

---

## 9. Technical Debt Inventory

### 9.1 Critical (Must Fix)

| # | Issue | Location | Impact | Effort |
|---|-------|----------|--------|--------|
| C1 | **In-memory state prevents horizontal scaling** | `backend/progress.py:98` (`_active_trackers` dict) | SSE progress breaks if more than 1 instance deployed. Search state is lost on restart. | HIGH -- requires Redis-backed pub/sub or external queue |
| C2 | **Monolithic main.py (1,959 lines)** | `backend/main.py` | Contains 20+ endpoints, business logic, helper functions, billing handlers. Difficult to maintain and test in isolation. | MEDIUM -- extract into separate router modules |
| C3 | **Dual ORM/DB access pattern** | `backend/supabase_client.py` + `backend/database.py` (SQLAlchemy) | Two competing database access patterns: Supabase Python client (most endpoints) and SQLAlchemy (Stripe webhooks, models). Schema drift risk. | HIGH -- consolidate on one pattern |
| C4 | **Test failures (pre-existing)** | Backend: 21 failures; Frontend: 70 failures | CI pipeline failures mask new regressions. Quality gate is non-functional. | MEDIUM -- fix or skip/mark expected failures |

### 9.2 High (Should Fix Soon)

| # | Issue | Location | Impact | Effort |
|---|-------|----------|--------|--------|
| H1 | **Synchronous PNCP client in async context** | `backend/pncp_client.py:67-557` (`PNCPClient` uses `requests`, not `httpx`) | The sync `PNCPClient` blocks the event loop when used as fallback. Only `AsyncPNCPClient` is non-blocking. | MEDIUM -- remove sync client or wrap in executor |
| H2 | **Excel file stored in temp filesystem** | `frontend/app/api/buscar/route.ts:180-204` | Temp files are not shared across instances. 60-minute TTL via `setTimeout` is unreliable. Files survive process restart. | MEDIUM -- use object storage or stream directly |
| H3 | **No database migrations tracked in repo** | No `migrations/` directory found | Schema changes rely on manual Supabase dashboard operations. Risk of environment drift. | LOW -- add Supabase migration files |
| H4 | **Business logic in main.py helper functions** | `backend/main.py:392-523` (`_check_user_roles`, `_is_admin`, `_has_master_access`, `_get_master_quota_info`) | Core authorization logic co-located with route handlers. Cannot be unit tested independently. | LOW -- extract to `authorization.py` |
| H5 | **Development dependencies in production requirements** | `backend/requirements.txt:37-50` | pytest, ruff, mypy, locust, faker all installed in production. Increases attack surface and image size. | LOW -- split into requirements-dev.txt |

### 9.3 Medium (Plan to Fix)

| # | Issue | Location | Impact | Effort |
|---|-------|----------|--------|--------|
| M1 | **No request ID / correlation ID** | Throughout backend | Cannot trace a request across log entries or between frontend proxy and backend. Debugging production issues is difficult. | LOW |
| M2 | **Token cache uses `hash()` of token prefix** | `backend/auth.py:45` | Python's `hash()` is not cryptographically secure and varies between runs. Potential for collisions on long-running instances. | LOW |
| M3 | **Rate limiter in-memory store has no max size** | `backend/rate_limiter.py:84-89` | Memory grows unbounded with unique user IDs in the in-memory fallback. Garbage collection only removes entries > 60s old. | LOW |
| M4 | **Hardcoded plan capabilities** | `backend/quota.py:62-95` | Plan definitions are in Python code, not database. Adding a new plan requires a code deployment. | LOW -- move to plans table |
| M5 | **Google API credentials handling** | `backend/requirements.txt:29-33` | Google Sheets integration adds 4 heavy dependencies. OAuth token storage mechanism not visible. | LOW |
| M6 | **`datetime.utcnow()` deprecated** | Multiple files | Python 3.12 deprecates `datetime.utcnow()`. Should use `datetime.now(timezone.utc)` consistently. | LOW |
| M7 | **Frontend coverage below threshold** | `frontend/` (49.46% vs 60% target) | CI coverage gate fails. Coverage gap primarily in LoadingProgress, RegionSelector, SavedSearchesDropdown, AnalyticsProvider. | MEDIUM |
| M8 | **No API versioning** | `backend/main.py` | All endpoints are unversioned. Breaking changes require coordinated frontend/backend deployments. | LOW |

### 9.4 Low (Nice to Have)

| # | Issue | Location | Impact | Effort |
|---|-------|----------|--------|--------|
| L1 | **No OpenAPI schema validation in tests** | Backend tests | API contract drift between backend and frontend could go unnoticed. | LOW |
| L2 | **Emoji usage in production logs** | `backend/pncp_client.py:525,533` | Log aggregators may not render emojis correctly. | TRIVIAL |
| L3 | **Inline CSS in layout.tsx** | `frontend/app/layout.tsx:62-77` | Theme initialization script uses inline styles. Should use CSS variables exclusively. | TRIVIAL |
| L4 | **No request/response logging middleware** | Backend | No centralized request logging (duration, status code, path). Each endpoint logs individually. | LOW |
| L5 | **Unused imports in main.py** | `backend/main.py:1694` | `from filter import match_keywords, KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO` imported inside diagnostic loop. | TRIVIAL |
| L6 | **No health check for Redis** | `backend/main.py:162-229` | Health endpoint checks Supabase and OpenAI but not Redis. Rate limiting silently degrades. | LOW |

---

## 10. Recommendations

### 10.1 Immediate (Next Sprint)

1. **Extract main.py into router modules** (C2) -- Split the 1,959-line main.py into:
   - `routes/search.py` -- `/buscar` and `/buscar-progress` endpoints
   - `routes/auth_routes.py` -- `/me`, `/change-password`
   - `routes/billing.py` -- `/checkout`, `/plans`, plan activation
   - `routes/sessions.py` -- `/sessions`
   - `services/authorization.py` -- Role checking functions
   This alone would improve maintainability significantly.

2. **Fix CI pipeline** (C4) -- Mark known-failing tests with `@pytest.mark.skip(reason="pre-existing")` or fix them. A green CI is prerequisite for safe deployments.

3. **Add request correlation IDs** (M1) -- FastAPI middleware that generates a UUID per request and propagates it through all log entries. Essential for production debugging.

### 10.2 Short-Term (1-2 Sprints)

4. **Migrate SSE state to Redis** (C1) -- Replace `_active_trackers` dict with Redis pub/sub for progress tracking. This is the single largest blocker to horizontal scaling.

5. **Consolidate database access** (C3) -- Choose either Supabase Python client OR SQLAlchemy. The Stripe webhook handler should use the same pattern as the rest of the application.

6. **Split requirements** (H5) -- Create `requirements.txt` (production) and `requirements-dev.txt` (development). Reduces production image size by ~200MB.

### 10.3 Medium-Term (1-3 Months)

7. **API versioning** (M8) -- Introduce `/api/v1/` prefix for all backend endpoints. The BFF proxy layer makes this relatively low-risk.

8. **Move plan definitions to database** (M4) -- Store plan capabilities in the `plans` table. Enables plan changes without code deployments.

9. **Replace synchronous PNCPClient** (H1) -- The sync client exists only as a fallback. Remove it entirely and use `AsyncPNCPClient` exclusively.

10. **Object storage for Excel files** (H2) -- Use Supabase Storage or S3 for generated Excel files instead of temp filesystem. Enables multi-instance deployments.

### 10.4 Architectural Evolution

11. **Consider event-driven architecture** for long-running searches. The current synchronous request-response model with 5-minute timeouts is fragile. A job queue (Redis + Celery or similar) would allow:
    - Search submission returns immediately with job ID
    - Progress updates via SSE connected to job state
    - Results fetched when job completes
    - Automatic retry on failure

12. **Database migration tracking** -- Adopt Supabase CLI migrations (`npx supabase migration new`) to version-control all schema changes. Currently, schema state is not reproducible from the repository alone.

---

*This document was generated by @architect (Aria) based on analysis of the production codebase at commit `808cd05` on branch `main`. All file paths and line numbers reference the state of the code as of 2026-02-11.*
