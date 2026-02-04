# Unified Procurement Schema Design

**Version:** 1.0
**Status:** Design Phase
**Last Updated:** 2026-02-03
**Author:** Data Engineer (@data-engineer)

---

## 1. Executive Summary

This document defines the unified data schema for consolidating procurement data from multiple Brazilian government procurement portals. The goal is to create a single, normalized data model that can ingest data from 5 distinct sources while maintaining data quality, enabling deduplication, and preserving source-specific metadata.

### 1.1 Scope

**In Scope:**
- PNCP (Portal Nacional de Contratacoes Publicas) - Primary source
- BLL Compras
- Portal de Compras Publicas
- BNC (Bolsa Nacional de Compras)
- Licitar Digital

**Out of Scope (Phase 1):**
- ComprasNet (legacy system being migrated to PNCP)
- State-specific portals (e.g., BEC-SP, SIGA-RJ)
- Private marketplace aggregators

---

## 2. Design Principles

### 2.1 Core Design Decisions

| Principle | Rationale |
|-----------|-----------|
| **Source-agnostic core** | Core fields work regardless of source, enabling consistent filtering and reporting |
| **Preserve source fidelity** | Source-specific fields retained in metadata to avoid data loss |
| **Explicit nullability** | Required vs optional clearly defined to enforce data quality |
| **Deduplication by design** | Composite keys and matching algorithms built into schema |
| **Audit trail** | Track which sources contributed data and when |

### 2.2 Field Naming Convention

- **snake_case** for all field names (Python/database compatible)
- **Portuguese field names** for domain concepts (objeto, orgao, modalidade)
- **English field names** for technical fields (source, created_at, hash)
- **Suffix conventions:**
  - `_id` - Unique identifiers
  - `_at` - Timestamps
  - `_url` - URLs/links
  - `_raw` - Unprocessed source data

---

## 3. Unified Schema Definition

### 3.1 Core Fields (Required)

These fields MUST be populated for every procurement record, regardless of source.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `unified_id` | `str` | System-generated unique identifier | UUID v4, auto-generated |
| `source_id` | `str` | Identifier from the source system | Non-empty string |
| `source_type` | `enum` | Source portal identifier | One of: PNCP, BLL, PORTAL_COMPRAS, BNC, LICITAR |
| `objeto` | `str` | Procurement object description | Min 10 chars, max 5000 chars |
| `orgao_nome` | `str` | Contracting agency name | Non-empty string |
| `uf` | `str` | Brazilian state code | Valid UF (2 chars, uppercase) |
| `valor_estimado` | `Decimal` | Estimated total value in BRL | >= 0, max 18 digits |
| `data_publicacao` | `datetime` | Publication date/time | ISO 8601, not future dated |
| `created_at` | `datetime` | Record creation timestamp | Auto-generated |
| `updated_at` | `datetime` | Last update timestamp | Auto-generated |

### 3.2 Standard Fields (Optional but Common)

These fields are available in most sources but may be null.

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `orgao_cnpj` | `str` | Agency CNPJ (tax ID) | null |
| `orgao_esfera` | `enum` | Government sphere | null |
| `municipio` | `str` | Municipality name | null |
| `municipio_codigo` | `str` | IBGE municipality code | null |
| `modalidade_id` | `int` | Modality code | null |
| `modalidade_nome` | `str` | Modality name | null |
| `situacao_id` | `int` | Status code | null |
| `situacao_nome` | `str` | Status name | null |
| `data_abertura` | `datetime` | Proposal opening date | null |
| `data_encerramento` | `datetime` | Proposal closing date | null |
| `valor_homologado` | `Decimal` | Homologated value (final) | null |
| `link_edital` | `str` | Direct link to notice | null |
| `link_portal` | `str` | Portal page URL | null |
| `numero_processo` | `str` | Process number | null |
| `numero_compra` | `str` | Purchase number | null |
| `ano_compra` | `int` | Purchase year | null |

### 3.3 Source Metadata Fields

Track data provenance and enable conflict resolution.

