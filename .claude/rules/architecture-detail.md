# Architecture Detail — SmartLic Backend & Frontend

## Backend Architecture (backend/)

**Scale:** ~59 top-level `.py` files + ~150 submodule files across packages. Decomposed via DEBT-302 (schemas/), DEBT-305 (jobs/), DEBT-107 (startup/) — façades preserve legacy imports.

**Module Map (18 functional modules — see `_reversa_sdd/code-analysis.md` for full breakdown):**

| Category | Modules / Packages | Purpose |
|----------|-------------------|---------|
| **Entry** | `main.py`, `startup/` (app_factory, routes, lifespan, middleware_setup, exception_handlers, sentry, state, endpoints), `config.py`, `feature_flags.py` | App bootstrap, router registration, lifespan tasks. SYS-020 keeps `main.py` <30 LOC. |
| **Schemas** | `schemas/` package (common, search, user, billing, admin, pipeline, feedback, messages, health, export, stats, contract, share) | Pydantic v2 BaseModels — 88 classes. Source-of-truth for OpenAPI + STORY-2.1 codegen → `frontend/app/api-types.generated.ts`. JSON Schema canary in `contracts/schemas/pncp_search_response.schema.json`. |
| **Search Pipeline** | `search_pipeline.py`, `search_state_manager.py`, `search_context.py`, `models/search_state.py`, `pipeline/` (budget, cache_manager, helpers, tracing, worker, stages/), `consolidation/` (dedup, source_merger, source_pipeline) | 7-stage state machine (CRIT-003) with 11 explicit states. Time budget waterfall (STORY-4.4) asserted in `tests/test_timeout_invariants.py`. 5-layer dedup engine. |
| **Ingestion / DataLake (Layer 1 — primary data source)** | `ingestion/` (config, scheduler, crawler, contracts_crawler, transformer, loader, checkpoint, enricher), `datalake_query.py` | ETL: `pncp_raw_bids` (~1.5M rows @ 400d retention, STORY-OBS-001), `pncp_supplier_contracts` (~2M+ rows, 3x/wk crawl, drives SEO inbound), `enriched_entities` (BrasilAPI), `indice_municipal` (IBGE). `search_datalake` RPC <100ms p95. |
| **Filter / LLM / Viability** | `filter/` package (pipeline, keywords, density, term_parser, synonyms, status_inference, stats), `llm.py` (executive summaries), `llm_arbiter/` package (classification, zero_match, async_runtime, batch_api, prompt_builder), `relevance.py`, `viability.py`, `sectors.py`, `sectors_data.yaml` (20 sectors) | Keyword density tiers + GPT-4.1-nano arbiter for zero-match. 4-factor viability scoring. SLA: precision ≥85%, recall ≥70%. |
| **Cache (passive — warming deprecated 2026-04-18)** | `cache/` (manager, cascade, swr, _ops, admin, enums), `redis_pool.py`, `redis_client.py`, `search_cache.py` | L1 InMemoryCache LRU 10k entries + L2 Redis (4h) + Supabase `search_results_cache` (24h, pg_cron cleanup). SWR per-request reactive. STORY-CIG-BE-cache-warming-deprecate removed proactive jobs (DataLake p95 <100ms made pre-population pure waste). |
| **Auth / Authorization / OAuth** | `auth.py` (JWT 3-strategy: JWKS ES256 > PEM > HS256, L1 LRU 60s + L2 Redis 5min), `authorization.py` (admin/master + ADMIN_USER_IDS env), `oauth.py` (Google Sheets — Fernet AES-256 refresh tokens) | Defense-in-depth: RLS + service-role bypass + explicit `.eq("user_id")` (ISSUE-021 pattern). |
| **Billing / Quota / Stripe** | `services/billing.py`, `quota/` (quota_core, quota_atomic, plan_enforcement, plan_auth, session_tracker), `webhooks/stripe.py`, `webhooks/handlers/` (checkout, subscription, invoice, founding) | 9 plans, 12 Stripe webhook events with `events_processed` idempotency, 30s timeout, signature gating. Atomic quota via `check_and_increment_quota_atomic` RPC. "Fail to last known plan" never falls back to free_trial on transient DB error. |
| **Pipeline (Kanban)** | `routes/pipeline.py`, `schemas/pipeline.py` | 5-stage CRUD with optimistic locking (STORY-307). Trial cap 5 items (`TRIAL_PAYWALL_MAX_PIPELINE`). Read-only mode for trial-expired (STORY-265 AC15). Distinct from `backend/pipeline/` (search stages). |
| **Jobs / Cron** | `jobs/queue/` (config, jobs, search, result_store, pool, redis_pool, worker, definitions), `jobs/cron/` (canary, billing, notifications, session_cleanup, scheduler, cron_monitor, pncp_canary, llm_batch_poll, new_bids_notifier, indice_municipal, seo_snapshot, trial_emails, trial_risk_detection), `cron/` (cache, billing, health, notifications, pncp_status, _loop), `job_queue.py`, `cron_jobs.py` (façades) | ARQ worker (PROCESS_TYPE=worker) with 7 base functions + N ingestion functions conditional. 9 ARQ cron schedules + 19 lifespan loops with Redis distributed locks. |
| **Routes** | `routes/` — **71 router files**, **65 registered** in `startup/routes.py::_v1_routers`, **187 endpoints**. Includes 18 SEO programmatic routers (`*_publicos.py`, `observatorio.py`, `blog_stats.py`, `dados_publicos.py`), 5 sitemap routers, 8+ admin routers (admin, admin_trace, admin_cron, admin_llm_cost, slo, seo_admin, feature_flags) | Tag-grouped, mostly authenticated. Public: observatório, sitemaps, calculadora, comparador, lead-capture, blog, sectors_public, alertas_publicos, share GET, emails/unsubscribe, trial-emails/webhook, health. |
| **Output / Exports** | `excel.py` (openpyxl, header verde + 11 cols + totals), `google_sheets.py` (OAuth user-scoped + batchUpdate API v4), `pdf_generator_edital.py` (ReportLab A4 1-page per bid + trial watermark) | Trial = paywall preview Excel + watermarked PDF. Paid = full + Google Sheets. |
| **Messages / Feedback** | `routes/messages.py`, `routes/feedback.py`, `feedback_analyzer.py` | InMail support threads (4-state lifecycle). Classification feedback loop (verdict + bi-gram analysis for FP exclusion suggestions). |
| **Onboarding / Analytics** | `routes/onboarding.py`, `routes/analytics.py`, `utils/cnae_mapping.py` | 3-step wizard → first-analysis auto-dispatch (GTM-004 TTV <5min). Personal dashboard with 6 aggregation endpoints. Tour Shepherd.js telemetry. |
| **Admin** | `admin.py` (1132 LOC — 17 endpoints user CRUD + cache + reconciliation + SLA + trial metrics + at-risk), `routes/admin_*.py`, `routes/feature_flags.py` (runtime toggle), `routes/slo.py` | Admin role boolean (LGPD-flagged for granular RBAC future). Sanitized search inputs (Issue #205). |
| **SEO Programmatic / Observatory** | 18 routers in `routes/` (observatorio, blog_stats, sitemap_*, empresa_publica, orgao_publico, contratos_publicos, dados_publicos, municipios_publicos, itens_publicos, compliance_publicos, indice_municipal, alertas_publicos, sectors_public, stats_public, calculadora, comparador, daily_digest, weekly_digest) — ~8.300 LOC | Public, no-auth. Drives organic inbound. ISR `revalidate=3600` (alignment fix SEN-FE-001). 4 dynamic XML sub-sitemaps + index. |
| **Email Templates / Service** | `templates/emails/` (15 templates: base, trial 6-step STORY-321, billing, dunning, welcome, welcome_subscriber, digest, alert_digest, quota, day3_activation, share_activation, referral_*, panorama_t1_delivery, boleto_reminder), `email_service.py` | Resend SDK + verified domain `smartlic.tech` from `tiago@smartlic.tech` + reply-to `tiago.sasaki@gmail.com`. HMAC verify on `/trial-emails/webhook` is currently a gap (security TODO). |
| **Cross-cutting / Observability** | `metrics.py` (Prometheus), `telemetry.py` (OpenTelemetry), `audit.py`, `log_sanitizer.py` (PII masking — Issue #168), `health.py`, `progress.py` (asyncio.Queue SSE), `rate_limiter.py` (Redis token bucket), `supabase_client.py` (CB + sb_execute) | Sentry + Mixpanel + Prometheus + OTel layered. pg_cron health monitor (STORY-1.1 hourly Sentry alert if >25h stale). |

## API Routes (187 endpoints across 65 registered routers)

Routers registered in `startup/routes.py::register_routes`:
- **`/v1/*` prefix** (auto): 60 routers — search, pipeline, billing, user, analytics, alerts, messages, onboarding, feedback, sessions, organizations, partners, referral, founding, conta, trial_extension, MFA, plans, share, lead_capture, comparador, calculadora, observatorio, blog_stats, 18 SEO `*_publicos`, 5 sitemap routers, etc.
- **`/v1/admin/*` self-prefixed**: admin, admin_trace, admin_cron, admin_llm_cost, slo
- **Root**: `/health/live`, `/health/ready`, `/sources/health` (health_core for Railway probes)
- **Root**: `/webhooks/stripe` (DEBT-324 single-registration; configure Stripe Dashboard for `POST /webhooks/stripe`, NOT `/v1/webhooks/stripe`)

| Module (sample of high-traffic) | Key Endpoints |
|--------|--------------|
| `search/` (subpkg + state.py + sse + retry) | `POST /buscar` (202 async via `SEARCH_ASYNC_ENABLED`), `GET /buscar-progress/{id}` (SSE), `GET /v1/search/{id}/{status,timeline,results,zero-match}`, `POST /v1/search/{id}/{regenerate-excel,retry,cancel}` |
| `pipeline.py` | `POST/GET/PATCH/DELETE /v1/pipeline`, `GET /v1/pipeline/alerts` |
| `billing.py` + `subscriptions.py` + `founding.py` + `conta.py` + `trial_extension.py` | `GET /v1/plans`, `POST /v1/checkout`, `POST /v1/billing-portal`, `GET /v1/subscription/status`, `POST /v1/billing/setup-intent`, `POST /v1/founding/checkout`, `POST /v1/api/subscriptions/{cancel,update-billing-period,cancel-feedback}`, `POST /v1/conta/cancelar-trial`, `POST /v1/trial/extend` |
| `user.py` (888 LOC — 13 endpoints) | `/me`, `/change-password`, `/trial-status`, `/profile/{context,completeness,alert-preferences}`, `/me/export` (LGPD), `/trial/exit-survey` |
| `analytics.py` | `/summary`, `/searches-over-time`, `/top-dimensions`, `/trial-value`, `/new-opportunities` (DEBT-127), `/track-cta` |
| `feedback.py` | `POST /v1/feedback` (upsert + rate limit), `DELETE /v1/feedback/{id}` (LGPD), `GET /v1/admin/feedback/patterns` |
| `health.py` + `health_core.py` | 11 endpoints (liveness, readiness, sources, cache, status incidents, uptime-history) |
| `messages.py` | 6 endpoints conversation CRUD + replies + status + unread-count |
| `onboarding.py` | `POST /v1/first-analysis`, `POST /v1/onboarding/tour-event` |
| `auth_*.py` + `mfa.py` + `auth_oauth.py` | signup, check-email, validate-signup-email, resend-confirmation, status, MFA recovery, Google OAuth |
| 18 `*_publicos.py` + observatorio + blog_stats + sitemap_*  | SEO programmatic public read endpoints (no auth) — drives 10k+ programmatic page views |

For full endpoint inventory, see `_reversa_sdd/openapi-summary.md`.

## Frontend Architecture (frontend/app/)

**Scale:** ~25 core authenticated/marketing pages + **10k+ programmatic SEO pages** (ISR `revalidate=3600`) generated from dynamic routes (`/observatorio/[slug]`, `/cnpj/[cnpj]`, `/orgaos/[slug]`, `/municipios/[slug]`, `/licitacoes/[setor]`, `/contratos/[setor]/[uf]`, `/blog/{contratos,licitacoes,panorama,programmatic}/[setor]`, `/alertas-publicos/[setor]/[uf]`, `/indice-municipal/[municipio-uf]`, `/compliance/[cnpj]`).

### Core pages (auth + marketing)

| Route | Purpose | Render |
|-------|---------|--------|
| `/` | Landing | SSG |
| `/login`, `/signup`, `/auth/callback`, `/recuperar-senha`, `/redefinir-senha` | Authentication | CSR |
| `/onboarding` | 3-step wizard (CNAE → UFs → confirmation + first-analysis dispatch) | CSR auth-gated |
| `/buscar` | **Main search page** — filters, SSE progress, results grid, paywall preview | CSR auth-gated |
| `/dashboard` | Personal dashboard (analytics) | CSR auth-gated |
| `/historico` | Search history | CSR auth-gated |
| `/pipeline` | Kanban (desktop) / mobile tabs | CSR auth-gated |
| `/mensagens` | InMail support inbox | CSR auth-gated |
| `/conta` | Account settings + billing portal + MFA + danger zone | CSR auth-gated |
| `/planos`, `/planos/obrigado`, `/pricing`, `/features` | Pricing + post-checkout + marketing | SSG / CSR |
| `/ajuda` | Help center (search included) | SSG |
| `/admin/*` (cache, feature-flags, emails, metrics, partners, seo, slo) | Admin dashboards | CSR + admin role |
| `/termos`, `/privacidade` | Legal | SSG |

### SEO programmatic (10k+ pages, ISR)

Driven by DataLake (`pncp_raw_bids` 400d + `pncp_supplier_contracts` 2M+ rows). 4 sub-sitemaps + index. JSON-LD structured data (FAQPage, Organization, ItemList).

| Pattern | Volume |
|---------|--------|
| `/observatorio/[slug]` + `/observatorio/raio-x-{setor,municipio,orgao,alerta}/[id]` | thousands |
| `/cnpj/[cnpj]`, `/fornecedores/[cnpj]` | per supplier in DataLake |
| `/orgaos/[slug]`, `/municipios/[slug]` | per public agency / municipality |
| `/licitacoes/[setor]`, `/contratos/[setor]/[uf]`, `/contratos/orgao/[cnpj]` | sector × UF combinatorial |
| `/blog/{contratos,licitacoes,panorama,programmatic}/[setor]`, `/blog/licitacoes/cidade/[city]` | sector + city programmatic |
| `/alertas-publicos/[setor]/[uf]` | preview alerts |
| `/indice-municipal/[municipio-uf]` | municipal scoring |

### Components

**~72 components** across `components/` + `app/buscar/components/`:

- **Component library** (`components/ui/`): button, Input, Label, Modal, Pagination, EmptyState, ErrorMessage, ErrorStateWithRetry, ViabilityBadge, AnimateOnScroll, CurrencyInput + Storybook stories
- **Search-specific** (`app/buscar/components/`, ~33 files): SearchForm, SearchResults, FilterPanel, UfProgressGrid, CacheBanner, DegradationBanner, PartialResultsPrompt, SourcesUnavailable, ErrorDetail, LlmSourceBadge, ViabilityBadge, FeedbackButtons, ReliabilityBadge, EnhancedLoadingProgress
- **Billing** (`components/billing/`): PlanCard, PlanToggle, PaymentFailedBanner, CancelSubscriptionModal, TrialUpsellCTA
- **Layout / Cross-cutting**: NavigationShell, Sidebar, BottomNav, MobileDrawer, PageHeader, AuthLoadingScreen, PageErrorBoundary, ErrorBoundary, SWRProvider, AuthProvider
- **Onboarding / Trial**: OnboardingTourButton, ProfileCompletionPrompt, ProfileCongratulations, ProfileProgressBar, TrialProgressBar, TrialExitSurveyModal
- **Tour** (`components/tour/`): Tour component (Shepherd.js wrapper) + step utilities
- **Pipeline-specific** (`app/pipeline/`): PipelineKanban (lazy via `next/dynamic`), PipelineColumn, PipelineCard, PipelineMobileTabs, ReadOnlyKanban

### API Proxies (`app/api/`)

Next.js route handlers proxying backend: `buscar`, `download`, `analytics`, `admin`, `feedback`, `trial-status`, `user`, `plans`, `pipeline`, `sessions`, `messages`, `onboarding`, `share`, `auth`, `setores`, `empresa`, `comparador`, `calculadora`, sitemap-* etc.

### Strategic context

**Production v0.5 — pre-revenue beta with paid trials.** SEO programmatic (10k+ ISR pages) is the primary inbound funnel; `/buscar` is the activation surface; `/pipeline` is the retention surface. Time-to-first-value <5min via `/onboarding` → first-analysis auto-dispatch (GTM-004).

For 18-module deep-dive, ERD, C4 diagrams, OpenAPI inventory, user stories, and Spec Impact Matrix, see `_reversa_sdd/`.
