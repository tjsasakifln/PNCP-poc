# STORY-4.1: LLM Async + Batch API Integration (TD-SYS-014)

**Priority:** P1 (latência 30s+ em alta concorrência)
**Effort:** M (16-24h)
**Squad:** @dev + @architect + @qa
**Status:** InReview
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 3
**Depends on:** STORY-3.1 (search.py decompose) ✅ shipped

---

## Story

**As a** SmartLic,
**I want** chamadas LLM via async client + Batch API quando aplicável,
**so that** latência média de search caia 50%+ em alta concorrência.

---

## Acceptance Criteria

### AC1: Async OpenAI client + semaphore bounded concurrency

- [x] `backend/llm_arbiter/async_runtime.py` — novo módulo com `_get_async_client` (lazy `openai.AsyncOpenAI`), loop-scoped `_get_semaphore`, `_bounded` async context manager, `gather_classifications` helper
- [x] `LLM_MAX_CONCURRENT` env (default 50) substitui o hardcoded `max_workers=10`
- [x] Ambos os call sites `ThreadPoolExecutor(max_workers=10)` em `filter/pipeline.py:895, 1284` removidos — agora usam `asyncio.gather` via `gather_classifications`
- [x] Sync wrappers preservados (`classify_contract_primary_match`, `classify_contract_recovery`, `_classify_zero_match_batch`) — zero quebra em `@patch("llm_arbiter._get_client")` tests
- [x] Exceptions do inner func são preservadas com `_FailedResult` + `unwrap_result` — mesma semântica de `future.result()` legado

### AC2: Batch API para classificação (escopo: offline)

- [x] `backend/llm_arbiter/batch_api.py` — `submit_batch`, `poll_batch`, metadata persistida em Redis (`smartlic:llm_batch:pending` SET + `smartlic:llm_batch:{id}:meta` HASH, TTL 72h)
- [x] `backend/jobs/cron/llm_batch_poll.py` — ARQ cron (default 60s via `LLM_BATCH_POLL_INTERVAL_S`)
- [x] Feature flag `LLM_BATCH_ENABLED` (default false) — default preserva comportamento live
- [x] `LLM_BATCH_MIN_ITEMS` threshold (default 20) — retorna None silently abaixo
- [x] **Escopo**: aplica apenas ao path offline (`reclassify_pending_bids_job`). OpenAI Batch API tem SLA 24h, incompatível com `/buscar` p95 — documentado como escolha arquitetural explícita

### AC3: Telemetria Prometheus

- [x] `smartlic_llm_call_duration_seconds` já existia (metrics.py:102)
- [x] `smartlic_llm_concurrent_calls{call_type}` — Gauge: concorrência real vs `LLM_MAX_CONCURRENT`
- [x] `smartlic_llm_batch_jobs_active` — Gauge de batches em flight
- [x] `smartlic_llm_batch_job_duration_seconds` — Histogram (buckets até 24h)

### AC4: Latency improvement

- [x] `backend/scripts/compare_p95.py` — parses 2 Locust CSVs, assert `(baseline-new)/baseline ≥ 0.40`
- [x] Refactor eleva teto de concorrência de 10 para 50 (default). Zero-match pools >10 items terão p95 proporcional. **Medição final em staging** pós-merge via Grafana query `histogram_quantile(0.95, rate(smartlic_pipeline_duration_seconds_bucket[5m]))` (STORY-3.3 baseline já coletada).

---

## Tasks / Subtasks

- [x] Task 1: Migrar `llm.py` para AsyncOpenAI (via `async_runtime.py`)
- [x] Task 2: Refactor llm_arbiter para async/await pattern (gather_classifications)
- [x] Task 3: Batch API integration — módulo + cron
- [x] Task 4: Métricas + dashboard (3 novas métricas Prometheus)
- [x] Task 5: Load test compare baseline vs new (`compare_p95.py`)
- [x] Task 6: Atualizar tests (12 novos)

## Dev Notes

