"""Tests for filter_density.py — proximity checks and co-occurrence patterns."""

import pytest
from types import SimpleNamespace
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from filter.density import (
    check_proximity_context,
    check_co_occurrence,
)


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
