# SmartLic Database Audit

## Executive Summary

- **Tables audited**: 23
- **Critical issues**: 4 🔴 (3 addressed via DEBT-001, 1 pending)
- **High severity**: 6 ⚠️
- **Medium severity**: 5 💡
- **Low/Style**: 4
- **Overall Score**: **62/100**

### Scoring Justification

- ✅ Solid RLS foundation, but significant gaps in user_id indexing (100x perf impact)
- ✅ Excellent index design on `pncp_raw_bids` (8 purpose-built indexes, GIN FTS)
- ✅ DEBT-210 optimization (pre-computed tsvector, batch upsert)
- ⚠️ 60% das migrations focaram em fixes/debt paydown — sinal de iteração pós-launch
- ⚠️ Data retention (purge_old_bids, health_checks, search_results_cache) não completamente automatizada
- ⚠️ Sem `down.sql` migration templates (rollback manual)

---

## Critical Issues 🔴

### TD-DB-001 — Service-Role RLS Bypass Missing on `search_sessions` (FIXED)

- **Severity**: CRITICAL (historical)
- **Status**: ✅ FIXED em `006b_search_sessions_service_role_policy.sql` (2026-02-10)
- **Finding**: Migration 001 criou tabela com policies `sessions_select_own` e `sessions_insert_own` mas SEM policy para service_role. Backend usa `SUPABASE_SERVICE_ROLE_KEY` onde `auth.uid()=NULL`, bloqueando INSERT.
- **Impact**: Pós-launch, todos usuários falhavam ao salvar histórico; `/historico` página vazia.
- **Fix applied**:
  ```sql
  CREATE POLICY "Service role can manage search sessions" ON public.search_sessions
      FOR ALL USING (true);
  ```

### TD-DB-002 — Missing `user_id` Indexes on RLS-Heavy Tables (FIXED)

- **Severity**: CRITICAL (historical)
- **Status**: ✅ FIXED em `020260308100000_debt001_database_integrity_fixes.sql`
- **Tables**: `search_sessions`, `pipeline_items`, `search_results_store`, `classification_feedback`
- **Finding**: RLS policies usam `auth.uid() = user_id`; sem índice em `user_id`, Supabase docs cita "100x+ performance degradation". Migration `20260307100000` tentou criar mas usou nomes errados (searches, pipeline, feedback).
- **Impact**: User login escaneava full table; risco de connection pool exhaustion em alta concorrência.
- **Fix applied**:
  ```sql
  CREATE INDEX IF NOT EXISTS idx_search_sessions_user_id ON public.search_sessions(user_id);
  CREATE INDEX IF NOT EXISTS idx_pipeline_items_user_id ON public.pipeline_items(user_id);
  CREATE INDEX IF NOT EXISTS idx_search_results_store_user_id ON public.search_results_store(user_id);
  CREATE INDEX IF NOT EXISTS idx_classification_feedback_user_id ON public.classification_feedback(user_id);
  ```

### TD-DB-003 — FK Constraint Conflict: partner_referrals ON DELETE SET NULL + NOT NULL (FIXED)

- **Severity**: CRITICAL (historical)
- **Status**: ✅ FIXED em `020260308100000_debt001_database_integrity_fixes.sql`
- **Finding**: `referred_user_id` era NOT NULL + FK ON DELETE SET NULL — contradição impedia deleção de profile (GDPR right-to-be-forgotten).
- **Fix applied**:
  ```sql
  ALTER TABLE public.partner_referrals ALTER COLUMN referred_user_id DROP NOT NULL;
  ```

### TD-DB-004 — `purge_old_bids()` cron NOT SCHEDULED in Production (PENDING)

- **Severity**: CRITICAL
- **Status**: 🔴 OPEN — @architect precisa confirmar
- **Finding**: Migration `020260326000000_pncp_raw_bids.sql` define função `purge_old_bids(12)` mas NÃO cria pg_cron schedule.
- **Impact**: Se cron não configurado manualmente → table cresce ilimitadamente → 500MB FREE tier exceeded em 3-4 semanas → table locks → downtime.
- **Fix SQL**:
  ```sql
  SELECT cron.schedule(
      'purge-old-bids',
      '0 3 * * *',  -- Daily at 3 AM UTC
      'SELECT public.purge_old_bids(12)'
  );
  ```
