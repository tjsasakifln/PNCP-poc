# Story SEO-008: 3 Pillar Pages para Topical Authority

**Epic:** EPIC-SEO-2026-04
**Priority:** 🟠 P1
**Story Points:** 13 SP (1 sprint)
**Owner:** @dev + @ux-design-expert
**Status:** Ready
**Audit Ref:** Audit 4.3

---

## Problem

`frontend/lib/blog.ts` define 3 clusters (Empresas B2G, Consultorias, Guias) mas **não há hub pages visuais explícitas**. Posts são estrutura "atômica" — cada um vive sozinho, sem topical hub.

**Impacto:**
- Google vê site como "80 posts soltos" vs "site com autoridade em licitações"
- Usuário buscando "o que é pregão eletrônico" cai direto em um post, sem hub que mostre todos os temas cobertos
- Perda de link equity interno (spokes não linkam para pillar; pillar não linka para spokes)
- Sem entrypoints de long-tail de alto volume ("guia completo licitações", "tudo sobre Lei 14.133")

---

## Acceptance Criteria

- [ ] **AC1** — Criar 3 pillar pages em rota `/guia/[slug]`:
  - `/guia/licitacoes` — Guia Completo de Licitações Públicas no Brasil
  - `/guia/lei-14133` — Tudo Sobre a Lei 14.133/2021
  - `/guia/pncp` — Portal Nacional de Contratações Públicas: Guia Completo

- [ ] **AC2** — Cada pillar page tem:
  - **Word count**: 3.000-5.000 palavras
  - **Structure**: H1 (1) + H2 (6-10) + H3 (15-25) + parágrafos densos
  - **TOC sticky**: navegação lateral desktop, collapse mobile (reuso do componente a ser criado em Audit 4.2 ou criar junto aqui)
  - **Answer-first intro** (STORY-SEO-004 pattern): primeiro parágrafo responde a query principal diretamente
  - **CTA inline**: "Experimente SmartLic grátis por 14 dias"
  - **≥10 internal links** para posts spokes existentes em cada pillar
  - **≥5 outbound links** para fontes autoritativas (gov.br, tcu.gov.br, planalto.gov.br)
  - **OG image customizada** via `/api/og?template=pillar&title=...`

- [ ] **AC3** — Posts spokes existentes (em `/blog/content/` ou `/content/posts/` pós-SEO-007) linkam de volta ao pillar via CTA "Leia o guia completo: [Pillar Title]" no final do post. Critério: posts com `category: Guias` + tag relevante (Lei 14.133, PNCP, Licitações) devem ter o link.

- [ ] **AC4** — JSON-LD em cada pillar:
  - `Article` schema (reuso componente STORY-SEO-002, `@type: 'Article'`)
  - `BreadcrumbList` schema (reuso helper STORY-SEO-003)
  - `ItemList` com URLs dos spokes (elegibilidade "Collection Page")

- [ ] **AC5** — 3 pillar URLs submetidos em GSC "URL Inspection" + "Request Indexing" após deploy. Meta: indexar em ≤7 dias.

- [ ] **AC6** — Sitemap shard 0 (core) ou shard 3 (content) inclui os 3 URLs com `changefreq: monthly`, `priority: 0.9`.

- [ ] **AC7** — Teste E2E `frontend/e2e-tests/pillar-pages.spec.ts` verifica:
  - Acesso HTTP 200
  - H1 presente
  - TOC renderizado com ≥5 âncoras
  - ≥10 links internos (para `/blog/*`)
  - JSON-LD Article válido

- [ ] **AC8** — Atingir meta de tráfego em 90 dias pós-deploy: ≥500 sessões orgânicas/mês por pillar (dados GSC STORY-SEO-005)

---

## Scope IN

- 3 pillar pages `/guia/[slug]`
- Content writing (~12-15k words total)
- TOC component sticky/mobile
- Internal linking audit dos spokes + add CTAs
- JSON-LD + sitemap update
- GSC submission
- Testes E2E

## Scope OUT

- Pillar pages #4-5 (delegado a stories futuras: `/guia/pregao-eletronico`, `/guia/consultoria-licitacao`)
- Taxonomia `/blog/categoria/[slug]` (Audit 7.4 — story separada)
- Review/estilização visual profunda (handoff a @ux-design-expert via implementation)

