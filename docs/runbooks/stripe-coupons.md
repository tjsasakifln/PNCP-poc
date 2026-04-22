# Runbook — Stripe Coupons

Central hub for all manually-provisioned coupons that the backend assumes to
exist in Stripe. Coupons are created via the Stripe Dashboard (not via
migration) because they are environment-specific and carry business constraints
(usage limits, expiry) that don't belong in SQL.

---

## FOUNDING30 — STORY-BIZ-001 (Founding Partners)

**Purpose:** 30% off for 12 months for the first 10 paying customers, as the
closing device for B2G wave-1 outreach.

### Stripe Dashboard configuration

1. Navigate to **Stripe Dashboard → Products → Coupons** (live mode).
2. Click **Create coupon** and set:

| Field | Value |
|-------|-------|
| ID | `FOUNDING30` |
| Type | Percentage discount |
| Percent off | `30` |
| Duration | `Repeating` |
| Duration in months | `12` |
| Max redemptions | `10` |
| Expires at | `2026-07-18 23:59 America/Sao_Paulo` |
| Name | `Founding Partner — 30% off 12 months` |
| Metadata | `source=founding`, `story=STORY-BIZ-001` |

3. Click **Save**, then create a matching Promotion Code:
   - Dashboard → Products → Promotion codes → Create
   - Code: `FOUNDING30` (user-facing label, same as ID for simplicity)
   - Coupon: `FOUNDING30`
   - Restrictions → First-time transaction: **enabled**
   - Minimum order value: leave blank
   - Active: **yes**

### Backend integration

The backend reads the coupon id from `FOUNDING_COUPON_ID` env var (default
`FOUNDING30`). If you rename the coupon, override via Railway:

```bash
railway variables set FOUNDING_COUPON_ID=<new_id>
```

The `POST /v1/founding/checkout` handler resolves the promotion code (prefer)
and falls back to the raw coupon id if promo code lookup fails. Both are
exercised by `backend/tests/test_founding_checkout.py`.

### Verification checklist (post-dashboard setup)

- [ ] Dashboard shows `FOUNDING30` coupon with `Max redemptions 10`
- [ ] Dashboard shows `FOUNDING30` promotion code with `first_time_transaction`
- [ ] `curl -X POST https://smartlic.tech/v1/founding/checkout` with a valid
      payload returns a `checkout_url` (200 OK)
- [ ] Visit the `checkout_url` in a browser — Stripe checkout page shows the
      30% discount line-item applied automatically
- [ ] Complete a test payment with a Stripe test card (`4242 4242 4242 4242`)
- [ ] `SELECT checkout_status FROM founding_leads WHERE email = '…';` returns
      `completed` within 30 seconds of payment

### Rollback

If usage needs to be suspended (e.g. all 10 slots filled too fast):

1. Dashboard → Promotion codes → `FOUNDING30` → **Deactivate**.
2. Deactivate the coupon itself: Dashboard → Coupons → `FOUNDING30` → delete.
3. Calls to `POST /v1/founding/checkout` will still create the lead row but
   will fail at Stripe's session-create step with `coupon not found`. That
   surfaces a 400 to the user with message "Não foi possível iniciar o
   checkout." Remove the `/founding` CTA from any public marketing to prevent
   further 400s.

---

## Partner coupons — STORY-323

**Purpose:** 25%-off forever coupons for partner consultancies. Auto-generated
from `partners` table via `scripts/create_partner_coupons.py`. See that script
for the full playbook.

---

## Conventions

- **Coupon ID format:** UPPERCASE_WITH_UNDERSCORES. No spaces, no dashes.
- **Promotion code** should match coupon id unless business wants to A/B
  different codes for the same discount.
- **Never** hardcode coupon IDs in application code. Always read from env var
  with a default constant.
- **Always** record the Dashboard action in this runbook when creating or
  deactivating a coupon. This is the audit trail.
