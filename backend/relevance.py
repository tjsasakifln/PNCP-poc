"""Relevance scoring and minimum match floor for search term filtering.

STORY-178 AC2: Matching com Correspondência Mínima e Scoring

Provides:
- score_relevance(): Calculate relevance score (0.0 - 1.0)
- calculate_min_matches(): Calculate minimum match floor
- should_include(): Determine if a bid passes the minimum match filter
"""

import logging
from math import ceil

logger = logging.getLogger(__name__)

# Configurable constants (overridable via environment variables in main.py)
PHRASE_MATCH_BONUS = 0.15
MIN_MATCH_DIVISOR = 3
MIN_MATCH_CAP = 3


def score_relevance(
    matched_count: int,
    total_terms: int,
    phrase_match_count: int = 0,
) -> float:
    """Calculate relevance score (0.0 - 1.0).

    Formula: min(1.0, matched_count/total_terms + 0.15 * phrase_match_count)
    Guard: total_terms == 0 → 0.0

    AC2.1: No weighted terms. All terms have equal weight (1.0x).
    No generic term list. No character length heuristic.

    Args:
        matched_count: Number of terms that matched in the bid text.
        total_terms: Total number of search terms.
        phrase_match_count: Number of multi-word terms that matched as exact phrases.

    Returns:
        Relevance score between 0.0 and 1.0.
    """
    if total_terms == 0:
        return 0.0

    base_score = matched_count / total_terms
    phrase_bonus = PHRASE_MATCH_BONUS * phrase_match_count
    return min(1.0, base_score + phrase_bonus)


def calculate_min_matches(total_terms: int) -> int:
    """Calculate minimum match floor.

    Formula: max(1, min(ceil(total_terms / 3), 3))

    AC2.2: Adaptive threshold that requires multiple term matches
    when the user provides multiple terms.

    | total_terms | min_matches | Rationale                              |
    |-------------|-------------|----------------------------------------|
    | 1           | 1           | Identical to current behavior           |
    | 2           | 1           | Identical to current behavior           |
    | 3           | 1           | Identical to current behavior           |
    | 4-6         | 2           | Requires minimum overlap                |
    | 7-9         | 3 (cap)     | Avoids excessive exclusion              |
    | 10+         | 3 (cap)     | Cap preserves recall for broad searches |

    Args:
        total_terms: Total number of search terms.

    Returns:
        Minimum number of terms that must match for inclusion.
    """
    if total_terms <= 0:
        return 1

    return max(1, min(ceil(total_terms / MIN_MATCH_DIVISOR), MIN_MATCH_CAP))


def should_include(
    matched_count: int,
    total_terms: int,
    has_phrase_match: bool,
) -> bool:
    """Determine if a bid passes the minimum match filter.

    AC2.2: A bid is included if:
    - matched_count >= min_matches (Condition A), OR
    - at least 1 multi-word phrase matched as exact sequence (Condition B)

    Condition B is a strong signal that overrides the minimum match floor,
    because an exact multi-word phrase match indicates high relevance.

    Args:
        matched_count: Number of terms that matched.
        total_terms: Total number of search terms.
        has_phrase_match: Whether at least one multi-word phrase matched exactly.

    Returns:
        True if the bid should be included in results.
    """
    min_matches = calculate_min_matches(total_terms)

    # Condition A: enough terms matched
    if matched_count >= min_matches:
        return True

    # Condition B: phrase match override
    if has_phrase_match:
        return True

    return False


def count_phrase_matches(matched_terms: list[str]) -> int:
    """Count how many matched terms are multi-word phrases.

    NI-2: A multi-word term present in matched_terms means it matched
    as a sequence (because match_keywords() uses \\b{keyword}\\b regex
    on the full keyword).

    Args:
        matched_terms: List of terms that matched in the bid text.

    Returns:
        Number of multi-word phrase matches.
    """
    return sum(1 for t in matched_terms if " " in t)
