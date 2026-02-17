# GTM-FIX-007: Handle invoice.payment_failed with Dunning

## Dimension Impact
- Moves D02 (Payment Reliability) +1

## Problem
`invoice.payment_failed` webhook has zero handlers (webhooks/stripe.py). When monthly renewals fail (expired card, insufficient funds), the failure is invisible to both system and user. Users retain full access for weeks until Stripe eventually cancels the subscription. No dunning emails, no in-app warnings, no status updates.

## Solution
1. Add `invoice.payment_failed` webhook handler
2. Update `profiles.subscription_status = 'past_due'`
3. Send transactional email: "Pagamento falhou - Atualize seu cartão"
4. Show in-app warning banner on all pages: "⚠️ Falha no pagamento. [Atualizar cartão]"
5. Track dunning events in Mixpanel for analysis
6. After 3 failed payment attempts (Stripe default), mark as `canceled`

## Acceptance Criteria
- [ ] AC1: `handle_invoice_payment_failed()` handler exists in webhooks/stripe.py
- [ ] AC2: Handler extracts customer_id and subscription_id from event
- [ ] AC3: Handler updates `profiles.subscription_status = 'past_due'`
- [ ] AC4: Handler logs event to Sentry with customer context
- [ ] AC5: Handler triggers email via SendGrid/Resend: "payment-failed" template
- [ ] AC6: Email includes CTA button: "Atualizar Forma de Pagamento" → Stripe billing portal
- [ ] AC7: Frontend checks `subscription_status === 'past_due'` on load
- [ ] AC8: If past_due, show PaymentFailedBanner at top of all pages (red, persistent)
- [ ] AC9: Banner text: "⚠️ Falha no pagamento da assinatura. Atualize seu cartão para continuar."
- [ ] AC10: Banner includes "Atualizar Cartão" button → opens Stripe billing portal
- [ ] AC11: Backend test: test_invoice_payment_failed_updates_status()
- [ ] AC12: Backend test: test_invoice_payment_failed_sends_email()
- [ ] AC13: Frontend test: test_payment_failed_banner_display()
- [ ] AC14: Manual test: Trigger test payment failure → verify email + banner
- [ ] AC15: Mixpanel event: `payment_failed` with metadata (plan, amount, attempt_count)

## Effort: S (8h)
## Priority: P1 (Revenue retention)
## Dependencies: GTM-FIX-002 (for email infrastructure)

## Files to Modify
- `backend/webhooks/stripe.py` (add handle_invoice_payment_failed)
- `backend/tests/test_webhooks.py` (add payment failure tests)
- `backend/emails/payment-failed.html` (NEW email template)
- `frontend/components/billing/PaymentFailedBanner.tsx` (NEW)
- `frontend/app/buscar/page.tsx` (add banner)
- `frontend/app/layout.tsx` (add banner to all pages)
- `frontend/__tests__/billing/payment-failed-banner.test.tsx` (NEW)

## Testing Strategy
1. Unit test (backend): Mock invoice.payment_failed event → verify status update
2. Unit test (backend): Verify email send called with correct template + data
3. Unit test (frontend): Mock user with subscription_status='past_due' → banner renders
4. Integration test: Stripe CLI trigger `stripe trigger invoice.payment_failed`
5. Manual test: Real test mode payment failure → verify end-to-end flow

## Email Template Structure
```
Subject: ⚠️ Falha no pagamento - SmartLic

Olá [NOME],

Tentamos processar o pagamento da sua assinatura SmartLic Pro (R$ 1.999,00),
mas o pagamento falhou.

Motivo: [FAILURE_REASON]

Para continuar aproveitando:
• 1000 buscas mensais
• Histórico de 5 anos
• Análise IA + Excel

[BOTÃO: Atualizar Forma de Pagamento]

Sua assinatura expira em [DAYS_UNTIL_CANCEL] dias se o pagamento não for processado.

Precisa de ajuda? Responda este email ou acesse nosso suporte.

Equipe SmartLic
```

## Stripe Dunning Configuration
Stripe default settings (verify in dashboard):
- Retry #1: Immediately after failure
- Retry #2: 3 days later
- Retry #3: 5 days later
- Cancel subscription: 7 days after final attempt

Send webhook on each retry (invoice.payment_failed fires 3x).

## Future Enhancement (not in scope)
- Smart retry timing based on user behavior (send retry on days user is active)
- Proactive alerts: "Your card expires next month" (before failure)
- Alternative payment methods: Boleto, PIX (Brazilian market)
- Grace period with reduced access (read-only mode for 7 days)
