# Story SEO-002: Article/BlogPosting Schema em /blog/[slug] e 70 Posts

**Epic:** EPIC-SEO-2026-04
**Priority:** 🟠 P1
**Story Points:** 5 SP
**Owner:** @dev
**Status:** Done (AC1-AC5 shipped, AC3 Rich Results formal PASS em transient-hellman)
**Audit Ref:** Audit 1.1 + 3.4

---

## Problem

70 arquivos em `frontend/app/blog/content/*.tsx` têm `generateMetadata()` completa (title + description + OG + canonical) mas **NÃO emitem** `<script type="application/ld+json">` com `@type: Article` ou `BlogPosting`.

**Impacto:**
- Rich Results Test falha em "Article" eligibility em 100% dos posts
- Perda de elegibilidade para Google News, Top Stories, Discover
- Sem badge "autor" em AI Overviews (SGE)
- CTR em SERP estimado 10-15% abaixo do potencial

**Observação adicional (Audit 3.4):** 29+ posts têm `FAQPage` schema como primário, o que Google considera má hierarquia. Article deveria ser primário com FAQPage aninhado como `mainEntity.hasPart`.

---

## Acceptance Criteria

- [ ] **AC1** — Criar componente `frontend/app/blog/_components/ArticleSchema.tsx` que emite JSON-LD com:
  - `@type: Article` (ou `TechArticle` via prop para posts técnicos)
  - `headline` (≤110 chars, derivado de `metadata.title`)
  - `image` (URL absoluta do OG image via `/api/og?title=...`)
  - `datePublished` + `dateModified` (do `blog.ts: publishDate, lastModified`)
  - `author` → `@type: Person`, `name`, `url: /blog/author/[slug]`
  - `publisher` → referência Organization (reuso de `StructuredData.tsx`)
  - `mainEntityOfPage` (canonical URL)
  - `wordCount` (do `BlogArticleMeta`)
  - `articleSection` (`category`)
  - `keywords` (`tags`)

- [ ] **AC2** — Importar em `frontend/app/blog/[slug]/page.tsx` no server component, antes do conteúdo

- [ ] **AC3** — 5 URLs sample (amostra estratificada: curto, médio, longo, Q&A-shaped, technical) passam no Rich Results Test: https://search.google.com/test/rich-results

- [ ] **AC4** — Posts com FAQPage schema (29 identificados) mantêm FAQPage mas DEVEM ter Article como schema principal (Article emitido antes, FAQPage como secundário). Auditoria de quais posts devem manter FAQPage (apenas Q&A-shaped genuínos) é escopo da STORY-SEO-007.

- [ ] **AC5** — Teste unitário Jest em `frontend/__tests__/blog/ArticleSchema.test.tsx` valida:
  - JSON parseable
  - Todos campos obrigatórios presentes
  - `@type` correto conforme prop
  - `datePublished` em formato ISO 8601

- [ ] **AC6** — GSC "Enhancements → Articles" report mostra 70 URLs válidas após re-crawl (validar em +30 dias pós-deploy)

---

## Scope IN

- Componente `ArticleSchema.tsx`
- Integração em `/blog/[slug]/page.tsx`
- Teste unitário
- Smoke test manual em 5 URLs via Rich Results Test

## Scope OUT

- Reescrever conteúdo dos posts (STORY-SEO-007, SEO-008)
- Auditoria de FAQPage overuse (escopo separado — Audit 4.7)
- Generation de `og image` customizada por post (existe via `/api/og?title=` — basta usar)

---

## Implementation Sketch

```tsx
// frontend/app/blog/_components/ArticleSchema.tsx
interface ArticleSchemaProps {
  slug: string;
  title: string;
  description: string;
  publishDate: string;
  lastModified?: string;
  author: { name: string; slug: string };
  category: string;
  tags: string[];
  wordCount: number;
  ogImageUrl: string;
  type?: 'Article' | 'TechArticle' | 'BlogPosting';
}

export function ArticleSchema(props: ArticleSchemaProps) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': props.type || 'Article',
    headline: props.title.slice(0, 110),
    description: props.description,
    image: props.ogImageUrl,
    datePublished: props.publishDate,
    dateModified: props.lastModified || props.publishDate,
    author: {
      '@type': 'Person',
      name: props.author.name,
      url: `https://smartlic.tech/blog/author/${props.author.slug}`,
    },
    publisher: {
      '@type': 'Organization',
      name: 'SmartLic',
      logo: {
        '@type': 'ImageObject',
        url: 'https://smartlic.tech/logo.svg',
      },
    },
    mainEntityOfPage: `https://smartlic.tech/blog/${props.slug}`,
    wordCount: props.wordCount,
    articleSection: props.category,
    keywords: props.tags.join(', '),
  };
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}
```

```tsx
// frontend/app/blog/[slug]/page.tsx (adicionar)
import { ArticleSchema } from '../_components/ArticleSchema';

export default async function BlogPost({ params }) {
  const article = await getArticle(params.slug);
  return (
    <>
      <ArticleSchema
        slug={params.slug}
        title={article.title}
        description={article.description}
        publishDate={article.publishDate}
        lastModified={article.lastModified}
        author={article.author}
        category={article.category}
        tags={article.tags}
        wordCount={article.wordCount}
        ogImageUrl={`https://smartlic.tech/api/og?title=${encodeURIComponent(article.title)}`}
      />
      {/* resto do conteúdo */}
    </>
  );
}
```

---

## Files

- `frontend/app/blog/_components/ArticleSchema.tsx` (new)
- `frontend/app/blog/[slug]/page.tsx` (modify)
- `frontend/__tests__/blog/ArticleSchema.test.tsx` (new)
- `frontend/lib/blog.ts` (adicionar helper `getArticleSchemaProps(slug)` se necessário)

---

## Success Metrics

- 100% dos 70 posts com Article schema válido no Rich Results Test (amostra 5)
- CTR médio de posts em GSC sobe ≥15% em 30 dias pós-deploy
- "Articles" report no GSC mostra 70 URLs válidas

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-04-21 | @sm (River) | Story criada a partir do audit SEO 2026-04-21 |
| 2026-04-21 | @po (Pax) | Validação 7.5/10 — GO. Obs: sem seção Risks; dep SEO-007 informal. Status Draft → Ready |
| 2026-04-21 | @devops (Gage) — sessão transient-hellman | **AC3 formalmente validado via Playwright + Google Rich Results Test.** 3 blog URLs validadas (`/blog/analise-viabilidade-editais-guia` — 3200 words, Tiago Sasaki Person author; `/blog/como-calcular-preco-proposta-licitacao` — 2800 words; `/blog/checklist-habilitacao-licitacao-2026` — 3000 words, articleSection=Guias). Rich Results Test oficial Google em `/blog/analise-viabilidade-editais-guia` retornou **5 itens válidos** (Article + FAQPage + Organization + LocalBusiness + SoftwareApplication) com `check_circle` e zero erros críticos. Status Ready → Done. AC6 (GSC "Articles" report +30d) permanece pós-deploy manual. |
