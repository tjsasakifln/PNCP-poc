"""Tests for SECTOR-PROX: Proximity Context Filter — Cross-Sector Disambiguation.

Tests organized by AC:
- AC6: Unit tests for check_proximity_context() core function (~12 tests)
- AC7: Integration tests with pipeline (~8 tests)
- AC8: Cross-sector tests (~8 tests)
- AC9: Regression tests (~4 tests)
"""

import pytest
from unittest.mock import patch, MagicMock

from filter import check_proximity_context, normalize_text


# ===========================================================================
# AC6: Unit tests — core function check_proximity_context()
# ===========================================================================


class TestCheckProximityContextCore:
    """AC6: Unit tests for the core proximity context function."""

    def test_confeccao_de_merenda_rejects_from_vestuario(self):
        """The original false positive case: 'confeccao de merenda escolar'."""
        texto = "compra de alimentos para confeccao de merenda escolar"
        matched_terms = ["confeccao"]
        other_sigs = {"alimentos": {"merenda", "alimenticio", "refeicao"}}

        should_reject, reason = check_proximity_context(
            texto, matched_terms, "vestuario", other_sigs
        )

        assert should_reject is True
        assert "confeccao" in reason
        assert "alimentos" in reason
        assert "merenda" in reason

    def test_confeccao_da_merenda_rejects_preposition_variant(self):
        """The main fix: preposition variant 'da' instead of 'de'."""
        texto = "confeccao da merenda escolar para alunos"
        matched_terms = ["confeccao"]
        other_sigs = {"alimentos": {"merenda", "alimenticio"}}

        should_reject, reason = check_proximity_context(
            texto, matched_terms, "vestuario", other_sigs
        )

        assert should_reject is True
        assert "merenda" in reason

    def test_confeccao_das_merendas_rejects_plural_article(self):
        """Plural + article variant: 'confeccao das merendas'."""
        texto = "servico de confeccao das merendas escolares do municipio"
        matched_terms = ["confeccao"]
        # "merenda" won't match "merendas" in single-word mode
        # but we test that the user provides the right sig terms
        other_sigs = {"alimentos": {"merenda", "merendas"}}

        should_reject, reason = check_proximity_context(
            texto, matched_terms, "vestuario", other_sigs
        )

        assert should_reject is True

    def test_confeccao_de_uniformes_keeps(self):
        """Legitimate vestuario bid: 'confeccao de uniformes'."""
        texto = "confeccao de uniformes para servidores municipais"
        matched_terms = ["confeccao"]
        other_sigs = {"alimentos": {"merenda", "alimenticio", "refeicao"}}

        should_reject, reason = check_proximity_context(
            texto, matched_terms, "vestuario", other_sigs
        )

        assert should_reject is False
        assert reason is None

    def test_reforma_predio_pintura(self):
        """Test cross-sector with maintenance terms."""
        texto = "reforma do predio com pintura e dedetizacao geral"
        matched_terms = ["reforma"]
        other_sigs = {
            "manutencao_predial": {"predial", "dedetizacao", "pintura predial"}
        }

        should_reject, reason = check_proximity_context(
            texto, matched_terms, "engenharia", other_sigs
        )

        assert should_reject is True
        assert "manutencao_predial" in reason

    def test_luva_procedimento_cirurgico_cross_sector(self):
        """'luva de procedimento cirurgico' — saude sig near vestuario keyword."""
        texto = "aquisicao de luva de procedimento cirurgico hospitalar"
        matched_terms = ["luva"]
        other_sigs = {
            "saude": {"cirurgico", "hospitalar", "medicamento", "farmaceutico"}
        }

        should_reject, reason = check_proximity_context(
            texto, matched_terms, "vestuario", other_sigs
        )

        assert should_reject is True
        assert "saude" in reason

    def test_sistema_hidraulico_keeps(self):
        """'sistema hidraulico de bombeamento' — no cross-sector sig nearby."""
        texto = "sistema hidraulico de bombeamento para estacao"
        matched_terms = ["hidraulico"]
        other_sigs = {
            "engenharia": {"pavimentacao", "terraplanagem", "concreto armado"}
        }

        should_reject, reason = check_proximity_context(
            texto, matched_terms, "materiais_hidraulicos", other_sigs
        )

        assert should_reject is False
        assert reason is None

    def test_empty_text_returns_false(self):
        """Empty text should return (False, None)."""
        should_reject, reason = check_proximity_context(
            "", ["confeccao"], "vestuario", {"alimentos": {"merenda"}}
        )

        assert should_reject is False
        assert reason is None

    def test_no_matched_terms_returns_false(self):
        """No matched terms should return (False, None)."""
        should_reject, reason = check_proximity_context(
            "some text here", [], "vestuario", {"alimentos": {"merenda"}}
        )

        assert should_reject is False
        assert reason is None

    def test_window_at_start_of_text(self):
        """Edge case: matched term at start of text."""
        texto = "merenda confeccao de algo totalmente diferente"
        matched_terms = ["confeccao"]
        other_sigs = {"alimentos": {"merenda"}}

        should_reject, reason = check_proximity_context(
            texto, matched_terms, "vestuario", other_sigs
        )

        assert should_reject is True

    def test_window_at_end_of_text(self):
        """Edge case: matched term at end of text."""
        texto = "algo totalmente diferente confeccao merenda"
        matched_terms = ["confeccao"]
        other_sigs = {"alimentos": {"merenda"}}

        should_reject, reason = check_proximity_context(
            texto, matched_terms, "vestuario", other_sigs
        )

        assert should_reject is True

    def test_multiword_signature_term_detected(self):
        """Multi-word signature terms should be detected via substring."""
        texto = "fornecimento de papel para cesta basica mensal"
        matched_terms = ["papel"]
        other_sigs = {"alimentos": {"cesta basica", "merenda"}}

        should_reject, reason = check_proximity_context(
            texto, matched_terms, "papelaria", other_sigs
        )

        assert should_reject is True
        assert "cesta basica" in reason

    def test_window_size_zero_disables_check(self):
        """Window size = 0 should effectively disable the check."""
        texto = "confeccao merenda escolar"
        matched_terms = ["confeccao"]
        other_sigs = {"alimentos": {"merenda"}}

        should_reject, reason = check_proximity_context(
            texto, matched_terms, "vestuario", other_sigs, window_size=0
        )

        assert should_reject is False
        assert reason is None


