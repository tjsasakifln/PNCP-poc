"""
Gerador de relatórios PDF profissionais para Diagnóstico de Oportunidades.

Usa reportlab (pure Python, sem dependências C) para gerar PDFs A4
com capa, resumo executivo, tabela de oportunidades e rodapé padrão.

Exemplo de uso:
    >>> from pdf_report import generate_diagnostico_pdf
    >>> buf = generate_diagnostico_pdf(licitacoes, resumo, metadata, client_name="Empresa X")
    >>> with open("diagnostico.pdf", "wb") as f:
    ...     f.write(buf.getvalue())
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Brand colors
# ---------------------------------------------------------------------------
BRAND_DARK_BLUE = colors.HexColor("#1B3A5C")
BRAND_MEDIUM_BLUE = colors.HexColor("#2C5F8A")
BRAND_LIGHT_BLUE = colors.HexColor("#E8F0FE")
BRAND_ACCENT = colors.HexColor("#3B82F6")

VIABILITY_GREEN = colors.HexColor("#16A34A")
VIABILITY_YELLOW = colors.HexColor("#CA8A04")
VIABILITY_RED = colors.HexColor("#DC2626")

TABLE_HEADER_BG = BRAND_DARK_BLUE
TABLE_HEADER_FG = colors.white
TABLE_ALT_ROW = colors.HexColor("#F8FAFC")
TABLE_BORDER = colors.HexColor("#CBD5E1")

# Page dimensions
PAGE_WIDTH, PAGE_HEIGHT = A4  # 595.27 x 841.89 points
MARGIN = 2 * cm

# Regex for illegal control characters (same as excel.py)
ILLEGAL_CHARACTERS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitize(value: Any) -> str:
    """Sanitize a value for PDF text, removing control characters."""
    if value is None:
        return ""
    text = str(value)
    return ILLEGAL_CHARACTERS_RE.sub(" ", text)


def _format_currency(value: float | int | None) -> str:
    """Format a number as Brazilian currency: R$ 1.234.567,89"""
    if value is None:
        return "N/I"
    try:
        v = float(value)
    except (ValueError, TypeError):
        return "N/I"
    if v == 0:
        return "R$ 0,00"
    # Format with 2 decimals, then swap separators for Brazilian format
    formatted = f"{v:,.2f}"  # e.g. "1,234,567.89"
    # Swap . and , via intermediate placeholder
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def _format_currency_short(value: float | int | None) -> str:
    """Format currency in short form: R$ 1,2M or R$ 450K."""
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
    return _format_currency(v)


def _format_date(value: str | None) -> str:
    """Parse ISO date string and format as DD/MM/YYYY."""
    if not value:
        return "N/I"
    text = str(value).strip()
    # Try common formats
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z",
                "%d/%m/%Y"):
        try:
            dt = datetime.strptime(text[:26].rstrip("Z"), fmt.rstrip("%z"))
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            continue
    # Already in DD/MM/YYYY?
    if re.match(r"\d{2}/\d{2}/\d{4}", text):
        return text[:10]
    return text[:10] if len(text) >= 10 else text


def _today_br() -> str:
    """Return today's date in DD/MM/YYYY format (UTC)."""
    return datetime.now(timezone.utc).strftime("%d/%m/%Y")


def _truncate(text: str, max_len: int = 100) -> str:
    """Truncate text to max_len characters, adding ellipsis if needed."""
    text = _sanitize(text)
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def _safe_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to int."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# Custom styles
# ---------------------------------------------------------------------------

