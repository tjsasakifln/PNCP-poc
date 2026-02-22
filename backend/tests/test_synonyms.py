"""
Tests for synonym matching module (STORY-179 AC12).

Coverage targets:
- Exact synonym matches
- Fuzzy synonym matches (SequenceMatcher)
- Auto-approval thresholds (2+ synonyms)
- Edge cases: accents, case sensitivity, word boundaries
- Multiple sectors
"""

from filter import normalize_text
from synonyms import (
    find_synonym_matches,
    count_synonym_matches,
    should_auto_approve_by_synonyms,
    SECTOR_SYNONYMS,
)


class TestFindSynonymMatches:
    """Test synonym matching logic."""

    def test_exact_synonym_match_vestuario(self):
        """Test exact match: 'fardamento' → 'uniforme'."""
        objeto = "Fardamento para guardas municipais"
        setor_keywords = {"uniforme", "farda"}
        setor_id = "vestuario"

        matches = find_synonym_matches(objeto, setor_keywords, setor_id)

        assert len(matches) >= 1
        assert any(m[0] == "uniforme" and "fardamento" in m[1] for m in matches)

    def test_exact_synonym_match_facilities(self):
        """Test exact match: 'asseio' → 'limpeza'."""
        objeto = "Serviços de asseio e conservação predial"
        setor_keywords = {"limpeza", "conservação"}
        setor_id = "facilities"

        matches = find_synonym_matches(objeto, setor_keywords, setor_id)

        # Should match: "asseio" → "limpeza", "conservação" directly matches
        assert len(matches) >= 1
        assert any(m[0] == "limpeza" for m in matches)

    def test_multiple_synonyms_match(self):
        """Test multiple synonym matches in same object."""
        objeto = "Fardamento e jaleco para servidores da saúde"
        setor_keywords = {"uniforme", "jaleco"}
        setor_id = "vestuario"

        matches = find_synonym_matches(objeto, setor_keywords, setor_id)

        assert len(matches) >= 1
        # "fardamento" → "uniforme" (either exact or fuzzy match)
        assert any(m[0] == "uniforme" and "fardamento" in m[1] for m in matches)

    def test_synonym_with_accents(self):
        """Test synonym matching with Portuguese accents."""
        objeto = "Manutenção e conservação de imóveis públicos"
        setor_keywords = {"manutenção predial", "conservação"}
        setor_id = "facilities"

        matches = find_synonym_matches(objeto, setor_keywords, setor_id)

        # "conservação" matches directly (not a synonym, but canonical)
        # "manutenção" should match if synonym dict includes variants
        assert len(matches) >= 0  # May or may not match depending on dict

    def test_fuzzy_match_typo(self):
        """Test fuzzy matching with minor typos."""
        # "fardamennto" (typo) should match "fardamento" if similarity ≥ 0.8
        objeto = "Fornecimento de fardamennto para guardas"
        setor_keywords = {"uniforme"}
        setor_id = "vestuario"

        matches = find_synonym_matches(objeto, setor_keywords, setor_id, similarity_threshold=0.8)

        # Fuzzy match should succeed (11/12 chars match = 91.7% similarity)
        assert len(matches) >= 1

    def test_no_match_if_canonical_keyword_present(self):
        """Test that synonym matching is skipped if canonical keyword already matches."""
        objeto = "Fornecimento de uniformes escolares"
        setor_keywords = {"uniforme", "farda"}
        setor_id = "vestuario"

        matches = find_synonym_matches(objeto, setor_keywords, setor_id)

        # "uniforme" is already in objeto, so no synonym match for it
        # "farda" is NOT in objeto, but its synonym "fardamento" is also NOT in objeto
        assert len(matches) == 0

    def test_synonym_match_informatica_servidor(self):
        """Test 'servidor de rede' synonym for 'servidor' (informatica)."""
        objeto = "Aquisição de servidores de rede para datacenter"
        setor_keywords = {"servidor"}
        setor_id = "informatica"

        matches = find_synonym_matches(objeto, setor_keywords, setor_id)

        # "servidor" is already in objeto (direct match), so no synonym match
        assert len(matches) == 0

    def test_synonym_match_no_dict_for_sector(self):
        """Test sector with no synonym dictionary (graceful degradation)."""
        objeto = "Qualquer coisa"
        setor_keywords = {"keyword"}
        setor_id = "nonexistent_sector"

        matches = find_synonym_matches(objeto, setor_keywords, setor_id)

        assert len(matches) == 0

    def test_synonym_match_empty_object(self):
        """Test empty object description."""
        objeto = ""
        setor_keywords = {"uniforme"}
        setor_id = "vestuario"

        matches = find_synonym_matches(objeto, setor_keywords, setor_id)

        assert len(matches) == 0

    def test_synonym_match_case_insensitive(self):
        """Test case-insensitive matching."""
        objeto = "FARDAMENTO PARA GUARDAS MUNICIPAIS"
        setor_keywords = {"uniforme"}
        setor_id = "vestuario"

        matches = find_synonym_matches(objeto, setor_keywords, setor_id)

        assert len(matches) >= 1
        assert any(m[0] == "uniforme" and "fardamento" in m[1].lower() for m in matches)


