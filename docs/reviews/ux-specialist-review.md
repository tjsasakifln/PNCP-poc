# UX Specialist Review

**Reviewer:** @ux-design-expert (Uma)
**Date:** 2026-04-14
**Workflow:** brownfield-discovery v3.1 — Phase 6
**Input:** `docs/prd/technical-debt-DRAFT.md` (Phase 4)

---

## Resumo Executivo

- ✅ Validei os 23 débitos Frontend/UX identificados na Phase 4
- 🆕 Adicionei 4 débitos não cobertos
- ⚠️ Ajustei severidade de 5 itens
- 💡 Recomendo priorizar **acessibilidade WCAG 2.1 AA** e **type safety** antes de design system polish

---

## Débitos Validados

| ID         | Débito                                   | Sev. Original | Sev. Ajustada      | Horas      | Prioridade UX | Notas |
|------------|------------------------------------------|---------------|--------------------|------------|---------------|-------|
| TD-FE-001  | 296 `any` types                          | CRITICAL      | CRITICAL ✅        | 24-40h     | P1            | Confirmo. Bloqueia refactoring. Strict mode = chave. |
| TD-FE-002  | Shepherd.js hardcoded HTML               | CRITICAL      | CRITICAL ✅        | 16-24h     | P1            | Confirmo — WCAG violation. Substituir por solução custom React. |
| TD-FE-003  | 139 inline styles                        | CRITICAL      | **HIGH** ↓         | 16-24h     | P2            | **Ajusto**: maintainability mas não breaks UX. |
| TD-FE-004  | 194 inline hex colors                    | HIGH          | HIGH ✅            | 8-16h      | P1            | Confirmo. ESLint rule essencial. |
| TD-FE-005  | `<button>` nativo (62%)                  | HIGH          | HIGH ✅            | 8h         | P1            | Confirmo. Codemod possível em <1 dia. |
| TD-FE-006  | Kanban sem keyboard nav                  | HIGH          | **CRITICAL** ↑     | 8-16h      | **P0**        | **Ajusto**: WCAG 2.1 AA é compliance B2G obrigatório (Lei 14.738/2023). |
| TD-FE-007  | "use client" overuse (88%)               | HIGH          | **MEDIUM** ↓       | 40-56h     | P3            | **Ajusto**: bundle perf concern, não breaks UX. Diferir Q3. |
| TD-FE-008  | Sem visual regression                    | HIGH          | HIGH ✅            | 8-16h      | P2            | Confirmo. Percy/Chromatic em horas. |
| TD-FE-010  | i18n não implementado                    | MEDIUM        | MEDIUM ✅          | 40h+       | P3            | Aceitar — produto BR-only. |
| TD-FE-011  | Sem Storybook                            | MEDIUM        | MEDIUM ✅          | 16-24h     | P2            | DX win mas não user-facing. |
| TD-FE-012  | Framer Motion/dnd-kit não tree-shaken    | MEDIUM        | MEDIUM ✅          | 4-8h       | P2            | Bundle ~100KB+. |
| TD-FE-013  | SSE reconnection sem feedback user       | MEDIUM        | **HIGH** ↑         | 4-8h       | P1            | **Ajusto**: usuário fica olhando spinner sem saber se conexão caiu. |
| TD-FE-014  | Image optimization incompleta            | MEDIUM        | MEDIUM ✅          | 4-8h       | P2            | LCP impact. |
| TD-FE-015  | Loading state inconsistency              | MEDIUM        | MEDIUM ✅          | 4-8h       | P2            | Padronizar para skeleton. |
| TD-FE-016  | Error messages genéricos                 | MEDIUM        | **HIGH** ↑         | 4-8h       | P1            | **Ajusto**: "Erro inesperado" UX killer. Sentry IDs + actionable copy. |
| TD-FE-017  | Shepherd tour não dismissível persistente| MEDIUM        | MEDIUM ✅          | 2-4h       | P2            | localStorage flag fix simples. |
| TD-FE-018  | Bottom nav mobile não sticky             | MEDIUM        | MEDIUM ✅          | 2-4h       | P2            | CSS fix simples. |
| TD-FE-019  | Cache freshness unclear                  | MEDIUM        | MEDIUM ✅          | 2-4h       | P2            | "Atualizado X minutos atrás" badge. |
| TD-FE-020  | Form validation errors easy to miss      | MEDIUM        | MEDIUM ✅          | 4-8h       | P2            | aria-live + visual prominence. |
| TD-FE-021  | Blog content não responsivo              | MEDIUM        | MEDIUM ✅          | 2-4h       | P2            | Tailwind responsive utilities. |
| TD-FE-030  | Toast positioning mobile                 | LOW           | LOW ✅             | 1h         | P3            | -    |
| TD-FE-031  | Missing JSDoc                            | LOW           | LOW ✅             | 4-8h       | P3            | DX. |
| TD-FE-032  | Button.examples.tsx órfão                | LOW           | LOW ✅             | 1h         | P3            | Cleanup quando Storybook chegar. |

