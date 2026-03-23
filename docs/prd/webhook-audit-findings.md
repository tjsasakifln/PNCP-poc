# Stripe Webhook Audit Findings — DEBT-324

**Date:** 2026-03-23
**Author:** @dev (Dex)
**Story:** DEBT-324 — Dual Stripe webhook router registration

---

## 1. Duplicate Registration (Root Cause)

### What was registered

In `backend/startup/routes.py`, the `stripe_webhook_router` was registered **twice**:

| Registration | Line | Resulting URL | Status |
|---|---|---|---|
| In `_v1_routers` list | line 46 | `POST /v1/webhooks/stripe` | REMOVED |
| Explicit `app.include_router(...)` | line 70 | `POST /webhooks/stripe` | KEPT |

FastAPI registers both routes. Stripe would send the webhook to only one URL (whichever is in the Dashboard), but if Stripe were ever pointed at `/v1/webhooks/stripe`, every event would double-process.

### Fix Applied

Removed `stripe_webhook_router` from the `_v1_routers` list (line 46). The explicit registration at the bottom of `register_routes()` (line 70, now line 69) is the only registration. Added a comment explaining why it is excluded from `_v1_routers`.

**File changed:** `backend/startup/routes.py`

---

## 2. Idempotency Check

### Status: ALREADY EXISTS — no action required

`backend/webhooks/stripe.py` implements DB-level idempotency via the `stripe_webhook_events` table (STORY-307 AC1):

```python
# Lines 160-206: atomic upsert with ON CONFLICT DO NOTHING
claim_result = sb.table("stripe_webhook_events").upsert(
    {"id": event.id, "type": event.type, "status": "processing", ...},
    on_conflict="id",
    ignore_duplicates=True,
).execute()

if not claim_result.data:
    # Event already exists — check for stuck-in-processing (>5 min)
    # ... if stuck, allow reprocessing; otherwise return "already_processed"
    return {"status": "already_processed", "event_id": event.id}
```

This is robust: every event ID is inserted once; duplicates are silently discarded. A "stuck in processing" recovery mechanism handles edge cases where a worker crashes mid-event.

**No in-memory set is needed** — the DB check is the correct pattern for multi-instance deployments (Railway runs multiple Gunicorn workers).

---

## 3. AC Recommendations (Manual Verification Required)

### AC1 — Stripe Dashboard webhook URL
- **Action:** Verify Stripe Dashboard points to `POST /webhooks/stripe` (NOT `/v1/webhooks/stripe`)
- **Where:** Stripe Dashboard → Developers → Webhooks → Endpoint URL
- **Expected:** `https://api.smartlic.tech/webhooks/stripe`

### AC2 — Single route in OpenAPI schema
- **Status:** VERIFIED — snapshot updated, `/v1/webhooks/stripe` removed, only `/webhooks/stripe` remains
- **Evidence:** `backend/tests/snapshots/openapi_schema.json` — 1 entry for `webhooks/stripe`

### AC5 — End-to-end webhook test (Stripe CLI)
- **Action:** Use Stripe CLI to send a test event and confirm exactly one DB row is created
  ```bash
  stripe trigger checkout.session.completed
  # Check: SELECT COUNT(*) FROM stripe_webhook_events WHERE type = 'checkout.session.completed'
  # Expected: 1 row per trigger
  ```
- **Note:** Cannot be automated in unit tests — requires live Stripe CLI + DB access

---

## 4. Test Results

```
132 passed (test_stripe_webhook.py, test_stripe_webhook_matrix.py,
            test_harden028_stripe_events_purge.py, test_stripe_reconciliation.py,
            test_dunning.py, test_payment_failed_webhook.py, test_webhook_rls_security.py)
7 passed  (test_openapi_schema.py — snapshot updated)
0 failures
```

---

## 5. Files Changed

| File | Change |
|---|---|
| `backend/startup/routes.py` | Removed `stripe_webhook_router` from `_v1_routers` list; added explanatory comment |
| `backend/tests/snapshots/openapi_schema.json` | Updated snapshot — removed `/v1/webhooks/stripe` entry |
| `docs/prd/webhook-audit-findings.md` | This document |
