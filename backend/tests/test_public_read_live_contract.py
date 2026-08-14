"""Exercise the shipped SmartLic adapter against a real extra-cli-shaped Postgres.

Uses the column contract from extra-cli origin/main migrations 089/090.
A missing launcher is a hard failure of this file (no fake adapter fallback).
"""

from __future__ import annotations

import os
import subprocess
import time
import uuid
from pathlib import Path

import pytest

FIXTURE_SQL = Path(__file__).resolve().parents[1] / "public_read" / "extra_cli_v1_fixture.sql"
SCRATCH_LAUNCHER_FAIL = Path(
    os.environ.get(
        "PUBLIC_READ_LAUNCHER_FAIL",
        "/tmp/grok-goal-f106739b82ed/implementer/public-read-launcher-fail.log",
    )
)
CONTAINER = "smartlic-pr2125-public-read"
PORT = os.environ.get("PUBLIC_READ_TEST_PORT", "55432")
ADMIN_DSN = f"postgresql://postgres:test@127.0.0.1:{PORT}/extra_cli_contract"
READER_DSN = f"postgresql://smartlic_reader_test:reader_test_only@127.0.0.1:{PORT}/extra_cli_contract"
PROCESS_KEY = "pncp:420240000001234:1"


def _write_fail(message: str) -> None:
    SCRATCH_LAUNCHER_FAIL.parent.mkdir(parents=True, exist_ok=True)
    SCRATCH_LAUNCHER_FAIL.write_text(message, encoding="utf-8")


def _psql(dsn: str, sql: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["psql", dsn, "-v", "ON_ERROR_STOP=1", "-c", sql],
        check=False,
        capture_output=True,
        text=True,
    )


