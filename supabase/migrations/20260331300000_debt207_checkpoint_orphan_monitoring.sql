-- DEBT-207 / DEBT-DB-NEW-002: FK checkpoint orphan monitoring
-- Decision: monitoring over enforced FK (performance — ingestion pipeline
-- does high-frequency upserts and enforced FK adds overhead).
--
-- Creates a diagnostic view to detect orphan checkpoints and a
-- lightweight function callable from ARQ cron or manual audit.

-- ══════════════════════════════════════════════════════════════════
-- View: orphan checkpoints (checkpoints without matching run)
-- ══════════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW public.ingestion_orphan_checkpoints AS
SELECT
  ic.id,
  ic.source,
  ic.uf,
  ic.modalidade_id,
  ic.crawl_batch_id,
  ic.status,
  ic.started_at,
  ic.completed_at
FROM public.ingestion_checkpoints ic
LEFT JOIN public.ingestion_runs ir
  ON ic.crawl_batch_id = ir.crawl_batch_id
WHERE ir.id IS NULL;

COMMENT ON VIEW public.ingestion_orphan_checkpoints IS
  'DEBT-DB-NEW-002: Detects ingestion_checkpoints rows whose crawl_batch_id has no matching ingestion_runs entry. Use for periodic audit.';

-- ══════════════════════════════════════════════════════════════════
-- Function: count orphans (callable from monitoring/cron)
-- ══════════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION public.check_ingestion_orphans()
RETURNS TABLE(orphan_count BIGINT, oldest_orphan TIMESTAMPTZ, sample_batch_ids TEXT[]) AS $$
BEGIN
  RETURN QUERY
  SELECT
    COUNT(*)::BIGINT AS orphan_count,
    MIN(ic.started_at) AS oldest_orphan,
    ARRAY(
      SELECT DISTINCT ic2.crawl_batch_id
      FROM public.ingestion_orphan_checkpoints ic2
      LIMIT 5
    ) AS sample_batch_ids
  FROM public.ingestion_orphan_checkpoints ic;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.check_ingestion_orphans() IS
  'DEBT-DB-NEW-002: Returns orphan checkpoint count, oldest orphan timestamp, and up to 5 sample batch IDs for investigation.';

NOTIFY pgrst, 'reload schema';
