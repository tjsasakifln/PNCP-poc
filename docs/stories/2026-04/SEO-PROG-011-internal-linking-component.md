# SEO-PROG-011: Internal linking automatizado `<RelatedPages />` (cap 8 links/page, backend pré-computa)

**Priority:** P1
**Effort:** M (3-4 dias)
**Squad:** @dev + @ux-design-expert
**Status:** Ready
**Epic:** [EPIC-SEO-PROG-2026-Q2](EPIC-SEO-PROG-2026-Q2.md)
**Sprint:** Sprint 4-5 (20/mai–02/jun)
**Sprint Window:** 2026-05-20 → 2026-06-02
**Bloqueado por:** SEO-PROG-001..005 (rotas SEO ISR estáveis)

---

## Contexto

Internal linking é mecanismo de PageRank flow + crawl budget optimization. SmartLic tem componente `<RelatedPages />` em **algumas** rotas (e.g., `/cnpj/[cnpj]/page.tsx:169-174` declara hardcoded `[/cnpj, /orgaos, /calculadora, /licitacoes]`), mas:

1. **Hardcoded lists** — sem variabilidade por contexto. Todos CNPJs têm exatamente os mesmos 4 links → Google não distingue páginas.
2. **Cap 4 links** — abaixo do ideal. SEO best practice é **5-10 internal links por página** para spread PageRank.
3. **Sem matriz de relevância** — link de `/cnpj/{X}` para `/cnpj/{Y}` (CNPJ correlato no mesmo setor) não existe.
4. **Long-tail isolado** — páginas long-tail (CNPJs com baixo volume) têm poucos backlinks externos; sem internal linking robusto, ficam órfãs no graph.

**Solução:** componente `<RelatedPages />` reutilizável que recebe contexto (rota + ID) e busca **8 links relevantes** via backend pré-computado.

**Backend pré-computado é necessário** porque:
- Cálculo de relevância é caro (similarity setor/UF, co-ocorrência em editais, embeddings semânticos)
- Build-time SSG já é gargalo (memory `feedback_wsl_next16_build_inviavel.md`)
- Cache backend (Redis) compartilha entre pages

**Por que P1:** SEO ranking direto. Memory `reference_smartlic_baseline_2026_04_24`: 9.9k impressões, 126 clicks. Internal linking robusto pode 2-3x CTR + ajudar páginas long-tail a indexar.

---

## Acceptance Criteria

### AC1: Backend endpoint `/v1/seo/related`

**Given** queremos pre-compute para evitar custo runtime
**When** @data-engineer + @architect cria endpoint
**Then**:

- [ ] Backend rota `GET /v1/seo/related?route={path}&limit=8&context={json}` retorna:

```json
{
  "links": [
    {"href": "/cnpj/12345678000100", "title": "Empresa Y — Setor Saúde SP", "anchor_context": "fornecedor_correlato"},
    {"href": "/orgaos/prefeitura-sao-paulo", "title": "Prefeitura de São Paulo", "anchor_context": "orgao_principal_24m"},
    // ... até 8 links
  ],
  "computed_at": "2026-04-27T12:00:00Z"
}
```

- [ ] **TODO @data-engineer:** definir queries de relevância:
  - `/cnpj/{X}`: top fornecedores correlatos (mesmo setor + UF), top órgãos compradores, link para hub `/cnpj`
  - `/orgaos/{slug}`: top fornecedores 24m do órgão, órgãos correlatos (mesma esfera/UF), `/contratos/orgao/{cnpj}`
  - `/itens/{catmat}`: top órgãos compradores deste item, fornecedores top 24m, item correlato (mesmo CATMAT category)
  - `/observatorio/{slug}`: outros raio-x mensais recentes, blog setores correlatos
  - `/blog/licitacoes/{setor}/{uf}`: licitações em UFs vizinhas, blog setor próximo, hub setor
