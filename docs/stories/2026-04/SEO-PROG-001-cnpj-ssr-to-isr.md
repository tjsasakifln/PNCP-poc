# SEO-PROG-001: Migrar `cnpj/[cnpj]` SSR puro → ISR + fallback blocking (top-1000 CNPJs)

**Priority:** P0
**Effort:** M (3-4 dias)
**Squad:** @dev + @architect
**Status:** Ready
**Epic:** [EPIC-SEO-PROG-2026-Q2](EPIC-SEO-PROG-2026-Q2.md)
**Sprint:** Sprint 1-2 (29/abr–12/mai)
**Sprint Window:** 2026-04-29 → 2026-05-12
**Bloqueado por:** RES-BE-002 (rotas backend protegidas com `_run_with_budget` em staging)

---

## Contexto

A rota `/cnpj/[cnpj]` é uma das **principais páginas SEO programáticas** do SmartLic (perfil B2G de fornecedor com histórico de contratos públicos, score, editais abertos no setor detectado, JSON-LD Organization+Dataset+BreadcrumbList). O sitemap declara ~5k CNPJs ativos (`/v1/sitemap/cnpjs`), e o backlog projeta ramp-up para 50k+ via Onda 2 da estratégia 100% inbound.

**Problema atual** (`frontend/app/cnpj/[cnpj]/page.tsx:49-51`):

```ts
export const revalidate = 86400; // 24h ISR
export function generateStaticParams() {
  return []; // SSR on-demand
}
```

A linha 50 retorna `[]` — `generateStaticParams = []` em Next.js 16 com `dynamicParams=true` (default) semanticamente equivale a **SSR puro on-demand**. Cada request crawler dispara um fetch ao backend (`/v1/empresa/{cnpj}/perfil-b2g`) sem cache pré-construído. Combinado com Googlebot wave + os outros 7 SSR puros (orgaos, itens, observatorio, fornecedores, etc.) e o SSG fan-out de `sitemap.ts` (786L com 6 fetches paralelos no shard id:4), é precursor direto do incidente PR #529 — o backend hobby (1 worker) saturou em 5-7 minutos.

A rota tem `revalidate=86400` declarado mas sem `generateStaticParams` populado o ISR nunca pré-popula o cache de página — a 1ª request por CNPJ é sempre miss completo. Top-1000 CNPJs (por volume de contratos 24m) representam ~80% das impressões GSC nesta rota; pré-construí-los em build elimina o burst inicial.

