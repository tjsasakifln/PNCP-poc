# QA Review — Technical Debt Assessment — SmartLic

**Reviewer:** @qa (Quinn)
**Date:** 2026-03-31
**Version:** v3 (supersedes v2 from 2026-03-30)
**Documents Reviewed:** `docs/prd/technical-debt-DRAFT.md` (63 debts, Phase 4), `docs/reviews/db-specialist-review.md` (Phase 5), `docs/reviews/ux-specialist-review.md` (Phase 6)
**Codebase Verification:** Spot-checked key claims against actual source files (migration count, ViabilityBadge.tsx, useSearchOrchestration.ts line count, globals.css reduced-motion rule, trigger DROP in migration 20260308100000)

---

## Gate Status: APPROVED

The assessment is comprehensive, well-structured, and actionable. Both specialist reviews are thorough and evidence-based, catching 2 already-resolved debts, correcting 9 severity ratings, and adding 7 new debts. After incorporating the adjustments documented below, this assessment is ready for Phase 8 (final consolidation by @architect).

---

## Assessment Quality Score

| Dimension | Score (1-5) | Notes |
|-----------|-------------|-------|
| Completeness | 4 | 63 debts across 4 categories (System, DB, FE, Cross-Cutting) is thorough. Specialists added 7 more (3 DB, 4 FE). A few gaps remain (see Section 3) but none are blocking. |
| Accuracy | 4 | Two debts already resolved (DB-003, FE-003), one partially resolved (FE-015, FE-009). All caught by specialists. useSearchOrchestration described as "200+ lines" -- actual is 369 (verified via `wc -l`). DB-003 DROP confirmed in migration 20260308100000. FE-003 `role="tooltip"` confirmed in ViabilityBadge.tsx. Migration count of 106 confirmed. |
| Prioritization | 4 | P0 items are correct (security fix DB-001 + user trust FE-001/FE-006). P1/P2 separation is reasonable. One concern: CROSS-006 (scaling, 32h) at P1 is premature for current traffic (~25 searches/day). |
| Effort Estimates | 3 | Total hours inflated by double-counting between CROSS items and their constituent SYS/FE/DB items. DRAFT shows ~506h but acknowledges overlap. Actual deduplicated effort is ~350-390h. DB specialist reduced DB section from 73h to 54h. UX specialist adjustments net to roughly flat (~148h) after closures and additions. |
| Dependencies | 4 | Dependency graph is clear and correct. DB specialist added important nuance: DB-007 FK with CASCADE would destroy audit trail. One missing dependency and one questionable dependency identified (see Section 6). |
| Risk Coverage | 4 | 8 risks in DRAFT, 5 added by DB specialist, 6 added by UX specialist. No major risk category unaddressed. Minor gap: test suite fragility during refactoring not explicitly addressed (see Section 3). |

**Overall: 3.8/5** -- Strong assessment with corrections needed before finalization, none blocking.

---

## Gaps Identified

### Gap 1: Test Suite Fragility During Refactoring (MEDIUM)

The DRAFT identifies debts requiring ~350-390h of refactoring. The project has 7656+ backend tests and 5733+ frontend tests with a zero-failure policy. However, the assessment does not address:

- **Which tests will break** during SYS-001 (filter decomposition, 40h), SYS-003/004 (cron/job decomposition, 32h), and FE-002 (useSearchOrchestration decomposition, 16h). For SYS-001 alone, expect 50+ test files referencing `filter.py` or `filter/` imports.
- **Test pollution patterns** documented in project memory (`sys.modules` injection, `importlib.reload`, global singleton leakage) that could resurface during module restructuring.
- **Windows full-suite constraint** -- `run_tests_safe.py` with subprocess isolation is required on Windows; direct `pytest` hangs. This adds overhead to every refactoring verification cycle.

