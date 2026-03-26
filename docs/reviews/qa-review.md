# QA Review - Technical Debt Assessment

**Date:** 2026-03-23 | **Reviewer:** @qa (Quinn)
**Status:** Phase 7 -- Brownfield Discovery
**Inputs:** `docs/prd/technical-debt-DRAFT.md`, `docs/reviews/db-specialist-review.md`, `docs/reviews/ux-specialist-review.md`

---

## Gate Status: APPROVED (with corrections)

The assessment is complete enough for planning. The specialists identified significant factual errors in the DRAFT, but the corrections are well-documented and the remaining debts are accurately characterized. The DRAFT should be updated with all corrections before being used for sprint planning. No additional discovery phases are needed.

---

## 1. Assessment Accuracy

### DRAFT Error Rate

| Source | Items in DRAFT | Items Found Inaccurate | Error Rate |
|--------|---------------|----------------------|------------|
| Database (Phase 5) | 17 | 5 (3 RESOLVED + 2 outdated) | 29% |
| Frontend/UX (Phase 6) | 18 | 4 (1 RESOLVED + 3 severity-wrong) | 22% |
| Backend/System (self-reviewed) | 21 | 1 (DEBT-301 path inaccurate) | 5% |
| **Total** | **56** | **10** | **18%** |

### Process Issue: Stale Data Collection

**The most significant quality finding is not a debt item -- it is a process defect.** Three of the highest-severity items in the DRAFT (DB-C01 CRITICAL, DB-H01 HIGH, DB-H03 HIGH) were already resolved by migrations applied 2-3 weeks before the assessment was written. This means Phase 1-3 data collection relied on `DB-AUDIT.md` and `SCHEMA.md` documents that had not been updated after migrations were applied.

**Root cause:** The assessment pipeline reads static documentation rather than querying live database state. Migration files exist and prove resolution, but the audit documents were stale.

**Recommendation:** For future assessments, the data collection phase should include a migration verification step:
1. List all migration files applied after the audit document's last-modified date
2. Cross-reference audit findings against recent migrations
3. Run `supabase migration list` to confirm which migrations have been applied

This is analogous to running tests before declaring a bug -- verify the current state, not the documented state.

### Spot-Check Results (Code Verification)

I performed independent code verification on 8 DRAFT claims:

| Claim | Verified? | Finding |
|-------|-----------|---------|
| DEBT-323: `_plan_status_cache` unbounded | **TRUE** | `quota.py:44` -- plain dict, no eviction. `_token_cache` uses LRU(1000) but plan cache does not. |
| DEBT-301: `filter.py` 3871 LOC | **TRUE (path adjusted)** | File is now `filter/core.py` (3871 LOC). A `filter/` package was created with proxy modules, but `core.py` still contains all logic. The decomposition was structural (package facade) not functional. |
| DEBT-324: Dual Stripe webhook registration | **TRUE** | `startup/routes.py` lines 46 and 70 both register `stripe_webhook_router`. Line 46 adds it to `_v1_routers` (prefix `/v1/`), line 70 adds it at root. Both paths are live. |
| DEBT-325: Hardcoded USD_TO_BRL | **TRUE** | `llm_arbiter.py:73` -- `_USD_TO_BRL = 5.0`. Used on lines 216 and 237. |
| DEBT-302: schemas.py 2121 LOC | **TRUE** | Confirmed 2121 lines. |
| DEBT-307: Stripe webhooks 1192 LOC | **TRUE** | `webhooks/stripe.py` confirmed at 1192 lines. |
| DEBT-304: 69 top-level .py files | **CLOSE** | Actual count: 68 (including filter_*.py at top level + filter/ package). Negligible difference. |
| DEBT-314: 40+ feature flags | **INACCURATE** | `config/features.py` contains 16 flag definitions, not 40+. The "40+" claim may include non-flag config constants counted incorrectly. Effort should be reduced from 3h to 1h. |

