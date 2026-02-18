# Story UX-308: Add Confirmação em Cancelamento de Plano

**Epic:** EPIC-UX-PREMIUM-2026-02
**Priority:** 🟠 P1
**Story Points:** 8 SP
**Owner:** @dev + @ux

## Problem
Botão "Cancelar SmartLic Pro" vermelho sem confirmação. Um clique cancela assinatura (irreversível).

## Acceptance Criteria
- [ ] Modal de confirmação com motivo de cancelamento
- [ ] Flow de retenção baseado no motivo
- [ ] Se "caro demais" → oferecer desconto
- [ ] Se "não usando" → oferecer pausa
- [ ] Confirmação final com checkbox "Entendo que perderei acesso"
- [ ] Feedback form após cancelamento

## Implementation
```tsx
<CancelSubscriptionModal
  onReasonSelect={(reason) => {
    if (reason === 'too_expensive') return <DiscountOfferStep />;
    if (reason === 'not_using') return <PauseOfferStep />;
    return <FinalConfirmationStep />;
  }}
/>
```

**Files:** `components/CancelSubscriptionModal.tsx`, `app/conta/page.tsx`, `routes/billing.py`
