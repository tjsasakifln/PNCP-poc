# STORY-261: Blog Platform & SEO Content Infrastructure

**Status:** Done
**Priority:** P0 — Critical (prerequisite for STORY-262 e STORY-263)
**Track:** GTM — Content Marketing & SEO Authority
**Created:** 2026-02-24
**Depends on:** —
**Blocks:** STORY-262, STORY-263

---

## Contexto

O SmartLic possui 4 páginas educacionais estáticas (`/como-avaliar-licitacao`, `/como-evitar-prejuizo-licitacao`, `/como-filtrar-editais`, `/como-priorizar-oportunidades`) que já demonstram o padrão técnico correto: `ContentPageLayout`, schemas JSON-LD, sitemap, canonical URLs.

Porém, **não existe uma seção de blog** — não há `/blog`, não há sistema de listagem de artigos, não há categorias, não há feed RSS, não há navegação por data. Para executar a estratégia de content marketing com 30 artigos (STORY-262 + STORY-263), é necessário construir a infraestrutura de blog primeiro.

### Diretrizes SEO 2026 Aplicadas

| Diretriz | Implementação |
|----------|---------------|
| **E-E-A-T** (Experience, Expertise, Authoritativeness, Trust) | Author schema (Organization), datePublished/dateModified, fonte de dados verificáveis |
| **Topical Authority** (content clusters) | Categorias B2G e Consultorias, internal linking entre artigos, breadcrumbs hierárquicos |
| **Schema Markup** | BlogPosting JSON-LD com author, publisher, datePublished, dateModified, wordCount, articleSection |
| **Rich Results** | FAQ schema em artigos com seção de perguntas; Article schema para todos |
| **Technical SEO** | Sitemap dinâmico, canonical URLs, OG/Twitter cards, RSS feed, Core Web Vitals |
| **Content Quality Signals** | readingTime, wordCount, structured headings (H1→H2→H3), data-backed claims |

### Current State

```
frontend/app/
├── como-avaliar-licitacao/page.tsx      ← 4 páginas estáticas
├── como-evitar-prejuizo-licitacao/      ← sem sistema de blog
├── como-filtrar-editais/
├── como-priorizar-oportunidades/
├── components/ContentPageLayout.tsx      ← layout reutilizável
├── sitemap.ts                           ← sitemap estático
└── (sem /blog, sem RSS, sem categorias)
```

### Target State

```
frontend/app/
├── blog/
│   ├── page.tsx                          ← Listing page com filtros
│   ├── [slug]/page.tsx                   ← Dynamic route para artigos
│   └── rss.xml/route.ts                  ← RSS feed (Route Handler)
├── components/
│   ├── ContentPageLayout.tsx             ← existente (sem alteração)
│   └── BlogArticleLayout.tsx             ← NOVO: layout de artigo de blog
├── lib/
│   └── blog.ts                           ← metadata index + utilities
├── sitemap.ts                            ← ATUALIZADO: inclui /blog/*
└── layout.tsx                            ← ATUALIZADO: nav link para blog
```

---

## Acceptance Criteria

### Frontend — Blog Article Layout

- [x] **AC1:** Criar `BlogArticleLayout.tsx` baseado no `ContentPageLayout.tsx` mas com campos adicionais:
  - `category` (badge: "Empresas B2G" | "Consultorias de Licitação")
  - `publishDate` (formatado "24 de fevereiro de 2026")
  - `readingTime` (calculado automaticamente: ~200 palavras/minuto)
  - `author` (fixo: "Equipe SmartLic" com link para /sobre)
  - `relatedArticles` (até 3 artigos relacionados com thumbnail-placeholder)
  - `tags` (lista de tags clicáveis que filtram na listing page)
  - Sidebar: CTA card (existente) + "Artigos Relacionados" + "Categorias"
  - Reading progress bar no topo (sutil, cor brand-blue, height 3px)
  - Botões de share (LinkedIn, WhatsApp, copiar link) — sem dependências externas

- [x] **AC2:** `BlogArticleLayout` deve renderizar structured data JSON-LD:
  ```json
  {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    "headline": "...",
    "description": "...",
    "author": { "@type": "Organization", "name": "SmartLic", "url": "https://smartlic.tech" },
    "publisher": { "@type": "Organization", "name": "SmartLic", "logo": { "@type": "ImageObject", "url": "https://smartlic.tech/logo.png" } },
    "datePublished": "2026-02-24",
    "dateModified": "2026-02-24",
    "mainEntityOfPage": { "@type": "WebPage", "@id": "https://smartlic.tech/blog/{slug}" },
    "wordCount": 2500,
    "articleSection": "Empresas B2G",
    "inLanguage": "pt-BR"
  }
  ```

- [x] **AC3:** `BlogArticleLayout` deve incluir Breadcrumb schema:
  ```
  Início > Blog > [Categoria] > [Título do Artigo]
  ```
  Com BreadcrumbList JSON-LD correspondente.

### Frontend — Blog Listing Page

