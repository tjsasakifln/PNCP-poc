"""DEBT-118 AC10: LLM classification logic for the filter pipeline.

Contains two main phases extracted from aplicar_todos_filtros():
- Phase 2B: Zero-match LLM classification (bids with 0 keyword matches)
- Phase 3A: LLM Arbiter (gray-zone bids with 1-5% term density)

Both phases use ThreadPoolExecutor for parallel LLM calls and include
budget guards (CRIT-057), per-future timeouts (HARDEN-014), and
structured metrics/logging.
"""

import logging
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from typing import Callable, Dict, List, Optional, Tuple

from filter_keywords import _strip_org_context
from filter_utils import get_valor_from_lic

logger = logging.getLogger(__name__)


def _extract_item(lic_item: dict) -> dict:
    """Extract objeto/valor from a lic dict for LLM classification.

    UX-402: Strips org context and parses valor to float.
    """
    obj = lic_item.get("objetoCompra", "")
    obj = _strip_org_context(obj)
    val = get_valor_from_lic(lic_item)
    return {"objeto": obj, "valor": val}


def classify_zero_match_pool(
    zero_match_pool: List[dict],
    resultado_valor: List[dict],
    resultado_keyword: List[dict],
    setor: Optional[str],
    custom_terms: Optional[List[str]],
    on_progress: Optional[Callable[[int, int, str], None]],
    stats: Dict,
) -> Tuple[List[dict], List[dict]]:
    """Run LLM zero-match classification on bids rejected by keyword gate.

    This is Phase 2B of the filter pipeline. Bids with 0 keyword matches
    are sent to LLM for sector-aware classification.

    Args:
        zero_match_pool: Pre-filtered pool of bids to classify (may be capped by CRIT-058).
        resultado_valor: All bids that passed value filters (superset).
        resultado_keyword: Bids that passed keyword matching (for ID exclusion).
        setor: Sector ID.
        custom_terms: User's free search terms (STORY-267).
        on_progress: Progress callback (processed, total, phase).
        stats: Mutable stats dict — updated in place.

    Returns:
        Tuple of (approved_bids, pending_review_bids).
    """
    from config import LLM_ZERO_MATCH_ENABLED

    resultado_llm_zero: List[dict] = []
    resultado_pending_review: List[dict] = []

    stats["llm_zero_match_calls"] = 0
    stats["llm_zero_match_aprovadas"] = 0
    stats["llm_zero_match_rejeitadas"] = 0
    stats["llm_zero_match_skipped_short"] = 0
    stats["pending_review_count"] = 0

    # STORY-267 AC2: term-aware prompt for zero-match
    _use_term_prompt_zm = False
    if custom_terms:
        from config import get_feature_flag as _gff_ac2
        _use_term_prompt_zm = _gff_ac2("TERM_SEARCH_LLM_AWARE")

    if not (LLM_ZERO_MATCH_ENABLED and setor):
        return resultado_llm_zero, resultado_pending_review

    # ISSUE-029: Load sector negative_keywords for pre-filter
    _sector_negative_kws: List[str] = []
    try:
        from sectors import get_sector as _get_sector_neg
        _neg_sec = _get_sector_neg(setor)
        _sector_negative_kws = [kw.lower() for kw in getattr(_neg_sec, "negative_keywords", [])]
    except Exception:
        pass

    # Collect bids rejected by keyword gate
    keyword_approved_ids = {id(lic) for lic in resultado_keyword}
    raw_pool: List[dict] = []
    for lic in resultado_valor:
        if id(lic) not in keyword_approved_ids:
            objeto = lic.get("objetoCompra", "")
            if len(objeto) < 20:
                stats["llm_zero_match_skipped_short"] += 1
                logger.debug(f"LLM zero_match: SKIP (objeto < 20 chars) objeto={objeto!r}")
                continue
            raw_pool.append(lic)

    # ISSUE-029: Pre-filter bids whose objetoCompra contains negative_keywords
    if _sector_negative_kws and raw_pool:
        _neg_filtered = []
        _neg_rejected = 0
        for lic in raw_pool:
            _obj_lower = (lic.get("objetoCompra") or "").lower()
            if any(neg_kw in _obj_lower for neg_kw in _sector_negative_kws):
                _neg_rejected += 1
                logger.debug(
                    f"LLM zero_match: PRE-FILTER (negative_keyword match) "
                    f"objeto={lic.get('objetoCompra', '')[:80]}"
                )
            else:
                _neg_filtered.append(lic)
        if _neg_rejected > 0:
            logger.info(
                f"[ISSUE-029] Zero-match negative_keyword pre-filter: "
                f"removed {_neg_rejected}/{len(raw_pool)} bids before LLM"
            )
        raw_pool = _neg_filtered

    # CRIT-058: Cap + prioritize zero-match pool
    from config import MAX_ZERO_MATCH_ITEMS, ZERO_MATCH_VALUE_RATIO
    from metrics import ZERO_MATCH_CAP_APPLIED_TOTAL, ZERO_MATCH_POOL_SIZE

    stats["zero_match_capped"] = False
    stats["zero_match_cap_value"] = MAX_ZERO_MATCH_ITEMS

    if raw_pool:
        ZERO_MATCH_POOL_SIZE.observe(len(raw_pool))

    if len(raw_pool) > MAX_ZERO_MATCH_ITEMS:
        raw_pool, deferred, stats_update = _cap_zero_match_pool(
            raw_pool, MAX_ZERO_MATCH_ITEMS, ZERO_MATCH_VALUE_RATIO, setor
        )
        resultado_pending_review.extend(deferred)
        stats["zero_match_capped"] = True
        stats["pending_review_count"] += len(deferred)
        ZERO_MATCH_CAP_APPLIED_TOTAL.inc()

    if raw_pool:
        # CRIT-059: Async zero-match
        from config import ASYNC_ZERO_MATCH_ENABLED
        if ASYNC_ZERO_MATCH_ENABLED:
            stats["zero_match_candidates"] = raw_pool
            stats["zero_match_candidates_count"] = len(raw_pool)
            logger.info(
                f"[CRIT-059] Async zero-match: collected {len(raw_pool)} candidates "
                f"for background job (inline LLM skipped)"
            )
            raw_pool = []

    if raw_pool:
        approved, pending = _run_zero_match_llm(
            raw_pool, setor, custom_terms, _use_term_prompt_zm, on_progress, stats
        )

        # ISSUE-029: Acceptance ratio circuit breaker — sector-aware threshold.
        # Narrow sectors (e.g. vestuario) use a tighter cap via zero_match_acceptance_cap.
        _cb_threshold = 0.30
        try:
            from sectors import get_sector as _get_sector_cb
            _sec_cfg = _get_sector_cb(setor)
            if hasattr(_sec_cfg, "zero_match_acceptance_cap") and _sec_cfg.zero_match_acceptance_cap is not None:
                _cb_threshold = _sec_cfg.zero_match_acceptance_cap
        except Exception:
            pass

        _total_classified = len(approved) + stats.get("llm_zero_match_rejeitadas", 0)
        if _total_classified > 0 and len(approved) / _total_classified > _cb_threshold:
            _accept_ratio = len(approved) / _total_classified
            _demoted_count = len(approved)
            logger.warning(
                f"[ISSUE-029] Zero-match acceptance ratio {_accept_ratio:.1%} exceeds "
                f"{_cb_threshold:.0%} threshold for setor={setor!r} "
                f"({_demoted_count}/{_total_classified}) — demoting to pending_review "
                f"to prevent false positive flood"
            )
            for _lic in approved:
                _lic["_relevance_source"] = "pending_review"
                _lic["_pending_review"] = True
                _lic["_pending_review_reason"] = "zero_match_high_acceptance_ratio"
            pending = list(pending) + approved
            approved = []
            stats["pending_review_count"] += _demoted_count

        resultado_llm_zero.extend(approved)
        resultado_pending_review.extend(pending)

        logger.info(
            f"GTM-FIX-028 LLM Zero Match: "
            f"{stats['llm_zero_match_calls']} calls, "
            f"{stats['llm_zero_match_aprovadas']} approved, "
            f"{stats['llm_zero_match_rejeitadas']} rejected, "
            f"{stats['llm_zero_match_skipped_short']} skipped (short), "
            f"{stats['pending_review_count']} pending_review"
        )

    return resultado_llm_zero, resultado_pending_review


