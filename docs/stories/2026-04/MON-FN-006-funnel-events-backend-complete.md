# MON-FN-006: 8 Eventos Funil Backend Completos (first_search → paid)

**Priority:** P0
**Effort:** L (5-7 dias)
**Squad:** @dev + @data-engineer
**Status:** Ready
**Epic:** [EPIC-MON-FN-2026-Q2](EPIC-MON-FN-2026-Q2.md)
**Sprint:** 2-3 (06–19/mai)
**Sprint Window:** Sprint 2-3 (depende de MON-FN-005)
**Dependências bloqueadoras:** MON-FN-005 (Mixpanel garantidamente init em prod)

---

## Contexto

Funil de monetização completo (do EPIC) tem **12 eventos**:
```
signup_started → signup_completed → onboarding_completed → first_search
  → paywall_hit → checkout_started → checkout_completed → trial_started
  → trial_expiring_d3 → trial_expiring_d1 → trial_expired | trial_converted
  → payment_failed | dunning_started → dunning_recovered | dunning_lost
```

Inventory atual (grep `track_funnel_event`):
- `paywall_hit` — emitido em `quota/plan_auth.py:67-75, 96-104, 135-144` (3 razões: dunning_blocked, dunning_grace_period, trial_expired). Existe.
- `signup_completed`, `signup_started` — frontend (Mixpanel JS). Existe.
- `trial_started` — emitido **parcialmente** em `webhooks/handlers/subscription.py::_emit_trial_started_event`. Verificar completeza.
- `payment_failed` — emitido **parcialmente** em `webhooks/handlers/invoice.py` (envia email mas não Mixpanel event consistente).

**Faltantes (8 eventos):**
1. `first_search` — server-side em `backend/routes/search/__init__.py` POST handler
2. `trial_started` — completar emissão consistente
3. `trial_expiring_d3` — ARQ cron diário detecta `trial_expires_at = now()+3d`
4. `trial_expiring_d1` — ARQ cron mesmo, +1d
5. `trial_expired` — ARQ cron quando `trial_expires_at < now()` AND `plan_type='free_trial'`
6. `checkout_started` — `routes/billing.py::create_checkout_session` antes de retornar URL Stripe
7. `payment_failed` — completar em `webhooks/handlers/invoice.py::_handle_invoice_payment_failed`
8. `trial_converted` — `webhooks/handlers/invoice.py::_handle_invoice_payment_succeeded` quando plan transition trial→paid

Memory `reference_mixpanel_backend_token_gap_2026_04_24` documenta que essa cegueira já durou. Sem completude, funil Mixpanel mostra dropout fictício (eventos faltantes parecem dropout real).

**Por que P0:** sem funnel completo, decisões editoriais SEO (EPIC B) e priorização produto são especulativas. n=2 baseline atual já é precário; tracking gap seria fatal.

**Paths críticos (8+ files):**
- `backend/routes/search/__init__.py` (POST /buscar)
- `backend/routes/billing.py` (create_checkout_session)
- `backend/webhooks/handlers/{subscription,invoice}.py`
- `backend/cron/billing.py` ou novo `backend/cron/trial_lifecycle.py`
- `backend/analytics_events.py` (já existe; usar como API)
- `supabase/migrations/` (nova tabela `analytics_events` para audit)
- `backend/schemas/profile.py` (campo `first_search_at`)

---

## Acceptance Criteria

### AC1: Tabela `analytics_events` (audit + retention 90d)

Given que Mixpanel é fonte primária mas pode quota-out,
When evento é emitido,
Then também grava em DB local para audit + replay.

- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_create_analytics_events.sql`:
```sql
CREATE TABLE public.analytics_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  event_name text NOT NULL,
  properties jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  ingested_at timestamptz NOT NULL DEFAULT now(),
  source text NOT NULL DEFAULT 'backend',  -- backend | frontend | webhook | cron
  mixpanel_synced boolean NOT NULL DEFAULT false
);
CREATE INDEX idx_analytics_events_user_occurred ON public.analytics_events (user_id, occurred_at DESC);
CREATE INDEX idx_analytics_events_event_occurred ON public.analytics_events (event_name, occurred_at DESC);
CREATE INDEX idx_analytics_events_unsynced ON public.analytics_events (ingested_at) WHERE mixpanel_synced = false;

