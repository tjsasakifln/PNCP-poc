"""STORY-BIZ-002: tests for plan_recommender.detect_consultoria_profile.

Target precision: >=90% on the AC1 validation sample.
"""

import pytest

from services.plan_recommender import (
    PLAN_CONSULTORIA,
    PLAN_PRO,
    _normalize_cnae,
    detect_consultoria_profile,
    recommend_plan,
)


# ---------------------------------------------------------------------------
# CNAE normalization
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, normalized",
    [
        ("70.20-4/00", "70.20"),
        ("70.20-4", "70.20"),
        ("70.20", "70.20"),
        ("7020-4/00", "70.20"),
        ("7020", "70.20"),
        ("74.90-1/04", "74.90"),
        ("82.99-7/00", "82.99"),
        ("  70.20-4/00  ", "70.20"),
    ],
)
def test_normalize_cnae_standard_formats(raw, normalized):
    assert _normalize_cnae(raw) == normalized


@pytest.mark.parametrize("raw", ["", None, "abc", "12", "XX.YY"])
def test_normalize_cnae_unparseable(raw):
    assert _normalize_cnae(raw) == ""


# ---------------------------------------------------------------------------
# Consultoria detection — positives
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cnae",
    [
        "70.20-4/00",   # Consultoria em gestão empresarial
        "70.20",
        "70.20-4/99",
        "74.90-1/04",   # Outras atividades profissionais cientificas/tecnicas
        "74.90",
        "82.99-7/00",   # Outros servicos combinados de apoio a empresas
        "82.99",
    ],
)
def test_detect_consultoria_accepts_known_codes(cnae):
    assert detect_consultoria_profile(cnae) is True


# ---------------------------------------------------------------------------
# Consultoria detection — negatives
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cnae",
    [
        "62.01-5/01",   # Desenvolvimento de software sob encomenda (TI)
        "41.20-4/00",   # Construcao de edificios
        "47.71-7/01",   # Varejo de vestuario
        "64.20-4/00",   # Holdings
        "70.10-7/00",   # Sede da empresa — divisao 70.1 (NAO 70.2)
        "74.10-2/02",   # Fotografia — divisao 74.1 (NAO 74.9)
        "82.20-2/00",   # Atividades de teleatendimento — divisao 82.2 (NAO 82.9)
        "",
        None,
    ],
)
def test_detect_consultoria_rejects_non_consultancy(cnae):
    assert detect_consultoria_profile(cnae) is False


def test_detect_consultoria_sample_precision():
    """Validate AC1 precision target (>=90%) on curated sample."""
    positives = [
        "70.20-4/00", "70.20-4/99", "74.90-1/04", "82.99-7/00", "70.20",
        "74.90", "82.99",
    ]
    negatives = [
        "62.01-5/01", "41.20-4/00", "47.71-7/01", "70.10-7/00",
        "74.10-2/02", "82.20-2/00", "64.20-4/00",
    ]

    tp = sum(1 for c in positives if detect_consultoria_profile(c))
    tn = sum(1 for c in negatives if not detect_consultoria_profile(c))
    total = len(positives) + len(negatives)
    accuracy = (tp + tn) / total
    assert accuracy >= 0.9, f"accuracy={accuracy:.2%} on 14-sample set"


# ---------------------------------------------------------------------------
# recommend_plan
# ---------------------------------------------------------------------------


def test_recommend_plan_consultoria_for_consultancy_cnae():
    rec = recommend_plan("70.20-4/00")
    assert rec.plan_key == PLAN_CONSULTORIA
    assert rec.reason == "cnae_consultoria"


def test_recommend_plan_pro_by_default():
    rec = recommend_plan("62.01-5/01")
    assert rec.plan_key == PLAN_PRO
    assert rec.reason == "default"


def test_recommend_plan_pro_for_missing_cnae():
    rec = recommend_plan(None)
    assert rec.plan_key == PLAN_PRO
    assert rec.reason == "default"
