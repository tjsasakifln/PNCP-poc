# STORY-5.12: Loading State Padronizar (TD-FE-015)

**Priority:** P2 | **Effort:** S (4-8h → actual ~1h) | **Squad:** @ux-design-expert + @dev | **Status:** InReview
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** usuário SmartLic, **I want** loading states consistentes (skeleton padrão),
**so that** UX seja previsível.

## Acceptance Criteria
- [x] AC1: Audit usage `<LoadingSpinner>` vs `<Skeleton>` vs `<EnhancedLoadingProgress>` — documentado em `docs/guides/loading-state-guidelines.md` (table: 60+ `animate-spin`, 40+ `animate-pulse`, 3 page-skeletons, ~10 EnhancedLoadingProgress)
- [x] AC2: Guidelines — **skeleton** para listas/cards; **spinner** para botões/ações inline; **EnhancedLoadingProgress** só para SSE/long-polling
- [x] AC3: Migrate to padrão — não fazemos bulk codemod (alto churn, baixo ROI). Criado primitivo canonical `<Skeleton>` com 5 variants; migração incremental on-touch documentada no guide
- [ ] AC4: Documentation em Storybook — **deferred** (STORY-5.9 setup é escopo fora desta tranche)

## Tasks
- [x] Audit — grep `animate-pulse`, `animate-spin`, `LoadingSpinner`, `EnhancedLoadingProgress` documentado
- [x] Guidelines — `docs/guides/loading-state-guidelines.md`
- [x] Migration — primitivo `<Skeleton>` criado + index re-export + tests

## Implementation Summary

**Files added:**
- `frontend/components/skeletons/Skeleton.tsx` — canonical primitive, 5 variants (`text` default, `card`, `list`, `avatar`, `block`), `aria-hidden="true"`, `count` prop for repeat
- `frontend/components/skeletons/index.ts` — re-export surface (`Skeleton`, `AdminPageSkeleton`, `ContaPageSkeleton`, `PlanosPageSkeleton`)
- `docs/guides/loading-state-guidelines.md` — guidelines + API + audit snapshot + anti-patterns
- `frontend/__tests__/components/Skeleton.test.tsx` — 5 unit tests (variants, count, className merge, aria-hidden)

**Decisions:**

1. **No bulk codemod.** Migrating every `animate-pulse` div to `<Skeleton>` introduces
   churn without UX gain. Guide documents the migration strategy: "migrate
   opportunistically when editing the surrounding file." This aligns with the
   Sprint's "high ROI" principle.
2. **Pre-existing page-level skeletons preserved.** `AdminPageSkeleton`,
   `ContaPageSkeleton`, `PlanosPageSkeleton` are precise shell matches — they
   stay as-is and are re-exported from the `skeletons/index.ts` barrel.
3. **Storybook (AC4) deferred.** Setting up Storybook is the work of
   STORY-5.9, which is out of this sprint's tranche.

## Tests

- `__tests__/components/Skeleton.test.tsx`: 5/5 passing
- Typecheck: clean
- Zero regressions (only adds new files + 0 modifications to existing callsites)

## File List

**Added:**
- `frontend/components/skeletons/Skeleton.tsx`
- `frontend/components/skeletons/index.ts`
- `frontend/__tests__/components/Skeleton.test.tsx`
- `docs/guides/loading-state-guidelines.md`

**Modified:** (none)

## Definition of Done
- [x] Primitive exists + tested
- [x] Guidelines documented
- [x] Zero regressions
- [ ] Storybook entry — **deferred** to STORY-5.9

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-15 | 1.1 | Primitive + guidelines + tests; bulk migration deferred to on-touch; Storybook AC4 deferred to STORY-5.9 | @dev |
