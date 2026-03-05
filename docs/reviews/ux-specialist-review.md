# UX Specialist Review

**Reviewer:** @ux-design-expert (Pixel)
**Date:** 2026-03-04
**Documents Reviewed:** technical-debt-DRAFT.md v2.0, frontend-spec.md (Phase 3)
**Supersedes:** ux-specialist-review.md v1 (2026-02-25)

---

## Review Summary

The DRAFT v2.0 accurately captures the vast majority of frontend/UX debts. Line counts and prop counts were validated against the codebase and are correct (SearchResults.tsx = 1,581 lines, ~55 top-level props; conta/page.tsx = 1,420 lines; useSearch.ts = 1,510 lines; buscar/page.tsx = 1,019 lines). The Sidebar SVG inline claim is confirmed (75 lines of SVG definitions in an `icons` object, no `aria-hidden` on any of them, though the nav and collapse button do have `aria-label`).

**Key correction:** FE-18 (Blog/SEO pages are CSR) is **no longer accurate**. All blog pages (`/blog/*`, `/blog/programmatic/*`, `/blog/panorama/*`, `/blog/licitacoes/*`) and content pages (`/como-*`, `/licitacoes/*`) are already Server Components -- none have `"use client"`. The only CSR concern remaining is pages like `/planos` and `/features` which could benefit from SSG but are not SEO-critical programmatic pages. This significantly reduces the FE-18 severity.

The design system gap (FE-27-32) is the most impactful cluster from a UX perspective. Inconsistent buttons, inputs, and cards create a "patchwork" visual impression that undermines trust -- particularly for B2G enterprise buyers who equate visual consistency with system reliability.

---

## Debitos Validados

### 3.1 Arquitetura de Componentes

| ID | Debito | Sev. Original | Sev. Ajustada | Horas | Prioridade | Impacto UX |
|----|--------|---------------|---------------|-------|------------|------------|
| FE-01 | Mega-componente SearchResults.tsx (1,581 linhas, ~55 props) | HIGH | **HIGH** | 14-18h | Tier 1 | **High** -- any bug fix in search results requires understanding 1,500+ lines |
| FE-02 | Mega-componente conta/page.tsx (1,420 linhas) | HIGH | **MEDIUM** | 8-12h | Tier 1 | **Medium** -- account page is low-traffic, but MFA/password changes need isolation for security audit |
| FE-03 | Mega-hook useSearch.ts (1,510 linhas) | HIGH | **HIGH** | 14-18h | Tier 1 | **High** -- core search logic; any regression here breaks the primary user flow |
| FE-04 | buscar/page.tsx (1,019 linhas) | MEDIUM | **MEDIUM** | 6-8h | Tier 2 | **Medium** -- page orchestration is complex but functionally stable |
| FE-05 | 3 diretorios de componentes sem convencao | MEDIUM | **MEDIUM** | 4-6h | Tier 2 | **Low** -- invisible to users but slows dev velocity |
| FE-06 | Sem Button component compartilhado | MEDIUM | **HIGH** | 6-8h | Tier 1 | **High** -- visual inconsistency directly visible to users |
| FE-07 | SVGs inline no Sidebar (75 linhas) | LOW | **LOW** | 2h | Tier 3 | **Low** -- functional, just uses Heroicons SVGs instead of lucide-react |

### 3.2 State Management

| ID | Debito | Sev. Original | Sev. Ajustada | Horas | Prioridade | Impacto UX |
|----|--------|---------------|---------------|-------|------------|------------|
| FE-08 | Sem data fetching library | HIGH | **HIGH** | 16-20h | Tier 1 | **High** -- no dedup, no cache, no revalidation = stale data shown to users |
| FE-09 | 13+ localStorage keys sem abstracao | MEDIUM | **LOW** | 4-6h | Tier 3 | **Low** -- invisible to users unless storage quota exceeded |
| FE-10 | Prop drilling SearchResults (55 props) | HIGH | **HIGH** | 6-8h | Tier 1 | **High** -- coupled to FE-01 decomposition; must resolve together |
| FE-11 | Ref-based circular dependency workaround | MEDIUM | **LOW** | 2-3h | Tier 3 | **Low** -- code smell but functionally works |

