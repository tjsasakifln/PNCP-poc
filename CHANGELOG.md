# Changelog

All notable changes to SmartLic will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.2] - 2026-02-27 - RELIABILITY SPRINT COMPLETE

### Added — Reliability Architecture
- **Async search 202 Accepted pattern** (STORY-292) — non-blocking search with polling
- **Redis state externalization** (STORY-294) — multi-worker state sharing
- **Progressive results delivery** (STORY-295) — meta-search with incremental updates
- **Bulkhead per source** (STORY-296) — concurrency + timeout isolation per data source
- **SSE Last-Event-ID resumption** (STORY-297) — reconnect without data loss
- **Unified error UX** (STORY-298) — SearchStateManager for consistent error handling
- **SLOs + alerting dashboard** (STORY-299) — admin SLO monitoring with alerts
- **Email alert system** (STORY-301) — CRUD alerts, cron execution, dedup, unsubscribe

### Changed — Security & Observability
- **Security hardening** (STORY-300) — CSP headers, error sanitization, LGPD compliance
- **Supabase circuit breaker** (STORY-291) — eliminates database SPOF
- **Event loop unblock** (STORY-290) — offload sync Supabase calls to thread pool
- **CI/CD pipeline fix** (STORY-293) — restore green builds

### Changed — Pricing & Billing
- **Repricing** (STORY-277) — R$1.999/mes → R$397/mes (mensal), R$357 (semestral), R$317 (anual)
- **Trial duration** — 7 days → 30 days (beta period)
- **Boleto + PIX** (STORY-280) — additional payment methods via Stripe

### Documentation
- **STORY-302** — Documentation + stale cleanup (this release)
- Updated pricing across CLAUDE.md, PRD.md, README.md, system-architecture.md
- Updated cost-analysis.md with new pricing margins

### Testing
- Backend: 169 test files, 5131+ tests passing, 0 failures
- Frontend: 135 test files, 2681+ tests passing, 0 failures
- E2E: 60 critical user flow tests

---

## [0.5.1] - 2026-02-26 - GTM Quick Wins (STORY-284)

### Fixed
- **Email links** — `/precos` replaced with `/planos` in billing and quota email templates
- **Help page** — Updated payment FAQ to reflect Boleto support and PIX status

### Changed
- **CSP documentation** — Documented `unsafe-eval`/`unsafe-inline` as accepted risk in `next.config.js`
- **`.env.example`** — Added `SUPABASE_JWT_SECRET` with documentation

### Removed
- **Deprecated banners** — Removed `DegradationBanner`, `CacheBanner`, `OperationalStateBanner` (replaced by `DataQualityBanner`)

### Verified
- **SENTRY_DSN** — Confirmed active in Railway for both backend and frontend services

---

## [0.5.0] - 2026-02-20 - GTM RESILIENCE COMPLETE

### Added — Resilience & Observability
- **Prometheus metrics exporter** — 11 metrics (histograms, counters, gauges) at `/metrics`
- **OpenTelemetry distributed tracing** — spans across search pipeline, LLM, cache
- **ARQ job queue** — background processing for LLM summaries and Excel generation
- **User feedback loop** — thumbs up/down classification feedback with bi-gram analysis
- **Viability assessment** — 4-factor scoring (modalidade, timeline, value_fit, geography)
- **Confidence indicator** — per-result relevance confidence with source badges

### Added — Cache Infrastructure
- **Two-level cache** — InMemoryCache (4h) + Supabase (24h) with SWR pattern
- **Hot/Warm/Cold priority** — dynamic cache tier classification with adaptive TTLs
- **Background revalidation** — stale-while-revalidate with dedup and budget control
- **Admin cache dashboard** — `/admin/cache` with metrics, inspection, invalidation
- **Mixpanel analytics events** — fire-and-forget event tracking

### Added — Classification Precision
- **LLM zero-match classification** — GPT-4.1-nano binary YES/NO for 0-keyword bids
- **Relevance source tagging** — keyword, llm_standard, llm_conservative, llm_zero_match
- **Viability badges** — Alta/Media/Baixa with factor breakdown tooltips

### Changed
- **Search period** — 180 days reduced to 10 days (performance + relevance)
- **PNCP page size** — 500 reduced to 50 (API limit change)
- **Default LLM model** — gpt-4o-mini migrated to gpt-4.1-nano (33% cheaper)
- **PCP integration** — migrated from v1 to v2 public API (no auth needed)
- **Timeout chain** — fully realigned: FE(480s) > Pipeline(360s) > Consolidation(300s) > PerSource(180s)
- **UF batching** — phased execution with PNCP_BATCH_SIZE=5, PNCP_BATCH_DELAY_S=2.0

### Fixed
- Datetime crash: tz-aware vs naive comparison in `filtrar_por_prazo_aberto()`
- HTTP 422 added to retryable codes with body logging
- Circuit breaker state tracking for degraded mode
- Near-timeout-inversion detection with warnings

### Testing
- Backend: ~3966 tests passing (~34 pre-existing failures)
- Frontend: ~1921 tests passing (~42 pre-existing failures)
- 25 GTM-RESILIENCE stories completed (see `docs/gtm-resilience-summary.md`)

---

## [0.4.0] - 2026-02-14 - GTM LAUNCH PHASE

### Added
- **Single subscription model** — SmartLic Pro (3 billing periods, repriced to R$397/mo in v0.5.1)
- **Onboarding wizard** — 3-step CNAE-based sector mapping with auto-search
- **Trial conversion flow** — TrialConversionScreen, TrialExpiringBanner, TrialCountdown
- **Multi-source search** — PNCP + PCP (Portal de Compras Publicas) consolidated results
- **15 industry sectors** — configurable keyword sets per sector
- **SSE progress tracking** — real-time per-UF search progress via Server-Sent Events
- **Pipeline management** — opportunity pipeline with drag-and-drop columns

### Changed
- Rebranded from BidIQ Uniformes to SmartLic
- Frontend migrated from Vercel to Railway
- Production URL: https://smartlic.tech

---

## [0.3.0] - 2026-02-03 - MULTI-SECTOR EXPANSION

### Added
- Plan restructuring (STORY-165) — pricing tiers with Stripe integration
- Signup with WhatsApp consent
- Institutional login/signup redesign
- Landing page redesign with value proposition
- Lead prospecting module
- Intelligent keyword filtering with LLM arbiter
- Google Sheets export

### Testing
- Backend: ~3300 tests
- Frontend: ~1700 tests

---

## [0.2.0] - 2026-01-28 - PRODUCTION RELEASE

### Deployed
- **Frontend:** Railway (was Vercel)
- **Backend:** Railway

### Added
- Production deployment on Railway
- E2E test suite with Playwright (25 tests)
- Automated CI/CD pipeline with GitHub Actions
- Health check endpoints for monitoring

### Testing
- Backend coverage: 99.2% (226 tests passing)
- Frontend coverage: 91.5% (94 tests passing)
- E2E tests: 25/25 passing

---

## [0.1.0] - 2026-01-25 - MVP COMPLETE

### Added
- Backend FastAPI implementation (PNCP client, filter, Excel, LLM)
- Frontend Next.js implementation (UF selector, date picker, results, download)
- Docker Compose setup for local development
- Comprehensive test suites (226 backend + 94 frontend tests)

---

## [0.0.1] - 2026-01-24 - Initial Setup

### Added
- Project structure and AIOS framework integration

---

## Links

- [GitHub Repository](https://github.com/tjsasakifln/PNCP-poc)
- [Production](https://smartlic.tech)
