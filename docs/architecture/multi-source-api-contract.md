# Multi-Source Consolidation API Contract

**Version:** 1.0
**Date:** 2026-02-03
**Status:** Proposed
**Author:** @architect (Aria)

---

## Overview

This document defines the API contract for the multi-source procurement consolidation system. It specifies:
1. The interface that all source adapters must implement
2. The unified procurement data model
3. Error handling contracts
4. Response format specifications

---

## 1. Source Adapter Interface

All procurement source adapters MUST implement this interface.

### 1.1 SourceAdapter Abstract Base Class

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import AsyncGenerator, Optional, Set, Dict, Any, List

class SourceStatus(Enum):
    """Health status of a procurement source."""
    AVAILABLE = "available"      # Fully operational
    DEGRADED = "degraded"        # Working but slow or partial
    UNAVAILABLE = "unavailable"  # Not responding

class SourceCapability(Enum):
    """Optional capabilities a source may support."""
    FILTER_BY_UF = "filter_by_uf"           # Server-side UF filtering
    FILTER_BY_VALUE = "filter_by_value"     # Server-side value range
    FILTER_BY_KEYWORD = "filter_by_keyword" # Server-side keyword search
    PAGINATION = "pagination"               # Supports pagination
    DATE_RANGE = "date_range"               # Supports date range queries
    REAL_TIME = "real_time"                 # Near real-time updates


@dataclass
class SourceMetadata:
    """Metadata about a procurement source."""
    name: str                              # Human-readable name
    code: str                              # Short code (e.g., "PNCP")
    base_url: str                          # API base URL
    documentation_url: Optional[str]       # Link to API docs
    capabilities: Set[SourceCapability]    # Supported capabilities
    rate_limit_rps: float                  # Max requests per second
    typical_response_ms: int               # Average response time
    priority: int = 100                    # For dedup (lower = higher priority)


