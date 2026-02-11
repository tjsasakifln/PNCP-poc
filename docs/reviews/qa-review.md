# QA Review - Technical Debt Assessment

**Reviewer:** @qa (Quinn)
**Date:** 2026-02-11
**Documents Reviewed:** DRAFT (`docs/prd/technical-debt-DRAFT.md`, 72 items) + DB specialist review (`docs/reviews/db-specialist-review.md`, 22 items) + UX specialist review (`docs/reviews/ux-specialist-review.md`, 33 items)
**Codebase Commit:** `808cd05` (branch `main`)
**Verification Method:** Direct codebase inspection, test execution, CI workflow review

---

## Gate Status: APPROVED WITH CONDITIONS

The assessment is thorough enough to proceed to final consolidation, provided the conditions listed in Section 7 are addressed during consolidation. The DRAFT plus specialist reviews cover all major technical debt areas comprehensively. No critical blind spots remain after incorporating this QA review.

---

## 1. Gaps Identified

### 1.1 Gaps Not Covered by Any Document

| Gap ID | Area | Description | Suggested Severity |
|--------|------|-------------|-------------------|
| GAP-01 | **CI/CD Pipeline Health** | The DRAFT states "21 backend failures + 70 frontend failures" (SYS-C04), but current test execution shows **0 backend failures** (all 1631 tests pass, verified locally) and only **38 frontend failures** (down from 70). The STORY-185 commit (`10c6a6a`) fixed many of these. The assessment references stale data. This matters because effort estimates for SYS-C04 are based on outdated failure counts. | N/A (data correction) |
| GAP-02 | **Stripe Webhook Reliability in Production** | The DB specialist identified that SQLAlchemy handlers are likely broken (DB-C01 Q1 answer), meaning Stripe lifecycle events (cancellations, payment failures, subscription updates) may not be recording. **No document assesses the actual production impact.** Are there users who cancelled via Stripe dashboard but still show as active? Is there a backlog of unprocessed webhook events? This is not just tech debt -- it is a potential billing integrity issue affecting revenue. | CRITICAL |
| GAP-03 | **Secret Management** | No document addresses how secrets are managed. `.env` files are referenced, Railway env vars are mentioned, but there is no assessment of: (a) whether secrets are rotated, (b) whether the Supabase service_role key is the same across environments, (c) whether Stripe test vs production keys are properly segregated. Given the hardcoded Stripe price IDs in migrations (DB-M05), the risk of cross-environment contamination is real. | MEDIUM |
| GAP-04 | **Backup and Disaster Recovery** | No document mentions database backup strategy, point-in-time recovery capability, or rollback procedures for Supabase. Given this is a production SaaS processing payments, the absence of documented backup/recovery is a risk. | MEDIUM |
| GAP-05 | **Dependency Vulnerability Scanning** | `requirements.txt` has ~50 dependencies. `package.json` has ~40. No document mentions `pip audit`, `npm audit`, Dependabot findings, or Snyk integration. The CodeQL workflow exists (`.github/workflows/codeql.yml`) but covers only static analysis, not dependency vulnerabilities. | MEDIUM |
| GAP-06 | **Rate Limiting for Authentication Endpoints** | The backend has rate limiting for search (`rate_limiter.py`) but no document assesses whether login/signup endpoints are rate-limited. Brute-force protection for authentication is a basic security requirement for a SaaS. | HIGH |
| GAP-07 | **Monitoring and Alerting** | No document mentions production monitoring, error tracking (Sentry, etc.), or alerting. The `SYS-M01` (no correlation IDs) and `SYS-L04` (no request logging middleware) debts are listed, but the broader question of "how do we know when production breaks" is unanswered. | MEDIUM |
| GAP-08 | **Frontend Bundle Size Analysis** | UX review mentions framer-motion (40KB) but no document provides actual bundle analysis data. With `next build`, the output includes chunk sizes. This data would validate or invalidate several FE performance debts. | LOW |
| GAP-09 | **E2E Test Gap for Billing Flows** | Verified: the 12 E2E spec files cover search, theme, saved-searches, empty-state, error-handling, admin, auth, performance, plan-display, signup, institutional, and landing. There is ZERO coverage of: Stripe checkout initiation, payment success callback, subscription management (upgrade/downgrade/cancel), and webhook-driven plan changes. See Q4 answer below for details. | HIGH |
| GAP-10 | **Locust Load Tests Not Integrated** | `locustfile.py` exists and is well-written. `.github/workflows/load-test.yml` exists. But there is no mention in the DRAFT of whether load tests have ever been run or what the baseline performance metrics are. | LOW |

### 1.2 Data Corrections for Final Consolidation

