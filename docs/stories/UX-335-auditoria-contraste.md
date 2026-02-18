# Story UX-335: Auditoria de Contraste WCAG AA
**Epic:** EPIC-UX-PREMIUM-2026-02 | **Priority:** 🟡 P2
**Story Points:** 5 SP
**Owner:** @dev + @ux

## Problem
Contraste insuficiente em vários elementos. WCAG AA requer 4.5:1 para texto normal.

## Acceptance Criteria
- [ ] Auditoria com WebAIM Contrast Checker
- [ ] Ajustar cores que não passam (cinza claro em branco, etc.)
- [ ] Lighthouse Accessibility score >95
- [ ] Testes automatizados de contraste (jest-axe)

**Files:** `tailwind.config.js`, `app/globals.css`, review global
