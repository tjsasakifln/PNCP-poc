# Changelog

All notable changes to SmartLic will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- **Single subscription model** — SmartLic Pro R$1,999/month (3 billing periods)
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
