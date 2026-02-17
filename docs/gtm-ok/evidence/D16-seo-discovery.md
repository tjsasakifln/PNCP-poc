# D16 - SEO & Discovery Audit

**Dimension:** SEO & Discovery (D16)
**Date:** 2026-02-17
**Auditor:** @analyst + @ux-design-expert
**Methodology:** Codebase static analysis of all SEO-relevant files, structured data review, content coverage assessment, keyword targeting evaluation
**Score: 5/10 (SEO Foundations)**

---

## Executive Summary

SmartLic has a solid technical SEO foundation with proper meta tags, sitemap, robots.txt, structured data, canonical URLs, and Google Search Console verification. However, it fundamentally lacks the **content depth** required to rank for competitive procurement keywords in Brazil. The site is a single-page SaaS application with no blog, no educational content, no case studies, and no indexable dynamic pages -- making organic discovery near-impossible against entrenched competitors (Licitanet, ComprasNet, Portal de Licitacoes) that have years of domain authority and content.

---

## 1. Technical SEO Audit

### 1.1 Sitemap

**File:** `frontend/public/sitemap.xml` (static, via `next-sitemap`)
**Config:** `frontend/next-sitemap.config.js`

**Findings:**
- [PASS] Valid XML sitemap with correct schema namespaces
- [PASS] Correct `siteUrl`: `https://smartlic.tech`
- [PASS] Priority correctly assigned: `/ /buscar /features /planos` at 1.0; auth pages at 0.7; utility pages at 0.5
- [PASS] `changefreq` values appropriate: daily for content pages, monthly for legal
- [ISSUE] Static lastmod timestamps (all identical `2026-02-17T12:38:27.887Z`) -- not reflecting actual content changes
- [ISSUE] `sitemap.xml` itself is listed as a URL in the sitemap (line 22), which is incorrect
- [ISSUE] `icon.png` listed as a page (line 9) -- an asset, not a page
- [ISSUE] No `<image:image>` entries despite having OG images
- [ISSUE] 22 URLs total -- extremely thin for SEO competitiveness
- [CRITICAL] Many included pages (`/buscar`, `/dashboard`, `/pipeline`, `/historico`, `/conta`, `/mensagens`) require authentication and return no useful content to crawlers -- these are wasted crawl budget

**Verdict: 6/10** -- Functional but with notable waste and missed opportunities.

### 1.2 Robots.txt

**File:** `frontend/public/robots.txt`

```
User-agent: *
Allow: /
Disallow: /admin
Disallow: /auth/callback
Disallow: /api

Host: https://smartlic.tech
Sitemap: https://smartlic.tech/sitemap.xml
```

**Findings:**
- [PASS] Correct structure, properly blocks `/admin`, `/auth/callback`, `/api`
- [PASS] Sitemap reference present
- [PASS] Host directive present (though not universally recognized)
- [ISSUE] Does not block authenticated-only pages (`/dashboard`, `/pipeline`, `/historico`, `/conta`, `/mensagens`) -- these will be crawled but show login redirects, wasting crawl budget and potentially causing soft 404s
- [ISSUE] No crawl-delay specified (minor, not critical)

**Verdict: 7/10** -- Good basics, should block auth-gated routes.

### 1.3 Meta Tags

**File:** `frontend/app/layout.tsx` (root metadata)

**Findings:**
- [PASS] `metadataBase` correctly set to `https://smartlic.tech`
- [PASS] Title template with site name: `%s | SmartLic.tech`
- [PASS] Default title: "SmartLic.tech - Como Encontrar e Vencer Licitacoes Publicas Facilmente" -- targets primary intent
- [PASS] Meta description: 170+ chars, includes keywords ("licitacoes publicas", "setor", "regiao", "valor", "IA", "500+ empresas")
- [PASS] 9 keyword entries targeting long-tail conversational queries (aligned with Google AI Search trends)
- [PASS] `lang="pt-BR"` on HTML tag
- [PASS] Viewport configured explicitly (`device-width, initial-scale: 1`)
- [PASS] Google Search Console verification token present
- [PASS] Robots directives: `index: true, follow: true`, with googleBot-specific max-preview settings

