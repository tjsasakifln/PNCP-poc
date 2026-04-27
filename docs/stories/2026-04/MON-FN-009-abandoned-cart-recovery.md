# MON-FN-009: Abandoned Cart Recovery (checkout.session.expired + Email)

**Priority:** P1
**Effort:** M (3-4 dias)
**Squad:** @dev
**Status:** Ready
**Epic:** [EPIC-MON-FN-2026-Q2](EPIC-MON-FN-2026-Q2.md)
**Sprint:** 4 (20–26/mai)
**Sprint Window:** Sprint 4 (depende de MON-FN-006)
**Dependências bloqueadoras:** MON-FN-006 (eventos `checkout_started` + audit funcional)

---

## Contexto

Stripe Checkout sessions expiram após **24h** por padrão (`checkout.session.expired` webhook). Hoje o handler em `backend/webhooks/stripe.py:190-194` apenas chama `_handle_founding_checkout_expired_raw` (cobre apenas founding leads) — **não há recovery genérico** para users que iniciaram checkout mas não completaram pagamento.

Benchmark: e-commerce/SaaS abandoned cart recovery emails recuperam **8-25%** dos carrinhos com 1 email D+1 + 1 reminder D+3. Para SmartLic com `n=2` baseline, qualquer recovery é incrementally significant — pre-revenue precisa cada conversão.

`backend/webhooks/handlers/founding.py::mark_founding_lead_abandoned` é o pattern existente de "abandoned" mas filtrado por metadata `founding=true`. Para recovery genérico:
- Precisamos guardar contexto do checkout (preço, plan_id, billing_period)
- Re-criar uma nova Stripe Checkout Session (não podemos "reabrir" expired)
- Email D+1 com link recovery + opcionalmente D+3 reminder
- Track recovery rate via Mixpanel (`abandoned_cart_recovered`)

**Por que P1:** com tráfego SEO inbound subindo (post-EPIC B), abandoned carts vão escalar — sem recovery, conversão é deixada na mesa. M effort, isolated.

**Paths críticos:**
- `backend/webhooks/stripe.py:190-194` (handler `checkout.session.expired`)
- `backend/webhooks/handlers/checkout.py` (estender; já handle completed/payment_*_succeeded/failed)
- `backend/services/billing.py::create_checkout_session` (re-cria session em recovery flow)
- `backend/cron/billing.py` ou novo (D+3 reminder cron)
- `supabase/migrations/` (tabela `abandoned_carts`)
- `backend/templates/emails/abandoned_cart_*.html`

---

## Acceptance Criteria

### AC1: Tabela `abandoned_carts`

Given que checkout expira,
When webhook handler processa,
Then INSERT em `abandoned_carts` (idempotente).

- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_create_abandoned_carts.sql`:
```sql
CREATE TABLE public.abandoned_carts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  stripe_session_id text NOT NULL UNIQUE,           -- original expired session
  plan_id text NOT NULL,
  billing_period text NOT NULL,                     -- mensal | semestral | anual
  amount_cents int NOT NULL,
  currency text NOT NULL DEFAULT 'BRL',
  expired_at timestamptz NOT NULL,
  recovery_session_id text,                          -- new Stripe session for recovery
  recovery_url text,                                 -- recovery checkout URL
  d1_email_sent_at timestamptz,
  d3_email_sent_at timestamptz,
  recovered_at timestamptz,                          -- if user pays via recovery flow
  recovered_via_session_id text,                    -- new session.id at recovery
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_abandoned_carts_user ON public.abandoned_carts (user_id);
CREATE INDEX idx_abandoned_carts_pending_d1 ON public.abandoned_carts (expired_at)
  WHERE d1_email_sent_at IS NULL AND recovered_at IS NULL;
CREATE INDEX idx_abandoned_carts_pending_d3 ON public.abandoned_carts (d1_email_sent_at)
  WHERE d3_email_sent_at IS NULL AND recovered_at IS NULL;

