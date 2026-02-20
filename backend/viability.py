"""GTM-RESILIENCE-D04: Viability Assessment — orthogonal to relevance classification.

Calculates a 0-100 viability score for accepted bids based on four deterministic factors:
- Modalidade (30%): procurement modality accessibility
- Timeline (25%): days until proposal deadline
- Value Fit (25%): bid value vs sector ideal range
- Geography (20%): proximity to user's search regions

Result maps to levels: Alta (>70), Média (40-70), Baixa (<40).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

import config

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================


class ViabilityFactors(BaseModel):
    """Breakdown of individual factor scores."""

    modalidade: int = Field(ge=0, le=100)
    modalidade_label: str = ""
    timeline: int = Field(ge=0, le=100)
    timeline_label: str = ""
    value_fit: int = Field(ge=0, le=100)
    value_fit_label: str = ""
    geography: int = Field(ge=0, le=100)
    geography_label: str = ""


class ViabilityAssessment(BaseModel):
    """Complete viability assessment for a single bid."""

    viability_score: int = Field(ge=0, le=100)
    viability_level: Literal["alta", "media", "baixa"]
    factors: ViabilityFactors


# =============================================================================
# Constants
# =============================================================================

# AC2: Modalidade scores — lower barrier = higher score
MODALITY_SCORES: dict[str, int] = {
    "pregão eletrônico": 100,
    "pregao eletronico": 100,
    "pregão": 100,
    "pregao": 100,
    "pregão presencial": 80,
    "pregao presencial": 80,
    "concorrência eletrônica": 70,
    "concorrencia eletronica": 70,
    "concorrência": 70,
    "concorrencia": 70,
    "concorrência presencial": 60,
    "concorrencia presencial": 60,
    "credenciamento": 50,
    "dispensa": 40,
    "dispensa eletrônica": 40,
    "dispensa eletronica": 40,
    "dispensa de licitação": 40,
    "dispensa de licitacao": 40,
}
DEFAULT_MODALITY_SCORE = 50

# AC5: Brazilian macro-regions for geography scoring
REGION_MAP: dict[str, list[str]] = {
    "norte": ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
    "nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "centro_oeste": ["DF", "GO", "MS", "MT"],
    "sudeste": ["ES", "MG", "RJ", "SP"],
    "sul": ["PR", "RS", "SC"],
}

# Reverse map: UF → region name
_UF_TO_REGION: dict[str, str] = {}
for _region, _ufs in REGION_MAP.items():
    for _uf in _ufs:
        _UF_TO_REGION[_uf] = _region

# Default value range when sector doesn't specify one
DEFAULT_VALUE_RANGE: tuple[float, float] = (50_000, 5_000_000)


# =============================================================================
# Factor Calculators
# =============================================================================


def _score_modalidade(modalidade: str | None) -> tuple[int, str]:
    """AC2: Score based on procurement modality accessibility."""
    if not modalidade:
        return DEFAULT_MODALITY_SCORE, "Não informada"

    mod_lower = modalidade.strip().lower()

    # Try exact match first
    if mod_lower in MODALITY_SCORES:
        score = MODALITY_SCORES[mod_lower]
    else:
        # Partial match: check if any key is contained in the modalidade string
        score = DEFAULT_MODALITY_SCORE
        for key, val in MODALITY_SCORES.items():
            if key in mod_lower:
                score = val
                break

    if score >= 90:
        label = "Ótimo"
    elif score >= 70:
        label = "Bom"
    elif score >= 50:
        label = "Regular"
    else:
        label = "Baixo"

    return score, label


def _score_timeline(data_str: str | None) -> tuple[int, str]:
    """AC3: Score based on days until proposal opening/deadline."""
    if not data_str:
        return 50, "Não informado"

    try:
        dt_str = data_str[:10]  # YYYY-MM-DD
        dt = datetime.strptime(dt_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        days_until = (dt - now).days

        if days_until > 14:
            return 100, f"{days_until} dias"
        elif days_until >= 7:
            return 80, f"{days_until} dias"
        elif days_until >= 3:
            return 60, f"{days_until} dias"
        elif days_until >= 1:
            return 30, f"{days_until} dia(s)"
        else:
            return 10, "Encerrada"
    except (ValueError, TypeError):
        return 50, "Não informado"


def _score_value_fit(
    valor: float, value_range: tuple[float, float]
) -> tuple[int, str]:
    """AC4: Score based on value proximity to sector ideal range."""
    val_min, val_max = value_range

    # PCP v2 and others may have valor=0
    if valor <= 0:
        return 40, "Não informado"

    # Within ideal range
    if val_min <= valor <= val_max:
        return 100, "Ideal"

    # Below range
    if valor < val_min:
        ratio = valor / val_min if val_min > 0 else 0
        if ratio >= 0.5:
            return 60, "Abaixo"
        else:
            return 20, "Muito abaixo"

    # Above range
    ratio = valor / val_max if val_max > 0 else 999
    if ratio <= 2.0:
        return 60, "Acima"
    else:
        return 20, "Muito acima"


def _score_geography(uf_licitacao: str, ufs_busca: set[str]) -> tuple[int, str]:
    """AC5: Score based on geographic proximity to user's search regions."""
    if not uf_licitacao:
        return 50, "Não identificada"

    uf_upper = uf_licitacao.upper().strip()

    # Direct match: user searched for this UF
    if uf_upper in ufs_busca:
        return 100, "Sua região"

    # Adjacent: same macro-region as any searched UF
    region_lic = _UF_TO_REGION.get(uf_upper)
    if region_lic:
        for uf_busca in ufs_busca:
            region_busca = _UF_TO_REGION.get(uf_busca.upper())
            if region_busca and region_busca == region_lic:
                return 60, "Região adjacente"

    # Distant
    return 30, "Distante"


