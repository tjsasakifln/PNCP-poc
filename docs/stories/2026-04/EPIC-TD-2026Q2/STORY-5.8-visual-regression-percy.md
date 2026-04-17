# STORY-5.8: Visual Regression Percy Setup (TD-FE-008)

**Priority:** P2 | **Effort:** S (8-16h) | **Squad:** @qa + @ux-design-expert + @dev | **Status:** Blocked
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** SmartLic, **I want** visual regression testing via Percy integrado com Playwright, **so that** mudanças CSS não quebrem UI silenciosamente.

## Acceptance Criteria
- [ ] AC1: Percy account setup (free tier 5K snapshots/mês)
- [ ] AC2: `@percy/playwright` integration em E2E suite
- [ ] AC3: Snapshots em rotas core (`/buscar`, `/pipeline`, `/dashboard`, `/conta`, `/onboarding`)
- [ ] AC4: CI gate — fail PR se diff >1% sem approval
- [ ] AC5: Documentation: how to approve baseline updates

## Tasks
- [ ] Percy setup
- [ ] Integration code
- [ ] Baseline snapshots
- [ ] CI workflow
- [ ] Docs

## Dev Notes
- TD-FE-008 ref
- Alternative: Chromatic (mais expensive), Loki (self-hosted)

## Definition of Done
- [ ] Percy active + baseline + CI gate

## Risks
- R1: Free tier 5K snapshots stretchy — mitigation: snapshot only critical routes

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
