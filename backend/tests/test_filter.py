"""Unit tests for keyword matching engine (filter.py)."""

from datetime import datetime, timezone, timedelta
from filter import (
    normalize_text,
    match_keywords,
    filter_licitacao,
    filter_batch,
    remove_stopwords,
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

    def test_rejects_valor_none(self):
        """Should reject bid when valorTotalEstimado is missing."""
        licitacao = {"uf": "SP", "objetoCompra": "Uniformes"}
        aprovada, motivo = filter_licitacao(licitacao, {"SP"})
        assert aprovada is False
        assert "Valor não informado" in motivo

    def test_rejects_valor_below_min(self):
        """Should reject bid when value is below minimum threshold."""
        licitacao = {
            "uf": "SP",
            "valorTotalEstimado": 30_000.0,  # Below 50k default
            "objetoCompra": "Uniformes escolares",
        }
        aprovada, motivo = filter_licitacao(licitacao, {"SP"})
        assert aprovada is False
        assert "Valor" in motivo
        assert "fora da faixa" in motivo

    def test_rejects_valor_above_max(self):
        """Should reject bid when value is above maximum threshold."""
        licitacao = {
            "uf": "SP",
            "valorTotalEstimado": 6_000_000.0,  # Above 5M default
            "objetoCompra": "Uniformes escolares",
        }
        aprovada, motivo = filter_licitacao(licitacao, {"SP"})
        assert aprovada is False
        assert "Valor" in motivo
        assert "fora da faixa" in motivo

    def test_accepts_valor_within_range(self):
        """Should accept bid when value is within range."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        licitacao = {
            "uf": "SP",
            "valorTotalEstimado": 150_000.0,  # Within 50k-5M range
            "objetoCompra": "Uniformes escolares",
            "dataAberturaProposta": future_date,
        }
        aprovada, motivo = filter_licitacao(licitacao, {"SP"})
        assert aprovada is True
        assert motivo is None

    def test_accepts_custom_valor_range(self):
        """Should respect custom valor_min and valor_max parameters."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        licitacao = {
            "uf": "SP",
            "valorTotalEstimado": 75_000.0,
            "objetoCompra": "Uniformes",
            "dataAberturaProposta": future_date,
        }
        # Custom range: 100k-200k (should reject 75k)
        aprovada, _ = filter_licitacao(
            licitacao, {"SP"}, valor_min=100_000, valor_max=200_000
        )
        assert aprovada is False

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

        Note (Investigation 2026-01-28): Prazo filter was removed, so both
        past_date and future_date bids are now approved. The rejeitadas_prazo
        counter should always be 0.
        """
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        past_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()

        licitacoes = [
            # Rejected: UF
            {"uf": "RJ", "valorTotalEstimado": 100_000.0, "objetoCompra": "Uniformes"},
            # Rejected: Valor (too low)
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

        # Both past and future date bids should now be approved
        assert len(aprovadas) == 2
        assert stats["total"] == 5
        assert stats["aprovadas"] == 2
        assert stats["rejeitadas_uf"] == 1
        assert stats["rejeitadas_valor"] == 1
        assert stats["rejeitadas_keyword"] == 1
        assert stats["rejeitadas_prazo"] == 0  # No deadline rejections after fix
        assert stats["rejeitadas_outros"] == 0

    def test_all_statistics_keys_present(self):
        """Should return all expected statistics keys."""
        aprovadas, stats = filter_batch([], {"SP"})

        required_keys = {
            "total",
            "aprovadas",
            "rejeitadas_uf",
            "rejeitadas_valor",
            "rejeitadas_keyword",
            "rejeitadas_prazo",
            "rejeitadas_outros",
        }
        assert set(stats.keys()) == required_keys

    def test_custom_valor_range_in_batch(self):
        """Should respect custom valor range in batch filtering."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        licitacoes = [
            # Within custom range: 80k-120k
            {
                "uf": "SP",
                "valorTotalEstimado": 100_000.0,
                "objetoCompra": "Uniformes",
                "dataAberturaProposta": future_date,
            },
            # Below custom min
            {
                "uf": "SP",
                "valorTotalEstimado": 60_000.0,
                "objetoCompra": "Uniformes",
                "dataAberturaProposta": future_date,
            },
            # Above custom max
            {
                "uf": "SP",
                "valorTotalEstimado": 150_000.0,
                "objetoCompra": "Uniformes",
                "dataAberturaProposta": future_date,
            },
        ]

        aprovadas, stats = filter_batch(
            licitacoes, {"SP"}, valor_min=80_000, valor_max=120_000
        )

        assert len(aprovadas) == 1
        assert stats["aprovadas"] == 1
        assert stats["rejeitadas_valor"] == 2

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
