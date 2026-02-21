# UX-336 — Flash de "Falha na autenticação" durante Google OAuth bem-sucedido

**Tipo:** Bug / UX
**Prioridade:** Alta (afeta 100% dos logins Google OAuth)
**Criada:** 2026-02-21
**Status:** Implementado

---

## Problema

Durante login via Google OAuth, uma tela de erro "Falha na autenticação" com mensagem **"PKCE code verifier not found in storage"** é exibida brevemente (~500ms-2s) antes do login ser completado com sucesso e o usuário redirecionado para `/buscar`.

### Screenshot do Bug

A tela mostra:
- ✕ vermelho grande
- "Falha na autenticação"
- "PKCE code verifier not found in storage. This can happen if the auth flow was initiated in a different browser or device, or if the storage was cleared. For SSR frameworks (Next.js, SvelteKit, etc.), use @supabase/ssr on both the server and client to store the code verifier in cookies."
- Botão "Tentar novamente"

### Impacto

- **UX negativo**: Usuário vê mensagem técnica assustadora ("PKCE code verifier", "storage was cleared")
- **Perda de confiança**: Tela vermelha de erro antes de sucesso cria ansiedade
- **Falso negativo**: Alguns usuários podem clicar "Tentar novamente" antes do redirect automático
- **Afeta 100% dos logins Google OAuth** (reproduzível consistentemente)

---

## Root Cause Analysis

### Fluxo atual (bugado)

```
1. Login page → signInWithOAuth() → salva code_verifier no localStorage
2. Google OAuth → redirect de volta com ?code=xxx
3. Callback page monta → limpa storage stale (linhas 35-62)
4. exchangeCodeForSession(code) → busca code_verifier no localStorage
5. Code verifier AUSENTE → AuthPKCECodeVerifierMissingError
6. setStatus("error") + setErrorMessage(error.message) → TELA DE ERRO APARECE
7. return (linha 127) → fallbacks NÃO executam
8. useEffect tem [status] como dependência → re-executa quando status muda para "error"
9. Na 2ª execução: exchangeCodeForSession falha de novo (code já usado)
10. Cai no fallback getUser() (linha 181) → encontra usuário via cookies HTTP
11. setStatus("success") → redirect para /buscar
```

### Por que o code_verifier desaparece?

O code_verifier é salvo no `localStorage` pelo `signInWithOAuth()` em `AuthProvider.tsx`. Porém:

1. **Limpeza agressiva de storage** (linhas 35-62 do callback): Remove chaves `sb-*` do localStorage. A proteção `!key.includes('code_verifier')` deveria preservar, mas o **timing** entre a limpeza e o `exchangeCodeForSession` pode criar uma race condition
2. **Browser/SSR mismatch**: O Supabase browser client (`lib/supabase.ts`) usa `createBrowserClient` com `flowType: "pkce"` que armazena o verifier em localStorage. Em SSR frameworks, o recomendado é usar cookies via `@supabase/ssr`
3. **Re-render causa re-execução**: A dependência `[status]` no useEffect faz o callback executar múltiplas vezes

### Arquivo principal

`frontend/app/auth/callback/page.tsx` (268 linhas)

---

## Acceptance Criteria

### AC1 — Não mostrar tela de erro quando PKCE falha mas login é recuperável
- [x] Quando `exchangeCodeForSession()` falha com erro PKCE, NÃO definir `status="error"` imediatamente
- [x] Em vez de `return`, continuar para o fallback `getUser()`
- [x] Manter o estado `"loading"` (spinner) durante toda a recuperação
- [x] Verificação: Login Google OAuth → spinner contínuo → redirect para /buscar (zero flash de erro)

### AC2 — Fallback robusto com getUser() + onAuthStateChange
- [x] Quando code exchange falha (qualquer motivo), tentar `getUser()` antes de mostrar erro
- [x] Se `getUser()` encontrar usuário autenticado, tratar como sucesso
- [x] Se `getUser()` falhar, tentar `onAuthStateChange` com timeout de 10s
- [x] Somente mostrar tela de erro se TODOS os fallbacks falharem

### AC3 — Remover `[status]` da dependência do useEffect
- [x] Alterar `useEffect(() => { ... }, [status])` para `useEffect(() => { ... }, [])`
- [x] Isso evita re-execução do callback quando status muda (causa do loop)
- [x] O callback deve executar apenas UMA vez no mount

