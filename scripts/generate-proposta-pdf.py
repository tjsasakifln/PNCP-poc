"""
Gerador de PDF de Proposta Comercial B2G
Usa reportlab para gerar PDF profissional a partir do JSON de dados.
v3 — Conteúdo 100% dinâmico do JSON, fix_accents(), CTA de alta conversão,
     seção de autoridade reescrita, KeepTogether, argparse, --pacote.
"""
import argparse
import datetime
import json
import re
import sys
from collections import Counter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)

# --- Dimensions ---
PAGE_W, PAGE_H = A4
MARGIN = 20 * mm
CONTENT_W = PAGE_W - 2 * MARGIN  # ~170mm

# --- Colors ---
NAVY = HexColor("#1a365d")
DARK_BLUE = HexColor("#2c5282")
MEDIUM_BLUE = HexColor("#3182ce")
LIGHT_BLUE = HexColor("#ebf8ff")
LIGHT_GRAY = HexColor("#f7fafc")
MEDIUM_GRAY = HexColor("#e2e8f0")
DARK_GRAY = HexColor("#2d3748")
WHITE = white

FOOTER_TEXT = "Tiago Sasaki — Consultor de Licitações (48) 9 8834-4559"

# ---------------------------------------------------------------------------
# Accent fixer — JSON data arrives WITHOUT accents (pure ASCII PT-BR)
# ---------------------------------------------------------------------------
_ACCENT_MAP = [
    # -ção / -ções endings (most common)
    (r"\bExecucao\b", "Execução"), (r"\bexecucao\b", "execução"),
    (r"\bmovimentacao\b", "movimentação"), (r"\bMovimentacao\b", "Movimentação"),
    (r"\bConstrucao\b", "Construção"), (r"\bconstrucao\b", "construção"),
    (r"\bPavimentacao\b", "Pavimentação"), (r"\bpavimentacao\b", "pavimentação"),
    (r"\blicitacao\b", "licitação"), (r"\bLicitacao\b", "Licitação"),
    (r"\blicitacoes\b", "licitações"), (r"\bLicitacoes\b", "Licitações"),
    (r"\bcompeticao\b", "competição"), (r"\bCompeticao\b", "Competição"),
    (r"\bhabitacao\b", "habitação"), (r"\bHabitacao\b", "Habitação"),
    (r"\bedificacao\b", "edificação"), (r"\bEdificacao\b", "Edificação"),
    (r"\brestricao\b", "restrição"), (r"\bRestricao\b", "Restrição"),
    (r"\bdeclaracao\b", "declaração"), (r"\bDeclaracao\b", "Declaração"),
    (r"\binstalacoes\b", "instalações"), (r"\bInstalacoes\b", "Instalações"),
    (r"\bcontratacao\b", "contratação"), (r"\bContratacao\b", "Contratação"),
    (r"\bcontratacoes\b", "contratações"), (r"\bContratacoes\b", "Contratações"),
    (r"\bConcorrencia\b", "Concorrência"), (r"\bconcorrencia\b", "concorrência"),
    (r"\bcomplementacao\b", "complementação"), (r"\bComplementacao\b", "Complementação"),
    (r"\bprecificacao\b", "precificação"), (r"\bPrecificacao\b", "Precificação"),
    (r"\bdiversificacao\b", "diversificação"),
    (r"\bparticipacao\b", "participação"), (r"\bParticipacao\b", "Participação"),
    (r"\biluminacao\b", "iluminação"),
    (r"\bimpugnacao\b", "impugnação"),
    (r"\bpreparacao\b", "preparação"),
    (r"\bmobilizacao\b", "mobilização"),
    (r"\bescavacao\b", "escavação"),
    (r"\binformacao\b", "informação"), (r"\binformacoes\b", "informações"),
    (r"\bsituacao\b", "situação"),
    (r"\bavaliacao\b", "avaliação"),
    (r"\bclassificacao\b", "classificação"),
    (r"\bobservacao\b", "observação"),
    (r"\bprojecao\b", "projeção"), (r"\bprojecoes\b", "projeções"),
    (r"\brecomendacao\b", "recomendação"),
    # -ão endings
    (r"\bpavilhao\b", "pavilhão"), (r"\bPavilhao\b", "Pavilhão"),
    (r"\borgao\b", "órgão"), (r"\bOrgao\b", "Órgão"),
    (r"\bPregao\b", "Pregão"), (r"\bpregao\b", "pregão"),
    (r"\bsessao\b", "sessão"), (r"\bSessao\b", "Sessão"),
    (r"\bpadrao\b", "padrão"), (r"\bPadrao\b", "Padrão"),
    (r"\bsao\b", "são"), (r"\bSao\b", "São"),
    (r"\bnao\b", "não"), (r"\bNao\b", "Não"),
    (r"\bentao\b", "então"),
    # -ência / -ância
    (r"\binteligencia\b", "inteligência"), (r"\bInteligencia\b", "Inteligência"),
    (r"\bfrequencia\b", "frequência"), (r"\bFrequencia\b", "Frequência"),
    (r"\breferencia\b", "referência"), (r"\bReferencia\b", "Referência"),
    (r"\bexperiencia\b", "experiência"), (r"\bExperiencia\b", "Experiência"),
    (r"\bexigencias\b", "exigências"), (r"\bExigencias\b", "Exigências"),
    (r"\bconcorrentes\b", "concorrentes"),  # correct already
    (r"\bCertidao\b", "Certidão"), (r"\bcertidao\b", "certidão"),
    (r"\bciencia\b", "ciência"),
    (r"\bvirgencia\b", "vigência"),
    (r"\bantecedencia\b", "antecedência"),
    (r"\bsuficiencia\b", "suficiência"),
    # -ível / -ável
    (r"\bcompativel\b", "compatível"), (r"\bCompativel\b", "Compatível"),
    (r"\bpossivel\b", "possível"), (r"\bPossivel\b", "Possível"),
    (r"\bdisponivel\b", "disponível"), (r"\bDisponivel\b", "Disponível"),
    (r"\bprovavel\b", "provável"), (r"\bProvavel\b", "Provável"),
    (r"\bfactivel\b", "factível"),
    (r"\bacessivel\b", "acessível"),
    # -ico / -ica / -icos
    (r"\bgenericos\b", "genéricos"), (r"\bGenerico\b", "Genérico"),
    (r"\blogistico\b", "logístico"), (r"\bLogistico\b", "Logístico"),
    (r"\bespecifico\b", "específico"), (r"\bEspecifico\b", "Específico"),
    (r"\bespecifica\b", "específica"), (r"\bespecificos\b", "específicos"),
    (r"\basfaltica\b", "asfáltica"), (r"\bAsfaltica\b", "Asfáltica"),
    (r"\bhidraulicas\b", "hidráulicas"), (r"\bHidraulicas\b", "Hidráulicas"),
    (r"\beletrica\b", "elétrica"), (r"\bEletrica\b", "Elétrica"),
    (r"\beletricas\b", "elétricas"),
    (r"\btecnica\b", "técnica"), (r"\bTecnica\b", "Técnica"),
    (r"\btecnico\b", "técnico"), (r"\bTecnico\b", "Técnico"),
    (r"\bjuridica\b", "jurídica"), (r"\bJuridica\b", "Jurídica"),
    (r"\beletronico\b", "eletrônico"), (r"\bEletronico\b", "Eletrônico"),
    (r"\beletronica\b", "eletrônica"), (r"\bEletronica\b", "Eletrônica"),
    # -ário / -ária
    (r"\borcamentaria\b", "orçamentária"), (r"\bOrcamentaria\b", "Orçamentária"),
    (r"\bsecundarios\b", "secundários"),
    (r"\bnecessario\b", "necessário"),
    (r"\bhabitacionais\b", "habitacionais"),  # correct
    # Place names
    (r"\bDionisio\b", "Dionísio"),
    (r"\bJoacaba\b", "Joaçaba"),
    (r"\bChapeco\b", "Chapecó"),
    (r"\bBalneario\b", "Balneário"),
    # -ço / -ça
    (r"\bpreco\b", "preço"), (r"\bPreco\b", "Preço"),
    (r"\bprecos\b", "preços"),
    (r"\bservico\b", "serviço"), (r"\bservicos\b", "serviços"),
    (r"\bGoncalves\b", "Gonçalves"),
    # Misc
    (r"\bMunicipio\b", "Município"), (r"\bmunicipio\b", "município"),
    (r"\bmunicipios\b", "municípios"), (r"\bMunicipios\b", "Municípios"),
    # REMOVED: (r"\be\b(...)", "é") — too aggressive, converts "e" conjunction to "é" verb
    # e.g. "terra e drenagem" → "terra é drenagem" (WRONG). PT-BR "e" conjunction is far more common.
    (r"\buteis\b", "úteis"),
    (r"\bunico\b", "único"),
    (r"\bminimo\b", "mínimo"),
    (r"\bmaximo\b", "máximo"),
    (r"\bultimos\b", "últimos"),
    (r"\bultimo\b", "último"),
    (r"\bindice\b", "índice"), (r"\bindices\b", "índices"),
    (r"\bsolido\b", "sólido"),
    (r"\brobusto\b", "robusto"),  # correct
    (r"\bhistorico\b", "histórico"),
    (r"\bcontabil\b", "contábil"), (r"\bcontabeis\b", "contábeis"),
    (r"\bdotacao\b", "dotação"),
    (r"\bregiao\b", "região"),
    (r"\bnicho\b", "nicho"),  # correct
    (r"\bPropostas\b", "Propostas"),  # correct
    (r"\bhabilitacao\b", "habilitação"), (r"\bHabilitacao\b", "Habilitação"),
    (r"\binabilitacao\b", "inabilitação"), (r"\binabilitacoes\b", "inabilitações"),
    (r"\bsancoes\b", "sanções"), (r"\bSancoes\b", "Sanções"),
    (r"\bsancao\b", "sanção"),
    (r"\bCracas\b", "Praças"),  # unlikely but safe
    (r"\bPraca\b", "Praça"), (r"\bpraca\b", "praça"),
]

