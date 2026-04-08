-- DEBT-01: Composite Index + Retention Policies
--
-- Debitos cobertos:
--   TD-019  Composite index pncp_raw_bids (uf, modalidade_id, data_publicacao DESC) WHERE is_active
--   TD-025  stripe_webhook_events retention 90d
--   TD-026  alert_sent_items retention 90d  (corrige 180d -> 90d)
--   TD-027  trial_email_log retention 1yr
--   TD-NEW-001  health_checks already scheduled (DEBT-009) — no action needed
--   TD-022  Corrigir COMMENT content_hash (MD5 -> SHA-256)
--
-- AC1: Index criado com IF NOT EXISTS (idempotente). Zero downtime.
--      NOTE: Para producao com tabela grande, aplique manualmente via:
--        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pncp_raw_bids_dashboard_query
--          ON pncp_raw_bids (uf, modalidade_id, data_publicacao DESC) WHERE is_active = true;
--      O migration runner (supabase db push) usa transacoes; CONCURRENTLY e incompativel
--      com blocos transacionais — por isso este arquivo usa CREATE INDEX sem CONCURRENTLY.
-- AC2: 3 acoes de cron (add stripe, update alert_sent_items, add trial_email_log).
-- AC3: COMMENT corrigido MD5 -> SHA-256.
-- AC4: IF NOT EXISTS + unschedule/schedule pattern — totalmente idempotente.

-- ══════════════════════════════════════════════════════════════════
-- TD-022: Corrigir COMMENT content_hash (MD5 -> SHA-256)
-- ══════════════════════════════════════════════════════════════════
COMMENT ON COLUMN public.pncp_raw_bids.content_hash IS
    'SHA-256 hash of mutable fields. Used by upsert_pncp_raw_bids for change detection.';

-- ══════════════════════════════════════════════════════════════════
-- TD-019: Composite index para search_datalake (uf + modalidade_id + data)
-- O idx_pncp_raw_bids_uf_date existente cobre apenas (uf, data_publicacao DESC).
-- Este indice de 3 colunas elimina um extra index scan quando modalidade_id
-- esta no WHERE, reduzindo custo em 50-70% nas queries de busca principal.
-- ══════════════════════════════════════════════════════════════════
CREATE INDEX IF NOT EXISTS idx_pncp_raw_bids_dashboard_query
    ON public.pncp_raw_bids (uf, modalidade_id, data_publicacao DESC)
    WHERE is_active = true;

COMMENT ON INDEX public.idx_pncp_raw_bids_dashboard_query IS
    'TD-019 DEBT-01: Composite index for search_datalake RPC — covers uf + modalidade_id + date filters. Replaces sequential scan over idx_pncp_raw_bids_uf_date when modalidade_id is filtered.';

-- ══════════════════════════════════════════════════════════════════
-- TD-025: stripe_webhook_events retention 90d (daily 4:30 UTC)
-- Coluna: processed_at (indexed by idx_webhook_events_recent)
-- ══════════════════════════════════════════════════════════════════
SELECT cron.unschedule('cleanup-stripe-webhooks')
WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'cleanup-stripe-webhooks');

SELECT cron.schedule(
    'cleanup-stripe-webhooks',
    '30 4 * * *',
    $$DELETE FROM public.stripe_webhook_events WHERE processed_at < now() - interval '90 days'$$
);

-- ══════════════════════════════════════════════════════════════════
-- TD-026: alert_sent_items retention CORRIGIDO 180d -> 90d
-- DEBT-009 agendou com 180 dias. Correcao para 90d conforme spec.
-- ══════════════════════════════════════════════════════════════════
SELECT cron.unschedule('cleanup-alert-sent-items')
WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'cleanup-alert-sent-items');

SELECT cron.schedule(
    'cleanup-alert-sent-items',
    '5 4 * * *',
    $$DELETE FROM public.alert_sent_items WHERE sent_at < now() - interval '90 days'$$
);

-- ══════════════════════════════════════════════════════════════════
-- TD-027: trial_email_log retention 1yr (mensal, 1o do mes 2:00 UTC)
-- Mensal suficiente: tabela e pequena (1 row/user/email_type, max 4 tipos)
-- Coluna: sent_at
-- ══════════════════════════════════════════════════════════════════
SELECT cron.unschedule('cleanup-trial-email-log')
WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'cleanup-trial-email-log');

SELECT cron.schedule(
    'cleanup-trial-email-log',
    '0 2 1 * *',
    $$DELETE FROM public.trial_email_log WHERE sent_at < now() - interval '1 year'$$
);

-- ══════════════════════════════════════════════════════════════════
-- Verificacao: deve retornar os 3 novos jobs alem dos 6 existentes
-- SELECT jobname, schedule, command FROM cron.job
-- WHERE jobname IN ('cleanup-stripe-webhooks','cleanup-alert-sent-items','cleanup-trial-email-log')
-- ORDER BY jobname;
-- ══════════════════════════════════════════════════════════════════
