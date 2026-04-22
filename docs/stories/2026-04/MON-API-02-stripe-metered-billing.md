# MON-API-02: Metered Billing — Stripe Usage Records + Audit Trail

**Priority:** P0
**Effort:** L (4-5 dias)
**Squad:** @dev + @devops
**Status:** Draft
**Epic:** [EPIC-MON-API-2026-04](EPIC-MON-API-2026-04.md)
**Sprint:** Wave 1 (depende MON-API-01)

---

## Contexto

Hoje Stripe só tem `mode=subscription` com **fixed monthly price**. Para cobrar **por consulta** (R$ 0,50–10/query), precisamos Stripe metered billing:
- Produtos Stripe com `price_type=metered` + aggregation `sum`
- Agregador interno que conta usage e envia `UsageRecord` ao Stripe no final do ciclo de billing
- Tabela `api_usage_events` para audit trail (reconciliação mensal com Stripe)
- Feature flag `ENABLE_METERED_BILLING` para rollout gradual

---

## Acceptance Criteria

### AC1: Tabela `api_usage_events`

- [ ] Migração cria:
```sql
CREATE TABLE public.api_usage_events (
  id bigserial PRIMARY KEY,
  api_key_id uuid NOT NULL REFERENCES api_keys(id),
  user_id uuid NOT NULL REFERENCES auth.users(id),
  endpoint text NOT NULL,  -- ex: '/v1/supplier/history'
  method varchar(10) NOT NULL DEFAULT 'GET',
  cost_cents int NOT NULL CHECK (cost_cents >= 0),
  response_status int NOT NULL,
  response_time_ms int NOT NULL,
  ip_address inet NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  stripe_usage_record_id text NULL,  -- preenchido quando sincronizado
  billing_period_start date NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX ON api_usage_events (user_id, created_at DESC);
CREATE INDEX ON api_usage_events (billing_period_start, user_id) WHERE stripe_usage_record_id IS NULL;
-- Particionamento por mês recomendado quando > 10M rows/mês
```
- [ ] RLS: user sees only own; service-role full access
- [ ] Migração paired down

### AC2: RPC `log_api_usage` atômico

- [ ] Função SQL:
```sql
CREATE OR REPLACE FUNCTION public.log_api_usage(
  p_api_key_id uuid, p_endpoint text, p_cost_cents int,
  p_response_status int, p_response_time_ms int, p_ip_address inet
) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  INSERT INTO api_usage_events (...) VALUES (...);
  UPDATE api_keys
    SET used_cents_current_month = used_cents_current_month + p_cost_cents,
        last_used_at = now(),
        last_used_ip = p_ip_address
    WHERE id = p_api_key_id;
END $$ SECURITY DEFINER;
```
- [ ] Performance: p99 < 20ms (medição obrigatória)
- [ ] Reset mensal de `used_cents_current_month` via cron (AC5)

### AC3: Middleware de billing

- [ ] `backend/services/metered_billing.py::charge_api_request(key, endpoint, cost_cents, status, elapsed_ms)`:
  - Chamado em `after_response` hook (post-response, fire-and-forget)
  - Invoca RPC `log_api_usage`
  - Check quota: se `used_cents_current_month + cost_cents > monthly_quota_cents` → futuro request retorna 402
- [ ] FastAPI dependency inject: cada endpoint monetizado declara `cost_cents`:
```python
@router.get("/supplier/{cnpj}/history", dependencies=[Depends(require_api_key), Depends(meter(cost_cents=100))])
```
- [ ] Feature flag `ENABLE_METERED_BILLING=false` por padrão; true em prod

### AC4: Stripe Usage Records sync

- [ ] `backend/services/metered_billing.py::sync_usage_to_stripe(user_id, period_start, period_end)`:
  - Agrega `api_usage_events` sem `stripe_usage_record_id` no período
  - Calcula total_cents por usuário
  - Cria `stripe.UsageRecord.create(subscription_item_id, quantity=total_cents, timestamp=period_end, action='set')`
  - Backfill `stripe_usage_record_id` + `billing_period_start` nos eventos sincronizados
