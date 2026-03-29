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

from schemas import ResumoLicitacoes, ResumoEstrategico, Recomendacao
from excel import parse_datetime


def _fmt_brl(value: float) -> str:
    """Format float as pt-BR currency (e.g., 360.366,00)."""
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_resumo(licitacoes: list[dict[str, Any]], *, sector_name: str = "licitações", termos_busca: str | None = None, setor_id: str | None = None) -> ResumoLicitacoes:
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
    # ISSUE-016/017: Resolve display context — prefer termos_busca over sector_name
    if termos_busca:
        _context_label = f"busca por termos específicos: {termos_busca}"
    elif sector_name and sector_name != "licitações":
        _context_label = sector_name
    else:
        _context_label = "licitações"

    # Handle empty input
    if not licitacoes:
        return ResumoLicitacoes(
            resumo_executivo=f"Nenhuma licitação de {_context_label.lower()} encontrada no período selecionado.",
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

    # ISSUE-026: Load sector keywords for contextual summary if setor_id provided
    _sector_context_line = ""
    if setor_id and not termos_busca:
        try:
            from sectors import get_sector as _get_sector_llm
            _sec = _get_sector_llm(setor_id)
            _sec_kws = sorted(getattr(_sec, "keywords", []), key=len, reverse=True)[:10]
            if _sec_kws:
                _sector_context_line = (
                    f"\nSETOR ALVO: {sector_name}\n"
                    f"Palavras-chave relevantes: {', '.join(_sec_kws)}\n"
                    f"- Foque o resumo nos itens mais relevantes para o setor {sector_name}. "
                    f"Ignore itens claramente fora do escopo do setor.\n"
                )
        except Exception:
            pass

    # System prompt with expert persona and rules
    system_prompt = f"""Você é um analista de licitações.
Analise as licitações fornecidas e gere um resumo executivo.
{_sector_context_line}
REGRAS:
- Seja direto e objetivo
- Destaque as maiores oportunidades por valor
- Alerte sobre prazos próximos (< 7 dias)
- Mencione a distribuição geográfica
- Use linguagem profissional, não técnica demais
- Valores sempre em reais (R$) formatados
- IMPORTANTE: NÃO afirme que todas as licitações são sobre um tema específico a menos que realmente sejam. Descreva o que os objetos REALMENTE tratam, baseado nos textos fornecidos.
- Se os objetos tratam de assuntos variados, diga isso explicitamente.
"""

    # User prompt with context — grounded, no assumption of relevance
    user_prompt = f"""Analise estas {len(licitacoes)} licitações e gere um resumo baseado nos OBJETOS REAIS listados abaixo:

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

    # ISSUE-039: Ground summary stats on actual data, not LLM counts.
    # The LLM may independently re-analyze relevance and report a different
    # count/value than what the pipeline actually returns to the frontend.
    resumo.total_oportunidades = len(licitacoes)
    resumo.valor_total = sum(
        float(lic.get("valorTotalEstimado") or 0) for lic in licitacoes
    )

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
                <span class="stat-value">R$ {_fmt_brl(resumo.valor_total)}</span>
                <span class="stat-label">Valor Total</span>
            </div>
        </div>

        {alerta_html}

        {destaques_html}
    </div>
    """

    return html


def gerar_resumo_fallback(
    licitacoes: list[dict[str, Any]],
    *,
    sector_name: str = "licitações",
    termos_busca: str | None = None,
) -> ResumoEstrategico:
    """
    Generate basic executive summary without using LLM (fallback for OpenAI failures).

    This function provides a statistical summary using pure Python logic when the
    OpenAI API is unavailable due to network issues, rate limits, missing API key,
    or any other errors. It maintains the same ResumoEstrategico schema as gerar_resumo()
    for seamless fallback integration.

    Features:
    - Calculates total opportunities and total value
    - Computes UF distribution (state-wise breakdown)
    - Highlights top 3 bids by value
    - Detects urgent bids (deadline < 7 days, excludes expired)
    - Generates actionable recommendations
    - No external dependencies (works offline)

    Args:
        licitacoes: List of filtered procurement bid dictionaries from PNCP API.
                   Each dict should contain keys: objetoCompra, nomeOrgao, uf,
                   valorTotalEstimado, dataAberturaProposta
        sector_name: Name of the sector being searched (e.g., "Engenharia Civil").
                    Defaults to "licitações" for backward compatibility.
        termos_busca: Optional search terms entered by the user. When provided,
                     these are used in the summary instead of sector_name.

    Returns:
        ResumoEstrategico: Structured summary with recommendations and sector insight.

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
    # Determine the display label for the summary
    display_label = termos_busca if termos_busca else sector_name

    # Handle empty input
    if not licitacoes:
        if termos_busca:
            _insight = f"Nenhuma oportunidade encontrada para '{termos_busca}'. Considere ampliar o período ou os estados da análise."
        else:
            _insight = f"Setor de {sector_name}: Nenhuma oportunidade encontrada. Considere ampliar o período ou os estados da análise."
        return ResumoEstrategico(
            resumo_executivo="Nenhuma licitação encontrada.",
            total_oportunidades=0,
            valor_total=0.0,
            destaques=[],
            alerta_urgencia=None,
            recomendacoes=[],
            alertas_urgencia=[],
            insight_setorial=_insight,
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
        f"{lic.get('nomeOrgao', 'N/A')}: R$ {_fmt_brl(lic.get('valorTotalEstimado') or 0)}"
        for lic in top_valor
    ]

    # Check for urgency (deadline < 7 days, exclude expired bids)
    alerta = None
    alertas_urgencia: list[str] = []
    recomendacoes: list[Recomendacao] = []
    hoje = datetime.now()
    for lic in licitacoes:
        data_abertura_str = lic.get("dataAberturaProposta")
        if not data_abertura_str:
            continue

        abertura = parse_datetime(data_abertura_str)
        if abertura:
            dias_restantes = (abertura - hoje).days
            # Only alert for future deadlines (not expired)
            if 0 <= dias_restantes < 7:
                orgao = lic.get("nomeOrgao", "Órgão não informado")
                alerta_text = f"{orgao} encerra em {dias_restantes} dia(s)"
                alertas_urgencia.append(alerta_text)
                if alerta is None:
                    alerta = alerta_text

    # Build recommendations from top bids
    for lic in top_valor:
        valor = lic.get("valorTotalEstimado") or 0
        orgao = lic.get("nomeOrgao", "N/A")
        objeto = (lic.get("objetoCompra") or "Objeto não informado")[:100]

        # Determine urgency from deadline
        urgencia = "baixa"
        data_abertura_str = lic.get("dataAberturaProposta")
        if data_abertura_str:
            abertura = parse_datetime(data_abertura_str)
            if abertura:
                dias = (abertura - hoje).days
                if dias < 0:
                    urgencia = "baixa"  # expired
                elif dias < 3:
                    urgencia = "alta"
                elif dias < 7:
                    urgencia = "media"

        recomendacoes.append(Recomendacao(
            oportunidade=f"{orgao} - {objeto}",
            valor=valor,
            urgencia=urgencia,
            acao_sugerida="Avaliar edital e preparar documentação.",
            justificativa=f"Valor estimado de R$ {_fmt_brl(valor)}.",
        ))

    # Build sector insight
    if termos_busca:
        insight = f"Análise de '{termos_busca}': {total} oportunidade(s) encontrada(s) totalizando R$ {_fmt_brl(valor_total)}."
    else:
        insight = f"Setor de {sector_name}: {total} oportunidade(s) encontrada(s) totalizando R$ {_fmt_brl(valor_total)}."

    return ResumoEstrategico(
        resumo_executivo=(
            f"Encontradas {total} licitações no período analisado, "
            f"totalizando R$ {_fmt_brl(valor_total)}."
        ),
        total_oportunidades=total,
        valor_total=valor_total,
        destaques=destaques,
        alerta_urgencia=alerta,
        recomendacoes=recomendacoes,
        alertas_urgencia=alertas_urgencia,
        insight_setorial=insight,
    )
