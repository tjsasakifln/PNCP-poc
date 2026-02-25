# GTM-STAB-002 — Estabilizar Redis e ARQ Worker

**Status:** Code Complete (needs deploy + prod validation)
**Priority:** P0 — Blocker (worker em crash loop impede jobs)
**Severity:** Infra — Redis TimeoutError mata worker, jobs falham
**Created:** 2026-02-24
**Sprint:** GTM Stabilization (imediato)
**Relates to:** GTM-RESILIENCE-F01 (ARQ job queue), CRIT-033 (worker liveness)
**Sentry:** Failed to enqueue llm_summary_job (2), Failed to enqueue excel_generation_job (2), WORKER TIMEOUT (4), SIGABRT (4)
**Railway Logs:** Redis `TimeoutError` + `CancelledError` + `asyncio.open_connection` failure

---

## Problema

O ARQ worker em produção está em **crash loop**. Os logs do Railway mostram a sequência:

```
1. Jobs executam com sucesso (bid_analysis 4s, llm_summary 9.5s)
2. Redis connection falha → TimeoutError em asyncio.open_connection
3. Worker recebe CancelledError
4. Worker morre (exit)
5. Railway reinicia → volta ao passo 1
```

### Causas identificadas

**1. Redis connectivity instável (Railway addon)**
- `asyncio.open_connection` falha com `TimeoutError` no DNS resolve (`getaddrinfo`)
- Isso sugere que o Redis addon do Railway tem networking instável
- O worker não tem retry/reconnect — morre na primeira falha

**2. ARQ worker sem resiliência de conexão**
- `job_queue.py:38-59` — `_get_redis_settings()` configura RedisSettings sem `conn_timeout`, `conn_retries`, ou `retry_on_timeout`
- O singleton `_arq_pool` perde conexão e nunca reconecta automaticamente
- `WorkerSettings` não define `health_check_interval`, `health_check_key`, ou `retry_jobs`

**3. Web process também afetado**
- `get_arq_pool()` tenta `ping()` → falha → seta `_arq_pool = None` → recria pool
- MAS entre falha e recriação, `enqueue_job()` recebe `pool = None` → log "Failed to enqueue"
- O fallback inline funciona (CRIT-033: `is_queue_available()` retorna False), mas o Sentry recebe error de qualquer forma

**4. CRIT-033 worker liveness check pode falso-positivo**
- Health check key tem cache de 60s (`_WORKER_CHECK_INTERVAL`)
- Worker morre → 60s de falso-positivo onde sistema acha que worker está vivo → enqueue falha

### Impacto

- LLM summaries e Excel generation falham esporadicamente
- 4 eventos de WORKER TIMEOUT + 4 SIGABRT = workers morrendo
- Sentry poluído com errors que degradam visibilidade de problemas reais
- Usuário não recebe Excel nem resumo AI (silent failure — resultado incompleto)

---

## Acceptance Criteria

### AC1: Migrar Redis para Upstash (ou estabilizar Railway addon)
- [ ] Avaliar Redis atual: `railway variables | grep REDIS`
- [ ] **Opção A (recomendada):** Provisionar Upstash Redis (free tier, 256MB, persistente)
  - Criar em https://console.upstash.com
  - Atualizar `REDIS_URL` no Railway
  - Upstash tem TLS nativo e melhor estabilidade de rede
- [ ] **Opção B:** Manter Railway Redis mas adicionar retry config
- [ ] Testar conectividade: `redis-cli -u $REDIS_URL ping` retorna PONG

### AC2: Adicionar resiliência à conexão Redis no ARQ
- [x] `_get_redis_settings()` em `job_queue.py:60-64` — conn_timeout=10, conn_retries=5, conn_retry_delay=2.0, ssl auto-detected ✅ (commit `899ee07`)
- [x] `get_arq_pool()` retry com backoff: 3 tentativas, 2s/4s/8s exponential delay ✅ (job_queue.py:67-103)
- [x] Log structured: `redis_pool_reconnect(attempt=N, delay=Xs, error=...)` ✅

### AC3: Worker resilience — reconexão automática
- [x] `WorkerSettings` — health_check_interval=30, max_tries=3, job_timeout=300 ✅ (job_queue.py:880-881)
- [ ] Worker deve capturar `ConnectionError`/`TimeoutError` no poll loop e reconectar — ⚠️ ARQ vanilla doesn't support (issue #386)
- [x] Wrapper no `start.sh` que reinicia automaticamente ✅ (start.sh:49-69, max 10 restarts, 5s delay):
  ```bash
  worker)
    while true; do
      echo "Starting ARQ worker..."
      arq job_queue.WorkerSettings || true
      echo "Worker died, restarting in 5s..."
      sleep 5
    done
  ```

### AC4: Reduzir cache de worker liveness
- [x] `_WORKER_CHECK_INTERVAL` = 15s ✅ (job_queue.py:35, comment "GTM-STAB-002 AC4")
- [x] Quando worker morre, sistema detecta em max 15s ✅
- [x] Fallback inline ativa em <15s após worker crash ✅

### AC5: Enqueue errors não devem ir para Sentry
- [x] `enqueue_job()` — `logger.warning` não ERROR ✅ (job_queue.py:224)
- [x] Sentry capture level WARNING ✅
- [x] Log local mantido para debugging ✅
- [x] Fallback inline failure → WARNING em search_pipeline.py:2071/2091 ✅

**Production health check (2026-02-25):** Redis UP (2ms latency), ARQ Worker UP per /health endpoint.

### AC6: Validação end-to-end
- [ ] Deploy web + worker — ⚠️ Worker confirmed UP via /health, search_job() confirmed dispatched via Railway logs
- [ ] Fazer 5 buscas consecutivas, todas devem retornar LLM summary via SSE `llm_ready`
- [ ] Matar worker manualmente (`railway service restart worker`), fazer busca → fallback inline funciona
- [ ] Monitorar Sentry por 2h → 0 novos eventos de enqueue failure
- [ ] `arq:queue:health-check` key visível no Redis quando worker está vivo

---

## Arquivos Envolvidos

| Arquivo | Ação |
|---------|------|
| `backend/job_queue.py:38-59` | AC2: Redis conn_timeout, retries |
| `backend/job_queue.py:62-89` | AC2: get_arq_pool retry com backoff |
| `backend/job_queue.py:104-136` | AC4: _WORKER_CHECK_INTERVAL 60→15 |
| `backend/job_queue.py:159-179` | AC5: enqueue log level WARNING |
| `backend/job_queue.py` WorkerSettings | AC3: health_check, retry_jobs |
| `backend/start.sh:49-52` | AC3: wrapper com restart automático |
| Railway env vars | AC1: REDIS_URL → Upstash |

---

## Decisões Técnicas

- **Upstash > Railway Redis** — Railway Redis addon é efêmero (perde dados no restart), networking instável dentro do cluster Railway. Upstash é gerenciado, persistente, TLS, melhor SLA
- **Worker restart wrapper** — ARQ não tem reconexão built-in no poll loop. Wrapper shell é padrão na indústria (Celery faz o mesmo)
- **15s liveness** — Balanceia entre overhead de Redis roundtrips e velocidade de failover

## Estimativa
- **Esforço:** 3-4h
- **Risco:** Médio (mudança de infra Redis requer migração de URL)
- **Squad:** @devops (Redis migration) + @dev (job_queue resilience) + @qa (E2E validation)
