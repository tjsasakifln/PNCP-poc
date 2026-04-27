# SEO-PROG-003: Migrar `itens/[catmat]` SSR puro → ISR + fallback blocking (top-5000 CATMAT)

**Priority:** P0
**Effort:** M (3-4 dias)
**Squad:** @dev + @architect
**Status:** Ready
**Epic:** [EPIC-SEO-PROG-2026-Q2](EPIC-SEO-PROG-2026-Q2.md)
**Sprint:** Sprint 2 (06–12/mai)
**Sprint Window:** 2026-05-06 → 2026-05-12
**Bloqueado por:** RES-BE-002 (rotas backend `_run_with_budget`)

---

## Contexto

A rota `/itens/[catmat]` renderiza benchmark de preços por código CATMAT (P10/P50/P90, valor médio, contratos referência, FAQs por item, JSON-LD `Dataset`). Universo total CATMAT: ~500k códigos no PNCP. Top-5000 por volume cobre >90% das impressões esperadas (cauda longa de 495k cobre <10%, predominantemente "discovered, not indexed" no GSC).

**Problema atual** (`frontend/app/itens/[catmat]/page.tsx:60-72`):

```ts
export async function generateStaticParams() {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  try {
    const res = await fetch(`${backendUrl}/v1/sitemap/itens`, {
      cache: 'no-store',  // ❌ ANTIPATTERN SEN-FE-001
      signal: AbortSignal.timeout(15000),
    });
    if (!res.ok) return [];
    const data = await res.json();
    const catmats: string[] = (data.catmats || []).slice(0, _MAX_STATIC_CATMATS); // 200
    return catmats.map((catmat) => ({ catmat }));
  } catch {
    return [];
  }
}
```

**Dois defeitos críticos**:

1. **`cache: 'no-store'` em rota com `revalidate=86400`** = SEN-FE-001 recidiva ativa em produção. Quebra SSG silenciosamente (build aceita, runtime SSR puro). Memory `feedback_sen_fe_001_recidiva_sitemap.md` advertiu que precisamos grep global pós-fix de cada ocorrência. Esta foi missed em 2026-04-24.
2. **`_MAX_STATIC_CATMATS = 200`** é under-provisioned para universo de 500k. Plano aprovou top-5000 (25× incremento) por que CATMAT é alta-cardinalidade e cauda comprida domina.

**Por que P0:** itens CATMAT são query-intent natural ("preço médio papel A4 governo", "valor unitário aço estrutural licitação"). É o nicho de maior potencial de captura de tráfego comercial (B2G procurement teams pesquisam preços antes de propostas). Defeito atual queima crawl budget e nem indexa direito.

---

## Acceptance Criteria

### AC1: Migração ISR + top-5000 SSG params + fix SEN-FE-001 antipattern

**Given** `frontend/app/itens/[catmat]/page.tsx:64` usa `cache: 'no-store'` (SEN-FE-001 antipattern)
**When** @dev refatora
**Then**:

- [ ] **CRITICAL FIX:** linha 64 muda de `cache: 'no-store'` para `next: { revalidate: 3600 }` em `generateStaticParams`
- [ ] `_MAX_STATIC_CATMATS` muda de 200 para 5000 (constante exportada para test/feature flag)
- [ ] `export const revalidate = 3600` (substitui atual `86400` — preços CATMAT mudam diariamente, mas sob carga 24h é aceitável; 1h alinha com sitemap ISR)
- [ ] `export const dynamicParams = true` (explícito)
- [ ] Endpoint `/v1/sitemap/itens?limit=5000&order=volume_24m` (TODO @architect: param `order` ou follow-up backend)

```ts
const _MAX_STATIC_CATMATS = parseInt(process.env.SEO_TOP_CATMAT_LIMIT ?? '5000', 10);

export const revalidate = 3600;
export const dynamicParams = true;

export async function generateStaticParams(): Promise<{ catmat: string }[]> {
  const backendUrl =
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    'http://localhost:8000';
  try {
    const res = await fetch(
      `${backendUrl}/v1/sitemap/itens?limit=${_MAX_STATIC_CATMATS}&order=volume_24m`,
      {
        // SEN-FE-001 + SEO-PROG-003: revalidate alignment com page-level (3600s).
        // ANTERIORMENTE usava `cache: 'no-store'` — recidiva do antipattern fatal Next.js 16.
        next: { revalidate: 3600 },
        signal: AbortSignal.timeout(15000),
      },
    );
    if (!res.ok) {
      console.error(`[itens] generateStaticParams HTTP ${res.status}`);
      return [];
    }
    const data = await res.json();
    return ((data.catmats as string[]) ?? [])
      .slice(0, _MAX_STATIC_CATMATS)
      .map((catmat) => ({ catmat }));
  } catch (err) {
    console.error('[itens] generateStaticParams failed', err);
    return [];
  }
}
```

### AC2: `fetchProfile` cache alignment

**Given** `fetchProfile` na linha 47 já usa `next: { revalidate: 86400 }` (mas page agora é 3600)
**When** @dev alinha
**Then**:

