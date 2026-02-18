# Story UX-309: Fix Estados "Aguardando..." Indefinidamente

**Epic:** EPIC-UX-PREMIUM-2026-02
**Priority:** 🟠 P1
**Story Points:** 5 SP
**Owner:** @dev

## Problem
Cards de UF ficam congelados em "Aguardando..." mesmo após busca falhar/completar.

## Acceptance Criteria
- [ ] Timeout por UF após 120s
- [ ] Estado de erro individual por UF (não global)
- [ ] Tooltip mostrando erro específico
- [ ] Retry individual por UF
- [ ] Visual: "Aguardando" → "Erro" → "Concluído"

**Files:** `components/UFProgressCard.tsx`, `app/buscar/page.tsx`
