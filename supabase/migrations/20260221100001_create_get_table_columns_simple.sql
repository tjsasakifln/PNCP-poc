-- CRIT-004 AC5: RPC function for schema validation
-- Enables schema contract checks without direct database access
-- Used by backend startup validation and cache schema checks

CREATE OR REPLACE FUNCTION get_table_columns_simple(p_table_name TEXT)
RETURNS TABLE(column_name TEXT)
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT column_name::TEXT
  FROM information_schema.columns
  WHERE table_schema = 'public'
    AND table_name = p_table_name
  ORDER BY ordinal_position;
$$;

GRANT EXECUTE ON FUNCTION get_table_columns_simple(TEXT) TO authenticated, service_role;

COMMENT ON FUNCTION get_table_columns_simple IS
  'CRIT-004 AC5: Returns column names for a table for schema validation';
