# EPIC-SEO-PROG-2026-Q2 — SEO Programático Escalável (Tese 100% Inbound)

**Status:** Draft
**Owner:** @architect (Aria) + @ux-design-expert (Uma) + @dev (Dex)
**Quality Gate:** @qa (Quinn)
**Sprint Window:** 2026-04-29 → 2026-06-30 (9 semanas, 5 sprints)
**Origem:** Auditoria sistêmica + pivô estratégico 2026-04-26 — plano `/home/tjsasakifln/.claude/plans/sistema-est-amea-ado-por-serene-hanrahan.md`

---

## Context

Em 2026-04-26 SmartLic pivotou para **estratégia 100% inbound via SEO programático** com páginas de elevado valor agregado, descartando outreach off-page. Baseline GSC 28d: **126 clicks, 9.9k impressions, CTR 1.3%, position 7.1**. Backlog de conversão trial→paid permanece bloqueado até `n≥30` (atualmente n=2/30d, abaixo do noise floor estatístico).

Auditoria do frontend identificou 8 rotas dinâmicas em **SSR puro** (`generateStaticParams = []` ou ausente, `revalidate = undefined`):

- `/cnpj/[cnpj]` — perfil de fornecedor (~5k CNPJs ativos no sitemap)
- `/orgaos/[slug]` — órgão público (~2k órgãos)
- `/itens/[catmat]` — item CATMAT (~10k itens, universo total ~500k)
- `/observatorio/[slug]` — análise editorial (Dataset CC-BY com JSON-LD)
- `/fornecedores/[cnpj]/[uf]` — perfil fornecedor × UF (2-segment dinâmico)
- (mais 3 rotas dinâmicas com `generateStaticParams = []`)

Cada request crawler nessas rotas dispara 1+ fetches ao backend → soma 6+ fetches simultâneos no SSG fan-out de `sitemap.ts` (786L) → cenário precursor do incidente PR #529 quando combinado com Googlebot wave.

Pipeline `sitemap.ts` já tem ISR 1h + AbortSignal.timeout(15s) + serialização (correção pós SEN-FE-001), mas:

- **Cap Google 50k URLs/sitemap** — atual ~10k em `sitemap/4.xml`; margem 5x antes de hit do limite.
- **`robots.ts` route handler ausente** — apenas `robots.txt` estático, sem control granular por env (prod/preview).
- **`Dockerfile` ARG `BACKEND_URL`** com gap conhecido em Railway service variables (sitemap build hits localhost:8000 se var ausente).
- **Bundle 1.75MB gzipped** com target -600KB (continuação STORY-5.14).
- **WSL build inviável** para >3k pages (memory: usa `--experimental-build-mode=compile` ou CI-only).

Conteúdo das páginas indexadas é tecnicamente sólido (H1 único, meta description dinâmica, JSON-LD `BreadcrumbList`/`Dataset`/`Organization`, narrativa textual, gráficos Recharts, FAQs, internal linking parcial via `<RelatedPages />` em alguns templates). Não há "thin content" detectado — gap está em **infra de escala**, não em qualidade editorial.

---

## Goal

Migrar 8 rotas dinâmicas SSR puro para ISR + fallback blocking, particionar sitemap para suportar 1M URLs e instituir `robots.ts` dinâmico em até 5 sprints (9 semanas).

---

## Business Value

- **Habilita escala 100x (10k → 1M páginas projetadas em 9-12 meses)** sem reincidir incidente Googlebot.
- **Aumenta CTR 1.3% → 3.0%+** via velocidade (LCP < 2.5s p75) e schema.org expandido (rich results).
- **Sustenta tese 100% inbound** — sem isto, off-page descartado torna-se decisão fatal.
- **Reduz custo backend** — ISR cacheia ao invés de recomputar a cada request crawler.
- **Habilita observabilidade SEO unificada** — GSC API ingest cross-validado com Mixpanel cria ciclo de feedback editorial-quantitativo.

---

## Success Metrics (binários ou numéricos pós-Sprint 6)

