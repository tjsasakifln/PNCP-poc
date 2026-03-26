"""DEBT-118 AC10: Synonym recovery logic for the filter pipeline.

Contains FLUXO 2: Anti-False Negative Recovery Pipeline, extracted
from aplicar_todos_filtros(). Recovers contracts incorrectly rejected
by keyword filters through 4 layers:

1. Camada 1B+2B: Synonym auto-match (2+ distinct synonym matches)
2. Camada 3B: LLM recovery for ambiguous synonym matches (1 match)
3. Camada 4: Zero-results relaxation (accept any 1+ synonym match)
"""

import logging
from typing import Dict, List, Optional, Set

from filter_keywords import _strip_org_context
from filter_utils import parse_valor

logger = logging.getLogger(__name__)


def run_synonym_recovery(
    aprovadas: List[dict],
    resultado_valor: List[dict],
    setor: Optional[str],
    custom_terms: Optional[List[str]],
    stats: Dict,
    llm_zero_match_active: bool,
) -> List[dict]:
    """Run FLUXO 2: Anti-False Negative Recovery Pipeline.

    Scans bids rejected at keyword stage and attempts recovery via
    synonym matching (deterministic) and LLM classification (fallback).

    Args:
        aprovadas: Currently approved bids (will be extended with recoveries).
        resultado_valor: All bids that passed value/basic filters (superset).
        setor: Sector ID.
        custom_terms: User's free search terms (STORY-267).
        stats: Mutable stats dict — updated in place.
        llm_zero_match_active: If True, skip FLUXO 2 (GTM-FIX-028 AC10).

    Returns:
        Extended list of approved bids (same reference as input + new recoveries).
    """
    from config import LLM_ZERO_MATCH_ENABLED

    # Initialize FLUXO 2 stats
    stats["recuperadas_exclusion_recovery"] = 0
    stats["aprovadas_synonym_match"] = 0
    stats["synonyms_auto_approved"] = 0
    stats["recuperadas_llm_fn"] = 0
    stats["recuperadas_zero_results"] = 0
    stats["llm_arbiter_calls_fn_flow"] = 0
    stats["zero_results_relaxation_triggered"] = False

    # GTM-FIX-028 AC10: Skip when LLM zero-match already ran
    _skip_fluxo_2 = LLM_ZERO_MATCH_ENABLED and llm_zero_match_active
    if _skip_fluxo_2:
        logger.info(
            "GTM-FIX-028 AC10: FLUXO 2 DISABLED — LLM zero-match already classified bids"
        )
        _log_fluxo2_stats(stats)
        return aprovadas

    # STORY-267 AC4+AC7: Term-aware recovery
    _use_term_prompt_recovery = False
    _use_term_synonyms = False
    if custom_terms:
        from config import get_feature_flag as _gff_ac4
        _use_term_prompt_recovery = _gff_ac4("TERM_SEARCH_LLM_AWARE")
        _use_term_synonyms = _gff_ac4("TERM_SEARCH_SYNONYMS")

    _run_fluxo_2 = (setor or (_use_term_synonyms and custom_terms)) and not _skip_fluxo_2
    if not _run_fluxo_2:
        _log_fluxo2_stats(stats)
        return aprovadas

    from synonyms import find_synonym_matches, should_auto_approve_by_synonyms
    if _use_term_synonyms and custom_terms:
        from synonyms import find_term_synonym_matches
    from sectors import get_sector as _get_sector

    try:
        setor_config = _get_sector(setor) if setor else None
        setor_keywords = setor_config.keywords if setor_config else set()
        setor_name = setor_config.name if setor_config else None

        aprovadas_ids = {id(lic) for lic in aprovadas}

        # Collect bids rejected at keyword stage
        rejeitadas_keyword_pool: List[dict] = []
        for lic in resultado_valor:
            if id(lic) not in aprovadas_ids:
                rejeitadas_keyword_pool.append(lic)

        logger.debug(
            f"FLUXO 2 iniciando: {len(rejeitadas_keyword_pool)} contratos no pool de "
            f"recuperação (rejeitados após filtros rápidos)"
        )

        recuperadas: List[dict] = []
        llm_candidates_fn: List[dict] = []

        # Camada 1B + 2B: Synonym matching
        for lic in rejeitadas_keyword_pool:
            objeto = lic.get("objetoCompra", "")
            if not objeto:
                continue

            if _use_term_synonyms and custom_terms:
                synonym_matches = find_term_synonym_matches(
                    custom_terms=custom_terms, objeto=objeto,
                )
            elif setor:
                synonym_matches = find_synonym_matches(
                    objeto=objeto, setor_keywords=setor_keywords, setor_id=setor,
                )
            else:
                synonym_matches = []

            if not synonym_matches:
                continue

            # Auto-approve check (2+ synonyms)
            if _use_term_synonyms and custom_terms:
                should_approve_flag = len(synonym_matches) >= 2
                matches = synonym_matches
            else:
                should_approve_flag, matches = should_auto_approve_by_synonyms(
                    objeto=objeto, setor_keywords=setor_keywords,
                    setor_id=setor, min_synonyms=2,
                )

            if should_approve_flag:
                stats["aprovadas_synonym_match"] += 1
                stats["synonyms_auto_approved"] += 1
                lic["_recovered_by"] = "synonym_auto_approve"
                lic["_synonym_matches"] = [
                    f"{canon}≈{syn}" for canon, syn in matches
                ]
                recuperadas.append(lic)
                if custom_terms:
                    from metrics import TERM_SEARCH_SYNONYM_RECOVERIES
                    TERM_SEARCH_SYNONYM_RECOVERIES.inc()
                logger.debug(
                    f"  Recuperada por sinônimos (auto): {matches} "
                    f"objeto={objeto[:80]}"
                )
            else:
                lic["_near_miss_synonyms"] = synonym_matches
                llm_candidates_fn.append(lic)

        # Camada 3B: LLM Recovery for ambiguous synonym matches
        if llm_candidates_fn:
            _run_llm_recovery(
                llm_candidates_fn, setor_name, custom_terms,
                _use_term_prompt_recovery, recuperadas, stats,
            )

        if recuperadas:
            aprovadas.extend(recuperadas)
            logger.info(
                f"FLUXO 2: {len(recuperadas)} contratos recuperados "
                f"(synonym_auto: {stats['aprovadas_synonym_match']}, "
                f"llm_recovery: {stats['recuperadas_llm_fn']})"
            )

        # Camada 4: Zero Results Relaxation
        if len(aprovadas) == 0 and len(rejeitadas_keyword_pool) > 0:
            _run_zero_results_relaxation(
                rejeitadas_keyword_pool, recuperadas, setor,
                setor_keywords, custom_terms, _use_term_synonyms,
                aprovadas, stats,
            )

    except KeyError:
        logger.warning(f"Setor '{setor}' não encontrado - pulando FLUXO 2")
    except Exception as e:
        logger.error(f"FLUXO 2 recovery failed: {e}", exc_info=True)

    _log_fluxo2_stats(stats)
    return aprovadas


