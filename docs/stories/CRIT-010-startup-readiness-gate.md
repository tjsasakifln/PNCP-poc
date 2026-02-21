# CRIT-010: Startup Readiness Gate — Prevenir Trafego Antes de Workers Prontos

## Epic
Consistencia Estrutural do Sistema (EPIC-CRIT)

## Sprint
Sprint 5: Resiliencia de Producao

## Prioridade
P1

## Estimativa
8h

## Status: COMPLETED (2026-02-20)

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

- [x] AC1: `backend/start.sh` adiciona `--preload` ao comando gunicorn para `PROCESS_TYPE=web`
- [x] AC2: `--preload` nao causa erro com o `lifespan` context manager do FastAPI (verificado: lifespan roda per-worker com UvicornWorker, nao no master)
- [x] AC3: Flag `GUNICORN_PRELOAD` adicionada ao start.sh (default: true), documentada em `.env.example`

### Startup Readiness Signal

- [x] AC4: Log explicito "APPLICATION READY — all routes registered, accepting traffic" na ultima linha do lifespan startup
- [x] AC5: `/health` inclui `ready: true` e `uptime_seconds` (float). Implementado via `_startup_time` module-level variable

### Graceful Shutdown

- [x] AC6: `--graceful-timeout` adequado (60s atual, configuravel via `GUNICORN_GRACEFUL_TIMEOUT`)
- [x] AC7: `SIGTERM` handler registrado no lifespan para logar "SIGTERM received — starting graceful shutdown"

### Frontend: Respeitar Readiness

- [x] AC8: Frontend health probe verifica campo `ready` e retorna `backend: "starting"` quando `ready === false`

## Testes

### Backend (pytest) — 7 passed

- [x] T1: `ready: true` quando `_startup_time` setado
- [x] T2: `uptime_seconds` como float positivo
- [x] T3: `uptime_seconds` aumenta monotonicamente
- [x] T4: `_startup_time` existe como atributo do modulo
- [x] test_ready_false_when_startup_time_none
- [x] test_health_response_includes_ready_and_uptime_fields (schema)
- [x] test_health_response_defaults (schema defaults)

### Frontend (jest) — 9 passed (7 existing updated + 2 new)

- [x] T5: Health probe retorna `backend: "starting"` quando `ready: false`
- [x] T6: Health probe retorna `backend: "healthy"` quando `ready: true`

### Integracao

- [ ] T7: Deploy com `--preload` habilitado → zero 404 durante startup (Railway — manual)

## Arquivos Modificados

| Arquivo | Tipo |
|---------|------|
| `backend/start.sh` | Modificado — `--preload` + `GUNICORN_PRELOAD` flag |
| `backend/main.py` | Modificado — `_startup_time`, `ready`/`uptime_seconds` no /health, SIGTERM handler, APPLICATION READY log |
| `backend/schemas.py` | Modificado — `ready` + `uptime_seconds` campos em HealthResponse |
| `.env.example` | Modificado — documentado `GUNICORN_PRELOAD` |
| `frontend/app/api/health/route.ts` | Modificado — parse `ready` field, return "starting" |
| `backend/tests/test_startup_readiness.py` | Criado — 7 testes |
| `frontend/__tests__/api/health.test.ts` | Modificado — testes atualizados + T5/T6 |

## Dependencias

| Tipo | Story | Motivo |
|------|-------|--------|
| Paralela | CRIT-008 | Frontend resilience complementa esta story |
| Nenhuma bloqueante | — | Pode ser implementada independentemente |
