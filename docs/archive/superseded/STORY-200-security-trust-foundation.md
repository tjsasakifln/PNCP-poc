# STORY-200: Security and Trust Foundation

**Status:** Backlog
**Sprint:** 1 (Week 1)
**Priority:** P0 -- Immediate
**Effort:** 20-28h
**Epic:** EPIC-TD (Technical Debt Resolution)
**Dependencies:** None (this is the foundation sprint)

---

## Context

SmartLic/BidIQ is a production SaaS with live users and Stripe billing. The brownfield discovery (commit `808cd05`) identified several security and trust issues that must be resolved before any architectural work begins:

1. **Direct access control bug:** The admin policy on `stripe_webhook_events` checks `plan_type = 'master'` instead of `is_admin = true`. These are independent columns -- a non-admin master user can view webhook events, while an admin with a different plan_type cannot.
2. **Overly permissive RLS:** Two tables use `FOR ALL USING (true)` without `TO service_role`, allowing any authenticated user to perform any operation via PostgREST.
3. **Price divergence:** Users see R$149/349/997 on the pricing page but R$297/597/1497 on the upgrade page. This directly undermines user trust.
4. **Broken error page:** The error boundary uses hardcoded colors, producing a completely white background in dark mode.
5. **Missing indexes:** Sequential scans on `stripe_subscription_id` and `profiles.email` for admin searches.
6. **Native alert():** Two call sites use `window.alert()` instead of the app's sonner toast system.
7. **Dev dependencies in production:** pytest, ruff, mypy installed in production requirements.txt.

All items in this sprint are low-risk, targeted fixes. Most are single-file changes.

---

## Acceptance Criteria

### Database Security (Items 1-6: combine in single migration `016_security_and_index_fixes.sql`)

- [ ] **DB-C03**: Fix `stripe_webhook_events` admin policy -- change `plan_type = 'master'` to `is_admin = true`
  - Files: `supabase/migrations/016_security_and_index_fixes.sql` (new)
  - Validation: Query `stripe_webhook_events` as admin user with `plan_type != 'master'` succeeds; query as non-admin master user fails
  - Effort: 0.5h

- [ ] **DB-H04**: Tighten RLS on `monthly_quota` and `search_sessions` -- add `TO service_role` to `FOR ALL USING (true)` policies
  - Files: `supabase/migrations/016_security_and_index_fixes.sql`
  - Validation: Authenticated user (non-service-role) cannot directly INSERT/UPDATE/DELETE on these tables via PostgREST. Service role operations still work.
  - Effort: 1h

- [ ] **DB-H03**: Add unique index on `user_subscriptions.stripe_subscription_id`
  - Files: `supabase/migrations/016_security_and_index_fixes.sql`
  - Validation: `EXPLAIN` on query by `stripe_subscription_id` shows index scan, not sequential scan. Duplicate subscription IDs rejected.
  - Effort: 0.5h

- [ ] **NEW-DB-03**: Add trigram index on `profiles.email` for admin ILIKE search
  - Files: `supabase/migrations/016_security_and_index_fixes.sql`
  - Validation: `EXPLAIN ANALYZE` on `SELECT * FROM profiles WHERE email ILIKE '%test%'` shows index scan. Requires `pg_trgm` extension (enable in migration if not already).
  - Effort: 1h

- [ ] **DB-C02**: Add service role RLS write policy on `user_subscriptions`
  - Files: `supabase/migrations/016_security_and_index_fixes.sql`
  - Validation: Consistent with `monthly_quota` and `search_sessions` patterns from migrations 013/014. Backend subscription operations still work.
  - Effort: 1h

- [ ] **NEW-DB-02**: Fix `handle_new_user()` trigger default -- change `plan_type = 'free'` to `plan_type = 'free_trial'`
  - Files: `supabase/migrations/016_security_and_index_fixes.sql`
  - Validation: Create a new user and verify `profiles.plan_type = 'free_trial'` (not `'free'`). Existing users unaffected.
  - Effort: 0.5h

### Frontend Trust and UX

- [ ] **FE-L03**: Fix divergent plan prices between pages -- reconcile `pricing/page.tsx`, `lib/plans.ts`, and `planos/page.tsx` to show consistent prices
  - Files: `frontend/app/pricing/page.tsx`, `frontend/lib/plans.ts`, `frontend/app/planos/page.tsx`
  - Validation: All three files show identical prices. Verify visually on both pages. Confirm with product owner which prices are correct.
  - Note: Must confirm with PO whether R$149/349/997 or R$297/597/1497 is the canonical set before implementing.
  - Effort: 2h

- [ ] **FE-H04**: Replace `window.alert()` with sonner toast at lines 1080 and 1087 in buscar/page.tsx
  - Files: `frontend/app/buscar/page.tsx` (lines ~1080, ~1087)
  - Validation: Save search success/error shows sonner toast notification, not a blocking alert dialog. No `window.alert` calls remain in codebase.
  - Effort: 1h

- [ ] **FE-H03 + FE-NEW-01**: Fix error boundary -- replace hardcoded Tailwind colors with design system tokens; fix contradictory ARIA (`role="img" aria-label` + `aria-hidden="true"`) on SVG
  - Files: `frontend/app/error.tsx`
  - Validation: Error page renders correctly in both light and dark mode. SVG uses either `aria-hidden="true"` (decorative) OR `role="img" aria-label="..."` (meaningful), not both. Colors use CSS custom properties or design tokens.
  - Effort: 1.5-2.5h

