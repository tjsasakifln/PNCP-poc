"""
Centralized loader for intel_sectors_config.yaml — sector-agnostic configuration.

ALL sector-specific logic is data-driven from YAML. Zero hardcoding in Python.

Provides:
  - load_intel_sectors_config() → parsed config dict
  - build_cnae_to_sector_map() → {cnae_prefix: sector_key}
  - build_sector_hints_map() → {sector_key: [hint_strings]}
  - get_cnae_refinements(cnae_prefix) → {exclude_patterns, extra_include}
  - get_incompatible_objects(cnae_prefix) → [regex_patterns]
  - get_sector_heuristic_patterns(sector_key) → {strong_compat, strong_incompat, weak_compat}
  - get_llm_fallback_config() → {enabled, model, prompt_template, ...}
  - get_cross_sector_exclusions(sector_key) → [phrases]
  - get_competition_keywords(sector_key) → [keywords]
  - get_weight_profile(sector_key) → {hab, fin, geo, prazo, comp}
  - get_base_win_rate(sector_key) → float
  - get_habilitacao_requirements(sector_key) → {capital_minimo_pct, atestados, certifications, fiscal}
  - get_timeline_rules(sector_key) → [{max_value, min_days}, ...]
  - get_priority_modalidades(sector_key) → [int]
  - get_cnae_gate_threshold(sector_key) → float
  - get_all_cross_sector_exclusions() → {sector_key: [phrases]}
  - get_all_competition_keywords() → {sector_key: [keywords]}

Used by: collect-report-data.py, intel-collect.py
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


# Cache to avoid re-reading the file on every call
_CONFIG_CACHE: dict[str, Any] | None = None
_CONFIG_PATH_CACHE: str | None = None


def _find_config_path() -> str | None:
    """Locate intel_sectors_config.yaml relative to common project layouts."""
    candidates = [
        Path("backend/intel_sectors_config.yaml"),
        Path("../backend/intel_sectors_config.yaml"),
        Path(__file__).parent.parent / "backend" / "intel_sectors_config.yaml",
    ]
    for c in candidates:
        if c.exists():
            return str(c.resolve())
    return None


def load_intel_sectors_config(config_path: str | None = None) -> dict[str, Any]:
    """Load and cache the intel sectors config YAML.

    Returns the full parsed dict. Raises FileNotFoundError if not found.
    """
    global _CONFIG_CACHE, _CONFIG_PATH_CACHE

    if config_path is None:
        config_path = _find_config_path()
    if config_path is None:
        raise FileNotFoundError("intel_sectors_config.yaml not found")

    # Return cached if same path
    if _CONFIG_CACHE is not None and _CONFIG_PATH_CACHE == config_path:
        return _CONFIG_CACHE

    if yaml is None:
        raise ImportError("pyyaml not installed")

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    _CONFIG_CACHE = data
    _CONFIG_PATH_CACHE = config_path
    return data


def invalidate_cache() -> None:
    """Clear the cached config (useful for tests)."""
    global _CONFIG_CACHE, _CONFIG_PATH_CACHE
    _CONFIG_CACHE = None
    _CONFIG_PATH_CACHE = None


# ---------------------------------------------------------------------------
# Tier 2: Lookup maps (built once, cached)
# ---------------------------------------------------------------------------

def build_cnae_to_sector_map(config: dict[str, Any] | None = None) -> dict[str, str]:
    """Build {cnae_4digit_prefix: sector_key} lookup from config."""
    if config is None:
        config = load_intel_sectors_config()

    sectors = config.get("sectors", {})
    result: dict[str, str] = {}
    for sector_key, sector_data in sectors.items():
        if not isinstance(sector_data, dict):
            continue
        for prefix in sector_data.get("cnae_prefixes", []):
            result[str(prefix)] = sector_key
    return result


def build_sector_hints_map(config: dict[str, Any] | None = None) -> dict[str, list[str]]:
    """Build {sector_key: [hint_strings]} lookup from config."""
    if config is None:
        config = load_intel_sectors_config()

    sectors = config.get("sectors", {})
    result: dict[str, list[str]] = {}
    for sector_key, sector_data in sectors.items():
        if not isinstance(sector_data, dict):
            continue
        hints = sector_data.get("sector_hints", [])
        if hints:
            result[sector_key] = hints
    return result


# ---------------------------------------------------------------------------
# Tier 3: Per-CNAE detail accessors
# ---------------------------------------------------------------------------

def get_cnae_refinements(
    cnae_prefix: str,
    config: dict[str, Any] | None = None,
) -> dict[str, list[str]]:
    """Get keyword refinements for a specific CNAE prefix.

    Returns: {"exclude_patterns": [...], "extra_include": [...]}
    """
    if config is None:
        config = load_intel_sectors_config()

    sectors = config.get("sectors", {})
    for sector_data in sectors.values():
        if not isinstance(sector_data, dict):
            continue
        refinements = sector_data.get("cnae_refinements", {})
        if isinstance(refinements, dict) and cnae_prefix in refinements:
            return refinements[cnae_prefix]
    return {}


def get_incompatible_objects(
    cnae_prefix: str,
    config: dict[str, Any] | None = None,
) -> list[str]:
    """Get incompatible object regex patterns for a specific CNAE prefix."""
    if config is None:
        config = load_intel_sectors_config()

    sectors = config.get("sectors", {})
    for sector_data in sectors.values():
        if not isinstance(sector_data, dict):
            continue
        incompat = sector_data.get("incompatible_objects", {})
        if isinstance(incompat, dict) and cnae_prefix in incompat:
            return incompat[cnae_prefix]
    return []


# ---------------------------------------------------------------------------
# Tier 3: Per-sector detail accessors
# ---------------------------------------------------------------------------

def _get_sector_data(sector_key: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Internal helper: get sector data dict, empty dict if not found."""
    if config is None:
        config = load_intel_sectors_config()
    sectors = config.get("sectors", {})
    data = sectors.get(sector_key, {})
    return data if isinstance(data, dict) else {}


