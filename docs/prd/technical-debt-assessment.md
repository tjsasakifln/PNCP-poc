# Technical Debt Assessment - FINAL

## SmartLic/BidIQ - Brownfield Discovery

**Status:** FINAL
**Date:** 2026-02-11
**Version:** 1.0
**Commit:** `808cd05` (branch `main`)
**Approved by:** @architect (Aria), @data-engineer (Dara), @ux-design-expert (Uma), @qa

**Sources:**
1. `docs/architecture/system-architecture.md` -- @architect
2. `supabase/docs/SCHEMA.md` -- @data-engineer
3. `supabase/docs/DB-AUDIT.md` -- @data-engineer
4. `docs/frontend/frontend-spec.md` -- @ux-design-expert
5. `docs/reviews/db-specialist-review.md` -- @data-engineer review
6. `docs/reviews/ux-specialist-review.md` -- @ux-design-expert review
7. `docs/reviews/qa-review.md` -- @qa review

---

### 1. Executive Summary

SmartLic/BidIQ is a production SaaS (POC v0.3) for automated procurement opportunity discovery from Brazil's PNCP. The system is functional with real users and live Stripe billing, but carries significant technical debt accumulated during rapid feature growth.

**Overall Health Assessment:**
- **Backend/Architecture:** MEDIUM (functional, scalability risks)
- **Database:** 6.5/10 (functional for POC, security and consistency gaps; competing Stripe handler implementations are an active correctness risk)
- **Frontend/UX:** MEDIUM-HIGH (feature-rich, but monolithic pages, accessibility gaps, and price divergence undermine user trust)
- **Testing:** MEDIUM-LOW (CI gates non-functional, testing strategy undocumented)

**Final Debt Count:**

| Severity | System | Database | Frontend | Cross-Cutting | Testing | Total |
|----------|--------|----------|----------|---------------|---------|-------|
| CRITICAL | 4 | 4 | 3 | 2 | 0 | **13** |
| HIGH | 5 | 4 | 8 | 1 | 1 | **19** |
| MEDIUM | 8 | 10 | 11 | 2 | 4 | **35** |
| LOW | 6 | 6 | 11 | 0 | 0 | **23** |
| **Total** | **23** | **24** | **33** | **5** | **5** | **90** |

**Total Estimated Effort:** 320-456 hours (4 sprints)

---

### 2. System/Architecture Debts (23 items)

Source: `docs/architecture/system-architecture.md` -- @architect (Aria)

No severity changes from specialist reviews for system debts.

#### 2.1 CRITICAL (4)

| ID | Debt | Description | File(s) | Effort Est. |
|----|------|-------------|---------|-------------|
| SYS-C01 | In-memory state blocks horizontal scaling | `_active_trackers` dict in `progress.py:98` stores SSE state in memory. If more than 1 instance is deployed, search progress breaks. State lost on restart. | `backend/progress.py:98` | 16-24h (requires Redis pub/sub) |
| SYS-C02 | Monolith main.py (1,959 lines) | Contains 20+ endpoints, business logic, helper functions, billing handlers. Difficult to maintain and test in isolation. | `backend/main.py` | 12-16h |
| SYS-C03 | Dual ORM/DB access pattern | Two DB access mechanisms coexist: Supabase Python Client (95% of code) and SQLAlchemy (Stripe webhooks). Schema drift risk. | `backend/supabase_client.py`, `backend/database.py` | 8-12h |
| SYS-C04 | Pre-existing test failures | Backend: 21 failures; Frontend: 70 failures. CI pipeline fails, masking new regressions. Quality gate non-functional. | Backend tests, Frontend tests | 8-16h |

#### 2.2 HIGH (5)

| ID | Debt | Description | File(s) | Effort Est. |
|----|------|-------------|---------|-------------|
| SYS-H01 | Synchronous PNCP client in async context | `PNCPClient` uses `requests` (blocking) as fallback. Blocks event loop when used. Only `AsyncPNCPClient` is non-blocking. | `backend/pncp_client.py:67-557` | 4-6h |
| SYS-H02 | Excel stored in temporary filesystem | Temp files not shared between instances. TTL of 60 min via `setTimeout` is unreliable. Files survive restarts. | `frontend/app/api/buscar/route.ts:180-204` | 6-8h |
| SYS-H03 | No tracked database migrations in repo | No standard `migrations/` directory found. Schema changes depend on manual Supabase dashboard operations. | N/A | 4-6h |
| SYS-H04 | Business logic in main.py helper functions | Core authorization logic (`_check_user_roles`, `_is_admin`, `_has_master_access`) co-located with route handlers. Cannot be unit tested. | `backend/main.py:392-523` | 4-6h |
| SYS-H05 | Development dependencies in production requirements | pytest, ruff, mypy, locust, faker installed in production. Increases attack surface and image size. | `backend/requirements.txt:37-50` | 2-3h |

#### 2.3 MEDIUM (8)

| ID | Debt | Description | File(s) | Effort Est. |
|----|------|-------------|---------|-------------|
| SYS-M01 | No request ID / correlation ID | Impossible to trace a request across log entries or between frontend proxy and backend. Hard to debug in production. | All backend | 3-4h |
| SYS-M02 | Token cache uses `hash()` of token prefix | Python's `hash()` is not cryptographically secure and varies between executions. Potential for collisions in long-running instances. | `backend/auth.py:45` | 2-3h |
| SYS-M03 | In-memory rate limiter without max size | Memory grows without limit with unique user IDs in the in-memory fallback. Garbage collection only removes entries > 60s. | `backend/rate_limiter.py:84-89` | 2-3h |
| SYS-M04 | Hardcoded plan capabilities | Plan definitions are in Python code, not in the database. Adding a new plan requires code deployment. | `backend/quota.py:62-95` | 4-6h |
| SYS-M05 | Google API credentials handling | Google Sheets integration adds 4 heavy dependencies. OAuth token storage mechanism not visible. | `backend/requirements.txt:29-33` | 2-3h |
| SYS-M06 | `datetime.utcnow()` deprecated | Python 3.12 deprecates `datetime.utcnow()`. Should use `datetime.now(timezone.utc)` consistently. | Multiple files | 2-3h |
| SYS-M07 | Frontend coverage below threshold | 49.46% vs target of 60%. CI coverage gate fails. Gap mainly in LoadingProgress, RegionSelector, SavedSearchesDropdown, AnalyticsProvider. | `frontend/` | 8-12h |
| SYS-M08 | No API versioning | All endpoints unversioned. Breaking changes require coordinated frontend/backend deploy. | `backend/main.py` | 4-6h |

#### 2.4 LOW (6)

| ID | Debt | Description | File(s) | Effort Est. |
|----|------|-------------|---------|-------------|
| SYS-L01 | No OpenAPI schema validation in tests | API contract drift between backend and frontend can go undetected. | Backend tests | 4-6h |
| SYS-L02 | Emoji usage in production logs | Log aggregators may not render emojis correctly. | `backend/pncp_client.py:525,533` | 1h |
| SYS-L03 | Inline CSS in layout.tsx | Theme initialization script uses inline styles. Should use CSS variables exclusively. | `frontend/app/layout.tsx:62-77` | 1-2h |
| SYS-L04 | No request/response logging middleware | No centralized request logging (duration, status code, path). Each endpoint logs individually. | Backend | 3-4h |
| SYS-L05 | Unused imports in main.py | `from filter import match_keywords, KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO` imported inside diagnostic loop. | `backend/main.py:1694` | 0.5h |
| SYS-L06 | No health check for Redis | Health endpoint checks Supabase and OpenAI but not Redis. Rate limiting degrades silently. | `backend/main.py:162-229` | 2h |

**Subtotal System:** 23 debts | Effort: ~105-155h

---

