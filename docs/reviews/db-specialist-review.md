# Database Specialist Review

**Reviewer:** @data-engineer (Dara)
**Date:** 2026-02-11
**Reviewed Document:** docs/prd/technical-debt-DRAFT.md (Section 3)
**Reference Sources:** supabase/docs/DB-AUDIT.md, supabase/docs/SCHEMA.md
**Codebase State:** commit `808cd05`, branch `main`

---

## 1. Debts Validated

All 19 database debts listed in Section 3 of the DRAFT are real issues. Below is the item-by-item validation with adjusted severity, refined hour estimates, and complexity ratings.

| ID | Debt | Original Severity | Validated Severity | Hours | Complexity | Notes |
|----|------|-------------------|-------------------|-------|------------|-------|
| DB-C01 | `database.py` derives PostgreSQL URL incorrectly from `SUPABASE_URL` | CRITICAL | **CRITICAL** | 2-4h | Simple | Confirmed: `SUPABASE_URL` is `https://fqqyovlzdzimiwfofdjk.supabase.co`. Line 33 produces `postgresql://fqqyovlzdzimiwfofdjk.supabase.co` which is NOT a valid PostgreSQL connection string (missing port, database name, credentials). The engine either fails on first use or falls back to `postgresql://localhost/smartlic`. See Q1 answer for full analysis. |
| DB-C02 | `user_subscriptions` missing service role RLS policy for writes | CRITICAL | **HIGH** | 1h | Simple | Valid concern but downgraded. See Q2 answer for nuance. The service_role key bypasses RLS in all current Supabase versions. The risk is future-proofing, not present breakage. Still must be fixed for consistency. |
| DB-C03 | `stripe_webhook_events` admin check uses `plan_type = 'master'` instead of `is_admin` | CRITICAL | **CRITICAL** | 0.5h | Simple | Confirmed by reading migration 010 lines 61-68. The policy checks `profiles.plan_type = 'master'` but the canonical admin flag is `profiles.is_admin`. These are independent columns. An admin with plan_type `consultor_agil` cannot view webhook events. A master user who is not an admin CAN view them. Direct access control bug. |
| DB-H01 | Dual ORM Architecture (Supabase Client + SQLAlchemy) | HIGH | **CRITICAL** (upgrade) | 10-14h | Complex | Upgraded to CRITICAL. Analysis reveals the situation is worse than documented: `main.py` (lines 733-829) has Supabase-client-based Stripe handlers (`_activate_plan`, `_deactivate_stripe_subscription`, `_handle_subscription_updated`), while `webhooks/stripe.py` has SQLAlchemy-based handlers for the SAME event types. Two competing implementations for the same business logic. This is not just architectural debt -- it is an active correctness risk. |
| DB-H02 | Migration 006 duplicated (3 files) | HIGH | **HIGH** | 1-2h | Simple | Confirmed: 3 files with `006_` prefix. `006_APPLY_ME.sql` and `006_search_sessions_service_role_policy.sql` are byte-for-byte identical in SQL effect (both create the same policy). The `006_APPLY_ME.sql` has dashboard-paste instructions. The risk is operational confusion, not data corruption. See Q4 answer. |
| DB-H03 | Index missing on `user_subscriptions.stripe_subscription_id` | HIGH | **HIGH** | 0.5h | Simple | Confirmed: Migration 001 defines `stripe_subscription_id text` with NO unique constraint. The SQLAlchemy model defines `unique=True` but `Base.metadata.create_all()` was never called (the engine URL is invalid). The `main.py` queries this column at lines 785, 795, 822, 886. Without an index, these are sequential scans on `user_subscriptions`. |
| DB-H04 | RLS policies overly permissive (`USING (true)` without `TO service_role`) | HIGH | **HIGH** | 1h | Simple | Confirmed in migration 002 (monthly_quota) and 006 (search_sessions). Compare with migrations 013/014 (user_oauth_tokens, google_sheets_exports) which correctly use `TO service_role`. The permissive policies allow any authenticated user to INSERT/UPDATE/DELETE rows on monthly_quota and search_sessions via PostgREST. In practice, PostgREST URL is not exposed to client-side code, but this is defense-in-depth failure. |
| DB-H05 | `profiles` missing INSERT policy for auth trigger | HIGH | **MEDIUM** (downgrade) | 0.5h | Simple | Downgraded. The `handle_new_user()` trigger runs as `SECURITY DEFINER` which inherently bypasses RLS. The `_ensure_profile_exists()` in quota.py uses service_role key which also bypasses RLS. There is no code path where a regular user or anon key attempts to INSERT into profiles. Adding an explicit INSERT policy is good hygiene but not a security gap in the current system. |
| DB-M01 | FK inconsistencies (auth.users vs profiles) | MEDIUM | **MEDIUM** | 3-4h | Medium | Confirmed: `monthly_quota` (migration 002), `user_oauth_tokens` (013), and `google_sheets_exports` (014) reference `auth.users(id)` while all other tables reference `profiles(id)`. Functionally equivalent because `profiles.id` has a cascading FK to `auth.users.id`, so deletions propagate correctly either way. The inconsistency is a maintenance burden, not a data integrity risk. See Q3 answer. |
| DB-M02 | CHECK constraint `plan_type` includes legacy values | MEDIUM | **MEDIUM** | 1-2h | Simple | Confirmed: constraint allows 10 values including legacy `free`, `avulso`, `pack`, `monthly`, `annual`. The `quota.py:386-392` PLAN_TYPE_MAP handles legacy-to-current mapping, but nothing prevents new profile insertions with legacy types. The `handle_new_user()` trigger sets `plan_type = 'free'` (a legacy value!) by default. This means every new user starts with a legacy plan_type. |
| DB-M03 | `updated_at` missing in migration for `user_subscriptions` | MEDIUM | **MEDIUM** | 1h | Simple | Confirmed: Migration 001 (line 63-73) does NOT define `updated_at`. Migration 008 does NOT add it either (verified by grep). The SQLAlchemy model defines it (line 83). This column was likely added manually via Supabase dashboard. If it exists in production, this is documentation/migration gap only. If it does not exist, SQLAlchemy writes to it would fail silently (Supabase client ignores unknown columns in UPDATE). |
| DB-M04 | `profiles.plan_type` and `user_subscriptions.plan_id` can drift | MEDIUM | **MEDIUM** | 4-6h | Complex | Confirmed. The 4-layer fallback in `quota.py:413-504` is well-designed resilience, but drift is not merely theoretical: `_activate_plan()` (main.py:764) syncs profiles.plan_type on activation, `_deactivate_stripe_subscription()` (main.py:799) syncs on cancellation, but `webhooks/stripe.py:handle_subscription_updated()` does NOT sync profiles.plan_type. So subscription updates via the SQLAlchemy handler create drift. See Q5 answer. |
| DB-M05 | Stripe price IDs hardcoded in migration 015 | MEDIUM | **MEDIUM** | 2h | Simple | Confirmed: Migration 015 contains 6 production Stripe price IDs (e.g., `price_1Syir09FhmvPslGYOCbOvWVB`). If applied to staging/dev, it sets production price IDs which would charge real money or fail Stripe API calls. |
| DB-M06 | N+1 query in conversation list endpoint | MEDIUM | **MEDIUM** | 2-3h | Medium | Confirmed in `routes/messages.py:112-122`. For each conversation, a separate Supabase call counts unread messages. The Supabase client does not support subqueries or JOINs natively, but this can be solved with an RPC function or database view. See Q6 answer. |
| DB-M07 | Analytics endpoints fetch ALL sessions | MEDIUM | **MEDIUM** | 2-3h | Medium | Confirmed in `routes/analytics.py:78-83`. `SELECT id, total_raw, total_filtered, valor_total, created_at` with no pagination or date limit. All aggregation done in Python. Should be an RPC or view with server-side aggregation. See Q6 answer. |
| DB-L01 | `plans` table missing `updated_at` column | LOW | **LOW** | 0.5h | Simple | Confirmed. Plans table has `created_at` only. Given plans change infrequently (5 updates total across 15 migrations), impact is minimal. |
| DB-L02 | No retention/cleanup for `monthly_quota` historical rows | LOW | **LOW** | 3-4h | Medium | Confirmed. One row per user per month, accumulates indefinitely. At 5,000 users for 5 years = 300,000 rows. Manageable for PostgreSQL but worth cleaning rows older than 24 months. |
| DB-L03 | No retention/cleanup for `stripe_webhook_events` | LOW | **LOW** | 3-4h | Medium | Confirmed. Migration 010 comment mentions 90-day retention but nothing implements it. With JSONB payload, this table grows faster in disk usage. |
| DB-L04 | Redundant index `idx_user_oauth_tokens_provider` | LOW | **LOW** | 0.25h | Simple | Confirmed. Table has at most hundreds of rows. The `unique_user_provider` constraint on `(user_id, provider)` already covers lookups. A standalone index on `provider` (3 possible values) has negligible selectivity. |

