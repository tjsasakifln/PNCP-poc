# DIAGNÓSTICO GTM — Fluxo Crítico de Busca (Ponta a Ponta)

**Data:** 2026-02-20
**Escopo:** Investigação completa do fluxo de busca, desde o clique do usuário até a resposta final
**Critério de classificação:** "Isso pode deixar o usuário sem resultado ou sem explicação?"
**Objetivo:** Base para PM derivar stories de alto impacto para GTM mínimo viável

---

## P0 CRÍTICO — FRONTEND DOWN EM PRODUÇÃO (Evidência Coletada 2026-02-21 02:02 UTC)

**O domínio `smartlic.tech` NÃO está alcançando nenhuma aplicação.**

### Evidência Real (probes executados):

```
$ curl -sS https://smartlic.tech/
{"status":"error","code":404,"message":"Application not found","request_id":"45dTJ6xqQoexN7qeBhdwDg"}

$ curl -sS https://bidiq-frontend-production.up.railway.app/
{"status":"error","code":404,"message":"Application not found","request_id":"pwZ7rZuJRcW-Pw1mBhdwDg"}
```

**Headers reveladores:**
```
Server: railway-edge
X-Railway-Fallback: true    ← Railway não encontrou app para rotear
X-Railway-Edge: railway/us-east4-eqdc4a
```

**Backend FUNCIONA normalmente:**
```
$ curl -sS https://bidiq-uniformes-production.up.railway.app/health
{"status":"healthy","ready":true,"uptime_seconds":2872.262,...}
```

**Domínios configurados no Railway (via `railway domain`):**
```
- https://smartlic.tech           ← bound to bidiq-frontend (DOWN)
- https://app.smartlic.tech       ← bound to bidiq-frontend (DOWN)
- https://bidiq-frontend-production.up.railway.app  ← Railway internal (DOWN)
```

**DNS resolve para Cloudflare (proxy):**
```
smartlic.tech → 104.21.78.33, 172.67.215.98 (Cloudflare IPs)
```

**www.smartlic.tech → SSL error (certificado não configurado)**

### Diagnóstico

O serviço `bidiq-frontend` no Railway está **parado, crashado, ou sem deploy válido**. O Railway retorna sua página padrão "Application not found" com `X-Railway-Fallback: true`. Isso significa:
1. O container do frontend não está rodando
2. OU o container está rodando mas não respondeu ao health check e foi marcado como unhealthy
3. OU não existe deploy ativo para o serviço

**O backend está operacional** — `bidiq-uniformes-production.up.railway.app/health` retorna 200 com `ready: true`.

**Impacto:** 100% dos usuários veem "Application not found" ao acessar smartlic.tech. O sistema está completamente inacessível. Nenhuma outra análise é relevante até que o frontend esteja rodando.

**Ação imediata necessária:** Verificar no dashboard do Railway o status do serviço `bidiq-frontend`, logs do último deploy, e fazer redeploy se necessário.

---

## A NARRATIVA: O QUE ACONTECE QUANDO O USUÁRIO CLICA EM "BUSCAR"

### Camada 1 — Frontend (page.tsx → useSearch.ts)

O usuário seleciona setor, UFs e período, e clica "Buscar". Antes de qualquer requisição, o frontend precisa carregar a **lista de setores** para popular o formulário.

**Carregamento de Setores — 3 fallbacks em cascata:**

1. Cache localStorage (TTL 5min) → usa direto
2. `GET /api/setores` → API proxy → `GET {BACKEND_URL}/setores`
3. Cache localStorage expirado → banner azul "Usando setores em cache"
4. `SETORES_FALLBACK` hardcoded → banner amarelo "Usando lista offline de setores"

**Evidência:** `useSearchFilters.ts:380-435` — Se o backend estiver indisponível no momento do carregamento inicial da página, o usuário verá o banner amarelo. A lista hardcoded (`SETORES_FALLBACK` em `page.tsx:64-80`) pode estar desatualizada — depende de sync manual via `scripts/sync-setores-fallback.js`.

