-- Contract-compatible fixture for extra-cli public_read_v1 v1.0.0
-- Column names/types match origin/main db/migrations/089 + 090 views.
-- This is not a fake adapter: SmartLic talks to these objects via SELECT.

CREATE SCHEMA IF NOT EXISTS public_read_v1;

CREATE TABLE IF NOT EXISTS public_read_v1.current_snapshot (
    snapshot_id     TEXT PRIMARY KEY,
    as_of           TIMESTAMPTZ NOT NULL,
    content_hash    TEXT,
    universe_hash   TEXT,
    policy_hash     TEXT,
    schema_hash     TEXT,
    adapter_hash    TEXT,
    data_hash       TEXT,
    document_hash   TEXT,
    dossier_hash    TEXT,
    closed_at       TIMESTAMPTZ,
    completeness    TEXT NOT NULL,
    provenance      JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE TABLE IF NOT EXISTS public_read_v1.tenders (
    event_id            TEXT NOT NULL,
    process_key         TEXT NOT NULL,
    event_type          TEXT NOT NULL,
    status_code         TEXT,
    title               TEXT,
    publication_at      TIMESTAMPTZ,
    official_number     TEXT,
    as_of               TIMESTAMPTZ NOT NULL,
    source_updated_at   TIMESTAMPTZ,
    completeness        TEXT NOT NULL,
    reason_codes        TEXT[] NOT NULL DEFAULT '{}',
    source              TEXT,
    source_uri          TEXT,
    provenance          JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE TABLE IF NOT EXISTS public_read_v1.contracts (
    event_id            TEXT NOT NULL,
    process_key         TEXT NOT NULL,
    status_code         TEXT,
    title               TEXT,
    contract_value      NUMERIC,
    official_number     TEXT,
    as_of               TIMESTAMPTZ NOT NULL,
    source_updated_at   TIMESTAMPTZ,
    completeness        TEXT NOT NULL,
    reason_codes        TEXT[] NOT NULL DEFAULT '{}',
    source              TEXT,
    source_uri          TEXT,
    provenance          JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE TABLE IF NOT EXISTS public_read_v1.entities (
    entity_id                 TEXT NOT NULL,
    entity_type               TEXT NOT NULL,
    display_name              TEXT,
    tax_identifier_type       TEXT,
    tax_identifier_export     TEXT,
    as_of                     TIMESTAMPTZ NOT NULL,
    source_updated_at         TIMESTAMPTZ,
    completeness              TEXT NOT NULL,
    reason_codes              TEXT[] NOT NULL DEFAULT '{}',
    provenance                JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE TABLE IF NOT EXISTS public_read_v1.suppliers (
    entity_id                 TEXT NOT NULL,
    entity_type               TEXT NOT NULL,
    display_name              TEXT,
    tax_identifier_type       TEXT,
    tax_identifier_export     TEXT,
    as_of                     TIMESTAMPTZ NOT NULL,
    source_updated_at         TIMESTAMPTZ,
    completeness              TEXT NOT NULL,
    reason_codes              TEXT[] NOT NULL DEFAULT '{}',
    provenance                JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE TABLE IF NOT EXISTS public_read_v1.organs (
    entity_id                 TEXT NOT NULL,
    entity_type               TEXT NOT NULL,
    display_name              TEXT,
    tax_identifier_type       TEXT,
    tax_identifier_export     TEXT,
    as_of                     TIMESTAMPTZ NOT NULL,
    source_updated_at         TIMESTAMPTZ,
    completeness              TEXT NOT NULL,
    reason_codes              TEXT[] NOT NULL DEFAULT '{}',
    provenance                JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE TABLE IF NOT EXISTS public_read_v1.municipalities (
    municipality_id     TEXT,
    ibge_code           TEXT,
    uf                  TEXT,
    name                TEXT,
    as_of               TIMESTAMPTZ,
    source_updated_at   TIMESTAMPTZ,
    completeness        TEXT,
    reason_codes        TEXT[] NOT NULL DEFAULT '{}',
    provenance          JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE TABLE IF NOT EXISTS public_read_v1.surface_health (
    view_name           TEXT PRIMARY KEY,
    enabled             BOOLEAN NOT NULL DEFAULT TRUE,
    refreshed_at        TIMESTAMPTZ,
    query_count         BIGINT NOT NULL DEFAULT 0,
    error_count         BIGINT NOT NULL DEFAULT 0,
    query_p95_ms        NUMERIC,
    last_refresh_status TEXT NOT NULL DEFAULT 'NEVER',
    snapshot_id         TEXT,
    as_of               TIMESTAMPTZ,
    completeness        TEXT,
    provenance          JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE TABLE IF NOT EXISTS public_read_v1.query_budgets (
    query_family             TEXT PRIMARY KEY,
    statement_timeout_ms     INTEGER NOT NULL,
    p95_budget_ms            INTEGER NOT NULL,
    max_rows                 INTEGER NOT NULL,
    max_concurrent           INTEGER NOT NULL,
    representative_query     TEXT NOT NULL
);

INSERT INTO public_read_v1.query_budgets VALUES
    ('tenders_by_process', 2000, 250, 100, 4, 'SELECT * FROM public_read_v1.tenders WHERE process_key = $1 LIMIT 100')
ON CONFLICT (query_family) DO NOTHING;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'smartlic_public_reader') THEN
        CREATE ROLE smartlic_public_reader NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION;
    END IF;
END $$;

REVOKE ALL ON SCHEMA public FROM smartlic_public_reader;
GRANT USAGE ON SCHEMA public_read_v1 TO smartlic_public_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public_read_v1 TO smartlic_public_reader;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA public_read_v1 FROM smartlic_public_reader;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'smartlic_reader_test') THEN
        CREATE ROLE smartlic_reader_test LOGIN PASSWORD 'reader_test_only' IN ROLE smartlic_public_reader NOSUPERUSER NOCREATEDB NOCREATEROLE;
    END IF;
END $$;

ALTER ROLE smartlic_reader_test SET default_transaction_read_only = 'on';
ALTER ROLE smartlic_reader_test SET statement_timeout = '2s';
ALTER ROLE smartlic_reader_test SET lock_timeout = '500ms';
ALTER ROLE smartlic_reader_test SET search_path = public_read_v1, pg_temp;
