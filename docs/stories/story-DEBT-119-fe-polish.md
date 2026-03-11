# DEBT-119: Frontend Polish — Hex Colors, localStorage, Icons, A11y

**Prioridade:** POST-GTM
**Estimativa:** 15h
**Fonte:** Brownfield Discovery — @ux (FE-TD-008, FE-008, FE-009, FE-A11Y-01, FE-A11Y-03)
**Score Impact:** UX 9→9.5

## Contexto
5 items de polish frontend: 96 raw hex colors que deveriam usar Tailwind tokens, 6 arquivos usando raw localStorage sem safe wrappers, inline SVGs em conta/layout.tsx, loading spinners sem role="status", SVGs sem aria-hidden.

## Acceptance Criteria

### Hex Colors → Tailwind Tokens (6h)
- [x] AC1: Auditar 96 raw hex colors em 20 TSX files
- [x] AC2: Excluir ThemeProvider.tsx (hex colors corretos — definem CSS variables)
- [x] AC3: Excluir social button colors (Google blue, GitHub black) — manter como constantes
- [x] AC4: Substituir demais hex colors por Tailwind tokens ou var(--*) references
- [x] AC5: Sem mudanças visuais (verificar visualmente páginas afetadas)

### localStorage Safe Wrappers (3h)
- [x] AC6: Identificar 6 arquivos com raw localStorage.getItem/setItem
- [x] AC7: Substituir por safeGetItem/safeSetItem de lib/storage.ts
- [x] AC8: Testes existentes passam

### Inline SVGs → Lucide (4h)
- [x] AC9: Substituir 5 inline SVGs em conta/layout.tsx por Lucide React icons
- [x] AC10: Adicionar aria-hidden="true" aos novos ícones (decorativos)

### A11y Quick Wins (2h)
- [x] AC11: Adicionar role="status" em loading spinners faltantes (login page, auth callback)
- [x] AC12: Adicionar aria-hidden="true" em SVGs decorativos em planos/page.tsx
- [x] AC13: npm test passa, 0 regressions

## File List
- [x] `components/OnboardingTourButton.tsx` (EDIT — hex #1e3a5f/#2a4d7a → var(--brand-navy)/var(--brand-blue-hover))
- [x] `components/ProfileProgressBar.tsx` (EDIT — hex → var(--success)/var(--warning)/var(--error))
- [x] `components/ProfileCongratulations.tsx` (EDIT — confetti hex → var() with fallbacks)
- [x] `app/dashboard/DashboardCharts.tsx` (EDIT — hex #116dff/#16a34a → var(--brand-blue)/var(--success))
- [x] `app/buscar/hooks/useSearchFilters.ts` (EDIT — 6x localStorage → safeGetItem)
- [x] `app/buscar/components/SearchResults.tsx` (EDIT — 2x localStorage → safeGetItem)
- [x] `app/components/ContextualTutorialTooltip.tsx` (EDIT — 1x localStorage → safeGetItem)
- [x] `app/conta/layout.tsx` (EDIT — 5 inline SVGs → Lucide icons + aria-hidden)
- [x] `app/planos/page.tsx` (EDIT — aria-hidden on FAQ chevron SVG + role="status" on spinner)
- [x] `app/login/page.tsx` (EDIT — 3x role="status" on loading spinners)
- [x] `app/auth/callback/page.tsx` (EDIT — role="status" on loading spinner)

### Excluded (correct as-is)
- `app/components/ThemeProvider.tsx` — hex colors define CSS variables (AC2)
- `app/global-error.tsx` — defines own CSS vars (can't use Tailwind, root layout failed)
- `app/api/og/route.tsx` — OG image generation (ImageResponse, no CSS var support)
- `app/login/page.tsx` + `app/signup/page.tsx` — Google OAuth SVG brand colors (AC3)
- `app/buscar/components/GoogleSheetsExportButton.tsx` — Google Sheets brand colors (AC3)
- `app/layout.tsx` — inline <script> for theme flash prevention (raw JS, can't import modules, already try/catch wrapped)
- `app/components/GoogleAnalytics.tsx` — inline Script for GA (raw JS string, can't import modules)
- `components/TestimonialSection.tsx` — already uses var() with hex fallback
- `components/KeyboardShortcutsHelp.tsx` — already uses var() with hex fallback
- `app/planos/obrigado/ObrigadoContent.tsx` — already uses var() with hex fallback
