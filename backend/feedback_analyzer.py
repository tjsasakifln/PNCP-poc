"""GTM-RESILIENCE-D05 AC6-AC7: Feedback pattern analysis and keyword suggestions.

Analyzes classification feedback to identify false positive/negative patterns
and suggest keyword improvements for the classification pipeline.
"""

import logging
import re
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)


def analyze_feedback_patterns(
    feedbacks: list[dict[str, Any]],
    sector_keywords: list[str] | None = None,
) -> dict[str, Any]:
    """Analyze feedback records and produce pattern analysis.

    Args:
        feedbacks: List of feedback records from Supabase.
        sector_keywords: Optional list of keywords for the sector being analyzed.

    Returns:
        Dict with breakdown, precision_estimate, fp_categories,
        top_fp_keywords, and suggested_exclusions.
    """
    if not feedbacks:
        return {
            "total_feedbacks": 0,
            "breakdown": {"correct": 0, "false_positive": 0, "false_negative": 0},
            "precision_estimate": None,
            "fp_categories": {},
            "top_fp_keywords": [],
            "suggested_exclusions": [],
        }

    # AC6: Breakdown
    breakdown = Counter(f.get("user_verdict", "unknown") for f in feedbacks)
    total = len(feedbacks)
    correct = breakdown.get("correct", 0)
    fp = breakdown.get("false_positive", 0)
    fn = breakdown.get("false_negative", 0)

    # Precision estimate: correct / (correct + false_positive)
    precision = None
    if (correct + fp) > 0:
        precision = round(correct / (correct + fp), 2)

    # FP category breakdown
    fp_feedbacks = [f for f in feedbacks if f.get("user_verdict") == "false_positive"]
    fp_categories = dict(Counter(f.get("category", "other") for f in fp_feedbacks))

    # AC6 + AC7: Keyword analysis on FP bid_objeto texts
    top_fp_keywords = _extract_fp_keywords(fp_feedbacks, feedbacks, sector_keywords)
    suggested_exclusions = _suggest_exclusions(fp_feedbacks, feedbacks)

    return {
        "total_feedbacks": total,
        "breakdown": {
            "correct": correct,
            "false_positive": fp,
            "false_negative": fn,
        },
        "precision_estimate": precision,
        "fp_categories": fp_categories,
        "top_fp_keywords": top_fp_keywords,
        "suggested_exclusions": suggested_exclusions,
    }


def _extract_fp_keywords(
    fp_feedbacks: list[dict],
    all_feedbacks: list[dict],
    sector_keywords: list[str] | None,
) -> list[dict[str, Any]]:
    """AC7: Find sector keywords that appear disproportionately in FP bid descriptions.

    If a keyword appears in >5 FPs and <2 corrects, suggest exclusion or co-occurrence rule.
    """
    if not sector_keywords or not fp_feedbacks:
        return []

    correct_feedbacks = [f for f in all_feedbacks if f.get("user_verdict") == "correct"]

    results = []
    for kw in sector_keywords:
        kw_lower = kw.lower()
        fp_count = sum(
            1 for f in fp_feedbacks
            if f.get("bid_objeto") and kw_lower in (f["bid_objeto"] or "").lower()
        )
        correct_count = sum(
            1 for f in correct_feedbacks
            if f.get("bid_objeto") and kw_lower in (f["bid_objeto"] or "").lower()
        )

        if fp_count > 5 and correct_count < 2:
            # Find most common co-occurring word in FP descriptions with this keyword
            co_words = _find_co_occurring_words(
                kw_lower,
                [f.get("bid_objeto", "") for f in fp_feedbacks if f.get("bid_objeto")]
            )
            suggestion = f"considerar exclusao ou co-occurrence com '{co_words[0]}'" if co_words else "considerar adicionar a exclusoes"
            results.append({
                "keyword": kw,
                "count": fp_count,
                "suggestion": suggestion,
            })

    # Sort by count descending, limit to top 10
    results.sort(key=lambda x: x["count"], reverse=True)
    return results[:10]


def _suggest_exclusions(
    fp_feedbacks: list[dict],
    all_feedbacks: list[dict],
) -> list[str]:
    """AC7: Find bi-grams frequent in FPs but not in corrects.

    Bi-grams appearing in >3 FPs and 0 corrects are suggested for exclusion.
    """
    if not fp_feedbacks:
        return []

    correct_feedbacks = [f for f in all_feedbacks if f.get("user_verdict") == "correct"]

    fp_bigrams = _extract_bigrams([f.get("bid_objeto", "") for f in fp_feedbacks if f.get("bid_objeto")])
    correct_bigrams = _extract_bigrams([f.get("bid_objeto", "") for f in correct_feedbacks if f.get("bid_objeto")])

    suggestions = []
    for bigram, count in fp_bigrams.most_common(20):
        if count >= 3 and correct_bigrams.get(bigram, 0) == 0:
            suggestions.append(bigram)

    return suggestions[:10]


def _extract_bigrams(texts: list[str]) -> Counter:
    """Extract word bi-grams from a list of texts."""
    bigrams: Counter = Counter()
    for text in texts:
        if not text:
            continue
        words = re.findall(r'\b\w+\b', text.lower())
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i + 1]}"
            bigrams[bigram] += 1
    return bigrams


def _find_co_occurring_words(keyword: str, texts: list[str]) -> list[str]:
    """Find words that commonly co-occur with a keyword in texts."""
    word_counts: Counter = Counter()
    stopwords = {
        "de", "do", "da", "dos", "das", "para", "com", "em", "por", "e",
        "a", "o", "os", "as", "um", "uma", "no", "na", "nos", "nas",
        "ao", "aos", "se", "que", "ou", "este", "esta",
    }
    for text in texts:
        if not text:
            continue
        text_lower = text.lower()
        if keyword not in text_lower:
            continue
        words = re.findall(r'\b\w+\b', text_lower)
        for word in words:
            if word != keyword and word not in stopwords and len(word) > 2:
                word_counts[word] += 1

    return [word for word, _ in word_counts.most_common(5)]
