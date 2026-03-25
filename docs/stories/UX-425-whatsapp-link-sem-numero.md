# UX-425 — WhatsApp Link na Página de Planos Sem Número de Telefone

**Status:** Done
**Severity:** LOW
**Origin:** Auditoria UX Playwright 25/03/2026
**Agent:** @ux-design-expert (Uma)

## Problema

Link "Fale conosco" na página /planos aponta para `wa.me/?text=Olá! Gostaria de saber mais sobre o SmartLic Pro.` — sem número de telefone. Abre WhatsApp sem destinatário.

## Acceptance Criteria

- [x] AC1: Link WhatsApp inclui número comercial válido: `wa.me/55XXXXXXXXXXX?text=...`
- [x] AC2: Testar que link abre conversa correta no WhatsApp Web e mobile
