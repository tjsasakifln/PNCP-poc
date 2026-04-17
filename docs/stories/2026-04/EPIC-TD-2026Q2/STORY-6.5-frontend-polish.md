# STORY-6.5: Frontend Polish (TD-FE-030, 031, 032)

**Priority:** P3 | **Effort:** S (6-13h) | **Squad:** @ux-design-expert + @dev | **Status:** Ready for Review
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 7+

## Story
**As a** SmartLic, **I want** débitos low FE resolvidos, **so that** polish final.

## Acceptance Criteria
- [x] AC1 (TD-FE-030): Toast positioning mobile fix (centro-bottom, não cobrindo nav)
  - `mobileOffset={{ bottom: 80 }}` — clears BottomNav (h-16=64px + 16px gap)
  - `toastOptions.classNames.toast = "max-w-[90vw] sm:max-w-md"` — 90vw mobile, md desktop
  - 5 unit tests passando (`toast-mobile-positioning.test.tsx`)
- [x] AC2 (TD-FE-031): JSDoc adicionado em components core
  - `components/ui/button.tsx` — JSDoc completo com @param e @example (4 exemplos)
  - `components/ui/Input.tsx` — JSDoc completo com @param e @example (3 exemplos)
  - `components/Modal.tsx` — JSDoc completo com @param e @example (2 exemplos)
  - `Card.tsx` não existe no codebase — documentado em Dev Notes
- [x] AC3 (TD-FE-032): `Button.examples.tsx` migrado para Storybook e arquivo removido
  - Novas stories em `button.stories.tsx`: WithIconAdd, WithIconDelete, WithIconDownload, LoadingSecondary, LoadingDestructive, DisabledSecondary, AllVariantsSm, AllVariantsLg (8 novas)
  - `Button.examples.tsx` deletado
  - Storybook build validado — falha por problema **pré-existente** de configuração webpack (presente antes desta story, em múltiplos story files)

## Tasks
- [x] Toast CSS adjust (mobileOffset + toastOptions classNames)
- [x] JSDoc per component (button, Input, Modal)
- [x] Storybook migration (Button.examples → button.stories)

## Dev Notes
- `Card.tsx` não existe em `components/` nem `components/ui/` — AC2 se aplica aos 3 que existem
- Storybook build falha com `Module parse failed: Unexpected token (1:12)` — problema pré-existente de configuração TypeScript/webpack do Storybook (confirmado: falha no estado limpo do branch antes desta story, em múltiplos files como EmptyState.stories, ErrorMessage.stories, Modal.stories). Não introduzido por esta story.
- `next lint` não existe mais no Next.js 16 CLI. Validação de TypeScript via `npx tsc --noEmit` (zero erros).

## File List

### Created
- `frontend/__tests__/layout/toast-mobile-positioning.test.tsx` — 5 unit tests para AC1

### Modified
- `frontend/app/layout.tsx` — Toaster: mobileOffset + toastOptions.classNames
- `frontend/components/ui/button.tsx` — JSDoc completo com @param/@example
- `frontend/components/ui/Input.tsx` — JSDoc completo com @param/@example
- `frontend/components/Modal.tsx` — JSDoc completo com @param/@example
- `frontend/components/ui/button.stories.tsx` — 8 novas stories do Button.examples

### Deleted
- `frontend/components/ui/Button.examples.tsx` — migrado para button.stories.tsx

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-16 | 1.1 | AC1-AC3 completos (Toast mobile, JSDoc 3 componentes, Button stories migrado) | @dev |
