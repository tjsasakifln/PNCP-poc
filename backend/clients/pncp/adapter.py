"""PNCPLegacyAdapter and module-level buscar_todas_ufs_paralelo convenience function.

Extracted from async_client.py to keep each file under 700 LOC.
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List

from clients.pncp.circuit_breaker import _circuit_breaker
from clients.pncp.retry import ParallelFetchResult

logger = logging.getLogger(__name__)


# ============================================================================
# PNCPLegacyAdapter — SourceAdapter wrapper for ConsolidationService (AC6)
# ============================================================================

class PNCPLegacyAdapter:
    """Wraps existing PNCPClient as a SourceAdapter for multi-source consolidation.

    STORY-216 AC6: Moved from inline class inside buscar_licitacoes() to module level.
    Accepts constructor parameters instead of capturing enclosing scope variables.

    This class conforms to the SourceAdapter interface (clients.base) but the import
    is deferred to avoid making pncp_client.py depend on clients.base at module level.
    The consolidation service only checks for the required methods at runtime.
    """

    def __init__(
        self,
        ufs: List[str],
        modalidades: List[int] | None = None,
        status: str | None = None,
        on_uf_complete: Callable | None = None,
        on_uf_status: Callable | None = None,
    ):
        self._ufs = ufs
        self._modalidades = modalidades
        self._status = status
        self._on_uf_complete = on_uf_complete
        self._on_uf_status = on_uf_status
        # GTM-FIX-004: Truncation detection for PNCP in multi-source mode
        self.was_truncated: bool = False
        self.truncated_ufs: List[str] = []

    @property
    def metadata(self):
        from clients.base import SourceMetadata, SourceCapability
        return SourceMetadata(
            name="PNCP", code="PNCP",
            base_url="https://pncp.gov.br/api/consulta/v1",
            capabilities={SourceCapability.PAGINATION, SourceCapability.DATE_RANGE, SourceCapability.FILTER_BY_UF},
            rate_limit_rps=10.0, priority=1,
        )

    @property
    def name(self) -> str:
        """Human-readable source name (GTM-FIX-024 T1)."""
        return self.metadata.name

    @property
    def code(self) -> str:
        """Short code for logs/metrics (GTM-FIX-024 T1)."""
        return self.metadata.code

    async def health_check(self):
        from clients.base import SourceStatus
        if _circuit_breaker.is_degraded:
            return SourceStatus.DEGRADED
        return SourceStatus.AVAILABLE

    async def fetch(self, data_inicial, data_final, ufs=None, **kwargs):
        from clients.base import UnifiedProcurement
        _ufs = list(ufs) if ufs else self._ufs
        if len(_ufs) > 1:
            fetch_result = await buscar_todas_ufs_paralelo(
                ufs=_ufs, data_inicial=data_inicial, data_final=data_final,
                modalidades=self._modalidades, status=self._status,
                max_concurrent=10, on_uf_complete=self._on_uf_complete,
                on_uf_status=self._on_uf_status,
            )
            if isinstance(fetch_result, ParallelFetchResult):
                results = fetch_result.items
                # GTM-FIX-004: Capture truncation state for multi-source propagation
                if fetch_result.truncated_ufs:
                    self.was_truncated = True
                    self.truncated_ufs = fetch_result.truncated_ufs
            else:
                results = fetch_result
        else:
            # W1-PR2: Use AsyncPNCPClient directly instead of wrapping sync
            # PNCPClient in asyncio.to_thread(). We're already in async context,
            # and buscar_todas_ufs_paralelo handles single-UF lists fine.
            # This eliminates the to_thread overhead and the sync requests dependency
            # on this code path.
            fetch_result = await buscar_todas_ufs_paralelo(
                ufs=_ufs, data_inicial=data_inicial, data_final=data_final,
                modalidades=self._modalidades, status=self._status,
                max_concurrent=10, on_uf_complete=self._on_uf_complete,
                on_uf_status=self._on_uf_status,
            )
            if isinstance(fetch_result, ParallelFetchResult):
                results = fetch_result.items
                if fetch_result.truncated_ufs:
                    self.was_truncated = True
                    self.truncated_ufs = fetch_result.truncated_ufs
            else:
                results = fetch_result
        for item in results:
            # GTM-FIX-017: Parse date fields from PNCP response
            data_pub = None
            if item.get("dataPublicacaoPncp"):
                try:
                    data_pub = datetime.fromisoformat(item["dataPublicacaoPncp"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass

            data_enc = None
            if item.get("dataEncerramentoProposta"):
                try:
                    data_enc = datetime.fromisoformat(item["dataEncerramentoProposta"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass

            data_abertura = None
            if item.get("dataAberturaProposta"):
                try:
                    data_abertura = datetime.fromisoformat(item["dataAberturaProposta"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass

            yield UnifiedProcurement(
                source_id=item.get("codigoCompra", ""),
                source_name="PNCP",
                objeto=item.get("objetoCompra", ""),
                valor_estimado=item.get("valorTotalEstimado", 0) or 0,
                orgao=item.get("nomeOrgao", ""),
                cnpj_orgao=item.get("cnpjOrgao", ""),
                uf=item.get("uf", ""),
                municipio=item.get("municipio", ""),
                data_publicacao=data_pub,
                data_abertura=data_abertura,
                data_encerramento=data_enc,
                numero_edital=item.get("numeroEdital", ""),
                ano=item.get("anoCompra", ""),
                esfera=item.get("esferaId", ""),
                modalidade=item.get("modalidadeNome", ""),
                modalidade_id=item.get("modalidadeId"),
                situacao=item.get("situacaoCompraNome", ""),
                link_edital=item.get("linkSistemaOrigem", ""),
                link_portal=item.get("linkProcessoEletronico", ""),
                raw_data=item,
            )

    def normalize(self, raw_record):
        pass

    async def close(self):
        pass


async def buscar_todas_ufs_paralelo(
    ufs: List[str],
    data_inicial: str,
    data_final: str,
    modalidades: List[int] | None = None,
    status: str | None = None,
    max_concurrent: int = 10,
    on_uf_complete: Callable[[str, int], Any] | None = None,
    on_uf_status: Callable[..., Any] | None = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function for parallel UF search.

    Creates an AsyncPNCPClient and performs parallel search in a single call.
    Use this for simple cases where you don't need to reuse the client.

    Args:
        ufs: List of state codes
        data_inicial: Start date YYYY-MM-DD
        data_final: End date YYYY-MM-DD
        modalidades: Optional modality codes
        status: Optional status filter
        max_concurrent: Maximum concurrent requests (default 10)
        on_uf_complete: Optional async callback(uf, items_count) called per UF
        on_uf_status: Optional async callback(uf, status, **detail) for per-UF status events

    Returns:
        List of procurement records

    Example:
        >>> results = await buscar_todas_ufs_paralelo(
        ...     ufs=["SP", "RJ"],
        ...     data_inicial="2026-01-01",
        ...     data_final="2026-01-15"
        ... )
    """
    from clients.pncp.async_client import AsyncPNCPClient
    async with AsyncPNCPClient(max_concurrent=max_concurrent) as client:
        return await client.buscar_todas_ufs_paralelo(
            ufs=ufs,
            data_inicial=data_inicial,
            data_final=data_final,
            modalidades=modalidades,
            status=status,
            on_uf_complete=on_uf_complete,
            on_uf_status=on_uf_status,
        )
