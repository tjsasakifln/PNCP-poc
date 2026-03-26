"""Search-related schemas: BuscaRequest, BuscaResponse, LicitacaoItem, etc."""

from datetime import date
from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Dict, List, Literal, Optional, Union

from schemas.common import (
    StatusLicitacao,
    EsferaGovernamental,
)


class SearchQueuedResponse(BaseModel):
    """GTM-STAB-009 AC1: Response schema for 202 Accepted (async search queued).

    Returned when SEARCH_ASYNC_ENABLED=true and ARQ worker is available.
    POST /buscar returns this in <1s instead of processing inline.
    """
    search_id: str = Field(..., description="UUID for SSE correlation")
    status: Literal["queued"] = Field("queued", description="Job status")
    status_url: str = Field(..., description="Polling endpoint for search progress")
    progress_url: str = Field(..., description="SSE endpoint for real-time progress")
    estimated_duration_s: int = Field(45, description="Estimated pipeline duration")


class SearchStatusResponse(BaseModel):
    """GTM-STAB-009 AC3: Enriched status response for /v1/search/{id}/status.

    Populated from in-memory progress tracker + state machine (lightweight, <50ms).
    No database queries — reads only from in-memory state.

    STORY-364 AC1: Includes excel_url and excel_status for polling fallback.
    """
    search_id: str = Field(..., description="UUID of the search")
    status: str = Field(..., description="running, completed, failed, or timeout")
    progress_pct: int = Field(0, description="Overall progress 0-100")
    ufs_completed: list[str] = Field(default_factory=list, description="UFs that finished fetching")
    ufs_pending: list[str] = Field(default_factory=list, description="UFs still being fetched")
    results_count: int = Field(0, description="Number of filtered results so far")
    results_url: Optional[str] = Field(None, description="URL to fetch full results (set when completed)")
    elapsed_s: float = Field(0.0, description="Seconds since search started")
    created_at: Optional[str] = Field(None, description="ISO timestamp when search was created")
    excel_url: Optional[str] = Field(None, description="Signed URL for Excel download (set when ready)")
    excel_status: Optional[str] = Field(None, description="Excel generation status: processing, ready, failed, skipped")


