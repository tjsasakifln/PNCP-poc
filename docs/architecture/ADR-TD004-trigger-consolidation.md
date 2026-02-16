# ADR-TD004-002: Database Trigger Consolidation Strategy

**Date:** 2026-02-15
**Status:** Proposed
**Deciders:** @architect, @data-engineer, @dev
**Author:** @architect (Aria)
**Story:** STORY-TD-004
**Dependencies:** STORY-TD-001 production verification (V1-V5 queries)

---

## Context

### Current State

The SmartLic/BidIQ database contains multiple trigger functions that have been redefined across several migrations, leading to confusion about which version is active and potential dead code.

#### 1. handle_new_user() Trigger Evolution

This trigger creates a `profiles` row when a new user signs up via Supabase Auth. It has been **redefined 4 times**:

| Migration | Date | Key Changes | Story |
|-----------|------|-------------|-------|
| **001** (initial) | 2026-01-XX | Basic user creation, `plan_type = 'free'` default | Initial schema |
| **007** | 2026-01-XX | Added `context_data` jsonb field | Context storage |
| **016** | 2026-01-XX | Added `phone_whatsapp`, `whatsapp_consent` fields | Contact info |
| **024** | 2026-01-XX | Added `sector` field for user categorization | Sector targeting |
| **027** (canonical) | 2026-02-15 | **CRITICAL FIX:** Changed default from `'free'` to `'free_trial'` to match CHECK constraint | STORY-TD-001 DB-02 |

**Current Active Version (migration 027):**
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
    'free_trial',  -- FIXED: was 'free' in migrations 001-024
    '{}'::jsonb
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

#### 2. sync_profile_plan_type() Trigger (Potentially Dead Code)

This trigger was introduced in migration 017 (STORY-202 DB-M04) to auto-sync `profiles.plan_type` when `user_subscriptions` changes.

**Implementation (migration 017):**
```sql
CREATE OR REPLACE FUNCTION sync_profile_plan_type()
RETURNS TRIGGER AS $$
BEGIN
    -- Only update if the subscription is active or trialing
    IF NEW.status IN ('active', 'trialing') THEN
        UPDATE profiles
        SET plan_type = NEW.plan_id,
            updated_at = NOW()
        WHERE id = NEW.user_id;
    END IF;

    -- Handle cancellation/expiry — revert to free_trial
    IF NEW.status IN ('canceled', 'expired', 'past_due') THEN
        UPDATE profiles
        SET plan_type = 'free_trial',
            updated_at = NOW()
        WHERE id = NEW.user_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS trg_sync_profile_plan_type ON user_subscriptions;
CREATE TRIGGER trg_sync_profile_plan_type
    AFTER INSERT OR UPDATE ON user_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION sync_profile_plan_type();
```

**Problem:** The trigger references `NEW.status`, but STORY-TD-001 verification queries (V1-V5) need to determine if the `user_subscriptions.status` column actually exists in production.

### Problem Statement

1. **Trigger Version Confusion (DB-11)**
   - Developers cannot easily determine which `handle_new_user()` version is active
   - Migration history shows 4 redefinitions without clear rationale for each change
   - No single source of truth documenting the evolution

2. **Potential Dead Code (DB-01)**
   - If `user_subscriptions.status` column does NOT exist (per V1 results), then `sync_profile_plan_type()` trigger is dead code that will FAIL on INSERT/UPDATE
   - If column EXISTS but is unused, trigger may execute but serve no purpose
   - Unclear if trigger was designed for future functionality or legacy artifact

3. **Maintenance Burden**
   - Multiple trigger definitions scattered across migrations make schema audits time-consuming
   - Risk of reintroducing bugs when making future changes
   - Difficult to trace which migration introduced which functionality

---

## Decision Drivers

1. **Clarity:** Developers must be able to quickly understand which trigger version is active and why
2. **Maintainability:** Reduce redundant trigger definitions to minimize confusion
3. **Correctness:** Remove or document dead code to prevent runtime failures
4. **Backward Compatibility:** Trigger consolidation must not break existing signup flows
5. **Data-Driven:** Decisions about `sync_profile_plan_type()` must wait for V1-V5 verification results from TD-001

---

## Considered Options

### Option 1: Full Consolidation (Rewrite all triggers in single migration)

**Approach:**
- Create migration 029 that drops ALL existing triggers
- Redefine both `handle_new_user()` and `sync_profile_plan_type()` in single migration
- Add comprehensive comments documenting evolution

**Pros:**
- Single source of truth for all triggers
- Clean slate removes historical baggage
- Easy to audit and test

