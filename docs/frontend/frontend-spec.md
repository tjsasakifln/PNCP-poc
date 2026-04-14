# SmartLic Frontend Specification & Audit

## Overview

- **Framework**: Next.js 16 (App Router)
- **UI Runtime**: React 18.3.1
- **Language**: TypeScript 5.9.3 (⚠️ strict NÃO habilitado — 296 `any` types)
- **Styling**: Tailwind CSS 3.4.19 (50+ tokens; ~70% adoção)
- **Deployment target**: Railway (Dockerfile, service root `frontend/`)
- **Production URL**: https://smartlic.tech
- **Architectural Pattern**: App Router, RSC mix com ~88% "use client" (TD-FE-007)
- **Audit Date**: 2026-04-14 (workflow brownfield-discovery Phase 3)

---

## Tech Stack (Verified from `frontend/package.json`)

| Layer                | Technology           | Version     |
|----------------------|----------------------|-------------|
| Framework            | Next.js              | 16.1.6      |
| React                | React                | 18.3.1      |
| TypeScript           | TypeScript           | 5.9.3       |
| Styling              | Tailwind CSS         | 3.4.19      |
| UI Component Lib     | CVA-based Button + custom | -      |
| Animations           | Framer Motion        | 12.33.0     |
| Charts               | Recharts             | 3.7.0       |
| Drag-Drop            | @dnd-kit/core        | 6.3.1       |
| Drag-Drop Sortable   | @dnd-kit/sortable    | 10.0.0      |
| Onboarding Tours     | Shepherd.js          | 14.5.1      |
| Forms                | react-hook-form      | 7.71.2      |
| Validation           | Zod                  | 4.3.6       |
| Auth                 | @supabase/ssr        | 0.8.0       |
| Data Fetching        | SWR                  | 2.4.1       |
| Toasts               | Sonner               | 2.0.7       |
| Analytics            | mixpanel-browser     | 2.74.0      |
| Error Tracking       | @sentry/nextjs       | 10.38.0     |
| Analytics (GA)       | Google Analytics 4   | -           |
| Icons                | lucide-react         | 0.563.0     |
| Testing (unit)       | Jest + RTL           | -           |
| Testing (E2E)        | Playwright           | -           |

---

## Design System Reality

### Status: PARTIAL ADOPTION (~70%)

**Strengths:**
- ✅ 50+ design tokens definidos em `tailwind.config.ts` + CSS custom properties em `globals.css`
- ✅ Dark mode completo com contraste WCAG AA+
- ✅ Semantic colors (success/error/warning + subtle variants)

**Gaps:**
- ❌ Sem Storybook (sem component gallery/docs)
- ❌ Estrutura atômica não enforçada (flat `/components/`)
- ❌ 194 hex colors hardcoded bypassam sistema de tokens
- ❌ 62% dos botões usam `<button>` nativo em vez de `<Button>` CVA

### Color Palette (actual)