class BuscaRequest(BaseModel):
    """
    Request schema for /buscar endpoint.

    Validates user input for procurement search:
    - At least 1 Brazilian state (UF) must be selected
    - Dates must be in YYYY-MM-DD format
    - data_inicial must be <= data_final
    - Date range cannot exceed 30 days
    - data_final cannot be in the future
    - valor_maximo must be >= valor_minimo (if both provided)

    Examples:
        >>> request = BuscaRequest(
        ...     ufs=["SP", "RJ"],
        ...     data_inicial="2025-01-01",
        ...     data_final="2025-01-31"
        ... )
        >>> request.ufs
        ['SP', 'RJ']

        >>> # With new P0/P1 filters
        >>> request = BuscaRequest(
        ...     ufs=["SP"],
        ...     data_inicial="2025-01-01",
        ...     data_final="2025-01-31",
        ...     status=StatusLicitacao.RECEBENDO_PROPOSTA,
        ...     modalidades=[1, 2, 6],
        ...     valor_minimo=50000,
        ...     valor_maximo=500000,
        ...     esferas=[EsferaGovernamental.MUNICIPAL]
        ... )
    """

    # -------------------------------------------------------------------------
    # Required Fields (Existing)
    # -------------------------------------------------------------------------
    ufs: List[str] = Field(
        ...,
        min_length=1,
        description="List of Brazilian state codes (e.g., ['SP', 'RJ', 'MG'])",
        examples=[["SP", "RJ"]],
    )
    data_inicial: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Start date in YYYY-MM-DD format",
        examples=["2025-01-01"],
    )
    data_final: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="End date in YYYY-MM-DD format",
        examples=["2025-01-31"],
    )

    # -------------------------------------------------------------------------
    # Optional Fields (Existing)
    # -------------------------------------------------------------------------
    setor_id: str = Field(
        default="vestuario",
        description="Sector ID for keyword filtering (e.g., 'vestuario', 'alimentos', 'informatica')",
        examples=["vestuario"],
    )
    termos_busca: Optional[str] = Field(
        default=None,
        description="Custom search terms. Use commas to separate multi-word phrases "
                    "(e.g., 'levantamento topográfico, terraplenagem, drenagem'). "
                    "Without commas, spaces separate individual keywords (legacy mode).",
        examples=["jaleco avental", "levantamento topográfico, terraplenagem, drenagem"],
    )
    show_all_matches: Optional[bool] = Field(
        default=False,
        description="When True, bypasses minimum match floor and returns all results "
                    "with at least 1 keyword match (for 'show hidden results' feature).",
    )
    exclusion_terms: Optional[List[str]] = Field(
        default=None,
        description="Custom exclusion terms. Overrides sector exclusions when provided.",
    )
    modo_busca: Optional[str] = Field(
        default="abertas",
        description="Modo de busca: 'abertas' (padrão) busca licitações com prazo aberto "
                    "nos últimos 180 dias; 'publicacao' usa datas enviadas pelo frontend.",
        examples=["abertas", "publicacao"],
    )

    # -------------------------------------------------------------------------
    # NEW P0 Filters: Status, Modalidade, Valor
    # -------------------------------------------------------------------------
    status: StatusLicitacao = Field(
        default=StatusLicitacao.TODOS,
        description=(
            "Status da licitação para filtrar. Padrão: 'todos' (sem filtro de status). "
            "IMPORTANTE: Filtro de status desabilitado por padrão devido a valores inconsistentes "
            "na API PNCP. Use 'todos' para máxima cobertura de resultados."
        ),
        examples=["todos", "recebendo_proposta", "em_julgamento", "encerrada"],
    )

    modalidades: Optional[List[int]] = Field(
        default=None,
        description="Lista de códigos de modalidade conforme API PNCP. "
                    "Códigos válidos: 1 (Leilão Eletrônico), 2 (Diálogo Competitivo), "
                    "3 (Concurso), 4 (Concorrência Eletrônica), 5 (Concorrência Presencial), "
                    "6 (Pregão Eletrônico), 7 (Pregão Presencial), 8 (Dispensa), "
                    "10 (Manifestação de Interesse), 11 (Pré-qualificação), "
                    "12 (Credenciamento), 13 (Leilão Presencial), 15 (Chamada Pública). "
                    "None = modalidades padrão [4, 5, 6, 7]. "
                    "EXCLUÍDOS: 9 (Inexigibilidade) e 14 (Inaplicabilidade) — vencedor pré-definido.",
        examples=[[4, 5, 6, 7]],
    )

    valor_minimo: Optional[float] = Field(
        default=None,
        ge=0,
        description="Valor mínimo estimado da licitação em BRL. None = sem limite inferior.",
        examples=[50000.0],
    )

    valor_maximo: Optional[float] = Field(
        default=None,
        ge=0,
        description="Valor máximo estimado da licitação em BRL. None = sem limite superior.",
        examples=[5000000.0],
    )

    # -------------------------------------------------------------------------
    # NEW P1 Filters: Esfera, Município, Ordenação
    # -------------------------------------------------------------------------
    esferas: Optional[List[EsferaGovernamental]] = Field(
        default=None,
        description="Lista de esferas governamentais ('F'=Federal, 'E'=Estadual, 'M'=Municipal). "
                    "None = todas as esferas.",
        examples=[["M", "E"]],
    )

    municipios: Optional[List[str]] = Field(
        default=None,
        description="Lista de códigos IBGE de municípios para filtrar. "
                    "None = todos os municípios das UFs selecionadas.",
        examples=[["3550308", "3304557"]],  # São Paulo, Rio de Janeiro
    )

    ordenacao: str = Field(
        default="data_desc",
        description="Critério de ordenação dos resultados: "
                    "'data_desc' (mais recente), 'data_asc' (mais antigo), "
                    "'valor_desc' (maior valor), 'valor_asc' (menor valor), "
                    "'prazo_asc' (prazo mais próximo), 'relevancia' (score de matching).",
        examples=["data_desc", "valor_desc", "prazo_asc"],
    )

    # -------------------------------------------------------------------------
    # NEW P2 Filters: Órgão, Paginação (Issue #xxx - P2 Enhancement)
    # -------------------------------------------------------------------------
    orgaos: Optional[List[str]] = Field(
        default=None,
        description="Lista de nomes de órgãos/entidades para filtrar (busca parcial). "
                    "None = todos os órgãos.",
        examples=[["Prefeitura de São Paulo", "Ministério da Saúde"]],
    )

    pagina: int = Field(
        default=1,
        ge=1,
        description="Número da página de resultados (1-indexed). Padrão: 1.",
        examples=[1, 2, 3],
    )

    itens_por_pagina: int = Field(
        default=20,
        ge=10,
        le=100,
        description="Quantidade de itens por página. Valores permitidos: 10, 20, 50, 100. Padrão: 20.",
        examples=[10, 20, 50, 100],
    )

    # -------------------------------------------------------------------------
    # SSE Progress Tracking (Real-Time Progress)
    # -------------------------------------------------------------------------
    search_id: Optional[str] = Field(
        default=None,
        max_length=36,
        description="Client-generated UUID for SSE progress tracking via /buscar-progress/{search_id}.",
    )

    # -------------------------------------------------------------------------
    # Sanctions Check (STORY-256 AC12)
    # -------------------------------------------------------------------------
    check_sanctions: bool = Field(
        default=False,
        description="When true, verify supplier CNPJs against CEIS/CNEP sanctions databases. "
                    "Adds supplier_sanctions field to each result. Performance impact: ~1s per unique CNPJ.",
    )

    # -------------------------------------------------------------------------
    # STORY-257A AC10: Cache bypass
    # -------------------------------------------------------------------------
    force_fresh: bool = Field(
        default=False,
        description="When true, bypass result cache and always query primary sources. "
                    "Cache write-through still happens on successful results.",
    )

    # -------------------------------------------------------------------------
    # Validators
    # -------------------------------------------------------------------------
    @model_validator(mode="after")
    def validate_dates_and_values(self) -> "BuscaRequest":
        """
        Validate business logic:
        1. Date range validation (data_inicial <= data_final)
        2. Value range validation (valor_maximo >= valor_minimo)
        """
        # Date validation
        try:
            d_ini = date.fromisoformat(self.data_inicial)
            d_fin = date.fromisoformat(self.data_final)
        except ValueError as e:
            raise ValueError(f"Data inválida: {e}")

        if d_ini > d_fin:
            raise ValueError(
                "Data inicial deve ser anterior ou igual à data final"
            )

        # Value range validation
        if self.valor_minimo is not None and self.valor_maximo is not None:
            if self.valor_maximo < self.valor_minimo:
                raise ValueError(
                    "valor_maximo deve ser maior ou igual a valor_minimo "
                    f"(min={self.valor_minimo}, max={self.valor_maximo})"
                )

        return self

    @field_validator('modo_busca')
    @classmethod
    def validate_modo_busca(cls, v: Optional[str]) -> Optional[str]:
        """Validate modo_busca is one of the allowed values."""
        allowed = {"abertas", "publicacao"}
        if v is not None and v not in allowed:
            raise ValueError(
                f"modo_busca inválido: '{v}'. Valores permitidos: {sorted(allowed)}"
            )
        return v

    @field_validator('modalidades')
    @classmethod
    def validate_modalidades(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        """
        Validate that modalidade codes match real PNCP API codes.

        Valid codes: 1-8, 10-13, 15 (all PNCP modalities except excluded).
        EXCLUDED: 9 (Inexigibilidade) and 14 (Inaplicabilidade) — pre-defined winner.
        """
        if v is None:
            return v

        # Valid codes per PNCP API (excluding 9=Inexigibilidade, 14=Inaplicabilidade)
        valid_codes = {1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 15}

        # Check for excluded codes specifically
        excluded_codes = [code for code in v if code in (9, 14)]
        if excluded_codes:
            raise ValueError(
                f"Modalidades excluídas: {excluded_codes}. "
                f"9 (Inexigibilidade) e 14 (Inaplicabilidade) não são permitidas "
                f"(vencedor pré-definido)."
            )

        # Check for invalid codes
        invalid_codes = [code for code in v if code not in valid_codes]
        if invalid_codes:
            raise ValueError(
                f"Códigos de modalidade inválidos: {invalid_codes}. "
                f"Valores válidos (API PNCP): {sorted(valid_codes)}."
            )

        return v

    @field_validator('ordenacao')
    @classmethod
    def validate_ordenacao(cls, v: str) -> str:
        """Validate that ordenacao is a valid option."""
        valid_options = {
            'data_desc', 'data_asc',
            'valor_desc', 'valor_asc',
            'prazo_asc', 'relevancia',
            'confianca',
        }
        if v not in valid_options:
            raise ValueError(
                f"Ordenação inválida: '{v}'. "
                f"Opções válidas: {sorted(valid_options)}"
            )
        return v

    @field_validator('itens_por_pagina')
    @classmethod
    def validate_itens_por_pagina(cls, v: int) -> int:
        """Validate that itens_por_pagina is one of the allowed values."""
        valid_options = {10, 20, 50, 100}
        if v not in valid_options:
            raise ValueError(
                f"Itens por página inválido: {v}. "
                f"Valores permitidos: {sorted(valid_options)}"
            )
        return v

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "ufs": ["SP", "RJ"],
                "data_inicial": "2025-01-01",
                "data_final": "2025-01-31",
                "status": "recebendo_proposta",
                "modalidades": [4, 5, 6, 7],
                "valor_minimo": 50000,
                "valor_maximo": 500000,
                "esferas": ["M"],
                "ordenacao": "data_desc"
            }
        }


