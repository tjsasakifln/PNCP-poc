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

    # === GTM-ARCH-001: Async search flags ===
    quota_pre_consumed: bool = False  # AC8: True when quota consumed in POST before enqueue

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
    # STORY-306 AC5: Cache fallback from different date range
    cache_fallback: bool = False
    cache_date_range: Optional[str] = None
    # GTM-INFRA-003 AC6: Whether response came fully from cache (quota was skipped)
    from_cache: bool = False
    # GTM-RESILIENCE-A01: Semantic response state
    response_state: str = "live"  # "live" | "cached" | "degraded" | "empty_failure"
    degradation_guidance: Optional[str] = None
    # CRIT-053: Sources that returned 0 results due to degradation (canary fail, etc.)
    sources_degraded: list = field(default_factory=list)  # List[str] e.g. ["PNCP"]
    # GTM-RESILIENCE-A04: Progressive delivery
    live_fetch_in_progress: bool = False

    # === Stage 4: FilterResults outputs ===
    licitacoes_filtradas: list = field(default_factory=list)
    filter_stats: dict = field(default_factory=dict)
    hidden_by_min_match: int = 0
    filter_relaxed: bool = False
    # GTM-STAB-005 AC4: Auto-relaxation level (0=normal, 1=no floor, 2=no density, 3=top by value)
    relaxation_level: Optional[int] = None
    # GTM-STAB-003 AC4: True when time budget forced simplified processing
    is_simplified: bool = False
    # GTM-STAB-005 AC3: Human-readable filter summary when results=0
    filter_summary: Optional[str] = None

    # === Stage 5: EnrichResults (modifies licitacoes_filtradas in-place) ===

    # === Stage 6: GenerateOutput outputs ===
    resumo: Any = None  # schemas.ResumoLicitacoes
    excel_base64: Optional[str] = None
    download_url: Optional[str] = None
    excel_available: bool = False
    upgrade_message: Optional[str] = None
    licitacao_items: list = field(default_factory=list)
    # CRIT-005 AC13: LLM summary provenance tracking
    llm_source: Optional[str] = None  # "ai" | "fallback" | "processing"

    # === Stage 6b: Queue mode flag (GTM-RESILIENCE-F01) ===
    queue_mode: bool = False  # True when LLM/Excel dispatched to background jobs
    llm_status: Optional[str] = None  # "ready" | "processing" | None
    excel_status: Optional[str] = None  # "ready" | "processing" | "skipped" | "failed" | None

    # === STORY-259: Bid analysis ===
    bid_analysis_status: Optional[str] = None  # "ready" | "processing" | None

    # === STORY-260: User profile for LLM analysis ===
    user_profile: Optional[dict] = None  # Profile context data from profiles.context_data

    # === Stage 7: Persist outputs ===
    session_id: Optional[str] = None
    response: Any = None  # schemas.BuscaResponse