- **Brand**: Navy (#0a1e3f), Blue (#116dff), Blue-hover (#0d5ad4)
- **Semantic**: Success (#16a34a), Error (#dc2626), Warning (#ca8a04)
- **Surfaces**: 0-2 hierarchy + elevated (light/dark variants)
- **Charts**: 10-color palette para Recharts

### Typography

- Font family: system-ui fallback (sem custom font por perf)
- Font sizes: Tailwind scale (xs → 6xl)
- Font weights: 400, 500, 600, 700 (unique values: 4+)

### Spacing

- Base unit: 4px (Tailwind default)
- Unique padding values detected: ~19
- Unique margin values: ~15
- Consistency: MEDIUM (inline styles indicam drift)

### Breakpoints

Tailwind defaults: sm(640), md(768), lg(1024), xl(1280), 2xl(1536). Mobile-first **declarado mas desktop-first na prática** (algumas páginas).

---

## Component Inventory

### Totals

- **Pages** (`frontend/app/**/page.tsx`): 22 rotas principais + subrotas (blog, admin sub-pages)
- **Shared components** (`frontend/components/`): ~68 componentes
- **Feature components** (`frontend/app/**/components/`): ~170
- **Total components**: ~243

### Shared Components (`frontend/components/`)

Exemplos enumerados:

- `Button.tsx` (CVA-based, canonical)
- `Card.tsx`, `Modal.tsx`, `Tooltip.tsx`
- `Input.tsx`, `Select.tsx`, `Textarea.tsx`
- `Badge.tsx`, `Tabs.tsx`, `Accordion.tsx`
- `LoadingSpinner.tsx`, `Skeleton.tsx`
- `Navbar.tsx`, `Footer.tsx`, `SidebarMobile.tsx`
- `ErrorBoundary.tsx`, `ErrorBanner.tsx`

### Feature Components (`frontend/app/buscar/components/`)

**Search:**
- `SearchForm`, `SearchResults`, `FilterPanel`, `UfProgressGrid`
- `SearchHeader`, `SectorSelector`, `CustomKeywordsInput`

**Resilience:**
- `CacheBanner`, `DegradationBanner`, `PartialResultsPrompt`
- `SourcesUnavailable`, `ErrorDetail`, `RetryButton`

**AI:**
- `LlmSourceBadge`, `ViabilityBadge`, `FeedbackButtons`, `ReliabilityBadge`
- `ClassificationReasoning`, `ViabilityReasonsModal`

**Billing:**
- `PlanCard`, `PlanToggle`, `PaymentFailedBanner`, `CancelSubscriptionModal`
- `UpgradeButton`, `QuotaBanner`

**Loading:**
- `EnhancedLoadingProgress`, `LoadingProgress`, `SkeletonResults`

---

## Pattern Redundancy Metrics (Quantified)

Métricas levantadas via `Grep` sobre `frontend/**/*.tsx`:

| Pattern                                   | Count  | Status                                                      |
|-------------------------------------------|--------|-------------------------------------------------------------|
| `<button>` native + `<Button>` component  | 629    | 62% são `<button>` nativo (deveria ser `<Button>`)          |
| Inline hex colors `#[0-9a-fA-F]{6}`       | 194    | HIGH debt — bypassa Tailwind tokens                         |
| `rgb()` inline                            | 0      | ✅ GOOD                                                      |
| `style={{...}}` inline styles             | 139    | MEDIUM debt — deveria ser Tailwind classes                  |
| `: any` ou `as any`                       | 296    | 🔴 CRITICAL — type safety gap                                |
| `aria-label` ou `role=`                   | 874    | ✅ STRONG accessibility coverage                             |
| `data-testid`                             | 930    | ✅ EXCELLENT test instrumentation                            |
| `"use client"` directives                 | ~88%   | ⚠️ Over-client; underutiliza Server Components             |

---

## Route Inventory (22 páginas principais)

| Path                 | Purpose                              | Auth         | Notable Concerns                                         |
|----------------------|--------------------------------------|--------------|----------------------------------------------------------|
| `/`                  | Landing page                         | Public       | LCP crítico; marketing copy                              |
| `/login`             | Email/password login                 | Public       | Google OAuth social                                      |
| `/signup`            | Trial signup                         | Public       | Sem email verify obrigatório (debate)                    |
| `/auth/callback`     | OAuth callback                       | Public       | -                                                         |
| `/recuperar-senha`   | Password reset request               | Public       | -                                                         |
| `/redefinir-senha`   | Password reset confirm               | Public       | -                                                         |
| `/onboarding`        | 3-step wizard (CNAE → UFs → Confirm) | Auth         | Friction point (TD-UX-001)                              |
| `/buscar`            | Main search page                     | Auth         | SSE + polling, 20+ components, CRITICAL flow             |
| `/dashboard`         | User analytics                       | Auth         | Recharts heavy                                           |
| `/historico`         | Search history                       | Auth         | Pagination absent                                        |
| `/pipeline`          | Opportunity kanban                   | Auth         | ✅ keyboard nav WCAG 2.1 AA (STORY-1.5, EPIC-TD-2026Q2)  |
| `/mensagens`         | Support tickets                      | Auth         | -                                                         |
| `/conta`             | Account settings                     | Auth         | Password change + data export                            |
| `/planos`            | Pricing/upgrade                      | Auth         | Stripe checkout                                          |
| `/planos/obrigado`   | Thank-you post-checkout              | Auth         | -                                                         |
| `/pricing`           | Marketing pricing                    | Public       | -                                                         |
| `/features`          | Marketing features                   | Public       | -                                                         |
| `/ajuda`             | Help center                          | Public       | -                                                         |
| `/admin`             | Admin dashboard                      | Admin        | is_admin gated                                           |
| `/admin/cache`       | Cache admin                          | Admin        | -                                                         |
| `/termos`            | Terms of service                     | Public       | -                                                         |
| `/privacidade`       | Privacy policy                       | Public       | LGPD disclosures                                         |

Adicionalmente: `/blog/*`, `/admin/*` sub-routes (total ~92 segmentos de rota).

### Critical Pages (top 5 detailed)

1. **`/buscar`** — CRITICAL flow. Orquestra POST /buscar → SSE → polling → render. Estado complexo (filtros, loading, progress per UF, results, cache banner). ~20+ components.
2. **`/pipeline`** — Kanban drag-drop via @dnd-kit. Acessibilidade gap (sem keyboard nav).
3. **`/dashboard`** — Analytics charts (Recharts). Heavy bundle; initial render slow.
4. **`/onboarding`** — 3-step wizard. Drop-off point (TD-UX-001).
5. **`/conta`** — Subscription + password + data export. Stripe portal integration.

---

## State Management

### Architecture

Multi-layer provider hierarchy em `frontend/app/layout.tsx`:

```
<AuthProvider>                     # Session, user, admin status (Supabase SSR)
  <ThemeProvider>                  # Dark/light mode
    <AnalyticsProvider>            # Mixpanel, Sentry, GA4
      <NProgressProvider>          # Page transition bar
        <SWRProvider>              # SWR config
          <UserProvider>           # Profile, features, quota
            <BackendStatusProvider># Health check polling
              {children}
            </BackendStatusProvider>
          </UserProvider>
        </SWRProvider>
      </NProgressProvider>
    </AnalyticsProvider>
  </ThemeProvider>
</AuthProvider>
```

### Patterns

- `useState` (637 instances) para local component state
- `useCallback` para memoization de handlers
- Custom hooks: `useSearchOrchestration`, `usePipeline`, `usePlan`, `useShepherdTour`, `useQuota`, `useAuth`
- **SWR** para API calls + cache + auto-revalidation
- **localStorage** para theme, plan cache (1h TTL — CLAUDE.md), survey flags
- **URL query params** para search filter state

### Observations

- Sem Zustand/Redux/Jotai — Context + Hooks + SWR é suficiente para o scale atual
- Plan cache localStorage (1h TTL) previne UI downgrades em erro transitório (CLAUDE.md)

---

## API Integration

### API Proxy Pattern

`frontend/app/api/` route handlers proxam para backend FastAPI. Exemplos:

- `app/api/buscar/route.ts` → backend `POST /buscar`
- `app/api/buscar-progress/[id]/route.ts` → backend `GET /buscar-progress/{id}` (SSE)
- `app/api/analytics/route.ts` → backend `GET /analytics/*`
- `app/api/admin/route.ts` → backend `GET /admin/*` (admin-gated)
- `app/api/feedback/route.ts` → backend `POST /feedback`
- `app/api/trial-status/route.ts` → backend `GET /trial-status`
- `app/api/plans/route.ts` → backend `GET /plans`
- `app/api/pipeline/route.ts` → backend `POST/GET/PATCH/DELETE /pipeline`
- `app/api/sessions/route.ts` → backend `GET /sessions`
- `app/api/user/route.ts` → backend `GET /me`, `PUT /profile/context`

### Error Handling

- `ErrorBoundary` component (react-error-boundary)
- Sentry captures para errors não-handled
- Toast (Sonner) para user feedback
- Degradation banners para partial failures (SSE fallback, source unavailable)

---

## Accessibility Audit

**Level alcançado**: WCAG AA+ (muitos tokens meet AAA)

### Positives

- ✅ 874 ARIA labels/roles
- ✅ Skip to content link
- ✅ Semantic HTML (nav, main, article, form, section)
- ✅ Focus management (`focus-trap-react` em modals)
- ✅ Dark mode com accessible contrast

### Verified Contrast Ratios (from tokens)

- Primary text vs canvas: 12.6:1 AAA ✅
- Secondary text: 5.5:1 AA ✅
- Error/success/warning: Todos AA+ ✅

### Known Violations / Gaps

- ⚠️ **Kanban (@dnd-kit)** sem keyboard nav completa (arrow keys drag-drop) — WCAG 2.1 AA gap
- ⚠️ **Shepherd.js** hardcoded HTML — screen readers não parseiam corretamente
- ⚠️ Form validation errors sometimes not `aria-live`
- ⚠️ Charts (Recharts) sem long descriptions para screen readers

---

## Performance

### Bundle Analysis (heuristic, sem bundle-analyzer report atual)

**Heavy dependencies:**
- Framer Motion 12.33 — não tree-shakeable
- Recharts 3.7 — ~60KB gzipped
- Shepherd.js 14.5 — ~30KB
- @dnd-kit/core+sortable — ~40KB combined

**Code splitting**: Next.js automático per-route (good).

### Rendering

- **SSR vs CSR vs SSG**: mix via App Router
- **"use client"**: ~88% dos components (⚠️ TD-FE-007 — underutilize RSC)
- **Suspense boundaries**: inconsistentes (alguns lugares sim, outros não)

### Known Performance Issues

- `/dashboard` initial render slow (Recharts heavy)
- SSE + polling chain em `/buscar` pode ter race conditions se backend lento
- Mobile viewport: bottom nav not always sticky durante scroll

---

## Testing Reality

### Unit/Integration

- **Jest + RTL**: 135 test files, 2681+ passing, 0 failures
- **Coverage threshold**: 60%
- **jest.setup.js** polyfills: `crypto.randomUUID` + `EventSource` (jsdom lacks both)

### E2E

- **Playwright**: 60 tests em `frontend/e2e-tests/`
- Cobertura: golden path, error handling, acessibilidade básica
- CI: `.github/workflows/e2e.yml`

### Known Testing Gaps

- Sem visual regression (Percy/Chromatic/Loki)
- Sem perf budget tests (Lighthouse CI)
- Sem a11y automated (axe-core integration parcial)

---

## Internationalization (i18n)

- **NÃO implementado** (TD-FE-010)
- Strings hardcoded em Português (pt-BR)
- Default locale: pt-BR (SmartLic é produto brasileiro)
- **Impacto**: Expansão LATAM requer retrofit
- **Risk**: Strings scattered em 170+ feature components

---

## Technical Debt Register (23 items)

### CRITICAL 🔴 (3 items, ~7-11 dias)

#### TD-FE-001: 296 `any` types

- **Location**: espalhado em `frontend/` (296 matches `: any` ou `as any`)
- **Impact**: Type safety gap; refactoring confiante impossível; bugs runtime não pegos em compile time.
- **Fix**: Enable TypeScript strict mode + progressive typing.
- **Effort**: 3-5 dias

#### TD-FE-002: Shepherd.js hardcoded HTML

- **Impact**: Accessibility violation; screen readers não parseiam.
- **Fix**: Substituir por solução custom com ARIA correto ou shepherd-react com renderização React.
- **Effort**: 2-3 dias

#### TD-FE-003: 139 inline `style={{...}}`

- **Impact**: Design system bypass; CSS scattered; manutenibilidade.
- **Fix**: ESLint rule + progressive migration para Tailwind classes.
- **Effort**: 2-3 dias

### HIGH ⚠️ (5 items, ~8-15 dias)

#### TD-FE-004: 194 inline hex colors

- **Impact**: Breaks token system.
- **Fix**: ESLint `no-arbitrary-values` + token enforcement em code review.
- **Effort**: 1-2 dias

#### TD-FE-005: 62% `<button>` nativo (deveria ser `<Button>`)

- **Impact**: Design system coherence; ARIA labels nem sempre presentes; styling drift.
- **Fix**: Codemod + ESLint rule.
- **Effort**: 1 dia

#### TD-FE-006: Kanban (@dnd-kit) sem keyboard nav ✅ RESOLVIDO (STORY-1.5, 2026-04-14)

- **Impact**: WCAG 2.1 AA violation; keyboard users excluded.
- **Resolution**: `KeyboardSensor` + `sortableKeyboardCoordinates` ativos em `PipelineKanban.tsx`; `PipelineCard`/`PipelineColumn` com `focus-visible:ring-2 focus-visible:ring-brand-blue`; aria-live announcements em português via `accessibility.announcements`; novo spec `e2e-tests/pipeline-keyboard.spec.ts` com gate axe-core (0 critical).

#### TD-FE-007: ~88% "use client" directives

- **Impact**: Bundle size, hydration cost, underutiliza RSC.
- **Fix**: Audit + migrate static components para Server Components.
- **Effort**: 5-7 dias

#### TD-FE-008: Sem visual regression testing

- **Impact**: CSS changes podem silenciosamente quebrar UI.
- **Fix**: Percy/Chromatic/Loki integration.
- **Effort**: 1-2 dias

### MEDIUM 💡 (12 items, ~12-20 dias)

#### TD-FE-010: i18n não implementado

- Strings hardcoded pt-BR; expansão LATAM bloqueada.

#### TD-FE-011: Sem Storybook

- DX gap; component discovery difícil.

#### TD-FE-012: Framer Motion/dnd-kit não tree-shaken

- Bundle weight ~100KB+ combined.

#### TD-FE-013: SSE reconnection não surface para user

- Se conexão cai, UI não sempre sinaliza.

#### TD-FE-014: Image optimization incompleta

- `<Image>` Next nem sempre usado; WebP conversion manual.

#### TD-FE-015: Loading state inconsistency

- Skeleton vs spinner mix.

#### TD-FE-016: Error messages genéricos

- "Erro inesperado" unhelpful.

#### TD-FE-017: Tour Shepherd.js não dismissível persistente

- Repete em cada visita.

#### TD-FE-018: Bottom nav mobile não sticky

- Navegação inacessível durante scroll.

#### TD-FE-019: Cache freshness unclear para user

- Usuários incertos se dados são recentes.

#### TD-FE-020: Form validation errors easy to miss

- Visual weak; ARIA live regions faltam.

#### TD-FE-021: Blog content não responsivo

- Images overflow em mobile.

### LOW (3 items, 2-4 dias)

#### TD-FE-030: Toast positioning em mobile sub-ótimo

#### TD-FE-031: Missing JSDoc em components core

#### TD-FE-032: `Button.examples.tsx` órfão (não em Storybook)

---

## UX Concerns (User-Facing)

### High Impact

1. **Onboarding friction** — 3-step wizard sente longo, causa drop-off
2. **Empty state confusing** — "No results found" sem sugestões de fix
3. **Pipeline accessibility** — Keyboard users não conseguem drag-drop
4. **Trial expiry não surfaced** — Sem countdown; usuários surpresos
5. **Error messages genéricos** — "Erro inesperado" unhelpful
6. **Bottom nav não sticky mobile** — Navegação perdida durante scroll
7. **Tour can't be dismissed permanently** — Irritação
8. **Cache freshness unclear** — Usuários incertos se dados recentes
9. **Loading states inconsistent** — Skeleton vs spinner drift
10. **Form validation não óbvia** — Erros fáceis de perder
11. **Pipeline card modal focus issues** — Focus management
12. **Blog content not responsive** — Mobile overflow

---

## Questions for @architect (Phase 4 Handoff)

1. **Server Components strategy** — atualmente 88% client-side. Migration plan?
2. **TypeScript strict mode** — quando habilitar? Bloqueador para 296 `any` types?
3. **Design token enforcement** — ESLint (`no-arbitrary-values`) ou code review?
4. **i18n roadmap** — retrofit agora ou deferir? LATAM roadmap?
5. **Storybook** — implementar quando?
6. **`<Button>` migration** — 62% ainda `<button>` nativo. Codemod aprovado?
7. **Kanban keyboard nav** — prioritize WCAG 2.1 AA compliance?
8. **Performance budget targets** — LCP/FID/CLS?
9. **Mobile-first vs desktop-first** — oficial stance?
10. **Visual regression tool choice** — Percy, Chromatic, Loki?

---

## Recommendations Summary — Top 5 ROI

1. **Eliminate 296 `any` types** (3-5 dias) — TypeScript strict mode; catches bugs compile-time
2. **`<button>` → `<Button>` migration** (1 dia) — codemod; design system coerência
3. **ESLint `no-arbitrary-values`** (2 dias) — bloqueia inline hex; força token usage
4. **Kanban keyboard nav** (1-2 dias) — WCAG 2.1 AA compliance
5. **Visual regression (Percy)** (1-2 dias) — catch CSS regressions automaticamente

---

## Summary Statistics

| Metric                    | Value                | Status          |
|---------------------------|----------------------|-----------------|
| Components Counted        | ~243                 | ✅              |
| Routes Inventoried        | 22 principais + subs | ✅              |
| Design Tokens             | 50+                  | ✅ Comprehensive |
| Unit+Integration Tests    | 135 files, 2681+     | ✅ Good coverage |
| E2E Tests                 | 60 Playwright        | ✅              |
| ARIA Coverage             | 874 labels/roles     | ✅ Strong       |
| `any` Type Instances      | 296                  | 🔴 CRITICAL     |
| Design Token Adoption     | ~70%                 | ⚠️ MEDIUM       |
| `<Button>` Consistency    | 38% (62% raw)        | ⚠️ HIGH         |
| Technical Debt Items      | 23 (3c, 5h, 12m, 3l) | ⚠️ Manageable   |
| UX Concerns               | 12 high-impact       | ⚠️ Phase 5+     |

---

**Document Status**: 2.0 (2026-04-14) — Phase 3 of brownfield-discovery complete. Handoff ao @architect para Phase 4 (consolidação inicial).
