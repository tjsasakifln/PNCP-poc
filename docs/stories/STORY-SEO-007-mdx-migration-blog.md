# Story SEO-007: Migração Blog Posts .tsx → .mdx

**Epic:** EPIC-SEO-2026-04
**Priority:** 🟠 P1
**Story Points:** 13 SP (1 sprint)
**Owner:** @dev
**Status:** Ready
**Audit Ref:** Audit 4.1

---

## Problem

70 arquivos em `frontend/app/blog/content/*.tsx` são **componentes JSX hardcoded**. Cada edit de copy requer deploy completo. Não há CMS. Isso degrada:

- **Content velocity**: iterações lentas → topical authority cresce devagar
- **A/B test de titles/intros**: inviável sem deploy por variação
- **Manutenção**: 70 arquivos TSX ≠ format amigável para escritor não-eng
- **Separação de concerns**: lógica (JSX) misturada com conteúdo editorial

Produto tem ritmo de ~35 posts/mês. Manter em .tsx limita esse ritmo.

---

## Acceptance Criteria

- [ ] **AC1** — Setup `next-mdx-remote` OU `contentlayer` (avaliar antes). Preferência: `next-mdx-remote` por zero vendor lock-in.

- [ ] **AC2** — Criar estrutura `frontend/content/posts/*.mdx` com frontmatter YAML:
  ```yaml
  ---
  slug: aditivos-contratuais-o-que-sao-como-monitorar
  title: Aditivos Contratuais — O Que São e Como Monitorar
  description: ...
  publishDate: 2026-02-24
  lastModified: 2026-04-10
  author: tiago-sasaki
  category: Guias
  tags: [Lei 14.133, Aditivos, TCU]
  wordCount: 3516
  readingTime: 15
  relatedSlugs: [slug1, slug2, slug3]
  ogImageTemplate: default  # ou "analise", etc.
  ---
  ```

- [ ] **AC3** — Migrar 70 posts de `.tsx` → `.mdx` preservando:
  - Mesmo `slug` (URL não muda — **ZERO** regressão no sitemap)
  - Mesmo HTML renderizado (comparar DOM via test visual)
  - Todos campos de `BlogArticleMeta` em `frontend/lib/blog.ts`
  - Componentes custom (CTA, tabelas estilizadas) disponíveis via MDX components map

- [ ] **AC4** — Criar helper `<BlogArticle>` wrapper que reduza boilerplate:
  - Metadata export automático de frontmatter
  - Integração com STORY-SEO-002 (ArticleSchema)
  - Integração com STORY-SEO-008 (link para pillar se `pillarParent` em frontmatter)

- [ ] **AC5** — `frontend/lib/blog.ts::getAllSlugs()` lê do diretório `content/posts/` em vez de import de TSX. Performance: build-time scan via `fs.readdir()`.

- [ ] **AC6** — Sitemap shard 3 (`/sitemap/3.xml`) preserva 301 URLs antes/depois da migração:
  ```bash
  # antes
  curl -sL /sitemap/3.xml | grep -c '<url>' == 301
  # depois (após deploy da migração)
  curl -sL /sitemap/3.xml | grep -c '<url>' == 301
  ```
  Se valor divergir → **BLOCKER** (regressão SEO).

- [ ] **AC7** — 301 redirects: se slug foi renomeado durante migração, adicionar em `next.config.js`. Preferir NÃO renomear.

- [ ] **AC8** — Teste E2E: `frontend/e2e-tests/blog-migration.spec.ts` verifica:
  - `/blog/[5 sample slugs]` retornam HTTP 200
  - HTML contém título do post + primeiro parágrafo (snapshot testing)
  - `og:title`, `og:description`, canonical corretos
  - JSON-LD Article schema (STORY-SEO-002) emitido

- [ ] **AC9** — Documentação: `docs/guides/writing-blog-posts.md` explicando novo fluxo MDX para equipe de conteúdo.

---

## Scope IN

- Setup MDX infra
- Migração 70 posts
- Helper `<BlogArticle>` + custom components
- Update `blog.ts` para MDX-based
- Sitemap coverage test
- Docs

## Scope OUT

- Reescrever conteúdo dos posts (é migração, não refresh — refresh é mid-term)
- CMS headless (Sanity/Strapi) — descartado por custo $$/mês e vendor lock-in
- Bump de `lastModified` (Audit 4.6 — story separada)
- FAQPage cleanup (Audit 4.7 — story separada)

---

## Migration Strategy

### Opção A (recomendada): Script automatizado de migração

```bash
# scripts/migrate-blog-tsx-to-mdx.js
# 1. Ler cada frontend/app/blog/content/*.tsx
# 2. Extrair:
#    - Metadata de frontmatter.ts ou export const metadata
#    - JSX content → converter para Markdown + componentes MDX
#    - Slug = filename - .tsx
# 3. Escrever frontend/content/posts/<slug>.mdx
# 4. Validar: count de arquivos antes/depois
```

### Opção B: Migração manual (se Opção A gerar MDX "sujo")

Migrar manualmente em batches de 10 posts. Mais lento mas qualidade superior.

### Fallback Plan

Se migração quebrar algum slug, fazer rollback via git revert; sitemap coverage test no CI previne merge.

---

## Files

### New
- `frontend/content/posts/*.mdx` (70 arquivos)
- `frontend/app/blog/_components/BlogArticle.tsx`
- `frontend/mdx-components.tsx` (custom components map)
- `scripts/migrate-blog-tsx-to-mdx.js`
- `docs/guides/writing-blog-posts.md`
- `frontend/e2e-tests/blog-migration.spec.ts`

### Modify
- `frontend/package.json` (add `next-mdx-remote`, `gray-matter`, `remark-gfm`)
- `frontend/next.config.js` (MDX config)
- `frontend/lib/blog.ts` (MDX-based `getAllSlugs`, `getArticle`)
- `frontend/app/blog/[slug]/page.tsx` (render MDX)

### Delete (após migração validada)
- `frontend/app/blog/content/*.tsx` (70 arquivos)

---

## Dependencies

- **Blockers**: STORY-SEO-002 (Article schema) idealmente antes, mas pode paralelizar
- **Downstream**: STORY-SEO-008 (pillar pages) reusa infra MDX

---

## Risks

| Risk | Mitigation |
|------|-----------|
| Migração quebra algum slug | Sitemap coverage CI test (AC6) + script de verificação URL×URL |
| Custom components JSX não traduzem limpo | Opção B (migração manual) |
| Bundle size aumenta | `next-mdx-remote` é lightweight; tree-shake per page |
| Dev experience piora para devs acostumados com TSX | Doc clara (AC9) + MDX suporta componentes React |

---

## Success Metrics

- 70 posts migrados, 301 URLs preservados no sitemap
- Build time reduzido em ≥10% (MDX mais leve que compilar 70 componentes)
- Próximo post publicado em <5 min (edit frontmatter + deploy) vs ~20 min hoje
- Zero regressão em LCP (STORY-SEO-006 tracking)

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-04-21 | @sm (River) | Story criada a partir do audit SEO 2026-04-21 |
| 2026-04-21 | @po (Pax) | Validação 9.5/10 — GO. Status Draft → Ready |
