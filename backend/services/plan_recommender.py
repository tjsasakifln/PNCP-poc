"""STORY-BIZ-002: plan recommendation service.

Detects whether a profile is likely a consultancy (CNAE starting with 70.2,
74.9, or 82.9) and, if so, recommends the Consultoria plan (ARPU 2.5x Pro).

Pure functions only — no Supabase / Redis here. Caching happens at the
endpoint layer.
"""

from __future__ import annotations

from dataclasses import dataclass


PLAN_PRO = "smartlic_pro"
PLAN_CONSULTORIA = "consultoria"

CONSULTORIA_CNAE_PREFIXES: tuple[str, ...] = ("70.2", "74.9", "82.9")


@dataclass(frozen=True)
class PlanRecommendation:
    plan_key: str
    reason: str


def _normalize_cnae(cnae: str | None) -> str:
    """Normalize a CNAE primário string to the canonical `XX.YY` form.

    Accepts common IBGE formats:
      - "70.20-4/00" -> "70.20"
      - "70.20-4"    -> "70.20"
      - "7020-4/00"  -> "70.20"
      - "7020"       -> "70.20"
      - "70.20"      -> "70.20"
    Returns empty string when input is falsy or unparseable.
    """
    if not cnae:
        return ""

    digits = "".join(c for c in cnae if c.isdigit())
    if len(digits) < 4:
        return ""
    return f"{digits[:2]}.{digits[2:4]}"


def detect_consultoria_profile(cnae_primary: str | None) -> bool:
    """Return True when the profile's primary CNAE marks it as a consultancy.

    Matches CNAE divisions 70.2, 74.9, and 82.9 — the three IBGE codes that
    consolidate management/technical/support-to-business consulting.

    Conservative by default: empty, malformed, or unknown CNAEs return False
    (user sees the regular Pro plan, no false-positive upsell banner).
    """
    normalized = _normalize_cnae(cnae_primary)
    if not normalized:
        return False
    return any(normalized.startswith(prefix) for prefix in CONSULTORIA_CNAE_PREFIXES)


def recommend_plan(cnae_primary: str | None) -> PlanRecommendation:
    """Map a CNAE primário to a plan recommendation."""
    if detect_consultoria_profile(cnae_primary):
        return PlanRecommendation(plan_key=PLAN_CONSULTORIA, reason="cnae_consultoria")
    return PlanRecommendation(plan_key=PLAN_PRO, reason="default")