**Accuracy of remaining items: 7/8 confirmed accurate (87.5%).** The one inaccuracy (DEBT-314) is a magnitude overestimate, not a structural error.

---

## 2. Revised Debt Summary

Incorporating all corrections from both specialists and my spot-check:

| Category | DRAFT Items | DRAFT Hours | Revised Items | Revised Hours | Delta |
|----------|-------------|-------------|---------------|---------------|-------|
| **CRITICAL** | 2 | 1.5h | 1 | 1h | -0.5h (DB-C01 resolved) |
| **HIGH** | 12 | ~67h | 8 | ~47h | -20h |
| **MEDIUM** | 25 | ~72h | 25 | ~62h | -10h |
| **LOW** | 17 | ~35h | 13 | ~27h | -8h |
| **New (specialists)** | 0 | 0h | 7 | ~7h | +7h |
| **TOTAL** | **56** | **~246h** | **47 open + 7 new = 54** | **~196h** | **-50h** |

### Severity Distribution After Corrections

**CRITICAL (1):**
- DEBT-323: `_plan_status_cache` unbounded dict (1h)

**HIGH (8):**
- TD-M07 (upgraded): Landing child components all client (10h)
- DEBT-301: filter/core.py 3871 LOC monolith (8h)
- DEBT-302: schemas.py 2121 LOC monolith (6h)
- DEBT-305: job_queue.py + cron_jobs.py monoliths (6h)
- DEBT-307: Stripe webhooks 1192 LOC monolith (6h)
- DEBT-304: Backend packaging (12h) -- but note 68 files, not 69
- TD-H02: Dual header/auth pattern (4h)
- DEBT-324: Dual Stripe webhook registration (1h)

**Items removed from HIGH:**
- DB-C01: RESOLVED
- DB-H01: RESOLVED
- DB-H03: RESOLVED
- TD-H01: Downgraded to MEDIUM (10h, partial RSC already exists)
- TD-H03: Downgraded to LOW (16 aria-live regions already exist)
- TD-H04: Downgraded to MEDIUM (keyboard DnD already works, only announcements missing)
- DB-H04: Remains HIGH but effort is tiny (0.25h)

---

## 3. Gaps Identificados

Areas NOT covered by the DRAFT or specialist reviews:

### Gap 1: Security Audit of Dual Webhook Registration (DEBT-324)

The DRAFT identifies dual registration but does not assess whether double-processing actually occurs. If Stripe sends webhooks to both `/v1/webhooks/stripe` and `/webhooks/stripe`, every event would be processed twice (double subscription activations, double invoice processing). This needs a targeted investigation:
- What URL is configured in Stripe Dashboard?
- Does FastAPI deduplicate handlers or would both fire?
- Is idempotency enforced at the handler level?

**Recommendation:** Elevate DEBT-324 from "1h fix" to "1h fix + 2h audit" to verify no data corruption has occurred from double-processing.

### Gap 2: Error Handling in Background Jobs

The DRAFT covers monolithic file sizes for `job_queue.py` (2152 LOC) and `cron_jobs.py` (2218 LOC) but does not assess error handling patterns within these files. Given ARQ has no runtime reconnection (documented in MEMORY.md), unhandled exceptions in background jobs could silently fail without retry. This is a reliability concern that the current debt assessment treats as a maintainability issue only.

### Gap 3: Redis Connection Resilience

No debt item covers Redis connection failure modes. The project uses Redis for cache, circuit breaker state, and rate limiting. If Redis becomes unavailable:
- Does the circuit breaker fail open or closed?
- Does rate limiting fail open (allow all) or closed (block all)?
- Are there Redis reconnection patterns in place?

This may already be handled (the project has extensive resilience work), but it was not assessed.

### Gap 4: API Proxy Security Headers

DEBT-315 covers proxy standardization but does not assess whether the 58 API proxies consistently forward security headers, validate content types, or enforce rate limits. A malformed proxy could bypass backend security controls.

### Gap 5: Migration Rollback Strategy

