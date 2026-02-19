"""Pydantic schemas for API request/response validation."""

import re
from datetime import date
from enum import Enum, IntEnum
from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Any, Dict, List, Literal, Optional


# ============================================================================
# Enums for Filter Options (P0/P1 Features)
# ============================================================================

class StatusLicitacao(str, Enum):
    """
    Status da licitação para filtro de busca.

    Define o estágio atual do processo licitatório:
    - RECEBENDO_PROPOSTA: Licitações abertas para envio de propostas (padrão)
    - EM_JULGAMENTO: Propostas encerradas, em análise pelo órgão
    - ENCERRADA: Processo finalizado (com ou sem vencedor)
    - TODOS: Sem filtro de status (retorna todas)
    """
    RECEBENDO_PROPOSTA = "recebendo_proposta"
    EM_JULGAMENTO = "em_julgamento"
    ENCERRADA = "encerrada"
    TODOS = "todos"


class ModalidadeContratacao(IntEnum):
    """
    Modalidades de contratação mapeadas pelos códigos reais da API PNCP.

    Fonte: https://pncp.gov.br/api/pncp/v1/modalidades
    Os códigos abaixo correspondem ao campo codigoModalidadeContratacao
    retornado pela API PNCP.

    EXCLUÍDAS: 9 (Inexigibilidade) e 14 (Inaplicabilidade) — modalidades
    com vencedor pré-definido, sem valor competitivo para o usuário.
    """
    LEILAO_ELETRONICO = 1       # Leilão - Eletrônico
    DIALOGO_COMPETITIVO = 2     # Diálogo Competitivo
    CONCURSO = 3                # Concurso
    CONCORRENCIA_ELETRONICA = 4 # Concorrência - Eletrônica
    CONCORRENCIA_PRESENCIAL = 5 # Concorrência - Presencial
    PREGAO_ELETRONICO = 6       # Pregão - Eletrônico
    PREGAO_PRESENCIAL = 7       # Pregão - Presencial
    DISPENSA = 8                # Dispensa de Licitação
    MANIFESTACAO_INTERESSE = 10 # Manifestação de Interesse
    PRE_QUALIFICACAO = 11       # Pré-qualificação
    CREDENCIAMENTO = 12         # Credenciamento
    LEILAO_PRESENCIAL = 13      # Leilão - Presencial
    CHAMADA_PUBLICA = 15        # Chamada Pública


class EsferaGovernamental(str, Enum):
    """
    Esfera governamental para filtro de busca.

    Define o nível de governo do órgão contratante:
    - FEDERAL (F): União, ministérios, autarquias federais
    - ESTADUAL (E): Estados, DF, secretarias estaduais
    - MUNICIPAL (M): Prefeituras, câmaras municipais
    """
    FEDERAL = "F"
    ESTADUAL = "E"
    MUNICIPAL = "M"


# ============================================================================
# Secure ID Validation (Issue #203 - P0 Security Fix)
# ============================================================================

# UUID v4 regex pattern (Supabase uses UUID v4 for user IDs)
UUID_V4_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
    re.IGNORECASE
)

# Plan ID pattern: alphanumeric with underscores, 1-50 chars
PLAN_ID_PATTERN = re.compile(r'^[a-z][a-z0-9_]{0,49}$', re.IGNORECASE)

# Search query sanitization - allows alphanumeric, spaces, accents, common punctuation
# NI-1: Updated to allow commas (phrase delimiter), parentheses, +, quotes for AC1.5 edge cases
# Note: $ deliberately excluded (command substitution risk). Currency like R$ handled by parser.
SAFE_SEARCH_PATTERN = re.compile(r'^[\w\s@.\-áéíóúàèìòùâêîôûãõñç,()+\'"]+$', re.IGNORECASE | re.UNICODE)


