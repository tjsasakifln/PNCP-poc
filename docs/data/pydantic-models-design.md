# Pydantic Models Design - Unified Procurement Schema

**Version:** 1.0
**Status:** Design Phase
**Last Updated:** 2026-02-03
**Related:** `unified-procurement-schema.md`

---

## Overview

This document contains the complete Pydantic model definitions for the unified procurement schema, ready for implementation. These models are designed to:

1. Validate data from multiple sources
2. Enable type-safe consolidation
3. Support serialization to JSON/database
4. Provide clear documentation via Field descriptions

---

## 1. Enum Definitions

```python
"""
Enum definitions for unified procurement schema.

Location: backend/unified_schema/enums.py
"""
from enum import Enum


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


class EsferaGoverno(str, Enum):
    """Government sphere classification."""
    FEDERAL = "F"
    ESTADUAL = "E"
    MUNICIPAL = "M"
    DISTRITAL = "D"


class StatusNormalizado(str, Enum):
    """
    Normalized procurement status across all sources.

    Maps various source-specific status strings to these canonical values.
    """
    PUBLICADA = "PUBLICADA"           # Notice published, accepting proposals
    EM_ANDAMENTO = "EM_ANDAMENTO"     # Bidding session in progress
    SUSPENSA = "SUSPENSA"             # Temporarily suspended
    CANCELADA = "CANCELADA"           # Cancelled by contracting authority
    DESERTA = "DESERTA"               # No bidders submitted proposals
    FRACASSADA = "FRACASSADA"         # Failed (no valid/qualifying bids)
    HOMOLOGADA = "HOMOLOGADA"         # Completed and officially approved
    REVOGADA = "REVOGADA"             # Revoked by authority (public interest)
    ANULADA = "ANULADA"               # Annulled (legal/procedural issues)


class FaixaValor(str, Enum):
    """
    Value brackets for quick filtering and analytics.

    Thresholds based on Brazilian procurement practices:
    - MICRO: Small purchases, often direct contracting
    - PEQUENO: Small/medium competitive bids
    - MEDIO: Standard competitive procurement
    - GRANDE: Large contracts requiring more oversight
    - MUITO_GRANDE: Major contracts (flagship projects)
    """
    MICRO = "MICRO"                   # < R$ 50,000
    PEQUENO = "PEQUENO"               # R$ 50,000 - R$ 500,000
    MEDIO = "MEDIO"                   # R$ 500,000 - R$ 2,000,000
    GRANDE = "GRANDE"                 # R$ 2,000,000 - R$ 5,000,000
    MUITO_GRANDE = "MUITO_GRANDE"     # > R$ 5,000,000


class ConsolidationMethod(str, Enum):
    """How duplicate records were identified."""
    EXACT_MATCH = "EXACT_MATCH"       # Same natural key (CNPJ+numero+ano)
    URL_MATCH = "URL_MATCH"           # Same link_edital URL
    FUZZY_MATCH = "FUZZY_MATCH"       # Algorithmic similarity detection
    MANUAL = "MANUAL"                 # Human-verified duplicate
```

---

## 2. Constants

