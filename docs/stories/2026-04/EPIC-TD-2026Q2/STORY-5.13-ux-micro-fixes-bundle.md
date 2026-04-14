# STORY-5.13: UX Micro-Fixes Bundle (TD-FE-017, 018, 019, 020, 021, 052, 053)

**Priority:** P2 | **Effort:** L (25-40h) | **Squad:** @ux-design-expert + @dev | **Status:** Draft
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** usuário SmartLic, **I want** múltiplas UX rough edges suavizadas, **so that** experiência seja mais polida.

## Acceptance Criteria
- [ ] AC1 (TD-FE-017): Shepherd tour dismiss persistente — localStorage flag (resolved se STORY-4.2 substituiu Shepherd)
- [ ] AC2 (TD-FE-018): Bottom nav mobile sticky durante scroll (CSS `position: sticky`)
- [ ] AC3 (TD-FE-019): "Atualizado X min atrás" badge nos resultados de busca + cache
- [ ] AC4 (TD-FE-020): Form validation errors com `aria-live="assertive"` + visual prominence
- [ ] AC5 (TD-FE-021): Blog content responsive (images max-width 100%)
- [ ] AC6 (TD-FE-052): SWR mutate revalidate em handlers POST/PATCH/DELETE
- [ ] AC7 (TD-FE-053): Skeleton dimensões match real cards (CLS reduce <0.1)

## Tasks
- [ ] Per AC, sub-PR
- [ ] Bundle review

## Dev Notes
- 7 fixes pequenos; podem ser stacked PR ou separados

## Definition of Done
- [ ] All 7 ACs met + Lighthouse CLS <0.1

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