ALTER TABLE public.abandoned_carts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users read own abandoned_carts" ON public.abandoned_carts
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Service full" ON public.abandoned_carts FOR ALL USING (auth.role() = 'service_role');
```
- [ ] Migration paired down `.down.sql`

### AC2: Handler `checkout.session.expired` genérico

Given webhook `checkout.session.expired`,
When chega no dispatcher,
Then INSERT em `abandoned_carts` se user está autenticado E sessão tem metadata útil.

- [ ] Em `backend/webhooks/handlers/checkout.py` adicionar:
```python
async def handle_checkout_session_expired(sb, event):
    """STORY MON-FN-009: track abandoned carts for recovery flow.

    Existing founding lead handler (mark_founding_lead_abandoned) runs separately —
    this is a generic abandoned cart for ALL users.
    """
    session = event.data.object
    user_id = session.get("metadata", {}).get("user_id") or await _resolve_user_id_by_customer(sb, session.customer)

    if not user_id:
        logger.info(f"checkout.session.expired without user_id: {session.id}")
        return

    # Skip if recovered already (Stripe sometimes fires expired after pay)
    if session.payment_status == "paid":
        return

    sb.table("abandoned_carts").upsert({
        "user_id": user_id,
        "stripe_session_id": session.id,
        "plan_id": session.metadata.get("plan_id"),
        "billing_period": session.metadata.get("billing_period"),
        "amount_cents": session.amount_total,
        "currency": session.currency or "brl",
        "expired_at": datetime.fromtimestamp(session.expires_at, tz=timezone.utc).isoformat(),
    }, on_conflict="stripe_session_id").execute()

    smartlic_abandoned_cart_created_total.labels(plan_id=session.metadata.get("plan_id", "unknown")).inc()
    track_funnel_event("abandoned_cart_created", user_id, properties={
        "stripe_session_id": session.id,
        "plan_id": session.metadata.get("plan_id"),
        "amount_cents": session.amount_total,
    })
```
- [ ] Atualizar `backend/webhooks/stripe.py:190-194` dispatcher para chamar genérico ALÉM do founding (ambos rodam — founding-specific e generic):
```python
elif event.type == "checkout.session.expired":
    # Generic abandoned cart (MON-FN-009)
    await handle_checkout_session_expired(sb, event)
    # Founding-specific (existing STORY-BIZ-001)
    _handle_founding_checkout_expired_raw(sb, event.data.object)
```
- [ ] Integration test cobrindo ambos handlers chamados sem double-side-effect

### AC3: Cron D+1 — recovery email

Given `abandoned_carts` com `d1_email_sent_at IS NULL AND expired_at < now() - 24h`,
When cron diário roda,
Then envia email recovery com novo Stripe Checkout URL.

- [ ] Novo `backend/cron/abandoned_cart.py`:
```python
import os
from datetime import datetime, timezone, timedelta
from cron._loop import acquire_redis_lock, release_redis_lock

LOCK_KEY = "smartlic:abandoned_cart:lock"

async def abandoned_cart_recovery_job() -> dict:
    """Daily job: send D+1 and D+3 recovery emails for abandoned carts."""
    lock = await acquire_redis_lock(LOCK_KEY, 30 * 60)
    if not lock:
        return {"status": "skipped"}
    try:
        from supabase_client import get_supabase
        from services.billing import create_recovery_checkout_session
        sb = get_supabase()
        now = datetime.now(timezone.utc)
        results = {"d1_sent": 0, "d3_sent": 0, "errors": 0}

        # D+1: 24h after expiration
        d1_pending = sb.table("abandoned_carts").select("*") \
            .is_("d1_email_sent_at", "null") \
            .is_("recovered_at", "null") \
            .lte("expired_at", (now - timedelta(hours=24)).isoformat()) \
            .gte("expired_at", (now - timedelta(hours=72)).isoformat()) \
            .execute()

        for cart in d1_pending.data or []:
            try:
                # Check suppression list
                if await _is_suppressed(cart["user_id"]):
                    continue
                # Create new Stripe session for recovery
                recovery_session = create_recovery_checkout_session(
                    user_id=cart["user_id"],
                    plan_id=cart["plan_id"],
                    billing_period=cart["billing_period"],
                    abandoned_cart_id=cart["id"],
                )
                sb.table("abandoned_carts").update({
                    "d1_email_sent_at": now.isoformat(),
                    "recovery_session_id": recovery_session["session_id"],
                    "recovery_url": recovery_session["checkout_url"],
                }).eq("id", cart["id"]).execute()

                await _send_recovery_email(cart, recovery_session["checkout_url"], stage="d1")
                track_funnel_event("abandoned_cart_email_sent", cart["user_id"], properties={
                    "stage": "d1",
                    "plan_id": cart["plan_id"],
                })
                results["d1_sent"] += 1
            except Exception as e:
                logger.error(f"D+1 recovery email failed for cart {cart['id']}: {e}")
                results["errors"] += 1

        # D+3: 72h after expiration (only if D+1 sent and no recovery)
        d3_pending = sb.table("abandoned_carts").select("*") \
            .not_.is_("d1_email_sent_at", "null") \
            .is_("d3_email_sent_at", "null") \
            .is_("recovered_at", "null") \
            .lte("d1_email_sent_at", (now - timedelta(hours=48)).isoformat()) \
            .execute()

        for cart in d3_pending.data or []:
            try:
                if await _is_suppressed(cart["user_id"]):
                    continue
                # Reuse recovery_url from D+1 (Stripe sessions valid 24h, but for D+3 we need new)
                recovery_session = create_recovery_checkout_session(
                    user_id=cart["user_id"],
                    plan_id=cart["plan_id"],
                    billing_period=cart["billing_period"],
                    abandoned_cart_id=cart["id"],
                )
                sb.table("abandoned_carts").update({
                    "d3_email_sent_at": now.isoformat(),
                    "recovery_session_id": recovery_session["session_id"],
                    "recovery_url": recovery_session["checkout_url"],
                }).eq("id", cart["id"]).execute()
                await _send_recovery_email(cart, recovery_session["checkout_url"], stage="d3")
                track_funnel_event("abandoned_cart_email_sent", cart["user_id"], properties={
                    "stage": "d3",
                    "plan_id": cart["plan_id"],
                })
                results["d3_sent"] += 1
            except Exception as e:
                logger.error(f"D+3 recovery email failed for cart {cart['id']}: {e}")
                results["errors"] += 1

        return results
    finally:
        await release_redis_lock(LOCK_KEY)
