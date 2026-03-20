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


# Common verbose prefixes in tender objects that obscure the actual content
_OBJECT_PREFIXES_TO_STRIP = [
    "Seleção de proposta mais vantajosa para contratação de empresa especializada em ",
    "Selecao de proposta mais vantajosa para contratacao de empresa especializada em ",
    "[Portal de Compras Públicas] - ",
    "[Portal de Compras Publicas] - ",
    "Registro de preços, visando a contratação de ",
    "Registro de precos, visando a contratacao de ",
    "Registro de preços para futura e eventual contratação de ",
    "Registro de precos para futura e eventual contratacao de ",
    "Contratação de empresa especializada em ",
    "Contratacao de empresa especializada em ",
    "Contratação de empresa especializada para ",
    "Contratacao de empresa especializada para ",
    "Contratação de pessoa jurídica especializada em ",
    "Contratacao de pessoa juridica especializada em ",
]


def _smart_trunc(objeto: str, n: int = 50) -> str:
    """Strip common verbose prefixes from tender objects, then truncate.

    This reveals the actual distinct content instead of 20 objects all
    starting with 'Seleção de proposta mais vantajosa...'.
    """
    text = _s(objeto)
    text_lower = text.lower()
    for prefix in _OBJECT_PREFIXES_TO_STRIP:
        if text_lower.startswith(prefix.lower()):
            text = text[len(prefix):]
            # Capitalize first letter of remaining text
            if text:
                text = text[0].upper() + text[1:]
            break
    return text if len(text) <= n else text[: n - 3].rstrip() + "…"


def _safe_float(v: Any, d: float = 0.0) -> float:
    try:
        return float(v) if v is not None else d
    except (ValueError, TypeError):
        return d


def _plural(n: int, singular: str, plural: str) -> str:
    return singular if n == 1 else plural


# ============================================================
# DETERMINISTIC RESUMO + PRÓXIMOS PASSOS (computed from data)
# ============================================================

def _generate_resumo(empresa: dict, top20_pdf: list[dict], stats: dict) -> str:
    """Generate resumo executivo deterministically from data."""
    participar = [e for e in top20_pdf if (e.get('analise') or {}).get('recomendacao_acao', '').upper().startswith('PARTICIPAR')]
    nao_part = [e for e in top20_pdf if (e.get('analise') or {}).get('recomendacao_acao', '').upper().startswith('NAO')]

    acao_imediata = [e for e in participar if e.get('status_temporal') in ('PLANEJAVEL', 'IMINENTE', 'URGENTE')]
    sessao_realizada = [e for e in participar if e.get('status_temporal') == 'SESSAO_REALIZADA']

    val_participar = sum((_safe_float(e.get('valor_estimado')) for e in participar))
    val_imediata = sum((_safe_float(e.get('valor_estimado')) for e in acao_imediata))

    total_compat = stats.get('total_cnae_compativel', 0)

    nome = empresa.get('razao_social', 'A empresa')
    sede = f"{empresa.get('cidade_sede', '')} / {empresa.get('uf_sede', '')}".strip(' /')

    lines: list[str] = []
    lines.append(f"A {nome} possui {total_compat} oportunidades compatíveis identificadas no PNCP.")
    lines.append(f"Dos editais analisados, {len(participar)} receberam recomendação PARTICIPAR "
                  f"(valor total R$ {val_participar/1e6:.1f}M) e {len(nao_part)} NÃO PARTICIPAR com justificativa.")

    if acao_imediata:
        lines.append(f"{len(acao_imediata)} editais têm propostas abertas para ação imediata "
                      f"(R$ {val_imediata/1e6:.1f}M).")
    if sessao_realizada:
        lines.append(f"{len(sessao_realizada)} editais tiveram sessão já realizada — consultar resultado "
                      f"nos portais antes de qualquer ação.")

    # Top 3 destaques
    top3 = sorted(participar, key=lambda e: _safe_float(e.get('valor_estimado')), reverse=True)[:3]
    if top3:
        destaques = []
        for e in top3:
            mun = e.get('municipio', '?')
            val = _safe_float(e.get('valor_estimado')) / 1e6
            obj_short = (e.get('objeto', '') or '')[:50]
            destaques.append(f"{mun} (R$ {val:.1f}M — {obj_short})")
        lines.append(f"Destaques: {', '.join(destaques)}.")

    return '\n\n'.join(lines)


