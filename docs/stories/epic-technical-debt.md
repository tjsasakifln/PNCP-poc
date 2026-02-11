# Epic: Technical Debt Resolution
## SmartLic/BidIQ - Brownfield Remediation

**Epic ID:** EPIC-TD
**Created:** 2026-02-11
**Supersedes:** TDE-001 (January 26, 2026 -- original 28-item assessment, now obsolete)
**Owner:** @pm (Morgan)
**Source:** `docs/prd/technical-debt-assessment.md` (FINAL, 2026-02-11)
**Commit Baseline:** `808cd05` (branch `main`)
**Approved By:** @architect (Aria), @data-engineer (Dara), @ux-design-expert (Uma), @qa

---

### Summary

This epic covers the systematic resolution of 90 technical debt items identified during a comprehensive brownfield discovery of SmartLic/BidIQ at commit `808cd05`. The system is a production SaaS (POC v0.3) for automated procurement opportunity discovery from Brazil's PNCP, with live users and Stripe billing. While functional, the system carries significant debt accumulated during rapid feature growth across architecture, database, frontend, and testing dimensions.

The 90 items span 5 categories:
- **System/Architecture:** 23 items (monolithic main.py, dual ORM, in-memory state)
- **Database:** 24 items (security policies, missing indexes, competing Stripe handlers)
- **Frontend/UX:** 33 items (monolithic page, accessibility gaps, price divergence)
- **Cross-Cutting:** 5 items (ORM consolidation, Excel storage, test failures)
- **Testing:** 5 items (undocumented strategies, missing test suites)

Resolution is organized into 4 sprints over 8 weeks, prioritized by security impact, architectural risk, and user trust.

---

### Business Justification

**From the executive assessment:**

The total estimated investment is 320-456 hours (~R$45K at blended rate). Failure to address these debts exposes the business to:

- **Security risk (R$50-100K):** Overly permissive RLS policies, admin policy checking wrong column, exposed backend URLs
- **Data integrity risk (R$50-100K):** Competing Stripe webhook handlers causing plan_type drift, dual ORM with broken SQLAlchemy URL
- **User trust risk (R$25-50K):** Divergent prices on different pages, broken dark mode on error pages, native alert() dialogs
- **Scaling risk (R$25-50K):** In-memory SSE state, temporary filesystem Excel storage, monolithic 1,959-line main.py
- **Development velocity risk:** 91 pre-existing test failures masking regressions, non-functional CI quality gates

**Total risk exposure:** R$100-250K in potential lost revenue, security incidents, and development slowdown.

**ROI:** R$45K investment to mitigate R$100-250K risk = 2.2-5.5x return.

---

### Scope

- **Total Items:** 90
- **Total Effort:** 320-456 hours
- **Duration:** 8 weeks (4 sprints)
- **Severity Breakdown:** 13 CRITICAL, 19 HIGH, 35 MEDIUM, 23 LOW

---

### Stories

| Story ID | Title | Sprint | Priority | Effort | Dependencies |
|----------|-------|--------|----------|--------|--------------|
| STORY-200 | Security and Trust Foundation | Sprint 1 (Week 1) | P0 | 20-28h | None |
| STORY-201 | Architecture Unification | Sprint 2 (Weeks 2-3) | P1 | 48-72h | STORY-200 |
| STORY-202 | Monolith Decomposition and Quality | Sprint 3 (Weeks 4-6) | P2 | 93-131h | STORY-201 |
| STORY-203 | Polish and Optimization | Sprint 4 (Weeks 7-8+) | P3 | 68-99h | STORY-202 (partial) |

**Total across all stories:** 229-330h (sum of sprint estimates; remainder is overlap with cross-cutting items counted in multiple sprints)

---

### Dependency Graph

```
STORY-200 (Sprint 1: Security + Trust)
    |
    v
STORY-201 (Sprint 2: Architecture Unification)
    |
    v
STORY-202 (Sprint 3: Decomposition + Quality)
    |
    v
STORY-203 (Sprint 4: Polish + Optimization)
```

Key internal dependency chains:

1. **ORM Consolidation:** DB-C03/DB-H04 (Sprint 1) --> CROSS-C01/DB-C01/DB-H01/NEW-DB-01 (Sprint 2) --> DB-M04 (Sprint 3)
2. **Frontend Decomposition:** FE-L03/FE-H04 (Sprint 1) --> FE-M01/FE-H01 (Sprint 2) --> FE-C01 (Sprint 3) --> FE-M03 (Sprint 4)
3. **CI Pipeline:** SYS-H05 (Sprint 1) --> SYS-C04/CROSS-M02 (Sprint 2) --> SYS-M07/FE-L07 (Sprint 3) --> SYS-L01 (Sprint 4)
4. **Horizontal Scaling:** SYS-C01 (Sprint 3) --> CROSS-C02/SYS-H02/FE-H06 (Sprint 3)
5. **Plan Data:** FE-L03 (Sprint 1) --> CROSS-M01 (Sprint 4) --> DB-M02 (Sprint 4)

---

### Success Criteria

1. **All 13 CRITICAL items resolved** -- verified by code review and automated tests
2. **All 19 HIGH items resolved** -- verified by code review and automated tests
3. **CI pipeline green** -- both backend (pytest) and frontend (npm test) pass with no pre-existing failures
4. **Frontend test coverage >= 60%** -- enforced by Jest threshold
5. **Backend test coverage >= 70%** -- enforced by pytest-cov threshold
6. **TypeScript check clean** -- `npx tsc --noEmit` passes
7. **Single ORM pattern** -- SQLAlchemy/models/ directory removed, all DB access via Supabase client
8. **main.py decomposed** -- no file exceeds 500 lines in backend/
9. **buscar/page.tsx decomposed** -- no file exceeds 300 lines in frontend/
10. **All MEDIUM items resolved or explicitly deferred** with documented justification
11. **Positive observations preserved** -- 23 architectural strengths listed in assessment section 11 verified intact after refactoring

---

### Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| ORM consolidation breaks Stripe webhooks | Medium | CRITICAL | Keep database.py as dead code for 2 weeks post-deploy. Monitor Stripe webhook delivery dashboard. |
| main.py decomposition introduces routing bugs | Medium | HIGH | Integration test suite must cover all 20+ endpoints before and after decomposition. |
| buscar/page.tsx decomposition causes visual regressions | Medium | HIGH | Playwright E2E tests as regression suite. Screenshot comparison. |
| Redis migration for SSE requires infrastructure changes | Low | MEDIUM | Railway supports Redis add-on. Fallback to in-memory with documented scaling limitation. |
| Sprint 3 scope exceeds 3 weeks | High | MEDIUM | P2 items can overflow into Sprint 4. Accessibility items are independently parallelizable. |
| Pre-existing test failures harder to fix than estimated | Medium | MEDIUM | 8-16h range accounts for uncertainty. Triage first: skip vs fix vs rewrite. |

---

### Positive Observations to Preserve

During debt resolution, these 23 architectural strengths MUST be preserved (from assessment section 11):

**Architecture/Backend:** Retry with exponential backoff + jitter, parallel UF fetching with asyncio.Semaphore, fail-fast sequential filtering, LLM Arbiter pattern, feature flags via env vars, multi-layer subscription fallback ("fail to last known plan"), log sanitization (PII masking), Stripe webhook idempotency.

**Database:** Atomic quota increment functions, RLS on 100% of tables, partial indexes, GIN index for JSONB, token encryption at rest (AES-256 Fernet), migrations with validation blocks.

**Frontend:** CSS custom properties design system, dark mode with flash prevention, EmptyState with actionable guidance, SSE progress tracking with simulation fallback, keyboard shortcuts (Ctrl+K, Ctrl+A, Escape), skip navigation link (WCAG 2.4.1), focus-visible outlines (WCAG 2.2 AAA), error message translation, pull-to-refresh mobile.

---

### Related Documents

- `docs/prd/technical-debt-assessment.md` -- Full 90-item assessment (FINAL)
- `docs/architecture/system-architecture.md` -- System architecture by @architect
- `supabase/docs/SCHEMA.md` -- Database schema documentation
- `supabase/docs/DB-AUDIT.md` -- Database audit by @data-engineer
- `docs/frontend/frontend-spec.md` -- Frontend specification by @ux-design-expert
- `docs/reviews/db-specialist-review.md` -- @data-engineer review
- `docs/reviews/ux-specialist-review.md` -- @ux-design-expert review
- `docs/reviews/qa-review.md` -- @qa review

---

*Epic created by @pm (Morgan) on 2026-02-11 based on the FINAL technical debt assessment approved by @architect, @data-engineer, @ux-design-expert, and @qa.*
