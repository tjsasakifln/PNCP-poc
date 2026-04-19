#!/usr/bin/env python3
"""STORY-B2G-001 AC4: generate per-CNPJ personalization brief for outreach.

Produces a markdown brief for a single supplier CNPJ containing:
  - Supplier summary (razao social, recent volume, geography)
  - Top 5 recent contracts
  - 3-5 relevant open bids from pncp_raw_bids filtered by UF and inferred sector

Usage:
    python scripts/b2g_lead_brief.py --cnpj 12345678000199
    python scripts/b2g_lead_brief.py --cnpj 12345678000199 --output /tmp/foo.md
    python scripts/b2g_lead_brief.py --cnpj 12345678000199 --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
load_dotenv()


def fetch_supplier_summary(sb, cnpj: str) -> dict | None:
    ninety_days = (date.today() - timedelta(days=90)).isoformat()
    resp = (
        sb.table("pncp_supplier_contracts")
        .select("ni_fornecedor, nome_fornecedor, uf, municipio, valor_global, data_assinatura, objeto_contrato")
        .eq("ni_fornecedor", cnpj)
        .eq("is_active", True)
        .gte("data_assinatura", ninety_days)
        .order("data_assinatura", desc=True)
        .limit(20)
        .execute()
    )
    rows = resp.data or []
    if not rows:
        return None
    total_vol = sum(float(r.get("valor_global") or 0) for r in rows)
    ufs = sorted({r.get("uf") for r in rows if r.get("uf")})
    return {
        "cnpj": cnpj,
        "razao_social": rows[0].get("nome_fornecedor") or "",
        "participacoes_90d": len(rows),
        "volume_total_90d": total_vol,
        "ufs": ufs,
        "municipios": sorted({r.get("municipio") for r in rows if r.get("municipio")}),
        "top_contratos": rows[:5],
    }


def fetch_open_bids_for_supplier(sb, uf: str, objetos: list[str], limit: int = 5) -> list[dict]:
    """Fetch open bids in the supplier's UF; rank client-side by keyword overlap
    with their recent contract objects."""
    resp = (
        sb.table("pncp_raw_bids")
        .select("pncp_id, objeto_compra, valor_total_estimado, modalidade_nome, orgao_razao_social, uf, data_encerramento, link_pncp")
        .eq("uf", uf)
        .eq("is_active", True)
        .limit(200)
        .execute()
    )
    rows = resp.data or []

    keywords = _extract_keywords(" ".join(objetos).lower(), top_k=10)
    if not keywords:
        return rows[:limit]

    def score(bid: dict) -> int:
        text = (bid.get("objeto_compra") or "").lower()
        return sum(1 for kw in keywords if kw in text)

    rows.sort(key=score, reverse=True)
    return rows[:limit]


def _extract_keywords(text: str, top_k: int) -> list[str]:
    stopwords = {
        "de", "do", "da", "dos", "das", "e", "a", "o", "os", "as",
        "para", "com", "em", "um", "uma", "sobre", "sem", "por",
        "no", "na", "nos", "nas", "que", "ao", "aos", "\u00e0", "\u00e0s",
        "servico", "servicos", "fornecimento", "aquisicao", "contratacao",
    }
    words = [w.strip(",.;:()/") for w in text.split()]
    counts: dict[str, int] = {}
    for w in words:
        if len(w) < 4 or w in stopwords or w.isdigit():
            continue
        counts[w] = counts.get(w, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    return [k for k, _ in ranked[:top_k]]


def render_brief(summary: dict, open_bids: list[dict]) -> str:
    lines: list[str] = []
    vol_fmt = f"R$ {summary['volume_total_90d']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    lines.append(f"# Brief de prospect — {summary['razao_social']}")
    lines.append("")
    lines.append(f"- **CNPJ:** {summary['cnpj']}")
    lines.append(f"- **Participacoes 90d:** {summary['participacoes_90d']}")
    lines.append(f"- **Volume 90d:** {vol_fmt}")
    lines.append(f"- **UFs de atuacao:** {', '.join(summary['ufs']) or 'n/d'}")
    lines.append(f"- **Municipios:** {', '.join(summary['municipios'][:5]) or 'n/d'}")
    lines.append("")
    lines.append("## Contratos recentes")
    lines.append("")
    for c in summary["top_contratos"]:
        valor = float(c.get("valor_global") or 0)
        valor_fmt = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        lines.append(f"- {c.get('data_assinatura', 'n/d')} | {valor_fmt} | {c.get('objeto_contrato', 'n/d')[:160]}")
    lines.append("")
    lines.append("## Editais abertos relevantes")
    lines.append("")
    if not open_bids:
        lines.append("_Nenhum edital aberto encontrado na UF principal. Considere expandir busca._")
    else:
        for b in open_bids:
            valor = float(b.get("valor_total_estimado") or 0)
            valor_fmt = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if valor else "n/d"
            lines.append(f"- **{b.get('objeto_compra', 'n/d')[:140]}**")
            lines.append(
                f"  - Modalidade: {b.get('modalidade_nome', 'n/d')} | "
                f"Valor: {valor_fmt} | Encerra: {b.get('data_encerramento', 'n/d')}"
            )
            lines.append(f"  - Orgao: {b.get('orgao_razao_social', 'n/d')} | {b.get('link_pncp') or ''}")
    lines.append("")
    lines.append("## Hook sugerido")
    lines.append("")
    objeto_principal = summary["top_contratos"][0].get("objeto_contrato", "")[:80] if summary["top_contratos"] else ""
    lines.append(
        f"> Notei que {summary['razao_social']} assinou {summary['participacoes_90d']} contratos nos "
        f"ultimos 90 dias (vol {vol_fmt}), com linha recente em \"{objeto_principal}\". "
        f"Mapeamos {len(open_bids)} edital(is) abertos agora com fit direto. Envio a lista?"
    )
    return "\n".join(lines) + "\n"


def default_output_path(cnpj: str) -> Path:
    return REPO_ROOT / "data" / "outreach" / "briefs" / f"{cnpj}.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate outreach brief for a CNPJ.")
    parser.add_argument("--cnpj", required=True, help="Supplier CNPJ (14 digits, no punctuation)")
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cnpj_clean = "".join(c for c in args.cnpj if c.isdigit())
    if len(cnpj_clean) != 14:
        print(f"ERROR: CNPJ must be 14 digits, got {len(cnpj_clean)}: {args.cnpj}")
        return 2

    if args.dry_run and not os.getenv("SUPABASE_URL"):
        print(f"[dry-run] no SUPABASE_URL set; would fetch brief for {cnpj_clean}")
        return 0

    from supabase_client import get_supabase
    sb = get_supabase()

    summary = fetch_supplier_summary(sb, cnpj_clean)
    if not summary:
        print(f"No contracts found for CNPJ {cnpj_clean} in the last 90 days.")
        return 1

    primary_uf = summary["ufs"][0] if summary["ufs"] else ""
    objetos = [c.get("objeto_contrato", "") for c in summary["top_contratos"]]
    open_bids = fetch_open_bids_for_supplier(sb, primary_uf, objetos) if primary_uf else []

    brief = render_brief(summary, open_bids)
    output = Path(args.output) if args.output else default_output_path(cnpj_clean)

    if args.dry_run:
        print(brief)
        print(f"[dry-run] would write to {output}")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(brief, encoding="utf-8")
    print(f"Wrote brief to {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
