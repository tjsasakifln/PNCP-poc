# Technical Debt Assessment — SmartLic — DRAFT

**Data:** 2026-03-31
**Status:** DRAFT — Pendente revisao dos especialistas (Fases 5, 6, 7)
**Autores:** @architect (Aria) — consolidacao de Phases 1-3
**Fontes:** `docs/architecture/system-architecture.md` (Phase 1), `supabase/docs/SCHEMA.md` + `supabase/docs/DB-AUDIT.md` (Phase 2), `docs/frontend/frontend-spec.md` (Phase 3)

---

## Executive Summary

SmartLic is a mature POC (v0.5) in production with substantial engineering investment across all layers. The backend demonstrates exemplary resilience patterns (circuit breakers, bulkhead isolation, multi-level cache with SWR, graceful degradation), a well-structured 8-stage search pipeline, and comprehensive observability (Prometheus + OpenTelemetry + Sentry). The database layer achieves 100% RLS coverage, atomic quota RPCs, JSONB size governance, and pre-computed tsvector indexing. The frontend delivers a polished search experience with SSE progress tracking, 42+ search components, a complete design system with semantic tokens, and partial WCAG AA compliance. Test coverage is strong: 7656+ backend tests, 5733+ frontend tests, and 60 E2E tests, all enforcing a zero-failure policy.

However, the rapid evolution from POC to production has accumulated significant structural debt. The backend suffers from oversized modules (filter package at 6,422 LOC, cron_jobs.py at 2,251 LOC, job_queue.py at 2,229 LOC) and a single-process constraint caused by C extension SIGSEGV issues that prevents horizontal scaling. The database has 106 un-squashed migrations creating schema archaeology risk, a missing `SET search_path` on the critical `handle_new_user()` function, and several tables growing without retention policies. The frontend has a dual component directory structure (`app/components/` vs `components/`) creating developer confusion, a mega-hook (`useSearchOrchestration`) that is difficult to maintain, divergent auth guard patterns between the route group and `/buscar`, and accessibility gaps in viability tooltips and screen reader announcements.

The total assessment identifies 63 individual debts across all layers. Of these, 2 are CRITICAL (SIGSEGV constraint, filter module complexity), 12 are HIGH, 25 are MEDIUM, and 24 are LOW. The estimated total remediation effort is approximately 340-420 hours. The recommended approach is to address CRITICAL and HIGH items across 2-3 sprints, with MEDIUM items folded into feature work and LOW items handled opportunistically.

---

## 1. Debitos de Sistema (from system-architecture.md)

### CRITICAL

| ID | Descricao | Severidade | Esforco (h) | Racional |
|----|-----------|-----------|-------------|----------|
| SYS-001 | **Filter package at 6,422 LOC total** — `filter/pipeline.py` (1,883 LOC) and `filter/keywords.py` (1,170 LOC) are the largest files. Core filtering logic is the most complex business logic in the system. | CRITICAL | 40 | Difficult to maintain, test in isolation, and debug. Target: no module above 500 LOC. Extract keyword matching, density calculation, and batch processing into dedicated modules. |
| SYS-002 | **SIGSEGV single-process constraint** — C extension restrictions (cryptography, chardet, hiredis) cause intermittent SIGSEGV in production with forked workers. Forces single-process mode (no `--workers`, no uvloop, no httptools). | CRITICAL | 24 | Prevents horizontal scaling per instance. All in-memory state (SSE queues, L1 cache, progress tracker) only works because there is one process. Only option for increased load is vertical scaling or multiple Railway services with Redis-based coordination. |

### HIGH

| ID | Descricao | Severidade | Esforco (h) | Racional |
|----|-----------|-----------|-------------|----------|
| SYS-003 | **`cron_jobs.py` at 2,251 LOC** — cache cleanup, PNCP canary, session cleanup, cache warming, trial emails all in one file. | HIGH | 16 | `jobs/cron/` sub-package already exists with partial extraction. Complete migration by moving all cron logic into the sub-package. |
| SYS-004 | **`job_queue.py` at 2,229 LOC** — mixes ARQ configuration, Redis pool management, and job definitions. | HIGH | 16 | Split into configuration, pool management, and job definitions. |
| SYS-005 | **Cache package complexity** — 2,379 LOC across 14 files plus root `search_cache.py` (118 LOC re-export) and `cache_module.py`. Cache key migration (STORY-306) added dual-read complexity. SWR logic interleaved with persistence. | HIGH | 24 | 14-file package plus root shims creates cognitive overhead. Consolidate root-level re-exports into package. |
| SYS-006 | **`consolidation.py` at 1,394 LOC** — multi-source orchestration with dedup, partial results, degradation tracking in single file. | HIGH | 16 | Growing complexity warrants decomposition into orchestrator + per-source modules. |
| SYS-007 | **Sync + async PNCP client coexistence** — `pncp_client.py` (66 LOC re-export) + `clients/pncp/` (7 files). Legacy sync client still present alongside async. Circuit breaker and retry logic duplicated. | HIGH | 12 | Remove sync client, consolidate into `clients/pncp/` only. |
| SYS-008 | **Feature flag sprawl: 30+ flags without governance** — no lifecycle (create -> active -> deprecated -> removed), no expiration dates, no cleanup process. Flags from early stories (STORY-165, STORY-179) still present. | HIGH | 8 | Testing matrix expands combinatorially. Configuration complexity grows with each feature. |

### MEDIUM

