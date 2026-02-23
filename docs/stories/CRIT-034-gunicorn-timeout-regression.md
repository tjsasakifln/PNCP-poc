# CRIT-034 — Gunicorn Worker Timeout Regression (CRIT-026 Recorrente)

**Status:** Pending
**Priority:** P0 — Critical
**Severity:** Fatal (backend indisponível)
**Sentry Issues:**
- SMARTLIC-BACKEND-1B (#7283894536) — WORKER TIMEOUT (pid:4/10), Level: Fatal, 4 events
- SMARTLIC-BACKEND-1A (#7283894498) — Worker (pid:4/10) was sent SIGABRT!, Level: Error, 4 events
- SMARTLIC-BACKEND-J (#7272358405) — Downtime detected for api.smartlic.tech, Age: 6d
- SMARTLIC-BACKEND-1D (#7284842971) — CancelledError on /v1/buscar, Level: Error
- SMARTLIC-FRONTEND-3 (#7282619928) — Error: failed to pipe response, **REGRESSED**, 4 events
- SMARTLIC-FRONTEND-1 (#7280268567) — Error: failed to pipe response, **REGRESSED**, 13 events
**Created:** 2026-02-23
**Relates to:** CRIT-026 (original, marked Done), CRIT-012 (SSE Heartbeat)

---

## Problema

CRIT-026 foi marcado como Done em 2026-02-22, mas as mesmas issues reaparecem com novos PIDs (pid:4, pid:10 vs pid:7 original). O backend continua matando workers durante buscas longas, causando:

1. **Backend downtime** — Ambos workers morrem em sequência
2. **SSE stream cortado** — Frontend recebe "failed to pipe response"
3. **CancelledError** — Requests asyncio cancelados
4. **524 Cloudflare timeout** — Observado na validação UX (busca "Todo o Brasil" timeout após ~98s)

### Evidência da Validação UX (2026-02-23)

```
1. Busca Vestuário "Todo o Brasil" → 524 timeout após ~98s
2. Frontend: "Não foi possível processar sua busca"
3. Auto-retry countdown (CRIT-008 feature working)
4. Backend red dot (CRIT-008 BackendStatusIndicator showing)
```

### Sentry Timeline Atualizada

| Issue | Last Seen | Events | Trend |
|-------|-----------|--------|-------|
| WORKER TIMEOUT (pid:4) | **NOW** (in 1min) | 4 | New |
| Worker SIGABRT (pid:4) | **NOW** (in 1min) | 4 | New |
| Downtime api.smartlic.tech | **NOW** (in 7s) | ongoing | 6d old |
| failed to pipe response (FE-3) | 26s ago | 4 | Regressed |
| failed to pipe response (FE-1) | 10hr ago | 13 | Regressed |
| CancelledError | 10hr ago | 1 | New |

## Análise

### Por que CRIT-026 não resolveu

CRIT-026 aumentou `GUNICORN_TIMEOUT` de 600s para valor maior, mas:

1. **Busca "Todo o Brasil" (27 UFs)** leva 70-183s normalmente
2. **Com backend sob carga**, pode exceder até timeouts generosos
3. **WEB_CONCURRENCY=2** — apenas 2 workers → uma busca longa bloqueia 50% da capacidade
4. **Railway sleep/restart** — container pode reiniciar, matando workers ativos

### Causa Raiz Profunda

O problema não é o timeout em si, mas a **arquitetura de busca síncrona**:
- Uma request `/v1/buscar` bloqueia um worker por 70-183s
- Com 2 workers, 2 buscas simultâneas = 100% saturação
- Qualquer 3ª request → timeout/queue

## Acceptance Criteria

### Mitigação Imediata (Sprint atual)

- [ ] **AC1**: Aumentar `WEB_CONCURRENCY` para 4 (Railway 1GB RAM suporta 4 uvicorn workers)
- [ ] **AC2**: Aumentar `GUNICORN_TIMEOUT` para 900s (15min) para cobrir buscas extremas
- [ ] **AC3**: Adicionar `--keep-alive 75` ao gunicorn (default 2s é muito baixo para SSE)
- [ ] **AC4**: Verificar `GUNICORN_GRACEFUL_TIMEOUT` >= 120s (permitir SSE cleanup)

### Monitoramento

- [ ] **AC5**: Alerta Sentry quando WORKER TIMEOUT ocorrer (threshold: 2 events/hour)
- [ ] **AC6**: Métrica Prometheus `gunicorn_workers_killed_total` (já existe em metrics.py?)
- [ ] **AC7**: Log structured ao matar worker: `{ worker_pid, request_duration, endpoint, search_id }`

### Solução Definitiva (Sprint futuro)

- [ ] **AC8**: Migrar busca para modelo async (request retorna search_id, resultado via polling/SSE)
- [ ] **AC9**: Worker nunca mantém connection >30s para /buscar (dispatch para job queue)

## Files Envolvidos

- `backend/start.sh` — Gunicorn config (timeout, workers, keep-alive)
- `backend/Procfile` / Railway config — WEB_CONCURRENCY
- `backend/metrics.py` — Worker kill metrics
- `backend/search_pipeline.py` — Busca síncrona (refactor futuro)