- [ ] ARQ cron diário 02:00 BRT `metered_usage_sync_job`:
  - Processa usuários com `user_subscriptions.is_metered=true`
  - Idempotente (events com `stripe_usage_record_id NOT NULL` não reprocessa)

### AC5: Reset mensal e cronjobs

- [ ] Cron 01:00 dia 1 de cada mês reset `api_keys.used_cents_current_month = 0` via pg_cron (job único, registrado em migração)
- [ ] Monitoramento via `cron_job_health` (infra STORY-1.1 já existente)

### AC6: Script Stripe setup

- [ ] `scripts/stripe_setup_metered.py` (run-once):
  - Cria produto Stripe "SmartLic B2B API — Metered"
  - Cria 3 tiers de volume discount (ex: primeiros 10k queries R$ 1.00; próximos 40k R$ 0.80; acima R$ 0.60)
  - Imprime `price_id` para config em Railway vars
- [ ] Idempotente: valida se produto já existe antes de criar

### AC7: Dashboard admin "Uso da API"

- [ ] `/admin/api-usage` mostra top usuários por gasto mensal, queries/minuto atual, conversion stage (usage → subscription)
- [ ] Export CSV de eventos (para auditoria)

### AC8: Testes

- [ ] Unit: `test_log_api_usage_rpc.py` — performance p99 < 20ms com 10k events
- [ ] Integration: `test_metered_billing_sync.py` — mock Stripe, valida UsageRecord.create com quantity correto + backfill
- [ ] Integration: quota exceeded → 402 na próxima request
- [ ] Unit: idempotência do sync (2x run → 1 UsageRecord apenas)

---

## Scope

**IN:**
- Tabela `api_usage_events` + RPC
- Middleware billing
- Sync diário Stripe
- Reset mensal
- Script setup
- Dashboard admin
- Testes

**OUT:**
- Billing real-time (cada request → Stripe) — caro; batch diário suficiente
- Partitioning automático da tabela (ativar quando > 10M rows/mês)
- Credits / free tier specific billing (v2 — hoje quota é hard limit)

---

## Dependências

- MON-API-01 (API keys)
- Stripe account com produtos metered setup

---

## Riscos

- **Drift entre usage interno e Stripe:** reconciliação diária + alerta Sentry se delta >1%
- **Perda de events em downtime:** RPC atômico + Redis fila buffer se DB down (v2)
- **Stripe UsageRecord rate limit:** 100 req/sec — sync diário agrupa por usuário, jamais atinge

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `supabase/migrations/.../create_api_usage_events.sql` + `.down.sql`
- `supabase/migrations/.../create_log_api_usage_rpc.sql` + `.down.sql`
- `supabase/migrations/.../schedule_monthly_reset.sql` (pg_cron)
- `backend/services/metered_billing.py` (novo)
- `backend/jobs/cron/metered_usage_sync.py` (novo)
- `scripts/stripe_setup_metered.py` (novo)
- `backend/routes/admin_api_usage.py` (novo)
- `frontend/app/admin/api-usage/page.tsx` (novo)
- `backend/tests/services/test_metered_billing.py` (novo)

---

## Definition of Done

- [ ] Setup Stripe script executado, `price_id_metered` em Railway vars
- [ ] Feature flag `ENABLE_METERED_BILLING=true` em staging
- [ ] Test purchase: API key com R$ 10 quota → 100 queries × R$ 0,10 → 0,00 restante → 402 na 101ª
- [ ] Sync diário em staging → UsageRecord visível em Stripe Dashboard
- [ ] Dashboard admin mostra dados em tempo real
- [ ] Testes passando

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — enables pay-per-query B2B; foundation para Camada 4 e MON-AI-01 |