def _build_styles() -> dict[str, ParagraphStyle]:
    """Build the custom paragraph styles for the report."""
    base = getSampleStyleSheet()

    styles: dict[str, ParagraphStyle] = {}

    # Cover page styles
    styles["cover_brand"] = ParagraphStyle(
        "cover_brand",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=28,
        textColor=BRAND_DARK_BLUE,
        alignment=TA_CENTER,
        spaceAfter=8 * mm,
    )
    styles["cover_title"] = ParagraphStyle(
        "cover_title",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=BRAND_DARK_BLUE,
        alignment=TA_CENTER,
        leading=26,
        spaceAfter=6 * mm,
    )
    styles["cover_subtitle"] = ParagraphStyle(
        "cover_subtitle",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=14,
        textColor=BRAND_MEDIUM_BLUE,
        alignment=TA_CENTER,
        spaceAfter=4 * mm,
    )
    styles["cover_info"] = ParagraphStyle(
        "cover_info",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=11,
        textColor=colors.HexColor("#475569"),
        alignment=TA_CENTER,
        leading=16,
        spaceAfter=3 * mm,
    )

    # Section headings
    styles["h1"] = ParagraphStyle(
        "h1_custom",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=BRAND_DARK_BLUE,
        spaceBefore=6 * mm,
        spaceAfter=4 * mm,
        borderWidth=0,
        borderPadding=0,
    )
    styles["h2"] = ParagraphStyle(
        "h2_custom",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=BRAND_MEDIUM_BLUE,
        spaceBefore=4 * mm,
        spaceAfter=3 * mm,
    )

    # Body text
    styles["body"] = ParagraphStyle(
        "body_custom",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#1E293B"),
        alignment=TA_JUSTIFY,
        leading=14,
        spaceAfter=2 * mm,
    )
    styles["body_small"] = ParagraphStyle(
        "body_small",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#475569"),
        leading=12,
        spaceAfter=1.5 * mm,
    )

    # Metric box value
    styles["metric_value"] = ParagraphStyle(
        "metric_value",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=BRAND_DARK_BLUE,
        alignment=TA_CENTER,
        leading=20,
    )
    styles["metric_label"] = ParagraphStyle(
        "metric_label",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.HexColor("#64748B"),
        alignment=TA_CENTER,
        leading=10,
    )

    # Table cell styles
    styles["cell"] = ParagraphStyle(
        "cell",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.HexColor("#1E293B"),
        leading=10,
        alignment=TA_LEFT,
    )
    styles["cell_center"] = ParagraphStyle(
        "cell_center",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.HexColor("#1E293B"),
        leading=10,
        alignment=TA_CENTER,
    )
    styles["cell_right"] = ParagraphStyle(
        "cell_right",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.HexColor("#1E293B"),
        leading=10,
        alignment=TA_RIGHT,
    )
    styles["cell_header"] = ParagraphStyle(
        "cell_header",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=TABLE_HEADER_FG,
        leading=10,
        alignment=TA_CENTER,
    )

    # Bullet / list item
    styles["bullet"] = ParagraphStyle(
        "bullet",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#1E293B"),
        leading=14,
        leftIndent=10,
        spaceAfter=1.5 * mm,
        bulletIndent=0,
        bulletFontName="Helvetica",
        bulletFontSize=10,
    )

    # Footer
    styles["footer"] = ParagraphStyle(
        "footer_style",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=7,
        textColor=colors.HexColor("#94A3B8"),
        alignment=TA_CENTER,
        leading=9,
    )

    return styles


# ---------------------------------------------------------------------------
# Footer callback
# ---------------------------------------------------------------------------

class _FooterCanvas:
    """Manages page numbering and footer text on every page."""

    def __init__(self, generation_date: str):
        self.generation_date = generation_date
        self._pages: list = []

    def on_page(self, canvas, doc):
        """Called on each page to draw footer."""
        canvas.saveState()
        page_num = doc.page  # noqa: F841

        # Footer line
        y = MARGIN - 10 * mm
        canvas.setStrokeColor(TABLE_BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, y + 4 * mm, PAGE_WIDTH - MARGIN, y + 4 * mm)

        # Footer text
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#94A3B8"))

        line1 = f"Gerado por SmartLic (smartlic.tech) em {self.generation_date}"
        line2 = "Este relat\u00f3rio \u00e9 uma an\u00e1lise automatizada e n\u00e3o constitui consultoria jur\u00eddica"

        canvas.drawCentredString(PAGE_WIDTH / 2, y + 1.5 * mm, line1)
        canvas.drawCentredString(PAGE_WIDTH / 2, y - 2 * mm, line2)

        canvas.restoreState()

    def on_page_later(self, canvas, doc):
        """Same footer on subsequent pages, with page number."""
        self.on_page(canvas, doc)

    def add_page_numbers(self, canvas, doc):
        """Second-pass: add 'Pagina X de Y' to every page."""
        canvas.saveState()
        y = MARGIN - 10 * mm
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#94A3B8"))
        text = f"P\u00e1gina {doc.page}"
        canvas.drawRightString(PAGE_WIDTH - MARGIN, y - 2 * mm, text)
        canvas.restoreState()


