# SmartLic Database Schema Reference

**Date:** 2026-03-20 | **Auditor:** @data-engineer (Brownfield Discovery Phase 2)
**Supabase Project:** fqqyovlzdzimiwfofdjk | **PostgreSQL:** 17
**Migrations:** 86 files in `supabase/migrations/`
**Tables:** 32 public tables | **Functions:** 12 | **Triggers:** 14 | **pg_cron Jobs:** 13

---

## Table of Contents

1. [Entity-Relationship Overview](#1-entity-relationship-overview)
2. [Tables — Full Column Reference](#2-tables--full-column-reference)
3. [RLS Policies](#3-rls-policies)
4. [Indexes](#4-indexes)
5. [Functions and Triggers](#5-functions-and-triggers)
6. [pg_cron Retention Jobs](#6-pgcron-retention-jobs)
7. [Key Access Patterns](#7-key-access-patterns)
8. [Custom Types](#8-custom-types)

---

## 1. Entity-Relationship Overview

```
auth.users (Supabase managed)
    |
    | 1:1 (ON DELETE CASCADE, via handle_new_user trigger)
    v
profiles --------> plans (plan_type FK via CHECK constraint, not FK)
    |                |
    |                |---> plan_billing_periods (plan_id FK)
    |                |---> plan_features (plan_id FK)
    |
    |----> user_subscriptions (user_id FK, plan_id FK to plans)
    |----> monthly_quota (user_id FK)
    |----> search_sessions (user_id FK)
    |          |---> search_state_transitions (search_id correlation, no FK)
    |
    |----> search_results_cache (user_id FK)
    |----> search_results_store (user_id FK)
    |----> pipeline_items (user_id FK)
    |----> classification_feedback (user_id FK)
    |
    |----> conversations (user_id FK)
    |          |---> messages (conversation_id FK, sender_id FK to profiles)
    |
    |----> alerts (user_id FK)
    |          |---> alert_sent_items (alert_id FK)
    |          |---> alert_runs (alert_id FK)
    |
    |----> alert_preferences (user_id FK, 1:1)
    |----> user_oauth_tokens (user_id FK)
    |----> google_sheets_exports (user_id FK)
    |----> trial_email_log (user_id FK)
    |----> mfa_recovery_codes (user_id FK)
    |----> mfa_recovery_attempts (user_id FK)
    |
    |----> organizations (owner_id FK, ON DELETE RESTRICT)
    |          |---> organization_members (org_id FK, user_id FK to profiles)
    |
    |----> partners (no FK to profiles, contact_email link)
    |          |---> partner_referrals (partner_id FK, referred_user_id FK to profiles)

Standalone:
    stripe_webhook_events (no user FK, evt_ PK)
    audit_events (hashed actor IDs, no FK)
    health_checks (no user FK, service_role only)
    incidents (no user FK, service_role only)
    reconciliation_log (no user FK, admin only)
```

---

## 2. Tables -- Full Column Reference

### 2.1 Core / Auth

#### `profiles`
Extends auth.users. Created automatically via `handle_new_user()` trigger on signup.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | - | PK, FK -> auth.users(id) ON DELETE CASCADE |
| `email` | text | NO | - | UNIQUE (partial index) |
| `full_name` | text | YES | - | |
| `company` | text | YES | - | |
| `sector` | text | YES | - | |
| `phone_whatsapp` | text | YES | - | CHECK regex `^[0-9]{10,11}$`, UNIQUE (partial) |
| `whatsapp_consent` | boolean | YES | false | |
| `whatsapp_consent_at` | timestamptz | YES | - | |
| `plan_type` | text | NO | 'free_trial' | CHECK IN ('free_trial','consultor_agil','maquina','sala_guerra','master','smartlic_pro','consultoria') |
| `avatar_url` | text | YES | - | |
| `is_admin` | boolean | NO | false | |
| `context_data` | jsonb | YES | '{}' | Onboarding wizard data |
| `subscription_status` | text | YES | 'trial' | CHECK IN ('trial','active','canceling','past_due','expired') |
| `trial_expires_at` | timestamptz | YES | - | |
| `subscription_end_date` | timestamptz | YES | - | |
| `email_unsubscribed` | boolean | YES | false | |
| `email_unsubscribed_at` | timestamptz | YES | - | |
| `marketing_emails_enabled` | boolean | NO | true | |
| `referred_by_partner_id` | uuid | YES | - | FK -> partners(id) |
| `created_at` | timestamptz | NO | now() | |
| `updated_at` | timestamptz | NO | now() | Auto-updated via trigger |

#### `user_subscriptions`
Tracks Stripe subscriptions and purchased packs per user.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `user_id` | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| `plan_id` | text | NO | - | FK -> plans(id) ON DELETE RESTRICT |
| `credits_remaining` | int | YES | - | null = unlimited |
| `starts_at` | timestamptz | NO | now() | |
| `expires_at` | timestamptz | YES | - | null = never expires |
| `stripe_subscription_id` | text | YES | - | UNIQUE (partial, WHERE NOT NULL) |
| `stripe_customer_id` | text | YES | - | Indexed (partial) |
| `is_active` | boolean | NO | true | |
| `billing_period` | varchar(10) | NO | 'monthly' | CHECK IN ('monthly','semiannual','annual') |
| `annual_benefits` | jsonb | NO | '{}' | |
| `subscription_status` | text | YES | 'active' | CHECK IN ('active','trialing','past_due','canceled','expired') |
| `first_failed_at` | timestamptz | YES | - | Dunning tracking |
| `version` | integer | NO | 1 | Optimistic locking |
| `created_at` | timestamptz | NO | now() | |
| `updated_at` | timestamptz | NO | now() | Auto-updated via trigger |

#### `monthly_quota`
Tracks monthly search usage per user. Lazy-reset (new row per month_year).

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `user_id` | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| `month_year` | varchar(7) | NO | - | Format: "YYYY-MM" |
| `searches_count` | int | NO | 0 | |
| `created_at` | timestamptz | NO | now() | |
| `updated_at` | timestamptz | NO | now() | |

UNIQUE constraint: `(user_id, month_year)`

#### `user_oauth_tokens`
Encrypted OAuth 2.0 tokens for Google Sheets integration.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `user_id` | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| `provider` | varchar(50) | NO | - | CHECK IN ('google','microsoft','dropbox') |
| `access_token` | text | NO | - | AES-256 encrypted |
| `refresh_token` | text | YES | - | AES-256 encrypted |
| `expires_at` | timestamptz | NO | - | |
| `scope` | text | NO | - | |
| `created_at` | timestamptz | YES | now() | |
| `updated_at` | timestamptz | YES | now() | |

UNIQUE constraint: `(user_id, provider)`

#### `mfa_recovery_codes`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `user_id` | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| `code_hash` | text | NO | - | bcrypt hashed |
| `used_at` | timestamptz | YES | - | |
| `created_at` | timestamptz | NO | now() | |

#### `mfa_recovery_attempts`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `user_id` | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| `attempted_at` | timestamptz | NO | now() | |
| `success` | boolean | NO | false | |

---

### 2.2 Search / Pipeline

#### `search_sessions`
Records every search attempt (success, failure, timeout).

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `user_id` | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| `search_id` | uuid | YES | - | Correlation ID for SSE/ARQ/cache |
| `sectors` | text[] | NO | - | |
| `ufs` | text[] | NO | - | |
| `data_inicial` | date | NO | - | |
| `data_final` | date | NO | - | |
| `custom_keywords` | text[] | YES | - | |
| `total_raw` | int | NO | 0 | |
| `total_filtered` | int | NO | 0 | |
| `valor_total` | numeric(14,2) | YES | 0 | |
| `resumo_executivo` | text | YES | - | |
| `destaques` | text[] | YES | - | |
| `excel_storage_path` | text | YES | - | |
| `status` | text | NO | 'created' | CHECK IN ('created','processing','completed','failed','timed_out','cancelled') |
| `error_message` | text | YES | - | |
| `error_code` | text | YES | - | |
| `started_at` | timestamptz | NO | now() | |
| `completed_at` | timestamptz | YES | - | |
| `duration_ms` | integer | YES | - | |
| `pipeline_stage` | text | YES | - | |
| `raw_count` | integer | YES | 0 | |
| `response_state` | text | YES | - | live/cached/degraded/empty_failure |
| `failed_ufs` | text[] | YES | - | |
| `created_at` | timestamptz | NO | now() | |

#### `search_state_transitions`
Audit trail for search state machine. Fire-and-forget inserts.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `search_id` | uuid | NO | - | No FK (app-layer integrity) |
| `user_id` | uuid | YES | - | FK -> profiles(id) ON DELETE CASCADE |
| `from_state` | text | YES | - | |
| `to_state` | text | NO | - | |
| `stage` | text | YES | - | |
| `details` | jsonb | YES | '{}' | |
| `duration_since_previous_ms` | integer | YES | - | |
| `created_at` | timestamptz | NO | now() | |

#### `search_results_cache`
L2 persistent cache (Supabase layer of two-level cache). Max 10 entries per user.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `user_id` | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| `params_hash` | text | NO | - | |
| `params_hash_global` | text | YES | - | Cross-user cache sharing |
| `search_params` | jsonb | NO | - | |
| `results` | jsonb | NO | - | CHECK octet_length <= 2MB |
| `total_results` | integer | NO | 0 | |
| `sources_json` | jsonb | NO | '["pncp"]' | |
| `fetched_at` | timestamptz | NO | now() | |
| `priority` | text | NO | 'cold' | CHECK IN ('hot','warm','cold') |
| `access_count` | integer | NO | 0 | |
| `last_accessed_at` | timestamptz | YES | - | |
| `last_success_at` | timestamptz | YES | - | |
| `last_attempt_at` | timestamptz | YES | - | |
| `fail_streak` | integer | NO | 0 | |
| `degraded_until` | timestamptz | YES | - | |
| `coverage` | jsonb | YES | - | |
| `fetch_duration_ms` | integer | YES | - | |
| `created_at` | timestamptz | NO | now() | |

UNIQUE constraint: `(user_id, params_hash)`

#### `search_results_store`
L3 persistent storage. Prevents "Busca nao encontrada" after L1/L2 TTL expiry.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `search_id` | uuid | NO | - | PK |
| `user_id` | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| `results` | jsonb | NO | - | CHECK octet_length < 2MB |
| `sector` | text | YES | - | |
| `ufs` | text[] | YES | - | |
| `total_filtered` | int | YES | 0 | |
| `created_at` | timestamptz | YES | now() | |
| `expires_at` | timestamptz | YES | now() + 24h | |

#### `pipeline_items`
Opportunity pipeline (kanban board). One item per user per PNCP ID.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `user_id` | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| `pncp_id` | text | NO | - | |
| `objeto` | text | NO | - | |
| `orgao` | text | YES | - | |
| `uf` | text | YES | - | |
| `valor_estimado` | numeric | YES | - | |
| `data_encerramento` | timestamptz | YES | - | |
| `link_pncp` | text | YES | - | |
| `stage` | text | NO | 'descoberta' | CHECK IN ('descoberta','analise','preparando','enviada','resultado') |
| `notes` | text | YES | - | |
| `search_id` | text | YES | - | Traceability to search origin |
| `version` | integer | NO | 1 | Optimistic locking |
| `created_at` | timestamptz | NO | now() | |
| `updated_at` | timestamptz | NO | now() | Auto-updated via trigger |

UNIQUE constraint: `(user_id, pncp_id)`

#### `classification_feedback`
User feedback on AI classification accuracy.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `user_id` | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| `search_id` | uuid | NO | - | |
| `bid_id` | text | NO | - | |
| `setor_id` | text | NO | - | |
| `user_verdict` | text | NO | - | CHECK IN ('false_positive','false_negative','correct') |
| `reason` | text | YES | - | |
| `category` | text | YES | - | CHECK IN ('wrong_sector','irrelevant_modality','too_small','too_large','closed','other') |
| `bid_objeto` | text | YES | - | |
| `bid_valor` | decimal | YES | - | |
| `bid_uf` | text | YES | - | |
| `confidence_score` | integer | YES | - | |
| `relevance_source` | text | YES | - | |
| `created_at` | timestamptz | YES | now() | |

UNIQUE constraint: `(user_id, search_id, bid_id)`

---

### 2.3 Billing

#### `plans`
Plan catalog. Source of truth for plan definitions.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | text | NO | - | PK |
| `name` | text | NO | - | |
| `description` | text | YES | - | |
| `max_searches` | int | YES | - | null = unlimited |
| `price_brl` | numeric(10,2) | NO | 0 | |
| `duration_days` | int | YES | - | null = perpetual |
| `stripe_price_id` | text | YES | - | DEPRECATED — use period-specific columns |
| `stripe_price_id_monthly` | text | YES | - | |
| `stripe_price_id_semiannual` | text | YES | - | |
| `stripe_price_id_annual` | text | YES | - | |
| `is_active` | boolean | NO | true | |
| `created_at` | timestamptz | NO | now() | |
| `updated_at` | timestamptz | NO | now() | Auto-updated via trigger |

Active plans: `free` (inactive), `smartlic_pro`, `consultoria`, `master`. Legacy: `consultor_agil`, `maquina`, `sala_guerra` (inactive).

#### `plan_billing_periods`
Multi-period pricing for each plan. Source of truth for Stripe price IDs.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `plan_id` | text | NO | - | FK -> plans(id) ON DELETE CASCADE |
| `billing_period` | text | NO | - | CHECK IN ('monthly','semiannual','annual') |
| `price_cents` | integer | NO | - | |
| `discount_percent` | integer | YES | 0 | |
| `stripe_price_id` | text | YES | - | |
| `created_at` | timestamptz | YES | now() | |
| `updated_at` | timestamptz | YES | now() | Auto-updated via trigger |

UNIQUE constraint: `(plan_id, billing_period)`

#### `plan_features`
Billing-period-specific feature flags.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | serial | NO | - | PK |
| `plan_id` | text | NO | - | FK -> plans(id) ON DELETE CASCADE |
| `billing_period` | varchar(10) | NO | - | CHECK IN ('monthly','semiannual','annual') |
| `feature_key` | varchar(100) | NO | - | |
| `enabled` | boolean | NO | true | |
| `metadata` | jsonb | YES | '{}' | |
| `created_at` | timestamptz | NO | now() | |
| `updated_at` | timestamptz | NO | now() | Auto-updated via trigger |

UNIQUE constraint: `(plan_id, billing_period, feature_key)`

#### `stripe_webhook_events`
Idempotency store for Stripe webhook processing.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | varchar(255) | NO | - | PK, CHECK starts with `evt_` |
| `type` | varchar(100) | NO | - | |
| `processed_at` | timestamptz | NO | now() | |
| `payload` | jsonb | YES | - | |
| `status` | varchar(20) | NO | 'completed' | |
| `received_at` | timestamptz | YES | now() | |

#### `reconciliation_log`
Stripe-to-DB sync audit trail.

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `run_at` | timestamptz | NO | now() | |
| `total_checked` | int | NO | 0 | |
| `divergences_found` | int | NO | 0 | |
| `auto_fixed` | int | NO | 0 | |
| `manual_review` | int | NO | 0 | |
| `duration_ms` | int | NO | 0 | |
| `details` | jsonb | YES | '[]' | |

---

### 2.4 Communication

#### `conversations`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `user_id` | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| `subject` | text | NO | - | CHECK length <= 200 |
| `category` | text | NO | - | CHECK IN ('suporte','sugestao','funcionalidade','bug','outro') |
| `status` | text | NO | 'aberto' | CHECK IN ('aberto','respondido','resolvido') |
| `first_response_at` | timestamptz | YES | - | SLA tracking |
| `last_message_at` | timestamptz | NO | now() | |
| `created_at` | timestamptz | NO | now() | |
| `updated_at` | timestamptz | NO | now() | |

#### `messages`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `conversation_id` | uuid | NO | - | FK -> conversations(id) ON DELETE CASCADE |
| `sender_id` | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| `body` | text | NO | - | CHECK length between 1 and 5000 |
| `is_admin_reply` | boolean | NO | false | |
| `read_by_user` | boolean | NO | false | |
| `read_by_admin` | boolean | NO | false | |
| `created_at` | timestamptz | NO | now() | |

#### `alerts`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `user_id` | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| `name` | text | NO | '' | |
| `filters` | jsonb | NO | '{}' | |
| `active` | boolean | NO | true | |
| `created_at` | timestamptz | NO | now() | |
| `updated_at` | timestamptz | NO | now() | Auto-updated via trigger |

#### `alert_preferences`
One row per user (1:1 with profiles, auto-created on profile insert).

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `user_id` | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE, UNIQUE |
| `frequency` | alert_frequency | NO | 'daily' | ENUM: daily, twice_weekly, weekly, off |
| `enabled` | boolean | NO | true | |
| `last_digest_sent_at` | timestamptz | YES | - | |
| `created_at` | timestamptz | NO | now() | |
| `updated_at` | timestamptz | NO | now() | Auto-updated via trigger |

#### `alert_sent_items`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `alert_id` | uuid | NO | - | FK -> alerts(id) ON DELETE CASCADE |
| `item_id` | text | NO | - | |
| `sent_at` | timestamptz | NO | now() | |

UNIQUE constraint: `(alert_id, item_id)`

#### `alert_runs`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `alert_id` | uuid | NO | - | FK -> alerts(id) ON DELETE CASCADE |
| `run_at` | timestamptz | NO | now() | |
| `items_found` | integer | NO | 0 | |
| `items_sent` | integer | NO | 0 | |
| `status` | text | NO | 'pending' | CHECK IN ('pending','running','completed','failed','matched','no_results','no_match','all_deduped','error') |

---

### 2.5 Multi-Tenant / Partners

#### `organizations`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `name` | text | NO | - | |
| `logo_url` | text | YES | - | |
| `owner_id` | uuid | NO | - | FK -> profiles(id) ON DELETE RESTRICT |
| `max_members` | int | NO | 5 | |
| `plan_type` | text | NO | 'consultoria' | CHECK for valid plan types |
| `stripe_customer_id` | text | YES | - | |
| `created_at` | timestamptz | NO | now() | |
| `updated_at` | timestamptz | NO | now() | Auto-updated via trigger |

#### `organization_members`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `org_id` | uuid | NO | - | FK -> organizations(id) ON DELETE CASCADE |
| `user_id` | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| `role` | text | NO | 'member' | CHECK IN ('owner','admin','member') |
| `invited_at` | timestamptz | NO | now() | |
| `accepted_at` | timestamptz | YES | - | NULL = pending |

UNIQUE constraint: `(org_id, user_id)`

#### `partners`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `name` | text | NO | - | |
| `slug` | text | NO | - | UNIQUE |
| `contact_email` | text | NO | - | |
| `contact_name` | text | YES | - | |
| `stripe_coupon_id` | text | YES | - | |
| `revenue_share_pct` | numeric(5,2) | YES | 25.00 | |
| `status` | text | YES | 'active' | CHECK IN ('active','inactive','pending') |
| `created_at` | timestamptz | NO | now() | |
| `updated_at` | timestamptz | NO | now() | Auto-updated via trigger |

#### `partner_referrals`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `partner_id` | uuid | NO | - | FK -> partners(id) ON DELETE CASCADE |
| `referred_user_id` | uuid | YES | - | FK -> profiles(id) ON DELETE SET NULL |
| `signup_at` | timestamptz | YES | now() | |
| `converted_at` | timestamptz | YES | - | |
| `churned_at` | timestamptz | YES | - | |
| `monthly_revenue` | numeric(10,2) | YES | - | |
| `revenue_share_amount` | numeric(10,2) | YES | - | |

UNIQUE constraint: `(partner_id, referred_user_id)`

---

### 2.6 Operational

#### `audit_events`
Persistent audit log. All PII stored as SHA-256 hashes (16 hex chars).

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `timestamp` | timestamptz | NO | now() | |
| `event_type` | text | NO | - | |
| `actor_id_hash` | text | YES | - | |
| `target_id_hash` | text | YES | - | |
| `details` | jsonb | YES | - | |
| `ip_hash` | text | YES | - | |

#### `health_checks`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `checked_at` | timestamptz | NO | now() | |
| `overall_status` | text | NO | - | CHECK IN ('healthy','degraded','unhealthy') |
| `sources_json` | jsonb | NO | '{}' | |
| `components_json` | jsonb | NO | '{}' | |
| `latency_ms` | integer | YES | - | |

#### `incidents`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `started_at` | timestamptz | NO | now() | |
| `resolved_at` | timestamptz | YES | - | |
| `status` | text | NO | 'ongoing' | CHECK IN ('ongoing','resolved') |
| `affected_sources` | text[] | NO | '{}' | |
| `description` | text | NO | '' | |
| `updated_at` | timestamptz | NO | now() | Auto-updated via trigger |

#### `trial_email_log`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `user_id` | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| `email_type` | text | NO | - | |
| `email_number` | integer | YES | - | CHECK 1-6 |
| `sent_at` | timestamptz | NO | now() | |
| `opened_at` | timestamptz | YES | - | Resend webhook |
| `clicked_at` | timestamptz | YES | - | Resend webhook |
| `resend_email_id` | text | YES | - | |

UNIQUE constraint: `(user_id, email_number)`

#### `google_sheets_exports`

| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| `id` | uuid | NO | gen_random_uuid() | PK |
| `user_id` | uuid | NO | - | FK -> profiles(id) ON DELETE CASCADE |
| `spreadsheet_id` | varchar(255) | NO | - | |
| `spreadsheet_url` | text | NO | - | |
| `search_params` | jsonb | NO | - | GIN index |
| `total_rows` | int | NO | - | CHECK >= 0 |
| `created_at` | timestamptz | NO | now() | |
| `updated_at` | timestamptz | NO | now() | Auto-updated via trigger |

---

## 3. RLS Policies

All 32 tables have RLS enabled. Policies follow a standardized pattern after 4 rounds of hardening (migrations 016, TD-003, DEBT-009, DEBT-113).

### Pattern Summary

| Pattern | Tables | Description |
|---------|--------|-------------|
| User owns rows | 20 tables | `auth.uid() = user_id` for SELECT/INSERT/UPDATE/DELETE |
| Service role ALL | All 32 tables | `TO service_role USING (true) WITH CHECK (true)` |
| Public read | plans, plan_features, plan_billing_periods | `FOR SELECT USING (true)` |
| Admin read | stripe_webhook_events, audit_events, reconciliation_log | `EXISTS (SELECT 1 FROM profiles WHERE ... is_admin = true)` |
| Service-only | health_checks, incidents, trial_email_log | No user-facing policies |

### Notable Policies

- **conversations/messages**: Users see own + admins see all (admin check via profiles.is_admin)
- **alert_sent_items**: Users can SELECT via join to alerts (verify ownership)
- **organizations**: Owner + admin members can SELECT; INSERT requires owner_id match
- **organization_members**: Self-referencing RLS (members check own membership role)
- **partners**: Admin ALL + self-read via contact_email match to auth.users email
- **search_state_transitions**: Users read via `user_id = auth.uid()` (optimized from correlated subquery)

---

## 4. Indexes

### Counts by Table (most indexed)

| Table | Index Count | Notable |
|-------|-------------|---------|
| search_results_cache | 7 | Priority, degraded, global hash, params hash |
| search_sessions | 5 | User+status+created composite, search_id, inflight |
| user_subscriptions | 5 | Stripe sub ID (unique), customer ID, billing |
| pipeline_items | 4 | User+stage, encerramento, search_id |
| profiles | 4 | Email trigram, admin, phone unique, subscription status |
| conversations | 4 | User, status, last_message, status+last_msg composite |
| messages | 3 | Conversation+created, unread by user, unread by admin |
| alerts | 2 | User, active |
| alert_sent_items | 3 | Dedup (unique), alert_id, sent_at |

### Key Indexes for Performance

- `idx_profiles_email_trgm` (GIN trigram) -- admin ILIKE search
- `idx_search_sessions_user_status_created` -- composite for history queries
- `idx_search_cache_priority` -- priority-based eviction
- `idx_search_cache_global_hash` -- cross-user cache fallback
- `idx_user_subscriptions_stripe_sub_id` -- unique partial, webhook processing
- `idx_conversations_status_last_msg` -- admin inbox composite
- `idx_messages_unread_by_user` / `idx_messages_unread_by_admin` -- partial indexes for badge counts

---

## 5. Functions and Triggers

### RPC Functions

| Function | Purpose | Called By |
|----------|---------|----------|
| `check_and_increment_quota(uuid, varchar, int)` | Atomic quota check + increment | `quota.py` |
| `increment_quota_atomic(uuid, varchar, int)` | Simpler atomic increment | `quota.py` fallback |
| `increment_quota_fallback_atomic(uuid, text, int)` | Lightweight fallback | `quota.py` |
| `get_conversations_with_unread_count(...)` | Conversations + unread in single query | `routes/messages.py` |
| `get_analytics_summary(uuid, timestamptz, timestamptz)` | Analytics aggregation | `routes/analytics.py` |
| `get_user_billing_period(uuid)` | Current billing period | Billing helpers |
| `user_has_feature(uuid, varchar)` | Feature flag check | Billing helpers |
| `get_user_features(uuid)` | All features for user | Billing helpers |
| `get_table_columns_simple(text)` | Schema validation | Backend startup |
| `pg_total_relation_size_safe(text)` | Safe table size query | Prometheus metrics |

### Trigger Functions

| Function | Triggers On | Purpose |
|----------|-------------|---------|
| `handle_new_user()` | auth.users INSERT | Auto-create profile with phone normalization |
| `set_updated_at()` | 10 tables (UPDATE) | Canonical updated_at auto-update |
| `update_conversation_last_message()` | messages INSERT | Update conversation.last_message_at |
| `cleanup_search_cache_per_user()` | search_results_cache INSERT | Evict beyond 5 entries (short-circuit at <=5) |
| `create_default_alert_preferences()` | profiles INSERT | Auto-create alert_preferences row |

### Triggers by Table

| Table | Trigger | Function |
|-------|---------|----------|
| auth.users | on_auth_user_created | handle_new_user() |
| profiles | profiles_updated_at | set_updated_at() |
| profiles | trigger_create_alert_preferences_on_profile | create_default_alert_preferences() |
| plans | plans_updated_at | set_updated_at() |
| plan_features | plan_features_updated_at | set_updated_at() |
| plan_billing_periods | trg_plan_billing_periods_updated_at | set_updated_at() |
| user_subscriptions | user_subscriptions_updated_at | set_updated_at() |
| pipeline_items | tr_pipeline_items_updated_at | set_updated_at() |
| organizations | tr_organizations_updated_at | set_updated_at() |
| alerts | trigger_alerts_updated_at | set_updated_at() |
| alert_preferences | trigger_alert_preferences_updated_at | set_updated_at() |
| incidents | trg_incidents_updated_at | set_updated_at() |
| partners | trg_partners_updated_at | set_updated_at() |
| google_sheets_exports | trg_google_sheets_exports_updated_at | set_updated_at() |
| conversations | trg_update_conversation_last_message | update_conversation_last_message() |
| search_results_cache | trg_cleanup_search_cache | cleanup_search_cache_per_user() |

---

## 6. pg_cron Retention Jobs

| Job Name | Schedule | Table | Retention | Migration |
|----------|----------|-------|-----------|-----------|
| cleanup-monthly-quota | 1st of month, 2am | monthly_quota | 24 months | 022 |
| cleanup-webhook-events | Daily, 3am | stripe_webhook_events | 90 days | 022 |
| cleanup-audit-events | 1st of month, 4am | audit_events | 12 months | 023 |
| cleanup-cold-cache-entries | Daily, 5am | search_results_cache | 7 days (cold only) | 20260225150000 |
| cleanup-search-state-transitions | Daily, 4am | search_state_transitions | 30 days | 20260308310000 |
| cleanup-alert-sent-items | Daily, 4:05am | alert_sent_items | 180 days | 20260308310000 |
| cleanup-health-checks | Daily, 4:10am | health_checks | 30 days | 20260308310000 |
| cleanup-incidents | Daily, 4:15am | incidents | 90 days | 20260308310000 |
| cleanup-mfa-recovery-attempts | Daily, 4:20am | mfa_recovery_attempts | 30 days | 20260308310000 |
| cleanup-alert-runs | Daily, 4:25am | alert_runs (completed) | 90 days | 20260308310000 |
| cleanup-expired-search-results | Daily, 4am | search_results_store | expired rows | 20260309200000 |
| cleanup-old-search-sessions | Daily, 4:30am | search_sessions | 12 months | 20260309200000 |
| cleanup-classification-feedback | Daily, 4:45am | classification_feedback | 24 months | 20260311100000 |
| cleanup-old-conversations | Daily, 4:50am | conversations | 24 months | 20260311100000 |
| cleanup-orphan-messages | Daily, 4:55am | messages | 24 months | 20260311100000 |

---

## 7. Key Access Patterns

### Search Flow (hot path)
1. `check_and_increment_quota()` RPC -- atomic quota check + increment
2. `INSERT INTO search_sessions` -- record search attempt
3. `INSERT INTO search_state_transitions` -- audit trail per state change
4. `UPSERT INTO search_results_cache` -- L2 cache write (ON CONFLICT user_id, params_hash)
5. `INSERT INTO search_results_store` -- L3 persistent store
6. `UPDATE search_sessions SET status='completed'` -- finalize

### Cache Lookup (read path)
1. `SELECT FROM search_results_cache WHERE user_id=? AND params_hash=?` -- L2 user-specific
2. `SELECT FROM search_results_cache WHERE params_hash_global=? ORDER BY created_at DESC LIMIT 1` -- cross-user fallback
3. `SELECT FROM search_results_store WHERE search_id=?` -- L3 by search_id

### Pipeline Operations
1. `INSERT INTO pipeline_items` -- add to pipeline (UNIQUE user_id + pncp_id)
2. `UPDATE pipeline_items SET stage=? WHERE id=? AND version=?` -- optimistic lock move
3. `SELECT FROM pipeline_items WHERE user_id=? ORDER BY stage, created_at DESC` -- kanban view

### Billing Flow
1. `SELECT FROM plans WHERE id=? AND is_active=true` -- plan lookup
2. `SELECT FROM plan_billing_periods WHERE plan_id=? AND billing_period=?` -- price lookup
3. `INSERT INTO stripe_webhook_events` -- idempotency check (PK = evt_id)
4. `UPDATE user_subscriptions` -- sync subscription state
5. `UPDATE profiles SET plan_type=?` -- keep denormalized plan_type current

### Analytics
1. `get_analytics_summary(user_id)` RPC -- aggregated search stats
2. `SELECT FROM search_sessions WHERE user_id=? ORDER BY created_at DESC` -- history
3. `get_conversations_with_unread_count(user_id)` RPC -- inbox with counts

---

## 8. Custom Types

| Type | Kind | Values | Used By |
|------|------|--------|---------|
| `alert_frequency` | ENUM | daily, twice_weekly, weekly, off | alert_preferences.frequency |

All other constrained columns use CHECK constraints rather than custom types.

---

## Extensions

| Extension | Purpose | Migration |
|-----------|---------|-----------|
| `pg_trgm` | Trigram matching for ILIKE search | 016 |
| `pg_cron` | Scheduled retention cleanup jobs | 022 |

---

*Generated 2026-03-20 by @data-engineer during Brownfield Discovery Phase 2.*
