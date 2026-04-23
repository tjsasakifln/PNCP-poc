# Session Handoff — Mutable-Simon: Max-ROI Week Execution (CI + Revenue SEO)

**Date:** 2026-04-22 (meio da tarde, pós-abundant-reddy)
**Codename:** mutable-simon
**Branch base inicial:** `docs/session-2026-04-22-abundant-reddy` (3 commits pending + untracked research doc)
**Duração:** ~4h YOLO mode (Wave A merge drain + Wave B pillar pages + Wave C GSC dashboard + Wave D review)
**Modelo:** Claude Opus 4.7 (1M context)

---

## TL;DR

Dia 1 da "semana max-ROI" consolidado em uma sessão só. **9 PRs mergeados**, **2 novas features SEO enviadas** (SEO-008 pillar pages com 11.6k palavras + SEO-005 GSC dashboard). Main CI 100% verde em required checks. Revenue funnel Mixpanel completo pós-#474. 3 novas stories SEO in-flight pós-validation.

---

## 1. Entregáveis

### Wave A — Merge Drain (✅ completa)

**Mergeados em main (9 PRs):**

| PR | SHA | Escopo | Impacto |
|----|-----|--------|---------|
| #473 | `d09578bf` | fix(test): JWT tamper determinístico | Destravou Tests Matrix (único failure em main) |
| #472 | `be58c335` | fix(ci): mkdir before supabase init migration-validate | Destravou TODOS PRs tocando migrations |
| #474 | `ee6f29f4` | feat(analytics): paywall_hit revenue tracking | **Completou funnel Mixpanel** signup→trial→paywall→checkout |
| #463 | `f5cbf276` | feat(seo-001/474/475): AC5/AC7 observability | Sentry + Prometheus em sitemap fetches |
| #464 | `ef63aa18` | docs(sessions): transient-hellman handoff | Docs-only |
| #475 | merged | docs(sessions): abundant-reddy handoff + PO validation | Inclui `c0d86545` (4 Drafts→Ready) |
| #462 | merged | docs(sessions): functional-lamport handoff | Docs-only |
| #469 | merged | test(countdown): stabilize fake timers | Previne flaky em CI |
| #468 | merged | feat(parity): CRIT-DATA-PARITY contract skeleton | Sprint 2 parity contracts |