### 3.3 Acessibilidade

| ID | Debito | Sev. Original | Sev. Ajustada | Horas | Prioridade | Impacto UX |
|----|--------|---------------|---------------|-------|------------|------------|
| FE-12 | Missing aria-labels em botoes icon-only | HIGH | **HIGH** | 1.5h | Tier 0 | **Critical** -- screen readers cannot navigate sidebar |
| FE-13 | SVG icons sem aria-hidden (Sidebar) | MEDIUM | **MEDIUM** | 0.5h | Tier 0 | **Medium** -- screen readers announce meaningless SVG paths |
| FE-14 | Viability scores usam cor sem alternativa textual | MEDIUM | **MEDIUM** | 2h | Tier 1 | **Medium** -- WCAG 1.4.1 violation |
| FE-15 | Inputs com placeholder em vez de label | MEDIUM | **MEDIUM** | 2h | Tier 1 | **Medium** -- WCAG 1.3.1; affects form comprehension |
| FE-16 | Sem hierarquia de headings auditada | LOW | **LOW** | 2h | Tier 3 | **Low** -- SEO impact minimal for authenticated pages |
| FE-17 | Sem ARIA live regions para progresso de busca | MEDIUM | **MEDIUM** | 2h | Tier 2 | **Medium** -- search progress invisible to screen readers |

### 3.4 Performance

| ID | Debito | Sev. Original | Sev. Ajustada | Horas | Prioridade | Impacto UX |
|----|--------|---------------|---------------|-------|------------|------------|
| FE-18 | Blog/SEO pages sao CSR | HIGH | **REMOVED** | 0h | N/A | **N/A** -- Verified: all blog/SEO pages are already Server Components (no `"use client"` found in `/blog/*`, `/licitacoes/*`, `/como-*`). Only `/planos` and `/features` are CSR, which is acceptable since they require client interactivity (Stripe, animations). |
| FE-19 | Sem dynamic imports para Recharts, Shepherd, dnd-kit | MEDIUM | **MEDIUM** | 3-4h | Tier 2 | **Medium** -- affects initial load time on slow connections |
| FE-20 | useIsMobile() hydration mismatch risk | LOW | **LOW** | 1h | Tier 3 | **Low** -- edge case, rarely visible |
| FE-21 | Sem Lighthouse CI gated | MEDIUM | **MEDIUM** | 3h | Tier 2 | **Medium** -- performance regressions ship undetected |

### 3.5 Qualidade de Codigo

| ID | Debito | Sev. Original | Sev. Ajustada | Horas | Prioridade | Impacto UX |
|----|--------|---------------|---------------|-------|------------|------------|
| FE-22 | Hardcoded Portuguese strings (44 paginas) | HIGH | **LOW** | 24-40h | Tier 3 | **Low** -- product is 100% BR, pre-revenue, no international plans. i18n is premature optimization. |
| FE-23 | eslint-disable react-hooks/exhaustive-deps | MEDIUM | **LOW** | 1h | Tier 3 | **Low** -- known exceptions, unlikely to cause bugs |
| FE-24 | APP_NAME redeclarado em 5+ arquivos | LOW | **LOW** | 0.5h | Tier 3 | **Low** -- trivial |
| FE-25 | Import patterns mistos para constantes | LOW | **LOW** | 1h | Tier 3 | **Low** -- dev convenience only |
| FE-26 | Sem TypeScript paths | LOW | **LOW** | 1h | Tier 3 | **Low** -- dev convenience only |

### 3.6 Design System Ausente

| ID | Debito | Sev. Original | Sev. Ajustada | Horas | Prioridade | Impacto UX |
|----|--------|---------------|---------------|-------|------------|------------|
| FE-27 | Sem Button component compartilhado | (from FE-06) | **HIGH** | 4-6h | Tier 1 | **High** -- most visible inconsistency |
| FE-28 | Sem Input component compartilhado | - | **MEDIUM** | 3-4h | Tier 2 | **Medium** -- forms feel different across pages |
| FE-29 | Sem Card component compartilhado | - | **MEDIUM** | 2-3h | Tier 2 | **Medium** -- visual rhythm varies |
| FE-30 | Sem Badge component compartilhado | - | **MEDIUM** | 2-3h | Tier 2 | **Low** -- many badge variants are intentionally different |
| FE-31 | Sem Storybook / documentacao visual | - | **LOW** | 8-12h | Tier 3 | **Low** -- useful for team scaling, not user-facing |
| FE-32 | Design tokens parcialmente adotados | - | **MEDIUM** | 3-4h | Tier 2 | **Medium** -- mix of `var()`, Tailwind tokens, and raw hex undermines consistency |

