# SEO-PROG-004: Migrar `observatorio/[slug]` SSR puro → ISR (todos slugs ativos, evergreen 24h)

**Priority:** P0
**Effort:** S (1-2 dias)
**Squad:** @dev + @architect
**Status:** Ready
**Epic:** [EPIC-SEO-PROG-2026-Q2](EPIC-SEO-PROG-2026-Q2.md)
**Sprint:** Sprint 2 (06–12/mai)
**Sprint Window:** 2026-05-06 → 2026-05-12
**Bloqueado por:** RES-BE-002 (rotas backend `_run_with_budget`)

---

## Contexto

A rota `/observatorio/[slug]` renderiza análises editoriais de longo prazo do mercado B2G (raio-X mensal de setores, panoramas regionais, datasets curados Lei 14.133). Universo limitado: 50-200 slugs ativos (evergreen content; cresce ~5-10/mês via produção editorial). Cada página inclui JSON-LD `Dataset` com licença CC-BY-4.0 (memory `STORY-OBS-001`).

**Problema atual** (`frontend/app/observatorio/[slug]/page.tsx`):

Mesmo padrão SSR puro (`generateStaticParams = []` ou ausente). Como o universo é limitado e 100% evergreen (artigos editoriais não mudam após publicação além de tweaks), pré-construir **todos** os slugs em SSG é trivialmente seguro e elimina 100% das requests crawler do failure path backend.

**Por que P0:** observatório é a rota com **maior CTR potencial** (conteúdo editorial autoritativo, JSON-LD Dataset CC-BY-4.0 é eligible para Google Dataset Search + AI Overviews via Google-Extended whitelist em `robots.txt`). Mas atualmente cada hit dispara fetch Supabase → mesmo padrão precursor wedge. Fix é o de menor esforço/maior valor da Sprint 2.

**Por que esforço S (não M):**

- Universo pequeno (≤200) elimina build OOM risk.
- Conteúdo evergreen → `revalidate = 86400` (24h) é generoso e estável.
- Sem fallback blocking necessário (todos slugs ativos pré-construídos; long-tail = inválido = 404).
- Sem threshold thin-content (curadoria editorial garante quality bar).

---

## Acceptance Criteria

### AC1: Migração ISR + SSG completo (todos slugs ativos)

**Given** rota em SSR puro
**When** @dev refatora
**Then**:

- [ ] `export const revalidate = 86400` (24h — evergreen)
- [ ] `export const dynamicParams = false` (slugs fora da lista = 404 hard, comportamento desejado já que universo é editorial-curado)
- [ ] `generateStaticParams` retorna **todos** slugs ativos:

```ts
export async function generateStaticParams(): Promise<{ slug: string }[]> {
  const backendUrl =
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    'http://localhost:8000';
  try {
    const res = await fetch(`${backendUrl}/v1/observatorio/slugs`, {
      next: { revalidate: 86400 },
      signal: AbortSignal.timeout(10000),
    });
    if (!res.ok) {
      console.error(`[observatorio] generateStaticParams HTTP ${res.status}`);
      return [];
    }
    const data = await res.json();
    return ((data.slugs as string[]) ?? []).map((slug) => ({ slug }));
  } catch (err) {
    console.error('[observatorio] generateStaticParams failed', err);
    return [];
  }
}
```

- [ ] Backend endpoint `/v1/observatorio/slugs` retorna slugs com `is_published=true` (TODO @architect: verificar se endpoint já existe; caso contrário, criar follow-up backend leve)
- [ ] Fetch interno de conteúdo (`fetchObservatorio` ou similar) usa `next: { revalidate: 86400 }` alinhado

### AC2: Manter JSON-LD Dataset CC-BY-4.0

**Given** página inclui Dataset schema com license CC-BY-4.0
**When** @dev refatora
**Then**:

- [ ] JSON-LD `Dataset` permanece intacto:

```ts
const datasetSchema = {
  '@context': 'https://schema.org',
  '@type': 'Dataset',
  name: `...`,
  description: `...`,
  creator: { '@type': 'Organization', name: 'SmartLic', url: 'https://smartlic.tech' },
  license: 'https://creativecommons.org/licenses/by/4.0/',
  // ...
};
```

- [ ] License URL é `https://creativecommons.org/licenses/by/4.0/` (não `https://dados.gov.br/...` que é PNCP-specific)
- [ ] BreadcrumbList JSON-LD presente