def validate_uuid(value: str, field_name: str = "id") -> str:
    """
    Validate that a string is a valid UUID v4 format.

    Args:
        value: The string to validate
        field_name: Name of the field for error messages

    Returns:
        The validated UUID string (lowercase normalized)

    Raises:
        ValueError: If the value is not a valid UUID v4
    """
    if not value:
        raise ValueError(f"{field_name} cannot be empty")

    value = str(value).strip().lower()

    if not UUID_V4_PATTERN.match(value):
        raise ValueError(
            f"Invalid {field_name} format. Expected UUID v4 format "
            f"(e.g., '550e8400-e29b-41d4-a716-446655440000')"
        )

    return value


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password against security policy.

    STORY-226 AC17: Enforce minimum password requirements:
    - At least 8 characters
    - At least 1 uppercase letter
    - At least 1 digit

    Args:
        password: The password string to validate.

    Returns:
        Tuple of (is_valid, error_message).
        If valid, error_message is an empty string.
        If invalid, error_message is in Portuguese.

    Examples:
        >>> validate_password("Abc12345")
        (True, "")
        >>> validate_password("abc")
        (False, "A senha deve ter pelo menos 8 caracteres.")
        >>> validate_password("abcdefgh")
        (False, "A senha deve conter pelo menos 1 letra maiúscula.")
        >>> validate_password("Abcdefgh")
        (False, "A senha deve conter pelo menos 1 dígito.")
    """
    if len(password) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres."
    if not re.search(r"[A-Z]", password):
        return False, "A senha deve conter pelo menos 1 letra maiúscula."
    if not re.search(r"\d", password):
        return False, "A senha deve conter pelo menos 1 dígito."
    return True, ""


def validate_plan_id(value: str) -> str:
    """
    Validate that a string is a valid plan ID.

    Args:
        value: The plan ID to validate

    Returns:
        The validated plan ID string (lowercase)

    Raises:
        ValueError: If the value is not a valid plan ID format
    """
    if not value:
        raise ValueError("plan_id cannot be empty")

    value = str(value).strip().lower()

    if len(value) > 50:
        raise ValueError("plan_id cannot exceed 50 characters")

    if not PLAN_ID_PATTERN.match(value):
        raise ValueError(
            "Invalid plan_id format. Expected alphanumeric with underscores, "
            "starting with a letter (e.g., 'free_trial', 'pack_10')"
        )

    return value


def sanitize_search_query(value: str, max_length: int = 100) -> str:
    """
    Sanitize a search query to prevent SQL injection and other attacks.

    Args:
        value: The search query to sanitize
        max_length: Maximum allowed length (default 100)

    Returns:
        The sanitized search query

    Raises:
        ValueError: If the query contains invalid characters
    """
    if not value:
        return ""

    value = str(value).strip()

    if len(value) > max_length:
        raise ValueError(f"Search query cannot exceed {max_length} characters")

    if not SAFE_SEARCH_PATTERN.match(value):
        raise ValueError(
            "Search query contains invalid characters. "
            "Only letters, numbers, spaces, and common punctuation are allowed."
        )

    # Escape SQL-like patterns used in ilike queries
    value = value.replace('%', '').replace('_', ' ')

    return value


class SecureUserId(BaseModel):
    """Pydantic model for secure user ID validation."""
    user_id: str

    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        return validate_uuid(v, "user_id")


class SecurePlanId(BaseModel):
    """Pydantic model for secure plan ID validation."""
    plan_id: str

    @field_validator('plan_id')
    @classmethod
    def validate_plan_id_field(cls, v: str) -> str:
        return validate_plan_id(v)


# Error codes for standardized error handling
ERROR_CODES = {
    "TRIAL_EXPIRED": "trial_expired",
    "QUOTA_EXHAUSTED": "quota_exhausted",
    "RATE_LIMIT_EXCEEDED": "rate_limit_exceeded",
    "DATE_RANGE_EXCEEDED": "date_range_exceeded",
    "EXCEL_NOT_ALLOWED": "excel_not_allowed",
}


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
            'prazo_asc', 'relevancia'
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
    valor: float = Field(..., ge=0, description="Estimated total value in BRL")
    modalidade: Optional[str] = Field(default=None, description="Procurement modality")
    data_publicacao: Optional[str] = Field(default=None, description="Publication date")
    data_abertura: Optional[str] = Field(default=None, description="Proposal opening date")
    data_encerramento: Optional[str] = Field(default=None, description="Proposal submission deadline")
    dias_restantes: Optional[int] = Field(default=None, description="Days remaining until proposal deadline (negative if past)")
    urgencia: Optional[str] = Field(default=None, description="Urgency level: critica (<7d), alta (7-14d), media (14-30d), baixa (>30d), encerrada (past)")
    link: str = Field(..., description="Direct link to PNCP portal")
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

    resumo: ResumoEstrategico = Field(
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
    # GTM-RESILIENCE-A01: Semantic response state
    response_state: Literal["live", "cached", "degraded", "empty_failure"] = Field(
        default="live",
        description="Semantic state of the response: 'live' (fresh data), 'cached' (stale cache served), "
                    "'degraded' (partial data), 'empty_failure' (all sources failed, no cache)"
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


class ErrorDetail(BaseModel):
    """
    Standardized error response with upgrade guidance.

    Used for 403 (Forbidden) and 429 (Too Many Requests) errors to provide
    clear user feedback and contextual upgrade suggestions.
    """
    message: str = Field(..., description="Human-readable error message")
    error_code: str = Field(..., description="Machine-readable error code")
    upgrade_cta: Optional[str] = Field(
        default=None, description="Call-to-action text for upgrade button"
    )
    suggested_plan: Optional[str] = Field(
        default=None, description="Plan ID to suggest (e.g., 'maquina')"
    )
    suggested_plan_name: Optional[str] = Field(
        default=None, description="Human-readable plan name"
    )
    suggested_plan_price: Optional[str] = Field(
        default=None, description="Plan price (e.g., 'R$ 597/mês')"
    )
    retry_after: Optional[int] = Field(
        default=None, description="Seconds to wait before retry (for 429 errors)"
    )


# ============================================================================
# InMail Messaging Schemas
# ============================================================================

class ConversationCategory(str, Enum):
    """Category for support conversations."""
    SUPORTE = "suporte"
    SUGESTAO = "sugestao"
    FUNCIONALIDADE = "funcionalidade"
    BUG = "bug"
    OUTRO = "outro"


class ConversationStatus(str, Enum):
    """Status of a support conversation."""
    ABERTO = "aberto"
    RESPONDIDO = "respondido"
    RESOLVIDO = "resolvido"


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation with first message."""
    subject: str = Field(..., min_length=1, max_length=200)
    category: ConversationCategory
    body: str = Field(..., min_length=1, max_length=5000)


