# Technical Debt Assessment - DRAFT v2.0

## Para Revisao dos Especialistas

**Projeto:** SmartLic/BidIQ
**Data:** 2026-02-15
**Status:** DRAFT - Pendente revisao dos especialistas
**Versao anterior:** v1.0 (2026-02-11, commit `808cd05`)
**Commit atual:** `b80e64a` (branch `main`)
**Autor:** @architect (Helix) - Brownfield Discovery Phase 4 Consolidation
**Fontes:**
1. `docs/architecture/system-architecture.md` v2.0 -- @architect (Helix) - Phase 1
2. `supabase/docs/SCHEMA.md` -- @data-engineer (Datum) - Phase 2
3. `supabase/docs/DB-AUDIT.md` -- @data-engineer (Datum) - Phase 2
4. `docs/frontend/frontend-spec.md` -- @ux-design-expert (Pixel) - Phase 3

---

## Changelog v1.0 -> v2.0

Since the v1.0 draft (2026-02-11), significant work has been completed:

**Resolved from v1.0:**
- SYS-C02 (main.py monolith 1959 lines): RESOLVED by STORY-202 route decomposition
- SYS-H03 (migrations not tracked): RESOLVED -- 26 migrations now in `supabase/migrations/`
- SYS-H04 (business logic in main.py helpers): RESOLVED by STORY-202 extraction to `authorization.py`
- SYS-M01 (no correlation ID): RESOLVED -- `CorrelationIDMiddleware` in `middleware.py`
- SYS-M08 (no API versioning): RESOLVED -- dual mount `/v1/` + legacy root with sunset headers
- SYS-L04 (no request logging): RESOLVED -- structured JSON logging in `config.py`
- SYS-L06 (no Redis health check): RESOLVED -- Redis checked in `/health` endpoint
- DB-C01 (database.py incorrect URL): Status unclear -- see questions for @data-engineer
- DB-C02 (user_subscriptions service role): RESOLVED by migration 016
- DB-C03 (stripe_webhook admin check): RESOLVED by migration 016
- DB-H03 (missing stripe_subscription_id index): RESOLVED by migration 016
- DB-H04 (overly permissive RLS): RESOLVED for old tables by migration 016; REGRESSED for 2 new tables
- DB-H05 (profiles INSERT policy): RESOLVED by migration 020
- DB-M01 (inconsistent FKs): PARTIALLY RESOLVED by migration 018 (3 of 5 tables; 2 new tables regressed)
- DB-M02 (legacy plan_type CHECK): RESOLVED by migration 020
- DB-M03 (updated_at missing on user_subscriptions): RESOLVED by migration 021
- DB-M06 (N+1 conversations): RESOLVED by migration 019 RPC function
- DB-L01 (plans missing updated_at): RESOLVED by migration 020
- DB-L02 (no monthly_quota cleanup): RESOLVED by migration 022 pg_cron
- DB-L03 (no webhook_events cleanup): RESOLVED by migration 022 pg_cron
- DB-L04 (redundant provider index): RESOLVED by migration 022 (dropped)
- FE-C01 (buscar monolith ~1100 lines): RESOLVED -- decomposed to 384 lines + sub-components + hooks
- FE-C02 (localhost fallback analytics): Status unclear -- needs verification
- FE-H04 (native alert()): Likely resolved -- toast system now in place
- FE-M08 (no middleware auth guards): RESOLVED -- `middleware.ts` with Supabase SSR cookie check

**New issues introduced since v1.0:**
- DB-01/DB-02: Critical schema integrity issues in new migrations 024-026
- DB-03/DB-04: RLS security regression on new tables (same pattern previously fixed)
- SYS-03: LLM Arbiter hardcoded sector description (newly identified)
- Multiple frontend architecture items from comprehensive frontend spec analysis

---

## Resumo Executivo

O SmartLic/BidIQ e um SaaS em producao (POC v0.3) para descoberta automatizada de oportunidades de contratacao publica no PNCP. O sistema melhorou significativamente desde a auditoria anterior (Feb 11), com decomposicao de monolitos, melhoria de RLS, e infraestrutura de observabilidade. Porem, novas features (pipeline, cache, profile context) introduziram regressoes nos mesmos patterns que haviam sido corrigidos.

**Avaliacao Geral de Saude:**

| Area | Nota Anterior (Feb 11) | Nota Atual (Feb 15) | Tendencia |
|------|------------------------|----------------------|-----------|
| Backend/Arquitetura | MEDIO | MEDIO-ALTO | Melhoria (route decomposition, middleware) |
| Database | 6.5/10 | 7.5/10 | Melhoria (RLS fixes, pg_cron, indexes) |
| Frontend/UX | MEDIO-ALTO | MEDIO-ALTO | Estavel (decomposed buscar, but new prop drilling) |

**Contagem Total de Debitos (v2.0):**

| Severidade | Sistema | Database | Frontend/UX | Total |
|------------|---------|----------|-------------|-------|
| CRITICAL | 3 | 2 | 0 | **5** |
| HIGH | 7 | 2 | 6 | **15** |
| MEDIUM | 8 | 7 | 18 | **33** |
| LOW | 5 | 3 | 21 | **29** |
| **Total** | **23** | **14** | **45** | **82** |

**Esforco Total Estimado:** ~412h+

---

## 1. Debitos de Sistema (Backend/Infrastructure)

Source: `docs/architecture/system-architecture.md` v2.0 -- Section 11 Technical Debt Registry

### 1.1 CRITICAL

