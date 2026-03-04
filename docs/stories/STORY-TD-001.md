# STORY-TD-001: FK Standardization + search_results_store Hardening

**Epic:** Resolucao de Debito Tecnico
**Tier:** 0
**Area:** Database
**Estimativa:** 10.5h (8h codigo + 2.5h testes)
**Prioridade:** P0
**Debt IDs:** C-01, H-02, H-03, M-03, L-06

## Objetivo

Corrigir o unico debito CRITICO do sistema: 6 tabelas com FK apontando para `auth.users` em vez de `profiles`. Isso cria risco de integridade em disaster recovery (se auth.users for restaurado de backup diferente, FKs quebram). Simultaneamente, endurecer `search_results_store` com retention automatica e indice composto para queries de limpeza.

**Tabelas afetadas pelo C-01:**
1. `search_results_store` (user_id -> auth.users)
2. `mfa_recovery_codes` (user_id -> auth.users)
3. `mfa_recovery_attempts` (user_id -> auth.users)
4. `organizations` (owner_id -> auth.users)
5. `org_members` (user_id -> auth.users)
6. `partner_referrals` (referred_user_id -> auth.users)

## Acceptance Criteria

### Migration 1: FK Standardization (C-01 + H-02 + M-03)
- [ ] AC1: Criar migration que re-aponta todas 6 FKs de `auth.users(id)` para `public.profiles(id)`
- [ ] AC2: Usar `NOT VALID` + separado `VALIDATE CONSTRAINT` para zero-downtime (nao bloqueia tabela)
- [ ] AC3: `search_results_store` FK inclui `ON DELETE CASCADE` (resolve H-02)
- [ ] AC4: `partner_referrals` FK inclui `ON DELETE SET NULL` (resolve M-03)
- [ ] AC5: Executar orphan detection query ANTES da migration: `SELECT id FROM tabela WHERE user_id NOT IN (SELECT id FROM profiles)` para cada tabela
- [ ] AC6: Migration testada em ambiente local com dados reais (dump parcial)

### Migration 2: search_results_store Hardening (H-03 + L-06)
- [ ] AC7: Criar composite index `(user_id, expires_at)` em search_results_store (L-06)
- [ ] AC8: Criar pg_cron job para cleanup diario: `DELETE FROM search_results_store WHERE expires_at < NOW() - INTERVAL '7 days'` (H-03)
- [ ] AC9: pg_cron job agendado para 4am UTC (horario de menor uso)
- [ ] AC10: Adicionar CHECK constraint para `octet_length(result_data::text) < 2097152` (2MB max por row)
- [ ] AC11: Verificar que pg_cron extension esta habilitada no Supabase Cloud

### Validacao
- [ ] AC12: Zero rows com FK apontando para auth.users apos migration
- [ ] AC13: `\d+ search_results_store` mostra FK para profiles com ON DELETE CASCADE
- [ ] AC14: pg_cron job visivel em `cron.job` table
- [ ] AC15: Todos 5774+ backend tests passam sem regressao

## Technical Notes

**Zero-downtime FK migration pattern:**
```sql
-- Step 1: Drop old FK
ALTER TABLE search_results_store DROP CONSTRAINT IF EXISTS search_results_store_user_id_fkey;

-- Step 2: Add new FK with NOT VALID (instant, no table scan)
ALTER TABLE search_results_store
  ADD CONSTRAINT search_results_store_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES public.profiles(id) ON DELETE CASCADE
  NOT VALID;

-- Step 3: Validate separately (concurrent-safe, reads only)
ALTER TABLE search_results_store VALIDATE CONSTRAINT search_results_store_user_id_fkey;
```

**Orphan detection (run BEFORE migration):**
```sql
-- If any rows returned, must fix manually before migration
SELECT 'search_results_store' AS tbl, count(*) FROM search_results_store WHERE user_id NOT IN (SELECT id FROM profiles)
UNION ALL
SELECT 'mfa_recovery_codes', count(*) FROM mfa_recovery_codes WHERE user_id NOT IN (SELECT id FROM profiles)
UNION ALL
SELECT 'mfa_recovery_attempts', count(*) FROM mfa_recovery_attempts WHERE user_id NOT IN (SELECT id FROM profiles)
UNION ALL
SELECT 'organizations', count(*) FROM organizations WHERE owner_id NOT IN (SELECT id FROM profiles)
UNION ALL
SELECT 'org_members', count(*) FROM org_members WHERE user_id NOT IN (SELECT id FROM profiles)
UNION ALL
SELECT 'partner_referrals', count(*) FROM partner_referrals WHERE referred_user_id NOT IN (SELECT id FROM profiles);
```

**pg_cron setup:**
```sql
-- Supabase has pg_cron enabled by default
SELECT cron.schedule(
  'cleanup-expired-search-results',
  '0 4 * * *',  -- 4am UTC daily
  $$DELETE FROM public.search_results_store WHERE expires_at < NOW() - INTERVAL '7 days'$$
);
```

**Deploy timing:** Preferir 4am UTC (menor uso). Se orphans encontrados, resolver manualmente antes.

## Dependencies

- Nenhuma — esta e a primeira story do epic
- Requer acesso ao Supabase Cloud (migration push)
- pg_cron extension deve estar habilitada

## Definition of Done
- [ ] Migration criada em `supabase/migrations/`
- [ ] Orphan detection query executada (zero orphans confirmado)
- [ ] Migration aplicada no Supabase Cloud via `supabase db push`
- [ ] pg_cron job confirmado rodando
- [ ] Composite index confirmado via `\d+ search_results_store`
- [ ] All 5774+ backend tests passing
- [ ] No regressions in frontend tests
- [ ] Reviewed by @data-engineer
