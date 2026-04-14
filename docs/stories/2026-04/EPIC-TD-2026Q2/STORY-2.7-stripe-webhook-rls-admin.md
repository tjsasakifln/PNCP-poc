# STORY-2.7: Stripe Webhook RLS Admin Policy Fix (TD-DB-010)

**Priority:** P1 (admins não conseguem debug payment failures)
**Effort:** XS (1h)
**Squad:** @data-engineer + @dev quality gate
**Status:** Ready for Review
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 1

---

## Story

**As a** admin SmartLic,
**I want** poder ler `stripe_webhook_events` para debug payment issues,
**so that** suporte a payment failures não fique bloqueado.

---

## Acceptance Criteria

### AC1: RLS policy fix

- [x] Drop policy atual `webhook_events_select_admin` (que checa `plan_type='master'`)
- [x] Recreate policy checking `is_admin=true OR is_master=true` — adaptação: `is_admin = true OR plan_type = 'master'` porque `is_master` **não existe como coluna real** em `profiles` (é derivação lógica conforme `backend/authorization.py`). Mantém paridade semântica com backend.

```sql
DROP POLICY IF EXISTS "webhook_events_select_admin" ON public.stripe_webhook_events;
CREATE POLICY "webhook_events_select_admin" ON public.stripe_webhook_events
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM public.profiles WHERE profiles.id = auth.uid() AND (profiles.is_admin = true OR profiles.is_master = true))
  );
```

### AC2: Test em prod

- [x] Validação via regex test cobre correctness da migration (9 testes passando em `backend/tests/test_stripe_webhook_rls.py`).
- [ ] Smoke E2E prod após CRIT-050 auto-apply: login com `is_admin=true` lista webhook events; regular retorna empty list. Gated em deploy.

---

## Tasks / Subtasks

- [x] Task 1: Migration nova — `supabase/migrations/20260414130000_fix_stripe_webhook_rls_admin.sql`
- [ ] Task 2: Aplicar via CRIT-050 deploy — automático após push para main
- [ ] Task 3: Validation com 2 user types em prod — post-deploy smoke

## Dev Notes

- DB-AUDIT TD-DB-010 ref
- `profiles.is_admin` boolean já existe; `is_master` é derivado (`is_admin OR plan_type='master'`), não coluna real.

## Testing

- pytest backend test que admin pode SELECT
- Manual via Supabase Studio

## File List

- **Created**:
  - `supabase/migrations/20260414130000_fix_stripe_webhook_rls_admin.sql`
  - `backend/tests/test_stripe_webhook_rls.py`

## Definition of Done

- [x] Migration criada + tests passando (pre-deploy).
- [ ] Migration aplicada via deploy.yml (CRIT-050) + admin debug funciona (post-deploy).

## Risks

- **R1**: Outros admins privilegiados além de is_admin/is_master? — mitigation: confirmar com PM

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-14 | 1.1     | Implementation complete — migration + 9 tests. Adapted `is_master` to `plan_type='master'` (coluna real). | @dev (EPIC-TD Sprint 1 batch) |
