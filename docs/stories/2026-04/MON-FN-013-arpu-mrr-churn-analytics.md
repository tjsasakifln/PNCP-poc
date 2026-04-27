# MON-FN-013: ARPU / MRR / Churn Analytics Dashboard

**Priority:** P2
**Effort:** M (3-4 dias)
**Squad:** @data-engineer + @analyst
**Status:** Ready
**Epic:** [EPIC-MON-FN-2026-Q2](EPIC-MON-FN-2026-Q2.md)
**Sprint:** 6 (03–09/jun)
**Sprint Window:** Sprint 6 (depende de MON-FN-007)
**Dependências bloqueadoras:** MON-FN-007 (`dunning_state` table + recovery events para churn cálculo)

---

## Contexto

SmartLic tem zero visibilidade financeira hoje:
- **MRR (Monthly Recurring Revenue):** soma de subscription cobranças mensalizadas. Sem cálculo.
- **ARPU (Average Revenue Per User):** MRR / active paying users. Sem cálculo.
- **Churn rate:** users que cancelaram / users active. Sem cálculo.
- **Expansion / Contraction MRR:** upgrades / downgrades intra-mês. Sem cálculo.
- **LTV (Lifetime Value):** ARPU × avg subscription length. Sem cálculo (n=2 baseline impede de qualquer forma).

Source of truth:
- **Stripe API:** `Subscription.list` retorna canonical billing state (active, canceled, past_due, etc.) + `latest_invoice.amount_paid`
- **`profiles.plan_type`:** snapshot local (sincronizado via webhooks STORY-307)
- **`plan_billing_periods`:** preços canonicos (memory `pricing-b2g`)
- **`dunning_state` (MON-FN-007):** dunning status para churn cálculo
- **`analytics_events.trial_converted`:** sinal de conversion timing

**Por que P2:** mesmo que n=2 atual, infra precisa estar pronta antes de scale. Decisões de pricing/plans (out-of-scope desta epic) requerem ARPU/MRR como input. Sem isto, qualquer experimento financeiro é cego.

**Cross-reference plano:** "Dashboard MRR (new + expansion + churn + contraction), ARPU, churn rate; fonte Stripe API + plan_type".

**Paths críticos:**
- `backend/services/financial_metrics.py` (NOVO — cálculo ARPU/MRR)
- `backend/cron/financial_dashboard.py` (NOVO — daily refresh)
- `supabase/migrations/` (tabela `financial_snapshots`)
- `backend/routes/admin.py` (endpoint expor data)
- Frontend admin dashboard

---

## Acceptance Criteria

### AC1: Tabela `financial_snapshots` (snapshots diárias)

Given que dashboards precisam time-series,
When daily refresh roda,
Then INSERT em `financial_snapshots`.

- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_create_financial_snapshots.sql`:
```sql
CREATE TABLE public.financial_snapshots (
  snapshot_date date PRIMARY KEY,
  -- MRR breakdown
  mrr_total_cents bigint NOT NULL DEFAULT 0,
  mrr_new_cents bigint NOT NULL DEFAULT 0,           -- new subscriptions this month
  mrr_expansion_cents bigint NOT NULL DEFAULT 0,    -- upgrades (e.g. mensal→anual)
  mrr_contraction_cents bigint NOT NULL DEFAULT 0,  -- downgrades
  mrr_churned_cents bigint NOT NULL DEFAULT 0,      -- canceled subs
  -- Counts
  active_paying_users int NOT NULL DEFAULT 0,
  active_trial_users int NOT NULL DEFAULT 0,
  active_free_users int NOT NULL DEFAULT 0,         -- smartlic_free (MON-FN-008)
  -- Metrics
  arpu_cents int NOT NULL DEFAULT 0,                 -- mrr_total / active_paying_users
  trial_to_paid_conversion_rate_pct numeric(5,2),    -- last 30d trial_converted / trial_started
  voluntary_churn_rate_pct numeric(5,2),             -- last 30d churned / start_of_period_active
  involuntary_churn_rate_pct numeric(5,2),           -- dunning_lost / start_of_period_active
  -- Plan distribution
  plan_distribution jsonb NOT NULL DEFAULT '{}'::jsonb,  -- {smartlic_pro: 12, smartlic_consultoria: 3, ...}
  -- Provenance
  calculated_at timestamptz NOT NULL DEFAULT now(),
  data_source text NOT NULL DEFAULT 'stripe_api+local',
  notes text
);
CREATE INDEX idx_financial_snapshots_date ON public.financial_snapshots (snapshot_date DESC);

