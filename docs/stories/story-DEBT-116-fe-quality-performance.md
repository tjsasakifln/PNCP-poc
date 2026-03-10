# DEBT-116: FE Quality & Performance

**Prioridade:** GTM-RISK (30 dias)
**Estimativa:** 16-20h
**Fonte:** Brownfield Discovery — @ux (FE-TD-023, FE-006, ARCH-006), @qa (QA-NEW-02)
**Score Impact:** Perf 7→8, Maint 6→7, Security 9→10

## Contexto
4 items agrupados: Framer Motion global (~70KB overhead), component directory convention, SearchForm decomposição, CSP style-src gap.

## Acceptance Criteria

### Framer Motion Isolation (4-6h)
- [x] AC1: Substituir framer-motion em GlassCard, ScoreBar, GradientButton por CSS transitions (visual idêntico)
- [x] AC2: ProfileCompletionPrompt e ProfileCongratulations: usar CSS @keyframes fade-in-up (já definido em globals.css)
- [x] AC3: framer-motion import apenas em landing page components + SearchStateManager (dynamic)
- [x] AC4: Bundle size de páginas autenticadas reduzido em ~70KB (verificar com .size-limit.js)

### Component Directory Convention (4-6h)
- [x] AC5: Documentar regra em README ou CONTRIBUTING.md: components/ = global (3+ pages), app/components/ = app-shared (2+ auth pages), page-local = 1 page
- [x] AC6: Mover BackendStatusIndicator de components/ para app/components/ (usa context provider)
- [x] AC7: Mover AlertNotificationBell de components/ para app/components/ (depende de auth context)

### SearchForm Decomposition (6-8h)
- [x] AC8: Split SearchForm.tsx (687 LOC) em: SearchFormHeader, SearchCustomizePanel, SearchFormActions
- [x] AC9: SearchForm container reduzido para <150 LOC
- [x] AC10: Prop drilling reduzido — cada sub-componente recebe apenas seus props relevantes

### CSP Style-src (2h)
- [x] AC11: Documentar style-src 'unsafe-inline' como accepted risk (necessário para Tailwind/Next.js) OU implementar nonce para styles
- [x] AC12: Se accepted risk: adicionar comment em middleware.ts explicando o rationale

## File List
- [x] `app/components/ui/GlassCard.tsx` (EDIT — CSS transitions, removed framer-motion)
- [x] `app/components/ui/ScoreBar.tsx` (EDIT — CSS transitions + IntersectionObserver)
- [x] `app/components/ui/GradientButton.tsx` (EDIT — CSS transitions)
- [x] `components/ProfileCompletionPrompt.tsx` (EDIT — CSS @keyframes fade-in-up)
- [x] `components/ProfileCongratulations.tsx` (EDIT — CSS @keyframes + confetti-dot animation)
- [x] `app/buscar/components/SearchForm.tsx` (EDIT — thin container, 125 LOC)
- [x] `app/buscar/components/SearchForm.types.ts` (NEW — extracted SearchFormProps interface)
- [x] `app/buscar/components/SearchFormHeader.tsx` (NEW — 289 LOC)
- [x] `app/buscar/components/SearchCustomizePanel.tsx` (NEW — 276 LOC)
- [x] `app/buscar/components/SearchFormActions.tsx` (NEW — 75 LOC)
- [x] `app/components/BackendStatusIndicator.tsx` (MOVED from components/)
- [x] `app/components/AlertNotificationBell.tsx` (MOVED from components/)
- [x] `frontend/CONTRIBUTING.md` (NEW — component directory convention)
- [x] `middleware.ts` (EDIT — CSP style-src accepted risk comment)
- [x] `app/globals.css` (EDIT — added @keyframes confetti-dot)
