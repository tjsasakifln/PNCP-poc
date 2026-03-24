"""
Gerador de PDF de Proposta Comercial B2G
v5 — Service-focused: sells the monitoring service, NOT specific editais.
     No PNCP data, no market metrics, no edital listings.
     Focus: what we deliver + authority + packages + ROI framework.
"""
import argparse
import datetime
import json
import re
import sys
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
CONTENT_W = PAGE_W - 2 * MARGIN

# --- Colors ---
NAVY = HexColor("#1a365d")
DARK_BLUE = HexColor("#2c5282")
MEDIUM_BLUE = HexColor("#3182ce")
LIGHT_BLUE = HexColor("#ebf8ff")
LIGHT_GRAY = HexColor("#f7fafc")
MEDIUM_GRAY = HexColor("#e2e8f0")
DARK_GRAY = HexColor("#2d3748")
GREEN = HexColor("#276749")
WHITE = white

FOOTER_TEXT = "Tiago Sasaki — Consultor de Licitações (48) 9 8834-4559"

# Fallback authority examples (normally comes from JSON)
_DEFAULT_AUTHORITY = [
    "Análise de centenas de processos licitatórios — identificação dos "
    "documentos que pregoeiros verificam primeiro e onde a maioria das "
    "inabilitações acontecem",
    "Conhecimento dos critérios não escritos das comissões: como avaliam "
    "atestados, o que configura experiência similar, quando uma exigência "
    "é restritiva o suficiente para impugnar",
    "Acompanhamento de dezenas de contratos públicos — conhecimento de "
    "quais órgãos pagam em dia e como funciona o fluxo real de medição "
    "e pagamento",
    "Identificação de cláusulas restritivas disfarçadas: requisitos de "
    "capital desproporcionais, índices contábeis eliminatórios, exigências "
    "de atestado acima do razoável",
]

# ---------------------------------------------------------------------------
# Accent fixer
# ---------------------------------------------------------------------------
_ACCENT_MAP = [
    (r"\bConstrucao\b", "Construção"), (r"\bconstrucao\b", "construção"),
    (r"\blicitacao\b", "licitação"), (r"\bLicitacao\b", "Licitação"),
    (r"\blicitacoes\b", "licitações"), (r"\bLicitacoes\b", "Licitações"),
    (r"\bcontratacao\b", "contratação"), (r"\bContratacao\b", "Contratação"),
    (r"\bcontratacoes\b", "contratações"), (r"\bContratacoes\b", "Contratações"),
    (r"\bConcorrencia\b", "Concorrência"), (r"\bconcorrencia\b", "concorrência"),
    (r"\bparticipacao\b", "participação"), (r"\bParticipacao\b", "Participação"),
    (r"\binformacao\b", "informação"), (r"\binformacoes\b", "informações"),
    (r"\bavaliacao\b", "avaliação"), (r"\brecomendacao\b", "recomendação"),
    (r"\bPregao\b", "Pregão"), (r"\bpregao\b", "pregão"),
    (r"\borgao\b", "órgão"), (r"\bOrgao\b", "Órgão"),
    (r"\binteligencia\b", "inteligência"), (r"\bInteligencia\b", "Inteligência"),
    (r"\bexperiencia\b", "experiência"), (r"\bExperiencia\b", "Experiência"),
    (r"\bexigencias\b", "exigências"), (r"\bExigencias\b", "Exigências"),
    (r"\bcompativel\b", "compatível"), (r"\bCompativel\b", "Compatível"),
    (r"\btecnica\b", "técnica"), (r"\bTecnica\b", "Técnica"),
    (r"\btecnico\b", "técnico"), (r"\bTecnico\b", "Técnico"),
    (r"\bjuridica\b", "jurídica"), (r"\bJuridica\b", "Jurídica"),
    (r"\beletronico\b", "eletrônico"), (r"\bEletronico\b", "Eletrônico"),
    (r"\beletronica\b", "eletrônica"), (r"\bEletronica\b", "Eletrônica"),
    (r"\bpreco\b", "preço"), (r"\bPreco\b", "Preço"),
    (r"\bservico\b", "serviço"), (r"\bservicos\b", "serviços"),
    (r"\bMunicipio\b", "Município"), (r"\bmunicipio\b", "município"),
    (r"\bhabilitacao\b", "habilitação"), (r"\bHabilitacao\b", "Habilitação"),
    (r"\binabilitacao\b", "inabilitação"), (r"\binabilitacoes\b", "inabilitações"),
    (r"\bsancoes\b", "sanções"), (r"\bSancoes\b", "Sanções"),
    (r"\bgestao\b", "gestão"), (r"\bGestao\b", "Gestão"),
    (r"\bsaude\b", "saúde"), (r"\bSaude\b", "Saúde"),
    (r"\bqualificacao\b", "qualificação"), (r"\bQualificacao\b", "Qualificação"),
    (r"\bclassificacao\b", "classificação"),
    (r"\bmanutencao\b", "manutenção"), (r"\bManutencao\b", "Manutenção"),
    (r"\bseguranca\b", "segurança"), (r"\bSeguranca\b", "Segurança"),
    (r"\bnao\b", "não"), (r"\bNao\b", "Não"),
    (r"\bSao\b", "São"),
    (r"\bindice\b", "índice"), (r"\bindices\b", "índices"),
    (r"\bcontabil\b", "contábil"), (r"\bcontabeis\b", "contábeis"),
    (r"\bregiao\b", "região"),
    (r"\buteis\b", "úteis"),
    (r"\bultimos\b", "últimos"),
]
_ACCENT_PATTERNS = [(re.compile(pat), repl) for pat, repl in _ACCENT_MAP]


