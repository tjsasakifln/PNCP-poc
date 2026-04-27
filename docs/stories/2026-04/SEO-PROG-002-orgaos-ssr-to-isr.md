# SEO-PROG-002: Migrar `orgaos/[slug]` SSR puro → ISR + fallback blocking (top-2000 órgãos)

**Priority:** P0
**Effort:** M (3-4 dias)
**Squad:** @dev + @architect
**Status:** Ready
**Epic:** [EPIC-SEO-PROG-2026-Q2](EPIC-SEO-PROG-2026-Q2.md)
**Sprint:** Sprint 2 (06–12/mai)
**Sprint Window:** 2026-05-06 → 2026-05-12
**Bloqueado por:** RES-BE-002 (rotas backend `_run_with_budget` em staging)

---

## Contexto

A rota `/orgaos/[slug]` renderiza estatísticas de um órgão público comprador (total de licitações, valor médio estimado, top modalidades, top setores, últimas 30 licitações, JSON-LD `Dataset`). É indexada pelo sitemap shard id:4 com top-2000 órgãos via `/v1/sitemap/orgaos`.

**Problema atual** (`frontend/app/orgaos/[slug]/page.tsx:42-45`):

```ts
export const revalidate = 86400; // 24h ISR
export function generateStaticParams() {
  return []; // SSR on-demand
}
```

Mesmo padrão fatal de `/cnpj/[cnpj]`: `revalidate=86400` declarado mas `generateStaticParams=[]` torna a rota efetivamente SSR puro on-demand. Cada hit crawler em órgão único dispara fetch a `/v1/orgao/{slug}/stats` (3+ queries Supabase: agregação licitações, contratos, modalidades). 2000 órgãos × ~5 hits/dia GSC = 10k req/dia sem cache pré-construído → backend hobby satura.

A página já tem `MIN_ACTIVE_BIDS_FOR_INDEX=5` gate de noindex (`page.tsx:76-78`), mas a falta de SSG significa que o gate é avaliado **em runtime**, não em build — Google ainda crawleia a URL antes de descobrir o noindex, queimando crawl budget.

**Por que P0:** órgãos públicos são query-intent natural ("CNPJ Prefeitura X licitações", "Ministério Y contratos"). Memory `reference_smartlic_baseline_2026_04_24`: GSC posição média 7.1 — qualquer migração para position 1-3 multiplica clicks. Sem ISR, escala SEO = wedge garantido.

---

## Acceptance Criteria

### AC1: Migração ISR + top-2000 SSG params

**Given** rota `frontend/app/orgaos/[slug]/page.tsx` em SSR puro
**When** @dev refatora para ISR pré-populado
**Then**:

- [ ] `export const revalidate = 7200` (2h — órgãos têm cadência de licitação semanal/mensal, mais lenta que CNPJs/itens)
- [ ] `export const dynamicParams = true` (explícito)
- [ ] `generateStaticParams` retorna top-2000 órgãos por volume:

```ts
export async function generateStaticParams(): Promise<{ slug: string }[]> {
  const backendUrl =
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    'http://localhost:8000';
  try {
    const res = await fetch(
      `${backendUrl}/v1/sitemap/orgaos?limit=2000&order=total_licitacoes`,
      {
        next: { revalidate: 7200 },
        signal: AbortSignal.timeout(10000),
      },
    );
    if (!res.ok) {
      console.error(`[orgaos] generateStaticParams HTTP ${res.status}`);
      return [];
    }
    const data = await res.json();
    return ((data.orgaos as string[]) ?? []).map((slug) => ({ slug }));
  } catch (err) {
    console.error('[orgaos] generateStaticParams failed', err);
    return [];
  }
}
```

- [ ] `fetchOrgaoStats` ajustado: `next: { revalidate: 7200 }` (alinhado), mantém `AbortSignal.timeout(10000)`
- [ ] Backend endpoint `/v1/sitemap/orgaos?limit=N&order=total_licitacoes` retorna ordenado desc (TODO @architect: verificar param `order` ou follow-up backend)

### AC2: Noindex thin-content gate em SSG

**Given** órgão tem `total_licitacoes < MIN_ACTIVE_BIDS_FOR_INDEX (5)`
**When** crawler acessa `/orgaos/{slug}`
**Then**:

- [ ] `metadata.robots = { index: false, follow: false }` (já implementado em `page.tsx:76-78` — manter)
- [ ] **NOVO:** `generateStaticParams` filtra órgãos abaixo do threshold:
  - Backend endpoint deve retornar apenas órgãos com `total_licitacoes >= MIN_ACTIVE_BIDS_FOR_INDEX` (consistente com endpoint `/v1/sitemap/contratos-orgao-indexable` precedente — SEO-460)
  - Frontend não duplica filtragem (single source of truth = backend)
