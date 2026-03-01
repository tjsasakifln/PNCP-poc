# MKT-003 Phase 1 — Indexation Validation Report

**Date:** 2026-03-01
**Phase:** 1 (25 pages: 5 setores × 5 UFs)
**Status:** Pre-deployment validation

## Phase 1 URLs (25 total)

| # | URL | Schema | Meta | Status |
|---|-----|--------|------|--------|
| 1 | /blog/licitacoes/informatica/sp | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 2 | /blog/licitacoes/informatica/rj | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 3 | /blog/licitacoes/informatica/mg | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 4 | /blog/licitacoes/informatica/pr | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 5 | /blog/licitacoes/informatica/rs | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 6 | /blog/licitacoes/saude/sp | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 7 | /blog/licitacoes/saude/rj | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 8 | /blog/licitacoes/saude/mg | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 9 | /blog/licitacoes/saude/pr | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 10 | /blog/licitacoes/saude/rs | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 11 | /blog/licitacoes/engenharia/sp | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 12 | /blog/licitacoes/engenharia/rj | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 13 | /blog/licitacoes/engenharia/mg | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 14 | /blog/licitacoes/engenharia/pr | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 15 | /blog/licitacoes/engenharia/rs | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 16 | /blog/licitacoes/facilities/sp | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 17 | /blog/licitacoes/facilities/rj | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 18 | /blog/licitacoes/facilities/mg | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 19 | /blog/licitacoes/facilities/pr | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 20 | /blog/licitacoes/facilities/rs | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 21 | /blog/licitacoes/software/sp | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 22 | /blog/licitacoes/software/rj | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 23 | /blog/licitacoes/software/mg | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 24 | /blog/licitacoes/software/pr | FAQPage+Dataset+BreadcrumbList | OK | Ready |
| 25 | /blog/licitacoes/software/rs | FAQPage+Dataset+BreadcrumbList | OK | Ready |

## Validation Results

### Schema Validation (Unit Tests)
- 144 frontend tests passing (mkt-003-licitacoes.test.tsx)
- SchemaMarkup: FAQPage (5 questions) + Dataset (4 data points) + BreadcrumbList (5 levels)
- All Phase 1 pages confirmed with correct JSON-LD structure

### Meta Tags
- Title format: "Licitações de {Setor} em {UF} — Editais Abertos {Ano} | SmartLic"
- Description includes edital count, data sources (PNCP, PCP, ComprasGov)
- Canonical URL: `/blog/licitacoes/{setor}/{uf}`
- OG tags: title, description, url, type=article, locale=pt_BR

### Backend API (Enhanced)
- 25 backend tests passing (test_blog_stats.py)
- SectorUfStats now includes: value_range_min, value_range_max, top_modalidades, trend_90d
- 6h InMemory cache TTL

### Sitemap
- sitemap.xml updated with 26 new entries (1 index + 25 Phase 1 pages)
- Priority: 0.8 for index, 0.7 for pages
- Changefreq: weekly for index, daily for pages

## GSC Scripts Available
- `mkt-003-gsc-indexation.spec.ts` — Request/verify indexation (GSC_RUN=1 / GSC_VERIFY=1)
- `mkt-003-schema-validation.spec.ts` — E2E schema validation for all 25 pages

## Next Steps
- [ ] Deploy to production
- [ ] Run `GSC_RUN=1 npx playwright test mkt-003-gsc-indexation` to request indexation
- [ ] Wait 7 days, run `GSC_VERIFY=1 npx playwright test mkt-003-gsc-indexation` to verify
- [ ] Run `GSC_RICH=1 npx playwright test mkt-003-gsc-indexation` for Rich Results Test