| Item | DRAFT States | Actual (verified 2026-02-11) | Impact |
|------|-------------|------------------------------|--------|
| SYS-C04 | 21 backend + 70 frontend failures | **0 backend + 38 frontend failures** | Effort estimate for SYS-C04 drops from 8-16h to 4-8h |
| FE-L07 | Coverage ~49.46%, 70 failures | **38 failures in 6 test suites** | More targeted fix needed |
| Backend test count | "82 tests" (from CLAUDE.md) | **1631 tests collected** | CLAUDE.md outdated |
| FE-M08 | "No middleware auth guards" | **Middleware EXISTS** (UX review correctly identified this) | Remove from DRAFT |
| Frontend test count | Not specified | **1072 total (1026 pass, 38 fail, 8 skip)** | 96.5% pass rate, not catastrophic |

---

## 2. Cross-Area Risks

| Risk ID | Risk | Areas Affected | Probability | Impact | Mitigation |
|---------|------|----------------|-------------|--------|------------|
| RISK-01 | **ORM consolidation causes payment processing interruption** | Database, Backend, Billing | HIGH | CRITICAL | The dual Stripe handler issue (NEW-DB-01) means consolidating to Supabase client requires rewriting webhook handlers. If the new handlers have bugs, real payments could be missed. Mitigation: deploy to staging with Stripe test mode first; verify webhook delivery in Stripe Dashboard for 48h before production cutover; maintain old code as dead code for 2 weeks (as DB specialist recommends). |
| RISK-02 | **Frontend monolith decomposition introduces visual regressions** | Frontend, UX | MEDIUM | HIGH | Decomposing `buscar/page.tsx` (1100 lines, 30+ hooks) is the highest-risk frontend change. State coordination between extracted hooks is error-prone. Mitigation: take Playwright visual regression screenshots before decomposition; run full E2E suite after each extraction step; do NOT combine with any feature work. |
| RISK-03 | **RLS policy changes lock out legitimate operations** | Database, Backend | LOW | CRITICAL | Tightening RLS policies (DB-H04) could block operations that currently work by accident. The `monthly_quota` and `search_sessions` policies with `USING (true)` mean any authenticated user can modify these -- if backend code relies on this (even inadvertently), tightening to `TO service_role` would break it. Mitigation: audit every Supabase client call that touches these tables; ensure all use the service_role key, not the anon key. |
| RISK-04 | **Migration 006 cleanup causes schema inconsistency** | Database | LOW | HIGH | Three `006_*` files create ambiguity. If the consolidation removes a migration that was never applied, the policy may not exist. If it removes one that WAS applied, Supabase migration tracking breaks. Mitigation: verify production state FIRST with `SELECT * FROM pg_policies WHERE tablename = 'search_sessions'` before any file changes. |
| RISK-05 | **Price reconciliation (FE-L03) reveals business decision not yet made** | Frontend, Product | HIGH | MEDIUM | The divergent prices (149/349/997 vs 297/597/1497) may be intentional (promotional vs list price) but undocumented. "Fixing" this by standardizing to one set could be wrong if the other set is what the business intended. Mitigation: require explicit product owner sign-off on canonical prices before any code change. |
| RISK-06 | **Test suite stabilization masks new regressions during debt resolution** | All areas | MEDIUM | HIGH | As tests are fixed/rewritten, newly introduced regressions could be attributed to "known failures" and ignored. Mitigation: establish a clean test baseline BEFORE starting debt resolution; run tests after EVERY debt fix; any new failure introduced during a debt fix must be resolved before merging. |
| RISK-07 | **API pattern unification (FE-C03) breaks production pages** | Frontend, Backend | MEDIUM | HIGH | Moving `historico`, `conta`, `admin` from direct backend calls to proxy routes changes the auth flow. If the proxy routes do not forward auth headers identically, users experience authentication failures on pages that previously worked. Mitigation: implement one page at a time; test each with real admin and user accounts; deploy incrementally. |

---

## 3. Dependency Validation

### 3.1 DRAFT Dependency Chains: Validated

The 6 dependency chains in DRAFT Section 7 are structurally correct. My assessment of each:

**Chain 1: ORM Consolidation** -- CORRECT. `CROSS-C01 -> DB-C01 -> DB-H01 -> DB-H03`. The DB specialist's finding that there are competing Stripe handler implementations (NEW-DB-01) strengthens this chain. I would add NEW-DB-01 as a parallel prerequisite alongside DB-C01:

```
CROSS-C01 (Dual ORM) --must-precede-->
  DB-C01 (database.py URL) --parallel-with--> NEW-DB-01 (competing handlers)
    --must-precede--> DB-H01 (Consolidate ORM)
      --must-precede--> DB-H03 (Index stripe_subscription_id)
```