The DB specialist provides a forward migration plan but no rollback strategy. For the NOT NULL additions (DB-H04), what happens if production data has NULLs that the backfill misses? The migration should include a pre-check query count.

---

## 4. Riscos Cruzados

| Risco | Areas Afetadas | Severidade | Mitigacao |
|-------|---------------|------------|-----------|
| **Monolith decomposition breaks test imports** | Backend + Tests (143K LOC) | HIGH | Decompose one file at a time. Run full test suite after each. Use re-export facades during transition. |
| **Server Components migration breaks Framer Motion** | Frontend landing + marketing | MEDIUM | The "islands" approach from UX review is correct. Start with zero-hook components first. |
| **Dual webhook double-processing** | Billing + Subscriptions | HIGH | Audit Stripe Dashboard URL immediately. Add idempotency key check if not present. |
| **filter/core.py decomposition** | Search pipeline + 14 test files (3704 LOC of filter tests) | HIGH | This is the highest-regression-risk decomposition. The `filter/__init__.py` re-export pattern must be preserved. |
| **Feature flag cleanup removes active flags** | Backend + Frontend | MEDIUM | Inventory all flags with usage grep before removing any. Cross-reference frontend and backend usage. |
| **Cache eviction regression (DA-01) data loss** | User search cache | MEDIUM | The DB specialist's fix (restore priority ordering + limit 10) is correct. Test with production-like cache volumes. |

---

## 5. Dependencias Validadas

The DRAFT's proposed batch order (Section 7) needs revision:

### DRAFT Batch Order vs Recommended Batch Order

**DRAFT Batch 1** included DB-C01, DB-H01, DB-H03 (all RESOLVED). Must be replaced.

**Revised batch order:**

| Batch | Items | Hours | Rationale |
|-------|-------|-------|-----------|
| **0: Audit** | DEBT-324 (audit Stripe double-processing) | 2h | Must verify no data corruption before proceeding with other work |
| **1: Quick Wins** | DEBT-323 (plan cache LRU), DEBT-324 (remove dual registration), DB-H04 (NOT NULL), DB-M04+M05 (CHECK constraints), DA-01 (cache eviction), DEBT-325 (USD_TO_BRL) | 4h | All low-risk, high-value, independent fixes |
| **2: Landing Performance** | TD-M07 + TD-NEW-04 (landing RSC islands) | 10h | Highest ROI for user-facing impact (acquisition funnel) |
| **3: Security/A11y** | DEBT-307 (webhook decomp), TD-H04 (pipeline announcements), TD-NEW-01 (duplicate IDs), TD-NEW-02 (color-only badges) | 14h | Security audit + accessibility quick wins |
| **4: Architecture** | DEBT-301 (filter decomp), DEBT-304 (packaging) | 20h | Highest regression risk -- do after test infrastructure is solid |
| **5: Continued** | DEBT-302, DEBT-305, DEBT-309, TD-H01, TD-H02, remaining MEDIUM | ~50h | Iterative improvement |
| **6: Polish** | All LOW items | ~27h | Backlog, opportunistic |

**Key dependency corrections:**
- TD-M07 (landing RSC) does NOT depend on TD-H01 (protected RSC). They are independent. The DRAFT's dependency graph incorrectly chains them.
- DEBT-304 (packaging) should precede DEBT-301/302/305 (file decomposition). The DRAFT gets this right.
- DEBT-314 (feature flags) should precede XC-04 (FE/BE sync). The DRAFT gets this right.
- **New dependency:** DEBT-324 audit should precede DEBT-307 (webhook decomposition). No point decomposing a webhook handler that is being double-registered.

---

## 6. Testes Requeridos

### Batch 0 (Audit)
- Manual: Verify Stripe Dashboard webhook URL(s)
- Automated: Send test webhook event, verify handler executes exactly once (check log count)

