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
    snapshot_id = f"snp-{uuid.uuid4().hex[:12]}"
    as_of = "2026-08-13T12:00:00+00"
    seed = f"""
    TRUNCATE public_read_v1.tenders, public_read_v1.contracts, public_read_v1.entities,
             public_read_v1.suppliers, public_read_v1.organs, public_read_v1.municipalities,
             public_read_v1.current_snapshot, public_read_v1.surface_health;
    INSERT INTO public_read_v1.current_snapshot
        (snapshot_id, as_of, content_hash, completeness, provenance, closed_at)
    VALUES ('{snapshot_id}', '{as_of}', repeat('ab', 32), 'COMPLETE',
            jsonb_build_object('snapshot_id', '{snapshot_id}'), '{as_of}');
    INSERT INTO public_read_v1.tenders
        (event_id, process_key, event_type, status_code, title, publication_at,
         official_number, as_of, source_updated_at, completeness, reason_codes,
         source, source_uri, provenance)
    VALUES (
        'evt-tender-1', '{PROCESS_KEY}', 'tender_publication', 'open',
        'Aquisição de uniformes escolares', '{as_of}', '001/2026',
        '{as_of}', '{as_of}', 'COMPLETE', ARRAY[]::TEXT[],
        'pncp', 'https://pncp.gov.br/app/editais/{PROCESS_KEY}',
        jsonb_build_object('snapshot_id', '{snapshot_id}', 'observation_id', 'obs-1',
                           'raw_sha256', repeat('cd', 32), 'revision_id', 'rev-1')
    );
    INSERT INTO public_read_v1.surface_health
        (view_name, enabled, refreshed_at, last_refresh_status, snapshot_id, as_of, completeness, provenance)
    VALUES ('tenders', TRUE, '{as_of}', 'VALID', '{snapshot_id}', '{as_of}', 'COMPLETE',
            jsonb_build_object('snapshot_id', '{snapshot_id}'));
    """
    seeded = _psql(admin, seed)
    if seeded.returncode != 0:
        _write_fail(seeded.stdout + "\n" + seeded.stderr)
        pytest.fail("failed to seed canonical tender fixture")
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
    from public_read.isolation import Backpressure, get_backpressure

    monkeypatch.setenv("PUBLIC_READ_V1_MODE", "shadow")
    monkeypatch.setenv("PUBLIC_READ_V1_DSN", live_pg["reader"])
    monkeypatch.setenv("PUBLIC_READ_KILL_SWITCH", "false")
    clear_last_known_good()
    pressure = get_backpressure()
    pressure._in_flight = 0
    pressure._window_count = 0
    yield live_pg
    clear_last_known_good()


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
                    "INSERT INTO public_read_v1.tenders (event_id, process_key, event_type, as_of, completeness) "
                    "VALUES ('x', 'y', 'tender_publication', NOW(), 'COMPLETE')"
                )
            with pytest.raises(Exception):
                cur.execute("UPDATE public_read_v1.tenders SET title = 'hack' WHERE process_key = %s", (PROCESS_KEY,))
            with pytest.raises(Exception):
                cur.execute("DELETE FROM public_read_v1.tenders WHERE process_key = %s", (PROCESS_KEY,))
            with pytest.raises(Exception):
                cur.execute("CREATE TABLE public_read_v1.owned (id int)")
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
