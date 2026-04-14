-- ============================================================================
-- STORY-2.12 (TD-DB-015) AC2 EPIC-TD-2026Q2: backfill pncp_raw_bids.data_* NULLs
-- Date: 2026-04-14
-- ============================================================================
-- Context:
--   `data_publicacao` is used as the primary temporal axis by search_datalake
--   (see 20260413000001_search_datalake_hybrid.sql). When it is NULL the row
--   is silently excluded from period-filtered searches.
--
--   Investigation (STORY-2.12 AC1 via audit_pncp_data_nullability.py) showed
--   a non-trivial count of NULL data_publicacao rows — mostly older ingestion
--   records where PNCP returned empty `dataPublicacaoPncp`. Until we guarantee
--   forward-looking non-NULL inserts (AC4, transformer defensive fallback),
--   we need a one-off backfill so those rows become searchable again.
--
--   The fallback is deliberately conservative: `(ingested_at - 1 day)`. That
--   is the newest timestamp we can justify — the bid was definitely published
--   on or before the day we ingested it, and one-day offset keeps it off of
--   "today's" results where it would look spurious.
--
-- Effects:
--   * data_publicacao: backfilled from ingested_at - 1 day where NULL.
--   * data_abertura:   backfilled from data_publicacao where NULL.
--   * data_encerramento: NOT backfilled — NULL is meaningful
--       (treated as "open indefinitely" by p_modo='abertas').
--
-- Idempotent: every UPDATE has a WHERE … IS NULL guard, so re-running is a
-- no-op after the first run.
-- ============================================================================

BEGIN;

SET LOCAL statement_timeout = '10min';

-- 1. data_publicacao: pull from ingested_at - 1 day
UPDATE public.pncp_raw_bids
SET data_publicacao = (ingested_at - INTERVAL '1 day')
WHERE data_publicacao IS NULL;

-- 2. data_abertura: follow data_publicacao (both now non-NULL from step 1)
UPDATE public.pncp_raw_bids
SET data_abertura = data_publicacao
WHERE data_abertura IS NULL
  AND data_publicacao IS NOT NULL;

-- 3. data_encerramento: intentionally left NULL — see header comment.

COMMENT ON COLUMN public.pncp_raw_bids.data_publicacao IS
  'STORY-2.12 (2026-04-14): NULL rows backfilled to (ingested_at - 1 day). '
  'Forward-looking inserts fall back at the transformer layer (backend/ingestion/transformer.py).';

COMMENT ON COLUMN public.pncp_raw_bids.data_abertura IS
  'STORY-2.12 (2026-04-14): NULL rows backfilled to data_publicacao when possible. '
  'Forward-looking inserts fall back to data_publicacao at the transformer layer.';

COMMIT;

-- ============================================================================
-- Verification:
--   SELECT
--     COUNT(*) FILTER (WHERE data_publicacao IS NULL)   AS pub_null,
--     COUNT(*) FILTER (WHERE data_abertura IS NULL)     AS abr_null,
--     COUNT(*) FILTER (WHERE data_encerramento IS NULL) AS enc_null,
--     COUNT(*)                                          AS total
--   FROM public.pncp_raw_bids
--   WHERE is_active = true;
-- ============================================================================
