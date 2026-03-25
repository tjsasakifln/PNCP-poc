# UX-421 — Paginação Exibida com Poucos Resultados

**Status:** Draft
**Severity:** MEDIUM
**Origin:** Auditoria UX Playwright 25/03/2026
**Agent:** @ux-design-expert (Uma)

## Problema

Com apenas 2 resultados, a UI exibe dropdown "Por página: 50" e "Exibindo 1-2 de 2 oportunidades" duplicado (topo e base dos resultados). Paginação com opções 10/20/50 para 2 itens parece absurdo.

## Acceptance Criteria

- [ ] AC1: Esconder paginação completa quando total de resultados <= itens por página
- [ ] AC2: Mostrar apenas contagem simples ("2 oportunidades") sem controles de paginação
- [ ] AC3: Se > 10 resultados, mostrar paginação com default 10/página (não 50)
- [ ] AC4: Remover paginação duplicada (manter apenas no topo OU na base, não ambos)