**Cons:**
- High risk if signup flow breaks (critical user-facing feature)
- May conflict with future migrations if done prematurely
- Requires extensive regression testing

**Verdict:** **REJECTED** — Too risky for production system, especially before V1-V5 results confirmed

---

### Option 2: Documentation-First Approach (RECOMMENDED)

**Approach:**
1. **Immediate:** Document trigger evolution in this ADR and migration comments
2. **Phase 1 (TD-004):** Confirm migration 027 is canonical for `handle_new_user()`
3. **Phase 2 (TD-005):** Based on V1-V5 results, decide fate of `sync_profile_plan_type()`:
   - If `status` column missing → Remove trigger in migration 029, document as dead code
   - If `status` column exists → Verify trigger behavior, document flow, keep active
4. **Future Consolidation (post-GTM):** After signup flow stabilizes, consider consolidation in dedicated story

**Pros:**
- Low risk — no immediate code changes
- Allows data-driven decision for `sync_profile_plan_type()`
- Preserves working state while improving documentation
- Clear roadmap for future cleanup

**Cons:**
- Trigger duplication persists in short term
- Requires follow-up story for full consolidation

**Verdict:** **SELECTED** — Balances safety with long-term maintainability

---

### Option 3: Immediate Removal of sync_profile_plan_type()

**Approach:**
- Assume `status` column does not exist (based on preliminary findings)
- Drop `sync_profile_plan_type()` trigger in migration 028 alongside webhook RLS fix

**Pros:**
- Quick removal of potential dead code
- Simpler schema

**Cons:**
- **RISKY:** If `status` column DOES exist and trigger is active, this breaks subscription sync
- Couples unrelated changes (webhook RLS + trigger removal) in single migration
- Premature without V1-V5 confirmation

**Verdict:** **REJECTED** — Too risky without verification data

---

## Decision Outcome

**Chosen Option: Documentation-First Approach (Option 2)**

### Phase 1: handle_new_user() Standardization (STORY-TD-004)

#### Decision

**Migration 027 is the CANONICAL version** of `handle_new_user()`.

#### Rationale

1. **Critical Bug Fix:** Migration 027 corrects the `plan_type = 'free'` bug that violated the CHECK constraint introduced in migration 020
2. **Most Complete:** Includes all fields from previous iterations (context_data, sector, phone_whatsapp, whatsapp_consent)
3. **Production-Tested:** Deployed as part of TD-001 and verified with V8 test (new user creation)
4. **Correct Semantics:** `'free_trial'` aligns with business logic (new users start on trial, not legacy "free" plan)

#### Evolution Documentation

| Migration | Trigger Function Fields | Rationale |
|-----------|------------------------|-----------|
| 001 | `id, email, full_name, company, plan_type='free'` | Initial implementation |
| 007 | Added `context_data` | Store user preferences/session data as JSONB |
| 016 | Added `phone_whatsapp, whatsapp_consent` | LGPD compliance, WhatsApp marketing consent tracking |
| 024 | Added `sector` | Enable sector-based filtering and targeting |
| 027 | **Changed `plan_type='free'` → `'free_trial'`** | **FIX:** Align with CHECK constraint from migration 020 |

#### Consequences

**Positive:**
- Clear canonical version documented
- No code changes needed (migration 027 already deployed)
- Future developers know to reference migration 027

**Negative:**
- Migrations 001, 007, 016, 024 remain as historical artifacts (low impact, standard migration pattern)

**Risks:**
- None — migration 027 already verified in production via TD-001 V8 test

---

### Phase 2: sync_profile_plan_type() Resolution (STORY-TD-005, Dependent on TD-001)

#### Decision Framework

**IF** V1 query results show `user_subscriptions.status` column **DOES NOT EXIST**:

```sql
-- Migration 029: Remove dead code trigger
DROP TRIGGER IF EXISTS trg_sync_profile_plan_type ON user_subscriptions;
DROP FUNCTION IF EXISTS sync_profile_plan_type();

COMMENT ON TABLE user_subscriptions IS
  'Migration 017 trigger sync_profile_plan_type() removed in migration 029 because status column does not exist. Trigger was dead code that would fail on execution.';
```

**IF** V1 query results show `user_subscriptions.status` column **EXISTS**:

1. **Verify trigger behavior:**
   ```sql
   -- V1a: Check for any subscriptions using status column
   SELECT status, COUNT(*) FROM user_subscriptions GROUP BY status;
   ```

2. **Document the flow:**
   - Create `docs/database/trigger-flows.md` explaining subscription → profile sync
   - Document relationship between `user_subscriptions.status` and `profiles.plan_type`
   - Clarify when trigger fires vs. when backend code updates plan_type directly

