# STORY-5.16: Lighthouse CI + axe-core E2E (G-010, G-011)

**Priority:** P2 | **Effort:** S (6-12h → actual ~1h — most already in place) | **Squad:** @qa + @dev | **Status:** InReview
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** SmartLic, **I want** Lighthouse CI + axe-core integrados em CI, **so that** perf + a11y regressions sejam pegos automaticamente.

## Discovery (2026-04-15)

Significant infrastructure was already in place before this story:

- `.github/workflows/lighthouse.yml` exists with PR-comment bot.
- `frontend/lighthouserc.js` exists with Core Web Vitals budgets.
- `frontend/e2e-tests/accessibility-audit.spec.ts` runs axe-core across 10 routes.
- `@lhci/cli` + `@axe-core/playwright` both listed as devDependencies.

Real scope of this story: tighten the budgets, consolidate documentation,
and confirm PR-gate semantics meet the AC list.

## Acceptance Criteria
- [x] AC1 (G-011): Lighthouse CI workflow `.github/workflows/lighthouse.yml` — pre-existing, kept
- [x] AC2 (G-011): Budgets — Performance >85, Accessibility >95, Best Practices >90, SEO >90
  - Performance 85 ✅ (kept)
  - Accessibility **raised 90 → 95** (`error` level so PR fails)
  - Best Practices 90 → now `error` (was `warn`)
  - SEO 90 → now `error` (was `warn`)
- [x] AC3 (G-010): `@axe-core/playwright` integrado em E2E (pre-existing `accessibility-audit.spec.ts`)
- [x] AC4 (G-010): Critical routes — 0 violations crítica (10 routes covered, including all 6 targets)
- [x] AC5: PR check fail se budget violated (all categories escalated to `error`)

## Tasks
- [x] Lighthouse setup — kept; expanded URL list from `/` to `/`, `/login`, `/planos`, `/features` so the budget check is representative of public marketing surfaces
- [x] axe-core integration — kept (10 routes already covered)
- [x] CI workflow + PR check — kept; budget severities changed to `error`
- [x] Documentation — new `docs/guides/ci-performance.md` consolidates both tools, thresholds, budget-change policy, and "when a budget fails" troubleshooting

## Implementation Summary

**File: `frontend/lighthouserc.js`** — 2 targeted edits:

```diff
-      url: [
-        'http://localhost:3000',
-      ],
+      url: [
+        'http://localhost:3000',
+        'http://localhost:3000/login',
+        'http://localhost:3000/planos',
+        'http://localhost:3000/features',
+      ],
...
-        'categories:performance': ['error', { minScore: 0.85 }], // 85+
-        'categories:accessibility': ['warn', { minScore: 0.90 }], // 90+
-        'categories:best-practices': ['warn', { minScore: 0.90 }], // 90+
-        'categories:seo': ['warn', { minScore: 0.90 }], // 90+
+        'categories:performance': ['error', { minScore: 0.85 }],
+        'categories:accessibility': ['error', { minScore: 0.95 }],
+        'categories:best-practices': ['error', { minScore: 0.90 }],
+        'categories:seo': ['error', { minScore: 0.90 }],
```

**File: `docs/guides/ci-performance.md`** — new doc covering:
- Both gates (Lighthouse + axe-core) side-by-side
- Budget table with enforcement level
- Troubleshooting a budget failure
- Budget change policy

## File List

**Modified:**
- `frontend/lighthouserc.js` — URL expansion + severity bump

**Added:**
- `docs/guides/ci-performance.md`

**Not modified (kept as-is):**
- `.github/workflows/lighthouse.yml` — already complete with PR comment bot
- `frontend/e2e-tests/accessibility-audit.spec.ts` — already covers 10 routes
- `frontend/package.json` — lighthouse + test:e2e scripts already present

## Definition of Done
- [x] Budgets enforce at `error` severity — PR will fail on regression
- [x] Documentation unified — one guide covers both gates
- [x] All 6 AC-specified routes are covered by axe-core (via pre-existing 10-route spec)
- [ ] Validate first Lighthouse run on the new URLs in CI — will surface on first PR merge after this one (pre-existing `/` already passes budgets)

## Risk / Rollback

- Bumping `best-practices` + `seo` from `warn` to `error` could red-flag currently-marginal
  scores on the existing `/` route. If that happens, either (a) fix in the same PR or
  (b) temporarily drop to `warn` with a follow-up story — NOT to be silenced long-term.
- Lowering the accessibility bar from 0.95 back to 0.90 is trivial if
  `categories:accessibility` proves over-zealous during first CI runs. Keep the `error`
  severity though — `warn` ≡ muted alerts.

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-15 | 1.1 | Implementation: tighten budgets (warn→error, a11y 90→95), expand URL list, consolidate docs; axe-core + Lighthouse workflow pre-existing | @dev |