**Por que P0:** reincidência do P0 (PR #529) é o risco existencial mais imediato; rota `/cnpj/[cnpj]` está no top-3 de tráfego crawler GSC + tem fan-out backend de ~3 queries Supabase por request (`empresa.razao_social`, `contratos`, `editais_amostra`). Sem ISR pré-populado, qualquer ramp-up de SEO ressuscita o wedge de 2026-04-27.

**Padrão técnico canônico (anti SEN-FE-001 recidiva):**

- `export const revalidate = 3600` (1h) — alinhado ao `sitemap.ts` ISR.
- `export const dynamicParams = true` — fallback blocking para CNPJs fora do top-1000.
- `generateStaticParams` retorna top-1000 via `GET /v1/sitemap/fornecedores-cnpj?limit=1000&order=volume_24m` — usar `next: { revalidate: 3600 }` (NUNCA `cache: 'no-store'`).
- Fetch interno (`fetchPerfil`) já tem `next: { revalidate: 86400 }` + `AbortSignal.timeout(10000)` — manter, mas alinhar `revalidate` com o page-level (3600s) e adicionar HTTP 503 fallback explícito.

---

## Acceptance Criteria

### AC1: Migração ISR + top-1000 SSG params

**Given** a rota `frontend/app/cnpj/[cnpj]/page.tsx` está em SSR puro (`generateStaticParams` retorna `[]`)
**When** o @dev refatora para ISR com pré-build top-1000
**Then**:

- [ ] `export const revalidate = 3600` (substitui o atual `86400`)
- [ ] `export const dynamicParams = true` (explícito, mesmo sendo default)
- [ ] `generateStaticParams` retorna top-1000 CNPJs por volume:

```ts
export async function generateStaticParams(): Promise<{ cnpj: string }[]> {
  const backendUrl =
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    'http://localhost:8000';
  try {
    const res = await fetch(
      `${backendUrl}/v1/sitemap/fornecedores-cnpj?limit=1000&order=volume_24m`,
      {
        next: { revalidate: 3600 },
        signal: AbortSignal.timeout(10000),
      },
    );
    if (!res.ok) {
      console.error(`[cnpj] generateStaticParams HTTP ${res.status}`);
      return [];
    }
    const data = await res.json();
    return ((data.cnpjs as string[]) ?? []).map((cnpj) => ({ cnpj }));
  } catch (err) {
    console.error('[cnpj] generateStaticParams failed', err);
    return [];
  }
}
```

- [ ] `fetchPerfil` ajustado: `next: { revalidate: 3600 }` (alinhado ao page-level), mantém `AbortSignal.timeout(10000)`
- [ ] Backend endpoint `GET /v1/sitemap/fornecedores-cnpj?limit=N&order=volume_24m` retorna ordenado desc por `total_contratos_24m` (TODO @architect: verificar se param `order` já existe no endpoint atual; senão, criar follow-up backend story)

### AC2: HTTP 503 fallback graceful

**Given** o backend retorna HTTP 5xx ou timeout no fetch de perfil em runtime ISR
**When** o usuário/crawler acessa `/cnpj/{cnpj}`
**Then**:

- [ ] Página renderiza fallback degradado (não crasha, não retorna 500)
- [ ] HTML inclui `<meta name="robots" content="noindex,follow" />` para evitar GSC indexar página vazia
- [ ] Texto visível: "Dados temporariamente indisponíveis. Tente novamente em alguns minutos."
- [ ] HTTP status code 503 (não 200) — Next.js suporta via `notFound()` para 404 e `unstable_serialize` para custom; opção: usar `headers().set('cache-control', 'public, max-age=60')` + retornar componente fallback
- [ ] Sentry breadcrumb `cnpj_perfil_fallback` com tag `outcome=backend_unavailable`

```ts
async function fetchPerfil(cnpj: string): Promise<PerfilB2G | null> {
  const backendUrl =
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    'http://localhost:8000';
  try {
    const resp = await fetch(`${backendUrl}/v1/empresa/${cnpj}/perfil-b2g`, {
      next: { revalidate: 3600 },
      signal: AbortSignal.timeout(10000),
    });
    if (!resp.ok) {
      Sentry.captureMessage(`cnpj_perfil_http_${resp.status}`, {
        level: resp.status >= 500 ? 'error' : 'warning',
        tags: { cnpj, http_status: String(resp.status) },
      });
      return null;
    }
    return await resp.json();
  } catch (err) {
    Sentry.captureException(err, {
      tags: { cnpj, route: 'cnpj_perfil', outcome: 'fetch_error' },
    });
    return null;
  }
}
```

### AC3: Noindex se `total_contratos_24m < MIN_ACTIVE_BIDS_FOR_INDEX`

**Given** um CNPJ existe mas tem `total_contratos_24m < 5` (gate de thin content)
**When** crawler acessa a página
**Then**:

- [ ] `metadata.robots.index = false` (já existe na linha 112: `robots: { index: total_contratos_24m > 0, follow: true }` — atualizar threshold de `> 0` para `>= MIN_ACTIVE_BIDS_FOR_INDEX`)
- [ ] Threshold via `process.env.MIN_ACTIVE_BIDS_FOR_INDEX ?? '5'` (consistente com `orgaos/[slug]` linha 76)
- [ ] Adicionar comentário inline citando STORY-439 + SEO-PROG-001 como precedente

### AC4: Cache alignment audit (SEN-FE-001 recidiva check)

**Given** a memory `feedback_isr_fetch_cache_alignment_next16` adverte contra `revalidate = N` + `cache: 'no-store'` no mesmo escopo
**When** o @dev grep por `cache: 'no-store'` em `frontend/app/cnpj/`
**Then**:

- [ ] Zero ocorrências de `cache: 'no-store'` em fetches dentro de `app/cnpj/[cnpj]/`
- [ ] Todos os fetches usam `next: { revalidate: N }` consistente com page-level
- [ ] Adicionar comentário SEN-FE-001 inline em `fetchPerfil` e `generateStaticParams`:

```ts
// SEN-FE-001 + SEO-PROG-001: NEVER use `cache: 'no-store'` em rota com `export const revalidate`.
// Quebra SSG silenciosamente (build 200 OK mas runtime SSR puro). Usar `next: { revalidate }` sempre.
```

### AC5: Feature flag rollback

**Given** rollback emergencial necessário (LCP p75 > 3.5s ou wedge backend reincidente)
**When** `process.env.SEO_ROUTE_MODE_CNPJ === 'ssr'` é setado
**Then**:

- [ ] `generateStaticParams` retorna `[]` (mantém comportamento SSR original)
- [ ] `revalidate` reverte para `0` (force-dynamic) via condicional:

```ts
export const revalidate = process.env.SEO_ROUTE_MODE_CNPJ === 'ssr' ? 0 : 3600;
```

- [ ] Feature flag documentada em `frontend/.env.example`
- [ ] Rollback runbook em PR description: "Set `SEO_ROUTE_MODE_CNPJ=ssr` no Railway frontend service e force redeploy via dashboard"

### AC6: Observabilidade Prometheus + Sentry

- [ ] Counter `nextjs_isr_revalidate_total{route="/cnpj/[cnpj]",outcome}` incrementado em cada revalidação (success/error/timeout) — usar middleware ou wrapper utilitário em `frontend/lib/isr-metrics.ts` (TODO @architect: verificar se utilitário já existe; senão, criar follow-up)
- [ ] Sentry breadcrumb por fetch: `tags={cnpj, outcome, latency_ms}`
- [ ] Log estruturado server-side: `[cnpj-isr] cnpj=X latency_ms=Y outcome=Z`

### AC7: Testes (Lighthouse CI + Playwright E2E + unit)

- [ ] **Unit:** `frontend/__tests__/app/cnpj/cnpj-page.test.ts` — testa `generateStaticParams` retorna array com `{cnpj}` quando backend OK, `[]` quando HTTP 5xx/timeout
- [ ] **Unit:** `fetchPerfil` retorna `null` em HTTP 503 + dispara `Sentry.captureMessage` (mock @sentry/nextjs)
- [ ] **E2E Playwright:** `frontend/e2e-tests/seo/cnpj-isr.spec.ts`:
  - Visit `/cnpj/{TOP_CNPJ_FIXTURE}` → 200 + JSON-LD presente + LCP < 2.5s
  - Visit `/cnpj/00000000000000` (long-tail/inválido) → 404 graceful (notFound)
  - Visit com backend mock 503 → renderiza fallback + meta noindex
- [ ] **Lighthouse CI:** sample top-3 CNPJs (fixtures); LCP<2.5s, INP<200ms, CLS<0.1 (instrumentação completa em SEO-PROG-010)
- [ ] **Rich Results Test:** validar JSON-LD `Organization`, `Dataset`, `BreadcrumbList` via API `https://searchconsole.googleapis.com/v1/urlInspection/index:inspect` ou `https://search.google.com/test/rich-results` smoke test em CI

---

## Scope

**IN:**
- Refator `frontend/app/cnpj/[cnpj]/page.tsx` para ISR + top-1000 SSG params
- HTTP 503 fallback + noindex thin content
- Feature flag `SEO_ROUTE_MODE_CNPJ`
- Cache alignment audit (`cache: 'no-store'` zero ocorrências)
- Testes unit + E2E + Lighthouse smoke
- Prometheus counter + Sentry instrumentation

**OUT:**
- Migração de `/cnpj` (index page sem param dinâmico) — fora de escopo (já SSG)
- `<RelatedPages />` automatizado — escopo de SEO-PROG-011
- Schema.org expansion (FAQPage, etc.) — escopo de SEO-PROG-012
- GSC API ingest dashboard — escopo de SEO-PROG-013
- Backend endpoint redesign de `/v1/sitemap/fornecedores-cnpj` (param `order` já existe ou follow-up backend separado)

---

## Definition of Done

- [ ] Rota `/cnpj/[cnpj]` reportando ISR pré-populado para top-1000 (verificar via `.next/server/app/cnpj/[cnpj].html` no build output CI)
- [ ] Long-tail (CNPJ fora do top-1000) renderiza via fallback blocking + cache em runtime
- [ ] Lighthouse CI top-3 CNPJs: LCP<2.5s, INP<200ms, CLS<0.1 (3 amostras CrUX)
- [ ] Rich Results Test pass: Organization + Dataset + BreadcrumbList sem warnings
- [ ] GSC URL Inspection top-3 CNPJs retornam HTTP 200 OK (cross-validate via Playwright MCP)
- [ ] Bundle delta < +0KB (rota não adiciona componente novo no client bundle — apenas server config)
- [ ] Feature flag `SEO_ROUTE_MODE_CNPJ` documentada em `.env.example` + rollback runbook em PR
- [ ] Zero `cache: 'no-store'` em `app/cnpj/` (`grep -r "cache: 'no-store'" frontend/app/cnpj/` retorna nada)
- [ ] CodeRabbit clean (max 2 self-healing iterations)
- [ ] PR aprovado por @qa + @architect (Aria)
- [ ] Deploy staging validado com Playwright smoke + Sentry breadcrumb verification
- [ ] Counter Prometheus `nextjs_isr_revalidate_total{route="/cnpj/[cnpj]"}` ativo em prod
- [ ] Change Log do epic atualizado

---

## Dev Notes

### Paths absolutos

- **Rota:** `/mnt/d/pncp-poc/frontend/app/cnpj/[cnpj]/page.tsx`
- **Client component:** `/mnt/d/pncp-poc/frontend/app/cnpj/[cnpj]/CnpjPerfilClient.tsx`
- **Reference (sitemap fetch pattern):** `/mnt/d/pncp-poc/frontend/app/sitemap.ts:17-48` (fetchSitemapJson com Sentry + AbortSignal)
- **Reference (ISR alignment pattern):** `/mnt/d/pncp-poc/frontend/app/blog/licitacoes/[setor]/[uf]/page.tsx`
- **Backend endpoint base:** `/mnt/d/pncp-poc/backend/routes/sitemap_fornecedores.py` (verificar param `order=volume_24m` ou follow-up)
- **Tests:** `/mnt/d/pncp-poc/frontend/__tests__/app/cnpj/` + `/mnt/d/pncp-poc/frontend/e2e-tests/seo/`
- **Env example:** `/mnt/d/pncp-poc/frontend/.env.example`

### Padrões existentes a reutilizar

- `fetchSitemapJson` pattern em `frontend/app/sitemap.ts:17-48` (cache + Sentry + AbortSignal). Replicar localmente em `cnpj/[cnpj]/page.tsx` (não importar — manter encapsulamento).
- `MIN_ACTIVE_BIDS_FOR_INDEX` env var pattern em `frontend/app/orgaos/[slug]/page.tsx:76`.
- BreadcrumbList JSON-LD utility (já presente inline em `cnpj/[cnpj]/page.tsx:156-164`).

### Testing standards

- **Jest + React Testing Library:** `frontend/__tests__/` — aderir ao polyfill jest.setup.js (crypto.randomUUID, EventSource).
- **Playwright E2E:** `frontend/e2e-tests/` — usar `npm run test:e2e` headless por padrão; smoke routes em `frontend/e2e-tests/seo/`.
- **Lighthouse CI:** instrumentação central em SEO-PROG-010; smoke amostragem manual neste story via `npx @lhci/cli autorun --collect.url=https://staging.smartlic.tech/cnpj/{TOP_CNPJ}`.
- **Mocking pattern:** mockar `fetch` global via `vi.spyOn(global, 'fetch')` ou usar `msw` se já configurado.
- **Coverage threshold:** ≥85% nas linhas tocadas (Jest `--coverage`).

### Padrão SEN-FE-001 (NUNCA mais recidivar)

A memory `feedback_isr_fetch_cache_alignment_next16` documenta o antipattern fatal Next.js 16:
- `export const revalidate = N` (page-level) **+** `cache: 'no-store'` em fetch interno = SSG quebra silenciosamente em runtime SSR puro. Build passa 200 OK.
- **SOLUÇÃO:** sempre `next: { revalidate: N }` com mesmo N do page-level. Em `generateStaticParams` use `next: { revalidate: 3600 }`. NÃO use `cache: 'no-store'` em nenhum fetch dentro de rota com `revalidate` declarado.
- A memory `feedback_sen_fe_001_recidiva_sitemap.md` advertiu (2026-04-24): após fix, **grep global por outros call sites é mandatório**. Esta story DEVE incluir grep audit em `frontend/app/cnpj/`.

### Build OOM risk

- Memory `feedback_wsl_next16_build_inviavel.md`: WSL build inviável para >3k pages.
- Top-1000 CNPJs SSG é seguro (<3k threshold).
- Build output validation deferred para CI (SEO-PROG-014 padroniza).

### Backend dependency

- **Bloqueador hard:** RES-BE-002 deve estar em **staging** (não prod necessariamente) antes do merge desta PR — endpoint `/v1/empresa/{cnpj}/perfil-b2g` precisa de `_run_with_budget(3s)` + negative cache (RES-BE-003 desejável mas não bloqueante).
- Validar com @architect via grep `grep -r "_run_with_budget" backend/routes/empresa.py` antes de iniciar dev.

---

## Risk & Rollback

### Triggers de rollback

| Trigger | Threshold | Detecção |
|---|---|---|
| LCP p75 (CrUX top-3 CNPJs) | > 3.5s | Lighthouse CI + WebPageTest weekly |
| GSC clicks 7d sobre `/cnpj/*` | -30% vs baseline | GSC API (após SEO-PROG-013) |
| Backend wedge reincidente | `smartlic_route_timeout_total{route="empresa_perfil_b2g"} > 0` | Prometheus alert |
| Build OOM Railway | exit code 137 no deploy | Railway logs |
| Sentry errors em `/cnpj/*` | > 5/min | Sentry alert |

### Ações de rollback

1. **Soft rollback (preferido):** Set `SEO_ROUTE_MODE_CNPJ=ssr` em Railway `bidiq-frontend` service vars + force redeploy via dashboard. Reverte para SSR puro on-demand sem revert PR. Tempo: ~3min.
2. **Hard rollback:** `gh pr revert {PR_NUMBER}` + push (delegar @devops). Tempo: ~10min.
3. **Reduce SSG params:** Set `SEO_TOP_CNPJ_LIMIT=200` (env var, leitura no `generateStaticParams`) para mitigar build OOM mantendo ISR ativo.

### Out-of-scope risks (escalate a @architect)

- Cap futuro 50k CNPJs SSG: build OOM Railway. Resolver via SEO-PROG-014 + tier upgrade.
- Long-tail (CNPJs sem score) saturando backend via fallback blocking sob Googlebot wave de URLs inválidas: depende de RES-BE-003 (negative cache) deployado em prod.

---

## Dependencies

### Entrada (bloqueia esta story)

- **RES-BE-002** (top-5 routes com `_run_with_budget`): rota backend `/v1/empresa/{cnpj}/perfil-b2g` deve estar em staging com budget temporal antes do merge.
- **SEO-PROG-008** (Dockerfile ARG BACKEND_URL): garantir build SSG não cai em `localhost:8000` fallback.

### Saída (esta story bloqueia)

- **SEO-PROG-006** (sitemap particionado): consume `/v1/sitemap/fornecedores-cnpj?limit=N` no shard 4.
- **SEO-PROG-011** (internal linking): aplica `<RelatedPages />` em `/cnpj/[cnpj]` após ISR estável.
- **SEO-PROG-012** (schema expansion): adiciona FAQPage em `/cnpj/[cnpj]`.

### Stories paralelas (mesmo sprint)

- SEO-PROG-002, SEO-PROG-003, SEO-PROG-004 (mesmo padrão, rotas diferentes — implementação independente).

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | Status | Notes |
|---|---|---|---|
| 1 | Clear and objective title | OK | Título preciso: rota + transição SSR→ISR + cap top-1000 |
| 2 | Complete description | OK | Contexto cita problema atual em linhas 49-51, vincula a wedge PR #529, justifica P0 |
| 3 | Testable acceptance criteria | OK | AC1-AC7 todos testáveis com Given/When/Then ou checklist binário; inclui regression test SEN-FE-001 |
| 4 | Well-defined scope (IN/OUT) | OK | Scope IN/OUT explícitos, OUT lista 5 itens deferidos para outras stories |
| 5 | Dependencies mapped | OK | Entrada: RES-BE-002 + SEO-PROG-008. Saída: SEO-PROG-006/011/012. Paralelas: 002/003/004 |
| 6 | Complexity estimate | OK | Effort M (3-4 dias) consistente com escopo (refator single-route + tests + flag) |
| 7 | Business value | OK | Vincula explícito a evitar reincidência P0 + tese 100% inbound |
| 8 | Risks documented | OK | 5 triggers + 3 ações rollback (soft/hard/reduce SSG) + soft-rollback via env var |
| 9 | Criteria of Done | OK | DoD 12 itens incluindo build artifact validation, Rich Results, GSC inspection, Sentry verification |
| 10 | Alignment with PRD/Epic | OK | Cita epic + plano + memories (SEN-FE-001, build_hammers); padrão técnico canônico (revalidate=3600, dynamicParams=true) consistente com SEO-PROG-002..005 |

### Observations

- Padrão técnico (revalidate=3600 + next.revalidate alignment + AbortSignal.timeout + HTTP 503 fallback + noindex thin) é canônico e replicável nas stories irmãs.
- Feature flag `SEO_ROUTE_MODE_CNPJ` provê soft-rollback em <3min — excelente.
- AC1 inclui TODO @architect sobre param `order=volume_24m` no endpoint backend — aceitável como follow-up condicional, não bloqueante para Ready.
- Audit grep `cache: 'no-store'` em AC4 protege contra recidiva SEN-FE-001 documentada na memory.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada a partir do plano EPIC-SEO-PROG seção SEO-PROG-001 | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). Padrão canônico para stories irmãs. Status Draft→Ready. | @po (Pax) |
