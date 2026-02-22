"""CRIT-020: Tests for red flag sector exemptions.

Validates that infrastructure sectors (engenharia, engenharia_rodoviaria,
manutencao_predial, materiais_hidraulicos) are exempt from RED_FLAGS_INFRASTRUCTURE,
and that saude is exempt from RED_FLAGS_MEDICAL, while non-exempt sectors remain
protected.
"""

import pytest
from filter import (
    has_red_flags,
    normalize_text,
    RED_FLAGS_INFRASTRUCTURE,
    RED_FLAGS_MEDICAL,
    RED_FLAGS_ADMINISTRATIVE,
    _INFRA_EXEMPT_SECTORS,
    _MEDICAL_EXEMPT_SECTORS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ALL_RED_FLAG_SETS = [RED_FLAGS_MEDICAL, RED_FLAGS_ADMINISTRATIVE, RED_FLAGS_INFRASTRUCTURE]


def _infra_heavy_text() -> str:
    """Typical engineering bid description with multiple infrastructure terms."""
    return normalize_text(
        "Pavimentacao asfaltica e drenagem pluvial na BR-101 "
        "incluindo terraplanagem e recapeamento"
    )


def _medical_heavy_text() -> str:
    """Typical medical bid description with multiple medical terms."""
    return normalize_text(
        "Aquisicao de medicamento hospitalar para paciente internado "
        "em leito de clinica cirurgica"
    )


def _admin_heavy_text() -> str:
    """Typical administrative bid with administrative terms."""
    return normalize_text(
        "Contratacao de consultoria e assessoria para auditoria "
        "e treinamento de capacitacao"
    )


# ---------------------------------------------------------------------------
# AC4: has_red_flags() receives setor parameter
# ---------------------------------------------------------------------------

class TestHasRedFlagsSetorParam:
    """AC4: has_red_flags() receives setor parameter to decide which sets to apply."""

    def test_setor_param_is_optional(self):
        """setor defaults to None, preserving backward compatibility."""
        flagged, terms = has_red_flags(
            _infra_heavy_text(), ALL_RED_FLAG_SETS
        )
        assert flagged is True
        assert len(terms) >= 2

    def test_setor_none_applies_all_sets(self):
        """When setor is None, all red flag sets are applied."""
        flagged, terms = has_red_flags(
            _infra_heavy_text(), ALL_RED_FLAG_SETS, setor=None
        )
        assert flagged is True


# ---------------------------------------------------------------------------
# AC2 + AC5: Engineering bids with infra terms are NOT rejected
# ---------------------------------------------------------------------------

class TestInfraExemptions:
    """AC2/AC5: Bids with infrastructure terms pass when setor is infrastructure."""

    @pytest.mark.parametrize("setor", sorted(_INFRA_EXEMPT_SECTORS))
    def test_infra_terms_exempt_for_infra_sectors(self, setor: str):
        """Infrastructure red flags are skipped for exempt sectors."""
        flagged, terms = has_red_flags(
            _infra_heavy_text(), ALL_RED_FLAG_SETS, setor=setor
        )
        # Should NOT be flagged for infrastructure terms
        infra_terms = [t for t in terms if t in RED_FLAGS_INFRASTRUCTURE]
        assert len(infra_terms) == 0, (
            f"Sector {setor} should be exempt from infra red flags, "
            f"but matched: {infra_terms}"
        )

    def test_engenharia_typical_bid_passes(self):
        """AC5: Typical engineering bid (pavimentacao + drenagem) passes filter."""
        text = normalize_text(
            "Pavimentacao asfaltica e drenagem pluvial na BR-101"
        )
        flagged, terms = has_red_flags(
            text, ALL_RED_FLAG_SETS, setor="engenharia"
        )
        assert flagged is False
        assert terms == []

    def test_engenharia_rodoviaria_typical_bid_passes(self):
        """Typical road engineering bid passes filter."""
        text = normalize_text(
            "Recapeamento asfaltico e drenagem da rodovia estadual "
            "com terraplanagem e saneamento basico"
        )
        flagged, terms = has_red_flags(
            text, ALL_RED_FLAG_SETS, setor="engenharia_rodoviaria"
        )
        assert flagged is False
        assert terms == []

    def test_manutencao_predial_typical_bid_passes(self):
        """Typical building maintenance bid passes filter."""
        text = normalize_text(
            "Servico de drenagem e saneamento basico predial"
        )
        flagged, terms = has_red_flags(
            text, ALL_RED_FLAG_SETS, setor="manutencao_predial"
        )
        assert flagged is False
        assert terms == []

    def test_materiais_hidraulicos_typical_bid_passes(self):
        """Typical hydraulic materials bid passes filter."""
        text = normalize_text(
            "Aquisicao de materiais para saneamento e esgoto "
            "incluindo bueiro e drenagem"
        )
        flagged, terms = has_red_flags(
            text, ALL_RED_FLAG_SETS, setor="materiais_hidraulicos"
        )
        assert flagged is False
        assert terms == []

    def test_infra_exempt_still_catches_medical_flags(self):
        """Infra-exempt sectors are still checked for medical red flags."""
        flagged, terms = has_red_flags(
            _medical_heavy_text(), ALL_RED_FLAG_SETS, setor="engenharia"
        )
        assert flagged is True
        medical_terms = [t for t in terms if t in RED_FLAGS_MEDICAL]
        assert len(medical_terms) >= 2

    def test_infra_exempt_still_catches_admin_flags(self):
        """Infra-exempt sectors are still checked for administrative red flags."""
        flagged, terms = has_red_flags(
            _admin_heavy_text(), ALL_RED_FLAG_SETS, setor="engenharia"
        )
        assert flagged is True
        admin_terms = [t for t in terms if t in RED_FLAGS_ADMINISTRATIVE]
        assert len(admin_terms) >= 2


# ---------------------------------------------------------------------------
# AC3 + AC6: Vestuario remains protected against false positives
# ---------------------------------------------------------------------------

class TestVestuarioProtection:
    """AC3/AC6: Vestuario sector remains protected from infrastructure terms."""

    def test_vestuario_rejects_infra_terms(self):
        """AC3: Bids with infra terms are REJECTED for vestuario."""
        flagged, terms = has_red_flags(
            _infra_heavy_text(), ALL_RED_FLAG_SETS, setor="vestuario"
        )
        assert flagged is True
        infra_terms = [t for t in terms if t in RED_FLAGS_INFRASTRUCTURE]
        assert len(infra_terms) >= 2

    def test_vestuario_with_infra_in_clothing_context(self):
        """Vestuario bid mentioning infrastructure terms is correctly rejected."""
        text = normalize_text(
            "Aquisicao de uniforme para equipe de pavimentacao "
            "asfaltica e drenagem pluvial"
        )
        flagged, terms = has_red_flags(
            text, ALL_RED_FLAG_SETS, setor="vestuario"
        )
        assert flagged is True

    def test_vestuario_without_flags_passes(self):
        """Vestuario bid without any red flags passes."""
        text = normalize_text(
            "Aquisicao de uniformes escolares e camisetas estampadas"
        )
        flagged, terms = has_red_flags(
            text, ALL_RED_FLAG_SETS, setor="vestuario"
        )
        assert flagged is False


# ---------------------------------------------------------------------------
# Medical exemption for saude
# ---------------------------------------------------------------------------

class TestMedicalExemptions:
    """Saude sector is exempt from medical red flags."""

    def test_saude_exempt_from_medical_flags(self):
        """Medical red flags are skipped for saude sector."""
        flagged, terms = has_red_flags(
            _medical_heavy_text(), ALL_RED_FLAG_SETS, setor="saude"
        )
        medical_terms = [t for t in terms if t in RED_FLAGS_MEDICAL]
        assert len(medical_terms) == 0

    def test_saude_still_catches_infra_flags(self):
        """Saude sector is still checked for infrastructure red flags."""
        flagged, terms = has_red_flags(
            _infra_heavy_text(), ALL_RED_FLAG_SETS, setor="saude"
        )
        assert flagged is True
        infra_terms = [t for t in terms if t in RED_FLAGS_INFRASTRUCTURE]
        assert len(infra_terms) >= 2

    def test_saude_typical_bid_passes(self):
        """Typical saude bid with medical terms passes filter."""
        text = normalize_text(
            "Aquisicao de medicamento para paciente hospitalar "
            "incluindo material cirurgico"
        )
        flagged, terms = has_red_flags(
            text, ALL_RED_FLAG_SETS, setor="saude"
        )
        # Should not be flagged due to medical exemption
        # (admin and infra flags wouldn't match this text)
        assert flagged is False


# ---------------------------------------------------------------------------
# Non-exempt sectors: all red flags applied
# ---------------------------------------------------------------------------

class TestNonExemptSectors:
    """Non-exempt sectors get full red flag treatment."""

    @pytest.mark.parametrize("setor", [
        "informatica", "software", "papelaria", "mobiliario",
        "alimentos", "facilities", "vigilancia", "transporte",
    ])
    def test_non_exempt_sector_catches_infra_flags(self, setor: str):
        """Non-exempt sectors are checked against infrastructure red flags."""
        flagged, terms = has_red_flags(
            _infra_heavy_text(), ALL_RED_FLAG_SETS, setor=setor
        )
        assert flagged is True

    @pytest.mark.parametrize("setor", [
        "informatica", "software", "vestuario", "engenharia",
    ])
    def test_non_exempt_sector_catches_medical_flags(self, setor: str):
        """Non-saude sectors are checked against medical red flags."""
        flagged, terms = has_red_flags(
            _medical_heavy_text(), ALL_RED_FLAG_SETS, setor=setor
        )
        assert flagged is True


# ---------------------------------------------------------------------------
# Threshold behavior preserved
# ---------------------------------------------------------------------------

class TestThresholdBehavior:
    """Red flag threshold (default=2) behavior is preserved with exemptions."""

    def test_single_infra_term_not_flagged_for_vestuario(self):
        """Single infrastructure term below threshold doesn't trigger flag."""
        text = normalize_text("Servico incluindo pavimentacao")
        flagged, terms = has_red_flags(
            text, ALL_RED_FLAG_SETS, setor="vestuario"
        )
        assert flagged is False

    def test_two_infra_terms_flagged_for_vestuario(self):
        """Two infrastructure terms meet threshold for non-exempt sector."""
        text = normalize_text("Servico de pavimentacao e drenagem")
        flagged, terms = has_red_flags(
            text, ALL_RED_FLAG_SETS, setor="vestuario"
        )
        assert flagged is True

    def test_two_infra_terms_not_flagged_for_engenharia(self):
        """Two infrastructure terms don't trigger for exempt sector."""
        text = normalize_text("Servico de pavimentacao e drenagem")
        flagged, terms = has_red_flags(
            text, ALL_RED_FLAG_SETS, setor="engenharia"
        )
        assert flagged is False


# ---------------------------------------------------------------------------
# Exemption sets correctness
# ---------------------------------------------------------------------------

class TestExemptionSets:
    """Verify exemption sets contain the expected sectors."""

    def test_infra_exempt_sectors(self):
        assert _INFRA_EXEMPT_SECTORS == {
            "engenharia", "engenharia_rodoviaria",
            "manutencao_predial", "materiais_hidraulicos",
        }

    def test_medical_exempt_sectors(self):
        assert _MEDICAL_EXEMPT_SECTORS == {"saude"}