Ao clicar "Buscar", o frontend:
1. Gera `search_id` via `crypto.randomUUID()` (`useSearch.ts:389`)
2. Abre conexão SSE em `GET /api/buscar-progress?search_id={id}` para receber progresso
3. Envia `POST /api/buscar` com payload (setor, UFs, datas, search_id)

---

### Camada 2 — API Proxy (frontend/app/api/buscar/route.ts)

O Next.js proxy intercepta e:
1. **Valida autenticação** — refresh do token Supabase server-side (`route.ts:10-21`)
2. **Verifica `BACKEND_URL`** — se ausente, retorna 503 imediato (`route.ts:57-65`)
3. **Encaminha ao backend** — adiciona headers `Authorization`, `X-Request-ID`, `X-Correlation-ID`
4. **Retry em 503** — max 2 tentativas com delays [0ms, 3s] (`route.ts:79-153`)
5. **Timeout de 8 minutos** — AbortController cancela após 480s (`route.ts:97`)

**Ponto de falha #1:** Se `BACKEND_URL` estiver errado (typo, env var desatualizada), TODAS as buscas falham com 503. Não existe validação de BACKEND_URL no startup do frontend — só falha na primeira requisição real.

**Ponto de falha #2:** O proxy só faz retry em HTTP 503. HTTP 502 (backend caiu) NÃO é retentado pelo proxy. O comentário na linha 81 diz: "502 means backend already retried PNCP internally" — mas 502 também pode significar que o Railway ainda não roteou para uma instância saudável.

---

### Camada 3 — Backend Entry Point (routes/search.py → search_pipeline.py)

A requisição chega em `POST /v1/buscar` (`routes/search.py`):
1. **Validação JWT** — decodifica token localmente (`auth.py:125-152`)
2. **Checagem de quota** — `check_and_increment_quota_atomic()` (`quota.py:465`)
3. **Inicialização do pipeline** — `SearchPipeline.__init__()` prepara contexto
4. **Registro da sessão** — insere em `search_sessions` com search_id

**Ponto de falha #3 — Auth JWT:** Se SUPABASE_JWT_SECRET e JWKS endpoint ambos falharem, auth retorna HTTP 500 (não 401). O frontend trata 401 (redireciona para login), mas 500 vira "Erro no backend" genérico.

**Evidência:** `auth.py:150-152`:
```python
logger.error("SUPABASE_JWT_SECRET not configured and no JWKS URL available!")
raise HTTPException(status_code=500, detail="Auth not configured")
```

**Ponto de falha #4 — Quota Supabase:** Se Supabase estiver lento, quota retry tem apenas 0.3s de window antes de cair para fallback hardcoded. Se a segunda tentativa também falhar, usa `PLAN_CAPABILITIES[plan_type]` hardcoded — que pode ser desatualizado.

**Ponto de falha #5 — Sessão DB:** Se `search_sessions` não tiver a coluna `search_id` (CRIT-011), o INSERT faz fallback para campos mínimos. A correlação entre SSE e resultado fica quebrada.

**Evidência:** `search_state_manager.py:368-403` — try/catch detecta erro PostgreSQL 42703 (column not found) e faz fallback silencioso.

---

### Camada 4 — Pipeline de Busca (search_pipeline.py → fontes de dados)

O pipeline tem 7 estágios:
1. Cache check (L1 InMemory → L2 Supabase)
2. Fetch multi-source (PNCP + PCP v2 + ComprasGov) em paralelo
3. Consolidação + dedup
4. Filtragem por keywords (density scoring)
5. LLM zero-match classification (GPT-4.1-nano)
6. Viability assessment (4 fatores)
7. Ranking + response

**Ponto de falha #6 — PNCP API:** Max `tamanhoPagina=50` (>50 retorna HTTP 400 silencioso). O health canary usa `tamanhoPagina=10`, então NÃO detecta esse limite. Se algum código futuro usar >50, as requisições falham silenciosamente.

**Ponto de falha #7 — Circuit Breaker efêmero:** O estado do circuit breaker é armazenado em memória do processo. Quando Railway reinicia o container, o estado reseta para 0 failures. Se o PNCP estava degradado, o backend imediatamente bombardeia a API novamente → cascading failure.

**Evidência:** `pncp_client.py:153-196` — `self.consecutive_failures: int = 0` em memória local.

