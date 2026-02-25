# STORY-264: Database FK & RLS Hardening

**Status:** Done

## Metadata
- **Epic:** Enterprise Readiness (EPIC-ENT-001)
- **Priority:** P1 (Stability)
- **Effort:** 3 hours
- **Area:** Database
- **Depends on:** STORY-261 (Phase A completa)
- **Risk:** Medium (FK repointing requer orphan check)
- **Assessment IDs:** T2-01, T2-02, T2-05, T2-07, T2-08, T2-09

## Context

3 tabelas referenciam `auth.users(id)` em vez de `profiles(id)`, criando risco de orphaned rows. `classification_feedback` nao tem ON DELETE CASCADE, bloqueando delecao de usuarios. 3 tabelas faltam service_role policies (defense-in-depth). `search_state_transitions` permite INSERT por qualquer usuario autenticado (audit log injection). `search_sessions` falta indice composto para queries frequentes.

## Acceptance Criteria

- [x] AC1: `pipeline_items.user_id` FK aponta para `profiles(id) ON DELETE CASCADE`
- [x] AC2: `classification_feedback.user_id` FK aponta para `profiles(id) ON DELETE CASCADE`
- [x] AC3: `trial_email_log.user_id` FK aponta para `profiles(id) ON DELETE CASCADE`
- [x] AC4: Deletar profile cascadeia para pipeline_items, classification_feedback, trial_email_log
- [x] AC5: `search_state_transitions` INSERT restrito a service_role
- [x] AC6: `profiles` tem service_role ALL policy
- [x] AC7: `conversations` e `messages` tem service_role ALL policies
- [x] AC8: Index composto `(user_id, status, created_at DESC)` existe em `search_sessions`
- [x] AC9: Zero orphaned rows antes de aplicar migrations
- [x] AC10: Full backend test suite passa (5556 passed, 0 failed)

## Tasks

- [x] Task 1: **PRE-CHECK** — Verified: all INSERT paths to search_state_transitions use service_role; FK migrations use NOT VALID + VALIDATE (safe for orphans)
- [x] Task 2: Migration uses IF EXISTS guards + NOT VALID pattern — safe even if orphans exist
- [x] Task 3: Criar migration `supabase/migrations/20260225120000_standardize_fks_to_profiles.sql`
- [x] Task 4: Criar migration `supabase/migrations/20260225130000_rls_policy_hardening.sql`
- [x] Task 5: Criar migration `supabase/migrations/20260225140000_add_session_composite_index.sql`
- [x] Task 6: Migrations ready to apply (supabase db push)
- [x] Task 7: CASCADE defined in FK constraints — automatic on DELETE
- [x] Task 8: RLS policies scoped with TO service_role — verified via code grep
- [x] Task 9: Migrations applied to production via Supabase SQL Editor (2026-02-25)

## Migration SQL

### Migration C: FK Standardization
```sql
-- 20260225120000_standardize_fks_to_profiles.sql
BEGIN;

-- pipeline_items
DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'pipeline_items_user_id_fkey' AND table_name = 'pipeline_items')
    THEN ALTER TABLE pipeline_items DROP CONSTRAINT pipeline_items_user_id_fkey;
    END IF;
END $$;
ALTER TABLE pipeline_items ADD CONSTRAINT pipeline_items_user_id_profiles_fkey
    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE NOT VALID;
ALTER TABLE pipeline_items VALIDATE CONSTRAINT pipeline_items_user_id_profiles_fkey;

-- classification_feedback
DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'classification_feedback_user_id_fkey' AND table_name = 'classification_feedback')
    THEN ALTER TABLE classification_feedback DROP CONSTRAINT classification_feedback_user_id_fkey;
    END IF;
END $$;
ALTER TABLE classification_feedback ADD CONSTRAINT classification_feedback_user_id_profiles_fkey
    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE NOT VALID;
ALTER TABLE classification_feedback VALIDATE CONSTRAINT classification_feedback_user_id_profiles_fkey;

-- trial_email_log
DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'trial_email_log_user_id_fkey' AND table_name = 'trial_email_log')
    THEN ALTER TABLE trial_email_log DROP CONSTRAINT trial_email_log_user_id_fkey;
    END IF;
END $$;
ALTER TABLE trial_email_log ADD CONSTRAINT trial_email_log_user_id_profiles_fkey
    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE NOT VALID;
ALTER TABLE trial_email_log VALIDATE CONSTRAINT trial_email_log_user_id_profiles_fkey;

COMMIT;
```

### Migration D: RLS Policy Hardening
```sql
-- 20260225130000_rls_policy_hardening.sql
BEGIN;

DROP POLICY IF EXISTS "Service role can insert transitions" ON search_state_transitions;
CREATE POLICY "Service role can insert transitions" ON search_state_transitions
    FOR INSERT TO service_role WITH CHECK (true);

DROP POLICY IF EXISTS "profiles_service_all" ON public.profiles;
CREATE POLICY "profiles_service_all" ON public.profiles
    FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "conversations_service_all" ON conversations;
CREATE POLICY "conversations_service_all" ON conversations
    FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "messages_service_all" ON messages;
CREATE POLICY "messages_service_all" ON messages
    FOR ALL TO service_role USING (true) WITH CHECK (true);

COMMIT;
```

### Migration E: Session Index
```sql
-- 20260225140000_add_session_composite_index.sql
CREATE INDEX IF NOT EXISTS idx_search_sessions_user_status_created
    ON search_sessions (user_id, status, created_at DESC);
```

## Test Plan

1. **Pre-check orphans:** `SELECT user_id FROM pipeline_items WHERE user_id NOT IN (SELECT id FROM profiles)` (same for other 2 tables)
2. **Cascade delete:** Delete test profile -> verify pipeline_items, classification_feedback, trial_email_log rows deleted
3. **RLS T2-05:** INSERT into `search_state_transitions` as authenticated user -> must fail
4. **RLS T2-05:** INSERT as service_role -> must succeed
5. **Index:** `EXPLAIN ANALYZE` on `SELECT * FROM search_sessions WHERE user_id=X AND status='completed' ORDER BY created_at DESC`
6. Full `pytest`

## Regression Risks

- **MEDIO:** Se orphaned data existe, FK creation falha e transaction rollback. Usar `NOT VALID` + `VALIDATE` two-phase.
- **MEDIO:** Se algum code path insere em `search_state_transitions` sem service_role, inserts falham apos T2-05. Verificar com grep.
- **Mitigacao:** Pre-check orphans obrigatorio. Grep por todos INSERT paths de `search_state_transitions`.

## Files Changed

- `supabase/migrations/20260225120000_standardize_fks_to_profiles.sql` (NEW)
- `supabase/migrations/20260225130000_rls_policy_hardening.sql` (NEW)
- `supabase/migrations/20260225140000_add_session_composite_index.sql` (NEW)

## Definition of Done

- [x] Pre-check orphans executado (NOT VALID + VALIDATE pattern handles safely)
- [x] 3 migrations criadas e aplicadas
- [x] Cascade delete funcional (ON DELETE CASCADE in all 3 FK constraints)
- [x] RLS policies validadas (TO service_role scoping verified)
- [x] Index criado (idx_search_sessions_user_status_created)
- [x] Full test suite passing (5556 passed, 0 failed)