---

## 2. Debts Removed/Downgraded

### 2.1 DB-C02: CRITICAL -> HIGH

**Reason:** The Supabase service_role key has bypassed RLS since Supabase's inception. This is a documented, core behavior of PostgREST's service_role. The risk of Supabase changing this behavior without a major version bump is extremely low -- it would break every Supabase project in existence. The inconsistency with other tables is worth fixing for code clarity, but calling it CRITICAL implies imminent production breakage, which is not the case. Reclassified as HIGH.

### 2.2 DB-H05: HIGH -> MEDIUM

**Reason:** No code path in the current system attempts to INSERT into profiles via a non-service-role client. The trigger uses SECURITY DEFINER. The service_role key bypasses RLS. Adding an INSERT policy is good practice for documentation purposes and defense-in-depth, but the lack of it is not exploitable in the current architecture.

---

## 3. NEW Debts Added

### NEW-DB-01: Competing Stripe webhook handler implementations (CRITICAL)

**Severity:** CRITICAL
**Files:** `backend/main.py:733-900` (Supabase client), `backend/webhooks/stripe.py:104-144` (SQLAlchemy)
**Description:** There are TWO complete implementations of Stripe subscription lifecycle handlers:

1. `main.py` contains `_activate_plan()`, `_deactivate_stripe_subscription()`, `_handle_subscription_updated()`, `_handle_invoice_payment()` -- all using the Supabase client.
2. `webhooks/stripe.py` contains `handle_subscription_updated()`, `handle_subscription_deleted()`, `handle_invoice_payment_succeeded()` -- all using SQLAlchemy.