**Ponto de falha #8 — Cache columns missing:** Se migration 027b não foi aplicada em produção, as colunas `sources_json` e `fetched_at` não existem em `search_results_cache`. O cache funciona parcialmente — lê/escreve os campos core, mas metadados ficam NULL. A migration 033 é recovery idempotente, mas precisa ser aplicada.

**Evidência:** `search_cache.py:238-246` — usa `.get()` com defaults para campos opcionais, loga WARNING se campos faltam.

---

### Camada 5 — Retorno ao Usuário

Se o pipeline completar com sucesso:
- Backend retorna JSON com licitações, resumo, download_url
- Proxy strip `excel_base64`, adiciona `download_id`
- Frontend recebe via `useSearch.ts`, popula estado, mostra resultados

Se o pipeline falhar:
- Backend constrói erro estruturado via `_build_error_detail()` (`routes/search.py:62-80`)
- Inclui: `error_code`, `search_id`, `correlation_id`, `timestamp`
- Proxy preserva metadata e encaminha ao frontend
- `useSearch.ts` mapeia `error_code` → mensagem PT-BR via `ERROR_CODE_MESSAGES`

**Ponto de falha #9 — Erro genérico "Erro no backend":** Quando o backend retorna erro sem campo `error_code` estruturado (ex: exceção não capturada), o proxy cai no fallback `route.ts:165`: `detail: "Erro no backend"`. O usuário não recebe informação útil. Não sabe se deve tentar de novo, esperar, ou mudar os parâmetros.

**Ponto de falha #10 — Component crash = tela branca:** Não existem React Error Boundaries no `buscar/page.tsx` nem no `SearchResults.tsx`. Se qualquer componente filho lançar exceção durante render (ex: dado inesperado do backend), a página inteira vira tela branca sem explicação.

**Evidência:** Grep por "ErrorBoundary" em `frontend/app/buscar/` retorna 0 resultados.

---

### Camada 6 — Infraestrutura (Railway, Health Checks, Deploys)

**Ponto de falha #11 — Health check mata container prematuramente:**

O Railway usa `/health` com timeout de 120s (`backend/railway.toml:16-17`). Mas o endpoint `/health` (`main.py:556-711`) executa **11 checks** incluindo:
- Supabase connectivity + RPC schema validation
- Redis ping + memory info
- 6 source health checks em paralelo (10s timeout cada)
- Circuit breaker state
- Rate limiter stats
- ARQ job queue health

Se Supabase estiver lento (>120s para responder), Railway mata o container. Isso causa restart → durante restart, requisições recebem 404 → frontend mostra "Erro no backend".

**Evidência:** `backend/railway.toml`:
```toml
healthcheckPath = "/health"
healthcheckTimeout = 120
```

**Ponto de falha #12 — Startup declara "ready" antes de confirmar dependências:**

`_startup_time` é setado em `main.py:354-357` ANTES de verificar que Redis, Supabase e ARQ estão funcionais. O health check retorna `ready: true` baseado em `_startup_time is not None`, mas as dependências podem ainda estar inicializando.

**Evidência:** `main.py:307-365` — lifespan manager seta `_startup_time` no final, mas `_check_cache_schema()` e `recover_stale_searches()` podem ter falhado silenciosamente antes.

**Ponto de falha #13 — Frontend health sempre retorna 200:**

`frontend/app/api/health/route.ts:18-25` SEMPRE retorna HTTP 200, mesmo quando:
- Backend está unreachable
- Backend está starting (ready: false)
- BACKEND_URL não está configurado

Railway vê 200 e assume frontend healthy. Mas o backend pode estar em estado inconsistente. Usuários acessam o frontend normalmente e só descobrem o problema ao tentar buscar.

---

### Camada 7 — Observabilidade (ou a falta dela)

**Ponto de falha #14 — Não é possível reconstruir uma falha a partir do erro visto pelo usuário:**

Quando o usuário vê "Erro no backend", o suporte precisa:
1. Obter o `search_id` do estado do frontend (se o componente não crashou)
2. Buscar nos logs do Railway por `search={search_id}`
3. Railway retém logs por apenas 7 dias
4. Não há serviço de log aggregation configurado (no Datadog, no Logtail)

