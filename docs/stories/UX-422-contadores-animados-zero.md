# UX-422 — Contadores Animados na Landing Mostram "0" Sem Scroll

**Status:** Draft
**Severity:** MEDIUM
**Origin:** Auditoria UX Playwright 25/03/2026
**Agent:** @ux-design-expert (Uma)

## Problema

Seção "Impacto real no mercado de licitações" na landing exibe "0 setores especializados", "0+ regras de filtragem", "0 estados cobertos" quando o IntersectionObserver não dispara (viewport não atinge threshold, ou em screenshots full-page).

## Acceptance Criteria

- [ ] AC1: Contadores iniciam com valor final (não zero) e animam apenas se IntersectionObserver dispara
- [ ] AC2: Fallback: se IntersectionObserver não disponível, mostrar valores finais estáticos
- [ ] AC3: Verificar que SSR/prerender mostra valores reais (não zeros) para SEO