- **Effort**: 0.5h (verify + schedule)

---

## High Severity ⚠️

### TD-DB-010 — Improper RLS on `stripe_webhook_events`

- **Table**: `stripe_webhook_events`
- **Finding**: SELECT policy usa subquery checking `plan_type='master'` — admins (is_admin=true) sem plan_type='master' NÃO podem ver webhooks.
- **Impact**: Admins não conseguem debug de falhas Stripe; suporte a payment issues bloqueado.
- **Fix**:
  ```sql
  DROP POLICY IF EXISTS "webhook_events_select_admin" ON public.stripe_webhook_events;
  CREATE POLICY "webhook_events_select_admin" ON public.stripe_webhook_events
    FOR SELECT USING (
      EXISTS (SELECT 1 FROM public.profiles WHERE profiles.id = auth.uid() AND profiles.is_admin = true)
    );
  ```
- **Effort**: 1h

### TD-DB-011 — No UNIQUE Constraint on `profiles.email`

- **Finding**: `email` column sem UNIQUE constraint. `auth.users.email` tem UNIQUE via Supabase Auth, mas `profiles` é decoupled. Race condition: 2 signups simultâneos → 2 profiles com mesmo email.
- **Impact**: Account confusion; billing chaos (2 Stripe customers, mesmo email); search history orphan.
- **Fix**:
  ```sql
  -- Primeiro: identify and merge duplicates
  -- Depois:
  ALTER TABLE public.profiles ADD CONSTRAINT unique_profiles_email UNIQUE (email);
  ```
- **Effort**: 2-4h (data cleanup first)

### TD-DB-012 — RLS Policy Complex Subquery on `messages.INSERT`

- **Finding**: Policy usa triple-nested EXISTS (messages.conversation_id → conversations.id → profiles.is_admin). Query planner pode não otimizar; N+1 risk.
- **Impact**: INSERT slow para users com muitas conversations; potential deadlock durante ownership transfer.
- **Fix**: Materialize via CTE, denormalized column, ou simplify policy.
- **Effort**: 4-6h (redesign + testing)

### TD-DB-013 — `search_results_cache` Sem pg_cron Cleanup (TD-SYS-016 DB side)

- **Finding**: Cleanup trigger mantém max 5 por user, mas sem cron global delete de entries >24h. Trigger só dispara em INSERT novo.
- **Impact**: Se user não volta, entries antigas ficam; table bloat cumulativo.
- **Fix**:
  ```sql
  SELECT cron.schedule(
      'cleanup-search-cache',
      '0 4 * * *',
      $$DELETE FROM public.search_results_cache WHERE created_at < now() - interval '24 hours'$$
  );
  ```
- **Effort**: 0.5h

### TD-DB-014 — `search_results_store.expires_at` Sem Cron Cleanup

- **Finding**: `expires_at` column existe mas nenhum cron deleta expired rows.
- **Impact**: Table cresce indefinidamente.
- **Fix**:
  ```sql
  SELECT cron.schedule(
      'cleanup-search-store',
      '0 4 * * *',
      $$DELETE FROM public.search_results_store WHERE expires_at < now()$$
  );
  ```
- **Effort**: 0.5h

### TD-DB-015 — Alert Digest Scan Index Missing

- **Finding**: `idx_alert_preferences_digest_due` é partial (enabled, frequency, last_digest_sent_at) WHERE enabled AND frequency!='off'. Cron job de digest pode fazer multi-step scan se planner escolher errado.
- **Fix**:
  ```sql
  CREATE INDEX IF NOT EXISTS idx_alert_preferences_digest_scan
    ON alert_preferences(frequency, last_digest_sent_at DESC)
    WHERE enabled = true;
  ```
- **Effort**: 1h

---

## Medium Severity 💡

### TD-DB-020 — `audit_events` Sem `is_active` Flag

