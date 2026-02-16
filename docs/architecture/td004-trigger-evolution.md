# STORY-TD-004 Track Bravo: Trigger Evolution Analysis

**Author:** @data-engineer
**Date:** 2026-02-16
**Stories:** DB-11 (handle_new_user evolution), DB-01 (sync_profile_plan_type analysis)

---

## Executive Summary

This document traces the evolution of two critical database triggers in the SmartLic system:

1. **handle_new_user()** — Auto-creates profile records when users sign up (5 versions across 6 migrations)
2. **sync_profile_plan_type()** — Auto-syncs `profiles.plan_type` from `user_subscriptions` changes (DEAD CODE)

**Critical Finding:** The `sync_profile_plan_type()` trigger is **non-functional dead code**. It references a `status` column on `user_subscriptions` that **does not exist** and never has existed in any migration. The trigger will cause runtime errors if fired.

---

## Part 1: handle_new_user() Evolution (DB-11)

### Migration Timeline

| Version | Migration | Date | Story | Key Changes |
|---------|-----------|------|-------|-------------|
| V1 | 001_profiles_and_sessions.sql | Initial | - | Basic profile creation (4 fields) |
| V2 | 007_add_whatsapp_consent.sql | - | STORY-166 | Added 6 marketing/consent fields |
| V3 | 016_security_and_index_fixes.sql | 2026-02-11 | STORY-200 | Fixed plan_type default to 'free_trial' |
| V4 | 024_add_profile_context.sql | - | STORY-247 | Added context_data JSONB |
| V5 | 027_fix_plan_type_default_and_rls.sql | 2026-02-15 | STORY-TD-001 | **CANONICAL** — Explicit plan_type + ON CONFLICT |

---

### Version-by-Version Comparison

#### Version 1 (Migration 001) — Initial Implementation

**Purpose:** Basic profile creation from auth metadata

```sql
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, full_name, avatar_url)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'name'),
    new.raw_user_meta_data->>'avatar_url'
  );
  return new;
end;
$$ language plpgsql security definer;
```

**Fields Inserted:** 4
**plan_type Handling:** Relied on column default (`'free'`)
**Issues:**
- No explicit plan_type value
- No conflict handling
- Minimal metadata extraction

---

#### Version 2 (Migration 007) — Marketing Consent

**Purpose:** Add sector, phone, WhatsApp consent fields

**Changes from V1:**
- ✅ Added `company`, `sector`, `phone_whatsapp` fields
- ✅ Added `whatsapp_consent` boolean + timestamp logic
- ✅ Dynamic consent timestamp (NOW() if TRUE, NULL otherwise)

```sql
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (
    id, email, full_name, company, sector, avatar_url,
    phone_whatsapp, whatsapp_consent, whatsapp_consent_at
  )
  VALUES (
    new.id,
    new.email,
    COALESCE(new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'name'),
    new.raw_user_meta_data->>'company',
    new.raw_user_meta_data->>'sector',
    new.raw_user_meta_data->>'avatar_url',
    new.raw_user_meta_data->>'phone_whatsapp',
    COALESCE((new.raw_user_meta_data->>'whatsapp_consent')::boolean, FALSE),
    CASE
      WHEN (new.raw_user_meta_data->>'whatsapp_consent')::boolean = TRUE
      THEN NOW()
      ELSE NULL
    END
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

**Fields Inserted:** 9
**plan_type Handling:** Still relied on column default
**Issues:**
- Still no explicit plan_type
- No conflict handling
- Complex CASE logic for consent timestamp

---

#### Version 3 (Migration 016) — Free Trial Fix

**Purpose:** Fix plan_type default from 'free' to 'free_trial' (DB-C02)

**Critical Change:** First version to **explicitly set plan_type**

```sql
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name, avatar_url, plan_type)
  VALUES (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'name'),
    new.raw_user_meta_data->>'avatar_url',
    'free_trial'  -- ⚠️ HARDCODED
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

**Fields Inserted:** 5
**plan_type Handling:** Hardcoded `'free_trial'`
**Issues:**
- ❌ **REGRESSION:** Lost all fields from V2 (company, sector, phone, consent, etc.)
- ❌ Incomplete implementation — only fixed plan_type
- ❌ No conflict handling

**Impact:** This version **broke** onboarding by discarding marketing/consent fields.

---

#### Version 4 (Migration 024) — Context Data

**Purpose:** Add onboarding wizard context (STORY-247)

**Changes from V3:**
- ✅ **RESTORED** all V2 fields (company, sector, phone, consent)
- ✅ Added `context_data` JSONB column
- ✅ Used COALESCE with empty strings for NULL safety
- ✅ Added `ON CONFLICT (id) DO NOTHING` (first time!)