# Pre-compile for performance
_ACCENT_PATTERNS = [(re.compile(pat), repl) for pat, repl in _ACCENT_MAP]


def fix_accents(text):
    """Fix common missing PT-BR accents in text from JSON data."""
    if not text or not isinstance(text, str):
        return text or ""
    for pat, repl in _ACCENT_PATTERNS:
        text = pat.sub(repl, text)
    # Replace any remaining en-dashes with em-dashes
    text = text.replace("\u2013", "\u2014")
    return text


def fmt_date(iso_str):
    """Convert YYYY-MM-DD to DD/MM/YYYY."""
    if not iso_str:
        return ""
    try:
        parts = iso_str.split("-")
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    except (IndexError, AttributeError):
        return str(iso_str)


def fmt_value(v):
    """Format a numeric value as R$ with Brazilian formatting."""
    if v is None:
        return "R$ 0"
    v = float(v)
    if v >= 1_000_000:
        return f"R$ {v/1_000_000:,.1f}M".replace(",", "X").replace(".", ",").replace("X", ".")
    elif v >= 1_000:
        return f"R$ {v/1_000:,.0f}K".replace(",", ".")
    else:
        return f"R$ {v:,.0f}".replace(",", ".")


def fmt_value_full(v):
    """Format a numeric value as R$ with full precision."""
    if v is None:
        return "R$ 0,00"
    v = float(v)
    return "R$ {:,.2f}".format(v).replace(",", "X").replace(".", ",").replace("X", ".")


def detect_gender(name):
    """Heuristic gender detection for PT-BR first names. Returns 'Sr.' or 'Sra.'."""
    if not name:
        return "Sr."
    first = name.strip().split()[0].lower()
    female_endings = ("a", "e", "ane", "ene", "ine", "ice", "ilde", "ude")
    female_names = {
        "angela", "ana", "maria", "mariana", "juliana", "fernanda", "amanda",
        "patricia", "luciana", "adriana", "cristiane", "rosane", "eliane",
        "simone", "viviane", "diane", "aline", "caroline", "michele",
        "vanessa", "larissa", "beatriz", "roberta", "denise", "raquel",
        "claudia", "silvia", "sandra", "carla", "paula", "lucia",
        "tereza", "teresa", "marta", "rita", "sonia", "rosa",
        "irene", "alice", "helene", "elise", "renata", "camila",
        "leticia", "gabriela", "daniela", "rafaela", "isabela", "priscila",
        "tatiana", "fabiana", "luana", "bruna", "natalia",
    }
    male_names = {
        "andre", "alexandre", "felipe", "henrique", "jose", "dante",
        "jorge", "duarte", "vicente", "bruce", "jaime", "rique",
    }
    if first in male_names:
        return "Sr."
    if first in female_names:
        return "Sra."
    if first.endswith("a") or first.endswith("e"):
        return "Sra."
    return "Sr."


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def create_styles():
    styles = getSampleStyleSheet()
    add = styles.add

    add(ParagraphStyle(
        'CoverTitle', parent=styles['Title'],
        fontSize=26, leading=32, textColor=NAVY,
        spaceAfter=5 * mm, alignment=TA_CENTER, fontName='Helvetica-Bold',
    ))
    add(ParagraphStyle(
        'CoverSub', parent=styles['Normal'],
        fontSize=14, leading=18, textColor=DARK_BLUE,
        spaceAfter=4 * mm, alignment=TA_CENTER, fontName='Helvetica',
    ))
    add(ParagraphStyle(
        'H1', parent=styles['Heading1'],
        fontSize=15, leading=19, textColor=NAVY,
        spaceBefore=6 * mm, spaceAfter=3 * mm, fontName='Helvetica-Bold',
    ))
    add(ParagraphStyle(
        'H2', parent=styles['Heading2'],
        fontSize=12, leading=15, textColor=DARK_BLUE,
        spaceBefore=4 * mm, spaceAfter=2 * mm, fontName='Helvetica-Bold',
    ))
    add(ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=9.5, leading=13, textColor=DARK_GRAY,
        spaceAfter=2 * mm, fontName='Helvetica', alignment=TA_JUSTIFY,
    ))
    add(ParagraphStyle(
        'BodyBold', parent=styles['Normal'],
        fontSize=9.5, leading=13, textColor=DARK_GRAY,
        spaceAfter=2 * mm, fontName='Helvetica-Bold',
    ))
    add(ParagraphStyle(
        'Quote', parent=styles['Normal'],
        fontSize=9.5, leading=13, textColor=DARK_BLUE,
        spaceAfter=3 * mm, fontName='Helvetica-Oblique',
        leftIndent=8 * mm, rightIndent=8 * mm,
        borderWidth=1, borderColor=MEDIUM_BLUE,
        borderPadding=(5, 8, 5, 8), backColor=LIGHT_BLUE,
    ))
    add(ParagraphStyle(
        'Small', parent=styles['Normal'],
        fontSize=7.5, leading=10, textColor=HexColor("#718096"), fontName='Helvetica',
    ))
    # Cell styles for tables
    add(ParagraphStyle(
        'CellH', parent=styles['Normal'],
        fontSize=8.5, leading=11, textColor=WHITE,
        fontName='Helvetica-Bold', alignment=TA_CENTER,
    ))
    add(ParagraphStyle(
        'Cell', parent=styles['Normal'],
        fontSize=8.5, leading=11, textColor=DARK_GRAY, fontName='Helvetica',
    ))
    add(ParagraphStyle(
        'CellB', parent=styles['Normal'],
        fontSize=8.5, leading=11, textColor=DARK_GRAY, fontName='Helvetica-Bold',
    ))
    add(ParagraphStyle(
        'CellC', parent=styles['Normal'],
        fontSize=8.5, leading=11, textColor=DARK_GRAY,
        fontName='Helvetica', alignment=TA_CENTER,
    ))
    add(ParagraphStyle(
        'CTAWhite', parent=styles['Normal'],
        fontSize=11, leading=15, textColor=WHITE,
        fontName='Helvetica-Bold', alignment=TA_CENTER,
    ))
    add(ParagraphStyle(
        'CTAWhiteSub', parent=styles['Normal'],
        fontSize=9.5, leading=13, textColor=WHITE,
        fontName='Helvetica', alignment=TA_CENTER,
    ))
    add(ParagraphStyle(
        'BadgeWhite', parent=styles['Normal'],
        fontSize=9, leading=12, textColor=WHITE,
        fontName='Helvetica-Bold', alignment=TA_CENTER,
    ))
    return styles


