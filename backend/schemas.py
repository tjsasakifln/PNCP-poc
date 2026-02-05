"""Pydantic schemas for API request/response validation."""

import re
from datetime import date, datetime
from pydantic import BaseModel, Field, model_validator, field_validator
from typing import List, Optional, Dict, Any, Annotated


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

    Examples:
        >>> request = BuscaRequest(
        ...     ufs=["SP", "RJ"],
        ...     data_inicial="2025-01-01",
        ...     data_final="2025-01-31"
        ... )
        >>> request.ufs
        ['SP', 'RJ']
    """

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

    @model_validator(mode="after")
    def validate_dates(self) -> "BuscaRequest":
        """Validate date business logic before hitting PNCP API."""
        try:
            d_ini = date.fromisoformat(self.data_inicial)
            d_fin = date.fromisoformat(self.data_final)
        except ValueError as e:
            raise ValueError(f"Data inválida: {e}")

        if d_ini > d_fin:
            raise ValueError(
                "Data inicial deve ser anterior ou igual à data final"
            )

        return self

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "ufs": ["SP", "RJ"],
                "data_inicial": "2025-01-01",
                "data_final": "2025-01-31",
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
