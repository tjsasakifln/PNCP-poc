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

# Risk score gradient colors
RISK_LOW = colors.HexColor("#DC2626")      # 0-30 red
RISK_MED = colors.HexColor("#F59E0B")      # 30-60 amber
RISK_HIGH = colors.HexColor("#16A34A")     # 60-100 green

# Metric card backgrounds
CARD_GREEN_BG = colors.HexColor("#F0FDF4")
CARD_YELLOW_BG = colors.HexColor("#FEFCE8")
CARD_RED_BG = colors.HexColor("#FEF2F2")
CARD_BLUE_BG = colors.HexColor("#EFF6FF")

# Section divider accent
ACCENT_LINE_COLOR = colors.HexColor("#3B82F6")

TABLE_HEADER_BG = BRAND_PRIMARY
TABLE_HEADER_FG = colors.white
TABLE_ALT_ROW = colors.HexColor("#F8FAFC")
TABLE_BORDER = colors.HexColor("#CBD5E1")

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 2 * cm

ILLEGAL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

# ============================================================
# ACCENT RESTORATION (API data often lacks PT-BR diacritics)
# ============================================================
_ACCENT_MAP = {
    "construcao": "construção", "construcoes": "construções",
    "licitacao": "licitação", "licitacoes": "licitações",
    "contratacao": "contratação", "contratacoes": "contratações",
    "pavimentacao": "pavimentação", "habitacao": "habitação",
    "edificacao": "edificação", "edificacoes": "edificações",
    "ampliacao": "ampliação", "revitalizacao": "revitalização",
    "execucao": "execução", "manutencao": "manutenção",
    "atencao": "atenção", "educacao": "educação",
    "implantacao": "implantação", "instalacao": "instalação",
    "instalacoes": "instalações", "fundacao": "fundação",
    "recreacao": "recreação", "recuperacao": "recuperação",
    "reabilitacao": "reabilitação", "fiscalizacao": "fiscalização",
    "sinalizacao": "sinalização", "urbanizacao": "urbanização",
    "impermeabilizacao": "impermeabilização",
    "adequacao": "adequação", "adequacoes": "adequações",
    "operacao": "operação", "operacoes": "operações",
    "medicao": "medição", "medicoes": "medições",
    "informacao": "informação", "informacoes": "informações",
    "situacao": "situação", "avaliacao": "avaliação",
    "qualificacao": "qualificação", "habilitacao": "habilitação",
    "documentacao": "documentação", "certificacao": "certificação",
    "certificacoes": "certificações", "restricao": "restrição",
    "restricoes": "restrições", "sancao": "sanção", "sancoes": "sanções",
    "pregao": "pregão", "concorrencia": "concorrência",
    "eletronica": "eletrônica", "eletronicas": "eletrônicas",
    "eletrica": "elétrica", "eletricas": "elétricas",
    "tecnico": "técnico", "tecnica": "técnica",
    "tecnicas": "técnicas", "tecnicos": "técnicos",
    "economico": "econômico", "economica": "econômica",
    "municipio": "município", "municipios": "municípios",
    "orgao": "órgão", "orgaos": "órgãos",
    "publico": "público", "publica": "pública",
    "publicos": "públicos", "publicas": "públicas",
    "indice": "índice", "indices": "índices",
    "area": "área", "areas": "áreas",
    "agua": "água", "aguas": "águas",
    "analise": "análise", "analises": "análises",
    "registro": "registro", "minimo": "mínimo", "minima": "mínima",
    "maximo": "máximo", "maxima": "máxima",
    "necessario": "necessário", "necessaria": "necessária",
    "necessarios": "necessários", "necessarias": "necessárias",
    "especifico": "específico", "especifica": "específica",
    "especificos": "específicos", "historico": "histórico",
    "historica": "histórica", "obrigatorio": "obrigatório",
    "obrigatoria": "obrigatória", "provisorio": "provisório",
    "viavel": "viável", "responsavel": "responsável",
    "compativel": "compatível", "acessivel": "acessível",
    "gerenciavel": "gerenciável", "possivel": "possível",
    "impossivel": "impossível", "provavel": "provável",
    "disponivel": "disponível",
    "nao": "não", "ja": "já", "tambem": "também",
    "ate": "até", "apos": "após", "so": "só",
    # NOTE: "e" → "é" REMOVED — too ambiguous (conjunction vs verb)
    # NOTE: "nos" → "nós" REMOVED — too ambiguous (preposition vs pronoun)
    "sera": "será", "serao": "serão",
    "voce": "você",
    "recomendacao": "recomendação",
    "preco": "preço", "precos": "preços",
    "orcamento": "orçamento", "orcamentos": "orçamentos",
    "orcado": "orçado", "servico": "serviço", "servicos": "serviços",
    "acervo": "acervo", "sessao": "sessão",
    "competicao": "competição", "competicoes": "competições",
    "reputacao": "reputação", "precificacao": "precificação",
    "associacao": "associação",
    "vigencia": "vigência", "exigencia": "exigência",
    "exigencias": "exigências", "frequencia": "frequência",
    "discrepancia": "discrepância",
    "pratica": "prática", "praticas": "práticas",
    "ceramico": "cerâmico", "ceramica": "cerâmica",
    "metalica": "metálica", "metalico": "metálico",
    "termoacustico": "termoacústico",
    "logistica": "logística", "basica": "básica",
    "estrategia": "estratégia",
}