Se o usuário reportar o erro depois de 7 dias, a evidência desapareceu.

**Ponto de falha #15 — Frontend errors não chegam ao Sentry:**

Sentry está configurado (`sentry.client.config.ts`) MAS:
- Depende de `NEXT_PUBLIC_SENTRY_DSN` estar setado
- Sampling rate é 10% — 90% dos erros não são capturados
- Não há `Sentry.captureException()` explícito nos caminhos de erro de busca
- Erros vão apenas para `console.warn` / `console.error`

**Evidência:** `useSearch.ts:376` — `console.warn([buscar] Client retry...)` — não há envio para Sentry.

**Ponto de falha #16 — RPC `get_table_columns_simple` não existe:**

O health check de startup (`main.py:204`) chama uma RPC function que NÃO EXISTE em nenhuma migration:
```python
result = db.rpc("get_table_columns_simple", {"p_table_name": "search_results_cache"}).execute()
```
Resultado: o check é SEMPRE silently skipped. A validação de schema nunca roda em produção. O sistema declara "healthy" mesmo com schema divergente.

**Evidência:** Grep por `get_table_columns_simple` em `supabase/migrations/` e `backend/migrations/` retorna 0 resultados.

---

## CLASSIFICAÇÃO PARETO: IMPACTO NO USUÁRIO

### ENTRA NO GTM — "Pode deixar o usuário sem resultado ou sem explicação"

| # | Problema | O que o usuário vê | Frequência | Evidência |
|---|---------|---------------------|------------|-----------|
| **P0** | **FRONTEND DOWN — serviço não está rodando no Railway** | **"Application not found" (404 do Railway, não da app)** | **AGORA — 100% dos acessos** | `curl smartlic.tech → 404, X-Railway-Fallback: true` |
| **P1** | Health check heavy mata container → 404 durante deploy | "Erro no backend" por 1-2 min durante cada deploy | A cada deploy | `railway.toml:16-17`, `main.py:556-711` |
| **P2** | Frontend health sempre 200 → backend down mascarado | Página carrega normal, busca falha sem aviso prévio | Sempre que backend reinicia | `health/route.ts:18-25` |
| **P3** | Startup declara "ready" antes das deps | Busca falha com erros aleatórios nos primeiros segundos pós-deploy | A cada deploy | `main.py:354-357` |
| **P4** | Nenhum Error Boundary no buscar | **Tela branca total** se qualquer componente crashar | Raro mas catastrófico | Ausência em `buscar/page.tsx` |
| **P5** | Auth retorna 500 em vez de 401 quando JWT config quebra | "Erro no backend" genérico, sem redirect para login | Se Supabase JWKS unavailable | `auth.py:150-152` |
| **P6** | "Erro no backend" genérico sem info útil | Usuário não sabe se deve tentar de novo ou esperar | Qualquer erro não-estruturado | `route.ts:165` |
| **P7** | Schema DB divergente → RPC functions crash endpoints | Analytics (trial-value) e Mensagens retornam 500 | Se migration 019 não aplicada | `analytics.py:74`, `messages.py:98` |
| **P8** | RPC `get_table_columns_simple` não existe → health check mudo | Sistema declara "healthy" com schema quebrado | **Permanente** — função nunca foi criada | `main.py:204`, 0 migrations |
| **P9** | Circuit breaker reseta no restart → cascading failure | Busca muito lenta ou timeout após deploy se PNCP estava degradado | A cada deploy durante degradação PNCP | `pncp_client.py:153-196` |
| **P10** | BACKEND_URL errado → 100% das buscas falham | "Servidor não configurado" ou CORS block silencioso | Misconfiguration em deploy | `route.ts:57-65` |

### VAI PARA BACKLOG — "Incomoda mas não impede resultado"

