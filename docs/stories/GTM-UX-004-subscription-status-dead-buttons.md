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

- [ ] AC1: Proxy `subscription-status/route.ts` usa `sanitizeProxyError()` — nao engole erros
- [ ] AC2: Quando backend offline, retornar ultimo status conhecido (localStorage cache) com nota "Verificado ha X min"
- [ ] AC3: Quando backend retorna erro, mostrar: "Nao foi possivel verificar seu plano. [Tentar novamente]"
- [ ] AC4: NUNCA retornar "pending" como fallback silencioso

### Dead Buttons

- [ ] AC5: Botao "Ver ultima busca" em `SourcesUnavailable.tsx` conectado a `localStorage` (ultima busca salva)
- [ ] AC6: Se nao houver ultima busca, botao nao aparece (em vez de aparecer desabilitado)
- [ ] AC7: Se houver ultima busca, botao carrega resultados do cache/localStorage

### Feedback Pos-Pagamento

- [ ] AC8: Apos checkout Stripe, pagina mostra "Processando pagamento..." com spinner (nao "pending" estatico)
- [ ] AC9: Polling do status a cada 5s por 60s apos checkout — quando `active`, mostrar confirmacao com confetti/toast

## Testes Obrigatorios

```bash
cd frontend && npm test -- --testPathPattern="subscription-status|SourcesUnavailable" --no-coverage
```

- [ ] T1: Subscription proxy retorna erro real (nao "pending") quando backend offline
- [ ] T2: Cache localStorage usado como fallback
- [ ] T3: Botao "Ver ultima busca" funciona quando ha busca salva
- [ ] T4: Botao escondido quando nao ha busca salva
- [ ] T5: Polling pos-checkout funciona

## Arquivos Afetados

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `frontend/app/api/subscription-status/route.ts` | Modificar — sanitizar, nao engolir erros |
| `frontend/app/buscar/components/SourcesUnavailable.tsx` | Modificar — wiring botao |
| `frontend/app/conta/page.tsx` | Modificar — error state para status |
| `frontend/app/planos/obrigado/page.tsx` | Modificar — polling pos-checkout |

## Dependencias

| Tipo | Story | Motivo |
|------|-------|--------|
| Depende de | GTM-PROXY-001 | sanitizeProxyError() precisa existir |
| Paralela | GTM-UX-002 | Error states complementam |
