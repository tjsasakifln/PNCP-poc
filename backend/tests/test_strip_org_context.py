"""STORY-328 AC17/AC21: Tests for _strip_org_context() function.

Tests cover:
- AC1: All org context clause patterns (para atender, de interesse, etc.)
- AC2: PCP source prefix stripping
- AC3: Accent-insensitive matching
- AC4: Original text preservation for display
- AC17: Real production examples from Saúde sector (2026-02-28)
- AC21: 20+ variations of org context clauses
"""


from filter import _strip_org_context, _strip_org_context_with_detail


# ============================================================================
# AC21: 20+ variations of org context clauses
# ============================================================================


class TestStripOrgContextBasicPatterns:
    """Test each regex pattern individually."""

    def test_para_atender_necessidades(self):
        texto = (
            "Contratação de empresa para prestação de serviços de locação de veículos "
            "para atender às necessidades da Secretaria de Estado da Saúde - SESA"
        )
        result = _strip_org_context(texto)
        assert "Secretaria" not in result
        assert "Saúde" not in result
        assert "locação de veículos" in result

    def test_para_atendimento_demandas(self):
        texto = (
            "Aquisição de material de escritório "
            "para atendimento às demandas da Secretaria Municipal de Saúde"
        )
        result = _strip_org_context(texto)
        assert "Secretaria" not in result
        assert "material de escritório" in result

    def test_para_atender_necessidade(self):
        texto = (
            "Fornecimento de gêneros alimentícios "
            "para atender a necessidade da Prefeitura Municipal"
        )
        result = _strip_org_context(texto)
        assert "Prefeitura" not in result
        assert "gêneros alimentícios" in result

    def test_em_atendimento_demanda(self):
        texto = (
            "Equipamentos de informática "
            "em atendimento à demanda da Secretaria de Tecnologia"
        )
        result = _strip_org_context(texto)
        assert "Secretaria" not in result
        assert "Equipamentos de informática" in result

    def test_em_atendimento_necessidades(self):
        texto = (
            "Serviço de limpeza em atendimento às necessidades "
            "da Fundação de Amparo à Pesquisa"
        )
        result = _strip_org_context(texto)
        assert "Fundação" not in result
        assert "Serviço de limpeza" in result

    def test_visando_atender(self):
        texto = (
            "Combustível automotivo visando atender a frota da "
            "Secretaria de Segurança Pública do Estado"
        )
        result = _strip_org_context(texto)
        assert "Secretaria" not in result
        assert "Combustível automotivo" in result

    def test_de_interesse(self):
        texto = (
            "Construção de muro de contenção "
            "de interesse da Unidade Básica de Saúde do Bairro Centro"
        )
        result = _strip_org_context(texto)
        assert "Unidade" not in result
        assert "Saúde" not in result
        assert "Construção de muro" in result

    def test_pertencentes(self):
        texto = (
            "Manutenção de veículos pertencentes à frota da "
            "Secretaria Municipal de Administração"
        )
        result = _strip_org_context(texto)
        assert "Secretaria" not in result
        assert "Manutenção de veículos" in result

    def test_pertencente_singular(self):
        texto = (
            "Reforma de imóvel pertencente ao patrimônio da "
            "Prefeitura de São Paulo"
        )
        result = _strip_org_context(texto)
        assert "Prefeitura" not in result
        assert "Reforma de imóvel" in result

    def test_a_pedido(self):
        texto = (
            "Material odontológico a pedido da Secretaria de Saúde"
        )
        result = _strip_org_context(texto)
        assert "Secretaria" not in result
        assert "Material odontológico" in result

    def test_atraves_da_secretaria(self):
        texto = (
            "Contratação de serviço de telefonia "
            "através da Secretaria de Administração e Planejamento"
        )
        result = _strip_org_context(texto)
        assert "Secretaria" not in result
        assert "serviço de telefonia" in result

    def test_atraves_do_departamento(self):
        texto = (
            "Aquisição de passagens aéreas "
            "através do Departamento de Logística"
        )
        result = _strip_org_context(texto)
        assert "Departamento" not in result
        assert "passagens aéreas" in result

    def test_conforme_demanda(self):
        texto = (
            "Fornecimento de combustível conforme demanda da Diretoria de Transportes"
        )
        result = _strip_org_context(texto)
        assert "Diretoria" not in result
        assert "combustível" in result

    def test_destinado_a_secretaria(self):
        texto = (
            "Material de copa e cozinha destinado à Secretaria de Saúde do Estado"
        )
        result = _strip_org_context(texto)
        assert "Secretaria" not in result
        assert "Saúde" not in result
        assert "Material de copa e cozinha" in result

    def test_no_ambito(self):
        texto = (
            "Aquisição de notebooks no âmbito da Secretaria de Tecnologia da Informação"
        )
        result = _strip_org_context(texto)
        assert "Secretaria" not in result
        assert "notebooks" in result

    def test_no_ambito_normalized(self):
        """AC3: Test with normalized text (no accents)."""
        texto = (
            "Aquisicao de material de limpeza no ambito da Secretaria de Saude"
        )
        result = _strip_org_context(texto)
        assert "Secretaria" not in result
        assert "material de limpeza" in result

    def test_para_atender_without_accents(self):
        """AC3: Test accent-insensitive matching."""
        texto = (
            "Locacao de veiculos para atender as necessidades "
            "da Secretaria de Estado da Saude"
        )
        result = _strip_org_context(texto)
        assert "Secretaria" not in result
        assert "Locacao de veiculos" in result

    def test_multiple_clauses_takes_earliest(self):
        """When multiple patterns match, strip from the earliest match."""
        texto = (
            "Material de escritório de interesse do Instituto de Tecnologia "
            "para atender às necessidades da Diretoria"
        )
        result = _strip_org_context(texto)
        assert "Instituto" not in result
        assert "Material de escritório" in result


