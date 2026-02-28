# STORY-318: Split Concurrency Safety Migration

**Status:** Done
**Priority:** High
**Sprint:** Current
**Points:** 2
**Agent:** @data-engineer

## Context

A migration `20260227120000_concurrency_safety.sql` (STORY-307) falha no `supabase db push` porque contém múltiplos statements incluindo uma `CREATE OR REPLACE FUNCTION` com PL/pgSQL. O Supabase CLI não suporta múltiplos comandos em uma prepared statement (SQLSTATE 42601).

**Erro:**
```
ERROR: cannot insert multiple commands into a prepared statement (SQLSTATE 42601)
At statement: 5
-- Fix 3: Quota Atomicity — Atomic Fallback RPC
```

As migrations subsequentes (`add_dunning_fields`, `story310_trial_email_sequence`) também estão bloqueadas.

## Acceptance Criteria

- [x] **AC1:** Remover `20260227120000_concurrency_safety.sql` do diretório de migrations
- [x] **AC2:** Criar `20260227120001_concurrency_stripe_webhook.sql` — ALTER TABLE stripe_webhook_events (status + received_at + backfill + GRANT)
- [x] **AC3:** Criar `20260227120002_concurrency_pipeline_version.sql` — ALTER TABLE pipeline_items (version column)
- [x] **AC4:** Criar `20260227120003_concurrency_quota_rpc.sql` — CREATE OR REPLACE FUNCTION (isolado) + `120004` para GRANT
- [x] **AC5:** Executar `supabase db push` com sucesso (todas 4 split + dunning + trial_email)
- [x] **AC6:** Verificar que as colunas `status`, `received_at` existem em `stripe_webhook_events`
- [x] **AC7:** Verificar que `version` existe em `pipeline_items`
- [x] **AC8:** Verificar que `increment_quota_fallback_atomic()` funciona via `SELECT * FROM increment_quota_fallback_atomic(...)`

## Technical Notes

- O Supabase CLI executa cada migration como prepared statement via PostgREST
- PL/pgSQL functions com `BEGIN...END` contam como múltiplos statements internos
- A solução é isolar a function creation em seu próprio arquivo de migration
- **Descoberta:** Mesmo isolada, a function + GRANT no mesmo arquivo ainda causa SQLSTATE 42601. A solução final foi 4 arquivos: function em `120003`, GRANT em `120004`.
- Timestamps das novas migrations devem manter ordem: `120001`, `120002`, `120003`, `120004` (entre `120000` e `130000`)
- A migration original `120000` deve ser deletada DEPOIS de confirmar que as novas aplicaram

## Migration Content Reference

**File 1 — `20260227120001_concurrency_stripe_webhook.sql`:**
```sql
ALTER TABLE stripe_webhook_events ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'completed' NOT NULL;
ALTER TABLE stripe_webhook_events ADD COLUMN IF NOT EXISTS received_at TIMESTAMPTZ DEFAULT NOW();
UPDATE stripe_webhook_events SET received_at = processed_at WHERE received_at IS NULL OR received_at = NOW();
GRANT UPDATE ON stripe_webhook_events TO service_role;
```

**File 2 — `20260227120002_concurrency_pipeline_version.sql`:**
```sql
ALTER TABLE pipeline_items ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1 NOT NULL;
```

**File 3 — `20260227120003_concurrency_quota_rpc.sql`:**
```sql
CREATE OR REPLACE FUNCTION increment_quota_fallback_atomic(...) ... $$ LANGUAGE plpgsql;
GRANT EXECUTE ON FUNCTION increment_quota_fallback_atomic(UUID, TEXT, INTEGER) TO service_role;
```

## Definition of Done

- [x] All 4 split migrations apply cleanly via `supabase db push`
- [x] Pending migrations (dunning, trial_email) also apply
- [x] Original `120000` file removed
- [x] No regressions in backend tests (5 migration-content tests updated to reference split files)

## File List

| Action | File |
|--------|------|
| DELETE | `supabase/migrations/20260227120000_concurrency_safety.sql` |
| CREATE | `supabase/migrations/20260227120001_concurrency_stripe_webhook.sql` |
| CREATE | `supabase/migrations/20260227120002_concurrency_pipeline_version.sql` |
| CREATE | `supabase/migrations/20260227120003_concurrency_quota_rpc.sql` |
| CREATE | `supabase/migrations/20260227120004_concurrency_quota_rpc_grant.sql` |
