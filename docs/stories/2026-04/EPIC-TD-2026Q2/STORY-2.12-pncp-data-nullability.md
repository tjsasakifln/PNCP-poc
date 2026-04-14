# STORY-2.12: pncp_raw_bids data_* Nullability Fix (TD-DB-022)

**Priority:** P1 (5-10% bids excluded silenciosamente em filtros por data)
**Effort:** S (4-8h)
**Squad:** @data-engineer + @dev quality gate
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 1

---

## Story

**As a** usuário SmartLic filtrando por data,
**I want** ver TODOS os bids relevantes mesmo se PNCP retorna data missing,
**so that** eu não perca oportunidades por inconsistência de dados upstream.

---

## Acceptance Criteria

### AC1: Audit ingestion data quality

- [ ] Query `SELECT COUNT(*) FROM pncp_raw_bids WHERE data_publicacao IS NULL` — quantificar
- [ ] Same para `data_abertura`, `data_encerramento`
- [ ] Documentar % de NULL por column

### AC2: Backfill estratégia

- [ ] Para rows com NULL date, popular com fallback (ingested_at - 1 day, ou outra heurística defensável)
- [ ] Migration ou script Python documenta + executa backfill

### AC3: search_datalake RPC tolera NULL

- [ ] Verificar query: filtro `data_publicacao BETWEEN x AND y` exclui NULL
- [ ] Refactor: usar `COALESCE(data_publicacao, ingested_at)` ou OR clause
- [ ] Test: bid com NULL data aparece em busca relevante

### AC4: Forward-looking

- [ ] Ingestion `transformer.py` adiciona fallback se PNCP retorna NULL
- [ ] Loader/upsert garante data_* não-NULL em writes futuros

---

## Tasks / Subtasks

- [ ] Task 1: Audit query (AC1)
- [ ] Task 2: Backfill script + migration (AC2)
- [ ] Task 3: Update search_datalake RPC (AC3)
- [ ] Task 4: Update transformer/loader (AC4)
- [ ] Task 5: Tests

## Dev Notes

- `pncp_raw_bids` schema doc em `supabase/docs/SCHEMA.md` item 19
- `backend/datalake_query.py` chama `search_datalake` RPC

## Testing

- pytest test_datalake_query com bid NULL date → assert returned
- Smoke prod após backfill

## Definition of Done

- [ ] Audit completed
- [ ] Backfill executed
- [ ] RPC + ingestion fixed
- [ ] Tests pass

## Risks

- **R1**: Backfill heurística incorreta → mitigation: conservative (fallback = ingested_at - 1 day)

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