def fix_accents(text):
    if not text or not isinstance(text, str):
        return text or ""
    for pat, repl in _ACCENT_PATTERNS:
        text = pat.sub(repl, text)
    return text


def fmt_value_full(v):
    if v is None:
        return "R$ 0,00"
    v = float(v)
    return "R$ {:,.2f}".format(v).replace(",", "X").replace(".", ",").replace("X", ".")


def detect_gender(name):
    if not name:
        return "Sr."
    first = name.strip().split()[0].lower()
    female_names = {
        "angela", "ana", "maria", "mariana", "juliana", "fernanda", "amanda",
        "patricia", "luciana", "adriana", "cristiane", "rosane", "eliane",
        "simone", "viviane", "aline", "caroline", "michele", "vanessa",
        "larissa", "beatriz", "roberta", "denise", "raquel", "claudia",
        "silvia", "sandra", "carla", "paula", "lucia", "renata", "camila",
        "leticia", "gabriela", "daniela", "rafaela", "isabela", "priscila",
        "tatiana", "fabiana", "luana", "bruna", "natalia",
    }
    male_names = {
        "andre", "alexandre", "felipe", "henrique", "jose", "dante",
        "jorge", "duarte", "vicente", "jaime", "juliano", "rogerio",
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


S = None


def P(text, style='Cell'):
    return Paragraph(str(fix_accents(str(text))), S[style])


def make_table(headers, rows, col_widths, header_color=NAVY):
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
    nome = (emp.get("nome_fantasia") or "").strip() or emp.get("razao_social", "Empresa")
    nome = fix_accents(nome)

    decisor_full = emp["qsa"][0]["nome"] if emp.get("qsa") else "Prezado(a) Diretor(a)"
    decisor_full = fix_accents(decisor_full)
    honorific = detect_gender(decisor_full)
    decisor_greeting = f"{honorific} {decisor_full}"

    cnpj = emp["cnpj"]
    cnaes_sec_str = emp.get("cnaes_secundarios", "")
    n_cnaes = data.get("n_cnaes", 1)
    capital = float(emp.get("capital_social", 0))
    capital_fmt = fmt_value_full(capital)
    setor = fix_accents(data.get("setor", ""))
    anos_mercado = data.get("anos_mercado", 0)

    today = datetime.date.today()
    today_fmt = today.strftime("%d/%m/%Y")
    validity_date = today + datetime.timedelta(days=15)
    validity_fmt = validity_date.strftime("%d/%m/%Y")

    sancoes = emp.get("sancoes", {})
    tem_sancao = any(sancoes.get(k) for k in ("ceis", "cnep", "cepim", "ceaf"))
    sancoes_txt = "NENHUMA (CEIS, CNEP, CEPIM, CEAF)" if not tem_sancao else "VERIFICAR — sanção detectada"

    sede = f"{fix_accents(emp.get('cidade_sede', ''))}/{emp.get('uf_sede', '')}"
    uf_sede = emp.get('uf_sede', 'MG')
    uf_abrangencia = data.get("uf_abrangencia", {})
    ufs_semanal = uf_abrangencia.get("semanal", [uf_sede])
    ufs_diario = uf_abrangencia.get("diario", [uf_sede])
    ufs_semanal_txt = " + ".join(ufs_semanal)
    ufs_diario_txt = " + ".join(ufs_diario)

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

    setor_intro = fix_accents(data.get("setor_intro",
        f"Como consultor especializado em licitações públicas, acompanho diariamente o volume de "
        f"contratações no setor de {setor}."
    ))
    story.append(Paragraph(setor_intro, S['Body']))
    story.append(Paragraph(
        f"O objetivo desta proposta é apresentar o serviço de monitoramento e análise de "
        f"licitações que pode transformar a forma como a {nome} acessa o mercado público. "
        f"Trata-se de um trabalho contínuo e personalizado — não uma lista genérica de editais.",
        S['Body']
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
        ["CNAEs Registrados", f"{n_cnaes} CNAEs (principal + secundários)"],
        ["Porte", fix_accents(emp.get("porte", ""))],
        ["Capital Social", capital_fmt],
        ["Sede", sede],
        [f"{'Sócia-Administradora' if honorific == 'Sra.' else 'Sócio-Administrador'}", decisor_full],
        ["Situação Cadastral", fix_accents(emp.get("situacao_cadastral", ""))],
        ["Sanções Gov.", sancoes_txt],
    ]))
    story.append(Spacer(1, 3 * mm))

    # Pontos Fortes
    story.append(Paragraph("Pontos Fortes", S['H2']))
    pontos_fortes = []
    if cnae_principal_txt:
        cnae_desc = cnae_principal_txt.split(" - ")[1].strip() if " - " in cnae_principal_txt else cnae_principal_txt
        pontos_fortes.append(f"CNAE principal posiciona a empresa no setor de {setor}")

    if anos_mercado > 0:
        pontos_fortes.append(f"{anos_mercado} anos de mercado — histórico que fortalece habilitação")

    if n_cnaes > 5:
        pontos_fortes.append(f"{n_cnaes} CNAEs cobrem escopo amplo de licitações")

    if not tem_sancao:
        pontos_fortes.append("Empresa ativa, sem nenhuma sanção governamental (CEIS, CNEP, CEPIM, CEAF)")

    for pf in pontos_fortes:
        story.append(bullet(pf))

    story.append(Paragraph(
        f"A {nome} tem perfil compatível com o mercado de licitações públicas em {setor.lower()}. "
        f"O próximo passo é ter acesso sistemático às oportunidades certas, no momento certo.",
        S['Quote']
    ))
    story.append(PageBreak())

    # ==========================================================
    # 3. O QUE NOSSO TRABALHO ENTREGA
    # ==========================================================
    story.append(Paragraph("3. O Que Nosso Trabalho Entrega", S['H1']))
    story.append(hr())
    story.append(Paragraph(
        "Cada relatório é construído exclusivamente para o perfil da sua empresa. "
        "Entre centenas de editais publicados, selecionamos e analisamos as "
        "<b>20 melhores oportunidades</b> — economizando dezenas de horas de trabalho "
        "que sua equipe gastaria vasculhando portais.",
        S['Body']
    ))
    story.append(Spacer(1, 2 * mm))

    # Processo de Análise
    story.append(Paragraph("Processo de Análise", S['H2']))
    cw_proc = [8 * mm, 40 * mm, CONTENT_W - 48 * mm]
    story.append(make_table(
        ["#", "Etapa", "O Que Fazemos"],
        [
            ["1", "Varredura", "Monitoramento contínuo de 100% das publicações obrigatórias por lei (Lei 14.133/2021)"],
            ["2", "Triagem Setorial", "Classificação automática por IA — zero ruído, só editais do seu setor"],
            ["3", "Análise Individual", "Cada edital avaliado em 17 dimensões: objeto, valor, modalidade, "
             "prazo, exigências de habilitação, atestados, índices contábeis, consórcio..."],
            ["4", "Análise Documental", "PDF do edital lido integralmente — checklist de 25 itens de "
             "habilitação, identificação de cláusulas restritivas e red flags"],
            ["5", "Score de Compatibilidade", "Avaliação com 7 fatores calibrados ao perfil da empresa: "
             "porte, capital, experiência, localização, modalidade, prazo, complexidade"],
            ["6", "Recomendação Final", "PARTICIPAR ou NÃO PARTICIPAR com justificativa detalhada — "
             "você decide com informação, não com achismo"],
        ], cw_proc
    ))
    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph("O Que Você Recebe", S['H2']))
    cw_rel = [42 * mm, CONTENT_W - 42 * mm]
    story.append(make_table(
        ["Entregável", "Detalhamento"],
        [
            ["Relatório Executivo", "Visão consolidada em 2 minutos: métricas-chave, alertas, destaques"],
            ["Top 20 Oportunidades", "As melhores oportunidades entre centenas analisadas, com recomendação individual"],
            ["Análise de Habilitação", "25 itens verificados por edital — antes de investir tempo na proposta, "
             "você sabe se tem chance real"],
            ["Cláusulas Restritivas", "Identificação de exigências que eliminam 60% das empresas antes do julgamento"],
            ["Plano de Ação", "Próximos passos priorizados com datas e responsáveis"],
        ], cw_rel
    ))
    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph(
        "Todos os dados são extraídos diretamente das publicações oficiais obrigatórias "
        "por lei, com cobertura total dos editais publicados nos portais governamentais. "
        "Cada relatório combina varredura automatizada com análise humana qualificada.",
        S['Quote']
    ))
    story.append(PageBreak())

    # ==========================================================
    # 4. POR QUE MONITORAMENTO CONTÍNUO
    # ==========================================================
    story.append(Paragraph("4. Por Que Monitoramento Contínuo", S['H1']))
    story.append(hr())

    story.append(Paragraph("Empresas COM vs SEM Monitoramento Sistemático", S['H2']))
    cw_comp = [CONTENT_W / 2] * 2
    story.append(make_table(
        ["Sem Monitoramento", "Com Monitoramento"],
        [
            ["Descobre editais por acaso ou indicação", "Recebe análises personalizadas"],
            ["Perde prazo de 60% dos editais", "Tempo adequado de preparação"],
            ["Participa de 2-3 editais/ano", "Participa de 20-30 editais/ano"],
            ["Ganha 0-1 contratos/ano", "Ganha 4-6 contratos/ano"],
            ["Depende de clientes privados", "Diversifica receita com contratos públicos"],
            ["Não sabe das cláusulas restritivas", "Red flags identificados antes de gastar tempo"],
        ], cw_comp, header_color=DARK_BLUE
    ))
    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph(
        "Empresas que monitoram sistematicamente participam de 5 a 10 vezes mais editais "
        "e, consequentemente, ganham mais contratos. A diferença não é sorte — é método.",
        S['Quote']
    ))
    story.append(Spacer(1, 4 * mm))

    # ROI framework (generic, not based on specific editais)
    story.append(Paragraph("Lógica do Retorno", S['H2']))
    story.append(Paragraph(
        "O investimento no monitoramento se paga com um único contrato ganho. "
        "Na prática, considerando uma taxa de vitória de 15-20% (média setorial "
        "para empresas que participam com preparação adequada), a matemática é direta:",
        S['Body']
    ))

    pkg_values = {"mensal": 997, "semanal": 1500, "diario": 2997}
    investimento = pkg_values.get(pacote_recomendado, 1500)
    investimento_anual = investimento * 12

    cw_roi = [CONTENT_W * 0.55, CONTENT_W * 0.45]
    inv_fmt = f"R$ {investimento:,.0f}".replace(",", ".")
    inv_anual_fmt = f"R$ {investimento_anual:,.0f}".replace(",", ".")
    story.append(make_table(
        ["Cenário", "Resultado"],
        [
            ["Investimento anual", inv_anual_fmt],
            ["Valor de 1 contrato típico no setor", "R$ 500K a R$ 5M"],
            ["Contratos necessários para pagar o ano inteiro", "1 (parcial)"],
            ["Editais analisados por ano (pacote semanal)", "240+"],
            ["Taxa média de vitória (com preparação)", "15-20%"],
        ], cw_roi
    ))
    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph(
        "Mesmo no cenário mais conservador, o valor de um único contrato público "
        "supera em dezenas de vezes o investimento anual no monitoramento.",
        S['Quote']
    ))
    story.append(PageBreak())

    # ==========================================================
    # 5. PACOTES DE MONITORAMENTO
    # ==========================================================
    story.append(Paragraph("5. Pacotes de Monitoramento", S['H1']))
    story.append(hr())
    story.append(Paragraph(
        "Três opções dimensionadas para diferentes níveis de acompanhamento.", S['Body']
    ))
    story.append(Spacer(1, 2 * mm))

    cw_pkg = [55 * mm, CONTENT_W - 55 * mm]

    def _make_pkg_table(items, is_recommended):
        t = make_table(["Item", "Detalhe"], items, cw_pkg)
        if is_recommended:
            t.setStyle(TableStyle([
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
        return t

    def _make_badge():
        badge = Table([[P("RECOMENDADO", 'BadgeWhite')]], colWidths=[40 * mm])
        badge.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), NAVY),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ]))
        return badge

    # --- MENSAL ---
    mensal_items = [
        ["Relatório Executivo Completo", "1x por mês"],
        ["Abrangência", f"Editais de {uf_sede} (Pregão + Concorrência)"],
        ["Análise documental (PDFs)", "Até 3 editais"],
        ["Suporte WhatsApp", "Horário comercial (seg-sex)"],
        ["Valor mensal", "R$ 997/mês"],
        ["Valor anual (pague 10, leve 12)", "R$ 9.970/ano (= R$ 831/mês)"],
    ]
    mensal_elements = [Paragraph("Pacote Mensal", S['H2'])]
    if pacote_recomendado == "mensal":
        mensal_elements.append(_make_badge())
        mensal_elements.append(Spacer(1, 1 * mm))
    mensal_elements.append(_make_pkg_table(mensal_items, pacote_recomendado == "mensal"))
    story.append(KeepTogether(mensal_elements))
    story.append(Spacer(1, 3 * mm))

    # --- SEMANAL ---
    semanal_items = [
        ["Relatório Semanal Resumido", "4x por mês (toda segunda-feira)"],
        ["Relatório Executivo Completo", "1x por mês (consolidado)"],
        ["Abrangência", ufs_semanal_txt],
        ["Análise documental (PDFs)", "Até 8 editais"],
        ["Alertas de prazo crítico", "WhatsApp quando edital encerra em < 7 dias"],
        ["Suporte WhatsApp", "Horário estendido (8h-20h, seg-sáb)"],
        ["Valor mensal", "R$ 1.500/mês"],
        ["Valor anual (pague 10, leve 12)", "R$ 15.000/ano (= R$ 1.250/mês)"],
    ]
    semanal_elements = [Paragraph("Pacote Semanal", S['H2'])]
    if pacote_recomendado == "semanal":
        semanal_elements.append(_make_badge())
        semanal_elements.append(Spacer(1, 1 * mm))
    semanal_elements.append(_make_pkg_table(semanal_items, pacote_recomendado == "semanal"))
    story.append(KeepTogether(semanal_elements))
    story.append(Spacer(1, 3 * mm))

    # --- DIÁRIO ---
    diario_items = [
        ["Alertas diários de novos editais", "Todos os dias úteis (WhatsApp + Email)"],
        ["Relatório Semanal + Mensal", "4x semanal + 1x mensal"],
        ["Abrangência", ufs_diario_txt],
        ["Análise documental (PDFs)", "Ilimitada"],
        ["Monitoramento de concorrentes", "Sim"],
        ["Estratégia de precificação", "Sugestão de desconto por edital"],
        ["Suporte dedicado", "WhatsApp + Tel (8h-22h, seg-dom)"],
        ["Valor mensal", "R$ 2.997/mês"],
        ["Valor anual (pague 10, leve 12)", "R$ 29.970/ano (= R$ 2.498/mês)"],
    ]
    diario_elements = [Paragraph("Pacote Diário", S['H2'])]
    if pacote_recomendado == "diario":
        diario_elements.append(_make_badge())
        diario_elements.append(Spacer(1, 1 * mm))
    diario_elements.append(_make_pkg_table(diario_items, pacote_recomendado == "diario"))
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
            ["UFs monitoradas", uf_sede, ufs_semanal_txt, ufs_diario_txt],
            ["Alerta prazo crítico", "—", "Sim", "Imediato"],
            ["Monit. concorrentes", "—", "—", "Sim"],
            ["Valor mensal", "R$ 997", "R$ 1.500", "R$ 2.997"],
            ["Valor anual (10 meses)", "R$ 9.970", "R$ 15.000", "R$ 29.970"],
        ], cw_cmp
    ))
    story.append(PageBreak())

    # ==========================================================
    # 6. QUEM ANALISA SEUS EDITAIS
    # ==========================================================
    story.append(Paragraph("6. Quem Analisa Seus Editais", S['H1']))
    story.append(hr())
    story.append(Paragraph(
        "<b>Tiago Sasaki — Engenheiro e servidor público efetivo há 7 anos, "
        "com experiência direta em processos licitatórios pelo lado do órgão público.</b>",
        S['BodyBold']
    ))
    story.append(Spacer(1, 2 * mm))

    story.append(Paragraph("O Que Significa 'Do Outro Lado do Balcão'", S['H2']))
    story.append(Paragraph(
        "Nos últimos 7 anos, participei diretamente de processos licitatórios pelo lado do "
        "órgão público: elaborei termos de referência, analisei propostas de habilitação, "
        "acompanhei execuções contratuais e vi, de perto, os erros mais comuns que eliminam "
        "empresas qualificadas antes mesmo da fase de preços.",
        S['Body']
    ))

    authority_items = data.get("autoridade_exemplos", _DEFAULT_AUTHORITY)
    for item in authority_items:
        story.append(bullet(fix_accents(item)))

    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("Tecnologia Proprietária", S['H2']))
    story.append(Paragraph(
        "Além da experiência como servidor, desenvolvi o SmartLic — plataforma de inteligência "
        "artificial que monitora continuamente as publicações oficiais de contratações públicas, "
        "classifica editais por setor com IA e gera análises de viabilidade personalizadas. "
        "Cada relatório combina varredura automatizada com análise humana de quem "
        "conhece a máquina por dentro.",
        S['Body']
    ))

    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("Diferenciais", S['H2']))
    cw_dif = [CONTENT_W / 2] * 2
    story.append(make_table(
        ["Consultoria Tradicional", "Consultoria Tiago Sasaki"],
        [
            ["Busca manual em portais", "Varredura automática diária com IA — cobertura total"],
            ["Planilha genérica de editais", "Relatório personalizado — 17 campos analisados por edital"],
            ["Analista sem vivência no órgão", "7 anos como servidor — entende a lógica de quem compra"],
            ["Leitura superficial do edital", "PDF do edital lido com checklist de habilitação e red flags"],
            ["Sem filtragem setorial", "Classificação automática — zero ruído, só editais do seu setor"],
            ["Alerta genérico", "Recomendação PARTICIPAR/NÃO PARTICIPAR com justificativa detalhada"],
        ], cw_dif, header_color=DARK_BLUE
    ))
    story.append(PageBreak())

    # ==========================================================
    # 7. CONDIÇÕES COMERCIAIS
    # ==========================================================
    pkg_names = {"mensal": "Mensal", "semanal": "Semanal", "diario": "Diário"}
    pkg_name = pkg_names.get(pacote_recomendado, "Semanal")

    story.append(Paragraph("7. Condições Comerciais", S['H1']))
    story.append(hr())
    story.append(Paragraph(f"Pacote Recomendado: {pkg_name}", S['H2']))

    investimento_anual_desc = investimento * 10  # pague 10, leve 12
    economia_anual = investimento * 2

    inv_fmt = f"{investimento:,.0f}".replace(",", ".")
    inv_anual_fmt2 = f"{investimento_anual_desc:,.0f}".replace(",", ".")
    eco_fmt = f"{economia_anual:,.0f}".replace(",", ".")
    story.append(make_kv([
        ["Pacote", pkg_name],
        ["Investimento mensal", f"R$ {inv_fmt}/mês"],
        ["Pagamento anual adiantado", f"R$ {inv_anual_fmt2}/ano (pague 10, leve 12)"],
        ["Economia no plano anual", f"R$ {eco_fmt} (2 meses de cortesia)"],
        ["Forma de pagamento", "Boleto, PIX ou Cartão de Crédito"],
        ["Prazo mínimo", "3 meses"],
        ["Cancelamento", "30 dias de antecedência"],
        ["Início", "Imediato após aceite"],
        ["Primeiro relatório", "Até 3 dias úteis após contratação"],
    ], kw=52 * mm))
    story.append(Spacer(1, 4 * mm))

    # Oferta especial
    cond_especial_elements = [Spacer(1, 2 * mm)]
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

    cond_text = (
        f"Para contratações formalizadas até <b>{validity_fmt}</b>, o primeiro mês de monitoramento "
        f"é cortesia — a empresa já recebe o primeiro relatório completo com "
        f"as oportunidades do setor de {setor.lower()}."
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
    cond_especial_elements.append(Paragraph("Após esta data, a condição padrão se aplica.", S['Small']))
    story.append(KeepTogether(cond_especial_elements))
    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph("O Que NÃO Está Incluído", S['H2']))
    for item in [
        "Elaboração de propostas comerciais (documentos de habilitação são responsabilidade da empresa)",
        "Representação presencial em sessões de licitação",
        "Serviços jurídicos (impugnações, recursos)",
        "Execução do objeto contratado",
        "Garantias financeiras",
    ]:
        story.append(bullet(item))
    story.append(Paragraph(
        "Estes serviços podem ser contratados separadamente sob demanda.", S['Small']
    ))
    story.append(PageBreak())

    # ==========================================================
    # 8. PRÓXIMOS PASSOS
    # ==========================================================
    story.append(Paragraph("8. Próximos Passos", S['H1']))
    story.append(hr())

    story.append(Paragraph("Após Aceite", S['H2']))
    cw_steps = [30 * mm, 22 * mm, CONTENT_W - 52 * mm]
    story.append(make_table(
        ["Etapa", "Quando", "O Que Acontece"],
        [
            ["Aceite", "Dia 0", "Confirmação via WhatsApp ou email"],
            ["Onboarding", "Dia 1-2", "Alinhamento: UFs, faixa de valor, tipos de contratação"],
            ["Primeiro Relatório", "Dia 3-5", "Relatório completo + plano de ação"],
            ["Monitoramento", "Dia 6+", "Relatórios na frequência contratada"],
        ], cw_steps
    ))
    story.append(Spacer(1, 4 * mm))

    # CTA
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

    story.append(Paragraph(
        f"Novos editais são publicados semanalmente. Cada semana sem monitoramento "
        f"é um conjunto de oportunidades que passa sem que a {nome} sequer saiba que existiram.",
        S['Quote']
    ))

    story.append(Spacer(1, 6 * mm))

    # Contact block
    story.append(HRFlowable(width="40%", thickness=1, color=NAVY, spaceAfter=4 * mm, spaceBefore=4 * mm))
    story.append(Paragraph("<b>Tiago Sasaki</b>", S['Body']))
    story.append(Paragraph("Engenheiro | Servidor Público Efetivo", S['Body']))
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
        f"Proposta preparada em {today_fmt}. Projeções são estimativas baseadas em "
        f"médias setoriais; resultados dependem da participação e execução da empresa.",
        S['Small']
    ))

    # ==========================================================
    # BUILD
    # ==========================================================
    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(HexColor("#a0aec0"))
        canvas.drawCentredString(PAGE_W / 2, 10 * mm, FOOTER_TEXT)
        canvas.drawRightString(PAGE_W - MARGIN, 10 * mm, f"Página {doc.page}")
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
        description="Gerador de PDF de Proposta Comercial B2G v5"
    )
    parser.add_argument(
        "input_positional", nargs="?", default=None,
        help="Caminho do JSON de dados (argumento posicional)"
    )
    parser.add_argument(
        "output_positional", nargs="?", default=None,
        help="Caminho do PDF de saída (argumento posicional)"
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

    data_path = args.input_file or args.input_positional
    output_path = args.output_file or args.output_positional or "docs/propostas/proposta-output.pdf"

    if not data_path:
        print("ERROR: Informe o caminho do JSON de dados (--input ou argumento posicional)")
        sys.exit(1)

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    build_pdf(data, output_path, pacote_recomendado=args.pacote)
