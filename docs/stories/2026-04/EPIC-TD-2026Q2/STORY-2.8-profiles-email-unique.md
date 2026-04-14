# STORY-2.8: profiles.email UNIQUE Constraint + Dedup Script (TD-DB-011)

**Priority:** P1 (account confusion + Stripe billing chaos com duplicate emails)
**Effort:** S (2-4h)
**Squad:** @data-engineer + @dev quality gate
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 1

---

## Story

**As a** SmartLic,
**I want** garantir email único por profile (após dedup de existentes),
**so that** evite contas duplicadas, Stripe customer chaos e search history orphan.

---

## Acceptance Criteria

### AC1: Dedup script DRY-RUN

- [ ] Script Python `scripts/dedup_profiles_email.py` que:
  - Identifica profiles com email duplicate
  - Outputs CSV: email, profile_ids, created_at, plan_type, last_login
  - Recommendation: qual manter (mais recente login com paid plan)
- [ ] Run em prod read-only — output review manual

### AC2: Dedup script EXECUTE

- [ ] Após approval @sponsor, script executa merge:
  - Move user_subscriptions, search_sessions, pipeline_items para profile_id "winner"
  - Soft-delete profiles "losers" (não hard delete)
  - Log em `audit_events`

### AC3: UNIQUE constraint

- [ ] Migration:
  ```sql
  ALTER TABLE public.profiles ADD CONSTRAINT unique_profiles_email UNIQUE (email);
  ```

### AC4: Frontend signup defensive check

- [ ] Signup form pre-check `/check-email-available` antes de submit
- [ ] Mensagem clara se email duplicate

---

## Tasks / Subtasks

- [ ] Task 1: Dedup script DRY-RUN (AC1)
- [ ] Task 2: Review CSV com sponsor
- [ ] Task 3: Backup DB antes (precaution)
- [ ] Task 4: Execute dedup (AC2)
- [ ] Task 5: Migration UNIQUE (AC3)
- [ ] Task 6: Frontend defensive check (AC4)

## Dev Notes

- DB-AUDIT HIGH-002 ref
- `auth.users.email` já tem UNIQUE — desync risk identified
- Backup via `pg_dump` antes de execute

## Testing

- pytest: try insert duplicate email → expect IntegrityError post-migration
- Manual: signup com email existente → erro claro

## Definition of Done

- [ ] Dedup completed (logs em audit_events)
- [ ] UNIQUE constraint aplicada
- [ ] Frontend pre-check ativo
- [ ] Backup salvo antes da operação

## Risks

- **R1**: Dedup quebra alguma user — mitigation: backup + soft-delete + audit log
- **R2**: Stripe customer associado ao profile loser — mitigation: merge stripe_customer_id também

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
