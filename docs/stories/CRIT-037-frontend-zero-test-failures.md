# CRIT-037 — Frontend: Zero Test Failures (68 → 0)

**Status:** Done
**Priority:** P0 — Blocker
**Severity:** Infraestrutura de qualidade
**Created:** 2026-02-23
**Blocks:** GTM launch (sem baseline limpo, regressões são invisíveis)

---

## Problema

68 testes falhando em 23 suites. A causa raiz dominante é **uma só**: localização PT-BR foi aplicada no código mas os testes continuam com assertions/mocks em inglês.

### Distribuição de Causas

| Causa | Suites | Tests (aprox) |
|-------|--------|---------------|
| **Mocks de `error-messages` desatualizados** | 18 | ~50 |
| **SSE route error messages em PT-BR** | 3 | ~6 |
| **Historico `act()` warnings** | 4 | ~12 |

---

## Acceptance Criteria

### Padrão A — SSE/API Error Messages (3 suites)

As rotas SSE retornam mensagens em PT-BR, mas os testes esperam inglês.

- [x] **AC1:** `sse-proxy-errors.test.ts` — Atualizar expectations:
  - `"SSE stream timeout"` → `"Tempo limite de conexão excedido"` (route.ts:202)
  - `"Client disconnected"` → `"Conexão encerrada pelo cliente"` (route.ts:178)
  - `"Failed to connect to backend"` → `"Erro ao conectar com o servidor"` (route.ts:217)
- [x] **AC2:** `analytics.test.ts` — Alinhar mocks/assertions com mensagens reais do proxy
- [x] **AC3:** `download.test.ts` — Idem

### Padrão B — Error-Messages Mock Localization (18 suites)

Os testes mockam `lib/error-messages` com funções identity que retornam inglês. O código real retorna PT-BR.

**Estratégia:** Substituir mocks customizados por `jest.requireActual()` OU atualizar mock return values para PT-BR.

- [x] **AC4:** `ux-348-align-promise.test.tsx` — Fix mock
- [x] **AC5:** `dashboard-retry.test.tsx` — Fix mock
- [x] **AC6:** `dashboard.test.tsx` — Fix mock
- [x] **AC7:** `crit-031-dashboard-skeleton.test.tsx` — Fix mock
- [x] **AC8:** `components/EmptyState.test.tsx` — Fix mock
- [x] **AC9:** `components/LandingNavbar.test.tsx` — Fix mock/assertions
- [x] **AC10:** `components/LicitacaoCard-deadline-clarity.test.tsx` — Fix mock
- [x] **AC11:** `search-resilience.test.tsx` — Fix mock (⚠️ MEMORY.md: must include `isTransientError`)
- [x] **AC12:** `source-indicators.test.tsx` — Fix mock
- [x] **AC13:** `buscar/operational-state.test.tsx` — Fix mock
- [x] **AC14:** `buscar/crit030-state-bleed.test.tsx` — Fix mock
- [x] **AC15:** `story-257b/ux-transparente.test.tsx` — Fix mock
- [x] **AC16:** `lib/error-messages.test.ts` — Este é O teste do módulo de mensagens. Atualizar expected values para PT-BR.
- [x] **AC17:** `landing-header.test.tsx` — Fix mock/assertions
- [x] **AC18:** `landing/ProofOfValue.test.tsx` — Fix mock/assertions
- [x] **AC19:** `empty-states.test.tsx` — Fix mock

### Padrão C — Historico React act() (4 suites)

State updates em `useEffect` disparam warnings de React `act()` nos testes.

- [x] **AC20:** `pages/HistoricoUX351.test.tsx` — Wrap fetch mock resolution em `await act(async () => ...)`
- [x] **AC21:** `pages/HistoricoUX354.test.tsx` — Idem
- [x] **AC22:** `pages/HistoricoStatusBadges.test.tsx` — Idem
- [x] **AC23:** `pages/HistoricoPage.test.tsx` — Idem

### Gate Final

- [x] **AC24:** `npm test` roda com **0 failures** (2613+ passed, 0 failed)
- [x] **AC25:** Coverage ≥ 60% mantida
- [x] **AC26:** Nenhum teste deletado — apenas corrigido

---

## Estratégia de Implementação

### Abordagem recomendada para Padrão B (18 suites):

**Opção 1 (Preferida):** Criar helper `__tests__/helpers/error-messages-mock.ts`:
```typescript
// Shared mock that matches actual PT-BR behavior
export const errorMessagesMock = {
  getUserFriendlyError: jest.requireActual("../../lib/error-messages").getUserFriendlyError,
  getMessageFromErrorCode: jest.requireActual("../../lib/error-messages").getMessageFromErrorCode,
  isTransientError: jest.requireActual("../../lib/error-messages").isTransientError,
  ERROR_CODE_MESSAGES: jest.requireActual("../../lib/error-messages").ERROR_CODE_MESSAGES,
};
```

**Opção 2:** Atualizar cada mock individualmente (mais trabalho, mais frágil).

**Decisão:** Verificar na implementação se `jest.requireActual` funciona sem efeitos colaterais. Se sim, Opção 1. Se não, Opção 2.

---

## Estimativa

**Esforço:** ~4-5 horas
- Padrão A: 30min (3 files, strings diretas)
- Padrão B: 3h (18 files, mas abordagem helper amortiza)
- Padrão C: 1h (4 files, padrão repetitivo)

**Risco:** Baixo — são fixes de testes, não de código de produção

## Files

### Padrão A
- `frontend/__tests__/api/sse-proxy-errors.test.ts`
- `frontend/__tests__/api/analytics.test.ts`
- `frontend/__tests__/api/download.test.ts`
- `frontend/app/api/buscar-progress/route.ts` (referência)

### Padrão B
- `frontend/__tests__/ux-348-align-promise.test.tsx`
- `frontend/__tests__/dashboard-retry.test.tsx`
- `frontend/__tests__/dashboard.test.tsx`
- `frontend/__tests__/crit-031-dashboard-skeleton.test.tsx`
- `frontend/__tests__/components/EmptyState.test.tsx`
- `frontend/__tests__/components/LandingNavbar.test.tsx`
- `frontend/__tests__/components/LicitacaoCard-deadline-clarity.test.tsx`
- `frontend/__tests__/search-resilience.test.tsx`
- `frontend/__tests__/source-indicators.test.tsx`
- `frontend/__tests__/buscar/operational-state.test.tsx`
- `frontend/__tests__/buscar/crit030-state-bleed.test.tsx`
- `frontend/__tests__/story-257b/ux-transparente.test.tsx`
- `frontend/__tests__/lib/error-messages.test.ts`
- `frontend/__tests__/landing-header.test.tsx`
- `frontend/__tests__/landing/ProofOfValue.test.tsx`
- `frontend/__tests__/empty-states.test.tsx`
- `frontend/lib/error-messages.ts` (referência)

### Padrão C
- `frontend/__tests__/pages/HistoricoUX351.test.tsx`
- `frontend/__tests__/pages/HistoricoUX354.test.tsx`
- `frontend/__tests__/pages/HistoricoStatusBadges.test.tsx`
- `frontend/__tests__/pages/HistoricoPage.test.tsx`

### Helper (novo, se Opção 1)
- `frontend/__tests__/helpers/error-messages-mock.ts`
