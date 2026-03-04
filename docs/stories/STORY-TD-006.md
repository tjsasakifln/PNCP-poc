# STORY-TD-006: Hook Test Coverage + useSearch Decomposition

**Epic:** Resolucao de Debito Tecnico
**Tier:** 1
**Area:** Frontend
**Estimativa:** 26-34h (18-24h codigo + 8-10h testes)
**Prioridade:** P1
**Debt IDs:** FE-41, FE-03

## Objetivo

Resolver dois debitos relacionados em sequencia: (1) criar testes isolados para os 5 hooks mais criticos do sistema (atualmente 19 hooks, 0 testes isolados), e (2) decompor o mega-hook `useSearch.ts` (1,510 linhas) em 5 hooks especializados. Os testes criados na parte 1 servem como safety net para a decomposicao na parte 2.

**Sequencia obrigatoria (validada por @qa):** FE-41 (hook tests) -> FE-03 (useSearch decomp). Nunca em paralelo.

## Acceptance Criteria

### Parte 1: Hook Isolation Tests (FE-41) — 12-16h
- [ ] AC1: Criar test suite isolado para `useSearch` — cobertura dos cenarios: busca sucesso, erro, retry, SSE progress, export, abort
- [ ] AC2: Criar test suite isolado para `useSearchFilters` — cobertura: load sectors, filter by UF, filter by value range, persist filters
- [ ] AC3: Criar test suite isolado para `usePipeline` — cobertura: add item, move item, delete item, drag-and-drop reorder
- [ ] AC4: Criar test suite isolado para `useFetchWithBackoff` — cobertura: success, retry with backoff, max retries, abort on unmount
- [ ] AC5: Criar test suite isolado para `useTrialStatus` — cobertura: active trial, expired trial, no trial, loading state
- [ ] AC6: Cada test suite usa `@testing-library/react` `renderHook()` (nao renderiza componentes completos)
- [ ] AC7: Mocks para fetch/Supabase/SSE isolados por hook (nao compartilhados)
- [ ] AC8: Minimo 80% branch coverage nos 5 hooks testados
- [ ] AC9: Todos testes rodam em <30s total

### Parte 2: useSearch Decomposition (FE-03) — 14-18h
- [ ] AC10: Extrair `useSearchExecution` — logica de submit, abort, timeout, search_id management
- [ ] AC11: Extrair `useSearchSSE` — SSE connection, progress tracking, event parsing, reconnection
- [ ] AC12: Extrair `useSearchRetry` — auto-retry logic, countdown, max attempts, transient error detection
- [ ] AC13: Extrair `useSearchExport` — Excel download, Google Sheets export, report generation
- [ ] AC14: Extrair `useSearchPersistence` — search history, saved searches, session management
- [ ] AC15: `useSearch` original se torna orchestrator (<300 linhas) que compoe os 5 sub-hooks
- [ ] AC16: Interface publica de `useSearch` permanece IDENTICA (nenhum consumidor precisa mudar)
- [ ] AC17: SSE integration continua funcionando end-to-end (busca com progresso real)
- [ ] AC18: Auto-retry continua funcionando (simular 503, verificar countdown)

### Validacao
- [ ] AC19: Todos 2681+ frontend tests passam (zero regressions)
- [ ] AC20: useSearch.ts < 300 linhas (orchestrator only)
- [ ] AC21: Cada sub-hook < 350 linhas
- [ ] AC22: TypeScript strict mode passa (`npx tsc --noEmit`)
- [ ] AC23: `npm run lint` passa
- [ ] AC24: E2E busca funciona em producao (SSE + resultados + export)

## Technical Notes

**Hook test setup pattern:**
```typescript
import { renderHook, act, waitFor } from '@testing-library/react';
import { useSearch } from '@/hooks/useSearch';

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock EventSource for SSE
class MockEventSource {
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  close = jest.fn();
  // ...simulate events
}

describe('useSearch', () => {
  it('should execute search and return results', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ resultados: [] }) });
    const { result } = renderHook(() => useSearch());
    await act(async () => { result.current.buscar({ termo: 'teste' }); });
    await waitFor(() => expect(result.current.results).toBeDefined());
  });
});
```

**Decomposition strategy for useSearch:**
1. Identificar state clusters (search state, SSE state, retry state, export state, persistence state)
2. Extrair cada cluster em hook proprio com interface minima
3. Orchestrator usa composicao: `const sse = useSearchSSE(searchId);`
4. Shared state via refs ou callback pattern (evitar context para performance)
5. Manter backward compat: `useSearch()` retorna exatamente os mesmos campos

**Risco critico:** SSE integration envolve timing complexo entre `useSearchExecution` e `useSearchSSE`. O `search_id` deve ser passado sincronamente do execution para o SSE hook. Usar `useRef` para evitar re-renders desnecessarios.

**Pitfall @qa identified:** `useSearch` imports from `error-messages.ts` — all mocks MUST include `isTransientError` and `getMessageFromErrorCode`.

## Dependencies

- Nenhuma dependencia de TD-001 a TD-005
- BLOQUEIA: TD-008 (SWR adoption) depende da decomposicao estar estavel
- Pode rodar em paralelo com TD-003, TD-004, TD-005

## Definition of Done
- [ ] 5 hook test suites criados e passando
- [ ] 80%+ branch coverage nos hooks testados
- [ ] useSearch.ts < 300 linhas (orchestrator)
- [ ] 5 sub-hooks extraidos e funcionais
- [ ] Interface publica de useSearch inalterada
- [ ] SSE + retry + export funcionando E2E
- [ ] All 2681+ frontend tests passing
- [ ] Zero TypeScript errors
- [ ] Reviewed by @qa (test quality) and @architect (decomposition design)
