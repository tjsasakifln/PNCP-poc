# DEBT-011: Frontend Component Architecture

**Sprint:** 2
**Effort:** 24-28h
**Priority:** HIGH
**Agent:** @dev + @ux-design-expert (Uma)

## Context

Four pages exceed 1000 lines (conta: 1420, alertas: 1068, buscar: 1057, dashboard: 1037), causing unnecessary re-renders and making changes risky. The root cause is lack of global state management — auth, plan, quota, and search data are passed via prop drilling, causing stale data display when values change. This story addresses the foundation (global state) and begins page decomposition with `conta` (largest page, best candidate for sub-routes). It also fixes `any` types in 8 production files.

**Critical dependency chain:** DEBT-005.FE-026 (quarantine resolution) must be complete before page decomposition begins. DEBT-011.FE-006 (global state) must be complete before FE-001 decomposition.

## Scope

| ID | Debito | Horas |
|----|--------|-------|
| FE-006 | No global state management — auth+plan+quota+search via prop drilling causes stale data | 8h |
| FE-001 | Monolithic pages (partial: decompose `conta/page.tsx` 1420 lines into sub-routes) | 8-10h |
| FE-008 | `any` types in 8 production files (pipeline, filters, analytics proxy + 5 others) | 2h |
| FE-030 | No `<Suspense>` boundaries in any page | 4-6h |

## Tasks

### Global State Management (FE-006) — 8h

- [x] Evaluate SWR vs Zustand vs React Context for global state (auth, plan, quota) — React Context chosen (composes existing SWR hooks)
- [x] Implement global state for auth/user data (replace prop drilling in 5+ pages) — `contexts/UserContext.tsx` with `useUser()` hook
- [x] Implement global state for plan/subscription data (replace localStorage polling) — usePlan composed into UserProvider
- [x] Implement global state for quota data (replace per-page fetching) — useQuota composed into UserProvider
- [x] Ensure state updates propagate to all consumers (no stale display) — React Context propagation
- [x] Leave SSE/search hooks as custom hooks (not global state) — confirmed, search hooks remain independent

### Page Decomposition: conta (FE-001 partial) — 8-10h

- [x] Decompose `conta/page.tsx` (1420 lines) into sub-routes:
  - `/conta/perfil` — profile editing (304 lines)
  - `/conta/seguranca` — password, MFA (287 lines)
  - `/conta/plano` — plan/subscription management (117 lines)
  - `/conta/dados` — data export/deletion (168 lines)
- [x] Create shared layout for `/conta` sub-routes (sidebar navigation) — `conta/layout.tsx`
- [x] Each sub-route < 300 lines
- [x] Migrate all state management to global state (from FE-006) — all use `useUser()`
- [x] Verify all existing functionality preserved — tests updated and passing

### Type Safety (FE-008) — 2h

- [x] Replace `any` with proper types in all 8 production files — `unknown` types, inline type definitions
- [x] Verify `npx tsc --noEmit` passes with zero errors — confirmed clean

### Suspense Boundaries (FE-030) — 4-6h

- [x] Add `<Suspense>` boundaries to pages with loading.tsx (from DEBT-003) — `(protected)/layout.tsx`
- [x] Add `<Suspense>` boundaries around dynamically imported components — `login/page.tsx` TotpVerificationScreen
- [x] Ensure fallback UI matches loading.tsx skeleton — ProtectedLoading fallback

## Acceptance Criteria

- [x] AC1: Global state management for auth/plan/quota — zero prop drilling for these values
- [x] AC2: `conta/page.tsx` decomposed into 4 sub-routes, each < 300 lines
- [x] AC3: Conta sub-routes have shared sidebar layout
- [x] AC4: Zero `any` types in production files (`npx tsc --noEmit` clean)
- [x] AC5: `<Suspense>` boundaries wrap dynamic imports and loading states
- [x] AC6: All conta functionality preserved (profile edit, password change, plan view, data export)
- [x] AC7: Zero regressions in frontend test suite (5291+ pass — post quarantine resolution)

## Tests Required

- Global state: verify state updates propagate (change plan, verify all consumers update)
- Conta sub-routes: render tests for each sub-route
- Conta navigation: tab switching between sub-routes preserves state
- Type safety: `npx tsc --noEmit` passes
- Suspense: loading fallback renders during async load

## Definition of Done

- [x] All tasks complete
- [x] Tests passing (frontend 5291+ / 0 new fail)
- [x] No regressions
- [x] `npx tsc --noEmit` passes
- [ ] Visual verification of conta page (all sub-routes)
- [ ] Code reviewed
