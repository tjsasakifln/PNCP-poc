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

## Baseline (origin/main, 2026-04-19 pós-Wave #386)

Medido pelo CI `frontend-tests.yml` job `Check bundle size budget` em 2026-04-19:

| Metric | Valor medido |
|--------|-------------|
| First Load JS agregado (`.next/static/chunks/**/*.js`, gzipped) | **1.64 MB** |
| Limite anterior (DEBT-108 AC10/AC11) | 250 KB — **irreal** |
| Novo limite (STORY-5.14, hold-the-line) | **1.75 MB** (baseline + 7% head-room) |
| Alvo de redução em 90 dias (STORY-5.14) | ≤ 600 KB |

### Decomposição estimada (a confirmar via `npm run analyze`)

| Pacote | Estimativa gzipped |
|--------|-------------------|
| Next.js 16 runtime + React 18       | ~200 KB |
| Sentry `@sentry/nextjs`             | ~100 KB |
| Framer Motion                        | ~80 KB |
| Recharts                             | ~150 KB |
| @dnd-kit/core + sortable + utilities | ~40 KB |
| Supabase SSR client                  | ~60 KB |
| Stripe Elements (PaymentElement)     | ~90 KB |
| Shepherd.js (onboarding tour)        | ~40 KB |
| App code (pages + components)        | ~300 KB |
| Outros (lodash helpers, toasts, etc) | ~600 KB |
| **Total**                            | **~1.66 MB** |

### Alvo de redução (STORY-5.14, 90 dias)

| Frente | Ganho esperado |
|--------|---------------|
| Dynamic import rotas autenticadas (`/dashboard`, `/pipeline`, `/admin`) | -250 KB |
| Migração Framer → CSS transitions em landing | -50 KB |
| Tree-shake Recharts (importar só charts usados) | -80 KB |
| Lazy-load Shepherd apenas no first signup | -30 KB |
| Lazy-load Stripe só em `/planos` + `/signup` 2-step | -60 KB |
| Remoção de lodash em favor de nativos | -40 KB |
| Sentry source-map upload off em prod build | -80 KB |
| **Total esperado** | **-590 KB → ~1.05 MB** |

Próxima revisão de alvo em 60 dias: se 1.05 MB atingido, fixar cap em 1.1 MB
e abrir STORY-5.15 para atingir 600 KB.

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
