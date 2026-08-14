"""pSEO eligibility gate — #2118."""

from pseo.eligibility import EligibilityInput, MVP_FAMILIES, decide, score_family


def test_mvp_families_ranked():
    assert set(MVP_FAMILIES) >= {
        "tender",
        "contract",
        "company",
        "organ",
        "municipality",
        "observatory",
    }
    assert score_family(1, 1, 1, 1, 1, 1, 1) == 1


def test_empty_combination_is_retired():
    decision = decide(
        EligibilityInput(
            path="/contratos/setor-vazio/zz",
            family="contract",
            demand_score=0.9,
            unique_canonical=True,
            freshness_ok=True,
            provenance_ok=True,
            template_useful=True,
            internal_links=4,
            commercial_relevance=True,
            empty_combination=True,
        )
    )
    assert decision.verdict == "retire"


def test_eligible_url_is_indexable():
    decision = decide(
        EligibilityInput(
            path="/cnpj/00000000000191",
            family="company",
            demand_score=0.8,
            unique_canonical=True,
            freshness_ok=True,
            provenance_ok=True,
            template_useful=True,
            internal_links=3,
            commercial_relevance=True,
        )
    )
    assert decision.verdict == "index"


def test_missing_provenance_is_noindex():
    decision = decide(
        EligibilityInput(
            path="/licitacoes/foo",
            family="tender",
            demand_score=0.5,
            unique_canonical=True,
            freshness_ok=True,
            provenance_ok=False,
            template_useful=True,
            internal_links=3,
            commercial_relevance=True,
        )
    )
    assert decision.verdict == "noindex"
    assert "missing_provenance" in decision.reasons
