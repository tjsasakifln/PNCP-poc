# STORY-201: Architecture Unification

**Status:** Backlog
**Sprint:** 2 (Weeks 2-3)
**Priority:** P1 -- Core Architecture
**Effort:** 48-72h
**Epic:** EPIC-TD (Technical Debt Resolution)
**Dependencies:** STORY-200 (security fixes must be deployed first; DB-C02 and DB-H04 RLS changes are prerequisites for ORM consolidation)

---

## Context

SmartLic/BidIQ has grown organically from a POC to a production SaaS, resulting in fundamental architectural inconsistencies that create active correctness risks:

1. **Dual ORM (most dangerous debt):** Two complete Stripe subscription lifecycle implementations coexist -- `main.py` uses Supabase client and syncs `profiles.plan_type`, while `webhooks/stripe.py` uses SQLAlchemy and does NOT sync `plan_type`. The SQLAlchemy engine URL is constructed incorrectly from `SUPABASE_URL` (HTTPS), so the SQLAlchemy path likely fails silently. Depending on which code path handles a Stripe event, `plan_type` may or may not be updated, causing unpredictable plan drift.

2. **Mixed API patterns:** Frontend pages inconsistently call the backend -- some use Next.js proxy routes (`/api/*`), others call `NEXT_PUBLIC_BACKEND_URL` directly from the browser. This exposes the backend URL to clients and creates two different auth forwarding patterns.

3. **No shared app shell:** Each protected page manages its own header independently. The app feels like separate applications stitched together. buscar has full header with PlanBadge, QuotaBadge, MessageBadge, ThemeToggle, UserMenu; other pages have minimal or no header.

4. **91 pre-existing test failures:** Backend: 21 failures (billing, stripe, feature flags, prorata). Frontend: 70 failures. CI pipeline is not green, masking new regressions.

This sprint resolves the most impactful systemic debts and restores the CI pipeline.

---

## Acceptance Criteria

### ORM Consolidation (Highest Risk, Highest Impact)

- [ ] **CROSS-C01 + DB-C01 + DB-H01 + NEW-DB-01**: Consolidate to single ORM (Supabase client only)
  - Rewrite `webhooks/stripe.py` handlers to use Supabase client instead of SQLAlchemy
  - Ensure ALL Stripe webhook handlers sync `profiles.plan_type` (matching main.py behavior)
  - Verify `_activate_plan()`, `_deactivate_stripe_subscription()`, `_handle_subscription_updated()` in main.py are the canonical implementations
  - Delete or deprecate `backend/database.py` (keep as dead code for 2-week rollback window)
  - Delete or deprecate `backend/models/` directory (keep as dead code for 2-week rollback window)
  - Remove SQLAlchemy from `requirements.txt` (after 2-week rollback window)
  - Files: `backend/webhooks/stripe.py`, `backend/database.py`, `backend/models/`, `backend/main.py` (lines 733-900), `backend/supabase_client.py`
  - Validation: All Stripe webhook events processed correctly. `profiles.plan_type` synced after every subscription event. No imports of `database.py` or `models/` in active code paths. Stripe Dashboard shows successful webhook delivery for all event types.
  - Effort: 10-14h

### API Pattern Unification

- [ ] **FE-C03 + CROSS-H01**: Migrate all direct backend calls to proxy `/api/*` routes
  - Create proxy routes for: `historico`, `conta`, `admin`, `mensagens`
  - Remove all `NEXT_PUBLIC_BACKEND_URL` direct calls from browser-side code
  - Standardize auth forwarding pattern (cookie-based via proxy, not direct token passing)
  - Remove `NEXT_PUBLIC_BACKEND_URL` from environment if no longer needed client-side
  - Files: `frontend/app/historico/page.tsx`, `frontend/app/conta/page.tsx`, `frontend/app/admin/page.tsx`, `frontend/app/mensagens/` (if exists), new `frontend/app/api/` route files
  - Validation: No `NEXT_PUBLIC_BACKEND_URL` references in any `page.tsx` or client component. All API calls go through `/api/*` proxy. Network tab in browser shows no direct backend URL calls. Error handling is consistent across all pages.
  - Effort: 8-12h

### Shared App Shell

- [ ] **FE-M01**: Implement shared app shell for all protected pages
  - Create `(protected)/layout.tsx` route group with consistent AppHeader
  - AppHeader includes: PlanBadge, QuotaBadge, MessageBadge, ThemeToggle, UserMenu (matching current buscar page header)
  - Add persistent sidebar or navigation breadcrumbs
  - Ensure all protected pages (`buscar`, `historico`, `conta`, `admin`, `dashboard`, `mensagens`, `planos`) use the shared layout
  - Files: `frontend/app/(protected)/layout.tsx` (new), all protected page files (move into route group)
  - Validation: Navigate between all protected pages -- header is consistent. No page manages its own header independently. Navigation context is always visible.
  - Effort: 6-8h