### 3.7 UX Inconsistencies

| ID | Debito | Sev. Original | Sev. Ajustada | Horas | Prioridade | Impacto UX |
|----|--------|---------------|---------------|-------|------------|------------|
| FE-33 | Search page header vs NavigationShell | MEDIUM | **MEDIUM** | 4-6h | Tier 2 | **Medium** -- user sees two different navigation paradigms |
| FE-34 | 2 padroes empty state | LOW | **LOW** | 1h | Tier 3 | **Low** |
| FE-35 | Toast vs inline banners sem criterio | LOW | **LOW** | 2h | Tier 3 | **Low** -- sonner toasts are more consistent than DRAFT implies |
| FE-36 | Loading spinner size/style varia | LOW | **LOW** | 1h | Tier 3 | **Low** |
| FE-37 | Date formatting inconsistente | LOW | **LOW** | 2h | Tier 3 | **Low** -- all show correct dates, just different APIs |
| FE-38 | Currency formatting inconsistente | LOW | **LOW** | 1h | Tier 3 | **Low** -- formatCurrencyBR covers most cases |

---

## Debitos Adicionados

| ID | Debito | Severidade | Horas | Impacto UX |
|----|--------|-----------|-------|------------|
| FE-39 | **Dashboard charts no mobile** -- Recharts Bar/Line/Pie have no mobile-specific layout (overflow, truncated labels, touch targets). Mentioned in frontend-spec.md responsive gaps but not in DRAFT. | MEDIUM | 4-6h | **Medium** -- dashboard is second most-visited page after search |
| FE-40 | **Missing `next/dynamic` usage** -- Only `TotpVerificationScreen` and `BlogListClient` use dynamic imports across the entire app. Shepherd.js tour initialization on every search page load is unnecessary for returning users. | MEDIUM | 2h | **Medium** -- unnecessary JS parse time |
| FE-41 | **No hook isolation tests** -- 19 custom hooks tested only indirectly through component tests. `useSearch` (1,510 lines) has zero isolated unit tests. Regression risk during decomposition. | MEDIUM | 8-12h | **Medium** -- indirect: decomposition of FE-03 without hook tests is high-risk |
| FE-42 | **Alert creation form not mobile-optimized** -- Mentioned in frontend-spec responsive gaps (Section 7.6) but absent from DRAFT. Feature-gated behind SHIP flag, but will need fixing before ungating. | LOW | 3h | **Low** -- currently behind feature flag |

---

## Respostas ao Architect

### 1. FE-01/02/03: Decomposition Strategy

**Recommended: Composition pattern + targeted Context for cross-cutting concerns.**

- **SearchResults.tsx (FE-01)**: Split into `ResultsToolbar` (sorting, export, counts), `ResultsList` (pagination + card iteration), `ResultCard` (single bid display), `ResultsLoadingState` (SSE progress, skeleton), `ResultsErrorState` (error display + retry). The ~55 props naturally group into 5-6 concerns. Each sub-component receives only its relevant props (5-10 each).

- **useSearch.ts (FE-03)**: Decompose into `useSearchExecution` (POST + response), `useSearchSSEIntegration` (SSE event routing), `useSearchRetry` (retry logic + countdown), `useSearchExport` (Excel + PDF + Google Sheets), `useSearchPersistence` (save/restore/partial cache). The orchestrating hook composes these and exposes a unified API.

- **conta/page.tsx (FE-02)**: Convert to tab-based sub-routes: `/conta/perfil`, `/conta/seguranca`, `/conta/plano`, `/conta/notificacoes`. Each tab is a separate file. Use Next.js nested layouts (`conta/layout.tsx`) for shared header/navigation.

