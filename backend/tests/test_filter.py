"""Unit tests for keyword matching engine (filter.py)."""

from datetime import datetime, timezone, timedelta
from filter import (
    normalize_text,
    match_keywords,
    filter_licitacao,
    filter_batch,
    remove_stopwords,
    filtrar_por_status,
    filtrar_por_modalidade,
    filtrar_por_valor,
    filtrar_por_esfera,
    filtrar_por_municipio,
    aplicar_todos_filtros,
    KEYWORDS_UNIFORMES,
    KEYWORDS_EXCLUSAO,
    STOPWORDS_PT,
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
            "Aquisição de uniformes escolares", KEYWORDS_UNIFORMES
        )
        assert matched is True
        assert "uniformes" in keywords

    def test_no_match(self):
        """Should return False when no keywords match."""
        matched, keywords = match_keywords(
            "Aquisição de software de gestão", KEYWORDS_UNIFORMES
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
            "Distribuição uniformemente espaçada", KEYWORDS_UNIFORMES
        )
        assert matched is False

        # "uniformização" should NOT match (partial word)
        matched, _ = match_keywords("Uniformização de processos", KEYWORDS_UNIFORMES)
        assert matched is False

    def test_exclusion_keywords_prevent_match(self):
        """Should return False if exclusion keywords found."""
        # Has "uniforme" but also has exclusion
        matched, keywords = match_keywords(
            "Uniformização de procedimento padrão",
            KEYWORDS_UNIFORMES,
            KEYWORDS_EXCLUSAO,
        )
        assert matched is False
        assert keywords == []

        # Another exclusion case
        matched, keywords = match_keywords(
            "Padrão uniforme de qualidade", KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO
        )
        assert matched is False
        assert keywords == []

    def test_multiple_keyword_matches(self):
        """Should return all matched keywords."""
        matched, keywords = match_keywords(
            "Fornecimento de jaleco e camiseta para hospital", KEYWORDS_UNIFORMES
        )
        assert matched is True
        assert "jaleco" in keywords
        assert "camiseta" in keywords
        assert len(keywords) >= 2

    def test_compound_keyword_matching(self):
        """Should match multi-word keywords."""
        matched, keywords = match_keywords(
            "Aquisição de uniforme escolar", KEYWORDS_UNIFORMES
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
            "Compra de uniformes", KEYWORDS_UNIFORMES, exclusions=None
        )
        assert matched is True
        assert len(keywords) > 0

    def test_real_world_procurement_examples(self):
        """Should correctly match real-world procurement descriptions."""
        # Valid uniform procurement
        test_cases_valid = [
            "Aquisição de uniformes escolares para alunos da rede municipal",
            "Fornecimento de jalecos para profissionais de saúde",
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
            "Confecção de fardamento militar",  # Military uniforms out of scope
        ]

        for caso in test_cases_invalid:
            matched, _ = match_keywords(caso, KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO)
            assert matched is False, f"Should NOT match: {caso}"

    def test_epi_keywords_match(self):
        """Should match EPI (Equipamento de Proteção Individual) procurement.

        Audit 2026-01-29: EPIs were the main source of false negatives.
        EPIs frequently include apparel items (jalecos, aventais, botas).
        """
        epi_cases = [
            "AQUISIÇÕES FUTURAS E PARCELADAS DE EQUIPAMENTOS DE PROTEÇÃO INDIVIDUAL - EPI",
            "Registro de preços para aquisição de EPIs para colaboradores",
            "REGISTRO DE PREÇOS PARA AQUISIÇÃO FUTURA E PARCELADA DE MATERIAIS DE EPI'S",
            "Aquisição de Materiais de Proteção Individual EPIS",
        ]
        for caso in epi_cases:
            matched, kw = match_keywords(caso, KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO)
            assert matched is True, f"Should match EPI case: {caso}"

    def test_real_world_exclusions_from_audit(self):
        """Should correctly exclude non-clothing items found in audit.

        Audit 2026-01-29: These real PNCP descriptions were correctly
        excluded or should be excluded.
        """
        exclusion_cases = [
            # confecção in non-clothing context (real from audit)
            "Contratação de serviço de confecção de carimbos, através do Sistema de Registro de Preços",
            "Contratação de Empresa Especializada para Confecção e Instalação de Cortinas Sob Medida",
            # roupa de cama / enxoval (preventive exclusion)
            "Aquisição de roupa de cama para unidades de saúde",
            "Prestação de serviços de lavanderia hospitalar com locação de enxoval hospitalar",
            # colete non-apparel
            "Aquisição de colete salva vidas para defesa civil",
            "Fornecimento de colete balístico para polícia militar",
        ]
        for caso in exclusion_cases:
            matched, _ = match_keywords(caso, KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO)
            assert matched is False, f"Should NOT match: {caso}"

    def test_real_world_approved_from_audit(self):
        """Should approve real procurement descriptions found in audit.

        Audit 2026-01-29: These are actual approved items from PNCP data.
        """
        approved_cases = [
            "Registro de Preços para aquisição de vestuário íntimo (infantil e adulto)",
            "Aquisição de Uniformes Escolares Infantis",
            "REGISTRO DE PREÇOS PARA EVENTUAL AQUISIÇÃO DE UNIFORMES ESPORTIVOS E ACESSÓRIOS PERSONALIZADOS",
        ]
        for caso in approved_cases:
            matched, _ = match_keywords(caso, KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO)
            assert matched is True, f"Should match: {caso}"


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