class TestStripOrgContextPCPPrefixes:
    """AC2: PCP source prefix stripping."""

    def test_pcp_prefix_brackets(self):
        texto = "[Portal de Compras Públicas] - Aquisição de uniformes escolares"
        result = _strip_org_context(texto)
        assert "Aquisição de uniformes escolares" in result
        assert "Portal" not in result

    def test_pcp_prefix_no_brackets(self):
        texto = "Portal de Compras Publicas - Material de escritório"
        result = _strip_org_context(texto)
        assert "Material de escritório" in result

    def test_pcp_abbreviation(self):
        texto = "[PCP] - Serviço de vigilância patrimonial"
        result = _strip_org_context(texto)
        assert "Serviço de vigilância" in result
        assert "PCP" not in result

    def test_pcp_prefix_with_org_context(self):
        """Combined: strip PCP prefix AND org context."""
        texto = (
            "[Portal de Compras Públicas] - Locação de veículos "
            "para atender às necessidades da Secretaria de Saúde"
        )
        result = _strip_org_context(texto)
        assert "Portal" not in result
        assert "Secretaria" not in result
        assert "Locação de veículos" in result


class TestStripOrgContextPreservation:
    """AC4: Original text preserved — only matching text is used for matching."""

    def test_no_match_returns_original(self):
        texto = "Aquisição de medicamentos hospitalares para UTI neonatal"
        result = _strip_org_context(texto)
        assert result == texto

    def test_empty_string(self):
        assert _strip_org_context("") == ""

    def test_none_like_empty(self):
        assert _strip_org_context("") == ""

    def test_short_text_unchanged(self):
        texto = "Uniformes escolares"
        result = _strip_org_context(texto)
        assert result == texto

    def test_legitimate_content_preserved(self):
        """Ensure 'serviços de secretaria' (clerical) is NOT stripped."""
        texto = "Contratação de serviços de secretaria e apoio administrativo"
        result = _strip_org_context(texto)
        assert "serviços de secretaria" in result


class TestStripOrgContextWithDetail:
    """Test the detail variant for logging/metrics."""

    def test_returns_removed_clause(self):
        texto = (
            "Material de escritório para atender às necessidades "
            "da Secretaria Municipal de Saúde"
        )
        stripped, removed = _strip_org_context_with_detail(texto)
        assert "Secretaria" not in stripped
        assert removed is not None
        assert "Secretaria" in removed or "atender" in removed

    def test_no_match_returns_none(self):
        texto = "Aquisição de medicamentos para UTI"
        stripped, removed = _strip_org_context_with_detail(texto)
        assert stripped == texto
        assert removed is None

    def test_empty_string(self):
        stripped, removed = _strip_org_context_with_detail("")
        assert stripped == ""
        assert removed is None


# ============================================================================
# AC17: Real production examples from Saúde sector (2026-02-28)
# ============================================================================


