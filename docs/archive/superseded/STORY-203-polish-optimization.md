# STORY-203: Polish and Optimization

**Status:** In Progress
**Sprint:** 4 (Weeks 7-8+)
**Priority:** P3 -- Polish + Optimization
**Effort:** 68-99h
**Epic:** EPIC-TD (Technical Debt Resolution)
**Dependencies:** STORY-202 (decomposition must be complete for many items; some items can start in parallel with Sprint 3)

---

## Context

With Sprints 1-3 complete, SmartLic/BidIQ has resolved all CRITICAL and HIGH items. The system has a single ORM, unified API patterns, a shared app shell, decomposed monoliths, horizontal scaling infrastructure, a green CI pipeline, and 60%+ frontend test coverage.

Sprint 4 addresses the remaining MEDIUM and LOW items: performance optimizations, developer experience improvements, cleanup of legacy code, SEO basics, and additional polish. These items individually have low risk and can be worked on incrementally or in parallel.

This sprint can extend beyond 2 weeks if needed. Items are ordered by business impact, but many can be worked on independently.

---

## Acceptance Criteria

### Database Cleanup

- [x] **DB-M02**: Tighten `plan_type` CHECK constraint -- remove legacy values (`free`, `avulso`, `pack`, `monthly`, `annual`)
  - Prerequisite: NEW-DB-02 (Sprint 1) already changed default from `'free'` to `'free_trial'`
  - Migrate any existing rows with legacy values to their current equivalents before tightening constraint
  - Files: `supabase/migrations/020_tighten_plan_type_constraint.sql` (new)
  - Validation: INSERT with `plan_type = 'free'` fails. All existing rows have non-legacy values. `PLAN_TYPE_MAP` in `quota.py` can be simplified.
  - Effort: 1-2h

- [x] **DB-M03 + DB-M05**: Fix `updated_at` migration gap for `user_subscriptions` + make Stripe price IDs environment-aware
  - DB-M03: Add `updated_at` column to `user_subscriptions` via migration (if not already present). Add trigger for auto-update.
  - DB-M05: Replace hardcoded Stripe price IDs in migration 015 with environment-variable-based approach or conditional SQL
  - Files: `supabase/migrations/021_user_subscriptions_updated_at.sql` (new), `supabase/migrations/015_add_stripe_price_ids_monthly_annual.sql` (document issue)
  - Validation: `updated_at` auto-updates on row modification. Price IDs are appropriate for the target environment (staging vs production).
  - Effort: 3h

- [x] **DB-H05**: Add explicit INSERT policy on `profiles` table
  - Good hygiene even though `handle_new_user()` runs as SECURITY DEFINER and `_ensure_profile_exists()` uses service_role
  - Files: `supabase/migrations/020_tighten_plan_type_constraint.sql` (can combine)
  - Validation: Policy exists. No behavior change for existing flows (trigger and service_role bypass RLS).
  - Effort: 0.5h

### Plan Data Reconciliation

- [x] **CROSS-M01**: Establish single source of truth for plan data across database, backend, and frontend
  - Create backend endpoint `/api/plans` that serves plan details (name, capabilities, prices) from the `plans` database table
  - Frontend reads plan data from this endpoint instead of hardcoded values in `lib/plans.ts` and `pricing/page.tsx`
  - Backend `quota.py` reads plan capabilities from database instead of hardcoded `PLAN_TYPE_MAP`
  - Files: `backend/routes/plans.py` (new), `backend/quota.py` (lines 62-95), `frontend/lib/plans.ts`, `frontend/app/pricing/page.tsx`, `frontend/app/planos/page.tsx`
  - Validation: Change a plan price in the database -- it reflects on both pricing page and upgrade page without code deployment. No hardcoded prices remain in frontend.
  - Effort: 6-8h

### Frontend Polish