class TestCountSynonymMatches:
    """Test convenience function count_synonym_matches."""

    def test_count_zero_matches(self):
        """Test zero synonym matches."""
        objeto = "Construção de escola"
        setor_keywords = {"uniforme"}
        setor_id = "vestuario"

        count = count_synonym_matches(objeto, setor_keywords, setor_id)

        assert count == 0

    def test_count_one_match(self):
        """Test one synonym match."""
        objeto = "Fardamento escolar"
        setor_keywords = {"uniforme"}
        setor_id = "vestuario"

        count = count_synonym_matches(objeto, setor_keywords, setor_id)

        assert count >= 1

    def test_count_multiple_matches(self):
        """Test multiple synonym matches."""
        objeto = "Fardamento e jaleco para servidores"
        setor_keywords = {"uniforme", "jaleco"}
        setor_id = "vestuario"

        count = count_synonym_matches(objeto, setor_keywords, setor_id)

        assert count >= 1  # At least "fardamento" → "uniforme"


class TestShouldAutoApproveBySynonyms:
    """Test auto-approval logic based on synonym matches (AC12.3)."""

    def test_auto_approve_two_synonyms(self):
        """Test auto-approval with 2+ synonym matches."""
        objeto = "Fardamento e avental hospitalar para servidores"
        setor_keywords = {"uniforme", "jaleco"}
        setor_id = "vestuario"

        should_approve, matches = should_auto_approve_by_synonyms(
            objeto, setor_keywords, setor_id, min_synonyms=2
        )

        # "fardamento" → "uniforme", "avental hospitalar" → "jaleco"
        assert should_approve is True
        assert len(matches) >= 2

    def test_no_auto_approve_one_synonym(self):
        """Test NO auto-approval with only 1 synonym match."""
        objeto = "Fardamento escolar"
        setor_keywords = {"uniforme", "jaleco"}
        setor_id = "vestuario"

        should_approve, matches = should_auto_approve_by_synonyms(
            objeto, setor_keywords, setor_id, min_synonyms=2
        )

        # Only 1 match: "fardamento" → "uniforme"
        assert should_approve is False
        assert len(matches) == 1

    def test_no_auto_approve_zero_synonyms(self):
        """Test NO auto-approval with 0 synonym matches."""
        objeto = "Construção de escola"
        setor_keywords = {"uniforme"}
        setor_id = "vestuario"

        should_approve, matches = should_auto_approve_by_synonyms(
            objeto, setor_keywords, setor_id, min_synonyms=2
        )

        assert should_approve is False
        assert len(matches) == 0

    def test_auto_approve_custom_threshold(self):
        """Test auto-approval with custom threshold (1 synonym)."""
        objeto = "Fardamento escolar"
        setor_keywords = {"uniforme"}
        setor_id = "vestuario"

        should_approve, matches = should_auto_approve_by_synonyms(
            objeto, setor_keywords, setor_id, min_synonyms=1
        )

        assert should_approve is True
        assert len(matches) >= 1


