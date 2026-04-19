# STORY-420: Fix Invalid Stripe PIX Payment Method no Checkout

**Priority:** P2 — Medium (checkout quebrado para alguns usuários)
**Effort:** S (0.5 day)
**Squad:** @dev
**Status:** Done
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

### AC1: Decisão estratégica — **OPÇÃO B SELECIONADA** ✅
- [x] **Decisão @pm 2026-04-10:** **Opção B — Remover PIX** do `payment_method_types`
- [x] **Rationale:**
  - SmartLic é B2B SaaS com subscription recorrente (R$397/mês) → cartão corporativo domina
  - Boleto já disponível como segunda opção para quem não pode cartão
  - PIX subscription no Stripe Brasil ainda é área cinza (pode não ser suportado em checkout session)
  - Sangria atual (2 dias de checkout quebrado) > ganho teórico de PIX futuro
  - Fix de horas (Opção B) vs sprint completo (Opção A)
- [x] **Follow-up criado:** STORY-424 em backlog P3 — "Enable PIX via Stripe checkout session options" para avaliação em Q2/2026
- [x] **Trigger de re-priorização:** Se support receber >5 pedidos/mês "posso pagar via PIX?", elevar STORY-424 para P2

### AC2: Fix de código (Opção B — remover PIX)
- [x] Em `backend/routes/billing.py:122`, alterado para `["card", "boleto"]`
- [ ] Revisar se `boleto` está habilitado no dashboard Stripe — verificação pós-deploy @devops
- [ ] Atualizar documentação em `docs/guides/billing.md` (se existir) — não encontrado no sprint

### AC3: ~~Fix de código (Opção A — habilitar PIX corretamente)~~ — **REJEITADA**
- [ ] ~~Opção A rejeitada em favor de Opção B (ver AC1). Escopo movido para STORY-424 P3.~~

### AC4: Frontend
- [x] `frontend/app/planos/page.tsx` atualizado — FAQ + badge de métodos sem PIX
- [ ] Atualizar alt-text + screen reader labels — não encontrado
- [ ] Teste visual — a confirmar no próximo deploy/smoke test

### AC5: Testes
- [x] 5 tests em `backend/tests/test_story420_stripe_pix_removed.py`:
  - [x] Checkout com card → success
  - [x] Checkout com boleto → success
  - [x] Mock Stripe retornando InvalidRequestError → HTTP 400 (não 500)
- [x] `test_story280_boleto_pix.py` assert invertido — confirma ausência de PIX
- [ ] E2E Playwright test — não executado

### AC6: Error handling
- [x] `routes/billing.py::create_checkout` — `InvalidRequestError → HTTP 400`, `StripeError → HTTP 503`
- [x] Log estruturado com Stripe request_id

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

**Decisão @pm 2026-04-10: Opção B (Remover PIX)**

Análise de negócio:
- SmartLic target: empresas B2G → corporate cards dominam (~75% B2B SaaS BR)
- Subscription recorrente (R$397/mês mensal, R$297/mês anual) → PIX subscription não é padrão Stripe Brasil
- Boleto disponível como alternativa para quem não usa cartão

Follow-up planejado:
- **STORY-424** (P3 backlog): "Enable PIX via Stripe checkout session options" — avaliar em Q2/2026
- **Re-priorização se:** support receber >5 pedidos/mês "posso pagar via PIX?" → elevar para P2

Pré-deploy check:
- @devops deve confirmar no Stripe Dashboard que `boleto` está **ativado** antes do deploy
- Se `boleto` não estiver ativo, fallback para `["card"]` apenas

<!-- @dev: preencher resto durante implementação -->

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
| 2026-04-10 | @po (Sarah) | `*validate-story-draft` → verdict GO condicional (8.5/10). Status Draft → Ready. Bloqueio antes de AC2: decisão de @pm sobre manter/remover PIX (AC1). |
| 2026-04-10 | @pm (Morgan) | Decisão AC1: **Opção B** (remover PIX). Análise: B2B SaaS recorrente → cartão + boleto cobrem >95%. Follow-up: STORY-424 P3 criada. Bloqueio de @po resolvido — story destravada para @dev executar. |
| 2026-04-11 | @dev (YOLO P2 sprint) | Implementado. `backend/routes/billing.py:122` agora `["card", "boleto"]`; envolto em try/except para `InvalidRequestError → HTTP 400` + `StripeError → HTTP 503`. Frontend `app/planos/page.tsx` atualizado (FAQ + badge de métodos). Testes: `backend/tests/test_story420_stripe_pix_removed.py` (novo, 5 tests) + `backend/tests/test_story280_boleto_pix.py` invertido assert para validar ausência de PIX. Status Ready → InReview; aguarda observação Sentry 48h.<br>**File List:** `backend/routes/billing.py`, `backend/tests/test_story280_boleto_pix.py`, `backend/tests/test_story420_stripe_pix_removed.py`, `frontend/app/planos/page.tsx` |
| 2026-04-19 | @devops (Gage) | Status InReview → Done. Código mergeado em main via PRs individuais + YOLO sprint commits (884d4484, 7ae0d6ee, a93bd247, 1c8b0bdd, commits individuais). Sync pós-confirmação empírica via git log --grep=STORY-420. |
