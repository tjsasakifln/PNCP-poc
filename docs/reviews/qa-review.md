# QA Review --- Technical Debt Assessment

**Reviewer:** @qa (Guardian)
**Date:** 2026-03-04
**Documents Reviewed:** DRAFT v2.0, db-specialist-review.md v2.0, ux-specialist-review.md v2.0, system-architecture.md v4.0, DB-AUDIT.md
**Supersedes:** qa-review.md v1 (2026-02-25) -- complete rewrite against DRAFT v2.0 and updated specialist reviews
**Validation Method:** Cross-referenced all specialist reviews against each other and the live codebase via automated grep/glob. Verified 6 specific claims independently.

---

## Gate Status: APPROVED WITH CONDITIONS

The assessment is comprehensive and ready for planning, subject to 4 conditions documented in the Parecer Final section. The specialist reviews are high-quality, evidence-based, and largely non-contradictory. The remaining issues are corrections and missing test coverage considerations that can be addressed during planning rather than requiring another review cycle.

---

## Assessment Completeness

**Overall: STRONG.** The three-phase approach (architect consolidation, DB specialist review, UX specialist review) covered the codebase thoroughly. The DRAFT identified 63 debts, adjusted to 66 after specialist additions (3 DB: DA-01/02/03, 4 FE: FE-39/40/41/42) minus 1 removal (FE-18).

**Coverage by area:**

| Area | Codebase Size | Debts Identified | Coverage Assessment |
|------|---------------|------------------|---------------------|
| Backend (73 modules, 31 route modules) | 73+ files | 24 | Good -- core modules well-analyzed |
| Database (66 migrations, 32 tables) | 98 entities | 26 (23 original + 3 added by DB specialist) | Excellent -- migration-level verification |
| Frontend (33 pages, 80+ components) | 113+ files | 41 (38 - 1 removed + 4 added by UX specialist) | Good -- component-level verification |
| CI/CD (17 workflows) | 17 workflows | 4 (TD-M02/M03/M04, FE-21) | Adequate |
| Infrastructure | 3 Railway services | 5 (TD-S01-S05) | Adequate |

**What was NOT assessed (see Gaps section):**
- E2E test coverage gaps
- Observability/monitoring completeness
- Dependency vulnerability scanning
- Backend test isolation debt

---

## Gaps Identificados

### GAP-01: TD-S05 is Already Fixed -- MUST REMOVE from DRAFT