- [ ] `fetchProfile` usa `next: { revalidate: 3600 }` consistente com page-level
- [ ] Mantém `AbortSignal.timeout(10000)`
- [ ] Adiciona Sentry capture em HTTP 5xx + timeout

### AC3: HTTP 503 fallback graceful

- [ ] Página renderiza fallback quando backend indisponível
- [ ] Meta noindex + texto "Benchmark de preços temporariamente indisponível"
- [ ] Sentry tags={catmat, outcome=backend_unavailable}

### AC4: Long-tail noindex thin content

**Given** CATMAT existe mas tem `total_contratos < 5`
**When** crawler acessa
**Then**:

- [ ] `metadata.robots = { index: false, follow: false }`
- [ ] Threshold via `process.env.MIN_ACTIVE_BIDS_FOR_INDEX ?? '5'`
- [ ] Backend filter no endpoint sitemap (não retorna CATMATs thin)

### AC5: Cache alignment audit (CRITICAL — anti SEN-FE-001 recidiva)

**Given** memory `feedback_sen_fe_001_recidiva_sitemap.md` advertiu sobre recidiva
**When** @dev faz audit
**Then**:

- [ ] `grep -r "cache: 'no-store'" frontend/app/itens/` retorna **zero**
- [ ] **GLOBAL AUDIT obrigatório (escopo desta story):** `grep -rn "cache: 'no-store'" frontend/app/` documentado em PR description; cada ocorrência adicional triagem (deixar para outras stories ou fixar inline)
- [ ] Comentário inline no fetch:

```ts
// SEN-FE-001 + SEO-PROG-003: rota antiga tinha `cache: 'no-store'` em generateStaticParams +
// `revalidate=86400` page-level — antipattern fatal Next.js 16 que quebrava SSG silenciosamente.
// Migrado para alignment estrito: page revalidate=3600 + fetch next.revalidate=3600.
```

### AC6: Feature flag rollback + SSG limit override

- [ ] `SEO_ROUTE_MODE_ITENS=ssr` reverte para SSR puro
- [ ] `SEO_TOP_CATMAT_LIMIT=200` permite reduzir SSG params em build OOM (já modelado em código)
- [ ] Documentar em `.env.example` + PR runbook

### AC7: Observabilidade

- [ ] Counter `nextjs_isr_revalidate_total{route="/itens/[catmat]",outcome}`
- [ ] Sentry breadcrumb `itens_perfil_isr` tags={catmat, outcome, latency_ms}

### AC8: Testes

- [ ] **Unit:** `frontend/__tests__/app/itens/itens-page.test.ts`:
  - `generateStaticParams` retorna até 5000 itens quando backend OK
  - Retorna `[]` em HTTP 5xx ou timeout
  - **REGRESSION:** verifica que `next.revalidate` está presente (não `cache: 'no-store'`)
- [ ] **E2E Playwright:** `frontend/e2e-tests/seo/itens-isr.spec.ts`:
  - Top CATMAT (papel A4, fixture) → 200 + Dataset JSON-LD + LCP<2.5s
  - Long-tail CATMAT inválido → 404
  - Backend mock 503 → fallback noindex
- [ ] **Lighthouse smoke:** top-3 CATMATs.
- [ ] **Build output validation:** CI artifact lista 5000+ HTMLs em `.next/server/app/itens/[catmat]/`.

---

## Scope

**IN:**
- Refator `frontend/app/itens/[catmat]/page.tsx` ISR + top-5000
- **CRITICAL FIX:** SEN-FE-001 antipattern em linha 64
- Global audit `cache: 'no-store'` em `frontend/app/`
- Backend filter dependency
- HTTP 503 fallback + noindex thin
- Feature flags `SEO_ROUTE_MODE_ITENS` + `SEO_TOP_CATMAT_LIMIT`
- Testes unit + E2E + regression no antipattern
- Prometheus + Sentry

**OUT:**
- `/itens` (index page)
- `<RelatedPages />` (SEO-PROG-011)
- FAQPage JSON-LD expansion (SEO-PROG-012)
- Backend endpoint redesign

---

## Definition of Done

- [ ] Top-5000 CATMATs pré-populados em build (CI artifact list)
- [ ] **SEN-FE-001 antipattern eliminado em `app/itens/`** (regression test prova)
- [ ] Long-tail via fallback blocking + ISR 1h
- [ ] Lighthouse CI top-3 CATMATs: LCP<2.5s, INP<200ms, CLS<0.1
- [ ] Rich Results Test pass: Dataset CC-BY
- [ ] GSC URL Inspection top-3: HTTP 200
- [ ] Bundle delta < +0KB
- [ ] Feature flags em `.env.example`
- [ ] Global audit `cache: 'no-store'` documentado em PR (zero em itens, restantes triagiados)
- [ ] CodeRabbit clean
- [ ] PR aprovado @qa + @architect
- [ ] Counter Prometheus ativo
- [ ] Change Log atualizado

---

## Dev Notes

### Paths absolutos