### AC3: HTTP 503 fallback graceful (defensive)

**Given** backend `/v1/observatorio/{slug}` indisponível em runtime ISR (raro — pages SSG estáticos)
**When** revalidação falha
**Then**:

- [ ] Stale-while-revalidate: serve último build success, não fallback degradado (Next.js ISR default behavior)
- [ ] Sentry breadcrumb `observatorio_revalidate_failed` tags={slug, outcome}

### AC4: Cache alignment audit

- [ ] Zero `cache: 'no-store'` em `frontend/app/observatorio/`
- [ ] Comentário inline SEN-FE-001:

```ts
// SEN-FE-001 + SEO-PROG-004: revalidate page-level (86400) + fetch next.revalidate alinhados.
// Evergreen content; dynamicParams=false (universo curado).
```

### AC5: Feature flag rollback

- [ ] `SEO_ROUTE_MODE_OBSERVATORIO=ssr` reverte para `generateStaticParams=[]` + `revalidate=0`
- [ ] Documentar em `.env.example`

### AC6: Observabilidade

- [ ] Counter `nextjs_isr_revalidate_total{route="/observatorio/[slug]",outcome}`
- [ ] Sentry tags={slug, outcome, latency_ms}

### AC7: Testes

- [ ] **Unit:** `frontend/__tests__/app/observatorio/observatorio-page.test.ts`:
  - `generateStaticParams` retorna lista completa quando backend OK
  - `[]` em error
- [ ] **E2E Playwright:** `frontend/e2e-tests/seo/observatorio-isr.spec.ts`:
  - Visit slug ativo → 200 + Dataset JSON-LD CC-BY-4.0 + LCP<2.5s
  - Visit slug inválido → 404 (não fallback dinâmico, dynamicParams=false)
- [ ] **Lighthouse smoke:** top-3 slugs (raio-x mensal, panorama regional, dataset curado).
- [ ] **Rich Results Test:** Dataset com license válida (CC-BY-4.0).
- [ ] **Google Dataset Search readiness:** verificar `https://datasetsearch.research.google.com/search?query=site:smartlic.tech` cobertura pós-deploy (smoke manual, não automatizado).

---

## Scope

**IN:**
- Refator `frontend/app/observatorio/[slug]/page.tsx` ISR completo
- `dynamicParams=false` (universo curado)
- Manter Dataset CC-BY-4.0
- Cache alignment audit
- Feature flag `SEO_ROUTE_MODE_OBSERVATORIO`
- Testes unit + E2E + Lighthouse smoke
- Prometheus + Sentry

**OUT:**
- `/observatorio` (index page) — já SSG
- `/observatorio/embed` — fora de escopo (componente de embed externo)
- `<RelatedPages />` (SEO-PROG-011)
- Backend novo de slugs (assumindo endpoint existe; follow-up se não)

---

## Definition of Done

- [ ] Todos slugs ativos pré-populados em build (CI artifact)
- [ ] `dynamicParams=false` valida 404 hard para slugs fora da lista
- [ ] Lighthouse CI top-3 slugs: LCP<2.5s, INP<200ms, CLS<0.1
- [ ] Rich Results Test pass: Dataset CC-BY-4.0
- [ ] GSC URL Inspection top-3: HTTP 200
- [ ] Bundle delta < +0KB
- [ ] Feature flag em `.env.example`
- [ ] Zero `cache: 'no-store'` em `app/observatorio/`
- [ ] CodeRabbit clean
- [ ] PR aprovado @qa + @architect
- [ ] Counter Prometheus ativo
- [ ] Change Log atualizado

---

## Dev Notes

### Paths absolutos

- **Rota:** `/mnt/d/pncp-poc/frontend/app/observatorio/[slug]/page.tsx`
- **Embed (fora de escopo):** `/mnt/d/pncp-poc/frontend/app/observatorio/embed/`
- **Backend endpoint slugs:** TODO @architect — verificar se `/v1/observatorio/slugs` existe; caso contrário, criar follow-up backend story leve (1h dev) + grep `backend/routes/observatorio.py`
- **Backend endpoint conteúdo:** `/mnt/d/pncp-poc/backend/routes/observatorio.py`
- **Tests:** `/mnt/d/pncp-poc/frontend/__tests__/app/observatorio/` + `/mnt/d/pncp-poc/frontend/e2e-tests/seo/`

### Padrões existentes

