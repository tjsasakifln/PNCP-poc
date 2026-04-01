# Technical Debt Assessment -- SmartLic -- FINAL

**Project:** SmartLic (smartlic.tech)
**Date:** 2026-03-31
**Version:** 1.0 -- Final (post specialist review + QA gate)
**Author:** @architect (Aria) -- Phase 8 consolidation
**Reviewed by:** @data-engineer (Dara, Phase 5), @ux-design-expert (Uma, Phase 6), @qa (Quinn, Phase 7)
**QA Gate:** APPROVED (3.8/5)
**Sources:** `docs/architecture/system-architecture.md` (Phase 1), `supabase/docs/SCHEMA.md` + `supabase/docs/DB-AUDIT.md` (Phase 2), `docs/frontend/frontend-spec.md` (Phase 3), `docs/prd/technical-debt-DRAFT.md` (Phase 4), `docs/reviews/db-specialist-review.md` (Phase 5), `docs/reviews/ux-specialist-review.md` (Phase 6), `docs/reviews/qa-review.md` (Phase 7)

---

## Executive Summary

SmartLic is a mature POC (v0.5) in production with substantial engineering investment. The backend demonstrates exemplary resilience patterns (circuit breakers, bulkhead isolation, multi-level cache with SWR, graceful degradation), a well-structured 8-stage search pipeline, and comprehensive observability (Prometheus + OpenTelemetry + Sentry). The database layer achieves 100% RLS coverage, atomic quota RPCs, JSONB size governance, and pre-computed tsvector indexing. The frontend delivers a polished search experience with SSE progress tracking, 42+ search components, a complete design system with semantic tokens, and partial WCAG AA compliance. Test coverage is strong: 7656+ backend tests, 5733+ frontend tests, and 60 E2E tests, all enforcing a zero-failure policy.

However, rapid evolution from POC to production has accumulated significant structural debt across all layers.

### Assessment Summary

| Metric | Value |
|--------|-------|
| **Total debts identified** | 68 (63 original - 2 closed + 7 added by specialists) |
| **CRITICAL** | 2 |
| **HIGH** | 13 |
| **MEDIUM** | 22 |
| **LOW** | 27 |
| **CLOSED/RESOLVED** | 2 (DB-003, FE-003) |
| **Deferred** | 2 (DB-009, DB-016) |
| **Total estimated effort** | ~370h (deduplicated; CROSS items share effort with constituent SYS/FE/DB items) |
| **Debts resolved during assessment** | 2 (DB-003: duplicate triggers, FE-003: ViabilityBadge accessibility) |
| **Debts added by specialists** | 7 (DB-021, DB-022, DB-023, FE-033, FE-034, FE-035, FE-036) |

### Key Changes from DRAFT

- DRAFT total was 506h across 63 items; after deduplicating CROSS items, closing 2 resolved debts, adjusting estimates per specialist feedback, and adding 7 new items, the real unique effort is **~370h across 68 items**.
- SYS-014 (LLM cost monitoring) upgraded to P0 as a safety net before any refactoring work.
- CROSS-006 (scaling constraint) downgraded from P1 to P2 -- premature at current traffic (~25 searches/day).
- DB-007 revised: CASCADE FK recommendation removed per @data-engineer (would destroy audit trail).
- FE-002 no longer blocks FE-004 -- these are independent per @qa review.
- useSearchOrchestration corrected to 369 lines (DRAFT stated "200+").
- DB migration count confirmed at 106 (squash plan references stale count of 96).
- handle_new_user() confirmed as 8th redefinition (DRAFT stated 7th).

---

## 1. System Debts (validated by @architect)

### CRITICAL

| ID | Debt | Severity | Hours | Priority | Test Impact | Status |
|----|------|----------|-------|----------|-------------|--------|
| SYS-001 | **Filter package at 6,422 LOC** -- `filter/pipeline.py` (1,883 LOC) and `filter/keywords.py` (1,170 LOC). Core filtering logic is the most complex business logic. Target: no module above 500 LOC. | CRITICAL | 40 | P1 | HIGH: 15-20 `test_filter*.py` + 10+ `test_search*.py` + 5+ `test_classification*.py`. Use `__init__.py` re-exports during transition. Budget +10h overhead. | Active |
| SYS-002 | **SIGSEGV single-process constraint** -- C extension restrictions (cryptography, chardet, hiredis) cause intermittent SIGSEGV. Forces single-process mode. All in-memory state assumes one process. | CRITICAL | 24 | P1 | LOW: No test changes needed. Benchmark + architecture evaluation. | Active |

### HIGH

| ID | Debt | Severity | Hours | Priority | Test Impact | Status |
|----|------|----------|-------|----------|-------------|--------|
| SYS-003 | **`cron_jobs.py` at 2,251 LOC** -- cache cleanup, PNCP canary, session cleanup, cache warming, trial emails all in one file. | HIGH | 16 | P1 | MEDIUM: `test_cron*.py`, ARQ mock pattern via conftest must be updated if paths change. | Active |
| SYS-004 | **`job_queue.py` at 2,229 LOC** -- mixes ARQ configuration, Redis pool management, and job definitions. | HIGH | 16 | P1 | MEDIUM: `test_job*.py`, `test_arq*.py`. | Active |
| SYS-005 | **Cache package complexity** -- 2,379 LOC across 14 files plus root shims. SWR logic interleaved with persistence. | HIGH | 24 | P1 | MEDIUM: Cache test files mock `supabase_client.get_supabase`. | Active |
| SYS-006 | **`consolidation.py` at 1,394 LOC** -- multi-source orchestration with dedup, partial results, degradation in single file. | HIGH | 16 | P2 | MEDIUM: `test_consolidation*.py`, use `SimpleNamespace` not `MagicMock` for ConsolidationResult. | Active |
| SYS-007 | **Sync + async PNCP client coexistence** -- legacy sync client alongside async. Circuit breaker and retry logic duplicated. | HIGH | 12 | P2 | LOW: Remove sync client, update imports. | Active |
| SYS-008 | **Feature flag sprawl: 30+ flags without governance** -- no lifecycle, no expiration dates, no cleanup process. | HIGH | 8 | P2 | LOW: Grep all flag references before removal. Add `deprecated_since` field. | Active |