| Field | Type | Description |
|-------|------|-------------|
| `source_metadata` | `JSON` | Raw source-specific fields (preserved) |
| `source_fetched_at` | `datetime` | When data was fetched from source |
| `source_hash` | `str` | SHA-256 hash of source record for change detection |
| `source_priority` | `int` | Priority for conflict resolution (1=highest) |

### 3.4 Consolidation Fields

Track deduplication and merging operations.

| Field | Type | Description |
|-------|------|-------------|
| `is_consolidated` | `bool` | True if merged from multiple sources |
| `consolidated_from` | `List[str]` | List of unified_ids that were merged |
| `consolidation_method` | `str` | How duplicates were detected (exact/fuzzy) |
| `consolidation_confidence` | `float` | Match confidence score (0.0-1.0) |
| `primary_source` | `enum` | Which source's data was preferred |

### 3.5 Computed/Derived Fields

Generated during ingestion for search and filtering optimization.

| Field | Type | Description |
|-------|------|-------------|
| `objeto_normalized` | `str` | Normalized object text (lowercase, no accents) |
| `valor_faixa` | `enum` | Value bracket (MICRO, PEQUENO, MEDIO, GRANDE) |
| `dias_ate_abertura` | `int` | Days until proposal opening (null if past) |
| `status_normalizado` | `enum` | Normalized status across sources |

---

## 4. Enum Definitions

### 4.1 SourceType

```python
class SourceType(str, Enum):
    PNCP = "PNCP"
    BLL = "BLL"
    PORTAL_COMPRAS = "PORTAL_COMPRAS"
    BNC = "BNC"
    LICITAR = "LICITAR"
```

### 4.2 EsferaGoverno (Government Sphere)

```python
class EsferaGoverno(str, Enum):
    FEDERAL = "F"
    ESTADUAL = "E"
    MUNICIPAL = "M"
    DISTRITAL = "D"
```

### 4.3 StatusNormalizado (Normalized Status)

```python
class StatusNormalizado(str, Enum):
    PUBLICADA = "PUBLICADA"           # Notice published, accepting proposals
    EM_ANDAMENTO = "EM_ANDAMENTO"     # Bidding in progress
    SUSPENSA = "SUSPENSA"             # Temporarily suspended
    CANCELADA = "CANCELADA"           # Cancelled
    DESERTA = "DESERTA"               # No bidders
    FRACASSADA = "FRACASSADA"         # Failed (no valid bids)
    HOMOLOGADA = "HOMOLOGADA"         # Completed and approved
    REVOGADA = "REVOGADA"             # Revoked by authority
    ANULADA = "ANULADA"               # Annulled
```

### 4.4 FaixaValor (Value Bracket)

```python
class FaixaValor(str, Enum):
    MICRO = "MICRO"           # < R$ 50,000
    PEQUENO = "PEQUENO"       # R$ 50,000 - R$ 500,000
    MEDIO = "MEDIO"           # R$ 500,000 - R$ 2,000,000
    GRANDE = "GRANDE"         # R$ 2,000,000 - R$ 5,000,000
    MUITO_GRANDE = "MUITO_GRANDE"  # > R$ 5,000,000
```

---

## 5. Field Mapping Table

### 5.1 Complete Source-to-Unified Mapping

