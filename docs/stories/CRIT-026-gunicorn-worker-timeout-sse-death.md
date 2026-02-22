# CRIT-026 — Gunicorn Worker Timeout Matando SSE Streams Ativos

**Status:** Pending
**Priority:** Critical
**Severity:** Fatal (backend) + Error Regressed (frontend)
**Sentry Issues:**
- SMARTLIC-BACKEND-1B (#7283894536) — WORKER TIMEOUT (pid:7), Level: Fatal
- SMARTLIC-BACKEND-1A (#7283894498) — Worker (pid:7) was sent SIGABRT!, Level: Error
- SMARTLIC-FRONTEND-3 (#7282619928) — Error: failed to pipe response, Level: Error, **REGRESSED**
**Created:** 2026-02-22
**Relates to:** CRIT-012 (SSE Heartbeat Gap + Undici BodyTimeoutError)

---

## Contexto

Sentry reporta 3 issues correlatas que formam uma cascata de falha:

### Cadeia de Falha

```
1. Gunicorn worker handles long search request (>600s timeout)
   -> WORKER TIMEOUT (pid:7)          [FATAL, gunicorn.error]
   -> Worker (pid:7) sent SIGABRT!    [ERROR, gunicorn.error]

2. Backend SSE stream dies abruptly (worker killed)
   -> Frontend SSE proxy gets broken pipe

3. Frontend SSE proxy fails
   -> BodyTimeoutError: Body Timeout Error     [root cause]
   -> TypeError: terminated                     [cascaded - socket closed]
   -> Error: failed to pipe response            [cascaded - Next.js]
```

### Timeline (Sentry breadcrumbs)

| Time (UTC) | Event |
|---|---|
| 12:49:21 | Backend server started (gunicorn + 2 UvicornWorkers) |
| 13:44:49 | Frontend server started |
| 13:47:14 | Frontend SSE proxy connects to backend (HTTP 200) |
| **13:53:38** | **Frontend: BodyTimeoutError on SSE stream** |
| **13:54:31** | **Backend: Worker pid:2 TIMEOUT + SIGABRT** |
| **13:59:31** | **Backend: Worker pid:7 TIMEOUT + SIGABRT** |

Ambos os workers (WEB_CONCURRENCY=2) morreram em sequencia, causando indisponibilidade temporaria.

## Analise Detalhada

### Backend: Gunicorn Worker Timeout

Configuracao atual (`backend/start.sh`):
```bash
exec gunicorn main:app \
  -k uvicorn.workers.UvicornWorker \
  -w "${WEB_CONCURRENCY:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-600}" \       # 10 min
  --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT:-60}"
```

O gunicorn mata workers que nao respondem apos `--timeout` segundos. Para SSE endpoints, o worker esta "ocupado" durante toda a duracao do stream, mesmo que esteja idle esperando eventos. Isso e um **conflito arquitetural**: SSE streams sao long-lived por natureza, mas gunicorn trata inatividade como timeout.

### Frontend: BodyTimeoutError Regressao

O CRIT-012 implementou `bodyTimeout: 0` via `undici.Agent`:

```typescript
// frontend/app/api/buscar-progress/route.ts:49-67
const undiciModule = await import("undici");
fetchOptions.dispatcher = new UndiciAgent({
  bodyTimeout: 0,          // Desabilita body timeout
  headersTimeout: 30_000,  // 30s para headers
});
```

**Porem o erro persiste.** Possiveis causas:

1. **`import("undici")` falha silenciosamente** — Node 20 tem undici built-in mas `import("undici")` pode nao funcionar se nao esta no `package.json`
2. **O `dispatcher` option e ignorado** pelo `fetch()` interno do Node em certas versoes
3. **O erro nao e body timeout propriamente** — e a conexao TCP sendo fechada (worker SIGABRT), que undici interpreta como BodyTimeoutError
4. **O backend nao esta enviando heartbeats** — se o SSE generator stalla >15s sem heartbeat, undici pode timeout antes mesmo do `bodyTimeout: 0` tomar efeito (race condition no startup)

## Arquivos Envolvidos

| Arquivo | Relevancia |
|---|---|
| `backend/start.sh:29-35` | Gunicorn timeout config |
| `backend/routes/search.py:68-70,214-330` | SSE heartbeat generator |
| `frontend/app/api/buscar-progress/route.ts:49-67` | Undici bodyTimeout fix |
| `backend/search_pipeline.py:855` | FETCH_TIMEOUT=360s |

## Acceptance Criteria

### Track 1: Gunicorn Worker Timeout (Backend)

- [ ] **AC1:** Investigar se `GUNICORN_TIMEOUT` no Railway esta realmente em 600s ou foi overridado
- [ ] **AC2:** Considerar alternativas ao gunicorn para SSE:
  - Opcao A: Usar `uvicorn` direto (sem gunicorn wrapper) — remove timeout per-worker
  - Opcao B: Aumentar `--timeout` para 900s (15min) e adicionar watchdog no SSE generator
  - Opcao C: Separar SSE endpoint em processo dedicado (process type `sse`)
- [ ] **AC3:** Adicionar metric `smartlic_worker_timeout_total` para tracking via Prometheus
- [ ] **AC4:** Aumentar `WEB_CONCURRENCY` de 2 para 3+ (evita indisponibilidade total quando 1 worker morre)

### Track 2: Frontend SSE Resilience (Frontend)

- [ ] **AC5:** Verificar se `import("undici")` esta realmente funcionando em producao:
  - Adicionar log: `console.log("[SSE-PROXY] undici dispatcher:", fetchOptions.dispatcher ? "custom" : "default")`
  - Se `undici` nao esta importavel, instalar como dependencia explicita: `npm install undici`
- [ ] **AC6:** Adicionar fallback: se `undici.Agent` nao disponivel, usar `AbortSignal.timeout()` como safety net
- [ ] **AC7:** No handler de `BodyTimeoutError`, tentar reconectar 1x antes de retornar 504 ao client

### Track 3: Observabilidade

- [ ] **AC8:** Logar no backend quando SSE generator finaliza abruptamente (conexao fechada pelo client/proxy)
- [ ] **AC9:** Adicionar breadcrumb no Sentry frontend com `search_id` e `elapsed_ms` antes do fetch SSE
- [ ] **AC10:** Resolver as 3 issues no Sentry apos deploy

## Impacto em Producao

| Cenario | Impacto | Frequencia |
|---|---|---|
| 1 worker timeout | 50% capacidade perdida (2→1 worker) | Medio |
| 2 workers timeout | **Indisponibilidade total** ate auto-restart | Baixo mas ocorreu |
| SSE stream morre | Busca parece travada, usuario sem feedback | Alto (toda vez que worker morre) |

## Recomendacao

**Opcao B (Curto prazo):** Aumentar `GUNICORN_TIMEOUT` para 900s + `WEB_CONCURRENCY=3` + fix undici import.
Resolve o sintoma imediato sem refactoring.

**Opcao C (Medio prazo):** Separar SSE em processo dedicado com uvicorn puro (sem gunicorn).
Resolve o conflito arquitetural (gunicorn timeout vs SSE long-lived).

## Verificacao

```bash
# Verificar config atual no Railway
railway variables | grep -E "GUNICORN|WEB_CONCURRENCY"

# Testar SSE stream duracao
curl -N "https://api.smartlic.tech/v1/buscar-progress/test-id" \
  -H "Accept: text/event-stream" --max-time 700

# Verificar undici em producao
railway run node -e "import('undici').then(m => console.log('OK', Object.keys(m))).catch(e => console.log('FAIL', e.message))"
```

## Estimativa

- **Esforco:** Medio (config + investigacao undici + observabilidade)
- **Risco:** Baixo se Opcao B, Medio se Opcao C
- **Impacto:** Critico (indisponibilidade total possivel com 2 workers mortos)
