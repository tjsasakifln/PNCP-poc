# STORIES GTM-CRÍTICAS — Derivadas do Diagnóstico E2E (2026-02-20)

**Origem:** `docs/sessions/2026-02/DIAGNOSTICO-GTM-BUSCA-E2E.md`
**Critério de priorização:** "Isso pode deixar o usuário sem resultado ou sem explicação?"
**Objetivo:** Resolver de forma definitiva cada ponto de falha que impede GTM seguro.

---

## STORY GTM-CRIT-000: Restaurar Frontend em Produção

**Prioridade:** P0 — BLOQUEADOR ABSOLUTO
**Resolve:** P0 (Frontend DOWN)
**Esforço:** Minutos a horas

### Contexto

O domínio `smartlic.tech` retorna HTTP 404 com `X-Railway-Fallback: true` do Railway edge. O serviço `bidiq-frontend` está completamente inoperante — container crashado, health check falhando repetidamente, ou sem deploy válido. 100% dos usuários veem "Application not found".

O backend está operacional (`bidiq-uniformes-production.up.railway.app/health` retorna 200 OK com `ready: true`). O problema é exclusivamente o frontend.

### Evidência

```bash
$ curl -sS -D- https://smartlic.tech/
HTTP/2 404
server: railway-edge
x-railway-fallback: true
x-railway-edge: railway/us-east4-eqdc4a
{"status":"error","code":404,"message":"Application not found","request_id":"45dTJ6xqQoexN7qeBhdwDg"}

$ curl -sS https://bidiq-frontend-production.up.railway.app/
{"status":"error","code":404,"message":"Application not found"}

$ curl -sS https://bidiq-uniformes-production.up.railway.app/health
{"status":"healthy","ready":true,"uptime_seconds":2872.262,...}
```

### Acceptance Criteria

- [ ] **AC1:** Verificar logs do serviço `bidiq-frontend` no Railway (`railway logs --service bidiq-frontend --limit 100`). Documentar causa raiz (crash, build failure, health check timeout, ou pausa manual).
- [ ] **AC2:** Se o último deploy falhou no build, identificar o erro exato, corrigir e rebuildar.
- [ ] **AC3:** Se o container crashou e excedeu `restartPolicyMaxRetries: 3`, diagnosticar o crash loop (OOM? missing env var? port conflict?) e corrigir.
- [ ] **AC4:** Se o health check `/api/health` está falhando consistentemente, verificar se a rota existe no build standalone (o standalone output do Next.js pode omitir API routes se o build tiver warnings).
- [ ] **AC5:** Executar `railway up` ou trigger redeploy. Verificar que `smartlic.tech` retorna HTTP 200 com conteúdo HTML.
- [ ] **AC6:** Verificar que `app.smartlic.tech` também responde corretamente.
- [ ] **AC7:** Verificar que `www.smartlic.tech` tem redirect ou certificado SSL válido (atualmente dá SSL error).
- [ ] **AC8:** Documentar causa raiz em `docs/sessions/2026-02/` para evitar recorrência.

### Critério de Sucesso

`curl -sS https://smartlic.tech/ | head -1` retorna HTML (não JSON 404).

### Notas para o Dev

- O Railway tem 3 serviços no projeto: `Redis-hejG`, `bidiq-frontend`, `bidiq-backend`.
- Domínios bound ao frontend: `smartlic.tech`, `app.smartlic.tech`, `bidiq-frontend-production.up.railway.app`.
- DNS passa por Cloudflare (104.21.78.33, 172.67.215.98) antes de chegar ao Railway.

---

## STORY GTM-CRIT-001: Health Check Lightweight + Startup Gate Real

**Prioridade:** P1 — Essencial para estabilidade de deploy
**Resolve:** P1 (health mata container), P2 (frontend health mascara backend), P3 (ready antes das deps)
**Esforço:** Pequeno (3-4 arquivos)

### Contexto

Três problemas relacionados à saúde do sistema convergem para uma única causa raiz: **o health check não é adequado para o que está sendo perguntado.**