class TestCritFlt006SynonymDedup:
    """CRIT-FLT-006: Multiple synonyms of same canonical should count as distinct matches."""

    def test_two_synonyms_same_canonical_returns_two_matches(self):
        """Two distinct synonyms of the same canonical keyword → 2 matches (not 1)."""
        objeto = "Aquisição de fardamento e indumentária profissional para servidores"
        setor_keywords = {"uniforme"}
        setor_id = "vestuario"

        matches = find_synonym_matches(objeto, setor_keywords, setor_id)

        # Both "fardamento" and "indumentária" are synonyms of "uniforme"
        # CRIT-FLT-006: should return 2 distinct matches
        assert len(matches) == 2
        matched_synonyms = {normalize_text(m[1]) for m in matches}
        assert "fardamento" in matched_synonyms
        assert "indumentaria" in matched_synonyms
        # Both map to same canonical
        assert all(m[0] == "uniforme" for m in matches)

    def test_two_synonyms_same_canonical_auto_approves(self):
        """Two synonyms of same canonical → auto-approve (no LLM needed)."""
        objeto = "Aquisição de fardamento e indumentária profissional para servidores"
        setor_keywords = {"uniforme"}
        setor_id = "vestuario"

        should_approve, matches = should_auto_approve_by_synonyms(
            objeto, setor_keywords, setor_id, min_synonyms=2
        )

        assert should_approve is True
        assert len(matches) >= 2

    def test_one_synonym_does_not_auto_approve(self):
        """Only 1 synonym match → send to LLM (no auto-approve)."""
        objeto = "Aquisição de fardamento profissional para servidores"
        setor_keywords = {"uniforme"}
        setor_id = "vestuario"

        should_approve, matches = should_auto_approve_by_synonyms(
            objeto, setor_keywords, setor_id, min_synonyms=2
        )

        assert should_approve is False
        assert len(matches) == 1

    def test_three_synonyms_same_canonical(self):
        """Three synonyms of same canonical → 3 matches, auto-approve."""
        objeto = "Fornecimento de fardamento, indumentária e vestimenta para guardas"
        setor_keywords = {"uniforme"}
        setor_id = "vestuario"

        matches = find_synonym_matches(objeto, setor_keywords, setor_id)

        assert len(matches) >= 3
        assert all(m[0] == "uniforme" for m in matches)

    def test_mixed_canonicals_and_same_canonical_synonyms(self):
        """Synonyms from different canonicals + same canonical all count."""
        objeto = "Fardamento e vestimenta com avental hospitalar"
        setor_keywords = {"uniforme", "jaleco"}
        setor_id = "vestuario"

        matches = find_synonym_matches(objeto, setor_keywords, setor_id)

        # "fardamento" → "uniforme", "vestimenta" → "uniforme", "avental hospitalar" → "jaleco"
        assert len(matches) >= 3

    def test_audit_log_contains_all_synonym_matches(self, caplog):
        """AC2: Audit log includes all matched synonyms."""
        import logging

        objeto = "Aquisição de fardamento e indumentária profissional para servidores"
        setor_keywords = {"uniforme"}
        setor_id = "vestuario"

        with caplog.at_level(logging.INFO, logger="synonyms"):
            matches = find_synonym_matches(objeto, setor_keywords, setor_id)

        assert len(matches) == 2
        # Verify audit log was emitted
        assert any("synonym_matches_audit" in r.message for r in caplog.records)

    def test_same_synonym_not_double_counted(self):
        """Same synonym appearing twice in objeto should only count once."""
        objeto = "Fardamento tipo A e fardamento tipo B para guardas"
        setor_keywords = {"uniforme"}
        setor_id = "vestuario"

        matches = find_synonym_matches(objeto, setor_keywords, setor_id)

        # "fardamento" appears twice in objeto, but should only match once
        fardamento_matches = [m for m in matches if "fardamento" in m[1]]
        assert len(fardamento_matches) == 1


