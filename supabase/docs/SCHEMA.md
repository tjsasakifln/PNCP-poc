# SmartLic Database Schema Reference

> **Generated:** 2026-03-31 | **Auditor:** @data-engineer (Dara) -- Brownfield Discovery Phase 2
> **Source:** 106 migration files in `supabase/migrations/`
> **Database:** PostgreSQL 17 (Supabase Cloud) | **Schema:** `public`
> **Extensions:** pg_trgm, pg_cron

---

## Overview

| Metric | Value |
|--------|-------|
| Total tables | 35 |
| Tables with RLS | 35 (100%) |
| RPC Functions | 15 |
| Triggers | 14 |
| pg_cron Jobs | 5 |
| CHECK Constraints | 30+ |
| Indexes | 80+ |
| Custom Types | 1 (alert_frequency ENUM) |
| Views | 2 (diagnostic) |

---

## Tables

### profiles

Extends `auth.users` with application-specific fields. Auto-created by `handle_new_user()` trigger.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | uuid PK | No | — | FK to auth.users(id) ON DELETE CASCADE |
| email | text | No | — | Unique partial index |
| full_name | text | Yes | — | |
| company | text | Yes | — | |
| sector | text | Yes | — | Business sector |
| phone_whatsapp | text | Yes | — | 10-11 digits, unique partial index |
| whatsapp_consent | boolean | Yes | false | LGPD marketing consent |
| whatsapp_consent_at | timestamptz | Yes | — | LGPD audit trail |
| plan_type | text | No | 'free_trial' | CHECK: free_trial, consultor_agil, maquina, sala_guerra, master, smartlic_pro, consultoria |
| is_admin | boolean | No | false | System administrator flag |
| avatar_url | text | Yes | — | |
| context_data | jsonb | Yes | '{}' | Onboarding wizard data (< 512KB) |
| subscription_status | text | Yes | 'trial' | CHECK: trial, active, canceling, past_due, expired |
| trial_expires_at | timestamptz | Yes | — | 14-day trial expiration |
| subscription_end_date | timestamptz | Yes | — | When canceled sub ends |
| email_unsubscribed | boolean | Yes | false | Email opt-out (LGPD) |
| email_unsubscribed_at | timestamptz | Yes | — | |
| marketing_emails_enabled | boolean | No | true | Marketing email opt-in |
| referred_by_partner_id | uuid | Yes | — | FK to partners(id) |
| created_at | timestamptz | No | now() | |
| updated_at | timestamptz | No | now() | Auto-updated by trigger |

**Indexes:** idx_profiles_is_admin (partial), idx_profiles_email_trgm (GIN trigram), idx_profiles_email_unique (unique partial), idx_profiles_phone_whatsapp_unique (unique partial), idx_profiles_context_porte, idx_profiles_subscription_status (partial), idx_profiles_referred_by_partner (partial).

---

### plans

Static plan catalog. Seeded by migrations.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | text PK | No | — | e.g., 'smartlic_pro', 'consultoria' |
| name | text | No | — | |
| description | text | Yes | — | |
| max_searches | int | Yes | — | NULL = unlimited |
| price_brl | numeric(10,2) | No | 0 | Base monthly price |
| duration_days | int | Yes | — | NULL = perpetual |
| stripe_price_id | text | Yes | — | Legacy default |
| stripe_price_id_monthly | text | Yes | — | |
| stripe_price_id_semiannual | text | Yes | — | |
| stripe_price_id_annual | text | Yes | — | |
| is_active | boolean | No | true | |
| created_at | timestamptz | No | now() | |
| updated_at | timestamptz | No | now() | |

**Active plans:** smartlic_pro (R$397/mo), consultoria (R$997/mo), master, free_trial.
**Deactivated legacy:** consultor_agil, maquina, sala_guerra, pack_5, pack_10, pack_20, monthly, annual.

---

### plan_billing_periods