- [x] **AC4:** Criar `/blog/page.tsx` com:
  - Hero section: título "Inteligência em Licitações", subtítulo "Artigos, guias e análises para empresas e consultorias que disputam contratos públicos"
  - Filtros: "Todos" | "Empresas B2G" | "Consultorias" (tabs ou toggle pills)
  - Grid de cards responsivo: 1 col (mobile), 2 cols (tablet), 3 cols (desktop)
  - Card de artigo: título, descrição (2 linhas max), categoria (badge), data, tempo de leitura
  - Ordenação: mais recentes primeiro
  - Sem paginação inicial (30 artigos cabem em 1 página com lazy loading)
  - CTA banner entre os cards (a cada 6 artigos): "Experimente o SmartLic gratuitamente"

- [x] **AC5:** Metadata da listing page:
  ```typescript
  export const metadata: Metadata = {
    title: 'Blog — Inteligência em Licitações Públicas',
    description: 'Artigos, guias e análises sobre licitações públicas para empresas B2G e consultorias. Estratégias baseadas em dados para aumentar sua taxa de vitória.',
    alternates: { canonical: 'https://smartlic.tech/blog' },
    openGraph: {
      title: 'Blog SmartLic — Inteligência em Licitações',
      description: 'Conteúdo premium sobre estratégia, análise e inteligência em licitações públicas.',
      type: 'website',
    },
  };
  ```

### Frontend — Article Data Index

- [x] **AC6:** Criar `frontend/app/lib/blog.ts` com:
  - Interface `BlogArticleMeta`: slug, title, description, category, tags, publishDate, readingTime, keywords (SEO), relatedSlugs
  - Array `BLOG_ARTICLES: BlogArticleMeta[]` com metadados de todos os artigos
  - Funções utilitárias:
    - `getArticleBySlug(slug: string): BlogArticleMeta | undefined`
    - `getArticlesByCategory(category: string): BlogArticleMeta[]`
    - `getRelatedArticles(slug: string): BlogArticleMeta[]`
    - `getAllSlugs(): string[]` (para generateStaticParams)
    - `calculateReadingTime(wordCount: number): string` (retorna "X min de leitura")

### Frontend — Dynamic Article Route

- [x] **AC7:** Criar `/blog/[slug]/page.tsx` com:
  - `generateStaticParams()` retornando todos os slugs do blog index
  - `generateMetadata()` retornando metadata dinâmica por slug (title, description, canonical, OG)
  - Importação dinâmica do conteúdo via lazy component: `const ArticleContent = dynamic(() => import(\`@/app/blog/content/${slug}\`))`
  - Fallback: `notFound()` para slugs inexistentes

- [x] **AC8:** Criar diretório `frontend/app/blog/content/` para armazenar conteúdo de cada artigo como componentes React exportados. Cada arquivo:
  - Exporta default function com JSX do conteúdo (segue padrão das como-* pages)
  - Nome do arquivo = slug do artigo (ex: `como-aumentar-taxa-vitoria-licitacoes.tsx`)

### Frontend — RSS Feed

- [x] **AC9:** Criar `/blog/rss.xml/route.ts` (Next.js Route Handler) que gera RSS 2.0 feed:
  - Content-Type: `application/rss+xml; charset=utf-8`
  - Inclui todos os artigos de `BLOG_ARTICLES`
  - Campos: title, link, description, pubDate, guid, category
  - Channel: title "SmartLic Blog", description, link, language "pt-BR"

### Frontend — Sitemap & Navigation Updates

- [x] **AC10:** Atualizar `sitemap.ts` para incluir:
  - `/blog` (priority 0.9, changeFrequency weekly)
  - Cada artigo `/blog/{slug}` (priority 0.7, changeFrequency monthly)
  - Importar slugs de `lib/blog.ts` para geração dinâmica

- [x] **AC11:** Atualizar navegação:
  - `LandingNavbar`: adicionar link "Blog" entre "Como Funciona" e "Sobre"
  - `Footer`: adicionar seção "Blog" com links para categorias
  - `<link rel="alternate" type="application/rss+xml">` no layout.tsx head

### Frontend — SEO & Performance

- [x] **AC12:** Cada artigo individual deve:
  - Ter canonical URL: `https://smartlic.tech/blog/{slug}`
  - Ter OG image dinâmica (pode usar `/api/og?title={title}&category={category}`)
  - Ter Twitter Card (summary_large_image)
  - Passar Core Web Vitals (LCP < 2.5s, FID < 100ms, CLS < 0.1)
  - Ser statically generated (ISR não é necessário — conteúdo é estático)

- [x] **AC13:** Links internos obrigatórios entre artigos:
  - Cada artigo deve linkar para pelo menos 2 outros artigos do blog
  - Cada artigo deve linkar para pelo menos 1 página de produto (/features, /planos, /buscar)
  - Sidebar "Artigos Relacionados" deve mostrar 3 artigos da mesma categoria

### Frontend — Visual & Brand Standards

