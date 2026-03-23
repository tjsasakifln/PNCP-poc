"""
Centralized loader for intel_sectors_config.yaml — sector-agnostic configuration.

Provides:
  - load_intel_sectors_config() → parsed config dict
  - build_cnae_to_sector_map() → {cnae_prefix: sector_key}
  - build_sector_hints_map() → {sector_key: [hint_strings]}
  - get_cnae_refinements(cnae_prefix) → {exclude_patterns: [...], extra_include: [...]}
  - get_incompatible_objects(cnae_prefix) → [regex_pattern_strings]
  - get_llm_fallback_config() → {enabled, model, prompt_template, ...}

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


def build_cnae_to_sector_map(config: dict[str, Any] | None = None) -> dict[str, str]:
    """Build {cnae_4digit_prefix: sector_key} lookup from config.

    Example: {"4120": "engenharia", "4211": "engenharia_rodoviaria", ...}
    """
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
    """Build {sector_key: [hint_strings]} lookup from config.

    Used by map_sector() Strategy 3 for fallback matching.
    """
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


def get_cnae_refinements(
    cnae_prefix: str,
    config: dict[str, Any] | None = None,
) -> dict[str, list[str]]:
    """Get keyword refinements for a specific CNAE prefix.

    Returns: {"exclude_patterns": [...], "extra_include": [...]}
    Empty dict if no refinements defined.
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
    """Get incompatible object regex patterns for a specific CNAE prefix.

    Returns: list of regex pattern strings. Empty list if none defined.
    """
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


def get_sector_heuristic_patterns(
    sector_key: str,
    config: dict[str, Any] | None = None,
) -> dict[str, list[str]]:
    """Get heuristic classification patterns for a sector.

    Returns: {"strong_compat": [...], "strong_incompat": [...], "weak_compat": [...]}
    Empty lists for any missing pattern type.
    """
    if config is None:
        config = load_intel_sectors_config()

    sectors = config.get("sectors", {})
    sector_data = sectors.get(sector_key, {})
    if not isinstance(sector_data, dict):
        return {"strong_compat": [], "strong_incompat": [], "weak_compat": []}

    hp = sector_data.get("heuristic_patterns", {})
    if not isinstance(hp, dict):
        return {"strong_compat": [], "strong_incompat": [], "weak_compat": []}

    return {
        "strong_compat": hp.get("strong_compat", []),
        "strong_incompat": hp.get("strong_incompat", []),
        "weak_compat": hp.get("weak_compat", []),
    }


def get_llm_fallback_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Get LLM fallback configuration for unknown CNAEs.

    Returns: {enabled, model, max_concurrent, timeout_s, on_failure, prompt_template}
    """
    if config is None:
        config = load_intel_sectors_config()

    return config.get("llm_fallback", {
        "enabled": False,
        "model": "gpt-4.1-nano",
        "max_concurrent": 5,
        "timeout_s": 10,
        "on_failure": "reject",
        "prompt_template": "",
    })