def _generate_proximos_passos(top20_pdf: list[dict]) -> list[dict]:
    """Generate action items deterministically from data."""
    participar = [e for e in top20_pdf if (e.get('analise') or {}).get('recomendacao_acao', '').upper().startswith('PARTICIPAR')]

    urgency_order = {'URGENTE': 0, 'IMINENTE': 1, 'PLANEJAVEL': 2, 'SESSAO_REALIZADA': 3}
    priority_label = {'URGENTE': 'URGENTE', 'IMINENTE': 'URGENTE', 'PLANEJAVEL': 'PRIORITÁRIO', 'SESSAO_REALIZADA': 'MONITORAR'}

    sorted_eds = sorted(participar, key=lambda e: (
        urgency_order.get(e.get('status_temporal', 'SESSAO_REALIZADA'), 9),
        -(_safe_float(e.get('valor_estimado')))
    ))

    passos: list[dict] = []
    for e in sorted_eds[:8]:
        st = e.get('status_temporal', 'SESSAO_REALIZADA')
        prefix = priority_label.get(st, 'AVALIAR')
        mun = e.get('municipio', '?')
        val = _safe_float(e.get('valor_estimado')) / 1e6
        obj = (e.get('objeto', '') or '')[:60].strip()

        data_val = (e.get('analise') or {}).get('data_sessao', '') or (e.get('analise') or {}).get('prazo_proposta', '')

        if st == 'SESSAO_REALIZADA':
            acao = f"{prefix}: {mun} — {obj} R$ {val:.1f}M. Sessão já realizada, consultar resultado no portal."
        else:
            acao = f"{prefix}: {mun} — {obj} R$ {val:.1f}M (sessão {data_val})."

        prazo = data_val if st != 'SESSAO_REALIZADA' else ""
        passos.append({"acao": acao, "prazo": prazo, "prioridade": prefix})

    return passos


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
        fontName="Helvetica", fontSize=8.5, textColor=TEXT_COLOR,
        leading=9.5, leftIndent=10, spaceAfter=0.5 * mm,
    )
    s["caption"] = ParagraphStyle(
        "caption_intel", parent=base["Normal"],
        fontName="Helvetica", fontSize=8, textColor=TEXT_MUTED,
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
        fontName="Times-Bold", fontSize=22, textColor=INK,
        alignment=TA_CENTER, leading=22,
    )
    s["metric_label"] = ParagraphStyle(
        "ml_intel", parent=base["Normal"],
        fontName="Helvetica", fontSize=8.5, textColor=TEXT_MUTED,
        alignment=TA_CENTER, leading=9,
    )

    # Table cells
    for name, align in [("cell", TA_LEFT), ("cell_center", TA_CENTER), ("cell_right", TA_RIGHT)]:
        s[name] = ParagraphStyle(
            f"{name}_intel", parent=base["Normal"],
            fontName="Helvetica", fontSize=8.5, textColor=TEXT_COLOR,
            leading=10, alignment=align,
        )
    s["cell_header"] = ParagraphStyle(
        "ch_intel", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=8.5, textColor=INK,
        leading=10, alignment=TA_LEFT,
    )
    s["cell_header_center"] = ParagraphStyle(
        "chc_intel", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=8.5, textColor=INK,
        leading=10, alignment=TA_CENTER,
    )
    s["cell_header_right"] = ParagraphStyle(
        "chr_intel", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=8.5, textColor=INK,
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


def _build_funil(data: dict, styles: dict) -> list:
    """Build visual funnel explaining the filtering pipeline."""
    el: list = []
    estatisticas = data.get("estatisticas", {})
    top20 = data.get("top20", [])

    total_bruto = estatisticas.get("total_bruto", len(data.get("editais", [])))
    total_expirados = estatisticas.get("total_expirados_removidos", estatisticas.get("total_expirados", 0))
    total_ativos = estatisticas.get("total_apos_filtro_temporal", total_bruto - total_expirados)
    total_compat = estatisticas.get("total_cnae_compativel", 0)
    total_dentro = estatisticas.get("total_dentro_capacidade", total_compat)
    total_analisados = estatisticas.get("total_analisados_profundidade", 20)
    total_recomendados = len(top20)

    empresa = data.get("empresa", {})
    ufs = ", ".join(data.get("busca", {}).get("ufs", []))
    dias = data.get("busca", {}).get("dias", 30)
    capital = _safe_float(empresa.get("capital_social")) or 0
    cap_10x = capital * 10 if capital > 0 else 0

    el.append(Spacer(1, 6 * mm))
    el.append(Paragraph("Metodologia de Seleção", styles["h2"]))
    el.append(Spacer(1, 2 * mm))

    avail = PAGE_WIDTH - 2 * MARGIN

    # Funnel rows: [count, description, detail]
    # Order matches pipeline: bruto → expirados removidos → CNAE → capacidade → analisados → recomendados
    funnel_steps = [
        (str(total_bruto), "editais publicados", f"PNCP — {ufs} — últimos {dias} dias"),
        (str(total_ativos), "com prazo vigente", f"{total_expirados} expirados removidos antes de qualquer análise"),
        (str(total_compat), "compatíveis com CNAE", f"filtro por {1 + len([c for c in (empresa.get('cnaes_secundarios') or '').split(',') if c.strip()])} códigos de atividade"),
        (str(total_dentro), "dentro da capacidade", f"limite: {_currency_short(cap_10x)} (10× capital social)"),
        (str(total_analisados), "analisados em profundidade", "documentos baixados e revisados individualmente"),
        (str(total_recomendados), "RECOMENDADOS", "viabilidade técnica e econômica confirmada"),
    ]

    rows = []
    for count, label, detail in funnel_steps:
        rows.append([
            Paragraph(f"<b>{count}</b>", ParagraphStyle("fc", fontName="Times-Bold", fontSize=14, textColor=INK, alignment=TA_RIGHT, leading=18)),
            Paragraph(f"<b>{label}</b>", ParagraphStyle("fl", fontName="Helvetica", fontSize=9, textColor=TEXT_COLOR, leading=12)),
            Paragraph(detail, ParagraphStyle("fd", fontName="Helvetica", fontSize=7.5, textColor=TEXT_SECONDARY, leading=10)),
        ])

    # Arrow rows between steps
    final_rows = []
    for i, row in enumerate(rows):
        final_rows.append(row)
        if i < len(rows) - 1:
            final_rows.append([
                Paragraph("", styles["cell"]),
                Paragraph("↓", ParagraphStyle("arrow", fontName="Helvetica", fontSize=8, textColor=TEXT_MUTED, alignment=TA_LEFT, leading=10)),
                Paragraph("", styles["cell"]),
            ])

    col_widths = [45, avail * 0.35, avail - 45 - avail * 0.35]
    t = Table(final_rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, -1), 8),
        # Last row highlight (green background)
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8F5E9")),
        ("ROUNDEDCORNERS", [0, 0, 0, 0]),
    ]))
    el.append(t)

    el.append(Spacer(1, 3 * mm))
    el.append(Paragraph(
        "<i>A planilha Excel contém todos os editais compatíveis com a empresa para análise própria.</i>",
        styles["italic_note"],
    ))

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
    _participar = [e for e in top20 if (e.get("analise") or {}).get("recomendacao_acao", "").upper().startswith("PARTICIPAR")]
    recomendados = len(_participar)

    valor_total = sum(_safe_float(e.get("valor_estimado")) for e in _participar)

    avail = PAGE_WIDTH - 2 * MARGIN
    col_w = avail / 4
    metrics_row = [[
        _metric_cell(str(total_compat), "Compatíveis com a Empresa", styles),
        _metric_cell(str(dentro_capacidade), "Dentro da Capacidade", styles),
        _metric_cell(str(recomendados), "Recomendados", styles),
        _metric_cell(_currency_short(valor_total), "Valor Total Recomendado", styles),
    ]]
    metrics_t = Table(metrics_row, colWidths=[col_w, col_w, col_w, col_w])
    metrics_t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    el.append(metrics_t)
    el.append(Spacer(1, 6 * mm))

    # Resumo executivo text — ALWAYS computed from data (never from JSON field)
    # Use raw top20 (includes NAO PARTICIPAR) for accurate counting
    raw_top20 = data.get("top20_raw", top20)
    top20_with_analise = [e for e in raw_top20 if e.get("analise")]
    resumo = _generate_resumo(
        data.get("empresa", {}),
        top20_with_analise,
        estatisticas,
    )
    for paragraph in resumo.split("\n\n"):
        paragraph = paragraph.strip()
        if paragraph:
            el.append(Paragraph(_s(paragraph), styles["body"]))

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
            Paragraph("Prazo", styles["cell_header_center"]),
        ]
        rows = [header]
        for idx, ed in enumerate(top5, 1):
            link = _fix_pncp_link(ed.get("link_pncp") or ed.get("link") or ed.get("link_edital", ""))
            obj_text = _smart_trunc(ed.get("objeto", ""), 55)
            if link:
                obj_text = f'<a href="{link}" color="#1a56db">{obj_text}</a>'
            rows.append([
                Paragraph(str(idx), styles["cell_center"]),
                Paragraph(obj_text, styles["cell"]),
                Paragraph(_currency_short(ed.get("valor_estimado")), styles["cell_right"]),
                Paragraph(_s(ed.get("uf", "")), styles["cell_center"]),
                Paragraph(_date(ed.get("data_encerramento_proposta") or ed.get("data_abertura_proposta") or ed.get("data_abertura") or ed.get("data_publicacao")), styles["cell_center"]),
            ])
        widths = [20, avail - 20 - 70 - 30 - 55, 70, 30, 55]
        el.append(_three_rule_table(rows, widths))

    # Quality Seal
    quality = data.get("quality_stats", {})
    completeness = quality.get("completeness_pct", 0)
    seal_color = SIGNAL_GREEN if completeness >= 80 else SIGNAL_AMBER if completeness >= 60 else SIGNAL_RED
    seal_text = f"Completude dos dados: {completeness}%"
    if data.get("empresa", {}).get("sicaf"):
        seal_text += " | SICAF: Verificado"
    if data.get("empresa", {}).get("sancionada") is False:
        seal_text += " | Sanções: Nenhuma"

    el.append(Spacer(1, 4 * mm))
    el.append(Paragraph(seal_text, ParagraphStyle(
        "QualitySeal", parent=styles["caption"],
        textColor=seal_color, fontSize=7,
    )))

    el.extend(_build_funil(data, styles))

    el.append(PageBreak())
    return el


