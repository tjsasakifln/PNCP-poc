"""pdf_generator_edital.py — Single-bid executive PDF generator.

STORY-447: Generates a 1-page A4 PDF for an individual bid/edital.
Reuses brand constants and helpers from pdf_report.py.

Usage:
    >>> from pdf_generator_edital import generate_edital_pdf
    >>> pdf_bytes = generate_edital_pdf(bid_data, plan_type="free_trial")
    >>> # Returns bytes directly (not BytesIO)
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Brand colors (kept in sync with pdf_report.py)
# ---------------------------------------------------------------------------
BRAND_DARK_BLUE = colors.HexColor("#1B3A5C")
BRAND_MEDIUM_BLUE = colors.HexColor("#2C5F8A")
BRAND_LIGHT_BLUE = colors.HexColor("#E8F0FE")
BRAND_ACCENT = colors.HexColor("#3B82F6")

VIABILITY_GREEN = colors.HexColor("#16A34A")
VIABILITY_YELLOW = colors.HexColor("#CA8A04")
VIABILITY_RED = colors.HexColor("#DC2626")
VIABILITY_GRAY = colors.HexColor("#64748B")

TABLE_HEADER_BG = BRAND_DARK_BLUE
TABLE_ALT_ROW = colors.HexColor("#F8FAFC")
TABLE_BORDER = colors.HexColor("#CBD5E1")

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 2 * cm

ILLEGAL_CHARACTERS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitize(value: Any) -> str:
    if value is None:
        return ""
    return ILLEGAL_CHARACTERS_RE.sub(" ", str(value))


def _format_currency(value: float | int | None) -> str:
    if value is None:
        return "Não informado"
    try:
        v = float(value)
    except (ValueError, TypeError):
        return "Não informado"
    if v == 0:
        return "Não informado"
    if v >= 1_000_000:
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _format_date(date_str: str | None) -> str:
    if not date_str:
        return "Não informado"
    try:
        parts = date_str.split("T")[0].split("-")
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    except Exception:
        return _sanitize(date_str)


def _viability_color(level: str | None) -> colors.Color:
    mapping = {
        "alta": VIABILITY_GREEN,
        "media": VIABILITY_YELLOW,
        "baixa": VIABILITY_RED,
    }
    return mapping.get(level or "", VIABILITY_GRAY)


def _viability_label(level: str | None, score: float | None) -> str:
    label_map = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}
    label = label_map.get(level or "", "Não avaliada")
    if score is not None:
        return f"{label} ({int(score)}/100)"
    return label


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_edital_pdf(bid_data: dict, plan_type: str = "free_trial") -> bytes:
    """Generate a 1-page executive PDF for a single bid.

    Args:
        bid_data: Fields from LicitacaoItem + optional resumo_executivo.
        plan_type: User plan — trial users get a watermark footer.

    Returns:
        Raw PDF bytes.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=1.5 * cm,
        bottomMargin=2.5 * cm,
        title="SmartLic — Edital Executivo",
        author="SmartLic",
    )

    styles = getSampleStyleSheet()

    # Custom styles
    h1 = ParagraphStyle(
        "EditalH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=BRAND_DARK_BLUE,
        spaceAfter=4 * mm,
    )
    h2 = ParagraphStyle(
        "EditalH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=BRAND_MEDIUM_BLUE,
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    )
    body = ParagraphStyle(
        "EditalBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceAfter=2 * mm,
    )
    meta = ParagraphStyle(
        "EditalMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748B"),
    )
    watermark_style = ParagraphStyle(
        "Watermark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#94A3B8"),
        alignment=TA_CENTER,
    )

    story = []

    # ------------------------------------------------------------------
    # Header: logo text + date
    # ------------------------------------------------------------------
    header_data = [
        [
            Paragraph(
                '<font color="#1B3A5C"><b>SmartLic</b></font>'
                '<font color="#3B82F6">.tech</font>',
                ParagraphStyle(
                    "Logo",
                    parent=styles["Normal"],
                    fontName="Helvetica-Bold",
                    fontSize=14,
                    textColor=BRAND_DARK_BLUE,
                ),
            ),
            Paragraph(
                f'Gerado em {datetime.now(timezone.utc).strftime("%d/%m/%Y")}',
                ParagraphStyle(
                    "GenDate",
                    parent=styles["Normal"],
                    fontName="Helvetica",
                    fontSize=8,
                    textColor=VIABILITY_GRAY,
                    alignment=TA_RIGHT,
                ),
            ),
        ]
    ]
    header_tbl = Table(header_data, colWidths=[PAGE_WIDTH - 2 * MARGIN - 60 * mm, 55 * mm])
    header_tbl.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, TABLE_BORDER),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 4 * mm))

    # ------------------------------------------------------------------
    # Title: objeto
    # ------------------------------------------------------------------
    objeto = _sanitize(bid_data.get("objeto") or "Edital sem título")
    story.append(Paragraph(objeto, h1))

    # ------------------------------------------------------------------
    # Meta grid: Órgão | Modalidade | Valor | Prazo
    # ------------------------------------------------------------------
    orgao = _sanitize(bid_data.get("orgao") or "—")
    uf = _sanitize(bid_data.get("uf") or "")
    municipio = _sanitize(bid_data.get("municipio") or "")
    localidade = f"{municipio} - {uf}" if municipio else uf

    modalidade = _sanitize(bid_data.get("modalidade") or "Não informada")
    valor = _format_currency(bid_data.get("valor"))
    data_enc = _format_date(bid_data.get("data_encerramento"))

    meta_data = [
        ["Órgão", orgao],
        ["Localidade", localidade],
        ["Modalidade", modalidade],
        ["Valor estimado", valor],
        ["Prazo de encerramento", data_enc],
    ]
    if bid_data.get("numero_compra"):
        meta_data.append(["Nº do processo", _sanitize(bid_data["numero_compra"])])

    meta_label_style = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=BRAND_DARK_BLUE,
    )
    meta_value_style = ParagraphStyle(
        "MetaValue",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.HexColor("#334155"),
    )

    meta_rows = [
        [Paragraph(k, meta_label_style), Paragraph(v, meta_value_style)]
        for k, v in meta_data
    ]
    col_w = PAGE_WIDTH - 2 * MARGIN
    meta_tbl = Table(meta_rows, colWidths=[40 * mm, col_w - 40 * mm])
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), BRAND_LIGHT_BLUE),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.3, TABLE_BORDER),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, TABLE_ALT_ROW]),
        ("BACKGROUND", (0, 0), (0, -1), BRAND_LIGHT_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 4 * mm))

    # ------------------------------------------------------------------
    # Viability section
    # ------------------------------------------------------------------
    v_level = bid_data.get("viability_level")
    v_score = bid_data.get("viability_score")
    v_factors = bid_data.get("viability_factors") or {}

    if v_level or v_score is not None:
        story.append(Paragraph("Análise de Viabilidade", h2))

        v_color = _viability_color(v_level)
        v_label = _viability_label(v_level, v_score)

        viab_data = [
            [
                Paragraph("Viabilidade geral", meta_label_style),
                Paragraph(
                    f'<font color="#{v_color.hexval()[2:]}"><b>{v_label}</b></font>',
                    meta_value_style,
                ),
            ]
        ]

        # Factor breakdown
        factor_labels = {
            "modalidade": f"Modalidade (30%)",
            "timeline": f"Timeline (25%)",
            "value_fit": f"Valor (25%)",
            "geography": f"Geografia (20%)",
        }
        factor_display_keys = ["modalidade", "timeline", "value_fit", "geography"]
        label_suffix = {
            "modalidade": "modalidade_label",
            "timeline": "timeline_label",
            "value_fit": "value_fit_label",
            "geography": "geography_label",
        }

        for fk in factor_display_keys:
            if fk in v_factors:
                score_v = v_factors.get(fk)
                lbl_v = v_factors.get(label_suffix[fk], "")
                display = f"{lbl_v} ({int(score_v)}/100)" if score_v is not None else str(lbl_v)
                viab_data.append([
                    Paragraph(factor_labels[fk], meta_label_style),
                    Paragraph(display, meta_value_style),
                ])

        viab_tbl = Table(viab_data, colWidths=[60 * mm, col_w - 60 * mm])
        viab_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), BRAND_LIGHT_BLUE),
            ("GRID", (0, 0), (-1, -1), 0.3, TABLE_BORDER),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, TABLE_ALT_ROW]),
            ("BACKGROUND", (0, 0), (0, -1), BRAND_LIGHT_BLUE),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(viab_tbl)
        story.append(Spacer(1, 4 * mm))

    # ------------------------------------------------------------------
    # Executive summary (optional — passed from BuscaResult)
    # ------------------------------------------------------------------
    resumo = _sanitize(bid_data.get("resumo_executivo") or "")
    if resumo:
        story.append(Paragraph("Resumo Executivo", h2))
        story.append(Paragraph(resumo, body))
        story.append(Spacer(1, 2 * mm))

    # Recommendation
    recomendacao = _sanitize(bid_data.get("recomendacao") or "")
    if recomendacao:
        story.append(Paragraph("Recomendação de Participação", h2))
        story.append(Paragraph(recomendacao, body))
        story.append(Spacer(1, 2 * mm))

    # ------------------------------------------------------------------
    # Source footer
    # ------------------------------------------------------------------
    source_parts = ["Fonte: PNCP"]
    if bid_data.get("data_publicacao"):
        source_parts.append(
            f'Publicado em {_format_date(bid_data.get("data_publicacao"))}'
        )
    if bid_data.get("link"):
        link = _sanitize(bid_data["link"])
        source_parts.append(f'<link href="{link}">{link}</link>')

    story.append(Spacer(1, 4 * mm))
    story.append(
        Paragraph(
            " · ".join(source_parts),
            ParagraphStyle(
                "Source",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7,
                textColor=VIABILITY_GRAY,
                alignment=TA_CENTER,
            ),
        )
    )

    # ------------------------------------------------------------------
    # Build PDF with footer callback
    # ------------------------------------------------------------------
    is_trial = plan_type in ("free_trial", "trial")

    def _add_footer(canvas, doc):
        canvas.saveState()
        if is_trial:
            footer_text = (
                "Gerado com SmartLic Trial — smartlic.tech | Assine para remover esta marca d'água"
            )
        else:
            footer_text = "Gerado por SmartLic — smartlic.tech"

        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#94A3B8"))
        canvas.drawCentredString(
            PAGE_WIDTH / 2,
            1.2 * cm,
            footer_text,
        )
        canvas.restoreState()

    doc.build(story, onFirstPage=_add_footer, onLaterPages=_add_footer)
    return buf.getvalue()
