"""Smoke tests for backend/scripts/panorama_t1_render_pdf.py.

Creates a mock data.json in a tmpdir, renders the PDF, and asserts the
output file exists and is > 10 KB (a minimally-populated reportlab PDF
is typically > 4 KB; 10 KB ensures real content was written).
"""

import importlib
import json
import sys
from pathlib import Path

import pytest


_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


@pytest.fixture
def render_module():
    if "panorama_t1_render_pdf" in sys.modules:
        del sys.modules["panorama_t1_render_pdf"]
    return importlib.import_module("panorama_t1_render_pdf")


def _mock_data() -> dict:
    return {
        "metadata": {
            "window_start": "2026-01-01",
            "window_end": "2026-04-01",
            "generated_at": "2026-04-05T12:00:00+00:00",
            "source": "pncp_raw_bids",
        },
        "top_sectors": [
            {"setor": "Construção / Engenharia", "count": 1234, "valor_total": 3_450_000_000.0},
            {"setor": "Saúde", "count": 980, "valor_total": 2_100_000_000.0},
            {"setor": "TI / Software", "count": 645, "valor_total": 1_250_000_000.0},
        ],
        "uf_growth": [
            {"uf": "SP", "count_2026_t1": 5421, "count_2025_t1": 4900, "growth_pct": 10.6},
            {"uf": "RJ", "count_2026_t1": 2103, "count_2025_t1": 1980, "growth_pct": 6.2},
            {"uf": "MG", "count_2026_t1": 1987, "count_2025_t1": 2100, "growth_pct": -5.4},
        ],
        "modalidades": [
            {"modalidade_id": 5, "modalidade_nome": "Pregão Eletrônico", "count": 8900, "valor_total": 9_200_000_000.0, "pct": 68.3},
            {"modalidade_id": 12, "modalidade_nome": "Dispensa", "count": 2100, "valor_total": 1_100_000_000.0, "pct": 16.1},
            {"modalidade_id": 4, "modalidade_nome": "Concorrência", "count": 1240, "valor_total": 3_400_000_000.0, "pct": 9.5},
        ],
        "value_quartiles": {
            "p25": 15000.0,
            "p50": 78000.0,
            "p75": 320000.0,
            "mean": 540000.0,
            "count": 12345,
        },
        "seasonality": [
            {"month": "2026-01", "count": 4100, "valor_total": 4_200_000_000.0},
            {"month": "2026-02", "count": 4350, "valor_total": 4_600_000_000.0},
            {"month": "2026-03", "count": 4700, "valor_total": 5_100_000_000.0},
        ],
    }


def test_render_produces_valid_pdf(tmp_path, render_module):
    input_path = tmp_path / "data.json"
    output_path = tmp_path / "panorama-2026-t1.pdf"
    input_path.write_text(json.dumps(_mock_data(), ensure_ascii=False), encoding="utf-8")

    result = render_module.render(input_path=input_path, output_path=output_path)

    assert result == output_path
    assert output_path.exists()
    size = output_path.stat().st_size
    assert size > 10_000, f"PDF too small ({size} bytes)"

    # Basic header sanity check — reportlab writes "%PDF-" at byte 0.
    with output_path.open("rb") as f:
        header = f.read(5)
    assert header == b"%PDF-"


def test_render_missing_input_raises(tmp_path, render_module):
    missing = tmp_path / "nope.json"
    output_path = tmp_path / "out.pdf"
    with pytest.raises(FileNotFoundError):
        render_module.render(input_path=missing, output_path=output_path)


def test_render_empty_sections_still_produces_pdf(tmp_path, render_module):
    """An empty-but-valid data.json should still render a PDF with placeholder rows."""
    empty = {
        "metadata": {
            "window_start": "2026-01-01",
            "window_end": "2026-04-01",
            "generated_at": "2026-04-05T12:00:00+00:00",
            "source": "pncp_raw_bids",
        },
        "top_sectors": [],
        "uf_growth": [],
        "modalidades": [],
        "value_quartiles": {"p25": 0, "p50": 0, "p75": 0, "mean": 0, "count": 0},
        "seasonality": [],
    }
    input_path = tmp_path / "data.json"
    output_path = tmp_path / "panorama-empty.pdf"
    input_path.write_text(json.dumps(empty), encoding="utf-8")

    result = render_module.render(input_path=input_path, output_path=output_path)
    assert result.exists()
    assert result.stat().st_size > 5_000
