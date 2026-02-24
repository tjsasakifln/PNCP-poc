"""
STORY-267 AC5: LLM Term-Aware Search Tests

Tests verifying that when custom_terms are present and TERM_SEARCH_LLM_AWARE=true,
all three LLM call sites in the filter pipeline use the term-aware prompt
(setor_name=None, termos_busca=custom_terms) instead of the sector-name prompt.

Coverage:
- AC5 Test 1: zero-match path uses term prompt (not sector name)
- AC5 Test 2: Camada 3A (arbiter gray-zone) uses term prompt
- AC5 Test 3: Camada 3B (FLUXO 2 recovery) uses term prompt
- AC1 (unit): _build_term_search_prompt has no sector name in output
- AC1 (unit): _build_term_search_prompt includes all user terms
"""

import os
from unittest.mock import MagicMock, Mock, patch, call, ANY

import pytest

from filter import aplicar_todos_filtros
from llm_arbiter import _build_term_search_prompt, clear_cache


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture(autouse=True)
def setup_env():
    """Set up a clean LLM environment for each test."""
    os.environ["LLM_ARBITER_ENABLED"] = "true"
    os.environ["OPENAI_API_KEY"] = "test-key"
    # Ensure feature flags are OFF by default (tests opt-in via patches)
    os.environ["TERM_SEARCH_LLM_AWARE"] = "false"
    os.environ["TERM_SEARCH_SYNONYMS"] = "false"
    clear_cache()
    yield
    clear_cache()
    os.environ.pop("TERM_SEARCH_LLM_AWARE", None)
    os.environ.pop("TERM_SEARCH_SYNONYMS", None)


def _make_llm_response(is_primary: bool = True, confidence: int = 75) -> dict:
    """Create a structured LLM mock response dict."""
    return {
        "is_primary": is_primary,
        "confidence": confidence,
        "evidence": ["termo buscado"] if is_primary else [],
        "rejection_reason": None if is_primary else "not relevant to search terms",
        "needs_more_data": False,
    }


def _make_zero_match_bid(
    codigo: str = "TM-001",
    objeto: str = (
        "Prestação de serviços de consultoria organizacional e planejamento "
        "estratégico para reestruturação dos processos internos da administração "
        "municipal, incluindo análise de fluxos e entrega de relatórios técnicos"
    ),
    valor: float = 150_000.0,
    uf: str = "SP",
) -> dict:
    """Create a bid that will NOT match any vestuario/generic keywords.

    The texto is long and generic — zero keyword density against the xyz set
    used in the zero-match tests.
    """
    return {
        "codigoCompra": codigo,
        "objetoCompra": objeto,
        "valorTotalEstimado": valor,
        "uf": uf,
        "modalidadeNome": "Pregão Eletrônico",
        "codigoModalidadeContratacao": 6,
        "nomeOrgao": "Prefeitura Municipal de São Paulo",
        "dataPublicacaoPncp": "2026-02-01",
        "dataAberturaProposta": "2026-02-05",
        "dataEncerramentoProposta": "2026-12-31T10:00:00Z",
    }


def _make_gray_zone_bid(
    index: int = 0,
    uf: str = "SP",
) -> dict:
    """Create a bid that lands in the 1-5% keyword density gray zone.

    Contains one keyword (uniformes) in a long text → ~2% density.
    This causes it to bypass alta-densidade path and enter Camada 3A (LLM arbiter).
    """
    return {
        "codigoCompra": f"GZ-{index:03d}",
        "objetoCompra": (
            f"Registro de preço para eventual aquisição de bens diversos "
            f"destinados ao órgão público federal, incluindo itens de "
            f"expediente e uniformes para colaboradores da unidade "
            f"número {index}, com entrega programada ao longo do exercício "
            f"financeiro vigente, pelo período de doze meses, com "
            f"possibilidade de prorrogação, em parcelas trimestrais, "
            f"tudo conforme condições do edital e seus respectivos anexos"
        ),
        "valorTotalEstimado": 120_000.0,
        "uf": uf,
        "modalidadeNome": "Pregão Eletrônico",
        "codigoModalidadeContratacao": 6,
        "nomeOrgao": "Órgão Federal",
        "dataPublicacaoPncp": "2026-02-01",
        "dataAberturaProposta": "2026-02-05",
        "dataEncerramentoProposta": "2026-12-31T10:00:00Z",
    }