**Why not Context API for everything:** Context causes re-renders on any value change. For SearchResults, the data changes frequently (progress events, partial results). Composition with prop grouping is more performant. Use Context only for truly cross-cutting data (plan info, auth session, theme) that changes rarely.

**Why not Zustand:** Adds a dependency for a problem solvable with composition. Zustand is justified only if state needs to be shared across unrelated component trees (not the case here -- all consumers are within the search page tree).

### 2. FE-08: SWR vs TanStack Query

**Recommended: SWR.**

Rationale:
- SWR is lighter (~4KB vs ~13KB for TanStack Query) -- matters for a product already loading Framer Motion, Recharts, etc.
- SWR's stale-while-revalidate model matches the existing backend cache pattern (the backend already implements SWR semantics)
- SSE is orthogonal to data fetching -- the SSE hooks (`useSearchSSE`) manage real-time events, not data fetching. SWR would replace the `useState + useEffect + fetch` boilerplate in `usePlan`, `useAnalytics`, `usePipeline`, `useSearchFilters`, etc. -- none of which use SSE.
- The core search `POST /buscar` is a mutation, not a query. SWR's `useSWRMutation` handles this cleanly.
- TanStack Query's advanced features (infinite queries, structural sharing, query cancellation) are not needed here.
- The team is small (1-2 devs). SWR's simpler API has lower learning curve.

**Migration path:** Start with read-only endpoints (`/v1/me`, `/v1/plans`, `/v1/analytics/*`, `/v1/pipeline`). These are pure GET requests with obvious cache keys. Then migrate `usePlan`, `useQuota`, `useAnalytics` hooks. Leave `useSearch` for last since it involves POST + SSE orchestration.

### 3. FE-18: SSG Conversion

**This question is now moot.** Verification confirmed all blog and SEO pages (`/blog/*`, `/licitacoes/*`, `/como-*`) are already Server Components. No `"use client"` directive found in any of these files. They use `Metadata` exports for SEO, `notFound()` for 404 handling, and import client sub-components where needed.

The only remaining SSG opportunity is enabling `generateStaticParams` for programmatic pages that currently use dynamic rendering. This is a performance optimization (build-time generation vs request-time), not a CSR-to-SSR migration. Estimated effort: 2-3h. Priority: Tier 3 (low impact since pages already render server-side).

### 4. FE-22: i18n Now vs Later

**Recommended: Later. Do not invest in i18n now.**

Justification:
- Product is pre-revenue, 100% Brazilian market, no international expansion plans
- 24-40h of effort for zero revenue impact
- The Portuguese strings are domain-specific (licitacao, edital, pregao, CNPJ) -- even with i18n, these terms have no direct English/Spanish equivalents
- If international expansion becomes viable, the i18n extraction can be done mechanically with tools like `react-i18next` + automated string extraction
- **Better investment:** Spend those 24-40h on design system primitives (FE-27-32) which have direct UX impact

**Downgrade severity from HIGH to LOW.**

### 5. FE-27-32: Design System Approach

**Recommended: Shadcn/ui.**

Rationale:
- **Shadcn/ui** copies components into your codebase (no dependency lock-in). This matches the project's pattern of owning all code.
- Shadcn uses Radix primitives underneath for accessibility (aria, keyboard navigation, focus management) -- gets WCAG compliance for free.
- Shadcn components use Tailwind CSS -- the project already uses Tailwind 3. CSS variable theming is already in place.
- The project already has design tokens (`--brand-blue`, `--ink`, `--canvas`, etc.) -- Shadcn components can be styled to use these existing tokens.
- Unlike building from scratch, Shadcn provides tested accessibility patterns (Button, Dialog, Select, Tooltip, etc.) out of the box.

**Implementation order:**
1. `Button` (highest impact, used everywhere) -- 4-6h
2. `Input` + `Label` (form consistency) -- 3-4h
3. `Badge` (status, plan, viability, LLM indicators) -- 2-3h
4. `Card` (result cards, dashboard cards, pipeline cards) -- 2-3h
5. `Select` (replace custom selects) -- 2h
6. `Dialog` (replace custom Dialog component) -- 2h

**Why not Radix directly:** Radix is unstyled -- would require building all styling from scratch. Shadcn provides the Radix accessibility + Tailwind styling integration pre-built.