- [ ] Cache Redis `seo:related:{route_hash}:v1` TTL 24h
- [ ] `_run_with_budget(2s)` (RES-BE-002 pattern)
- [ ] Counter `smartlic_seo_related_request_total{route_pattern,outcome}`

### AC2: Componente React `<RelatedPages />` reutilizável

**Given** queremos componente único usado em 5+ rotas
**When** @dev + @ux-design-expert cria
**Then**:

- [ ] Criar `frontend/app/components/seo/RelatedPages.tsx`:

```tsx
import Link from 'next/link';

interface RelatedLink {
  href: string;
  title: string;
  anchor_context?: string;
}

interface RelatedPagesProps {
  links: RelatedLink[];
  heading?: string;
  variant?: 'sidebar' | 'footer' | 'inline';
}

export default function RelatedPages({
  links,
  heading = 'Páginas relacionadas',
  variant = 'footer',
}: RelatedPagesProps) {
  if (!links || links.length === 0) return null;

  // SEO-PROG-011: cap 8 hard (anti-overlinking penalty)
  const cappedLinks = links.slice(0, 8);

  return (
    <nav
      aria-label={heading}
      className={
        variant === 'sidebar'
          ? 'rounded-lg border bg-gray-50 p-4'
          : variant === 'footer'
            ? 'mt-8 border-t pt-6'
            : 'inline-flex flex-wrap gap-2'
      }
    >
      <h2 className="text-lg font-semibold mb-3">{heading}</h2>
      <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {cappedLinks.map((link) => (
          <li key={link.href}>
            <Link
              href={link.href}
              className="text-blue-600 hover:underline focus:underline"
              prefetch={false} // SEO-PROG-011: disable prefetch para não saturar backend em rotas SEO
            >
              {link.title}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
```

- [ ] **`prefetch={false}`** crítico: rotas SEO crawler-heavy não devem prefetch links em hover (saturação backend)
- [ ] Acessibilidade: `aria-label`, semantic `<nav>`, focus styles
- [ ] Responsive: mobile 1col, desktop 2col
- [ ] Variants: `sidebar` | `footer` | `inline` (UX-design-expert decide qual usar onde)
- [ ] Component is **server component** (não `'use client'`) — renderização SSR/ISR sem JS hidratado

### AC3: Server-side fetch wrapper

**Given** queremos abstrair fetch + cache + fallback
**When** @dev cria utility
**Then**:

- [ ] Criar `frontend/lib/seo-related.ts`:

```ts
import { getBackendUrl } from './backend-url';

export interface RelatedLink {
  href: string;
  title: string;
  anchor_context?: string;
}

export async function fetchRelatedPages(
  route: string,
  limit = 8,
): Promise<RelatedLink[]> {
  try {
    const res = await fetch(
      `${getBackendUrl()}/v1/seo/related?route=${encodeURIComponent(route)}&limit=${limit}`,
      {
        next: { revalidate: 3600 },
        signal: AbortSignal.timeout(5000),
      },
    );
    if (!res.ok) {
      console.warn(`[seo-related] HTTP ${res.status} for route ${route}`);
      return [];
    }
    const data = await res.json();
    return (data.links as RelatedLink[]) ?? [];
  } catch (err) {
    console.warn('[seo-related] fetch failed', err);
    return [];
  }
}
```

- [ ] Fail-open: empty array se backend down (não crasha página)
- [ ] Cache alignment: `next: { revalidate: 3600 }` consistente

### AC4: Integração nas 5 rotas SEO ISR

**Given** SEO-PROG-001..005 estão estáveis
**When** @dev integra
**Then**:

- [ ] Rotas alvo (mínimo):
  - `/cnpj/[cnpj]/page.tsx` — substituir hardcoded `relatedPages` (linha 169-174) por fetch dinâmico
  - `/orgaos/[slug]/page.tsx`
  - `/itens/[catmat]/page.tsx`
  - `/observatorio/[slug]/page.tsx`
  - `/fornecedores/[cnpj]/[uf]/page.tsx`
  - `/blog/licitacoes/[setor]/[uf]/page.tsx` (precedente)