```python
"""
Constants for unified procurement schema.

Location: backend/unified_schema/constants.py
"""
from decimal import Decimal

# Valid Brazilian state codes
VALID_UFS = frozenset({
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
})

# Source priority for conflict resolution (lower = higher priority)
SOURCE_PRIORITY = {
    "PNCP": 1,
    "PORTAL_COMPRAS": 2,
    "BLL": 3,
    "BNC": 4,
    "LICITAR": 5,
}

# Value thresholds for FaixaValor computation
VALUE_THRESHOLDS = {
    "MICRO": Decimal("50000"),
    "PEQUENO": Decimal("500000"),
    "MEDIO": Decimal("2000000"),
    "GRANDE": Decimal("5000000"),
}

# Fields that can be filled from lower-priority sources when null
FILLABLE_FIELDS = [
    "orgao_cnpj",
    "orgao_esfera",
    "municipio",
    "municipio_codigo",
    "modalidade_id",
    "modalidade_nome",
    "situacao_id",
    "situacao_nome",
    "data_abertura",
    "data_encerramento",
    "valor_homologado",
    "link_edital",
    "link_portal",
    "numero_processo",
    "numero_compra",
    "ano_compra",
]

# Status normalization mapping
STATUS_NORMALIZATION_MAP = {
    # Portuguese variations (lowercase for matching)
    "publicada": "PUBLICADA",
    "publicado": "PUBLICADA",
    "aberta": "PUBLICADA",
    "aberto": "PUBLICADA",
    "em andamento": "EM_ANDAMENTO",
    "andamento": "EM_ANDAMENTO",
    "em sessao": "EM_ANDAMENTO",
    "suspensa": "SUSPENSA",
    "suspenso": "SUSPENSA",
    "suspensao": "SUSPENSA",
    "cancelada": "CANCELADA",
    "cancelado": "CANCELADA",
    "cancelamento": "CANCELADA",
    "deserta": "DESERTA",
    "deserto": "DESERTA",
    "licitacao deserta": "DESERTA",
    "fracassada": "FRACASSADA",
    "fracassado": "FRACASSADA",
    "licitacao fracassada": "FRACASSADA",
    "homologada": "HOMOLOGADA",
    "homologado": "HOMOLOGADA",
    "homologacao": "HOMOLOGADA",
    "adjudicada": "HOMOLOGADA",
    "adjudicado": "HOMOLOGADA",
    "adjudicacao": "HOMOLOGADA",
    "concluida": "HOMOLOGADA",
    "concluido": "HOMOLOGADA",
    "encerrada": "HOMOLOGADA",
    "encerrado": "HOMOLOGADA",
    "revogada": "REVOGADA",
    "revogado": "REVOGADA",
    "revogacao": "REVOGADA",
    "anulada": "ANULADA",
    "anulado": "ANULADA",
    "anulacao": "ANULADA",
}
```

---

## 3. Core Models

### 3.1 UnifiedProcurement

