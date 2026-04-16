-- ============================================================================
-- STORY-5.4 (TD-SYS-015) EPIC-TD-2026Q2 P2: portuguese_smartlic FTS config
--
-- Purpose:
--   Create a custom text-search configuration that augments Postgres's
--   builtin 'portuguese' with the `unaccent` filter. Effect on queries:
--   "licitação" and "licitacao" map to the same lexeme at parse time, so
--   users typing without accents still match accented corpora.
--
-- Why not synonym dicts?
--   Supabase Cloud does NOT expose `$SHAREDIR/tsearch_data/*.syn`, so
--   file-based synonym dictionaries cannot be installed. Synonym expansion
--   is handled in Python (`backend/data/fts_synonyms.py` +
--   `datalake_query.expand_synonyms`) — this migration intentionally does
--   NOT register a synonym_dict TEMPLATE dict.
--
-- AC mapping for STORY-5.4:
--   AC1: CREATE TEXT SEARCH CONFIGURATION public.portuguese_smartlic.  ✅ (this file)
--   AC2: Synonyms map — implemented in Python, not Postgres.            ⟶ backend/data/fts_synonyms.py
--   AC3: search_datalake RPC uses new config.                          ⟶ follow-up migration (20260415120001)
--   AC4: Re-index pncp_raw_bids.tsv.                                   ⟶ deferred (off-hours ops, ~40k rows)
--   AC5: Precision/recall benchmark ≥ 5%.                              ⟶ backend/scripts/bench_fts.py (post-deploy)
-- ============================================================================

-- 1. unaccent extension — idempotent; already available on Supabase.
CREATE EXTENSION IF NOT EXISTS unaccent;

-- 2. Clone the builtin portuguese configuration and layer unaccent on top.
--
-- Idempotency: `CREATE TEXT SEARCH CONFIGURATION IF NOT EXISTS` is NOT
-- supported by Postgres, so we use a DO block + pg_ts_config lookup.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_ts_config
        WHERE cfgname = 'portuguese_smartlic'
          AND cfgnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
    ) THEN
        EXECUTE 'CREATE TEXT SEARCH CONFIGURATION public.portuguese_smartlic (COPY = pg_catalog.portuguese)';

        -- Add unaccent as a pre-processing filter in the lexer pipeline.
        -- It runs BEFORE portuguese_stem so the stemmer sees the bare form.
        EXECUTE $alt$
            ALTER TEXT SEARCH CONFIGURATION public.portuguese_smartlic
                ALTER MAPPING FOR hword, hword_part, word
                WITH unaccent, portuguese_stem
        $alt$;
    END IF;
END
$$;

-- 3. Smoke-test that the new config parses at least one token without error.
--    Raises NOTICE on success; RAISE EXCEPTION if the config is unusable.
DO $$
DECLARE
    v_test tsvector;
BEGIN
    SELECT to_tsvector('public.portuguese_smartlic', 'licitação eletrônica') INTO v_test;
    IF v_test IS NULL OR length(v_test::text) = 0 THEN
        RAISE EXCEPTION 'portuguese_smartlic tsvector smoke-test produced empty vector';
    END IF;
    RAISE NOTICE 'portuguese_smartlic config ready (sample tsvector: %)', v_test;
END
$$;

COMMENT ON TEXT SEARCH CONFIGURATION public.portuguese_smartlic IS
    'STORY-5.4 TD-SYS-015: Portuguese FTS config with unaccent filter. '
    'Synonym expansion is handled at query-build time in Python, not via '
    'Postgres synonym dicts (Supabase Cloud does not expose filesystem).';