ALTER TABLE public.financial_snapshots ENABLE ROW LEVEL SECURITY;
-- Admin only
CREATE POLICY "Admins read financial_snapshots" ON public.financial_snapshots
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND (is_admin OR is_master))
  );
CREATE POLICY "Service full" ON public.financial_snapshots FOR ALL USING (auth.role() = 'service_role');
```
- [ ] Migration paired down `.down.sql`
- [ ] Retention: keep all snapshots forever (financial audit value); ~365 rows/year, cheap

### AC2: Cron `financial_metrics_job` daily

Given que precisamos snapshot diário,
When cron roda,
Then calcula MRR/ARPU/churn e UPSERT em `financial_snapshots`.

- [ ] Novo `backend/cron/financial_dashboard.py`:
```python
import os
from datetime import date, datetime, timezone, timedelta
import stripe

async def financial_metrics_job() -> dict:
    """Daily: calculate MRR/ARPU/churn metrics and snapshot them."""
    lock = await acquire_redis_lock("smartlic:financial_metrics:lock", 30 * 60)
    if not lock:
        return {"status": "skipped"}
    try:
        from supabase_client import get_supabase
        from services.financial_metrics import calculate_daily_snapshot

        sb = get_supabase()
        today = date.today()
        snapshot = await calculate_daily_snapshot(sb, today)

        sb.table("financial_snapshots").upsert(snapshot, on_conflict="snapshot_date").execute()

        return {"status": "completed", "snapshot": snapshot}
    finally:
        await release_redis_lock("smartlic:financial_metrics:lock")
```
- [ ] Cron schedule: 14 UTC daily (after cohort dashboard refresh)
- [ ] Idempotência: UPSERT com on_conflict snapshot_date

### AC3: Helper `calculate_daily_snapshot`

Given que cálculo é complex,
When chamado,
Then orquestra Stripe + local data.

- [ ] Novo `backend/services/financial_metrics.py`:
```python
import stripe
from datetime import date, datetime, timezone, timedelta

async def calculate_daily_snapshot(sb, snapshot_date: date) -> dict:
    """Calculate financial snapshot for a given date."""
    stripe_key = os.getenv("STRIPE_SECRET_KEY")

    # 1. MRR via Stripe API (canonical)
    mrr_total = 0
    active_paying = 0
    plan_distribution = {}

    # Fetch all active subscriptions (paginated)
    starting_after = None
    while True:
        page = stripe.Subscription.list(
            api_key=stripe_key,
            status="active",
            limit=100,
            starting_after=starting_after,
        )
        for sub in page.data:
            # Monthlyize the subscription amount
            for item in sub["items"]["data"]:
                price = item["price"]
                interval = price["recurring"]["interval"]  # month | year
                unit_amount = price["unit_amount"] or 0
                monthly_cents = unit_amount if interval == "month" else unit_amount // 12
                mrr_total += monthly_cents
                plan_id = sub.metadata.get("plan_id", "unknown")
                plan_distribution[plan_id] = plan_distribution.get(plan_id, 0) + 1
            active_paying += 1
        if not page.has_more:
            break
        starting_after = page.data[-1].id

    # 2. Counts from local DB
    trial_users = sb.table("profiles").select("id", count="exact") \
        .eq("plan_type", "free_trial").is_("deleted_at", "null").execute().count or 0
    free_users = sb.table("profiles").select("id", count="exact") \
        .eq("plan_type", "smartlic_free").is_("deleted_at", "null").execute().count or 0

    # 3. ARPU
    arpu = mrr_total // max(active_paying, 1)

    # 4. Conversion rate (last 30d)
    period_start = snapshot_date - timedelta(days=30)
    trial_started = sb.table("analytics_events").select("user_id", count="exact") \
        .eq("event_name", "trial_started") \
        .gte("occurred_at", period_start.isoformat()).execute().count or 0
    trial_converted = sb.table("analytics_events").select("user_id", count="exact") \
        .eq("event_name", "trial_converted") \
        .gte("occurred_at", period_start.isoformat()).execute().count or 0
    conv_rate = round(100.0 * trial_converted / max(trial_started, 1), 2)

    # 5. Churn rates (last 30d)
    voluntary_churn = sb.table("analytics_events").select("user_id", count="exact") \
        .eq("event_name", "subscription_cancelled") \
        .gte("occurred_at", period_start.isoformat()).execute().count or 0
    involuntary_churn = sb.table("analytics_events").select("user_id", count="exact") \
        .eq("event_name", "dunning_lost") \
        .gte("occurred_at", period_start.isoformat()).execute().count or 0
    # Active at start of period (approx — could be smarter)
    active_at_start = active_paying + voluntary_churn + involuntary_churn  # rough
    voluntary_rate = round(100.0 * voluntary_churn / max(active_at_start, 1), 2)
    involuntary_rate = round(100.0 * involuntary_churn / max(active_at_start, 1), 2)

    # 6. MRR breakdown (new/expansion/contraction/churned) — last 30d
    # Simplified: only "new" tracked from trial_converted; full breakdown requires more state
    mrr_new = trial_converted * arpu  # very rough; refine in iteration
    mrr_churned = (voluntary_churn + involuntary_churn) * arpu

    return {
        "snapshot_date": snapshot_date.isoformat(),
        "mrr_total_cents": mrr_total,
        "mrr_new_cents": mrr_new,
        "mrr_expansion_cents": 0,  # TODO: detect upgrades via Stripe events
        "mrr_contraction_cents": 0,  # TODO: detect downgrades
        "mrr_churned_cents": mrr_churned,
        "active_paying_users": active_paying,
        "active_trial_users": trial_users,
        "active_free_users": free_users,
        "arpu_cents": arpu,
        "trial_to_paid_conversion_rate_pct": conv_rate,
        "voluntary_churn_rate_pct": voluntary_rate,
        "involuntary_churn_rate_pct": involuntary_rate,
        "plan_distribution": plan_distribution,
    }
