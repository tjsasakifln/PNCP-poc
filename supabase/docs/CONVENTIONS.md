# Database Naming Conventions

Established in DEBT-207. All new database objects MUST follow these conventions.

## Triggers

**Prefix:** `trg_`

**Pattern:** `trg_{description}`

**Examples:**
- `trg_profiles_updated_at` — BEFORE UPDATE, sets updated_at
- `trg_create_alert_preferences_on_profile` — AFTER INSERT, creates defaults
- `trg_sync_subscription_status` — AFTER INSERT/UPDATE, syncs status
- `trg_cleanup_search_cache` — AFTER INSERT, enforces per-user limit

**Rules:**
- ALL triggers must use the `trg_` prefix
- Use snake_case after the prefix
- Include the table name for clarity
- For `updated_at` triggers: `trg_{table}_updated_at`
- For business logic triggers: `trg_{action}_{context}`

**Canonical function:** `public.set_updated_at()` for all `updated_at` triggers.

## RLS Policies

**Pattern:** `{action}_{table}_{role}`

| Component | Values | Description |
|-----------|--------|-------------|
| `action` | `select`, `insert`, `update`, `delete`, `all` | The SQL operation |
| `table` | exact table name | The table the policy is on |
| `role` | `owner`, `authenticated`, `service`, `admin`, `public`, `self`, `partner` | Who the policy applies to |

**Role definitions:**
- `owner` — `auth.uid() = user_id` (row belongs to the requesting user)
- `authenticated` — any logged-in user (TO authenticated)
- `service` — backend service role (TO service_role)
- `admin` — users with `is_admin = true` or `is_master = true`
- `public` — anonymous access (anon role)
- `self` — user can only see their own membership/record (not necessarily owner)
- `partner` — partner-specific access

**Examples:**
```
select_profiles_owner          -- Users can read their own profile
insert_pipeline_items_owner    -- Users can create their own pipeline items
all_health_checks_service      -- Service role has full access to health_checks
select_audit_events_admin      -- Admins can read audit events
select_plan_features_public    -- Anyone can read plan features
```

**Rules:**
- Every policy name must start with the action
- Table name must be the EXACT table name (not abbreviated)
- One policy per (action, table, role) combination
- Service role `ALL` policies: `all_{table}_service`
- Never use spaces or descriptive sentences in policy names

## Indexes

**Pattern:** `idx_{table}_{columns}`

**Examples:**
- `idx_pipeline_items_user_id`
- `idx_pncp_raw_bids_uf_date`
- `idx_search_sessions_user_id`

## Constraints

**Pattern:** `chk_{table}_{description}` (CHECK), `uq_{table}_{columns}` (UNIQUE), `fk_{table}_{ref}` (FK)

**Examples:**
- `chk_ingestion_runs_metadata_size`
- `uq_ingestion_checkpoints`

## Functions

**Canonical utility functions:**
- `public.set_updated_at()` — trigger function for updated_at columns
- `public.handle_new_user()` — auth.users trigger for profile creation

**RPC functions:** `{verb}_{resource}` (e.g., `upsert_pncp_raw_bids`, `search_datalake`)

## Migration Files

**Pattern:** `YYYYMMDDHHMMSS_{description}.sql`

**Description prefixes:**
- `debt{id}_` — technical debt resolution
- `story{id}_` — feature story implementation
- `fix_` — bug fix
- `datalake_` — ingestion pipeline