class ResumoLicitacoes(BaseModel):
    """
    Executive summary schema for procurement search results.

    This schema will be populated by GPT-4.1-nano (Issue #14) or
    fallback mechanism (Issue #15). For now, it defines the structure
    that the LLM module must adhere to.

    Fields:
        resumo_executivo: Brief 1-2 sentence summary
        total_oportunidades: Count of filtered procurement opportunities
        valor_total: Sum of all bid values in BRL
        destaques: List of 2-5 key highlights (e.g., "3 urgente opportunities")
        alerta_urgencia: Optional alert for time-sensitive bids
    """

    resumo_executivo: str = Field(
        ...,
        description="1-2 sentence executive summary",
        examples=[
            "Encontradas 15 licitações de uniformes em SP e RJ, totalizando R$ 2.3M."
        ],
    )
    total_oportunidades: int = Field(
        ..., ge=0, description="Number of procurement opportunities found"
    )
    valor_total: float = Field(
        ..., ge=0.0, description="Total value of all opportunities in BRL"
    )
    destaques: List[str] = Field(
        default_factory=list,
        description="Key highlights (2-5 bullet points)",
        examples=[["3 licitações com prazo até 48h", "Maior valor: R$ 500k em SP"]],
    )
    alerta_urgencia: Optional[str] = Field(
        default=None,
        description="Optional urgency alert for time-sensitive opportunities",
        examples=["⚠️ 5 licitações encerram em 24 horas"],
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "resumo_executivo": "Encontradas 15 licitações de uniformes em SP e RJ.",
                "total_oportunidades": 15,
                "valor_total": 2300000.00,
                "destaques": [
                    "3 licitações com prazo até 48h",
                    "Maior valor: R$ 500k em SP",
                ],
                "alerta_urgencia": "⚠️ 5 licitações encerram em 24 horas",
            }
        }