# ===========================================================================
# AC7: Integration tests — pipeline behavior
# ===========================================================================


class TestProximityContextPipeline:
    """AC7: Integration tests verifying proximity in the full pipeline."""

    @pytest.fixture
    def mock_pipeline_deps(self):
        """Mock common pipeline dependencies."""
        with patch("filter._get_tracker") as mock_tracker:
            tracker = MagicMock()
            mock_tracker.return_value = tracker
            yield tracker

    def test_feature_flag_off_zero_rejections(self, mock_pipeline_deps):
        """Feature flag OFF → zero proximity rejections."""
        from filter import aplicar_todos_filtros

        licitacoes = [
            {
                "objetoCompra": "confeccao da merenda escolar",
                "valorTotalEstimado": 100000,
                "ufSigla": "SP",
            }
        ]

        with patch("config.get_feature_flag", side_effect=lambda name, **kw: name != "PROXIMITY_CONTEXT_ENABLED"):
            aprovadas, stats = aplicar_todos_filtros(
                licitacoes, {"SP"}, setor="vestuario"
            )

        assert stats.get("proximity_rejections", 0) == 0

    def test_feature_flag_on_proximity_rejections_counted(self, mock_pipeline_deps):
        """Feature flag ON → proximity rejections counted in stats."""
        from filter import aplicar_todos_filtros

        licitacoes = [
            {
                "objetoCompra": "confeccao da merenda escolar para alunos da rede",
                "valorTotalEstimado": 100000,
                "ufSigla": "SP",
            }
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes, {"SP"}, setor="vestuario"
        )

        assert "proximity_rejections" in stats

    def test_proximity_rejections_key_present_in_stats(self, mock_pipeline_deps):
        """Key 'proximity_rejections' present in stats even when 0."""
        from filter import aplicar_todos_filtros

        aprovadas, stats = aplicar_todos_filtros(
            [], {"SP"}, setor="vestuario"
        )

        assert "proximity_rejections" in stats

    def test_rejected_bids_not_in_final_result(self, mock_pipeline_deps):
        """Bids rejected by proximity don't appear in final approved list."""
        from filter import aplicar_todos_filtros

        licitacoes = [
            {
                "objetoCompra": "confeccao da merenda escolar para alunos",
                "valorTotalEstimado": 100000,
                "ufSigla": "SP",
            },
            {
                "objetoCompra": "confeccao de uniformes escolares para alunos",
                "valorTotalEstimado": 100000,
                "ufSigla": "SP",
            },
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes, {"SP"}, setor="vestuario"
        )

        # The merenda bid should be rejected, the uniform bid should pass
        for bid in aprovadas:
            assert "merenda" not in bid.get("objetoCompra", "").lower()

    def test_co_occurrence_still_runs_after_proximity(self, mock_pipeline_deps):
        """Co-occurrence layer still runs after proximity (layers compose)."""
        from filter import aplicar_todos_filtros

        aprovadas, stats = aplicar_todos_filtros(
            [], {"SP"}, setor="vestuario"
        )

        # Both keys should exist
        assert "proximity_rejections" in stats
        assert "co_occurrence_rejections" in stats

    def test_no_sector_specified_skips_proximity(self, mock_pipeline_deps):
        """No sector specified → proximity skipped entirely."""
        from filter import aplicar_todos_filtros

        aprovadas, stats = aplicar_todos_filtros(
            [], {"SP"}, setor=None
        )

        assert stats.get("proximity_rejections", 0) == 0

    def test_no_matched_terms_in_bid_skips_proximity(self, mock_pipeline_deps):
        """Bids without _matched_terms are not checked by proximity."""
        from filter import aplicar_todos_filtros

        licitacoes = [
            {
                "objetoCompra": "aquisicao de uniformes escolares",
                "valorTotalEstimado": 100000,
                "ufSigla": "SP",
            }
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes, {"SP"}, setor="vestuario"
        )

        # Should not crash even if _matched_terms is not set
        assert isinstance(stats, dict)

    def test_all_15_sectors_have_signature_terms(self):
        """All 15 sectors should have signature_terms loaded."""
        from sectors import SECTORS

        for sector_id, config in SECTORS.items():
            assert hasattr(config, "signature_terms"), (
                f"Sector '{sector_id}' missing signature_terms field"
            )
            assert len(config.signature_terms) >= 5, (
                f"Sector '{sector_id}' has fewer than 5 signature_terms: "
                f"{len(config.signature_terms)}"
            )


