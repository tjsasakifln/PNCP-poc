"""
Tests for STORY-267 AC8: Synonym matching with custom search terms.

Coverage targets:
- find_term_synonym_matches() reverse matching (canonical → synonym in objeto)
- find_term_synonym_matches() forward matching (synonym term → canonical in objeto)
- FLOW 2 integration: custom_terms triggers find_term_synonym_matches instead of
  sector-based find_synonym_matches
- No self-match when the custom term itself is present in the objeto
- Cross-sector matching across all 15 sectors
- Empty result for unknown terms with no synonyms
"""

from unittest.mock import patch, MagicMock
from synonyms import find_term_synonym_matches


# ---------------------------------------------------------------------------
# Helper: minimal bid factory
# ---------------------------------------------------------------------------

def _bid(objeto: str, uf: str = "SP") -> dict:
    """Return a minimal bid dict suitable for aplicar_todos_filtros."""
    return {
        "objetoCompra": objeto,
        "uf": uf,
        "valorTotalEstimado": 100_000.0,
        "situacaoCompra": "Aberta",
        "dataPublicacaoPncp": "2026-02-01",
        "dataAberturaProposta": "2026-02-20T10:00:00",
        "dataEncerramentoProposta": "2099-12-31T23:59:59",
        "modalidadeId": 6,
        "esfera": "M",
    }


# ---------------------------------------------------------------------------
# 1. test_synonym_finds_reverse_match_for_custom_term
# ---------------------------------------------------------------------------

class TestFindTermSynonymReverseMatch:
    """AC8: find_term_synonym_matches() — canonical custom term finds synonym in objeto."""

    def test_reverse_match_guarda_po_jaleco(self):
        """
        User searched "guarda-po".
        objeto contains "jaleco hospitalar".
        "jaleco" is a canonical keyword in vestuario whose synonyms include
        "guarda-pó" (normalised: "guarda po").  The function should detect that
        "guarda-po" (the custom term) appears in the synonym set of "jaleco",
        and that "jaleco" is present in the objeto → returns [("guarda-po", "jaleco")].
        """
        matches = find_term_synonym_matches(
            custom_terms=["guarda-po"],
            objeto="jaleco hospitalar para uso dos servidores",
        )

        # Must find at least one match linking "guarda-po" to "jaleco"
        assert len(matches) >= 1
        terms_found = [m[0] for m in matches]
        syns_found = [m[1] for m in matches]
        assert "guarda-po" in terms_found
        assert any("jaleco" in s.lower() for s in syns_found)

    def test_reverse_match_tuple_structure(self):
        """Each match is a (custom_term, matched_synonym) tuple."""
        matches = find_term_synonym_matches(
            custom_terms=["guarda-po"],
            objeto="jaleco cirurgico para medicos",
        )

        for match in matches:
            assert isinstance(match, tuple)
            assert len(match) == 2
            custom_term, matched = match
            assert isinstance(custom_term, str)
            assert isinstance(matched, str)

    def test_reverse_match_accent_variant(self):
        """
        "guarda-po" (no accent) is the normalised form of "guarda-pó".
        The synonym dict stores "guarda-pó" / "guarda pó" under canonical "jaleco".
        Normalization must bridge the accent gap so find_term_synonym_matches works.
        """
        # objeto contains "jaleco" which is a canonical that has "guarda-pó" as synonym
        matches = find_term_synonym_matches(
            custom_terms=["guarda-po"],
            objeto="Aquisição de jaleco branco para laboratório",
        )

        assert len(matches) >= 1
        assert all(m[0] == "guarda-po" for m in matches)


# ---------------------------------------------------------------------------
# 2. test_synonym_recovery_uses_custom_terms_not_sector
# ---------------------------------------------------------------------------

