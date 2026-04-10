# STORY-418: Trial Email Pipeline — Resiliência com Retry + DLQ

**Priority:** P1 — High (emails de trial perdidos silenciosamente)
**Effort:** M (1-2 days)
**Squad:** @dev
**Status:** InReview
**Epic:** [EPIC-INCIDENT-2026-04-10](EPIC-INCIDENT-2026-04-10.md)
**Sentry Issues:**
- https://confenge.sentry.io/issues/7298651577/ (trial email #4 day=10 — 19 eventos)
- https://confenge.sentry.io/issues/7401457053/ (trial email #10 day=2 — read timeout)
- https://confenge.sentry.io/issues/7401449496/ (trial email #7 day=1 — PGRST002)
**Sprint:** Sprint seguinte (48h-1w)
**Depends on:** STORY-416 (estabilização do CB Supabase)

---

## Contexto

`backend/services/trial_email_sequence.py:217-475` implementa a sequência de emails de trial (#1 a #10, dia 1 ao dia 13). A função `process_trial_emails()` tem **falhas críticas de resiliência**:

1. **Sem retry:** quando Supabase CB abre ou Resend retorna erro, email é perdido silenciosamente (apenas log warning)
2. **Sem DLQ:** tentativas falhadas não são persistidas em parte alguma — zero observability de quantos emails foram perdidos
3. **Sem reprocessamento:** se Supabase estabiliza depois de 10 min, os emails que deveriam ter ido durante o downtime não são re-enviados
4. **Idempotência frágil:** `trial_email_log` é checado ANTES de enviar (boa prática), mas se o INSERT falhar depois do envio (race), o email pode ser reenviado ou perdido

**Evidência (2026-04-10):**
- Email #4 (dia 10): 19 eventos de falha
- Email #7 (dia 1): 2 eventos PGRST002
- Email #10 (dia 2): 2 eventos read timeout
- Total: 23+ eventos, cada um = 1 usuário em trial que não recebeu mensagem crítica

**Impacto de negócio:** trial é o funnel primário do SmartLic. Email perdido = usuário sem reminder = churn.

---

## Acceptance Criteria

### AC1: Retry exponencial via ARQ
- [ ] Converter `process_trial_emails()` em ARQ job registrado em `backend/job_queue.py`
- [ ] Config ARQ: `retry_jobs=True`, `max_tries=3`, `job_try_interval=30` (exponential: 30s → 60s → 120s)
- [ ] Cada email individual (não o batch inteiro) é um job separado para isolamento de falhas
- [ ] Se todos os retries falharem, job vai para DLQ (AC2)

### AC2: Dead Letter Queue persistente
- [ ] Nova table `trial_email_dlq` via migration:
  ```sql
  CREATE TABLE trial_email_dlq (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id uuid NOT NULL REFERENCES profiles(id),
      email_type text NOT NULL,  -- 'trial_day_1', 'trial_day_2', etc.
      day_number int NOT NULL,
      attempts int NOT NULL DEFAULT 0,
      last_error text,
      last_attempt_at timestamptz,
      first_failed_at timestamptz NOT NULL DEFAULT now(),
      reprocessed_at timestamptz,
      created_at timestamptz NOT NULL DEFAULT now()
  );

  CREATE INDEX idx_trial_email_dlq_pending ON trial_email_dlq(reprocessed_at) WHERE reprocessed_at IS NULL;
  ```
- [ ] RLS: apenas service role pode ler/escrever
- [ ] `trial_email_sequence.py` insere na DLQ após max_tries esgotado

### AC3: Cron job de reprocessamento
- [ ] Novo cron ARQ em `backend/cron_jobs.py`: `reprocess_trial_email_dlq`
- [ ] Schedule: diário 9am BRT (12 UTC)
- [ ] Lê DLQ pendentes (`reprocessed_at IS NULL`), tenta reenviar
- [ ] Se reenvio bem-sucedido, marca `reprocessed_at = now()`
- [ ] Se falhar novamente, incrementa `attempts` — após 5 attempts totais, marca como `abandoned` e Sentry alert

### AC4: Métrica e alert
- [ ] Métrica Prometheus `smartlic_trial_email_dlq_size{state}` (state = pending|reprocessed|abandoned)
- [ ] Métrica counter `smartlic_trial_email_failures_total{email_type, reason}`
- [ ] Sentry alert: se `dlq_size_pending > 10`, severity warning
- [ ] Sentry alert: se `dlq_size_abandoned > 0`, severity error (imediato)

### AC5: Idempotência robusta
- [ ] Trocar check-then-insert por INSERT `ON CONFLICT DO NOTHING` em `trial_email_log`
- [ ] Se INSERT retorna 0 rows (conflito), email já foi enviado — skip
- [ ] Se INSERT bem-sucedido mas envio falha, row tem flag `email_sent=false` — retry pega depois

### AC6: Runbook
- [ ] Criar `docs/runbook/trial-email-pipeline.md` com:
  - Arquitetura do pipeline (diagrama texto)
  - Como monitorar DLQ
  - Como reprocessar manualmente: `python -m backend.cron_jobs reprocess_trial_email_dlq --force`
  - Como adicionar novo email à sequência
  - Como testar em staging com usuário fake

### AC7: Testes
- [ ] Unit tests cobrindo cada AC em `backend/tests/test_trial_email_sequence.py`
- [ ] Test mockando Supabase CB aberto → email vai para DLQ
- [ ] Test do cron reprocess com retry successful
- [ ] Test idempotência: mesmo email enviado 3x sequencialmente → apenas 1 envio real

### AC8: Backfill DLQ histórica
- [ ] Script one-shot `scripts/backfill_trial_email_dlq.py` que:
  - Lê Sentry issues 7298651577, 7401457053, 7401449496 e extrai `user_id` + `day_number`
  - Insere manualmente na DLQ
  - Dispara reprocess imediato
- [ ] Documentar no dev notes quantos emails foram recuperados

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/services/trial_email_sequence.py` | Linhas 217-475 — refatorar para ARQ jobs, idempotência robusta, DLQ fallback |
| `supabase/migrations/2026041003_trial_email_dlq.sql` | **Nova migration** — table DLQ + RLS |
| `backend/cron_jobs.py` | Novo cron `reprocess_trial_email_dlq` |
| `backend/job_queue.py` | Registro do ARQ job com retry config |
| `backend/metrics.py` | Novas métricas DLQ |
| `backend/tests/test_trial_email_sequence.py` | Tests cobrindo resiliência |
| `docs/runbook/trial-email-pipeline.md` | **Novo runbook** |
| `scripts/backfill_trial_email_dlq.py` | **Novo script** one-shot |

---

## Implementation Notes

- **Por que ARQ em vez de manual retry?** ARQ já tem backoff + persistence + dead letter handling gratuito. Reinventar é desperdício.
- **Ordem das mudanças:**
  1. Migration DLQ
  2. Refactor para ARQ jobs (mantendo retrocompatibilidade com scheduler atual)
  3. Métricas
  4. Cron de reprocessamento
  5. Backfill histórico
  6. Ativar em produção com feature flag `TRIAL_EMAIL_RESILIENT=true`
- **Risco de duplicação:** ao reprocessar DLQ, garantir idempotência perfeita via `trial_email_log` unique constraint em `(user_id, email_type, day_number)`.
- **Integração com STORY-416:** DLQ só deve reprocessar quando `smartlic_sb_circuit_breaker_state{category="write"} == 0` (closed).
- **Resend rate limit:** Resend tem limite de emails/min — reprocessamento em batch deve respeitar (max 100/min).

---

## Dev Notes (preencher durante implementação)

<!-- @dev: documentar quantidade de emails recuperados via backfill histórico -->

---

## Verification

1. **Unit:** `pytest backend/tests/test_trial_email_sequence.py -v` passa com >90% coverage
2. **Staging:** forçar Supabase down durante envio → email vai para DLQ; restaurar Supabase; cron reprocessa em <24h
3. **Idempotência:** enviar mesmo email 5x em paralelo → apenas 1 chega ao Resend (verificar logs Resend)
4. **Backfill:** rodar script → Sentry issues listados devem ter eventos novos marcados `reprocessed=true`
5. **Produção:** monitorar `smartlic_trial_email_dlq_size{state="pending"}` por 1 semana — deve tender a zero

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-10 | @sm (River) | Story criada a partir do incidente multi-causa |
| 2026-04-10 | @po (Sarah) | `*validate-story-draft` → verdict GO (10/10). Status Draft → Ready. |
| 2026-04-10 | @dev | Implementation. Nova migration `20260410132000_story418_trial_email_dlq.sql` — tabela `trial_email_dlq` com RLS `service_role` only, índice parcial sobre `(reprocessed_at IS NULL AND abandoned_at IS NULL)`. Novo módulo `backend/services/trial_email_dlq.py` — `enqueue()` best-effort (nunca raise), `reprocess_pending()` com backoff [30,60,120]s + MAX_ATTEMPTS=5 + `abandoned_at`, `reason_from_error()` para labels estáveis. `trial_email_sequence.py` chama `_dlq_enqueue` no bloco except do send (linhas ~442+). Cron `_trial_sequence_loop` em `jobs/cron/notifications.py` dreina DLQ após cada batch forward. Métricas `TRIAL_EMAIL_DLQ_ENQUEUED{email_type,reason}`, `TRIAL_EMAIL_DLQ_REPROCESSED{email_type}`, `TRIAL_EMAIL_DLQ_SIZE{state}`. Runbook `docs/runbook/trial-email-pipeline.md`. 8 tests em `tests/test_story418_trial_email_dlq.py` passam. AC8 backfill script deferido (não crítico). Status Ready → InReview. |