# ==============================================================================
# Tests: _build_term_search_prompt (unit, AC1)
# ==============================================================================


class TestBuildTermSearchPrompt:
    """Unit tests for _build_term_search_prompt — verifies AC1 prompt shape."""

    def test_build_term_search_prompt_no_sector_name(self):
        """AC1: Term-aware prompt must NOT mention any sector name.

        The prompt is setor-agnostic — it only talks about what the user searched.
        """
        prompt = _build_term_search_prompt(
            termos=["guarda-pó", "avental"],
            objeto_truncated="Fornecimento de EPIs para colaboradores industriais",
            valor=80_000.0,
        )

        # Must NOT mention any of the 15 sector names
        sector_names = [
            "Vestuário", "Alimentos", "Hardware", "Mobiliário", "Papelaria",
            "Engenharia", "Software", "Facilities", "Saúde", "Vigilância",
            "Transporte", "Conservação Predial", "Rodoviária", "Elétricos",
            "Hidráulicos",
        ]
        prompt_lower = prompt.lower()
        for name in sector_names:
            assert name.lower() not in prompt_lower, (
                f"Prompt must not mention sector name '{name}', but it does.\n"
                f"Prompt:\n{prompt}"
            )

    def test_build_term_search_prompt_includes_all_terms(self):
        """AC1: All user terms must appear in the prompt."""
        custom_terms = ["guarda-pó", "jaleco", "avental"]

        prompt = _build_term_search_prompt(
            termos=custom_terms,
            objeto_truncated="Aquisição de vestimentas de proteção",
            valor=50_000.0,
        )

        for term in custom_terms:
            assert term in prompt, (
                f"Term '{term}' missing from term-aware prompt.\nPrompt:\n{prompt}"
            )

    def test_build_term_search_prompt_includes_valor(self):
        """Prompt must display the contract value."""
        prompt = _build_term_search_prompt(
            termos=["equipamento"],
            objeto_truncated="Aquisição de equipamentos hospitalares",
            valor=200_000.0,
        )
        # Value should appear in some form
        assert "200" in prompt, f"Valor not found in prompt:\n{prompt}"

    def test_build_term_search_prompt_asks_about_relevance(self):
        """Prompt must ask about relevance to the search terms (not sector)."""
        prompt = _build_term_search_prompt(
            termos=["microscópio"],
            objeto_truncated="Aquisição de microscópios ópticos para laboratório",
            valor=30_000.0,
        )
        # Should ask if contract is relevant for someone searching these terms
        assert "RELEVANTE" in prompt.upper() or "relevante" in prompt.lower()
        assert "termos" in prompt.lower() or "buscados" in prompt.lower()

    @pytest.mark.parametrize("terms,objeto", [
        (["notebook", "laptop"], "Fornecimento de computadores portáteis"),
        (["saneamento", "tratamento de água"], "Obra de infraestrutura hídrica"),
        (["vigilância", "monitoramento"], "Serviço de segurança eletrônica"),
    ])
    def test_build_term_search_prompt_various_terms(self, terms, objeto):
        """Parametrized: prompt always includes all provided terms."""
        prompt = _build_term_search_prompt(
            termos=terms,
            objeto_truncated=objeto,
            valor=100_000.0,
        )
        for term in terms:
            assert term in prompt, (
                f"Term '{term}' missing from prompt for objeto='{objeto}'"
            )


# ==============================================================================
# Tests: Zero-match path — AC5 Test 1
# ==============================================================================