Multi-period pricing. Source of truth for Stripe price IDs.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | uuid PK | No | gen_random_uuid() | |
| plan_id | text | No | — | FK plans(id) CASCADE |
| billing_period | text | No | — | CHECK: monthly, semiannual, annual |
| price_cents | integer | No | — | BRL centavos |
| discount_percent | integer | Yes | 0 | |
| stripe_price_id | text | Yes | — | |
| created_at | timestamptz | Yes | now() | |

**Unique:** (plan_id, billing_period)

---

### plan_features

Feature flags per plan + billing period.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | serial PK | No | — | |
| plan_id | text | No | — | FK plans(id) CASCADE |
| billing_period | varchar(10) | No | — | CHECK: monthly, semiannual, annual |
| feature_key | varchar(100) | No | — | e.g., full_access, multi_user |
| enabled | boolean | No | true | |
| metadata | jsonb | Yes | '{}' | < 512KB |
| created_at | timestamptz | No | now() | |
| updated_at | timestamptz | No | now() | |

**Unique:** (plan_id, billing_period, feature_key)

---

### user_subscriptions

Active subscriptions per user.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | uuid PK | No | gen_random_uuid() | |
| user_id | uuid | No | — | FK profiles(id) CASCADE |
| plan_id | text | No | — | FK plans(id) RESTRICT |
| credits_remaining | int | Yes | — | NULL = unlimited |
| starts_at | timestamptz | No | now() | |
| expires_at | timestamptz | Yes | — | |
| stripe_subscription_id | text | Yes | — | Unique partial |
| stripe_customer_id | text | Yes | — | |
| is_active | boolean | No | true | |
| billing_period | varchar(10) | No | 'monthly' | CHECK: monthly, semiannual, annual |
| annual_benefits | jsonb | No | '{}' | < 512KB |
| subscription_status | text | Yes | 'active' | CHECK: active, trialing, past_due, canceled, expired |
| first_failed_at | timestamptz | Yes | — | Dunning tracking |
| version | integer | No | 1 | Optimistic locking |
| created_at | timestamptz | No | now() | |
| updated_at | timestamptz | No | now() | |

---

### monthly_quota

Monthly search usage tracking. Retention: 24 months.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | uuid PK | No | gen_random_uuid() | |
| user_id | uuid | No | — | FK profiles(id) CASCADE |
| month_year | varchar(7) | No | — | Format: "2026-02" |
| searches_count | int | No | 0 | |
| created_at | timestamptz | No | now() | |
| updated_at | timestamptz | No | now() | |

**Unique:** (user_id, month_year)

---

### search_sessions

Search history per user with full lifecycle tracking.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | uuid PK | No | gen_random_uuid() | |
| user_id | uuid | No | — | FK profiles(id) CASCADE |
| search_id | uuid | Yes | — | Correlation ID for SSE/ARQ/cache |
| sectors | text[] | No | — | |
| ufs | text[] | No | — | |
| data_inicial | date | No | — | |
| data_final | date | No | — | |
| custom_keywords | text[] | Yes | — | |
| total_raw | int | No | 0 | |
| total_filtered | int | No | 0 | |
| valor_total | numeric(14,2) | Yes | 0 | |
| resumo_executivo | text | Yes | — | LLM-generated summary |
| destaques | text[] | Yes | — | |
| excel_storage_path | text | Yes | — | |
| status | text | No | 'created' | CHECK: created, processing, completed, failed, timed_out, cancelled |
| error_message | text | Yes | — | |
| error_code | text | Yes | — | |
| started_at | timestamptz | No | now() | |
| completed_at | timestamptz | Yes | — | |
| duration_ms | integer | Yes | — | |
| pipeline_stage | text | Yes | — | Last stage reached |
| raw_count | integer | Yes | 0 | |
| response_state | text | Yes | — | live, cached, degraded, empty_failure |
| failed_ufs | text[] | Yes | — | |
| created_at | timestamptz | No | now() | |

**Key indexes:** idx_search_sessions_user_status_created (composite), idx_search_sessions_search_id (partial), idx_search_sessions_inflight (partial for SIGTERM cleanup).

---

### search_results_cache