### MEDIUM

| ID | Debt | Severity | Hours | Priority | Status |
|----|------|----------|-------|----------|--------|
| SYS-009 | **Root `filter_*.py` duplication with `filter/` package** | MEDIUM | 8 | P2 | Active |
| SYS-010 | **LLM timeout configuration spread across modules** | MEDIUM | 4 | P2 | Active |
| SYS-011 | **Schemas scattered between `schemas/` dir and root** | MEDIUM | 4 | P2 | Active |
| SYS-012 | **Route files total 11,138 LOC across 37 modules** -- `search.py` (784), `user.py` (698), `pipeline.py` (491), `analytics.py` (468) | MEDIUM | 16 | P2 | Active |
| SYS-013 | **SSE reliability fragility** -- `bodyTimeout(0)` disables timeout protection; Railway idle kills long searches | MEDIUM | 12 | P2 | Active |
| SYS-014 | **LLM cost monitoring absent** -- no Prometheus counters for LLM API costs. A refactoring error removing MAX_ZERO_MATCH_ITEMS cap would go undetected until the monthly bill. | MEDIUM | 6 | **P0** | Active |
| SYS-015 | **Monorepo without workspace tooling** | MEDIUM | 8 | P3 | Active |

### LOW

| ID | Debt | Severity | Hours | Priority | Status |
|----|------|----------|-------|----------|--------|
| SYS-016 | **Backward-compat shims in `main.py`** | LOW | 2 | P3 | Active |
| SYS-017 | **Experimental clients without active usage** -- portal_transparencia, querido_diario, licitaja, sanctions | LOW | 4 | P3 | Active |
| SYS-018 | **Dual-hash transition in `auth.py`** | LOW | 2 | P3 | Active |
| SYS-019 | **`search_cache.py` at root is 118 LOC re-export** | LOW | 1 | P3 | Active |

---

## 2. Database Debts (validated by @data-engineer)

All 20 original debts validated against actual migration files, SCHEMA.md, and backend code. DB section effort adjusted from 73h to 58h (17 active original + 3 new items, after closing DB-003 and deferring DB-009/DB-016).

### HIGH

| ID | Debt | Severity | Hours | Priority | Status | Notes |
|----|------|----------|-------|----------|--------|-------|
| DB-001 | **`handle_new_user()` missing `SET search_path`** -- SECURITY DEFINER without explicit path. 8th redefinition in migration `20260321140000`. | HIGH | 1 | P0 | Active | Confirmed safe to add. Single-line fix. Zero risk. |
| DB-002 | **106 migration files -- schema archaeology risk** -- objects redefined 5-8x each. DR from migration replay untested. Squash plan exists at `MIGRATION-SQUASH-PLAN.md`. | HIGH | 24 | P1 | Active | Count confirmed at 106 (squash plan references stale 96). Execute after all pre-squash fixes. |
| DB-008 | **Multiple tables lack retention/cleanup strategy** -- search_state_transitions (6-8 rows/search), classification_feedback, alert_runs, mfa_recovery_attempts grow without bound. | **HIGH** (upgraded from MEDIUM) | 6 | P0 | Active | @data-engineer: first table to cause perf issues at scale. Projected 126K rows in 6 months at 100 searches/day. 4 pg_cron jobs needed. Hours increased from 4 to 6. |

### MEDIUM

| ID | Debt | Severity | Hours | Priority | Status | Notes |
|----|------|----------|-------|----------|--------|-------|
| DB-004 | **`classification_feedback.user_id` references `auth.users`** -- bridge migration re-introduced old pattern after FK standardization wave. | MEDIUM | 2 | P2 | Active | Must precede squash. |
| DB-005 | **Hardcoded Stripe price IDs in migrations** -- production price IDs in migration files. | MEDIUM | 4 | P2 | Active | Resolve during squash (env-aware seed in new baseline). |
| DB-006 | **`ingestion_checkpoints.crawl_batch_id` lacks enforced FK** -- monitoring exists but no referential integrity. | MEDIUM | 2 | P2 | Active | Add FK with `NOT VALID` + `VALIDATE` + `ON DELETE CASCADE`. |
| DB-010 | **No VACUUM ANALYZE for high-churn tables** -- auto-vacuum may not trigger after single day's purge (~3K deletes, needs 8,050+ dead tuples at 40K rows). | MEDIUM | 2 | P1 | Active | Add pg_cron at 7:30 UTC (30 min after purge). Also schedule weekly `check_pncp_raw_bids_bloat()`. |
| DB-013 | **`profiles.context_data` schema not enforced at DB level** | MEDIUM | 4 | P3 | Active | Keep Pydantic validation; add minimal CHECK `jsonb_typeof(context_data) = 'object'`. |
| DB-021 | **`check_and_increment_quota()` and `increment_quota_atomic()` lack SECURITY DEFINER** -- also lack `SET search_path = public`. Same risk class as DB-001. | MEDIUM | 1 | P2 | **NEW** | Added by @data-engineer. Defensive hardening. |
| DB-023 | **No pg_cron job for `search_sessions` retention** -- old completed/failed sessions accumulate indefinitely. 5 existing pg_cron jobs do not cover this table. | MEDIUM | 2 | P1 | **NEW** | Added by @data-engineer. 6-month retention for terminal states. Batch with DB-008. |

