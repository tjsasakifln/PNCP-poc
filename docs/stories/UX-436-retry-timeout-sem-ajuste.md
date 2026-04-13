# UX-436: Retry de timeout repete mesma busca sem ajuste

**Status:** Done
**Prioridade:** P1 — Importante
**Origem:** UX Audit 2026-03-25 (I5)
**Sprint:** Próximo

## Contexto

Quando uma busca dá timeout, o botão "Tentar novamente" repete exatamente os mesmos parâmetros (mesmas 4 UFs). A probabilidade de falhar novamente no mesmo limite é alta, gerando frustração.

Esta story trata da **experiência de retry** — não da causa do timeout (endereçada em UX-430).

## Acceptance Criteria

- [x] AC1: Ao exibir o botão "Tentar novamente" após timeout, mostrar quais UFs completaram antes do timeout (ex: "SP e PR tiveram resultados — SC e RS não responderam")
- [x] AC2: Botão principal de retry: "Buscar apenas [UFs que completaram]" — pre-seleciona apenas as UFs bem-sucedidas
- [x] AC3: Botão secundário: "Tentar com todas as UFs novamente" — repete a busca original (comportamento atual, agora como opção secundária)
- [x] AC4: Se 2 tentativas consecutivas falharam com as mesmas 4+ UFs, sugerir automaticamente reduzir para as 2 UFs com maior volume histórico de editais do setor buscado
- [x] AC5: Mensagem de timeout não contém "Tente com menos estados" como instrução — substituir por contexto acionável conforme AC1

## Escopo

**IN:** `frontend/app/buscar/hooks/useSearch.ts` (snapshot de ufStatuses), `frontend/app/buscar/components/SearchStateManager.tsx` (UI do retry adaptativo), `frontend/app/buscar/components/SearchResults.tsx`, `frontend/app/buscar/types/search-results.ts`, `frontend/app/buscar/hooks/useSearchComputedProps.ts`
**OUT:** Mudanças no pipeline de timeout no backend (UX-430), mudanças no timeout chain (CRIT-082), dados de volume histórico por setor/UF (usar contagem simples dos resultados retornados, não endpoint externo)

## Complexidade

**S** (1–2 dias) — requer que o estado de "UFs completadas" seja acessível no momento do erro; `useSearchRetry.ts` já existe

## Dependências

- **UX-430** (recomendado antes): fix do timeout chain torna esta story mais efetiva — mas pode ser implementada independentemente
- **CRIT-082** (recomendado antes): com retry amplification resolvido, o fluxo de retry fica mais previsível

## Riscos

- **UFs completadas não persistidas:** ✅ Resolvido — `ufStatusesSnapshot` captura estado de ufStatuses antes do SSE hook limpar o Map no timeout.
- **AC4 — volume histórico:** ✅ Resolvido — usa `resultados_por_uf` (campo `count` no ufStatuses) como proxy.

## Critério de Done

- [x] Após timeout em SP/PR/RS/SC com SP e PR retornando resultados: botão "Buscar apenas SP e PR" aparece como opção principal
- [x] Clicar no botão refaz a busca com apenas SP e PR pré-selecionados
- [x] Texto do erro não contém "Tente com menos estados"
- [x] `npm test` passa sem regressões

## Arquivos Modificados

- `frontend/app/buscar/hooks/useSearch.ts` — captura snapshot de ufStatuses via useEffect antes do SSE limpar
- `frontend/app/buscar/types/search-results.ts` — adiciona `ufStatusesSnapshot` ao `SearchLoadingState`
- `frontend/app/buscar/hooks/useSearchComputedProps.ts` — passa `ufStatusesSnapshot` no props object
- `frontend/app/buscar/components/SearchResults.tsx` — destructura e passa `ufStatusesSnapshot` ao `SearchStateManager`
- `frontend/app/buscar/components/SearchStateManager.tsx` — implementação completa AC1-AC5 com `AdaptiveRetryPanel`
- `frontend/__tests__/components/UX436-timeout-retry.test.tsx` — 19 testes cobrindo todos os ACs

## Notas de Implementação

**Problema crítico de timing:** `ufStatuses` é zerado para `new Map()` quando `enabled` vai para `false` no `useSearchSSE` (ocorre quando `loading=false` após timeout). A solução usa dois `useEffect` em `useSearch.ts`:
1. Captura snapshot sempre que `ufStatuses.size > 0` → mantém último estado não-vazio
2. Limpa snapshot quando `execution.loading` vai para `true` → nova busca descarta snapshot anterior

**AC4 proxy:** `retryExhausted=true` (auto-retry esgotou 2 tentativas) serve como proxy para "2 tentativas consecutivas falharam".

## Change Log

| Data | Quem | O quê |
|------|------|-------|
| 2026-04-13 | @dev | Implementação completa AC1-AC5, 19 testes |