# =============================================================================
# Main Assessment Function
# =============================================================================


def calculate_viability(
    bid: dict,
    ufs_busca: set[str],
    value_range: tuple[float, float] | None = None,
) -> ViabilityAssessment:
    """Calculate viability assessment for a single accepted bid.

    Args:
        bid: Raw bid dictionary (internal format with PNCP/PCP field names).
        ufs_busca: Set of UF codes the user selected for the search.
        value_range: (min, max) value range for the sector. Uses DEFAULT_VALUE_RANGE if None.

    Returns:
        ViabilityAssessment with composite score, level, and factor breakdown.
    """
    vr = value_range or DEFAULT_VALUE_RANGE

    # Get weights from config
    w_mod = getattr(config, "VIABILITY_WEIGHT_MODALITY", 0.30)
    w_tl = getattr(config, "VIABILITY_WEIGHT_TIMELINE", 0.25)
    w_vf = getattr(config, "VIABILITY_WEIGHT_VALUE_FIT", 0.25)
    w_geo = getattr(config, "VIABILITY_WEIGHT_GEOGRAPHY", 0.20)

    # Calculate each factor
    mod_score, mod_label = _score_modalidade(
        bid.get("modalidadeNome") or bid.get("modalidade")
    )

    tl_score, tl_label = _score_timeline(
        bid.get("dataEncerramentoProposta") or bid.get("dataAberturaProposta")
    )

    valor = float(bid.get("valorTotalEstimado") or bid.get("valorEstimado") or 0)
    vf_score, vf_label = _score_value_fit(valor, vr)

    geo_score, geo_label = _score_geography(bid.get("uf", ""), ufs_busca)

    # Composite score
    raw_score = (
        mod_score * w_mod
        + tl_score * w_tl
        + vf_score * w_vf
        + geo_score * w_geo
    )
    composite = max(0, min(100, round(raw_score)))

    # Map to level
    if composite > 70:
        level: Literal["alta", "media", "baixa"] = "alta"
    elif composite >= 40:
        level = "media"
    else:
        level = "baixa"

    return ViabilityAssessment(
        viability_score=composite,
        viability_level=level,
        factors=ViabilityFactors(
            modalidade=mod_score,
            modalidade_label=mod_label,
            timeline=tl_score,
            timeline_label=tl_label,
            value_fit=vf_score,
            value_fit_label=vf_label,
            geography=geo_score,
            geography_label=geo_label,
        ),
    )


def assess_batch(
    bids: list[dict],
    ufs_busca: set[str],
    value_range: tuple[float, float] | None = None,
) -> None:
    """Calculate viability for a batch of bids, enriching them in-place.

    Adds _viability_score, _viability_level, and _viability_factors to each bid dict.

    Args:
        bids: List of bid dicts (modified in-place).
        ufs_busca: UFs selected by user.
        value_range: Sector-specific value range.
    """
    for bid in bids:
        assessment = calculate_viability(bid, ufs_busca, value_range)
        bid["_viability_score"] = assessment.viability_score
        bid["_viability_level"] = assessment.viability_level
        bid["_viability_factors"] = assessment.factors.model_dump()
