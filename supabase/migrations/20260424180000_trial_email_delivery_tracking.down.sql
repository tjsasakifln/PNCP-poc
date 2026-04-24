-- Rollback mission sparkling-patterson delivery tracking columns.
-- Safe to apply even if columns are already populated — data is
-- additive observability, no referential integrity lost.

DROP INDEX IF EXISTS idx_trial_email_log_delivery_status;

ALTER TABLE trial_email_log
    DROP COLUMN IF EXISTS bounce_reason,
    DROP COLUMN IF EXISTS failed_at,
    DROP COLUMN IF EXISTS complained_at,
    DROP COLUMN IF EXISTS bounced_at,
    DROP COLUMN IF EXISTS delivered_at,
    DROP COLUMN IF EXISTS delivery_status;
