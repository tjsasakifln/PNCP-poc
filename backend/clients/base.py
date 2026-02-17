"""Base classes for multi-source procurement adapters.

This module defines the abstract interface that all procurement source
adapters must implement, along with common data models and exceptions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Dict, Optional, Set
import hashlib
import re


class SourceStatus(Enum):
    """Health status of a procurement source."""

    AVAILABLE = "available"  # Fully operational
    DEGRADED = "degraded"  # Working but slow or partial
    UNAVAILABLE = "unavailable"  # Not responding


class SourceCapability(Enum):
    """Optional capabilities a source may support."""

    FILTER_BY_UF = "filter_by_uf"  # Server-side UF filtering
    FILTER_BY_VALUE = "filter_by_value"  # Server-side value range
    FILTER_BY_KEYWORD = "filter_by_keyword"  # Server-side keyword search
    PAGINATION = "pagination"  # Supports pagination
    DATE_RANGE = "date_range"  # Supports date range queries
    REAL_TIME = "real_time"  # Near real-time updates


@dataclass
class SourceMetadata:
    """Metadata about a procurement source."""

    name: str  # Human-readable name
    code: str  # Short code (e.g., "PNCP", "PORTAL_COMPRAS")
    base_url: str  # API base URL
    documentation_url: Optional[str] = None  # Link to API docs
    capabilities: Set[SourceCapability] = field(default_factory=set)
    rate_limit_rps: float = 10.0  # Max requests per second
    typical_response_ms: int = 2000  # Average response time
    priority: int = 100  # For dedup (lower = higher priority)


# ============ Custom Exceptions ============


class SourceError(Exception):
    """Base exception for source adapter errors.

    GTM-FIX-002 AC9: All SourceError subclasses include source_code attribute
    for Sentry tagging (data_source tag).
    """

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


class SourceAuthError(SourceAPIError):
    """Authentication failed."""

    def __init__(self, source_code: str, message: str = "Authentication failed"):
        super().__init__(source_code, 401, message)


class SourceParseError(SourceError):
    """Failed to parse source response."""

    def __init__(self, source_code: str, field_name: str, value: Any):
        super().__init__(source_code, f"Failed to parse {field_name}: {value!r}")
        self.field_name = field_name
        self.value = value


# ============ Unified Data Model ============


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
    """Source adapter code (e.g., 'PNCP', 'PORTAL_COMPRAS')."""

    dedup_key: str = ""
    """
    Deduplication key for identifying same procurement across sources.
    Generated from: normalized_cnpj:numero_edital:ano
    """

    # === Core Fields (REQUIRED) ===
    objeto: str = ""
    """Procurement object description."""

    valor_estimado: float = 0.0
    """Estimated total value in BRL. Use 0.0 if unknown."""

    orgao: str = ""
    """Name of the contracting government agency."""

    cnpj_orgao: str = ""
    """CNPJ of the contracting agency (with or without formatting)."""

    uf: str = ""
    """Brazilian state code (2 letters, e.g., 'SP', 'RJ')."""

    municipio: str = ""
    """Municipality name."""

    data_publicacao: Optional[datetime] = None
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

    raw_data: Optional[Dict[str, Any]] = field(default=None, repr=False)
    """Original raw data from source (for debugging)."""

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
        cnpj_clean = re.sub(r"[^\d]", "", self.cnpj_orgao) if self.cnpj_orgao else ""

        # If we have numero_edital and ano, use them
        if self.numero_edital and self.ano:
            return f"{cnpj_clean}:{self.numero_edital}:{self.ano}"

        # Fallback: use objeto hash and value
        objeto_normalized = " ".join(self.objeto.lower().split()) if self.objeto else ""
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
            "data_publicacao": (
                self.data_publicacao.isoformat() if self.data_publicacao else None
            ),
            "data_abertura": (
                self.data_abertura.isoformat() if self.data_abertura else None
            ),
            "data_encerramento": (
                self.data_encerramento.isoformat() if self.data_encerramento else None
            ),
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
            "dataPublicacaoPncp": (
                self.data_publicacao.isoformat() if self.data_publicacao else None
            ),
            "dataAberturaProposta": (
                self.data_abertura.isoformat() if self.data_abertura else None
            ),
            "modalidadeNome": self.modalidade,
            "situacaoCompraNome": self.situacao,
            "linkSistemaOrigem": self.link_edital,
            "linkProcessoEletronico": self.link_portal,
            # Source tracking (new fields)
            "_source": self.source_name,
            "_dedup_key": self.dedup_key,
        }


# ============ Abstract Base Class ============


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
        # This is required syntax for abstract async generator
        yield  # type: ignore

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
