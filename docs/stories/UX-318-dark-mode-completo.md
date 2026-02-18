# Story UX-318: Dark Mode Completo (Cores Adaptativas)

**Epic:** EPIC-UX-PREMIUM-2026-02
**Priority:** 🟡 P2
**Story Points:** 8 SP
**Owner:** @dev

## Problem
Toggle dark mode existe mas cores não adaptam corretamente. Muitos elementos ficam ilegíveis.

## Acceptance Criteria
- [ ] Auditoria completa de todas as cores
- [ ] Tailwind dark: variants em todos os componentes
- [ ] Contraste WCAG AA em ambos os modos
- [ ] Imagens com filter invert() quando apropriado
- [ ] Persistência em localStorage
- [ ] Transição suave entre modos (300ms)

**Files:** `tailwind.config.js`, `app/globals.css`, todos os componentes
