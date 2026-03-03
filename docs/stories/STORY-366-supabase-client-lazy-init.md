# STORY-366 — Lazy Initialization do Supabase Browser Client (Test Infrastructure)

**Status:** pending
**Priority:** P1 — Test Infrastructure (79 test suites falham no import)
**Origem:** Conselho CTO Advisory — Analise de falhas SSE no STORY-365 (2026-03-03)
**Componentes:** frontend/lib/supabase.ts, frontend/jest.setup.js, frontend/__tests__/
**Depende de:** nenhuma
**Bloqueia:** STORY-367 (SSE Hook Consolidation), STORY-368 (EventSource Test Utilities)
**Estimativa:** ~3h

---

## Contexto

`frontend/lib/supabase.ts` executa `createBrowserClient(supabaseUrl, supabaseAnonKey)` no **top-level do modulo** (linha 14). Quando `NEXT_PUBLIC_SUPABASE_URL` e `NEXT_PUBLIC_SUPABASE_ANON_KEY` nao estao definidos (ambiente de teste), a chamada lanca excecao.

### Cadeia de importacao toxica

```
qualquer teste que importa SearchResults
  -> SearchResults.tsx
    -> LicitacoesPreview.tsx
      -> AddToPipelineButton.tsx
        -> hooks/usePipeline.ts
          -> app/components/AuthProvider.tsx
            -> lib/supabase.ts  <-- BOOM: createBrowserClient() throws
```

79 test suites (de 135) falham no **import time** — antes de qualquer `jest.mock()` ser aplicado. Os testes que passam sao aqueles que fazem `jest.mock('../lib/supabase', ...)` no topo do arquivo (hoisting do Jest). Porem, testes que importam componentes downstream (SearchResults, LicitacoesPreview) sem mockar `lib/supabase` explicitamente recebem o erro.

### Escala do problema

- **82 test files** ja mockam `AuthProvider` manualmente
- **17 test files** ja mockam `lib/supabase` manualmente
- Ambos os mocks sao necessarios porque o modulo executa side-effects no import
- Cada novo teste que importa qualquer componente com auth precisa duplicar esse boilerplate

### Solucao

Substituir a inicializacao eager (top-level) por lazy initialization (getter function), eliminando o side-effect no import.

## Acceptance Criteria

### AC1: Lazy Supabase Client

- [ ] `lib/supabase.ts` exporta `getSupabase()` (funcao getter) em vez de `supabase` (instancia)
- [ ] A instancia e criada na primeira chamada a `getSupabase()` e cacheada (singleton pattern)
- [ ] Export `supabase` mantido como re-export via getter para backward compatibility: `export const supabase = /* lazy proxy ou getter */`
- [ ] Nenhum `createBrowserClient()` executa no top-level do modulo

### AC2: Backward Compatibility

- [ ] Todos os 24+ arquivos que importam `supabase` de `lib/supabase` continuam funcionando sem alteracao
- [ ] `AuthProvider.tsx` funciona sem mudanca (usa `supabase.auth.onAuthStateChange`)
- [ ] Runtime behavior identico — a instancia e criada antes do primeiro uso real

### AC3: jest.setup.js Global Mock

- [ ] `jest.setup.js` adiciona mock global de `lib/supabase` que retorna um mock client com:
  - `auth.getSession()` -> `{ data: { session: null }, error: null }`
  - `auth.onAuthStateChange()` -> `{ data: { subscription: { unsubscribe: jest.fn() } } }`
  - `from()` -> mock de query builder
- [ ] O mock global elimina a necessidade de `jest.mock('../lib/supabase', ...)` repetido em cada test file

### AC4: Reduzir boilerplate nos testes

- [ ] Pelo menos 50% dos `jest.mock('../lib/supabase', ...)` espalhados pelos test files podem ser REMOVIDOS (substituidos pelo mock global do AC3)
- [ ] Test files que precisam de comportamento customizado do Supabase (ex: auth-callback, mfa-flow) ainda podem sobrescrever com `jest.mock()` local

### AC5: Verificacao

- [ ] Zero test suites falham por import error de `createBrowserClient`
- [ ] `npm test` continua com 2681+ passing, 0 failures (baseline)
- [ ] `npm run build` continua sem erros de TypeScript

## Arquivos Impactados

| Arquivo | Mudanca |
|---------|---------|
| `frontend/lib/supabase.ts` | Lazy initialization via getter function + Proxy ou deferred pattern |
| `frontend/jest.setup.js` | Mock global de `lib/supabase` (elimina side-effect no import) |
| `frontend/__tests__/*.test.tsx` (17+ files) | Remover `jest.mock('../lib/supabase', ...)` redundantes |

## Notas Tecnicas

### Pattern recomendado para `lib/supabase.ts`

```typescript
import { createBrowserClient } from "@supabase/ssr";

let _client: ReturnType<typeof createBrowserClient> | null = null;

export function getSupabase() {
  if (!_client) {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
    _client = createBrowserClient(url, key, { auth: { flowType: "pkce" } });
  }
  return _client;
}

// Backward-compatible export (lazy via ES module getter)
// Consumers using `import { supabase } from 'lib/supabase'` still work
export const supabase = new Proxy({} as ReturnType<typeof createBrowserClient>, {
  get(_target, prop) {
    return (getSupabase() as any)[prop];
  },
});
```

### Alternativa mais simples (sem Proxy)

Se o Proxy causar problemas com TypeScript types:

```typescript
// jest.setup.js — mock ANTES de qualquer import
jest.mock('./lib/supabase', () => ({
  supabase: { auth: { getSession: jest.fn(), onAuthStateChange: jest.fn(() => ({ data: { subscription: { unsubscribe: jest.fn() } } })) }, from: jest.fn() },
  getSupabase: jest.fn(),
}));
```

### Risco: Barrel imports

Se algum arquivo faz `import * from 'lib/supabase'`, o Proxy pode nao funcionar. Verificar com `grep -r "import \*.*supabase"`.

### Referencia de industry best practice

Next.js oficial recomenda lazy initialization para clients que dependem de env vars: os env vars podem nao estar disponiveis durante o build ou em contextos de teste.
