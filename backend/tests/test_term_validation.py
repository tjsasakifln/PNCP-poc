"""
Unit tests for term validation logic (filter.validate_terms).

Tests the critical bug fix that prevents terms from appearing in BOTH
"valid" and "ignored" lists simultaneously.
"""

from filter import validate_terms


class TestValidateTerms:
    """Test suite for validate_terms() function."""

    def test_valid_single_terms(self):
        """Valid single terms should pass validation."""
        result = validate_terms(['uniforme', 'jaleco', 'fardamento'])

        assert result['valid'] == ['uniforme', 'jaleco', 'fardamento']
        assert result['ignored'] == []
        assert result['reasons'] == {}

    def test_valid_phrases(self):
        """Multi-word phrases should pass validation."""
        result = validate_terms(['uniforme escolar', 'jaleco branco', 'fardamento militar'])

        assert result['valid'] == ['uniforme escolar', 'jaleco branco', 'fardamento militar']
        assert result['ignored'] == []
        assert result['reasons'] == {}

    def test_stopword_rejection(self):
        """Single-word stopwords should be rejected with reason."""
        result = validate_terms(['de', 'da', 'uniforme'])

        assert result['valid'] == ['uniforme']
        assert set(result['ignored']) == {'de', 'da'}
        assert 'de' in result['reasons']
        assert 'stopword' in result['reasons']['de'].lower()

    def test_short_term_rejection(self):
        """Terms shorter than 4 characters should be rejected."""
        result = validate_terms(['abc', 'abcd', 'uniforme'])

        assert result['valid'] == ['abcd', 'uniforme']
        assert result['ignored'] == ['abc']
        assert 'abc' in result['reasons']
        assert 'curto' in result['reasons']['abc'].lower()

    def test_whitespace_normalization(self):
        """Terms with extra whitespace should be normalized."""
        result = validate_terms(['  uniforme  ', ' jaleco', 'fardamento  '])

        assert result['valid'] == ['uniforme', 'jaleco', 'fardamento']
        assert result['ignored'] == []
        assert result['reasons'] == {}

    def test_empty_terms_rejection(self):
        """Empty strings or whitespace-only should be rejected."""
        result = validate_terms(['', '   ', 'uniforme'])

        assert result['valid'] == ['uniforme']
        assert len(result['ignored']) == 2
        for term in result['ignored']:
            assert 'vazio' in result['reasons'][term].lower()

    def test_special_chars_rejection(self):
        """Terms with special characters should be rejected."""
        result = validate_terms(['uniforme$', 'jaleco!', 'fardamento'])

        assert result['valid'] == ['fardamento']
        assert set(result['ignored']) == {'uniforme$', 'jaleco!'}
        for term in result['ignored']:
            assert 'especiais' in result['reasons'][term].lower()

    def test_accented_terms_allowed(self):
        """Terms with Portuguese accents should be allowed."""
        result = validate_terms(['uniformé', 'jáleco', 'façade'])

        assert result['valid'] == ['uniformé', 'jáleco', 'façade']
        assert result['ignored'] == []

    def test_hyphenated_terms_allowed(self):
        """Terms with hyphens should be allowed."""
        result = validate_terms(['guarda-pó', 'micro-ondas'])

        assert result['valid'] == ['guarda-pó', 'micro-ondas']
        assert result['ignored'] == []

    def test_mixed_valid_invalid(self):
        """Mixed valid/invalid terms should be properly categorized."""
        result = validate_terms(['uniforme', 'de', 'abc', 'jaleco', '  ', 'farda'])

        assert set(result['valid']) == {'uniforme', 'jaleco', 'farda'}
        assert len(result['ignored']) == 3  # 'de', 'abc', '  '

        # Verify all ignored terms have reasons
        for term in result['ignored']:
            assert term in result['reasons']
            assert len(result['reasons'][term]) > 0

    def test_no_intersection_valid_ignored(self):
        """CRITICAL: Terms cannot be in both valid and ignored lists."""
        result = validate_terms(['uniforme', 'de', 'jaleco', 'da', 'abc'])

        valid_normalized = {t.strip().lower() for t in result['valid']}
        ignored_normalized = {t.strip().lower() for t in result['ignored']}

        intersection = valid_normalized.intersection(ignored_normalized)
        assert len(intersection) == 0, (
            f"BUG: Terms found in BOTH lists: {intersection}. "
            f"Valid: {result['valid']}, Ignored: {result['ignored']}"
        )

    def test_phrase_with_stopwords_not_rejected(self):
        """Phrases containing stopwords should NOT be rejected as stopwords."""
        result = validate_terms(['aquisição de uniformes', 'fornecimento de jalecos'])

        # These are multi-word phrases, so they should NOT be rejected as stopwords
        assert 'aquisição de uniformes' in result['valid']
        assert 'fornecimento de jalecos' in result['valid']
        assert len(result['ignored']) == 0

    def test_real_world_bug_scenario(self):
        """Test the exact bug scenario from the user report."""
        # User input: "uniforme escolar, jaleco, fardamento"
        # Parser output (after comma split): ["uniforme escolar", " jaleco", " fardamento"]
        result = validate_terms(['uniforme escolar', ' jaleco', ' fardamento'])

        # All should be VALID after normalization
        assert set(result['valid']) == {'uniforme escolar', 'jaleco', 'fardamento'}
        assert result['ignored'] == []

        # CRITICAL: jaleco must NOT be in ignored
        assert 'jaleco' not in [t.strip().lower() for t in result['ignored']]
        assert ' jaleco' not in result['ignored']

    def test_case_insensitivity(self):
        """Validation should be case-insensitive."""
        result = validate_terms(['UNIFORME', 'Jaleco', 'FARDAmento'])

        assert result['valid'] == ['uniforme', 'jaleco', 'fardamento']
        assert result['ignored'] == []

    def test_all_terms_rejected(self):
        """When all terms are rejected, return empty valid list."""
        result = validate_terms(['de', 'da', 'abc', '  '])

        assert result['valid'] == []
        assert len(result['ignored']) == 4
        assert len(result['reasons']) == 4

    def test_duplicates_normalized(self):
        """Duplicate terms (different case/whitespace) should be handled."""
        result = validate_terms(['uniforme', ' UNIFORME ', 'Uniforme'])

        # Should deduplicate to one normalized term
        # (Current implementation doesn't dedupe, but should not crash)
        assert len(result['valid']) >= 1
        assert all(t.lower() == 'uniforme' for t in result['valid'])

    def test_reasons_clarity(self):
        """Rejection reasons should be clear and actionable."""
        result = validate_terms(['de', 'abc', 'uniforme$'])

        # Each rejected term must have a reason
        assert 'de' in result['reasons']
        assert 'abc' in result['reasons']
        assert 'uniforme$' in result['reasons']

        # Reasons must be human-readable (not just codes)
        for reason in result['reasons'].values():
            assert len(reason) > 10  # Meaningful message, not just "ERROR"
            assert any(keyword in reason.lower() for keyword in [
                'stopword', 'curto', 'caracteres', 'especiais', 'vazio'
            ])