```python
"""
Unified procurement model.

Location: backend/unified_schema/models.py
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
import hashlib
import json
import uuid

from .enums import (
    SourceType, EsferaGoverno, StatusNormalizado,
    FaixaValor, ConsolidationMethod
)
from .constants import (
    VALID_UFS, VALUE_THRESHOLDS, SOURCE_PRIORITY,
    STATUS_NORMALIZATION_MAP
)


class UnifiedProcurement(BaseModel):
    """
    Unified procurement record that consolidates data from multiple sources.

    This model represents the canonical form of a procurement opportunity,
    regardless of which portal it originated from. It handles:

    1. Data normalization across sources
    2. Computed/derived fields
    3. Consolidation metadata
    4. Audit trail information

    Examples:
        >>> from decimal import Decimal
        >>> from datetime import datetime
        >>> proc = UnifiedProcurement(
        ...     source_id="12345-0001-2026",
        ...     source_type=SourceType.PNCP,
        ...     objeto="Aquisicao de uniformes escolares",
        ...     orgao_nome="Prefeitura Municipal",
        ...     uf="SP",
        ...     valor_estimado=Decimal("150000.00"),
        ...     data_publicacao=datetime(2026, 1, 15, 10, 0, 0),
        ... )
        >>> proc.valor_faixa
        <FaixaValor.PEQUENO: 'PEQUENO'>
    """

    # === Primary Identification ===
    unified_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="System-generated unique identifier (UUID v4)"
    )
    source_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Original identifier from source system (e.g., numeroControlePNCP)"
    )
    source_type: SourceType = Field(
        ...,
        description="Source portal identifier"
    )

    # === Core Required Fields ===
    objeto: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Procurement object description (objetoCompra)"
    )
    orgao_nome: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Contracting agency name"
    )
    uf: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Brazilian state code (e.g., SP, RJ, SC)"
    )
    valor_estimado: Decimal = Field(
        ...,
        ge=Decimal("0"),
        max_digits=18,
        decimal_places=2,
        description="Estimated total value in BRL"
    )
    data_publicacao: datetime = Field(
        ...,
        description="Publication date/time (UTC)"
    )

    # === Optional Standard Fields ===
    orgao_cnpj: Optional[str] = Field(
        default=None,
        max_length=20,
        pattern=r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$|^\d{14}$",
        description="Agency CNPJ (formatted or unformatted)"
    )
    orgao_esfera: Optional[EsferaGoverno] = Field(
        default=None,
        description="Government sphere (F=Federal, E=Estadual, M=Municipal, D=Distrital)"
    )
    municipio: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Municipality name"
    )
    municipio_codigo: Optional[str] = Field(
        default=None,
        max_length=10,
        description="IBGE municipality code"
    )
    modalidade_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="Modality code (codigoModalidadeContratacao)"
    )
    modalidade_nome: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Modality name (e.g., Pregao Eletronico)"
    )
    situacao_id: Optional[int] = Field(
        default=None,
        description="Status code from source"
    )
    situacao_nome: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Status name (raw from source)"
    )
    data_abertura: Optional[datetime] = Field(
        default=None,
        description="Proposal opening date/time"
    )
    data_encerramento: Optional[datetime] = Field(
        default=None,
        description="Proposal closing date/time"
    )
    valor_homologado: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("0"),
        max_digits=18,
        decimal_places=2,
        description="Final homologated value in BRL"
    )
    link_edital: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Direct link to notice/documents"
    )
    link_portal: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Portal page URL"
    )
    numero_processo: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Administrative process number"
    )
    numero_compra: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Purchase/bid number"
    )
    ano_compra: Optional[int] = Field(
        default=None,
        ge=2000,
        le=2100,
        description="Purchase year"
    )

    # === Source Metadata ===
    source_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw source-specific fields (preserved for debugging)"
    )
    source_fetched_at: Optional[datetime] = Field(
        default=None,
        description="When data was fetched from source"
    )
    source_hash: Optional[str] = Field(
        default=None,
        max_length=64,
        description="SHA-256 hash for change detection"
    )
    source_priority: int = Field(
        default=5,
        ge=1,
        le=5,
        description="Priority for conflict resolution (1=highest)"
    )

    # === Consolidation Fields ===
    is_consolidated: bool = Field(
        default=False,
        description="True if merged from multiple sources"
    )
    consolidated_from: List[str] = Field(
        default_factory=list,
        description="List of unified_ids that were merged into this record"
    )
    consolidation_method: Optional[ConsolidationMethod] = Field(
        default=None,
        description="How duplicates were detected"
    )
    consolidation_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Match confidence score (0.0-1.0)"
    )
    primary_source: Optional[SourceType] = Field(
        default=None,
        description="Which source's data was preferred for this record"
    )

    # === Computed Fields (auto-populated) ===
    objeto_normalized: Optional[str] = Field(
        default=None,
        description="Normalized object text (lowercase, no accents, for search)"
    )
    valor_faixa: Optional[FaixaValor] = Field(
        default=None,
        description="Value bracket (computed from valor_estimado)"
    )
    dias_ate_abertura: Optional[int] = Field(
        default=None,
        description="Days until proposal opening (null if past or unknown)"
    )
    status_normalizado: Optional[StatusNormalizado] = Field(
        default=None,
        description="Normalized status (mapped from situacao_nome)"
    )

    # === Timestamps ===
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Record creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp"
    )

    # === Validators ===

    @field_validator("uf")
    @classmethod
    def validate_uf(cls, v: str) -> str:
        """Validate UF is a valid Brazilian state code."""
        v_upper = v.upper().strip()
        if v_upper not in VALID_UFS:
            raise ValueError(
                f"Invalid UF: '{v}'. Must be one of: {sorted(VALID_UFS)}"
            )
        return v_upper

    @field_validator("orgao_cnpj")
    @classmethod
    def normalize_cnpj(cls, v: Optional[str]) -> Optional[str]:
        """Normalize CNPJ to standard format."""
        if v is None:
            return None
        # Remove non-digits
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) != 14:
            raise ValueError(f"CNPJ must have 14 digits, got {len(digits)}")
        # Format as XX.XXX.XXX/XXXX-XX
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"

    @model_validator(mode="after")
    def compute_derived_fields(self) -> "UnifiedProcurement":
        """Compute derived fields after all validation."""
        import unicodedata
        import re

        # Compute valor_faixa
        if self.valor_estimado is not None:
            v = self.valor_estimado
            if v < VALUE_THRESHOLDS["MICRO"]:
                self.valor_faixa = FaixaValor.MICRO
            elif v < VALUE_THRESHOLDS["PEQUENO"]:
                self.valor_faixa = FaixaValor.PEQUENO
            elif v < VALUE_THRESHOLDS["MEDIO"]:
                self.valor_faixa = FaixaValor.MEDIO
            elif v < VALUE_THRESHOLDS["GRANDE"]:
                self.valor_faixa = FaixaValor.GRANDE
            else:
                self.valor_faixa = FaixaValor.MUITO_GRANDE

        # Compute dias_ate_abertura
        if self.data_abertura:
            now = datetime.utcnow()
            delta = self.data_abertura.replace(tzinfo=None) - now
            self.dias_ate_abertura = delta.days if delta.days >= 0 else None

        # Compute objeto_normalized
        if self.objeto:
            text = self.objeto.lower()
            text = unicodedata.normalize("NFD", text)
            text = "".join(c for c in text if unicodedata.category(c) != "Mn")
            text = re.sub(r"[^\w\s]", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            self.objeto_normalized = text

        # Compute status_normalizado
        if self.situacao_nome:
            key = self.situacao_nome.lower().strip()
            if key in STATUS_NORMALIZATION_MAP:
                self.status_normalizado = StatusNormalizado(
                    STATUS_NORMALIZATION_MAP[key]
                )

        # Set source_priority based on source_type
        self.source_priority = SOURCE_PRIORITY.get(self.source_type.value, 5)

        return self

    # === Methods ===

    def compute_natural_key(self) -> str:
        """
        Generate natural key for deduplication.

        Format: {orgao_cnpj}:{modalidade_id}:{numero_compra}:{ano_compra}

        Falls back to normalized orgao_nome if CNPJ unavailable.
        """
        if self.orgao_cnpj:
            org_part = self.orgao_cnpj.replace(".", "").replace("/", "").replace("-", "")
        else:
            # Fallback: use normalized orgao_nome + UF
            import unicodedata
            org_norm = self.orgao_nome.lower()
            org_norm = unicodedata.normalize("NFD", org_norm)
            org_norm = "".join(c for c in org_norm if unicodedata.category(c) != "Mn")
            org_norm = "".join(c for c in org_norm if c.isalnum())
            org_part = f"{org_norm}_{self.uf}"

        mod_part = str(self.modalidade_id) if self.modalidade_id else "UNK"
        num_part = self.numero_compra or "UNK"
        ano_part = str(self.ano_compra) if self.ano_compra else "UNK"

        return f"{org_part}:{mod_part}:{num_part}:{ano_part}"

    def compute_content_hash(self) -> str:
        """
        Compute SHA-256 hash of key fields for change detection.

        Used to detect if source data has changed since last fetch.
        """
        key_fields = {
            "source_id": self.source_id,
            "objeto": self.objeto,
            "valor_estimado": str(self.valor_estimado),
            "data_publicacao": self.data_publicacao.isoformat() if self.data_publicacao else None,
            "data_abertura": self.data_abertura.isoformat() if self.data_abertura else None,
            "situacao_nome": self.situacao_nome,
            "link_edital": self.link_edital,
        }
        content = json.dumps(key_fields, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()

    def merge_with(self, other: "UnifiedProcurement") -> "UnifiedProcurement":
        """
        Merge this record with another, filling nulls from lower-priority source.

        Args:
            other: Another UnifiedProcurement to merge

        Returns:
            New UnifiedProcurement with merged data
        """
        from .constants import FILLABLE_FIELDS

        # Determine primary (higher priority = lower number)
        if self.source_priority <= other.source_priority:
            primary, secondary = self, other
        else:
            primary, secondary = other, self

        # Create merged record from primary
        merged_data = primary.model_dump()

        # Fill nulls from secondary
        for field in FILLABLE_FIELDS:
            if merged_data.get(field) is None:
                secondary_value = getattr(secondary, field)
                if secondary_value is not None:
                    merged_data[field] = secondary_value

        # Set consolidation metadata
        merged_data["is_consolidated"] = True
        merged_data["consolidated_from"] = [primary.unified_id, secondary.unified_id]
        merged_data["primary_source"] = primary.source_type
        merged_data["consolidation_method"] = ConsolidationMethod.EXACT_MATCH

        return UnifiedProcurement(**merged_data)

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat(),
        }
        json_schema_extra = {
            "example": {
                "source_id": "83614912000156-1-000001/2026",
                "source_type": "PNCP",
                "objeto": "Aquisicao de uniformes escolares para rede municipal",
                "orgao_nome": "Prefeitura Municipal de Exemplo",
                "orgao_cnpj": "83.614.912/0001-56",
                "uf": "SC",
                "municipio": "Exemplo",
                "valor_estimado": "150000.00",
                "data_publicacao": "2026-01-15T10:00:00Z",
                "data_abertura": "2026-02-01T09:00:00Z",
                "modalidade_nome": "Pregao Eletronico",
                "situacao_nome": "Publicada",
            }
        }
```

