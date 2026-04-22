# EPIC-MON-DIST-2026-04: Extras de Distribuição e Empacotamento de Dados

**Priority:** P2 — Wave 3
**Status:** Draft
**Owner:** @pm + @architect + @dev + @devops
**Sprint:** Wave 3 (paralelo com EPIC-MON-SEO)
**Meta:** Amplificar alcance via 2 canais não convencionais — data licensing one-shot e white-label para consultorias.

---

## Contexto Estratégico

O SmartLic hoje vende majoritariamente direto para o **end-user** (empresa B2G). Dois canais sub-explorados:

### Data Licensing / Bulk Export (one-shot enterprise)
- Compradores: consultorias McKinsey/BCG, universidades, think tanks, M&A advisors, agências de rating
- Demanda: dataset temático em CSV/JSON/Parquet para análise offline
- Ticket: R$ 2.997–49.997 one-shot (sem ciclo de venda longo)
- Ex: "Construção Civil SP 2020-2025" (500k contratos, R$ 9.997)

### White-label para Consultorias de Licitação
- Canal: ~15% das empresas B2G usam consultoria especializada — mercado paralelo massivo
- Modelo: consultoria revende relatórios/monitores com marca própria + Stripe Connect revshare
- Vantagem: consultoria tem carteira de clientes; nós ganhamos distribuição + receita recorrente escalável

---

## Stories do Epic

| Story | Priority | Effort | Squad | Status | Objetivo |
|-------|:--------:|:------:|-------|:------:|----------|
| MON-DIST-01 | P2 | L | @dev + @devops | Draft | Data Licensing / Bulk Export (pacotes one-shot) |
| MON-DIST-02 | P2 | XL | @dev + @architect | Draft | White-label para Consultorias (Stripe Connect + branding) |

---

## Ordem de Execução

1. **MON-DIST-01** primeiro (menor esforço, reutiliza MON-REP-01 para checkout)
2. **MON-DIST-02** depois (requer MON-SUB-01 para revshare em add-ons recorrentes; integração Stripe Connect é complexa)

---

## KPIs do Epic

| KPI | Meta 90 dias | Meta 180 dias |
|-----|--------------|---------------|
| Pacotes de dados vendidos | 3 | 30 |
| Receita data licensing | R$ 15.000 | R$ 250.000 |
| Parceiros consultoria onboarded | 3 | 15 |
| GMV via white-label | R$ 5.000 | R$ 60.000 |
| Revshare a parceiros | R$ 2.500 | R$ 30.000 |

---

## Dependências

- **Bloqueado por:**
  - MON-REP-01 → MON-DIST-01 (checkout one-shot)
  - MON-REP-01 + MON-SUB-01 → MON-DIST-02 (checkout + add-ons)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Epic criado — extras de distribuição (não estavam nas 4 camadas originais) |
