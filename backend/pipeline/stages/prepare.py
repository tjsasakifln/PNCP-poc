"""Stage 2: PrepareSearch — parse terms, configure sector, build query params.

Extracted from SearchPipeline.stage_prepare (DEBT-015 SYS-002).
"""

import logging

from sectors import get_sector
from term_parser import parse_search_terms
from relevance import calculate_min_matches
from search_context import SearchContext
from fastapi import HTTPException

logger = logging.getLogger(__name__)


async def stage_prepare(pipeline, ctx: SearchContext) -> None:
    """Load sector, parse custom terms, configure keywords and exclusions."""
    # Override dates for "abertas" mode — search_datalake RPC ignores dates
    # for "abertas" (only filters by data_encerramento > now()), but we still
    # need valid values for cache key compatibility and logging.
    if ctx.request.modo_busca == "abertas":
        from datetime import timedelta, timezone, datetime as dt
        today = dt.now(timezone.utc).date()
        # Wide window — effectively "all time". The RPC ignores these for "abertas".
        _days = 730
        ctx.request.data_inicial = (today - timedelta(days=_days)).isoformat()
        ctx.request.data_final = today.isoformat()
        logger.info(
            f"modo_busca='abertas': dates set to wide range "
            f"{ctx.request.data_inicial} → {ctx.request.data_final} "
            f"(RPC ignores dates for abertas mode)"
        )

    # GTM-FIX-032 AC3.1: Normalize all dates to canonical YYYY-MM-DD
    from datetime import date as date_type
    d_ini = date_type.fromisoformat(ctx.request.data_inicial)
    d_fin = date_type.fromisoformat(ctx.request.data_final)
    ctx.request.data_inicial = d_ini.isoformat()
    ctx.request.data_final = d_fin.isoformat()
    logger.debug(f"stage_prepare: dates normalized to {ctx.request.data_inicial} → {ctx.request.data_final}")

    # ISSUE-017: setor_id=None means "Termos Específicos" mode — no sector, custom terms only
    if ctx.request.setor_id:
        try:
            ctx.sector = get_sector(ctx.request.setor_id)
        except KeyError as e:
            raise HTTPException(status_code=400, detail=str(e))
        logger.debug(f"Using sector: {ctx.sector.name} ({len(ctx.sector.keywords)} keywords)")
    else:
        ctx.sector = None
        logger.debug("No sector selected — using custom terms only (Termos Específicos mode)")

    ctx.custom_terms = []
    ctx.stopwords_removed = []
    ctx.min_match_floor_value = None

    if ctx.request.termos_busca and ctx.request.termos_busca.strip():
        parsed_terms = parse_search_terms(ctx.request.termos_busca)
        validated = pipeline.deps.validate_terms(parsed_terms)

        if not validated['valid']:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Nenhum termo válido para busca",
                    "termos_ignorados": validated['ignored'],
                    "motivos_ignorados": validated['reasons'],
                    "sugestao": "Use termos mais específicos (mínimo 4 caracteres, evite palavras comuns como 'de', 'da', etc.)"
                }
            )

        ctx.custom_terms = validated['valid']
        ctx.stopwords_removed = validated['ignored']

        logger.debug(
            f"Term validation: {len(ctx.custom_terms)} valid, {len(ctx.stopwords_removed)} ignored. "
            f"Valid={ctx.custom_terms}, Ignored={list(validated['reasons'].keys())}"
        )

        if ctx.custom_terms and not ctx.request.show_all_matches:
            ctx.min_match_floor_value = calculate_min_matches(len(ctx.custom_terms))
            logger.debug(
                f"Min match floor: {ctx.min_match_floor_value} "
                f"(total_terms={len(ctx.custom_terms)})"
            )

    if ctx.custom_terms:
        ctx.active_keywords = set(ctx.custom_terms)
        logger.debug(f"Using {len(ctx.custom_terms)} custom search terms: {ctx.custom_terms}")
    elif ctx.sector:
        ctx.active_keywords = set(ctx.sector.keywords)
        logger.debug(f"Using sector keywords ({len(ctx.active_keywords)} terms)")
    else:
        # ISSUE-017: No sector + no custom terms — empty keywords (should not happen in practice)
        ctx.active_keywords = set()
        logger.warning("No sector and no custom terms — active_keywords is empty")

    # Determine exclusions
    # ISSUE-017: When sector is None (Termos Específicos), no sector exclusions apply
    if ctx.request.exclusion_terms:
        ctx.active_exclusions = set(ctx.request.exclusion_terms)
        ctx.active_context_required = None
    elif ctx.sector is None:
        # No sector = no sector exclusions
        ctx.active_exclusions = set()
        ctx.active_context_required = None
    elif ctx.custom_terms and ctx.request.setor_id and ctx.request.setor_id != "vestuario":
        ctx.active_exclusions = ctx.sector.exclusions
        ctx.active_context_required = ctx.sector.context_required_keywords
    elif not ctx.custom_terms:
        ctx.active_exclusions = ctx.sector.exclusions
        ctx.active_context_required = ctx.sector.context_required_keywords
    else:
        # STORY-267 AC11: custom_terms + vestuario — apply PARTIAL exclusions
        # Remove exclusions that contain any of the user's custom terms (avoid self-exclusion)
        # Keep exclusions unrelated to custom terms (reduce noise)
        from config import get_feature_flag
        if get_feature_flag("TERM_SEARCH_FILTER_CONTEXT"):
            all_exclusions = ctx.sector.exclusions
            terms_lower = {t.lower() for t in ctx.custom_terms}
            partial_exclusions = set()
            for exc in all_exclusions:
                exc_lower = exc.lower()
                # Keep exclusion only if it does NOT contain any custom term
                if not any(term in exc_lower for term in terms_lower):
                    partial_exclusions.add(exc)
            removed_count = len(all_exclusions) - len(partial_exclusions)
            if removed_count > 0:
                logger.debug(
                    f"STORY-267 AC11: Removed {removed_count} self-exclusions "
                    f"for custom terms {ctx.custom_terms}"
                )
            ctx.active_exclusions = partial_exclusions
        else:
            ctx.active_exclusions = set()
        ctx.active_context_required = None

    # STORY-260 AC5: Load user profile for LLM analysis
    try:
        from supabase_client import get_supabase, sb_execute
        _db = get_supabase()
        _profile_row = await sb_execute(
            _db.table("profiles").select("context_data").eq("id", ctx.user["id"]).single()
        )
        ctx.user_profile = (_profile_row.data or {}).get("context_data") or {}
    except Exception as _prof_err:
        logger.debug(f"Could not load user profile: {_prof_err}")
        ctx.user_profile = None

    # SSE: Sector ready
    if ctx.tracker:
        if ctx.sector:
            await ctx.tracker.emit("connecting", 8, f"Setor '{ctx.sector.name}' configurado, conectando ao PNCP...")
        else:
            _terms_label = ctx.request.termos_busca or "termos específicos"
            await ctx.tracker.emit("connecting", 8, f"Busca por '{_terms_label}' configurada, conectando ao PNCP...")
