-- mission sparkling-patterson: trial_email_log delivery tracking
--
-- Baseline 2026-04-24 diagnostic: 14 trial emails sent (9 in 30d),
-- 0 opens / 0 clicks lifetime. Resend webhook endpoint exists
-- (backend/routes/trial_emails.py::resend_webhook) but only handles
-- email.opened and email.clicked. This migration adds the columns
-- needed to track email.delivered / email.bounced / email.complained
-- events so we can distinguish "email never arrived" from "email
-- arrived but user didn't open".
--
-- Once Resend dashboard is configured to POST to
-- https://api.smartlic.tech/trial-emails/webhook, the extended
-- service handler populates these columns.

ALTER TABLE trial_email_log
    ADD COLUMN IF NOT EXISTS delivery_status TEXT
        CHECK (delivery_status IN (
            'queued', 'sent', 'delivered', 'opened', 'clicked',
            'bounced', 'complained', 'delivery_delayed', 'failed'
        )),
    ADD COLUMN IF NOT EXISTS delivered_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS bounced_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS complained_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS failed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS bounce_reason TEXT;

COMMENT ON COLUMN trial_email_log.delivery_status IS
    'Current Resend delivery state: queued|sent|delivered|opened|clicked|bounced|complained|delivery_delayed|failed. NULL = tracking not yet populated (Resend webhook not configured before 2026-04-24).';
COMMENT ON COLUMN trial_email_log.delivered_at IS
    'Timestamp from email.delivered Resend webhook event.';
COMMENT ON COLUMN trial_email_log.bounced_at IS
    'Timestamp from email.bounced Resend webhook event.';
COMMENT ON COLUMN trial_email_log.complained_at IS
    'Timestamp from email.complained Resend webhook event (user marked as spam).';
COMMENT ON COLUMN trial_email_log.failed_at IS
    'Timestamp from email.failed Resend webhook event.';
COMMENT ON COLUMN trial_email_log.bounce_reason IS
    'Human-readable bounce category from Resend payload (e.g. hard, soft, mailbox_full).';

-- Partial index for admin funnel dashboards that filter by status.
CREATE INDEX IF NOT EXISTS idx_trial_email_log_delivery_status
    ON trial_email_log(delivery_status)
    WHERE delivery_status IS NOT NULL;
