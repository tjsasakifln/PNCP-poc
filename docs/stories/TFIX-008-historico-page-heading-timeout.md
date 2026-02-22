# TFIX-008: Corrigir testes HistoricoPage (heading + timeouts)

**Status:** Pending
**Prioridade:** Média
**Estimativa:** 1h
**Arquivos afetados:** 1 test file + possivelmente 1 componente

## Problema

6 testes em `HistoricoPage.test.tsx` falham — 4 por timeout (1s) e 2 por heading não encontrado.

## Causa Raiz

### Problema 1: Heading errado
O teste busca `getByRole('heading', { name: /Histórico de Buscas/i })` mas o componente usa `<PageHeader title="Historico" />` (sem acento e texto diferente).

**Nota:** Aqui há dois bugs — o título no componente provavelmente deveria ter acento ("Histórico") E o teste pode estar com texto ligeiramente diferente do real.

### Problema 2: Timeouts
Testes usam `waitFor` com timeout padrão de 1s, mas o fluxo assíncrono do componente (auth check → fetch sessions → render) demora mais que 1s. O componente faz:
1. `useEffect` para verificar auth
2. Depois `useEffect` para `fetchSessions()` com `fetch('/api/sessions')`
3. O mock do fetch pode não resolver rápido o suficiente

Os testes que fazem `waitFor(() => expect(...))` expiram antes do ciclo async completar.

## Testes que serão corrigidos

- `HistoricoPage.test.tsx`: 6 falhas
  - `should show page title` (heading not found)
  - `should show empty state when no sessions` (timeout)
  - `should display session list` (timeout)
  - `should format currency correctly` (timeout)
  - `should handle fetch error gracefully` (timeout)
  - `should handle network error` (timeout)

## Critérios de Aceitação

- [ ] AC1: Verificar título real do componente e corrigir teste OU componente
- [ ] AC2: Se componente tem "Historico" sem acento → corrigir para "Histórico"
- [ ] AC3: Aumentar timeout de `waitFor` ou garantir que mocks resolvem sincronamente
- [ ] AC4: Todos 19 testes passam
- [ ] AC5: Não introduzir flakiness (testes devem ser determinísticos)

## Solução

1. **Heading**: Ler `PageHeader` e verificar o título real renderizado. Ajustar teste para match exato.
2. **Timeout**: Usar `waitFor(..., { timeout: 3000 })` ou refatorar mocks para resolver via `Promise.resolve()` síncrono.
3. **Acento**: Se `title="Historico"` está sem acento no componente, corrigir para `title="Histórico"`.

## Arquivos

- `frontend/__tests__/pages/HistoricoPage.test.tsx` — corrigir heading + timeout
- `frontend/app/historico/page.tsx` — possivelmente corrigir título (acento)
