# Story UX-320: Cleanup Console Errors (Lighthouse)

**Epic:** EPIC-UX-PREMIUM-2026-02
**Priority:** 🟡 P2
**Story Points:** 3 SP
**Owner:** @dev

## Problem
Console cheio de warnings/errors impacta Lighthouse score.

## Errors Identificados
- [ERROR] Failed to load resource: 524
- [WARNING] Input elements should have autocomplete
- [WARNING] Resource preloaded but not used

## Acceptance Criteria
- [ ] Adicionar autocomplete attributes em todos os inputs
- [ ] Remover preloads não-usados (Next.js config)
- [ ] Try-catch em fetch com erro silencioso (não console.error)
- [ ] Lighthouse Performance score >90
- [ ] Zero errors no console em produção

**Files:** `app/buscar/page.tsx`, `app/conta/page.tsx`, `next.config.js`
