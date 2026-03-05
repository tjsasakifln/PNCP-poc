# CRIT-052: Health Canary PNCP — Falso Positivo por Timeout Agressivo

**Prioridade:** CRITICAL
**Componente:** Backend — pncp_client.py
**Origem:** Incidente 2026-03-05 — PNCP respondendo em 700ms-4s mas canary descarta fonte inteira

## Problema

O health canary per-search usa `CANARY_TIMEOUT = 5.0s`. O PNCP esta respondendo (status=degraded, latencia 700ms-4s), mas nos picos de latencia o canary estoura o timeout e descarta o PNCP inteiro para aquela busca.

Resultado: fonte primaria (que TEM dados de status confiaveis) e tratada como morta quando esta apenas lenta. O fallback (PCP v2) sozinho e inutil — 95% das licitacoes sao rejeitadas pelo filtro de status.

### Evidencia nos Logs

```
[PNCP cron canary] status=degraded, latency=4027ms (respondendo!)
[Per-search canary] PNCP health check failed (timeout) — skipping PNCP
```

## Solucao

Canary mais tolerante + fallback gradual em vez de tudo-ou-nada.

## Acceptance Criteria

### AC1: Timeout adaptativo
- [x] `CANARY_TIMEOUT` aumentado de 5s para 10s (env var `PNCP_CANARY_TIMEOUT_S`)
- [x] Se cron canary reporta status=degraded (mas respondendo), per-search canary usa timeout estendido (15s)
- [x] Se cron canary reporta status=healthy, per-search canary usa timeout padrao (10s)

### AC2: Canary nao bloqueia — apenas alerta
- [x] Quando canary falha por timeout, NAO retornar empty results imediatamente
- [x] Em vez disso, tentar fetch normal com timeout estendido (30s para UFs individuais)
- [x] Se fetch normal TAMBEM falha, ai sim descartar PNCP e logar

### AC3: Cron canary alimenta decisao
- [x] `cron_jobs.run_health_canary` armazena ultimo status em variavel global thread-safe
- [x] Per-search canary consulta status do cron antes de decidir timeout
- [x] Status possiveis: `healthy` (latencia < 2s), `degraded` (2-10s), `down` (sem resposta)

### AC4: Log honesto
- [x] Quando PNCP e descartado, logar motivo real: `"PNCP skipped: canary timeout after Xs (cron status: degraded, last_latency: Yms)"`
- [x] Incluir no search_complete event: `pncp_canary_status`, `pncp_canary_latency_ms`

### AC5: Testes
- [x] Test: PNCP respondendo em 4s com canary timeout 10s → PNCP usado normalmente
- [x] Test: PNCP respondendo em 12s com canary timeout 10s → timeout estendido aplicado
- [x] Test: PNCP sem resposta em 15s → descartado corretamente
- [x] Test: cron status=degraded → per-search usa timeout estendido

## Arquivos Afetados

- `backend/pncp_client.py` — `health_canary()`, `buscar_todas_ufs_paralelo()`
- `backend/cron_jobs.py` — `run_health_canary()` armazena status global + `get_pncp_cron_status()`
- `backend/config.py` — `PNCP_CANARY_TIMEOUT_S`, `PNCP_CANARY_TIMEOUT_EXTENDED_S`
- `backend/search_pipeline.py` — `search_complete` event inclui canary telemetry
- `backend/tests/test_crit052_canary_false_positive.py` — 15 testes novos
