# STORY-2.12: pncp_raw_bids data_* Nullability Fix (TD-DB-022)

**Priority:** P1 (5-10% bids excluded silenciosamente em filtros por data)
**Effort:** S (4-8h)
**Squad:** @data-engineer + @dev quality gate
**Status:** Ready for Review
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

- [x] Script `backend/scripts/audit_pncp_data_nullability.py` quantifica NULL em `data_publicacao`, `data_abertura`, `data_encerramento`
- [x] Output formato Markdown em `docs/audit/pncp_data_nullability_{YYYYMMDD_HHMMSS}.md` com % NULL por column

### AC2: Backfill estratégia

- [x] Migration `20260414132000_backfill_pncp_raw_bids_dates.sql`:
  - `data_publicacao = COALESCE(data_publicacao, ingested_at::date - interval '1 day')` (fallback conservador)
  - `data_abertura = COALESCE(data_abertura, data_publicacao)`
  - `data_encerramento` preservado NULL (sem heurística segura)
  - Idempotente via WHERE clause; wrapped em transaction + statement_timeout '10min'

### AC3: search_datalake RPC tolera NULL

- [x] Migration `20260414133000_search_datalake_coalesce_dates.sql` usa `CREATE OR REPLACE FUNCTION` preservando signature/body byte-for-byte, alterando apenas filtros de data para `COALESCE(data_publicacao, ingested_at::date)`.
- [x] ORDER BY modificado para `... data_publicacao DESC NULLS LAST` (tolera NULL no sort).
- [x] Preserva hybrid FTS + pgvector + trigram fallback + modo 'abertas'.

### AC4: Forward-looking

- [x] `transformer.py`: fallback `datetime.utcnow() - 1 day` se `dataPublicacaoPncp` None/empty; `data_abertura` default para `data_publicacao`
- [x] `loader.py`: `_apply_date_fallbacks` como defence-in-depth (safety net se alguém bypass o transformer)

---

## Tasks / Subtasks

- [x] Task 1: Audit query (AC1) — script Python standalone
- [x] Task 2: Backfill migration (AC2)
- [x] Task 3: Update search_datalake RPC (AC3)
- [x] Task 4: Update transformer/loader (AC4)
- [x] Task 5: Tests (25 tests + regressão do test_ingestion_transformer existente)

## Dev Notes

- `pncp_raw_bids` schema doc em `supabase/docs/SCHEMA.md` item 19
- `backend/datalake_query.py` chama `search_datalake` RPC

## Testing

- pytest test_datalake_query com bid NULL date → assert returned
- Smoke prod após backfill

## File List

- **Created**:
  - `supabase/migrations/20260414132000_backfill_pncp_raw_bids_dates.sql`
  - `supabase/migrations/20260414133000_search_datalake_coalesce_dates.sql`
  - `backend/scripts/audit_pncp_data_nullability.py`
  - `backend/tests/test_transformer_null_date_fallback.py` (8 tests)
  - `backend/tests/test_datalake_query_null_dates.py` (17 tests)
- **Modified**:
  - `backend/ingestion/transformer.py`
  - `backend/ingestion/loader.py`
  - `backend/tests/test_ingestion_transformer.py` (1 test atualizado p/ novo contrato AC4)

## Definition of Done

- [x] Audit script pronto (executar post-deploy para gerar snapshot inicial)
- [x] Backfill migration criada (aplicada via CRIT-050 auto-apply em deploy)
- [x] RPC + ingestion fixed
- [x] 25 tests novos passando + regressão do suite existente estável

## Risks

- **R1**: Backfill heurística incorreta → mitigation: conservative (fallback = ingested_at - 1 day)

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-14 | 1.1     | Implementation complete — 25 tests. `search_datalake` refatorado cirurgicamente preservando hybrid body. Forward-looking fallback no transformer + loader. | @dev (EPIC-TD Sprint 1 batch) |
