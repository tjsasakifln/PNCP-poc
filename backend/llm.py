"""
LLM integration module for generating executive summaries of procurement bids.

This module uses OpenAI's GPT-4.1-nano model with structured output to create
actionable summaries of filtered procurement opportunities. It includes:
- Token-optimized input preparation (max 50 bids)
- Structured output using Pydantic schemas
- Error handling for API failures
- Empty input handling

Usage:
    from llm import gerar_resumo
    from schemas import ResumoEstrategico

    licitacoes = [...]  # List of filtered bids
    resumo = gerar_resumo(licitacoes)
    print(resumo.resumo_executivo)
"""

from datetime import datetime, timezone
from typing import Any
import json
import os

from openai import OpenAI

from schemas import ResumoEstrategico, Recomendacao
from excel import parse_datetime
from middleware import request_id_var


def gerar_resumo(licitacoes: list[dict[str, Any]], sector_name: str = "uniformes e fardamentos") -> ResumoEstrategico:
    """
    Generate AI-powered executive summary of procurement bids using GPT-4.1-nano.

    This function calls OpenAI's API with structured output to create a comprehensive
    summary of filtered procurement opportunities. It optimizes for token usage by
    limiting input to 50 bids and truncating long descriptions.

    Args:
        licitacoes: List of filtered procurement bid dictionaries from PNCP API.
                   Each dict should contain keys: objetoCompra, nomeOrgao, uf,
                   municipio, valorTotalEstimado, dataAberturaProposta

    Returns:
        ResumoEstrategico: Strategic summary containing:
            - resumo_executivo: 1-2 sentence consultive overview
            - total_oportunidades: Count of opportunities
            - valor_total: Sum of all bid values in BRL
            - destaques: 2-5 key highlights
            - alerta_urgencia: Optional time-sensitive alert (legacy)
            - recomendacoes: Prioritized actionable recommendations
            - alertas_urgencia: Multiple urgency alerts
            - insight_setorial: Sector-level market context

    Raises:
        ValueError: If OPENAI_API_KEY environment variable is not set
        OpenAI API errors: Network issues, rate limits, auth failures

    Examples:
        >>> licitacoes = [
        ...     {
        ...         "objetoCompra": "Uniforme escolar",
        ...         "nomeOrgao": "Prefeitura de São Paulo",
        ...         "uf": "SP",
        ...         "valorTotalEstimado": 100000.0,
        ...         "dataAberturaProposta": "2025-02-15T10:00:00"
        ...     }
        ... ]
        >>> resumo = gerar_resumo(licitacoes)
        >>> resumo.total_oportunidades
        1
    """
    # Handle empty input
    if not licitacoes:
        return ResumoEstrategico(
            resumo_executivo=f"Nenhuma licitação de {sector_name} encontrada no período selecionado.",
            total_oportunidades=0,
            valor_total=0.0,
            destaques=[],
            alerta_urgencia=None,
            recomendacoes=[],
            alertas_urgencia=[],
            insight_setorial=f"Não foram encontradas oportunidades de {sector_name} nos filtros selecionados. Considere ampliar o período ou os estados de busca.",
        )

    # Validate API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable not set. "
            "Please configure your OpenAI API key."
        )

    # Prepare data for LLM (limit to 50 bids to avoid token overflow)
    # Use UTC for correct timestamp; strip tzinfo for comparison with naive
    # datetimes from parse_datetime() (which strips tz for Excel compatibility)
    hoje = datetime.now(timezone.utc).replace(tzinfo=None)
    dados_resumidos = []
    for lic in licitacoes[:50]:
        # Calculate days remaining for urgency classification
        dias_restantes = None
        data_abertura_str = lic.get("dataAberturaProposta") or ""
        if data_abertura_str:
            abertura_dt = parse_datetime(data_abertura_str)
            if abertura_dt:
                dias_restantes = (abertura_dt - hoje).days

        dados_resumidos.append(
            {
                "objeto": (lic.get("objetoCompra") or "")[
                    :200
                ],  # Truncate to 200 chars
                "orgao": lic.get("nomeOrgao") or "",
                "uf": lic.get("uf") or "",
                "municipio": lic.get("municipio") or "",
                "valor": lic.get("valorTotalEstimado") or 0,
                "abertura": data_abertura_str,
                "dias_restantes": dias_restantes,
            }
        )

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # System prompt with strategic consultant persona (STORY-245)
    system_prompt = f"""Você é um CONSULTOR ESTRATÉGICO de licitações especializado em {sector_name}.
Seu papel NÃO é apenas descrever — é RECOMENDAR AÇÕES CONCRETAS para o usuário.

PERSONA: Consultor sênior com 15 anos de experiência em licitações públicas no setor de {sector_name}. Você ajuda empresas a decidir em quais licitações participar e como se preparar.

REGRAS DE RECOMENDAÇÃO:
1. Para cada oportunidade relevante, forneça uma AÇÃO CONCRETA e uma JUSTIFICATIVA
2. Priorize por combinação de valor + urgência + viabilidade
3. Recomende no máximo 5 oportunidades (as mais relevantes)

REGRAS DE URGÊNCIA (campo "dias_restantes" nos dados):
- "alta": dias_restantes < 3 (ação IMEDIATA necessária)
- "media": dias_restantes entre 3 e 7 (preparar documentação esta semana)
- "baixa": dias_restantes > 7 (tempo para análise detalhada)

REGRAS CRÍTICAS DE TERMINOLOGIA:
1. NUNCA use estes termos ambíguos:
   - ❌ "prazo de abertura"
   - ❌ "abertura em [data]"
   - ❌ "prazo em [data]" (sem contexto claro)

2. SEMPRE use estes termos claros para datas:
   - ✅ "recebe propostas a partir de [data_início]"
   - ✅ "prazo final para propostas em [data_fim]"
   - ✅ "você tem X dias para enviar proposta até [data_fim]"
   - ✅ "encerra em [data_fim]"

FORMATO DO RESUMO EXECUTIVO:
- Tom consultivo: "Recomendamos atenção a X oportunidades..."
- Destaque valor total e distribuição geográfica
- Mencione a oportunidade de maior valor
- Para prazos urgentes (< 3 dias): "encerra em X dias — ação imediata necessária"
- Valores sempre em reais (R$) formatados

INSIGHT SETORIAL:
- Contextualize as oportunidades no mercado de {sector_name}
- Mencione concentração geográfica se houver padrão
- Se possível, compare com expectativas do setor

ALERTAS DE URGÊNCIA (lista):
- Gere um alerta para cada situação crítica encontrada
- Inclua prazos curtos, exigências documentais, valores atípicos
"""

    # User prompt with context
    user_prompt = f"""Analise estas {len(licitacoes)} licitações de {sector_name} como consultor estratégico.

Para cada oportunidade relevante, forneça:
1. Ação concreta que o usuário deve tomar
2. Justificativa de por que vale a pena participar
3. Classificação de urgência baseada nos dias_restantes

Dados das licitações:
{json.dumps(dados_resumidos, ensure_ascii=False, indent=2)}

Data atual: {hoje.strftime("%d/%m/%Y")}
"""

    # STORY-226 AC23: Forward X-Request-ID for distributed tracing
    req_id = request_id_var.get("-")
    extra_headers = {}
    if req_id and req_id != "-":
        extra_headers["X-Request-ID"] = req_id

    # Call OpenAI API with structured output (STORY-245: max_tokens 500→1200 for recommendations)
    response = client.beta.chat.completions.parse(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=ResumoEstrategico,
        temperature=0.3,
        max_tokens=1200,
        extra_headers=extra_headers if extra_headers else None,
    )

    # Extract parsed response
    resumo = response.choices[0].message.parsed

    if not resumo:
        raise ValueError("OpenAI API returned empty response")

    # CRITICAL: Validate that ambiguous deadline terminology is not present
    forbidden_terms = [
        "prazo de abertura",
        "abertura em",
        "abertura:",
    ]
    resumo_text = resumo.resumo_executivo.lower()
    for term in forbidden_terms:
        if term in resumo_text:
            # Log the error for monitoring
            import logging
            logging.warning(
                f"LLM generated ambiguous term '{term}' in summary: {resumo.resumo_executivo}"
            )
            # Fail fast to prevent user confusion
            raise ValueError(
                f"LLM output contains ambiguous deadline terminology: '{term}'. "
                "This violates UX clarity rules. Please regenerate summary."
            )

    return resumo