def _run_llm_recovery(
    candidates: List[dict],
    setor_name: Optional[str],
    custom_terms: Optional[List[str]],
    use_term_prompt: bool,
    recuperadas: List[dict],
    stats: Dict,
) -> None:
    """Camada 3B: LLM recovery for ambiguous synonym matches."""
    from llm_arbiter import classify_contract_recovery

    for lic in candidates:
        objeto = lic.get("objetoCompra", "")
        objeto = _strip_org_context(objeto)
        valor = lic.get("valorTotalEstimado") or lic.get("valorEstimado") or 0
        valor = parse_valor(valor)

        near_miss = lic.get("_near_miss_synonyms", [])
        near_miss_info = ", ".join(
            f"{canon}≈{syn}" for canon, syn in near_miss
        )

        stats["llm_arbiter_calls_fn_flow"] += 1

        if use_term_prompt and custom_terms:
            should_recover = classify_contract_recovery(
                objeto=objeto, valor=valor,
                rejection_reason="keyword_no_match + synonym_near_miss",
                termos_busca=custom_terms, near_miss_info=near_miss_info,
            )
        else:
            should_recover = classify_contract_recovery(
                objeto=objeto, valor=valor,
                rejection_reason="keyword_no_match + synonym_near_miss",
                setor_name=setor_name, near_miss_info=near_miss_info,
            )

        if should_recover:
            stats["recuperadas_llm_fn"] += 1
            lic["_recovered_by"] = "llm_recovery"
            lic["_synonym_matches"] = [
                f"{canon}≈{syn}" for canon, syn in near_miss
            ]
            recuperadas.append(lic)
            logger.debug(
                f"  Recuperada por LLM (FN flow): near_miss={near_miss_info} "
                f"objeto={objeto[:80]}"
            )


def _run_zero_results_relaxation(
    rejeitadas_pool: List[dict],
    recuperadas: List[dict],
    setor: Optional[str],
    setor_keywords: Set[str],
    custom_terms: Optional[List[str]],
    use_term_synonyms: bool,
    aprovadas: List[dict],
    stats: Dict,
) -> None:
    """Camada 4: Zero-results relaxation — accept any 1+ synonym match."""
    from synonyms import find_synonym_matches
    if use_term_synonyms and custom_terms:
        from synonyms import find_term_synonym_matches

    stats["zero_results_relaxation_triggered"] = True
    logger.info("FLUXO 2 Camada 4: Zero results detected, attempting relaxation")

    recuperadas_ids = {id(r) for r in recuperadas}

    for lic in rejeitadas_pool:
        if id(lic) in recuperadas_ids:
            continue

        objeto = lic.get("objetoCompra", "")
        if not objeto:
            continue

        if use_term_synonyms and custom_terms:
            synonym_matches = find_term_synonym_matches(
                custom_terms=custom_terms, objeto=objeto,
            )
        elif setor:
            synonym_matches = find_synonym_matches(
                objeto=objeto, setor_keywords=setor_keywords, setor_id=setor,
            )
        else:
            synonym_matches = []

        if synonym_matches:
            stats["recuperadas_zero_results"] += 1
            lic["_recovered_by"] = "zero_results_relaxation"
            lic["_synonym_matches"] = [
                f"{canon}≈{syn}" for canon, syn in synonym_matches
            ]
            aprovadas.append(lic)

    if stats["recuperadas_zero_results"] > 0:
        logger.info(
            f"Camada 4 relaxation: recovered {stats['recuperadas_zero_results']} "
            f"contracts via single-synonym matching"
        )


def _log_fluxo2_stats(stats: Dict) -> None:
    """Log FLUXO 2 summary stats."""
    logger.debug(
        f"FLUXO 2 resultado: "
        f"synonym_auto={stats.get('aprovadas_synonym_match', 0)}, "
        f"llm_recovery={stats.get('recuperadas_llm_fn', 0)}, "
        f"zero_results={stats.get('recuperadas_zero_results', 0)}, "
        f"llm_calls_fn={stats.get('llm_arbiter_calls_fn_flow', 0)}"
    )
