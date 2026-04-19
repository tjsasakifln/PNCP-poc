#!/usr/bin/env python3
"""STORY-B2G-001 AC1: generate qualified B2G outreach lead list.

Queries pncp_supplier_contracts for suppliers with signal of active B2G
engagement in the last 90 days and exports a timestamped CSV with heuristic
email inference + sector fit flags.

Usage:
    python scripts/b2g_outreach_query.py                     # default: top 50, current ISO week
    python scripts/b2g_outreach_query.py --limit 30          # override result cap
    python scripts/b2g_outreach_query.py --min-contracts 5   # raise qualification floor
    python scripts/b2g_outreach_query.py --output /tmp/x.csv # custom path
    python scripts/b2g_outreach_query.py --dry-run           # print preview, do not write

Output CSV columns:
    cnpj, razao_social, participacoes_90d, volume_total_90d,
    top_3_objetos, email_provavel, email_source, cidade_uf

Output path default:
    data/outreach/leads-2026-W{WW}.csv  (ISO week from --week or today)

Known limitation (2026-04):
    profiles table has no cnpj column, so we cannot LEFT JOIN to exclude
    already-registered SmartLic users. Founder must cross-check manually
    before first outreach. A future story will add profiles.cnpj.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
load_dotenv()


EMAIL_GUESSES = ("contato", "comercial", "diretoria", "financeiro")
CORP_STOPWORDS = {
    "ltda", "me", "eireli", "s/a", "sa", "s.a", "sociedade", "limitada",
    "empresa", "empresas", "industria", "industrial", "comercio", "comercial",
    "construtora", "construcoes", "construcao", "engenharia", "servicos",
    "servico", "consultoria", "transportes", "transporte", "distribuidora",
    "industrias", "holding", "grupo", "cia", "e",
}


def _strip_diacritics(text: str) -> str:
    """Remove Latin diacritics (c-cedilha, accents) returning plain ASCII."""
    import unicodedata
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def slugify_company(name: str) -> str:
    """Best-effort slug used as the email's local-part prefix.

    Returns the first *distinctive* word (longer than 2 chars, not a corporate
    stopword like "Construtora" or "LTDA"). Falls back to empty string when no
    such word exists.
    """
    plain = _strip_diacritics(name or "").lower()
    ascii_only = re.sub(r"[^a-z0-9 ]", "", plain)
    words = [w for w in ascii_only.split() if w and len(w) >= 3 and w not in CORP_STOPWORDS]
    if not words:
        return ""
    return words[0][:20]


def guess_email(razao_social: str | None) -> tuple[str, str]:
    """Returns (email_heuristic, source_label).

    source_label is one of:
        - "HEURISTIC_DOMAIN": fabricated domain from slug (LOW confidence)
        - "UNKNOWN": could not infer at all
    """
    if not razao_social:
        return "", "UNKNOWN"
    slug = slugify_company(razao_social)
    if not slug:
        return "", "UNKNOWN"
    return f"{EMAIL_GUESSES[0]}@{slug}.com.br", "HEURISTIC_DOMAIN"


def load_opt_outs(opt_out_path: Path) -> set[str]:
    if not opt_out_path.exists():
        return set()
    out = set()
    for line in opt_out_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            out.add(stripped)
    return out


def fetch_qualified_suppliers(
    supabase_client,
    *,
    min_contracts: int,
    min_volume_brl: float,
    limit: int,
):
    """Run the qualified-suppliers aggregation against pncp_supplier_contracts.

    Uses an RPC if available; falls back to client-side aggregation over a
    bounded window so the script works on today's schema without adding a
    migration.
    """
    response = (
        supabase_client.table("pncp_supplier_contracts")
        .select("ni_fornecedor, nome_fornecedor, uf, municipio, valor_global, objeto_contrato, data_assinatura")
        .gte("data_assinatura", _ninety_days_ago_iso())
        .gt("valor_global", 0)
        .eq("is_active", True)
        .limit(10000)
        .execute()
    )
    rows = response.data or []

    by_cnpj: dict[str, dict] = {}
    for row in rows:
        cnpj = (row.get("ni_fornecedor") or "").strip()
        if not cnpj:
            continue
        bucket = by_cnpj.setdefault(
            cnpj,
            {
                "cnpj": cnpj,
                "razao_social": row.get("nome_fornecedor") or "",
                "uf": row.get("uf") or "",
                "municipio": row.get("municipio") or "",
                "participacoes_90d": 0,
                "volume_total_90d": 0.0,
                "objetos": [],
            },
        )
        bucket["participacoes_90d"] += 1
        try:
            bucket["volume_total_90d"] += float(row.get("valor_global") or 0)
        except (TypeError, ValueError):
            pass
        objeto = (row.get("objeto_contrato") or "").strip()
        if objeto and len(bucket["objetos"]) < 3:
            bucket["objetos"].append(objeto[:140])
        if not bucket["razao_social"] and row.get("nome_fornecedor"):
            bucket["razao_social"] = row["nome_fornecedor"]

    qualified = [
        b for b in by_cnpj.values()
        if b["participacoes_90d"] >= min_contracts and b["volume_total_90d"] >= min_volume_brl
    ]
    qualified.sort(key=lambda b: b["volume_total_90d"], reverse=True)
    return qualified[:limit]


def _ninety_days_ago_iso() -> str:
    from datetime import timedelta
    return (date.today() - timedelta(days=90)).isoformat()


def build_rows(suppliers: list[dict], opt_outs: set[str]) -> list[dict]:
    out = []
    for s in suppliers:
        if s["cnpj"] in opt_outs:
            continue
        email, source = guess_email(s["razao_social"])
        out.append(
            {
                "cnpj": s["cnpj"],
                "razao_social": s["razao_social"],
                "participacoes_90d": s["participacoes_90d"],
                "volume_total_90d": f"{s['volume_total_90d']:.2f}",
                "top_3_objetos": " | ".join(s["objetos"]),
                "email_provavel": email,
                "email_source": source,
                "cidade_uf": f"{s['municipio']}/{s['uf']}".strip("/"),
            }
        )
    return out


def default_output_path(week: str | None) -> Path:
    if week:
        tag = week
    else:
        iso = date.today().isocalendar()
        tag = f"{iso.year}-W{iso.week:02d}"
    return REPO_ROOT / "data" / "outreach" / f"leads-{tag}.csv"


def write_csv(rows: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "cnpj", "razao_social", "participacoes_90d", "volume_total_90d",
        "top_3_objetos", "email_provavel", "email_source", "cidade_uf",
    ]
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate B2G outreach lead list.")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--min-contracts", type=int, default=3)
    parser.add_argument("--min-volume", type=float, default=100_000.0)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--week", type=str, default=None, help="ISO week tag for filename (e.g., 2026-W17)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    output = Path(args.output) if args.output else default_output_path(args.week)
    opt_outs = load_opt_outs(REPO_ROOT / "data" / "outreach" / "opt-outs.txt")

    if args.dry_run and not os.getenv("SUPABASE_URL"):
        print("[dry-run] no SUPABASE_URL set; emitting empty preview")
        rows = []
    else:
        from supabase_client import get_supabase
        sb = get_supabase()
        suppliers = fetch_qualified_suppliers(
            sb,
            min_contracts=args.min_contracts,
            min_volume_brl=args.min_volume,
            limit=args.limit,
        )
        rows = build_rows(suppliers, opt_outs)

    print(f"qualified_leads={len(rows)} opt_outs_filtered={len(opt_outs)}")

    if args.dry_run:
        for r in rows[:5]:
            print(r)
        print(f"[dry-run] would write to {output}")
        return 0

    write_csv(rows, output)
    print(f"Wrote {len(rows)} leads to {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