| ID | Descricao | Severidade | Esforco (h) | Racional |
|----|-----------|-----------|-------------|----------|
| SYS-009 | **Duplication between root `filter_*.py` and `filter/` package** — legacy root files coexist with `filter/` package imports via `filter/__init__.py`. | MEDIUM | 8 | Remove or convert root-level legacy files into proper re-exports. |
| SYS-010 | **LLM timeout configuration spread across modules** — OpenAI timeout in `llm_arbiter.py` + config in `config/features.py`, not always consistent. | MEDIUM | 4 | Centralize LLM configuration into single source of truth. |
| SYS-011 | **Schemas scattered between `schemas/` directory (14 files) and root** — `schemas_stats.py`, `schema_contract.py` at root. | MEDIUM | 4 | Move root schema files into `schemas/` package. |
| SYS-012 | **Route files total 11,138 LOC across 37 modules** — `search.py` (784 LOC), `user.py` (698 LOC), `pipeline.py` (491 LOC), `analytics.py` (468 LOC). | MEDIUM | 16 | Large route files should extract business logic into service modules. |
| SYS-013 | **SSE reliability fragility** — `bodyTimeout(0)` disables all timeout protection; Railway ~120s idle timeout can kill SSE during slow searches; Last-Event-ID resumption (STORY-297) adds complexity. | MEDIUM | 12 | Heartbeat (15s) must stay below Railway idle threshold. Consider WebSocket upgrade path. |
| SYS-014 | **LLM cost monitoring absent** — no Prometheus counters for LLM API costs per classification/summary. A single search can classify 200+ items. ThreadPoolExecutor(max_workers=10) could create burst costs. | MEDIUM | 6 | Add cost tracking metrics and budget alerts before scaling user base. |
| SYS-015 | **Monorepo without workspace tooling** — backend (Python) and frontend (Node.js) share repository but lack workspace-level tooling (nx, turborepo, just, make). Separate CI workflows that could share caching. | MEDIUM | 8 | Evaluate lightweight monorepo tooling to unify build/test/deploy commands. |

### LOW

| ID | Descricao | Severidade | Esforco (h) | Racional |
|----|-----------|-----------|-------------|----------|
| SYS-016 | **Backward-compat shims in `main.py`** — re-exports for legacy tests. | LOW | 2 | Functional but adds indirection. |
| SYS-017 | **Experimental clients without active usage** — `portal_transparencia_client.py`, `querido_diario_client.py`, `qd_extraction.py`, `licitaja_client.py` (disabled by default), `sanctions.py`. | LOW | 4 | Unclear integration status. Consider moving to feature branch. |
| SYS-018 | **Dual-hash transition in `auth.py`** — 1h window for cache key compatibility. | LOW | 2 | Can be removed after stabilization. |
| SYS-019 | **`search_cache.py` at root is 118 LOC re-export** — may confuse developers expecting full implementation. | LOW | 1 | Redirect or remove. |

---

## 2. Debitos de Database (from SCHEMA.md + DB-AUDIT.md)

> :warning: **PENDENTE: Revisao do @data-engineer (Fase 5)**

### HIGH

| ID | Descricao | Severidade | Esforco (h) | Racional |
|----|-----------|-----------|-------------|----------|
| DB-001 | **`handle_new_user()` missing `SET search_path`** — SECURITY DEFINER without explicit `SET search_path = public`. Vulnerable to search_path injection. Called on every signup. Redefined 7 times across migrations. | HIGH | 1 | Security hardening — single line change. |
| DB-002 | **106 migration files create schema archaeology risk** — multiple migrations modify same objects (handle_new_user redefined 7x, profiles_plan_type_check redefined 5x). Disaster recovery from migration replay would be fragile. | HIGH | 24 | Squash plan exists (`supabase/docs/MIGRATION-SQUASH-PLAN.md`). Target: ~5-10 canonical migrations. |
| DB-003 | **Duplicate trigger functions not cleaned up** — `update_updated_at()` vs `set_updated_at()` both exist. DEBT-207 re-pointed triggers to `set_updated_at()` but original still exists. | HIGH | 2 | Confusion risk. Drop `update_updated_at()` after verifying no references. |

### MEDIUM

| ID | Descricao | Severidade | Esforco (h) | Racional |
|----|-----------|-----------|-------------|----------|
| DB-004 | **`classification_feedback.user_id` still references `auth.users`** — all other tables standardized to `profiles(id)` but bridge migration re-introduced old pattern. | MEDIUM | 2 | Inconsistent cascade behavior. Create migration to re-point FK. |
| DB-005 | **Hardcoded Stripe price IDs in migrations** — production price_ids (price_1Sy..., price_1T1..., price_1T5...) in migration files. Re-running against staging inserts production price IDs. | MEDIUM | 4 | Move to environment-aware seed script. |
| DB-006 | **`ingestion_checkpoints.crawl_batch_id` lacks enforced FK to `ingestion_runs`** — relationship documented but not enforced. Orphan checkpoints possible. | MEDIUM | 2 | Mitigated by monitoring function. Consider FK with NOT VALID + VALIDATE. |
| DB-007 | **`search_state_transitions.search_id` has no FK to `search_sessions`** — no referential integrity. Orphan transitions possible. | MEDIUM | 2 | Add FK with ON DELETE CASCADE if performance acceptable. |
| DB-008 | **Multiple tables lack retention/cleanup strategy** — search_state_transitions, classification_feedback, alert_runs, mfa_recovery_attempts grow without bound. | MEDIUM | 4 | Add pg_cron cleanup jobs: transitions >90 days, feedback >12 months, attempts >30 days. |
| DB-009 | **`organizations/organization_members` FKs** — self-referencing RLS policy on org_members queries itself, which PostgreSQL optimizes poorly. | MEDIUM | 4 | Monitor query performance. Consider denormalization. |
| DB-010 | **No VACUUM ANALYZE scheduled for high-churn tables** — pncp_raw_bids has daily hard deletes. Bloat monitoring exists but no automated VACUUM. | MEDIUM | 2 | Add pg_cron: VACUUM ANALYZE pncp_raw_bids daily after purge. |
| DB-011 | **Trigger naming partially standardized** — DEBT-207 standardized `trg_` prefix but 4 triggers still use `tr_` or `trigger_` prefix. | MEDIUM | 2 | Complete rename in follow-up migration. |

