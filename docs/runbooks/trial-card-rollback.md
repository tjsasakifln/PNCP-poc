# Runbook — Trial Card Rollback

**Story:** STORY-CONV-003c AC5
**Related:** STORY-CONV-003a (backend signup + Stripe), STORY-CONV-003b (frontend PaymentElement + A/B rollout)
**Last updated:** 2026-04-20

---

## Quando acionar este runbook

Dispare rollback do coleta-de-cartão quando QUALQUER um destes triggers for observado em produção:

| Trigger | Threshold | Fonte |
|---------|-----------|-------|
| **Conversion rate drop** | Queda ≥50% em 7 dias vs baseline pré-rollout | Mixpanel funnel `signup_attempted → signup_completed` por `rollout_branch` |
| **Chargeback rate** | > 1% dos signups com cartão em 30 dias | Stripe dashboard `balance.dispute_funds_withdrawn` |
| **Payment failure spike** | > 20% dos `signup_completed` com `subscription_status=payment_failed` em 24h | `smartlic_trial_charge_failed_total` Prometheus / Sentry tag `signup_payment_failed` |
| **Suporte overwhelmed** | > 5 tickets/dia sobre "cobrança indevida" ou "cartão debitado no trial" | Email/chat inbox |
| **Regulatório** | Notificação Procon/ANS/CDC ou órgão equivalente | Legal escalation |

**Escalação imediata (P0 — sem espera por consenso):**
- Chargeback > 2% ou fraud detected por Stripe Radar → rollback **agora** + freeze novos signups até causa raiz.

---

## Ação de rollback — 30 segundos

### Passo 1 — Desligar o A/B rollout

```bash
# Railway (frontend service)
railway variables set NEXT_PUBLIC_TRIAL_REQUIRE_CARD_ROLLOUT_PCT=0 \
  --service smartlic-frontend
```

A branch `card` lê essa env var em runtime via `useRolloutBranch.ts` (hash % 100 < pct). `PCT=0` força TODOS os novos signups para o branch `legacy` (Supabase direct, sem cartão).

> **Nota:** Next.js `NEXT_PUBLIC_*` vars são inlineadas no build. Em staging/prod o frontend precisa re-deploy para que a var nova seja lida — OU o código lê `process.env` em runtime (nosso caso via `readRolloutPctFromEnv`). Validate com `curl` em passo 4.

### Passo 2 — Validar que o rollout caiu a zero

Dentro de 5 minutos da env var set:

```bash
# Mixpanel (via API ou dashboard)
# Query: últimas 30min, filtro event=signup_completed, breakdown por rollout_branch
# Esperado: rollout_branch=legacy counts crescendo, rollout_branch=card → 0
```

Alternativa via curl em /signup:

```bash
# Deve retornar HTML sem <div data-testid="signup-step-2-card">
curl -s https://smartlic.tech/signup | grep -c 'data-testid="signup-step-2-card"'
# Esperado: 0
```

### Passo 3 — Signups em trialing ativo NÃO são afetados

- Usuários que já completaram signup com cartão mantêm sua subscription Stripe `trialing` normalmente.
- Stripe continua o charge em D+14 conforme agendado.
- **NÃO cancelar subscriptions existentes** — isso geraria refunds desnecessários e confusão.
- Se a causa raiz exigir cancelamento em massa, seguir sub-processo "Mass cancel" abaixo (requires user approval).

### Passo 4 — Comunicação

- Post em `#incidents-live` (Slack) com: trigger observado, timestamp, env var alterada, impacto estimado.
- Update status page se impacto for user-visible (`smartlic.tech/status`).
- Abrir issue no backlog `INCIDENT-trial-card-rollback-{YYYY-MM-DD}` com link para este runbook.

---

## Root cause investigation

Após rollback estabilizar, investigar em paralelo:

1. **Stripe Dashboard > Payments** — filtrar `metadata.flow=pre_signup_trial` últimos 7 dias. Identificar padrões (issuer declines, CVV mismatches, 3DS failures).
2. **Sentry** — filtro tag `signup_payment_failed` + breadcrumb `stripe.SetupIntent.create` + `stripe.Subscription.create`.
3. **Mixpanel** — funnel completeness `signup_attempted → trial_card_captured → signup_completed` por `rollout_branch`. Gaps apontam onde usuários caem.
4. **Backend logs (Railway)** — grep `StripeSignupError` + `step=` para triangular qual sub-passo falha (customer_create, pm_attach, subscription_create).
5. **Chargeback codes Stripe** — se rollback foi por chargeback, classificar por `reason` (fraudulent, product_not_received, subscription_canceled). "Fraudulent" = fraud signal; "product_not_received" = UX (usuários esqueceram que assinaram).

---

## Mass cancel — apenas sob escalação explícita

**Pré-requisitos:** user (founder) autoriza por escrito (Slack/email); causa raiz identificada e documentada.

```python
# backend/scripts/mass_cancel_trials.py (não commitado — criar ad-hoc)
import stripe
from datetime import datetime, timezone, timedelta

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

# Buscar subscriptions trialing criadas em window do incidente
start = datetime(2026, X, X, tzinfo=timezone.utc)
end = datetime(2026, X, X, tzinfo=timezone.utc)

subs = stripe.Subscription.list(
    status="trialing",
    created={"gte": int(start.timestamp()), "lte": int(end.timestamp())},
    limit=100,
)

for sub in subs.auto_paging_iter():
    # Log antes de cancelar — audit trail
    print(f"Cancelling {sub.id} (customer={sub.customer}, trial_end={sub.trial_end})")
    stripe.Subscription.cancel(sub.id)
```

**Pós mass cancel:**
- Email de esclarecimento para todos os usuários afetados (template `trial_cancelled_by_incident.html` — criar).
- Atualizar `profiles.subscription_status='canceled_incident'` via backfill SQL.
- Postmortem 5-why em `docs/postmortems/YYYY-MM-DD-trial-card-incident.md`.

---

## Re-rollout (quando voltar)

Após root cause fix + 7 dias estabilizado:

1. Staging: `NEXT_PUBLIC_TRIAL_REQUIRE_CARD_ROLLOUT_PCT=100` durante 48h com equipe testando signups.
2. Prod canary: `PCT=5` por 72h. Monitorar funnel + chargebacks diários.
3. Prod ratchet: 5→15→30→50 em incrementos de 7 dias cada, com GO/NO-GO daily review.
4. Parar ratchet se qualquer trigger acima for observado.

---

## Observabilidade esperada (AC4 — a ser shipado)

- Prometheus: `smartlic_trial_signup_with_card_total{branch}`, `smartlic_trial_cancel_before_charge_total`, `smartlic_trial_auto_converted_total`, `smartlic_trial_charge_failed_total`
- Mixpanel events: `trial_card_captured`, `trial_cancelled_before_charge`, `trial_converted_auto`, `trial_charge_failed`
- Dashboard admin: `/admin/billing/trial-funnel` (deferido — STORY-CONV-003c AC4)

Até o dashboard chegar, usar queries Mixpanel manuais via dashboard.mixpanel.com + Stripe Dashboard para dispute rate.

---

## Change log

- **2026-04-20** — Runbook criado (@dev flickering-llama session, Opus 4.7). Ainda sem incidentes — doc preventivo antes do primeiro rollout em prod.
