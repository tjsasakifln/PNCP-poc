"""Stage 7: Persist — save search session to history and return response.

Extracted from SearchPipeline.stage_persist (DEBT-015 SYS-002).
"""

import json
import logging
import time as sync_time_module
from datetime import datetime, timezone as _tz

from search_context import SearchContext
from schemas import BuscaResponse
from pncp_client import get_circuit_breaker
from log_sanitizer import mask_user_id
from metrics import SEARCH_RESPONSE_STATE, PARTIAL_RESULTS_SERVED_TOTAL

import quota

logger = logging.getLogger(__name__)


async def stage_persist(pipeline, ctx: SearchContext) -> BuscaResponse:
    """Save search session to history and return response.

    Errors in session save do NOT fail the search request.
    """

    # CRIT-050 AC8: Ensure resumo is never None (fallback if stage_generate crashed)
    if ctx.resumo is None:
        from llm import gerar_resumo_fallback
        ctx.resumo = gerar_resumo_fallback(
            ctx.licitacoes_filtradas,
            sector_name=ctx.sector.name if ctx.sector else "geral",
        )

    # AC26: Emit structured log per search completion
    elapsed_ms = int((sync_time_module.time() - ctx.start_time) * 1000)
    # CRIT-005 AC3: Increment response state counter
    SEARCH_RESPONSE_STATE.labels(state=ctx.response_state).inc()
    # CRIT-053 AC7: Track partial results served
    if ctx.is_partial:
        PARTIAL_RESULTS_SERVED_TOTAL.inc()

    # Determine which sources were attempted, succeeded, and failed
    sources_attempted = []
    sources_succeeded = []
    sources_failed_with_reason = []

    if ctx.source_stats_data:
        # Multi-source path
        for stat in ctx.source_stats_data:
            src_code = stat.get("source_code", "unknown")
            sources_attempted.append(src_code)
            if stat.get("error"):
                sources_failed_with_reason.append({
                    "source": src_code,
                    "reason": stat["error"][:100]  # Truncate long error messages
                })
            elif stat.get("status") == "degraded":
                # CRIT-053 AC1: Degraded sources NOT counted as succeeded
                pass
            else:
                sources_succeeded.append(src_code)
    else:
        # PNCP-only path
        sources_attempted = ["PNCP"]
        if ctx.licitacoes_raw is not None:
            sources_succeeded = ["PNCP"]
        else:
            sources_failed_with_reason = [{"source": "PNCP", "reason": "unknown"}]

    # CRIT-052 AC4: Include canary telemetry in search_complete
    canary_info = getattr(ctx, "_pncp_canary_result", None) or {}
    logger.info(json.dumps({
        "event": "search_complete",
        "search_id": ctx.request.search_id or "no_id",
        "sources_attempted": sources_attempted,
        "sources_succeeded": sources_succeeded,
        "sources_failed": [s["source"] for s in sources_failed_with_reason],
        "cache_hit": ctx.cached,
        "pncp_circuit_breaker": "degraded" if get_circuit_breaker("pncp").is_degraded else "healthy",
        "pcp_circuit_breaker": "degraded" if get_circuit_breaker("pcp").is_degraded else "healthy",
        "comprasgov_circuit_breaker": "degraded" if get_circuit_breaker("comprasgov").is_degraded else "healthy",
        "pncp_canary_status": canary_info.get("cron_status", "unknown"),
        "pncp_canary_latency_ms": canary_info.get("latency_ms"),
        "sources_degraded": ctx.sources_degraded or [],
        "total_results": len(ctx.licitacoes_raw) if ctx.licitacoes_raw else 0,
        "total_filtered": len(ctx.licitacoes_filtradas) if ctx.licitacoes_filtradas else 0,
        "ufs_requested": len(ctx.request.ufs),
        "ufs_succeeded": len(ctx.succeeded_ufs) if ctx.succeeded_ufs else 0,
        "ufs_failed": len(ctx.failed_ufs) if ctx.failed_ufs else 0,
        "failed_ufs": ctx.failed_ufs or [],
        "is_partial": ctx.is_partial,
        "latency_ms": elapsed_ms,
    }))

    # CRIT-002 AC11: Update existing session OR fallback to full INSERT
    if ctx.user:
        total_filtered = len(ctx.licitacoes_filtradas) if ctx.licitacoes_filtradas else 0
        valor_total = ctx.resumo.valor_total if ctx.resumo else 0.0
        resumo_exec = ctx.resumo.resumo_executivo if ctx.resumo else None
        destaques_val = (ctx.resumo.destaques if ctx.licitacoes_filtradas else []) if ctx.resumo else None

        if ctx.session_id:
            # AC11: Session was pre-registered — UPDATE with results
            try:
                await quota.update_search_session_status(
                    ctx.session_id,
                    status="completed",
                    pipeline_stage="persist",
                    completed_at=datetime.now(_tz.utc).isoformat(),
                    duration_ms=elapsed_ms,
                    raw_count=len(ctx.licitacoes_raw) if ctx.licitacoes_raw else 0,
                    total_filtered=total_filtered,
                    valor_total=valor_total,
                    resumo_executivo=resumo_exec,
                    destaques=destaques_val,
                    response_state=ctx.response_state,
                )
                logger.debug(
                    f"Search session updated to completed: {ctx.session_id[:8]}*** "
                    f"for user {mask_user_id(ctx.user['id'])}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to update session {ctx.session_id[:8]}***: "
                    f"{type(e).__name__}: {e}",
                    exc_info=True,
                )
        else:
            # AC23: Fallback — no pre-registered session (graceful degradation)
            try:
                ctx.session_id = await quota.save_search_session(
                    user_id=ctx.user["id"],
                    sectors=[ctx.request.setor_id],
                    ufs=ctx.request.ufs,
                    data_inicial=ctx.request.data_inicial,
                    data_final=ctx.request.data_final,
                    custom_keywords=ctx.custom_terms if ctx.custom_terms else None,
                    total_raw=len(ctx.licitacoes_raw) if ctx.licitacoes_raw else 0,
                    total_filtered=total_filtered,
                    valor_total=valor_total,
                    resumo_executivo=resumo_exec,
                    destaques=destaques_val,
                )
                logger.debug(
                    f"Search session saved (fallback): {ctx.session_id[:8] if ctx.session_id else 'None'}*** "
                    f"for user {mask_user_id(ctx.user['id'])}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to save search session for user "
                    f"{mask_user_id(ctx.user['id'])}: {type(e).__name__}: {e}",
                    exc_info=True,
                )

    # If response was already built (e.g., empty results early return in stage_generate)
    if ctx.response is not None and not ctx.licitacoes_filtradas:
        return ctx.response

    return ctx.response