```
- [ ] Cron 11 UTC daily (after dunning)
- [ ] Max 2 retries por cart (D+1 + D+3); não enviar D+5+ para evitar spam
- [ ] Idempotência via `d{N}_email_sent_at IS NULL` check

### AC4: Helper `create_recovery_checkout_session`

Given cart abandonado,
When precisamos novo Stripe session,
Then helper cria com metadata `recovery_of=<original_session_id>`.

- [ ] Em `backend/services/billing.py` adicionar:
```python
def create_recovery_checkout_session(
    user_id: str,
    plan_id: str,
    billing_period: str,
    abandoned_cart_id: str,
) -> dict:
    """Create new Stripe Checkout Session for cart recovery flow.

    Metadata 'recovery_of=<original_session_id>' links back to abandoned_carts row.
    """
    # ... lookup user email + customer_id ...
    # ... lookup price_id from plan_billing_periods ...

    session = stripe.checkout.Session.create(
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{FRONTEND_URL}/planos/obrigado?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}/planos?recovery_cancelled=1",
        metadata={
            "user_id": user_id,
            "plan_id": plan_id,
            "billing_period": billing_period,
            "recovery_of_cart_id": abandoned_cart_id,
        },
        subscription_data={
            "trial_period_days": 0,  # no trial — already had one
        },
    )
    return {"session_id": session.id, "checkout_url": session.url}
```

### AC5: Recovery completion: `checkout.session.completed` AND `metadata.recovery_of_cart_id`

Given user paga via recovery link,
When webhook completed chega com metadata recovery,
Then UPDATE `abandoned_carts.recovered_at = now()` + emit event.

- [ ] Em `backend/webhooks/handlers/checkout.py::handle_checkout_session_completed`:
```python
# After existing handler logic:
recovery_cart_id = session.metadata.get("recovery_of_cart_id")
if recovery_cart_id:
    sb.table("abandoned_carts").update({
        "recovered_at": datetime.now(timezone.utc).isoformat(),
        "recovered_via_session_id": session.id,
    }).eq("id", recovery_cart_id).execute()
    smartlic_abandoned_cart_recovered_total.labels(plan_id=session.metadata.get("plan_id")).inc()
    track_funnel_event("abandoned_cart_recovered", user_id, properties={
        "abandoned_cart_id": recovery_cart_id,
        "stripe_session_id": session.id,
        "amount_cents": session.amount_total,
    })
