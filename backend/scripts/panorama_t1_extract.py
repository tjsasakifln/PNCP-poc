"""Panorama Licitações Brasil 2026 T1 — Data Extraction Script.

Extracts 5 datasets from pncp_raw_bids (window 2026-01-01 to 2026-03-31):
  1. Top sectors by volume (sector inferred via keyword matching on objeto_compra)
  2. UFs with highest growth vs 2025 T1
  3. Modalidade distribution
  4. Value quartiles (P25 / P50 / P75)
  5. Monthly seasonality

Output:
  data/panorama_t1/data.json
  data/panorama_t1/summary.csv

Usage:
    python backend/scripts/panorama_t1_extract.py

Notes
-----
- pncp_raw_bids does NOT store an inferred sector column. We re-classify
  each row client-side via lightweight keyword matching against a small
  fixed dictionary. This is deliberately coarse — the goal is a top-N
  ranking for a public report, not per-row production classification.
- Percentile computation happens in Python (supabase-py does not expose
  PERCENTILE_CONT directly). For large windows this loads the valor column
  into memory — acceptable for the quarterly window (< 100k rows typical).
- Each extract_* function is wrapped in try/except and returns an empty
  list/dict on failure so a single bad query does not abort the run.
"""

from __future__ import annotations

import csv
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Make backend/ importable when invoked directly.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

logger = logging.getLogger("panorama_t1_extract")
logging.basicConfig(level=logging.INFO, format="[panorama-t1] %(message)s")

OUTPUT_DIR = _BACKEND_DIR.parent / "data" / "panorama_t1"

WINDOW_START = "2026-01-01"
WINDOW_END = "2026-04-01"  # exclusive upper bound
WINDOW_PREV_START = "2025-01-01"
WINDOW_PREV_END = "2025-04-01"

# Supabase default row cap per select() is 1000. We page explicitly via range().
_PAGE_SIZE = 1000
_MAX_PAGES = 200  # safety cap: 200k rows

# Coarse keyword-based sector inference (lowercase, stripped matches).
_SECTOR_KEYWORDS: list[tuple[str, list[str]]] = [
    ("Construção / Engenharia", ["obra", "construc", "engenharia", "reforma", "pavimenta", "edifica"]),
    ("Saúde", ["saude", "hospital", "medic", "enfermag", "farmac", "ambulanc", "clinic"]),
    ("TI / Software", ["software", "ti ", "informatica", "sistema ", "licenc", "servidor", "datacenter", "cloud"]),
    ("Limpeza / Conservação", ["limpeza", "conservac", "higienizac", "dedetiza"]),
    ("Segurança / Vigilância", ["seguranc", "vigilanc", "monitoramento"]),
    ("Alimentação", ["alimentac", "refeic", "merenda", "cozinha"]),
    ("Educação", ["educac", "escolar", "ensino", "professor"]),
    ("Transporte / Logística", ["transporte", "logistic", "frete", "veicul"]),
    ("Consultoria", ["consultoria", "assessoria", "auditoria"]),
    ("Material de Escritório", ["escritorio", "papelaria", "impress", "cartucho"]),
]

