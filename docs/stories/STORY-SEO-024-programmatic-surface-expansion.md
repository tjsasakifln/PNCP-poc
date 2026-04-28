# STORY-SEO-024: Programmatic surface expansion (lever principal de 3x tráfego)

## Status

Approved

## Story

**As a** time de growth com baseline 9.9k impressões em queries B2G long-tail,
**I want** 2-3 novos templates programmatic cobrindo gaps GSC (queries com >50 impressões e zero ranking),
**so that** ganhemos ≥1k novas URLs indexáveis com dados reais — multiplicador maior para 3x tráfego (advisor: este é o lever principal, não consertar páginas existentes).

## Acceptance Criteria

1. Análise GSC entregue: lista exportada de keywords com >50 impressões 28d e posição >20 (oportunidades não cobertas), com mapping para entidades de domínio (município/setor/CNAE/região).
2. Decisão de templates: ≥3 novos templates programmatic escolhidos baseado na análise. Candidatos sugeridos no plano: `/{municipio}/{setor}/`, `/{cnae}/{regiao}/`, `/comparacao/{orgao1}-vs-{orgao2}/`. Decisão final via @analyst com data.
3. ADR registrado em `docs/adr/` justificando escolha de templates (rejected alternatives + rationale).
4. Cada novo template implementado com: `generateStaticParams` populando ≥333 URLs/template (≥1k total), `generateMetadata` apropriado, JSON-LD relevante (BreadcrumbList + entity schema), thin-content gating (reusa STORY-SEO-023 pattern), revalidate apropriado.
5. Sitemap (`frontend/app/sitemap.ts`) inclui novas rotas; sitemap-N.xml apropriado tem ≥1k novas `<loc>` entries.
6. GSC indexa ≥30% das novas URLs em 21d pós-deploy (medido via Coverage > Indexed).
7. Backend RPCs/queries necessárias têm índices Supabase apropriados (validação @data-engineer); p95 build-time `generateStaticParams` <60s por template.
8. Conteúdo das páginas é real (não Lorem) e tem valor SEO: ≥300 palavras úteis por página, dados reais de Supabase, internal links (relacionados/breadcrumb).

## Tasks / Subtasks

- [ ] Task 1 — Análise GSC (AC: 1, 2)
  - [ ] @analyst exporta GSC Performance > Queries últimos 28d
  - [ ] Filtra impressões >50 + posição >20
  - [ ] Mapeia clusters → entidades de domínio
  - [ ] Recomenda 3 templates com volume estimado
- [ ] Task 2 — ADR (AC: 3)
  - [ ] @architect escreve ADR `docs/adr/NNN-programmatic-surface-expansion.md`
  - [ ] Inclui: alternatives considered, rejection reasons, expected impact
- [ ] Task 3 — Backend prep (AC: 7)
  - [ ] @data-engineer cria/valida RPCs Supabase para cada template
  - [ ] Índices revisados (EXPLAIN ANALYZE em queries de listagem)
- [ ] Task 4 — Implementação templates (AC: 4)
  - [ ] @ux-design-expert produz layout base reusável
  - [ ] @dev implementa cada template em `frontend/app/{template}/[slug]/page.tsx`
  - [ ] Reuso do `<EmptyEntityFallback />` da STORY-SEO-023
- [ ] Task 5 — Sitemap integration (AC: 5)
  - [ ] Adicionar nova RPC ao `frontend/app/sitemap.ts` ID router
  - [ ] Sitemap split (próximo ID após o 4 atual) — TBD em base na contagem
- [ ] Task 6 — Conteúdo real (AC: 8)
  - [ ] Cada template tem ≥300 palavras úteis (pode ser dinâmico — stats, comparativos, histórico)
  - [ ] Internal links bidirecionais
- [ ] Task 7 — GSC monitoring (AC: 6)
  - [ ] Submit sitemap atualizado no GSC
  - [ ] Re-medição cobertura em 21d

## Dev Notes

**Plano:** Wave 2, story 6 — **lever maior** (advisor flagged: "consertar páginas existentes não escala 3x; mais URLs indexadas escala").

**Audit evidence:**
- Audit Agent 1 confirmou rotas vivas: `/cnpj/{cnpj}`, `/fornecedores/{cnpj}`, `/municipios/{slug}`, `/orgaos/{slug}`, `/contratos/orgao/{cnpj}`, `/blog/licitacoes/{setor}/{uf}`, `/alertas-publicos/{setor}/{uf}` — surface programmatic já existe, mas long-tail não totalmente coberta.
- GSC baseline (memória `reference_smartlic_baseline_2026_04_24.md`): 9.9k impressões com posição 7.1 — espaço grande para queries onde nem aparecemos.

**Cuidados (advisor + diretriz do usuário 2026-04-26):**
- NÃO criar templates sem análise GSC primeiro — risco de Lorem programmatic (Google penalty)
- **Reusa enrichment pattern de SEO-023 obrigatório**: cada nova URL tem conteúdo real (identificação + resumo de dados verificados + bloco educacional + relacionados), nunca depende de volume momentâneo de licitações
- **Proibido**: `noindex` condicional, `notFound()` por dados vazios, página com <300 palavras úteis. Slug estruturalmente inválido segue 404.
- @data-engineer valida queries — Supabase free tier tem connection limits

**Files mapeados:**
- `frontend/app/{novo-template-1}/[slug]/page.tsx` (criar)
- `frontend/app/{novo-template-2}/[slug]/page.tsx` (criar)
- `frontend/app/{novo-template-3}/[slug]/page.tsx` (criar)
- `frontend/app/sitemap.ts` (extend ID router)
- `backend/routes/sitemap*.py` ou Supabase RPC (criar/validar)
- `docs/adr/NNN-programmatic-surface-expansion.md` (criar)

### Testing

- Unit: `generateStaticParams` retorna ≥333 entries em fixtures
- Integration: Playwright crawl 20 URLs random de cada template + valida 200 + JSON-LD
- E2E: Lighthouse SEO score ≥90 em 5 amostras

## Dependencies

- **Bloqueado por:** STORY-SEO-020 (sitemap funcionando), STORY-SEO-023 (thin-content gating reusável)
- **Bloqueia:** future stories de growth orgânico que dependem de tráfego volume

## Owners

- Primary: @analyst (análise GSC), @architect (ADR), @dev (implementação)
- Backend: @data-engineer (RPCs + índices)
- Design: @ux-design-expert (layout)
- Quality: @qa

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-26 | 0.1 | Initial draft via /sm — lever principal flagged by advisor | @sm (River) |