class TestRealProductionExamplesSaude:
    """All 7 examples from production must be handled correctly."""

    def test_locacao_veiculos_sesa(self):
        """Vehicle rental — irrelevant to health."""
        texto = (
            "Contratação de empresa especializada na prestação de serviços de "
            "locação de veículos tipo sedan e caminhonete pick-up, sem motorista, "
            "para atendimento às necessidades da Secretaria de Estado da Saúde - SESA"
        )
        result = _strip_org_context(texto)
        assert "Secretaria" not in result
        assert "Saúde" not in result
        assert "locação de veículos" in result

    def test_generos_alimenticios_secretaria_saude(self):
        """Food/cleaning — irrelevant to health."""
        texto = (
            "Aquisição de gêneros alimentícios e materiais de limpeza "
            "para atender às necessidades da Secretaria Municipal de Saúde"
        )
        result = _strip_org_context(texto)
        assert "Secretaria" not in result
        assert "Saúde" not in result
        assert "gêneros alimentícios" in result

    def test_equipamentos_informatica_consorcio_saude(self):
        """IT equipment — irrelevant to health."""
        texto = (
            "Aquisição de equipamentos de informática "
            "de interesse do Consórcio de Saúde do Vale do Rio"
        )
        result = _strip_org_context(texto)
        assert "Consórcio" not in result
        assert "Saúde" not in result
        assert "equipamentos de informática" in result

    def test_material_escritorio_secretaria_saude(self):
        """Office supplies — irrelevant to health."""
        texto = (
            "Material de escritório e papelaria "
            "para atender às necessidades da Secretaria Municipal de Saúde"
        )
        result = _strip_org_context(texto)
        assert "Secretaria" not in result

    def test_construcao_muro_unidade_saude(self):
        """Wall construction — irrelevant to health."""
        texto = (
            "Construção de muro de contenção na Unidade de Saúde "
            "pertencente ao patrimônio da Prefeitura Municipal"
        )
        result = _strip_org_context(texto)
        assert "Prefeitura" not in result

    def test_material_odontologico_ceo(self):
        """Dental materials — borderline but 'saúde' in org context should be stripped."""
        texto = (
            "Material odontológico para CEO a pedido da Secretaria de Saúde"
        )
        result = _strip_org_context(texto)
        assert "Secretaria" not in result
        assert "Material odontológico" in result

    def test_legitimate_health_procurement_passes(self):
        """AC19: Legitimate health procurement should NOT be stripped (no org clause)."""
        texto = "Aquisição de medicamentos para hospital municipal — lote de antibióticos e analgésicos"
        result = _strip_org_context(texto)
        assert result == texto
        assert "medicamentos" in result
        assert "hospital" in result


# ============================================================================
# Edge cases
# ============================================================================


class TestStripOrgContextEdgeCases:
    """Edge cases and regression guards."""

    def test_org_name_at_very_start(self):
        """If the entire text IS the org clause, should return empty or near-empty."""
        texto = "Para atender às necessidades da Secretaria de Saúde"
        result = _strip_org_context(texto)
        # Should be mostly empty since the entire text is an org clause
        assert "Secretaria" not in result

    def test_text_with_only_whitespace(self):
        result = _strip_org_context("   ")
        assert result == ""

    def test_unicode_characters(self):
        texto = (
            "Serviço de manutenção — para atendimento às necessidades "
            "da Fundação de Saúde Pública"
        )
        result = _strip_org_context(texto)
        assert "Fundação" not in result

    def test_multiple_sentences(self):
        texto = (
            "Aquisição de equipamentos médicos. "
            "Incluindo monitores multiparamétricos e ventiladores pulmonares. "
            "Para atender às necessidades da Secretaria de Saúde."
        )
        result = _strip_org_context(texto)
        assert "equipamentos médicos" in result
        assert "monitores" in result

    def test_very_long_text(self):
        """Test with long text to ensure performance is reasonable."""
        base = "Contratação de empresa para fornecimento de materiais diversos " * 10
        texto = base + "para atender às necessidades da Secretaria de Saúde do Estado"
        result = _strip_org_context(texto)
        assert "Secretaria" not in result
        assert len(result) < len(texto)

    def test_partial_match_not_stripped(self):
        """'atender' alone should NOT trigger stripping — needs full clause."""
        texto = "Contratação para atender demandas internas de uniformes"
        result = _strip_org_context(texto)
        # "para atender demandas internas" doesn't match the full pattern
        # because it's "demandas internas" not "demandas da/do/das"
        assert "uniformes" in result
