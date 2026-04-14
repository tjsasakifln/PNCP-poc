# STORY-5.16: Lighthouse CI + axe-core E2E (G-010, G-011)

**Priority:** P2 | **Effort:** S (6-12h) | **Squad:** @qa + @dev | **Status:** Draft
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** SmartLic, **I want** Lighthouse CI + axe-core integrados em CI, **so that** perf + a11y regressions sejam pegos automaticamente.

## Acceptance Criteria
- [ ] AC1 (G-011): Lighthouse CI workflow `.github/workflows/lighthouse.yml`
- [ ] AC2 (G-011): Budgets — Performance >85, Accessibility >95, Best Practices >90, SEO >90
- [ ] AC3 (G-010): `@axe-core/playwright` integrado em E2E
- [ ] AC4 (G-010): Critical routes — 0 violations crítica
- [ ] AC5: PR check fail se budget violated

## Tasks
- [ ] Lighthouse setup
- [ ] axe-core integration
- [ ] CI workflow + PR check

## Dev Notes
- G-010, G-011 refs (QA review Phase 7)

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
