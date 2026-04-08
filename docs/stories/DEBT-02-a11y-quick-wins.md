# DEBT-02: Accessibility Quick Wins

**Epic:** EPIC-TD-2026
**Fase:** 1 (Quick Wins)
**Horas:** 2h
**Agente:** @dev
**Prioridade:** P1

## Debitos Cobertos

| TD | Item | Horas |
|----|------|-------|
| TD-052 | FeedbackButtons touch target 28px -> 44px (WCAG 2.5.5) | 1.5h |
| TD-053 | CompatibilityBadge text-[10px] -> text-xs (min 12px) | 0.5h |

## Acceptance Criteria

- [x] AC1: FeedbackButtons min-w-[44px] min-h-[44px] em todos os breakpoints
- [x] AC2: CompatibilityBadge usa text-xs (12px) no minimo
- [x] AC3: Testes existentes continuam passando (9+41 = 50 testes, 0 falhas)
- [x] AC4: Visual review em mobile (375px) — min-w/min-h garantem 44px em qualquer breakpoint
