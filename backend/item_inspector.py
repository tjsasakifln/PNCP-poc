"""
Item-level inspection for gray zone bids (GTM-RESILIENCE-D01).

Fetches individual items from PNCP API for bids in the 0-5% density zone,
applies majority rule with domain signals for more precise classification.

Key concepts:
- **Majority rule**: >50% items matching sector keywords → accept
- **Domain signals**: NCM prefixes, unit patterns, size patterns → boost matching
- **Budget**: Max N item-fetches per search (configurable via MAX_ITEM_INSPECTIONS)
- **Cache**: LRU in-memory cache (24h TTL, max 1000 entries)

Called from filter.py (sync context) using ThreadPoolExecutor for parallel fetching.
"""

import logging
import re
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx

logger = logging.getLogger(__name__)

# PNCP API base URL for item fetching
_PNCP_ITEMS_BASE = "https://pncp.gov.br/api/consulta/v1"


# ============================================================================
# AC7: In-memory LRU cache for fetched items (24h TTL, max 1000 entries)
# ============================================================================

_CACHE_MAX_SIZE = 1000
_CACHE_TTL_SECONDS = 86400  # 24 hours

# OrderedDict for LRU: key = "cnpj:ano:sequencial", value = (items_list, timestamp)
_items_cache: OrderedDict[str, Tuple[List[Dict], float]] = OrderedDict()


def _cache_key(cnpj: str, ano: str, sequencial: str) -> str:
    """Build cache key for item lookups."""
    return f"{cnpj}:{ano}:{sequencial}"


def _get_cached_items(key: str) -> Optional[List[Dict]]:
    """Get items from cache if present and not expired."""
    if key not in _items_cache:
        return None

    items, cached_at = _items_cache[key]
    if (time.time() - cached_at) > _CACHE_TTL_SECONDS:
        del _items_cache[key]
        return None

    _items_cache.move_to_end(key)
    return items


def _put_cached_items(key: str, items: List[Dict]) -> None:
    """Store items in cache, evicting oldest if over capacity."""
    _items_cache[key] = (items, time.time())
    _items_cache.move_to_end(key)

    while len(_items_cache) > _CACHE_MAX_SIZE:
        _items_cache.popitem(last=False)


def get_cache_stats() -> Dict[str, int]:
    """Return cache statistics for health endpoints."""
    return {
        "item_cache_size": len(_items_cache),
        "item_cache_max": _CACHE_MAX_SIZE,
    }


def clear_cache() -> None:
    """Clear the item cache (for testing/debugging)."""
    _items_cache.clear()
    logger.info("Item inspector cache cleared")


# ============================================================================
# AC1: Sync item fetch via httpx (called from ThreadPoolExecutor)
# ============================================================================

def _fetch_items_sync(
    cnpj: str, ano: str, sequencial: str, timeout: float = 5.0
) -> List[Dict[str, Any]]:
    """Fetch bid items from PNCP API synchronously.

    Used within ThreadPoolExecutor from the sync filter context.
    Retry 1x on 429/5xx. Returns empty list on 404 or timeout.
    """
    cnpj_clean = "".join(c for c in cnpj if c.isdigit())
    url = f"{_PNCP_ITEMS_BASE}/orgaos/{cnpj_clean}/compras/{ano}/{sequencial}/itens"

    for attempt in range(2):
        try:
            response = httpx.get(url, timeout=timeout)

            if response.status_code == 200:
                data = response.json()
                items = (
                    data
                    if isinstance(data, list)
                    else data.get("itens", data.get("data", []))
                )
                return [
                    {
                        "descricao": item.get("descricao", ""),
                        "codigoNcm": (
                            item.get("materialOuServico", {}).get("codigoNcm", "")
                            if isinstance(item.get("materialOuServico"), dict)
                            else item.get("codigoNcm", "")
                        ),
                        "unidadeMedida": item.get("unidadeMedida", ""),
                        "quantidade": item.get("quantidade", 0),
                        "valorUnitario": (
                            item.get("valorUnitarioEstimado", 0)
                            or item.get("valorUnitario", 0)
                        ),
                    }
                    for item in items
                ]

            if response.status_code == 404:
                return []

            if attempt == 0 and response.status_code in (429, 500, 502, 503, 504):
                retry_after = float(response.headers.get("Retry-After", "1"))
                time.sleep(min(retry_after, 3.0))
                continue

            return []

        except (httpx.TimeoutException, httpx.HTTPError):
            if attempt == 0:
                continue
            return []
        except Exception:
            return []

    return []


# ============================================================================
# AC4: Item classification with domain signals
# ============================================================================

