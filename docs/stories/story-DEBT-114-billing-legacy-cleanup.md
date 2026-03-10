# DEBT-114: Billing Legacy Cleanup — stripe_price_id

**Prioridade:** GTM-RISK (30 dias)
**Estimativa:** 4h
**Fonte:** Brownfield Discovery — @data-engineer (DB-013)
**Score Impact:** Billing 8→9
**Status:** COMPLETED (2026-03-10)

## Contexto
`plans.stripe_price_id` está marcado como DEPRECATED mas billing.py ainda usa como fallback. Source of truth é `plan_billing_periods.stripe_price_id` desde STORY-360.

## Acceptance Criteria

- [x] AC1: billing.py usa APENAS plan_billing_periods para buscar stripe_price_id (remover fallback para plans.stripe_price_id)
- [x] AC2: WARNING log adicionado se código legado for acessado (safety net por 1 semana)
- [x] AC3: Todos os testes de billing passam (test_billing.py, test_stripe_webhook.py, test_payment_failed_webhook.py)
- [ ] AC4: Smoke test manual: criar checkout session via /planos funciona
- [ ] AC5: Após 1 semana sem WARNING logs, criar follow-up migration para DROP COLUMN plans.stripe_price_id

## File List
- [x] `backend/routes/billing.py` (EDIT) — Removed legacy `plans.stripe_price_id` fallback, now queries `plan_billing_periods` table exclusively
- [ ] `backend/services/billing.py` — No changes needed (already uses per-period price IDs from `plans` table columns, not the deprecated `stripe_price_id`)
- [x] `backend/tests/test_debt114_billing_legacy_cleanup.py` (NEW) — 13 tests covering AC1+AC2
- [x] `backend/tests/test_debt017_database_optimization.py` (EDIT) — Updated assertion from "fallback must exist" to "fallback must be removed"
- [x] `backend/tests/test_organizations.py` (EDIT) — Updated checkout mock to use side_effect for two sb_execute calls

## Implementation Notes

### AC1 Changes (billing.py)
- `create_checkout()` now queries `plan_billing_periods` table with `plan_id + billing_period` filter
- Plans query narrowed from `SELECT *` to `SELECT id, name, is_active` (no longer needs price columns)
- Removed `price_id_key = f"stripe_price_id_{billing_period}"` pattern
- Removed `plan.get("stripe_price_id")` fallback

### AC2 Changes
- WARNING log with `DEBT-114:` prefix emitted when `plan_billing_periods` has no `stripe_price_id` for the requested plan+period combo
- Message explicitly states "Legacy plans.stripe_price_id fallback has been removed"

### AC5 Follow-up
After 1 week of monitoring (target: 2026-03-17), if no DEBT-114 WARNING logs appear in Railway:
```sql
ALTER TABLE public.plans DROP COLUMN IF EXISTS stripe_price_id;
```
