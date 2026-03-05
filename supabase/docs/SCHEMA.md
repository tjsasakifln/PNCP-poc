# SmartLic Database Schema Documentation

**Provider:** Supabase (PostgreSQL 17)
**Project Ref:** `fqqyovlzdzimiwfofdjk`
**Schema Generated:** 2026-03-04
**Migrations Analyzed:** 66 migration files (56 Supabase + 10 backend-specific)
**Total Tables:** 27
**Total Functions:** 15
**Total Triggers:** 12
**Total Enums:** 1

---

## Table of Contents

1. [Tables](#tables)
   - [profiles](#1-profiles)
   - [plans](#2-plans)
   - [user_subscriptions](#3-user_subscriptions)
   - [plan_features](#4-plan_features)
   - [plan_billing_periods](#5-plan_billing_periods)
   - [monthly_quota](#6-monthly_quota)
   - [search_sessions](#7-search_sessions)
   - [search_results_cache](#8-search_results_cache)
   - [search_results_store](#9-search_results_store)
   - [search_state_transitions](#10-search_state_transitions)
   - [pipeline_items](#11-pipeline_items)
   - [conversations](#12-conversations)
   - [messages](#13-messages)
   - [stripe_webhook_events](#14-stripe_webhook_events)
   - [user_oauth_tokens](#15-user_oauth_tokens)
   - [google_sheets_exports](#16-google_sheets_exports)
   - [audit_events](#17-audit_events)
   - [classification_feedback](#18-classification_feedback)
   - [trial_email_log](#19-trial_email_log)
   - [alert_preferences](#20-alert_preferences)
   - [alerts](#21-alerts)
   - [alert_sent_items](#22-alert_sent_items)
   - [alert_runs](#23-alert_runs)
   - [reconciliation_log](#24-reconciliation_log)
   - [health_checks](#25-health_checks)
   - [incidents](#26-incidents)
   - [mfa_recovery_codes](#27-mfa_recovery_codes)
   - [mfa_recovery_attempts](#28-mfa_recovery_attempts)
   - [organizations](#29-organizations)
   - [organization_members](#30-organization_members)
   - [partners](#31-partners)
   - [partner_referrals](#32-partner_referrals)
2. [Functions / Stored Procedures](#functions--stored-procedures)
3. [Triggers](#triggers)
4. [Enums / Custom Types](#enums--custom-types)
5. [Extensions](#extensions)

---

## Tables

### 1. profiles

- **Purpose:** Extends auth.users with application-specific user data (plan, company, admin status, onboarding context).
- **Created:** Migration 001
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | - | PK, FK -> auth.users(id) ON DELETE CASCADE |
| email | text | NO | - | UNIQUE (partial index) |
| full_name | text | YES | - | - |
| company | text | YES | - | - |
| plan_type | text | NO | 'free_trial' | CHECK: free_trial, consultor_agil, maquina, sala_guerra, master, smartlic_pro, consultoria |
| avatar_url | text | YES | - | - |
| is_admin | boolean | NO | false | Partial index WHERE true |
| sector | text | YES | - | - |
| phone_whatsapp | text | YES | - | CHECK: 10-11 digits, UNIQUE (partial WHERE NOT NULL) |
| whatsapp_consent | boolean | YES | false | - |
| whatsapp_consent_at | timestamptz | YES | - | - |
| context_data | jsonb | YES | '{}' | Onboarding wizard data |
| subscription_status | text | YES | 'trial' | CHECK: trial, active, canceling, past_due, expired |
| trial_expires_at | timestamptz | YES | - | - |
| subscription_end_date | timestamptz | YES | - | - |
| email_unsubscribed | boolean | YES | false | - |
| email_unsubscribed_at | timestamptz | YES | - | - |
| marketing_emails_enabled | boolean | NO | true | - |
| referred_by_partner_id | uuid | YES | - | FK -> partners(id) |
| created_at | timestamptz | NO | now() | - |
| updated_at | timestamptz | NO | now() | Auto-updated by trigger |

- **Indexes:**
  - `idx_profiles_is_admin` (partial WHERE is_admin = true)
  - `idx_profiles_whatsapp_consent` (partial WHERE whatsapp_consent = true)
  - `idx_profiles_email_trgm` (GIN, trigram ops for ILIKE search)
  - `idx_profiles_email_unique` (UNIQUE partial WHERE NOT NULL)
  - `idx_profiles_phone_whatsapp_unique` (UNIQUE partial WHERE NOT NULL)
  - `idx_profiles_context_porte` (btree on context_data->>'porte_empresa')
  - `idx_profiles_subscription_status` (partial WHERE != 'trial')
  - `idx_profiles_referred_by_partner` (partial WHERE NOT NULL)
- **RLS Policies:**
  - `profiles_select_own` SELECT USING (auth.uid() = id)
  - `profiles_update_own` UPDATE USING (auth.uid() = id)
  - `profiles_insert_own` INSERT TO authenticated WITH CHECK (auth.uid() = id)
  - `profiles_insert_service` INSERT TO service_role WITH CHECK (true)
  - `profiles_service_all` ALL TO service_role USING (true)
- **Used by:** auth.py, authorization.py, quota.py, routes/user.py, routes/admin.py, routes/billing.py, routes/analytics.py

---

### 2. plans

- **Purpose:** Plan catalog defining subscription tiers, pricing, and Stripe price IDs.
- **Created:** Migration 001, updated in 005, 015, 029, 20260226120000, 20260301300000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | text | NO | - | PK |
| name | text | NO | - | - |
| description | text | YES | - | - |
| max_searches | int | YES | - | NULL = unlimited |
| price_brl | numeric(10,2) | NO | 0 | - |
| duration_days | int | YES | - | NULL = perpetual |
| stripe_price_id | text | YES | - | Legacy default column |
| stripe_price_id_monthly | text | YES | - | - |
| stripe_price_id_annual | text | YES | - | - |
| stripe_price_id_semiannual | text | YES | - | Added migration 029 |
| is_active | boolean | NO | true | - |
| created_at | timestamptz | NO | now() | - |
| updated_at | timestamptz | NO | now() | Auto-updated by trigger |

- **Active Plans:** free_trial (implicit), smartlic_pro (R$397/mo), consultoria (R$997/mo), master
- **Legacy Plans (inactive):** free, pack_5/10/20, monthly, annual, consultor_agil, maquina, sala_guerra
- **RLS Policies:**
  - `plans_select_all` SELECT USING (true) -- public catalog
- **Used by:** quota.py, services/billing.py, routes/billing.py

---

### 3. user_subscriptions

- **Purpose:** Tracks active/historical user subscriptions with Stripe integration.
- **Created:** Migration 001, extended in 008, 021, 20260225100000, 20260227130000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| user_id | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| plan_id | text | NO | - | FK -> plans(id) ON DELETE RESTRICT |
| credits_remaining | int | YES | - | NULL = unlimited |
| starts_at | timestamptz | NO | now() | - |
| expires_at | timestamptz | YES | - | NULL = never expires |
| stripe_subscription_id | text | YES | - | UNIQUE (partial WHERE NOT NULL) |
| stripe_customer_id | text | YES | - | Indexed partial WHERE NOT NULL |
| is_active | boolean | NO | true | - |
| billing_period | varchar(10) | NO | 'monthly' | CHECK: monthly, semiannual, annual |
| annual_benefits | jsonb | NO | '{}' | - |
| subscription_status | text | YES | 'active' | CHECK: active, trialing, past_due, canceled, expired |
| first_failed_at | timestamptz | YES | NULL | For dunning tracking |
| created_at | timestamptz | NO | now() | - |
| updated_at | timestamptz | NO | now() | Auto-updated by trigger |

- **Indexes:**
  - `idx_user_subscriptions_user` (user_id)
  - `idx_user_subscriptions_active` (user_id, is_active) WHERE is_active = true
  - `idx_user_subscriptions_billing` (user_id, billing_period, is_active) WHERE is_active = true
  - `idx_user_subscriptions_stripe_sub_id` UNIQUE (stripe_subscription_id) WHERE NOT NULL
  - `idx_user_subscriptions_customer_id` (stripe_customer_id) WHERE NOT NULL
  - `idx_user_subscriptions_first_failed_at` (first_failed_at) WHERE NOT NULL
- **RLS Policies:**
  - `subscriptions_select_own` SELECT USING (auth.uid() = user_id)
  - `Service role can manage subscriptions` ALL TO service_role
- **Used by:** services/billing.py, webhooks/stripe.py, quota.py, routes/billing.py

---

### 4. plan_features

- **Purpose:** Billing-period-specific feature flags for subscription plans.
- **Created:** Migration 009
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | serial | NO | - | PK |
| plan_id | text | NO | - | FK -> plans(id) ON DELETE CASCADE |
| billing_period | varchar(10) | NO | - | CHECK: monthly, semiannual, annual |
| feature_key | varchar(100) | NO | - | - |
| enabled | boolean | NO | true | - |
| metadata | jsonb | YES | '{}' | - |
| created_at | timestamptz | NO | now() | - |
| updated_at | timestamptz | NO | now() | Auto-updated by trigger |

- **Unique:** (plan_id, billing_period, feature_key)
- **Indexes:** `idx_plan_features_lookup` (plan_id, billing_period, enabled) WHERE enabled = true
- **RLS Policies:**
  - `plan_features_select_all` SELECT USING (true) -- public catalog
- **Used by:** services/billing.py, quota.py

---

### 5. plan_billing_periods

- **Purpose:** Multi-period pricing for plans (monthly/semiannual/annual with discounts).
- **Created:** Migration 029
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| plan_id | text | NO | - | FK -> plans(id) ON DELETE CASCADE |
| billing_period | text | NO | - | CHECK: monthly, semiannual, annual |
| price_cents | integer | NO | - | - |
| discount_percent | integer | YES | 0 | - |
| stripe_price_id | text | YES | - | - |
| created_at | timestamptz | YES | now() | - |

- **Unique:** (plan_id, billing_period)
- **RLS Policies:**
  - `plan_billing_periods_public_read` SELECT TO authenticated, anon USING (true)
  - `plan_billing_periods_service_all` ALL TO service_role
- **Used by:** services/billing.py, routes/billing.py

---

### 6. monthly_quota

- **Purpose:** Tracks monthly search quota usage per user for plan-based pricing.
- **Created:** Migration 002
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| user_id | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| month_year | varchar(7) | NO | - | Format: "YYYY-MM" |
| searches_count | int | NO | 0 | - |
| created_at | timestamptz | NO | now() | - |
| updated_at | timestamptz | NO | now() | - |

- **Unique:** (user_id, month_year)
- **Indexes:** `idx_monthly_quota_user_month` (user_id, month_year)
- **Retention:** 24 months (pg_cron cleanup)
- **RLS Policies:**
  - `Users can view own quota` SELECT USING (auth.uid() = user_id)
  - `Service role can manage quota` ALL TO service_role
- **Used by:** quota.py (via RPC functions)

---

### 7. search_sessions

- **Purpose:** Search history per user. Records every search attempt with lifecycle tracking.
- **Created:** Migration 001, extended in 20260220120000, 20260221100000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| user_id | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| search_id | uuid | YES | NULL | Correlation with SSE/ARQ |
| sectors | text[] | NO | - | - |
| ufs | text[] | NO | - | - |
| data_inicial | date | NO | - | - |
| data_final | date | NO | - | - |
| custom_keywords | text[] | YES | - | - |
| total_raw | int | NO | 0 | - |
| total_filtered | int | NO | 0 | - |
| valor_total | numeric(14,2) | YES | 0 | - |
| resumo_executivo | text | YES | - | - |
| destaques | text[] | YES | - | - |
| excel_storage_path | text | YES | - | - |
| status | text | NO | 'created' | CHECK: created, processing, completed, failed, timed_out, cancelled |
| error_message | text | YES | - | - |
| error_code | text | YES | - | - |
| started_at | timestamptz | NO | now() | - |
| completed_at | timestamptz | YES | - | - |
| duration_ms | integer | YES | - | - |
| pipeline_stage | text | YES | - | - |
| raw_count | integer | YES | 0 | - |
| response_state | text | YES | - | live, cached, degraded, empty_failure |
| failed_ufs | text[] | YES | - | - |
| created_at | timestamptz | NO | now() | - |

- **Indexes:**
  - `idx_search_sessions_user` (user_id)
  - `idx_search_sessions_created` (user_id, created_at DESC)
  - `idx_search_sessions_search_id` (search_id) WHERE NOT NULL
  - `idx_search_sessions_status` (status) WHERE IN ('created', 'processing')
  - `idx_search_sessions_inflight` (status, started_at) WHERE IN ('created', 'processing')
  - `idx_search_sessions_user_status_created` (user_id, status, created_at DESC)
- **RLS Policies:**
  - `sessions_select_own` SELECT USING (auth.uid() = user_id)
  - `sessions_insert_own` INSERT WITH CHECK (auth.uid() = user_id)
  - `Service role can manage search sessions` ALL TO service_role
- **Used by:** routes/search.py, routes/sessions.py, routes/analytics.py, search_pipeline.py

---

### 8. search_results_cache

- **Purpose:** Persistent L2 cache of search results per user (SWR pattern). Max 10 entries per user with priority-aware eviction.
- **Created:** Migration 026, extended in 027b, 031, 032, 033, 20260223100000, 20260224200000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| user_id | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| params_hash | text | NO | - | - |
| params_hash_global | text | YES | - | Cross-user cache sharing |
| search_params | jsonb | NO | - | - |
| results | jsonb | NO | - | CHECK: octet_length <= 2MB |
| total_results | integer | NO | 0 | - |
| sources_json | jsonb | NO | '["pncp"]' | Data source tracking |
| fetched_at | timestamptz | NO | now() | When live fetch occurred |
| priority | text | NO | 'cold' | hot/warm/cold |
| access_count | integer | NO | 0 | - |
| last_accessed_at | timestamptz | YES | - | - |
| last_success_at | timestamptz | YES | - | - |
| last_attempt_at | timestamptz | YES | - | - |
| fail_streak | integer | NO | 0 | - |
| degraded_until | timestamptz | YES | - | - |
| coverage | jsonb | YES | - | - |
| fetch_duration_ms | integer | YES | - | - |
| created_at | timestamptz | NO | now() | - |

- **Unique:** (user_id, params_hash)
- **Indexes:**
  - `idx_search_cache_user` (user_id, created_at DESC)
  - `idx_search_cache_params_hash` (params_hash)
  - `idx_search_cache_fetched_at` (fetched_at)
  - `idx_search_cache_degraded` (degraded_until) WHERE NOT NULL
  - `idx_search_cache_priority` (user_id, priority, last_accessed_at)
  - `idx_search_cache_global_hash` (params_hash_global, created_at DESC)
- **Retention:** Cold entries > 7 days (pg_cron cleanup)
- **RLS Policies:**
  - `Users can read own search cache` SELECT USING (auth.uid() = user_id)
  - `Service role full access on search_results_cache` ALL TO service_role
- **Used by:** search_cache.py, routes/search.py, routes/admin.py

---

### 9. search_results_store

- **Purpose:** Persistent L3 storage for search results. Prevents "Busca nao encontrada ou expirada" after L1/L2 TTL expiry.
- **Created:** Migration 20260303100000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| search_id | uuid | NO | - | PK |
| user_id | uuid | NO | - | FK -> auth.users(id) |
| results | jsonb | NO | - | - |
| sector | text | YES | - | - |
| ufs | text[] | YES | - | - |
| total_filtered | int | YES | 0 | - |
| created_at | timestamptz | YES | now() | - |
| expires_at | timestamptz | YES | now() + 24h | - |

- **Indexes:**
  - `idx_search_results_user` (user_id)
  - `idx_search_results_expires` (expires_at)
- **RLS Policies:**
  - `Users can read own results` SELECT USING (auth.uid() = user_id)
  - `Service role full access` ALL USING (auth.role() = 'service_role')
- **Used by:** routes/search.py

---

### 10. search_state_transitions

- **Purpose:** Audit trail for search state machine transitions. Fire-and-forget inserts.
- **Created:** Migration 20260221100002
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| search_id | uuid | NO | - | - |
| from_state | text | YES | - | NULL for initial CREATED |
| to_state | text | NO | - | - |
| stage | text | YES | - | - |
| details | jsonb | YES | '{}' | - |
| duration_since_previous_ms | integer | YES | - | - |
| created_at | timestamptz | NO | now() | - |

- **Indexes:**
  - `idx_state_transitions_search_id` (search_id, created_at ASC)
  - `idx_state_transitions_to_state` (to_state, created_at)
- **RLS Policies:**
  - `Users can read own transitions` SELECT (join through search_sessions)
  - `Service role can insert transitions` INSERT TO service_role
- **Note:** No FK to search_sessions (fire-and-forget pattern; search_id may not be persisted yet)
- **Used by:** search_state_manager.py, routes/admin_trace.py

---

### 11. pipeline_items

- **Purpose:** Kanban pipeline tracking procurement opportunities through stages.
- **Created:** Migration 025, extended in 20260227120002
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| user_id | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| pncp_id | text | NO | - | - |
| objeto | text | NO | - | - |
| orgao | text | YES | - | - |
| uf | text | YES | - | - |
| valor_estimado | numeric | YES | - | - |
| data_encerramento | timestamptz | YES | - | - |
| link_pncp | text | YES | - | - |
| stage | text | NO | 'descoberta' | CHECK: descoberta, analise, preparando, enviada, resultado |
| notes | text | YES | - | - |
| version | integer | NO | 1 | Optimistic locking |
| created_at | timestamptz | NO | now() | - |
| updated_at | timestamptz | NO | now() | Auto-updated by trigger |

- **Unique:** (user_id, pncp_id)
- **Indexes:**
  - `idx_pipeline_user_stage` (user_id, stage)
  - `idx_pipeline_encerramento` (data_encerramento) WHERE stage NOT IN ('enviada', 'resultado')
  - `idx_pipeline_user_created` (user_id, created_at DESC)
- **RLS Policies:**
  - `Users can view/insert/update/delete own pipeline items` (4 policies)
  - `Service role full access on pipeline_items` ALL TO service_role
- **Used by:** routes/pipeline.py

---

### 12. conversations

- **Purpose:** InMail messaging threads between users and admins.
- **Created:** Migration 012, extended in 20260301400000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| user_id | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| subject | text | NO | - | CHECK: <= 200 chars |
| category | text | NO | - | CHECK: suporte, sugestao, funcionalidade, bug, outro |
| status | text | NO | 'aberto' | CHECK: aberto, respondido, resolvido |
| first_response_at | timestamptz | YES | - | SLA tracking |
| last_message_at | timestamptz | NO | now() | Auto-updated by trigger |
| created_at | timestamptz | NO | now() | - |
| updated_at | timestamptz | NO | now() | - |

- **Indexes:**
  - `idx_conversations_user_id` (user_id)
  - `idx_conversations_status` (status)
  - `idx_conversations_last_message` (last_message_at DESC)
  - `idx_conversations_unanswered` (created_at) WHERE first_response_at IS NULL AND status != 'resolvido'
- **RLS Policies:**
  - `conversations_select_own` SELECT (user OR admin)
  - `conversations_insert_own` INSERT WITH CHECK (auth.uid() = user_id)
  - `conversations_update_admin` UPDATE (admin only)
  - `conversations_service_all` ALL TO service_role
- **Used by:** routes/messages.py

---

### 13. messages

- **Purpose:** Individual messages within conversations.
- **Created:** Migration 012
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| conversation_id | uuid | NO | - | FK -> conversations(id) ON DELETE CASCADE |
| sender_id | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| body | text | NO | - | CHECK: 1-5000 chars |
| is_admin_reply | boolean | NO | false | - |
| read_by_user | boolean | NO | false | - |
| read_by_admin | boolean | NO | false | - |
| created_at | timestamptz | NO | now() | - |

- **Indexes:**
  - `idx_messages_conversation` (conversation_id, created_at)
  - `idx_messages_unread_by_user` (conversation_id) WHERE is_admin_reply = true AND read_by_user = false
  - `idx_messages_unread_by_admin` (conversation_id) WHERE is_admin_reply = false AND read_by_admin = false
- **RLS Policies:**
  - `messages_select` SELECT (conversation owner OR admin)
  - `messages_insert_user` INSERT WITH CHECK (sender + conversation owner)
  - `messages_update_read` UPDATE (conversation owner OR admin)
  - `messages_service_all` ALL TO service_role
- **Used by:** routes/messages.py

---

### 14. stripe_webhook_events

- **Purpose:** Idempotency store for Stripe webhook events. Prevents duplicate processing.
- **Created:** Migration 010, extended in 028, 20260227120001
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | varchar(255) | NO | - | PK, CHECK: starts with 'evt_' |
| type | varchar(100) | NO | - | - |
| status | varchar(20) | NO | 'completed' | processing, completed, failed |
| processed_at | timestamptz | NO | now() | - |
| received_at | timestamptz | YES | now() | For stuck event detection |
| payload | jsonb | YES | - | Full Stripe event object |

- **Indexes:**
  - `idx_webhook_events_type` (type, processed_at)
  - `idx_webhook_events_recent` (processed_at DESC)
- **Retention:** 90 days (pg_cron cleanup)
- **RLS Policies:**
  - `webhook_events_insert_service` INSERT TO service_role
  - `webhook_events_select_admin` SELECT TO authenticated (WHERE is_admin)
  - `webhook_events_service_role_select` SELECT TO service_role
- **Used by:** webhooks/stripe.py, services/billing.py

---

### 15. user_oauth_tokens

- **Purpose:** Encrypted OAuth 2.0 tokens for third-party integrations (Google Sheets).
- **Created:** Migration 013
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| user_id | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| provider | varchar(50) | NO | - | CHECK: google, microsoft, dropbox |
| access_token | text | NO | - | AES-256 encrypted |
| refresh_token | text | YES | - | AES-256 encrypted |
| expires_at | timestamptz | NO | - | - |
| scope | text | NO | - | - |
| created_at | timestamptz | YES | now() | - |
| updated_at | timestamptz | YES | now() | - |

- **Unique:** (user_id, provider)
- **Indexes:**
  - `idx_user_oauth_tokens_user_id` (user_id)
  - `idx_user_oauth_tokens_expires_at` (expires_at)
- **RLS Policies:**
  - Users can view/update/delete own OAuth tokens (3 policies)
  - `Service role can manage all OAuth tokens` ALL TO service_role
- **Used by:** oauth.py, google_sheets.py

---

### 16. google_sheets_exports

- **Purpose:** Audit trail for Google Sheets exports. Enables "re-open last export".
- **Created:** Migration 014
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| user_id | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| spreadsheet_id | varchar(255) | NO | - | - |
| spreadsheet_url | text | NO | - | - |
| search_params | jsonb | NO | - | - |
| total_rows | int | NO | - | CHECK >= 0 |
| created_at | timestamptz | YES | now() | - |
| last_updated_at | timestamptz | YES | now() | - |

- **Indexes:**
  - `idx_google_sheets_exports_user_id` (user_id)
  - `idx_google_sheets_exports_created_at` (created_at DESC)
  - `idx_google_sheets_exports_spreadsheet_id` (spreadsheet_id)
  - `idx_google_sheets_exports_search_params` (GIN on search_params)
- **RLS Policies:**
  - Users can view/insert/update own exports (3 policies)
  - `Service role can manage all Google Sheets exports` ALL TO service_role
- **Used by:** google_sheets.py

---

### 17. audit_events

- **Purpose:** Persistent audit log for security-relevant events. PII stored as SHA-256 hashes.
- **Created:** Migration 023
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| timestamp | timestamptz | NO | now() | - |
| event_type | text | NO | - | - |
| actor_id_hash | text | YES | - | SHA-256 truncated 16 hex |
| target_id_hash | text | YES | - | SHA-256 truncated 16 hex |
| details | jsonb | YES | - | - |
| ip_hash | text | YES | - | SHA-256 truncated 16 hex |

- **Indexes:**
  - `idx_audit_events_event_type` (event_type)
  - `idx_audit_events_timestamp` (timestamp)
  - `idx_audit_events_actor` (actor_id_hash) WHERE NOT NULL
  - `idx_audit_events_type_timestamp` (event_type, timestamp DESC)
- **Retention:** 12 months (pg_cron cleanup)
- **RLS Policies:**
  - `Service role can manage audit events` ALL TO service_role
  - `Admins can read audit events` SELECT (WHERE is_admin)
- **Used by:** audit.py

---

### 18. classification_feedback

- **Purpose:** User feedback on search result relevance for continuous improvement.
- **Created:** Backend migration 006
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| user_id | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| search_id | uuid | NO | - | - |
| bid_id | text | NO | - | - |
| setor_id | text | NO | - | - |
| user_verdict | text | NO | - | CHECK: false_positive, false_negative, correct |
| reason | text | YES | - | - |
| category | text | YES | - | CHECK: wrong_sector, irrelevant_modality, too_small, too_large, closed, other |
| bid_objeto | text | YES | - | - |
| bid_valor | decimal | YES | - | - |
| bid_uf | text | YES | - | - |
| confidence_score | integer | YES | - | - |
| relevance_source | text | YES | - | - |
| created_at | timestamptz | YES | now() | - |

- **Unique:** (user_id, search_id, bid_id)
- **Indexes:**
  - `idx_feedback_sector_verdict` (setor_id, user_verdict, created_at)
  - `idx_feedback_user_created` (user_id, created_at)
- **RLS Policies:**
  - `feedback_insert_own` INSERT WITH CHECK (auth.uid() = user_id)
  - `feedback_select_own` SELECT USING (auth.uid() = user_id)
  - `feedback_update_own` UPDATE USING (auth.uid() = user_id)
  - `feedback_delete_own` DELETE USING (auth.uid() = user_id)
  - `feedback_admin_all` ALL USING (auth.role() = 'service_role')
- **Used by:** routes/feedback.py, feedback_analyzer.py

---

### 19. trial_email_log

- **Purpose:** Tracks trial email sequence (6 emails over 14 days) for idempotent delivery.
- **Created:** Migration 20260224100000, extended in 20260227140000, 20260228110000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| user_id | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| email_type | text | NO | - | midpoint, expiring, last_day, expired |
| email_number | integer | YES | - | CHECK: 1-6 |
| sent_at | timestamptz | NO | now() | - |
| opened_at | timestamptz | YES | - | Resend webhook |
| clicked_at | timestamptz | YES | - | Resend webhook |
| resend_email_id | text | YES | - | For webhook correlation |

- **Unique:** (user_id, email_number)
- **Indexes:**
  - `idx_trial_email_log_user_id` (user_id)
  - `idx_trial_email_log_resend_id` (resend_email_id) WHERE NOT NULL
- **RLS Policies:** RLS enabled, no user-facing policies (service_role only via RLS bypass)
- **Used by:** email_service.py, cron_jobs.py

---

### 20. alert_preferences

- **Purpose:** Per-user email alert digest scheduling preferences.
- **Created:** Migration 20260226100000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| user_id | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE, UNIQUE |
| frequency | alert_frequency | NO | 'daily' | Enum: daily, twice_weekly, weekly, off |
| enabled | boolean | NO | true | - |
| last_digest_sent_at | timestamptz | YES | - | - |
| created_at | timestamptz | NO | now() | - |
| updated_at | timestamptz | NO | now() | Auto-updated by trigger |

- **Indexes:**
  - `idx_alert_preferences_user_id` (user_id)
  - `idx_alert_preferences_digest_due` (enabled, frequency, last_digest_sent_at) WHERE enabled AND frequency != 'off'
- **RLS Policies:**
  - Users can view/insert/update own preferences (3 policies)
  - `Service role full access to alert preferences` ALL USING (auth.role() = 'service_role')
- **Auto-created:** Trigger on profiles INSERT creates default preferences
- **Used by:** routes/user.py, cron_jobs.py

---

### 21. alerts

- **Purpose:** User-defined email alerts with search filters.
- **Created:** Migration 20260227100000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| user_id | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| name | text | NO | '' | - |
| filters | jsonb | NO | '{}' | setor, ufs[], valor_min, valor_max, keywords[] |
| active | boolean | NO | true | - |
| created_at | timestamptz | NO | now() | - |
| updated_at | timestamptz | NO | now() | Auto-updated by trigger |

- **Indexes:**
  - `idx_alerts_user_id` (user_id)
  - `idx_alerts_active` (user_id, active) WHERE active = true
- **RLS Policies:**
  - Users can view/insert/update/delete own alerts (4 policies)
  - `Service role full access to alerts` ALL TO service_role
- **Used by:** routes/pipeline.py (alerts endpoint), cron_jobs.py

---

### 22. alert_sent_items

- **Purpose:** Dedup tracking for alert email items. Prevents re-sending the same item.
- **Created:** Migration 20260227100000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| alert_id | uuid | NO | - | FK -> alerts(id) ON DELETE CASCADE |
| item_id | text | NO | - | - |
| sent_at | timestamptz | NO | now() | - |

- **Unique:** (alert_id, item_id)
- **Indexes:**
  - `idx_alert_sent_items_dedup` UNIQUE (alert_id, item_id)
  - `idx_alert_sent_items_alert_id` (alert_id)
  - `idx_alert_sent_items_sent_at` (sent_at)
- **RLS Policies:**
  - `Service role full access to alert_sent_items` ALL TO service_role
  - `Users can view own alert sent items` SELECT (via join to alerts)
- **Used by:** cron_jobs.py

---

### 23. alert_runs

- **Purpose:** Alert execution history for debugging and auditing.
- **Created:** Migration 20260228100000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| alert_id | uuid | NO | - | FK -> alerts(id) ON DELETE CASCADE |
| run_at | timestamptz | NO | now() | - |
| items_found | integer | NO | 0 | - |
| items_sent | integer | NO | 0 | - |
| status | text | NO | 'pending' | matched, no_results, no_match, all_deduped, error |

- **Indexes:**
  - `idx_alert_runs_alert_id` (alert_id)
  - `idx_alert_runs_run_at` (run_at DESC)
- **RLS Policies:**
  - `Service role full access to alert_runs` ALL TO service_role
  - `Users can view own alert runs` SELECT (via join to alerts)
- **Used by:** cron_jobs.py

---

### 24. reconciliation_log

- **Purpose:** Stripe-DB sync audit trail for billing reconciliation.
- **Created:** Migration 20260228140000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| run_at | timestamptz | NO | now() | - |
| total_checked | int | NO | 0 | - |
| divergences_found | int | NO | 0 | - |
| auto_fixed | int | NO | 0 | - |
| manual_review | int | NO | 0 | - |
| duration_ms | int | NO | 0 | - |
| details | jsonb | YES | '[]' | - |

- **Indexes:** `idx_reconciliation_log_run_at` (run_at DESC)
- **RLS Policies:**
  - `Admin read reconciliation_log` SELECT (WHERE is_admin)
  - `Service role full access reconciliation_log` ALL USING (auth.role() = 'service_role')
- **Used by:** services/billing.py (reconciliation job)

---

### 25. health_checks

- **Purpose:** Periodic health check results for uptime calculation (30-day retention).
- **Created:** Migration 20260228150000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| checked_at | timestamptz | NO | now() | - |
| overall_status | text | NO | - | CHECK: healthy, degraded, unhealthy |
| sources_json | jsonb | NO | '{}' | - |
| components_json | jsonb | NO | '{}' | - |
| latency_ms | integer | YES | - | - |

- **Indexes:** `idx_health_checks_checked_at` (checked_at DESC)
- **RLS:** Enabled (20260303200000), no user-facing policies (service_role bypass only)
- **Used by:** health.py

---

### 26. incidents

- **Purpose:** System incidents for public status page.
- **Created:** Migration 20260228150001
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| started_at | timestamptz | NO | now() | - |
| resolved_at | timestamptz | YES | - | - |
| status | text | NO | 'ongoing' | CHECK: ongoing, resolved |
| affected_sources | text[] | NO | '{}' | - |
| description | text | NO | '' | - |

- **Indexes:**
  - `idx_incidents_status` (status) WHERE status = 'ongoing'
  - `idx_incidents_started_at` (started_at DESC)
- **RLS:** Enabled (20260303200000), no user-facing policies (service_role bypass only)
- **Used by:** health.py

---

### 27. mfa_recovery_codes

- **Purpose:** Bcrypt-hashed recovery codes for TOTP MFA backup authentication.
- **Created:** Migration 20260228160000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| user_id | uuid | NO | - | FK -> auth.users(id) ON DELETE CASCADE |
| code_hash | text | NO | - | - |
| used_at | timestamptz | YES | NULL | - |
| created_at | timestamptz | NO | now() | - |

- **Indexes:**
  - `idx_mfa_recovery_codes_user_id` (user_id)
  - `idx_mfa_recovery_codes_used_at` (used_at) WHERE NOT NULL
- **RLS Policies:**
  - `Users can view own recovery codes` SELECT TO authenticated
  - `Service role full access to recovery codes` ALL TO service_role
- **Used by:** routes/user.py (MFA endpoints)

---

### 28. mfa_recovery_attempts

- **Purpose:** Brute force tracking for MFA recovery code usage.
- **Created:** Migration 20260228160000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| user_id | uuid | NO | - | FK -> auth.users(id) ON DELETE CASCADE |
| attempted_at | timestamptz | NO | now() | - |
| success | boolean | NO | false | - |

- **Indexes:** `idx_mfa_recovery_attempts_user_id_time` (user_id, attempted_at DESC)
- **RLS Policies:**
  - `Service role full access to recovery attempts` ALL TO service_role
- **Used by:** routes/user.py (MFA endpoints)

---

### 29. organizations

- **Purpose:** Multi-user organizations for consultoria/agency accounts.
- **Created:** Migration 20260301100000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| name | text | NO | - | - |
| logo_url | text | YES | - | - |
| owner_id | uuid | NO | - | FK -> auth.users(id) ON DELETE RESTRICT |
| max_members | int | NO | 5 | - |
| plan_type | text | NO | 'consultoria' | - |
| stripe_customer_id | text | YES | - | - |
| created_at | timestamptz | NO | now() | - |
| updated_at | timestamptz | NO | now() | Auto-updated by trigger |

- **Indexes:** `idx_organizations_owner` (owner_id)
- **RLS Policies:**
  - `Org owner can view organization` SELECT (owner_id)
  - `Org admins can view organization` SELECT (org admin/owner members)
  - `Owner can insert/update organization` INSERT/UPDATE (owner_id)
  - `Service role full access on organizations` ALL (auth.role() = 'service_role')
- **Used by:** routes/billing.py (planned)

---

### 30. organization_members

- **Purpose:** Members of an organization with role-based access.
- **Created:** Migration 20260301100000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| org_id | uuid | NO | - | FK -> organizations(id) ON DELETE CASCADE |
| user_id | uuid | NO | - | FK -> auth.users(id) ON DELETE CASCADE |
| role | text | NO | 'member' | CHECK: owner, admin, member |
| invited_at | timestamptz | NO | now() | - |
| accepted_at | timestamptz | YES | - | NULL = pending |

- **Unique:** (org_id, user_id)
- **Indexes:**
  - `idx_org_members_org` (org_id)
  - `idx_org_members_user` (user_id)
- **RLS Policies:**
  - `Users can view own membership` SELECT (user_id)
  - `Org owner/admin can view all members` SELECT
  - `Org owner/admin can insert/delete members` INSERT/DELETE
  - `Service role full access on organization_members` ALL
- **Used by:** routes/billing.py (planned)

---

### 31. partners

- **Purpose:** Revenue share partner accounts.
- **Created:** Migration 20260301200000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| name | text | NO | - | - |
| slug | text | NO | - | UNIQUE |
| contact_email | text | NO | - | - |
| contact_name | text | YES | - | - |
| stripe_coupon_id | text | YES | - | - |
| revenue_share_pct | numeric(5,2) | YES | 25.00 | - |
| status | text | YES | 'active' | CHECK: active, inactive, pending |
| created_at | timestamptz | YES | now() | - |

- **Indexes:**
  - `idx_partners_slug` (slug)
  - `idx_partners_status` (status)
- **RLS Policies:**
  - `partners_admin_all` ALL (WHERE is_admin)
  - `partners_self_read` SELECT (matched by contact_email)
  - `partners_service_role` ALL (auth.role() = 'service_role')
- **Used by:** routes/billing.py (planned)

---

### 32. partner_referrals

- **Purpose:** Tracks partner referrals for revenue share calculation.
- **Created:** Migration 20260301200000
- **Columns:**

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | uuid | NO | gen_random_uuid() | PK |
| partner_id | uuid | NO | - | FK -> partners(id) |
| referred_user_id | uuid | NO | - | FK -> auth.users(id) |
| signup_at | timestamptz | YES | now() | - |
| converted_at | timestamptz | YES | - | - |
| churned_at | timestamptz | YES | - | - |
| monthly_revenue | numeric(10,2) | YES | - | - |
| revenue_share_amount | numeric(10,2) | YES | - | - |

- **Unique:** (partner_id, referred_user_id)
- **Indexes:**
  - `idx_partner_referrals_partner_id` (partner_id)
  - `idx_partner_referrals_referred_user_id` (referred_user_id)
- **RLS Policies:**
  - `partner_referrals_admin_all` ALL (WHERE is_admin)
  - `partner_referrals_partner_read` SELECT (via partner join)
  - `partner_referrals_service_role` ALL (auth.role() = 'service_role')
- **Used by:** routes/billing.py (planned)

---

## Functions / Stored Procedures

### 1. handle_new_user()
- **Returns:** trigger
- **Security:** DEFINER
- **Purpose:** Auto-create profile when auth.users row is created. Normalizes phone numbers, sets plan_type='free_trial', handles ON CONFLICT.
- **Latest version:** Migration 20260225110000

### 2. update_updated_at()
- **Returns:** trigger
- **Security:** INVOKER
- **Purpose:** Generic updated_at auto-updater. Used by profiles, plans, user_subscriptions.

### 3. increment_quota_atomic(p_user_id, p_month_year, p_max_quota)
- **Returns:** TABLE (new_count, was_at_limit, previous_count)
- **Security:** INVOKER
- **Purpose:** Atomic quota check+increment with row-level locking. Prevents race conditions.
- **Grant:** service_role

### 4. check_and_increment_quota(p_user_id, p_month_year, p_max_quota)
- **Returns:** TABLE (allowed, new_count, previous_count, quota_remaining)
- **Security:** INVOKER
- **Purpose:** Combined quota check + atomic increment. Single DB call.
- **Grant:** service_role

### 5. increment_quota_fallback_atomic(p_user_id, p_month_year, p_max_quota)
- **Returns:** TABLE (new_count)
- **Security:** INVOKER
- **Purpose:** Simplified fallback quota increment for when the primary RPC fails.
- **Grant:** service_role

### 6. get_user_billing_period(p_user_id)
- **Returns:** VARCHAR(10)
- **Security:** DEFINER
- **Purpose:** Quick lookup of user's current billing period.

### 7. user_has_feature(p_user_id, p_feature_key)
- **Returns:** BOOLEAN
- **Security:** DEFINER
- **Purpose:** Check if user has specific feature based on plan + billing period.

### 8. get_user_features(p_user_id)
- **Returns:** TEXT[]
- **Security:** DEFINER
- **Purpose:** Get all enabled feature keys for user.

### 9. get_conversations_with_unread_count(p_user_id, p_is_admin, p_status, p_limit, p_offset)
- **Returns:** TABLE (id, user_id, user_email, subject, category, status, last_message_at, created_at, unread_count, total_count)
- **Security:** DEFINER
- **Purpose:** Eliminates N+1 query in conversation list.

### 10. get_analytics_summary(p_user_id, p_start_date, p_end_date)
- **Returns:** TABLE (total_searches, total_downloads, total_opportunities, total_value_discovered, member_since)
- **Security:** DEFINER
- **Purpose:** Eliminates full-table-scan in analytics summary.

### 11. cleanup_search_cache_per_user()
- **Returns:** trigger
- **Security:** DEFINER
- **Purpose:** Priority-aware cache eviction (cold -> warm -> hot). Keeps max 10 entries per user.

### 12. get_table_columns_simple(p_table_name)
- **Returns:** TABLE (column_name)
- **Security:** DEFINER
- **Purpose:** Schema validation RPC for backend startup checks.
- **Grant:** authenticated, service_role

### 13. update_conversation_last_message()
- **Returns:** trigger
- **Purpose:** Updates conversations.last_message_at when new message is inserted.

### 14. create_default_alert_preferences()
- **Returns:** trigger
- **Purpose:** Auto-creates alert_preferences row when a new profile is inserted.

### 15. update_pipeline_updated_at(), update_alert_preferences_updated_at(), update_alerts_updated_at()
- **Returns:** trigger
- **Purpose:** Dedicated updated_at triggers for pipeline_items, alert_preferences, alerts.

---

## Triggers

| Trigger | Table | Event | Function |
|---------|-------|-------|----------|
| on_auth_user_created | auth.users | AFTER INSERT | handle_new_user() |
| profiles_updated_at | profiles | BEFORE UPDATE | update_updated_at() |
| plans_updated_at | plans | BEFORE UPDATE | update_updated_at() |
| user_subscriptions_updated_at | user_subscriptions | BEFORE UPDATE | update_updated_at() |
| plan_features_updated_at | plan_features | BEFORE UPDATE | update_updated_at() |
| tr_pipeline_items_updated_at | pipeline_items | BEFORE UPDATE | update_pipeline_updated_at() |
| trg_update_conversation_last_message | messages | AFTER INSERT | update_conversation_last_message() |
| trg_cleanup_search_cache | search_results_cache | AFTER INSERT | cleanup_search_cache_per_user() |
| trigger_alert_preferences_updated_at | alert_preferences | BEFORE UPDATE | update_alert_preferences_updated_at() |
| trigger_create_alert_preferences_on_profile | profiles | AFTER INSERT | create_default_alert_preferences() |
| trigger_alerts_updated_at | alerts | BEFORE UPDATE | update_alerts_updated_at() |
| tr_organizations_updated_at | organizations | BEFORE UPDATE | update_updated_at() |

---

## Enums / Custom Types

### alert_frequency
- **Values:** daily, twice_weekly, weekly, off
- **Used by:** alert_preferences.frequency

---

## Extensions

| Extension | Purpose | Migration |
|-----------|---------|-----------|
| pg_trgm | Trigram indexing for ILIKE search on profiles.email | 016 |
| pg_cron | Scheduled cleanup jobs (quota, webhooks, audit, cache) | 022 |

---

## pg_cron Jobs

| Job Name | Schedule | Action |
|----------|----------|--------|
| cleanup-monthly-quota | 2am 1st of month | DELETE monthly_quota > 24 months |
| cleanup-webhook-events | 3am daily | DELETE stripe_webhook_events > 90 days |
| cleanup-audit-events | 4am 1st of month | DELETE audit_events > 12 months |
| cleanup-cold-cache-entries | 5am daily | DELETE search_results_cache WHERE priority='cold' AND > 7 days |

---

## System User

| ID | Email | Plan | Purpose |
|----|-------|------|---------|
| 00000000-0000-0000-0000-000000000000 | system-cache-warmer@internal.smartlic.tech | master | Cache warming background job (no quota limits) |
