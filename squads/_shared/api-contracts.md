# API Contracts — Rotas Backend SmartLic

Todos os endpoints expostos ao frontend DEVEM declarar `response_model=` no decorator de rota. Sem isso o schema não entra no OpenAPI e o frontend fica com `{[k: string]: unknown}` mesmo passando no CI.

## Rotas críticas

### Search

| Rota | Response model | Observações |
|---|---|---|
| `POST /buscar` | `BuscaResponse` | Retorna 202 em <2s com `search_id`. Resultados via SSE + polling. |
| `GET /buscar-progress/{search_id}` | **SSE stream** | Eventos: `progress`, `partial_results`, `llm_ready`, `excel_ready`, `complete`, `error`. bodyTimeout=0 + heartbeat=15s. |
| `GET /v1/search/{search_id}/status` | `SearchStatus` | Polling fallback (quando SSE falha) |
| `POST /v1/search/{search_id}/retry` | `BuscaResponse` | Retry de busca com erro recuperável |

### Produto

| Rota | Response model |
|---|---|
| `GET /setores` | `List[Setor]` — 15 setores com id/name/description |
| `GET /plans` | `List[Plan]` |
| `POST /checkout` | `CheckoutSession` (Stripe) |
| `GET /subscription/status` | `SubscriptionStatus` |
| `GET /me` | `UserProfile` |
| `GET /trial-status` | `TrialStatus` |
| `POST /first-analysis` | `FirstAnalysisResult` |
| `GET/POST/PATCH/DELETE /pipeline` | `PipelineItem[]` |
| `GET/POST/PATCH /conversations` | `Conversation` |

### Admin

| Rota | Response model | Auth |
|---|---|---|
| `GET /v1/admin/cron-status` | `CronHealthReport` | `is_admin` |
| `GET /admin/feedback/patterns` | `FeedbackPatterns` | `is_admin` |
| `GET /admin/search-trace/{search_id}` | `SearchTrace` | `is_admin` |

## Timeout Waterfall (STORY-4.4 TD-SYS-003)

**Invariante:** `pipeline(100) > consolidation(90) > per_source(70) > per_uf(25) > (per_modality 20 + httpx 15)`.

```
Railway proxy     [========================== 120s ==========================]
Gunicorn worker   [======================= 110s ========================]
Pipeline budget   [==================== 100s ====================]
  Consolidation   [================== 90s ===================]
    PerSource     [============= 70s =============]
      PerUF       [===== 25s =====]
```

Enforced por `backend/tests/test_timeout_invariants.py`. Pipeline call sites usam `backend/pipeline/budget.py::_run_with_budget` — cada TimeoutError incrementa `smartlic_pipeline_budget_exceeded_total{phase,source}`.

Override via env vars (emergência): `PIPELINE_TIMEOUT`, `CONSOLIDATION_TIMEOUT`, `PNCP_TIMEOUT_PER_SOURCE`.

## SSE contract

- Cliente: `new EventSource('/buscar-progress/{search_id}')` no frontend
- Eventos bem-definidos (ver tabela Search acima)
- Fallback gracioso: se SSE falha, frontend usa polling + simulação por tempo
- Keep-alive: 15s heartbeat backend > 60s Railway proxy idle > 120s SSE inactivity
- jsdom (tests) precisa de polyfill `EventSource` em `jest.setup.js`

## Regeneração de types

```bash
# Terminal 1: backend rodando
cd backend && uvicorn main:app --port 8000

# Terminal 2: regenerar e commitar
npm --prefix frontend run generate:api-types
git add frontend/app/api-types.generated.ts
```

- Fonte: `frontend/app/api-types.generated.ts` (auto-gerado via `openapi-typescript`)
- Re-export UI-friendly: `frontend/app/types.ts` (`BuscaResult`, `LicitacaoItem`, `Resumo`)
- CI gate: `.github/workflows/api-types-check.yml` extrai OpenAPI direto do FastAPI (sem backend rodando) e falha PR se o committed drifta

## Quando atualizar

- Nova rota pública → adicionar linha + `response_model=`
- Mudança de shape → regenerar types (comando acima) + atualizar `api-contracts.md`
- Nova policy de timeout → atualizar a tabela waterfall acima + `invariants.md`