| # | Métrica | Baseline | Target | Fonte |
|---|---|---|---|---|
| 1 | Rotas SSR puro indexáveis (sem `generateStaticParams`) | 8 | 0 | code audit + Lighthouse |
| 2 | LCP p75 top-10 rotas SEO (CrUX) | desconhecido | < 2.5s | Lighthouse CI + CrUX |
| 3 | INP p75 top-10 rotas SEO | desconhecido | < 200ms | Lighthouse CI |
| 4 | CLS p75 top-10 rotas SEO | desconhecido | < 0.1 | Lighthouse CI |
| 5 | GSC clicks 28d | 126 | ≥ 500 (4x) | GSC API |
| 6 | GSC CTR 28d | 1.3% | ≥ 2.5% | GSC API |
| 7 | Sitemap render time (50k URLs) | desconhecido | < 5s | Sentry breadcrumb |
| 8 | Bundle gzipped | 1.75MB | < 1.15MB | `.size-limit.js` |
| 9 | Sitemap-vs-GSC URL count delta | desconhecido | < 5% | reconciliação script |

---

## Constraints

- **Next.js 16 ISR semantics** — `revalidate` (em segundos) + `dynamicParams=true` (fallback blocking); cuidado com cache alignment (precedente memory: ISR + `cache: 'no-store'` quebra SSG).
- **Cap Google 50k URLs/sitemap** — paginar via `sitemap_index.xml` antes de hit.
- **WSL build inviável >3k pages** — defer build output validation para CI; dev local usa `--experimental-build-mode=compile` se disponível.
- **Railway frontend memory** — build OOM possível em monorepo 3k+ pages; investigar antes de subir cap SSG.
- **Bundle budget 1.75MB hold-the-line** durante migração; redução via STORY-5.14 (continuação).
- **n=2 baseline** impede A/B SEO empírico; decisões via Lighthouse score + GSC delta histórico.
- **Backend dependência:** SEO-PROG-001..005 dependem de RES-BE-002 estar deployado em staging.

---

## Stories deste Epic

| ID | Título | Prio | Esforço | Sprint | Dep |
|---|---|---|---|---|---|
| [SEO-PROG-001](SEO-PROG-001-cnpj-ssr-to-isr.md) | Migrar `cnpj/[cnpj]` SSR→ISR (top-1000 + fallback blocking) | P0 | M | 1-2 | RES-BE-002 |
| [SEO-PROG-002](SEO-PROG-002-orgaos-ssr-to-isr.md) | Migrar `orgaos/[slug]` SSR→ISR (top-2000) | P0 | M | 2 | RES-BE-002 |
| [SEO-PROG-003](SEO-PROG-003-itens-ssr-to-isr.md) | Migrar `itens/[catmat]` SSR→ISR (top-5000) | P0 | M | 2 | RES-BE-002 |
| [SEO-PROG-004](SEO-PROG-004-observatorio-ssr-to-isr.md) | Migrar `observatorio/[slug]` SSR→ISR (todos slugs ativos) | P0 | S | 2 | RES-BE-002 |
| [SEO-PROG-005](SEO-PROG-005-fornecedores-2seg-ssr-to-isr.md) | Migrar `fornecedores/[cnpj]/[uf]` SSR→ISR (top-1000 pares) | P0 | M | 3 | RES-BE-002 |
| [SEO-PROG-006](SEO-PROG-006-sitemap-partitioned-index.md) | Sitemap particionado + `sitemap_index.xml` (45k URLs/child) | P0 | L | 2-3 | RES-BE-002 |
| [SEO-PROG-007](SEO-PROG-007-robots-ts-dynamic.md) | `robots.ts` dinâmico Next.js 16 (env-aware) | P0 | S | 3 | SEO-PROG-006 |
| [SEO-PROG-008](SEO-PROG-008-dockerfile-backend-url.md) | Verificar `Dockerfile` ARG `BACKEND_URL` Railway | P0 | S | 1 | — |
| [SEO-PROG-009](SEO-PROG-009-bundle-reduction-600kb.md) | Bundle reduction -600KB (continuação STORY-5.14) | P1 | L | 4-5 | — |
| [SEO-PROG-010](SEO-PROG-010-lighthouse-ci-budget.md) | Lighthouse CI gate (LCP/INP/CLS budget) | P1 | M | 4 | SEO-PROG-009 |
| [SEO-PROG-011](SEO-PROG-011-internal-linking-component.md) | Internal linking automatizado `<RelatedPages />` | P1 | M | 4-5 | SEO-PROG-001..005 |
| [SEO-PROG-012](SEO-PROG-012-schema-org-expansion.md) | Schema.org expansion (FAQPage, Organization, BreadcrumbList) | P2 | M | 5 | SEO-PROG-001..005 |
| [SEO-PROG-013](SEO-PROG-013-gsc-api-ingest.md) | GSC API ingestion → Mixpanel + dashboard | P2 | M | 6 | — |
| [SEO-PROG-014](SEO-PROG-014-defer-build-validation-ci.md) | Defer build SSG output validation para CI (workaround WSL) | P2 | S | 6 | — |