- **Finding**: Sem soft-delete; entries permanentes mesmo se erroneamente criadas.
- **Impact**: Compliance auditor vê orphaned entries; retention cleanup só hard-delete.
- **Fix**: `ALTER TABLE audit_events ADD COLUMN is_active BOOLEAN DEFAULT true;`
- **Effort**: 1h

### TD-DB-021 — `classification_feedback` Table Status Unclear

- **Finding**: Referenced em migrations + backend/migrations, mas conditional IF EXISTS checks suggestem feature optional.
- **Impact**: Future devs confusos; queries podem falhar silenciosamente.
- **Fix**: @architect deve confirmar status; commit ou remove.
- **Effort**: 2-4h

### TD-DB-022 — `pncp_raw_bids` Date Columns Nullable

- **Finding**: `data_publicacao`, `data_abertura`, `data_encerramento` todos nullable. 5-10% dos bids podem ter datas missing. Filtros por data silenciosamente excluem NULL.
- **Impact**: Users recebem menos resultados que deveriam.
- **Fix**: Audit ingestion data; default para CURRENT_DATE ou NOT NULL constraint.
- **Effort**: 2-3h

### TD-DB-023 — `health_checks` Manual Cleanup (30-day)

- **Finding**: Sem pg_cron delete. Aceitável (~5K rows em 30d) mas easily forgotten.
- **Fix**: Schedule cron job.
- **Effort**: 0.5h

### TD-DB-024 — `stripe_webhook_events` PII in payload JSONB

- **Finding**: `payload` stores full Stripe webhook (customer IDs, amounts). 90-day retention manual.
- **Impact**: LGPD/GDPR compliance risk se retention falha.
- **Fix**: SELECT masking ou archive to S3 after 7 days.
- **Effort**: 4-8h

---

## Low / Style

### TD-DB-030 — No `down.sql` Rollback Templates

- **Finding**: Sem rollback-safe migrations; cleanup manual se migration falha.
- **Fix**: Criar template + enforcement em `@devops` task.
- **Effort**: 4-8h

### TD-DB-031 — Duplicate Trigger Functions (FIXED)

- **Status**: ✅ FIXED em DEBT-001 (consolidado para `set_updated_at`)

### TD-DB-032 — Soft FK on `pncp_raw_bids.crawl_batch_id`

- **Finding**: Sem FK constraint real para `ingestion_runs.crawl_batch_id` — trade-off de performance documentado.
- **Fix**: Adicionar comment em schema.
- **Effort**: 0.5h

### TD-DB-033 — `search_results_store.user_id` NO ACTION vs sister CASCADE

- **Finding**: Inconsistência com `search_results_cache` (CASCADE).
- **Fix**: ALTER TO CASCADE.
- **Effort**: 1h

---

## Specific Audits

### 1. Primary Keys

- ✅ Todas 23 tabelas têm PKs explícitas (uuid ou bigint GENERATED AS IDENTITY)
- ✅ Sem composite PKs
- ✅ Defaults: `gen_random_uuid()` ou `GENERATED AS IDENTITY`

### 2. Foreign Keys

- ✅ 14 FK constraints explícitas
- ⚠️ `pncp_raw_bids.crawl_batch_id` → `ingestion_runs.crawl_batch_id` = **soft FK** (sem constraint). Trade-off documented — FKs add overhead durante ingestion.
- ⚠️ `search_results_store.user_id` ON NO ACTION vs `search_results_cache` CASCADE — inconsistente.
- ✅ FK indexes: todos FKs têm índices no referring column (após CRIT-002 fix).

### 3. Nullability

- ⚠️ `pncp_raw_bids.data_*` nullable — 5-10% de bids possivelmente excluídos.
- ⚠️ `conversations.last_message_at` NOT NULL default now() — levemente misleading (mostra creation time se sem messages).
- ✅ `profiles.company, full_name, avatar_url` nullable (OK para dados opcionais).

### 4. Timestamps

- ✅ Todas 23 tabelas têm `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`
- ✅ Todas user-data têm `updated_at` via triggers `set_updated_at()`
- ⚠️ `stripe_webhook_events` sem `updated_at` (acceptable — imutável)
- ⚠️ `ingestion_checkpoints` sem `updated_at` (tem started_at/completed_at — OK)

