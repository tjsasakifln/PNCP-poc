# EPIC-MON-REPORTS-2026-04: Camada 2 — Relatórios Avulsos Monetizados

**Priority:** P1 — Wave 1 Fast-Revenue
**Status:** Draft
**Owner:** @pm (Morgan) + @architect + @dev + @qa + @devops
**Sprint:** Wave 1 (paralelo com EPIC-MON-API)
**Meta:** Gerar receita one-shot R$ 47–697/transação via 4 tipos de relatório auto-gerados por Stripe + LLM + email.

---

## Contexto Estratégico

Hoje o SmartLic possui infraestrutura de PDF apenas para 1 tipo de relatório (diagnóstico via `backend/pdf_report.py` com reportlab) e Stripe configurado exclusivamente para assinaturas recorrentes (`mode=subscription`). Faltam:

- Fluxo de **pagamento único** (`mode=payment`) com tabela `purchases` e webhook `charge.succeeded`
- Pipeline de **geração assíncrona + entrega por email** (tabela `generated_reports`, storage, template `report_ready`)
- 4 **tipos de relatório** de alto valor percebido:

| Produto | Ticket | Personas |
|---------|--------|----------|
| Fornecedor por CNPJ | R$ 47–197 | Advogados, bancos, construtoras pesquisando concorrente |
| Preço de Referência | R$ 97–297 | Fiscais de contrato, orçamentistas, pregoeiros |
| Mapeamento de Concorrência | R$ 197–497 | Construtoras, consultorias, M&A advisors |
| Due Diligence Express (lite v1) | R$ 297–697 | Bancos, fintechs de crédito PME |

Todas as 4 são geradas **automaticamente** (sem ciclo de venda humana) — compra → geração em <5 min → entrega por email com link.

---

## Stories do Epic

| Story | Priority | Effort | Squad | Status | Objetivo |
|-------|:--------:|:------:|-------|:------:|----------|
| MON-REP-01 | P0 | M | @dev | Draft | Stripe one-time + tabela `purchases` + webhook |
| MON-REP-02 | P0 | M | @dev | Draft | Infra `generated_reports` + email delivery + storage |
| MON-REP-03 | P1 | L | @dev + @ux | Draft | Relatório Fornecedor por CNPJ (R$ 47–197) |
| MON-REP-04 | P1 | L | @dev | Draft | Relatório Preço de Referência (R$ 97–297) |
| MON-REP-05 | P1 | L | @dev | Draft | Relatório Mapeamento de Concorrência (R$ 197–497) |
| MON-REP-06 | P1 | L | @dev | Draft | Due Diligence Express lite (R$ 297–697) |

---

## Ordem de Execução

1. **MON-REP-01 + MON-REP-02** em paralelo (foundation, bloqueiam todas as outras)
2. Após MON-REP-02: **MON-REP-03 + MON-REP-05** em paralelo (não dependem de MON-SCH-*)
3. Após MON-SCH-02: **MON-REP-04**
4. Após MON-SCH-01 + MON-SCH-02: **MON-REP-06**

---

## KPIs do Epic

| KPI | Meta 30 dias | Meta 90 dias |
|-----|-------------|--------------|
| Volume de compras one-shot/mês | 10 | 100 |
| Receita one-shot/mês | R$ 1.500 | R$ 20.000 |
| Tempo compra→entrega (p95) | <5 min | <3 min |
| Taxa de refund | <5% | <2% |
| NPS do relatório | N/A | >40 |

---

## Dependências

- **Bloqueia:** MON-DIST-01 (Data Licensing reutiliza MON-REP-01 para checkout)
- **Bloqueado por:**
  - MON-SCH-02 (CATMAT) → MON-REP-04
  - MON-SCH-01 (aditivos) + MON-SCH-02 → MON-REP-06

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Epic criado — Camada 2 da estratégia de monetização dataset 2M+ contratos |
