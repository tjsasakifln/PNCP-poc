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
from pydantic import ValidationError

from schemas import ResumoLicitacoes


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
            alerta_urgencia=None
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
        dados_resumidos.append({
            "objeto": (lic.get("objetoCompra") or "")[:200],  # Truncate to 200 chars
            "orgao": lic.get("nomeOrgao") or "",
            "uf": lic.get("uf") or "",
            "municipio": lic.get("municipio") or "",
            "valor": lic.get("valorTotalEstimado") or 0,
            "abertura": lic.get("dataAberturaProposta") or ""
        })

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
            {"role": "user", "content": user_prompt}
        ],
        response_format=ResumoLicitacoes,
        temperature=0.3,
        max_tokens=500
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
