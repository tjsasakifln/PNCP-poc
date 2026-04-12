# STORY-439: Thin Content Gates — Entity Pages + Trust Signals

**Priority:** P0 (complemento urgente à STORY-430 — portões faltando em entity pages + E-E-A-T)
**Effort:** M (1-2 dias)
**Squad:** @dev + @devops
**Status:** Done
**Epic:** [EPIC-SEO-ORGANIC-2026-04](EPIC-SEO-ORGANIC-2026-04.md)
**Sprint:** Sprint 1 — urgente (paralelo à STORY-430)

---

## Contexto

A STORY-430 cobriu os portões de noindex nas páginas programáticas setor×UF. Esta story cobre os gaps remanescentes identificados no audit de 2026-04-12:

1. **`/orgaos/[slug]` não tem nenhum portão de qualidade** — indexa 100% das páginas de órgãos independentemente do volume de licitações. Com ~2.000 URLs no sitemap, muitas com conteúdo raso (120 palavras, dados tabulares).

2. **City×Sector (1.215 URLs) no sitemap sem threshold** — `CITIES.flatMap(SECTORS)` inclui todas as 1.215 combinações cidade×setor no sitemap.xml sem qualquer verificação de conteúdo disponível. Essas páginas têm noindex em nível de página (via `MIN_ACTIVE_BIDS_FOR_INDEX`), mas ainda consomem crawl budget ao aparecerem no sitemap.

3. **Backend endpoints de sitemap sem filtro de qualidade** — `/v1/sitemap/cnpjs`, `/v1/sitemap/orgaos`, `/v1/sitemap/fornecedores-cnpj` precisam ser auditados para confirmar que retornam apenas entidades com dados suficientes. Se não filtrarem, o sitemap inclui entidades que a própria page.tsx vai noindex — desperdício de crawl budget.

4. **Organization schema incompleto** — O schema `Organization` em `StructuredData.tsx` não tem `taxID` (CNPJ), `founder` (pessoa real) nem `legalName` completo. Esses são sinais críticos de Trust para o Google E-E-A-T classifier em 2026.

5. **Autor dos artigos do blog não renderizado no HTML** — O JSON-LD tem `author: SmartLic Organization` (genérico), mas o byline não aparece no HTML visível. Em 2026, conteúdo sem autoria visível e individual é sinal de thin/AI content.

---

## Acceptance Criteria

### AC1: `/orgaos/[slug]` — Portão de noindex
- [x] Em `frontend/app/orgaos/[slug]/page.tsx`, na função `generateMetadata()`, adicionado:
  - Caso `!stats`: retorna `robots: { index: false, follow: false }`
  - Caso `stats.total_licitacoes < minBids`: retorna `robots: { index: false, follow: true }`
- [x] `follow: true` quando dados insuficientes — mantém seguimento de links internos
- [x] TypeScript compila sem erros em `frontend/`

### AC2: Sitemap — remover city×sector sem threshold
- [x] Em `frontend/app/sitemap.ts`, bloco `cidadeSectorRoutes` comentado (1.215 URLs removidas)
- [x] `cidadeRoutes` (81 cidades sem setor) permanece no sitemap
- [x] Return array atualizado — linha `...cidadeSectorRoutes` removida

### AC3: Auditar e corrigir backend endpoints de sitemap
- [x] **`/v1/sitemap/orgaos`** (`backend/routes/sitemap_orgaos.py`): filtra por `is_active = True` no RPC `get_sitemap_orgaos_json` e no fallback paginated. ✅ Retorna apenas órgãos com ≥1 bid ativo.
- [x] **`/v1/sitemap/cnpjs`** (`backend/routes/sitemap_cnpjs.py`): filtra por `is_active = True` na `pncp_raw_bids`. ✅ Retorna apenas CNPJs com ≥1 bid ativo.
- [x] **`/v1/sitemap/fornecedores-cnpj`**: filtra por `is_active = True` na `pncp_supplier_contracts`. ✅ Retorna apenas fornecedores com contratos ativos.
- [x] **Sem modificação necessária** — backends já aplicam quality filter adequado.
- [x] **Threshold mismatch documentado** (Fase B): backend usa ≥1 ativo; pages usam ≥5 via `MIN_ACTIVE_BIDS_FOR_INDEX`. Entidades com 1-4 bids ficam no sitemap mas serão noindex na page. Impacto: minor crawl budget leak. Correção via endpoint filtrado (Fase B).

