# EPIC-MON-API-2026-04: Camada 4 — API de Dados B2B Monetizada

**Priority:** P1 — Wave 1 Fast-Revenue
**Status:** Draft
**Owner:** @architect + @dev + @devops + @qa
**Sprint:** Wave 1 (paralelo com EPIC-MON-REPORTS)
**Meta:** Receita B2B pay-per-call R$ 0,50–10/consulta via 3 endpoints + distribuição RapidAPI.

---

## Contexto Estratégico

Hoje a única forma de auth no backend é JWT Supabase (não serve bem B2B). Não existe tabela `api_keys`, middleware `X-API-Key`, nem metered billing (`stripe.UsageRecord`). A STORY-434 (Draft, P2) planeja API GRATUITA sobre licitações ativas — **este epic é diferente**: monetização pay-per-call sobre o dataset de 2M contratos históricos.

**Compradores-alvo:** fintechs, plataformas de compliance, ERPs, sistemas de orçamentação, sites de due diligence, integradores que consomem dado bruto.

**Endpoints:**

| Endpoint | Preço | Use Case |
|----------|-------|----------|
| `GET /api/v1/supplier/{cnpj}/history` | R$ 0,50–2 / query | Histórico consolidado por CNPJ |
| `GET /api/v1/benchmark/price` | R$ 1–5 / query | Distribuição estatística CATMAT/CATSER + UF |
| `GET /api/v1/supplier/{cnpj}/score` *(Q3)* | R$ 2–10 / query | Score modelado capacidade/risco |

**Distribuição:**
- Endpoint direto (clientes enterprise)
- RapidAPI marketplace (DA 91) para descoberta + backlinks

---

## Stories do Epic

| Story | Priority | Effort | Squad | Status | Objetivo |
|-------|:--------:|:------:|-------|:------:|----------|
| MON-API-01 | P0 | M | @dev | Draft | API Key Management (tabela + middleware X-API-Key) |
| MON-API-02 | P0 | L | @dev + @devops | Draft | Metered Billing (Stripe UsageRecord + audit trail) |
| MON-API-03 | P1 | M | @dev | Draft | `GET /api/v1/supplier/{cnpj}/history` |
| MON-API-04 | P1 | M | @dev | Draft | `GET /api/v1/benchmark/price` |
| MON-API-05 | P1 | M | @dev + @devops | Draft | Distribuição RapidAPI + landing `/api` + docs público |
| MON-API-06 *(FUTURE Q3)* | P2 | L | @data-engineer + @dev | Backlog | `GET /api/v1/supplier/{cnpj}/score` (requer modelo ML) |

---

## Ordem de Execução

1. **MON-API-01** (sprint 1, bloqueia todas)
2. **MON-API-02** (sprint 2, depende de MON-API-01)
3. **MON-API-03** paralelo com **MON-API-04** (MON-API-04 depende também de MON-SCH-02 CATMAT)
4. **MON-API-05** por último (precisa dos endpoints para docs/demo)
5. MON-API-06 em backlog Q3

---

## KPIs do Epic

| KPI | Meta 30 dias | Meta 90 dias |
|-----|-------------|--------------|
| Clientes B2B ativos | 2 | 15 |
| Queries/mês | 5.000 | 50.000 |
| Receita API/mês | R$ 300 | R$ 5.000 |
| p95 latência | <500ms | <300ms |
| Uptime | 99.5% | 99.9% |
| Listagem RapidAPI | Pending | Live + 100 subscribers |

---

## Dependências

- **Bloqueia:** STORY-434 (API pública gratuita) deve reutilizar middleware `X-API-Key` criado em MON-API-01
- **Bloqueado por:**
  - MON-SCH-02 (CATMAT) → MON-API-04
- **Integra com:** MON-AI-01 (Semantic Search usa mesma infra de API key + metered billing)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Epic criado — Camada 4 da estratégia de monetização; complementa (não sobrepõe) STORY-434 |