**Recommendation:** The final assessment should include a "Test Impact" column for HIGH-effort items, estimating test files needing import path updates. Budget 20-30% overhead on effort estimates for test maintenance.

### Gap 2: No Observability Debt Category (LOW)

Observability-specific debt is scattered across categories:

- SYS-014 (LLM cost monitoring) is in System
- DB-010 (VACUUM monitoring) is in Database
- The `check_pncp_raw_bids_bloat()` function exists but nobody monitors it (DB specialist confirmed)
- Prometheus metrics, Sentry error grouping, and alerting rules are not assessed as a category

Individual items are captured, but a coherent "Observability and Alerting" section in the final assessment would help plan monitoring improvements as a single initiative rather than scattered fixes.

### Gap 3: No CI/CD Pipeline Debt Assessment (LOW)

The DRAFT mentions the 3-layer migration CI flow and Railway deploy rules but does not assess CI workflow run times, the `.railwayignore` configuration, the Docker `CACHEBUST` ARG mechanism, or whether redundant workflows exist. Acceptable because CI/CD is operational rather than structural debt, but worth noting for awareness.

### Gap 4: Worker/Queue Resilience (LOW)

The DRAFT covers `job_queue.py` decomposition (SYS-004) but does not assess ARQ's known lack of runtime reconnection (issue #386), the restart wrapper pattern, queue depth monitoring, dead letter handling, or in-flight job behavior during Railway deploy restarts. Should be noted as a known operational concern in the final assessment.

---

## Cross-Cutting Risks

| Risk | Areas Affected | Probability | Impact | Mitigation |
|------|---------------|-------------|--------|------------|
| **Refactoring regression** -- Large decompositions (SYS-001, SYS-003, SYS-004, FE-002) will break import paths across 100+ test files | Backend, Frontend, CI | HIGH | MEDIUM | Run full test suite after each decomposition using `run_tests_safe.py --parallel 4`. Budget 20-30% overhead. Use `__init__.py` re-exports during transition. |
| **Migration squash data loss** -- DB-002 squash creates new baseline. If any migration side effect (data transform, seed insert) is missed in squashed version, data integrity is silently lost | Database, Backend | MEDIUM | HIGH | DB specialist's phased approach (fix DB-001/004/008/010/011 before squash) is correct. Add: test clean DB creation from squashed baseline against pg_dump of production schema. |
| **Auth unification regression** -- FE-004 + CROSS-002 touch three auth enforcement points. A mistake could create temporary auth bypass | Frontend, Backend | LOW | CRITICAL | Require dedicated security review before and after. Extend E2E Playwright tests with auth boundary checks. |
| **SSE breaking change** -- CROSS-001 modifies both backend event emission and frontend event handling. Mismatched deploy order could break search progress | Backend, Frontend, Infra | MEDIUM | HIGH | Deploy backend first (new events are additive). Frontend must handle both old and new event shapes during transition. |
| **Feature flag removal side effects** -- SYS-008/CROSS-003 removing old flags could re-enable or disable features unexpectedly | Backend, Frontend | MEDIUM | MEDIUM | Never remove a flag without grep-verifying all references. Add `deprecated_since` field; only remove flags deprecated 2+ sprints with zero references. |
| **LLM cost spike during refactoring** -- If SYS-014 (cost monitoring) is not implemented before SYS-001 (filter decomposition), a regression in classification logic could bypass MAX_ZERO_MATCH_ITEMS cap without alerting | Backend | LOW | HIGH | Implement SYS-014 early (alongside P0 items). 6h investment provides safety net for all subsequent work. |

---

## Specialist Review Reconciliation

### DB Review Adjustments

The @data-engineer review is methodical and evidence-based. All adjustments are well-justified.

