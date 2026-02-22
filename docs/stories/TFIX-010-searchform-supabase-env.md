# TFIX-010: Corrigir SearchForm.test.tsx (Supabase env não mockado)

**Status:** Pending
**Prioridade:** Alta
**Estimativa:** 30min
**Arquivos afetados:** 1 test file

## Problema

O test suite inteiro de `SearchForm.test.tsx` falha antes de executar qualquer teste — 0 testes rodam.

## Causa Raiz

A importação do `SearchForm` component dispara uma cadeia de imports:

```
SearchForm.tsx
  → useSearchFilters.ts
    → AuthProvider.tsx
      → lib/supabase.ts
        → createBrowserClient(supabaseUrl, supabaseAnonKey)
```

`supabaseUrl` e `supabaseAnonKey` são `undefined` no ambiente de teste (variáveis de ambiente não configuradas), e `@supabase/ssr` lança:

```
@supabase/ssr: Your project's URL and API key are required to create a Supabase client!
```

Isso acontece no import-time, antes de qualquer mock poder ser aplicado.

## Testes que serão corrigidos

- `SearchForm.test.tsx`: suite inteira (todos os testes — atualmente 0/0)

## Critérios de Aceitação

- [ ] AC1: `lib/supabase.ts` é mockado antes do import de `SearchForm`
- [ ] AC2: Todos os testes de `SearchForm.test.tsx` executam e passam
- [ ] AC3: Nenhum import real de Supabase acontece durante testes

## Solução

Adicionar mock de `lib/supabase` no topo do arquivo de teste (antes de qualquer import do componente):

```typescript
jest.mock('../../lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: jest.fn().mockResolvedValue({ data: { session: null }, error: null }),
      onAuthStateChange: jest.fn().mockReturnValue({ data: { subscription: { unsubscribe: jest.fn() } } }),
    },
  },
}));
```

Ou alternativamente, configurar variáveis de ambiente no `jest.setup.js`:
```javascript
process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://test.supabase.co';
process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'test-anon-key';
```

**A primeira opção é preferível** pois evita qualquer tentativa de conexão real.

## Arquivos

- `frontend/__tests__/components/SearchForm.test.tsx` — adicionar mock de supabase
