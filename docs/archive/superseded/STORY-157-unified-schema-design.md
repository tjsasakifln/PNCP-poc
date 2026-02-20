# Story MSP-001-02: Unified Schema Design

**Story ID:** MSP-001-02
**GitHub Issue:** #157 (to be created)
**Epic:** MSP-001 (Multi-Source Procurement Consolidation)
**Sprint:** TBD
**Owner:** @data-engineer
**Created:** February 3, 2026

---

## Story

**As a** data engineer,
**I want** a unified procurement data schema that normalizes data from all 5 sources,
**So that** downstream services can process procurement data uniformly regardless of origin.

---

## Objective

Design and document a comprehensive unified schema that:

1. Captures all essential procurement attributes
2. Normalizes heterogeneous source formats
3. Preserves source-specific data when needed
4. Supports efficient querying and filtering
5. Enables cross-source deduplication

---

## Acceptance Criteria

### AC1: Core Schema Definition
- [ ] Pydantic model created for `UnifiedProcurement`
- [ ] All required fields defined with types
- [ ] Optional fields properly annotated
- [ ] Validation rules implemented
- [ ] Schema documented with field descriptions

### AC2: Source-Specific Schemas
- [ ] Schema for PNCP data (existing, review for completeness)
- [ ] Schema for BLL Compras data
- [ ] Schema for Portal Compras Publicas data
- [ ] Schema for BNC data
- [ ] Schema for Licitar Digital data

### AC3: Transformation Layer
- [ ] Transformer interface defined
- [ ] PNCP transformer implemented/updated
- [ ] BLL transformer stub created
- [ ] PCP transformer stub created
- [ ] BNC transformer stub created
- [ ] Licitar transformer stub created

### AC4: Normalization Rules
- [ ] Modality normalization (map source codes to unified)
- [ ] Status normalization (Open, Closed, Suspended, etc.)
- [ ] Date format standardization
- [ ] Currency/value normalization
- [ ] Location normalization (UF, municipio)

### AC5: Deduplication Support
- [ ] Define unique identifier strategy
- [ ] Document matching criteria for duplicates
- [ ] Implement hash/fingerprint for comparison
- [ ] Handle priority when same bid on multiple sources

### AC6: Documentation
- [ ] Schema documentation in `docs/architecture/unified-schema.md`
- [ ] Field mapping table (source field -> unified field)
- [ ] Migration guide for existing code

---

## Technical Tasks

### Task 1: Analyze Existing PNCP Schema (1 SP)
- [ ] Review current `_normalize_item()` in pncp_client.py
- [ ] Document all fields currently used
- [ ] Identify missing fields needed for unified schema
- [ ] Map PNCP fields to proposed unified schema

### Task 2: Design Unified Schema (3 SP)
- [ ] Define `UnifiedProcurement` Pydantic model
- [ ] Define `SourceType` enum
- [ ] Define `ProcurementStatus` enum
- [ ] Define `Modality` enum (normalized)
- [ ] Add validators and field constraints
- [ ] Include `raw_data` for source preservation

### Task 3: Create Source Schemas (2 SP)
- [ ] `PNCPProcurement` schema
- [ ] `BLLProcurement` schema (based on research)
- [ ] `PCPProcurement` schema (based on research)
- [ ] `BNCProcurement` schema (based on research)
- [ ] `LicitarProcurement` schema (based on research)

### Task 4: Implement Transformer Interface (1.5 SP)
- [ ] Create abstract `BaseTransformer` class
- [ ] Implement `PNCPTransformer`
- [ ] Create stub transformers for other sources
- [ ] Add validation in transform pipeline

### Task 5: Documentation (0.5 SP)
- [ ] Write schema documentation
- [ ] Create field mapping reference
- [ ] Document normalization rules

---

## Schema Design (Draft)

### Unified Schema

