#!/usr/bin/env python3
"""
Analise automatizada via LLM dos top 20 editais do /intel-busca.

Le o JSON gerado pelo intel-extract-docs.py (com campo top20[].texto_documentos)
e produz analise estruturada por edital em top20[].analise usando GPT-4.1-nano.

Tambem gera resumo_executivo e proximos_passos automaticamente.

Usage:
    python scripts/intel-analyze.py --input docs/intel/intel-CNPJ-slug-YYYY-MM-DD.json
    python scripts/intel-analyze.py --input data.json --top 10
    python scripts/intel-analyze.py --input data.json --model gpt-4.1-mini --output analyzed.json
    python scripts/intel-analyze.py --input data.json --review

Requires:
    pip install openai
    OPENAI_API_KEY env var set
"""
from __future__ import annotations

import argparse
import concurrent.futures
import io
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ============================================================
# Windows console encoding fix
# ============================================================
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "buffer") and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "buffer") and not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except (ValueError, AttributeError):
        pass  # Already wrapped or buffer closed

# ============================================================
# CONSTANTS
# ============================================================

VERSION = "2.0.0"

MAX_TEXT_CHARS = 50_000       # Truncate document text beyond this
MAX_TOKENS_RESPONSE = 2_500  # Increased for 21 fields (was 2000 for 16)
LLM_TEMPERATURE = 0          # Deterministic output
MAX_WORKERS = 5              # Parallel LLM calls
RETRY_ATTEMPTS = 2           # Retry on transient failures
RETRY_DELAY_S = 2.0          # Seconds between retries

REVIEW_MAX_TEXT_CHARS = 10_000  # Max text chars for adversarial review context
REVIEW_MAX_TOKENS = 1_000       # Max tokens for review response

# Thread-safe print lock
import threading
_print_lock = threading.Lock()

def _tprint(*args: Any, **kwargs: Any) -> None:
    """Thread-safe print."""
    with _print_lock:
        print(*args, **kwargs)


# ============================================================
# ANALYSIS SCHEMA (matches intel-report.py expectations)
# ============================================================

ANALYSIS_FIELDS = [
    "resumo_objeto",
    "requisitos_tecnicos",
    "requisitos_habilitacao",
    "qualificacao_economica",
    "prazo_execucao",
    "garantias",
    "criterio_julgamento",
    "data_sessao",
    "prazo_proposta",
    "visita_tecnica",
    "exclusividade_me_epp",
    "regime_execucao",
    "consorcio",
    "observacoes_criticas",
    "nivel_dificuldade",
    "recomendacao_acao",
    "custo_logistico_nota",
    # v2.0 fields
    "valor_garantia_proposta",
    "percentual_subcontratacao",
    "indices_contabeis_exigidos",
    "atestados_especificos",
    "penalidades_principais",
]

CRITERIO_ENUM = [
    "Menor Preco",
    "Tecnica e Preco",
    "Maior Desconto",
    "Menor Preco Global",
    "Menor Preco por Item",
    "Melhor Tecnica",
]

VISITA_ENUM = [
    "Obrigatoria",
    "Facultativa",
    "Nao consta no edital disponivel",
]

REGIME_ENUM = [
    "Empreitada por preco global",
    "Empreitada por preco unitario",
    "Semi-Integrada",
    "Tarefa",
    "Contratacao Integrada",
    "Nao consta no edital disponivel",
]

CONSORCIO_ENUM = [
    "Permitido",
    "Vedado",
    "Nao mencionado no edital",
]

DIFICULDADE_ENUM = ["BAIXO", "MEDIO", "ALTO"]

RECOMENDACAO_ENUM = ["PARTICIPAR", "NAO PARTICIPAR"]

# ============================================================
# BID/NO-BID MULTI-CRITERIA SCORING (Ajuste 1)
# ============================================================

BID_SCORE_WEIGHTS = {
    "fit_estrategico": 0.20,
    "viabilidade_financeira": 0.15,
    "roi": 0.15,
    "p_vitoria": 0.15,
    "custo_logistico": 0.10,
    "janela_temporal": 0.10,
    "concorrencia": 0.15,
}

BID_SCORE_THRESHOLD = 0.45  # Calibravel via win/loss tracker


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """\
Voce e um analista especializado em licitacoes publicas brasileiras.
Sua tarefa e extrair informacoes estruturadas do texto de editais de licitacao
e produzir uma analise objetiva para tomada de decisao empresarial.

REGRAS ABSOLUTAS:
1. Responda SOMENTE com o JSON solicitado — sem prosa, sem markdown, sem explicacoes.
2. Para campos onde a informacao NAO existe no texto: use exatamente "Nao consta no edital disponivel".
3. NUNCA use: "verificar", "possivelmente", "a confirmar", "nao detalhado", "buscar edital", "consultar".
4. recomendacao_acao DEVE ser exatamente "PARTICIPAR" ou "NAO PARTICIPAR" — sem terceira opcao.
5. nivel_dificuldade DEVE ser um JSON com sub-scores (ver formato abaixo).
6. criterio_julgamento DEVE ser um dos: Menor Preco, Tecnica e Preco, Maior Desconto, Menor Preco Global, Menor Preco por Item, Melhor Tecnica, ou "Nao consta no edital disponivel".
7. visita_tecnica DEVE ser: Obrigatoria, Facultativa, ou "Nao consta no edital disponivel".
8. regime_execucao DEVE ser: Empreitada por preco global, Empreitada por preco unitario, Semi-Integrada, Tarefa, Contratacao Integrada, ou "Nao consta no edital disponivel".
9. consorcio DEVE ser: Permitido, Vedado, ou "Nao mencionado no edital".
10. resumo_objeto deve ter 2-3 frases concisas descrevendo o que esta sendo contratado.
11. requisitos_tecnicos e requisitos_habilitacao sao listas de strings (minimo 1 item cada).
12. Datas no formato DD/MM/YYYY HH:MM ou "Nao consta no edital disponivel".
13. Se o edital e claramente incompativel com a atividade da empresa, recomende "NAO PARTICIPAR" com justificativa em observacoes_criticas.
14. Seja CONCRETO — extraia numeros, datas, percentuais, valores exatos do texto.
15. Se um campo _bid_score foi fornecido no contexto, USE como referencia para recomendacao_acao. Pode discordar se houver razao concreta no edital, mas justifique em observacoes_criticas.
16. valor_garantia_proposta: percentual ou valor da garantia de proposta. Ex: "5% do valor estimado". Se nao consta: "Nao consta no edital disponivel".
17. percentual_subcontratacao: limite de subcontratacao. Ex: "Ate 30%", "Vedado". Se nao consta: "Nao consta no edital disponivel".
18. indices_contabeis_exigidos: lista de indices com valores minimos. Ex: ["ILC >= 1,0", "ILG >= 1,0", "SG >= 1,0"]. Se nao consta: ["Nao consta no edital disponivel"].
19. atestados_especificos: lista de atestados/CATs exigidos com especificidades. Ex: ["Atestado de edificacao >= 500m2", "CAT engenheiro civil em drenagem"]. Se nao consta: ["Nao consta no edital disponivel"].
20. penalidades_principais: resumo das penalidades. Ex: "Multa de 0,5% por dia de atraso, max 10%. Suspensao de 2 anos por inexecucao total." Se nao consta: "Nao consta no edital disponivel".

FORMATO DE SAIDA (JSON exato):
{
  "resumo_objeto": "string",
  "requisitos_tecnicos": ["string", ...],
  "requisitos_habilitacao": ["string", ...],
  "qualificacao_economica": "string",
  "prazo_execucao": "string",
  "garantias": "string",
  "criterio_julgamento": "string",
  "data_sessao": "string",
  "prazo_proposta": "string",
  "visita_tecnica": "string",
  "exclusividade_me_epp": "string",
  "regime_execucao": "string",
  "consorcio": "string",
  "observacoes_criticas": "string",
  "nivel_dificuldade": {"tecnico": 1-5, "prazo": 1-5, "regulatorio": 1-5, "logistico": 1-5, "financeiro": 1-5, "geral": "BAIXO|MEDIO|ALTO", "justificativa": "string"},
  "recomendacao_acao": "PARTICIPAR|NAO PARTICIPAR",
  "custo_logistico_nota": "string",
  "valor_garantia_proposta": "string",
  "percentual_subcontratacao": "string",
  "indices_contabeis_exigidos": ["string", ...],
  "atestados_especificos": ["string", ...],
  "penalidades_principais": "string"
}"""


# ============================================================
# ADVERSARIAL REVIEW PROMPT
# ============================================================

