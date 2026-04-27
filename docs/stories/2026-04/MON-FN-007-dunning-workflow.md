# MON-FN-007: Dunning Workflow (D+1, D+2, D+3, Suspend D+4)

**Priority:** P1
**Effort:** L (5-7 dias)
**Squad:** @dev + @data-engineer
**Status:** Ready
**Epic:** [EPIC-MON-FN-2026-Q2](EPIC-MON-FN-2026-Q2.md)
**Sprint:** 4-5 (20/mai–02/jun)
**Sprint Window:** Sprint 4-5 (depende de MON-FN-006)
**Dependências bloqueadoras:** MON-FN-006 (eventos `payment_failed` + audit table funcionais)

---

## Contexto

`backend/cron/billing.py:75-180` implementa **pre-dunning** (`check_pre_dunning_cards`) — detecta cartões expirando em 7 dias e envia warning. Não há **dunning workflow real** (recovery após payment fail). Env var `SUBSCRIPTION_GRACE_DAYS=3` declarada em `backend/config.py` mas sem ARQ job correspondente.

Stripe Smart Retries faz alguma recuperação built-in mas **não é Fortune-500-grade**: sem custom email cadence, sem evento granular por estágio, sem suspensão graceful, sem recovery rate measurável. Benchmark: dunning Fortune-500 recupera 15-30% de payment fails — n=2 atual sem nenhum recovery loop perde 100% por default.

`quota/plan_auth.py:55-114` já enforça `dunning_phase` (`grace_period`, `blocked`) — porém **a fonte do `dunning_phase` é ausente**: nenhum process altera esse campo em `profiles` ou tabela. Existe stub mas não populado.

Sequência alvo:
- **D+0** (`invoice.payment_failed` webhook) — registra `dunning_started`, status `past_due`, agenda D+1 email
- **D+1** — Email "Atualize seu pagamento. Acesso continua normal por 2 dias."
- **D+2** — Email "Seu acesso será limitado amanhã. Atualize agora."
- **D+3** — Email "Acesso suspenso. Atualize para reativar."  + transition `dunning_phase=grace_period` (read-only)
- **D+4** — `dunning_phase=blocked` + `plan_type=expired`. Evento `dunning_lost`.
- **A qualquer momento:** se `invoice.payment_succeeded` → `dunning_recovered` event + restore.

**Por que P1:** sem dunning, churn voluntário = churn total. Mesmo que n=2 hoje, infra precisa estar pronta antes de inbound ramp-up SEO.

**Paths críticos:**
- `backend/cron/billing.py` (adicionar `dunning_workflow_job`)
- `backend/services/dunning.py` ou `services/billing.py` (helpers + emails)
- `backend/webhooks/handlers/invoice.py::_handle_invoice_payment_failed/succeeded` (entry/exit dunning)
- `supabase/migrations/` (tabela `dunning_state`)
- `backend/templates/emails/dunning_*.html` (3 templates)

---

## Acceptance Criteria

### AC1: Tabela `dunning_state` (state machine persistente)

Given que dunning é state machine multi-day,
When evento entra,
Then state persiste em DB.

- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_create_dunning_state.sql`:
```sql
CREATE TABLE public.dunning_state (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  stripe_subscription_id text NOT NULL,
  status text NOT NULL CHECK (status IN ('active', 'past_due', 'grace_period', 'blocked', 'recovered', 'lost')),
  past_due_started_at timestamptz NOT NULL,
  d1_sent_at timestamptz,
  d2_sent_at timestamptz,
  d3_sent_at timestamptz,
  recovered_at timestamptz,
  lost_at timestamptz,
  attempt_count int NOT NULL DEFAULT 1,
  last_invoice_id text,
  last_failure_reason text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (user_id, stripe_subscription_id)
);
CREATE INDEX idx_dunning_state_status ON public.dunning_state (status, past_due_started_at);
CREATE INDEX idx_dunning_state_user ON public.dunning_state (user_id);