L2 persistent cache (SWR pattern). Max 10 entries per user with priority-based eviction.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | uuid PK | No | gen_random_uuid() | |
| user_id | uuid | No | — | FK profiles(id) CASCADE |
| params_hash | text | No | — | Per-user cache key |
| params_hash_global | text | Yes | — | Cross-user cache key |
| search_params | jsonb | No | — | |
| results | jsonb | No | — | CHECK: <= 2MB |
| total_results | integer | No | 0 | |
| sources_json | jsonb | No | '["pncp"]' | |
| fetched_at | timestamptz | No | now() | |
| priority | text | No | 'cold' | hot, warm, cold |
| access_count | integer | No | 0 | |
| last_accessed_at | timestamptz | Yes | — | |
| last_success_at | timestamptz | Yes | — | |
| last_attempt_at | timestamptz | Yes | — | |
| fail_streak | integer | No | 0 | |
| degraded_until | timestamptz | Yes | — | |
| coverage | jsonb | Yes | — | |
| fetch_duration_ms | integer | Yes | — | |
| created_at | timestamptz | No | now() | |

**Unique:** (user_id, params_hash). **Cleanup trigger:** priority-based eviction (cold first). **pg_cron:** cold entries > 7 days deleted daily.

---

### search_results_store

L3 persistent storage. 24h default TTL. Prevents "Busca nao encontrada" after L1/L2 expiry.

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| search_id | uuid PK | No | — |
| user_id | uuid | No | — |
| results | jsonb | No | — |
| sector | text | Yes | — |
| ufs | text[] | Yes | — |
| total_filtered | int | Yes | 0 |
| created_at | timestamptz | Yes | now() |
| expires_at | timestamptz | Yes | now() + 24h |

**CHECK:** results < 2MB. **pg_cron:** expired > 7 days deleted daily.

---

### search_state_transitions

Audit trail for search state machine. Fire-and-forget inserts.

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid PK | No | gen_random_uuid() |
| search_id | uuid | No | — |
| from_state | text | Yes | — |
| to_state | text | No | — |
| stage | text | Yes | — |
| details | jsonb | Yes | '{}' |
| duration_since_previous_ms | integer | Yes | — |
| created_at | timestamptz | No | now() |

**JSONB constraint:** details < 512KB.

---

### pipeline_items

Opportunity pipeline (kanban). Optimistic locking via version column.

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid PK | No | gen_random_uuid() |
| user_id | uuid | No | — |
| pncp_id | text | No | — |
| objeto | text | No | — |
| orgao | text | Yes | — |
| uf | text | Yes | — |
| valor_estimado | numeric | Yes | — |
| data_encerramento | timestamptz | Yes | — |
| link_pncp | text | Yes | — |
| stage | text | No | 'descoberta' |
| notes | text | Yes | — |
| version | integer | No | 1 |
| created_at | timestamptz | No | now() |
| updated_at | timestamptz | No | now() |

**Unique:** (user_id, pncp_id). **Stage CHECK:** descoberta, analise, preparando, enviada, resultado.

---

### classification_feedback

User feedback on bid classification accuracy.

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid PK | No | gen_random_uuid() |
| user_id | uuid | No | — |
| search_id | uuid | No | — |
| bid_id | text | No | — |
| setor_id | text | No | — |
| user_verdict | text | No | — |
| reason | text | Yes | — |
| category | text | Yes | — |
| bid_objeto | text | Yes | — |
| bid_valor | decimal | Yes | — |
| bid_uf | text | Yes | — |
| confidence_score | integer | Yes | — |
| relevance_source | text | Yes | — |
| created_at | timestamptz | Yes | now() |

**Unique:** (user_id, search_id, bid_id). **user_verdict CHECK:** false_positive, false_negative, correct.

---

### pncp_raw_bids

