# STORY-253: JWT Token Refresh — Sessão Expira Silenciosamente

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-253 |
| **Priority** | P2 |
| **Sprint** | Sprint 2 |
| **Estimate** | 5h |
| **Depends on** | Nenhuma |
| **Blocks** | Nenhuma (UX degradada, não bloqueante) |

## Problema

Logs de produção (2026-02-14) mostram JWT token expirado repetidamente a cada ~60 segundos:

```
JWT token expired
GET /v1/api/messages/unread-count -> 401
JWT token expired
GET /v1/api/messages/unread-count -> 401
... (loop infinito)
```

O token do Supabase expira e **não é renovado proativamente**. O frontend continua fazendo requests com token expirado, recebe 401, e silenciosamente ignora o erro — sem notificar o usuário e sem tentar refresh.

## Root Cause Analysis

### Fluxo Atual (Quebrado)

```
[AuthProvider]                    [useUnreadCount]              [Backend]
     |                                  |                          |
     |-- onAuthStateChange (reactive) --|                          |
     |   (só detecta mudanças locais)   |                          |
     |                                  |-- GET /unread-count ---->|
     |                                  |<---- 401 (expired) ------|
     |                                  |-- silently ignores ✗     |
     |                                  |                          |
     |   (60s later)                    |                          |
     |                                  |-- GET /unread-count ---->|
     |                                  |<---- 401 (expired) ------|
     |                                  |-- silently ignores ✗     |
     |                                  |                          |
     |   (loop infinito de 401s)        |                          |
```

### Componentes Envolvidos

| Componente | Arquivo | Comportamento Atual | Problema |
|------------|---------|---------------------|----------|
| **Supabase Browser Client** | `frontend/lib/supabase.ts` | `createBrowserClient()` com PKCE | Sem auto-refresh configurado |
| **AuthProvider** | `frontend/app/components/AuthProvider.tsx:54-169` | `onAuthStateChange()` listener (reativo) + 1 `refreshSession()` no init | Não faz refresh proativo periódico |
| **useUnreadCount** | `frontend/hooks/useUnreadCount.ts:1-52` | Poll a cada 60s, silencia 401 | Não tenta refresh, não notifica |
| **API Routes** | `frontend/app/api/*/route.ts` | Forward Bearer token as-is | Sem refresh antes de chamar backend |
| **Middleware** | `frontend/middleware.ts:32-170` | `getUser()` para validar, bypass em API routes | API routes não passam pelo middleware |
| **Backend auth.py** | `backend/auth.py:280-282` | `ExpiredSignatureError` → 401 | Correto, mas frontend não reage |
| **Token Cache** | `backend/auth.py:44-49` | 60s TTL (mesmo intervalo do poll!) | Cache pode mascarar expiração |

### Gaps Identificados

1. **Nenhum refresh proativo** — não existe `setInterval` que chame `refreshSession()` antes do token expirar
2. **Nenhum interceptor 401** — quando API route recebe 401 do backend, não tenta refresh e retry
3. **API routes bypassam middleware** — `middleware.ts:36-39` exclui `/api/*` da validação de sessão
4. **useUnreadCount silencia erros** — `catch` no poll apenas ignora, badge fica stale
5. **Supabase `onAuthStateChange` é reativo** — só detecta mudanças iniciadas pelo client-side, não detecta expiração natural do token

## Impacto

- Após ~1h de sessão, todas as chamadas autenticadas falham silenciosamente
- Badge de mensagens não-lidas fica congelado
- Busca pode falhar com 401 sem explicação clara
- Usuário não sabe que precisa fazer login novamente
- Logs de produção poluídos com 401s repetidos (1 por minuto)

---

## Acceptance Criteria

### Track 1: Proactive Token Refresh (2h)

- [ ] **AC1:** `AuthProvider` implementa refresh proativo: `setInterval` que chama `supabase.auth.refreshSession()` a cada 10 minutos (Supabase tokens têm TTL de 1h por default).
- [ ] **AC2:** Timer de refresh é limpo no cleanup do `useEffect` (evita memory leak).
- [ ] **AC3:** Se `refreshSession()` falha (ex: refresh token expirado), setar estado `sessionExpired=true` e mostrar modal/banner pedindo re-login.
- [ ] **AC4:** Log no console (dev mode): `"Token refreshed successfully"` ou `"Token refresh failed — session expired"`.

### Track 2: 401 Interceptor (2h)

- [ ] **AC5:** Criar utility `fetchWithAuth(url, options)` que wrapa `fetch` com lógica: se resposta é 401, tenta `refreshSession()` uma vez e retenta o request original com novo token.
- [ ] **AC6:** `useUnreadCount` usa `fetchWithAuth` em vez de `fetch` direto.
- [ ] **AC7:** API proxy routes (`/api/buscar`, `/api/me`, `/api/sessions`, `/api/messages/*`) usam `fetchWithAuth` ou equivalente server-side.
- [ ] **AC8:** Se retry após refresh também retorna 401, redirecionar para `/login?reason=session_expired`.

### Track 3: UX de Sessão Expirada (1h)

- [ ] **AC9:** Quando `sessionExpired=true`, mostrar toast/banner: "Sua sessão expirou. Faça login novamente para continuar."
- [ ] **AC10:** Botão "Fazer Login" no banner redireciona para `/login` preservando a URL atual como `?redirect=`.
- [ ] **AC11:** Após re-login, usuário é redirecionado de volta para a página onde estava.

---

## Arquivos a Modificar

| Arquivo | Track | Mudança |
|---------|-------|---------|
| `frontend/app/components/AuthProvider.tsx` | T1 | Adicionar `setInterval` para refresh proativo + estado `sessionExpired` |
| `frontend/lib/fetchWithAuth.ts` | T2 | **NOVO** — utility de fetch com retry em 401 |
| `frontend/hooks/useUnreadCount.ts` | T2 | Usar `fetchWithAuth`, não silenciar 401 |
| `frontend/app/api/buscar/route.ts` | T2 | Usar refresh antes de forward (server-side) |
| `frontend/app/api/me/route.ts` | T2 | Idem |
| `frontend/app/api/messages/unread-count/route.ts` | T2 | Idem |
| `frontend/app/components/SessionExpiredBanner.tsx` | T3 | **NOVO** — componente de banner |
| `frontend/middleware.ts` | T1 | Avaliar se API routes devem passar por refresh no middleware |

## Definition of Done

- [ ] Sessão não expira silenciosamente — refresh proativo a cada 10 min
- [ ] 401 → retry automático com token novo (1 tentativa)
- [ ] Se sessão realmente expirou, banner claro com redirect para login
- [ ] Zero 401 repetidos em loop nos logs de produção
- [ ] Testes unitários para `fetchWithAuth` (mock de 401 → refresh → retry)
- [ ] Zero regressão em testes existentes

## Out of Scope

- Mudanças no backend `auth.py` (comportamento 401 está correto)
- Refresh token rotation (gerenciado pelo Supabase)
- Token cache TTL no backend (60s é adequado)