| ID | Descricao | Localizacao | Impacto | Esforco Est. |
|----|-----------|-------------|---------|--------------|
| SYS-01 | **Frontend test coverage below threshold (49.46% vs 60%)** -- 20+ quarantined test files. CI fails on every push. Quality gate bypassed. | `frontend/__tests__/` | CI pipeline broken; no regression safety net. | 40h |
| SYS-02 | **Dual HTTP client implementations (sync `requests` + async `httpx`)** -- duplicate retry logic, rate limiting, error handling across 1585 lines. Sync client only used in `PNCPLegacyAdapter.fetch()` single-UF fallback. | `backend/pncp_client.py` lines 223-1585 | Maintenance burden: every PNCP behavior change must be applied twice. | 16h |
| SYS-03 | **LLM Arbiter hardcoded "Vestuario e Uniformes" sector description** applied to ALL 15 sectors. Acknowledged in `config.py` line 263 but not fixed. | `backend/llm_arbiter.py` lines 115-137 | False positive/negative classification errors for 14 of 15 sectors. Business-impacting data quality. | 8h |

### 1.2 HIGH

| ID | Descricao | Localizacao | Impacto | Esforco Est. |
|----|-----------|-------------|---------|--------------|
| SYS-04 | **In-memory progress tracker not horizontally scalable** -- `_active_trackers` dict is primary registry. Redis pub/sub mode exists but secondary. | `backend/progress.py` | Two Railway instances would split SSE state. | 8h |
| SYS-05 | **In-memory auth token cache not shared across instances** | `backend/auth.py` `_token_cache` dict | Cache fragmentation in multi-instance deploy. | 4h |
| SYS-06 | **Legacy plan seeds vs current plan IDs** -- Migration 001 seeds `free`, `pack_5`, etc.; code uses `free_trial`, `consultor_agil`, etc. Translation in `quota.py` lines 525-531. | `supabase/migrations/001`, `backend/quota.py` | Brittle mapping code, confusing for new developers. | 8h |
| SYS-07 | **`save_search_session` uses synchronous `time.sleep(0.3)` in async context** -- blocks event loop on retry. | `backend/quota.py` line 910 | Event loop stall: all concurrent requests pause 300ms during retry. | 2h |
| SYS-08 | **Excel base64 fallback writes to filesystem tmpdir** -- not cleaned on crash, not scalable across instances. | `frontend/app/api/buscar/route.ts` lines 197-223 | Disk fills up. Signed URL from Supabase Storage is correct path. | 4h |
| SYS-09 | **Backend routes mounted twice** (root + `/v1/` prefix) -- doubles route table size. Sunset 2026-06-01. | `backend/main.py` lines 242-278 | Debugging confusion, doubled route dispatch memory. | 4h |
| SYS-10 | **No backend linting enforcement in CI** -- `ruff` and `mypy` mentioned but not wired into GitHub Actions. | `.github/workflows/tests.yml` | Code quality regressions not caught automatically. | 4h |

### 1.3 MEDIUM

| ID | Descricao | Localizacao | Impacto | Esforco Est. |
|----|-----------|-------------|---------|--------------|
| SYS-11 | **`search_pipeline.py` becoming god module** -- 7 stages with inline helpers. Absorbed complexity from main.py decomposition. | `backend/search_pipeline.py` | Hard to test individual stages. Growing file size. | 16h |
| SYS-12 | **Feature flags in env vars only** -- 7+ flags require container restart. POST reload is ephemeral. | `backend/config.py` | No runtime toggle UI. Operators must redeploy. | 8h |
| SYS-13 | **`dotenv` loaded before FastAPI imports** at module level. | `backend/main.py` line 33 | Env vars read at import time may use stale values. | 2h |
| SYS-14 | **Hardcoded User-Agent "BidIQ/1.0"** -- product renamed to SmartLic. | `backend/pncp_client.py` line 264 (+ AsyncPNCPClient) | Outdated branding in API traffic. | 2h |
| SYS-15 | **No database connection pooling in Supabase client** -- single global instance. | `backend/supabase_client.py` | Relies on supabase-py internal handling. May bottleneck. | 8h |
| SYS-16 | **Integration tests job is placeholder** -- echoes skip message. | `.github/workflows/tests.yml` lines 216-221 | No integration coverage in CI. | 16h |
| SYS-17 | **No request timeout for Stripe webhooks** -- handler has no explicit timeout. | `backend/webhooks/stripe.py` | Long-running DB ops could block worker, causing Stripe retries. | 4h |
| SYS-18 | **`datetime.now()` without timezone** in excel.py and llm.py. | `backend/excel.py` line 227, `backend/llm.py` line 97 | Incorrect timestamps in non-UTC environments. | 2h |

### 1.4 LOW

| ID | Descricao | Localizacao | Impacto | Esforco Est. |
|----|-----------|-------------|---------|--------------|
| SYS-19 | **Screenshot .png files in git status** (18 untracked). | Repository root | Cluttered working tree. Should be gitignored. | 1h |
| SYS-20 | **`_request_count` never reset** -- counter grows per client instance. | `backend/pncp_client.py` line 237 | Diagnostic only; could overflow. | 1h |
| SYS-21 | **`asyncio.get_event_loop().time()` deprecated** in Python 3.10+. | `backend/pncp_client.py` line 861 | Use `get_running_loop()`. | 1h |
| SYS-22 | **`format_resumo_html` function unused** -- frontend renders from JSON. | `backend/llm.py` lines 232-300 | ~70 lines dead code. | 1h |
| SYS-23 | **Deprecated migration file in directory.** | `006b_DEPRECATED_...DUPLICATE.sql` | Confuses schema understanding. | 1h |