| Action | Items | Impact on Backlog |
|--------|-------|-------------------|
| **Closure** | DB-003 (duplicate triggers) -- already resolved in migration `20260308100000` | -2h, remove from active backlog |
| **Deferrals** | DB-009 (org RLS perf, 0 production rows), DB-016 (SERIAL vs UUID, not worth changing) | -5h deferred |
| **Severity upgrade** | DB-008 (retention policies, MEDIUM to HIGH) -- table growth is guaranteed and will be first perf issue at scale | Moves to higher priority |
| **Severity downgrades** | DB-003 (HIGH to CLOSED), DB-007 (MEDIUM to LOW, FK CASCADE would destroy audit), DB-009 (MEDIUM to LOW), DB-011 (MEDIUM to LOW, cosmetic) | 4 items deprioritized |
| **Hour adjustments** | DB-008 (4h to 6h), DB-012 (2h to 1h) | Net DB section: 73h to 54h for 17 active debts |
| **New items** | DB-021 (quota RPCs missing SECURITY DEFINER, 1h), DB-022 (2 more functions missing SET search_path, 1h), DB-023 (search_sessions retention, 2h) | +4h, +3 items |

**Critical insight accepted:** DB-007 FK with ON DELETE CASCADE would destroy the audit trail when search sessions are cleaned up. The DB specialist's recommendation to handle cleanup via independent retention policy is correct. The DRAFT's CASCADE recommendation must be revised.

**Resolution order validated:** Phase 0 (immediate security) -> Phase 1 (pre-squash cleanup) -> Phase 2 (squash) -> Phase 3 (opportunistic). Dependencies are correctly mapped.

### UX Review Adjustments

The @ux-design-expert review is thorough and provides actionable design guidance with code-level evidence.

| Action | Items | Impact on Backlog |
|--------|-------|-------------------|
| **Closure** | FE-003 (ViabilityBadge) -- already has accessible tooltip with `role="tooltip"`, `aria-describedby`, keyboard support, tap-to-toggle mobile | -4h, remove from active backlog |
| **Partial resolutions** | FE-015 (reduced-motion CSS done, only Framer Motion JS gap remains, 4h to 2h), FE-009 (28+ aria-live usages found, narrow gap, 4h to 2h) | -4h combined |
| **Severity upgrades** | FE-007 (MEDIUM to HIGH, 12 banners on core page), FE-028 (LOW to MEDIUM, brand-blue contrast fails AA for small text), FE-030 (LOW to MEDIUM, mobile conversion impact) | 3 items elevated |
| **Severity downgrades** | FE-011 (MEDIUM to LOW, not UX debt), FE-013 (MEDIUM to LOW, narrower gap than described), FE-015 (MEDIUM to LOW, largely resolved), FE-017 (MEDIUM to LOW, not UX), FE-019 (MEDIUM to LOW, purely DX) | 5 items deprioritized |
| **New items** | FE-033 (landing page hydration, HIGH, 10h), FE-034 (pipeline drag announcements, MEDIUM, 4h), FE-035 (chart colorblind safety, LOW, 4h), FE-036 (Shepherd.js eager loading, LOW, 2h) | +20h, +4 items |

**Critical insight accepted:** FE-033 (landing page RSC conversion) is a legitimate HIGH-severity addition. All 13 landing page children use `"use client"` but only 3 need client-side JS. Estimated LCP improvement from ~3.5s to ~2.0s is credible and directly affects trial acquisition.

### Conflicts Between Reviews

**No direct contradictions found.** The specialist reviews are complementary (DB focuses on data layer, UX on user-facing layer).

One **tension worth resolving:**

- The DRAFT places CROSS-006 (scaling constraint, 32h) at P1. Neither specialist flagged scaling as urgent. Given current traffic (~25 searches/day, ~50 users), the single-process constraint is a ceiling, not an active fire. **Recommendation:** Downgrade CROSS-006 from P1 to P2 with a trigger condition: "Move to P1 when daily searches exceed 200 or concurrent searches exceed 10."

---

## Dependency Validation

### Validated Dependencies (correct as documented)