### 5. Row-Level Security (RLS)

**Coverage Matrix:**

| Table                    | SELECT   | INSERT    | UPDATE    | DELETE    | Service Role | Status     |
|--------------------------|----------|-----------|-----------|-----------|--------------|------------|
| profiles                 | own      | own       | own       | NO        | ALL          | ✅ GOOD    |
| plans                    | ALL      | NO        | NO        | NO        | -            | ✅ PUBLIC  |
| user_subscriptions       | own      | NO        | NO        | NO        | ?            | ⚠️ NO INSERT |
| search_sessions          | own      | own       | NO        | NO        | ALL          | ✅ FIXED   |
| monthly_quota            | own      | NO        | NO        | NO        | ALL          | ✅ GOOD    |
| stripe_webhook_events    | master   | service   | NO        | NO        | -            | ⚠️ HIGH-001 |
| conversations            | own/admin| own       | admin     | admin     | ALL          | ✅ GOOD    |
| messages                 | conv     | conv      | conv      | -         | ALL          | ⚠️ HIGH-003 complex |
| alert_preferences        | own      | own       | own       | own       | ALL          | ✅ GOOD    |
| alerts                   | own      | own       | own       | own       | ALL          | ✅ GOOD    |
| alert_sent_items         | own/join | NO        | NO        | NO        | ALL          | ✅ GOOD    |
| health_checks            | ALL      | NO        | NO        | NO        | -            | ✅ PUBLIC  |
| incidents                | ALL      | NO        | NO        | NO        | -            | ✅ PUBLIC  |
| organizations            | own/admin| own       | own       | NO        | ALL          | ✅ GOOD    |
| org_members              | own/adm  | own/admin | -         | own/admin | ALL          | ✅ GOOD    |
| pipeline_items           | own      | own       | own       | own       | ALL          | ✅ GOOD    |
| search_results_cache     | own      | NO        | NO        | NO        | ALL          | ✅ GOOD    |
| search_results_store     | own      | NO        | NO        | NO        | ALL          | ✅ GOOD    |
| pncp_raw_bids            | auth     | service   | service   | service   | -            | ✅ PUBLIC DATA |
| ingestion_checkpoints    | auth     | service   | service   | service   | -            | ✅ GOOD    |
| ingestion_runs           | auth     | service   | service   | service   | -            | ✅ GOOD    |
| audit_events             | admin    | service   | NO        | NO        | ALL          | ⚠️ NO DELETE |
| classification_feedback  | own/adm  | own       | own       | NO        | ALL          | ✅ (if exists) |

**Critical Findings:**
1. ⚠️ `user_subscriptions` sem INSERT policy user-level (admin/service only) — frontend signup não pode escrever?
2. ⚠️ `stripe_webhook_events` SELECT restrito a master plan (HIGH-001)
3. ⚠️ `audit_events` sem DELETE policy — LGPD right-to-erasure bloqueado
4. ⚠️ Service role `FOR ALL USING (true)` em quase todas tabelas — wide bypass necessário mas deve ser auditado

### 6. Indexes

**Coverage Analysis:**

| Category | Status |
|----------|--------|
| `pncp_raw_bids` | ✅ EXCELLENT (8 purpose-built + GIN FTS) |
| `profiles.email` | ⚠️ HIGH-002 (sem UNIQUE, sem index) |
| user_id em RLS tables | ✅ FIXED (post CRIT-002) |
| Partial indexes | ✅ Excelente (alert_preferences, messages, pipeline, alerts) |
| Duplicate indexes | ✅ Não detectados |
| Unused indexes | ⚠️ Verificação via `pg_stat_user_indexes` pendente |

### 7. Data Integrity

