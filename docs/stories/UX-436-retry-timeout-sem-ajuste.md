# UX-436: Retry de timeout repete mesma busca sem ajuste

**Status:** Draft
**Prioridade:** P1 — Importante
**Origem:** UX Audit 2026-03-25 (I5)
**Sprint:** Próximo

## Contexto

Quando uma busca dá timeout, o botão "Tentar novamente" repete exatamente os mesmos parâmetros (mesmas 4 UFs). A probabilidade de falhar novamente no mesmo limite é alta, gerando frustração.

Esta story trata da **experiência de retry** — não da causa do timeout (endereçada em UX-430).

## Acceptance Criteria

- [ ] AC1: Ao exibir o botão "Tentar novamente" após timeout, mostrar quais UFs completaram antes do timeout (ex: "SP e PR tiveram resultados — SC e RS não responderam")
- [ ] AC2: Botão principal de retry: "Buscar apenas [UFs que completaram]" — pre-seleciona apenas as UFs bem-sucedidas
- [ ] AC3: Botão secundário: "Tentar com todas as UFs novamente" — repete a busca original (comportamento atual, agora como opção secundária)
- [ ] AC4: Se 2 tentativas consecutivas falharam com as mesmas 4+ UFs, sugerir automaticamente reduzir para as 2 UFs com maior volume histórico de editais do setor buscado
- [ ] AC5: Mensagem de timeout não contém "Tente com menos estados" como instrução — substituir por contexto acionável conforme AC1

## Escopo

**IN:** `frontend/app/buscar/hooks/useSearchRetry.ts` (lógica de retry com UFs parciais), `frontend/app/buscar/components/SearchErrorBanner.tsx` ou `PartialTimeoutBanner.tsx` (UI do retry adaptativo), `frontend/app/buscar/page.tsx` (estado de UFs completadas)
**OUT:** Mudanças no pipeline de timeout no backend (UX-430), mudanças no timeout chain (CRIT-082), dados de volume histórico por setor/UF (usar contagem simples dos resultados retornados, não endpoint externo)

## Complexidade

**S** (1–2 dias) — requer que o estado de "UFs completadas" seja acessível no momento do erro; `useSearchRetry.ts` já existe

## Dependências

- **UX-430** (recomendado antes): fix do timeout chain torna esta story mais efetiva — mas pode ser implementada independentemente
- **CRIT-082** (recomendado antes): com retry amplification resolvido, o fluxo de retry fica mais previsível

## Riscos

- **UFs completadas não persistidas:** Se o estado de progresso por UF é perdido quando o timeout ocorre, AC1 e AC2 não têm dados para trabalhar — verificar se `useUfProgress.ts` mantém estado acessível após timeout
- **AC4 — volume histórico:** Sugerir as "2 UFs com maior volume" requer alguma fonte de dados; usar os dados de progresso já retornados (`resultados_por_uf`) como proxy é suficiente

## Critério de Done

- Após timeout em SP/PR/RS/SC com SP e PR retornando resultados: botão "Buscar apenas SP e PR" aparece como opção principal
- Clicar no botão refaz a busca com apenas SP e PR pré-selecionados
- Texto do erro não contém "Tente com menos estados"
- `npm test` passa sem regressões

## Arquivos Prováveis

- `frontend/app/buscar/hooks/useSearchRetry.ts` — lógica de retry (já existe)
- `frontend/app/buscar/hooks/useUfProgress.ts` — progresso por UF (fonte de "quais completaram")
- `frontend/app/buscar/components/PartialTimeoutBanner.tsx` — UI de timeout com opções
- `frontend/app/buscar/page.tsx` — coordenação de estado entre hooks
