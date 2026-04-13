# SEO-473 — Páginas de cidade: panorama de contratos universal e noindex baseado em dados combinados

**Status:** Ready  
**Type:** Feature  
**Prioridade:** Média — ~100 páginas de cidade com thin content potencial  
**Depende de:** SEO-474 (ContractsPanoramaBlock), SEO-475 (backend enriquecido)  
**Bloqueia:** —

## Problema

As páginas `/blog/licitacoes/cidade/[cidade]` têm `fetchContratosCidadeStats` importado em `lib/contracts-fallback.ts`, mas o componente `HistoricalContractsFallback` é chamado de forma inconsistente — não cobre todos os cenários em que a cidade tem contratos históricos mas poucos editais ativos.

Adicionalmente, não há threshold de noindex explícito: todas as cidades são indexadas mesmo quando a página está completamente vazia (0 bids, 0 contratos), gerando thin content real no GSC.

## Solução

Aplicar o mesmo padrão de SEO-470 às páginas de cidade:
- Fetch paralelo de bids + contratos
- `ContractsPanoramaBlock` sempre que `total_contracts > 0`
- `robots.index=false` apenas quando ambos são zero

## Acceptance Criteria

- [ ] AC1: `fetchCidadeStats` (bids) e `fetchContratosCidadeStats` (contratos) são chamados em paralelo via `Promise.all`
- [ ] AC2: `ContractsPanoramaBlock` com `variant="cidade"` renderiza abaixo dos editais quando `total_contracts > 0`
- [ ] AC3: Quando `total_contracts === 0`: bloco não renderiza (sem seção vazia ou texto genérico)
- [ ] AC4: `robots.index=false` apenas quando `bids === 0 AND contracts === 0`
- [ ] AC5: `robots.index=true` quando qualquer um dos datasets tem dados
- [ ] AC6: `alternates.canonical` presente em todos os branches
- [ ] AC7: Metadata description atualizada quando há contratos: inclui total movimentado ou número de contratos
- [ ] AC8: Fallback graceful: se `fetchContratosCidadeStats` falhar, página funciona com dados de bids apenas
- [ ] AC9: Todo texto gerado tem acentuação correta, linguagem natural, sem resíduo de markdown — passa em revisão editorial humana
- [ ] AC10: `npx tsc --noEmit` sem erros
- [ ] AC11: ISR `revalidate = 86400` mantido

## Escopo

**IN:**
- `frontend/app/blog/licitacoes/cidade/[cidade]/page.tsx`

**OUT:**
- `frontend/app/blog/licitacoes/cidade/[cidade]/[setor]/page.tsx` — fora do escopo desta story (abordado separadamente se necessário)
- Mudanças no backend endpoint de cidade — usa endpoint existente `/blog/stats/contratos/cidade/{cidade}`

## Dependências

| Story | Tipo | Razão |
|-------|------|-------|
| SEO-474 | Pré-requisito | `ContractsPanoramaBlock` com variant="cidade" |
| SEO-475 | Recomendado | Endpoint de contratos por cidade também pode precisar de enriquecimento |

## Riscos

- **Endpoint de contratos por cidade:** `/blog/stats/contratos/cidade/{cidade}` — verificar se retorna campos suficientes para o `ContractsPanoramaBlock`
- **Cidades sem dados de contratos:** Esperado para cidades menores; renderização condicional (AC3) mitiga

## Complexidade

**S** (1 dia) — mesma lógica de SEO-470 aplicada a página diferente

## Critério de Done

- `/blog/licitacoes/cidade/sao-paulo` mostra panorama de contratos abaixo dos editais
- `/blog/licitacoes/cidade/cruzeiro-do-sul` (cidade pequena, AC) com 0 bids e 0 contratos: `robots.index=false`
- `/blog/licitacoes/cidade/fortaleza` com contratos mas poucos bids: `robots.index=true`, bloco visível
- Build sem erros TypeScript

## File List

- [ ] `docs/stories/SEO-473-cidades-panorama-contratos-universal.md` (esta story)
- [ ] `frontend/app/blog/licitacoes/cidade/[cidade]/page.tsx`
