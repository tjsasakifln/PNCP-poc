"""Data models for multi-source consolidation."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import hashlib
import re


class SourceStatus(Enum):
    """Health status of a procurement source."""
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class SourceCapability(Enum):
    """Optional capabilities a source may support."""
    FILTER_BY_UF = "filter_by_uf"
    FILTER_BY_VALUE = "filter_by_value"
    FILTER_BY_KEYWORD = "filter_by_keyword"
    PAGINATION = "pagination"
    DATE_RANGE = "date_range"
    REAL_TIME = "real_time"


@dataclass
class SourceMetadata:
    """Metadata about a procurement source."""
    name: str
    code: str
    base_url: str
    documentation_url: Optional[str] = None
    capabilities: Set[SourceCapability] = field(default_factory=set)
    rate_limit_rps: float = 10.0
    typical_response_ms: int = 5000
    priority: int = 100  # Lower = higher priority


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
    source_name: str
    dedup_key: str = ""

    # === Core Fields (REQUIRED) ===
    objeto: str = ""
    valor_estimado: float = 0.0
    orgao: str = ""
    cnpj_orgao: str = ""
    uf: str = ""
    municipio: str = ""
    data_publicacao: Optional[datetime] = None

    # === Optional Fields ===
    data_abertura: Optional[datetime] = None
    data_encerramento: Optional[datetime] = None
    numero_edital: str = ""
    ano: str = ""
    modalidade: str = ""
    situacao: str = ""
    esfera: str = ""
    poder: str = ""

    # === Links ===
    link_edital: str = ""
    link_portal: str = ""

    # === Metadata ===
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    raw_data: Optional[Dict[str, Any]] = field(default=None, repr=False)

    # === Consolidation tracking ===
    matched_sources: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate and normalize fields after initialization."""
        self.source_id = str(self.source_id) if self.source_id else ""
        self.uf = self.uf.upper().strip() if self.uf else ""
        if self.valor_estimado is None:
            self.valor_estimado = 0.0
        if not self.dedup_key:
            self.dedup_key = self._generate_dedup_key()
        if not self.matched_sources:
            self.matched_sources = [self.source_name]

    def _generate_dedup_key(self) -> str:
        """Generate deduplication key from record attributes."""
        cnpj_clean = re.sub(r"[^\d]", "", self.cnpj_orgao) if self.cnpj_orgao else ""

        if self.numero_edital and self.ano:
            return f"{cnpj_clean}:{self.numero_edital}:{self.ano}"

        if self.objeto:
            objeto_normalized = " ".join(self.objeto.lower().split())
            objeto_hash = hashlib.md5(objeto_normalized.encode()).hexdigest()[:12]
            return f"{cnpj_clean}:{objeto_hash}:{int(self.valor_estimado)}"

        return f"{self.source_name}:{self.source_id}"

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
            "matched_sources": self.matched_sources,
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
            "_source": self.source_name,
            "_dedup_key": self.dedup_key,
            "_matched_sources": self.matched_sources,
        }


@dataclass
class SourceStats:
    """Statistics for a single source fetch."""
    count: int
    duration_ms: int
    status: SourceStatus
    pages_fetched: int = 0
    rate_limited: bool = False


@dataclass
class ConsolidationResult:
    """Result of multi-source consolidation."""

    # === Records ===
    items: List[UnifiedProcurement]

    # === Source tracking ===
    sources_queried: List[str]
    sources_failed: List[str]

    # === Counts ===
    total_before_dedup: int
    total_after_dedup: int

    # === Timing ===
    execution_time_ms: int

    # === Per-Source Stats ===
    source_stats: Dict[str, SourceStats] = field(default_factory=dict)

    # === Errors ===
    errors: Dict[str, str] = field(default_factory=dict)

    # === Timestamps ===
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def duplicates_removed(self) -> int:
        """Number of duplicates removed during deduplication."""
        return self.total_before_dedup - self.total_after_dedup

    @property
    def sources_succeeded(self) -> int:
        """Number of sources that returned successfully."""
        return len(self.source_stats)

    @property
    def success_rate(self) -> float:
        """Percentage of sources that succeeded."""
        total = len(self.sources_queried)
        return (self.sources_succeeded / total * 100) if total > 0 else 0.0

    @property
    def has_partial_results(self) -> bool:
        """True if some but not all sources failed."""
        return len(self.sources_failed) > 0 and self.sources_succeeded > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "items": [item.to_dict() for item in self.items],
            "sources_queried": self.sources_queried,
            "sources_failed": self.sources_failed,
            "total_before_dedup": self.total_before_dedup,
            "total_after_dedup": self.total_after_dedup,
            "duplicates_removed": self.duplicates_removed,
            "execution_time_ms": self.execution_time_ms,
            "source_stats": {
                k: {
                    "count": v.count,
                    "duration_ms": v.duration_ms,
                    "status": v.status.value,
                    "pages_fetched": v.pages_fetched,
                    "rate_limited": v.rate_limited,
                }
                for k, v in self.source_stats.items()
            },
            "errors": self.errors,
            "sources_succeeded": self.sources_succeeded,
            "success_rate": self.success_rate,
            "has_partial_results": self.has_partial_results,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
