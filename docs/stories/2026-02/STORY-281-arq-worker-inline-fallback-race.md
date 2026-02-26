# STORY-281: ARQ Worker Race Condition — Double Execution Fix

**Priority:** P0 BLOCKER
**Effort:** 1 day
**Squad:** @dev + @qa
**Fundamentacao:** Logs de producao 2026-02-26 (search 90578569)

## Problema Observado em Producao

```
00:58:39  POST /buscar → 202 (async mode, job enqueued)
00:58:39  Worker PEGOU o job (0.30s pickup latency)
00:59:09  Web server timeout 30s → executa INLINE (mesma busca!)
01:01:44  Worker completa apos 185s (0 results — PNCP timeout)
01:01:xx  Inline tambem completa (mesma busca, mesmos timeouts)
```

**Impacto:** Toda busca roda DUAS VEZES — no worker E inline. Dobra a carga no PNCP, dobra conexoes Redis, desperdiça CPU.

## Root Cause

`routes/search.py` enfileira o job via ARQ e depois aguarda resultado por `_ASYNC_WAIT_TIMEOUT=30s`. Se o worker nao completa em 30s, executa inline como fallback.

Problema: buscas com 1 UF (SP) levam 180s+ quando PNCP esta lento. O timeout de 30s SEMPRE estourara, causando double execution em 100% dos casos.

## Acceptance Criteria

### AC1: Aumentar async wait timeout para 120s
- [x] `routes/search.py`: `SEARCH_ASYNC_WAIT_TIMEOUT = 120` (era 30 via SEARCH_WORKER_FALLBACK_TIMEOUT)
- [x] Configurable via env `SEARCH_ASYNC_WAIT_TIMEOUT` (default 120)
- [x] Se worker completa em tempo, retorna resultado do worker (nao executa inline)

### AC2: Cancelar job no worker quando fallback inline inicia
- [x] Se timeout expira, enviar signal de cancel para o worker via Redis (`set_cancel_flag`)
- [x] Worker checa cancel flag periodicamente (`check_cancel_flag` before and after pipeline)
- [x] Evita execucao duplicada — worker returns `{status: "cancelled"}` and discards results

### AC3: SSE mantém heartbeat durante o wait
- [x] SSE endpoint envia `: heartbeat\n\n` a cada 15s enquanto aguarda worker (CRIT-012)
- [x] Se worker emitir progress events, propagar via SSE (existing tracker→queue→SSE)
- [x] Frontend mantem conexao aberta (bodyTimeout: 0 ja configurado em CRIT-012)

### AC4: Metrics de observabilidade
- [x] `smartlic_search_inline_fallback_total` — counter de fallbacks inline (metrics.py)
- [x] `smartlic_search_worker_completion_seconds` — histogram do tempo do worker (metrics.py)
- [x] Log estruturado: `{"event": "inline_fallback", "search_id": X, "wait_timeout": 120}`

## Files to Modify

| File | Change |
|------|--------|
| `backend/routes/search.py` | Increase timeout, add cancel logic |
| `backend/job_queue.py` | Add cancel check in search_job |
| `backend/config.py` | SEARCH_ASYNC_WAIT_TIMEOUT |
| `backend/metrics.py` | New counters |

## Files Modified

| File | Change |
|------|--------|
| `backend/config.py` | `SEARCH_ASYNC_WAIT_TIMEOUT=120` + legacy alias |
| `backend/metrics.py` | `SEARCH_INLINE_FALLBACK` counter + `SEARCH_WORKER_COMPLETION` histogram |
| `backend/job_queue.py` | `set_cancel_flag`, `check_cancel_flag`, `clear_cancel_flag` + search_job cancel checks |
| `backend/routes/search.py` | Watchdog uses 120s timeout, sets cancel flag on fallback, emits metrics |
| `backend/tests/test_story281_double_execution.py` | 24 tests covering AC1-AC4 |
| `docs/stories/2026-02/STORY-281-arq-worker-inline-fallback-race.md` | Checkboxes marked |

## Evidencia

Worker log:
```
00:58:39:   0.30s → search:90578569:search_job(...)
[CONSOLIDATION] PNCP: timeout after 180001ms — no records
[CONSOLIDATION] Degraded mode — Partial results: sources failed: PNCP
[STAB-003] Time budget exceeded after filter (182.7s > 90s)
01:01:44: 185.08s ← search:90578569:search_job ● total_results: 0
```