### LOW

| ID | Descricao | Severidade | Esforco (h) | Racional |
|----|-----------|-----------|-------------|----------|
| DB-012 | **Dead plan catalog entries** — multiple legacy plans with `is_active=false`: pack_5, pack_10, pack_20, monthly, annual, consultor_agil, maquina, sala_guerra, free. | LOW | 2 | Consider `deprecated_at` timestamp for audit trail. |
| DB-013 | **`profiles.context_data` schema not enforced** — JSONB has size constraint but no schema validation at DB level. | LOW | 4 | Consider CHECK constraint with jsonb_typeof or validation function. |
| DB-014 | **Redundant index on `alert_preferences.user_id`** — `idx_alert_preferences_user_id` is redundant with UNIQUE constraint. | LOW | 1 | Drop redundant index. |
| DB-015 | **`google_sheets_exports` GIN index on `search_params` rarely queried** — write amplification cost for unlikely query pattern. | LOW | 1 | Verify usage; drop if unused. |
| DB-016 | **`plan_features.id` uses SERIAL instead of UUID** — inconsistent with all other tables. | LOW | 1 | No action needed unless migrating to distributed DB. |
| DB-017 | **Overly broad admin RLS checks via subquery** — `profiles.is_admin = true` subquery executes per-row on stripe_webhook_events, audit_events, reconciliation_log, conversations, messages. | LOW | 8 | Consider JWT claim for admin status at scale. |
| DB-018 | **`user_subscriptions.annual_benefits` column is vestigial** — superseded by `plan_features` table, defaults to '{}', not populated by any code path. | LOW | 1 | Verify, then drop in cleanup migration. |
| DB-019 | **Missing composite indexes** — `search_state_transitions (search_id, to_state)` for debugging queries; `classification_feedback (setor_id, created_at DESC)` for sector analysis. | LOW | 2 | Add indexes. |
| DB-020 | **Timestamp naming inconsistency** — most tables use `created_at`/`updated_at` but `google_sheets_exports` uses `last_updated_at`, `health_checks` uses `checked_at`. | LOW | 2 | Standardize in cleanup migration. |

---

## 3. Debitos de Frontend/UX (from frontend-spec.md)

> :warning: **PENDENTE: Revisao do @ux-design-expert (Fase 6)**

### CRITICAL

| ID | Descricao | Severidade | Esforco (h) | Racional |
|----|-----------|-----------|-------------|----------|
| FE-001 | **UX-CRIT-001: Search stuck at 78% for 130+ seconds** — SSE progress stalls when backend enters filtering/LLM phase (no granular progress events). Users have no indication if search is working or has silently failed. | CRITICAL (UX) | 12 | Add intermediate progress events for post-fetch stages. Add "taking longer than expected" message at 60s with option to cancel or view partial results. |

### HIGH

| ID | Descricao | Severidade | Esforco (h) | Racional |
|----|-----------|-----------|-------------|----------|
| FE-002 | **TD-001: `useSearchOrchestration` mega-hook (200+ lines)** — orchestrates 9+ sub-hooks, trial state, modals, tours. Difficult to maintain and test. | HIGH | 16 | Extract `useSearchModals`, `useSearchTours`, `useTrialOrchestration`. |
| FE-003 | **TD-008 + A11Y-002: `ViabilityBadge` uses `title` for critical data** — viability factor breakdown uses HTML title attribute, inaccessible on mobile/touch. | HIGH | 4 | Replace with Radix Tooltip or accessible popover component. |
| FE-004 | **TD-011: Divergent auth guard patterns** — `(protected)/layout.tsx` for route-group pages AND manual `useEffect` redirect in `/buscar`. Risk of auth bypass if patterns diverge. | HIGH | 8 | Unify: either move `/buscar` into route group or extract shared hook. |
| FE-005 | **TD-012: Dual component directory structure** — `app/components/` (50+ files) vs `components/` (33+ files) with unclear separation criteria. AuthProvider and BackendStatusIndicator in `app/components/`; NavigationShell and Sidebar in `components/`. | HIGH | 16 | Define clear rule: `components/` for truly shared, `app/components/` for app-shell. Move providers to `providers/` directory. |
| FE-006 | **UX-CRIT-002: Error 524 exposes technical details** — retry counter and technical phrasing create user anxiety. Error recovery is manual-only. | HIGH | 6 | Auto-retry first 2 attempts silently. Only show banner after all automatic retries exhausted. Remove attempt counter. |

### MEDIUM