| Unified Field | PNCP | BLL | Portal Compras | BNC | Licitar Digital |
|---------------|------|-----|----------------|-----|-----------------|
| **Identification** |
| `source_id` | `numeroControlePNCP` | TBD | TBD | TBD | TBD |
| `numero_compra` | `numeroCompra` | TBD | TBD | TBD | TBD |
| `ano_compra` | `anoCompra` | TBD | TBD | TBD | TBD |
| `numero_processo` | `numeroProcesso` | TBD | TBD | TBD | TBD |
| **Object** |
| `objeto` | `objetoCompra` | TBD | TBD | TBD | TBD |
| `objeto_normalized` | *computed* | *computed* | *computed* | *computed* | *computed* |
| **Values** |
| `valor_estimado` | `valorTotalEstimado` | TBD | TBD | TBD | TBD |
| `valor_homologado` | `valorTotalHomologado` | TBD | TBD | TBD | TBD |
| `valor_faixa` | *computed* | *computed* | *computed* | *computed* | *computed* |
| **Dates** |
| `data_publicacao` | `dataPublicacaoPncp` | TBD | TBD | TBD | TBD |
| `data_abertura` | `dataAberturaProposta` | TBD | TBD | TBD | TBD |
| `data_encerramento` | `dataEncerramentoProposta` | TBD | TBD | TBD | TBD |
| **Agency** |
| `orgao_nome` | `orgaoEntidade.razaoSocial` OR `unidadeOrgao.nomeUnidade` | TBD | TBD | TBD | TBD |
| `orgao_cnpj` | `orgaoEntidade.cnpj` | TBD | TBD | TBD | TBD |
| `orgao_esfera` | `esferaId` | TBD | TBD | TBD | TBD |
| **Location** |
| `uf` | `unidadeOrgao.ufSigla` | TBD | TBD | TBD | TBD |
| `municipio` | `unidadeOrgao.municipioNome` | TBD | TBD | TBD | TBD |
| `municipio_codigo` | `codigoMunicipio` | TBD | TBD | TBD | TBD |
| **Classification** |
| `modalidade_id` | `codigoModalidadeContratacao` | TBD | TBD | TBD | TBD |
| `modalidade_nome` | `modalidadeNome` | TBD | TBD | TBD | TBD |
| `situacao_id` | `situacaoCompraId` | TBD | TBD | TBD | TBD |
| `situacao_nome` | `situacaoCompraNome` | TBD | TBD | TBD | TBD |
| `status_normalizado` | *mapped from situacaoCompraNome* | TBD | TBD | TBD | TBD |
| **Links** |
| `link_edital` | `linkSistemaOrigem` | TBD | TBD | TBD | TBD |
| `link_portal` | `linkProcessoEletronico` OR constructed | TBD | TBD | TBD | TBD |

**Note:** TBD fields are pending research by the Business Analyst. Once API documentation for each source is available, this table will be completed.

### 5.2 PNCP Status Mapping

| PNCP `situacaoCompraNome` | `status_normalizado` |
|---------------------------|---------------------|
| Publicada | PUBLICADA |
| Em andamento | EM_ANDAMENTO |
| Suspensa | SUSPENSA |
| Cancelada | CANCELADA |
| Deserta | DESERTA |
| Fracassada | FRACASSADA |
| Homologada | HOMOLOGADA |
| Revogada | REVOGADA |
| Anulada | ANULADA |

---

## 6. Deduplication Strategy

### 6.1 Primary Key Definition

A procurement is uniquely identified by:

**Composite Natural Key:**
```
{orgao_cnpj}:{modalidade_id}:{numero_compra}:{ano_compra}
```

**Example:**
```
12.345.678/0001-90:6:000001/2026:2026
```

**Fallback when CNPJ unavailable:**
```
{orgao_nome_normalized}:{uf}:{modalidade_id}:{numero_compra}:{ano_compra}
```

### 6.2 Matching Algorithm

#### 6.2.1 Exact Match (High Confidence)

Conditions for exact match (confidence = 1.0):
1. Same CNPJ + numero_compra + ano_compra
2. Same link_edital URL (normalized)

#### 6.2.2 Fuzzy Match (Medium Confidence)

When exact match fails, use fuzzy matching with scoring:

| Factor | Weight | Match Criteria |
|--------|--------|----------------|
| `objeto` similarity | 0.35 | Jaccard similarity > 0.85 on normalized tokens |
| `orgao_nome` similarity | 0.25 | Levenshtein ratio > 0.90 |
| `valor_estimado` proximity | 0.20 | Within 5% of each other |
| `data_publicacao` proximity | 0.10 | Within 7 days |
| `uf` + `municipio` match | 0.10 | Exact match |

**Confidence Score Calculation:**
```python
confidence = sum(weight * score for factor in factors)
```

**Thresholds:**
- `confidence >= 0.90`: Auto-merge
- `0.75 <= confidence < 0.90`: Flag for review
- `confidence < 0.75`: Treat as distinct records