### 3. Database Debts (24 items)

Source: `supabase/docs/SCHEMA.md`, `supabase/docs/DB-AUDIT.md` -- @data-engineer (Dara)
Reviewed and validated by: @data-engineer (see `docs/reviews/db-specialist-review.md`)

#### 3.1 CRITICAL (4)

| ID | Debt | Description | File(s) | Effort Est. |
|----|------|-------------|---------|-------------|
| DB-C01 | `database.py` derives PostgreSQL URL incorrectly from `SUPABASE_URL` | The SQLAlchemy engine builds URL by replacing `https://` in `SUPABASE_URL`, producing `postgresql://fqqyovlzdzimiwfofdjk.supabase.co` -- missing port, database name, and credentials. Connection almost certainly fails silently. Stripe webhook processing via SQLAlchemy path is non-functional. | `backend/database.py:33` | 2-4h |
| DB-C03 | `stripe_webhook_events` admin check uses `plan_type = 'master'` instead of `is_admin` | Policy SELECT checks `profiles.plan_type = 'master'` but canonical admin flag is `profiles.is_admin`. These are independent columns. Admin with `plan_type != 'master'` cannot view webhook events. Non-admin master user CAN view them. Direct access control bug. | `supabase/migrations/010_stripe_webhook_events.sql:61-68` | 0.5h |
| DB-H01 | Dual ORM Architecture (Supabase Client + SQLAlchemy) | **Upgraded from HIGH by @data-engineer.** Two complete implementations of Stripe subscription lifecycle handlers exist: `main.py:733-829` (Supabase client) and `webhooks/stripe.py:104-144` (SQLAlchemy). Two competing implementations for the same business logic with different access mechanisms. Active correctness risk, not just architectural debt. | `backend/supabase_client.py`, `backend/database.py`, `backend/models/`, `backend/webhooks/stripe.py` | 10-14h |
| NEW-DB-01 | Competing Stripe webhook handler implementations | **NEW from @data-engineer.** `main.py` contains `_activate_plan()`, `_deactivate_stripe_subscription()`, `_handle_subscription_updated()` using Supabase client. `webhooks/stripe.py` contains `handle_subscription_updated()`, `handle_subscription_deleted()`, `handle_invoice_payment_succeeded()` using SQLAlchemy. The SQLAlchemy handlers do NOT sync `profiles.plan_type` while the main.py handlers DO. Behavior depends on which code path handles the event, leading to unpredictable plan_type drift. **Most dangerous database-related debt.** | `backend/main.py:733-900`, `backend/webhooks/stripe.py:104-144` | Included in DB-H01 (6-8h) |

#### 3.2 HIGH (4)

| ID | Debt | Description | File(s) | Effort Est. |
|----|------|-------------|---------|-------------|
| DB-C02 | `user_subscriptions` missing service role RLS policy for writes | **Downgraded from CRITICAL by @data-engineer.** Backend uses `SUPABASE_SERVICE_ROLE_KEY` which bypasses RLS by design. Risk is future-proofing, not present breakage. Inconsistent with `monthly_quota` and `search_sessions` patterns. | `supabase/migrations/001_profiles_and_sessions.sql:119-121` | 1h |
| DB-H02 | Migration 006 duplicated (3 files) | Three files with `006_` prefix. `006_APPLY_ME.sql` and `006_search_sessions_service_role_policy.sql` are byte-for-byte identical in SQL effect. `006_update_profiles_plan_type_constraint.sql` is a different migration. Operational confusion risk. | `supabase/migrations/006_*` | 1-2h |
| DB-H03 | Missing index on `user_subscriptions.stripe_subscription_id` | Migration 001 defines `stripe_subscription_id text` with NO unique constraint. SQLAlchemy model defines `unique=True` but `Base.metadata.create_all()` was never called (engine URL is invalid). `main.py` queries this column at lines 785, 795, 822, 886. Without index, these are sequential scans. | `backend/webhooks/stripe.py:187-189`, `backend/main.py:795` | 0.5h |
| DB-H04 | RLS policies overly permissive (`USING (true)` without `TO service_role`) | `monthly_quota` (migration 002) and `search_sessions` (migration 006) have `FOR ALL USING (true)` without `TO service_role`. Compare with migrations 013/014 which correctly use `TO service_role`. Allows any authenticated user to perform any operation via PostgREST. Defense-in-depth failure. | Migrations 002, 006 | 1h |

#### 3.3 MEDIUM (10)

| ID | Debt | Description | File(s) | Effort Est. |
|----|------|-------------|---------|-------------|
| DB-H05 | `profiles` missing INSERT policy for auth trigger | **Downgraded from HIGH by @data-engineer.** `handle_new_user()` trigger runs as `SECURITY DEFINER` (bypasses RLS). `_ensure_profile_exists()` uses service_role key (also bypasses). No code path where a regular user attempts INSERT into profiles. Good hygiene but not a security gap. | `supabase/migrations/001_profiles_and_sessions.sql:110-113` | 0.5h |
| DB-M01 | Inconsistent Foreign Keys (auth.users vs profiles) | `monthly_quota`, `user_oauth_tokens`, `google_sheets_exports` reference `auth.users(id)` directly; others reference `profiles(id)`. Functionally equivalent due to cascading FK, but inconsistent maintenance pattern. | Migrations 002, 013, 014 | 3-4h |
| DB-M02 | CHECK constraint `plan_type` includes legacy values | Constraint allows 10 values including legacy `free`, `avulso`, `pack`, `monthly`, `annual`. The `handle_new_user()` trigger sets `plan_type = 'free'` (a legacy value!) by default. Every new user starts with an inconsistent legacy plan_type. | `supabase/migrations/006_update_profiles_plan_type_constraint.sql` | 1-2h |
| DB-M03 | `updated_at` column missing in migration for `user_subscriptions` | Migration 001 does NOT define `updated_at`. Migration 008 does NOT add it. SQLAlchemy model defines it. Likely added manually via dashboard. Documentation/migration gap. | `001_profiles_and_sessions.sql`, `backend/models/user_subscription.py:83` | 1h |
| DB-M04 | `profiles.plan_type` and `user_subscriptions.plan_id` can drift | Two sources of truth for user plan. The 4-layer fallback in `quota.py:413-504` handles drift for reads, but `webhooks/stripe.py:handle_subscription_updated()` does NOT sync `profiles.plan_type`. Subscription updates via SQLAlchemy create drift. | `backend/quota.py:413-504` | 4-6h |
| DB-M05 | Stripe price IDs hardcoded in migration 015 | Migration contains 6 production Stripe price IDs. If applied to staging/dev, configures production price IDs that would charge real money or fail API calls. | `supabase/migrations/015_add_stripe_price_ids_monthly_annual.sql` | 2h |
| DB-M06 | N+1 query in conversation list endpoint | For each conversation, a separate Supabase call counts unread messages. With 50 conversations, produces 51 queries. ~200ms-1.5s added latency. | `backend/routes/messages.py:112-122` | 2-3h |
| DB-M07 | Analytics endpoints fetch ALL sessions | `get_analytics_summary()` fetches ALL search sessions for a user with no pagination or date limit. All aggregation done in Python. Power users with 1000+ sessions transfer significant data. | `backend/routes/analytics.py:78-83` | 2-3h |
| NEW-DB-02 | `handle_new_user()` trigger sets `plan_type = 'free'` (legacy value) | **NEW from @data-engineer.** The trigger creates profiles with `plan_type = 'free'` (column default), but `'free'` is a legacy value -- current equivalent is `'free_trial'`. `PLAN_TYPE_MAP` in `quota.py:386-392` maps `free` -> `free_trial` at runtime, but every new user starts with an inconsistent legacy value. | `supabase/migrations/001_profiles_and_sessions.sql`, `supabase/migrations/007_add_whatsapp_consent.sql` | 0.5h |
| NEW-DB-03 | Missing index on `profiles.email` for admin ILIKE search | **NEW from @data-engineer.** Admin panel searches users by email using `email.ilike.%search%`. Without a trigram index, this performs a sequential scan on the profiles table. Noticeable slowdown at 5,000+ users. | `backend/admin.py:268-269` | 1h |

