"""STORY-267 AC10 + AC14: Tests for term-search filter context and viability adjustments.

AC10: When TERM_SEARCH_VIABILITY_GENERIC=true, calculate_viability uses a broad
      generic value range for term-based searches instead of the sector range.
      User profile faixa_valor always takes precedence over the generic range.

AC14: When TERM_SEARCH_FILTER_CONTEXT=true, the following sector-specific filters
      are disabled for custom_terms searches:
        - Sector max_contract_value ceiling (Camada 1A)
        - Co-occurrence rules (Camada 1B.5)
        - Proximity context filter (Camada 1B.3)
      Additionally, exclusions that overlap with user search terms are removed
      (partial exclusion logic — tested via direct exclusion set construction).

Patching notes:
- viability.py uses `from config import get_feature_flag, TERM_SEARCH_VALUE_RANGE_MIN,
  TERM_SEARCH_VALUE_RANGE_MAX` inside calculate_viability → patch at config module level:
    patch("config.get_feature_flag", ...)
    patch("config.TERM_SEARCH_VALUE_RANGE_MIN", ...)
    patch("config.TERM_SEARCH_VALUE_RANGE_MAX", ...)
- filter.py uses `from config import LLM_ZERO_MATCH_ENABLED` inside aplicar_todos_filtros
  → patch at config module level: patch("config.LLM_ZERO_MATCH_ENABLED", False)
- filter.py uses `from config import get_feature_flag` (multiple deferred imports with aliases)
  → patch at config module level: patch("config.get_feature_flag", ...)
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from typing import Set
from unittest.mock import patch, MagicMock

from viability import calculate_viability, DEFAULT_VALUE_RANGE
from filter import aplicar_todos_filtros


# =============================================================================
# Helpers
# =============================================================================


def _make_bid(
    *,
    objeto: str = "Aquisição de colete refletivo para agentes de trânsito",
    uf: str = "SP",
    valor: float = 150_000.0,
    modalidade: str = "Pregão Eletrônico",
    data_encerramento: str | None = None,
    codigo_modalidade: int = 6,
) -> dict:
    """Build a minimal bid dict compatible with both filter.py and viability.py."""
    if data_encerramento is None:
        # 20 days from now — safely within "alta" timeline window
        future = datetime.now(timezone.utc) + timedelta(days=20)
        data_encerramento = future.strftime("%Y-%m-%dT%H:%M:%S")

    return {
        "objetoCompra": objeto,
        "uf": uf,
        "valorTotalEstimado": valor,
        "modalidadeNome": modalidade,
        "codigoModalidadeContratacao": codigo_modalidade,
        "dataEncerramentoProposta": data_encerramento,
        "_status_inferido": "recebendo_proposta",
    }


# =============================================================================
# AC10: Viability generic range
# =============================================================================


class TestViabilityGenericRange:
    """AC10: calculate_viability uses broad generic range for term searches."""

    def test_viability_uses_generic_range_for_term_search(self):
        """AC10 (AC9 implementation): With custom_terms, no user profile faixa_valor,
        and value_range=None, the TERM_SEARCH_VIABILITY_GENERIC flag switches the
        value_fit scorer to use (10_000, 50_000_000) instead of DEFAULT_VALUE_RANGE.

        Verification: a bid valued at R$30M would score "Muito acima" against the
        DEFAULT_VALUE_RANGE (50k-5M) but "Ideal" against the generic range (10k-50M),
        demonstrating the flag's effect on the value_fit factor.
        """
        bid = _make_bid(valor=30_000_000.0)  # R$30M — above DEFAULT_VALUE_RANGE max of 5M

        # Without generic range flag: uses DEFAULT_VALUE_RANGE → "Muito acima" (score 20)
        with patch("config.get_feature_flag", return_value=False):
            result_sector = calculate_viability(
                bid=bid,
                ufs_busca={"SP"},
                value_range=None,
                user_profile=None,
                custom_terms=["topografia"],
            )

        # With generic range flag: uses (10_000, 50_000_000) → R$30M is within range (score 100)
        with (
            patch("config.get_feature_flag", return_value=True),
            patch("config.TERM_SEARCH_VALUE_RANGE_MIN", 10_000.0),
            patch("config.TERM_SEARCH_VALUE_RANGE_MAX", 50_000_000.0),
        ):
            result_generic = calculate_viability(
                bid=bid,
                ufs_busca={"SP"},
                value_range=None,
                user_profile=None,
                custom_terms=["topografia"],
            )

        # Sector path: R$30M >> DEFAULT_VALUE_RANGE max (5M) → ratio=6 → score 20 ("Muito acima")
        assert result_sector.factors.value_fit == 20, (
            f"Without generic range, expected value_fit=20 (Muito acima), "
            f"got {result_sector.factors.value_fit}"
        )

        # Generic path: R$30M is within (10k, 50M) → score 100 ("Ideal")
        assert result_generic.factors.value_fit == 100, (
            f"With generic range, expected value_fit=100 (Ideal for R$30M in 10k-50M), "
            f"got {result_generic.factors.value_fit}"
        )

        # Generic score must be strictly higher than sector score
        assert result_generic.factors.value_fit > result_sector.factors.value_fit

    def test_viability_user_profile_prevails_over_generic(self):
        """AC10: When user profile has faixa_valor_min/max, those values ALWAYS
        win — even when custom_terms are present and TERM_SEARCH_VIABILITY_GENERIC
        is enabled. This ensures user preference is never overridden.
        """
        bid = _make_bid(valor=500_000.0)  # R$500k

        user_profile = {
            "faixa_valor_min": 100_000.0,   # User's min: R$100k
            "faixa_valor_max": 1_000_000.0,  # User's max: R$1M
        }

        # With both generic flag and user profile — profile wins
        with (
            patch("config.get_feature_flag", return_value=True),
            patch("config.TERM_SEARCH_VALUE_RANGE_MIN", 10_000.0),
            patch("config.TERM_SEARCH_VALUE_RANGE_MAX", 50_000_000.0),
        ):
            result = calculate_viability(
                bid=bid,
                ufs_busca={"SP"},
                value_range=None,
                user_profile=user_profile,
                custom_terms=["levantamento topografico"],
            )

        # R$500k is within user range (100k-1M) → value_fit = 100 (Ideal)
        assert result.factors.value_fit == 100, (
            f"User profile range (100k-1M) should yield value_fit=100 for R$500k, "
            f"got {result.factors.value_fit}"
        )
        # Label must reference "do seu perfil" (not "do setor")
        assert "perfil" in result.factors.value_fit_label, (
            f"value_fit_label should mention 'perfil' when profile range is used, "
            f"got: '{result.factors.value_fit_label}'"
        )

    def test_viability_generic_not_applied_when_flag_disabled(self):
        """AC10 complement: When TERM_SEARCH_VIABILITY_GENERIC=false, custom_terms
        do NOT change value_range — the function falls through to DEFAULT_VALUE_RANGE.
        """
        bid = _make_bid(valor=30_000_000.0)  # R$30M — above sector range

        with patch("config.get_feature_flag", return_value=False):
            result = calculate_viability(
                bid=bid,
                ufs_busca={"SP"},
                value_range=None,
                user_profile=None,
                custom_terms=["topografia"],
            )

        # Flag is off → uses DEFAULT_VALUE_RANGE (50k-5M)
        # R$30M >> 5M → ratio=6 → score 20
        assert result.factors.value_fit == 20

    def test_viability_generic_not_applied_when_no_custom_terms(self):
        """AC10 complement: Without custom_terms, flag has no effect — falls back
        to DEFAULT_VALUE_RANGE even if TERM_SEARCH_VIABILITY_GENERIC is enabled.
        """
        bid = _make_bid(valor=30_000_000.0)

        with (
            patch("config.get_feature_flag", return_value=True),
            patch("config.TERM_SEARCH_VALUE_RANGE_MIN", 10_000.0),
            patch("config.TERM_SEARCH_VALUE_RANGE_MAX", 50_000_000.0),
        ):
            result = calculate_viability(
                bid=bid,
                ufs_busca={"SP"},
                value_range=None,
                user_profile=None,
                custom_terms=None,  # No custom terms
            )

        # No custom_terms → condition `if custom_terms and not _using_profile_value_range…`
        # evaluates to False → DEFAULT_VALUE_RANGE applies
        assert result.factors.value_fit == 20  # R$30M >> DEFAULT max of 5M


# =============================================================================
# AC14: Filter adjustments for custom_terms searches
# =============================================================================


class TestFilterContextAdjustments:
    """AC14: Sector-specific filter layers are disabled when custom_terms are present
    and TERM_SEARCH_FILTER_CONTEXT=true.
    """

    # -------------------------------------------------------------------------
    # AC14 test 1: Partial exclusions for vestuário with custom_terms
    # -------------------------------------------------------------------------

    def test_exclusions_partial_for_vestuario_with_custom_terms(self):
        """AC11/AC14: When custom_terms=["colete"], the exclusion "colete salva-vidas"
        (which contains the search term) must NOT block relevant bids that mention
        "colete" in a legitimate context.

        This test simulates the AC11 partial-exclusion logic: the caller
        (search_pipeline PrepareSearch) removes exclusions whose text contains any
        of the custom_terms before passing the set to aplicar_todos_filtros.
        We verify that a bid about "colete refletivo" is accepted when
        "colete salva-vidas" is removed from exclusions, but still rejected
        when the unrelated exclusion "uniformização de procedimento" is present
        in the bid text.

        Concretely:
        - Full exclusion set includes "colete salva-vidas" and "uniformização de procedimento"
        - After partial filter: only "uniformização de procedimento" remains
        - Bid with "colete refletivo" → passes (colete exclusion removed)
        - Bid with "uniformização de procedimento" → still rejected (unrelated exclusion kept)
        """
        # Vestuário keywords relevant to "colete"
        keywords: Set[str] = {"colete", "uniforme", "jaleco"}

        # Full exclusion set from vestuário sector — includes colete-related entries
        full_exclusions: Set[str] = {
            "colete salva-vidas",
            "colete salva vida",
            "colete balistico",
            "uniformização de procedimento",
            "uniformização de entendimento",
            "malha viaria",
        }

        # Simulate AC11 partial-exclusion logic:
        # Remove any exclusion whose normalized text CONTAINS any of the custom terms
        custom_terms = ["colete"]
        partial_exclusions: Set[str] = {
            exc for exc in full_exclusions
            if not any(term.lower() in exc.lower() for term in custom_terms)
        }

        # Verify partial exclusions: colete entries removed, others kept
        assert "colete salva-vidas" not in partial_exclusions
        assert "colete salva vida" not in partial_exclusions
        assert "colete balistico" not in partial_exclusions
        assert "uniformização de procedimento" in partial_exclusions
        assert "malha viaria" in partial_exclusions

        # Bid about "colete refletivo" — should PASS with partial exclusions
        bid_colete = _make_bid(
            objeto="Aquisição de colete refletivo para agentes de trânsito municipal",
        )

        # Bid about "uniformização de procedimento" — should still be REJECTED
        bid_uniformizacao = _make_bid(
            objeto="Uniformização de procedimento administrativo interno de pessoal",
        )

        with patch("config.LLM_ZERO_MATCH_ENABLED", False):
            aprovadas_colete, stats_colete = aplicar_todos_filtros(
                licitacoes=[bid_colete],
                ufs_selecionadas={"SP"},
                keywords=keywords,
                exclusions=partial_exclusions,
                setor="vestuario",
                custom_terms=custom_terms,
            )

            aprovadas_uniformizacao, stats_uniformizacao = aplicar_todos_filtros(
                licitacoes=[bid_uniformizacao],
                ufs_selecionadas={"SP"},
                keywords=keywords,
                exclusions=partial_exclusions,
                setor="vestuario",
                custom_terms=custom_terms,
            )

        assert len(aprovadas_colete) == 1, (
            "Bid about 'colete refletivo' should be approved when "
            "'colete salva-vidas' exclusion is removed (partial exclusion logic)"
        )
        assert len(aprovadas_uniformizacao) == 0, (
            "Bid about 'uniformização de procedimento' should still be rejected "
            "because that exclusion is unrelated to the search term 'colete'"
        )

    # -------------------------------------------------------------------------
    # AC14 test 2: max_contract_value ceiling disabled for custom_terms
    # -------------------------------------------------------------------------

    def test_max_value_ceiling_disabled_for_custom_terms(self):
        """AC12/AC14: When custom_terms present + TERM_SEARCH_FILTER_CONTEXT=true,
        the sector max_contract_value ceiling (Camada 1A) is NOT applied.

        vestuário has max_contract_value=5_000_000 (R$5M). A bid worth R$8M would
        normally be rejected by Camada 1A. With custom_terms + flag=True, it passes.
        """
        # R$8M bid — above vestuário ceiling of R$5M
        bid = _make_bid(
            objeto="Aquisição de coletes de segurança para servidores da prefeitura",
            valor=8_000_000.0,
        )

        keywords: Set[str] = {"colete"}

        # --- WITHOUT flag: ceiling applies → bid rejected by Camada 1A ---
        with (
            patch("config.LLM_ZERO_MATCH_ENABLED", False),
            patch("config.get_feature_flag", return_value=False),
        ):
            aprovadas_without, stats_without = aplicar_todos_filtros(
                licitacoes=[bid],
                ufs_selecionadas={"SP"},
                keywords=keywords,
                exclusions=set(),
                setor="vestuario",
                custom_terms=["colete"],
            )

        # --- WITH flag: ceiling skipped → bid reaches keyword stage and is approved ---
        with (
            patch("config.LLM_ZERO_MATCH_ENABLED", False),
            patch("config.get_feature_flag", return_value=True),
        ):
            aprovadas_with, stats_with = aplicar_todos_filtros(
                licitacoes=[bid],
                ufs_selecionadas={"SP"},
                keywords=keywords,
                exclusions=set(),
                setor="vestuario",
                custom_terms=["colete"],
            )

        assert stats_without.get("rejeitadas_valor_alto", 0) == 1, (
            "Without TERM_SEARCH_FILTER_CONTEXT, R$8M bid should be rejected by "
            "vestuário ceiling of R$5M (rejeitadas_valor_alto=1)"
        )
        assert stats_with.get("rejeitadas_valor_alto", 0) == 0, (
            "With TERM_SEARCH_FILTER_CONTEXT=True and custom_terms, the sector "
            "max_contract_value ceiling must be skipped (rejeitadas_valor_alto=0)"
        )
        assert len(aprovadas_with) == 1, (
            "Bid with R$8M should pass when sector ceiling is disabled for custom_terms"
        )

    # -------------------------------------------------------------------------
    # AC14 test 3: Co-occurrence rules disabled for custom_terms
    # -------------------------------------------------------------------------

    def test_co_occurrence_disabled_for_custom_terms(self):
        """AC13/AC14: When custom_terms present + TERM_SEARCH_FILTER_CONTEXT=true,
        co-occurrence rules for the sector are NOT applied.

        vestuário co-occurrence rule 1: trigger="uniform" +
        negative_contexts=["fachada", "pintura", "reforma", "revestimento"] +
        positive_signals=["textil", "epi", "costura", "tecido"]
        → Without custom_terms flag, "uniforme de fachada renovada" is rejected.
        → With custom_terms flag, co-occurrence is skipped and bid may pass.
        """
        # This bid would trigger co-occurrence rule (uniform + reforma context, no positive signal)
        bid = _make_bid(
            objeto=(
                "Fornecimento de uniforme operacional para equipe de reforma e "
                "revestimento de fachada do prédio municipal"
            ),
        )

        keywords: Set[str] = {"uniforme", "jaleco"}

        # --- Co-occurrence enabled, TERM_SEARCH_FILTER_CONTEXT=false, no custom_terms ---
        # Co-occurrence runs normally → may reject the bid
        def _flag_co_on_term_off(flag_name: str) -> bool:
            return flag_name == "CO_OCCURRENCE_RULES_ENABLED"

        with (
            patch("config.LLM_ZERO_MATCH_ENABLED", False),
            patch("config.get_feature_flag", side_effect=_flag_co_on_term_off),
        ):
            aprovadas_with_co, stats_with_co = aplicar_todos_filtros(
                licitacoes=[bid],
                ufs_selecionadas={"SP"},
                keywords=keywords,
                exclusions=set(),
                setor="vestuario",
                custom_terms=None,  # No custom_terms → co-occurrence runs normally
            )

        # --- Both CO_OCCURRENCE_RULES_ENABLED=true AND TERM_SEARCH_FILTER_CONTEXT=true ---
        # custom_terms present → co-occurrence is skipped
        def _flag_both_on(flag_name: str) -> bool:
            return flag_name in ("CO_OCCURRENCE_RULES_ENABLED", "TERM_SEARCH_FILTER_CONTEXT")

        with (
            patch("config.LLM_ZERO_MATCH_ENABLED", False),
            patch("config.get_feature_flag", side_effect=_flag_both_on),
        ):
            aprovadas_skipped_co, stats_skipped_co = aplicar_todos_filtros(
                licitacoes=[bid],
                ufs_selecionadas={"SP"},
                keywords=keywords,
                exclusions=set(),
                setor="vestuario",
                custom_terms=["uniforme"],  # custom_terms → co-occurrence skipped
            )

        # Without custom_terms: co-occurrence rejects the bid
        assert stats_with_co.get("co_occurrence_rejections", 0) >= 1, (
            "Without custom_terms, co-occurrence rule should reject bid with "
            "'uniforme + reforma/revestimento/fachada' context"
        )
        # With custom_terms: co-occurrence is skipped
        assert stats_skipped_co.get("co_occurrence_rejections", 0) == 0, (
            "With custom_terms + TERM_SEARCH_FILTER_CONTEXT=true, "
            "co-occurrence rules must be skipped entirely"
        )

    # -------------------------------------------------------------------------
    # AC14 test 4: Proximity filter disabled for custom_terms
    # -------------------------------------------------------------------------

    def test_proximity_filter_disabled_for_custom_terms(self):
        """AC13/AC14: When custom_terms present + TERM_SEARCH_FILTER_CONTEXT=true,
        the proximity context filter (Camada 1B.3) is NOT applied.

        This test verifies via the stats key 'proximity_rejections':
        - Without custom_terms (or with flag=False): proximity filter runs (may or may not reject)
        - With custom_terms + flag=True: proximity filter is skipped (0 proximity rejections)

        We use a bid that mentions the search keyword near cross-sector signature terms.
        The key assertion is that proximity_rejections=0 when custom_terms present + flag on.
        """
        # Bid that mentions "jaleco" near informatica signature terms (cross-sector context)
        bid = _make_bid(
            objeto=(
                "Aquisição de jaleco laboratorial para técnicos de suporte de TI, "
                "hardware e sistema de computadores"
            ),
        )

        keywords: Set[str] = {"jaleco"}

        def _flag_prox_on_term_off(flag_name: str) -> bool:
            """PROXIMITY_CONTEXT_ENABLED=true, TERM_SEARCH_FILTER_CONTEXT=false."""
            return flag_name == "PROXIMITY_CONTEXT_ENABLED"

        def _flag_prox_on_term_on(flag_name: str) -> bool:
            """PROXIMITY_CONTEXT_ENABLED=true, TERM_SEARCH_FILTER_CONTEXT=true."""
            return flag_name in ("PROXIMITY_CONTEXT_ENABLED", "TERM_SEARCH_FILTER_CONTEXT")

        # --- Proximity enabled, no custom_terms: filter runs (counter initialized) ---
        with (
            patch("config.LLM_ZERO_MATCH_ENABLED", False),
            patch("config.get_feature_flag", side_effect=_flag_prox_on_term_off),
        ):
            _, stats_no_terms = aplicar_todos_filtros(
                licitacoes=[bid],
                ufs_selecionadas={"SP"},
                keywords=keywords,
                exclusions=set(),
                setor="vestuario",
                custom_terms=None,
            )

        # --- Proximity enabled, custom_terms present + TERM_SEARCH_FILTER_CONTEXT=true ---
        with (
            patch("config.LLM_ZERO_MATCH_ENABLED", False),
            patch("config.get_feature_flag", side_effect=_flag_prox_on_term_on),
        ):
            _, stats_with_terms = aplicar_todos_filtros(
                licitacoes=[bid],
                ufs_selecionadas={"SP"},
                keywords=keywords,
                exclusions=set(),
                setor="vestuario",
                custom_terms=["jaleco"],
            )

        # With custom_terms + TERM_SEARCH_FILTER_CONTEXT=true: proximity skipped
        assert stats_with_terms.get("proximity_rejections", 0) == 0, (
            "With custom_terms + TERM_SEARCH_FILTER_CONTEXT=true, "
            "proximity_rejections must be 0 (filter skipped)"
        )

        # The stats key must exist (added by filter.py regardless of skip)
        assert "proximity_rejections" in stats_with_terms

    # -------------------------------------------------------------------------
    # Additional guard: flags off → sector behavior preserved
    # -------------------------------------------------------------------------

    def test_ceiling_and_co_occurrence_active_when_flag_disabled(self):
        """Guard: When TERM_SEARCH_FILTER_CONTEXT=false, sector ceiling and
        co-occurrence rules are active even if custom_terms are provided.
        This validates the feature-flag opt-in nature (AC18).
        """
        # R$8M bid above vestuário ceiling
        bid = _make_bid(
            objeto="Fornecimento de uniforme escolar padronizado para toda a rede municipal",
            valor=8_000_000.0,
        )

        keywords: Set[str] = {"uniforme"}

        # All feature flags return False → sector behavior fully active
        with (
            patch("config.LLM_ZERO_MATCH_ENABLED", False),
            patch("config.get_feature_flag", return_value=False),
        ):
            aprovadas, stats = aplicar_todos_filtros(
                licitacoes=[bid],
                ufs_selecionadas={"SP"},
                keywords=keywords,
                exclusions=set(),
                setor="vestuario",
                custom_terms=["uniforme"],  # custom_terms present but flag is off
            )

        assert stats.get("rejeitadas_valor_alto", 0) == 1, (
            "With TERM_SEARCH_FILTER_CONTEXT=false, sector max_contract_value ceiling "
            "must still apply even when custom_terms are provided"
        )
        assert len(aprovadas) == 0
