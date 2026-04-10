# Runbook — Supabase Circuit Breaker

**Owner:** @architect + @devops
**Last updated:** 2026-04-10 (STORY-416)
**Sentry reference:** incident 2026-04-10 (`docs/stories/2026-04/EPIC-INCIDENT-2026-04-10.md`)

## What it protects

Every Supabase call that goes through `sb_execute()` in
`backend/supabase_client.py` is wrapped in a circuit breaker. Prior to
STORY-416 there was a single global breaker (`supabase_cb`); a failure
on one hot path (slow reads, PGRST timeouts) would trip it and starve
every other path — writes, RPC calls, trial emails, pipeline updates.

STORY-416 split the breaker into three **segregated** categories, each
protecting one class of query, plus the legacy global that is still
updated for backward-compatible dashboards:

| Category | Instance          | Used by                                                    |
|----------|-------------------|------------------------------------------------------------|
| `read`   | `read_cb`         | SELECTs (analytics, history, pipeline GET, trial-value)    |
| `write`  | `write_cb`        | INSERT/UPDATE (session_tracker, trial emails, feedback)    |
| `rpc`    | `rpc_cb`          | `db.rpc(...)` calls (search_datalake, get_analytics_summary) |
| legacy   | `supabase_cb`     | Pre-existing callers that still read `.state` directly    |

## Trip conditions (hybrid mode)

A category CB transitions to `OPEN` when **either**:

- **Rate trip:** the sliding window is full (`SUPABASE_CB_WINDOW_SIZE`,
  default `10`) and the failure rate exceeds
  `SUPABASE_CB_FAILURE_RATE` (default `0.7`, up from 0.5 pre-STORY-416).
- **Streak trip:** consecutive failures reach the category threshold:
  - Read: `SUPABASE_CB_READ_STREAK` (default 5)
  - Write: `SUPABASE_CB_WRITE_STREAK` (default 3)
  - RPC: `SUPABASE_CB_RPC_STREAK` (default 4)

Recovery: after `SUPABASE_CB_COOLDOWN_SECONDS` (60s default) the CB
moves to `HALF_OPEN`. Two consecutive successes (`SUPABASE_CB_TRIAL_CALLS=2`,
down from 3) move it back to `CLOSED`.

Schema errors (`PGRST204`, `PGRST205`, `42703`, `42P01`) are excluded
from the failure count by `_is_schema_error` — those indicate missing
tables or columns, not a Supabase outage (CRIT-040 parity).

## Observability

- **Metric:** `smartlic_supabase_cb_state_by_category{category=...}`
  (gauge, `0=closed 1=open 2=half_open`) — Grafana panel
  "Supabase CBs by category".
- **Metric:** `smartlic_supabase_cb_transitions_total{from_state,to_state,source}`
  (counter) — `source` label carries the category name.
- **Log lines:**
  - `Supabase circuit breaker[<name>]: CLOSED → OPEN`
  - `CB[<name>]: excluded error from failure count: ...`
  - `STORY-416: reset_all_circuit_breakers — previous states=...`
- **Sentry:** any `CircuitBreakerOpenError` exception — filter by
  `error.value:"circuit breaker[read]"` to see per-category issues.

## Playbook

### "Everything is 503"

1. Check `/admin/schema-contract-status` — if it reports drift, apply
   the pending migration first; this is STORY-414 territory, not the CB.
2. Check Grafana `smartlic_supabase_cb_state_by_category` — which
   category is OPEN?
3. Check Sentry for the exception that triggered the streak. If it is a
   PGRST002 or similar transient, wait for the 60s cooldown.
4. If the upstream issue is confirmed fixed and the CB still refuses
   traffic, manually reset with:
   ```bash
   curl -X POST https://api.smartlic.tech/v1/admin/cb/reset \
     -H "Authorization: Bearer <admin-jwt>"
   ```
   This endpoint is **admin only** and logs the previous state per
   category to Railway logs for audit.

### "Read is OPEN but everything else looks fine"

This is exactly the segregation STORY-416 was designed for: the system
should keep accepting writes while read-side UI endpoints degrade.
Verify that:
- `/buscar` still accepts new searches (write + RPC paths).
- Trial emails are still flowing (write path — see
  `docs/runbook/trial-email-pipeline.md`).
- Analytics / history endpoints return cached data or 503.

If a write path is also broken, treat as a global outage.

### "CB trips on every deploy"

Usually a migration race — the new code version reads a column that
existed in staging but not yet in prod. Fix:
1. Apply the missing migration (`supabase db push`).
2. Reset the CBs (`POST /admin/cb/reset`).
3. File a STORY-414 follow-up — the strict schema contract gate in
   staging should have caught it earlier.

## Related stories

- STORY-416 — this story, segregated CBs + hybrid trip mode.
- STORY-414 — schema contract strict-mode gate.
- STORY-412 — `objeto_resumo` schema drift (same incident).
- CRIT-040 — schema errors excluded from CB trip.
- CRIT-042 — health canary must not trip shared CB.
- STORY-291 — original circuit breaker implementation.

## Env vars cheat sheet

```
SUPABASE_CB_WINDOW_SIZE       = 10
SUPABASE_CB_FAILURE_RATE      = 0.7      # STORY-416 raised from 0.5
SUPABASE_CB_COOLDOWN_SECONDS  = 60.0
SUPABASE_CB_TRIAL_CALLS       = 2        # STORY-416 lowered from 3
SUPABASE_CB_READ_STREAK       = 5
SUPABASE_CB_WRITE_STREAK      = 3
SUPABASE_CB_RPC_STREAK        = 4
```
