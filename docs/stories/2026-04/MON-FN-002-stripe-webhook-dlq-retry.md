# MON-FN-002: Stripe Webhook DLQ + Retry Exponencial (5 tentativas)

**Priority:** P0
**Effort:** M (3-4 dias)
**Squad:** @dev + @architect
**Status:** Ready
**Epic:** [EPIC-MON-FN-2026-Q2](EPIC-MON-FN-2026-Q2.md)
**Sprint:** 1-2 (29/abr–12/mai)
**Sprint Window:** Sprint 1-2 (bloqueador para MON-FN-003)
**Dependências bloqueadoras:** Nenhuma (paralelo com MON-FN-001 e MON-FN-005)

---

## Contexto

`backend/webhooks/stripe.py:213-228` envolve `_process_event()` em `asyncio.wait_for(timeout=30s)` e marca `stripe_webhook_events.status='failed'` em exception (linhas 240-253). Tabela `stripe_webhook_events` é **idempotente** (STORY-307: ON CONFLICT DO NOTHING + stuck check >5min) — porém **não há retry exponencial nem alert Sentry após N falhas**. Resultado: handler crash (DB indisponível, Supabase circuit breaker open, Stripe rate limit) marca evento como `failed` e nunca mais reprocessa. Receita perdida silenciosamente.

Stripe re-tenta até 3 dias com backoff próprio mas se nosso endpoint retornar 200 erroneamente (ou 500 + tabela `failed`), Stripe marca como entregue e não retenta. **Padrão Fortune-500 exige DLQ persistente com retry application-side independente do retry Stripe**, alert após N tentativas, e ferramenta admin para reprocesso manual.