- [ ] Pattern de uso:

```tsx
import RelatedPages from '@/app/components/seo/RelatedPages';
import { fetchRelatedPages } from '@/lib/seo-related';

export default async function CnpjPerfilPage({ params }: Props) {
  const { cnpj } = await params;
  const [perfil, related] = await Promise.all([
    fetchPerfil(cnpj),
    fetchRelatedPages(`/cnpj/${cnpj}`),
  ]);
  // ...
  return (
    <ContentPageLayout>
      {/* ... existing content ... */}
      <RelatedPages links={related} heading="Empresas e Órgãos relacionados" variant="footer" />
    </ContentPageLayout>
  );
}
```

- [ ] Promise.all para fetch paralelo (perfil + related independentes)
- [ ] **NÃO** sobrecarregar backend: fetch related é separado de fetch principal — se backend já saturando, related pode falhar gracefully (empty array)

### AC5: Existing hardcoded `<ContentPageLayout relatedPages={...}>` deprecation

**Given** `cnpj/[cnpj]/page.tsx:169-174` já usa hardcoded list
**When** @dev migra
**Then**:

- [ ] Manter prop `relatedPages` em `ContentPageLayout` como fallback (se array empty, mostra hardcoded; se preenchido, usa)
- [ ] Após validação 14 dias produção sem regressões SEO, remover prop hardcoded em PR follow-up

### AC6: Schema.org BreadcrumbList já presente, NÃO modificar

**Given** todas rotas SEO já têm BreadcrumbList JSON-LD
**When** @dev adiciona RelatedPages
**Then**:

- [ ] **NÃO** adicionar SiteNavigationElement schema (over-engineering; Google já infere)
- [ ] BreadcrumbList existing intacto
- [ ] RelatedPages é semantic HTML (`<nav>`) sem schema adicional

### AC7: Bundle delta + Lighthouse impact

- [ ] RelatedPages component server-side (`<nav>` static HTML) → bundle delta < +1KB
- [ ] Lighthouse INP impact: zero (sem JS hidratado novo)
- [ ] Lighthouse SEO score: melhora esperada (aumento de internal links)

### AC8: Testes

- [ ] **Unit:** `frontend/__tests__/lib/seo-related.test.ts`:
  - `fetchRelatedPages` retorna array em sucesso
  - Empty array em HTTP error/timeout
- [ ] **Unit:** `frontend/__tests__/components/RelatedPages.test.tsx`:
  - Renderiza N links cappados a 8
  - Variants (sidebar/footer/inline) aplicam classes corretas
  - `prefetch={false}` em todos `<Link>`
  - Empty array → renderiza nada (return null)
- [ ] **E2E Playwright:** `frontend/e2e-tests/seo/related-pages.spec.ts`:
  - Visit top CNPJ → ver `<nav aria-label="Páginas relacionadas">` + 8 links
  - Click em link related → navegação funcional + URL correto
- [ ] **Backend tests:** `backend/tests/routes/test_seo_related.py`:
  - Endpoint retorna 8 links para CNPJ válido
  - Cache hit em segunda chamada (Redis)
  - Timeout backend → retorna empty `links: []` graceful

---

## Scope

**IN:**
- Backend endpoint `/v1/seo/related?route=&limit=&context=`
- Componente `<RelatedPages />` server-side reutilizável
- Utility `fetchRelatedPages` com fail-open
- Integração em 6 rotas SEO ISR
- Counter Prometheus + cache Redis
- Tests unit + E2E + backend
- Acessibilidade (aria, semantic, focus)

**OUT:**
- ML-based recommendation (defer; queries SQL setor/UF/co-ocorrência são suficientes para v1)
- Embedding semantic similarity (defer; over-engineering pre-revenue)
- Anchor text personalizado por intent (defer; usar título da página alvo)
- Click tracking analytics em internal links (defer; GSC + Mixpanel `page_view` cobrem indireto)
- Hub `<RelatedSectors />` separado (out-of-scope; cobre apenas via 8 links pattern)