1. **DB-001/004/008/010/011 -> DB-002 (squash)** -- Individual fixes must be in baseline before squashing. DB specialist confirmed with specific migration references and recommended DB-019 and DB-023 also precede squash.
2. **SYS-001 -> SYS-009** -- Cannot clean root filter shims until package is canonical.
3. **CROSS-001 = FE-001 + SYS-013** -- Single coordinated SSE fix.
4. **CROSS-003 = SYS-008 + FE-017** -- Unified feature flag implementation.
5. **FE-005 -> FE-010** -- Need clear directory structure before extracting new components.
6. **SYS-005 -> SYS-019** -- Root cache shim depends on package consolidation.
7. **SYS-003 -> SYS-004** -- Both reference same Redis pool patterns.

### Dependency Corrections

1. **FE-002 -> FE-004 (questionable direction)** -- The DRAFT says decomposing useSearchOrchestration enables auth guard unification because "auth logic is currently embedded in the mega-hook." The hook has a manual `useEffect` redirect at ~line 37. However, the auth unification (FE-004) requires a decision on whether `/buscar` joins the `(protected)` route group or gets middleware-level guard -- this is an architectural decision independent of hook decomposition. **Recommendation:** Remove FE-002 -> FE-004 dependency. These can be done in parallel.

2. **Missing: SYS-014 should precede SYS-001** -- LLM cost monitoring (6h) should be in place before filter decomposition (40h). The filter package includes the classification pipeline that invokes LLM. A refactoring error during SYS-001 that accidentally removes MAX_ZERO_MATCH_ITEMS cap or changes classification thresholds would be caught by cost monitoring. Without it, the error persists until the monthly OpenAI bill arrives.

3. **Missing: DB-023 -> DB-002** -- The DB specialist added DB-023 (search_sessions retention) and recommended it precede the squash, but this is not in the DRAFT's dependency graph. Should be added.

### Circular Dependencies

None detected. The dependency graph is a directed acyclic graph. DB dependencies are linear. FE dependencies are independent of DB. CROSS items bridge them without creating cycles.

---

## Test Strategy Post-Resolution

### Per-Debt Category

| Debt Category | Required Tests | Automation Level |
|---------------|---------------|-----------------|
| **DB Security (DB-001, DB-021, DB-022)** | Verify handle_new_user(), quota RPCs, analytics RPCs work after SET search_path. Test with non-public schema to confirm path isolation. | Manual SQL + automated integration via pytest against test DB |
| **DB Retention (DB-008, DB-023)** | Verify pg_cron jobs delete correct rows, preserve active records. Test boundary conditions (exactly 90 days, exactly 6 months). Verify no FK violations. | Automated: test migration + test data script, verify row counts |
| **DB Squash (DB-002)** | Full migration replay from squashed baseline on clean DB. Compare resulting schema against pg_dump of production (diff should be empty). Verify all RPCs, triggers, RLS, indexes. | Semi-automated: script to create clean DB + squash + diff |
| **Backend Decomposition (SYS-001, 003, 004, 005, 006)** | Full 7656+ test suite must pass. Import path verification: no test importing from legacy locations. Coverage must not decrease. | Automated: `python scripts/run_tests_safe.py --parallel 4` |
| **Frontend Hook Decomposition (FE-002)** | All 5733+ frontend tests pass. Focus: useSearchOrchestration tests, search flow E2E. No behavioral regression on search page. | Automated: `npm test` + `npm run test:e2e` |
| **Auth Unification (FE-004, CROSS-002)** | E2E: unauthenticated access to /buscar redirects, expired session handling, OAuth callback, all protected routes. Manual: incognito to each protected page. | Playwright E2E (extend existing 60 tests) + manual smoke |
| **SSE Fix (CROSS-001, FE-001)** | E2E: search taking >45s shows phase-specific messages, "longer than expected" UI, partial results option. Backend unit tests for new progress events. | Semi-automated: E2E + manual with slow search |
| **Accessibility (FE-009, 012, 014, 028, 034)** | axe-core on all pages (extend accessibility-audit.spec.ts). Manual NVDA screen reader test on search results, pipeline, forms. Color contrast check for brand-blue. | Automated: axe-core Playwright + manual NVDA |
| **Landing RSC (FE-033)** | Lighthouse CI: LCP < 2.5s (target < 2.0s). All interactive elements work (CTAs, sector grid, carousel). Visual regression test. | Automated: Lighthouse CI + Playwright screenshots |
| **Feature Flag Governance (CROSS-003)** | Each deprecated flag: verify default matches production behavior. Flag service: test backend API, frontend consumption, flag override in tests. | Automated: pytest for backend, jest for frontend hook |

