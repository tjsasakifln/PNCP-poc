"""Tests for filter_keywords.py — text normalization, keyword matching, red flags.

Wave 0 Safety Net: Covers normalize_text, validate_terms, remove_stopwords,
match_keywords, has_red_flags, has_sector_red_flags.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from filter_keywords import (
    normalize_text,
    validate_terms,
    remove_stopwords,
    match_keywords,
    has_red_flags,
    KEYWORDS_UNIFORMES,
    KEYWORDS_EXCLUSAO,
    STOPWORDS_PT,
    RED_FLAGS_MEDICAL,
    RED_FLAGS_ADMINISTRATIVE,
    RED_FLAGS_INFRASTRUCTURE,
)


# ──────────────────────────────────────────────────────────────────────
# normalize_text
# ──────────────────────────────────────────────────────────────────────

class TestNormalizeText:
    """Tests for text normalization."""

    @pytest.mark.timeout(30)
    def test_lowercase(self):
        assert normalize_text("HELLO WORLD") == "hello world"

    @pytest.mark.timeout(30)
    def test_accent_removal(self):
        result = normalize_text("aquisicao")
        assert result == "aquisicao"

    @pytest.mark.timeout(30)
    def test_accent_chars(self):
        result = normalize_text("acao")
        assert "a" in result

    @pytest.mark.timeout(30)
    def test_empty_string(self):
        assert normalize_text("") == ""

    @pytest.mark.timeout(30)
    def test_special_characters_preserved(self):
        result = normalize_text("guarda-po")
        assert "-" in result or "guarda" in result

    @pytest.mark.timeout(30)
    def test_numbers_preserved(self):
        result = normalize_text("item 123")
        assert "123" in result


# ──────────────────────────────────────────────────────────────────────
# validate_terms
# ──────────────────────────────────────────────────────────────────────

class TestValidateTerms:
    """Tests for search term validation."""

    @pytest.mark.timeout(30)
    def test_valid_term(self):
        result = validate_terms(["uniforme escolar"])
        assert "uniforme escolar" in result["valid"]
        assert len(result["ignored"]) == 0

    @pytest.mark.timeout(30)
    def test_stopword_rejected(self):
        result = validate_terms(["de"])
        assert len(result["valid"]) == 0
        assert "de" in result["ignored"]
        assert "stopword" in result["reasons"]["de"].lower()

    @pytest.mark.timeout(30)
    def test_short_term_rejected(self):
        result = validate_terms(["abc"])
        assert len(result["valid"]) == 0
        assert "abc" in result["ignored"]

    @pytest.mark.timeout(30)
    def test_empty_term_rejected(self):
        result = validate_terms(["   "])
        assert len(result["valid"]) == 0
        assert len(result["ignored"]) == 1

    @pytest.mark.timeout(30)
    def test_multi_word_phrase_accepted(self):
        result = validate_terms(["uniforme escolar"])
        assert "uniforme escolar" in result["valid"]

    @pytest.mark.timeout(30)
    def test_special_chars_rejected(self):
        result = validate_terms(["test@#$"])
        assert len(result["valid"]) == 0
        assert len(result["ignored"]) == 1

    @pytest.mark.timeout(30)
    def test_mixed_valid_and_invalid(self):
        result = validate_terms(["uniforme escolar", "de", "abc", "jaleco"])
        assert len(result["valid"]) == 2
        assert len(result["ignored"]) == 2

    @pytest.mark.timeout(30)
    def test_no_intersection_invariant(self):
        """Valid and ignored must never overlap."""
        result = validate_terms(["uniforme", "de", "jaleco", "a", "colete"])
        valid_set = {t.strip().lower() for t in result["valid"]}
        ignored_set = {t.strip().lower() for t in result["ignored"]}
        assert valid_set.isdisjoint(ignored_set)

    @pytest.mark.timeout(30)
    def test_whitespace_trimmed(self):
        result = validate_terms(["  jaleco  "])
        assert "jaleco" in result["valid"]


# ──────────────────────────────────────────────────────────────────────
# remove_stopwords
# ──────────────────────────────────────────────────────────────────────

class TestRemoveStopwords:
    """Tests for deprecated stopword removal."""

    @pytest.mark.timeout(30)
    def test_removes_stopwords(self):
        result = remove_stopwords(["de", "uniforme", "para"])
        assert "uniforme" in result
        assert "de" not in result
        assert "para" not in result

    @pytest.mark.timeout(30)
    def test_all_stopwords_returns_empty(self):
        result = remove_stopwords(["de", "do", "da"])
        assert result == []

    @pytest.mark.timeout(30)
    def test_no_stopwords(self):
        result = remove_stopwords(["uniforme", "escolar"])
        assert len(result) == 2


# ──────────────────────────────────────────────────────────────────────
# match_keywords
# ──────────────────────────────────────────────────────────────────────

class TestMatchKeywords:
    """Tests for keyword matching in bid text."""

    @pytest.mark.timeout(30)
    def test_match_uniform(self):
        match, terms = match_keywords(
            "Aquisicao de uniformes escolares para a prefeitura",
            KEYWORDS_UNIFORMES,
            KEYWORDS_EXCLUSAO,
        )
        assert match is True
        assert len(terms) > 0

    @pytest.mark.timeout(30)
    def test_no_match(self):
        match, terms = match_keywords(
            "Aquisicao de computadores e monitores",
            KEYWORDS_UNIFORMES,
            KEYWORDS_EXCLUSAO,
        )
        assert match is False

    @pytest.mark.timeout(30)
    def test_exclusion_overrides_match(self):
        """Exclusion keywords should prevent a match."""
        match, terms = match_keywords(
            "confeccao de placas de sinalizacao",
            {"confeccao"},
            {"placa", "sinalizacao"},
        )
        assert match is False

    @pytest.mark.timeout(30)
    def test_custom_keywords(self):
        match, terms = match_keywords(
            "Aquisicao de software para gestao",
            {"software", "gestao"},
            set(),
        )
        assert match is True

    @pytest.mark.timeout(30)
    def test_empty_text(self):
        match, terms = match_keywords("", KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO)
        assert match is False


# ──────────────────────────────────────────────────────────────────────
# has_red_flags
# ──────────────────────────────────────────────────────────────────────

class TestHasRedFlags:
    """Tests for red flag detection."""

    @pytest.mark.timeout(30)
    def test_no_flags(self):
        flagged, terms = has_red_flags(
            "uniformes escolares simples",
            [RED_FLAGS_MEDICAL, RED_FLAGS_ADMINISTRATIVE],
        )
        assert flagged is False

    @pytest.mark.timeout(30)
    def test_empty_text(self):
        flagged, terms = has_red_flags(
            "",
            [RED_FLAGS_MEDICAL],
        )
        assert flagged is False

    @pytest.mark.timeout(30)
    def test_empty_flag_sets(self):
        flagged, terms = has_red_flags("some text", [])
        assert flagged is False
