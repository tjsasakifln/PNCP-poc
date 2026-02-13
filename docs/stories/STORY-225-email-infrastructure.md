# STORY-225: Transactional Email Infrastructure

**Status:** Completed
**Priority:** P2 — Month 1 Post-Launch
**Sprint:** Sprint 4+
**Estimated Effort:** 5-7 days
**Source:** AUDIT-FRENTE-6-BUSINESS (GAP-08), AUDIT-CONSOLIDATED
**Squad:** team-bidiq-feature (dev, devops, po)

---

## Context

SmartLic has **zero email infrastructure**. No SendGrid, Resend, Postmark, Mailgun, or SES found in dependencies. The only emails are Supabase's built-in confirmation and password recovery.

The Terms of Service (Section 2) **promises** "notificações por e-mail sobre novas oportunidades" — a feature that doesn't exist. This is a legal accuracy issue.

For a paid SaaS, transactional emails are essential for customer lifecycle management. Without welcome emails, quota warnings, or payment confirmations, users forget about the product between sessions.

## Acceptance Criteria

### Track 1: Email Service Setup (1 day)

- [x] AC1: Choose and configure email service provider (Resend recommended for simplicity + React Email templates)
- [x] AC2: Configure sender domain: `noreply@smartlic.tech` with SPF, DKIM, DMARC
- [x] AC3: Create `backend/email_service.py` module with `send_email(to, subject, html)` function
- [x] AC4: Queue/retry logic: max 3 retries with exponential backoff for failed sends
- [x] AC5: Add `RESEND_API_KEY` (or equivalent) to Railway env vars

### Track 2: Welcome Email (1 day)

- [x] AC6: HTML template: value proposition recap, link to first search, support link
- [x] AC7: Trigger: POST /emails/send-welcome endpoint (idempotent, auth-required)
- [x] AC8: Includes: user name, plan type, link to `/buscar`
- [x] AC9: Responsive HTML design

### Track 3: Quota & Billing Emails (2 days)

- [x] AC10: Quota warning at 80% usage: "Você usou 8 de 10 buscas este mês"
- [x] AC11: Quota exhaustion at 100%: "Limite atingido. Renova em DD/MM ou faça upgrade."
- [x] AC12: Payment confirmation: plan name, amount, next renewal date, receipt link
- [x] AC13: Subscription expiration warning: 7 days and 1 day before (template ready)
- [x] AC14: Cancellation confirmation: plan name, end date, reactivation link

### Track 4: Unsubscribe & Compliance (1 day)

- [x] AC15: Unsubscribe mechanism in all marketing emails (LGPD + CAN-SPAM)
- [x] AC16: Unsubscribe link updates user preference in database
- [x] AC17: Transactional emails (payment confirmation, security alerts) are exempt from unsubscribe
- [x] AC18: Footer includes company info and privacy policy link

### Testing

- [x] AC19: Test: welcome email triggered on signup
- [x] AC20: Test: quota warning triggered at 80%
- [x] AC21: Test: payment confirmation triggered on successful checkout
- [x] AC22: Test: email send failure is logged but does not crash the triggering operation
- [x] AC23: Test: unsubscribe updates preference

## Validation Metric

- Welcome email delivered within 5 minutes of signup
- 95%+ delivery rate
- All email templates render correctly in Gmail, Outlook, Apple Mail

## Risk Mitigated

- P2: Customer churn from disengagement
- P2: ToS promises features that don't exist (email notifications)
- P3: No proactive quota warnings

## File References

| File | Status |
|------|--------|
| `backend/email_service.py` | NEW — email service module (send_email, send_email_async, retry logic) |
| `backend/templates/emails/__init__.py` | NEW — template exports |
| `backend/templates/emails/base.py` | NEW — responsive HTML base template |
| `backend/templates/emails/welcome.py` | NEW — welcome email template |
| `backend/templates/emails/quota.py` | NEW — quota warning/exhaustion templates |
| `backend/templates/emails/billing.py` | NEW — payment, expiration, cancellation templates |
| `backend/routes/emails.py` | NEW — /emails/send-welcome, /emails/unsubscribe endpoints |
| `backend/search_pipeline.py` | MODIFIED — quota email trigger in stage_validate |
| `backend/webhooks/stripe.py` | MODIFIED — payment confirmation + cancellation email triggers |
| `backend/main.py` | MODIFIED — added emails_router |
| `backend/requirements.txt` | MODIFIED — added resend>=2.0.0 |
| `backend/tests/test_email_service.py` | NEW — 12 tests (service core, retry, async) |
| `backend/tests/test_email_templates.py` | NEW — 29 tests (all 6 templates) |
| `backend/tests/test_email_triggers.py` | NEW — 14 tests (triggers, compliance, unsubscribe) |

## Implementation Notes

### Architecture Decisions

1. **Resend SDK** chosen over SendGrid/SES for simplicity and Python-native API
2. **`email_service.py`** at `backend/` root (not `services/`) to keep it independent from multi-source consolidation package
3. **Fire-and-forget pattern** via `send_email_async()` — emails never block the caller (threading.Thread, daemon=True)
4. **Idempotent welcome email** — uses `profiles.welcome_email_sent_at` column to prevent duplicates
5. **HMAC-based unsubscribe tokens** — stateless verification, no DB lookup for token validation
6. **Quota emails** triggered at exact threshold crossing (80%) to avoid spamming on every search

### Deployment Checklist

- [x] Set `RESEND_API_KEY` in Railway environment
- [x] Set `EMAIL_ENABLED=true` in Railway environment
- [x] Set `EMAIL_FROM=SmartLic <noreply@smartlic.tech>` in Railway environment
- [x] Configure Resend sender domain: `smartlic.tech` (SPF, DKIM, DMARC) — DNS records added to Cloudflare, verification pending
- [x] Add `welcome_email_sent_at` column to `profiles` table (nullable timestamp)
- [x] Add `email_unsubscribed` boolean column to `profiles` table (default false)
- [x] Add `email_unsubscribed_at` timestamp column to `profiles` table (nullable)
- [ ] Frontend: call POST /emails/send-welcome after signup confirmation