| Table | PK | FK | UNIQUE | CHECK | NOT NULL | Status |
|-------|----|----|--------|-------|----------|--------|
| profiles | ✓ | ✓ | - | plan_type enum | ✓ | ⚠️ NO UNIQUE email |
| pncp_raw_bids | ✓ | - | - | content_hash NOT NULL | ✓ strict | ✅ GOOD |
| user_subscriptions | ✓ | ✓✓ | - | - | ✓ | ✅ GOOD |
| conversations | ✓ | ✓ | - | category/status/subject enums | ✓ strict | ✅ GOOD |
| messages | ✓ | ✓✓ | - | body 1-5000, is_admin_reply bool | ✓ strict | ✅ GOOD |
| alerts | ✓ | ✓ | - | active bool | ✓ strict | ✅ GOOD |
| organizations | ✓ | ✓ (RESTRICT!) | - | - | ✓ strict | ✅ GOOD |
| org_members | ✓ | ✓✓ | org_id+user_id | role enum | ✓ strict | ✅ GOOD |
| pipeline_items | ✓ | ✓ | user_id+pncp_id | stage enum | ✓ strict | ✅ GOOD |

**Findings:**
- ✅ Strong enum CHECK constraints (category, status, stage, frequency, role, run_type)
- ✅ ON DELETE RESTRICT em `organizations.owner_id` previne orphan org
- ⚠️ HIGH-002: profiles.email sem UNIQUE

### 8. PII & Security

| Table | PII | Stored As | Protection | Notes |
|-------|-----|-----------|------------|-------|
| profiles | email, full_name | PLAINTEXT | Auth.users encrypted | ⚠️ Duplicate possible |
| auth.users | email, password | Supabase-managed | ✅ Encrypted | ✅ |
| stripe_webhook_events | payload | JSONB plaintext | ⚠️ Customer IDs | ⚠️ TD-DB-024 |
| audit_events | hashes SHA-256 (16 chars) | Hashed | ✅ LGPD/GDPR | ✅ EXCELLENT |
| pncp_raw_bids | orgao_cnpj | PLAINTEXT | Public data (Lei 14.133) | ✅ LEGAL |
| conversations/messages | body | PLAINTEXT | RLS-protected | ✅ ACCEPTABLE |

### 9. Performance

**Problematic Patterns:**

| Issue | Tables | Risk | Status |
|-------|--------|------|--------|
| Full table scans on RLS | search_sessions, pipeline_items | HIGH | ✅ FIXED (CRIT-002) |
| Double tsvector computation | pncp_raw_bids | MEDIUM (2x CPU) | ✅ FIXED (DEBT-210) |
| Row-by-row upsert | pncp_raw_bids | HIGH (N round-trips) | ✅ FIXED (DEBT-210) |
| Triple nested EXISTS RLS | messages | MEDIUM | 🟡 HIGH-003 |
| Unindexed digest scan | alert_preferences | LOW-MEDIUM | 🟡 HIGH-004 |

**Scaling Estimates:**
- `pncp_raw_bids`: 40K-100K rows, 8 indexes, GIN FTS → scales to 1M easily dentro do 500MB (sem raw_json)
- `search_sessions`: 10K-50K → scales to 1M (pós CRIT-002 fix)

### 10. Data Retention

| Table | Retention | Enforcement | Status |
|-------|-----------|-------------|--------|
| audit_events | 12 months | pg_cron `0 4 1 * *` | ✅ DOCUMENTED, ⚠️ verify ativo |
| pncp_raw_bids | 12 days | Manual `purge_old_bids(12)` | 🔴 TD-DB-004 (cron não confirmed) |
| search_results_cache | 24h | Trigger cleanup max 5/user + app-level TTL | ⚠️ TD-DB-013 (sem cron global) |
| search_results_store | 24h | `expires_at` soft TTL | 🟡 TD-DB-014 (sem cleanup cron) |
| health_checks | 30 days | Manual cleanup | ⚠️ TD-DB-023 |
| stripe_webhook_events | 90 days | Manual | ⚠️ TD-DB-024 |

---

## Migration Hygiene Audit

### Rollback Coverage

- 🔴 **Sem `down.sql` files**: Migrations NÃO rollback-safe; cleanup manual se falha.
- **Fix**: Criar template + @devops enforcement.

### Unsafe Operations

- ✅ Migrations usam pattern com backfill + concurrent-safe (DEBT-210 adiciona tsv com cuidado)
- ⚠️ Alguns ALTER TABLE sem CONCURRENTLY — aceitável para 40K-100K rows, risky em 1M+

