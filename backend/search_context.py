"""Search context dataclass — carries intermediate state across pipeline stages.

AC2: Each stage takes and returns a typed SearchContext dataclass.
AC3: SearchContext carries all intermediate state (raw results, filtered results, scores, etc.)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SearchContext:
    """Typed container for all intermediate state during a search pipeline execution.

    Each pipeline stage reads from and writes to this context. This ensures:
    - Stages are independently testable (construct context, call stage, assert results)
    - Failure in a later stage preserves results from earlier stages
    - No hidden shared state between stages
    """

    # === Input (set by caller) ===
    request: Any  # schemas.BuscaRequest
    user: dict
    start_time: float = field(default_factory=time.time)
    tracker: Any = None  # progress.ProgressTracker

    # === Stage 1: ValidateRequest outputs ===
    is_admin: bool = False
    is_master: bool = False
    quota_info: Any = None  # quota.QuotaInfo

    # === Stage 2: PrepareSearch outputs ===
    sector: Any = None  # sectors.Sector
    active_keywords: set = field(default_factory=set)
    custom_terms: list = field(default_factory=list)
    stopwords_removed: list = field(default_factory=list)
    min_match_floor_value: Optional[int] = None
    active_exclusions: set = field(default_factory=set)
    active_context_required: Optional[set] = None

    # === Stage 3: ExecuteSearch outputs ===
    licitacoes_raw: list = field(default_factory=list)
    source_stats_data: Optional[list] = None
    is_partial: bool = False
    data_sources: Optional[list] = None  # List[schemas.DataSourceStatus]
    degradation_reason: Optional[str] = None
    # STORY-257A: Partial results tracking
    failed_ufs: Optional[list] = None  # List of UF codes that failed
    succeeded_ufs: Optional[list] = None  # List of UF codes that succeeded
    # GTM-FIX-004: Truncation tracking
    is_truncated: bool = False  # True when any UF hit max_pages limit
    truncated_ufs: Optional[list] = None  # UF codes where data was truncated
    truncation_details: Optional[dict] = None  # Per-source truncation: {"pncp": True, "portal_compras": False}
    # GTM-FIX-010: SWR cache fields
    cached: bool = False  # True when serving stale cached results
    cached_at: Optional[str] = None  # ISO timestamp of cache creation
    cached_sources: Optional[list] = None  # Source codes in cached data
    cache_status: Optional[str] = None  # UX-303: "fresh" or "stale"
    cache_level: Optional[str] = None  # UX-303: "supabase", "redis", "local"
    # GTM-RESILIENCE-A01: Semantic response state
    response_state: str = "live"  # "live" | "cached" | "degraded" | "empty_failure"
    degradation_guidance: Optional[str] = None
    # GTM-RESILIENCE-A04: Progressive delivery
    live_fetch_in_progress: bool = False

    # === Stage 4: FilterResults outputs ===
    licitacoes_filtradas: list = field(default_factory=list)
    filter_stats: dict = field(default_factory=dict)
    hidden_by_min_match: int = 0
    filter_relaxed: bool = False

    # === Stage 5: EnrichResults (modifies licitacoes_filtradas in-place) ===

    # === Stage 6: GenerateOutput outputs ===
    resumo: Any = None  # schemas.ResumoLicitacoes
    excel_base64: Optional[str] = None
    download_url: Optional[str] = None
    excel_available: bool = False
    upgrade_message: Optional[str] = None
    licitacao_items: list = field(default_factory=list)

    # === Stage 7: Persist outputs ===
    session_id: Optional[str] = None
    response: Any = None  # schemas.BuscaResponse