-- RLS: user reads own; service-role full
ALTER TABLE public.analytics_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users read own analytics_events" ON public.analytics_events
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Service role full" ON public.analytics_events
  FOR ALL USING (auth.role() = 'service_role');

-- pg_cron: purge >90 days
SELECT cron.schedule('purge-analytics-events',
  '0 8 * * *',
  $$DELETE FROM public.analytics_events WHERE occurred_at < now() - interval '90 days'$$);
```
- [ ] Migration paired down `.down.sql` (DROP TABLE + cron.unschedule)
- [ ] STORY-1.1 monitora cron via `cron_job_health` view (já existe)

### AC2: Modificar `track_funnel_event` para gravar audit

Given chamada `track_funnel_event(event_name, user_id, properties)`,
When fire,
Then também INSERT em `analytics_events` (best-effort, não bloqueia Mixpanel send).

- [ ] Em `backend/analytics_events.py:63` modificar:
```python
def track_funnel_event(
    event_name: str,
    user_id: str,
    properties: dict[str, Any] | None = None,
    variant: str | None = None,
) -> None:
    """Track conversion funnel event with audit trail. Fire-and-forget."""
    try:
        props = dict(properties) if properties else {}
        props["user_id"] = user_id
        # ... existing enrichment (engagement_tier, ab_variants, etc.) ...

        track_event(event_name, props)

        # MON-FN-006: audit to DB (best-effort)
        _audit_to_db(event_name, user_id, props)
    except Exception:
        pass

def _audit_to_db(event_name: str, user_id: str, properties: dict) -> None:
    """Best-effort audit insert. Never blocks. Spawned as fire-and-forget thread."""
    import threading
    def _insert():
        try:
            from supabase_client import get_supabase
            sb = get_supabase()
            sb.table("analytics_events").insert({
                "user_id": user_id,
                "event_name": event_name,
                "properties": properties,
                "source": "backend",
            }).execute()
        except Exception as e:
            logger.debug(f"analytics_events audit insert failed: {e}")
    threading.Thread(target=_insert, daemon=True).start()
