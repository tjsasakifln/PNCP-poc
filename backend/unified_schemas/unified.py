"""
Unified procurement schema models for multi-source consolidation.

This module provides the canonical data models used by all source adapters
to ensure consistent data representation across different procurement portals.

Location: backend/schemas/unified.py
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Set
import hashlib
import re

from pydantic import BaseModel, Field, field_validator, model_validator


class SourceType(str, Enum):
    """
    Identifies the source portal for procurement data.

    Priority order (for conflict resolution):
    1. PNCP - Official federal portal (highest authority)
    2. PORTAL_COMPRAS - Established marketplace
    3. BLL - Major private portal
    4. BNC - Regional focus
    5. LICITAR - Newest entrant
    """
    PNCP = "PNCP"
    BLL = "BLL"
    PORTAL_COMPRAS = "PORTAL_COMPRAS"
    BNC = "BNC"
    LICITAR = "LICITAR"


class SourceStatus(str, Enum):
    """Health status of a procurement source."""
    AVAILABLE = "available"      # Fully operational
    DEGRADED = "degraded"        # Working but slow or partial
    UNAVAILABLE = "unavailable"  # Not responding


class SourceCapability(str, Enum):
    """Optional capabilities a source may support."""
    FILTER_BY_UF = "filter_by_uf"           # Server-side UF filtering
    FILTER_BY_VALUE = "filter_by_value"     # Server-side value range
    FILTER_BY_KEYWORD = "filter_by_keyword" # Server-side keyword search
    PAGINATION = "pagination"               # Supports pagination
    DATE_RANGE = "date_range"               # Supports date range queries
    REAL_TIME = "real_time"                 # Near real-time updates


# Valid Brazilian state codes
VALID_UFS: frozenset[str] = frozenset({
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
})

# Source priority for conflict resolution (lower = higher priority)
SOURCE_PRIORITY: Dict[str, int] = {
    "PNCP": 1,
    "PORTAL_COMPRAS": 2,
    "BLL": 3,
    "BNC": 4,
    "LICITAR": 5,
}


class SourceMetadata(BaseModel):
    """
    Metadata about a procurement source.

    Contains configuration and capability information for a source adapter,
    used by the consolidation service for orchestration decisions.
    """
    name: str = Field(
        ...,
        description="Human-readable source name"
    )
    code: str = Field(
        ...,
        description="Short code for logs/metrics (e.g., 'PNCP', 'BLL')"
    )
    base_url: str = Field(
        ...,
        description="API base URL"
    )
    documentation_url: Optional[str] = Field(
        default=None,
        description="Link to API documentation"
    )
    capabilities: Set[SourceCapability] = Field(
        default_factory=set,
        description="Supported capabilities"
    )
    rate_limit_rps: float = Field(
        default=10.0,
        ge=0.1,
        description="Maximum requests per second"
    )
    typical_response_ms: int = Field(
        default=500,
        ge=0,
        description="Average response time in milliseconds"
    )
    priority: int = Field(
        default=100,
        ge=1,
        description="Priority for deduplication (lower = higher priority)"
    )

    class Config:
        use_enum_values = True


class UnifiedProcurement(BaseModel):
    """
    Unified procurement record format.

    This is the canonical representation of a procurement opportunity
    across all sources. All source adapters MUST convert their
    source-specific formats to this structure.

    Examples:
        >>> from datetime import datetime
        >>> proc = UnifiedProcurement(
        ...     source_id="12345-0001-2026",
        ...     source_name="PNCP",
        ...     objeto="Aquisicao de uniformes escolares",
        ...     valor_estimado=150000.0,
        ...     orgao="Prefeitura Municipal",
        ...     cnpj_orgao="83.614.912/0001-56",
        ...     uf="SP",
        ...     municipio="Sao Paulo",
        ...     data_publicacao=datetime(2026, 1, 15, 10, 0, 0),
        ... )
    """

    # === Identification (REQUIRED) ===
    source_id: str = Field(
        ...,
        min_length=1,
        description="Original unique identifier from the source system"
    )
    source_name: str = Field(
        ...,
        description="Source adapter code (e.g., 'PNCP', 'BLL')"
    )
    dedup_key: str = Field(
        default="",
        description="Deduplication key for identifying same procurement across sources"
    )

    # === Core Fields (REQUIRED) ===
    objeto: str = Field(
        ...,
        min_length=1,
        description="Procurement object description"
    )
    valor_estimado: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated total value in BRL"
    )
    orgao: str = Field(
        ...,
        min_length=1,
        description="Name of the contracting government agency"
    )
    cnpj_orgao: str = Field(
        default="",
        description="CNPJ of the contracting agency"
    )
    uf: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Brazilian state code (2 letters)"
    )
    municipio: str = Field(
        default="",
        description="Municipality name"
    )
    data_publicacao: datetime = Field(
        ...,
        description="Date/time when the procurement was published"
    )

    # === Optional Fields ===
    data_abertura: Optional[datetime] = Field(
        default=None,
        description="Date/time when proposals can be submitted/opened"
    )
    data_encerramento: Optional[datetime] = Field(
        default=None,
        description="Deadline for proposal submission"
    )
    numero_edital: str = Field(
        default="",
        description="Procurement notice number"
    )
    ano: str = Field(
        default="",
        description="Year of the procurement process"
    )
    modalidade: str = Field(
        default="",
        description="Procurement modality (e.g., 'Pregao Eletronico')"
    )
    situacao: str = Field(
        default="",
        description="Current status (e.g., 'Publicada', 'Em andamento')"
    )
    esfera: str = Field(
        default="",
        description="Government sphere: 'F'=Federal, 'E'=Estadual, 'M'=Municipal"
    )
    poder: str = Field(
        default="",
        description="Government branch: 'E'=Executive, 'L'=Legislative, 'J'=Judiciary"
    )

    # === Links ===
    link_edital: str = Field(
        default="",
        description="Direct link to procurement notice/documents"
    )
    link_portal: str = Field(
        default="",
        description="Link to view on source portal"
    )

    # === Metadata ===
    fetched_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this record was fetched from the source"
    )
    raw_data: Optional[Dict[str, Any]] = Field(
        default=None,
        repr=False,
        description="Original raw data from source (for debugging)"
    )

    @field_validator("uf")
    @classmethod
    def validate_uf(cls, v: str) -> str:
        """Validate and normalize UF to uppercase."""
        v_upper = v.upper().strip()
        if v_upper and v_upper not in VALID_UFS:
            # Log warning but don't reject - some sources may have special codes
            pass
        return v_upper

    @model_validator(mode="after")
    def compute_dedup_key(self) -> "UnifiedProcurement":
        """Generate deduplication key if not provided."""
        if not self.dedup_key:
            self.dedup_key = self._generate_dedup_key()
        return self

    def _generate_dedup_key(self) -> str:
        """
        Generate deduplication key from record attributes.

        Format: {cnpj_clean}:{numero_edital}:{ano}
        Fallback: {cnpj_clean}:{objeto_hash}:{valor}
        """
        # Normalize CNPJ (digits only)
        cnpj_clean = re.sub(r"[^\d]", "", self.cnpj_orgao)

        # If we have numero_edital and ano, use them
        if self.numero_edital and self.ano:
            return f"{cnpj_clean}:{self.numero_edital}:{self.ano}"

        # Fallback: use objeto hash and value
        objeto_normalized = " ".join(self.objeto.lower().split())
        objeto_hash = hashlib.md5(objeto_normalized.encode()).hexdigest()[:12]
        return f"{cnpj_clean}:{objeto_hash}:{int(self.valor_estimado)}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "dedup_key": self.dedup_key,
            "objeto": self.objeto,
            "valor_estimado": self.valor_estimado,
            "orgao": self.orgao,
            "cnpj_orgao": self.cnpj_orgao,
            "uf": self.uf,
            "municipio": self.municipio,
            "data_publicacao": self.data_publicacao.isoformat() if self.data_publicacao else None,
            "data_abertura": self.data_abertura.isoformat() if self.data_abertura else None,
            "data_encerramento": self.data_encerramento.isoformat() if self.data_encerramento else None,
            "numero_edital": self.numero_edital,
            "ano": self.ano,
            "modalidade": self.modalidade,
            "situacao": self.situacao,
            "esfera": self.esfera,
            "poder": self.poder,
            "link_edital": self.link_edital,
            "link_portal": self.link_portal,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
        }

    def to_legacy_format(self) -> Dict[str, Any]:
        """
        Convert to legacy format expected by filter.py and excel.py.

        This maintains backward compatibility with existing code.
        """
        return {
            "numeroControlePNCP": self.source_id,
            "codigoCompra": self.source_id,
            "objetoCompra": self.objeto,
            "valorTotalEstimado": self.valor_estimado,
            "nomeOrgao": self.orgao,
            "cnpjOrgao": self.cnpj_orgao,
            "uf": self.uf,
            "municipio": self.municipio,
            "dataPublicacaoPncp": self.data_publicacao.isoformat() if self.data_publicacao else None,
            "dataAberturaProposta": self.data_abertura.isoformat() if self.data_abertura else None,
            "modalidadeNome": self.modalidade,
            "situacaoCompraNome": self.situacao,
            "linkSistemaOrigem": self.link_edital,
            "linkProcessoEletronico": self.link_portal,
            # Source tracking (new fields)
            "_source": self.source_name,
            "_dedup_key": self.dedup_key,
        }

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class SourceStats(BaseModel):
    """Statistics for a single source fetch operation."""
    count: int = Field(
        default=0,
        ge=0,
        description="Number of records returned"
    )
    duration_ms: int = Field(
        default=0,
        ge=0,
        description="Time taken in milliseconds"
    )
    status: SourceStatus = Field(
        default=SourceStatus.AVAILABLE,
        description="Health status at fetch time"
    )
    pages_fetched: int = Field(
        default=0,
        ge=0,
        description="Number of pages fetched (if applicable)"
    )
    rate_limited: bool = Field(
        default=False,
        description="Whether rate limiting was encountered"
    )

    class Config:
        use_enum_values = True