- [ ] Comment inline citando STORY-439 + SEO-PROG-002 (precedente).

### AC3: HTTP 503 fallback graceful

**Given** backend `/v1/orgao/{slug}/stats` indisponível em runtime ISR
**When** usuário/crawler acessa página
**Then**:

- [ ] Página renderiza fallback (não crash)
- [ ] HTML inclui `<meta name="robots" content="noindex,follow" />`
- [ ] Texto: "Estatísticas temporariamente indisponíveis para este órgão. Tente novamente em alguns minutos."
- [ ] Sentry breadcrumb `orgao_stats_fallback` tags={slug, outcome=backend_unavailable, http_status}

### AC4: Cache alignment audit (anti SEN-FE-001)

- [ ] Zero `cache: 'no-store'` em `frontend/app/orgaos/[slug]/`
- [ ] Todos fetches usam `next: { revalidate: N }` consistente com page-level (7200)
- [ ] Comentário inline em fetch:

```ts
// SEN-FE-001 + SEO-PROG-002: revalidate page-level + next.revalidate alinhados (7200s).
// NUNCA cache: 'no-store' em rota ISR — quebra SSG silenciosamente.
```

### AC5: Feature flag rollback

- [ ] `process.env.SEO_ROUTE_MODE_ORGAOS === 'ssr'` reverte para `generateStaticParams = []` + `revalidate = 0`
- [ ] Documentar em `frontend/.env.example` + PR description

### AC6: Observabilidade

- [ ] Counter `nextjs_isr_revalidate_total{route="/orgaos/[slug]",outcome}` ativo
- [ ] Sentry tags={slug, outcome, latency_ms}
- [ ] Log estruturado: `[orgaos-isr] slug=X latency_ms=Y outcome=Z`

### AC7: Testes

- [ ] **Unit:** `frontend/__tests__/app/orgaos/orgaos-page.test.ts` — `generateStaticParams` returns top-2000, `[]` em error.
- [ ] **Unit:** `fetchOrgaoStats` retorna `null` em HTTP 503 + Sentry capture.
- [ ] **E2E Playwright:** `frontend/e2e-tests/seo/orgaos-isr.spec.ts`:
  - Visit top órgão → 200 + JSON-LD `Dataset` + LCP<2.5s
  - Visit órgão thin (<5 licitações) → noindex meta presente
  - Visit órgão inválido (slug-fake) → 404 graceful
  - Visit com backend mock 503 → fallback com noindex
- [ ] **Lighthouse smoke:** top-3 órgãos amostrados.
- [ ] **Rich Results Test:** JSON-LD `Dataset` validation.

---

## Scope

**IN:**
- Refator `frontend/app/orgaos/[slug]/page.tsx` para ISR top-2000
- Backend filter dependency `MIN_ACTIVE_BIDS_FOR_INDEX` no endpoint sitemap
- HTTP 503 fallback + noindex thin content
- Feature flag `SEO_ROUTE_MODE_ORGAOS`
- Cache alignment audit
- Testes unit + E2E + Lighthouse smoke
- Prometheus + Sentry instrumentation

**OUT:**
- `/orgaos` (index page) — já SSG estático
- `<RelatedPages />` — escopo SEO-PROG-011
- FAQPage JSON-LD — escopo SEO-PROG-012
- Backend endpoint redesign profundo (param `order` é follow-up backend separado se não existir)

---

## Definition of Done