class _NumberedCanvas:
    """Canvas wrapper that tracks total page count for 'Page X of Y'."""

    def __init__(self, generation_date: str):
        self.generation_date = generation_date

    def __call__(self, canvas, doc):
        """Draw footer on every page."""
        canvas.saveState()

        y = MARGIN - 10 * mm
        canvas.setStrokeColor(TABLE_BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, y + 4 * mm, PAGE_WIDTH - MARGIN, y + 4 * mm)

        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#94A3B8"))

        line1 = f"Gerado por SmartLic (smartlic.tech) em {self.generation_date}"
        line2 = "Este relat\u00f3rio \u00e9 uma an\u00e1lise automatizada e n\u00e3o constitui consultoria jur\u00eddica"

        canvas.drawCentredString(PAGE_WIDTH / 2, y + 1.5 * mm, line1)
        canvas.drawCentredString(PAGE_WIDTH / 2, y - 2 * mm, line2)

        # Page number on the right
        page_text = f"P\u00e1gina {doc.page}"
        canvas.drawRightString(PAGE_WIDTH - MARGIN, y - 2 * mm, page_text)

        canvas.restoreState()


# ---------------------------------------------------------------------------
# Page builders
# ---------------------------------------------------------------------------

def _build_cover(
    styles: dict[str, ParagraphStyle],
    search_metadata: dict,
    client_name: str | None,
    generation_date: str,
) -> list:
    """Build the cover page flowables."""
    elements: list = []

    # Vertical spacer to push content down
    elements.append(Spacer(1, 60 * mm))

    # Brand name
    elements.append(Paragraph("SmartLic.tech", styles["cover_brand"]))
    elements.append(Spacer(1, 4 * mm))

    # Decorative line
    line_data = [["", ""]]
    line_table = Table(line_data, colWidths=[PAGE_WIDTH / 2 - MARGIN])
    line_table.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (0, 0), 2, BRAND_ACCENT),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 8 * mm))

    # Title
    elements.append(
        Paragraph(
            "Diagn\u00f3stico de Oportunidades<br/>em Licita\u00e7\u00f5es",
            styles["cover_title"],
        )
    )

    # Subtitle: client name
    if client_name:
        elements.append(
            Paragraph(f"Preparado para <b>{_sanitize(client_name)}</b>", styles["cover_subtitle"])
        )
    elements.append(Spacer(1, 10 * mm))

    # Metadata info block
    setor = _sanitize(search_metadata.get("setor_name", "N/I"))
    ufs = search_metadata.get("ufs", [])
    ufs_text = ", ".join(ufs) if ufs else "Todas"
    date_from = _format_date(search_metadata.get("date_from"))
    date_to = _format_date(search_metadata.get("date_to"))

    info_lines = [
        f"<b>Setor:</b> {setor}",
        f"<b>Per\u00edodo:</b> {date_from} a {date_to}",
        f"<b>UFs analisadas:</b> {ufs_text}",
        f"<b>Data de gera\u00e7\u00e3o:</b> {generation_date}",
    ]
    for line in info_lines:
        elements.append(Paragraph(line, styles["cover_info"]))

    elements.append(PageBreak())
    return elements