---

## Definition of Done

- [ ] Backend endpoint `/v1/seo/related` em prod, cached Redis, `_run_with_budget(2s)`
- [ ] `<RelatedPages />` integrado em 6 rotas SEO
- [ ] 8 links/page hard cap aplicado
- [ ] Lighthouse SEO score ≥ 0.95 em sample routes (validação SEO-PROG-010)
- [ ] Bundle delta < +2KB
- [ ] E2E suite 100% pass
- [ ] Acessibilidade audit: WAVE Browser Extension reporta 0 errors em sample routes
- [ ] CodeRabbit clean
- [ ] PR aprovado @qa + @ux-design-expert (Uma)
- [ ] Counter Prometheus ativo
- [ ] Memory atualizada: `project_internal_linking_pattern.md` (criar)
- [ ] Change Log atualizado

---

## Dev Notes

### Paths absolutos

- **Backend route:** `/mnt/d/pncp-poc/backend/routes/seo_related.py` (criar)
- **Backend service:** `/mnt/d/pncp-poc/backend/services/seo_related_service.py` (criar — queries de relevância)
- **Backend tests:** `/mnt/d/pncp-poc/backend/tests/routes/test_seo_related.py` (criar)
- **Component novo:** `/mnt/d/pncp-poc/frontend/app/components/seo/RelatedPages.tsx`
- **Utility novo:** `/mnt/d/pncp-poc/frontend/lib/seo-related.ts`
- **Tests:** `/mnt/d/pncp-poc/frontend/__tests__/components/RelatedPages.test.tsx`, `frontend/__tests__/lib/seo-related.test.ts`
- **E2E:** `/mnt/d/pncp-poc/frontend/e2e-tests/seo/related-pages.spec.ts`
- **Integração rotas:**
  - `/mnt/d/pncp-poc/frontend/app/cnpj/[cnpj]/page.tsx`
  - `/mnt/d/pncp-poc/frontend/app/orgaos/[slug]/page.tsx`
  - `/mnt/d/pncp-poc/frontend/app/itens/[catmat]/page.tsx`
  - `/mnt/d/pncp-poc/frontend/app/observatorio/[slug]/page.tsx`
  - `/mnt/d/pncp-poc/frontend/app/fornecedores/[cnpj]/[uf]/page.tsx`
  - `/mnt/d/pncp-poc/frontend/app/blog/licitacoes/[setor]/[uf]/page.tsx`

### Padrões existentes

- `ContentPageLayout` em `frontend/app/components/ContentPageLayout.tsx` — analizar antes de criar componente novo (reutilizar layout existente?)
- `getBackendUrl()` helper de SEO-PROG-008
- `_run_with_budget` pattern de RES-BE-002

### Backend queries de relevância (TODO @data-engineer detalhar)

Pseudocódigo para `/cnpj/{X}`:

```sql
-- Top fornecedores correlatos (mesmo setor + UF do CNPJ X)
SELECT cnpj, razao_social
FROM pncp_supplier_contracts
WHERE setor_detectado = (SELECT setor_detectado FROM ... WHERE cnpj = $1)
  AND uf = (SELECT uf FROM ... WHERE cnpj = $1)
  AND cnpj != $1
ORDER BY total_contratos_24m DESC
LIMIT 4;

-- Top órgãos compradores
SELECT orgao_cnpj, orgao_nome
FROM pncp_supplier_contracts
WHERE cnpj = $1
GROUP BY orgao_cnpj, orgao_nome
ORDER BY count(*) DESC
LIMIT 3;

-- Hub `/cnpj` (sempre incluir)
```

### UX consideration (Uma — @ux-design-expert)

