# STORY-TD-004: Remove Legacy Routes

**Epic:** Resolucao de Debito Tecnico
**Tier:** 1
**Area:** Backend
**Estimativa:** 4-8h (3-6h codigo + 1-2h testes)
**Prioridade:** P1
**Debt IDs:** TD-A01

## Objetivo

Remover a duplicacao de rotas montadas 2x no `main.py`: uma vez no root (`/`) e outra com prefixo `/v1/`. Atualmente existem 61 `include_router` calls gerando 120+ endpoints, onde metade sao legados sem versionamento. Manter apenas o prefixo `/v1/` para todas as rotas, eliminando ambiguidade e reduzindo superficie de ataque.

**Impacto:** 61 include_router calls -> ~30 (metade). 120+ endpoints -> ~60 endpoints canônicos.

## Acceptance Criteria

### Pre-requisito: Analise de Uso
- [ ] AC1: Verificar Railway access logs dos ultimos 30 dias para chamadas em rotas SEM prefixo `/v1/` (ex: `GET /health`, `POST /buscar` vs `POST /v1/buscar`)
- [ ] AC2: Documentar quais rotas legacy tem trafego real (se alguma, criar redirect temporario)
- [ ] AC3: Verificar frontend `app/api/` proxy routes — garantir que todas apontam para `/v1/` endpoints

### Implementacao
- [ ] AC4: Adicionar deprecation counter metric (`smartlic_legacy_route_calls_total`) ANTES de remover — deploy, aguardar 48h, verificar contagem
- [ ] AC5: Remover todos `include_router()` calls sem prefixo `/v1/` do `main.py`
- [ ] AC6: Manter APENAS os `include_router()` calls com `prefix="/v1/"` (ou equivalente)
- [ ] AC7: Endpoint `/health` (sem prefixo) continua funcionando — Railway healthcheck depende dele
- [ ] AC8: Endpoint `/docs` e `/redoc` continuam funcionando (OpenAPI spec)
- [ ] AC9: Atualizar `frontend/app/api/` proxy routes se alguma ainda aponta para rota sem `/v1/`

### Validacao
- [ ] AC10: `GET /buscar` retorna 404 (somente `POST /v1/buscar` existe)
- [ ] AC11: OpenAPI spec (`/docs`) mostra ~60 endpoints (metade do atual)
- [ ] AC12: Todos 5774+ backend tests passam (atualizar paths nos testes se necessario)
- [ ] AC13: Todos 2681+ frontend tests passam
- [ ] AC14: E2E smoke test em producao confirma busca funcionando

## Technical Notes

**Estrutura atual em main.py (simplificada):**
```python
# Legacy (root) — REMOVER
app.include_router(search_router)           # POST /buscar
app.include_router(pipeline_router)         # GET /pipeline

# Versioned — MANTER
app.include_router(search_router, prefix="/v1")    # POST /v1/buscar
app.include_router(pipeline_router, prefix="/v1")  # GET /v1/pipeline
```

**Excecoes a manter no root:**
- `GET /health` — Railway healthcheck (confirmar com Railway config)
- `GET /docs`, `GET /redoc` — OpenAPI UI (FastAPI default)
- Webhook endpoints (`POST /webhooks/stripe`) — Stripe callback URL ja configurado

**Deprecation metric pattern:**
```python
from prometheus_client import Counter

legacy_route_calls = Counter(
    'smartlic_legacy_route_calls_total',
    'Calls to legacy (non-/v1/) routes',
    ['method', 'path']
)

@app.middleware("http")
async def track_legacy_routes(request, call_next):
    if not request.url.path.startswith("/v1/") and request.url.path not in ALLOWED_ROOT_PATHS:
        legacy_route_calls.labels(method=request.method, path=request.url.path).inc()
    return await call_next(request)
```

**Frontend proxy audit:** Grep `BACKEND_URL` in `frontend/app/api/` to find all backend calls. Each must use `/v1/` prefix.

## Dependencies

- Nenhuma dependencia de database stories
- TD-003 pode rodar em paralelo
- Prerequisito para TD-M02 (API contract CI) em Tier 2

## Definition of Done
- [ ] Deprecation metric deployed e verificado (48h sem trafego legacy, ou redirects criados)
- [ ] Legacy route mounts removidos do main.py
- [ ] /health, /docs, /redoc continuam funcionando
- [ ] All frontend proxy routes use /v1/ prefix
- [ ] All backend tests passing (paths updated)
- [ ] All frontend tests passing
- [ ] E2E smoke test passes
- [ ] Reviewed by @architect