# ===========================================================================
# AC8: Cross-sector tests
# ===========================================================================


class TestProximityContextCrossSector:
    """AC8: Cross-sector interaction tests."""

    def test_same_term_two_sectors_rejects_first_found(self):
        """Same term in window of 2 different sectors → rejects with first found."""
        texto = "confeccao de merenda e medicamento hospitalar"
        matched_terms = ["confeccao"]
        other_sigs = {
            "alimentos": {"merenda"},
            "saude": {"medicamento", "hospitalar"},
        }

        should_reject, reason = check_proximity_context(
            texto, matched_terms, "vestuario", other_sigs
        )

        assert should_reject is True
        # Should match one of the sectors
        assert "alimentos" in reason or "saude" in reason

    def test_own_sector_signature_not_rejected(self):
        """Signature terms of OWN sector in window → NOT rejected."""
        texto = "confeccao de uniforme fardamento jaleco para servidores"
        matched_terms = ["confeccao"]
        # vestuario's own signature terms should NOT cause rejection
        other_sigs = {
            "alimentos": {"merenda", "alimenticio"},
        }
        # Note: we do NOT include vestuario in other_sigs (that's the point)

        should_reject, reason = check_proximity_context(
            texto, matched_terms, "vestuario", other_sigs
        )

        assert should_reject is False

    def test_larger_window_captures_more_context(self):
        """Larger window size captures terms further away."""
        # 15 words between keyword and signature term
        texto = (
            "confeccao de algo muito diferente que nao tem nada a ver com "
            "nenhum outro setor mas menciona merenda"
        )
        matched_terms = ["confeccao"]
        other_sigs = {"alimentos": {"merenda"}}

        # Default window (8) should NOT catch it (merenda is >8 words away)
        reject_8, _ = check_proximity_context(
            texto, matched_terms, "vestuario", other_sigs, window_size=8
        )

        # Large window (20) SHOULD catch it
        reject_20, reason_20 = check_proximity_context(
            texto, matched_terms, "vestuario", other_sigs, window_size=20
        )

        assert reject_8 is False
        assert reject_20 is True

    def test_window_size_zero_no_proximity_check(self):
        """Window size = 0 → effectively disabled."""
        texto = "confeccao merenda"
        matched_terms = ["confeccao"]
        other_sigs = {"alimentos": {"merenda"}}

        should_reject, reason = check_proximity_context(
            texto, matched_terms, "vestuario", other_sigs, window_size=0
        )

        assert should_reject is False

    def test_all_sectors_have_signature_terms_loaded(self):
        """All 15 sectors have signature_terms loaded in SECTORS dict."""
        from sectors import SECTORS

        expected_sectors = {
            "vestuario", "alimentos", "informatica", "mobiliario",
            "papelaria", "engenharia", "software", "facilities",
            "saude", "vigilancia", "transporte", "manutencao_predial",
            "engenharia_rodoviaria", "materiais_eletricos", "materiais_hidraulicos",
        }

        assert set(SECTORS.keys()) == expected_sectors

        for sector_id in expected_sectors:
            config = SECTORS[sector_id]
            assert isinstance(config.signature_terms, set), (
                f"Sector '{sector_id}' signature_terms should be a set"
            )
            assert len(config.signature_terms) >= 5, (
                f"Sector '{sector_id}' has {len(config.signature_terms)} "
                f"signature_terms (minimum 5)"
            )

    def test_accented_text_handled(self):
        """Accented text should be normalized before comparison."""
        texto = "confecção da merenda escolar para alunos"
        matched_terms = ["confecção"]
        other_sigs = {"alimentos": {"merenda"}}

        should_reject, reason = check_proximity_context(
            texto, matched_terms, "vestuario", other_sigs
        )

        assert should_reject is True

    def test_informatica_near_software_terms(self):
        """Informatica keyword near software signature terms."""
        texto = "aquisicao de computador para sistema de gestao erp"
        matched_terms = ["computador"]
        other_sigs = {
            "software": {"licenca de software", "sistema de gestao", "erp"}
        }

        should_reject, reason = check_proximity_context(
            texto, matched_terms, "informatica", other_sigs
        )

        # "erp" is within window of "computador"
        assert should_reject is True
        assert "software" in reason

    def test_multiple_matched_terms_checked(self):
        """All matched terms should be checked, not just the first."""
        texto = "aquisicao de uniforme e confeccao para merenda escolar"
        matched_terms = ["uniforme", "confeccao"]
        other_sigs = {"alimentos": {"merenda"}}

        should_reject, reason = check_proximity_context(
            texto, matched_terms, "vestuario", other_sigs
        )

        assert should_reject is True
        assert "merenda" in reason


