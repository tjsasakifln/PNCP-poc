# STORY-225: Transactional Email Infrastructure

**Status:** Pending
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

- [ ] AC1: Choose and configure email service provider (Resend recommended for simplicity + React Email templates)
- [ ] AC2: Configure sender domain: `noreply@smartlic.tech` with SPF, DKIM, DMARC
- [ ] AC3: Create `backend/services/email.py` module with `send_email(to, template, data)` function
- [ ] AC4: Queue/retry logic: max 3 retries with exponential backoff for failed sends
- [ ] AC5: Add `RESEND_API_KEY` (or equivalent) to Railway env vars

### Track 2: Welcome Email (1 day)

- [ ] AC6: HTML template: value proposition recap, link to first search, support link
- [ ] AC7: Trigger: after successful signup (both email and Google OAuth)
- [ ] AC8: Includes: user name, plan type, link to `/buscar`
- [ ] AC9: Responsive HTML design

### Track 3: Quota & Billing Emails (2 days)

- [ ] AC10: Quota warning at 80% usage: "Você usou 8 de 10 buscas este mês"
- [ ] AC11: Quota exhaustion at 100%: "Limite atingido. Renova em DD/MM ou faça upgrade."
- [ ] AC12: Payment confirmation: plan name, amount, next renewal date, receipt link
- [ ] AC13: Subscription expiration warning: 7 days and 1 day before
- [ ] AC14: Cancellation confirmation: plan name, end date, reactivation link

### Track 4: Unsubscribe & Compliance (1 day)

- [ ] AC15: Unsubscribe mechanism in all marketing emails (LGPD + CAN-SPAM)
- [ ] AC16: Unsubscribe link updates user preference in database
- [ ] AC17: Transactional emails (payment confirmation, security alerts) are exempt from unsubscribe
- [ ] AC18: Footer includes company info and privacy policy link

### Testing

- [ ] AC19: Test: welcome email triggered on signup
- [ ] AC20: Test: quota warning triggered at 80%
- [ ] AC21: Test: payment confirmation triggered on successful checkout
- [ ] AC22: Test: email send failure is logged but does not crash the triggering operation
- [ ] AC23: Test: unsubscribe updates preference

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
| `backend/services/email.py` | NEW — email service module |
| `backend/templates/emails/` | NEW — HTML email templates |
| `backend/requirements.txt` | Add resend (or equivalent) |