### AC4: Organization schema — Trust completeness
- [x] Em `frontend/app/components/StructuredData.tsx`, adicionado ao schema `Organization`:
  - `taxID: '52.407.089/0001-09'`
  - `logo: { '@type': 'ImageObject', url, contentUrl }`
  - `address.addressLocality: 'Florianópolis'` + `addressRegion: 'SC'`
  - `founder: { '@type': 'Person', name: 'Tiago Sasaki', jobTitle: 'CEO & CTO', sameAs: [LinkedIn, GitHub] }`
- [x] Campos existentes preservados (`contactPoint`, `sameAs`, `legalName`, `foundingDate`)
- [x] TypeScript compila sem erros

### AC5: Blog — autor visível no HTML + JSON-LD Person
- [x] **Já implementado**: `BlogArticleLayout.tsx` usa `DEFAULT_AUTHOR_SLUG = 'tiago-sasaki'` como fallback
- [x] Byline já renderizado no HTML (linhas 258-267 de `BlogArticleLayout.tsx`): nome como link + `shortBio`
- [x] JSON-LD `Article.author` já usa `@type: 'Person'` com dados completos do Tiago Sasaki
- [x] `lib/authors.ts` já contém perfil completo: LinkedIn, GitHub, bio, credentials
- [x] TypeScript compila sem erros

---

## Scope

**IN:**
- `/orgaos/[slug]/page.tsx` — portão noindex
- `sitemap.ts` — remoção de city×sector
- Backend sitemap endpoints — auditoria e correção de queries
- `StructuredData.tsx` — enriquecimento do schema Organization
- `blog/[slug]/page.tsx` e `SchemaMarkup.tsx` — autor visível + JSON-LD Person

**OUT:**
- Enriquecimento editorial das entity pages (Fase B)
- Schema `Offer` + `FAQPage` em `/features` e `/planos` (Fase B)
- Expansão de word count (Fase B)
- Endpoint backend `/v1/sitemap/cidade-setor-indexable` (Fase B — apenas removemos do sitemap agora)
- Nenhuma mudança em páginas já cobertas pela STORY-430

---

## Dependencies

- STORY-430 (completa ou em paralelo) — garante que setor×UF já estão com noindex correto
- Acesso ao backend Python para AC3

---

## Risks

- **AC2 reduz crawl budget mas temporariamente remove city×sector do sitemap** — aceitável porque essas páginas já são noindex em page-level
- **AC5 muda autoria no JSON-LD de Organization → Person** — risco baixo, melhora E-E-A-T

---

## File List

- [x] `frontend/app/orgaos/[slug]/page.tsx` — AC1: portão noindex adicionado
- [x] `frontend/app/sitemap.ts` — AC2: city×sector removido (1.215 URLs)
- [x] `frontend/app/components/StructuredData.tsx` — AC4: taxID, founder, addressLocality
- [x] `frontend/__tests__/orgaos-noindex-gate.test.tsx` — QA: 6 novos testes para AC1 (todos passando)
- [ ] `frontend/app/blog/[slug]/page.tsx` — AC5: já estava correto (DEFAULT_AUTHOR_SLUG)
- [ ] `frontend/components/blog/SchemaMarkup.tsx` — AC5: já estava correto
- [ ] `backend/routes/sitemap_orgaos.py` — AC3: auditado, sem modificação necessária
- [ ] `backend/routes/sitemap_cnpjs.py` — AC3: auditado, sem modificação necessária

---

## Dev Notes

- `MIN_ACTIVE_BIDS_FOR_INDEX` já é env var existente — usar o mesmo padrão do AC1 sem criar nova constante
- `formatDate()` para byline deve usar locale `pt-BR` (`toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', year: 'numeric' })`)
- Byline styling: seguir classes Tailwind já usadas nas páginas de blog (verificar `blog/[slug]/page.tsx` antes de adicionar novas classes)
- LinkedIn do Tiago: confirmar URL antes de incluir no `sameAs` do founder

---

## Change Log

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-12 | @sm (River) | Story criada — gaps identificados após audit de thin content |
| 2026-04-12 | @po (Pax) | GO — 10/10 — Status Draft → Ready |
| 2026-04-12 | @dev | Implementação completa — AC1, AC2, AC4 com código; AC3 auditado (sem mudanças); AC5 já estava implementado |
| 2026-04-12 | @qa (Quinn) | PASS — 7 checks OK, 6 novos testes criados e passando, TypeScript limpo |
