#!/usr/bin/env python3
"""
Download and convert Brazilian municipality coordinates to a static JSON lookup.

Source: https://github.com/kelvins/municipios-brasileiros
CSV columns: codigo_ibge,nome,latitude,longitude,capital,codigo_uf,siafi_id,ddd,fuso_horario

Output: data/municipios_coords.json
  {
    "_meta": {...},
    "by_name":     { "NOME_UPPER/UF": {"lat": ..., "lon": ..., "cod_ibge": ...} },
    "by_cod_ibge": { "1234567":       {"lat": ..., "lon": ..., "nome": ..., "uf": ...} }
  }

Usage:
    python scripts/build-municipios-coords.py
"""
from __future__ import annotations

import csv
import io
import json
import sys
import unicodedata
from datetime import date
from pathlib import Path

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)

CSV_URL = "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv"

# UF code → abbreviation mapping (codigo_uf from IBGE)
_UF_MAP: dict[str, str] = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA",
    "16": "AP", "17": "TO", "21": "MA", "22": "PI", "23": "CE",
    "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE",
    "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT",
    "52": "GO", "53": "DF",
}


def _strip_accents(s: str) -> str:
    """Remove diacritical marks. E.g. 'São Paulo' → 'Sao Paulo'."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _normalize_name(nome: str) -> str:
    """Normalize to uppercase ASCII for use as by_name key."""
    return _strip_accents(nome).upper().strip()


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    out_path = project_root / "data" / "municipios_coords.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading CSV from:\n  {CSV_URL}")
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        response = client.get(CSV_URL)
        response.raise_for_status()

    raw_text = response.text
    print(f"  Downloaded {len(raw_text):,} bytes")

    reader = csv.DictReader(io.StringIO(raw_text))
    by_name: dict[str, dict] = {}
    by_cod_ibge: dict[str, dict] = {}
    skipped = 0

    for row in reader:
        cod_ibge = row.get("codigo_ibge", "").strip()
        nome = row.get("nome", "").strip()
        lat_str = row.get("latitude", "").strip()
        lon_str = row.get("longitude", "").strip()
        cod_uf = row.get("codigo_uf", "").strip()

        if not (cod_ibge and nome and lat_str and lon_str and cod_uf):
            skipped += 1
            continue

        uf = _UF_MAP.get(cod_uf)
        if not uf:
            skipped += 1
            continue

        try:
            lat = float(lat_str)
            lon = float(lon_str)
        except ValueError:
            skipped += 1
            continue

        norm_name = _normalize_name(nome)
        key = f"{norm_name}/{uf}"

        by_name[key] = {"lat": lat, "lon": lon, "cod_ibge": int(cod_ibge)}
        by_cod_ibge[cod_ibge] = {"lat": lat, "lon": lon, "nome": nome, "uf": uf}

    total = len(by_cod_ibge)
    print(f"  Parsed {total} municipalities ({skipped} skipped)")

    out = {
        "_meta": {
            "source": "IBGE/kelvins/municipios-brasileiros",
            "url": CSV_URL,
            "count": total,
            "updated": str(date.today()),
        },
        "by_name": by_name,
        "by_cod_ibge": by_cod_ibge,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = out_path.stat().st_size / 1024
    print(f"  Written to: {out_path}")
    print(f"  File size: {size_kb:.1f} KB")

    # Quick validation
    with open(out_path, "r", encoding="utf-8") as f:
        parsed = json.load(f)
    assert len(parsed["by_name"]) == total, "by_name count mismatch"
    assert len(parsed["by_cod_ibge"]) == total, "by_cod_ibge count mismatch"
    print(f"  Validation OK — {total} entries in both indexes")

    # Sample check
    sp_key = "SAO PAULO/SP"
    if sp_key in parsed["by_name"]:
        sp = parsed["by_name"][sp_key]
        print(f"  Sample — {sp_key}: lat={sp['lat']}, lon={sp['lon']}")
    else:
        # Try without accents stripped differently
        candidates = [k for k in parsed["by_name"] if "SAO PAULO" in k and "/SP" in k]
        print(f"  Sample — SP candidates: {candidates[:3]}")


if __name__ == "__main__":
    main()