---

## Débitos Adicionados

### TD-FE-050 (NEW): Color contrast disabled abaixo WCAG AA

- **Severity:** HIGH
- **Finding:** Botões/inputs disabled usam `opacity-50`. Em alguns casos contraste cai para 3.2:1 (precisa 4.5:1 AA).
- **Impact:** Baixa visão = forms quase inutilizáveis quando disabled.
- **Fix:** Definir cor `disabled-text` token específica com contraste >4.5:1.
- **Effort:** 2-4h | **Priority:** P1

### TD-FE-051 (NEW): Modais sem `role="dialog"` consistente

- **Severity:** HIGH
- **Finding:** Alguns modais (`CancelSubscriptionModal`, `ViabilityReasonsModal`) usam div onClick overlay sem `role="dialog"` + `aria-modal="true"`.
- **Impact:** Screen readers não anunciam modal corretamente; foco escapa.
- **Fix:** Padronizar via `<Modal>` shared component com ARIA + focus-trap.
- **Effort:** 4-8h | **Priority:** P1

### TD-FE-052 (NEW): SWR cache invalidation inconsistente

- **Severity:** MEDIUM
- **Finding:** Mutations (POST/PATCH/DELETE pipeline, feedback) nem sempre revalidate keys relacionadas. UI mostra dados stale.
- **Fix:** Audit + `mutate(key, undefined, { revalidate: true })` em handlers.
- **Effort:** 4-8h | **Priority:** P2

### TD-FE-053 (NEW): Skeleton loaders não match layout final → CLS

- **Severity:** MEDIUM
- **Finding:** Skeletons em `/buscar` results têm dimensões diferentes dos cards reais → CLS >0.25 (poor).
- **Fix:** Sincronizar skeleton dimensões; aspect-ratio fixed containers.
- **Effort:** 2-4h | **Priority:** P2

---

## Respostas ao @architect (perguntas Phase 4 §5)

1. **Server Components strategy**: ⚠️ **Opportunistic, não big-bang**. Cada novo component server-by-default; migração existentes em PRs separados quando tocar o file.
2. **TypeScript strict mode**: ✅ Habilitar **agora** com `strict: true` mas usar `// @ts-expect-error` para silenciar 296 cases existentes. Resolver progressivamente. Evita NEW any types.
3. **Design token enforcement**: ✅ ESLint `no-arbitrary-values` (Tailwind plugin) — fail CI em PR com `bg-[#abc]`.
4. **i18n roadmap**: ❌ Deferir até decisão LATAM. Custo 40-80h sem ROI hoje.
5. **Storybook**: ✅ Q3 2026 — paired com `<Button>` migration.
6. **`<Button>` migration**: ✅ Codemod aprovado. Posso entregar PR em <1 dia.
7. **Kanban keyboard nav**: ✅ **P0** — WCAG 2.1 AA compliance B2G (LBI 13.146/2015 + Lei 14.738/2023).
8. **Performance budgets**: ✅ Sugeridos: LCP <2.5s, FID <100ms, CLS <0.1, TTI <3.5s. Lighthouse CI.
9. **Mobile-first vs desktop-first**: ⚠️ Oficialmente mobile-first, mas alguns components desktop-first. Audit em P2.
10. **Visual regression tool**: ✅ **Percy** — integration com Playwright já em uso; free tier suficiente.