# Build regex — match whole words, case-insensitive
_ACCENT_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in sorted(_ACCENT_MAP.keys(), key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def _restore_accents(text: str) -> str:
    """Restore PT-BR diacritics to unaccented text from APIs."""
    if not text:
        return text

    def _replace(m: re.Match) -> str:
        word = m.group(0)
        lower = word.lower()
        replacement = _ACCENT_MAP.get(lower, word)
        # Preserve original casing pattern
        if word.isupper():
            return replacement.upper()
        if word[0].isupper():
            return replacement[0].upper() + replacement[1:]
        return replacement

    return _ACCENT_PATTERN.sub(_replace, text)


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


def _validate_json(data: dict) -> tuple[list[str], list[str]]:
    """Validate the input JSON. Returns (warnings, errors).

    Errors are blocking — PDF generation MUST NOT proceed if errors exist.
    """
    warnings = []
    errors = []
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
        # Justificativa é OBRIGATÓRIA para toda recomendação (ERRO BLOQUEANTE)
        rec = (ed.get("recomendacao") or "").upper()
        status = ed.get("status_edital", "")
        if rec and status != "ENCERRADO" and not ed.get("justificativa"):
            errors.append(
                f"edital[{i}].justificativa ausente — recomendação '{rec}' "
                f"para \"{(ed.get('objeto') or 'sem título')[:60]}\" não tem fundamentação"
            )
    if warnings:
        print(f"⚠ Validação JSON: {len(warnings)} avisos")
        for w in warnings[:10]:
            print(f"  - {w}")
    if errors:
        print(f"\n❌ Validação JSON: {len(errors)} ERROS BLOQUEANTES")
        for e in errors:
            print(f"  - {e}")
    return warnings, errors


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
    text = ILLEGAL_CHARS_RE.sub(" ", str(value))
    return _restore_accents(text)


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


def _format_dias_restantes(dias: Any) -> str:
    """Format remaining days for human display."""
    if dias is None or dias == "None":
        return "N/D"
    d = _safe_int(dias)
    if d < 0:
        return f"Encerrado ({abs(d)}d atrás)"
    if d == 0:
        return "Hoje"
    if d == 1:
        return "Amanhã"
    return f"{d} dias"


def _format_prazo_short(dias: Any) -> str:
    """Format days for table column (compact)."""
    if dias is None or dias == "None":
        return "—"
    d = _safe_int(dias)
    if d < 0:
        return f"Enc."
    if d == 0:
        return "Hoje"
    return f"{d}d"


def _collapse_cnaes(cnaes: Any, max_show: int = 5) -> str:
    """Collapse long CNAE lists into readable format."""
    if not cnaes:
        return ""
    if isinstance(cnaes, str):
        parts = [c.strip() for c in cnaes.replace(";", ",").split(",") if c.strip()]
    elif isinstance(cnaes, list):
        parts = [str(c).strip() for c in cnaes if c]
    else:
        return str(cnaes)
    if len(parts) <= max_show:
        return ", ".join(parts)
    shown = ", ".join(parts[:max_show])
    return f"{shown} (e mais {len(parts) - max_show})"


# ============================================================
# SECTION DIVIDER HELPER
# ============================================================

def _section_divider() -> Table:
    """Create a thin accent-colored horizontal divider between sections."""
    t = Table([[""]],  colWidths=[PAGE_WIDTH - 2 * MARGIN], rowHeights=[1])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (0, 0), 1.5, ACCENT_LINE_COLOR),
        ("TOPPADDING", (0, 0), (0, 0), 0),
        ("BOTTOMPADDING", (0, 0), (0, 0), 0),
    ]))
    return t