| ID | Descricao | Severidade | Esforco (h) | Racional |
|----|-----------|-----------|-------------|----------|
| FE-007 | **TD-002: 12 banners on search page** — excessive information for average user. Cognitive overload risk. | MEDIUM | 8 | Consolidate into stacked notification system with priority suppression. |
| FE-008 | **TD-003: `/admin` uses useState + manual fetch instead of SWR** — inconsistent with rest of app. Stale data risk. | MEDIUM | 4 | Migrate to SWR for consistency. |
| FE-009 | **TD-009 + A11Y-004: No `aria-live` region for dynamic search results** — screen readers not notified when results arrive. 12 banner types lack consistent `role="alert"` or `aria-live`. | MEDIUM | 4 | Add `aria-live="polite"` region announcing "X oportunidades encontradas". |
| FE-010 | **TD-010: `mensagens/page.tsx` at 591 lines** — largest page file, needs decomposition. | MEDIUM | 8 | Extract ConversationList, ConversationDetail, MessageComposer. |
| FE-011 | **TD-005: Potential `any` types in API proxy routes** — type safety gap. | MEDIUM | 6 | Audit and type all proxy routes. |
| FE-012 | **A11Y-001: SVG icons lacking `role="img"` or `aria-label`** — some informational icons only have `aria-hidden`. | MEDIUM | 4 | Audit informational vs decorative SVGs. |
| FE-013 | **A11Y-003: Inconsistent landmarks** — not all pages have `role="main"`, `<nav>`, `<footer>` marked correctly. | MEDIUM | 4 | Standardize landmarks across all protected pages. |
| FE-014 | **A11Y-008: Forms missing `aria-describedby`** — search fields lack linked hints/instructions. | MEDIUM | 4 | Add `aria-describedby` to all form fields with hints. |
| FE-015 | **TD-014: `prefers-reduced-motion` not systematically respected** — Framer Motion animations and 8 custom CSS keyframes run regardless of user preference. | MEDIUM | 4 | Add media query check globally for motion-sensitive users. |
| FE-016 | **TD-015: No ErrorBoundary wrapping SWRProvider/UserProvider** — if providers throw during initialization, entire app crashes with generic global-error.tsx. | MEDIUM | 3 | Wrap provider stack in ErrorBoundary with minimal recovery UI. |
| FE-017 | **DEBT-FE-012: Feature gates hardcoded** — only `alertas` is gated. No feature flag service on frontend. | MEDIUM | 6 | Implement client-side feature flag evaluation from backend. |
| FE-018 | **UX-MED-001: Dark mode contrast on search form** — low contrast between sector dropdown and dark surfaces. | MEDIUM | 2 | Increase `--surface-2` separation or add border-accent to form inputs. |
| FE-019 | **60+ API proxy routes** — many are simple GET/POST wrappers. `create-proxy-route.ts` factory handles most but custom implementations duplicate error handling. | MEDIUM | 8 | Further consolidate via factory; consider single catch-all for simple proxies. |
| FE-020 | **No edge caching for stable endpoints** — `/api/setores` and `/api/plans` change infrequently but lack `Cache-Control` headers. | MEDIUM | 2 | Add `Cache-Control: public, s-maxage=3600` to stable endpoints. |

### LOW

| ID | Descricao | Severidade | Esforco (h) | Racional |
|----|-----------|-----------|-------------|----------|
| FE-021 | **TD-004: SVGs inline in multiple components** — MobileDrawer, BottomNav, ErrorStates use inline SVGs instead of lucide-react (already a dependency). | LOW | 4 | Migrate to lucide-react. |
| FE-022 | **DEBT-012: Raw hex values instead of semantic tokens** — some components bypass token system. | LOW | 4 | Migrate to Tailwind semantic classes. |
| FE-023 | **DEBT-011: `/conta` is redirect to `/conta/perfil`** — flash of redirect instead of tabs layout. | LOW | 2 | Add tab navigation at `/conta` level. |
| FE-024 | **DEBT-105: Duplicate footers** — NavigationShell footer + buscar custom footer. | LOW | 2 | Consolidate into single footer pattern. |
| FE-025 | **DEBT-108: RootLayout async for CSP nonce** — unnecessary complexity if middleware always present. | LOW | 2 | Simplify if middleware is guaranteed. |
| FE-026 | **TD-006: Programmatic SEO pages may have thin/duplicate content** — `/como-*` pages are structurally similar (316-349 lines each). | LOW | 4 | Audit for duplicate content penalty risk. |
| FE-027 | **TD-007: SearchResults.tsx backward-compat re-exports** — indicates incomplete refactor. | LOW | 1 | Clean up re-exports. |
| FE-028 | **A11Y-005: Dark mode brand-blue contrast borderline** — `#116dff` vs `#121212` = ~4.5:1, borderline AA for small text. | LOW | 2 | Increase contrast or use lighter blue variant in dark mode. |
| FE-029 | **A11Y-006/007: Focus order in BuscarModals + BottomNav overlay** — multiple stacked modals may confuse focus; overlay background lacks `aria-hidden="true"`. | LOW | 3 | Add `aria-hidden` to overlay; audit modal stacking order. |
| FE-030 | **UX-MED-002: Mobile search limited vertical space** — search form fills entire mobile viewport on first visit. | LOW | 4 | Collapse title/description for returning users. |
| FE-031 | **UX-MED-003: Dashboard chart sparse for low-usage users** — chart shows minimal data points for users with <10 searches. | LOW | 3 | Show insight card instead of sparse chart for low-activity users. |
| FE-032 | **UX-MED-004: Pipeline empty state wordy** — 3-step instructions too verbose. | LOW | 1 | Reduce to 2 steps. |

