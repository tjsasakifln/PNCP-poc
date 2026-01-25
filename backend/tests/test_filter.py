"""Unit tests for keyword matching engine (filter.py)."""
import pytest
from filter import (
    normalize_text,
    match_keywords,
    KEYWORDS_UNIFORMES,
    KEYWORDS_EXCLUSAO
)


class TestNormalizeText:
    """Tests for text normalization function."""

    def test_lowercase_conversion(self):
        """Should convert all text to lowercase."""
        assert normalize_text("UNIFORME") == "uniforme"
        assert normalize_text("Jaleco Médico") == "jaleco medico"
        assert normalize_text("MiXeD CaSe") == "mixed case"

    def test_accent_removal(self):
        """Should remove all accents and diacritics."""
        assert normalize_text("jaleco") == "jaleco"
        assert normalize_text("jáleco") == "jaleco"
        assert normalize_text("médico") == "medico"
        assert normalize_text("açúcar") == "acucar"
        assert normalize_text("José") == "jose"
        assert normalize_text("São Paulo") == "sao paulo"

    def test_punctuation_removal(self):
        """Should remove punctuation but preserve word separation."""
        assert normalize_text("uniforme-escolar") == "uniforme escolar"
        assert normalize_text("jaleco!!!") == "jaleco"
        assert normalize_text("kit: uniforme") == "kit uniforme"
        assert normalize_text("R$ 1.500,00") == "r 1 500 00"
        assert normalize_text("teste@exemplo.com") == "teste exemplo com"

    def test_whitespace_normalization(self):
        """Should normalize multiple spaces to single space."""
        assert normalize_text("  múltiplos   espaços  ") == "multiplos espacos"
        assert normalize_text("teste\t\ttab") == "teste tab"
        assert normalize_text("linha\n\nnova") == "linha nova"
        assert normalize_text("   ") == ""

    def test_empty_and_none_inputs(self):
        """Should handle empty strings gracefully."""
        assert normalize_text("") == ""
        assert normalize_text("   ") == ""

    def test_combined_normalization(self):
        """Should apply all normalization steps together."""
        input_text = "  AQUISIÇÃO de UNIFORMES-ESCOLARES (São Paulo)!!!  "
        expected = "aquisicao de uniformes escolares sao paulo"
        assert normalize_text(input_text) == expected

    def test_preserves_word_characters(self):
        """Should preserve alphanumeric characters."""
        assert normalize_text("abc123xyz") == "abc123xyz"
        assert normalize_text("teste2024") == "teste2024"


