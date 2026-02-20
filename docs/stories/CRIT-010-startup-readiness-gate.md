# CRIT-010: Startup Readiness Gate — Prevenir Trafego Antes de Workers Prontos

## Epic
Consistencia Estrutural do Sistema (EPIC-CRIT)

## Sprint
Sprint 5: Resiliencia de Producao

## Prioridade
P1

## Estimativa
8h

## Descricao

O backend aceita trafego antes que todos os workers Gunicorn/Uvicorn estejam prontos para servir requisicoes. Durante este intervalo (~5-15s), requests chegam a workers que ainda nao registraram as rotas FastAPI, resultando em HTTP 404 — mesmo para endpoints validos como `/health`.

### Problema

```
Timeline de restart:
t=0     Gunicorn master inicia
t=1     Worker 1 faz fork → inicia import de modulos
t=2     Worker 2 faz fork → inicia import de modulos
t=3     Railway health check chega → Worker 1 ainda importando → 404
t=5     Worker 1 termina imports → rotas registradas → 200
t=8     Worker 2 termina imports → rotas registradas → 200
```

O problema e que Gunicorn começa a aceitar conexoes TCP antes que workers completem o import dos modulos e registrem as rotas. Isso causa:
- Health check intermitente: 404 → 200 → 404 → 200 (dependendo de qual worker responde)
- Frontend detecta backend "morto" e ativa modo offline
- Usuario ve erro transiente que se resolve sozinho em segundos

### Evidencia

Nos logs do Railway (2026-02-20), o frontend logou `Backend health check failed with status: 404` repetidamente. No entanto, curl para `https://api.smartlic.tech/health` retornou 200 quando testado segundos depois. O backend tem import chain pesada (~65 modulos Python) que leva varios segundos para completar.

### Abordagem: Gunicorn --preload

`gunicorn --preload` carrega a aplicacao ASGI no master process ANTES de fazer fork dos workers. Isso garante que:
1. Todos os imports sao resolvidos no master
2. Workers ja nascem com rotas registradas
3. Nenhum request chega a worker sem rotas

Trade-off: `--preload` desabilita hot-reload (irrelevante em producao) e aumenta uso de memoria do master process (~50-100MB a mais). Aceitavel.

## Criterios de Aceite

### Gunicorn Preload

- [ ] AC1: `backend/start.sh` deve adicionar `--preload` ao comando gunicorn para `PROCESS_TYPE=web`:
  ```bash
  exec gunicorn main:app \
    --preload \
    -k uvicorn.workers.UvicornWorker \
    -w "${WEB_CONCURRENCY:-2}" \
    --bind "0.0.0.0:${PORT:-8000}" \
    --timeout "${GUNICORN_TIMEOUT:-600}" \
    --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT:-60}"
  ```

- [ ] AC2: Verificar que `--preload` nao causa erro com o `lifespan` context manager do FastAPI
  - O `lifespan` (main.py:290-368) inicializa Redis, Sentry, ARQ pool, metrics
  - Com `--preload`, lifespan roda no master → workers herdam estado via fork
  - Se lifespan depende de `os.getpid()` ou thread-local state, pode causar issues
  - Testar: deploy com `--preload` e verificar que `/health` retorna dependencies healthy

- [ ] AC3: Adicionar flag `GUNICORN_PRELOAD` ao start.sh para poder desabilitar se necessario:
  ```bash
  PRELOAD_FLAG=""
  if [ "${GUNICORN_PRELOAD:-true}" = "true" ]; then
    PRELOAD_FLAG="--preload"
  fi
  ```
  - Default: `true` (preload habilitado)
  - Documentar em `.env.example`

### Startup Readiness Signal

- [ ] AC4: Adicionar log explicito quando aplicacao esta pronta para receber trafego:
  ```python
  logger.info("APPLICATION READY — all routes registered, accepting traffic")
  ```
  - Deve ser a ULTIMA linha do `lifespan` startup (apos todas as inicializacoes)
  - Util para debugging e para confirmar que preload funcionou

- [ ] AC5: Endpoint `/health` deve incluir campo `ready: true` na resposta:
  ```json
  {
    "status": "healthy",
    "ready": true,
    "uptime_seconds": 123.4,
    ...
  }
  ```
  - `ready` = True somente apos `lifespan` startup completar
  - `uptime_seconds` = tempo desde startup (util para diagnostico de restarts frequentes)
  - Implementar com variavel global `_startup_time: float | None` setada no final do lifespan

### Graceful Shutdown

- [ ] AC6: Verificar que `--graceful-timeout` esta adequado para requests em andamento
  - Atual: 60s (configurado em start.sh)
  - Verificar que requests de busca (que podem levar ate 360s) nao sao cortados
  - Se necessario, aumentar `graceful-timeout` para 120s
  - Documentar decisao: requests longos podem ser interrompidos em deploy, aceitavel?

