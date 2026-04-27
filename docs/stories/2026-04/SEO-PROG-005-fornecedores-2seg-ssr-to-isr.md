# SEO-PROG-005: Migrar `fornecedores/[cnpj]/[uf]` (2-segment) SSR puro → ISR + canonical (top-1000 pares)

**Priority:** P0
**Effort:** M (3-4 dias)
**Squad:** @dev + @architect
**Status:** Ready
**Epic:** [EPIC-SEO-PROG-2026-Q2](EPIC-SEO-PROG-2026-Q2.md)
**Sprint:** Sprint 3 (13–19/mai)
**Sprint Window:** 2026-05-13 → 2026-05-19
**Bloqueado por:** RES-BE-002, SEO-PROG-001 (precedente single-segment estável)

---

## Contexto

A rota `/fornecedores/[cnpj]/[uf]` é **2-segment dinâmico** — perfil de fornecedor filtrado por UF de atuação (ex: `/fornecedores/12345678000100/SP` mostra contratos do CNPJ apenas em São Paulo). Universo combinatório: ~5k CNPJs × 27 UFs = 135k pares teóricos. Top-1000 pares por volume cobre ~85% das impressões (cauda longa pulverizada).

**Problema atual** (estimado, mesmo padrão de `cnpj/[cnpj]`):

```ts
export const revalidate = 86400;
export function generateStaticParams() {
  return []; // SSR on-demand
}
```

**Defeitos específicos do 2-segment**:

1. **Fan-out duplicado:** `/fornecedores/[cnpj]` (single-segment, já existe) + `/fornecedores/[cnpj]/[uf]` (2-segment). Sem canonical correto, Google indexa as duas variantes como **conteúdo duplicado** → penalty + crawl budget waste.
2. **Universo combinatório explosivo:** sem cap, `dynamicParams=true` permite crawler atacar URLs inventados (`/fornecedores/{cnpj}/ZZ` com UF inexistente) → backend hammer.
3. **Validação UF:** UFs válidos = 27 brasileiros. Slug fora da whitelist deve ser 404 hard.