**Per-page metadata:**
| Page | Has metadata? | Title quality |
|------|:---:|---|
| `/` (layout) | Yes | Excellent -- targets "encontrar e vencer licitacoes" |
| `/features` | Yes | Good -- "O Que Muda no Seu Resultado" (transformation framing) |
| `/termos` | Yes | Adequate |
| `/privacidade` | Yes | Adequate |
| `/planos` | NO | Missing -- client component, no metadata export |
| `/ajuda` | NO | Missing -- client component, no metadata export |
| `/buscar` | NO | Missing -- client component, no metadata export |

**Verdict: 7/10** -- Root metadata is strong, but 3 important public pages lack custom metadata.

### 1.4 Canonical URLs

- [PASS] Root canonical set: `alternates.canonical: "https://smartlic.tech"`
- [ISSUE] Only root page has canonical -- `/features`, `/planos`, `/ajuda` do not declare their own canonical URLs, risking duplicate content issues if accessed via multiple URLs (e.g., `smartlic.tech` vs `bidiq-frontend-production.up.railway.app`)

**Verdict: 5/10** -- Root only; per-page canonicals missing.

### 1.5 Open Graph / Social Sharing

- [PASS] Full OG tags: title, description, siteName, url, type=website, locale=pt_BR
- [PASS] OG image specified: `/og-image.png` (1200x630 -- correct dimensions)
- [CRITICAL] `og-image.png` does not exist in `frontend/public/` -- social shares will show no image
- [PASS] Twitter Card: `summary_large_image` with title, description, image
- [ISSUE] Twitter `@smartlic` handle may not be claimed/active
- [ISSUE] Logo referenced in structured data (`https://smartlic.tech/logo.png`) does not exist in `frontend/public/`

**Verdict: 4/10** -- Tags are correct but referenced assets are missing. Social sharing is broken.

### 1.6 Security Headers (SEO-adjacent)

**File:** `frontend/next.config.js`

- [PASS] HSTS: `max-age=31536000; includeSubDomains`
- [PASS] X-Content-Type-Options: `nosniff`
- [PASS] X-Frame-Options: `DENY`
- [PASS] Content-Security-Policy: comprehensive
- [PASS] Referrer-Policy: `strict-origin-when-cross-origin` (good for SEO -- passes referrer data to same-origin)

**Verdict: 9/10** -- Excellent security posture, which contributes to E-E-A-T trust signals.

---

## 2. Structured Data (Schema.org)

**File:** `frontend/app/components/StructuredData.tsx`

### 2.1 Organization Schema
```json
{
  "@type": "Organization",
  "name": "SmartLic",
  "url": "https://smartlic.tech",
  "logo": "https://smartlic.tech/logo.png",  // MISSING FILE
  "foundingDate": "2025",
  "contactPoint": { "email": "contato@smartlic.tech" },
  "sameAs": ["https://www.linkedin.com/company/smartlic"]  // Verify exists
}
```
- [PASS] Valid structure
- [ISSUE] Logo URL returns 404
- [ISSUE] LinkedIn profile may not exist

### 2.2 WebSite Schema with SearchAction
```json
{
  "@type": "WebSite",
  "potentialAction": {
    "@type": "SearchAction",
    "target": "https://smartlic.tech/buscar?q={search_term_string}"
  }
}
```
- [PASS] Enables Google sitelinks searchbox
- [ISSUE] `/buscar` requires authentication -- SearchAction will fail for non-logged-in users. Google may drop the sitelinks searchbox.

### 2.3 SoftwareApplication Schema
```json
{
  "@type": "SoftwareApplication",
  "applicationCategory": "BusinessApplication",
  "offers": { "price": "1999.00", "priceCurrency": "BRL" },
  "aggregateRating": { "ratingValue": "4.8", "reviewCount": "127" }
}
```
- [CRITICAL] **Fabricated reviews** -- `aggregateRating` claims 127 reviews with 4.8 rating. There are no actual user reviews on the platform. This violates Google's structured data guidelines and can result in a manual penalty.
- [PASS] Price information correct (R$1,999)
- [PASS] Feature list present

### 2.4 Missing Structured Data
- [MISSING] **FAQPage schema** -- `/ajuda` has 20+ FAQ items but no structured data markup. This is a significant missed opportunity for rich snippet SERP features.
- [MISSING] **BreadcrumbList** -- No breadcrumb schema on any page
- [MISSING] **LocalBusiness** or more specific organization type
- [MISSING] **HowTo schema** for "Como funciona" section

**Verdict: 4/10** -- Foundation present but fabricated reviews are a penalty risk and significant opportunities are missed.

---