### 3.2 SourceMetadata

```python
class SourceMetadata(BaseModel):
    """
    Track which sources contributed to a record.

    Used for audit trails and debugging.
    """
    source_type: SourceType = Field(
        ...,
        description="Source portal"
    )
    source_id: str = Field(
        ...,
        description="ID in source system"
    )
    fetched_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When data was fetched"
    )
    record_hash: str = Field(
        ...,
        max_length=64,
        description="SHA-256 hash of source data"
    )
    raw_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Original source response"
    )
    priority: int = Field(
        default=5,
        ge=1,
        le=5,
        description="Source priority"
    )

    class Config:
        use_enum_values = True
```

### 3.3 ConsolidationResult

```python
class ConsolidationResult(BaseModel):
    """
    Wrapper for consolidation operation results with statistics.

    Provides visibility into the consolidation process for debugging
    and monitoring.
    """
    unified_records: List[UnifiedProcurement] = Field(
        default_factory=list,
        description="Consolidated procurement records"
    )
    total_input_records: int = Field(
        default=0,
        ge=0,
        description="Total records received from all sources"
    )
    total_output_records: int = Field(
        default=0,
        ge=0,
        description="Total unique records after consolidation"
    )
    duplicates_merged: int = Field(
        default=0,
        ge=0,
        description="Number of duplicate sets merged"
    )
    records_by_source: Dict[str, int] = Field(
        default_factory=dict,
        description="Input record count by source"
    )
    output_by_primary_source: Dict[str, int] = Field(
        default_factory=dict,
        description="Output records by primary source"
    )
    validation_errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Records that failed validation with error details"
    )
    processing_time_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Total processing time in milliseconds"
    )

    @property
    def deduplication_rate(self) -> float:
        """Percentage of records removed as duplicates."""
        if self.total_input_records == 0:
            return 0.0
        removed = self.total_input_records - self.total_output_records
        return removed / self.total_input_records

    @property
    def error_rate(self) -> float:
        """Percentage of records that failed validation."""
        if self.total_input_records == 0:
            return 0.0
        return len(self.validation_errors) / self.total_input_records

    def summary(self) -> str:
        """Human-readable summary string."""
        source_breakdown = ", ".join(
            f"{s}: {c}" for s, c in sorted(self.records_by_source.items())
        )
        return (
            f"Consolidation Results:\n"
            f"  Input: {self.total_input_records} records ({source_breakdown})\n"
            f"  Output: {self.total_output_records} unique records\n"
            f"  Merged: {self.duplicates_merged} duplicate sets\n"
            f"  Dedup rate: {self.deduplication_rate:.1%}\n"
            f"  Errors: {len(self.validation_errors)} ({self.error_rate:.1%})\n"
            f"  Time: {self.processing_time_ms:.0f}ms"
        )

    class Config:
        json_schema_extra = {
            "example": {
                "total_input_records": 1500,
                "total_output_records": 1200,
                "duplicates_merged": 150,
                "records_by_source": {"PNCP": 1000, "BLL": 500},
                "output_by_primary_source": {"PNCP": 1000, "BLL": 200},
                "validation_errors": [],
                "processing_time_ms": 2500.0,
            }
        }
```