---

## Content Outline (exemplos)

### Pillar 1: `/guia/licitacoes`

**H1:** Guia Completo de Licitações Públicas no Brasil

**H2 (suggested):**
1. O que é uma licitação pública? (answer-first: 2-3 frases)
2. Por que o governo precisa licitar?
3. Modalidades previstas na Lei 14.133/2021
   - H3 por modalidade: Pregão, Concorrência, Diálogo Competitivo, Concurso, Leilão, Credenciamento
4. Como participar de uma licitação (passo a passo)
5. Documentação e habilitação
6. Lei 14.133 vs Lei 8.666: principais mudanças
7. Portal PNCP: a porta de entrada atual
8. Erros comuns de iniciantes
9. Quando vale a pena participar? (análise de viabilidade)
10. Ferramentas que automatizam a busca (link para SmartLic)

**Spokes linkados (≥10):**
- `/blog/como-participar-primeira-licitacao-2026`
- `/blog/lei-14133-guia-fornecedores`
- `/blog/pregao-eletronico-guia-passo-a-passo`
- `/blog/pncp-guia-completo-empresas`
- `/blog/checklist-habilitacao-licitacao-2026`
- `/blog/analise-viabilidade-editais-guia`
- `/blog/como-calcular-preco-proposta-licitacao`
- `/blog/mei-microempresa-vantagens-licitacoes`
- `/blog/sicaf-como-cadastrar-manter-ativo-2026`
- `/blog/impugnacao-edital-quando-como-contestar`

### Pillar 2: `/guia/lei-14133`
Similar structure — H2s por capítulos da lei, H3s por artigos importantes, ≥10 spokes sobre Lei 14.133.

### Pillar 3: `/guia/pncp`
H2s sobre navegação PNCP, API, consultas, recursos, alternativas (link para SmartLic como wrapper inteligente).

---

## Files

- `frontend/app/guia/[slug]/page.tsx` (new dynamic route)
- `frontend/app/guia/layout.tsx` (new)
- `frontend/app/guia/_components/PillarContent.tsx` (new — base layout com TOC)
- `frontend/app/guia/_components/TableOfContents.tsx` (new — sticky nav, mobile collapse)
- `frontend/content/pillars/licitacoes.mdx` (new)
- `frontend/content/pillars/lei-14133.mdx` (new)
- `frontend/content/pillars/pncp.mdx` (new)
- `frontend/app/sitemap.ts` (add pillars to shard 0 or 3)
- `frontend/app/api/og/route.tsx` (add `template=pillar`)
- `frontend/e2e-tests/pillar-pages.spec.ts` (new)
- Modify: 10-20 spoke posts para adicionar CTA de volta ao pillar

---

## Dependencies

- **Blockers**: STORY-SEO-007 (MDX infra) preferível antes — mas pode usar TSX se urgência
- **Blockers**: STORY-SEO-002 (ArticleSchema) para reuso
- **Blockers**: STORY-SEO-003 (Breadcrumb helper) para reuso
- **Downstream**: `<TableOfContents>` component pode ser reusado em posts longos (Audit 4.2)

---

## Risks

| Risk | Mitigation |
|------|-----------|
| 12-15k words de content é esforço grande | Delegar parte a `/copymasters` squad; validar outline antes |
| Thin content penalty se não 3k+ words | Word count threshold no CI (fail se <3000) |
| Duplicate content com posts existentes | Lint script que mede overlap via simhash <20% |
| Indexação lenta | GSC manual submission (AC5) + internal linking forte |

---

## Success Metrics

- 3 pillars indexados em GSC ≤7 dias pós-deploy
- ≥500 sessões/mês por pillar em 90 dias (via SEO-005 dashboard)
- Posts spokes com CTA para pillar: CTR do CTA ≥5% (via Mixpanel/GA4)
- Pillar pages rankeiam top 10 para queries head-term ("guia licitações", "lei 14.133") em 90 dias

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-04-21 | @sm (River) | Story criada a partir do audit SEO 2026-04-21 |
| 2026-04-21 | @po (Pax) | Validação 9.5/10 — GO. Status Draft → Ready |