- Posição: footer da página (após conteúdo principal) é padrão SEO. Sidebar é alternativa em layouts de blog.
- Heading: específico ao contexto (e.g., "Empresas similares" vs "Páginas relacionadas") melhora CTR.
- Mobile: 1col stack, desktop 2col grid.
- A/B test (defer): heading variants. Memory `feedback_n2_below_noise_eng_theater.md`: n<5 = engineering theater. Defer A/B até n≥30.

### Testing standards

- Mock `fetchRelatedPages` em tests unit dos pages.
- E2E: usar fixture top CNPJ + verify 8 `<a>` em `<nav>`.
- Backend test: cache hit verification via patch `redis_client.get`.

---

## Risk & Rollback

### Triggers

| Trigger | Threshold | Detecção |
|---|---|---|
| GSC clicks regression | -10% 7d em routes integradas | GSC API |
| Backend wedge `seo_related` | timeout >5/min | Prometheus |
| Bundle delta >+5KB | size-limit fail | CI |
| INP regression | >50ms incremento | Lighthouse |

### Ações

1. **Soft rollback:** prop `relatedPages` hardcoded mantida em `ContentPageLayout` como fallback — set env `SEO_RELATED_FETCH_DISABLED=true` para forçar fallback.
2. **Hard rollback:** revert PR via @devops.

---

## Dependencies

### Entrada

- SEO-PROG-001..005 (rotas estáveis ISR)
- RES-BE-002 (`_run_with_budget` pattern em backend)
- SEO-PROG-008 (`getBackendUrl()` helper)

### Saída

- SEO-PROG-012 (Schema.org expansion pode adicionar `SiteNavigationElement` se desejado — fora deste escopo)

### Paralelas

- SEO-PROG-009 (bundle reduction — coordenar para não estourar cap)

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 9/10

### 10-Point Checklist

| # | Criterion | Status | Notes |
|---|---|---|---|
| 1 | Clear and objective title | OK | Título preciso: cap 8 links + backend pré-computa |
| 2 | Complete description | OK | 4 problemas claros (hardcoded, cap baixo, sem matriz relevância, long-tail isolado) |
| 3 | Testable acceptance criteria | OK | AC1-AC8 testáveis; queries de relevância pseudo-codificadas |
| 4 | Well-defined scope (IN/OUT) | OK | OUT defer: ML, embedding, anchor personalizado, click tracking, RelatedSectors |
| 5 | Dependencies mapped | OK | 001-005 ISR + RES-BE-002 + SEO-PROG-008 (`getBackendUrl()`) |
| 6 | Complexity estimate | OK | Effort M apropriado: backend endpoint + service + frontend component + 6 rotas integration + tests |
| 7 | Business value | OK | Vincula a 2-3x CTR potential + ajudar long-tail a indexar |
| 8 | Risks documented | OK | 4 triggers; soft rollback via env var `SEO_RELATED_FETCH_DISABLED` |
| 9 | Criteria of Done | OK | 12 itens; WAVE Browser Extension acessibilidade audit |
| 10 | Alignment with PRD/Epic | OK | Backend pre-compute alinha com `_run_with_budget` pattern (RES-BE-002) |

### Observations

- AC2 `prefetch={false}` em `<Link>` é decisão crítica para rotas SEO crawler-heavy — previne saturação backend.
- AC1 backend queries marcadas TODO @data-engineer — pseudo-código provido, suficiente para Ready (data-engineer detalha durante implementação).
- AC8 backend tests incluem cache hit verification (Redis) — teste do Layer 2 cache pattern.
- Memory `feedback_n2_below_noise_eng_theater.md` reconhecida em UX consideration (defer A/B até n≥30) — alinhamento com baseline n=2.
- Cap 8 links hard (vs 4 hardcoded atual) está dentro de SEO best practice 5-10.
- Score 9 (não 10) por queries SQL ainda em pseudo-código (TODO @data-engineer); aceitável para Ready dado escopo de detalhamento durante implementação.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — internal linking automatizado backend pré-computado | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (9/10). Queries pseudo-codificadas; @data-engineer detalha durante dev. Status Draft→Ready. | @po (Pax) |
