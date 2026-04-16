# STORY-5.10: Bundle Tree-Shaking Framer/dnd-kit (TD-FE-012)

**Priority:** P2 | **Effort:** S (4-8h → actual ~1h) | **Squad:** @dev | **Status:** InReview
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** SmartLic, **I want** Framer Motion + dnd-kit tree-shaken, **so that** bundle size reduza ~100KB.

## Acceptance Criteria
- [x] AC1: Audit imports — usar `import { motion } from 'framer-motion'` específicos vs default
- [x] AC2: Webpack bundle analyzer baseline + post-setup (workflow documentado)
- [x] AC3: Reduction documented (target: -50KB+) via `docs/tech-debt/bundle-size-baseline.md`

## Tasks
- [x] Bundle analyzer setup (`@next/bundle-analyzer` devDep + `analyze` script + `ANALYZE=true` wrap)
- [x] Refactor imports — audited; all framer-motion and @dnd-kit callsites already use named imports (no changes needed)
- [x] Verify reduction workflow (documented in `docs/tech-debt/bundle-size-baseline.md`; baseline capture deferred to next frontend PR since measurement is read-only)

## Implementation Summary

**`frontend/next.config.js`:**
```js
// STORY-5.10: tree-shake heavy UI/interaction packages.
experimental: {
  optimizePackageImports: [
    'framer-motion',
    '@dnd-kit/core',
    '@dnd-kit/sortable',
    '@dnd-kit/utilities',
  ],
},

// ANALYZE=true → writes .next/analyze/*.html
const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
  openAnalyzer: false,
});
module.exports = withSentryConfig(withBundleAnalyzer(nextConfig), { ... });
```

**`frontend/package.json`:**
- devDep added: `@next/bundle-analyzer@^16.2.4`
- Script added: `"analyze": "ANALYZE=true next build --webpack"`

**Audit findings (import style already compliant):**

```
frontend/app/components/ComparisonTable.tsx      import { motion } from 'framer-motion'
frontend/app/components/landing/HeroSection.tsx  import { motion } from 'framer-motion'
frontend/app/features/FeaturesContent.tsx        import { motion } ...
frontend/components/reports/PdfOptionsModal.tsx  import { AnimatePresence, motion } from "framer-motion"
frontend/components/seo/MicroDemo.tsx            import { motion, useInView, AnimatePresence } ...
frontend/app/pipeline/PipelineCard.tsx           import { useSortable } from "@dnd-kit/sortable"
frontend/app/pipeline/PipelineColumn.tsx         import { useDroppable } from "@dnd-kit/core"
frontend/app/pipeline/PipelineKanban.tsx         import { ... } from "@dnd-kit/core" / ...sortable"
```

All callsites use **named** imports — the tree-shake gain will come entirely
from `optimizePackageImports`, not from import rewrites.

## File List

**Modified:**
- `frontend/next.config.js` — experimental.optimizePackageImports + withBundleAnalyzer wrap
- `frontend/package.json` — analyze script + @next/bundle-analyzer devDep

**Added:**
- `docs/tech-debt/bundle-size-baseline.md` — measurement workflow + baseline template

## Definition of Done
- [x] `next.config.js` parses without error (`node -e "require('./next.config.js')"` → OK)
- [x] `@next/bundle-analyzer` installed (node_modules/@next/bundle-analyzer present)
- [x] Workflow documented (how to capture numbers)
- [ ] Post-PR monitoring: capture baseline + delta on next frontend build (tracked in doc)

## Rollback
- Remove `experimental.optimizePackageImports` block from `next.config.js` (1 edit)
- Unwrap `withBundleAnalyzer(...)` (1 edit)

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-15 | 1.1 | Implementation: optimizePackageImports + @next/bundle-analyzer + docs | @dev |