**Why not build from scratch:** The project already has 15+ button variants implemented inline. Building a design system from scratch would replicate this inconsistency problem. Shadcn provides a proven starting point.

### 6. FE-33: Unify Search Page Navigation

**Recommended: Keep separate layout, but align visually.**

The search page (`/buscar`) intentionally uses a full-width layout without the sidebar. This is correct UX for a data-intensive search interface:
- Search results need maximum horizontal space (result cards, filter panels, progress grids)
- The sidebar steals 240-280px that is better used for data display
- Users spend 80%+ of their session on the search page -- it deserves an optimized layout

**However**, the current implementation creates visual discontinuity:
- The search page has its own header with logo, theme toggle, and user menu
- Other pages use the sidebar with the same controls
- Users navigating between search and dashboard experience a jarring layout shift

**Solution:** Keep the full-width layout but add a thin top navigation bar that mirrors the sidebar's visual language (same colors, same user menu, same logo). Remove the custom header. This preserves horizontal space while maintaining visual continuity. The sidebar items (Dashboard, Pipeline, Historico, Conta) appear as horizontal links in the top bar.

Estimated effort: 4-6h. Impact: Medium -- reduces cognitive load during navigation transitions.

### 7. FE-10: Prop Drilling Solution

**Recommended: Composition pattern (not Context, not Zustand).**

The 55 props in SearchResults naturally cluster into 6 groups:

1. **Loading state** (8 props): `loading`, `loadingStep`, `estimatedTime`, `stateCount`, `statesProcessed`, `onCancel`, `sseEvent`, `useRealProgress`
2. **Error state** (4 props): `error`, `quotaError`, `retryCountdown`, `onRetryNow`
3. **Results data** (6 props): `result`, `rawCount`, `ordenacao`, `onOrdenacaoChange`, `filterSummary`, `sourceStatuses`
4. **Export actions** (6 props): `downloadLoading`, `downloadError`, `onDownload`, `onRegenerateExcel`, `onGeneratePdf`, `pdfLoading`
5. **Plan/auth** (5 props): `planInfo`, `session`, `onShowUpgradeModal`, `isTrialExpired`, `trialPhase`
6. **SSE/progress** (10 props): `ufStatuses`, `ufTotalFound`, `partialProgress`, `refreshAvailable`, etc.

**Step 1:** Group props into typed objects (`LoadingState`, `ErrorState`, `ResultsData`, `ExportActions`, `PlanContext`, `ProgressState`). This reduces SearchResults from 55 props to 6-8 grouped props.

**Step 2:** Pass grouped objects to sub-components after decomposition (FE-01). Each sub-component receives only its relevant group.

**Step 3:** For truly cross-cutting data (plan info, auth session), use the existing `usePlan()` and `useAuth()` hooks inside sub-components rather than threading through props.

This approach eliminates prop drilling without introducing new state management dependencies.

---

## Recomendacoes de Design

### 1. SearchResults Decomposition (FE-01 + FE-10)

The search results area should be split into a **compositional tree**:

```
SearchResultsArea/
  ResultsToolbar       -- sorting, count, export buttons
  ResultsLoadingState  -- SSE progress, educational carousel, skeleton
  ResultsErrorState    -- structured error, retry mechanism
  ResultsList          -- pagination wrapper
    ResultCard         -- single bid card (viability, feedback, actions)
  ResultsEmptyState    -- zero results with suggestions
  ResultsBanners       -- cache, degradation, truncation banners
```

Each component has 5-10 props maximum. The parent `SearchResultsArea` receives grouped prop objects and distributes to children.

### 2. Button Component (FE-27)

Implement a `Button` component with these variants (observed from codebase audit):

- **Primary**: Blue background (`--brand-blue`), white text. Used for CTAs.
- **Secondary**: Transparent with border. Used for secondary actions.
- **Ghost**: No background, no border. Used for toolbar actions.
- **Destructive**: Red background. Used for delete/cancel.
- **Sizes**: `sm` (32px height), `md` (40px), `lg` (48px).
- **States**: Loading (spinner replaces text), disabled (opacity 50%).
- **Icon-only**: Square button with `aria-label` required.

### 3. Account Page Sub-routes (FE-02)