REVIEW_SYSTEM_PROMPT = """\
Voce e um AUDITOR independente de analises de editais de licitacao.
Sua tarefa e revisar uma analise produzida por outro analista e identificar ERROS FACTUAIS.

Voce recebera:
1. O texto (parcial) do edital
2. A analise produzida pelo analista

Verifique CADA ponto abaixo:
- data_sessao: a data extraida confere com o texto do edital?
- criterio_julgamento: o criterio esta correto conforme o texto?
- garantias: as garantias foram corretamente extraidas (tipo, percentual, valor)?
- recomendacao_acao: a recomendacao e coerente com os dados (prazo, valor, dificuldade, requisitos)?
- Algum campo diz "Nao consta no edital disponivel" mas a informacao ESTA presente no texto?

REGRAS:
1. Retorne SOMENTE um JSON com os campos que precisam correcao.
2. Se a analise esta 100% correta, retorne: {"corrections": {}}
3. Se encontrou erros, retorne: {"corrections": {"campo": "valor_correto", ...}}
4. Inclua um campo "review_notes" com uma string explicando brevemente o que foi corrigido (ou "Analise validada sem correcoes").
5. NAO invente informacao — so corrija com base no texto do edital.
6. Mantenha os mesmos formatos de enum (PARTICIPAR/NAO PARTICIPAR, BAIXO/MEDIO/ALTO, etc).
"""

# Model mapping for adversarial review (use different model to reduce confirmation bias)
REVIEW_MODEL_MAP = {
    "gpt-4.1-nano": "gpt-4.1-mini",
    "gpt-4.1-mini": "gpt-4.1-nano",
    "gpt-4.1": "gpt-4.1-mini",
    "gpt-4o-mini": "gpt-4o",
    "gpt-4o": "gpt-4o-mini",
}


# ============================================================
# HELPERS
# ============================================================

def _safe_float(val: Any) -> float:
    """Convert value to float safely."""
    if val is None:
        return 0.0
    try:
        if isinstance(val, str):
            return float(val.replace(".", "").replace(",", ".") or 0)
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _fmt_brl(val: float) -> str:
    """Format float as BRL currency string."""
    if not val or val <= 0:
        return "Nao informado"
    if val >= 1_000_000:
        return f"R$ {val / 1_000_000:,.1f}M"
    if val >= 1_000:
        return f"R$ {val / 1_000:,.1f}mil"
    return f"R$ {val:,.2f}"


# ============================================================
# BID/NO-BID SCORING (Ajuste 1)
# ============================================================

def _compute_bid_score(edital: dict[str, Any], empresa: dict[str, Any]) -> dict[str, Any]:
    """Compute multi-criteria bid/no-bid score BEFORE LLM analysis."""
    scores: dict[str, float] = {}

    # D1: Fit Estrategico (victory_profile score)
    scores["fit_estrategico"] = float(edital.get("_victory_fit") or 0.5)

    # D2: Viabilidade Financeira (capital_social vs valor_estimado)
    valor = _safe_float(edital.get("valor_estimado"))
    cs_raw = str(empresa.get("capital_social") or "0").strip()
    try:
        if "," in cs_raw:
            cs_raw = cs_raw.replace(".", "").replace(",", ".")
        capital = float(cs_raw)
    except (ValueError, TypeError):
        capital = 0.0

    if capital > 0 and valor > 0:
        ratio = valor / capital
        if ratio <= 1.0:
            scores["viabilidade_financeira"] = 1.0
        elif ratio <= 3.0:
            scores["viabilidade_financeira"] = 0.7
        elif ratio <= 5.0:
            scores["viabilidade_financeira"] = 0.4
        elif ratio <= 10.0:
            scores["viabilidade_financeira"] = 0.2
        else:
            scores["viabilidade_financeira"] = 0.05
    else:
        scores["viabilidade_financeira"] = 0.5

    # D3: ROI Estimado
    roi_data = edital.get("roi_proposta") or {}
    roi_ratio = _safe_float(roi_data.get("ratio_valor_custo"))
    if roi_ratio >= 5.0:
        scores["roi"] = 1.0
    elif roi_ratio >= 3.0:
        scores["roi"] = 0.7
    elif roi_ratio >= 1.5:
        scores["roi"] = 0.4
    elif roi_ratio > 0:
        scores["roi"] = 0.1
    else:
        scores["roi"] = 0.5  # Unknown

    # D4: Probabilidade de Vitoria
    bid_sim = edital.get("_bid_simulation") or {}
    p_win = _safe_float(bid_sim.get("p_vitoria_pct"))
    scores["p_vitoria"] = min(1.0, p_win / 60.0) if p_win > 0 else 0.5

    # D5: Custo Logistico (distancia)
    dist = (edital.get("distancia") or {}).get("km")
    if dist is None:
        scores["custo_logistico"] = 0.5
    elif dist <= 100:
        scores["custo_logistico"] = 1.0
    elif dist <= 300:
        scores["custo_logistico"] = 0.7
    elif dist <= 600:
        scores["custo_logistico"] = 0.4
    else:
        scores["custo_logistico"] = 0.2

    # D6: Janela Temporal
    status = edital.get("status_temporal", "")
    if status == "URGENTE":
        scores["janela_temporal"] = 0.3
    elif status == "IMINENTE":
        scores["janela_temporal"] = 0.6
    elif status == "PLANEJAVEL":
        scores["janela_temporal"] = 1.0
    elif status == "SEM_DATA":
        scores["janela_temporal"] = 0.4
    else:
        scores["janela_temporal"] = 0.5

    # D7: Nivel de Concorrencia (from competitive_intel)
    ci = edital.get("competitive_intel") or {}
    comp_level = ci.get("competition_level", "")
    if comp_level == "BAIXA":
        scores["concorrencia"] = 1.0
    elif comp_level == "MEDIA":
        scores["concorrencia"] = 0.7
    elif comp_level == "ALTA":
        scores["concorrencia"] = 0.4
    elif comp_level == "MUITO_ALTA":
        scores["concorrencia"] = 0.2
    else:
        scores["concorrencia"] = 0.5

    # Weighted composite
    composite = sum(scores[k] * BID_SCORE_WEIGHTS[k] for k in BID_SCORE_WEIGHTS)

    return {
        **scores,
        "_composite": round(composite, 4),
        "_threshold": BID_SCORE_THRESHOLD,
        "_recommendation": "PARTICIPAR" if composite >= BID_SCORE_THRESHOLD else "NAO PARTICIPAR",
    }


# ============================================================
# COMPLIANCE MATRIX (Ajuste 2)
# ============================================================

def _build_compliance_matrix(
    analise: dict[str, Any],
    empresa: dict[str, Any],
) -> list[dict[str, str]]:
    """Cross-reference edital requirements with known company capabilities."""
    reqs = analise.get("requisitos_habilitacao") or []
    if isinstance(reqs, str):
        reqs = [reqs]

    # Known capabilities
    sicaf_ok = not empresa.get("restricao_sicaf", False)
    sancionada = empresa.get("sancionada", False)
    cs_raw = str(empresa.get("capital_social") or "0").strip()
    try:
        if "," in cs_raw:
            cs_raw = cs_raw.replace(".", "").replace(",", ".")
        capital = float(cs_raw)
    except (ValueError, TypeError):
        capital = 0.0
    cnaes = empresa.get("cnaes") or empresa.get("cnaes_secundarios") or []
    porte = empresa.get("porte", "")
    simples = empresa.get("opcao_pelo_simples", False)

    matrix: list[dict[str, str]] = []
    for req in reqs:
        req_lower = (req or "").lower()
        item = {"requisito": req, "status": "VERIFICAR", "evidencia": ""}

        if any(k in req_lower for k in ("sicaf", "crc", "cadastro")):
            if sicaf_ok:
                item.update(status="ATENDE", evidencia="SICAF regular verificado")
            else:
                item.update(status="RISCO", evidencia="SICAF com restricao ativa")

        elif any(k in req_lower for k in ("sancao", "impedid", "ceis", "cnep", "debar")):
            if not sancionada:
                item.update(status="ATENDE", evidencia="Sem sancoes identificadas")
            else:
                item.update(status="NAO ATENDE", evidencia="Empresa sancionada")

        elif any(k in req_lower for k in ("capital social", "patrimonio", "patrimônio")):
            item.update(evidencia=f"Capital social: R$ {capital:,.2f}")

        elif any(k in req_lower for k in ("cnae", "atividade", "ramo")):
            n = len(cnaes) if isinstance(cnaes, list) else 0
            item.update(status="ATENDE" if n > 0 else "VERIFICAR", evidencia=f"{n} CNAEs ativos")

        elif any(k in req_lower for k in ("me ", "epp", "micro", "pequeno porte")):
            item.update(evidencia=f"Porte: {porte or 'nao informado'}")

        elif any(k in req_lower for k in ("simples", "optante")):
            item.update(
                status="ATENDE" if simples else "VERIFICAR",
                evidencia=f"Simples Nacional: {'Sim' if simples else 'Nao/Nao informado'}",
            )

        elif any(k in req_lower for k in ("atestado", "acervo", "cat ", "certidao de acervo")):
            item.update(status="VERIFICAR_MANUAL", evidencia="Requer verificacao de acervo tecnico")

        elif any(k in req_lower for k in ("responsavel tecnico", "crea", "cau", "engenheiro")):
            item.update(status="VERIFICAR_MANUAL", evidencia="Requer verificacao de corpo tecnico")

        matrix.append(item)

    return matrix


