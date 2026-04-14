# STORY-5.14: Inline Style Cleanup ESLint (TD-FE-003)

**Priority:** P2 | **Effort:** M (16-24h) | **Squad:** @ux-design-expert + @dev | **Status:** Draft
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** SmartLic, **I want** 139 inline `style={{...}}` migrados para Tailwind classes (com ESLint enforcement), **so that** design system seja consistent.

## Acceptance Criteria
- [ ] AC1: ESLint rule `react/forbid-component-props` ou custom blocks `style=` em components
- [ ] AC2: Audit + migrate 139 instances → Tailwind utilities ou CVA variants
- [ ] AC3: Allow exceptions com comment justifying (dynamic computed styles)
- [ ] AC4: Visual regression Percy <1%

## Tasks
- [ ] ESLint rule
- [ ] Audit + migrate
- [ ] Visual regression

## Dev Notes
- TD-FE-003 ref
- Some inline necessários (e.g., dynamic colors via JS) — allow with comment

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