def _section_heading(title: str, styles: dict) -> list:
    """Create section heading elements that stay together (never orphaned at page bottom).

    Returns a list of flowables: [divider, spacer, heading].
    The heading has keepWithNext=True so it always has content below it on the same page.
    """
    divider = _section_divider()
    divider.keepWithNext = True
    h = Paragraph(title, styles["h1"])
    h.keepWithNext = True
    return [divider, Spacer(1, 2 * mm), h]


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

    # Premium: decision table semaphore
    s["semaphore_green"] = ParagraphStyle(
        "sem_g", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=9, textColor=GREEN,
        alignment=TA_CENTER, leading=11,
    )
    s["semaphore_yellow"] = ParagraphStyle(
        "sem_y", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=9, textColor=YELLOW,
        alignment=TA_CENTER, leading=11,
    )
    s["semaphore_red"] = ParagraphStyle(
        "sem_r", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=9, textColor=RED,
        alignment=TA_CENTER, leading=11,
    )
    # Premium: card value large
    s["card_value_large"] = ParagraphStyle(
        "cvl", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=20, textColor=BRAND_PRIMARY,
        alignment=TA_CENTER, leading=24,
    )
    s["card_label_small"] = ParagraphStyle(
        "cls", parent=base["Normal"],
        fontName="Helvetica", fontSize=7, textColor=colors.HexColor("#64748B"),
        alignment=TA_CENTER, leading=9,
    )
    # Premium: chronogram
    s["chrono_status_ok"] = ParagraphStyle(
        "cs_ok", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=8, textColor=GREEN,
        alignment=TA_CENTER, leading=10,
    )
    s["chrono_status_warn"] = ParagraphStyle(
        "cs_warn", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=8, textColor=ORANGE,
        alignment=TA_CENTER, leading=10,
    )
    s["chrono_status_late"] = ParagraphStyle(
        "cs_late", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=8, textColor=RED,
        alignment=TA_CENTER, leading=10,
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


def _build_decision_table(data: dict, styles: dict, sec: dict) -> list:
    """Build 'Decisão em 30 Segundos' — traffic-light summary table on page 2.

    Redesigned: wider justificativa, merged semáforo+objeto, readable layout.
    """
    el = []
    editais = data.get("editais", [])
    if not editais:
        return el

    num = sec["next"]()
    el.extend(_section_heading(f"{num}. Decisão em 30 Segundos", styles))
    el.append(Paragraph(
        "Visão semáforo: <font color='#16A34A'><b>●</b></font> Participar  "
        "<font color='#CA8A04'><b>●</b></font> Avaliar  "
        "<font color='#DC2626'><b>●</b></font> Não recomendado",
        styles["body_small"],
    ))
    el.append(Spacer(1, 3 * mm))

    avail = PAGE_WIDTH - 2 * MARGIN

    # One card per edital — more readable than a cramped table
    for idx, ed in enumerate(editais, 1):
        rec = _normalize_recommendation(_s(ed.get("recomendacao", "")))
        risk = ed.get("risk_score", {})
        score_val = _safe_int(risk.get("total") if isinstance(risk, dict) else risk)

        # Semaphore color
        if rec == "PARTICIPAR":
            sem_color = GREEN
            sem_bg = CARD_GREEN_BG
            border_color = GREEN
        elif "CAUTELA" in rec or "AVALIAR" in rec:
            sem_color = YELLOW
            sem_bg = CARD_YELLOW_BG
            border_color = YELLOW
        else:
            sem_color = RED
            sem_bg = CARD_RED_BG
            border_color = RED

        objeto = _s(ed.get("objeto", ""))
        valor = _currency_short(ed.get("valor_estimado"))
        prazo = _format_prazo_short(ed.get("dias_restantes"))
        justif = _s(ed.get("justificativa", ""))

        # Row 1: semáforo + objeto + valor + prazo
        sem_style = ParagraphStyle(
            f"dsem_{idx}", fontName="Helvetica-Bold", fontSize=12,
            textColor=sem_color, alignment=TA_CENTER, leading=14,
        )
        rec_style = ParagraphStyle(
            f"drec_{idx}", fontName="Helvetica-Bold", fontSize=8,
            textColor=sem_color, alignment=TA_CENTER, leading=10,
        )

        row1 = [
            Paragraph("●", sem_style),
            Paragraph(f"<b>{idx}. {_trunc(objeto, 140)}</b>", styles["cell"]),
            Paragraph(valor, ParagraphStyle(
                f"dval_{idx}", parent=styles["cell_right"],
                fontName="Helvetica-Bold", fontSize=9,
            )),
            Paragraph(prazo, styles["cell_center"]),
            Paragraph(rec.replace("NÃO RECOMENDADO", "NÃO REC."), rec_style),
        ]

        card_data = [row1]
        col_w = [avail * 0.05, avail * 0.48, avail * 0.15, avail * 0.10, avail * 0.22]

        # Row 2: justificativa (spans full width)
        if justif:
            just_para = Paragraph(
                f"<font color='#475569' size='7'>{_trunc(justif, 250)}</font>",
                styles["cell"],
            )
            card_data.append(["", just_para, "", "", ""])

        t = Table(card_data, colWidths=col_w)
        card_styles = [
            ("BACKGROUND", (0, 0), (-1, -1), sem_bg),
            ("BOX", (0, 0), (-1, -1), 0.75, border_color),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]
        if justif:
            card_styles.append(("SPAN", (1, 1), (4, 1)))
            card_styles.append(("TOPPADDING", (0, 1), (-1, 1), 0))
        t.setStyle(TableStyle(card_styles))
        el.append(KeepTogether([t, Spacer(1, 2 * mm)]))

    el.append(Spacer(1, 4 * mm))
    return el


def _draw_risk_bar(score: int, styles: dict) -> list:
    """Build viability index bar 0-100 with explanation.

    Combines 4 factors: modalidade (30%), prazo (25%), valor (25%), geografia (20%).
    Higher = more viable for this company.
    """
    if score <= 0:
        return []

    avail = PAGE_WIDTH - 2 * MARGIN
    bar_width = avail * 0.6

    if score >= 60:
        bar_color = RISK_HIGH
        label_color = "#16A34A"
        qualif = "Alta"
    elif score >= 30:
        bar_color = RISK_MED
        label_color = "#F59E0B"
        qualif = "Moderada"
    else:
        bar_color = RISK_LOW
        label_color = "#DC2626"
        qualif = "Baixa"

    filled = bar_width * (score / 100)
    empty = bar_width - filled

    label_style = ParagraphStyle(
        "rbl", fontName="Helvetica-Bold", fontSize=8,
        textColor=colors.HexColor("#475569"), leading=10,
    )
    value_style = ParagraphStyle(
        "rbv", fontName="Helvetica-Bold", fontSize=11,
        textColor=colors.HexColor(label_color), leading=14,
    )
    bar_row = [
        Paragraph("Viabilidade", label_style),
        "",  # filled portion
        "",  # empty portion
        Paragraph(f"{score}/100 ({qualif})", value_style),
    ]
    t = Table([bar_row], colWidths=[avail * 0.15, filled, empty, avail * 0.20])
    t.setStyle(TableStyle([
        ("BACKGROUND", (1, 0), (1, 0), bar_color),
        ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#E2E8F0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEABOVE", (1, 0), (2, 0), 0.5, TABLE_BORDER),
        ("LINEBELOW", (1, 0), (2, 0), 0.5, TABLE_BORDER),
    ]))

    el = [t]
    # Brief explanation so the reader knows what this measures
    el.append(Paragraph(
        "<font size='7' color='#64748B'>Índice calculado com base em modalidade (30%), "
        "prazo (25%), valor vs. capacidade (25%) e proximidade geográfica (20%).</font>",
        styles["body_small"],
    ))
    return el


def _build_chronogram_table(cronograma: list, styles: dict) -> list:
    """Build a compact chronogram table for an edital."""
    if not cronograma:
        return []

    el = []
    el.append(Paragraph("<b>Cronograma Reverso</b>", styles["h3"]))

    avail = PAGE_WIDTH - 2 * MARGIN
    header = [Paragraph(f"<b>{h}</b>", styles["cell_header"]) for h in [
        "Data", "Marco", "Status",
    ]]
    rows = [header]

    for item in cronograma:
        data_str = _date(item.get("data", ""))
        marco = _s(item.get("marco", ""))
        status = _s(item.get("status", ""))

        if "atrasado" in status.lower() or "vencido" in status.lower():
            status_style = styles["chrono_status_late"]
        elif "atenção" in status.lower() or "atencao" in status.lower() or "hoje" in status.lower():
            status_style = styles["chrono_status_warn"]
        else:
            status_style = styles["chrono_status_ok"]

        rows.append([
            Paragraph(data_str, styles["cell_center"]),
            Paragraph(marco, styles["cell"]),
            Paragraph(status, status_style),
        ])

    t = Table(rows, colWidths=[avail * 0.20, avail * 0.50, avail * 0.30])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ] + [("BACKGROUND", (0, i), (-1, i), TABLE_ALT_ROW) for i in range(2, len(rows), 2)]))
    el.append(t)
    el.append(Spacer(1, 2 * mm))
    return el


