# STORY-280: Boleto + PIX via Stripe — Implementacao Validada

**Priority:** P2
**Effort:** 2 days
**Squad:** @dev + @qa
**Replaces:** STORY-275 — agora com restricoes tecnicas reais documentadas

## Fundamentacao (Stripe Docs Validados)

### Restricao Critica: PIX NAO Suporta Subscriptions

| Metodo | mode="payment" | mode="subscription" |
|--------|---------------|-------------------|
| Card | ✅ | ✅ |
| Boleto | ✅ | ✅ |
| PIX | ✅ | **❌ NAO SUPORTADO** |

Fonte: [Stripe PIX docs](https://docs.stripe.com/payments/pix), [Stripe Boleto subscriptions](https://docs.stripe.com/payments/boleto/set-up-subscription)

**PIX so funciona para pagamentos avulsos.** Para subscriptions, apenas Card + Boleto.

### Webhook Flow — Diferente de Card

Card (sincrono):
```
checkout.session.completed (payment_status="paid") → ativar
```

Boleto/PIX (assincrono):
```
checkout.session.completed (payment_status="unpaid") → ESPERAR
  → checkout.session.async_payment_succeeded → ATIVAR
  → checkout.session.async_payment_failed → NOTIFICAR
```

Fonte: [Stripe Fulfillment](https://docs.stripe.com/checkout/fulfillment)

### Codigo Validado (Python + Stripe)

```python
# Subscription com Card + Boleto
session = stripe.checkout.Session.create(
    customer=customer_id,
    line_items=[{"price": price_id, "quantity": 1}],
    mode="subscription",
    payment_method_types=["card", "boleto"],  # SEM pix
    payment_method_options={
        "boleto": {"expires_after_days": 3},  # 0-60 dias
    },
    success_url="https://smartlic.tech/planos/obrigado?session_id={CHECKOUT_SESSION_ID}",
    cancel_url="https://smartlic.tech/planos",
)
```

Fonte: [Stripe API: Create Checkout Session](https://docs.stripe.com/api/checkout/sessions/create?lang=python)

### Boleto: Customer Experience
- Apos checkout, redirecionado para `hosted_voucher_url` (NAO success_url)
- Customer copia codigo de barras ou baixa PDF
- Pagamento confirmado em **1 dia util** apos pagamento pelo cliente
- Refund: NAO suportado para Boleto
- Fonte: [Stripe Boleto docs](https://docs.stripe.com/payments/boleto)

### PIX: Limites
- Minimo: R$0,50 / Maximo: R$3.000 por transacao
- Limite mensal: $10.000 por customer/merchant
- Expiracao: `expires_after_seconds` (10s a 14 dias, default 1 dia)
- Fonte: [Stripe PIX docs](https://docs.stripe.com/payments/pix)

### Test Mode Emails
- `anything@domain.com` → paga apos 3 minutos
- `succeed_immediately@domain.com` → sucesso instantaneo
- `expire_immediately@domain.com` → expira instantaneamente
- `fill_never@domain.com` → nunca completa

## Acceptance Criteria

### AC1: Boleto em Checkout de Subscription
- [x] `routes/billing.py`: adicionar `"boleto"` a `payment_method_types`
- [x] `payment_method_options.boleto.expires_after_days = 3`
- [x] **NAO adicionar "pix"** ao mode=subscription (Stripe rejeita)

### AC2: Webhook Handlers para Pagamento Assincrono
- [x] `webhooks/stripe.py`: handler para `checkout.session.async_payment_succeeded`
  - Atualizar `profiles.plan_type` = plano pago
  - Atualizar `profiles.subscription_status` = "active"
- [x] Handler para `checkout.session.async_payment_failed`
  - Enviar email: "Seu boleto expirou. Gere um novo em /planos"
  - Manter acesso atual (grace period de 3 dias ja implementado)
- [x] Modificar handler de `checkout.session.completed`:
  - Se `payment_status == "paid"`: ativar (card — comportamento atual)
  - Se `payment_status == "unpaid"`: **NAO ativar**, aguardar async_payment_succeeded

### AC3: PIX Apenas para Pagamento Avulso (Opcional)
- [ ] Se plano anual: oferecer PIX como pagamento unico (mode="payment")
- [x] Ou: nao implementar PIX nesta iteracao (Boleto ja resolve 90% dos casos)
- [x] **Decisao PO:** PIX adiado para versao futura — Boleto cobre 90% dos casos B2G

### AC4: Frontend — Icones de Pagamento
- [x] `/planos`: mostrar icones Card + Boleto (+ PIX se AC3 aprovado)
- [x] Remover "em fase de implementacao" do FAQ (nao existia no FAQ atual)
- [x] FAQ: "Aceitamos cartao de credito e Boleto Bancario" (+ PIX se aplicavel)

### AC5: Email de Lembrete de Boleto
- [x] Dia 2 apos geracao: "Seu boleto vence amanha"
- [x] Usar template em `templates/emails/boleto_reminder.py`
- [x] Trigger: Stripe envia lembretes built-in para boleto subscriptions; template criado para uso futuro via cron

## Pre-requisitos

- [ ] Boleto e PIX habilitados no Stripe Dashboard (Settings → Payment Methods)
- [ ] Capabilities `boleto_payments` e `pix_payments` ativas
- [ ] Conta Stripe com entidade brasileira (CONFENGE ja tem)

## Files Modified

| File | Change |
|------|--------|
| `backend/routes/billing.py` | Add boleto to payment_method_types + expires_after_days=3 |
| `backend/webhooks/stripe.py` | async_payment_succeeded/failed handlers + checkout unpaid logic |
| `frontend/app/planos/page.tsx` | Payment icons (Card + Boleto) + new FAQ about payment methods |
| `backend/templates/emails/boleto_reminder.py` | **NEW** — boleto reminder + expired templates |
| `backend/tests/test_story280_boleto_pix.py` | **NEW** — 20 tests covering all ACs |
| `frontend/__tests__/planos-page.test.tsx` | Updated — 4 new tests for payment icons + FAQ |

## Fontes
- Boleto: https://docs.stripe.com/payments/boleto
- Boleto subscriptions: https://docs.stripe.com/payments/boleto/set-up-subscription
- PIX: https://docs.stripe.com/payments/pix
- Fulfillment: https://docs.stripe.com/checkout/fulfillment
- API: https://docs.stripe.com/api/checkout/sessions/create