def _build_executive_summary(
    styles: dict[str, ParagraphStyle],
    licitacoes: list[dict],
    resumo: dict,
    search_metadata: dict,
) -> list:
    """Build the executive summary page."""
    elements: list = []

    elements.append(Paragraph("Resumo Executivo", styles["h1"]))
    elements.append(Spacer(1, 2 * mm))

    # AI summary text
    exec_summary = _sanitize(resumo.get("resumo_executivo", ""))
    if exec_summary:
        elements.append(Paragraph(exec_summary, styles["body"]))
        elements.append(Spacer(1, 4 * mm))

    # --- Key metrics boxes ---
    total_found = _safe_int(search_metadata.get("total_raw", len(licitacoes)))
    total_filtered = len(licitacoes)
    values = [_safe_float(lic.get("valor")) for lic in licitacoes if lic.get("valor")]
    valor_total = sum(values) if values else _safe_float(resumo.get("valor_total", 0))
    avg_value = valor_total / len(values) if values else 0

    metric_data = [
        [
            _metric_cell(str(total_found), "Total Encontradas", styles),
            _metric_cell(str(total_filtered), "Total Filtradas", styles),
            _metric_cell(_format_currency_short(valor_total), "Valor Total", styles),
            _metric_cell(_format_currency_short(avg_value), "Valor M\u00e9dio", styles),
        ]
    ]

    avail_width = PAGE_WIDTH - 2 * MARGIN
    col_w = avail_width / 4
    metric_table = Table(metric_data, colWidths=[col_w] * 4, rowHeights=[22 * mm])
    metric_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_LIGHT_BLUE),
        ("BOX", (0, 0), (0, 0), 0.5, TABLE_BORDER),
        ("BOX", (1, 0), (1, 0), 0.5, TABLE_BORDER),
        ("BOX", (2, 0), (2, 0), 0.5, TABLE_BORDER),
        ("BOX", (3, 0), (3, 0), 0.5, TABLE_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(metric_table)
    elements.append(Spacer(1, 6 * mm))

    # --- Distribution by UF ---
    uf_counts: dict[str, int] = {}
    for lic in licitacoes:
        uf = lic.get("uf", "N/I")
        if uf:
            uf_counts[uf] = uf_counts.get(uf, 0) + 1

    if uf_counts:
        elements.append(Paragraph("Distribui\u00e7\u00e3o por UF (Top 5)", styles["h2"]))
        sorted_ufs = sorted(uf_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        uf_header = [
            Paragraph("<b>UF</b>", styles["cell_header"]),
            Paragraph("<b>Quantidade</b>", styles["cell_header"]),
            Paragraph("<b>%</b>", styles["cell_header"]),
        ]
        uf_rows = [uf_header]
        for uf, count in sorted_ufs:
            pct = (count / total_filtered * 100) if total_filtered > 0 else 0
            uf_rows.append([
                Paragraph(uf, styles["cell_center"]),
                Paragraph(str(count), styles["cell_center"]),
                Paragraph(f"{pct:.1f}%", styles["cell_center"]),
            ])

        uf_table = Table(uf_rows, colWidths=[avail_width * 0.3, avail_width * 0.35, avail_width * 0.35])
        uf_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), TABLE_HEADER_FG),
            ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ] + [
            ("BACKGROUND", (0, i), (-1, i), TABLE_ALT_ROW)
            for i in range(2, len(uf_rows), 2)
        ]))
        elements.append(uf_table)
        elements.append(Spacer(1, 4 * mm))

    # --- Distribution by modality ---
    mod_counts: dict[str, int] = {}
    for lic in licitacoes:
        mod = _sanitize(lic.get("modalidade", "N/I")) or "N/I"
        mod_counts[mod] = mod_counts.get(mod, 0) + 1

    if mod_counts:
        elements.append(Paragraph("Distribui\u00e7\u00e3o por Modalidade", styles["h2"]))
        sorted_mods = sorted(mod_counts.items(), key=lambda x: x[1], reverse=True)

        mod_header = [
            Paragraph("<b>Modalidade</b>", styles["cell_header"]),
            Paragraph("<b>Quantidade</b>", styles["cell_header"]),
            Paragraph("<b>%</b>", styles["cell_header"]),
        ]
        mod_rows = [mod_header]
        for mod, count in sorted_mods:
            pct = (count / total_filtered * 100) if total_filtered > 0 else 0
            mod_rows.append([
                Paragraph(_truncate(mod, 50), styles["cell"]),
                Paragraph(str(count), styles["cell_center"]),
                Paragraph(f"{pct:.1f}%", styles["cell_center"]),
            ])

        mod_table = Table(mod_rows, colWidths=[avail_width * 0.5, avail_width * 0.25, avail_width * 0.25])
        mod_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), TABLE_HEADER_FG),
            ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ] + [
            ("BACKGROUND", (0, i), (-1, i), TABLE_ALT_ROW)
            for i in range(2, len(mod_rows), 2)
        ]))
        elements.append(mod_table)
        elements.append(Spacer(1, 4 * mm))

    # --- Viability summary line ---
    high_viability = sum(
        1 for lic in licitacoes
        if _safe_int(lic.get("_viability_score")) > 70
    )
    if total_filtered > 0:
        elements.append(
            Paragraph(
                f"Das <b>{total_filtered}</b> oportunidades, "
                f"<b>{high_viability}</b> t\u00eam score de viabilidade acima de 70%.",
                styles["body"],
            )
        )
        elements.append(Spacer(1, 3 * mm))

    # --- Destaques ---
    destaques = resumo.get("destaques", [])
    if destaques:
        elements.append(Paragraph("Destaques", styles["h2"]))
        for item in destaques:
            text = _sanitize(item)
            if text:
                elements.append(
                    Paragraph(f"\u2022 {text}", styles["bullet"])
                )
        elements.append(Spacer(1, 3 * mm))

    # --- Recomendacoes ---
    recomendacoes = resumo.get("recomendacoes", [])
    if recomendacoes:
        elements.append(Paragraph("Recomenda\u00e7\u00f5es", styles["h2"]))
        for rec in recomendacoes:
            if isinstance(rec, dict):
                text = _sanitize(rec.get("oportunidade", ""))
                acao = _sanitize(rec.get("acao", ""))
                if text:
                    line = f"\u2022 <b>{text}</b>"
                    if acao:
                        line += f" \u2014 {acao}"
                    elements.append(Paragraph(line, styles["bullet"]))
            elif isinstance(rec, str):
                elements.append(Paragraph(f"\u2022 {_sanitize(rec)}", styles["bullet"]))

    elements.append(PageBreak())
    return elements


