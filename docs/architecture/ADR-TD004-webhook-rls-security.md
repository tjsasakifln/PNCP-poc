# ADR-TD004-001: Stripe Webhook Events RLS Security Hardening

**Date:** 2026-02-15
**Status:** Accepted
**Deciders:** @architect, @devops, @dev
**Author:** @architect (Aria)
**Story:** STORY-TD-004
**Related Migration:** 028_fix_stripe_webhook_events_rls.sql

---

## Context

### Current State

The `stripe_webhook_events` table was introduced in migration 010 (STORY-171) to prevent duplicate webhook processing through idempotency checks. The table stores Stripe event IDs (`evt_xxx`) with full payloads for debugging and compliance.

The original RLS (Row Level Security) policies had the following configuration:

```sql
-- Migration 010 (original)
CREATE POLICY "webhook_events_insert_service" ON public.stripe_webhook_events
  FOR INSERT
  WITH CHECK (true);  -- Service role bypasses RLS

CREATE POLICY "webhook_events_select_admin" ON public.stripe_webhook_events
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE profiles.id = auth.uid() AND profiles.plan_type = 'master'
    )
  );

GRANT SELECT ON public.stripe_webhook_events TO authenticated;
GRANT INSERT ON public.stripe_webhook_events TO service_role;
```

### Problem Statement

During the STORY-TD-001 post-deployment verification (V6 query), we discovered two security vulnerabilities:

1. **Critical: Overly Permissive INSERT Policy (DB-05)**
   - Policy name: `webhook_events_insert_service`
   - **Observed behavior:** `roles={public}`, `WITH CHECK=true`
   - **Risk:** ANY authenticated user can insert arbitrary webhook events
   - **Impact:** User could inject fake Stripe events, potentially triggering unauthorized subscription changes or billing actions
   - **Mitigation (partial):** The `CHECK (id ~ '^evt_')` constraint prevents non-Stripe event IDs, but this is insufficient protection

2. **Medium: Unnecessarily Broad SELECT Policy (DB-06)**
   - Policy name: `webhook_events_select_admin`
   - **Observed behavior:** `roles={public}`, `USING=(is_admin check)`
   - **Issue:** The `USING` clause is functionally correct (only admins can select), but granting to `public` is unnecessarily broad
   - **Best practice:** Should be scoped to `authenticated` role since anonymous users can never satisfy `auth.uid()` check anyway

### Verification Query Results (V6)

```sql
SELECT policyname, roles, cmd, qual, with_check
FROM pg_policies
WHERE tablename = 'stripe_webhook_events'
ORDER BY policyname;
```

**Before migration 028:**
| policyname | roles | cmd | qual | with_check |
|------------|-------|-----|------|------------|
| webhook_events_insert_service | {public} | INSERT | NULL | true |
| webhook_events_select_admin | {public} | SELECT | (EXISTS ...) | NULL |

---

## Decision Drivers

1. **Security:** Only the backend service (service_role) should insert webhook events
2. **Least Privilege:** Policies should grant minimum necessary permissions
3. **Defense in Depth:** Even if service_role key leaks, CHECK constraints provide secondary protection
4. **Backend Diagnostics:** Service role needs SELECT access for webhook retry/debugging operations
5. **Backward Compatibility:** Admin SELECT functionality must remain intact

---

## Decision Outcome

**Implemented in migration 028:**

### 1. Restrict INSERT to service_role only

```sql
DROP POLICY IF EXISTS "webhook_events_insert_service"
  ON public.stripe_webhook_events;

CREATE POLICY "webhook_events_insert_service"
  ON public.stripe_webhook_events
  FOR INSERT
  TO service_role
  WITH CHECK (true);
```

**Rationale:**
- Only the backend webhook handler runs with `service_role` credentials
- Prevents authenticated users from inserting fake events
- `WITH CHECK (true)` is safe here because only service_role can reach it

### 2. Scope SELECT policy to authenticated role

```sql
DROP POLICY IF EXISTS "webhook_events_select_admin"
  ON public.stripe_webhook_events;

CREATE POLICY "webhook_events_select_admin"
  ON public.stripe_webhook_events
  FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
        AND profiles.is_admin = true
    )
  );
```

**Rationale:**
- Anonymous (`anon`) users cannot satisfy `auth.uid()` check
- Scoping to `authenticated` follows principle of least privilege
- Functional behavior unchanged (only admins can still SELECT)

### 3. Add service_role SELECT for diagnostics

```sql
CREATE POLICY "webhook_events_service_role_select"
  ON public.stripe_webhook_events
  FOR SELECT
  TO service_role
  USING (true);
```

**Rationale:**
- Backend may need to query webhook events for retry logic or debugging
- Separate policy makes permissions explicit and auditable

---

## Consequences

### Positive

1. **Closed Critical Vulnerability:** Authenticated users can no longer insert fake webhook events
2. **Improved Security Posture:** All policies now follow least-privilege principle
3. **Better Auditability:** Explicit `service_role` SELECT policy makes backend access traceable
4. **Defense in Depth:** Even if `service_role` key leaks, the `CHECK (id ~ '^evt_')` constraint prevents arbitrary event IDs

### Negative

1. **None Identified:** This is a pure security hardening with no functional trade-offs

### Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Backend webhook processing fails | Low | High | Tested with SEC-T04, SEC-T05; Stripe webhooks must continue processing normally (AC3) |
| Service role key leak | Low | Medium | CHECK constraint `'^evt_'` provides secondary defense; monitor for anomalous event patterns |
| Policy conflict with future extensions | Low | Low | Migration 028 can be rolled back independently; well-documented policies make future changes clear |

---

## Verification

### Expected Policy State (after migration 028)

```sql
SELECT policyname, roles, cmd
FROM pg_policies
WHERE tablename = 'stripe_webhook_events'
ORDER BY policyname;
```

| policyname | roles | cmd |
|------------|-------|-----|
| webhook_events_insert_service | {service_role} | INSERT |
| webhook_events_select_admin | {authenticated} | SELECT |
| webhook_events_service_role_select | {service_role} | SELECT |

### Test Cases (STORY-TD-004)

| Test ID | Test Description | Expected Result |
|---------|------------------|-----------------|
| SEC-T04 | INSERT with authenticated key | FAIL (permission denied) |
| SEC-T05 | INSERT with id='not_evt_xxx' | FAIL (CHECK constraint violation) |
| AC3 | Stripe webhook processing after fix | SUCCESS (webhooks process normally) |

---

## Related Documents

- **Migration 010:** `supabase/migrations/010_stripe_webhook_events.sql` (original table definition)
- **Migration 027:** `supabase/migrations/027_fix_plan_type_default_and_rls.sql` (TD-001 RLS fixes for `pipeline_items`, `search_results_cache`)
- **STORY-TD-001:** Post-deployment verification that discovered DB-05 and DB-06
- **STORY-TD-004:** Security remediation story for remaining RLS gaps
- **STORY-171:** Original story that introduced webhook events table

---

## References

- Supabase RLS Best Practices: https://supabase.com/docs/guides/auth/row-level-security
- Stripe Webhook Security: https://stripe.com/docs/webhooks/best-practices
- PostgreSQL Policies: https://www.postgresql.org/docs/current/sql-createpolicy.html

---

**END OF ADR-TD004-001**
