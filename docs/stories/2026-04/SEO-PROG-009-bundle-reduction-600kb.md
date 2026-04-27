# SEO-PROG-009: Bundle reduction -600KB (1.75MB → 1.15MB) — continuação STORY-5.14

**Priority:** P1
**Effort:** L (5-7 dias)
**Squad:** @dev + @ux-design-expert
**Status:** Ready
**Epic:** [EPIC-SEO-PROG-2026-Q2](EPIC-SEO-PROG-2026-Q2.md)
**Sprint:** Sprint 4-5 (20/mai–02/jun)
**Sprint Window:** 2026-05-20 → 2026-06-02
**Bloqueado por:** — (independente; ideal após SEO-PROG-001..005 estabilizarem rotas)

---

## Contexto

O bundle gzipped atual do SmartLic frontend é **1.75 MB** (`.size-limit.js` cap atual, baseline real 1.64MB pós STORY-5.14 baseline). Memory `project_bundle_size_budget.md` (2026-04-19) documentou recalibração de cap 250KB → 1.75MB com **alvo de redução -600KB em 90 dias** via STORY-5.14.

**Esta story é continuação direta de STORY-5.14**, executando o plano de redução para atingir **First Load JS ≤ 1.15MB gzipped** (target). 600KB de redução = ~34% do bundle atual.

**Justificativa SEO (por que P1):**

- LCP <2.5s exige First Load JS comprimido (HTTP/2 Server Push ou similar não é universal).
- Memory `reference_smartlic_baseline_2026_04_24`: GSC posição média 7.1 — Core Web Vitals score baixo é hipótese forte para por que SmartLic não rankeia top-3.
- `nextjs.org/learn/seo/web-performance` documenta correlação direta LCP↓ → ranking↑ em queries comerciais B2G.
- Rotas SEO migradas para ISR (SEO-PROG-001..005) servem HTML rápido, mas First Load JS bloqueia hydration → INP/TBT degradados.

**Componentes pesados conhecidos** (estimativas pós-audit STORY-5.14):

| Lib | Peso (~gzip) | Status |
|---|---|---|
| Framer Motion | ~70KB | Usado em landing animations + pipeline kanban; substituível por CSS em landing |
| Recharts | ~110KB | Usado em dashboard + observatorio + cnpj/orgaos analytics |
| dnd-kit | ~60KB | Apenas pipeline kanban; lazy-loadable |
| Shepherd.js | ~30KB | Apenas onboarding; lazy-loadable |
| @sentry/nextjs | ~80KB | Server + client; otimizar via tree-shake config |
| Stripe Elements | ~50KB | Apenas /planos + checkout; lazy-loadable |
| Supabase JS SSR | ~120KB | Universal; difícil cortar |

**Por que esforço L:** múltiplas frentes (route-level code-split, lazy imports, tree-shake configs, Framer→CSS migration). Cada técnica isolada é S; a soma é L. Risco: regressões funcionais em rotas autenticadas (kanban drag, onboarding tour).

---

## Acceptance Criteria

### AC1: Code-split rotas autenticadas via `dynamic()`

**Given** rotas autenticadas (`/dashboard`, `/pipeline`, `/historico`, `/admin`) carregam libs pesadas (Recharts, dnd-kit) no First Load JS
**When** @dev migra para `dynamic()` imports
**Then**:

- [ ] Componentes pesados em rotas autenticadas usam `next/dynamic` com `ssr: false`:

```tsx
import dynamic from 'next/dynamic';

const PipelineKanban = dynamic(() => import('./PipelineKanban'), {
  ssr: false,
  loading: () => <PipelineKanbanSkeleton />,
});

const DashboardCharts = dynamic(() => import('./DashboardCharts'), {
  ssr: false,
  loading: () => <ChartsSkeleton />,
});
```

- [ ] Rotas alvo: `/pipeline` (dnd-kit), `/dashboard` (Recharts), `/admin` (Recharts), `/historico` (Recharts), `/observatorio/[slug]` (Recharts — verificar se SEO-relevante; pode ser SSR só com dados estáticos sem Recharts no client)
- [ ] Skeleton components usam apenas Tailwind CSS (zero JS bloat)

### AC2: Tree-shake Recharts (custom subset)

**Given** Recharts ~110KB gzipped inclui chart types não usados (RadarChart, FunnelChart, etc.)
**When** @dev cria custom build minimal
**Then**:

- [ ] Importar apenas chart types em uso:

```ts
// ❌ Antes
import { LineChart, BarChart, AreaChart, PieChart, RadarChart, FunnelChart } from 'recharts';

// ✅ Depois — somente o que é usado
import { LineChart } from 'recharts/es6/chart/LineChart';
import { BarChart } from 'recharts/es6/chart/BarChart';
import { Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts/es6';
```