class Recomendacao(BaseModel):
    """
    Actionable recommendation for a specific procurement opportunity.

    Generated by the LLM consultant or heuristic fallback.
    Each recommendation includes a concrete action and justification.
    """

    oportunidade: str = Field(
        ...,
        description="Opportunity name (agency/object)",
        examples=["Prefeitura de Porto Alegre - Uniformes Escolares"],
    )
    valor: float = Field(
        ...,
        ge=0.0,
        description="Estimated value in BRL",
    )
    urgencia: Literal["alta", "media", "baixa"] = Field(
        ...,
        description="Urgency level: alta (<3 days), media (3-7 days), baixa (>7 days)",
    )
    acao_sugerida: str = Field(
        ...,
        description="Concrete suggested action",
        examples=["Prepare documentação até 17/02. Prazo final para propostas em 3 dias."],
    )
    justificativa: str = Field(
        ...,
        description="Why this opportunity is relevant",
        examples=["Valor compatível com seu porte, órgão federal com bom histórico de pagamento."],
    )


class ResumoEstrategico(ResumoLicitacoes):
    """
    Strategic executive summary with actionable recommendations.

    Extends ResumoLicitacoes for backward compatibility — all original fields
    (resumo_executivo, total_oportunidades, valor_total, destaques, alerta_urgencia)
    remain present. New fields provide actionable intelligence.

    Fields:
        recomendacoes: Prioritized list of recommended opportunities with actions
        alertas_urgencia: Multiple urgency alerts (replaces single alerta_urgencia)
        insight_setorial: Sector-level market context and trends
    """

    recomendacoes: List[Recomendacao] = Field(
        default_factory=list,
        description="Prioritized list of recommended opportunities with concrete actions",
    )
    alertas_urgencia: List[str] = Field(
        default_factory=list,
        description="Multiple urgency alerts for time-sensitive opportunities",
        examples=[["⚠️ 2 licitações encerram em 48h", "📋 3 editais exigem certidão atualizada"]],
    )
    insight_setorial: str = Field(
        default="",
        description="Sector-level market context and trend insight",
        examples=["Este mês há 20% mais oportunidades de vestuário que o mês anterior no RS."],
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "resumo_executivo": "Encontradas 15 licitações de vestuário em SP e RJ, totalizando R$ 2.3M. Recomendamos atenção imediata a 3 oportunidades com prazo curto.",
                "total_oportunidades": 15,
                "valor_total": 2300000.00,
                "destaques": [
                    "3 licitações encerram em menos de 72h",
                    "Maior valor: R$ 500k em SP",
                ],
                "alerta_urgencia": "⚠️ 5 licitações encerram em 24 horas",
                "recomendacoes": [
                    {
                        "oportunidade": "Prefeitura de São Paulo - Uniformes Escolares",
                        "valor": 500000.00,
                        "urgencia": "alta",
                        "acao_sugerida": "Prepare documentação até 16/02. Exige certidão negativa atualizada.",
                        "justificativa": "Maior valor do lote, órgão municipal com bom histórico de pagamento.",
                    }
                ],
                "alertas_urgencia": [
                    "⚠️ 2 licitações encerram em 48h — ação imediata necessária",
                    "📋 Edital de SP exige certidão FGTS atualizada (verificar validade)",
                ],
                "insight_setorial": "O setor de vestuário apresenta 15 oportunidades esta semana, 25% acima da média mensal. Concentração em SP e RJ sugere demanda sazonal por uniformes escolares.",
            }
        }


