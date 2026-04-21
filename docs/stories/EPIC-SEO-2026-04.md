# EPIC: SEO Observability & Programmatic Recovery — 2026 Q2

**Epic ID:** EPIC-SEO-2026-04
**Created:** 2026-04-21
**Owner:** @pm (Morgan) + @sm (River)
**Status:** 🔴 PLANNING
**Audit Source:** `/home/tjsasakifln/.claude/plans/elenque-todas-as-fragilidades-humble-dream.md`
**Squad:** aiox-seo

---

## Epic Overview

Recuperar ~92% do potencial long-tail orgânico não-indexado (descoberta crítica do audit SEO 2026-04-21) e elevar score SEO de **B+ (78/100)** para **A (88/100)** em 6 sprints.

O audit identificou 1 P0 verificado empiricamente (sitemap/4.xml vazio em produção) e ~12 gaps P1 de alto ROI. Esta epic consolida a execução em 8 stories priorizadas.

---

## Current State (Baseline — 2026-04-21)

### Métricas Verificadas Empiricamente

- **URLs indexadas no sitemap**: 1.210 (0.xml=39 + 1.xml=60 + 2.xml=810 + 3.xml=301 + **4.xml=0**)
- **Potencial declarado**: 15k-20k (`squads/aiox-seo/config/smartlic-overlay.yaml`)
- **Gap de indexação**: **~92%** do long-tail não descoberto pelo Googlebot
- **Causa raiz confirmada**: `BACKEND_URL` env var ausente no Railway frontend build → `fetch('http://localhost:8000/v1/sitemap/*')` falha → catch silencioso em `frontend/app/sitemap.ts:43-56` → shard 4 vazio

### Scores Estimados por Categoria (aiox-seo weights)

| Categoria | Peso | Score atual |
|-----------|------|-------------|
| On-page SEO | 25% | 82/100 |
| Technical SEO | 20% | 80/100 |
| Schema / Structured Data | 15% | 75/100 |
| Content Quality / E-E-A-T | 15% | 75/100 |
| Performance / CWV | 10% | 70/100 (não medido) |
| AI Visibility / GEO | 10% | 65/100 |
| Site Architecture | 5% | 82/100 |
| **Total** | 100% | **~78/100 (B+)** |

---

## Target State (Goals)

- **URLs indexadas**: 1.210 → **≥10.000** (+720%)
- **Score SEO**: 78/100 → **88/100** (A)
- **Observabilidade**: GSC API integrada + Prometheus metrics + Sentry alerts
- **Content velocity**: 70 posts `.tsx` → workflow MDX editável + 3 pillar pages

---

## Stories

| ID | Prioridade | Story Points | Agente | Descrição |
|----|-----------|--------------|--------|-----------|
| STORY-SEO-001 | 🔴 P0 | 5 SP | @devops + @dev | Fix sitemap/4.xml vazio em produção |
| STORY-SEO-002 | 🟠 P1 | 5 SP | @dev | Article/BlogPosting schema em /blog/[slug] |
| STORY-SEO-003 | 🟠 P1 | 3 SP | @dev | BreadcrumbList schema em 7 rotas dinâmicas |
| STORY-SEO-004 | 🟠 P1 | 2 SP | @dev | Fix pricing SoftwareApplication + Product schema /planos |
| STORY-SEO-005 | 🟠 P1 | 8 SP | @dev + @data-engineer | GSC API + dashboard /admin/seo |
| STORY-SEO-006 | 🟠 P1 | 2 SP | @dev | Vercel Speed Insights (CWV real) |
| STORY-SEO-007 | 🟠 P1 | 13 SP | @dev | Migração blog .tsx → .mdx |
| STORY-SEO-008 | 🟠 P1 | 13 SP | @dev + @ux-design-expert | 3 pillar pages topical authority |

**Total:** 51 SP · ~3 sprints

---

## Success Criteria

- [ ] `curl -sL https://smartlic.tech/sitemap/4.xml \| grep -c '<url>'` retorna ≥5.000
- [ ] GSC Coverage report mostra crescimento consistente em "Valid" pages
- [ ] Prometheus metric `smartlic_sitemap_urls_count{shard="4"} > 5000` + Sentry alert <100
- [ ] Rich Results Test PASS em 5 URLs de `/blog/*` (Article) + 7 rotas dinâmicas (BreadcrumbList)
- [ ] Vercel Speed Insights dashboard ativo com LCP/INP/CLS p75 reais
- [ ] `/admin/seo` mostra top 50 queries GSC + CTR por URL
- [ ] Blog migrado para MDX (70 posts) com zero regressão de URLs no sitemap
- [ ] 3 pillar pages (`/guia/licitacoes`, `/guia/lei-14133`, `/guia/pncp`) publicados e indexados

---

## Dependencies

- **Upstream**: Audit SEO concluído (2026-04-21) ✓
- **Downstream**: Roadmap Sprint 4+ (refinamentos: llms-full.txt, PNG logo, taxonomia tag/categoria) dependem deste epic.

---

## Risks

| Risk | Mitigation |
|------|-----------|
| Deploy Railway bloqueado (CRIT-080) | Manual `railway redeploy` ou coordenação @devops |
| MDX migration quebra 70 URLs → SEO drop | Preservar slugs idênticos; rodar sitemap-diff CI antes do merge |
| GSC API rate limits | Job ARQ com backoff + cache de 24h |
| Pillar pages thin content | 3-5k words mínimo + link graph validated via lighthouse |

---

## Related

- **Audit**: `/home/tjsasakifln/.claude/plans/elenque-todas-as-fragilidades-humble-dream.md`
- **Overlay SEO**: `squads/aiox-seo/config/smartlic-overlay.yaml`
- **Squad config**: `squads/aiox-seo/config.yaml`
- **Memory**: `project_cache_warming_deprecation.md` (contexto DataLake primário)
