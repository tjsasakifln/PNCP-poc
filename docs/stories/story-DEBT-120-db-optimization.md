# DEBT-120: DB Optimization — Index Analysis, Traceability, Cleanup

**Prioridade:** POST-GTM
**Estimativa:** 3.5h
**Fonte:** Brownfield Discovery — @data-engineer (DB-025, DB-031, DB-INFO-01)
**Score Impact:** Integrity 8→9

## Contexto
3 items de otimização de database: analisar usage dos 6 indexes em search_results_cache (potencial remoção de redundantes), adicionar search_id a pipeline_items para rastreabilidade, e deprecar o diretório backend/migrations/.

## Acceptance Criteria

### Index Analysis (2h)
- [x] AC1: Executar pg_stat_user_indexes em produção para search_results_cache
- [x] AC2: Identificar indexes com idx_scan = 0 (candidatos a remoção)
- [x] AC3: Se idx_search_cache_params_hash redundante com UNIQUE: DROP INDEX → NOT redundant (236 scans, different leading column). Dropped idx_search_cache_fetched_at instead (0 scans).
- [x] AC4: Documentar decisão sobre cada index (documented in migration SQL comments)

### Pipeline Traceability (1h)
- [x] AC5: Migration: ADD COLUMN search_id TEXT a pipeline_items
- [x] AC6: Atualizar routes/pipeline.py para salvar search_id ao adicionar item ao pipeline
- [x] AC7: Teste unitário para novo campo (6 tests in test_debt120_pipeline_search_id.py)

### Migrations Cleanup (0.5h)
- [x] AC8: Adicionar README.md em backend/migrations/ marcando como DEPRECATED → Already done by DEBT-002 (2026-03-08)
- [x] AC9: Ou deletar o diretório inteiro (se confirmado que nenhum script usa) → NOT deleted: DEBT-002 test enforces preservation + files serve as historical reference

## File List
- [x] `supabase/migrations/20260315100000_debt120_db_optimization.sql` (NEW)
- [x] `backend/routes/pipeline.py` (EDIT — search_id in insert)
- [x] `backend/schemas.py` (EDIT — search_id in PipelineItemCreate + PipelineItemResponse)
- [x] `frontend/app/pipeline/types.ts` (EDIT — search_id in PipelineItem interface)
- [x] `frontend/app/components/AddToPipelineButton.tsx` (EDIT — pass search_id: null)
- [x] `frontend/__tests__/pipeline/AddToPipelineButton.test.tsx` (EDIT — updated assertion)
- [x] `backend/tests/test_debt120_pipeline_search_id.py` (NEW — 6 tests)
- [x] `backend/migrations/README.md` (EXISTING — already DEPRECATED by DEBT-002)