**Chain 2: Monolith Decomposition** -- CORRECT with one addition. The UX specialist's finding that FE-M01 (shared app shell) is a natural companion to FE-C01 (buscar decomposition) should be reflected. If the app shell is built FIRST, the buscar decomposition has a clear layout target:

```
FE-M01 (Shared app shell) --should-precede--> FE-C01 (buscar decomposition)
```

**Chain 3: Horizontal Scalability** -- CORRECT. No changes needed.

**Chain 4: CI/CD Green** -- NEEDS UPDATE. Given the corrected failure counts (0 backend, 38 frontend), the chain should reflect that backend CI is likely already green:

```
SYS-C04 (Fix pre-existing failures) -- PARTIALLY DONE (backend: 0 failures, frontend: 38)
  --must-precede--> SYS-M07 (Frontend coverage)
    --must-precede--> SYS-L01 (OpenAPI schema validation)
```

**Chain 5: RLS Security** -- CORRECT. These are independent and can be batched into a single migration as the DB specialist recommends.

**Chain 6: API Pattern Unification** -- CORRECT with UX specialist's addition. FE-M08 should be replaced with FE-NEW-09 (missing middleware routes), which is a smaller task.

### 3.2 Missing Dependencies Identified

| From | To | Dependency Type | Rationale |
|------|----|----------------|-----------|
| GAP-02 (Stripe production audit) | CROSS-C01 (ORM consolidation) | MUST-PRECEDE | Before rewriting Stripe handlers, we need to know the current production state: which webhooks are failing, are there users with stale subscription status? This data determines the scope of the ORM consolidation. |
| FE-L03 (Price reconciliation) | Product owner sign-off | BLOCKED-BY | Cannot resolve price divergence without business decision on canonical prices. |
| DB-H04 (RLS tightening) | Backend audit of table access patterns | MUST-PRECEDE | Need to verify all code paths use service_role key before restricting policies. |
| NEW-DB-02 (fix default plan_type) | DB-M02 (tighten CHECK constraint) | MUST-PRECEDE | Must update the trigger default before removing `'free'` from the CHECK constraint, otherwise new user creation fails. DB specialist correctly identifies this. |

### 3.3 Proposed Resolution Order Validation

The DRAFT's 4-sprint plan is structurally sound. I validate the ordering with the following adjustments:

**Sprint 1 adjustments:**
- ADD: GAP-02 (Stripe production audit) as item 0 -- a 2-4h investigation that determines the urgency and scope of the ORM consolidation.
- MOVE: SYS-C04 partially into Sprint 1 -- given backend failures are already resolved, the remaining work is only the 38 frontend failures (4-8h). Getting CI green early provides the safety net for all subsequent work.
- ADD: FE-L03 (price reconciliation) as P0 per UX specialist -- this is a trust issue for paying users.

**Sprint 2 adjustments:**
- No structural changes. The ORM consolidation + API unification pairing is correct.

**Sprint 3 adjustments:**
- ADD: FE-M01 (shared app shell) BEFORE FE-C01 (buscar decomposition). Building the app shell first gives the buscar refactoring a clear layout target.

**Sprint 4: No changes needed.**

---

## 4. Test Requirements

### 4.1 Tests Needed Post-Resolution

For each major debt, the tests that validate the fix:

| Debt ID | Resolution | Required Tests | Type |
|---------|-----------|----------------|------|
| DB-C01 + DB-H01 + NEW-DB-01 (ORM consolidation) | Migrate Stripe webhooks to Supabase client | (1) Unit tests for each webhook handler (subscription.created, updated, deleted, invoice.payment_succeeded, invoice.payment_failed) using mocked Supabase client. (2) Integration test: send Stripe test webhook, verify `user_subscriptions` and `profiles.plan_type` both updated. (3) Verify `stripe_webhook_events` idempotency table is written. (4) Regression: existing `test_stripe_webhook.py` (21 tests) must continue passing. | Unit + Integration |
| DB-C03 (admin policy fix) | Change `plan_type='master'` to `is_admin=true` | (1) Test: admin user with `plan_type='consultor_agil'` and `is_admin=true` CAN read webhook events. (2) Test: master user with `is_admin=false` CANNOT read webhook events. (3) Test: admin user with `plan_type='master'` and `is_admin=true` still works. | Integration (Supabase RLS) |
| DB-H04 (RLS tightening) | Add `TO service_role` restriction | (1) Test: anon key CANNOT insert/update/delete `monthly_quota`. (2) Test: authenticated user key CANNOT insert/update `monthly_quota`. (3) Test: service_role key CAN insert/update/delete. (4) Same for `search_sessions`. | Integration (Supabase RLS) |
| SYS-C02 (main.py decomposition) | Extract into router modules | (1) All existing `test_main.py` tests must pass against the new router structure. (2) Import paths test: verify no circular imports in extracted modules. (3) OpenAPI schema comparison: exported schema before and after must be identical (no API contract changes). | Unit + Contract |
| FE-C01 (buscar decomposition) | Extract components and hooks | (1) Visual regression: Playwright screenshots before/after must match. (2) All existing `page.test.tsx` tests that currently pass must continue passing. (3) New unit tests for extracted hooks (`useSearch`, `useSearchFilters`). (4) E2E: `search-flow.spec.ts` must pass. | Visual + Unit + E2E |
| FE-C03 (API pattern unification) | All pages use proxy routes | (1) Test each migrated page (historico, conta, admin, mensagens) with expired auth token -- should redirect to login, not show raw 401. (2) Test: `NEXT_PUBLIC_BACKEND_URL` is NOT present in client-side JavaScript bundle (verify with `next build` + bundle grep). (3) Network tab verification: no requests to backend URL from browser. | E2E + Bundle analysis |
| FE-L03 (price reconciliation) | Single source of truth for prices | (1) Unit test: all price display components reference the same data source. (2) E2E test: navigate to pricing page, compare prices with planos page -- they must match. (3) Contract test: frontend price data matches backend `/plans` endpoint response. | Unit + E2E + Contract |
| SYS-C01 (Redis for SSE state) | Replace in-memory dict with Redis pub/sub | (1) Test: start search on instance A, receive progress on instance B (simulated with separate worker processes). (2) Test: Redis connection failure degrades gracefully (falls back to simulation, does not crash). (3) Load test: 50 concurrent SSE connections with Locust. | Integration + Load |
| CROSS-C02 (Object storage for Excel) | Replace tmpdir with S3/Supabase Storage | (1) Test: generate Excel, restart server, download still works. (2) Test: concurrent downloads of different files. (3) Test: file cleanup after TTL. (4) Test: signed URL expiry. | Integration |

### 4.2 Regression Test Strategy

**Baseline Establishment (BEFORE any debt resolution begins):**

1. **Backend:** Run full test suite, record exact counts. Current baseline: 1631 tests, 0 failures (to be confirmed in CI).
2. **Frontend:** Run full test suite, record exact counts. Current baseline: 1072 tests, 38 failures in 6 suites, 8 skipped.
3. **E2E:** Run full Playwright suite against production, record results. Current: 60 tests across 12 spec files.
4. **Save baseline as artifact:** Create `docs/testing/baseline-2026-02-11.md` with exact counts.

**During Debt Resolution:**

1. **Per-PR testing:** Every PR that resolves a debt must include the test results summary. The number of passing tests must be >= baseline. The number of failing tests must be <= baseline. Any deviation must be explained.
2. **No "temporary regressions":** If fixing debt X breaks test Y, both must be fixed in the same PR. Do not merge a PR that introduces new failures with the promise of fixing them later.
3. **CI enforcement:** The CI pipeline (`.github/workflows/tests.yml`) must be green before merging any debt-resolution PR. Given backend tests now pass, the immediate action is to fix the 38 frontend failures to establish a green baseline.
4. **E2E gate for high-risk changes:** For ORM consolidation (CROSS-C01), monolith decomposition (SYS-C02, FE-C01), and API unification (FE-C03), require a full E2E run as a merge gate.

**Post-Sprint Validation:**

After each debt resolution sprint, run:
1. Full backend test suite with coverage (must stay above 70%)
2. Full frontend test suite with coverage (target: 60%)
3. Full E2E suite against staging
4. Manual smoke test of billing flow (as this has no automated E2E coverage)

---

## 5. Answers to DRAFT Questions

### Q1: Pre-existing test failures -- fix vs rewrite vs remove?

**Current State (verified 2026-02-11):**
- **Backend:** 0 failures out of 1631 tests. The 21 previously reported failures (billing, stripe, feature flags, prorata) have been resolved by commit `10c6a6a` (STORY-185). No backend tests need fixing, rewriting, or removing.
- **Frontend:** 38 failures in 6 test suites out of 1072 total tests (96.5% pass rate).

**Breakdown of the 38 frontend failures:**

