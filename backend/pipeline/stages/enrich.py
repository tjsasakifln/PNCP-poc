"""Stage 5: EnrichResults — relevance scoring, viability, confidence re-ranking, sorting.

Extracted from SearchPipeline.stage_enrich + _enrich_with_sanctions (DEBT-015 SYS-002).
"""

import logging

from relevance import score_relevance, count_phrase_matches
from utils.ordenacao import ordenar_licitacoes
from search_context import SearchContext
from viability import assess_batch as viability_assess_batch

logger = logging.getLogger(__name__)


async def stage_enrich(pipeline, ctx: SearchContext) -> None:
    """Compute relevance scores, viability assessment, confidence-based re-ranking, and sorting."""

    # D-04 AC7: Viability assessment (Stage 4.5 — post-filter, pre-ranking)
    from config import get_feature_flag
    if get_feature_flag("VIABILITY_ASSESSMENT_ENABLED") and ctx.licitacoes_filtradas and not ctx.is_simplified:
        # Get sector-specific value range
        vr = None
        if ctx.sector and hasattr(ctx.sector, "viability_value_range"):
            vr = ctx.sector.viability_value_range
        ufs_busca = set(ctx.request.ufs) if ctx.request.ufs else set()
        viability_assess_batch(ctx.licitacoes_filtradas, ufs_busca, vr, user_profile=ctx.user_profile, custom_terms=ctx.custom_terms or None)
        # CRIT-FLT-003 AC4: Log zero-value proportion
        total = len(ctx.licitacoes_filtradas)
        zero_count = sum(
            1 for bid in ctx.licitacoes_filtradas
            if bid.get("_value_source") == "missing"
        )
        zero_pct = round(zero_count / total * 100, 1) if total else 0.0
        logger.info(
            "CRIT-FLT-003: zero_value_stats",
            extra={"zero_value_count": zero_count, "total_bids": total, "zero_value_pct": zero_pct},
        )
        logger.debug(
            f"D-04: Viability assessed for {total} bids. "
            f"Alta: {sum(1 for bid in ctx.licitacoes_filtradas if bid.get('_viability_level') == 'alta')}, "
            f"Media: {sum(1 for bid in ctx.licitacoes_filtradas if bid.get('_viability_level') == 'media')}, "
            f"Baixa: {sum(1 for bid in ctx.licitacoes_filtradas if bid.get('_viability_level') == 'baixa')}, "
            f"Zero-value: {zero_count}/{total} ({zero_pct}%)"
        )

    # Relevance scoring (STORY-178)
    if ctx.custom_terms and ctx.licitacoes_filtradas:
        for lic in ctx.licitacoes_filtradas:
            matched_terms = lic.get("_matched_terms", [])
            phrase_count = count_phrase_matches(matched_terms)
            lic["_relevance_score"] = score_relevance(
                len(matched_terms), len(ctx.custom_terms), phrase_count
            )

    # D-02 AC5 + D-04 AC9: Re-ranking by combined score when viability active
    # Falls back to confidence-only when viability is disabled
    if ctx.licitacoes_filtradas:
        viability_active = get_feature_flag("VIABILITY_ASSESSMENT_ENABLED") and any(
            bid.get("_viability_score") is not None for bid in ctx.licitacoes_filtradas
        )

        def _confidence_sort_key(lic: dict) -> tuple:
            conf = lic.get("_confidence_score", 50)
            valor = float(lic.get("valorTotalEstimado") or lic.get("valorEstimado") or 0)

            if viability_active:
                # D-04 AC9: combined_score = confidence * 0.6 + viability * 0.4
                viab = lic.get("_viability_score", 50)
                combined = conf * 0.6 + viab * 0.4
                lic["_combined_score"] = round(combined)
                return (-combined, -valor)

            # Band: 0=high(>=80), 1=medium(50-79), 2=low(<50)
            if conf >= 80:
                band = 0
            elif conf >= 50:
                band = 1
            else:
                band = 2
            return (band, -conf, -valor)

        ctx.licitacoes_filtradas.sort(key=_confidence_sort_key)
        logger.debug(
            f"D-02 AC5: Re-ranked {len(ctx.licitacoes_filtradas)} results by confidence. "
            f"High(>=80): {sum(1 for bid in ctx.licitacoes_filtradas if bid.get('_confidence_score', 50) >= 80)}, "
            f"Medium(50-79): {sum(1 for bid in ctx.licitacoes_filtradas if 50 <= bid.get('_confidence_score', 50) < 80)}, "
            f"Low(<50): {sum(1 for bid in ctx.licitacoes_filtradas if bid.get('_confidence_score', 50) < 50)}"
        )

    # User-requested sorting (applied AFTER confidence re-ranking for non-default)
    if ctx.licitacoes_filtradas and ctx.request.ordenacao != "data_desc":
        logger.debug(f"Applying user sorting: ordenacao='{ctx.request.ordenacao}'")
        ctx.licitacoes_filtradas = ordenar_licitacoes(
            ctx.licitacoes_filtradas,
            ordenacao=ctx.request.ordenacao,
            termos_busca=ctx.custom_terms if ctx.custom_terms else list(ctx.active_keywords)[:10],
        )

    if ctx.licitacoes_filtradas:
        import time as _sync_time
        filter_elapsed = _sync_time.time() - ctx.start_time
        logger.debug(
            f"Filtering and sorting complete in {filter_elapsed:.2f}s: "
            f"{len(ctx.licitacoes_filtradas)} results ordered by '{ctx.request.ordenacao}'"
        )