Raw PNCP bid records (datalake layer). 40K+ rows. 12-day retention.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| pncp_id | text PK | No | — | Natural key |
| objeto_compra | text | No | — | |
| valor_total_estimado | numeric(18,2) | Yes | — | |
| modalidade_id | integer | No | — | 4=Concorrencia, 5=Pregao, etc. |
| modalidade_nome | text | Yes | — | |
| situacao_compra | text | Yes | — | |
| esfera_id | text | Yes | — | |
| uf | text | No | — | |
| municipio | text | Yes | — | |
| codigo_municipio_ibge | text | Yes | — | |
| orgao_razao_social | text | Yes | — | |
| orgao_cnpj | text | Yes | — | |
| unidade_nome | text | Yes | — | |
| data_publicacao | timestamptz | Yes | — | |
| data_abertura | timestamptz | Yes | — | |
| data_encerramento | timestamptz | Yes | — | |
| link_sistema_origem | text | Yes | — | |
| link_pncp | text | Yes | — | |
| content_hash | text | No | — | MD5 for change detection |
| tsv | tsvector | No | — | Pre-computed, maintained by trigger |
| ingested_at | timestamptz | No | now() | |
| updated_at | timestamptz | No | now() | |
| source | text | No | 'pncp' | |
| crawl_batch_id | text | Yes | — | Links to ingestion_runs |
| is_active | boolean | No | true | |

**Key indexes:** idx_pncp_raw_bids_fts GIN(tsv), idx_pncp_raw_bids_uf_date (partial), idx_pncp_raw_bids_content_hash.

---

### ingestion_checkpoints

Per-(source, uf, modalidade, batch) crawl progress for resumable crawls.

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | bigint IDENTITY PK | No | — |
| source | text | No | 'pncp' |
| uf | text | No | — |
| modalidade_id | integer | No | — |
| last_date | date | No | — |
| last_page | integer | Yes | 1 |
| records_fetched | integer | Yes | 0 |
| status | text | No | 'pending' |
| error_message | text | Yes | — |
| started_at | timestamptz | Yes | — |
| completed_at | timestamptz | Yes | — |
| crawl_batch_id | text | No | — |

**Unique:** (source, uf, modalidade_id, crawl_batch_id). **Status CHECK:** pending, running, completed, failed.

---

### ingestion_runs

Top-level ingestion batch ledger.

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | bigint IDENTITY PK | No | — |
| crawl_batch_id | text UNIQUE | No | — |
| run_type | text | No | — |
| status | text | No | 'running' |
| started_at | timestamptz | No | now() |
| completed_at | timestamptz | Yes | — |
| total_fetched | integer | No | 0 |
| inserted | integer | No | 0 |
| updated | integer | No | 0 |
| unchanged | integer | No | 0 |
| errors | integer | No | 0 |
| ufs_completed | text[] | Yes | — |
| ufs_failed | text[] | Yes | — |
| duration_s | numeric(10,1) | Yes | — |
| metadata | jsonb | No | '{}' |

**run_type CHECK:** full, incremental. **status CHECK:** running, completed, failed, partial. **JSONB constraint:** metadata < 512KB.

---

### conversations / messages

InMail messaging system.

**conversations:** id (uuid), user_id, subject (max 200), category (suporte/sugestao/funcionalidade/bug/outro), status (aberto/respondido/resolvido), first_response_at, last_message_at, created_at, updated_at.

**messages:** id (uuid), conversation_id, sender_id, body (1-5000 chars), is_admin_reply, read_by_user, read_by_admin, created_at. Trigger updates parent conversation.last_message_at.

---

### stripe_webhook_events

Idempotency log. 90-day retention.

Columns: id (varchar PK, evt_xxx format), type, processed_at, payload (jsonb), status (varchar, default 'completed'), received_at.

---

### audit_events

Security audit log with hashed PII (LGPD). 12-month retention.

Columns: id (uuid), timestamp, event_type, actor_id_hash (SHA-256 x16), target_id_hash, details (jsonb), ip_hash.

---

### trial_email_log

Trial email sequence tracking (6 emails over 14 days).

Columns: id (uuid), user_id, email_type, email_number (1-6 CHECK), sent_at, opened_at, clicked_at, resend_email_id. Unique: (user_id, email_number).

---

### alert_preferences / alerts / alert_sent_items / alert_runs

Email alert system.