- [ ] **FE-NEW-02**: Add `aria-expanded` attribute to advanced filters toggle button
  - Files: `frontend/app/buscar/page.tsx` (lines ~1627-1639)
  - Validation: Screen reader announces expanded/collapsed state when toggling "Filtros Avancados". `aria-expanded` value matches panel visibility.
  - Effort: 0.5h

- [ ] **FE-C02**: Remove `http://localhost:8000` fallback in analytics API route
  - Files: `frontend/app/api/analytics/route.ts` (line 4)
  - Validation: If `BACKEND_URL` is not set, the route returns a proper error instead of attempting localhost connection. No localhost strings remain in production API routes.
  - Effort: 1h

### Backend Cleanup

- [ ] **SYS-H05**: Split `requirements.txt` into `requirements.txt` (production) and `requirements-dev.txt` (development)
  - Files: `backend/requirements.txt`, `backend/requirements-dev.txt` (new)
  - Validation: Production requirements do not include pytest, ruff, mypy, locust, faker. Dev requirements include all tools. `pip install -r requirements.txt` succeeds for production. `pip install -r requirements-dev.txt` installs dev tools.
  - Effort: 2-3h

- [ ] **DB-H02**: Consolidate migration 006 duplicates -- keep one canonical `006_search_sessions_service_role_policy.sql`, remove/rename the other two files with clear comments
  - Files: `supabase/migrations/006_*` (three files)
  - Validation: Only one `006_` migration file remains (or files renamed to prevent confusion). Document which was applied to production.
  - Effort: 1-2h

- [ ] **SYS-L05**: Clean unused imports in main.py (line ~1694: `from filter import match_keywords, KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO` inside diagnostic loop)
  - Files: `backend/main.py` (line ~1694)
  - Validation: No unused imports. `ruff check backend/main.py` shows no import warnings for these.
  - Effort: 0.5h

---

## Technical Notes

### Migration Strategy

Items DB-C03, DB-H04, DB-H03, NEW-DB-03, DB-C02, and NEW-DB-02 should be combined into a single migration file `016_security_and_index_fixes.sql`. This is atomic -- if any statement fails, the entire migration rolls back.

The migration should:
1. `ALTER POLICY` for `stripe_webhook_events` (DB-C03)
2. `DROP POLICY` + `CREATE POLICY` with `TO service_role` for `monthly_quota` and `search_sessions` (DB-H04)
3. `CREATE UNIQUE INDEX` on `user_subscriptions(stripe_subscription_id)` (DB-H03)
4. `CREATE EXTENSION IF NOT EXISTS pg_trgm` + `CREATE INDEX` using `gin_trgm_ops` on `profiles(email)` (NEW-DB-03)
5. `CREATE POLICY` for service role writes on `user_subscriptions` (DB-C02)
6. `ALTER FUNCTION handle_new_user()` or update the trigger function to set `plan_type = 'free_trial'` instead of `'free'` (NEW-DB-02)

### Price Reconciliation

FE-L03 requires product owner confirmation on canonical prices before implementation. The developer should:
1. Document both price sets found
2. Get explicit PO sign-off on which is correct
3. Update all three files to match
4. Consider whether prices should come from the backend `plans` table (deferred to CROSS-M01 in Sprint 4)

### Requirements Split

SYS-H05: Review current `requirements.txt` lines 37-50 for dev-only packages. Common candidates: `pytest`, `pytest-cov`, `pytest-asyncio`, `ruff`, `mypy`, `locust`, `faker`, `httpx[test]`. Update Dockerfile/Railway build command if it references `requirements.txt`.

---

## Testing Requirements

- All existing backend tests must still pass: `pytest` (baseline: 21 known failures, do not increase)
- All existing frontend tests must still pass: `npm test` (baseline: 70 known failures, do not increase)
- TypeScript check must pass: `npx tsc --noEmit --pretty`
- Migration must be tested on a staging/local Supabase instance before production
- Manual verification: dark mode error page, toast notifications, admin panel search performance

---

## Rollback Plan

- **Database migration:** Each statement in migration 016 can be individually reverted with a `017_rollback_security_fixes.sql` if needed. Keep the rollback SQL prepared but do not apply unless issues arise.
- **Frontend changes:** All changes are to individual files. Git revert on specific commits.
- **requirements.txt split:** Revert by restoring original single file and updating Dockerfile.

---

## Definition of Done

- [ ] All acceptance criteria checked
- [ ] Tests pass (pytest + npm test) -- no new failures beyond baseline
- [ ] TypeScript check clean (`npx tsc --noEmit`)
- [ ] No new lint errors
- [ ] Migration applied to staging and verified
- [ ] PR reviewed and approved
- [ ] Deployed to staging
- [ ] Dark mode error page verified visually
- [ ] Admin panel search performance verified (no full table scan)

---

## File List

**New files:**
- `supabase/migrations/016_security_and_index_fixes.sql`
- `backend/requirements-dev.txt`

**Modified files:**
- `frontend/app/error.tsx`
- `frontend/app/buscar/page.tsx` (lines ~1080, ~1087, ~1627-1639)
- `frontend/app/api/analytics/route.ts` (line 4)
- `frontend/app/pricing/page.tsx`
- `frontend/lib/plans.ts`
- `frontend/app/planos/page.tsx`
- `backend/requirements.txt`
- `backend/main.py` (line ~1694)
- `supabase/migrations/006_*` (consolidation/cleanup)