class FilterStats(BaseModel):
    """Statistics about filter rejection reasons."""

    rejeitadas_uf: int = Field(default=0, description="Rejected by UF filter")
    rejeitadas_valor: int = Field(default=0, description="Rejected by value range")
    rejeitadas_keyword: int = Field(default=0, description="Rejected by keyword match (zero matches)")
    rejeitadas_min_match: int = Field(default=0, description="Rejected by minimum match floor (had matches but below threshold)")
    rejeitadas_prazo: int = Field(default=0, description="Rejected by deadline")
    rejeitadas_outros: int = Field(default=0, description="Rejected by other reasons")
    # GTM-FIX-028 AC7: LLM zero-match classification stats
    llm_zero_match_calls: int = Field(default=0, description="Number of LLM calls for zero-keyword-match bids")
    llm_zero_match_aprovadas: int = Field(default=0, description="Zero-match bids approved by LLM")
    llm_zero_match_rejeitadas: int = Field(default=0, description="Zero-match bids rejected by LLM")
    llm_zero_match_skipped_short: int = Field(default=0, description="Zero-match bids skipped due to objeto < 20 chars")
    # CRIT-057 AC2/AC4: Zero-match budget tracking
    zero_match_budget_exceeded: int = Field(default=0, description="Zero-match bids deferred due to time budget")
    # CRIT-058 AC4: Zero-match cap tracking
    zero_match_capped: bool = Field(default=False, description="Whether zero-match pool was capped")
    zero_match_cap_value: int = Field(default=200, description="Cap value applied to zero-match pool")


class SanctionsSummarySchema(BaseModel):
    """
    Lightweight sanctions summary for search result enrichment (STORY-256 AC11).

    Shown as a badge on each search result when check_sanctions=true.
    """
    is_clean: bool = Field(..., description="True if no active sanctions found")
    active_sanctions_count: int = Field(default=0, description="Number of active sanctions")
    sanction_types: List[str] = Field(
        default_factory=list,
        description="e.g. ['CEIS: Impedimento', 'CNEP: Multa']"
    )
    checked_at: Optional[str] = Field(default=None, description="ISO timestamp of check")


class LicitacaoItem(BaseModel):
    """
    Individual bid item for display in search results.

    Used for FREE tier preview feature - shows 5-10 items fully,
    rest are displayed blurred/partial without links.
    """
    pncp_id: str = Field(..., description="Unique PNCP identifier")
    objeto: str = Field(..., description="Procurement object description")
    orgao: str = Field(..., description="Government agency name")
    uf: str = Field(..., description="State code (e.g., 'SP')")
    municipio: Optional[str] = Field(default=None, description="Municipality name")
    valor: Optional[float] = Field(default=None, ge=0, description="Estimated total value in BRL. Null when source does not provide value data (e.g., PCP v2).")
    modalidade: Optional[str] = Field(default=None, description="Procurement modality")
    data_publicacao: Optional[str] = Field(default=None, description="Publication date")
    data_abertura: Optional[str] = Field(default=None, description="Proposal opening date")
    data_encerramento: Optional[str] = Field(default=None, description="Proposal submission deadline")
    dias_restantes: Optional[int] = Field(default=None, description="Days remaining until proposal deadline (negative if past)")
    urgencia: Optional[str] = Field(default=None, description="Urgency level: critica (<7d), alta (7-14d), media (14-30d), baixa (>30d), encerrada (past)")
    link: Optional[str] = Field(default=None, description="Direct link to bid source (priority: linkSistemaOrigem > constructed PNCP URL). Null when no link available (UX-400 AC2).")
    numero_compra: Optional[str] = Field(default=None, description="Procurement number (e.g., edital number). UX-400 AC5.")
    cnpj_orgao: Optional[str] = Field(default=None, description="CNPJ of the issuing government agency. UX-400 AC6.")
    source: Optional[str] = Field(default=None, alias="_source", description="Source that provided this record")
    relevance_score: Optional[float] = Field(default=None, description="Relevance score 0.0-1.0 (only when custom terms active)")
    matched_terms: Optional[List[str]] = Field(default=None, description="List of search terms that matched this bid")
    supplier_sanctions: Optional[SanctionsSummarySchema] = Field(
        default=None,
        description="Sanctions check result (only when check_sanctions=true in request)"
    )
    # GTM-FIX-028 AC8: How this bid was classified as relevant
    relevance_source: Optional[str] = Field(
        default=None,
        description="How relevance was determined: 'keyword' (density >5%), 'llm_standard' (2-5%), 'llm_conservative' (1-2%), 'llm_zero_match' (0% keyword match, LLM classified)"
    )
    # D-02 AC7: Confidence score and LLM evidence for frontend display
    confidence_score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Classification confidence 0-100%. keyword=95, llm=varies, item_inspection=85, zero_match<=70"
    )
    llm_evidence: Optional[List[str]] = Field(
        default=None,
        description="Literal text excerpts from procurement description that support the classification (max 3)"
    )
    # C-02 AC1: Categorical confidence level for frontend badge display
    confidence: Optional[Literal["high", "medium", "low"]] = Field(
        default=None,
        description="Confidence level derived from relevance_source: keyword=high, llm_standard=medium, llm_conservative/llm_zero_match=low"
    )
    # D-04 AC1: Viability assessment — orthogonal to relevance
    viability_score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Viability score 0-100 based on modalidade, timeline, value fit, and geography"
    )
    viability_level: Optional[Literal["alta", "media", "baixa"]] = Field(
        default=None,
        description="Viability level: alta (>70), media (40-70), baixa (<40)"
    )
    viability_factors: Optional[dict] = Field(
        default=None,
        description="Breakdown of viability factors: modalidade, timeline, value_fit, geography (each 0-100 with label)"
    )
    # CRIT-FLT-003 AC2: Whether bid value was reported or missing
    value_source: Optional[Literal["estimated", "missing"]] = Field(
        default=None,
        alias="_value_source",
        description="Whether the bid's estimated value was reported ('estimated') or missing ('missing')"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "pncp_id": "12345678000190-1-000001/2026",
                "objeto": "Aquisição de uniformes para funcionários",
                "orgao": "Prefeitura Municipal de São Paulo",
                "uf": "SP",
                "municipio": "São Paulo",
                "valor": 150000.00,
                "modalidade": "Pregão Eletrônico",
                "data_publicacao": "2026-02-01",
                "data_abertura": "2026-02-15",
                "link": "https://pncp.gov.br/app/editais/12345678000190/2026/1"
            }
        }