# ============================================================
# URGENCY COMPUTATION (Ajuste 9)
# ============================================================

def _compute_urgency(edital: dict[str, Any], analise: dict[str, Any]) -> dict[str, Any]:
    """Compute urgency level from session date extracted by LLM."""
    data_sessao = analise.get("data_sessao", "")
    if not data_sessao or "Nao consta" in data_sessao:
        return {"nivel": "INDEFINIDO", "dias_restantes": None, "cor": "gray"}

    # Try to parse date from various formats
    dt = None
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(data_sessao.strip(), fmt)
            break
        except (ValueError, IndexError):
            continue

    if dt is None:
        # Try just the date part
        import re as _re
        date_match = _re.search(r"(\d{2}/\d{2}/\d{4})", data_sessao)
        if date_match:
            try:
                dt = datetime.strptime(date_match.group(1), "%d/%m/%Y")
            except ValueError:
                pass

    if dt is None:
        return {"nivel": "INDEFINIDO", "dias_restantes": None, "cor": "gray"}

    dias = (dt - datetime.now()).days

    if dias < 0:
        return {"nivel": "EXPIRADO", "dias_restantes": dias, "cor": "red"}
    elif dias <= 3:
        return {"nivel": "CRITICO", "dias_restantes": dias, "cor": "red"}
    elif dias <= 7:
        return {"nivel": "URGENTE", "dias_restantes": dias, "cor": "amber"}
    elif dias <= 15:
        return {"nivel": "ATENCAO", "dias_restantes": dias, "cor": "amber"}
    elif dias <= 30:
        return {"nivel": "NORMAL", "dias_restantes": dias, "cor": "green"}
    else:
        return {"nivel": "CONFORTAVEL", "dias_restantes": dias, "cor": "green"}


def _build_enrichment_context(edital: dict[str, Any], empresa: dict[str, Any]) -> str:
    """Build context string from enriched data for the LLM prompt."""
    parts: list[str] = []

    # Company context
    razao = empresa.get("razao_social", "N/A")
    cnaes = empresa.get("cnaes_descricao") or empresa.get("cnaes") or []
    cidade_sede = empresa.get("cidade_sede") or empresa.get("municipio", "")
    uf_sede = empresa.get("uf_sede") or empresa.get("uf", "")
    parts.append(f"EMPRESA: {razao}")
    parts.append(f"SEDE: {cidade_sede}/{uf_sede}")
    if cnaes:
        if isinstance(cnaes, list):
            parts.append(f"CNAEs: {', '.join(str(c) for c in cnaes[:5])}")
        else:
            parts.append(f"CNAEs: {cnaes}")

    # Sanctions / SICAF
    sancionada = empresa.get("sancionada", False)
    restricao = empresa.get("restricao_sicaf")
    if sancionada:
        parts.append("*** EMPRESA SANCIONADA — IMPEDIDA DE LICITAR ***")
    if restricao:
        parts.append("*** SICAF COM RESTRICAO ATIVA — RISCO DE INABILITACAO ***")

    # Edital metadata
    valor = _safe_float(edital.get("valor_estimado"))
    parts.append(f"\nEDITAL: {edital.get('objeto', 'N/A')[:200]}")
    parts.append(f"MUNICIPIO: {edital.get('municipio', 'N/A')}/{edital.get('uf', 'N/A')}")
    parts.append(f"VALOR ESTIMADO: {_fmt_brl(valor)}")
    parts.append(f"MODALIDADE: {edital.get('modalidade_nome', 'N/A')}")
    parts.append(f"ORGAO: {edital.get('orgao_nome', 'N/A')}")

    # CNAE confidence (v4)
    cnae_conf = edital.get("cnae_confidence")
    if cnae_conf is not None:
        parts.append(f"CONFIANCA CNAE: {cnae_conf:.0%}")

    # Victory profile fit (v4)
    fit_label = edital.get("_victory_fit_label")
    if fit_label:
        fit_score = edital.get("_victory_fit", 0)
        parts.append(f"ADERENCIA PERFIL HISTORICO: {fit_label} ({fit_score:.0%})")

    # Temporal status
    status = edital.get("status_temporal")
    if status:
        parts.append(f"STATUS TEMPORAL: {status}")
    data_abertura = edital.get("data_abertura") or edital.get("data_sessao")
    if data_abertura:
        parts.append(f"DATA ABERTURA: {data_abertura}")

    # Delta status (v4)
    delta = edital.get("_delta_status")
    if delta and delta != "INALTERADO":
        parts.append(f"STATUS DELTA: {delta}")

    # Distance
    dist = edital.get("distancia") or {}
    km = dist.get("km")
    if km is not None:
        parts.append(f"DISTANCIA DA SEDE: {km:.0f} km")

    # IBGE
    ibge = edital.get("ibge") or {}
    pop = ibge.get("populacao")
    if pop:
        parts.append(f"POPULACAO MUNICIPIO: {pop:,}")

    # ROI
    roi = edital.get("roi_proposta") or {}
    classif_roi = roi.get("classificacao")
    if classif_roi:
        parts.append(f"CLASSIFICACAO ROI: {classif_roi}")

    # Cost
    custo = edital.get("custo_proposta") or {}
    custo_total = custo.get("total")
    if custo_total:
        parts.append(f"CUSTO ESTIMADO PROPOSTA: {_fmt_brl(custo_total)}")

    # Bid simulation (v4)
    bid = edital.get("_bid_simulation") or {}
    if bid.get("has_data") or bid.get("historico_contratos", 0) >= 3:
        lance = bid.get("lance_sugerido", 0)
        desc = bid.get("desconto_sugerido_pct", 0)
        pwin = bid.get("p_vitoria_pct", 0)
        parts.append(
            f"SIMULACAO LANCE: R$ {lance:,.2f} (desconto {desc:.1f}%, "
            f"P(vitoria) {pwin:.0f}%)"
        )

    # Bid/No-Bid Score (v2)
    bid_score = edital.get("_bid_score") or {}
    if bid_score:
        composite = bid_score.get("_composite", 0)
        parts.append(f"\nSCORE BID/NO-BID: {composite:.0%} (threshold: {BID_SCORE_THRESHOLD:.0%})")
        parts.append("Decomposicao:")
        for k, v in bid_score.items():
            if not k.startswith("_") and isinstance(v, (int, float)):
                parts.append(f"  - {k}: {v:.0%}")

    # Competitive Intelligence Detail (v2)
    ci = edital.get("competitive_intel") or {}
    top_comp = ci.get("top_suppliers") or []
    if top_comp:
        parts.append(f"\nCONCORRENTES HISTORICOS DO ORGAO:")
        for comp in top_comp[:3]:
            nome = (comp.get("nome") or "")[:40]
            ctr = comp.get("contratos", 0)
            share = comp.get("share_pct", 0)
            parts.append(f"  - {nome}: {ctr} contratos, {share:.0f}% share")
    pb = ci.get("price_benchmark") or {}
    if pb:
        dm = pb.get("desconto_mediano", 0)
        parts.append(
            f"BENCHMARK DE PRECO: desconto mediano {dm:.1%} "
            f"({pb.get('contratos_analisados', 0)} contratos)"
        )

    # Structured extraction hints (v4)
    struct = edital.get("_structured_extraction") or {}
    struct_fields = struct.get("fields") or {}
    hints: list[str] = []
    for fname, fdata in struct_fields.items():
        if isinstance(fdata, dict) and fdata.get("found"):
            val = fdata.get("value", "")
            if val and len(val) < 200:
                hints.append(f"  {fname}: {val}")
    if hints:
        parts.append("\nDADOS PRE-EXTRAIDOS (confirmar com texto do edital):")
        parts.extend(hints[:15])  # Max 15 hints to not overflow context

    return "\n".join(parts)