def gerar_resumo_fallback(licitacoes: list[dict[str, Any]], sector_name: str = "uniformes") -> ResumoEstrategico:
    """
    Generate strategic summary without using LLM (fallback for OpenAI failures).

    This function provides a heuristic-based strategic summary using pure Python logic
    when the OpenAI API is unavailable. It generates actionable recommendations based
    on value and urgency heuristics, maintaining the same ResumoEstrategico schema
    as gerar_resumo() for seamless fallback integration.

    Args:
        licitacoes: List of filtered procurement bid dictionaries from PNCP API.
        sector_name: Name of the sector for context.

    Returns:
        ResumoEstrategico: Strategic summary with heuristic recommendations.

    Examples:
        >>> licitacoes = [
        ...     {
        ...         "nomeOrgao": "Prefeitura de SP",
        ...         "uf": "SP",
        ...         "valorTotalEstimado": 150000.0,
        ...         "dataAberturaProposta": "2025-03-01T10:00:00"
        ...     }
        ... ]
        >>> resumo = gerar_resumo_fallback(licitacoes)
        >>> resumo.total_oportunidades
        1
    """
    # Handle empty input
    if not licitacoes:
        return ResumoEstrategico(
            resumo_executivo="Nenhuma licitação encontrada.",
            total_oportunidades=0,
            valor_total=0.0,
            destaques=[],
            alerta_urgencia=None,
            recomendacoes=[],
            alertas_urgencia=[],
            insight_setorial=f"Não foram encontradas oportunidades de {sector_name} nos filtros selecionados.",
        )

    # Calculate basic statistics
    total = len(licitacoes)
    valor_total = sum(lic.get("valorTotalEstimado", 0) or 0 for lic in licitacoes)

    # Compute UF distribution (state-wise breakdown)
    dist_uf: dict[str, int] = {}
    for lic in licitacoes:
        uf = lic.get("uf", "N/A")
        dist_uf[uf] = dist_uf.get(uf, 0) + 1

    # Find top 3 bids by value
    top_valor = sorted(
        licitacoes, key=lambda x: x.get("valorTotalEstimado", 0) or 0, reverse=True
    )[:3]

    destaques = [
        f"{lic.get('nomeOrgao', 'N/A')}: R$ {(lic.get('valorTotalEstimado') or 0):,.2f}"
        for lic in top_valor
    ]

    # Build recommendations and urgency alerts from heuristics
    hoje = datetime.now(timezone.utc).replace(tzinfo=None)
    recomendacoes: list[Recomendacao] = []
    alertas_urgencia: list[str] = []
    alerta_legacy = None  # backward compat single alert

    for lic in licitacoes:
        data_abertura_str = lic.get("dataAberturaProposta")
        dias_restantes = None
        if data_abertura_str:
            abertura = parse_datetime(data_abertura_str)
            if abertura:
                dias_restantes = (abertura - hoje).days

        valor = lic.get("valorTotalEstimado") or 0
        orgao = lic.get("nomeOrgao", "Órgão não informado")
        objeto = (lic.get("objetoCompra") or "")[:100]

        # Classify urgency
        if dias_restantes is not None and dias_restantes < 3:
            urgencia = "alta"
            alerta_msg = f"⚠️ {orgao}: encerra em {dias_restantes} dia(s) — ação imediata necessária"
            alertas_urgencia.append(alerta_msg)
            if alerta_legacy is None:
                alerta_legacy = alerta_msg
        elif dias_restantes is not None and dias_restantes < 7:
            urgencia = "media"
            alerta_msg = f"📋 {orgao}: encerra em {dias_restantes} dia(s) — prepare documentação"
            alertas_urgencia.append(alerta_msg)
            if alerta_legacy is None:
                alerta_legacy = alerta_msg
        else:
            urgencia = "baixa"

        # Build recommendation for top bids (max 5)
        if len(recomendacoes) < 5 and (valor > 0 or urgencia != "baixa"):
            if urgencia == "alta":
                acao = f"Ação imediata: prepare e envie proposta nos próximos {dias_restantes} dia(s)."
            elif urgencia == "media":
                acao = f"Prepare documentação esta semana. Prazo final em {dias_restantes} dias."
            else:
                acao = "Analise o edital com calma e avalie requisitos técnicos antes de participar."

            justificativa = f"Valor de R$ {valor:,.2f}"
            if lic.get("uf"):
                justificativa += f" em {lic['uf']}"
            if objeto:
                justificativa += f" — {objeto}"

            recomendacoes.append(Recomendacao(
                oportunidade=f"{orgao}" + (f" — {objeto[:60]}" if objeto else ""),
                valor=valor,
                urgencia=urgencia,
                acao_sugerida=acao,
                justificativa=justificativa,
            ))

    # Sort recommendations: alta first, then media, then by value desc
    urgencia_order = {"alta": 0, "media": 1, "baixa": 2}
    recomendacoes.sort(key=lambda r: (urgencia_order[r.urgencia], -r.valor))

    # Generate insight setorial from data
    ufs_str = ", ".join(sorted(dist_uf.keys()))
    insight = f"Setor de {sector_name}: {total} oportunidades distribuídas em {len(dist_uf)} estado(s) ({ufs_str}), totalizando R$ {valor_total:,.2f}."

    # Consultive resumo executivo
    urgentes = sum(1 for r in recomendacoes if r.urgencia == "alta")
    resumo_exec = f"Encontradas {total} licitações de {sector_name} totalizando R$ {valor_total:,.2f}."
    if urgentes > 0:
        resumo_exec += f" Recomendamos atenção imediata a {urgentes} oportunidade(s) com prazo curto."
    elif recomendacoes:
        resumo_exec += f" Destacamos {len(recomendacoes)} oportunidade(s) para análise."

    return ResumoEstrategico(
        resumo_executivo=resumo_exec,
        total_oportunidades=total,
        valor_total=valor_total,
        destaques=destaques,
        alerta_urgencia=alerta_legacy,
        recomendacoes=recomendacoes,
        alertas_urgencia=alertas_urgencia,
        insight_setorial=insight,
    )