| Test Suite | Failures | Recommendation | Effort |
|-----------|----------|---------------|--------|
| `page.test.tsx` | ~7 | **FIX.** These test the main search page. Failures are in download button assertions and loading state detection. The tests are structurally sound but have stale selectors (e.g., checking for `bg-brand-navy` class that may have changed). Update selectors and assertions to match current UI. | 3-4h |
| `free-user-search-flow.test.tsx` | ~8 | **REWRITE as E2E.** These are integration-style tests that render the full buscar page with complex mock chains. They are brittle because they depend on deep implementation details (specific hook return shapes, component internal state). Rewrite as Playwright E2E tests -- they are testing user flows, not unit behavior. | 4-6h (as E2E) |
| `free-user-history-save.test.tsx` | ~5 | **REWRITE as E2E.** Same reasoning as above. | 2-3h (as E2E) |
| `free-user-auth-token-consistency.test.tsx` | ~5 | **REWRITE as E2E.** Tests auth token behavior across navigation -- this is inherently an integration concern. | 2-3h (as E2E) |
| `free-user-navigation-persistence.test.tsx` | ~6 | **REWRITE as E2E.** Tests state persistence across page navigation. | 2-3h (as E2E) |
| `GoogleSheetsExportButton.test.tsx` | 7 | **FIX.** All 7 tests fail -- likely a component import/mock issue rather than individual test bugs. The test structure is correct (tests rendering, success flow, OAuth redirect, error handling). Probably needs updated mocks after a component refactor. | 2-3h |

**Summary:** 0 tests should be removed. ~14 should be fixed in-place. ~24 should be rewritten as E2E tests (they are testing integration flows with unit test tooling, which is the wrong abstraction level).