def _build_roi_card(roi: dict, styles: dict) -> list:
    """Build potential revenue card for an edital opportunity."""
    if not roi or not isinstance(roi, dict):
        return []
    roi_min = roi.get("roi_min", 0)
    roi_max = roi.get("roi_max", 0)
    probability = roi.get("probability", 0)
    if roi_max <= 0:
        return []

    el = []
    avail = PAGE_WIDTH - 2 * MARGIN

    roi_text = f"{_currency_short(roi_min)} — {_currency_short(roi_max)}"
    prob_text = f"{probability:.0f}%" if probability else "N/I"

    card_data = [
        [Paragraph("<b>Faturamento Potencial</b>", styles["cell"]),
         Paragraph(roi_text, ParagraphStyle(
             "roi_v", fontName="Helvetica-Bold", fontSize=11,
             textColor=BRAND_PRIMARY, alignment=TA_CENTER, leading=14,
         )),
         Paragraph(f"Chance de vitória: {prob_text}", styles["cell_center"])],
    ]
    t = Table(card_data, colWidths=[avail * 0.25, avail * 0.45, avail * 0.30])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CARD_BLUE_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, BRAND_ACCENT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    el.append(t)
    el.append(Paragraph(
        "<font size='7' color='#64748B'>Estimativa com base no valor do edital, "
        "margem típica do setor e perfil competitivo da empresa.</font>",
        styles["body_small"],
    ))
    el.append(Spacer(1, 2 * mm))
    return el


def _build_competitive_section(data: dict, styles: dict, sec: dict) -> list:
    """Build competitive intelligence section from competitive_intel in editais."""
    # Collect all competitive intel entries across editais
    entries = []
    for ed in data.get("editais", []):
        ci = ed.get("competitive_intel", [])
        if ci:
            orgao = _s(ed.get("orgao", ""))
            for c in ci[:5]:  # max 5 per orgão
                entries.append({
                    "orgao": orgao,
                    "fornecedor": _s(c.get("fornecedor", "")),
                    "objeto": _trunc(_s(c.get("objeto", "")), 60),
                    "valor": c.get("valor"),
                    "data": c.get("data", ""),
                })
    if not entries:
        return []

    el = []
    num = sec["next"]()
    el.extend(_section_heading(f"{num}. Mapa Competitivo", styles))
    el.append(Paragraph(
        "Contratos históricos identificados nos órgãos licitantes — "
        "indica incumbentes e valores praticados.",
        styles["body_small"],
    ))
    el.append(Spacer(1, 3 * mm))

    avail = PAGE_WIDTH - 2 * MARGIN
    header = [Paragraph(f"<b>{h}</b>", styles["cell_header"]) for h in [
        "Órgão", "Fornecedor", "Objeto", "Valor", "Data",
    ]]
    rows = [header]

    # Deduplicate by fornecedor+orgao, keep most recent
    seen = set()
    for e in sorted(entries, key=lambda x: x["data"], reverse=True):
        key = (e["orgao"][:30], e["fornecedor"][:30])
        if key in seen:
            continue
        seen.add(key)
        rows.append([
            Paragraph(_trunc(e["orgao"], 35), styles["cell"]),
            Paragraph(_trunc(e["fornecedor"], 30), styles["cell"]),
            Paragraph(e["objeto"], styles["cell"]),
            Paragraph(_currency_short(e["valor"]), styles["cell_right"]),
            Paragraph(_date(e["data"]), styles["cell_center"]),
        ])
        if len(rows) > 20:  # Cap at 20 rows
            break

    t = Table(rows, colWidths=[
        avail * 0.20, avail * 0.20, avail * 0.30, avail * 0.15, avail * 0.15,
    ], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
    ] + [("BACKGROUND", (0, i), (-1, i), TABLE_ALT_ROW) for i in range(2, len(rows), 2)]))
    el.append(t)

    el.append(Spacer(1, 6 * mm))
    return el


def _section_counter() -> dict:
    """Create a dynamic section counter for auto-numbering."""
    state = {"n": 0}

    def _next() -> int:
        state["n"] += 1
        return state["n"]

    return {"next": _next, "current": lambda: state["n"]}