**Subtotal Sistema:** 23 debitos | Esforco estimado: ~155h

---

## 2. Debitos de Database

Sources: `supabase/docs/SCHEMA.md` and `supabase/docs/DB-AUDIT.md` -- @data-engineer (Datum)

> **PENDENTE: Revisao do @data-engineer**

### 2.1 CRITICAL

| ID | Descricao | Localizacao | Impacto | Esforco Est. |
|----|-----------|-------------|---------|--------------|
| DB-01 | **Missing `status` column on `user_subscriptions`** -- Migration 017 trigger `sync_profile_plan_type()` references `NEW.status` with values `('active', 'trialing', 'canceled', 'expired', 'past_due')`. NO migration defines this column. If column missing: trigger is dead code and plan_type sync broken. If PostgreSQL errors on `NEW.status`: ALL subscription INSERT/UPDATE fail. | `supabase/migrations/017_sync_plan_type_trigger.sql` | P0: Potential production breakage or silent data inconsistency. | 4h |
| DB-02 | **`handle_new_user()` trigger omits explicit `plan_type` after migration 024** -- Column default remains `'free'` (from migration 001), which VIOLATES the CHECK constraint tightened by migration 020 (only allows `free_trial`, `consultor_agil`, `maquina`, `sala_guerra`, `master`). New user signups may FAIL with constraint violation. | `supabase/migrations/024_add_profile_context.sql`, `001_profiles_and_sessions.sql` | P0: New user registration potentially broken. | 2h |

### 2.2 HIGH (Security)

| ID | Descricao | Localizacao | Impacto | Esforco Est. |
|----|-----------|-------------|---------|--------------|
| DB-03 | **`pipeline_items` RLS policy `FOR ALL USING(true)` without `TO service_role`** -- Any authenticated user can read, modify, or delete other users' pipeline items via direct PostgREST requests. Per-user policies are effectively overridden. Same class of bug fixed for older tables in migration 016. | `supabase/migrations/025_create_pipeline_items.sql` lines 102-105 | Cross-user data access: data breach vector. | 2h |
| DB-04 | **`search_results_cache` RLS policy `FOR ALL USING(true)` without `TO service_role`** -- Same pattern as DB-03. Any authenticated user can access other users' cached search results, which contain business-sensitive procurement data. | `supabase/migrations/026_search_results_cache.sql` lines 31-35 | Cross-user data access: business data exposed. | 2h |

### 2.3 MEDIUM

| ID | Descricao | Localizacao | Impacto | Esforco Est. |
|----|-----------|-------------|---------|--------------|
| DB-05 | **`stripe_webhook_events` INSERT policy not scoped to `service_role`** -- Any authenticated user can insert fake webhook events, potentially poisoning idempotency checks. Partially mitigated by `'^evt_'` format CHECK. | `supabase/migrations/010_stripe_webhook_events.sql` lines 56-58 | Fake events could cause real Stripe webhooks to be skipped. | 2h |
| DB-06 | **`_ensure_profile_exists()` uses `plan_type: "free"` violating CHECK constraint** from migration 020. | `backend/quota.py` line 791 | Fallback profile creation fails with constraint violation. | 1h |
| DB-07 | **`pipeline_items` and `search_results_cache` FK to `auth.users` instead of `profiles`** -- Regression from standardization done in migration 018 for older tables. | `supabase/migrations/025`, `026` | Inconsistent FK pattern. | 4h |
| DB-08 | **Hardcoded Stripe production price IDs in migration 015** -- Not environment-aware. Migration 021 documents but doesn't fix structurally. | `supabase/migrations/015_add_stripe_price_ids_monthly_annual.sql` | Staging/dev get wrong Stripe IDs. | 4h |
| DB-09 | **`search_sessions` time-series query fetches all rows into Python** -- For users with 1000+ sessions, significant data transfer. | `backend/routes/analytics.py` lines 148-207 | Slow analytics page for power users. | 8h |
| DB-10 | **`search_results_cache.results` JSONB can be 10-100KB per entry** -- 5 per user, projected 250MB-2.5GB at scale. Max-5-per-user trigger mitigates but doesn't cap payload size. | `supabase/migrations/026_search_results_cache.sql` | Database size bloat at scale. | 4h |
| DB-11 | **`handle_new_user()` trigger redefined 4 times** (migrations 001, 007, 016, 024) -- Latest version (024) may conflict with constraints from intermediate migrations. Should be consolidated. | Multiple migration files | Fragile trigger evolution. | 4h |

### 2.4 LOW

| ID | Descricao | Localizacao | Impacto | Esforco Est. |
|----|-----------|-------------|---------|--------------|
| DB-12 | **Deprecated migration file 006b still in directory** (same as SYS-23). | `006b_DEPRECATED_...DUPLICATE.sql` | Confusion during migration runs. | 1h |
| DB-13 | **`pipeline_items` uses separate `update_pipeline_updated_at()`** instead of shared `update_updated_at()`. | `supabase/migrations/025` line 57 | Unnecessary function duplication. | 1h |
| DB-14 | **`search_results_cache` missing INSERT policy for users** -- All writes depend on the overly-permissive service role policy (DB-04). Backend uses service_role so not blocking currently. | `supabase/migrations/026` | Only relevant for future client-side caching. | 2h |

