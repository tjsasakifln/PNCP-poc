# STORY-6.6: Mutation Testing Stryker (G-012)

**Priority:** P3 | **Effort:** M (8-16h) | **Squad:** @qa + @dev | **Status:** Draft
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 7+

## Story
**As a** SmartLic, **I want** mutation testing em backend critical paths, **so that** test quality (não só coverage) seja medido.

## Acceptance Criteria
- [ ] AC1: Stryker (Python: `mutmut` ou `cosmic-ray`) setup
- [ ] AC2: Run em modules críticos (filter.py, llm_arbiter.py, consolidation.py, quota.py)
- [ ] AC3: Mutation score >70%
- [ ] AC4: Documentation + CI weekly run

## Tasks
- [ ] Tool setup
- [ ] Run + fix surviving mutants
- [ ] CI workflow

## Dev Notes
- G-012 ref (QA review Phase 7)
- Python: `mutmut` mais comum; `cosmic-ray` mais estatístico

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