The webhook router in `webhooks/stripe.py` is mounted on the app (line 100 of main.py). The main.py helper functions are called from the Stripe checkout success handler (`_activate_plan`) and potentially from other inline handlers.

**Impact:** If both code paths can be triggered for the same event type, they will execute different logic against the database using different access mechanisms. The SQLAlchemy handlers do NOT sync `profiles.plan_type`, while the main.py handlers DO. This means the behavior of a subscription update depends on WHICH code path handles it, leading to unpredictable plan_type drift.

**Recommendation:** This is the single most dangerous database-related debt. Consolidate to one implementation (Supabase client, matching 95% of the codebase).

**Hours:** 6-8h (included in DB-H01 estimate)

### NEW-DB-02: `handle_new_user()` trigger sets `plan_type = 'free'` (legacy value) (MEDIUM)

**Severity:** MEDIUM
**Files:** `supabase/migrations/001_profiles_and_sessions.sql` (handle_new_user function), `supabase/migrations/007_add_whatsapp_consent.sql` (updated version)
**Description:** The trigger that creates profiles for new auth users sets `plan_type` to `'free'` (the default in the column definition). But `'free'` is a legacy plan_type -- the current equivalent is `'free_trial'`. The `PLAN_TYPE_MAP` in `quota.py:386-392` maps `free` -> `free_trial`, so functionally it works, but every new user starts with an inconsistent legacy value that requires runtime mapping.

**Recommendation:** Either update the trigger/column default to `'free_trial'`, or update the CHECK constraint to remove `'free'` and accept the mapping layer. The cleaner fix is changing the default.

**Hours:** 0.5h
**Complexity:** Simple

### NEW-DB-03: Missing index on `profiles.email` for admin ILIKE search (MEDIUM)

**Severity:** MEDIUM
**Files:** `backend/admin.py:268-269`
**Description:** This was identified in the DB-AUDIT (PERF-IDX-3) but NOT carried over into the DRAFT. The admin panel searches users by email using `email.ilike.%search%`. Without a trigram index, this performs a sequential scan on the profiles table. At 5,000+ users, this will be noticeably slow.

