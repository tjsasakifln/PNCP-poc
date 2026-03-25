# UX-417 — Filtros Críticos Escondidos em Accordion Colapsado

**Status:** Done
**Severity:** HIGH
**Origin:** Auditoria UX Playwright 25/03/2026
**Agent:** @ux-design-expert (Uma)

## Problema

Filtros essenciais (UFs, modalidade, valor) estão atrás de "Personalizar análise" colapsado. O resumo "São Paulo • Abertas • Oportunidades recentes" é discreto e não editável por clique direto. Usuário pode buscar sem perceber que está filtrando apenas 1 estado.

## Impacto

Usuários novos fazem busca com filtros default (1 UF, 10 dias) e recebem poucos resultados. Não percebem que podem expandir para selecionar mais estados.

## Acceptance Criteria

- [x] AC1: Seleção de UFs visível por padrão (fora do accordion) — é o filtro mais impactante
- [x] AC2: Resumo de filtros ativos clicável — ao clicar em "São Paulo" abre direto o seletor de UFs
- [x] AC3: Se apenas 1 UF selecionada, mostrar hint: "Selecione mais estados para ampliar resultados"
- [x] AC4: Primeiro acesso: accordion aberto por padrão (fechar só após primeira busca bem-sucedida)
- [x] AC5: Manter accordion colapsável para usuários recorrentes que já configuraram filtros
