"""
Unit tests for term_parser.py - Intelligent keyword parsing with comma/space detection.

Tests cover:
- AC8.1: Comma mode (phrase preservation) vs space mode (legacy behavior)
- Edge cases: empty segments, stopwords, special characters, deduplication
- Cross-industry scenarios
"""

from term_parser import parse_search_terms


class TestCommaMode:
    """Test comma-separated input (phrase mode) - AC8.1 primary behavior."""

    def test_multi_word_phrases_preserved(self):
        """Multi-word phrases in comma mode are kept together."""
        result = parse_search_terms("projeto, levantamento topográfico, terraplenagem")
        assert result == ["projeto", "levantamento topográfico", "terraplenagem"]

    def test_stopwords_preserved_in_multi_word(self):
        """Stopwords are kept when part of multi-word phrases."""
        result = parse_search_terms("estudos de impacto ambiental, drenagem")
        assert result == ["estudos de impacto ambiental", "drenagem"]

    def test_currency_and_numbers_preserved(self):
        """Currency symbols and numbers stay together in comma mode."""
        result = parse_search_terms("item, R$ 50.000")
        assert result == ["item", "r$ 50.000"]

    def test_special_characters_preserved(self):
        """Special characters in terms are kept."""
        result = parse_search_terms("C++, item (A)")
        assert result == ["c++", "item (a)"]

    def test_deduplication_case_insensitive(self):
        """Duplicate terms (different cases) are deduplicated."""
        result = parse_search_terms("projeto, PROJETO, Projeto")
        assert result == ["projeto"]

    def test_stopwords_only_yields_empty(self):
        """Input with only stopwords returns empty list."""
        result = parse_search_terms("de, para, com")
        assert result == []


class TestSpaceMode:
    """Test space-separated input (legacy/fallback mode) - AC8.1 fallback."""

    def test_space_separated_terms(self):
        """Space mode splits by whitespace (no commas present)."""
        result = parse_search_terms("jaleco avental")
        assert result == ["jaleco", "avental"]

    def test_stopwords_removed_in_space_mode(self):
        """Stopwords are removed in space mode."""
        result = parse_search_terms("uniforme de trabalho")
        assert result == ["uniforme", "trabalho"]

    def test_newlines_treated_as_space(self):
        """Newlines are treated as whitespace in space mode."""
        result = parse_search_terms("item1\nitem2")
        assert result == ["item1", "item2"]

    def test_stopwords_only_space_mode(self):
        """Space mode with only stopwords returns empty."""
        result = parse_search_terms("de para com")
        assert result == []


class TestEdgeCases:
    """Test edge cases from AC1.5 - empty segments, special chars, etc."""

    def test_empty_segments_ignored(self):
        """Empty segments from consecutive commas are ignored."""
        # "a" is a stopword, "b" is not
        result = parse_search_terms("a,,b")
        assert result == ["b"]

    def test_leading_trailing_commas(self):
        """Leading/trailing commas are handled gracefully."""
        # "a" is stopword, "b" is not
        result = parse_search_terms(",a,b,")
        assert result == ["b"]

    def test_only_commas(self):
        """Input with only commas returns empty list."""
        result = parse_search_terms(",,,")
        assert result == []

    def test_whitespace_only_segments(self):
        """Whitespace-only segments are ignored."""
        # "a" is stopword, "b" is not
        result = parse_search_terms("a, , b")
        assert result == ["b"]

    def test_smart_quotes_normalized(self):
        """Smart quotes are converted to regular quotes."""
        result = parse_search_terms("\u201citem\u201d")
        # No comma, so space mode, but it's one token with quotes
        assert result == ['"item"']

    def test_empty_string(self):
        """Empty string input returns empty list."""
        result = parse_search_terms("")
        assert result == []

    def test_whitespace_only(self):
        """Whitespace-only input returns empty list."""
        result = parse_search_terms("   ")
        assert result == []


class TestCrossIndustryScenarios:
    """Test parsing for various industry verticals - AC8.4 parsing validation."""

    def test_engineering_6_terms(self):
        """Engineering: Complex multi-word phrases."""
        result = parse_search_terms(
            "projeto, levantamento topográfico, estudos geotécnicos, "
            "terraplenagem, drenagem, pavimentação"
        )
        assert len(result) == 6
        assert "levantamento topográfico" in result
        assert "estudos geotécnicos" in result

    def test_health_4_terms(self):
        """Health: Medical supplies."""
        result = parse_search_terms("gaze, seringa, cateter, soro fisiológico")
        assert len(result) == 4
        assert "soro fisiológico" in result

    def test_it_3_terms(self):
        """IT: Software and systems."""
        result = parse_search_terms("sistema, software, licença")
        assert len(result) == 3

    def test_food_3_terms(self):
        """Food: School meals and catering."""
        result = parse_search_terms(
            "fornecimento de refeição, marmita, alimentação escolar"
        )
        assert len(result) == 3
        assert "fornecimento de refeição" in result
        assert "alimentação escolar" in result

    def test_security_4_terms(self):
        """Security: Surveillance and monitoring."""
        result = parse_search_terms(
            "vigilância, portaria, segurança patrimonial, CFTV"
        )
        assert len(result) == 4
        assert "segurança patrimonial" in result
        assert "cftv" in result  # Lowercase normalization

    def test_cleaning_4_terms(self):
        """Cleaning: Facility maintenance."""
        result = parse_search_terms("limpeza, higienização, desinfecção, conservação")
        assert len(result) == 4


class TestNormalization:
    """Test text normalization applied to all terms."""

    def test_lowercase_conversion(self):
        """All terms are converted to lowercase."""
        result = parse_search_terms("PROJETO, Levantamento TOPOGRÁFICO")
        assert result == ["projeto", "levantamento topográfico"]

    def test_whitespace_trimming(self):
        """Leading/trailing whitespace is trimmed."""
        result = parse_search_terms("  projeto  ,  levantamento  ")
        assert result == ["projeto", "levantamento"]

    def test_accented_characters_preserved(self):
        """Accented characters are preserved (not normalized to ASCII)."""
        result = parse_search_terms("pavimentação, drenagem")
        assert result == ["pavimentação", "drenagem"]


class TestBehaviorConsistency:
    """Ensure consistent behavior across mode switching."""

    def test_single_term_comma_vs_space(self):
        """Single term behaves identically in both modes."""
        comma_result = parse_search_terms("projeto,")
        space_result = parse_search_terms("projeto")
        assert comma_result == space_result == ["projeto"]

    def test_multi_term_difference(self):
        """Multi-word handling differs between modes."""
        # Comma mode: keeps "de trabalho" together
        comma_result = parse_search_terms("uniforme de trabalho")
        # Space mode: splits and removes "de"
        space_result = parse_search_terms("uniforme de trabalho")

        # Wait, both are space mode (no comma). Let me fix this.
        # Comma mode example:
        comma_result = parse_search_terms("item, uniforme de trabalho")
        assert "uniforme de trabalho" in comma_result

        # Space mode (no comma):
        space_result = parse_search_terms("uniforme de trabalho")
        assert space_result == ["uniforme", "trabalho"]