- [x] **FE-H05**: Extract `UF_NAMES` mapping to shared module
  - Currently duplicated in `buscar/page.tsx` and `dashboard/page.tsx`
  - Create `frontend/lib/constants/uf-names.ts` with canonical mapping
  - Files: `frontend/lib/constants/uf-names.ts` (new), `frontend/app/(protected)/buscar/page.tsx`, `frontend/app/(protected)/dashboard/page.tsx`
  - Validation: Single source of truth for UF names. Both pages import from shared module. No duplicate UF_NAMES definitions.
  - Effort: 1-2h

- [ ] **FE-M03**: Adopt zod + react-hook-form for form validation
  - Standardize validation timing across all forms (login, signup, search, password change, conta settings)
  - Create zod schemas for each form
  - Replace manual validation with react-hook-form integration
  - Files: `frontend/app/(public)/login/page.tsx`, `frontend/app/(public)/cadastro/page.tsx`, `frontend/app/(protected)/conta/page.tsx`, `frontend/app/components/SearchForm.tsx` (from Sprint 3 decomposition)
  - Validation: All forms validate consistently (real-time field validation). Error messages appear immediately on blur. Form submissions are blocked until valid. No manual useState for validation errors.
  - Effort: 8-12h

- [x] **FE-NEW-04**: Add page transition indicators (NProgress or similar)
  - Show loading bar/indicator when navigating between protected pages
  - Prevent user from staring at blank screen on slow connections
  - Files: `frontend/app/(protected)/layout.tsx`
  - Validation: Navigate between pages -- loading indicator visible during transition. Works on slow 3G throttled connection.
  - Effort: 3-4h

- [x] **FE-M02 + FE-M05**: Expand feature flags system + automate SETORES sync
  - FE-M02: Adopt feature flags more broadly in new components from Sprint 3 decomposition
  - FE-M05: Automate the sector sync script (`scripts/sync-setores-fallback.js`) via CI/CD or pre-deploy hook
  - Files: `frontend/lib/config.ts`, `scripts/sync-setores-fallback.js`, `.github/workflows/` (CI config)
  - Validation: Feature flags control at least 3 features via environment variables. Sector sync runs automatically on deploy. No manual sync needed.
  - Effort: 3-4h

### Backend Improvements

- [x] **SYS-M02**: Fix token cache hash mechanism -- replace `hash()` with `hashlib.sha256()` for deterministic, collision-resistant caching
  - Files: `backend/auth.py` (line 45)
  - Validation: Token cache works correctly across Python process restarts. No hash collisions in test scenarios.
  - Effort: 2-3h

- [x] **SYS-M03**: Add max size limit to in-memory rate limiter
  - Implement LRU eviction or periodic cleanup when dict exceeds configurable max size (e.g., 10,000 entries)
  - Files: `backend/rate_limiter.py` (lines 84-89)
  - Validation: Memory usage bounded. After 10,000+ unique users, oldest entries are evicted. GC cleanup still runs for entries > 60s.
  - Effort: 2-3h

- [x] **SYS-M04**: Move plan capabilities from Python code to database
  - Load plan definitions from `plans` table instead of hardcoded dicts in `quota.py:62-95`
  - Cache in memory with TTL (e.g., 5 minutes)
  - Files: `backend/quota.py` (lines 62-95)
  - Validation: Adding a new plan requires only a database INSERT, not a code deployment. Existing plan lookups still work. Cache refreshes after TTL.
  - Effort: 4-6h

- [x] **SYS-M06**: Replace all `datetime.utcnow()` with `datetime.now(timezone.utc)` across codebase
  - Python 3.12 deprecation: `datetime.utcnow()` is deprecated
  - Files: Multiple backend files (search with grep for `utcnow()`)
  - Validation: No `utcnow()` calls remain in codebase. No deprecation warnings in Python 3.12 logs.
  - Effort: 2-3h

- [x] **SYS-M08**: Add API versioning prefix (`/v1/`) to all endpoints
  - Add `prefix="/v1"` to FastAPI router or create versioned router groups
  - Maintain backward compatibility: old URLs redirect or continue to work during transition
  - Files: `backend/main.py` (router setup), all frontend proxy routes
  - Validation: `/v1/buscar`, `/v1/health`, etc. all respond. Old paths either redirect (301) or still work (deprecation period).
  - Effort: 4-6h

