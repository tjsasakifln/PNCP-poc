"""
Multi-sector configuration for BidIQ procurement search.

Each sector defines a keyword set and exclusion list used by filter.py
to identify relevant procurement opportunities in PNCP data.

Sector data is loaded from sectors_data.yaml at startup.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

import yaml


@dataclass(frozen=True)
class DomainSignals:
    """Domain-specific signals for item-level inspection (GTM-RESILIENCE-D01 AC4).

    Used by item_inspector.py to classify individual bid items beyond keyword matching.

    Attributes:
        ncm_prefixes: NCM code prefixes (e.g., ["61", "62"] for vestuario).
                      If item's codigoNcm starts with any prefix → full match.
        unit_patterns: Unit of measure patterns (e.g., ["peça", "kit"]).
                       If item's unidadeMedida contains pattern → 0.5 boost.
        size_patterns: Size patterns in descriptions (e.g., ["\\bP\\b", "\\bM\\b", "\\bG\\b"]).
                       If item's descricao matches pattern → 0.5 boost.
    """

    ncm_prefixes: List[str] = field(default_factory=list)
    unit_patterns: List[str] = field(default_factory=list)
    size_patterns: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CoOccurrenceRule:
    """A co-occurrence rule for detecting false positive keyword matches.

    GTM-RESILIENCE-D03: When a trigger keyword is found together with a
    negative context term, and no positive signal is present, the bid is
    rejected as a false positive.

    Attributes:
        trigger: Keyword prefix to match (regex word-boundary).
        negative_contexts: Terms whose presence alongside trigger indicates FP.
        positive_signals: Terms that rescue the bid (substring match, permissive).
    """

    trigger: str
    negative_contexts: List[str]
    positive_signals: List[str] = field(default_factory=list)


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
    # GTM-RESILIENCE-D03: Co-occurrence rules for false positive detection
    co_occurrence_rules: List[CoOccurrenceRule] = field(default_factory=list)
    # GTM-RESILIENCE-D01: Domain signals for item-level inspection
    domain_signals: DomainSignals = field(default_factory=DomainSignals)


def _load_sectors_from_yaml() -> Dict[str, SectorConfig]:
    """Load sector configurations from the YAML data file.

    Returns:
        Dict mapping sector ID to SectorConfig.
    """
    _logger = logging.getLogger(__name__)
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

        # GTM-RESILIENCE-D03: Parse co_occurrence_rules
        co_rules_raw = cfg.get("co_occurrence_rules", [])
        co_rules: List[CoOccurrenceRule] = []
        for rule_data in co_rules_raw:
            trigger = rule_data.get("trigger", "")
            neg = rule_data.get("negative_contexts", [])
            pos = rule_data.get("positive_signals", [])
            co_rules.append(CoOccurrenceRule(
                trigger=trigger,
                negative_contexts=neg,
                positive_signals=pos,
            ))
            # AC1: Validate trigger is subset of sector keywords (warning if not)
            # Check if any keyword starts with the trigger (prefix match)
            trigger_lower = trigger.lower()
            has_matching_keyword = any(
                kw.lower().startswith(trigger_lower) for kw in keywords
            )
            if not has_matching_keyword:
                _logger.warning(
                    f"Co-occurrence trigger '{trigger}' in sector '{sector_id}' "
                    f"does not match any keyword prefix — may never fire"
                )

        # GTM-RESILIENCE-D01: Parse domain_signals
        ds_raw = cfg.get("domain_signals", {})
        domain_signals = DomainSignals(
            ncm_prefixes=ds_raw.get("ncm_prefixes", []),
            unit_patterns=ds_raw.get("unit_patterns", []),
            size_patterns=ds_raw.get("size_patterns", []),
        )

        sectors[sector_id] = SectorConfig(
            id=sector_id,
            name=cfg["name"],
            description=cfg["description"],
            keywords=keywords,
            exclusions=exclusions,
            context_required_keywords=context_required_keywords,
            max_contract_value=cfg.get("max_contract_value"),
            co_occurrence_rules=co_rules,
            domain_signals=domain_signals,
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
