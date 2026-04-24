-- STORY-SEO-013: Partial index pncp_raw_bids.orgao_cnpj WHERE is_active=true
--
-- Root cause de /v1/orgao/{cnpj}/stats levar 443s em producao (seq scan em 1.5M rows).
-- Cascata: trava 1 worker Gunicorn por 443s -> WEB_CONCURRENCY=2 perde 50% capacidade
-- -> /v1/sitemap/cnpjs timeout -> sitemap-4.xml=0 URLs.
--
-- pncp_supplier_contracts ja tem idx_psc_orgao_cnpj (20260409110000_wave2_contratos_indexes).
-- Indice esquecido em pncp_raw_bids no commit original (20260326000000_datalake_raw_bids.sql).
--
-- NOTA producao com tabela ~1.5M rows + writes constantes (ingestion ARQ cron):
--   Para zero downtime, aplicar CONCURRENTLY MANUALMENTE em producao ANTES do merge:
--     psql "$SUPABASE_DB_URL" -c "CREATE INDEX CONCURRENTLY IF NOT EXISTS \
--       idx_pncp_raw_bids_orgao_cnpj ON public.pncp_raw_bids (orgao_cnpj) \
--       WHERE is_active = true;"
--   Padrao seguido de 20260408210000_debt01_index_retention.sql (CONCURRENTLY incompativel
--   com transacao do supabase db push). IF NOT EXISTS torna esta migration idempotente:
--   se index ja existe, supabase db push registra schema_migrations sem efeito.
--
-- Sem aplicacao manual, este CREATE INDEX vai BLOQUEAR writes durante criacao
-- (~30s-2min em 1.5M rows) — janela segura: entre cron runs (2am/8am/2pm/8pm BRT).

CREATE INDEX IF NOT EXISTS idx_pncp_raw_bids_orgao_cnpj
    ON public.pncp_raw_bids (orgao_cnpj)
    WHERE is_active = true;

COMMENT ON INDEX public.idx_pncp_raw_bids_orgao_cnpj IS
    'STORY-SEO-013: unblock /v1/orgao/{cnpj}/stats + sitemap cnpjs. Partial (is_active=true) reduz tamanho ~60%. Paridade com idx_psc_orgao_cnpj em pncp_supplier_contracts.';