### 6.3 Merge Strategy

When duplicate detected, create consolidated record:

```python
def merge_duplicates(records: List[UnifiedProcurement]) -> UnifiedProcurement:
    """
    Merge duplicate records with source priority.

    Priority Order (highest to lowest):
    1. PNCP (official government portal)
    2. Portal de Compras Publicas
    3. BLL Compras
    4. BNC
    5. Licitar Digital
    """
    # Sort by source priority
    sorted_records = sorted(records, key=lambda r: SOURCE_PRIORITY[r.source_type])

    primary = sorted_records[0]
    merged = primary.copy()

    # Fill nulls from lower-priority sources
    for field in FILLABLE_FIELDS:
        if getattr(merged, field) is None:
            for record in sorted_records[1:]:
                value = getattr(record, field)
                if value is not None:
                    setattr(merged, field, value)
                    break

    # Set consolidation metadata
    merged.is_consolidated = True
    merged.consolidated_from = [r.unified_id for r in records]
    merged.primary_source = primary.source_type

    return merged
```

### 6.4 Source Priority

| Priority | Source | Rationale |
|----------|--------|-----------|
| 1 | PNCP | Official federal portal, most authoritative |
| 2 | Portal de Compras Publicas | Established marketplace |
| 3 | BLL Compras | Major private portal |
| 4 | BNC | Regional focus |
| 5 | Licitar Digital | Newest entrant |

---

## 7. Data Quality Rules

### 7.1 Required Field Validation

```python
REQUIRED_FIELDS = {
    'source_id': lambda v: v and len(v) > 0,
    'source_type': lambda v: v in SourceType.__members__,
    'objeto': lambda v: v and 10 <= len(v) <= 5000,
    'orgao_nome': lambda v: v and len(v) > 0,
    'uf': lambda v: v and v in VALID_UFS,
    'valor_estimado': lambda v: v is not None and v >= 0,
    'data_publicacao': lambda v: v is not None and v <= datetime.now(),
}
```

### 7.2 Value Range Validation

```python
VALUE_CONSTRAINTS = {
    'valor_estimado': {
        'min': Decimal('0'),
        'max': Decimal('999999999999999.99'),  # 18 digits
        'warn_if_below': Decimal('1000'),      # Suspicious if < R$1000
        'warn_if_above': Decimal('100000000'), # Flag > R$100M for review
    },
    'ano_compra': {
        'min': 2000,
        'max': datetime.now().year + 1,
    },
}
```

### 7.3 Date Consistency Checks

```python
def validate_date_consistency(record: UnifiedProcurement) -> List[str]:
    """Return list of validation warnings."""
    warnings = []

    if record.data_publicacao and record.data_abertura:
        if record.data_abertura < record.data_publicacao:
            warnings.append("data_abertura before data_publicacao")

    if record.data_abertura and record.data_encerramento:
        if record.data_encerramento < record.data_abertura:
            warnings.append("data_encerramento before data_abertura")

    if record.data_publicacao:
        if record.data_publicacao > datetime.now():
            warnings.append("data_publicacao in future")

    return warnings
```

### 7.4 Status Normalization Rules

```python
STATUS_NORMALIZATION_MAP = {
    # PNCP variations
    'publicada': StatusNormalizado.PUBLICADA,
    'publicado': StatusNormalizado.PUBLICADA,
    'aberta': StatusNormalizado.PUBLICADA,
    'em andamento': StatusNormalizado.EM_ANDAMENTO,
    'andamento': StatusNormalizado.EM_ANDAMENTO,
    'suspensa': StatusNormalizado.SUSPENSA,
    'suspenso': StatusNormalizado.SUSPENSA,
    'cancelada': StatusNormalizado.CANCELADA,
    'cancelado': StatusNormalizado.CANCELADA,
    'deserta': StatusNormalizado.DESERTA,
    'deserto': StatusNormalizado.DESERTA,
    'fracassada': StatusNormalizado.FRACASSADA,
    'fracassado': StatusNormalizado.FRACASSADA,
    'homologada': StatusNormalizado.HOMOLOGADA,
    'homologado': StatusNormalizado.HOMOLOGADA,
    'adjudicada': StatusNormalizado.HOMOLOGADA,
    'adjudicado': StatusNormalizado.HOMOLOGADA,
    'revogada': StatusNormalizado.REVOGADA,
    'revogado': StatusNormalizado.REVOGADA,
    'anulada': StatusNormalizado.ANULADA,
    'anulado': StatusNormalizado.ANULADA,
    # Add more mappings as sources are analyzed
}

def normalize_status(status_raw: str) -> Optional[StatusNormalizado]:
    """Normalize status string to enum."""
    if not status_raw:
        return None
    key = status_raw.lower().strip()
    return STATUS_NORMALIZATION_MAP.get(key)
```