**Recommendation:** Add pg_trgm extension and GIN index:
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_profiles_email_trgm ON profiles USING GIN(email gin_trgm_ops);
```

**Hours:** 1h
**Complexity:** Simple

### NEW-DB-04: Missing index on `user_subscriptions.stripe_customer_id` (LOW)

**Severity:** LOW
**Files:** `backend/webhooks/stripe.py`, `backend/main.py`
**Description:** This was identified in the DB-AUDIT (PERF-IDX-2) but NOT carried over into the DRAFT. Admin panel and Stripe reconciliation may query by customer_id. Currently no index exists.

**Hours:** 0.5h
**Complexity:** Simple

### NEW-DB-05: `user_subscriptions.plan_id` FK has no explicit ON DELETE action (LOW)

**Severity:** LOW
**Files:** `supabase/migrations/001_profiles_and_sessions.sql:66`
**Description:** This was identified in the DB-AUDIT (INTEGRITY-2) but NOT carried over. The FK `plan_id text NOT NULL REFERENCES public.plans(id)` defaults to RESTRICT. This is actually the correct behavior (you should not delete a plan with active subscriptions), but it should be explicitly documented as intentional.

**Hours:** 0.25h (documentation only)
**Complexity:** Simple

---

## 4. Answers to Architect Questions

### Q1: database.py URL -- is SQLAlchemy actually failing in production?

**Answer: Almost certainly yes, the SQLAlchemy connection is broken.**

The derivation at `database.py:33`:
```python
DATABASE_URL = SUPABASE_URL.replace("https://", "postgresql://")
```

Transforms `https://fqqyovlzdzimiwfofdjk.supabase.co` into `postgresql://fqqyovlzdzimiwfofdjk.supabase.co`.

This is missing:
- Port (Supabase PostgreSQL uses port 5432 or 6543 for pooler)
- Database name (typically `postgres`)
- Username (`postgres` or `postgres.fqqyovlzdzimiwfofdjk`)
- Password (the database password)

SQLAlchemy will attempt to connect and fail. The `pool_pre_ping=True` on line 42 means it retries on each request, so each webhook call will:
1. Attempt connection -> fail
2. Raise `OperationalError`
3. Get caught by the `except SQLAlchemyError` in `webhooks/stripe.py:139-142`
4. Return HTTP 500 to Stripe

**How are Stripe webhooks working then?**

They are likely NOT working via the SQLAlchemy path. Instead, Stripe payments work because:
1. **Checkout success** is handled by `_activate_plan()` in `main.py:733` which uses the Supabase client (works correctly).
2. **Subscription lifecycle events** (updated, deleted) have TWO handlers. If the SQLAlchemy handler in `webhooks/stripe.py` fails with HTTP 500, Stripe retries the webhook up to ~15 times over 72 hours. Each retry fails.
3. Meanwhile, user-facing functionality (quota checks, plan lookups) uses the Supabase client via `quota.py` which has the robust 4-layer fallback.

**Implication:** Stripe webhook-driven updates (subscription changes, cancellations originating from Stripe dashboard, failed payment -> subscription deletion) are likely NOT being recorded. Users who cancel via Stripe are probably still showing as active in the system until the profile-based fallback eventually resets them. The idempotency table (`stripe_webhook_events`) via SQLAlchemy is also non-functional, meaning there is no webhook audit trail.

**Recommendation:** This is a P0 fix. Either:
- (A) Add `DATABASE_URL` env var in Railway with the Supabase PostgreSQL connection string (quick fix, 1h)
- (B) Migrate `webhooks/stripe.py` to Supabase client and remove SQLAlchemy entirely (correct fix, 10-14h)

Option (B) is strongly recommended because it eliminates the dual-ORM debt permanently.

### Q2: user_subscriptions RLS -- is explicit policy needed given service_role bypass?

**Answer: Recommended but not urgent. Reclassify from CRITICAL to HIGH.**

The service_role key bypasses RLS in Supabase by design. This behavior is:
- Documented in Supabase official docs
- Implemented at the PostgREST level (not in PostgreSQL itself)
- Has been stable since Supabase v1

