"""Tests for filter_density.py — sector context analysis and proximity checks.

Wave 0 Safety Net: Covers analisar_contexto_setor, obter_setor_dominante,
check_proximity_context, check_co_occurrence.
"""

import pytest
from types import SimpleNamespace
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from filter_density import (
    analisar_contexto_setor,
    obter_setor_dominante,
    check_proximity_context,
    check_co_occurrence,
    SETOR_VOCABULARIOS,
)


# ──────────────────────────────────────────────────────────────────────
# analisar_contexto_setor
# ──────────────────────────────────────────────────────────────────────

class TestAnalisarContextoSetor:
    """Tests for sector relevance scoring."""

    @pytest.mark.timeout(30)
    def test_empty_terms(self):
        result = analisar_contexto_setor([])
        assert result == {}

    @pytest.mark.timeout(30)
    def test_rodoviario_terms(self):
        result = analisar_contexto_setor(["pavimentacao", "asfalto", "rodovia"])
        assert "rodoviario" in result or "rodoviário" in result
        # At least one sector should score > 0
        max_score = max(result.values()) if result else 0
        assert max_score > 0

    @pytest.mark.timeout(30)
    def test_tecnologia_terms(self):
        result = analisar_contexto_setor(["software", "hardware"])
        assert "tecnologia" in result
        assert result["tecnologia"] > 0

    @pytest.mark.timeout(30)
    def test_no_match(self):
        result = analisar_contexto_setor(["xyzabc123"])
        assert all(v == 0.0 for v in result.values())

    @pytest.mark.timeout(30)
    def test_single_term(self):
        result = analisar_contexto_setor(["esgoto"])
        assert "saneamento" in result
        assert result["saneamento"] > 0

    @pytest.mark.timeout(30)
    def test_returns_all_sectors(self):
        result = analisar_contexto_setor(["teste"])
        assert len(result) == len(SETOR_VOCABULARIOS)


# ──────────────────────────────────────────────────────────────────────
# obter_setor_dominante
# ──────────────────────────────────────────────────────────────────────

class TestObterSetorDominante:
    """Tests for dominant sector detection."""

    @pytest.mark.timeout(30)
    def test_clear_dominant(self):
        result = obter_setor_dominante(["software", "hardware", "computador"])
        assert result == "tecnologia"

    @pytest.mark.timeout(30)
    def test_no_dominant_generic_terms(self):
        result = obter_setor_dominante(["algo generico"])
        assert result is None

    @pytest.mark.timeout(30)
    def test_empty_terms(self):
        result = obter_setor_dominante([])
        assert result is None

    @pytest.mark.timeout(30)
    def test_custom_threshold(self):
        result = obter_setor_dominante(["esgoto"], threshold=0.9)
        # Single term out of 1 = 100% match, so should pass even high threshold
        assert result == "saneamento"

    @pytest.mark.timeout(30)
    def test_threshold_too_high(self):
        result = obter_setor_dominante(["esgoto", "random", "other"], threshold=0.9)
        assert result is None


# ──────────────────────────────────────────────────────────────────────
# check_proximity_context
# ──────────────────────────────────────────────────────────────────────

class TestCheckProximityContext:
    """Tests for proximity context filtering."""

    @pytest.mark.timeout(30)
    def test_no_proximity_issue(self):
        should_reject, reason = check_proximity_context(
            "Aquisicao de uniformes para a escola municipal",
            ["uniformes"],
            "vestuario",
            {"alimentos": {"merenda", "alimentacao"}},
        )
        assert should_reject is False
        assert reason is None

    @pytest.mark.timeout(30)
    def test_proximity_rejection(self):
        should_reject, reason = check_proximity_context(
            "confeccao de merenda escolar uniforme padrao",
            ["confeccao"],
            "vestuario",
            {"alimentos": {"merenda"}},
            window_size=10,
        )
        assert should_reject is True
        assert "alimentos" in reason

    @pytest.mark.timeout(30)
    def test_empty_text(self):
        should_reject, reason = check_proximity_context(
            "", ["keyword"], "sector", {"other": {"sig"}}
        )
        assert should_reject is False

    @pytest.mark.timeout(30)
    def test_empty_matched_terms(self):
        should_reject, reason = check_proximity_context(
            "some text", [], "sector", {"other": {"sig"}}
        )
        assert should_reject is False

    @pytest.mark.timeout(30)
    def test_zero_window_size(self):
        should_reject, reason = check_proximity_context(
            "some text", ["some"], "sector", {"other": {"text"}}, window_size=0
        )
        assert should_reject is False

    @pytest.mark.timeout(30)
    def test_no_other_sectors(self):
        should_reject, reason = check_proximity_context(
            "uniformes escolares", ["uniformes"], "vestuario", {}
        )
        assert should_reject is False


# ──────────────────────────────────────────────────────────────────────
# check_co_occurrence
# ──────────────────────────────────────────────────────────────────────

class TestCheckCoOccurrence:
    """Tests for co-occurrence pattern detection."""

    @pytest.mark.timeout(30)
    def test_no_rules(self):
        should_reject, reason = check_co_occurrence("text", [], "sector")
        assert should_reject is False

    @pytest.mark.timeout(30)
    def test_empty_text(self):
        rule = SimpleNamespace(
            trigger="confeccao",
            negative_contexts=["placa"],
            positive_signals=["uniforme"],
        )
        should_reject, reason = check_co_occurrence("", [rule], "sector")
        assert should_reject is False

    @pytest.mark.timeout(30)
    def test_trigger_and_negative_no_positive_rejects(self):
        rule = SimpleNamespace(
            trigger="confeccao",
            negative_contexts=["placa"],
            positive_signals=["uniforme"],
        )
        should_reject, reason = check_co_occurrence(
            "confeccao de placas de sinalizacao", [rule], "vestuario"
        )
        assert should_reject is True
        assert "confeccao" in reason
        assert "placa" in reason

    @pytest.mark.timeout(30)
    def test_trigger_and_negative_with_positive_passes(self):
        rule = SimpleNamespace(
            trigger="confeccao",
            negative_contexts=["placa"],
            positive_signals=["uniforme"],
        )
        should_reject, reason = check_co_occurrence(
            "confeccao de placas e uniformes escolares", [rule], "vestuario"
        )
        assert should_reject is False

    @pytest.mark.timeout(30)
    def test_no_trigger_match(self):
        rule = SimpleNamespace(
            trigger="confeccao",
            negative_contexts=["placa"],
            positive_signals=["uniforme"],
        )
        should_reject, reason = check_co_occurrence(
            "aquisicao de placas de sinalizacao", [rule], "vestuario"
        )
        assert should_reject is False

    @pytest.mark.timeout(30)
    def test_trigger_no_negative_passes(self):
        rule = SimpleNamespace(
            trigger="confeccao",
            negative_contexts=["placa"],
            positive_signals=["uniforme"],
        )
        should_reject, reason = check_co_occurrence(
            "confeccao de uniformes escolares", [rule], "vestuario"
        )
        assert should_reject is False