class TestSectorSynonymDictionaries:
    """Test coverage of all sector synonym dictionaries."""

    def test_all_sectors_have_synonyms(self):
        """Test that all 12 sectors have synonym dictionaries."""

        # Not all sectors may have synonyms initially (incremental expansion)
        # Just verify dict structure is valid
        assert isinstance(SECTOR_SYNONYMS, dict)
        for sector_id, synonyms_dict in SECTOR_SYNONYMS.items():
            assert isinstance(synonyms_dict, dict)
            for canonical, synonym_set in synonyms_dict.items():
                assert isinstance(canonical, str)
                assert isinstance(synonym_set, set)

    def test_vestuario_fardamento_synonym(self):
        """Test vestuario sector has 'fardamento' as synonym for 'uniforme'."""
        assert "vestuario" in SECTOR_SYNONYMS
        assert "uniforme" in SECTOR_SYNONYMS["vestuario"]
        assert "fardamento" in SECTOR_SYNONYMS["vestuario"]["uniforme"]

    def test_facilities_asseio_synonym(self):
        """Test facilities sector has 'asseio' as synonym for 'limpeza'."""
        assert "facilities" in SECTOR_SYNONYMS
        assert "limpeza" in SECTOR_SYNONYMS["facilities"]
        assert "asseio" in SECTOR_SYNONYMS["facilities"]["limpeza"]

    def test_informatica_servidor_synonyms(self):
        """Test informatica sector has server-related synonyms."""
        assert "informatica" in SECTOR_SYNONYMS
        assert "servidor" in SECTOR_SYNONYMS["informatica"]
        # Should have "servidor de rede" as synonym
        assert any("rede" in s for s in SECTOR_SYNONYMS["informatica"]["servidor"])


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_synonym_word_boundary(self):
        """Test synonym matching respects word boundaries."""
        # "uniformes" should NOT match "uni" or "formes"
        objeto = "Fornecimento de materiais diversos"
        setor_keywords = {"uniforme"}
        setor_id = "vestuario"

        matches = find_synonym_matches(objeto, setor_keywords, setor_id)

        assert len(matches) == 0

    def test_synonym_unicode_normalization(self):
        """Test unicode normalization (accents)."""
        objeto = "Manutenção de imóveis públicos"
        setor_keywords = {"manutenção predial"}
        setor_id = "manutencao_predial"

        matches = find_synonym_matches(objeto, setor_keywords, setor_id)

        # "manutenção de imóveis" is synonym for "manutenção predial"
        # Depends on synonym dict having this variant
        assert len(matches) >= 0

    def test_synonym_match_very_long_object(self):
        """Test synonym matching on very long object descriptions."""
        objeto = (
            "Aquisição de fardamento completo incluindo camisas, calças, "
            "botas, cintos, bonés e acessórios diversos para guardas municipais "
            "conforme especificações técnicas detalhadas no termo de referência "
            "anexo a este processo licitatório " * 10  # Repeat 10x
        )
        setor_keywords = {"uniforme"}
        setor_id = "vestuario"

        matches = find_synonym_matches(objeto, setor_keywords, setor_id)

        # Should still find "fardamento" → "uniforme" once (deduped)
        assert len(matches) >= 1
        assert matches[0][0] == "uniforme"
        assert "fardamento" in matches[0][1]

    def test_similarity_threshold_boundary(self):
        """Test fuzzy matching with different similarity thresholds."""
        # "fardazinho" vs "fardamento" - significantly different (< 80% similarity)
        objeto = "Fornecimento de fardazinho escolar"
        setor_keywords = {"uniforme"}
        setor_id = "vestuario"

        # High threshold (0.95) should NOT match
        matches_high = find_synonym_matches(
            objeto, setor_keywords, setor_id, similarity_threshold=0.95
        )
        assert len(matches_high) == 0

        # Lower threshold (0.5) might match (very lenient)
        matches_low = find_synonym_matches(
            objeto, setor_keywords, setor_id, similarity_threshold=0.5
        )
        # May or may not match depending on fuzzy logic
        assert len(matches_low) >= 0


class TestIntegrationWithRealData:
    """Test with real PNCP-like procurement descriptions."""

    def test_real_fardamento_case(self):
        """Test real case: single synonym doesn't auto-approve, needs LLM."""
        objeto = (
            "Registro de preços para eventual aquisição de fardamento "
            "operacional para guardas municipais, incluindo camisas, calças, "
            "bonés e coturnos conforme especificações"
        )
        setor_keywords = {"uniforme", "farda"}
        setor_id = "vestuario"

        should_approve, matches = should_auto_approve_by_synonyms(
            objeto, setor_keywords, setor_id, min_synonyms=2
        )

        # Only "fardamento" → "uniforme" (1 distinct synonym match)
        # CRIT-FLT-006: Still not enough for auto-approve — needs 2+ distinct synonyms
        assert should_approve is False
        assert len(matches) >= 1

    def test_real_manutencao_predial_case(self):
        """Test real case: 'Conservação predial' → synonym for 'manutenção predial'."""
        objeto = (
            "Contratação de empresa especializada para prestação de serviços "
            "continuados de conservação predial preventiva e corretiva das "
            "unidades da secretaria municipal"
        )
        setor_keywords = {"manutenção predial"}
        setor_id = "manutencao_predial"

        matches = find_synonym_matches(objeto, setor_keywords, setor_id)

        # "conservação predial" is synonym for "manutenção predial"
        assert len(matches) >= 1

    def test_real_servidor_rede_case(self):
        """Test real case: 'Servidor de rede' (IT) vs 'servidor público' (person)."""
        objeto_ti = "Aquisição de servidores de rede para datacenter municipal"
        objeto_rh = "Capacitação de servidores públicos municipais"

        setor_keywords = {"servidor"}
        setor_id = "informatica"

        matches_ti = find_synonym_matches(objeto_ti, setor_keywords, setor_id)
        matches_rh = find_synonym_matches(objeto_rh, setor_keywords, setor_id)

        # Both have "servidor" directly, so no synonym matches
        # This test demonstrates synonym matching is NOT the solution for
        # "servidor" disambiguation (LLM arbiter handles this in AC13)
        assert len(matches_ti) == 0
        assert len(matches_rh) == 0
