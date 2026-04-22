# EPIC-MON-AI-2026-04: Extras IA/ML sobre o Dataset de 2M+ Contratos

**Priority:** P1 — Wave 2 (moat tecnológico)
**Status:** Draft
**Owner:** @architect + @dev + @data-engineer
**Sprint:** Wave 2 (paralelo com EPIC-MON-SUBS)
**Meta:** Construir moat defensivo via produtos de IA/ML treinados sobre dataset proprietário; add-ons alto ticket + API ML.

---

## Contexto Estratégico

O dataset de 2.1M contratos históricos é ativo **único no mercado B2G brasileiro** — nenhum competidor tem:
- Dados estruturados com classificação setorial IA + score de viabilidade
- Possibilidade de RAG/few-shot sobre corpus proprietário vasto
- Histórico longitudinal para detecção de sazonalidade/padrões

Três produtos aproveitam esse moat:

| Produto | Preço | Moat |
|---------|-------|------|
| Semantic Search / Embeddings API | R$ 0,10–1/query | Base vetorial única do PNCP |
| AI Copilot de Propostas | R$ 197/proposta ou R$ 497/mês | RAG sobre vencedores — impossível replicar sem o dataset |
| Radar Preditivo de Editais | R$ 297–997/mês | ML sazonal requer 3+ anos de histórico |

---

## Stories do Epic

| Story | Priority | Effort | Squad | Status | Objetivo |
|-------|:--------:|:------:|-------|:------:|----------|
| MON-AI-01 | P0 | L | @data-engineer + @dev | Draft | Semantic Search / Embeddings API (pgvector) |
| MON-AI-02 | P1 | XL | @dev + @architect | Draft | AI Copilot de Propostas (RAG) |
| MON-AI-03 | P1 | XL | @data-engineer + @dev | Draft | Radar Preditivo de Editais (ML sazonal) |

---

## Ordem de Execução

1. **MON-AI-01** primeiro (bloqueia MON-AI-02; usa infra criada em MON-API-01/02)
2. **MON-AI-02** após MON-AI-01 + MON-REP-01 + MON-SUB-01
3. **MON-AI-03** paralelo com MON-AI-02 (depende de MON-SCH-01 + MON-SCH-02 + MON-SUB-01; não depende de MON-AI-01)

---

## KPIs do Epic

| KPI | Meta 90 dias | Meta 180 dias |
|-----|--------------|---------------|
| Coverage embeddings (top 500k por valor) | 100% | 100% (+ 1M extras) |
| Queries semantic search/mês | 1.000 | 20.000 |
| Propostas geradas/mês (Copilot) | 50 | 500 |
| NPS Copilot | >30 | >50 |
| Precision Radar Preditivo (backtest) | >60% | >75% |
| Alertas preditivos acionados | 100/mês | 2.000/mês |
| Receita Extras IA/ML | R$ 3.000/mês | R$ 50.000/mês |

---

## Dependências

- **Bloqueado por:**
  - MON-API-01/02 → MON-AI-01 (usa infra API key + metered billing)
  - MON-AI-01 → MON-AI-02 (RAG usa embeddings)
  - MON-REP-01 → MON-AI-02 (one-shot R$197)
  - MON-SUB-01 → MON-AI-02 + MON-AI-03 (add-on recorrente)
  - MON-SCH-01 + MON-SCH-02 → MON-AI-03

---

## Riscos

- **Custo de embeddings** — vetorizar 2.1M linhas com `text-embedding-3-small` @ USD 0.02/1M tokens; estimativa ~USD 200 one-shot. Priorizar top 500k por valor para controle de custo inicial
- **Qualidade do Copilot** — rascunhos ruins geram churn; requer validação humana em 20+ propostas reais antes de liberar público
- **Precision Radar** — ML sazonal sobre procurement é nicho; benchmark internos vs dados históricos obrigatórios antes de cobrar

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Epic criado — estratégia extra IA/ML (não estava nas 4 camadas originais) |