class DataSourceStatus(BaseModel):
    """
    Status information for a single data source in multi-source fetching.

    Used to provide transparency about which sources contributed to results
    and which failed/timed out during the search operation.
    """
    source: str = Field(
        ...,
        description="Data source identifier (e.g., 'pncp', 'compras_gov', 'portal')"
    )
    status: str = Field(
        ...,
        description="Source status: 'ok' (success), 'timeout' (timed out), 'error' (failed), 'skipped' (not attempted)"
    )
    records: int = Field(
        default=0,
        ge=0,
        description="Number of records successfully returned by this source"
    )


class UfStatusDetail(BaseModel):
    """Per-UF status detail for coverage indicators (GTM-RESILIENCE-A05 AC2)."""
    uf: str = Field(..., description="State code (e.g., 'SP')")
    status: Literal["ok", "timeout", "error", "skipped"] = Field(..., description="UF fetch status")
    results_count: int = Field(default=0, ge=0, description="Number of results from this UF")


class CoverageMetadata(BaseModel):
    """GTM-RESILIENCE-C03 AC1: Consolidated coverage metadata."""
    ufs_requested: List[str] = Field(..., description="UFs solicitadas pelo usuario")
    ufs_processed: List[str] = Field(..., description="UFs que retornaram dados com sucesso")
    ufs_failed: List[str] = Field(default_factory=list, description="UFs que falharam (timeout/erro)")
    coverage_pct: float = Field(..., ge=0, le=100, description="Porcentagem de cobertura (1 decimal)")
    data_timestamp: str = Field(..., description="ISO timestamp de quando dados foram obtidos")
    freshness: Literal["live", "cached_fresh", "cached_stale"] = Field(..., description="Indicador de freshness")