### LOW

| ID | Debt | Severity | Hours | Priority | Status | Notes |
|----|------|----------|-------|----------|--------|-------|
| DB-007 | **`search_state_transitions.search_id` has no FK** | **LOW** (downgraded from MEDIUM) | 1 | P3 | Active | @data-engineer: FK with CASCADE destroys audit trail. Use independent retention (DB-008). |
| DB-009 | **`organizations/organization_members` self-referencing RLS** | **LOW** (downgraded from MEDIUM) | 0 | Deferred | Active | Zero production rows. Revisit when consultoria plan launches. |
| DB-011 | **Trigger naming: 4 remaining with old prefix** (`tr_`, `trigger_`) | **LOW** (downgraded from MEDIUM) | 1 | P1 | Active | Cosmetic. Rename during pre-squash cleanup. |
| DB-012 | **Dead plan catalog entries** (8 with `is_active=false`) | LOW | 1 | P3 | Active | No query impact. |
| DB-014 | **Redundant index on `alert_preferences.user_id`** | LOW | 0.5 | P0 | Active | Trivial DROP. Include in DB-001 migration. |
| DB-015 | **`google_sheets_exports` unused GIN index** | LOW | 0.5 | P0 | Active | Confirmed unused. Include in DB-001 migration. |
| DB-016 | **`plan_features.id` uses SERIAL vs UUID** | LOW | 0 | Deferred | Active | Not worth changing. Low-volume catalog table (~20 rows). |
| DB-017 | **Admin RLS subquery** -- PG caches result within single statement. Concern at 10K+ users (currently ~200). | LOW | 8 | P3 | Active | Years away from threshold. |
| DB-018 | **`user_subscriptions.annual_benefits` vestigial column** | LOW | 1 | P3 | Active | Remove from SQLAlchemy model first, then DROP. |
| DB-019 | **Missing composite indexes** -- `search_state_transitions(search_id, to_state)`, `classification_feedback(setor_id, created_at DESC)`. | LOW | 2 | P1 | Active | Include in pre-squash migration. |
| DB-020 | **Timestamp naming inconsistency** -- `last_updated_at`, `checked_at` outliers. | LOW | 1 | P3 | Active | Rename during squash (included in baseline). |
| DB-022 | **`get_conversations_with_unread_count()` and `get_analytics_summary()` lack `SET search_path`** -- both are SECURITY DEFINER functions. | LOW | 1 | P0 | **NEW** | Added by @data-engineer. Batch fix with DB-001. |

### CLOSED

| ID | Debt | Original Severity | Status | Notes |
|----|------|-------------------|--------|-------|
| DB-003 | **Duplicate trigger functions `update_updated_at()` vs `set_updated_at()`** | HIGH | **CLOSED** | Already resolved in migration `20260308100000_debt001_database_integrity_fixes.sql`. All triggers re-pointed; original function dropped. Saves 2h. |

---

## 3. Frontend/UX Debts (validated by @ux-design-expert)

32 original debts reviewed. 1 resolved (FE-003). 3 upgraded (FE-007, FE-028, FE-030). 5 downgraded (FE-011, FE-013, FE-015, FE-017, FE-019). 4 new items added. Net section effort: ~151h across 35 active items.

### CRITICAL

| ID | Debt | Severity | Hours | Priority | Test Impact | Status |
|----|------|----------|-------|----------|-------------|--------|
| FE-001 | **Search stuck at 78% for 130+ seconds** -- SSE progress stalls during filtering/LLM phase. Users cannot distinguish "working" from "broken." Coordinated with CROSS-001. | CRITICAL | 12 | P0 | MEDIUM: E2E + manual with slow search. New backend progress events + frontend "longer than expected" UI at 45s with partial results option. | Active |

### HIGH

| ID | Debt | Severity | Hours | Priority | Test Impact | Status |
|----|------|----------|-------|----------|-------------|--------|
| FE-002 | **`useSearchOrchestration` mega-hook (369 lines)** -- imports 15 hooks/modules. Orchestrates trial state, modals, tours. Decompose into `useSearchModals` (~60 LOC), `useSearchTours` (~50), `useSearchBillingGuard` (~50), `usePdfGeneration` (~40). | HIGH | 16 | P1 | MEDIUM: `useSearchOrchestration*.test.ts`, `search-resilience.test.tsx`. Extract sub-hooks with identical external API. | Active |
| FE-004 | **Divergent auth guard patterns** -- `(protected)/layout.tsx` vs manual `useEffect` in `/buscar` at ~line 37. | HIGH | 8 | P1 | HIGH: Extend E2E with auth boundary checks. Dedicated security review required before and after. | Active |
| FE-005 | **Dual component directory** -- 51 files in `app/components/` vs 33 in `components/`. Extract providers to `providers/`. Deprecate `app/components/`. | HIGH | 12 | P1 | HIGH: All imports from `app/components/` or `components/` affected. Update `moduleNameMapper` in jest.config.js. | Active |
| FE-006 | **Error 524 exposes technical details** -- retry counter (1/3, 2/3, 3/3) signals fragility. Auto-retry first 2 silently; show calm banner only after all retries exhausted. No counter, no HTTP codes. | HIGH | 6 | P0 | LOW: Update error-messages tests. | Active |
| FE-007 | **12 banners on search page** -- cognitive overload on core page. BannerStack has priority system but no cap. Need max 2 visible, auto-collapse informational after 5s. | **HIGH** (upgraded from MEDIUM) | 8 | P0 | LOW: Update BannerStack tests. | Active |
| FE-033 | **Landing page excessive hydration** -- all 13 child components use `"use client"`, only 3 need client-side JS (HeroSection, SectorsGrid, AnalysisExamplesCarousel). Estimated LCP improvement from ~3.5s to ~2.0s. | HIGH | 10 | P0 | MEDIUM: Lighthouse CI for LCP < 2.5s target, visual regression, interactive element verification. | **NEW** |