---

## 4. Debitos Cross-Cutting

| ID | Descricao | Areas | Severidade | Esforco (h) | Racional |
|----|-----------|-------|-----------|-------------|----------|
| CROSS-001 | **SSE chain fragility spans backend + frontend** — Backend: Redis Streams + heartbeat (15s) + adaptive skip. Frontend: `bodyTimeout(0)` disables timeout protection, `AbortController` for cleanup. Railway: ~120s idle kills long searches. The search-stuck-at-78% UX issue (FE-001) is the user-visible symptom of backend progress event gaps (SYS-013). | Backend + Frontend + Infra | HIGH | 16 | Requires coordinated fix: backend adds post-fetch stage progress events; frontend adds "longer than expected" UI; infrastructure timeout tuning. |
| CROSS-002 | **Auth pattern divergence across stack** — Backend: JWT (ES256+JWKS) with local validation. Frontend: `(protected)/layout.tsx` route group + manual `useEffect` in `/buscar` (FE-004). Middleware: server-side session validation. Three independent auth enforcement points that could diverge. | Backend + Frontend | HIGH | 8 | Unify into single auth enforcement pathway per layer. |
| CROSS-003 | **Feature flag governance absent at all layers** — Backend: 30+ flags in `config/features.py` without lifecycle. Frontend: hardcoded gates (only `alertas`). No shared flag service, no feature flag evaluation from backend to frontend. | Backend + Frontend | MEDIUM | 12 | Implement flag lifecycle management backend-side; expose to frontend via API. |
| CROSS-004 | **Migration volume + schema archaeology** — 106 Supabase migrations impact deploy time (DB-002). Backend code references specific migration-era patterns. Migration squash requires coordination with deploy pipeline (CI auto-apply). | Database + Infra | HIGH | 24 | Already has squash plan. Requires careful coordination with CI 3-layer migration defense. |
| CROSS-005 | **LLM dependency spans classification + summarization + cost** — Classification in `llm_arbiter.py`, summarization in `llm.py`, cost tracking absent (SYS-014). Backend timeout configuration inconsistent (SYS-010). Frontend shows LLM badges without fallback explanation when LLM is down. | Backend + Frontend | MEDIUM | 8 | Centralize LLM config; add cost counters; improve frontend LLM failure UX. |
| CROSS-006 | **Scaling constraint affects all layers** — SIGSEGV (SYS-002) forces single-process. In-memory L1 cache, SSE queues, progress tracker all assume single process. Scaling to multiple Railway services requires Redis-based coordination for all three. | Backend + Infra | CRITICAL | 32 | Document scaling path. Evaluate Redis coordination architecture. |

---

## 5. Matriz Preliminar de Priorizacao

