"""
GTM-FIX-028: LLM Zero Match Classification Tests

Tests for bids with ZERO keyword matches being classified by LLM
instead of being auto-rejected.

Covers AC17-AC26 from the story + prompt building + regression tests.
"""

import os
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime, timedelta

import pytest

from filter import aplicar_todos_filtros
from llm_arbiter import _build_zero_match_prompt, clear_cache


@pytest.fixture(autouse=True)
def setup_env():
    """Set up environment for testing."""
    os.environ["LLM_ARBITER_ENABLED"] = "true"
    os.environ["LLM_ZERO_MATCH_ENABLED"] = "true"
    os.environ["OPENAI_API_KEY"] = "test-key"
    clear_cache()
    yield
    clear_cache()
    # Restore defaults
    os.environ.pop("LLM_ZERO_MATCH_ENABLED", None)


def _future_date(days=10):
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")


def _past_date(days=2):
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


def make_zero_match_bid(codigo="ZM-001", objeto="Consultoria em gestão empresarial e planejamento estratégico", valor=150000.0, uf="SP"):
    """Create a bid that will NOT match vestuario keywords."""
    return {
        "codigoCompra": codigo,
        "objetoCompra": objeto,
        "valorTotalEstimado": valor,
        "uf": uf,
        "modalidadeNome": "Pregão Eletrônico",
        "nomeOrgao": "Prefeitura Municipal de São Paulo",
        "municipio": "São Paulo",
        "dataPublicacaoPncp": _past_date(),
        "dataAberturaProposta": _past_date(1),
        "dataEncerramentoProposta": _future_date(),
    }


def make_keyword_match_bid(codigo="KW-001", objeto="Aquisição de uniformes escolares e fardamento para funcionários", valor=200000.0, uf="SP"):
    """Create a bid that WILL match vestuario keywords (>5% density)."""
    return {
        "codigoCompra": codigo,
        "objetoCompra": objeto,
        "valorTotalEstimado": valor,
        "uf": uf,
        "modalidadeNome": "Pregão Eletrônico",
        "nomeOrgao": "Prefeitura Municipal de São Paulo",
        "municipio": "São Paulo",
        "dataPublicacaoPncp": _past_date(),
        "dataAberturaProposta": _past_date(1),
        "dataEncerramentoProposta": _future_date(),
    }


# ==============================================================================
# AC17: Zero-match bids pass through LLM, some approved
# ==============================================================================

class TestAC17ZeroMatchLLMClassification:
    """AC17: Bids with 0 keyword matches go through LLM → N>0 approved."""

    @patch("llm_arbiter._get_client")
    def test_zero_match_bids_classified_by_llm(self, mock_get_client):
        """10 zero-match bids, LLM approves 4."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # LLM returns SIM for calls 0,2,5,8 and NAO for rest
        responses = []
        for i in range(10):
            resp = MagicMock()
            resp.choices[0].message.content = "SIM" if i in {0, 2, 5, 8} else "NAO"
            responses.append(resp)
        mock_client.chat.completions.create.side_effect = responses

        bids = [
            make_zero_match_bid(codigo=f"ZM-{i}", objeto=f"Consultoria técnica em TI e software customizado para empresa {i}")
            for i in range(10)
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        assert stats["llm_zero_match_calls"] == 10
        assert stats["llm_zero_match_aprovadas"] == 4
        assert stats["llm_zero_match_rejeitadas"] == 6
        assert len(aprovadas) >= 4  # At least the LLM-approved ones

    @patch("llm_arbiter._get_client")
    def test_zero_match_prompt_level_is_zero_match(self, mock_get_client):
        """Verify LLM calls use prompt_level='zero_match'."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        resp = MagicMock()
        resp.choices[0].message.content = "SIM"
        mock_client.chat.completions.create.return_value = resp

        bids = [make_zero_match_bid()]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        # LLM was called
        assert mock_client.chat.completions.create.call_count >= 1

        # Check the prompt contains zero-match indicators
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs.get("messages") or call_args[1].get("messages", [])
        user_msg = messages[-1]["content"] if messages else ""
        # Zero match prompt should mention the sector
        assert "Vestuário" in user_msg or "vestuario" in user_msg.lower()


