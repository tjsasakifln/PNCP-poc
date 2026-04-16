# Bundle Size Baseline — STORY-5.10 (TD-FE-012)

## Context

Story-5.10 enables tree-shaking for Framer Motion and @dnd-kit via Next.js
`experimental.optimizePackageImports`. This document establishes the bundle
size measurement workflow and captures before/after numbers as they become
available.

## How to measure

From `frontend/`:

```bash
# Generate analyzer reports (.next/analyze/*.html)
npm run analyze

# Open the two generated reports — client.html and nodejs.html —
# and look at the shared JS (largest chunk shown at the top).
```

The output is written to `.next/analyze/client.html` (browser-side) and
`.next/analyze/nodejs.html` (server-side). The CI does NOT publish these as
artifacts yet; the repo relies on the `size-limit` check (already wired via
`npm run size-limit` and the `@size-limit/file` devDep) to fail PRs that
blow the budget.

## Baseline (origin/main, 2026-04-15 pre-STORY-5.10)

> TODO: Capture via `npm run analyze` on the commit that precedes this story
> and paste the "Parsed size" totals here. We can do this opportunistically
> on the next PR that ships a frontend build — the numbers aren't load-bearing
> for merge, only for verifying the expected reduction.

| Metric | Baseline | Target | Post-5.10 |
|--------|----------|--------|-----------|
| Shared JS (First Load)       | TBD | ≤ baseline - 50 KB | TBD |
| `framer-motion` chunk size   | TBD | ≤ baseline - 30% | TBD |
| `@dnd-kit/*` chunk size      | TBD | ≤ baseline - 20% | TBD |

## Why tree-shaking works here

The inspection done during STORY-5.10 confirmed that every callsite already uses
**named imports** (no default or wildcard imports):

```
grep -rn "from 'framer-motion'" frontend/app/ frontend/components/
grep -rn "from '@dnd-kit/" frontend/app/ frontend/components/
```

Next.js's `optimizePackageImports` rewrites those named imports to the
package's submodule path at compile time (e.g.
`import { motion } from 'framer-motion'` →
`import motion from 'framer-motion/dist/es/render/components/motion/index.mjs'`),
which lets webpack/Turbopack drop unused code.

## Non-goals

- **Dynamic imports** for pipeline/Kanban are already in place
  (`PipelineKanban` is code-split). STORY-5.10 does NOT change that.
- **Moving off framer-motion** is out of scope. Some landing/marketing
  components depend on `motion`/`AnimatePresence`/`useInView`. Replacing
  with CSS transitions was done for `SearchStateManager` in a prior story
  (DEBT-FE-004) and is a per-file judgment call, not a global refactor.

## Verifying no regression

After `npm run analyze`:

1. Compare `Shared JS` total before/after — should drop or stay flat.
2. Spot-check a route that imports framer-motion (e.g. `/features`) and
   confirm the chunk size went down.
3. Run `npm run build` — must succeed with zero new warnings.

## Related

- `frontend/next.config.js` — `experimental.optimizePackageImports` config
- `frontend/package.json` — `analyze` script + `@next/bundle-analyzer` devDep
- Future: STORY-5.16 will wire Lighthouse CI which surfaces Total Blocking
  Time regressions that usually correlate with bundle growth.