- JSON-LD Dataset CC-BY pattern (já presente — não reinventar). Verificar `creator.name = 'SmartLic'` + `creator.url = 'https://smartlic.tech'`.
- BreadcrumbList JSON-LD (utilities em `lib/seo.ts` se existirem).

### Threshold revalidate justificativa

- 86400s (24h) é generoso porque conteúdo é evergreen. Updates editoriais raros (revisões factuais) reflectem em até 24h via ISR — aceitável para nicho B2G.
- Compare: `/cnpj/[cnpj]` 3600s, `/orgaos/[slug]` 7200s, `/itens/[catmat]` 3600s.

### Testing standards

- Mockar fetch global. Top-3 fixtures: usar slugs reais de raio-x produzidos (via `getAllObservatorioSlugs` se utility existe).
- Lighthouse focus: TTFB<600ms (SSG pré-construído deve servir <100ms TTFB sem regression Sentry overhead).

### Why dynamicParams=false (vs others)

- `/cnpj/[cnpj]`, `/orgaos/[slug]`, `/itens/[catmat]`, `/fornecedores/[cnpj]/[uf]` usam `dynamicParams=true` (fallback blocking) — universo grande, long-tail viável.
- `/observatorio/[slug]` usa `dynamicParams=false` — universo editorial curado; slug fora da lista deve ser 404 hard (não tentativa de SSR runtime). Previne crawler abuse de URLs inventados.

---

## Risk & Rollback

### Triggers

| Trigger | Threshold | Detecção |
|---|---|---|
| Build OOM | exit 137 (improvável com ≤200 pages) | Railway logs |
| LCP top-3 | >3.5s | Lighthouse |
| GSC clicks `/observatorio/*` 7d | -30% | GSC API |
| Sentry errors | >5/min | Sentry |

### Ações

1. Soft: `SEO_ROUTE_MODE_OBSERVATORIO=ssr` + redeploy.
2. Hard: revert PR via @devops.

---

## Dependencies

### Entrada

- RES-BE-002 (backend `observatorio` rotas com budget — light dependency since SSG pré-popula maioria)
- SEO-PROG-008 (Dockerfile BACKEND_URL ARG)

### Saída

- SEO-PROG-006 (sitemap shard 0 ou 4 — observatório está em shard 0 atualmente como hub `/observatorio` + slugs em sitemap dinâmico)
- SEO-PROG-011 (RelatedPages)
- SEO-PROG-012 (Schema expansion)

### Paralelas

- SEO-PROG-001, 002, 003 (mesmo sprint, rotas independentes)

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | Status | Notes |
|---|---|---|---|
| 1 | Clear and objective title | OK | Título preciso: rota + transição + universo evergreen 24h |
| 2 | Complete description | OK | Justifica `dynamicParams=false` (universo curado editorial) |
| 3 | Testable acceptance criteria | OK | AC1-AC7 testáveis; Dataset CC-BY-4.0 schema preservado |
| 4 | Well-defined scope (IN/OUT) | OK | OUT inclui `/observatorio/embed` (componente externo) — clear separation |
| 5 | Dependencies mapped | OK | Light dependency em RES-BE-002 (SSG pré-popula maioria) |
| 6 | Complexity estimate | OK | Effort S justificado: universo ≤200 + evergreen + dynamicParams=false (sem fallback blocking) |
| 7 | Business value | OK | "Maior CTR potencial" + Dataset CC-BY eligible para Google Dataset Search + AI Overviews |
| 8 | Risks documented | OK | 4 triggers; build OOM improvável (universo ≤200) |
| 9 | Criteria of Done | OK | 11 itens; valida dynamicParams=false → 404 hard para slugs fora |
| 10 | Alignment with PRD/Epic | OK | revalidate=86400 (evergreen) diferenciado dos demais; razão técnica documentada em Dev Notes |

### Observations

- Decisão `dynamicParams=false` (vs sister stories com `=true`) é tecnicamente correta para universo curado editorial.
- AC1 contém TODO @architect sobre endpoint `/v1/observatorio/slugs` — aceitável: `if not exists, follow-up backend leve (1h dev)`.
- License CC-BY-4.0 (vs PNCP-specific) é precedente memory `STORY-OBS-001` — preservado corretamente.
- Google Dataset Search readiness é smoke manual (não automatizado) — adequado para esforço S.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — esforço S (universo limitado evergreen) | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). dynamicParams=false justificado. Status Draft→Ready. | @po (Pax) |
