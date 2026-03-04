# STORY-408: Corrigir race condition AuthProvider e perda de PKCE verifier no OAuth

**Prioridade:** P1
**Esforço:** M
**Squad:** team-bidiq-frontend

## Contexto
Dois problemas de autenticação que causam fricção no login:
1. `AuthApiError` aparece no console da landing page quando o timeout de 10s do AuthProvider dispara antes do `getUser()` completar — típico em conexões lentas ou cold start do backend.
2. OAuth callback falha quando `code_verifier` (PKCE) é perdido do localStorage entre a página de login e o callback — causado por limpeza de storage, cookies de terceiros bloqueados, ou navegação em aba anônima.

## Problema (Causa Raiz)

**AuthApiError:**
- `frontend/app/components/AuthProvider.tsx:56-73`: Timeout de 10s dispara `getSession()` concorrentemente com `getUser()` (linha 78). Ambos podem tentar setar estado simultaneamente.

**PKCE verifier:**
- `frontend/app/auth/callback/page.tsx:86-134`: `supabase.auth.exchangeCodeForSession(code)` depende de `code_verifier` armazenado no localStorage pela página de login. Se localStorage for limpo, o verifier desaparece e o exchange falha com erro opaco.

## Critérios de Aceitação
- [x] AC1: AuthProvider: Usar `isMounted` ref que é setado `false` no cleanup do useEffect. Nenhum `setState` deve ocorrer após desmontagem.
- [x] AC2: AuthProvider: Quando `getUser()` retorna `AuthApiError`, não logar como `console.error` — usar `console.warn` com mensagem amigável "Sessão expirada, redirecionando para login."
- [x] AC3: OAuth callback: Antes de chamar `exchangeCodeForSession`, verificar se `code_verifier` existe no localStorage. Se não existir, mostrar mensagem específica: "Sessão de login expirada. Por favor, tente fazer login novamente." com botão "Voltar ao login".
- [x] AC4: OAuth callback: Adicionar telemetria para taxa de falha PKCE (`oauth_pkce_missing` event).
- [x] AC5: Nenhum `AuthApiError` deve aparecer no console em fluxo normal (página pública sem usuário logado).

## Arquivos Impactados
- `frontend/app/components/AuthProvider.tsx` — Race condition fix com isMounted + cleanup.
- `frontend/app/auth/callback/page.tsx` — Validar `code_verifier` antes de exchange.

## Testes Necessários
- [x] Teste que AuthProvider não faz setState após unmount.
- [x] Teste que página pública (landing) não gera AuthApiError no console.
- [x] Teste que callback sem code_verifier mostra mensagem amigável.
- [x] Teste que callback com code_verifier funciona normalmente.

## Notas Técnicas
- Supabase JS v2 armazena PKCE no localStorage sob chave `sb-...-auth-token`.
- Considerar `sessionStorage` como fallback para `code_verifier` (mais resistente a limpeza de localStorage).