The risk of this changing is minimal. However, the inconsistency IS worth fixing because:
1. `monthly_quota` (migration 002) and `search_sessions` (migration 006) both have explicit `FOR ALL USING (true)` service role policies.
2. `user_oauth_tokens` (013) and `google_sheets_exports` (014) have proper `TO service_role` variants.
3. `user_subscriptions` has NEITHER. This is an inconsistency that makes security review harder.

**Recommendation:** Add the policy in the next migration batch, but do not treat as an emergency. Use the correct pattern with `TO service_role`:

```sql
CREATE POLICY "Service role can manage subscriptions" ON user_subscriptions
    FOR ALL TO service_role USING (true);
```

### Q3: FK inconsistencies -- effort to migrate 3 tables without downtime?

**Answer: 3-4 hours, low risk, no downtime required.**

The migration involves:
1. `monthly_quota`: FK `user_id -> auth.users(id)` -> change to `user_id -> profiles(id)`
2. `user_oauth_tokens`: Same change
3. `google_sheets_exports`: Same change

**Orphan data risk:** Zero. Since `profiles.id` has `ON DELETE CASCADE` from `auth.users.id`, every `auth.users.id` that has data in these tables also has a corresponding `profiles.id`. The sets are identical by construction (the `handle_new_user` trigger guarantees this).

**Migration steps (no downtime):**
```sql
-- Step 1: Verify no orphans (safety check)
SELECT COUNT(*) FROM monthly_quota mq
  LEFT JOIN profiles p ON p.id = mq.user_id
  WHERE p.id IS NULL;
-- Must return 0

-- Step 2: Drop old FK, add new FK
ALTER TABLE monthly_quota DROP CONSTRAINT monthly_quota_user_id_fkey;
ALTER TABLE monthly_quota ADD CONSTRAINT monthly_quota_user_id_fkey
  FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;

-- Repeat for user_oauth_tokens and google_sheets_exports
```

PostgreSQL acquires a brief `ACCESS EXCLUSIVE` lock on the table when adding/dropping FK constraints. For tables with hundreds of rows, this lock is held for milliseconds. Zero practical downtime.

**Complexity:** Simple. The only risk is if the FK constraint names differ from the default convention. Run `\d+ monthly_quota` in production to get the exact constraint name before writing the migration.

### Q4: Migration 006 duplicates -- which is actually applied?

**Answer: `006_APPLY_ME.sql` was applied manually; `006_search_sessions_service_role_policy.sql` is the code-tracked duplicate.**

Evidence:
1. `006_APPLY_ME.sql` contains "COPY AND PASTE THIS SQL INTO SUPABASE DASHBOARD SQL EDITOR" header, indicating it was designed for manual application.
2. `006_search_sessions_service_role_policy.sql` is the "clean" version for version control, with the verification query commented out.
3. Both produce the identical result: a `FOR ALL USING (true)` policy on `search_sessions`.
4. The third file `006_update_profiles_plan_type_constraint.sql` is a DIFFERENT migration (updates the plan_type CHECK constraint).

**Recommendation:**
1. Verify in production that the policy exists: `SELECT * FROM pg_policies WHERE tablename = 'search_sessions';`
2. Rename `006_update_profiles_plan_type_constraint.sql` to keep its `006_` prefix (it was first chronologically).
3. Delete `006_APPLY_ME.sql` (it was a one-time manual apply script).
4. Renumber `006_search_sessions_service_role_policy.sql` to `016_` or the next available number, noting it was already applied.
5. Add a `MIGRATIONS_APPLIED.md` document tracking which migrations have been applied and when.

**Hours:** 1-2h (including verification and documentation).

### Q5: plan_type drift -- is quota.py fallback sufficient or need PostgreSQL trigger?

**Answer: The fallback is resilient but a PostgreSQL trigger is the correct long-term solution.**

**Current state:**
- The 4-layer fallback in `quota.py:413-504` handles drift gracefully for READ operations (checking what plan a user has).
- `_activate_plan()` (main.py:764) syncs `profiles.plan_type` on new subscription creation.
- `_deactivate_stripe_subscription()` (main.py:799) syncs on cancellation.
- BUT `webhooks/stripe.py:handle_subscription_updated()` does NOT sync `profiles.plan_type`. If this handler ever works (after fixing DB-C01), it will create drift.
- There is no periodic reconciliation.