### Component Consolidation

- [ ] **FE-H01**: Consolidate duplicate filter components
  - Delete fragile `components/EsferaFilter.tsx` and `components/MunicipioFilter.tsx` (div-based with manual keyboard handling)
  - Keep `app/components/EsferaFilter.tsx` and `app/components/MunicipioFilter.tsx` (native button, correct ARIA)
  - Update all imports to reference the canonical versions
  - Files: `frontend/components/EsferaFilter.tsx` (delete), `frontend/components/MunicipioFilter.tsx` (delete), `frontend/app/components/EsferaFilter.tsx` (keep), `frontend/app/components/MunicipioFilter.tsx` (keep)
  - Validation: No duplicate component files. All filter imports resolve to `app/components/` versions. Keyboard navigation still works on filters.
  - Effort: 3-4h

- [ ] **FE-H02**: Replace direct DOM manipulation with sonner toast for search state restoration
  - Remove `document.createElement` usage at lines ~285-293 in buscar/page.tsx
  - Replace with sonner toast notification (matching the rest of the app)
  - Add `role="status"` or `aria-live="polite"` for screen reader announcement
  - Respect `prefers-reduced-motion` for any animation
  - Files: `frontend/app/buscar/page.tsx` (lines ~285-293)
  - Validation: Search state restoration shows toast notification instead of injected DOM element. Screen readers announce the restoration. No `document.createElement` calls remain in buscar/page.tsx.
  - Effort: 2-3h

### CI Pipeline Restoration

- [ ] **SYS-C04 + CROSS-M02**: Fix or triage all pre-existing test failures to restore green CI
  - Backend: Fix 21 pre-existing failures (billing, stripe, feature flags, prorata tests)
  - Frontend: Fix 70 pre-existing failures
  - For each failure: fix, update test expectation, or mark as `skip` with documented reason and follow-up ticket
  - Files: `backend/tests/` (multiple), `frontend/__tests__/` (multiple)
  - Validation: `pytest` exits with 0 failures (all pass or explicitly skipped with reason). `npm test` exits with 0 failures. CI pipeline is green on main branch.
  - Effort: 8-16h

### Backend Architecture

- [ ] **SYS-H01**: Remove or refactor synchronous PNCPClient
  - Remove the synchronous `requests`-based fallback in `PNCPClient` (lines 67-557)
  - Ensure only `AsyncPNCPClient` is used in all code paths
  - If synchronous client is needed for scripts/CLI, isolate it with clear documentation
  - Files: `backend/pncp_client.py` (lines 67-557)
  - Validation: No `import requests` in pncp_client.py (or only in clearly marked sync utility). All endpoint handlers use `AsyncPNCPClient`. Event loop is never blocked by synchronous HTTP calls.
  - Effort: 4-6h

### Testing Infrastructure

- [ ] **TEST-03**: Create PNCP API resilience test plan and mock fixtures
  - Document testing approach for: rate limiting (429 responses), exponential backoff, circuit breaker, timeout handling
  - Create reusable mock fixtures for PNCP API responses (success, 429, 500, timeout, malformed JSON)
  - Implement at least 5 resilience test cases using the new fixtures
  - Files: `backend/tests/fixtures/pncp_responses/` (new directory), `backend/tests/test_pncp_resilience.py` (new or extend existing), `docs/testing/pncp-resilience-test-plan.md` (new)
  - Validation: Resilience tests pass. Fixtures cover all documented PNCP failure modes. Test plan document exists and is comprehensive.
  - Effort: 4-6h

---

## Technical Notes

### ORM Consolidation Strategy

This is the highest-risk change in the entire epic. Follow this sequence:

1. **Audit:** Map every Stripe webhook event type to its handler in both `main.py` and `webhooks/stripe.py`. Document which fields each handler reads/writes.
2. **Implement:** Rewrite `webhooks/stripe.py` handlers to use `supabase_client`. Ensure every handler that modifies subscription state also calls the equivalent of `_sync_profile_plan_type()`.
3. **Test:** Process test Stripe webhook events through the new handlers. Verify `profiles.plan_type` is correct after each event type.
4. **Deploy:** Ship with `database.py` and `models/` still present but unused (dead code). Monitor Stripe webhook delivery for 2 weeks.
5. **Cleanup:** After 2 weeks with zero issues, delete `database.py`, `models/`, and remove SQLAlchemy from requirements.

**Rollback:** If webhook processing fails post-deploy, re-enable the old import path. The old code remains in the repo as dead code.

### API Unification Pattern

For each page that currently calls `NEXT_PUBLIC_BACKEND_URL` directly:

```typescript
// NEW: frontend/app/api/{feature}/route.ts
export async function GET(request: NextRequest) {
  const supabase = createRouteHandlerClient({ cookies });
  const { data: { session } } = await supabase.auth.getSession();

  const response = await fetch(`${BACKEND_URL}/{endpoint}`, {
    headers: {
      'Authorization': `Bearer ${session?.access_token}`,
      'Content-Type': 'application/json',
    },
  });

  return NextResponse.json(await response.json());
}
```

### Shared App Shell Architecture

```
frontend/app/
  (protected)/
    layout.tsx        # <-- NEW: AppHeader + sidebar/nav
    buscar/
      page.tsx        # <-- MOVED from app/buscar/
    historico/
      page.tsx
    conta/
      page.tsx
    admin/
      page.tsx
    dashboard/
      page.tsx
    mensagens/
      page.tsx
    planos/
      page.tsx
  (public)/
    page.tsx          # Landing page
    pricing/
      page.tsx
    login/
      page.tsx
    cadastro/
      page.tsx
```

### Pre-existing Test Failure Triage

For each failing test, apply one of:
1. **Fix:** Update test or code to make it pass (preferred)
2. **Update expectation:** If behavior intentionally changed, update the test assertion
3. **Skip with reason:** `@pytest.mark.skip(reason="STORY-201: requires Stripe test mode setup")` or Jest equivalent. Must include a story/ticket reference for follow-up.

Do NOT delete tests.

---

## Testing Requirements

- `pytest` must exit with 0 failures after this sprint (all pass or explicitly skipped)
- `npm test` must exit with 0 failures after this sprint
- `npx tsc --noEmit --pretty` must pass
- Stripe webhook processing must be tested with Stripe CLI test mode: `stripe trigger customer.subscription.updated`
- All new proxy API routes must have at least one integration test
- Playwright E2E tests must still pass: `npm run test:e2e`

---

## Rollback Plan

- **ORM consolidation:** Keep `database.py` and `models/` as dead code for 2 weeks. Monitor Stripe Dashboard for webhook delivery failures. Re-enable old import path if issues arise.
- **API unification:** Revert by restoring `NEXT_PUBLIC_BACKEND_URL` direct calls. Proxy routes can coexist with direct calls temporarily.
- **Shared app shell:** Revert route group by moving pages back to original locations. Layout changes are isolated.
- **Test fixes:** Individual test fixes can be reverted per-file via git.

---

## Definition of Done

- [ ] All acceptance criteria checked
- [ ] Tests pass: `pytest` with 0 failures, `npm test` with 0 failures
- [ ] TypeScript check clean (`npx tsc --noEmit`)
- [ ] No new lint errors
- [ ] CI pipeline green on feature branch
- [ ] Stripe webhook delivery verified in Stripe Dashboard
- [ ] No `NEXT_PUBLIC_BACKEND_URL` in browser-side code
- [ ] Shared app shell visible on all protected pages
- [ ] PR reviewed and approved
- [ ] Deployed to staging
- [ ] 2-week monitoring window for ORM consolidation begins

---

## File List

**New files:**
- `frontend/app/(protected)/layout.tsx`
- `frontend/app/api/historico/route.ts`
- `frontend/app/api/conta/route.ts`
- `frontend/app/api/admin/[...path]/route.ts` (or similar catch-all)
- `frontend/app/api/mensagens/route.ts`
- `backend/tests/fixtures/pncp_responses/` (directory with mock fixtures)
- `backend/tests/test_pncp_resilience.py`
- `docs/testing/pncp-resilience-test-plan.md`

**Modified files:**
- `backend/webhooks/stripe.py` (rewrite to Supabase client)
- `backend/main.py` (lines 733-900, ensure canonical handlers)
- `backend/database.py` (mark as deprecated, keep for rollback)
- `backend/models/` (mark as deprecated, keep for rollback)
- `backend/pncp_client.py` (remove sync client or isolate)
- `backend/requirements.txt` (note SQLAlchemy for future removal)
- `frontend/app/historico/page.tsx` (remove direct backend calls)
- `frontend/app/conta/page.tsx` (remove direct backend calls)
- `frontend/app/admin/page.tsx` (remove direct backend calls)
- `frontend/app/buscar/page.tsx` (lines ~285-293, remove DOM manipulation; move to route group)
- `frontend/components/EsferaFilter.tsx` (delete)
- `frontend/components/MunicipioFilter.tsx` (delete)
- `backend/tests/` (multiple test files fixed)
- `frontend/__tests__/` (multiple test files fixed)

**Deleted files (after 2-week rollback window):**
- `backend/database.py`
- `backend/models/*.py`
- `frontend/components/EsferaFilter.tsx`
- `frontend/components/MunicipioFilter.tsx`