#### 3.4 LOW (6)

| ID | Debt | Description | File(s) | Effort Est. |
|----|------|-------------|---------|-------------|
| DB-L01 | `plans` table missing `updated_at` column | No audit trail of when plan attributes changed. Plans change infrequently (5 updates across 15 migrations). | Migrations 001, 005 | 0.5h |
| DB-L02 | No retention/cleanup for `monthly_quota` historical rows | Rows accumulate indefinitely. At 5,000 users for 5 years = 300,000 rows. Manageable but worth cleaning rows older than 24 months. | N/A | 3-4h |
| DB-L03 | No retention/cleanup for `stripe_webhook_events` | Migration 010 mentions 90-day retention but nothing implements it. With JSONB payload, table grows fast in disk usage. | Migration 010 | 3-4h |
| DB-L04 | Redundant index `idx_user_oauth_tokens_provider` | Table has at most hundreds of rows. `unique_user_provider` constraint on `(user_id, provider)` already covers lookups. Standalone index on `provider` (3 possible values) has negligible selectivity. | Migration 013 | 0.25h |
| NEW-DB-04 | Missing index on `user_subscriptions.stripe_customer_id` | **NEW from @data-engineer.** Admin panel and Stripe reconciliation may query by customer_id. Currently no index exists. Low volume makes this non-urgent. | `backend/webhooks/stripe.py`, `backend/main.py` | 0.5h |
| NEW-DB-05 | `user_subscriptions.plan_id` FK lacks explicit ON DELETE documentation | **NEW from @data-engineer.** FK defaults to RESTRICT, which is correct behavior (should not delete a plan with active subscriptions), but should be explicitly documented as intentional. | `supabase/migrations/001_profiles_and_sessions.sql:66` | 0.25h |

**Subtotal Database:** 24 debts | Effort: ~38-50h

---

### 4. Frontend/UX Debts (33 items)

Source: `docs/frontend/frontend-spec.md` -- @ux-design-expert (Uma)
Reviewed and validated by: @ux-design-expert (see `docs/reviews/ux-specialist-review.md`)

Note: FE-M08 ("No middleware auth guards") was **REMOVED** -- middleware exists at `frontend/middleware.ts` with full Supabase SSR auth guard. The narrower issue (incomplete PROTECTED_ROUTES list) is captured as FE-NEW-09.

#### 4.1 CRITICAL (3)

| ID | Debt | Description | File(s) | Effort Est. |
|----|------|-------------|---------|-------------|
| FE-C01 | Monolithic buscar/page.tsx (~1100 lines) | Contains 30+ useState hooks, all business logic inline. Single component concentrating all application complexity. Prevents iterative UX improvement; single change risks regressions across all search features. | `frontend/app/buscar/page.tsx` | 16-24h |
| FE-C03 | Mixed API patterns | Some pages use proxy `/api/*`, others call `NEXT_PUBLIC_BACKEND_URL` directly from browser. Two different auth forwarding patterns, exposes backend URL to client. Creates unpredictable error handling and failures for users. | `historico/page.tsx`, `conta/page.tsx`, `admin/page.tsx` | 8-12h |
| FE-L03 | Divergent plan prices between pages | **Upgraded from LOW to CRITICAL by @ux-design-expert.** Users see R$149/349/997 on `pricing/page.tsx` but R$297/597/1497 in `lib/plans.ts` and on `planos/page.tsx`. Directly undermines user trust. A user comparing prices before signing up sees one set, then different prices on the upgrade page. | `pricing/page.tsx`, `lib/plans.ts`, `planos/page.tsx` | 2h |

#### 4.2 HIGH (8)

| ID | Debt | Description | File(s) | Effort Est. |
|----|------|-------------|---------|-------------|
| FE-C02 | Fallback localhost in analytics route | **Downgraded from CRITICAL by @ux-design-expert.** `http://localhost:8000` as fallback for `BACKEND_URL` in analytics route. Server-side only (not `NEXT_PUBLIC_`), no browser data leak. Risk is misconfigured deployment hitting localhost, not client-side exposure. Still incorrect and must be fixed. | `frontend/app/api/analytics/route.ts:4` | 1h |
| FE-H01 | Duplicate filter components | EsferaFilter and MunicipioFilter exist in two directories (`app/components/` and `components/`). Different ARIA patterns, different icon SVG paths, different stroke widths. `app/components/` version uses native `<button>` (correct); `components/` version uses `<div>` with manual keyboard handling (fragile). | `app/components/EsferaFilter.tsx`, `components/EsferaFilter.tsx`, etc. | 3-4h |
| FE-H02 | Direct DOM manipulation for search state restoration | `document.createElement` used to create success banner at lines 285-293. Bypasses React rendering, toast system, and is invisible to screen readers (no `role="status"` or `aria-live`). Uses hardcoded animation that may not respect `prefers-reduced-motion`. | `app/buscar/page.tsx:285-293` | 2-3h |
| FE-H03 | Error boundary ignores design system | Hardcoded Tailwind colors (`bg-gray-50`, `text-red-500`, `bg-green-600`) instead of design tokens. Completely white background in dark mode. Error page is the worst place for UX breakage. SVG has conflicting `role="img" aria-label="Icone"` AND `aria-hidden="true"`. | `frontend/app/error.tsx` | 1-2h |
| FE-H04 | Native `alert()` for user feedback | Uses `window.alert()` at line 1080 (save search success) and line 1087 (save search error). Blocks main thread. Disrupts flow. Inconsistent with the rest of the app which uses sonner toast. | `app/buscar/page.tsx:1080,1087` | 1h |
| FE-H06 | Excel storage in tmpdir() | If server restarts between search completion and download click, user loses results. No error message explains what happened; download just fails silently. Most confusing failure mode for users. | `app/api/buscar/route.ts`, `app/api/download/route.ts` | 6-8h |
| FE-M01 | No shared app shell for protected pages | **Upgraded from MEDIUM by @ux-design-expert.** Each protected page manages its own header independently. No persistent sidebar or breadcrumbs. The buscar page has full header with PlanBadge, QuotaBadge, MessageBadge, ThemeToggle, UserMenu; other pages have minimal or no header. App feels like separate apps stitched together. | All protected pages | 6-8h |
| FE-NEW-02 | Advanced filters toggle lacks `aria-expanded` | **NEW from @ux-design-expert.** The "Filtros Avancados" collapsible section uses a `<button>` that toggles state but does NOT have `aria-expanded`. Screen readers cannot determine panel state. WCAG 4.1.2 violation (Name, Role, Value). | `app/buscar/page.tsx:1627-1639` | 0.5h |

#### 4.3 MEDIUM (11)