The DRAFT lists `time.sleep(0.3)` in quota.py as a MEDIUM debt (Tier 0, item #3, estimated 1h). The DB specialist review (line 298) notes "Already verified as fixed in v1 review -- `asyncio.sleep(0.3)` used everywhere."

**Independent verification:** Grep confirms quota.py uses `await asyncio.sleep(0.3)` in all 3 occurrences (lines 1467, 1557, 1624). Zero instances of `time.sleep` exist in the file.

**Action:** Remove TD-S05 from Tier 0. This frees 1h from the estimate.

### GAP-02: UX Specialist Minor Inaccuracy on /features Page

The UX specialist states (FE-18 justification): "Only `/planos` and `/features` are CSR, which is acceptable since they require client interactivity."

**Independent verification:** `/features/page.tsx` does NOT have `"use client"` -- it is already a Server Component. Only `/planos/page.tsx` and `/planos/obrigado/page.tsx` are CSR. This does not affect the FE-18 removal decision (which is correct), but should be noted for accuracy in the final document.

### GAP-03: No E2E Test Debt Tracked

The codebase has 290 backend test files, 268 frontend test files, and 20 E2E spec files covering 33 pages. Critical user flows including MFA setup, organization management, alert creation, and partner referrals have no E2E coverage. This gap is not tracked as a debt in any document.

### GAP-04: No Observability/Monitoring Debt Tracked

The assessment does not evaluate completeness of Prometheus metrics, OpenTelemetry spans, or Sentry coverage against the 60+ endpoints. For example: are all 7 pipeline stages instrumented? Are circuit breaker state changes consistently tracked across all 3 data sources? Is the ARQ worker adequately instrumented? These become important as the product moves from beta to revenue.

### GAP-05: No Dependency Vulnerability Audit

Neither the DRAFT nor specialist reviews mention dependency security scanning. The `requirements.txt` pins most versions, but there is no `pip-audit` or `npm audit` in any of the 17 CI workflows. This is a security debt that should be tracked alongside TD-SEC01-04.

### GAP-06: Backend Test Isolation Debt Not Tracked

MEMORY.md documents extensive test pollution patterns: `sys.modules` MagicMock injection without cleanup, `importlib.reload` leaving modules in altered state, SimpleNamespace requirements for Pydantic compatibility, global singleton leaks (supabase_cb). The UX specialist identified FE-41 (no hook isolation tests) as a frontend testing debt, but the backend equivalent (fragile test fixtures, mock pattern inconsistencies documented across 6+ MEMORY entries) was not captured.

---

## Riscos Cruzados

| # | Risco | Areas Afetadas | Probabilidade | Impacto | Mitigacao |
|---|-------|----------------|---------------|---------|-----------|
| R-01 | FE-01 (SearchResults decomp) breaks existing 268 frontend tests | Frontend tests, E2E | HIGH | HIGH | Run full test suite after each sub-component extraction. Create snapshot tests for rendered output before decomposition starts. |
| R-02 | FE-03 (useSearch decomp) + FE-08 (SWR adoption) compound breakage of SSE integration | Frontend, Backend SSE | HIGH | CRITICAL | The SSE dual-connection pattern is the most fragile integration point. Decomposing useSearch while simultaneously adopting SWR creates compounding risk. Resolve FE-03 FIRST, stabilize with tests, THEN adopt SWR. Never in parallel. |
| R-03 | C-01 (FK re-pointing to profiles) with live beta users | Database, Backend | MEDIUM | HIGH | The NOT VALID + VALIDATE pattern mitigates lock contention, but the pre-migration orphan detection query is essential. Run during low-traffic window (1am BRT / 4am UTC). |
| R-04 | TD-A01 (remove legacy routes) breaks unknown API consumers | Backend, external consumers | LOW | MEDIUM | The DRAFT states frontend already uses versioned endpoints. Verify via Railway access logs for non-/v1/ API calls before removal. Add deprecation metric counter first. |
| R-05 | FE-27 (Button via Shadcn/ui) requires Tailwind config changes | Frontend build, all pages | MEDIUM | MEDIUM | Shadcn initialization modifies `tailwind.config.js` and `globals.css`. Test full build + visual regression on all 33 pages after setup. |
| R-06 | Migration 3 (RLS policy standardization, 8 tables) typo in one of 8 statements | Database, Backend | LOW | HIGH | Both `auth.role()` and `TO service_role` work today. Mitigate with staging test before production apply. |
| R-07 | TD-A02 (search_pipeline refactor) + TD-A03 (progress tracker to Redis) change core business logic simultaneously | Backend, Frontend SSE, E2E | MEDIUM | CRITICAL | These are the two highest-risk refactors. Consider decoupling -- pipeline refactoring (code organization) does not inherently require changing the progress tracking mechanism. See dependency validation below. |
| R-08 | H-03 pg_cron DELETE during peak hours causes lock contention | Database, search availability | LOW | MEDIUM | DB specialist recommends 4am UTC = 1am BRT. Outside peak Brazilian business hours. Acceptable. |

---

## Contradicoes Entre Especialistas

### No Major Contradictions Found

The DB and UX specialist reviews are cleanly separated by domain with no overlapping or conflicting claims. Three severity adjustments and one removal were made:

### C-02 Downgrade: CRITICAL to HIGH -- APPROPRIATE

- **DB-AUDIT.md (original):** CRITICAL -- "RLS enabled but ZERO policies"
- **DB Specialist Review:** Downgraded to HIGH
- **Assessment:** The downgrade is appropriate. Three concrete justifications provided: (1) both tables are backend-only append logs with no PII, (2) service_role bypass is the intended and only access pattern, (3) no client-side status page planned. The defense-in-depth recommendation (add explicit service_role policies) is the right action. This is a hardening item, not a security vulnerability.

### H-04/05/06 Downgrade: HIGH to MEDIUM -- APPROPRIATE

- **DB-AUDIT.md (original):** HIGH
- **DB Specialist Review:** Downgraded to MEDIUM -- "functionally equivalent, consistency debt not security debt"
- **Assessment:** Appropriate. The `auth.role()` pattern works correctly in Supabase PostgreSQL 17. The theoretical risk (Supabase JWT structure change) is low probability. Classifying as MEDIUM consistency debt is accurate.

### FE-22 Downgrade: HIGH to LOW -- APPROPRIATE

- **DRAFT:** HIGH -- "Hardcoded Portuguese strings in 44 pages, sem i18n"
- **UX Specialist:** Downgraded to LOW -- "product is 100% BR, pre-revenue, no international plans"
- **Assessment:** Appropriate and well-justified. Domain-specific terms (licitacao, edital, pregao, CNPJ) have no direct translations. 24-40h effort for zero revenue impact is premature optimization. Note: if product ever targets Portuguese-speaking African markets (Angola, Mozambique), procurement terminology differs. Future consideration, not current debt.

### FE-18 Removal -- CORRECT AND VERIFIED

- **DRAFT:** Listed as HIGH, Tier 1, 8-12h
- **UX Specialist:** REMOVED -- "all blog/SEO pages are already Server Components"
- **Verification:** Grep confirms no `"use client"` in `/blog/*`, `/licitacoes/*`, `/como-*`. The DRAFT Section 7 dependency graph lists FE-18 as independent with no dependents, so its removal does not break the graph. Tier 1 total should be reduced by 8-12h.

---

## Dependencias Validadas

### DRAFT Dependency Graph (Section 7) -- Post-Specialist Status

```
C-01 (FK standardization) --- bloqueia --> H-02 (search_results_store FK)
                                       --> M-03 (partner_referrals FK)
STATUS: VALID. DB specialist confirms H-02 and M-03 are subsumed by C-01.
        DB specialist ADDS: DA-02 (search_results_store policy) can batch.

TD-A01 (remover legacy routes) --- habilita --> TD-M02 (API contract validation)
STATUS: VALID. Cannot validate contract drift while legacy routes exist.

FE-01 (SearchResults decomp) --- requer --> FE-10 (eliminar prop drilling)
                              --- requer --> FE-06 (Button component)
                              --- requer --> FE-27-30 (design primitives)
STATUS: PARTIALLY VALID.
  - FE-10 prerequisite: CORRECT (confirmed by UX specialist).
  - FE-06 and FE-27: DUPLICATE IDs for same debt. UX specialist clarifies
    FE-27 should precede FE-01 (new components use shared Button from day one).
  - FE-28-30: NOT required before FE-01. Nice-to-have, not blocking.

FE-03 (useSearch decomp) --- requer --> FE-08 (data fetching library)
STATUS: *** INVERTED *** This is the most significant dependency error.
  The UX specialist explicitly recommends FE-03 BEFORE FE-08:
  decompose useSearch first, then adopt SWR into the decomposed hooks.
  Correct order: FE-03 -> FE-08 (not FE-08 -> FE-03).

FE-18 (SSG/ISR) --- independente
STATUS: REMOVED (FE-18 no longer exists). No impact on graph.

TD-A02 (pipeline refactor) --- requer --> TD-A03 (progress tracker Redis)
STATUS: QUESTIONABLE. Pipeline refactoring (extracting stages into modules)
  does not inherently require changing the progress tracking implementation.
  These CAN be decoupled. TD-A02 should depend on TD-A03 only if the
  refactoring also restructures progress tracking. Recommend treating as
  independent to reduce compounding risk (see R-07).
```

### Hidden Dependencies Discovered

| Dependency | Source | Impact |
|------------|--------|--------|
| FE-27 (Button) must precede FE-01 (SearchResults decomp) | UX specialist line 332 | Decomposed sub-components should use shared Button from day one |
| L-06 (composite index) must precede H-03 (retention job) | DB specialist dependency graph | DELETE performance requires (user_id, expires_at) index |
| M-02 (created_at index) must precede M-04/05/06 retention jobs | DB specialist dependency graph | Cleanup queries need efficient index path |
| FE-41 (hook isolation tests) should precede FE-03 (useSearch decomp) | Logical dependency | Cannot safely decompose 1,510-line hook without tests as safety net |
| GAP-05 (dependency audit) should precede new dependency additions | Logical dependency | FE-08 (SWR adoption) adds a dependency -- should audit existing deps first |

---

## Ajustes de Estimativa

### Items Requiring Adjustment

| ID | DRAFT Estimate | Specialist Estimate | QA Assessment | Rationale |
|----|---------------|---------------------|---------------|-----------|
| TD-S05 | 1h | N/A (already fixed) | **0h -- REMOVE** | Verified: quota.py already uses asyncio.sleep in all 3 locations. |
| C-01 | 4h | 6h (DB specialist) | **6-8h** | DB specialist's 6h includes writing + staging + verification + deploy. Add 2h buffer for orphan detection across 6 tables and ON DELETE decisions. |
| FE-18 | 8-12h | 0h (removed by UX) | **0h -- REMOVE** | Verified: all blog/SEO pages are Server Components. |
| FE-01 | 12-16h (DRAFT) | 14-18h (UX) | **14-18h** | UX specialist's estimate realistic for 1,581 lines and ~55 props. |
| FE-03 | 12-16h (DRAFT) | 14-18h (UX) | **14-18h** | 1,510-line hook with SSE, retry, export, and persistence logic. |
| FE-08 | 16-24h (DRAFT) | 16-20h (UX) | **20-28h** | Both estimates optimistic. SWR migration touches 15+ hooks/components with raw fetch. Add 4-8h for SSE integration testing. |
| M-01 | 4h (DRAFT) | 1.5h (DB specialist) | **1.5h** | DB specialist correctly identified append-only tables do not need updated_at. 11 tables reduced to 3. |
| M-07 | 2h (DRAFT) | 3h (DB specialist) | **3h** | Integration test + CI guard + canonical comment. Breakdown is detailed and realistic. |
| TD-A02 | 16-24h (DRAFT) | N/A | **24-32h** | DRAFT underestimates. 800-line god module with inline helpers. The 290 backend test files likely have significant coupling to current pipeline structure. Need test coverage before AND after. |
| FE-41 | 8-12h (UX added) | N/A | **12-16h** | Writing isolated tests for 1,510-line hook requires mock infrastructure for SSE, fetch, localStorage, timers. Prerequisite for FE-03. |

### Revised Tier Totals

| Tier | DRAFT Estimate | After All Adjustments |
|------|---------------|-----------------------|
| Tier 0 | ~16h | **~14h** (remove TD-S05 1h, adjust C-01 to 6h) |
| Tier 1 | ~97-146h | **~105-155h** (remove FE-18 8-12h, increase FE-01/03/08, add FE-41 as prerequisite) |
| Tier 2 | ~87-125h | **~85-120h** (minor adjustments, M-01 reduced) |
| Tier 3 | ~65-85h | **~65-85h** (unchanged) |
| **Subtotal (code changes)** | **~265-372h** | **~269-374h** |
| **Testing effort (NEW)** | Not estimated | **~59.5h** (see Testes Requeridos section) |
| **Grand Total** | **~265-372h** | **~328-434h** |

---

## Testes Requeridos Pos-Resolucao

### Tier 0 (Quick Wins) -- ~6h testing effort

| Debt Resolved | Required Tests | Type | Est. |
|---------------|---------------|------|------|
| C-01 (FK re-pointing, 6 tables) | Orphan detection query pre-migration; verify CASCADE on user deletion for all 6 tables; verify ON DELETE SET NULL for partner_referrals.referred_user_id | DB integration | 2h |
| C-02 (RLS policies for health_checks, incidents) | Verify service_role can read/write; verify authenticated role denied | DB integration | 0.5h |
| H-03 (search_results_store retention) | Insert expired rows, run cleanup, verify deletion; verify non-expired preserved; EXPLAIN ANALYZE on DELETE query | DB integration | 1h |
| H-01 (trigger consolidation) | Verify updated_at fires on UPDATE for pipeline_items, alert_preferences, alerts after switching to shared function | DB integration | 0.5h |
| H-04/05/06 + DA-01/02 (policy standardization, 8 tables) | Verify service_role access on all 8 tables after policy replacement; verify authenticated denied where expected | DB integration | 1h |
| FE-12 + FE-13 (aria-labels, aria-hidden) | Axe accessibility audit on sidebar; verify all icon-only buttons have aria-label | Frontend unit + a11y | 0.5h |
| TD-P03/04 (branding fix) | Verify User-Agent in PNCP requests; grep for "BidIQ" to confirm removal | Backend unit | 0.5h |

### Tier 1 (Structural) -- ~35h testing effort

| Debt Resolved | Required Tests | Type | Est. |
|---------------|---------------|------|------|
| TD-A01 (remove legacy routes) | Verify all /v1/ endpoints return 200; verify non-/v1/ returns 404 or redirect; monitor production logs for 404 spike post-deploy | Backend integration + E2E + monitoring | 4h |
| FE-01 (SearchResults decomp) | Snapshot tests per sub-component; verify prop types; all existing SearchResults tests pass against new structure; visual regression on results page | Frontend unit + E2E | 4h |
| FE-03 (useSearch decomp) | Isolated hook tests for each decomposed hook; SSE integration end-to-end; retry logic; export functionality | Frontend unit + integration | 6h |
| FE-08 (SWR adoption) | Cache behavior; revalidation; error handling; SSE hooks alongside SWR; all migrated endpoints return correct data | Frontend integration | 4h |
| FE-10 (prop drilling elimination) | Grouped prop objects pass type checks; no runtime undefined errors; component rendering with partial props | Frontend unit | 2h |
| TD-A02 (pipeline refactor) | Full 290-file backend suite must pass; search flow E2E; SSE progress events; cache behavior; response time benchmarks (no regression) | Backend full suite + E2E + perf | 8h |
| TD-A03 (Redis Streams progress) | SSE events delivered via Redis Streams; fallback to in-memory when Redis down; multi-instance progress sharing; heartbeat timing | Backend integration + E2E | 4h |
| TD-S01 (memory optimization) | Memory profiling before/after; no OOM under concurrent searches; shared caches work across workers | Backend performance | 3h |

### Tier 2 (Quality) -- ~18.5h testing effort

| Debt Resolved | Required Tests | Type | Est. |
|---------------|---------------|------|------|
| FE-27-32 (design system primitives) | Visual regression on all pages using new components; dark mode; responsive behavior | Frontend visual + unit | 6h |
| TD-A05 (eliminate dual PNCP client) | PNCP fetching with async-only client; fallback behavior; circuit breaker; retry logic | Backend integration | 3h |
| TD-P02 (feature flags UI) | Flag toggle works; cache invalidation; no restart required; admin-only access | Backend integration + E2E | 2h |
| M-04/05/06 + DA-03 (retention jobs, 4+ tables) | Each job deletes correct age range; no premature deletion; staggered scheduling works | DB integration | 1.5h |
| FE-13/14/15/17 (accessibility) | Axe audit on affected pages; ARIA live regions announce progress; form labels present | Frontend a11y | 2h |
| FE-19 (dynamic imports) | Lazy-loaded components render correctly; loading states work; bundle size reduction verified | Frontend perf | 1h |
| TD-M02 (API contract CI) | CI fails when backend schema drifts from frontend types; passes when in sync | CI pipeline | 1h |
| FE-33 (navigation unification) | Visual regression on search page with new nav; all navigation links work; responsive behavior | Frontend unit + visual | 2h |

---

## Testing Debts (novos)

The following testing gaps should be tracked as new debts:

| ID | Debt | Severity | Area | Est. Effort | Rationale |
|----|------|----------|------|-------------|-----------|
| TD-T01 | **No E2E coverage for MFA, organizations, alerts, partners** | MEDIUM | E2E | 12-16h | 20 E2E spec files cover core flows only. 4 major feature areas have zero E2E coverage. |
| TD-T02 | **Backend test pollution patterns** (sys.modules MagicMock, singleton leak, importlib.reload) | MEDIUM | Backend tests | 8-12h | Documented in MEMORY.md as recurring flaky test source. Conftest fixtures partially mitigate but patterns not enforced. Root cause of historical test count discrepancies. |
| TD-T03 | **No hook isolation tests for 19 custom hooks** (= FE-41, already identified by UX specialist) | MEDIUM | Frontend tests | 12-16h | useSearch (1,510 lines) has zero isolated tests. Prerequisite for safe FE-03 decomposition. |
| TD-T04 | **No visual regression testing infrastructure** | LOW | Frontend tests | 8h | No Chromatic, Percy, or Playwright screenshot comparison. Design system adoption (FE-27-32) without visual regression creates blind spots. |
| TD-T05 | **No dependency security scanning in CI** | MEDIUM | CI | 2h | No `pip-audit`, `npm audit`, or Snyk in any of 17 workflows. |
| TD-T06 | **No load/stress testing baseline** | LOW | Backend | 4h | Locust workflow exists (`load-test.yml`) but is manual-only. No automated baseline or regression detection. |

---

## Parecer Final

### APPROVED FOR PLANNING -- Subject to 4 Conditions

**Condition 1: Remove TD-S05 from Tier 0.**
It is already fixed. Verified: `asyncio.sleep` in all 3 occurrences in quota.py. Including a resolved debt wastes sprint capacity on investigation.

**Condition 2: Correct the FE-03 / FE-08 dependency direction in DRAFT Section 7.**
The DRAFT states FE-03 requires FE-08. The UX specialist correctly states the inverse: decompose useSearch (FE-03) first, then adopt SWR (FE-08) into the decomposed hooks. The dependency graph must be updated before planning to avoid executing these in the wrong order. Correct chain: FE-41 (hook tests) -> FE-03 (decompose) -> FE-08 (adopt SWR).

**Condition 3: Add FE-41 (hook isolation tests) as explicit prerequisite for FE-03.**
Decomposing a 1,510-line hook without test coverage is high-risk. The UX specialist identified this debt (8-12h) but did not mark it as a blocker for FE-03. It must be sequenced: FE-41 -> FE-03 -> FE-08.

**Condition 4: Acknowledge testing effort in sprint planning.**
Tier 0/1/2 resolutions require approximately 59.5h of testing effort (6h + 35h + 18.5h) that is not included in the DRAFT's estimates. The total effort including testing is approximately 328-434h, not 265-372h. Sprint planning that ignores this will systematically underestimate velocity.

### Overall Quality Assessment

The Brownfield Discovery v2 process produced a thorough, well-structured assessment. The three-phase specialist review model (architect consolidation, DB specialist, UX specialist) provides strong separation of concerns with appropriate cross-references. Both specialist reviews are evidence-based: DB specialist verified every claim against actual migration SQL files; UX specialist validated line counts and prop counts against the live codebase.

The prioritization into 4 tiers is sound. Tier 0 items are genuinely quick wins with security/stability impact. Tier 1 items correctly target the highest-impact structural debts. All four specialist severity adjustments (C-02, H-04/05/06, FE-22, FE-18) are well-justified and improve accuracy.

The primary risk for planning is the compounding effect of Tier 1 frontend refactors: FE-01 + FE-03 + FE-08 + FE-10 represent 60-80h of interconnected changes to the core search experience. These must be sequenced carefully with mandatory test stabilization gates between each item, not parallelized.

**Recommendation:** Proceed to FINAL v3.0 consolidation by the architect, incorporating the 4 conditions above and the 6 new testing debts (TD-T01 through TD-T06).

---

*Review completed 2026-03-04 by @qa (Guardian).*
*Methodology: Cross-referencing all specialist reviews against each other and the live codebase via automated search. Independently verified: TD-S05 fix status (3 grep hits confirm asyncio.sleep), FE-18 removal validity (0 "use client" in blog/SEO pages), /features CSR claim (Server Component confirmed), dependency graph consistency (FE-03/FE-08 inversion identified), test file counts (290 backend, 268 frontend, 20 E2E).*