```

### AC6: Email templates D+1 e D+3

- [ ] Novo `backend/templates/emails/abandoned_cart_d1.html`:
  - Subject: `{{name}}, você esqueceu algo no SmartLic`
  - Tom: amigável, não pressivo
  - Conteúdo: "Você iniciou um plano e não finalizou. Aqui está o link para concluir:"
  - CTA: "Finalizar pagamento" → recovery_url
  - Footer: "Se mudou de ideia, ignore este email" + link unsubscribe (suppression)
- [ ] `abandoned_cart_d3.html`:
  - Subject: `Última chance — Sua oferta SmartLic expira hoje`
  - Tom: urgência leve
  - CTA mesmo + texto "Não enviaremos mais lembretes após este"

### AC7: Métricas + Sentry

- [ ] Counter `smartlic_abandoned_cart_created_total{plan_id}` (AC2)
- [ ] Counter `smartlic_abandoned_cart_email_sent_total{stage}` (AC3)
- [ ] Counter `smartlic_abandoned_cart_recovered_total{plan_id}` (AC5)
- [ ] Recovery rate query: `recovered_total / created_total` (alvo: >5% baseline)
- [ ] Sentry breadcrumb em recovery failure (Stripe Session.create error)

### AC8: Testes

- [ ] Unit `backend/tests/cron/test_abandoned_cart_recovery.py`:
  - [ ] Cart >24h sem D+1 → email enviado
  - [ ] Cart >72h sem D+3 (mas D+1 enviado) → email enviado
  - [ ] Recovered cart → skip
  - [ ] Suppressed user → skip
  - [ ] Re-run mesmo dia → no double-send (idempotência)
- [ ] Integration `backend/tests/webhooks/test_checkout_expired_recovery.py`:
  - [ ] Webhook expired → cart row criado
  - [ ] Webhook expired sem user_id → skip silently
  - [ ] Webhook expired payment_status=paid → skip (false positive)
  - [ ] Webhook completed com metadata recovery_of_cart_id → cart marcado recovered
- [ ] E2E (Stripe CLI):
  - [ ] `stripe trigger checkout.session.expired` → cart row + Mixpanel event
  - [ ] Avançar 24h (freezegun) + run cron → email + new session created
- [ ] Cobertura ≥85%

---

## Scope

**IN:**
- Tabela `abandoned_carts` + RLS
- Handler `checkout.session.expired` genérico (coexiste com founding)
- Cron D+1 + D+3 recovery emails
- Helper `create_recovery_checkout_session`
- Tracking via Mixpanel + Prometheus
- Email templates 2 stages
- Suppression list integration

**OUT:**
- D+5+ reminders (spam risk)
- SMS recovery (custo)
- A/B test de subject lines (n=2 impede)
- Discount code generation (Stripe coupons separado decision)
- In-app banner "you have abandoned cart" (apenas email)
- Personalized product recommendations no email
- Multi-language (pt-BR único)

---

## Definition of Done

- [ ] Migration aplicada
- [ ] Handler `checkout.session.expired` genérico implementado + coexiste com founding
- [ ] Cron `abandoned_cart_recovery_job` registrado em ARQ + executando
- [ ] 2 email templates criados + validados via send manual
- [ ] Stripe CLI: `stripe trigger checkout.session.expired` → cart row + event
- [ ] Avançar 24h (staging) → D+1 email recebido
- [ ] Counters expostos em /metrics
- [ ] Cobertura ≥85%
- [ ] CodeRabbit clean
- [ ] Operational runbook
- [ ] Sentry alert em high error rate (recovery email send failures)

---

## Dev Notes

### Padrões existentes a reutilizar

- **Founding lead handler:** `webhooks/handlers/founding.py::mark_founding_lead_abandoned` (existente)
- **Stripe Session.create:** `services/billing.py` já cria sessions
- **`acquire_redis_lock`:** `cron/_loop.py`
- **`send_email_async`:** `email_service.py:194`
- **`track_funnel_event`:** MON-FN-006

### Funções afetadas

- `backend/webhooks/stripe.py:190-194` (dispatcher: chamar generic + founding)
- `backend/webhooks/handlers/checkout.py` (NOVO `handle_checkout_session_expired` + UPDATE em completion)
- `backend/services/billing.py` (NOVO `create_recovery_checkout_session`)
- `backend/cron/abandoned_cart.py` (NOVO)
- `backend/templates/emails/abandoned_cart_{d1,d3}.html` (NOVO)
- `backend/job_queue.py::WorkerSettings` (registrar cron)
- `backend/metrics.py` (counters)
- `supabase/migrations/YYYYMMDDHHMMSS_create_abandoned_carts.sql` + `.down.sql`

### Trade-off: Stripe Session expiration default 24h

Stripe default expiration: 24h. Pode ser ajustado em `Session.create(expires_at=ts)` mas:
- Aumentar para 72h: user volta após 2 dias e link ainda funciona — mas perde sinal "abandoned"
- Manter 24h: clean signal "expired = abandoned"; recovery email cria new session

Decisão: manter 24h default; email recovery cria NEW session com 24h validity.

### Testing Standards

- Mock Stripe `stripe.checkout.Session.create` via `@patch`
- `freezegun` para avançar tempo entre cron runs
- Suppression check mock via `@patch("services.dunning._is_suppressed")` ou similar
- Cobertura: `pytest --cov=backend/cron/abandoned_cart.py --cov=backend/webhooks/handlers/checkout.py`
- Anti-hang: pytest-timeout 30s

---

## Risk & Rollback

### Triggers de rollback
- Email rate spam complaints (Resend account suspension risk)
- Recovery rate <1% após 30d (não justifica esforço)
- Stripe Session.create failures elevados (recovery quebra)
- False positives: emails enviados para users que pagaram fora-Stripe

### Ações de rollback
1. **Imediato:** `ABANDONED_CART_RECOVERY_ENABLED=false` — cron pula
2. **Email-only:** `ABANDONED_CART_EMAILS_ENABLED=false` — schema continua, sem envio
3. **Schema:** down.sql; manter table preferível (audit value)
4. **Communication:** se complaint rate spike, pause + investigate via Resend dashboard

### Compliance
- Email recovery contém oferta — não Spam (legítimo follow-up de relacionamento iniciado)
- LGPD: `abandoned_carts` incluído em export/deletion (MON-FN-010, MON-FN-011)
- Retention: 90d para recovered/abandoned-no-recovery; daily purge cron

---

## Dependencies

### Entrada
- **MON-FN-006** (eventos funil): `checkout_started` + audit DB
- **MON-FN-001** (Resend HMAC): suppression list
- Stripe webhook operacional
- `email_service.py` Resend integration

### Saída
- **MON-FN-013** (ARPU/MRR): recovery rate alimenta métrica conversion uplift
- **MON-FN-007** (dunning): pattern similar reutilizado

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 9/10

### 10-Point Checklist

| # | Criterion | OK | Notes |
|---|---|---|---|
| 1 | Clear and objective title | Y | "Abandoned Cart Recovery (checkout.session.expired + Email)" |
| 2 | Complete description | Y | Benchmark recovery 8-25% + cita pattern existente founding handler |
| 3 | Testable acceptance criteria | Y | 8 ACs incluindo Stripe CLI E2E + freezegun avançar 24h |
| 4 | Well-defined scope (IN/OUT) | Y | IN/OUT explícitos; OUT exclui SMS/discount/A/B (n=2) |
| 5 | Dependencies mapped | Y | Entrada MON-FN-006/001; Saída MON-FN-013/007 (pattern reuse) |
| 6 | Complexity estimate | Y | M (3-4 dias) coerente — handler + cron + helper + 2 templates |
| 7 | Business value | Y | "Pre-revenue precisa cada conversão" + ramp-up SEO inbound |
| 8 | Risks documented | Y | Spam complaints + recovery rate <1% rollback + Stripe failures |
| 9 | Criteria of Done | Y | Stripe CLI smoke test + Sentry alert em high error rate |
| 10 | Alignment with PRD/Epic | Y | EPIC sequencing Sprint 4; pattern reutilizado de founding |

### Observations
- Coexistência com `mark_founding_lead_abandoned` correta (ambos handlers rodam paralelos)
- D+1/D+3 cadência standard SaaS (não envia D+5+ — anti-spam)
- Trade-off Stripe Session 24h vs 72h documentado (manter 24h, recovery cria new session)
- Suppression list integrada
- Counter recovery rate: `recovered_total / created_total` com alvo >5%
- Migration paired `.down.sql`
- Recovery checkout session com `trial_period_days=0` (no double-trial)

### Observations (não-blocking)
- Note: padrão de score 9 (não 10) — story é completa mas é P1 com impact medindo via recovery rate baseline desconhecido (n=2). Score reflete inerente incerteza de rate até primeiros dados, não falta de quality.

---

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — abandoned cart recovery genérico (não-founding) | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (9/10). P1 recovery infra sólida; baseline rate desconhecido até primeiros runs; Status Draft → Ready. | @po (Pax) |
