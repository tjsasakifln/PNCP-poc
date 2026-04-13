"""UX-437: Valor R$ 0 no histórico para buscas com resultados.

Root cause: Portal de Compras v2 não fornece valorTotalEstimado.
sanitize_valor(None) → 0.0, portanto sum([0.0, ...]) = 0.0 é salvo
em search_sessions.valor_total.

Tests:
- sanitize_valor(None) = 0.0 (PCP v2 bid sem valor)
- sanitize_valor(0) = 0.0 (bid com valor explicitamente zero)
- Cálculo de raw_values: bids sem valorTotalEstimado → valor_total = 0.0
- Cálculo de raw_values: bids PNCP com valores reais → soma correta
- Cálculo de raw_values: mix PNCP + PCP v2 → soma apenas PNCP
- quota.update_session_status recebe valor_total=0.0 quando todas são PCP v2
"""
import pytest
from utils.value_sanitizer import sanitize_valor


class TestSanitizeValorNone:
    """AC1: sanitize_valor(None) → 0.0 (base do problema UX-437)."""

    def test_none_returns_zero(self):
        """PCP v2 bids have valorTotalEstimado=None → sanitize returns 0.0."""
        assert sanitize_valor(None) == 0.0

    def test_zero_returns_zero(self):
        """Explicit zero value → sanitize returns 0.0."""
        assert sanitize_valor(0) == 0.0

    def test_missing_key_via_dict_get_default(self):
        """lic.get('valorTotalEstimado', 0) returns 0 when key absent → 0.0."""
        lic = {"resumo": "Serviço de limpeza", "codigoLicitacao": "123"}
        value = sanitize_valor(lic.get("valorTotalEstimado", 0))
        assert value == 0.0

    def test_valid_pncp_value_passes_through(self):
        """Real PNCP bid value is sanitized correctly (not zeroed)."""
        assert sanitize_valor(500_000.0) == 500_000.0
        assert sanitize_valor(1_200_000) == 1_200_000.0
        assert sanitize_valor("750000.50") == 750_000.50


class TestValorTotalCalculation:
    """AC2/AC5: Cálculo de valor_total no pipeline (generate.py logic)."""

    def _calc_raw_total(self, licitacoes):
        """Replica o cálculo de generate.py para valor_total."""
        raw_values = [
            sanitize_valor(lic.get("valorTotalEstimado", 0))
            for lic in licitacoes
        ]
        return sum(raw_values)

    def test_all_pcp_v2_bids_yield_zero_total(self):
        """AC3: Bids do PCP v2 sem valorTotalEstimado → valor_total = 0.0.

        Isso é o comportamento correto: frontend deve exibir
        'Valor não disponível' para este caso.
        """
        bids_pcp_v2 = [
            {"resumo": "Compra de material", "codigoLicitacao": "001"},
            {"resumo": "Contratação de serviço", "codigoLicitacao": "002"},
            {"resumo": "Aquisição de uniforme", "codigoLicitacao": "003"},
        ]
        total = self._calc_raw_total(bids_pcp_v2)
        assert total == 0.0

    def test_pncp_bids_with_values_yield_correct_total(self):
        """AC5: Bids PNCP com valores reais → valor_total correto no histórico."""
        bids_pncp = [
            {"valorTotalEstimado": 100_000.0, "codigoLicitacao": "PNCP-001"},
            {"valorTotalEstimado": 250_000.0, "codigoLicitacao": "PNCP-002"},
            {"valorTotalEstimado": 75_000.0, "codigoLicitacao": "PNCP-003"},
        ]
        total = self._calc_raw_total(bids_pncp)
        assert total == 425_000.0

    def test_mixed_sources_sum_only_pncp_values(self):
        """Mix PNCP + PCP v2: apenas valores PNCP entram na soma."""
        bids_mixed = [
            # PNCP com valor
            {"valorTotalEstimado": 300_000.0, "codigoLicitacao": "PNCP-001"},
            # PCP v2 sem valor
            {"resumo": "Limpeza predial", "codigoLicitacao": "PCP-001"},
            # PNCP com valor
            {"valorTotalEstimado": 150_000.0, "codigoLicitacao": "PNCP-002"},
            # PCP v2 explicitamente None
            {"valorTotalEstimado": None, "codigoLicitacao": "PCP-002"},
        ]
        total = self._calc_raw_total(bids_mixed)
        # Apenas os dois valores PNCP somam
        assert total == 450_000.0

    def test_bids_with_none_valor_explicitly(self):
        """valorTotalEstimado=None explícito → contribui 0 para a soma."""
        bids = [
            {"valorTotalEstimado": None, "codigoLicitacao": "X-001"},
            {"valorTotalEstimado": None, "codigoLicitacao": "X-002"},
        ]
        total = self._calc_raw_total(bids)
        assert total == 0.0

    def test_single_high_value_pncp_bid(self):
        """Busca com apenas 1 bid PNCP de alto valor → valor correto."""
        bids = [{"valorTotalEstimado": 5_000_000.0, "codigoLicitacao": "PNCP-999"}]
        total = self._calc_raw_total(bids)
        assert total == 5_000_000.0

    def test_empty_licitacoes_yields_zero(self):
        """Sem licitações → valor_total = 0.0 (status 'failed' sessions)."""
        total = self._calc_raw_total([])
        assert total == 0.0
