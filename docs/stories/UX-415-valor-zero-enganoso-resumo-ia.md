# UX-415 — "R$ 0" no Resumo IA é Enganoso Quando Valor Não Foi Informado

**Status:** Draft
**Severity:** HIGH
**Origin:** Auditoria UX Playwright 25/03/2026
**Agent:** @ux-design-expert (Uma)

## Problema

Resultados mostram "Valor não informado" nos cards, mas o Resumo por IA exibe "R$ 0 valor total". Isso é semanticamente errado — não é zero, é desconhecido. O resumo textual da IA diz "Maior valor: Não especificado" mas o número grande "R$ 0" contradiz.

## Impacto

Usuário pode interpretar como licitações sem valor, reduzindo interesse. Inconsistência entre card e resumo gera desconfiança.

## Acceptance Criteria

- [ ] AC1: Resumo IA exibe "Valor não divulgado" em vez de "R$ 0" quando nenhum resultado tem valor
- [ ] AC2: Métrica grande no resumo mostra "—" ou "N/D" em vez de "R$ 0" quando valor é desconhecido
- [ ] AC3: Cards mantêm "Valor não informado" (está correto)
- [ ] AC4: Prompt da IA recebe instrução para diferenciar "sem valor informado" de "valor zero"
- [ ] AC5: Alerta "2 licitações encerram em 7 dias" deve considerar se licitação já encerrou (hoje É 25/03 e diz "Último dia: 25/03")