**Subtotal Database:** 14 debitos | Esforco estimado: ~39h

---

## 3. Debitos de Frontend/UX

Source: `docs/frontend/frontend-spec.md` -- @ux-design-expert (Pixel)

> **PENDENTE: Revisao do @ux-expert**

### 3.1 Technical Debt (HIGH)

| ID | Descricao | Localizacao | Impacto | Esforco Est. |
|----|-----------|-------------|---------|--------------|
| FE-01 | **SearchForm receives ~40 props** via prop drilling. SearchFormProps interface is 102 lines. Any filter change requires updating 4+ layers. | `buscar/components/SearchForm.tsx` | Maintenance nightmare; cascading changes. | 16h |
| FE-02 | **SearchResults receives ~35 props.** Same prop drilling issue as FE-01. | `buscar/components/SearchResults.tsx` | Changes cascade across hook -> page -> component. | 16h |
| FE-03 | **`useSearchFilters` is 528 lines with 40+ state variables.** Single hook doing too much. | `buscar/hooks/useSearchFilters.ts` | Impossible to test/debug individual filter logic. | 16h |
| FE-04 | **17 test files quarantined** in `__tests__/quarantine/`. Meant to be temporary (STORY-218). Includes critical files: AuthProvider, useSearch, DashboardPage. | `frontend/__tests__/quarantine/` | Reduced test confidence; critical flows untested in CI. | 24h |

### 3.2 Accessibility (HIGH)

| ID | Descricao | Localizacao | Impacto | Esforco Est. |
|----|-----------|-------------|---------|--------------|
| A11Y-01 | **Modal dialogs (save search, keyboard help) lack focus trap** -- keyboard users can Tab behind modal. | `/buscar` save dialog, keyboard help modal | WCAG 2.4.3 Focus Order violation. | 4h |
| A11Y-02 | **Modals do not use `role="dialog"` or `aria-modal="true"`** -- screen readers don't announce dialog context. | Multiple modal dialogs across app | WCAG 4.1.2 Name/Role/Value violation. | 4h |

### 3.3 Technical Debt (MEDIUM)

| ID | Descricao | Localizacao | Impacto | Esforco Est. |
|----|-----------|-------------|---------|--------------|
| FE-05 | **Inline SVGs duplicated across 20+ files** -- same icons repeated verbatim. | Multiple component files | Bundle bloat, inconsistent sizing. | 8h |
| FE-06 | **Sector list hardcoded in two places** -- `useSearchFilters.ts` (SETORES_FALLBACK) and `signup/page.tsx` (SECTORS) can drift. | `buscar/hooks/`, `app/signup/page.tsx` | Signup sectors may not match search. | 4h |
| FE-07 | **No dynamic imports for heavy dependencies** (recharts ~200KB, @dnd-kit, framer-motion, shepherd.js). All static imports. | Dashboard, Pipeline, Landing, Search | Larger initial JS bundle; degrades LCP/TTI. | 8h |
| FE-08 | **Error boundary button uses `--brand-green` not defined in design tokens.** | `app/error.tsx` | Button may be invisible in production. | 1h |
| FE-09 | **No tests for SearchResults.tsx (678 lines)** -- core results display completely untested. | `buscar/components/SearchResults.tsx` | No regression safety for most visible UI. | 16h |
| FE-10 | **No tests for pipeline drag-and-drop.** | `app/pipeline/page.tsx` | Complex interaction untested. | 8h |
| FE-11 | **No tests for onboarding wizard flow.** | `app/onboarding/page.tsx` | Multi-step form untested. | 8h |
| FE-12 | **No tests for middleware.ts route protection logic.** | `frontend/middleware.ts` | Auth guard logic untested. | 8h |

### 3.4 Accessibility (MEDIUM)

| ID | Descricao | Localizacao | Impacto | Esforco Est. |
|----|-----------|-------------|---------|--------------|
| A11Y-03 | **Custom dropdowns (CustomSelect) may not announce selection changes** to screen readers. | `app/components/CustomSelect.tsx` | AT users miss selection feedback. | 4h |
| A11Y-04 | **Pull-to-refresh has no keyboard alternative** (mobile-only swipe gesture). | `/buscar` PullToRefresh wrapper | Mobile keyboard/switch users cannot refresh. | 4h |
| A11Y-05 | **Shepherd.js onboarding may block content without `inert` attribute** on background. | `/buscar` onboarding tour | During tour, background is interactive. | 4h |

### 3.5 UX Issues (MEDIUM)

| ID | Descricao | Localizacao | Impacto | Esforco Est. |
|----|-----------|-------------|---------|--------------|
| UX-01 | **Search button below the fold** on desktop with "Personalizar busca" accordion open. Users must scroll to find CTA. | `/buscar` SearchForm | Primary CTA not visible. | 4h |
| UX-02 | **Keyboard shortcuts modal lacks focus trap; Escape triggers limparSelecao instead of modal dismiss.** | `/buscar` keyboard help | Escape key conflict confuses users. | 4h |
| UX-03 | **Pricing page annual calculation shows "9.6x" multiplier** -- confusing. Should display "20% desconto". | `/planos` pricing cards | Users confused by 9.6x math. | 4h |
| UX-04 | **Pipeline page not optimized for mobile** -- drag-and-drop difficult on small screens. | `/pipeline` | Mobile users cannot effectively use Kanban. | 16h |
| UX-05 | **Admin page table not responsive** -- horizontal scrolling required on mobile. | `/admin` | Mobile admin degraded experience. | 8h |