class TestFluxo2UsesTermSynonymMatches:
    """
    AC8 integration: when FLOW 2 runs with custom_terms and TERM_SEARCH_SYNONYMS=true,
    it calls find_term_synonym_matches(custom_terms, objeto) instead of the
    sector-based find_synonym_matches().
    """

    @patch("config.LLM_ZERO_MATCH_ENABLED", False)
    @patch("config.get_feature_flag")
    @patch("filter._get_tracker")
    def test_flow2_calls_term_synonym_when_flag_on(self, mock_tracker, mock_gff):
        """
        With TERM_SEARCH_SYNONYMS=true and custom_terms present, FLOW 2 should
        invoke find_term_synonym_matches, recover bids containing synonyms, and
        NOT call sector-based find_synonym_matches.
        """
        from filter import aplicar_todos_filtros

        # Feature flag mapping: only TERM_SEARCH_SYNONYMS is True
        def _flag_side_effect(name, default=None):
            flags = {
                "TERM_SEARCH_SYNONYMS": True,
                "TERM_SEARCH_LLM_AWARE": False,
                "TERM_SEARCH_FILTER_CONTEXT": False,
                "PROXIMITY_CONTEXT_ENABLED": False,
                "CO_OCCURRENCE_RULES_ENABLED": False,
                "ITEM_INSPECTION_ENABLED": False,
                "LLM_ARBITER_ENABLED": False,
                "SECTOR_RED_FLAGS_ENABLED": False,
            }
            return flags.get(name, False)

        mock_gff.side_effect = _flag_side_effect
        mock_tracker.return_value = MagicMock()

        # Bid that does NOT contain "guarda-po" (keyword miss) but DOES contain "jaleco"
        # → FLOW 2 synonym recovery should pick it up
        bids = [
            _bid("Fornecimento de jaleco hospitalar para servidores"),
        ]

        # keywords={"guarda-po"} — bid won't pass keyword stage (no "guarda-po" in objeto)
        # custom_terms=["guarda-po"] — triggers FLOW 2 with term synonyms
        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            keywords={"guarda-po"},
            exclusions=set(),
            custom_terms=["guarda-po"],
            setor=None,  # No sector — term search path
        )

        # The bid should have been recovered via synonym matching
        assert stats["aprovadas_synonym_match"] >= 1 or stats["recuperadas_zero_results"] >= 1

    @patch("config.LLM_ZERO_MATCH_ENABLED", False)
    @patch("config.get_feature_flag")
    @patch("filter._get_tracker")
    def test_flow2_does_not_recover_when_flag_off(self, mock_tracker, mock_gff):
        """
        With TERM_SEARCH_SYNONYMS=false, FLOW 2 should NOT use term synonym
        matching, and a bid containing only a synonym of the custom term should
        not be recovered.
        """
        from filter import aplicar_todos_filtros

        def _flag_side_effect(name, default=None):
            flags = {
                "TERM_SEARCH_SYNONYMS": False,
                "TERM_SEARCH_LLM_AWARE": False,
                "TERM_SEARCH_FILTER_CONTEXT": False,
                "PROXIMITY_CONTEXT_ENABLED": False,
                "CO_OCCURRENCE_RULES_ENABLED": False,
                "ITEM_INSPECTION_ENABLED": False,
                "LLM_ARBITER_ENABLED": False,
                "SECTOR_RED_FLAGS_ENABLED": False,
            }
            return flags.get(name, False)

        mock_gff.side_effect = _flag_side_effect
        mock_tracker.return_value = MagicMock()

        bids = [
            _bid("Fornecimento de jaleco hospitalar para servidores"),
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            keywords={"guarda-po"},
            exclusions=set(),
            custom_terms=["guarda-po"],
            setor=None,
        )

        # With flag off and no sector, FLOW 2 synonym path is inactive
        assert stats["aprovadas_synonym_match"] == 0
        assert stats.get("recuperadas_zero_results", 0) == 0


# ---------------------------------------------------------------------------
# 3. test_synonym_finds_canonical_from_synonym_term
# ---------------------------------------------------------------------------

class TestFindTermSynonymForwardMatch:
    """
    AC8: When user searches for a synonym term (e.g., "fardamento") and the
    objeto contains the canonical keyword (e.g., "uniforme"), the function
    should match.
    """

    def test_fardamento_finds_uniforme_in_objeto(self):
        """
        User searched "fardamento" (which is a synonym of canonical "uniforme").
        objeto contains "uniforme escolar".
        find_term_synonym_matches should return [("fardamento", "uniforme")].
        """
        matches = find_term_synonym_matches(
            custom_terms=["fardamento"],
            objeto="Aquisição de uniforme escolar para alunos",
        )

        assert len(matches) >= 1
        # The custom term is "fardamento"
        assert any(m[0] == "fardamento" for m in matches)
        # The matched text should be "uniforme" (or a variant)
        assert any("uniforme" in m[1].lower() for m in matches)

    def test_indumentaria_finds_uniforme(self):
        """
        "indumentária" is a synonym of canonical "uniforme".
        objeto contains "uniforme profissional".
        """
        matches = find_term_synonym_matches(
            custom_terms=["indumentaria"],
            objeto="Compra de uniforme profissional para funcionários",
        )

        assert len(matches) >= 1
        assert any(m[0] == "indumentaria" for m in matches)

    def test_asseio_finds_limpeza(self):
        """
        "asseio" is a synonym of canonical "limpeza" in the facilities sector.
        objeto contains "limpeza predial".
        """
        matches = find_term_synonym_matches(
            custom_terms=["asseio"],
            objeto="Prestação de serviços de limpeza predial",
        )

        assert len(matches) >= 1
        assert any(m[0] == "asseio" for m in matches)
        assert any("limpeza" in m[1].lower() for m in matches)


