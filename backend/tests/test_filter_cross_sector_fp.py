"""STORY-328 AC18-AC20: Cross-sector false positive elimination tests.

Tests cover:
- AC18: Synthetic examples for each of 15 sectors
- AC19: Legitimate bids continue to pass
- AC20: Regression — no new failures in existing filter tests
- AC22: End-to-end pipeline test with sample bids
"""

import pytest

from filter import (
    _strip_org_context,
    _strip_org_context_with_detail,
    match_keywords,
    normalize_text,
    GLOBAL_EXCLUSIONS_NORMALIZED,
    GLOBAL_EXCLUSION_OVERRIDES,
)
from sectors import get_sector


# ============================================================================
# AC18: Synthetic cross-sector tests — each sector gets a false positive test
# ============================================================================


class TestCrossSectorFalsePositives:
    """For each sector, test that generic purchases with org name are handled."""

    @pytest.mark.parametrize("sector_id,generic_purchase,org_name", [
        ("saude", "Locação de veículos", "Secretaria de Saúde"),
        ("saude", "Material de escritório", "Hospital Municipal de São Paulo"),
        ("saude", "Gêneros alimentícios", "Secretaria Municipal de Saúde"),
        ("informatica", "Uniformes escolares", "Secretaria de Tecnologia da Informação"),
        ("informatica", "Material de limpeza", "Instituto de Tecnologia"),
        ("vigilancia", "Material de escritório", "Secretaria de Segurança Pública"),
        ("vigilancia", "Gêneros alimentícios", "Departamento de Segurança"),
        ("vestuario", "Equipamentos de informática", "Fábrica de Confecções Municipal"),
        ("alimentos", "Material de escritório", "Secretaria de Alimentação"),
        ("facilities", "Uniformes para equipe", "Empresa de Limpeza Predial"),
        ("engenharia_rodoviaria", "Material de escritório", "Departamento de Estradas"),
        ("transporte_servicos", "Material de escritório", "Secretaria de Transportes"),
        ("materiais_eletricos", "Material de limpeza", "Companhia de Energia"),
        ("materiais_hidraulicos", "Material de escritório", "Companhia de Saneamento"),
        ("mobiliario", "Material de limpeza", "Fábrica de Móveis"),
    ])
    def test_generic_purchase_with_org_name_stripped(
        self, sector_id, generic_purchase, org_name
    ):
        """AC18: Generic purchase + org name should have org context stripped."""
        texto = f"{generic_purchase} para atender às necessidades da {org_name}"
        stripped = _strip_org_context(texto)
        # The org name should be stripped
        assert org_name not in stripped, (
            f"Org name '{org_name}' should have been stripped from: {texto}"
        )
        # The generic purchase description should remain
        assert generic_purchase.lower() in stripped.lower() or \
               normalize_text(generic_purchase) in normalize_text(stripped), (
            f"Generic purchase '{generic_purchase}' should remain in stripped text"
        )


# ============================================================================
# AC19: Legitimate bids should continue to pass
# ============================================================================


class TestLegitimatePassThrough:
    """Ensure legitimate sector-specific bids are NOT incorrectly stripped."""

    @pytest.mark.parametrize("sector_id,legitimate_text", [
        ("saude", "Aquisição de medicamentos para hospital municipal — lote antibióticos"),
        ("saude", "Equipamentos médicos hospitalares para UTI neonatal do SUS"),
        ("saude", "Material cirúrgico e instrumentais para centro cirúrgico"),
        ("informatica", "Aquisição de servidores Dell PowerEdge para datacenter"),
        ("informatica", "Notebooks e estações de trabalho para rede corporativa"),
        ("informatica", "Licenciamento de software Microsoft Office 365"),
        ("vigilancia", "Contratação de vigilância patrimonial armada 24 horas"),
        ("vigilancia", "Instalação de sistema CFTV com monitoramento remoto"),
        ("vigilancia", "Serviço de controle de acesso e portaria"),
        ("vestuario", "Confecção de uniformes escolares para alunos da rede municipal"),
        ("vestuario", "Aquisição de EPIs — luvas, botas e jalecos para equipe"),
        ("alimentos", "Fornecimento de merenda escolar e gêneros alimentícios"),
        ("facilities", "Serviço de limpeza e conservação predial"),
        ("transporte_servicos", "Locação de veículos tipo van para transporte escolar"),
        ("mobiliario", "Aquisição de mesas e cadeiras para escritório"),
    ])
    def test_legitimate_bid_not_stripped(self, sector_id, legitimate_text):
        """AC19: Legitimate bids should pass through _strip_org_context unchanged."""
        result = _strip_org_context(legitimate_text)
        assert result == legitimate_text, (
            f"Legitimate text should not be stripped. "
            f"Original: {legitimate_text!r}, Got: {result!r}"
        )


