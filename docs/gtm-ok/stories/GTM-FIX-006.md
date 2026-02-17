# GTM-FIX-006: Add Subscription Cancellation Endpoint + UI

## Dimension Impact
- Moves D02 (Payment Reliability) +1 (improves user control)
- Moves D12 (Account Management) +1 (adds missing feature)

## Problem
No standalone cancel subscription endpoint exists. Users can only cancel by deleting their entire account (routes/user.py:292). Landing page promises "Cancele quando quiser" but the feature is missing. This violates user expectations and potentially Brazilian consumer protection laws (CDC Art. 49).

## Solution
1. Add `POST /v1/subscriptions/cancel` endpoint
2. Call Stripe `subscription.update(cancel_at_period_end=True)`
3. Update `profiles.subscription_status` to `canceling` (new status)
4. Add cancel button to `/conta` account management page
5. Show cancellation confirmation modal with retention offer
6. Display "Active until [end_date]" badge for canceling subscriptions

## Acceptance Criteria
- [ ] AC1: `POST /v1/subscriptions/cancel` endpoint exists in routes/billing.py
- [ ] AC2: Endpoint requires authentication + active subscription
- [ ] AC3: Endpoint calls `stripe.Subscription.modify(sub_id, cancel_at_period_end=True)`
- [ ] AC4: Endpoint updates `profiles.subscription_status = 'canceling'`
- [ ] AC5: Endpoint updates `profiles.subscription_end_date` to period end timestamp
- [ ] AC6: Backend returns 200 with `{ success: true, ends_at: "2026-03-15" }`
- [ ] AC7: `/conta` page shows "Cancelar Assinatura" button (red, secondary)
- [ ] AC8: Button opens CancelSubscriptionModal with confirmation + retention offer
- [ ] AC9: Modal shows: "Tem certeza? Você perderá acesso em [date]"
- [ ] AC10: Modal includes "Fale conosco" link to support (last retention attempt)
- [ ] AC11: After confirmation, frontend calls `POST /api/subscriptions/cancel`
- [ ] AC12: Success: Show toast + update UI to display "Ativa até [date]" badge
- [ ] AC13: Badge appears in navbar + account page (yellow/orange color)
- [ ] AC14: Backend test: test_cancel_subscription_success()
- [ ] AC15: Backend test: test_cancel_subscription_no_active_subscription()
- [ ] AC16: Frontend test: test_cancel_modal_flow()

## Effort: S (8h)
## Priority: P1 (Legal compliance + UX)
## Dependencies: None

## Files to Modify
- `backend/routes/billing.py` (add cancel_subscription endpoint)
- `backend/billing.py` (add cancel_subscription_for_user helper)
- `backend/tests/test_billing.py` (add cancellation tests)
- `frontend/app/api/subscriptions/cancel/route.ts` (NEW proxy)
- `frontend/app/conta/page.tsx` (add cancel button)
- `frontend/components/account/CancelSubscriptionModal.tsx` (NEW)
- `frontend/components/layout/Navbar.tsx` (add canceling status badge)
- `frontend/__tests__/account/cancel-subscription.test.tsx` (NEW)

## Testing Strategy
1. Unit test (backend): Mock Stripe API → verify cancel_at_period_end=True set
2. Unit test (backend): Verify profiles.subscription_status updates to 'canceling'
3. Unit test (frontend): Modal renders → user confirms → API called → toast shown
4. Integration test: Real Stripe test mode → cancel → verify subscription ends at period_end
5. Manual test: Cancel subscription → verify access retained until period end → verify access revoked after

## Retention Strategy (in modal)
```
⚠️ Tem certeza que deseja cancelar?

Você perderá acesso aos seguintes benefícios em [DATA]:
• 1000 buscas mensais ilimitadas
• Histórico de 5 anos (1825 dias)
• Exportação Excel com análise IA
• Filtros avançados por setor

[Botão: Falar com Suporte] [Botão: Confirmar Cancelamento]
```

## Stripe Webhook Handling
When subscription actually ends (customer.subscription.deleted):
- Set `profiles.subscription_status = 'canceled'`
- Set `profiles.plan_type = 'free_trial'`
- Send "We miss you" email with reactivation offer

## Future Enhancement (not in scope)
- Add "Pause subscription" option (freeze for 1-3 months)
- Exit survey: "Why are you canceling?" (radio options)
- Winback email sequence (7 days, 30 days, 90 days after cancellation)