- [x] **SYS-H03**: Establish tracked migration workflow in repository
  - Create `supabase/migrations/` as the canonical source for all schema changes
  - Document migration creation, testing, and application workflow
  - Ensure all migrations from 001 to current are tracked in git
  - Files: `supabase/migrations/` (verify all present), `docs/development/migration-workflow.md` (new)
  - Validation: New developer can follow the documented workflow to create and apply a migration. All production migrations are tracked in git.
  - Effort: 4-6h

- [x] **SYS-M05**: Review Google API credentials handling
  - Audit Google Sheets integration dependencies (4 packages)
  - Verify OAuth token storage mechanism is secure
  - Remove unused Google dependencies if integration is not active
  - Files: `backend/requirements.txt` (lines 29-33)
  - Validation: Google dependencies justified or removed. Token storage documented. No credential leaks.
  - Effort: 2-3h

### Data Retention

- [x] **DB-L02 + DB-L03**: Implement retention cleanup via pg_cron
  - DB-L02: Delete `monthly_quota` rows older than 24 months
  - DB-L03: Delete `stripe_webhook_events` rows older than 90 days (as documented in migration 010)
  - Schedule via pg_cron (Supabase supports this)
  - Files: `supabase/migrations/022_retention_cleanup.sql` (new)
  - Validation: Cron jobs visible in Supabase dashboard. Old test rows are cleaned up. Recent rows preserved.
  - Effort: 6-8h

### Remaining LOW Items (Cleanup Batch)

- [x] **DB-L01**: Add `updated_at` column to `plans` table
  - Files: migration SQL
  - Validation: Column exists, auto-updates on modification.
  - Effort: 0.5h

- [x] **DB-L04**: Drop redundant index `idx_user_oauth_tokens_provider`
  - Files: migration SQL
  - Validation: Index removed. `unique_user_provider` constraint still exists.
  - Effort: 0.25h

- [x] **NEW-DB-04**: Add index on `user_subscriptions.stripe_customer_id`
  - Files: migration SQL
  - Validation: Index exists. Queries by customer_id use index scan.
  - Effort: 0.5h

- [x] **NEW-DB-05**: Document `plan_id` FK ON DELETE behavior as intentional RESTRICT
  - Files: `supabase/docs/SCHEMA.md` or inline comment in migration
  - Validation: Documentation explains that RESTRICT is intentional (cannot delete plan with active subscriptions).
  - Effort: 0.25h

- [x] **SYS-L01**: Add OpenAPI schema validation in tests
  - Validate that backend OpenAPI schema matches frontend expectations
  - Files: `backend/tests/test_openapi_schema.py` (new)
  - Validation: Test compares generated OpenAPI schema against a snapshot. Schema drift detected automatically.
  - Effort: 4-6h

- [x] **SYS-L02**: Remove emoji from production logs
  - Files: `backend/pncp_client.py` (lines 525, 533)
  - Validation: No emoji characters in log output. Log aggregators display correctly.
  - Effort: 1h

- [x] **SYS-L03**: Replace inline CSS in layout.tsx with CSS custom properties
  - Files: `frontend/app/layout.tsx` (lines 62-77)
  - Validation: Theme initialization uses CSS variables exclusively. No inline `style` blocks.
  - Effort: 1-2h

- [x] **SYS-L04**: Add centralized request/response logging middleware
  - Log: method, path, status code, duration for every request
  - Files: `backend/middleware.py` (extend from SYS-M01 correlation IDs)
  - Validation: Every request produces exactly one log line with duration and status code.
  - Effort: 3-4h

- [x] **SYS-L06**: Add Redis health check to health endpoint
  - Files: `backend/routes/health.py` (or wherever health endpoint lives after decomposition)
  - Validation: `/health` response includes Redis connectivity status. Returns degraded status if Redis is down.
  - Effort: 2h

- [x] **FE-M04**: Extract `STOPWORDS_PT` from buscar/page.tsx to shared module
  - Files: `frontend/lib/constants/stopwords.ts` (new), `frontend/app/components/SearchForm.tsx` (from decomposition)
  - Validation: Single source of truth. No duplicate stopword lists.
  - Effort: 1-2h

