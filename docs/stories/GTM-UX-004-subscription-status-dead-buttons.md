# GTM-UX-004: Subscription Status Proxy + Dead Buttons

## Epic
Root Cause — UX (EPIC-GTM-ROOT)

## Sprint
Sprint 7: GTM Root Cause — Tier 2

## Prioridade
P1

## Estimativa
6h

## Descricao

Dois problemas conectados: (1) O proxy de subscription-status engole erros e retorna "pending" durante outage — o usuario pos-pagamento pensa que o plano nao ativou. (2) O botao "Ver ultima busca" no componente `SourcesUnavailable` esta permanentemente desabilitado (hardcoded `false` ou nunca wired ao estado real).

### Situacao Atual

| Componente | Comportamento | Problema |
|------------|---------------|----------|
| `app/api/subscription-status/route.ts` | Erro → retorna `{ status: "pending" }` | Usuario pensa que plano nao ativou |
| `SourcesUnavailable.tsx` L544 | Botao "Ver ultima busca" | `hasLastSearch` sempre false — botao morto |
| Pagina de conta | Status do plano | Mostra "pending" durante outage |

### Evidencia da Investigacao (Squad Root Cause 2026-02-23)

| Finding | Agente | Descricao |
|---------|--------|-----------|
| ERROR-009 | QA | Subscription status engolido como "pending" durante outage |
| UX-ISSUE-021 | UX | Botao "Ver ultima busca" permanentemente desabilitado |

## Criterios de Aceite

### Subscription Status

- [x] AC1: Proxy `subscription-status/route.ts` usa `sanitizeProxyError()` — nao engole erros
- [x] AC2: Quando backend offline, retornar ultimo status conhecido (localStorage cache) com nota "Verificado ha X min"
- [x] AC3: Quando backend retorna erro, mostrar: "Nao foi possivel verificar seu plano. [Tentar novamente]"
- [x] AC4: NUNCA retornar "pending" como fallback silencioso

### Dead Buttons

- [x] AC5: Botao "Ver ultima busca" em `SourcesUnavailable.tsx` conectado a `localStorage` (ultima busca salva)
- [x] AC6: Se nao houver ultima busca, botao nao aparece (em vez de aparecer desabilitado)
- [x] AC7: Se houver ultima busca, botao carrega resultados do cache/localStorage

### Feedback Pos-Pagamento

- [x] AC8: Apos checkout Stripe, pagina mostra "Processando pagamento..." com spinner (nao "pending" estatico)
- [x] AC9: Polling do status a cada 5s por 60s apos checkout — quando `active`, mostrar confirmacao com confetti/toast

## Testes Obrigatorios

```bash
cd frontend && npm test -- --testPathPattern="subscription-status|SourcesUnavailable" --no-coverage
```

- [x] T1: Subscription proxy retorna erro real (nao "pending") quando backend offline
- [x] T2: Cache localStorage usado como fallback
- [x] T3: Botao "Ver ultima busca" funciona quando ha busca salva
- [x] T4: Botao escondido quando nao ha busca salva
- [x] T5: Polling pos-checkout funciona

## Arquivos Afetados

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `frontend/app/api/subscription-status/route.ts` | Ja usava sanitizeProxyError — verificado |
| `frontend/app/buscar/components/SourcesUnavailable.tsx` | Modificar — botao hidden em vez de disabled (AC6) |
| `frontend/app/buscar/page.tsx` | Modificar — wiring hasLastSearch + onLoadLastSearch (AC5, AC7) |
| `frontend/app/buscar/hooks/useSearch.ts` | Modificar — saveLastSearch apos busca (AC5) |
| `frontend/app/conta/page.tsx` | Modificar — error state + cache notice (AC2, AC3) |
| `frontend/app/planos/obrigado/page.tsx` | Modificar — polling 60s + toast (AC9) |
| `frontend/hooks/usePlan.ts` | Modificar — isFromCache + cachedAt (AC2) |
| `frontend/lib/lastSearchCache.ts` | Novo — utilidade cache ultima busca (AC5-AC7) |
| `frontend/__tests__/gtm-ux-004-subscription-dead-buttons.test.tsx` | Novo — testes T2-T5 |
| `frontend/__tests__/proxy-error-handler.test.ts` | Modificar — T1 (never pending) |
| `frontend/__tests__/buscar/empty-failure.test.tsx` | Modificar — AC6 (button hidden) |
| `frontend/__tests__/story-257b/ux-transparente.test.tsx` | Modificar — AC6 (button hidden) |

## Dependencias

| Tipo | Story | Motivo |
|------|-------|--------|
| Depende de | GTM-PROXY-001 | sanitizeProxyError() precisa existir |
| Paralela | GTM-UX-002 | Error states complementam |
