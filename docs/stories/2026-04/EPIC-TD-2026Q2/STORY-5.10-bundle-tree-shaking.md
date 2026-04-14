# STORY-5.10: Bundle Tree-Shaking Framer/dnd-kit (TD-FE-012)

**Priority:** P2 | **Effort:** S (4-8h) | **Squad:** @dev | **Status:** Draft
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** SmartLic, **I want** Framer Motion + dnd-kit tree-shaken, **so that** bundle size reduza ~100KB.

## Acceptance Criteria
- [ ] AC1: Audit imports — usar `import { motion } from 'framer-motion'` específicos vs default
- [ ] AC2: Webpack bundle analyzer baseline + post
- [ ] AC3: Reduction documented (target: -50KB+)

## Tasks
- [ ] Bundle analyzer
- [ ] Refactor imports
- [ ] Verify reduction

## Dev Notes
- TD-FE-012 ref
- `next.config.js` may need `experimental.optimizePackageImports`

## Definition of Done
- [ ] Reduction confirmed via analyzer

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