1. **P1 — Health check pesado mata o container:** O Railway usa `GET /health` com timeout de 120s (`backend/railway.toml:16-17`). O endpoint `main.py:556-711` executa **11 checks** incluindo Supabase RPC, Redis ping+memory, 6 source health checks (10s timeout cada), circuit breaker state, rate limiter stats, e ARQ queue health. Se qualquer dependência estiver lenta, o Railway mata o container por timeout, causando 404s durante o deploy.

2. **P2 — Frontend health sempre retorna 200:** `frontend/app/api/health/route.ts:18-86` SEMPRE retorna HTTP 200, independente do estado do backend. O Railway vê o frontend como healthy, mas o backend pode estar crashed. Usuários acessam a página normal e só descobrem o problema ao clicar "Buscar".

3. **P3 — Startup declara "ready" antes das deps:** `main.py:354-357` seta `_startup_time` no final do lifespan, mas APÓS `_check_cache_schema()` e `recover_stale_searches()` terem feito fallback silencioso por falha. O flag `ready: true` no health não garante que as dependências estão funcionais.

### Evidência

**Backend health (main.py:556-711):**
```python
@app.get("/health", response_model=HealthResponse)
async def health():
    # 11 checks: Supabase, OpenAI config, Redis ping+memory,
    # 6 sources, 2 circuit breakers, 2 rate limiters, ARQ queue, tracing
    # Cada source check tem 10s timeout = potencial 60s+ total
```

**Frontend health (route.ts:18-25):**
```typescript
export async function GET() {
  // ALWAYS returns status: 200, even when:
  // - backend is unreachable
  // - BACKEND_URL is not configured
  // - backend reports ready: false
  return NextResponse.json({ status: "healthy", ... }, { status: 200 });
}
```

**Startup gate (main.py:354-357):**
```python
# Set AFTER _check_cache_schema() and recover_stale_searches()
# But those functions do silent fallback on failure
_startup_time = time.monotonic()
logger.info("APPLICATION READY — all routes registered, accepting traffic")
```

### Acceptance Criteria

**Backend — Split health em 2 endpoints:**

- [ ] **AC1:** Criar `GET /health/ready` — retorna `{"ready": true, "uptime_seconds": N}` em <50ms. Zero I/O. Zero imports dinâmicos. Apenas verifica `_startup_time is not None`.
- [ ] **AC2:** Manter `GET /health` como endpoint deep (dashboard, Prometheus, debugging). Sem mudança funcional.
- [ ] **AC3:** Alterar `backend/railway.toml` para usar `/health/ready` como `healthcheckPath`.
- [ ] **AC4:** Reduzir `healthcheckTimeout` de 120s para 30s (o ready check é instantâneo).

**Backend — Startup gate real:**

- [ ] **AC5:** `_startup_time` só é setado APÓS confirmar que Supabase responde a um `SELECT 1` (ou equivalente PostgREST probe).
- [ ] **AC6:** Se Redis estiver configurado (`REDIS_URL` presente), `_startup_time` só é setado APÓS `is_redis_available()` retornar True. Se Redis não estiver configurado, ignorar este gate.
- [ ] **AC7:** Se `_check_cache_schema()` falhar, logar CRITICAL mas NÃO bloquear startup (schema drift é non-blocking conforme CRIT-001).
- [ ] **AC8:** Adicionar log `"STARTUP GATE: Supabase OK, Redis OK — setting ready=true"` para evidência no Railway.

**Frontend — Health reflete backend:**

- [ ] **AC9:** `GET /api/health` retorna HTTP 200 quando backend reporta `ready: true`.
- [ ] **AC10:** `GET /api/health` retorna HTTP 503 quando:
  - `BACKEND_URL` não está configurado
  - Backend retorna `ready: false`
  - Backend é unreachable (timeout 5s)
- [ ] **AC11:** Railway passará a ver o frontend como unhealthy quando o backend estiver down, prevenindo que usuários acessem UI sem backend funcional.
- [ ] **AC12:** Alterar `frontend/railway.toml` `healthcheckTimeout` para 30s.