def _build_delta_section(data: dict, styles: dict) -> list:
    """Delta section: changes since last analysis run."""
    meta = data.get("meta", {})
    delta = meta.get("_delta_summary") if isinstance(meta, dict) else None
    if not delta or not isinstance(delta, dict):
        return []

    el: list = []
    avail = PAGE_WIDTH - 2 * MARGIN

    data_anterior = _s(delta.get("data_anterior", ""))
    titulo = f"Mudanças desde última análise ({data_anterior})" if data_anterior else "Mudanças desde última análise"
    el.extend(_section_heading(titulo, styles))
    el.append(Spacer(1, 2 * mm))

    novos = delta.get("novos", 0)
    atualizados = delta.get("atualizados", 0)
    vencendo = delta.get("vencendo_3dias", 0)
    sem_alteracao = delta.get("sem_alteracao", 0)

    # Green bullet — novos
    if novos > 0:
        el.append(Paragraph(
            f'<font color="{SIGNAL_GREEN.hexval()}">●</font> '
            f'<b>{novos}</b> {_plural(novos, "novo edital identificado", "novos editais identificados")}',
            styles["bullet"],
        ))

    # Blue bullet — atualizados
    if atualizados > 0:
        el.append(Paragraph(
            f'<font color="{LINK_BLUE.hexval()}">●</font> '
            f'<b>{atualizados}</b> {_plural(atualizados, "edital com valor atualizado", "editais com valor atualizado")}',
            styles["bullet"],
        ))

    # Red bullet — vencendo (bold)
    if vencendo > 0:
        el.append(Paragraph(
            f'<font color="{SIGNAL_RED.hexval()}">●</font> '
            f'<b>{vencendo}</b> {_plural(vencendo, "edital vencendo em até 3 dias", "editais vencendo em até 3 dias")}',
            ParagraphStyle(
                "delta_urgent", parent=styles["bullet"],
                fontName="Times-Bold",
            ),
        ))

    # Gray bullet — sem alteração (smaller)
    if sem_alteracao > 0:
        el.append(Paragraph(
            f'<font color="{TEXT_MUTED.hexval()}">●</font> '
            f'{sem_alteracao} {_plural(sem_alteracao, "edital sem alteração", "editais sem alteração")}',
            styles["bullet_small"],
        ))

    # Red alert box if vencendo > 0
    if vencendo > 0:
        el.append(Spacer(1, 3 * mm))
        alert_text = (
            f'<b>AÇÃO IMEDIATA:</b> {vencendo} '
            f'{_plural(vencendo, "edital encerra", "editais encerram")} em até 3 dias'
        )
        alert_para = Paragraph(alert_text, ParagraphStyle(
            "delta_alert", parent=styles["body"],
            fontName="Helvetica-Bold", fontSize=9, textColor=colors.white,
            leading=12,
        ))
        alert_table = Table([[alert_para]], colWidths=[avail - 10 * mm])
        alert_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SIGNAL_RED),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("ROUNDEDCORNERS", [3, 3, 3, 3]),
        ]))
        el.append(alert_table)

    el.append(Spacer(1, 4 * mm))
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
            Paragraph("Atividade Principal", styles["cell_header"]),
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
                # Avoid duplicate CRC if sicaf_status already contains it
                if "CRC:" not in sicaf_status:
                    sicaf_text += f" — CRC: {crc_status}"
                else:
                    # Deduplicate: keep first CRC mention, append Restrições if present
                    crc_m = re.search(r"CRC:\s*[^,—]+", sicaf_status)
                    rest_m = re.search(r"Restrições:\s*[^,—]+", sicaf_status)
                    parts = []
                    base = sicaf_status.split("CRC:")[0].strip().rstrip("—").rstrip(" —").strip()
                    if base:
                        parts.append(base)
                    if crc_m:
                        parts.append(crc_m.group(0).strip())
                    if rest_m:
                        parts.append(rest_m.group(0).strip())
                    sicaf_text = " — ".join(parts) if parts else sicaf_status

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
                sancoes_text = '<font color="#1B7A3D">Nenhuma sanção ativa nos cadastros federais</font>'

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

    # Only show editais that have analise populated
    top20_pdf = [e for e in top20 if e.get("analise")]

    if top20_pdf:
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
        for idx, ed in enumerate(top20_pdf, 1):
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
            obj_text = _smart_trunc(ed.get("objeto", ""), 40)
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

    # Title (clickable link to PNCP) + NOVO badge if delta status
    objeto = _smart_trunc(ed.get("objeto", "Sem objeto"), 80)
    link = _fix_pncp_link(ed.get("link") or ed.get("link_pncp") or ed.get("link_edital", ""))
    delta_status = ed.get("_delta_status", "")
    novo_badge = ""
    if delta_status == "NOVO":
        novo_badge = f' <font color="{SIGNAL_GREEN.hexval()}" size="8"><b>[NOVO]</b></font>'
    if link:
        title_text = f'#{idx} — <a href="{link}" color="#1a56db">{objeto}</a>{novo_badge}'
    else:
        title_text = f"#{idx} — {objeto}{novo_badge}"
    elements.append(Paragraph(title_text, styles["edital_title"]))

    # Metadata line
    orgao = _s(ed.get("orgao") or ed.get("nomeOrgao", ""))
    uf = _s(ed.get("uf", ""))
    municipio = _s(ed.get("municipio", ""))
    modalidade = _s(ed.get("modalidade", ""))
    loc = f"{uf} — {municipio}" if municipio else uf
    meta_parts = [p for p in [orgao, loc, modalidade] if p]

    # Enhancement 3: cnae_confidence + victory_fit_label in metadata row
    cnae_conf = ed.get("cnae_confidence")
    if cnae_conf is not None:
        try:
            cnae_pct = int(float(cnae_conf) * 100) if float(cnae_conf) <= 1 else int(float(cnae_conf))
        except (ValueError, TypeError):
            cnae_pct = None
        if cnae_pct is not None:
            conf_color = SIGNAL_GREEN if cnae_pct >= 70 else SIGNAL_AMBER if cnae_pct >= 40 else SIGNAL_RED
            meta_parts.append(f'<font color="{conf_color.hexval()}">Compatibilidade: {cnae_pct}%</font>')

    fit_label = ed.get("_victory_fit_label")
    if not fit_label:
        # Derive from cnae_confidence when _victory_fit_label is absent
        _cnae_c = ed.get("cnae_confidence")
        if _cnae_c is not None:
            try:
                _cnae_v = float(_cnae_c)
            except (ValueError, TypeError):
                _cnae_v = 0.5
            fit_label = "Alto" if _cnae_v >= 0.9 else ("Moderado" if _cnae_v >= 0.6 else "Baixo")
        else:
            fit_label = "Moderado"
    fit_upper = str(fit_label).upper()
    fit_color = (
        SIGNAL_GREEN if fit_upper in ("EXCELENTE", "ÓTIMO", "OTIMO", "ALTO") else
        SIGNAL_AMBER if fit_upper in ("BOM", "MODERADO") else
        SIGNAL_RED if fit_upper in ("BAIXO", "FRACO") else TEXT_SECONDARY
    )
    meta_parts.append(f'<font color="{fit_color.hexval()}">Aderência ao Perfil: {_s(fit_label)}</font>')

    if meta_parts:
        elements.append(Paragraph(" | ".join(meta_parts), styles["edital_meta"]))

    # Value + date line
    valor = _currency(ed.get("valor_estimado"))
    prazo_proposta = _date(ed.get("data_encerramento_proposta") or ed.get("data_abertura_proposta") or ed.get("data_abertura") or ed.get("data_publicacao"))

    # Status temporal badge
    status_t = ed.get("status_temporal", "")
    if status_t == "URGENTE":
        status_badge = f'<font color="{SIGNAL_RED.hexval()}">URGENTE — {ed.get("dias_restantes", "?")} dias</font>'
    elif status_t == "IMINENTE":
        status_badge = f'<font color="{SIGNAL_AMBER.hexval()}">IMINENTE — {ed.get("dias_restantes", "?")} dias</font>'
    elif status_t == "PLANEJAVEL":
        dias = ed.get("dias_restantes", "?")
        status_badge = f'<font color="{SIGNAL_GREEN.hexval()}">PLANEJÁVEL — {dias} dias</font>'
    elif status_t == "EXPIRADO":
        status_badge = f'<font color="{TEXT_MUTED.hexval()}">ENCERRADO</font>'
    else:
        status_badge = '<font color="#8896A6">Sem data de encerramento publicada — consultar edital</font>'

    elements.append(Paragraph(
        f"Valor Estimado: <b>{valor}</b> | Prazo Proposta: <b>{prazo_proposta}</b> | {status_badge}",
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

    # Calculate retorno label from actual ROI and distance
    _valor_est = _safe_float(ed.get("valor_estimado"))
    _custo_prop = cost_data.get("total") if isinstance(cost_data, dict) else None
    _dist_km_val = dist_data.get("km") if isinstance(dist_data, dict) else None
    _roi_ratio = (_valor_est / float(_custo_prop)) if _custo_prop and float(_custo_prop) > 0 else None

    if _roi_ratio is not None or (isinstance(roi_data, dict) and roi_data.get("classificacao")):
        # Derive retorno_label from ROI + distance
        if _roi_ratio is not None and _dist_km_val is not None:
            if _roi_ratio > 5000 and _dist_km_val < 300:
                retorno_label = "Retorno excelente"
                roi_color = "#1B7A3D"
            elif _roi_ratio > 2000 or _dist_km_val < 200:
                retorno_label = "Bom retorno"
                roi_color = "#1B7A3D"
            elif _dist_km_val > 500:
                retorno_label = "Retorno questionável"
                roi_color = "#B5342A"
            else:
                retorno_label = "Retorno moderado"
                roi_color = "#B8860B"
        elif isinstance(roi_data, dict) and roi_data.get("classificacao"):
            roi_class = roi_data["classificacao"]
            roi_color = "#1B7A3D" if roi_class in ("EXCELENTE", "BOM") else (
                "#B5342A" if roi_class in ("MARGINAL", "DESFAVORAVEL") else "#B8860B"
            )
            retorno_label = {
                "EXCELENTE": "Retorno excelente",
                "BOM": "Bom retorno",
                "MODERADO": "Retorno moderado",
                "MARGINAL": "Retorno marginal",
                "DESFAVORAVEL": "Retorno desfavorável",
            }.get(roi_class, roi_class)
        else:
            retorno_label = "Retorno moderado"
            roi_color = "#B8860B"
        geo_parts.append(f'<font color="{roi_color}"><b>{retorno_label}</b></font>')

    if isinstance(ibge_data, dict) and ibge_data.get("populacao"):
        pop = ibge_data["populacao"]
        pop_text = f"{pop:,}".replace(",", ".")
        geo_parts.append(f"Pop: {pop_text} hab")

    if geo_parts:
        elements.append(Paragraph(" | ".join(geo_parts), styles["edital_meta"]))

    # Sector-specific cost/distance warnings
    _roi_class = roi_data.get("classificacao", "") if isinstance(roi_data, dict) else ""
    _dist_km = dist_data.get("km") if isinstance(dist_data, dict) else None
    if _roi_class in ("MARGINAL", "DESFAVORAVEL"):
        elements.append(Paragraph(
            '<font color="' + SIGNAL_RED.hexval() + '"><b>Custo de participação elevado</b> — '
            'O investimento para participar desta licitação é alto em relação ao retorno potencial. '
            'Avaliar cuidadosamente antes de prosseguir.</font>',
            styles["edital_meta"],
        ))
    if _dist_km is not None and _dist_km > 1000:
        elements.append(Paragraph(
            '<font color="' + SIGNAL_AMBER.hexval() + '"><i>'
            'Logística de longa distância (' + f'{_dist_km:.0f}' + ' km) — avaliar custo-benefício'
            '</i></font>',
            styles["edital_meta"],
        ))

    # Link is already in the clickable title — no standalone link needed

    # --- Competitive Intelligence ---
    comp_intel = ed.get("competitive_intel", {})
    if isinstance(comp_intel, dict) and comp_intel.get("unique_suppliers"):
        comp_parts = []
        level = comp_intel.get("competition_level", "")
        level_color = {"BAIXA": SIGNAL_RED, "MEDIA": SIGNAL_AMBER, "ALTA": SIGNAL_GREEN, "MUITO_ALTA": SIGNAL_GREEN}
        color = level_color.get(level, TEXT_COLOR)

        level_label = {
            "BAIXA": "Poucos concorrentes",
            "MEDIA": "Concorrência moderada",
            "ALTA": "Muitos concorrentes",
            "MUITO_ALTA": "Concorrência intensa",
        }.get(level, level)
        comp_parts.append(f'<font color="{color.hexval()}"><b>{level_label}</b></font> ({comp_intel["unique_suppliers"]} fornecedores no órgão)')

        top_sup = comp_intel.get("top_suppliers", [])
        if top_sup:
            top_name = top_sup[0].get("nome", "")[:40]
            top_share = top_sup[0].get("share", 0)
            comp_parts.append(f"Incumbente: {top_name} ({top_share:.0%})")

        hhi = comp_intel.get("hhi", 0)
        if hhi > 0.5:
            comp_parts.append(f'<font color="{SIGNAL_RED.hexval()}"><b>Mercado dominado por poucos fornecedores</b></font>')
        elif hhi > 0.25:
            comp_parts.append("Mercado com fornecedores recorrentes")

        elements.append(Paragraph(" | ".join(comp_parts), styles["edital_meta"]))

    # --- Price Benchmark ---
    benchmark = ed.get("price_benchmark", {})
    if isinstance(benchmark, dict) and benchmark.get("contratos_analisados", 0) >= 3:
        val_min = benchmark.get("valor_sugerido_min")
        val_max = benchmark.get("valor_sugerido_max")
        desc_med = benchmark.get("desconto_mediano_orgao", 0)
        n = benchmark.get("contratos_analisados", 0)

        bench_text = f"Faixa de lance sugerida: <b>{_currency_short(val_min)} — {_currency_short(val_max)}</b>"
        bench_text += f" | Desconto mediano do órgão: <b>{desc_med:.0%}</b> (base: {n} contratos)"

        elements.append(Paragraph(bench_text, styles["edital_meta"]))

    # --- Bid Simulation ---
    bid_sim = ed.get("_bid_simulation", {})
    _bid_desconto = bid_sim.get("desconto_pct", 0) if isinstance(bid_sim, dict) else 0
    _bid_confianca = (bid_sim.get("confianca") or "").upper() if isinstance(bid_sim, dict) else ""
    _bid_skip = (isinstance(_bid_desconto, (int, float)) and _bid_desconto == 0 and _bid_confianca in ("INSUFICIENTE", ""))
    if isinstance(bid_sim, dict) and bid_sim.get("lance_sugerido") is not None and not _bid_skip:
        elements.append(Paragraph("SIMULAÇÃO DE LANCE", styles["subsection"]))

        lance = _currency(bid_sim.get("lance_sugerido"))
        desconto = bid_sim.get("desconto_pct", 0)
        desc_text = f"{desconto:.1f}%" if isinstance(desconto, (int, float)) else str(desconto)
        elements.append(Paragraph(
            f"Lance sugerido: <b>{lance}</b> (desconto {desc_text})",
            styles["bullet"],
        ))

        # Range: agressivo — conservador
        val_agr = bid_sim.get("lance_agressivo")
        val_cons = bid_sim.get("lance_conservador")
        desc_agr = bid_sim.get("desconto_agressivo_pct")
        desc_cons = bid_sim.get("desconto_conservador_pct")
        if val_agr is not None and val_cons is not None:
            agr_desc = f", desc {desc_agr:.1f}%" if isinstance(desc_agr, (int, float)) else ""
            cons_desc = f", desc {desc_cons:.1f}%" if isinstance(desc_cons, (int, float)) else ""
            elements.append(Paragraph(
                f"Faixa: {_currency(val_agr)} (agressivo{agr_desc}) a {_currency(val_cons)} (conservador{cons_desc})",
                styles["bullet_small"],
            ))

        # P(vitória)
        p_vitoria = bid_sim.get("probabilidade_vitoria")
        if p_vitoria is not None:
            try:
                pv = float(p_vitoria)
                pv_pct = pv * 100 if pv <= 1 else pv
            except (ValueError, TypeError):
                pv_pct = None
            if pv_pct is not None:
                pv_color = SIGNAL_GREEN if pv_pct >= 50 else SIGNAL_AMBER if pv_pct >= 30 else SIGNAL_RED
                elements.append(Paragraph(
                    f'P(vitória) estimada: <font color="{pv_color.hexval()}"><b>{pv_pct:.0f}%</b></font>',
                    styles["bullet"],
                ))

        # Margem líquida
        margem = bid_sim.get("margem_liquida_pct")
        if margem is not None:
            try:
                m_text = f"{float(margem):.1f}%"
            except (ValueError, TypeError):
                m_text = str(margem)
            elements.append(Paragraph(
                f"Margem líquida projetada: {m_text}",
                styles["bullet_small"],
            ))

        # Confidence note
        n_contratos = bid_sim.get("contratos_base", 0)
        confianca = _s(bid_sim.get("confianca", ""))
        note_parts = []
        if n_contratos:
            note_parts.append(f"Baseado em {n_contratos} contratos do órgão")
        if confianca:
            note_parts.append(f"Confiança: {confianca.upper()}")
        if note_parts:
            elements.append(Paragraph(
                ". ".join(note_parts),
                styles["caption"],
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
    # Only render editais that have analise populated
    top20_pdf = [e for e in top20 if e.get("analise")]

    if not top20_pdf:
        return el

    el.extend(_section_heading("Análise Individual", styles))
    el.append(Spacer(1, 2 * mm))

    for idx, ed in enumerate(top20_pdf, 1):
        detail = _build_edital_detail(idx, ed, styles)
        # Use KeepTogether to avoid splitting a single edital across pages
        el.append(KeepTogether(detail))

    el.append(PageBreak())
    return el



def _build_proximos_passos(data: dict, styles: dict) -> list:
    """Render Próximos Passos section — ALWAYS computed from top20 data."""
    top20 = data.get("top20", [])
    top20_pdf = [e for e in top20 if e.get("analise")]

    # Generate passos deterministically from data (ignore JSON proximos_passos field)
    valid_passos = _generate_proximos_passos(top20_pdf)
    if not valid_passos:
        return []

    el: list = []
    avail = PAGE_WIDTH - 2 * MARGIN

    el.extend(_section_heading("Próximos Passos", styles))
    el.append(Spacer(1, 2 * mm))

    # Map priority labels to internal priority levels
    _PRIO_MAP = {"URGENTE": "URGENTE", "PRIORITÁRIO": "ALTA", "MONITORAR": "BAIXA", "AVALIAR": "MEDIA"}
    for p in valid_passos:
        p["_priority"] = _PRIO_MAP.get(p.get("prioridade", ""), "MEDIA")

    # Sort by priority
    _PRIORITY_ORDER = {"URGENTE": 0, "ALTA": 1, "MEDIA": 2, "BAIXA": 3}
    valid_passos.sort(key=lambda x: _PRIORITY_ORDER.get(x["_priority"], 2))

    # Priority colors
    _PRIORITY_COLORS = {
        "URGENTE": SIGNAL_RED,
        "ALTA": SIGNAL_AMBER,
        "MEDIA": TEXT_COLOR,
        "BAIXA": TEXT_MUTED,
    }

    # Build table
    header = [
        Paragraph("#", styles["cell_header_center"]),
        Paragraph("Ação", styles["cell_header"]),
        Paragraph("Prazo", styles["cell_header_center"]),
        Paragraph("Prioridade", styles["cell_header_center"]),
    ]
    rows = [header]
    for idx, p in enumerate(valid_passos, 1):
        prio = p["_priority"]
        prio_color = _PRIORITY_COLORS.get(prio, TEXT_COLOR)
        prio_style = ParagraphStyle(
            f"prio_{idx}", parent=styles["cell_center"],
            textColor=prio_color, fontName="Helvetica-Bold",
        )
        rows.append([
            Paragraph(str(idx), styles["cell_center"]),
            Paragraph(_s(p["acao"]), styles["cell"]),
            Paragraph(_s(p["prazo"]) or "—", styles["cell_center"]),
            Paragraph(prio, prio_style),
        ])

    widths = [20, avail - 20 - 65 - 65, 65, 65]
    el.append(_three_rule_table(rows, widths))
    el.append(Spacer(1, 4 * mm))

    return el


def _build_consorcio_section(data: dict, styles: dict) -> list:
    """Render consortium opportunities -- tenders above 10x capacity but relevant."""
    opportunities = data.get("consorcio_opportunities", [])
    if not opportunities:
        return []

    el: list = []
    avail = PAGE_WIDTH - 2 * MARGIN

    el.extend(_section_heading("Oportunidades de Consórcio", styles))
    el.append(Spacer(1, 2 * mm))

    el.append(Paragraph(
        "Os editais abaixo excedem a capacidade econômico-financeira individual da empresa, "
        "mas são relevantes para o setor. Considere participação via consórcio.",
        styles["body_small"],
    ))
    el.append(Spacer(1, 2 * mm))

    # Show up to 5 items
    items = opportunities[:5]
    header = [
        Paragraph("#", styles["cell_header_center"]),
        Paragraph("Objeto", styles["cell_header"]),
        Paragraph("Valor", styles["cell_header_right"]),
        Paragraph("Município/UF", styles["cell_header_center"]),
        Paragraph("Interesse", styles["cell_header"]),
    ]
    rows = [header]
    for idx, opp in enumerate(items, 1):
        obj_text = _smart_trunc(opp.get("objeto", ""), 40)
        link = _fix_pncp_link(opp.get("link") or opp.get("link_edital", ""))
        if link:
            obj_text = '<a href="' + link + '" color="#1a56db">' + obj_text + '</a>'
        mun = _s(opp.get("municipio", ""))
        uf = _s(opp.get("uf", ""))
        loc = f"{mun}/{uf}" if mun else uf
        motivo = _s(opp.get("motivo_interesse") or opp.get("motivo", "Setor compatível"))
        rows.append([
            Paragraph(str(idx), styles["cell_center"]),
            Paragraph(obj_text, styles["cell"]),
            Paragraph(_currency_short(opp.get("valor_estimado")), styles["cell_right"]),
            Paragraph(loc, styles["cell_center"]),
            Paragraph(_trunc(motivo, 40), styles["cell"]),
        ])

    widths = [18, avail - 18 - 60 - 65 - 100, 60, 65, 100]
    el.append(_three_rule_table(rows, widths))
    el.append(Spacer(1, 4 * mm))

    return el

def _build_plano_acao(data: dict, styles: dict) -> list:
    """Cronograma de Prazos (timeline table only — Plano de Ação removed per FALHA 8)."""
    el: list = []
    top20 = data.get("top20", [])
    avail = PAGE_WIDTH - 2 * MARGIN

    # Timeline table
    if top20:
        el.append(Paragraph("Cronograma de Prazos", styles["h2"]))

        header = [
            Paragraph("#", styles["cell_header_center"]),
            Paragraph("Edital", styles["cell_header"]),
            Paragraph("Sessão", styles["cell_header_center"]),
            Paragraph("Ação Prioritária", styles["cell_header"]),
            Paragraph("Dificuldade", styles["cell_header_center"]),
        ]
        rows = [header]

        def _extract_sessao_date(ed_item: dict) -> str:
            """Extract session date for sorting — priority: analise fields > edital fields."""
            a = ed_item.get("analise") or {}
            # Try analise date fields first (may contain "DD/MM/YYYY as HH:MMh" format)
            for field in ("data_sessao", "prazo_proposta"):
                val = a.get(field, "")
                if val:
                    m = re.search(r"(\d{2}/\d{2}/\d{4})", str(val))
                    if m:
                        # Convert DD/MM/YYYY to YYYY-MM-DD for sorting
                        parts = m.group(1).split("/")
                        return f"{parts[2]}-{parts[1]}-{parts[0]}"
            return ed_item.get("data_abertura_proposta") or ed_item.get("data_abertura") or ed_item.get("data_publicacao") or "9999"

        # Sort by session date (earliest first)
        sorted_eds = sorted(
            enumerate(top20, 1),
            key=lambda x: _extract_sessao_date(x[1]),
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
            obj_text = _smart_trunc(ed.get("objeto", ""), 40)
            if link:
                obj_text = f'<a href="{link}" color="#1a56db">{obj_text}</a>'
            rows.append([
                Paragraph(str(orig_idx), styles["cell_center"]),
                Paragraph(obj_text, styles["cell"]),
                Paragraph(_date(_extract_sessao_date(ed)), styles["cell_center"]),
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
        # Skip expired editais
        if e.get("status_temporal") == "EXPIRADO":
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
    # Keep raw top20 for resumo counting (needs NAO PARTICIPAR count)
    data["top20_raw"] = raw_top20
    # Use filtered list for Mapa + Análise Individual sections
    data["top20"] = filtered_top20

    # ── Quality Gate: Validate completeness ──
    REQUIRED_FIELDS = ["data_sessao", "criterio_julgamento", "regime_execucao", "consorcio", "recomendacao_acao"]
    FORBIDDEN_WORDS = ["verificar", "possivelmente", "buscar edital", "não detalhado", "a confirmar"]

    quality_stats = {
        "total_editais": len(filtered_top20),
        "campos_completos": 0,
        "campos_total": 0,
        "editais_completos": 0,
        "warnings": [],
    }

    for e in filtered_top20:
        analise = e.get("analise", {})
        edital_complete = True
        for field in REQUIRED_FIELDS:
            quality_stats["campos_total"] += 1
            val = (analise.get(field) or "").lower()
            has_forbidden = any(fw in val for fw in FORBIDDEN_WORDS)
            is_empty = not val or val == "n/a"
            if has_forbidden or is_empty:
                edital_complete = False
                obj_short = (e.get("objeto") or "")[:50]
                quality_stats["warnings"].append(f"{obj_short}: campo '{field}' incompleto")
            else:
                quality_stats["campos_completos"] += 1
        if edital_complete:
            quality_stats["editais_completos"] += 1

    total_fields = quality_stats["campos_total"]
    complete_fields = quality_stats["campos_completos"]
    completeness_pct = round(complete_fields / total_fields * 100) if total_fields > 0 else 0
    quality_stats["completeness_pct"] = completeness_pct
    data["quality_stats"] = quality_stats

    # Print quality report
    print(f"  Qualidade: {completeness_pct}% campos completos ({complete_fields}/{total_fields})")
    print(f"  Editais 100% completos: {quality_stats['editais_completos']}/{quality_stats['total_editais']}")
    if quality_stats["warnings"]:
        print(f"  Warnings ({len(quality_stats['warnings'])}):")
        for w in quality_stats["warnings"][:10]:
            print(f"    - {w}")

    styles = _build_styles()
    elements: list = []

    # Page 1: Cover
    elements.extend(_build_cover(data, styles))

    # Page 2: Sumário Executivo
    elements.extend(_build_sumario_executivo(data, styles))

    # Delta section (changes since last run) — after executive summary
    elements.extend(_build_delta_section(data, styles))

    # Page 3: Perfil + Mapa
    elements.extend(_build_perfil_e_mapa(data, styles))

    # Pages 4-13: Análise Individual
    elements.extend(_build_analise_individual(data, styles))

    # Próximos Passos (priority-grouped action items)
    elements.extend(_build_proximos_passos(data, styles))

    # Consortium opportunities (above capacity but relevant)
    elements.extend(_build_consorcio_section(data, styles))

    # Plano de Ação (timeline + final notes)
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