### 3.6 Technical Debt (LOW)

| ID | Descricao | Localizacao | Impacto | Esforco Est. |
|----|-----------|-------------|---------|--------------|
| FE-13 | **Auth guard duplicated** between middleware.ts and `(protected)/layout.tsx`. | `middleware.ts`, `app/(protected)/layout.tsx` | Double redirect logic, potential race. | 4h |
| FE-14 | **Console.log statements in AuthProvider** -- Google OAuth debug logging in production. | `app/components/AuthProvider.tsx` lines 254-258 | Leaks implementation details. | 1h |
| FE-15 | **`useEffect` missing dependencies** -- multiple `eslint-disable-next-line` comments. | Multiple hooks and components | Potential stale closure bugs. | 8h |
| FE-16 | **Search state uses `window.location.href`** instead of Next.js `router.push`. | Search-related code | Full page reload instead of client nav. | 2h |
| FE-17 | **PLAN_HIERARCHY and PLAN_FEATURES hardcoded** in planos/page.tsx. Duplicate of `lib/plans.ts`. | `app/planos/page.tsx`, `lib/plans.ts` | Multiple sources of truth. | 4h |
| FE-18 | **`next.config.js` uses CommonJS** while rest is ESM/TypeScript. | `frontend/next.config.js` | Codebase inconsistency. | 2h |
| FE-19 | **Pull-to-refresh CSS hack** disables pointer-events then re-enables on children. Fragile. | `/buscar` CSS | Could break with layout changes. | 4h |
| FE-20 | **CSS class `sr-only` hardcoded inline** in layout.tsx skip-nav. | `frontend/app/layout.tsx` line 96 | Should use Tailwind utility. | 1h |
| FE-21 | **`dangerouslySetInnerHTML` for theme script** -- legitimate but needs safety comment. | `frontend/app/layout.tsx` lines 73-89 | Already necessary for FOUC prevention. | 1h |

### 3.7 UX Inconsistencies (LOW)

| ID | Descricao | Localizacao | Impacto | Esforco Est. |
|----|-----------|-------------|---------|--------------|
| IC-01 | **Hardcoded "SmartLic" in header** despite `APP_NAME` env var. | `buscar/page.tsx` line 123 | Brand not centralized. | 1h |
| IC-02 | **Mixed color approaches** -- Tailwind tokens vs inline CSS vars inconsistently. | Multiple files | Visual ok, codebase inconsistent. | 4h |
| IC-03 | **Icon sources mixed** -- lucide-react vs inline SVGs. | Multiple components | No consistent icon system. | 4h |
| IC-04 | **Loading spinner styles vary** across components. | Multiple components | Visual inconsistency. | 4h |
| IC-05 | **Link vs anchor tag mixed** for internal navigation. | Multiple pages | Inconsistent client-side nav. | 2h |
| IC-06 | **Error message translation only in login page** -- backend errors shown raw elsewhere. | Login vs other pages | Poor non-login error UX. | 8h |
| IC-07 | **Max-width container varies** (4xl, 5xl, 7xl, landing) with no documented rationale. | Multiple layouts | Inconsistent page widths. | 4h |

### 3.8 Missing UX Feedback (LOW)

| ID | Descricao | Localizacao | Impacto | Esforco Est. |
|----|-----------|-------------|---------|--------------|
| MF-01 | **No unsaved changes confirmation** when leaving mid-search with results. | `/buscar` navigation | Users accidentally lose results. | 4h |
| MF-02 | **No "Copied to clipboard" feedback.** | `LicitacaoCard` copy actions | Users don't know if copy succeeded. | 2h |
| MF-03 | **Pipeline drag-and-drop no haptic/audio feedback on mobile.** | `/pipeline` | Touch users may not feel drag start. | 4h |
| MF-04 | **Sector change doesn't confirm results were cleared.** | `/buscar` sector selector | Users may not notice. | 2h |

### 3.9 Accessibility (LOW)

| ID | Descricao | Localizacao | Impacto | Esforco Est. |
|----|-----------|-------------|---------|--------------|
| A11Y-06 | **UF buttons use `title` but no `aria-label`** for full state name. | `RegionSelector.tsx` | Most AT reads title, but inconsistent. | 2h |
| A11Y-07 | **Keyboard shortcuts no way to disable/customize.** | `/buscar` shortcuts | Conflict risk with browser/OS. | 4h |
| A11Y-08 | **Some SVG icons use generic `aria-label="Icone"`.** | Multiple components | No useful info for AT users. | 2h |
| A11Y-09 | **Dark mode `--ink-muted` at 4.9:1** -- borderline AA (4.5:1 required). | `globals.css` dark mode | Very close; technically passes. | 1h |

**Subtotal Frontend/UX:** 45 debitos | Esforco estimado: ~218h

---

## 4. Matriz Preliminar de Priorizacao

### Legenda

- **Impacto:** SAFETY (security/data breach), FUNCTIONAL (feature broken), QUALITY (degraded experience), MAINTENANCE (developer burden)
- **[QW]**: Quick Win -- 4h or less
- **Prioridade:** P0 (imediato), P1 (este sprint), P2 (proximo sprint), P3 (backlog)

### P0 -- Corrigir Imediatamente (~19h, 6 items)