def _build_company_profile(data: dict, styles: dict, sec: dict | None = None) -> list:
    el = []
    emp = data.get("empresa", {})

    num = sec["next"]() if sec else 1
    el.extend(_section_heading(f"{num}. Perfil da Empresa", styles))

    # Build as structured table for clean alignment
    avail = PAGE_WIDTH - 2 * MARGIN
    info_rows = []

    raw_fields = [
        ("Razão Social", emp.get("razao_social")),
        ("Nome Fantasia", emp.get("nome_fantasia")),
        ("CNPJ", emp.get("cnpj")),
        ("CNAE Principal", emp.get("cnae_principal")),
        ("CNAEs Secundários", _collapse_cnaes(emp.get("cnaes_secundarios"))),
        ("Porte", emp.get("porte")),
        ("Capital Social", _currency(emp.get("capital_social")) if emp.get("capital_social") else None),
        ("Sede", f"{emp.get('cidade_sede', '')} - {emp.get('uf_sede', '')}"),
        ("Situação Cadastral", emp.get("situacao_cadastral")),
    ]
    for label, value in raw_fields:
        if value and str(value).strip() and value != " - ":
            info_rows.append([
                Paragraph(f"<b>{label}</b>", styles["cell"]),
                Paragraph(_s(str(value)), styles["cell"]),
            ])

    if info_rows:
        info_t = Table(info_rows, colWidths=[avail * 0.22, avail * 0.78])
        info_t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
            ("BACKGROUND", (0, 0), (0, -1), BRAND_LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ]))
        el.append(info_t)
        el.append(Spacer(1, 4 * mm))

    # QSA / Decisores
    qsa = emp.get("qsa", [])
    if qsa:
        el.append(Paragraph("<b>Quadro Societário</b>", styles["h3"]))
        for socio in qsa[:5]:
            nome = _s(socio.get("nome", socio) if isinstance(socio, dict) else socio)
            qual = _s(socio.get("qualificacao", "")) if isinstance(socio, dict) else ""
            line = f"• {nome}" + (f" ({qual})" if qual else "")
            el.append(Paragraph(line, styles["bullet"]))
        el.append(Spacer(1, 2 * mm))

    # Sanções — as a visual card
    sancoes = emp.get("sancoes", {})
    if sancoes:
        has_sanction = any(sancoes.get(k) for k in ["ceis", "cnep", "cepim", "ceaf"])
        if has_sanction:
            card_bg = CARD_RED_BG
            card_border = RED
            card_text = "<font color='#DC2626'><b>ATENÇÃO: Empresa possui sanção ativa</b></font>"
            details = []
            for k, label in [("ceis", "CEIS"), ("cnep", "CNEP"), ("cepim", "CEPIM"), ("ceaf", "CEAF")]:
                if sancoes.get(k):
                    details.append(f"<font color='#DC2626'>{label}: Sancionada</font>")
            if details:
                card_text += "<br/>" + " | ".join(details)
        else:
            card_bg = CARD_GREEN_BG
            card_border = GREEN
            card_text = "<font color='#16A34A'><b>Sem sanções ativas</b></font> (CEIS, CNEP, CEPIM, CEAF)"

        sanc_t = Table(
            [[Paragraph(card_text, styles["body"])]],
            colWidths=[avail],
        )
        sanc_t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), card_bg),
            ("BOX", (0, 0), (-1, -1), 0.75, card_border),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        el.append(sanc_t)
        el.append(Spacer(1, 3 * mm))

    # Histórico de contratos governamentais
    historico = emp.get("historico_contratos", [])
    if historico:
        el.append(Paragraph("<b>Histórico de Contratos Governamentais</b>", styles["h3"]))
        valor_hist = sum(_safe_float(c.get("valor")) for c in historico)
        hist_text = f"Total: <b>{len(historico)}</b> contrato(s)"
        if valor_hist > 0:
            hist_text += f" | Valor total: <b>{_currency(valor_hist)}</b>"
        el.append(Paragraph(hist_text, styles["body"]))
    else:
        el.append(Paragraph(
            "<font color='#CA8A04'><b>Sem histórico de contratos governamentais federais</b></font>",
            styles["body"],
        ))

    el.append(Spacer(1, 6 * mm))
    return el


def _build_executive_summary(data: dict, styles: dict, sec: dict | None = None) -> list:
    el = []
    editais = data.get("editais", [])
    resumo = data.get("resumo_executivo", {})

    num = sec["next"]() if sec else 2
    el.extend(_section_heading(f"{num}. Resumo Executivo", styles))

    # Summary text
    texto = _s(resumo.get("texto", ""))
    if texto:
        el.append(Paragraph(texto, styles["body"]))
        el.append(Spacer(1, 4 * mm))

    # Metrics
    total = len(editais)
    participar = sum(1 for e in editais if (e.get("recomendacao") or "").upper().startswith("PARTICIPAR"))
    cautela = sum(1 for e in editais if "CAUTELA" in (e.get("recomendacao") or "").upper() or "AVALIAR" in (e.get("recomendacao") or "").upper())
    nao_rec = total - participar - cautela
    valores = [_safe_float(e.get("valor_estimado")) for e in editais if e.get("valor_estimado")]
    valor_total = sum(valores)

    avail = PAGE_WIDTH - 2 * MARGIN
    col_w = avail / 4
    metrics = Table(
        [[
            _metric_cell(str(total), "Oportunidades", styles),
            _metric_cell(str(participar), "Participar", styles),
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
    el.append(Spacer(1, 5 * mm))

    # Distribution by UF — compact inline if few UFs
    uf_counts: dict[str, int] = {}
    for e in editais:
        uf = e.get("uf", "N/I")
        if uf:
            uf_counts[uf] = uf_counts.get(uf, 0) + 1
    if uf_counts and len(uf_counts) > 1:
        el.append(Paragraph("<b>Distribuição por UF</b>", styles["h3"]))
        header = [Paragraph(f"<b>{h}</b>", styles["cell_header"]) for h in ["UF", "Qtd", "%"]]
        rows = [header]
        for uf, cnt in sorted(uf_counts.items(), key=lambda x: -x[1])[:8]:
            pct = cnt / total * 100 if total else 0
            rows.append([
                Paragraph(uf, styles["cell_center"]),
                Paragraph(str(cnt), styles["cell_center"]),
                Paragraph(f"{pct:.0f}%", styles["cell_center"]),
            ])
        # Use half-width table when few UFs
        tw = avail * 0.5 if len(uf_counts) <= 4 else avail
        t = Table(rows, colWidths=[tw * 0.3, tw * 0.35, tw * 0.35])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
            ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ] + [("BACKGROUND", (0, i), (-1, i), TABLE_ALT_ROW) for i in range(2, len(rows), 2)]))
        el.append(t)
        el.append(Spacer(1, 4 * mm))
    elif uf_counts:
        # Single UF — just show inline
        uf_name = list(uf_counts.keys())[0]
        el.append(Paragraph(f"<b>UF:</b> {uf_name} ({total} editais)", styles["body"]))
        el.append(Spacer(1, 3 * mm))

    # Destaques
    destaques = resumo.get("destaques", [])
    if destaques:
        el.append(Paragraph("<b>Destaques</b>", styles["h3"]))
        for d in destaques:
            el.append(Paragraph(f"• {_s(d)}", styles["bullet"]))

    el.append(Spacer(1, 6 * mm))
    return el