**Testes:**

- [ ] **AC13:** Teste unitário: `/health/ready` retorna 200 + `ready: true` quando `_startup_time` setado.
- [ ] **AC14:** Teste unitário: `/health/ready` retorna 200 + `ready: false` quando `_startup_time` é None.
- [ ] **AC15:** Teste unitário: frontend health retorna 503 quando backend unreachable.
- [ ] **AC16:** Teste unitário: frontend health retorna 200 quando backend reporta `ready: true`.

### Arquivos Afetados

| Arquivo | Mudança |
|---------|---------|
| `backend/main.py:556+` | Adicionar `/health/ready` endpoint (~10 linhas) |
| `backend/main.py:354-357` | Mover `_startup_time` para após probe de deps |
| `backend/railway.toml:16-17` | `healthcheckPath = "/health/ready"`, `healthcheckTimeout = 30` |
| `frontend/app/api/health/route.ts` | Retornar 503 quando backend down/not ready |
| `frontend/railway.toml:14-15` | `healthcheckTimeout = 30` |

### Critério de Sucesso

1. Deploy do backend: zero 404s transientes durante startup.
2. Deploy do frontend: Railway marca unhealthy se backend estiver down.
3. Health check timeout: nunca excede 5s (vs 120s atual).

---

## STORY GTM-CRIT-002: Error Boundary + Eliminação de "Erro no backend" Genérico

**Prioridade:** P2 — Impede tela branca e mensagens inúteis
**Resolve:** P4 (tela branca por crash), P6 (mensagem genérica sem ação)
**Esforço:** Pequeno (2-3 arquivos)

### Contexto

1. **P4 — Tela branca catastrófica:** Não existem React Error Boundaries no fluxo de busca. Se qualquer componente filho de `buscar/page.tsx` lançar exceção durante render (ex: dado inesperado do backend, prop undefined, JSON malformado), a página inteira vira tela branca sem nenhuma explicação.

2. **P6 — "Erro no backend" genérico:** Quando o backend retorna erro sem campo `error_code` estruturado (ex: exceção não capturada, timeout interno, resposta malformada), o proxy cai no fallback `route.ts:165`: `detail: "Erro no backend"`. O usuário não sabe se deve tentar de novo, esperar, ou mudar parâmetros.

### Evidência

**Ausência de Error Boundary:**
```bash
$ grep -r "ErrorBoundary" frontend/app/buscar/
# 0 resultados
```

**Fallback genérico (route.ts:165-187):**
```typescript
message: isStructured ? detail.detail : (typeof detail === "string" ? detail : "Erro no backend"),
// Quando detail é undefined/null/number → "Erro no backend" sem contexto
```

### Acceptance Criteria

**Error Boundary:**

- [ ] **AC1:** Criar componente `frontend/app/buscar/components/SearchErrorBoundary.tsx` que:
  - Captura erros de render em qualquer componente filho
  - Exibe UI em português com: "Algo deu errado ao exibir os resultados"
  - Inclui botão "Tentar novamente" que faz `window.location.reload()`
  - Inclui botão "Voltar ao formulário" que reseta estado de busca
  - Envia erro para Sentry via `Sentry.captureException(error)` (se disponível)
  - Mostra `error.message` em texto pequeno/colapsável para debugging

- [ ] **AC2:** Envolver o `<main>` de `buscar/page.tsx` com `<SearchErrorBoundary>`. A área de formulário (SearchForm) deve ficar FORA do boundary — se o resultado crashar, o formulário continua funcional.

- [ ] **AC3:** O Error Boundary captura exceções de render mas NÃO captura erros de event handlers ou promises (essas são tratadas pelo try/catch existente em `useSearch.ts`).

**Eliminação de mensagens genéricas:**