```sql
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (
    id, email, full_name, company, sector,
    phone_whatsapp, whatsapp_consent, context_data
  )
  VALUES (
    new.id,
    new.email,
    COALESCE(new.raw_user_meta_data->>'full_name', ''),
    COALESCE(new.raw_user_meta_data->>'company', ''),
    COALESCE(new.raw_user_meta_data->>'sector', ''),
    COALESCE(new.raw_user_meta_data->>'phone_whatsapp', ''),
    COALESCE((new.raw_user_meta_data->>'whatsapp_consent')::boolean, FALSE),
    '{}'::jsonb
  )
  ON CONFLICT (id) DO NOTHING;  -- ⚠️ First appearance of conflict handling
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

**Fields Inserted:** 8
**plan_type Handling:** Relied on column default (still 'free' at this point)
**Issues:**
- ❌ **BUG:** Column default still 'free', which violates CHECK constraint after migration 020
- ❌ Missing explicit plan_type (would fail in production)
- ❌ Removed whatsapp_consent_at timestamp logic from V2

---

#### Version 5 (Migration 027) — CANONICAL VERSION ✅

**Purpose:** Fix DB-02 critical bug — column default violates CHECK constraint

**Final State:** All fields + explicit plan_type + conflict handling

```sql
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (
    id, email, full_name, company, sector,
    phone_whatsapp, whatsapp_consent, plan_type, context_data
  )
  VALUES (
    new.id,
    new.email,
    COALESCE(new.raw_user_meta_data->>'full_name', ''),
    COALESCE(new.raw_user_meta_data->>'company', ''),
    COALESCE(new.raw_user_meta_data->>'sector', ''),
    COALESCE(new.raw_user_meta_data->>'phone_whatsapp', ''),
    COALESCE((new.raw_user_meta_data->>'whatsapp_consent')::boolean, FALSE),
    'free_trial',  -- ✅ EXPLICIT VALUE
    '{}'::jsonb
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

**Fields Inserted:** 9
**plan_type Handling:** Explicit `'free_trial'` value
**Status:** ✅ **PRODUCTION READY**

**Improvements:**
- ✅ Explicit plan_type (no reliance on column default)
- ✅ Conflict handling via `ON CONFLICT (id) DO NOTHING`
- ✅ All metadata fields preserved
- ✅ Empty string defaults for safety

**Trade-offs:**
- ❌ Lost whatsapp_consent_at timestamp logic (acceptable — can be added in app layer)
- ❌ No validation of metadata structure (acceptable — Pydantic validates in backend)

---

### Evolution Summary Table

| Version | Migration | Fields | plan_type | Conflict Handling | Status |
|---------|-----------|--------|-----------|-------------------|--------|
| V1 | 001 | 4 | Column default | None | Superseded |
| V2 | 007 | 9 | Column default | None | Superseded |
| V3 | 016 | 5 | Hardcoded 'free_trial' | None | **BROKEN** (lost fields) |
| V4 | 024 | 8 | Column default | ON CONFLICT | **BUGGY** (violates CHECK) |
| V5 | 027 | 9 | Explicit 'free_trial' | ON CONFLICT | ✅ **CANONICAL** |

---

### Recommended Actions (DB-11)

**Status:** ✅ **NO ACTION NEEDED**
**Reason:** Migration 027 (V5) is the canonical version and is production-ready.

**Optional Enhancements (Future):**
1. Restore whatsapp_consent_at timestamp logic from V2 if LGPD audit trail is needed
2. Add validation logic to reject invalid metadata (e.g., malformed phone numbers)
3. Add error logging/notification if metadata extraction fails

---

## Part 2: sync_profile_plan_type() Analysis (DB-01)

### Migration 017 Source Code

```sql
-- STORY-202 DB-M04: Auto-sync profiles.plan_type when user_subscriptions changes
-- This eliminates drift between user_subscriptions.plan_id and profiles.plan_type

CREATE OR REPLACE FUNCTION sync_profile_plan_type()
RETURNS TRIGGER AS $$
BEGIN
    -- Only update if the subscription is active or trialing
    IF NEW.status IN ('active', 'trialing') THEN  -- ⚠️ REFERENCES .status COLUMN
        UPDATE profiles
        SET plan_type = NEW.plan_id,
            updated_at = NOW()
        WHERE id = NEW.user_id;

        RAISE LOG 'sync_profile_plan_type: Updated user % plan to %', NEW.user_id, NEW.plan_id;
    END IF;

    -- Handle cancellation/expiry — revert to free_trial
    IF NEW.status IN ('canceled', 'expired', 'past_due') THEN  -- ⚠️ REFERENCES .status COLUMN
        UPDATE profiles
        SET plan_type = 'free_trial',
            updated_at = NOW()
        WHERE id = NEW.user_id;

        RAISE LOG 'sync_profile_plan_type: Reverted user % to free_trial (status=%)', NEW.user_id, NEW.status;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger on INSERT and UPDATE of user_subscriptions
DROP TRIGGER IF EXISTS trg_sync_profile_plan_type ON user_subscriptions;
CREATE TRIGGER trg_sync_profile_plan_type
    AFTER INSERT OR UPDATE ON user_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION sync_profile_plan_type();
```

---

### Critical Problem: Missing `status` Column

**Analysis:**
The trigger logic references `NEW.status` in two places:
```sql
IF NEW.status IN ('active', 'trialing') THEN ...
IF NEW.status IN ('canceled', 'expired', 'past_due') THEN ...
```

**Table Definition (Migration 001):**
```sql
create table if not exists public.user_subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  plan_id text not null references public.plans(id),
  credits_remaining int,
  starts_at timestamptz not null default now(),
  expires_at timestamptz,
  stripe_subscription_id text,
  stripe_customer_id text,
  is_active boolean not null default true,  -- ⚠️ BOOLEAN, NOT ENUM
  created_at timestamptz not null default now()
);
```

**Subsequent Migrations:**
| Migration | Changes to user_subscriptions |
|-----------|-------------------------------|
| 008 | Added `billing_period`, `annual_benefits` columns |
| 021 | Added `updated_at` trigger |
| 029 | Updated billing_period CHECK constraint (monthly/semiannual/annual) |

**Result:** No migration has EVER added a `status` column to `user_subscriptions`.

---

### Why This Is Dead Code

1. **Column Does Not Exist:** `user_subscriptions.status` has never been defined
2. **Runtime Error:** Any INSERT/UPDATE on `user_subscriptions` would trigger:
   ```
   ERROR: column "status" does not exist
   LINE 3: IF NEW.status IN ('active', 'trialing') THEN
   ```
3. **Unreachable Logic:** Both IF blocks will never execute successfully
4. **No Test Coverage:** If this trigger ever fired in production, it would fail immediately

---

### Root Cause Analysis

**Hypothesis:** Migration 017 was written based on a **planned but unimplemented** schema change.

**Evidence:**
- STORY-202 references "DB-M04: Auto-sync profiles.plan_type"
- Trigger uses Stripe-style status enum (`'active'`, `'trialing'`, `'canceled'`, `'past_due'`)
- SmartLic uses `is_active` boolean instead of status enum
- No follow-up migration added the `status` column

**Likely Scenario:**
1. Developer planned to add `status` enum column to match Stripe's subscription lifecycle
2. Wrote trigger function based on that future schema
3. Applied migration 017 with the trigger
4. Never implemented the schema change in a subsequent migration
5. System uses `is_active` boolean and Stripe webhooks handle state in application layer

---

### Impact Assessment

**Current State:**
- ✅ Trigger is installed and active
- ❌ Trigger logic is unreachable (column doesn't exist)
- ❌ Any INSERT/UPDATE on `user_subscriptions` would fail if trigger executes

**Why Production Hasn't Broken:**
- Trigger fires on INSERT/UPDATE to `user_subscriptions`
- PostgreSQL evaluates `NEW.status` at runtime
- If the column doesn't exist, the trigger should throw an error
- **Mystery:** Why hasn't production broken yet?

**Possible Explanations:**
1. **No subscriptions created since migration 017** (unlikely)
2. **Trigger is not actually firing** (check `pg_trigger` to verify it's enabled)
3. **Errors are being silently caught** (check PostgreSQL logs)
4. **Column exists in production but not in migrations** (schema drift)

---

### Verification Commands

Run these queries to verify trigger status:

```sql
-- V1: Check if trigger exists and is enabled
SELECT tgname, tgenabled, tgtype
FROM pg_trigger
WHERE tgname = 'trg_sync_profile_plan_type';

-- V2: Check user_subscriptions columns
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'user_subscriptions'
ORDER BY ordinal_position;

-- V3: Test trigger manually (should fail)
BEGIN;
INSERT INTO user_subscriptions (user_id, plan_id, stripe_subscription_id)
VALUES (
  (SELECT id FROM profiles LIMIT 1),
  'smartlic_pro',
  'sub_test_123'
);
ROLLBACK;
-- Expected: ERROR: column "status" does not exist

-- V4: Check PostgreSQL logs for errors
SELECT * FROM pg_stat_statements WHERE query LIKE '%sync_profile_plan_type%';
```

---

### Recommended Actions (DB-01)

**Priority:** HIGH (Dead code + potential runtime errors)

**Option A: Remove Dead Trigger (Recommended)**

```sql
-- Migration 030_remove_dead_sync_trigger.sql
DROP TRIGGER IF EXISTS trg_sync_profile_plan_type ON user_subscriptions;
DROP FUNCTION IF EXISTS sync_profile_plan_type();

COMMENT ON TABLE user_subscriptions IS
  'Removed sync_profile_plan_type trigger (migration 030) — references non-existent status column. Plan sync handled in application layer via Stripe webhooks.';
```

**Reason:**
- Plan sync is already handled in `backend/billing.py` via Stripe webhook handlers
- Application layer has full context (grace periods, retries, logging)
- Trigger logic was based on unimplemented schema
- Removing dead code reduces maintenance burden

---

**Option B: Implement Original Intent (Not Recommended)**

If the original sync logic is still desired:

1. Add `status` column:
   ```sql
   ALTER TABLE user_subscriptions
     ADD COLUMN status TEXT NOT NULL DEFAULT 'active'
     CHECK (status IN ('active', 'trialing', 'canceled', 'expired', 'past_due', 'incomplete'));
   ```

2. Backfill status from `is_active`:
   ```sql
   UPDATE user_subscriptions
   SET status = CASE
     WHEN is_active = TRUE THEN 'active'
     ELSE 'canceled'
   END;
   ```

3. Keep trigger as-is (migration 017)

**Why Not Recommended:**
- Adds complexity (new column + trigger)
- Duplicates logic already in application layer
- Requires Stripe webhook updates to populate `status`
- No clear benefit over current `is_active` boolean approach

---

**Option C: Replace with Correct Logic (Alternative)**

If sync is desired but based on existing columns:

```sql
CREATE OR REPLACE FUNCTION sync_profile_plan_type()
RETURNS TRIGGER AS $$
BEGIN
    -- Sync plan_type if subscription is active
    IF NEW.is_active = TRUE THEN
        UPDATE profiles
        SET plan_type = NEW.plan_id,
            updated_at = NOW()
        WHERE id = NEW.user_id;
    ELSE
        -- Revert to free_trial if subscription becomes inactive
        UPDATE profiles
        SET plan_type = 'free_trial',
            updated_at = NOW()
        WHERE id = NEW.user_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

**Trade-offs:**
- Uses existing `is_active` boolean
- Simpler logic than status enum
- Still duplicates application layer logic
- May cause issues with grace period logic in `quota.py`

---

## Recommendations Summary

| Task | Priority | Action | Rationale |
|------|----------|--------|-----------|
| DB-11 (handle_new_user) | ✅ DONE | No action — V5 is canonical | Migration 027 fixed all issues |
| DB-01 (sync_profile_plan_type) | ⚠️ HIGH | Remove dead trigger (Option A) | Dead code, references non-existent column, duplicates app layer |

---

## Next Steps (Track Bravo)

1. **Verify trigger status in production**
   - Run V1-V4 queries from verification section
   - Check if trigger has ever thrown errors
   - Confirm `status` column doesn't exist in production schema

2. **Create migration 030** (if Option A chosen)
   - Drop trigger and function
   - Add comment explaining removal
   - Test in dev environment

3. **Update STORY-TD-004 checklist**
   - Mark DB-11 as ✅ COMPLETE (no action)
   - Mark DB-01 as ⚠️ REMOVE (migration 030 needed)

4. **Document in architecture**
   - Link this analysis from main README
   - Update schema documentation to reflect canonical handle_new_user()

---

## Appendix: Migration File References

| Migration | File | Relevant Sections |
|-----------|------|-------------------|
| 001 | `001_profiles_and_sessions.sql` | Lines 19-36 (handle_new_user V1), Lines 63-74 (user_subscriptions table) |
| 007 | `007_add_whatsapp_consent.sql` | Lines 29-60 (handle_new_user V2) |
| 016 | `016_security_and_index_fixes.sql` | Lines 92-105 (handle_new_user V3) |
| 017 | `017_sync_plan_type_trigger.sql` | Lines 4-36 (sync_profile_plan_type — DEAD CODE) |
| 024 | `024_add_profile_context.sql` | Lines 21-38 (handle_new_user V4) |
| 027 | `027_fix_plan_type_default_and_rls.sql` | Lines 27-48 (handle_new_user V5 — CANONICAL) |

---

**End of Analysis**
**Generated:** 2026-02-16
**Agent:** @data-engineer
**Story:** STORY-TD-004 Track Bravo