class ReplyRequest(BaseModel):
    """Request to reply to a conversation."""
    body: str = Field(..., min_length=1, max_length=5000)


class UpdateConversationStatusRequest(BaseModel):
    """Request to update conversation status (admin only)."""
    status: ConversationStatus


class MessageResponse(BaseModel):
    """Single message in a conversation thread."""
    id: str
    sender_id: str
    sender_email: Optional[str] = None
    body: str
    is_admin_reply: bool
    read_by_user: bool
    read_by_admin: bool
    created_at: str


class ConversationSummary(BaseModel):
    """Summary of a conversation for list views."""
    id: str
    user_id: str
    user_email: Optional[str] = None
    subject: str
    category: str
    status: str
    last_message_at: str
    created_at: str
    unread_count: int = 0


class ConversationDetail(BaseModel):
    """Full conversation with messages thread."""
    id: str
    user_id: str
    user_email: Optional[str] = None
    subject: str
    category: str
    status: str
    last_message_at: str
    created_at: str
    messages: List[MessageResponse] = []


class ConversationsListResponse(BaseModel):
    """Paginated list of conversations."""
    conversations: List[ConversationSummary]
    total: int


class UnreadCountResponse(BaseModel):
    """Unread message count for badge display."""
    unread_count: int


# ============================================================================
# Profile Context Schemas (STORY-247: Onboarding Profundo)
# ============================================================================

class PorteEmpresa(str, Enum):
    """Company size classification."""
    ME = "ME"
    EPP = "EPP"
    MEDIO = "MEDIO"
    GRANDE = "GRANDE"


class ExperienciaLicitacoes(str, Enum):
    """Procurement experience level."""
    PRIMEIRA_VEZ = "PRIMEIRA_VEZ"
    INICIANTE = "INICIANTE"
    EXPERIENTE = "EXPERIENTE"


