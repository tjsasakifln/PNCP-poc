#!/usr/bin/env python3
"""
Template abstraction for B2G Report PDF generation.

Separates content structure from presentation logic.
Each template function takes raw data and returns a structured
dict ready for rendering. The PDF generator calls these instead
of doing inline data extraction.

This enables:
  1. Testing content generation independently of PDF rendering
  2. Supporting multiple output formats (PDF, HTML, Markdown) from same templates
  3. Iterating on content structure without touching ReportLab code

Usage:
    from report_templates import build_cover_data, build_edital_card, build_executive_summary

    cover = build_cover_data(data)
    # cover = {"empresa": "Razao Social", "cnpj": "12.345.678/0001-90", ...}
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Formatting utilities (pure functions, no ReportLab dependency)
# ---------------------------------------------------------------------------

def format_brl(value: float | None) -> str:
    """Format as Brazilian Real: R$ 1.500.000,00 (or 'N/D' if None/invalid)."""
    if value is None:
        return "Não informado"
    try:
        v = float(value)
    except (ValueError, TypeError):
        return "Não informado"
    if v == 0:
        return "R$ 0,00"
    formatted = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def format_brl_short(value: float | None) -> str:
    """Compact BRL: R$ 1,5M / R$ 800K / R$ 1.200,00."""
    if value is None:
        return "Não informado"
    try:
        v = float(value)
    except (ValueError, TypeError):
        return "Não informado"
    if v >= 1_000_000:
        return f"R$ {v / 1_000_000:,.1f}M".replace(",", "X").replace(".", ",").replace("X", ".")
    if v >= 1_000:
        return f"R$ {v / 1_000:,.0f}K".replace(",", "X").replace(".", ",").replace("X", ".")
    return format_brl(v)


def format_date_br(date_str: str | None) -> str:
    """Convert YYYY-MM-DD (or variants) to DD/MM/YYYY. Returns 'N/D' if None/invalid."""
    if not date_str:
        return "Não informado"
    text = str(date_str).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y", "%Y%m%d"):
        try:
            dt = datetime.strptime(text[:10], fmt)
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            continue
    return "Não informado"


def format_percentage(value: float | None, decimals: int = 1) -> str:
    """Format as XX,X% (Brazilian locale). Returns 'N/D' if None/invalid.

    Expects values in 0-1 range (ratios) or 0-100 range.
    Values <= 1.0 are treated as ratios and multiplied by 100.
    Values > 1.0 are treated as already being percentages.
    """
    if value is None:
        return "Não informado"
    try:
        v = float(value)
    except (ValueError, TypeError):
        return "Não informado"
    # Heuristic: if <= 1.0, treat as ratio (0.0-1.0)
    if v <= 1.0:
        v = v * 100
    return f"{v:.{decimals}f}%".replace(".", ",")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_SAFE_TEXT_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _safe_str(value: Any) -> str:
    """Sanitize value to a clean string, stripping illegal chars."""
    if value is None:
        return ""
    return _SAFE_TEXT_RE.sub(" ", str(value))


def _safe_float(v: Any, default: float = 0.0) -> float:
    """Safely convert to float."""
    if v is None:
        return default
    try:
        if isinstance(v, str):
            v = v.replace(",", ".")
        return float(v)
    except (ValueError, TypeError):
        return default


def _safe_int(v: Any, default: int = 0) -> int:
    """Safely convert to int."""
    if v is None:
        return default
    try:
        return int(v)
    except (ValueError, TypeError):
        return default


def _trunc(text: str, n: int = 100) -> str:
    """Truncate text to n chars with ellipsis."""
    text = _safe_str(text)
    return text if len(text) <= n else text[:n - 3].rstrip() + "..."


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%d/%m/%Y")


def _normalize_recommendation(rec: str) -> str:
    """Normalize recommendation string to canonical form."""
    rec = rec.strip().upper()
    rec = rec.replace("NAO RECOMENDADO", "NAO RECOMENDADO")
    rec = rec.replace("NAO ", "NAO ")
    if "PARTICIPAR" in rec:
        return "PARTICIPAR"
    if "CAUTELA" in rec or "AVALIAR" in rec:
        return "AVALIAR COM CAUTELA"
    if "NAO" in rec or "RECOMENDADO" in rec:
        return "NAO RECOMENDADO"
    return rec


def _recommendation_color(rec: str) -> str:
    """Map recommendation to a semantic color name."""
    rec_upper = rec.upper()
    if "PARTICIPAR" in rec_upper:
        return "green"
    if "AVALIAR" in rec_upper or "CAUTELA" in rec_upper:
        return "amber"
    return "red"


def _collapse_cnaes(cnaes: Any, max_show: int = 5) -> str:
    """Collapse CNAE list into readable string."""
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


def _fix_pncp_link(link: str | None) -> str | None:
    """Normalize PNCP links from hyphenated to slash format."""
    if not link:
        return None
    link = str(link).strip()
    m = re.match(r"https://pncp\.gov\.br/app/editais/(\d{14})-(\d{4})-(\d+)$", link)
    if m:
        cnpj, ano, seq = m.groups()
        return f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"
    if re.match(r"https://pncp\.gov\.br/app/editais\?q=", link):
        return None
    return link


# ---------------------------------------------------------------------------
# Template functions
# ---------------------------------------------------------------------------

def build_cover_data(data: dict) -> dict:
    """Extract cover page data from report JSON.

    Returns:
        dict with keys: empresa, cnpj, date, setor, report_type,
        cidade, uf, nome_fantasia, razao_social
    """
    empresa = data.get("empresa", {})
    nome_fantasia = _safe_str(empresa.get("nome_fantasia", ""))
    razao_social = _safe_str(empresa.get("razao_social", ""))

    # Determine report type from delivery validation gate
    delivery = data.get("delivery_validation", {}) or {}
    gate = delivery.get("gate_deterministic") or delivery.get("gate_adversarial", "")
    has_enrichment = bool(data.get("resumo_executivo")) and bool(data.get("editais"))
    report_type = "EXECUTIVO" if has_enrichment else "DETERMINISTICO"

    return {
        "empresa": nome_fantasia or razao_social,
        "razao_social": razao_social,
        "nome_fantasia": nome_fantasia,
        "cnpj": _safe_str(empresa.get("cnpj", "")),
        "date": _today(),
        "setor": _safe_str(data.get("setor", "")),
        "report_type": report_type,
        "cidade": _safe_str(empresa.get("cidade_sede", "")),
        "uf": _safe_str(empresa.get("uf_sede", "")),
        "gate_result": gate,
    }


def build_executive_summary(data: dict) -> dict:
    """Extract executive summary content from report JSON.

    Returns:
        dict with keys: texto, destaques, recommendation_counts,
        total_valor, gate_result, tese_estrategica, n_editais,
        valor_participar
    """
    resumo = data.get("resumo_executivo", {}) or {}
    editais = data.get("editais", [])

    # Count recommendations
    participar = 0
    avaliar = 0
    nao_recomendado = 0
    total_valor = 0.0
    valor_participar = 0.0

    for e in editais:
        rec = _normalize_recommendation(_safe_str(e.get("recomendacao", "")))
        valor = _safe_float(e.get("valor_estimado"))
        total_valor += valor

        if rec == "PARTICIPAR":
            participar += 1
            valor_participar += valor
        elif rec == "AVALIAR COM CAUTELA":
            avaliar += 1
        elif rec == "NAO RECOMENDADO":
            nao_recomendado += 1

    # Gate result from delivery validation
    delivery = data.get("delivery_validation", {}) or {}
    gate_result = delivery.get("gate_adversarial", "")

    # Strategic thesis
    thesis_data = data.get("strategic_thesis") or {}
    tese = {}
    if thesis_data.get("thesis"):
        tese = {
            "thesis": thesis_data["thesis"],
            "rationale": _safe_str(thesis_data.get("rationale", "")),
        }

    return {
        "texto": _safe_str(resumo.get("texto", "")),
        "destaques": [_safe_str(d) for d in resumo.get("destaques", [])],
        "recommendation_counts": {
            "participar": participar,
            "avaliar": avaliar,
            "nao_recomendado": nao_recomendado,
        },
        "n_editais": len(editais),
        "total_valor": total_valor,
        "total_valor_formatted": format_brl_short(total_valor),
        "valor_participar": valor_participar,
        "valor_participar_formatted": format_brl_short(valor_participar),
        "gate_result": gate_result,
        "tese_estrategica": tese,
    }


def build_empresa_profile(data: dict) -> dict:
    """Extract structured empresa profile from report JSON.

    Returns:
        dict with keys: razao_social, nome_fantasia, cnpj, cnae_principal,
        cnaes_secundarios, porte, capital_social, capital_social_formatted,
        cidade, uf, sede, situacao_cadastral, socios, sancoes_status,
        sancoes_detail, sicaf_status, regime_tributario, historico_contratos,
        maturity_profile
    """
    emp = data.get("empresa", {})

    # Sanctions status
    sancoes = emp.get("sancoes", {}) or {}
    is_inconclusive = sancoes.get("inconclusive", False)
    has_sanction = any(sancoes.get(k) for k in ["ceis", "cnep", "cepim", "ceaf"])

    if is_inconclusive:
        sancoes_status = "PENDENTE"
    elif has_sanction:
        active = [label for k, label in [("ceis", "CEIS"), ("cnep", "CNEP"),
                                          ("cepim", "CEPIM"), ("ceaf", "CEAF")]
                  if sancoes.get(k)]
        sancoes_status = "ATIVA"
    else:
        sancoes_status = "LIMPA"

    sancoes_detail = []
    if has_sanction:
        for k, label in [("ceis", "CEIS"), ("cnep", "CNEP"),
                         ("cepim", "CEPIM"), ("ceaf", "CEAF")]:
            if sancoes.get(k):
                sancoes_detail.append(label)

    # Socios
    qsa = emp.get("qsa", [])
    socios = []
    for socio in qsa[:10]:
        if isinstance(socio, dict):
            socios.append({
                "nome": _safe_str(socio.get("nome", "")),
                "qualificacao": _safe_str(socio.get("qualificacao", "")),
            })
        else:
            socios.append({"nome": _safe_str(socio), "qualificacao": ""})

    # SICAF
    sicaf = data.get("sicaf", {}) or {}
    sicaf_source = sicaf.get("_source", {}) if isinstance(sicaf, dict) else {}
    sicaf_status_raw = ""
    if isinstance(sicaf_source, dict):
        sicaf_status_raw = sicaf_source.get("status", "")
    elif isinstance(sicaf_source, str):
        sicaf_status_raw = sicaf_source
    sicaf_status = sicaf_status_raw or "NAO_VERIFICADO"

    # Regime tributario
    simples = emp.get("simples_nacional")
    mei = emp.get("mei")
    if mei:
        regime = "MEI"
    elif simples:
        data_opcao = emp.get("data_opcao_simples", "")
        regime = f"Simples Nacional{' (desde ' + str(data_opcao)[:10] + ')' if data_opcao else ''}"
    elif simples is False:
        regime = "Regime Geral"
    else:
        regime = ""

    # Capital social
    capital = emp.get("capital_social")
    capital_formatted = format_brl(capital) if capital else "Não informado"

    # Sede
    cidade = _safe_str(emp.get("cidade_sede", ""))
    uf = _safe_str(emp.get("uf_sede", ""))
    sede = ""
    if cidade and uf:
        sede = f"{cidade}/{uf}"
    elif cidade:
        sede = cidade
    elif uf:
        sede = uf

    # Maturity profile
    maturity = data.get("maturity_profile") or emp.get("maturity_profile", {}) or {}
    maturity_info = {}
    if maturity.get("profile"):
        maturity_info = {
            "profile": maturity["profile"],
            "rationale": _safe_str(maturity.get("rationale", "")),
        }

    # Historico contratos
    historico = emp.get("historico_contratos", [])
    hist_total_valor = sum(_safe_float(c.get("valor")) for c in historico)

    return {
        "razao_social": _safe_str(emp.get("razao_social", "")),
        "nome_fantasia": _safe_str(emp.get("nome_fantasia", "")),
        "cnpj": _safe_str(emp.get("cnpj", "")),
        "cnae_principal": _safe_str(emp.get("cnae_principal", "")),
        "cnaes_secundarios": _collapse_cnaes(emp.get("cnaes_secundarios")),
        "porte": _safe_str(emp.get("porte", "")),
        "capital_social": _safe_float(capital) if capital else None,
        "capital_social_formatted": capital_formatted,
        "cidade": cidade,
        "uf": uf,
        "sede": sede,
        "situacao_cadastral": _safe_str(emp.get("situacao_cadastral", "")),
        "socios": socios,
        "sancoes_status": sancoes_status,
        "sancoes_detail": sancoes_detail,
        "sicaf_status": sicaf_status,
        "regime_tributario": regime,
        "historico_contratos_count": len(historico),
        "historico_contratos_valor": hist_total_valor,
        "historico_contratos_valor_formatted": format_brl(hist_total_valor) if hist_total_valor > 0 else "Não informado",
        "maturity_profile": maturity_info,
    }


def build_edital_card(edital: dict, empresa: dict, idx: int) -> dict:
    """Build a structured card for a single edital.

    Args:
        edital: Raw edital dict from data["editais"][n]
        empresa: Raw empresa dict from data["empresa"]
        idx: Display index (1-based)

    Returns:
        dict with all fields needed to render an edital card in any format.
    """
    risk = edital.get("risk_score", {}) or {}
    wp = edital.get("win_probability", {}) or {}
    roi = edital.get("roi_potential", {}) or {}
    distancia_info = edital.get("distancia", {}) or {}

    # Recommendation
    rec_raw = _safe_str(edital.get("recomendacao", ""))
    rec = _normalize_recommendation(rec_raw)
    vetoed = risk.get("vetoed", False)
    if vetoed:
        rec = "NAO RECOMENDADO"

    rec_color = _recommendation_color(rec)

    # Valor
    valor = edital.get("valor_estimado")
    valor_formatted = format_brl(valor) if valor is not None else "Não informado"

    # Data encerramento
    data_enc = edital.get("data_encerramento")
    data_enc_formatted = format_date_br(data_enc)

    # Dias restantes
    dias = edital.get("dias_restantes")
    dias_int = _safe_int(dias) if dias is not None else None

    # Risk dimensions
    risk_dimensions = {}
    for key, label in [("habilitacao", "hab"), ("financeiro", "fin"),
                       ("geografico", "geo"), ("prazo", "prazo"),
                       ("competitivo", "comp")]:
        val = risk.get(key)
        if val is not None:
            risk_dimensions[label] = _safe_int(val)

    # Win probability
    prob = _safe_float(wp.get("probability", 0)) if isinstance(wp, dict) else 0.0
    prob_str = format_percentage(prob) if prob > 0 else "Não informado"

    # Acervo
    acervo = _safe_str(edital.get("acervo_status", "NAO_VERIFICADO"))

    # Alertas criticos
    alertas_raw = edital.get("alertas_criticos", [])
    alertas = []
    for a in alertas_raw:
        if isinstance(a, dict):
            alertas.append(_safe_str(a.get("mensagem", a.get("descricao", ""))))
        elif isinstance(a, str):
            alertas.append(a)
    # Add veto reasons as alerts
    if vetoed:
        for reason in risk.get("veto_reasons", []):
            alertas.insert(0, f"VETO: {_safe_str(reason)}")

    # Fonte
    fonte = _safe_str(edital.get("fonte", ""))

    # Link
    link = _fix_pncp_link(edital.get("link"))

    # Municipio/UF
    municipio = _safe_str(edital.get("municipio", ""))
    uf = _safe_str(edital.get("uf", ""))
    municipio_uf = ""
    if municipio and uf:
        municipio_uf = f"{municipio}/{uf}"
    elif municipio:
        municipio_uf = municipio
    elif uf:
        municipio_uf = uf

    # Distancia
    dist_km = None
    if isinstance(distancia_info, dict):
        dist_km = distancia_info.get("distancia_km", distancia_info.get("km"))
        if dist_km is not None:
            dist_km = _safe_float(dist_km)

    # Analise resumo
    analise = edital.get("analise_resumo") or edital.get("analise_detalhada")
    analise_str = _safe_str(analise) if analise else None

    # Objeto truncated
    objeto_full = _safe_str(edital.get("objeto", ""))
    objeto = _trunc(objeto_full, 200)

    return {
        "numero": idx,
        "objeto": objeto,
        "objeto_full": objeto_full,
        "orgao": _safe_str(edital.get("orgao", "")),
        "municipio": municipio,
        "uf": uf,
        "municipio_uf": municipio_uf,
        "valor": _safe_float(valor) if valor is not None else None,
        "valor_formatted": valor_formatted,
        "modalidade": _safe_str(edital.get("modalidade", "")),
        "data_abertura": format_date_br(edital.get("data_abertura")),
        "data_encerramento": data_enc_formatted,
        "dias_restantes": dias_int,
        "recomendacao": rec,
        "recomendacao_raw": rec_raw,
        "recomendacao_color": rec_color,
        "vetoed": vetoed,
        "justificativa": _safe_str(edital.get("justificativa", "")),
        "risk_score_total": _safe_float(risk.get("total", 0)),
        "risk_dimensions": risk_dimensions,
        "risk_weights": risk.get("weights", {}),
        "win_probability": prob,
        "win_probability_formatted": prob_str,
        "win_probability_range": {
            "low": _safe_float(wp.get("probability_low", 0)) if isinstance(wp, dict) else 0.0,
            "high": _safe_float(wp.get("probability_high", 0)) if isinstance(wp, dict) else 0.0,
        },
        "n_unique_suppliers": _safe_int(
            wp.get("n_unique_suppliers", wp.get("unique_suppliers", 0))
            if isinstance(wp, dict) else 0
        ),
        "acervo_status": acervo,
        "alertas_criticos": alertas,
        "fonte": fonte,
        "link": link,
        "analise_resumo": analise_str,
        "distancia_km": dist_km,
        "roi_min": _safe_float(roi.get("roi_min", 0)),
        "roi_max": _safe_float(roi.get("roi_max", 0)),
        "roi_min_formatted": format_brl_short(roi.get("roi_min")) if roi.get("roi_min") else None,
        "roi_max_formatted": format_brl_short(roi.get("roi_max")) if roi.get("roi_max") else None,
        "roi_confidence": _safe_str(roi.get("confidence", "")),
        "strategic_reclassification": roi.get("strategic_reclassification"),
        "calculation_memory": roi.get("calculation_memory", {}),
    }


def build_market_intelligence(data: dict) -> dict:
    """Extract market intelligence section from report JSON.

    Returns:
        dict with keys: panorama, tendencias, vantagens,
        recomendacao_geral, tese_estrategica, has_content
    """
    intel = data.get("inteligencia_mercado", {}) or {}

    panorama = _safe_str(intel.get("panorama", ""))
    tendencias = _safe_str(intel.get("tendencias", ""))
    vantagens = _safe_str(intel.get("vantagens", ""))
    recomendacao_geral = _safe_str(intel.get("recomendacao_geral", ""))

    # Strategic thesis (can be at top level or inside intel)
    thesis_data = data.get("strategic_thesis") or intel.get("strategic_thesis") or {}
    tese = {}
    if thesis_data.get("thesis"):
        tese = {
            "thesis": thesis_data["thesis"],
            "rationale": _safe_str(thesis_data.get("rationale", "")),
        }

    has_content = bool(panorama or tendencias or vantagens or recomendacao_geral)

    return {
        "panorama": panorama,
        "tendencias": tendencias,
        "vantagens": vantagens,
        "recomendacao_geral": recomendacao_geral,
        "tese_estrategica": tese,
        "has_content": has_content,
    }


def build_next_steps(data: dict) -> list[dict]:
    """Extract and normalize next steps from report JSON.

    Handles both the legacy list format and the new dict-based
    horizon format (acao_imediata / medio_prazo / desenvolvimento_estrategico).

    Returns:
        list of dicts, each with: acao, prazo, prioridade (ALTA/MEDIA/BAIXA),
        edital_ref (optional), horizon (IMEDIATA/MEDIO_PRAZO/ESTRATEGICA)
    """
    proximos = data.get("proximos_passos")
    steps: list[dict] = []

    if isinstance(proximos, dict):
        # New horizon-based structure
        horizon_map = {
            "acao_imediata": ("IMEDIATA", "ALTA"),
            "medio_prazo": ("MEDIO_PRAZO", "MEDIA"),
            "desenvolvimento_estrategico": ("ESTRATEGICA", "BAIXA"),
            "checklist_habilitacao": ("IMEDIATA", "ALTA"),
        }
        for key, (horizon, default_prio) in horizon_map.items():
            items = proximos.get(key, [])
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict):
                    steps.append({
                        "acao": _safe_str(item.get("acao", "")),
                        "prazo": _safe_str(item.get("prazo", "")),
                        "prioridade": _safe_str(item.get("prioridade", default_prio)).upper() or default_prio,
                        "edital_ref": _safe_str(item.get("edital_ref", item.get("edital", ""))),
                        "horizon": horizon,
                        "documentos": item.get("documentos_necessarios", []),
                    })
                elif isinstance(item, str):
                    steps.append({
                        "acao": _safe_str(item),
                        "prazo": "",
                        "prioridade": default_prio,
                        "edital_ref": "",
                        "horizon": horizon,
                        "documentos": [],
                    })

    elif isinstance(proximos, list):
        # Legacy flat list
        for item in proximos:
            if isinstance(item, dict):
                prio = _safe_str(item.get("prioridade", "MEDIA")).upper()
                if "URGENTE" in prio or "ALTA" in prio:
                    prio = "ALTA"
                elif "BAIXA" in prio:
                    prio = "BAIXA"
                else:
                    prio = "MEDIA"
                steps.append({
                    "acao": _safe_str(item.get("acao", "")),
                    "prazo": _safe_str(item.get("prazo", "")),
                    "prioridade": prio,
                    "edital_ref": _safe_str(item.get("edital_ref", item.get("edital", ""))),
                    "horizon": "",
                    "documentos": [],
                })
            elif isinstance(item, str):
                steps.append({
                    "acao": _safe_str(item),
                    "prazo": "",
                    "prioridade": "MEDIA",
                    "edital_ref": "",
                    "horizon": "",
                    "documentos": [],
                })

    return steps


def build_methodology_section() -> dict:
    """Return static methodology content explaining the analysis approach.

    Returns:
        dict with keys: data_sources, scoring_methodology, dimensions,
        recommendation_thresholds, roi_formula, probability_calibration,
        disclaimer
    """
    return {
        "data_sources": [
            {
                "name": "Portal Nacional de Contratacoes Publicas (PNCP)",
                "description": "Editais e contratos publicados sob a Lei 14.133/2021",
                "priority": 1,
            },
            {
                "name": "Portal de Compras Publicas (PCP)",
                "description": "Licitacoes publicadas no portal PCP v2",
                "priority": 2,
            },
            {
                "name": "Portal da Transparencia",
                "description": "Sancoes (CEIS, CNEP, CEPIM, CEAF) e contratos historicos",
                "priority": 3,
            },
            {
                "name": "Receita Federal / OpenCNPJ",
                "description": "Dados cadastrais, QSA, capital social, CNAEs",
                "priority": 4,
            },
            {
                "name": "SICAF",
                "description": "Situacao cadastral e habilitacao parcial (quando disponivel)",
                "priority": 5,
            },
        ],
        "scoring_methodology": (
            "O indice de Compatibilidade combina cinco dimensoes com pesos estimados "
            "para refletir os fatores mais determinantes na decisao de participacao. "
            "Os pesos sao estimativas setoriais utilizadas como aproximacao -- o peso real "
            "de cada fator varia conforme o edital especifico."
        ),
        "dimensions": [
            {"name": "Habilitacao", "default_weight": 0.30,
             "description": "Capacidade tecnica, atestados, capital minimo, certidoes"},
            {"name": "Financeiro", "default_weight": 0.25,
             "description": "Valor do edital vs. capacidade da empresa, regime tributario"},
            {"name": "Geografico", "default_weight": 0.20,
             "description": "Distancia rodoviaria ate o local de execucao"},
            {"name": "Prazo", "default_weight": 0.15,
             "description": "Dias restantes para preparacao da proposta"},
            {"name": "Competitivo", "default_weight": 0.10,
             "description": "Historico de fornecedores do orgao, concentracao de mercado"},
        ],
        "recommendation_thresholds": {
            "PARTICIPAR": {"min_score": 70, "description": "Alta compatibilidade -- participacao recomendada"},
            "AVALIAR COM CAUTELA": {"min_score": 40, "max_score": 69,
                                     "description": "Compatibilidade moderada -- avaliar requisitos especificos"},
            "NAO RECOMENDADO": {"max_score": 39, "description": "Baixa compatibilidade ou impedimento identificado"},
        },
        "roi_formula": (
            "(Valor do edital x Competitividade Estimada x Margem liquida setorial) "
            "- Custo estimado de participacao"
        ),
        "probability_calibration": {
            "alta": {"sample_min": 20, "description": "Mais de 20 contratos historicos"},
            "media": {"sample_min": 5, "sample_max": 20, "description": "5 a 20 contratos historicos"},
            "baixa": {"sample_max": 5, "description": "Menos de 5 contratos historicos"},
        },
        "disclaimer": (
            "Este relatorio tem carater informativo e analitico. NAO constitui parecer "
            "juridico, contabil ou de engenharia. "
            "Limitacoes: (1) verificacao de habilitacao e PARCIAL -- regularidade fiscal "
            "(CND Federal, Estadual, Municipal, FGTS, CNDT), certidao de falencia e registro "
            "CREA/CAU NAO sao verificados automaticamente; (2) o percentual de capital "
            "minimo/patrimonio liquido utilizado e uma estimativa setorial -- o percentual "
            "real e definido em cada edital e deve ser conferido antes de submeter proposta; "
            "(3) Competitividade Estimada e heuristica baseada em dados historicos de "
            "contratacao do orgao -- percentual baixo e normal em licitacoes abertas, NAO e "
            "projecao estatistica calibrada; (4) a capacidade financeira estimada e uma "
            "aproximacao -- a capacidade real depende de patrimonio liquido, receita, linhas "
            "de credito e contratos em andamento; (5) CNAE nao e requisito legal de "
            "habilitacao -- a Lei 14.133/2021 exige qualificacao tecnica (atestados) e "
            "compatibilidade do objeto social. A decisao de participar e de exclusiva "
            "responsabilidade da empresa. Recomenda-se consulta a advogado e contador antes "
            "de submeter propostas."
        ),
    }


# ---------------------------------------------------------------------------
# Convenience: build all cards at once
# ---------------------------------------------------------------------------

def build_all_edital_cards(data: dict) -> list[dict]:
    """Build structured cards for all editais in the report.

    Returns list of edital card dicts, preserving original order and assigning
    1-based display indices.
    """
    empresa = data.get("empresa", {})
    editais = data.get("editais", [])
    cards = []
    for i, ed in enumerate(editais, 1):
        # Use existing _display_idx if set by the pipeline, else use position
        display_idx = ed.get("_display_idx", i)
        cards.append(build_edital_card(ed, empresa, display_idx))
    return cards


def build_full_report_data(data: dict) -> dict:
    """Build all template sections from raw report JSON.

    Convenience function that calls all builders and returns a single
    dict keyed by section name. Useful for multi-format renderers.

    Returns:
        dict with keys: cover, executive_summary, empresa_profile,
        edital_cards, market_intelligence, next_steps, methodology
    """
    return {
        "cover": build_cover_data(data),
        "executive_summary": build_executive_summary(data),
        "empresa_profile": build_empresa_profile(data),
        "edital_cards": build_all_edital_cards(data),
        "market_intelligence": build_market_intelligence(data),
        "next_steps": build_next_steps(data),
        "methodology": build_methodology_section(),
    }