```python
from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, HttpUrl, Field
from typing import Any

class SourceType(str, Enum):
    PNCP = "pncp"
    BLL = "bll"
    PCP = "pcp"       # Portal Compras Publicas
    BNC = "bnc"
    LICITAR = "licitar"

class ProcurementStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    AWARDED = "awarded"
    UNKNOWN = "unknown"

class UnifiedModality(str, Enum):
    PREGAO_ELETRONICO = "pregao_eletronico"
    PREGAO_PRESENCIAL = "pregao_presencial"
    CONCORRENCIA = "concorrencia"
    TOMADA_PRECOS = "tomada_precos"
    CONVITE = "convite"
    DISPENSA = "dispensa"
    INEXIGIBILIDADE = "inexigibilidade"
    RDC = "rdc"
    LEILAO = "leilao"
    CREDENCIAMENTO = "credenciamento"
    OTHER = "other"

class UnifiedProcurement(BaseModel):
    """Unified procurement record from any source."""

    # Identity
    id: str = Field(..., description="Internal UUID")
    source: SourceType = Field(..., description="Origin platform")
    source_id: str = Field(..., description="Original ID from source")
    source_url: HttpUrl | None = Field(None, description="Direct link")

    # Core Data
    objeto: str = Field(..., description="Procurement description")
    valor_estimado: float | None = Field(None, ge=0)
    modalidade: UnifiedModality = Field(...)
    modalidade_original: str | None = Field(None, description="Source-specific code")
    status: ProcurementStatus = Field(default=ProcurementStatus.UNKNOWN)

    # Location
    uf: str = Field(..., min_length=2, max_length=2)
    municipio: str | None = None

    # Organization
    orgao_nome: str = Field(..., description="Agency name")
    orgao_cnpj: str | None = Field(None, pattern=r"^\d{14}$")

    # Dates
    data_publicacao: date
    data_abertura: datetime | None = None
    data_encerramento: datetime | None = None

    # Metadata
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    raw_data: dict[str, Any] = Field(default_factory=dict)

    # Deduplication
    fingerprint: str | None = Field(None, description="Hash for dedup")

    class Config:
        use_enum_values = True
```

### Transformer Interface

```python
from abc import ABC, abstractmethod

class BaseTransformer(ABC):
    """Abstract transformer for converting source data to unified schema."""

    @abstractmethod
    def transform(self, raw: dict) -> UnifiedProcurement:
        """Transform source-specific data to unified format."""
        pass

    @abstractmethod
    def validate_source_data(self, raw: dict) -> bool:
        """Validate source data before transformation."""
        pass

    def generate_fingerprint(self, procurement: UnifiedProcurement) -> str:
        """Generate deduplication fingerprint."""
        # Combine key fields for matching
        key = f"{procurement.orgao_cnpj}|{procurement.objeto[:100]}|{procurement.valor_estimado}"
        return hashlib.md5(key.encode()).hexdigest()
```

---

## Field Mapping Reference

| Unified Field | PNCP | BLL | PCP | BNC | Licitar |
|---------------|------|-----|-----|-----|---------|
| source_id | numeroControlePNCP | TBD | TBD | TBD | TBD |
| objeto | objetoCompra | TBD | TBD | TBD | TBD |
| valor_estimado | valorTotalEstimado | TBD | TBD | TBD | TBD |
| modalidade | codigoModalidadeContratacao | TBD | TBD | TBD | TBD |
| status | situacaoCompra | TBD | TBD | TBD | TBD |
| uf | unidadeOrgao.ufSigla | TBD | TBD | TBD | TBD |
| municipio | unidadeOrgao.municipioNome | TBD | TBD | TBD | TBD |
| orgao_nome | orgaoEntidade.razaoSocial | TBD | TBD | TBD | TBD |
| orgao_cnpj | orgaoEntidade.cnpj | TBD | TBD | TBD | TBD |
| data_publicacao | dataPublicacaoPncp | TBD | TBD | TBD | TBD |
| data_abertura | dataAberturaProposta | TBD | TBD | TBD | TBD |
| source_url | linkSistemaOrigem | TBD | TBD | TBD | TBD |

*TBD fields to be filled after research story (MSP-001-01) completes*

---

## Definition of Done

- [ ] All Pydantic models created and validated
- [ ] Transformer interface implemented
- [ ] PNCP transformer updated to use new schema
- [ ] Unit tests for all schemas (100% coverage)
- [ ] Unit tests for PNCP transformer
- [ ] Documentation complete
- [ ] Code reviewed by @architect

---

## Story Points: 8 SP

**Complexity:** Medium (clear requirements, standard patterns)
**Uncertainty:** Medium (depends on research findings)

---

## Dependencies

| Story | Dependency Type | Notes |
|-------|-----------------|-------|
| MSP-001-01 | Blocks this story | Need API research to complete field mappings |

---

## Blocks

- MSP-001-04 (Base Client Refactoring)
- MSP-001-05 through MSP-001-08 (All client implementations)

---

## Files to Create/Modify

### New Files
- `backend/schemas/unified_schema.py` - Unified Pydantic models
- `backend/schemas/source_schemas.py` - Source-specific models
- `backend/schemas/transformers.py` - Transformer implementations
- `backend/tests/test_unified_schema.py` - Schema tests
- `backend/tests/test_transformers.py` - Transformer tests
- `docs/architecture/unified-schema.md` - Documentation

### Modified Files
- `backend/pncp_client.py` - Update to use transformer
- `backend/filter.py` - Update to use unified schema
- `backend/excel.py` - Update to use unified schema

---

## References

- Epic: `docs/stories/epic-multi-source-procurement.md`
- Research Story: `docs/stories/STORY-156-api-research-discovery.md`
- Existing PNCP normalization: `backend/pncp_client.py` lines 375-398

---

**Story Status:** READY (pending dependency completion)
**Estimated Duration:** 3-4 days
**Priority:** P1 - Critical Path