def _build_overview_table(editais_list: list, styles: dict, start_idx: int = 1) -> list:
    """Build an overview table for a list of editais.

    Redesigned: fewer columns, wider text, no truncation of key info.
    Columns: #, Objeto+Órgão (merged for readability), UF, Valor, Prazo, Recomendação
    """
    avail = PAGE_WIDTH - 2 * MARGIN
    col_widths = [
        avail * 0.04,   # #
        avail * 0.42,   # Objeto + Órgão (combined — no more truncation)
        avail * 0.05,   # UF
        avail * 0.15,   # Valor
        avail * 0.12,   # Prazo
        avail * 0.22,   # Recomendação
    ]

    header = [Paragraph(f"<b>{h}</b>", styles["cell_header"]) for h in [
        "#", "Objeto / Órgão", "UF", "Valor (R$)", "Prazo", "Recomendação",
    ]]
    rows = [header]

    for idx, ed in enumerate(editais_list, start_idx):
        rec = _normalize_recommendation(_s(ed.get("recomendacao", "")))
        rec_color = REC_COLORS.get(rec, RED)

        rec_style = ParagraphStyle(
            f"rec_{idx}", parent=styles["cell_center"],
            fontName="Helvetica-Bold", textColor=rec_color, fontSize=7,
        )

        # Combined objeto + órgão for readability
        objeto = _s(ed.get("objeto", ""))
        orgao = _s(ed.get("orgao", ""))
        objeto_orgao = f"<b>{objeto}</b><br/><font size='7' color='#64748B'>{orgao}</font>"

        prazo = _format_prazo_short(ed.get("dias_restantes"))
        if prazo == "—":
            enc_date = _date(ed.get("data_encerramento"))
            prazo = enc_date if enc_date != "N/I" else "—"

        rows.append([
            Paragraph(str(idx), styles["cell_center"]),
            Paragraph(objeto_orgao, styles["cell"]),
            Paragraph(_s(ed.get("uf", "")), styles["cell_center"]),
            Paragraph(_currency_short(ed.get("valor_estimado")), styles["cell_right"]),
            Paragraph(prazo, styles["cell_center"]),
            Paragraph(rec, rec_style),
        ])

    t = Table(rows, colWidths=col_widths, repeatRows=1)
    base_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(2, len(rows), 2):
        base_styles.append(("BACKGROUND", (0, i), (-1, i), TABLE_ALT_ROW))
    t.setStyle(TableStyle(base_styles))
    return [t]


def _build_opportunities_overview(data: dict, styles: dict, sec: dict | None = None) -> list:
    el = []
    editais = data.get("editais", [])
    if not editais:
        return el

    num = sec["next"]() if sec else 3
    el.extend(_section_heading(f"{num}. Panorama de Oportunidades", styles))
    el.append(Spacer(1, 2 * mm))

    el.extend(_build_overview_table(editais, styles, start_idx=1))
    el.append(Spacer(1, 6 * mm))
    return el


