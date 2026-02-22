# TFIX-007: Atualizar testes source-indicators para UI atual

**Status:** Pending
**Prioridade:** Média
**Estimativa:** 1h
**Arquivos afetados:** 1 test file

## Problema

4 testes em `source-indicators.test.tsx` falham porque buscam textos e elementos que não existem na UI atual.

## Causa Raiz

Os testes foram escritos baseados em specs (GTM-FIX-011 AC32) mas a implementação final tem textos diferentes ou funcionalidades renderizadas de forma diferente:

### Divergências identificadas:

| Teste espera | Realidade |
|---|---|
| `"(dados de múltiplas fontes)"` no summary | Texto não existe na UI — SearchResults não renderiza esse texto |
| Tooltip com "per-source record counts" on hover | Tooltip não implementado ou texto diferente |
| `"Algumas fontes não responderam"` (partial failure) | Mensagem/texto diferente ou não renderizado nesse contexto |
| Amber/warning styling para partial failure | Styling/classes podem ter mudado |

O componente `SearchResults` em `page.tsx` foi reestruturado (UX-340, UX-341) e os indicadores de fontes foram movidos para `OperationalStateBanner` em vez de ficarem no summary.

## Testes que serão corrigidos

- `source-indicators.test.tsx`: 4 falhas
  - `shows '(dados de múltiplas fontes)' when multiple sources`
  - `shows tooltip with per-source record counts on hover`
  - `shows partial failure message when is_partial=true`
  - `uses amber/warning styling for partial failure message`

## Critérios de Aceitação

- [ ] AC1: Identificar onde indicadores de fontes são renderizados atualmente (OperationalStateBanner? SearchResults?)
- [ ] AC2: Atualizar testes para refletir a UI real
- [ ] AC3: 14/14 testes passam
- [ ] AC4: Se feature foi removida, remover/skip testes correspondentes

## Solução

1. Mapear onde `sources_used`, `source_stats`, `is_partial` são consumidos na UI atual
2. Atualizar seletores e textos esperados
3. Se funcionalidade foi migrada para OperationalStateBanner, mover testes para lá

## Arquivos

- `frontend/__tests__/source-indicators.test.tsx` — atualizar expectativas
- `frontend/app/buscar/page.tsx` — referência para textos atuais