---

## 4. Validation Error Model

```python
class ValidationError(BaseModel):
    """
    Detailed validation error for a single record.
    """
    source_type: SourceType
    source_id: str
    field: str = Field(description="Field that failed validation")
    error: str = Field(description="Error message")
    value: Optional[Any] = Field(default=None, description="Invalid value")
    raw_record: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Original record for debugging"
    )
```

---

## 5. Request/Response Models

### 5.1 Search Request

```python
class UnifiedSearchRequest(BaseModel):
    """
    Request model for searching unified procurement records.

    Extends existing BuscaRequest with multi-source support.
    """
    ufs: List[str] = Field(
        ...,
        min_length=1,
        description="List of UF codes to search"
    )
    data_inicial: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Start date (YYYY-MM-DD)"
    )
    data_final: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="End date (YYYY-MM-DD)"
    )
    sources: Optional[List[SourceType]] = Field(
        default=None,
        description="Sources to query (None = all available)"
    )
    setor_id: str = Field(
        default="vestuario",
        description="Sector for keyword filtering"
    )
    valor_min: Optional[Decimal] = Field(
        default=Decimal("50000"),
        ge=Decimal("0"),
        description="Minimum value filter"
    )
    valor_max: Optional[Decimal] = Field(
        default=Decimal("5000000"),
        ge=Decimal("0"),
        description="Maximum value filter"
    )
    status_filter: Optional[List[StatusNormalizado]] = Field(
        default=None,
        description="Filter by normalized status"
    )
    include_consolidated: bool = Field(
        default=True,
        description="Include consolidated records in results"
    )
```