### Batch 1 (Quick Wins)
- **DEBT-323:** Unit test for LRU eviction behavior -- insert 1001 entries, verify oldest is evicted. Test concurrent access with threading.
- **DEBT-324:** Integration test that webhook route responds at root path only, not at `/v1/` prefix. Verify with `TestClient`.
- **DB-H04:** Migration test with NULL backfill verification: `SELECT COUNT(*) FROM classification_feedback WHERE created_at IS NULL` should return 0 after migration.
- **DB-M04+M05:** Negative tests: INSERT with invalid `response_state` / `pipeline_stage` values should raise CHECK violation.
- **DA-01:** Cache eviction test: insert 11 entries with mixed priorities, verify cold entries evicted first. Verify hot entries survive.
- **DEBT-325:** Config test: verify `USD_TO_BRL` is read from env var with fallback to 5.0.

### Batch 2 (Landing Performance)
- Lighthouse CI check: LCP < 2.5s, TTFB < 800ms for landing page
- Visual regression test with Playwright screenshot comparison
- Verify Framer Motion animations still function in client islands
- Bundle size check: verify client JS reduction of 40-60KB gzipped

### Batch 3 (Security/A11y)
- **DEBT-307:** Each webhook event type gets its own handler test. Regression: replay all existing Stripe webhook tests against new handler structure.
- **TD-H04:** Playwright a11y test: Tab to pipeline card, Space to pick up, arrow to move, Space to drop. Verify `aria-live` announcement text.
- **TD-NEW-01:** DOM validation test: no duplicate IDs on any page. Can use `jest-axe` or Playwright `page.$$eval('[id]', ...)`.
- **TD-NEW-02:** Visual test: viability badges render text labels alongside color indicators.

### Batch 4 (Architecture)
- **CRITICAL: Full test suite must pass before AND after each file decomposition.**
- **DEBT-301:** Run all 14 filter test files (3704 LOC). Verify `from filter import X` still works via `__init__.py` re-exports.
- **DEBT-304:** After each package creation, run `python -c "from <package> import <key_function>"` to verify import paths.
- Snapshot test: verify OpenAPI schema does not change after internal refactoring.

---

## 7. Respostas ao Architect

### Q1: DEBT-311 -- Does test/source ratio of 1.8x indicate over-specification?

**Answer: No, but it warrants targeted review.**

The measured ratio is 143.8K test LOC / 76.7K source LOC = 1.87x. This is within normal range for a production system with the following characteristics:
- Multiple data sources requiring extensive mocking (PNCP, PCP, ComprasGov)
- Financial/billing logic requiring edge case coverage (Stripe webhooks, quota, trial)
- Resilience patterns requiring failure mode testing (circuit breakers, cache fallback, SSE)

Industry benchmarks for well-tested Python projects:
- Django: ~1.5x
- FastAPI production systems: ~1.5-2.5x
- Financial/billing systems: ~2.0-3.0x

**1.87x is not over-specification.** However, two areas warrant audit:

1. **Filter tests (3704 LOC across 14 files)** vs filter source (3871 LOC in core.py + 4332 LOC in filter_*.py = ~8200 LOC). The test-to-source ratio for filtering is 0.45x -- actually under-tested relative to the codebase average.

2. **Potential duplication:** Some test files may test the same behavior at different integration levels (unit test in `test_filter_keywords.py` + integration test in `test_filter.py` + E2E in `test_main.py`). This is acceptable redundancy (defense in depth), not over-specification. An audit would take ~4h and could identify ~2h of consolidation savings -- not worth the investment at this stage.

**Recommendation:** Keep current ratio. Do not reduce tests. The 1.87x ratio provides a safety net that is essential given the upcoming Batch 4 decomposition work.

### Q2: Which debts have highest regression risk if resolved?

**Ranked by regression risk:**

