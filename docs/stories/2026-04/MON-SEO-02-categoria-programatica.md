# MON-SEO-02: Páginas `/categoria/[slug]` Programáticas (5k+ Páginas)

**Priority:** P1
**Effort:** L (5-6 dias)
**Squad:** @dev + @devops + @ux
**Status:** Draft
**Epic:** [EPIC-MON-SEO-2026-04](EPIC-MON-SEO-2026-04.md)
**Sprint:** Wave 3 (depende MON-SCH-02 + MON-REP-04)

---

## Contexto

**Pergunta-mãe do SEO:** "Quanto o governo paga por [produto/serviço]?"

Hoje não existe página dedicada a essa query. Após MON-SCH-02 (CATMAT/CATSER + catálogo), podemos gerar **5.000+ páginas programáticas** automaticamente — uma por código CATMAT/CATSER com ≥ 20 contratos históricos.

Cada página é **alta intenção**: orçamentista, pregoeiro, fornecedor avaliando mercado. CTA para MON-REP-04 (Relatório Preço Referência R$ 97-297).

---

## Acceptance Criteria

### AC1: Rota dinâmica `/categoria/[slug]`

- [ ] `frontend/app/categoria/[slug]/page.tsx`:
  - `generateStaticParams()` gera slugs para top 5k CATMAT/CATSER por volume
  - ISR 24h
  - Fallback: on-demand generation para slugs novos
  - SSR via RPC `benchmark_by_catmat` (MON-SCH-02) + listagem top 20 contratos + top 10 fornecedores

### AC2: Conteúdo da página

- [ ] Hero: "Quanto o governo paga por {label}?" (H1)
- [ ] Box destacado: mediana nacional (R$), amostra (N contratos)
- [ ] Seção "Distribuição de preços" — histograma + percentis
- [ ] Seção "Variação por UF" — tabela sortable com mediana por UF
- [ ] Seção "Top fornecedores" — 10 players + share
- [ ] Seção "Últimos contratos" — tabela paginada top 20 por recência
- [ ] CTA persistente: "Quer análise completa? Compre o Relatório de Preço Referência (R$ 97)"
- [ ] Sidebar: "Categorias relacionadas" (linkando outros slugs)

### AC3: JSON-LD `Dataset`

```json
{
  "@context": "https://schema.org",
  "@type": "Dataset",
  "name": "Preços Públicos — {label}",
  "description": "...",
  "creator": {"@type": "Organization", "name": "SmartLic"},
  "distribution": {"@type": "DataDownload", "contentUrl": "https://smartlic.tech/api/..."},
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "measurementTechnique": "Aggregation from PNCP public data"
}
```

### AC4: SEO metadata

- [ ] Title: `"{label} — Preços Pagos pelo Governo | SmartLic"` (max 60)
- [ ] Description: `"Mediana nacional R$ {mediana} para {label}. {n_contratos} contratos no PNCP. Distribuição por UF, top fornecedores. Dados atualizados."` (max 160)
- [ ] og:image dinâmico: card com mediana + label

### AC5: Sitemap dedicado

- [ ] `frontend/app/sitemap/categorias-[n].ts` shardado por primeira letra do slug (26 shards máximo)
- [ ] Cada shard lista URLs `/categoria/{slug}` com `lastmod` do `updated_at` do catálogo
- [ ] Registrado em `sitemap_index.xml` (MON-SEO-04)

### AC6: Thin content gate

- [ ] Página com `sample_size < 10` contratos → noindex + conteúdo degradado "Dados insuficientes. Considere outra categoria."
- [ ] Página com `sample_size >= 10 AND < 50` → index mas label "Amostra pequena — use com cautela"

### AC7: CTAs múltiplos

- [ ] Sticky CTA bottom em mobile
- [ ] Inline CTA após histograma
- [ ] Sidebar CTA com 3 variantes (Relatório R$ 97 / Monitor R$ 197 / API R$ 1/query)

### AC8: Testes

- [ ] Integration: 10 slugs random rendereizam com sucesso
- [ ] Lighthouse: 90+ performance em slug top 100
- [ ] Thin content gate: slug com 5 contratos retorna noindex
- [ ] JSON-LD valida em Rich Results Test

---

## Scope

**IN:**
- Rota dinâmica + SSR
- Conteúdo completo (6 seções)
- JSON-LD Dataset
- SEO metadata + og:image
- Sitemap shardado
- Thin content gate
- CTAs múltiplos
- Testes

**OUT:**
- Filtros interativos (UF, período) no frontend — usar query params, não persistência
- Comparador multi-categoria — v2
- Export CSV direto da página — encaminha para MON-API-04

---

## Dependências

- **MON-SCH-02 (CATMAT/CATSER + catálogo)** — bloqueador absoluto
- MON-REP-04 (CTA principal)
- MON-SEO-04 (sitemap index)

---

## Riscos

- **Google thin content penalty (AC6 mitiga):** cada página precisa ter ≥ 10 contratos únicos; gates rígidos
- **5000 páginas geradas ao mesmo tempo sobrecarregam build:** ISR on-demand para a cauda (usar `dynamicParams = true`)
- **SEO canibalização com `/relatorios/preco-referencia`:** `/categoria/*` é informacional (SEO), `/relatorios/preco-referencia` é transacional (conversão); estabelecer linking entre elas

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `frontend/app/categoria/[slug]/page.tsx` (novo)
- `frontend/app/categoria/[slug]/loading.tsx` (novo)
- `frontend/app/api/og/categoria/route.tsx` (novo — og:image dinâmico)
- `frontend/app/sitemap/categorias-[n].ts` (novo)
- `backend/routes/categoria.py` (novo — endpoint data aggregado)
- `frontend/__tests__/categoria-page.test.tsx` (novo)
- `frontend/e2e-tests/categoria-seo.spec.ts` (novo)

---

## Definition of Done

- [ ] 5.000+ slugs gerados e acessíveis
- [ ] Sitemap shardado registrado no Search Console
- [ ] Google Rich Results Test valida JSON-LD em 5 samples
- [ ] Coverage de CATMAT no catálogo >= 80% (dep MON-SCH-02)
- [ ] Lighthouse 85+ em top slugs
- [ ] A/B test CTA placements ativo

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — 5k+ páginas programáticas, resposta à query de alto volume de busca |
