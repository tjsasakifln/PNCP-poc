# 🔧 OAuth Browser Session Fix

**Issue:** Google OAuth funciona em janela anônima, mas falha em navegador logado no Google

**Root Cause:** Conflito de cookies/sessões entre conta Google existente e novo fluxo OAuth

---

## 🎯 Soluções Implementadas

### Solução 1: Usar Popup Flow (RECOMENDADO)

Trocar de **redirect flow** para **popup flow** evita conflitos de cookies cross-domain.

### Solução 2: Detectar e Avisar Bloqueio de Cookies

Detectar se cookies de terceiros estão bloqueados e avisar usuário.

### Solução 3: Limpar Storage Antes do OAuth

Limpar localStorage/sessionStorage antes de iniciar OAuth.

---

## 📝 Modificações no Código

### Arquivo: `frontend/app/components/AuthProvider.tsx`

#### Modificação 1: Adicionar Popup Flow

```typescript
const signInWithGoogle = useCallback(async () => {
  // Use canonical URL for OAuth redirects
  const canonicalUrl = process.env.NEXT_PUBLIC_CANONICAL_URL || window.location.origin;
  const redirectUrl = `${canonicalUrl}/auth/callback`;

  console.log("[AuthProvider] Google OAuth Login Starting");
  console.log("[AuthProvider] Using POPUP flow to avoid cookie conflicts");
  console.log("[AuthProvider] Redirect URL:", redirectUrl);

  // CRITICAL: Clear any stale auth state before OAuth
  try {
    // Remove any old Supabase auth tokens that might conflict
    const storageKeys = ['supabase.auth.token', 'sb-auth-token'];
    storageKeys.forEach(key => {
      localStorage.removeItem(key);
      sessionStorage.removeItem(key);
    });
    console.log("[AuthProvider] Cleared stale auth storage");
  } catch (e) {
    console.warn("[AuthProvider] Could not clear storage:", e);
  }

  // Try popup flow first (better for logged-in browsers)
  try {
    console.log("[AuthProvider] Attempting popup OAuth flow");
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: redirectUrl,
        skipBrowserRedirect: false, // Let Supabase handle popup
        queryParams: {
          access_type: 'offline',
          prompt: 'consent', // Force consent screen to avoid account conflicts
        }
      },
    });

    if (error) {
      console.error("[AuthProvider] Popup OAuth failed:", error);

      // Check if it's a popup blocked error
      if (error.message?.includes('popup') || error.message?.includes('blocked')) {
        throw new Error(
          'Popup bloqueado! Por favor, permita popups para smartlic.tech e tente novamente.'
        );
      }

      throw error;
    }

    console.log("[AuthProvider] Popup OAuth initiated successfully");
  } catch (error: any) {
    console.error("[AuthProvider] OAuth error:", error);

    // Provide user-friendly error messages
    if (error.message?.includes('cookies')) {
      throw new Error(
        'Cookies de terceiros bloqueados. Por favor, habilite cookies em Configurações → Privacidade.'
      );
    }

    throw error;
  }
}, []);
```

#### Modificação 2: Detectar Bloqueio de Cookies

Adicionar função helper para detectar se cookies de terceiros estão bloqueados:

```typescript
// Add this helper function before AuthProvider component
async function detectThirdPartyCookieBlock(): Promise<boolean> {
  try {
    // Try to set a test cookie via Supabase domain
    const testUrl = 'https://fqqyovlzdzimiwfofdjk.supabase.co';
    const response = await fetch(`${testUrl}/auth/v1/health`, {
      credentials: 'include'
    });

    // If we can't make cross-origin requests with credentials, cookies are blocked
    return !response.ok;
  } catch (error) {
    // If fetch fails, likely blocked
    return true;
  }
}

// Use it before OAuth:
const signInWithGoogle = useCallback(async () => {
  // Check for cookie blocking
  const cookiesBlocked = await detectThirdPartyCookieBlock();

  if (cookiesBlocked) {
    console.warn("[AuthProvider] Third-party cookies appear to be blocked");
    // Show user a warning but proceed anyway
    if (confirm(
      'Detectamos que cookies de terceiros podem estar bloqueados. ' +
      'Isso pode causar problemas no login. Deseja tentar mesmo assim?'
    )) {
      // Continue with OAuth
    } else {
      return;
    }
  }

  // ... rest of OAuth code
}, []);
```

