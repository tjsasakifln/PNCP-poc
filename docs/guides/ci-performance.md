# CI Performance & Accessibility Gate

**Origin:** STORY-5.16 (G-010 + G-011, EPIC-TD-2026Q2 P2)
**Last updated:** 2026-04-15

The frontend has two automated quality gates that run on every PR touching
`frontend/**`. Together they catch performance regressions and WCAG 2.1 AA
violations before they ship.

## The two workflows

| File | Tool | Scope | Gate |
|------|------|-------|------|
| `.github/workflows/lighthouse.yml` | Lighthouse CI (`@lhci/cli`) | 4 public routes (`/`, `/login`, `/planos`, `/features`) | Fails PR on budget violation |
| `.github/workflows/e2e.yml` (via `npm run test:e2e`) | `@axe-core/playwright` (`accessibility-audit.spec.ts`) | 10 routes including auth-gated | Fails PR on **critical** a11y violation |

Together they give cover across public marketing pages (Lighthouse) and
deep app flows (axe via mocked auth). Lighthouse doesn't need auth mocks;
axe handles what Lighthouse can't reach.

## Performance budgets (Lighthouse)

Enforced via `frontend/lighthouserc.js` assertion preset. Current thresholds:

| Category | Budget | Enforcement |
|----------|--------|-------------|
| Performance | ≥ 85 | **error** (fails PR) |
| Accessibility | ≥ 95 | **error** (fails PR) |
| Best Practices | ≥ 90 | **error** (fails PR) |
| SEO | ≥ 90 | **error** (fails PR) |

### Core Web Vitals

| Metric | Budget | Why |
|--------|--------|-----|
| FCP | < 2000 ms | First paint → user orientation. |
| LCP | < 2500 ms | Google Web Vitals "Good" threshold. |
| TBT | < 300 ms | Main-thread blocking → interactivity. |
| CLS | < 0.1 | Layout stability. |
| Speed Index | < 3400 ms | Overall rendering speed. |

## Accessibility (axe-core)

Configured in `frontend/e2e-tests/accessibility-audit.spec.ts`. Each route
runs `AxeBuilder.withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])` and
the test fails if **any critical violation** is found. `serious`/`moderate`
violations are logged but do not fail (they're tracked as debt).

Current coverage (10 routes): `/login`, `/buscar`, `/dashboard`, `/pipeline`,
`/planos`, `/`, `/signup`, `/historico`, `/conta`, `/ajuda`.

Adding a new route:

```ts
test('AC1.11: NewPage has 0 critical a11y violations', async ({ page }) => {
  // Set up any required mocks (auth, API responses)
  await mockAuthAPI(page, 'user');
  await page.goto('/newpage');
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(500);
  const result = await auditPage(page, 'NewPage');
  console.log(`NewPage: ${result.total} total violations (${result.serious.length} serious, ${result.moderate.length} moderate)`);
});
```

## Running locally

```bash
# Lighthouse (builds first, runs 3 times, medians)
cd frontend
npm run build
npm run lighthouse

# axe-core across all 10 routes
npm run test:e2e -- accessibility-audit.spec.ts

# Just one route (faster feedback)
npm run test:e2e -- accessibility-audit.spec.ts -g "Login"
```

## When a budget fails

**Performance drop (Lighthouse score fell below 85):**
1. Check the PR comment — it lists category scores + CWV metrics.
2. Download the `lighthouse-results` artifact for the detailed report.
3. Common culprits: large new image without `next/image`, sync-loading third-party
   script, regressed bundle (check `npm run analyze` — STORY-5.10).
4. If the regression is intentional (e.g. critical feature that justifies it),
   adjust the budget IN THE SAME PR with a 1-line rationale comment. Don't
   silently lower the bar.

**Accessibility critical violation:**
1. The test name in the Playwright output tells you which route.
2. Look for the `critical` entry in the Playwright terminal — axe gives the
   rule id (e.g. `color-contrast`, `aria-required-attr`).
3. Fix the violation (preferred) OR document a waiver with reason in the
   story's Change Log.

## Budget change policy

Budgets are quality gates, not aspirational targets. Lowering any threshold
requires:

1. A rationale in the commit message referencing the story/PR number.
2. A follow-up story opened to recover the lost ground.

Raising a threshold (tightening) is always welcome — open a PR that
demonstrates the build currently clears the new bar.

## Related

- `frontend/lighthouserc.js` — assertion config + URLs
- `.github/workflows/lighthouse.yml` — CI workflow + PR comment bot
- `frontend/e2e-tests/accessibility-audit.spec.ts` — axe test suite
- `frontend/next.config.js` — `optimizePackageImports` (STORY-5.10) impacts bundle → TBT/LCP
