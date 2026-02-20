# Database Schema Documentation - SmartLic/BidIQ

**Provider:** Supabase (PostgreSQL 17)
**Project Ref:** `fqqyovlzdzimiwfofdjk`
**Schema Generated:** 2026-02-15
**Migrations Analyzed:** 001 through 026 (26 migration files)

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
   - [audit_events](#12-audit_events)
   - [pipeline_items](#13-pipeline_items)
   - [search_results_cache](#14-search_results_cache)
4. [Functions & Triggers](#functions--triggers)
5. [Indexes](#indexes)
6. [Enums & Constraints](#enums--constraints)
7. [Row Level Security Policies](#row-level-security-policies)
8. [Data Access Patterns](#data-access-patterns)
9. [pg_cron Scheduled Jobs](#pg_cron-scheduled-jobs)

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
- **Audit Logging** with SHA-256 hashed PII for LGPD/GDPR compliance
- **Opportunity Pipeline** for tracking procurement through stages
- **Search Results Cache** for resilient "never empty-handed" fallback

**Total Tables:** 14 (in `public` schema) + Supabase `auth.users` (managed)
**Total Migrations:** 26 files (numbered 001-026, including 006a/006b, rollback, deprecated)
**Total RLS Policies:** ~38
**Total Functions:** 14
**Total Triggers:** 8
**Total Indexes:** ~52

---

## Entity Relationship Diagram

```
auth.users (managed by Supabase Auth)
    |
    | 1:1 (trigger: handle_new_user)
    v
profiles -------+-------+-------+-------+-------+
    |           |       |       |       |       |
    | 1:N       | 1:N   | 1:N   | 1:N   | 1:N   |
    v           v       v       v       v       v
user_subs  search_  monthly  convers-  user_   google_
criptions  sessions  _quota   ations  oauth_  sheets_
    |                           |     tokens  exports
    | N:1                       |
    v                           | 1:N
  plans ----+                   v
    |       |               messages
    | 1:N   |
    v       v
plan_     (stripe_
features   price_ids)

pipeline_items -----------> auth.users (FK)
search_results_cache -----> auth.users (FK)
audit_events (standalone, no FKs)
stripe_webhook_events (standalone, no FKs)
```

---

## Tables

### 1. profiles

**Purpose:** Extends `auth.users` with application-specific user data.
**Migrations:** 001, 004, 007, 016 (handle_new_user fix), 020 (plan_type constraint tightened, INSERT policies), 024 (context_data)

| Column | Type | Nullable | Default | Constraints / Notes |
|--------|------|----------|---------|---------------------|
| `id` | `uuid` | NO | - | **PK**, FK -> `auth.users(id) ON DELETE CASCADE` |
| `email` | `text` | NO | - | Trigram index (gin_trgm_ops) for admin ILIKE search |
| `full_name` | `text` | YES | NULL | |
| `company` | `text` | YES | NULL | |
| `plan_type` | `text` | NO | `'free'` (orig) / `'free_trial'` (via handle_new_user after 016) | CHECK: see constraint below |
| `avatar_url` | `text` | YES | NULL | |
| `is_admin` | `boolean` | NO | `false` | Added in migration 004 |
| `sector` | `text` | YES | NULL | Added in migration 007 |
| `phone_whatsapp` | `text` | YES | NULL | CHECK: `^[0-9]{10,11}$` or NULL |
| `whatsapp_consent` | `boolean` | YES | `false` | |
| `whatsapp_consent_at` | `timestamptz` | YES | NULL | LGPD audit trail |
| `context_data` | `jsonb` | YES | `'{}'::jsonb` | Added in migration 024. Onboarding wizard data |
| `created_at` | `timestamptz` | NO | `now()` | |
| `updated_at` | `timestamptz` | NO | `now()` | Auto-updated via trigger |

**CHECK Constraint (`profiles_plan_type_check`) -- tightened in migration 020:**
```sql
plan_type IN (
  'free_trial',      -- Trial plan (default for new users)
  'consultor_agil',  -- Tier 1: 25-50 searches/month
  'maquina',         -- Tier 2: 100-300 searches/month
  'sala_guerra',     -- Tier 3: Unlimited searches
  'master'           -- Admin/internal accounts
)
```
Legacy values `('free', 'avulso', 'pack', 'monthly', 'annual')` were removed by migration 020 after data migration.

**context_data JSONB Schema (migration 024, STORY-247):**
```json
{
  "ufs_atuacao": ["SP", "RJ"],
  "faixa_valor_min": 50000.0,
  "faixa_valor_max": 5000000.0,
  "porte_empresa": "ME|EPP|MEDIO|GRANDE",
  "modalidades_interesse": [4, 6],
  "palavras_chave": ["uniforme", "fardamento"],
  "experiencia_licitacoes": "PRIMEIRA_VEZ|INICIANTE|EXPERIENTE"
}
```

**Indexes:**
| Name | Columns | Type | Condition |
|------|---------|------|-----------|
| `profiles_pkey` | `id` | B-tree (PK) | - |
| `idx_profiles_is_admin` | `is_admin` | B-tree (partial) | `WHERE is_admin = true` |
| `idx_profiles_whatsapp_consent` | `whatsapp_consent` | B-tree (partial) | `WHERE whatsapp_consent = true` |
| `idx_profiles_email_trgm` | `email` | **GIN** (trigram) | - (migration 016) |
| `idx_profiles_context_porte` | `(context_data->>'porte_empresa')` | B-tree | `WHERE context_data->>'porte_empresa' IS NOT NULL` (migration 024) |

**Triggers:**
- `profiles_updated_at` -> `update_updated_at()` (BEFORE UPDATE)
- `on_auth_user_created` on `auth.users` -> `handle_new_user()` (AFTER INSERT)

---

### 2. plans

**Purpose:** Plan catalog with pricing and Stripe integration.
**Migrations:** 001, 005, 015, 020 (updated_at column + trigger)

| Column | Type | Nullable | Default | Constraints / Notes |
|--------|------|----------|---------|---------------------|
| `id` | `text` | NO | - | **PK** |
| `name` | `text` | NO | - | |
| `description` | `text` | YES | NULL | |
| `max_searches` | `int` | YES | NULL | NULL = unlimited |
| `price_brl` | `numeric(10,2)` | NO | `0` | |
| `duration_days` | `int` | YES | NULL | NULL = perpetual |
| `stripe_price_id` | `text` | YES | NULL | Legacy default (= monthly). Hardcoded production IDs in migration 015 |
| `stripe_price_id_monthly` | `text` | YES | NULL | Added in migration 015 |
| `stripe_price_id_annual` | `text` | YES | NULL | Added in migration 015 |
| `is_active` | `boolean` | NO | `true` | |
| `created_at` | `timestamptz` | NO | `now()` | |
| `updated_at` | `timestamptz` | NO | `now()` | Added in migration 020, auto-updated via trigger |

**Seeded Data (after migrations 001 + 005):**

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

**Stripe Price IDs (migration 015, PRODUCTION values):**

| plan_id | stripe_price_id_monthly | stripe_price_id_annual |
|---------|------------------------|----------------------|
| consultor_agil | `price_1Syir09FhmvPslGYOCbOvWVB` | `price_1SzRAC9FhmvPslGYLBuYTaSa` |
| maquina | `price_1Syirk9FhmvPslGY1kbNWxaz` | `price_1SzR8F9FhmvPslGYDW84AzYA` |
| sala_guerra | `price_1Syise9FhmvPslGYAR8Fbf5E` | `price_1SzR5c9FhmvPslGYQym74G6K` |

**WARNING:** Migration 015 hardcodes PRODUCTION Stripe price IDs. For staging/dev, manually update with test mode IDs.

---

### 3. user_subscriptions

**Purpose:** Active and historical subscriptions for each user.
**Migrations:** 001, 008 (billing_period, annual_benefits), 016 (unique index on stripe_subscription_id, service role policy), 017 (sync trigger references `status` column), 021 (updated_at column + trigger), 022 (stripe_customer_id index)

| Column | Type | Nullable | Default | Constraints / Notes |
|--------|------|----------|---------|---------------------|
| `id` | `uuid` | NO | `gen_random_uuid()` | **PK** |
| `user_id` | `uuid` | NO | - | FK -> `profiles(id) ON DELETE CASCADE` |
| `plan_id` | `text` | NO | - | FK -> `plans(id)` ON DELETE RESTRICT (intentional, documented in migration 022) |
| `credits_remaining` | `int` | YES | NULL | NULL = unlimited (deprecated by monthly quota) |
| `starts_at` | `timestamptz` | NO | `now()` | |
| `expires_at` | `timestamptz` | YES | NULL | NULL = never expires |
| `stripe_subscription_id` | `text` | YES | NULL | UNIQUE partial index (WHERE NOT NULL) |
| `stripe_customer_id` | `text` | YES | NULL | Partial index for webhook lookups |
| `billing_period` | `varchar(10)` | NO | `'monthly'` | CHECK: `IN ('monthly', 'annual')` (migration 008) |
| `annual_benefits` | `jsonb` | NO | `'{}'` | Added in migration 008 |
| `is_active` | `boolean` | NO | `true` | |
| `created_at` | `timestamptz` | NO | `now()` | |
| `updated_at` | `timestamptz` | NO | `now()` | Added in migration 021, auto-updated via trigger |

**CRITICAL NOTE: Missing `status` column.** Migration 017 creates trigger `sync_profile_plan_type()` which references `NEW.status` on this table with values `('active', 'trialing', 'canceled', 'expired', 'past_due')`. However, NO migration defines a `status` column on `user_subscriptions`. The trigger will fail silently or reference a nonexistent column unless `status` was added manually outside the migration sequence.

**Indexes:**
| Name | Columns | Type | Condition |
|------|---------|------|-----------|
| `user_subscriptions_pkey` | `id` | B-tree (PK) | - |
| `idx_user_subscriptions_user` | `user_id` | B-tree | - |
| `idx_user_subscriptions_active` | `user_id, is_active` | B-tree (partial) | `WHERE is_active = true` |
| `idx_user_subscriptions_billing` | `user_id, billing_period, is_active` | B-tree (partial) | `WHERE is_active = true` (migration 008) |
| `idx_user_subscriptions_stripe_sub_id` | `stripe_subscription_id` | B-tree (UNIQUE, partial) | `WHERE stripe_subscription_id IS NOT NULL` (migration 016) |
| `idx_user_subscriptions_customer_id` | `stripe_customer_id` | B-tree (partial) | `WHERE stripe_customer_id IS NOT NULL` (migration 022) |

**ON DELETE RESTRICT on plan_id** is intentional (documented in migration 022):
- Prevents deleting plans with active subscriptions
- To retire a plan: set `plans.is_active = false`, then deactivate subscriptions, then optionally delete

---

### 4. search_sessions

**Purpose:** Search history for analytics, session replay, and the /historico page.
**Migration:** 001

| Column | Type | Nullable | Default | Constraints / Notes |
|--------|------|----------|---------|---------------------|
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

**Purpose:** Tracks monthly search usage per user. Uses lazy reset (new month key means fresh counter).
**Migrations:** 002, 018 (FK standardized to profiles(id))

| Column | Type | Nullable | Default | Constraints / Notes |
|--------|------|----------|---------|---------------------|
| `id` | `uuid` | NO | `gen_random_uuid()` | **PK** |
| `user_id` | `uuid` | NO | - | FK -> `profiles(id) ON DELETE CASCADE` (changed from auth.users in migration 018) |
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
| `unique_user_month` | `user_id, month_year` | B-tree (UNIQUE, auto-created) |

**Retention:** 24 months. pg_cron job `cleanup-monthly-quota` runs on 1st of each month at 2:00 AM UTC (migration 022).

---

### 6. plan_features

**Purpose:** Feature flags per plan + billing period (e.g., annual-exclusive features).
**Migration:** 009

| Column | Type | Nullable | Default | Constraints / Notes |
|--------|------|----------|---------|---------------------|
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

**Seeded Features (7 rows, migration 009):**

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
**Migrations:** 010, 016 (admin policy fix)

| Column | Type | Nullable | Default | Constraints / Notes |
|--------|------|----------|---------|---------------------|
| `id` | `varchar(255)` | NO | - | **PK**, CHECK: `id ~ '^evt_'` |
| `type` | `varchar(100)` | NO | - | e.g., `customer.subscription.updated` |
| `processed_at` | `timestamptz` | NO | `now()` | |
| `payload` | `jsonb` | YES | NULL | Full Stripe event object |

**Indexes:**
| Name | Columns | Type |
|------|---------|------|
| `stripe_webhook_events_pkey` | `id` | B-tree (PK) |
| `idx_webhook_events_type` | `type, processed_at` | B-tree |
| `idx_webhook_events_recent` | `processed_at DESC` | B-tree |

**Retention:** 90 days. pg_cron job `cleanup-webhook-events` runs daily at 3:00 AM UTC (migration 022).

---

### 8. conversations

**Purpose:** Support conversation threads between users and admins (InMail system).
**Migration:** 012

| Column | Type | Nullable | Default | Constraints / Notes |
|--------|------|----------|---------|---------------------|
| `id` | `uuid` | NO | `gen_random_uuid()` | **PK** |
| `user_id` | `uuid` | NO | - | FK -> `profiles(id) ON DELETE CASCADE` |
| `subject` | `text` | NO | - | CHECK: `char_length(subject) <= 200` |
| `category` | `text` | NO | - | CHECK: `IN ('suporte', 'sugestao', 'funcionalidade', 'bug', 'outro')` |
| `status` | `text` | NO | `'aberto'` | CHECK: `IN ('aberto', 'respondido', 'resolvido')` |
| `last_message_at` | `timestamptz` | NO | `now()` | Auto-updated via trigger on messages INSERT |
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
**Migration:** 012

| Column | Type | Nullable | Default | Constraints / Notes |
|--------|------|----------|---------|---------------------|
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
**Migrations:** 013, 018 (FK standardized to profiles(id)), 022 (redundant provider index dropped)

| Column | Type | Nullable | Default | Constraints / Notes |
|--------|------|----------|---------|---------------------|
| `id` | `uuid` | NO | `gen_random_uuid()` | **PK** |
| `user_id` | `uuid` | NO | - | FK -> `profiles(id) ON DELETE CASCADE` (changed from auth.users in migration 018) |
| `provider` | `varchar(50)` | NO | - | CHECK: `IN ('google', 'microsoft', 'dropbox')` |
| `access_token` | `text` | NO | - | AES-256 encrypted at application layer |
| `refresh_token` | `text` | YES | NULL | AES-256 encrypted at application layer |
| `expires_at` | `timestamptz` | NO | - | |
| `scope` | `text` | NO | - | |
| `created_at` | `timestamptz` | YES | `now()` | |
| `updated_at` | `timestamptz` | YES | `now()` | |

**Constraints:**
- `unique_user_provider`: UNIQUE(`user_id`, `provider`)

**Indexes:**
| Name | Columns | Type | Notes |
|------|---------|------|-------|
| `user_oauth_tokens_pkey` | `id` | B-tree (PK) | |
| `idx_user_oauth_tokens_user_id` | `user_id` | B-tree | |
| `idx_user_oauth_tokens_expires_at` | `expires_at` | B-tree | For token refresh job |
| ~~`idx_user_oauth_tokens_provider`~~ | ~~`provider`~~ | ~~B-tree~~ | **DROPPED** in migration 022 (redundant with unique_user_provider) |

---

### 11. google_sheets_exports

**Purpose:** Audit trail and "re-open last export" for Google Sheets exports.
**Migrations:** 014, 018 (FK standardized to profiles(id))

| Column | Type | Nullable | Default | Constraints / Notes |
|--------|------|----------|---------|---------------------|
| `id` | `uuid` | NO | `gen_random_uuid()` | **PK** |
| `user_id` | `uuid` | NO | - | FK -> `profiles(id) ON DELETE CASCADE` (changed from auth.users in migration 018) |
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

### 12. audit_events

**Purpose:** Persistent audit log for security-relevant events with SHA-256 hashed PII.
**Migration:** 023 (STORY-226 Track 5)

| Column | Type | Nullable | Default | Constraints / Notes |
|--------|------|----------|---------|---------------------|
| `id` | `uuid` | NO | `gen_random_uuid()` | **PK** |
| `timestamp` | `timestamptz` | NO | `now()` | |
| `event_type` | `text` | NO | - | See valid types below |
| `actor_id_hash` | `text` | YES | NULL | SHA-256 hash truncated to 16 hex chars |
| `target_id_hash` | `text` | YES | NULL | SHA-256 hash truncated to 16 hex chars |
| `details` | `jsonb` | YES | NULL | Structured event metadata, no PII |
| `ip_hash` | `text` | YES | NULL | SHA-256 hash truncated to 16 hex chars |

**Valid event_type values:**
`auth.login`, `auth.logout`, `auth.signup`, `admin.user_create`, `admin.user_delete`, `admin.plan_assign`, `billing.checkout`, `billing.subscription_change`, `data.search`, `data.download`

**Indexes:**
| Name | Columns | Type | Condition |
|------|---------|------|-----------|
| `audit_events_pkey` | `id` | B-tree (PK) | - |
| `idx_audit_events_event_type` | `event_type` | B-tree | - |
| `idx_audit_events_timestamp` | `timestamp` | B-tree | - |
| `idx_audit_events_actor` | `actor_id_hash` | B-tree (partial) | `WHERE actor_id_hash IS NOT NULL` |
| `idx_audit_events_type_timestamp` | `event_type, timestamp DESC` | B-tree | Composite for dashboard queries |

**Retention:** 12 months. pg_cron job `cleanup-audit-events` runs on 1st of each month at 4:00 AM UTC (migration 023).

---

### 13. pipeline_items

**Purpose:** Tracks procurement opportunities through pipeline stages (descoberta -> analise -> preparando -> enviada -> resultado).
**Migration:** 025 (STORY-250)

| Column | Type | Nullable | Default | Constraints / Notes |
|--------|------|----------|---------|---------------------|
| `id` | `uuid` | NO | `gen_random_uuid()` | **PK** |
| `user_id` | `uuid` | NO | - | FK -> `auth.users(id) ON DELETE CASCADE` (**inconsistent: should be profiles(id)**) |
| `pncp_id` | `text` | NO | - | PNCP procurement ID (snapshot) |
| `objeto` | `text` | NO | - | |
| `orgao` | `text` | YES | NULL | |
| `uf` | `text` | YES | NULL | |
| `valor_estimado` | `numeric` | YES | NULL | |
| `data_encerramento` | `timestamptz` | YES | NULL | |
| `link_pncp` | `text` | YES | NULL | |
| `stage` | `text` | NO | `'descoberta'` | CHECK: `IN ('descoberta', 'analise', 'preparando', 'enviada', 'resultado')` |
| `notes` | `text` | YES | NULL | |
| `created_at` | `timestamptz` | NO | `now()` | |
| `updated_at` | `timestamptz` | NO | `now()` | Auto-updated via trigger |

**Constraints:**
- UNIQUE(`user_id`, `pncp_id`) -- prevents duplicate pipeline entries per user

**Indexes:**
| Name | Columns | Type | Condition |
|------|---------|------|-----------|
| `pipeline_items_pkey` | `id` | B-tree (PK) | - |
| `idx_pipeline_user_stage` | `user_id, stage` | B-tree | - |
| `idx_pipeline_encerramento` | `data_encerramento` | B-tree (partial) | `WHERE stage NOT IN ('enviada', 'resultado')` |
| `idx_pipeline_user_created` | `user_id, created_at DESC` | B-tree | - |

---

### 14. search_results_cache

**Purpose:** Cache for search results with health monitoring and priority management. Serves cached data when all sources fail ("Never Empty-Handed" principle).
**Migrations:** 026 (STORY-257A — base), 027 (sources_json + fetched_at), 031 (health fields), 032 (priority + access tracking), 033 (fetched_at index)

| # | Column | Type | Nullable | Default | Migration |
|---|--------|------|----------|---------|-----------|
| 1 | id | UUID | NO | gen_random_uuid() | 026 |
| 2 | user_id | UUID | NO | - | 026 |
| 3 | params_hash | TEXT | NO | - | 026 |
| 4 | search_params | JSONB | NO | - | 026 |
| 5 | results | JSONB | NO | - | 026 |
| 6 | total_results | INTEGER | NO | - | 026 |
| 7 | created_at | TIMESTAMPTZ | NO | now() | 026 |
| 8 | sources_json | JSONB | NO | '["pncp"]' | 027 |
| 9 | fetched_at | TIMESTAMPTZ | NO | now() | 027 |
| 10 | last_success_at | TIMESTAMPTZ | YES | NULL | 031 |
| 11 | last_attempt_at | TIMESTAMPTZ | YES | NULL | 031 |
| 12 | fail_streak | INTEGER | NO | 0 | 031 |
| 13 | degraded_until | TIMESTAMPTZ | YES | NULL | 031 |
| 14 | coverage | JSONB | YES | NULL | 031 |
| 15 | fetch_duration_ms | INTEGER | YES | NULL | 031 |
| 16 | priority | TEXT | NO | 'cold' | 032 |
| 17 | access_count | INTEGER | NO | 0 | 032 |
| 18 | last_accessed_at | TIMESTAMPTZ | YES | NULL | 032 |

**Constraints:**
- UNIQUE(`user_id`, `params_hash`) -- one cache entry per user per unique search

**Indexes:**
| Name | Columns | Type |
|------|---------|------|
| `search_results_cache_pkey` | `id` | B-tree (PK) |
| `idx_search_cache_user` | `user_id, created_at DESC` | B-tree |
| `idx_search_cache_params_hash` | `params_hash` | B-tree |
| `idx_search_cache_fetched_at` | `fetched_at` | B-tree (migration 033) |

**Auto-cleanup:** Trigger `trg_cleanup_search_cache` fires AFTER INSERT and invokes `cleanup_search_cache_per_user()` to keep max 5 entries per user (oldest beyond 5 are deleted).

**Foreign Key NOTE:** `user_id` references `auth.users(id)` (not standardized to `profiles(id)` yet).

**SSOT Model:** `backend/models/cache.py:SearchResultsCacheRow`

---

## Functions & Triggers

### Functions

| Function | Returns | Language | Security | Purpose | Migration |
|----------|---------|----------|----------|---------|-----------|
| `handle_new_user()` | trigger | plpgsql | DEFINER | Auto-create profile on auth.users INSERT. Sets plan_type to free_trial (migration 016), includes context_data default (migration 024) | 001, 007, 016, 024 |
| `update_updated_at()` | trigger | plpgsql | INVOKER | Set `updated_at = now()` on UPDATE | 001 |
| `increment_quota_atomic(p_user_id, p_month_year, p_max_quota)` | TABLE(new_count, was_at_limit, previous_count) | plpgsql | INVOKER | Atomic quota increment with limit check | 003 |
| `check_and_increment_quota(p_user_id, p_month_year, p_max_quota)` | TABLE(allowed, new_count, previous_count, quota_remaining) | plpgsql | INVOKER | Combined check+increment (race-condition-safe) | 003 |
| `get_user_billing_period(p_user_id)` | varchar(10) | plpgsql | DEFINER | Get user's current billing period (monthly/annual) | 011 |
| `user_has_feature(p_user_id, p_feature_key)` | boolean | plpgsql | DEFINER | Check if user has specific feature | 011 |
| `get_user_features(p_user_id)` | text[] | plpgsql | DEFINER | Get all enabled features for user | 011 |
| `update_conversation_last_message()` | trigger | plpgsql | INVOKER | Update conversations.last_message_at on new message | 012 |
| `sync_profile_plan_type()` | trigger | plpgsql | DEFINER | Auto-sync profiles.plan_type from user_subscriptions changes. **WARNING: References nonexistent `status` column** | 017 |
| `get_conversations_with_unread_count(...)` | TABLE(...) | plpgsql | DEFINER | Eliminates N+1 query in conversation list | 019 |
| `get_analytics_summary(...)` | TABLE(...) | plpgsql | DEFINER | Eliminates full-table-scan in analytics summary | 019 |
| `update_pipeline_updated_at()` | trigger | plpgsql | INVOKER | Set updated_at on pipeline_items | 025 |
| `cleanup_search_cache_per_user()` | trigger | plpgsql | DEFINER | Enforce max 5 cache entries per user | 026 |

### Triggers

| Trigger | Table | Event | Function |
|---------|-------|-------|----------|
| `on_auth_user_created` | `auth.users` | AFTER INSERT | `handle_new_user()` |
| `profiles_updated_at` | `profiles` | BEFORE UPDATE | `update_updated_at()` |
| `plan_features_updated_at` | `plan_features` | BEFORE UPDATE | `update_updated_at()` |
| `plans_updated_at` | `plans` | BEFORE UPDATE | `update_updated_at()` (migration 020) |
| `user_subscriptions_updated_at` | `user_subscriptions` | BEFORE UPDATE | `update_updated_at()` (migration 021) |
| `trg_sync_profile_plan_type` | `user_subscriptions` | AFTER INSERT OR UPDATE | `sync_profile_plan_type()` (migration 017) |
| `trg_update_conversation_last_message` | `messages` | AFTER INSERT | `update_conversation_last_message()` |
| `tr_pipeline_items_updated_at` | `pipeline_items` | BEFORE UPDATE | `update_pipeline_updated_at()` (migration 025) |
| `trg_cleanup_search_cache` | `search_results_cache` | AFTER INSERT | `cleanup_search_cache_per_user()` (migration 026) |

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
| profiles | 5 | 2 | 1 (trigram) |
| plans | 1 | 0 | 0 |
| user_subscriptions | 6 | 3 | 0 |
| search_sessions | 3 | 0 | 0 |
| monthly_quota | 3 | 0 | 0 |
| plan_features | 2 | 1 | 0 |
| stripe_webhook_events | 3 | 0 | 0 |
| conversations | 4 | 0 | 0 |
| messages | 4 | 2 | 0 |
| user_oauth_tokens | 3 | 0 | 0 |
| google_sheets_exports | 5 | 0 | 1 |
| audit_events | 5 | 1 | 0 |
| pipeline_items | 4 | 1 | 0 |
| search_results_cache | 3 | 0 | 0 |
| **TOTAL** | **~51** | **10** | **2** |

---

## Enums & Constraints

### CHECK Constraints

| Table | Constraint Name | Expression |
|-------|----------------|------------|
| profiles | `profiles_plan_type_check` | `plan_type IN ('free_trial', 'consultor_agil', 'maquina', 'sala_guerra', 'master')` |
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
| pipeline_items | (unnamed) | `stage IN ('descoberta', 'analise', 'preparando', 'enviada', 'resultado')` |

### UNIQUE Constraints

| Table | Constraint Name | Columns |
|-------|----------------|---------|
| monthly_quota | `unique_user_month` | `(user_id, month_year)` |
| plan_features | (unnamed) | `(plan_id, billing_period, feature_key)` |
| user_oauth_tokens | `unique_user_provider` | `(user_id, provider)` |
| pipeline_items | (unnamed) | `(user_id, pncp_id)` |
| search_results_cache | (unnamed) | `(user_id, params_hash)` |
| user_subscriptions | (partial unique index) | `stripe_subscription_id` WHERE NOT NULL |

### Foreign Keys

| Source Table | Column | Target Table | Target Column | On Delete | Notes |
|-------------|--------|-------------|---------------|-----------|-------|
| profiles | id | auth.users | id | CASCADE | Bridge table |
| user_subscriptions | user_id | profiles | id | CASCADE | |
| user_subscriptions | plan_id | plans | id | RESTRICT (default) | Intentional (migration 022 documents) |
| search_sessions | user_id | profiles | id | CASCADE | |
| monthly_quota | user_id | profiles | id | CASCADE | Changed from auth.users in migration 018 |
| plan_features | plan_id | plans | id | CASCADE | |
| conversations | user_id | profiles | id | CASCADE | |
| messages | conversation_id | conversations | id | CASCADE | |
| messages | sender_id | profiles | id | CASCADE | |
| user_oauth_tokens | user_id | profiles | id | CASCADE | Changed from auth.users in migration 018 |
| google_sheets_exports | user_id | profiles | id | CASCADE | Changed from auth.users in migration 018 |
| **pipeline_items** | **user_id** | **auth.users** | **id** | **CASCADE** | **NOT standardized -- should be profiles(id)** |
| **search_results_cache** | **user_id** | **auth.users** | **id** | **CASCADE** | **NOT standardized -- should be profiles(id)** |

---

## Row Level Security Policies

### profiles (RLS: ENABLED)

| Policy | Operation | Role | Expression |
|--------|-----------|------|------------|
| `profiles_select_own` | SELECT | public | `auth.uid() = id` |
| `profiles_update_own` | UPDATE | public | `auth.uid() = id` |
| `profiles_insert_own` | INSERT | authenticated | `auth.uid() = id` (migration 020) |
| `profiles_insert_service` | INSERT | service_role | `true` (migration 020) |

### plans (RLS: ENABLED)

| Policy | Operation | Role | Expression |
|--------|-----------|------|------------|
| `plans_select_all` | SELECT | public | `true` (public catalog) |

### user_subscriptions (RLS: ENABLED)

| Policy | Operation | Role | Expression |
|--------|-----------|------|------------|
| `subscriptions_select_own` | SELECT | public | `auth.uid() = user_id` |
| `Service role can manage subscriptions` | ALL | service_role | `true` (migration 016) |

### search_sessions (RLS: ENABLED)

| Policy | Operation | Role | Expression |
|--------|-----------|------|------------|
| `sessions_select_own` | SELECT | public | `auth.uid() = user_id` |
| `sessions_insert_own` | INSERT | public | `auth.uid() = user_id` |
| `Service role can manage search sessions` | ALL | service_role | `true` (migration 016 fixed TO service_role) |

### monthly_quota (RLS: ENABLED)

| Policy | Operation | Role | Expression |
|--------|-----------|------|------------|
| `Users can view own quota` | SELECT | public | `auth.uid() = user_id` |
| `Service role can manage quota` | ALL | service_role | `true` (migration 016 fixed TO service_role) |

### plan_features (RLS: ENABLED)

| Policy | Operation | Role | Expression |
|--------|-----------|------|------------|
| `plan_features_select_all` | SELECT | public | `true` (public catalog) |

### stripe_webhook_events (RLS: ENABLED)

| Policy | Operation | Role | Expression |
|--------|-----------|------|------------|
| `webhook_events_insert_service` | INSERT | public | `true` |
| `webhook_events_select_admin` | SELECT | public | `EXISTS (profiles WHERE id = auth.uid() AND is_admin = true)` (fixed in migration 016) |

### conversations (RLS: ENABLED)

| Policy | Operation | Role | Expression |
|--------|-----------|------|------------|
| `conversations_select_own` | SELECT | public | `user_id = auth.uid() OR is_admin(auth.uid())` |
| `conversations_insert_own` | INSERT | public | `auth.uid() = user_id` |
| `conversations_update_admin` | UPDATE | public | `is_admin(auth.uid())` |

### messages (RLS: ENABLED)

| Policy | Operation | Role | Expression |
|--------|-----------|------|------------|
| `messages_select` | SELECT | public | User owns conversation OR is admin |
| `messages_insert_user` | INSERT | public | sender_id = auth.uid() AND (owns conversation OR is admin) |
| `messages_update_read` | UPDATE | public | Owns conversation OR is admin |

### user_oauth_tokens (RLS: ENABLED)

| Policy | Operation | Role | Expression |
|--------|-----------|------|------------|
| `Users can view own OAuth tokens` | SELECT | public | `auth.uid() = user_id` |
| `Users can update own OAuth tokens` | UPDATE | public | `auth.uid() = user_id` |
| `Users can delete own OAuth tokens` | DELETE | public | `auth.uid() = user_id` |
| `Service role can manage all OAuth tokens` | ALL | service_role | `true` |

### google_sheets_exports (RLS: ENABLED)

| Policy | Operation | Role | Expression |
|--------|-----------|------|------------|
| `Users can view own Google Sheets exports` | SELECT | public | `auth.uid() = user_id` |
| `Users can create Google Sheets exports` | INSERT | public | `auth.uid() = user_id` |
| `Users can update own Google Sheets exports` | UPDATE | public | `auth.uid() = user_id` |
| `Service role can manage all Google Sheets exports` | ALL | service_role | `true` |

### audit_events (RLS: ENABLED)

| Policy | Operation | Role | Expression |
|--------|-----------|------|------------|
| `Service role can manage audit events` | ALL | service_role | `true` |
| `Admins can read audit events` | SELECT | public | `EXISTS (profiles WHERE id = auth.uid() AND is_admin = true)` |

### pipeline_items (RLS: ENABLED)

| Policy | Operation | Role | Expression |
|--------|-----------|------|------------|
| `Users can view own pipeline items` | SELECT | public | `auth.uid() = user_id` |
| `Users can insert own pipeline items` | INSERT | public | `auth.uid() = user_id` |
| `Users can update own pipeline items` | UPDATE | public | `auth.uid() = user_id` (USING + WITH CHECK) |
| `Users can delete own pipeline items` | DELETE | public | `auth.uid() = user_id` |
| `Service role full access on pipeline_items` | ALL | **public** | `true` **-- SECURITY: missing `TO service_role`** |

### search_results_cache (RLS: ENABLED)

| Policy | Operation | Role | Expression |
|--------|-----------|------|------------|
| `Users can read own search cache` | SELECT | public | `auth.uid() = user_id` |
| `Service role full access on search_results_cache` | ALL | **public** | `true` **-- SECURITY: missing `TO service_role`** |

---

## Data Access Patterns

### Backend Client

The backend uses the **Supabase Python Client** (`supabase_client.py`) as the primary database access mechanism:
- Uses `SUPABASE_SERVICE_ROLE_KEY` (admin privileges, bypasses RLS)
- Singleton pattern via `get_supabase()`
- FastAPI dependency injection via `database.py:get_db()`

**Tables accessed by each module:**

| Backend Module | Tables Accessed | Operations |
|----------------|----------------|------------|
| `quota.py` | profiles, plans, user_subscriptions, monthly_quota, search_sessions | SELECT, INSERT, UPDATE, RPC |
| `admin.py` | profiles, user_subscriptions, plans | SELECT (with JOIN), UPDATE, INSERT |
| `auth.py` / `authorization.py` | profiles | SELECT |
| `audit.py` | audit_events | INSERT |
| `oauth.py` | user_oauth_tokens | SELECT, INSERT (upsert), UPDATE, DELETE |
| `routes/analytics.py` | search_sessions | RPC (get_analytics_summary), SELECT |
| `routes/billing.py` | plans, user_subscriptions, profiles | SELECT, INSERT, UPDATE |
| `routes/messages.py` | conversations, messages | SELECT, INSERT, UPDATE, RPC (get_conversations_with_unread_count) |
| `routes/pipeline.py` | pipeline_items | SELECT, INSERT, UPDATE, DELETE |
| `routes/export_sheets.py` | google_sheets_exports | SELECT, INSERT |
| `routes/features.py` | user_subscriptions, plan_features | SELECT |
| `routes/sessions.py` | search_sessions | SELECT |
| `routes/user.py` | profiles, user_subscriptions | SELECT, UPDATE |
| `routes/plans.py` | plans | SELECT |
| `routes/emails.py` | profiles | SELECT, UPDATE |
| `search_pipeline.py` | profiles | SELECT |

### RPC Function Usage (Backend)

| RPC Function | Called By | Purpose |
|-------------|----------|---------|
| `increment_quota_atomic` | `quota.py:increment_monthly_quota()` | Atomic quota increment |
| `check_and_increment_quota` | `quota.py:check_and_increment_quota_atomic()` | Atomic check+increment |
| `get_analytics_summary` | `routes/analytics.py:get_analytics_summary()` | Aggregated user stats |
| `get_conversations_with_unread_count` | `routes/messages.py:list_conversations()` | Conversations with counts |

---

## pg_cron Scheduled Jobs

| Job Name | Schedule | Action | Retention | Migration |
|----------|----------|--------|-----------|-----------|
| `cleanup-monthly-quota` | `0 2 1 * *` (1st of month, 2:00 AM UTC) | DELETE rows older than 24 months | 24 months | 022 |
| `cleanup-webhook-events` | `0 3 * * *` (daily, 3:00 AM UTC) | DELETE rows older than 90 days | 90 days | 022 |
| `cleanup-audit-events` | `0 4 1 * *` (1st of month, 4:00 AM UTC) | DELETE rows older than 12 months | 12 months | 023 |

**NOTE:** pg_cron extension must be enabled by Supabase support. Jobs will fail silently if extension is not installed.

---

## Migration History

| # | File | Date | Story/Issue | Summary |
|---|------|------|-------------|---------|
| 001 | `001_profiles_and_sessions.sql` | - | - | Core schema: profiles, plans, user_subscriptions, search_sessions, RLS, triggers |
| 002 | `002_monthly_quota.sql` | 2026-02-03 | PNCP-165 | monthly_quota table |
| 003 | `003_atomic_quota_increment.sql` | 2026-02-04 | Issue #189 | Atomic quota functions |
| 004 | `004_add_is_admin.sql` | - | - | profiles.is_admin column |
| 005 | `005_update_plans_to_new_tiers.sql` | 2026-02-05 | - | New pricing tiers, deactivate legacy plans |
| 006a | `006a_update_profiles_plan_type_constraint.sql` | 2026-02-06 | - | Update CHECK constraint for new plan types |
| 006b | `006b_search_sessions_service_role_policy.sql` | 2026-02-10 | P0-CRITICAL | Service role policy for search_sessions |
| - | `006b_DEPRECATED_...DUPLICATE.sql` | - | - | Deprecated duplicate of 006b (DO NOT APPLY) |
| 007 | `007_add_whatsapp_consent.sql` | - | STORY-166 | Marketing consent fields, updated handle_new_user trigger |
| 008 | `008_add_billing_period.sql` | 2026-02-07 | STORY-171 | billing_period + annual_benefits on user_subscriptions |
| - | `008_rollback.sql.bak` | 2026-02-07 | STORY-171 | Rollback script for 008 (reference only) |
| 009 | `009_create_plan_features.sql` | 2026-02-07 | STORY-171 | plan_features table + seed data |
| 010 | `010_stripe_webhook_events.sql` | - | STORY-171 | stripe_webhook_events table |
| 011 | `011_add_billing_helper_functions.sql` | 2026-02-07 | STORY-171 | Billing helper DB functions |
| 012 | `012_create_messages.sql` | - | - | conversations + messages tables (InMail) |
| 013 | `013_google_oauth_tokens.sql` | - | STORY-180 | user_oauth_tokens table |
| 014 | `014_google_sheets_exports.sql` | - | STORY-180 | google_sheets_exports table |
| 015 | `015_add_stripe_price_ids_monthly_annual.sql` | 2026-02-10 | - | Stripe price ID columns on plans |
| 016 | `016_security_and_index_fixes.sql` | 2026-02-11 | STORY-200 | Fix webhook admin policy, tighten RLS, stripe_sub_id index, trigram index, service role policies, fix handle_new_user default |
| 017 | `017_sync_plan_type_trigger.sql` | - | STORY-202 | Auto-sync profiles.plan_type trigger (references missing `status` column) |
| 018 | `018_standardize_fk_references.sql` | - | STORY-202 | Standardize FKs to profiles(id) for monthly_quota, user_oauth_tokens, google_sheets_exports |
| 019 | `019_rpc_performance_functions.sql` | - | STORY-202 | RPC functions: get_conversations_with_unread_count, get_analytics_summary |
| 020 | `020_tighten_plan_type_constraint.sql` | 2026-02-12 | STORY-203 | Remove legacy plan_type values, add INSERT policies, add plans.updated_at |
| 021 | `021_user_subscriptions_updated_at.sql` | 2026-02-12 | STORY-203 | Add updated_at to user_subscriptions, document Stripe price ID env awareness |
| 022 | `022_retention_cleanup.sql` | 2026-02-12 | STORY-203 | pg_cron cleanup jobs, drop redundant index, add customer_id index, document plan_id FK |
| 023 | `023_audit_events.sql` | 2026-02-13 | STORY-226 | audit_events table with hashed PII, pg_cron retention |
| 024 | `024_add_profile_context.sql` | - | STORY-247 | profiles.context_data JSONB column, updated handle_new_user |
| 025 | `025_create_pipeline_items.sql` | - | STORY-250 | pipeline_items table for opportunity tracking |
| 026 | `026_search_results_cache.sql` | - | STORY-257A | search_results_cache table with auto-cleanup trigger |

---

## Environment Variables for Database

| Variable | Required | Used By | Purpose |
|----------|----------|---------|---------|
| `SUPABASE_URL` | YES | supabase_client.py | Supabase project URL |
| `SUPABASE_ANON_KEY` | YES | supabase_client.py | Public anonymous key (frontend JWT verify) |
| `SUPABASE_SERVICE_ROLE_KEY` | YES | supabase_client.py | Admin access key (bypasses RLS) |
| `SUPABASE_JWT_SECRET` | YES | auth.py | JWT token verification |
| `ENCRYPTION_KEY` | Recommended | oauth.py | AES-256 key for OAuth token encryption |
| `REDIS_URL` | Optional | routes/features.py | Feature flag cache |

---

## Database Size Estimates

| Table | Expected Row Count (1 year) | Growth Pattern |
|-------|---------------------------|----------------|
| profiles | 500-5,000 | Linear with signups |
| plans | 10-15 | Static (manual changes) |
| user_subscriptions | 1,000-10,000 | Linear (new subs + historical) |
| search_sessions | 10,000-100,000 | **High growth** (every search) |
| monthly_quota | 500-60,000 | Linear (users x months), cleaned after 24 months |
| plan_features | 10-50 | Static (manual changes) |
| stripe_webhook_events | 1,000-50,000 | Linear, cleaned after 90 days |
| conversations | 100-1,000 | Low growth |
| messages | 500-5,000 | Low-medium growth |
| user_oauth_tokens | 100-2,000 | Linear with Google integrations |
| google_sheets_exports | 500-10,000 | Moderate growth |
| audit_events | 5,000-100,000 | **High growth** (every auth/search event), cleaned after 12 months |
| pipeline_items | 1,000-20,000 | Moderate growth (user pipeline actions) |
| search_results_cache | 500-25,000 | Self-limiting (max 5 per user via trigger) |

**Largest tables to monitor:** `search_sessions`, `audit_events`, `search_results_cache` (JSONB payload size)
