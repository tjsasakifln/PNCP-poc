"""DEBT-110 AC4: Density scoring and proximity checks.

Extracted from filter.py. Contains proximity context filtering
and co-occurrence pattern detection.
"""

import logging
import re
from typing import Dict, Optional, Tuple

from filter.keywords import normalize_text

logger = logging.getLogger(__name__)


def check_proximity_context(
    texto: str,
    matched_terms: list,
    current_sector: str,
    other_sectors_signatures: Dict[str, set],
    window_size: int = 8,
) -> Tuple[bool, Optional[str]]:
    """Check if matched keywords appear near signature terms of other sectors.

    When a keyword from the current sector matches, extracts a window of N words
    around each match position. If the window contains signature terms of ANOTHER
    sector, the bid is rejected as a cross-sector false positive.

    Args:
        texto: The bid's objetoCompra text (raw, will be normalized).
        matched_terms: List of keywords that matched in this bid.
        current_sector: The sector ID being evaluated.
        other_sectors_signatures: Dict mapping other sector IDs to their signature terms.
        window_size: Number of words before/after match to examine (default 8).

    Returns:
        Tuple of (should_reject: bool, reason: str | None).
        If should_reject is True, reason contains the rejection detail
        (e.g., "keyword:confeccao near alimentos:merenda").
    """
    if not texto or not matched_terms or window_size <= 0:
        return (False, None)

    texto_norm = normalize_text(texto)
    words = texto_norm.split()

    if not words:
        return (False, None)

    for term in matched_terms:
        term_norm = normalize_text(term)
        term_words = term_norm.split()
        term_len = len(term_words)

        # Find all positions where this term starts in the word array
        positions = []
        for i in range(len(words) - term_len + 1):
            if words[i:i + term_len] == term_words:
                positions.append(i)

        for pos in positions:
            # Extract window around the matched term
            win_start = max(0, pos - window_size)
            win_end = min(len(words), pos + term_len + window_size)
            window_words = words[win_start:win_end]
            window_text = " ".join(window_words)

            # Check signature terms of each OTHER sector
            for other_sector, sigs in other_sectors_signatures.items():
                for sig in sigs:
                    sig_norm = normalize_text(sig)
                    # Multi-word signature: check substring in window text
                    if " " in sig_norm:
                        if sig_norm in window_text:
                            return (
                                True,
                                f"keyword:{term} near {other_sector}:{sig}",
                            )
                    else:
                        # Single-word signature: check membership in window words
                        if sig_norm in window_words:
                            return (
                                True,
                                f"keyword:{term} near {other_sector}:{sig}",
                            )

    return (False, None)


# GTM-RESILIENCE-D03: Co-occurrence Negative Pattern Engine (Camada 1B.5)
# ============================================================================
# Deterministic, zero-LLM-cost check that detects false positive keyword
# matches by evaluating trigger + negative_context combinations.
# Runs AFTER keyword match, BEFORE density zone.
# ============================================================================

def check_co_occurrence(
    texto: str,
    rules: list,
    setor_id: str,
) -> tuple:
    """Check if a bid text triggers any co-occurrence rejection rule.

    GTM-RESILIENCE-D03 AC2: Evaluates trigger + negative_context + positive_signal
    combinations to detect false positive keyword matches.

    Args:
        texto: The bid's objetoCompra text (raw, will be normalized internally).
        rules: List of CoOccurrenceRule objects for this sector.
        setor_id: Sector ID (for logging/tracking).

    Returns:
        Tuple of (should_reject: bool, reason: str | None).
        If should_reject is True, reason contains the rejection detail.
    """
    if not rules or not texto:
        return (False, None)

    texto_norm = normalize_text(texto)

    for rule in rules:
        trigger_norm = normalize_text(rule.trigger)

        # AC2: Word boundary match for trigger (prefix matching)
        trigger_pattern = re.compile(
            rf'\b{re.escape(trigger_norm)}\w*\b', re.UNICODE
        )
        if not trigger_pattern.search(texto_norm):
            continue

        # Check negative contexts (prefix word-boundary match for singles,
        # substring for multi-word)
        matched_negative = None
        for neg_ctx in rule.negative_contexts:
            neg_norm = normalize_text(neg_ctx)
            # Multi-word negative contexts use substring match,
            # single-word uses prefix word boundary (handles plurals)
            if " " in neg_norm:
                if neg_norm in texto_norm:
                    matched_negative = neg_ctx
                    break
            else:
                neg_pattern = re.compile(
                    rf'\b{re.escape(neg_norm)}\w*\b', re.UNICODE
                )
                if neg_pattern.search(texto_norm):
                    matched_negative = neg_ctx
                    break

        if matched_negative is None:
            continue

        # Check positive signals (substring match — more permissive, AC2)
        has_positive = False
        for pos_sig in rule.positive_signals:
            pos_norm = normalize_text(pos_sig)
            if pos_norm in texto_norm:
                has_positive = True
                break

        if not has_positive:
            reason = f"trigger:{rule.trigger} + negative:{matched_negative}"
            return (True, reason)

    return (False, None)