| ID | Debito | Area | Severidade | Impacto | Esforco (h) | Prioridade |
|----|--------|------|-----------|---------|-------------|------------|
| DB-001 | handle_new_user() missing SET search_path | DB | HIGH | Security | 1 | **P0** |
| DB-008 | Tables without retention (state_transitions, feedback, etc.) | DB | MEDIUM | Storage/Perf | 4 | **P0** |
| FE-001 | Search stuck at 78% — no post-fetch progress events | FE/UX | CRITICAL | User experience | 12 | **P0** |
| FE-006 | Error 524 exposes technical details + manual-only retry | FE/UX | HIGH | User anxiety | 6 | **P0** |
| SYS-001 | Filter package at 6,422 LOC | Backend | CRITICAL | Maintainability | 40 | **P1** |
| SYS-002 | SIGSEGV single-process constraint | Backend | CRITICAL | Scalability | 24 | **P1** |
| CROSS-006 | Scaling constraint (Redis coordination needed) | Cross | CRITICAL | Scalability | 32 | **P1** |
| CROSS-001 | SSE chain fragility (backend + frontend + infra) | Cross | HIGH | Reliability | 16 | **P1** |
| FE-002 | useSearchOrchestration mega-hook | FE | HIGH | Maintainability | 16 | **P1** |
| FE-004 | Divergent auth guard patterns | FE | HIGH | Security | 8 | **P1** |
| FE-005 | Dual component directory structure | FE | HIGH | DX | 16 | **P1** |
| DB-002 | 106 migrations — schema archaeology risk | DB | HIGH | Dev productivity | 24 | **P1** |
| DB-003 | Duplicate trigger functions | DB | HIGH | Confusion | 2 | **P1** |
| SYS-003 | cron_jobs.py at 2,251 LOC | Backend | HIGH | Maintainability | 16 | **P1** |
| SYS-004 | job_queue.py at 2,229 LOC | Backend | HIGH | Maintainability | 16 | **P1** |
| SYS-005 | Cache package complexity (14 files + root shims) | Backend | HIGH | Cognitive overhead | 24 | **P1** |
| SYS-006 | consolidation.py at 1,394 LOC | Backend | HIGH | Maintainability | 16 | **P2** |
| SYS-007 | Sync + async PNCP client coexistence | Backend | HIGH | Dead code | 12 | **P2** |
| SYS-008 | Feature flag sprawl (30+ without lifecycle) | Backend | HIGH | Config complexity | 8 | **P2** |
| CROSS-002 | Auth pattern divergence | Cross | HIGH | Security | 8 | **P2** |
| CROSS-004 | Migration volume + schema archaeology | Cross | HIGH | Deploy/DX | 24 | **P2** |
| FE-003 | ViabilityBadge title attr inaccessible | FE | HIGH | A11y | 4 | **P2** |
| FE-007 | 12 banners cognitive overload | FE | MEDIUM | UX | 8 | **P2** |
| FE-009 | No aria-live for search results | FE | MEDIUM | A11y | 4 | **P2** |
| FE-010 | mensagens/page.tsx at 591 lines | FE | MEDIUM | Maintainability | 8 | **P2** |
| FE-016 | No ErrorBoundary on providers | FE | MEDIUM | Resilience | 3 | **P2** |
| FE-017 | Frontend feature gates hardcoded | FE | MEDIUM | Flexibility | 6 | **P2** |
| FE-020 | No edge caching for stable endpoints | FE | MEDIUM | Performance | 2 | **P2** |
| DB-004 | classification_feedback FK to auth.users | DB | MEDIUM | Data integrity | 2 | **P2** |
| DB-005 | Hardcoded Stripe price IDs in migrations | DB | MEDIUM | Env safety | 4 | **P2** |
| DB-006 | ingestion_checkpoints FK gap | DB | MEDIUM | Data integrity | 2 | **P2** |
| DB-007 | search_state_transitions FK gap | DB | MEDIUM | Data integrity | 2 | **P2** |
| DB-009 | org_members self-referencing RLS perf | DB | MEDIUM | Performance | 4 | **P2** |
| DB-010 | No VACUUM ANALYZE for high-churn tables | DB | MEDIUM | Performance | 2 | **P2** |
| DB-011 | Trigger naming inconsistency (4 remaining) | DB | MEDIUM | Consistency | 2 | **P2** |
| SYS-009 | Root filter_*.py duplication | Backend | MEDIUM | Confusion | 8 | **P2** |
| SYS-010 | LLM timeout config scattered | Backend | MEDIUM | Reliability | 4 | **P2** |
| SYS-011 | Schemas scattered (root + dir) | Backend | MEDIUM | DX | 4 | **P2** |
| SYS-012 | Large route files (11K+ LOC across 37) | Backend | MEDIUM | Maintainability | 16 | **P2** |
| SYS-013 | SSE reliability fragility | Backend | MEDIUM | Reliability | 12 | **P2** |
| SYS-014 | LLM cost monitoring absent | Backend | MEDIUM | Cost risk | 6 | **P2** |
| SYS-015 | Monorepo without workspace tooling | Backend | MEDIUM | DX | 8 | **P3** |
| CROSS-003 | Feature flag governance absent | Cross | MEDIUM | Config debt | 12 | **P2** |
| CROSS-005 | LLM dependency spans multiple layers | Cross | MEDIUM | Reliability/Cost | 8 | **P2** |
| FE-008 | Admin page manual fetch | FE | MEDIUM | Consistency | 4 | **P3** |
| FE-011 | Proxy routes any types | FE | MEDIUM | Type safety | 6 | **P3** |
| FE-012 | SVG icons missing accessibility | FE | MEDIUM | A11y | 4 | **P3** |
| FE-013 | Inconsistent landmarks | FE | MEDIUM | A11y | 4 | **P3** |
| FE-014 | Forms missing aria-describedby | FE | MEDIUM | A11y | 4 | **P3** |
| FE-015 | prefers-reduced-motion not respected | FE | MEDIUM | A11y | 4 | **P3** |
| FE-018 | Dark mode contrast on search form | FE | MEDIUM | UX | 2 | **P3** |
| FE-019 | 60+ API proxy routes consolidation | FE | MEDIUM | Maintenance | 8 | **P3** |
| SYS-016 | main.py backward-compat shims | Backend | LOW | Code hygiene | 2 | **P3** |
| SYS-017 | Experimental clients unused | Backend | LOW | Code hygiene | 4 | **P3** |
| SYS-018 | auth.py dual-hash transition | Backend | LOW | Code hygiene | 2 | **P3** |
| SYS-019 | search_cache.py root re-export | Backend | LOW | Confusion | 1 | **P3** |
| DB-012 | Dead plan catalog entries | DB | LOW | Data hygiene | 2 | **P3** |
| DB-013 | context_data schema unenforced | DB | LOW | Data integrity | 4 | **P3** |
| DB-014 | Redundant alert_preferences index | DB | LOW | Write perf | 1 | **P3** |
| DB-015 | google_sheets_exports GIN unused | DB | LOW | Write perf | 1 | **P3** |
| DB-016 | plan_features SERIAL vs UUID | DB | LOW | Consistency | 1 | **P3** |
| DB-017 | Admin RLS subquery per-row | DB | LOW | Performance | 8 | **P3** |
| DB-018 | annual_benefits vestigial column | DB | LOW | Data hygiene | 1 | **P3** |
| DB-019 | Missing composite indexes | DB | LOW | Query perf | 2 | **P3** |
| DB-020 | Timestamp naming inconsistency | DB | LOW | Consistency | 2 | **P3** |
| FE-021 | Inline SVGs vs lucide-react | FE | LOW | Bundle size | 4 | **P3** |
| FE-022 | Raw hex values vs tokens | FE | LOW | Consistency | 4 | **P3** |
| FE-023 | /conta redirect flash | FE | LOW | UX polish | 2 | **P3** |
| FE-024 | Duplicate footers | FE | LOW | Landmarks | 2 | **P3** |
| FE-025 | RootLayout async CSP nonce | FE | LOW | Complexity | 2 | **P3** |
| FE-026 | SEO pages thin content risk | FE | LOW | SEO | 4 | **P3** |
| FE-027 | SearchResults re-export cleanup | FE | LOW | Code hygiene | 1 | **P3** |
| FE-028 | Dark mode brand-blue contrast | FE | LOW | A11y | 2 | **P3** |
| FE-029 | Focus order in modals/overlay | FE | LOW | A11y | 3 | **P3** |
| FE-030 | Mobile search vertical space | FE | LOW | Mobile UX | 4 | **P3** |
| FE-031 | Dashboard sparse chart | FE | LOW | UX polish | 3 | **P3** |
| FE-032 | Pipeline empty state wordy | FE | LOW | UX polish | 1 | **P3** |

