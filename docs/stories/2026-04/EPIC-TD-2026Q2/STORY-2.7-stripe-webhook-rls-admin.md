# STORY-2.7: Stripe Webhook RLS Admin Policy Fix (TD-DB-010)

**Priority:** P1 (admins não conseguem debug payment failures)
**Effort:** XS (1h)
**Squad:** @data-engineer + @dev quality gate
**Status:** Draft
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

- [ ] Drop policy atual `webhook_events_select_admin` (que checa `plan_type='master'`)
- [ ] Recreate policy checking `is_admin=true OR is_master=true`

```sql
DROP POLICY IF EXISTS "webhook_events_select_admin" ON public.stripe_webhook_events;
CREATE POLICY "webhook_events_select_admin" ON public.stripe_webhook_events
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM public.profiles WHERE profiles.id = auth.uid() AND (profiles.is_admin = true OR profiles.is_master = true))
  );
```

### AC2: Test em prod

- [ ] Login com user `is_admin=true` (não master) — pode listar webhook events via Supabase REST
- [ ] Login com user regular — recebe empty list (RLS funciona)

---

## Tasks / Subtasks

- [ ] Task 1: Migration nova
- [ ] Task 2: Aplicar via CRIT-050 deploy
- [ ] Task 3: Validation com 2 user types

## Dev Notes

- DB-AUDIT TD-DB-010 ref
- `profiles.is_admin` boolean já existe; `is_master` também

## Testing

- pytest backend test que admin pode SELECT
- Manual via Supabase Studio

## Definition of Done

- [ ] Migration aplicada + admin debug funciona

## Risks

- **R1**: Outros admins privilegiados além de is_admin/is_master? — mitigation: confirmar com PM

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
