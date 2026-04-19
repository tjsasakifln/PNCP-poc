"""STORY-B2G-001 — unit tests for b2g_weekly_report pure helpers."""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "b2g_weekly_report.py"


@pytest.fixture(scope="module")
def module():
    spec = importlib.util.spec_from_file_location("b2g_weekly_report", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["b2g_weekly_report"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_current_week_tag_shape(module):
    tag = module.current_week_tag()
    assert tag.count("-W") == 1
    year, week = tag.split("-W")
    assert year.isdigit() and len(year) == 4
    assert week.isdigit() and 1 <= int(week) <= 53


def test_read_csv_if_exists_returns_empty_when_missing(module, tmp_path):
    assert module.read_csv_if_exists(tmp_path / "nope.csv") == []


def test_read_csv_if_exists_parses_rows(module, tmp_path):
    p = tmp_path / "x.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["a", "b"])
        writer.writeheader()
        writer.writerow({"a": "1", "b": "2"})
    rows = module.read_csv_if_exists(p)
    assert rows == [{"a": "1", "b": "2"}]


def test_summarize_leads_aggregates_volumes_and_ufs(module):
    leads = [
        {"volume_total_90d": "100000.00", "cidade_uf": "São Paulo/SP"},
        {"volume_total_90d": "200000.00", "cidade_uf": "Rio/RJ"},
        {"volume_total_90d": "50000.00", "cidade_uf": "Santos/SP"},
        {"volume_total_90d": "not-a-number", "cidade_uf": ""},
    ]
    summary = module.summarize_leads(leads)
    assert summary["count"] == 4
    assert summary["volume_total"] == 350000.0
    assert summary["top_ufs"][0] == ("SP", 2)


def test_summarize_crm_computes_rates(module):
    crm = [
        {"canal": "email", "status": "Contactado"},
        {"canal": "email", "status": "Respondeu"},
        {"canal": "linkedin", "status": "Trial"},
        {"canal": "linkedin", "status": "Fechado"},
        {"canal": "email", "status": "Churn"},
    ]
    summary = module.summarize_crm(crm)
    assert summary["total_contacts"] == 5
    assert summary["contacts_by_channel"]["email"] == 3
    assert summary["pipeline"]["Trial"] == 1
    assert summary["pipeline"]["Fechado"] == 1
    # 3 responded (Respondeu+Trial+Fechado) out of 5
    assert summary["response_rate"] == pytest.approx(3 / 5)
    # 2 trials (Trial+Fechado) out of 3 responders
    assert summary["trial_start_rate"] == pytest.approx(2 / 3)


def test_render_report_includes_key_sections(module, tmp_path):
    leads_summary = {"count": 12, "volume_total": 500000.0, "top_ufs": [("SP", 8), ("RJ", 4)]}
    crm_summary = {
        "pipeline": {s: 0 for s in module.STAGES},
        "contacts_by_channel": {},
        "total_contacts": 0,
        "response_rate": 0.0,
        "trial_start_rate": 0.0,
    }
    report = module.render_report("2026-W17", leads_summary, crm_summary, tmp_path / "x.csv")
    assert "Relatorio Semanal 2026-W17" in report
    assert "Pipeline atual" in report
    assert "Meta semanal: 15 contatos" in report
