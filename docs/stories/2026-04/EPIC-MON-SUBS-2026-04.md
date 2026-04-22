# EPIC-MON-SUBS-2026-04: Camada 3 — Assinaturas de Inteligência (MRR)

**Priority:** P1 — Wave 2
**Status:** Draft
**Owner:** @pm + @architect + @dev + @qa
**Sprint:** Wave 2 (após Wave 1 foundation estabilizada)
**Meta:** MRR R$ 147–997/mês via 3 add-ons sobre a infra de subscription existente.

---

## Contexto Estratégico

Hoje o SmartLic tem único plano recorrente (SmartLic Pro R$ 397–997/mês via `plan_billing_periods`). Não há noção de **add-ons vendáveis separados do plano base**. A tabela `alerts` suporta monitoramento por filtros genéricos (STORY-301, STORY-315) mas não há produtos empacotados + precificados.

**Produtos planejados:**

| Produto | Preço | Cadência | Uso |
|---------|-------|----------|-----|
| Monitor de Segmento por UF | R$ 197–497/mês | Semanal ou Mensal | Empresa operando em 1-3 segmentos |
| Monitor de Órgão Contratante | R$ 147–397/mês | Mensal | Quem vende recorrente para 1 órgão |
| Radar de Risco de Fornecedor | R$ 297–997/mês/carteira | Diário (alerta em tempo real) | Bancos/fintechs com exposição PME B2G |

Modelo **add-on standalone ou over-plan** — usuário pode assinar sem ter Smartlic Pro base (melhor DAU fintech), ou como add-on sobre Pro (melhor upsell).

---

## Stories do Epic

| Story | Priority | Effort | Squad | Status | Objetivo |
|-------|:--------:|:------:|-------|:------:|----------|
| MON-SUB-01 | P0 | M | @dev | Draft | Add-ons Stripe + schema `monitored_subscriptions` + watchlists |
| MON-SUB-02 | P1 | L | @dev | Draft | Monitor de Segmento por UF (R$ 197–497/mês) |
| MON-SUB-03 | P1 | M | @dev | Draft | Monitor de Órgão Contratante (R$ 147–397/mês) |
| MON-SUB-04 | P1 | L | @dev | Draft | Radar de Risco de Fornecedor (R$ 297–997/mês/carteira) |

---

## Ordem de Execução

1. **MON-SUB-01** (foundation, bloqueia as 3 subsequentes)
2. **MON-SUB-02** (não depende de MON-SCH-*)
3. **MON-SUB-03** (depende de MON-SCH-01 aditivos)
4. **MON-SUB-04** (depende de MON-SCH-01, maior esforço)

---

## KPIs do Epic

| KPI | Meta 60 dias | Meta 180 dias |
|-----|--------------|---------------|
| Assinaturas ativas add-ons | 20 | 200 |
| MRR add-ons | R$ 5.000 | R$ 80.000 |
| Churn mensal add-ons | <10% | <5% |
| ARPU add-on | R$ 250 | R$ 400 |
| % clientes multi-add-on | 10% | 30% |

---

## Dependências

- **Bloqueia:** MON-AI-02 (Copilot add-on), MON-AI-03 (Radar Preditivo add-on), MON-DIST-02 (White-label)
- **Bloqueado por:** MON-SCH-01 (aditivos) → MON-SUB-03 e MON-SUB-04

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Epic criado — Camada 3 da estratégia de monetização; MRR target R$ 80k/mês em 6 meses |
