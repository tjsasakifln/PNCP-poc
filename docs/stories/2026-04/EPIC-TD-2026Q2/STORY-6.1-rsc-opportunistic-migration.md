# STORY-6.1: RSC Opportunistic Migration Plan + First Wave (TD-FE-007)

**Priority:** P3 | **Effort:** L (40-56h) | **Squad:** @architect + @dev + @ux-design-expert | **Status:** Draft
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 7+

## Story
**As a** SmartLic, **I want** plano de migração RSC opportunistic + first wave (5-10 components), **so that** bundle size reduza progressively sem big-bang risk.

## Acceptance Criteria
- [ ] AC1: Documento `docs/architecture/rsc-migration-plan.md` com:
  - Quais components são candidatos (server-by-default)
  - Dependências client-side a remover
  - Padrão de migration
- [ ] AC2: 5-10 components migrated em first wave
- [ ] AC3: Bundle size reduce ≥10%
- [ ] AC4: Sem regressões funcionais (E2E pass)

## Tasks
- [ ] Audit candidates
- [ ] Migration plan doc
- [ ] First wave migration
- [ ] Bundle measure

## Dev Notes
- TD-FE-007 ref
- 88% "use client" atual

## Risks
- R1: Hidden client-side dependencies — mitigation: incremental + test-after-each

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
