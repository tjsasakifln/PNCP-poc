# MON-INDEX — Monetização do Dataset de 2M+ Contratos (Índice Consolidado)

**Created:** 2026-04-22
**Owner:** @sm (River)
**Status:** Draft
**Epic Super:** estratégia integrada de 7 epics / 27 stories + 1 future

---

## Visão Geral

Plano para transformar o dataset `pncp_supplier_contracts` (~2.1M contratos históricos) em 4 camadas de monetização + 2 blocos de estratégias extras validadas com o usuário em 2026-04-22.

**Priorização fast-revenue:** Wave 1 (Camadas 2+4) → Wave 2 (Camada 3 + IA/ML) → Wave 3 (Camada 1 + Distribuição).

---

## Epics + Stories

### Prereq — EPIC-MON-SCHEMA (3 stories)
Enriquecimento do schema `pncp_supplier_contracts` (aditivos, CATMAT/CATSER, data_fim).

| Story | Priority | Effort | Status |
|-------|:--------:|:------:|:------:|
| [MON-SCH-01](MON-SCH-01-aditivos-crawler-schema.md) | P0 | M | Draft |
| [MON-SCH-02](MON-SCH-02-catmat-catser-parsing.md) | P0 | M | Draft |
| [MON-SCH-03](MON-SCH-03-data-fim-vigencia-status.md) | P0 | S | Draft |

### Wave 1a — EPIC-MON-REPORTS (6 stories) — Camada 2
Relatórios avulsos, R$ 47–697 por venda via Stripe one-time + LLM + email.

| Story | Priority | Effort | Status |
|-------|:--------:|:------:|:------:|
| [MON-REP-01](MON-REP-01-stripe-one-time-purchases-webhook.md) | P0 | M | Draft |
| [MON-REP-02](MON-REP-02-generated-reports-delivery.md) | P0 | M | Draft |
| [MON-REP-03](MON-REP-03-relatorio-fornecedor-cnpj.md) | P1 | L | Draft |
| [MON-REP-04](MON-REP-04-relatorio-preco-referencia.md) | P1 | L | Draft |
| [MON-REP-05](MON-REP-05-relatorio-mapeamento-concorrencia.md) | P1 | L | Draft |
| [MON-REP-06](MON-REP-06-due-diligence-express-lite.md) | P1 | L | Draft |

### Wave 1b — EPIC-MON-API (5 stories + 1 future) — Camada 4
API B2B pay-per-call, R$ 0,50–10/consulta, distribuição RapidAPI.

| Story | Priority | Effort | Status |
|-------|:--------:|:------:|:------:|
| [MON-API-01](MON-API-01-api-key-management.md) | P0 | M | Draft |
| [MON-API-02](MON-API-02-stripe-metered-billing.md) | P0 | L | Draft |
| [MON-API-03](MON-API-03-supplier-history-endpoint.md) | P1 | M | Draft |
| [MON-API-04](MON-API-04-benchmark-price-endpoint.md) | P1 | M | Draft |
| [MON-API-05](MON-API-05-rapidapi-landing-public-docs.md) | P1 | M | Draft |
| [MON-API-06](MON-API-06-supplier-score-endpoint.future.md) | P2 | L | Future (Q3) |

### Wave 2a — EPIC-MON-SUBS (4 stories) — Camada 3
Assinaturas de inteligência recorrentes R$ 147–997/mês.

| Story | Priority | Effort | Status |
|-------|:--------:|:------:|:------:|
| [MON-SUB-01](MON-SUB-01-addons-stripe-monitored-subscriptions.md) | P0 | M | Draft |
| [MON-SUB-02](MON-SUB-02-monitor-segmento-uf.md) | P1 | L | Draft |
| [MON-SUB-03](MON-SUB-03-monitor-orgao-contratante.md) | P1 | M | Draft |
| [MON-SUB-04](MON-SUB-04-radar-risco-fornecedor.md) | P1 | L | Draft |

### Wave 2b — EPIC-MON-AI (3 stories) — Extras IA/ML
Moat tecnológico via produtos de IA treinados sobre dataset proprietário.

| Story | Priority | Effort | Status |
|-------|:--------:|:------:|:------:|
| [MON-AI-01](MON-AI-01-semantic-search-embeddings.md) | P0 | L | Draft |
| [MON-AI-02](MON-AI-02-ai-copilot-propostas.md) | P1 | XL | Draft |
| [MON-AI-03](MON-AI-03-radar-preditivo-editais.md) | P1 | XL | Draft |

### Wave 3a — EPIC-MON-SEO (5 stories) — Camada 1
SEO de entidade: funil orgânico gratuito para compradores das camadas pagas.

| Story | Priority | Effort | Status |
|-------|:--------:|:------:|:------:|
| [MON-SEO-01](MON-SEO-01-fornecedor-enriquecer-cta.md) | P1 | M | Draft |
| [MON-SEO-02](MON-SEO-02-categoria-programatica.md) | P1 | L | Draft |
| [MON-SEO-03](MON-SEO-03-orgao-enriquecer-cta.md) | P2 | M | Draft |
| [MON-SEO-04](MON-SEO-04-sitemaps-dinamicos-shards.md) | P0 | M | Draft |
| [MON-SEO-05](MON-SEO-05-schema-org-jsonld-entity-pages.md) | P2 | S | Draft |

### Wave 3b — EPIC-MON-DIST (2 stories) — Extras Distribuição
Canais enterprise e white-label.