| ID | Debt | Description | File(s) | Effort Est. |
|----|------|-------------|---------|-------------|
| FE-H05 | UF_NAMES duplicated in multiple files | **Downgraded from HIGH by @ux-design-expert.** Maintenance debt, not user-facing. Both copies appear identical. Risk is drift, not current UX issue. | `buscar/page.tsx`, `dashboard/page.tsx` | 1-2h |
| FE-M02 | Feature flags system underused | Feature flags defined in `lib/config.ts` but not widely adopted. Developer experience debt, not user-facing. | `frontend/lib/config.ts` | 2-3h |
| FE-M03 | No form validation library | Validation timing inconsistent: signup validates on submit, search validates in real-time, password change validates on submit. Users learn different patterns per form. No react-hook-form or zod. | Login, signup, search pages | 8-12h |
| FE-M05 | SETORES_FALLBACK requires manual sync | Sector fallback list must be manually synchronized with backend. Sync script exists (`scripts/sync-setores-fallback.js`) but is not automated. Risk: user sees stale sector names. | `app/buscar/page.tsx:429-442` | 1h |
| FE-L01 | SVG icons with generic aria-label="Icone" | **Upgraded from LOW by @ux-design-expert.** Screen reader users hear "Icone" for every SVG, providing zero information. Some elements have BOTH `role="img" aria-label="Icone"` AND `aria-hidden="true"`, which is contradictory. WCAG 1.1.1 violation. | Multiple pages | 3-4h |
| FE-L07 | Test coverage ~49.46% vs threshold 60% (70 pre-existing failures) | **Upgraded from LOW by @ux-design-expert.** Low coverage means UX regressions ship undetected. The 70 failing tests are a broken safety net. Affects team's ability to ship UX improvements confidently. | `frontend/__tests__/` | 12-16h |
| FE-NEW-01 | Contradictory ARIA on error boundary SVG | **NEW from @ux-design-expert.** `app/error.tsx` has both `role="img" aria-label="Icone"` AND `aria-hidden="true"`. These contradict: `aria-hidden` hides from AT, but `role="img"` exposes it. Screen readers may behave unpredictably. | `app/error.tsx:26-28` | 0.5h |
| FE-NEW-03 | No `aria-describedby` on search term validation errors | **NEW from @ux-design-expert.** Term validation feedback (stopword warnings, min-length errors) is displayed visually but not linked to input via `aria-describedby`. Screen readers miss validation feedback. WCAG 3.3.1 violation. | `app/buscar/page.tsx` (term validation) | 1h |
| FE-NEW-04 | No page transition indicators | **NEW from @ux-design-expert.** Navigating between protected pages shows no loading indicator. On slow connections, user stares at blank screen. No NProgress bar or similar. | All page navigations | 3-4h |
| FE-NEW-06 | framer-motion does not check `prefers-reduced-motion` | **NEW from @ux-design-expert.** 9 files import framer-motion. CSS `globals.css:281` disables CSS animations for `prefers-reduced-motion`, but framer-motion uses JS animations that bypass CSS media queries. Only `SectorsGrid.tsx` comments about respecting it. WCAG 2.3.3 accessibility concern. | 9 files using framer-motion | 2-3h |
| FE-NEW-07 | UF grid has no roving tabindex | **NEW from @ux-design-expert.** The 27-state UF selection grid creates 27 individual tab stops. Keyboard users must press Tab 27 times to pass through it. Should use roving tabindex (arrow keys within group, single Tab stop). WCAG 2.1.1 concern. | `app/components/RegionSelector.tsx` | 3-4h |

#### 4.4 LOW (11)

| ID | Debt | Description | File(s) | Effort Est. |
|----|------|-------------|---------|-------------|
| FE-M04 | STOPWORDS_PT duplicated from backend | **Downgraded from MEDIUM by @ux-design-expert.** Internal optimization data. Users never see stopwords. Drift risk minimal because the list is stable Portuguese function words. | `app/buscar/page.tsx:70-82` | 1-2h |
| FE-M06 | Stale file: `dashboard-old.tsx` | **Downgraded from MEDIUM by @ux-design-expert.** Dead code, not imported anywhere. No user impact. | `app/dashboard-old.tsx` | 0.5h |
| FE-M07 | Stale file: `landing-layout-backup.tsx` | **Downgraded from MEDIUM by @ux-design-expert.** Dead code, not imported anywhere. No user impact. | `app/landing-layout-backup.tsx` | 0.5h |
| FE-M09 | `performance.timing` deprecated | **Downgraded from MEDIUM by @ux-design-expert.** Internal analytics data collection. Users never see this value. Browser deprecation warnings only visible in dev tools. | `app/components/AnalyticsProvider.tsx:53` | 1h |
| FE-L02 | useEffect with serialized Set dependency | Set serialized as string for useEffect dependency. May cause unnecessary re-renders but no visible UX impact at current scale. | `app/buscar/page.tsx:426` | 1h |
| FE-L04 | Unused barrel file `components/filters/index.ts` | Export barrel file unused/empty. | `components/filters/index.ts` | 0.5h |
| FE-L05 | No robots.txt or sitemap | Basic SEO missing. Affects discoverability, not in-app UX. | N/A | 2-3h |
| FE-L06 | No OpenGraph images configured | Social sharing without image preview. No impact on logged-in users. | `app/layout.tsx` | 2-3h |
| FE-NEW-05 | No breadcrumbs on any protected page | **NEW from @ux-design-expert.** Users lose context of where they are in the app. Combined with lack of shared app shell, navigation feels rootless. | All protected pages | 2-3h |
| FE-NEW-08 | Sector list not cached client-side | **NEW from @ux-design-expert.** Every visit to `/buscar` fetches sector list from backend. On slow connections, dropdown shows loading state each time. Should cache in memory or localStorage with short TTL. | `app/buscar/page.tsx` (sector fetch) | 1-2h |
| FE-NEW-09 | `/mensagens` and `/planos/obrigado` missing from middleware PROTECTED_ROUTES | **NEW from @ux-design-expert.** These routes require auth but are not in the middleware list. Flash of content possible on these two routes specifically. Replaces removed FE-M08. | `frontend/middleware.ts:15-21` | 0.5h |

**Accessibility notes from audit (tracked via FE-NEW items above):**
- `aria-live` regions for dynamic updates need coverage of empty and error states
- `aria-expanded` missing on collapsible filter panels (FE-NEW-02)
- `aria-describedby` missing linking form fields to validation errors (FE-NEW-03)
- No roving tabindex for 27-state UF grid (FE-NEW-07)
- Custom dropdowns may not implement full ARIA listbox pattern
- framer-motion may not respect `prefers-reduced-motion` (FE-NEW-06)

**Subtotal Frontend:** 33 debts | Effort: ~115-162h

---

### 5. Cross-Cutting Debts (5 items)

These debts affect multiple system areas simultaneously.

| ID | Debt | Areas | Severity | Description | Effort Est. |
|----|------|-------|----------|-------------|-------------|
| CROSS-C01 | Dual ORM affecting DB + Backend | Database, Backend | CRITICAL | `database.py` constructs PostgreSQL URL incorrectly from `SUPABASE_URL` (HTTPS), affecting Stripe webhook handlers that use SQLAlchemy. The rest of the code uses Supabase client. Two transaction strategies, two connection pools, schema drift between SQL migrations and SQLAlchemy models. **Most impactful systemic debt.** | 12-16h |
| CROSS-C02 | Excel storage in temporary filesystem | Backend, Frontend | CRITICAL | Backend generates Excel (base64 in JSON response). Frontend proxy saves to `tmpdir()` with setTimeout cleanup. Not shared between instances. Not persistent across restarts. Affects both API proxy route and download route. | 8-12h |
| CROSS-H01 | Inconsistent API patterns between frontend and backend | Frontend, Backend | HIGH | Frontend mixes proxy routes (`/api/*`) with direct calls to `NEXT_PUBLIC_BACKEND_URL`. Two auth forwarding patterns. Backend URL exposed to client. Affects: `historico`, `conta`, `admin`, `mensagens`. | 8-12h |
| CROSS-M01 | Plan data hardcoded in multiple places | Database, Backend, Frontend | MEDIUM | Plan capabilities in `quota.py:62-95` (Python), prices in `plans` table (DB), prices in `pricing/page.tsx` and `lib/plans.ts` (frontend). Values diverge (149/349/997 vs 297/597/1497). No single source of truth accessible to all. | 6-8h |
| CROSS-M02 | Pre-existing test failures mask regressions | Backend, Frontend, CI/CD | MEDIUM | Backend: 21 pre-existing failures (billing, stripe, feature flags, prorata). Frontend: 70 pre-existing failures. CI pipeline is not green, quality gates non-functional. New regressions are invisible. | 16-24h |