3. **Keep trigger active** if it serves a functional purpose OR **remove** if redundant with Stripe webhook handlers

#### Acceptance Criteria (TD-004)

- [ ] **AC: Trigger Evolution Documented** — This ADR documents all 4 versions of `handle_new_user()` with rationale
- [ ] **AC: Migration 027 Marked Canonical** — Clear statement that migration 027 is the reference implementation
- [ ] **AC: V1 Dependency Explicit** — sync_profile_plan_type() decision explicitly deferred until V1 results available
- [ ] **AC: Rollback Path Defined** — If consolidation causes issues, rollback to migration 027 state

---

## Implementation Plan

### Immediate Actions (STORY-TD-004)

1. **Document Evolution:**
   - [x] Create this ADR documenting trigger history
   - [ ] Add migration comment to migration 027 marking it as canonical

2. **Mark Canonical Version:**
   ```sql
   -- Add to migration 027 (retroactive documentation)
   COMMENT ON FUNCTION handle_new_user() IS
     'CANONICAL VERSION (migration 027): Creates profile on user signup. This is the authoritative implementation after 4 revisions (001, 007, 016, 024, 027). See ADR-TD004-002 for evolution history.';
   ```

3. **Document Uncertainty:**
   - [x] Explicitly mark `sync_profile_plan_type()` as "pending V1 verification"
   - [x] Create decision framework for Phase 2 based on V1 results

### Future Actions (STORY-TD-005, after TD-001 completion)

4. **Execute Phase 2 Decision:**
   - Run V1 query to check for `user_subscriptions.status` column
   - If column missing → Create migration 029 to drop trigger
   - If column exists → Run V1a to verify usage, document flow

5. **Full Consolidation (Optional, Post-GTM):**
   - After signup flow stabilizes (no changes for 2+ sprints)
   - Create dedicated story for trigger consolidation migration
   - Rewrite all triggers in single migration with comprehensive tests
   - Add CI check to prevent future trigger fragmentation

---

## Consequences

### Positive

1. **Improved Clarity:** Evolution of `handle_new_user()` now documented and understandable
2. **Risk Mitigation:** Data-driven approach prevents premature removal of potentially active trigger
3. **Maintainability:** Future developers have clear reference for trigger versions
4. **Incremental Safety:** No immediate code changes reduce deployment risk

### Negative

1. **Short-Term Duplication:** Trigger definitions remain scattered across migrations until Phase 2
2. **Delayed Cleanup:** Full consolidation deferred to future story
3. **Dependency on TD-001:** Cannot complete TD-004 until V1-V5 verification runs

### Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| V1 results delayed | Medium | Low | TD-004 can proceed with documentation tasks; trigger decision is separate AC |
| sync_profile_plan_type() is critical | Low | High | If V1 shows usage, keep trigger and document thoroughly; consolidation deferred |
| Future trigger changes conflict | Medium | Medium | Migration 027 marked as canonical; future changes MUST reference this ADR |

---

## Testing Strategy

### handle_new_user() (Already Verified in TD-001)

| Test ID | Test Description | Status |
|---------|------------------|--------|
| V8 | New user creation → profile has plan_type='free_trial' | ✅ PASS (TD-001) |
| REG-T03 | Admin creates user without explicit plan_id → default 'free_trial' | Pending TD-004 |

### sync_profile_plan_type() (Pending V1 Results)

| Scenario | Test | Action |
|----------|------|--------|
| Column missing | V1 returns 0 rows or error | Remove trigger in migration 029 |
| Column exists | V1a shows usage | Document flow, add regression tests |
| Column exists but unused | V1a shows 0 rows | Remove trigger, document as dead code |

---

## Related Documents

- **Migration 001:** Initial `handle_new_user()` definition
- **Migration 007:** Added `context_data` field
- **Migration 016:** Added `phone_whatsapp`, `whatsapp_consent`
- **Migration 017:** Introduced `sync_profile_plan_type()` trigger
- **Migration 024:** Added `sector` field
- **Migration 027:** **CANONICAL** — Fixed `plan_type` default to `'free_trial'`
- **STORY-TD-001:** Post-deployment verification (V1-V8 queries)
- **STORY-TD-004:** Security and documentation (this story)
- **ADR-TD004-001:** Webhook RLS security hardening

---

## References

- PostgreSQL Trigger Best Practices: https://www.postgresql.org/docs/current/trigger-definition.html
- Supabase Auth Triggers: https://supabase.com/docs/guides/auth/managing-user-data#using-triggers
- Database Refactoring: Martin Fowler, "Refactoring Databases" (Addison-Wesley, 2006)

---

**END OF ADR-TD004-002**