def _cap_zero_match_pool(
    pool: List[dict],
    max_items: int,
    value_ratio: float,
    setor: Optional[str],
) -> Tuple[List[dict], List[dict], Dict]:
    """CRIT-058: Cap + prioritize zero-match pool via intelligent sampling.

    Returns (to_classify, deferred, stats_update).
    """
    from middleware import search_id_var as _sid_var_058

    _sid_058 = _sid_var_058.get(None)
    _rng = random.Random(hash(_sid_058) if _sid_058 else 42)

    pool.sort(key=lambda x: get_valor_from_lic(x), reverse=True)

    n_value = int(max_items * value_ratio)
    n_random = max_items - n_value

    top_value = pool[:n_value]
    remainder = pool[n_value:]

    # ISSUE-029: Replace random sampling with sector-aware affinity scoring.
    # Random sampling was injecting completely irrelevant bids (e.g. diesel, poços)
    # into the LLM classification budget. Sector-keyword affinity ranks by relevance.
    if n_random > 0 and remainder:
        if setor:
            try:
                from sectors import get_sector_config
                sector_cfg = get_sector_config(setor)
                sector_kws = {
                    kw.lower()
                    for kw in (
                        sector_cfg.get("keywords", [])
                        if isinstance(sector_cfg, dict)
                        else getattr(sector_cfg, "keywords", [])
                    )
                }

                def _sector_affinity(lic: dict) -> int:
                    obj = (lic.get("objetoCompra") or lic.get("objeto") or "").lower()
                    # ISSUE-029: Use word-boundary matching to avoid substring false
                    # positives (e.g. "confecção" matching "confecção de fossas sépticas").
                    # Multi-word keywords get higher weight (more specific = more confident).
                    score = 0
                    obj_padded = f" {obj} "
                    for kw in sector_kws:
                        kw_lower = kw.lower()
                        matched = (
                            f" {kw_lower} " in obj_padded
                            or obj.startswith(f"{kw_lower} ")
                            or obj.endswith(f" {kw_lower}")
                            or obj == kw_lower
                        )
                        if matched:
                            score += len(kw_lower.split())
                    return score

                remainder.sort(key=_sector_affinity, reverse=True)
            except Exception:
                pass  # Keep value-based order as fallback
        semantic_sample = remainder[:n_random]

        # ISSUE-029: Second negative_keywords pass — remove construction/infra
        # bids that slipped through value-based selection into the affinity pool.
        if setor:
            try:
                from sectors import get_sector as _get_sec_neg2
                _neg2_cfg = _get_sec_neg2(setor)
                _neg2_kws = [k.lower() for k in getattr(_neg2_cfg, "negative_keywords", [])]
                if _neg2_kws:
                    _before = len(semantic_sample)
                    semantic_sample = [
                        lic for lic in semantic_sample
                        if not any(
                            neg in (lic.get("objetoCompra") or lic.get("objeto") or "").lower()
                            for neg in _neg2_kws
                        )
                    ]
                    _removed = _before - len(semantic_sample)
                    if _removed > 0:
                        logger.info(
                            f"[ISSUE-029] Affinity-pool negative_keyword pass: "
                            f"removed {_removed}/{_before} bids from semantic_sample"
                        )
            except Exception:
                pass
    else:
        semantic_sample = []

    to_classify = top_value + semantic_sample
    to_classify_ids = {id(x) for x in to_classify}

    deferred: List[dict] = []
    for lic_item in pool:
        if id(lic_item) not in to_classify_ids:
            lic_item["_relevance_source"] = "pending_review"
            lic_item["_pending_review"] = True
            lic_item["_pending_review_reason"] = "zero_match_cap_exceeded"
            lic_item["_term_density"] = 0.0
            lic_item["_matched_terms"] = []
            lic_item["_confidence_score"] = 0
            lic_item["_llm_evidence"] = []
            deferred.append(lic_item)

    # AC6: Impact log with value bands
    classified_vals = [get_valor_from_lic(x) for x in to_classify]
    deferred_vals = [get_valor_from_lic(x) for x in deferred]

    def _count_bands(vals: list) -> dict:
        bands = {">1M": 0, "100K-1M": 0, "10K-100K": 0, "<10K": 0}
        for v in vals:
            if v > 1_000_000:
                bands[">1M"] += 1
            elif v > 100_000:
                bands["100K-1M"] += 1
            elif v > 10_000:
                bands["10K-100K"] += 1
            else:
                bands["<10K"] += 1
        return bands

    logger.info(
        f"[CRIT-058] Zero-match pool capped: {len(to_classify)}/{len(pool)} items "
        f"(cap={max_items}). "
        f"Value split: {n_value} by value + {len(semantic_sample)} sector-affinity. "
        f"Classified bands={_count_bands(classified_vals)}, "
        f"Deferred bands={_count_bands(deferred_vals)}, "
        f"Classified total value={sum(classified_vals):,.0f}, "
        f"Deferred total value={sum(deferred_vals):,.0f}"
    )

    return to_classify, deferred, {}


