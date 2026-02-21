# STORIES GTM-CRÍTICAS — Derivadas do Diagnóstico E2E (2026-02-20)

**Origem:** `docs/sessions/2026-02/DIAGNOSTICO-GTM-BUSCA-E2E.md`
**Critério de priorização:** "Isso pode deixar o usuário sem resultado ou sem explicação?"
**Objetivo:** Resolver de forma definitiva cada ponto de falha que impede GTM seguro.
**Codebase baseline:** branch `main`, commit `5194593`

### Trabalho já concluído (pré-condições)

| Story anterior | O que implementou | Relevante para |
|----------------|-------------------|----------------|
| **CRIT-008** | Auto-retry [10s,20s,30s], BackendStatusIndicator, search queuing, `isTransientError()` | GTM-CRIT-001, 002 |
| **CRIT-009** | `SearchErrorCode` enum, `_build_error_detail()`, `ErrorDetail.tsx`, `ERROR_CODE_MESSAGES` | GTM-CRIT-002 |
| **CRIT-010** | `_startup_time`, campo `ready` no `/health`, gunicorn `--preload`, SIGTERM handler | GTM-CRIT-001 |
| **CRIT-011** | Migration `search_id` column, session cleanup task | GTM-CRIT-004 |

### Validação contra Sentry (2026-02-21T01:15 UTC)

Erros ativos em produção confirmados e mapeados às stories:

| Sentry Error | Descrição | Story que resolve |
|-------------|-----------|-------------------|
| `POST /rpc/get_table_columns_simple` → 404 | RPC inexistente | **GTM-CRIT-004** AC4 |
| `GET /search_sessions?select=id,search_id,status,started_at` → 400 | Colunas `status`, `started_at` inexistentes | **GTM-CRIT-004** AC1 |
| `PATCH /search_sessions` → `completed_at` missing (Sentry #7280852332) | Migration 007 não sincronizada | **GTM-CRIT-004** AC1 |
| `search_sessions` fallback para `created_at` only | Code funciona degradado mas sem lifecycle tracking | **GTM-CRIT-004** AC11-AC12 |

---

## STORY GTM-CRIT-000: Restaurar Frontend em Produção

**Prioridade:** P0 — BLOQUEADOR ABSOLUTO
**Resolve:** P0 (Frontend DOWN — `smartlic.tech` retorna 404)
**Esforço:** Minutos a horas
**Depende de:** —

### Contexto

O domínio `smartlic.tech` retorna HTTP 404 com `X-Railway-Fallback: true`. O serviço `bidiq-frontend` está inoperante — container crashado, health check falhando, ou sem deploy válido. **100% dos usuários veem "Application not found".**

O backend está operacional (`bidiq-uniformes-production.up.railway.app/health` → 200 OK).

### Evidência coletada (2026-02-21 02:02 UTC)

```bash
$ curl -sS https://smartlic.tech/
{"status":"error","code":404,"message":"Application not found"}
# Headers: Server: railway-edge, X-Railway-Fallback: true

$ curl -sS https://bidiq-uniformes-production.up.railway.app/health
{"status":"healthy","ready":true,"uptime_seconds":2872.262,...}
```

### Acceptance Criteria

- [ ] **AC1 — Diagnosticar causa raiz:**
  ```bash
  railway logs --service bidiq-frontend --limit 200
  railway status
  ```
  Documentar o que aparece: crash loop? build failure? health timeout? serviço pausado?

- [ ] **AC2 — Se build falhou:** Identificar erro exato no log. Verificar:
  - `frontend/Dockerfile` existe e faz `npm run build` com sucesso
  - Todas env vars obrigatórias estão setadas no Railway (`BACKEND_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`)
  - O standalone output do Next.js inclui `/api/health` (pode ser omitido se build tiver warnings)

- [ ] **AC3 — Se container crashou (OOM/port/env):** Verificar:
  - Memória alocada ao serviço (Next.js standalone precisa de ~256MB mínimo)
  - Variável `PORT` está sendo respeitada (Railway injeta, `standalone/server.js` deve ler)
  - Nenhum `process.exit()` não-intencional no startup

- [ ] **AC4 — Se health check falhou persistentemente:** `frontend/railway.toml:14` aponta para `/api/health` com timeout 120s. Verificar:
  - A rota existe no build: `ls .next/standalone/.next/server/app/api/health/`
  - A rota responde localmente: `npm run build && PORT=3000 node .next/standalone/server.js`, depois `curl localhost:3000/api/health`

- [ ] **AC5 — Redeploy:** `railway up` ou trigger manual. Confirmar:
  ```bash
  curl -sS https://smartlic.tech/ | head -c 100
  # Deve retornar HTML, não JSON 404
  ```

- [ ] **AC6 — Validar todos os domínios:**
  | Domínio | Esperado |
  |---------|----------|
  | `https://smartlic.tech` | HTTP 200, HTML |
  | `https://app.smartlic.tech` | HTTP 200, HTML |
  | `https://bidiq-frontend-production.up.railway.app` | HTTP 200, HTML |
  | `https://www.smartlic.tech` | Redirect para `smartlic.tech` OU certificado SSL válido |

- [ ] **AC7 — Documentar causa raiz:** Criar `docs/sessions/2026-02/postmortem-frontend-down.md` com:
  - Causa raiz identificada
  - Timeline do incidente
  - O que fazer se acontecer de novo

### Definition of Done

`curl -sS https://smartlic.tech/` retorna HTML (não JSON 404). Todos os 4 domínios respondem.

### Notas para o Dev

- Railway tem 3 serviços: `Redis-hejG`, `bidiq-frontend`, `bidiq-backend`
- DNS passa por Cloudflare (104.21.78.33, 172.67.215.98) antes do Railway
- Se for problema de Cloudflare, verificar no dashboard Cloudflare se o CNAME está correto

---

## STORY GTM-CRIT-001: Health Check Lightweight + Startup Gate Real

**Prioridade:** P1 — Essencial para estabilidade de deploy
**Resolve:** P1 (health pesado mata container), P2 (frontend health mascara backend), P3 (ready antes das deps)
**Esforço:** Pequeno (4-5 arquivos, ~150 linhas)
**Depende de:** GTM-CRIT-000

### Contexto

CRIT-010 adicionou `ready: true/false` no `/health` e `_startup_time`. Mas três problemas persistem:

1. **P1 — Health check pesado mata container:** Railway usa `GET /health` com timeout 120s (`backend/railway.toml:16-17`). O endpoint (`main.py:556-711`) executa **11 checks** incluindo Supabase RPC, Redis ping+memory, 6 source health checks (10s timeout cada), circuit breaker, rate limiter, ARQ. Se qualquer dependência estiver lenta, Railway mata o container.

2. **P2 — Frontend health sempre retorna HTTP 200:** `frontend/app/api/health/route.ts:18-86` SEMPRE retorna HTTP 200. Quando `BACKEND_URL` não está definido, retorna `{"status":"healthy","backend":"not configured"}` — Railway vê 200 e assume healthy.

3. **P3 — Startup gate incompleto:** `_startup_time` é setado em `main.py:356` APÓS `_check_cache_schema()`, mas esta função retorna silenciosamente se a RPC falha (line 211-215). Não há probe real de conectividade Supabase/Redis antes de declarar ready.

### Evidência

**Backend health — 11 checks, potencial 60s+ (main.py:556-711):**
```python
# Supabase init (lines 575-583)
# OpenAI config check (lines 586-589)
# Redis ping + memory (lines 596-629)
# 6 source health checks (lines 631-658) — 10s timeout CADA
# Rate limiter stats (lines 660-665)
# ARQ queue health (lines 683-688)
# Tracing status (lines 690-692)
```

**Frontend health — sempre 200 (route.ts:21-25):**
```typescript
if (!backendUrl) {
  return NextResponse.json(
    { status: "healthy", backend: "not configured" },
    { status: 200 }  // ← Railway vê healthy, mas NADA funciona
  );
}
```

**Railway config — timeout 120s:**
```toml
# backend/railway.toml:16-17
healthcheckPath = "/health"
healthcheckTimeout = 120

# frontend/railway.toml:14-15
healthcheckPath = "/api/health"
healthcheckTimeout = 120
```

### Acceptance Criteria

**Backend — Novo endpoint `/health/ready` (lightweight):**

- [ ] **AC1:** Criar `GET /health/ready` em `main.py` — retorna JSON em <50ms:
  ```python
  @app.get("/health/ready")
  async def health_ready():
      is_ready = _startup_time is not None
      uptime = round(time.monotonic() - _startup_time, 3) if is_ready else 0.0
      return {"ready": is_ready, "uptime_seconds": uptime}
  ```
  **Restrições:** Zero I/O. Zero imports dinâmicos. Zero checks de dependência. Apenas lê `_startup_time`.

- [ ] **AC2:** O endpoint `GET /health` (deep) continua existindo sem mudança funcional. É usado por dashboards, Prometheus, debugging — NÃO por Railway.

- [ ] **AC3:** Alterar `backend/railway.toml`:
  ```toml
  healthcheckPath = "/health/ready"
  healthcheckTimeout = 30
  ```

**Backend — Startup gate com verificação real de dependências:**

- [ ] **AC4:** ANTES de setar `_startup_time` (main.py:354-357), verificar conectividade Supabase:
  ```python
  # Probe Supabase — must succeed before accepting traffic
  try:
      from supabase_client import get_supabase
      db = get_supabase()
      db.table("profiles").select("id").limit(1).execute()
      logger.info("STARTUP GATE: Supabase connectivity confirmed")
  except Exception as e:
      logger.critical(f"STARTUP GATE FAILED: Supabase unreachable — {e}")
      raise  # Crash on startup = Railway will retry
  ```

- [ ] **AC5:** Se `REDIS_URL` estiver configurado, verificar conectividade Redis antes de setar `_startup_time`:
  ```python
  if os.getenv("REDIS_URL"):
      from redis_pool import is_redis_available
      if await is_redis_available():
          logger.info("STARTUP GATE: Redis connectivity confirmed")
      else:
          logger.warning("STARTUP GATE: Redis configured but unavailable — proceeding without Redis")
          # NÃO bloquear — Redis é optional
  ```

- [ ] **AC6:** `_check_cache_schema()` e `recover_stale_searches()` continuam non-blocking (comportamento atual mantido). Apenas Supabase é gate obrigatório.

- [ ] **AC7:** Log de startup consolidado:
  ```
  STARTUP GATE: Supabase OK, Redis OK — setting ready=true
  APPLICATION READY — all routes registered, accepting traffic
  ```

**Frontend — Health reflete estado real:**

- [ ] **AC8:** Quando `BACKEND_URL` NÃO está definido, retornar HTTP 503 (não 200):
  ```typescript
  if (!backendUrl) {
    console.error("[HEALTH] CRITICAL: BACKEND_URL not configured");
    return NextResponse.json(
      { status: "misconfigured", backend: "not configured", error: "BACKEND_URL missing" },
      { status: 503 }
    );
  }
  ```
  **Razão:** `BACKEND_URL` ausente é erro de configuração DEFINITIVO (não transiente). Railway deve marcar como unhealthy.

- [ ] **AC9:** Quando backend é unreachable ou unhealthy, MANTER HTTP 200 (comportamento atual):
  ```typescript
  // Backend unreachable → 200 + backend: "unreachable" (pode ser temporário durante deploy)
  // Backend ready: false → 200 + backend: "starting" (esperado durante startup)
  // Backend unhealthy → 200 + backend: "unhealthy" (pode ser temporário)
  ```
  **Razão:** Se frontend retornar 503 quando backend está reiniciando, Railway mata o frontend também → deadlock de deploy.

- [ ] **AC10:** Alterar `frontend/railway.toml`:
  ```toml
  healthcheckTimeout = 30
  ```

**Testes:**

- [ ] **AC11:** Backend: `/health/ready` retorna `{"ready": true}` quando `_startup_time` setado.
- [ ] **AC12:** Backend: `/health/ready` retorna `{"ready": false}` quando `_startup_time` é None.
- [ ] **AC13:** Backend: `/health/ready` retorna em <50ms (sem I/O).
- [ ] **AC14:** Frontend: health retorna 503 quando `BACKEND_URL` undefined.
- [ ] **AC15:** Frontend: health retorna 200 + `backend: "unreachable"` quando fetch falha.
- [ ] **AC16:** Frontend: health retorna 200 + `backend: "healthy"` quando backend responde ready: true.

### Arquivos Afetados

| Arquivo | Mudança |
|---------|---------|
| `backend/main.py` | Novo endpoint `/health/ready` (~8 linhas), startup gate com Supabase probe (~15 linhas) |
| `backend/railway.toml:16-17` | `healthcheckPath="/health/ready"`, `healthcheckTimeout=30` |
| `frontend/app/api/health/route.ts:21-25` | 503 quando BACKEND_URL missing (em vez de 200) |
| `frontend/railway.toml:14-15` | `healthcheckTimeout=30` |
| `backend/tests/test_health_ready.py` | NOVO — 3 testes |
| `frontend/__tests__/api/health.test.ts` | Atualizar/adicionar 3 testes |

### Definition of Done

1. Deploy do backend: zero 404s transientes durante startup.
2. `GET /health/ready` responde em <50ms.
3. Frontend com `BACKEND_URL` vazio: Railway detecta 503, não marca como healthy.
4. Frontend com backend reiniciando: Railway vê 200 (não mata frontend).
5. Todos os testes passam sem regressão no baseline (~35 BE / ~42 FE).

---

## STORY GTM-CRIT-002: Error Boundary + Eliminação de "Erro no backend" Genérico

**Prioridade:** P2 — Impede tela branca e mensagens inúteis
**Resolve:** P4 (tela branca por crash de componente), P6 (mensagem genérica sem ação)
**Esforço:** Pequeno (3 arquivos, ~120 linhas)
**Depende de:** GTM-CRIT-000

### Contexto

CRIT-009 adicionou erros estruturados (`SearchErrorCode`, `ErrorDetail.tsx`, `ERROR_CODE_MESSAGES`). Mas dois problemas persistem:

1. **P4 — Tela branca catastrófica:** Zero Error Boundaries no fluxo de busca. Se qualquer componente filho de `buscar/page.tsx` lançar exceção durante render (dado inesperado, prop undefined, JSON malformado), a página inteira vira tela branca sem explicação.

2. **P6 — "Erro no backend" genérico:** O string literal `"Erro no backend"` ainda existe em `route.ts:165` e `route.ts:187`. Quando o backend retorna erro sem `error_code` estruturado (exceção não capturada, timeout interno), o proxy retorna esta mensagem genérica. O usuário não sabe se deve tentar de novo, esperar, ou mudar parâmetros.

### Evidência

**Ausência de Error Boundary:**
```bash
$ grep -r "ErrorBoundary" frontend/app/buscar/
# 0 resultados
```

**"Erro no backend" literal (route.ts:165 e 187):**
```typescript
// Linha 165:
message: isStructured ? detail.detail : (typeof detail === "string" ? detail : "Erro no backend"),
// Linha 187:
message: isStructured ? detail.detail : (typeof detail === "string" ? detail : errorBody.message || "Erro no backend"),
```

### Acceptance Criteria

**Error Boundary:**

- [ ] **AC1:** Criar `frontend/app/buscar/components/SearchErrorBoundary.tsx` — class component React que:
  - Captura erros de render em componentes filhos via `componentDidCatch`
  - Exibe UI em português: título "Algo deu errado ao exibir os resultados"
  - Botão "Tentar novamente" → `window.location.reload()`
  - Botão "Nova busca" → reseta state via callback prop `onReset`
  - Mostra `error.message` em `<details>` colapsável (para debugging)
  - Chama `Sentry.captureException(error)` se Sentry estiver disponível (import dinâmico, não quebra se Sentry não configurado)
  - Estilo consistente com o design system existente (Tailwind classes do projeto)

- [ ] **AC2:** Em `buscar/page.tsx`, envolver a área de **resultados** com `<SearchErrorBoundary>`. O formulário (`SearchForm`) fica **FORA** do boundary:
  ```tsx
  <SearchForm ... />           {/* FORA — sempre funcional */}
  <SearchErrorBoundary onReset={handleReset}>
    <SearchResults ... />      {/* DENTRO — protegido */}
    <ErrorDetail ... />
    <FeedbackButtons ... />
  </SearchErrorBoundary>
  ```
  **Razão:** Se o resultado crashar, o formulário continua acessível para nova busca.

- [ ] **AC3:** `onReset` limpa o estado de resultado/erro em `page.tsx` (seta `result` para null, `error` para null) para que o usuário volte ao estado inicial de formulário limpo.

**Eliminação de mensagens genéricas:**

- [ ] **AC4:** Em `frontend/app/api/buscar/route.ts`, substituir TODA ocorrência de `"Erro no backend"` por mensagens contextuais com ação sugerida. Mapear pelo status HTTP da resposta do backend:

  | Status backend | Mensagem para o usuário |
  |----------------|-------------------------|
  | 500 (sem error_code) | `"Ocorreu um erro interno. Tente novamente em alguns segundos."` |
  | 502 | `"O servidor está reiniciando. Aguarde ~30 segundos e tente novamente."` |
  | 429 | `"Muitas consultas simultâneas. Aguarde alguns segundos e tente novamente."` |
  | 503 | `"O servidor está temporariamente indisponível. Tente novamente em 1 minuto."` |
  | Outro / desconhecido | `"Erro inesperado. Tente novamente ou reduza o número de UFs selecionadas."` |

- [ ] **AC5:** Para erros de conexão (fetch throws), substituir mensagem de fallback em `route.ts:200-213`:
  - Connection refused: `"O servidor está temporariamente indisponível. Tente novamente em 1 minuto."`
  - Timeout (AbortError): já tem mensagem boa (manter `"Busca demorou mais que o esperado..."`)
  - DNS error: `"Erro de configuração do servidor. Contate o suporte."`

- [ ] **AC6:** Incluir `request_id` em TODAS as mensagens de erro: formato `(Ref: {request_id})` em texto secundário. Permite que suporte rastreie o erro nos logs.

- [ ] **AC7:** Verificar que NENHUMA ocorrência de `"Erro no backend"` literal permanece em `route.ts` ao final. Validar com:
  ```bash
  grep -n "Erro no backend" frontend/app/api/buscar/route.ts
  # Deve retornar 0 resultados
  ```

**Testes:**

- [ ] **AC8:** Teste: `SearchErrorBoundary` renderiza fallback UI quando componente filho lança `throw new Error("test")`.
- [ ] **AC9:** Teste: `SearchErrorBoundary` chama `onReset` quando botão "Nova busca" é clicado.
- [ ] **AC10:** Teste: proxy retorna mensagem com ação sugerida para HTTP 500 (não "Erro no backend").
- [ ] **AC11:** Teste: proxy retorna mensagem com ação sugerida para HTTP 502 (não "Erro no backend").
- [ ] **AC12:** Teste: todas as mensagens de erro incluem `request_id`.

### Arquivos Afetados

| Arquivo | Mudança |
|---------|---------|
| `frontend/app/buscar/components/SearchErrorBoundary.tsx` | NOVO (~60 linhas) |
| `frontend/app/buscar/page.tsx` | Envolver resultados com `<SearchErrorBoundary>` (~5 linhas) |
| `frontend/app/api/buscar/route.ts:165,187,200` | Substituir "Erro no backend" por mensagens contextuais (~20 linhas) |
| `frontend/__tests__/buscar/SearchErrorBoundary.test.tsx` | NOVO — 3 testes |
| `frontend/__tests__/api/buscar.test.ts` | Adicionar/atualizar 3 testes |

### Definition of Done

1. Forçar exceção em componente de resultado → usuário vê UI de erro com botão "Tentar novamente" (não tela branca).
2. Backend retorna 500 sem error_code → usuário vê "Ocorreu um erro interno. Tente novamente em alguns segundos." (não "Erro no backend").
3. `grep "Erro no backend" frontend/app/api/buscar/route.ts` retorna 0 resultados.
4. Todos os testes passam sem regressão no baseline.

---

## STORY GTM-CRIT-003: Auth Retorna 401 (Não 500) Quando JWT Config Falha

**Prioridade:** P3 — Fix de 1 linha, impacto desproporcional
**Resolve:** P5 (Auth retorna 500 em vez de 401 quando JWKS + JWT secret faltam)
**Esforço:** Mínimo (2 linhas + 2 testes)
**Depende de:** —

### Contexto

Quando **todos** os mecanismos de JWT falham (JWKS endpoint indisponível + `SUPABASE_JWT_SECRET` não configurado), `auth.py:150-152` levanta HTTP 500. O frontend trata 401 corretamente (redirect para login) mas trata 500 como "Erro no backend" genérico.

**Resultado:** Se Supabase JWKS estiver temporariamente indisponível E o `SUPABASE_JWT_SECRET` não estiver configurado, o usuário vê "Erro no backend" em vez de ser redirecionado para login.

### Evidência

```python
# backend/auth.py:150-152
logger.error("SUPABASE_JWT_SECRET not configured and no JWKS URL available!")
raise HTTPException(status_code=500, detail="Auth not configured")
```

Frontend detecta 401 e redireciona (`useSearch.ts`):
```typescript
if (response.status === 401) {
  // Redirect to login
}
```
Mas 500 cai no handler genérico de erro.

### Acceptance Criteria

- [ ] **AC1:** Em `backend/auth.py:152`, alterar:
  ```python
  # ANTES:
  raise HTTPException(status_code=500, detail="Auth not configured")

  # DEPOIS:
  raise HTTPException(
      status_code=401,
      detail="Autenticação indisponível. Faça login novamente.",
      headers={"WWW-Authenticate": "Bearer"},
  )
  ```

- [ ] **AC2:** Manter o `logger.error()` na linha 151 inalterado — a causa raiz é config, mas o **efeito** para o usuário deve ser "faça login de novo".

- [ ] **AC3:** Auditar `auth.py` inteiro para verificar se existem OUTROS `status_code=500` que deveriam ser 401. Checar:
  - `require_auth()` — quando token é inválido/expirado
  - `require_admin()` — quando user não é admin (este deve ser 403, não 401)
  - `_decode_with_fallback()` — quando decode falha

  Listar resultado da auditoria no PR description.

- [ ] **AC4:** Teste: quando `_resolve_signing_key()` levanta, response é 401 com header `WWW-Authenticate: Bearer`.
- [ ] **AC5:** Teste: `logger.error` é chamado (a causa raiz é logada para o time, mesmo que o user veja 401).

### Arquivos Afetados

| Arquivo | Mudança |
|---------|---------|
| `backend/auth.py:152` | `status_code=500` → `status_code=401`, adicionar `headers`, atualizar detail |
| `backend/tests/test_auth_401.py` | NOVO ou adicionar ao existente — 2 testes |

### Definition of Done

Com JWT config completamente quebrada (`SUPABASE_JWT_SECRET` vazio + JWKS indisponível), o frontend redireciona o usuário para login (não mostra "Erro no backend").

---

## STORY GTM-CRIT-004: Sincronização de Migrations + Schema Validation Funcional

**Prioridade:** P4 — Estabiliza DB, elimina crashes silenciosos, resolve erros ativos no Sentry
**Resolve:** P7 (RPC ausente → endpoints crasham), P8 (RPC inexistente → health check mudo), **Sentry #7280852332** (missing `completed_at` column)
**Esforço:** Médio (3 migrations + 3 arquivos backend, ~150 linhas)
**Depende de:** —

### Contexto

**3 problemas convergentes confirmados por evidência do Sentry (2026-02-21T01:15):**

1. **P8 — RPC `get_table_columns_simple` nunca foi criada:** O health check de startup (`main.py:189-215`) chama esta RPC que NÃO EXISTE. O check é silently skipped (linha 211-215). **A validação de schema NUNCA roda em produção.**

2. **Sentry #7280852332 — `search_sessions` missing 10 columns:** A migration `backend/migrations/007_search_session_lifecycle.sql` adiciona 10 colunas essenciais (`status`, `completed_at`, `started_at`, `error_code`, etc.) mas **nunca foi sincronizada para `supabase/migrations/`**. Em produção, `cron_jobs.py:71` e `search_state_manager.py:375` falham com HTTP 400 (PGRST204: column not found).

3. **P7 — Coluna `failed_ufs` inexistente:** `routes/search.py:841` faz `SELECT failed_ufs` na tabela `search_sessions`, mas essa coluna não existe em NENHUMA migration. O endpoint de retry crasharia com HTTP 400.

### Evidência do Sentry (2026-02-21T01:15:04-05 UTC)

**Erro S1 — RPC 404 (main.py:207):**
```
POST /rest/v1/rpc/get_table_columns_simple → 404 Not Found
```

**Erro S2 — search_sessions columns missing (search_state_manager.py:375):**
```
GET /rest/v1/search_sessions?select=id,search_id,status,started_at → 400 Bad Request
```

**Erro S3 — completed_at column missing (cron_jobs.py:71):**
```
PATCH /rest/v1/search_sessions → 400 Bad Request
APIError: Could not find the 'completed_at' column of 'search_sessions' in the schema cache
```

**Nota:** O código tem fallback gracioso (catch error 42703), então o sistema FUNCIONA em modo degradado. Mas o Sentry captura o erro, e o session lifecycle tracking (status, duração, errors) está completamente inoperante.

### Acceptance Criteria

**Parte A — Sincronizar migration 007 (search_sessions lifecycle):**

- [ ] **AC1:** Copiar `backend/migrations/007_search_session_lifecycle.sql` para `supabase/migrations/` com timestamp adequado (ex: `20260221100000_search_session_lifecycle.sql`). O conteúdo é idempotente (`ADD COLUMN IF NOT EXISTS`):
  ```sql
  ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'created'
      CHECK (status IN ('created', 'processing', 'completed', 'failed', 'timed_out', 'cancelled'));
  ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS error_message TEXT;
  ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS error_code TEXT;
  ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ NOT NULL DEFAULT now();
  ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
  ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS duration_ms INTEGER;
  ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS pipeline_stage TEXT;
  ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS raw_count INTEGER DEFAULT 0;
  ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS response_state TEXT;
  -- search_id já existe (migration 20260220120000), não repetir
  -- Backfill + indexes incluídos
  ```

- [ ] **AC2:** **NÃO duplicar** a adição de `search_id` — essa coluna já existe via `20260220120000_add_search_id_to_search_sessions.sql`. Remover a linha `ADD COLUMN IF NOT EXISTS search_id` da cópia (é safe por ser IF NOT EXISTS, mas evita confusão).

- [ ] **AC3:** Adicionar coluna `failed_ufs` que é usada no endpoint de retry:
  ```sql
  ALTER TABLE search_sessions ADD COLUMN IF NOT EXISTS failed_ufs TEXT[];
  ```

**Parte B — Criar RPC get_table_columns_simple:**

- [ ] **AC4:** Criar `supabase/migrations/20260221100001_create_get_table_columns_simple.sql`:
  ```sql
  CREATE OR REPLACE FUNCTION get_table_columns_simple(p_table_name TEXT)
  RETURNS TABLE(column_name TEXT)
  LANGUAGE sql
  SECURITY DEFINER
  STABLE
  AS $$
    SELECT column_name::TEXT
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = p_table_name
    ORDER BY ordinal_position;
  $$;

  GRANT EXECUTE ON FUNCTION get_table_columns_simple(TEXT) TO authenticated, service_role;
  ```

- [ ] **AC5:** Verificar que ambas migrations são idempotentes (safe to run multiple times).

**Parte C — Melhorar fallback no startup:**

- [ ] **AC6:** Em `main.py:_check_cache_schema()` (linhas 203-215), melhorar fallback quando RPC falha:
  ```python
  except Exception as rpc_err:
      logger.warning(f"CRIT-004: RPC get_table_columns_simple failed ({rpc_err}) — trying direct query")
      try:
          result = db.table("search_results_cache").select("*").limit(0).execute()
          logger.info("CRIT-004: Table search_results_cache exists (column validation skipped)")
          return
      except Exception as fallback_err:
          logger.critical(
              f"CRIT-004: Schema validation FAILED — RPC: {rpc_err}, Fallback: {fallback_err}"
          )
          return  # Non-blocking
  ```

**Parte D — Graceful degradation em endpoints:**

- [ ] **AC7:** Auditar todos os usos de `db.rpc()` no codebase:
  ```bash
  grep -rn "\.rpc(" backend/ --include="*.py"
  ```
  Listar cada RPC e se a migration correspondente existe em `supabase/migrations/`.

- [ ] **AC8:** Para endpoints com RPCs sem migration, adicionar try/except com resposta degradada.

- [ ] **AC9:** Verificar especificamente `routes/analytics.py` e `routes/messages.py`.

**Parte E — Aplicar em produção e verificar:**

- [ ] **AC10:** Aplicar migrations: `npx supabase db push`.

- [ ] **AC11:** Verificar no Sentry que os erros S1, S2, S3 **param de ocorrer** após o deploy:
  - `get_table_columns_simple` → 404 **não mais**
  - `search_sessions` select com `status,started_at` → 400 **não mais**
  - `completed_at` column missing → APIError **não mais**

- [ ] **AC12:** Verificar no log do backend:
  - `"CRIT-001: Schema validated — 0 missing columns"` (não `"Schema health check skipped"`)
  - `cron_jobs` cleanup executa sem warnings de 42703

**Testes:**

- [ ] **AC13:** Teste: `_check_cache_schema()` funciona quando RPC existe e retorna colunas.
- [ ] **AC14:** Teste: `_check_cache_schema()` faz fallback quando RPC levanta Exception.
- [ ] **AC15:** Teste: endpoint analytics retorna resposta degradada (não 500) quando RPC falha.

### Arquivos Afetados

| Arquivo | Mudança |
|---------|---------|
| `supabase/migrations/20260221100000_search_session_lifecycle.sql` | NOVO — sync de backend/migrations/007 + failed_ufs |
| `supabase/migrations/20260221100001_create_get_table_columns_simple.sql` | NOVO — RPC function |
| `backend/main.py:203-215` | Melhorar fallback em `_check_cache_schema()` |
| `backend/routes/analytics.py` | Adicionar try/except com resposta degradada |
| `backend/routes/messages.py` | Adicionar try/except se usa RPC sem migration |
| `backend/tests/test_schema_validation.py` | NOVO — 3 testes |

### Definition of Done

1. **Sentry limpo:** Erros S1, S2, S3 não recorrem após deploy.
2. Startup: log `"CRIT-001: Schema validated"` (não `"Schema health check skipped"`).
3. `cron_jobs.py` cleanup executa sem error 42703.
4. `search_state_manager.py` recover encontra sessions por `status` e `started_at`.
5. Endpoint retry (`/v1/search/{id}/retry`) pode ler `failed_ufs`.
6. Analytics com RPC ausente: retorna 200 degradado (não 500).
7. Todos os testes passam sem regressão.

---

## STORY GTM-CRIT-005: Circuit Breaker Persistente em Redis

**Prioridade:** P5 — Evita cascading failure pós-restart
**Resolve:** P9 (CB reseta no restart → cascading failure)
**Esforço:** Médio (1 arquivo principal, ~80 linhas)
**Depende de:** —

### Contexto

O estado do circuit breaker é armazenado na memória do processo (`pncp_client.py:182`). Quando Railway reinicia o container (deploy, crash, health timeout), o estado reseta para `consecutive_failures=0`. Se o PNCP estava degradado antes do restart, o backend imediatamente bombardeia a API com requisições, causando cascading failure.

**Impacto real:** Durante degradação PNCP, cada restart do container causa burst de requisições → PNCP bloqueia → mais timeouts → container reinicia → cycle repeat.

### Evidência

```python
# pncp_client.py:173-184
class PNCPCircuitBreaker:
    def __init__(self, name="pncp", ...):
        self.consecutive_failures: int = 0          # ← perdido no restart
        self.degraded_until: Optional[float] = None  # ← perdido no restart
```

O health endpoint já tem `get_state()` para Redis (main.py:643-644), mas o estado NÃO é lido de volta na inicialização.

### Acceptance Criteria

**Persistência no Redis:**

- [ ] **AC1:** Em `PNCPCircuitBreaker.__init__()`, se Redis estiver disponível, ler estado salvo:
  ```python
  async def _restore_from_redis(self) -> None:
      """Restore circuit breaker state from Redis if available."""
      try:
          from redis_pool import get_redis_pool, is_redis_available
          if not await is_redis_available():
              return
          pool = await get_redis_pool()
          data = await pool.get(f"bidiq:cb:{self.name}:state")
          if not data:
              return
          state = json.loads(data)
          self.consecutive_failures = state.get("failures", 0)
          degraded_until = state.get("degraded_until")
          if degraded_until and degraded_until > time.time():
              self.degraded_until = degraded_until
              remaining = round(degraded_until - time.time())
              logger.warning(
                  f"Circuit breaker [{self.name}] restored DEGRADED state from Redis "
                  f"(expires in {remaining}s)"
              )
          elif degraded_until:
              # Cooldown expired — start healthy
              self.consecutive_failures = 0
              self.degraded_until = None
              logger.info(
                  f"Circuit breaker [{self.name}] restored from Redis — "
                  f"cooldown expired, starting healthy"
              )
      except Exception as e:
          logger.debug(f"Circuit breaker [{self.name}] Redis restore failed: {e}")
  ```
  **Nota:** `__init__` é sync, então `_restore_from_redis()` deve ser chamado na primeira operação async OU via um método explícito `await cb.initialize()` no startup.

- [ ] **AC2:** Em `record_failure()`, se Redis disponível, persistir estado:
  ```python
  # Após atualizar self.consecutive_failures e self.degraded_until
  await self._persist_to_redis()
  ```
  Formato: `{"failures": N, "degraded_until": float|null, "updated_at": "ISO-8601"}`
  TTL: `cooldown_seconds + 300` (cooldown + 5min margem).

- [ ] **AC3:** Em `record_success()`, se Redis disponível, persistir estado limpo (failures=0, degraded_until=null).

- [ ] **AC4:** Se Redis **NÃO** estiver disponível, comportamento é IDÊNTICO ao atual (in-memory only). Zero regressão. O Redis persist é fire-and-forget com try/except.

- [ ] **AC5:** Adicionar chamada `await pncp_cb.initialize()` e `await pcp_cb.initialize()` no lifespan startup (main.py), ANTES de `_startup_time`.

**Testes:**

- [ ] **AC6:** Teste: CB persiste estado no Redis mock após `record_failure()`.
- [ ] **AC7:** Teste: CB restaura estado degradado do Redis no `initialize()`.
- [ ] **AC8:** Teste: CB com cooldown expirado no Redis reseta para healthy.
- [ ] **AC9:** Teste: CB funciona normalmente quando Redis indisponível (in-memory fallback).
- [ ] **AC10:** Teste: Múltiplas instâncias de CB (pncp, pcp) usam keys diferentes.

### Arquivos Afetados

| Arquivo | Mudança |
|---------|---------|
| `backend/pncp_client.py:153-230` | Adicionar `_restore_from_redis()`, `_persist_to_redis()`, `initialize()` |
| `backend/main.py:340-357` | Adicionar `await cb.initialize()` antes de `_startup_time` |
| `backend/tests/test_circuit_breaker_redis.py` | NOVO — 5 testes |

### Definition of Done

1. Restart durante degradação PNCP: backend inicia já em estado degradado, usa fontes alternativas (não bombardeia PNCP).
2. Restart após cooldown expirado: backend inicia healthy, retoma requisições.
3. Sem Redis configurado: comportamento idêntico ao atual (zero regressão).
4. Todos os testes passam sem regressão.

---

## STORY GTM-CRIT-006: Validação de BACKEND_URL no Startup do Frontend

**Prioridade:** P6 — Previne misconfiguration silenciosa
**Resolve:** P10 (BACKEND_URL errado → 100% buscas falham)
**Esforço:** Pequeno (1 arquivo, ~20 linhas)
**Depende de:** GTM-CRIT-001 (ambos modificam `health/route.ts`)

### Contexto

Se `BACKEND_URL` estiver errado (typo, env var desatualizada, apontando para serviço inexistente), TODAS as buscas falham com 503. A verificação acontece only per-request (`route.ts:58-65`) — não há validação proativa. O time só descobre quando um usuário reclama.

**Nota:** GTM-CRIT-001 AC8 já cobre o caso `BACKEND_URL` **não definido** (retorna 503). Esta story cobre o caso `BACKEND_URL` **definido mas errado** (URL inválida, host inexistente).

### Evidência

```typescript
// frontend/app/api/health/route.ts:21-25 (ATUAL)
if (!backendUrl) {
  return NextResponse.json(
    { status: "healthy", backend: "not configured" },
    { status: 200 }  // ← CRIT-001 muda para 503
  );
}
// Se backendUrl existe mas aponta para host errado → 200 + "unreachable" (ninguém alerta)
```

### Acceptance Criteria

- [ ] **AC1:** Em `frontend/app/api/health/route.ts`, quando `BACKEND_URL` está definido mas o probe falha com **DNS resolution error** ou **connection refused** (não timeout):
  ```typescript
  console.error(
    `[HEALTH] WARNING: BACKEND_URL '${backendUrl}' unreachable — ` +
    `possible misconfiguration: ${errorMessage}`
  );
  ```

- [ ] **AC2:** Incluir `backend_url_valid: false` no response body quando o probe falha com DNS/connection error:
  ```typescript
  return NextResponse.json({
    status: "healthy",
    backend: "unreachable",
    backend_url_valid: false,
    latency_ms: latencyMs,
    warning: `BACKEND_URL may be misconfigured: ${errorMessage}`,
  }, { status: 200 });
  ```
  **Nota:** Mantém HTTP 200 (pode ser temporário durante deploy), mas inclui `backend_url_valid: false` para monitoramento.

- [ ] **AC3:** Distinguir tipos de falha de conexão:
  | Tipo de erro | `backend_url_valid` | Interpretação |
  |-------------|---------------------|---------------|
  | DNS resolution failure | `false` | Provavelmente misconfiguration |
  | Connection refused | `false` | Host existe mas porta errada ou serviço down |
  | Timeout (5s) | `true` | Serviço existe mas lento (temporário) |
  | HTTP error (4xx/5xx) | `true` | Serviço existe mas com problema (temporário) |

- [ ] **AC4:** Log `CRITICAL` apenas para DNS resolution failure (quase certamente config errada). Connection refused e timeout são `WARNING`.

**Testes:**

- [ ] **AC5:** Teste: DNS failure → `backend_url_valid: false` + log CRITICAL.
- [ ] **AC6:** Teste: timeout → `backend_url_valid: true` + log WARNING.
- [ ] **AC7:** Teste: backend healthy → `backend_url_valid` não presente (ou true).

### Arquivos Afetados

| Arquivo | Mudança |
|---------|---------|
| `frontend/app/api/health/route.ts:69-84` | Adicionar `backend_url_valid` flag + error type detection |
| `frontend/__tests__/api/health.test.ts` | Adicionar 3 testes |

### Definition of Done

1. Deploy com `BACKEND_URL` apontando para host inexistente: log `CRITICAL` no console, `backend_url_valid: false` no health.
2. Deploy com backend reiniciando (timeout): log `WARNING`, `backend_url_valid: true`.
3. Todos os testes passam sem regressão.

---

## STORY GTM-CRIT-007: Sanitização e Classificação de Testes Pre-Existentes

**Prioridade:** P7 — Qualidade e confiança no test suite
**Resolve:** Baseline de ~35 backend + ~42 frontend test failures
**Esforço:** Médio-Grande (análise detalhada + fixes cirúrgicos)
**Depende de:** — (pode rodar em paralelo com tudo)

### Contexto

O projeto tem ~35 falhas pre-existentes no backend e ~42 no frontend. Esses testes são sistematicamente ignorados como "pre-existing baseline", mas podem estar mascarando bugs reais. O diagnóstico E2E revelou que pelo menos 5 testes backend falham por mocks desatualizados (ex: `test_api_buscar.py` — assertions mudaram após CRIT-009).

**Risco:** Se um bug real causar uma nova falha num arquivo que já tem falhas pre-existentes, a regressão passa despercebida.

### Evidência (amostra)

```
# Backend — mocks desatualizados pós-CRIT-009
FAILED tests/test_api_buscar.py::test_enforces_quota — dict != string (format changed)
FAILED tests/test_api_buscar.py::test_no_quota_enforcement — 429 != 200
FAILED tests/test_api_buscar.py::test_returns_503_when_pncp_rate_limit — format changed

# Backend — bugs potenciais
FAILED tests/integration/test_full_pipeline_cascade.py — AttributeError: 'dict' has no 'lower'
FAILED tests/integration/test_frontend_504_timeout.py — error detail assertion

# Frontend — mocks desatualizados
FAILED download.test.tsx, buscar.test.tsx, signup.test.tsx (vários)
```

7 testes estão marcados SKIP referenciando STORY-224 (que pode não existir).

### Acceptance Criteria

**Fase 1 — Classificação (análise pura, sem código):**

- [ ] **AC1:** Executar suíte completa e catalogar CADA falha:
  ```bash
  cd backend && python -m pytest --tb=line -q 2>&1 | grep "FAILED"
  cd frontend && npm test -- --ci 2>&1 | grep "FAIL\|✕"
  ```

- [ ] **AC2:** Classificar cada falha em uma das 3 categorias:
  | Categoria | Significado | Ação |
  |-----------|-------------|------|
  | **Mock desatualizado** | Teste correto, mock/assertion não reflete behavior atual | Atualizar mock |
  | **Teste obsoleto** | Funcionalidade foi removida ou substituída | Deletar teste |
  | **Bug real** | Teste correto, código está errado | Criar sub-story |

- [ ] **AC3:** Entregar tabela completa no PR com: arquivo, teste, categoria, ação proposta.

**Fase 2 — Correção (backend):**

- [ ] **AC4:** Para cada "mock desatualizado": atualizar assertion/mock para refletir o comportamento atual. **NÃO deletar** — o teste cobre funcionalidade real.

- [ ] **AC5:** Para cada "teste obsoleto": deletar com mensagem no commit explicando por quê (ex: "funcionalidade removida em GTM-002").

- [ ] **AC6:** Os 7 testes SKIP com referência a STORY-224 devem ser avaliados: se STORY-224 não existe, atualizar o skip reason ou corrigir o teste.

**Fase 3 — Correção (frontend):**

- [ ] **AC7:** Mesma classificação e correção para as ~42 falhas frontend. Priorizar testes que cobrem o fluxo de busca (`buscar.test.tsx`, `useSearch.test.tsx`).

**Fase 4 — Novo baseline:**

- [ ] **AC8:** Após correções, documentar novo baseline de falhas residuais. Target: **<20 total** (de ~77 atual).

- [ ] **AC9:** Para cada falha residual, incluir justificativa de por que não foi corrigida (ex: "depende de migration em produção", "flaky test — investigation pending").

- [ ] **AC10:** Atualizar `MEMORY.md` com o novo baseline.

### Arquivos Afetados

Múltiplos arquivos de teste — lista exata será determinada na Fase 1.

### Definition of Done

1. Todas as falhas classificadas em tabela.
2. Falhas de "mock desatualizado" corrigidas.
3. Falhas de "teste obsoleto" deletadas com justificativa.
4. Novo baseline < 20 falhas, cada uma justificada.
5. Zero regressões em testes que passavam antes.

---

## RESUMO EXECUTIVO — ORDEM DE EXECUÇÃO E PARALELIZAÇÃO

### Ordem de Execução Recomendada

```
SPRINT 1 — "Sistema Acessível" (1-2 dias)
═══════════════════════════════════════════
  [SEQUENCIAL] GTM-CRIT-000 → Frontend UP (BLOQUEADOR)
  [PARALELO após 000]:
    ├── GTM-CRIT-003 → Auth 401 (30 min, 1 dev)
    ├── GTM-CRIT-001 → Health split + startup gate (4h, 1 dev)
    └── GTM-CRIT-002 → Error boundary + mensagens (3h, 1 dev)

SPRINT 2 — "Sistema Resiliente" (2-3 dias)
═══════════════════════════════════════════
  [PARALELO]:
    ├── GTM-CRIT-004 → Schema validation (4h, 1 dev)
    ├── GTM-CRIT-005 → CB persistent (4h, 1 dev)
    └── GTM-CRIT-006 → URL validation (2h, 1 dev — APÓS CRIT-001 merge)

SPRINT 3 — "Qualidade Baseline" (3-5 dias)
═══════════════════════════════════════════
  [PARALELO]:
    └── GTM-CRIT-007 → Test sanitization (pode começar a qualquer momento)
```

### Tabela Resumo

| # | Story | Impacto | Esforço | Resolve | Depende de | Track |
|---|-------|---------|---------|---------|------------|-------|
| **0** | GTM-CRIT-000 (Restaurar Frontend) | **Sistema inacessível** | Min-Hrs | P0 | — | Bloqueador |
| **1** | GTM-CRIT-003 (Auth 401 not 500) | 2 linhas, impacto alto | 30 min | P5 | — | Paralelo |
| **2** | GTM-CRIT-001 (Health Split + Gate) | Elimina 404 em deploy | 4h | P1,P2,P3 | CRIT-000 | Sequencial |
| **3** | GTM-CRIT-002 (Error Boundary + Msgs) | Elimina tela branca | 3h | P4,P6 | CRIT-000 | Paralelo c/ 001 |
| **4** | GTM-CRIT-004 (Migrations + Schema) | Estabiliza DB + resolve 3 erros Sentry | 5h | P7,P8,Sentry#7280852332 | — | Paralelo |
| **5** | GTM-CRIT-005 (CB Persistent) | Evita cascading | 4h | P9 | — | Paralelo |
| **6** | GTM-CRIT-006 (URL Validation) | Previne misconfig | 2h | P10 | CRIT-001 | Após CRIT-001 |
| **7** | GTM-CRIT-007 (Test Sanitization) | Qualidade baseline | 3-5d | ~77 falhas | — | Background |

### Caminho Mínimo para GTM Seguro

**Com CRIT-000 + 003 + 001 + 002** (Sprint 1): o sistema opera de forma que o usuário **SEMPRE** recebe resultado **OU** explicação com ação sugerida. Zero tela branca. Zero "Erro no backend" genérico. Deploy estável.

**Com todas 7 stories:** o sistema opera com resiliência completa e test suite confiável para GTM.

### Critérios de Merge

- Cada story é um PR independente
- Cada PR deve: testes passando, zero regressão vs baseline, PR description com ACs checados
- Stories que modificam os mesmos arquivos devem ser mergeadas em sequência (001 antes de 006)
- Commit message format: `fix(scope): GTM-CRIT-NNN — descrição` ou `feat(scope): GTM-CRIT-NNN — descrição`

---

*Revisado em 2026-02-20 pelo PM.*
*Incorpora trabalho já concluído em CRIT-008, CRIT-009, CRIT-010, CRIT-011.*
*Codebase: branch main, commit 5194593.*