class TestZeroMatchUsesTermPrompt:
    """AC5 Test 1: Zero-match path calls LLM with setor_name=None, termos_busca=custom_terms."""

    @patch("llm_arbiter.classify_contract_primary_match")
    @patch("config.get_feature_flag")
    @patch("config.LLM_ZERO_MATCH_ENABLED", True)
    def test_zero_match_uses_term_prompt_when_custom_terms(
        self, mock_get_feature_flag, mock_classify
    ):
        """When custom_terms is non-empty and TERM_SEARCH_LLM_AWARE=true,
        the zero-match path calls classify_contract_primary_match with
        setor_name=None and termos_busca=custom_terms.
        """
        # TERM_SEARCH_LLM_AWARE=True, all other flags off
        def feature_flag_side_effect(name, **kwargs):
            if name == "TERM_SEARCH_LLM_AWARE":
                return True
            return False

        mock_get_feature_flag.side_effect = feature_flag_side_effect
        mock_classify.return_value = _make_llm_response(is_primary=True)

        custom_terms = ["guarda-pó", "jaleco"]

        # Bids with NO matching keywords (using a keyword set that won't match)
        bids = [
            _make_zero_match_bid(codigo="ZM-001"),
            _make_zero_match_bid(
                codigo="ZM-002",
                objeto=(
                    "Fornecimento de materiais de limpeza e higienização para "
                    "manutenção das instalações do órgão público municipal durante "
                    "o período de doze meses, conforme especificações do edital"
                ),
            ),
        ]

        # Use a keyword set that does NOT match the bid objects
        # so bids land in the zero-match pool
        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            keywords={"xyz_nonexistent_keyword_abc"},
            exclusions=set(),
            setor="vestuario",
            custom_terms=custom_terms,
        )

        # The LLM must have been called
        assert mock_classify.call_count >= 1, (
            "classify_contract_primary_match was not called for zero-match bids"
        )

        # Every call must use setor_name=None and termos_busca=custom_terms
        for i, call_args in enumerate(mock_classify.call_args_list):
            kwargs = call_args.kwargs if call_args.kwargs else {}
            # Also handle positional args
            if not kwargs and call_args.args:
                # positional: objeto, valor, setor_name, termos_busca, ...
                # But the function uses keyword args in the filter code
                pass
            setor_name_passed = kwargs.get("setor_name")
            termos_passed = kwargs.get("termos_busca")

            assert setor_name_passed is None, (
                f"Call {i}: expected setor_name=None but got setor_name={setor_name_passed!r}. "
                f"Term-aware zero-match must not pass sector name to LLM."
            )
            assert termos_passed == custom_terms, (
                f"Call {i}: expected termos_busca={custom_terms!r} but got {termos_passed!r}. "
                f"Zero-match term-aware path must pass custom_terms to LLM."
            )

    @patch("llm_arbiter.classify_contract_primary_match")
    @patch("config.get_feature_flag")
    @patch("config.LLM_ZERO_MATCH_ENABLED", True)
    def test_zero_match_uses_sector_prompt_when_flag_off(
        self, mock_get_feature_flag, mock_classify
    ):
        """Sanity check: when TERM_SEARCH_LLM_AWARE=false, sector name is used (not terms)."""
        def feature_flag_side_effect(name, **kwargs):
            return False  # All flags off

        mock_get_feature_flag.side_effect = feature_flag_side_effect
        mock_classify.return_value = _make_llm_response(is_primary=True)

        custom_terms = ["guarda-pó", "jaleco"]
        bids = [_make_zero_match_bid()]

        aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            keywords={"xyz_nonexistent_keyword_abc"},
            exclusions=set(),
            setor="vestuario",
            custom_terms=custom_terms,
        )

        if mock_classify.call_count >= 1:
            for call_args in mock_classify.call_args_list:
                kwargs = call_args.kwargs if call_args.kwargs else {}
                setor_name_passed = kwargs.get("setor_name")
                termos_passed = kwargs.get("termos_busca")
                # When flag is off, sector name should be passed (not custom_terms)
                assert setor_name_passed is not None or termos_passed != custom_terms, (
                    "When TERM_SEARCH_LLM_AWARE=false, sector name must be used, not custom_terms"
                )

    @patch("llm_arbiter.classify_contract_primary_match")
    @patch("config.get_feature_flag")
    @patch("config.LLM_ZERO_MATCH_ENABLED", True)
    def test_zero_match_no_custom_terms_uses_sector_prompt(
        self, mock_get_feature_flag, mock_classify
    ):
        """When custom_terms is None/empty, zero-match uses sector-based prompt even if flag=true."""
        def feature_flag_side_effect(name, **kwargs):
            if name == "TERM_SEARCH_LLM_AWARE":
                return True
            return False

        mock_get_feature_flag.side_effect = feature_flag_side_effect
        mock_classify.return_value = _make_llm_response(is_primary=True)

        bids = [_make_zero_match_bid()]

        aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            keywords={"xyz_nonexistent_keyword_abc"},
            exclusions=set(),
            setor="vestuario",
            custom_terms=None,  # No custom terms
        )

        if mock_classify.call_count >= 1:
            for call_args in mock_classify.call_args_list:
                kwargs = call_args.kwargs if call_args.kwargs else {}
                setor_name_passed = kwargs.get("setor_name")
                # Without custom_terms, sector name must be present
                assert setor_name_passed is not None, (
                    "Without custom_terms, zero-match must use sector name"
                )


