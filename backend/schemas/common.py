"""Common enums, validation functions, patterns, and base models.

Shared across all schema submodules.
"""

import re
from enum import Enum, IntEnum
from pydantic import BaseModel, Field, field_validator
from typing import Optional


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


# SYS-011 / DEBT-015: SearchErrorCode is now an alias for the project-wide
# ErrorCode enum defined in error_response.py.  All existing code that imports
# SearchErrorCode from this module continues to work unchanged.
from error_response import ErrorCode as SearchErrorCode  # noqa: F401, E402


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
