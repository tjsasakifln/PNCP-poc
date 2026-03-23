"""Export schemas: Google Sheets, Querido Diario extraction, sessions."""

from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Any, Dict, List, Optional


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
# Google Sheets Export Schemas (STORY-180)
# ============================================================================

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
    updated_at: str = Field(..., description="Last update timestamp (ISO 8601)")


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
