# ADR-BILL-SYNC-001 — Bidirectional Stripe ↔ DB sync strategy for `plan_billing_periods`

**Status:** Deprecated
**Date:** 2026-04-28
**Deprecated:** 2026-08-13 — billing/Stripe não é direção de produto ([ADR-STRAT-001](./ADR-STRAT-001-smartlic-confenge-inbound.md), #2111). Manter apenas enquanto o código de sync existir; não expandir.
**Story:** [BILL-SYNC-001](../stories/2026-04/BILL-SYNC-001-stripe-product-price-bidirectional-sync.story.md)
**Owners:** @dev, @data-engineer
**Related:** STORY-360 (frontend reads DB pricing — Done), STORY-307 (Stripe webhook idempotency), DEBT-114 (sole source of truth removed in `plans.stripe_price_id`)

---

## 1. Context

`plan_billing_periods` is the source of truth that `GET /v1/plans` reads (STORY-360). Until BILL-SYNC-001, sync between Stripe (where prices are actually billed against) and that table was performed manually via SQL — leaving 3 risks:

1. **Silent drift:** admin updates a Price in the Stripe Dashboard → DB stays stale → frontend shows wrong price → checkout charges a different amount than the user just saw.
2. **Operational overhead:** every Stripe price change required a hand-edited migration.
3. **No detection:** drift was only ever discovered via complaint or human audit.

Reversa Audit 2026-04-27 (`_reversa_sdd/review-report.md` Gap-9) flagged this. CTO decision 2026-04-27: **both directions** must be automated, with human-readable visibility (last_synced_at + drift indicators in admin UI).

## 2. Decision

We implement three coordinated mechanisms:

### 2.1 Forward sync — Stripe → DB (webhook-driven, automatic)

| Stripe event | Effect on DB |
|---|---|
| `product.updated` | refresh `last_forward_synced_at` for any `plan_billing_periods` row carrying that `stripe_product_id` |
| `price.created` | if a row already references the new price id, refresh `last_forward_synced_at`; orphan prices fire a Sentry warning (admin must explicitly attach via reverse sync) |
| `price.updated` | refresh timestamp; sync `is_archived` from `active=false`; sync `stripe_product_id` if changed |
| `price.deleted` | set `is_archived = TRUE` (Stripe never hard-deletes prices, but archived prices should not appear in the public `/plans` response) |

**Idempotency** is enforced at the dispatcher layer (`webhooks/stripe.py`) via the existing `stripe_webhook_events` table (`INSERT … ON CONFLICT (id) DO NOTHING`). Handlers are pure `UPDATE`s, so duplicate dispatch produces zero net effect — no per-handler dedup needed.

**Out-of-order events (R1):** every handler compares `event.created` with the row's `last_forward_synced_at`. If the incoming event is *older* than what's already on the row, it is silently dropped. This stops a Stripe replay from un-doing newer state.

### 2.2 Reverse sync — DB → Stripe (admin-triggered, explicit)

`POST /v1/admin/plans/{plan_billing_period_id}/sync-to-stripe`:

1. Verify admin role + explicit `i_understand_this_modifies_stripe=true` flag.
2. **Race guard (AC9):** if `last_forward_synced_at` is younger than 24 hours, the operation is rejected with `status=skipped, skipped_reason=race_guard_24h`. An audit log entry records the rejection. This is the primary defence against a forward webhook arriving immediately after a reverse push and creating a feedback loop.
3. Create a **new** Stripe Price using the DB's `price_cents` + `recurring` (Stripe prices are immutable in `unit_amount`).
4. Archive the old Stripe Price (`Price.modify(active=false)`). Old price stays valid for in-flight checkouts (R2).
5. Update DB row: `stripe_price_id = new`, `last_reverse_synced_at = now()`.
6. Write an `admin_billing_audit_log` row with `actor_user_id`, `actor_email`, old/new price ids, optional admin note.

### 2.3 Reconciliation cron — backup against webhook miss (daily 03 UTC)

`backend/jobs/cron/billing_reconciliation.py::reconcile_stripe_prices`:

* Lists every Stripe Price (via auto-pagination — R4 rate-limit defence) and joins against `plan_billing_periods`.
* Classifies each row: `in_sync | price_mismatch | archived_mismatch | db_missing_in_stripe | stripe_missing_in_db`.
* **Auto-fixes** high-confidence drifts: `archived_mismatch` (align `is_archived`), `db_missing_in_stripe` (set `is_archived=TRUE`).
* **Manual-flags** ambiguous drifts (`price_mismatch`, `stripe_missing_in_db`) — admin must run reverse sync explicitly.
* Records one row per execution in `billing_reconciliation_runs` (status, drift_report JSONB, timestamps).
* Fires a Sentry warning (fingerprint `["billing_reconciliation_drift"]`) iff `drifts_detected > 0`.
* Dry-run mode (`BILLING_RECON_DRY_RUN=1` or `?dry_run=true` on the admin trigger) writes the run row but never mutates `plan_billing_periods` — useful when rolling out the cron.
* Redis NX lock (`smartlic:bill_sync_001:reconciliation:lock`) prevents concurrent runs (R3).

## 3. Why webhook is not enough on its own

| Failure mode | Caught by webhook? | Caught by reconciliation? |
|---|---|---|
| Missed event (Stripe outage, our 5xx) | NO | YES (next 03 UTC tick) |
| Manual SQL edit on `plan_billing_periods` | NO | YES |
| Stripe price archived in dashboard while our worker was offline | NO | YES |
| Stripe price `unit_amount` mutation | N/A (Stripe blocks this) | N/A |
| Race: reverse sync triggers webhook → loop | mitigated by 24h race guard | belt-and-suspenders |

## 4. Why reverse sync exists

The default direction is Stripe-as-master (Stripe is what actually bills the customer). But two flows require DB-as-master:

1. **Admin first edits the DB** (e.g. one-off promo, A/B price experiment limited to non-checkout surface). They then want Stripe to mirror that without leaving the SmartLic admin panel.
2. **Disaster recovery:** Stripe price was deleted by mistake; DB is the only intact record of the historical price.

Both are rare. The 24h race guard makes the operation safe even when Stripe webhooks are firing actively.

## 5. Stripe price immutability

Stripe explicitly forbids mutating `unit_amount`, `currency`, `recurring.interval`, or `product` on an existing Price (`PriceUpdateableProperties` is a strict subset). The reverse-sync route therefore always:

1. `stripe.Price.create(...)` — new price.
2. `stripe.Price.modify(old_id, active=False)` — archive old.

`stripe_price_id` on the DB row is repointed to the new price. Old Stripe Price remains in the system for historical invoices.

## 6. Conflict resolution

If a forward webhook and a reverse sync race within sub-second window:

1. The reverse sync writes `last_reverse_synced_at = NOW()`, then issues the Stripe API call.
2. Stripe accepts and emits `price.created`/`product.updated`.
3. The forward handler reads the row, sees `last_reverse_synced_at` < 24h ago → SKIPS the write. No clobber.
4. After 24 hours, ordinary forward sync resumes for that row.

If two forward events arrive out of order:
* Newer event wins (event.created comparison).
* Older event is dropped.

## 7. Stripe Dashboard configuration (manual deployment step)

**Before deploying this change**, enable the following events in Stripe Dashboard → Developers → Webhooks (the existing `https://smartlic.tech/webhooks/stripe` endpoint):

* `product.updated`
* `price.created`
* `price.updated`
* `price.deleted`

The signing secret remains the same; `STRIPE_WEBHOOK_SECRET` env var is reused.

## 8. Schema changes

| Migration | Adds |
|---|---|
| `20260428101050_plan_billing_periods_sync_tracking.sql` | columns `stripe_product_id`, `last_forward_synced_at`, `last_reverse_synced_at`, `is_archived`; indexes by `stripe_price_id` and `stripe_product_id` |
| `20260428101100_billing_reconciliation_runs.sql` | reconciliation execution history (RLS service_role only) |
| `20260428101200_admin_billing_audit_log.sql` | reverse-sync audit trail (actor_user_id, actor_email, old/new price ids) |

All three have paired `.down.sql` rollbacks.

## 9. Alternatives considered

* **Pull-only reconciliation, no webhooks.** Rejected: 24h drift window leaves customers seeing stale prices for almost a full day. Webhooks reduce that window to ~minutes.
* **Single direction (forward only).** Rejected: doesn't cover disaster recovery or admin-first workflows.
* **Per-handler idempotency keys.** Rejected: redundant with dispatcher-level `stripe_webhook_events` upsert and adds maintenance burden.
* **Stripe Price `lookup_key` as the primary join key.** Rejected: not all our prices have lookup_key set, and changing the join key would break in-flight checkouts that reference `stripe_price_id`.

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| R1 Out-of-order webhooks | event.created comparison in handler |
| R2 In-flight checkout breakage | new Price created, old archived (not deleted) |
| R3 Cron + webhook race | Redis NX lock + 24h race guard on row |
| R4 Stripe rate limits | auto-pagination via SDK iterator, default 100/page |

## 11. Observability

* Sentry tag `billing_sync` on each forward-sync event (visibility for dashboard tracking).
* Sentry warning `billing_reconciliation_drift` when daily run finds >0 drifts.
* Admin UI `/admin/billing/sync` shows green/yellow/red drift indicator per row + last 30 reconciliation runs.

## 12. Future work

* Webhook for `product.created` / `product.deleted` (currently we don't auto-create new plans from Stripe — admin must seed `plans` table first).
* Slack notification for `stripe_missing_in_db` (orphan Stripe prices) since these always require manual triage.
* Drift trend chart in admin UI (mini-chart of last 30 runs' `drifts_detected`).
