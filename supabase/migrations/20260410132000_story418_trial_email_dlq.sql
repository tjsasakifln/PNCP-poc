-- STORY-418: Trial email dead-letter queue.
--
-- Context:
--   ``backend/services/trial_email_sequence.py::process_trial_emails``
--   currently catches any render/send exception at the innermost loop
--   and logs it — nothing else. When Supabase is flaky (CB open) or
--   Resend is throttled, the affected emails are **lost forever**:
--   there is no retry, no backlog, no audit trail. The 2026-04-10
--   incident documented 23 such lost events across three milestones.
--
-- Scope:
--   * New table ``trial_email_dlq`` that stores the full context needed
--     to retry a failed delivery (user, email type/number, payload JSON,
--     attempt counter, last error).
--   * RLS lock to ``service_role`` only — regular authenticated users
--     must never see the DLQ (it may contain PII like email address,
--     full_name, and stats used for personalisation).
--   * Partial index on ``reprocessed_at IS NULL`` so the daily cron
--     job scans only pending rows instead of the full table.
--   * Helper RPC ``dlq_claim_pending`` left out on purpose — the cron
--     runs as service_role and is happy to SELECT + UPDATE directly.

CREATE TABLE IF NOT EXISTS public.trial_email_dlq (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    email_address   text NOT NULL,
    email_type      text NOT NULL,
    email_number    integer NOT NULL,
    payload         jsonb NOT NULL DEFAULT '{}'::jsonb,
    attempts        integer NOT NULL DEFAULT 0,
    last_error      text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    next_retry_at   timestamptz NOT NULL DEFAULT now(),
    reprocessed_at  timestamptz,
    reprocessed_count integer NOT NULL DEFAULT 0,
    abandoned_at    timestamptz
);

COMMENT ON TABLE public.trial_email_dlq IS
    'STORY-418: Dead-letter queue for failed trial email deliveries. '
    'Populated by services/trial_email_sequence on send failure, drained '
    'by the reprocess_trial_email_dlq cron (9am BRT daily).';

-- Partial index is cheaper than a full index because the vast majority
-- of rows will be reprocessed within 24h and carry reprocessed_at.
CREATE INDEX IF NOT EXISTS trial_email_dlq_pending_idx
    ON public.trial_email_dlq (next_retry_at)
    WHERE reprocessed_at IS NULL AND abandoned_at IS NULL;

CREATE INDEX IF NOT EXISTS trial_email_dlq_user_idx
    ON public.trial_email_dlq (user_id);

-- RLS: nobody outside service_role can read or write the DLQ.
ALTER TABLE public.trial_email_dlq ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "trial_email_dlq_service_only" ON public.trial_email_dlq;
CREATE POLICY "trial_email_dlq_service_only"
    ON public.trial_email_dlq
    FOR ALL
    USING (
        coalesce(current_setting('request.jwt.claim.role', true),
                 current_setting('role', true)) = 'service_role'
    )
    WITH CHECK (
        coalesce(current_setting('request.jwt.claim.role', true),
                 current_setting('role', true)) = 'service_role'
    );

REVOKE ALL ON public.trial_email_dlq FROM PUBLIC;
REVOKE ALL ON public.trial_email_dlq FROM authenticated;
REVOKE ALL ON public.trial_email_dlq FROM anon;
