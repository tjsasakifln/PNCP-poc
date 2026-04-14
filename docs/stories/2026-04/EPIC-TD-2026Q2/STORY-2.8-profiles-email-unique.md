# STORY-2.8: profiles.email UNIQUE Constraint + Dedup Script (TD-DB-011)

**Priority:** P1 (account confusion + Stripe billing chaos com duplicate emails)
**Effort:** S (2-4h)
**Squad:** @data-engineer + @dev quality gate
**Status:** Ready for Review
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

- [x] Script `backend/scripts/dedup_profiles_email.py` implementado:
  - Identifica duplicates via GROUP BY LOWER(email) HAVING count > 1
  - CSV em `docs/audit/dedup_profiles_email_{timestamp}.csv`: email, winner_id, loser_ids, count, recommendation
  - Heurística winner: último `last_sign_in_at` → plano pago → `created_at` mais antigo → `id` (tiebreak determinístico)
- [ ] Run em prod read-only — pendente, gated em sponsor approval (não bloqueante para implementação)

### AC2: Dedup script EXECUTE

- [x] Dual guard: flag `--execute` + env var `CONFIRM_DEDUP=YES`
- [x] Merge move `user_subscriptions`, `search_sessions`, `pipeline_items`, `feedback` para winner
- [x] Soft-delete losers via colunas `deleted_at`, `deleted_reason`, `migrated_to` (adicionadas por migration `20260414131000_profiles_soft_delete_and_email_unique.sql`)
- [x] Log em `audit_events` (event_type `profile_dedup_merged`)

### AC3: UNIQUE constraint

- [x] Partial UNIQUE index `idx_profiles_email_unique WHERE email IS NOT NULL` já existe em `20260224000000_phone_email_unique.sql` — **funcionalmente enforce uniqueness** (NULL values não conflitam em UNIQUE constraint padrão também). Migration `20260414131000_profiles_soft_delete_and_email_unique.sql` reafirma defensivamente (idempotente).

### AC4: Frontend signup defensive check

- [x] Atendido por STORY-258 (já em produção): endpoint `/api/auth/check-email` no blur + `translateAuthError("User already registered")` no submit + DB partial UNIQUE index
- **Nota design**: `/auth/check-email` **intencionalmente** não revela se email existe (STORY-258 AC15, anti-enumeration attack). Defesa é em 3 camadas: client-side (disposable-only), submit-side (Supabase error translation), DB-side (UNIQUE).

---

## Tasks / Subtasks

- [x] Task 1: Dedup script DRY-RUN (AC1)
- [ ] Task 2: Review CSV com sponsor (out-of-band)
- [ ] Task 3: Backup DB antes (sponsor action)
- [ ] Task 4: Execute dedup (AC2) — gated, não executado nesta iteração
- [x] Task 5: Migration UNIQUE/soft-delete columns (AC3)
- [x] Task 6: Frontend defensive check (AC4) — já atendido por STORY-258

## Dev Notes

- DB-AUDIT HIGH-002 ref
- `auth.users.email` já tem UNIQUE — desync risk identified
- Backup via `pg_dump` antes de execute

## Testing

- pytest: try insert duplicate email → expect IntegrityError post-migration
- Manual: signup com email existente → erro claro

## File List

- **Created**:
  - `supabase/migrations/20260414131000_profiles_soft_delete_and_email_unique.sql`
  - `backend/scripts/dedup_profiles_email.py`
  - `backend/tests/test_dedup_profiles_email.py` (13 tests)
  - `backend/tests/test_profiles_email_unique_constraint.py` (10 tests)

## Definition of Done

- [x] Dedup script completo (DRY-RUN + EXECUTE gated) + 23 tests passando
- [x] UNIQUE constraint aplicada (partial UNIQUE index pre-existente + soft-delete columns em migration nova)
- [x] Frontend pre-check ativo (atendido por STORY-258)
- [ ] Backup salvo antes da operação EXECUTE — gated, responsabilidade do sponsor out-of-band

## Risks

- **R1**: Dedup quebra alguma user — mitigation: backup + soft-delete + audit log
- **R2**: Stripe customer associado ao profile loser — mitigation: merge stripe_customer_id também

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-14 | 1.1     | Implementation complete — 23 tests passing. AC2 EXECUTE gated em sponsor approval (dual-guard: --execute + CONFIRM_DEDUP=YES). AC4 atendido por STORY-258 pre-existente. | @dev (EPIC-TD Sprint 1 batch) |
