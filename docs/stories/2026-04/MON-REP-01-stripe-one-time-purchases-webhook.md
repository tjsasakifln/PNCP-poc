# MON-REP-01: Stripe One-Time Purchase + Tabela `purchases` + Webhook

**Priority:** P0
**Effort:** M (3 dias)
**Squad:** @dev + @devops
**Status:** Draft
**Epic:** [EPIC-MON-REPORTS-2026-04](EPIC-MON-REPORTS-2026-04.md)
**Sprint:** Wave 1 (bloqueador de MON-REP-02/03/04/05/06 + MON-AI-02 + MON-DIST-01)

---

## Contexto

Hoje o Stripe está configurado **apenas para assinaturas recorrentes** (`mode=subscription` em `backend/routes/billing.py`). A tabela `user_subscriptions` rastreia assinaturas, mas não há tabela para compras únicas. O webhook `webhooks/stripe.py` trata `checkout.session.completed` e `customer.subscription.*` mas não `charge.succeeded` nem `payment_intent.succeeded`.

Para lançar relatórios avulsos (Camada 2), pacotes de dados (MON-DIST-01) e compras one-shot de AI Copilot (MON-AI-02), precisamos da infra de **pagamento único** + rastreamento + trigger de entrega automática.

---

## Acceptance Criteria

### AC1: Tabela `purchases`

- [ ] Migração cria:
```sql
CREATE TABLE public.purchases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  product_type text NOT NULL CHECK (product_type IN (
    'report_supplier', 'report_price_reference', 'report_competition',
    'report_due_diligence', 'data_package', 'ai_proposal', 'custom'
  )),
  product_params jsonb NOT NULL DEFAULT '{}'::jsonb,
  amount_cents int NOT NULL CHECK (amount_cents > 0),
  currency char(3) NOT NULL DEFAULT 'BRL',
  stripe_checkout_session_id text UNIQUE,
  stripe_payment_intent_id text UNIQUE,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN (
    'pending', 'paid', 'delivered', 'refunded', 'failed', 'expired'
  )),
  created_at timestamptz NOT NULL DEFAULT now(),
  paid_at timestamptz NULL,
  delivered_at timestamptz NULL,
  refunded_at timestamptz NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX ON purchases (user_id, created_at DESC);
CREATE INDEX ON purchases (status, created_at) WHERE status IN ('pending','paid');
```
- [ ] RLS: `SELECT`/`UPDATE` restringe ao próprio `user_id`; `INSERT`/`DELETE` apenas service role
- [ ] Migração paired down

### AC2: Endpoint de checkout one-time

- [ ] `POST /v1/purchases/checkout` recebe `{product_type, product_params, success_url, cancel_url}`
- [ ] Validação de `product_type` + preço via lookup `PRODUCT_CATALOG` (hardcoded inicial em `backend/services/product_catalog.py`, depois migra para tabela)
- [ ] Cria Stripe session `mode='payment'` com `line_items` dinâmico + metadata `purchase_id`
- [ ] Insere row em `purchases` com `status='pending'` + `stripe_checkout_session_id`
- [ ] Retorna `{purchase_id, checkout_url}`
- [ ] Rate limit: 10 checkouts/minuto por usuário (reusa infra `quota/`)

### AC3: Webhook handler para pagamento

- [ ] Adicionar em `backend/webhooks/handlers/payment.py`:
  - `checkout.session.completed` com `mode='payment'` → atualiza `status='paid'`, `paid_at=now()`, `stripe_payment_intent_id`, enfileira ARQ job `generate_report_job(purchase_id)` (criado em MON-REP-02)
  - `charge.refunded` → atualiza `status='refunded'`, `refunded_at=now()`, envia email de confirmação de reembolso
  - `payment_intent.payment_failed` → `status='failed'` + email para usuário
- [ ] Idempotência via `stripe_payment_intent_id` (UNIQUE constraint) — webhook replay não duplica registro
- [ ] Signature verification já existente em `stripe.py` — reutilizar

### AC4: Lista de produtos catalogados