- [ ] **AC4:** Em `frontend/app/api/buscar/route.ts`, substituir todo `"Erro no backend"` literal por mensagens com ação sugerida:
  - HTTP 500 do backend: `"Ocorreu um erro interno. Tente novamente em alguns segundos."`
  - HTTP 502: `"O servidor está reiniciando. Aguarde ~30 segundos e tente novamente."`
  - HTTP 429: `"Muitas consultas simultâneas. Aguarde {retry_after} segundos."`
  - Timeout 504: já tem mensagem boa (manter)
  - Connection refused: `"O servidor está temporariamente indisponível. Tente novamente em 1 minuto."`
  - JSON parse error: `"Resposta inesperada do servidor. Tente novamente."`

- [ ] **AC5:** Cada mensagem de erro DEVE incluir pelo menos uma ação que o usuário pode tomar. Nenhuma mensagem pode terminar sem sugestão de próximo passo.

- [ ] **AC6:** Incluir `request_id` na mensagem em texto pequeno: `"(Ref: {request_id})"` para que suporte possa rastrear o erro.

**Testes:**

- [ ] **AC7:** Teste: Error Boundary renderiza fallback UI quando componente filho lança.
- [ ] **AC8:** Teste: Error Boundary chama Sentry.captureException.
- [ ] **AC9:** Teste: proxy retorna mensagens com ação sugerida para cada status code (500, 502, 429, 504, connection error).
- [ ] **AC10:** Nenhum `"Erro no backend"` literal existe mais em `route.ts`.

### Arquivos Afetados

| Arquivo | Mudança |
|---------|---------|
| `frontend/app/buscar/components/SearchErrorBoundary.tsx` | NOVO — Error Boundary component |
| `frontend/app/buscar/page.tsx` | Envolver `<main>` com `<SearchErrorBoundary>` |
| `frontend/app/api/buscar/route.ts:157-213` | Substituir mensagens genéricas por específicas com ação |

### Critério de Sucesso

1. Forçar exceção em componente de resultado → usuário vê UI de erro com botão de retry (não tela branca).
2. Backend retorna 500 sem error_code → usuário vê "Ocorreu um erro interno. Tente novamente." (não "Erro no backend").

---

## STORY GTM-CRIT-003: Auth Retorna 401 (Não 500) Quando JWT Config Falha

**Prioridade:** P3 — Fix de 1 linha, impacto desproporcional
**Resolve:** P5 (Auth retorna 500 em vez de 401)
**Esforço:** Mínimo (1-2 linhas)

### Contexto

Quando TODOS os mecanismos de JWT falham (JWKS + PEM + HS256), `auth.py:150-152` levanta HTTP 500 com `"Auth not configured"`. O frontend trata 401 corretamente (redirect para login) mas trata 500 como "Erro no backend" genérico.

Resultado: se Supabase JWKS estiver temporariamente indisponível E o `SUPABASE_JWT_SECRET` não estiver configurado, o usuário vê "Erro no backend" em vez de ser redirecionado para login.

### Evidência

```python
# auth.py:150-152
logger.error("SUPABASE_JWT_SECRET not configured and no JWKS URL available!")
raise HTTPException(status_code=500, detail="Auth not configured")
```

O frontend (`useSearch.ts`) detecta 401 e redireciona:
```typescript
if (response.status === 401) {
  // Redirect to login
}
```

Mas 500 cai no handler genérico de erro.

### Acceptance Criteria

- [ ] **AC1:** Alterar `auth.py:152` de `status_code=500` para `status_code=401`.
- [ ] **AC2:** Alterar detail para: `"Autenticação indisponível. Faça login novamente."`.
- [ ] **AC3:** Manter o `logger.error()` existente para alertar o time sobre misconfiguration (a causa raiz é config, mas o EFEITO para o usuário deve ser "faça login de novo").
- [ ] **AC4:** Teste: quando `_resolve_signing_key()` levanta 401, o response inclui `WWW-Authenticate: Bearer` header.
- [ ] **AC5:** Verificar que não existem OUTROS `status_code=500` em `auth.py` que deveriam ser 401. (Revisar `require_auth()` e `require_admin()`.)

### Arquivos Afetados

| Arquivo | Mudança |
|---------|---------|
| `backend/auth.py:150-152` | `status_code=500` → `status_code=401`, atualizar detail |