**Recommendation:** Two-phase approach:

**Phase 1 (immediate, with ORM consolidation):** Ensure ALL write paths to `user_subscriptions` also update `profiles.plan_type`. This is best done during the ORM consolidation (DB-H01) since you are rewriting the Stripe handlers anyway.

**Phase 2 (medium-term):** Add a PostgreSQL trigger on `user_subscriptions` that automatically syncs `profiles.plan_type`:

```sql
CREATE OR REPLACE FUNCTION sync_profile_plan_type()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_active = true THEN
        UPDATE profiles SET plan_type = NEW.plan_id WHERE id = NEW.user_id;
    ELSIF OLD.is_active = true AND NEW.is_active = false THEN
        -- Check if user has another active subscription
        IF NOT EXISTS (
            SELECT 1 FROM user_subscriptions
            WHERE user_id = NEW.user_id AND is_active = true AND id != NEW.id
        ) THEN
            UPDATE profiles SET plan_type = 'free_trial' WHERE id = NEW.user_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER trg_sync_profile_plan_type
    AFTER INSERT OR UPDATE ON user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION sync_profile_plan_type();
```

This trigger eliminates drift regardless of which code path (Supabase client, SQLAlchemy, manual SQL, future microservice) modifies subscriptions.

**Hours:** Phase 1 is included in DB-H01 (0h incremental). Phase 2 is 2-3h.

### Q6: N+1 and analytics queries -- production data on typical sizes?

**Answer: Based on table growth estimates from the DB-AUDIT and the current user base.**

**Conversations (DB-M06):**
- Based on Appendix C of the DB-AUDIT: 100-1,000 conversations expected in year 1.
- The admin panel loads ALL conversations. A typical admin page load might fetch 20-50 conversations with pagination.
- Each conversation triggers 1 unread-count subquery.
- **Impact:** 21-51 Supabase REST API calls per page load. Each call has ~10-30ms network overhead to PostgREST. Total: 200ms-1.5s added latency.
- **Priority:** MEDIUM. Noticeable but not critical given low conversation volume.

**Search sessions (DB-M07):**
- Based on Appendix C: 10,000-100,000 sessions expected in year 1.
- Power users (sales teams) might have 50-200 sessions per month.
- `get_analytics_summary()` fetches ALL sessions for a user with no date filter.
- A user with 1,000 sessions transfers ~100KB of data that is then aggregated in Python.
- **Impact:** 200-500ms for typical users, 1-3s for power users. Grows linearly.
- **Priority:** MEDIUM. Should be addressed before exceeding 500 active users.

**Recommended fix for both:**

For DB-M06, create an RPC function:
```sql
CREATE OR REPLACE FUNCTION get_conversations_with_unread(p_user_id uuid, p_is_admin boolean, p_limit int, p_offset int)
RETURNS TABLE(...) AS $$
-- Single query with LEFT JOIN and COUNT aggregate
$$;
```

For DB-M07, create a materialized view or RPC:
```sql
CREATE OR REPLACE FUNCTION get_user_analytics_summary(p_user_id uuid)
RETURNS TABLE(total_searches bigint, total_opportunities bigint, total_value numeric, ...) AS $$
SELECT COUNT(*), SUM(total_filtered), SUM(valor_total), ...
FROM search_sessions WHERE user_id = p_user_id;
$$;
```

### Q7: Retention strategy -- pg_cron, Edge Function, or app-level cleanup?

**Answer: pg_cron is the recommended approach. Edge Function is the fallback if pg_cron is unavailable.**

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| **pg_cron** | Runs inside PostgreSQL, no external dependencies, transactional, no network overhead | Requires pg_cron extension (available on Supabase Pro+), limited scheduling UI | **PREFERRED** |
| **Supabase Edge Function + cron** | Works on all Supabase tiers, visible in dashboard, can send notifications | Network overhead, non-transactional, cold start latency, Deno runtime | **FALLBACK** |
| **Application-level cleanup** | No infrastructure changes, easy to test | Requires running backend instance, not reliable if backend restarts, couples cleanup to app lifecycle | **NOT RECOMMENDED** |

