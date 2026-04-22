# MON-SUB-01: Add-ons Recorrentes Stripe + Schema `monitored_subscriptions` + Watchlists

**Priority:** P0
**Effort:** M (3 dias)
**Squad:** @dev + @devops
**Status:** Draft
**Epic:** [EPIC-MON-SUBS-2026-04](EPIC-MON-SUBS-2026-04.md)
**Sprint:** Wave 2 (bloqueador de MON-SUB-02/03/04 + MON-AI-02 + MON-AI-03 + MON-DIST-02)

---

## Contexto

Hoje existe 1 plano recorrente (Smartlic Pro) via `plan_billing_periods`. Não há conceito de **add-ons vendáveis separadamente**. Para lançar 3 monitores (Camada 3) + Copilot add-on (MON-AI-02) + Radar Preditivo (MON-AI-03), precisamos:

- Modelo Stripe com múltiplos `subscription_items` por customer (plano base + add-ons)
- Schema interno `monitored_subscriptions` rastreando cada add-on independentemente
- `watchlist_items` para entidades monitoradas (setor, UF, órgão, CNPJ)
- Add-ons devem funcionar **standalone** (sem plano base) ou **over-plan**

---

## Acceptance Criteria

### AC1: Tabela `monitored_subscriptions`

- [ ] Migração:
```sql
CREATE TABLE public.monitored_subscriptions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  addon_type text NOT NULL CHECK (addon_type IN (
    'monitor_segmento_uf', 'monitor_orgao', 'radar_risco',
    'ai_copilot', 'radar_preditivo'
  )),
  tier text NOT NULL,  -- 'basic'|'standard'|'premium'
  stripe_subscription_id text NOT NULL,
  stripe_subscription_item_id text NOT NULL UNIQUE,
  stripe_price_id text NOT NULL,
  config jsonb NOT NULL DEFAULT '{}'::jsonb,  -- parametros específicos do addon
  cadence text NOT NULL DEFAULT 'monthly' CHECK (cadence IN ('daily', 'weekly', 'monthly')),
  price_cents int NOT NULL,
  active boolean NOT NULL DEFAULT true,
  started_at timestamptz NOT NULL DEFAULT now(),
  current_period_end timestamptz NULL,
  cancelled_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON monitored_subscriptions (user_id, active, addon_type);
```
- [ ] RLS: user sees only own
- [ ] Migração paired down

### AC2: Tabela `watchlist_items`

- [ ] Migração:
```sql
CREATE TABLE public.watchlist_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subscription_id uuid NOT NULL REFERENCES monitored_subscriptions(id) ON DELETE CASCADE,
  entity_type text NOT NULL CHECK (entity_type IN ('setor', 'uf', 'orgao_cnpj', 'fornecedor_cnpj')),
  entity_id text NOT NULL,  -- setor slug, UF code, CNPJ 14 digits
  entity_metadata jsonb NULL,  -- label, config customizada
  added_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(subscription_id, entity_type, entity_id)
);
CREATE INDEX ON watchlist_items (entity_type, entity_id);
```
- [ ] Constraint de tier: basic=10 items max, standard=50, premium=500 (check em application layer)

### AC3: Endpoints CRUD

- [ ] `POST /v1/monitors` — cria nova assinatura add-on:
  - Body: `{addon_type, tier, config, watchlist_items: [...]}`
  - Cria Stripe subscription_item (em sub existente ou cria sub nova)
  - Insere `monitored_subscriptions` + `watchlist_items`
  - Retorna `{id, stripe_subscription_id, next_charge_date, total_cents}`
- [ ] `GET /v1/monitors` — lista assinaturas ativas do user
- [ ] `PATCH /v1/monitors/{id}` — atualizar config, tier, watchlist
- [ ] `DELETE /v1/monitors/{id}` — cancela no Stripe (end of period) + marca `cancelled_at`
- [ ] `POST /v1/monitors/{id}/watchlist` — adiciona item
- [ ] `DELETE /v1/monitors/{id}/watchlist/{item_id}` — remove item

### AC4: Webhook handlers extendidos

- [ ] `backend/webhooks/handlers/subscription_item.py`:
  - `customer.subscription.updated` → sincroniza `stripe_subscription_item_id`, `current_period_end`
  - `invoice.paid` → confirma pagamento, pode disparar geração primeiro relatório
  - `customer.subscription.deleted` → marca add-on inativo

### AC5: Dashboard frontend `/conta/monitores`

- [ ] `frontend/app/conta/monitores/page.tsx`:
  - Lista add-ons ativos (cards por add-on)
  - Para cada: tier, próxima cobrança, watchlist, botões Editar/Cancelar
  - "Criar novo monitor" → wizard: tipo → tier → watchlist → checkout
  - Integração com Stripe Billing Portal para atualização de payment method

### AC6: Catálogo de add-ons em Stripe

- [ ] Script `scripts/stripe_setup_addons.py` (run-once):
  - Cria Products Stripe para cada addon_type × tier (3×3 + 2×1 = 11 prices)
  - Printa mapeamento para Railway env vars (`STRIPE_PRICE_MONITOR_SEG_UF_BASIC`, etc)
- [ ] Lookup table em `backend/services/addon_catalog.py`

### AC7: Testes

- [ ] Unit: `test_monitors_crud.py`
  - Create monitor happy path → Stripe called + DB row
  - Watchlist limit por tier (basic=10, standard=50)
  - Cancel → Stripe called + DB updated
- [ ] Integration: webhook flow E2E (mock Stripe)
- [ ] E2E Playwright: user cria Monitor de Segmento UF, adiciona watchlist, cancela

---

## Scope

**IN:**
- Migrações + RLS
- CRUD endpoints + webhook handlers
- Dashboard frontend
- Stripe setup script
- Testes

**OUT:**
- Geração dos relatórios (MON-SUB-02/03/04)
- Add-ons de AI (MON-AI-02/03) — usam este foundation
- Upgrade/downgrade tier (v2; v1 = cancelar + criar novo)

---

## Dependências

- Stripe account + Billing Portal configurado
- Nenhuma story anterior (é foundation da Wave 2)

---

## Riscos

- **Complexidade de multi-add-on billing:** testar com combinações (plan base + 2 add-ons simultâneos)
- **Downgrade sem proration:** Stripe auto-proration cobre; documentar expectativa usuário
- **Webhook race conditions:** events podem chegar fora de ordem; lógica idempotente por `stripe_subscription_item_id`

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `supabase/migrations/.../create_monitored_subscriptions.sql` + `.down.sql`
- `supabase/migrations/.../create_watchlist_items.sql` + `.down.sql`
- `backend/routes/monitors.py` (novo)
- `backend/services/addon_catalog.py` (novo)
- `backend/webhooks/handlers/subscription_item.py` (novo)
- `scripts/stripe_setup_addons.py` (novo)
- `frontend/app/conta/monitores/page.tsx` (novo)
- `backend/tests/routes/test_monitors_crud.py` (novo)

---

## Definition of Done

- [ ] Stripe setup script executado em test + prod
- [ ] Migração aplicada
- [ ] User cria add-on via dashboard → Stripe sub_item criado + DB consistente
- [ ] Cancel → Stripe cancels + ativo=false no período atual
- [ ] Testes passando

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — foundation Wave 2; habilita 5 add-ons recorrentes |