def _mark_pending_review(lic_item: dict, reason: str) -> None:
    """Mark a bid as pending_review with standard fields."""
    lic_item["_relevance_source"] = "pending_review"
    lic_item["_pending_review"] = True
    lic_item["_pending_review_reason"] = reason
    lic_item["_term_density"] = 0.0
    lic_item["_matched_terms"] = []
    lic_item["_confidence_score"] = 0
    lic_item["_llm_evidence"] = []


def _apply_zero_match_result(
    lic_item: dict,
    llm_result,
    custom_terms: Optional[List[str]],
    resultado_approved: List[dict],
    resultado_pending: List[dict],
    stats: Dict,
) -> None:
    """Process a single LLM zero-match result and route to approved or pending."""
    is_relevant = llm_result.get("is_primary", False) if isinstance(llm_result, dict) else llm_result
    if is_relevant:
        stats["llm_zero_match_aprovadas"] += 1
        if custom_terms:
            from metrics import TERM_SEARCH_LLM_ACCEPTS
            TERM_SEARCH_LLM_ACCEPTS.labels(zone="zero_match").inc()
        lic_item["_relevance_source"] = "llm_zero_match"
        lic_item["_term_density"] = 0.0
        lic_item["_matched_terms"] = []
        # D-02 AC4: Confidence capped at 70 for zero-match
        if isinstance(llm_result, dict):
            raw_conf = llm_result.get("confidence", 60)
            lic_item["_confidence_score"] = min(raw_conf, 70)
            lic_item["_llm_evidence"] = llm_result.get("evidence", [])
        else:
            lic_item["_confidence_score"] = 60
            lic_item["_llm_evidence"] = []
        resultado_approved.append(lic_item)
        logger.debug(
            f"LLM zero_match: ACCEPT conf={lic_item.get('_confidence_score')} "
            f"objeto={lic_item.get('objetoCompra', '')[:80]}"
        )
    else:
        _is_pending = isinstance(llm_result, dict) and llm_result.get("pending_review", False)
        if _is_pending:
            stats["pending_review_count"] += 1
            _mark_pending_review(lic_item, "llm_unavailable")
            resultado_pending.append(lic_item)
            logger.info(
                f"LLM zero_match: PENDING_REVIEW (LLM unavailable) "
                f"objeto={lic_item.get('objetoCompra', '')[:80]}"
            )
        else:
            stats["llm_zero_match_rejeitadas"] += 1
            if custom_terms:
                from metrics import TERM_SEARCH_LLM_REJECTS
                TERM_SEARCH_LLM_REJECTS.labels(zone="zero_match").inc()
            if isinstance(llm_result, dict):
                lic_item["_llm_rejection_reason"] = llm_result.get("rejection_reason", "")
            logger.debug(
                f"LLM zero_match: REJECT objeto={lic_item.get('objetoCompra', '')[:80]}"
            )