## 3. E-E-A-T Signals (Experience, Expertise, Authoritativeness, Trustworthiness)

### 3.1 Experience
- [MISSING] No case studies or customer success stories
- [MISSING] No real testimonials (the AnalysisExamplesCarousel shows fabricated analysis examples, not user testimonials)
- [MISSING] No user-generated content
- [WEAK] No screenshots or video demos of actual product usage

### 3.2 Expertise
- [MISSING] No "About" page (`/sobre` does not exist)
- [MISSING] No team bios or author credentials
- [MISSING] No industry expertise articles or educational content
- [WEAK] Footer claims "Sistema desenvolvido por servidores publicos" but provides no details
- [PARTIAL] FAQ page (`/ajuda`) demonstrates some domain knowledge

### 3.3 Authoritativeness
- [MISSING] No blog (`/blog` does not exist)
- [MISSING] No backlink strategy or content marketing
- [MISSING] No press mentions or media coverage
- [MISSING] No partnerships or official endorsements
- [WEAK] LinkedIn profile may not exist or be inactive

### 3.4 Trustworthiness
- [PASS] LGPD compliance badge in footer
- [PASS] Privacy policy page exists (`/privacidade`)
- [PASS] Terms of service page exists (`/termos`)
- [PASS] Cookie consent banner
- [PASS] HTTPS with HSTS
- [PASS] Data source transparency section in footer
- [PASS] Contact email provided (suporte@smartlic.tech)
- [CRITICAL] Fabricated review count (127 reviews) in structured data -- undermines trust
- [ISSUE] Claims "500+ empresas" in meta description -- unverifiable, potentially misleading

**Verdict: 3/10** -- Trust signals are present, but E-E-A-T is fundamentally weak due to absence of expertise content, team visibility, and verifiable social proof.

---

## 4. Content Coverage & Keyword Targeting

### 4.1 Target Keywords Analysis

| Primary Keyword | Monthly Volume (est.) | Title Tag? | H1? | Body Content? |
|---|---|:---:|:---:|:---:|
| editais licitacoes | High | Partial ("licitacoes") | No | Minimal |
| busca licitacoes | High | Yes (meta desc) | No | Minimal |
| pregao eletronico | High | No | No | No |
| monitoramento licitacoes | Medium | Partial ("alertas") | No | No |
| como ganhar licitacoes | Medium | Yes (title) | Yes | Yes |
| licitacoes PNCP | Medium | No (GTM-007 sanitized) | No | No |
| compras governamentais | Medium | Yes (keyword) | No | Minimal |
| sistema licitacoes | Medium | Yes (keyword) | No | Minimal |
| portal licitacoes | Low-Med | No | No | No |

**Critical gap:** The site does not use the highest-volume head terms ("editais", "pregao eletronico") anywhere in its H1 or primary heading structure. The H1 on homepage is "Saiba Onde Investir para Ganhar Mais Licitacoes" -- excellent for conversion copy but weak for informational search intent.

### 4.2 Content Depth Assessment

| Page | Word Count (est.) | Crawlable? | SEO Value |
|---|---|:---:|---|
| `/` (landing) | ~800 | Yes (SSR components) | High but thin |
| `/features` | ~500 | Yes (SSR + client) | Medium |
| `/planos` | ~400 | Partial (client-only) | Low -- no metadata |
| `/ajuda` | ~2000+ | Partial (client-only) | Low -- no metadata, no FAQ schema |
| `/privacidade` | ~1500 | Yes | Low (legal) |
| `/termos` | ~1500 | Yes | Low (legal) |

**Total unique, crawlable content pages: 6** (vs. competitors with 100s-1000s of pages)

### 4.3 Content Marketing Gap

- [MISSING] **Blog**: No `/blog` directory. Zero educational/informational content.
  - Missing opportunities: "como participar de pregao eletronico", "o que e PNCP", "guia licitacoes para PMEs", "passo a passo licitacoes publicas"
  - These long-tail queries drive top-of-funnel traffic for procurement SaaS
- [MISSING] **Glossary**: No procurement terminology glossary (licitacao, pregao, tomada de precos, etc.)
- [MISSING] **Industry reports**: No sector-specific data or analysis publications
- [MISSING] **Landing pages per sector**: 15 sectors served but no dedicated `/setores/uniformes`, `/setores/saude`, etc.
- [MISSING] **Geographic pages**: 27 states covered but no `/licitacoes/sao-paulo`, etc.