# ==============================================================================
# Tests: Camada 3A (arbiter gray-zone) — AC5 Test 2
# ==============================================================================


class TestArbiterUsesTermPrompt:
    """AC5 Test 2: Camada 3A LLM Arbiter uses term prompt when custom_terms + flag=true."""

    @patch("llm_arbiter.classify_contract_primary_match")
    @patch("config.get_feature_flag")
    def test_arbiter_uses_term_prompt_when_custom_terms(
        self, mock_get_feature_flag, mock_classify
    ):
        """When custom_terms is non-empty and TERM_SEARCH_LLM_AWARE=true,
        Camada 3A calls classify_contract_primary_match with
        setor_name=None and termos_busca=custom_terms.
        """
        def feature_flag_side_effect(name, **kwargs):
            if name == "TERM_SEARCH_LLM_AWARE":
                return True
            # Disable sector ceiling, proximity, etc. to avoid noise
            return False

        mock_get_feature_flag.side_effect = feature_flag_side_effect
        mock_classify.return_value = _make_llm_response(is_primary=True)

        custom_terms = ["equipamento médico", "material hospitalar"]

        # Gray zone bid: has ONE keyword match in a long text → density ~2%
        # We pass keywords that match one word in the objeto to land in gray zone
        bids = [_make_gray_zone_bid(0), _make_gray_zone_bid(1)]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
            custom_terms=custom_terms,
        )

        # LLM arbiter must have been called (gray zone triggers Camada 3A)
        assert mock_classify.call_count >= 1, (
            "classify_contract_primary_match was not called. "
            "Gray-zone bids should trigger Camada 3A."
        )

        # All arbiter calls: setor_name=None, termos_busca=custom_terms
        for i, call_args in enumerate(mock_classify.call_args_list):
            kwargs = call_args.kwargs if call_args.kwargs else {}
            setor_name_passed = kwargs.get("setor_name")
            termos_passed = kwargs.get("termos_busca")

            assert setor_name_passed is None, (
                f"Camada 3A call {i}: expected setor_name=None "
                f"but got setor_name={setor_name_passed!r}. "
                f"Term-aware arbiter must not pass sector name."
            )
            assert termos_passed == custom_terms, (
                f"Camada 3A call {i}: expected termos_busca={custom_terms!r} "
                f"but got {termos_passed!r}."
            )

    @patch("llm_arbiter.classify_contract_primary_match")
    @patch("config.get_feature_flag")
    def test_arbiter_uses_term_prompt_multiple_bids(
        self, mock_get_feature_flag, mock_classify
    ):
        """All gray-zone bids get the term-aware prompt (not just the first one)."""
        def feature_flag_side_effect(name, **kwargs):
            return name == "TERM_SEARCH_LLM_AWARE"

        mock_get_feature_flag.side_effect = feature_flag_side_effect
        mock_classify.return_value = _make_llm_response(is_primary=True)

        custom_terms = ["sensor", "automação industrial"]
        bids = [_make_gray_zone_bid(i) for i in range(4)]

        aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
            custom_terms=custom_terms,
        )

        # Every LLM call should use term-aware mode
        for i, call_args in enumerate(mock_classify.call_args_list):
            kwargs = call_args.kwargs if call_args.kwargs else {}
            assert kwargs.get("setor_name") is None, (
                f"Call {i} used sector name — expected None for term-aware mode"
            )
            assert kwargs.get("termos_busca") == custom_terms, (
                f"Call {i} used wrong terms: {kwargs.get('termos_busca')!r}"
            )

    @patch("llm_arbiter.classify_contract_primary_match")
    @patch("config.get_feature_flag")
    def test_arbiter_uses_sector_prompt_without_custom_terms(
        self, mock_get_feature_flag, mock_classify
    ):
        """Sanity: without custom_terms, Camada 3A uses sector-based prompt."""
        def feature_flag_side_effect(name, **kwargs):
            return name == "TERM_SEARCH_LLM_AWARE"

        mock_get_feature_flag.side_effect = feature_flag_side_effect
        mock_classify.return_value = _make_llm_response(is_primary=True)

        bids = [_make_gray_zone_bid(0)]

        aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
            custom_terms=None,  # No custom terms
        )

        if mock_classify.call_count >= 1:
            for call_args in mock_classify.call_args_list:
                kwargs = call_args.kwargs if call_args.kwargs else {}
                setor_name_passed = kwargs.get("setor_name")
                # Without custom_terms, must use sector name
                assert setor_name_passed is not None, (
                    "Without custom_terms, Camada 3A must use sector name"
                )


