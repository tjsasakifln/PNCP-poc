-- STORY-OBS-001: Extend pncp_raw_bids retention from 30 to 400 days
--
-- Root cause: /observatorio/raio-x-* and other SEO programmatic pages
-- (alertas, municipios, orgao, dados-publicos) depend on historical data in
-- pncp_raw_bids. Hard-purge after 12/30 days left March 2026 (and earlier
-- months) with 0 rows, so pages rendered 200 OK with Total=0 editais,
-- Valor=R$0 — breaking SEO credibility.
--
-- Fix: retain ~13 months of data (400 days) in pncp_raw_bids. Storage cost
-- is bounded: ~3-5k rows/day × 400 days ≈ 1.2-2M rows. Postgres with the
-- existing indexes (data_publicacao btree, uf btree, tsv GIN) handles this
-- range with sub-second queries.
--
-- Two changes:
--   1. RPC purge_old_bids default: 30 → 400
--   2. pg_cron 'purge-old-bids' invocation: purge_old_bids(12) → purge_old_bids(400)
--
-- Backfill of Jan-Mar 2026 runs post-deploy via scripts/backfill_pncp_historical.py.

SET statement_timeout = 0;

-- 1. Update RPC default
CREATE OR REPLACE FUNCTION public.purge_old_bids(
    p_retention_days INTEGER DEFAULT 400
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
    'Deletes active bids with data_publicacao older than p_retention_days (default 400). '
    'Changed from 30 to 400 days (STORY-OBS-001) so SEO programmatic pages '
    '(observatorio, alertas, municipios, orgao) can query ~13 months of history. '
    'Returns count of deleted rows. Schedule via pg_cron. '
    'SECURITY DEFINER: caller needs only EXECUTE, not DELETE on the table.';

GRANT EXECUTE ON FUNCTION public.purge_old_bids(INTEGER) TO service_role;

-- 2. Reschedule pg_cron job with the new retention window
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'purge-old-bids') THEN
        PERFORM cron.unschedule('purge-old-bids');
    END IF;
END $$;

SELECT cron.schedule(
    'purge-old-bids',
    '0 7 * * *',
    $$SELECT public.purge_old_bids(400)$$
);
