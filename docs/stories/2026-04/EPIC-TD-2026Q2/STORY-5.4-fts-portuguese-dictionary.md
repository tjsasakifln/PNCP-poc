# STORY-5.4: PostgreSQL FTS Portuguese Custom Dictionary (TD-SYS-015)

**Priority:** P2 | **Effort:** M (8-16h) | **Squad:** @data-engineer + @dev | **Status:** Draft
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** SmartLic, **I want** dicionário FTS Portuguese custom para termos legais BR (modalidade, esfera, tipo licitação), **so that** precisão de busca aumente.

## Acceptance Criteria
- [ ] AC1: Migration cria text search config `public.portuguese_smartlic`
- [ ] AC2: Termos legais comuns (concorrência, pregão, dispensa, etc.) com synonyms map
- [ ] AC3: `search_datalake` RPC usa novo config
- [ ] AC4: Re-index `pncp_raw_bids.tsv` via novo config
- [ ] AC5: Precision/recall benchmark melhora >5%

## Tasks
- [ ] Identify common terms missing
- [ ] Build synonyms file
- [ ] Migration
- [ ] Re-index (CONCURRENTLY)
- [ ] Benchmark

## Dev Notes
- TD-SYS-015 ref
- Postgres text search config: https://www.postgresql.org/docs/17/textsearch-dictionaries.html

## Definition of Done
- [ ] Config + re-index + benchmark improvement

## Risks
- R1: Re-index trava table — mitigation: CONCURRENTLY + off-hours

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
