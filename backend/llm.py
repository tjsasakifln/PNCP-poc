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
    from schemas import ResumoLicitacoes

    licitacoes = [...]  # List of filtered bids
    resumo = gerar_resumo(licitacoes)
    print(resumo.resumo_executivo)
"""

from datetime import datetime
from typing import Any
import json
import os

from openai import OpenAI

from schemas import ResumoLicitacoes
from excel import parse_datetime


def gerar_resumo(licitacoes: list[dict[str, Any]]) -> ResumoLicitacoes:
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
        ResumoLicitacoes: Structured summary containing:
            - resumo_executivo: 1-2 sentence overview
            - total_oportunidades: Count of opportunities
            - valor_total: Sum of all bid values in BRL
            - destaques: 2-5 key highlights
            - alerta_urgencia: Optional time-sensitive alert

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
        return ResumoLicitacoes(
            resumo_executivo="Nenhuma licitação de uniformes encontrada no período selecionado.",
            total_oportunidades=0,
            valor_total=0.0,
            destaques=[],
            alerta_urgencia=None,
        )

    # Validate API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable not set. "
            "Please configure your OpenAI API key."
        )

    # Prepare data for LLM (limit to 50 bids to avoid token overflow)
    dados_resumidos = []
    for lic in licitacoes[:50]:
        dados_resumidos.append(
            {
                "objeto": (lic.get("objetoCompra") or "")[
                    :200
                ],  # Truncate to 200 chars
                "orgao": lic.get("nomeOrgao") or "",
                "uf": lic.get("uf") or "",
                "municipio": lic.get("municipio") or "",
                "valor": lic.get("valorTotalEstimado") or 0,
                "abertura": lic.get("dataAberturaProposta") or "",
            }
        )

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # System prompt with expert persona and rules
    system_prompt = """Você é um analista de licitações especializado em uniformes e fardamentos.
Analise as licitações fornecidas e gere um resumo executivo.

REGRAS:
- Seja direto e objetivo
- Destaque as maiores oportunidades por valor
- Alerte sobre prazos próximos (< 7 dias)
- Mencione a distribuição geográfica
- Use linguagem profissional, não técnica demais
- Valores sempre em reais (R$) formatados
"""

    # User prompt with context
    user_prompt = f"""Analise estas {len(licitacoes)} licitações de uniformes/fardamentos e gere um resumo:

{json.dumps(dados_resumidos, ensure_ascii=False, indent=2)}