**Subtotal Cross-Cutting:** 5 debts | Effort: ~50-72h

---

### 6. Testing Debts (5 items)

Source: `docs/reviews/qa-review.md` -- @qa
These gaps were identified during the QA review as areas where the testing strategy is insufficiently defined to support debt resolution work.

| ID | Debt | Severity | Description | Effort Est. |
|----|------|----------|-------------|-------------|
| TEST-01 | Backend testing strategy undocumented | MEDIUM | No documented mocking strategy for PNCP API, no test data fixture templates, no clear unit vs integration test structure guide. Developers may spend time choosing approaches. | 1-2h (documentation) |
| TEST-02 | Frontend testing strategy undocumented | MEDIUM | No documented breakdown of 60% coverage target (unit vs integration vs E2E ratio). No MSW (Mock Service Worker) setup for API mocking. No accessibility test tooling (axe, jest-axe). | 1-2h (documentation) |
| TEST-03 | PNCP API resilience test plan missing | HIGH | No documented approach for testing rate limiting, 429 response handling, exponential backoff behavior, or circuit breaker without hitting real PNCP API. Critical for production reliability. | 4-6h (implementation + docs) |
| TEST-04 | Excel output validation tests missing | MEDIUM | No test suite for validating Excel file structure (column count, headers, data types, currency formatting, styling). No tests for large file handling (500+ rows). | 3-4h |
| TEST-05 | LLM integration error case tests missing | MEDIUM | No documented test scenarios for OpenAI API timeout, invalid JSON response, token limit exceeded, or rate limiting (429). LLM could fail silently. | 2-3h |

**Subtotal Testing:** 5 debts | Effort: ~12-17h

---

### 7. Priority Matrix

All 90 items organized by resolution priority. Priorities account for specialist-reviewed severities.

#### P0 -- Immediate (Security + Trust-Critical)

| ID | Debt | Area | Final Severity | Effort | Rationale |
|----|------|------|----------------|--------|-----------|
| DB-C03 | Fix `stripe_webhook_events` admin policy | DB | CRITICAL | 0.5h | Direct access control bug. Single ALTER POLICY. |
| DB-H04 | Tighten overly permissive RLS | DB | HIGH | 1h | Security hardening. No behavior change for existing code. |
| DB-H03 | Add unique index on `stripe_subscription_id` | DB | HIGH | 0.5h | Performance + data integrity. |
| NEW-DB-03 | Add trigram index on `profiles.email` | DB | MEDIUM | 1h | Admin panel performance. Prevents full table scan. |
| FE-L03 | **Fix divergent plan prices** | FE | CRITICAL | 2h | Trust-destroying. Users see different prices on different pages. |
| FE-H04 | Replace `alert()` with sonner toast | FE | HIGH | 1h | Trivial fix, high UX improvement. |
| FE-H03 | Fix error boundary design system | FE | HIGH | 1-2h | Dark mode completely broken on error page. |
| FE-NEW-02 | Add `aria-expanded` to advanced filters | FE | HIGH | 0.5h | One-line WCAG 4.1.2 fix. |
| FE-NEW-01 | Fix contradictory ARIA on error SVG | FE | MEDIUM | 0.5h | Fix while touching error boundary anyway. |
| FE-C02 | Remove localhost fallback in analytics | FE | HIGH | 1h | Quick security fix. |
| SYS-H05 | Split requirements prod/dev | SYS | HIGH | 2-3h | Reduces attack surface. |

**P0 Total: ~11-14h**

#### P1 -- Core Architecture (ORM Consolidation + API Unification + App Shell)

| ID | Debt | Area | Final Severity | Effort | Rationale |
|----|------|------|----------------|--------|-----------|
| CROSS-C01 + DB-C01 + DB-H01 + NEW-DB-01 | **Consolidate ORM** | Cross + DB | CRITICAL | 10-14h | Most impactful single fix. Resolves 4 debts. |
| DB-C02 | Add service role RLS on `user_subscriptions` | DB | HIGH | 1h | Consistency. |
| DB-H02 | Consolidate migration 006 files | DB | HIGH | 1-2h | Clean up confusion. |
| NEW-DB-02 | Fix `handle_new_user()` default plan_type | DB | MEDIUM | 0.5h | Every new user gets legacy value. |
| FE-C03 + CROSS-H01 | **Unify API patterns** | FE + Cross | CRITICAL + HIGH | 8-12h | Consistent error handling, security. |
| FE-M01 | **Shared app shell** | FE | HIGH | 6-8h | Biggest single UX improvement. |
| FE-H01 | Consolidate duplicate filter components | FE | HIGH | 3-4h | Delete fragile `components/` versions. |
| FE-H02 | Replace DOM manipulation with toast | FE | HIGH | 2-3h | React anti-pattern + a11y gap. |
| SYS-C04 + CROSS-M02 | Fix pre-existing test failures | SYS + Cross | CRITICAL + MEDIUM | 8-16h | Restore CI pipeline. |
| TEST-03 | PNCP API resilience test plan | TEST | HIGH | 4-6h | Production reliability. |
| SYS-H01 | Remove synchronous PNCP client | SYS | HIGH | 4-6h | Blocks event loop. |

**P1 Total: ~48-72h**

#### P2 -- Decomposition + Quality (Monolith Breakup + Testing + Scaling)

| ID | Debt | Area | Final Severity | Effort | Rationale |
|----|------|------|----------------|--------|-----------|
| SYS-C02 + SYS-H04 | Decompose main.py | SYS | CRITICAL | 12-16h | Includes business logic extraction. |
| FE-C01 | Decompose buscar/page.tsx | FE | CRITICAL | 16-24h | Prerequisite for search UX iteration. |
| SYS-C01 | Migrate SSE state to Redis | SYS | CRITICAL | 16-24h | Horizontal scaling prerequisite. |
| CROSS-C02 + SYS-H02 + FE-H06 | Object storage for Excel | Cross + SYS + FE | CRITICAL + HIGH | 8-12h | Resolves 3 debts. |
| SYS-M01 | Add correlation IDs | SYS | MEDIUM | 3-4h | Easier after decomposition. |
| SYS-M07 + FE-L07 | Frontend coverage to 60% | SYS + FE | MEDIUM | 12-16h | Restore coverage gate. |
| DB-M04 | Add plan_type sync trigger | DB | MEDIUM | 2-3h | Eliminates drift permanently. |
| DB-M01 | Standardize FK references | DB | MEDIUM | 3-4h | Consistency. |
| DB-M06 + DB-M07 | RPC functions for N+1 + analytics | DB | MEDIUM | 4-6h | Performance. |
| FE-NEW-03 | aria-describedby for validation | FE | MEDIUM | 1h | WCAG 3.3.1. |
| FE-NEW-06 | prefers-reduced-motion support | FE | MEDIUM | 2-3h | Accessibility. |
| FE-NEW-07 | Roving tabindex for UF grid | FE | MEDIUM | 3-4h | Keyboard usability. |
| FE-L01 | Fix generic SVG aria-labels | FE | MEDIUM | 3-4h | WCAG 1.1.1. |
| TEST-01 + TEST-02 | Document testing strategies | TEST | MEDIUM | 2-4h | Developer guidance. |
| TEST-04 + TEST-05 | Excel + LLM test suites | TEST | MEDIUM | 5-7h | Test coverage. |

**P2 Total: ~93-131h**

#### P3 -- Polish + Optimization (Remaining MEDIUM + All LOW)

