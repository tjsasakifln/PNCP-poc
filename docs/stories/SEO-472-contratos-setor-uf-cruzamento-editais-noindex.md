# SEO-472 — Contratos/[setor]/[uf]: cruzamento com editais ativos e noindex relaxado

**Status:** Ready  
**Type:** Feature  
**Prioridade:** Média — 405 páginas de contratos com thin content potencial  
**Depende de:** SEO-474 (ContractsPanoramaBlock), SEO-475 (backend enriquecido)  
**Bloqueia:** —

## Problema

As páginas `/contratos/[setor]/[uf]` mostram apenas dados de contratos históricos (`pncp_supplier_contracts`) e aplicam `robots.index=false` quando `total_contracts < 5`. O problema é duplo:

1. **Dado subutilizado:** Quando há editais ativos para aquele setor/UF, a página não os mostra — perdendo a oportunidade de conectar histórico de contratos com oportunidades atuais
2. **Noindex excessivo:** Um combo com 3 contratos e 8 editais ativos recebe noindex porque só se conta os contratos, ignorando os bids

**Resultado:** Páginas que poderiam ser ricas em dados live + histórico são tratadas como thin content.

## Solução

Adicionar fetch de editais ativos (`fetchSectorUfBlogStats`) em paralelo com o fetch de contratos existente. A decisão de noindex passa a considerar os dois datasets.

**Layout resultante:**
```
[Hero com dados de contratos — posição principal mantida]
[Tabela de top órgãos compradores e fornecedores]
[━━━ Editais Abertos Agora ━━━]  ← NOVO — só aparece quando total_editais > 0
  - N editais nos últimos 30 dias
  - Faixa de valores
  - Link "Ver todos no SmartLic" (CTA de conversão)
[FAQ combinado contratos + editais]
```

## Acceptance Criteria

- [ ] AC1: `fetchSectorUfBlogStats` chamado em paralelo com `fetchContratosStats` via `Promise.all`
- [ ] AC2: Seção "Editais Abertos" renderiza quando `total_editais > 0`, posicionada abaixo dos dados de contratos
- [ ] AC3: Seção "Editais Abertos" inclui: contagem, faixa de valores, e link CTA para busca no app
- [ ] AC4: `robots.index=false` apenas quando `total_contracts === 0 AND total_editais === 0`
- [ ] AC5: `robots.index=true` quando `contracts ≥ 1 OR editais ≥ 1`
- [ ] AC6: `alternates.canonical` presente em todos os branches (incluindo noindex) — autocanonical
- [ ] AC7: Metadata description atualizada: menciona editais quando disponíveis ("X contratos firmados — Y editais abertos agora")
- [ ] AC8: Fallback graceful: se `fetchSectorUfBlogStats` falhar, página renderiza apenas dados de contratos (sem erro 500)
- [ ] AC9: Todo texto gerado dinamicamente usa português correto, com acentuação perfeita e construção de frases naturais — nenhum vestígio de formatação markdown visível ao usuário
- [ ] AC10: `npx tsc --noEmit` sem erros
- [ ] AC11: ISR `revalidate = 86400` mantido

## Escopo

**IN:**
- `frontend/app/contratos/[setor]/[uf]/page.tsx` — fetch paralelo, seção de editais, lógica noindex

**OUT:**
- Mudanças no componente de contratos principal — fora do escopo
- Mudanças no endpoint backend de contratos — fora do escopo (usa endpoint existente)
- Criação do `ContractsPanoramaBlock` — SEO-474

## Dependências

| Story | Tipo | Razão |
|-------|------|-------|
| SEO-474 | Pré-requisito | `ContractsPanoramaBlock` deve existir para ser usado na seção de contratos da página |
| SEO-475 | Pré-requisito | Backend enriquecido com `sample_contracts` e `n_unique_orgaos` |

## Riscos

- **Latência ISR:** Segundo fetch em paralelo não deve impactar rebuild (ambos têm cache de 6h no backend)
- **Contexto de setor:** `fetchSectorUfBlogStats` usa slug do setor — garantir que a conversão slug→setor_id é consistente entre os dois endpoints

## Complexidade

**S** (1–2 dias) — mudança localizada em um arquivo

## Critério de Done

- `/contratos/tecnologia-da-informacao/ac` (UF pequena) com 3 contratos e 5 editais ativos: `robots.index=true`, seção de editais visível
- `/contratos/saude/sp` com 150 contratos e 20 editais: ambos os blocos presentes
- Nenhum erro no console do browser
- Build completa sem erros TypeScript

## File List

- [ ] `docs/stories/SEO-472-contratos-setor-uf-cruzamento-editais-noindex.md` (esta story)
- [ ] `frontend/app/contratos/[setor]/[uf]/page.tsx`
