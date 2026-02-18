# Story UX-317: Fix Links Quebrados no Footer

**Epic:** EPIC-UX-PREMIUM-2026-02
**Priority:** 🟠 P1
**Story Points:** 5 SP
**Owner:** @dev

## Problem
- "Central de Ajuda" → /mensagens (deveria ser /ajuda)
- "Contato" → /mensagens (deveria ter formulário)
- "Atalhos de Teclado" → não implementado

## Acceptance Criteria
- [ ] Criar página /ajuda com FAQ
- [ ] Criar página /contato com formulário
- [ ] Modal de atalhos de teclado (Ctrl+K, Ctrl+S, Esc)
- [ ] Atualizar todos os links do footer
- [ ] 404 page para rotas inválidas

**Files:** `app/ajuda/page.tsx`, `app/contato/page.tsx`, `components/KeyboardShortcutsModal.tsx`, `components/Footer.tsx`