- [ ] Audit usos via grep `import.*from ['"]recharts['"]` em `frontend/app/ frontend/components/`
- [ ] Configurar webpack/SWC para Recharts side-effects: `false` em `package.json` ou `next.config.mjs`
- [ ] Estimativa de redução: 30-40KB

### AC3: Framer Motion → CSS animations em landing

**Given** landing pages (`/`, `/features`, `/planos`, `/sobre`, etc.) usam Framer Motion para animations simples (fade-in, slide-up, viewport reveal)
**When** @dev migra
**Then**:

- [ ] Animations simples (sem gestos, sem layout animations) migram para Tailwind CSS classes ou `@keyframes` CSS
- [ ] Audit usages: `grep -rn "from 'framer-motion'" frontend/app/`
- [ ] Páginas alvo (mínimo): `/`, `/features`, `/planos`, `/sobre`
- [ ] Manter Framer Motion em rotas autenticadas (pipeline, dashboard) onde gestos/layout animations são necessários
- [ ] Estimativa de redução: ~50KB (se Framer só ficar em autenticadas, pode dynamic-import lá também, +20KB)
- [ ] Zero regressões visuais (validar via Playwright screenshot diffs)

### AC4: Lazy-load Shepherd.js (onboarding only)

**Given** Shepherd.js ~30KB carregado universalmente
**When** @dev lazy-loada
**Then**:

- [ ] `OnboardingTour` componente usa `dynamic(() => import('shepherd.js'), { ssr: false })`
- [ ] Tour só carrega quando user dispara (e.g., click no botão "Tour" ou primeiro login flag)
- [ ] Rota `/onboarding` mantém eager-load (já é entry point de onboarding)
- [ ] Estimativa: ~30KB redução

### AC5: Lazy-load Stripe Elements (checkout only)

**Given** Stripe.js + Elements ~50KB carregados via `_app` ou layout
**When** @dev lazy-loada
**Then**:

- [ ] Stripe SDK só carrega em `/planos`, `/planos/obrigado`, `/checkout` (já é route-level — verificar bundle splits)
- [ ] Componente `StripeCheckoutButton` usa `dynamic()` com `ssr: false`
- [ ] Verify: rotas SEO públicas (cnpj, orgaos, blog) não importam Stripe no First Load JS

### AC6: Sentry tree-shake config

**Given** `@sentry/nextjs` ~80KB pode ser otimizado via integrations seletivas
**When** @dev configura
**Then**:

- [ ] `sentry.client.config.ts`: incluir apenas integrations necessárias:

```ts
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  integrations: [
    // Manter apenas o essencial
    Sentry.browserTracingIntegration(),
    // Sentry.replayIntegration() — REMOVER se não usado (replay é ~30KB)
  ],
  tracesSampleRate: 0.1,
  // ...
});
```

- [ ] Audit `Sentry.replayIntegration()`, `Sentry.feedbackIntegration()` — remover se não em uso
- [ ] Verify via DevTools Network Panel que `@sentry-internal/replay-canvas` não é loaded no client (se replay removido)
- [ ] Estimativa: ~30KB redução

### AC7: Atualizar `.size-limit.js` com novo cap

**Given** target -600KB atingível
**When** PR está pronto para merge
**Then**:

- [ ] `frontend/.size-limit.js` cap atualizado de `'1.75 MB'` para `'1.15 MB'`:

```js
module.exports = [
  {
    name: 'First Load JS (total)',
    path: '.next/static/chunks/**/*.js',
    gzip: true,
    limit: '1.15 MB', // SEO-PROG-009: -600KB target atingido (era 1.75MB hold-the-line)
  },
];
```

- [ ] Comentário inline atualizado citando SEO-PROG-009 + memory `project_bundle_size_budget.md`
- [ ] CI workflow `frontend-tests.yml` step "Check bundle size budget" valida cap 1.15MB

### AC8: Bundle analyzer CI artifact

**Given** queremos visibility contínua sobre bundle composition
**When** PR run
**Then**:

- [ ] CI step gera bundle analyzer report:

```yaml
- name: Bundle analyzer
  run: |
    cd frontend
    ANALYZE=true npm run build
- name: Upload bundle analyzer artifact
  uses: actions/upload-artifact@v4
  with:
    name: bundle-analyzer-report
    path: frontend/.next/analyze/
```

- [ ] Configurar `next.config.mjs` com `@next/bundle-analyzer`:

```js
import withBundleAnalyzer from '@next/bundle-analyzer';

const bundleAnalyzer = withBundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
});

export default bundleAnalyzer(nextConfig);
```

- [ ] Artifact retém últimos 30 dias para diff comparison