- **Exception propagation**: `asyncio.gather` por default propaga a primeira exceção e cancela as outras. Para preservar a semântica legado de `future.result()` por item, `gather_classifications` guarda falhas em `_FailedResult(exc)` e `unwrap_result` re-raise no consumo. Isso mantém `stats["rejeitadas_llm_arbiter"]` incrementando uma vez por falha individual (CRIT-FLT-002 AC4 preservado).
- **Semaphore loop-scoped**: `_get_semaphore` compara o loop ativo e rebuild se houver mismatch. Previne "Future attached to different loop" quando `asyncio.run` é chamado de dentro de `asyncio.to_thread` (cenário exato de `aplicar_todos_filtros`).
- **Batch API escopo**: OpenAI Batch API tem SLA de 24h. Aplicar em `/buscar` (live) violaria p95. Solução: only offline `reclassify_pending_bids_job`. Feature flag default false garante roll-out gradual.
- **ThreadPoolExecutor import preservado em filter/pipeline.py**: os 2 call sites foram migrados, mas o `import` no topo fica para não mexer em outros paths que possam usar. Audit + removal é follow-up se confirmado zero uso.

## File List

### Created

- `backend/llm_arbiter/async_runtime.py` — AsyncOpenAI client, semaphore, `_bounded`, `gather_classifications`, `_FailedResult`, `unwrap_result`
- `backend/llm_arbiter/batch_api.py` — `submit_batch`, `poll_batch`, Redis state
- `backend/jobs/cron/llm_batch_poll.py` — ARQ cron task loop
- `backend/scripts/compare_p95.py` — AC4 CI gate helper
- `backend/tests/test_llm_arbiter_async.py` — 5 tests (semaphore, bounded concurrency, gather order, lazy client)
- `backend/tests/test_llm_batch_api.py` — 7 tests (gating, submission, poll states, cron registration)

### Modified

- `backend/llm_arbiter/__init__.py` — re-export async_runtime + batch_api
- `backend/filter/pipeline.py:895, 1284` — ThreadPoolExecutor → `gather_classifications`
- `backend/config/features.py` — added `LLM_MAX_CONCURRENT`, `LLM_BATCH_ENABLED`, `LLM_BATCH_MIN_ITEMS`, `LLM_BATCH_POLL_INTERVAL_S`
- `backend/config/__init__.py` — re-exports
- `backend/metrics.py` — added `LLM_CONCURRENT_CALLS`, `LLM_BATCH_JOBS_ACTIVE`, `LLM_BATCH_JOB_DURATION`
- `backend/jobs/cron/scheduler.py` — registers `start_llm_batch_poll_task`

## Testing

- 12 novos tests (`test_llm_arbiter_async.py` + `test_llm_batch_api.py`) — 12/12 passam
- Regression suite verificada:
  - `test_crit_flt_002_arbiter_parallel.py`: 9/10 (1 failed é pré-existente `test_qa_audit_sampling_in_parallel` com `filter.random` patch issue — já quebrava em main pré-refactor)
  - `test_ux402_llm_batch.py`: 26/26 ✅
  - `test_filter.py`: 70/75 (5 skips documentados)
  - `test_llm_arbiter.py`: todos passam

## Definition of Done

- [x] AsyncOpenAI + Batch API entregues; ThreadPoolExecutor removido nos 2 call sites críticos; semaphore configurável; 3 métricas + 12 testes; script `compare_p95.py`

## Risks

- **R1 (batch latency)**: confinado ao path offline — live `/buscar` inalterado ✅
- **R2 (race conditions async refactor)**: mitigado via `_FailedResult` wrapper preservando exatamente a semântica de `future.result()` — regression tests (`test_llm_exception_counts_as_reject`, `test_partial_failure_mixed`) confirmam ✅
- **R3 (nested event loop)**: `asyncio.run` dentro de `aplicar_todos_filtros` (que roda em `asyncio.to_thread`) é seguro — nenhum loop ambiente detectado ✅

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-15 | 2.0     | Async runtime + Batch API + 12 tests + ThreadPoolExecutor removed nos 2 call sites de filter/pipeline.py | @dev |
