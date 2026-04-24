-- Rollback STORY-OBS-001: revert retention 400→30 days
--
-- WARNING: rolling back will cause the next cron run to purge any rows with
-- data_publicacao older than 30 days. Only run if you explicitly want to
-- shrink the dataset (storage reclaim).

SET statement_timeout = 0;

CREATE OR REPLACE FUNCTION public.purge_old_bids(
    p_retention_days INTEGER DEFAULT 30
)
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_deleted INTEGER;
    v_cutoff  TIMESTAMPTZ;
BEGIN
    IF p_retention_days < 1 THEN
        RAISE EXCEPTION 'p_retention_days must be >= 1, got: %', p_retention_days;
    END IF;

    v_cutoff := now() - (p_retention_days || ' days')::INTERVAL;

    DELETE FROM public.pncp_raw_bids
    WHERE data_publicacao < v_cutoff
      AND is_active = true;

    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END;
$$;

COMMENT ON FUNCTION public.purge_old_bids(INTEGER) IS
    'Deletes active bids with data_publicacao older than p_retention_days (default 30). '
    'Rolled back from 400→30 (revert of STORY-OBS-001). '
    'Returns count of deleted rows.';

GRANT EXECUTE ON FUNCTION public.purge_old_bids(INTEGER) TO service_role;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'purge-old-bids') THEN
        PERFORM cron.unschedule('purge-old-bids');
    END IF;
END $$;

SELECT cron.schedule(
    'purge-old-bids',
    '0 7 * * *',
    $$SELECT public.purge_old_bids(12)$$
);