# ============================================================================
# AC7-AC8: Global exclusions tests
# ============================================================================


class TestGlobalExclusions:
    """Test that global exclusions block generic purchases."""

    def test_global_exclusions_are_normalized(self):
        """All global exclusions should be normalized (no accents)."""
        for exc in GLOBAL_EXCLUSIONS_NORMALIZED:
            # Normalized text should have no accents
            assert exc == normalize_text(exc), (
                f"Global exclusion '{exc}' is not properly normalized"
            )

    @pytest.mark.parametrize("exclusion_text", [
        "locacao de veiculo",
        "material de escritorio",
        "generos alimenticios",
        "equipamentos de informatica",
        "combustivel",
        "servico de limpeza",
        "construcao de muro",
        "material de copa e cozinha",
        "passagem aerea",
        "servico de telefonia",
    ])
    def test_global_exclusion_exists(self, exclusion_text):
        """Each expected global exclusion should be in the normalized set."""
        normalized = normalize_text(exclusion_text)
        assert normalized in GLOBAL_EXCLUSIONS_NORMALIZED, (
            f"Expected global exclusion '{exclusion_text}' not found"
        )


class TestGlobalExclusionOverrides:
    """AC10: Per-sector overrides allow sectors to bypass specific global exclusions."""

    def test_alimentos_overrides_generos_alimenticios(self):
        overrides = GLOBAL_EXCLUSION_OVERRIDES.get("alimentos", set())
        assert "generos alimenticios" in overrides

    def test_informatica_overrides_equipamentos_informatica(self):
        overrides = GLOBAL_EXCLUSION_OVERRIDES.get("informatica", set())
        assert "equipamentos de informatica" in overrides

    def test_facilities_overrides_servico_limpeza(self):
        overrides = GLOBAL_EXCLUSION_OVERRIDES.get("facilities", set())
        assert "servico de limpeza" in overrides

    def test_transporte_overrides_combustivel(self):
        overrides = GLOBAL_EXCLUSION_OVERRIDES.get("frota_veicular", set())
        assert "combustivel" in overrides

    def test_papelaria_overrides_material_escritorio(self):
        overrides = GLOBAL_EXCLUSION_OVERRIDES.get("papelaria", set())
        assert "material de escritorio" in overrides

    def test_transporte_overrides_locacao_veiculo(self):
        overrides = GLOBAL_EXCLUSION_OVERRIDES.get("transporte_servicos", set())
        assert "locacao de veiculo" in overrides or "locacao de veiculos" in overrides

    def test_override_removes_from_effective_set(self):
        """Verify that overrides actually remove items from the effective set."""
        for sector_id, override_set in GLOBAL_EXCLUSION_OVERRIDES.items():
            effective = GLOBAL_EXCLUSIONS_NORMALIZED - override_set
            for item in override_set:
                assert item not in effective, (
                    f"Override '{item}' for sector '{sector_id}' "
                    f"should not be in effective exclusions"
                )


# ============================================================================
# AC16: context_required_keywords for vulnerable sectors
# ============================================================================