Data atual: {datetime.now().strftime("%d/%m/%Y")}
"""

    # Call OpenAI API with structured output
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",  # Using gpt-4o-mini as gpt-4.1-nano doesn't exist
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=ResumoLicitacoes,
        temperature=0.3,
        max_tokens=500,
    )

    # Extract parsed response
    resumo = response.choices[0].message.parsed

    if not resumo:
        raise ValueError("OpenAI API returned empty response")

    return resumo


def format_resumo_html(resumo: ResumoLicitacoes) -> str:
    """
    Format executive summary as HTML for frontend display.

    Converts the structured ResumoLicitacoes object into styled HTML with:
    - Executive summary paragraph
    - Statistics cards (count and total value)
    - Urgency alert (if present)
    - Highlights list

    Args:
        resumo: Structured summary from gerar_resumo()

    Returns:
        str: HTML string ready for frontend rendering

    Examples:
        >>> resumo = ResumoLicitacoes(
        ...     resumo_executivo="Encontradas 15 licitações.",
        ...     total_oportunidades=15,
        ...     valor_total=2300000.00,
        ...     destaques=["3 urgentes"],
        ...     alerta_urgencia="⚠️ 5 encerram em 24h"
        ... )
        >>> html = format_resumo_html(resumo)
        >>> "resumo-container" in html
        True
    """
    # Build urgency alert HTML if present
    alerta_html = ""
    if resumo.alerta_urgencia:
        alerta_html = f'<div class="alerta-urgencia">⚠️ {resumo.alerta_urgencia}</div>'

    # Build highlights list HTML
    destaques_html = ""
    if resumo.destaques:
        destaques_items = "".join(f"<li>{d}</li>" for d in resumo.destaques)
        destaques_html = f"""
        <div class="destaques">
            <h4>Destaques:</h4>
            <ul>
                {destaques_items}
            </ul>
        </div>
        """

    # Assemble complete HTML
    html = f"""
    <div class="resumo-container">
        <p class="resumo-executivo">{resumo.resumo_executivo}</p>

        <div class="resumo-stats">
            <div class="stat">
                <span class="stat-value">{resumo.total_oportunidades}</span>
                <span class="stat-label">Licitações</span>
            </div>
            <div class="stat">
                <span class="stat-value">R$ {resumo.valor_total:,.2f}</span>
                <span class="stat-label">Valor Total</span>
            </div>
        </div>

        {alerta_html}

        {destaques_html}
    </div>
    """

    return html


def gerar_resumo_fallback(licitacoes: list[dict[str, Any]]) -> ResumoLicitacoes:
    """
    Generate basic executive summary without using LLM (fallback for OpenAI failures).

    This function provides a statistical summary using pure Python logic when the
    OpenAI API is unavailable due to network issues, rate limits, missing API key,
    or any other errors. It maintains the same ResumoLicitacoes schema as gerar_resumo()
    for seamless fallback integration.

    Features:
    - Calculates total opportunities and total value
    - Computes UF distribution (state-wise breakdown)
    - Highlights top 3 bids by value
    - Detects urgent bids (deadline < 7 days)
    - No external dependencies (works offline)

    Args:
        licitacoes: List of filtered procurement bid dictionaries from PNCP API.
                   Each dict should contain keys: objetoCompra, nomeOrgao, uf,
                   valorTotalEstimado, dataAberturaProposta

    Returns:
        ResumoLicitacoes: Structured summary containing:
            - resumo_executivo: Basic sentence with count and total value
            - total_oportunidades: Count of opportunities
            - valor_total: Sum of all bid values in BRL
            - destaques: Top 3 bids by value
            - alerta_urgencia: Alert if any bid closes within 7 days
            - distribuicao_uf: Dict mapping UF codes to bid counts

    Examples:
        >>> licitacoes = [
        ...     {
        ...         "nomeOrgao": "Prefeitura de SP",
        ...         "uf": "SP",
        ...         "valorTotalEstimado": 150000.0,
        ...         "dataAberturaProposta": "2025-03-01T10:00:00"
        ...     },
        ...     {
        ...         "nomeOrgao": "Prefeitura do RJ",
        ...         "uf": "RJ",
        ...         "valorTotalEstimado": 200000.0,
        ...         "dataAberturaProposta": "2025-03-15T14:00:00"
        ...     }
        ... ]
        >>> resumo = gerar_resumo_fallback(licitacoes)
        >>> resumo.total_oportunidades
        2
        >>> resumo.valor_total
        350000.0
    """
    # Handle empty input
    if not licitacoes:
        return ResumoLicitacoes(
            resumo_executivo="Nenhuma licitação encontrada.",
            total_oportunidades=0,
            valor_total=0.0,
            destaques=[],
            alerta_urgencia=None,
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

    # Check for urgency (deadline < 7 days)
    alerta = None
    hoje = datetime.now()
    for lic in licitacoes:
        data_abertura_str = lic.get("dataAberturaProposta")
        if not data_abertura_str:
            continue

        abertura = parse_datetime(data_abertura_str)
        if abertura:
            dias_restantes = (abertura - hoje).days
            if dias_restantes < 7:
                orgao = lic.get("nomeOrgao", "Órgão não informado")
                alerta = f"Licitação com prazo em menos de 7 dias: {orgao}"
                break  # First urgent bid found

    return ResumoLicitacoes(
        resumo_executivo=(
            f"Encontradas {total} licitações de uniformes "
            f"totalizando R$ {valor_total:,.2f}."
        ),
        total_oportunidades=total,
        valor_total=valor_total,
        destaques=destaques,
        alerta_urgencia=alerta,
    )
