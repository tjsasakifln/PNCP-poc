# Architecture Detail — SmartLic Backend & Frontend

## Backend Architecture (backend/)

**Core Modules (65+ files):**

| Category | Modules | Purpose |
|----------|---------|---------|
| **Entry** | `main.py`, `config.py`, `schemas.py` | App setup, env config, Pydantic models |
| **Search Pipeline** | `search_pipeline.py`, `consolidation.py`, `search_context.py`, `search_state_manager.py` | Multi-source orchestration, state machine |
| **Data Sources** | `pncp_client.py`, `portal_compras_client.py`, `compras_gov_client.py` + 4 others in `clients/` | PNCP, PCP v2, ComprasGov v3 |
| **Filtering** | `filter.py`, `filter_stats.py`, `term_parser.py`, `synonyms.py`, `status_inference.py` | Keyword matching, density scoring |
| **AI/LLM** | `llm.py`, `llm_arbiter.py`, `relevance.py`, `viability.py` | Classification, summaries, viability |
| **Cache** | `search_cache.py`, `cache.py`, `redis_client.py`, `redis_pool.py` | Two-level cache (InMemory + Supabase), SWR |
| **Auth** | `auth.py`, `authorization.py`, `oauth.py`, `quota.py` | Supabase auth, RLS, plan quotas |
| **Billing** | `services/billing.py`, `webhooks/stripe.py` | Stripe subscriptions, webhooks |
| **Jobs** | `job_queue.py`, `cron_jobs.py` | ARQ background processing |
| **Monitoring** | `metrics.py`, `telemetry.py`, `health.py`, `audit.py` | Prometheus, OpenTelemetry, Sentry |
| **Output** | `excel.py`, `google_sheets.py`, `report_generator.py` | Excel, Google Sheets export |
| **Feedback** | `feedback_analyzer.py` | User feedback patterns, bi-gram analysis |
| **Sectors** | `sectors.py`, `sectors_data.yaml` | 15 sector definitions + keywords |
| **Email** | `email_service.py`, `templates/emails/` | Transactional emails via Resend |
| **Progress** | `progress.py` | SSE progress tracking (asyncio.Queue) |
| **Routes** | 19 modules in `routes/` | All API endpoints |

## API Routes (49 endpoints across 19 modules)

| Module | Key Endpoints |
|--------|--------------|
| `search.py` | `POST /buscar`, `GET /buscar-progress/{id}` (SSE), `GET /v1/search/{id}/status`, `POST /v1/search/{id}/retry` |
| `pipeline.py` | `POST/GET/PATCH/DELETE /pipeline`, `GET /pipeline/alerts` |
| `billing.py` | `GET /plans`, `POST /checkout`, `POST /billing-portal`, `GET /subscription/status` |
| `user.py` | `GET /me`, `POST /change-password`, `GET /trial-status`, `PUT/GET /profile/context` |
| `analytics.py` | `GET /summary`, `GET /searches-over-time`, `GET /top-dimensions`, `GET /trial-value` |
| `feedback.py` | `POST/DELETE /feedback`, `GET /admin/feedback/patterns` |
| `health.py` | `GET /health/cache` |
| `onboarding.py` | `POST /first-analysis` |
| `sessions.py` | `GET /sessions` |
| `messages.py` | `POST/GET /conversations`, `POST /{id}/reply`, `PATCH /{id}/status` |
| `auth_oauth.py` | `GET /google`, `GET /google/callback`, `DELETE /google` |
| `admin_trace.py` | `GET /search-trace/{search_id}` |
| Others | Plans, exports, features, subscriptions, emails |

## Frontend Architecture (frontend/app/)

**22 Pages:**

| Route | Purpose |
|-------|---------|
| `/` | Landing page |
| `/login`, `/signup` | Authentication |
| `/auth/callback` | OAuth callback |
| `/recuperar-senha`, `/redefinir-senha` | Password reset |
| `/onboarding` | 3-step wizard (CNAE -> UFs -> Confirmacao) |
| `/buscar` | **Main search page** — filters, results, SSE progress |
| `/dashboard` | User dashboard with analytics |
| `/historico` | Search history |
| `/pipeline` | Opportunity pipeline (kanban) |
| `/mensagens` | Messaging system |
| `/conta` | Account settings |
| `/planos`, `/planos/obrigado` | Pricing + thank you |
| `/pricing`, `/features` | Marketing pages |
| `/ajuda` | Help center |
| `/admin`, `/admin/cache` | Admin dashboards |
| `/termos`, `/privacidade` | Legal pages |

**33 Components** in `app/buscar/components/` + `components/`:
- Search: `SearchForm`, `SearchResults`, `FilterPanel`, `UfProgressGrid`
- Resilience: `CacheBanner`, `DegradationBanner`, `PartialResultsPrompt`, `SourcesUnavailable`, `ErrorDetail`
- AI: `LlmSourceBadge`, `ViabilityBadge`, `FeedbackButtons`, `ReliabilityBadge`
- Billing: `PlanCard`, `PlanToggle`, `PaymentFailedBanner`, `CancelSubscriptionModal`
- Loading: `EnhancedLoadingProgress`, `LoadingProgress`

**API Proxies** (`app/api/`): buscar, download, analytics, admin, feedback, trial-status, user, plans, pipeline, sessions, etc.