# ==============================================================================
# AC18: All LLM rejections → stats recorded
# ==============================================================================

class TestAC18AllRejections:
    """AC18: LLM rejects all → stats show calls but 0 approved."""

    @patch("llm_arbiter._get_client")
    def test_all_rejected_stats_recorded(self, mock_get_client):
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        resp = MagicMock()
        resp.choices[0].message.content = "NAO"
        mock_client.chat.completions.create.return_value = resp

        bids = [
            make_zero_match_bid(codigo=f"REJ-{i}", objeto=f"Obra de pavimentação urbana e infraestrutura viária {i}")
            for i in range(5)
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        assert len(aprovadas) == 0
        assert stats["llm_zero_match_calls"] == 5
        assert stats["llm_zero_match_aprovadas"] == 0
        assert stats["llm_zero_match_rejeitadas"] == 5


# ==============================================================================
# AC19: LLM fallback (API down) → bids REJECTED
# ==============================================================================

class TestAC19LLMFallback:
    """AC19: When LLM fails, fallback = REJECT."""

    @patch("llm_arbiter._get_client")
    def test_llm_failure_rejects_bids(self, mock_get_client):
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("OpenAI API timeout")

        bids = [
            make_zero_match_bid(codigo=f"FAIL-{i}", objeto=f"Serviços de tecnologia da informação e comunicação {i}")
            for i in range(3)
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        # All rejected due to LLM failure (fallback = REJECT)
        assert len(aprovadas) == 0
        assert stats["llm_zero_match_calls"] == 3
        assert stats["llm_zero_match_rejeitadas"] == 3


# ==============================================================================
# AC20: Concurrency — ThreadPoolExecutor(max_workers=10)
# ==============================================================================

class TestAC20Concurrency:
    """AC20: Verify concurrent LLM calls with max 10 workers."""

    @patch("llm_arbiter._get_client")
    def test_multiple_bids_processed(self, mock_get_client):
        """15 zero-match bids should all be processed."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        resp = MagicMock()
        resp.choices[0].message.content = "SIM"
        mock_client.chat.completions.create.return_value = resp

        bids = [
            make_zero_match_bid(codigo=f"CONC-{i}", objeto=f"Consultoria em planejamento e gestão pública para município {i}")
            for i in range(15)
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        # All 15 should be processed
        assert stats["llm_zero_match_calls"] == 15
        assert stats["llm_zero_match_aprovadas"] == 15


# ==============================================================================
# AC21: FilterStats records new fields
# ==============================================================================

class TestAC21FilterStats:
    """AC21: Stats dict contains llm_zero_match_* fields."""

    @patch("llm_arbiter._get_client")
    def test_stats_fields_present(self, mock_get_client):
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # 3 SIM, 3 NAO
        responses = []
        for i in range(6):
            resp = MagicMock()
            resp.choices[0].message.content = "SIM" if i < 3 else "NAO"
            responses.append(resp)
        mock_client.chat.completions.create.side_effect = responses

        bids = [
            make_zero_match_bid(codigo=f"STAT-{i}", objeto=f"Consultoria estratégica e análise de dados corporativos {i}")
            for i in range(6)
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        assert "llm_zero_match_calls" in stats
        assert "llm_zero_match_aprovadas" in stats
        assert "llm_zero_match_rejeitadas" in stats
        assert "llm_zero_match_skipped_short" in stats
        assert stats["llm_zero_match_calls"] == 6
        assert stats["llm_zero_match_aprovadas"] == 3
        assert stats["llm_zero_match_rejeitadas"] == 3


# ==============================================================================
# AC22: High density (>5%) auto-accept regression
# ==============================================================================

class TestAC22HighDensityRegression:
    """AC22: Keyword-matched bids with >5% density should auto-accept without LLM."""

    @patch("llm_arbiter._get_client")
    def test_keyword_match_no_llm_call(self, mock_get_client):
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        bids = [make_keyword_match_bid(codigo=f"KW-{i}") for i in range(3)]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        # Should be approved (keyword match + high density)
        assert len(aprovadas) == 3
        # Zero-match LLM should NOT be called
        assert stats["llm_zero_match_calls"] == 0
        # Relevance source should be "keyword"
        for bid in aprovadas:
            assert bid.get("_relevance_source") == "keyword"


# ==============================================================================
# AC23: Medium density (1-5%) uses standard/conservative LLM
# ==============================================================================

class TestAC23MediumDensityRegression:
    """AC23: Low-density keyword matches should use standard/conservative LLM."""

    @patch("llm_arbiter._get_client")
    def test_mix_keyword_and_zero_match(self, mock_get_client):
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        resp = MagicMock()
        resp.choices[0].message.content = "SIM"
        mock_client.chat.completions.create.return_value = resp

        bids = [
            make_keyword_match_bid(codigo="KW-1"),
            make_zero_match_bid(codigo="ZM-1"),
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        # keyword bid approved, zero-match bid goes through LLM
        assert stats["llm_zero_match_calls"] == 1
        assert len(aprovadas) >= 2  # keyword auto + LLM approved


# ==============================================================================
# AC24: PCP bid with valor=0.0 → "Não informado" in prompt
# ==============================================================================

class TestAC24PCPZeroValue:
    """AC24: PCP bid with valor_estimado=0.0 → prompt shows 'Não informado'."""

    def test_zero_value_prompt_nao_informado(self):
        prompt = _build_zero_match_prompt(
            setor_id=None,
            setor_name="Vestuário e Uniformes",
            objeto_truncated="Contratação de empresa para serviços gerais e manutenção predial",
            valor=0.0,
        )
        assert "Não informado" in prompt

    def test_nonzero_value_shows_reais(self):
        prompt = _build_zero_match_prompt(
            setor_id=None,
            setor_name="Vestuário e Uniformes",
            objeto_truncated="Contratação de empresa para serviços gerais",
            valor=150000.0,
        )
        assert "R$" in prompt
        assert "Não informado" not in prompt

    def test_prompt_with_valid_sector(self):
        prompt = _build_zero_match_prompt(
            setor_id="vestuario",
            setor_name="Vestuário e Uniformes",
            objeto_truncated="Aquisição de materiais diversos para escola municipal",
            valor=50000.0,
        )
        assert "Vestuário e Uniformes" in prompt
        # Should contain keyword examples from the sector
        assert "SIM" in prompt

    def test_prompt_without_sector_id_fallback(self):
        prompt = _build_zero_match_prompt(
            setor_id=None,
            setor_name="Vestuário",
            objeto_truncated="Serviços de consultoria empresarial",
            valor=100000.0,
        )
        assert "Vestuário" in prompt
        assert "SIM ou NAO" in prompt


# ==============================================================================
# AC25: Short resumo (<20 chars) → skipped
# ==============================================================================

class TestAC25ShortResumo:
    """AC25: PCP bid with resumo < 20 chars → skipped."""

    @patch("llm_arbiter._get_client")
    def test_short_objeto_skipped(self, mock_get_client):
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        resp = MagicMock()
        resp.choices[0].message.content = "SIM"
        mock_client.chat.completions.create.return_value = resp

        bids = [
            make_zero_match_bid(codigo="SHORT-1", objeto="Obra civil"),      # 10 chars - skipped
            make_zero_match_bid(codigo="SHORT-2", objeto="Serviços gerais"),  # 16 chars - skipped
            make_zero_match_bid(codigo="LONG-1", objeto="Consultoria completa em gestão empresarial e planejamento estratégico"),  # 72 chars - classified
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        assert stats["llm_zero_match_skipped_short"] == 2
        assert stats["llm_zero_match_calls"] == 1
        # Only the long one goes to LLM and gets approved
        assert len(aprovadas) == 1


# ==============================================================================
# AC26: FLUXO 2 disabled when LLM zero-match active
# ==============================================================================

class TestAC26Fluxo2Disabled:
    """AC26: FLUXO 2 disabled when LLM_ZERO_MATCH_ENABLED=true and LLM was called."""

    @patch("llm_arbiter._get_client")
    def test_fluxo2_skipped(self, mock_get_client):
        """When LLM zero-match runs, FLUXO 2 recovery should be skipped."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        resp = MagicMock()
        resp.choices[0].message.content = "NAO"
        mock_client.chat.completions.create.return_value = resp

        bids = [make_zero_match_bid()]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        # LLM was called (zero match)
        assert stats["llm_zero_match_calls"] == 1

        # FLUXO 2 should NOT have been executed (synonym recovery = 0)
        assert stats.get("recuperadas_llm_fn", 0) == 0
        assert stats.get("aprovadas_synonym_match", 0) == 0


# ==============================================================================
# EDGE CASES
# ==============================================================================

class TestEdgeCases:
    """Edge cases for LLM zero-match classification."""

    @patch("config.LLM_ZERO_MATCH_ENABLED", False)
    def test_feature_flag_disabled(self):
        """When LLM_ZERO_MATCH_ENABLED=False, zero-match bids rejected immediately."""
        bids = [
            make_zero_match_bid(codigo=f"OFF-{i}", objeto=f"Consultoria e assessoria empresarial completa número {i}")
            for i in range(5)
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        assert len(aprovadas) == 0
        assert stats.get("llm_zero_match_calls", 0) == 0

    def test_no_sector_skips_zero_match(self):
        """Without setor param, zero-match classification is skipped."""
        bids = [make_zero_match_bid()]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            # no setor param
        )

        assert stats.get("llm_zero_match_calls", 0) == 0

    @patch("llm_arbiter._get_client")
    def test_relevance_source_on_approved(self, mock_get_client):
        """Approved zero-match bids have _relevance_source='llm_zero_match'."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        resp = MagicMock()
        resp.choices[0].message.content = "SIM"
        mock_client.chat.completions.create.return_value = resp

        bids = [make_zero_match_bid(objeto="Consultoria em planejamento estratégico e desenvolvimento organizacional")]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        assert len(aprovadas) == 1
        assert aprovadas[0].get("_relevance_source") == "llm_zero_match"

    def test_empty_input(self):
        """Empty input list should not crash."""
        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=[],
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )
        assert len(aprovadas) == 0
        assert stats.get("llm_zero_match_calls", 0) == 0


# ==============================================================================
# SCHEMA TESTS
# ==============================================================================

class TestSchemas:
    """Verify new schema fields work correctly."""

    def test_filter_stats_new_fields(self):
        from schemas import FilterStats
        fs = FilterStats(
            llm_zero_match_calls=10,
            llm_zero_match_aprovadas=4,
            llm_zero_match_rejeitadas=5,
            llm_zero_match_skipped_short=1,
        )
        assert fs.llm_zero_match_calls == 10
        assert fs.llm_zero_match_aprovadas == 4
        assert fs.llm_zero_match_rejeitadas == 5
        assert fs.llm_zero_match_skipped_short == 1

    def test_filter_stats_defaults(self):
        from schemas import FilterStats
        fs = FilterStats()
        assert fs.llm_zero_match_calls == 0
        assert fs.llm_zero_match_aprovadas == 0
        assert fs.llm_zero_match_rejeitadas == 0
        assert fs.llm_zero_match_skipped_short == 0

    def test_licitacao_item_relevance_source(self):
        from schemas import LicitacaoItem
        item = LicitacaoItem(
            pncp_id="test-123",
            objeto="Teste",
            orgao="Prefeitura",
            uf="SP",
            valor=100000,
            link="https://pncp.gov.br/test",
            relevance_source="llm_zero_match",
        )
        assert item.relevance_source == "llm_zero_match"

    def test_licitacao_item_relevance_source_default_none(self):
        from schemas import LicitacaoItem
        item = LicitacaoItem(
            pncp_id="test-123",
            objeto="Teste",
            orgao="Prefeitura",
            uf="SP",
            valor=100000,
            link="https://pncp.gov.br/test",
        )
        assert item.relevance_source is None