---

## Sequenciamento Crítico

```
Sprint 1 (29/abr–05/mai):  SEO-PROG-008 (BACKEND_URL audit) ← independente
                           [bloqueado por RES-BE-002 em staging]
Sprint 2 (06–12/mai):      SEO-PROG-001, SEO-PROG-002, SEO-PROG-003, SEO-PROG-004 (paralelos)
                           SEO-PROG-006 (sitemap particionado)
Sprint 3 (13–19/mai):      SEO-PROG-005 (2-segment)
                           SEO-PROG-007 (robots.ts depende de 006)
Sprint 4 (20–26/mai):      SEO-PROG-009 (bundle), SEO-PROG-011 (internal linking)
Sprint 5 (27/mai–02/jun):  SEO-PROG-010 (Lighthouse CI), SEO-PROG-012 (schema)
Sprint 6 (03–09/jun):      SEO-PROG-013 (GSC ingest), SEO-PROG-014 (CI defer)
```

---

## Validation Framework

### Lighthouse CI thresholds (PR gate)

```yaml
budgets:
  LCP: 2500 # ms (p75)
  INP: 200  # ms (p75)
  CLS: 0.1  # score (p75)
  TTFB: 600 # ms (p75)
fail_threshold: 3 # rotas amostradas excedendo
sample_routes:
  - /cnpj/{cnpj_top}
  - /orgaos/{slug_top}
  - /itens/{catmat_top}
  - /observatorio/{slug_evergreen}
  - /blog/licitacoes/{setor_top}/{uf_top}
```

### GSC reconciliação (semanal)

- Sitemap URLs declaradas vs GSC "submitted" — delta < 5%
- "Discovered, not indexed" + "Crawled, not indexed" — alarme se > 30% de submitted

### Prometheus

- `nextjs_isr_revalidate_total{route}` — confirma ISR funcionando
- `sitemap_render_seconds{shard}` — < 5s p99
- `frontend_build_duration_seconds` — < 12min CI

### Rich Results Test

- Validação automática (Google Rich Results Test API) no CI para JSON-LD em rotas indexáveis
- Failure → PR block

---

## Rollback Strategy

| Trigger | Ação |
|---|---|
| LCP p75 > 3.5s pós-deploy | `SEO_ROUTE_MODE=ssr` flag por rota; revert ISR específica |
| GSC clicks -30% em 7d | Revert PR; manter sitemap antigo congelado; investigar via GSC URL Inspection |
| Sitemap render > 10s | Reduzir cap URLs por shard; aumentar Redis cache TTL |
| Bundle > 1.75MB | Bloqueio CI via `.size-limit.js` (já existe); revert PR |
| Build OOM Railway | Reduzir SSG params (top-1000 → top-500); ativar `--experimental-build-mode=compile` |

---

## Out-of-Scope (deste Epic)

- **Off-page SEO (backlinks, PR, parcerias)** — pivô 2026-04-26 descartou.
- **Conteúdo editorial novo (blog posts manuais)** — produção contínua, escopo separado.
- **Tradução i18n** — Brasil-only por natureza Lei 14.133.
- **AMP / Web Stories** — formato declinante; não alinha com SEO B2G.
- **Algolia/search index para 1M páginas** — defer; ISR cobre escala atual.
- **CDN edge cache cross-region** — Railway/Vercel default suficiente até 1M.

---

## Dependencies (entrada)

- **EPIC-RES-BE-2026-Q2 RES-BE-002** deve estar em staging antes de SEO-PROG-001..005 (rotas backend protegidas com budget temporal).
- Plano aprovado: `/home/tjsasakifln/.claude/plans/sistema-est-amea-ado-por-serene-hanrahan.md`
- Stories existentes referenciadas: STORY-5.14 (bundle), STORY-OBS-001 (retention 400d), SEN-FE-001 (sitemap antipattern fix).

## Dependencies (saída)

- **EPIC-MON-FN-2026-Q2 MON-FN-006** consome eventos `page_view{route}` de SEO-PROG no funnel Mixpanel.

---

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Epic criado a partir do plano de auditoria + pivô on-page | @sm (River) |