| Rank | Debt | Risk Level | Why |
|------|------|-----------|-----|
| 1 | **DEBT-301** (filter/core.py decomp) | **CRITICAL** | 3871 LOC, 14 test files, core search pipeline. Any import path change breaks 654+ test lines in `test_filter.py` alone. The `filter/__init__` re-export pattern means all consumers use `from filter import X` -- this MUST be preserved. |
| 2 | **DEBT-307** (Stripe webhook decomp) | **HIGH** | 1192 LOC handling 10+ event types, all affecting billing state. Wrong decomposition could cause missed webhook events, failed subscription activations, or double charges. |
| 3 | **DEBT-302** (schemas.py decomp) | **HIGH** | 2121 LOC of Pydantic models used by every route. Import path changes cascade to all 49 endpoints. |
| 4 | **DEBT-304** (backend packaging) | **HIGH** | Meta-change that restructures imports for 68 files. Must be done incrementally, not as a big-bang. |
| 5 | **TD-M07** (landing RSC) | **MEDIUM** | Risk of breaking animations or layout. Mitigated by visual regression tests. |
| 6 | **DEBT-324** (dual webhook) | **MEDIUM** | Removing the `/v1/` registration could break clients if any external system uses that path. |

**Recommendation:** For ranks 1-4, use the "facade preservation" pattern -- create new package structure, move code, but keep re-export `__init__.py` files so existing imports continue to work. This is exactly what was done for `filter/` (except the actual decomposition of `core.py` was never completed). Validate with the full test suite (7656 passing tests) after each file move.

### Q3: Is current test coverage (70% BE, 60% FE) adequate for the debt areas?

**Backend (70%): Adequate for most debt areas, with gaps.**

The 70% overall coverage is acceptable, but coverage is likely unevenly distributed. The monolithic files being decomposed (filter, schemas, webhooks) probably have high coverage because they are core functionality. The risk areas are:
- **Background jobs (job_queue.py, cron_jobs.py):** These are hard to test and likely under-covered. ARQ mocking complexity contributes to this.
- **Error paths in search pipeline:** Timeout chains, partial failures, circuit breaker state transitions. These are tested but coverage may be thin.

**Frontend (60%): Below ideal for the planned changes.**

60% is adequate for current production, but the landing page RSC migration (TD-M07) and accessibility fixes (TD-H04, TD-NEW-01, TD-NEW-02) will touch UI-critical paths. Recommended:
- Add Lighthouse CI for landing page metrics before TD-M07 work begins
- Add `jest-axe` integration (TD-L01) before TD-H04/TD-NEW-01/TD-NEW-02 work begins
- Target 65% frontend coverage by end of debt resolution sprint

**Verdict:** Coverage is adequate to begin Batches 0-2 safely. Before starting Batch 4 (architecture decomposition), ensure the specific files being decomposed have >80% line coverage. Run `pytest --cov=filter --cov-report=term-missing` to identify gaps.

### Q4: Should the 12 scripts in `scripts/` have CI tests?

**Answer: Selective, not comprehensive.**

The 12 scripts in `backend/scripts/` and 57 scripts in `scripts/` (project root) fall into categories:

| Category | Examples | CI Tests? | Rationale |
|----------|----------|-----------|-----------|
| **Data enrichment** (one-time) | `enrich-*.py`, `build-*.py` | No | These are run-once data processing scripts. Testing them in CI adds maintenance burden for throwaway code. |
| **Audit/diagnostic** | `audit_*.py`, `sector_diagnostic.py` | No | Read-only scripts that import from backend modules. If the backend modules break, the existing backend tests catch it. |
| **Operational** | `run_tests_safe.py`, `sync-setores-fallback.js` | Yes | These affect CI/CD pipeline reliability. `run_tests_safe.py` is the primary Windows test runner. |
| **Data sync** | `search-contracts-cnpj.py`, `parse_pncp.py` | Smoke test only | These interact with external APIs. A dry-run smoke test (verify import + argument parsing) is sufficient. |

**Recommendation:** Add CI smoke tests for the 2-3 operational scripts only. Do not add tests for one-time enrichment scripts. Total effort: ~1h (not the 2h in the DRAFT). DEBT-319 effort should be reduced to 1h.

### Q5: Testing strategy for Server Components migration (TD-H01 / TD-M07)?

**Answer: Four-layer strategy.**