class SourceAdapter(ABC):
    """
    Abstract base class for procurement source adapters.

    All source adapters MUST implement this interface to be used
    with the ConsolidationService.
    """

    @property
    @abstractmethod
    def metadata(self) -> SourceMetadata:
        """Return source metadata."""
        pass

    @property
    def name(self) -> str:
        """Human-readable source name."""
        return self.metadata.name

    @property
    def code(self) -> str:
        """Short code for logs/metrics."""
        return self.metadata.code

    @abstractmethod
    async def health_check(self) -> SourceStatus:
        """
        Check if source API is available.

        Returns:
            SourceStatus indicating current health

        Implementation notes:
            - MUST complete within 5 seconds
            - SHOULD use lightweight endpoint (e.g., HEAD request, health endpoint)
            - MUST NOT throw exceptions (return UNAVAILABLE instead)
        """
        pass

    @abstractmethod
    async def fetch(
        self,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator["UnifiedProcurement", None]:
        """
        Fetch procurement records from this source.

        Args:
            data_inicial: Start date in YYYY-MM-DD format
            data_final: End date in YYYY-MM-DD format
            ufs: Optional set of Brazilian state codes (e.g., {"SP", "RJ"})
            **kwargs: Source-specific parameters

        Yields:
            UnifiedProcurement records one at a time (for memory efficiency)

        Raises:
            SourceTimeoutError: If source doesn't respond in time
            SourceAPIError: If source returns an error response
            SourceRateLimitError: If rate limit exceeded

        Implementation notes:
            - MUST handle pagination internally
            - MUST apply rate limiting internally
            - MUST normalize records to UnifiedProcurement before yielding
            - SHOULD log progress for long-running fetches
            - MAY filter by UF client-side if source doesn't support it
        """
        pass

    @abstractmethod
    def normalize(self, raw_record: Dict[str, Any]) -> "UnifiedProcurement":
        """
        Convert source-specific record format to unified model.

        Args:
            raw_record: Raw record from source API

        Returns:
            UnifiedProcurement with all fields populated

        Implementation notes:
            - MUST set source_id and source_name
            - MUST generate dedup_key
            - MUST handle missing/null fields gracefully
            - SHOULD normalize text (remove extra whitespace, fix encoding)
        """
        pass

    async def close(self) -> None:
        """
        Clean up resources (HTTP sessions, connections, etc.).

        Called when adapter is no longer needed.
        """
        pass
```

### 1.2 Required Method Signatures

| Method | Return Type | Async | Description |
|--------|-------------|-------|-------------|
| `metadata` | `SourceMetadata` | No | Source configuration |
| `health_check()` | `SourceStatus` | Yes | API health check |
| `fetch(...)` | `AsyncGenerator[UnifiedProcurement]` | Yes | Fetch records |
| `normalize(raw)` | `UnifiedProcurement` | No | Convert to unified format |
| `close()` | `None` | Yes | Cleanup (optional) |

---

## 2. Unified Procurement Data Model

All procurement records, regardless of source, MUST be converted to this unified format.

### 2.1 UnifiedProcurement Dataclass

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import re
import hashlib

@dataclass
class UnifiedProcurement:
    """
    Unified procurement record format.

    This is the canonical representation of a procurement opportunity
    across all sources. All source adapters MUST convert their
    source-specific formats to this structure.
    """

    # === Identification (REQUIRED) ===
    source_id: str
    """Original unique identifier from the source system."""

    source_name: str
    """Source adapter code (e.g., 'PNCP', 'BLL')."""

    dedup_key: str
    """
    Deduplication key for identifying same procurement across sources.
    Generated from: normalized_cnpj:numero_edital:ano
    """

    # === Core Fields (REQUIRED) ===
    objeto: str
    """Procurement object description."""

    valor_estimado: float
    """Estimated total value in BRL. Use 0.0 if unknown."""

    orgao: str
    """Name of the contracting government agency."""

    cnpj_orgao: str
    """CNPJ of the contracting agency (with or without formatting)."""

    uf: str
    """Brazilian state code (2 letters, e.g., 'SP', 'RJ')."""

    municipio: str
    """Municipality name."""

    data_publicacao: datetime
    """Date/time when the procurement was published."""

    # === Optional Fields ===
    data_abertura: Optional[datetime] = None
    """Date/time when proposals can be submitted/opened."""

    data_encerramento: Optional[datetime] = None
    """Deadline for proposal submission."""

    numero_edital: str = ""
    """Procurement notice number."""

    ano: str = ""
    """Year of the procurement process."""

    modalidade: str = ""
    """Procurement modality (e.g., 'Pregao Eletronico')."""

    situacao: str = ""
    """Current status (e.g., 'Publicada', 'Em andamento')."""

    esfera: str = ""
    """Government sphere: 'F'=Federal, 'E'=Estadual, 'M'=Municipal."""

    poder: str = ""
    """Government branch: 'E'=Executive, 'L'=Legislative, 'J'=Judiciary."""

    # === Links ===
    link_edital: str = ""
    """Direct link to procurement notice/documents."""

    link_portal: str = ""
    """Link to view on source portal."""

    # === Metadata ===
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    """When this record was fetched from the source."""

    raw_data: Optional[dict] = field(default=None, repr=False)
    """Original raw data from source (for debugging)."""

    # === Methods ===
    def __post_init__(self):
        """Validate and normalize fields after initialization."""
        # Ensure source_id is string
        self.source_id = str(self.source_id)

        # Normalize UF to uppercase
        self.uf = self.uf.upper().strip() if self.uf else ""

        # Ensure valor_estimado is float
        if self.valor_estimado is None:
            self.valor_estimado = 0.0

        # Generate dedup_key if not provided
        if not self.dedup_key:
            self.dedup_key = self._generate_dedup_key()

    def _generate_dedup_key(self) -> str:
        """Generate deduplication key from record attributes."""
        # Normalize CNPJ (digits only)
        cnpj_clean = re.sub(r"[^\d]", "", self.cnpj_orgao)

        # If we have numero_edital and ano, use them
        if self.numero_edital and self.ano:
            return f"{cnpj_clean}:{self.numero_edital}:{self.ano}"

        # Fallback: use objeto hash and value
        objeto_normalized = " ".join(self.objeto.lower().split())
        objeto_hash = hashlib.md5(objeto_normalized.encode()).hexdigest()[:12]
        return f"{cnpj_clean}:{objeto_hash}:{int(self.valor_estimado)}"

    def to_dict(self) -> dict:
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

    def to_legacy_format(self) -> dict:
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
```

### 2.2 Field Mapping Table

| Unified Field | PNCP | BLL | Portal | BNC | Licitar |
|--------------|------|-----|--------|-----|---------|
| `source_id` | `numeroControlePNCP` | `id` | `codigo` | `codigo_licitacao` | `processo_id` |
| `objeto` | `objetoCompra` | `descricao` | `objeto` | `objeto` | `descricao_objeto` |
| `valor_estimado` | `valorTotalEstimado` | `valor` | `valorEstimado` | `valor_total` | `valor_estimado` |
| `orgao` | `orgaoEntidade.razaoSocial` | `entidade.nome` | `orgao.nome` | `orgao_nome` | `entidade_nome` |
| `cnpj_orgao` | `orgaoEntidade.cnpj` | `entidade.cnpj` | `orgao.cnpj` | `orgao_cnpj` | `entidade_cnpj` |
| `uf` | `unidadeOrgao.ufSigla` | `estado` | `uf` | `uf` | `estado_sigla` |
| `municipio` | `unidadeOrgao.municipioNome` | `cidade` | `municipio` | `municipio` | `cidade_nome` |
| `data_publicacao` | `dataPublicacaoPncp` | `data_publicacao` | `dataPublicacao` | `dt_publicacao` | `publicado_em` |
| `data_abertura` | `dataAberturaProposta` | `data_abertura` | `dataAbertura` | `dt_abertura` | `abertura_propostas` |
| `modalidade` | `modalidadeNome` | `modalidade` | `tipoLicitacao` | `tipo` | `modalidade_nome` |
| `link_edital` | `linkSistemaOrigem` | `url_edital` | `linkDocumentos` | `link_edital` | `url_documentos` |

---

## 3. Consolidation Service Interface

### 3.1 ConsolidationResult

```python
@dataclass
class SourceStats:
    """Statistics for a single source."""
    count: int                  # Records returned
    duration_ms: int            # Time taken in milliseconds
    status: SourceStatus        # Health status at fetch time
    pages_fetched: int = 0      # Pagination info (if applicable)
    rate_limited: bool = False  # Whether rate limiting was hit

@dataclass
class ConsolidationResult:
    """Result of multi-source consolidation."""

    # === Records ===
    records: List[UnifiedProcurement]
    """Deduplicated procurement records."""

    # === Counts ===
    total_raw: int
    """Total records before deduplication."""

    total_deduplicated: int
    """Total records after deduplication."""

    duplicates_removed: int
    """Number of duplicates removed."""

    # === Per-Source Stats ===
    source_stats: Dict[str, SourceStats]
    """Statistics for each successful source."""

    # === Errors ===
    errors: Dict[str, str]
    """Source code -> error message for failed sources."""

    # === Timing ===
    duration_ms: int
    """Total consolidation time in milliseconds."""

    started_at: datetime
    """When consolidation started."""

    completed_at: datetime
    """When consolidation completed."""

    # === Computed Properties ===
    @property
    def sources_succeeded(self) -> int:
        """Number of sources that returned successfully."""
        return len(self.source_stats)

    @property
    def sources_failed(self) -> int:
        """Number of sources that failed."""
        return len(self.errors)

    @property
    def success_rate(self) -> float:
        """Percentage of sources that succeeded."""
        total = self.sources_succeeded + self.sources_failed
        return (self.sources_succeeded / total * 100) if total > 0 else 0.0

    @property
    def has_partial_results(self) -> bool:
        """True if some but not all sources failed."""
        return self.sources_failed > 0 and self.sources_succeeded > 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "records": [r.to_dict() for r in self.records],
            "total_raw": self.total_raw,
            "total_deduplicated": self.total_deduplicated,
            "duplicates_removed": self.duplicates_removed,
            "source_stats": {
                k: {
                    "count": v.count,
                    "duration_ms": v.duration_ms,
                    "status": v.status.value,
                }
                for k, v in self.source_stats.items()
            },
            "errors": self.errors,
            "duration_ms": self.duration_ms,
            "sources_succeeded": self.sources_succeeded,
            "sources_failed": self.sources_failed,
            "success_rate": self.success_rate,
            "has_partial_results": self.has_partial_results,
        }
```

### 3.2 ConsolidationService Methods

```python
class ConsolidationService:
    """Service for fetching and consolidating procurement from multiple sources."""

    async def fetch_all_sources(
        self,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]] = None,
        enabled_sources: Optional[Set[str]] = None,
    ) -> ConsolidationResult:
        """
        Fetch from all enabled sources in parallel.

        Args:
            data_inicial: Start date (YYYY-MM-DD)
            data_final: End date (YYYY-MM-DD)
            ufs: Optional set of state codes to filter
            enabled_sources: Optional set of source codes (default: all)

        Returns:
            ConsolidationResult with deduplicated records

        Raises:
            ValueError: If no sources are enabled
            RuntimeError: If all sources fail (when fail_on_all_errors=True)
        """
        pass

    async def fetch_single_source(
        self,
        source_code: str,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]] = None,
    ) -> List[UnifiedProcurement]:
        """
        Fetch from a single source (useful for testing).

        Args:
            source_code: Source adapter code (e.g., "PNCP")
            data_inicial: Start date
            data_final: End date
            ufs: Optional state filter

        Returns:
            List of records from that source

        Raises:
            KeyError: If source_code is not registered
            SourceAPIError: If source fails
        """
        pass

    async def health_check_all(self) -> Dict[str, SourceStatus]:
        """
        Check health of all registered sources.

        Returns:
            Dict mapping source code to health status
        """
        pass

    def get_available_sources(self) -> List[SourceMetadata]:
        """
        Get metadata for all registered sources.

        Returns:
            List of SourceMetadata objects
        """
        pass
```

---

## 4. Error Handling Contract

### 4.1 Custom Exceptions

```python
class SourceError(Exception):
    """Base exception for source adapter errors."""

    def __init__(self, source_code: str, message: str):
        self.source_code = source_code
        self.message = message
        super().__init__(f"[{source_code}] {message}")


class SourceTimeoutError(SourceError):
    """Source did not respond within timeout period."""

    def __init__(self, source_code: str, timeout_seconds: int):
        super().__init__(source_code, f"Timeout after {timeout_seconds}s")
        self.timeout_seconds = timeout_seconds


class SourceAPIError(SourceError):
    """Source API returned an error response."""

    def __init__(self, source_code: str, status_code: int, body: str = ""):
        super().__init__(source_code, f"HTTP {status_code}: {body[:200]}")
        self.status_code = status_code
        self.body = body


class SourceRateLimitError(SourceAPIError):
    """Source rate limit exceeded."""

    def __init__(self, source_code: str, retry_after: Optional[int] = None):
        super().__init__(source_code, 429, "Rate limit exceeded")
        self.retry_after = retry_after


class SourceParseError(SourceError):
    """Failed to parse source response."""

    def __init__(self, source_code: str, field: str, value: Any):
        super().__init__(source_code, f"Failed to parse {field}: {value!r}")
        self.field = field
        self.value = value


class DeduplicationError(Exception):
    """Error during deduplication process."""
    pass


class ConsolidationError(Exception):
    """Error during consolidation process."""

    def __init__(self, message: str, partial_result: Optional[ConsolidationResult] = None):
        super().__init__(message)
        self.partial_result = partial_result
```

### 4.2 Error Handling Matrix

| Error Type | HTTP Response | Retry? | User Message |
|------------|---------------|--------|--------------|
| Single source timeout | 200 (partial) | No | "Results from X sources. Y timed out." |
| Single source 5xx | 200 (partial) | Yes (3x) | "Results from X sources. Y unavailable." |
| Single source 4xx | 200 (partial) | No | "Results from X sources. Y returned error." |
| Single source rate limit | 200 (partial) | Yes (with delay) | "Results from X sources." |
| All sources timeout | 504 | No | "All sources timed out." |
| All sources fail | 502 | No | "No sources available." |
| Invalid date range | 400 | No | "Invalid date range." |
| No sources enabled | 400 | No | "No sources configured." |

---

## 5. HTTP API Response Format

### 5.1 Updated BuscaResponse

```python
class BuscaResponse(BaseModel):
    """Response schema for /buscar endpoint (multi-source version)."""

    # === Core Response (unchanged from v1) ===
    resumo: ResumoLicitacoes
    excel_base64: str
    total_raw: int
    total_filtrado: int
    filter_stats: Optional[FilterStats] = None
    termos_utilizados: Optional[List[str]] = None
    stopwords_removidas: Optional[List[str]] = None

    # === Multi-Source Extensions (new in v2) ===
    source_stats: Optional[Dict[str, Dict[str, Any]]] = None
    """Per-source statistics: {"PNCP": {"count": 100, "duration_ms": 4500}, ...}"""

    source_errors: Optional[Dict[str, str]] = None
    """Errors from failed sources: {"Portal": "Timeout after 30s"}"""

    deduplication_stats: Optional[Dict[str, int]] = None
    """Dedup info: {"total_before": 500, "total_after": 450, "duplicates": 50}"""

    consolidation_warning: Optional[str] = None
    """Warning if partial results due to source failures."""

    class Config:
        json_schema_extra = {
            "example": {
                "resumo": {"resumo_executivo": "..."},
                "excel_base64": "UEsDBB...",
                "total_raw": 523,
                "total_filtrado": 15,
                "source_stats": {
                    "PNCP": {"count": 300, "duration_ms": 4500},
                    "BLL": {"count": 223, "duration_ms": 3200}
                },
                "source_errors": {
                    "Portal": "Timeout after 30s"
                },
                "deduplication_stats": {
                    "total_before": 523,
                    "total_after": 450,
                    "duplicates": 73
                },
                "consolidation_warning": "1 of 3 sources failed. Results may be incomplete."
            }
        }
```

### 5.2 Updated BuscaRequest

```python
class BuscaRequest(BaseModel):
    """Request schema for /buscar endpoint (multi-source version)."""

    # === Core Fields (unchanged) ===
    ufs: List[str] = Field(..., min_length=1)
    data_inicial: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    data_final: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    setor_id: str = Field(default="vestuario")
    termos_busca: Optional[str] = None

    # === Multi-Source Extensions (new in v2) ===
    sources: Optional[List[str]] = Field(
        default=None,
        description="List of source codes to query (default: all available)"
    )
    """
    Examples:
    - null/omitted: Query all enabled sources
    - ["PNCP"]: Query only PNCP
    - ["PNCP", "BLL"]: Query PNCP and BLL
    """

    dedup_strategy: Optional[str] = Field(
        default="first_seen",
        description="Deduplication strategy: first_seen, most_recent, highest_value"
    )

    include_source_metadata: bool = Field(
        default=False,
        description="Include _source field in each record"
    )
```

---

## 6. Backward Compatibility

### 6.1 API Compatibility

The v2 API is **backward compatible** with v1:
- All v1 request fields remain supported
- All v1 response fields remain in the same location
- New fields are optional additions
- Default behavior (no `sources` specified) queries all sources including PNCP

### 6.2 Data Format Compatibility

The `UnifiedProcurement.to_legacy_format()` method ensures records can be passed to existing:
- `filter.py` - Uses `objetoCompra`, `valorTotalEstimado`, `uf`, etc.
- `excel.py` - Uses same field names
- `llm.py` - Uses same field names

---

## 7. Testing Contract

### 7.1 Adapter Test Requirements

Each adapter MUST pass these tests:

```python
class AdapterTestContract:
    """Tests that all adapters must pass."""

    async def test_implements_interface(self, adapter: SourceAdapter):
        """Adapter must implement all required methods."""
        assert hasattr(adapter, 'metadata')
        assert hasattr(adapter, 'health_check')
        assert hasattr(adapter, 'fetch')
        assert hasattr(adapter, 'normalize')

    async def test_health_check_returns_valid_status(self, adapter: SourceAdapter):
        """health_check must return valid SourceStatus."""
        status = await adapter.health_check()
        assert isinstance(status, SourceStatus)

    async def test_fetch_yields_unified_procurement(self, adapter: SourceAdapter):
        """fetch must yield UnifiedProcurement objects."""
        async for record in adapter.fetch("2026-01-01", "2026-01-07"):
            assert isinstance(record, UnifiedProcurement)
            assert record.source_id
            assert record.source_name == adapter.code
            assert record.dedup_key
            break  # Just test first record

    async def test_normalize_handles_missing_fields(self, adapter: SourceAdapter):
        """normalize must handle records with missing fields."""
        minimal_record = {"id": "test-123"}
        result = adapter.normalize(minimal_record)
        assert isinstance(result, UnifiedProcurement)
        assert result.source_id == "test-123"
        assert result.valor_estimado == 0.0  # Default value

    async def test_fetch_respects_uf_filter(self, adapter: SourceAdapter):
        """fetch should filter by UF when provided."""
        # Source-specific test if capability exists
        pass
```

---

**END OF API CONTRACT**
