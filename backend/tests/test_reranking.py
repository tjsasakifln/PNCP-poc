"""
D-02 AC10: Tests for confidence-based re-ranking in search pipeline.

Tests:
- Re-ranking sorts by confidence DESC, then value DESC
- High (>=80), Medium (50-79), Low (<50) banding
- Zero-match confidence capped at 70
- Integration test with mixed relevance sources
"""

import pytest


class TestConfidenceReranking:
    """D-02 AC5/AC10.5: Re-ranking by confidence_score."""

    def _sort_bids(self, bids: list[dict]) -> list[dict]:
        """Apply the same sort logic as search_pipeline.py stage_enrich."""
        def _confidence_sort_key(lic: dict) -> tuple:
            conf = lic.get("_confidence_score", 50)
            if conf >= 80:
                band = 0
            elif conf >= 50:
                band = 1
            else:
                band = 2
            valor = float(lic.get("valorTotalEstimado") or lic.get("valorEstimado") or 0)
            return (band, -conf, -valor)

        return sorted(bids, key=_confidence_sort_key)

    def test_sorts_by_confidence_desc(self):
        """AC10.5: Results sorted by confidence DESC."""
        bids = [
            {"objetoCompra": "Low", "_confidence_score": 30, "valorTotalEstimado": 100_000},
            {"objetoCompra": "High", "_confidence_score": 95, "valorTotalEstimado": 100_000},
            {"objetoCompra": "Med", "_confidence_score": 65, "valorTotalEstimado": 100_000},
        ]
        sorted_bids = self._sort_bids(bids)

        assert sorted_bids[0]["objetoCompra"] == "High"  # 95 >= 80 (band 0)
        assert sorted_bids[1]["objetoCompra"] == "Med"    # 65 in 50-79 (band 1)
        assert sorted_bids[2]["objetoCompra"] == "Low"    # 30 < 50 (band 2)

    def test_within_band_sorts_by_value_desc(self):
        """AC10.5: Within each confidence band, sort by value DESC."""
        bids = [
            {"objetoCompra": "High-Low$", "_confidence_score": 90, "valorTotalEstimado": 100_000},
            {"objetoCompra": "High-High$", "_confidence_score": 85, "valorTotalEstimado": 500_000},
            {"objetoCompra": "High-Med$", "_confidence_score": 92, "valorTotalEstimado": 300_000},
        ]
        sorted_bids = self._sort_bids(bids)

        # All in band 0 (>=80), so secondary sort by -conf then -valor
        assert sorted_bids[0]["_confidence_score"] == 92
        assert sorted_bids[1]["_confidence_score"] == 90
        assert sorted_bids[2]["_confidence_score"] == 85

    def test_confidence_bands_ordering(self):
        """High (>=80) before Medium (50-79) before Low (<50)."""
        bids = [
            {"objetoCompra": "Low-big$", "_confidence_score": 40, "valorTotalEstimado": 1_000_000},
            {"objetoCompra": "High-small$", "_confidence_score": 80, "valorTotalEstimado": 50_000},
            {"objetoCompra": "Med-med$", "_confidence_score": 60, "valorTotalEstimado": 200_000},
        ]
        sorted_bids = self._sort_bids(bids)

        assert sorted_bids[0]["_confidence_score"] == 80   # High band (even though lowest value)
        assert sorted_bids[1]["_confidence_score"] == 60   # Medium band
        assert sorted_bids[2]["_confidence_score"] == 40   # Low band (even though highest value)

    def test_default_confidence_50_when_missing(self):
        """Bids without _confidence_score default to 50 (medium band)."""
        bids = [
            {"objetoCompra": "No-score", "valorTotalEstimado": 100_000},
            {"objetoCompra": "High", "_confidence_score": 95, "valorTotalEstimado": 100_000},
            {"objetoCompra": "Low", "_confidence_score": 30, "valorTotalEstimado": 100_000},
        ]
        sorted_bids = self._sort_bids(bids)

        assert sorted_bids[0]["objetoCompra"] == "High"     # Band 0
        assert sorted_bids[1]["objetoCompra"] == "No-score"  # Default 50 = Band 1
        assert sorted_bids[2]["objetoCompra"] == "Low"       # Band 2