- **alert_preferences:** user_id (unique), frequency (ENUM: daily/twice_weekly/weekly/off), enabled, last_digest_sent_at. Auto-created on profile insert.
- **alerts:** user_id, name, filters (jsonb), active.
- **alert_sent_items:** alert_id, item_id (unique pair), sent_at.
- **alert_runs:** alert_id, run_at, items_found, items_sent, status.

---

### user_oauth_tokens / google_sheets_exports

OAuth and export tracking.

- **user_oauth_tokens:** user_id, provider (google/microsoft/dropbox), access_token (AES-256), refresh_token, expires_at, scope. Unique: (user_id, provider).
- **google_sheets_exports:** user_id, spreadsheet_id, spreadsheet_url, search_params (jsonb GIN), total_rows, created_at, last_updated_at.

---

### organizations / organization_members

Multi-user org accounts.

- **organizations:** id, name, logo_url, owner_id (FK profiles RESTRICT), max_members (default 5), plan_type ('consultoria'), stripe_customer_id.
- **organization_members:** org_id, user_id (unique pair), role (owner/admin/member), invited_at, accepted_at.

---

### partners / partner_referrals

Revenue share tracking.

- **partners:** id, name, slug (unique), contact_email, revenue_share_pct (default 25%), status, stripe_coupon_id.
- **partner_referrals:** partner_id, referred_user_id (nullable, SET NULL on delete), signup_at, converted_at, churned_at, monthly_revenue, revenue_share_amount.

---

### reconciliation_log / health_checks / incidents

Operations tables.

- **reconciliation_log:** Stripe-DB sync audit. Columns: run_at, total_checked, divergences_found, auto_fixed, manual_review, duration_ms, details (jsonb).
- **health_checks:** Periodic health results. Columns: checked_at, overall_status (healthy/degraded/unhealthy), sources_json, components_json, latency_ms. 30-day retention.
- **incidents:** System incidents. Columns: started_at, resolved_at, status (ongoing/resolved), affected_sources, description.

---

### mfa_recovery_codes / mfa_recovery_attempts

MFA backup authentication.

- **mfa_recovery_codes:** user_id, code_hash (bcrypt), used_at, created_at.
- **mfa_recovery_attempts:** user_id, attempted_at, success. Brute force tracking.

---

## Functions / RPCs

### Quota

| Function | Returns | Purpose |
|----------|---------|---------|
| `check_and_increment_quota(user_id, month_year, max_quota)` | (allowed, new_count, previous_count, quota_remaining) | Primary atomic quota enforcement |
| `increment_quota_atomic(user_id, month_year, max_quota)` | (new_count, was_at_limit, previous_count) | Legacy atomic increment |
| `increment_quota_fallback_atomic(user_id, month_year, max_quota)` | (new_count) | Concurrency fallback |

### Datalake

| Function | Purpose |
|----------|---------|
| `upsert_pncp_raw_bids(p_records JSONB)` | Batch upsert via INSERT ON CONFLICT. SECURITY DEFINER. Returns (inserted, updated, unchanged). |
| `search_datalake(p_ufs, p_date_start, p_date_end, p_tsquery, p_modalidades, p_valor_min, p_valor_max, p_esferas, p_modo, p_limit)` | Full-featured search using pre-computed tsv. Two modes: publicacao/abertas. Max 5000. SECURITY DEFINER. |
| `purge_old_bids(p_retention_days)` | Hard-deletes bids older than retention (default 12 days). SECURITY DEFINER. |

### Analytics / Messaging

| Function | Purpose |
|----------|---------|
| `get_conversations_with_unread_count(...)` | Eliminates N+1 in conversation listing |
| `get_analytics_summary(user_id, start, end)` | Summary stats (searches, value, member_since) |

### Billing Helpers

| Function | Purpose |
|----------|---------|
| `get_user_billing_period(user_id)` | Returns current billing period |
| `user_has_feature(user_id, feature_key)` | Check plan feature access |
| `get_user_features(user_id)` | Get all enabled features |

### Utility