def classify_item(
    item: Dict[str, Any],
    sector_keywords: Set[str],
    ncm_prefixes: List[str],
    unit_patterns: List[str],
    size_patterns: List[str],
) -> float:
    """Classify a single item against sector signals.

    Returns an "equivalent items" score:
    - 1.0 for a full keyword/NCM match
    - 0.5 for unit pattern match (boost)
    - 0.5 for size pattern match (boost)
    - Boosts are additive but capped: 1 real match + boosts = max 2.0

    Args:
        item: Dict with descricao, codigoNcm, unidadeMedida.
        sector_keywords: Keywords for the sector (lowercase).
        ncm_prefixes: NCM code prefixes.
        unit_patterns: Unit of measure patterns.
        size_patterns: Regex patterns for sizes.

    Returns:
        Float score: 0.0-2.0.
    """
    descricao = (item.get("descricao") or "").lower()
    ncm = str(item.get("codigoNcm") or "")
    unidade = (item.get("unidadeMedida") or "").lower()

    base_match = 0.0
    boost = 0.0

    # 1. NCM prefix match → full match (1.0)
    if ncm and ncm_prefixes:
        for prefix in ncm_prefixes:
            if ncm.startswith(prefix):
                base_match = 1.0
                break

    # 2. Keyword match in description → full match (1.0)
    if base_match == 0.0 and descricao and sector_keywords:
        for kw in sector_keywords:
            if kw in descricao:
                base_match = 1.0
                break

    # 3. Unit pattern match → boost 0.5
    if unidade and unit_patterns:
        for pattern in unit_patterns:
            if pattern.lower() in unidade:
                boost += 0.5
                break

    # 4. Size pattern match in description → boost 0.5
    if descricao and size_patterns:
        for pattern in size_patterns:
            try:
                if re.search(pattern, descricao, re.IGNORECASE):
                    boost += 0.5
                    break
            except re.error:
                continue

    return min(base_match + boost, 2.0)


# ============================================================================
# AC3: Majority rule
# ============================================================================

def apply_majority_rule(
    items: List[Dict[str, Any]],
    sector_keywords: Set[str],
    ncm_prefixes: List[str],
    unit_patterns: List[str],
    size_patterns: List[str],
) -> Tuple[bool, float, int, int]:
    """Apply majority rule to bid items.

    >50% items matching sector → accept.

    Returns:
        Tuple of (accepted, match_ratio, matching_count, total_count).
    """
    if not items:
        return False, 0.0, 0, 0

    matching = 0
    total = len(items)

    for item in items:
        score = classify_item(
            item, sector_keywords, ncm_prefixes, unit_patterns, size_patterns
        )
        if score >= 1.0:
            matching += 1

    ratio = matching / total if total > 0 else 0.0
    accepted = ratio > 0.5

    return accepted, ratio, matching, total


# ============================================================================
# AC2 + AC6: Sync orchestrator for filter.py integration
# ============================================================================

