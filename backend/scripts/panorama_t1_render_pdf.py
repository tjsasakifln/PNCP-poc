"""Panorama Licitações Brasil 2026 T1 — PDF Renderer.

Consumes the JSON produced by panorama_t1_extract.py and renders an
8-10 page report PDF using reportlab (already in backend/requirements.txt).

Matplotlib is NOT a dependency of this project, so the renderer is
text+table only. Charts can be added later if mpl is introduced.

Usage:
    # After running extract:
    python backend/scripts/panorama_t1_render_pdf.py

Output:
    data/panorama_t1/panorama-2026-t1.pdf
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger("panorama_t1_render_pdf")
logging.basicConfig(level=logging.INFO, format="[panorama-t1-pdf] %(message)s")

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_INPUT = _BACKEND_DIR.parent / "data" / "panorama_t1" / "data.json"
_DEFAULT_OUTPUT = _BACKEND_DIR.parent / "data" / "panorama_t1" / "panorama-2026-t1.pdf"

SMARTLIC_GREEN = colors.HexColor("#2E7D32")
SMARTLIC_DARK = colors.HexColor("#1B5E20")
LIGHT_GREY = colors.HexColor("#F5F5F5")


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _fmt_brl(value: float) -> str:
    """Format a numeric value as BRL with pt-BR thousand separators."""
    try:
        v = float(value or 0)
    except (TypeError, ValueError):
        return "R$ 0,00"
    if v >= 1_000_000_000:
        return f"R$ {v / 1_000_000_000:.2f} bi".replace(".", ",")
    if v >= 1_000_000:
        return f"R$ {v / 1_000_000:.2f} mi".replace(".", ",")
    if v >= 1_000:
        return f"R$ {v / 1_000:.1f} k".replace(".", ",")
    return f"R$ {v:.2f}".replace(".", ",")


def _fmt_int(value: int | float) -> str:
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "0"


def _styles():
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "TitleCustom",
            parent=base["Title"],
            fontSize=26,
            textColor=SMARTLIC_DARK,
            spaceAfter=14,
            leading=32,
        ),
        "Subtitle": ParagraphStyle(
            "SubtitleCustom",
            parent=base["Normal"],
            fontSize=14,
            textColor=colors.HexColor("#555555"),
            spaceAfter=10,
            leading=18,
        ),
        "H1": ParagraphStyle(
            "H1Custom",
            parent=base["Heading1"],
            fontSize=18,
            textColor=SMARTLIC_GREEN,
            spaceAfter=10,
            leading=22,
        ),
        "H2": ParagraphStyle(
            "H2Custom",
            parent=base["Heading2"],
            fontSize=13,
            textColor=SMARTLIC_DARK,
            spaceAfter=8,
        ),
        "Body": ParagraphStyle(
            "BodyCustom",
            parent=base["Normal"],
            fontSize=10.5,
            leading=15,
            spaceAfter=8,
        ),
        "Small": ParagraphStyle(
            "SmallCustom",
            parent=base["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#777777"),
            leading=12,
        ),
        "CTA": ParagraphStyle(
            "CTACustom",
            parent=base["Heading1"],
            fontSize=16,
            textColor=SMARTLIC_GREEN,
            alignment=1,  # center
            spaceAfter=10,
        ),
    }


def _table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), SMARTLIC_GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#DDDDDD")),
        ]
    )


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------


def _cover_page(styles: dict, data: dict) -> list:
    meta = data.get("metadata", {})
    return [
        Spacer(1, 4 * cm),
        Paragraph("Panorama Licitações Brasil 2026 T1", styles["Title"]),
        Paragraph(
            "Análise de editais PNCP · Janeiro a Março de 2026",
            styles["Subtitle"],
        ),
        Spacer(1, 1 * cm),
        Paragraph(
            f"Janela de análise: {meta.get('window_start', '2026-01-01')} a "
            f"{meta.get('window_end', '2026-04-01')} (exclusivo)",
            styles["Body"],
        ),
        Paragraph(
            f"Gerado em: {meta.get('generated_at', datetime.utcnow().isoformat())}",
            styles["Body"],
        ),
        Spacer(1, 6 * cm),
        Paragraph(
            "SmartLic — Inteligência em Licitações Públicas<br/>"
            "CONFENGE Avaliações e Inteligência Artificial LTDA",
            styles["Body"],
        ),
        Paragraph(
            "https://smartlic.tech",
            styles["Small"],
        ),
        PageBreak(),
    ]


def _executive_summary(styles: dict, data: dict) -> list:
    modalidades = data.get("modalidades", []) or []
    top_sectors = data.get("top_sectors", []) or []
    uf_growth = data.get("uf_growth", []) or []
    quartiles = data.get("value_quartiles", {}) or {}

    top_mod = modalidades[0] if modalidades else None
    top_sector = top_sectors[0] if top_sectors else None
    top_uf = uf_growth[0] if uf_growth else None

    insights = []
    if top_mod:
        insights.append(
            f"<b>{top_mod.get('modalidade_nome', 'N/D')}</b> liderou o trimestre "
            f"com {_fmt_int(top_mod.get('count', 0))} editais "
            f"({top_mod.get('pct', 0)}% do total)."
        )
    if top_sector:
        insights.append(
            f"Setor de maior volume: <b>{top_sector.get('setor', 'N/D')}</b> "
            f"com {_fmt_int(top_sector.get('count', 0))} editais e valor agregado "
            f"estimado de {_fmt_brl(top_sector.get('valor_total', 0))}."
        )
    if top_uf:
        insights.append(
            f"<b>{top_uf.get('uf', 'N/D')}</b> foi a UF com maior número absoluto "
            f"de editais publicados ({_fmt_int(top_uf.get('count_2026_t1', 0))})."
        )
    if quartiles and quartiles.get("count", 0) > 0:
        insights.append(
            f"Valor mediano por edital: <b>{_fmt_brl(quartiles.get('p50', 0))}</b> "
            f"(base de {_fmt_int(quartiles.get('count', 0))} editais com valor declarado)."
        )

    bullets = "".join(f"• {txt}<br/><br/>" for txt in insights) or "• Dados insuficientes para o período.<br/>"

    return [
        Paragraph("Sumário Executivo", styles["H1"]),
        Paragraph(
            "Este relatório consolida os editais publicados no Portal Nacional "
            "de Contratações Públicas (PNCP) no primeiro trimestre de 2026, "
            "agrupados por setor inferido, UF, modalidade e distribuição de valor. "
            "Os dados são extraídos do data lake SmartLic (tabela pncp_raw_bids).",
            styles["Body"],
        ),
        Spacer(1, 0.4 * cm),
        Paragraph("Principais achados", styles["H2"]),
        Paragraph(bullets, styles["Body"]),
        PageBreak(),
    ]


def _top_sectors_section(styles: dict, data: dict) -> list:
    rows = data.get("top_sectors", []) or []
    table_data = [["Setor (inferido)", "Editais", "Valor total (est.)"]]
    for r in rows:
        table_data.append(
            [
                r.get("setor", ""),
                _fmt_int(r.get("count", 0)),
                _fmt_brl(r.get("valor_total", 0)),
            ]
        )
    if len(table_data) == 1:
        table_data.append(["Sem dados no período", "—", "—"])

    t = Table(table_data, colWidths=[8 * cm, 3 * cm, 5 * cm])
    t.setStyle(_table_style())

    return [
        Paragraph("1. Setores quentes", styles["H1"]),
        Paragraph(
            "Ranking dos 10 setores com maior número de editais publicados no "
            "trimestre. A classificação é inferida via keyword-matching sobre o "
            "campo objeto_compra — é uma aproximação coarse para uso em reporting "
            "público, não classificação fina por CNAE.",
            styles["Body"],
        ),
        Spacer(1, 0.3 * cm),
        t,
        PageBreak(),
    ]


def _uf_section(styles: dict, data: dict) -> list:
    rows = data.get("uf_growth", []) or []
    table_data = [["UF", "2026 T1", "2025 T1", "Variação YoY"]]
    for r in rows:
        growth = r.get("growth_pct")
        growth_str = f"{growth:+.1f}%" if isinstance(growth, (int, float)) else "—"
        table_data.append(
            [
                r.get("uf", ""),
                _fmt_int(r.get("count_2026_t1", 0)),
                _fmt_int(r.get("count_2025_t1", 0)),
                growth_str,
            ]
        )
    if len(table_data) == 1:
        table_data.append(["—", "—", "—", "—"])

    t = Table(table_data, colWidths=[3 * cm, 3.5 * cm, 3.5 * cm, 4 * cm])
    t.setStyle(_table_style())

    return [
        Paragraph("2. UFs em destaque", styles["H1"]),
        Paragraph(
            "Top 10 UFs pelo volume absoluto de editais em 2026 T1, com comparativo "
            "YoY contra o mesmo período de 2025 quando disponível.",
            styles["Body"],
        ),
        Spacer(1, 0.3 * cm),
        t,
        PageBreak(),
    ]


def _modalidades_section(styles: dict, data: dict) -> list:
    rows = data.get("modalidades", []) or []
    table_data = [["Modalidade", "Editais", "% do total", "Valor total"]]
    for r in rows:
        table_data.append(
            [
                r.get("modalidade_nome", ""),
                _fmt_int(r.get("count", 0)),
                f"{r.get('pct', 0)}%",
                _fmt_brl(r.get("valor_total", 0)),
            ]
        )
    if len(table_data) == 1:
        table_data.append(["—", "—", "—", "—"])

    t = Table(table_data, colWidths=[5 * cm, 3 * cm, 3 * cm, 4.5 * cm])
    t.setStyle(_table_style())

    return [
        Paragraph("3. Distribuição por modalidade", styles["H1"]),
        Paragraph(
            "Volume e valor estimado por modalidade de contratação. Pregão "
            "Eletrônico tipicamente domina o mix pós-Lei 14.133 — acompanhe "
            "a evolução de Dispensa (mod 12) como indicador de descentralização.",
            styles["Body"],
        ),
        Spacer(1, 0.3 * cm),
        t,
        PageBreak(),
    ]


def _quartiles_section(styles: dict, data: dict) -> list:
    q = data.get("value_quartiles", {}) or {}
    table_data = [
        ["Métrica", "Valor"],
        ["P25", _fmt_brl(q.get("p25", 0))],
        ["P50 (mediana)", _fmt_brl(q.get("p50", 0))],
        ["P75", _fmt_brl(q.get("p75", 0))],
        ["Média", _fmt_brl(q.get("mean", 0))],
        ["Base (editais com valor)", _fmt_int(q.get("count", 0))],
    ]

    t = Table(table_data, colWidths=[8 * cm, 6 * cm])
    t.setStyle(_table_style())

    return [
        Paragraph("4. Distribuição de valores", styles["H1"]),
        Paragraph(
            "Quartis do valor_total_estimado (excluindo editais sem valor declarado "
            "e registros com valor zero). A mediana é mais representativa do que "
            "a média por conta de grandes outliers em contratos de infraestrutura.",
            styles["Body"],
        ),
        Spacer(1, 0.3 * cm),
        t,
        PageBreak(),
    ]


def _seasonality_section(styles: dict, data: dict) -> list:
    rows = data.get("seasonality", []) or []
    table_data = [["Mês", "Editais", "Valor total"]]
    for r in rows:
        table_data.append(
            [
                r.get("month", ""),
                _fmt_int(r.get("count", 0)),
                _fmt_brl(r.get("valor_total", 0)),
            ]
        )
    if len(table_data) == 1:
        table_data.append(["—", "—", "—"])

    t = Table(table_data, colWidths=[4 * cm, 4 * cm, 6 * cm])
    t.setStyle(_table_style())

    return [
        Paragraph("5. Sazonalidade mensal", styles["H1"]),
        Paragraph(
            "Publicações agrupadas por mês dentro da janela 2026 T1. Meses com "
            "pico absoluto tipicamente correspondem ao fechamento de ciclos "
            "orçamentários (março) ou ao início de planejamentos anuais (janeiro).",
            styles["Body"],
        ),
        Spacer(1, 0.3 * cm),
        t,
        PageBreak(),
    ]


def _methodology_page(styles: dict) -> list:
    return [
        Paragraph("6. Metodologia e limitações", styles["H1"]),
        Paragraph(
            "<b>Fonte.</b> Tabela pncp_raw_bids do data lake SmartLic, populada por "
            "ingestão periódica do Portal Nacional de Contratações Públicas (PNCP) — "
            "endpoint /api/consulta/v1/contratacoes/publicacao. Escopo: 27 UFs x 6 "
            "modalidades principais (4, 5, 6, 7, 8, 12), janela 2026-01-01 a 2026-03-31 "
            "(exclusivo superior).",
            styles["Body"],
        ),
        Paragraph(
            "<b>Dedup.</b> Cada linha de pncp_raw_bids é deduplicada por content_hash "
            "(MD5 dos campos mutáveis) — retificações geram novas linhas apenas quando "
            "campos relevantes mudam.",
            styles["Body"],
        ),
        Paragraph(
            "<b>Inferência de setor.</b> Classificação coarse via keyword-matching "
            "sobre objeto_compra (10 categorias principais). Não é substituto da "
            "classificação setorial fina do SmartLic (15 setores, LLM arbiter), "
            "que opera em runtime durante buscas dos usuários.",
            styles["Body"],
        ),
        Paragraph(
            "<b>Tratamento de valores.</b> Editais sem valor declarado (NULL) ou com "
            "valor zero são excluídos apenas dos cálculos de quartil e média. Eles "
            "permanecem nas contagens de volume.",
            styles["Body"],
        ),
        Paragraph(
            "<b>Limitações.</b> (1) Editais publicados fora do PNCP (sistemas "
            "estaduais legados, Lei 8.666 residual) não estão cobertos. (2) "
            "Cancelamentos e anulações posteriores à data de corte não se refletem. "
            "(3) A inferência de setor por keywords tem precisão limitada para "
            "objetos de compra compostos ou ambíguos.",
            styles["Body"],
        ),
        Paragraph(
            "<b>Disclaimer.</b> SmartLic e CONFENGE não se responsabilizam por "
            "decisões de negócio tomadas com base exclusivamente neste relatório. "
            "Os dados são válidos na data de geração e podem mudar conforme o PNCP "
            "republica ou corrige registros.",
            styles["Small"],
        ),
        PageBreak(),
    ]


def _cta_page(styles: dict) -> list:
    return [
        Spacer(1, 5 * cm),
        Paragraph("Quer esses dados ao vivo?", styles["CTA"]),
        Spacer(1, 0.5 * cm),
        Paragraph(
            "O SmartLic monitora o PNCP em tempo real, classifica editais pelo seu "
            "setor e entrega alertas diários diretamente no seu pipeline. "
            "Teste gratuitamente por 14 dias, sem cartão.",
            ParagraphStyle(
                "CTABody",
                parent=styles["Body"],
                fontSize=12,
                alignment=1,
                leading=18,
            ),
        ),
        Spacer(1, 1 * cm),
        Paragraph(
            '<a href="https://smartlic.tech/signup?utm_source=panorama_t1&utm_medium=pdf">'
            "<b>smartlic.tech/signup</b></a>",
            ParagraphStyle(
                "CTALink",
                parent=styles["Body"],
                fontSize=14,
                textColor=SMARTLIC_GREEN,
                alignment=1,
            ),
        ),
        Spacer(1, 4 * cm),
        Paragraph(
            "CONFENGE Avaliações e Inteligência Artificial LTDA<br/>"
            "contato@smartlic.tech",
            styles["Small"],
        ),
    ]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def render(input_path: Path | None = None, output_path: Path | None = None) -> Path:
    in_path = input_path or _DEFAULT_INPUT
    out_path = output_path or _DEFAULT_OUTPUT

    if not in_path.exists():
        raise FileNotFoundError(
            f"Input JSON not found: {in_path}. "
            "Run backend/scripts/panorama_t1_extract.py first."
        )

    data = json.loads(in_path.read_text(encoding="utf-8"))
    out_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title="Panorama Licitações Brasil 2026 T1",
        author="SmartLic / CONFENGE",
    )

    styles = _styles()
    story: list = []
    story.extend(_cover_page(styles, data))
    story.extend(_executive_summary(styles, data))
    story.extend(_top_sectors_section(styles, data))
    story.extend(_uf_section(styles, data))
    story.extend(_modalidades_section(styles, data))
    story.extend(_quartiles_section(styles, data))
    story.extend(_seasonality_section(styles, data))
    story.extend(_methodology_page(styles))
    story.extend(_cta_page(styles))

    doc.build(story)
    logger.info("Wrote PDF: %s (%d bytes)", out_path, out_path.stat().st_size)
    return out_path


def main() -> None:
    render()


if __name__ == "__main__":
    main()