Convert to tabbed navigation with sub-routes:

```
/conta              -> redirect to /conta/perfil
/conta/perfil       -> Profile editing (CNAE, UFs, porte, atestados)
/conta/seguranca    -> Password change, MFA setup
/conta/plano        -> Plan info, billing, cancellation
/conta/notificacoes -> Alert preferences (future)
```

Use `conta/layout.tsx` for shared tab navigation. Each tab is <400 lines.

---

## Ordem de Resolucao Recomendada

From a UX perspective, ordered by user-visible impact per hour invested:

### Phase 1: Quick Wins (1 sprint, ~12h)

| # | ID | Horas | Justificativa |
|---|-----|-------|--------------|
| 1 | FE-12 + FE-13 | 2h | Accessibility compliance -- legal risk if reported |
| 2 | FE-27 (Button) | 4-6h | Most visible inconsistency; foundation for all future work |
| 3 | FE-07 | 2h | Replace inline SVGs with lucide-react + add aria-hidden |
| 4 | FE-24 | 0.5h | APP_NAME consolidation (trivial) |
| 5 | FE-14 | 2h | Viability scores need text alternatives |

### Phase 2: Structural (2 sprints, ~50-60h)

| # | ID | Horas | Justificativa |
|---|-----|-------|--------------|
| 6 | FE-10 | 6-8h | Group props into typed objects (prerequisite for FE-01) |
| 7 | FE-01 | 14-18h | Decompose SearchResults -- unblocks maintainability |
| 8 | FE-03 | 14-18h | Decompose useSearch -- unblocks FE-08 |
| 9 | FE-08 | 16-20h | Adopt SWR -- eliminates boilerplate, improves data freshness |

### Phase 3: Polish (2-3 sprints, ~30-40h)

| # | ID | Horas | Justificativa |
|---|-----|-------|--------------|
| 10 | FE-02 | 8-12h | Account page sub-routes |
| 11 | FE-28-30 | 7-10h | Input, Card, Badge primitives |
| 12 | FE-33 | 4-6h | Unify search page navigation |
| 13 | FE-19 | 3-4h | Dynamic imports for heavy deps |
| 14 | FE-17 | 2h | ARIA live regions for search progress |
| 15 | FE-15 | 2h | Form labels on onboarding |
| 16 | FE-32 | 3-4h | Consolidate design token usage |

### Phase 4: Backlog (as capacity allows)

FE-04, FE-05, FE-09, FE-11, FE-16, FE-20, FE-21, FE-22, FE-23, FE-25, FE-26, FE-31, FE-34-38, FE-39-42

---

## Quick Wins

Items that take less than 2h but have measurable UX impact:

| ID | Debito | Horas | Impact |
|----|--------|-------|--------|
| FE-12 + FE-13 | Add `aria-label` to icon-only buttons + `aria-hidden="true"` to sidebar SVGs | 1.5h | Screen reader users can navigate the app |
| FE-24 | Consolidate APP_NAME to single import from `lib/constants` | 0.5h | Prevents branding inconsistency if name changes |
| FE-07 | Replace sidebar `icons` object with lucide-react components | 1.5h | Consistency with rest of codebase + automatic aria-hidden |
| FE-23 | Audit and document the 3 eslint-disable locations | 0.5h | Confirms intentionality, prevents future copy-paste |

---

## Adjusted Totals

| Metrica | DRAFT v2.0 | Adjusted |
|---------|-----------|----------|
| Total frontend debts | 38 | 37 (FE-18 removed) + 4 added = **41** |
| FE-18 (Blog CSR) | 8-12h | **0h** (already fixed) |
| FE-22 (i18n) severity | HIGH | **LOW** (pre-revenue, BR only) |
| FE-02 severity | HIGH | **MEDIUM** (low-traffic page) |
| Total frontend effort | ~155-205h | **~135-175h** (FE-18 removed, some estimates adjusted) |

**Note to @architect:** The dependency graph in Section 7 of the DRAFT is correct. FE-01 does require FE-10 first, and FE-03 should precede FE-08 adoption. I would add one dependency: FE-27 (Button) should precede FE-01 (SearchResults decomp) since the decomposed sub-components should use the shared Button from day one.