**Estado pós-merge na main:**
- Required checks (Backend Tests + Frontend Tests PR Gate) 🟢 em 100% dos runs recentes
- Migration Check post-merge: SUCCESS (fix via #471 + #472)
- Tests Matrix integration: in_progress (long-running ~40min, não bloqueia)
- Revenue tracking funnel: completo em prod após deploy de #474

### Wave B — STORY-SEO-008 Pillar Pages (✅ shipada como PR #477)

**PR aberto:** https://github.com/tjsasakifln/PNCP-poc/pull/477

Implementação completa em `frontend/app/guia/[slug]/`:

| Rota | H1 | Palavras |
|------|----|---------:|
| `/guia/licitacoes` | Guia Completo de Licitações Públicas no Brasil | 3800 |
| `/guia/lei-14133` | Tudo Sobre a Lei 14.133/2021 | 4200 |
| `/guia/pncp` | PNCP: Portal Nacional de Contratações Públicas | 3600 |
| `/guia` | Hub que lista os 3 pillars | — |

**Cada pillar:**
- 4 JSON-LD schemas (Article + BreadcrumbList + ItemList + FAQPage)
- Sticky TOC via IntersectionObserver (scroll-mt-24)
- 10 internal spoke links para `/blog/*` (AC3)
- 5 outbound authority links (planalto, pncp, tcu, compras.gov, cgu)
- Inline trial CTA (data-testid=pillar-inline-cta, ref=pillar-inline-cta)
- E-E-A-T: Organization author, citation a fontes oficiais

**Sitemap shard 0:** +4 URLs (hub + 3 pillars, priority 0.9, changeFrequency monthly)

**E2E test:** `frontend/e2e-tests/pillar-pages.spec.ts` — H1 match, TOC ≥5 anchors, spokes ≥10 links, 4 JSON-LD types validados, robots indexable, CTA presente.

**Total:** ~11.6k palavras de conteúdo denso, com citações Lei 14.133 (arts. 5º, 28, 32, 62-70, 90-121, 134-137, 155-163, 174), dados do PNCP (~800B/ano), taxonomias de modalidade.

### Wave C — STORY-SEO-005 GSC Dashboard (✅ shipada como PR #478)

**PR aberto:** https://github.com/tjsasakifln/PNCP-poc/pull/478

**Backend:**
- Migration `gsc_metrics` com RLS (admin read + service write), GIN index em `query` tsvector
- ARQ weekly cron `backend/jobs/cron/gsc_sync.py` (domingo 06:00 UTC) — **graceful no-op** se `GSC_SERVICE_ACCOUNT_JSON` ausente
- Endpoint `GET /v1/admin/seo/summary?days={7,30,90}` → top_queries, top_pages_ctr, low_ctr_opportunities
- Prometheus: `smartlic_gsc_sync_duration_seconds` + `smartlic_gsc_sync_rows_upserted_total`
- 6 unit tests passando (disabled / missing creds / invalid JSON / row-to-record / happy path)

**Frontend:**
- Componente `GSCSummarySection` em `/admin/seo` com 3 tabelas + filtro 7/30/90d
- Empty state com instruções de setup (service account + env var)

**Activation path** (pós-merge, manual config do user):
1. Criar service account em Google Cloud + habilitar Search Console API
2. Adicionar JSON como `GSC_SERVICE_ACCOUNT_JSON` em Railway
3. Adicionar email da service account como user em GSC Settings → Users
4. Aguardar domingo → cron popula cache automaticamente

Sem configuração, é totalmente inerte (não quebra nada, apenas empty state + instruções).

### Wave D — PO validate drafts (✅ descoberta empírica: desnecessário)

Escopo original (advisor): validar STORY-431, 432, 433, 435, 436 (children EPIC-SEO-ORGANIC).

**Grep empírico revelou:**
- STORY-431, 432, 433, 435: **InProgress** (não Draft)
- STORY-436: **Done**

Então validation `*validate-story-draft` não se aplica — essas já saíram do Draft. Commit `c0d86545` (abundant-reddy) já havia movido EPIC-CI-GREEN, EPIC-INCIDENT, EPIC-SEO-ORGANIC, STORY-434 para Ready — mergeado em main via #475.

**Drafts remanescentes (41 total):** 30 MON-* (deferidos conscientemente, não são roadmap ativo esta semana), 8 EPIC-MON-*, EPIC.md dentro de EPIC-CI-RECOVERY, STORY-6.8 (BLOCKED at-source LATAM), outras.

Pattern `feedback_story_discovery_grep_before_implement` aplicado com sucesso → evitou retrabalho.

---

## 2. Estado atual da main e PRs abertos

**Main CI (2026-04-22 ~15:00 UTC):**

| Workflow | Estado |
|----------|--------|
| Backend Tests (PR Gate) | 🟢 |
| Frontend Tests (PR Gate) | 🟢 |
| Migration Check (Post-Merge) | 🟢 |
| Ingest LicitaJá | 🟢 |
| CodeQL Security Scan | 🟢 |
| Dep Scan | 🟢 |
| Chromatic Visual Regression | 🟢 |
| Deploy to Production (Railway) | 🟢 |
| Tests Matrix (Integration) | 🟡 long-running (~40min), não required |

**PRs abertos pós-sessão (7):**

| PR | Estado | Prioridade | Próxima ação |
|----|--------|-----------|-------------|
| #478 | CI rodando (BLOCKED 24 pending) | P1 SEO-005 | Merge quando required verdes |
| #477 | CI rodando (UNKNOWN 5 pending) | P1 SEO-008 | Merge quando required verdes |
| #476 | CI rodando (externa) | ? (docs research) | Revisar origem + merge |
| #470 | BEHIND → re-synced durante sessão | P2 uptime metric | Merge quando CI verde novamente |
| #459 | DIRTY (conflito main) | P3 BreadcrumbList licitacoes/[setor] | Investigar se já shipado alhures; fechar ou rebase |
| #420 | BEHIND (Dependabot google-auth) | P3 | Aguardar rebase automático via comment |
| #418 | BEHIND (Dependabot lucide-react) | P3 | Aguardar rebase automático |

---

## 3. Arquivos criados / modificados

### Wave B — Pillar Pages (PR #477)

| Arquivo | Tipo |
|---------|------|
| `frontend/lib/pillars.ts` | new (410 linhas) |
| `frontend/app/guia/page.tsx` | new (hub) |
| `frontend/app/guia/[slug]/page.tsx` | new (dynamic route + metadata + generateStaticParams) |
| `frontend/app/guia/_components/PillarPageLayout.tsx` | new |
| `frontend/app/guia/_components/TableOfContents.tsx` | new |
| `frontend/app/guia/_content/licitacoes.tsx` | new (3800 palavras) |
| `frontend/app/guia/_content/lei-14133.tsx` | new (4200 palavras) |
| `frontend/app/guia/_content/pncp.tsx` | new (3600 palavras) |
| `frontend/app/sitemap.ts` | modify (+4 URLs shard 0) |
| `frontend/e2e-tests/pillar-pages.spec.ts` | new |

### Wave C — GSC Dashboard (PR #478)

| Arquivo | Tipo |
|---------|------|
| `supabase/migrations/20260422120000_create_gsc_metrics.sql` | new |
| `supabase/migrations/20260422120000_create_gsc_metrics.down.sql` | new |
| `backend/jobs/cron/gsc_sync.py` | new |
| `backend/tests/test_gsc_sync.py` | new (6 unit tests) |
| `backend/routes/seo_admin.py` | modify (+GSC summary endpoint) |
| `backend/jobs/queue/config.py` | modify (register cron) |
| `backend/metrics.py` | modify (+2 Prometheus metrics) |
| `frontend/app/admin/seo/page.tsx` | modify (import GSCSummarySection) |
| `frontend/app/admin/seo/_components/GSCSummarySection.tsx` | new |

---

## 4. Decisões importantes tomadas na sessão

1. **Scope correction SEO-008:** plano original tinha 8 pillars; story real pede 3. Ajustado para licitacoes + lei-14133 + pncp (as que a story lista explícitamente como IN).
2. **SEO-005 graceful degradation:** sem requerer user pré-configurar GCP, toda infra é shippada com `GSC_SERVICE_ACCOUNT_JSON` como env var opcional. Dashboard mostra instruções de setup quando ausente.
3. **Wave D deferida:** grep revelou que 5 stories alvo já estão InProgress/Done. Validation desnecessária.
4. **STORY-418 (trial emails) pulada:** declarado pelo user "100% inbound SEO". Activation não é aquisição — deferida para próxima semana.
5. **#459 BreadcrumbList deferido:** DIRTY (conflito main). Não critical path esta semana.
6. **Tests Matrix integration ignored:** matrix é long-running (~40min) e não-required. Continuar monitorando, não bloquear merge.
7. **Merge via squash + delete-branch:** estratégia padrão. Repo tem `auto-merge disabled` (memory `reference_auto_merge_disabled`), então cada merge é manual fetch+reset+push per PR.

---

## 5. Memórias novas / validadas nesta sessão

Atualizadas empiricamente:

1. **`feedback_concurrent_jobs_cap`** — confirmado 20 concurrent job cap. 9 merges em sequência (com ~10-15s de delay entre) não saturaram. Batches de 2-3 seguem válidos.
2. **`reference_main_required_checks`** — confirmado: `Backend Tests` e `Frontend Tests` sem "(PR Gate)" são os required; `Backend Tests (3.11)/(3.12)` são matrix não-required. `Validate Migration Sequence` NÃO é required mas bloqueia merge via UI (precisa rebase ou skip).
3. **`feedback_story_discovery_grep_before_implement`** — aplicado com sucesso: stories 431-436 já estavam InProgress/Done, economizou ~2h de Wave D desnecessária.
4. **`reference_auto_merge_disabled`** — confirmado. `gh pr merge --squash` funciona direto quando required checks verdes. Sem `--auto` flag.

Nova memória potencial para criar posteriormente (não crítica):
- PR merge estratégia via @devops Skill funciona bem quando fornecido plano estruturado (steps numerados + constraints explícitos). Tentativa anterior de "rebase train paralelo" em Bash background falhou por race conditions.

---

## 6. Metricas da sessão

**Shipped em main:** 9 PRs (Wave A completa + handoffs)
**Shipped em PRs abertos:** 2 (SEO-008 + SEO-005)
**Linhas de código:** ~12k (pillars) + ~1k (GSC backend/frontend)
**Tests criados:** 6 unit (backend gsc_sync) + 6 E2E (pillar pages)
**Horas de trabalho cronometradas:** ~4h sessão ativa

**Revenue funnel Mixpanel agora completo:**
```
signup_completed → (trial_card_captured) → paywall_hit → checkout_initiated → checkout_completed
```

**Topical authority signal:** 3 pillar pages (11.6k palavras) + 30 internal spoke links cross-referenciados + structured data 4 tipos = primeiro grande sinal SEO pós-CRIT-SEO-011 (cidades) e pós-SEO-001 (sitemap shard 4).

---

## 7. Follow-ups para próxima sessão

### Pickup imediato (quando CI verdear)

1. **Mergear #477** (pillar pages) — assim que required green
2. **Mergear #478** (SEO-005 GSC) — assim que required green + migration-check pass
3. **Mergear #470** (uptime metric) — re-synced, aguarda CI
4. **Submissão manual no GSC** (post-merge #477): URL Inspection + Request Indexing para `/guia/licitacoes`, `/guia/lei-14133`, `/guia/pncp`
5. **Configurar GSC service account** (post-merge #478): criar SA em Google Cloud, adicionar JSON em Railway, convidar SA no GSC. Próximo domingo cron popula.

### Pickup secundário

6. **#459 DIRTY** — verificar se já shipado via outro PR; fechar ou rebase manual.
7. **#476** — revisar origem e conteúdo (blue ocean research doc + ocean-compass handoff).
8. **Rich Results Test Google** em `https://search.google.com/test/rich-results?url=https://smartlic.tech/guia/lei-14133` para validar JSON-LD shippado.

### Deferidos intencionalmente

9. **STORY-418 (trial email pipeline)** — activation, não aquisição. Reabrir quando CAC estabilizar e próxima prioridade for conversão in-flight.
10. **STORY-SEO-007 (MDX migration)** — pillars usam TSX; MDX seria nice-to-have para DX dos 71 blog posts existentes. Próxima sessão.
11. **STORY-BTS-012 (drift cluster tail)** — 4 clusters com xfail(strict=False), noise mas não bloqueio.
12. **MON-* stories (30 Drafts)** — roadmap monetização próximo trimestre. Validation por wave, não em lote.

### Housekeeping

13. **8 stashes locais** — user ainda precisa revisar e dropar conforme handoff abundant-reddy section 4.
14. **DEBT-mypy-1.20** — type safety cleanup, não-blocker.

---

## 8. Notas para próximo operador

1. **Reality-check empírico primeiro.** Handoffs envelhecem em horas. Grep-before-implement economizou Wave D inteira nesta sessão.
2. **@devops Skill funciona bem com plano estruturado.** Steps numerados + constraints explícitos produzem execução limpa. Tentativa anterior de rebase train paralelo em Bash background falhou por race conditions no `.git/index.lock`.
3. **Merge batches de 2-3 PRs** — conforme memory `feedback_concurrent_jobs_cap`. Sequential OK, full-parallel satura GH Actions.
4. **Dado que `auto-merge disabled`:** cada merge é `gh pr merge --squash --delete-branch` (sem `--auto`). Funciona direto se required checks verdes.
5. **Validate Migration Sequence** às vezes bloqueia merge mesmo sendo não-required — cuidado em PRs que tocam migrations sem workaround.
6. **SEO-005 activation é manual** (GCP service account). Código é totalmente inerte sem env var — zero risco de ship incompleto.
7. **Pillar pages `/guia/*` pós-merge** precisam submissão manual no GSC para indexação acelerada. 3 URLs, 1 por vez via URL Inspection.

---

**Sessão fechada:** 9 merges em main + 2 features novas in-flight + Wave D deferida por descoberta empírica. Revenue funnel completo. Topical authority grande sinal shippado. Próxima sessão pode pegar o trem e mergear #477, #478, #470 quando CI verdear — e iniciar activation GCP para Wave C ir live.
