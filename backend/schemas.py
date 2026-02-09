"""Pydantic schemas for API request/response validation."""

import re
from datetime import date
from enum import Enum, IntEnum
from pydantic import BaseModel, Field, model_validator, field_validator
from typing import List, Optional, Dict, Any


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
    Modalidades de contratação conforme legislação brasileira.

    Códigos padronizados pela API PNCP para tipos de licitação:
    - 1-2: Pregões (eletrônico/presencial) - mais comuns
    - 3-5: Modalidades tradicionais por valor
    - 6-7: Contratação direta
    - 8-10: Modalidades especiais
    """
    PREGAO_ELETRONICO = 1
    PREGAO_PRESENCIAL = 2
    CONCORRENCIA = 3
    TOMADA_PRECOS = 4
    CONVITE = 5
    DISPENSA = 6
    INEXIGIBILIDADE = 7
    CREDENCIAMENTO = 8
    LEILAO = 9
    DIALOGO_COMPETITIVO = 10


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
SAFE_SEARCH_PATTERN = re.compile(r'^[\w\s@.\-áéíóúàèìòùâêîôûãõñç]+$', re.IGNORECASE | re.UNICODE)


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
        description="Custom search terms separated by spaces (e.g., 'jaleco avental'). "
                    "Each space-separated word is treated as an additional keyword.",
        examples=["jaleco avental"],
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
        description="Lista de códigos de modalidade de contratação (1=Pregão Eletrônico, "
                    "2=Pregão Presencial, 3=Concorrência, 4=Tomada de Preços, 5=Convite, "
                    "6=Dispensa, 7=Inexigibilidade, 8=Credenciamento, 9=Leilão, "
                    "10=Diálogo Competitivo). None = todas as modalidades.",
        examples=[[1, 2, 6]],
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

    @field_validator('modalidades')
    @classmethod
    def validate_modalidades(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        """Validate that modalidade codes are within valid range (1-10)."""
        if v is not None:
            valid_codes = set(m.value for m in ModalidadeContratacao)
            invalid_codes = [code for code in v if code not in valid_codes]
            if invalid_codes:
                raise ValueError(
                    f"Códigos de modalidade inválidos: {invalid_codes}. "
                    f"Valores válidos: {sorted(valid_codes)}"
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
                "modalidades": [1, 2, 6],
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


class FilterStats(BaseModel):
    """Statistics about filter rejection reasons."""

    rejeitadas_uf: int = Field(default=0, description="Rejected by UF filter")
    rejeitadas_valor: int = Field(default=0, description="Rejected by value range")
    rejeitadas_keyword: int = Field(default=0, description="Rejected by keyword match")
    rejeitadas_prazo: int = Field(default=0, description="Rejected by deadline")
    rejeitadas_outros: int = Field(default=0, description="Rejected by other reasons")


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
    link: str = Field(..., description="Direct link to PNCP portal")

    class Config:
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

    resumo: ResumoLicitacoes = Field(
        ..., description="Executive summary (AI-generated or fallback)"
    )
    licitacoes: List[LicitacaoItem] = Field(
        default_factory=list,
        description="List of individual bids for display. FREE tier shows 5-10 fully, rest blurred."
    )
    excel_base64: Optional[str] = Field(
        default=None, description="Excel file encoded as base64 string (None if plan doesn't allow)"
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


class PNCPStatsResponse(BaseModel):
    """
    PNCP platform-wide statistics for landing page hero section.

    Shows real-time data about the scale of procurement opportunities
    in the PNCP system to demonstrate platform value.

    Cached for 24 hours to minimize API load while maintaining freshness.
    """
    total_bids_30d: int = Field(
        ..., ge=0, description="Total bids published in last 30 days (modalidade=6 only)"
    )
    annualized_total: int = Field(
        ..., ge=0, description="Annualized bid count projection (total_bids_30d * 365/30)"
    )
    total_value_30d: float = Field(
        ..., ge=0.0, description="Total estimated value (R$) in last 30 days"
    )
    annualized_value: float = Field(
        ..., ge=0.0, description="Annualized value projection (R$)"
    )
    total_sectors: int = Field(
        ..., ge=0, description="Number of available sectors in platform"
    )
    last_updated: str = Field(
        ..., description="ISO 8601 timestamp of last data refresh"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_bids_30d": 12500,
                "annualized_total": 152083,
                "total_value_30d": 45000000.00,
                "annualized_value": 547500000.00,
                "total_sectors": 9,
                "last_updated": "2026-02-09T14:30:00Z"
            }
        }
