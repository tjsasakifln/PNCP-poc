# MON-SEO-01: Enriquecer `/fornecedores/[cnpj]` com Score de Risco + Aditivos + CTAs Pagos

**Priority:** P1
**Effort:** M (3-4 dias)
**Squad:** @dev + @ux-design-expert
**Status:** Draft
**Epic:** [EPIC-MON-SEO-2026-04](EPIC-MON-SEO-2026-04.md)
**Sprint:** Wave 3 (depende MON-SCH-01 + MON-REP-03 + MON-SUB-04)

---

## Contexto

Página `/fornecedores/[cnpj]` já existe (ISR 24h). Hoje mostra:
- Dados básicos (razão social, endereço)
- Lista de contratos recentes
- Top compradores (órgãos)

**Falta:** elementos que transformem a página em **funil de conversão**:
- Score de risco (do `supplier_risk_summary_mv` criado em MON-SCH-01)
- Índice de aditivos (% contratos aditados)
- 3 CTAs claros para produtos pagos:
  1. "Comprar relatório completo" (R$ 47+) → MON-REP-03
  2. "Monitorar este fornecedor em minha carteira" (R$ 297/mês) → MON-SUB-04
  3. "Consultar via API" (R$ 0,50/query) → MON-API-03 com link para `/api`

---

## Acceptance Criteria

### AC1: Componente `SupplierRiskScore`

- [ ] `frontend/app/components/SupplierRiskScore.tsx`:
  - Score numeral 0-100 (grande, destacado)
  - Gauge ou bar chart visual
  - Label ("Baixo risco", "Moderado", "Alto risco", "Atenção")
  - Breakdown: aditivos %, concentração %, volatilidade
  - Disclaimer pequeno "Score derivado de dados públicos"
- [ ] Dados vêm do view `supplier_risk_summary_mv` via endpoint `GET /v1/suppliers/{cnpj}/risk-summary`

### AC2: Componente `AdditivesIndex`

- [ ] `frontend/app/components/AdditivesIndex.tsx`:
  - "X% dos contratos sofreram aditivos" (percentual)
  - Bar chart por ano: aditivos por vencimento
  - Link expansível "Ver últimos 5 aditivos"

### AC3: Componente `ConversionCTAs`

- [ ] `frontend/app/components/supplier/ConversionCTAs.tsx`:
  - 3 cards lado-a-lado (mobile: stack):
    - **Relatório completo** — R$ 47-197 (3 tiers) → redirect `/relatorios/fornecedor/{cnpj}`
    - **Monitor de Risco** — R$ 297/mês/carteira → redirect `/conta/monitores/novo?type=radar_risco&watch={cnpj}`
    - **API de Dados** — R$ 0,50/query → redirect `/api`
  - A/B test placement (sidebar vs inline vs sticky bottom) via feature flag
- [ ] Event tracking Mixpanel: `cta_view`, `cta_click` por tipo

### AC4: Enriquecer `page.tsx`

- [ ] `frontend/app/fornecedores/[cnpj]/page.tsx`:
  - Adicionar seções (order): hero → SupplierRiskScore → AdditivesIndex → ConversionCTAs → contratos → top órgãos
  - Sticky right sidebar com CTA principal em desktop (visibility >= 50% do scroll)
  - ISR 24h (atual), refresh trigger on-demand via revalidateTag

### AC5: JSON-LD schemas

- [ ] Schema `Organization` com:
  - `@type: "Organization"`
  - `identifier: {@type: "PropertyValue", propertyID: "CNPJ", value: "..."}`
  - `address`, `foundingDate` (se disponível)
- [ ] Schema `ProfilePage` wrapping
- [ ] Schema `AggregateRating` usando métricas: `ratingValue` (inverso do score de risco, ex: 100 - score_risco), `reviewCount` (total_contratos)

### AC6: SEO meta tags

- [ ] Title: `"{nome} — CNPJ {cnpj} | Histórico de Contratos Públicos | SmartLic"` (max 60)
- [ ] Description: `"Histórico completo de contratos públicos de {nome}. {total_contratos} contratos, R$ {total_valor} em valor. Score de risco, aditivos, órgãos contratantes."` (max 160)
- [ ] og:image dinâmico: card gerado via `@vercel/og` com score + total contratos

### AC7: Testes

- [ ] Unit: `frontend/__tests__/components/SupplierRiskScore.test.tsx`
- [ ] Snapshot: page renderiza com dados mockados
- [ ] E2E Playwright: user navega → vê score → clica CTA → vai para landing de compra

---

## Scope

**IN:**
- 3 novos componentes
- Enriquecer page
- JSON-LD schemas
- SEO metadata + og:image
- A/B test infra (feature flag)
- Testes

**OUT:**
- Dashboard de fornecedor logado (parte de /conta)
- Filtros de "contratos ativos hoje" — requer MON-SCH-03 (pode vir depois)
- Integração com dados Receita Federal — v2

---

## Dependências

- **MON-SCH-01** (aditivos + risk summary view)
- MON-REP-03 (para CTA funcionar)
- MON-SUB-04 (para CTA do monitor)

---

## Riscos

- **Score de risco pode ofender fornecedor:** disclaimer robusto; link "Contestar dados"; revisar base legal LGPD
- **Fornecedor com score alto de risco processando judicial:** mitigação comunicacional — score é sinal, não diagnóstico; cada contrato específico pode ter contexto
- **Coverage aditivos < 50%:** score com confiança baixa → exibir "baseado em dados parciais" com contador "X/Y contratos analisados"

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `frontend/app/fornecedores/[cnpj]/page.tsx` (estender)
- `frontend/app/components/SupplierRiskScore.tsx` (novo)
- `frontend/app/components/AdditivesIndex.tsx` (novo)
- `frontend/app/components/supplier/ConversionCTAs.tsx` (novo)
- `backend/routes/suppliers_risk.py` (novo endpoint risk-summary)
- `frontend/app/api/og/supplier/route.tsx` (og:image dinâmico)
- `frontend/__tests__/components/SupplierRiskScore.test.tsx` (novo)

---

## Definition of Done

- [ ] Página live com 3 componentes funcionais
- [ ] JSON-LD valida em Google Rich Results Test
- [ ] A/B test rodando em 3 variantes de CTA placement
- [ ] Mixpanel tracking confirmado
- [ ] Lighthouse score >= 85
- [ ] Testes passando

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — funil de conversão da Camada 1 |
