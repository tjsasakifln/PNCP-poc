#!/usr/bin/env python3
"""
Pré-popula o cache de geocode (data/geocode_cache.json) a partir de
relatórios existentes e/ou da lista de municípios do IBGE.

Uso:
    # Extrair cidades de relatórios existentes e geocodar
    python scripts/seed-geocode-cache.py --from-reports

    # Geocodar municípios de UFs específicas via IBGE + Nominatim
    python scripts/seed-geocode-cache.py --ufs SC,SP,PR,RS,MG,GO,BA,ES,RJ,PE

    # Ambos
    python scripts/seed-geocode-cache.py --from-reports --ufs SC,SP

Respeita o rate limit do Nominatim (1 req/s). Resumível — pula cidades já em cache.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = str(PROJECT_ROOT / "data" / "geocode_cache.json")
NOMINATIM_BASE = "https://nominatim.openstreetmap.org/search"
IBGE_BASE = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
USER_AGENT = "SmartLic-GeocodeSeed/1.0 (report@smartlic.tech)"


def load_cache() -> dict:
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_cache(cache: dict) -> None:
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    tmp = CACHE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)
    os.replace(tmp, CACHE_FILE)


def geocode_nominatim(client: httpx.Client, cidade: str, uf: str) -> list[float] | None:
    """Returns [lat, lon] or None."""
    try:
        resp = client.get(
            NOMINATIM_BASE,
            params={"q": f"{cidade}, {uf}, Brasil", "format": "json", "limit": 1, "countrycodes": "br"},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data and len(data) > 0:
                return [float(data[0]["lat"]), float(data[0]["lon"])]
    except Exception as e:
        print(f"    ✗ {cidade}/{uf}: {e}")
    return None


def collect_cities_from_reports() -> set[tuple[str, str]]:
    """Extract unique (cidade, UF) pairs from existing report JSON files."""
    cities: set[tuple[str, str]] = set()
    reports_dir = PROJECT_ROOT / "docs" / "reports"
    if not reports_dir.exists():
        return cities

    for f in reports_dir.glob("data-*.json"):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)

            # From editais
            for ed in data.get("editais", []):
                mun = ed.get("municipio", "")
                uf = ed.get("uf", "")
                if mun and uf:
                    cities.add((mun, uf))

            # From empresa sede
            emp = data.get("empresa", {})
            cidade = emp.get("cidade_sede", "")
            uf = emp.get("uf_sede", "")
            if cidade and uf:
                cities.add((cidade, uf))

        except (json.JSONDecodeError, OSError):
            continue

    return cities


def collect_cities_from_ibge(client: httpx.Client, ufs: list[str]) -> set[tuple[str, str]]:
    """Fetch municipality names from IBGE for given UFs."""
    cities: set[tuple[str, str]] = set()
    for uf in ufs:
        try:
            resp = client.get(f"{IBGE_BASE}/{uf}/municipios", timeout=30)
            if resp.status_code == 200:
                for mun in resp.json():
                    nome = mun.get("nome", "")
                    if nome:
                        cities.add((nome, uf.upper()))
                print(f"  IBGE {uf}: {len([m for m in resp.json()])} municípios")
        except Exception as e:
            print(f"  IBGE {uf}: erro — {e}")
    return cities


def main():
    parser = argparse.ArgumentParser(description="Seed geocode cache")
    parser.add_argument("--from-reports", action="store_true", help="Extract cities from existing report JSONs")
    parser.add_argument("--ufs", type=str, default="", help="Comma-separated UFs to fetch from IBGE (e.g. SC,SP,PR)")
    args = parser.parse_args()

    if not args.from_reports and not args.ufs:
        print("Uso: --from-reports e/ou --ufs SC,SP,PR,...")
        sys.exit(1)

    cache = load_cache()
    print(f"Cache atual: {len(cache)} cidades geocodadas")

    cities: set[tuple[str, str]] = set()

    if args.from_reports:
        report_cities = collect_cities_from_reports()
        print(f"Cidades de relatórios: {len(report_cities)}")
        cities.update(report_cities)

    client = httpx.Client()

    if args.ufs:
        uf_list = [u.strip().upper() for u in args.ufs.split(",") if u.strip()]
        ibge_cities = collect_cities_from_ibge(client, uf_list)
        print(f"Cidades do IBGE: {len(ibge_cities)}")
        cities.update(ibge_cities)

    # Filter out already cached
    to_geocode = []
    for cidade, uf in sorted(cities):
        key = f"{cidade.strip().lower()}|{uf.strip().upper()}"
        if key not in cache:
            to_geocode.append((cidade, uf))

    print(f"\nTotal: {len(cities)} cidades, {len(cities) - len(to_geocode)} já em cache, {len(to_geocode)} a geocodar")

    if not to_geocode:
        print("Nada a fazer — cache já completo!")
        return

    eta_min = len(to_geocode) * 1.1 / 60
    print(f"ETA: ~{eta_min:.0f} min (Nominatim 1 req/s)\n")

    success = 0
    failed = 0
    for i, (cidade, uf) in enumerate(to_geocode):
        key = f"{cidade.strip().lower()}|{uf.strip().upper()}"
        coords = geocode_nominatim(client, cidade, uf)
        cache[key] = coords
        if coords:
            success += 1
        else:
            failed += 1

        # Progress every 50
        if (i + 1) % 50 == 0 or i == len(to_geocode) - 1:
            print(f"  [{i+1}/{len(to_geocode)}] ✓{success} ✗{failed}")
            save_cache(cache)  # Checkpoint

        time.sleep(1.1)

    save_cache(cache)
    print(f"\nDone: {success} OK, {failed} falhas. Cache total: {len(cache)} cidades")
    client.close()


if __name__ == "__main__":
    main()
