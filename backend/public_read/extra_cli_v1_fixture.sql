-- Extra-cli public_read_v1 producer surface for SmartLic live contract tests.
-- Stub tables are ONLY the public.* relations the views read.
-- VIEW text is copied from extra-cli origin/main
--   db/migrations/089_canonical_snapshot_public_read_v1.sql
--   (reaffirmed in 090_public_read_select_only_lock.sql)
-- SHA: c5f3728b5a50b8b375133db0c66dd946c60ba8a6 (#358)
-- Do NOT create public_read_v1.tenders as a TABLE. Seed via public.canonical_*.

CREATE TABLE IF NOT EXISTS public.truth_plane_kill_switch (
    singleton             BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (singleton),
    enabled               BOOLEAN NOT NULL DEFAULT FALSE,
    reason                TEXT,
    changed_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    changed_by            TEXT NOT NULL DEFAULT 'migration'
);
INSERT INTO public.truth_plane_kill_switch (singleton, enabled, reason, changed_by)
VALUES (TRUE, FALSE, 'initial fail-closed control state', 'migration-087')
ON CONFLICT (singleton) DO NOTHING;

CREATE TABLE IF NOT EXISTS public.canonical_public_entities_v2 (
    entity_id             TEXT PRIMARY KEY,
    entity_type           TEXT NOT NULL CHECK (entity_type IN ('organ', 'unit', 'company', 'supplier', 'process')),
    strong_key            TEXT NOT NULL,
    display_name          TEXT,
    tax_identifier_type   TEXT,
    tax_identifier_export TEXT,
    state                 TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (state IN ('ACTIVE', 'MERGED', 'SPLIT', 'RETIRED')),
    canonical_successor_id TEXT REFERENCES public.canonical_public_entities_v2(entity_id),
    first_seen_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_policy     TEXT NOT NULL,
    CHECK (strong_key !~* 'client[_-]?id'),
    CHECK (canonical_successor_id IS NULL OR canonical_successor_id <> entity_id),
    UNIQUE (entity_type, strong_key)
);

CREATE TABLE IF NOT EXISTS public.canonical_public_events_v1 (
    event_id              TEXT PRIMARY KEY,
    event_type            TEXT NOT NULL CHECK (event_type IN (
        'tender_publication', 'tender_status', 'tender_document_change', 'contract_lifecycle'
    )),
    process_key           TEXT NOT NULL,
    subject_entity_id     TEXT NOT NULL REFERENCES public.canonical_public_entities_v2(entity_id),
    official_number       TEXT,
    state                 TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (state IN ('ACTIVE', 'MERGED', 'SPLIT', 'RETIRED')),
    canonical_successor_id TEXT REFERENCES public.canonical_public_events_v1(event_id),
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_policy     TEXT NOT NULL,
    CHECK (process_key !~* 'client[_-]?id'),
    CHECK (canonical_successor_id IS NULL OR canonical_successor_id <> event_id),
    UNIQUE (event_type, process_key)
);

CREATE TABLE IF NOT EXISTS public.canonical_public_observations (
    observation_id        TEXT PRIMARY KEY,
    source                TEXT NOT NULL,
    source_record_id      TEXT NOT NULL,
    source_version        TEXT NOT NULL,
    document_version      TEXT,
    raw_sha256            TEXT NOT NULL CHECK (raw_sha256 ~ '^[0-9a-f]{64}$'),
    observed_at           TIMESTAMPTZ NOT NULL,
    received_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_uri            TEXT,
    snapshot_id           TEXT,
    payload_hash          TEXT NOT NULL CHECK (payload_hash ~ '^[0-9a-f]{64}$'),
    payload               JSONB NOT NULL,
    CHECK (NOT (payload ? 'client_id')),
    UNIQUE (source, source_record_id, source_version, raw_sha256)
);

CREATE TABLE IF NOT EXISTS public.canonical_event_entity_links (
    event_id              TEXT NOT NULL REFERENCES public.canonical_public_events_v1(event_id),
    entity_id             TEXT NOT NULL REFERENCES public.canonical_public_entities_v2(entity_id),
    relation_type         TEXT NOT NULL CHECK (relation_type IN ('subject_process', 'buyer', 'supplier', 'publisher')),
    observation_id        TEXT NOT NULL REFERENCES public.canonical_public_observations(observation_id),
    confidence            NUMERIC(6,5) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    policy_version        TEXT NOT NULL,
    PRIMARY KEY (event_id, entity_id, relation_type, observation_id)
);

CREATE TABLE IF NOT EXISTS public.canonical_event_revisions (
    revision_id           TEXT PRIMARY KEY,
    event_id              TEXT NOT NULL REFERENCES public.canonical_public_events_v1(event_id),
    valid_from            TIMESTAMPTZ NOT NULL,
    valid_to              TIMESTAMPTZ,
    system_from           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    system_to             TIMESTAMPTZ,
    status_code           TEXT,
    title                 TEXT,
    publication_at        TIMESTAMPTZ,
    document_sha256       TEXT,
    contract_value        NUMERIC(18,2),
    official_number       TEXT,
    fact_hash             TEXT NOT NULL CHECK (fact_hash ~ '^[0-9a-f]{64}$'),
    fact_payload          JSONB NOT NULL,
    created_from_observation_id TEXT NOT NULL REFERENCES public.canonical_public_observations(observation_id),
    policy_version        TEXT NOT NULL,
    CHECK (valid_to IS NULL OR valid_to > valid_from),
    CHECK (system_to IS NULL OR system_to > system_from),
    UNIQUE (event_id, valid_from, fact_hash)
);

CREATE TABLE IF NOT EXISTS public.canonical_public_snapshots (
    snapshot_id              TEXT PRIMARY KEY,
    cutoff_at                TIMESTAMPTZ NOT NULL,
    cutoff_timezone          TEXT NOT NULL DEFAULT 'America/Sao_Paulo'
                                  CHECK (cutoff_timezone = 'America/Sao_Paulo'),
    universe_hash            TEXT NOT NULL CHECK (universe_hash ~ '^[0-9a-f]{64}$'),
    policy_hash              TEXT NOT NULL CHECK (policy_hash ~ '^[0-9a-f]{64}$'),
    schema_hash              TEXT NOT NULL CHECK (schema_hash ~ '^[0-9a-f]{64}$'),
    adapter_hash             TEXT NOT NULL CHECK (adapter_hash ~ '^[0-9a-f]{64}$'),
    data_hash                TEXT NOT NULL CHECK (data_hash ~ '^[0-9a-f]{64}$'),
    document_hash            TEXT NOT NULL CHECK (document_hash ~ '^[0-9a-f]{64}$'),
    dossier_hash             TEXT NOT NULL CHECK (dossier_hash ~ '^[0-9a-f]{64}$'),
    state                    TEXT NOT NULL DEFAULT 'BUILDING'
                                  CHECK (state IN ('BUILDING', 'BLOCKED', 'READY_CANONICAL', 'SUPERSEDED')),
    required_pair_count      INTEGER NOT NULL CHECK (required_pair_count >= 0),
    relevant_dossier_count   INTEGER NOT NULL CHECK (relevant_dossier_count >= 0),
    blockers                 JSONB NOT NULL DEFAULT '[]'::JSONB,
    content_hash             TEXT CHECK (content_hash IS NULL OR content_hash ~ '^[0-9a-f]{64}$'),
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at                TIMESTAMPTZ,
    superseded_at            TIMESTAMPTZ,
    created_by               TEXT NOT NULL,
    CHECK (snapshot_id !~* 'client|profile'),
    CHECK (state <> 'READY_CANONICAL' OR (closed_at IS NOT NULL AND content_hash IS NOT NULL AND blockers = '[]'::JSONB))
);

CREATE TABLE IF NOT EXISTS public.canonical_snapshot_source_watermarks (
    snapshot_id              TEXT NOT NULL REFERENCES public.canonical_public_snapshots(snapshot_id),
    source                   TEXT NOT NULL,
    source_run_id            TEXT NOT NULL,
    watermark_at             TIMESTAMPTZ NOT NULL,
    freshness_state          TEXT NOT NULL CHECK (freshness_state IN ('FRESH', 'STALE', 'FAILED', 'BLOCKED', 'UNKNOWN')),
    completeness_state       TEXT NOT NULL CHECK (completeness_state IN ('COMPLETE', 'INCOMPLETE', 'UNKNOWN')),
    applicable_pair_count    INTEGER NOT NULL CHECK (applicable_pair_count >= 0),
    evaluated_pair_count     INTEGER NOT NULL CHECK (evaluated_pair_count >= 0),
    evidence_hash            TEXT NOT NULL CHECK (evidence_hash ~ '^[0-9a-f]{64}$'),
    recorded_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (snapshot_id, source)
);

CREATE TABLE IF NOT EXISTS public.canonical_snapshot_event_revisions (
    snapshot_id              TEXT NOT NULL REFERENCES public.canonical_public_snapshots(snapshot_id),
    event_id                 TEXT NOT NULL REFERENCES public.canonical_public_events_v1(event_id),
    revision_id              TEXT NOT NULL REFERENCES public.canonical_event_revisions(revision_id),
    fact_hash                TEXT NOT NULL CHECK (fact_hash ~ '^[0-9a-f]{64}$'),
    included_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (snapshot_id, event_id),
    UNIQUE (snapshot_id, revision_id)
);

CREATE TABLE IF NOT EXISTS public.public_read_surface_health_internal (
    view_name                TEXT PRIMARY KEY,
    enabled                  BOOLEAN NOT NULL DEFAULT TRUE,
    refreshed_at             TIMESTAMPTZ,
    query_count              BIGINT NOT NULL DEFAULT 0 CHECK (query_count >= 0),
    error_count              BIGINT NOT NULL DEFAULT 0 CHECK (error_count >= 0),
    query_p95_ms             NUMERIC,
    last_refresh_status      TEXT NOT NULL DEFAULT 'NEVER'
                                  CHECK (last_refresh_status IN ('NEVER', 'VALID', 'FAILED', 'STALE')),
    last_error               TEXT,
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO public.public_read_surface_health_internal (view_name)
VALUES ('snapshots'), ('tenders'), ('contracts'), ('entities'), ('suppliers'), ('organs'), ('municipalities')
ON CONFLICT (view_name) DO NOTHING;

-- ===== VIEW TEXT FROM extra-cli 089 (verbatim) =====
CREATE SCHEMA IF NOT EXISTS public_read_v1;

CREATE OR REPLACE VIEW public_read_v1.current_snapshot AS
SELECT snapshot.snapshot_id, snapshot.cutoff_at AS as_of, snapshot.content_hash,
       snapshot.universe_hash, snapshot.policy_hash, snapshot.schema_hash,
       snapshot.adapter_hash, snapshot.data_hash, snapshot.document_hash,
       snapshot.dossier_hash, snapshot.closed_at,
       CASE
           WHEN EXISTS (
               SELECT 1 FROM public.canonical_snapshot_source_watermarks watermark
               WHERE watermark.snapshot_id = snapshot.snapshot_id
                 AND (watermark.completeness_state <> 'COMPLETE' OR watermark.freshness_state <> 'FRESH')
           ) THEN 'INCOMPLETE'
           WHEN NOT EXISTS (
               SELECT 1 FROM public.canonical_snapshot_source_watermarks watermark
               WHERE watermark.snapshot_id = snapshot.snapshot_id
           ) THEN 'UNKNOWN'
           ELSE 'COMPLETE'
       END AS completeness,
       jsonb_build_object('snapshot_id', snapshot.snapshot_id, 'content_hash', snapshot.content_hash) AS provenance
FROM public.canonical_public_snapshots snapshot
WHERE snapshot.state = 'READY_CANONICAL'
ORDER BY snapshot.cutoff_at DESC, snapshot.snapshot_id DESC
LIMIT 1;

CREATE OR REPLACE VIEW public_read_v1.access_gate AS
SELECT NOT COALESCE((SELECT enabled FROM public.truth_plane_kill_switch WHERE singleton), TRUE) AS enabled;

CREATE OR REPLACE VIEW public_read_v1.tenders AS
SELECT event.event_id, event.process_key, event.event_type, revision.status_code,
       revision.title, revision.publication_at, revision.official_number,
       snapshot.as_of, revision.system_from AS source_updated_at,
       snapshot.completeness,
       CASE WHEN snapshot.completeness = 'COMPLETE' THEN ARRAY[]::TEXT[]
            WHEN snapshot.completeness = 'UNKNOWN' THEN ARRAY['missing_source_watermarks']
            ELSE ARRAY['source_watermark_incomplete'] END AS reason_codes,
       observation.source, observation.source_uri,
       jsonb_build_object('observation_id', observation.observation_id, 'raw_sha256', observation.raw_sha256, 'revision_id', revision.revision_id, 'snapshot_id', snapshot.snapshot_id) AS provenance
FROM public_read_v1.current_snapshot snapshot
JOIN public.canonical_snapshot_event_revisions membership USING (snapshot_id)
JOIN public.canonical_public_events_v1 event USING (event_id)
JOIN public.canonical_event_revisions revision USING (revision_id)
JOIN public.canonical_public_observations observation ON observation.observation_id = revision.created_from_observation_id
CROSS JOIN public_read_v1.access_gate gate
WHERE event.event_type IN ('tender_publication', 'tender_status', 'tender_document_change') AND gate.enabled;

CREATE OR REPLACE VIEW public_read_v1.contracts AS
SELECT event.event_id, event.process_key, revision.status_code, revision.title,
       revision.contract_value, revision.official_number,
       snapshot.as_of, revision.system_from AS source_updated_at,
       snapshot.completeness,
       CASE WHEN snapshot.completeness = 'COMPLETE' THEN ARRAY[]::TEXT[]
            WHEN snapshot.completeness = 'UNKNOWN' THEN ARRAY['missing_source_watermarks']
            ELSE ARRAY['source_watermark_incomplete'] END AS reason_codes,
       observation.source, observation.source_uri,
       jsonb_build_object('observation_id', observation.observation_id, 'raw_sha256', observation.raw_sha256, 'revision_id', revision.revision_id, 'snapshot_id', snapshot.snapshot_id) AS provenance
FROM public_read_v1.current_snapshot snapshot
JOIN public.canonical_snapshot_event_revisions membership USING (snapshot_id)
JOIN public.canonical_public_events_v1 event USING (event_id)
JOIN public.canonical_event_revisions revision USING (revision_id)
JOIN public.canonical_public_observations observation ON observation.observation_id = revision.created_from_observation_id
CROSS JOIN public_read_v1.access_gate gate
WHERE event.event_type = 'contract_lifecycle' AND gate.enabled;

CREATE OR REPLACE VIEW public_read_v1.entities AS
WITH entity_links AS (
    SELECT DISTINCT snapshot.snapshot_id, snapshot.as_of, link.entity_id,
           link.event_id, link.observation_id
    FROM public_read_v1.current_snapshot snapshot
    JOIN public.canonical_snapshot_event_revisions membership USING (snapshot_id)
    JOIN public.canonical_event_entity_links link USING (event_id)
    CROSS JOIN public_read_v1.access_gate gate
    WHERE gate.enabled
), entity_provenance AS (
    SELECT snapshot_id, as_of, entity_id,
           jsonb_agg(
               jsonb_build_object('event_id', event_id, 'observation_id', observation_id)
               ORDER BY event_id, observation_id
           ) AS lineage
    FROM entity_links
    GROUP BY snapshot_id, as_of, entity_id
)
SELECT entity.entity_id, entity.entity_type, entity.display_name,
       entity.tax_identifier_type, entity.tax_identifier_export,
       provenance.as_of, entity.last_seen_at AS source_updated_at,
       snapshot.completeness,
       CASE WHEN snapshot.completeness = 'COMPLETE' THEN ARRAY[]::TEXT[]
            WHEN snapshot.completeness = 'UNKNOWN' THEN ARRAY['missing_source_watermarks']
            ELSE ARRAY['source_watermark_incomplete'] END AS reason_codes,
       jsonb_build_object('snapshot_id', provenance.snapshot_id, 'lineage', provenance.lineage) AS provenance
FROM entity_provenance provenance
JOIN public.canonical_public_entities_v2 entity USING (entity_id)
JOIN public_read_v1.current_snapshot snapshot ON snapshot.snapshot_id = provenance.snapshot_id;

CREATE OR REPLACE VIEW public_read_v1.suppliers AS
SELECT * FROM public_read_v1.entities WHERE entity_type IN ('supplier', 'company');
CREATE OR REPLACE VIEW public_read_v1.organs AS
SELECT * FROM public_read_v1.entities WHERE entity_type IN ('organ', 'unit');

CREATE OR REPLACE VIEW public_read_v1.municipalities AS
SELECT
    NULL::TEXT AS municipality_id,
    NULL::TEXT AS ibge_code,
    NULL::TEXT AS uf,
    NULL::TEXT AS name,
    snapshot.as_of,
    snapshot.as_of AS source_updated_at,
    'UNKNOWN'::TEXT AS completeness,
    ARRAY['municipality_facts_not_snapshot_bound']::TEXT[] AS reason_codes,
    jsonb_build_object('snapshot_id', snapshot.snapshot_id) AS provenance
FROM public_read_v1.current_snapshot snapshot
WHERE FALSE;

CREATE OR REPLACE VIEW public_read_v1.surface_health AS
SELECT health.view_name, health.enabled,
       health.refreshed_at, health.query_count, health.error_count,
       health.query_p95_ms, health.last_refresh_status,
       snapshot.snapshot_id, snapshot.as_of,
       CASE WHEN switch.enabled THEN 'KILL_SWITCH_BLOCKED'
            WHEN health.last_refresh_status = 'VALID' THEN 'COMPLETE'
            ELSE 'INCOMPLETE' END AS completeness,
       jsonb_build_object('snapshot_id', snapshot.snapshot_id, 'content_hash', snapshot.content_hash) AS provenance
FROM public.public_read_surface_health_internal health
LEFT JOIN public_read_v1.current_snapshot snapshot ON TRUE
CROSS JOIN public.truth_plane_kill_switch switch
WHERE switch.singleton;

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
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM smartlic_public_reader;
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