### Critério de Sucesso

Com JWT config completamente quebrada, o frontend redireciona o usuário para login (não mostra "Erro no backend").

---

## STORY GTM-CRIT-004: Schema Validation Funcional + RPC get_table_columns_simple

**Prioridade:** P4 — Estabiliza DB e elimina crashes silenciosos
**Resolve:** P7 (RPC crashes endpoints), P8 (RPC inexistente = health check mudo)
**Esforço:** Médio (2 migrations + 3 endpoints)

### Contexto

1. **P8 — RPC `get_table_columns_simple` nunca foi criada:** O health check de startup (`main.py:189-215`) chama uma RPC function que NÃO EXISTE em nenhuma migration. O check é silently skipped — o sistema declara "healthy" com schema potencialmente divergente. A validação de schema NUNCA roda em produção.

2. **P7 — Endpoints crasham por RPC ausente:** Se migrations 019 ou outras não foram aplicadas, endpoints que usam funções RPC (analytics, mensagens) retornam HTTP 500 sem fallback.

### Evidência

**RPC inexistente (main.py:204):**
```python
result = db.rpc(
    "get_table_columns_simple",
    {"p_table_name": "search_results_cache"},
).execute()
# Exceção capturada silenciosamente → check nunca roda
```

**Verificação:**
```bash
$ grep -r "get_table_columns_simple" supabase/migrations/ backend/migrations/
# 0 resultados — função nunca foi criada
```

### Acceptance Criteria

**Migration — Criar a RPC:**

- [ ] **AC1:** Criar migration `supabase/migrations/20260221000000_create_get_table_columns_simple.sql`:
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
```
- [ ] **AC2:** A função é `SECURITY DEFINER` para que funcione com RLS habilitado.
- [ ] **AC3:** A função é `STABLE` (read-only, cacheable).

**Startup — Fallback direto se RPC falhar:**

- [ ] **AC4:** Em `main.py:_check_cache_schema()`, se a RPC falhar, fazer fallback para query direta via PostgREST:
```python
# Fallback: query information_schema diretamente
result = db.from_("information_schema.columns") \
    .select("column_name") \
    .eq("table_schema", "public") \
    .eq("table_name", "search_results_cache") \
    .execute()
```
- [ ] **AC5:** Se ambos (RPC + fallback) falharem, logar `CRITICAL` com a mensagem exata do erro e retornar sem crashar.

**Endpoints — Graceful fallback:**

- [ ] **AC6:** Auditar todos os endpoints que usam `db.rpc()` e listar quais RPCs são chamadas. Para cada uma, verificar se a migration que a cria existe.
- [ ] **AC7:** Endpoints que usam RPCs ausentes devem retornar resposta degradada (não HTTP 500). Ex: analytics retorna `{"summary": null, "error": "Analytics temporarily unavailable"}` com HTTP 200 + flag.
- [ ] **AC8:** Logar `WARNING` quando RPC fallback é usado, com o nome da RPC e o endpoint.

**Validação em Produção:**

- [ ] **AC9:** Executar `npx supabase db push` para aplicar a nova migration em produção.
- [ ] **AC10:** Verificar que o health check de startup agora RODA a validação de schema (em vez de skip silencioso).
- [ ] **AC11:** Listar TODAS as migrations existentes vs aplicadas em produção. Documentar quais estão pendentes.

**Testes:**

- [ ] **AC12:** Teste: `_check_cache_schema()` funciona quando RPC existe.
- [ ] **AC13:** Teste: `_check_cache_schema()` faz fallback quando RPC não existe (mock Exception).
- [ ] **AC14:** Teste: endpoint analytics retorna resposta degradada (não 500) quando RPC falha.

### Arquivos Afetados

| Arquivo | Mudança |
|---------|---------|
| `supabase/migrations/20260221000000_create_get_table_columns_simple.sql` | NOVO — migration |
| `backend/main.py:189-215` | Adicionar fallback PostgREST em `_check_cache_schema()` |
| `backend/routes/analytics.py` | Adicionar try/catch com resposta degradada |
| `backend/routes/messages.py` | Adicionar try/catch com resposta degradada (se usa RPC) |

### Critério de Sucesso

1. Startup: log `"CRIT-001: Schema validated — 0 missing columns"` (não `"Schema health check skipped"`).
2. Se RPC ausente: log `"CRIT-001: Using PostgREST fallback for schema validation"` e check ainda roda.
3. Analytics endpoint com RPC ausente: retorna 200 com dados degradados (não 500).

---

## STORY GTM-CRIT-005: Circuit Breaker Persistente em Redis

**Prioridade:** P5 — Evita cascading failure pós-restart
**Resolve:** P9 (CB reseta no restart → cascading failure)
**Esforço:** Médio (1 arquivo principal)

### Contexto

O estado do circuit breaker é armazenado na memória do processo (`pncp_client.py:182`). Quando o Railway reinicia o container (deploy, health check timeout, crash), o estado reseta para 0 failures. Se o PNCP estava degradado antes do restart, o backend imediatamente bombardeia a API novamente com requisições, causando cascading failure.

### Evidência

```python
# pncp_client.py:173-184
class PNCPCircuitBreaker:
    def __init__(self, name="pncp", ...):
        self.consecutive_failures: int = 0          # ← perdido no restart
        self.degraded_until: Optional[float] = None  # ← perdido no restart
        self._lock = asyncio.Lock()
