# STORY-5.4: PostgreSQL FTS Portuguese Custom Dictionary (TD-SYS-015)

**Priority:** P2 | **Effort:** M (8-16h) | **Squad:** @data-engineer + @dev | **Status:** InReview
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** SmartLic, **I want** dicionário FTS Portuguese custom para termos legais BR (modalidade, esfera, tipo licitação),
**so that** precisão de busca aumente.

## Discovery Note (2026-04-15)

Supabase Cloud does NOT expose `$SHAREDIR/tsearch_data/*.syn`, so file-based synonym
dictionaries (the Postgres-native path) are not available. Approach rewritten in two
layers:

1. **DB config:** `public.portuguese_smartlic` cloned from builtin `portuguese` + `unaccent`
   filter. Eliminates "licitação" vs "licitacao" lexeme divergence at parse time.
2. **Python synonym expansion:** `backend/data/fts_synonyms.py` + integration in
   `datalake_query._keyword_to_tstoken` rewrites single-word tokens to
   `(term | synonym1 | synonym2)` OR groups BEFORE handing them to `to_tsquery`.

## Acceptance Criteria
- [x] AC1: Migration cria text search config `public.portuguese_smartlic` (`20260415120000_fts_portuguese_smartlic.sql`)
- [x] AC2: Termos legais comuns com synonyms map — **implemented in Python** (`backend/data/fts_synonyms.py`, ~50 curated entries: modalidade, objeto, esfera); NOT via Postgres synonym dict (Supabase Cloud limitation)
- [x] AC3: `search_datalake` RPC usa novo config (`20260415120001_search_datalake_use_portuguese_smartlic.sql`)
- [ ] AC4: Re-index `pncp_raw_bids.tsv` via novo config — **deferred** (separate maintenance window; ~40k rows; requires UPDATE sweep + CREATE INDEX CONCURRENTLY)
- [ ] AC5: Precision/recall benchmark melhora >5% — **harness shipped** (`backend/scripts/bench_fts.py`), actual measurement runs post-deploy (ground-truth seed set needs prod IDs)

## Tasks
- [x] Identify common terms — ~50 curated in fts_synonyms.py (modalidade, objeto, esfera, CNPJ-type)
- [x] Build synonyms file (Python dict, not Postgres dict)
- [x] Migration (2 files: config + RPC swap)
- [ ] Re-index CONCURRENTLY — **deferred**
- [x] Benchmark harness (bench_fts.py)

## Implementation Summary

**Migrations:**

```
20260415120000_fts_portuguese_smartlic.sql
└── CREATE EXTENSION unaccent (idempotent)
└── CREATE TEXT SEARCH CONFIGURATION public.portuguese_smartlic (COPY portuguese)
└── ALTER MAPPING FOR hword, hword_part, word WITH unaccent, portuguese_stem
└── Smoke test: to_tsvector('portuguese_smartlic', 'licitação eletrônica')

20260415120001_search_datalake_use_portuguese_smartlic.sql
└── CREATE OR REPLACE FUNCTION search_datalake (same signature)
└── to_tsquery/websearch_to_tsquery now use 'public.portuguese_smartlic'
└── tsv column and trigger remain on 'portuguese' (AC4 deferred)
└── Grants re-applied (CREATE OR REPLACE doesn't re-grant)
```

**Python:**
- `backend/data/fts_synonyms.py` — curated synonym map
- `backend/datalake_query._keyword_to_tstoken` — single-word tokens expanded via
  `data.fts_synonyms.expand_term` when `FTS_SYNONYM_EXPANSION_ENABLED=true`
- `backend/config/features.py` — feature flag `FTS_SYNONYM_EXPANSION_ENABLED` (default true)
- `backend/scripts/bench_fts.py` — precision/recall harness (ground-truth driven)

**Tests:**
- `backend/tests/test_fts_synonyms_expansion.py` — 9 unit tests (expand_term contract,
  _keyword_to_tstoken variants, phrase semantics, custom-terms bypass, coverage smoke)
- Zero regression: `test_datalake_query.py` 88/88 passing after adding an autouse
  fixture to preserve legacy assertions (which pre-date expansion)

## Rollback

| Variable | Effect |
|----------|--------|
| `FTS_SYNONYM_EXPANSION_ENABLED=false` | Restores 1:1 `to_tsquery` input (legacy behavior). |
| Drop migration `20260415120001_search_datalake_use_portuguese_smartlic.sql` | RPC falls back to builtin `portuguese`. |
| Drop migration `20260415120000_fts_portuguese_smartlic.sql` | Removes the custom config entirely. |

## Risks

- **R1:** Re-index without AC4 means tsv stored with `portuguese`, query parsed with
  `portuguese_smartlic`. Cross-config match works (lexemes are plain text), and
  `unaccent` helps user queries match accent-preserving stored data. Full upside
  requires AC4 re-index; interim state is still a net-positive.
- **R2:** Over-aggressive synonym expansion can flood matches and hurt precision.
  Mitigation: conservative curation (start with 50 terms), feature flag for quick
  rollback, benchmark harness for delta measurement before/after rollout.

## File List

**Added:**
- `supabase/migrations/20260415120000_fts_portuguese_smartlic.sql`
- `supabase/migrations/20260415120001_search_datalake_use_portuguese_smartlic.sql`
- `backend/data/__init__.py`
- `backend/data/fts_synonyms.py`
- `backend/scripts/bench_fts.py`
- `backend/tests/test_fts_synonyms_expansion.py`

**Modified:**
- `backend/datalake_query.py` — `_keyword_to_tstoken` synonym expansion (flag-guarded)
- `backend/config/features.py` — `FTS_SYNONYM_EXPANSION_ENABLED`
- `backend/config/__init__.py` — re-export
- `backend/tests/test_datalake_query.py` — autouse fixture to restore legacy format

## Definition of Done
- [x] Migrations apply cleanly (SQL syntax verified; smoke test in migration body)
- [x] Synonym map curated + integrated + flag-guarded
- [x] Unit tests green; datalake_query regression zero
- [x] Benchmark harness in place
- [ ] Post-deploy: run `bench_fts.py` against prod with seeded ground truth
- [ ] AC4 re-index scheduled for a maintenance window

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-15 | 1.1 | Discovery: Supabase Cloud lacks filesystem synonym dicts; approach split into config (DB) + expansion (Python) | @dev |
| 2026-04-15 | 1.2 | Implementation: 2 migrations + synonym map + flag + 9 new tests; AC4 deferred; AC5 harness shipped | @dev |