ALTER TABLE public.dunning_state ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users read own dunning_state" ON public.dunning_state FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Service full" ON public.dunning_state FOR ALL USING (auth.role() = 'service_role');
```
- [ ] Migration paired down `.down.sql`

### AC2: Entry: `invoice.payment_failed` → criar dunning state

Given webhook `invoice.payment_failed`,
When handler processa,
Then INSERT em `dunning_state` com status `past_due` (idempotente: ON CONFLICT DO UPDATE).

- [ ] Em `backend/webhooks/handlers/invoice.py::_handle_invoice_payment_failed`:
```python
async def handle_invoice_payment_failed(sb, event):
    invoice = event.data.object
    user_id = await _resolve_user_id(sb, invoice.customer)
    if not user_id:
        return

    sb.table("dunning_state").upsert({
        "user_id": user_id,
        "stripe_subscription_id": invoice.subscription,
        "status": "past_due",
        "past_due_started_at": datetime.now(timezone.utc).isoformat(),
        "attempt_count": invoice.attempt_count,
        "last_invoice_id": invoice.id,
        "last_failure_reason": invoice.last_finalization_error or "payment_failed",
    }, on_conflict="user_id,stripe_subscription_id").execute()

    track_funnel_event("dunning_started", user_id, properties={
        "stripe_invoice_id": invoice.id,
        "amount_cents": invoice.amount_due,
        "attempt_count": invoice.attempt_count,
    })

    # ... existing email send logic preserved ...
```
- [ ] Counter `smartlic_dunning_started_total{plan_id, billing_period}`

### AC3: Cron `dunning_workflow_job` diário

Given dunning_state com status `past_due` ou `grace_period`,
When cron roda diariamente,
Then envia email apropriado e transiciona state.

- [ ] Em `backend/cron/billing.py` (estender) ou novo `backend/cron/dunning.py`:
```python
GRACE_DAYS = int(os.getenv("SUBSCRIPTION_GRACE_DAYS", "3"))  # config existente

async def dunning_workflow_job() -> dict:
    """Daily dunning workflow: D+1/D+2/D+3 emails + state transitions.

    Cron schedule: 10 UTC daily (after trial_lifecycle_job at 09 UTC).
    Idempotent: D+N email only sent if d{N}_sent_at IS NULL.
    """
    lock = await acquire_redis_lock("smartlic:dunning:lock", 30 * 60)
    if not lock:
        return {"status": "skipped"}
    try:
        sb = get_supabase()
        now = datetime.now(timezone.utc)
        results = {"d1": 0, "d2": 0, "d3": 0, "blocked": 0, "lost": 0}

        # Fetch all active dunning states
        active = sb.table("dunning_state").select("*") \
            .in_("status", ["past_due", "grace_period"]) \
            .execute()

        for state in active.data or []:
            past_due_at = datetime.fromisoformat(state["past_due_started_at"].replace("Z", "+00:00"))
            days_since = (now - past_due_at).days

            if days_since >= 1 and not state["d1_sent_at"]:
                await _send_dunning_email(state["user_id"], "d1", state)
                _mark_sent(sb, state["id"], "d1_sent_at", now)
                results["d1"] += 1

            if days_since >= 2 and not state["d2_sent_at"]:
                await _send_dunning_email(state["user_id"], "d2", state)
                _mark_sent(sb, state["id"], "d2_sent_at", now)
                results["d2"] += 1

            if days_since >= 3 and not state["d3_sent_at"]:
                await _send_dunning_email(state["user_id"], "d3", state)
                _mark_sent(sb, state["id"], "d3_sent_at", now)
                # Transition to grace_period (read-only)
                sb.table("dunning_state").update({"status": "grace_period"}).eq("id", state["id"]).execute()
                results["d3"] += 1

            if days_since >= GRACE_DAYS + 1:  # D+4 default
                # Transition to blocked + downgrade plan
                sb.table("dunning_state").update({
                    "status": "blocked",
                    "lost_at": now.isoformat(),
                }).eq("id", state["id"]).execute()
                sb.table("profiles").update({
                    "plan_type": "expired",
                    "dunning_phase": "blocked",
                }).eq("id", state["user_id"]).execute()
                # Invalidate plan cache (MON-FN-003)
                await publish_plan_invalidation(state["user_id"], "expired")
                track_funnel_event("dunning_lost", state["user_id"], properties={
                    "days_since_failure": days_since,
                    "stripe_subscription_id": state["stripe_subscription_id"],
                })
                results["lost"] += 1
                smartlic_dunning_lost_total.labels(plan_id="unknown").inc()

        return results
    finally:
        await release_redis_lock("smartlic:dunning:lock")
