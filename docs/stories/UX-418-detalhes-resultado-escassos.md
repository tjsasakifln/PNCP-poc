# UX-418 — Detalhes Expandidos do Resultado São Muito Escassos

**Status:** Draft
**Severity:** HIGH
**Origin:** Auditoria UX Playwright 25/03/2026
**Agent:** @ux-design-expert (Uma)

## Problema

Ao expandir "Ver detalhes" de uma licitação, aparecem apenas 3 campos:
- Órgão: Município de Schroeder
- Modalidade: Concorrência
- Propostas desde: 11/03/2026
- Badge "Validado por IA"

Falta informação crítica para decisão: número do processo, CNPJ do órgão, link para edital PDF, prazo exato de encerramento, itens/lotes, critério de julgamento, exigências de habilitação.

## Impacto

Usuário precisa clicar "Ver edital" (link externo) para obter informações básicas. Perde o valor de ter tudo consolidado no SmartLic.

## Acceptance Criteria

- [ ] AC1: Detalhes expandidos incluem: número do processo/edital, CNPJ do órgão
- [ ] AC2: Data/hora exata de encerramento de propostas (não só "Último dia")
- [ ] AC3: Critério de julgamento (menor preço, técnica e preço, etc.)
- [ ] AC4: Link direto para edital PDF quando disponível na API
- [ ] AC5: Quantidade de itens/lotes (se disponível)
- [ ] AC6: Fonte do dado (PNCP, PCP, ComprasGov) visível nos detalhes
- [ ] AC7: Campos com dados da API PNCP que já estão disponíveis no backend mas não são exibidos
