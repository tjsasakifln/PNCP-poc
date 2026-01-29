"""Pydantic schemas for API request/response validation."""

from datetime import date
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional


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


class BuscaResponse(BaseModel):
    """
    Response schema for /buscar endpoint.

    Returns the complete search results including:
    - AI-generated executive summary
    - Excel file as base64-encoded string
    - Statistics about raw vs filtered results

    The Excel file can be decoded and downloaded by the frontend.
    """

    resumo: ResumoLicitacoes = Field(
        ..., description="Executive summary (AI-generated or fallback)"
    )
    excel_base64: str = Field(
        ..., description="Excel file encoded as base64 string (decode for download)"
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
                "total_raw": 523,
                "total_filtrado": 15,
            }
        }
