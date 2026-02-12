# Database Schema - SmartLic/BidIQ

**Provider:** Supabase (PostgreSQL 17)
**Project ID:** `pncp-poc`
**Project Ref:** `fqqyovlzdzimiwfofdjk`
**Schema Generated:** 2026-02-11

---

## Table of Contents

1. [Overview](#overview)
2. [Entity Relationship Diagram](#entity-relationship-diagram)
3. [Tables](#tables)
   - [profiles](#1-profiles)
   - [plans](#2-plans)
   - [user_subscriptions](#3-user_subscriptions)
   - [search_sessions](#4-search_sessions)
   - [monthly_quota](#5-monthly_quota)
   - [plan_features](#6-plan_features)
   - [stripe_webhook_events](#7-stripe_webhook_events)
   - [conversations](#8-conversations)
   - [messages](#9-messages)
   - [user_oauth_tokens](#10-user_oauth_tokens)
   - [google_sheets_exports](#11-google_sheets_exports)
4. [Functions & Triggers](#functions--triggers)
5. [Indexes](#indexes)
6. [Enums & Constraints](#enums--constraints)
7. [Row Level Security Policies](#row-level-security-policies)
8. [Data Access Patterns](#data-access-patterns)

---

## Overview

SmartLic uses Supabase (hosted PostgreSQL 17) as its primary database. The schema supports:

- **User Management** via Supabase Auth (`auth.users`) with extended profiles
- **Plan-Based Billing** with Stripe integration (monthly/annual subscriptions)
- **Search Quota Tracking** with atomic increment for race condition prevention
- **Search History** for user analytics and session replay
- **Feature Flags** per plan + billing period combination
- **InMail Messaging** for support conversations
- **Google Sheets Integration** with encrypted OAuth token storage
- **Webhook Idempotency** for Stripe event deduplication

**Total Tables:** 11 (in `public` schema) + Supabase `auth.users` (managed)
**Total Migrations:** 15 (numbered 001-015)
**Total RLS Policies:** ~25

---

## Entity Relationship Diagram

```
auth.users (managed by Supabase Auth)
    |
    | 1:1 (trigger: handle_new_user)
    v
profiles
    |
    |--- 1:N ---> user_subscriptions ---> plans
    |--- 1:N ---> search_sessions
    |--- 1:N ---> monthly_quota (via auth.users FK)
    |--- 1:N ---> conversations ---> messages
    |--- 1:N ---> user_oauth_tokens (via auth.users FK)
    |--- 1:N ---> google_sheets_exports (via auth.users FK)

plans
    |--- 1:N ---> user_subscriptions
    |--- 1:N ---> plan_features

stripe_webhook_events (standalone audit table)
```

---

## Tables

### 1. profiles

**Purpose:** Extends `auth.users` with application-specific user data.
**Migration:** `001_profiles_and_sessions.sql`, `004_add_is_admin.sql`, `007_add_whatsapp_consent.sql`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | NO | - | **PK**, FK -> `auth.users(id) ON DELETE CASCADE` |
| `email` | `text` | NO | - | |
| `full_name` | `text` | YES | NULL | |
| `company` | `text` | YES | NULL | |
| `plan_type` | `text` | NO | `'free'` | CHECK: see constraint below |
| `avatar_url` | `text` | YES | NULL | |
| `is_admin` | `boolean` | NO | `false` | Added in migration 004 |
| `sector` | `text` | YES | NULL | Added in migration 007 |
| `phone_whatsapp` | `text` | YES | NULL | CHECK: `^[0-9]{10,11}$` or NULL |
| `whatsapp_consent` | `boolean` | YES | `false` | |
| `whatsapp_consent_at` | `timestamptz` | YES | NULL | LGPD audit trail |
| `created_at` | `timestamptz` | NO | `now()` | |
| `updated_at` | `timestamptz` | NO | `now()` | Auto-updated via trigger |

**CHECK Constraint (`profiles_plan_type_check`):**
```sql
plan_type IN (
  'free', 'avulso', 'pack', 'monthly', 'annual', 'master',
  'free_trial', 'consultor_agil', 'maquina', 'sala_guerra'
)
```

**Indexes:**
| Name | Columns | Type | Condition |
|------|---------|------|-----------|
| `profiles_pkey` | `id` | B-tree (PK) | - |
| `idx_profiles_is_admin` | `is_admin` | B-tree (partial) | `WHERE is_admin = true` |
| `idx_profiles_whatsapp_consent` | `whatsapp_consent` | B-tree (partial) | `WHERE whatsapp_consent = true` |

**Triggers:**
- `profiles_updated_at` -> `update_updated_at()` (BEFORE UPDATE)
- `on_auth_user_created` on `auth.users` -> `handle_new_user()` (AFTER INSERT)

---

### 2. plans

**Purpose:** Plan catalog with pricing and Stripe integration.
**Migration:** `001_profiles_and_sessions.sql`, `005_update_plans_to_new_tiers.sql`, `015_add_stripe_price_ids_monthly_annual.sql`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | `text` | NO | - | **PK** |
| `name` | `text` | NO | - | |
| `description` | `text` | YES | NULL | |
| `max_searches` | `int` | YES | NULL | NULL = unlimited |
| `price_brl` | `numeric(10,2)` | NO | `0` | |
| `duration_days` | `int` | YES | NULL | NULL = perpetual |
| `stripe_price_id` | `text` | YES | NULL | Default Stripe price (monthly) |
| `stripe_price_id_monthly` | `text` | YES | NULL | Added in migration 015 |
| `stripe_price_id_annual` | `text` | YES | NULL | Added in migration 015 |
| `is_active` | `boolean` | NO | `true` | |
| `created_at` | `timestamptz` | NO | `now()` | |

**Seeded Data (active plans after migration 005):**

| id | name | max_searches | price_brl | is_active |
|----|------|-------------|-----------|-----------|
| `free` | Gratuito | 3 | 0.00 | true |
| `consultor_agil` | Consultor Agil | 50 | 297.00 | true |
| `maquina` | Maquina | 300 | 597.00 | true |
| `sala_guerra` | Sala de Guerra | 1000 | 1497.00 | true |
| `master` | Master | NULL (unlimited) | 0.00 | true |
| `pack_5` | Pacote 5 Buscas | 5 | 29.90 | **false** (legacy) |
| `pack_10` | Pacote 10 Buscas | 10 | 49.90 | **false** (legacy) |
| `pack_20` | Pacote 20 Buscas | 20 | 89.90 | **false** (legacy) |
| `monthly` | Mensal Ilimitado | NULL | 149.90 | **false** (legacy) |
| `annual` | Anual Ilimitado | NULL | 1199.90 | **false** (legacy) |

---

### 3. user_subscriptions

**Purpose:** Active and historical subscriptions for each user.
**Migration:** `001_profiles_and_sessions.sql`, `008_add_billing_period.sql`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | NO | `gen_random_uuid()` | **PK** |
| `user_id` | `uuid` | NO | - | FK -> `profiles(id) ON DELETE CASCADE` |
| `plan_id` | `text` | NO | - | FK -> `plans(id) ON DELETE RESTRICT` |
| `credits_remaining` | `int` | YES | NULL | NULL = unlimited |
| `starts_at` | `timestamptz` | NO | `now()` | |
| `expires_at` | `timestamptz` | YES | NULL | NULL = never expires |
| `stripe_subscription_id` | `text` | YES | NULL | UNIQUE (for Stripe integration) |
| `stripe_customer_id` | `text` | YES | NULL | |
| `billing_period` | `varchar(10)` | NO | `'monthly'` | CHECK: `IN ('monthly', 'annual')` |
| `annual_benefits` | `jsonb` | NO | `'{}'` | Added in migration 008 |
| `is_active` | `boolean` | NO | `true` | |
| `created_at` | `timestamptz` | NO | `now()` | |

**Indexes:**
| Name | Columns | Type | Condition |
|------|---------|------|-----------|
| `user_subscriptions_pkey` | `id` | B-tree (PK) | - |
| `idx_user_subscriptions_user` | `user_id` | B-tree | - |
| `idx_user_subscriptions_active` | `user_id, is_active` | B-tree (partial) | `WHERE is_active = true` |
| `idx_user_subscriptions_billing` | `user_id, billing_period, is_active` | B-tree (partial) | `WHERE is_active = true` |

**Notes:**

1. **stripe_subscription_id index:** The `stripe_subscription_id` has a UNIQUE constraint but no explicit index was created in migrations -- PostgreSQL auto-creates an index for UNIQUE constraints via the SQLAlchemy model definition.

2. **plan_id FK ON DELETE behavior (NEW-DB-05):**
   - The `plan_id` foreign key uses **RESTRICT** (PostgreSQL default when ON DELETE is not specified)
   - This is an **intentional safety feature** to prevent accidental data loss
   - **Behavior:** Cannot delete a plan from `plans` table if any active subscriptions reference it
   - **Rationale:**
     - Plans are business-critical entities with pricing, features, and Stripe integration
     - Deleting a plan with active subscriptions would orphan billing records
     - Forces explicit handling: deactivate subscriptions first (`is_active = false`), then optionally delete plan
   - **Alternative approaches considered:**
     - `ON DELETE CASCADE`: Too dangerous - would delete all user subscriptions if plan is removed
     - `ON DELETE SET NULL`: Invalid - `plan_id` is NOT NULL (required for billing logic)
     - `RESTRICT` (current): Safest option - requires intentional cleanup workflow
   - **How to retire a plan:**
     ```sql
     -- 1. Mark plan as inactive (hides from catalog)
     UPDATE plans SET is_active = false WHERE id = 'old_plan';

     -- 2. Migrate or expire active subscriptions
     UPDATE user_subscriptions SET is_active = false WHERE plan_id = 'old_plan' AND is_active = true;

     -- 3. Only then can you delete the plan (if needed)
     DELETE FROM plans WHERE id = 'old_plan';
     ```

---

### 4. search_sessions

**Purpose:** Search history for analytics, session replay, and the /historico page.
**Migration:** `001_profiles_and_sessions.sql`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | NO | `gen_random_uuid()` | **PK** |
| `user_id` | `uuid` | NO | - | FK -> `profiles(id) ON DELETE CASCADE` |
| `sectors` | `text[]` | NO | - | |
| `ufs` | `text[]` | NO | - | |
| `data_inicial` | `date` | NO | - | |
| `data_final` | `date` | NO | - | |
| `custom_keywords` | `text[]` | YES | NULL | |
| `total_raw` | `int` | NO | `0` | |
| `total_filtered` | `int` | NO | `0` | |
| `valor_total` | `numeric(14,2)` | YES | `0` | |
| `resumo_executivo` | `text` | YES | NULL | |
| `destaques` | `text[]` | YES | NULL | |
| `excel_storage_path` | `text` | YES | NULL | Future: Supabase Storage |
| `created_at` | `timestamptz` | NO | `now()` | |

**Indexes:**
| Name | Columns | Type |
|------|---------|------|
| `search_sessions_pkey` | `id` | B-tree (PK) |
| `idx_search_sessions_user` | `user_id` | B-tree |
| `idx_search_sessions_created` | `user_id, created_at DESC` | B-tree |

---

### 5. monthly_quota

**Purpose:** Tracks monthly search usage per user. Uses lazy reset (no cron job -- new month key means fresh counter).
**Migration:** `002_monthly_quota.sql`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | NO | `gen_random_uuid()` | **PK** |
| `user_id` | `uuid` | NO | - | FK -> `auth.users(id) ON DELETE CASCADE` |
| `month_year` | `varchar(7)` | NO | - | Format: "2026-02" |
| `searches_count` | `int` | NO | `0` | |
| `created_at` | `timestamptz` | NO | `now()` | |
| `updated_at` | `timestamptz` | NO | `now()` | |

**Constraints:**
- `unique_user_month`: UNIQUE(`user_id`, `month_year`)

**Indexes:**
| Name | Columns | Type |
|------|---------|------|
| `monthly_quota_pkey` | `id` | B-tree (PK) |
| `idx_monthly_quota_user_month` | `user_id, month_year` | B-tree |
| `unique_user_month` | `user_id, month_year` | B-tree (UNIQUE) |

**Note:** FK references `auth.users(id)` directly, NOT `profiles(id)`. This is inconsistent with other tables.

---

### 6. plan_features

**Purpose:** Feature flags per plan + billing period (e.g., annual-exclusive features).
**Migration:** `009_create_plan_features.sql`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | `serial` | NO | auto-increment | **PK** |
| `plan_id` | `text` | NO | - | FK -> `plans(id) ON DELETE CASCADE` |
| `billing_period` | `varchar(10)` | NO | - | CHECK: `IN ('monthly', 'annual')` |
| `feature_key` | `varchar(100)` | NO | - | |
| `enabled` | `boolean` | NO | `true` | |
| `metadata` | `jsonb` | YES | `'{}'` | |
| `created_at` | `timestamptz` | NO | `now()` | |
| `updated_at` | `timestamptz` | NO | `now()` | Auto-updated via trigger |

**Constraints:**
- UNIQUE(`plan_id`, `billing_period`, `feature_key`)

**Indexes:**
| Name | Columns | Type | Condition |
|------|---------|------|-----------|
| `plan_features_pkey` | `id` | B-tree (PK) | - |
| `idx_plan_features_lookup` | `plan_id, billing_period, enabled` | B-tree (partial) | `WHERE enabled = true` |

**Seeded Features (7 rows):**

| plan_id | billing_period | feature_key | enabled |
|---------|---------------|-------------|---------|
| consultor_agil | annual | early_access | true |
| consultor_agil | annual | proactive_search | true |
| maquina | annual | early_access | true |
| maquina | annual | proactive_search | true |
| sala_guerra | annual | early_access | true |
| sala_guerra | annual | proactive_search | true |
| sala_guerra | annual | ai_edital_analysis | true |

---

### 7. stripe_webhook_events

**Purpose:** Idempotency table for Stripe webhook deduplication and audit trail.
**Migration:** `010_stripe_webhook_events.sql`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | `varchar(255)` | NO | - | **PK**, CHECK: `id ~ '^evt_'` |
| `type` | `varchar(100)` | NO | - | |
| `processed_at` | `timestamptz` | NO | `now()` | |
| `payload` | `jsonb` | YES | NULL | |

**Indexes:**
| Name | Columns | Type |
|------|---------|------|
| `stripe_webhook_events_pkey` | `id` | B-tree (PK) |
| `idx_webhook_events_type` | `type, processed_at` | B-tree |
| `idx_webhook_events_recent` | `processed_at DESC` | B-tree |

---

### 8. conversations

**Purpose:** Support conversation threads between users and admins (InMail system).
**Migration:** `012_create_messages.sql`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | NO | `gen_random_uuid()` | **PK** |
| `user_id` | `uuid` | NO | - | FK -> `profiles(id) ON DELETE CASCADE` |
| `subject` | `text` | NO | - | CHECK: `char_length(subject) <= 200` |
| `category` | `text` | NO | - | CHECK: `IN ('suporte', 'sugestao', 'funcionalidade', 'bug', 'outro')` |
| `status` | `text` | NO | `'aberto'` | CHECK: `IN ('aberto', 'respondido', 'resolvido')` |
| `last_message_at` | `timestamptz` | NO | `now()` | Auto-updated via trigger |
| `created_at` | `timestamptz` | NO | `now()` | |
| `updated_at` | `timestamptz` | NO | `now()` | |

**Indexes:**
| Name | Columns | Type |
|------|---------|------|
| `conversations_pkey` | `id` | B-tree (PK) |
| `idx_conversations_user_id` | `user_id` | B-tree |
| `idx_conversations_status` | `status` | B-tree |
| `idx_conversations_last_message` | `last_message_at DESC` | B-tree |

---

### 9. messages

**Purpose:** Individual messages within conversation threads.
**Migration:** `012_create_messages.sql`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | NO | `gen_random_uuid()` | **PK** |
| `conversation_id` | `uuid` | NO | - | FK -> `conversations(id) ON DELETE CASCADE` |
| `sender_id` | `uuid` | NO | - | FK -> `profiles(id) ON DELETE CASCADE` |
| `body` | `text` | NO | - | CHECK: `char_length >= 1 AND char_length <= 5000` |
| `is_admin_reply` | `boolean` | NO | `false` | |
| `read_by_user` | `boolean` | NO | `false` | |
| `read_by_admin` | `boolean` | NO | `false` | |
| `created_at` | `timestamptz` | NO | `now()` | |

**Indexes:**
| Name | Columns | Type | Condition |
|------|---------|------|-----------|
| `messages_pkey` | `id` | B-tree (PK) | - |
| `idx_messages_conversation` | `conversation_id, created_at` | B-tree | - |
| `idx_messages_unread_by_user` | `conversation_id` | B-tree (partial) | `WHERE is_admin_reply = true AND read_by_user = false` |
| `idx_messages_unread_by_admin` | `conversation_id` | B-tree (partial) | `WHERE is_admin_reply = false AND read_by_admin = false` |

---

### 10. user_oauth_tokens

**Purpose:** Encrypted OAuth 2.0 tokens for Google Sheets (and future) integrations.
**Migration:** `013_google_oauth_tokens.sql`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | NO | `gen_random_uuid()` | **PK** |
| `user_id` | `uuid` | NO | - | FK -> `auth.users(id) ON DELETE CASCADE` |
| `provider` | `varchar(50)` | NO | - | CHECK: `IN ('google', 'microsoft', 'dropbox')` |
| `access_token` | `text` | NO | - | AES-256 encrypted |
| `refresh_token` | `text` | YES | NULL | AES-256 encrypted |
| `expires_at` | `timestamptz` | NO | - | |
| `scope` | `text` | NO | - | |
| `created_at` | `timestamptz` | YES | `now()` | |
| `updated_at` | `timestamptz` | YES | `now()` | |

**Constraints:**
- `unique_user_provider`: UNIQUE(`user_id`, `provider`)

**Indexes:**
| Name | Columns | Type |
|------|---------|------|
| `user_oauth_tokens_pkey` | `id` | B-tree (PK) |
| `idx_user_oauth_tokens_user_id` | `user_id` | B-tree |
| `idx_user_oauth_tokens_expires_at` | `expires_at` | B-tree |
| `idx_user_oauth_tokens_provider` | `provider` | B-tree |

**Note:** FK references `auth.users(id)` directly, not `profiles(id)`.

---

### 11. google_sheets_exports

**Purpose:** Audit trail and "re-open last export" for Google Sheets exports.
**Migration:** `014_google_sheets_exports.sql`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | `uuid` | NO | `gen_random_uuid()` | **PK** |
| `user_id` | `uuid` | NO | - | FK -> `auth.users(id) ON DELETE CASCADE` |
| `spreadsheet_id` | `varchar(255)` | NO | - | |
| `spreadsheet_url` | `text` | NO | - | |
| `search_params` | `jsonb` | NO | - | Snapshot of search parameters |
| `total_rows` | `int` | NO | - | CHECK: `total_rows >= 0` |
| `created_at` | `timestamptz` | YES | `now()` | |
| `last_updated_at` | `timestamptz` | YES | `now()` | |

**Indexes:**
| Name | Columns | Type |
|------|---------|------|
| `google_sheets_exports_pkey` | `id` | B-tree (PK) |
| `idx_google_sheets_exports_user_id` | `user_id` | B-tree |
| `idx_google_sheets_exports_created_at` | `created_at DESC` | B-tree |
| `idx_google_sheets_exports_spreadsheet_id` | `spreadsheet_id` | B-tree |
| `idx_google_sheets_exports_search_params` | `search_params` | **GIN** (JSONB) |

---

## Functions & Triggers

### Functions

| Function | Returns | Language | Security | Purpose | Migration |
|----------|---------|----------|----------|---------|-----------|
| `handle_new_user()` | trigger | plpgsql | DEFINER | Auto-create profile on auth.users INSERT | 001 (updated in 007) |
| `update_updated_at()` | trigger | plpgsql | INVOKER | Set `updated_at = now()` on UPDATE | 001 |
| `increment_quota_atomic(p_user_id, p_month_year, p_max_quota)` | TABLE(new_count, was_at_limit, previous_count) | plpgsql | INVOKER | Atomic quota increment with limit check | 003 |
| `check_and_increment_quota(p_user_id, p_month_year, p_max_quota)` | TABLE(allowed, new_count, previous_count, quota_remaining) | plpgsql | INVOKER | Combined check+increment (race-condition-safe) | 003 |
| `get_user_billing_period(p_user_id)` | varchar(10) | plpgsql | DEFINER | Get user's current billing period | 011 |
| `user_has_feature(p_user_id, p_feature_key)` | boolean | plpgsql | DEFINER | Check if user has specific feature | 011 |
| `get_user_features(p_user_id)` | text[] | plpgsql | DEFINER | Get all enabled features for user | 011 |
| `update_conversation_last_message()` | trigger | plpgsql | INVOKER | Update conversations.last_message_at on new message | 012 |

### Triggers

| Trigger | Table | Event | Function |
|---------|-------|-------|----------|
| `on_auth_user_created` | `auth.users` | AFTER INSERT | `handle_new_user()` |
| `profiles_updated_at` | `profiles` | BEFORE UPDATE | `update_updated_at()` |
| `plan_features_updated_at` | `plan_features` | BEFORE UPDATE | `update_updated_at()` |
| `trg_update_conversation_last_message` | `messages` | AFTER INSERT | `update_conversation_last_message()` |

### Grants

| Function | Granted To |
|----------|-----------|
| `increment_quota_atomic` | `service_role` |
| `check_and_increment_quota` | `service_role` |

---

## Indexes

### Summary (all tables)

| Table | Index Count | Partial Indexes | GIN Indexes |
|-------|-------------|-----------------|-------------|
| profiles | 3 | 2 | 0 |
| plans | 1 | 0 | 0 |
| user_subscriptions | 4 | 2 | 0 |
| search_sessions | 3 | 0 | 0 |
| monthly_quota | 3 | 0 | 0 |
| plan_features | 2 | 1 | 0 |
| stripe_webhook_events | 3 | 0 | 0 |
| conversations | 4 | 0 | 0 |
| messages | 4 | 2 | 0 |
| user_oauth_tokens | 4 | 0 | 0 |
| google_sheets_exports | 5 | 0 | 1 |
| **TOTAL** | **36** | **7** | **1** |

---

## Enums & Constraints

### CHECK Constraints

| Table | Constraint | Expression |
|-------|-----------|------------|
| profiles | `profiles_plan_type_check` | `plan_type IN ('free', 'avulso', 'pack', 'monthly', 'annual', 'master', 'free_trial', 'consultor_agil', 'maquina', 'sala_guerra')` |
| profiles | `phone_whatsapp_format` | `phone_whatsapp IS NULL OR phone_whatsapp ~ '^[0-9]{10,11}$'` |
| user_subscriptions | (unnamed) | `billing_period IN ('monthly', 'annual')` |
| plan_features | (unnamed) | `billing_period IN ('monthly', 'annual')` |
| stripe_webhook_events | `check_event_id_format` | `id ~ '^evt_'` |
| conversations | (unnamed) | `char_length(subject) <= 200` |
| conversations | (unnamed) | `category IN ('suporte', 'sugestao', 'funcionalidade', 'bug', 'outro')` |
| conversations | (unnamed) | `status IN ('aberto', 'respondido', 'resolvido')` |
| messages | (unnamed) | `char_length(body) >= 1 AND char_length(body) <= 5000` |
| user_oauth_tokens | (unnamed) | `provider IN ('google', 'microsoft', 'dropbox')` |
| google_sheets_exports | (unnamed) | `total_rows >= 0` |

### UNIQUE Constraints

| Table | Constraint | Columns |
|-------|-----------|---------|
| monthly_quota | `unique_user_month` | `(user_id, month_year)` |
| plan_features | (unnamed) | `(plan_id, billing_period, feature_key)` |
| user_oauth_tokens | `unique_user_provider` | `(user_id, provider)` |

### Foreign Keys

| Source Table | Column | Target Table | Target Column | On Delete |
|-------------|--------|-------------|---------------|-----------|
| profiles | id | auth.users | id | CASCADE |
| user_subscriptions | user_id | profiles | id | CASCADE |
| user_subscriptions | plan_id | plans | id | (none/restrict) |
| search_sessions | user_id | profiles | id | CASCADE |
| monthly_quota | user_id | auth.users | id | CASCADE |
| plan_features | plan_id | plans | id | CASCADE |
| conversations | user_id | profiles | id | CASCADE |
| messages | conversation_id | conversations | id | CASCADE |
| messages | sender_id | profiles | id | CASCADE |
| user_oauth_tokens | user_id | auth.users | id | CASCADE |
| google_sheets_exports | user_id | auth.users | id | CASCADE |

---

## Row Level Security Policies

### profiles (RLS: ENABLED)

| Policy | Operation | Expression |
|--------|-----------|------------|
| `profiles_select_own` | SELECT | `auth.uid() = id` |
| `profiles_update_own` | UPDATE | `auth.uid() = id` |

### plans (RLS: ENABLED)

| Policy | Operation | Expression |
|--------|-----------|------------|
| `plans_select_all` | SELECT | `true` (public catalog) |

### user_subscriptions (RLS: ENABLED)

| Policy | Operation | Expression |
|--------|-----------|------------|
| `subscriptions_select_own` | SELECT | `auth.uid() = user_id` |

### search_sessions (RLS: ENABLED)

| Policy | Operation | Expression |
|--------|-----------|------------|
| `sessions_select_own` | SELECT | `auth.uid() = user_id` |
| `sessions_insert_own` | INSERT | `auth.uid() = user_id` |
| `Service role can manage search sessions` | ALL | `true` |

### monthly_quota (RLS: ENABLED)

| Policy | Operation | Expression |
|--------|-----------|------------|
| `Users can view own quota` | SELECT | `auth.uid() = user_id` |
| `Service role can manage quota` | ALL | `true` |

### plan_features (RLS: ENABLED)

| Policy | Operation | Expression |
|--------|-----------|------------|
| `plan_features_select_all` | SELECT | `true` (public catalog) |

### stripe_webhook_events (RLS: ENABLED)

| Policy | Operation | Expression |
|--------|-----------|------------|
| `webhook_events_insert_service` | INSERT | `true` (service role) |
| `webhook_events_select_admin` | SELECT | `EXISTS (profiles WHERE id = auth.uid() AND plan_type = 'master')` |

### conversations (RLS: ENABLED)

| Policy | Operation | Expression |
|--------|-----------|------------|
| `conversations_select_own` | SELECT | `user_id = auth.uid() OR is_admin(auth.uid())` |
| `conversations_insert_own` | INSERT | `auth.uid() = user_id` |
| `conversations_update_admin` | UPDATE | `is_admin(auth.uid())` |

### messages (RLS: ENABLED)

| Policy | Operation | Expression |
|--------|-----------|------------|
| `messages_select` | SELECT | user owns conversation OR is admin |
| `messages_insert_user` | INSERT | sender_id = auth.uid() AND (owns conversation OR is admin) |
| `messages_update_read` | UPDATE | owns conversation OR is admin |

### user_oauth_tokens (RLS: ENABLED)

| Policy | Operation | Expression |
|--------|-----------|------------|
| `Users can view own OAuth tokens` | SELECT | `auth.uid() = user_id` |
| `Users can update own OAuth tokens` | UPDATE | `auth.uid() = user_id` |
| `Users can delete own OAuth tokens` | DELETE | `auth.uid() = user_id` |
| `Service role can manage all OAuth tokens` | ALL | `true` (TO service_role) |

### google_sheets_exports (RLS: ENABLED)

| Policy | Operation | Expression |
|--------|-----------|------------|
| `Users can view own Google Sheets exports` | SELECT | `auth.uid() = user_id` |
| `Users can create Google Sheets exports` | INSERT | `auth.uid() = user_id` |
| `Users can update own Google Sheets exports` | UPDATE | `auth.uid() = user_id` |
| `Service role can manage all Google Sheets exports` | ALL | `true` (TO service_role) |

---

## Data Access Patterns

### Backend Client

The backend uses **two separate database access mechanisms:**

1. **Supabase Python Client** (`supabase_client.py`) -- Used by most modules
   - Uses `SUPABASE_SERVICE_ROLE_KEY` (admin privileges, bypasses RLS)
   - Tables accessed: profiles, plans, user_subscriptions, search_sessions, monthly_quota, plan_features, user_oauth_tokens, google_sheets_exports, conversations, messages

2. **SQLAlchemy ORM** (`database.py`) -- Used exclusively by Stripe webhook handler
   - Uses direct PostgreSQL connection (derived from `SUPABASE_URL`)
   - Models: `StripeWebhookEvent`, `UserSubscription`
   - Tables accessed: stripe_webhook_events, user_subscriptions

### Common Query Patterns

| Operation | Table(s) | Access Method | Frequency |
|-----------|----------|--------------|-----------|
| Auth token validation | auth.users | Supabase Auth API | Every request |
| Check user plan | user_subscriptions, profiles | Supabase client | Every search |
| Quota check + increment | monthly_quota | RPC function | Every search |
| Save search session | search_sessions | Supabase client | Every search |
| List admin users | profiles + user_subscriptions | Supabase client | Admin page loads |
| Feature flag lookup | user_subscriptions + plan_features | Supabase client (Redis cached) | Feature checks |
| Stripe webhook | stripe_webhook_events, user_subscriptions | SQLAlchemy | Stripe events |
| Messaging | conversations, messages | Supabase client | User interactions |
| Google export | user_oauth_tokens, google_sheets_exports | Supabase client | Export actions |