- [ ] AC7: `SIGTERM` handler deve logar que shutdown esta em andamento:
  ```
  [SHUTDOWN] Received SIGTERM — draining connections (graceful_timeout=60s)
  ```
  - Usar `signal.signal(signal.SIGTERM, handler)` ou confiar no gunicorn default
  - Util para correlacionar "backend offline" com deploy/restart

### Frontend: Respeitar Readiness

- [ ] AC8: Frontend health probe deve verificar campo `ready` do backend:
  ```typescript
  const data = await response.json();
  if (data.ready === false) {
    console.warn("[HealthCheck] Backend is starting up, not yet ready");
    return NextResponse.json({ status: "healthy", backend: "starting" });
  }
  ```
  - Novo estado: `"starting"` (diferente de `"healthy"`, `"unhealthy"`, `"unreachable"`)
  - Nao considerar como falha — backend esta subindo, nao caiu

## Testes Obrigatorios

### Backend (pytest)

```bash
cd backend && python -m pytest tests/test_startup_readiness.py -v --no-header
```

- [ ] T1: `/health` retorna `ready: true` apos startup completo
- [ ] T2: `/health` retorna `uptime_seconds` como float positivo
- [ ] T3: `uptime_seconds` aumenta monotonicamente entre requests
- [ ] T4: Startup log "APPLICATION READY" presente apos lifespan

### Frontend (jest)

```bash
cd frontend && npm test -- --testPathPattern="health" --no-coverage
```

- [ ] T5: Health probe retorna `backend: "starting"` quando backend retorna `ready: false`
- [ ] T6: Health probe retorna `backend: "healthy"` quando backend retorna `ready: true`

### Integracao

- [ ] T7: Deploy com `--preload` habilitado → zero 404 durante startup (verificar manualmente no Railway)

### Pre-existing baselines
- Backend: ~35 fail / ~3924 pass
- Frontend: ~42 fail / ~1912 pass
- Nenhuma regressao permitida

## Definicao de Pronto

- [ ] Todos os ACs implementados e checkboxes marcados
- [ ] 7 testes novos passando
- [ ] Zero regressoes nos baselines
- [ ] Deploy de teste no Railway com `--preload` — verificar logs de startup
- [ ] Zero 404 no health check durante restart do backend
- [ ] Story file atualizado com `[x]` em todos os checkboxes

## Arquivos Afetados

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `backend/start.sh` | Modificar — adicionar `--preload` + `GUNICORN_PRELOAD` flag |
| `backend/main.py` | Modificar — log "APPLICATION READY", `_startup_time`, `ready` + `uptime_seconds` no /health |
| `backend/.env.example` | Modificar — documentar `GUNICORN_PRELOAD` |
| `frontend/app/api/health/route.ts` | Modificar — tratar `ready: false` como "starting" |
| `backend/tests/test_startup_readiness.py` | Criar — testes T1-T4 |
| `frontend/__tests__/api/health.test.ts` | Modificar — adicionar testes T5-T6 |

## Notas Tecnicas

### Riscos e Mitigacoes

| Risco | Mitigacao |
|-------|----------|
| `--preload` incompativel com lifespan async | Testar em staging antes de prod; flag `GUNICORN_PRELOAD` permite reverter |
| `--preload` aumenta memoria do master | ~50-100MB a mais; aceitavel no plano Railway atual |
| `--preload` desabilita auto-reload | Irrelevante em producao (dev usa uvicorn direto) |
| Workers herdam conexoes do master (Redis, Supabase) | Verificar que connection pools recriam apos fork |
| `graceful-timeout` insuficiente para buscas longas | Buscas tem timeout proprio (360s); deploy interrompe — aceitar ou aumentar |

### Investigacao Necessaria Antes de Implementar
- [ ] Verificar se `httpx.AsyncClient` (usado pelo PNCP client) e fork-safe
- [ ] Verificar se `redis.asyncio.ConnectionPool` sobrevive ao fork do gunicorn
- [ ] Verificar se `supabase` client Python e fork-safe
- [ ] Se algum nao for fork-safe: usar `post_fork` hook do gunicorn para reinicializar

### Alternativa Considerada e Descartada
**Health check com readiness probe separado:** Railway nao suporta readiness vs liveness probe separados (apenas `healthcheckPath`). Portanto, `/health` precisa servir ambos os propositos — retornando 200 sempre (liveness) mas com `ready` no body (readiness informacional).

## Dependencias

| Tipo | Story | Motivo |
|------|-------|--------|
| Paralela | CRIT-008 | Frontend resilience complementa esta story |
| Nenhuma bloqueante | — | Pode ser implementada independentemente |