| Function | Purpose |
|----------|---------|
| `handle_new_user()` | Trigger: auto-creates profile on signup |
| `set_updated_at()` | Canonical updated_at trigger function |
| `get_table_columns_simple(table_name)` | Schema validation RPC |
| `pncp_raw_bids_tsv_trigger()` | Maintains pre-computed tsv column |
| `check_pncp_raw_bids_bloat()` | Monitoring: dead tuple ratio |
| `check_ingestion_orphans()` | Monitoring: orphan checkpoints |

### Views

| View | Purpose |
|------|---------|
| `ingestion_orphan_checkpoints` | Checkpoints without matching runs |
| `pncp_raw_bids_bloat_stats` | Table bloat statistics |

---

## Triggers

| Trigger | Table | Function | Event |
|---------|-------|----------|-------|
| on_auth_user_created | auth.users | handle_new_user() | AFTER INSERT |
| trg_profiles_updated_at | profiles | set_updated_at() | BEFORE UPDATE |
| trg_plans_updated_at | plans | set_updated_at() | BEFORE UPDATE |
| trg_plan_features_updated_at | plan_features | set_updated_at() | BEFORE UPDATE |
| trg_user_subscriptions_updated_at | user_subscriptions | set_updated_at() | BEFORE UPDATE |
| trg_organizations_updated_at | organizations | set_updated_at() | BEFORE UPDATE |
| tr_pipeline_items_updated_at | pipeline_items | set_updated_at() | BEFORE UPDATE |
| trigger_alert_preferences_updated_at | alert_preferences | set_updated_at() | BEFORE UPDATE |
| trigger_alerts_updated_at | alerts | set_updated_at() | BEFORE UPDATE |
| trg_pncp_raw_bids_updated_at | pncp_raw_bids | set_updated_at() | BEFORE UPDATE |
| trg_pncp_raw_bids_tsv | pncp_raw_bids | pncp_raw_bids_tsv_trigger() | BEFORE INSERT/UPDATE OF objeto_compra |
| trg_update_conversation_last_message | messages | update_conversation_last_message() | AFTER INSERT |
| trg_cleanup_search_cache | search_results_cache | cleanup_search_cache_per_user() | AFTER INSERT |
| trigger_create_alert_preferences_on_profile | profiles | create_default_alert_preferences() | AFTER INSERT |

---

## pg_cron Jobs

| Job | Schedule | Action |
|-----|----------|--------|
| cleanup-monthly-quota | 1st monthly, 2am UTC | DELETE monthly_quota > 24 months |
| cleanup-webhook-events | Daily, 3am UTC | DELETE stripe_webhook_events > 90 days |
| cleanup-audit-events | 1st monthly, 4am UTC | DELETE audit_events > 12 months |
| cleanup-cold-cache-entries | Daily, 5am UTC | DELETE cold cache > 7 days |
| cleanup-expired-search-results | Daily, 4am UTC | DELETE expired results > 7 days |

---

## FK Reference Standard

All user-referencing FKs standardized to `profiles(id)` (not auth.users) via migration waves 018, 20260225120000, 20260304100000.

**ON DELETE behavior:**
- Most tables: `CASCADE`
- user_subscriptions.plan_id -> plans: `RESTRICT`
- organizations.owner_id -> profiles: `RESTRICT`
- partner_referrals.referred_user_id -> profiles: `SET NULL`

---

## RLS Policy Patterns

All 35 tables have RLS enabled. Naming convention (DEBT-207): `{action}_{table}_{role}`.

1. **User-owned:** `auth.uid() = user_id` (SELECT/INSERT/UPDATE/DELETE)
2. **Service role:** `TO service_role USING (true)` (ALL operations)
3. **Admin read:** `profiles.is_admin = true` check
4. **Public read:** `USING (true)` for catalog tables (plans, plan_billing_periods)
5. **Authenticated read:** `TO authenticated USING (true)` for public data (pncp_raw_bids)

---

## Custom Type

```sql
CREATE TYPE alert_frequency AS ENUM ('daily', 'twice_weekly', 'weekly', 'off');
```