```

O `B-06 AC9` já tem `get_state()` para Redis, mas o estado NÃO é lido de volta no startup.

### Acceptance Criteria

- [ ] **AC1:** Ao inicializar `PNCPCircuitBreaker`, se Redis estiver disponível, ler estado salvo da key `bidiq:cb:{name}:state` e restaurar `consecutive_failures` e `degraded_until`.
- [ ] **AC2:** Ao chamar `record_failure()`, se Redis estiver disponível, persistir o novo estado (failures count + degraded_until) na key `bidiq:cb:{name}:state` com TTL = `cooldown_seconds + 300s` (cooldown + margem).
- [ ] **AC3:** Ao chamar `record_success()` que reseta o counter, persistir estado limpo em Redis.
- [ ] **AC4:** Se Redis NÃO estiver disponível, comportamento é idêntico ao atual (in-memory only). Zero regressão.
- [ ] **AC5:** Formato Redis: JSON `{"failures": N, "degraded_until": float_or_null, "updated_at": iso_str}`.
- [ ] **AC6:** Na startup, se Redis tem `degraded_until` no futuro, o circuit breaker inicia em estado degradado. Log: `"Circuit breaker [{name}] restored degraded state from Redis (expires in {N}s)"`.
- [ ] **AC7:** Na startup, se Redis tem `degraded_until` no passado (cooldown expirou), resetar para healthy. Log: `"Circuit breaker [{name}] restored from Redis — cooldown expired, starting healthy"`.

**Testes:**

- [ ] **AC8:** Teste: CB persiste estado no Redis mock quando disponível.
- [ ] **AC9:** Teste: CB restaura estado degradado do Redis no init.
- [ ] **AC10:** Teste: CB ignora Redis quando indisponível (fallback in-memory).
- [ ] **AC11:** Teste: CB com cooldown expirado reseta corretamente.

### Arquivos Afetados

| Arquivo | Mudança |
|---------|---------|
| `backend/pncp_client.py:153-209` | `__init__`, `record_failure`, `record_success`, `try_recover` — adicionar Redis persist/restore |

### Critério de Sucesso

1. Restart durante degradação PNCP: backend inicia já em estado degradado, usa fontes alternativas.
2. Restart após cooldown: backend inicia healthy, retoma requisições ao PNCP.
3. Sem Redis: comportamento idêntico ao atual.

---

## STORY GTM-CRIT-006: Validação de BACKEND_URL no Startup do Frontend

**Prioridade:** P6 — Previne misconfiguration silenciosa
**Resolve:** P10 (BACKEND_URL errado → 100% buscas falham)
**Esforço:** Pequeno (1 arquivo)

### Contexto

Se `BACKEND_URL` estiver errado (typo, env var desatualizada, apontando para serviço inexistente), TODAS as buscas falham com 503. A verificação acontece only per-request (`route.ts:58-65`) — não há validação no startup. O time só descobre o problema quando um usuário reclama.

### Evidência

```typescript
// route.ts:58-65 — verificação per-request, não startup
const backendUrl = process.env.BACKEND_URL;
if (!backendUrl) {
  console.error("BACKEND_URL environment variable is not configured");
  return NextResponse.json(
    { message: "Servidor nao configurado. Contate o suporte." },
    { status: 503 }
  );
}
```

A mesma variável é verificada em `health/route.ts:19-26` mas lá retorna HTTP 200 com `backend: "not configured"` — não alerta ninguém.

### Acceptance Criteria

- [ ] **AC1:** Em `frontend/app/api/health/route.ts`, quando `BACKEND_URL` não está definido:
  - Logar `console.error("[STARTUP] CRITICAL: BACKEND_URL not configured — all search requests will fail")`
  - Retornar HTTP 503 (não 200) — isto fará Railway marcar o frontend como unhealthy

- [ ] **AC2:** Em `frontend/app/api/health/route.ts`, quando o probe ao backend falha:
  - Se o erro for DNS resolution failure ou connection refused (não timeout), logar `console.error("[STARTUP] CRITICAL: BACKEND_URL '${backendUrl}' is unreachable — possible misconfiguration")`.
  - Incluir `backend_url_valid: false` no response body.

- [ ] **AC3:** O health endpoint do frontend distingue entre:
  - `BACKEND_URL` não definido → 503 (config error)
  - Backend unreachable (network) → 200 + `backend: "unreachable"` (pode ser temporário)
  - Backend retorna error → 200 + `backend: "unhealthy"` (pode ser temporário)
  - Backend retorna ready: false → 200 + `backend: "starting"` (esperado durante deploy)
  - Backend ready: true → 200 + `backend: "healthy"`

- [ ] **AC4:** Apenas `BACKEND_URL` não definido retorna 503 (é definitivamente um erro de config, não transiente).

**Testes:**

- [ ] **AC5:** Teste: health retorna 503 quando `BACKEND_URL` undefined.
- [ ] **AC6:** Teste: health retorna 200 + `backend: "unreachable"` quando fetch throws.
- [ ] **AC7:** Teste: health retorna 200 + `backend: "healthy"` quando backend responde 200 + ready: true.

### Arquivos Afetados

| Arquivo | Mudança |
|---------|---------|
| `frontend/app/api/health/route.ts` | Retornar 503 para BACKEND_URL missing, logar warnings |

### Critério de Sucesso

Deploy do frontend com `BACKEND_URL` vazio/errado: Railway detecta 503, NÃO marca como healthy, alerta na dashboard.

---

## STORY GTM-CRIT-007: Testes Pre-Existentes — Classificação e Sanitização

**Prioridade:** P7 — Backlog de qualidade
**Resolve:** Baseline de ~35 backend + ~50 frontend test failures
**Esforço:** Médio-Grande (análise + fixes cirúrgicos)

### Contexto

O projeto tem ~35 falhas pre-existentes no backend e ~50 no frontend. Esses testes foram classificados como "pre-existing" e ignorados, mas alguns podem estar mascarando bugs reais que afetam o usuário.

O diagnóstico E2E revelou que pelo menos 5 testes falham por mocks desatualizados (ex: `test_api_buscar.py` — quota e rate limit assertions mudaram após CRIT-009 structured errors). Esses precisam ser atualizados para refletir o comportamento atual, não deletados.

### Evidência (amostra de falhas backend)

```
FAILED tests/integration/test_frontend_504_timeout.py — AssertionError: Error detail must be meaningful message, not short code
FAILED tests/integration/test_full_pipeline_cascade.py — AttributeError: 'dict' object has no attribute 'lower'
FAILED tests/test_api_buscar.py::test_enforces_quota — assert 'Limite de 50 buscas' in {dict...}  (CRIT-009 mudou format)
FAILED tests/test_api_buscar.py::test_no_quota_enforcement — assert 429 == 200
FAILED tests/test_api_buscar.py::test_returns_503_when_pncp_rate_limit — assert '60' in {dict...}
```

7 testes estão marcados como SKIP com referência a STORY-224 (stale mocks).

### Acceptance Criteria

- [ ] **AC1:** Executar `pytest --tb=short -q` completo e listar TODAS as falhas com:
  - Arquivo + teste
  - Tipo de falha (assertion, attribute error, import error, mock stale)
  - Classificação: "bug real" vs "mock desatualizado" vs "test obsoleto"

- [ ] **AC2:** Para cada falha classificada como "mock desatualizado" (ex: test_api_buscar quota assertions que mudaram após CRIT-009):
  - Atualizar o mock/assertion para refletir o comportamento atual
  - NÃO deletar o teste — ele cobre funcionalidade real

- [ ] **AC3:** Para cada falha classificada como "test obsoleto" (funcionalidade removida):
  - Deletar o teste com comentário no commit explicando por quê

- [ ] **AC4:** Para cada falha classificada como "bug real" (o teste está certo, o código está errado):
  - Criar sub-story com fix específico

- [ ] **AC5:** Frontend: mesma classificação para as ~50 falhas. Priorizar as que cobrem o fluxo de busca.

- [ ] **AC6:** Ao final, o número de falhas pre-existentes deve ser documentado como novo baseline. Target: reduzir de ~85 total para <20.

- [ ] **AC7:** Os 7 testes SKIP com STORY-224 devem ser atualizados ou deletados (STORY-224 pode não existir).

### Critério de Sucesso

Baseline de falhas reduzido de ~85 para <20, com cada falha restante justificada e documentada.

---

## RESUMO EXECUTIVO — ORDEM DE EXECUÇÃO

| # | Story | Impacto | Esforço | Resolve | Depende de |
|---|-------|---------|---------|---------|------------|
| **0** | GTM-CRIT-000 (Restaurar Frontend) | **Sistema inacessível** | Min-Hrs | P0 | — |
| **1** | GTM-CRIT-001 (Health Check Split) | Elimina 404 em deploy + container kills | Pequeno | P1,P2,P3 | GTM-CRIT-000 |
| **2** | GTM-CRIT-002 (Error Boundary + Msgs) | Elimina tela branca + msgs inúteis | Pequeno | P4,P6 | GTM-CRIT-000 |
| **3** | GTM-CRIT-003 (Auth 401 not 500) | 1 linha, impacto desproporcional | Mínimo | P5 | — |
| **4** | GTM-CRIT-004 (Schema Validation) | Estabiliza DB + endpoints | Médio | P7,P8 | GTM-CRIT-000 |
| **5** | GTM-CRIT-005 (CB Persistent) | Evita cascading post-restart | Médio | P9 | — |
| **6** | GTM-CRIT-006 (URL Validation) | Previne misconfiguration | Pequeno | P10 | GTM-CRIT-001 |
| **7** | GTM-CRIT-007 (Test Sanitization) | Qualidade baseline | Médio-Grande | ~85 falhas | — |

### Caminho Crítico para GTM

```
GTM-CRIT-000 (frontend UP)
    ├── GTM-CRIT-001 (health split) ── GTM-CRIT-006 (URL validation)
    ├── GTM-CRIT-002 (error boundary)
    └── GTM-CRIT-004 (schema validation)

Paralelo (sem dependência):
    ├── GTM-CRIT-003 (auth 401)
    ├── GTM-CRIT-005 (CB persistent)
    └── GTM-CRIT-007 (test sanitization)
```

**Com GTM-CRIT-000 + 001 + 002 + 003:** o sistema opera de forma que o usuário SEMPRE recebe resultado OU explicação com ação sugerida.

**Com todas 7:** o sistema opera com resiliência suficiente para GTM.

---

*Gerado em 2026-02-20 a partir do diagnóstico do full squad.*
*Codebase: branch main, commit 4e33918.*
