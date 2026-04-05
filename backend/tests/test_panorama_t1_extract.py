"""Smoke tests for backend/scripts/panorama_t1_extract.py.

These tests inject a fake Supabase client and verify:
  1. Normal extraction produces a well-shaped data.json + summary.csv.
  2. Empty database yields an empty-but-valid structure.
  3. A failing single query does not abort the whole run — the affected
     section is empty and the rest still runs.
"""

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# The script lives in backend/scripts/ which is NOT on sys.path by default.
# We add it once so importlib can resolve it as a top-level module.
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


@pytest.fixture
def extract_module():
    # Fresh import each test to avoid state leakage between runs.
    if "panorama_t1_extract" in sys.modules:
        del sys.modules["panorama_t1_extract"]
    return importlib.import_module("panorama_t1_extract")


# ---------------------------------------------------------------------------
# Fake Supabase — supports the chain used by _fetch_all()
# ---------------------------------------------------------------------------


class _FakeQuery:
    def __init__(self, rows: list[dict], fail: bool = False):
        self._rows = rows
        self._fail = fail
        self._lo = 0
        self._hi = 999

    def select(self, *_a, **_kw):
        return self

    def gte(self, *_a, **_kw):
        return self

    def lt(self, *_a, **_kw):
        return self

    def eq(self, *_a, **_kw):
        return self

    def range(self, lo, hi):
        self._lo = lo
        self._hi = hi
        return self

    def execute(self):
        if self._fail:
            raise RuntimeError("simulated query failure")
        sliced = self._rows[self._lo : self._hi + 1]
        return MagicMock(data=sliced)


class FakeSupabase:
    def __init__(self, rows: list[dict], fail_tables: set[str] | None = None):
        self._rows = rows
        self._fail_tables = fail_tables or set()

    def table(self, name):
        if name in self._fail_tables:
            return _FakeQuery(self._rows, fail=True)
        return _FakeQuery(self._rows)


def _sample_rows() -> list[dict]:
    return [
        {
            "pncp_id": "1",
            "objeto_compra": "Contratação de obra de pavimentação asfáltica",
            "valor_total_estimado": 500000.0,
            "modalidade_id": 5,
            "uf": "SP",
            "data_publicacao": "2026-01-15T10:00:00+00:00",
            "is_active": True,
        },
        {
            "pncp_id": "2",
            "objeto_compra": "Aquisição de software de gestão hospitalar",
            "valor_total_estimado": 120000.0,
            "modalidade_id": 5,
            "uf": "RJ",
            "data_publicacao": "2026-02-10T10:00:00+00:00",
            "is_active": True,
        },
        {
            "pncp_id": "3",
            "objeto_compra": "Serviços de limpeza e conservação predial",
            "valor_total_estimado": 80000.0,
            "modalidade_id": 4,
            "uf": "SP",
            "data_publicacao": "2026-03-05T10:00:00+00:00",
            "is_active": True,
        },
        {
            "pncp_id": "4",
            "objeto_compra": "Prestação de serviços médicos ambulatoriais",
            "valor_total_estimado": 2000000.0,
            "modalidade_id": 5,
            "uf": "MG",
            "data_publicacao": "2026-02-20T10:00:00+00:00",
            "is_active": True,
        },
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_run_extraction_success(tmp_path, extract_module):
    sb = FakeSupabase(_sample_rows())
    with patch("supabase_client.get_supabase", return_value=sb):
        data = extract_module.run(output_dir=tmp_path)

    assert "metadata" in data
    assert data["metadata"]["window_start"] == "2026-01-01"
    assert data["metadata"]["window_end"] == "2026-04-01"
    assert isinstance(data["top_sectors"], list)
    assert len(data["top_sectors"]) >= 1
    assert isinstance(data["uf_growth"], list)
    assert isinstance(data["modalidades"], list)
    assert isinstance(data["value_quartiles"], dict)
    assert isinstance(data["seasonality"], list)

    # Output files exist
    json_path = tmp_path / "data.json"
    csv_path = tmp_path / "summary.csv"
    assert json_path.exists()
    assert csv_path.exists()

    # JSON round-trips
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["metadata"]["source"] == "pncp_raw_bids"

    # Modalidade 5 (Pregão Eletrônico) should be top by count (3 of 4 rows)
    top_mod = data["modalidades"][0]
    assert top_mod["modalidade_id"] == 5
    assert top_mod["count"] == 3

    # Quartiles computed from 4 positive values
    assert data["value_quartiles"]["count"] == 4
    assert data["value_quartiles"]["p50"] > 0


def test_run_extraction_empty_db(tmp_path, extract_module):
    sb = FakeSupabase([])
    with patch("supabase_client.get_supabase", return_value=sb):
        data = extract_module.run(output_dir=tmp_path)

    assert data["top_sectors"] == []
    assert data["uf_growth"] == []
    assert data["modalidades"] == []
    assert data["value_quartiles"] == {"p25": 0.0, "p50": 0.0, "p75": 0.0, "mean": 0.0, "count": 0}
    assert data["seasonality"] == []
    assert (tmp_path / "data.json").exists()
    assert (tmp_path / "summary.csv").exists()


def test_run_extraction_failing_query_is_isolated(tmp_path, extract_module, monkeypatch):
    """One failing extractor should not abort the rest of the run."""
    sb = FakeSupabase(_sample_rows())

    # Force extract_top_sectors to raise by patching _fetch_all to explode
    # only on the first call, then behave normally.
    original_fetch = extract_module._fetch_all
    calls = {"n": 0}

    def flaky_fetch(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("boom")
        return original_fetch(*args, **kwargs)

    monkeypatch.setattr(extract_module, "_fetch_all", flaky_fetch)

    with patch("supabase_client.get_supabase", return_value=sb):
        data = extract_module.run(output_dir=tmp_path)

    # First extractor (top_sectors) swallowed the error -> empty list.
    assert data["top_sectors"] == []
    # Subsequent extractors still produced data.
    assert len(data["modalidades"]) >= 1
    assert (tmp_path / "data.json").exists()
