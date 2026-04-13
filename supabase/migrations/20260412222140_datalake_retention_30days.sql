-- SEO-460: Ampliar retenção datalake de 12 para 30 dias
-- Atualiza o default do RPC purge_old_bids para consistência com INGESTION_RETENTION_DAYS=30
-- (config.py já definia 30; loader.py e este RPC estavam em 12 — corrigidos juntos)

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
    'Changed from 12 to 30 days (SEO-460) to allow more data for thin content threshold. '
    'Returns count of deleted rows. Schedule via pg_cron or external cron job. '
    'SECURITY DEFINER: caller needs only EXECUTE, not DELETE on the table.';

GRANT EXECUTE ON FUNCTION public.purge_old_bids(INTEGER) TO service_role;