def _wait_ready(dsn: str, attempts: int = 30) -> bool:
    for _ in range(attempts):
        result = subprocess.run(
            ["pg_isready", "-d", dsn],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            probe = _psql(dsn, "SELECT 1")
            if probe.returncode == 0:
                return True
        time.sleep(1)
    return False


def _start_postgres() -> str:
    existing = os.environ.get("PUBLIC_READ_TEST_DSN")
    if existing:
        if not _wait_ready(existing, attempts=5):
            _write_fail(f"PUBLIC_READ_TEST_DSN not ready: {existing}")
            pytest.fail("PUBLIC_READ_TEST_DSN provided but not reachable")
        return existing

    subprocess.run(["docker", "rm", "-f", CONTAINER], check=False, capture_output=True)
    launched = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--rm",
            "--name",
            CONTAINER,
            "-e",
            "POSTGRES_PASSWORD=test",
            "-e",
            "POSTGRES_USER=postgres",
            "-e",
            "POSTGRES_DB=extra_cli_contract",
            "-p",
            f"{PORT}:5432",
            "postgres:16-alpine",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if launched.returncode != 0:
        _write_fail(launched.stdout + "\n" + launched.stderr)
        pytest.fail("failed to start postgres:16 for public_read_v1 contract proof")
    if not _wait_ready(ADMIN_DSN):
        logs = subprocess.run(
            ["docker", "logs", CONTAINER],
            check=False,
            capture_output=True,
            text=True,
        )
        _write_fail(logs.stdout + "\n" + logs.stderr)
        pytest.fail("postgres started but never became ready")
    return ADMIN_DSN


@pytest.fixture(scope="module")
def live_pg():
    admin = _start_postgres()
    applied = subprocess.run(
        ["psql", admin, "-v", "ON_ERROR_STOP=1", "-f", str(FIXTURE_SQL)],
        check=False,
        capture_output=True,
        text=True,
    )
    if applied.returncode != 0:
        _write_fail(applied.stdout + "\n" + applied.stderr)
        pytest.fail("failed to apply extra-cli public_read_v1 contract fixture")
    grant = _psql(admin, "GRANT CONNECT ON DATABASE extra_cli_contract TO smartlic_reader_test")
    if grant.returncode != 0:
        _write_fail(grant.stdout + "\n" + grant.stderr)
        pytest.fail("failed to grant CONNECT to reader role")
    kind = _psql(
        admin,
        "SELECT table_type FROM information_schema.tables "
        "WHERE table_schema='public_read_v1' AND table_name='tenders'",
    )
    if "VIEW" not in kind.stdout:
        _write_fail(kind.stdout + "\n" + kind.stderr)
        pytest.fail("public_read_v1.tenders must be a VIEW from extra-cli 089, not a table")
    snapshot_id = f"snp-{uuid.uuid4().hex[:12]}"
    as_of = "2026-08-13T12:00:00+00"
    hx = "ab" * 32
    hx2 = "cd" * 32
    hx3 = "ef" * 32
    seed = f"""
    DELETE FROM public.canonical_snapshot_event_revisions;
    DELETE FROM public.canonical_snapshot_source_watermarks;
    DELETE FROM public.canonical_public_snapshots;
    DELETE FROM public.canonical_event_entity_links;
    DELETE FROM public.canonical_event_revisions;
    DELETE FROM public.canonical_public_events_v1;
    DELETE FROM public.canonical_public_observations;
    DELETE FROM public.canonical_public_entities_v2;
    INSERT INTO public.canonical_public_entities_v2
        (entity_id, entity_type, strong_key, display_name, created_by_policy)
    VALUES ('ent-process-1', 'process', '{PROCESS_KEY}', 'Processo uniforme', 'canonical-events-v1');
    INSERT INTO public.canonical_public_observations
        (observation_id, source, source_record_id, source_version, raw_sha256,
         observed_at, source_uri, payload_hash, payload)
    VALUES (
        'obs-1', 'pncp', '{PROCESS_KEY}', 'v1', '{hx2}',
        '{as_of}', 'https://pncp.gov.br/app/editais/{PROCESS_KEY}', '{hx3}',
        '{{"title": "Aquisição de uniformes escolares"}}'::JSONB
    );
    INSERT INTO public.canonical_public_events_v1
        (event_id, event_type, process_key, subject_entity_id, official_number, created_by_policy)
    VALUES ('evt-tender-1', 'tender_publication', '{PROCESS_KEY}', 'ent-process-1', '001/2026', 'canonical-events-v1');
    INSERT INTO public.canonical_event_revisions
        (revision_id, event_id, valid_from, system_from, status_code, title,
         publication_at, official_number, fact_hash, fact_payload,
         created_from_observation_id, policy_version)
    VALUES (
        'rev-1', 'evt-tender-1', '{as_of}', '{as_of}', 'open',
        'Aquisição de uniformes escolares', '{as_of}', '001/2026', '{hx}',
        '{{"status_code":"open","title":"Aquisição de uniformes escolares"}}'::JSONB,
        'obs-1', 'canonical-events-v1'
    );
    INSERT INTO public.canonical_event_entity_links
        (event_id, entity_id, relation_type, observation_id, confidence, policy_version)
    VALUES ('evt-tender-1', 'ent-process-1', 'subject_process', 'obs-1', 1, 'canonical-events-v1');
    INSERT INTO public.canonical_public_snapshots
        (snapshot_id, cutoff_at, universe_hash, policy_hash, schema_hash, adapter_hash,
         data_hash, document_hash, dossier_hash, state, required_pair_count,
         relevant_dossier_count, blockers, content_hash, closed_at, created_by)
    VALUES (
        '{snapshot_id}', '{as_of}', '{hx}', '{hx}', '{hx}', '{hx}',
        '{hx}', '{hx}', '{hx}', 'READY_CANONICAL', 1, 0, '[]'::JSONB,
        '{hx}', '{as_of}', 'contract-fixture'
    );
    INSERT INTO public.canonical_snapshot_source_watermarks
        (snapshot_id, source, source_run_id, watermark_at, freshness_state,
         completeness_state, applicable_pair_count, evaluated_pair_count, evidence_hash)
    VALUES ('{snapshot_id}', 'pncp', 'run-1', '{as_of}', 'FRESH', 'COMPLETE', 1, 1, '{hx}');
    INSERT INTO public.canonical_snapshot_event_revisions
        (snapshot_id, event_id, revision_id, fact_hash)
    VALUES ('{snapshot_id}', 'evt-tender-1', 'rev-1', '{hx}');
    UPDATE public.public_read_surface_health_internal
       SET last_refresh_status = 'VALID', refreshed_at = '{as_of}', last_error = NULL
     WHERE view_name = 'tenders';
    """
    seeded = _psql(admin, seed)
    if seeded.returncode != 0:
        _write_fail(seeded.stdout + "\n" + seeded.stderr)
        pytest.fail("failed to seed READY_CANONICAL membership via public.canonical_*")
    yield {
        "admin": admin,
        "reader": READER_DSN if admin == ADMIN_DSN else os.environ.get("PUBLIC_READ_TEST_READER_DSN", READER_DSN),
        "snapshot_id": snapshot_id,
        "as_of": as_of,
    }
    if not os.environ.get("PUBLIC_READ_TEST_DSN"):
        subprocess.run(["docker", "rm", "-f", CONTAINER], check=False, capture_output=True)


@pytest.fixture
def live_env(live_pg, monkeypatch):
    from public_read.client import clear_last_known_good
    from public_read.isolation import get_backpressure

    monkeypatch.setenv("PUBLIC_READ_V1_MODE", "shadow")
    monkeypatch.setenv("PUBLIC_READ_V1_DSN", live_pg["reader"])
    monkeypatch.setenv("PUBLIC_READ_KILL_SWITCH", "false")
    clear_last_known_good()
    pressure = get_backpressure()
    pressure._in_flight = 0
    pressure._window_count = 0
    yield live_pg
    clear_last_known_good()


def test_producer_surface_is_extra_cli_views(live_env):
    admin = live_env["admin"]
    kind = _psql(
        admin,
        "SELECT table_name, table_type FROM information_schema.tables "
        "WHERE table_schema='public_read_v1' AND table_name IN "
        "('tenders','current_snapshot','contracts') ORDER BY table_name",
    )
    assert kind.returncode == 0
    assert kind.stdout.count("VIEW") >= 3
    via_view = _psql(
        admin,
        f"SELECT process_key, title FROM public_read_v1.tenders WHERE process_key = '{PROCESS_KEY}'",
    )
    assert via_view.returncode == 0
    assert PROCESS_KEY in via_view.stdout
    assert "Aquisição de uniformes escolares" in via_view.stdout


def test_round_trip_tenders_to_page_model(live_env):
    from public_read.adapters import read_family
    from public_read.page_model import family_read_to_page_model
    from public_read.serve import serve_family

    public = read_family("tenders", PROCESS_KEY)
    assert public.served_from == "public_read_v1"
    assert public.entity is not None
    assert public.entity.canonical_id == PROCESS_KEY
    assert public.entity.display_name == "Aquisição de uniformes escolares"
    assert public.entity.as_of is not None
    assert public.entity.source_updated_at is not None
    assert public.entity.completeness == "COMPLETE"
    assert public.entity.freshness == "FRESH"
    assert public.entity.reason_codes == []
    assert public.entity.provenance.get("snapshot_id") == live_env["snapshot_id"]
    page = family_read_to_page_model(public)
    assert page["canonical_id"] == PROCESS_KEY
    assert page["empty"] is False
    assert page["blocked"] is False

    served = serve_family(
        "tenders",
        PROCESS_KEY,
        legacy={
            "canonical_id": PROCESS_KEY,
            "title": "Aquisição de uniformes escolares",
            "row_count": 1,
            "freshness": "FRESH",
            "completeness": "COMPLETE",
            "provenance": {"snapshot_id": live_env["snapshot_id"]},
            "reason_codes": [],
        },
    )
    assert served.served_from == "legacy"
    assert served.divergence == []


def test_reader_cannot_write_or_escape_schema(live_env):
    from public_read.client import fetchall, public_read_connection

    with public_read_connection() as conn:
        with conn.cursor() as cur:
            with pytest.raises(Exception):
                cur.execute(
                    "INSERT INTO public_read_v1.tenders (event_id, process_key, event_type) "
                    "VALUES ('x', 'y', 'tender_publication')"
                )
            with pytest.raises(Exception):
                cur.execute("UPDATE public_read_v1.tenders SET title = 'hack' WHERE process_key = %s", (PROCESS_KEY,))
            with pytest.raises(Exception):
                cur.execute("DELETE FROM public_read_v1.tenders WHERE process_key = %s", (PROCESS_KEY,))
            with pytest.raises(Exception):
                cur.execute("CREATE TABLE public_read_v1.owned (id int)")
            with pytest.raises(Exception):
                cur.execute("SELECT * FROM public.canonical_public_events_v1 LIMIT 1")
            with pytest.raises(Exception):
                cur.execute("INSERT INTO public.canonical_public_events_v1 (event_id) VALUES ('x')")
            with pytest.raises(Exception):
                cur.execute("SELECT * FROM pg_catalog.pg_authid LIMIT 1")

    rows = fetchall(
        "SELECT process_key FROM public_read_v1.tenders WHERE process_key = %s LIMIT 1",
        (PROCESS_KEY,),
    )
    assert rows[0]["process_key"] == PROCESS_KEY


def test_last_known_good_and_kill_switch(live_env, monkeypatch):
    from public_read.adapters import read_family
    from public_read.client import PublicReadUnavailable, public_read_connection

    first = read_family("tenders", PROCESS_KEY)
    assert first.served_from == "public_read_v1"
    monkeypatch.setenv("PUBLIC_READ_KILL_SWITCH", "true")
    with pytest.raises(PublicReadUnavailable) as blocked:
        with public_read_connection():
            pass
    assert blocked.value.reason == "kill_switch"
    cached = read_family("tenders", PROCESS_KEY)
    assert cached.served_from == "last_known_good"
    assert cached.entity.canonical_id == PROCESS_KEY
    assert "kill_switch" in cached.divergence


def test_dsn_not_serialized_in_family_read(live_env):
    from public_read.adapters import read_family

    payload = read_family("tenders", PROCESS_KEY).model_dump()
    dumped = str(payload)
    assert "reader_test_only" not in dumped
    assert "postgresql://" not in dumped


def test_serve_family_current_snapshot_latest(live_env):
    """Hub path: extra-cli 089 VIEW → adapter without bind → serve_family."""
    from public_read.adapters import read_family
    from public_read.page_model import family_read_to_page_model
    from public_read.serve import serve_family

    public = read_family("current_snapshot", "latest")
    assert public.served_from == "public_read_v1"
    assert public.entity is not None
    assert public.entity.canonical_id == live_env["snapshot_id"]
    assert public.entity.as_of is not None
    page = family_read_to_page_model(public)
    assert page["empty"] is False
    assert page["blocked"] is False

    served = serve_family("current_snapshot", "latest")
    assert served.served_from == "legacy"
    assert "public_unavailable" not in served.divergence
    assert "public_only" in served.divergence
