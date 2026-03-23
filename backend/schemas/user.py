"""User profile, onboarding, and auth-related schemas."""

from enum import Enum
from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Any, Dict, List, Optional


class PorteEmpresa(str, Enum):
    """Company size classification (STORY-260: added MEI)."""
    MEI = "MEI"
    ME = "ME"
    EPP = "EPP"
    MEDIO = "MEDIO"
    GRANDE = "GRANDE"


class ExperienciaLicitacoes(str, Enum):
    """Procurement experience level (STORY-260: added INTERMEDIARIO)."""
    PRIMEIRA_VEZ = "PRIMEIRA_VEZ"
    INICIANTE = "INICIANTE"
    INTERMEDIARIO = "INTERMEDIARIO"
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
    # STORY-260: Expanded profile fields (all Optional for progressive profiling)
    atestados: Optional[List[str]] = Field(
        default=None,
        description="Certifications held (e.g., ['crea', 'iso_9001'])",
    )
    capacidade_funcionarios: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of employees",
    )
    faturamento_anual: Optional[float] = Field(
        default=None,
        ge=0,
        description="Annual revenue in BRL",
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


class ProfileCompletenessResponse(BaseModel):
    """STORY-260 AC3: Response for GET /v1/profile/completeness."""
    completeness_pct: int = Field(ge=0, le=100)
    total_fields: int
    filled_fields: int
    missing_fields: List[str] = Field(default_factory=list)
    next_question: Optional[str] = None
    is_complete: bool = False


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


class TourEventRequest(BaseModel):
    """Request for onboarding tour event tracking (STORY-313 AC18)."""
    tour_id: str = Field(
        ...,
        max_length=50,
        description="Tour identifier (search, results, pipeline)",
    )
    event: str = Field(
        ...,
        description="Event type: completed or skipped",
    )
    steps_seen: int = Field(
        ...,
        ge=0,
        description="Number of steps the user saw before event",
    )

    @field_validator('event')
    @classmethod
    def validate_event(cls, v: str) -> str:
        valid_events = {"completed", "skipped"}
        if v not in valid_events:
            raise ValueError(f"Invalid event: {v}. Must be one of {valid_events}")
        return v


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
        ..., description="Status: 'trial', 'active', 'expired', or 'past_due'"
    )
    is_admin: bool = Field(
        default=False, description="Whether user has admin privileges"
    )
    dunning_phase: str = Field(
        default="healthy",
        description="STORY-309: Dunning phase — healthy, active_retries, grace_period, blocked"
    )
    days_since_failure: Optional[int] = Field(
        default=None,
        description="STORY-309: Days since first payment failure (null if no failure)"
    )


class DeleteAccountResponse(BaseModel):
    """Response for DELETE /me."""
    success: bool
    message: str