class BuscaResponse(BaseModel):
    """
    Response schema for /buscar endpoint.

    Returns the complete search results including:
    - AI-generated executive summary
    - Excel file as base64-encoded string (optional, based on plan)
    - Statistics about raw vs filtered results
    - Quota information for user awareness

    The Excel file can be decoded and downloaded by the frontend.
    """

    resumo: Union[ResumoEstrategico, ResumoLicitacoes] = Field(
        ..., description="Strategic executive summary with actionable recommendations (AI-generated or fallback)"
    )
    licitacoes: List[LicitacaoItem] = Field(
        default_factory=list,
        description="List of individual bids for display. FREE tier shows 5-10 fully, rest blurred."
    )
    excel_base64: Optional[str] = Field(
        default=None, description="Excel file encoded as base64 string (None if plan doesn't allow or storage used)"
    )
    download_url: Optional[str] = Field(
        default=None, description="Signed URL for direct Excel download (60min TTL, preferred over base64)"
    )
    excel_available: bool = Field(
        ..., description="Whether Excel export is available for user's plan"
    )
    quota_used: int = Field(
        ..., ge=0, description="Monthly searches used after this request"
    )
    quota_remaining: int = Field(
        ..., ge=0, description="Monthly searches remaining"
    )
    total_raw: int = Field(
        ..., ge=0, description="Total records fetched from PNCP API (before filtering)"
    )
    total_filtrado: int = Field(
        ...,
        ge=0,
        description="Records after applying filters (UF, value, keywords, deadline)",
    )
    filter_stats: Optional[FilterStats] = Field(
        default=None, description="Breakdown of filter rejection reasons"
    )
    termos_utilizados: Optional[List[str]] = Field(
        default=None,
        description="Keywords effectively used for filtering (after stopword removal)",
    )
    stopwords_removidas: Optional[List[str]] = Field(
        default=None,
        description="Stopwords stripped from user input (for transparency)",
    )
    upgrade_message: Optional[str] = Field(
        default=None,
        description="Message shown when Excel is blocked, encouraging upgrade"
    )
    sources_used: Optional[List[str]] = Field(
        default=None,
        description="List of source codes that returned data (e.g., ['PNCP', 'PORTAL_COMPRAS'])"
    )
    source_stats: Optional[List[dict]] = Field(
        default=None,
        description="Per-source fetch metrics when multi-source is active"
    )
    is_partial: bool = Field(
        default=False,
        description="True when not all configured data sources responded successfully (some timed out/failed)"
    )
    data_sources: Optional[List[DataSourceStatus]] = Field(
        default=None,
        description="Detailed status breakdown of each data source (None for backward compatibility)"
    )
    degradation_reason: Optional[str] = Field(
        default=None,
        description="Human-readable explanation of partial results (e.g., 'PNCP indisponível, resultados de fontes alternativas')"
    )
    # CRIT-053 AC1/AC4: Sources that were degraded (canary fail, 0 results due to health issues)
    sources_degraded: Optional[List[str]] = Field(
        default=None,
        description="CRIT-053: Source codes that are degraded (e.g., canary timeout). Not counted as succeeded."
    )
    # STORY-257A AC5: Partial results transparency
    failed_ufs: Optional[List[str]] = Field(
        default=None,
        description="List of UF codes that failed during fetch (timeout or error)"
    )
    succeeded_ufs: Optional[List[str]] = Field(
        default=None,
        description="List of UF codes that returned data successfully"
    )
    # GTM-FIX-004: Truncation transparency
    is_truncated: bool = Field(
        default=False,
        description="True when at least one UF hit the max_pages limit (data may be incomplete)"
    )
    truncated_ufs: Optional[List[str]] = Field(
        default=None,
        description="UF codes where results were truncated due to max_pages limit"
    )
    truncation_details: Optional[Dict[str, bool]] = Field(
        default=None,
        description="Per-source truncation flags, e.g. {'pncp': true, 'portal_compras': false}. "
                    "None when no truncation occurred (backward compatible)."
    )
    total_ufs_requested: Optional[int] = Field(
        default=None,
        description="Total number of UFs in the original request"
    )
    cached: bool = Field(
        default=False,
        description="True when results are served from cache (STORY-257A AC9)"
    )
    from_cache: bool = Field(
        default=False,
        description="GTM-INFRA-003 AC6: True when response came 100% from cache (quota was NOT consumed)"
    )
    cached_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp of when cached results were generated"
    )
    cached_sources: Optional[List[str]] = Field(
        default=None,
        description="GTM-FIX-010 AC5r: Source codes that contributed to cached data (e.g. ['PNCP','PORTAL_COMPRAS'])"
    )
    cache_status: Optional[str] = Field(
        default=None,
        description="UX-303 AC5: Cache freshness status — 'fresh' (0-6h) or 'stale' (6-24h)"
    )
    cache_level: Optional[str] = Field(
        default=None,
        description="UX-303 AC2: Which cache level served the data — 'supabase', 'redis', or 'local'"
    )
    # STORY-306 AC5: Cache fallback — serving data from different date range
    cache_fallback: bool = Field(
        default=False,
        description="STORY-306 AC5: True when serving cached data from a different date range than requested"
    )
    cache_date_range: Optional[str] = Field(
        default=None,
        description="STORY-306 AC5: Date of the cached data when cache_fallback=True (e.g. '2026-02-20')"
    )
    # GTM-RESILIENCE-A01: Semantic response state
    response_state: Literal["live", "cached", "degraded", "empty_failure", "degraded_expired"] = Field(
        default="live",
        description="Semantic state of the response: 'live' (fresh data), 'cached' (stale cache served), "
                    "'degraded' (partial data), 'empty_failure' (all sources failed, no cache), "
                    "'degraded_expired' (all sources failed, expired cache >24h served as last resort)"
    )
    # GTM-RESILIENCE-A04: Progressive delivery — indicates live fetch running in background
    live_fetch_in_progress: bool = Field(
        default=False,
        description="A-04 AC1: True when cache-first response returned and live fetch is running in background"
    )
    degradation_guidance: Optional[str] = Field(
        default=None,
        description="GTM-RESILIENCE-A01: User-facing guidance when response_state is 'empty_failure' or 'degraded'"
    )
    # GTM-RESILIENCE-A05: Coverage indicators
    coverage_pct: int = Field(
        default=100,
        ge=0,
        le=100,
        description="GTM-RESILIENCE-A05 AC1: Coverage percentage (succeeded_ufs / total_ufs_requested * 100)"
    )
    ufs_status_detail: Optional[List[UfStatusDetail]] = Field(
        default=None,
        description="GTM-RESILIENCE-A05 AC2: Per-UF status breakdown with results count"
    )
    # GTM-RESILIENCE-C03 AC1: Consolidated coverage metadata
    coverage_metadata: Optional[CoverageMetadata] = Field(
        default=None,
        description="GTM-RESILIENCE-C03: Consolidated coverage metadata for frontend display"
    )
    hidden_by_min_match: Optional[int] = Field(
        default=None,
        description="Number of bids that matched at least 1 term but were below the minimum match floor"
    )
    filter_relaxed: Optional[bool] = Field(
        default=None,
        description="True if the minimum match filter was relaxed from strict to 1 due to zero results"
    )
    ultima_atualizacao: Optional[str] = Field(
        default=None,
        description="ISO timestamp of when search results were generated"
    )
    # STORY-354 AC2: Pending review bids awaiting LLM reclassification
    pending_review_count: int = Field(
        default=0,
        ge=0,
        description="STORY-354 AC2: Number of bids awaiting AI reclassification (LLM was temporarily unavailable)"
    )
    # GTM-RESILIENCE-F01: Background job status fields
    llm_status: Optional[str] = Field(
        default=None,
        description="LLM summary status: 'ready' (inline), 'processing' (background job running), None (legacy)"
    )
    excel_status: Optional[str] = Field(
        default=None,
        description="Excel generation status: 'ready' (inline), 'processing' (background job running), "
                    "'skipped' (plan does not allow), 'failed' (job failed), None (legacy)"
    )
    # CRIT-005 AC13: LLM summary provenance
    llm_source: Optional[Literal["ai", "fallback", "processing"]] = Field(
        default=None,
        description="CRIT-005 AC13: Source of the summary — 'ai' (GPT-generated), 'fallback' (heuristic), 'processing' (in progress)"
    )
    # STORY-267 AC15: Inform frontend when min_match_floor was relaxed
    match_relaxed: bool = Field(
        default=False,
        description="STORY-267 AC15: True when min_match_floor was relaxed, enabling 'expanded matching' badge in frontend"
    )
    # GTM-STAB-005 AC3: Human-readable filter summary when results=0
    filter_summary: Optional[str] = Field(
        default=None,
        description="GTM-STAB-005 AC3: Human-readable filter summary (e.g. '3 rejeitadas por UF, 12 por keyword')"
    )
    # GTM-STAB-003 AC4: True when time budget forced simplified processing
    is_simplified: bool = Field(
        default=False,
        description="GTM-STAB-003 AC4: True when time budget forced simplified (LLM/viability skipped)"
    )
    # GTM-STAB-005 AC4: Auto-relaxation level applied when results=0
    relaxation_level: Optional[int] = Field(
        default=None,
        description="GTM-STAB-005 AC4: 0=normal, 1=no floor, 2=no density, 3=top by value"
    )
    # CRIT-059: Async zero-match background job
    zero_match_job_id: Optional[str] = Field(
        default=None,
        description="CRIT-059 AC6: Job ID for background zero-match classification (None when sync or disabled)"
    )
    zero_match_candidates_count: int = Field(
        default=0,
        ge=0,
        description="CRIT-059 AC6: Number of zero-match candidates pending background classification"
    )
    # STORY-320 AC3: Soft paywall indicators
    paywall_applied: bool = Field(
        default=False,
        description="STORY-320 AC3: True when results were truncated due to trial paywall"
    )
    total_before_paywall: Optional[int] = Field(
        default=None,
        description="STORY-320 AC3: Total results before paywall truncation (shown as 'See all N results')"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "resumo": {
                    "resumo_executivo": "Encontradas 15 licitações.",
                    "total_oportunidades": 15,
                    "valor_total": 2300000.00,
                    "destaques": ["3 urgentes"],
                    "alerta_urgencia": None,
                },
                "excel_base64": "UEsDBBQABg...",
                "excel_available": True,
                "quota_used": 24,
                "quota_remaining": 26,
                "total_raw": 523,
                "total_filtrado": 15,
                "upgrade_message": None,
                "ultima_atualizacao": "2026-02-10T14:30:00Z",
            }
        }