- **Rota:** `/mnt/d/pncp-poc/frontend/app/itens/[catmat]/page.tsx`
- **Backend endpoint sitemap:** `/mnt/d/pncp-poc/backend/routes/sitemap_itens.py` (verify param `order` + filter)
- **Backend endpoint profile:** `/mnt/d/pncp-poc/backend/routes/itens.py` (precisa `_run_with_budget` — RES-BE-002)
- **Tests:** `/mnt/d/pncp-poc/frontend/__tests__/app/itens/` + `/mnt/d/pncp-poc/frontend/e2e-tests/seo/`
- **Memory referência:** `feedback_sen_fe_001_recidiva_sitemap.md`

### Build OOM risk (CRITICAL)

- 5000 SSG pages × ~50KB HTML = 250MB total. Memory `feedback_wsl_next16_build_inviavel.md` advertiu inviabilidade WSL local.
- **Validação obrigatória:** build CI deve completar em <12min com cap atual Railway. Se fail OOM:
  1. Fallback: `SEO_TOP_CATMAT_LIMIT=2000` (50% reduction)
  2. Investigar via SEO-PROG-014 (workaround `--experimental-build-mode=compile`)
  3. Última opção: defer top-5000 → top-2000 e document em ROADMAP.md

### Padrões existentes

- `MIN_ACTIVE_BIDS_FOR_INDEX` env pattern (`orgaos/[slug]/page.tsx:76`).
- Sitemap fetch já em `sitemap.ts:159-169` (`fetchSitemapItens`).

### Testing standards

- Mockar fetch global; verificar regression test acompanha que `init.cache` NÃO seja `'no-store'` quando `init.next` está presente.
- E2E top CATMAT: usar fixture estável (e.g., código CATMAT de papel A4 reams comum em compras municipais).

---

## Risk & Rollback

### Triggers

| Trigger | Threshold | Ação |
|---|---|---|
| Build OOM Railway | exit 137 | `SEO_TOP_CATMAT_LIMIT=2000` |
| LCP top-3 | >3.5s | Soft rollback |
| GSC clicks `/itens/*` | -30% 7d | Hard rollback |
| Backend wedge `itens_profile` | timeout >0/min | Soft rollback |

### Ações

1. Soft: `SEO_ROUTE_MODE_ITENS=ssr` + reduce limit.
2. Hard: revert PR via @devops.

---

## Dependencies

### Entrada

- RES-BE-002 (`itens_profile` backend budget)
- SEO-PROG-008 (Dockerfile BACKEND_URL)

### Saída

- SEO-PROG-006 (sitemap shard 4)
- SEO-PROG-011 (RelatedPages)
- SEO-PROG-012 (FAQPage)

### Paralelas

- SEO-PROG-001, 002, 004 (mesmo sprint).

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | Status | Notes |
|---|---|---|---|
| 1 | Clear and objective title | OK | Título preciso: rota + transição + cap top-5000 (25× incremento de 200) |
| 2 | Complete description | OK | Contexto identifica DOIS defeitos críticos: SEN-FE-001 antipattern ATIVO + cap under-provisioned |
| 3 | Testable acceptance criteria | OK | AC1-AC8 testáveis; AC1 inclui CRITICAL FIX claramente marcado; AC5 mandatory global audit |
| 4 | Well-defined scope (IN/OUT) | OK | IN inclui CRITICAL FIX + global audit; OUT explícito |
| 5 | Dependencies mapped | OK | Entrada/Saída/Paralelas todas mapeadas |
| 6 | Complexity estimate | OK | Effort M apropriado; build OOM risk levantado em Dev Notes (5000 pages × 50KB = 250MB) com fallback `SEO_TOP_CATMAT_LIMIT=2000` |
| 7 | Business value | OK | Vincula a CTR comercial B2G (procurement teams) — query-intent rico |
| 8 | Risks documented | OK | 4 triggers; mitigação build OOM via SEO_TOP_CATMAT_LIMIT |
| 9 | Criteria of Done | OK | DoD inclui regression test que prova SEN-FE-001 antipattern foi eliminado + audit global documentado |
| 10 | Alignment with PRD/Epic | OK | CRITICAL FIX alinha com bar específica do epic (anti SEN-FE-001 recidiva) |

### Required Fixes

Nenhum.

### Observations

- **Confirmação empírica via grep:** `cache: 'no-store'` está em linha 65 de `frontend/app/itens/[catmat]/page.tsx` (story declara linha 64; offset minor de 1 linha — dev deve ajustar referência durante implementação, não bloqueia Ready).
- AC5 inclui global audit grep como mandatório — alinha com memory `feedback_sen_fe_001_recidiva_sitemap.md` que advertiu (2026-04-24) sobre necessidade de grep global pós-fix.
- AC1 declaração "CRITICAL FIX" e regression test em AC8 são exatamente o pattern correto para prevenir 2ª recidiva.
- Build OOM mitigation em Dev Notes (`SEO_TOP_CATMAT_LIMIT=2000`) é defesa robusta.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — inclui CRITICAL FIX SEN-FE-001 recidiva (linha 64) | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). CRITICAL FIX SEN-FE-001 + audit global mandatórios. Linha real do antipattern é 65 (offset minor). Status Draft→Ready. | @po (Pax) |
