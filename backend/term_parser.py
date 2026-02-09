"""Intelligent search term parser for procurement keyword filtering.

Supports two parsing modes:
- Comma mode: when input contains commas, uses commas as delimiters (phrase mode)
- Space mode: when input has no commas, splits by whitespace (legacy/backward compatible)

STORY-178 AC1: Parsing Inteligente de Termos de Busca
"""

import logging
import re
import unicodedata
from typing import List

from filter import STOPWORDS_PT

logger = logging.getLogger(__name__)


def parse_search_terms(raw_input: str) -> List[str]:
    """Parse user search input into structured search terms.

    Strategy: if input contains commas, use commas as delimiters (phrase mode).
    If no commas, fall back to space-as-delimiter (legacy mode).

    Args:
        raw_input: Raw user input string.

    Returns:
        List of normalized, deduplicated search terms.
        Empty list if input is empty or only contains stopwords.
    """
    if not raw_input or not raw_input.strip():
        return []

    # Sanitize: convert smart quotes to normal, normalize whitespace
    sanitized = _sanitize_input(raw_input)

    if not sanitized:
        return []

    # AC1.1: Presence of comma activates phrase mode; absence preserves legacy mode
    if "," in sanitized:
        terms = _parse_comma_mode(sanitized)
    else:
        terms = _parse_space_mode(sanitized)

    # AC1.3: Deduplicate after normalization
    terms = _deduplicate(terms)

    return terms


def _sanitize_input(raw: str) -> str:
    """Sanitize raw input: normalize whitespace, convert smart quotes.

    AC1.5: Newlines treated as space. Smart quotes converted to normal.
    """
    # Convert smart quotes to normal quotes
    result = raw.replace("\u201c", '"').replace("\u201d", '"')
    result = result.replace("\u2018", "'").replace("\u2019", "'")

    # Normalize all whitespace (newlines, tabs, multiple spaces) to single space
    result = re.sub(r"\s+", " ", result).strip()

    return result


def _parse_comma_mode(raw: str) -> List[str]:
    """Split by comma, trim each segment, remove empty, apply stopword rules.

    AC1.1: Comma as delimiter for phrase mode.
    AC1.2: Stopwords removed only from single-word terms.
    AC1.5: Empty segments ignored, leading/trailing commas ignored.
    """
    segments = raw.split(",")
    terms = []

    for segment in segments:
        term = segment.strip()

        if not term:
            continue

        # Normalize: lowercase
        term = term.lower()

        # AC1.2: Remove stopwords only from single-word terms
        words = term.split()
        if len(words) == 1:
            normalized = _normalize_for_stopword_check(term)
            if normalized in STOPWORDS_PT:
                continue
        # Multi-word terms preserve stopwords internally (AC1.2)

        terms.append(term)

    return terms


def _parse_space_mode(raw: str) -> List[str]:
    """Split by whitespace, remove stopwords. Backward compatible with existing behavior.

    AC1.1: No commas = legacy space-delimited mode.
    """
    words = raw.strip().lower().split()
    terms = []

    for word in words:
        word = word.strip()
        if not word:
            continue

        normalized = _normalize_for_stopword_check(word)
        if normalized not in STOPWORDS_PT:
            terms.append(word)

    return terms


def _normalize_for_stopword_check(term: str) -> str:
    """Normalize a term for stopword comparison: lowercase, remove accents."""
    text = term.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text


def _deduplicate(terms: List[str]) -> List[str]:
    """Deduplicate terms preserving order. Uses normalized form for comparison."""
    seen = set()
    result = []
    for term in terms:
        normalized = _normalize_for_stopword_check(term)
        if normalized not in seen:
            seen.add(normalized)
            result.append(term)
    return result