### Migration Sequence Issues

- ⚠️ Migration `020260301100000` chama `update_updated_at()` definida em `001_*`. Risk se migrations replayed out-of-order (defensive coding em newer migrations).

### Post-Launch Hotfixes

- `006b_search_sessions_service_role_policy.sql` (2026-02-10) — CRIT-001 hotfix 1 day após launch
- `020260308100000_debt001_database_integrity_fixes.sql` — large DEBT phase (CRIT-002, CRIT-003, CRIT-004)
- `20260410150000_fix_is_master_trigger_story415.sql` (2026-04-10) — trigger fix

---

## Questions for @architect (Phase 4 Handoff)

1. **`purge_old_bids()` cron job** está configurado em prod? Sem isso, table exceeds 500MB em 3-4 semanas (TD-DB-004).
2. **Soft vs hard delete** em `pncp_raw_bids`: por que `is_active=false`? Audit trail requirement?
3. **`partner_referrals` table**: feature shipped ou WIP? Migration 202603012 cria tabela mas pouco referenciada.
4. **`classification_feedback` table**: status (shipped/WIP)? Conditional IF EXISTS checks suggest optional.
5. **Service role bypass**: intencional wide-open admin? Considerar narrow para functions específicas.
6. **`messages.INSERT` RLS complexity**: refactor ou accept?
7. **`profiles.email` UNIQUE**: adicionar? Duplicate account risk real.
8. **`stripe_webhook_events` PII**: mask ou archive após 7 days?
9. **`organizations.owner_id` RESTRICT**: se owner morre, org orfã. Soft-delete?
10. **Constraint audit**: após DEBT-001, correr check_constraints.sql completo.

---

## Recommendations for Phase 7 QA & Phase 8 Final Assessment

### Quick Wins (P0, <4h total)

1. ✅ Schedule `purge_old_bids` cron (0.5h) — **blocking storage quota**
2. ✅ Schedule `search_results_cache` cleanup cron (0.5h)
3. ✅ Schedule `search_results_store` expired cleanup cron (0.5h)
4. ✅ Fix `stripe_webhook_events` RLS para admins (1h) — HIGH-001
5. ✅ Add `alert_preferences` digest scan index (1h) — HIGH-004

### High Impact (P1, 4-12h)

6. Add UNIQUE(email) to profiles + dedup (2-4h) — HIGH-002
7. `messages.INSERT` RLS optimization (4-6h) — HIGH-003
8. `audit_events` DELETE policy for GDPR (1h) — TD-DB-020
9. Investigate `classification_feedback` status (2-4h) — TD-DB-021

### Strategic (P2, ongoing)

10. `down.sql` templates + enforcement (4-8h)
11. PII archive strategy for `stripe_webhook_events` (4-8h)
12. Portuguese FTS dictionary tuning (8-16h)

---

## Action Plan

| Priority | Action | Effort | Risk | Blocking |
|----------|--------|--------|------|----------|
| P0 | Verify/schedule purge_old_bids cron | 0.5h | CRITICAL storage | YES |
| P0 | Schedule search_results_cache cleanup | 0.5h | MEDIUM storage | YES |
| P0 | Schedule search_results_store cleanup | 0.5h | MEDIUM storage | YES |
| P0 | Fix stripe_webhook_events admin RLS | 1h | MEDIUM debug | NO |
| P1 | UNIQUE(email) on profiles | 2-4h | MEDIUM data quality | data cleanup |
| P1 | Optimize messages INSERT RLS | 4-6h | LOW perf | NO |
| P1 | audit_events DELETE policy | 1h | LOW compliance | NO |
| P2 | alert_preferences digest scan idx | 1h | LOW cron perf | NO |
| P2 | Investigate classification_feedback | 2-4h | LOW schema clarity | NO |
| P3 | down.sql migration templates | 4-8h | MAINT | NO |
| P3 | PII archive webhook payload | 4-8h | LGPD | NO |

---

## Summary

**SmartLic database is FUNCTIONAL but DEBT-HEAVY:**