| ID | Debt | Area | Final Severity | Effort |
|----|------|------|----------------|--------|
| DB-M02 | Tighten plan_type CHECK constraint | DB | MEDIUM | 1-2h |
| DB-M03 | Fix updated_at migration | DB | MEDIUM | 1h |
| DB-M05 | Environment-aware Stripe IDs | DB | MEDIUM | 2h |
| DB-H05 | Add profiles INSERT policy | DB | MEDIUM | 0.5h |
| CROSS-M01 | Reconcile plan data | Cross | MEDIUM | 6-8h |
| FE-H05 | Extract UF_NAMES | FE | MEDIUM | 1-2h |
| FE-M03 | Adopt zod + react-hook-form | FE | MEDIUM | 8-12h |
| FE-NEW-04 | Page transition indicators | FE | MEDIUM | 3-4h |
| FE-M02 | Expand feature flags | FE | MEDIUM | 2-3h |
| FE-M05 | Automate SETORES sync | FE | MEDIUM | 1h |
| SYS-M02 | Fix token cache hash | SYS | MEDIUM | 2-3h |
| SYS-M03 | Rate limiter max size | SYS | MEDIUM | 2-3h |
| SYS-M04 | Plan capabilities to DB | SYS | MEDIUM | 4-6h |
| SYS-M05 | Google API credentials | SYS | MEDIUM | 2-3h |
| SYS-M06 | Replace datetime.utcnow() | SYS | MEDIUM | 2-3h |
| SYS-M08 | API versioning | SYS | MEDIUM | 4-6h |
| SYS-H03 | Track migrations in repo | SYS | HIGH | 4-6h |
| DB-L01 | plans updated_at | DB | LOW | 0.5h |
| DB-L02 + DB-L03 | Retention cleanup (pg_cron) | DB | LOW | 6-8h |
| DB-L04 | Drop redundant index | DB | LOW | 0.25h |
| NEW-DB-04 | Index on stripe_customer_id | DB | LOW | 0.5h |
| NEW-DB-05 | Document plan_id FK | DB | LOW | 0.25h |
| SYS-L01 | OpenAPI schema validation | SYS | LOW | 4-6h |
| SYS-L02 | Remove emoji from logs | SYS | LOW | 1h |
| SYS-L03 | Replace inline CSS | SYS | LOW | 1-2h |
| SYS-L04 | Request logging middleware | SYS | LOW | 3-4h |
| SYS-L05 | Clean unused imports | SYS | LOW | 0.5h |
| SYS-L06 | Redis health check | SYS | LOW | 2h |
| FE-M04 | Extract STOPWORDS_PT | FE | LOW | 1-2h |
| FE-M06 + FE-M07 | Delete stale files | FE | LOW | 1h |
| FE-M09 | Replace performance.timing | FE | LOW | 1h |
| FE-L02 | Fix useEffect Set dep | FE | LOW | 1h |
| FE-L04 | Delete unused barrel file | FE | LOW | 0.5h |
| FE-L05 | robots.txt + sitemap | FE | LOW | 2-3h |
| FE-L06 | OpenGraph images | FE | LOW | 2-3h |
| FE-NEW-05 | Breadcrumbs | FE | LOW | 2-3h |
| FE-NEW-08 | Cache sector list | FE | LOW | 1-2h |
| FE-NEW-09 | Missing middleware routes | FE | LOW | 0.5h |

**P3 Total: ~68-99h**

---

### 8. Dependency Chains

```
Chain 1: ORM Consolidation (prerequisite for all DB Stripe work)
  CROSS-C01 (Dual ORM) --must-precede-->
    DB-C01 (database.py URL) --must-precede-->
      DB-H01 + NEW-DB-01 (Consolidate ORM + competing handlers) --must-precede-->
        DB-H03 (Index stripe_subscription_id)
        DB-M04 (sync_profile_plan_type trigger)

Chain 2: Backend Monolith Decomposition
  SYS-C02 (main.py 1959 lines) --must-precede-->
    SYS-H04 (Business logic in helpers -- extracted during decomposition)
    SYS-M01 (Correlation IDs -- easier after decomposition)
    SYS-L04 (Request logging middleware)

Chain 3: Frontend Monolith Decomposition
  FE-C01 (buscar 1100 lines) --must-precede-->
    FE-H01 (Duplicate components -- consolidate during decomposition)
    FE-H02 (DOM manipulation -- refactor during decomposition)
    FE-H05 (UF_NAMES -- extract during decomposition)
    FE-M03 (Form validation library -- integrate during decomposition)
    FE-NEW-07 (Roving tabindex -- easier on extracted RegionSelector)

Chain 4: Horizontal Scaling Prerequisites
  SYS-C01 (In-memory SSE state) --must-precede-->
    CROSS-C02 (Excel in tmpdir) --must-precede-->
      SYS-H02 + FE-H06 (Object storage for Excel)

Chain 5: CI/CD Green Pipeline
  SYS-C04 + CROSS-M02 (Fix pre-existing test failures) --must-precede-->
    SYS-M07 + FE-L07 (Frontend coverage to 60%) --must-precede-->
      SYS-L01 (OpenAPI schema validation)

Chain 6: RLS Security Hardening (parallel, all independent)
  DB-C03 (stripe_webhook_events admin check) --parallel-->
  DB-H04 (Overly permissive policies) --parallel-->
  DB-C02 (user_subscriptions service role) --parallel-->
  DB-H05 (profiles INSERT policy)

Chain 7: API Pattern Unification
  FE-C03 + CROSS-H01 (Mixed API patterns) --must-precede-->
    FE-C02 (localhost fallback -- fix during unification)
    FE-M01 (Shared app shell -- easier after unified patterns)

Chain 8: Plan Data Consistency
  FE-L03 (Divergent prices -- P0 immediate fix) --must-precede-->
    CROSS-M01 (Single source of truth for plan data)
    NEW-DB-02 (Fix handle_new_user default)
    DB-M02 (Tighten CHECK constraint)
```

---

### 9. Sprint Resolution Plan

#### Sprint 1: Foundation -- Security + Trust (Week 1)

**Objective:** Fix critical security issues, price divergence, and quick UX wins.
**Effort:** ~20-28h
**Risk:** Low (all changes are targeted, additive, or simple fixes)

| Order | ID(s) | Task | Hours |
|-------|--------|------|-------|
| 1 | DB-C03 | Fix `stripe_webhook_events` admin policy (`plan_type='master'` -> `is_admin=true`) | 0.5h |
| 2 | DB-H04 | Tighten RLS on monthly_quota and search_sessions (add `TO service_role`) | 1h |
| 3 | DB-H03 | Add unique index on `stripe_subscription_id` | 0.5h |
| 4 | NEW-DB-03 | Add trigram index on `profiles.email` | 1h |
| 5 | DB-C02 | Add service role policy on `user_subscriptions` | 1h |
| 6 | NEW-DB-02 | Fix `handle_new_user()` default (`'free'` -> `'free_trial'`) | 0.5h |
| -- | -- | **Items 1-6: combine in single migration `016_security_and_index_fixes.sql`** | -- |
| 7 | FE-L03 | **Fix divergent plan prices** -- reconcile with product owner, single source | 2h |
| 8 | FE-H04 | Replace `window.alert()` with sonner toast (2 call sites) | 1h |
| 9 | FE-H03 + FE-NEW-01 | Fix error boundary: design tokens + fix contradictory ARIA | 1.5-2.5h |
| 10 | FE-NEW-02 | Add `aria-expanded` to advanced filters toggle | 0.5h |
| 11 | FE-C02 | Remove localhost fallback in analytics route | 1h |
| 12 | SYS-H05 | Split requirements.txt into prod/dev | 2-3h |
| 13 | DB-H02 | Consolidate migration 006 duplicates | 1-2h |
| 14 | SYS-L05 | Clean unused imports (trivial, while touching files) | 0.5h |