| # | ID | Debito | Area | Impacto | Esforco |
|---|-----|--------|------|---------|---------|
| 1 | DB-02 | `handle_new_user()` trigger + column default `'free'` viola CHECK | DB | FUNCTIONAL | 2h [QW] |
| 2 | DB-01 | Missing `status` column on `user_subscriptions` (verify production first) | DB | FUNCTIONAL | 4h [QW] |
| 3 | DB-03 | `pipeline_items` RLS overly permissive -- cross-user access | DB | SAFETY | 2h [QW] |
| 4 | DB-04 | `search_results_cache` RLS overly permissive -- cross-user access | DB | SAFETY | 2h [QW] |
| 5 | DB-06 | `_ensure_profile_exists()` uses `plan_type: "free"` violating CHECK | Backend | FUNCTIONAL | 1h [QW] |
| 6 | SYS-03 | LLM Arbiter hardcoded sector -- wrong classification for 14/15 sectors | Backend | FUNCTIONAL | 8h |

### P1 -- Corrigir Este Sprint (~41h, 8 items)

| # | ID | Debito | Area | Impacto | Esforco |
|---|-----|--------|------|---------|---------|
| 7 | SYS-07 | `time.sleep(0.3)` blocking async event loop | Backend | QUALITY | 2h [QW] |
| 8 | DB-05 | `stripe_webhook_events` INSERT policy not scoped to service_role | DB | SAFETY | 2h [QW] |
| 9 | SYS-10 | No backend linting in CI (ruff/mypy) | CI/CD | QUALITY | 4h [QW] |
| 10 | A11Y-01 | Modal dialogs lack focus trap | Frontend | QUALITY | 4h [QW] |
| 11 | A11Y-02 | Modals missing `role="dialog"` / `aria-modal` | Frontend | QUALITY | 4h [QW] |
| 12 | SYS-02 | Dual HTTP client implementations (consolidate) | Backend | MAINTENANCE | 16h |
| 13 | SYS-04 | In-memory progress tracker not scalable | Backend | FUNCTIONAL | 8h |
| 14 | FE-08 | Error boundary `--brand-green` undefined in tokens | Frontend | FUNCTIONAL | 1h [QW] |

### P2 -- Proximo Sprint (~152h, 11 items)

| # | ID | Debito | Area | Impacto | Esforco |
|---|-----|--------|------|---------|---------|
| 15 | SYS-01 | Frontend test coverage below 60% threshold | Frontend | QUALITY | 40h |
| 16 | FE-04 | 17 quarantined test files | Frontend | QUALITY | 24h |
| 17 | FE-01 | SearchForm ~40 props drilling | Frontend | MAINTENANCE | 16h |
| 18 | FE-02 | SearchResults ~35 props drilling | Frontend | MAINTENANCE | 16h |
| 19 | FE-03 | `useSearchFilters` 528 lines / 40+ states | Frontend | MAINTENANCE | 16h |
| 20 | DB-07 | FK inconsistency (auth.users vs profiles) for new tables | DB | MAINTENANCE | 4h [QW] |
| 21 | DB-09 | Analytics time-series full row fetch | DB | QUALITY | 8h |
| 22 | SYS-08 | Excel tmpdir fallback not cleaned | Frontend | QUALITY | 4h [QW] |
| 23 | SYS-09 | Dual route mounting (root + /v1/) -- sunset 2026-06-01 | Backend | MAINTENANCE | 4h [QW] |
| 24 | FE-07 | No dynamic imports for heavy deps | Frontend | QUALITY | 8h |
| 25 | FE-09 | No tests for SearchResults.tsx (678 lines) | Frontend | QUALITY | 16h |

### P3 -- Backlog (~200h+, remaining items)

All MEDIUM items not listed in P0-P2, plus all LOW items. See individual sections for details.

Key backlog clusters:
- Backend quality: SYS-05, SYS-06, SYS-11 through SYS-18
- Database optimization: DB-08, DB-10, DB-11
- Frontend architecture: FE-05, FE-06, FE-10 through FE-21
- UX improvements: UX-01 through UX-05, IC-01 through IC-07
- Accessibility polish: A11Y-03 through A11Y-09
- Missing feedback: MF-01 through MF-04

### Resumo de Esforco

| Prioridade | Items | Esforco Total |
|------------|-------|---------------|
| P0 | 6 | ~19h |
| P1 | 8 | ~41h |
| P2 | 11 | ~152h |
| P3 | 57+ | ~200h+ |
| **Total** | **82** | **~412h+** |

---

## 5. Dependencias Entre Debitos

### Grafo de Dependencias

```
DB-02 (handle_new_user default) ---blocks---> DB-11 (trigger consolidation)
                                                     |
                                                     +---> SYS-06 (legacy plan cleanup)

DB-01 (missing status column) ---blocks---> DB-11 (trigger consolidation)
                                                     |
                                                     +---> plan_type sync verification

DB-03 (pipeline RLS) ---independent, same migration---> DB-04 (cache RLS)
  |                                                        |
  +---can combine with--> DB-05 (webhook INSERT RLS) ------+
  |
  +---should combine with--> DB-07 (FK standardization)

SYS-01 (test coverage) <---depends-on--- FE-04 (quarantined tests)
  |
  +---depends-on---> FE-09 (SearchResults tests)
  +---depends-on---> FE-10 (pipeline tests)
  +---depends-on---> FE-11 (onboarding tests)
  +---depends-on---> FE-12 (middleware tests)

FE-01 (SearchForm props) ---co-refactor---> FE-02 (SearchResults props)
  |                                           |
  +---depends-on---> FE-03 (useSearchFilters split)

SYS-02 (dual HTTP client) ---enables---> SYS-04 (progress tracker scalability)
                                                   |
                                                   +---enables---> SYS-05 (auth cache sharing)

SYS-09 (dual route mounting) ---deadline---> 2026-06-01 (sunset date)

A11Y-01 (focus trap) ---co-implementation---> A11Y-02 (role="dialog")
  |
  +---can use same library---> (@radix-ui/react-dialog)
```