| Story | Priority | Effort | Status |
|-------|:--------:|:------:|:------:|
| [MON-DIST-01](MON-DIST-01-data-licensing-bulk-export.md) | P2 | L | Draft |
| [MON-DIST-02](MON-DIST-02-white-label-consultorias.md) | P2 | XL | Draft |

---

## Dependências Cross-Epic

```
MON-SCH-01 (aditivos) ──┬──> MON-REP-06 (Due Diligence)
                         ├──> MON-SUB-03 (Monitor Órgão)
                         ├──> MON-SUB-04 (Radar Risco)
                         └──> MON-SEO-01 (score na pública)

MON-SCH-02 (CATMAT) ─────┬──> MON-REP-04 (Preço Referência)
                          ├──> MON-API-04 (benchmark endpoint)
                          ├──> MON-SEO-02 (páginas /categoria)
                          └──> MON-AI-03 (Radar Preditivo)

MON-REP-01 (one-time) ──┬──> MON-REP-02 → MON-REP-03/04/05/06
                         ├──> MON-AI-02 (Copilot one-shot)
                         └──> MON-DIST-01 (Data Licensing)

MON-API-01 (keys) ──> MON-API-02 → MON-API-03/04/05
                                 └──> MON-AI-01 (Semantic Search)

MON-SUB-01 (add-ons) ──┬──> MON-SUB-02/03/04
                        ├──> MON-AI-02 (Copilot add-on)
                        ├──> MON-AI-03 (Radar Preditivo add-on)
                        └──> MON-DIST-02 (White-label)

MON-AI-01 ──> MON-AI-02 (RAG depende de embeddings)
```

---

## Projeção de Receita

| Produto | Ticket | Volume Q3 | Volume Q4 | MRR/Rev Q4 |
|---------|--------|-----------|-----------|------------|
| Relatório Fornecedor | R$ 97 avg | 60/mês | 300/mês | R$ 29k/mês |
| Relatório Preço | R$ 197 avg | 20 | 100 | R$ 19.7k |
| Relatório Concorrência | R$ 347 avg | 10 | 50 | R$ 17.3k |
| Due Diligence | R$ 497 avg | 10 | 50 | R$ 25k |
| Monitor Segmento | R$ 297/mês | 10 ass. | 50 ass. | R$ 14.8k MRR |
| Monitor Órgão | R$ 247/mês | 10 | 40 | R$ 9.9k MRR |
| Radar Risco | R$ 597/mês | 5 | 20 | R$ 11.9k MRR |
| API B2B | R$ ~1/query | 10k/mês | 100k/mês | R$ 10k/mês |
| AI Copilot | R$ 497/mês | 10 | 50 | R$ 24.8k MRR |
| Radar Preditivo | R$ 497/mês | 5 | 30 | R$ 14.9k MRR |
| Data Licensing | R$ 6.997 avg | 3 | 15 | R$ 105k one-shot |
| White-label (revshare 40%) | - | 2 partners | 10 partners | R$ 30k MRR |
| **TOTAL Q4 (run-rate)** | | | | **~R$ 180k/mês + R$ 105k one-shot** |

Target conservador: MRR R$ 100k no mês 6; Receita anual Run-rate >= R$ 2M.

---

## Ordem Sugerida de Execução

### Sprint 1 (semanas 1-2)
- MON-SCH-01, MON-SCH-02, MON-SCH-03 (paralelo, squads separados)
- MON-API-01 + MON-REP-01 (paralelo)

### Sprint 2 (semanas 3-4)
- MON-API-02 + MON-REP-02 (depend 1-1)
- MON-REP-03 (inicia, produto com maior volume)

### Sprint 3 (semanas 5-6)
- MON-REP-04 (depende MON-SCH-02 concluído)
- MON-REP-05
- MON-API-03 + MON-API-04

### Sprint 4 (semanas 7-8)
- MON-REP-06 (depende MON-SCH-01 + MON-SCH-02)
- MON-API-05 (distribuição)
- **Wave 1 FIM — receita inicial esperada ~R$ 5k-10k/mês**

### Sprint 5-8 (semanas 9-16): Wave 2
- MON-SUB-01 + MON-AI-01 (paralelo)
- MON-SUB-02/03/04 + MON-AI-02/03

### Sprint 9-12 (semanas 17-24): Wave 3
- MON-SEO-04 primeiro (fix bug)
- MON-SEO-01/02/03 em paralelo
- MON-SEO-05 (polimento)
- MON-DIST-01 + MON-DIST-02 em paralelo (squads dedicados)

---

## Verificação End-to-End (pós Wave 3)

1. Receita validada em staging — cada produto com test purchase em Stripe test mode
2. Pipeline de dados — coverage CATMAT >= 80%, aditivos >= 50% últimos 2 anos
3. SEO — 5k+ URLs categoria indexadas, sitemap shards funcionando
4. API B2B — 3 endpoints p95 <500ms, metered billing reportando a Stripe
5. Assinaturas — 3 monitors + 2 add-ons IA entregando
6. IA — Copilot precision >70% em review humano; Radar Preditivo precision >60% backtest
7. Testes — pytest full suite + frontend + E2E golden paths
8. Observability — Grafana dashboards de conversão, MRR, ARPU, API usage

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Índice consolidado criado — 27 stories + 1 future ativos; plano validado com o usuário |