**Positive:**
- ✅ Comprehensive RLS em user-data tables
- ✅ Strong timestamp discipline
- ✅ Excellent index design em `pncp_raw_bids` (8 purpose-built)
- ✅ Great use of partial indexes
- ✅ DEBT-210 optimization (tsvector pre-compute, batch upsert)

**Negative:**
- ⚠️ Missing `user_id` indexes descobertos post-launch (fixed)
- ⚠️ `search_sessions` precisou hotfix (CRIT-001)
- ⚠️ `profiles.email` sem UNIQUE (duplicate account risk)
- ⚠️ RLS `messages` policy complexity
- ⚠️ Data retention (pncp_raw_bids, search_results_*) não completamente automatizada
- ⚠️ Sem `down.sql` rollback templates

**Score: 62/100**
- 85/100 schema design
- 65/100 RLS/security
- 55/100 performance (foundations boas, gaps pós-launch)
- 45/100 data retention (automação incompleta)

**Recomendação**: Endereçar P0 items antes de scaling para 1M+ `pncp_raw_bids` rows. Todos fixes são 1-4h e low-risk.

---

**Document Status**: 2.0 (2026-04-14) — Phase 2 of brownfield-discovery complete. Handoff ao @architect para Phase 4 (consolidação inicial).

---

## 10. Accepted Risks & Design Decisions (DEBT-017)

**Added:** 2026-03-09 — DEBT-017 Database Long-Term Optimization

### DB-004 — `mfa_recovery_codes` no rate limiting in DB

**Status:** ACCEPTED — App-layer rate limiting is the correct pattern.
**Rationale:** Database-level rate limiting via triggers would add complexity and coupling. The `mfa_recovery_attempts` table + application code in `auth.py` provides rate limiting with proper backoff and lockout. DB-level triggers cannot implement exponential backoff or account-level lockout policies.
**Owner:** Backend auth module (`auth.py`)

### DB-005 — `mfa_recovery_attempts` no SELECT policy for users

**Status:** ACCEPTED — Intentional information leakage prevention.
**Rationale:** Exposing recovery attempt history to users would reveal timing information about brute-force attempts against their account. Only `service_role` can read this table. Users see "too many attempts" errors via the API without knowing attempt counts.

### DB-006 — `trial_email_log` no user-facing policies

**Status:** ACCEPTED — Backend-only table.
**Rationale:** This table tracks automated trial drip emails sent by the worker process. Users have no legitimate need to query their email send history. If a user settings page needs this data in the future, add a SELECT policy scoped to `user_id = auth.uid()`.

### DB-008 — Stripe Price IDs visible in `plans` table

**Status:** ACCEPTED — Used client-side by design (Stripe Checkout).
**Rationale:** Stripe Price IDs are not secret — they are used in the Stripe Checkout flow. The `plans` table has `FOR SELECT USING (true)` because the pricing page needs to display plan information. The actual checkout session creation happens server-side with additional validation. Note: STORY-210 AC11 strips `stripe_price_id_*` from the API response, so frontend never receives them directly.

### DB-009 — Partner RLS uses `auth.users.email` (cross-schema query)

**Status:** OPTIMIZED — Already uses `partners.contact_email` pattern.
**Rationale:** The `partners_self_read` policy compares `contact_email = (SELECT email FROM auth.users WHERE id = auth.uid())`. This is the standard Supabase pattern for email-based RLS. The query is to `auth.users` (not `profiles`), which is the canonical source of email. No further optimization needed — the `auth.uid()` call is already indexed.

### DB-016 — `search_sessions.status` no DB-level transition enforcement

**Status:** ACCEPTED — App-layer state machine is the correct pattern.
**Rationale:** Complex FSM transition logic (with stages, error recovery, retries, cancellation) is better expressed in application code (`search_state_manager.py`) than in SQL triggers. DB-level enforcement would require duplicating the state machine logic, creating a maintenance burden. The `search_state_transitions` audit table provides full traceability. Valid transitions documented via SQL COMMENT on the column (DEBT-017 migration).

### DB-020 — Naming inconsistency in constraints