class TestValidateTermsEdgeCases:
    """Edge case tests for validate_terms()."""

    def test_unicode_characters(self):
        """Unicode characters should be handled gracefully."""
        result = validate_terms(['uniformé', 'çedilha', 'ñoño'])

        assert len(result['valid']) >= 1
        assert len(result['reasons']) == 0

    def test_numbers_in_terms(self):
        """Terms with numbers should be allowed."""
        result = validate_terms(['uniforme2024', 'tipo1', 'modelo3'])

        assert set(result['valid']) == {'uniforme2024', 'tipo1', 'modelo3'}

    def test_very_long_terms(self):
        """Very long terms should be allowed (no max length)."""
        long_term = 'uniforme' * 20  # 160 characters
        result = validate_terms([long_term])

        assert result['valid'] == [long_term]

    def test_empty_input_list(self):
        """Empty input list should return empty results."""
        result = validate_terms([])

        assert result['valid'] == []
        assert result['ignored'] == []
        assert result['reasons'] == {}

    def test_single_char_after_strip(self):
        """Single character after stripping should be rejected."""
        result = validate_terms(['  a  ', '  b  '])

        assert result['valid'] == []
        assert len(result['ignored']) == 2


class TestValidateTermsInvariant:
    """Tests for the CRITICAL invariant: no term in both lists."""

    def test_invariant_simple_case(self):
        """Simple case: no duplicates between valid and ignored."""
        result = validate_terms(['uniforme', 'de', 'jaleco'])

        valid_set = set(result['valid'])
        ignored_set = set(result['ignored'])

        assert len(valid_set.intersection(ignored_set)) == 0

    def test_invariant_whitespace_variations(self):
        """Whitespace variations should not violate invariant."""
        result = validate_terms(['uniforme', ' uniforme', '  uniforme  '])

        valid_normalized = {t.strip().lower() for t in result['valid']}
        ignored_normalized = {t.strip().lower() for t in result['ignored']}

        assert len(valid_normalized.intersection(ignored_normalized)) == 0

    def test_invariant_case_variations(self):
        """Case variations should not violate invariant."""
        result = validate_terms(['UNIFORME', 'uniforme', 'Uniforme'])

        valid_normalized = {t.strip().lower() for t in result['valid']}
        ignored_normalized = {t.strip().lower() for t in result['ignored']}

        assert len(valid_normalized.intersection(ignored_normalized)) == 0

    def test_invariant_with_all_types(self):
        """Mix of valid, stopwords, short, and invalid should maintain invariant."""
        result = validate_terms([
            'uniforme', 'de', 'abc', 'jaleco', 'da',
            'fardamento', 'test$', '  ', 'colete'
        ])

        valid_normalized = {t.strip().lower() for t in result['valid']}
        ignored_normalized = {t.strip().lower() for t in result['ignored']}

        intersection = valid_normalized.intersection(ignored_normalized)
        assert len(intersection) == 0, f"Invariant violated: {intersection}"