```
- [ ] Counter `smartlic_analytics_events_emitted_total{event_name, source}`
- [ ] Counter `smartlic_analytics_events_audit_failed_total` (DB insert failure rate)
- [ ] Test: 1000 events emitidos → 1000 rows em DB (eventual consistency 1s)

### AC3: Evento `first_search` server-side

Given user (`profiles.first_search_at IS NULL`) faz POST /buscar bem-sucedido,
When response 202,
Then emit `first_search` event + UPDATE `profiles.first_search_at = now()`.

- [ ] Migration adiciona coluna `first_search_at timestamptz` em `profiles` (se não existir):
```sql
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS first_search_at timestamptz;
```
- [ ] Em `backend/routes/search/__init__.py` POST handler:
```python
# After successful pipeline dispatch (return 202), before returning:
async def _maybe_emit_first_search(user_id: str, search_id: str) -> None:
    """Emit first_search event idempotently. UPDATE profiles.first_search_at."""
    try:
        from supabase_client import get_supabase
        sb = get_supabase()
        # Atomic check-and-set
        result = sb.table("profiles").update({
            "first_search_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", user_id).is_("first_search_at", "null").execute()

        if result.data:  # affected rows > 0 means we just set it now
            track_funnel_event("first_search", user_id, properties={
                "search_id": search_id,
                "via": "buscar_endpoint",
            })
    except Exception as e:
        logger.debug(f"first_search emit failed: {e}")
```
- [ ] Idempotência via `WHERE first_search_at IS NULL` (atomic)
- [ ] Race condition: dois requests concorrentes na mesma sessão — só primeiro UPDATE succeeds
- [ ] Test: hit /buscar 5x para mesmo user → 1 evento `first_search` apenas

### AC4: Evento `trial_started` (completar)

Given `customer.subscription.created` com `trial_end > now()`,
When webhook handler processa,
Then emit `trial_started` em `track_funnel_event`.

- [ ] Verificar `_emit_trial_started_event` em `backend/webhooks/handlers/subscription.py` — completar se necessário:
```python
def _emit_trial_started_event(user_id: str, subscription: dict) -> None:
    track_funnel_event("trial_started", user_id, properties={
        "stripe_subscription_id": subscription.get("id"),
        "plan_id": subscription.get("metadata", {}).get("plan_id"),
        "trial_end_ts": subscription.get("trial_end"),
        "trial_days": (subscription.get("trial_end") - subscription.get("created")) // 86400 if subscription.get("trial_end") else None,
    })
```
- [ ] Idempotência: usar `stripe_webhook_events` (STORY-307) — mesmo subscription.created não dispara 2x
- [ ] Test: replay webhook 2x → único evento `trial_started`

### AC5: Eventos `trial_expiring_d3`, `trial_expiring_d1`, `trial_expired` (ARQ cron)

Given trial users com `trial_expires_at` próximo,
When cron diário roda (07 UTC = 04 BRT),
Then emite eventos correspondentes em janelas de 24h.

- [ ] Novo `backend/cron/trial_lifecycle.py`:
```python
import asyncio
from datetime import datetime, timezone, timedelta
from cron._loop import daily_loop, acquire_redis_lock, release_redis_lock

LOCK_KEY = "smartlic:trial_lifecycle:lock"
LOCK_TTL = 30 * 60

async def trial_lifecycle_job() -> dict:
    """Daily job emitting trial_expiring_d3, trial_expiring_d1, trial_expired events."""
    lock_acquired = await acquire_redis_lock(LOCK_KEY, LOCK_TTL)
    if not lock_acquired:
        return {"status": "skipped"}
    try:
        from supabase_client import get_supabase
        from analytics_events import track_funnel_event

        sb = get_supabase()
        now = datetime.now(timezone.utc)
        results = {"d3": 0, "d1": 0, "expired": 0}

        # D-3 — trial expires in 3 days (window: 72-96h ahead)
        d3_users = sb.table("profiles").select("id, trial_expires_at, plan_type") \
            .eq("plan_type", "free_trial") \
            .gte("trial_expires_at", (now + timedelta(days=3)).isoformat()) \
            .lt("trial_expires_at", (now + timedelta(days=4)).isoformat()) \
            .execute()
        for u in d3_users.data or []:
            track_funnel_event("trial_expiring_d3", u["id"], properties={
                "trial_expires_at": u["trial_expires_at"],
            })
            results["d3"] += 1

        # D-1 — trial expires in 1 day
        d1_users = sb.table("profiles").select("id, trial_expires_at, plan_type") \
            .eq("plan_type", "free_trial") \
            .gte("trial_expires_at", (now + timedelta(days=1)).isoformat()) \
            .lt("trial_expires_at", (now + timedelta(days=2)).isoformat()) \
            .execute()
        for u in d1_users.data or []:
            track_funnel_event("trial_expiring_d1", u["id"], properties={
                "trial_expires_at": u["trial_expires_at"],
            })
            results["d1"] += 1

        # Expired — trial_expires_at < now() AND plan still free_trial
        expired_users = sb.table("profiles").select("id, trial_expires_at") \
            .eq("plan_type", "free_trial") \
            .lt("trial_expires_at", now.isoformat()) \
            .execute()
        for u in expired_users.data or []:
            track_funnel_event("trial_expired", u["id"], properties={
                "trial_expires_at": u["trial_expires_at"],
                "days_overdue": (now - datetime.fromisoformat(u["trial_expires_at"].replace("Z", "+00:00"))).days,
            })
            results["expired"] += 1

        return results
    finally:
        await release_redis_lock(LOCK_KEY)
```
- [ ] Idempotência: tabela `trial_lifecycle_events_log` (user_id, event_name, sent_at) com UNIQUE constraint para evitar duplicatas em re-execução
- [ ] Cron schedule: 09 UTC daily (after dunning if any)
- [ ] Registrar em `backend/job_queue.py::WorkerSettings`

### AC6: Evento `checkout_started`

Given user clica "Pagar" → `POST /v1/billing/checkout`,
When endpoint cria session Stripe,
Then emit `checkout_started` ANTES de retornar URL.

- [ ] Em `backend/routes/billing.py::create_checkout_session`:
```python
@router.post("/v1/billing/checkout")
async def create_checkout_session(
    request: CheckoutRequest,
    user: User = Depends(require_auth),
):
    # ... create stripe session ...
    session = stripe.checkout.Session.create(...)

    # MON-FN-006: emit checkout_started BEFORE returning URL
    track_funnel_event("checkout_started", user["id"], properties={
        "stripe_session_id": session.id,
        "plan_id": request.plan_id,
        "billing_period": request.billing_period,  # mensal | semestral | anual
        "amount_cents": session.amount_total,
        "currency": session.currency,
    })

    return {"checkout_url": session.url, "session_id": session.id}
```
- [ ] Mesmo se Stripe `Session.create` falhar, **não emitir** `checkout_started` (somente em sucesso da intent — não em erro de criação)
- [ ] Test: 1 user → 1 click → 1 evento `checkout_started`

### AC7: Evento `payment_failed` consistente

Given `invoice.payment_failed` webhook,
When handler processa,
Then emit `payment_failed` (já envia email — adicionar event Mixpanel).

- [ ] Em `backend/webhooks/handlers/invoice.py::_handle_invoice_payment_failed`:
```python
async def handle_invoice_payment_failed(sb, event):
    invoice = event.data.object
    user_id = await _resolve_user_id(sb, invoice.customer)
    if not user_id:
        return
    # ... existing email send logic ...

    # MON-FN-006: emit funnel event
    track_funnel_event("payment_failed", user_id, properties={
        "stripe_invoice_id": invoice.id,
        "amount_cents": invoice.amount_due,
        "currency": invoice.currency,
        "attempt_count": invoice.attempt_count,
        "next_payment_attempt_ts": invoice.next_payment_attempt,
    })
```
- [ ] Idempotência via `stripe_webhook_events` (já cobre)

### AC8: Evento `trial_converted`

Given `invoice.payment_succeeded` AND user previously `plan_type='free_trial'`,
When transition trial→paid,
Then emit `trial_converted`.

- [ ] Em `backend/webhooks/handlers/invoice.py::_handle_invoice_payment_succeeded`:
```python
async def handle_invoice_payment_succeeded(sb, event):
    invoice = event.data.object
    user_id = await _resolve_user_id(sb, invoice.customer)
    if not user_id:
        return

    # Check pre-state
    profile = sb.table("profiles").select("plan_type").eq("id", user_id).single().execute()
    was_trial = profile.data and profile.data["plan_type"] == "free_trial"

    # ... existing logic to update plan_type ...

    if was_trial:
        track_funnel_event("trial_converted", user_id, properties={
            "stripe_invoice_id": invoice.id,
            "amount_cents": invoice.amount_paid,
            "billing_period": invoice.lines.data[0].plan.interval if invoice.lines.data else None,
        })
```
- [ ] Test: webhook sequence trial_started → invoice.payment_succeeded → assert `trial_converted` event emitido

### AC9: Métricas Prometheus + Sentry

- [ ] Counter `smartlic_funnel_events_emitted_total{event_name}`
- [ ] Histograma `smartlic_funnel_events_db_audit_duration_seconds` (latência insert audit)
- [ ] Sentry tag `funnel_event=<event_name>` em qualquer exception em `track_funnel_event`
- [ ] Dashboard Grafana: "Funnel Events Last 24h" mostrando rate por event_name

### AC10: Testes (unit + integration + E2E)

- [ ] Unit `backend/tests/analytics/test_funnel_events.py`:
  - [ ] `track_funnel_event` chama Mixpanel + audit DB
  - [ ] Audit DB falha → Mixpanel send ainda funciona (best-effort isolation)
  - [ ] Mixpanel falha → audit DB ainda grava (best-effort isolation)
  - [ ] Concorrência: 100 emits paralelos → 100 rows em DB
- [ ] Integration `backend/tests/cron/test_trial_lifecycle.py`:
  - [ ] D-3 user → emit `trial_expiring_d3` once
  - [ ] D-1 user → emit `trial_expiring_d1` once
  - [ ] Expired user (1d ago) → emit `trial_expired`
  - [ ] Re-run mesmo dia → no duplicates (UNIQUE constraint)
- [ ] Integration `backend/tests/routes/test_first_search_event.py`:
  - [ ] First /buscar request → event emitted + `profiles.first_search_at` set
  - [ ] Second /buscar request → no event
  - [ ] Concurrent requests → 1 event only (atomic UPDATE)
- [ ] Integration `backend/tests/webhooks/test_trial_converted_event.py`:
  - [ ] free_trial user → invoice.payment_succeeded → `trial_converted` emitted
  - [ ] paid user → invoice.payment_succeeded → no `trial_converted` (already paid)
- [ ] E2E Playwright `frontend/e2e-tests/funnel-flow.spec.ts`:
  - [ ] Signup → first_search → paywall_hit → checkout_started → checkout_completed → trial_started visíveis em Mixpanel API
- [ ] Cobertura ≥85% nas linhas tocadas

---

## Scope

**IN:**
- Tabela `analytics_events` audit + retention 90d
- 8 eventos backend faltantes implementados
- ARQ cron `trial_lifecycle_job`
- Idempotência via UNIQUE constraints + atomic UPDATEs
- Métricas Prometheus
- Schema migration paired

**OUT:**
- Frontend events (signup_started, signup_completed, onboarding_completed) — já existentes, não rewrite
- Mixpanel cohort import (manual via Mixpanel UI)
- BigQuery export (futuro)
- Reverse ETL Mixpanel → DB (Mixpanel é primary; DB é audit)
- Eventos não-funil (page_view, button_click) — fora de escopo
- Refactor enrichment logic em `track_funnel_event` (já enriquece com cohort; não mexer)

---

## Definition of Done

- [ ] Migration `analytics_events` aplicada em prod
- [ ] Coluna `profiles.first_search_at` adicionada
- [ ] Cron `purge-analytics-events` rodando (validar via `cron_job_health` view)
- [ ] 8 eventos visíveis em Mixpanel Live View (signup → trial_converted)
- [ ] Audit table `analytics_events` populada (samples nos últimos 24h)
- [ ] Counter `smartlic_funnel_events_emitted_total{event_name}` exposto
- [ ] Cobertura ≥85% nas linhas tocadas
- [ ] CodeRabbit clean
- [ ] Funnel Mixpanel completo configurado (UI Mixpanel) — screenshot anexo na PR
- [ ] Cron `trial_lifecycle_job` registrado em ARQ (verificar via `arq job_queue.WorkerSettings`)
- [ ] Tabela `trial_lifecycle_events_log` UNIQUE constraint testada
- [ ] Operational runbook para investigar discrepância DB vs Mixpanel
- [ ] Memory existente atualizada referenciando funnel completion

---

## Dev Notes

### Padrões existentes a reutilizar

- **`track_funnel_event` API:** `backend/analytics_events.py:63` — já enriquece com cohort + ab_variants. NÃO reescrever; apenas adicionar audit DB.
- **ARQ cron pattern:** `backend/cron/billing.py::run_reconciliation` (lock Redis + daily loop)
- **`stripe_webhook_events` idempotência:** STORY-307 — webhook handlers automaticamente idempotent
- **Migration patterns:** `supabase/migrations/` paired down.sql obrigatório (STORY-6.2)

### Funções afetadas

- `backend/analytics_events.py:63-109` (track_funnel_event + audit helper)
- `backend/routes/search/__init__.py` (first_search emit)
- `backend/routes/billing.py::create_checkout_session` (checkout_started emit)
- `backend/webhooks/handlers/subscription.py` (trial_started complete)
- `backend/webhooks/handlers/invoice.py::_handle_invoice_payment_failed` (payment_failed emit)
- `backend/webhooks/handlers/invoice.py::_handle_invoice_payment_succeeded` (trial_converted emit)
- `backend/cron/trial_lifecycle.py` (NOVO)
- `backend/job_queue.py::WorkerSettings` (registrar cron)
- `backend/metrics.py` (counters)
- `supabase/migrations/YYYYMMDDHHMMSS_create_analytics_events.sql` + `.down.sql`
- `supabase/migrations/YYYYMMDDHHMMSS_add_first_search_at.sql` + `.down.sql`
- `supabase/migrations/YYYYMMDDHHMMSS_create_trial_lifecycle_events_log.sql` + `.down.sql`

### Idempotência: por que `trial_lifecycle_events_log`

Cron pode rodar 2x no mesmo dia (Railway redeploy + manual trigger). Mixpanel deduplica por `insert_id` (Mixpanel SDK envia automaticamente) MAS:
- Sem `insert_id` consistente, dedup falha
- Tabela log permite query "user X recebeu evento Y hoje?" antes de emit
- Schema: `(user_id, event_name, sent_at_date)` com UNIQUE

```sql
CREATE TABLE public.trial_lifecycle_events_log (
  user_id uuid NOT NULL,
  event_name text NOT NULL,
  sent_at_date date NOT NULL DEFAULT CURRENT_DATE,
  sent_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, event_name, sent_at_date)
);
```

### Testing Standards

- Test files em `backend/tests/{analytics,cron,routes,webhooks}/`
- Mock Mixpanel via `@patch("analytics_events._get_mixpanel")` — retorna MagicMock
- Mock Supabase via `supabase_client.get_supabase` patch
- `freezegun` para tests de cron lifecycle
- Anti-hang: pytest-timeout 30s; ARQ jobs em test usam `asyncio.wait_for(timeout=10)`
- Cobertura focada em `track_funnel_event` paths + cron lifecycle

---

## Risk & Rollback

### Triggers de rollback
- Mixpanel quota exceeded (free tier 100k events/mês — monitorar)
- DB insert audit causando lock em `analytics_events` (índices wrong)
- Cron `trial_lifecycle` emitindo duplicatas (UNIQUE violation)
- `first_search` event missing pós-deploy (signal regression)

### Ações de rollback
1. **Imediato:** env var `ANALYTICS_AUDIT_DB_ENABLED=false` — Mixpanel mantém, audit pula
2. **Cron-level:** desabilitar `trial_lifecycle_job` via `TRIAL_LIFECYCLE_CRON_ENABLED=false`
3. **Mixpanel quota emergency:** sample non-critical events (`page_view` etc.) — mas TODOS funnel events permanecem 100%
4. **Schema:** down.sql disponível; preferir manter audit table mesmo em rollback (audit-positive)

### Compliance
- `analytics_events` contém PII (user_id) — incluir em LGPD export (MON-FN-010) e deletion (MON-FN-011)
- Retention 90d (cron purge automático)
- `properties` jsonb pode ter `email`, `name` em alguns eventos — sanitizar antes de insert se necessário (não logar PII em events Mixpanel-bound)

---

## Dependencies

### Entrada
- **MON-FN-005** (Mixpanel assertion): Mixpanel garantidamente init em prod
- **STORY-307** (stripe_webhook_events idempotência): handlers idempotent
- ARQ worker rodando

### Saída
- **MON-FN-007** (dunning workflow): consome `payment_failed` + `trial_expired` eventos para decidir cohorte dunning
- **MON-FN-008** (free tier downsell): emite `trial_downgraded_to_free` (extension futura desta story)
- **MON-FN-012** (cohort retention dashboard): consome `analytics_events` para SQL aggregations
- **MON-FN-013** (ARPU/MRR): consome `trial_converted`, `payment_failed` para churn rate
- **MON-FN-014** (onboarding tracking): server-side `first_search` substitui localStorage flag

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | OK | Notes |
|---|---|---|---|
| 1 | Clear and objective title | Y | "8 Eventos Funil Backend Completos (first_search → paid)" — quantificado |
| 2 | Complete description | Y | Inventory atual (4/12) + 8 faltantes listados explicitamente |
| 3 | Testable acceptance criteria | Y | 10 ACs cobrindo cada evento + idempotência + métricas + E2E Playwright |
| 4 | Well-defined scope (IN/OUT) | Y | IN/OUT explícitos; OUT exclui frontend events (já existentes) |
| 5 | Dependencies mapped | Y | Entrada MON-FN-005; Saída MON-FN-007/008/012/013/014 |
| 6 | Complexity estimate | Y | L (5-7 dias) coerente — 8 events + audit table + cron + tests |
| 7 | Business value | Y | "Decisões editoriais SEO especulativas sem funnel completo" |
| 8 | Risks documented | Y | Mixpanel quota + cron duplicates + DB lock; flag rollback granular |
| 9 | Criteria of Done | Y | 8 eventos visíveis em Mixpanel Live View + funnel screenshot na PR |
| 10 | Alignment with PRD/Epic | Y | EPIC gap #6 endereçado direto; Success Metric 1 (4/12 → 12/12) |

### Observations
- API canônica `track_funnel_event` respeitada em todos call sites — não há acesso direto Mixpanel SDK
- Tabela `analytics_events` com retention 90d alinhada com `cron_job_health` (STORY-1.1)
- Idempotência via `trial_lifecycle_events_log` UNIQUE constraint (cron re-runs no-op)
- Pattern atomic UPDATE `WHERE first_search_at IS NULL` para race condition first_search
- Best-effort audit DB via `threading.Thread(daemon=True)` mantém Mixpanel send rápido
- Migration paired `.down.sql` para 3 migrations (analytics_events, first_search_at, trial_lifecycle_events_log)

---

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — 8 eventos backend faltantes + audit table | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). P0 funnel backbone L effort; Status Draft → Ready. | @po (Pax) |