def _run_zero_match_llm(
    pool: List[dict],
    setor: str,
    custom_terms: Optional[List[str]],
    use_term_prompt: bool,
    on_progress: Optional[Callable],
    stats: Dict,
) -> Tuple[List[dict], List[dict]]:
    """Execute LLM zero-match classification (batch or individual).

    Returns (approved, pending_review).
    """
    from llm_arbiter import _classify_zero_match_batch as _classify_batch
    from config import (
        LLM_ZERO_MATCH_BATCH_SIZE,
        FILTER_ZERO_MATCH_BUDGET_S,
    )

    setor_config = None
    setor_name = setor
    try:
        from sectors import get_sector as _get_sector_zm
        setor_config = _get_sector_zm(setor)
        setor_name = setor_config.name
    except (KeyError, Exception):
        pass

    resultado_approved: List[dict] = []
    resultado_pending: List[dict] = []
    _llm_total = len(pool)
    stats["zero_match_budget_exceeded"] = 0

    # DEBT-128: Batch mode is now always-on (LLM_ZERO_MATCH_BATCH_ENABLED removed)
    _run_zero_match_batch(
        pool, setor, setor_name, custom_terms, use_term_prompt,
        on_progress, stats, resultado_approved, resultado_pending,
        _classify_batch, LLM_ZERO_MATCH_BATCH_SIZE, FILTER_ZERO_MATCH_BUDGET_S,
    )

    return resultado_approved, resultado_pending