- [x] **AC14:** Estilo visual deve transmitir:
  - **Rigor institucional**: tipografia serif para títulos de artigo (font-family: Georgia, 'Times New Roman'), sans-serif para corpo
  - **Elegância**: espaçamento generoso (prose-lg), margens amplas, hierarquia visual clara
  - **Sobriedade**: paleta neutra com acentos brand-blue, sem animações excessivas
  - **Confiança**: dados citados com fonte, citações em blockquote estilizado, autor visível
  - Dark mode completo (respeitar variáveis CSS existentes)

### Testes

- [x] **AC15:** Frontend tests ≥20 em `__tests__/blog-infrastructure.test.tsx`:
  - BlogArticleLayout renderiza schema JSON-LD correto
  - BlogArticleLayout renderiza breadcrumbs corretos
  - Blog listing page renderiza cards de artigos
  - Blog listing page filtra por categoria
  - getArticleBySlug retorna artigo correto
  - getRelatedArticles retorna artigos relacionados
  - calculateReadingTime retorna formato correto
  - RSS route retorna XML válido
  - generateStaticParams retorna todos os slugs
  - Share buttons renderizam e copiam link

- [x] **AC16:** Zero regressões nos testes existentes (baseline: 2681 pass / 0 fail)

### Backward Compatibility

- [x] **AC17:** As 4 páginas existentes (`/como-*`) continuam funcionando sem alteração
- [x] **AC18:** ContentPageLayout.tsx não é modificado (BlogArticleLayout é componente novo)
- [x] **AC19:** Sitemap existente mantém todas as URLs atuais (apenas adições)

---

## Architecture

```
User Request → /blog                    → Blog Listing (SSG)
            → /blog/{slug}              → Article Page (SSG)
            → /blog/rss.xml             → RSS Feed (Route Handler)

Blog Listing                             Article Page
┌─────────────────────────┐              ┌─────────────────────────┐
│ Hero: "Inteligência em  │              │ Breadcrumb              │
│  Licitações"            │              │ ┌───────────────┐ ┌───┐│
│                         │              │ │ Article Title  │ │   ││
│ [Todos] [B2G] [Consult] │              │ │ Category Badge │ │ S ││
│                         │              │ │ Date • 8 min   │ │ I ││
│ ┌─────┐ ┌─────┐ ┌─────┐│              │ │               │ │ D ││
│ │Card │ │Card │ │Card ││              │ │ Content...    │ │ E ││
│ │  1  │ │  2  │ │  3  ││              │ │ H2, H3, data │ │ B ││
│ └─────┘ └─────┘ └─────┘│              │ │ blockquotes  │ │ A ││
│ ┌─────┐ ┌─────┐ ┌─────┐│              │ │               │ │ R ││
│ │Card │ │Card │ │Card ││              │ │ CTA Section   │ │   ││
│ │  4  │ │  5  │ │  6  ││              │ └───────────────┘ └───┘│
│ └─────┘ └─────┘ └─────┘│              │ Related Articles       │
│                         │              └─────────────────────────┘
│ ┌─── CTA Banner ──────┐│
│ └──────────────────────┘│              JSON-LD: BlogPosting +
│ ... more cards ...      │              BreadcrumbList + FAQ
└─────────────────────────┘
```

### File Structure

```
frontend/
├── app/
│   ├── blog/
│   │   ├── page.tsx                    # Listing page
│   │   ├── [slug]/page.tsx             # Dynamic article route
│   │   ├── content/                    # Article content components
│   │   │   ├── como-aumentar-taxa-vitoria-licitacoes.tsx
│   │   │   ├── erro-operacional-perder-contratos.tsx
│   │   │   └── ... (30 files total, created in STORY-262/263)
│   │   └── rss.xml/
│   │       └── route.ts                # RSS feed
│   ├── components/
│   │   └── BlogArticleLayout.tsx       # Article layout
│   └── lib/
│       └── blog.ts                     # Article metadata index
├── __tests__/
│   └── blog-infrastructure.test.tsx    # Tests
└── sitemap.ts                          # MODIFIED: add blog routes
```

---

## Estimativa

| Componente | Esforço |
|------------|---------|
| BlogArticleLayout.tsx | 3h |
| Blog listing page | 2h |
| lib/blog.ts (data index) | 1h |
| Dynamic route [slug] | 1h |
| RSS feed | 1h |
| Sitemap + Navigation | 1h |
| Visual styling (brand) | 2h |
| Tests (20+) | 2h |
| **Total** | **~13h** |

---

## File List

| File | Action |
|------|--------|
| `frontend/app/components/BlogArticleLayout.tsx` | CREATE |
| `frontend/app/blog/page.tsx` | CREATE |
| `frontend/app/blog/[slug]/page.tsx` | CREATE |
| `frontend/app/blog/rss.xml/route.ts` | CREATE |
| `frontend/app/blog/content/.gitkeep` | CREATE |
| `frontend/app/lib/blog.ts` | CREATE |
| `frontend/app/sitemap.ts` | MODIFY |
| `frontend/app/layout.tsx` | MODIFY |
| `frontend/app/components/landing/LandingNavbar.tsx` | MODIFY |
| `frontend/app/components/Footer.tsx` | MODIFY |
| `frontend/__tests__/blog-infrastructure.test.tsx` | CREATE |