class TestMatchKeywords:
    """Tests for keyword matching function."""

    def test_simple_match(self):
        """Should match simple uniform keywords."""
        matched, keywords = match_keywords(
            "Aquisição de uniformes escolares",
            KEYWORDS_UNIFORMES
        )
        assert matched is True
        assert "uniformes" in keywords

    def test_no_match(self):
        """Should return False when no keywords match."""
        matched, keywords = match_keywords(
            "Aquisição de software de gestão",
            KEYWORDS_UNIFORMES
        )
        assert matched is False
        assert keywords == []

    def test_case_insensitive_matching(self):
        """Should match regardless of case."""
        matched, _ = match_keywords("JALECO MÉDICO", KEYWORDS_UNIFORMES)
        assert matched is True

        matched, _ = match_keywords("jaleco médico", KEYWORDS_UNIFORMES)
        assert matched is True

        matched, _ = match_keywords("Jaleco Médico", KEYWORDS_UNIFORMES)
        assert matched is True

    def test_accent_insensitive_matching(self):
        """Should match with or without accents."""
        matched, _ = match_keywords("jaleco medico", KEYWORDS_UNIFORMES)
        assert matched is True

        matched, _ = match_keywords("jáleco médico", KEYWORDS_UNIFORMES)
        assert matched is True

    def test_word_boundary_matching(self):
        """Should use word boundaries to prevent partial matches."""
        # "uniforme" should match
        matched, _ = match_keywords("Compra de uniformes", KEYWORDS_UNIFORMES)
        assert matched is True

        # "uniformemente" should NOT match (partial word)
        matched, _ = match_keywords(
            "Distribuição uniformemente espaçada",
            KEYWORDS_UNIFORMES
        )
        assert matched is False

        # "uniformização" should NOT match (partial word)
        matched, _ = match_keywords(
            "Uniformização de processos",
            KEYWORDS_UNIFORMES
        )
        assert matched is False

    def test_exclusion_keywords_prevent_match(self):
        """Should return False if exclusion keywords found."""
        # Has "uniforme" but also has exclusion
        matched, keywords = match_keywords(
            "Uniformização de procedimento padrão",
            KEYWORDS_UNIFORMES,
            KEYWORDS_EXCLUSAO
        )
        assert matched is False
        assert keywords == []

        # Another exclusion case
        matched, keywords = match_keywords(
            "Padrão uniforme de qualidade",
            KEYWORDS_UNIFORMES,
            KEYWORDS_EXCLUSAO
        )
        assert matched is False
        assert keywords == []

    def test_multiple_keyword_matches(self):
        """Should return all matched keywords."""
        matched, keywords = match_keywords(
            "Fornecimento de jaleco e avental para hospital",
            KEYWORDS_UNIFORMES
        )
        assert matched is True
        assert "jaleco" in keywords
        assert "avental" in keywords
        assert len(keywords) >= 2

    def test_compound_keyword_matching(self):
        """Should match multi-word keywords."""
        matched, keywords = match_keywords(
            "Aquisição de uniforme escolar",
            KEYWORDS_UNIFORMES
        )
        assert matched is True
        assert "uniforme escolar" in keywords or "uniforme" in keywords

    def test_punctuation_does_not_prevent_match(self):
        """Should match even with punctuation."""
        matched, _ = match_keywords("uniforme-escolar", KEYWORDS_UNIFORMES)
        assert matched is True

        matched, _ = match_keywords("jaleco!!!", KEYWORDS_UNIFORMES)
        assert matched is True

        matched, _ = match_keywords("kit: uniformes", KEYWORDS_UNIFORMES)
        assert matched is True

    def test_empty_objeto_returns_no_match(self):
        """Should handle empty object description."""
        matched, keywords = match_keywords("", KEYWORDS_UNIFORMES)
        assert matched is False
        assert keywords == []

    def test_exclusions_none_parameter(self):
        """Should work correctly when exclusions=None."""
        matched, keywords = match_keywords(
            "Compra de uniformes",
            KEYWORDS_UNIFORMES,
            exclusions=None
        )
        assert matched is True
        assert len(keywords) > 0

    def test_real_world_procurement_examples(self):
        """Should correctly match real-world procurement descriptions."""
        # Valid uniform procurement
        test_cases_valid = [
            "Aquisição de uniformes escolares para alunos da rede municipal",
            "Fornecimento de jalecos para profissionais de saúde",
            "Confecção de fardamento militar",
            "Kit uniforme completo (camisa, calça, boné)",
            "PREGÃO ELETRÔNICO - Aquisição de uniformes",
        ]

        for caso in test_cases_valid:
            matched, _ = match_keywords(caso, KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO)
            assert matched is True, f"Should match: {caso}"

        # Invalid (non-uniform procurement)
        test_cases_invalid = [
            "Aquisição de notebooks e impressoras",
            "Serviços de limpeza e conservação",
            "Uniformização de procedimento administrativo",
            "Software de gestão uniformemente distribuído",
        ]

        for caso in test_cases_invalid:
            matched, _ = match_keywords(caso, KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO)
            assert matched is False, f"Should NOT match: {caso}"


class TestKeywordConstants:
    """Tests for keyword constant definitions."""

    def test_keywords_uniformes_has_minimum_terms(self):
        """Should have at least 50 keywords."""
        assert len(KEYWORDS_UNIFORMES) >= 50

    def test_keywords_exclusao_has_minimum_terms(self):
        """Should have at least 4 exclusion keywords."""
        assert len(KEYWORDS_EXCLUSAO) >= 4

    def test_keywords_are_lowercase(self):
        """All keywords should be lowercase for consistency."""
        for kw in KEYWORDS_UNIFORMES:
            assert kw == kw.lower(), f"Keyword '{kw}' should be lowercase"

        for kw in KEYWORDS_EXCLUSAO:
            assert kw == kw.lower(), f"Exclusion '{kw}' should be lowercase"

    def test_no_duplicate_keywords(self):
        """Should not have duplicate keywords (set enforces this)."""
        # Sets automatically prevent duplicates, but verify type
        assert isinstance(KEYWORDS_UNIFORMES, set)
        assert isinstance(KEYWORDS_EXCLUSAO, set)

    def test_keywords_contain_expected_terms(self):
        """Should contain key expected terms from PRD."""
        expected_primary = {"uniforme", "uniformes", "fardamento", "jaleco"}
        assert expected_primary.issubset(KEYWORDS_UNIFORMES)

        expected_exclusions = {"uniformização de procedimento", "padrão uniforme"}
        assert expected_exclusions.issubset(KEYWORDS_EXCLUSAO)
