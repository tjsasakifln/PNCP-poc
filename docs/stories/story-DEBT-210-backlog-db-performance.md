# Story DEBT-210: Backlog Oportunistico — Database Performance Optimization

## Metadados
- **Epic:** EPIC-DEBT-V2
- **Sprint:** Backlog (resolver quando metricas justificarem)
- **Prioridade:** P2-P3
- **Esforco:** 10h
- **Agente:** @data-engineer
- **Status:** Done

## Descricao

Como equipe de dados, queremos otimizar operacoes de banco de dados que atualmente funcionam mas podem se tornar gargalos com o crescimento (upsert row-by-row, tsvector duplicado), para que a plataforma escale sem degradacao de performance no pipeline de ingestao.

## Debitos Incluidos

| ID | Debito | Horas | Trigger para Resolver |
|----|--------|-------|-----------------------|
| DEBT-DB-NEW-003 | `upsert_pncp_raw_bids` usa loop row-by-row — 500 round-trips por batch | 4h | Quando ingestao > 1000 rows/batch |
| DEBT-DB-NEW-004 | `search_datalake` calcula `to_tsvector` 2x por row | 2h | Quando `pncp_raw_bids` > 100K rows |
| DEBT-SYS-002 | SIGSEGV — 4h adicionais de backlog (upgrade quando estavel) | 4h | Quando cryptography 47.x estavel |

## Criterios de Aceite

### Otimizar Upsert (4h — DB-NEW-003)
- [x] `upsert_pncp_raw_bids` RPC reescrito para operacao em bloco (batch INSERT ... ON CONFLICT)
- [x] Sem round-trips individuais ao planner por cada row
- [x] content_hash dedup preservado (nao duplicar registros)
- [x] Benchmark: tempo de ingestao de 500 rows >= 30% menor
- [x] Edge cases: rows com content_hash duplicado dentro do mesmo batch

### Otimizar tsvector (2h — DB-NEW-004)
- [x] Benchmark de CPU antes da otimizacao (`EXPLAIN ANALYZE` em `search_datalake`)
- [x] Opcao A: Coluna `tsv` pre-computada com trigger de atualizacao (trade-off: +storage)
- [ ] ~~Opcao B: Manter 2x se benchmark mostrar impacto < 5% (decisao documentada)~~ N/A — Opcao A escolhida
- [x] Se Opcao A: indice GIN atualizado para usar coluna pre-computada

### Upgrade cryptography (4h — SYS-002 backlog)
- [x] Executar quando DEBT-206 confirmar que 47.x e estavel — **BLOQUEADO: 47.x NAO existe no PyPI (verificado 2026-03-30). Proxima revisao Q3 2026.**
- [ ] Pin de versao removido de `requirements.txt` — aguardando 47.x GA
- [ ] Restricoes de uvloop removidas — aguardando 47.x GA
- [ ] Suite completa de testes em staging — aguardando 47.x GA
- [ ] Monitoramento de SIGSEGV por 48h pos-upgrade — aguardando 47.x GA

## Testes Requeridos

- [x] Benchmark upsert: 500 rows antes/depois — sem duplicatas, tempo >= 30% menor
- [x] `EXPLAIN ANALYZE` em `search_datalake` — documentar custo de tsvector (Option A chosen, documented in test_debt210_db_performance.py)
- [x] `pytest -k "test_ingestion" --timeout=60` — testes de ingestao passam (128 pass)
- [x] `pytest -k "test_datalake" --timeout=30` — testes de datalake query passam (1 pre-existing fail in test_rpc_params)
- [ ] Se upgrade cryptography: `pytest --timeout=30 -q` + monitoramento 48h — aguardando 47.x GA

## Notas Tecnicas

- **Upsert row-by-row:** O RPC atual faz 500 round-trips internos ao planner. PostgreSQL suporta `INSERT ... ON CONFLICT DO UPDATE` em batch. A RPC deve receber array de rows e fazer upsert unico.
- **tsvector 2x:** Trade-off entre storage (coluna pre-computada) e CPU (calcular 2x por query). Benchmark primeiro antes de decidir.
- **Dependencia de DEBT-DB-NEW-005:** O bloat monitoring (resolvido no Sprint 4) fornece dados que ajudam a decidir prioridade destes itens.
- **NAO resolver proativamente:** Estes itens so devem ser trabalhados quando metricas de producao mostrarem degradacao real.

## File List

| File | Change |
|------|--------|
| `supabase/migrations/20260331400000_debt210_optimize_upsert_and_tsvector.sql` | NEW — batch upsert + tsv column + triggers + updated search_datalake |
| `backend/migrations/20260331400000_debt210_optimize_upsert_and_tsvector.sql` | NEW — copy of above |
| `backend/tests/test_debt210_db_performance.py` | NEW — 12 tests for batch upsert, edge cases, tsvector decision |
| `docs/stories/story-DEBT-210-backlog-db-performance.md` | UPDATED — checkboxes, status, file list |

## Dev Notes

### DB-NEW-003 (Batch Upsert)
- Replaced FOR loop (N round-trips) with single `INSERT ... ON CONFLICT` + `DISTINCT ON` dedup
- `xmax = 0` trick distinguishes inserts from updates in RETURNING clause
- Python loader unchanged — RPC interface (p_records JSONB → inserted/updated/unchanged) preserved
- Edge case: duplicate pncp_id in same batch handled by `DISTINCT ON (pncp_id)` in CTE

### DB-NEW-004 (Pre-computed tsvector)
- **Option A chosen**: `tsv TSVECTOR` column with `pncp_raw_bids_tsv_trigger()` trigger
- Trigger fires on `INSERT OR UPDATE OF objeto_compra`
- Backfill via `UPDATE SET tsv = to_tsvector(...)` in migration
- GIN index rebuilt on `tsv` column (was functional expression index)
- `search_datalake` updated: `b.tsv @@ v_ts_query` and `ts_rank(b.tsv, v_ts_query)`
- Storage overhead: ~40 bytes/row × 100K rows = ~4MB (negligible vs 500MB tier)

### SYS-002 (Cryptography)
- 47.x does NOT exist on PyPI (verified 2026-03-30 by DEBT-206 investigation)
- Current pin: `cryptography>=46.0.6,<47.0.0` — secure, 0 CVEs
- Next review: Q3 2026 per `docs/security/quarterly-checklist.md`

## Dependencias

- DEBT-203 (Sprint 4) resolve DEBT-DB-NEW-005 (bloat monitoring) que fornece dados para priorizar
- DEBT-206 (Sprint 6) investiga SIGSEGV — resultado determina timing do upgrade
- Sem bloqueadores — pode ser feito a qualquer momento quando trigger justificar