---

## 8. Pydantic Model Definitions

### 8.1 UnifiedProcurement Model

```python
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
import uuid


class SourceType(str, Enum):
    PNCP = "PNCP"
    BLL = "BLL"
    PORTAL_COMPRAS = "PORTAL_COMPRAS"
    BNC = "BNC"
    LICITAR = "LICITAR"


class EsferaGoverno(str, Enum):
    FEDERAL = "F"
    ESTADUAL = "E"
    MUNICIPAL = "M"
    DISTRITAL = "D"


class StatusNormalizado(str, Enum):
    PUBLICADA = "PUBLICADA"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    SUSPENSA = "SUSPENSA"
    CANCELADA = "CANCELADA"
    DESERTA = "DESERTA"
    FRACASSADA = "FRACASSADA"
    HOMOLOGADA = "HOMOLOGADA"
    REVOGADA = "REVOGADA"
    ANULADA = "ANULADA"


class FaixaValor(str, Enum):
    MICRO = "MICRO"
    PEQUENO = "PEQUENO"
    MEDIO = "MEDIO"
    GRANDE = "GRANDE"
    MUITO_GRANDE = "MUITO_GRANDE"


VALID_UFS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
}


class UnifiedProcurement(BaseModel):
    """
    Unified procurement record that consolidates data from multiple sources.

    This model represents the canonical form of a procurement opportunity,
    regardless of which portal it originated from.
    """

    # === Primary Identification ===
    unified_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="System-generated unique identifier"
    )
    source_id: str = Field(
        ...,
        min_length=1,
        description="Original identifier from source system"
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
        description="Procurement object description"
    )
    orgao_nome: str = Field(
        ...,
        min_length=1,
        description="Contracting agency name"
    )
    uf: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Brazilian state code"
    )
    valor_estimado: Decimal = Field(
        ...,
        ge=0,
        description="Estimated total value in BRL"
    )
    data_publicacao: datetime = Field(
        ...,
        description="Publication date/time"
    )

    # === Optional Standard Fields ===
    orgao_cnpj: Optional[str] = Field(
        default=None,
        description="Agency CNPJ (tax ID)"
    )
    orgao_esfera: Optional[EsferaGoverno] = Field(
        default=None,
        description="Government sphere"
    )
    municipio: Optional[str] = Field(
        default=None,
        description="Municipality name"
    )
    municipio_codigo: Optional[str] = Field(
        default=None,
        description="IBGE municipality code"
    )
    modalidade_id: Optional[int] = Field(
        default=None,
        description="Modality code"
    )
    modalidade_nome: Optional[str] = Field(
        default=None,
        description="Modality name"
    )
    situacao_id: Optional[int] = Field(
        default=None,
        description="Status code"
    )
    situacao_nome: Optional[str] = Field(
        default=None,
        description="Status name (raw from source)"
    )
    data_abertura: Optional[datetime] = Field(
        default=None,
        description="Proposal opening date"
    )
    data_encerramento: Optional[datetime] = Field(
        default=None,
        description="Proposal closing date"
    )
    valor_homologado: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Homologated value (final)"
    )
    link_edital: Optional[str] = Field(
        default=None,
        description="Direct link to notice"
    )
    link_portal: Optional[str] = Field(
        default=None,
        description="Portal page URL"
    )
    numero_processo: Optional[str] = Field(
        default=None,
        description="Process number"
    )
    numero_compra: Optional[str] = Field(
        default=None,
        description="Purchase number"
    )
    ano_compra: Optional[int] = Field(
        default=None,
        ge=2000,
        description="Purchase year"
    )

    # === Source Metadata ===
    source_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw source-specific fields"
    )
    source_fetched_at: Optional[datetime] = Field(
        default=None,
        description="When data was fetched from source"
    )
    source_hash: Optional[str] = Field(
        default=None,
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
        description="List of unified_ids that were merged"
    )
    consolidation_method: Optional[str] = Field(
        default=None,
        description="How duplicates were detected"
    )
    consolidation_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Match confidence score"
    )
    primary_source: Optional[SourceType] = Field(
        default=None,
        description="Which source's data was preferred"
    )

    # === Computed Fields ===
    objeto_normalized: Optional[str] = Field(
        default=None,
        description="Normalized object text"
    )
    valor_faixa: Optional[FaixaValor] = Field(
        default=None,
        description="Value bracket"
    )
    dias_ate_abertura: Optional[int] = Field(
        default=None,
        description="Days until proposal opening"
    )
    status_normalizado: Optional[StatusNormalizado] = Field(
        default=None,
        description="Normalized status"
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

    @field_validator('uf')
    @classmethod
    def validate_uf(cls, v: str) -> str:
        v = v.upper()
        if v not in VALID_UFS:
            raise ValueError(f"Invalid UF: {v}. Must be one of {VALID_UFS}")
        return v

    @model_validator(mode='after')
    def compute_derived_fields(self) -> 'UnifiedProcurement':
        """Compute derived fields after validation."""
        # Compute valor_faixa
        if self.valor_estimado is not None:
            v = self.valor_estimado
            if v < 50000:
                self.valor_faixa = FaixaValor.MICRO
            elif v < 500000:
                self.valor_faixa = FaixaValor.PEQUENO
            elif v < 2000000:
                self.valor_faixa = FaixaValor.MEDIO
            elif v < 5000000:
                self.valor_faixa = FaixaValor.GRANDE
            else:
                self.valor_faixa = FaixaValor.MUITO_GRANDE

        # Compute dias_ate_abertura
        if self.data_abertura:
            delta = self.data_abertura - datetime.utcnow()
            self.dias_ate_abertura = delta.days if delta.days >= 0 else None

        return self

    class Config:
        use_enum_values = True
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat(),
        }
```

