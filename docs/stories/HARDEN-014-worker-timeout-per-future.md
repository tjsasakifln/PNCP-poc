# HARDEN-014: ThreadPoolExecutor Timeout por Future (LLM Batches)

**Severidade:** ALTA
**Esforço:** 30 min
**Quick Win:** Nao
**Origem:** Conselho CTO — Auditoria de Fragilidades (2026-03-06)

## Contexto

`ThreadPoolExecutor(max_workers=3)` em `filter.py:3194` submete batches para classificação LLM. `as_completed()` não tem timeout por future individual. Se OpenAI trava em 1 batch, bloqueia o executor. O budget check (CRIT-057) existe mas age sobre elapsed total, não per-future.

## Critérios de Aceitação

- [x] AC1: `wait(timeout=20)` com `FIRST_COMPLETED` ao invés de `as_completed()`
- [x] AC2: Futures que excedem timeout são cancelled
- [x] AC3: Items não classificados marcados como `pending_review`
- [x] AC4: Metric `smartlic_llm_batch_timeout_total`
- [x] AC5: Teste unitário com future que trava
- [x] AC6: Zero regressions

## Arquivos Afetados

- `backend/filter.py` — 3 ThreadPoolExecutor loops converted (zero-match batch, zero-match individual, arbiter)
- `backend/metrics.py` — `LLM_BATCH_TIMEOUT` counter with `phase` label
- `backend/tests/test_harden014_future_timeout.py` — 5 tests (batch timeout, fast batch, individual timeout, arbiter timeout, metric)