- [ ] Top-2000 órgãos pré-populados no build (.next/server/app/orgaos/[slug]/*.html presentes em CI artifact)
- [ ] Long-tail via fallback blocking + ISR cache 7200s
- [ ] Lighthouse CI top-3 órgãos: LCP<2.5s, INP<200ms, CLS<0.1
- [ ] Rich Results Test pass: Dataset CC-BY (já presente)
- [ ] GSC URL Inspection top-3 órgãos: HTTP 200 OK
- [ ] Bundle delta < +0KB
- [ ] Feature flag `SEO_ROUTE_MODE_ORGAOS` em `.env.example`
- [ ] Zero `cache: 'no-store'` em `app/orgaos/`
- [ ] CodeRabbit clean
- [ ] PR aprovado por @qa + @architect
- [ ] Counter Prometheus ativo em prod
- [ ] Change Log atualizado

---

## Dev Notes

### Paths absolutos

- **Rota:** `/mnt/d/pncp-poc/frontend/app/orgaos/[slug]/page.tsx`
- **Client:** `/mnt/d/pncp-poc/frontend/app/orgaos/[slug]/OrgaoPerfilClient.tsx`
- **Backend endpoint:** `/mnt/d/pncp-poc/backend/routes/sitemap_orgaos.py` (verificar param `order` + filtro `MIN_ACTIVE_BIDS_FOR_INDEX`)
- **Stats endpoint:** `/mnt/d/pncp-poc/backend/routes/orgao_stats.py` (precisa `_run_with_budget` — RES-BE-002)
- **Tests:** `/mnt/d/pncp-poc/frontend/__tests__/app/orgaos/` + `/mnt/d/pncp-poc/frontend/e2e-tests/seo/`
- **Reference (similar pattern):** `/mnt/d/pncp-poc/frontend/app/cnpj/[cnpj]/page.tsx` (após SEO-PROG-001)

### Padrões existentes

- `MIN_ACTIVE_BIDS_FOR_INDEX` env pattern já em `orgaos/[slug]/page.tsx:76` — replicar nos outros stories.
- Sitemap fetch já reusa em `frontend/app/sitemap.ts` `fetchSitemapOrgaos` (`sitemap.ts:171-181`).
- Backend filter pattern em `/v1/sitemap/contratos-orgao-indexable` (SEO-460) — clonar para `/v1/sitemap/orgaos?indexable=true`.

### Testing standards

- Igual ao SEO-PROG-001.
- Fixture top-3 órgãos: usar CNPJs de prefeituras/ministérios reais com baseline GSC conhecido (consultar `reference_smartlic_baseline_2026_04_24`).

### Threshold revalidate diferente

- `/cnpj/[cnpj]`: 3600s (CNPJ ativos podem ganhar contratos diariamente)
- `/orgaos/[slug]`: **7200s** (órgãos publicam licitações em cadência semanal/mensal — menor frequência de mudança)
- `/itens/[catmat]`: 3600s (preços CATMAT mudam diariamente)
- `/observatorio/[slug]`: 86400s (evergreen — ver SEO-PROG-004)

---

## Risk & Rollback

### Triggers

| Trigger | Threshold | Detecção |
|---|---|---|
| LCP p75 top-3 órgãos | > 3.5s | Lighthouse CI |
| GSC clicks `/orgaos/*` 7d | -30% | GSC API |
| Sentry errors `/orgaos/*` | > 5/min | Sentry alert |
| Backend wedge `orgao_stats` | timeout > 0/min | Prometheus |

### Ações

1. Soft: `SEO_ROUTE_MODE_ORGAOS=ssr` + redeploy.
2. Hard: revert PR via @devops.
3. Reduce SSG: `SEO_TOP_ORGAOS_LIMIT=500`.

---

## Dependencies

### Entrada

- RES-BE-002 (orgao_stats backend com budget)
- SEO-PROG-008 (Dockerfile BACKEND_URL ARG)

### Saída

- SEO-PROG-006 (sitemap shard 4 consume orgaos)
- SEO-PROG-011 (RelatedPages aplicado pós-estabilização)
- SEO-PROG-012 (schema expansion)

### Paralelas

- SEO-PROG-001, 003, 004 (mesmo sprint, rotas independentes)

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | Status | Notes |
|---|---|---|---|
| 1 | Clear and objective title | OK | Título preciso: rota + transição + cap top-2000 |
| 2 | Complete description | OK | Contexto cita problema linhas 42-45 + threshold runtime vs build (crawl budget waste) |
| 3 | Testable acceptance criteria | OK | AC1-AC7 todos testáveis; threshold revalidate=7200 justificado (cadência semanal/mensal) |
| 4 | Well-defined scope (IN/OUT) | OK | Scope IN/OUT claros; backend filter dependency explícita |
| 5 | Dependencies mapped | OK | Entrada: RES-BE-002 + SEO-PROG-008. Saída: 006/011/012. Paralelas: 001/003/004 |
| 6 | Complexity estimate | OK | Effort M consistente com SEO-PROG-001 (mesmo padrão, rota diferente) |
| 7 | Business value | OK | Justifica P0 com query-intent natural + position 7.1 baseline |
| 8 | Risks documented | OK | 4 triggers + 3 ações rollback |
| 9 | Criteria of Done | OK | DoD 12 itens; valida Dataset CC-BY (já existe — não regredir) |
| 10 | Alignment with PRD/Epic | OK | Padrão SEN-FE-001 + revalidate=7200 diferenciado vs cnpj=3600/itens=3600/observatorio=86400 (justificado em Dev Notes) |

### Observations

- Threshold revalidate=7200 (vs 3600 em sister stories) é decisão consciente baseada em cadência de mudança — bem documentada.
- AC2 propõe filter no backend (single source of truth) — correto, evita duplicação.
- Reuso de `MIN_ACTIVE_BIDS_FOR_INDEX` env pattern existente em `orgaos/[slug]:76`.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada a partir do plano EPIC-SEO-PROG seção SEO-PROG-002 | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). Padrão canônico irmão de SEO-PROG-001. Status Draft→Ready. | @po (Pax) |
