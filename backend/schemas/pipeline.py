"""Pipeline (kanban) schemas."""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


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
    search_id: Optional[str] = Field(default=None, max_length=100, description="Search session that discovered this item (DEBT-120)")

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
    version: Optional[int] = Field(default=None, description="Current version for optimistic locking (STORY-307)")

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
    search_id: Optional[str] = None
    created_at: str
    updated_at: str
    version: int = 1  # STORY-307 AC12: Optimistic locking version


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