class TestFilterLicitacao:
    """Tests for filter_licitacao() function (sequential filtering)."""

    def test_rejects_uf_not_selected(self):
        """Should reject bid when UF is not in selected set."""
        licitacao = {
            "uf": "RJ",
            "valorTotalEstimado": 100_000.0,
            "objetoCompra": "Aquisição de uniformes escolares",
        }
        aprovada, motivo = filter_licitacao(licitacao, {"SP", "MG"})
        assert aprovada is False
        assert "UF 'RJ' não selecionada" in motivo

    def test_accepts_uf_in_selected_set(self):
        """Should accept bid when UF is in selected set."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        licitacao = {
            "uf": "SP",
            "valorTotalEstimado": 100_000.0,
            "objetoCompra": "Aquisição de uniformes escolares",
            "dataAberturaProposta": future_date,
        }
        aprovada, motivo = filter_licitacao(licitacao, {"SP", "RJ"})
        assert aprovada is True
        assert motivo is None

    def test_accepts_valor_none(self):
        """Should accept bid even when valorTotalEstimado is missing (value filter removed 2026-02-05)."""
        licitacao = {"uf": "SP", "objetoCompra": "Uniformes"}
        aprovada, motivo = filter_licitacao(licitacao, {"SP"})
        assert aprovada is True
        assert motivo is None

    def test_accepts_valor_below_previous_min(self):
        """Should accept bid with any value (value filter removed 2026-02-05)."""
        licitacao = {
            "uf": "SP",
            "valorTotalEstimado": 100.0,  # Very small value - now accepted
            "objetoCompra": "Uniformes escolares",
        }
        aprovada, motivo = filter_licitacao(licitacao, {"SP"})
        assert aprovada is True
        assert motivo is None

    def test_accepts_valor_above_previous_max(self):
        """Should accept bid with any value (value filter removed 2026-02-05)."""
        licitacao = {
            "uf": "SP",
            "valorTotalEstimado": 100_000_000.0,  # Very large value - now accepted
            "objetoCompra": "Uniformes escolares",
        }
        aprovada, motivo = filter_licitacao(licitacao, {"SP"})
        assert aprovada is True
        assert motivo is None

    def test_accepts_valor_within_any_range(self):
        """Should accept bid with any value (value filter removed 2026-02-05)."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        licitacao = {
            "uf": "SP",
            "valorTotalEstimado": 150_000.0,
            "objetoCompra": "Uniformes escolares",
            "dataAberturaProposta": future_date,
        }
        aprovada, motivo = filter_licitacao(licitacao, {"SP"})
        assert aprovada is True
        assert motivo is None

    def test_accepts_any_valor_after_filter_removal(self):
        """Should accept any value since filter was removed (2026-02-05)."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        licitacao = {
            "uf": "SP",
            "valorTotalEstimado": 75_000.0,
            "objetoCompra": "Uniformes",
            "dataAberturaProposta": future_date,
        }
        # Value filter parameters no longer exist
        aprovada, motivo = filter_licitacao(licitacao, {"SP"})
        assert aprovada is True
        assert motivo is None

    def test_rejects_missing_keywords(self):
        """Should reject bid without uniform keywords."""
        licitacao = {
            "uf": "SP",
            "valorTotalEstimado": 100_000.0,
            "objetoCompra": "Aquisição de notebooks e impressoras",
        }
        aprovada, motivo = filter_licitacao(licitacao, {"SP"})
        assert aprovada is False
        assert "keywords" in motivo.lower() or "setor" in motivo.lower()

    def test_accepts_with_uniform_keywords(self):
        """Should accept bid with uniform keywords."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        licitacao = {
            "uf": "SP",
            "valorTotalEstimado": 100_000.0,
            "objetoCompra": "Aquisição de uniformes escolares",
            "dataAberturaProposta": future_date,
        }
        aprovada, motivo = filter_licitacao(licitacao, {"SP"})
        assert aprovada is True
        assert motivo is None

    def test_accepts_past_deadline(self):
        """
        Should ACCEPT bid even when dataAberturaProposta is in the past.

        Rationale (Investigation 2026-01-28):
        - dataAberturaProposta is the proposal OPENING date, not the deadline
        - Historical bids are valid for analysis, planning, and recurring opportunity identification
        - Filtering by deadline should use dataFimReceberPropostas when available
        - Previous behavior rejected 100% of historical searches, causing zero results

        Reference: docs/investigations/2026-01-28-zero-results-analysis.md
        """
        past_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        licitacao = {
            "uf": "SP",
            "valorTotalEstimado": 100_000.0,
            "objetoCompra": "Uniformes",
            "dataAberturaProposta": past_date,
        }
        aprovada, motivo = filter_licitacao(licitacao, {"SP"})
        assert aprovada is True  # Now accepts historical bids
        assert motivo is None

    def test_accepts_future_deadline(self):
        """Should accept bid when deadline is in the future."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        licitacao = {
            "uf": "SP",
            "valorTotalEstimado": 100_000.0,
            "objetoCompra": "Uniformes escolares",
            "dataAberturaProposta": future_date,
        }
        aprovada, motivo = filter_licitacao(licitacao, {"SP"})
        assert aprovada is True
        assert motivo is None

    def test_accepts_missing_deadline(self):
        """Should accept bid when dataAberturaProposta is missing (skip filter)."""
        licitacao = {
            "uf": "SP",
            "valorTotalEstimado": 100_000.0,
            "objetoCompra": "Uniformes",
        }
        aprovada, motivo = filter_licitacao(licitacao, {"SP"})
        assert aprovada is True  # Missing date doesn't fail the filter
        assert motivo is None

    def test_accepts_malformed_deadline(self):
        """Should accept bid when date is malformed (skip filter gracefully)."""
        licitacao = {
            "uf": "SP",
            "valorTotalEstimado": 100_000.0,
            "objetoCompra": "Uniformes",
            "dataAberturaProposta": "invalid-date-format",
        }
        aprovada, motivo = filter_licitacao(licitacao, {"SP"})
        assert aprovada is True  # Malformed date doesn't fail the filter
        assert motivo is None

    def test_filter_order_is_fail_fast(self):
        """Should stop at first filter failure (fail-fast optimization)."""
        # UF filter should fail before value check
        licitacao_wrong_uf = {
            "uf": "RJ",
            "valorTotalEstimado": 30_000.0,  # Also wrong value
            "objetoCompra": "Software",  # Also wrong keywords
        }
        aprovada, motivo = filter_licitacao(licitacao_wrong_uf, {"SP"})
        assert aprovada is False
        # Should fail on UF (first check), not mention value or keywords
        assert "UF" in motivo
        assert "RJ" in motivo

    def test_historical_search_accepts_all_valid_bids(self):
        """
        Should accept ALL valid bids in historical searches regardless of date.

        This test simulates the common use case of searching for bids from the
        past week/month. ALL bids matching UF, value range, and keywords should
        be accepted, even if their dataAberturaProposta is in the past.

        Reference: Investigation 2026-01-28 - Zero results bug fix
        """
        # Simulate historical search: bids from last 7 days (all dates in past)
        historical_bids = [
            {
                "uf": "SP",
                "valorTotalEstimado": 150_000.0,
                "objetoCompra": "Aquisição de uniformes escolares",
                "dataAberturaProposta": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            },
            {
                "uf": "RJ",
                "valorTotalEstimado": 75_000.0,
                "objetoCompra": "Pregão eletrônico para aquisição de jalecos hospitalares",
                "dataAberturaProposta": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
            },
            {
                "uf": "MG",
                "valorTotalEstimado": 200_000.0,
                "objetoCompra": "Contratação de empresa para fornecimento de fardamento",
                "dataAberturaProposta": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
            },
        ]

        # All should be accepted
        for i, bid in enumerate(historical_bids):
            aprovada, motivo = filter_licitacao(bid, {"SP", "RJ", "MG"})
            assert aprovada is True, f"Bid {i+1} should be accepted, but got: {motivo}"
            assert motivo is None

    def test_batch_filter_accepts_historical_bids(self):
        """
        Batch filter should accept historical bids and track stats correctly.

        After the deadline filter removal (Investigation 2026-01-28), the
        rejeitadas_prazo counter should always be 0.
        """
        historical_bids = [
            {
                "uf": "SP",
                "valorTotalEstimado": 100_000.0,
                "objetoCompra": "Uniformes escolares",
                "dataAberturaProposta": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
            },
            {
                "uf": "SP",
                "valorTotalEstimado": 200_000.0,
                "objetoCompra": "Jalecos médicos",
                "dataAberturaProposta": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
            },
        ]

        aprovadas, stats = filter_batch(historical_bids, {"SP"})

        assert len(aprovadas) == 2, "Both historical bids should be accepted"
        assert stats["aprovadas"] == 2
        assert stats["rejeitadas_prazo"] == 0, "No bids should be rejected due to deadline"

    def test_real_world_valid_bid(self):
        """Should accept realistic valid procurement bid."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
        licitacao = {
            "uf": "SP",
            "valorTotalEstimado": 287_500.0,
            "objetoCompra": "PREGÃO ELETRÔNICO - Aquisição de uniformes escolares "
            "para alunos da rede municipal de ensino",
            "dataAberturaProposta": future_date,
            "codigoCompra": "12345678",
            "nomeOrgao": "Prefeitura Municipal de São Paulo",
        }
        aprovada, motivo = filter_licitacao(licitacao, {"SP", "RJ", "MG"})
        assert aprovada is True
        assert motivo is None

    def test_handles_z_suffix_in_iso_datetime(self):
        """Should correctly parse ISO datetime with 'Z' suffix."""
        future_date = datetime.now(timezone.utc) + timedelta(days=30)
        future_date_z = future_date.strftime("%Y-%m-%dT%H:%M:%SZ")  # Z format

        licitacao = {
            "uf": "SP",
            "valorTotalEstimado": 100_000.0,
            "objetoCompra": "Uniformes",
            "dataAberturaProposta": future_date_z,
        }
        aprovada, motivo = filter_licitacao(licitacao, {"SP"})
        assert aprovada is True
        assert motivo is None


