# STORY-267: Enterprise UX Polish — Error Handling & Accessibility

## Metadata
- **Epic:** Enterprise Readiness (EPIC-ENT-001)
- **Priority:** P1 (Stability)
- **Effort:** 5 hours
- **Area:** Frontend
- **Depends on:** None
- **Risk:** Low (novos arquivos + edits em strings/imports)
- **Assessment IDs:** T2-11, T2-16, T2-17, T2-18, T2-19
- **Status:** DONE

## Context

O UX Enterprise Readiness Score atual e 3.7/5. Para atingir 4.0+ (enterprise-presentable), 5 fixes sao necessarios: (1) error boundaries expoem `error.message` raw ao usuario — o issue UX mais danoso; (2) 4 paginas protegidas nao tem error boundary proprio; (3) pagina 404 tem acentos faltando em portugues; (4) `global-error.tsx` usa inline styles fora do design system; (5) BottomNav drawer nao tem focus trap (WCAG violation).

## Acceptance Criteria

### T2-19: getUserFriendlyError em error boundaries
- [x] AC1: `app/error.tsx` usa `getUserFriendlyError()` para filtrar `error.message`
- [x] AC2: `app/buscar/error.tsx` usa `getUserFriendlyError()`
- [x] AC3: `app/dashboard/error.tsx` usa `getUserFriendlyError()`
- [x] AC4: `app/admin/error.tsx` usa `getUserFriendlyError()`
- [x] AC5: Nenhum error boundary exibe raw `error.message` ao usuario

### T2-18: Error boundaries para 4 paginas
- [x] AC6: `app/pipeline/error.tsx` existe com mensagem contextual em portugues
- [x] AC7: `app/historico/error.tsx` existe com mensagem contextual em portugues
- [x] AC8: `app/mensagens/error.tsx` existe com mensagem contextual em portugues
- [x] AC9: `app/conta/error.tsx` existe com mensagem contextual em portugues
- [x] AC10: Todas as 4 novas error boundaries usam `getUserFriendlyError()`

### T2-16: 404 acentos
- [x] AC11: `app/not-found.tsx` exibe texto com acentos corretos em portugues

### T2-17: global-error.tsx brand
- [x] AC12: `app/global-error.tsx` usa cores do design system (nao hardcoded `#f9fafb`)
- [x] AC13: `global-error.tsx` suporta dark mode via media query
- [x] AC14: Botao de acao usa cor brand-blue

### T2-11: Focus trap
- [x] AC15: BottomNav drawer prende foco dentro do overlay quando aberto
- [x] AC16: Pressionar Escape fecha o drawer
- [x] AC17: Foco retorna ao botao trigger apos fechar

## Tasks

### T2-19: getUserFriendlyError (1h)
- [x] Task 1: Em `app/error.tsx`: importar `getUserFriendlyError` de `lib/error-messages.ts` e aplicar no render de `error.message`
- [x] Task 2: Repetir para `app/buscar/error.tsx`
- [x] Task 3: Repetir para `app/dashboard/error.tsx`
- [x] Task 4: Repetir para `app/admin/error.tsx`

### T2-18: Novas error boundaries (2h)
- [x] Task 5: Criar `app/pipeline/error.tsx` — copiar pattern de `buscar/error.tsx`, mensagem: "Ocorreu um erro ao carregar o pipeline. Tente novamente."
- [x] Task 6: Criar `app/historico/error.tsx` — mensagem: "Ocorreu um erro ao carregar o historico. Tente novamente."
- [x] Task 7: Criar `app/mensagens/error.tsx` — mensagem: "Ocorreu um erro ao carregar as mensagens. Tente novamente."
- [x] Task 8: Criar `app/conta/error.tsx` — mensagem: "Ocorreu um erro ao carregar sua conta. Tente novamente."
- [x] Task 9: Todas as novas error boundaries importam e usam `getUserFriendlyError()`

### T2-16: 404 acentos (5min)
- [x] Task 10: Em `app/not-found.tsx`: corrigir strings com acentos portugueses corretos

### T2-17: global-error.tsx (30min)
- [x] Task 11: Substituir inline styles hardcoded por valores do design system
- [x] Task 12: Adicionar `<style>` tag com `@media (prefers-color-scheme: dark)` para dark mode
- [x] Task 13: Botao de acao com cor brand (nao verde generico)

### T2-11: Focus trap (1.5h)
- [x] Task 14: Adicionar focus trap ao drawer overlay em `components/BottomNav.tsx`
- [x] Task 15: Implementar Escape para fechar drawer
- [x] Task 16: Implementar retorno de foco ao trigger button apos fechar

## Test Plan

### Error Boundaries (T2-18/19)
1. Para cada pagina protegida: simular erro React -> verificar que mensagem amigavel aparece (nao raw `error.message`)
2. Verificar que `getUserFriendlyError()` cobre os tipos de erro mais comuns
3. `npm test` — 0 regressions

### 404 (T2-16)
1. Navegar para `/pagina-inexistente` -> verificar acentos corretos visualmente

### Global Error (T2-17)
1. Simular crash do root layout -> verificar cores brand em light mode
2. Verificar dark mode via media query
3. Verificar que botao usa cor brand

### Focus Trap (T2-11)
1. Mobile: abrir drawer -> Tab por todos os elementos focaveis -> foco nao sai do drawer
2. Pressionar Escape -> drawer fecha
3. Apos fechar, foco retorna ao botao trigger
4. Verificar que touch/swipe nao e afetado pelo focus trap

### Suite Completa
5. `npm test` — 3306 passing, 0 failures (baseline exceeded)
6. `npm run lint` — ESLint not installed (pre-existing)

## Regression Risks

- **Baixo (T2-18/19):** Novos arquivos + import de funcao existente. Nenhum componente existente e alterado destrutivamente.
- **Baixo (T2-16):** 2 string replacements.
- **Baixo (T2-17):** `global-error.tsx` nao pode usar Tailwind/CSS imports (root layout falhou). Inline styles devem funcionar standalone. Testar que page renderiza sem dependencias externas.
- **Baixo (T2-11):** Focus trap deve nao interferir com touch/swipe em mobile. Testar em device real ou emulador.

## Files Changed

### Editados
- `frontend/app/error.tsx` (EDIT — add getUserFriendlyError)
- `frontend/app/buscar/error.tsx` (EDIT — add getUserFriendlyError)
- `frontend/app/dashboard/error.tsx` (EDIT — add getUserFriendlyError)
- `frontend/app/admin/error.tsx` (EDIT — add getUserFriendlyError)
- `frontend/app/not-found.tsx` (EDIT — fix accents)
- `frontend/app/global-error.tsx` (EDIT — brand alignment + dark mode)
- `frontend/components/BottomNav.tsx` (EDIT — focus trap)

### Novos
- `frontend/app/pipeline/error.tsx` (NEW)
- `frontend/app/historico/error.tsx` (NEW)
- `frontend/app/mensagens/error.tsx` (NEW)
- `frontend/app/conta/error.tsx` (NEW)
- `frontend/__tests__/story-267-enterprise-ux-polish.test.tsx` (NEW — 41 tests)

## Definition of Done

- [x] Todos os 17 acceptance criteria met
- [x] Nenhuma pagina protegida mostra raw error.message
- [x] 404 com acentos corretos
- [x] global-error.tsx com brand alignment + dark mode
- [x] Focus trap funcional no BottomNav drawer
- [x] `npm test` passing (3306 tests, 0 failures)
- [ ] `npm run lint` passing (ESLint not installed — pre-existing)
- [x] UX Enterprise Score: 4.0+/5