def inspect_bids_in_filter(
    gray_zone_bids: List[Dict[str, Any]],
    sector_keywords: Set[str],
    ncm_prefixes: List[str],
    unit_patterns: List[str],
    size_patterns: List[str],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """Inspect gray zone bids synchronously (called from filter.py).

    Uses ThreadPoolExecutor for parallel item fetching, matching the
    pattern used by LLM zero-match in filter.py.

    Args:
        gray_zone_bids: Bids with 0-5% keyword density.
        sector_keywords: Lowercase keywords for the sector.
        ncm_prefixes: NCM code prefixes for domain signals.
        unit_patterns: Unit patterns for domain signals.
        size_patterns: Size regex patterns for domain signals.

    Returns:
        Tuple of (accepted, remaining, metrics).
    """
    from config import (
        MAX_ITEM_INSPECTIONS,
        ITEM_INSPECTION_TIMEOUT,
        ITEM_INSPECTION_CONCURRENCY,
        get_feature_flag,
    )

    metrics: Dict[str, Any] = {
        "item_inspections_performed": 0,
        "item_inspections_accepted": 0,
        "item_inspections_cache_hits": 0,
        "item_fetch_total_ms": 0.0,
        "item_fetch_count": 0,
    }

    # AC8: Runtime feature flag check
    if not get_feature_flag("ITEM_INSPECTION_ENABLED"):
        return [], gray_zone_bids, metrics

    if not gray_zone_bids:
        return [], [], metrics

    budget_remaining = MAX_ITEM_INSPECTIONS
    accepted: List[Dict[str, Any]] = []
    remaining: List[Dict[str, Any]] = []
    phase_start = time.time()

    def _extract_ids(bid: Dict) -> Tuple[str, str, str]:
        """Extract cnpj, ano, sequencial from a bid dict."""
        orgao = bid.get("orgaoEntidade") or {}
        cnpj = orgao.get("cnpj", "") if isinstance(orgao, dict) else ""
        if not cnpj:
            cnpj = bid.get("cnpjOrgao", "") or bid.get("cnpj", "")
        ano = str(bid.get("anoCompra", ""))
        sequencial = str(bid.get("sequencialCompra", ""))
        return cnpj, ano, sequencial

    def _inspect_one(bid: Dict) -> Tuple[Dict, bool, bool]:
        """Inspect a single bid. Returns (bid, accepted, used_cache)."""
        cnpj, ano, sequencial = _extract_ids(bid)
        if not (cnpj and ano and sequencial):
            return bid, False, False

        key = _cache_key(cnpj, ano, sequencial)
        cached = _get_cached_items(key)

        if cached is not None:
            items = cached
            return _apply_rule(bid, items, cnpj, ano, sequencial, True)

        # Fetch from API
        start_ms = time.time() * 1000
        items = _fetch_items_sync(cnpj, ano, sequencial, timeout=ITEM_INSPECTION_TIMEOUT)
        elapsed_ms = time.time() * 1000 - start_ms

        # Cache result (even empty — avoids re-fetching 404s)
        _put_cached_items(key, items)

        return _apply_rule(bid, items, cnpj, ano, sequencial, False, elapsed_ms)

    def _apply_rule(
        bid: Dict,
        items: List[Dict],
        cnpj: str,
        ano: str,
        sequencial: str,
        was_cached: bool,
        elapsed_ms: float = 0.0,
    ) -> Tuple[Dict, bool, bool]:
        if not items:
            return bid, False, was_cached

        accepted_flag, ratio, matching, total = apply_majority_rule(
            items, sector_keywords, ncm_prefixes, unit_patterns, size_patterns
        )

        if accepted_flag:
            bid["_relevance_source"] = "item_inspection"
            bid["_item_inspection_detail"] = (
                f"{matching}/{total} items matching ({ratio:.0%})"
            )
            logger.debug(
                f"Item inspection ACCEPT: {matching}/{total} ({ratio:.0%}) "
                f"for {cnpj}/{ano}/{sequencial}"
            )

        return bid, accepted_flag, was_cached

    # Separate cache-hit bids from fetch-needed bids
    cache_hit_bids: List[Tuple[Dict, List[Dict]]] = []
    fetch_needed: List[Dict] = []

    for bid in gray_zone_bids:
        cnpj, ano, sequencial = _extract_ids(bid)
        if not (cnpj and ano and sequencial):
            remaining.append(bid)
            continue

        key = _cache_key(cnpj, ano, sequencial)
        cached = _get_cached_items(key)
        if cached is not None:
            cache_hit_bids.append((bid, cached))
            metrics["item_inspections_cache_hits"] += 1
        else:
            if budget_remaining > 0:
                fetch_needed.append(bid)
                budget_remaining -= 1
            else:
                remaining.append(bid)  # Over budget → LLM flow

    # Process cache hits immediately (no network, no budget cost)
    for bid, items in cache_hit_bids:
        bid_result, was_accepted, _ = _apply_rule(
            bid, items, *_extract_ids(bid), True
        )
        metrics["item_inspections_performed"] += 1
        if was_accepted:
            metrics["item_inspections_accepted"] += 1
            accepted.append(bid_result)
        else:
            remaining.append(bid_result)

    # Fetch items in parallel via ThreadPoolExecutor
    if fetch_needed:
        from config import ITEM_INSPECTION_PHASE_TIMEOUT

        with ThreadPoolExecutor(max_workers=ITEM_INSPECTION_CONCURRENCY) as executor:
            futures = {
                executor.submit(_inspect_one, bid): bid
                for bid in fetch_needed
            }

            for future in as_completed(futures):
                # Check phase timeout
                elapsed = time.time() - phase_start
                if elapsed > ITEM_INSPECTION_PHASE_TIMEOUT:
                    logger.warning(
                        f"Item inspection phase timeout ({ITEM_INSPECTION_PHASE_TIMEOUT}s). "
                        f"Remaining bids go to LLM."
                    )
                    # Cancel remaining futures and send to LLM
                    for f in futures:
                        f.cancel()
                    break

                try:
                    bid_result, was_accepted, was_cached = future.result(timeout=5)
                    metrics["item_inspections_performed"] += 1
                    if not was_cached:
                        metrics["item_fetch_count"] += 1

                    if was_accepted:
                        metrics["item_inspections_accepted"] += 1
                        accepted.append(bid_result)
                    else:
                        remaining.append(bid_result)
                except Exception as e:
                    logger.debug(f"Item inspection failed: {e}")
                    bid = futures[future]
                    remaining.append(bid)

        # Any bids not yet processed go to remaining
        processed_ids = {id(b) for b in accepted} | {id(b) for b in remaining}
        for bid in fetch_needed:
            if id(bid) not in processed_ids:
                remaining.append(bid)

    # Compute avg fetch time
    avg_ms = (
        metrics["item_fetch_total_ms"] / metrics["item_fetch_count"]
        if metrics["item_fetch_count"] > 0
        else 0
    )
    metrics["item_fetch_avg_ms"] = round(avg_ms, 1)

    logger.info(
        f"D-01 Item inspection: "
        f"{metrics['item_inspections_performed']} inspected, "
        f"{metrics['item_inspections_accepted']} accepted, "
        f"{metrics['item_inspections_cache_hits']} cache hits"
    )

    return accepted, remaining, metrics