**Por que P0:** webhook handler error rate desconhecido (sem instrumentação no DLQ); incidente Stage 2 (PR #529) revelou que `_handle_*` handlers fazem `.execute()` Supabase direto em paths críticos (`subscription.py`, `invoice.py`) — qualquer wedge backend = receita potencial perdida. Bloqueador para MON-FN-003 (cache invalidation depende de webhook commit confiável).

**Paths críticos:**
- `backend/webhooks/stripe.py` (linhas 213-253: catch + mark failed)
- `backend/webhooks/handlers/{checkout,subscription,invoice,founding}.py` (consumidores)
- `backend/jobs/` ou `backend/cron/billing.py` (novo ARQ job retry)
- `supabase/migrations/` (tabela `stripe_webhook_dlq`)

---

## Acceptance Criteria

### AC1: Tabela `stripe_webhook_dlq` (Dead Letter Queue)

Given que webhook handler falha por exception em `_process_event`,
When o catch block é atingido,
Then o evento é movido para `stripe_webhook_dlq` (não apenas marcado `failed`).

- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_create_stripe_webhook_dlq.sql`:
```sql
CREATE TABLE public.stripe_webhook_dlq (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id text NOT NULL,                            -- Stripe event.id (FK lógica para stripe_webhook_events)
  event_type text NOT NULL,                          -- e.g., invoice.payment_failed
  payload jsonb NOT NULL,                            -- full event.data.object snapshot
  attempt_count int NOT NULL DEFAULT 0,
  last_error text,                                   -- exception message + traceback hash
  last_attempt_at timestamptz,
  next_attempt_at timestamptz,                       -- scheduled retry (exponential backoff)
  status text NOT NULL DEFAULT 'pending',            -- pending | retrying | exhausted | recovered
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  recovered_at timestamptz,
  CONSTRAINT stripe_webhook_dlq_status_chk CHECK (status IN ('pending','retrying','exhausted','recovered'))
);
CREATE INDEX idx_stripe_webhook_dlq_next_attempt ON public.stripe_webhook_dlq (next_attempt_at)
  WHERE status IN ('pending', 'retrying');
CREATE INDEX idx_stripe_webhook_dlq_event_id ON public.stripe_webhook_dlq (event_id);
CREATE INDEX idx_stripe_webhook_dlq_status ON public.stripe_webhook_dlq (status);

ALTER TABLE public.stripe_webhook_dlq ENABLE ROW LEVEL SECURITY;
-- Service-role only (no user-facing access)
```
- [ ] Migration paired down `.down.sql`
- [ ] Trigger `updated_at` auto-update (ou via app-side)
- [ ] Comentário explicando relação com `stripe_webhook_events` (audit) vs `stripe_webhook_dlq` (retry queue)

### AC2: Modificar handler para enfileirar em DLQ on failure

Given que `_process_event` lança exception,
When o catch block roda,
Then move payload para `stripe_webhook_dlq` com `attempt_count=1`, `next_attempt_at=now()+1min`, e mantém `stripe_webhook_events.status='failed'` para audit trail.

- [ ] Em `backend/webhooks/stripe.py:240-253` substituir lógica:
```python
except Exception as e:
    error_msg = f"{type(e).__name__}: {str(e)[:500]}"
    try:
        # Mark audit row as failed (existing behavior)
        sb.table("stripe_webhook_events").update({
            "status": "failed",
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "payload": {"error": error_msg},
        }).eq("id", event.id).execute()

        # Enqueue to DLQ for retry
        sb.table("stripe_webhook_dlq").insert({
            "event_id": event.id,
            "event_type": event.type,
            "payload": event.data.object,
            "attempt_count": 1,
            "last_error": error_msg,
            "last_attempt_at": datetime.now(timezone.utc).isoformat(),
            "next_attempt_at": (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(),
            "status": "pending",
        }).execute()

        smartlic_stripe_webhook_dlq_enqueued_total.labels(event_type=event.type).inc()
    except Exception as enqueue_err:
        logger.error(f"Failed to enqueue to DLQ: {enqueue_err}")
        # Last-resort Sentry capture so we don't lose the event silently
        sentry_sdk.capture_exception(enqueue_err)

    logger.error(f"Error processing webhook (enqueued to DLQ): {e}", exc_info=True)
    # Return 200 to Stripe so they don't retry — we own the retry now
    return {"status": "enqueued_dlq", "event_id": event.id}
```
- [ ] Trade-off documentado: retornar 200 ao Stripe (ao invés de 500) para evitar duplo-retry (Stripe + nosso) — Stripe marca delivered; nós retemos posse via DLQ.
- [ ] Alternativa: retornar 500 e deixar Stripe retry — escolher uma e documentar em `docs/architecture/webhooks.md`. Recomendação: 200 + DLQ próprio (controle total).

### AC3: ARQ job `stripe_webhook_retry` com backoff exponencial

Given DLQ entries com `status='pending' AND next_attempt_at <= now()`,
When ARQ job rodar (scheduler a cada 1 min),
Then processa entries em ordem de `next_attempt_at` ASC com backoff: 1min, 5min, 15min, 1h, 4h (5 tentativas total).

- [ ] Novo `backend/jobs/cron/stripe_webhook_retry.py` (padrão similar a `pncp_canary.py`):
```python
import asyncio
from datetime import datetime, timezone, timedelta
from arq import cron

BACKOFF_SCHEDULE_SECONDS = [60, 300, 900, 3600, 14400]  # 1m, 5m, 15m, 1h, 4h
MAX_ATTEMPTS = 5

async def stripe_webhook_retry_job(ctx: dict) -> dict:
    """Process pending DLQ entries with exponential backoff. Idempotent — safe to run every minute."""
    from supabase_client import get_supabase
    from webhooks.stripe import _process_event_from_dlq  # extracted helper

    sb = get_supabase()
    now = datetime.now(timezone.utc)

    # Claim entries (atomic via UPDATE ... WHERE status='pending')
    pending = sb.table("stripe_webhook_dlq").select("*") \
        .eq("status", "pending") \
        .lte("next_attempt_at", now.isoformat()) \
        .order("next_attempt_at") \
        .limit(50).execute()

    processed = recovered = exhausted = 0
    for entry in pending.data or []:
        # Mark retrying
        sb.table("stripe_webhook_dlq").update({"status": "retrying"}).eq("id", entry["id"]).execute()
        try:
            await _process_event_from_dlq(entry)
            sb.table("stripe_webhook_dlq").update({
                "status": "recovered",
                "recovered_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", entry["id"]).execute()
            recovered += 1
            smartlic_stripe_webhook_dlq_recovered_total.labels(event_type=entry["event_type"]).inc()
        except Exception as e:
            new_count = entry["attempt_count"] + 1
            if new_count >= MAX_ATTEMPTS:
                sb.table("stripe_webhook_dlq").update({
                    "status": "exhausted",
                    "attempt_count": new_count,
                    "last_error": str(e)[:500],
                    "last_attempt_at": datetime.now(timezone.utc).isoformat(),
                }).eq("id", entry["id"]).execute()
                exhausted += 1
                # Sentry alert (fingerprint per event_type)
                sentry_sdk.capture_message(
                    f"Stripe webhook DLQ exhausted: {entry['event_type']}",
                    level="error",
                    fingerprint=["stripe_webhook_dlq", entry["event_type"]],
                    extras={"event_id": entry["event_id"], "attempts": new_count, "error": str(e)[:500]},
                )
                smartlic_stripe_webhook_dlq_exhausted_total.labels(event_type=entry["event_type"]).inc()
            else:
                next_delay = BACKOFF_SCHEDULE_SECONDS[new_count]
                sb.table("stripe_webhook_dlq").update({
                    "status": "pending",
                    "attempt_count": new_count,
                    "last_error": str(e)[:500],
                    "last_attempt_at": datetime.now(timezone.utc).isoformat(),
                    "next_attempt_at": (datetime.now(timezone.utc) + timedelta(seconds=next_delay)).isoformat(),
                }).eq("id", entry["id"]).execute()
        processed += 1

    return {"processed": processed, "recovered": recovered, "exhausted": exhausted}

# Register in arq WorkerSettings:
# cron_jobs = [cron(stripe_webhook_retry_job, minute={0, 1, 2, ..., 59})]  # every minute
```
- [ ] Backoff schedule: 1min, 5min, 15min, 1h, 4h (configurable via `STRIPE_WEBHOOK_DLQ_BACKOFF_SECONDS` env var, comma-separated)
- [ ] Idempotência: claim via `WHERE status='pending'` evita double-processing entre ticks
- [ ] Limit 50 entries per run (evita blast under DB pressure)
- [ ] Helper `_process_event_from_dlq(entry)` extrai event reconstruction de `entry.payload` e despacha para `_handle_*` handlers

### AC4: Sentry alert após 3 falhas consecutivas (não esperar exhausted)

Given DLQ entry com `attempt_count >= 3`,
When o retry job marca `attempt_count` ≥ 3,
Then Sentry capture_message imediato (não aguardar exhausted=5) com fingerprint dedup.

- [ ] Adicional ao AC3: dentro do retry handler, após `attempt_count == 3`, emitir Sentry warning (não error) — assim equipe sabe ANTES de chegar em exhausted
- [ ] Fingerprint dedup `["stripe_webhook_dlq_warning", event_type]` (6h TTL Redis flag para evitar spam)
- [ ] Tags: `attempt_count`, `event_type`, `event_id` (mascarado se necessário)

### AC5: Endpoint admin de reprocesso manual

Given DLQ entry com `status='exhausted'`,
When admin invoca `POST /v1/admin/stripe-webhook-dlq/{dlq_id}/reprocess`,
Then re-enqueue para retry imediato (`status='pending'`, `next_attempt_at=now()`, `attempt_count=0`).

- [ ] Novo endpoint `backend/routes/admin.py` ou novo módulo `routes/admin_webhooks.py`:
```python
@router.post("/admin/stripe-webhook-dlq/{dlq_id}/reprocess")
async def reprocess_dlq_entry(dlq_id: str, user: User = Depends(require_admin)):
    sb = get_supabase()
    entry = sb.table("stripe_webhook_dlq").select("*").eq("id", dlq_id).single().execute()
    if not entry.data:
        raise HTTPException(404, "Entry not found")
    sb.table("stripe_webhook_dlq").update({
        "status": "pending",
        "next_attempt_at": datetime.now(timezone.utc).isoformat(),
        "attempt_count": 0,  # reset attempt count on manual reprocess
        "last_error": None,
    }).eq("id", dlq_id).execute()
    return {"status": "reprocess_scheduled", "dlq_id": dlq_id}

@router.get("/admin/stripe-webhook-dlq")
async def list_dlq_entries(
    status_filter: Optional[str] = None,
    limit: int = 100,
    user: User = Depends(require_admin),
):
    """List DLQ entries for admin UI."""
    ...
```
- [ ] Frontend admin (`/admin/webhooks` — opcional Sprint 4+): tabela com filtros + botão "Reprocess"
- [ ] Audit log: cada manual reprocess gera entry em tabela `admin_actions` (existente ou nova) com `user_id, action='dlq_reprocess', dlq_id, timestamp`

### AC6: Métricas Prometheus

- [ ] Counters:
  - `smartlic_stripe_webhook_dlq_enqueued_total{event_type}` — incrementa em AC2
  - `smartlic_stripe_webhook_dlq_recovered_total{event_type}` — incrementa em AC3 success
  - `smartlic_stripe_webhook_dlq_exhausted_total{event_type}` — incrementa em AC3 final fail
- [ ] Gauge `smartlic_stripe_webhook_dlq_size{status}` — pending|retrying|exhausted (atualizado a cada tick do retry job)
- [ ] Histograma `smartlic_stripe_webhook_dlq_recovery_duration_seconds` — tempo entre enqueue e recovered (alvo p95 < 5min)
- [ ] Sentry release tag para correlacionar deploys com DLQ growth

### AC7: Testes (unit + integration + simulação Stripe)

- [ ] Unit `backend/tests/webhooks/test_stripe_webhook_dlq.py`:
  - [ ] Handler exception → entry inserido em DLQ com `attempt_count=1`
  - [ ] Retry job processa entry → success → status='recovered'
  - [ ] Retry job 5 falhas → status='exhausted' + Sentry capture
  - [ ] Backoff schedule respeitado (next_attempt_at correto)
  - [ ] Idempotência: 2x trigger do retry job no mesmo tick → 1 processamento
  - [ ] Endpoint admin reprocess reseta attempt_count=0
- [ ] Integration: simular crash em `_handle_invoice_payment_failed` (mock raise) → verificar DLQ → mock fix → trigger retry job → verificar recovered
- [ ] Stripe CLI simulation: `stripe trigger invoice.payment_failed` em staging → assert event lands em audit + processado OK
- [ ] Cobertura ≥85% nas linhas tocadas
- [ ] Anti-hang: tests usam `freeze_time` ou `freezegun` para avançar `next_attempt_at` sem sleep real

---

## Scope

**IN:**
- Tabela `stripe_webhook_dlq` (migration paired)
- Modificação em `webhooks/stripe.py` para enfileirar em DLQ
- ARQ job `stripe_webhook_retry_job` com 5-step backoff
- Sentry alert após 3 falhas + exhausted
- Endpoint admin reprocess
- Métricas Prometheus (counters + gauge + histograma)

**OUT:**
- Reescrever lógica idempotência `stripe_webhook_events` (STORY-307 cobre)
- Frontend dashboard admin completo (apenas endpoints; UI futura)
- Migrar para Stripe Workers/Queue Service (Stripe internal — não temos acesso)
- Replay de eventos Stripe (Stripe Dashboard > Webhooks > Resend faz isso; não duplicar)
- Auto-fix de eventos exhausted (manual reprocess only, audit-friendly)

---

## Definition of Done

- [ ] Migration aplicada em prod via `supabase db push`
- [ ] Tabela `stripe_webhook_dlq` existe e RLS service-role-only
- [ ] Webhook handler enfileira em DLQ em exception (validar via test mock falha em `_handle_subscription_created`)
- [ ] ARQ retry job rodando a cada minuto (verificar via `arq job_queue.WorkerSettings` registry)
- [ ] Counter `smartlic_stripe_webhook_dlq_enqueued_total` exposto em `/metrics`
- [ ] Sentry alert dispara após 3 falhas consecutivas (validar com mock infinito-fail)
- [ ] Endpoint `POST /v1/admin/stripe-webhook-dlq/{id}/reprocess` funcional + auth admin
- [ ] Backoff schedule validado (1min, 5min, 15min, 1h, 4h)
- [ ] Cobertura ≥85% nas linhas tocadas
- [ ] CodeRabbit clean
- [ ] Runbook documentado em `docs/architecture/webhooks.md`
- [ ] Smoke test em staging: `stripe trigger invoice.payment_failed` → mock backend handler exception → assert recovery após mock fix

---

## Dev Notes

### Padrões existentes a reutilizar

- **`stripe_webhook_events` schema** (STORY-307): manter audit trail + adicionar DLQ ortogonal. NÃO mesclar tabelas (separation of concerns).
- **ARQ cron pattern**: `backend/jobs/cron/pncp_canary.py` é referência (lock Redis, scheduler 1 min, return dict de stats).
- **Sentry fingerprint**: `["stripe_webhook_dlq", event_type]` similar a STORY-4.5 PNCP canary.
- **Logger sanitization**: `get_sanitized_logger` mascara `customer_id` e `email`.

### Funções afetadas

- `backend/webhooks/stripe.py` (linhas 213-253: substituir catch block)
- `backend/webhooks/handlers/{checkout,subscription,invoice}.py` (sem mudança — apenas chamadas via DLQ replay)
- `backend/jobs/cron/stripe_webhook_retry.py` (NOVO)
- `backend/job_queue.py` ou `backend/jobs/__init__.py` (registrar novo cron)
- `backend/routes/admin.py` ou `routes/admin_webhooks.py` (NOVO endpoint reprocess)
- `backend/metrics.py` (counters + gauge + histograma)
- `supabase/migrations/YYYYMMDDHHMMSS_create_stripe_webhook_dlq.sql` + `.down.sql`

### Helper: `_process_event_from_dlq`

Reconstruir `event` object a partir de `entry.payload` + `entry.event_type`:
```python
async def _process_event_from_dlq(entry: dict) -> None:
    """Replay event from DLQ entry. Reuses existing handlers."""
    sb = get_supabase()
    fake_event = type("Event", (), {
        "id": entry["event_id"],
        "type": entry["event_type"],
        "data": type("Data", (), {"object": entry["payload"]})(),
    })()
    # Reuse existing dispatcher logic — refactor _process_event into shared helper
    if fake_event.type == "checkout.session.completed":
        await _handle_checkout_session_completed(sb, fake_event)
    # ... mesmo dispatcher de webhooks/stripe.py:184-211
```
Recomendação: extrair dispatcher para `webhooks/_dispatcher.py` para evitar duplicação.

### Testing Standards

- Mock Supabase via `supabase_client.get_supabase` patch
- `freezegun` para avançar `next_attempt_at` sem sleep
- Test factory: `tests/factories/stripe_dlq.py` para gerar entries
- Sentry mock via `@patch("sentry_sdk.capture_message")` + assert call_count
- Anti-hang: pytest-timeout 30s; ARQ job test wraps em `asyncio.wait_for(timeout=10)`

---

## Risk & Rollback

### Triggers de rollback
- DLQ size sustained >50 entries (sinal de bug em handler downstream — não na DLQ)
- Retry job crashing repetidamente (Sentry events/min >5 com `task=stripe_webhook_retry`)
- `stripe_webhook_dlq_recovered_total / enqueued_total` < 0.5 após 24h (recovery rate insuficiente — sinal handler tem bug deterministico)
- Receita Stripe vs DB drift detectado em STORY-314 reconciliation cron

### Ações de rollback
1. **Imediato:** disable retry job via env var `STRIPE_WEBHOOK_DLQ_ENABLED=false` (loop pula sem processar)
2. **Manual processing:** equipe processa exhausted entries via Stripe Dashboard "Resend" + endpoint admin reprocess
3. **Schema rollback:** down.sql disponível mas DLQ é audit-positive — preservar mesmo em rollback (apenas pausar processamento)
4. **Communication:** Sentry fingerprint `["stripe_webhook_dlq", event_type]` notifica equipe + finance via email se exhausted >0 em 1 dia

### Compliance
- Eventos Stripe podem conter PII (email, customer_id) — DLQ payload deve estar em LGPD export (MON-FN-010) e deletion (MON-FN-011)
- Retention DLQ: 30 dias para `recovered`/`exhausted`; pending mantém até processado

---

## Dependencies

### Entrada
- Tabela `stripe_webhook_events` (STORY-307 já criada)
- ARQ worker rodando (`PROCESS_TYPE=worker` em Railway)
- Sentry configurado com `SENTRY_DSN`
- Supabase migration CI flow (CRIT-050) ativo

### Saída
- **MON-FN-003** (cache invalidation) depende de webhook commit confiável — DLQ garante eventual consistency
- **MON-FN-007** (dunning) consome `invoice.payment_failed` events; DLQ recovery garante que mesmo eventos falhados disparam dunning
- **MON-FN-009** (abandoned cart) consome `checkout.session.expired` events

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | OK | Notes |
|---|---|---|---|
| 1 | Clear and objective title | Y | "Stripe Webhook DLQ + Retry Exponencial (5 tentativas)" — escopo nítido |
| 2 | Complete description | Y | Contexto cita STORY-307 (idempotência) + PR #529 + linhas código exatas |
| 3 | Testable acceptance criteria | Y | 7 ACs com tests + Stripe CLI simulation + freezegun pattern |
| 4 | Well-defined scope (IN/OUT) | Y | IN/OUT explícitos; OUT distingue "não reescrever idempotência" vs "adicionar DLQ" |
| 5 | Dependencies mapped | Y | Entrada STORY-307; Saída MON-FN-003/007/009 |
| 6 | Complexity estimate | Y | M (3-4 dias) coerente — DLQ + cron + admin endpoint + tests |
| 7 | Business value | Y | Receita perdida silenciosamente, recovery rate Fortune-500 mensurável |
| 8 | Risks documented | Y | Triggers (DLQ size, recovery rate, drift), 4 ações de rollback |
| 9 | Criteria of Done | Y | Migration prod, smoke test staging, runbook, cobertura ≥85% |
| 10 | Alignment with PRD/Epic | Y | EPIC gap #2 endereçado; Sentry/Prometheus integrados |

### Observations
- Trade-off documentado em AC2 (200 vs 500 ao Stripe) é boa prática
- Backoff schedule configurável via env é correto
- Helper `_process_event_from_dlq` extrai dispatcher para evitar duplicação
- Sentry alert após 3 falhas (não esperar exhausted=5) é insight Fortune-500
- Migration paired `.down.sql` documentada

---

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — DLQ + retry exponencial pós PR #529 webhook hardening | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). P0 receita-critical sólido; Status Draft → Ready. | @po (Pax) |