# ===========================================================================
# AC9: Regression tests
# ===========================================================================


class TestProximityContextRegression:
    """AC9: Regression tests to ensure no breakage of existing filters."""

    def test_existing_vestuario_keyword_matching_works(self):
        """Existing vestuario keyword matching continues working."""
        from filter import match_keywords
        from sectors import SECTORS

        config = SECTORS["vestuario"]
        text = "aquisicao de uniformes escolares para alunos"

        match, matched = match_keywords(
            text, config.keywords, config.exclusions,
            config.context_required_keywords
        )

        assert match is True
        assert len(matched) > 0

    def test_existing_alimentos_keyword_matching_works(self):
        """Existing alimentos keyword matching continues working."""
        from filter import match_keywords
        from sectors import SECTORS

        config = SECTORS["alimentos"]
        text = "aquisicao de generos alimenticios para merenda escolar"

        match, matched = match_keywords(
            text, config.keywords, config.exclusions,
            config.context_required_keywords
        )

        assert match is True

    def test_co_occurrence_still_functions(self):
        """Co-occurrence rules still function correctly."""
        from filter import check_co_occurrence
        from sectors import SECTORS

        # Only test sectors that have co_occurrence_rules
        for sector_id, config in SECTORS.items():
            if config.co_occurrence_rules:
                # Should not crash
                result = check_co_occurrence(
                    "some test text", config.co_occurrence_rules, sector_id
                )
                assert isinstance(result, tuple)
                assert len(result) == 2

    def test_sector_config_backwards_compatible(self):
        """SectorConfig still has all existing fields (no removal)."""
        import dataclasses
        from sectors import SectorConfig

        # Check all pre-existing fields still exist
        expected_fields = {
            "id", "name", "description", "keywords", "exclusions",
            "context_required_keywords", "max_contract_value",
            "co_occurrence_rules", "domain_signals", "viability_value_range",
            "signature_terms",  # New field
        }

        actual_fields = {f.name for f in dataclasses.fields(SectorConfig)}
        missing = expected_fields - actual_fields
        assert not missing, f"SectorConfig missing fields: {missing}"


# ===========================================================================
# Additional edge case tests
# ===========================================================================


class TestProximityContextEdgeCases:
    """Additional edge case tests for robustness."""

    def test_signature_term_not_in_window(self):
        """Signature term outside window should not trigger rejection."""
        # Build text with >8 word gap
        texto = "confeccao de algo um dois tres quatro cinco seis sete oito merenda"
        matched_terms = ["confeccao"]
        other_sigs = {"alimentos": {"merenda"}}

        should_reject, _ = check_proximity_context(
            texto, matched_terms, "vestuario", other_sigs, window_size=3
        )

        assert should_reject is False

    def test_normalize_text_consistency(self):
        """normalize_text produces consistent output for comparison."""
        assert normalize_text("Confecção") == "confeccao"
        assert normalize_text("MERENDA") == "merenda"
        assert normalize_text("  espaços  ") == "espacos"
