# Runbook — Trial Email Pipeline

**Owner:** @dev + @devops
**Last updated:** 2026-04-10 (STORY-418)
**Sentry incident:** 2026-04-10 (`docs/stories/2026-04/EPIC-INCIDENT-2026-04-10.md`)

## Overview

The trial email sequence delivers ~16 emails across a 14-day trial to
drive activation and conversion. It is driven by a loop in
`backend/jobs/cron/notifications.py::_trial_sequence_loop` which calls
`services.trial_email_sequence.process_trial_emails` every
`TRIAL_SEQUENCE_INTERVAL_SECONDS` (default: every 2h).

Prior to STORY-418, a render error or a Resend throttle in the middle
of the batch would be logged and silently lost — there was no retry,
no backlog, and no audit trail. The 2026-04-10 incident left ~23 emails
undelivered across three milestones (Day 4, Day 7 paywall alert, Day 10
value email), each worth ~R$ 397 in expected MRR.

## Components

| Piece | File | Responsibility |
|---|---|---|
| Forward pass | `backend/services/trial_email_sequence.py` | Identifies eligible users, renders, sends |
| DLQ helper | `backend/services/trial_email_dlq.py` | `enqueue` / `reprocess_pending` |
| DLQ table | `supabase/migrations/20260410132000_story418_trial_email_dlq.sql` | Service-role-only persistence |
| Cron driver | `backend/jobs/cron/notifications.py::_trial_sequence_loop` | Calls forward pass + DLQ drain |
| Metrics | `backend/metrics.py` (`TRIAL_EMAIL_DLQ_*`) | Prometheus counters + gauge |

## Failure handling

```
process_trial_emails()
     │
     ├── render OK + send OK   → trial_email_log insert, sent += 1
     │
     └── render/send raises    → trial_email_dlq.enqueue(...)
                                  (attempts=1, next_retry_at = now+30s)

_trial_sequence_loop()
     │
     ├── forward pass          → (counts from process_trial_emails)
     │
     └── drain DLQ             → reprocess_pending(limit=100)
                                  • scan reprocessed_at IS NULL
                                  • retry render + send
                                  • success → reprocessed_at = now
                                  • fail & attempts < 5 → bump + backoff
                                  • fail & attempts >= 5 → abandoned_at
```

Retry backoff schedule (seconds): `[30, 60, 120]`. Combined with the
2-hour cron cadence, a user gets at most 5 attempts over ~24h before
the row is abandoned. Abandoned rows emit a `STORY-418: trial_email_dlq
abandoning after ...` error log that Sentry picks up.

## Observability

- `smartlic_trial_email_dlq_enqueued_total{email_type, reason}` — counter
- `smartlic_trial_email_dlq_reprocessed_total{email_type}` — counter
- `smartlic_trial_email_dlq_size{state=pending|abandoned}` — gauge
- Log markers:
  - `STORY-418: trial_email_dlq enqueued` (warning)
  - `STORY-418: trial_email_dlq reprocess stats:` (info)
  - `STORY-418: trial_email_dlq abandoning after ...` (error → Sentry)

## Playbook

### "Trial emails stopped going out"

1. Check Grafana for `smartlic_trial_emails_sent_total` — if it's at
   zero but `smartlic_trial_email_dlq_enqueued_total` is climbing, the
   upstream is down, not the pipeline.
2. Look at `smartlic_supabase_cb_state_by_category{category="write"}` —
   if it's `1` (OPEN) the DLQ itself cannot be written either. See
   `docs/runbook/supabase-circuit-breaker.md` for recovery.
3. Tail Railway logs for `STORY-418` markers to see the per-batch DLQ
   stats.

### "User X reports missing trial email"

```sql
-- Check if we tried and failed
SELECT * FROM public.trial_email_dlq
WHERE user_id = '<uuid>'
ORDER BY created_at DESC;

-- Check if we ever sent
SELECT * FROM public.trial_email_log
WHERE user_id = '<uuid>'
ORDER BY sent_at DESC;
```

If the row is in `trial_email_dlq` with `reprocessed_at IS NULL` and
`abandoned_at IS NULL`, the next cron run (within 2h) will retry it.
If `abandoned_at` is set, fix the root cause (check `last_error`) and
manually clear `abandoned_at` to re-queue:

```sql
UPDATE public.trial_email_dlq
   SET abandoned_at = NULL,
       attempts = 0,
       next_retry_at = now()
 WHERE id = '<dlq-row-id>';
```

### "DLQ is growing fast"

1. Query by `reason` to find the dominant failure mode.
2. If `reason='supabase_cb_open'` → this is STORY-416 territory, the
   Supabase CB needs attention; the DLQ is doing its job.
3. If `reason='other'` with a specific `last_error` template → file a
   bug against `services/trial_email_sequence._render_email`.
4. Manually drain if needed:
   ```python
   from services.trial_email_dlq import reprocess_pending
   stats = await reprocess_pending(limit=500)
   ```

## Related stories

- STORY-418 — this story, ARQ-style retry + DLQ table.
- STORY-416 — segregated Supabase CBs (DLQ uses `category="write"`).
- STORY-310 — original trial email sequence.
- STORY-321 — batch dispatch + idempotency.
