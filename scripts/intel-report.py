#!/usr/bin/env python3
"""
Gerador de PDF de Inteligência de Mercado — Top 20 Oportunidades.

Recebe JSON enriquecido (com campo 'analise' por edital do top20) e gera PDF
institucional com análise estratégica individual.

Design: Big Four / Management Consulting aesthetic — idêntico ao generate-report-b2g.py.

Usage:
    python scripts/intel-report.py --input data.json --output report.pdf
    python scripts/intel-report.py --input data.json  # output auto-named
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Windows console encoding fix
if sys.platform == "win32":
    import io
    try:
        if hasattr(sys.stdout, "buffer") and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "buffer") and not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except (ValueError, AttributeError):
        pass

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm, mm
    from reportlab.pdfgen import canvas as pdfgen_canvas
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
# DESIGN TOKENS — Big Four Aesthetic (matches generate-report-b2g.py)
# ============================================================

INK = colors.HexColor("#1B2A3D")
ACCENT = colors.HexColor("#8B7355")
SIGNAL_RED = colors.HexColor("#B5342A")
SIGNAL_GREEN = colors.HexColor("#1B7A3D")
SIGNAL_AMBER = colors.HexColor("#B8860B")

TEXT_COLOR = colors.HexColor("#2D3748")
TEXT_SECONDARY = colors.HexColor("#5A6577")
TEXT_MUTED = colors.HexColor("#8896A6")
LINK_BLUE = colors.HexColor("#1a56db")
RULE_COLOR = colors.HexColor("#C8CDD3")
RULE_HEAVY = colors.HexColor("#4A5568")
BG_SUBTLE = colors.HexColor("#F5F6F8")

DIFFICULTY_STYLES = {
    "BAIXO": SIGNAL_GREEN,
    "MEDIO": SIGNAL_AMBER,
    "ALTO": SIGNAL_RED,
}

FOOTER_LINE1 = "Tiago Sasaki — Consultor de Inteligência em Licitações"
FOOTER_LINE2 = "Relatório confidencial preparado exclusivamente para o destinatário"

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 2.2 * cm

ILLEGAL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

# ============================================================
# ACCENT RESTORATION
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
    "especifico": "específico", "especifica": "específica",
    "historico": "histórico", "historica": "histórica",
    "obrigatorio": "obrigatório", "obrigatoria": "obrigatória",
    "provisorio": "provisório",
    "viavel": "viável", "responsavel": "responsável",
    "compativel": "compatível", "acessivel": "acessível",
    "gerenciavel": "gerenciável", "possivel": "possível",
    "impossivel": "impossível", "provavel": "provável",
    "disponivel": "disponível",
    "nao": "não", "ja": "já", "tambem": "também",
    "ate": "até", "apos": "após", "so": "só",
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
    "logistica": "logística", "basica": "básica",
    "estrategia": "estratégia",
    "demolicao": "demolição", "demolicoes": "demolições",
    "aprovacao": "aprovação", "aprovacoes": "aprovações",
    "orcamentario": "orçamentário", "orcamentaria": "orçamentária",
    "contribuicao": "contribuição", "contribuicoes": "contribuições",
    "resolucao": "resolução", "resolucoes": "resoluções",
    "suspensao": "suspensão", "suspensoes": "suspensões",
    "impugnacao": "impugnação", "impugnacoes": "impugnações",
    "rescisao": "rescisão", "rescisoes": "rescisões",
    "homologacao": "homologação", "adjudicacao": "adjudicação",
    "revogacao": "revogação", "anulacao": "anulação",
    "inspecao": "inspeção", "aquisicao": "aquisição",
    "obrigacao": "obrigação", "obrigacoes": "obrigações",
    "alteracao": "alteração", "alteracoes": "alterações",
    "cotacao": "cotação", "publicacao": "publicação",
    "participacao": "participação",
    "classificacao": "classificação",
    "juridico": "jurídico", "juridica": "jurídica",
    "relatorio": "relatório", "relatorios": "relatórios",
    "valido": "válido", "valida": "válida",
    "inteligencia": "inteligência",
    "referencia": "referência", "referencias": "referências",
    "criterio": "critério", "criterios": "critérios",
    "patrimonio": "patrimônio",
    "territorio": "território",
    "beneficio": "benefício", "beneficios": "benefícios",
    "edificio": "edifício", "edificios": "edifícios",
    "exercicio": "exercício",
    "previo": "prévio", "previa": "prévia",
    "veiculos": "veículos", "veiculo": "veículo",
    "residuos": "resíduos",
    "conteudo": "conteúdo",
    "periodo": "período", "periodos": "períodos",
    "equilibrio": "equilíbrio",
    "portfolio": "portfólio",
    "diagnostico": "diagnóstico",
    "mobilizacao": "mobilização",
    "regiao": "região", "regioes": "regiões",
    "comercio": "comércio",
}

_ACCENT_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in sorted(_ACCENT_MAP.keys(), key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def _restore_accents(text: str) -> str:
    if not text:
        return text

    def _replace(m: re.Match) -> str:
        word = m.group(0)
        lower = word.lower()
        replacement = _ACCENT_MAP.get(lower, word)
        if word.isupper():
            return replacement.upper()
        if word[0].isupper():
            return replacement[0].upper() + replacement[1:]
        return replacement

    return _ACCENT_PATTERN.sub(_replace, text)


# ============================================================
# HELPERS
# ============================================================

def _s(value: Any, restore_accents: bool = True) -> str:
    """Sanitize text for PDF."""
    if value is None:
        return ""
    text = ILLEGAL_CHARS_RE.sub(" ", str(value))
    if restore_accents:
        text = _restore_accents(text)
    return text


def _currency(value: Any, default: str = "N/I") -> str:
    if value is None:
        return default
    try:
        v = float(value)
    except (ValueError, TypeError):
        return default
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


def _month_year() -> str:
    months = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
    }
    now = datetime.now(timezone.utc)
    return f"{months[now.month]} {now.year}"


def _trunc(text: str, n: int = 100) -> str:
    text = _s(text)
    return text if len(text) <= n else text[: n - 3].rstrip() + "..."


def _safe_float(v: Any, d: float = 0.0) -> float:
    try:
        return float(v) if v is not None else d
    except (ValueError, TypeError):
        return d


def _format_cnpj(cnpj: str) -> str:
    """Format CNPJ: 12345678000199 -> 12.345.678/0001-99."""
    c = re.sub(r"\D", "", str(cnpj))
    if len(c) == 14:
        return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:14]}"
    return cnpj


def _fix_pncp_link(link: str | None) -> str:
    if not link:
        return ""
    link = str(link).strip()
    m = re.match(r"https://pncp\.gov\.br/app/editais/(\d{14})-(\d{4})-(\d+)$", link)
    if m:
        cnpj, ano, seq = m.groups()
        return f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"
    return link


# ============================================================
# THREE-RULE TABLE
# ============================================================

def _three_rule_table(rows: list, col_widths: list, repeat_rows: int = 1) -> Table:
    t = Table(rows, colWidths=col_widths, repeatRows=repeat_rows)
    n = len(rows)
    style_cmds = [
        ("LINEABOVE", (0, 0), (-1, 0), 1.2, RULE_HEAVY),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, RULE_HEAVY),
        ("LINEBELOW", (0, n - 1), (-1, n - 1), 0.8, RULE_COLOR),
        *[("LINEBELOW", (0, i), (-1, i), 0.3, RULE_COLOR) for i in range(1, n - 1)],
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t


# ============================================================
# SECTION HEADING
# ============================================================

def _section_heading(title: str, styles: dict) -> list:
    avail = PAGE_WIDTH - 2 * MARGIN
    rule_t = Table([[""]], colWidths=[avail], rowHeights=[1])
    rule_t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (0, 0), 0.6, ACCENT),
        ("TOPPADDING", (0, 0), (0, 0), 0),
        ("BOTTOMPADDING", (0, 0), (0, 0), 0),
    ]))
    rule_t.keepWithNext = True
    h = Paragraph(title, styles["h1"])
    h.keepWithNext = True
    return [rule_t, Spacer(1, 2 * mm), h]


# ============================================================
# STYLES
# ============================================================

def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    s: dict[str, ParagraphStyle] = {}

    # Cover
    s["cover_title"] = ParagraphStyle(
        "cover_title", parent=base["Normal"],
        fontName="Times-Bold", fontSize=26, textColor=INK,
        alignment=TA_LEFT, leading=32, spaceAfter=4 * mm,
    )
    s["cover_subtitle"] = ParagraphStyle(
        "cover_subtitle", parent=base["Normal"],
        fontName="Times-Roman", fontSize=14, textColor=TEXT_SECONDARY,
        alignment=TA_LEFT, spaceAfter=3 * mm, leading=18,
    )
    s["cover_info"] = ParagraphStyle(
        "cover_info", parent=base["Normal"],
        fontName="Helvetica", fontSize=9, textColor=TEXT_SECONDARY,
        alignment=TA_LEFT, leading=13, spaceAfter=1.5 * mm,
    )

    # Headings
    s["h1"] = ParagraphStyle(
        "h1_intel", parent=base["Normal"],
        fontName="Times-Bold", fontSize=14, textColor=INK,
        spaceBefore=8 * mm, spaceAfter=4 * mm, leading=18,
    )
    s["h2"] = ParagraphStyle(
        "h2_intel", parent=base["Normal"],
        fontName="Times-Bold", fontSize=11, textColor=INK,
        spaceBefore=5 * mm, spaceAfter=3 * mm, leading=14,
    )

    # Body
    s["body"] = ParagraphStyle(
        "body_intel", parent=base["Normal"],
        fontName="Times-Roman", fontSize=10, textColor=TEXT_COLOR,
        alignment=TA_JUSTIFY, leading=14, spaceAfter=2 * mm,
    )
    s["body_small"] = ParagraphStyle(
        "body_small_intel", parent=base["Normal"],
        fontName="Times-Roman", fontSize=9, textColor=TEXT_SECONDARY,
        leading=12, spaceAfter=1.5 * mm,
    )
    s["bullet"] = ParagraphStyle(
        "bullet_intel", parent=base["Normal"],
        fontName="Times-Roman", fontSize=9, textColor=TEXT_COLOR,
        leading=12, leftIndent=10, spaceAfter=1 * mm,
    )
    s["bullet_small"] = ParagraphStyle(
        "bullet_small_intel", parent=base["Normal"],
        fontName="Helvetica", fontSize=7.5, textColor=TEXT_COLOR,
        leading=9.5, leftIndent=10, spaceAfter=0.5 * mm,
    )
    s["caption"] = ParagraphStyle(
        "caption_intel", parent=base["Normal"],
        fontName="Helvetica", fontSize=7, textColor=TEXT_MUTED,
        leading=9,
    )
    s["italic_note"] = ParagraphStyle(
        "italic_note_intel", parent=base["Normal"],
        fontName="Times-Italic", fontSize=9, textColor=SIGNAL_AMBER,
        leading=12, spaceAfter=1.5 * mm,
    )

    # Metrics
    s["metric_value"] = ParagraphStyle(
        "mv_intel", parent=base["Normal"],
        fontName="Times-Bold", fontSize=18, textColor=INK,
        alignment=TA_CENTER, leading=22,
    )
    s["metric_label"] = ParagraphStyle(
        "ml_intel", parent=base["Normal"],
        fontName="Helvetica", fontSize=7, textColor=TEXT_MUTED,
        alignment=TA_CENTER, leading=9,
    )

    # Table cells
    for name, align in [("cell", TA_LEFT), ("cell_center", TA_CENTER), ("cell_right", TA_RIGHT)]:
        s[name] = ParagraphStyle(
            f"{name}_intel", parent=base["Normal"],
            fontName="Helvetica", fontSize=8, textColor=TEXT_COLOR,
            leading=10, alignment=align,
        )
    s["cell_header"] = ParagraphStyle(
        "ch_intel", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=8, textColor=INK,
        leading=10, alignment=TA_LEFT,
    )
    s["cell_header_center"] = ParagraphStyle(
        "chc_intel", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=8, textColor=INK,
        leading=10, alignment=TA_CENTER,
    )
    s["cell_header_right"] = ParagraphStyle(
        "chr_intel", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=8, textColor=INK,
        leading=10, alignment=TA_RIGHT,
    )

    # Edital detail styles
    s["edital_title"] = ParagraphStyle(
        "edital_title_intel", parent=base["Normal"],
        fontName="Times-Bold", fontSize=10, textColor=INK,
        leading=13, spaceAfter=1 * mm,
    )
    s["edital_meta"] = ParagraphStyle(
        "edital_meta_intel", parent=base["Normal"],
        fontName="Helvetica", fontSize=8, textColor=TEXT_SECONDARY,
        leading=10, spaceAfter=1 * mm,
    )
    s["edital_link"] = ParagraphStyle(
        "edital_link_intel", parent=base["Normal"],
        fontName="Helvetica", fontSize=7.5, textColor=LINK_BLUE,
        leading=10, spaceAfter=2 * mm,
    )
    s["subsection"] = ParagraphStyle(
        "subsection_intel", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=8, textColor=INK,
        leading=10, spaceBefore=2 * mm, spaceAfter=1 * mm,
    )
    s["action_rec"] = ParagraphStyle(
        "action_rec_intel", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=9, textColor=SIGNAL_GREEN,
        leading=12, spaceBefore=2 * mm, spaceAfter=1 * mm,
    )

    return s


# ============================================================
# FOOTER with page numbers
# ============================================================

class _NumberedCanvas(pdfgen_canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states: list = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_number(total)
            pdfgen_canvas.Canvas.showPage(self)
        pdfgen_canvas.Canvas.save(self)

    def _draw_page_number(self, total: int):
        self.saveState()
        self.setFont("Helvetica", 7)
        self.setFillColor(TEXT_MUTED)
        self.drawRightString(
            PAGE_WIDTH - MARGIN,
            MARGIN - 12 * mm,
            f"Página {self._pageNumber} de {total}",
        )
        self.restoreState()


def _draw_footer(canvas, doc):
    """Footer callback — skips cover (page 1)."""
    if canvas._pageNumber == 1:
        return
    canvas.saveState()
    y = MARGIN - 10 * mm

    # Thin rule
    canvas.setStrokeColor(RULE_COLOR)
    canvas.setLineWidth(0.4)
    canvas.line(MARGIN, y + 4 * mm, PAGE_WIDTH - MARGIN, y + 4 * mm)

    # Institutional attribution
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawCentredString(PAGE_WIDTH / 2, y + 1.5 * mm, FOOTER_LINE1)
    canvas.drawCentredString(PAGE_WIDTH / 2, y - 2 * mm, FOOTER_LINE2)

    canvas.restoreState()


# ============================================================
# METRIC CELL
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


# ============================================================
# PAGE BUILDERS
# ============================================================

def _build_cover(data: dict, styles: dict) -> list:
    el: list = []
    empresa = data.get("empresa", {})

    # Top whitespace
    el.append(Spacer(1, 80 * mm))

    # Short bronze rule
    avail = PAGE_WIDTH - 2 * MARGIN
    rule_t = Table([["", ""]], colWidths=[40 * mm, avail - 40 * mm])
    rule_t.setStyle(TableStyle([("LINEBELOW", (0, 0), (0, 0), 0.8, ACCENT)]))
    el.append(rule_t)
    el.append(Spacer(1, 6 * mm))

    # Title
    el.append(Paragraph(
        "INTELIGÊNCIA DE MERCADO",
        styles["cover_title"],
    ))

    # Company name
    nome = _s(empresa.get("razao_social") or empresa.get("nome_fantasia", ""))
    if nome:
        el.append(Paragraph(nome, styles["cover_subtitle"]))

    # CNPJ + CNAE
    cnpj = empresa.get("cnpj", "")
    cnae_desc = _s(empresa.get("cnae_descricao") or empresa.get("cnae_principal_descricao", ""))
    meta_parts = []
    if cnpj:
        meta_parts.append(f"CNPJ {_format_cnpj(cnpj)}")
    if cnae_desc:
        meta_parts.append(cnae_desc)
    if meta_parts:
        el.append(Paragraph(
            " | ".join(meta_parts),
            ParagraphStyle(
                "cover_cnpj", fontName="Helvetica", fontSize=9,
                textColor=TEXT_SECONDARY, alignment=TA_LEFT, leading=13,
                spaceAfter=2 * mm,
            ),
        ))

    # Date
    el.append(Paragraph(_month_year(), styles["cover_info"]))

    el.append(Spacer(1, 40 * mm))

    # Consultant attribution
    el.append(Paragraph(
        "<b>Tiago Sasaki</b><br/>"
        "Consultor de Inteligência em Licitações<br/>"
        "(48) 9 8834-4559",
        ParagraphStyle(
            "cover_attr", fontName="Helvetica", fontSize=9,
            textColor=TEXT_SECONDARY, alignment=TA_LEFT, leading=13,
        ),
    ))

    el.append(PageBreak())
    return el


def _build_sumario_executivo(data: dict, styles: dict) -> list:
    """Page 2: Sumário Executivo."""
    el: list = []
    top20 = data.get("top20", [])
    estatisticas = data.get("estatisticas", {})

    el.extend(_section_heading("Sumário Executivo", styles))
    el.append(Spacer(1, 4 * mm))

    # Metrics row — 4 big numbers
    total_compat = estatisticas.get("total_cnae_compativel", len(data.get("editais", [])))
    dentro_capacidade = estatisticas.get("total_dentro_capacidade", total_compat)
    analisados = len(top20)

    valor_total = sum(_safe_float(e.get("valor_estimado")) for e in top20)

    avail = PAGE_WIDTH - 2 * MARGIN
    col_w = avail / 4
    metrics_row = [[
        _metric_cell(str(total_compat), "Compatíveis CNAE", styles),
        _metric_cell(str(dentro_capacidade), "Dentro da Capacidade", styles),
        _metric_cell(str(analisados), "Analisados em Profundidade", styles),
        _metric_cell(_currency_short(valor_total), "Valor Total Analisado", styles),
    ]]
    metrics_t = Table(metrics_row, colWidths=[col_w, col_w, col_w, col_w])
    metrics_t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    el.append(metrics_t)
    el.append(Spacer(1, 6 * mm))

    # Resumo executivo text
    resumo = data.get("resumo_executivo", "")
    if resumo:
        for paragraph in resumo.split("\n\n"):
            paragraph = paragraph.strip()
            if paragraph:
                el.append(Paragraph(_s(paragraph), styles["body"]))
    else:
        el.append(Paragraph(
            f"Foram identificadas <b>{total_compat}</b> oportunidades compatíveis com os CNAEs da empresa. "
            f"Destas, <b>{dentro_capacidade}</b> estão dentro da capacidade econômico-financeira. "
            f"<b>{analisados}</b> foram analisados em profundidade, totalizando <b>{_currency_short(valor_total)}</b> "
            f"em valor estimado.",
            styles["body"],
        ))

    # Note about excluded editais
    excluded = data.get("top20_excluded_count", 0)
    if excluded > 0:
        el.append(Spacer(1, 2 * mm))
        el.append(Paragraph(
            f"<i>{excluded} editais foram analisados mas excluídos deste relatório por incompatibilidade "
            f"com a atividade da empresa ou duplicidade. A lista completa está na planilha Excel.</i>",
            styles["italic_note"],
        ))

    el.append(Spacer(1, 4 * mm))

    # Top 5 summary table
    top5 = top20[:5]
    if top5:
        el.append(Paragraph("Destaques", styles["h2"]))
        header = [
            Paragraph("#", styles["cell_header_center"]),
            Paragraph("Objeto", styles["cell_header"]),
            Paragraph("Valor", styles["cell_header_right"]),
            Paragraph("UF", styles["cell_header_center"]),
            Paragraph("Abertura", styles["cell_header_center"]),
        ]
        rows = [header]
        for idx, ed in enumerate(top5, 1):
            link = _fix_pncp_link(ed.get("link") or ed.get("link_edital", ""))
            obj_text = _trunc(_s(ed.get("objeto", "")), 55)
            if link:
                obj_text = f'<a href="{link}" color="#1a56db">{obj_text}</a>'
            rows.append([
                Paragraph(str(idx), styles["cell_center"]),
                Paragraph(obj_text, styles["cell"]),
                Paragraph(_currency_short(ed.get("valor_estimado")), styles["cell_right"]),
                Paragraph(_s(ed.get("uf", "")), styles["cell_center"]),
                Paragraph(_date(ed.get("data_abertura") or ed.get("data_publicacao")), styles["cell_center"]),
            ])
        widths = [20, avail - 20 - 70 - 30 - 55, 70, 30, 55]
        el.append(_three_rule_table(rows, widths))

    el.append(PageBreak())
    return el


def _build_perfil_e_mapa(data: dict, styles: dict) -> list:
    """Page 3: Perfil da Empresa + Mapa de Oportunidades."""
    el: list = []
    empresa = data.get("empresa", {})
    top20 = data.get("top20", [])
    avail = PAGE_WIDTH - 2 * MARGIN

    # --- Perfil da Empresa ---
    el.extend(_section_heading("Perfil da Empresa", styles))
    el.append(Spacer(1, 2 * mm))

    cnae = _s(empresa.get("cnae_principal") or empresa.get("cnae", ""))
    cnae_desc = _s(empresa.get("cnae_descricao") or empresa.get("cnae_principal_descricao", ""))
    capital = _safe_float(empresa.get("capital_social"))
    capacidade_10x = capital * 10 if capital > 0 else 0
    uf_sede = _s(empresa.get("uf_sede") or empresa.get("uf", ""))
    cidade = _s(empresa.get("cidade_sede") or empresa.get("municipio", ""))

    profile_rows = []
    if empresa.get("razao_social"):
        profile_rows.append([
            Paragraph("Razão Social", styles["cell_header"]),
            Paragraph(_s(empresa["razao_social"]), styles["cell"]),
        ])
    if cnae:
        cnae_text = f"{cnae} — {cnae_desc}" if cnae_desc else cnae
        profile_rows.append([
            Paragraph("CNAE Principal", styles["cell_header"]),
            Paragraph(cnae_text, styles["cell"]),
        ])
    if capital > 0:
        profile_rows.append([
            Paragraph("Capital Social", styles["cell_header"]),
            Paragraph(_currency(capital), styles["cell"]),
        ])
    if capacidade_10x > 0:
        profile_rows.append([
            Paragraph("Capacidade (10×)", styles["cell_header"]),
            Paragraph(_currency(capacidade_10x), styles["cell"]),
        ])
    if cidade and uf_sede:
        profile_rows.append([
            Paragraph("Sede", styles["cell_header"]),
            Paragraph(f"{cidade} / {uf_sede}", styles["cell"]),
        ])
    elif uf_sede:
        profile_rows.append([
            Paragraph("UF Sede", styles["cell_header"]),
            Paragraph(uf_sede, styles["cell"]),
        ])

    if profile_rows:
        pt = Table(profile_rows, colWidths=[80, avail - 80])
        pt.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LINEBELOW", (0, 0), (-1, -1), 0.3, RULE_COLOR),
        ]))
        el.append(pt)

    el.append(Spacer(1, 4 * mm))

    # --- Situação Cadastral (SICAF + Sanções) ---
    sicaf = empresa.get("sicaf", {})
    sancoes = empresa.get("sancoes", {})
    sancionada = empresa.get("sancionada", False)
    restricao = empresa.get("restricao_sicaf")
    has_cadastral = isinstance(sicaf, dict) and sicaf.get("status") or isinstance(sancoes, dict)

    if has_cadastral:
        el.append(Paragraph("Situação Cadastral", styles["h2"]))

        cadastral_rows = []

        # SICAF
        if isinstance(sicaf, dict) and sicaf.get("status"):
            sicaf_status = _s(sicaf.get("status", ""))
            crc = sicaf.get("crc", {})
            crc_status = _s(crc.get("status_cadastral", "")) if isinstance(crc, dict) else ""

            sicaf_text = sicaf_status
            if crc_status:
                sicaf_text += f" — CRC: {crc_status}"

            cadastral_rows.append([
                Paragraph("SICAF", styles["cell_header"]),
                Paragraph(sicaf_text, styles["cell"]),
            ])

            if restricao is True:
                cadastral_rows.append([
                    Paragraph("Restrição SICAF", styles["cell_header"]),
                    Paragraph(
                        '<font color="#B5342A"><b>SIM — Empresa com restrição cadastral ativa</b></font>',
                        styles["cell"],
                    ),
                ])
            elif restricao is False:
                cadastral_rows.append([
                    Paragraph("Restrição SICAF", styles["cell_header"]),
                    Paragraph(
                        '<font color="#1B7A3D">Nenhuma restrição</font>',
                        styles["cell"],
                    ),
                ])

        # Sanções
        if isinstance(sancoes, dict):
            if sancionada:
                ativas = [k.upper() for k, v in sancoes.items() if v and k not in ("sancionada", "inconclusive")]
                sancoes_text = (
                    f'<font color="#B5342A"><b>EMPRESA SANCIONADA — {", ".join(ativas)}</b></font>'
                    if ativas else
                    '<font color="#B5342A"><b>EMPRESA SANCIONADA</b></font>'
                )
            else:
                sancoes_text = '<font color="#1B7A3D">Nenhuma sanção ativa (CEIS/CNEP/CEPIM/CEAF)</font>'

            cadastral_rows.append([
                Paragraph("Sanções", styles["cell_header"]),
                Paragraph(sancoes_text, styles["cell"]),
            ])

        if cadastral_rows:
            ct = Table(cadastral_rows, colWidths=[80, avail - 80])
            ct.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LINEBELOW", (0, 0), (-1, -1), 0.3, RULE_COLOR),
            ]))
            el.append(ct)

        if sancionada:
            el.append(Spacer(1, 2 * mm))
            el.append(Paragraph(
                "<i>Empresa com impedimento legal para participação em licitações. "
                "Recomenda-se regularização junto aos órgãos competentes antes de prosseguir.</i>",
                styles["italic_note"],
            ))

    el.append(Spacer(1, 6 * mm))

    # --- Mapa de Oportunidades ---
    el.extend(_section_heading("Mapa de Oportunidades", styles))
    el.append(Spacer(1, 2 * mm))

    if top20:
        header = [
            Paragraph("#", styles["cell_header_center"]),
            Paragraph("Objeto", styles["cell_header"]),
            Paragraph("Valor", styles["cell_header_right"]),
            Paragraph("UF", styles["cell_header_center"]),
            Paragraph("Dist.", styles["cell_header_right"]),
            Paragraph("Custo", styles["cell_header_right"]),
            Paragraph("Dificuldade", styles["cell_header_center"]),
        ]
        rows = [header]
        for idx, ed in enumerate(top20, 1):
            analise = ed.get("analise", {})
            dif = (analise.get("nivel_dificuldade") or "").upper()
            dif_color = DIFFICULTY_STYLES.get(dif, TEXT_COLOR)
            dif_text = dif if dif in DIFFICULTY_STYLES else "—"
            dif_style = ParagraphStyle(
                f"dif_{idx}", parent=styles["cell_center"],
                textColor=dif_color, fontName="Helvetica-Bold",
            )

            # Distance
            dist_data = ed.get("distancia", {})
            dist_km = dist_data.get("km") if isinstance(dist_data, dict) else None
            dist_text = f"{dist_km:.0f}km" if dist_km is not None else "—"

            # Cost
            cost_data = ed.get("custo_proposta", {})
            cost_total = cost_data.get("total") if isinstance(cost_data, dict) else None
            cost_text = _currency_short(cost_total) if cost_total else "—"

            link = _fix_pncp_link(ed.get("link") or ed.get("link_edital", ""))
            obj_text = _trunc(_s(ed.get("objeto", "")), 40)
            if link:
                obj_text = f'<a href="{link}" color="#1a56db">{obj_text}</a>'
            rows.append([
                Paragraph(str(idx), styles["cell_center"]),
                Paragraph(obj_text, styles["cell"]),
                Paragraph(_currency_short(ed.get("valor_estimado")), styles["cell_right"]),
                Paragraph(_s(ed.get("uf", "")), styles["cell_center"]),
                Paragraph(dist_text, styles["cell_right"]),
                Paragraph(cost_text, styles["cell_right"]),
                Paragraph(dif_text, dif_style),
            ])

        widths = [18, avail - 18 - 58 - 25 - 42 - 52 - 50, 58, 25, 42, 52, 50]
        el.append(_three_rule_table(rows, widths))

    el.append(PageBreak())
    return el


def _build_edital_detail(idx: int, ed: dict, styles: dict) -> list:
    """Build half-page detail block for one edital."""
    elements: list = []
    analise = ed.get("analise") or {}
    avail = PAGE_WIDTH - 2 * MARGIN

    # Bronze rule separator
    rule_t = Table([[""]], colWidths=[avail], rowHeights=[1])
    rule_t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (0, 0), 0.6, ACCENT),
        ("TOPPADDING", (0, 0), (0, 0), 0),
        ("BOTTOMPADDING", (0, 0), (0, 0), 0),
    ]))
    elements.append(rule_t)
    elements.append(Spacer(1, 2 * mm))

    # Title (clickable link to PNCP)
    objeto = _trunc(_s(ed.get("objeto", "Sem objeto")), 80)
    link = _fix_pncp_link(ed.get("link") or ed.get("link_pncp") or ed.get("link_edital", ""))
    if link:
        title_text = f'#{idx} — <a href="{link}" color="#1a56db">{objeto}</a>'
    else:
        title_text = f"#{idx} — {objeto}"
    elements.append(Paragraph(title_text, styles["edital_title"]))

    # Metadata line
    orgao = _s(ed.get("orgao") or ed.get("nomeOrgao", ""))
    uf = _s(ed.get("uf", ""))
    municipio = _s(ed.get("municipio", ""))
    modalidade = _s(ed.get("modalidade", ""))
    loc = f"{uf} — {municipio}" if municipio else uf
    meta_parts = [p for p in [orgao, loc, modalidade] if p]
    if meta_parts:
        elements.append(Paragraph(" | ".join(meta_parts), styles["edital_meta"]))

    # Value + date line
    valor = _currency(ed.get("valor_estimado"))
    data_abertura = _date(ed.get("data_abertura") or ed.get("data_publicacao"))
    elements.append(Paragraph(
        f"Valor Estimado: <b>{valor}</b> | Abertura: <b>{data_abertura}</b>",
        styles["edital_meta"],
    ))

    # Distance + Cost line (if enriched)
    dist_data = ed.get("distancia", {})
    cost_data = ed.get("custo_proposta", {})
    ibge_data = ed.get("ibge", {})
    roi_data = ed.get("roi_proposta", {})

    geo_parts = []
    if isinstance(dist_data, dict) and dist_data.get("km") is not None:
        km = dist_data["km"]
        dur = dist_data.get("duracao_horas")
        dur_text = f" ({dur:.1f}h)" if dur else ""
        geo_parts.append(f"Distância: <b>{km:.0f} km{dur_text}</b>")

    if isinstance(cost_data, dict) and cost_data.get("total") is not None:
        tipo = cost_data.get("modalidade_tipo", "")
        tipo_label = " (eletrônica)" if tipo == "eletronica" else ""
        geo_parts.append(f"Custo proposta{tipo_label}: <b>{_currency(cost_data['total'])}</b>")

    if isinstance(roi_data, dict) and roi_data.get("classificacao"):
        roi_class = roi_data["classificacao"]
        roi_color = "#1B7A3D" if roi_class in ("EXCELENTE", "BOM") else (
            "#B5342A" if roi_class in ("MARGINAL", "DESFAVORAVEL") else "#B8860B"
        )
        geo_parts.append(f'ROI: <font color="{roi_color}"><b>{roi_class}</b></font>')

    if isinstance(ibge_data, dict) and ibge_data.get("populacao"):
        pop = ibge_data["populacao"]
        pop_text = f"{pop:,}".replace(",", ".")
        geo_parts.append(f"Pop: {pop_text} hab")

    if geo_parts:
        elements.append(Paragraph(" | ".join(geo_parts), styles["edital_meta"]))

    # Clickable link
    link = _fix_pncp_link(ed.get("link") or ed.get("link_edital", ""))
    if link:
        elements.append(Paragraph(
            f'Link: <a href="{link}" color="#1a56db">{_trunc(link, 70)}</a>',
            styles["edital_link"],
        ))

    # If no analise, show placeholder
    if not analise:
        elements.append(Paragraph(
            "<i>Análise pendente — dados do edital ainda não foram processados.</i>",
            styles["italic_note"],
        ))
        elements.append(Spacer(1, 3 * mm))
        return elements

    # Resumo do objeto
    resumo_obj = analise.get("resumo_objeto", "")
    if resumo_obj:
        elements.append(Paragraph(_s(resumo_obj), styles["body_small"]))
        elements.append(Spacer(1, 1 * mm))

    # REQUISITOS TÉCNICOS
    req_tec = analise.get("requisitos_tecnicos", [])
    if req_tec:
        elements.append(Paragraph("REQUISITOS TÉCNICOS", styles["subsection"]))
        for req in req_tec[:5]:  # cap at 5 items to save space
            elements.append(Paragraph(f"• {_s(req)}", styles["bullet_small"]))

    # HABILITAÇÃO E QUALIFICAÇÃO
    req_hab = analise.get("requisitos_habilitacao", [])
    qual_econ = analise.get("qualificacao_economica", "")
    garantias = analise.get("garantias", "")
    if req_hab or qual_econ or garantias:
        elements.append(Paragraph("HABILITAÇÃO E QUALIFICAÇÃO", styles["subsection"]))
        for req in req_hab[:4]:  # cap at 4
            elements.append(Paragraph(f"• {_s(req)}", styles["bullet_small"]))
        if qual_econ:
            elements.append(Paragraph(f"• Qualificação econômica: {_s(qual_econ)}", styles["bullet_small"]))
        if garantias:
            elements.append(Paragraph(f"• Garantia: {_s(garantias)}", styles["bullet_small"]))

    # CONDITIONS ROW
    prazo = _s(analise.get("prazo_execucao", ""))
    criterio = _s(analise.get("criterio_julgamento", ""))
    visita = _s(analise.get("visita_tecnica", ""))
    consorcio = _s(analise.get("consorcio", ""))

    cond_parts = []
    if prazo:
        cond_parts.append(f"Prazo: {prazo}")
    if criterio:
        cond_parts.append(f"Julgamento: {criterio}")
    if visita:
        # Normalize to Sim/Não
        visita_lower = visita.lower()
        if "obrigat" in visita_lower or visita_lower in ("sim", "yes"):
            cond_parts.append("Visita: Sim")
        elif visita_lower in ("não", "nao", "no", "não obrigatória", "dispensada", "facultativa"):
            cond_parts.append("Visita: Não")
        else:
            cond_parts.append(f"Visita: {visita}")
    if consorcio:
        consorcio_lower = consorcio.lower()
        if "permit" in consorcio_lower or consorcio_lower in ("sim", "yes"):
            cond_parts.append("Consórcio: Sim")
        elif "não" in consorcio_lower or "nao" in consorcio_lower or consorcio_lower in ("no",):
            cond_parts.append("Consórcio: Não")
        else:
            cond_parts.append(f"Consórcio: {consorcio}")

    if cond_parts:
        elements.append(Spacer(1, 1 * mm))
        elements.append(Paragraph(
            " | ".join(cond_parts),
            ParagraphStyle(
                f"cond_{idx}", parent=styles["edital_meta"],
                fontName="Helvetica", fontSize=7.5, textColor=TEXT_SECONDARY,
            ),
        ))

    # Observações críticas (italic, amber)
    obs = analise.get("observacoes_criticas", "")
    if obs:
        elements.append(Paragraph(f"<i>{_s(obs)}</i>", styles["italic_note"]))

    # AÇÃO RECOMENDADA
    acao = analise.get("recomendacao_acao", "")
    if acao:
        elements.append(Paragraph(f"AÇÃO RECOMENDADA: {_s(acao)}", styles["action_rec"]))

    # Hairline separator at bottom
    hr_t = Table([[""]], colWidths=[avail], rowHeights=[1])
    hr_t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (0, 0), 0.3, RULE_COLOR),
        ("TOPPADDING", (0, 0), (0, 0), 0),
        ("BOTTOMPADDING", (0, 0), (0, 0), 0),
    ]))
    elements.append(Spacer(1, 1.5 * mm))
    elements.append(hr_t)
    elements.append(Spacer(1, 2 * mm))

    return elements


def _build_analise_individual(data: dict, styles: dict) -> list:
    """Pages 4-13: Individual analysis of top 20 editais, 2 per page."""
    el: list = []
    top20 = data.get("top20", [])

    if not top20:
        return el

    el.extend(_section_heading("Análise Individual", styles))
    el.append(Spacer(1, 2 * mm))

    for idx, ed in enumerate(top20, 1):
        detail = _build_edital_detail(idx, ed, styles)
        # Use KeepTogether to avoid splitting a single edital across pages
        el.append(KeepTogether(detail))

    el.append(PageBreak())
    return el


def _build_plano_acao(data: dict, styles: dict) -> list:
    """Pages 14-15: Próximos Passos + Cronograma."""
    el: list = []
    top20 = data.get("top20", [])
    proximos_passos = data.get("proximos_passos", [])
    avail = PAGE_WIDTH - 2 * MARGIN

    el.extend(_section_heading("Plano de Ação", styles))
    el.append(Spacer(1, 4 * mm))

    # Numbered list of próximos passos
    if proximos_passos:
        for idx, passo in enumerate(proximos_passos, 1):
            el.append(Paragraph(f"<b>{idx}.</b> {_s(passo)}", styles["body"]))
    else:
        el.append(Paragraph(
            "1. Revisar os requisitos de habilitação de cada edital priorizado.<br/>"
            "2. Providenciar atestados de capacidade técnica necessários.<br/>"
            "3. Agendar visitas técnicas obrigatórias.<br/>"
            "4. Preparar documentação econômico-financeira.<br/>"
            "5. Elaborar propostas de preço competitivas.",
            styles["body"],
        ))

    el.append(Spacer(1, 6 * mm))

    # Timeline table
    if top20:
        el.append(Paragraph("Cronograma de Prazos", styles["h2"]))

        header = [
            Paragraph("#", styles["cell_header_center"]),
            Paragraph("Edital", styles["cell_header"]),
            Paragraph("Abertura", styles["cell_header_center"]),
            Paragraph("Ação Prioritária", styles["cell_header"]),
            Paragraph("Dificuldade", styles["cell_header_center"]),
        ]
        rows = [header]

        # Sort by data_abertura (earliest first)
        sorted_eds = sorted(
            enumerate(top20, 1),
            key=lambda x: x[1].get("data_abertura") or x[1].get("data_publicacao") or "9999",
        )

        for orig_idx, ed in sorted_eds[:20]:
            analise = ed.get("analise") or {}
            dif = (analise.get("nivel_dificuldade") or "").upper()
            dif_color = DIFFICULTY_STYLES.get(dif, TEXT_COLOR)
            dif_text = dif if dif in DIFFICULTY_STYLES else "—"
            dif_style = ParagraphStyle(
                f"tl_dif_{orig_idx}", parent=styles["cell_center"],
                textColor=dif_color, fontName="Helvetica-Bold",
            )
            acao = _trunc(_s(analise.get("recomendacao_acao", "—")), 45)
            link = _fix_pncp_link(ed.get("link") or ed.get("link_pncp") or ed.get("link_edital", ""))
            obj_text = _trunc(_s(ed.get("objeto", "")), 40)
            if link:
                obj_text = f'<a href="{link}" color="#1a56db">{obj_text}</a>'
            rows.append([
                Paragraph(str(orig_idx), styles["cell_center"]),
                Paragraph(obj_text, styles["cell"]),
                Paragraph(_date(ed.get("data_abertura") or ed.get("data_publicacao")), styles["cell_center"]),
                Paragraph(acao, styles["cell"]),
                Paragraph(dif_text, dif_style),
            ])

        widths = [18, avail - 18 - 50 - 145 - 48, 50, 145, 48]
        el.append(_three_rule_table(rows, widths))

    el.append(Spacer(1, 8 * mm))

    # Footer note
    el.append(Paragraph(
        "Este relatório foi gerado com base em dados públicos do Portal Nacional de Contratações Públicas (PNCP) "
        "e demais fontes de dados abertos. As informações refletem o estado dos editais no momento da consulta. "
        "Recomenda-se a verificação direta nos portais oficiais antes de qualquer decisão de participação.",
        styles["caption"],
    ))

    return el


# ============================================================
# MAIN GENERATOR
# ============================================================

def _filter_top20(top20: list[dict]) -> list[dict]:
    """Remove editais NÃO PARTICIPAR and DUPLICATAs from top20 for the PDF report."""
    exclude_keywords = ["NÃO PARTICIPAR", "NAO PARTICIPAR", "DUPLICATA"]
    seen_keys: set[str] = set()
    filtered: list[dict] = []
    for e in top20:
        analise = e.get("analise", {})
        acao = (analise.get("recomendacao_acao") or "").upper()
        # Skip excluded recommendations
        if any(kw in acao for kw in exclude_keywords):
            continue
        # Dedup by normalized objeto + valor
        obj = (e.get("objeto") or "").lower().strip()
        for prefix in ["[portal de compras públicas] - ", "[portal de compras publicas] - "]:
            if obj.startswith(prefix):
                obj = obj[len(prefix):]
        valor = e.get("valor_estimado") or 0
        key = f"{e.get('uf','')}|{valor}|{obj[:80]}"
        if key in seen_keys:
            continue
        seen_keys.add(key)
        filtered.append(e)
    return filtered


def generate_intel_report(data: dict, output_path: str) -> str:
    """Generate the intelligence report PDF."""
    # Filter top20: remove NÃO PARTICIPAR, DUPLICATAs, and dedup
    raw_top20 = data.get("top20", [])
    filtered_top20 = _filter_top20(raw_top20)
    excluded_count = len(raw_top20) - len(filtered_top20)
    data["top20_report"] = filtered_top20
    data["top20_excluded_count"] = excluded_count
    # Use filtered list for all report sections
    data["top20"] = filtered_top20

    styles = _build_styles()
    elements: list = []

    # Page 1: Cover
    elements.extend(_build_cover(data, styles))

    # Page 2: Sumário Executivo
    elements.extend(_build_sumario_executivo(data, styles))

    # Page 3: Perfil + Mapa
    elements.extend(_build_perfil_e_mapa(data, styles))

    # Pages 4-13: Análise Individual
    elements.extend(_build_analise_individual(data, styles))

    # Pages 14-15: Plano de Ação
    elements.extend(_build_plano_acao(data, styles))

    # Build PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN + 8 * mm,  # room for footer
        title="Inteligência de Mercado",
        author="Tiago Sasaki",
    )

    doc.build(elements, onFirstPage=lambda c, d: None, onLaterPages=_draw_footer, canvasmaker=_NumberedCanvas)

    return output_path


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Gera PDF de Inteligência de Mercado a partir de JSON enriquecido."
    )
    parser.add_argument("--input", required=True, help="Caminho para JSON de entrada")
    parser.add_argument("--output", help="Caminho para PDF de saída (auto-nomeado se omitido)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    print(f"  Lendo {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate minimum structure
    empresa = data.get("empresa", {})
    top20 = data.get("top20", [])
    editais = data.get("editais", [])

    print(f"  Empresa: {empresa.get('razao_social', 'N/I')}")
    print(f"  Editais totais: {len(editais)}")
    print(f"  Top 20 selecionados: {len(top20)}")

    # Count analyzed
    analyzed = sum(1 for e in top20 if e.get("analise"))
    print(f"  Com análise: {analyzed}/{len(top20)}")

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        cnpj = re.sub(r"\D", "", empresa.get("cnpj", "empresa"))
        slug = re.sub(r"[^\w\-]", "-", (empresa.get("razao_social") or "empresa").lower())[:30].rstrip("-")
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        output_path = str(input_path.parent / f"intel-{cnpj}-{slug}-{date_str}.pdf")

    print(f"  Gerando PDF: {output_path}")
    result = generate_intel_report(data, output_path)
    print(f"  PDF gerado com sucesso: {result}")

    return result


if __name__ == "__main__":
    main()