### Regression Test Plan

| Refactoring Item | Test Files at Risk | Risk Level | Mitigation |
|------------------|--------------------|------------|------------|
| SYS-001 (filter decomposition) | 15-20 `test_filter*.py` + 10+ `test_search*.py` + 5+ `test_classification*.py` | HIGH | Update imports incrementally. Use `__init__.py` re-exports during transition. |
| SYS-003/004 (cron/job decomposition) | `test_cron*.py`, `test_job*.py`, `test_arq*.py` | MEDIUM | ARQ mock pattern via conftest `_isolate_arq_module` must be updated if module paths change. |
| FE-002 (hook decomposition) | `useSearchOrchestration*.test.ts`, `search-resilience.test.tsx`, `buscar.test.ts` | MEDIUM | Extract sub-hooks with identical external API contract. |
| FE-005 (directory consolidation) | All frontend tests importing from `app/components/` or `components/` | HIGH | Use TypeScript path aliases for backward compatibility. Update `moduleNameMapper` in jest.config.js. Pitfall: `@/` alias maps to `<rootDir>/` -- directory renames affect test resolution. |
| DB-002 (migration squash) | `test_crit001_schema_alignment.py` and any tests creating test DBs from migrations | LOW | Tests mock Supabase; they do not replay migrations. Verify post-squash schema matches test assumptions. |

---

## Metrics and Success Criteria

### Per-Priority Band

| Priority | Metric | Target | Measurement |
|----------|--------|--------|-------------|
| **P0** | Security vulnerabilities, search UX incidents | Zero SET search_path vulnerabilities; <5% of searches trigger "longer than expected" UI | Sentry monitoring; Mixpanel partial-results-prompt events |
| **P1** | Module sizes, test pass rate | No backend module >500 LOC (from filter package); no frontend hook >200 LOC; zero test failures | `wc -l` audit; CI green |
| **P2** | Accessibility compliance, flag count | axe-core zero critical violations; active flags <20 (from 30+) | Lighthouse CI; flag audit script |
| **P3** | Code hygiene | No duplicate functions, no redundant indexes, no vestigial columns | Schema audit query (run quarterly) |

### Overall Success Criteria

1. **Zero test regressions** -- Full suite (backend + frontend + E2E) passes after each debt resolution sprint
2. **Migration replay verified** -- Clean DB creation from squashed baseline matches production schema (pg_dump diff)
3. **LCP < 2.5s** -- Landing page after FE-033 RSC conversion (Lighthouse CI)
4. **Search UX** -- No searches "stuck" without user feedback for >45 seconds (Mixpanel tracking)
5. **Security** -- All SECURITY DEFINER functions have SET search_path (verified via schema audit query)
6. **Effort tracking** -- Actual hours within 30% of estimates (retrospective validation)

---

## Final Verdict

### Strengths of this Assessment

