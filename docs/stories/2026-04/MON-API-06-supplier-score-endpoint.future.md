# MON-API-06 (FUTURE — Q3): `GET /api/v1/supplier/{cnpj}/score` (R$ 2–10/consulta)

**Priority:** P2 — Backlog Q3
**Effort:** L (6-8 dias)
**Squad:** @data-engineer + @dev + @architect
**Status:** Future (não incluído em Wave 1)
**Epic:** [EPIC-MON-API-2026-04](EPIC-MON-API-2026-04.md)
**Sprint:** Q3 (após Waves 1-3 consolidadas)

---

## Contexto

Terceiro endpoint da Camada 4, **mais alto ticket** (R$ 2–10/consulta) porque entrega **score modelado via ML**, não agregação simples. Composição do score:

- Capacidade (30%): volume de contratos executados, diversidade de órgãos, crescimento YoY
- Adimplência (30%): índice de aditivos, rescisões, % valor aditado
- Concentração (20%): Herfindahl-Hirschman (órgão + setor), volatilidade
- Estabilidade (20%): anos atuante, gap entre contratos, sazonalidade

Requer modelo ML treinado em dataset histórico com labels (default rate, churn, sanção CEIS/CNEP no futuro).

---

## Acceptance Criteria

### AC1: Modelo ML offline

- [ ] Pipeline de feature engineering em `backend/ml/supplier_score/features.py`
- [ ] Modelo: Gradient Boosting (XGBoost ou LightGBM) treinado em labels proxy (ex: fornecedor teve aditivo >50% → label risky)
- [ ] Cross-validation: AUC > 0.75 mínimo
- [ ] Model versioning: mlflow ou arquivo versionado em S3 com hash

### AC2: Endpoint

- [ ] `GET /api/v1/supplier/{cnpj}/score`
- [ ] Response: `{cnpj, score_geral: 0-100, breakdown: {capacidade, adimplencia, concentracao, estabilidade}, percentil_setor, flags[], confidence: 0-1, model_version, computed_at}`
- [ ] Cache 24h em Redis (score não muda diariamente)

### AC3: Disclaimer e governança

- [ ] Response inclui disclaimer: "score derivado de dados públicos; não constitui análise de crédito formal"
- [ ] Opt-out endpoint: `POST /api/v1/supplier/{cnpj}/opt-out` (requer prova de titularidade — email do domínio do CNPJ)
- [ ] Audit log de cada consulta (quem consultou quem, para compliance LGPD)

### AC4: Testes e validação

- [ ] Backtest: score alto para peers históricos estáveis, score baixo para peers com default conhecido
- [ ] Monitoramento de drift: retrain mensal se AUC cair abaixo 0.7

---

## Dependências

- MON-SCH-01 (aditivos)
- MON-SCH-02 (CATMAT) — para padrão de preço por categoria
- MON-AI-01 (embeddings) — opcional, para feature "similaridade com defaulters"
- CEIS/CNEP integration (MON-REP-06b Q3) — labels para treinamento
- Infraestrutura ML: GPU opcional para training, CPU suficiente para inference

---

## Scope

**IN (Q3 quando ativado):**
- Pipeline ML offline
- Endpoint REST
- Cache + disclaimer + opt-out
- Testes + backtest

**OUT (mesmo em Q3):**
- Score preditivo de "ganhará próximo edital?" — produto separado (pertence a MON-AI-03)
- Score de correlação entre fornecedores (cartel detection) — story dedicada se virar demanda

---

## Status: BACKLOG Q3

Esta story **não** será implementada em Wave 1. Fica como placeholder para rastreamento do roadmap. Pré-requisitos (MON-SCH-01, MON-SCH-02) sobrepõem com Wave 1.

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story FUTURE criada — roadmap Q3 pós Waves 1-3 |
