#!/usr/bin/env python3
"""STORY-B2G-001 AC7: generate weekly B2G outreach report.

Aggregates the per-week lead CSV + a simple CRM CSV (if present) into a
markdown report stored in docs/sales/reports/. Safe to run without
network access — reads local files only.

Usage:
    python scripts/b2g_weekly_report.py
    python scripts/b2g_weekly_report.py --week 2026-W17
    python scripts/b2g_weekly_report.py --crm data/outreach/crm.csv

CRM CSV expected shape (optional, for manual tracking before Airtable/Notion):
    cnpj, canal, data_contato, status, trial_start_ts, deal_size_estimado
    where status in {Prospectado,Contactado,Respondeu,Trial,Proposta,Fechado,Churn}
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


STAGES = [
    "Prospectado", "Contactado", "Respondeu", "Trial",
    "Proposta", "Fechado", "Churn",
]


def current_week_tag() -> str:
    iso = date.today().isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def read_csv_if_exists(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def summarize_leads(leads: list[dict]) -> dict:
    vol_sum = 0.0
    ufs: dict[str, int] = {}
    for lead in leads:
        try:
            vol_sum += float(lead.get("volume_total_90d") or 0)
        except ValueError:
            pass
        cidade_uf = lead.get("cidade_uf") or ""
        if "/" in cidade_uf:
            uf = cidade_uf.rsplit("/", 1)[-1].strip()
            ufs[uf] = ufs.get(uf, 0) + 1
    return {
        "count": len(leads),
        "volume_total": vol_sum,
        "top_ufs": sorted(ufs.items(), key=lambda kv: kv[1], reverse=True)[:5],
    }


def summarize_crm(crm_rows: list[dict]) -> dict:
    pipeline: dict[str, int] = {s: 0 for s in STAGES}
    contacts_this_week: dict[str, int] = {}
    responded = 0
    trials = 0
    for row in crm_rows:
        status = (row.get("status") or "").strip()
        if status in pipeline:
            pipeline[status] += 1
        canal = (row.get("canal") or "").strip() or "unknown"
        contacts_this_week[canal] = contacts_this_week.get(canal, 0) + 1
        if status in {"Respondeu", "Trial", "Proposta", "Fechado"}:
            responded += 1
        if status in {"Trial", "Proposta", "Fechado"}:
            trials += 1
    total_contacts = sum(contacts_this_week.values())
    return {
        "pipeline": pipeline,
        "contacts_by_channel": contacts_this_week,
        "total_contacts": total_contacts,
        "response_rate": (responded / total_contacts) if total_contacts else 0.0,
        "trial_start_rate": (trials / responded) if responded else 0.0,
    }


def render_report(week: str, leads_summary: dict, crm_summary: dict, week_path: Path) -> str:
    lines: list[str] = []
    lines.append(f"# Outreach B2G — Relatorio Semanal {week}")
    lines.append("")
    lines.append(f"**Gerado:** {date.today().isoformat()}")
    lines.append("")
    lines.append("## Lista qualificada da semana")
    lines.append("")
    vol_fmt = f"R$ {leads_summary['volume_total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    lines.append(f"- Leads na lista: **{leads_summary['count']}**")
    lines.append(f"- Volume agregado 90d: {vol_fmt}")
    if leads_summary["top_ufs"]:
        ufs_str = ", ".join(f"{uf} ({n})" for uf, n in leads_summary["top_ufs"])
        lines.append(f"- Top UFs: {ufs_str}")
    try:
        source_label = str(week_path.relative_to(REPO_ROOT))
    except ValueError:
        source_label = str(week_path)
    lines.append(f"- Fonte: `{source_label}`")
    lines.append("")
    lines.append("## Execucao de outreach")
    lines.append("")
    if crm_summary["total_contacts"] == 0:
        lines.append("_Sem CRM registrado. Meta semanal: 15 contatos (10 email + 5 LinkedIn)._")
    else:
        lines.append(f"- Contatos enviados: **{crm_summary['total_contacts']}** (meta 15)")
        for canal, n in crm_summary["contacts_by_channel"].items():
            lines.append(f"  - {canal}: {n}")
        lines.append(f"- Response rate: {crm_summary['response_rate']:.1%}")
        lines.append(f"- Trial-start rate: {crm_summary['trial_start_rate']:.1%}")
    lines.append("")
    lines.append("## Pipeline atual")
    lines.append("")
    lines.append("| Estagio | Qtd |")
    lines.append("|---------|-----|")
    for stage, count in crm_summary["pipeline"].items():
        lines.append(f"| {stage} | {count} |")
    lines.append("")
    lines.append("## Bloqueadores identificados")
    lines.append("")
    lines.append("_(preencher manualmente)_")
    lines.append("")
    lines.append("## Proxima semana")
    lines.append("")
    lines.append("- [ ] Rodar `scripts/b2g_outreach_query.py` com --week novo")
    lines.append("- [ ] Atualizar templates com base no response rate")
    lines.append("- [ ] Revisar estagios travados >14 dias")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate weekly B2G outreach report.")
    parser.add_argument("--week", type=str, default=None)
    parser.add_argument("--leads", type=str, default=None, help="Path to leads CSV for the week")
    parser.add_argument("--crm", type=str, default=None, help="Optional CRM CSV (Airtable/Notion export)")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    week = args.week or current_week_tag()
    leads_path = Path(args.leads) if args.leads else REPO_ROOT / "data" / "outreach" / f"leads-{week}.csv"
    crm_path = Path(args.crm) if args.crm else REPO_ROOT / "data" / "outreach" / "crm.csv"

    leads = read_csv_if_exists(leads_path)
    crm_rows = read_csv_if_exists(crm_path)

    leads_summary = summarize_leads(leads)
    crm_summary = summarize_crm(crm_rows)

    report = render_report(week, leads_summary, crm_summary, leads_path)
    output = Path(args.output) if args.output else REPO_ROOT / "docs" / "sales" / "reports" / f"weekly-{week}.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(f"Wrote report to {output}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
