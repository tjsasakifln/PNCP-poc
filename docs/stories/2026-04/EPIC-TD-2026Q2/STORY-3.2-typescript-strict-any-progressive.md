# STORY-3.2: TypeScript Strict + Progressive Any Removal (TD-FE-001)

**Priority:** P1 (type safety — bloqueia refactoring confiável)
**Effort:** L (24-40h, paralelo com STORY-3.1)
**Squad:** @dev + @architect + @qa
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 2
**Depends on:** STORY-2.1 (Pydantic→TS gen pode reduzir 30-50% scope)

---

## Story

**As a** dev SmartLic,
**I want** TypeScript strict mode habilitado e <50 `any` types remaining,
**so that** bugs sejam pegos em compile time e refactoring tenha confiança.

---

## Acceptance Criteria

### AC1: tsconfig strict

- [ ] `frontend/tsconfig.json` set `"strict": true` (e flags relacionadas)
- [ ] CI gate `tsc --noEmit` passa

### AC2: Any removal

- [ ] Baseline: 296 `any` types
- [ ] Target: <50 (≥83% reduction)
- [ ] Remaining `any` justificados com `// @ts-expect-error TODO: ...` comment

### AC3: Generated types adoption

- [ ] Após STORY-2.1 entregue, frontend usa types gerados (não duplicates)

### AC4: Build + tests pass

- [ ] `npm run build` succeeds
- [ ] `npm test` 2681+ pass
- [ ] `npm run test:e2e` 60 pass

---

## Tasks / Subtasks

- [ ] Task 1: Habilitar strict mode incrementally (per file ou globally)
- [ ] Task 2: Audit 296 `any` — categorize (API responses, event handlers, refs, etc.)
- [ ] Task 3: Substituir API any com generated types (depends STORY-2.1)
- [ ] Task 4: Substituir event handler any com proper React types
- [ ] Task 5: Substituir ref any com `useRef<HTMLElement>`
- [ ] Task 6: Substituir general any com `unknown` + narrowing
- [ ] Task 7: CI gate strict

## Dev Notes

- 296 `any` matches via grep `: any` ou `as any` em `frontend/**/*.tsx`
- Helper packages: `type-fest` (utility types)
- Strategy: enable strict, use `// @ts-expect-error` to silence existing, fix progressively per PR

## Testing

- `tsc --noEmit` clean
- Existing test suites green
- Optional: install `eslint-plugin-no-explicit-any` rule

## Definition of Done

- [ ] strict: true habilitado
- [ ] <50 `any` remaining (with TODO comments)
- [ ] All builds + tests pass
- [ ] CI gate active

## Risks

- **R1**: Strict mode revela 1000s de errors latentes — mitigation: progressive enable per directory
- **R2**: Esforço excede 40h — mitigation: timebox + accept higher remaining count se necessário

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