### MEDIUM

| ID | Debt | Severity | Hours | Priority | Status |
|----|------|----------|-------|----------|--------|
| FE-008 | **`/admin` uses useState + manual fetch instead of SWR** | MEDIUM | 4 | P2 | Active |
| FE-009 | **Incomplete `aria-live` for search results** -- 28+ usages exist; 6 banners still lack it; results count announcement could be more explicit. | MEDIUM | 2 | P2 | Active |
| FE-010 | **`mensagens/page.tsx` at 591 lines** -- extract ConversationList, ConversationDetail, MessageComposer. | MEDIUM | 8 | P2 | Active |
| FE-012 | **SVG icons lacking `role="img"` or `aria-label`** -- priority: status icons in `/historico` and `/mensagens`. | MEDIUM | 3 | P2 | Active |
| FE-014 | **Forms missing `aria-describedby`** for fields with hints. | MEDIUM | 3 | P2 | Active |
| FE-016 | **No ErrorBoundary on SWRProvider/UserProvider** -- 7-deep provider hierarchy with no boundary. | MEDIUM | 3 | P2 | Active |
| FE-018 | **Dark mode contrast on search form** -- targeted borders on interactive elements only (`border border-ink/10`). Do NOT change card surfaces globally. | MEDIUM | 2 | P2 | Active |
| FE-020 | **No edge caching for stable endpoints** -- add `Cache-Control: public, s-maxage=3600, stale-while-revalidate=86400` to `/api/setores` and `/api/plans`. | MEDIUM | 2 | P2 | Active |
| FE-028 | **Dark mode brand-blue contrast** -- `#116dff` vs `#121212` at 4.5:1 fails AA for small text (<18px). Fix: `--brand-blue-dark: #3388ff` (~5.2:1). | **MEDIUM** (upgraded from LOW) | 2 | P2 | Active |
| FE-030 | **Mobile search limited vertical space** -- form fills viewport, results invisible without scrolling. Collapse description for returning users (`has_searched_before` localStorage flag). Keep title visible for wayfinding. | **MEDIUM** (upgraded from LOW) | 4 | P2 | Active |
| FE-034 | **Pipeline kanban missing drag announcements** -- `DndContext` lacks `accessibility` prop for `onDragStart`/`onDragOver`/`onDragEnd`/`onDragCancel` announcements. Cards lack `aria-roledescription="item ordenavel"`. | MEDIUM | 4 | P2 | **NEW** |

### LOW

| ID | Debt | Severity | Hours | Priority | Status |
|----|------|----------|-------|----------|--------|
| FE-011 | **Potential `any` types in API proxy routes** | **LOW** (downgraded from MEDIUM) | 4 | P3 | Active |
| FE-013 | **Inconsistent landmarks** -- gap narrower than described. Minor `id` inconsistency and `conta/equipe/` branching. | **LOW** (downgraded from MEDIUM) | 2 | P3 | Active |
| FE-015 | **`prefers-reduced-motion` partially unresolved** -- CSS rule + `useInView` + `AnimateOnScroll` all check. Only gap: Framer Motion JS-driven landing page animations. Add `useReducedMotion()` from framer-motion. | **LOW** (downgraded from MEDIUM) | 2 | P3 | Active |
| FE-017 | **Frontend feature gates hardcoded** -- `useFeatureFlags` hook exists fetching from `/api/feature-flags`. DX/architecture concern, not UX. | **LOW** (downgraded from MEDIUM) | 3 | P3 | Active |
| FE-019 | **60+ API proxy routes consolidation** -- purely DX/maintenance concern. | **LOW** (downgraded from MEDIUM) | 6 | P3 | Active |
| FE-021 | **Inline SVGs vs lucide-react** | LOW | 3 | P3 | Active |
| FE-022 | **Raw hex values vs semantic tokens** | LOW | 4 | P3 | Active |
| FE-023 | **`/conta` redirect flash** | LOW | 2 | P3 | Active |
| FE-024 | **Duplicate footers** | LOW | 2 | P3 | Active |
| FE-025 | **RootLayout async for CSP nonce** | LOW | 2 | P3 | Active |
| FE-026 | **SEO pages thin/duplicate content risk** | LOW | 4 | P3 | Active |
| FE-027 | **SearchResults.tsx backward-compat re-exports** | LOW | 1 | P3 | Active |
| FE-029 | **Focus order in BuscarModals + BottomNav overlay** | LOW | 3 | P3 | Active |
| FE-031 | **Dashboard chart sparse for low-usage users** | LOW | 3 | P3 | Active |
| FE-032 | **Pipeline empty state wordy** | LOW | 1 | P3 | Active |
| FE-035 | **Chart colors not colorblind-safe** -- 10-color palette relies entirely on hue differentiation. ~8% of male users affected. | LOW | 4 | P3 | **NEW** |
| FE-036 | **Shepherd.js loaded eagerly on all protected pages** -- ~15KB unnecessary JS for 95%+ of views. Wrap in `next/dynamic`. | LOW | 2 | P3 | **NEW** |

### CLOSED