**Por que P0:** rota tem alto query-intent ("CNPJ X licitações em SP"). Sem ISR + canonical, é vetor direto de duplicate content + saturação backend (mesmo padrão wedge PR #529).

---

## Acceptance Criteria

### AC1: Migração ISR + top-1000 pares SSG

**Given** rota em SSR puro 2-segment
**When** @dev refatora
**Then**:

- [ ] `export const revalidate = 3600` (1h, alinhado com `/cnpj/[cnpj]`)
- [ ] `export const dynamicParams = true` (fallback blocking para long-tail válido)
- [ ] `generateStaticParams` retorna top-1000 pares `(cnpj, uf)` por volume:

```ts
export async function generateStaticParams(): Promise<{ cnpj: string; uf: string }[]> {
  const backendUrl =
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    'http://localhost:8000';
  try {
    const res = await fetch(
      `${backendUrl}/v1/sitemap/fornecedores-cnpj-uf?limit=1000&order=volume_24m`,
      {
        next: { revalidate: 3600 },
        signal: AbortSignal.timeout(10000),
      },
    );
    if (!res.ok) {
      console.error(`[fornecedores-uf] generateStaticParams HTTP ${res.status}`);
      return [];
    }
    const data = await res.json();
    return ((data.pairs as { cnpj: string; uf: string }[]) ?? []).map(({ cnpj, uf }) => ({
      cnpj,
      uf,
    }));
  } catch (err) {
    console.error('[fornecedores-uf] generateStaticParams failed', err);
    return [];
  }
}
```

- [ ] Backend endpoint `/v1/sitemap/fornecedores-cnpj-uf?limit=N&order=volume_24m` retorna `{pairs: [{cnpj, uf}, ...]}` (TODO @architect: verificar se endpoint existe; se não, criar follow-up backend story para spec do payload `{pairs}`)
- [ ] Fetch interno (`fetchPerfilUf` ou similar) usa `next: { revalidate: 3600 }` + `AbortSignal.timeout(10000)`

### AC2: UF whitelist validation (anti crawler abuse)

**Given** crawler envia request com UF inválido (e.g., `ZZ`, `XX`, lowercase, etc.)
**When** runtime ISR processa
**Then**:

- [ ] Whitelist 27 UFs brasileiros: `['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']`
- [ ] Validação no início da rota:

```ts
const VALID_UFS = new Set(['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']);

export default async function FornecedorUfPage({
  params,
}: {
  params: Promise<{ cnpj: string; uf: string }>;
}) {
  const { cnpj, uf } = await params;
  if (!VALID_UFS.has(uf.toUpperCase())) {
    notFound(); // 404 hard, não permite SSR runtime de UF inválida
  }
  // ... continua
}
```

- [ ] UF normalizada para uppercase antes do fetch backend
- [ ] Counter `smartlic_invalid_uf_requests_total{route="/fornecedores/[cnpj]/[uf]"}` incrementado (Sentry breadcrumb)

### AC3: Canonical anti-duplicate content

**Given** `/fornecedores/{cnpj}` (single-segment) e `/fornecedores/{cnpj}/{uf}` (2-segment) coexistem
**When** crawler indexa
**Then**:

- [ ] `/fornecedores/{cnpj}/{uf}` declara `<link rel="canonical" href="/fornecedores/{cnpj}/{uf}" />` (self-canonical — é a URL canônica para o filtro UF)
- [ ] **NÃO** canonical para single-segment (`/fornecedores/{cnpj}`) — são entidades de pageview distintas com agregações diferentes
- [ ] BreadcrumbList JSON-LD inclui pai `/fornecedores/{cnpj}`:

```json
{
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Início", "item": "https://smartlic.tech"},
    {"@type": "ListItem", "position": 2, "name": "Fornecedores", "item": "https://smartlic.tech/fornecedores"},
    {"@type": "ListItem", "position": 3, "name": "{razao_social}", "item": "https://smartlic.tech/fornecedores/{cnpj}"},
    {"@type": "ListItem", "position": 4, "name": "{razao_social} em {uf}", "item": "https://smartlic.tech/fornecedores/{cnpj}/{uf}"}
  ]
}
```

- [ ] `metadata.alternates.canonical` setado dinamicamente em `generateMetadata`

### AC4: HTTP 503 fallback graceful

- [ ] Backend down → fallback noindex + texto "Estatísticas regionais temporariamente indisponíveis"
- [ ] Sentry tags={cnpj, uf, outcome=backend_unavailable}

### AC5: Noindex se par tem `total_contratos_uf < 3`

**Given** par `(cnpj, uf)` tem volume baixo nesta UF (mesmo que CNPJ tenha alto volume nacional)
**When** crawler acessa
**Then**:

- [ ] `metadata.robots = { index: false, follow: true }` (follow=true para preservar PageRank flow ao parent `/fornecedores/{cnpj}`)
- [ ] Threshold via `process.env.MIN_ACTIVE_BIDS_FOR_INDEX_UF ?? '3'` (lower bar que single-segment já que é filtro especializado)
- [ ] Backend filter no endpoint sitemap (não retorna pares thin)

### AC6: Cache alignment audit

- [ ] Zero `cache: 'no-store'` em `frontend/app/fornecedores/`
- [ ] Comentário SEN-FE-001 inline.

### AC7: Feature flag rollback

- [ ] `SEO_ROUTE_MODE_FORNECEDORES_UF=ssr` reverte
- [ ] Documentar em `.env.example`

### AC8: Observabilidade

- [ ] Counter `nextjs_isr_revalidate_total{route="/fornecedores/[cnpj]/[uf]",outcome}`
- [ ] Counter `smartlic_invalid_uf_requests_total{route}` (anti-crawler-abuse)
- [ ] Sentry tags={cnpj, uf, outcome, latency_ms}

### AC9: Testes

- [ ] **Unit:** `frontend/__tests__/app/fornecedores/cnpj-uf-page.test.ts`:
  - `generateStaticParams` retorna top-1000 pares
  - UF whitelist rejeita inválidos (lowercase, ZZ, etc.)
  - Canonical correto (self, não parent)
- [ ] **E2E Playwright:** `frontend/e2e-tests/seo/fornecedores-cnpj-uf-isr.spec.ts`:
  - Top par (CNPJ + SP) → 200 + canonical self + BreadcrumbList completo + LCP<2.5s
  - UF inválido (`/fornecedores/{cnpj}/ZZ`) → 404 hard
  - Long-tail par válido (UF=AC raro) → fallback blocking 200 OK + ISR cache
  - Backend mock 503 → fallback noindex
- [ ] **Lighthouse smoke:** top-3 pares.
- [ ] **Rich Results Test:** BreadcrumbList 4-level.

---

## Scope

**IN:**
- Refator `frontend/app/fornecedores/[cnpj]/[uf]/page.tsx` ISR + top-1000 pares
- UF whitelist + canonical anti-duplicate
- HTTP 503 fallback + noindex thin pair
- Feature flag `SEO_ROUTE_MODE_FORNECEDORES_UF`
- Cache alignment audit
- Testes unit + E2E + Lighthouse + Rich Results
- Prometheus + Sentry
- Counter `smartlic_invalid_uf_requests_total`

**OUT:**
- `/fornecedores/[cnpj]` (single-segment) — escopo separado, já existe e funciona; refator se necessário em follow-up
- `/fornecedores` (index hub) — já SSG
- `<RelatedPages />` (SEO-PROG-011)
- Backend endpoint redesign profundo

---

## Definition of Done

- [ ] Top-1000 pares pré-populados (CI artifact)
- [ ] UF whitelist enforced (27 UFs)
- [ ] Canonical self correto (não parent) em todas páginas
- [ ] Long-tail pares válidos via fallback blocking
- [ ] Lighthouse CI top-3 pares: LCP<2.5s, INP<200ms, CLS<0.1
- [ ] Rich Results Test pass: BreadcrumbList 4-level
- [ ] GSC URL Inspection top-3 pares: HTTP 200
- [ ] Counter `smartlic_invalid_uf_requests_total` ativo (validação anti-abuse)
- [ ] Bundle delta < +0KB
- [ ] Feature flag em `.env.example`
- [ ] Zero `cache: 'no-store'`
- [ ] CodeRabbit clean
- [ ] PR aprovado @qa + @architect
- [ ] Change Log atualizado

---

## Dev Notes

### Paths absolutos

- **Rota:** `/mnt/d/pncp-poc/frontend/app/fornecedores/[cnpj]/[uf]/page.tsx`
- **Parent rota:** `/mnt/d/pncp-poc/frontend/app/fornecedores/[cnpj]/page.tsx` (NÃO modificar — escopo separado)
- **Backend endpoint sitemap pares:** TODO @architect — verificar `/v1/sitemap/fornecedores-cnpj-uf` ou criar follow-up backend para spec
- **Backend endpoint perfil:** `/mnt/d/pncp-poc/backend/routes/fornecedores.py` (precisa `_run_with_budget` — RES-BE-002)
- **Tests:** `/mnt/d/pncp-poc/frontend/__tests__/app/fornecedores/` + `/mnt/d/pncp-poc/frontend/e2e-tests/seo/`

### UF whitelist source of truth

- 27 UFs brasileiros constante em `frontend/lib/sectors.ts` (SECTORS) ou `frontend/lib/cities.ts` (CITIES) — verificar se existe util `BRAZIL_UFS` reutilizável; senão, hardcode no page.tsx.

### Canonical strategy

- Canonical self (`/fornecedores/{cnpj}/{uf}`) é correto porque a página representa subset diferente de `/fornecedores/{cnpj}` (filtro UF). Google trata como entidade distinta.
- BreadcrumbList provê o link estrutural ao parent.
- Anti-duplicate é via **conteúdo distinto** (agregações UF-specific), não canonical to parent.

### Padrões existentes

- Pattern fetch + AbortSignal: replicar de `cnpj/[cnpj]/page.tsx` (após SEO-PROG-001 stable).
- BreadcrumbList JSON-LD: util em `lib/seo.ts` se existir.

### Testing standards

- Mockar fetch global. Testar UF lowercase explicitamente (regression: caso `sp` sem upper deve 404 hard, não 200).
- E2E top par: usar fixture estável (CNPJ ativo + SP).

---

## Risk & Rollback

### Triggers

| Trigger | Threshold | Detecção |
|---|---|---|
| Build OOM | exit 137 | Railway |
| LCP top-3 | >3.5s | Lighthouse |
| GSC duplicate content warnings | aparece em GSC | GSC manual review |
| Backend wedge `fornecedores_uf` | timeout >0/min | Prometheus |
| Crawler abuse UFs inválidos | counter >100/min | Prometheus alert |

### Ações

1. Soft: `SEO_ROUTE_MODE_FORNECEDORES_UF=ssr` + redeploy.
2. Hard: revert PR via @devops.
3. Reduce SSG: `SEO_TOP_FORNECEDORES_UF_LIMIT=300`.
4. Crawler abuse mitigation: bloquear UA específico em `robots.txt` ou Cloudflare WAF (escalate a @devops).

---

## Dependencies

### Entrada

- RES-BE-002 (backend `fornecedores` rota com budget)
- SEO-PROG-001 (precedente single-segment estável; valida pattern + sentry instrumentação)
- SEO-PROG-008 (Dockerfile BACKEND_URL)

### Saída

- SEO-PROG-006 (sitemap shard 4 consume pares)
- SEO-PROG-011 (RelatedPages)

### Paralelas

- Nenhuma no Sprint 3 (esta é a única SSR→ISR migration na sprint).

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | Status | Notes |
|---|---|---|---|
| 1 | Clear and objective title | OK | Título preciso: 2-segment + canonical + cap top-1000 pares |
| 2 | Complete description | OK | Identifica 3 defeitos específicos do 2-segment: fan-out duplicado, universo combinatório, UF inválida |
| 3 | Testable acceptance criteria | OK | AC1-AC9 testáveis; UF whitelist explícita (27 UFs); canonical strategy clara |
| 4 | Well-defined scope (IN/OUT) | OK | OUT separa explicitamente `/fornecedores/[cnpj]` single-segment (escopo distinto) |
| 5 | Dependencies mapped | OK | Bloqueado por SEO-PROG-001 (precedente single-segment); Entrada/Saída completas |
| 6 | Complexity estimate | OK | Effort M apropriado para 2-segment + canonical + whitelist + counter abuse-detection |
| 7 | Business value | OK | Query-intent natural + previne wedge backend |
| 8 | Risks documented | OK | 5 triggers; ação 4 inclui WAF escalation para crawler abuse |
| 9 | Criteria of Done | OK | 13 itens; valida UF whitelist + canonical self + counter abuse |
| 10 | Alignment with PRD/Epic | OK | Padrão SEN-FE-001 + canonical strategy + threshold MIN_ACTIVE_BIDS_FOR_INDEX_UF=3 (lower bar) justificado |

### Observations

- Decisão "canonical self, não parent" (AC3) é tecnicamente correta — agregações UF-specific são entidades distintas.
- Counter `smartlic_invalid_uf_requests_total` (AC2/AC8) é defesa proativa contra crawler abuse — excelente.
- Threshold UF=3 (vs single-segment=5) reflete que filtro especializado tem volume natural menor.
- Sequenciamento (Sprint 3, após SEO-PROG-001 estável) é correto: pattern + sentry instrumentação validados antes de 2-segment.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — 2-segment com canonical + UF whitelist | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). Canonical self + UF whitelist + counter abuse approved. Status Draft→Ready. | @po (Pax) |
