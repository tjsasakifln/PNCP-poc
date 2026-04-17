# STORY-5.14: Inline Style Cleanup ESLint (TD-FE-003)

**Priority:** P2 | **Effort:** M (16-24h) | **Squad:** @ux-design-expert + @dev | **Status:** InReview
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** SmartLic, **I want** 139 inline `style={{...}}` migrados para Tailwind classes (com ESLint enforcement), **so that** design system seja consistent.

## Acceptance Criteria
- [x] AC1: Custom ESLint rule `local-rules/no-inline-styles` criada em `scripts/eslint-rules/`
- [x] AC2: Audit + migrate 138 instances — static→Tailwind, dynamic→eslint-disable comments
- [x] AC3: Allow exceptions com `// eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: <reason>`
- [ ] AC4: Visual regression Percy <1% — **BLOCKED: depends on STORY-5.8 (Percy setup)**

## Implementation Notes

### ESLint Rule (AC1)
- Custom rule: `frontend/scripts/eslint-rules/no-inline-styles.js`
- Plugin: `eslint-plugin-local-rules` installed, resolver at `frontend/eslint-local-rules.js`
- Registered in `.eslintrc.json` as `local-rules/no-inline-styles: warn`
- **Note:** `next lint` removed in Next.js 16 — ESLint runs via `npx eslint` directly (pre-existing issue)

### Style Migration (AC2)
- **138 instances** audited across 67 files
- **47 in OG routes**: exempt (Vercel OG requires inline styles)
- **9 in global-error.tsx**: exempt (renders outside Tailwind context)
- **8 in e2e/test files**: exempt
- **~47 dynamic styles**: annotated with eslint-disable + specific reason
- **~27 static styles**: converted to Tailwind classes
  - `fontFamily: 'Georgia...'` → `font-serif` (13 blog files)
  - `transform: translate(-50%, -100%)` → `-translate-x-1/2 -translate-y-full`
  - `height: '600px'` → `h-[600px]`
  - `aspectRatio: '16/9'` → `aspect-video`
  - `width: '30%'` → `w-[30%]` (indeterminate progress bar)

### Exemptions (AC3)
- OG routes, global-error, tests: `.eslintrc.json` override `"local-rules/no-inline-styles": "off"`
- Dynamic styles: `// eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: <reason>`
- Every disable comment includes specific justification (not generic)

## File List
- `frontend/scripts/eslint-rules/no-inline-styles.js` — new rule
- `frontend/scripts/eslint-rules/index.js` — updated exports
- `frontend/eslint-local-rules.js` — new resolver
- `frontend/.eslintrc.json` — rule registration + overrides
- `frontend/package.json` — `eslint-plugin-local-rules` devDep
- ~60 `.tsx` files — style migrations + eslint-disable comments
- 2 test files updated to match Tailwind class assertions

## Test Results
- TypeScript: 0 errors
- Tests: 35 fail (all pre-existing) / 6080 pass — zero new regressions
- 2 test assertions updated (inline style → Tailwind class checks)

## Definition of Done
- [x] AC1-AC3 met (3/4)
- [ ] AC4 deferred (Percy — STORY-5.8)

## Risks
- R1: `next lint` broken in Next.js 16 — separate fix needed
- R2: Dynamic styles kept as inline — monitored via eslint-disable comments

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-15 | 1.1 | Implementation: ESLint rule + 138 instances migrated/annotated. AC4 blocked (Percy). | @dev |