**Recommended implementation (pg_cron):**

```sql
-- Supabase Pro plans include pg_cron
SELECT cron.schedule(
    'cleanup-webhook-events',
    '0 3 * * 0',  -- Every Sunday at 3 AM UTC
    $$DELETE FROM stripe_webhook_events WHERE processed_at < NOW() - INTERVAL '90 days'$$
);

SELECT cron.schedule(
    'cleanup-monthly-quota',
    '0 4 1 * *',  -- First day of month at 4 AM UTC
    $$DELETE FROM monthly_quota WHERE month_year < to_char(NOW() - INTERVAL '24 months', 'YYYY-MM')$$
);
```

If on Supabase Free tier (no pg_cron), use Edge Function:

```typescript
// supabase/functions/cleanup-retention/index.ts
Deno.serve(async () => {
    const supabase = createClient(/* service_role */);
    await supabase.rpc('cleanup_old_records');
    return new Response('OK');
});
```

Then schedule via Supabase Dashboard > Edge Functions > Schedules.

**Hours:** 3-4h for either approach (including testing and monitoring).

---

## 5. Priority Recommendations

Ordered by risk impact and dependency chain. Items that must precede others are explicitly noted.

### P0 -- Fix Immediately (Week 1)

| Order | ID | Debt | Hours | Rationale |
|-------|-----|------|-------|-----------|
| 1 | DB-C03 | Fix `stripe_webhook_events` admin policy (`plan_type='master'` -> `is_admin=true`) | 0.5h | Direct access control bug. Single ALTER POLICY statement. Zero risk. |
| 2 | DB-H04 | Tighten overly permissive RLS (`TO service_role` on monthly_quota, search_sessions) | 1h | Security hardening. No behavior change for existing code (service_role still passes). |
| 3 | DB-H03 | Add unique index on `stripe_subscription_id` | 0.5h | Performance + data integrity. Prevents duplicate subscription IDs. |
| 4 | NEW-DB-03 | Add trigram index on `profiles.email` | 1h | Admin panel performance. Prevents full table scan on user search. |

**Subtotal P0:** 3h. All are independent, can be applied in a single migration file.

### P1 -- Fix This Sprint (Week 1-2)

| Order | ID | Debt | Hours | Rationale |
|-------|-----|------|-------|-----------|
| 5 | DB-C01 + DB-H01 + NEW-DB-01 | Consolidate ORM: migrate `webhooks/stripe.py` to Supabase client, delete `database.py` and `models/` | 10-14h | **The most impactful single fix.** Resolves 3 debts simultaneously. Eliminates broken SQLAlchemy connection, competing handler implementations, and dual ORM risk. MUST be done before any other Stripe-related work. |
| 6 | DB-C02 | Add service role RLS policy on `user_subscriptions` | 1h | Consistency. Can be done in same migration batch as P0 items. |
| 7 | DB-H02 | Consolidate migration 006 files | 1-2h | Clean up confusion. Verify production state, remove duplicates, document. |
| 8 | NEW-DB-02 | Fix `handle_new_user()` default plan_type (`'free'` -> `'free_trial'`) | 0.5h | Data consistency. Every new user currently gets a legacy value. |

**Subtotal P1:** 13-18h.

### P2 -- Fix Within 2 Sprints (Week 3-4)

| Order | ID | Debt | Hours | Rationale |
|-------|-----|------|-------|-----------|
| 9 | DB-M04 | Add `sync_profile_plan_type` trigger (Phase 2) | 2-3h | Eliminates plan_type drift permanently. Depends on P1 ORM consolidation. |
| 10 | DB-M02 | Tighten plan_type CHECK constraint (remove legacy values) | 1-2h | Depends on NEW-DB-02 and a data migration of existing `'free'` users. |
| 11 | DB-M01 | Standardize FK references (auth.users -> profiles) | 3-4h | Consistency. Low risk but requires careful migration. |
| 12 | DB-M06 | Fix N+1 query in conversation list | 2-3h | Performance for admin panel. |
| 13 | DB-M07 | Server-side aggregation for analytics | 2-3h | Performance for power users. |
| 14 | DB-M03 | Add remediation migration for `updated_at` on user_subscriptions | 1h | Schema consistency. |
| 15 | DB-M05 | Environment-aware Stripe price ID loading | 2h | DevOps hygiene. |
| 16 | DB-H05 | Add explicit INSERT policy on profiles | 0.5h | Documentation/hygiene. |