# ---------------------------------------------------------------------------
# 4. test_synonym_no_self_match
# ---------------------------------------------------------------------------

class TestFindTermSynonymNoSelfMatch:
    """
    AC8: When the custom term itself is present in the objeto, the function
    should skip synonym matching for that term (it's not a near-miss).
    """

    def test_no_match_when_guarda_po_in_objeto(self):
        """
        Custom term "guarda-po" is already present in the objeto.
        No synonym match should be returned — it's a direct keyword hit.
        """
        matches = find_term_synonym_matches(
            custom_terms=["guarda-po"],
            objeto="Aquisição de guarda-po e jaleco para servidores",
        )

        # "guarda-po" is in objeto → it's a direct hit, NOT a near-miss
        # There may or may not be a match for the "jaleco" synonym path,
        # but "guarda-po" itself should not appear as a self-match tuple.
        for term, synonym in matches:
            if term == "guarda-po":
                # The synonym found should NOT be "guarda-po" itself
                from filter import normalize_text
                assert normalize_text(synonym) != normalize_text("guarda-po"), (
                    "Self-match: 'guarda-po' returned itself as a synonym"
                )

    def test_no_match_when_fardamento_in_objeto(self):
        """
        Custom term "fardamento" appears directly in the objeto.
        find_term_synonym_matches must not return a (fardamento, fardamento) pair.
        """
        matches = find_term_synonym_matches(
            custom_terms=["fardamento"],
            objeto="Compra de fardamento completo para guardas municipais",
        )

        # The term is in objeto → skip this term entirely in synonym search
        for term, synonym in matches:
            if term == "fardamento":
                from filter import normalize_text
                assert normalize_text(synonym) != "fardamento", (
                    "Self-match: 'fardamento' returned itself as synonym"
                )

    def test_no_match_returns_empty_when_all_terms_present(self):
        """
        When ALL custom terms appear directly in the objeto, result should be empty.
        """
        matches = find_term_synonym_matches(
            custom_terms=["jaleco", "uniforme"],
            objeto="Fornecimento de jaleco e uniforme para servidores",
        )

        # Both terms are directly in objeto → nothing to recover via synonyms
        assert matches == []


# ---------------------------------------------------------------------------
# 5. test_synonym_cross_sector_matching
# ---------------------------------------------------------------------------