```
- [ ] Cron schedule: 10 UTC daily (07 BRT)
- [ ] Registrar em `backend/job_queue.py::WorkerSettings.cron_jobs`
- [ ] Idempotência: `d{N}_sent_at IS NULL` check antes de send (re-runs no-op)

### AC4: Email templates D+1, D+2, D+3

Given que cada estágio tem mensagem diferente,
When email é enviado,
Then template apropriado é usado.

- [ ] Novo `backend/templates/emails/dunning_d1.html`:
  - Subject: `Atualize seu pagamento — SmartLic`
  - Tom: amigável, não-alarmista
  - CTA: "Atualizar método de pagamento" → Stripe Customer Portal URL
  - Mostrar: motivo da falha (último 4 dígitos cartão, mensagem Stripe se disponível)
- [ ] `dunning_d2.html`:
  - Subject: `Seu acesso ao SmartLic será limitado amanhã`
  - Tom: urgência média
  - CTA mesmo + link para suporte
- [ ] `dunning_d3.html`:
  - Subject: `Última chance — Acesso será suspenso hoje`
  - Tom: urgência máxima
  - CTA + alternativa: "Quer pausar a assinatura?" link
- [ ] Helper `services/dunning.py::_send_dunning_email(user_id, stage, state)`:
```python
async def _send_dunning_email(user_id: str, stage: str, state: dict) -> None:
    """Send dunning email; idempotent — caller checks state.d{N}_sent_at."""
    sb = get_supabase()
    profile = sb.table("profiles").select("email,name").eq("id", user_id).single().execute()
    if not profile.data:
        return
    template = render_template(f"dunning_{stage}.html", {
        "name": profile.data["name"],
        "portal_url": _stripe_customer_portal_url(state["stripe_subscription_id"]),
        "amount": state.get("last_invoice_amount"),
    })
    send_email_async(
        to=profile.data["email"],
        subject=DUNNING_SUBJECTS[stage],
        html=template,
        tags=[{"name": "category", "value": "dunning"}, {"name": "stage", "value": stage}],
    )