**Deliverable:** All P0 security fixes deployed. Prices reconciled. Error boundary fixed for dark mode. WCAG quick wins landed. Single migration file handles all DB fixes atomically.

#### Sprint 2: Consolidation -- Architecture Unification (Weeks 2-3)

**Objective:** Eliminate dual ORM, unify API patterns, establish shared app shell.
**Effort:** ~48-72h
**Risk:** Medium (ORM consolidation is highest-risk change; requires Stripe webhook monitoring post-deploy)

| Order | ID(s) | Task | Hours |
|-------|--------|------|-------|
| 1 | CROSS-C01 + DB-C01 + DB-H01 + NEW-DB-01 | **Consolidate ORM:** rewrite `webhooks/stripe.py` to Supabase client, ensure all handlers sync `profiles.plan_type`, delete `database.py` and `models/` | 10-14h |
| 2 | FE-C03 + CROSS-H01 | **Unify API patterns:** migrate all direct backend calls to proxy `/api/*` routes | 8-12h |
| 3 | FE-M01 | **Implement shared app shell:** `(protected)/layout.tsx` with AppHeader, consistent nav | 6-8h |
| 4 | FE-H01 | Consolidate duplicate filter components (delete `components/` versions) | 3-4h |
| 5 | FE-H02 | Replace DOM manipulation with sonner toast | 2-3h |
| 6 | SYS-C04 + CROSS-M02 | Fix/triage pre-existing test failures (restore green CI) | 8-16h |
| 7 | SYS-H01 | Remove/refactor synchronous PNCPClient | 4-6h |
| 8 | TEST-03 | Create PNCP API resilience test plan + mock fixtures | 4-6h |

**Deliverable:** Single ORM (Supabase client only). All frontend calls via proxy. Shared app shell for all protected pages. CI pipeline green. PNCP test infrastructure established.

**ORM Consolidation rollback plan:** Keep `database.py` and models as dead code for 2 weeks. Monitor Stripe webhook delivery in Stripe Dashboard. Re-enable import if issues arise.

#### Sprint 3: Decomposition -- Monolith Breakup + Scaling (Weeks 4-6)

**Objective:** Break monolithic files into maintainable modules. Establish horizontal scaling prerequisites. Improve test coverage and accessibility.
**Effort:** ~93-131h
**Risk:** Medium (large refactors require visual regression testing; Redis migration requires infrastructure changes)

| Order | ID(s) | Task | Hours |
|-------|--------|------|-------|
| 1 | SYS-C02 + SYS-H04 | **Decompose main.py:** extract into router modules (search, auth, billing, sessions, authorization) | 12-16h |
| 2 | FE-C01 | **Decompose buscar/page.tsx:** SearchForm, FilterPanel, SearchResults, useSearch, useSearchFilters | 16-24h |
| 3 | SYS-C01 | Migrate SSE state to Redis pub/sub | 16-24h |
| 4 | CROSS-C02 + SYS-H02 + FE-H06 | Object storage for Excel (Supabase Storage or S3) | 8-12h |
| 5 | SYS-M01 | Add correlation IDs (easier after main.py decomposition) | 3-4h |
| 6 | SYS-M07 + FE-L07 | Improve frontend test coverage to 60%+ | 12-16h |
| 7 | DB-M04 | Add plan_type sync trigger | 2-3h |
| 8 | DB-M01 | Standardize FK references | 3-4h |
| 9 | DB-M06 + DB-M07 | Create RPC functions for N+1 + analytics queries | 4-6h |
| 10 | FE-NEW-03 | Add `aria-describedby` for validation errors | 1h |
| 11 | FE-NEW-06 | framer-motion `prefers-reduced-motion` support | 2-3h |
| 12 | FE-NEW-07 | Implement roving tabindex for UF grid | 3-4h |
| 13 | FE-L01 | Fix all generic SVG aria-labels | 3-4h |
| 14 | TEST-01 + TEST-02 | Document backend + frontend testing strategies | 2-4h |
| 15 | TEST-04 + TEST-05 | Create Excel validation + LLM fallback test suites | 5-7h |

**Deliverable:** main.py decomposed into 5+ router modules. buscar/page.tsx decomposed into 5 components/hooks. SSE via Redis. Excel via object storage. Frontend coverage >= 60%. Testing infrastructure documented. WCAG accessibility sprint completed.

#### Sprint 4: Polish + Optimization (Weeks 7-8+)

**Objective:** Address remaining MEDIUM and LOW items. Performance optimization. Cleanup.
**Effort:** ~68-99h (can be spread across multiple sprints or done incrementally)

| Order | ID(s) | Task | Hours |
|-------|--------|------|-------|
| 1 | DB-M02 | Tighten plan_type CHECK constraint (remove legacy values) | 1-2h |
| 2 | DB-M03 + DB-M05 | Fix updated_at migration + env-aware Stripe IDs | 3h |
| 3 | DB-H05 | Add explicit INSERT policy on profiles | 0.5h |
| 4 | CROSS-M01 | Reconcile hardcoded plan data (single source of truth) | 6-8h |
| 5 | FE-H05 | Extract UF_NAMES to shared module | 1-2h |
| 6 | FE-M03 | Adopt zod + react-hook-form (conta, login, signup) | 8-12h |
| 7 | FE-NEW-04 | Add page transition indicators | 3-4h |
| 8 | SYS-M02 | Fix token cache hash mechanism | 2-3h |
| 9 | SYS-M03 | Add max size to in-memory rate limiter | 2-3h |
| 10 | SYS-M04 | Move plan capabilities to database | 4-6h |
| 11 | SYS-M06 | Replace `datetime.utcnow()` across codebase | 2-3h |
| 12 | SYS-M08 | Add API versioning prefix | 4-6h |
| 13 | SYS-H03 | Establish tracked migration workflow | 4-6h |
| 14 | FE-M02 + FE-M05 | Expand feature flags + automate SETORES sync | 3-4h |
| 15 | SYS-M05 | Review Google API credentials handling | 2-3h |
| 16 | DB-L02 + DB-L03 | Retention cleanup via pg_cron | 6-8h |
| 17 | Remaining LOW items | All cleanup, SEO, dead code, indexes, docs | ~25-35h |

**Deliverable:** All MEDIUM items resolved. Backlog of LOW items worked down. System fully polished for production scaling.

---

### 10. Changes from DRAFT

This section documents all modifications made to the DRAFT based on specialist reviews.

#### 10.1 Severity Changes (13 changes)

| ID | DRAFT Severity | FINAL Severity | Changed By | Reason |
|----|---------------|----------------|------------|--------|
| DB-C02 | CRITICAL | **HIGH** | @data-engineer | Service_role key bypasses RLS by design. Risk is future-proofing, not present breakage. |
| DB-H01 | HIGH | **CRITICAL** | @data-engineer | Competing Stripe handler implementations discovered. Active correctness risk. |
| DB-H05 | HIGH | **MEDIUM** | @data-engineer | No code path where regular user INSERTs into profiles. Good hygiene, not exploitable. |
| FE-C02 | CRITICAL | **HIGH** | @ux-design-expert | Server-side only env var, not `NEXT_PUBLIC_`. No browser data leak. |
| FE-H05 | HIGH | **MEDIUM** | @ux-design-expert | Maintenance issue, not user-facing. Both copies identical. |
| FE-M01 | MEDIUM | **HIGH** | @ux-design-expert | App feels like separate apps stitched together. Biggest single UX improvement opportunity. |
| FE-M04 | MEDIUM | **LOW** | @ux-design-expert | Stable data, no user impact. Internal optimization. |
| FE-M06 | MEDIUM | **LOW** | @ux-design-expert | Dead code, zero user impact. |
| FE-M07 | MEDIUM | **LOW** | @ux-design-expert | Dead code, zero user impact. |
| FE-M09 | MEDIUM | **LOW** | @ux-design-expert | Internal analytics, no user impact. |
| FE-L01 | LOW | **MEDIUM** | @ux-design-expert | WCAG 1.1.1 violation. Directly affects assistive technology users. |
| FE-L03 | LOW | **CRITICAL** | @ux-design-expert | Trust-destroying. Users see different prices on different pages. |
| FE-L07 | LOW | **MEDIUM** | @ux-design-expert | Affects ability to ship UX improvements confidently. |