| ID | Debt | Original Severity | Status | Notes |
|----|------|-------------------|--------|-------|
| FE-003 | **ViabilityBadge uses `title` for critical data** | HIGH | **CLOSED** | Already refactored. Custom `ViabilityTooltip` with `role="tooltip"`, `aria-describedby`, keyboard Enter/Space toggle, Escape dismiss, tap-to-toggle mobile. 21 accessibility attributes. Component references `DEBT-FE-002` as fix ticket. Saves 4h. |

---

## 4. Cross-Cutting Debts

Cross-cutting debts represent coordinated work spanning multiple layers. **Effort is NOT additive** with constituent items -- the hours below represent coordination overhead only. Constituent item hours are tracked in their respective sections above.

| ID | Debt | Areas | Severity | Coord. Hours | Constituent Items | Priority | Status |
|----|------|-------|----------|-------------|-------------------|----------|--------|
| CROSS-001 | **SSE chain fragility** -- search-stuck-at-78% is user-visible symptom of backend progress event gaps. Coordinated fix: backend adds post-fetch stage events; frontend adds "longer than expected" UI at 45s; infrastructure timeout tuning. | BE + FE + Infra | HIGH | 4 | FE-001 (12h), SYS-013 (12h) | P0 | Active |
| CROSS-002 | **Auth pattern divergence** -- three independent enforcement points (middleware, route group layout, manual useEffect) could diverge silently. | BE + FE | HIGH | 2 | FE-004 (8h) | P1 | Active |
| CROSS-003 | **Feature flag governance absent** -- backend 30+ flags + frontend hardcoded gates. No shared flag service, no lifecycle. | BE + FE | MEDIUM | 2 | SYS-008 (8h), FE-017 (3h) | P2 | Active |
| CROSS-004 | **Migration volume + schema archaeology** -- 106 migrations impact deploy time and DR. Squash requires CI coordination. | DB + Infra | HIGH | 0 | DB-002 (24h) | P1 | Active |
| CROSS-005 | **LLM dependency spans layers** -- config scattered, cost untracked, frontend LLM failure UX inadequate. | BE + FE | MEDIUM | 2 | SYS-010 (4h), SYS-014 (6h) | P2 | Active |
| CROSS-006 | **Scaling constraint** -- SIGSEGV forces single-process. L1 cache, SSE queues, progress tracker all assume one process. Redis coordination needed for multi-service. | BE + Infra | CRITICAL | 8 | SYS-002 (24h) | **P2** (downgraded) | Active |

**CROSS-006 downgrade rationale (per @qa review):** At current traffic (~25 searches/day, ~50 users), the single-process constraint is a ceiling, not an active fire. **Trigger condition for P1 upgrade:** daily searches exceed 200 OR concurrent searches exceed 10.

**CROSS coordination total:** 18h (all substantive work tracked in constituent items).

---

## 5. QA-Identified Gaps

Identified during QA gate review (Phase 7). Documented for awareness and future sprint planning.

### Gap 1: Test Suite Fragility During Refactoring (MEDIUM)

Large decompositions (SYS-001 at 40h, SYS-003/004 at 32h, FE-002 at 16h) will break import paths across 50+ test files each. Known pollution patterns (`sys.modules` injection, `importlib.reload`, global singleton leakage) could resurface. Windows full-suite requires `run_tests_safe.py --parallel 4` (direct `pytest` hangs due to state leakage).

**Mitigation:** Budget 20-30% overhead on effort estimates for test maintenance. Use `__init__.py` re-exports during transitions. Run full suite after each decomposition via `python scripts/run_tests_safe.py --parallel 4`.

### Gap 2: Observability Coherence (LOW)

Observability debt scattered: SYS-014 (LLM costs in System), DB-010 (VACUUM in Database), `check_pncp_raw_bids_bloat()` (exists but unmonitored). Prometheus metrics, Sentry error grouping, and alerting rules not assessed as a coherent category.

**Mitigation:** When implementing SYS-014, audit existing monitoring for completeness. Consider dedicated observability sprint if gaps compound.

### Gap 3: CI/CD Pipeline Debt (LOW)

CI workflow run times, `.railwayignore` configuration, Docker `CACHEBUST` mechanism, and potential redundant workflows not assessed. CI/CD is operational rather than structural debt.

**Mitigation:** Monitor CI run times. Flag if backend test CI exceeds 10 minutes.

### Gap 4: Worker/Queue Resilience (LOW)