def _run_zero_match_batch(
    pool: List[dict],
    setor: str,
    setor_name: str,
    custom_terms: Optional[List[str]],
    use_term_prompt: bool,
    on_progress: Optional[Callable],
    stats: Dict,
    resultado_approved: List[dict],
    resultado_pending: List[dict],
    _classify_batch,
    batch_size: int,
    budget_s: float,
) -> bool:
    """Run batch zero-match classification. Returns True if batch succeeded."""
    from metrics import LLM_ZERO_MATCH_BATCH_DURATION, LLM_ZERO_MATCH_BATCH_SIZE as _BATCH_SIZE_METRIC

    _batch_start = time.time()
    _llm_total = len(pool)
    _zm_budget_hit = False

    batch_items = [_extract_item(lic) for lic in pool]
    batches = [
        batch_items[i:i + batch_size]
        for i in range(0, len(batch_items), batch_size)
    ]
    batch_lic_groups = [
        pool[i:i + batch_size]
        for i in range(0, len(pool), batch_size)
    ]

    for batch in batches:
        _BATCH_SIZE_METRIC.observe(len(batch))

    all_results: list[tuple[int, list[dict]]] = []
    _completed_batch_indices: set = set()

    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_idx = {}
        for idx, batch in enumerate(batches):
            if use_term_prompt and custom_terms:
                fut = executor.submit(
                    _classify_batch, items=batch, setor_name=None,
                    setor_id=None, termos_busca=custom_terms,
                )
            else:
                fut = executor.submit(
                    _classify_batch, items=batch, setor_name=setor_name,
                    setor_id=setor, termos_busca=None,
                )
            future_to_idx[fut] = idx

        pending = set(future_to_idx.keys())
        while pending:
            _zm_elapsed = time.time() - _batch_start
            if _zm_elapsed > budget_s:
                _zm_budget_hit = True
                for f in pending:
                    f.cancel()
                for b_idx, b_group in enumerate(batch_lic_groups):
                    if b_idx not in _completed_batch_indices:
                        for lic_item in b_group:
                            _mark_pending_review(lic_item, "zero_match_budget_exceeded")
                            resultado_pending.append(lic_item)
                            stats["zero_match_budget_exceeded"] += 1
                            stats["pending_review_count"] += 1
                logger.warning(
                    f"[CRIT-057] Zero-match budget exceeded after "
                    f"{len(_completed_batch_indices)}/{len(batches)} batches "
                    f"in {_zm_elapsed:.1f}s (budget={budget_s}s)"
                )
                break

            done, pending = wait(pending, timeout=20, return_when=FIRST_COMPLETED)

            if not done:
                from metrics import LLM_BATCH_TIMEOUT
                for f in pending:
                    f.cancel()
                    LLM_BATCH_TIMEOUT.labels(phase="zero_match_batch").inc()
                for b_idx, b_group in enumerate(batch_lic_groups):
                    if b_idx not in _completed_batch_indices:
                        for lic_item in b_group:
                            _mark_pending_review(lic_item, "llm_future_timeout")
                            resultado_pending.append(lic_item)
                            stats["pending_review_count"] += 1
                logger.warning(
                    f"[HARDEN-014] Per-future timeout (20s) hit for "
                    f"{len(pending)} batch futures, "
                    f"{len(_completed_batch_indices)}/{len(batches)} completed"
                )
                break

            for future in done:
                idx = future_to_idx[future]
                _completed_batch_indices.add(idx)
                batch_results = future.result()
                all_results.append((idx, batch_results))

    all_results.sort(key=lambda x: x[0])
    _llm_completed = 0
    for idx, batch_results in all_results:
        lic_group = batch_lic_groups[idx]
        for lic_item, llm_result in zip(lic_group, batch_results):
            _llm_completed += 1
            stats["llm_zero_match_calls"] += 1
            if on_progress:
                on_progress(_llm_completed, _llm_total, "llm_classify")
            _apply_zero_match_result(
                lic_item, llm_result, custom_terms,
                resultado_approved, resultado_pending, stats,
            )

    _batch_elapsed = time.time() - _batch_start
    LLM_ZERO_MATCH_BATCH_DURATION.observe(_batch_elapsed)
    try:
        from metrics import FILTER_ZERO_MATCH_DURATION
        FILTER_ZERO_MATCH_DURATION.labels(
            mode="batch", budget_exceeded=str(_zm_budget_hit).lower(),
        ).observe(_batch_elapsed)
    except Exception:
        pass
    logger.info(
        f"UX-402: Batch mode completed {_llm_completed}/{_llm_total} items "
        f"in {_batch_elapsed:.2f}s ({len(batches)} batches)"
        + (f" [CRIT-057: budget hit, {stats['zero_match_budget_exceeded']} deferred]"
           if _zm_budget_hit else "")
    )
    return True


