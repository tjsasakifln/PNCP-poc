-- ============================================================================
-- Migration: 20260420000001_create_founding_leads
-- Story: STORY-BIZ-001 — Founding Customer Stripe Coupon + Landing /founding
-- Date: 2026-04-20
--
-- Purpose:
--   Persists every qualifying form submission from /founding landing for
--   manual follow-up (abandoned checkouts) and analytics. One row per
--   submission — not per user (user may not exist yet when form submits).
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS public.founding_leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    nome TEXT NOT NULL,
    cnpj TEXT NOT NULL,
    razao_social TEXT,
    motivo TEXT NOT NULL,
    checkout_session_id TEXT,
    checkout_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (checkout_status IN ('pending', 'completed', 'abandoned', 'failed')),
    stripe_customer_id TEXT,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

COMMENT ON TABLE public.founding_leads IS
    'STORY-BIZ-001: /founding form submissions. Pre-checkout captures for '
    'abandoned-cart follow-up + admin analytics. Not joinable to profiles '
    '(user may sign up later with different email).';

CREATE INDEX IF NOT EXISTS idx_founding_leads_email
    ON public.founding_leads (email);

CREATE INDEX IF NOT EXISTS idx_founding_leads_status
    ON public.founding_leads (checkout_status)
    WHERE checkout_status != 'completed';

CREATE INDEX IF NOT EXISTS idx_founding_leads_session_id
    ON public.founding_leads (checkout_session_id)
    WHERE checkout_session_id IS NOT NULL;

-- RLS: admins only.
ALTER TABLE public.founding_leads ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "founding_leads_admin_read" ON public.founding_leads;
CREATE POLICY "founding_leads_admin_read" ON public.founding_leads
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid()
              AND p.plan_type IN ('master')
        )
    );

DROP POLICY IF EXISTS "founding_leads_service_write" ON public.founding_leads;
CREATE POLICY "founding_leads_service_write" ON public.founding_leads
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

COMMIT;