class TestFilterBatch:
    """Tests for filter_batch() function (batch filtering with statistics)."""

    def test_empty_batch_returns_empty_list(self):
        """Should handle empty batch gracefully."""
        aprovadas, stats = filter_batch([], {"SP"})
        assert aprovadas == []
        assert stats["total"] == 0
        assert stats["aprovadas"] == 0

    def test_single_approved_bid(self):
        """Should correctly filter single approved bid."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        licitacoes = [
            {
                "uf": "SP",
                "valorTotalEstimado": 100_000.0,
                "objetoCompra": "Uniformes escolares",
                "dataAberturaProposta": future_date,
            }
        ]
        aprovadas, stats = filter_batch(licitacoes, {"SP"})

        assert len(aprovadas) == 1
        assert stats["total"] == 1
        assert stats["aprovadas"] == 1
        assert stats["rejeitadas_uf"] == 0

    def test_batch_with_mixed_results(self):
        """Should correctly separate approved and rejected bids."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        licitacoes = [
            # Approved
            {
                "uf": "SP",
                "valorTotalEstimado": 100_000.0,
                "objetoCompra": "Uniformes",
                "dataAberturaProposta": future_date,
            },
            # Rejected: wrong UF
            {
                "uf": "RJ",
                "valorTotalEstimado": 100_000.0,
                "objetoCompra": "Uniformes",
                "dataAberturaProposta": future_date,
            },
            # Approved
            {
                "uf": "MG",
                "valorTotalEstimado": 150_000.0,
                "objetoCompra": "Jalecos hospitalares",
                "dataAberturaProposta": future_date,
            },
        ]
        aprovadas, stats = filter_batch(licitacoes, {"SP", "MG"})

        assert len(aprovadas) == 2
        assert stats["total"] == 3
        assert stats["aprovadas"] == 2
        assert stats["rejeitadas_uf"] == 1

    def test_rejection_statistics_accuracy(self):
        """
        Should accurately count rejections by category.

        Note (2026-02-05): Value filter was removed, so low/high values are now accepted.
        Note (2026-01-28): Prazo filter was removed, so past dates are approved.
        """
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        past_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()

        licitacoes = [
            # Rejected: UF
            {"uf": "RJ", "valorTotalEstimado": 100_000.0, "objetoCompra": "Uniformes"},
            # Approved: Low value no longer rejected (value filter removed 2026-02-05)
            {"uf": "SP", "valorTotalEstimado": 30_000.0, "objetoCompra": "Uniformes"},
            # Rejected: Keywords
            {"uf": "SP", "valorTotalEstimado": 100_000.0, "objetoCompra": "Notebooks"},
            # Approved (past date - deadline filter removed)
            {
                "uf": "SP",
                "valorTotalEstimado": 100_000.0,
                "objetoCompra": "Uniformes",
                "dataAberturaProposta": past_date,
            },
            # Approved (future date)
            {
                "uf": "SP",
                "valorTotalEstimado": 100_000.0,
                "objetoCompra": "Uniformes",
                "dataAberturaProposta": future_date,
            },
        ]

        aprovadas, stats = filter_batch(licitacoes, {"SP"})

        # 3 approved: low value (now OK), past date, future date
        assert len(aprovadas) == 3
        assert stats["total"] == 5
        assert stats["aprovadas"] == 3
        assert stats["rejeitadas_uf"] == 1
        assert stats["rejeitadas_keyword"] == 1
        assert stats["rejeitadas_prazo"] == 0  # No deadline rejections
        assert stats["rejeitadas_outros"] == 0

    def test_all_statistics_keys_present(self):
        """Should return all expected statistics keys (value filter removed 2026-02-05)."""
        aprovadas, stats = filter_batch([], {"SP"})

        required_keys = {
            "total",
            "aprovadas",
            "rejeitadas_uf",
            "rejeitadas_keyword",
            "rejeitadas_prazo",
            "rejeitadas_outros",
        }
        assert set(stats.keys()) == required_keys

    def test_batch_accepts_all_values_after_filter_removal(self):
        """Should accept all values since value filter was removed (2026-02-05)."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        licitacoes = [
            # Any value is now accepted
            {
                "uf": "SP",
                "valorTotalEstimado": 100_000.0,
                "objetoCompra": "Uniformes",
                "dataAberturaProposta": future_date,
            },
            # Low value - now accepted
            {
                "uf": "SP",
                "valorTotalEstimado": 60_000.0,
                "objetoCompra": "Uniformes",
                "dataAberturaProposta": future_date,
            },
            # High value - now accepted
            {
                "uf": "SP",
                "valorTotalEstimado": 150_000.0,
                "objetoCompra": "Uniformes",
                "dataAberturaProposta": future_date,
            },
        ]

        aprovadas, stats = filter_batch(licitacoes, {"SP"})

        # All 3 should be approved - no value filtering
        assert len(aprovadas) == 3
        assert stats["aprovadas"] == 3

    def test_preserves_original_bid_structure(self):
        """Should return approved bids with all original fields intact."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        original_bid = {
            "uf": "SP",
            "valorTotalEstimado": 100_000.0,
            "objetoCompra": "Uniformes escolares",
            "dataAberturaProposta": future_date,
            "codigoCompra": "ABC123",
            "nomeOrgao": "Prefeitura XYZ",
            "municipio": "São Paulo",
        }

        aprovadas, _ = filter_batch([original_bid], {"SP"})

        assert len(aprovadas) == 1
        assert aprovadas[0] == original_bid
        assert aprovadas[0]["codigoCompra"] == "ABC123"
        assert aprovadas[0]["municipio"] == "São Paulo"

    def test_large_batch_performance(self):
        """Should handle large batches efficiently."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

        # Create 1000 bids
        licitacoes = [
            {
                "uf": "SP",
                "valorTotalEstimado": 100_000.0 + (i * 1000),
                "objetoCompra": f"Uniformes lote {i}",
                "dataAberturaProposta": future_date,
                "id": i,
            }
            for i in range(1000)
        ]

        aprovadas, stats = filter_batch(licitacoes, {"SP"})

        # All should be approved (all meet criteria)
        assert len(aprovadas) == 1000
        assert stats["total"] == 1000
        assert stats["aprovadas"] == 1000


class TestRemoveStopwords:
    """Tests for Portuguese stopword removal from custom search terms."""

    def test_removes_common_prepositions(self):
        assert remove_stopwords(["serviço", "de", "limpeza"]) == ["serviço", "limpeza"]

    def test_removes_articles(self):
        assert remove_stopwords(["aquisição", "de", "os", "uniformes"]) == ["aquisição", "uniformes"]

    def test_removes_conjunctions(self):
        assert remove_stopwords(["mesa", "e", "cadeira"]) == ["mesa", "cadeira"]

    def test_keeps_meaningful_terms(self):
        terms = ["jaleco", "avental", "uniforme"]
        assert remove_stopwords(terms) == terms

    def test_handles_accented_stopwords(self):
        # "após" normalizes to "apos" which is in STOPWORDS_PT
        assert remove_stopwords(["após", "licitação"]) == ["licitação"]

    def test_all_stopwords_returns_empty(self):
        """If ALL terms are stopwords, return empty list so caller falls back to sector keywords."""
        terms = ["de", "para", "com"]
        assert remove_stopwords(terms) == []

    def test_empty_list(self):
        assert remove_stopwords([]) == []

    def test_single_meaningful_term(self):
        assert remove_stopwords(["uniforme"]) == ["uniforme"]

    def test_single_stopword_returns_empty(self):
        assert remove_stopwords(["de"]) == []

    def test_mixed_case_stopwords(self):
        # Terms should already be lowercased, but test robustness
        assert remove_stopwords(["serviço", "de", "limpeza"]) == ["serviço", "limpeza"]

    def test_stopwords_set_contains_essentials(self):
        """Verify the most critical stopwords are in the set."""
        essential = {"de", "do", "da", "dos", "das", "para", "com", "em",
                     "no", "na", "e", "ou", "o", "a", "os", "as", "um", "uma"}
        assert essential.issubset(STOPWORDS_PT)

    def test_real_world_query_servico_de_limpeza(self):
        result = remove_stopwords(["serviço", "de", "limpeza", "para", "o", "prédio"])
        assert result == ["serviço", "limpeza", "prédio"]

    def test_real_world_query_material_de_escritorio(self):
        result = remove_stopwords(["material", "de", "escritório", "e", "papelaria"])
        assert result == ["material", "escritório", "papelaria"]


# =============================================================================
# NEW FILTER FUNCTION TESTS (P0/P1)
# =============================================================================


class TestFiltrarPorStatus:
    """Tests for filtrar_por_status() function."""

    def test_status_todos_returns_all(self):
        """Status 'todos' should return all bids."""
        bids = [
            {"situacaoCompra": "Recebendo propostas"},
            {"situacaoCompra": "Encerrada"},
        ]
        result = filtrar_por_status(bids, "todos")
        assert len(result) == 2

    def test_status_none_returns_all(self):
        """None status should return all bids."""
        bids = [
            {"situacaoCompra": "Recebendo propostas"},
            {"situacaoCompra": "Encerrada"},
        ]
        result = filtrar_por_status(bids, None)
        assert len(result) == 2

    def test_status_recebendo_proposta(self):
        """Should filter bids receiving proposals."""
        bids = [
            {"situacaoCompra": "Recebendo propostas"},
            {"situacaoCompra": "Aberta"},
            {"situacaoCompra": "Encerrada"},
            {"situacaoCompra": "Em julgamento"},
        ]
        result = filtrar_por_status(bids, "recebendo_proposta")
        assert len(result) == 2
        assert all(
            "recebendo" in b["situacaoCompra"].lower() or
            "aberta" in b["situacaoCompra"].lower()
            for b in result
        )

    def test_status_em_julgamento(self):
        """Should filter bids under evaluation."""
        bids = [
            {"situacaoCompra": "Recebendo propostas"},
            {"situacaoCompra": "Em julgamento"},
            {"situacaoCompra": "Propostas encerradas"},
            {"situacaoCompra": "Encerrada"},
        ]
        result = filtrar_por_status(bids, "em_julgamento")
        assert len(result) == 2

    def test_status_encerrada(self):
        """Should filter closed/finalized bids."""
        bids = [
            {"situacaoCompra": "Recebendo propostas"},
            {"situacaoCompra": "Encerrada"},
            {"situacaoCompra": "Homologada"},
            {"situacaoCompra": "Adjudicada"},
            {"situacaoCompra": "Anulada"},
        ]
        result = filtrar_por_status(bids, "encerrada")
        assert len(result) == 4

    def test_status_case_insensitive(self):
        """Should handle case variations."""
        bids = [
            {"situacaoCompra": "RECEBENDO PROPOSTAS"},
            {"situacaoCompra": "recebendo propostas"},
            {"situacaoCompra": "Recebendo Propostas"},
        ]
        result = filtrar_por_status(bids, "recebendo_proposta")
        assert len(result) == 3

    def test_uses_alternative_status_fields(self):
        """Should check situacao and statusCompra as fallback."""
        bids = [
            {"situacao": "Recebendo propostas"},
            {"statusCompra": "Aberta"},
            {"outroCampo": "Recebendo propostas"},  # Should NOT match
        ]
        result = filtrar_por_status(bids, "recebendo_proposta")
        assert len(result) == 2

    def test_unknown_status_returns_all(self):
        """Unknown status should return all bids (graceful fallback)."""
        bids = [
            {"situacaoCompra": "Recebendo propostas"},
            {"situacaoCompra": "Encerrada"},
        ]
        result = filtrar_por_status(bids, "status_invalido")
        assert len(result) == 2


class TestFiltrarPorModalidade:
    """Tests for filtrar_por_modalidade() function."""

    def test_modalidade_none_returns_all(self):
        """None modalidades should return all bids."""
        bids = [
            {"modalidadeId": 1},
            {"modalidadeId": 6},
        ]
        result = filtrar_por_modalidade(bids, None)
        assert len(result) == 2

    def test_modalidade_empty_list_returns_all(self):
        """Empty list should return all bids."""
        bids = [
            {"modalidadeId": 1},
            {"modalidadeId": 6},
        ]
        result = filtrar_por_modalidade(bids, [])
        assert len(result) == 2

    def test_single_modalidade_filter(self):
        """Should filter by single modalidade."""
        bids = [
            {"modalidadeId": 1, "objeto": "Pregão"},
            {"modalidadeId": 6, "objeto": "Dispensa"},
            {"modalidadeId": 3, "objeto": "Concorrência"},
        ]
        result = filtrar_por_modalidade(bids, [1])
        assert len(result) == 1
        assert result[0]["modalidadeId"] == 1

    def test_multiple_modalidades_filter(self):
        """Should filter by multiple modalidades."""
        bids = [
            {"modalidadeId": 1, "objeto": "Pregão Eletrônico"},
            {"modalidadeId": 2, "objeto": "Pregão Presencial"},
            {"modalidadeId": 6, "objeto": "Dispensa"},
            {"modalidadeId": 3, "objeto": "Concorrência"},
        ]
        result = filtrar_por_modalidade(bids, [1, 2, 6])
        assert len(result) == 3

    def test_uses_alternative_modalidade_fields(self):
        """Should check codigoModalidadeContratacao as fallback."""
        bids = [
            {"codigoModalidadeContratacao": 1},
            {"modalidade_id": 6},
        ]
        result = filtrar_por_modalidade(bids, [1, 6])
        assert len(result) == 2

    def test_handles_string_modalidade_id(self):
        """Should handle modalidadeId as string."""
        bids = [
            {"modalidadeId": "1"},
            {"modalidadeId": "6"},
        ]
        result = filtrar_por_modalidade(bids, [1])
        assert len(result) == 1


class TestFiltrarPorValor:
    """Tests for filtrar_por_valor() function."""

    def test_no_limits_returns_all(self):
        """No min/max should return all bids."""
        bids = [
            {"valorTotalEstimado": 50000},
            {"valorTotalEstimado": 200000},
            {"valorTotalEstimado": 1000000},
        ]
        result = filtrar_por_valor(bids, None, None)
        assert len(result) == 3

    def test_min_only_filter(self):
        """Should filter with only minimum value."""
        bids = [
            {"valorTotalEstimado": 50000},
            {"valorTotalEstimado": 100000},
            {"valorTotalEstimado": 200000},
        ]
        result = filtrar_por_valor(bids, valor_min=100000)
        assert len(result) == 2
        assert all(b["valorTotalEstimado"] >= 100000 for b in result)

    def test_max_only_filter(self):
        """Should filter with only maximum value."""
        bids = [
            {"valorTotalEstimado": 50000},
            {"valorTotalEstimado": 100000},
            {"valorTotalEstimado": 200000},
        ]
        result = filtrar_por_valor(bids, valor_max=100000)
        assert len(result) == 2
        assert all(b["valorTotalEstimado"] <= 100000 for b in result)

    def test_range_filter(self):
        """Should filter with both min and max."""
        bids = [
            {"valorTotalEstimado": 50000},
            {"valorTotalEstimado": 100000},
            {"valorTotalEstimado": 200000},
            {"valorTotalEstimado": 500000},
        ]
        result = filtrar_por_valor(bids, valor_min=75000, valor_max=300000)
        assert len(result) == 2
        assert all(75000 <= b["valorTotalEstimado"] <= 300000 for b in result)

    def test_uses_alternative_value_fields(self):
        """Should check valorEstimado as fallback."""
        bids = [
            {"valorEstimado": 100000},
            {"valor": 200000},
        ]
        result = filtrar_por_valor(bids, valor_min=50000)
        assert len(result) == 2

    def test_handles_string_value_brazilian_format(self):
        """Should handle Brazilian number format (1.000,00)."""
        bids = [
            {"valorTotalEstimado": "100.000,00"},  # 100000
            {"valorTotalEstimado": "200.000,00"},  # 200000
        ]
        result = filtrar_por_valor(bids, valor_min=150000)
        assert len(result) == 1

    def test_handles_zero_and_none_values(self):
        """Should handle zero and missing values."""
        bids = [
            {"valorTotalEstimado": 0},
            {"valorTotalEstimado": None},
            {},  # Missing field
            {"valorTotalEstimado": 100000},
        ]
        result = filtrar_por_valor(bids, valor_min=50000)
        assert len(result) == 1


class TestFiltrarPorEsfera:
    """Tests for filtrar_por_esfera() function."""

    def test_esfera_none_returns_all(self):
        """None esferas should return all bids."""
        bids = [
            {"esferaId": "F"},
            {"esferaId": "M"},
        ]
        result = filtrar_por_esfera(bids, None)
        assert len(result) == 2

    def test_federal_filter(self):
        """Should filter federal bids."""
        bids = [
            {"esferaId": "F", "orgao": "Ministério da Saúde"},
            {"esferaId": "E", "orgao": "Governo do Estado"},
            {"esferaId": "M", "orgao": "Prefeitura"},
        ]
        result = filtrar_por_esfera(bids, ["F"])
        assert len(result) == 1
        assert result[0]["esferaId"] == "F"

    def test_municipal_filter(self):
        """Should filter municipal bids."""
        bids = [
            {"esferaId": "F"},
            {"esferaId": "E"},
            {"esferaId": "M"},
        ]
        result = filtrar_por_esfera(bids, ["M"])
        assert len(result) == 1

    def test_multiple_esferas_filter(self):
        """Should filter by multiple esferas."""
        bids = [
            {"esferaId": "F"},
            {"esferaId": "E"},
            {"esferaId": "M"},
        ]
        result = filtrar_por_esfera(bids, ["F", "M"])
        assert len(result) == 2

    def test_fallback_by_orgao_name(self):
        """Should use orgao name as fallback when esferaId missing."""
        bids = [
            {"nomeOrgao": "Ministério da Educação"},  # Federal
            {"nomeOrgao": "Prefeitura Municipal de São Paulo"},  # Municipal
            {"nomeOrgao": "Secretaria de Estado de Saúde"},  # Estadual
        ]
        result = filtrar_por_esfera(bids, ["F"])
        assert len(result) == 1

    def test_case_insensitive_esfera_id(self):
        """Should handle case variations in esferaId."""
        bids = [
            {"esferaId": "f"},
            {"esferaId": "F"},
            {"esfera": "f"},
        ]
        result = filtrar_por_esfera(bids, ["F"])
        assert len(result) == 3


class TestFiltrarPorMunicipio:
    """Tests for filtrar_por_municipio() function."""

    def test_municipio_none_returns_all(self):
        """None municipios should return all bids."""
        bids = [
            {"codigoMunicipioIbge": "3550308"},
            {"codigoMunicipioIbge": "3304557"},
        ]
        result = filtrar_por_municipio(bids, None)
        assert len(result) == 2

    def test_single_municipio_filter(self):
        """Should filter by single municipio code."""
        bids = [
            {"codigoMunicipioIbge": "3550308", "municipio": "São Paulo"},
            {"codigoMunicipioIbge": "3304557", "municipio": "Rio de Janeiro"},
        ]
        result = filtrar_por_municipio(bids, ["3550308"])
        assert len(result) == 1
        assert result[0]["municipio"] == "São Paulo"

    def test_multiple_municipios_filter(self):
        """Should filter by multiple municipio codes."""
        bids = [
            {"codigoMunicipioIbge": "3550308"},
            {"codigoMunicipioIbge": "3304557"},
            {"codigoMunicipioIbge": "3106200"},
        ]
        result = filtrar_por_municipio(bids, ["3550308", "3304557"])
        assert len(result) == 2

    def test_uses_alternative_municipio_fields(self):
        """Should check municipioId and ibge as fallback."""
        bids = [
            {"municipioId": "3550308"},
            {"codigoMunicipio": "3304557"},
            {"ibge": "3106200"},
        ]
        result = filtrar_por_municipio(bids, ["3550308", "3304557", "3106200"])
        assert len(result) == 3

    def test_handles_integer_codes(self):
        """Should handle integer municipio codes."""
        bids = [
            {"codigoMunicipioIbge": 3550308},
        ]
        result = filtrar_por_municipio(bids, ["3550308"])
        assert len(result) == 1


class TestFiltrarPorStatusEdgeCases:
    """Additional edge case tests for filtrar_por_status()."""

    def test_status_empty_string_returns_all(self):
        """Empty string status should return all bids (same as 'todos')."""
        bids = [
            {"situacaoCompra": "Recebendo propostas"},
            {"situacaoCompra": "Encerrada"},
        ]
        result = filtrar_por_status(bids, "")
        assert len(result) == 2

    def test_bid_with_all_status_fields_none(self):
        """Bid with no status fields should not match any filter."""
        bids = [
            {},  # No situacaoCompra, situacao, or statusCompra
            {"situacaoCompra": "Recebendo propostas"},
        ]
        result = filtrar_por_status(bids, "recebendo_proposta")
        assert len(result) == 1

    def test_bid_with_none_status_value(self):
        """Bid with None as status value should be handled."""
        bids = [
            {"situacaoCompra": None},
            {"situacaoCompra": "Recebendo propostas"},
        ]
        result = filtrar_por_status(bids, "recebendo_proposta")
        assert len(result) == 1

    def test_empty_list_returns_empty(self):
        """Empty bid list should return empty list."""
        result = filtrar_por_status([], "recebendo_proposta")
        assert result == []

    def test_status_with_extra_whitespace(self):
        """Status with extra whitespace should still match."""
        bids = [
            {"situacaoCompra": "  Recebendo propostas  "},
        ]
        # Note: The current implementation doesn't strip, so we test as-is
        result = filtrar_por_status(bids, "recebendo_proposta")
        # Should match because 'recebendo' is found in the lowercased string
        assert len(result) == 1


class TestFiltrarPorModalidadeEdgeCases:
    """Additional edge case tests for filtrar_por_modalidade()."""

    def test_modalidade_none_value_in_bid(self):
        """Bid with None modalidadeId should be filtered out."""
        bids = [
            {"modalidadeId": None},
            {"modalidadeId": 1},
        ]
        result = filtrar_por_modalidade(bids, [1])
        assert len(result) == 1
        assert result[0]["modalidadeId"] == 1

    def test_modalidade_invalid_string_value(self):
        """Bid with non-numeric string modalidadeId should be filtered out."""
        bids = [
            {"modalidadeId": "invalid"},
            {"modalidadeId": "1"},
        ]
        result = filtrar_por_modalidade(bids, [1])
        assert len(result) == 1

    def test_modalidade_float_conversion(self):
        """Bid with float modalidadeId should be handled."""
        bids = [
            {"modalidadeId": 1.0},
            {"modalidadeId": 2.5},  # Should convert to 2
        ]
        result = filtrar_por_modalidade(bids, [1, 2])
        assert len(result) == 2

    def test_modalidade_empty_bid(self):
        """Bid with no modalidade fields should be filtered out."""
        bids = [
            {},
            {"modalidadeId": 1},
        ]
        result = filtrar_por_modalidade(bids, [1])
        assert len(result) == 1


class TestFiltrarPorValorEdgeCases:
    """Additional edge case tests for filtrar_por_valor()."""

    def test_value_exactly_at_min(self):
        """Value exactly at minimum should be included."""
        bids = [{"valorTotalEstimado": 100000}]
        result = filtrar_por_valor(bids, valor_min=100000)
        assert len(result) == 1

    def test_value_exactly_at_max(self):
        """Value exactly at maximum should be included."""
        bids = [{"valorTotalEstimado": 100000}]
        result = filtrar_por_valor(bids, valor_max=100000)
        assert len(result) == 1

    def test_value_negative_number(self):
        """Negative value should be handled (filtered out by min)."""
        bids = [
            {"valorTotalEstimado": -1000},
            {"valorTotalEstimado": 100000},
        ]
        result = filtrar_por_valor(bids, valor_min=0)
        assert len(result) == 1

    def test_value_very_large_number(self):
        """Very large value should be handled."""
        bids = [
            {"valorTotalEstimado": 999_999_999_999.99},
        ]
        result = filtrar_por_valor(bids, valor_max=1_000_000_000_000)
        assert len(result) == 1

    def test_value_list_type_returns_zero(self):
        """Non-numeric type (list) should be treated as 0."""
        bids = [
            {"valorTotalEstimado": [100000]},  # Invalid type
            {"valorTotalEstimado": 100000},
        ]
        result = filtrar_por_valor(bids, valor_min=50000)
        assert len(result) == 1

    def test_value_dict_type_returns_zero(self):
        """Non-numeric type (dict) should be treated as 0."""
        bids = [
            {"valorTotalEstimado": {"amount": 100000}},  # Invalid type
            {"valorTotalEstimado": 100000},
        ]
        result = filtrar_por_valor(bids, valor_min=50000)
        assert len(result) == 1

    def test_value_empty_string(self):
        """Empty string value should be treated as 0."""
        bids = [
            {"valorTotalEstimado": ""},
            {"valorTotalEstimado": 100000},
        ]
        result = filtrar_por_valor(bids, valor_min=50000)
        assert len(result) == 1


class TestFiltrarPorEsferaEdgeCases:
    """Additional edge case tests for filtrar_por_esfera()."""

    def test_esfera_empty_list_returns_all(self):
        """Empty esferas list should return all bids."""
        bids = [
            {"esferaId": "F"},
            {"esferaId": "M"},
        ]
        result = filtrar_por_esfera(bids, [])
        assert len(result) == 2

    def test_esfera_lowercase_input(self):
        """Lowercase esfera input should work."""
        bids = [
            {"esferaId": "F"},
            {"esferaId": "M"},
        ]
        result = filtrar_por_esfera(bids, ["f", "m"])
        assert len(result) == 2

    def test_esfera_bid_with_no_fields(self):
        """Bid with no esfera or orgao fields should be excluded."""
        bids = [
            {},  # No esferaId, esfera, tipoOrgao, or nomeOrgao
            {"esferaId": "M"},
        ]
        result = filtrar_por_esfera(bids, ["M"])
        assert len(result) == 1

    def test_esfera_estadual_detection_by_orgao(self):
        """Should detect estadual from orgao name."""
        bids = [
            {"nomeOrgao": "Secretaria de Estado de Educação"},
            {"nomeOrgao": "Prefeitura Municipal"},
        ]
        result = filtrar_por_esfera(bids, ["E"])
        assert len(result) == 1


class TestFiltrarPorMunicipioEdgeCases:
    """Additional edge case tests for filtrar_por_municipio()."""

    def test_municipio_empty_list_returns_all(self):
        """Empty municipios list should return all bids."""
        bids = [
            {"codigoMunicipioIbge": "3550308"},
            {"codigoMunicipioIbge": "3304557"},
        ]
        result = filtrar_por_municipio(bids, [])
        assert len(result) == 2

    def test_municipio_partial_code_no_match(self):
        """Partial IBGE code should not match."""
        bids = [
            {"codigoMunicipioIbge": "3550308"},
        ]
        result = filtrar_por_municipio(bids, ["35503"])  # Partial
        assert len(result) == 0

    def test_municipio_bid_with_no_fields(self):
        """Bid with no municipio fields should be excluded."""
        bids = [
            {},  # No municipio fields
            {"codigoMunicipioIbge": "3550308"},
        ]
        result = filtrar_por_municipio(bids, ["3550308"])
        assert len(result) == 1

    def test_municipio_with_whitespace_in_code(self):
        """Whitespace in municipio code should be stripped."""
        bids = [
            {"codigoMunicipioIbge": " 3550308 "},
        ]
        result = filtrar_por_municipio(bids, ["3550308"])
        assert len(result) == 1


class TestAplicarTodosFiltros:
    """Tests for aplicar_todos_filtros() orchestrator function."""

    def test_minimal_filter_uf_only(self):
        """Should filter by UF when only UF specified."""
        bids = [
            {"uf": "SP", "objetoCompra": "Uniformes escolares"},
            {"uf": "RJ", "objetoCompra": "Uniformes escolares"},
        ]
        result, stats = aplicar_todos_filtros(bids, {"SP"})
        assert len(result) == 1
        assert stats["rejeitadas_uf"] == 1

    def test_combined_filters(self):
        """Should apply all filters in sequence."""
        bids = [
            # Should pass all filters
            {
                "uf": "SP",
                "situacaoCompra": "Recebendo propostas",
                "esferaId": "M",
                "modalidadeId": 1,
                "codigoMunicipioIbge": "3550308",
                "valorTotalEstimado": 150000,
                "objetoCompra": "Aquisição de uniformes escolares",
            },
            # Rejected by UF
            {
                "uf": "RJ",
                "situacaoCompra": "Recebendo propostas",
                "esferaId": "M",
                "modalidadeId": 1,
                "codigoMunicipioIbge": "3550308",
                "valorTotalEstimado": 150000,
                "objetoCompra": "Aquisição de uniformes escolares",
            },
            # Rejected by modalidade
            {
                "uf": "SP",
                "situacaoCompra": "Recebendo propostas",
                "esferaId": "M",
                "modalidadeId": 3,  # Concorrência, not in filter
                "codigoMunicipioIbge": "3550308",
                "valorTotalEstimado": 150000,
                "objetoCompra": "Aquisição de uniformes escolares",
            },
            # Rejected by value
            {
                "uf": "SP",
                "situacaoCompra": "Recebendo propostas",
                "esferaId": "M",
                "modalidadeId": 1,
                "codigoMunicipioIbge": "3550308",
                "valorTotalEstimado": 50000,  # Below minimum
                "objetoCompra": "Aquisição de uniformes escolares",
            },
            # Rejected by keyword
            {
                "uf": "SP",
                "situacaoCompra": "Recebendo propostas",
                "esferaId": "M",
                "modalidadeId": 1,
                "codigoMunicipioIbge": "3550308",
                "valorTotalEstimado": 150000,
                "objetoCompra": "Aquisição de notebooks",  # No uniform keywords
            },
        ]

        result, stats = aplicar_todos_filtros(
            bids,
            ufs_selecionadas={"SP"},
            status="recebendo_proposta",
            modalidades=[1, 2],
            valor_min=100000,
            valor_max=500000,
            esferas=["M"],
            municipios=["3550308"],
        )

        assert len(result) == 1
        assert stats["total"] == 5
        assert stats["aprovadas"] == 1
        assert stats["rejeitadas_uf"] == 1
        assert stats["rejeitadas_modalidade"] == 1
        assert stats["rejeitadas_valor"] == 1
        assert stats["rejeitadas_keyword"] == 1

    def test_returns_complete_statistics(self):
        """Should return all statistics keys."""
        result, stats = aplicar_todos_filtros([], {"SP"})

        required_keys = {
            "total",
            "aprovadas",
            "rejeitadas_uf",
            "rejeitadas_status",
            "rejeitadas_esfera",
            "rejeitadas_modalidade",
            "rejeitadas_municipio",
            "rejeitadas_valor",
            "rejeitadas_keyword",
            "rejeitadas_outros",
        }
        assert required_keys.issubset(set(stats.keys()))

    def test_fail_fast_order(self):
        """Should reject early to optimize performance."""
        # Bid that would fail UF filter
        bids = [
            {
                "uf": "RJ",  # Will fail first filter (UF)
                "situacaoCompra": "Encerrada",  # Would fail status
                "esferaId": "F",  # Would fail esfera
                "modalidadeId": 99,  # Would fail modalidade
                "valorTotalEstimado": 1,  # Would fail value
                "objetoCompra": "Notebooks",  # Would fail keyword
            }
        ]

        result, stats = aplicar_todos_filtros(
            bids,
            ufs_selecionadas={"SP"},
            status="recebendo_proposta",
            esferas=["M"],
            modalidades=[1],
            valor_min=100000,
        )

        # Should only count UF rejection (fail-fast)
        assert stats["rejeitadas_uf"] == 1
        assert stats["rejeitadas_status"] == 0
        assert stats["rejeitadas_esfera"] == 0
        assert stats["rejeitadas_modalidade"] == 0
        assert stats["rejeitadas_valor"] == 0

    def test_no_optional_filters(self):
        """Should work with only required UF filter."""
        bids = [
            {"uf": "SP", "objetoCompra": "Uniformes escolares"},
            {"uf": "RJ", "objetoCompra": "Uniformes escolares"},
        ]
        result, stats = aplicar_todos_filtros(
            bids,
            ufs_selecionadas={"SP", "RJ"},
        )
        assert len(result) == 2

    def test_empty_input(self):
        """Should handle empty input gracefully."""
        result, stats = aplicar_todos_filtros([], {"SP"})
        assert result == []
        assert stats["total"] == 0
        assert stats["aprovadas"] == 0

    def test_preserves_bid_structure(self):
        """Should preserve all original fields in approved bids."""
        original_bid = {
            "uf": "SP",
            "objetoCompra": "Uniformes escolares",
            "customField": "custom value",
            "nestedObject": {"key": "value"},
        }
        result, _ = aplicar_todos_filtros([original_bid], {"SP"})
        assert len(result) == 1
        assert result[0]["customField"] == "custom value"
        assert result[0]["nestedObject"]["key"] == "value"

    def test_multiple_filters_all_pass(self):
        """Bid passing all filters should be approved."""
        bid = {
            "uf": "SP",
            "situacaoCompra": "Recebendo propostas",
            "esferaId": "M",
            "modalidadeId": 1,
            "codigoMunicipioIbge": "3550308",
            "valorTotalEstimado": 150000,
            "objetoCompra": "Aquisição de uniformes escolares",
        }
        result, stats = aplicar_todos_filtros(
            [bid],
            ufs_selecionadas={"SP"},
            status="recebendo_proposta",
            modalidades=[1],
            valor_min=100000,
            valor_max=200000,
            esferas=["M"],
            municipios=["3550308"],
        )
        assert len(result) == 1
        assert stats["aprovadas"] == 1

    def test_custom_keywords_override_defaults(self):
        """Custom keywords should override default KEYWORDS_UNIFORMES."""
        bid = {
            "uf": "SP",
            "objetoCompra": "Aquisição de software de gestão",  # No uniform keywords
        }
        # Should fail with default keywords
        result1, _ = aplicar_todos_filtros([bid], {"SP"})
        assert len(result1) == 0

        # Should pass with custom keywords
        result2, _ = aplicar_todos_filtros(
            [bid], {"SP"}, keywords={"software", "gestao"}
        )
        assert len(result2) == 1

    def test_custom_exclusions_override_defaults(self):
        """Custom exclusions should override default KEYWORDS_EXCLUSAO."""
        bid = {
            "uf": "SP",
            "objetoCompra": "Aquisição de uniformes para militares",
        }
        # Should fail with default exclusions (militar is excluded)
        result1, _ = aplicar_todos_filtros([bid], {"SP"})
        assert len(result1) == 0

        # Should pass with empty exclusions
        result2, _ = aplicar_todos_filtros([bid], {"SP"}, exclusions=set())
        assert len(result2) == 1

    def test_all_filters_applied_in_sequence(self):
        """All filters should be applied in fail-fast sequence."""
        bids = [
            # Fails UF
            {"uf": "RJ", "objetoCompra": "Uniformes"},
            # Fails status
            {
                "uf": "SP",
                "situacaoCompra": "Encerrada",
                "objetoCompra": "Uniformes",
            },
            # Fails esfera
            {
                "uf": "SP",
                "situacaoCompra": "Recebendo propostas",
                "esferaId": "F",
                "objetoCompra": "Uniformes",
            },
            # Fails modalidade
            {
                "uf": "SP",
                "situacaoCompra": "Recebendo propostas",
                "esferaId": "M",
                "modalidadeId": 9,
                "objetoCompra": "Uniformes",
            },
            # Fails municipio
            {
                "uf": "SP",
                "situacaoCompra": "Recebendo propostas",
                "esferaId": "M",
                "modalidadeId": 1,
                "codigoMunicipioIbge": "9999999",
                "objetoCompra": "Uniformes",
            },
            # Fails value
            {
                "uf": "SP",
                "situacaoCompra": "Recebendo propostas",
                "esferaId": "M",
                "modalidadeId": 1,
                "codigoMunicipioIbge": "3550308",
                "valorTotalEstimado": 10,
                "objetoCompra": "Uniformes",
            },
            # Fails keyword
            {
                "uf": "SP",
                "situacaoCompra": "Recebendo propostas",
                "esferaId": "M",
                "modalidadeId": 1,
                "codigoMunicipioIbge": "3550308",
                "valorTotalEstimado": 100000,
                "objetoCompra": "Notebooks",
            },
            # PASSES all
            {
                "uf": "SP",
                "situacaoCompra": "Recebendo propostas",
                "esferaId": "M",
                "modalidadeId": 1,
                "codigoMunicipioIbge": "3550308",
                "valorTotalEstimado": 100000,
                "objetoCompra": "Uniformes escolares",
            },
        ]

        result, stats = aplicar_todos_filtros(
            bids,
            ufs_selecionadas={"SP"},
            status="recebendo_proposta",
            modalidades=[1],
            valor_min=50000,
            valor_max=200000,
            esferas=["M"],
            municipios=["3550308"],
        )

        assert len(result) == 1
        assert stats["total"] == 8
        assert stats["aprovadas"] == 1
        assert stats["rejeitadas_uf"] == 1
        assert stats["rejeitadas_status"] == 1
        assert stats["rejeitadas_esfera"] == 1
        assert stats["rejeitadas_modalidade"] == 1
        assert stats["rejeitadas_municipio"] == 1
        assert stats["rejeitadas_valor"] == 1
        assert stats["rejeitadas_keyword"] == 1

    def test_status_todos_skips_status_filter(self):
        """Status 'todos' should not filter by status."""
        bids = [
            {"uf": "SP", "situacaoCompra": "Encerrada", "objetoCompra": "Uniformes"},
            {"uf": "SP", "situacaoCompra": "Recebendo propostas", "objetoCompra": "Uniformes"},
        ]
        result, stats = aplicar_todos_filtros(bids, {"SP"}, status="todos")
        assert len(result) == 2
        assert stats["rejeitadas_status"] == 0