def _run_zero_match_individual(
    pool: List[dict],
    setor: str,
    setor_name: str,
    custom_terms: Optional[List[str]],
    use_term_prompt: bool,
    on_progress: Optional[Callable],
    stats: Dict,
    resultado_approved: List[dict],
    resultado_pending: List[dict],
    _classify_zm,
    budget_s: float,
) -> None:
    """Run individual zero-match classification (fallback from batch)."""
    _llm_total = len(pool)
    _zm_budget_hit = False

    def _classify_one(lic_item: dict) -> tuple:
        item = _extract_item(lic_item)
        if use_term_prompt and custom_terms:
            result = _classify_zm(
                objeto=item["objeto"], valor=item["valor"],
                setor_name=None, termos_busca=custom_terms,
                prompt_level="zero_match", setor_id=None,
            )
        else:
            result = _classify_zm(
                objeto=item["objeto"], valor=item["valor"],
                setor_name=setor_name, prompt_level="zero_match",
                setor_id=setor,
            )
        return lic_item, result

    _llm_completed = 0
    _indiv_start = time.time()
    _indiv_classified_ids: set = set()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(_classify_one, lic): lic
            for lic in pool
        }
        pending = set(futures.keys())
        while pending:
            _zm_elapsed = time.time() - _indiv_start
            if _zm_elapsed > budget_s:
                _zm_budget_hit = True
                for f in pending:
                    f.cancel()
                for lic in pool:
                    if id(lic) not in _indiv_classified_ids:
                        _mark_pending_review(lic, "zero_match_budget_exceeded")
                        resultado_pending.append(lic)
                        stats["zero_match_budget_exceeded"] += 1
                        stats["pending_review_count"] += 1
                logger.warning(
                    f"[CRIT-057] Zero-match budget exceeded after "
                    f"{_llm_completed}/{_llm_total} items "
                    f"in {_zm_elapsed:.1f}s (budget={budget_s}s)"
                )
                break

            done, pending = wait(pending, timeout=20, return_when=FIRST_COMPLETED)

            if not done:
                from metrics import LLM_BATCH_TIMEOUT
                for f in pending:
                    f.cancel()
                    LLM_BATCH_TIMEOUT.labels(phase="zero_match_individual").inc()
                for lic in pool:
                    if id(lic) not in _indiv_classified_ids:
                        _mark_pending_review(lic, "llm_future_timeout")
                        resultado_pending.append(lic)
                        stats["pending_review_count"] += 1
                logger.warning(
                    f"[HARDEN-014] Per-future timeout (20s) hit for "
                    f"{len(pending)} individual futures, "
                    f"{_llm_completed}/{_llm_total} completed"
                )
                break

            for future in done:
                _llm_completed += 1
                stats["llm_zero_match_calls"] += 1
                _indiv_classified_ids.add(id(futures[future]))
                if on_progress:
                    on_progress(_llm_completed, _llm_total, "llm_classify")
                try:
                    lic_item, llm_result = future.result()
                    _apply_zero_match_result(
                        lic_item, llm_result, custom_terms,
                        resultado_approved, resultado_pending, stats,
                    )
                except Exception as e:
                    from config import LLM_FALLBACK_PENDING_ENABLED
                    if LLM_FALLBACK_PENDING_ENABLED:
                        stats["pending_review_count"] += 1
                        lic_ref = futures[future]
                        _mark_pending_review(lic_ref, "llm_error")
                        resultado_pending.append(lic_ref)
                        logger.warning(f"LLM zero_match: FAILED → PENDING_REVIEW: {e}")
                    else:
                        stats["llm_zero_match_rejeitadas"] += 1
                        logger.error(f"LLM zero_match: FAILED (REJECT fallback): {e}")

    _indiv_elapsed = time.time() - _indiv_start
    try:
        from metrics import FILTER_ZERO_MATCH_DURATION
        FILTER_ZERO_MATCH_DURATION.labels(
            mode="individual", budget_exceeded=str(_zm_budget_hit).lower(),
        ).observe(_indiv_elapsed)
    except Exception:
        pass