**Summary:**
- **P0 (immediate):** 4 items, ~23h
- **P1 (this sprint):** 12 items, ~236h
- **P2 (next sprint):** 26 items, ~156h
- **P3 (backlog):** 21 items, ~91h
- **Total:** 63 items, ~506h (includes overlap from CROSS items sharing effort with SYS/FE/DB items)

---

## 6. Dependencias entre Debitos

```
CROSS-006 (scaling constraint) ──depends on──> SYS-002 (SIGSEGV resolution)
                                               Must resolve SIGSEGV before
                                               designing multi-process arch

SYS-001 (filter decomposition) ──enables──> SYS-009 (root filter cleanup)
                                            Can't clean root shims until
                                            package is canonical

DB-002 (migration squash) ──depends on──> DB-003 (duplicate triggers cleanup)
                          ──depends on──> DB-001 (handle_new_user fix)
                          ──depends on──> DB-004 (FK standardization)
                          ──depends on──> DB-011 (trigger naming)
                                          Squash should happen AFTER these
                                          individual fixes to avoid squashing
                                          then re-migrating

CROSS-001 (SSE chain fix) ──includes──> FE-001 (search stuck at 78%)
                          ──includes──> SYS-013 (SSE reliability)
                                        Single coordinated effort

CROSS-003 (feature flag governance) ──includes──> SYS-008 (backend flags)
                                    ──includes──> FE-017 (frontend gates)
                                                  Single unified implementation

FE-005 (component directory consolidation) ──enables──> FE-010 (mensagens decomposition)
                                                         Need clear structure before
                                                         extracting new components

FE-002 (useSearchOrchestration decomp) ──enables──> FE-004 (auth guard unification)
                                                     Auth logic currently embedded
                                                     in the mega-hook

SYS-003 (cron_jobs decomp) ──enables──> SYS-004 (job_queue decomp)
                                         Both reference same Redis pool patterns;
                                         decouple pool management first

SYS-005 (cache consolidation) ──enables──> SYS-019 (search_cache.py root removal)
                                           Root file exists as shim for cache/
```

---

## 7. Perguntas para Especialistas

### Para @data-engineer (Fase 5):

1. **DB-001 (handle_new_user SET search_path):** The function has been redefined 7 times across migrations. Can you confirm the current final definition and verify that adding `SET search_path = public` will not break the trigger chain with `auth.users`?

2. **DB-002 (migration squash):** The squash plan exists at `supabase/docs/MIGRATION-SQUASH-PLAN.md`. What is the estimated risk of replaying 106 migrations in a disaster recovery scenario? Have you tested a clean DB creation from the full migration chain recently?

3. **DB-008 (retention policies):** `search_state_transitions` will grow proportionally to search volume. At current traffic, what is the projected table size in 6 months? Is 90-day retention sufficient for debugging purposes, or should we keep longer for audit compliance?

4. **DB-010 (VACUUM ANALYZE):** Is Supabase Cloud's auto-vacuum aggressive enough for the daily DELETE pattern on `pncp_raw_bids`? The `check_pncp_raw_bids_bloat()` function exists but is it being monitored regularly?

5. **DB-006 (ingestion_checkpoints FK):** The orphan monitoring via view + function was added in DEBT-207. Is this sufficient, or would an enforced FK with `NOT VALID + VALIDATE` pattern provide meaningful additional safety without impacting ingestion throughput?

6. **DB-017 (admin RLS subquery):** At what user/row scale would the per-row admin check in RLS policies become a performance concern? Is the current scale (35 tables, ~40K bids, ~few hundred users) anywhere near that threshold?

7. **Missing from SCHEMA.md:** Are there any planned schema changes for upcoming features (alerts email system, organization billing, partner revenue share) that would affect the squash timing?

### Para @ux-design-expert (Fase 6):

1. **FE-001 (search stuck at 78%):** The screenshot shows 130+ seconds at "Filtrando resultados". What is the acceptable maximum wait time before the user should be given an option to view partial results? Should we show a different message per phase (fetching -> filtering -> classifying -> generating)?

2. **FE-007 (12 banners):** Which of the 12 search banners do users actually read/interact with? Have you observed any user behavior data (Clarity heatmaps, Mixpanel events) that indicates which banners are ignored? Recommendation for priority ordering?

3. **FE-005 (component directories):** What is the proposed separation rule? Suggested structure: `components/` (design system primitives + reusable), `app/components/` (providers + app shell), `app/buscar/components/` (search-specific). Does this align with your design system vision?

4. **FE-003 (ViabilityBadge):** The viability factor breakdown is critical decision information. What is the preferred interaction pattern on mobile? Options: (a) tap to expand inline, (b) bottom sheet, (c) separate detail view. What has worked in similar B2G tools?

5. **A11Y-002 vs mobile UX:** The ViabilityBadge issue (title attr) affects both accessibility and mobile usability. Should the fix also change the visual presentation (e.g., always-visible mini breakdown below the badge instead of hover-only)?