1. **Comprehensive coverage** -- 63 debts across 4 categories with clear IDs, severity, effort, and rationale. Production-quality documentation.
2. **Effective multi-phase process** -- Both specialist reviews validated claims against actual code, caught already-resolved items, and added missing debts with evidence. The reviews are not rubber stamps.
3. **Clear dependency graph** -- Section 6 dependencies are correct and match specialists' recommended resolution orders.
4. **Actionable prioritization** -- P0 items are genuinely urgent (security + user trust). Priority bands enable sprint planning.
5. **Thorough risk identification** -- 8 DRAFT risks + 5 DB risks + 6 UX risks cover security, performance, accessibility, and operational concerns.
6. **Specialist answers are excellent** -- DB specialist answered all 7 architect questions with specific migration references and SQL examples. UX specialist answered all 8 questions with concrete UX thresholds and component recommendations.

### Weaknesses / Areas for Improvement

1. **Effort double-counting** -- CROSS items share effort with constituent SYS/FE/DB items but total (506h) sums them independently. Final assessment must deduplicate. Estimated unique effort: ~350-390h.
2. **Missing test impact analysis** -- For a project with 13,000+ tests and zero-failure policy, every major refactoring needs a test impact estimate. Add "Test Impact" column to prioritization matrix.
3. **CROSS-006 premature at P1** -- 32h on scaling architecture is premature for 25 searches/day. Should be P2 with trigger condition.
4. **useSearchOrchestration line count error** -- DRAFT says "200+ lines," actual is 369. Minor but suggests incomplete verification. UX specialist corrected.
5. **No observability coherence** -- Monitoring debt is scattered. Should be presented as a coherent initiative in final assessment.
6. **DB-007 CASCADE recommendation is wrong** -- DRAFT recommends FK with ON DELETE CASCADE. DB specialist correctly argues this destroys audit trail. Must be revised.

### Recommendation

**APPROVED -- proceed to Phase 8 (final assessment consolidation by @architect).**

The following adjustments MUST be incorporated in the final version:

| # | Adjustment | Source |
|---|-----------|--------|
| 1 | Close DB-003 (duplicate triggers) -- mark RESOLVED, remove from active backlog (-2h) | DB specialist |
| 2 | Close FE-003 (ViabilityBadge) -- mark RESOLVED, remove from active backlog (-4h) | UX specialist |
| 3 | Accept DB severity changes: DB-007 to LOW (no CASCADE), DB-008 to HIGH, DB-009/016 deferred | DB specialist |
| 4 | Accept UX severity changes: FE-007 to HIGH, FE-028/030 to MEDIUM, FE-011/013/015/017/019 to LOW | UX specialist |
| 5 | Add 7 new items: DB-021, DB-022, DB-023, FE-033, FE-034, FE-035, FE-036 | Both specialists |
| 6 | Deduplicate effort totals -- CROSS items should note "included in SYS-X + FE-Y" | QA review |
| 7 | Downgrade CROSS-006 from P1 to P2 with trigger condition (>200 daily searches) | QA review |
| 8 | Add SYS-014 (LLM cost monitoring, 6h) to P0 as safety net before refactoring | QA review |
| 9 | Fix useSearchOrchestration description: "369 lines" not "200+" | UX specialist (verified) |
| 10 | Revise DB-007: remove CASCADE FK recommendation, use independent retention policy | DB specialist |
| 11 | Add DB-023 to dependency graph (should precede DB-002) | DB specialist |
| 12 | Remove FE-002 -> FE-004 dependency (independent items) | QA review |
| 13 | Add "Test Impact" column to prioritization matrix for HIGH-effort items | QA review |

**Estimated final debt count:** 68 items (63 original - 2 closed + 7 added)

**Estimated deduplicated effort:** ~350-390h across all priorities.

---

*Review completed 2026-03-31 by @qa (Quinn) as Phase 7 of Brownfield Discovery workflow.*
*Gate decision: APPROVED -- proceed to Phase 8 (@architect final consolidation).*
*Previous phases: Phase 4 (DRAFT by @architect), Phase 5 (DB review by @data-engineer), Phase 6 (UX review by @ux-design-expert).*