1. **Build verification (automated, CI):** `npm run build` must succeed. Server Components that accidentally import client-only modules (Framer Motion, useState) will fail at build time. This is the strongest safety net and is already in CI.

2. **Visual regression (Playwright):** Before starting TD-M07, capture baseline screenshots of the landing page at 3 breakpoints (mobile 375px, tablet 768px, desktop 1440px). After conversion, compare pixel-by-pixel. Acceptable diff threshold: < 1%.

3. **Performance validation (Lighthouse CI):** Add Lighthouse CI check for landing page only. Thresholds:
   - LCP < 2.5s (currently likely >3s due to full client rendering)
   - TTFB < 800ms
   - Total Blocking Time < 200ms
   - CLS < 0.1

4. **Hydration boundary tests (unit):** For each client island created during the conversion, write a test that:
   - Renders the component in isolation
   - Verifies it accepts `children` (for the wrapper pattern)
   - Verifies Framer Motion animations trigger correctly

**Estimated test effort for RSC migration: 4h** (included in the 10h estimate for TD-M07).

**Key risk:** The `"use client"` boundary is a compile-time concept in Next.js. If a Server Component accidentally imports a client module, the build fails immediately. This makes RSC migration one of the safest refactoring patterns -- errors are caught at build time, not runtime.

---

## 8. Parecer Final

### Overall Assessment

The Technical Debt Assessment is **thorough and actionable** after incorporating specialist corrections. The 18% error rate in the DRAFT is concerning but expected for a first-pass assessment of a 56-item audit. The specialist review process (Phases 5-6) caught all material errors, which validates the multi-phase workflow design.

### Key Strengths

1. **Comprehensive coverage:** 56 items across 4 categories (system, database, frontend, cross-cutting) with effort estimates and dependency mapping.
2. **Pragmatic prioritization:** Quick wins correctly identified. The batch ordering (after corrections) follows a sensible risk-adjusted sequence.
3. **Specialist reviews added value:** DB review saved ~1.7h of wasted effort on resolved items. UX review corrected 20h of misestimated work and identified 3 new items the architect missed.

### Key Weaknesses

1. **Stale data collection (process):** 3 CRITICAL/HIGH items were already resolved. Future assessments must verify against live migration state.
2. **DEBT-314 overestimated (data):** 40+ feature flags claimed, only 16 found. The effort estimate for flag cleanup should be halved.
3. **No security deep-dive:** DEBT-324 (dual webhook registration) needs an audit before remediation, not just a 1h fix.
4. **Missing Redis resilience assessment:** No debt item covers Redis failure modes despite Redis being critical infrastructure.

### Recommendations

1. **Proceed to Phase 8** (final assessment) -- the DRAFT has sufficient quality for planning after corrections are applied.
2. **Priority zero:** Audit DEBT-324 (dual Stripe webhook) for evidence of double-processing in production logs.
3. **Update the DRAFT** with all corrections from DB specialist review (Section "Corrections to DRAFT"), UX specialist review (adjusted severities/hours), and this QA review (DEBT-314 adjustment, Batch 0 addition).
4. **Add a "Resolved" section** to the final assessment documenting DB-C01, DB-H01, DB-H03, DB-L02, TD-M09 -- these demonstrate that prior debt sprints were effective.
5. **Do not start Batch 4** (architecture decomposition) until Batches 0-2 are complete and the test suite is verified stable.

### Revised Totals for Planning

| Metric | DRAFT | After All Reviews |
|--------|-------|-------------------|
| Total open debts | 56 | 47 (9 resolved/removed) + 7 new = 54 |
| CRITICAL | 2 | 1 |
| HIGH | 12 | 8 |
| Total effort | ~246h | ~196h |
| Quick wins (Batch 0+1) | ~5h | ~6h (added audit) |
| DB effort | ~4h | ~2.3h |
| Frontend effort | ~88h | ~68h |

---

*Phase 7 QA Review complete. The assessment is APPROVED for finalization in Phase 8.*