S = None  # global ref set in build_pdf


def P(text, style='Cell'):
    """Wrap text in a Paragraph for proper word-wrap inside table cells."""
    return Paragraph(str(fix_accents(str(text))), S[style])


def make_table(headers, rows, col_widths, header_color=NAVY):
    """Table with Paragraph-wrapped cells for proper word-wrap."""
    hdr = [P(h, 'CellH') for h in headers]
    body = []
    for row in rows:
        body.append([P(c) if not isinstance(c, Paragraph) else c for c in row])
    data = [hdr] + body
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.4, MEDIUM_GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    return t


def make_kv(rows, kw=50 * mm):
    """Key-value 2-column table."""
    vw = CONTENT_W - kw
    data = [[P(k, 'CellB'), P(v)] for k, v in rows]
    t = Table(data, colWidths=[kw, vw])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.4, MEDIUM_GRAY),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [WHITE, LIGHT_GRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    return t


def hr():
    return HRFlowable(width="100%", thickness=0.8, color=MEDIUM_GRAY, spaceAfter=2 * mm, spaceBefore=2 * mm)


def bullet(text, style='Body'):
    return Paragraph("\u2022  " + fix_accents(text), S[style])


# ---------------------------------------------------------------------------
# PDF Builder
# ---------------------------------------------------------------------------

def build_pdf(data, output_path, pacote_recomendado="semanal"):
    global S
    S = create_styles()
    story = []

    emp = data["empresa"]
    editais = data["editais"]
    nome = emp.get("nome_fantasia", emp["razao_social"])
    nome = fix_accents(nome)

    # Decisor from QSA
    decisor_full = emp["qsa"][0]["nome"] if emp.get("qsa") else "Prezado(a) Diretor(a)"
    decisor_full = fix_accents(decisor_full)
    honorific = detect_gender(decisor_full)
    decisor_greeting = f"{honorific} {decisor_full}"

    cnpj = emp["cnpj"]
    cnaes_sec_str = emp.get("cnaes_secundarios", "")
    n_cnaes = len([c.strip() for c in cnaes_sec_str.split(",") if c.strip()]) if cnaes_sec_str else 0
    total_cnaes = n_cnaes + 1  # principal + secondary
    capital = float(emp.get("capital_social", 0))
    capital_fmt = fmt_value_full(capital)
    setor = fix_accents(data.get("setor", ""))

    # Computed values from editais
    today = datetime.date.today()
    today_fmt = today.strftime("%d/%m/%Y")
    validity_date = today + datetime.timedelta(days=15)
    validity_fmt = validity_date.strftime("%d/%m/%Y")

    n_editais = len(editais)
    participar = [e for e in editais if e.get("recomendacao") == "PARTICIPAR"]
    avaliar = [e for e in editais if e.get("recomendacao") == "AVALIAR COM CAUTELA"]
    n_participar = len(participar)
    n_avaliar = len(avaliar)
    n_compativeis = n_participar + n_avaliar
    total_valor = sum(float(e.get("valor_estimado", 0)) for e in editais)
    total_valor_fmt = fmt_value(total_valor)
    valor_medio = total_valor / n_editais if n_editais > 0 else 0

    # Sanctions check
    sancoes = emp.get("sancoes", {})
    tem_sancao = any(sancoes.get(k) for k in ("ceis", "cnep", "cepim", "ceaf"))
    sancoes_txt = "NENHUMA (CEIS, CNEP, CEPIM, CEAF)" if not tem_sancao else "VERIFICAR — sanção detectada"

    # Contratos
    contratos = emp.get("historico_contratos", [])
    contratos_txt = f"{len(contratos)} registrados" if contratos else "Nenhum registrado"

    # Municipality distribution
    mun_counter = Counter()
    mun_valor = {}
    for e in editais:
        m = fix_accents(e.get("municipio", "Desconhecido"))
        mun_counter[m] += 1
        mun_valor[m] = mun_valor.get(m, 0) + float(e.get("valor_estimado", 0))

    # Sort editais for top opportunities: PARTICIPAR first, then AVALIAR, by valor desc
    rec_order = {"PARTICIPAR": 0, "AVALIAR COM CAUTELA": 1, "NAO RECOMENDADO": 2}
    editais_sorted = sorted(editais, key=lambda e: (
        rec_order.get(e.get("recomendacao", ""), 9),
        -float(e.get("valor_estimado", 0))
    ))

    # First edital to close (soonest deadline)
    editais_by_deadline = sorted(editais, key=lambda e: e.get("data_encerramento", "9999-99-99"))
    primeiro_encerrar = editais_by_deadline[0] if editais_by_deadline else None

    # Best edital (first PARTICIPAR)
    melhor_edital = participar[0] if participar else editais_sorted[0] if editais_sorted else None

    # Resumo executivo
    resumo = data.get("resumo_executivo", {})
    resumo_texto = fix_accents(resumo.get("texto", ""))
    resumo_destaques = resumo.get("destaques", [])

    # Inteligência de mercado
    intel = data.get("inteligencia_mercado", {})

    # Próximos passos
    proximos = data.get("proximos_passos", [])

    # Company age (heuristic: not in JSON, so omit specific years)
    sede = f"{fix_accents(emp.get('cidade_sede', ''))}/{emp.get('uf_sede', '')}"

    # ==========================================================
    # CAPA
    # ==========================================================
    story.append(Spacer(1, 35 * mm))
    story.append(Paragraph("PROPOSTA DE CONSULTORIA", S['CoverTitle']))
    story.append(Paragraph("EM LICITAÇÕES PÚBLICAS", S['CoverTitle']))
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="50%", thickness=2, color=NAVY, spaceAfter=8 * mm, spaceBefore=4 * mm))
    story.append(Paragraph("Preparada exclusivamente para", S['CoverSub']))
    story.append(Paragraph(f"<b>{nome}</b>", S['CoverSub']))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(f"CNPJ: {cnpj}", S['CoverSub']))
    story.append(Spacer(1, 15 * mm))

    cover = [
        ["Data", today_fmt],
        ["Validade", f"15 dias (até {validity_fmt})"],
        ["Consultor", "Tiago Sasaki"],
        ["Contato", "(48) 9 8834-4559"],
    ]
    ct = Table([[P(a, 'CellB'), P(b, 'CellC')] for a, b in cover], colWidths=[35 * mm, 55 * mm])
    ct.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(ct)
    story.append(PageBreak())

    # ==========================================================
    # 1. CARTA AO DECISOR
    # ==========================================================
    carta_title = f"1. Carta {'à Decisora' if honorific == 'Sra.' else 'ao Decisor'}"
    story.append(Paragraph(carta_title, S['H1']))
    story.append(hr())
    story.append(Paragraph(f"{decisor_greeting},", S['BodyBold']))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        f"Como engenheiro da Secretaria de Estado da Infraestrutura de SC, acompanho diariamente o volume de obras "
        f"públicas licitadas no estado. Na minha atividade paralela de consultoria, faço o caminho inverso: "
        f"identifico, para empresas como a {nome}, quais dessas oportunidades têm aderência real ao perfil "
        f"técnico e financeiro da empresa.", S['Body']
    ))

    # Dynamic paragraph based on data
    melhor_mun = fix_accents(melhor_edital.get("municipio", "")) if melhor_edital else ""
    melhor_obj_short = fix_accents(melhor_edital.get("objeto", "")) if melhor_edital else ""
    melhor_valor = fmt_value(melhor_edital.get("valor_estimado", 0)) if melhor_edital else ""

    story.append(Paragraph(
        f"Nos últimos 30 dias, mapeei <b>{n_editais} editais abertos em {emp.get('uf_sede', 'SC')}</b> "
        f"diretamente compatíveis com os CNAEs da {nome}, totalizando <b>{total_valor_fmt} em valor estimado</b>. "
        f"O edital de {melhor_mun}, por exemplo, é de {melhor_obj_short.lower()} — "
        f"match direto com o CNAE principal da empresa, com competição estimada baixa.",
        S['Body']
    ))
    story.append(Paragraph(
        f"O objetivo desta proposta é apresentar um diagnóstico do mercado atual, as oportunidades "
        f"mapeadas, e uma opção de serviço de monitoramento contínuo que permita a {nome} "
        f"participar de forma sistemática do mercado de licitações.", S['Body']
    ))
    story.append(Paragraph(
        "Os dados são públicos. A análise é o diferencial.", S['BodyBold']
    ))
    story.append(PageBreak())

    # ==========================================================
    # 2. DIAGNÓSTICO DA EMPRESA
    # ==========================================================
    story.append(Paragraph("2. Diagnóstico da Empresa", S['H1']))
    story.append(hr())

    cnae_principal_txt = fix_accents(emp.get("cnae_principal", ""))
    story.append(make_kv([
        ["Razão Social", fix_accents(emp["razao_social"])],
        ["CNPJ", cnpj],
        ["CNAE Principal", cnae_principal_txt],
        ["CNAEs Secundários", f"{n_cnaes} CNAEs registrados"],
        ["Porte", fix_accents(emp.get("porte", ""))],
        ["Capital Social", capital_fmt],
        ["Sede", sede],
        [f"{'Sócia-Administradora' if honorific == 'Sra.' else 'Sócio-Administrador'}", decisor_full],
        ["Situação Cadastral", fix_accents(emp.get("situacao_cadastral", ""))],
        ["Sanções Gov.", sancoes_txt],
        ["Contratos Federais", contratos_txt],
    ]))
    story.append(Spacer(1, 3 * mm))

    # Pontos Fortes — derived from data
    story.append(Paragraph("Pontos Fortes", S['H2']))
    pontos_fortes = []
    if "terraplenagem" in cnae_principal_txt.lower() or "4313" in cnae_principal_txt:
        pontos_fortes.append("CNAE principal (terraplenagem) é o mais demandado em editais de infraestrutura de SC")
    elif cnae_principal_txt:
        pontos_fortes.append(f"CNAE principal ({cnae_principal_txt.split(' - ')[0]}) posiciona a empresa no setor de {setor}")

    if capital >= 5_000_000:
        pct_editais = sum(1 for e in editais if float(e.get("valor_estimado", 0)) <= capital) / max(n_editais, 1) * 100
        pontos_fortes.append(f"Capital de {fmt_value(capital)} permite participar de {pct_editais:.0f}% dos editais identificados")
    elif capital > 0:
        pontos_fortes.append(f"Capital social de {fmt_value(capital)}")

    if n_cnaes > 5:
        pontos_fortes.append(f"{total_cnaes} CNAEs (principal + {n_cnaes} secundários) cobrem escopo amplo")

    if not tem_sancao:
        pontos_fortes.append("Empresa ativa, sem nenhuma sanção governamental")

    for pf in pontos_fortes:
        story.append(bullet(pf))

    # Pontos de Atenção — derived from data
    story.append(Paragraph("Pontos de Atenção", S['H2']))
    pontos_atencao = []
    if not contratos:
        pontos_atencao.append("Zero contratos federais registrados")
    pontos_atencao.append("Nenhuma participação detectada nos editais abertos atuais")

    # Capital limitation
    editais_acima_capital = sum(1 for e in editais if float(e.get("valor_estimado", 0)) > capital)
    if editais_acima_capital > 0 and capital > 0:
        pontos_atencao.append(
            f"Capital limita editais acima de {fmt_value(capital)} "
            f"({editais_acima_capital} dos {n_editais} identificados)"
        )

    for pa in pontos_atencao:
        story.append(bullet(pa))

    story.append(Paragraph(
        f"A {nome} tem perfil técnico e financeiro compatível com a grande maioria dos editais "
        f"de infraestrutura em {emp.get('uf_sede', 'SC')}, mas não possui histórico registrado de participação. "
        f"Isso representa uma oportunidade significativa de diversificação de receita.",
        S['Quote']
    ))
    story.append(PageBreak())

    # ==========================================================
    # 3. RADIOGRAFIA DO MERCADO
    # ==========================================================
    story.append(Paragraph(f"3. Radiografia do Mercado — {emp.get('uf_sede', 'SC')} {setor}", S['H1']))
    story.append(hr())

    # Big numbers
    bn = Table(
        [[P(f"{n_editais}", 'CellB'), P(f"{n_compativeis}", 'CellB'), P(total_valor_fmt, 'CellB')],
         [P("Editais mapeados"), P("Compatíveis com o perfil"), P("Valor total em disputa")]],
        colWidths=[CONTENT_W / 3] * 3,
    )
    bn.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, 0), 18),
        ('TEXTCOLOR', (0, 0), (-1, 0), NAVY),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('BOX', (0, 0), (-1, -1), 1, MEDIUM_BLUE),
        ('LINEBEFORE', (1, 0), (1, -1), 0.5, MEDIUM_GRAY),
        ('LINEBEFORE', (2, 0), (2, -1), 0.5, MEDIUM_GRAY),
    ]))
    story.append(bn)
    story.append(Spacer(1, 4 * mm))

    # Distribuição por Município — dynamic
    story.append(Paragraph("Distribuição por Município", S['H2']))
    cw_mun = [48 * mm, 18 * mm, 32 * mm, 32 * mm]
    mun_rows = []
    for mun, count in mun_counter.most_common():
        valor_mun = mun_valor.get(mun, 0)
        mun_rows.append([mun, str(count), fmt_value(valor_mun), ""])
    story.append(make_table(
        ["Município", "Editais", "Valor Total", "Observação"],
        mun_rows, cw_mun
    ))
    story.append(Spacer(1, 3 * mm))

    # Tendências do Mercado — from JSON
    story.append(Paragraph("Tendências do Mercado", S['H2']))
    tendencias_txt = fix_accents(intel.get("tendencias", ""))
    if tendencias_txt:
        # Split on ". " to create bullet points
        frases = [f.strip() for f in tendencias_txt.split(". ") if f.strip()]
        for f in frases:
            if not f.endswith("."):
                f += "."
            story.append(bullet(f))
    story.append(PageBreak())

    # ==========================================================
    # 4. TOP OPORTUNIDADES
    # ==========================================================
    n_top = min(len(editais_sorted), 10)
    story.append(Paragraph(f"4. As {n_top} Melhores Oportunidades Abertas Agora", S['H1']))
    story.append(hr())

    top = editais_sorted[:n_top]
    # F2: New column widths — total = 170mm
    cw_top = [8 * mm, 68 * mm, 22 * mm, 22 * mm, 24 * mm, 26 * mm]
    top_rows = []
    for i, e in enumerate(top, 1):
        v = fmt_value(float(e.get("valor_estimado", 0)))
        mun = fix_accents(e.get("municipio", ""))
        obj = fix_accents(e.get("objeto", ""))
        # F2: município — objeto (em-dash), no truncation
        edital_cell = f"{mun} — {obj}"
        enc = fmt_date(e.get("data_encerramento", ""))
        comp = ""
        if isinstance(e.get("analise"), dict):
            comp_raw = fix_accents(e["analise"].get("competitividade", ""))
            comp = comp_raw.split(" - ")[0] if " - " in comp_raw else comp_raw.split(" — ")[0]
        rec = fix_accents(e.get("recomendacao", ""))
        top_rows.append([str(i), edital_cell, v, enc, comp, rec])

    story.append(make_table(
        ["#", "Edital", "Valor", "Encerra", "Competição", "Recomendação"],
        top_rows, cw_top
    ))
    story.append(Spacer(1, 3 * mm))

    # Dynamic highlight for best edital
    if melhor_edital:
        me_mun = fix_accents(melhor_edital.get("municipio", ""))
        me_obj = fix_accents(melhor_edital.get("objeto", ""))
        me_valor = fmt_value_full(float(melhor_edital.get("valor_estimado", 0)))
        me_analise = melhor_edital.get("analise", {})
        me_aderencia = fix_accents(me_analise.get("aderencia", ""))
        me_comp = fix_accents(me_analise.get("competitividade", ""))
        me_mod = fix_accents(melhor_edital.get("modalidade", ""))

        story.append(Paragraph(f"Destaque: {me_mun}", S['H2']))
        story.append(Paragraph(
            f"{me_obj}. Aderência: {me_aderencia}. "
            f"Modalidade: {me_mod}. Competitividade: {me_comp}. "
            f"Valor de {me_valor} — "
            f"{('compatível' if float(melhor_edital.get('valor_estimado', 0)) <= capital else 'acima')} "
            f"com capital de {fmt_value(capital)} "
            f"({float(melhor_edital.get('valor_estimado', 0))/capital*100:.0f}%)." if capital > 0 else "",
            S['Body']
        ))

    # Detect clusters (2+ editais same municipio)
    clusters = {m: c for m, c in mun_counter.items() if c >= 2}
    for cluster_mun, cluster_count in clusters.items():
        cluster_valor = mun_valor.get(cluster_mun, 0)
        story.append(Paragraph(f"Destaque: Cluster {cluster_mun}", S['H2']))
        story.append(Paragraph(
            f"{cluster_count} editais do mesmo órgão totalizando {fmt_value(cluster_valor)}. "
            f"Participar de todos permite estratégia de volume: uma única mobilização para o "
            f"município atende {cluster_count} contratos. Reduz custo logístico e aumenta a "
            f"probabilidade de retorno.",
            S['Body']
        ))
    story.append(PageBreak())

    # ==========================================================
    # 5. ANÁLISE DETALHADA — Edital Prioritário
    # ==========================================================
    story.append(Paragraph("5. Análise Detalhada — Edital Prioritário", S['H1']))
    story.append(hr())

    if melhor_edital:
        me = melhor_edital
        me_mun = fix_accents(me.get("municipio", ""))
        me_obj = fix_accents(me.get("objeto", ""))
        me_orgao = fix_accents(me.get("orgao", ""))
        me_valor_full = fmt_value_full(float(me.get("valor_estimado", 0)))
        me_mod = fix_accents(me.get("modalidade", ""))
        me_enc = fmt_date(me.get("data_encerramento", ""))
        me_link = me.get("link", "")

        story.append(Paragraph(f"Edital 1: {me_obj} — {me_mun}", S['H2']))
        story.append(make_kv([
            ["Órgão", me_orgao],
            ["Objeto", me_obj],
            ["Valor Estimado", me_valor_full],
            ["Modalidade", me_mod],
            ["Encerramento", me_enc],
            ["Link", me_link],
        ], kw=45 * mm))
        story.append(Spacer(1, 3 * mm))

        # Análise Estratégica from JSON
        me_analise = me.get("analise", {})
        if me_analise:
            story.append(Paragraph("Análise Estratégica", S['H2']))
            cw_str = [40 * mm, CONTENT_W - 40 * mm]
            analise_rows = []
            factor_labels = {
                "aderencia": "Aderência ao perfil",
                "valor": "Valor vs capacidade",
                "geografica": "Geografia",
                "prazo": "Prazo",
                "modalidade": "Modalidade",
                "competitividade": "Competitividade",
                "riscos": "Riscos",
            }
            for key, label in factor_labels.items():
                val = fix_accents(me_analise.get(key, ""))
                if val:
                    analise_rows.append([label, val])
            story.append(make_table(["Fator", "Avaliação"], analise_rows, cw_str))
            story.append(Spacer(1, 3 * mm))

        # Perguntas do Decisor from JSON
        perguntas = me.get("perguntas_decisor", {})
        if isinstance(perguntas, dict) and perguntas:
            story.append(Paragraph("Perguntas do Decisor", S['H2']))
            cw_perg = [48 * mm, CONTENT_W - 48 * mm]
            perg_rows = [[fix_accents(k), fix_accents(v)] for k, v in perguntas.items()]
            story.append(make_table(["Pergunta", "Resposta"], perg_rows, cw_perg))

    story.append(PageBreak())

    # ==========================================================
    # 6. DIMENSIONAMENTO DA OPORTUNIDADE
    # ==========================================================
    story.append(Paragraph("6. Dimensionamento da Oportunidade", S['H1']))
    story.append(hr())

    # Valor médio por contrato
    valor_medio_fmt = fmt_value(valor_medio)
    # ROI assumptions
    taxa_vitoria = 0.20
    pct_participacao = 0.30
    editais_participados = max(1, int(n_editais * pct_participacao))
    contratos_estimados = editais_participados * taxa_vitoria
    receita_mensal = contratos_estimados * valor_medio
    receita_anual = receita_mensal * 12

    cw_loss = [CONTENT_W * 0.55, CONTENT_W * 0.45]
    story.append(make_table(
        ["Indicador", "Valor"],
        [
            [f"Editais compatíveis abertos (último mês)", str(n_editais)],
            ["Participação atual estimada", "0"],
            ["Valor total dos editais compatíveis", total_valor_fmt],
            ["Taxa média de vitória no setor (SC)", "20%"],
            [f"Receita potencial estimada (anual)", fmt_value(receita_anual)],
            ["Receita gov. atual registrada", f"R$ 0" if not contratos else f"{len(contratos)} contratos"],
        ], cw_loss
    ))
    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph("Projeção em 12 Meses (cenário conservador)", S['H2']))
    cw_proj = [30 * mm, 30 * mm, 35 * mm, 40 * mm]
    # Project forward: assume same monthly rate
    story.append(make_table(
        ["Período", "Editais Est.", "Valor Est.", "Com 20% Vitória"],
        [
            ["3 meses", str(n_editais * 3), fmt_value(total_valor * 3), fmt_value(total_valor * 3 * taxa_vitoria)],
            ["6 meses", str(n_editais * 6), fmt_value(total_valor * 6), fmt_value(total_valor * 6 * taxa_vitoria)],
            ["12 meses", str(n_editais * 12), fmt_value(total_valor * 12), fmt_value(total_valor * 12 * taxa_vitoria)],
        ], cw_proj
    ))
    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph("Empresas COM vs SEM Monitoramento Sistemático", S['H2']))
    cw_comp = [CONTENT_W / 2] * 2
    story.append(make_table(
        ["Sem Monitoramento", "Com Monitoramento"],
        [
            ["Descobre editais por acaso ou indicação", "Recebe alertas automáticos"],
            ["Perde prazo de 60% dos editais", "Tempo adequado de preparação"],
            ["Participa de 2-3 editais/ano", "Participa de 20-30 editais/ano"],
            ["Ganha 0-1 contratos/ano", "Ganha 4-6 contratos/ano"],
            ["Depende de obra privada", "Diversifica receita com contratos públicos"],
        ], cw_comp, header_color=DARK_BLUE
    ))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "Empresas que monitoram sistematicamente participam de 5 a 10 vezes mais editais "
        "e, consequentemente, ganham mais contratos.", S['Quote']
    ))
    story.append(PageBreak())

    # ==========================================================
    # 7. CONTEÚDO DOS RELATÓRIOS
    # ==========================================================
    story.append(Paragraph("7. O Que Cada Relatório Entrega", S['H1']))
    story.append(hr())
    story.append(Paragraph(
        "Cada relatório entregue segue o mesmo padrão desta proposta: personalizado para o perfil "
        "da empresa, com dados reais e recomendações acionáveis.", S['Body']
    ))

    cw_rel = [42 * mm, CONTENT_W - 42 * mm]
    story.append(make_table(
        ["Seção", "Conteúdo"],
        [
            ["Perfil da Empresa", "Dados cadastrais, CNAEs, QSA, sanções, histórico gov."],
            ["Resumo Executivo", "Métricas-chave, destaques, alertas (visão em 2 minutos)"],
            ["Análise por Edital", "Órgão, valor, modalidade, prazo, link PNCP"],
            ["Análise Documental", "PDF do edital lido: habilitação, red flags, riscos"],
            ["Análise Estratégica", "6 fatores com nota 0-10 por edital"],
            ["Perguntas do Decisor", "Vale participar? Quanto ofertar? Quais documentos?"],
            ["Mapa Competitivo", "Nível de competição + estratégia de precificação"],
            ["Inteligência de Mercado", "Panorama setorial, tendências, oportunidades"],
            ["Diários Oficiais", "Monitoramento Querido Diário"],
            ["Plano de Ação", "Próximos passos priorizados com datas"],
        ], cw_rel
    ))
    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph("Fontes Consultadas", S['H2']))
    cw_fnt = [42 * mm, CONTENT_W - 42 * mm]
    story.append(make_table(
        ["Fonte", "Dados"],
        [
            ["PNCP", "Editais Pregão + Concorrência"],
            ["PCP v2", "Editais complementares"],
            ["OpenCNPJ", "Perfil empresarial atualizado"],
            ["Portal da Transparência", "Sanções + contratos federais"],
            ["Querido Diário", "Diários oficiais municipais"],
            ["PDFs dos Editais", "Análise documental completa"],
        ], cw_fnt
    ))
    story.append(PageBreak())

    # ==========================================================
    # 8. PACOTES DE MONITORAMENTO
    # ==========================================================
    story.append(Paragraph("8. Pacotes de Monitoramento", S['H1']))
    story.append(hr())
    story.append(Paragraph(
        "Três opções dimensionadas para diferentes níveis de acompanhamento.", S['Body']
    ))
    story.append(Spacer(1, 2 * mm))

    cw_pkg = [55 * mm, CONTENT_W - 55 * mm]

    # --- MENSAL ---
    mensal_items = [
        ["Relatório Executivo Completo", "1x por mês"],
        ["Abrangência", f"Editais de {emp.get('uf_sede', 'SC')} (Pregão + Concorrência)"],
        ["Análise documental (PDFs)", "Até 3 editais"],
        ["Perguntas do Decisor", "Sim"],
        ["Mapa competitivo", "Sim"],
        ["Plano de ação", "Sim"],
        ["Suporte WhatsApp", "Horário comercial (seg-sex)"],
        ["Valor mensal", "R$ 997/mês"],
        ["Valor anual (pague 10, leve 12)", "R$ 9.970/ano (= R$ 831/mês)"],
    ]
    mensal_table = make_table(["Item", "Detalhe"], mensal_items, cw_pkg)
    mensal_elements = [Paragraph("Pacote Mensal", S['H2'])]
    if pacote_recomendado == "mensal":
        badge = Table([[P("RECOMENDADO", 'BadgeWhite')]], colWidths=[40 * mm])
        badge.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), NAVY),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ]))
        mensal_elements.append(badge)
        mensal_elements.append(Spacer(1, 1 * mm))
        mensal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.4, MEDIUM_GRAY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('BOX', (0, 0), (-1, -1), 2, MEDIUM_BLUE),
        ]))
    mensal_elements.append(mensal_table)
    story.append(KeepTogether(mensal_elements))
    story.append(Spacer(1, 3 * mm))

    # --- SEMANAL ---
    uf_sede = emp.get('uf_sede', 'SC')
    semanal_items = [
        ["Relatório Semanal Resumido", "4x por mês (toda segunda-feira)"],
        ["Relatório Executivo Completo", "1x por mês (consolidado)"],
        ["Abrangência", f"{uf_sede} + PR + RS"],
        ["Análise documental (PDFs)", "Até 8 editais"],
        ["Perguntas do Decisor", "Sim"],
        ["Mapa competitivo semanal", "Sim"],
        ["Alertas de prazo crítico", "WhatsApp quando edital encerra em < 7 dias"],
        ["Suporte WhatsApp", "Horário estendido (8h-20h, seg-sáb)"],
        ["Valor mensal", "R$ 1.500/mês"],
        ["Valor anual (pague 10, leve 12)", "R$ 15.000/ano (= R$ 1.250/mês)"],
    ]
    semanal_table = make_table(["Item", "Detalhe"], semanal_items, cw_pkg)

    semanal_elements = [Paragraph("Pacote Semanal", S['H2'])]
    if pacote_recomendado == "semanal":
        badge = Table([[P("RECOMENDADO", 'BadgeWhite')]], colWidths=[40 * mm])
        badge.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), NAVY),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ]))
        semanal_elements.append(badge)
        semanal_elements.append(Spacer(1, 1 * mm))
        semanal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.4, MEDIUM_GRAY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('BOX', (0, 0), (-1, -1), 2, MEDIUM_BLUE),
        ]))
    else:
        semanal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.4, MEDIUM_GRAY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
    semanal_elements.append(semanal_table)
    story.append(KeepTogether(semanal_elements))
    story.append(Spacer(1, 3 * mm))

    # --- DIÁRIO ---
    diario_items = [
        ["Alertas diários de novos editais", "Todos os dias úteis (WhatsApp + Email)"],
        ["Relatório Semanal + Mensal", "4x semanal + 1x mensal"],
        ["Abrangência", f"{uf_sede} + PR + RS + MG + SP"],
        ["Análise documental (PDFs)", "Ilimitada"],
        ["Monitoramento de concorrentes", "Sim"],
        ["Estratégia de precificação", "Sugestão de desconto por edital"],
        ["Suporte dedicado", "WhatsApp + Tel (8h-22h, seg-dom)"],
        ["Valor mensal", "R$ 2.997/mês"],
        ["Valor anual (pague 10, leve 12)", "R$ 29.970/ano (= R$ 2.498/mês)"],
    ]
    diario_table = make_table(["Item", "Detalhe"], diario_items, cw_pkg)

    diario_elements = [Paragraph("Pacote Diário", S['H2'])]
    if pacote_recomendado == "diario":
        badge = Table([[P("RECOMENDADO", 'BadgeWhite')]], colWidths=[40 * mm])
        badge.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), NAVY),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ]))
        diario_elements.append(badge)
        diario_elements.append(Spacer(1, 1 * mm))
        diario_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.4, MEDIUM_GRAY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('BOX', (0, 0), (-1, -1), 2, MEDIUM_BLUE),
        ]))
    diario_elements.append(diario_table)
    story.append(KeepTogether(diario_elements))
    story.append(Spacer(1, 3 * mm))

    # Comparativo Rápido
    story.append(Paragraph("Comparativo Rápido", S['H2']))
    cw_cmp = [40 * mm, 30 * mm, 30 * mm, 30 * mm]
    story.append(make_table(
        ["Recurso", "Mensal", "Semanal", "Diário"],
        [
            ["Relatório completo", "1x/mês", "1x/mês", "1x/mês"],
            ["Relatório resumido", "—", "4x/mês", "4x/mês"],
            ["Alertas diários", "—", "—", "Sim"],
            ["Análise de PDFs", "3", "8", "Ilimitada"],
            ["UFs monitoradas", uf_sede, f"{uf_sede}+PR+RS", "5 estados"],
            ["Alerta prazo crítico", "—", "Sim", "Imediato"],
            ["Monit. concorrentes", "—", "—", "Sim"],
            ["Valor mensal", "R$ 997", "R$ 1.500", "R$ 2.997"],
            ["Valor anual (10 meses)", "R$ 9.970", "R$ 15.000", "R$ 29.970"],
        ], cw_cmp
    ))
    story.append(PageBreak())

    # ==========================================================
    # 9. ROI
    # ==========================================================
    story.append(Paragraph("9. Retorno do Investimento", S['H1']))
    story.append(hr())

    # Package values for ROI calculation
    pkg_values = {"mensal": 997, "semanal": 1500, "diario": 2997}
    pkg_names = {"mensal": "Mensal", "semanal": "Semanal", "diario": "Diário"}
    investimento = pkg_values.get(pacote_recomendado, 5000)
    pkg_name = pkg_names.get(pacote_recomendado, "Semanal")

    story.append(Paragraph(
        f"Cenário Conservador — Pacote {pkg_name} (R$ {investimento:,.0f}/mês)".replace(",", "."),
        S['H2']
    ))

    roi_mensal = (receita_mensal / investimento * 100) if investimento > 0 else 0
    cw_roi = [CONTENT_W * 0.55, CONTENT_W * 0.45]
    story.append(make_table(
        ["Métrica", "Valor"],
        [
            ["Editais compatíveis identificados/mês", str(n_editais)],
            [f"Editais participados (30% do total)", f"{editais_participados}/mês"],
            ["Taxa de vitória (média setorial SC)", "20%"],
            ["Contratos estimados/mês", f"{contratos_estimados:.1f}"],
            ["Valor médio por contrato", valor_medio_fmt],
            ["Receita incremental mensal", fmt_value(receita_mensal)],
            ["Investimento mensal", f"R$ {investimento:,.0f}".replace(",", ".")],
            ["ROI mensal", f"{roi_mensal:,.0f}%".replace(",", ".")],
        ], cw_roi
    ))
    story.append(Spacer(1, 3 * mm))

    # Análise de Sensibilidade — wrapped in KeepTogether
    story.append(Paragraph("Análise de Sensibilidade", S['H2']))
    cw_sens = [32 * mm, 22 * mm, 20 * mm, 24 * mm, 26 * mm, 24 * mm]
    # Compute scenarios based on actual data
    scenarios = [
        ("Otimista", n_editais, 0.25, valor_medio * 1.4),
        ("Realista", max(1, int(n_editais * 0.6)), 0.20, valor_medio),
        ("Conservador", max(1, int(n_editais * 0.35)), 0.15, valor_medio * 0.6),
        ("Ultra-conservador", max(1, int(n_editais * 0.2)), 0.10, valor_medio * 0.3),
    ]
    sens_rows = []
    for label, ed, vit, vm in scenarios:
        rec_mes = ed * vit * vm
        roi_s = (rec_mes / investimento * 100) if investimento > 0 else 0
        sens_rows.append([label, str(ed), f"{vit:.0%}", fmt_value(vm), fmt_value(rec_mes), f"{roi_s:,.0f}%".replace(",", ".")])

    sens_table = make_table(
        ["Cenário", "Editais/mês", "Vitória", "Valor Méd.", "Receita/mês", "ROI"],
        sens_rows, cw_sens
    )
    story.append(KeepTogether([sens_table]))
    story.append(Spacer(1, 3 * mm))

    # Dynamic reference to best edital for context
    if melhor_edital:
        me_valor_n = float(melhor_edital.get("valor_estimado", 0))
        me_mun = fix_accents(melhor_edital.get("municipio", ""))
        anos_equiv = me_valor_n / (investimento * 12) if investimento > 0 else 0
        story.append(Paragraph(
            f"Mesmo no cenário mais conservador, o valor de um único contrato ganho supera em dezenas "
            f"de vezes o investimento anual no monitoramento. A título de referência: o edital de "
            f"{me_mun} ({fmt_value(me_valor_n)}) equivale a mais de {anos_equiv:.0f} anos do Pacote {pkg_name}.",
            S['Quote']
        ))
    story.append(Paragraph(
        "Projeções baseadas em dados públicos e médias setoriais. "
        "Resultados dependem da participação e execução da empresa.", S['Small']
    ))
    story.append(PageBreak())

    # ==========================================================
    # 10. QUEM ANALISA SEUS EDITAIS (Authority Section)
    # ==========================================================
    story.append(Paragraph("10. Quem Analisa Seus Editais", S['H1']))
    story.append(hr())
    story.append(Paragraph(
        "<b>Tiago Sasaki — Engenheiro e servidor público efetivo da Secretaria de Estado da "
        "Infraestrutura de Santa Catarina há 7 anos.</b>",
        S['BodyBold']
    ))
    story.append(Spacer(1, 2 * mm))

    story.append(Paragraph("O Que Significa 'Do Outro Lado do Balcão'", S['H2']))
    story.append(Paragraph(
        "Nos últimos 7 anos, participei diretamente de processos licitatórios pelo lado do "
        "órgão público: elaborei termos de referência, analisei propostas de habilitação, "
        "acompanhei execuções de obras e vi, de perto, os erros mais comuns que eliminam "
        "empresas qualificadas antes mesmo da fase de preços.",
        S['Body']
    ))
    for item in [
        "Já analisei mais de 500 propostas de habilitação — sei exatamente quais documentos "
        "os pregoeiros verificam primeiro e onde 80% das inabilitações acontecem",

        "Conheço os critérios não escritos: como comissões avaliam atestados, o que realmente "
        "configura 'experiência similar', e quando uma exigência é restritiva o suficiente para impugnar",

        "Acompanhei dezenas de obras pelo Estado de SC — sei quais órgãos pagam em dia, quais "
        "atrasam, e como funciona o fluxo real de medição e pagamento",

        "Identifiquei cláusulas restritivas disfarçadas em editais que pareciam limpos — "
        "requisitos de capital social desproporcionais, índices contábeis eliminatórios, "
        "exigências de atestado com quantitativos acima do razoável",
    ]:
        story.append(bullet(item))

    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("Tecnologia Proprietária", S['H2']))
    story.append(Paragraph(
        "Além da experiência como servidor, desenvolvi o SmartLic — plataforma de inteligência "
        "artificial que monitora automaticamente 3 fontes governamentais (PNCP, Portal de Compras "
        "Públicas e Portal da Transparência), classifica editais por setor e gera análises de "
        "viabilidade. Cada relatório combina varredura automatizada com análise humana de quem "
        "conhece a máquina por dentro.",
        S['Body']
    ))

    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("Diferenciais", S['H2']))
    cw_dif = [CONTENT_W / 2] * 2
    story.append(make_table(
        ["Consultoria Tradicional", "Consultoria Tiago Sasaki"],
        [
            ["Busca manual em portais", "Varredura automática diária de 3+ fontes (IA)"],
            ["Planilha genérica de editais", "Relatório personalizado com análise estratégica por edital"],
            ["Analista sem vivência no órgão", "7 anos como servidor — entende a lógica de quem compra"],
            ["Leitura superficial do edital", "PDF do edital lido página por página com checklist de habilitação"],
            ["Sem inteligência competitiva", "Mapeamento de incumbentes e histórico de preços por órgão"],
            ["Alerta genérico", "Recomendação com nota 0-10 em 6 fatores estratégicos"],
        ], cw_dif, header_color=DARK_BLUE
    ))
    story.append(PageBreak())

    # ==========================================================
    # 11. CONDIÇÕES COMERCIAIS
    # ==========================================================
    story.append(Paragraph("11. Condições Comerciais", S['H1']))
    story.append(hr())
    story.append(Paragraph(f"Pacote Recomendado: {pkg_name}", S['H2']))

    investimento_anual = investimento * 10  # pague 10, leve 12
    economia_anual = investimento * 2
    mensal_anual = investimento_anual / 12

    inv_fmt = f"{investimento:,.0f}".replace(",", ".")
    inv_anual_fmt = f"{investimento_anual:,.0f}".replace(",", ".")
    eco_fmt = f"{economia_anual:,.0f}".replace(",", ".")
    story.append(make_kv([
        ["Pacote", pkg_name],
        ["Investimento mensal", f"R$ {inv_fmt}/mês"],
        ["Pagamento anual adiantado", f"R$ {inv_anual_fmt}/ano (pague 10, leve 12)"],
        ["Economia no plano anual", f"R$ {eco_fmt} (2 meses de cortesia)"],
        ["Forma de pagamento", "Boleto, PIX ou Cartão de Crédito"],
        ["Prazo mínimo", "3 meses"],
        ["Cancelamento", "30 dias de antecedência"],
        ["Início", "Imediato após aceite"],
        ["Primeiro relatório", "Até 3 dias úteis após contratação"],
    ], kw=52 * mm))
    story.append(Spacer(1, 4 * mm))

    # C3: Condição Especial — visual highlight box
    cond_especial_elements = []
    cond_especial_elements.append(Spacer(1, 2 * mm))

    oferta_label = Table(
        [[P("OFERTA POR TEMPO LIMITADO", 'BadgeWhite')]],
        colWidths=[60 * mm]
    )
    oferta_label.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
    ]))
    cond_especial_elements.append(oferta_label)
    cond_especial_elements.append(Spacer(1, 2 * mm))

    # Build the special condition text dynamically
    # Find the soonest and second-soonest editais for urgency
    soonest = editais_by_deadline[:2] if len(editais_by_deadline) >= 2 else editais_by_deadline
    urgency_examples = ""
    for e in soonest:
        e_mun = fix_accents(e.get("municipio", ""))
        e_enc = fmt_date(e.get("data_encerramento", ""))
        urgency_examples += f"{e_mun} encerra em {e_enc}, "
    urgency_examples = urgency_examples.rstrip(", ")

    cond_text = (
        f"Para contratações formalizadas até <b>{validity_fmt}</b>, o primeiro mês de monitoramento "
        f"é cortesia, permitindo que a empresa já receba o primeiro relatório cobrindo os "
        f"editais com prazo mais próximo ({urgency_examples})."
    )

    cond_inner = Table(
        [[Paragraph(cond_text, S['Body'])]],
        colWidths=[CONTENT_W - 12 * mm]
    )
    cond_inner.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BLUE),
        ('BOX', (0, 0), (-1, -1), 2, MEDIUM_BLUE),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    cond_especial_elements.append(cond_inner)
    cond_especial_elements.append(Spacer(1, 1 * mm))
    cond_especial_elements.append(Paragraph(
        f"Após esta data, a condição padrão se aplica.", S['Small']
    ))

    story.append(KeepTogether(cond_especial_elements))
    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph("O Que NÃO Está Incluído", S['H2']))
    for item in [
        "Elaboração de propostas comerciais (documentos de habilitação são responsabilidade da empresa)",
        "Representação presencial em sessões de licitação",
        "Serviços jurídicos (impugnações, recursos)",
        "Execução das obras",
        "Garantias financeiras",
    ]:
        story.append(bullet(item))
    story.append(Paragraph(
        "Estes serviços podem ser contratados separadamente sob demanda.", S['Small']
    ))
    story.append(PageBreak())

    # ==========================================================
    # 12. PRÓXIMOS PASSOS
    # ==========================================================
    story.append(Paragraph("12. Próximos Passos", S['H1']))
    story.append(hr())

    # Resumo Executivo (from JSON)
    if resumo_texto:
        story.append(Paragraph("Resumo Executivo", S['H2']))
        story.append(Paragraph(resumo_texto, S['Body']))
        if resumo_destaques:
            for d in resumo_destaques:
                story.append(bullet(fix_accents(d)))
        story.append(Spacer(1, 3 * mm))

    story.append(Paragraph("Após Aceite", S['H2']))
    cw_steps = [30 * mm, 22 * mm, CONTENT_W - 52 * mm]
    story.append(make_table(
        ["Etapa", "Quando", "O Que Acontece"],
        [
            ["Aceite", "Dia 0", "Confirmação via WhatsApp ou email"],
            ["Onboarding", "Dia 1-2", "Alinhamento: UFs, faixa de valor, tipos de obra"],
            ["Primeiro Relatório", "Dia 3-5", "Relatório completo + plano de ação"],
            ["Monitoramento", "Dia 6+", "Relatórios na frequência contratada"],
        ], cw_steps
    ))
    story.append(Spacer(1, 4 * mm))

    # Calendário de Editais — dynamic from JSON, sorted by encerramento
    story.append(Paragraph("Calendário de Editais em Andamento", S['H2']))
    cw_cal = [32 * mm, CONTENT_W - 62 * mm, 30 * mm]
    cal_rows = []
    for e in editais_by_deadline:
        enc_date = fmt_date(e.get("data_encerramento", ""))
        dias = e.get("dias_restantes", "")
        dias_str = f" ({dias} dias)" if dias else ""
        mun = fix_accents(e.get("municipio", ""))
        obj_short = fix_accents(e.get("objeto", ""))
        # Shorten object for calendar — take first meaningful portion
        if len(obj_short) > 45:
            obj_short = obj_short[:42] + "..."
        valor = fmt_value(float(e.get("valor_estimado", 0)))
        cal_rows.append([f"{enc_date}{dias_str}", f"{mun} — {obj_short}", valor])

    story.append(make_table(["Data", "Edital", "Valor"], cal_rows, cw_cal))
    story.append(Spacer(1, 3 * mm))

    # C2: CTA Box — high-conversion
    cta_box = Table(
        [
            [Paragraph("Responda agora pelo WhatsApp: (48) 9 8834-4559", S['CTAWhite'])],
            [Paragraph("ou envie um email para tiago.sasaki@confenge.com.br", S['CTAWhiteSub'])],
        ],
        colWidths=[CONTENT_W],
    )
    cta_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (0, 0), 10),
        ('BOTTOMPADDING', (-1, -1), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    story.append(cta_box)
    story.append(Spacer(1, 3 * mm))

    # Urgency paragraph
    if primeiro_encerrar:
        pe_mun = fix_accents(primeiro_encerrar.get("municipio", ""))
        pe_dias = primeiro_encerrar.get("dias_restantes", "?")
        story.append(Paragraph(
            f"O edital de {pe_mun} encerra em {pe_dias} dias. Cada dia sem monitoramento "
            f"é um edital compatível que passa sem que {nome} sequer saiba que existiu.",
            S['Quote']
        ))

    story.append(Spacer(1, 3 * mm))

    # Próximos Passos table from JSON
    if proximos:
        story.append(Paragraph("Plano de Ação Recomendado", S['H2']))
        cw_prox = [CONTENT_W * 0.50, 30 * mm, 25 * mm]
        prox_rows = []
        for p in proximos:
            prox_rows.append([
                fix_accents(p.get("acao", "")),
                fix_accents(p.get("prazo", "")),
                fix_accents(p.get("prioridade", "")),
            ])
        story.append(make_table(["Ação", "Prazo", "Prioridade"], prox_rows, cw_prox))
        story.append(Spacer(1, 3 * mm))

    story.append(Paragraph(
        "Os prazos acima são reais e públicos. A decisão de acompanhar ou não o "
        "mercado de licitações é estratégica, e o momento ideal para iniciar é "
        "enquanto ainda há editais abertos compatíveis com o perfil da empresa.", S['Quote']
    ))
    story.append(Spacer(1, 6 * mm))

    # Contact block
    story.append(HRFlowable(width="40%", thickness=1, color=NAVY, spaceAfter=4 * mm, spaceBefore=4 * mm))
    story.append(Paragraph("<b>Tiago Sasaki</b>", S['Body']))
    story.append(Paragraph("Engenheiro | Servidor Efetivo — SIE/SC", S['Body']))
    story.append(Paragraph("Consultor de Licitações | CONFENGE", S['Body']))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("<b>WhatsApp:</b> (48) 9 8834-4559", S['Body']))
    story.append(Paragraph("<b>Email:</b> tiago.sasaki@confenge.com.br", S['Body']))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "Disponível para uma conversa sem compromisso para esclarecer qualquer ponto desta proposta.",
        S['Body']
    ))
    story.append(Spacer(1, 8 * mm))

    # Disclaimer
    story.append(Paragraph(
        f"Proposta preparada com dados reais de editais abertos em {today_fmt}. "
        f"Informações extraídas de fontes públicas oficiais (PNCP, Portal da "
        f"Transparência, OpenCNPJ). Projeções de ROI são estimativas baseadas em "
        f"médias setoriais; resultados dependem da participação e execução da empresa.",
        S['Small']
    ))

    # ==========================================================
    # BUILD
    # ==========================================================
    def on_page(canvas, doc):
        canvas.saveState()
        # Footer
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(HexColor("#a0aec0"))
        canvas.drawCentredString(PAGE_W / 2, 10 * mm, FOOTER_TEXT)
        canvas.drawRightString(PAGE_W - MARGIN, 10 * mm, f"Página {doc.page}")
        # Top line
        canvas.setStrokeColor(MEDIUM_BLUE)
        canvas.setLineWidth(0.4)
        canvas.line(MARGIN, PAGE_H - 14 * mm, PAGE_W - MARGIN, PAGE_H - 14 * mm)
        canvas.restoreState()

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=18 * mm, bottomMargin=18 * mm,
    )
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"PDF gerado: {output_path}")
    print(f"Páginas: ~{doc.page}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gerador de PDF de Proposta Comercial B2G v3"
    )
    parser.add_argument(
        "input_positional", nargs="?", default=None,
        help="Caminho do JSON de dados (argumento posicional, alternativa a --input)"
    )
    parser.add_argument(
        "output_positional", nargs="?", default=None,
        help="Caminho do PDF de saída (argumento posicional, alternativa a --output)"
    )
    parser.add_argument(
        "--input", "-i", dest="input_file", default=None,
        help="Caminho do JSON de dados"
    )
    parser.add_argument(
        "--output", "-o", dest="output_file", default=None,
        help="Caminho do PDF de saída"
    )
    parser.add_argument(
        "--pacote", "-p", choices=["mensal", "semanal", "diario"], default="semanal",
        help="Pacote recomendado a destacar (default: semanal)"
    )

    args = parser.parse_args()

    # Resolve input: --input takes precedence over positional
    data_path = args.input_file or args.input_positional or "docs/reports/data-27232335000191-2026-03-11.json"
    output_path = args.output_file or args.output_positional or "docs/propostas/proposta-output.pdf"

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    build_pdf(data, output_path, pacote_recomendado=args.pacote)
