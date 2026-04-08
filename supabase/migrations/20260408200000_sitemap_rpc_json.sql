-- SEO Onda 1+2: RPC functions returning JSON scalar (bypasses PostgREST max-rows=1000)
-- RETURNS json (scalar) is not subject to the row-count limit that TABLE/SETOF are.

-- get_sitemap_cnpjs_json: returns JSON array of top CNPJs (no row-count cap)
CREATE OR REPLACE FUNCTION public.get_sitemap_cnpjs_json(max_results integer DEFAULT 5000)
RETURNS json
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT COALESCE(json_agg(t.orgao_cnpj ORDER BY t.bid_count DESC), '[]'::json)
  FROM (
    SELECT orgao_cnpj, COUNT(*) AS bid_count
    FROM pncp_raw_bids
    WHERE is_active = true
      AND orgao_cnpj IS NOT NULL
      AND orgao_cnpj <> ''
      AND length(orgao_cnpj) >= 11
    GROUP BY orgao_cnpj
    ORDER BY bid_count DESC
    LIMIT max_results
  ) t;
$$;

-- get_sitemap_orgaos_json: returns JSON array of top órgãos (no row-count cap)
CREATE OR REPLACE FUNCTION public.get_sitemap_orgaos_json(max_results integer DEFAULT 2000)
RETURNS json
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT COALESCE(json_agg(t.orgao_cnpj ORDER BY t.bid_count DESC), '[]'::json)
  FROM (
    SELECT orgao_cnpj, COUNT(*) AS bid_count
    FROM pncp_raw_bids
    WHERE is_active = true
      AND orgao_cnpj IS NOT NULL
      AND orgao_cnpj <> ''
      AND length(orgao_cnpj) >= 11
    GROUP BY orgao_cnpj
    ORDER BY bid_count DESC
    LIMIT max_results
  ) t;
$$;

GRANT EXECUTE ON FUNCTION public.get_sitemap_cnpjs_json(integer) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_sitemap_orgaos_json(integer) TO anon, authenticated, service_role;