```
- [ ] Trade-off documentado: simplified MRR breakdown (new/churn only) v1; expansion/contraction em iteração
- [ ] n=2 baseline: ARPU pode ser inflated por outliers; flag se cohort < 5

### AC4: Endpoint `/v1/admin/dashboards/financial`

Given admin pede,
When request,
Then retorna time-series.

- [ ] Em `backend/routes/admin.py` ou `routes/admin_dashboards.py`:
```python
@router.get("/v1/admin/dashboards/financial")
async def financial_dashboard(
    days_back: int = Query(90, ge=7, le=365),
    user: User = Depends(require_admin),
):
    sb = get_supabase()
    period_start = (date.today() - timedelta(days=days_back)).isoformat()
    result = sb.table("financial_snapshots").select("*") \
        .gte("snapshot_date", period_start) \
        .order("snapshot_date").execute()

    return {
        "snapshots": result.data,
        "as_of": datetime.now(timezone.utc).isoformat(),
        "n_warning": result.data and result.data[-1]["active_paying_users"] < 30,  # n<30 noise warning
    }
```

### AC5: Frontend dashboard `/admin/dashboards/financial`

Given admin acessa,
When render,
Then mostra gráficos MRR/ARPU/churn.

- [ ] `frontend/app/admin/dashboards/financial/page.tsx`:
  - **Header KPIs:** MRR atual, ARPU, total paying, growth WoW%
  - **Chart 1:** MRR line chart (90d) com componentes empilhados (new/expansion/churned)
  - **Chart 2:** Active users (paying + trial + free) bar chart por plan_type
  - **Chart 3:** Churn rate trendline (voluntary vs involuntary)
  - **Table:** plan_distribution snapshot mais recente
  - **N-warning banner:** "n < 30 — métricas podem ser ruido" (memory `feedback_n2_below_noise_eng_theater`)
  - Recharts library
- [ ] Mobile-responsive (KPIs em cards stackable)
- [ ] Export CSV (snapshots time-series)

### AC6: Counter `subscription_cancelled` event

Given que MRR breakdown precisa de event consistente,
When subscription cancela,
Then `subscription_cancelled` event emitido.

- [ ] Em `backend/webhooks/handlers/subscription.py::handle_subscription_deleted`:
```python
# Add to existing handler:
track_funnel_event("subscription_cancelled", user_id, properties={
    "stripe_subscription_id": subscription.id,
    "cancellation_reason": subscription.cancellation_details.get("reason") if subscription.cancellation_details else None,
    "canceled_at": subscription.canceled_at,
})
```
- [ ] Idempotência via stripe_webhook_events (existente)

### AC7: Métricas Prometheus

- [ ] Gauge `smartlic_mrr_total_cents` (snapshot diário)
- [ ] Gauge `smartlic_arpu_cents`
- [ ] Gauge `smartlic_active_paying_users`
- [ ] Counter `smartlic_subscription_cancelled_total`
- [ ] Histograma `smartlic_financial_snapshot_duration_seconds`

### AC8: Documentação metodológica

- [ ] Doc `docs/dashboards/financial-metrics.md`:
  - Definições: MRR, ARPU, voluntary vs involuntary churn
  - Source of truth: Stripe (subscriptions) + local DB (`profiles.plan_type` + `analytics_events`)
  - Refresh cadence: daily 14 UTC
  - Limitações: expansion/contraction MRR não capturados em v1
  - n<30 warning: dados são noise abaixo desse threshold

### AC9: Testes

- [ ] Unit `backend/tests/services/test_financial_metrics.py`:
  - [ ] `calculate_daily_snapshot` com mock Stripe + DB → snapshot correto
  - [ ] ARPU = mrr / paying (correct integer math)
  - [ ] Conversion rate: 5 trials, 1 converted → 20%
  - [ ] Edge: 0 active_paying → no division by zero (uses max(1))
- [ ] Integration `backend/tests/cron/test_financial_metrics_job.py`:
  - [ ] Job creates snapshot for today
  - [ ] Re-run mesmo dia → UPSERT (overwrites)
  - [ ] Mock Stripe Subscription.list paginated
- [ ] Frontend `frontend/__tests__/admin/financial.test.tsx`:
  - [ ] Render charts with mock data
  - [ ] N-warning visible when active_paying < 30
- [ ] Cobertura ≥85%

---

## Scope

**IN:**
- Tabela `financial_snapshots`
- Cron `financial_metrics_job` daily
- Helper `calculate_daily_snapshot`
- Endpoint admin
- Frontend dashboard com Recharts
- Métricas Prometheus
- Doc metodológico
- `subscription_cancelled` event

**OUT:**
- LTV calculation (over-engineering pre-revenue; n insuficiente)
- Cohort-based MRR (separate dashboard MON-FN-012)
- Expansion/contraction MRR detection (v2 — exige tracking de plan upgrades)
- Forecasting / ML predictions (premature)
- Multi-currency (BRL only)
- Tax-adjusted revenue (Stripe Tax handles)
- Quickbooks/Xero export (manual via CSV se necessário)
- Realtime dashboard (daily refresh suficiente)

---

## Definition of Done

- [ ] Migration aplicada
- [ ] Cron `financial_metrics_job` registrado + executando 14 UTC
- [ ] Smoke test: snapshot D+0 inserted após primeiro run
- [ ] Endpoint `/v1/admin/dashboards/financial` retorna time-series
- [ ] Frontend dashboard renderiza charts
- [ ] Cobertura ≥85%
- [ ] CodeRabbit clean
- [ ] Doc metodológico publicado
- [ ] N-warning banner visível em frontend (memory n<30)
- [ ] Sentry alert em job failure
- [ ] Stripe API key restrito a read-only no Railway env (security)

---

## Dev Notes

### Padrões existentes a reutilizar

- **`acquire_redis_lock`:** existing
- **`stripe.Subscription.list`:** SDK já em deps
- **`require_admin`:** existing
- **Recharts:** já usado em outros dashboards
- **STORY-1.1 cron monitor:** view auto-cobre

### Funções afetadas

- `backend/services/financial_metrics.py` (NOVO)
- `backend/cron/financial_dashboard.py` (NOVO)
- `backend/job_queue.py::WorkerSettings` (registrar)
- `backend/routes/admin.py` ou `routes/admin_dashboards.py` (NOVO endpoint)
- `frontend/app/admin/dashboards/financial/page.tsx` (NOVO)
- `backend/webhooks/handlers/subscription.py` (adicionar event)
- `backend/metrics.py` (gauges)
- `supabase/migrations/YYYYMMDDHHMMSS_create_financial_snapshots.sql` + `.down.sql`
- `docs/dashboards/financial-metrics.md` (NOVO)

### Trade-off: Stripe API vs local cache

- Stripe API: canonical truth mas rate-limited (100 req/sec)
- Local `profiles.plan_type`: snapshot rápido mas pode dessincronizar
- Decisão: hybrid — Stripe API para MRR (canonical), local DB para counts

### n<30 noise warning (memory)

Memory `feedback_n2_below_noise_eng_theater` (2026-04-26): "<5 reais = defer automação, foque outreach manual". Aplicado:
- Banner visual no dashboard
- Endpoint retorna `n_warning` boolean
- Logs Sentry tag `n_below_threshold` quando active_paying < 30

### Testing Standards

- Mock Stripe via `@patch("stripe.Subscription.list")`
- Generator paginado mocked
- Cobertura: `pytest --cov=backend/services/financial_metrics.py --cov=backend/cron/financial_dashboard.py`
- Anti-hang: pytest-timeout 30s

---

## Risk & Rollback

### Triggers de rollback
- Stripe API rate limit hit (Stripe penalty)
- Snapshot job timeout (>30 min)
- Stripe API key compromise (rotate immediately)
- Bad data: ARPU ou MRR claramente errado (validation antes de UPSERT)

### Ações de rollback
1. **Imediato:** disable cron via `FINANCIAL_DASHBOARD_ENABLED=false`
2. **Stripe issue:** Stripe Dashboard rate limit → reduce frequency to weekly
3. **Bad data:** SQL DELETE bad snapshots (audit value preserved via `notes` column de manual override)
4. **Communication:** dashboard mostra "dados em manutenção"

### Compliance
- Stripe customer data não é fetchada (apenas aggregate counts) — LGPD-safe
- Admin-only — no user PII exposure
- Snapshot table não contém PII

---

## Dependencies

### Entrada
- **MON-FN-007** (dunning): `dunning_lost` events para involuntary churn
- **MON-FN-006** (eventos funil): `trial_started`, `trial_converted`
- **MON-FN-008** (free tier): `smartlic_free` count
- Stripe API key (read-only)

### Saída
- Decisões pricing pós-n≥30: ARPU/MRR/churn como input crítico
- Investor reporting (futuro): dashboard reutilizável

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 8/10

### 10-Point Checklist

| # | Criterion | OK | Notes |
|---|---|---|---|
| 1 | Clear and objective title | Y | "ARPU / MRR / Churn Analytics Dashboard" — métricas explícitas |
| 2 | Complete description | Y | Sources of truth claras (Stripe API + plan_billing_periods + analytics_events) |
| 3 | Testable acceptance criteria | Y | 9 ACs incluindo edge case 0 active_paying division by zero |
| 4 | Well-defined scope (IN/OUT) | Y | IN/OUT explícitos; OUT exclui LTV/forecasting/multi-currency |
| 5 | Dependencies mapped | Y | Entrada MON-FN-007/006/008 + Stripe API; Saída pricing decisions pós-n≥30 |
| 6 | Complexity estimate | Y | M (3-4 dias) coerente — snapshots + cron + Stripe API + frontend Recharts |
| 7 | Business value | Y | "Decisões pricing pós-n≥30 requerem ARPU/MRR como input crítico" |
| 8 | Risks documented | Y | Stripe rate limit + bad data validation + key compromise |
| 9 | Criteria of Done | Y | n<30 banner + Sentry alert + Stripe key restrito read-only |
| 10 | Alignment with PRD/Epic | Y | EPIC P2 Sprint 6 + memory `feedback_n2_below_noise_eng_theater` aplicada |

### Observations
- **Score 8 reflete trade-offs explícitos no v1:** AC3 nota `mrr_expansion_cents=0` TODO (expansion/contraction MRR não detectados em v1; refine em iteração) — story self-bounds suas próprias limitações honestamente
- "Active at start of period" approximation (`active_paying + voluntary_churn + involuntary_churn` rough) é tradeoff pragmático
- n<30 noise warning corretamente integrado (banner + endpoint flag + Sentry tag)
- Stripe API key read-only (security) explicitamente em DoD
- Hybrid Stripe API (canonical MRR) + local DB (counts) trade-off documentado
- Migration paired `.down.sql`
- `subscription_cancelled` event adicionado para alimentar churn (v1 closure)

---

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — financial dashboard MRR/ARPU/churn | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (8/10). P2 dashboard v1 com trade-offs honestos (expansion/contraction MRR TODO); Status Draft → Ready. | @po (Pax) |
