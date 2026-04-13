# SEO-470 — Panorama de contratos históricos universal em /blog/licitacoes/[setor]/[uf]

**Status:** Done  
**Type:** Feature  
**Prioridade:** Alta — causa raiz do thin content nas 405 páginas setor×UF  
**Depende de:** SEO-474 (ContractsPanoramaBlock), SEO-475 (backend endpoint enriquecido)  
**Bloqueia:** SEO-471 (sitemap precisa de noindex coerente)

## Problema

As páginas `/blog/licitacoes/[setor]/[uf]` usam `pncp_supplier_contracts` (2M+ linhas) **apenas como fallback de último recurso** quando `total_editais === 0`. Resultado: páginas com 1–30 bids abertos não mostram o panorama histórico de contratos, perdendo a oportunidade de demonstrar autoridade de mercado.

Além disso, o critério de noindex é `total_editais < 5` — ignorando completamente se há centenas de contratos históricos naquela combinação. Combos como "TI no Acre" podem ter 2 editais abertos mas 180 contratos firmados nos últimos 12 meses. A página está sendo noindex apesar de ter conteúdo valioso.

**Impacto estimado:** ~200–280 das 405 combinações setor×UF seriam recuperadas para indexação.

## Solução

Transformar o bloco de contratos de fallback em **seção permanente de todas as páginas**, posicionado abaixo dos editais live. O panorama histórico complementa (não substitui) os dados de editais.

**Layout resultante:**
```
[Hero + KPIs de editais live — sem mudança]
[Lista de editais abertos — sem mudança]
[━━━ Panorama Histórico de Contratos ━━━]  ← SEMPRE presente quando total_contracts > 0
  - Total gasto nos últimos 12 meses
  - Top 5 órgãos compradores (links /orgaos/{cnpj})
  - Top 5 fornecedores (links /fornecedores/{cnpj})
  - Gráfico de tendência mensal (12 meses)
  - Ticket médio e n° de contratos
[FAQ com dados combinados]
[CTA]
```

**Lógica de noindex:** `robots.index=false` apenas quando `bids === 0 AND contracts === 0`.

## Acceptance Criteria

- [x] AC1: `fetchContratosSetorUfStats` é chamado em **todas** as páginas setor×UF, não só quando `total_editais === 0`
- [x] AC2: Chamadas a `fetchSectorUfBlogStats` (bids) e `fetchContratosSetorUfStats` (contratos) são paralelas via `Promise.all` — sem aumento de latência
- [x] AC3: `ContractsPanoramaBlock` (SEO-474) renderiza abaixo da seção de editais quando `total_contracts > 0`
- [x] AC4: Quando `total_contracts === 0`: bloco não renderiza (sem seção vazia ou placeholder)
- [x] AC5: `robots.index=false` apenas quando `bids === 0 AND contracts === 0`; `robots.index=true` se qualquer um dos dois for > 0
- [x] AC6: Metadata description menciona contratos quando disponíveis: "X editais abertos — R$ Y movimentados em {N} contratos históricos"
- [x] AC7: `alternates.canonical` presente em **todos** os branches (incluindo noindex) — autocanonical self-referencial
- [x] AC8: FAQ (`generateLicitacoesFAQsWithFallback`) usa dados de contratos mesmo quando há bids disponíveis
- [x] AC9: ISR `revalidate = 86400` (24h) mantido — nenhuma mudança de frequência de rebuild
- [x] AC10: `npx tsc --noEmit` sem erros
- [x] AC11: Testes existentes de `blog/licitacoes/[setor]/[uf]` passam sem regressão

## Escopo

**IN:**
- `frontend/app/blog/licitacoes/[setor]/[uf]/page.tsx` — lógica de fetch, noindex e layout
- `frontend/lib/contracts-fallback.ts` — sem mudanças estruturais, apenas verificar que `fetchContratosSetorUfStats` retorna os campos necessários para o componente

**OUT:**
- Criação do componente `ContractsPanoramaBlock` → SEO-474
- Enriquecimento do backend endpoint → SEO-475
- Mudanças no sitemap → SEO-471
- Outras rotas (contratos, cidades) → SEO-472, SEO-473

## Dependências

| Story | Tipo | Razão |
|-------|------|-------|
| SEO-474 | Pré-requisito | Componente `ContractsPanoramaBlock` deve existir antes de importar |
| SEO-475 | Pré-requisito | Backend endpoint deve retornar `n_unique_orgaos`, `sample_contracts` |
| SEO-471 | Bloqueada por esta | Sitemap deve incluir combos com `contracts ≥ 1` |

## Riscos

- **Performance:** Fetch duplo por página pode aumentar tempo de ISR rebuild. Mitigação: `Promise.all` + cache 6h no backend endpoint
- **Dados ausentes:** `pncp_supplier_contracts` pode não ter dados para setores de nicho/UFs pequenas. Mitigação: renderização condicional (AC4)
- **Regressão FAQ:** `generateLicitacoesFAQsWithFallback` pode gerar FAQs inconsistentes quando há tanto bids quanto contratos. Verificar manualmente amostra de 5 combos

## Complexidade

**M** (3-5 dias) — mudança de lógica consolidada em um arquivo, dependente de componente externo

## Critério de Done

- Página `/blog/licitacoes/tecnologia-da-informacao/sp` mostra panorama de contratos abaixo dos editais live
- Página `/blog/licitacoes/tecnologia-da-informacao/ac` (UF pequena) mostra panorama de contratos sem bids ativos (apenas contratos) e está `robots.index=true`
- Build Next.js completa sem erros
- Nenhum teste existente quebrado

## File List

- [x] `docs/stories/SEO-470-panorama-contratos-universal-licitacoes-setor-uf.md` (esta story)
- [x] `frontend/app/blog/licitacoes/[setor]/[uf]/page.tsx`
- [x] `frontend/lib/contracts-fallback.ts` (somente leitura — interface verificada, nenhuma mudança necessária)
- [x] `frontend/__tests__/mkt-003-licitacoes.test.tsx` (novos testes SEO-470 adicionados)
- [x] `frontend/__tests__/app/licitacoes-noindex.test.tsx` (corrigido assert STORY-450 pré-existente)