```
- [ ] Suppression list (MON-FN-001): skip se email em `email_suppression`
- [ ] Tag Resend `category=dunning, stage={d1,d2,d3}` para audit em webhook

### AC5: Recovery: `invoice.payment_succeeded` → exit dunning

Given user paga após dunning iniciado,
When webhook `invoice.payment_succeeded` chega,
Then atualiza state `recovered`, restore plan_type, emit event.

- [ ] Em `backend/webhooks/handlers/invoice.py::_handle_invoice_payment_succeeded`:
```python
async def handle_invoice_payment_succeeded(sb, event):
    invoice = event.data.object
    user_id = await _resolve_user_id(sb, invoice.customer)

    # Check if user was in dunning
    dunning = sb.table("dunning_state").select("*") \
        .eq("user_id", user_id) \
        .eq("stripe_subscription_id", invoice.subscription) \
        .in_("status", ["past_due", "grace_period", "blocked"]) \
        .single().execute()

    if dunning.data:
        sb.table("dunning_state").update({
            "status": "recovered",
            "recovered_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", dunning.data["id"]).execute()

        # Restore plan_type if was blocked
        if dunning.data["status"] == "blocked":
            sb.table("profiles").update({
                "plan_type": "smartlic_pro",  # or read from subscription metadata
                "dunning_phase": "healthy",
            }).eq("id", user_id).execute()
            await publish_plan_invalidation(user_id, "smartlic_pro")

        track_funnel_event("dunning_recovered", user_id, properties={
            "days_in_dunning": (datetime.now(timezone.utc) - datetime.fromisoformat(dunning.data["past_due_started_at"].replace("Z", "+00:00"))).days,
            "stripe_invoice_id": invoice.id,
        })
        smartlic_dunning_recovered_total.labels(plan_id="unknown").inc()

    # ... existing trial_converted logic preserved ...
```
- [ ] Recovery rate metric: `dunning_recovered_total / dunning_started_total` ratio (alvo Fortune-500: 0.15-0.30)

### AC6: Métricas Prometheus

- [ ] Counters:
  - `smartlic_dunning_started_total{plan_id}` (incrementa AC2)
  - `smartlic_dunning_recovered_total{plan_id}` (AC5)
  - `smartlic_dunning_lost_total{plan_id}` (AC3 D+4 transition)
  - `smartlic_dunning_email_sent_total{stage}` (d1|d2|d3)
- [ ] Gauge `smartlic_dunning_active{status}` (past_due|grace_period|blocked active counts)
- [ ] Histograma `smartlic_dunning_recovery_days` (dias entre `past_due_started_at` e `recovered_at`)

### AC7: Email-stop-on-recovery race condition

Given user paga D+1 mid-day antes do cron rodar,
When state já marca recovered,
Then cron skip (idempotência via status check).

- [ ] AC3 query filtra `IN ('past_due', 'grace_period')` — recovered não entram
- [ ] Test: simular mid-day recovery + run cron → no extra email sent

### AC8: Testes (unit + integration + cron simulation)

- [ ] Unit `backend/tests/cron/test_dunning_workflow.py`:
  - [ ] D+1 user → email enviado, `d1_sent_at` set
  - [ ] D+2 user → email enviado, `d2_sent_at` set, NÃO reenviar D+1
  - [ ] D+3 user → email + status='grace_period'
  - [ ] D+4 user → status='blocked', plan_type='expired', cache invalidated, event 'dunning_lost'
  - [ ] Recovered user mid-cron → exit (status='recovered', skip emails)
  - [ ] Re-run cron mesmo dia → no duplicate emails (idempotência via d{N}_sent_at)
- [ ] Integration `backend/tests/webhooks/test_dunning_state_transitions.py`:
  - [ ] `invoice.payment_failed` → INSERT dunning_state
  - [ ] `invoice.payment_succeeded` mid-dunning → status=recovered + plan restored
  - [ ] Multiple `payment_failed` events → idempotent (UPDATE only attempt_count)
- [ ] E2E (Stripe CLI simulation):
  - [ ] `stripe trigger invoice.payment_failed` → DB state criado
  - [ ] Avançar `freezegun` 4 dias + run cron → 3 emails sent + plan blocked
  - [ ] `stripe trigger invoice.payment_succeeded` → recovered
- [ ] Cobertura ≥85% nas linhas tocadas

---

## Scope

**IN:**
- Tabela `dunning_state` (state machine)
- Cron `dunning_workflow_job` diário
- 3 email templates D+1/D+2/D+3
- Recovery logic via `invoice.payment_succeeded`
- Métricas Prometheus + Mixpanel events
- Suppression list integration

**OUT:**
- SMS notifications (futuro, custo)
- WhatsApp recovery flow (over-engineering pre-revenue)
- Custom Stripe Smart Retries logic (Stripe internal)
- Recovery via in-app modal (apenas email; in-app já tem paywall via plan_auth.py)
- Refund automation
- Custom payment retry (Stripe handles)
- A/B test cadence (n=2 baseline impede)

---

## Definition of Done

- [ ] Migration `dunning_state` aplicada em prod
- [ ] Cron `dunning_workflow_job` registrado em ARQ + executando às 10 UTC
- [ ] 3 templates email criados + validados via send manual
- [ ] Stripe CLI test: trigger `invoice.payment_failed` → assert state criado + Mixpanel event
- [ ] Avançar tempo (staging) → assert D+1/D+2/D+3 emails + final block
- [ ] Counter `smartlic_dunning_started_total` exposto
- [ ] Recovery rate dashboard (Grafana) com query `dunning_recovered / dunning_started`
- [ ] Cobertura ≥85% nas linhas tocadas
- [ ] CodeRabbit clean
- [ ] Operational runbook em `docs/operations/dunning-runbook.md`
- [ ] Smoke test em staging completo (4-day simulated lifecycle)

---

## Dev Notes

### Padrões existentes a reutilizar

- **`acquire_redis_lock` / `release_redis_lock`:** `cron/_loop.py` (existente)
- **`daily_loop`:** scheduler pattern (existente)
- **`send_email_async`:** `email_service.py:194` (fire-and-forget)
- **`track_funnel_event`:** MON-FN-006 já implementado
- **`publish_plan_invalidation`:** MON-FN-003 já implementado
- **`stripe_webhook_events` idempotência:** STORY-307

### Funções afetadas

- `backend/cron/billing.py` ou novo `backend/cron/dunning.py` (NOVO)
- `backend/services/dunning.py` (NOVO ou estender existente)
- `backend/webhooks/handlers/invoice.py::_handle_invoice_payment_failed` (entry)
- `backend/webhooks/handlers/invoice.py::_handle_invoice_payment_succeeded` (exit)
- `backend/templates/emails/dunning_{d1,d2,d3}.html` (NOVO)
- `backend/job_queue.py::WorkerSettings` (registrar cron)
- `backend/metrics.py` (counters + gauge + histograma)
- `backend/quota/plan_auth.py` (já enforça `dunning_phase` — verificar consistência)
- `supabase/migrations/YYYYMMDDHHMMSS_create_dunning_state.sql` + `.down.sql`

### Trade-off: Stripe Smart Retries vs custom dunning

Stripe Smart Retries (default) re-tenta cobrança automaticamente em janela ~3 semanas com algoritmo proprietário. **Coexistem com nosso dunning**:
- Smart Retries dispara `invoice.payment_failed` repetidamente até give-up ou success
- Cada falha incrementa `attempt_count` no nosso state (UPSERT mantém row, atualiza)
- Nosso D+1/D+2/D+3 schedule é **independente** de Stripe retry timing — é cadência de comunicação user, não de cobrança
- Stripe sucess automático → dispara `payment_succeeded` → nosso recovery ativa

### Testing Standards

- Mock Stripe via fixture
- `freezegun` para avançar dias entre runs do cron
- `@patch("services.dunning._send_dunning_email")` para count chamadas sem enviar real
- Cobertura: `pytest --cov=backend/cron/dunning.py --cov=backend/services/dunning.py`
- Anti-hang: cron tests usam `asyncio.wait_for(timeout=10)`

---

## Risk & Rollback

### Triggers de rollback
- Email rate spike (3 emails/user-day em mass past_due event) — Resend rate limit
- False positive: usuário paga via banco/PIX externo — recebe email mesmo pago (se webhook `payment_succeeded` atrasa)
- Plan downgrade incorreto: D+4 transition errada por timestamp drift
- DB lock em `dunning_state` (UNIQUE constraint contention)

### Ações de rollback
1. **Imediato:** env var `DUNNING_WORKFLOW_ENABLED=false` — cron pula sem processar
2. **Email-only revert:** `DUNNING_EMAILS_ENABLED=false` — state machine continua, sem envio
3. **Schema:** down.sql; mas dunning_state é audit value — preferir manter
4. **Manual override:** admin endpoint `POST /admin/dunning/{user_id}/force-recover` (criar se necessário)
5. **Communication:** equipe finance recebe alert se `dunning_lost > 5/dia`

### Compliance
- Emails contém PII (nome, email, último 4 cartão) — Resend envia via TLS, audit log em `trial_email_log`
- LGPD export: `dunning_state` incluído (MON-FN-010)
- LGPD deletion: cascade via FK ON DELETE CASCADE

---

## Dependencies

### Entrada
- **MON-FN-006** (eventos funil): `payment_failed` event + audit table operacionais
- **MON-FN-003** (cache invalidation): `publish_plan_invalidation` disponível para D+4 downgrade
- **MON-FN-001** (Resend HMAC): suppression list para skip bounced
- Stripe webhooks operacionais
- Stripe Customer Portal URL (link para update card)

### Saída
- **MON-FN-008** (free tier): D+4 downgrade pode ser para `smartlic_free` em vez de `expired` se feature ativa
- **MON-FN-013** (ARPU/MRR): consome `dunning_recovered`/`dunning_lost` events para churn rate
- **MON-FN-009** (abandoned cart): pattern similar reutilizado

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | OK | Notes |
|---|---|---|---|
| 1 | Clear and objective title | Y | "Dunning Workflow (D+1, D+2, D+3, Suspend D+4)" — cadência explícita |
| 2 | Complete description | Y | Sequência alvo D+0..D+4 mapeada + benchmark Fortune-500 (15-30%) |
| 3 | Testable acceptance criteria | Y | 8 ACs incluindo Stripe CLI E2E + freezegun 4-day lifecycle |
| 4 | Well-defined scope (IN/OUT) | Y | IN/OUT explícitos; OUT exclui SMS/WhatsApp/A/B (n=2) |
| 5 | Dependencies mapped | Y | Entrada MON-FN-006/003/001; Saída MON-FN-008/013/009 |
| 6 | Complexity estimate | Y | L (5-7 dias) coerente — state machine + cron + 3 templates + E2E |
| 7 | Business value | Y | "Sem dunning, churn voluntário = churn total" + benchmark recovery |
| 8 | Risks documented | Y | Email rate spike + false positive (banco/PIX) + Suppression list integration |
| 9 | Criteria of Done | Y | Smoke test 4-day simulated + recovery rate dashboard Grafana |
| 10 | Alignment with PRD/Epic | Y | EPIC gap #7 + env `SUBSCRIPTION_GRACE_DAYS=3` operacional finalmente |

### Observations
- Decisão de quantos dias = config (`SUBSCRIPTION_GRACE_DAYS`) não story scope — task delimitação respeitada
- Trade-off Stripe Smart Retries vs custom dunning explicitamente documentado (coexistem)
- Idempotência via `d{N}_sent_at IS NULL` previne duplicatas em re-execução
- 3 templates email com tom escalonado (amigável → urgência média → última chance)
- Suppression list (MON-FN-001) integrada para skip bounced/complained
- Recovery via `invoice.payment_succeeded` restaura plan_type + cache invalidação atômica

---

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — dunning workflow ARQ + state machine + 3 emails | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). P1 retention essential L effort; Status Draft → Ready. | @po (Pax) |
