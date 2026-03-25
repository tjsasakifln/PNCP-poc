# UX-416 — Dashboard: Skeleton Loading Infinito Antes do Erro

**Status:** Draft
**Severity:** HIGH
**Origin:** Auditoria UX Playwright 25/03/2026
**Agent:** @ux-design-expert (Uma)

## Problema

Dashboard exibe skeleton placeholders por ~5s e depois colapsa para "Dados temporariamente indisponíveis" com botão "Tentar novamente". Quando carrega brevemente (antes do erro final), os dados são úteis (54 análises, R$ 31,2 bi descobertos, 108h economizadas).

## Impacto

- Abordagem tudo-ou-nada: se 1 endpoint falha, toda a página vira erro
- Skeletons não indicam o que cada card será (métricas? gráficos? alertas?)
- Dados parciais poderiam ser mostrados mesmo com falha parcial

## Acceptance Criteria

- [ ] AC1: Dashboard renderiza componentes independentemente — se analytics falha, gráficos mostram erro mas cards de métricas ainda aparecem
- [ ] AC2: Cada seção tem seu próprio estado de erro inline (não colapsa a página inteira)
- [ ] AC3: Skeletons com labels ("Análises", "Oportunidades", etc.) para indicar o que vai carregar
- [ ] AC4: Timeout de skeleton: se não carregou em 10s, mostrar estado vazio com "retry" por seção
- [ ] AC5: Dados que carregaram com sucesso persistem visíveis mesmo quando "Tentar novamente" é clicado para seções falhadas