# ==============================================================================
# Tests: Camada 3B (FLUXO 2 recovery) — AC5 Test 3
# ==============================================================================


class TestRecoveryUsesTermPrompt:
    """AC5 Test 3: FLUXO 2 Camada 3B recovery uses term prompt when custom_terms + flag=true."""

    @patch("llm_arbiter.classify_contract_recovery")
    @patch("synonyms.find_term_synonym_matches")
    @patch("config.get_feature_flag")
    @patch("config.LLM_ZERO_MATCH_ENABLED", False)
    def test_recovery_uses_term_prompt_when_custom_terms(
        self,
        mock_get_feature_flag,
        mock_find_term_synonyms,
        mock_recovery,
    ):
        """When custom_terms is non-empty and TERM_SEARCH_LLM_AWARE=true,
        Camada 3B recovery calls classify_contract_recovery with
        termos_busca=custom_terms (not setor_name).
        """
        def feature_flag_side_effect(name, **kwargs):
            if name in ("TERM_SEARCH_LLM_AWARE", "TERM_SEARCH_SYNONYMS"):
                return True
            return False

        mock_get_feature_flag.side_effect = feature_flag_side_effect

        # Synonym match returns EXACTLY 1 match → ambiguous → goes to Camada 3B
        mock_find_term_synonyms.return_value = [("guarda-pó", "avental")]
        mock_recovery.return_value = True

        custom_terms = ["guarda-pó", "jaleco"]

        # Bid rejected by keywords (no keyword match) but has synonym near-miss
        bid = {
            "codigoCompra": "REC-001",
            "objetoCompra": (
                "Fornecimento de avental para uso em laboratório e área industrial "
                "com certificação de qualidade e entrega parcelada mensalmente"
            ),
            "valorTotalEstimado": 80_000.0,
            "uf": "SP",
            "modalidadeNome": "Pregão Eletrônico",
            "codigoModalidadeContratacao": 6,
            "nomeOrgao": "Instituto de Pesquisa",
            "dataPublicacaoPncp": "2026-02-01",
            "dataAberturaProposta": "2026-02-05",
            "dataEncerramentoProposta": "2026-12-31T10:00:00Z",
        }

        # Use a keyword set that does NOT match "avental" so bid lands in recovery pool
        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=[bid],
            ufs_selecionadas={"SP"},
            keywords={"xyz_nonexistent_keyword_abc"},
            exclusions=set(),
            setor=None,  # No sector — only custom_terms drives the search
            custom_terms=custom_terms,
        )

        # Recovery must have been called
        assert mock_recovery.call_count >= 1, (
            "classify_contract_recovery was not called. "
            "Synonym near-miss with 1 match should trigger Camada 3B."
        )

        # Every recovery call: termos_busca=custom_terms, no setor_name
        for i, call_args in enumerate(mock_recovery.call_args_list):
            kwargs = call_args.kwargs if call_args.kwargs else {}
            setor_name_passed = kwargs.get("setor_name")
            termos_passed = kwargs.get("termos_busca")

            assert setor_name_passed is None, (
                f"Recovery call {i}: expected setor_name=None "
                f"but got setor_name={setor_name_passed!r}. "
                f"Term-aware recovery must not pass sector name."
            )
            assert termos_passed == custom_terms, (
                f"Recovery call {i}: expected termos_busca={custom_terms!r} "
                f"but got {termos_passed!r}."
            )

    @patch("llm_arbiter.classify_contract_recovery")
    @patch("synonyms.find_term_synonym_matches")
    @patch("config.get_feature_flag")
    @patch("config.LLM_ZERO_MATCH_ENABLED", False)
    def test_recovery_uses_term_prompt_not_setor_name(
        self,
        mock_get_feature_flag,
        mock_find_term_synonyms,
        mock_recovery,
    ):
        """Recovery with custom_terms must NOT pass setor_name to classify_contract_recovery."""
        def feature_flag_side_effect(name, **kwargs):
            return name in ("TERM_SEARCH_LLM_AWARE", "TERM_SEARCH_SYNONYMS")

        mock_get_feature_flag.side_effect = feature_flag_side_effect
        mock_find_term_synonyms.return_value = [("jaleco", "avental")]  # 1 match → ambiguous
        mock_recovery.return_value = False

        custom_terms = ["jaleco", "guarda-pó"]

        bid = {
            "codigoCompra": "REC-002",
            "objetoCompra": (
                "Aquisição de avental laboratorial e equipamentos de proteção "
                "individual para servidores da unidade hospitalar pública"
            ),
            "valorTotalEstimado": 60_000.0,
            "uf": "SP",
            "modalidadeNome": "Pregão Eletrônico",
            "codigoModalidadeContratacao": 6,
            "nomeOrgao": "Hospital Municipal",
            "dataPublicacaoPncp": "2026-02-01",
            "dataAberturaProposta": "2026-02-05",
            "dataEncerramentoProposta": "2026-12-31T10:00:00Z",
        }

        aplicar_todos_filtros(
            licitacoes=[bid],
            ufs_selecionadas={"SP"},
            keywords={"xyz_nonexistent_keyword_abc"},
            exclusions=set(),
            setor=None,
            custom_terms=custom_terms,
        )

        if mock_recovery.call_count >= 1:
            for i, call_args in enumerate(mock_recovery.call_args_list):
                kwargs = call_args.kwargs if call_args.kwargs else {}
                # The key assertion: no setor_name in term-aware recovery
                assert "setor_name" not in kwargs or kwargs["setor_name"] is None, (
                    f"Recovery call {i}: setor_name must be None or absent in term-aware mode, "
                    f"got {kwargs.get('setor_name')!r}"
                )
                assert kwargs.get("termos_busca") == custom_terms, (
                    f"Recovery call {i}: termos_busca must be custom_terms"
                )

    @patch("llm_arbiter.classify_contract_recovery")
    @patch("synonyms.find_synonym_matches")
    @patch("config.get_feature_flag")
    @patch("config.LLM_ZERO_MATCH_ENABLED", False)
    def test_recovery_uses_setor_name_when_no_custom_terms(
        self,
        mock_get_feature_flag,
        mock_find_synonyms,
        mock_recovery,
    ):
        """Sanity: without custom_terms, recovery uses setor_name (sector-based flow)."""
        def feature_flag_side_effect(name, **kwargs):
            return False  # All flags off

        mock_get_feature_flag.side_effect = feature_flag_side_effect
        mock_find_synonyms.return_value = [("uniforme", "fardamento")]  # 1 match
        mock_recovery.return_value = True

        bid = {
            "codigoCompra": "REC-003",
            "objetoCompra": (
                "Fornecimento de fardamento para funcionários da prefeitura municipal "
                "com entrega parcelada e requisitos de qualidade conforme edital"
            ),
            "valorTotalEstimado": 90_000.0,
            "uf": "SP",
            "modalidadeNome": "Pregão Eletrônico",
            "codigoModalidadeContratacao": 6,
            "nomeOrgao": "Prefeitura",
            "dataPublicacaoPncp": "2026-02-01",
            "dataAberturaProposta": "2026-02-05",
            "dataEncerramentoProposta": "2026-12-31T10:00:00Z",
        }

        # Exclude "fardamento" from keywords so bid is rejected then recovered via synonyms
        aplicar_todos_filtros(
            licitacoes=[bid],
            ufs_selecionadas={"SP"},
            keywords={"xyz_nonexistent_keyword_abc"},
            exclusions=set(),
            setor="vestuario",
            custom_terms=None,  # Sector-based search
        )

        if mock_recovery.call_count >= 1:
            for call_args in mock_recovery.call_args_list:
                kwargs = call_args.kwargs if call_args.kwargs else {}
                setor_name_passed = kwargs.get("setor_name")
                assert setor_name_passed is not None, (
                    "Without custom_terms, recovery must pass setor_name"
                )


