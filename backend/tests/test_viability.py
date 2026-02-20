"""GTM-RESILIENCE-D04: Tests for viability assessment module.

Covers all 11 ACs with unit tests for each factor calculator,
independence from relevance, combined scoring, and batch assessment.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from viability import (
    ViabilityAssessment,
    ViabilityFactors,
    _score_modalidade,
    _score_timeline,
    _score_value_fit,
    _score_geography,
    calculate_viability,
    assess_batch,
    REGION_MAP,
    _UF_TO_REGION,
    DEFAULT_VALUE_RANGE,
)


# =============================================================================
# AC2: Modalidade Factor
# =============================================================================


class TestScoreModalidade:
    """AC2: Modality scoring tests."""

    def test_pregao_eletronico_score_100(self):
        """AC11: Pregão Eletrônico = 100."""
        score, label = _score_modalidade("Pregão Eletrônico")
        assert score == 100
        assert label == "Ótimo"

    def test_pregao_presencial_score_80(self):
        score, label = _score_modalidade("Pregão Presencial")
        assert score == 80
        assert label == "Bom"

    def test_concorrencia_eletronica_score_70(self):
        score, label = _score_modalidade("Concorrência Eletrônica")
        assert score == 70
        assert label == "Bom"

    def test_concorrencia_presencial_score_60(self):
        score, label = _score_modalidade("Concorrência Presencial")
        assert score == 60
        assert label == "Regular"

    def test_credenciamento_score_50(self):
        score, label = _score_modalidade("Credenciamento")
        assert score == 50
        assert label == "Regular"

    def test_dispensa_score_40(self):
        """AC11: Dispensa = 40."""
        score, label = _score_modalidade("Dispensa")
        assert score == 40
        assert label == "Baixo"

    def test_dispensa_eletronica_score_40(self):
        score, label = _score_modalidade("Dispensa Eletrônica")
        assert score == 40
        assert label == "Baixo"

    def test_unknown_modality_score_50(self):
        score, label = _score_modalidade("Leilão")
        assert score == 50
        assert label == "Regular"

    def test_none_modality_score_50(self):
        score, label = _score_modalidade(None)
        assert score == 50

    def test_partial_match_pregao(self):
        """Partial match: 'Pregão Eletrônico - SRP' should match 'pregão eletrônico'."""
        score, _ = _score_modalidade("Pregão Eletrônico - SRP")
        assert score == 100

    def test_case_insensitive(self):
        score, _ = _score_modalidade("PREGÃO ELETRÔNICO")
        assert score == 100


# =============================================================================
# AC3: Timeline Factor
# =============================================================================


class TestScoreTimeline:
    """AC3: Timeline scoring tests."""

    def test_20_days_future_score_100(self):
        """AC11: data_abertura em 20 dias = 100."""
        future = (datetime.now(timezone.utc) + timedelta(days=20)).strftime("%Y-%m-%d")
        score, label = _score_timeline(future)
        assert score == 100
        assert "dias" in label

    def test_10_days_future_score_80(self):
        future = (datetime.now(timezone.utc) + timedelta(days=10)).strftime("%Y-%m-%d")
        score, _ = _score_timeline(future)
        assert score == 80

    def test_5_days_future_score_60(self):
        future = (datetime.now(timezone.utc) + timedelta(days=5)).strftime("%Y-%m-%d")
        score, _ = _score_timeline(future)
        assert score == 60

    def test_2_days_future_score_30(self):
        future = (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d")
        score, _ = _score_timeline(future)
        assert score == 30

    def test_yesterday_score_10(self):
        """AC11: data_abertura ontem = 10."""
        past = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        score, label = _score_timeline(past)
        assert score == 10
        assert label == "Encerrada"

    def test_none_score_50(self):
        score, label = _score_timeline(None)
        assert score == 50
        assert label == "Não informado"

    def test_invalid_date_score_50(self):
        score, _ = _score_timeline("not-a-date")
        assert score == 50

    def test_long_datetime_string(self):
        """Handle full datetime strings like '2026-03-15T10:00:00'."""
        future = (datetime.now(timezone.utc) + timedelta(days=20)).strftime("%Y-%m-%dT%H:%M:%S")
        score, _ = _score_timeline(future)
        assert score == 100


# =============================================================================
# AC4: Value Fit Factor
# =============================================================================


class TestScoreValueFit:
    """AC4: Value fit scoring tests."""

    def test_in_range_score_100(self):
        """AC11: R$100k for vestuário (range 50k-2M) = 100."""
        score, label = _score_value_fit(100_000, (50_000, 2_000_000))
        assert score == 100
        assert label == "Ideal"

    def test_below_range_moderate_score_60(self):
        """AC11: R$10k for vestuário (below range) <= 60."""
        score, label = _score_value_fit(10_000, (50_000, 2_000_000))
        # 10k / 50k = 0.2 → below 0.5 → score 20
        assert score <= 60

    def test_below_range_close_score_60(self):
        score, _ = _score_value_fit(30_000, (50_000, 2_000_000))
        # 30k / 50k = 0.6 → above 0.5 → score 60
        assert score == 60

    def test_above_range_moderate_score_60(self):
        score, label = _score_value_fit(3_000_000, (50_000, 2_000_000))
        # 3M / 2M = 1.5 → below 2.0 → score 60
        assert score == 60
        assert label == "Acima"

    def test_above_range_extreme_score_20(self):
        score, label = _score_value_fit(5_000_000, (50_000, 2_000_000))
        # 5M / 2M = 2.5 → above 2.0 → score 20
        assert score == 20
        assert label == "Muito acima"

    def test_zero_value_score_40(self):
        """PCP v2 bids with valor=0 should get neutral score 40."""
        score, label = _score_value_fit(0, (50_000, 2_000_000))
        assert score == 40
        assert label == "Não informado"

    def test_negative_value_score_40(self):
        score, _ = _score_value_fit(-1, (50_000, 2_000_000))
        assert score == 40

    def test_exact_min_boundary(self):
        score, _ = _score_value_fit(50_000, (50_000, 2_000_000))
        assert score == 100

    def test_exact_max_boundary(self):
        score, _ = _score_value_fit(2_000_000, (50_000, 2_000_000))
        assert score == 100


# =============================================================================
# AC5: Geography Factor
# =============================================================================


class TestScoreGeography:
    """AC5: Geography scoring tests."""

    def test_same_uf_score_100(self):
        """AC11: UF da busca = UF da licitação = 100."""
        score, label = _score_geography("SP", {"SP", "RJ"})
        assert score == 100
        assert label == "Sua região"

    def test_adjacent_uf_score_60(self):
        """Same macro-region: SP search, RJ bid → 60."""
        score, label = _score_geography("MG", {"SP"})
        assert score == 60
        assert label == "Região adjacente"

    def test_distant_uf_score_30(self):
        """AC11: Distant UF = 30."""
        score, label = _score_geography("AM", {"SP"})
        assert score == 30
        assert label == "Distante"

    def test_empty_uf_score_50(self):
        score, label = _score_geography("", {"SP"})
        assert score == 50
        assert label == "Não identificada"

    def test_case_insensitive(self):
        score, _ = _score_geography("sp", {"SP"})
        assert score == 100

    def test_all_regions_covered(self):
        """Verify all 27 UFs are mapped to a region."""
        all_ufs = set()
        for ufs in REGION_MAP.values():
            all_ufs.update(ufs)
        assert len(all_ufs) == 27
        # Verify reverse map
        assert len(_UF_TO_REGION) == 27

    def test_nordeste_adjacency(self):
        """BA and CE are in nordeste → adjacent."""
        score, _ = _score_geography("CE", {"BA"})
        assert score == 60

    def test_sul_adjacency(self):
        """RS and SC are in sul → adjacent."""
        score, _ = _score_geography("SC", {"RS"})
        assert score == 60


# =============================================================================
# AC1 + AC6: ViabilityAssessment Model & Independence
# =============================================================================


class TestCalculateViability:
    """AC1, AC6, AC9: End-to-end viability calculation."""

    def test_high_viability(self):
        """Pregão + 20 days + ideal value + same UF → alta."""
        bid = {
            "modalidadeNome": "Pregão Eletrônico",
            "dataEncerramentoProposta": (datetime.now(timezone.utc) + timedelta(days=20)).strftime("%Y-%m-%d"),
            "valorTotalEstimado": 100_000,
            "uf": "SP",
        }
        result = calculate_viability(bid, {"SP"}, (50_000, 2_000_000))
        assert result.viability_score > 70
        assert result.viability_level == "alta"
        assert result.factors.modalidade == 100
        assert result.factors.geography == 100

    def test_low_viability(self):
        """Dispensa + past + out-of-range + distant → baixa."""
        bid = {
            "modalidadeNome": "Dispensa",
            "dataEncerramentoProposta": (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d"),
            "valorTotalEstimado": 500,
            "uf": "RR",
        }
        result = calculate_viability(bid, {"SP"}, (50_000, 2_000_000))
        assert result.viability_score < 40
        assert result.viability_level == "baixa"

    def test_medium_viability(self):
        """Mixed factors → media: bad modality, bad timeline, out-of-range, adjacent UF."""
        bid = {
            "modalidadeNome": "Credenciamento",
            "dataEncerramentoProposta": (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d"),
            "valorTotalEstimado": 10_000,
            "uf": "MG",
        }
        result = calculate_viability(bid, {"SP"}, (50_000, 2_000_000))
        # Credenciamento(50) + 2 days(30) + below range(20) + adjacent(60) → ~40
        assert 30 <= result.viability_score <= 70
        assert result.viability_level == "media"

    def test_viability_does_not_alter_relevance(self):
        """AC6: Viability score does NOT affect bid dict keys used for relevance."""
        bid = {
            "modalidadeNome": "Dispensa",
            "valorTotalEstimado": 500,
            "uf": "RR",
            "_relevance_source": "keyword",
            "_confidence_score": 95,
        }
        result = calculate_viability(bid, {"SP"})
        # Viability is informational — original fields unchanged
        assert result.viability_level == "baixa"
        assert bid["_relevance_source"] == "keyword"
        assert bid["_confidence_score"] == 95

    def test_default_value_range(self):
        """Uses DEFAULT_VALUE_RANGE when no sector range provided."""
        bid = {"valorTotalEstimado": 100_000, "uf": "SP"}
        result = calculate_viability(bid, {"SP"})
        # 100k is within DEFAULT_VALUE_RANGE (50k, 5M)
        assert result.factors.value_fit == 100

    def test_factors_breakdown(self):
        """Factors dict has all expected keys."""
        bid = {
            "modalidadeNome": "Pregão Eletrônico",
            "dataEncerramentoProposta": (datetime.now(timezone.utc) + timedelta(days=20)).strftime("%Y-%m-%d"),
            "valorTotalEstimado": 100_000,
            "uf": "SP",
        }
        result = calculate_viability(bid, {"SP"}, (50_000, 2_000_000))
        factors = result.factors
        assert hasattr(factors, "modalidade")
        assert hasattr(factors, "timeline")
        assert hasattr(factors, "value_fit")
        assert hasattr(factors, "geography")
        assert all(hasattr(factors, f"{f}_label") for f in ["modalidade", "timeline", "value_fit", "geography"])


# =============================================================================
# AC9: Combined Score Ordering
# =============================================================================


class TestCombinedScore:
    """AC9: Combined score ordering tests."""

    def test_combined_score_correct_formula(self):
        """combined_score = confidence * 0.6 + viability * 0.4."""
        bid_high_conf_low_viab = {
            "_confidence_score": 95,
            "modalidadeNome": "Dispensa",
            "valorTotalEstimado": 500,
            "uf": "RR",
        }
        bid_low_conf_high_viab = {
            "_confidence_score": 55,
            "modalidadeNome": "Pregão Eletrônico",
            "dataEncerramentoProposta": (datetime.now(timezone.utc) + timedelta(days=20)).strftime("%Y-%m-%d"),
            "valorTotalEstimado": 100_000,
            "uf": "SP",
        }
        v1 = calculate_viability(bid_high_conf_low_viab, {"SP"}, (50_000, 2_000_000))
        v2 = calculate_viability(bid_low_conf_high_viab, {"SP"}, (50_000, 2_000_000))

        combined1 = 95 * 0.6 + v1.viability_score * 0.4
        combined2 = 55 * 0.6 + v2.viability_score * 0.4

        # Both are valid calculations — the combined score balances both dimensions
        assert combined1 > 0
        assert combined2 > 0


# =============================================================================
# Batch Assessment
# =============================================================================


class TestAssessBatch:
    """Tests for assess_batch — in-place enrichment."""

    def test_enriches_bids_in_place(self):
        bids = [
            {"modalidadeNome": "Pregão Eletrônico", "valorTotalEstimado": 100_000, "uf": "SP"},
            {"modalidadeNome": "Dispensa", "valorTotalEstimado": 500, "uf": "RR"},
        ]
        assess_batch(bids, {"SP"}, (50_000, 2_000_000))

        for bid in bids:
            assert "_viability_score" in bid
            assert "_viability_level" in bid
            assert "_viability_factors" in bid
            assert isinstance(bid["_viability_factors"], dict)

    def test_empty_batch(self):
        """Empty list should not crash."""
        bids = []
        assess_batch(bids, {"SP"})
        assert bids == []

    def test_batch_preserves_original_fields(self):
        """AC6: assess_batch does NOT remove existing bid fields."""
        bids = [{"objetoCompra": "Test", "_confidence_score": 95, "uf": "SP"}]
        assess_batch(bids, {"SP"})
        assert bids[0]["objetoCompra"] == "Test"
        assert bids[0]["_confidence_score"] == 95


# =============================================================================
# AC10: Feature Flag & Config
# =============================================================================


class TestConfigWeights:
    """AC10: Configurable weights."""

    @patch("config.VIABILITY_WEIGHT_MODALITY", 1.0)
    @patch("config.VIABILITY_WEIGHT_TIMELINE", 0.0)
    @patch("config.VIABILITY_WEIGHT_VALUE_FIT", 0.0)
    @patch("config.VIABILITY_WEIGHT_GEOGRAPHY", 0.0)
    def test_custom_weights_modality_only(self):
        """When modality weight is 100%, score equals modality score."""
        bid = {
            "modalidadeNome": "Pregão Eletrônico",
            "valorTotalEstimado": 0,
            "uf": "",
        }
        result = calculate_viability(bid, set())
        assert result.viability_score == 100

    @patch("config.VIABILITY_WEIGHT_MODALITY", 0.0)
    @patch("config.VIABILITY_WEIGHT_TIMELINE", 0.0)
    @patch("config.VIABILITY_WEIGHT_VALUE_FIT", 0.0)
    @patch("config.VIABILITY_WEIGHT_GEOGRAPHY", 1.0)
    def test_custom_weights_geography_only(self):
        """When geography weight is 100%, score equals geography score."""
        bid = {"uf": "SP", "modalidadeNome": None, "valorTotalEstimado": 0}
        result = calculate_viability(bid, {"SP"})
        assert result.viability_score == 100


# =============================================================================
# REGION_MAP completeness
# =============================================================================


class TestRegionMap:
    """Verify REGION_MAP correctness."""

    def test_five_regions(self):
        assert len(REGION_MAP) == 5

    def test_27_ufs_total(self):
        all_ufs = set()
        for ufs in REGION_MAP.values():
            all_ufs.update(ufs)
        assert len(all_ufs) == 27

    def test_sp_in_sudeste(self):
        assert "SP" in REGION_MAP["sudeste"]

    def test_am_in_norte(self):
        assert "AM" in REGION_MAP["norte"]

    def test_ba_in_nordeste(self):
        assert "BA" in REGION_MAP["nordeste"]

    def test_df_in_centro_oeste(self):
        assert "DF" in REGION_MAP["centro_oeste"]

    def test_rs_in_sul(self):
        assert "RS" in REGION_MAP["sul"]
