# GTM-PROXY-001: Sanitizar TODAS as Proxies (Erros Ingles + Localhost Fallback)

## Epic
Root Cause — Proxy/API (EPIC-GTM-ROOT)

## Sprint
Sprint 6: GTM Root Cause — Tier 1

## Prioridade
P0

## Estimativa
12h

## Descricao

Existem 7+ proxies Next.js (`app/api/*/route.ts`) sem `sanitizeProxyError()`, 5 com fallback `localhost:8000`, e as rotas de login/signup encaminham erros do Supabase Auth em ingles cru ("Invalid login credentials", "User already registered"). O FastAPI tambem retorna erros de validacao Pydantic em ingles.

O usuario vê mensagens como "Invalid login credentials", "Stripe not configured", "Application not found", "fetch failed" — destruindo confianca no produto.

### Situacao Atual

| Componente | Comportamento | Problema |
|------------|---------------|----------|
| `app/api/buscar/route.ts` | Tem `sanitizeProxyError()` | OK (referencia) |
| `app/api/analytics/route.ts` | Sem sanitizacao | Erros crus em ingles |
| `app/api/pipeline/route.ts` | Sem sanitizacao | Erros crus |
| `app/api/feedback/route.ts` | Sem sanitizacao | Erros crus |
| `app/api/subscription-status/route.ts` | Sem sanitizacao | "pending" engolido em outage |
| 5 proxies | Fallback `localhost:8000` | Timeout + erro diferente em prod |
| Login/Signup | Supabase Auth errors forwarded | "Invalid login credentials" |
| FastAPI | Pydantic ValidationError | Erro ingles tecnico |

### Evidencia da Investigacao (Squad Root Cause 2026-02-23)

| Finding | Agente | Descricao |
|---------|--------|-----------|
| ERROR-001 | QA | sanitizeProxyError() nao aplicada em 7+ proxies |
| ERROR-005 | QA | localhost:8000 fallback em 5 proxies |
| ERROR-008-014 | QA | Erros especificos sem sanitizacao (analytics, pipeline, feedback, etc.) |
| ERROR-043 | QA | Login forward de "Invalid login credentials" |
| ERROR-044 | QA | Signup forward de "User already registered" |
| ERROR-049 | QA | FastAPI validation errors em ingles |
| ERROR-050 | QA | Stripe errors em ingles ("not configured") |

## Criterios de Aceite

### Sanitizacao de Proxies

- [ ] AC1: TODAS as proxies em `app/api/*/route.ts` usam `sanitizeProxyError()` no catch
- [ ] AC2: Zero fallback para `localhost:8000` — usar SOMENTE `BACKEND_URL` env var
- [ ] AC3: Quando `BACKEND_URL` nao definido, retornar 503 com mensagem: "Servico temporariamente indisponivel"

### Mapeamento de Erros Auth

- [ ] AC4: "Invalid login credentials" → "Email ou senha incorretos"
- [ ] AC5: "User already registered" → "Este email ja esta cadastrado"
- [ ] AC6: "Email not confirmed" → "Confirme seu email antes de fazer login"
- [ ] AC7: "Password should be at least 6 characters" → "A senha deve ter pelo menos 6 caracteres"
- [ ] AC8: Mapa centralizado em `lib/error-messages.ts` (nao espalhado em cada pagina)

### Backend Error Messages

- [ ] AC9: FastAPI exception handler para `RequestValidationError` retorna mensagem em PT
- [ ] AC10: Stripe errors sanitizados: "Erro ao processar pagamento. Tente novamente." (nunca expor detalhes Stripe)
- [ ] AC11: Supabase RLS errors: "Erro de permissao. Faca login novamente." (nunca expor "RLS policy")

### Verificacao

- [ ] AC12: `grep -r "localhost:8000" frontend/app/api/` retorna ZERO matches
- [ ] AC13: `grep -r "Invalid login" frontend/` retorna ZERO matches em user-facing code
- [ ] AC14: Nenhum erro visivel ao usuario contem texto em ingles

## Testes Obrigatorios

```bash
cd frontend && npm test -- --testPathPattern="proxy-sanitization|error-messages" --no-coverage
cd backend && pytest -k "test_error_handler" --no-coverage
```

- [ ] T1: Cada proxy retorna mensagem PT quando backend offline
- [ ] T2: Login com senha errada mostra "Email ou senha incorretos"
- [ ] T3: Signup com email existente mostra "Este email ja esta cadastrado"
- [ ] T4: FastAPI validation retorna mensagem PT
- [ ] T5: Stripe error retorna mensagem generica PT

## Arquivos Afetados

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `frontend/app/api/analytics/[...path]/route.ts` | Modificar — adicionar sanitizeProxyError |
| `frontend/app/api/pipeline/route.ts` | Modificar — adicionar sanitizeProxyError |
| `frontend/app/api/feedback/route.ts` | Modificar — adicionar sanitizeProxyError |
| `frontend/app/api/subscription-status/route.ts` | Modificar — adicionar sanitizeProxyError |
| `frontend/app/api/sessions/route.ts` | Modificar — remover localhost fallback |
| `frontend/app/api/trial-status/route.ts` | Modificar — sanitizar |
| `frontend/app/api/user/route.ts` | Modificar — sanitizar |
| `frontend/lib/error-messages.ts` | Modificar — adicionar AUTH_ERROR_MAP PT |
| `frontend/app/login/page.tsx` | Modificar — usar AUTH_ERROR_MAP |
| `frontend/app/signup/page.tsx` | Modificar — usar AUTH_ERROR_MAP |
| `backend/main.py` | Modificar — exception handler para ValidationError PT |
| `backend/auth.py` | Modificar — sanitizar Supabase errors |

## Dependencias

| Tipo | Story | Motivo |
|------|-------|--------|
| Paralela | GTM-ARCH-001 | Independente — pode ser feita em paralelo |
| Complementa | GTM-UX-002 | Erros explicitos complementam sanitizacao |