# ==============================================================================
# Integration: verify prompt content reaches LLM when using _get_client
# ==============================================================================


class TestTermPromptContentReachesLLM:
    """Verify the actual prompt text sent to the LLM contains terms, not sector name."""

    @patch("llm_arbiter._get_client")
    @patch("config.get_feature_flag")
    def test_zero_match_prompt_contains_terms_not_sector(
        self, mock_get_feature_flag, mock_get_client
    ):
        """End-to-end: LLM API receives prompt with user terms, not 'Vestuário e Uniformes'."""
        def feature_flag_side_effect(name, **kwargs):
            return name == "TERM_SEARCH_LLM_AWARE"

        mock_get_feature_flag.side_effect = feature_flag_side_effect

        mock_client = Mock()
        mock_get_client.return_value = mock_client
        resp = MagicMock()
        resp.choices[0].message.content = "SIM"
        mock_client.chat.completions.create.return_value = resp

        custom_terms = ["guarda-pó", "jaleco"]
        bids = [_make_zero_match_bid()]

        with patch("config.LLM_ZERO_MATCH_ENABLED", True):
            aplicar_todos_filtros(
                licitacoes=bids,
                ufs_selecionadas={"SP"},
                keywords={"xyz_nonexistent_keyword_abc"},
                exclusions=set(),
                setor="vestuario",
                custom_terms=custom_terms,
            )

        if mock_client.chat.completions.create.call_count >= 1:
            call_args = mock_client.chat.completions.create.call_args
            messages = (
                call_args.kwargs.get("messages")
                or (call_args[1].get("messages") if call_args[1] else [])
                or []
            )
            # Find the user message
            user_messages = [m for m in messages if m.get("role") == "user"]
            assert user_messages, "No user message found in LLM call"
            user_content = user_messages[-1]["content"]

            # Terms must appear in the prompt
            for term in custom_terms:
                assert term in user_content, (
                    f"Term '{term}' not found in LLM prompt.\nPrompt:\n{user_content}"
                )

            # Sector name must NOT appear
            assert "Vestuário e Uniformes" not in user_content, (
                f"Sector name found in term-aware prompt — should not be there.\n"
                f"Prompt:\n{user_content}"
            )

    @patch("llm_arbiter._get_client")
    @patch("config.get_feature_flag")
    def test_arbiter_prompt_contains_terms_not_sector(
        self, mock_get_feature_flag, mock_get_client
    ):
        """End-to-end: Camada 3A LLM prompt contains user terms, not sector name."""
        def feature_flag_side_effect(name, **kwargs):
            return name == "TERM_SEARCH_LLM_AWARE"

        mock_get_feature_flag.side_effect = feature_flag_side_effect

        mock_client = Mock()
        mock_get_client.return_value = mock_client
        resp = MagicMock()
        resp.choices[0].message.content = "SIM"
        mock_client.chat.completions.create.return_value = resp

        custom_terms = ["equipamento de medição", "calibrador"]
        bids = [_make_gray_zone_bid(0)]

        with patch("config.LLM_ZERO_MATCH_ENABLED", False):
            aplicar_todos_filtros(
                licitacoes=bids,
                ufs_selecionadas={"SP"},
                setor="vestuario",
                custom_terms=custom_terms,
            )

        if mock_client.chat.completions.create.call_count >= 1:
            call_args = mock_client.chat.completions.create.call_args
            messages = (
                call_args.kwargs.get("messages")
                or (call_args[1].get("messages") if call_args[1] else [])
                or []
            )
            user_messages = [m for m in messages if m.get("role") == "user"]
            if user_messages:
                user_content = user_messages[-1]["content"]

                for term in custom_terms:
                    assert term in user_content, (
                        f"Term '{term}' not in Camada 3A prompt.\nPrompt:\n{user_content}"
                    )

                assert "Vestuário e Uniformes" not in user_content, (
                    f"Sector name should not appear in term-aware arbiter prompt.\n"
                    f"Prompt:\n{user_content}"
                )