def _build_override_rules(edital: dict[str, Any], empresa: dict[str, Any]) -> str:
    """Build mandatory override rules based on enriched data."""
    rules: list[str] = []

    sancionada = empresa.get("sancionada", False)
    restricao = empresa.get("restricao_sicaf")
    status = edital.get("status_temporal", "")
    dist = edital.get("distancia") or {}
    km = dist.get("km")
    roi = edital.get("roi_proposta") or {}
    classif_roi = roi.get("classificacao", "")
    ibge = edital.get("ibge") or {}
    pop = ibge.get("populacao")
    valor = _safe_float(edital.get("valor_estimado"))

    if sancionada:
        rules.append(
            "REGRA OBRIGATORIA: A empresa esta SANCIONADA. "
            "recomendacao_acao DEVE ser 'NAO PARTICIPAR'. "
            "observacoes_criticas DEVE mencionar o impedimento por sancao."
        )

    if restricao:
        rules.append(
            "REGRA OBRIGATORIA: A empresa tem RESTRICAO no SICAF. "
            "observacoes_criticas DEVE alertar risco de inabilitacao por restricao SICAF."
        )

    if status == "EXPIRADO":
        rules.append(
            "REGRA OBRIGATORIA: O edital esta EXPIRADO/ENCERRADO. "
            "recomendacao_acao DEVE ser 'NAO PARTICIPAR'. "
            "observacoes_criticas DEVE informar que o prazo ja encerrou."
        )

    if status == "URGENTE":
        rules.append(
            "REGRA OBRIGATORIA: O prazo do edital esta URGENTE (poucos dias). "
            "observacoes_criticas DEVE mencionar a urgencia do prazo."
        )

    if km is not None and km > 500:
        rules.append(
            f"INFORMACAO: Distancia da sede ao local e {km:.0f} km (acima de 500km). "
            "custo_logistico_nota DEVE mencionar o custo logistico elevado."
        )

    if classif_roi == "DESFAVORAVEL":
        rules.append(
            "INFORMACAO: O ROI estimado e DESFAVORAVEL. "
            "observacoes_criticas DEVE recomendar cautela em relacao ao retorno."
        )

    if pop is not None and pop < 5000 and valor > 1_000_000:
        rules.append(
            f"INFORMACAO: Municipio com populacao pequena ({pop:,} hab) e valor alto ({_fmt_brl(valor)}). "
            "observacoes_criticas DEVE alertar fragilidade logistica."
        )

    # ── Compatibilidade CNAE / Aderência ao Perfil ──
    cnae_conf = edital.get("_cnae_confidence")
    if cnae_conf is not None:
        try:
            cnae_pct = float(cnae_conf)
        except (TypeError, ValueError):
            cnae_pct = -1
        if cnae_pct == 0:
            rules.append(
                "REGRA OBRIGATORIA: Compatibilidade CNAE = 0% — o objeto deste edital "
                "NAO corresponde a nenhum CNAE da empresa. "
                "recomendacao_acao DEVE ser 'NAO PARTICIPAR'. "
                "observacoes_criticas DEVE explicar a incompatibilidade setorial."
            )
        elif 0 < cnae_pct < 20:
            rules.append(
                f"ALERTA: Compatibilidade CNAE muito baixa ({cnae_pct}%). "
                "Avaliar cuidadosamente se o objeto e genuinamente compativel "
                "com a atividade da empresa antes de recomendar PARTICIPAR."
            )

    victory_fit = edital.get("_victory_fit")
    if victory_fit is not None:
        try:
            fit_val = float(victory_fit)
        except (TypeError, ValueError):
            fit_val = -1
        if fit_val < 0.1:
            rules.append(
                f"ALERTA: Aderencia ao perfil de vitoria muito baixa ({fit_val:.0%}). "
                "A empresa nao tem historico de contratos similares a este edital."
            )

    # ── Bid Score composite ──
    bid_score = edital.get("_bid_score") or {}
    composite = bid_score.get("_composite")
    if composite is not None:
        try:
            comp_val = float(composite)
        except (TypeError, ValueError):
            comp_val = -1
        if comp_val < 0.25:
            rules.append(
                f"REGRA OBRIGATORIA: Score bid/no-bid = {comp_val:.0%} (muito abaixo do "
                f"threshold {bid_score.get('_threshold', 0.45):.0%}). "
                "recomendacao_acao DEVE ser 'NAO PARTICIPAR' a menos que haja razao "
                "estrategica excepcional justificada em observacoes_criticas."
            )

    if not rules:
        return ""

    return "\n\nREGRAS MANDATORIAS PARA ESTA ANALISE:\n" + "\n".join(f"- {r}" for r in rules)


def _build_user_prompt(
    edital: dict[str, Any],
    empresa: dict[str, Any],
    idx: int,
    total: int,
    limited: bool = False,
) -> str:
    """Build the user prompt for a single edital analysis."""
    context = _build_enrichment_context(edital, empresa)
    overrides = _build_override_rules(edital, empresa)

    if limited:
        # No document text available
        prompt = (
            f"EDITAL {idx}/{total} — ANALISE LIMITADA (documentos nao disponiveis)\n\n"
            f"{context}"
            f"{overrides}\n\n"
            "INSTRUCAO: Produza a analise baseada SOMENTE nas informacoes acima "
            "(metadados do edital). Para campos que dependem do texto do edital, "
            'use "Nao consta no edital disponivel". '
            "Em observacoes_criticas, inclua: "
            '"Analise limitada — documentos nao disponiveis no PNCP. '
            'Recomenda-se buscar o edital completo no portal do orgao."\n\n'
            "Retorne SOMENTE o JSON."
        )
    else:
        texto = edital.get("texto_documentos", "")
        if len(texto) > MAX_TEXT_CHARS:
            texto = texto[:MAX_TEXT_CHARS] + "\n\n[... texto truncado ...]"

        prompt = (
            f"EDITAL {idx}/{total}\n\n"
            f"{context}"
            f"{overrides}\n\n"
            f"TEXTO DO EDITAL:\n{texto}\n\n"
            "Analise o texto acima e retorne SOMENTE o JSON estruturado."
        )

    return prompt


# ============================================================
# LLM CALL
# ============================================================