ARQ has no runtime reconnection (upstream issue #386). Restart wrapper is community standard. Queue depth monitoring, dead letter handling, and in-flight job behavior during Railway deploy restarts not assessed.

**Mitigation:** Document current ARQ failure modes. Add queue depth metric. Consider dead letter queue for failed LLM summarization jobs.

---

## 6. Final Prioritization Matrix

| Priority | Count | Hours | Items |
|----------|-------|-------|-------|
| **P0** | 9 items | ~46h | DB-001 (1h), DB-008 (6h), DB-014 (0.5h), DB-015 (0.5h), DB-022 (1h), SYS-014 (6h), FE-001 (12h), FE-006 (6h), FE-007 (8h), FE-033 (10h), CROSS-001 coord (4h) |
| **P1** | 13 items | ~151h | SYS-001 (40h), SYS-002 (24h), SYS-003 (16h), SYS-004 (16h), SYS-005 (24h), DB-002 (24h), DB-010 (2h), DB-011 (1h), DB-019 (2h), DB-023 (2h), FE-002 (16h), FE-004 (8h), FE-005 (12h), CROSS-002 coord (2h) |
| **P2** | 22 items | ~113h | SYS-006 (16h), SYS-007 (12h), SYS-008 (8h), SYS-009 (8h), SYS-010 (4h), SYS-011 (4h), SYS-012 (16h), SYS-013 (12h), DB-004 (2h), DB-005 (4h), DB-006 (2h), DB-021 (1h), FE-008 (4h), FE-009 (2h), FE-010 (8h), FE-012 (3h), FE-014 (3h), FE-016 (3h), FE-018 (2h), FE-020 (2h), FE-028 (2h), FE-030 (4h), FE-034 (4h), CROSS-003 coord (2h), CROSS-005 coord (2h), CROSS-006 coord (8h) |
| **P3** | 24 items | ~60h | SYS-015 (8h), SYS-016 (2h), SYS-017 (4h), SYS-018 (2h), SYS-019 (1h), DB-007 (1h), DB-012 (1h), DB-013 (4h), DB-017 (8h), DB-018 (1h), DB-020 (1h), FE-011 (4h), FE-013 (2h), FE-015 (2h), FE-017 (3h), FE-019 (6h), FE-021 (3h), FE-022 (4h), FE-023 (2h), FE-024 (2h), FE-025 (2h), FE-026 (4h), FE-027 (1h), FE-029 (3h), FE-031 (3h), FE-032 (1h), FE-035 (4h), FE-036 (2h) |
| **CLOSED** | 2 items | 0h | DB-003, FE-003 |
| **Deferred** | 2 items | 0h | DB-009, DB-016 |
| **TOTAL** | **68** | **~370h** | |

---

## 7. Resolution Roadmap

### Phase 1: Quick Wins + Safety Net (1-2 weeks, ~46h)

P0 items that protect the system before larger refactoring begins.

**Database security batch (single migration, ~3h):**

| Order | ID | Hours | Action |
|-------|-----|-------|--------|
| 1 | DB-001 | 1 | Add `SET search_path = public` to `handle_new_user()`. |
| 2 | DB-022 | 1 | Add `SET search_path` to `get_conversations_with_unread_count()` and `get_analytics_summary()`. |
| 3 | DB-014 | 0.5 | DROP redundant `idx_alert_preferences_user_id`. |
| 4 | DB-015 | 0.5 | DROP unused GIN index on `google_sheets_exports.search_params`. |

**Retention policies batch (single pg_cron migration, ~8h):**

| Order | ID | Hours | Action |
|-------|-----|-------|--------|
| 5 | DB-008 | 6 | Add pg_cron for search_state_transitions (90d), classification_feedback (12mo), mfa_recovery_attempts (30d), alert_runs (6mo). |
| 6 | DB-023 | 2 | Add pg_cron for search_sessions (6mo, terminal states only). |

**Backend safety net (~6h):**

| Order | ID | Hours | Action |
|-------|-----|-------|--------|
| 7 | SYS-014 | 6 | Prometheus counters for LLM calls/costs + budget alert thresholds. Must be in place before SYS-001. |

**Frontend UX critical (~36h, parallelizable):**

| Order | ID | Hours | Action |
|-------|-----|-------|--------|
| 8 | FE-001 + CROSS-001 | 12+4 | Phase-specific progress events backend + "longer than expected" UI at 45s with partial results option + coordination. |
| 9 | FE-006 | 6 | Silent auto-retry (2 attempts), calm messaging after exhaustion. No counter, no HTTP codes. Small pulsing dot during retry. |
| 10 | FE-007 | 8 | BannerStack `maxVisible: 2`, auto-collapse informational after 5s, expandable "N more" row. Consolidate CacheBanner + ExpiredCacheBanner + RefreshBanner. |
| 11 | FE-033 | 10 | Convert 10 of 13 landing page children to Server Components. Only HeroSection, SectorsGrid, AnalysisExamplesCarousel remain client. |

### Phase 2: Foundation (2-4 weeks, ~151h)

P1 items establishing clean architecture for all future work.

**Database track (~29h, sequential):**

| Order | ID | Hours | Action |
|-------|-----|-------|--------|
| 1 | DB-010 | 2 | VACUUM ANALYZE schedule at 7:30 UTC + weekly bloat check. |
| 2 | DB-011 | 1 | Rename 4 triggers to `trg_` prefix. |
| 3 | DB-019 | 2 | Add 2 composite indexes. |
| 4 | DB-002 | 24 | **Migration squash (106 to ~5-10 files).** Follow existing squash plan. Also resolves DB-005 (env-aware seeds) and DB-020 (timestamps in baseline). Test clean DB creation against pg_dump of production. |

**Backend track (~120h, largely parallelizable with DB):**

| Order | ID | Hours | Action |
|-------|-----|-------|--------|
| 1 | SYS-001 | 40+10 | Filter package decomposition. Target: no module >500 LOC. Budget +10h for test path updates (~30 test files). |
| 2 | SYS-003 | 16 | cron_jobs.py to `jobs/cron/` sub-package. |
| 3 | SYS-004 | 16 | job_queue.py split: config, pool management, job definitions. |
| 4 | SYS-005 | 24 | Cache package consolidation. Remove root shims. |
| 5 | SYS-002 | 24 | SIGSEGV investigation. Benchmark current capacity. Evaluate newer cryptography versions. |

**Frontend track (~36h, parallelizable with backend):**

| Order | ID | Hours | Action |
|-------|-----|-------|--------|
| 1 | FE-005 | 12 | Consolidate to `components/` (shared) + `providers/` (infra). Empty and remove `app/components/`. |
| 2 | FE-002 | 16 | Decompose into 4 sub-hooks (~150 LOC compositor). |
| 3 | FE-004 | 8 | Unify auth guard. Independent of FE-002. Security review required. |

### Phase 3: Optimization (4-6 weeks, ~113h)

P2 items folded into feature work or dedicated cleanup sprints.

**Key clusters:**

- **Backend module decomposition:** SYS-006 (16h), SYS-012 (16h), SYS-007 (12h), SYS-013 (12h) = 56h
- **Feature flag governance:** SYS-008 (8h) + FE-017 via CROSS-003 (2h coord) = 10h
- **Accessibility cluster:** FE-009 (2h) + FE-012 (3h) + FE-014 (3h) + FE-028 (2h) + FE-030 (4h) + FE-034 (4h) = 18h
- **Database opportunistic:** DB-004 (2h) + DB-005 (in squash) + DB-006 (2h) + DB-021 (1h) = 5h
- **Scaling architecture:** CROSS-006 (8h evaluation) -- trigger for P1 upgrade: >200 daily searches

### Phase 4: Polish (backlog, ~60h)

P3 items addressed opportunistically during related feature work. No dedicated sprint needed. All items are LOW severity with no user-facing urgency.

---

## 8. Dependency Graph (Updated)

All corrections from specialist reviews and QA gate incorporated.

```
PHASE 1 (P0) -- no inter-dependencies, all can deploy independently:
  DB-001 + DB-022 + DB-014 + DB-015  ──single migration──>  Deploy immediately
  DB-008 + DB-023                     ──single pg_cron migration──>  Deploy
  SYS-014                            ──independent──>  Deploy (safety net)
  FE-001 + SYS-013                   ──coordinated──>  CROSS-001 (deploy BE first)
  FE-006, FE-007, FE-033             ──independent──>  Deploy

PHASE 2 (P1) -- Database pre-squash chain:
  DB-001 (Phase 1, done) ──must precede──> DB-002 (squash)
  DB-004               ──must precede──> DB-002 (squash)
  DB-008 (Phase 1, done) ──must precede──> DB-002 (squash)
  DB-010               ──must precede──> DB-002 (squash)
  DB-011               ──must precede──> DB-002 (squash)
  DB-019               ──should precede──> DB-002 (squash)
  DB-023 (Phase 1, done) ──should precede──> DB-002 (squash)
  DB-002 (squash)      ──resolves──> DB-005 (Stripe IDs), DB-020 (timestamps)

PHASE 2 (P1) -- Backend decomposition chain:
  SYS-014 (Phase 1, done) ──safety net for──> SYS-001 (filter decomposition)
  SYS-001              ──enables──> SYS-009 (root filter cleanup, P2)
  SYS-003              ──enables──> SYS-004 (shared Redis pool patterns)
  SYS-005              ──enables──> SYS-019 (root cache shim removal, P3)

PHASE 2 (P1) -- Frontend (NO cross-dependencies):
  FE-005 (directory consolidation) ──enables──> FE-010 (mensagens decomp, P2)
  FE-002 (hook decomposition)     ──independent of──> FE-004 (auth unification)

PHASE 2/3 -- Cross-cutting:
  CROSS-006 (scaling, P2) ──depends on──> SYS-002 (SIGSEGV, P1)
  SYS-008 + FE-017       ──unified as──> CROSS-003 (feature flags, P2)
  DB-018 (drop column)   ──requires──> Backend model change first

NO circular dependencies. Graph is a DAG.
```

---

## 9. Risk Register

### Consolidated Risks (deduplicated across all reviews)

| ID | Risk | Probability | Impact | Source | Key Debts | Mitigation |
|----|------|-------------|--------|--------|-----------|------------|
| R-001 | **Single-process scaling ceiling** | Medium | HIGH | DRAFT + DB + QA | SYS-002, CROSS-006 | Benchmark capacity. Design Redis coordination. Evaluate newer cryptography. P1 trigger: >200 daily searches. |
| R-002 | **Migration chain replay failure** | Medium-High | HIGH | DRAFT + DB | DB-002 | Execute squash within 2 sprints. pg_dump backup. Test clean replay weekly post-squash. |
| R-003 | **Search UX trust erosion** (stuck at 78%, error 524) | High | HIGH | DRAFT + UX | FE-001, FE-006, FE-007, CROSS-001 | Phase 1 fixes. ~10% of trial users affected by degraded first experience. |
| R-004 | **Auth guard divergence / data exposure** | Low | CRITICAL | DRAFT + UX + QA | FE-004, CROSS-002 | Security review before/after. E2E auth boundary tests. |
| R-005 | **Feature flag combinatorial explosion** | Medium | MEDIUM | DRAFT | SYS-008, CROSS-003 | Flag lifecycle with `deprecated_since`. Remove after 2+ sprints, zero refs. |
| R-006 | **LLM cost spike** (no monitoring, burst classification) | Medium | MEDIUM | DRAFT + QA | SYS-014 | P0: cost counters before any refactoring. Budget alerts. |
| R-007 | **Accessibility legal exposure** (Lei 13.146/2015) | Medium | MEDIUM | DRAFT + UX | FE-028, FE-009, FE-012, FE-014, FE-034 | Sprint 2-3 a11y cluster. Brand-blue contrast fix is AA minimum. |
| R-008 | **Landing page acquisition loss** (LCP ~3.5s) | High | HIGH | UX | FE-033 | Phase 1: RSC conversion for 10 of 13 components. |
| R-009 | **Unbounded table growth** | High | MEDIUM | DB | DB-008, DB-023 | Phase 1: retention policies. 6 months before impact at current traffic. |
| R-010 | **Refactoring regression** (100+ test files affected) | HIGH | MEDIUM | QA | SYS-001, SYS-003/004, FE-002, FE-005 | `__init__.py` re-exports. `run_tests_safe.py --parallel 4`. Budget 20-30% overhead. |
| R-011 | **Migration squash data loss** | Medium | HIGH | QA | DB-002 | Compare squashed schema against pg_dump. DB specialist phased approach. |
| R-012 | **SSE breaking change during deploy** | Medium | HIGH | QA | CROSS-001 | Deploy backend first (additive events). Frontend handles both old/new shapes. |
| R-013 | **Post-squash migration drift** | Medium | MEDIUM | DB | DB-002 | Each week adds 1-3 migrations, increasing squash complexity. Execute promptly. |
| R-014 | **Mobile user abandonment** | Medium | MEDIUM | UX | FE-030 | Compact header for returning users. |
| R-015 | **Data source SPOF** (multi-day ingestion failure) | Low | MEDIUM | DRAFT | N/A | Already mitigated by 3x daily incremental + monitoring. Alert on >2 consecutive failures. |

---

## 10. Success Criteria and Metrics

### Per-Priority Band

| Priority | Metric | Target | Measurement |
|----------|--------|--------|-------------|
| **P0** | Security vulnerabilities; search UX incidents; LLM cost visibility | Zero SET search_path vulnerabilities; <5% of searches trigger "longer than expected" UI; LLM cost dashboard operational | Sentry; Mixpanel `partial-results-prompt` events; Prometheus/Grafana |
| **P1** | Module sizes; test pass rate; migration chain health | No backend module >500 LOC; no frontend hook >200 LOC; zero test failures; clean DB from squashed baseline matches production | `wc -l` audit; CI green; pg_dump diff |
| **P2** | Accessibility compliance; flag governance; scaling readiness | axe-core zero critical violations; active flags <20; scaling trigger conditions documented | Lighthouse CI; flag audit script; architecture doc |
| **P3** | Code hygiene | No duplicate functions; no redundant indexes; no vestigial columns | Schema audit query (quarterly) |

### Overall Success Criteria

1. **Zero test regressions** -- full suite (backend + frontend + E2E) passes after each debt resolution sprint.
2. **Migration replay verified** -- clean DB creation from squashed baseline matches production schema (pg_dump diff = empty).
3. **LCP < 2.5s** -- landing page after FE-033 RSC conversion (target < 2.0s). Measured via Lighthouse CI.
4. **Search UX** -- no searches "stuck" without user feedback for >45 seconds. Measured via Mixpanel.
5. **Security** -- all SECURITY DEFINER functions have SET search_path. Verified via schema audit query.
6. **Effort tracking** -- actual hours within 30% of estimates (retrospective validation per sprint).
7. **Table growth controlled** -- search_state_transitions, search_sessions rows stay within retention targets (90d / 6mo).
8. **Landing performance** -- LCP improvement measurable after FE-033. Target: ~3.5s to <2.5s.

---

## 11. Appendix: Review Trail

### Phase 1: Architecture Assessment
- **Output:** `docs/architecture/system-architecture.md` (1,013 lines)
- **Author:** @architect (Aria)
- **Content:** Full system inventory -- backend modules, route map, frontend pages, component tree, resilience patterns, timeout chain, data flow

### Phase 2: Database Assessment
- **Output:** `supabase/docs/SCHEMA.md` (608 lines) + `supabase/docs/DB-AUDIT.md` (294 lines)
- **Author:** @data-engineer (Dara)
- **Content:** Schema inventory (35 tables, 39 functions, 95 indexes, 15 RLS policies), audit findings

### Phase 3: Frontend Assessment
- **Output:** `docs/frontend/frontend-spec.md` (908 lines)
- **Author:** @ux-design-expert (Uma)
- **Content:** Component tree, design system tokens, accessibility audit, UX critical issues

### Phase 4: DRAFT Consolidation
- **Output:** `docs/prd/technical-debt-DRAFT.md` (418 lines)
- **Author:** @architect (Aria)
- **Content:** 63 debts, prioritization matrix, dependency graph, risk register, specialist questions (7 DB + 8 UX)

### Phase 5: Database Specialist Review
- **Output:** `docs/reviews/db-specialist-review.md` (280 lines)
- **Author:** @data-engineer (Dara)
- **Verdict:** APPROVED with adjustments
- **Key changes:** DB-003 CLOSED, DB-007/009/011 downgraded, DB-008 upgraded, 3 new items (DB-021/022/023), all 7 questions answered with migration-level evidence

### Phase 6: UX Specialist Review
- **Output:** `docs/reviews/ux-specialist-review.md` (377 lines)
- **Author:** @ux-design-expert (Uma)
- **Verdict:** APPROVED with adjustments
- **Key changes:** FE-003 CLOSED, FE-007/028/030 upgraded, FE-011/013/015/017/019 downgraded, 4 new items (FE-033/034/035/036), all 8 questions answered with component-level evidence

### Phase 7: QA Gate Review
- **Output:** `docs/reviews/qa-review.md` (249 lines)
- **Author:** @qa (Quinn)
- **Verdict:** APPROVED (3.8/5)
- **Key changes:** 13 mandatory adjustments -- effort deduplication, CROSS-006 downgrade to P2, SYS-014 to P0, FE-002/FE-004 dependency removal, DB-023 to pre-squash chain, 4 gap identifications

### Phase 8: Final Assessment (this document)
- **Output:** `docs/prd/technical-debt-assessment.md`
- **Author:** @architect (Aria)
- **Content:** All 13 QA adjustments incorporated, 68 items finalized, ~370h deduplicated effort, 4-phase roadmap, consolidated risk register (15 risks), success criteria

---

*Document finalized 2026-03-31 by @architect (Aria) as Phase 8 of Brownfield Discovery workflow.*
*This is the DEFINITIVE technical debt assessment for SmartLic. All specialist feedback and QA gate adjustments have been incorporated.*
