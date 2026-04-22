# MON-AI-03: Radar Preditivo de Editais (ML Sazonal)

**Priority:** P1
**Effort:** XL (8-10 dias)
**Squad:** @data-engineer + @dev + @architect
**Status:** Draft
**Epic:** [EPIC-MON-AI-2026-04](EPIC-MON-AI-2026-04.md)
**Sprint:** Wave 2 (depende MON-SCH-01/02 + MON-SUB-01)

---

## Contexto

Dataset de 2.1M contratos com 3+ anos de histórico permite **detecção de padrões sazonais**: órgão X licita serviço Y recorrentemente em mês Z. Ex: "Município São Paulo sempre licita limpeza urbana em setembro (contrato vencendo em dezembro)".

**Produto:** add-on "Radar Preditivo" que prevê editais dos próximos 30-60 dias para (órgão + CATMAT/CATSER). Fornecedor se antecipa — prepara proposta, entra em contato com órgão, ganha vantagem competitiva.

**Modelo comercial:**
- Add-on R$ 297-997/mês (via MON-SUB-01)
- Tiers: 5 previsões (R$ 297), 20 (R$ 597), ilimitado (R$ 997)

**Diferencial:** competidores reactive (mostram editais publicados); SmartLic proactive (antes da publicação).

---

## Acceptance Criteria

### AC1: Detecção de sazonalidade

- [ ] `backend/ml/seasonal_detection.py`:
  - Para cada tupla (orgao_cnpj, catmat_catser) com ≥ 3 contratos histórico ≥ 2 anos:
    - Calcula coeficiente de sazonalidade via `statsmodels.tsa.seasonal_decompose` ou `prophet`
    - Se coef >= 0.6 (limiar de confiança): marca como "padrão sazonal confirmado"
    - Extrai mês(es) do ano com maior probabilidade de novo contrato
    - Calcula intervalo médio entre contratos (dias)
- [ ] Pipeline offline rodando semanalmente (ARQ cron)
- [ ] Persistir em `seasonal_patterns`:
```sql
CREATE TABLE public.seasonal_patterns (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  orgao_cnpj varchar(14) NOT NULL,
  catmat_catser varchar(10) NOT NULL,
  setor_classificado text NULL,
  uf varchar(2) NULL,
  coef_sazonalidade numeric(4,3) NOT NULL,
  months_high_prob int[] NOT NULL,  -- [9, 10] = setembro, outubro
  interval_days_mean int NOT NULL,
  interval_days_stddev int NOT NULL,
  last_contract_date date NOT NULL,
  historical_n_contracts int NOT NULL,
  confidence_tier text NOT NULL CHECK (confidence_tier IN ('high','medium','low')),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(orgao_cnpj, catmat_catser)
);
CREATE INDEX ON seasonal_patterns (months_high_prob, coef_sazonalidade);
```

### AC2: Previsão de próximos editais

- [ ] `backend/ml/prediction_engine.py`:
  - Para cada `seasonal_patterns` row + `last_contract_date`:
    - Calcula `expected_next_date = last_contract_date + interval_days_mean`
    - Se `expected_next_date` está nos próximos 30-60 dias E `current_month+1 IN months_high_prob`:
      - Gera predição em `predicted_bids`:
```sql
CREATE TABLE public.predicted_bids (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  orgao_cnpj varchar(14) NOT NULL,
  catmat_catser varchar(10) NOT NULL,
  expected_publish_date date NOT NULL,
  expected_publish_window_start date NOT NULL,
  expected_publish_window_end date NOT NULL,
  confidence_score numeric(3,2) NOT NULL,
  estimated_value_cents int NULL,
  historical_evidence jsonb NOT NULL,  -- últimos 3-5 contratos como prova
  generated_at timestamptz NOT NULL DEFAULT now(),
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','fulfilled','missed','cancelled')),
  fulfilled_bid_id text NULL REFERENCES pncp_raw_bids(id)
);
```
  - ARQ cron semanal atualiza predictions

### AC3: Validação de predições (feedback loop)

- [ ] Cron diário `validate_predictions_job`:
  - Para cada `predicted_bids` com `status='pending'`:
    - Busca em `pncp_raw_bids` por editais novos match (orgao_cnpj + catmat_catser + data dentro de janela)
    - Se encontra: marca `status='fulfilled'`, `fulfilled_bid_id`
    - Se janela expirou sem match: `status='missed'`