6. **FE-018 (dark mode contrast):** The `--surface-2` vs `--surface-0` gap in dark mode is subtle. Should we increase the gap globally, or only add border-accent to specific interactive elements (dropdowns, inputs)?

7. **UX-CRIT-002 (error 524):** The current auto-retry shows attempt counter (1/3, 2/3, 3/3). If we remove the counter and retry silently, should we still show a progress indicator (e.g., subtle pulse) so the user knows the system is working?

8. **FE-030 (mobile vertical space):** For returning users, should we collapse the entire search header (title + description) or just the description? How does this interact with the onboarding flow for first-time users?

---

## 8. Riscos Identificados

### R-001: Single-Process Scaling Ceiling (CRITICAL)

**Risk:** The SIGSEGV constraint (SYS-002) prevents multi-process mode. Current architecture assumes single process for in-memory state (L1 cache, SSE queues, progress tracker). As user base grows, the only option is vertical scaling (more CPU/RAM on Railway) or multiple isolated Railway services with Redis-based coordination.

**Impact:** Revenue ceiling. If 10+ concurrent users perform searches simultaneously, the single process may become CPU-bound during LLM classification (ThreadPoolExecutor with 10 workers).

**Mitigation path:** (1) Benchmark current capacity under load. (2) Design Redis-based coordination for L1 cache, SSE, and progress. (3) Evaluate whether newer cryptography versions (>47.0) resolve the SIGSEGV.

### R-002: Migration Chain Fragility (HIGH)

**Risk:** 106 migrations with objects redefined multiple times (handle_new_user 7x, plan_type_check 5x). A disaster recovery requiring full migration replay has not been tested recently. Migration squash has been planned but not executed.

**Impact:** If Supabase Cloud has an incident requiring DB recreation, the migration chain may fail on intermediate states.

**Mitigation:** Execute squash plan. Test clean migration replay quarterly.

### R-003: SSE Chain Timeout Mismatch (HIGH)

**Risk:** The timeout chain (Per-UF 30s -> Per-Source 80s -> Consolidation 100s -> Pipeline 110s -> ARQ 300s) works well for data fetching, but post-fetch stages (filtering, LLM, viability) lack progress events. Users see the search "stuck" for 30-60+ seconds during these phases. Railway's ~120s idle timeout can kill SSE connections, and `bodyTimeout(0)` removes the safety net entirely.

**Impact:** User trust erosion. Users may close the tab or assume the system is broken during legitimate post-fetch processing.

**Mitigation:** Add granular progress events for post-fetch stages (FE-001 + CROSS-001).

### R-004: Auth Guard Divergence (HIGH)

**Risk:** Three independent auth enforcement points (middleware, route group layout, manual useEffect) could diverge silently. A change to one pattern may not be reflected in others.

**Impact:** Potential auth bypass allowing unauthenticated access to `/buscar` data.

**Mitigation:** Unify auth pattern (FE-004 + CROSS-002).

### R-005: Feature Flag Combinatorial Explosion (MEDIUM)

**Risk:** 30+ backend feature flags without lifecycle management creates an exponentially growing test matrix. No frontend feature flag service means features are gated by hardcoded checks that may go stale.

**Impact:** Untested flag combinations may cause unexpected behavior in production. Old flags that should be removed add cognitive overhead.

**Mitigation:** Implement flag lifecycle with expiration dates (CROSS-003).

### R-006: LLM Cost Exposure at Scale (MEDIUM)

**Risk:** No cost monitoring or budget alerts. A single search can classify 200+ items at ~R$0.00007/each. With ThreadPoolExecutor(max_workers=10), burst scenarios could generate unexpected OpenAI bills. If a coding error removes the MAX_ZERO_MATCH_ITEMS cap, costs could spike.

**Impact:** Unexpected OpEx as user base grows.

**Mitigation:** Add cost tracking metrics (SYS-014). Implement budget alerts. Consider batch classification to reduce per-item overhead.

### R-007: Accessibility Legal Exposure (MEDIUM)

**Risk:** Brazilian accessibility law (Lei 13.146/2015 - Lei Brasileira de Inclusao) requires digital accessibility for government-related tools. SmartLic serves B2G companies and interfaces with government procurement systems. Critical information (viability factors) is inaccessible on mobile (FE-003), search results are not announced to screen readers (FE-009), and `prefers-reduced-motion` is not respected (FE-015).

**Impact:** Potential legal compliance risk and exclusion of users with disabilities.

**Mitigation:** Address HIGH and MEDIUM a11y items in P1/P2 sprints.

### R-008: Data Source Single Point of Failure (LOW)

**Risk:** The datalake strategy (Layer 1) successfully decouples search from live APIs. However, if the daily full crawl fails for multiple consecutive days AND the 12-day retention expires, the datalake becomes stale. The fallback to live API fetch has its own fragility (PNCP rate limits, ComprasGov historically unreliable).

**Impact:** Users receive outdated or no results during multi-day ingestion failures.

**Mitigation:** Already partially mitigated by ingestion monitoring, checkpoint tracking, and 3x daily incremental crawls. Consider alerting when ingestion fails >2 consecutive runs.

---

*Document generated 2026-03-31 by @architect (Aria) as Phase 4 of Brownfield Discovery workflow.*
*Pending: Phase 5 (@data-engineer review), Phase 6 (@ux-design-expert review), Phase 7 (@qa gate).*
