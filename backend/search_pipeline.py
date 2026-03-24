"""SearchPipeline — 7-stage orchestrator for procurement search.

DEBT-015 SYS-002: Thin orchestrator (<200 lines). Stage logic in pipeline/stages/.
"""

import logging
import time as sync_time_module
from types import SimpleNamespace

from search_context import SearchContext
from schemas import BuscaResponse
from metrics import SEARCH_DURATION, ACTIVE_SEARCHES, SEARCHES
from telemetry import get_tracer, optional_span
from pipeline.stages import (
    stage_validate, stage_prepare, stage_execute,
    stage_filter, stage_enrich, stage_generate, stage_persist,
)
from pipeline.tracing import traced_stage, validate_stage_outputs

logger = logging.getLogger(__name__)
_tracer = get_tracer("search_pipeline")

# State machine stages with their span names and SearchState values
_STAGE_TABLE = [
    ("VALIDATING", "pipeline.validate", "stage_validate"),
    (None, "pipeline.prepare", "stage_prepare"),
    ("FETCHING", "pipeline.fetch", "stage_execute"),
    ("FILTERING", "pipeline.filter", "stage_filter"),
    (None, None, "_time_budget_check"),  # synthetic entry for time budget
    ("ENRICHING", "pipeline.enrich", "stage_enrich"),
    ("GENERATING", "pipeline.generate", "stage_generate"),
    ("PERSISTING", "pipeline.persist", "stage_persist"),
]


class SearchPipeline:
    """7-stage search pipeline orchestrator.

    Emits search_complete structured log with fields:
    sources_attempted, sources_succeeded, sources_failed,
    cache_hit, total_results, total_filtered, latency_ms.
    """

    _EXCEL_ERROR_MSG = "Erro temporário ao gerar Excel"

    def __init__(self, deps: SimpleNamespace):
        self.deps = deps

    # Stage method wrappers — backward compat for tests calling pipeline.stage_X(ctx)
    async def stage_validate(self, ctx): return await stage_validate(self, ctx)
    async def stage_prepare(self, ctx): return await stage_prepare(self, ctx)
    async def stage_execute(self, ctx): return await stage_execute(self, ctx)
    async def stage_filter(self, ctx): return await stage_filter(self, ctx)
    async def stage_enrich(self, ctx): return await stage_enrich(self, ctx)
    async def stage_generate(self, ctx): return await stage_generate(self, ctx)
    async def stage_persist(self, ctx): return await stage_persist(self, ctx)

    async def _execute_multi_source(self, *a, **kw):
        from pipeline.stages.execute import _execute_multi_source
        return await _execute_multi_source(self, *a, **kw)

    async def _execute_pncp_only(self, *a, **kw):
        from pipeline.stages.execute import _execute_pncp_only
        return await _execute_pncp_only(self, *a, **kw)

    async def run(self, ctx: SearchContext) -> BuscaResponse:
        """Execute all 7 stages in sequence."""
        ACTIVE_SEARCHES.inc()
        logger.info("Starting procurement search", extra={
            "ufs": ctx.request.ufs, "setor_id": ctx.request.setor_id,
            "data_inicial": ctx.request.data_inicial, "data_final": ctx.request.data_final,
            "status": ctx.request.status.value if ctx.request.status else None,
            "modalidades": ctx.request.modalidades,
        })
        with optional_span(_tracer, "search_pipeline", {
            "search.id": getattr(ctx.request, "search_id", None) or "",
            "search.sector": ctx.request.setor_id or "",
            "search.ufs": ",".join(ctx.request.ufs),
            "search.user_id": ctx.user.get("id", "") if ctx.user else "",
        }) as root_span:
            return await self._run_stages(ctx, root_span)

    async def _run_stages(self, ctx: SearchContext, root_span) -> BuscaResponse:
        """Execute pipeline stages with state machine transitions."""
        from search_state_manager import get_state_machine
        from models.search_state import SearchState
        sm = get_state_machine(getattr(ctx.request, "search_id", None) or "")
        stage_fns = {
            "stage_validate": self.stage_validate,
            "stage_prepare": self.stage_prepare,
            "stage_execute": self.stage_execute,
            "stage_filter": self.stage_filter,
            "stage_enrich": self.stage_enrich,
            "stage_generate": self.stage_generate,
            "stage_persist": self.stage_persist,
        }

        try:
            for state_name, span_name, fn_key in _STAGE_TABLE:
                if fn_key == "_time_budget_check":
                    self._check_time_budget(ctx)
                    continue
                if sm and state_name:
                    await sm.transition_to(getattr(SearchState, state_name), stage=fn_key.replace("stage_", ""))
                await traced_stage(_tracer, ctx, span_name, stage_fns[fn_key])
            if sm:
                await sm.transition_to(SearchState.COMPLETED, stage="persist")
            return ctx.response
        finally:
            ACTIVE_SEARCHES.dec()
            elapsed_s = sync_time_module.time() - ctx.start_time
            SEARCH_DURATION.labels(
                sector=ctx.request.setor_id or "unknown",
                uf_count=str(len(ctx.request.ufs)),
                cache_status=ctx.cache_status or "miss",
            ).observe(elapsed_s)
            result_status = "success" if ctx.licitacoes_filtradas else ("empty" if not ctx.is_partial else "partial")
            SEARCHES.labels(
                sector=ctx.request.setor_id or "unknown",
                result_status=result_status,
                search_mode="terms" if ctx.custom_terms else "sector",
            ).inc()
            root_span.set_attribute("search.result_status", result_status)
            root_span.set_attribute("search.duration_ms", int(elapsed_s * 1000))
            root_span.set_attribute("search.total_raw", len(ctx.licitacoes_raw))
            root_span.set_attribute("search.total_filtered", len(ctx.licitacoes_filtradas))

    @staticmethod
    def _check_time_budget(ctx):
        """GTM-STAB-003 AC4: Skip LLM/viability if over time budget."""
        import asyncio
        elapsed = sync_time_module.time() - ctx.start_time
        if elapsed > 90 or ctx.is_deadline_expired():
            logger.warning(f"[STAB-003] Time budget exceeded ({elapsed:.1f}s > 90s) — skipping LLM")
            ctx.is_simplified = True
            if ctx.tracker:
                asyncio.get_event_loop().create_task(ctx.tracker.emit(
                    "filtering", 70, "Classificação IA ignorada (timeout)",
                    llm_skipped=True, reason="timeout",
                ))

    @staticmethod
    def _validate_stage_outputs(stage_name: str, ctx: SearchContext) -> None:
        return validate_stage_outputs(stage_name, ctx)