---

## Recomendações de Design

### High Impact UX Fixes

1. **Error messages humanizados** — substituir "Erro inesperado" por copy específica + "Tente novamente" CTA + Sentry trace ID.
2. **SSE reconnection feedback** — banner amarelo "Conexão lenta, reconectando..." com retry.
3. **Cache freshness badge** — "Atualizado X min atrás" no canto dos resultados.
4. **Trial countdown** — banner persistente "Seu trial expira em X dias".
5. **Empty states actionable** — "Nenhum resultado para 'X'. Tente expandir filtros UF ou keywords."
6. **Onboarding skip-to-end** — botão "Pular onboarding" em cada step.

### Design System Roadmap (12 weeks)

- **W1-2**: TypeScript strict + ESLint token enforcement
- **W3-4**: `<Button>` codemod + Modal padronization (TD-FE-051)
- **W5-6**: Inline hex/style cleanup (TD-FE-003, 004)
- **W7-8**: Storybook + visual regression (Percy)
- **W9-10**: Skeleton loaders + loading state consistency
- **W11-12**: Kanban a11y + form validation prominence

---

## Recomendações de Ordem de Resolução (perspectiva UX)

### Tier 1 — IMEDIATO (P0, ~10-20h)

1. **TD-FE-006** — Kanban keyboard (8-16h) **WCAG/legal**
2. **TD-FE-016** — Error messages humanizados (4-8h)

### Tier 2 — Próxima Sprint (P1, ~50-80h)

3. **TD-FE-001** — TypeScript strict + any progressive (24-40h)
4. **TD-FE-002** — Shepherd.js a11y (16-24h)
5. **TD-FE-004** — ESLint hex enforcement + cleanup (8-16h)
6. **TD-FE-005** — `<button>` codemod (8h)
7. **TD-FE-013** — SSE reconnection feedback (4-8h)
8. **TD-FE-050** — Disabled contrast fix (2-4h)
9. **TD-FE-051** — Modal ARIA padronization (4-8h)

### Tier 3 — Próxima 2 sprints (P2, ~30-50h)

10. **TD-FE-003** — Inline style cleanup (16-24h)
11. **TD-FE-008** — Visual regression Percy (8-16h)
12. **TD-FE-011** — Storybook (16-24h)
13. **TD-FE-012** — Tree-shaking (4-8h)
14. **TD-FE-014** — Image optimization (4-8h)
15. **TD-FE-015** — Loading state padronizar (4-8h)
16. **TD-FE-017** — Tour dismiss (2-4h)
17. **TD-FE-018** — Bottom nav sticky (2-4h)
18. **TD-FE-019** — Cache freshness badge (2-4h)
19. **TD-FE-020** — Form validation prominence (4-8h)
20. **TD-FE-021** — Blog responsive (2-4h)
21. **TD-FE-052** — SWR invalidation (4-8h)
22. **TD-FE-053** — Skeleton CLS (2-4h)

### Tier 4 — Strategic (P3, ~50-90h)

23. **TD-FE-007** — RSC opportunistic migration (40-56h)
24. **TD-FE-010** — i18n (deferred)
25. **TD-FE-030, 031, 032** — Polish

---

## Effort Total

- **Frontend tier 1 (P0)**: ~12-24h
- **Frontend tier 2 (P1)**: ~50-80h
- **Frontend tier 3 (P2)**: ~30-50h
- **Frontend tier 4 (P3)**: ~50-90h (deferable)
- **Total Frontend**: ~140-240h (3-6 sprints solo dev)

---

**Status**: ✅ Review completo. Handoff para Phase 7 (@qa).