def _build_detailed_analysis(data: dict, styles: dict, sec: dict | None = None) -> list:
    el = []
    editais = data.get("editais", [])
    if not editais:
        return el

    num = sec["next"]() if sec else 4
    el.extend(_section_heading(f"{num}. Análise Detalhada por Edital", styles))
    el.append(Spacer(1, 2 * mm))

    avail = PAGE_WIDTH - 2 * MARGIN

    for idx, ed in enumerate(editais, 1):
        # === HEADER BLOCK (KeepTogether: title + ficha + recommendation) ===
        header_block = []

        objeto = _s(ed.get("objeto", "Sem título"))
        rec = _normalize_recommendation(_s(ed.get("recomendacao", "")))
        badge_color = REC_COLORS.get(rec, RED)

        # Edital title with recommendation color bar on left
        title_bg = CARD_GREEN_BG if rec == "PARTICIPAR" else CARD_YELLOW_BG if "CAUTELA" in rec else CARD_RED_BG
        title_border = badge_color

        title_row = Table(
            [[Paragraph(f"<b>{num}.{idx}. {objeto}</b>", styles["h2"])]],
            colWidths=[avail],
        )
        title_row.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), title_bg),
            ("LINEBELOW", (0, 0), (-1, -1), 2, title_border),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        header_block.append(title_row)
        header_block.append(Spacer(1, 2 * mm))

        # Ficha técnica — cleaned up
        info_rows = []
        raw_fields = [
            ("Órgão", ed.get("orgao")),
            ("UF / Município", f"{ed.get('uf', 'N/I')} - {ed.get('municipio', 'N/I')}"),
            ("Modalidade", ed.get("modalidade")),
            ("Valor Estimado", _currency(ed.get("valor_estimado")) if ed.get("valor_estimado") else None),
            ("Data de Abertura", _date(ed.get("data_abertura"))),
            ("Data de Encerramento", _date(ed.get("data_encerramento"))),
            ("Situação", _format_dias_restantes(ed.get("dias_restantes"))),
            ("Fonte", ed.get("fonte")),
        ]
        # Add link only if valid
        link = ed.get("link", "")
        if link and link != "N/I" and link.startswith("http"):
            raw_fields.append(("Link", link))

        for label, value in raw_fields:
            if value and str(value).strip() and value != "N/I" and value != " - N/I" and str(value) != "None":
                info_rows.append([
                    Paragraph(f"<b>{label}</b>", styles["cell"]),
                    Paragraph(_s(str(value)), styles["cell"]),
                ])
        if info_rows:
            info_t = Table(info_rows, colWidths=[avail * 0.22, avail * 0.78])
            info_t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
                ("BACKGROUND", (0, 0), (0, -1), BRAND_LIGHT),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ]))
            header_block.append(info_t)
            header_block.append(Spacer(1, 3 * mm))

        # Recommendation card
        rec_text = f"Recomendação: <b>{rec}</b>"
        justificativa = _s(ed.get("justificativa", ""))
        if justificativa:
            rec_text += f"<br/><font size='9'>{justificativa}</font>"

        rec_card = Table(
            [[Paragraph(rec_text, ParagraphStyle(
                f"reccard_{idx}", parent=styles["body"],
                fontName="Helvetica-Bold", fontSize=11, textColor=badge_color,
            ))]],
            colWidths=[avail],
        )
        rec_bg = CARD_GREEN_BG if rec == "PARTICIPAR" else CARD_YELLOW_BG if "CAUTELA" in rec else CARD_RED_BG
        rec_card.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), rec_bg),
            ("BOX", (0, 0), (-1, -1), 0.75, badge_color),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        header_block.append(rec_card)
        header_block.append(Spacer(1, 3 * mm))

        # KeepTogether: title + ficha + recommendation never split
        el.append(KeepTogether(header_block))

        # === BODY (can flow across pages) ===

        # Distance
        distancia = ed.get("distancia", {})
        if isinstance(distancia, dict) and distancia.get("km"):
            km = distancia["km"]
            hrs = distancia.get("duracao_horas", "")
            badge_char, badge_color_d, badge_text = _get_source_badge(distancia.get("_source"))
            dist_text = f"<b>Distância da sede:</b> {km} km"
            if hrs:
                dist_text += f" (~{hrs}h de carro)"
            dist_text += f" <font color='{'#16A34A' if badge_char == '✓' else '#CA8A04'}'>[{badge_char} {badge_text}]</font>"
            el.append(Paragraph(dist_text, styles["body"]))

        # Viability index bar
        risk = ed.get("risk_score", {})
        if isinstance(risk, dict) and risk.get("total"):
            el.extend(_draw_risk_bar(_safe_int(risk["total"]), styles))
            el.append(Spacer(1, 2 * mm))

        # ROI Potential card
        roi = ed.get("roi_potential", {})
        el.extend(_build_roi_card(roi, styles))

        # Reverse Chronogram
        cronograma = ed.get("cronograma", [])
        el.extend(_build_chronogram_table(cronograma, styles))

        # Analysis sections — in a light bordered box
        analise = ed.get("analise", {})
        analysis_content = []
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
                analysis_content.append(Paragraph(f"<b>{title}:</b> {text}", styles["body"]))

        if analysis_content:
            # Wrap in a subtle bordered box
            box_content = []
            for item in analysis_content:
                box_content.append([item])
            box_t = Table(box_content, colWidths=[avail - 4 * mm])
            box_t.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFBFC")),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            el.append(box_t)
            el.append(Spacer(1, 3 * mm))

        # Q&A section — alternating background cards
        perguntas = ed.get("perguntas_decisor", {})
        if perguntas:
            el.append(Paragraph("<b>Perguntas do Decisor</b>", styles["h3"]))
            qa_rows = []
            for i, (pergunta, resposta) in enumerate(perguntas.items()):
                if resposta:
                    qa_rows.append([Paragraph(
                        f"<b>{_s(pergunta)}</b><br/><font size='8' color='#475569'>{_s(resposta)}</font>",
                        styles["cell"],
                    )])
            if qa_rows:
                qa_t = Table(qa_rows, colWidths=[avail - 2 * mm])
                qa_styles = [
                    ("BOX", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("LINEBELOW", (0, 0), (-1, -2), 0.25, TABLE_BORDER),
                ]
                for i in range(0, len(qa_rows), 2):
                    qa_styles.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F8FAFC")))
                qa_t.setStyle(TableStyle(qa_styles))
                el.append(qa_t)

        el.append(Spacer(1, 8 * mm))

    return el


def _build_market_intelligence(data: dict, styles: dict, sec: dict | None = None) -> list:
    el = []
    intel = data.get("inteligencia_mercado", {})
    if not intel:
        return el

    num = sec["next"]() if sec else 5
    el.extend(_section_heading(f"{num}. Inteligência de Mercado", styles))

    for title, key in [
        ("Panorama Setorial", "panorama"),
        ("Tendências", "tendencias"),
        ("Vantagens Competitivas da Empresa", "vantagens"),
        ("Recomendação Geral", "recomendacao_geral"),
    ]:
        text = _s(intel.get(key, ""))
        if text:
            el.append(Paragraph(f"<b>{title}</b>", styles["h3"]))
            for paragraph in text.split("\n"):
                paragraph = paragraph.strip()
                if paragraph:
                    if paragraph.startswith("•") or paragraph.startswith("-"):
                        el.append(Paragraph(paragraph, styles["bullet"]))
                    else:
                        el.append(Paragraph(paragraph, styles["body"]))

    el.append(Spacer(1, 6 * mm))
    return el


def _build_querido_diario(data: dict, styles: dict, sec: dict | None = None) -> list:
    el = []
    mencoes = data.get("querido_diario", [])
    if not mencoes:
        return el

    num = sec["next"]() if sec else 6
    el.extend(_section_heading(f"{num}. Menções em Diários Oficiais", styles))
    el.append(Paragraph(
        "Publicações encontradas no Querido Diário (diários oficiais municipais).",
        styles["body_small"],
    ))
    el.append(Spacer(1, 3 * mm))

    avail = PAGE_WIDTH - 2 * MARGIN

    # Build as a structured table: # | Data - Município | Trecho
    header = [Paragraph(f"<b>{h}</b>", styles["cell_header"]) for h in [
        "#", "Data / Município", "Trecho Relevante",
    ]]
    rows = [header]

    for idx, m in enumerate(mencoes[:10], 1):
        data_str = _date(m.get("data"))
        territorio = _s(m.get("territorio", ""))
        local_info = f"<b>{data_str}</b><br/><font size='7' color='#64748B'>{territorio}</font>"

        excerpts = m.get("excerpts", [])
        excerpt_texts = []
        for exc in excerpts[:2]:
            text = _s(exc.get("text", exc) if isinstance(exc, dict) else exc)
            if text:
                excerpt_texts.append(f"<i>\"{_trunc(text, 200)}\"</i>")

        trecho = "<br/>".join(excerpt_texts) if excerpt_texts else "<i>Sem trecho disponível</i>"

        rows.append([
            Paragraph(str(idx), styles["cell_center"]),
            Paragraph(local_info, styles["cell"]),
            Paragraph(f"<font size='7'>{trecho}</font>", styles["cell"]),
        ])

    t = Table(rows, colWidths=[avail * 0.05, avail * 0.22, avail * 0.73], repeatRows=1)
    base_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(2, len(rows), 2):
        base_styles.append(("BACKGROUND", (0, i), (-1, i), TABLE_ALT_ROW))
    t.setStyle(TableStyle(base_styles))
    el.append(t)

    el.append(Spacer(1, 6 * mm))
    return el


def _build_next_steps(data: dict, styles: dict, sec: dict | None = None) -> list:
    el = []
    proximos = data.get("proximos_passos", [])

    num = sec["next"]() if sec else 7
    el.extend(_section_heading(f"{num}. Próximos Passos", styles))

    avail = PAGE_WIDTH - 2 * MARGIN

    if proximos:
        # Build as a structured table: Ação | Prazo | Prioridade
        header = [Paragraph(f"<b>{h}</b>", styles["cell_header"]) for h in [
            "Ação", "Prazo", "Prioridade",
        ]]
        rows = [header]
        for step in proximos:
            if isinstance(step, dict):
                acao = _s(step.get("acao", ""))
                prazo = _s(step.get("prazo", ""))
                prioridade = _s(step.get("prioridade", ""))
                prio_upper = prioridade.upper()
                prio_color = "#DC2626" if "URGENTE" in prio_upper or "ALTA" in prio_upper else "#CA8A04" if "MEDIA" in prio_upper or "MÉDIA" in prio_upper else "#475569"
                rows.append([
                    Paragraph(acao, styles["cell"]),
                    Paragraph(prazo, styles["cell_center"]),
                    Paragraph(f"<font color='{prio_color}'><b>{prioridade}</b></font>", styles["cell_center"]),
                ])
            else:
                rows.append([
                    Paragraph(_s(step), styles["cell"]),
                    Paragraph("—", styles["cell_center"]),
                    Paragraph("—", styles["cell_center"]),
                ])

        t = Table(rows, colWidths=[avail * 0.60, avail * 0.22, avail * 0.18], repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
            ("GRID", (0, 0), (-1, -1), 0.5, TABLE_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ] + [("BACKGROUND", (0, i), (-1, i), TABLE_ALT_ROW) for i in range(2, len(rows), 2)]))
        el.append(t)
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

    el.append(Spacer(1, 8 * mm))
    # Contact card
    contact_t = Table(
        [[Paragraph(
            "Para dúvidas ou acompanhamento:<br/>"
            "<b>Tiago Sasaki</b> — Consultor de Licitações<br/>"
            "(48)9 8834-4559",
            styles["body"],
        )]],
        colWidths=[avail],
    )
    contact_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, BRAND_ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    el.append(contact_t)

    el.append(Spacer(1, 6 * mm))
    return el