- [ ] Backtest mensal: compara predictions vs pncp_raw_bids reais dos últimos 6 meses → computa precision/recall
- [ ] Se precision < 50% por 2 meses: fine-tune thresholds (adjust via config YAML)

### AC4: Endpoint `/v1/radar-preditivo` (add-on restrito)

- [ ] `GET /v1/radar-preditivo` (auth JWT + check `monitored_subscriptions.addon_type='radar_preditivo' AND active=true`)
- [ ] Query params: `setor` (obrigatório), `uf` (opcional), `min_confidence` (default 0.7)
- [ ] Retorna array de `predicted_bids` do user (limit por tier)
- [ ] Rate limit: 30 req/min

### AC5: Dashboard `/radar-preditivo`

- [ ] `frontend/app/radar-preditivo/page.tsx`:
  - Seletor setor + UF
  - Lista de predições: órgão, CATMAT, expected_date, confidence, valor estimado, botão "Ver evidência histórica"
  - Mapa do Brasil com densidade de predições (heatmap)
  - Timeline próximos 60 dias
- [ ] Onboarding: tutorial de 3 slides "Como usar o radar"

### AC6: Notificações de alerta (tier Premium)

- [ ] Trigger diário: se nova predição entra dentro de 15 dias de expected_publish_date + CATMAT match watchlist do user → email alerta
- [ ] Template `radar_preditivo_alert.py`

### AC7: Testes

- [ ] Unit: `test_seasonal_detection.py` — série temporal sintética com padrão conhecido → detecta corretamente
- [ ] Integration: pipeline completo para 1 órgão real → gera predições plausíveis
- [ ] Backtest: precision >= 55% em 6 meses histórico (gate para release)

---

## Scope

**IN:**
- Detecção sazonal offline
- Engine de predição
- Validação feedback loop
- Endpoint + dashboard + alertas
- Backtest precision gate
- Testes

**OUT:**
- ML sofisticado (LSTM, Transformers) — v2 se Prophet/seasonal_decompose não atingir target
- Predição de vencedor (quem ganhará o edital) — é outro produto (futuro Q3)
- Recomendação de preço para proposta — é outro produto (combina com MON-AI-02)

---

## Dependências

- **MON-SCH-01 (aditivos)** — dá sinal de contrato "ativo" para filtragem
- **MON-SCH-02 (CATMAT)** — bloqueador absoluto (sem CATMAT, sazonalidade vira ruído)
- MON-SUB-01 (add-on recorrente)
- Python ML libs: `statsmodels` ou `prophet`

---

## Riscos

- **Precision baixa em categorias não-sazonais:** filtrar apenas pairs com `coef_sazonalidade >= 0.6`; se amostra fica muito pequena, documentar como "v1 cobertura restrita, expandindo"
- **Backtest mostra precision <50%:** release bloqueado; ajuste de thresholds ou adiamento para Q3
- **Dataset ruidoso (mudança de código CATMAT ao longo do tempo):** limitar janela a 3 anos recentes

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `supabase/migrations/.../create_seasonal_patterns.sql` + `.down.sql`
- `supabase/migrations/.../create_predicted_bids.sql` + `.down.sql`
- `backend/ml/seasonal_detection.py` (novo)
- `backend/ml/prediction_engine.py` (novo)
- `backend/jobs/cron/seasonal_detection_job.py` (novo)
- `backend/jobs/cron/validate_predictions_job.py` (novo)
- `backend/routes/radar_preditivo.py` (novo)
- `backend/templates/emails/radar_preditivo_alert.py` (novo)
- `frontend/app/radar-preditivo/page.tsx` (novo)
- `scripts/backtest_predictions.py` (novo)
- `backend/tests/ml/test_seasonal_detection.py` (novo)

---

## Definition of Done

- [ ] Pipeline semanal rodando + persistindo predictions
- [ ] Backtest 6 meses: precision >= 55%
- [ ] 10 predições de exemplo validadas com analista humano
- [ ] Dashboard funcional
- [ ] Testes passando

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — moat IA via ML sazonal sobre histórico proprietário |