def run_arbiter(
    resultado_llm_candidates: List[dict],
    setor: Optional[str],
    custom_terms: Optional[List[str]],
    resultado_densidade: List[dict],
    stats: Dict,
) -> None:
    """Run LLM Arbiter (Phase 3A) on gray-zone bids.

    Modifies resultado_densidade in place by appending approved bids.
    Updates stats dict in place.

    Args:
        resultado_llm_candidates: Bids in the 1-5% density zone.
        setor: Sector ID.
        custom_terms: User's free search terms.
        resultado_densidade: Accumulator for density-approved bids (modified in place).
        stats: Mutable stats dict.
    """
    from config import QA_AUDIT_SAMPLE_RATE

    stats["aprovadas_llm_arbiter"] = 0
    stats["rejeitadas_llm_arbiter"] = 0
    stats["llm_arbiter_calls"] = 0

    if not resultado_llm_candidates:
        return

    from llm_arbiter import classify_contract_primary_match

    # STORY-267 AC3: term-aware prompt
    _use_term_prompt = False
    if custom_terms:
        from config import get_feature_flag as _gff_ac3
        _use_term_prompt = _gff_ac3("TERM_SEARCH_LLM_AWARE")

    # CRIT-FLT-002: Resolve sector name ONCE
    _arbiter_setor_name = None
    if setor and not _use_term_prompt:
        from sectors import get_sector
        try:
            _arbiter_setor_config = get_sector(setor)
            _arbiter_setor_name = _arbiter_setor_config.name
        except KeyError:
            logger.warning(f"Setor '{setor}' não encontrado para LLM arbiter")

    _arbiter_stats_lock = threading.Lock()

    def _classify_one_arbiter(lic_item):
        objeto = lic_item.get("objetoCompra", "")
        objeto = _strip_org_context(objeto)
        valor = get_valor_from_lic(lic_item)
        prompt_level = lic_item.get("_llm_prompt_level", "standard")

        if _use_term_prompt and custom_terms:
            llm_result = classify_contract_primary_match(
                objeto=objeto, valor=valor, setor_name=None,
                termos_busca=custom_terms, prompt_level=prompt_level, setor_id=None,
            )
        else:
            termos = None
            if not _arbiter_setor_name:
                termos = lic_item.get("_matched_terms", [])
            llm_result = classify_contract_primary_match(
                objeto=objeto, valor=valor, setor_name=_arbiter_setor_name,
                termos_busca=termos, prompt_level=prompt_level,
                setor_id=setor if _arbiter_setor_name else None,
            )
        return lic_item, llm_result, valor

    t0_arbiter = time.monotonic()
    tracker = None
    try:
        from filter_keywords import _get_tracker
        tracker = _get_tracker()
    except Exception:
        pass

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(_classify_one_arbiter, lic): lic
            for lic in resultado_llm_candidates
        }
        pending = set(futures.keys())
        while pending:
            done, pending = wait(pending, timeout=20, return_when=FIRST_COMPLETED)

            if not done:
                from metrics import LLM_BATCH_TIMEOUT
                for f in pending:
                    f.cancel()
                    LLM_BATCH_TIMEOUT.labels(phase="arbiter").inc()
                with _arbiter_stats_lock:
                    stats["rejeitadas_llm_arbiter"] += len(pending)
                logger.warning(
                    f"[HARDEN-014] Per-future timeout (20s) hit for "
                    f"{len(pending)} arbiter futures"
                )
                break

            for future in done:
                with _arbiter_stats_lock:
                    stats["llm_arbiter_calls"] += 1
                try:
                    lic, llm_result, valor = future.result()
                    trace_id = lic.get("_trace_id", "unknown")
                    prompt_level = lic.get("_llm_prompt_level", "standard")
                    objeto = lic.get("objetoCompra", "")
                    is_primary = llm_result.get("is_primary", False) if isinstance(llm_result, dict) else llm_result

                    if is_primary:
                        with _arbiter_stats_lock:
                            stats["aprovadas_llm_arbiter"] += 1
                        lic["_relevance_source"] = f"llm_{prompt_level}"
                        if isinstance(llm_result, dict):
                            lic["_confidence_score"] = llm_result.get("confidence", 70)
                            lic["_llm_evidence"] = llm_result.get("evidence", [])
                        else:
                            lic["_confidence_score"] = 70
                            lic["_llm_evidence"] = []
                        resultado_densidade.append(lic)
                        logger.debug(
                            f"[{trace_id}] Camada 3A: ACCEPT (LLM={prompt_level}) "
                            f"conf={lic.get('_confidence_score')} "
                            f"density={lic.get('_term_density', 0):.1%} "
                            f"objeto={objeto[:80]}"
                        )
                    else:
                        with _arbiter_stats_lock:
                            stats["rejeitadas_llm_arbiter"] += 1
                        if isinstance(llm_result, dict):
                            lic["_llm_rejection_reason"] = llm_result.get("rejection_reason", "")
                        logger.debug(
                            f"[{trace_id}] Camada 3A: REJECT (LLM={prompt_level}) "
                            f"density={lic.get('_term_density', 0):.1%} "
                            f"valor=R$ {valor:,.2f} objeto={objeto[:80]}"
                        )
                        if tracker:
                            try:
                                tracker.record_rejection(
                                    "llm_reject", sector=setor,
                                    description_preview=objeto[:100],
                                )
                            except Exception:
                                pass

                    # QA Audit sampling
                    if random.random() < QA_AUDIT_SAMPLE_RATE:
                        lic["_qa_audit"] = True
                        lic["_qa_audit_decision"] = {
                            "trace_id": trace_id,
                            "llm_response": "SIM" if is_primary else "NAO",
                            "prompt_level": prompt_level,
                            "density": lic.get("_term_density", 0),
                            "matched_terms": lic.get("_matched_terms", []),
                            "valor": valor,
                            "confidence": llm_result.get("confidence") if isinstance(llm_result, dict) else None,
                            "evidence": llm_result.get("evidence") if isinstance(llm_result, dict) else None,
                            "rejection_reason": llm_result.get("rejection_reason") if isinstance(llm_result, dict) else None,
                        }

                except Exception as e:
                    with _arbiter_stats_lock:
                        stats["rejeitadas_llm_arbiter"] += 1
                    logger.error(f"Camada 3A: LLM FAILED (REJECT fallback): {e}")

    elapsed_arbiter = time.monotonic() - t0_arbiter
    logger.info(
        f"Camada 3A resultado: "
        f"{stats['aprovadas_llm_arbiter']} aprovadas, "
        f"{stats['rejeitadas_llm_arbiter']} rejeitadas, "
        f"{stats['llm_arbiter_calls']} chamadas LLM, "
        f"elapsed={elapsed_arbiter:.2f}s (parallel, {len(resultado_llm_candidates)} bids)"
    )