# ============================================================
# SICAF & SOURCE CONFIDENCE
# ============================================================

def _build_sicaf_section(data: dict, styles: dict, sec: dict | None = None) -> list:
    el = []
    sicaf = data.get("sicaf", {})
    if not sicaf:
        return el

    num = sec["next"]() if sec else 8
    el.extend(_section_heading(f"{num}. Verificação SICAF", styles))

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


def _build_data_sources_section(data: dict, styles: dict, sec: dict | None = None) -> list:
    """Render data provenance section showing source status for each data category."""
    el = []
    metadata = data.get("_metadata", {})
    sources = metadata.get("sources", {})
    if not sources:
        return el

    num = sec["next"]() if sec else 9
    el.extend(_section_heading(f"{num}. Fontes de Dados e Confiabilidade", styles))
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

    el.append(Spacer(1, 6 * mm))
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
    """Generate the full B2G report PDF from structured data.

    Raises ValueError if blocking validation errors are found
    (e.g. recommendations without justificativa).
    """
    warnings, errors = _validate_json(data)
    if errors:
        raise ValueError(
            f"Geração do PDF bloqueada — {len(errors)} edital(is) com recomendação "
            f"sem justificativa. Preencha 'justificativa' em cada edital antes de gerar.\n"
            + "\n".join(f"  • {e}" for e in errors)
        )

    data = _sanitize_links(data)

    # Drop ENCERRADO editais — they don't belong in an opportunities report
    data["editais"] = [e for e in data.get("editais", []) if e.get("status_edital") != "ENCERRADO"]

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

    sec = _section_counter()
    elements: list = []
    elements.extend(_build_cover(data, styles, gen_date))
    elements.extend(_build_decision_table(data, styles, sec))
    elements.extend(_build_company_profile(data, styles, sec))
    elements.extend(_build_executive_summary(data, styles, sec))
    elements.extend(_build_opportunities_overview(data, styles, sec))
    elements.extend(_build_detailed_analysis(data, styles, sec))
    elements.extend(_build_competitive_section(data, styles, sec))
    elements.extend(_build_market_intelligence(data, styles, sec))
    elements.extend(_build_querido_diario(data, styles, sec))
    elements.extend(_build_next_steps(data, styles, sec))
    elements.extend(_build_sicaf_section(data, styles, sec))
    elements.extend(_build_data_sources_section(data, styles, sec))

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