### 5.2 Search Response

```python
class UnifiedSearchResponse(BaseModel):
    """
    Response model for unified search results.

    Extends existing BuscaResponse with consolidation stats.
    """
    resultados: List[UnifiedProcurement] = Field(
        default_factory=list,
        description="Matching procurement records"
    )
    total_resultados: int = Field(
        default=0,
        description="Total matching records"
    )
    consolidation_stats: Optional[ConsolidationResult] = Field(
        default=None,
        description="Consolidation statistics (if applicable)"
    )
    sources_queried: List[SourceType] = Field(
        default_factory=list,
        description="Sources that were queried"
    )
    sources_failed: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Sources that failed with error messages"
    )
    resumo: Optional[Any] = Field(
        default=None,
        description="LLM-generated summary (same as existing)"
    )
    excel_base64: Optional[str] = Field(
        default=None,
        description="Excel file as base64 (same as existing)"
    )
```

---

## 6. File Structure

Recommended file organization:

```
backend/
  unified_schema/
    __init__.py           # Export public API
    enums.py              # SourceType, StatusNormalizado, etc.
    constants.py          # VALID_UFS, mappings, thresholds
    models.py             # UnifiedProcurement, ConsolidationResult
    adapters/
      __init__.py
      base.py             # SourceAdapter ABC
      pncp.py             # PNCPAdapter
      bll.py              # BLLAdapter (future)
      portal_compras.py   # PortalComprasAdapter (future)
      bnc.py              # BNCAdapter (future)
      licitar.py          # LicitarAdapter (future)
    consolidation.py      # Deduplication logic
    validation.py         # Custom validators
```

---

## 7. Usage Examples

### 7.1 Creating a Record

```python
from decimal import Decimal
from datetime import datetime
from backend.unified_schema import UnifiedProcurement, SourceType

# Create from PNCP data
proc = UnifiedProcurement(
    source_id="83614912000156-1-000001/2026",
    source_type=SourceType.PNCP,
    objeto="Aquisicao de uniformes escolares para rede municipal de ensino",
    orgao_nome="Prefeitura Municipal de Joinville",
    orgao_cnpj="83.614.912/0001-56",
    uf="SC",
    municipio="Joinville",
    valor_estimado=Decimal("487500.00"),
    data_publicacao=datetime(2026, 1, 20, 8, 0, 0),
    data_abertura=datetime(2026, 2, 5, 9, 0, 0),
    modalidade_id=6,
    modalidade_nome="Pregao Eletronico",
    situacao_nome="Publicada",
    link_edital="https://compras.joinville.sc.gov.br/pregao/1",
)

# Computed fields are auto-populated
print(proc.valor_faixa)        # FaixaValor.PEQUENO
print(proc.status_normalizado) # StatusNormalizado.PUBLICADA
print(proc.dias_ate_abertura)  # Computed from data_abertura
print(proc.objeto_normalized)  # "aquisicao de uniformes escolares..."
```

### 7.2 Merging Duplicates

```python
# Two records from different sources
pncp_record = UnifiedProcurement(
    source_id="123",
    source_type=SourceType.PNCP,
    objeto="Uniformes escolares",
    orgao_nome="Prefeitura",
    uf="SP",
    valor_estimado=Decimal("100000"),
    data_publicacao=datetime.now(),
    # Missing some fields
    municipio=None,
    link_edital=None,
)

bll_record = UnifiedProcurement(
    source_id="abc",
    source_type=SourceType.BLL,
    objeto="Uniformes escolares",
    orgao_nome="Prefeitura",
    uf="SP",
    valor_estimado=Decimal("100000"),
    data_publicacao=datetime.now(),
    # Has additional data
    municipio="Sao Paulo",
    link_edital="https://bll.com.br/edital/123",
)

# Merge (PNCP preferred, but fills nulls from BLL)
merged = pncp_record.merge_with(bll_record)

print(merged.primary_source)   # SourceType.PNCP
print(merged.municipio)        # "Sao Paulo" (from BLL)
print(merged.link_edital)      # "https://bll.com.br/..." (from BLL)
print(merged.is_consolidated)  # True
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-03 | @data-engineer | Initial model design |
