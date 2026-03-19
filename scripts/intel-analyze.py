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

VERSION = "1.0.0"

MAX_TEXT_CHARS = 50_000       # Truncate document text beyond this
MAX_TOKENS_RESPONSE = 2_000  # Max tokens for LLM response
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
5. nivel_dificuldade DEVE ser exatamente "BAIXO", "MEDIO" ou "ALTO".
6. criterio_julgamento DEVE ser um dos: Menor Preco, Tecnica e Preco, Maior Desconto, Menor Preco Global, Menor Preco por Item, Melhor Tecnica, ou "Nao consta no edital disponivel".
7. visita_tecnica DEVE ser: Obrigatoria, Facultativa, ou "Nao consta no edital disponivel".
8. regime_execucao DEVE ser: Empreitada por preco global, Empreitada por preco unitario, Semi-Integrada, Tarefa, Contratacao Integrada, ou "Nao consta no edital disponivel".
9. consorcio DEVE ser: Permitido, Vedado, ou "Nao mencionado no edital".
10. resumo_objeto deve ter 2-3 frases concisas descrevendo o que esta sendo contratado.
11. requisitos_tecnicos e requisitos_habilitacao sao listas de strings (minimo 1 item cada).
12. Datas no formato DD/MM/YYYY HH:MM ou "Nao consta no edital disponivel".
13. Se o edital e claramente incompativel com a atividade da empresa, recomende "NAO PARTICIPAR" com justificativa em observacoes_criticas.
14. Seja CONCRETO — extraia numeros, datas, percentuais, valores exatos do texto.

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
  "nivel_dificuldade": "BAIXO|MEDIO|ALTO",
  "recomendacao_acao": "PARTICIPAR|NAO PARTICIPAR",
  "custo_logistico_nota": "string"
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

    # Temporal status
    status = edital.get("status_temporal")
    if status:
        parts.append(f"STATUS TEMPORAL: {status}")
    data_abertura = edital.get("data_abertura") or edital.get("data_sessao")
    if data_abertura:
        parts.append(f"DATA ABERTURA: {data_abertura}")

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


def _validate_analysis(analysis: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize analysis fields to match expected schema."""
    # Ensure all required fields exist
    for field in ANALYSIS_FIELDS:
        if field not in analysis:
            if field in ("requisitos_tecnicos", "requisitos_habilitacao"):
                analysis[field] = ["Nao consta no edital disponivel"]
            else:
                analysis[field] = "Nao consta no edital disponivel"

    # Enforce enums
    if analysis.get("nivel_dificuldade", "").upper() not in DIFICULDADE_ENUM:
        analysis["nivel_dificuldade"] = "MEDIO"
    else:
        analysis["nivel_dificuldade"] = analysis["nivel_dificuldade"].upper()

    rec = (analysis.get("recomendacao_acao") or "").upper()
    if "NAO" in rec or "NÃO" in rec:
        analysis["recomendacao_acao"] = "NAO PARTICIPAR"
    elif "PARTICIPAR" in rec:
        analysis["recomendacao_acao"] = "PARTICIPAR"
    else:
        # Default to NAO PARTICIPAR if unclear (zero noise philosophy)
        analysis["recomendacao_acao"] = "NAO PARTICIPAR"

    # Ensure lists are actually lists
    for list_field in ("requisitos_tecnicos", "requisitos_habilitacao"):
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
            analysis = _validate_analysis(raw)

            # Add metadata
            analysis["_source"] = "llm" if not limited else "llm_limited"
            analysis["_model"] = model
            analysis["_texto_chars"] = len(texto)

            _tprint(f"    OK — {analysis['recomendacao_acao']} | {analysis['nivel_dificuldade']}")
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
        "nivel_dificuldade": "MEDIO",
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
        ("\n..." if len(nao_participar) > 10 else "")
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
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

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
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    top20 = data.get("top20", [])

    print(f"{'=' * 60}")
    print(f"  INTEL-ANALYZE v{VERSION} — SAVE-ANALYSIS MODE")
    print(f"  Input: {input_path}")
    print(f"{'=' * 60}")

    analyzed = 0
    for ed in top20:
        analise = ed.get("analise")
        if analise:
            ed["analise"] = _validate_analysis(analise)
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
    parser = argparse.ArgumentParser(
        description="Intel Analyze — Analise LLM automatizada dos top editais para /intel-busca",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        metavar="JSON",
        help="JSON de entrada (output do intel-extract-docs.py com top20[])",
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
        help="Numero maximo de editais do top20 a analisar (default: 20)",
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
        help="Modelo OpenAI a usar no modo API (default: gpt-4.1-nano)",
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
        help="Re-analisar editais que ja possuem campo 'analise'",
    )
    parser.add_argument(
        "--review",
        action="store_true",
        help="Habilitar revisao adversarial pos-analise (modo API)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduzir output",
    )
    args = parser.parse_args()

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

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    empresa = data.get("empresa", {})
    top20 = data.get("top20", [])

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

                corrections = _adversarial_review(client, ed, analise, args.model)
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
                    ed["analise"] = _validate_analysis(ed["analise"])

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