### AC4 — Mensagem de erro humanizada (quando erro genuíno)
- [x] Substituir mensagem técnica do Supabase ("PKCE code verifier not found in storage...") por mensagem amigável
- [x] Mensagem sugerida: "Não foi possível completar o login com Google. Isso pode acontecer por instabilidade temporária. Tente novamente."
- [x] Nunca mostrar termos técnicos (PKCE, code verifier, storage, SSR) para o usuário
- [x] Manter log técnico no console.error para debug

### AC5 — Timeout adequado para fallback completo
- [x] Timeout geral: 15s (atual 30s é excessivo para UX)
- [x] Timeout do `onAuthStateChange` listener: 10s (atual 5s pode ser insuficiente em redes lentas)
- [x] Se timeout atingido, mostrar mensagem amigável (AC4) + botão "Tentar novamente"

### AC6 — Testes
- [x] Teste: `exchangeCodeForSession` falha com PKCE error → fallback `getUser` sucede → status="success" (sem flash de erro)
- [x] Teste: `exchangeCodeForSession` falha + `getUser` falha + `onAuthStateChange` sucede → status="success"
- [x] Teste: Todos os fallbacks falham → status="error" com mensagem amigável (não técnica)
- [x] Teste: `exchangeCodeForSession` sucede na 1ª tentativa → fluxo normal (sem regressão)
- [x] Teste: Timeout → mensagem amigável exibida
- [x] Zero regressão nos testes existentes (50 fail / 2002 pass = baseline)

### AC7 — Logging estruturado para observabilidade
- [x] Log `console.warn` quando PKCE falha mas fallback recupera (para monitorar frequência)
- [x] Log `console.error` apenas quando todos os fallbacks falham (erro genuíno)
- [x] Incluir timestamps e duração de cada tentativa nos logs

---

## Implementação Sugerida

### Opção 1 — Quick Fix (Recomendada, menor risco)

Modificar o fluxo em `auth/callback/page.tsx` para NÃO fazer `return` quando `exchangeCodeForSession` falha:

```typescript
// ANTES (bugado):
if (exchangeError) {
  setStatus("error");
  setErrorMessage(exchangeError.message);
  return; // ← BUG: impede fallback
}

// DEPOIS (corrigido):
if (exchangeError) {
  console.warn("[OAuth Callback] Code exchange failed, trying fallback:", exchangeError.message);
  // NÃO fazer return — continuar para fallback getUser()
}
```

E remover `[status]` da dependência do useEffect:

```typescript
// ANTES:
useEffect(() => { handleCallback(); }, [status]); // ← BUG: re-executa em loop

// DEPOIS:
useEffect(() => { handleCallback(); }, []); // ← Executa apenas no mount
```

### Opção 2 — Proper Fix (maior esforço, solução definitiva)

Converter callback para **Route Handler** (`app/auth/callback/route.ts`) usando `@supabase/ssr` server-side:

```typescript
// app/auth/callback/route.ts
import { createServerClient } from '@supabase/ssr';
import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get('code');

  if (code) {
    const supabase = createServerClient(/* ... cookies ... */);
    await supabase.auth.exchangeCodeForSession(code);
  }

  return NextResponse.redirect(new URL('/buscar', request.url));
}
```

Isso elimina o problema de PKCE porque o server-side client armazena o code_verifier em cookies HTTP-only (não localStorage).

### Recomendação

**Opção 1** para fix imediato (1-2h). **Opção 2** como melhoria futura (refactor maior).

---

## Arquivos Envolvidos

| Arquivo | Ação |
|---------|------|
| `frontend/app/auth/callback/page.tsx` | **Modificar** — lógica de fallback + remover [status] dep |
| `frontend/__tests__/auth-callback.test.tsx` | **Criar** — testes para cenários de fallback |

---

## Definição de Pronto

- [x] Login Google OAuth: spinner → redirect (ZERO flash de erro)
- [x] Mensagem técnica PKCE nunca visível para o usuário
- [x] Testes passando (5 novos, zero regressão)
- [x] Console logs estruturados para debug

---

## Notas Técnicas

- O `useEffect` com `[status]` como dependência é o amplificador do bug — faz o callback re-executar quando o status muda para "error", criando um loop que eventualmente resolve via fallback
- A mensagem "PKCE code verifier not found" é um erro do `@supabase/auth-js` (GoTrueClient), não do backend
- O login funciona porque os cookies HTTP do Google redirect são válidos — o `getUser()` os valida independente do PKCE flow
- Testar em modo incógnito (maior chance de code_verifier ser perdido)
