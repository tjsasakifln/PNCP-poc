"""STORY-B2G-001 — unit tests for the pure-python helpers in b2g_outreach_query."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "b2g_outreach_query.py"


@pytest.fixture(scope="module")
def module():
    spec = importlib.util.spec_from_file_location("b2g_outreach_query", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["b2g_outreach_query"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_slugify_drops_stopwords(module):
    assert module.slugify_company("Construtora Alfa LTDA") == "alfa"


def test_slugify_accented_preserves_ascii(module):
    # c-cedilha becomes "c" after lowercasing + stripping non-ascii
    assert module.slugify_company("Construção Beta S/A") == "beta"


def test_slugify_only_stopwords_returns_empty(module):
    assert module.slugify_company("LTDA ME EIRELI") == ""


def test_guess_email_unknown_for_empty_name(module):
    email, source = module.guess_email("")
    assert email == ""
    assert source == "UNKNOWN"


def test_guess_email_builds_heuristic(module):
    email, source = module.guess_email("Gamma Engenharia LTDA")
    assert email.endswith("@gamma.com.br")
    assert email.startswith("contato@")
    assert source == "HEURISTIC_DOMAIN"


def test_load_opt_outs_missing_file(module, tmp_path):
    missing = tmp_path / "does-not-exist.txt"
    assert module.load_opt_outs(missing) == set()


def test_load_opt_outs_reads_lines_and_skips_comments(module, tmp_path):
    p = tmp_path / "opt-outs.txt"
    p.write_text("12345678000199\n# comment\n  \n99887766000155\n", encoding="utf-8")
    assert module.load_opt_outs(p) == {"12345678000199", "99887766000155"}


def test_build_rows_filters_opt_outs(module):
    suppliers = [
        {
            "cnpj": "11111111000111",
            "razao_social": "Alfa LTDA",
            "uf": "SP",
            "municipio": "São Paulo",
            "participacoes_90d": 5,
            "volume_total_90d": 250000.0,
            "objetos": ["Servicos de engenharia"],
        },
        {
            "cnpj": "22222222000122",
            "razao_social": "Beta LTDA",
            "uf": "RJ",
            "municipio": "Rio",
            "participacoes_90d": 4,
            "volume_total_90d": 180000.0,
            "objetos": [],
        },
    ]
    rows = module.build_rows(suppliers, opt_outs={"11111111000111"})
    assert len(rows) == 1
    assert rows[0]["cnpj"] == "22222222000122"
    assert rows[0]["email_source"] == "HEURISTIC_DOMAIN"
    assert rows[0]["volume_total_90d"] == "180000.00"


def test_default_output_path_uses_explicit_week(module):
    p = module.default_output_path("2026-W17")
    assert p.name == "leads-2026-W17.csv"
    assert p.parent.name == "outreach"


def test_default_output_path_falls_back_to_today(module):
    p = module.default_output_path(None)
    assert p.name.startswith("leads-")
    assert p.suffix == ".csv"


def test_write_csv_roundtrip(module, tmp_path):
    out = tmp_path / "leads.csv"
    rows = [
        {
            "cnpj": "33333333000133",
            "razao_social": "Gamma",
            "participacoes_90d": 7,
            "volume_total_90d": "500000.00",
            "top_3_objetos": "obj1 | obj2",
            "email_provavel": "contato@gamma.com.br",
            "email_source": "HEURISTIC_DOMAIN",
            "cidade_uf": "Curitiba/PR",
        }
    ]
    module.write_csv(rows, out)
    content = out.read_text(encoding="utf-8")
    assert "33333333000133" in content
    assert "HEURISTIC_DOMAIN" in content
