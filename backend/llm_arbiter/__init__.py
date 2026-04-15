"""LLM arbiter package — facade re-export for backwards compatibility.

TD-009: llm_arbiter.py (1362 LOC) split into:
  - prompt_builder.py  — all prompt construction functions
  - classification.py  — OpenAI client, cache, LLMClassification, classify_contract_primary_match
  - zero_match.py      — batch classification and contract recovery

All original symbols re-exported here so that `from llm_arbiter import X`
continues to work without any changes in callers (AC2 — zero broken imports).
"""

# prompt_builder: all prompt construction functions
from llm_arbiter.prompt_builder import (
    _SECTOR_NEGATIVE_EXAMPLES,
    _STRUCTURED_JSON_INSTRUCTION,
    _build_conservative_prompt,
    _build_standard_sector_prompt,
    _build_term_search_prompt,
    _build_zero_match_batch_prompt,
    _build_zero_match_batch_prompt_terms,
    _build_zero_match_prompt,
    _get_sector_negative_examples,
)

# classification: core LLM logic
from llm_arbiter.classification import (
    LLM_ENABLED,
    LLM_MAX_TOKENS,
    LLM_MODEL,
    LLM_STRUCTURED_MAX_TOKENS,
    LLM_TEMPERATURE,
    LLMClassification,
    _ARBITER_CACHE_MAX,
    _ARBITER_REDIS_PREFIX,
    _KNOWN_PREFIXES,
    _PRICING_INPUT_PER_M,
    _PRICING_OUTPUT_PER_M,
    _arbiter_cache,
    _arbiter_cache_get_redis,
    _arbiter_cache_set,
    _arbiter_cache_set_redis,
    _get_client,
    _get_usd_to_brl,
    _log_token_usage,
    _parse_structured_response,
    _strip_evidence_prefix,
    classify_contract_primary_match,
    clear_cache,
    get_cache_stats,
    get_parse_stats,
    get_search_cost_stats,
)

# zero_match: batch and recovery functions
from llm_arbiter.zero_match import (
    _classify_zero_match_batch,
    _parse_batch_response,
    classify_contract_recovery,
)

# STORY-4.1 (TD-SYS-014): Async runtime + Batch API
from llm_arbiter.async_runtime import (  # noqa: F401
    _bounded,
    _get_async_client,
    _get_semaphore,
    gather_classifications,
    get_max_concurrent,
    reset_semaphore,
    run_bounded_in_thread,
)
from llm_arbiter.batch_api import (  # noqa: F401
    list_pending_batch_ids,
    poll_batch,
    submit_batch,
)

__all__ = [
    # prompt_builder
    "_SECTOR_NEGATIVE_EXAMPLES",
    "_STRUCTURED_JSON_INSTRUCTION",
    "_build_conservative_prompt",
    "_build_standard_sector_prompt",
    "_build_term_search_prompt",
    "_build_zero_match_batch_prompt",
    "_build_zero_match_batch_prompt_terms",
    "_build_zero_match_prompt",
    "_get_sector_negative_examples",
    # classification
    "LLM_ENABLED",
    "LLM_MAX_TOKENS",
    "LLM_MODEL",
    "LLM_STRUCTURED_MAX_TOKENS",
    "LLM_TEMPERATURE",
    "LLMClassification",
    "_ARBITER_CACHE_MAX",
    "_ARBITER_REDIS_PREFIX",
    "_KNOWN_PREFIXES",
    "_PRICING_INPUT_PER_M",
    "_PRICING_OUTPUT_PER_M",
    "_arbiter_cache",
    "_arbiter_cache_get_redis",
    "_arbiter_cache_set",
    "_arbiter_cache_set_redis",
    "_get_client",
    "_get_usd_to_brl",
    "_log_token_usage",
    "_parse_structured_response",
    "_strip_evidence_prefix",
    "classify_contract_primary_match",
    "clear_cache",
    "get_cache_stats",
    "get_parse_stats",
    "get_search_cost_stats",
    # zero_match
    "_classify_zero_match_batch",
    "_parse_batch_response",
    "classify_contract_recovery",
]