| # | Problema | Impacto | Justificativa |
|---|---------|---------|---------------|
| B1 | SETORES_FALLBACK desatualizado | Banner amarelo, mas setores core funcionam | Degradação visual, não funcional |
| B2 | Sentry sampling 10% | Erros não capturados para análise | Operacional, não bloqueia busca |
| B3 | Logs Railway 7 dias | Não consegue debugar depois de 7 dias | Post-mortem, não impacta tempo real |
| B4 | METRICS_TOKEN vazio expõe /metrics | Leak de métricas | Segurança, não UX |
| B5 | Feature flag cache 60s | Mudanças demoram 1 min | Operacional |
| B6 | Quota cache 5 min | Plano atualizado demora 5 min | UX menor |
| B7 | Excel em /tmp ephemeral | Download pode falhar após restart | Edge case raro |
| B8 | 401 durante busca perde contexto | Precisa refazer busca após login | UX inconveniente |
| B9 | Routes montadas 2x sem validação | 36 mounts, sem check se todos registraram | Risco latente |
| B10 | Frontend SSE lifecycle não logado | Difícil debugar SSE drops | Operacional |

---

## STORIES SUGERIDAS PARA O PM (Pareto — Menor Esforço, Maior Impacto)

### STORY-GTM-000: Restaurar Frontend em Produção (resolve P0)
**O que:** Verificar status do serviço `bidiq-frontend` no Railway. Possíveis causas:
1. Container crashou e excedeu max retries (3)
2. Health check `/api/health` falhou persistentemente
3. Último deploy falhou no build
4. Serviço foi pausado manualmente

**Ação:** `railway logs --service bidiq-frontend` para ver causa do crash. Se build OK, `railway up` para redeploy. Se build falhou, fix build e redeploy.

**Impacto:** Sistema COMPLETAMENTE INACESSÍVEL sem esta correção. NADA mais importa até isto estar resolvido.
**Esforço estimado:** Minutos (se for redeploy) a horas (se for bug no build)

### STORY-GTM-001: Split Health Check (resolve P1, P2, P3)
**O que:** Separar `/health` em dois endpoints:
- `/health/ready` — lightweight (ready status + uptime, <100ms, zero I/O)
- `/health/deep` — comprehensive (todos os 11 checks atuais)

Configurar Railway para usar `/health/ready` como healthcheck.
Adicionar gates de dependência no startup: só setar `_startup_time` APÓS confirmar Supabase + Redis connectivity.
Frontend health proxy deve retornar 503 quando backend reporta `ready: false`.

**Impacto:** Elimina 404s durante deploy, elimina container kills por health timeout, elimina gap "ready mas não ready".
**Esforço estimado:** Pequeno (1 arquivo backend + 1 frontend + railway.toml)

### STORY-GTM-002: Error Boundary + Mensagens Úteis (resolve P4, P6)
**O que:** Adicionar React Error Boundary wrapper em `buscar/page.tsx` com fallback UI em português.
Garantir que TODOS os erros do proxy incluam pelo menos uma ação sugerida ao usuário (tentar novamente / esperar / reduzir escopo).
Eliminar o fallback "Erro no backend" genérico — substituir por mensagem com contexto.

**Impacto:** Elimina tela branca catastrófica. Dá ao usuário sempre uma explicação + próximo passo.
**Esforço estimado:** Pequeno (2 arquivos)

### STORY-GTM-003: Schema Validation Funcional (resolve P7, P8)
**O que:** Criar a RPC function `get_table_columns_simple` em nova migration.
Adicionar fallback direto via `information_schema.columns` se RPC falhar.
Adicionar try/catch com fallback nos endpoints `analytics.py:74` e `messages.py:98`.
Validar que migrations 019, 027b/033, e 20260220120000 estão aplicadas em produção.

**Impacto:** Health check realmente detecta schema drift. Endpoints de analytics e mensagens param de crashar.
**Esforço estimado:** Médio (2-3 migrations + 3 endpoints)

### STORY-GTM-004: Auth Graceful Failure (resolve P5)
**O que:** Quando TODOS os mecanismos JWT falham (JWKS + PEM + HS256), retornar 401 (não 500).
O frontend já trata 401 corretamente (redirect para login).

**Impacto:** Usuário é redirecionado para login em vez de ver "Erro no backend".
**Esforço estimado:** Mínimo (1 linha em auth.py)