### AC9: Zero regressões funcionais

**Given** lazy-loading muda timing de hydration
**When** @dev valida
**Then**:

- [ ] **E2E Playwright suite** roda 100% pass: `frontend/e2e-tests/` (60 critical user flows)
- [ ] **Visual regression** (opcional, defer se não tiver infra): screenshot diff em landing pages via Playwright
- [ ] Manual smoke: pipeline kanban drag-and-drop funciona após dynamic load
- [ ] Manual smoke: onboarding Shepherd tour completa fluxo
- [ ] Manual smoke: Stripe checkout abre em `/planos`

---

## Scope

**IN:**
- Code-split rotas autenticadas (pipeline, dashboard, admin, historico) via `dynamic()`
- Tree-shake Recharts custom imports
- Framer Motion → CSS em landing pages (mínimo: `/`, `/features`, `/planos`, `/sobre`)
- Lazy-load Shepherd.js (onboarding)
- Lazy-load Stripe Elements (checkout)
- Sentry integrations audit + tree-shake
- `.size-limit.js` cap update para 1.15MB
- Bundle analyzer CI artifact
- E2E suite full pass + manual smoke

**OUT:**
- Migração Recharts → alternative chart lib (out-of-scope; tree-shake é suficiente)
- Server-side rendering optimizations (escopo de SEO-PROG-001..005)
- Edge runtime migration (out-of-scope epic level)
- Image optimization (next/image já usado; defer se baseline OK)
- Font optimization (subset, preload) — out-of-scope; criar follow-up se font ainda problema

---

## Definition of Done

- [ ] First Load JS gzipped ≤ 1.15MB (validado por `.size-limit.js` em CI)
- [ ] Bundle analyzer report mostra dependências pesadas em chunks separados (não em main bundle)
- [ ] E2E suite 100% pass (60 critical flows)
- [ ] Manual smoke: pipeline drag, onboarding tour, Stripe checkout funcionam
- [ ] Lighthouse CI top-3 SEO routes: LCP<2.5s, INP<200ms (validação plena em SEO-PROG-010)
- [ ] Bundle analyzer CI artifact uploaded
- [ ] Zero regressões visuais detectadas (Playwright screenshot diff opcional)
- [ ] CodeRabbit clean
- [ ] PR aprovado @qa + @ux-design-expert (Uma) + @dev
- [ ] Change Log atualizado
- [ ] Memory `project_bundle_size_budget.md` atualizada para nova baseline

---

## Dev Notes

### Paths absolutos

- **Size limit config:** `/mnt/d/pncp-poc/frontend/.size-limit.js`
- **Next config:** `/mnt/d/pncp-poc/frontend/next.config.mjs`
- **Sentry config:** `/mnt/d/pncp-poc/frontend/sentry.client.config.ts`, `sentry.server.config.ts`, `sentry.edge.config.ts`
- **CI workflow:** `/mnt/d/pncp-poc/.github/workflows/frontend-tests.yml`
- **Pipeline kanban:** `/mnt/d/pncp-poc/frontend/app/pipeline/components/`
- **Dashboard charts:** `/mnt/d/pncp-poc/frontend/app/dashboard/components/`
- **Onboarding:** `/mnt/d/pncp-poc/frontend/app/onboarding/`
- **Stripe checkout:** `/mnt/d/pncp-poc/frontend/app/planos/`
- **E2E tests:** `/mnt/d/pncp-poc/frontend/e2e-tests/`

### Memory + reference