**Verdict: 2/10** -- Extremely thin content. Only 6 crawlable pages. No content marketing strategy. Cannot compete for organic search.

---

## 5. Mobile-First Assessment

### 5.1 Responsive Design
- [PASS] Tailwind CSS with full responsive breakpoint system (`sm:`, `md:`, `lg:`)
- [PASS] All landing sections use responsive grid (`grid-cols-1 md:grid-cols-3`, etc.)
- [PASS] Touch targets: hamburger menu is 44x44px minimum (`min-h-[44px] min-w-[44px]`)
- [PASS] Font display: `swap` on all Google Fonts (prevents FOIT)
- [PASS] Mobile menu component with overlay and animation
- [PASS] Skip navigation link for accessibility (`sr-only focus:not-sr-only`)
- [PASS] Cards adapt from multi-column (desktop) to single-column (mobile)
- [PASS] ComparisonTable has card-based layout for mobile (`hidden md:block` table / `md:hidden` cards)

### 5.2 Font Sizes
- [PASS] Base font size: `1rem` with `lineHeight: 1.6`
- [PASS] Headings scale responsively: `text-4xl sm:text-5xl lg:text-6xl`
- [PASS] Body text uses `text-sm` (14px) to `text-lg` (18px) range

### 5.3 Performance Signals (Code-level)
- [PASS] `output: 'standalone'` in next.config.js (smaller deployment footprint)
- [PASS] Google Analytics loaded `afterInteractive` (not blocking)
- [PASS] Framer Motion used for animations (tree-shakeable)
- [ISSUE] Multiple large SVG icons inlined in components (not using sprite sheet or icon component library efficiently)
- [ISSUE] `framer-motion` adds ~30KB to bundle -- could impact LCP on slow connections

**Verdict: 8/10** -- Mobile-first is well-implemented at the code level. Minor performance concerns.

---

## 6. Content Freshness & Dynamic Content

- [ISSUE] No visible "last updated" dates on any page
- [ISSUE] All sitemap lastmod timestamps are identical (build-time)
- [ISSUE] No dynamic content generation (blog, reports, updated stats)
- [ISSUE] Landing page stats ("15 setores", "1000+ regras", "27 estados") are hardcoded -- no evidence of freshness
- [PARTIAL] Analysis examples carousel shows curated examples (static, not real-time)
- [PASS] `changefreq: daily` set for key pages in sitemap (but meaningless without actual daily changes)

**Verdict: 2/10** -- Static site with no freshness signals. Google may deprioritize stale content.

---

## 7. Google Analytics & Measurement

- [PASS] GA4 integration with LGPD-compliant consent gate
- [PASS] Custom event tracking: search, download, signup, login, plan selection
- [PASS] `anonymize_ip: true` for privacy compliance
- [ISSUE] GA only fires after cookie consent -- may lose significant measurement data
- [ISSUE] No Google Search Console data integration (verification token present but cannot verify actual GSC setup from code)

**Verdict: 7/10** -- Well-implemented measurement, consent-aware.

---

## 8. Critical SEO Risks

### 8.1 Fabricated Structured Data (SEVERITY: CRITICAL)
The `SoftwareApplication` schema claims `aggregateRating: { ratingValue: 4.8, reviewCount: 127 }`. These reviews do not exist. Google explicitly penalizes fabricated structured data with:
- Manual action (removal from rich results)
- Potential site-wide ranking demotion
- Loss of structured data eligibility

**Recommendation:** Remove `aggregateRating` immediately until real reviews exist.

### 8.2 Missing OG Image (SEVERITY: HIGH)
`og-image.png` is referenced in metadata but does not exist in `frontend/public/`. Every social share will show a broken/missing preview image, severely impacting click-through from social channels.

### 8.3 Missing Logo File (SEVERITY: MEDIUM)
`logo.png` referenced in Organization schema does not exist. Schema validation will flag this.

### 8.4 Auth-Gated Pages in Sitemap (SEVERITY: MEDIUM)
8 of 22 sitemap URLs require authentication (`/buscar`, `/dashboard`, `/pipeline`, `/historico`, `/conta`, `/mensagens`, `/planos/obrigado`, `/recuperar-senha`). Googlebot will encounter login walls or redirects, generating soft 404s and wasting crawl budget.

---

## 9. Competitive Position Assessment

SmartLic competes in the "licitacoes" search space against:

1. **Licitanet** -- Years of domain authority, thousands of indexed pages, blog content
2. **ComprasNet/ComprasGov** -- Official government portal, ultimate authority
3. **LicitaWeb** -- Established content marketing, glossary, guides
4. **Portal de Compras** -- Integrated source but also a competitor for searches
5. **Licitacao.net** -- Large backlink profile, educational content

SmartLic has:
- ~6 crawlable pages vs. competitors with 100-10,000+
- No blog vs. competitors with years of content
- No backlinks vs. established domain authority
- Brand-new domain (2025/2026) vs. domains with 10+ years of history
- No reviews or testimonials vs. established trust signals

**Realistic organic ranking probability for "editais licitacoes" in next 6 months: < 5%**

---

## 10. Scoring Breakdown

| Sub-dimension | Score | Weight | Weighted |
|---|:---:|:---:|:---:|
| Technical SEO (sitemap, robots, meta) | 6 | 20% | 1.2 |
| Structured Data | 4 | 10% | 0.4 |
| E-E-A-T Signals | 3 | 20% | 0.6 |
| Content Coverage & Keywords | 2 | 25% | 0.5 |
| Mobile-First | 8 | 10% | 0.8 |
| Content Freshness | 2 | 10% | 0.2 |
| Measurement / Analytics | 7 | 5% | 0.35 |
| **TOTAL** | | **100%** | **4.05 -> 5/10** |

Rounded up to **5/10** because the technical foundation is competent and correctable -- the gap is strategic (content), not structural.

---

## 11. Recommendations (Priority Order)

### P0: Immediate (before launch)
1. **Remove fabricated `aggregateRating`** from StructuredData.tsx -- penalty risk
2. **Create and deploy `og-image.png`** (1200x630) to `frontend/public/`
3. **Create and deploy `logo.png`** to `frontend/public/`
4. **Remove auth-gated pages from sitemap** (`/buscar`, `/dashboard`, `/pipeline`, `/historico`, `/conta`, `/mensagens`) or create public-facing versions
5. **Add metadata to `/planos`, `/ajuda`** -- these are high-value public pages without titles

### P1: Short-term (1-2 weeks)
6. **Add FAQPage structured data** to `/ajuda` -- immediate rich snippet opportunity
7. **Add per-page canonical URLs** to `/features`, `/planos`, `/ajuda`
8. **Fix `icon.png` and `sitemap.xml` entries** in sitemap
9. **Add BreadcrumbList schema** across all pages
10. **Remove `"500+ empresas"` claim** from meta description until verifiable

### P2: Medium-term (1-2 months)
11. **Create a blog** at `/blog` with 10-20 foundational articles targeting:
    - "como participar de licitacoes publicas" (guide)
    - "o que e pregao eletronico" (educational)
    - "dicas para vencer licitacoes" (intent-matching)
    - "PNCP como funciona" (topical authority)
    - Per-sector guides: "licitacoes uniformes", "licitacoes TI"
12. **Create sector landing pages** (`/setores/[slug]`) for each of the 15 sectors
13. **Create state landing pages** (`/licitacoes/[estado]`) for high-volume states (SP, RJ, MG, etc.)
14. **Add an About/Sobre page** with team info, mission, expertise credentials

### P3: Long-term (3-6 months)
15. **Content marketing program** -- 2-4 blog posts per month
16. **Backlink acquisition** -- Guest posts on procurement/business blogs
17. **Google Business Profile** if applicable
18. **Real user reviews** -- Integrate review collection flow post-trial

---

## 12. Final Verdict

**Score: 5/10 -- SEO Foundations**

SmartLic has built a technically competent SEO foundation (meta tags, sitemap, structured data, canonical URL, responsive design, GA4). However, the site is critically deficient in content depth, E-E-A-T signals, and competitive content strategy. With only 6 crawlable pages, no blog, no educational content, fabricated review data, and missing OG assets, the site cannot realistically rank for any competitive procurement keyword in Brazil.

The good news: the technical base is solid. The gap is entirely in content strategy, which can be addressed systematically. The P0 items (removing fabricated data, adding missing assets) should be done immediately to avoid Google penalties. The P2 items (blog, sector pages) are the most impactful for long-term organic discovery.

**Path to 7/10:** Fix P0 + P1 items + launch blog with 10 articles + create sector landing pages (~4-6 weeks of work).
**Path to 9/10:** All of the above + sustained content marketing + backlink program + real reviews (~6-12 months).
