# Story UX-311: Estimativa de Tempo Realista (Calibração)

**Epic:** EPIC-UX-PREMIUM-2026-02
**Priority:** 🟠 P1
**Story Points:** 5 SP
**Owner:** @dev

## Problem
Estimativa "~1m restantes" quando já passou 2min. Completamente errada.

## Acceptance Criteria
- [ ] Calibração baseada em histórico real (não hardcoded)
- [ ] Fórmula: tempo_restante = (tempo_decorrido / progresso_atual) * (100 - progresso_atual)
- [ ] Margem de erro +/- 20% mostrada
- [ ] Atualização a cada 5s (não a cada render)
- [ ] Depois de 90s, mostra "Pode levar mais alguns minutos" (não estimativa falsa)

**Files:** `hooks/useSearchProgress.ts`, `components/LoadingProgress.tsx`