### 8.2 SourceMetadata Model

```python
class SourceMetadata(BaseModel):
    """
    Track which sources contributed to a record.

    Used for audit trails and conflict resolution.
    """
    source_type: SourceType
    source_id: str
    fetched_at: datetime
    record_hash: str
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=5)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "fetched_at": self.fetched_at.isoformat(),
            "record_hash": self.record_hash,
            "priority": self.priority,
        }
```

### 8.3 ConsolidationResult Model

```python
class ConsolidationResult(BaseModel):
    """
    Wrapper for consolidation operation results with statistics.
    """
    unified_records: List[UnifiedProcurement] = Field(
        default_factory=list,
        description="Consolidated procurement records"
    )
    total_input_records: int = Field(
        default=0,
        description="Total records received from all sources"
    )
    total_output_records: int = Field(
        default=0,
        description="Total unique records after consolidation"
    )
    duplicates_merged: int = Field(
        default=0,
        description="Number of duplicate sets merged"
    )
    records_by_source: Dict[str, int] = Field(
        default_factory=dict,
        description="Input record count by source"
    )
    output_by_source: Dict[str, int] = Field(
        default_factory=dict,
        description="Output records by primary source"
    )
    validation_errors: List[str] = Field(
        default_factory=list,
        description="Records that failed validation"
    )
    processing_time_ms: float = Field(
        default=0.0,
        description="Processing time in milliseconds"
    )

    @property
    def deduplication_rate(self) -> float:
        """Percentage of records removed as duplicates."""
        if self.total_input_records == 0:
            return 0.0
        return 1 - (self.total_output_records / self.total_input_records)

    def summary(self) -> str:
        """Human-readable summary."""
        return (
            f"Consolidation complete:\n"
            f"  Input: {self.total_input_records} records from {len(self.records_by_source)} sources\n"
            f"  Output: {self.total_output_records} unique records\n"
            f"  Merged: {self.duplicates_merged} duplicate sets\n"
            f"  Dedup rate: {self.deduplication_rate:.1%}\n"
            f"  Errors: {len(self.validation_errors)}\n"
            f"  Time: {self.processing_time_ms:.0f}ms"
        )
```