def _metric_cell(value: str, label: str, styles: dict[str, ParagraphStyle]) -> list:
    """Build a metric cell as a list of paragraphs (for nesting in Table)."""
    # We return a list wrapped in a small inner Table for vertical centering
    inner_data = [
        [Paragraph(value, styles["metric_value"])],
        [Paragraph(label, styles["metric_label"])],
    ]
    inner = Table(inner_data, colWidths=["*"])
    inner.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))
    return inner


def _build_opportunities_table(
    styles: dict[str, ParagraphStyle],
    licitacoes: list[dict],
    max_items: int,
) -> list:
    """Build the Top N opportunities table pages."""
    elements: list = []

    # Sort by viability score descending
    sorted_lics = sorted(
        licitacoes,
        key=lambda x: _safe_int(x.get("_viability_score")),
        reverse=True,
    )
    display_lics = sorted_lics[:max_items]
    actual_count = len(display_lics)

    if actual_count == 0:
        elements.append(Paragraph("Oportunidades", styles["h1"]))
        elements.append(Paragraph("Nenhuma oportunidade encontrada para os crit\u00e9rios informados.", styles["body"]))
        return elements

    elements.append(
        Paragraph(
            f"Top {actual_count} Oportunidades por Viabilidade",
            styles["h1"],
        )
    )
    elements.append(Spacer(1, 2 * mm))

    # Table header
    avail_width = PAGE_WIDTH - 2 * MARGIN
    col_widths = [
        avail_width * 0.04,   # #
        avail_width * 0.28,   # Titulo
        avail_width * 0.18,   # Orgao
        avail_width * 0.05,   # UF
        avail_width * 0.14,   # Valor
        avail_width * 0.14,   # Modalidade
        avail_width * 0.08,   # Prazo
        avail_width * 0.09,   # Score
    ]

    header = [
        Paragraph("<b>#</b>", styles["cell_header"]),
        Paragraph("<b>T\u00edtulo</b>", styles["cell_header"]),
        Paragraph("<b>\u00d3rg\u00e3o</b>", styles["cell_header"]),
        Paragraph("<b>UF</b>", styles["cell_header"]),
        Paragraph("<b>Valor (R$)</b>", styles["cell_header"]),
        Paragraph("<b>Modalidade</b>", styles["cell_header"]),
        Paragraph("<b>Prazo</b>", styles["cell_header"]),
        Paragraph("<b>Score</b>", styles["cell_header"]),
    ]
    rows = [header]

    # Build conditional style commands for viability coloring
    viability_styles: list[tuple] = []  # noqa: F841

    for idx, lic in enumerate(display_lics, 1):
        score = _safe_int(lic.get("_viability_score"))
        level = lic.get("_viability_level", "")  # noqa: F841

        # Determine score display color
        if score > 70:
            score_color = VIABILITY_GREEN
        elif score >= 40:
            score_color = VIABILITY_YELLOW
        else:
            score_color = VIABILITY_RED

        score_style = ParagraphStyle(
            f"score_{idx}",
            parent=styles["cell_center"],
            fontName="Helvetica-Bold",
            textColor=score_color,
        )

        # Prazo (days remaining)
        dias = lic.get("dias_restantes")
        if dias is not None:
            prazo_text = f"{_safe_int(dias)}d"
        else:
            # Try to compute from data_encerramento
            prazo_text = "N/I"

        row = [
            Paragraph(str(idx), styles["cell_center"]),
            Paragraph(_truncate(lic.get("objeto", ""), 100), styles["cell"]),
            Paragraph(_truncate(lic.get("orgao", ""), 60), styles["cell"]),
            Paragraph(_sanitize(lic.get("uf", "")), styles["cell_center"]),
            Paragraph(_format_currency(_safe_float(lic.get("valor"))), styles["cell_right"]),
            Paragraph(_truncate(lic.get("modalidade", ""), 30), styles["cell"]),
            Paragraph(prazo_text, styles["cell_center"]),
            Paragraph(f"{score}%" if score > 0 else "N/I", score_style),
        ]
        rows.append(row)

    table = Table(rows, colWidths=col_widths, repeatRows=1)

    # Base table style
    base_styles = [
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), TABLE_HEADER_FG),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        # Alignment
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Padding
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]

    # Alternating row backgrounds
    for i in range(2, len(rows), 2):
        base_styles.append(("BACKGROUND", (0, i), (-1, i), TABLE_ALT_ROW))

    table.setStyle(TableStyle(base_styles))
    elements.append(table)

    # Note if truncated
    if len(sorted_lics) > max_items:
        elements.append(Spacer(1, 3 * mm))
        elements.append(
            Paragraph(
                f"<i>Exibindo as {max_items} melhores de {len(sorted_lics)} oportunidades totais. "
                f"Acesse smartlic.tech para a lista completa.</i>",
                styles["body_small"],
            )
        )

    return elements


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def generate_diagnostico_pdf(
    licitacoes: list[dict],
    resumo: dict,
    search_metadata: dict,
    client_name: str | None = None,
    max_items: int = 20,
) -> BytesIO:
    """
    Generate a professional PDF report for "Diagnostico de Oportunidades".

    Args:
        licitacoes: List of bid dicts with keys: objeto, orgao, uf, valor,
            modalidade, data_abertura, data_encerramento, dias_restantes, link,
            _viability_score (optional), _viability_level (optional).
        resumo: Dict with: resumo_executivo, total_oportunidades, valor_total,
            destaques (list), recomendacoes (list).
        search_metadata: Dict with: setor_name, ufs (list), date_from, date_to,
            total_raw.
        client_name: Optional company name for the cover page.
        max_items: How many top opportunities to show (default 20).

    Returns:
        BytesIO buffer containing the generated PDF.
    """
    # Ensure inputs are safe
    if not isinstance(licitacoes, list):
        licitacoes = []
    if not isinstance(resumo, dict):
        resumo = {}
    if not isinstance(search_metadata, dict):
        search_metadata = {}
    max_items = max(1, min(max_items, 100))

    generation_date = _today_br()
    styles = _build_styles()

    buffer = BytesIO()

    # Build the document
    setor = _sanitize(search_metadata.get("setor_name", ""))
    doc_title = f"Diagn\u00f3stico de Oportunidades \u2014 {setor} \u2014 {generation_date}" if setor else f"Diagn\u00f3stico de Oportunidades \u2014 {generation_date}"

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN + 8 * mm,  # Extra space for footer
        title=doc_title,
        author="SmartLic",
        creator="SmartLic v0.5",
    )

    # Footer handler
    footer_handler = _NumberedCanvas(generation_date)

    # Assemble all flowables
    elements: list = []

    # Page 1: Cover
    elements.extend(_build_cover(styles, search_metadata, client_name, generation_date))

    # Page 2: Executive Summary
    elements.extend(_build_executive_summary(styles, licitacoes, resumo, search_metadata))

    # Pages 3+: Opportunities Table
    elements.extend(_build_opportunities_table(styles, licitacoes, max_items))

    # Build the PDF
    doc.build(
        elements,
        onFirstPage=footer_handler,
        onLaterPages=footer_handler,
    )

    buffer.seek(0)
    return buffer
