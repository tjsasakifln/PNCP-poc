# SAB-005: Skeleton loading permanente sem timeout/retry

**Origem:** UX Premium Audit P1-02
**Prioridade:** P1 — Alto
**Complexidade:** M (Medium)
**Sprint:** SAB-P1
**Owner:** @dev
**Screenshots:** `ux-audit/18-busca-results-loading.png` → `ux-audit/21-busca-stuck-backend-done.png`

---

## Problema

Skeleton cards de resultado aparecem durante o loading da busca mas nunca são substituídos por resultados reais (vinculado ao SAB-001). Não há timeout nem fallback — fica em skeleton infinitamente.

**Esperado:** Após 30s sem dados novos, mostrar mensagem "Resultados demorando mais que o esperado" com botão de retry.

---

## Critérios de Aceite

### Timeout Defensivo

- [x] **AC1:** Se skeletons visíveis por > 30s sem atualização de dados, exibir banner: "A busca está demorando mais que o esperado"
- [x] **AC2:** Banner inclui botão "Tentar novamente" que re-executa a busca com mesmos parâmetros
- [x] **AC3:** Banner inclui link secundário "Ver buscas anteriores" → `/historico`

### Busca sem Resultados

- [x] **AC4:** Se `POST /buscar` retorna `resultados: []` (0 resultados), exibir empty state imediatamente (não skeleton)
- [x] **AC5:** Empty state mostra: "Nenhuma licitação encontrada para [setor] em [UFs]. Tente ampliar o período ou os estados."

### Erro de Rede

- [x] **AC6:** Se `POST /buscar` falha (network error, 5xx), exibir mensagem de erro com retry em vez de skeleton infinito
- [x] **AC7:** Máximo 3 retries automáticos com backoff (já existe em `useSearch`? Verificar e alinhar)

### Testes

- [x] **AC8:** Teste: mock POST que nunca resolve → após 30s aparece banner de timeout
- [x] **AC9:** Teste: POST retorna `resultados: []` → empty state imediato

---

## Arquivos Prováveis

- `frontend/hooks/useSearch.ts` — lógica de timeout
- `frontend/app/buscar/page.tsx` — renderização condicional skeleton vs timeout vs results
- `frontend/components/SearchResults.tsx` — empty state

## Implementação

### Arquivos Modificados

| Arquivo | Mudança |
|---------|---------|
| `frontend/app/buscar/hooks/useSearch.ts` | AC1: `skeletonTimeoutReached` state + 30s timer, reset on SSE events, cleanup on cancel/complete |
| `frontend/app/buscar/components/SearchResults.tsx` | AC1-3: Timeout banner with retry button + /historico link; AC5: pass UF names to ZeroResultsSuggestions |
| `frontend/app/buscar/page.tsx` | Pass `skeletonTimeoutReached` prop to SearchResults |
| `frontend/app/buscar/components/ZeroResultsSuggestions.tsx` | AC5: Accept `ufNames` prop, show contextual "para [setor] em [UFs]" message |
| `frontend/__tests__/hooks/useSearch-sab005.test.ts` | AC8-9: 6 tests — timeout after 30s, cancel reset, zero results immediate |
| `frontend/__tests__/components/SearchResults-sab005.test.tsx` | AC1-3, AC5: 8 tests — banner rendering, retry button, historico link, UF context |

### Notas de Implementação

- **AC4**: Already working after SAB-001 fix (loading→result transition is clean)
- **AC6-AC7**: Already implemented via CRIT-008 (auto-retry with 5s/10s/15s backoff, max 3 retries)
- **AC1**: Timer resets on each SSE event (data update), so active searches with progress don't trigger timeout
- **AC5**: Shows individual UF abbreviations when ≤5 selected, otherwise shows "X estados"

## Dependência

- SAB-001 (P0-01) — o root cause fix deve ser feito primeiro. SAB-005 é a camada defensiva de UX.
