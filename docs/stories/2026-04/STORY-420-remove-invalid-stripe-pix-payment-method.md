# STORY-420: Fix Invalid Stripe PIX Payment Method no Checkout

**Priority:** P2 — Medium (checkout quebrado para alguns usuários)
**Effort:** S (0.5 day)
**Squad:** @dev
**Status:** Draft
**Epic:** [EPIC-INCIDENT-2026-04-10](EPIC-INCIDENT-2026-04-10.md)
**Sentry Issues:**
- https://confenge.sentry.io/issues/7397513115/ (InvalidRequestError)
- https://confenge.sentry.io/issues/7397513088/ (Unhandled Stripe error)
- https://confenge.sentry.io/issues/7397513083/ (POST /v1/checkout ERROR)
**Sprint:** Sprint rotina (1w-2w)

---

## Contexto

`backend/routes/billing.py:122` passa:
```python
"payment_method_types": ["card", "boleto", "pix"],
```

Para `stripe.checkout.Session.create()`. O Stripe Brazil **não aceita `"pix"` como valor válido em `payment_method_types`**, causando:

```
Request req_M05qyRae7xIQjY: The payment method type provided: pix is invalid.
Please ensure the provided type is activated in your dashboard
(https://dashboard.stripe.com/account/payments/settings) and your account
is enabled for any preview features that you are trying to use.
```

**Impacto:**
- 2 eventos Sentry há 2 dias
- Usuários que tentam checkout recebem 500
- Revenue perdido (trial → pro conversion bloqueada)

**Contexto adicional:** O frontend (provavelmente em `frontend/app/planos/`) não restringe PIX — a configuração vem hardcoded do backend.

---

## Acceptance Criteria

### AC1: Decisão estratégica
- [ ] Consultar @pm sobre PIX: o produto **precisa** oferecer PIX ou foi aspiracional?
- [ ] Se PIX é necessário: investigar como Stripe Brasil recomenda habilitá-lo (pode ser via `payment_method_options.pix` ou via outro produto Stripe)
- [ ] Se PIX não é necessário: remover do array e documentar decisão

### AC2: Fix de código (Opção B — remover PIX)
- [ ] Em `backend/routes/billing.py:122`, alterar:
  ```python
  "payment_method_types": ["card", "boleto"],
  ```
- [ ] Revisar se `boleto` está realmente habilitado no dashboard Stripe antes de deploy (smoke test)
- [ ] Atualizar documentação em `docs/guides/billing.md` (se existir) removendo menções a PIX

### AC3: Fix de código (Opção A — habilitar PIX corretamente)
- [ ] Seguir documentação Stripe: https://docs.stripe.com/payments/pix
- [ ] Habilitar PIX no dashboard Stripe (via @devops)
- [ ] Usar `payment_method_options.pix` em vez de `payment_method_types`:
  ```python
  "payment_method_types": ["card", "boleto"],
  "payment_method_options": {"pix": {...}},  # verificar se suportado
  ```
- [ ] Testar fluxo completo em ambiente Stripe test mode

### AC4: Frontend
- [ ] Se Opção B (remover): verificar `frontend/app/planos/` e `frontend/app/pricing/` para remover menções visuais a PIX
- [ ] Se Opção A (manter): garantir que UI mostra corretamente a opção PIX no checkout (redirect Stripe Checkout)

### AC5: Testes
- [ ] Unit test em `backend/tests/test_billing.py`:
  - [ ] Checkout com card → success
  - [ ] Checkout com boleto → success
  - [ ] Mock Stripe retornando InvalidRequestError → tratamento gracioso (HTTP 400, não 500)
- [ ] E2E Playwright test: clicar "Assinar Pro" → redirect Stripe Checkout funciona (no test mode)

### AC6: Error handling
- [ ] Em `routes/billing.py::create_checkout`, catch `stripe.error.InvalidRequestError` e retornar HTTP 400 com mensagem amigável em pt-BR em vez de 500
- [ ] Log estruturado com `request_id` do Stripe para facilitar debug

### AC7: Verificação pós-deploy
- [ ] Monitorar Sentry issues 7397513115, 7397513088, 7397513083 por 48h — zero novos eventos
- [ ] Smoke test manual em staging: fazer checkout completo com card
- [ ] Marcar issues como **Resolved** no Sentry

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/routes/billing.py` | Linha 122 — fix payment_method_types |
| `backend/tests/test_billing.py` | Tests cobrindo PIX decision |
| `frontend/app/planos/page.tsx` | (Se Opção B) remover menções a PIX |
| `frontend/app/pricing/page.tsx` | (Se Opção B) remover menções a PIX |
| `docs/guides/billing.md` | Atualizar documentação (se existir) |

---

## Implementation Notes

- **Pragmática:** Opção B (remover PIX) é mais rápida e resolve o bug imediato. PIX pode ser re-adicionado depois como uma feature nova.
- **Verificar boleto:** antes de deploy, confirmar no Stripe Dashboard que `boleto` está ativado para a conta. Se não estiver, remover também e ficar só com `["card"]`.
- **Stripe account mode:** verificar se está em test mode vs live mode antes de testar — erros são diferentes.
- **Impacto em trial → pro:** essa story tem prioridade P2 mas afeta revenue. Se o time tem bandwidth, priorizar para a primeira semana.

---

## Dev Notes (preencher durante implementação)

<!-- @dev: documentar decisão (Opção A ou B) e consulta com @pm -->

---

## Verification

1. **Unit:** `pytest backend/tests/test_billing.py::test_create_checkout -v` passa
2. **Staging:** fazer checkout completo com cartão de teste Stripe `4242...` → redireciona para success URL
3. **Sentry:** 48h sem novos eventos
4. **Revenue tracking:** monitorar Mixpanel/Stripe Dashboard — conversões trial → pro voltam ao normal

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-10 | @sm (River) | Story criada a partir do incidente multi-causa |