- [x] **FE-M06 + FE-M07**: Delete stale files (`dashboard-old.tsx`, `landing-layout-backup.tsx`)
  - Files: `frontend/app/dashboard-old.tsx` (delete), `frontend/app/landing-layout-backup.tsx` (delete)
  - Validation: Files removed. No imports reference them.
  - Effort: 1h

- [x] **FE-M09**: Replace deprecated `performance.timing` with `performance.getEntriesByType('navigation')`
  - Files: `frontend/app/components/AnalyticsProvider.tsx` (line 53)
  - Validation: No deprecation warnings in browser console. Timing data still collected correctly.
  - Effort: 1h

- [x] **FE-L02**: Fix `useEffect` with serialized Set dependency (investigated — no issue found, Set properly managed)
  - Files: `frontend/app/(protected)/buscar/page.tsx` (line ~426, or in extracted hook)
  - Validation: Effect runs only when Set contents change, not on every render.
  - Effort: 1h

- [x] **FE-L04**: Delete unused barrel file `components/filters/index.ts`
  - Files: `frontend/components/filters/index.ts` (delete)
  - Validation: File removed. No imports reference it.
  - Effort: 0.5h

- [x] **FE-L05**: Add `robots.txt` and `sitemap.xml`
  - Files: `frontend/public/robots.txt` (new), `frontend/app/sitemap.ts` (new, Next.js convention)
  - Validation: `/robots.txt` serves valid robots file. `/sitemap.xml` lists all public pages.
  - Effort: 2-3h

- [x] **FE-L06**: Configure OpenGraph images for social sharing
  - Files: `frontend/app/layout.tsx` (metadata), `frontend/public/og-image.png` (new)
  - Validation: Sharing a SmartLic URL on social media shows preview image and description.
  - Effort: 2-3h

- [x] **FE-NEW-05**: Add breadcrumbs to protected pages
  - Files: `frontend/app/(protected)/layout.tsx` (extend shared app shell from Sprint 2)
  - Validation: Each protected page shows breadcrumb trail. User can navigate back via breadcrumbs.
  - Effort: 2-3h

- [x] **FE-NEW-08**: Cache sector list client-side (memory or localStorage with short TTL)
  - Files: `frontend/app/components/SearchForm.tsx` or `frontend/hooks/useSearch.ts`
  - Validation: Navigating away from `/buscar` and back does not re-fetch sector list. Cache expires after TTL (e.g., 5 minutes).
  - Effort: 1-2h

- [x] **FE-NEW-09**: Add `/mensagens` and `/planos/obrigado` to middleware PROTECTED_ROUTES list
  - Files: `frontend/middleware.ts` (lines 15-21)
  - Validation: Unauthenticated access to `/mensagens` and `/planos/obrigado` redirects to login. No flash of protected content.
  - Effort: 0.5h

---

## Technical Notes

### Plan Data Architecture (CROSS-M01)

After this change, the data flow for plan information should be:

```
Database (plans table) -- single source of truth
  |
  ├── Backend: quota.py reads capabilities from DB (cached 5min)
  ├── Backend: /api/plans endpoint serves plan details
  └── Frontend: reads /api/plans for display (pricing, upgrade pages)
```

No plan prices or capability definitions should remain hardcoded in any code file.

### API Versioning Strategy (SYS-M08)

Recommended approach:
1. Add `/v1` prefix to all routers
2. Create redirect middleware: requests to old paths (e.g., `/buscar`) redirect to `/v1/buscar` with 301
3. Update all frontend proxy routes to use `/v1/` prefix
4. Document deprecation timeline for unversioned paths (e.g., remove after 3 months)

### pg_cron Retention (DB-L02 + DB-L03)

