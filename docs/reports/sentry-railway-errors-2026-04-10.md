# Erros Vivos em Produção — Sentry + Railway

**Data:** 2026-04-10 (snapshot 13:00 BRT / 16:00 UTC)
**Fontes:** Sentry `confenge` (14 dias) + Railway `bidiq-backend` (janela efetiva ~30 min)
**Total:** 69 issues ativos no Sentry + 500 eventos ERROR em Railway na última meia hora

---

## ⚠️ Resumo Executivo

Estado **crítico** com múltiplas causas-raiz concorrentes:

1. **Schema drift ativo** (`search_sessions.objeto_resumo does not exist`) — 213 eventos Sentry, **Escalating**, último há 5 min. Disparado pelo endpoint `GET /v1/analytics/trial-value`. **Migration não aplicada ou código referenciando coluna removida.**
2. **Incidente Supabase recorrente** — circuit breaker abriu várias vezes, timeouts, `PGRST002 schema cache`, `ConnectionTerminated`, startup gate falhando. 276 eventos de Health → `degraded`.
3. **Timeouts em endpoint B2G** (`/v1/empresa/{cnpj}/perfil-b2g`) — `httpx.ReadTimeout` na chamada BrasilAPI; 42 eventos Sentry + rajada ativa no Railway agora.
4. **Bug de crash loop no backend** (`TypeError: func() missing 1 required positional argument: 'coroutine'`) — 44 eventos, **Escalating**, há 15h. Causou `Application startup failed. Exiting.` (também com 44 eventos **Regressed**).
5. **Trigger SQL quebrado** (`record "new" has no field "is_master"`) — bloqueia reconciliação Stripe e atribuição de plano admin.
6. **Crash no frontend Next.js** — conflito de slug `[setor]` vs `[cnpj]` (já corrigido no commit `40bf4968` mas ainda gerando 10 eventos) + `InvariantError: Expected RSC response, got text/plain` no /login (6 eventos).
7. **Trial email pipeline quebrado** — múltiplos dias (#4, #7, #10) falhando por circuit breaker e PGRST002.

> **Ressalva importante sobre Railway:** a API do Railway CLI retorna apenas ~500 logs por query e a janela efetiva com retorno hoje foi **apenas ~30 min** (15:32–16:02 UTC). Janelas anteriores (`--since 3h`, `--since 24h`, `--since 2d` etc.) retornaram **0 logs** — ou retenção efetiva é muito curta, ou esses 500 eventos em 30 min representam burst de incidente ativo que esgotou o cap. **Sentry é a fonte autoritativa de histórico.**

---

## 🔥 Sentry — Top Issues (ordenado por frequência, 14 dias)

### Backend — Issues ativos/escalando

| # | Status | Events | Last Seen | Título | Componente |
|---|--------|-------:|-----------|--------|------------|
| 1 | Ongoing | **276** | 37 min | Health incident: System status changed to degraded. Affected: pncp | `health` middleware |
| 2 | **Escalating** | **213** | **5 min** | `column search_sessions.objeto_resumo does not exist` (code 42703) | `routes.analytics.get_trial_value` |
| 3 | **Escalating** | **44** | 15 h | `TypeError: func() missing 1 required positional argument: 'coroutine'` | ASGI middleware (**Unhandled**) |
| 4 | Regressed | 44 | 15 h | `Application startup failed. Exiting.` | uvicorn startup |
| 5 | Regressed | 44 | 15 h | `Traceback (most recent call last):` (sibling do #4) | uvicorn startup |
| 6 | **Escalating** | 42 | 18 min | `GET /v1/empresa/03935826000130/perfil-b2g → ERROR (15034ms) ReadTimeout` | `routes.empresa_publica.perfil_b2g` |
| 7 | New | 25 | 3 h | `orgao_stats DB query failed for 14105209000124 — canceling statement due to statement timeout` (57014) | `routes.orgao_publico.orgao_stats` |
| 8 | — | 24 | 2 h | `Failed to update session … Supabase circuit breaker is OPEN — sb_execute rejected` | `routes.search.buscar_licitacoes` |
| 9 | — | 19 | — | `Error listing pipeline for user … circuit breaker is OPEN` | `routes.pipeline.list_pipeline_items` |
| 10 | — | 19 | 4 h | `Failed to process trial email #4 day=10 — circuit breaker is OPEN` | `services.trial_email_sequence` |
| 11 | — | 6 | 10 h | `APIError: record "new" has no field "is_master"` | `services.stripe_reconciliation` |
| 12 | Warning | 6 | 2 h | `Slow sync search: 110.4s` | `routes.search.buscar_licitacoes` |
| 13 | Warning | 3 | 4 h | `slow_request: GET /v1/empresa/44404731000178/perfil-b2g (120.7s)` | `routes.empresa_publica` |
| 14 | — | 3 | — | `Failed to update session … numeric field overflow (22003)` precision 14 scale 2 | `routes.search.buscar_licitacoes` |
| 15 | — | 2 | 4 h | `Failed to process trial email #10 day=2: read operation timed out` | `trial_email_sequence` |
| 16 | — | 2 | 4 h | `orgao_contratos DB query failed for 13908702000110 — statement timeout` | `routes.contratos_publicos` |
| 17 | — | 2 | 4 h | `Failed to process trial email #7 day=1 — PGRST002 schema cache` | `trial_email_sequence` |
| 18 | — | 2 | 4 h | `APIError: canceling statement due to statement timeout` | `jobs.cron.cache_ops` |
| 19 | **Fatal** | 2 | 4 h | `SCHEMA CONTRACT VIOLATED: missing ['search_sessions.id', 'search_sessions.user_id', ...]` | startup gate |
| 20 | — | 2 | 2 h | `Error fetching active subscription … <ConnectionTerminated error_code:1>` | `routes.user.get_trial_status` |
| 21 | — | 2 | — | `Error listing pipeline … <ConnectionTerminated error_code:9>` | `routes.pipeline` |

### Backend — Issues com 1 evento (últimas 24h)

- **Health incident: unhealthy (Affected: unknown)** — 9h atrás
- **slow_request: POST /v1/buscar (110.5s)** — 2h, New
- **Error fetching monthly quota** `<ConnectionTerminated error_code:1>` — 2h, New
- **CRIT-004: Tables `profiles` / `search_results_cache` / `search_sessions` check failed — read operation timed out** (3 issues separadas) — 4h, New. Repetiu 4h atrás com `PGRST002 schema cache` também.
- **ConnectTimeout** no perfil-b2g — 4h, New
- **Fatal: STARTUP GATE: Supabase unreachable — read operation timed out** — 4h
- **Fatal: STARTUP GATE: Supabase unreachable — PGRST002** — 4h
- **APIError: Could not query the database for the schema cache. Retrying.** (várias instâncias) — 4h
- **CRIT-004** (triplas repetidas com `PGRST002`) — 4h
- **Health incident: unhealthy (Affected: pncp)** — 16h
- **Failed to assign plan `smartlic_pro` to user a18e0a77: `record "new" has no field "is_master"`** — 19h
- **InvalidRequestError: payment method type `pix` is invalid** (Stripe) + **Unhandled Stripe error on /v1/checkout** — 2d atrás
- **POST /v1/checkout → ERROR InvalidRequestError (pix)** — 2d
- **RemoteProtocolError: Server disconnected** — 3 instâncias 2d atrás, 1 instância 6d
- **APIError: `new row … violates check constraint "chk_search_sessions_error_code"`**
- **Error fetching monthly quota … `JSON could not be generated` (400 Bad Request)**
- **Error creating pipeline item … `new row violates row-level security policy for table "pipeline_items"` (42501)**
- **Error fetching top dimensions: `1 validation error for DimensionItem`** (Pydantic)
- **BadRequestError (OpenAI) — invalid JSON body**
- **Circuit breaker OPEN** em `sessions`, `time series`, `new opportunities`, `analytics summary`, `top dimensions` (todos `a18e0a77`)

### Frontend

| # | Status | Events | Last Seen | Título |
|---|--------|-------:|-----------|--------|
| 1 | New | 34 | 5 d | `Error: Connection closed.` |
| 2 | — | 10 | 37 min | `Error: You cannot use different slug names for the same dynamic path ('setor' !== 'cnpj')` |
| 3 | — | 6 | 2 d | `InvariantError: Expected RSC response, got text/plain. This is a bug in Next.js.` (/login/page) |
| 4 | — | 2 | 2 h | `TypeError: Cannot read properties of undefined (reading 'total_oportunidades')` |
| 5 | New | 1 | 5 d | `Error: Connection closed.` (×2, instâncias separadas) |

> **Nota:** Issue #2 (slug `setor`/`cnpj`) foi corrigida pelo commit `40bf4968` mas ainda aparece como não resolvida — precisa ser **marcada como resolved** no Sentry.

---

## 📊 Agrupamento por Causa Raiz

| Causa raiz | Issues Sentry | Eventos | Severidade | Ação |
|------------|---------------|--------:|------------|------|
| **A. Schema drift — `search_sessions.objeto_resumo`** | 1 (escalating) + 1 Fatal (SCHEMA CONTRACT) | 215 | 🔴 Crítico | Aplicar migration ou hotfix no código |
| **B. Supabase instável (circuit breaker, PGRST002, timeouts, ConnectionTerminated)** | ~15 issues | ~100 | 🔴 Crítico | Investigar pool/conexão + incidente Supabase |
| **C. PNCP/BrasilAPI timeouts (perfil-b2g, orgao_stats)** | 5 issues | ~70 | 🟠 Alto | Adicionar timeout agressivo + circuit breaker por fonte |
| **D. Crash middleware (`TypeError: coroutine missing`)** | 2 issues | 88 | 🔴 Crítico | Causou `Application startup failed` — regressão de código |
| **E. Trigger SQL `is_master` quebrado** | 2 issues | 7 | 🟠 Alto | Corrigir trigger em `profiles` |
| **F. Trial email pipeline** | 3 issues | 23 | 🟡 Médio | Consequência de B — espera Supabase estabilizar |
| **G. Frontend slug conflict (já corrigido)** | 1 issue | 10 | 🟢 Baixo | Marcar como resolved |
| **H. Frontend `Error: Connection closed`** | 3 issues | 36 | 🟡 Médio | Investigar SSE/fetch aborts |
| **I. Stripe PIX invalid** | 2 issues | 2 | 🟡 Médio | Ativar PIX no dashboard Stripe ou remover do checkout |
| **J. Numeric overflow (valor precision 14,2)** | 1 issue | 3 | 🟡 Médio | Alargar coluna ou normalizar input |
| **K. Warnings de slow_request (>110s)** | 2 issues | 9 | 🟠 Alto | Aproximando-se do timeout Railway de 120s |

---

## 🚂 Railway — Análise da Janela Ativa (15:32–16:02 UTC, 10-Apr)

**500 eventos ERROR** em ~30 minutos (cap do CLI atingido).

**Após remover stack frames (preservando só mensagens de negócio):** 44 mensagens úteis, dominadas por:

| Ocorrências | Mensagem | Logger |
|------------:|----------|--------|
| 14 | `Error fetching trial value for <uid>: column search_sessions.objeto_resumo does not exist` (42703) | `routes.analytics` |
| 4 | `httpx.ReadTimeout` na stack `_build_perfil → _fetch_brasilapi → client.get` | `routes.empresa_publica` |
| 2 | `Unhandled error on /v1/empresa/<cnpj>/perfil-b2g` | `startup.exception_handlers` |
| 2 | `ERROR: Exception in ASGI application` | starlette |

**Dois usuários afetados** pelo schema drift nas últimas 30 min: `39b32b6f-***` e `285edd6e-***`.

---

## ✅ Ações Recomendadas (ordem de prioridade)

1. **[P0] Schema drift `objeto_resumo`** — Verificar se existe migration pendente em `supabase/migrations/`. Se a coluna foi removida, aplicar hotfix em `routes/analytics.py → get_trial_value` (ou onde a query é montada). 213 eventos e ativamente escalando.
2. **[P0] `TypeError: coroutine missing`** — Regressão crítica (44 eventos, causou crash loop de startup). Investigar último deploy de middleware ASGI.
3. **[P0] Health incident `pncp degraded`** — 276 eventos. Verificar se PNCP API está retornando 5xx ou se é consequência do cascade Supabase.
4. **[P1] CRIT-004 startup gate + Schema contract violated** — Validar que todas as migrations do schema crítico foram aplicadas (`supabase db push --include-all`). Coordenar com CI workflow `migration-check.yml`.
5. **[P1] Trigger `is_master`** — Grep por trigger/function que referencia `NEW.is_master` em `supabase/migrations/`. Provavelmente migration recente do `profiles` renomeou/removeu a coluna.
6. **[P1] `perfil-b2g` ReadTimeout** — Reduzir timeout de BrasilAPI (atualmente 15s). Adicionar circuit breaker por host. Slow requests já estão batendo 120s (limite Railway).
7. **[P2] Stripe PIX** — Decidir: ativar PIX no dashboard OU remover da UI `/checkout`.
8. **[P2] Frontend slug (já corrigido)** — Marcar issue `SMARTLIC-FRONTEND-A` como resolved no Sentry.
9. **[P2] Numeric overflow (14,2)** — Alargar coluna `valor_estimado` ou clamp no input (12 dígitos permite até R$ 9.999.999.999,99).
10. **[P3] Frontend `Connection closed`** (36 eventos, 5 dias) — Provável aborto de fetch SSE; validar tratamento em `/buscar`.

---

## 🔗 Links Diretos Sentry (principais issues)

| Issue | URL |
|-------|-----|
| Schema drift `objeto_resumo` | https://confenge.sentry.io/issues/7396988861/ |
| TypeError coroutine missing | https://confenge.sentry.io/issues/7400217484/ |
| Application startup failed | https://confenge.sentry.io/issues/7282829485/ |
| Health degraded pncp | https://confenge.sentry.io/issues/7355911985/ |
| perfil-b2g ReadTimeout (03935826) | https://confenge.sentry.io/issues/7398756337/ |
| SCHEMA CONTRACT VIOLATED (Fatal) | https://confenge.sentry.io/issues/7401448164/ |
| Circuit breaker pipeline | https://confenge.sentry.io/issues/7362741373/ |
| `is_master` Stripe reconciliation | https://confenge.sentry.io/issues/7388075442/ |
| Frontend slug conflict (resolvido no código) | https://confenge.sentry.io/issues/7401546943/ |
| Frontend InvariantError /login | https://confenge.sentry.io/issues/7397346898/ |

---

## Arquivos Gerados

- `railway-errors-consolidated.json` — 1000 raw logs (500 + 500, com sobreposição temporal)
- `railway-errors-10d.json` — vazio (janela > 30 min retorna 0)
- `.playwright-mcp/sentry-backend-issues.yml` — snapshot acessibilidade página 1 Sentry
