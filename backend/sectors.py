"""
Multi-sector configuration for BidIQ procurement search.

Each sector defines a keyword set and exclusion list used by filter.py
to identify relevant procurement opportunities in PNCP data.

Sector data is loaded from sectors_data.yaml at startup.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

import yaml


@dataclass(frozen=True)
class SectorConfig:
    """Configuration for a procurement sector."""

    id: str
    name: str
    description: str
    keywords: Set[str]
    exclusions: Set[str] = field(default_factory=set)
    # Maps generic/ambiguous keywords to a set of context keywords.
    # A generic keyword only matches if at least one of its context keywords
    # is also found in the procurement text.  This prevents broad terms like
    # "mesa" or "banco" from matching unrelated procurements.
    context_required_keywords: Dict[str, Set[str]] = field(default_factory=dict)
    # STORY-179 AC1: Maximum contract value threshold (anti-false positive)
    # Contracts above this value are rejected as likely multi-sector infrastructure
    # projects with tangential mentions of this sector (e.g., R$ 47.6M "melhorias
    # urbanas" with R$ 50K uniformes). None = no limit (e.g., engenharia).
    max_contract_value: Optional[int] = None


def _load_sectors_from_yaml() -> Dict[str, SectorConfig]:
    """Load sector configurations from the YAML data file.

    Returns:
        Dict mapping sector ID to SectorConfig.
    """
    yaml_path = os.path.join(os.path.dirname(__file__), "sectors_data.yaml")
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    sectors: Dict[str, SectorConfig] = {}
    for sector_id, cfg in data["sectors"].items():
        # Convert lists to sets for keywords, exclusions
        keywords = set(cfg.get("keywords", []))
        exclusions = set(cfg.get("exclusions", []))

        # Convert context_required_keywords: dict of lists -> dict of sets
        crk_raw = cfg.get("context_required_keywords", {})
        context_required_keywords = {
            k: set(v) for k, v in crk_raw.items()
        }

        sectors[sector_id] = SectorConfig(
            id=sector_id,
            name=cfg["name"],
            description=cfg["description"],
            keywords=keywords,
            exclusions=exclusions,
            context_required_keywords=context_required_keywords,
            max_contract_value=cfg.get("max_contract_value"),
        )

    return sectors


SECTORS: Dict[str, SectorConfig] = _load_sectors_from_yaml()


def get_sector(sector_id: str) -> SectorConfig:
    """
    Get sector configuration by ID.

    Args:
        sector_id: Sector identifier (e.g., "vestuario", "alimentos")

    Returns:
        SectorConfig for the requested sector

    Raises:
        KeyError: If sector_id not found
    """
    if sector_id not in SECTORS:
        raise KeyError(
            f"Setor '{sector_id}' não encontrado. "
            f"Setores disponíveis: {list(SECTORS.keys())}"
        )
    return SECTORS[sector_id]


def list_sectors() -> List[dict]:
    """
    List all available sectors for frontend consumption.

    Returns:
        List of dicts with id, name, description for each sector.
    """
    return [
        {"id": s.id, "name": s.name, "description": s.description}
        for s in SECTORS.values()
    ]