```sql
-- Example pg_cron job for monthly_quota cleanup
SELECT cron.schedule(
  'cleanup-monthly-quota',
  '0 3 1 * *',  -- 3 AM on 1st of each month
  $$DELETE FROM monthly_quota WHERE period < (now() - interval '24 months')::date$$
);

-- Example for stripe_webhook_events cleanup
SELECT cron.schedule(
  'cleanup-webhook-events',
  '0 4 * * 0',  -- 4 AM every Sunday
  $$DELETE FROM stripe_webhook_events WHERE created_at < now() - interval '90 days'$$
);
```

---

## Testing Requirements

- All tests must continue to pass (0 failures from Sprint 2/3)
- Frontend test coverage must remain >= 60%
- `npx tsc --noEmit --pretty` must pass
- New tests for: plan data endpoint, API versioning redirects, OpenAPI schema validation
- Verify pg_cron jobs execute correctly on test data

---

## Rollback Plan

All items in Sprint 4 are independent and low-risk. Each can be reverted individually via git:
- Database migrations: inverse SQL for each change
- Frontend changes: individual file reverts
- Backend changes: individual file reverts
- Deleted files: restore from git history

No item in Sprint 4 has cascading dependencies that would require coordinated rollback.

---

## Definition of Done

- [ ] All acceptance criteria checked (or explicitly deferred with documented justification)
- [ ] Tests pass (pytest + npm test) with 0 failures
- [ ] Frontend test coverage >= 60%
- [ ] TypeScript check clean (`npx tsc --noEmit`)
- [ ] No new lint errors
- [ ] No `datetime.utcnow()` calls in codebase
- [ ] No hardcoded plan prices in frontend
- [ ] No stale/dead files remain
- [ ] PR reviewed and approved
- [ ] Deployed to staging
- [ ] All 90 items from technical debt assessment resolved or explicitly deferred

---

## File List

**New files:**
- `frontend/lib/constants/uf-names.ts`
- `frontend/lib/constants/stopwords.ts`
- `frontend/public/robots.txt`
- `frontend/app/sitemap.ts`
- `frontend/public/og-image.png`
- `backend/routes/plans.py`
- `backend/tests/test_openapi_schema.py`
- `docs/development/migration-workflow.md`
- `supabase/migrations/020_tighten_plan_type_constraint.sql`
- `supabase/migrations/021_user_subscriptions_updated_at.sql`
- `supabase/migrations/022_retention_cleanup.sql`

**Modified files:**
- `backend/auth.py` (line 45)
- `backend/rate_limiter.py` (lines 84-89)
- `backend/quota.py` (lines 62-95)
- `backend/main.py` (router versioning)
- `backend/pncp_client.py` (lines 525, 533 -- emoji removal)
- `backend/requirements.txt` (Google dependencies audit)
- `backend/routes/health.py` (Redis health check)
- `backend/middleware.py` (request logging)
- `frontend/app/(protected)/layout.tsx` (breadcrumbs, page transitions)
- `frontend/app/(protected)/buscar/page.tsx` (or extracted hooks -- useEffect fix, stopwords extraction)
- `frontend/app/components/SearchForm.tsx` (sector caching, feature flags)
- `frontend/app/components/AnalyticsProvider.tsx` (line 53)
- `frontend/app/layout.tsx` (lines 62-77 -- inline CSS, OpenGraph)
- `frontend/app/pricing/page.tsx` (read from API)
- `frontend/app/planos/page.tsx` (read from API)
- `frontend/lib/plans.ts` (read from API)
- `frontend/lib/config.ts` (expanded feature flags)
- `frontend/middleware.ts` (lines 15-21 -- add routes)
- `frontend/app/(public)/login/page.tsx` (zod + react-hook-form)
- `frontend/app/(public)/cadastro/page.tsx` (zod + react-hook-form)
- `frontend/app/(protected)/conta/page.tsx` (zod + react-hook-form)
- `scripts/sync-setores-fallback.js` (CI automation)
- `.github/workflows/` (sector sync + migration workflow)
- `supabase/docs/SCHEMA.md` (FK documentation)
- Multiple backend files (datetime.utcnow replacement)

**Deleted files:**
- `frontend/app/dashboard-old.tsx`
- `frontend/app/landing-layout-backup.tsx`
- `frontend/components/filters/index.ts`
