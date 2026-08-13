"""Eligibility gate for programmatic URL clusters — #2118.

A URL enters sitemap/index only if ALL of:
  demand AND unique canonical data AND freshness AND provenance
  AND useful template AND internal linking AND commercial/intelligence relevance
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Verdict = Literal["index", "noindex", "retire"]


@dataclass(frozen=True)
class EligibilityInput:
    path: str
    family: str
    demand_score: float
    unique_canonical: bool
    freshness_ok: bool
    provenance_ok: bool
    template_useful: bool
    internal_links: int
    commercial_relevance: bool
    thin_or_duplicate: bool = False
    empty_combination: bool = False


@dataclass
class EligibilityDecision:
    verdict: Verdict
    reasons: list[str] = field(default_factory=list)
    score: float = 0.0


def score_family(
    commercial_intent: float,
    organic_demand: float,
    utility: float,
    data_quality: float,
    linking: float,
    conversion: float,
    effort: float,
) -> float:
    effort = max(effort, 0.1)
    return (
        commercial_intent
        * organic_demand
        * utility
        * data_quality
        * linking
        * conversion
    ) / effort


MVP_FAMILIES = {
    "tender": score_family(0.9, 0.8, 0.9, 0.7, 0.9, 0.8, 1.0),
    "contract": score_family(0.85, 0.75, 0.85, 0.7, 0.9, 0.75, 1.0),
    "company": score_family(0.95, 0.9, 0.9, 0.7, 0.85, 0.85, 1.1),
    "organ": score_family(0.8, 0.7, 0.8, 0.65, 0.85, 0.7, 1.0),
    "municipality": score_family(0.75, 0.7, 0.8, 0.6, 0.8, 0.7, 1.0),
    "observatory": score_family(0.7, 0.65, 0.85, 0.7, 0.8, 0.65, 1.2),
}


def decide(item: EligibilityInput) -> EligibilityDecision:
    reasons: list[str] = []
    if item.empty_combination:
        return EligibilityDecision("retire", ["empty_combination"])
    if item.thin_or_duplicate:
        return EligibilityDecision("retire", ["thin_or_duplicate"])
    if not item.unique_canonical:
        reasons.append("no_unique_canonical_data")
    if not item.freshness_ok:
        reasons.append("stale_or_unknown_freshness")
    if not item.provenance_ok:
        reasons.append("missing_provenance")
    if not item.template_useful:
        reasons.append("template_not_useful")
    if item.internal_links < 2:
        reasons.append("insufficient_internal_linking")
    if not item.commercial_relevance:
        reasons.append("no_commercial_or_intelligence_relevance")
    if item.demand_score < 0.2:
        reasons.append("no_demand_evidence")

    blocking = {
        "no_unique_canonical_data",
        "missing_provenance",
        "template_not_useful",
        "no_commercial_or_intelligence_relevance",
    }
    if blocking.intersection(reasons):
        return EligibilityDecision("noindex", reasons, item.demand_score)

    if reasons:
        return EligibilityDecision("noindex", reasons, item.demand_score)
    return EligibilityDecision("index", ["eligible"], item.demand_score)