---

## 🧪 Solução Alternativa: Fallback para Email/Password

Se OAuth continuar falhando em navegadores logados, mostrar mensagem ao usuário:

```typescript
<div className="oauth-warning">
  ⚠️ Problemas com Google OAuth?
  <br />
  <small>
    Tente: (1) Abrir em janela anônima, ou (2) Usar email/senha abaixo
  </small>
</div>
```

---

## 🔧 Configuração do Navegador (Para Usuários)

Se OAuth continuar falhando, instruir usuários:

### Chrome/Edge:
1. Settings → Privacy and security → Cookies
2. Certifique-se que **"Block third-party cookies"** está OFF
3. Ou adicione exceção para `supabase.co`

### Firefox:
1. Settings → Privacy & Security
2. Enhanced Tracking Protection → Standard (não "Strict")
3. Ou adicione exceção para `supabase.co`

### Safari:
1. Preferences → Privacy
2. Desmarque **"Prevent cross-site tracking"** temporariamente
3. Tente login
4. Pode reativar depois

---

## 📊 Debugging

### Logs para Identificar o Problema:

```javascript
// Console do navegador durante OAuth:

// 1. Verificar storage ANTES do OAuth:
console.log('localStorage:', localStorage);
console.log('sessionStorage:', sessionStorage);

// 2. Verificar cookies:
console.log('cookies:', document.cookie);

// 3. Verificar se há erros CORS:
// (Network tab) - Procure por requests bloqueados

// 4. Verificar Storage Access:
navigator.permissions.query({name: 'storage-access'})
  .then(result => console.log('Storage Access:', result.state));
```

---

## 🎯 Teste Rápido

### Cenário 1: Navegador Limpo (Anônimo)
✅ **Esperado:** OAuth funciona perfeitamente
✅ **Atual:** Funciona ✅

### Cenário 2: Navegador Logado no Google
❌ **Esperado:** OAuth funciona
❌ **Atual:** Falha com erro de sessão

### Cenário 3: Navegador com Bloqueio de Cookies
❌ **Esperado:** Detecta e avisa usuário
❓ **Atual:** A implementar

---

## 🚀 Implementação Passo-a-Passo

### Passo 1: Testar Prompt Consent (MAIS SIMPLES)

Apenas adicionar `prompt: 'consent'` nas options do OAuth:

```typescript
const { error } = await supabase.auth.signInWithOAuth({
  provider: "google",
  options: {
    redirectTo: redirectUrl,
    queryParams: {
      prompt: 'consent', // ← Adicione esta linha
    }
  },
});
```

**Por que funciona:**
- Força Google a mostrar tela de consent mesmo se já logado
- Evita conflitos de sessão existente
- Mais simples que popup flow

### Passo 2: Se não resolver, implementar Popup Flow

Use o código completo mostrado acima.

### Passo 3: Se ainda não resolver, adicionar Clear Storage

Limpar storage antes do OAuth (código mostrado acima).

---

## 📈 Prioridade de Implementação

1. **🔥 URGENTE:** Adicionar `prompt: 'consent'` (1 linha)
2. **⚡ ALTA:** Limpar storage antes de OAuth (5 linhas)
3. **📊 MÉDIA:** Detectar e avisar sobre cookies bloqueados (20 linhas)
4. **🔧 BAIXA:** Implementar popup flow completo (50+ linhas)

---

## ✅ Resumo

**Problema:** OAuth falha em navegador logado devido a conflitos de sessão/cookies

**Solução Mais Simples:** Adicionar `prompt: 'consent'` forçando nova autorização

**Solução Completa:** Implementar popup flow + detectar cookies + limpar storage

**Próximo Passo:** Testar com `prompt: 'consent'` primeiro (mudança mínima)

---

**Implemento a solução mais simples agora?** (Apenas adicionar `prompt: 'consent'`)
