# SmartLic Database Schema Documentation

**Provider:** Supabase (PostgreSQL 17)
**Project Ref:** `fqqyovlzdzimiwfofdjk`
**Schema Generated:** 2026-02-25
**Migrations Analyzed:** 42 migration files (35 Supabase + 7 backend-specific)
**Total Tables:** 15
**Total Functions:** 10
**Total Triggers:** 8

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
   - [search_state_transitions](#9-search_state_transitions)
   - [pipeline_items](#10-pipeline_items)
   - [conversations](#11-conversations)
   - [messages](#12-messages)
   - [stripe_webhook_events](#13-stripe_webhook_events)
   - [user_oauth_tokens](#14-user_oauth_tokens)
   - [google_sheets_exports](#15-google_sheets_exports)
   - [audit_events](#16-audit_events)
   - [classification_feedback](#17-classification_feedback)
   - [trial_email_log](#18-trial_email_log)
2. [Functions](#functions)
3. [Triggers](#triggers)
4. [Extensions](#extensions)
5. [Row-Level Security Summary](#row-level-security-summary)
6. [Index Catalog](#index-catalog)
7. [Entity-Relationship Diagram](#entity-relationship-diagram)

---

## Tables

### 1. profiles

**Purpose:** Extends `auth.users` with application-specific fields. Core identity table.
**Created:** Migration 001 | **Modified:** 004, 006a, 007, 016, 020, 024, 027, 029, 20260224000000

| Column | Type | Nullable | Default | Constraints | Notes |
|--------|------|----------|---------|-------------|-------|
| `id` | `uuid` | NO | - | PK, FK -> `auth.users(id) ON DELETE CASCADE` | Same as auth.users ID |
| `email` | `text` | NO | - | UNIQUE (partial index, WHERE NOT NULL) | Defense-in-depth; auth.users is source of truth |
| `full_name` | `text` | YES | - | - | From signup metadata |
| `company` | `text` | YES | - | - | User's company name |
| `plan_type` | `text` | NO | `'free_trial'` | CHECK: `IN ('free_trial','consultor_agil','maquina','sala_guerra','master','smartlic_pro')` | Current plan, synced by Stripe webhooks |
| `avatar_url` | `text` | YES | - | - | Profile picture URL |
| `is_admin` | `boolean` | NO | `false` | - | System administrator flag |
| `sector` | `text` | YES | - | - | User's business sector |
| `phone_whatsapp` | `text` | YES | - | CHECK: `phone_whatsapp IS NULL OR phone_whatsapp ~ '^[0-9]{10,11}$'`; UNIQUE (partial, WHERE NOT NULL) | Brazilian phone number (10-11 digits) |
| `whatsapp_consent` | `boolean` | YES | `false` | - | LGPD marketing consent |
| `whatsapp_consent_at` | `timestamptz` | YES | - | - | Consent timestamp (LGPD audit trail) |
| `context_data` | `jsonb` | YES | `'{}'::jsonb` | - | Onboarding business context (STORY-247) |
| `subscription_status` | `text` | YES | - | - | **Note:** Used in code but no migration creating it; likely added via Supabase dashboard |
| `trial_expires_at` | `timestamptz` | YES | - | - | **Note:** Used in code but no migration creating it; likely added via Supabase dashboard |
| `created_at` | `timestamptz` | NO | `now()` | - | Account creation |
| `updated_at` | `timestamptz` | NO | `now()` | - | Auto-updated by trigger |

**Indexes:**
| Index Name | Columns | Type | Partial |
|------------|---------|------|---------|
| `profiles_pkey` | `id` | PK (btree) | No |
| `idx_profiles_is_admin` | `is_admin` | btree | `WHERE is_admin = true` |
| `idx_profiles_whatsapp_consent` | `whatsapp_consent` | btree | `WHERE whatsapp_consent = TRUE` |
| `idx_profiles_email_trgm` | `email` | GIN (trigram) | No |
| `idx_profiles_context_porte` | `(context_data->>'porte_empresa')` | btree | `WHERE context_data->>'porte_empresa' IS NOT NULL` |
| `idx_profiles_phone_whatsapp_unique` | `phone_whatsapp` | UNIQUE btree | `WHERE phone_whatsapp IS NOT NULL` |
| `idx_profiles_email_unique` | `email` | UNIQUE btree | `WHERE email IS NOT NULL` |

**RLS Policies:**
| Policy Name | Command | Role | USING / WITH CHECK |
|-------------|---------|------|-------------------|
| `profiles_select_own` | SELECT | public | `auth.uid() = id` |
| `profiles_update_own` | UPDATE | public | `auth.uid() = id` |
| `profiles_insert_own` | INSERT | authenticated | `auth.uid() = id` |
| `profiles_insert_service` | INSERT | service_role | `true` |

---

### 2. plans

**Purpose:** Plan catalog (pricing tiers). Public read access.
**Created:** Migration 001 | **Modified:** 005, 015, 020, 029

| Column | Type | Nullable | Default | Constraints | Notes |
|--------|------|----------|---------|-------------|-------|
| `id` | `text` | NO | - | PK | Plan identifier (e.g., `smartlic_pro`) |
| `name` | `text` | NO | - | - | Display name |
| `description` | `text` | YES | - | - | Plan description |
| `max_searches` | `int` | YES | - | - | null = unlimited |
| `price_brl` | `numeric(10,2)` | NO | `0` | - | Monthly price in BRL |
| `duration_days` | `int` | YES | - | - | null = perpetual |
| `stripe_price_id` | `text` | YES | - | - | Legacy default Stripe price ID |
| `stripe_price_id_monthly` | `text` | YES | - | - | Monthly Stripe price ID |
| `stripe_price_id_annual` | `text` | YES | - | - | Annual Stripe price ID |
| `stripe_price_id_semiannual` | `text` | YES | - | - | Semiannual Stripe price ID |
| `is_active` | `boolean` | NO | `true` | - | Whether plan is available |
| `created_at` | `timestamptz` | NO | `now()` | - | - |
| `updated_at` | `timestamptz` | NO | `now()` | - | Auto-updated by trigger |

**Active Plans (as of migration 029):**
| Plan ID | Name | Price (BRL) | Max Searches | Status |
|---------|------|-------------|--------------|--------|
| `free_trial` | Gratuito | 0 | 3 | via `free` (deactivated, mapped to free_trial) |
| `smartlic_pro` | SmartLic Pro | 397.00 | 1,000 | Active |
| `master` | Master | 0 | unlimited | Active (internal) |
| `consultor_agil` | Consultor Agil | 297.00 | 50 | Deactivated |
| `maquina` | Maquina | 597.00 | 300 | Deactivated |
| `sala_guerra` | Sala de Guerra | 1,497.00 | 1,000 | Deactivated |

**Indexes:** `plans_pkey` (PK on `id`)

**RLS Policies:**
| Policy Name | Command | USING |
|-------------|---------|-------|
| `plans_select_all` | SELECT | `true` (public catalog) |

---

### 3. user_subscriptions

**Purpose:** Active and historical user subscriptions. Links users to plans with Stripe data.
**Created:** Migration 001 | **Modified:** 008, 016, 017 (trigger removed in 030), 021, 022, 029

| Column | Type | Nullable | Default | Constraints | Notes |
|--------|------|----------|---------|-------------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | PK | - |
| `user_id` | `uuid` | NO | - | FK -> `profiles(id) ON DELETE CASCADE` | - |
| `plan_id` | `text` | NO | - | FK -> `plans(id)` (ON DELETE RESTRICT, intentional) | - |
| `credits_remaining` | `int` | YES | - | - | null = unlimited |
| `starts_at` | `timestamptz` | NO | `now()` | - | Subscription start |
| `expires_at` | `timestamptz` | YES | - | - | null = never expires |
| `stripe_subscription_id` | `text` | YES | - | UNIQUE (partial, WHERE NOT NULL) | Stripe Subscription ID |
| `stripe_customer_id` | `text` | YES | - | - | Stripe Customer ID |
| `is_active` | `boolean` | NO | `true` | - | Active subscription flag |
| `billing_period` | `varchar(10)` | NO | `'monthly'` | CHECK: `IN ('monthly','semiannual','annual')` | Billing cycle |
| `annual_benefits` | `jsonb` | NO | `'{}'::jsonb` | - | Annual-exclusive features |
| `subscription_status` | `text` | YES | - | - | **Note:** Used in webhook code but no explicit migration creating this column |
| `created_at` | `timestamptz` | NO | `now()` | - | - |
| `updated_at` | `timestamptz` | NO | `now()` | - | Auto-updated by trigger |

**Indexes:**
| Index Name | Columns | Type | Partial |
|------------|---------|------|---------|
| `user_subscriptions_pkey` | `id` | PK | No |
| `idx_user_subscriptions_user` | `user_id` | btree | No |
| `idx_user_subscriptions_active` | `(user_id, is_active)` | btree | `WHERE is_active = true` |
| `idx_user_subscriptions_billing` | `(user_id, billing_period, is_active)` | btree | `WHERE is_active = true` |
| `idx_user_subscriptions_stripe_sub_id` | `stripe_subscription_id` | UNIQUE btree | `WHERE stripe_subscription_id IS NOT NULL` |
| `idx_user_subscriptions_customer_id` | `stripe_customer_id` | btree | `WHERE stripe_customer_id IS NOT NULL` |

**RLS Policies:**
| Policy Name | Command | Role | USING |
|-------------|---------|------|-------|
| `subscriptions_select_own` | SELECT | public | `auth.uid() = user_id` |
| `Service role can manage subscriptions` | ALL | service_role | `true` |

---

### 4. plan_features

**Purpose:** Billing-period-specific feature flags for subscription plans.
**Created:** Migration 009 | **Modified:** 029

| Column | Type | Nullable | Default | Constraints | Notes |
|--------|------|----------|---------|-------------|-------|
| `id` | `serial` | NO | auto-increment | PK | - |
| `plan_id` | `text` | NO | - | FK -> `plans(id) ON DELETE CASCADE` | - |
| `billing_period` | `varchar(10)` | NO | - | CHECK: `IN ('monthly','semiannual','annual')` | - |
| `feature_key` | `varchar(100)` | NO | - | - | Feature identifier |
| `enabled` | `boolean` | NO | `true` | - | - |
| `metadata` | `jsonb` | YES | `'{}'::jsonb` | - | Feature-specific config |
| `created_at` | `timestamptz` | NO | `NOW()` | - | - |
| `updated_at` | `timestamptz` | NO | `NOW()` | - | Auto-updated by trigger |

**Unique constraint:** `(plan_id, billing_period, feature_key)`

**Indexes:**
| Index Name | Columns | Partial |
|------------|---------|---------|
| `idx_plan_features_lookup` | `(plan_id, billing_period, enabled)` | `WHERE enabled = true` |

**RLS Policies:**
| Policy Name | Command | USING |
|-------------|---------|-------|
| `plan_features_select_all` | SELECT | `true` (public catalog) |

---

### 5. plan_billing_periods

**Purpose:** Multi-period pricing for plans (monthly/semiannual/annual with discounts).
**Created:** Migration 029

| Column | Type | Nullable | Default | Constraints | Notes |
|--------|------|----------|---------|-------------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | PK | - |
| `plan_id` | `text` | NO | - | FK -> `plans(id) ON DELETE CASCADE` | - |
| `billing_period` | `text` | NO | - | CHECK: `IN ('monthly','semiannual','annual')` | - |
| `price_cents` | `integer` | NO | - | - | Price in centavos |
| `discount_percent` | `integer` | YES | `0` | - | Discount percentage |
| `stripe_price_id` | `text` | YES | - | - | Stripe Price ID |
| `created_at` | `timestamptz` | YES | `NOW()` | - | - |

**Unique constraint:** `(plan_id, billing_period)`

**RLS Policies:**
| Policy Name | Command | Role | USING |
|-------------|---------|------|-------|
| `plan_billing_periods_public_read` | SELECT | authenticated, anon | `true` |
| `plan_billing_periods_service_all` | ALL | service_role | `true` |

---

### 6. monthly_quota

**Purpose:** Tracks monthly search quota usage per user (lazy reset by month_year key).
**Created:** Migration 002 | **Modified:** 016, 018

| Column | Type | Nullable | Default | Constraints | Notes |
|--------|------|----------|---------|-------------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | PK | - |
| `user_id` | `uuid` | NO | - | FK -> `profiles(id) ON DELETE CASCADE` | Standardized in mig. 018 |
| `month_year` | `varchar(7)` | NO | - | UNIQUE with `user_id` | Format: "YYYY-MM" |
| `searches_count` | `int` | NO | `0` | - | Searches this month |
| `created_at` | `timestamptz` | NO | `now()` | - | - |
| `updated_at` | `timestamptz` | NO | `now()` | - | - |

**Unique constraint:** `(user_id, month_year)`

**Indexes:**
| Index Name | Columns |
|------------|---------|
| `idx_monthly_quota_user_month` | `(user_id, month_year)` |

**RLS Policies:**
| Policy Name | Command | Role | USING |
|-------------|---------|------|-------|
| `Users can view own quota` | SELECT | public | `auth.uid() = user_id` |
| `Service role can manage quota` | ALL | service_role | `true` |

**Retention:** 24 months via pg_cron (`cleanup-monthly-quota`, 1st of month at 2AM UTC)

---

### 7. search_sessions

**Purpose:** Search history per user. Records every search attempt with lifecycle tracking.
**Created:** Migration 001 | **Modified:** 006b, 20260220120000, 20260221100000, backend/010

| Column | Type | Nullable | Default | Constraints | Notes |
|--------|------|----------|---------|-------------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | PK | - |
| `user_id` | `uuid` | NO | - | FK -> `profiles(id) ON DELETE CASCADE` | - |
| `search_id` | `uuid` | YES | `NULL` | - | Links to SSE progress tracker |
| `sectors` | `text[]` | NO | - | - | Searched sectors (sorted) |
| `ufs` | `text[]` | NO | - | - | Searched states (sorted) |
| `data_inicial` | `date` | NO | - | - | Search start date |
| `data_final` | `date` | NO | - | - | Search end date |
| `custom_keywords` | `text[]` | YES | - | - | User-provided keywords |
| `total_raw` | `int` | NO | `0` | - | Raw results before filter |
| `total_filtered` | `int` | NO | `0` | - | Filtered results |
| `valor_total` | `numeric(14,2)` | YES | `0` | - | Total estimated value |
| `resumo_executivo` | `text` | YES | - | - | AI executive summary |
| `destaques` | `text[]` | YES | - | - | Key highlights |
| `excel_storage_path` | `text` | YES | - | - | Supabase Storage path |
| `status` | `text` | NO | `'created'` | CHECK: `IN ('created','processing','completed','failed','timed_out','cancelled')` | Session lifecycle |
| `error_message` | `text` | YES | - | - | Human-readable error |
| `error_code` | `text` | YES | - | - | Machine-readable error code |
| `started_at` | `timestamptz` | NO | `now()` | - | When search initiated |
| `completed_at` | `timestamptz` | YES | - | - | When processing finished |
| `duration_ms` | `integer` | YES | - | - | Total processing time |
| `pipeline_stage` | `text` | YES | - | - | Last pipeline stage reached |
| `raw_count` | `integer` | YES | `0` | - | Items fetched before filter |
| `response_state` | `text` | YES | - | - | Data quality: live, cached, degraded |
| `failed_ufs` | `text[]` | YES | - | - | UFs that failed to fetch |
| `created_at` | `timestamptz` | NO | `now()` | - | - |

**Indexes:**
| Index Name | Columns | Partial |
|------------|---------|---------|
| `idx_search_sessions_user` | `user_id` | No |
| `idx_search_sessions_created` | `(user_id, created_at DESC)` | No |
| `idx_search_sessions_search_id` | `search_id` | `WHERE search_id IS NOT NULL` |
| `idx_search_sessions_status` | `status` | `WHERE status IN ('created','processing')` |
| `idx_search_sessions_inflight` | `(status, started_at)` | `WHERE status IN ('created','processing')` |

**RLS Policies:**
| Policy Name | Command | Role | USING |
|-------------|---------|------|-------|
| `sessions_select_own` | SELECT | public | `auth.uid() = user_id` |
| `sessions_insert_own` | INSERT | public | `auth.uid() = user_id` |
| `Service role can manage search sessions` | ALL | service_role | `true` |

---

### 8. search_results_cache

**Purpose:** Persistent L2 cache of search results per user. "Never Empty-Handed" resilience.
**Created:** Migration 026 | **Modified:** 027, 027b, 031, 032, 033, 20260223100000, 20260224200000

| Column | Type | Nullable | Default | Constraints | Notes |
|--------|------|----------|---------|-------------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | PK | - |
| `user_id` | `uuid` | NO | - | FK -> `profiles(id) ON DELETE CASCADE` | Standardized in mig. 20260224200000 |
| `params_hash` | `text` | NO | - | UNIQUE with `user_id` | Per-user search hash |
| `params_hash_global` | `text` | YES | - | - | Cross-user search hash for cache sharing |
| `search_params` | `jsonb` | NO | - | - | Snapshot of search parameters |
| `results` | `jsonb` | NO | - | - | Cached search results |
| `total_results` | `integer` | NO | `0` | - | Count of results |
| `sources_json` | `jsonb` | NO | `'["pncp"]'::jsonb` | - | Data sources that contributed |
| `fetched_at` | `timestamptz` | NO | `now()` | - | When live fetch occurred |
| `priority` | `text` | NO | `'cold'` | - | hot/warm/cold priority tier |
| `access_count` | `integer` | NO | `0` | - | Number of cache hits |
| `last_accessed_at` | `timestamptz` | YES | - | - | Last cache hit time |
| `last_success_at` | `timestamptz` | YES | - | - | Last successful fetch |
| `last_attempt_at` | `timestamptz` | YES | - | - | Last fetch attempt |
| `fail_streak` | `integer` | NO | `0` | - | Consecutive failure count |
| `degraded_until` | `timestamptz` | YES | - | - | Cache degradation expiry |
| `coverage` | `jsonb` | YES | - | - | Per-source coverage details |
| `fetch_duration_ms` | `integer` | YES | - | - | Fetch time in milliseconds |
| `created_at` | `timestamptz` | NO | `now()` | - | - |

**Unique constraint:** `(user_id, params_hash)`

**Indexes:**
| Index Name | Columns | Partial |
|------------|---------|---------|
| `idx_search_cache_user` | `(user_id, created_at DESC)` | No |
| `idx_search_cache_params_hash` | `params_hash` | No |
| `idx_search_cache_fetched_at` | `fetched_at` | No |
| `idx_search_cache_degraded` | `degraded_until` | `WHERE degraded_until IS NOT NULL` |
| `idx_search_cache_priority` | `(user_id, priority, last_accessed_at)` | No |
| `idx_search_cache_global_hash` | `(params_hash_global, created_at DESC)` | No |

**RLS Policies:**
| Policy Name | Command | Role | USING |
|-------------|---------|------|-------|
| `Users can read own search cache` | SELECT | public | `auth.uid() = user_id` |
| `Service role full access on search_results_cache` | ALL | service_role | `true` |

**Trigger:** `trg_cleanup_search_cache` -- Smart eviction (max 10 per user, cold-first)

---

### 9. search_state_transitions

**Purpose:** Audit trail for search state machine transitions. Fire-and-forget inserts.
**Created:** Migration 20260221100002

| Column | Type | Nullable | Default | Constraints | Notes |
|--------|------|----------|---------|-------------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | PK | - |
| `search_id` | `uuid` | NO | - | - | Correlates with `search_sessions.search_id` (no FK) |
| `from_state` | `text` | YES | - | - | Previous state (NULL for initial) |
| `to_state` | `text` | NO | - | - | New state |
| `stage` | `text` | YES | - | - | Pipeline stage |
| `details` | `jsonb` | YES | `'{}'` | - | Transition metadata |
| `duration_since_previous_ms` | `integer` | YES | - | - | Time since previous transition |
| `created_at` | `timestamptz` | NO | `now()` | - | - |

**Indexes:**
| Index Name | Columns |
|------------|---------|
| `idx_state_transitions_search_id` | `(search_id, created_at ASC)` |
| `idx_state_transitions_to_state` | `(to_state, created_at)` |

**RLS Policies:**
| Policy Name | Command | USING |
|-------------|---------|-------|
| `Users can read own transitions` | SELECT | `search_id IN (SELECT search_id FROM search_sessions WHERE user_id = auth.uid())` |
| `Service role can insert transitions` | INSERT | `true` (service role INSERT policy without explicit TO clause) |

**Note:** `search_id` is NOT a foreign key -- designed for fire-and-forget to never block the pipeline.

---

### 10. pipeline_items

**Purpose:** Opportunity pipeline (kanban stages) for tracking bids.
**Created:** Migration 025 | **Modified:** 027

| Column | Type | Nullable | Default | Constraints | Notes |
|--------|------|----------|---------|-------------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | PK | - |
| `user_id` | `uuid` | NO | - | FK -> `auth.users(id) ON DELETE CASCADE` | **Note:** Still references auth.users, not standardized to profiles |
| `pncp_id` | `text` | NO | - | - | PNCP bid identifier (snapshot) |
| `objeto` | `text` | NO | - | - | Bid description |
| `orgao` | `text` | YES | - | - | Government agency |
| `uf` | `text` | YES | - | - | State code |
| `valor_estimado` | `numeric` | YES | - | - | Estimated value |
| `data_encerramento` | `timestamptz` | YES | - | - | Bid closing date |
| `link_pncp` | `text` | YES | - | - | PNCP link |
| `stage` | `text` | NO | `'descoberta'` | CHECK: `IN ('descoberta','analise','preparando','enviada','resultado')` | Pipeline stage |
| `notes` | `text` | YES | - | - | User notes |
| `created_at` | `timestamptz` | NO | `now()` | - | - |
| `updated_at` | `timestamptz` | NO | `now()` | - | Auto-updated by trigger |

**Unique constraint:** `(user_id, pncp_id)` -- prevent duplicate items per user

**Indexes:**
| Index Name | Columns | Partial |
|------------|---------|---------|
| `idx_pipeline_user_stage` | `(user_id, stage)` | No |
| `idx_pipeline_encerramento` | `data_encerramento` | `WHERE stage NOT IN ('enviada','resultado')` |
| `idx_pipeline_user_created` | `(user_id, created_at DESC)` | No |

**RLS Policies:**
| Policy Name | Command | Role | USING |
|-------------|---------|------|-------|
| `Users can view own pipeline items` | SELECT | public | `auth.uid() = user_id` |
| `Users can insert own pipeline items` | INSERT | public | `auth.uid() = user_id` |
| `Users can update own pipeline items` | UPDATE | public | `auth.uid() = user_id` (both USING and WITH CHECK) |
| `Users can delete own pipeline items` | DELETE | public | `auth.uid() = user_id` |
| `Service role full access on pipeline_items` | ALL | service_role | `true` |

---

### 11. conversations

**Purpose:** InMail messaging system -- support conversations between users and admins.
**Created:** Migration 012

| Column | Type | Nullable | Default | Constraints | Notes |
|--------|------|----------|---------|-------------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | PK | - |
| `user_id` | `uuid` | NO | - | FK -> `profiles(id) ON DELETE CASCADE` | - |
| `subject` | `text` | NO | - | CHECK: `char_length(subject) <= 200` | - |
| `category` | `text` | NO | - | CHECK: `IN ('suporte','sugestao','funcionalidade','bug','outro')` | - |
| `status` | `text` | NO | `'aberto'` | CHECK: `IN ('aberto','respondido','resolvido')` | - |
| `last_message_at` | `timestamptz` | NO | `now()` | - | Auto-updated by trigger |
| `created_at` | `timestamptz` | NO | `now()` | - | - |
| `updated_at` | `timestamptz` | NO | `now()` | - | - |

**Indexes:**
| Index Name | Columns |
|------------|---------|
| `idx_conversations_user_id` | `user_id` |
| `idx_conversations_status` | `status` |
| `idx_conversations_last_message` | `last_message_at DESC` |

**RLS Policies:**
| Policy Name | Command | USING |
|-------------|---------|-------|
| `conversations_select_own` | SELECT | `auth.uid() = user_id OR is_admin(auth.uid())` |
| `conversations_insert_own` | INSERT | `auth.uid() = user_id` |
| `conversations_update_admin` | UPDATE | `is_admin(auth.uid())` |

---

### 12. messages

**Purpose:** Individual messages within conversations.
**Created:** Migration 012

| Column | Type | Nullable | Default | Constraints | Notes |
|--------|------|----------|---------|-------------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | PK | - |
| `conversation_id` | `uuid` | NO | - | FK -> `conversations(id) ON DELETE CASCADE` | - |
| `sender_id` | `uuid` | NO | - | FK -> `profiles(id) ON DELETE CASCADE` | - |
| `body` | `text` | NO | - | CHECK: `char_length(body) >= 1 AND char_length(body) <= 5000` | - |
| `is_admin_reply` | `boolean` | NO | `false` | - | - |
| `read_by_user` | `boolean` | NO | `false` | - | - |
| `read_by_admin` | `boolean` | NO | `false` | - | - |
| `created_at` | `timestamptz` | NO | `now()` | - | - |

**Indexes:**
| Index Name | Columns | Partial |
|------------|---------|---------|
| `idx_messages_conversation` | `(conversation_id, created_at)` | No |
| `idx_messages_unread_by_user` | `conversation_id` | `WHERE is_admin_reply = true AND read_by_user = false` |
| `idx_messages_unread_by_admin` | `conversation_id` | `WHERE is_admin_reply = false AND read_by_admin = false` |

**RLS Policies:**
| Policy Name | Command | USING |
|-------------|---------|-------|
| `messages_select` | SELECT | Owns conversation OR is admin |
| `messages_insert_user` | INSERT | `auth.uid() = sender_id` AND owns conversation or is admin |
| `messages_update_read` | UPDATE | Owns conversation OR is admin |

---

### 13. stripe_webhook_events

**Purpose:** Idempotency log for Stripe webhook events. Prevents duplicate processing.
**Created:** Migration 010 | **Modified:** 016, 028

| Column | Type | Nullable | Default | Constraints | Notes |
|--------|------|----------|---------|-------------|-------|
| `id` | `varchar(255)` | NO | - | PK; CHECK: `id ~ '^evt_'` | Stripe event ID |
| `type` | `varchar(100)` | NO | - | - | Stripe event type |
| `processed_at` | `timestamptz` | NO | `NOW()` | - | - |
| `payload` | `jsonb` | YES | - | - | Full Stripe event object |

**Indexes:**
| Index Name | Columns |
|------------|---------|
| `idx_webhook_events_type` | `(type, processed_at)` |
| `idx_webhook_events_recent` | `processed_at DESC` |

**RLS Policies:**
| Policy Name | Command | Role | USING |
|-------------|---------|------|-------|
| `webhook_events_insert_service` | INSERT | service_role | `true` |
| `webhook_events_select_admin` | SELECT | authenticated | `is_admin = true` |
| `webhook_events_service_role_select` | SELECT | service_role | `true` |

**Retention:** 90 days via pg_cron (`cleanup-webhook-events`, daily at 3AM UTC)

---

### 14. user_oauth_tokens

**Purpose:** Encrypted OAuth 2.0 tokens for Google Sheets integration.
**Created:** Migration 013 | **Modified:** 018, 022

| Column | Type | Nullable | Default | Constraints | Notes |
|--------|------|----------|---------|-------------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | PK | - |
| `user_id` | `uuid` | NO | - | FK -> `profiles(id) ON DELETE CASCADE` | Standardized in mig. 018 |
| `provider` | `varchar(50)` | NO | - | CHECK: `IN ('google','microsoft','dropbox')` | - |
| `access_token` | `text` | NO | - | - | AES-256 encrypted |
| `refresh_token` | `text` | YES | - | - | AES-256 encrypted |
| `expires_at` | `timestamptz` | NO | - | - | Token expiration |
| `scope` | `text` | NO | - | - | OAuth scopes |
| `created_at` | `timestamptz` | YES | `NOW()` | - | - |
| `updated_at` | `timestamptz` | YES | `NOW()` | - | - |

**Unique constraint:** `(user_id, provider)`

**Indexes:**
| Index Name | Columns |
|------------|---------|
| `idx_user_oauth_tokens_user_id` | `user_id` |
| `idx_user_oauth_tokens_expires_at` | `expires_at` |

**RLS Policies:**
| Policy Name | Command | Role | USING |
|-------------|---------|------|-------|
| `Users can view own OAuth tokens` | SELECT | public | `auth.uid() = user_id` |
| `Users can update own OAuth tokens` | UPDATE | public | `auth.uid() = user_id` |
| `Users can delete own OAuth tokens` | DELETE | public | `auth.uid() = user_id` |
| `Service role can manage all OAuth tokens` | ALL | service_role | `true` |

---

### 15. google_sheets_exports

**Purpose:** Tracks Google Sheets export history for audit and "re-open last export".
**Created:** Migration 014 | **Modified:** 018

| Column | Type | Nullable | Default | Constraints | Notes |
|--------|------|----------|---------|-------------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | PK | - |
| `user_id` | `uuid` | NO | - | FK -> `profiles(id) ON DELETE CASCADE` | Standardized in mig. 018 |
| `spreadsheet_id` | `varchar(255)` | NO | - | - | Google Sheets ID |
| `spreadsheet_url` | `text` | NO | - | - | Full shareable URL |
| `search_params` | `jsonb` | NO | - | - | Snapshot of search parameters |
| `total_rows` | `int` | NO | - | CHECK: `total_rows >= 0` | Rows exported |
| `created_at` | `timestamptz` | YES | `NOW()` | - | - |
| `last_updated_at` | `timestamptz` | YES | `NOW()` | - | - |

**Indexes:**
| Index Name | Columns | Type |
|------------|---------|------|
| `idx_google_sheets_exports_user_id` | `user_id` | btree |
| `idx_google_sheets_exports_created_at` | `created_at DESC` | btree |
| `idx_google_sheets_exports_spreadsheet_id` | `spreadsheet_id` | btree |
| `idx_google_sheets_exports_search_params` | `search_params` | GIN |

**RLS Policies:**
| Policy Name | Command | Role | USING |
|-------------|---------|------|-------|
| `Users can view own Google Sheets exports` | SELECT | public | `auth.uid() = user_id` |
| `Users can create Google Sheets exports` | INSERT | public | `auth.uid() = user_id` |
| `Users can update own Google Sheets exports` | UPDATE | public | `auth.uid() = user_id` |
| `Service role can manage all Google Sheets exports` | ALL | service_role | `true` |

---

### 16. audit_events

**Purpose:** Persistent security audit log. All PII stored as SHA-256 hashes (LGPD/GDPR).
**Created:** Migration 023

| Column | Type | Nullable | Default | Constraints | Notes |
|--------|------|----------|---------|-------------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | PK | - |
| `timestamp` | `timestamptz` | NO | `now()` | - | - |
| `event_type` | `text` | NO | - | - | auth.login, admin.plan_assign, etc. |
| `actor_id_hash` | `text` | YES | - | - | SHA-256 hash of user ID (16 hex chars) |
| `target_id_hash` | `text` | YES | - | - | SHA-256 hash of target user ID |
| `details` | `jsonb` | YES | - | - | Structured metadata (sanitized) |
| `ip_hash` | `text` | YES | - | - | SHA-256 hash of client IP |

**Indexes:**
| Index Name | Columns | Partial |
|------------|---------|---------|
| `idx_audit_events_event_type` | `event_type` | No |
| `idx_audit_events_timestamp` | `timestamp` | No |
| `idx_audit_events_actor` | `actor_id_hash` | `WHERE actor_id_hash IS NOT NULL` |
| `idx_audit_events_type_timestamp` | `(event_type, timestamp DESC)` | No |

**RLS Policies:**
| Policy Name | Command | Role | USING |
|-------------|---------|------|-------|
| `Service role can manage audit events` | ALL | service_role | `true` |
| `Admins can read audit events` | SELECT | public | `is_admin = true` |

**Retention:** 12 months via pg_cron (`cleanup-audit-events`, 1st of month at 4AM UTC)

---

### 17. classification_feedback

**Purpose:** User feedback on search result relevance for continuous improvement.
**Created:** Backend migration 006

| Column | Type | Nullable | Default | Constraints | Notes |
|--------|------|----------|---------|-------------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | PK | - |
| `user_id` | `uuid` | NO | - | FK -> `auth.users(id)` (no cascade) | **Note:** Not standardized to profiles |
| `search_id` | `uuid` | NO | - | - | - |
| `bid_id` | `text` | NO | - | - | - |
| `setor_id` | `text` | NO | - | - | - |
| `user_verdict` | `text` | NO | - | CHECK: `IN ('false_positive','false_negative','correct')` | - |
| `reason` | `text` | YES | - | - | - |
| `category` | `text` | YES | - | CHECK: `IN ('wrong_sector','irrelevant_modality','too_small','too_large','closed','other')` | - |
| `bid_objeto` | `text` | YES | - | - | Snapshot of bid description |
| `bid_valor` | `decimal` | YES | - | - | Snapshot of bid value |
| `bid_uf` | `text` | YES | - | - | Snapshot of bid state |
| `confidence_score` | `integer` | YES | - | - | Relevance confidence |
| `relevance_source` | `text` | YES | - | - | keyword, llm_standard, etc. |
| `created_at` | `timestamptz` | YES | `now()` | - | - |

**Unique constraint:** `(user_id, search_id, bid_id)`

**Indexes:**
| Index Name | Columns |
|------------|---------|
| `idx_feedback_sector_verdict` | `(setor_id, user_verdict, created_at)` |
| `idx_feedback_user_created` | `(user_id, created_at)` |

**RLS Policies:**
| Policy Name | Command | USING |
|-------------|---------|-------|
| `feedback_insert_own` | INSERT | `auth.uid() = user_id` |
| `feedback_select_own` | SELECT | `auth.uid() = user_id` |
| `feedback_update_own` | UPDATE | `auth.uid() = user_id` |
| `feedback_delete_own` | DELETE | `auth.uid() = user_id` |
| `feedback_admin_all` | ALL | `auth.role() = 'service_role'` |

---

### 18. trial_email_log

**Purpose:** Tracks trial reminder emails sent to prevent duplicate delivery.
**Created:** Migration 20260224100000

| Column | Type | Nullable | Default | Constraints | Notes |
|--------|------|----------|---------|-------------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | PK | - |
| `user_id` | `uuid` | NO | - | FK -> `auth.users(id) ON DELETE CASCADE` | **Note:** Not standardized to profiles |
| `email_type` | `text` | NO | - | - | midpoint, expiring, last_day, expired |
| `sent_at` | `timestamptz` | NO | `now()` | - | - |

**Unique constraint:** `(user_id, email_type)`

**Indexes:**
| Index Name | Columns |
|------------|---------|
| `idx_trial_email_log_user_id` | `user_id` |

**RLS Policies:** RLS ENABLED but **no user-facing policies**. Only service_role (which bypasses RLS) can access.

---

## Functions

### Database Functions

| # | Function Name | Parameters | Returns | Security | Created In |
|---|---------------|------------|---------|----------|------------|
| 1 | `handle_new_user()` | trigger function | trigger | SECURITY DEFINER | 001, updated in 007, 016, 024, 027, 20260224000000 |
| 2 | `update_updated_at()` | trigger function | trigger | - | 001 |
| 3 | `increment_quota_atomic()` | `(p_user_id UUID, p_month_year VARCHAR(7), p_max_quota INT)` | TABLE(new_count, was_at_limit, previous_count) | - | 003 |
| 4 | `check_and_increment_quota()` | `(p_user_id UUID, p_month_year VARCHAR(7), p_max_quota INT)` | TABLE(allowed, new_count, previous_count, quota_remaining) | - | 003 |
| 5 | `get_user_billing_period()` | `(p_user_id UUID)` | VARCHAR(10) | SECURITY DEFINER | 011 |
| 6 | `user_has_feature()` | `(p_user_id UUID, p_feature_key VARCHAR(100))` | BOOLEAN | SECURITY DEFINER | 011 |
| 7 | `get_user_features()` | `(p_user_id UUID)` | TEXT[] | SECURITY DEFINER | 011 |
| 8 | `update_conversation_last_message()` | trigger function | trigger | - | 012 |
| 9 | `get_conversations_with_unread_count()` | `(p_user_id UUID, p_is_admin BOOL, p_status TEXT, p_limit INT, p_offset INT)` | TABLE(...) | SECURITY DEFINER | 019 |
| 10 | `get_analytics_summary()` | `(p_user_id UUID, p_start_date TIMESTAMPTZ, p_end_date TIMESTAMPTZ)` | TABLE(...) | SECURITY DEFINER | 019 |
| 11 | `update_pipeline_updated_at()` | trigger function | trigger | - | 025 |
| 12 | `cleanup_search_cache_per_user()` | trigger function | trigger | SECURITY DEFINER | 026, updated in 032 |
| 13 | `get_table_columns_simple()` | `(p_table_name TEXT)` | TABLE(column_name TEXT) | SECURITY DEFINER | 20260221100001 |

### Removed Functions

| Function | Removed In | Reason |
|----------|-----------|--------|
| `sync_profile_plan_type()` | Migration 030 | Referenced non-existent `status` column on `user_subscriptions` (dead code) |

---

## Triggers

| # | Trigger Name | Table | Event | Function |
|---|-------------|-------|-------|----------|
| 1 | `on_auth_user_created` | `auth.users` | AFTER INSERT | `handle_new_user()` |
| 2 | `profiles_updated_at` | `profiles` | BEFORE UPDATE | `update_updated_at()` |
| 3 | `plans_updated_at` | `plans` | BEFORE UPDATE | `update_updated_at()` |
| 4 | `plan_features_updated_at` | `plan_features` | BEFORE UPDATE | `update_updated_at()` |
| 5 | `user_subscriptions_updated_at` | `user_subscriptions` | BEFORE UPDATE | `update_updated_at()` |
| 6 | `trg_update_conversation_last_message` | `messages` | AFTER INSERT | `update_conversation_last_message()` |
| 7 | `tr_pipeline_items_updated_at` | `pipeline_items` | BEFORE UPDATE | `update_pipeline_updated_at()` |
| 8 | `trg_cleanup_search_cache` | `search_results_cache` | AFTER INSERT | `cleanup_search_cache_per_user()` |

### Removed Triggers

| Trigger | Table | Removed In | Reason |
|---------|-------|-----------|--------|
| `trg_sync_profile_plan_type` | `user_subscriptions` | Migration 030 | Dead code (referenced non-existent column) |

---

## Extensions

| Extension | Purpose | Created In |
|-----------|---------|------------|
| `pg_trgm` | Trigram indexes for fuzzy text search (ILIKE on profiles.email) | Migration 016 |
| `pg_cron` | Scheduled retention cleanup jobs | Migration 022 |

---

## Row-Level Security Summary

| Table | RLS Enabled | User SELECT | User INSERT | User UPDATE | User DELETE | Service Role | Admin |
|-------|-------------|-------------|-------------|-------------|-------------|--------------|-------|
| `profiles` | Yes | Own only | Own only | Own only | -- | INSERT only | -- |
| `plans` | Yes | All (public) | -- | -- | -- | -- | -- |
| `user_subscriptions` | Yes | Own only | -- | -- | -- | ALL | -- |
| `plan_features` | Yes | All (public) | -- | -- | -- | -- | -- |
| `plan_billing_periods` | Yes | All (public) | -- | -- | -- | ALL | -- |
| `monthly_quota` | Yes | Own only | -- | -- | -- | ALL | -- |
| `search_sessions` | Yes | Own only | Own only | -- | -- | ALL | -- |
| `search_results_cache` | Yes | Own only | -- | -- | -- | ALL | -- |
| `search_state_transitions` | Yes | Own (via join) | -- | -- | -- | INSERT | -- |
| `pipeline_items` | Yes | Own only | Own only | Own only | Own only | ALL | -- |
| `conversations` | Yes | Own + admin | Own only | Admin only | -- | -- | UPDATE |
| `messages` | Yes | Own conv + admin | Own conv + admin | Own conv + admin | -- | -- | Via conv |
| `stripe_webhook_events` | Yes | -- | -- | -- | -- | INSERT + SELECT | SELECT |
| `user_oauth_tokens` | Yes | Own only | -- | Own only | Own only | ALL | -- |
| `google_sheets_exports` | Yes | Own only | Own only | Own only | -- | ALL | -- |
| `audit_events` | Yes | -- | -- | -- | -- | ALL | SELECT |
| `classification_feedback` | Yes | Own only | Own only | Own only | Own only | ALL | -- |
| `trial_email_log` | Yes | -- | -- | -- | -- | (bypasses RLS) | -- |

---

## Index Catalog

### Total: 49 indexes across 18 tables

| Table | Index Count | Notable Indexes |
|-------|-------------|-----------------|
| `profiles` | 7 | trigram (GIN) on email, partial unique on phone and email |
| `plans` | 1 | PK only |
| `user_subscriptions` | 6 | Unique partial on stripe_subscription_id |
| `plan_features` | 1 + PK | Partial on enabled features |
| `plan_billing_periods` | 1 + PK | - |
| `monthly_quota` | 1 + PK | Composite on (user_id, month_year) |
| `search_sessions` | 5 | Partial on in-flight status |
| `search_results_cache` | 6 | Priority, degraded, global hash |
| `search_state_transitions` | 2 | Timeline by search_id |
| `pipeline_items` | 3 | Partial on non-terminal stages |
| `conversations` | 3 | Last message DESC |
| `messages` | 3 | Partial unread indexes (efficient badge counts) |
| `stripe_webhook_events` | 2 | Recent events DESC |
| `user_oauth_tokens` | 2 | Expires_at for refresh jobs |
| `google_sheets_exports` | 4 | GIN on JSONB search_params |
| `audit_events` | 4 | Composite (event_type, timestamp DESC) |
| `classification_feedback` | 2 | Sector+verdict composite |
| `trial_email_log` | 1 | user_id for lookups |

---

## Entity-Relationship Diagram

```
auth.users (Supabase managed)
    |
    | 1:1 (PK/FK on id, ON DELETE CASCADE)
    v
+--profiles--+
|  id (PK)   |---< user_subscriptions (user_id FK)
|  email     |---< monthly_quota (user_id FK)
|  plan_type |---< search_sessions (user_id FK)
|  is_admin  |---< search_results_cache (user_id FK)
|  ...       |---< conversations (user_id FK)
+------------+---< messages (sender_id FK)
             |---< user_oauth_tokens (user_id FK)
             |---< google_sheets_exports (user_id FK)

auth.users (direct FK, not via profiles)
    |---< pipeline_items (user_id FK)
    |---< classification_feedback (user_id FK, NO CASCADE)
    |---< trial_email_log (user_id FK)

+--plans--+
|  id (PK)|---< user_subscriptions (plan_id FK, ON DELETE RESTRICT)
|  ...    |---< plan_features (plan_id FK, ON DELETE CASCADE)
+---------+---< plan_billing_periods (plan_id FK, ON DELETE CASCADE)

conversations ---< messages (conversation_id FK, ON DELETE CASCADE)

search_sessions ...... search_state_transitions (search_id correlation, NO FK)
```

---

## pg_cron Scheduled Jobs

| Job Name | Schedule | SQL | Retention |
|----------|----------|-----|-----------|
| `cleanup-monthly-quota` | `0 2 1 * *` (1st of month, 2AM UTC) | `DELETE FROM monthly_quota WHERE created_at < NOW() - INTERVAL '24 months'` | 24 months |
| `cleanup-webhook-events` | `0 3 * * *` (daily, 3AM UTC) | `DELETE FROM stripe_webhook_events WHERE processed_at < NOW() - INTERVAL '90 days'` | 90 days |
| `cleanup-audit-events` | `0 4 1 * *` (1st of month, 4AM UTC) | `DELETE FROM audit_events WHERE timestamp < NOW() - INTERVAL '12 months'` | 12 months |

---

## Migration History

| Migration | Date | Description |
|-----------|------|-------------|
| 001 | 2026-02 | profiles, plans, user_subscriptions, search_sessions (foundation) |
| 002 | 2026-02-03 | monthly_quota table |
| 003 | 2026-02-04 | Atomic quota increment functions |
| 004 | 2026-02 | Add is_admin to profiles |
| 005 | 2026-02-05 | New pricing tiers (consultor_agil, maquina, sala_guerra) |
| 006a | 2026-02-06 | Update plan_type CHECK constraint |
| 006b | 2026-02-10 | Service role policy for search_sessions |
| 007 | 2026-02 | WhatsApp consent + sector + phone fields |
| 008 | 2026-02-07 | billing_period + annual_benefits on user_subscriptions |
| 009 | 2026-02-07 | plan_features table |
| 010 | 2026-02 | stripe_webhook_events table |
| 011 | 2026-02-07 | Billing helper functions |
| 012 | 2026-02 | conversations + messages tables |
| 013 | 2026-02 | user_oauth_tokens table |
| 014 | 2026-02 | google_sheets_exports table |
| 015 | 2026-02-10 | Stripe price IDs (monthly/annual) |
| 016 | 2026-02-11 | Security + index fixes (6 items) |
| 017 | 2026-02 | sync_profile_plan_type trigger (removed in 030) |
| 018 | 2026-02 | Standardize FKs to profiles(id) |
| 019 | 2026-02 | RPC performance functions |
| 020 | 2026-02-12 | Tighten plan_type constraint + INSERT policy |
| 021 | 2026-02-12 | updated_at on user_subscriptions |
| 022 | 2026-02-12 | Retention cleanup + pg_cron jobs |
| 023 | 2026-02-13 | audit_events table |
| 024 | 2026-02 | context_data on profiles |
| 025 | 2026-02 | pipeline_items table |
| 026 | 2026-02 | search_results_cache table |
| 027 | 2026-02-15 | Fix plan_type default + RLS hardening |
| 027b | 2026-02 | Cache sources_json + fetched_at (superseded by 033) |
| 028 | 2026-02-15 | Fix stripe_webhook_events RLS |
| 029 | 2026-02-15 | Single plan model (SmartLic Pro) |
| 030 | 2026-02-16 | Remove dead sync trigger |
| 031 | 2026-02 | Cache health metadata |
| 032 | 2026-02 | Cache priority fields (hot/warm/cold) |
| 033 | 2026-02 | Fix missing cache columns |
| 20260220120000 | 2026-02-20 | Add search_id to search_sessions |
| 20260221100000 | 2026-02-21 | Search session lifecycle columns |
| 20260221100001 | 2026-02-21 | get_table_columns_simple RPC |
| 20260221100002 | 2026-02-21 | search_state_transitions table |
| 20260223100000 | 2026-02-23 | params_hash_global for cross-user cache |
| 20260224000000 | 2026-02-24 | Phone + email uniqueness constraints |
| 20260224100000 | 2026-02-24 | trial_email_log table |
| 20260224200000 | 2026-02-24 | Fix cache user FK to profiles |

### Backend-Only Migrations (backend/migrations/)

| Migration | Description |
|-----------|-------------|
| 002 | monthly_quota (duplicate of Supabase 002) |
| 003 | Atomic quota increment (duplicate of Supabase 003) |
| 004 | Google OAuth tokens (duplicate of Supabase 013) |
| 005 | Google Sheets exports (duplicate of Supabase 014) |
| 006 | classification_feedback table |
| 007 | Search session lifecycle (synced as Supabase 20260221100000) |
| 008 | Search state transitions (synced as Supabase 20260221100002) |
| 009 | Add search_id to search_sessions (synced as Supabase 20260220120000) |
| 010 | Normalize session arrays (sort UFs and sectors) |