**Total effort:** 14-22h (less than the DRAFT's 8-16h estimate because backend is already done, but frontend rewrite-as-E2E is more work than simple fixing).

### Q2: Coverage priorities -- which components to reach 60%?

Current coverage is ~49.46%. The gap to 60% is approximately 10.5 percentage points. Based on the test file list and the DRAFT's suggestions, here is the prioritized list:

**Priority 1 -- Highest coverage ROI (pages with most logic):**

| Component | Current Coverage | Lines of Code | Estimated Coverage Gain | Effort |
|-----------|-----------------|---------------|------------------------|--------|
| `app/buscar/page.tsx` | Partial (page.test.tsx exists but 7 tests fail) | ~1100 lines | 4-6% | 3-4h (fix existing + add new) |
| `app/api/buscar/route.ts` | Partial (download.test.ts exists) | ~200 lines | 1-2% | 2h |
| `app/historico/page.tsx` | Partial (HistoricoPage.test.tsx exists) | ~400 lines | 1-2% | 2h |

**Priority 2 -- Untested critical components:**

| Component | Current Coverage | Lines of Code | Estimated Coverage Gain | Effort |
|-----------|-----------------|---------------|------------------------|--------|
| `app/components/AnalyticsProvider.tsx` | Partial (test exists) | ~100 lines | 0.5% | 1h |
| `app/components/RegionSelector.tsx` | Partial (test exists) | ~200 lines | 1% | 1h |
| `app/components/LoadingProgress.tsx` | Partial (test exists) | ~150 lines | 0.5% | 1h |
| `app/components/SavedSearchesDropdown.tsx` | None | ~150 lines | 1% | 2h |

**Priority 3 -- Easy wins (small untested files):**

| Component | Estimated Coverage Gain | Effort |
|-----------|------------------------|--------|
| `lib/plans.ts` | 0.5% | 0.5h |
| `lib/config.ts` | 0.3% | 0.5h |
| `app/api/analytics/route.ts` | 0.3% | 1h |
| `middleware.ts` | 0.5% | 1h |

**Recommended strategy:** Fix Priority 1 first (fix existing failing tests + add tests for buscar/route). This alone should push coverage to ~55-57%. Then add Priority 2 tests to cross the 60% threshold. Total estimated effort: 12-16h. This aligns with FE-L07's estimate.

**Components NOT to prioritize (from DRAFT's suggestions):** The DRAFT mentions `LoadingProgress`, `RegionSelector`, `SavedSearchesDropdown`, `AnalyticsProvider`. These are correct Priority 2 targets, but the biggest coverage gains come from fixing the broken `page.test.tsx` (Priority 1) because `buscar/page.tsx` is the largest file in the frontend.

### Q3: Highest regression risk areas given production use with Stripe payments

Ranked by severity of potential production impact:

**Tier 1 -- Immediate financial impact:**

1. **Stripe webhook processing** (`backend/webhooks/stripe.py`, `backend/main.py:733-900`). The DB specialist confirmed these are likely broken (SQLAlchemy path fails). Any change here risks payment state inconsistency. This area has 21 unit tests but zero integration tests against real Supabase, and zero E2E tests.

2. **Quota enforcement** (`backend/quota.py`). The 4-layer fallback is robust but complex. Changes to plan definitions, subscription logic, or the fallback chain could silently allow free users to bypass limits or block paid users from searching. This area has 37 unit tests -- relatively well covered.

3. **Auth middleware** (`frontend/middleware.ts`, `backend/auth.py`). Token cache, session validation, and role checking. A regression here either locks out all users or allows unauthorized access. Backend has 18 auth tests. Frontend middleware has no unit tests.

**Tier 2 -- User experience degradation:**

4. **Search flow** (`backend/main.py:buscar_licitacoes`, `frontend/app/buscar/page.tsx`). The core product function. Regressions here are immediately visible to all users. Well-covered by E2E tests (`search-flow.spec.ts`), but the monolithic structure means any refactoring is high-risk.

5. **SSE progress tracking** (`backend/progress.py`, `frontend/app/buscar/page.tsx` SSE consumer). In-memory state means regressions are hard to reproduce. No dedicated unit tests for progress tracking.

6. **Excel generation and download** (`backend/excel.py`, `frontend/app/api/download/route.ts`). File-system-dependent, cross-service. A regression here means users complete a search but cannot download results.

**Tier 3 -- Administrative impact:**

7. **Admin panel** (`backend/admin.py`, `frontend/app/admin/page.tsx`). Used for user management and plan changes. Regressions here affect operations but not end users directly.

### Q4: E2E Playwright gaps for billing/Stripe checkout

**Critical gap confirmed.** I verified the 12 E2E spec files:

```
search-flow.spec.ts       -- search UX
theme.spec.ts             -- dark/light mode
saved-searches.spec.ts    -- save/load searches
empty-state.spec.ts       -- no results UX
error-handling.spec.ts    -- error states
admin-users.spec.ts       -- admin panel
auth-ux.spec.ts           -- login/signup
performance.spec.ts       -- load times
plan-display.spec.ts      -- plan badge and quota display
signup-consent.spec.ts    -- signup consent checkboxes
institutional-pages.spec.ts -- terms, privacy
landing-page.spec.ts      -- landing page
```

**Missing billing/Stripe E2E tests:**

| Missing Test | Priority | Description |
|-------------|----------|-------------|
| `checkout-flow.spec.ts` | **P0** | Navigate to /planos, select a plan, click "Assinar", verify redirect to Stripe Checkout (or mock). Verify return to /planos/obrigado on success. Verify plan badge updates. |
| `subscription-management.spec.ts` | **P1** | Logged-in paid user visits /conta, clicks "Gerenciar Assinatura", verify redirect to Stripe Customer Portal (or mock). |
| `upgrade-downgrade.spec.ts` | **P1** | Free trial user sees upgrade prompts. Clicking "Upgrade" navigates to /planos. Plan comparison page shows correct prices (ties into FE-L03). |
| `quota-enforcement.spec.ts` | **P1** | User with 0 remaining credits attempts search, verify block message and upgrade CTA appear. |
| `price-consistency.spec.ts` | **P0** | Navigate to /pricing, capture prices. Navigate to /planos, capture prices. Assert they match. (This would have caught FE-L03 automatically.) |

**Recommendation:** Add at minimum `checkout-flow.spec.ts` and `price-consistency.spec.ts` as P0. These can use Playwright route mocking to intercept Stripe redirects rather than requiring a real Stripe test environment. The `plan-display.spec.ts` already does mock-based testing of plan badges -- extend this pattern for checkout flows.

### Q5: Should we prioritize Locust load testing?

**Yes, but not immediately.** Here is the reasoning:

**Current state:**
- `locustfile.py` exists with well-structured test scenarios (search, download, health check)
- `.github/workflows/load-test.yml` exists and runs weekly + on backend PRs
- The backend has rate limiting (10 req/s to PNCP) and retry logic (exponential backoff)

**When load testing matters most:**
1. **After ORM consolidation (Sprint 2):** The new Supabase-client-based Stripe handlers may have different connection pool behavior. Load test the webhook endpoint with 50 concurrent events.
2. **After Redis migration (Sprint 4):** SSE state moves from in-memory to Redis. The latency characteristics change fundamentally. Load test with 100 concurrent search sessions.
3. **Before any pricing tier changes:** If Sala de Guerra users are promised unlimited searches, the system must handle their peak usage without degradation.

**Recommendation:** Do not prioritize load testing in Sprint 1 (security fixes). In Sprint 2, after ORM consolidation, run a baseline load test and save results. In Sprint 4, run comparative load tests before and after Redis migration. The existing `locustfile.py` and workflow are sufficient infrastructure -- the gap is in actually running them and establishing baselines, not in building test infrastructure.

**One specific load test to add:** The current `locustfile.py` does not test SSE connections. Add a Locust task that opens an SSE connection to `/buscar-progress/{search_id}` and holds it open for 30-60 seconds. This validates the `_active_trackers` in-memory dict under concurrent load (relevant to SYS-C01).

### Q6: Should we add automated security tests to CI?

**Yes. Here is the phased approach:**

**Phase 1 (Immediate -- already partially done):**
- CodeQL is already configured (`.github/workflows/codeql.yml`). It runs weekly and on PRs. This covers static analysis for both Python and JavaScript. **Verify it is actually running and not failing silently** (check GitHub Actions history).
- Add `pip audit` to the backend CI job (`.github/workflows/tests.yml`). One line: `pip install pip-audit && pip-audit`. Catches known CVEs in Python dependencies.
- Add `npm audit --audit-level=high` to the frontend CI job. Already common practice.
- **Effort:** 1-2h.

**Phase 2 (After RLS fixes in Sprint 1):**
- Add RLS policy regression tests. These are SQL-based tests that verify:
  - Anon key cannot access any table
  - Authenticated user can only read their own data
  - Service role can access everything
  - Admin policies work correctly (test DB-C03 fix)
- Implement as a pytest fixture that connects to a test Supabase instance with different role keys.
- **Effort:** 4-6h.

**Phase 3 (Sprint 3+):**
- Add OWASP ZAP or similar DAST (Dynamic Application Security Testing) to the E2E pipeline. Run against staging after deployment.
- Test for: SQL injection via search parameters, XSS via user-generated content (search terms, message bodies), CSRF on state-changing endpoints, auth bypass on protected routes.
- **Effort:** 8-12h.

**Specific tests recommended for the identified RLS gaps:**

```python
# tests/test_rls_security.py
async def test_anon_cannot_insert_monthly_quota(anon_client):
    """DB-H04: Verify anon key blocked after RLS tightening."""
    result = await anon_client.table('monthly_quota').insert({...}).execute()
    assert result.error is not None

async def test_user_cannot_read_other_user_subscriptions(user_a_client):
    """Verify user cannot access other users' subscription data."""
    result = await user_a_client.table('user_subscriptions').select('*').execute()
    # Should only return user_a's subscriptions, not others
    for sub in result.data:
        assert sub['user_id'] == user_a_id

async def test_admin_can_read_webhook_events(admin_client):
    """DB-C03: Verify admin with is_admin=true can read webhook events."""
    result = await admin_client.table('stripe_webhook_events').select('*').execute()
    assert result.error is None
```

### Q7: How to ensure schema consistency between environments given migration issues?

**Current problem:**
- 17 migration files in `supabase/migrations/`, including 3 with `006_` prefix
- At least one migration (`006_APPLY_ME.sql`) was designed for manual dashboard paste
- No migration tracking document exists
- No way to verify which migrations have been applied in production
- The column `user_subscriptions.updated_at` may have been added manually

**Recommended solution (3-phase):**

**Phase 1 (Immediate, Sprint 1): Audit and Document**
1. Connect to production Supabase and dump the current schema: `supabase db pull --schema public`
2. Compare with local migration state: `supabase db diff`
3. Create `supabase/MIGRATIONS_APPLIED.md` documenting which migrations are applied and when (as DB specialist recommends)
4. Resolve the `006_*` ambiguity per DB specialist's recommendation
5. **Effort:** 2-3h

**Phase 2 (Sprint 2): Enforce Migration Discipline**
1. All schema changes go through migration files starting from `016_`
2. Use `supabase db push` for applying migrations, never dashboard SQL editor
3. Add a CI check that runs `supabase db diff` against a fresh Supabase instance with all migrations applied -- if the diff is non-empty, the migration files do not reproduce the expected schema
4. **Effort:** 3-4h

**Phase 3 (Sprint 3+): Environment Parity**
1. Create a staging Supabase project (if not already existing)
2. Apply all migrations to staging first, verify, then apply to production
3. Add environment-specific seed files for data that differs between environments (Stripe price IDs from DB-M05, test users, etc.)
4. Separate migration files from seed files: `supabase/migrations/` for DDL, `supabase/seeds/` for environment-specific DML
5. **Effort:** 4-6h

**Key principle:** The migration files in the repository must be the single source of truth for the schema. If you cannot start from an empty database, apply all migrations, and get a schema identical to production, then the migration system is broken. Phase 1's audit will determine how far the current state is from this ideal.

---

## 6. Quality Metrics Targets

Measurable quality goals for after debt resolution is complete (end of Sprint 4):

| Metric | Current | Sprint 1 Target | Sprint 2 Target | Sprint 4 Target |
|--------|---------|-----------------|-----------------|-----------------|
| Backend test pass rate | 100% (1631/1631) | 100% | 100% | 100% |
| Frontend test pass rate | 96.5% (1026/1072) | 100% (fix 38 failures) | 100% | 100% |
| Backend coverage | ~96.69% | >= 70% (maintain) | >= 70% | >= 80% |
| Frontend coverage | ~49.46% | >= 55% | >= 60% (threshold) | >= 65% |
| E2E test count | 60 tests / 12 specs | 60 (no regression) | 75+ (add billing specs) | 85+ |
| E2E pass rate | Unknown (not baselined) | Establish baseline | >= 95% | >= 98% |
| CRITICAL debts open | 12 | 7 (resolve DB-C03, FE-C02, DB-H04, DB-H05, FE-L03) | 2 (resolve CROSS-C01, SYS-C04) | 0 |
| HIGH debts open | 17 | 12 | 5 | 0 |
| CI pipeline status | RED (frontend coverage gate fails) | GREEN | GREEN | GREEN |
| Lighthouse performance (buscar) | Unknown | Establish baseline | >= 80 | >= 90 |
| Mean time to detect regression | Unknown (CI broken) | < 15 min (CI green) | < 15 min | < 10 min |
| Security vulnerabilities (CodeQL) | Unknown | 0 critical, 0 high | 0 critical, 0 high | 0 critical, 0 high, 0 medium |
| Schema drift (migration diff) | Unknown | 0 untracked changes | 0 untracked changes | 0 untracked changes |

---

## 7. Final Assessment

### Overall Quality of the Assessment

The DRAFT, combined with the DB specialist and UX specialist reviews, forms a comprehensive and well-structured technical debt inventory. The quality of analysis is high -- specific file paths, line numbers, and severity justifications are provided for every item. The dependency chains are well-reasoned. The sprint plan is realistic.

### Conditions for Approval

The following must be addressed during final consolidation before this assessment can be used as a work plan:

1. **Update failure counts.** The DRAFT references 21 backend + 70 frontend failures. The actual numbers are 0 backend + 38 frontend. This changes the effort estimate for SYS-C04 and the urgency of Chain 4 (CI/CD Green). Backend CI may already be green.

2. **Incorporate the 14 new debts from specialist reviews.** The DB specialist added 5 new items (NEW-DB-01 through NEW-DB-05). The UX specialist added 9 new items (FE-NEW-01 through FE-NEW-09). The UX specialist also removed 1 item (FE-M08) and upgraded FE-L03 from LOW to CRITICAL. The final consolidated document must reflect all of these, bringing the total from 72 to approximately 85 items.

3. **Add GAP-02 (Stripe production audit) as Sprint 0 prerequisite.** Before beginning any ORM consolidation work, the team must verify the current state of Stripe webhook processing in production. This is a 2-4h investigation that could reveal the ORM consolidation is even more urgent than estimated, or could reveal compensating controls that reduce urgency.

4. **Add GAP-06 (auth rate limiting) and GAP-09 (billing E2E gap) to the inventory.** These are meaningful quality gaps that should be tracked.

5. **Require product owner sign-off on FE-L03 (prices).** The UX specialist correctly escalated this to CRITICAL. However, the fix requires a business decision on canonical prices. This must be flagged as blocked-by-business-decision, not just as a code task.

### Strengths of the Assessment

- **Evidence-based.** Every debt cites specific files, line numbers, and commits.
- **Dependency-aware.** The chain analysis prevents wasted work from incorrect ordering.
- **Specialist-reviewed.** Both the DB and UX specialists validated findings and added material new items.
- **Actionable.** Sprint plan includes effort estimates, ordering, and groupings.
- **Balanced.** Positive observations (Section 9) ensure the team knows what to preserve.

### Concerns

- **Effort estimates are optimistic.** The total (280-380h across all documents) assumes no rework, no discovery of additional issues during resolution, and no context-switching overhead. In my experience, debt resolution typically takes 1.3-1.5x the estimated effort. Budget accordingly.
- **Sprint 2 is overloaded.** ORM consolidation (12-16h) + API unification (8-12h) + component consolidation (3-4h) + test fixes (8-16h) = 31-48h in one sprint. If sprints are 2-week with one developer, this is aggressive. Consider splitting Sprint 2 into 2a (ORM consolidation only) and 2b (API unification + component cleanup).
- **No rollback plan documented.** For each sprint, document what happens if the changes need to be reverted. The DB specialist's rollback suggestion for ORM consolidation (keep dead code for 2 weeks) is good but should be a pattern for all high-risk changes.

### Verdict

**APPROVED WITH CONDITIONS.** The assessment is ready for final consolidation pending the 5 conditions listed above. The combined ~85 items, 4-sprint plan, and dependency chains provide a solid foundation for systematic debt reduction. The specialist reviews materially improved the assessment by adding 14 new items, correcting 7 severity ratings, and removing 1 false positive.

---

*Review completed by @qa (Quinn) on 2026-02-11. Test execution verified against codebase at commit `808cd05`. All gap identifications and risk assessments are based on direct codebase inspection, not assumptions.*