**Status:** DOCUMENTED — Convention adopted for future constraints.
**Rationale:** Retroactively renaming all existing constraints would require DROP + ADD for each, risking downtime and FK dependency issues. Convention documented in schema COMMENT: `chk_{table}_{column}` for CHECK, `fk_{table}_{column}` for FK, `uq_{table}_{column}` for UNIQUE, `idx_{table}_{column}` for indexes. Legacy constraints retain original names.

### DB-022 — `profiles.phone_whatsapp` CHECK only validates digits/length

**Status:** ACCEPTED — App-layer validation is the correct pattern.
**Rationale:** Brazilian phone number validation rules (area codes, mobile prefixes, landline vs mobile) change over time. Encoding these rules in a CHECK constraint would require migrations for each regulatory change. The DB CHECK `'^[0-9]{10,11}$'` catches obvious errors; full validation happens in the frontend form and backend Pydantic schema.

### DB-023 — `search_results_cache` cross-user sharing with date range

**Status:** MONITORED — Low risk at current scale.
**Rationale:** The `params_hash_global` column enables SWR-style cross-user cache sharing. Date ranges ARE included in the hash (STORY-306), so different date ranges produce different hashes. The risk is that a cached result from user A could be served to user B for identical params — this is intentional for performance. Stale data risk is mitigated by the 24h TTL and background revalidation.

### DB-024 — `plan_billing_periods` no `updated_at` column

**Status:** RESOLVED — Column added in DEBT-017 migration.
**Rationale:** Pricing changes are infrequent but should be trackable. Added `updated_at TIMESTAMPTZ DEFAULT now()` with auto-update trigger.

### DB-027 — No down-migrations

**Status:** ACCEPTED — PITR is the rollback mechanism.
**Rationale:** Supabase provides Point-in-Time Recovery (PITR) as the primary rollback mechanism. Down-migrations for 76+ files would be expensive to write and maintain. For critical schema changes, the rollback procedure is: (1) Identify the timestamp before the migration, (2) Use Supabase PITR to restore, (3) Re-apply any migrations after the restore point that should be kept. Manual rollback scripts can be added as comments in individual migrations for high-risk changes.

### DB-036 — No table partitioning

**Status:** DEFERRED — Plan when row count > 1M/month.
**Rationale:** Tables `audit_events`, `search_state_transitions`, and `search_sessions` are append-heavy and time-series. At current beta scale (~10K rows/month), partitioning overhead exceeds benefit. Monitor via: `SELECT relname, n_live_tup FROM pg_stat_user_tables WHERE relname IN ('audit_events', 'search_state_transitions', 'search_sessions') ORDER BY n_live_tup DESC;`. Partition by month when any table exceeds 1M rows/month.

### DB-044 — pg_cron jobs not in migrations (require superuser)

**Status:** ACCEPTED — Manual setup required.
**Rationale:** pg_cron requires the `cron` extension which needs superuser. On Supabase, this is enabled via the Dashboard (Database > Extensions > pg_cron). Migrations use `CREATE EXTENSION IF NOT EXISTS pg_cron` but this only works if the extension is already enabled. Manual setup steps:
1. Enable pg_cron in Supabase Dashboard > Database > Extensions
2. Run migrations normally — pg_cron jobs will be created
3. Verify with: `SELECT * FROM cron.job;`

### DB-046 — No audit trail for DB-level schema changes

**Status:** ACCEPTED — Policy: "never modify schema via dashboard".
**Rationale:** All schema changes MUST go through migration files in `supabase/migrations/`. Direct Dashboard modifications are prohibited. If a Dashboard change is unavoidable (e.g., enabling extensions), create a corresponding migration file documenting the change. This policy is documented in the schema COMMENT and enforced by code review.

### DB-050 — No FK from `search_state_transitions.search_id` to `search_sessions`

**Status:** ACCEPTED — Cannot add FK due to schema constraints.
**Rationale:** `search_sessions.search_id` is nullable and not unique (retries can share search IDs). Adding a FK would require: (1) making search_id NOT NULL on search_sessions (breaks existing rows), (2) adding UNIQUE constraint (breaks retry semantics). Orphan transitions are cleaned up by the pg_cron retention job (30-day retention). Documented via SQL COMMENT on the column.