---

## 9. Implementation Notes

### 9.1 Source Adapter Pattern

Each source should have an adapter that transforms raw API response to `UnifiedProcurement`:

```python
class SourceAdapter(ABC):
    """Abstract base for source-specific adapters."""

    @abstractmethod
    def transform(self, raw: Dict[str, Any]) -> UnifiedProcurement:
        """Transform raw API response to unified format."""
        pass

    @abstractmethod
    def get_source_type(self) -> SourceType:
        """Return the source type this adapter handles."""
        pass

    @abstractmethod
    def compute_hash(self, raw: Dict[str, Any]) -> str:
        """Compute hash for change detection."""
        pass


class PNCPAdapter(SourceAdapter):
    """Adapter for PNCP API responses."""

    def get_source_type(self) -> SourceType:
        return SourceType.PNCP

    def transform(self, raw: Dict[str, Any]) -> UnifiedProcurement:
        # Extract nested fields
        unidade = raw.get("unidadeOrgao") or {}
        orgao = raw.get("orgaoEntidade") or {}

        return UnifiedProcurement(
            source_id=raw.get("numeroControlePNCP", ""),
            source_type=SourceType.PNCP,
            objeto=raw.get("objetoCompra", ""),
            orgao_nome=orgao.get("razaoSocial") or unidade.get("nomeUnidade", ""),
            orgao_cnpj=orgao.get("cnpj"),
            uf=unidade.get("ufSigla", ""),
            municipio=unidade.get("municipioNome"),
            valor_estimado=Decimal(str(raw.get("valorTotalEstimado", 0))),
            data_publicacao=self._parse_datetime(raw.get("dataPublicacaoPncp")),
            data_abertura=self._parse_datetime(raw.get("dataAberturaProposta")),
            modalidade_id=raw.get("codigoModalidadeContratacao"),
            modalidade_nome=raw.get("modalidadeNome"),
            situacao_nome=raw.get("situacaoCompraNome"),
            link_edital=raw.get("linkSistemaOrigem"),
            link_portal=raw.get("linkProcessoEletronico"),
            source_metadata=raw,
            source_priority=1,  # PNCP is highest priority
        )

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
```

### 9.2 Database Schema (Future)

When persisting to database, consider:

```sql
-- PostgreSQL schema sketch
CREATE TABLE unified_procurements (
    unified_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id VARCHAR(100) NOT NULL,
    source_type VARCHAR(20) NOT NULL,

    -- Core fields
    objeto TEXT NOT NULL,
    objeto_normalized TEXT,  -- Generated, indexed for search
    orgao_nome VARCHAR(500) NOT NULL,
    orgao_cnpj VARCHAR(20),
    uf CHAR(2) NOT NULL,
    municipio VARCHAR(200),
    valor_estimado DECIMAL(18,2) NOT NULL,
    valor_faixa VARCHAR(20),

    -- Dates
    data_publicacao TIMESTAMPTZ NOT NULL,
    data_abertura TIMESTAMPTZ,
    data_encerramento TIMESTAMPTZ,

    -- Status
    situacao_nome VARCHAR(100),
    status_normalizado VARCHAR(20),

    -- Links
    link_edital TEXT,
    link_portal TEXT,

    -- Metadata
    source_metadata JSONB,
    source_hash VARCHAR(64),
    source_priority SMALLINT DEFAULT 5,

    -- Consolidation
    is_consolidated BOOLEAN DEFAULT FALSE,
    consolidated_from TEXT[],
    primary_source VARCHAR(20),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    CONSTRAINT chk_uf CHECK (uf ~ '^[A-Z]{2}$'),
    CONSTRAINT chk_valor CHECK (valor_estimado >= 0)
);

-- Indexes for common queries
CREATE INDEX idx_procurements_uf ON unified_procurements(uf);
CREATE INDEX idx_procurements_data_pub ON unified_procurements(data_publicacao);
CREATE INDEX idx_procurements_valor ON unified_procurements(valor_estimado);
CREATE INDEX idx_procurements_status ON unified_procurements(status_normalizado);
CREATE INDEX idx_procurements_source ON unified_procurements(source_type, source_id);
CREATE INDEX idx_procurements_objeto_search ON unified_procurements
    USING gin(to_tsvector('portuguese', objeto_normalized));

-- Unique constraint for deduplication
CREATE UNIQUE INDEX idx_procurements_natural_key
    ON unified_procurements(orgao_cnpj, modalidade_id, numero_compra, ano_compra)
    WHERE orgao_cnpj IS NOT NULL;
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

- Field validation for all constraints
- Enum conversions
- Date parsing across formats
- Value range calculations
- Status normalization mapping

### 10.2 Integration Tests

- PNCP adapter with real API responses
- Deduplication algorithm accuracy
- Merge strategy correctness
- Hash consistency

### 10.3 Test Data

Maintain fixtures for:
- Valid records from each source
- Edge cases (missing fields, unusual values)
- Known duplicate pairs for dedup testing

---

## 11. Migration Path

### 11.1 Phase 1: PNCP Only (Current)

- Existing `pncp_client.py` feeds data
- Add `UnifiedProcurement` model
- Create `PNCPAdapter` to transform existing flow
- No breaking changes to current functionality

### 11.2 Phase 2: Add Source Tracking

- Add `source_type` and `source_metadata` fields
- Implement change detection with `source_hash`
- Build consolidation pipeline (PNCP-only)

### 11.3 Phase 3: Multi-Source Integration

- Add adapters for each new source (as analyst completes research)
- Implement deduplication algorithm
- Enable cross-source consolidation

---

## 12. Open Questions

1. **API Rate Limits**: What are the rate limits for BLL, Portal, BNC, Licitar?
2. **Authentication**: Which sources require API keys or OAuth?
3. **Historical Data**: How far back can we fetch from each source?
4. **Update Frequency**: How often do sources update their data?
5. **Field Availability**: Which optional fields are actually available in each source?

These questions will be addressed as the Business Analyst completes source research.

---

## Appendix A: PNCP Field Reference

Complete field list from PNCP API response (reference from PRD.md):

```json
{
  "numeroControlePNCP": "83614912000156-1-000001/2026",
  "numeroCompra": "000001/2026",
  "anoCompra": 2026,
  "objetoCompra": "AQUISICAO DE UNIFORMES ESCOLARES...",
  "informacaoComplementar": "Conforme especificacoes...",
  "valorTotalEstimado": 487500.00,
  "valorTotalHomologado": null,
  "dataPublicacaoPncp": "2026-01-20T08:00:00Z",
  "dataAberturaProposta": "2026-02-05T09:00:00Z",
  "dataEncerramentoProposta": "2026-02-04T23:59:59Z",
  "codigoModalidadeContratacao": 6,
  "modalidadeNome": "Pregao - Loss",
  "situacaoCompraId": 1,
  "situacaoCompraNome": "Publicada",
  "orgaoEntidade": {
    "cnpj": "83.614.912/0001-56",
    "razaoSocial": "PREFEITURA MUNICIPAL DE EXEMPLO"
  },
  "unidadeOrgao": {
    "codigoUnidade": "1",
    "nomeUnidade": "SECRETARIA DE EDUCACAO",
    "ufSigla": "SC",
    "municipioNome": "Exemplo",
    "codigoMunicipio": "4205407"
  },
  "esferaId": "M",
  "poderId": "E",
  "linkSistemaOrigem": "https://compras.exemplo.sc.gov.br/pregao/1",
  "linkProcessoEletronico": "https://pncp.gov.br/app/editais/..."
}
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-03 | @data-engineer | Initial schema design |