### STORY-GTM-005: Circuit Breaker Persistent (resolve P9)
**O que:** Se Redis disponível, persistir estado do circuit breaker em Redis key.
Na startup, ler estado do Redis antes de aceitar tráfego.
Se PNCP estava degradado, manter degradação até cooldown expirar.

**Impacto:** Evita cascading failure após restart durante degradação de fonte.
**Esforço estimado:** Médio (1 arquivo, pncp_client.py)

### STORY-GTM-006: BACKEND_URL Validation (resolve P10)
**O que:** No startup do frontend (não a cada request), validar que BACKEND_URL responde.
Se não responde, logar CRITICAL e mostrar banner persistente na UI.

**Impacto:** Deploy com URL errada é detectado imediatamente, não na primeira busca do usuário.
**Esforço estimado:** Pequeno (1 arquivo)

---

## PRIORIZAÇÃO FINAL — ORDEM DE EXECUÇÃO

| Prioridade | Story | Impacto | Esforço | Resolve |
|-----------|-------|---------|---------|---------|
| **0** | GTM-000 (Restaurar Frontend) | **Sistema inacessível sem isso** | Minutos-Horas | P0 |
| **1** | GTM-001 (Split Health) | Elimina 404 em deploy + container kills | Pequeno | P1, P2, P3 |
| **2** | GTM-002 (Error Boundary + Msgs) | Elimina tela branca + "Erro no backend" | Pequeno | P4, P6 |
| **3** | GTM-004 (Auth 401 not 500) | Fix de 1 linha, alto impacto | Mínimo | P5 |
| **4** | GTM-003 (Schema Validation) | Estabiliza DB + endpoints | Médio | P7, P8 |
| **5** | GTM-005 (CB Persistent) | Evita cascading post-restart | Médio | P9 |
| **6** | GTM-006 (URL Validation) | Previne misconfiguration | Pequeno | P10 |

**Com as 3 primeiras stories (GTM-001 + GTM-002 + GTM-004), eliminamos os cenários que deixam o usuário completamente sem resultado E sem explicação.**

**Com todas as 6, o sistema opera de forma consistente o suficiente para GTM.**

---

## EVIDÊNCIAS DE REFERÊNCIA POR ARQUIVO

| Arquivo | Evidências Críticas |
|---------|---------------------|
| `backend/railway.toml:16-17` | healthcheckPath="/health", timeout=120s |
| `backend/main.py:354-357` | _startup_time set before deps confirmed |
| `backend/main.py:556-711` | /health com 11 checks sem timeout individual |
| `backend/main.py:204` | RPC get_table_columns_simple (não existe) |
| `backend/auth.py:150-152` | HTTP 500 em vez de 401 quando JWT falha |
| `backend/pncp_client.py:153-196` | Circuit breaker in-memory, lost on restart |
| `backend/routes/search.py:62-80` | _build_error_detail() — structured errors |
| `backend/routes/analytics.py:74` | RPC sem fallback → crash se migration missing |
| `backend/routes/messages.py:98` | RPC sem fallback → crash se migration missing |
| `backend/search_cache.py:238-246` | .get() com defaults para campos opcionais |
| `backend/search_state_manager.py:368-403` | Fallback para missing columns (PostgreSQL 42703) |
| `frontend/app/api/buscar/route.ts:57-65` | BACKEND_URL check per-request, not startup |
| `frontend/app/api/buscar/route.ts:165` | Fallback "Erro no backend" genérico |
| `frontend/app/api/health/route.ts:18-25` | Sempre retorna 200 |
| `frontend/app/buscar/page.tsx` | Zero Error Boundaries |
| `frontend/app/buscar/hooks/useSearch.ts:389` | search_id generation |
| `frontend/app/buscar/hooks/useSearchFilters.ts:380-435` | Sector loading cascade |
| `frontend/lib/error-messages.ts:191-199` | ERROR_CODE_MESSAGES mapping |
| `supabase/migrations/` | 0 results for get_table_columns_simple |

---

*Investigação conduzida em 2026-02-20. Codebase na branch main, commit 4e33918.*
*6 tracks paralelos analisaram: infra/health, config/fallbacks, schema/DB, frontend/errors, rastreabilidade, produção.*
*Critério único de priorização: "pode deixar o usuário sem resultado ou sem explicação?"*