class TestContextRequiredKeywords:
    """Test that vulnerable sector keywords have context requirements."""

    def test_saude_has_saude_context_required(self):
        config = get_sector("saude")
        crk = config.context_required_keywords
        assert "saude" in crk, "saude keyword should require context"
        assert "medico" in crk["saude"] or "médico" in crk["saude"]

    def test_informatica_has_tecnologia_context_required(self):
        config = get_sector("informatica")
        crk = config.context_required_keywords
        assert "tecnologia" in crk, "tecnologia keyword should require context"

    def test_vigilancia_has_seguranca_context_required(self):
        config = get_sector("vigilancia")
        crk = config.context_required_keywords
        # Check both normalized and accented forms
        has_seguranca = "seguranca" in crk or "segurança" in crk
        assert has_seguranca, "segurança/seguranca keyword should require context"


# ============================================================================
# AC22: End-to-end pipeline simulation with sample bids
# ============================================================================


class TestEndToEndPipeline:
    """Simulate the full filtering pipeline with realistic bid data."""

    def _make_bid(self, objeto, uf="SP", valor=100000.0, nome_orgao=""):
        return {
            "objetoCompra": objeto,
            "uf": uf,
            "valorTotalEstimado": valor,
            "dataAberturaProposta": "2026-12-31T10:00:00Z",
            "nomeOrgao": nome_orgao,
        }

    def test_strip_then_keyword_rejects_vehicle_rental_for_saude(self):
        """Vehicle rental bid with 'Secretaria de Saúde' should be stripped then fail keywords."""
        bid = self._make_bid(
            "Locação de veículos sedan para atender às necessidades "
            "da Secretaria de Estado da Saúde - SESA",
            nome_orgao="Secretaria de Estado da Saúde - SESA",
        )
        config = get_sector("saude")

        # Step 1: Strip org context
        stripped = _strip_org_context(bid["objetoCompra"])
        assert "Saúde" not in stripped

        # Step 2: Keyword match on stripped text
        match, terms = match_keywords(
            stripped,
            config.keywords,
            config.exclusions,
            config.context_required_keywords,
        )
        # Should NOT match saude keywords (vehicle rental is not health)
        assert not match, f"Vehicle rental should not match saude keywords. Matched: {terms}"

    def test_strip_then_keyword_accepts_legitimate_saude(self):
        """Legitimate health bid should pass keyword matching."""
        bid = self._make_bid(
            "Aquisição de medicamentos — antibióticos e analgésicos para "
            "atendimento hospitalar no SUS",
        )
        config = get_sector("saude")

        # Step 1: Strip org context (should not strip anything here)
        stripped = _strip_org_context(bid["objetoCompra"])
        assert "medicamentos" in stripped

        # Step 2: Keyword match
        match, terms = match_keywords(
            stripped,
            config.keywords,
            config.exclusions,
            config.context_required_keywords,
        )
        assert match, "Legitimate health bid should match saude keywords"

    def test_strip_then_keyword_rejects_office_supplies_for_informatica(self):
        """Office supplies for Secretaria de Tecnologia should fail IT keywords."""
        bid = self._make_bid(
            "Material de escritório e papelaria para atender às demandas "
            "da Secretaria de Tecnologia da Informação",
        )
        config = get_sector("informatica")

        stripped = _strip_org_context(bid["objetoCompra"])
        assert "Tecnologia" not in stripped

        match, terms = match_keywords(
            stripped,
            config.keywords,
            config.exclusions,
            config.context_required_keywords,
        )
        assert not match, f"Office supplies should not match informatica keywords. Matched: {terms}"

    def test_strip_then_keyword_rejects_food_for_vigilancia(self):
        """Food procurement for Secretaria de Segurança should fail security keywords."""
        bid = self._make_bid(
            "Gêneros alimentícios e material de limpeza para atender "
            "às necessidades da Secretaria de Segurança Pública",
        )
        config = get_sector("vigilancia")

        stripped = _strip_org_context(bid["objetoCompra"])
        assert "Segurança" not in stripped

        match, terms = match_keywords(
            stripped,
            config.keywords,
            config.exclusions,
            config.context_required_keywords,
        )
        assert not match, f"Food should not match vigilancia keywords. Matched: {terms}"

    def test_strip_preserves_legitimate_security_bid(self):
        """Legitimate security bid should pass even after stripping."""
        bid = self._make_bid(
            "Contratação de vigilância patrimonial armada e desarmada 24 horas "
            "com monitoramento eletrônico CFTV",
        )
        config = get_sector("vigilancia")

        stripped = _strip_org_context(bid["objetoCompra"])
        # No org clause to strip
        assert "vigilância patrimonial" in stripped

        match, terms = match_keywords(
            stripped,
            config.keywords,
            config.exclusions,
            config.context_required_keywords,
        )
        assert match, "Legitimate security bid should match vigilancia keywords"


