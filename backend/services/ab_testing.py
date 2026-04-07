"""A/B testing service — deterministic variant assignment."""

import hashlib
import json
import logging
from typing import Any

from config.features import get_feature_flag

logger = logging.getLogger(__name__)

# Active experiments config from env
# Format: JSON string {"experiment_name": {"variants": ["control", "variant_a"], "description": "..."}}
_DEFAULT_EXPERIMENTS: dict[str, Any] = {}


def _get_active_experiments() -> dict[str, Any]:
    """Return active experiments from AB_ACTIVE_EXPERIMENTS env var."""
    import os
    if not get_feature_flag("ab_experiments_enabled", default=False):
        return {}
    raw = os.getenv("AB_ACTIVE_EXPERIMENTS", "{}")
    try:
        experiments = json.loads(raw)
        return experiments if isinstance(experiments, dict) else {}
    except (json.JSONDecodeError, TypeError):
        logger.warning("Invalid AB_ACTIVE_EXPERIMENTS JSON, returning empty")
        return {}


def get_variant(user_id: str, experiment: str, variants: list[str] | None = None) -> str | None:
    """Deterministic variant assignment via hash.

    Same user_id + experiment always returns same variant.
    Returns None if experiment not active or no variants configured.
    """
    if not user_id or not experiment:
        return None

    experiments = _get_active_experiments()
    exp_config = experiments.get(experiment)

    if not exp_config and not variants:
        return None

    variant_list = variants or exp_config.get("variants", [])
    if not variant_list:
        return None

    hash_input = f"{user_id}:{experiment}"
    hash_hex = hashlib.md5(hash_input.encode()).hexdigest()
    index = int(hash_hex, 16) % len(variant_list)
    return variant_list[index]


def get_user_experiments(user_id: str) -> dict[str, str]:
    """Return all active experiment variants for a user.

    Returns dict like {"cta_copy": "variant_a", "pricing_display": "control"}
    """
    if not user_id:
        return {}

    experiments = _get_active_experiments()
    result = {}
    for exp_name, exp_config in experiments.items():
        variants = exp_config.get("variants", [])
        if variants:
            variant = get_variant(user_id, exp_name, variants)
            if variant:
                result[exp_name] = variant
    return result