**Subtotal P2:** 14-19h.

### P3 -- Backlog

| Order | ID | Debt | Hours | Rationale |
|-------|-----|------|-------|-----------|
| 17 | DB-L02 | Retention cleanup for monthly_quota | 3-4h | Maintenance. Not urgent at current scale. |
| 18 | DB-L03 | Retention cleanup for stripe_webhook_events | 3-4h | Maintenance. Combined with DB-L02 for shared pg_cron setup. |
| 19 | DB-L01 | Add `updated_at` to plans table | 0.5h | Audit trail. Very low priority. |
| 20 | DB-L04 | Drop redundant oauth provider index | 0.25h | Trivial cleanup. |
| 21 | NEW-DB-04 | Add index on stripe_customer_id | 0.5h | Low priority optimization. |
| 22 | NEW-DB-05 | Document intentional ON DELETE RESTRICT on plan_id FK | 0.25h | Documentation only. |

**Subtotal P3:** 8-10h.

---

## 6. Migration Plan Considerations

### 6.1 Production Safety

All P0 database changes (items 1-4) are **additive only** (CREATE INDEX, CREATE POLICY, ALTER POLICY). They:
- Do not modify existing data
- Do not change column types
- Do not drop anything
- Can be applied during business hours with zero downtime
- Are idempotent (use `IF NOT EXISTS`, `DROP POLICY IF EXISTS` before CREATE)

### 6.2 ORM Consolidation (P1, item 5) -- Critical Path

The ORM consolidation is the highest-risk change. Recommended approach:

1. **Before starting:** Verify which Stripe webhook events are being received in production. Check Railway logs for `"Database error processing webhook"` entries from `webhooks/stripe.py:141`. This confirms the SQLAlchemy path is failing.

2. **Implementation order:**
   - Rewrite `webhooks/stripe.py` handlers to use Supabase client
   - Ensure ALL handlers sync `profiles.plan_type` (matching main.py pattern)
   - Remove `from database import get_db` dependency
   - Add integration tests against Supabase
   - Deploy and monitor Stripe webhook delivery in Stripe Dashboard
   - After 1 week of clean webhook delivery, delete `database.py` and `models/` directory

3. **Rollback plan:** Keep `database.py` and models as dead code for 2 weeks after migration. If issues arise, re-enable by restoring the import.

### 6.3 Migration File Strategy

Going forward, migrations should:
1. Use sequential numbering starting from `016_`
2. Never include environment-specific data (use seed scripts for Stripe IDs, plan data)
3. Include `DO $$ ... $$` validation blocks (following the good pattern from migration 008)
4. Be applied via `supabase db push`, never via manual dashboard paste
5. Include rollback SQL in comments or companion `.rollback.sql` files

### 6.4 Recommended Migration Batch

Combine P0 + some P1 items into a single migration file for atomic application:

```
016_security_and_index_fixes.sql
  - Fix stripe_webhook_events admin policy
  - Tighten RLS on monthly_quota and search_sessions (add TO service_role)
  - Add unique index on stripe_subscription_id
  - Add trigram index on profiles.email
  - Add service role policy on user_subscriptions
  - Update profiles default plan_type to 'free_trial'
```

This single migration resolves 6 debts in one atomic application. Estimated application time: < 5 seconds.

### 6.5 Total Effort Summary

| Priority | Debts | Hours (min) | Hours (max) |
|----------|-------|-------------|-------------|
| P0 | 4 | 3 | 3 |
| P1 | 4 | 13 | 18 |
| P2 | 8 | 14 | 19 |
| P3 | 6 | 8 | 10 |
| **Total** | **22** | **38** | **50** |

Note: The DRAFT estimated 43-62h for 19 database debts. This review identifies 22 debts (3 new) with a tighter estimate of 38-50h. The reduction comes from more accurate scoping of individual items after code verification, and the consolidation of DB-C01 + DB-H01 + NEW-DB-01 into a single work item.

---

*Review completed by @data-engineer (Dara) on 2026-02-11. All findings verified against source code at commit `808cd05`.*