def _call_llm(
    client: Any,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> dict[str, Any]:
    """Call OpenAI API and parse the JSON response."""
    response = client.chat.completions.create(
        model=model,
        temperature=LLM_TEMPERATURE,
        max_tokens=MAX_TOKENS_RESPONSE,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content or "{}"

    # Parse JSON
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code block
        import re
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if match:
            result = json.loads(match.group(1))
        else:
            raise ValueError(f"LLM retornou resposta nao-JSON: {content[:200]}")

    return result


def _validate_analysis(analysis: dict[str, Any], edital: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate and normalize analysis fields to match expected schema."""
    # Ensure all required fields exist
    for field in ANALYSIS_FIELDS:
        if field not in analysis:
            if field in ("requisitos_tecnicos", "requisitos_habilitacao", "indices_contabeis_exigidos", "atestados_especificos"):
                analysis[field] = ["Nao consta no edital disponivel"]
            else:
                analysis[field] = "Nao consta no edital disponivel"

    # Enforce enums
    # Handle nivel_dificuldade as dict (v2) or string (legacy)
    dif = analysis.get("nivel_dificuldade")
    if isinstance(dif, dict):
        # Validate sub-scores
        for sub in ("tecnico", "prazo", "regulatorio", "logistico", "financeiro"):
            val = dif.get(sub)
            if not isinstance(val, (int, float)) or val < 1 or val > 5:
                dif[sub] = 3  # Default mid-range
        geral = str(dif.get("geral", "")).upper()
        if geral not in DIFICULDADE_ENUM:
            # Compute from sub-scores
            avg = sum(dif.get(s, 3) for s in ("tecnico", "prazo", "regulatorio", "logistico", "financeiro")) / 5
            dif["geral"] = "BAIXO" if avg <= 2 else ("ALTO" if avg >= 4 else "MEDIO")
        else:
            dif["geral"] = geral
        if "justificativa" not in dif:
            dif["justificativa"] = ""
        analysis["nivel_dificuldade"] = dif
    elif isinstance(dif, str):
        # Legacy string format — convert to dict
        geral = dif.upper() if dif.upper() in DIFICULDADE_ENUM else "MEDIO"
        analysis["nivel_dificuldade"] = {
            "tecnico": 3, "prazo": 3, "regulatorio": 3, "logistico": 3, "financeiro": 3,
            "geral": geral, "justificativa": "",
        }
    else:
        analysis["nivel_dificuldade"] = {
            "tecnico": 3, "prazo": 3, "regulatorio": 3, "logistico": 3, "financeiro": 3,
            "geral": "MEDIO", "justificativa": "",
        }

    rec = (analysis.get("recomendacao_acao") or "").upper()
    if "NAO" in rec or "NÃO" in rec:
        analysis["recomendacao_acao"] = "NAO PARTICIPAR"
    elif "PARTICIPAR" in rec:
        analysis["recomendacao_acao"] = "PARTICIPAR"
    else:
        # Default to NAO PARTICIPAR if unclear (zero noise philosophy)
        analysis["recomendacao_acao"] = "NAO PARTICIPAR"

    # ── Programmatic override: force NAO PARTICIPAR on hard signals ──
    # These override LLM recommendation regardless of what it said
    _force_nao = False
    _force_reason = ""

    # 1. Compatibilidade CNAE = 0% → always NAO PARTICIPAR
    cnae_conf = edital.get("_cnae_confidence") if edital else None
    if cnae_conf is not None:
        try:
            if float(cnae_conf) == 0:
                _force_nao = True
                _force_reason = "Compatibilidade CNAE 0% — objeto incompatível com atividade da empresa"
        except (TypeError, ValueError):
            pass

    # 2. Bid score < 0.20 (catastrophically low) → always NAO PARTICIPAR
    bid_score = (edital or {}).get("_bid_score") or {}
    composite = bid_score.get("_composite")
    if composite is not None:
        try:
            if float(composite) < 0.20:
                _force_nao = True
                _force_reason = f"Score bid/no-bid {float(composite):.0%} — abaixo do mínimo viável"
        except (TypeError, ValueError):
            pass

    # 3. Compatibilidade CNAE < 20% AND aderência < 0.15 → always NAO PARTICIPAR
    victory_fit = (edital or {}).get("_victory_fit")
    if cnae_conf is not None and victory_fit is not None:
        try:
            cnae_val = float(cnae_conf)
            fit_val = float(victory_fit)
            if cnae_val < 20 and fit_val < 0.15:
                _force_nao = True
                _force_reason = (
                    f"Compatibilidade {cnae_val:.0f}% + Aderência {fit_val:.0%} — "
                    "duplo sinal de incompatibilidade"
                )
        except (TypeError, ValueError):
            pass

    if _force_nao and analysis["recomendacao_acao"] == "PARTICIPAR":
        analysis["recomendacao_acao"] = "NAO PARTICIPAR"
        obs = analysis.get("observacoes_criticas", "")
        override_note = f"[OVERRIDE PROGRAMÁTICO] {_force_reason}."
        analysis["observacoes_criticas"] = (
            f"{override_note} {obs}" if obs else override_note
        )

    # Ensure lists are actually lists
    for list_field in ("requisitos_tecnicos", "requisitos_habilitacao", "indices_contabeis_exigidos", "atestados_especificos"):
        val = analysis.get(list_field)
        if isinstance(val, str):
            analysis[list_field] = [val] if val else ["Nao consta no edital disponivel"]
        elif not isinstance(val, list):
            analysis[list_field] = ["Nao consta no edital disponivel"]

    return analysis


# ============================================================
# ADVERSARIAL REVIEW
# ============================================================

def _adversarial_review(
    client: Any,
    edital: dict[str, Any],
    analise: dict[str, Any],
    model: str,
) -> dict[str, Any]:
    """Run an adversarial review pass on a completed analysis.

    Sends the analysis + first 10000 chars of document text to an AUDITOR
    persona that checks for factual errors and missing extractions.

    Args:
        client: OpenAI client instance
        edital: The edital dict (with texto_documentos)
        analise: The completed analysis dict to review
        model: OpenAI model to use

    Returns:
        dict of corrections (only fields that need fixing), empty if all correct.
    """
    texto = (edital.get("texto_documentos") or "")[:REVIEW_MAX_TEXT_CHARS]
    if not texto.strip():
        return {}

    # Build a clean copy of the analysis (exclude internal metadata fields)
    analise_clean = {k: v for k, v in analise.items() if not k.startswith("_")}

    user_prompt = (
        "TEXTO DO EDITAL (primeiros 10000 caracteres):\n"
        f"{texto}\n\n"
        "ANALISE PRODUZIDA PELO ANALISTA:\n"
        f"{json.dumps(analise_clean, ensure_ascii=False, indent=2)}\n\n"
        "Revise a analise acima comparando com o texto do edital. "
        "Retorne SOMENTE o JSON com corrections e review_notes."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            max_tokens=REVIEW_MAX_TOKENS,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = response.choices[0].message.content or "{}"
        result = json.loads(content)

        corrections = result.get("corrections", {})
        if not isinstance(corrections, dict):
            corrections = {}

        return corrections

    except Exception as exc:
        _tprint(f"    REVIEW WARN: Falha na revisao adversarial: {exc}")
        return {}


# ============================================================
# PER-EDITAL ANALYSIS
# ============================================================

def analyze_edital(
    client: Any,
    model: str,
    edital: dict[str, Any],
    empresa: dict[str, Any],
    idx: int,
    total: int,
) -> dict[str, Any]:
    """Analyze a single edital using the LLM. Returns the analysis dict."""
    objeto = (edital.get("objeto") or "")[:80]
    texto = edital.get("texto_documentos") or ""
    quality = edital.get("extraction_quality", "")

    limited = quality == "VAZIO" or len(texto.strip()) < 100

    if limited:
        _tprint(f"  [{idx}/{total}] {objeto} — analise limitada (sem texto)")
    else:
        _tprint(f"  [{idx}/{total}] {objeto} — {len(texto):,} chars")

    user_prompt = _build_user_prompt(edital, empresa, idx, total, limited=limited)

    last_error: Exception | None = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            raw = _call_llm(client, model, SYSTEM_PROMPT, user_prompt)
            analysis = _validate_analysis(raw, edital=edital)

            # Add metadata
            analysis["_source"] = "llm" if not limited else "llm_limited"
            analysis["_model"] = model
            analysis["_texto_chars"] = len(texto)

            # Compute urgency (v2)
            analysis["_urgency"] = _compute_urgency(edital, analysis)

            dif = analysis.get("nivel_dificuldade", {})
            dif_label = dif.get("geral", dif) if isinstance(dif, dict) else dif
            _tprint(f"    OK — {analysis['recomendacao_acao']} | {dif_label}")
            return analysis

        except Exception as exc:
            last_error = exc
            _tprint(f"    Tentativa {attempt}/{RETRY_ATTEMPTS} falhou: {exc}")
            if attempt < RETRY_ATTEMPTS:
                time.sleep(RETRY_DELAY_S * attempt)

    # All retries failed — produce a minimal fallback analysis
    _tprint(f"    FALHA — usando analise fallback (erro: {last_error})")
    return _fallback_analysis(edital, empresa, str(last_error))


def _fallback_analysis(
    edital: dict[str, Any],
    empresa: dict[str, Any],
    error_msg: str,
) -> dict[str, Any]:
    """Produce a minimal analysis when LLM fails."""
    objeto = edital.get("objeto", "N/A")
    municipio = edital.get("municipio", "N/A")
    uf = edital.get("uf", "N/A")
    valor = _safe_float(edital.get("valor_estimado"))

    sancionada = empresa.get("sancionada", False)
    status = edital.get("status_temporal", "")

    if sancionada:
        rec = "NAO PARTICIPAR"
        obs = f"Empresa sancionada — impedida de licitar. Erro na analise LLM: {error_msg}"
    elif status == "EXPIRADO":
        rec = "NAO PARTICIPAR"
        obs = f"Edital encerrado. Erro na analise LLM: {error_msg}"
    else:
        rec = "NAO PARTICIPAR"
        obs = (
            f"Analise automatica indisponivel (erro LLM: {error_msg}). "
            "Recomenda-se analise manual do edital."
        )

    return {
        "resumo_objeto": f"{objeto[:300]}",
        "requisitos_tecnicos": ["Analise automatica indisponivel — verificar edital manualmente"],
        "requisitos_habilitacao": ["Analise automatica indisponivel — verificar edital manualmente"],
        "qualificacao_economica": "Analise automatica indisponivel",
        "prazo_execucao": "Nao consta no edital disponivel",
        "garantias": "Nao consta no edital disponivel",
        "criterio_julgamento": "Nao consta no edital disponivel",
        "data_sessao": "Nao consta no edital disponivel",
        "prazo_proposta": "Nao consta no edital disponivel",
        "visita_tecnica": "Nao consta no edital disponivel",
        "exclusividade_me_epp": "Nao consta no edital disponivel",
        "regime_execucao": "Nao consta no edital disponivel",
        "consorcio": "Nao mencionado no edital",
        "observacoes_criticas": obs,
        "nivel_dificuldade": {"tecnico": 3, "prazo": 3, "regulatorio": 3, "logistico": 3, "financeiro": 3, "geral": "MEDIO", "justificativa": "Analise automatica indisponivel"},
        "recomendacao_acao": rec,
        "custo_logistico_nota": f"{municipio}/{uf} — distancia nao calculada",
        "_source": "fallback",
        "_model": "none",
        "_texto_chars": 0,
        "_error": error_msg,
    }


# ============================================================
# EXECUTIVE SUMMARY GENERATION
# ============================================================

def generate_executive_summary(
    client: Any,
    model: str,
    data: dict[str, Any],
) -> tuple[str, list[str]]:
    """Generate resumo_executivo and proximos_passos from analyzed top20."""
    top20 = data.get("top20", [])
    empresa = data.get("empresa", {})
    busca = data.get("busca", {})
    editais = data.get("editais", [])

    razao = empresa.get("razao_social", "Empresa")
    total_editais = len(editais)
    compat = sum(1 for e in editais if e.get("cnae_compatible"))
    ufs = busca.get("ufs", [])
    dias = busca.get("dias", 30)

    # Build summary of analyzed editais
    summary_parts: list[str] = []
    participar = []
    nao_participar = []

    for i, ed in enumerate(top20, 1):
        analise = ed.get("analise", {})
        rec = analise.get("recomendacao_acao", "")
        obj = (ed.get("objeto") or "")[:100]
        mun = ed.get("municipio", "")
        uf = ed.get("uf", "")
        valor = _safe_float(ed.get("valor_estimado"))
        dif = analise.get("nivel_dificuldade", "")

        line = f"#{i}: {obj} | {mun}/{uf} | {_fmt_brl(valor)} | {dif} | {rec}"
        summary_parts.append(line)

        if "PARTICIPAR" in rec and "NAO" not in rec:
            participar.append(f"#{i} {obj[:60]} ({mun}/{uf}, {_fmt_brl(valor)})")
        else:
            nao_participar.append(f"#{i} {obj[:60]}")

    # Portfolio metrics (v2 — deterministic, pre-LLM)
    total_valor_participar = sum(
        _safe_float(ed.get("valor_estimado"))
        for ed in top20
        if "PARTICIPAR" in (ed.get("analise", {}).get("recomendacao_acao", ""))
        and "NAO" not in (ed.get("analise", {}).get("recomendacao_acao", ""))
    )
    total_custo_propostas = sum(
        _safe_float((ed.get("custo_proposta") or {}).get("total"))
        for ed in top20
        if "PARTICIPAR" in (ed.get("analise", {}).get("recomendacao_acao", ""))
        and "NAO" not in (ed.get("analise", {}).get("recomendacao_acao", ""))
    )
    p_vitorias = [
        _safe_float((ed.get("_bid_simulation") or {}).get("p_vitoria_pct"))
        for ed in top20
        if "PARTICIPAR" in (ed.get("analise", {}).get("recomendacao_acao", ""))
        and "NAO" not in (ed.get("analise", {}).get("recomendacao_acao", ""))
    ]
    avg_p_vitoria = sum(p_vitorias) / max(1, len(p_vitorias)) if p_vitorias else 0
    valor_esperado = sum(
        _safe_float(ed.get("valor_estimado")) * _safe_float((ed.get("_bid_simulation") or {}).get("p_vitoria_pct")) / 100
        for ed in top20
        if "PARTICIPAR" in (ed.get("analise", {}).get("recomendacao_acao", ""))
        and "NAO" not in (ed.get("analise", {}).get("recomendacao_acao", ""))
    )
    roi_portfolio = total_valor_participar / max(1, total_custo_propostas)

    portfolio_metrics = (
        f"\n\nMETRICAS DE PORTFOLIO:"
        f"\n- Oportunidades recomendadas: {len(participar)} de {len(top20)}"
        f"\n- Valor total do pipeline: {_fmt_brl(total_valor_participar)}"
        f"\n- Custo estimado de propostas: {_fmt_brl(total_custo_propostas)}"
        f"\n- ROI potencial do portfolio: {roi_portfolio:.0f}x"
        f"\n- P(vitoria) media: {avg_p_vitoria:.0f}%"
        f"\n- Valor esperado (EV): {_fmt_brl(valor_esperado)}"
    )

    summary_prompt = (
        f"Empresa: {razao}\n"
        f"Busca: {total_editais} editais encontrados, {compat} compativeis por CNAE, "
        f"UFs: {', '.join(ufs) if ufs else 'N/A'}, ultimos {dias} dias\n"
        f"Top {len(top20)} analisados:\n" +
        "\n".join(summary_parts) +
        f"\n\nRecomendados PARTICIPAR ({len(participar)}):\n" +
        "\n".join(participar) +
        f"\n\nRecomendados NAO PARTICIPAR ({len(nao_participar)}):\n" +
        "\n".join(nao_participar[:10]) +
        ("\n..." if len(nao_participar) > 10 else "") +
        portfolio_metrics
    )

    system = (
        "Voce e um consultor de licitacoes. Com base na analise dos editais abaixo, "
        "produza um JSON com dois campos:\n"
        '1. "resumo_executivo": string com 3-5 paragrafos resumindo os achados '
        "(total de editais, quantos compativeis, quantos recomendados, destaques, alertas)\n"
        '2. "proximos_passos": lista de strings com 5-8 acoes concretas priorizadas '
        "(URGENTE > PRIORITARIO > BUSCAR > AVALIAR > MONITORAR)\n\n"
        "REGRAS:\n"
        "- Seja concreto: cite numeros de editais (#N), valores, datas, municipios\n"
        "- Inclua as METRICAS DE PORTFOLIO fornecidas (valor total, ROI, P(vitoria), valor esperado) no resumo\n"
        "- proximos_passos devem comecar com prefixo: URGENTE:, PRIORITARIO:, BUSCAR:, AVALIAR:, MONITORAR:\n"
        "- Retorne SOMENTE o JSON, sem markdown\n"
    )

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=LLM_TEMPERATURE,
            max_tokens=2000,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": summary_prompt},
            ],
        )
        content = response.choices[0].message.content or "{}"
        result = json.loads(content)
        resumo = result.get("resumo_executivo", "")
        passos = result.get("proximos_passos", [])
        if isinstance(passos, str):
            passos = [passos]
        return resumo, passos
    except Exception as exc:
        print(f"  WARN: Falha ao gerar resumo executivo: {exc}")
        # Fallback summary
        resumo = (
            f"A busca no PNCP identificou {total_editais} editais nos estados "
            f"{', '.join(ufs) if ufs else 'configurados'} nos ultimos {dias} dias. "
            f"Destes, {compat} sao compativeis com os CNAEs da {razao}. "
            f"Dos {len(top20)} editais analisados em profundidade, "
            f"{len(participar)} foram recomendados para participacao."
        )
        passos = [
            f"PRIORITARIO: Revisar os {len(participar)} editais recomendados para participacao",
            "AVALIAR: Verificar prazos de sessao e preparar documentacao",
            f"MONITORAR: Acompanhar novos editais semanalmente ({compat} compativeis na base)",
        ]
        return resumo, passos


# ============================================================
# PREPARE MODE (no API calls — Claude analyzes inline)
# ============================================================

def prepare_mode(input_path: Path, output_path: str | None, top_n: int) -> None:
    """Prepare analysis context for each edital without making LLM calls.

    Adds _analysis_context, _analysis_rules, and _analysis_limited to each
    top20 entry so Claude Code can read them and produce the analysis inline.
    """
    if not input_path.exists():
        print(f"ERROR: Arquivo nao encontrado: {input_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON invalido em {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, dict):
        print("ERROR: JSON raiz deve ser um objeto (dict)", file=sys.stderr)
        sys.exit(1)

    empresa = data.get("empresa", {})
    top20 = data.get("top20", [])

    if not top20:
        print("ERROR: Campo 'top20' vazio ou ausente no JSON.", file=sys.stderr)
        sys.exit(1)

    to_prepare = top20[:top_n]
    razao = empresa.get("razao_social", "N/A")

    print(f"{'=' * 60}")
    print(f"  INTEL-ANALYZE v{VERSION} — PREPARE MODE")
    print(f"  Input:   {input_path}")
    print(f"  Empresa: {razao}")
    print(f"  Top20:   {len(to_prepare)} editais")
    print(f"{'=' * 60}")

    for i, ed in enumerate(to_prepare, 1):
        texto = ed.get("texto_documentos", "")
        quality = ed.get("extraction_quality", "")
        limited = quality == "VAZIO" or len(texto.strip()) < 100

        context = _build_enrichment_context(ed, empresa)
        overrides = _build_override_rules(ed, empresa)

        ed["_analysis_context"] = context
        ed["_analysis_rules"] = overrides
        ed["_analysis_limited"] = limited

        objeto = (ed.get("objeto") or "")[:60]
        chars = len(texto)
        print(f"  [{i}/{len(to_prepare)}] {objeto} — {'limitada' if limited else f'{chars:,} chars'}")

    # Save
    out_path = output_path or str(input_path)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n  Contexto preparado para {len(to_prepare)} editais.")
    print(f"  Salvo em: {out_path}")
    print(f"  Proximo passo: Claude analisa cada edital e preenche top20[].analise")


# ============================================================
# SAVE-ANALYSIS MODE (validate Claude's output)
# ============================================================

def save_analysis_mode(input_path: Path, output_path: str | None) -> None:
    """Validate and finalize analyses pre-filled by Claude inline.

    Runs _validate_analysis() on each top20[].analise, cleans up
    preparation fields, and updates metadata.
    """
    if not input_path.exists():
        print(f"ERROR: Arquivo nao encontrado: {input_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON invalido em {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, dict):
        print("ERROR: JSON raiz deve ser um objeto (dict)", file=sys.stderr)
        sys.exit(1)

    top20 = data.get("top20", [])

    print(f"{'=' * 60}")
    print(f"  INTEL-ANALYZE v{VERSION} — SAVE-ANALYSIS MODE")
    print(f"  Input: {input_path}")
    print(f"{'=' * 60}")

    analyzed = 0
    for ed in top20:
        analise = ed.get("analise")
        if analise:
            ed["analise"] = _validate_analysis(analise, edital=ed)
            # Add metadata if not present
            if "_source" not in ed["analise"]:
                ed["analise"]["_source"] = "claude"
            if "_model" not in ed["analise"]:
                ed["analise"]["_model"] = "claude-inline"
            ed["analise"]["_texto_chars"] = len(ed.get("texto_documentos", ""))
            analyzed += 1

        # Clean up preparation fields
        ed.pop("_analysis_context", None)
        ed.pop("_analysis_rules", None)
        ed.pop("_analysis_limited", None)

    # Update metadata
    if "_metadata" not in data:
        data["_metadata"] = {}
    data["_metadata"]["analysis"] = {
        "version": VERSION,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "model": "claude-inline",
        "editais_analyzed": analyzed,
        "editais_total": len(top20),
        "editais_with_text": sum(1 for e in top20 if (e.get("texto_documentos") or "").strip()),
        "editais_limited": sum(
            1 for e in top20
            if e.get("analise", {}).get("_source") in ("claude_limited", "llm_limited")
        ),
        "editais_fallback": sum(
            1 for e in top20
            if e.get("analise", {}).get("_source") == "fallback"
        ),
        "participar": sum(
            1 for e in top20
            if "PARTICIPAR" in (e.get("analise", {}).get("recomendacao_acao", ""))
            and "NAO" not in (e.get("analise", {}).get("recomendacao_acao", ""))
        ),
        "nao_participar": sum(
            1 for e in top20
            if "NAO" in (e.get("analise", {}).get("recomendacao_acao", ""))
        ),
        "review_enabled": False,
        "review_corrections_total": 0,
        "review_corrections_per_edital": {},
    }

    # Save
    out_path = output_path or str(input_path)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    participar = data["_metadata"]["analysis"]["participar"]
    nao = data["_metadata"]["analysis"]["nao_participar"]

    print(f"\n  Editais validados:  {analyzed}/{len(top20)}")
    print(f"  PARTICIPAR:         {participar}")
    print(f"  NAO PARTICIPAR:     {nao}")
    print(f"  Salvo em:           {out_path}")
    print(f"{'=' * 60}")


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """Entry point for intel-analyze CLI."""
    from lib.constants import INTEL_VERSION
    from lib.cli_validation import validate_input_json, validate_top, validate_model

    parser = argparse.ArgumentParser(
        description="Intel Analyze — Analise LLM automatizada dos top editais para /intel-busca.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        metavar="JSON",
        help="JSON de entrada (output do intel-extract-docs.py com top20[]). Deve existir e ser JSON valido.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        metavar="JSON",
        help="JSON de saida (default: sobrescreve input)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        metavar="N",
        help="Numero maximo de editais do top20 a analisar, 1-50 (default: 20)",
    )
    parser.add_argument(
        "--prepare",
        action="store_true",
        help="Preparar contexto de analise para cada edital (sem chamadas API). "
             "Adiciona _analysis_context e _analysis_rules ao top20.",
    )
    parser.add_argument(
        "--save-analysis",
        action="store_true",
        dest="save_analysis",
        help="Validar e salvar analises pre-preenchidas por Claude inline. "
             "Espera top20[].analise ja populado. Roda _validate_analysis() em cada.",
    )
    parser.add_argument(
        "--model",
        default="gpt-4.1-nano",
        help="Modelo OpenAI a usar no modo API. Modelos validos: gpt-4.1-nano, gpt-4.1-mini, gpt-4.1, gpt-4o-mini, gpt-4o (default: gpt-4.1-nano)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=MAX_WORKERS,
        help=f"Numero de workers paralelos para chamadas LLM (default: {MAX_WORKERS})",
    )
    parser.add_argument(
        "--skip-summary",
        action="store_true",
        help="Pular geracao de resumo_executivo e proximos_passos (modo API)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-analisar editais que ja possuem campo 'analise' (sobrescreve analises existentes)",
    )
    parser.add_argument(
        "--review",
        action="store_true",
        help="Habilitar revisao adversarial pos-analise (modo API) — verifica consistencia da analise",
    )
    parser.add_argument(
        "--review-model",
        default=None,
        metavar="MODEL",
        help="Modelo especifico para revisao adversarial (default: modelo diferente do principal)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduzir output (somente erros e resumo final)",
    )
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {INTEL_VERSION}")
    args = parser.parse_args()

    # ── Validate arguments ──
    validate_input_json(args.input)
    validate_top(args.top, max_val=50)
    if not args.prepare and not args.save_analysis:
        validate_model(args.model)

    t0 = time.time()

    # ── Route to new modes ──
    if args.prepare:
        prepare_mode(Path(args.input), args.output, args.top)
        return

    if args.save_analysis:
        save_analysis_mode(Path(args.input), args.output)
        return

    # ── API mode (legacy) — requires OPENAI_API_KEY ──
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("ERROR: OPENAI_API_KEY env var not set.", file=sys.stderr)
        print("  Dica: Use --prepare para modo sem API (Claude analisa inline).", file=sys.stderr)
        sys.exit(1)

    # ── Load input ──
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Arquivo nao encontrado: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"{'=' * 60}")
    print(f"  INTEL-ANALYZE v{VERSION}")
    print(f"  Input:   {input_path}")
    print(f"  Model:   {args.model}")
    print(f"  Workers: {args.workers}")
    print(f"  Review:  {'ON' if args.review else 'OFF'}")
    print(f"{'=' * 60}")

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON invalido em {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, dict):
        print("ERROR: JSON raiz deve ser um objeto (dict)", file=sys.stderr)
        sys.exit(1)

    empresa = data.get("empresa", {})
    if not isinstance(empresa, dict):
        print("ERROR: campo 'empresa' deve ser um objeto (dict)", file=sys.stderr)
        sys.exit(1)

    top20 = data.get("top20", [])
    if not isinstance(top20, list):
        print("ERROR: campo 'top20' deve ser uma lista", file=sys.stderr)
        sys.exit(1)

    if not top20:
        print("\nERROR: Campo 'top20' vazio ou ausente no JSON.", file=sys.stderr)
        print("Execute intel-extract-docs.py primeiro para selecionar o top20.", file=sys.stderr)
        sys.exit(1)

    razao = empresa.get("razao_social", "N/A")
    print(f"  Empresa: {razao}")
    print(f"  Top20:   {len(top20)} editais")

    # ── Determine which editais to analyze ──
    to_analyze = top20[:args.top]
    if not args.force:
        to_analyze = [ed for ed in to_analyze if not ed.get("analise")]
        skipped = min(len(top20), args.top) - len(to_analyze)
        if skipped > 0:
            print(f"  Pulando: {skipped} editais ja analisados (use --force para re-analisar)")

    if not to_analyze:
        print("\nTodos os editais ja possuem analise. Use --force para re-analisar.")
        # Still generate summary if needed
        if not args.skip_summary and not data.get("resumo_executivo"):
            print("\n[2/2] Gerando resumo executivo...")
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                resumo, passos = generate_executive_summary(client, args.model, data)
                data["resumo_executivo"] = resumo
                data["proximos_passos"] = passos
                print(f"  Resumo: {len(resumo)} chars | {len(passos)} passos")
            except Exception as exc:
                print(f"  WARN: Falha no resumo: {exc}")

            out_path = args.output or str(input_path)
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            print(f"  Salvo em: {out_path}")
        return

    print(f"\n[1/2] Analisando {len(to_analyze)} editais via {args.model}...")

    # ── Initialize OpenAI client ──
    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai not installed. Run: pip install openai", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # ── Build index for parallel processing ──
    # Map edital _id to its index in top20 for in-place update
    edital_indices: dict[str, int] = {}
    for i, ed in enumerate(top20):
        eid = ed.get("_id") or str(i)
        edital_indices[eid] = i

    # ── Parallel analysis ──
    results: dict[str, dict[str, Any]] = {}
    total = len(to_analyze)

    def _analyze_one(item: tuple[int, dict[str, Any]]) -> tuple[str, dict[str, Any]]:
        idx, ed = item
        eid = ed.get("_id") or str(edital_indices.get(ed.get("_id", ""), idx))
        analysis = analyze_edital(client, args.model, ed, empresa, idx, total)
        return eid, analysis

    indexed_items = list(enumerate(to_analyze, 1))

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(_analyze_one, item): item
            for item in indexed_items
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                eid, analysis = future.result()
                results[eid] = analysis
            except Exception as exc:
                idx, ed = futures[future]
                eid = ed.get("_id") or str(idx)
                _tprint(f"    ERRO fatal no edital {eid}: {exc}")
                results[eid] = _fallback_analysis(ed, empresa, str(exc))

    # ── Apply results to top20 ──
    applied = 0
    for ed in top20:
        eid = ed.get("_id")
        if eid and eid in results:
            ed["analise"] = results[eid]
            applied += 1
            continue
        # Fallback: match by index for editais without _id
        for i, to_ed in enumerate(to_analyze):
            if to_ed is ed:
                fallback_eid = to_ed.get("_id") or str(i + 1)
                if fallback_eid in results:
                    ed["analise"] = results[fallback_eid]
                    applied += 1
                break

    # ── Adversarial review pass ──
    review_corrections_total = 0
    review_corrections_per_edital: dict[str, int] = {}

    if args.review:
        reviewed_editais = [ed for ed in top20 if ed.get("analise") and ed.get("analise", {}).get("_source") != "fallback"]
        if reviewed_editais:
            print(f"\n[1.5/2] Revisao adversarial de {len(reviewed_editais)} editais...")
            for ed in reviewed_editais:
                objeto = (ed.get("objeto") or "")[:60]
                eid = ed.get("_id") or objeto[:30]
                analise = ed["analise"]

                review_model = args.review_model or REVIEW_MODEL_MAP.get(args.model, args.model)
                corrections = _adversarial_review(client, ed, analise, review_model)
                num_corrections = len(corrections)
                review_corrections_per_edital[eid] = num_corrections

                if num_corrections > 0:
                    review_corrections_total += num_corrections
                    _tprint(f"    REVIEW [{eid[:40]}]: {num_corrections} correcao(oes) aplicada(s)")
                    # Merge corrections into analysis (override fields)
                    for field_name, corrected_value in corrections.items():
                        if field_name in ANALYSIS_FIELDS:
                            analise[field_name] = corrected_value
                    analise["_reviewed"] = True
                    analise["_review_corrections"] = num_corrections
                else:
                    _tprint(f"    REVIEW [{eid[:40]}]: OK — sem correcoes")
                    analise["_reviewed"] = True
                    analise["_review_corrections"] = 0

            # Re-validate after corrections
            for ed in reviewed_editais:
                if ed.get("analise", {}).get("_review_corrections", 0) > 0:
                    ed["analise"] = _validate_analysis(ed["analise"], edital=ed)

    # Compute compliance matrix for each analyzed edital (v2)
    for ed in to_analyze:
        analise = ed.get("analise")
        if analise:
            ed["analise"]["_compliance_matrix"] = _build_compliance_matrix(analise, empresa)
            matrix = ed["analise"]["_compliance_matrix"]
            atende = sum(1 for m in matrix if m["status"] == "ATENDE")
            total_m = len(matrix)
            ed["analise"]["_compliance_summary"] = f"{atende}/{total_m} auto-verificados"

    # ── Generate executive summary ──
    if not args.skip_summary:
        print(f"\n[2/2] Gerando resumo executivo...")
        try:
            resumo, passos = generate_executive_summary(client, args.model, data)
            data["resumo_executivo"] = resumo
            data["proximos_passos"] = passos
            print(f"  Resumo: {len(resumo)} chars | {len(passos)} passos")
        except Exception as exc:
            print(f"  WARN: Falha ao gerar resumo: {exc}")

    # ── Update metadata ──
    if "_metadata" not in data:
        data["_metadata"] = {}
    data["_metadata"]["analysis"] = {
        "version": VERSION,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "editais_analyzed": applied,
        "editais_total": len(top20),
        "editais_with_text": sum(1 for e in top20 if (e.get("texto_documentos") or "").strip()),
        "editais_limited": sum(
            1 for e in top20
            if e.get("analise", {}).get("_source") == "llm_limited"
        ),
        "editais_fallback": sum(
            1 for e in top20
            if e.get("analise", {}).get("_source") == "fallback"
        ),
        "participar": sum(
            1 for e in top20
            if "PARTICIPAR" in (e.get("analise", {}).get("recomendacao_acao", ""))
            and "NAO" not in (e.get("analise", {}).get("recomendacao_acao", ""))
        ),
        "nao_participar": sum(
            1 for e in top20
            if "NAO" in (e.get("analise", {}).get("recomendacao_acao", ""))
        ),
        "review_enabled": args.review,
        "review_corrections_total": review_corrections_total,
        "review_corrections_per_edital": review_corrections_per_edital,
    }

    # ── Save output ──
    out_path = args.output or str(input_path)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    elapsed = time.time() - t0

    # ── Summary ──
    analyzed_count = sum(1 for e in top20 if e.get("analise"))
    participar = sum(
        1 for e in top20
        if "PARTICIPAR" in (e.get("analise", {}).get("recomendacao_acao", ""))
        and "NAO" not in (e.get("analise", {}).get("recomendacao_acao", ""))
    )
    nao = sum(
        1 for e in top20
        if "NAO" in (e.get("analise", {}).get("recomendacao_acao", ""))
    )
    llm_ok = sum(
        1 for e in top20
        if e.get("analise", {}).get("_source") == "llm"
    )
    llm_limited = sum(
        1 for e in top20
        if e.get("analise", {}).get("_source") == "llm_limited"
    )
    fallback = sum(
        1 for e in top20
        if e.get("analise", {}).get("_source") == "fallback"
    )

    print(f"\n{'=' * 60}")
    print(f"  RESULTADO ANALISE")
    print(f"{'=' * 60}")
    print(f"  Editais analisados:    {analyzed_count}/{len(top20)}")
    print(f"  LLM completo:          {llm_ok}")
    print(f"  LLM limitado:          {llm_limited}")
    print(f"  Fallback (erro LLM):   {fallback}")
    print(f"  PARTICIPAR:            {participar}")
    print(f"  NAO PARTICIPAR:        {nao}")
    if args.review:
        print(f"  Revisao adversarial:   ON")
        print(f"  Correcoes totais:      {review_corrections_total}")
        reviewed_count = sum(1 for v in review_corrections_per_edital.values())
        corrected_count = sum(1 for v in review_corrections_per_edital.values() if v > 0)
        print(f"  Editais revisados:     {reviewed_count}")
        print(f"  Editais corrigidos:    {corrected_count}")
    print(f"  Resumo executivo:      {'Sim' if data.get('resumo_executivo') else 'Nao'}")
    print(f"  Proximos passos:       {len(data.get('proximos_passos', []))} itens")
    print(f"  Tempo total:           {elapsed:.1f}s")
    print(f"  Salvo em:              {out_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
