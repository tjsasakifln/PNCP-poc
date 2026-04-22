# MON-SEO-03: Enriquecer `/orgaos/[slug]` com Perfil de Compras + CTAs

**Priority:** P2
**Effort:** M (3 dias)
**Squad:** @dev
**Status:** Draft
**Epic:** [EPIC-MON-SEO-2026-04](EPIC-MON-SEO-2026-04.md)
**Sprint:** Wave 3 (depende MON-SCH-01 + MON-SUB-03)

---

## Contexto

Página `/orgaos/[slug]` já existe (básica). Falta transformar em hub de conversão para persona "fornecedor que quer vender para este órgão":

**Valor novo:**
- Perfil de compras recente (últimos 90 dias)
- Top 10 fornecedores que o órgão compra
- **Aditivos recentes** (alerta para fornecedor atento — se órgão aditou, pode haver renovação em breve)
- Evolução de gastos por ano/categoria
- CTA para Monitor de Órgão (MON-SUB-03) + API

---

## Acceptance Criteria

### AC1: Componentes novos

- [ ] `OrgTopSuppliers` — tabela top 10 com valor contratado + share
- [ ] `OrgAdditivesFeed` — timeline aditivos últimos 90d
- [ ] `OrgSpendEvolution` — line chart gastos 24 meses por CATMAT principal
- [ ] `OrgCTAs` — 3 cards (Monitor R$ 147/mês, Relatório Fornecedor dos top 10, API)

### AC2: Enriquecer page.tsx

- [ ] `frontend/app/orgaos/[slug]/page.tsx` estende seções
- [ ] ISR 24h

### AC3: JSON-LD `GovernmentOrganization`

- [ ] Schema:
```json
{"@type": "GovernmentOrganization", "identifier": {...}, "address": {...}}
```

### AC4: SEO metadata

- [ ] Title: `"{nome_orgao} — Compras Públicas | SmartLic"` (max 60)
- [ ] Description: `"{nome_orgao} contratou R$ {total} em {periodo} com {n} fornecedores. Análise de compras, aditivos, fornecedores principais."` (max 160)

### AC5: Testes

- [ ] Snapshot da página com órgão real
- [ ] E2E Playwright: user visita → vê perfil → clica Monitor CTA → chega em wizard de criação

---

## Scope

**IN:** 4 componentes novos, JSON-LD, SEO, testes
**OUT:** Dashboard interativo completo (isso é o que MON-SUB-03 entrega para quem paga)

---

## Dependências

- **MON-SCH-01 (aditivos)** — bloqueador
- MON-SUB-03 (para CTA funcionar)

---

## Riscos

- **Órgão com poucos dados:** mostrar "Baixa atividade recente" quando volume <10 contratos/ano

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `frontend/app/orgaos/[slug]/page.tsx` (estender)
- `frontend/app/components/org/OrgTopSuppliers.tsx` (novo)
- `frontend/app/components/org/OrgAdditivesFeed.tsx` (novo)
- `frontend/app/components/org/OrgSpendEvolution.tsx` (novo)
- `frontend/app/components/org/OrgCTAs.tsx` (novo)
- `backend/routes/orgao_profile.py` (novo ou estender)

---

## Definition of Done

- [ ] Página enriquecida live
- [ ] JSON-LD válido
- [ ] Lighthouse 85+
- [ ] 2 A/B test variants de CTA
- [ ] Testes passando

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — página existente vira hub de conversão |