# ============================================================================
# LLM prompt hardening tests (AC11-AC13)
# ============================================================================


class TestLLMPromptHardening:
    """Verify LLM prompts include org-name ignore instructions."""

    def test_zero_match_prompt_has_org_warning(self):
        from llm_arbiter import _build_zero_match_prompt
        prompt = _build_zero_match_prompt(
            setor_id="saude",
            setor_name="Saúde",
            objeto_truncated="Locação de veículos sedan",
            valor=50000.0,
        )
        assert "IGNORE" in prompt or "ignore" in prompt.lower()
        assert "órgão" in prompt.lower() or "orgao" in prompt.lower()

    def test_conservative_prompt_has_org_warning(self):
        from llm_arbiter import _build_conservative_prompt
        prompt = _build_conservative_prompt(
            setor_id="saude",
            setor_name="Saúde",
            objeto_truncated="Equipamentos diversos para hospital",
            valor=100000.0,
        )
        assert "IGNORE" in prompt or "ignore" in prompt.lower()
        assert "órgão" in prompt.lower() or "orgao" in prompt.lower()

    def test_zero_match_prompt_has_negative_examples(self):
        """AC13: Prompt should include dynamic negative examples for saude."""
        from llm_arbiter import _build_zero_match_prompt
        prompt = _build_zero_match_prompt(
            setor_id="saude",
            setor_name="Saúde",
            objeto_truncated="Material de escritório",
            valor=10000.0,
        )
        assert "ARMADILHA" in prompt or "armadilha" in prompt.lower()
        assert "Locação de veículos" in prompt or "veiculos" in prompt.lower()

    def test_conservative_prompt_has_negative_examples(self):
        """AC13: Conservative prompt should also include negative examples."""
        from llm_arbiter import _build_conservative_prompt
        prompt = _build_conservative_prompt(
            setor_id="saude",
            setor_name="Saúde",
            objeto_truncated="Material diverso",
            valor=10000.0,
        )
        assert "ARMADILHA" in prompt or "armadilha" in prompt.lower()

    def test_negative_examples_per_sector(self):
        """AC13: Different sectors should have different negative examples."""
        from llm_arbiter import _get_sector_negative_examples
        saude_examples = _get_sector_negative_examples("saude")
        informatica_examples = _get_sector_negative_examples("informatica")
        assert len(saude_examples) >= 2
        assert len(informatica_examples) >= 2
        assert saude_examples != informatica_examples

    def test_unknown_sector_returns_empty_examples(self):
        from llm_arbiter import _get_sector_negative_examples
        examples = _get_sector_negative_examples("nonexistent_sector")
        assert examples == []


# ============================================================================
# Metrics integration tests (AC23-AC25)
# ============================================================================


class TestOrgContextMetrics:
    """Test that org context stripping is tracked in metrics."""

    def test_org_context_stripped_field_set(self):
        """AC23: Bids should have _org_context_stripped field after processing."""
        # This tests the field is set during the filter pipeline
        # We test the function directly here
        texto = (
            "Material de escritório para atender às necessidades "
            "da Secretaria de Saúde"
        )
        stripped, removed = _strip_org_context_with_detail(texto)
        assert removed is not None
        assert "Secretaria" not in stripped

    def test_no_strip_returns_none_removed(self):
        """AC23: When no stripping, removed should be None."""
        texto = "Aquisição de medicamentos hospitalares"
        stripped, removed = _strip_org_context_with_detail(texto)
        assert removed is None

    def test_prometheus_metric_exists(self):
        """AC25: ORG_CONTEXT_STRIPPED metric should exist."""
        from metrics import ORG_CONTEXT_STRIPPED
        assert ORG_CONTEXT_STRIPPED is not None
