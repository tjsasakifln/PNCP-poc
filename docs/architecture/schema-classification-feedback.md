# Schema: classification_feedback

> STORY-5.6 AC4 (TD-DB-021) — Schema documentation for the classification feedback table.

## Purpose

Stores user feedback on the AI classification pipeline. When users mark a bid as
"false positive", "false negative", or "correct", this table records the verdict
along with contextual metadata for downstream analysis and model retraining.

## Table Definition

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Primary key |
| `user_id` | UUID | NO | — | FK → `profiles(id)` (standardized from `auth.users`) |
| `search_id` | UUID | NO | — | The search session that surfaced this bid |
| `bid_id` | TEXT | NO | — | PNCP bid identifier (e.g., `pncp_id`) |
| `setor_id` | TEXT | NO | — | Sector the bid was classified into |
| `user_verdict` | TEXT | NO | — | `'false_positive'` \| `'false_negative'` \| `'correct'` |
| `reason` | TEXT | YES | — | Free-text explanation from the user |
| `category` | TEXT | YES | — | `'wrong_sector'` \| `'irrelevant_modality'` \| `'too_small'` \| `'too_large'` \| `'closed'` \| `'other'` |
| `bid_objeto` | TEXT | YES | — | Snapshot of `objeto_compra` at feedback time |
| `bid_valor` | DECIMAL | YES | — | Snapshot of `valor_total_estimado` at feedback time |
| `bid_uf` | TEXT | YES | — | Snapshot of UF at feedback time |
| `confidence_score` | INTEGER | YES | — | AI confidence score at classification time |
| `relevance_source` | TEXT | YES | — | Classification method: `'keyword'`, `'llm_standard'`, `'llm_zero_match'`, etc. |
| `created_at` | TIMESTAMPTZ | YES | `now()` | Feedback submission timestamp |

## Constraints

| Name | Type | Definition |
|------|------|------------|
| PK | PRIMARY KEY | `id` |
| FK | FOREIGN KEY | `user_id` → `profiles(id)` |
| CHECK | CHECK | `user_verdict IN ('false_positive', 'false_negative', 'correct')` |
| CHECK | CHECK | `category IN ('wrong_sector', 'irrelevant_modality', 'too_small', 'too_large', 'closed', 'other')` |
| UNIQUE | UNIQUE | `(user_id, search_id, bid_id)` — one verdict per user per bid per search |

## Indexes

| Name | Columns | Condition | Purpose |
|------|---------|-----------|---------|
| `idx_feedback_sector_verdict` | `(setor_id, user_verdict, created_at)` | — | Sector-level accuracy analysis |
| `idx_feedback_user_created` | `(user_id, created_at)` | — | User feedback history |
| `idx_classification_feedback_user_id` | `(user_id)` | — | RLS performance |

## RLS Policies

| Policy | Operation | Rule |
|--------|-----------|------|
| `feedback_insert_own` | INSERT | `auth.uid() = user_id` |
| `feedback_select_own` | SELECT | `auth.uid() = user_id` |
| `feedback_update_own` | UPDATE | `auth.uid() = user_id` |
| `feedback_delete_own` | DELETE | `auth.uid() = user_id` |
| `feedback_admin_all` | ALL | `auth.role() = 'service_role'` |

## Backend Integration

- **Write path:** `POST /v1/feedback` → `routes/feedback.py` → inserts row
- **Delete path:** `DELETE /v1/feedback` → `routes/feedback.py` → deletes by (user, search, bid)
- **Analysis:** `GET /v1/admin/feedback/patterns` → `feedback_analyzer.py` → bi-gram false-positive patterns
- **Metrics:** `smartlic_feedback_negative_total` Prometheus counter

## Migration History

| Migration | Change |
|-----------|--------|
| `20260308200000_debt002_bridge_backend_migrations.sql` | Initial CREATE TABLE + indexes + RLS |
| `20260225120000_standardize_fks_to_profiles.sql` | FK changed from `auth.users(id)` → `profiles(id)` |
| `20260304200000_rls_standardize_service_role.sql` | Service role policy standardized |
| `20260308100000_debt001_database_integrity_fixes.sql` | Added `idx_classification_feedback_user_id` |
