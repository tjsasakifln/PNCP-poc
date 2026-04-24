-- STORY-SEO-013 rollback: drop partial index orgao_cnpj.
-- Se aplicado CONCURRENTLY originalmente, drop tambem deve ser CONCURRENTLY em producao:
--   psql "$SUPABASE_DB_URL" -c "DROP INDEX CONCURRENTLY IF EXISTS public.idx_pncp_raw_bids_orgao_cnpj;"

DROP INDEX IF EXISTS public.idx_pncp_raw_bids_orgao_cnpj;
