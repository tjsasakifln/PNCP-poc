# MKT-004 — Panorama Pages: GSC Validation Report

**Date:** 2026-03-02
**Scope:** 15 panorama pages (pillar pages, 1 per sector)
**Status:** Pre-deployment validation

## Panorama URLs (15 total)

| # | URL | Schema Types | Meta | Content | Status |
|---|-----|-------------|------|---------|--------|
| 1 | /blog/panorama/informatica | FAQPage+Dataset+Article+HowTo+Breadcrumb | OK | 2500+ words | Ready |
| 2 | /blog/panorama/saude | FAQPage+Dataset+Article+HowTo+Breadcrumb | OK | 2500+ words | Ready |
| 3 | /blog/panorama/engenharia | FAQPage+Dataset+Article+HowTo+Breadcrumb | OK | 2500+ words | Ready |
| 4 | /blog/panorama/facilities | FAQPage+Dataset+Article+HowTo+Breadcrumb | OK | 2500+ words | Ready |
| 5 | /blog/panorama/software | FAQPage+Dataset+Article+HowTo+Breadcrumb | OK | 2500+ words | Ready |
| 6 | /blog/panorama/vestuario | FAQPage+Dataset+Article+HowTo+Breadcrumb | OK | 2500+ words | Ready |
| 7 | /blog/panorama/alimentos | FAQPage+Dataset+Article+HowTo+Breadcrumb | OK | 2500+ words | Ready |
| 8 | /blog/panorama/mobiliario | FAQPage+Dataset+Article+HowTo+Breadcrumb | OK | 2500+ words | Ready |
| 9 | /blog/panorama/vigilancia | FAQPage+Dataset+Article+HowTo+Breadcrumb | OK | 2500+ words | Ready |
| 10 | /blog/panorama/transporte | FAQPage+Dataset+Article+HowTo+Breadcrumb | OK | 2500+ words | Ready |
| 11 | /blog/panorama/papelaria | FAQPage+Dataset+Article+HowTo+Breadcrumb | OK | 2500+ words | Ready |
| 12 | /blog/panorama/manutencao-predial | FAQPage+Dataset+Article+HowTo+Breadcrumb | OK | 2500+ words | Ready |
| 13 | /blog/panorama/engenharia-rodoviaria | FAQPage+Dataset+Article+HowTo+Breadcrumb | OK | 2500+ words | Ready |
| 14 | /blog/panorama/materiais-eletricos | FAQPage+Dataset+Article+HowTo+Breadcrumb | OK | 2500+ words | Ready |
| 15 | /blog/panorama/materiais-hidraulicos | FAQPage+Dataset+Article+HowTo+Breadcrumb | OK | 2500+ words | Ready |

## Validation Results

### Schema Validation (Unit Tests)
- 41 frontend tests passing (mkt-004-panorama.test.tsx)
- Schema types validated: Article, FAQPage, Dataset, HowTo, BreadcrumbList
- All 15 sectors: editorial content + panorama editorial present
- 7 FAQs per page (40-60 words each answer)
- TypeScript compiles cleanly (`tsc --noEmit`)

### Meta Tags (per AC4)
- **Title pattern:** "Panorama de Licitações de {Setor} no Brasil — 2026 | SmartLic"
- **OG type:** article
- **Canonical URL:** https://smartlic.tech/blog/panorama/{setor}
- **Twitter card:** summary_large_image

### Content Quality (per AC3)
- Each page has 5 editorial sections: contexto, dicas, perfil comprador, casos de uso, tendências 2026
- Base editorial content (getEditorialContent) + panoramaEditorial = 2500+ words
- 7 sector-specific FAQs per page
- Data sections: stats grid, top 5 UFs, modalidades %, sazonalidade chart, faixa de valores

### Internal Linking (per AC5)
- Each panorama links to all 27 UF pages for its sector
- Links to related panoramas (3 sectors)
- Links to editorial posts (via RelatedPages component)
- Setor×UF pages link BACK to /blog/panorama/ (RelatedPages updated)
- Bidirectional linking confirmed

### Sitemap Integration
- 15 panorama URLs added to sitemap-blog.xml with priority 0.8
- Pillar pages get highest priority after blog listing (0.9)
- changefreq: daily
- ISR revalidation: 24h (86400s)

### Regression Check
- MKT-003 tests: 144/144 passing (zero regressions)
- Full frontend suite: 4334 passing (63 pre-existing failures, unrelated)
- TypeScript: clean

## Post-Deploy GSC Actions (AC7)

### Step 1: Request Indexation (immediately after deploy)
- [ ] Submit updated sitemap-blog.xml via GSC
- [ ] Request indexation for each of the 15 panorama URLs via GSC URL Inspection
- [ ] Priority: pillar pages should index within 3-7 days

### Step 2: Rich Results Test (1-2 days after deploy)
- [ ] Submit each URL in https://search.google.com/test/rich-results
- [ ] Validate FAQPage detected
- [ ] Validate Dataset detected
- [ ] Validate Article detected
- [ ] Validate HowTo detected
- [ ] Report 0 errors, 0 warnings

### Step 3: Indexation Verification (7 days after deploy)
- [ ] Re-inspect all 15 URLs via GSC URL Inspection
- [ ] Confirm "URL is on Google" status
- [ ] Check for any crawl errors or warnings

### Step 4: Performance Monitoring (14+ days)
- [ ] Export GSC performance data filtered by /blog/panorama/
- [ ] Monitor impressions, clicks, CTR, avg position
- [ ] Compare with MKT-003 licitacoes pages performance

## Launch Phases (per AC6)

### Phase 1 (Weeks 1-2): 5 largest sectors
- informatica, saude, engenharia, facilities, software

### Phase 2 (Weeks 3-4): 5 intermediate sectors
- vestuario, alimentos, mobiliario, vigilancia, transporte

### Phase 3 (Month 2): 5 remaining sectors
- papelaria, manutencao-predial, engenharia-rodoviaria, materiais-eletricos, materiais-hidraulicos

**Note:** All 15 pages are implemented and deployed simultaneously. The phased approach refers to GSC indexation requests and performance monitoring priority.
