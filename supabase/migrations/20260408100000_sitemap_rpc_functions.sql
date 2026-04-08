-- SEO Onda 1+2: RPC functions for sitemap CNPJ/órgão expansion
-- Replaces Python-level aggregation (which was limited to 1k rows by PostgREST max-rows)
-- These functions run directly in SQL, bypassing the row limit.

-- get_sitemap_cnpjs: returns top CNPJs sorted by bid count, for /cnpj/{cnpj} pages
CREATE OR REPLACE FUNCTION public.get_sitemap_cnpjs(max_results integer DEFAULT 5000)
RETURNS TABLE(orgao_cnpj text, bid_count bigint)
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT orgao_cnpj, COUNT(*) AS bid_count
  FROM pncp_raw_bids
  WHERE is_active = true
    AND orgao_cnpj IS NOT NULL
    AND orgao_cnpj <> ''
    AND length(orgao_cnpj) >= 11
  GROUP BY orgao_cnpj
  ORDER BY bid_count DESC
  LIMIT max_results;
$$;

-- get_sitemap_orgaos: returns top órgãos sorted by bid count, for /orgaos/{cnpj} pages
CREATE OR REPLACE FUNCTION public.get_sitemap_orgaos(max_results integer DEFAULT 2000)
RETURNS TABLE(orgao_cnpj text, bid_count bigint)
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT orgao_cnpj, COUNT(*) AS bid_count
  FROM pncp_raw_bids
  WHERE is_active = true
    AND orgao_cnpj IS NOT NULL
    AND orgao_cnpj <> ''
    AND length(orgao_cnpj) >= 11
  GROUP BY orgao_cnpj
  ORDER BY bid_count DESC
  LIMIT max_results;
$$;

-- Grant execute to anon and authenticated (public sitemap endpoints, no auth)
GRANT EXECUTE ON FUNCTION public.get_sitemap_cnpjs(integer) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_sitemap_orgaos(integer) TO anon, authenticated, service_role;
