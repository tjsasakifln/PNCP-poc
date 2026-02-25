-- STORY-264 AC5-AC7: RLS Policy Hardening
-- AC5: Restrict search_state_transitions INSERT to service_role only
-- AC6: Add service_role ALL policy to profiles
-- AC7: Add service_role ALL policies to conversations and messages

-- ============================================================
-- AC5: search_state_transitions — scope INSERT to service_role
-- ============================================================
-- The original policy (migration 20260221100002) lacked TO service_role,
-- allowing any authenticated user to insert. Fix: scope to service_role.
DROP POLICY IF EXISTS "Service role can insert transitions" ON search_state_transitions;

CREATE POLICY "Service role can insert transitions" ON search_state_transitions
    FOR INSERT TO service_role WITH CHECK (true);

-- ============================================================
-- AC6: profiles — service_role ALL policy
-- ============================================================
DROP POLICY IF EXISTS "profiles_service_all" ON public.profiles;

CREATE POLICY "profiles_service_all" ON public.profiles
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================================
-- AC7: conversations — service_role ALL policy
-- ============================================================
DROP POLICY IF EXISTS "conversations_service_all" ON conversations;

CREATE POLICY "conversations_service_all" ON conversations
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================================
-- AC7: messages — service_role ALL policy
-- ============================================================
DROP POLICY IF EXISTS "messages_service_all" ON messages;

CREATE POLICY "messages_service_all" ON messages
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Reload PostgREST schema cache
NOTIFY pgrst, 'reload schema';