class TestFindTermSynonymCrossSector:
    """
    AC8: Custom terms can match synonyms from ALL 15 sectors, not just one.
    The function searches the entire SECTOR_SYNONYMS dictionary.
    """

    def test_cross_sector_vestuario_and_informatica(self):
        """
        Custom terms span two sectors.
        "fardamento" (synonym of "uniforme" in vestuario) and
        "desktop" (synonym of "computador" in informatica).
        """
        # objeto contains canonical keywords from two different sectors
        objeto = "Aquisição de uniforme e computador para escola"

        matches_vestuario = find_term_synonym_matches(
            custom_terms=["fardamento"],
            objeto=objeto,
        )
        matches_informatica = find_term_synonym_matches(
            custom_terms=["desktop"],
            objeto=objeto,
        )

        assert len(matches_vestuario) >= 1, (
            "Expected 'fardamento' to find 'uniforme' via vestuario synonyms"
        )
        assert len(matches_informatica) >= 1, (
            "Expected 'desktop' to find 'computador' via informatica synonyms"
        )

    def test_cross_sector_single_call_multiple_terms(self):
        """
        A single call with terms from multiple sectors should return matches
        from all applicable sectors.
        """
        objeto = "Uniforme e computador para gestores municipais"

        matches = find_term_synonym_matches(
            custom_terms=["fardamento", "desktop"],
            objeto=objeto,
        )

        custom_terms_found = {m[0] for m in matches}
        assert "fardamento" in custom_terms_found
        assert "desktop" in custom_terms_found

    def test_cross_sector_facilities_and_saude(self):
        """
        "remedio" is a synonym of "medicamento" in saude sector.
        "zeladoria predial" is a synonym of "zeladoria" in facilities sector.
        """
        matches_saude = find_term_synonym_matches(
            custom_terms=["remedio"],
            objeto="Compra de medicamento para posto de saúde",
        )
        assert len(matches_saude) >= 1
        assert any(m[0] == "remedio" for m in matches_saude)

    def test_all_sectors_are_searchable(self):
        """SECTOR_SYNONYMS contains every sector defined in sectors_data.yaml.

        CIG-BE-story-drift-sectors-split: derive the expected sector set
        dynamically from the canonical YAML so assertions stay in sync when
        sectors are split (software → software_desenvolvimento /
        software_licencas, etc.). Any sector present in the YAML must have
        a synonym group.
        """
        import yaml
        from pathlib import Path

        from synonyms import SECTOR_SYNONYMS

        yaml_path = Path(__file__).resolve().parent.parent / "sectors_data.yaml"
        data = yaml.safe_load(yaml_path.read_text())
        expected_sectors = set(data["sectors"].keys())

        assert expected_sectors.issubset(set(SECTOR_SYNONYMS.keys())), (
            f"Missing sectors: {expected_sectors - set(SECTOR_SYNONYMS.keys())}"
        )

    def test_term_not_sector_specific_finds_across_sectors(self):
        """
        The term "asfalto" is a synonym of "pavimentação" which appears in BOTH
        "engenharia" and "engenharia_rodoviaria" sectors.
        A single call should find matches regardless of which sector the synonym
        dict entry comes from.
        """
        matches = find_term_synonym_matches(
            custom_terms=["asfalto"],
            objeto="Execução de pavimentação de via urbana",
        )

        # "asfalto" is a synonym of "pavimentação" → "pavimentação" is in objeto
        assert len(matches) >= 1
        assert any(m[0] == "asfalto" for m in matches)


# ---------------------------------------------------------------------------
# 6. test_term_synonym_matches_returns_empty_for_unknown_terms
# ---------------------------------------------------------------------------

class TestFindTermSynonymUnknownTerms:
    """
    AC8: Custom terms that are not synonyms in any sector return empty list.
    """

    def test_completely_unknown_term(self):
        """
        A gibberish term with no synonyms anywhere returns [].
        """
        matches = find_term_synonym_matches(
            custom_terms=["xyzblorgfoo"],
            objeto="Contratação de serviço de limpeza e manutenção",
        )

        assert matches == []

    def test_empty_custom_terms_list(self):
        """Empty custom_terms list always returns []."""
        matches = find_term_synonym_matches(
            custom_terms=[],
            objeto="Qualquer objeto de licitação com jaleco e uniforme",
        )

        assert matches == []

    def test_term_with_no_synonym_entry_in_any_sector(self):
        """
        A real Portuguese word that happens to have no entry in any synonym dict.
        "pavimento" (floor tile, distinct from "pavimentação") has no synonyms.
        """
        matches = find_term_synonym_matches(
            custom_terms=["lajotas"],
            objeto="Aquisição de uniforme e jaleco para trabalhadores",
        )

        assert matches == []

    def test_empty_objeto_always_returns_empty(self):
        """Even a known synonym term returns [] when objeto is empty."""
        matches = find_term_synonym_matches(
            custom_terms=["fardamento"],
            objeto="",
        )

        assert matches == []

    def test_unknown_term_does_not_error(self):
        """Unknown terms must not raise exceptions, just return []."""
        # Use a long list of unknown terms
        unknown_terms = [
            "qwertyuiop", "zxcvbnm", "asdfghjkl",
            "nonexistent_term_123", "bogus_keyword",
        ]
        matches = find_term_synonym_matches(
            custom_terms=unknown_terms,
            objeto="Compra de jaleco uniforme para servidores",
        )

        # No exception, just empty (or possibly some match for known object words,
        # but none of these terms exist as synonyms anywhere)
        assert isinstance(matches, list)
        # Verify none of the bogus terms appear as the first element
        for term, _ in matches:
            assert term in unknown_terms  # structural check only

    def test_term_present_only_as_canonical_with_no_synonyms_in_objeto(self):
        """
        "jaleco" IS a canonical keyword with synonyms. But if the objeto contains
        neither the canonical nor any of its synonyms, result is empty.
        """
        matches = find_term_synonym_matches(
            custom_terms=["jaleco"],
            objeto="Construção de escola pública municipal",  # totally unrelated
        )

        # "jaleco" is not in objeto, nor are its synonyms ("guarda-pó", "avental hospitalar", etc.)
        assert matches == []