_MODALIDADE_NAMES = {
    4: "Concorrência",
    5: "Pregão Eletrônico",
    6: "Pregão Presencial",
    7: "Leilão",
    8: "Inexigibilidade",
    12: "Dispensa",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _infer_sector(objeto: str) -> str:
    if not objeto:
        return "Outros"
    lower = objeto.lower()
    for sector, kws in _SECTOR_KEYWORDS:
        for kw in kws:
            if kw in lower:
                return sector
    return "Outros"


def _safe_float(v: Any) -> float:
    if v is None:
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _percentile(values: list[float], pct: float) -> float:
    """Simple linear interpolation percentile (pct in [0,1])."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    k = pct * (len(ordered) - 1)
    lo = int(k)
    hi = min(lo + 1, len(ordered) - 1)
    frac = k - lo
    return ordered[lo] * (1 - frac) + ordered[hi] * frac


def _fetch_all(
    supabase,
    columns: str,
    start: str,
    end: str,
    filters: list[tuple[str, str, Any]] | None = None,
) -> list[dict]:
    """Page through pncp_raw_bids respecting the 1000-row default limit."""
    rows: list[dict] = []
    for page in range(_MAX_PAGES):
        q = (
            supabase.table("pncp_raw_bids")
            .select(columns)
            .gte("data_publicacao", start)
            .lt("data_publicacao", end)
            .eq("is_active", True)
        )
        if filters:
            for col, op, val in filters:
                q = getattr(q, op)(col, val)
        lo = page * _PAGE_SIZE
        hi = lo + _PAGE_SIZE - 1
        q = q.range(lo, hi)
        result = q.execute()
        batch = getattr(result, "data", None) or []
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < _PAGE_SIZE:
            break
    return rows


# ---------------------------------------------------------------------------
# Extractors
# ---------------------------------------------------------------------------


def extract_top_sectors(supabase) -> list[dict]:
    """Top 10 inferred sectors by edital count (with aggregated value)."""
    try:
        rows = _fetch_all(
            supabase,
            "pncp_id,objeto_compra,valor_total_estimado",
            WINDOW_START,
            WINDOW_END,
        )
    except Exception as e:
        logger.warning("extract_top_sectors failed: %s", e)
        return []

    counts: dict[str, int] = defaultdict(int)
    values: dict[str, float] = defaultdict(float)
    for r in rows:
        sector = _infer_sector(r.get("objeto_compra") or "")
        counts[sector] += 1
        values[sector] += _safe_float(r.get("valor_total_estimado"))

    ranked = sorted(
        (
            {"setor": s, "count": c, "valor_total": round(values[s], 2)}
            for s, c in counts.items()
        ),
        key=lambda d: d["count"],
        reverse=True,
    )
    return ranked[:10]


def extract_uf_growth(supabase) -> list[dict]:
    """Top 10 UFs by 2026 T1 count, with YoY delta vs 2025 T1."""
    try:
        current = _fetch_all(supabase, "uf", WINDOW_START, WINDOW_END)
        previous = _fetch_all(supabase, "uf", WINDOW_PREV_START, WINDOW_PREV_END)
    except Exception as e:
        logger.warning("extract_uf_growth failed: %s", e)
        return []

    cur_counts: dict[str, int] = defaultdict(int)
    prev_counts: dict[str, int] = defaultdict(int)
    for r in current:
        uf = (r.get("uf") or "").strip().upper()
        if uf:
            cur_counts[uf] += 1
    for r in previous:
        uf = (r.get("uf") or "").strip().upper()
        if uf:
            prev_counts[uf] += 1

    out = []
    for uf, cur in cur_counts.items():
        prev = prev_counts.get(uf, 0)
        if prev > 0:
            growth_pct = round(((cur - prev) / prev) * 100, 1)
        else:
            growth_pct = None  # no prior baseline
        out.append(
            {
                "uf": uf,
                "count_2026_t1": cur,
                "count_2025_t1": prev,
                "growth_pct": growth_pct,
            }
        )
    out.sort(key=lambda d: d["count_2026_t1"], reverse=True)
    return out[:10]


def extract_modalidades(supabase) -> list[dict]:
    """Edital count + value by modalidade for 2026 T1."""
    try:
        rows = _fetch_all(
            supabase,
            "modalidade_id,valor_total_estimado",
            WINDOW_START,
            WINDOW_END,
        )
    except Exception as e:
        logger.warning("extract_modalidades failed: %s", e)
        return []

    counts: dict[int, int] = defaultdict(int)
    values: dict[int, float] = defaultdict(float)
    for r in rows:
        mid = r.get("modalidade_id")
        if mid is None:
            continue
        try:
            mid = int(mid)
        except (TypeError, ValueError):
            continue
        counts[mid] += 1
        values[mid] += _safe_float(r.get("valor_total_estimado"))

    total = sum(counts.values()) or 1
    out = [
        {
            "modalidade_id": mid,
            "modalidade_nome": _MODALIDADE_NAMES.get(mid, f"Outras ({mid})"),
            "count": c,
            "valor_total": round(values[mid], 2),
            "pct": round((c / total) * 100, 1),
        }
        for mid, c in counts.items()
    ]
    out.sort(key=lambda d: d["count"], reverse=True)
    return out


def extract_value_quartiles(supabase) -> dict[str, float]:
    """P25/P50/P75 + mean of valor_total_estimado for 2026 T1 (positive values only)."""
    try:
        rows = _fetch_all(
            supabase,
            "valor_total_estimado",
            WINDOW_START,
            WINDOW_END,
        )
    except Exception as e:
        logger.warning("extract_value_quartiles failed: %s", e)
        return {}

    values = [
        _safe_float(r.get("valor_total_estimado"))
        for r in rows
        if r.get("valor_total_estimado") is not None
    ]
    values = [v for v in values if v > 0]
    if not values:
        return {"p25": 0.0, "p50": 0.0, "p75": 0.0, "mean": 0.0, "count": 0}
    return {
        "p25": round(_percentile(values, 0.25), 2),
        "p50": round(_percentile(values, 0.50), 2),
        "p75": round(_percentile(values, 0.75), 2),
        "mean": round(sum(values) / len(values), 2),
        "count": len(values),
    }


def extract_seasonality(supabase) -> list[dict]:
    """Edital count + aggregated value per month (2026-01, 2026-02, 2026-03)."""
    try:
        rows = _fetch_all(
            supabase,
            "data_publicacao,valor_total_estimado",
            WINDOW_START,
            WINDOW_END,
        )
    except Exception as e:
        logger.warning("extract_seasonality failed: %s", e)
        return []

    buckets: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0, "valor_total": 0.0})
    for r in rows:
        raw = r.get("data_publicacao")
        if not raw:
            continue
        try:
            # ISO strings from PostgREST — we only need YYYY-MM.
            month = str(raw)[:7]
        except Exception:
            continue
        if not (month.startswith("2026-")):
            continue
        buckets[month]["count"] += 1
        buckets[month]["valor_total"] += _safe_float(r.get("valor_total_estimado"))

    out = [
        {
            "month": m,
            "count": int(b["count"]),
            "valor_total": round(b["valor_total"], 2),
        }
        for m, b in buckets.items()
    ]
    out.sort(key=lambda d: d["month"])
    return out


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run(output_dir: Path | None = None) -> dict:
    """Execute all extractors and persist outputs. Returns the data dict."""
    from supabase_client import get_supabase

    out_dir = output_dir or OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Starting extraction (window: %s to %s)", WINDOW_START, WINDOW_END
    )
    supabase = get_supabase()

    data = {
        "metadata": {
            "window_start": WINDOW_START,
            "window_end": WINDOW_END,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "pncp_raw_bids",
        },
        "top_sectors": extract_top_sectors(supabase),
        "uf_growth": extract_uf_growth(supabase),
        "modalidades": extract_modalidades(supabase),
        "value_quartiles": extract_value_quartiles(supabase),
        "seasonality": extract_seasonality(supabase),
    }

    json_path = out_dir / "data.json"
    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("Wrote %s", json_path)

    csv_path = out_dir / "summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["section", "key", "value"])
        for s in data["top_sectors"]:
            writer.writerow(["top_sectors", s.get("setor", ""), s.get("count", 0)])
        for u in data["uf_growth"]:
            writer.writerow(["uf_growth", u.get("uf", ""), u.get("count_2026_t1", 0)])
        for m in data["modalidades"]:
            writer.writerow(["modalidades", m.get("modalidade_nome", ""), m.get("count", 0)])
        for k, v in (data["value_quartiles"] or {}).items():
            writer.writerow(["value_quartiles", k, v])
        for sz in data["seasonality"]:
            writer.writerow(["seasonality", sz.get("month", ""), sz.get("count", 0)])
    logger.info("Wrote %s", csv_path)

    logger.info(
        "Done. Counts: top_sectors=%d uf_growth=%d modalidades=%d "
        "value_quartiles=%s seasonality=%d",
        len(data["top_sectors"]),
        len(data["uf_growth"]),
        len(data["modalidades"]),
        bool(data["value_quartiles"]),
        len(data["seasonality"]),
    )
    return data


def main() -> None:
    run()


if __name__ == "__main__":
    main()