### Clusters de Trabalho Sugeridos

**Cluster A: Database Security Sprint (P0, ~13h, single migration)**
Items: DB-02 + DB-03 + DB-04 + DB-05 + DB-06 + DB-07
- Create migration 027 addressing all RLS + FK + trigger + default fixes
- Pre-condition: Verify DB-01 (status column) in production first
- Backend code fix: Change `plan_type: "free"` to `"free_trial"` in `quota.py`

**Cluster B: Backend Correctness Quick Wins (P0-P1, ~12h)**
Items: SYS-03 + SYS-07 + SYS-14 + SYS-18
- LLM Arbiter sector parameterization
- async sleep fix
- User-Agent rename
- Timezone-aware datetime
- Independent, no inter-dependencies

**Cluster C: CI/Quality Gates (P1, ~8h)**
Items: SYS-10 + FE-08
- Add ruff/mypy to CI workflow
- Fix error boundary token

**Cluster D: Accessibility Sprint (P1, ~8h)**
Items: A11Y-01 + A11Y-02
- Install `@radix-ui/react-dialog` or implement focus trap utility
- Both items share same root cause (missing modal infrastructure)

**Cluster E: PNCP Client Consolidation (P1, ~18h)**
Items: SYS-02 + SYS-20 + SYS-21
- Remove sync `PNCPClient`, keep only `AsyncPNCPClient`
- Fix deprecated patterns
- Reduces pncp_client.py from ~1585 to ~800 lines

**Cluster F: Frontend Architecture Refactor (P2, ~64h)**
Items: FE-01 + FE-02 + FE-03
- Extract search state into React Context or add lightweight state library
- Split `useSearchFilters` into `useUfSelection`, `useDateRange`, `useTermSearch`, `useAdvancedFilters`
- Coordinated refactor -- all three items share same codebase area

**Cluster G: Test Coverage Campaign (P2, ~80h)**
Items: SYS-01 + FE-04 + FE-09 + FE-10 + FE-11 + FE-12
- Phase 1: Unquarantine AuthProvider and useSearch tests (highest value)
- Phase 2: Add SearchResults.tsx tests (most visible component)
- Phase 3: Pipeline and onboarding tests
- Phase 4: Middleware tests
- Target: reach 60% to unblock CI

---

## 6. Perguntas para Especialistas

### Para @data-engineer (Datum):

1. **DB-01 (CRITICAL):** O campo `status` existe na tabela `user_subscriptions` em producao? Executar:
   ```sql
   SELECT column_name, data_type FROM information_schema.columns
   WHERE table_name = 'user_subscriptions' AND column_name = 'status';
   ```
   Se ausente, o trigger `sync_profile_plan_type()` da migration 017 e dead code. Se existente, como foi criado (manualmente via SQL editor)?

2. **DB-02 (CRITICAL):** Verificar o default da coluna `profiles.plan_type` em producao:
   ```sql
   SELECT column_default FROM information_schema.columns
   WHERE table_name = 'profiles' AND column_name = 'plan_type';
   ```
   Se retornar `'free'`, novos signups estao falhando. Se retornar `'free_trial'`, foi corrigido manualmente.

3. **DB-10:** Qual o tamanho atual da tabela `search_results_cache`?
   ```sql
   SELECT pg_size_pretty(pg_total_relation_size('search_results_cache'));
   ```
   Recomenda compressao de JSONB, truncamento, ou o max-5-per-user e suficiente?

4. **DB-09:** Numero medio de `search_sessions` por usuario ativo? Isso determina se o RPC server-side e urgente ou pode ir para backlog.

5. **DB-08:** Estrategia recomendada para Stripe price IDs em staging/dev -- seed condicional, env vars, ou manual update?

6. **Migrations squash:** Com 26 migrations, faz sentido criar um squash para simplificar? Ou o historico completo tem valor documental?

7. **pg_cron:** Os jobs de cleanup (022, 023) estao funcionando? A extensao pg_cron esta habilitada no Supabase?

### Para @ux-expert (Pixel):

1. **A11Y-01/A11Y-02:** Recomenda adotar `@radix-ui/react-dialog` como padrao para modais? Ou componente `<Modal>` custom com focus trap?

2. **FE-01/FE-02/FE-03:** Para o refactor de prop drilling, qual pattern preferido: React Context + Provider, compound components, ou Zustand? Considerando que nao ha state management library atualmente.

3. **UX-04:** O pipeline kanban em mobile -- converter para lista ordenavel (sortable list) em telas <768px? Ou manter DnD com adaptacoes touch?

4. **IC-06:** Existe plano para i18n? Se sim, investir em traduzir mensagens de erro agora ou esperar framework de i18n?

5. **FE-07:** Quais componentes priorizar para `next/dynamic`? Recharts (~200KB) e @dnd-kit parecem os maiores candidatos.

6. **UX-03:** A formula "9.6x" na pagina de pricing -- como apresentar o desconto anual de forma mais clara? "20% off" vs "2 meses gratis"?

7. **FE-05:** Para consolidacao de icones, lucide-react ja esta instalado. Faz sentido migrar todos inline SVGs para lucide-react, ou criar icon component wrapper?

### Para @qa:

