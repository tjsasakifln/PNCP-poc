#!/usr/bin/env python3
"""
Gerador de PDF executivo para Relatório B2G de Oportunidades.

Recebe JSON com dados coletados pelos agentes e gera PDF institucional
com análise estratégica por edital.

Usage:
    python scripts/generate-report-b2g.py --input data.json --output report.pdf
    python scripts/generate-report-b2g.py --input data.json  # output auto-named

Input JSON schema: see SCHEMA section below.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (
        KeepTogether,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError:
    print("ERROR: reportlab not installed. Run: pip install reportlab")
    sys.exit(1)

# ============================================================
# BRAND & CONSTANTS
# ============================================================

FOOTER_TEXT = "Tiago Sasaki - Consultor de Inteligência em Licitações (48)9 8834-4559"
FOOTER_LINE2 = "Relatório confidencial preparado exclusivamente para o destinatário"

BRAND_DARK = colors.HexColor("#1a2332")
BRAND_PRIMARY = colors.HexColor("#1B3A5C")
BRAND_SECONDARY = colors.HexColor("#2C5F8A")
BRAND_LIGHT = colors.HexColor("#E8F0FE")
BRAND_ACCENT = colors.HexColor("#3B82F6")

GREEN = colors.HexColor("#16A34A")
YELLOW = colors.HexColor("#CA8A04")
RED = colors.HexColor("#DC2626")
ORANGE = colors.HexColor("#EA580C")

TABLE_HEADER_BG = BRAND_PRIMARY
TABLE_HEADER_FG = colors.white
TABLE_ALT_ROW = colors.HexColor("#F8FAFC")
TABLE_BORDER = colors.HexColor("#CBD5E1")

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 2 * cm

ILLEGAL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

# Regex to detect broken PNCP links using hyphens instead of slashes
# e.g. https://pncp.gov.br/app/editais/27142058000126-2026-85
_PNCP_HYPHEN_LINK_RE = re.compile(
    r"https://pncp\.gov\.br/app/editais/(\d{14})-(\d{4})-(\d+)$"
)
# Regex to detect fabricated search query links
_PNCP_SEARCH_LINK_RE = re.compile(
    r"https://pncp\.gov\.br/app/editais\?q="
)

# Recommendation colors/labels
REC_COLORS = {
    "PARTICIPAR": GREEN,
    "AVALIAR": YELLOW,
    "AVALIAR COM CAUTELA": YELLOW,
    "NÃO RECOMENDADO": RED,
}

# Source status → confidence badge
SOURCE_BADGES = {
    "API": ("✓", GREEN, "Confirmado via API"),
    "CALCULATED": ("✓", GREEN, "Calculado"),
    "API_PARTIAL": ("~", YELLOW, "Dados parciais"),
    "ESTIMATED": ("~", YELLOW, "Estimado"),
    "API_FAILED": ("✗", RED, "API indisponível"),
    "UNAVAILABLE": ("—", colors.HexColor("#94A3B8"), "Não disponível"),
}


# ============================================================
# HELPERS
# ============================================================

def _normalize_recommendation(rec: str) -> str:
    """Normalize recommendation text: fix accents, casing."""
    rec = rec.strip().upper()
    # Fix missing accents
    rec = rec.replace("NAO RECOMENDADO", "NÃO RECOMENDADO")
    rec = rec.replace("NAO ", "NÃO ")
    # Normalize variants
    if "PARTICIPAR" in rec:
        return "PARTICIPAR"
    if "CAUTELA" in rec or "AVALIAR" in rec:
        return "AVALIAR COM CAUTELA"
    if "NÃO" in rec or "RECOMENDADO" in rec:
        return "NÃO RECOMENDADO"
    return rec


def _validate_json(data: dict) -> list[str]:
    """Validate the input JSON and return list of warnings."""
    warnings = []
    if "empresa" not in data:
        warnings.append("Campo 'empresa' ausente")
    else:
        emp = data["empresa"]
        for field in ["cnpj", "razao_social"]:
            if not emp.get(field):
                warnings.append(f"empresa.{field} ausente")
    if "editais" not in data:
        warnings.append("Campo 'editais' ausente")
    for i, ed in enumerate(data.get("editais", [])):
        if not ed.get("objeto"):
            warnings.append(f"edital[{i}].objeto ausente")
        if not ed.get("orgao"):
            warnings.append(f"edital[{i}].orgao ausente")
    if warnings:
        print(f"⚠ Validação JSON: {len(warnings)} avisos")
        for w in warnings[:5]:
            print(f"  - {w}")
    return warnings


def _get_source_badge(source: dict | str | None) -> tuple[str, Any, str]:
    """Extract confidence badge from _source field."""
    if not source:
        return SOURCE_BADGES["UNAVAILABLE"]
    if isinstance(source, str):
        return SOURCE_BADGES.get(source, SOURCE_BADGES["UNAVAILABLE"])
    status = source.get("status", "UNAVAILABLE") if isinstance(source, dict) else "UNAVAILABLE"
    return SOURCE_BADGES.get(status, SOURCE_BADGES["UNAVAILABLE"])

def _fix_pncp_link(link: str | None) -> str:
    """Fix common PNCP link format errors.

    Corrects:
    - Hyphens instead of slashes: .../27142058000126-2026-85 -> .../27142058000126/2026/85
    - Fabricated search query links: ...?q=reforma+obra -> removed (returns empty)
    """
    if not link:
        return ""
    link = str(link).strip()

    # Fix hyphen-separated format -> slash-separated
    m = _PNCP_HYPHEN_LINK_RE.match(link)
    if m:
        cnpj, ano, seq = m.groups()
        return f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"

    # Remove fabricated search query links (they don't work on PNCP)
    if _PNCP_SEARCH_LINK_RE.match(link):
        return ""

    return link


def _s(value: Any) -> str:
    if value is None:
        return ""
    return ILLEGAL_CHARS_RE.sub(" ", str(value))


def _currency(value: Any) -> str:
    if value is None:
        return "N/I"
    try:
        v = float(value)
    except (ValueError, TypeError):
        return "N/I"
    if v == 0:
        return "R$ 0,00"
    formatted = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def _currency_short(value: Any) -> str:
    if value is None:
        return "N/I"
    try:
        v = float(value)
    except (ValueError, TypeError):
        return "N/I"
    if v >= 1_000_000:
        return f"R$ {v / 1_000_000:,.1f}M".replace(",", "X").replace(".", ",").replace("X", ".")
    if v >= 1_000:
        return f"R$ {v / 1_000:,.0f}K".replace(",", "X").replace(".", ",").replace("X", ".")
    return _currency(v)


def _date(value: str | None) -> str:
    if not value:
        return "N/I"
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y", "%Y%m%d"):
        try:
            dt = datetime.strptime(text[:10], fmt)
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            continue
    return text[:10]


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%d/%m/%Y")


def _trunc(text: str, n: int = 100) -> str:
    text = _s(text)
    return text if len(text) <= n else text[: n - 3].rstrip() + "..."


def _safe_float(v: Any, d: float = 0.0) -> float:
    try:
        return float(v) if v is not None else d
    except (ValueError, TypeError):
        return d


def _safe_int(v: Any, d: int = 0) -> int:
    try:
        return int(v) if v is not None else d
    except (ValueError, TypeError):
        return d


# ============================================================
# STYLES
# ============================================================

def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    s: dict[str, ParagraphStyle] = {}

    s["cover_title"] = ParagraphStyle(
        "cover_title", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=22, textColor=BRAND_PRIMARY,
        alignment=TA_CENTER, leading=28, spaceAfter=6 * mm,
    )
    s["cover_subtitle"] = ParagraphStyle(
        "cover_subtitle", parent=base["Normal"],
        fontName="Helvetica", fontSize=14, textColor=BRAND_SECONDARY,
        alignment=TA_CENTER, spaceAfter=4 * mm,
    )
    s["cover_info"] = ParagraphStyle(
        "cover_info", parent=base["Normal"],
        fontName="Helvetica", fontSize=11, textColor=colors.HexColor("#475569"),
        alignment=TA_CENTER, leading=16, spaceAfter=3 * mm,
    )
    s["h1"] = ParagraphStyle(
        "h1_r", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=16, textColor=BRAND_PRIMARY,
        spaceBefore=6 * mm, spaceAfter=4 * mm,
    )
    s["h2"] = ParagraphStyle(
        "h2_r", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=13, textColor=BRAND_SECONDARY,
        spaceBefore=4 * mm, spaceAfter=3 * mm,
    )
    s["h3"] = ParagraphStyle(
        "h3_r", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=11, textColor=BRAND_PRIMARY,
        spaceBefore=3 * mm, spaceAfter=2 * mm,
    )
    s["body"] = ParagraphStyle(
        "body_r", parent=base["Normal"],
        fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#1E293B"),
        alignment=TA_JUSTIFY, leading=14, spaceAfter=2 * mm,
    )
    s["body_small"] = ParagraphStyle(
        "body_small_r", parent=base["Normal"],
        fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#475569"),
        leading=12, spaceAfter=1.5 * mm,
    )
    s["bullet"] = ParagraphStyle(
        "bullet_r", parent=base["Normal"],
        fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#1E293B"),
        leading=14, leftIndent=10, spaceAfter=1.5 * mm,
    )
    s["metric_value"] = ParagraphStyle(
        "mv_r", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=16, textColor=BRAND_PRIMARY,
        alignment=TA_CENTER, leading=20,
    )
    s["metric_label"] = ParagraphStyle(
        "ml_r", parent=base["Normal"],
        fontName="Helvetica", fontSize=8, textColor=colors.HexColor("#64748B"),
        alignment=TA_CENTER, leading=10,
    )
    for name, align in [("cell", TA_LEFT), ("cell_center", TA_CENTER), ("cell_right", TA_RIGHT)]:
        s[name] = ParagraphStyle(
            f"{name}_r", parent=base["Normal"],
            fontName="Helvetica", fontSize=8, textColor=colors.HexColor("#1E293B"),
            leading=10, alignment=align,
        )
    s["cell_header"] = ParagraphStyle(
        "ch_r", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=8, textColor=TABLE_HEADER_FG,
        leading=10, alignment=TA_CENTER,
    )
    # Recommendation badge styles
    for rec, color in REC_COLORS.items():
        key = f"rec_{rec.lower().replace(' ', '_').replace('ã', 'a')}"
        s[key] = ParagraphStyle(
            key, parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=10, textColor=color,
            alignment=TA_CENTER, leading=14,
        )

    return s


# ============================================================
# FOOTER
# ============================================================

def _draw_footer(canvas, doc):
    canvas.saveState()
    y = MARGIN - 10 * mm

    canvas.setStrokeColor(TABLE_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, y + 4 * mm, PAGE_WIDTH - MARGIN, y + 4 * mm)

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawCentredString(PAGE_WIDTH / 2, y + 1.5 * mm, FOOTER_TEXT)

    canvas.setFillColor(colors.HexColor("#94A3B8"))
    canvas.drawCentredString(PAGE_WIDTH / 2, y - 2 * mm, FOOTER_LINE2)

    canvas.drawRightString(PAGE_WIDTH - MARGIN, y - 2 * mm, f"Página {doc.page}")
    canvas.restoreState()


# ============================================================
# PAGE BUILDERS
# ============================================================

def _metric_cell(value: str, label: str, styles: dict) -> Table:
    inner = Table(
        [[Paragraph(value, styles["metric_value"])],
         [Paragraph(label, styles["metric_label"])]],
        colWidths=["*"],
    )
    inner.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    return inner


def _build_cover(data: dict, styles: dict, gen_date: str) -> list:
    el = []
    empresa = data.get("empresa", {})

    el.append(Spacer(1, 55 * mm))

    # Decorative line
    line_t = Table([["", ""]], colWidths=[PAGE_WIDTH / 2 - MARGIN])
    line_t.setStyle(TableStyle([("LINEBELOW", (0, 0), (0, 0), 3, BRAND_ACCENT)]))
    el.append(line_t)
    el.append(Spacer(1, 8 * mm))

    el.append(Paragraph("Relatório Executivo de<br/>Oportunidades em Licitações", styles["cover_title"]))

    nome = _s(empresa.get("nome_fantasia") or empresa.get("razao_social", ""))
    if nome:
        el.append(Paragraph(f"Preparado para <b>{nome}</b>", styles["cover_subtitle"]))

    el.append(Spacer(1, 10 * mm))

    cnpj = _s(empresa.get("cnpj", ""))
    setor = _s(data.get("setor", ""))
    uf_sede = _s(empresa.get("uf_sede", ""))
    cidade = _s(empresa.get("cidade_sede", ""))

    for line in [
        f"<b>CNPJ:</b> {cnpj}",
        f"<b>Setor:</b> {setor}",
        f"<b>Sede:</b> {cidade} - {uf_sede}" if cidade else f"<b>UF:</b> {uf_sede}",
        f"<b>Data:</b> {gen_date}",
    ]:
        el.append(Paragraph(line, styles["cover_info"]))

    el.append(Spacer(1, 20 * mm))

    # Consultant attribution
    el.append(Paragraph(
        "<b>Tiago Sasaki</b><br/>Consultor de Licitações<br/>(48)9 8834-4559",
        styles["cover_info"],
    ))

    el.append(PageBreak())
    return el


def _build_company_profile(data: dict, styles: dict) -> list:
    el = []
    emp = data.get("empresa", {})

    el.append(Paragraph("1. Perfil da Empresa", styles["h1"]))

    fields = [
        ("Razão Social", emp.get("razao_social")),
        ("Nome Fantasia", emp.get("nome_fantasia")),
        ("CNPJ", emp.get("cnpj")),
        ("CNAE Principal", emp.get("cnae_principal")),
        ("CNAEs Secundários", emp.get("cnaes_secundarios")),
        ("Porte", emp.get("porte")),
        ("Capital Social", _currency(emp.get("capital_social")) if emp.get("capital_social") else None),
        ("Sede", f"{emp.get('cidade_sede', '')} - {emp.get('uf_sede', '')}"),
        ("Situação Cadastral", emp.get("situacao_cadastral")),
    ]
    for label, value in fields:
        if value:
            el.append(Paragraph(f"<b>{label}:</b> {_s(value)}", styles["body"]))

    # QSA / Decisores
    qsa = emp.get("qsa", [])
    if qsa:
        el.append(Spacer(1, 2 * mm))
        el.append(Paragraph("Quadro Societário", styles["h2"]))
        for socio in qsa[:5]:
            nome = _s(socio.get("nome", socio) if isinstance(socio, dict) else socio)
            qual = _s(socio.get("qualificacao", "")) if isinstance(socio, dict) else ""
            line = f"• {nome}" + (f" ({qual})" if qual else "")
            el.append(Paragraph(line, styles["bullet"]))

    # Sanções
    sancoes = emp.get("sancoes", {})
    if sancoes:
        el.append(Spacer(1, 2 * mm))
        el.append(Paragraph("Situação de Sanções", styles["h2"]))
        has_sanction = any(sancoes.get(k) for k in ["ceis", "cnep", "cepim", "ceaf"])
        if has_sanction:
            el.append(Paragraph(
                "<font color='#DC2626'><b>ATENÇÃO: Empresa possui sanção ativa.</b></font>",
                styles["body"],
            ))
            for k, label in [("ceis", "CEIS"), ("cnep", "CNEP"), ("cepim", "CEPIM"), ("ceaf", "CEAF")]:
                if sancoes.get(k):
                    el.append(Paragraph(f"• <font color='#DC2626'>{label}: Sancionada</font>", styles["bullet"]))
        else:
            el.append(Paragraph(
                "<font color='#16A34A'><b>Sem sanções ativas (CEIS, CNEP, CEPIM, CEAF)</b></font>",
                styles["body"],
            ))

    # Histórico de contratos governamentais
    historico = emp.get("historico_contratos", [])
    if historico:
        el.append(Spacer(1, 2 * mm))
        el.append(Paragraph("Histórico de Contratos Governamentais", styles["h2"]))
        el.append(Paragraph(
            f"Total de contratos no histórico federal: <b>{len(historico)}</b>",
            styles["body"],
        ))
        valor_hist = sum(_safe_float(c.get("valor")) for c in historico)
        if valor_hist > 0:
            el.append(Paragraph(f"Valor total histórico: <b>{_currency(valor_hist)}</b>", styles["body"]))

    el.append(PageBreak())
    return el


def _build_executive_summary(data: dict, styles: dict) -> list:
    el = []
    editais = data.get("editais", [])
    resumo = data.get("resumo_executivo", {})

    el.append(Paragraph("2. Resumo Executivo", styles["h1"]))

    # Summary text
    texto = _s(resumo.get("texto", ""))
    if texto:
        el.append(Paragraph(texto, styles["body"]))
        el.append(Spacer(1, 4 * mm))

    # Metrics
    total = len(editais)
    participar = sum(1 for e in editais if (e.get("recomendacao") or "").upper().startswith("PARTICIPAR"))
    cautela = sum(1 for e in editais if "CAUTELA" in (e.get("recomendacao") or "").upper() or "AVALIAR" in (e.get("recomendacao") or "").upper())
    valores = [_safe_float(e.get("valor_estimado")) for e in editais if e.get("valor_estimado")]
    valor_total = sum(valores)

    avail = PAGE_WIDTH - 2 * MARGIN
    col_w = avail / 4
    metrics = Table(
        [[
            _metric_cell(str(total), "Editais Encontrados", styles),
            _metric_cell(str(participar), "Recomendados", styles),
            _metric_cell(str(cautela), "Avaliar", styles),
            _metric_cell(_currency_short(valor_total), "Valor Total", styles),
        ]],
        colWidths=[col_w] * 4, rowHeights=[22 * mm],
    )
    metrics.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_LIGHT),
        ("BOX", (0, 0), (0, 0), 0.5, TABLE_BORDER),
        ("BOX", (1, 0), (1, 0), 0.5, TABLE_BORDER),
        ("BOX", (2, 0), (2, 0), 0.5, TABLE_BORDER),
        ("BOX", (3, 0), (3, 0), 0.5, TABLE_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    el.append(metrics)
    el.append(Spacer(1, 6 * mm))

    # Distribution by UF
    uf_counts: dict[str, int] = {}
    for e in editais:
        uf = e.get("uf", "N/I")
        if uf:
            uf_counts[uf] = uf_counts.get(uf, 0) + 1
    if uf_counts:
        el.append(Paragraph("Distribuição por UF", styles["h2"]))
        header = [Paragraph(f"<b>{h}</b>", styles["cell_header"]) for h in ["UF", "Qtd", "%"]]
        rows = [header]
        for uf, cnt in sorted(uf_counts.items(), key=lambda x: -x[1])[:8]:
            pct = cnt / total * 100 if total else 0
            rows.append([
                Paragraph(uf, styles["cell_center"]),
                Paragraph(str(cnt), styles["cell_center"]),
                Paragraph(f"{pct:.0f}%", styles["cell_center"]),
            ])
        t = Table(rows, colWidths=[avail * 0.3, avail * 0.35, avail * 0.35])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
            ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ] + [("BACKGROUND", (0, i), (-1, i), TABLE_ALT_ROW) for i in range(2, len(rows), 2)]))
        el.append(t)
        el.append(Spacer(1, 4 * mm))

    # Destaques
    destaques = resumo.get("destaques", [])
    if destaques:
        el.append(Paragraph("Destaques", styles["h2"]))
        for d in destaques:
            el.append(Paragraph(f"• {_s(d)}", styles["bullet"]))

    el.append(PageBreak())
    return el


def _build_opportunities_overview(data: dict, styles: dict) -> list:
    el = []
    editais = data.get("editais", [])
    if not editais:
        return el

    el.append(Paragraph("3. Panorama de Oportunidades", styles["h1"]))
    el.append(Spacer(1, 2 * mm))

    avail = PAGE_WIDTH - 2 * MARGIN
    col_widths = [
        avail * 0.04,  # #
        avail * 0.30,  # Objeto
        avail * 0.14,  # Órgão
        avail * 0.05,  # UF
        avail * 0.13,  # Valor
        avail * 0.11,  # Modalidade
        avail * 0.08,  # Prazo
        avail * 0.15,  # Recomendação
    ]

    header = [Paragraph(f"<b>{h}</b>", styles["cell_header"]) for h in [
        "#", "Objeto", "Órgão", "UF", "Valor", "Modalidade", "Prazo", "Recomendação",
    ]]
    rows = [header]

    for idx, ed in enumerate(editais, 1):
        rec = _normalize_recommendation(_s(ed.get("recomendacao", "")))
        rec_color = REC_COLORS.get(rec, RED)

        rec_style = ParagraphStyle(
            f"rec_{idx}", parent=styles["cell_center"],
            fontName="Helvetica-Bold", textColor=rec_color,
        )

        dias = ed.get("dias_restantes")
        prazo = f"{_safe_int(dias)}d" if dias is not None else _date(ed.get("data_encerramento"))

        # Show ENCERRADO status
        status = ed.get("status_edital", "")
        if status == "ENCERRADO":
            rec = "ENCERRADO"
            rec_color = colors.HexColor("#94A3B8")
            rec_style = ParagraphStyle(
                f"rec_enc_{idx}", parent=styles["cell_center"],
                fontName="Helvetica-Bold", textColor=rec_color,
            )

        rows.append([
            Paragraph(str(idx), styles["cell_center"]),
            Paragraph(_trunc(ed.get("objeto", ""), 80), styles["cell"]),
            Paragraph(_trunc(ed.get("orgao", ""), 40), styles["cell"]),
            Paragraph(_s(ed.get("uf", "")), styles["cell_center"]),
            Paragraph(_currency(_safe_float(ed.get("valor_estimado"))), styles["cell_right"]),
            Paragraph(_trunc(ed.get("modalidade", ""), 25), styles["cell"]),
            Paragraph(str(prazo), styles["cell_center"]),
            Paragraph(rec, rec_style),
        ])

    t = Table(rows, colWidths=col_widths, repeatRows=1)
    base_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]
    for i in range(2, len(rows), 2):
        base_styles.append(("BACKGROUND", (0, i), (-1, i), TABLE_ALT_ROW))
    t.setStyle(TableStyle(base_styles))
    el.append(t)

    el.append(PageBreak())
    return el


def _build_detailed_analysis(data: dict, styles: dict) -> list:
    el = []
    editais = data.get("editais", [])
    if not editais:
        return el

    el.append(Paragraph("4. Análise Detalhada por Edital", styles["h1"]))
    el.append(Spacer(1, 2 * mm))

    for idx, ed in enumerate(editais, 1):
        section = []

        # Edital header
        objeto = _s(ed.get("objeto", "Sem título"))
        section.append(Paragraph(f"4.{idx}. {_trunc(objeto, 120)}", styles["h2"]))

        # Basic info table
        avail = PAGE_WIDTH - 2 * MARGIN
        info_rows = []
        fields = [
            ("Órgão", ed.get("orgao")),
            ("UF / Município", f"{ed.get('uf', 'N/I')} - {ed.get('municipio', 'N/I')}"),
            ("Modalidade", ed.get("modalidade")),
            ("Valor Estimado", _currency(ed.get("valor_estimado")) if ed.get("valor_estimado") else "N/I"),
            ("Data de Abertura", _date(ed.get("data_abertura"))),
            ("Data de Encerramento", _date(ed.get("data_encerramento"))),
            ("Dias Restantes", str(ed.get("dias_restantes", "N/I"))),
            ("Fonte", ed.get("fonte", "N/I")),
            ("Link", ed.get("link", "N/I")),
        ]
        for label, value in fields:
            if value and value != "N/I" and value != " - N/I":
                info_rows.append([
                    Paragraph(f"<b>{label}</b>", styles["cell"]),
                    Paragraph(_s(str(value)), styles["cell"]),
                ])
        if info_rows:
            info_t = Table(info_rows, colWidths=[avail * 0.25, avail * 0.75])
            info_t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
                ("BACKGROUND", (0, 0), (0, -1), BRAND_LIGHT),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ]))
            section.append(info_t)
            section.append(Spacer(1, 3 * mm))

        # Distance (from collect-report-data.py)
        distancia = ed.get("distancia", {})
        if isinstance(distancia, dict) and distancia.get("km"):
            km = distancia["km"]
            hrs = distancia.get("duracao_horas", "")
            badge_char, badge_color_d, badge_text = _get_source_badge(distancia.get("_source"))
            dist_text = f"<b>Distância da sede:</b> {km} km"
            if hrs:
                dist_text += f" (~{hrs}h de carro)"
            dist_text += f" <font color='{'#16A34A' if badge_char == '✓' else '#CA8A04'}'>[{badge_char} {badge_text}]</font>"
            section.append(Paragraph(dist_text, styles["body"]))

        # Recommendation badge
        rec = _normalize_recommendation(_s(ed.get("recomendacao", "")))
        if rec:
            badge_color = REC_COLORS.get(rec, RED)

            # Override for ENCERRADO
            if ed.get("status_edital") == "ENCERRADO":
                rec = "ENCERRADO"
                badge_color = colors.HexColor("#94A3B8")

            badge_style = ParagraphStyle(
                f"badge_{idx}", parent=styles["body"],
                fontName="Helvetica-Bold", fontSize=11, textColor=badge_color,
            )
            section.append(Paragraph(f"Recomendação: {rec}", badge_style))
            section.append(Spacer(1, 2 * mm))

        # Analysis sections
        analise = ed.get("analise", {})

        analysis_fields = [
            ("Aderência ao Perfil", "aderencia"),
            ("Análise de Valor", "valor"),
            ("Análise Geográfica", "geografica"),
            ("Análise de Prazo", "prazo"),
            ("Análise de Modalidade", "modalidade"),
            ("Competitividade", "competitividade"),
            ("Riscos e Alertas", "riscos"),
        ]
        for title, key in analysis_fields:
            text = _s(analise.get(key, ""))
            if text:
                section.append(Paragraph(f"<b>{title}:</b> {text}", styles["body"]))

        # Q&A section
        perguntas = ed.get("perguntas_decisor", {})
        if perguntas:
            section.append(Spacer(1, 2 * mm))
            section.append(Paragraph("Perguntas do Decisor", styles["h3"]))
            for pergunta, resposta in perguntas.items():
                if resposta:
                    section.append(Paragraph(
                        f"<b>{_s(pergunta)}</b>",
                        styles["body"],
                    ))
                    section.append(Paragraph(f"{_s(resposta)}", styles["body_small"]))
                    section.append(Spacer(1, 1 * mm))

        section.append(Spacer(1, 4 * mm))

        # Keep edital header + first few lines together
        el.extend(section)

    el.append(PageBreak())
    return el


def _build_market_intelligence(data: dict, styles: dict) -> list:
    el = []
    intel = data.get("inteligencia_mercado", {})
    if not intel:
        return el

    el.append(Paragraph("5. Inteligência de Mercado", styles["h1"]))

    for title, key in [
        ("Panorama Setorial", "panorama"),
        ("Tendências", "tendencias"),
        ("Vantagens Competitivas da Empresa", "vantagens"),
        ("Recomendação Geral", "recomendacao_geral"),
    ]:
        text = _s(intel.get(key, ""))
        if text:
            el.append(Paragraph(title, styles["h2"]))
            # Split by newlines for better formatting
            for paragraph in text.split("\n"):
                paragraph = paragraph.strip()
                if paragraph:
                    if paragraph.startswith("•") or paragraph.startswith("-"):
                        el.append(Paragraph(paragraph, styles["bullet"]))
                    else:
                        el.append(Paragraph(paragraph, styles["body"]))

    el.append(PageBreak())
    return el


def _build_querido_diario(data: dict, styles: dict) -> list:
    el = []
    mencoes = data.get("querido_diario", [])
    if not mencoes:
        return el

    el.append(Paragraph("6. Menções em Diários Oficiais", styles["h1"]))
    el.append(Paragraph(
        "Publicações encontradas no Querido Diário (diários oficiais municipais).",
        styles["body_small"],
    ))
    el.append(Spacer(1, 3 * mm))

    for idx, m in enumerate(mencoes[:10], 1):
        el.append(Paragraph(f"<b>{idx}. {_date(m.get('data'))} - {_s(m.get('territorio', ''))}</b>", styles["body"]))
        excerpts = m.get("excerpts", [])
        for exc in excerpts[:2]:
            text = _s(exc.get("text", exc) if isinstance(exc, dict) else exc)
            el.append(Paragraph(f"<i>\"{_trunc(text, 300)}\"</i>", styles["body_small"]))
        el.append(Spacer(1, 2 * mm))

    el.append(PageBreak())
    return el


def _build_next_steps(data: dict, styles: dict) -> list:
    el = []
    proximos = data.get("proximos_passos", [])

    section_num = "7" if data.get("querido_diario") else "6"
    el.append(Paragraph(f"{section_num}. Próximos Passos", styles["h1"]))

    if proximos:
        for step in proximos:
            if isinstance(step, dict):
                acao = _s(step.get("acao", ""))
                prazo = _s(step.get("prazo", ""))
                prioridade = _s(step.get("prioridade", ""))
                line = f"• <b>{acao}</b>"
                if prazo:
                    line += f" (Prazo: {prazo})"
                if prioridade:
                    line += f" [{prioridade}]"
                el.append(Paragraph(line, styles["bullet"]))
            else:
                el.append(Paragraph(f"• {_s(step)}", styles["bullet"]))
    else:
        el.append(Paragraph(
            "1. Revisar os editais marcados como PARTICIPAR e iniciar preparação documental",
            styles["bullet"],
        ))
        el.append(Paragraph(
            "2. Avaliar os editais marcados como AVALIAR COM CAUTELA conforme capacidade operacional",
            styles["bullet"],
        ))
        el.append(Paragraph(
            "3. Monitorar novos editais semanalmente para oportunidades adicionais",
            styles["bullet"],
        ))

    el.append(Spacer(1, 10 * mm))
    el.append(Paragraph(
        "Para dúvidas ou acompanhamento, entre em contato:<br/>"
        "<b>Tiago Sasaki</b> - (48)9 8834-4559",
        styles["body"],
    ))

    return el


# ============================================================
# SICAF & SOURCE CONFIDENCE
# ============================================================

def _build_sicaf_section(data: dict, styles: dict) -> list:
    el = []
    sicaf = data.get("sicaf", {})
    if not sicaf:
        return el

    # Dynamic section number
    has_qd = bool(data.get("querido_diario"))
    section_num = "8" if has_qd else "7"

    el.append(Paragraph(f"{section_num}. Verificação SICAF", styles["h1"]))

    badge_char, badge_color, badge_text = _get_source_badge(sicaf.get("_source"))

    # New format: collect-sicaf.py output with crc + restricao
    crc = sicaf.get("crc", {})
    restricao = sicaf.get("restricao", {})

    if crc or restricao:
        # CRC section
        if crc:
            status_cad = _s(crc.get("status_cadastral", ""))
            color = "#16A34A" if status_cad == "CADASTRADO" else "#DC2626" if "NÃO" in status_cad else "#CA8A04"
            el.append(Paragraph(
                f"<b>Status Cadastral (CRC):</b> <font color='{color}'><b>{status_cad}</b></font>",
                styles["body"],
            ))
            # Show parsed CRC fields
            for label, key in [
                ("Razão Social", "razao_social"),
                ("CNAE", "atividade_principal"),
                ("Endereço", "endereco"),
                ("Emissão CRC", "data_emissao"),
            ]:
                val = crc.get(key)
                if val:
                    el.append(Paragraph(f"<b>{label}:</b> {_s(val)}", styles["body"]))

            # Habilitação details
            hab = crc.get("habilitacao", {})
            if hab:
                el.append(Spacer(1, 2 * mm))
                el.append(Paragraph("<b>Habilitações SICAF:</b>", styles["body"]))
                for label, key in [
                    ("Habilitação Jurídica", "habilitacao_juridica"),
                    ("Fiscal Federal", "regularidade_fiscal_federal"),
                    ("Fiscal Estadual", "regularidade_fiscal_estadual"),
                    ("Fiscal Municipal", "regularidade_fiscal_municipal"),
                    ("Trabalhista", "regularidade_trabalhista"),
                    ("Qualificação Econômica", "qualificacao_economica"),
                ]:
                    val = hab.get(key)
                    if val:
                        hcolor = "#16A34A" if val.lower() == "regular" else "#DC2626"
                        el.append(Paragraph(
                            f"  • {label}: <font color='{hcolor}'><b>{_s(val)}</b></font>",
                            styles["body_small"],
                        ))

            detalhe = crc.get("detalhe")
            if detalhe and status_cad != "CADASTRADO":
                el.append(Paragraph(f"<i>{_s(detalhe)}</i>", styles["body_small"]))

        el.append(Spacer(1, 3 * mm))

        # Restrição section
        if restricao:
            possui = restricao.get("possui_restricao", False)
            if possui:
                el.append(Paragraph(
                    "<b>Restrições:</b> <font color='#DC2626'><b>SIM — Verificar detalhes</b></font>",
                    styles["body"],
                ))
                for r in restricao.get("restricoes", []):
                    el.append(Paragraph(
                        f"  • {_s(r.get('tipo', ''))} — {_s(r.get('detalhe', ''))}",
                        styles["body_small"],
                    ))
            else:
                el.append(Paragraph(
                    "<b>Restrições:</b> <font color='#16A34A'><b>Nenhuma</b></font>",
                    styles["body"],
                ))
    else:
        # Legacy format: simple status + instrucao
        status = _s(sicaf.get("status", ""))
        instrucao = _s(sicaf.get("instrucao", ""))
        url = sicaf.get("url", "")

        el.append(Paragraph(
            f"<font color='#CA8A04'><b>{status}</b></font>",
            styles["body"],
        ))
        if instrucao:
            el.append(Paragraph(instrucao, styles["body"]))
        if url:
            el.append(Paragraph(f"<b>Portal:</b> {url}", styles["body"]))

    el.append(Spacer(1, 3 * mm))
    el.append(Paragraph(
        f"<font color='#94A3B8'>[{badge_char} {badge_text}]</font>",
        styles["body_small"],
    ))

    el.append(Spacer(1, 6 * mm))
    return el


def _build_data_sources_section(data: dict, styles: dict) -> list:
    """Render data provenance section showing source status for each data category."""
    el = []
    metadata = data.get("_metadata", {})
    sources = metadata.get("sources", {})
    if not sources:
        return el

    has_qd = bool(data.get("querido_diario"))
    has_sicaf = bool(data.get("sicaf"))
    section_num = 7 + (1 if has_qd else 0) + (1 if has_sicaf else 0)

    el.append(Paragraph(f"{section_num}. Fontes de Dados e Confiabilidade", styles["h1"]))
    el.append(Paragraph(
        "Cada dado neste relatório foi obtido de forma determinística via APIs públicas. "
        "A tabela abaixo indica o status de cada fonte no momento da coleta.",
        styles["body_small"],
    ))
    el.append(Spacer(1, 3 * mm))

    avail = PAGE_WIDTH - 2 * MARGIN
    header = [
        Paragraph("<b>Fonte</b>", styles["cell_header"]),
        Paragraph("<b>Status</b>", styles["cell_header"]),
        Paragraph("<b>Detalhe</b>", styles["cell_header"]),
    ]
    rows = [header]

    source_labels = {
        "opencnpj": "OpenCNPJ (perfil da empresa)",
        "portal_transparencia_sancoes": "Portal Transparência (sanções)",
        "portal_transparencia_contratos": "Portal Transparência (contratos)",
        "pncp": "PNCP (editais)",
        "pcp_v2": "PCP v2 (editais complementares)",
        "querido_diario": "Querido Diário (diários oficiais)",
        "sicaf": "SICAF (cadastro fornecedores)",
    }

    for key, label in source_labels.items():
        src = sources.get(key, {})
        badge_char, badge_color, badge_text = _get_source_badge(src)
        detail = src.get("detail", "") if isinstance(src, dict) else ""

        status_style = ParagraphStyle(
            f"src_{key}", parent=styles["cell"],
            fontName="Helvetica-Bold", textColor=badge_color,
        )
        rows.append([
            Paragraph(label, styles["cell"]),
            Paragraph(f"{badge_char} {badge_text}", status_style),
            Paragraph(_s(detail)[:80], styles["cell"]),
        ])

    t = Table(rows, colWidths=[avail * 0.35, avail * 0.25, avail * 0.40])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ] + [("BACKGROUND", (0, i), (-1, i), TABLE_ALT_ROW) for i in range(2, len(rows), 2)]))
    el.append(t)

    el.append(Spacer(1, 4 * mm))
    gen_at = metadata.get("generated_at", "")
    gen_by = metadata.get("generator", "")
    if gen_at or gen_by:
        el.append(Paragraph(
            f"<font color='#94A3B8'>Dados coletados em {gen_at} por {gen_by}</font>",
            styles["body_small"],
        ))

    el.append(PageBreak())
    return el


# ============================================================
# MAIN
# ============================================================

def _sanitize_links(data: dict) -> dict:
    """Fix broken PNCP links in all editais before rendering."""
    editais = data.get("editais", [])
    fixed = 0
    for ed in editais:
        original = ed.get("link", "")
        corrected = _fix_pncp_link(original)
        if corrected != original:
            ed["link"] = corrected
            fixed += 1
    if fixed:
        print(f"Links corrected: {fixed}/{len(editais)}")
    return data


def generate_report_b2g(data: dict) -> BytesIO:
    """Generate the full B2G report PDF from structured data."""
    # Validate input data and warn about issues
    _validate_json(data)

    data = _sanitize_links(data)
    gen_date = _today()
    styles = _build_styles()
    buffer = BytesIO()

    empresa = data.get("empresa", {})
    nome = _s(empresa.get("nome_fantasia") or empresa.get("razao_social", "Empresa"))
    cnpj = _s(empresa.get("cnpj", ""))

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN + 8 * mm,
        title=f"Relatório B2G - {nome} - {gen_date}",
        author="Tiago Sasaki",
        creator="Report B2G Generator",
    )

    elements: list = []
    elements.extend(_build_cover(data, styles, gen_date))
    elements.extend(_build_company_profile(data, styles))
    elements.extend(_build_executive_summary(data, styles))
    elements.extend(_build_opportunities_overview(data, styles))
    elements.extend(_build_detailed_analysis(data, styles))
    elements.extend(_build_market_intelligence(data, styles))
    elements.extend(_build_querido_diario(data, styles))
    elements.extend(_build_next_steps(data, styles))
    elements.extend(_build_sicaf_section(data, styles))
    elements.extend(_build_data_sources_section(data, styles))

    doc.build(elements, onFirstPage=_draw_footer, onLaterPages=_draw_footer)
    buffer.seek(0)
    return buffer


def main():
    parser = argparse.ArgumentParser(description="Generate B2G Report PDF from JSON data")
    parser.add_argument("--input", required=True, help="Path to JSON data file")
    parser.add_argument("--output", help="Output PDF path (auto-generated if omitted)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if args.output:
        output_path = Path(args.output)
    else:
        cnpj = data.get("empresa", {}).get("cnpj", "unknown").replace("/", "").replace(".", "").replace("-", "")
        nome = data.get("empresa", {}).get("nome_fantasia") or data.get("empresa", {}).get("razao_social", "")
        # Slugify: lowercase, replace spaces/special chars with hyphens, strip
        nome_slug = re.sub(r"[^a-z0-9]+", "-", nome.lower().strip()).strip("-")[:40] if nome else ""
        date_str = datetime.now().strftime("%Y-%m-%d")
        if nome_slug:
            output_path = input_path.parent / f"report-{cnpj}-{nome_slug}-{date_str}.pdf"
        else:
            output_path = input_path.parent / f"report-{cnpj}-{date_str}.pdf"

    buffer = generate_report_b2g(data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(buffer.getvalue())

    print(f"PDF generated: {output_path}")
    print(f"Size: {output_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()


# ============================================================
# JSON INPUT SCHEMA (for agents generating the data file)
# ============================================================
"""
{
  "empresa": {
    "cnpj": "12.345.678/0001-90",
    "razao_social": "Empresa LTDA",
    "nome_fantasia": "Empresa",
    "cnae_principal": "4120400 - Construção de edifícios",
    "cnaes_secundarios": "4211101, 4213800",
    "porte": "EPP",
    "capital_social": 1500000.00,
    "cidade_sede": "Florianópolis",
    "uf_sede": "SC",
    "situacao_cadastral": "ATIVA",
    "email": "contato@empresa.com",
    "telefones": ["(48) 99999-9999"],
    "qsa": [
      {"nome": "João Silva", "qualificacao": "Sócio-Administrador"}
    ],
    "sancoes": {"ceis": false, "cnep": false, "cepim": false, "ceaf": false},
    "historico_contratos": [
      {"orgao": "Prefeitura X", "valor": 500000, "data": "2025-06-01"}
    ]
  },
  "setor": "Engenharia e Construção Civil",
  "keywords": ["construção", "obra", "reforma", "edificação"],
  "editais": [
    {
      "objeto": "Contratação de empresa para reforma do prédio...",
      "orgao": "Prefeitura Municipal de Florianópolis",
      "uf": "SC",
      "municipio": "Florianópolis",
      "valor_estimado": 1500000.00,
      "modalidade": "Pregão Eletrônico",
      "data_abertura": "2026-03-15",
      "data_encerramento": "2026-03-25",
      "dias_restantes": 15,
      "fonte": "PNCP",
      "link": "https://pncp.gov.br/...",
      "recomendacao": "PARTICIPAR",
      "analise": {
        "aderencia": "Alta - objeto 100% compatível com CNAE principal 4120400",
        "valor": "Dentro da faixa operacional (capital R$1.5M, contrato R$1.5M)",
        "geografica": "Mesmo município da sede - custo logístico mínimo",
        "prazo": "15 dias restantes - tempo adequado para preparação",
        "modalidade": "Pregão Eletrônico - disputa por menor preço",
        "competitividade": "Órgão tem histórico de 3-5 participantes por edital",
        "riscos": "Valor no limite do capital social - avaliar BDI com cuidado"
      },
      "perguntas_decisor": {
        "Vale a pena participar?": "Sim. Objeto altamente aderente...",
        "Quanto eu deveria ofertar?": "Baseado no histórico do órgão...",
        "Quem são os concorrentes prováveis?": "Empresas locais de porte similar...",
        "Quais documentos preciso preparar?": "CND, certidões negativas...",
        "Qual o risco de não conseguir executar?": "Baixo, considerando...",
        "Esse órgão paga em dia?": "Histórico indica pagamento em 30-45 dias...",
        "Existe restrição que me impeça?": "Nenhuma restrição identificada..."
      }
    }
  ],
  "resumo_executivo": {
    "texto": "Foram identificadas X oportunidades abertas...",
    "destaques": [
      "3 editais com alta aderência ao perfil da empresa",
      "Valor total em jogo: R$ X milhões"
    ]
  },
  "inteligencia_mercado": {
    "panorama": "O setor de engenharia em SC apresenta...",
    "tendencias": "• Pregão eletrônico domina (78% das modalidades)...",
    "vantagens": "• Localização estratégica em Florianópolis...",
    "recomendacao_geral": "Focar nos 3 editais de maior aderência..."
  },
  "querido_diario": [
    {
      "data": "2026-03-08",
      "territorio": "Florianópolis - SC",
      "excerpts": [{"text": "...trecho do diário oficial mencionando..."}]
    }
  ],
  "proximos_passos": [
    {"acao": "Preparar documentação para edital X", "prazo": "5 dias", "prioridade": "ALTA"},
    {"acao": "Agendar visita técnica ao local", "prazo": "3 dias", "prioridade": "MÉDIA"}
  ]
}
"""