class PerfilContexto(BaseModel):
    """
    Business context profile collected during onboarding wizard.

    Used to personalize search defaults and LLM recommendations.
    Stored as JSONB in profiles.context_data.
    """
    ufs_atuacao: List[str] = Field(
        ...,
        min_length=1,
        max_length=27,
        description="States where the company operates (e.g., ['SP', 'RJ', 'MG'])",
        examples=[["SP", "RJ"]],
    )
    porte_empresa: PorteEmpresa = Field(
        ...,
        description="Company size: ME, EPP, MEDIO, GRANDE",
    )
    experiencia_licitacoes: ExperienciaLicitacoes = Field(
        ...,
        description="Procurement experience level",
    )
    faixa_valor_min: Optional[float] = Field(
        default=None,
        ge=0,
        description="Minimum contract value of interest (BRL)",
    )
    faixa_valor_max: Optional[float] = Field(
        default=None,
        ge=0,
        description="Maximum contract value of interest (BRL)",
    )
    modalidades_interesse: Optional[List[int]] = Field(
        default=None,
        description="Preferred procurement modality codes (PNCP API codes)",
    )
    palavras_chave: Optional[List[str]] = Field(
        default=None,
        max_length=20,
        description="Business-specific keywords for relevance boosting",
    )
    # GTM-004: Strategic onboarding fields
    cnae: Optional[str] = Field(
        default=None,
        max_length=20,
        description="CNAE code or business segment (e.g., '4781-4/00')",
    )
    objetivo_principal: Optional[str] = Field(
        default=None,
        max_length=200,
        description="User's primary objective in free text",
    )
    ticket_medio_desejado: Optional[int] = Field(
        default=None,
        ge=0,
        description="Desired average ticket in BRL cents",
    )

    @model_validator(mode="after")
    def validate_value_range(self) -> "PerfilContexto":
        """Ensure faixa_valor_max >= faixa_valor_min when both provided."""
        if self.faixa_valor_min is not None and self.faixa_valor_max is not None:
            if self.faixa_valor_max < self.faixa_valor_min:
                raise ValueError(
                    "faixa_valor_max deve ser maior ou igual a faixa_valor_min"
                )
        return self

    @field_validator('ufs_atuacao')
    @classmethod
    def validate_ufs(cls, v: List[str]) -> List[str]:
        """Validate that all UFs are valid Brazilian state codes."""
        valid_ufs = {
            "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
            "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
            "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
        }
        invalid = [uf for uf in v if uf.upper() not in valid_ufs]
        if invalid:
            raise ValueError(f"UFs inválidas: {invalid}")
        return [uf.upper() for uf in v]

    @field_validator('palavras_chave')
    @classmethod
    def validate_palavras_chave(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate keyword list."""
        if v is None:
            return v
        # Strip whitespace and remove empties
        cleaned = [kw.strip() for kw in v if kw.strip()]
        if len(cleaned) > 20:
            raise ValueError("Máximo de 20 palavras-chave permitidas")
        return cleaned


class PerfilContextoResponse(BaseModel):
    """Response for GET /v1/profile/context."""
    context_data: dict = Field(
        default_factory=dict,
        description="Business context data from onboarding",
    )
    completed: bool = Field(
        default=False,
        description="Whether onboarding wizard has been completed",
    )


class FirstAnalysisRequest(BaseModel):
    """Request for automatic first analysis after onboarding (GTM-004 AC1)."""
    cnae: str = Field(
        ...,
        max_length=20,
        description="CNAE code or business segment text",
    )
    objetivo_principal: str = Field(
        default="",
        max_length=200,
        description="User's primary objective",
    )
    ufs: List[str] = Field(
        ...,
        min_length=1,
        max_length=27,
        description="States of operation",
    )
    faixa_valor_min: Optional[int] = Field(
        default=None,
        ge=0,
        description="Min contract value in BRL (not cents)",
    )
    faixa_valor_max: Optional[int] = Field(
        default=None,
        ge=0,
        description="Max contract value in BRL (not cents)",
    )

    @field_validator('ufs')
    @classmethod
    def validate_ufs(cls, v: List[str]) -> List[str]:
        valid_ufs = {
            "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
            "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
            "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
        }
        invalid = [uf for uf in v if uf.upper() not in valid_ufs]
        if invalid:
            raise ValueError(f"UFs inválidas: {invalid}")
        return [uf.upper() for uf in v]


class FirstAnalysisResponse(BaseModel):
    """Response from first analysis endpoint (GTM-004 AC3)."""
    search_id: str = Field(
        ...,
        description="UUID for tracking search progress via SSE",
    )
    status: str = Field(
        default="in_progress",
        description="Search status",
    )
    message: str = Field(
        default="",
        description="User-facing status message",
    )
    setor_id: str = Field(
        default="vestuario",
        description="Resolved sector ID from CNAE mapping",
    )


class UserProfileResponse(BaseModel):
    """
    User profile with plan capabilities and quota status.

    Returned by /api/me endpoint to provide frontend with all
    necessary plan information for UI rendering.
    """
    user_id: str
    email: str
    plan_id: str = Field(..., description="Plan ID (e.g., 'consultor_agil')")
    plan_name: str = Field(..., description="Display name (e.g., 'Consultor Ágil')")
    capabilities: Dict[str, Any] = Field(
        ..., description="Plan capabilities (max_history_days, allow_excel, etc.)"
    )
    quota_used: int = Field(..., ge=0, description="Searches used this month")
    quota_remaining: int = Field(..., ge=0, description="Searches remaining this month")
    quota_reset_date: str = Field(
        ..., description="ISO 8601 timestamp of next quota reset"
    )
    trial_expires_at: Optional[str] = Field(
        default=None, description="ISO 8601 timestamp when trial expires (if applicable)"
    )
    subscription_status: str = Field(
        ..., description="Status: 'trial', 'active', or 'expired'"
    )
    is_admin: bool = Field(
        default=False, description="Whether user has admin privileges"
    )


# ============================================================================
# Google Sheets Export Schemas (STORY-180)
# ============================================================================

# ============================================================================
# Generic Response Models (STORY-222: OpenAPI contract stabilization)
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response for simple operations."""
    success: bool


class SuccessMessageResponse(BaseModel):
    """Success response with message."""
    success: bool
    message: str


class StatusResponse(BaseModel):
    """Generic status response."""
    status: str


# ============================================================================
# Main App Endpoint Response Models (STORY-222)
# ============================================================================

class RootResponse(BaseModel):
    """Response for GET / root endpoint."""
    name: str
    version: str
    api_version: str
    description: str
    endpoints: Dict[str, str]
    versioning: Dict[str, Any]
    status: str


class RedisMetrics(BaseModel):
    """Redis health metrics (B-04 AC8)."""
    connected: bool = False
    latency_ms: Optional[float] = None
    memory_used_mb: Optional[float] = None


class HealthDependencies(BaseModel):
    """Health check dependency statuses."""
    supabase: str
    openai: str
    redis: str
    redis_metrics: Optional[RedisMetrics] = None


class HealthResponse(BaseModel):
    """Response for GET /health endpoint."""
    status: str
    timestamp: str
    version: str
    dependencies: HealthDependencies
    sources: Optional[Dict[str, Any]] = None  # AC27 + B-06: Per-source health status (str or dict)


class SourceInfo(BaseModel):
    """Individual data source health info."""
    code: str
    name: str
    enabled: bool
    priority: int
    status: Optional[str] = None
    response_ms: Optional[int] = None


class SourcesHealthResponse(BaseModel):
    """Response for GET /sources/health endpoint."""
    sources: List[SourceInfo]
    multi_source_enabled: bool
    total_enabled: int
    total_available: int
    checked_at: str


class SetoresResponse(BaseModel):
    """Response for GET /setores endpoint."""
    setores: List[Dict[str, Any]]


class DebugPNCPResponse(BaseModel):
    """Response for GET /debug/pncp-test endpoint."""
    success: bool
    total_registros: Optional[int] = None
    items_returned: Optional[int] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    elapsed_ms: int


# ============================================================================
# Billing Response Models (STORY-222)
# ============================================================================

class BillingPlansResponse(BaseModel):
    """Response for GET /plans (billing.py)."""
    plans: List[Dict[str, Any]]


class CheckoutResponse(BaseModel):
    """Response for POST /checkout."""
    checkout_url: str


# ============================================================================
# Sessions Response Model (STORY-222)
# ============================================================================

class SessionsListResponse(BaseModel):
    """Response for GET /sessions."""
    sessions: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


# ============================================================================
# Messages Response Models — missing ones (STORY-222)
# ============================================================================

class CreateConversationResponse(BaseModel):
    """Response for POST /api/messages/conversations."""
    id: str
    status: str


class ReplyStatusResponse(BaseModel):
    """Response for POST /api/messages/conversations/{id}/reply."""
    status: str


# ============================================================================
# User Response Models (STORY-222)
# ============================================================================

class DeleteAccountResponse(BaseModel):
    """Response for DELETE /me."""
    success: bool
    message: str


# ============================================================================
# Admin Response Models (STORY-222)
# ============================================================================

class AdminUsersListResponse(BaseModel):
    """Response for GET /admin/users."""
    users: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


class AdminCreateUserResponse(BaseModel):
    """Response for POST /admin/users."""
    user_id: str
    email: str
    plan_id: Optional[str] = None


class AdminDeleteUserResponse(BaseModel):
    """Response for DELETE /admin/users/{user_id}."""
    deleted: bool
    user_id: str


class AdminUpdateUserResponse(BaseModel):
    """Response for PUT /admin/users/{user_id}."""
    updated: bool
    user_id: str


class AdminResetPasswordResponse(BaseModel):
    """Response for POST /admin/users/{user_id}/reset-password."""
    success: bool
    user_id: str


class AdminAssignPlanResponse(BaseModel):
    """Response for POST /admin/users/{user_id}/assign-plan."""
    assigned: bool
    user_id: str
    plan_id: str


class AdminUpdateCreditsResponse(BaseModel):
    """Response for PUT /admin/users/{user_id}/credits."""
    success: bool
    user_id: str
    credits: int
    previous_credits: Optional[int] = None
    subscription_created: Optional[bool] = None


class GoogleSheetsExportRequest(BaseModel):
    """
    Request schema for Google Sheets export endpoint.

    Supports both "create new spreadsheet" and "update existing" modes.
    """
    licitacoes: List[Dict[str, Any]] = Field(
        ...,
        description="List of procurement contracts to export",
        min_length=1,
        max_length=10000,  # Google Sheets practical limit
    )
    title: str = Field(
        ...,
        description="Spreadsheet title",
        min_length=1,
        max_length=100,
    )
    mode: str = Field(
        default="create",
        description="'create' for new spreadsheet, 'update' for existing",
        pattern="^(create|update)$"
    )
    spreadsheet_id: Optional[str] = Field(
        default=None,
        description="Google Sheets spreadsheet ID (required for mode='update')",
        pattern=r'^[a-zA-Z0-9_-]{44}$',  # Google Sheets ID format
    )

    @model_validator(mode="after")
    def validate_update_mode(self) -> "GoogleSheetsExportRequest":
        """Ensure spreadsheet_id is provided when mode='update'."""
        if self.mode == "update" and not self.spreadsheet_id:
            raise ValueError(
                "spreadsheet_id is required when mode='update'. "
                "Provide the Google Sheets ID from the URL: "
                "docs.google.com/spreadsheets/d/{spreadsheet_id}"
            )
        return self

    @field_validator('licitacoes')
    @classmethod
    def validate_row_limit(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Warn if exceeding Google Sheets practical row limit."""
        if len(v) > 10000:
            raise ValueError(
                f"Export too large: {len(v)} rows. "
                "Google Sheets supports max 10,000 rows per export. "
                "Please filter your search to reduce result count."
            )
        return v


class GoogleSheetsExportResponse(BaseModel):
    """Response schema for successful Google Sheets export."""
    success: bool = Field(
        default=True,
        description="Export success indicator"
    )
    spreadsheet_id: str = Field(
        ...,
        description="Google Sheets spreadsheet ID",
    )
    spreadsheet_url: str = Field(
        ...,
        description="Full shareable URL to the spreadsheet",
    )
    total_rows: int = Field(
        ...,
        description="Number of contracts exported",
        ge=0
    )
    updated_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp (only for mode='update')",
    )


class GoogleSheetsExportHistory(BaseModel):
    """Schema for individual export history entry."""
    id: str = Field(..., description="Export record UUID")
    spreadsheet_id: str = Field(..., description="Google Sheets spreadsheet ID")
    spreadsheet_url: str = Field(..., description="Shareable URL")
    search_params: Dict[str, Any] = Field(..., description="Search parameters snapshot")
    total_rows: int = Field(..., description="Number of rows exported")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    last_updated_at: str = Field(..., description="Last update timestamp (ISO 8601)")


class GoogleSheetsExportHistoryResponse(BaseModel):
    """Response schema for export history endpoint."""
    exports: List[GoogleSheetsExportHistory] = Field(
        ...,
        description="List of user's Google Sheets exports"
    )
    total: int = Field(
        ...,
        description="Total number of exports in history",
        ge=0
    )


# ============================================================================
# Pipeline Schemas (STORY-250: Gestão de Pipeline de Oportunidades)
# ============================================================================

VALID_PIPELINE_STAGES = {"descoberta", "analise", "preparando", "enviada", "resultado"}

PIPELINE_STAGE_LABELS = {
    "descoberta": "Descoberta",
    "analise": "Em Análise",
    "preparando": "Preparando Proposta",
    "enviada": "Enviada",
    "resultado": "Resultado",
}


class PipelineItemCreate(BaseModel):
    """Request to add an item to the pipeline."""
    pncp_id: str = Field(..., min_length=1, max_length=100, description="PNCP unique identifier")
    objeto: str = Field(..., min_length=1, max_length=2000, description="Procurement object description")
    orgao: Optional[str] = Field(default=None, max_length=500, description="Government agency name")
    uf: Optional[str] = Field(default=None, max_length=2, description="State code")
    valor_estimado: Optional[float] = Field(default=None, ge=0, description="Estimated value in BRL")
    data_encerramento: Optional[str] = Field(default=None, description="Deadline ISO timestamp")
    link_pncp: Optional[str] = Field(default=None, max_length=500, description="Direct PNCP link")
    stage: Optional[str] = Field(default="descoberta", description="Initial pipeline stage")
    notes: Optional[str] = Field(default=None, max_length=5000, description="User notes")

    @field_validator('stage')
    @classmethod
    def validate_stage(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_PIPELINE_STAGES:
            raise ValueError(f"Stage inválido: '{v}'. Valores válidos: {sorted(VALID_PIPELINE_STAGES)}")
        return v


class PipelineItemUpdate(BaseModel):
    """Request to update a pipeline item (stage and/or notes)."""
    stage: Optional[str] = Field(default=None, description="New pipeline stage")
    notes: Optional[str] = Field(default=None, max_length=5000, description="Updated notes")

    @field_validator('stage')
    @classmethod
    def validate_stage(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_PIPELINE_STAGES:
            raise ValueError(f"Stage inválido: '{v}'. Valores válidos: {sorted(VALID_PIPELINE_STAGES)}")
        return v


class PipelineItemResponse(BaseModel):
    """Single pipeline item response."""
    id: str
    user_id: str
    pncp_id: str
    objeto: str
    orgao: Optional[str] = None
    uf: Optional[str] = None
    valor_estimado: Optional[float] = None
    data_encerramento: Optional[str] = None
    link_pncp: Optional[str] = None
    stage: str
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class PipelineListResponse(BaseModel):
    """Paginated list of pipeline items."""
    items: List[PipelineItemResponse]
    total: int
    limit: int
    offset: int


class PipelineAlertsResponse(BaseModel):
    """Pipeline items with approaching deadlines."""
    items: List[PipelineItemResponse]
    total: int


# ============================================================================
# Querido Diario Extraction Schemas (STORY-255)
# ============================================================================

class ExtractedProcurement(BaseModel):
    """
    Structured procurement data extracted from gazette text via LLM or regex.

    Used by the Querido Diario adapter to convert unstructured gazette text
    into structured procurement records.
    """
    modality: Optional[str] = Field(
        default=None,
        description="Procurement modality (e.g., 'Pregao Eletronico', 'Concorrencia')"
    )
    number: Optional[str] = Field(
        default=None,
        description="Procurement number (e.g., '023/2026')"
    )
    object_description: str = Field(
        ...,
        description="Description of the procurement object"
    )
    estimated_value: Optional[float] = Field(
        default=None,
        ge=0,
        description="Estimated value in BRL (e.g., 450000.0)"
    )
    opening_date: Optional[str] = Field(
        default=None,
        description="Opening date in YYYY-MM-DD format"
    )
    agency_name: Optional[str] = Field(
        default=None,
        description="Name of the contracting agency/municipality"
    )
    municipality: str = Field(
        ...,
        description="Municipality name (from territory_name)"
    )
    uf: str = Field(
        ...,
        description="State code (from state_code)"
    )
    source_url: str = Field(
        ...,
        description="URL to the gazette text/PDF"
    )
    gazette_date: str = Field(
        ...,
        description="Publication date of the gazette (YYYY-MM-DD)"
    )
    extraction_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence score of the extraction (0-1)"
    )
    raw_excerpt: str = Field(
        default="",
        description="Original text excerpt that was extracted from"
    )