#### 10.2 Items Removed (1 item)

| ID | DRAFT Description | Removed By | Reason |
|----|-------------------|------------|--------|
| FE-M08 | "No middleware auth guards (flash of unprotected content)" | @ux-design-expert | Middleware EXISTS at `frontend/middleware.ts` with full Supabase SSR auth guard. Narrower issue (incomplete PROTECTED_ROUTES) captured as FE-NEW-09. |

#### 10.3 New Items Added (19 items)

**From @data-engineer (5 items):**

| ID | Description | Severity | Source |
|----|-------------|----------|--------|
| NEW-DB-01 | Competing Stripe webhook handler implementations | CRITICAL | Found during DB-H01 deep analysis |
| NEW-DB-02 | `handle_new_user()` trigger sets legacy `plan_type = 'free'` | MEDIUM | Migration analysis |
| NEW-DB-03 | Missing index on `profiles.email` for admin ILIKE search | MEDIUM | DB-AUDIT PERF-IDX-3 (not carried to DRAFT) |
| NEW-DB-04 | Missing index on `stripe_customer_id` | LOW | DB-AUDIT PERF-IDX-2 (not carried to DRAFT) |
| NEW-DB-05 | `plan_id` FK lacks explicit ON DELETE documentation | LOW | DB-AUDIT INTEGRITY-2 (not carried to DRAFT) |

**From @ux-design-expert (9 items):**

| ID | Description | Severity | Source |
|----|-------------|----------|--------|
| FE-NEW-01 | Contradictory ARIA on error boundary SVG | MEDIUM | Code review of error.tsx |
| FE-NEW-02 | Advanced filters toggle lacks `aria-expanded` | HIGH | WCAG 4.1.2 audit |
| FE-NEW-03 | No `aria-describedby` on search validation errors | MEDIUM | WCAG 3.3.1 audit |
| FE-NEW-04 | No page transition indicators | MEDIUM | UX flow analysis |
| FE-NEW-05 | No breadcrumbs on protected pages | LOW | UX wayfinding analysis |
| FE-NEW-06 | framer-motion does not check `prefers-reduced-motion` | MEDIUM | Accessibility audit |
| FE-NEW-07 | UF grid no roving tabindex | MEDIUM | Keyboard usability audit |
| FE-NEW-08 | Sector list not cached client-side | LOW | Performance observation |
| FE-NEW-09 | Missing middleware PROTECTED_ROUTES entries | LOW | Replaces removed FE-M08 |

**From @qa (5 items):**

| ID | Description | Severity | Source |
|----|-------------|----------|--------|
| TEST-01 | Backend testing strategy undocumented | MEDIUM | QA Gap 1 |
| TEST-02 | Frontend testing strategy undocumented | MEDIUM | QA Gap 2 |
| TEST-03 | PNCP API resilience test plan missing | HIGH | QA Gap 3 |
| TEST-04 | Excel output validation tests missing | MEDIUM | QA Gap 4 |
| TEST-05 | LLM integration error case tests missing | MEDIUM | QA Gap 5 |

#### 10.4 Effort Estimate Changes

| Area | DRAFT Estimate | FINAL Estimate | Delta | Reason |
|------|---------------|----------------|-------|--------|
| System | 105-155h | 105-155h | 0 | No changes to system items |
| Database | 43-62h | 38-50h | -5 to -12h | Tighter scoping after code verification by @data-engineer |
| Frontend | 85-120h | 115-162h | +30 to +42h | 9 new items + upgraded priorities by @ux-design-expert |
| Cross-cutting | 50-72h | 50-72h | 0 | No changes |
| Testing | N/A | 12-17h | +12 to +17h | New category from QA gaps |
| **Total** | **280-380h** | **320-456h** | **+40 to +76h** | Net increase from new items and upgraded priorities |

#### 10.5 Sprint Plan Changes

- **Sprint 1 (P0):** Added FE-L03 (divergent prices, upgraded to CRITICAL), FE-NEW-01, FE-NEW-02 (WCAG quick wins). Added DB-C02, NEW-DB-02, NEW-DB-03 to combined migration file. Removed FE-M08.
- **Sprint 2 (P1):** Added FE-M01 (shared app shell, upgraded to HIGH), TEST-03 (PNCP test plan). ORM consolidation work item now explicitly includes NEW-DB-01.
- **Sprint 3 (P2):** Added accessibility items (FE-NEW-03, FE-NEW-06, FE-NEW-07, FE-L01), testing documentation (TEST-01, TEST-02), and test suite creation (TEST-04, TEST-05).
- **Sprint 4 (P3):** Absorbed downgraded items (FE-M04, FE-M06, FE-M07, FE-M09 now LOW). Added remaining new LOW items (FE-NEW-05, FE-NEW-08, FE-NEW-09, NEW-DB-04, NEW-DB-05).

---

### 11. Positive Observations (Preserve)

These qualities were highlighted by specialists and must be preserved during debt resolution:

**Architecture/Backend:**
1. Retry with exponential backoff and jitter in PNCP client
2. Parallel UF fetching with asyncio.Semaphore (10 concurrent)
3. Fail-fast sequential filtering (cheapest filters first)
4. LLM Arbiter pattern (auto-accept/reject + LLM for medium confidence)
5. Feature flags runtime-configurable via env vars
6. Multi-layer subscription fallback (4 layers, "fail to last known plan")
7. Log sanitization (PII masking)
8. Stripe webhook idempotency

**Database:**
9. Atomic quota increment functions (race condition prevention)
10. RLS enabled on 100% of tables
11. Partial indexes for common queries (`is_active`, `is_admin`, unread messages)
12. GIN index for JSONB queries
13. Token encryption at rest (AES-256 Fernet)
14. Migrations with validation blocks and inline documentation

**Frontend:**
15. Design system with CSS custom properties (WCAG contrast documented)
16. Dark mode with flash prevention
17. EmptyState component with actionable guidance
18. SSE progress tracking with simulation fallback
19. Keyboard shortcuts (Ctrl+K, Ctrl+A, Escape)
20. Skip navigation link (WCAG 2.4.1)
21. Focus-visible outlines (WCAG 2.2 Level AAA)
22. Error message translation (technical -> user-friendly Portuguese)
23. Pull-to-refresh mobile

---

### 12. Sign-off

| Reviewer | Role | Status | Date |
|----------|------|--------|------|
| @architect (Aria) | Technical Architect -- Author and Final Consolidation | APPROVED | 2026-02-11 |
| @data-engineer (Dara) | Database Specialist -- Section 3 Review | APPROVED | 2026-02-11 |
| @ux-design-expert (Uma) | UX Specialist -- Section 4 Review | APPROVED | 2026-02-11 |
| @qa | Quality Assurance -- Full Assessment Review | APPROVED (with adjustments, incorporated) | 2026-02-11 |

---

*Final document consolidated by @architect (Aria) on 2026-02-11. Incorporates all specialist reviews from @data-engineer, @ux-design-expert, and @qa. All file paths and line numbers reference codebase state at commit `808cd05` on branch `main`.*
