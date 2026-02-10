"""
Statistics schema for PNCP search results (STORY-179 AC5).

This module defines the comprehensive statistics response schema for the
dual-flow LLM arbiter system (anti-false positive + anti-false negative).
"""

from typing import TypedDict, Optional


class SearchStats(TypedDict, total=False):
    """
    Statistics for PNCP search results.

    Includes metrics for both FLUXO 1 (anti-false positive) and FLUXO 2
    (anti-false negative) filtering pipelines.
    """

    # ============================================
    # Core Metrics
    # ============================================
    total: int  # Total contracts processed
    aprovadas: int  # Total contracts approved (final result)

    # ============================================
    # FLUXO 1: Anti-False Positive Metrics
    # ============================================

    # Camada 1A: Value Threshold
    rejeitadas_valor_alto: int  # Contracts rejected for exceeding max_contract_value

    # Camada 2A: Term Density
    aprovadas_alta_densidade: int  # Auto-approved: density > 5%
    rejeitadas_baixa_densidade: int  # Auto-rejected: density < 1%
    duvidosas_llm_arbiter: int  # Ambiguous: 1% ≤ density ≤ 5% → sent to LLM

    # Camada 3A: LLM Arbiter (False Positive Check)
    aprovadas_llm_fp_check: int  # LLM confirmed "SIM" (not a false positive)
    rejeitadas_llm_fp: int  # LLM confirmed "NAO" (was a false positive!)

    # ============================================
    # FLUXO 2: Anti-False Negative Metrics
    # ============================================

    # Camada 1B: Exclusion Recovery Candidates
    exclusion_recovery_candidates: int  # Rejected by exclusion but high density

    # Camada 2B: Synonym Matching
    aprovadas_synonym_match: int  # Auto-approved via synonym (2+ matches, no LLM)
    synonym_matches_1: int  # 1 synonym match (sent to LLM for validation)

    # Camada 3B: LLM Recovery
    recuperadas_llm_fn: int  # LLM confirmed "SIM" (false negative recovered!)
    rejeitadas_llm_fn_confirmed: int  # LLM confirmed "NAO" (rejection was valid)

    # Camada 4: Zero Results Relaxation
    zero_results_relaxation_triggered: bool  # If relaxation was attempted
    recuperadas_zero_results: int  # Contracts recovered via relaxation

    # ============================================
    # LLM Arbiter Aggregated Metrics
    # ============================================
    llm_arbiter_calls_total: int  # Total LLM calls (FLUXO 1 + FLUXO 2)
    llm_arbiter_calls_fp_flow: int  # LLM calls for FLUXO 1 (anti-FP)
    llm_arbiter_calls_fn_flow: int  # LLM calls for FLUXO 2 (anti-FN)
    llm_arbiter_cache_hits: int  # Cache hits (avoided LLM calls)
    llm_arbiter_cost_brl: float  # Estimated cost in BRL (calls × R$ 0.00003)

    # ============================================
    # Legacy Filter Metrics (from filter.py)
    # ============================================
    rejeitadas_uf: Optional[int]  # Rejected by UF filter
    rejeitadas_status: Optional[int]  # Rejected by status filter
    rejeitadas_esfera: Optional[int]  # Rejected by esfera filter
    rejeitadas_modalidade: Optional[int]  # Rejected by modalidade filter
    rejeitadas_municipio: Optional[int]  # Rejected by município filter
    rejeitadas_orgao: Optional[int]  # Rejected by órgão filter
    rejeitadas_keyword: Optional[int]  # Rejected by keyword matching
    rejeitadas_exclusao: Optional[int]  # Rejected by exclusion keywords
    rejeitadas_valor: Optional[int]  # Rejected by value range


# Example response with all fields
EXAMPLE_STATS_RESPONSE = {
    # Core
    "total": 10000,
    "aprovadas": 287,

    # FLUXO 1 (Anti-FP)
    "rejeitadas_valor_alto": 3000,  # 30% rejected by Camada 1A
    "aprovadas_alta_densidade": 4200,  # 60% approved by Camada 2A (density > 5%)
    "rejeitadas_baixa_densidade": 700,  # 10% rejected by Camada 2A (density < 1%)
    "duvidosas_llm_arbiter": 2100,  # Sent to Camada 3A
    "aprovadas_llm_fp_check": 1890,  # LLM: "SIM" (90% of ambiguous)
    "rejeitadas_llm_fp": 210,  # LLM: "NAO" (10% of ambiguous - were FP!)

    # FLUXO 2 (Anti-FN)
    "exclusion_recovery_candidates": 500,  # Camada 1B candidates
    "aprovadas_synonym_match": 320,  # Camada 2B auto-approved
    "synonym_matches_1": 180,  # Sent to Camada 3B
    "recuperadas_llm_fn": 108,  # LLM: "SIM" (60% recovery rate)
    "rejeitadas_llm_fn_confirmed": 72,  # LLM: "NAO" (40% rejection valid)
    "zero_results_relaxation_triggered": False,
    "recuperadas_zero_results": 0,

    # LLM Aggregated
    "llm_arbiter_calls_total": 2280,  # 2100 (FP) + 180 (FN)
    "llm_arbiter_calls_fp_flow": 2100,
    "llm_arbiter_calls_fn_flow": 180,
    "llm_arbiter_cache_hits": 1824,  # 80% cache hit rate
    "llm_arbiter_cost_brl": 0.0684,  # 2280 × R$ 0.00003

    # Legacy
    "rejeitadas_uf": 0,
    "rejeitadas_status": 150,
    "rejeitadas_keyword": 800,
    "rejeitadas_exclusao": 1200,
    "rejeitadas_valor": 500,
}


# Cost estimation helper
def calculate_llm_cost(llm_calls: int) -> float:
    """
    Calculate estimated LLM arbiter cost in BRL.

    Args:
        llm_calls: Number of LLM API calls made

    Returns:
        Estimated cost in BRL (R$)

    Example:
        >>> calculate_llm_cost(2280)
        0.0684
    """
    COST_PER_CALL_BRL = 0.00003  # R$ 0.00003 per GPT-4o-mini call
    return llm_calls * COST_PER_CALL_BRL


# Performance benchmarks reference
PERFORMANCE_BENCHMARKS = {
    "target_llm_calls_percentage": 0.20,  # < 20% of contracts should use LLM
    "target_cache_hit_rate": 0.80,  # > 80% cache hit rate for repeated searches
    "target_cost_per_1k_contracts": 0.01,  # < R$ 0.01 per 1,000 contracts
    "target_false_positive_rate": 0.005,  # < 0.5%
    "target_false_negative_rate": 0.02,  # < 2%
    "target_latency_increase_ms": 150,  # < 150ms P95 increase from baseline
}