def _get_defaults(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Internal helper: get sector_defaults from config."""
    if config is None:
        config = load_intel_sectors_config()
    return config.get("sector_defaults", {})


def get_sector_heuristic_patterns(
    sector_key: str,
    config: dict[str, Any] | None = None,
) -> dict[str, list[str]]:
    """Get heuristic classification patterns for a sector.

    Returns: {"strong_compat": [...], "strong_incompat": [...], "weak_compat": [...]}
    """
    sector_data = _get_sector_data(sector_key, config)
    hp = sector_data.get("heuristic_patterns", {})
    if not isinstance(hp, dict):
        return {"strong_compat": [], "strong_incompat": [], "weak_compat": []}

    return {
        "strong_compat": hp.get("strong_compat", []),
        "strong_incompat": hp.get("strong_incompat", []),
        "weak_compat": hp.get("weak_compat", []),
    }


def get_cross_sector_exclusions(
    sector_key: str,
    config: dict[str, Any] | None = None,
) -> list[str]:
    """Get cross-sector exclusion phrases for a sector.

    These are phrases that indicate an edital is NOT for this sector.
    Example: for 'engenharia', exclusions include 'medicamento', 'uniforme', etc.
    """
    if config is None:
        config = load_intel_sectors_config()
    sector_data = _get_sector_data(sector_key, config)
    result = sector_data.get("cross_sector_exclusions")
    if result is not None:
        return result
    return _get_defaults(config).get("cross_sector_exclusions", [])


def get_competition_keywords(
    sector_key: str,
    config: dict[str, Any] | None = None,
) -> list[str]:
    """Get competition-filtering keywords for a sector.

    Used to filter competitive intelligence contracts to sector-relevant ones.
    """
    if config is None:
        config = load_intel_sectors_config()
    sector_data = _get_sector_data(sector_key, config)
    result = sector_data.get("competition_keywords")
    if result is not None:
        return result
    return _get_defaults(config).get("competition_keywords", [])


def get_weight_profile(
    sector_key: str,
    config: dict[str, Any] | None = None,
) -> dict[str, float]:
    """Get viability scoring weight profile for a sector.

    Returns: {"hab": float, "fin": float, "geo": float, "prazo": float, "comp": float}
    Weights must sum to 1.0.
    """
    if config is None:
        config = load_intel_sectors_config()
    sector_data = _get_sector_data(sector_key, config)
    result = sector_data.get("weight_profile")
    if result is not None and isinstance(result, dict):
        return result
    return _get_defaults(config).get("weight_profile", {
        "hab": 0.25, "fin": 0.25, "geo": 0.15, "prazo": 0.20, "comp": 0.15,
    })


def get_base_win_rate(
    sector_key: str,
    config: dict[str, Any] | None = None,
) -> float:
    """Get base win rate for a sector (0.0-1.0)."""
    if config is None:
        config = load_intel_sectors_config()
    sector_data = _get_sector_data(sector_key, config)
    result = sector_data.get("base_win_rate")
    if result is not None:
        return float(result)
    return float(_get_defaults(config).get("base_win_rate", 0.10))


def get_habilitacao_requirements(
    sector_key: str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Get habilitação requirements for a sector.

    Returns: {"capital_minimo_pct": float, "atestados": [...], "certifications": [...], "fiscal": [...]}
    """
    if config is None:
        config = load_intel_sectors_config()
    sector_data = _get_sector_data(sector_key, config)
    result = sector_data.get("habilitacao")
    if result is not None and isinstance(result, dict):
        return result
    return _get_defaults(config).get("habilitacao", {
        "capital_minimo_pct": 0.10,
        "atestados": ["Atestado de fornecimento ou serviço similar"],
        "certifications": [],
        "fiscal": ["CND Federal/Previdenciária", "CND Municipal", "CRF FGTS", "CNDT Trabalhista"],
    })


def get_timeline_rules(
    sector_key: str,
    config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Get timeline rules for a sector.

    Returns: [{"max_value": float|None, "min_days": int}, ...]
    Ordered by max_value ascending. null means infinity.
    """
    if config is None:
        config = load_intel_sectors_config()
    sector_data = _get_sector_data(sector_key, config)
    result = sector_data.get("timeline_rules")
    if result is not None and isinstance(result, list):
        return result
    return _get_defaults(config).get("timeline_rules", [
        {"max_value": 500000, "min_days": 15},
        {"max_value": 2000000, "min_days": 30},
        {"max_value": None, "min_days": 45},
    ])


def get_priority_modalidades(
    sector_key: str,
    config: dict[str, Any] | None = None,
) -> list[int]:
    """Get priority modalidades for a sector.

    Returns list of modalidade codes (e.g., [4, 5, 6]).
    """
    if config is None:
        config = load_intel_sectors_config()
    sector_data = _get_sector_data(sector_key, config)
    result = sector_data.get("priority_modalidades")
    if result is not None and isinstance(result, list):
        return result
    return _get_defaults(config).get("priority_modalidades", [5, 4, 6, 8])


def get_cnae_gate_threshold(
    sector_key: str,
    config: dict[str, Any] | None = None,
) -> float:
    """Get CNAE gate confidence threshold for a sector (0.0-1.0)."""
    if config is None:
        config = load_intel_sectors_config()
    sector_data = _get_sector_data(sector_key, config)
    result = sector_data.get("cnae_gate_threshold")
    if result is not None:
        return float(result)
    return float(_get_defaults(config).get("cnae_gate_threshold", 0.45))


def get_llm_fallback_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Get LLM fallback configuration.

    Now applies to ANY sector with low confidence, not just unknown CNAEs.
    """
    if config is None:
        config = load_intel_sectors_config()

    return config.get("llm_fallback", {
        "enabled": False,
        "model": "gpt-4.1-nano",
        "max_concurrent": 5,
        "timeout_s": 10,
        "on_failure": "reject",
        "confidence_threshold": 0.40,
        "prompt_template": "",
    })


# ---------------------------------------------------------------------------
# Tier 4: Bulk accessors (all sectors at once)
# ---------------------------------------------------------------------------

def get_all_cnae_refinements(config: dict[str, Any] | None = None) -> dict[str, dict[str, list[str]]]:
    """Get ALL CNAE refinements across all sectors.

    Returns: {cnae_prefix: {"exclude_patterns": [...], "extra_include": [...]}}
    """
    if config is None:
        config = load_intel_sectors_config()

    sectors = config.get("sectors", {})
    result: dict[str, dict[str, list[str]]] = {}
    for sector_data in sectors.values():
        if not isinstance(sector_data, dict):
            continue
        refinements = sector_data.get("cnae_refinements", {})
        if isinstance(refinements, dict):
            for cnae_prefix, ref_data in refinements.items():
                if isinstance(ref_data, dict):
                    result[str(cnae_prefix)] = ref_data
    return result


def get_all_incompatible_objects(config: dict[str, Any] | None = None) -> dict[str, list[str]]:
    """Get ALL incompatible object patterns across all sectors.

    Returns: {cnae_prefix: [regex_pattern_strings]}
    """
    if config is None:
        config = load_intel_sectors_config()

    sectors = config.get("sectors", {})
    result: dict[str, list[str]] = {}
    for sector_data in sectors.values():
        if not isinstance(sector_data, dict):
            continue
        incompat = sector_data.get("incompatible_objects", {})
        if isinstance(incompat, dict):
            for cnae_prefix, patterns in incompat.items():
                if isinstance(patterns, list) and patterns:
                    result[str(cnae_prefix)] = patterns
    return result


def get_all_cross_sector_exclusions(config: dict[str, Any] | None = None) -> dict[str, list[str]]:
    """Get ALL cross-sector exclusions across all sectors.

    Returns: {sector_key: [exclusion_phrases]}
    """
    if config is None:
        config = load_intel_sectors_config()

    sectors = config.get("sectors", {})
    result: dict[str, list[str]] = {}
    for sector_key, sector_data in sectors.items():
        if not isinstance(sector_data, dict):
            continue
        exclusions = sector_data.get("cross_sector_exclusions", [])
        if exclusions:
            result[sector_key] = exclusions
    return result


def get_all_competition_keywords(config: dict[str, Any] | None = None) -> dict[str, list[str]]:
    """Get ALL competition keywords across all sectors.

    Returns: {sector_key: [keywords]}
    """
    if config is None:
        config = load_intel_sectors_config()

    sectors = config.get("sectors", {})
    result: dict[str, list[str]] = {}
    for sector_key, sector_data in sectors.items():
        if not isinstance(sector_data, dict):
            continue
        keywords = sector_data.get("competition_keywords", [])
        if keywords:
            result[sector_key] = keywords
    return result


def get_all_weight_profiles(config: dict[str, Any] | None = None) -> dict[str, dict[str, float]]:
    """Get ALL weight profiles across all sectors.

    Returns: {sector_key: {"hab": float, "fin": float, ...}}
    """
    if config is None:
        config = load_intel_sectors_config()

    defaults = _get_defaults(config)
    default_profile = defaults.get("weight_profile", {
        "hab": 0.25, "fin": 0.25, "geo": 0.15, "prazo": 0.20, "comp": 0.15,
    })

    sectors = config.get("sectors", {})
    result: dict[str, dict[str, float]] = {}
    for sector_key, sector_data in sectors.items():
        if not isinstance(sector_data, dict):
            continue
        profile = sector_data.get("weight_profile")
        if profile and isinstance(profile, dict):
            result[sector_key] = profile
        else:
            result[sector_key] = default_profile
    result["_default"] = default_profile
    return result


def get_all_base_win_rates(config: dict[str, Any] | None = None) -> dict[str, float]:
    """Get ALL base win rates across all sectors.

    Returns: {sector_key: float}
    """
    if config is None:
        config = load_intel_sectors_config()

    defaults = _get_defaults(config)
    default_rate = float(defaults.get("base_win_rate", 0.10))

    sectors = config.get("sectors", {})
    result: dict[str, float] = {}
    for sector_key, sector_data in sectors.items():
        if not isinstance(sector_data, dict):
            continue
        rate = sector_data.get("base_win_rate")
        if rate is not None:
            result[sector_key] = float(rate)
        else:
            result[sector_key] = default_rate
    result["_default"] = default_rate
    return result


def get_all_habilitacao_requirements(config: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    """Get ALL habilitação requirements across all sectors.

    Returns: {sector_key: {"capital_minimo_pct": float, ...}}
    """
    if config is None:
        config = load_intel_sectors_config()

    defaults = _get_defaults(config)
    default_hab = defaults.get("habilitacao", {
        "capital_minimo_pct": 0.10,
        "atestados": ["Atestado de fornecimento ou serviço similar"],
        "certifications": [],
        "fiscal": ["CND Federal/Previdenciária", "CND Municipal", "CRF FGTS", "CNDT Trabalhista"],
    })

    sectors = config.get("sectors", {})
    result: dict[str, dict[str, Any]] = {}
    for sector_key, sector_data in sectors.items():
        if not isinstance(sector_data, dict):
            continue
        hab = sector_data.get("habilitacao")
        if hab and isinstance(hab, dict):
            result[sector_key] = hab
        else:
            result[sector_key] = default_hab
    result["_default"] = default_hab
    return result