1. **SYS-01/FE-04:** Estrategia para atingir 60% -- priorizar unquarantine dos existentes ou escrever novos para componentes sem cobertura?

2. **FE-09:** SearchResults.tsx (678 linhas, zero testes) -- abordagem: testes unitarios com mocks pesados, ou priorizar E2E via Playwright?

3. **SYS-16:** Integration tests placeholder -- quais cenarios primeiro? Sugestao: search pipeline E2E (mock PNCP), Stripe webhook handler, auth flow.

4. **SYS-10:** Configuracao de `ruff` e `mypy` para CI -- strict ou permissive para comecar? Qual subset de rules?

5. **Risk map:** Com 100+ test files backend (96.69%) e ~90 frontend (49.46%), qual area de maior risco nao coberta? Pipeline CRUD? Stripe checkout? Search error paths?

6. **Quarantine audit:** Dos 17 quarantined test files, quais estao broken por mudancas de API e quais sao genuinamente flaky? Priorizar os broken-by-API (fixes rapidas) vs flaky (requerem infra).

---

## Apendice A: Itens Deduplicados

Os seguintes itens apareciam em multiplos documentos e foram consolidados:

| Item nos Documentos Fonte | ID Consolidado | Notas |
|---------------------------|----------------|-------|
| system-arch TD-C01 + frontend-spec TD-04 (test coverage/quarantine) | SYS-01 + FE-04 | Split: SYS-01 = coverage gap, FE-04 = quarantine specifically |
| system-arch TD-H02 + DB-AUDIT TD-11 (deprecated migration) | SYS-23 / DB-12 | Cross-reference kept; same item |
| system-arch TD-L04 (sr-only inline CSS) | FE-20 | Moved to frontend debt |
| system-arch TD-L05 (format_resumo_html unused) | SYS-22 | Kept in system debt |
| system-arch TD-L06 (dangerouslySetInnerHTML) | FE-21 | Moved to frontend debt |
| DB-AUDIT SEC-01 + SCHEMA pipeline_items RLS note | DB-03 | Audit provides more detail |
| DB-AUDIT SEC-02 + SCHEMA search_results_cache RLS note | DB-04 | Audit provides more detail |
| DB-AUDIT INTEGRITY-04 (quota.py free) + system usage | DB-06 | Backend code + DB constraint |
| frontend-spec A-10 + TD-08 (brand-green error boundary) | FE-08 | Accessibility + visual issue = same root cause |
| frontend-spec UX-03 (save dialog focus trap) = A-01 | A11Y-01 | Same underlying issue |
| frontend-spec IC-03 (mixed icons) ~ TD-05 (inline SVGs) | FE-05 + IC-03 | Related but distinct (duplication vs inconsistency) |
| system-arch TD-H06 (Excel tmpdir) = frontend-spec observation | SYS-08 | Kept in system debt (cross-cutting) |

## Apendice B: Observacoes Positivas (Preservar)

These quality aspects were highlighted by specialists and must be preserved during debt resolution:

**Backend/Architecture:**
1. Route decomposition (STORY-202) into 14 route modules
2. 7-stage search pipeline with independent error handling per stage
3. Circuit breaker with degraded mode (8 failures / 120s cooldown)
4. Parallel UF fetching with asyncio.Semaphore concurrency control
5. Health canary probe before full search
6. Auto-retry failed UFs with 5s delay
7. Fail-fast sequential filtering (cheapest filters first)
8. LLM Arbiter pattern (auto-accept/reject + LLM for ambiguous)
9. Multi-layer subscription fallback (4 camadas, "fail to last known plan")
10. PII masking in logs (log_sanitizer.py) + Sentry scrubbing
11. Stripe webhook idempotency via `stripe_webhook_events` table
12. Correlation ID middleware for distributed tracing
13. RFC 8594 deprecation headers on legacy routes
14. Structured JSON logging with python-json-logger

**Database:**
15. Atomic quota functions with `SELECT ... FOR UPDATE` (race condition prevention)
16. 100% RLS coverage across all 14 tables
17. Systematic migration-driven schema evolution (26 documented migrations)
18. Partial indexes for common query patterns
19. GIN trigram index for admin email search
20. pg_cron retention automation (3 staggered jobs)
21. Privacy-first audit logging with SHA-256 hashed PII
22. Search cache self-limitation trigger (max 5 per user)
23. RPC functions eliminating N+1 queries (conversations, analytics)

**Frontend:**
24. Complete design system with CSS custom properties and documented WCAG ratios
25. Dark/light mode with FOUC prevention (inline script)
26. Skip navigation link (WCAG 2.4.1) and focus-visible (WCAG 2.2 AAA)
27. `prefers-reduced-motion` respected globally
28. SSE real-time progress with per-UF status grid
29. Keyboard shortcuts (Ctrl+K, Ctrl+A, Escape)
30. Client-side search retry (2 retries with 3s/8s delays)
31. LGPD compliance: Cookie consent banner, data export, account deletion
32. Search state persistence for auth recovery
33. Resilience UX components (CacheBanner, DegradationBanner, PartialResultsPrompt)
34. 14 E2E Playwright specs covering critical user flows

---

*Documento consolidado por @architect (Helix) em 2026-02-15.*
*Brownfield Discovery Phase 4 -- Consolidation of Phases 1, 2, 3.*
*Commit de referencia: `b80e64a` (branch `main`).*
*Proximo passo: Revisao pelos especialistas, depois promocao a versao final em `docs/prd/technical-debt-assessment.md`.*
