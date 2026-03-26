"""ARQ Worker entry points for search pipeline execution.

GTM-ARCH-001: Standalone functions for ARQ Worker consumption.
DEBT-015 SYS-002: Extracted from search_pipeline.py.
"""

from types import SimpleNamespace


def build_default_deps() -> SimpleNamespace:
    """GTM-ARCH-001 AC2: Build default deps namespace for Worker context."""
    from config import ENABLE_NEW_PRICING
    from pncp_client import PNCPClient, buscar_todas_ufs_paralelo
    from filter import (
        aplicar_todos_filtros,
        match_keywords,
        KEYWORDS_UNIFORMES,
        KEYWORDS_EXCLUSAO,
        validate_terms,
    )
    from excel import create_excel
    from rate_limiter import rate_limiter
    from authorization import check_user_roles

    return SimpleNamespace(
        ENABLE_NEW_PRICING=ENABLE_NEW_PRICING,
        PNCPClient=PNCPClient,
        buscar_todas_ufs_paralelo=buscar_todas_ufs_paralelo,
        aplicar_todos_filtros=aplicar_todos_filtros,
        create_excel=create_excel,
        rate_limiter=rate_limiter,
        check_user_roles=check_user_roles,
        match_keywords=match_keywords,
        KEYWORDS_UNIFORMES=KEYWORDS_UNIFORMES,
        KEYWORDS_EXCLUSAO=KEYWORDS_EXCLUSAO,
        validate_terms=validate_terms,
    )


async def executar_busca_completa(
    search_id: str,
    request_data: dict,
    user_data: dict,
    tracker=None,
    quota_pre_consumed: bool = False,
    deadline_ts: float | None = None,
) -> "BuscaResponse":  # noqa: F821
    """GTM-ARCH-001 AC2 + CRIT-072 AC8: Execute full search pipeline.

    Designed for ARQ Worker. Reconstructs BuscaRequest and SearchContext
    from serializable dicts, builds default deps, and runs the 7-stage pipeline.
    """
    from schemas import BuscaRequest
    from search_context import SearchContext
    from progress import get_tracker, create_tracker
    import time as _time

    request = BuscaRequest(**request_data)
    request.search_id = search_id

    if tracker is None:
        tracker = await get_tracker(search_id)
    if tracker is None:
        tracker = await create_tracker(search_id, len(request.ufs))

    deps = build_default_deps()

    from search_pipeline import SearchPipeline
    pipeline = SearchPipeline(deps)
    ctx = SearchContext(
        request=request,
        user=user_data,
        tracker=tracker,
        start_time=_time.time(),
        quota_pre_consumed=quota_pre_consumed,
    )
    ctx.deadline_ts = deadline_ts

    return await pipeline.run(ctx)