- [ ] `backend/services/product_catalog.py` expõe dict:
```python
PRODUCT_CATALOG = {
    'report_supplier': {'tiers': [(47_00, 'basic'), (97_00, 'standard'), (197_00, 'premium')]},
    'report_price_reference': {'tiers': [(97_00, 'basic'), (197_00, 'standard'), (297_00, 'premium')]},
    'report_competition': {'tiers': [(197_00, 'basic'), (347_00, 'standard'), (497_00, 'premium')]},
    'report_due_diligence': {'tiers': [(297_00, 'basic'), (497_00, 'standard'), (697_00, 'premium')]},
    'ai_proposal': {'tiers': [(197_00, 'one_shot')]},
    'data_package': {'dynamic': True},  # validado contra tabela data_packages (MON-DIST-01)
}
```
- [ ] Teste unitário valida que `amount_cents` do request bate com tier declarado

### AC5: Endpoint admin de listagem

- [ ] `GET /v1/admin/purchases` (paginado, admin only): últimas compras com filtros `status`, `product_type`, `user_email`
- [ ] Frontend `/admin/purchases` simples (reusar componentes de `/admin/cache`)

### AC6: Testes

- [ ] Unit: `backend/tests/routes/test_purchases_checkout.py`
  - Happy path: valid product_type + tier → Stripe session criada + row pending
  - Invalid product_type → 400
  - Tier não existe → 400
  - Rate limit 10/min → 429
- [ ] Integration: `backend/tests/webhooks/test_payment_handler.py`
  - `checkout.session.completed` happy path → status='paid' + job enfileirado (mock ARQ)
  - Replay idempotência: mesma session event 2x → 1 insert apenas
  - `charge.refunded` → status='refunded' + email
- [ ] E2E: Playwright test em `frontend/e2e-tests/checkout-one-time.spec.ts` (mock Stripe)

---

## Scope

**IN:**
- Migração `purchases` + RLS
- `backend/routes/purchases.py` (novo)
- `backend/webhooks/handlers/payment.py` (novo)
- `backend/services/product_catalog.py` (novo)
- Endpoint admin + frontend dashboard
- Testes

**OUT:**
- Geração de relatórios (MON-REP-02)
- Entrega por email (MON-REP-02)
- Storage de PDFs (MON-REP-02)
- Produtos específicos — cada relatório tem sua story (MON-REP-03 em diante)

---

## Dependências

- Stripe account configurado em dev e prod (já existe)
- Rate limiter (já existe em `quota/`)
- ARQ worker (já em produção)

---

## Riscos

- **Coexistência `mode=payment` vs `mode=subscription`:** webhook handler precisa distinguir via `session.mode`; teste de regressão garante que subscription flow não quebra
- **Webhooks fora de ordem:** `charge.succeeded` pode chegar antes de `checkout.session.completed` → lógica idempotente por `stripe_payment_intent_id` resolve
- **Reembolso parcial:** v1 só suporta reembolso total (tudo-ou-nada); reembolso parcial fica para Q3

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `supabase/migrations/.../create_purchases_table.sql` + `.down.sql`
- `backend/routes/purchases.py` (novo)
- `backend/services/product_catalog.py` (novo)
- `backend/webhooks/handlers/payment.py` (novo)
- `backend/webhooks/stripe.py` (dispatcher — adicionar handler)
- `backend/routes/admin_purchases.py` (novo)
- `frontend/app/admin/purchases/page.tsx` (novo)
- `backend/tests/routes/test_purchases_checkout.py` (novo)
- `backend/tests/webhooks/test_payment_handler.py` (novo)

---

## Definition of Done

- [ ] Migração aplicada em produção
- [ ] Test purchase em Stripe test mode bem-sucedido (status: pending → paid)
- [ ] Webhook replay bem-sucedido (idempotência validada)
- [ ] `pytest backend/tests/routes/test_purchases_checkout.py` + `test_payment_handler.py` passando
- [ ] E2E Playwright cobrindo checkout flow
- [ ] Dashboard admin mostra compras em tempo real

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — bloqueador Wave 1 para todos os relatórios pagos + pacotes de dados + AI Copilot one-shot |
