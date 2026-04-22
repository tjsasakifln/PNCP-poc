# MON-SUB-04: Radar de Risco de Fornecedor (R$ 297–997/mês/carteira)

**Priority:** P1
**Effort:** L (5-6 dias)
**Squad:** @dev + @qa
**Status:** Draft
**Epic:** [EPIC-MON-SUBS-2026-04](EPIC-MON-SUBS-2026-04.md)
**Sprint:** Wave 2 (depende MON-SUB-01 + MON-SCH-01)

---

## Contexto

**Produto de maior ticket da Camada 3.** Persona: bancos e fintechs com exposição a fornecedores PME do setor público — precisam monitorar sinais de risco em **carteiras de CNPJs** (centenas a milhares).

**Valor percebido alto:** detecção antecipada de default → economiza perdas de crédito que podem superar R$ 100k/cliente.

**Triggers monitorados (sinais de risco):**
- Aditivo anômalo (>30% valor original ou >6 meses prazo)
- Novo contrato muito acima da mediana de mercado (superfaturamento)
- Queda abrupta de receita YoY (>40% vs período anterior)
- Perda de órgão-âncora (órgão que representava >50% da receita)
- Novos contratos com órgãos problemáticos (flag futuro: CEIS/CNEP quando Q3)

**3 tiers:**
- **R$ 297/mês** — 50 CNPJs monitorados, alertas diários por email
- **R$ 597/mês** — 200 CNPJs, alertas real-time (< 2h), webhook outbound
- **R$ 997/mês** — 500 CNPJs, + dashboard dedicado + API pull

---

## Acceptance Criteria

### AC1: Service de detecção de triggers

- [ ] `backend/monitors/risk_triggers.py` implementa:
```python
@dataclass
class RiskTrigger:
    cnpj: str
    trigger_type: str  # 'aditivo_anomalo', 'superfaturamento', 'queda_receita', 'perda_ancora'
    severity: int  # 1-10
    detected_at: datetime
    evidence: dict  # dados específicos do trigger
    score_delta: float  # mudança no score do fornecedor

def detect_triggers_for_cnpj(cnpj: str, since: datetime) -> list[RiskTrigger]: ...
```
- [ ] Cada tipo de trigger tem regra determinística documentada + testada
- [ ] Score delta calculado usando `supplier_risk_score` (MON-REP-06)

### AC2: ARQ cron `risk_radar_scan`

- [ ] `backend/jobs/cron/risk_scan.py` — diário 06:00 BRT:
  - Para cada `monitored_subscriptions` com `addon_type='radar_risco'`:
    - Itera watchlist (até 500 CNPJs)
    - Para cada CNPJ: detecta triggers desde última varredura
    - Persiste em `risk_triggers_log` (nova tabela)
    - Enfileira notificações (email + webhook)
- [ ] Shard por `subscription_id` para evitar noisy neighbor: max 1 subscription processada por vez por worker
- [ ] Rate limit interno: max 100 CNPJs checkeds por min por worker

### AC3: Tabela `risk_triggers_log`

- [ ] Migração:
```sql
CREATE TABLE public.risk_triggers_log (
  id bigserial PRIMARY KEY,
  subscription_id uuid NOT NULL REFERENCES monitored_subscriptions(id),
  cnpj varchar(14) NOT NULL,
  trigger_type text NOT NULL,
  severity int NOT NULL CHECK (severity BETWEEN 1 AND 10),
  evidence jsonb NOT NULL,
  score_delta numeric(5,2) NULL,
  detected_at timestamptz NOT NULL DEFAULT now(),
  notified_at timestamptz NULL,
  acknowledged_at timestamptz NULL,
  acknowledged_by_user_id uuid NULL
);
CREATE INDEX ON risk_triggers_log (subscription_id, detected_at DESC);
CREATE INDEX ON risk_triggers_log (cnpj, detected_at DESC);
```

### AC4: Notificações email + webhook

- [ ] Template email `risk_alert.py`:
  - Subject: `"🚨 {cnpj} — {trigger_type} (severidade {severity}/10)"`
  - Body: CNPJ, nome, trigger, evidência, link para dashboard, CTA "Ignorar este alerta"
- [ ] Webhook outbound (tier Premium+):
  - POST para URL configurada pelo cliente com payload JSON + HMAC signature
  - Retry 3x com backoff exponencial
  - DLQ em Redis se falhar

### AC5: Dashboard `/monitores/{id}` para radar

- [ ] Adapta dashboard MON-SUB-02:
  - Seção "Alertas ativos" com triggers dos últimos 30 dias
  - Botão "Reconhecer" por trigger (marca `acknowledged_at`)
  - Gráfico de triggers por severidade ao longo do tempo
  - Tabela "CNPJs na carteira" com score atual + número de triggers ativos

### AC6: Webhook outbound config

- [ ] Endpoint `POST /v1/monitors/{id}/webhook-config`:
  - Body: `{url, secret, events: [trigger_types]}`
  - Valida URL (HTTPS obrigatório + teste ping)
- [ ] Documentação: `docs/api/webhooks-risk-radar.md`

### AC7: Testes

- [ ] Unit: `test_risk_triggers.py` — cada tipo de trigger com dados conhecidos → detecta ou não
- [ ] Integration: cron full flow E2E
- [ ] Unit: webhook HMAC signature válida; retry on failure
- [ ] Performance: scan de 500 CNPJs < 5 min

---

## Scope

**IN:**
- Service de triggers (4 tipos iniciais)
- Cron + tabela log
- Notificações email + webhook
- Dashboard
- Testes

**OUT:**
- CEIS/CNEP triggers (Q3)
- ML anomaly detection (Q3, complementar a regras determinísticas)
- Integração Slack/Teams (v2)
- Alertas SMS (v2)

---

## Dependências

- MON-SUB-01 (bloqueador)
- **MON-SCH-01 (aditivos)** — obrigatório para trigger de aditivo anômalo
- `supplier_risk_summary_mv` populada

---

## Riscos

- **False positives causam churn:** cada trigger precisa threshold calibrado em dataset histórico (80% precision target) — gate antes do release
- **Carteira grande (500 CNPJs) sobrecarrega worker:** shard por subscription, throttle 100 CNPJs/min
- **Webhook destination down:** DLQ com alerta para cliente; se falha >24h, desativa webhook + email admin

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `supabase/migrations/.../create_risk_triggers_log.sql` + `.down.sql`
- `backend/monitors/risk_triggers.py` (novo)
- `backend/jobs/cron/risk_scan.py` (novo)
- `backend/templates/emails/risk_alert.py` (novo)
- `backend/webhooks/outbound.py` (novo)
- `backend/routes/monitors_webhook.py` (novo)
- `frontend/app/monitores/[id]/page.tsx` (estender — componente de radar)
- `backend/tests/monitors/test_risk_triggers.py` (novo)

---

## Definition of Done

- [ ] 4 tipos de trigger com precision >80% em backtest (6 meses históricos)
- [ ] Cron rodando com carteira simulada (50 CNPJs) sem Sentry errors por 1 semana
- [ ] Webhook outbound funciona end-to-end para endpoint de teste
- [ ] Dashboard funcional
- [ ] Testes passando

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — produto high-ticket Camada 3 para fintechs/bancos |
