# CRIT-033 — ARQ Job Enqueue Falha: NoneType (Worker Não Ativo)

**Status:** Pending
**Priority:** P1 — High
**Severity:** Error (silencioso — busca completa mas sem LLM summary/Excel)
**Sentry Issues:**
- SMARTLIC-BACKEND-1F (#7284854767) — Failed to enqueue llm_summary_job: 'NoneType' object has no attribute 'job_id'
- SMARTLIC-BACKEND-1E (#7284854756) — Failed to enqueue excel_generation_job: 'NoneType' object has no attribute 'job_id'
**Created:** 2026-02-23
**Relates to:** F-01 (ARQ Job Queue), CRIT-026 (Worker Timeout)

---

## Problema

Após deploy do F-01 (ARQ Job Queue), os jobs de LLM summary e Excel generation falham silenciosamente em produção. O `pool.enqueue_job()` retorna `None` em vez de um objeto `Job`, e o acesso a `.job_id` gera `AttributeError`.

### Cadeia de Falha

```
1. search_pipeline.py: "Queue mode: dispatching LLM + Excel jobs for search_id=..."
2. Redis PING → OK (pool conecta normalmente)
3. pool.enqueue_job('llm_summary_job', ...) → retorna None
4. result.job_id → AttributeError: 'NoneType' object has no attribute 'job_id'
```

### Causa Raiz Provável

O ARQ pool conecta ao Redis mas `enqueue_job` retorna `None` quando:

1. **Worker não está rodando** — `PROCESS_TYPE=worker` não foi deployado no Railway
2. **Função não registrada** — A função `llm_summary_job` não está no `WorkerSettings.functions`
3. **ARQ pool stale** — Pool foi criado antes do worker estar pronto

### Evidência (Sentry Breadcrumbs)

```
02:31:21.380 — Redis PING (OK)
02:31:21.381 — Redis PING (OK)
02:31:21.382 — search_pipeline: "Queue mode: dispatching LLM + Excel jobs"
02:31:21.391 — Redis PING (OK)
02:31:21.395 — ERROR: "Failed to enqueue llm_summary_job: 'NoneType'..."
```

### Impacto

| Feature | Estado | Impacto |
|---------|--------|---------|
| LLM Summary | Fallback inline | Usuário recebe `gerar_resumo_fallback()` (puro Python, genérico) em vez de resumo IA |
| Excel Export | Fallback inline | Excel gerado inline (bloqueia response se pesado) em vez de background |
| SSE events | Nunca emitidos | `llm_ready` e `excel_ready` nunca chegam ao frontend |

**Nota:** O fallback funciona — busca não quebra. Mas o valor agregado de F-01 (background processing) está inativo.

## Acceptance Criteria

- [ ] **AC1**: Verificar se `PROCESS_TYPE=worker` está configurado como serviço separado no Railway
- [ ] **AC2**: Se worker não existe, criar Railway service com `PROCESS_TYPE=worker` usando mesmo Dockerfile
- [ ] **AC3**: Se worker existe, verificar logs do worker para erros de conexão/startup
- [ ] **AC4**: `pool.enqueue_job()` deve retornar Job object (não None) — testar com log do job_id
- [ ] **AC5**: Após fix, LLM summary via SSE (`llm_ready` event) funciona em produção
- [ ] **AC6**: Após fix, Excel via SSE (`excel_ready` event) funciona em produção
- [ ] **AC7**: Sentry issues SMARTLIC-BACKEND-1F e 1E marcados como resolved
- [ ] **AC8**: Fallback continua funcionando se ARQ/Redis indisponível (zero regression)

## Diagnóstico Rápido

```bash
# 1. Verificar serviços no Railway
railway status

# 2. Verificar se worker está rodando
railway logs --service worker

# 3. Verificar variáveis
railway variables --service worker | grep PROCESS_TYPE

# 4. Se não existe, criar:
# Railway Dashboard → New Service → Same repo → Set PROCESS_TYPE=worker
```

## Files Envolvidos

- `backend/job_queue.py` — Pool creation, enqueue logic
- `backend/start.sh` — PROCESS_TYPE routing (web vs worker)
- `backend/search_pipeline.py` — Job dispatch call site
- Railway config — Service configuration
