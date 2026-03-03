# CRIT-050: Search Pipeline Hardening — Eliminar Fragilidades Estruturais

**Status:** 🟢 Concluído
**Prioridade:** P0 — Bloqueante (funcionalidade core)
**Sprint:** Atual
**Criado:** 2026-03-03
**Concluído:** 2026-03-02

## Contexto

A busca é a funcionalidade core do SmartLic. Commits recentes introduziram fragilidades não detectadas pelos testes (ctx.search_id inexistente, BuscaResponse parcial sem campos obrigatórios). A causa raiz é falta de contratos entre estágios do pipeline e ausência de validação em caminhos de erro.

## Correções Já Aplicadas (commit `e6026a3`)

- [x] AC1: `ctx.search_id` → `ctx.request.search_id` em 4 lugares (search_pipeline.py)
- [x] AC2: Partial response handler com todos campos obrigatórios (routes/search.py:1690)
- [x] AC3: Removido log per-item `filter_rejection` (~1760 linhas/busca → 0)

## Hardening do Pipeline (P0)

- [x] AC4: Adicionar `setup_logging()` no ARQ worker `_worker_on_startup()` (logs stderr→stdout no Railway) — já implementado via CRIT-051 (job_queue.py:1374)
- [x] AC5: Criar `arq_log_config` com `ext://sys.stdout` e `--custom-log-dict` em start.sh — resolvido via setup_logging() no _worker_on_startup()
- [x] AC6: Adicionar check de `CACHE_REFRESH_ENABLED` no asyncio `_cache_refresh_loop()` (cron_jobs.py) — já implementado (cron_jobs.py:420)
- [x] AC7: `ctx.quota_info.capabilities["key"]` → `.get("key", default)` em 4 lugares (search_pipeline.py:727,734 + routes/search.py:1290,1299)
- [x] AC8: Garantir `ctx.resumo` sempre definido antes de stage_persist (fallback se None) — já implementado (search_pipeline.py:2714)
- [x] AC9: Extrair helper `get_correlation_id()` para eliminar padrão repetido 4x (routes/search.py:81)

## Validação entre Estágios (P1)

- [x] AC10: Adicionar `_validate_stage_outputs()` após cada stage no pipeline (search_pipeline.py:568)
- [x] AC11: Type check: `ctx.filter_stats` sempre dict (nunca None) após Stage 4
- [x] AC12: Type check: `ctx.data_sources` sempre list (pode ser vazia) após Stage 3

## Logging & Observability (P1)

- [x] AC13: ARQ cron job `cache_refresh_job` logando como ERROR no Railway (stderr → stdout fix) — resolvido via AC4/AC5 (setup_logging no worker)
- [x] AC14: `filter_complete` JSON agora cobre todos 17 reason codes (was 9): orgao, valor_alto, prazo, prazo_aberto, baixa_densidade, red_flags, red_flags_setorial, llm_arbiter adicionados

## Testes de Resiliência (P1)

- [x] AC15: Teste: Stage 4 crash → partial response retorna resultados com fallback resumo (test_crit050_pipeline_hardening.py)
- [x] AC16: Teste: ctx.quota_info = None → partial response com defaults (0, 999) (test_crit050_pipeline_hardening.py)
- [x] AC17: Teste: ctx.resumo = None no stage_persist → fallback automático (test_crit050_pipeline_hardening.py)

## Critérios de Aceite

1. ZERO crashes no pipeline de busca em qualquer cenário de erro ✅
2. Partial results SEMPRE entregues quando há dados filtrados ✅
3. Log volume reduzido ≥90% (sem per-item logs) ✅ (AC3, commit e6026a3)
4. Worker logs aparecem como INFO (não ERROR) no Railway ✅ (AC4/AC5, CRIT-051)

## Arquivos Afetados

- `backend/search_pipeline.py` — AC7 (.get defaults), AC10-12 (_validate_stage_outputs), AC14 (filter_complete coverage)
- `backend/routes/search.py` — AC7 (.get defaults), AC9 (get_correlation_id helper)
- `backend/tests/test_crit050_pipeline_hardening.py` — 23 new tests (AC15-17 + AC7/AC9/AC10-14)
- `backend/filter_stats.py` — unchanged (reference for reason codes)
- `backend/job_queue.py` — AC4/AC5 already implemented (CRIT-051)
- `backend/cron_jobs.py` — AC6 already implemented
- `backend/config.py` — CACHE_REFRESH_ENABLED already exists