- `project_bundle_size_budget.md` — baseline 1.64MB gzipped (Wave #386), cap 1.75MB hold-the-line, alvo -600KB em 90d via STORY-5.14
- `feedback_wsl_next16_build_inviavel.md` — bundle analyzer pode falhar OOM local; rodar em CI

### Padrões existentes

- `dynamic()` já usado em ~5 rotas (audit antes de assumir greenfield)
- `@sentry/nextjs` config já tree-shakable via `withSentryConfig` em `next.config.mjs`

### Testing standards

- E2E Playwright headed mode para validar lazy-loaded components (`npm run test:e2e:headed`)
- Lighthouse CI rodado manualmente em staging via `npx @lhci/cli autorun --collect.url=https://staging.smartlic.tech/`
- Memory `feedback_jwt_base64url_flaky_test.md` (não aplica direto, mas princípio: testes funcionais > screenshot pixel diff em casos de flakiness)

### Risk: regressões em routes autenticadas

- Pipeline kanban com `ssr: false` + dnd-kit dynamic = atraso ~200-500ms em primeira interação. UX-design-expert (Uma) deve validar skeleton state UX.
- Onboarding tour: se Shepherd.js demora a carregar, usuário pode ter clicado fora antes do tour iniciar. Mitigação: pré-loadar via `<link rel="preload">` ou `useEffect`.

---

## Risk & Rollback

### Triggers

| Trigger | Threshold | Detecção |
|---|---|---|
| E2E suite regressões | >0 fails | CI |
| Bundle size cap fail | >1.15MB | CI |
| Pipeline kanban drag broken | manual smoke fail | QA |
| Lighthouse INP regressão | >200ms top-3 routes | Lighthouse CI |

### Ações

1. **Soft:** revert technique específica (e.g., undo Framer→CSS em landing se regressão visual). Story aceita parcial: 400KB redução ainda é vitória.
2. **Hard:** revert PR via @devops + manter cap 1.75MB.

---

## Dependencies

### Entrada

- Nenhuma hard. Ideal após SEO-PROG-001..005 estabilizarem (ISR funcionando) para Lighthouse baseline limpo.

### Saída

- SEO-PROG-010 (Lighthouse CI assume bundle ≤1.15MB)

### Paralelas

- SEO-PROG-011 (RelatedPages — componente novo deve respeitar bundle budget)

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO (conditional — observação sobre matemática do target)
**Score:** 8/10

### 10-Point Checklist

| # | Criterion | Status | Notes |
|---|---|---|---|
| 1 | Clear and objective title | OK | Título preciso: -600KB target + continuação STORY-5.14 |
| 2 | Complete description | OK | Tabela de componentes pesados com estimativas (Framer 70KB, Recharts 110KB, dnd-kit 60KB, etc.) |
| 3 | Testable acceptance criteria | PARTIAL | AC1-AC9 testáveis; AC7 cap update enforced via CI; AC9 zero regressões via E2E. **Math do target merece scrutiny** (ver Observations) |
| 4 | Well-defined scope (IN/OUT) | OK | OUT exclui: chart lib migration, edge runtime, image opt, font opt |
| 5 | Dependencies mapped | OK | Soft dependency em SEO-PROG-001..005 (baseline limpo); Saída: SEO-PROG-010 |
| 6 | Complexity estimate | OK | Effort L (5-7 dias) apropriado: múltiplas frentes (route-level split, lazy imports, tree-shake, Framer→CSS) |
| 7 | Business value | OK | Vincula a LCP/INP ranking factor + hipótese forte para position 7.1 baseline |
| 8 | Risks documented | OK | 4 triggers; soft rollback aceita parcial (400KB ainda é vitória) |
| 9 | Criteria of Done | OK | 11 itens; bundle analyzer artifact + memory update |
| 10 | Alignment with PRD/Epic | OK | Continuação direta STORY-5.14 (memory `project_bundle_size_budget.md`) |

### Observations (não bloqueantes)

- **Soma de savings explícitos em ACs ≈ 190-260KB direto** (Recharts ~30-40 + Framer ~50 + Shepherd ~30 + Sentry ~30 + Stripe lazy). Restante ~340-410KB precisa vir de `dynamic()` route-splits — mas **dynamic imports movem bundles, não reduzem o agregado** medido por `.size-limit.js` (mede `.next/static/chunks/**/*.js` gzipped agregado). Importante: First Load JS de uma rota PODE diminuir, mas size-limit metric agregado não. Ver AC7 que assume cap update funciona; pode precisar revisitar metric ou aceitar partial.
- **Drift entre `.size-limit.js` comment ("≤ 600 KB em 90 dias" — absoluto) e story 009 ("≤ 1.15MB" — diff de 600KB)** — story 009 deve win pois é mais conservativo e empírico (1.75 - 0.6 = 1.15). Dev deve corrigir o comentário em `.size-limit.js` durante implementação para alinhar com 1.15MB target.
- **Soft rollback "400KB ainda é vitória"** auto-mitiga risco de math discrepancy.
- AC8 bundle analyzer CI artifact é defesa para visibility contínua — excelente.
- AC9 pipeline kanban + Shepherd tour smoke previne regressão funcional em rotas autenticadas.

### Required Fixes

Nenhum bloqueante — observações são para @dev considerar durante implementação:
1. Decidir se metric é "First Load JS por rota" (rota-específico) ou "agregate chunks" (size-limit atual). Se segundo, target -600KB pode ser ambicioso demais sem deletar deps.
2. Atualizar comentário `.size-limit.js` linha "STORY-5.14: First Load JS para ≤ 600 KB" para refletir cap 1.15MB target da SEO-PROG-009.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — continuação STORY-5.14 (alvo -600KB) | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO conditional (8/10). Math do target merece scrutiny: dynamic imports movem bundles, não reduzem agregate; soft rollback auto-mitiga. Drift no `.size-limit.js` comment a corrigir. Status Draft→Ready. | @po (Pax) |