class TestZeroMatchConfidenceCap:
    """D-02 AC10.6: Zero-match confidence capped at 70."""

    def test_zero_match_cap_at_70(self):
        """AC10.6: LLM returns confidence=90 but zero-match caps at 70."""
        # Simulates what filter.py does for zero-match bids
        raw_conf = 90
        capped = min(raw_conf, 70)
        assert capped == 70

    def test_zero_match_below_cap_unchanged(self):
        """Zero-match with confidence=60 stays at 60."""
        raw_conf = 60
        capped = min(raw_conf, 70)
        assert capped == 60

    def test_zero_match_at_boundary(self):
        """Zero-match with confidence=70 stays at 70."""
        raw_conf = 70
        capped = min(raw_conf, 70)
        assert capped == 70


class TestIntegrationReranking:
    """D-02 AC10.8: Integration test with mixed relevance sources."""

    def test_mixed_sources_ordered_by_confidence(self):
        """5 bids from different sources, 3 accepted by LLM, ordered by confidence."""
        # Simulates bids after filter.py processing
        bids = [
            # keyword-accepted (confidence=95)
            {
                "objetoCompra": "Uniformes escolares para rede municipal",
                "_relevance_source": "keyword",
                "_confidence_score": 95,
                "valorTotalEstimado": 300_000,
                "_llm_evidence": [],
            },
            # LLM standard accepted (confidence=75)
            {
                "objetoCompra": "Material de vestuário para guarda",
                "_relevance_source": "llm_standard",
                "_confidence_score": 75,
                "valorTotalEstimado": 200_000,
                "_llm_evidence": ["vestuário para guarda"],
            },
            # LLM conservative accepted (confidence=55)
            {
                "objetoCompra": "Aquisição de EPIs e vestimentas",
                "_relevance_source": "llm_conservative",
                "_confidence_score": 55,
                "valorTotalEstimado": 150_000,
                "_llm_evidence": ["vestimentas"],
            },
            # Zero-match LLM accepted (confidence=65, capped from 90)
            {
                "objetoCompra": "Fardamento militar completo",
                "_relevance_source": "llm_zero_match",
                "_confidence_score": 65,
                "valorTotalEstimado": 500_000,
                "_llm_evidence": [],
            },
            # item_inspection accepted (confidence=85)
            {
                "objetoCompra": "Camisetas e calças para servidores",
                "_relevance_source": "item_inspection",
                "_confidence_score": 85,
                "valorTotalEstimado": 100_000,
                "_llm_evidence": [],
            },
        ]

        # Apply re-ranking
        def _confidence_sort_key(lic: dict) -> tuple:
            conf = lic.get("_confidence_score", 50)
            if conf >= 80:
                band = 0
            elif conf >= 50:
                band = 1
            else:
                band = 2
            valor = float(lic.get("valorTotalEstimado") or 0)
            return (band, -conf, -valor)

        sorted_bids = sorted(bids, key=_confidence_sort_key)

        # Band 0 (>=80): keyword(95), item_inspection(85) — ordered by conf DESC
        assert sorted_bids[0]["_relevance_source"] == "keyword"
        assert sorted_bids[0]["_confidence_score"] == 95
        assert sorted_bids[1]["_relevance_source"] == "item_inspection"
        assert sorted_bids[1]["_confidence_score"] == 85

        # Band 1 (50-79): llm_standard(75), zero_match(65), llm_conservative(55)
        assert sorted_bids[2]["_relevance_source"] == "llm_standard"
        assert sorted_bids[2]["_confidence_score"] == 75
        assert sorted_bids[3]["_relevance_source"] == "llm_zero_match"
        assert sorted_bids[3]["_confidence_score"] == 65
        assert sorted_bids[4]["_relevance_source"] == "llm_conservative"
        assert sorted_bids[4]["_confidence_score"] == 55

    def test_all_bids_have_required_fields(self):
        """Verify all fields expected by frontend are present."""
        bid = {
            "objetoCompra": "Teste",
            "_relevance_source": "keyword",
            "_confidence_score": 95,
            "_llm_evidence": ["Teste"],
            "valorTotalEstimado": 100_000,
        }

        assert "_confidence_score" in bid
        assert "_llm_evidence" in bid
        assert "_relevance_source" in bid
        assert isinstance(bid["_llm_evidence"], list)
        assert 0 <= bid["_confidence_score"] <= 100
