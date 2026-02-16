"""
STORY-240 AC6, AC11, AC12: Unit tests for filtrar_por_prazo_aberto() and modo_busca integration.

Tests the new "abertas" search mode that filters out bids whose proposal deadline has passed.
"""

from datetime import datetime, timezone, timedelta
from filter import filtrar_por_prazo_aberto, aplicar_todos_filtros


class TestFiltrarPorPrazoAberto:
    """Test suite for filtrar_por_prazo_aberto() function."""

    def test_bid_closed_yesterday_rejected(self):
        """AC6.1: Bid with deadline yesterday should be rejected."""
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        licitacoes = [
            {
                "codigoCompra": "123456",
                "objetoCompra": "Aquisição de uniformes escolares",
                "dataEncerramentoProposta": yesterday,
                "valorTotalEstimado": 100000,
            }
        ]

        aprovadas, rejeitadas = filtrar_por_prazo_aberto(licitacoes)

        assert len(aprovadas) == 0, "Bid closed yesterday should be rejected"
        assert rejeitadas == 1, "Should count 1 rejection"

    def test_bid_closes_tomorrow_accepted(self):
        """AC6.2: Bid with deadline tomorrow should be accepted."""
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        licitacoes = [
            {
                "codigoCompra": "123457",
                "objetoCompra": "Fornecimento de uniformes profissionais",
                "dataEncerramentoProposta": tomorrow,
                "valorTotalEstimado": 150000,
            }
        ]

        aprovadas, rejeitadas = filtrar_por_prazo_aberto(licitacoes)

        assert len(aprovadas) == 1, "Bid closing tomorrow should be accepted"
        assert rejeitadas == 0, "Should count 0 rejections"
        assert aprovadas[0]["codigoCompra"] == "123457"

    def test_bid_no_closing_date_accepted(self):
        """AC6.3: Bid without dataEncerramentoProposta should be accepted (conservative)."""
        licitacoes = [
            {
                "codigoCompra": "123458",
                "objetoCompra": "Compra de uniformes militares",
                "valorTotalEstimado": 200000,
                # No dataEncerramentoProposta field
            }
        ]

        aprovadas, rejeitadas = filtrar_por_prazo_aberto(licitacoes)

        assert len(aprovadas) == 1, "Bid without closing date should be accepted"
        assert rejeitadas == 0, "Should count 0 rejections"

    def test_bid_closes_right_now_rejected(self):
        """AC6.4: Bid closing exactly now should be rejected (edge case)."""
        now = datetime.now(timezone.utc).isoformat()
        licitacoes = [
            {
                "codigoCompra": "123459",
                "objetoCompra": "Aquisição de uniformes operacionais",
                "dataEncerramentoProposta": now,
                "valorTotalEstimado": 120000,
            }
        ]

        aprovadas, rejeitadas = filtrar_por_prazo_aberto(licitacoes)

        # Since data_fim <= agora, it should be rejected
        assert len(aprovadas) == 0, "Bid closing right now should be rejected"
        assert rejeitadas == 1, "Should count 1 rejection"

    def test_invalid_date_accepted(self):
        """AC6.5: Bid with malformed date should be accepted (graceful handling)."""
        licitacoes = [
            {
                "codigoCompra": "123460",
                "objetoCompra": "Fornecimento de uniformes hospitalares",
                "dataEncerramentoProposta": "invalid-date-format",
                "valorTotalEstimado": 80000,
            },
            {
                "codigoCompra": "123461",
                "objetoCompra": "Uniformes de segurança",
                "dataEncerramentoProposta": "32/13/2025",  # Invalid day/month
                "valorTotalEstimado": 90000,
            },
        ]

        aprovadas, rejeitadas = filtrar_por_prazo_aberto(licitacoes)

        # Conservative approach: accept bids with invalid dates
        assert len(aprovadas) == 2, "Bids with invalid dates should be accepted"
        assert rejeitadas == 0, "Should count 0 rejections"

    def test_multiple_bids_mixed(self):
        """AC6.6: Mix of open, closed, and no-date bids should be filtered correctly."""
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        next_week = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

        licitacoes = [
            {
                "codigoCompra": "001",
                "objetoCompra": "Bid closed yesterday",
                "dataEncerramentoProposta": yesterday,
                "valorTotalEstimado": 50000,
            },
            {
                "codigoCompra": "002",
                "objetoCompra": "Bid closes tomorrow",
                "dataEncerramentoProposta": tomorrow,
                "valorTotalEstimado": 60000,
            },
            {
                "codigoCompra": "003",
                "objetoCompra": "Bid with no closing date",
                "valorTotalEstimado": 70000,
                # No dataEncerramentoProposta
            },
            {
                "codigoCompra": "004",
                "objetoCompra": "Bid closes next week",
                "dataEncerramentoProposta": next_week,
                "valorTotalEstimado": 80000,
            },
            {
                "codigoCompra": "005",
                "objetoCompra": "Bid with invalid date",
                "dataEncerramentoProposta": "not-a-date",
                "valorTotalEstimado": 90000,
            },
        ]

        aprovadas, rejeitadas = filtrar_por_prazo_aberto(licitacoes)

        # Should accept: 002 (tomorrow), 003 (no date), 004 (next week), 005 (invalid date)
        # Should reject: 001 (yesterday)
        assert len(aprovadas) == 4, "Should accept 4 bids (open + no-date + invalid)"
        assert rejeitadas == 1, "Should reject 1 bid (closed)"

        approved_codes = {bid["codigoCompra"] for bid in aprovadas}
        assert approved_codes == {"002", "003", "004", "005"}

    def test_empty_list(self):
        """Edge case: Empty list should return empty list."""
        aprovadas, rejeitadas = filtrar_por_prazo_aberto([])

        assert len(aprovadas) == 0
        assert rejeitadas == 0

    def test_date_with_z_suffix(self):
        """Test that dates with 'Z' suffix (UTC indicator) are parsed correctly."""
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1))
        # Format with 'Z' suffix (common PNCP format)
        tomorrow_str = tomorrow.strftime("%Y-%m-%dT%H:%M:%SZ")

        licitacoes = [
            {
                "codigoCompra": "Z001",
                "objetoCompra": "Uniformes com data Z",
                "dataEncerramentoProposta": tomorrow_str,
                "valorTotalEstimado": 100000,
            }
        ]

        aprovadas, rejeitadas = filtrar_por_prazo_aberto(licitacoes)

        assert len(aprovadas) == 1, "Date with Z suffix should be parsed correctly"
        assert rejeitadas == 0


class TestModoFiscaIntegration:
    """Test suite for modo_busca integration in aplicar_todos_filtros()."""

    def test_modo_abertas_applies_prazo_filter(self):
        """AC6: When modo_busca='abertas', prazo aberto filter should be applied."""
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

        licitacoes = [
            {
                "uf": "SP",
                "codigoCompra": "A001",
                "objetoCompra": "Uniformes - closed yesterday",
                "dataEncerramentoProposta": yesterday,
                "valorTotalEstimado": 100000,
            },
            {
                "uf": "SP",
                "codigoCompra": "A002",
                "objetoCompra": "Uniformes - open tomorrow",
                "dataEncerramentoProposta": tomorrow,
                "valorTotalEstimado": 150000,
            },
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes,
            ufs_selecionadas={"SP"},
            modo_busca="abertas"
        )

        # Only the bid closing tomorrow should pass
        assert len(aprovadas) == 1, "Should only accept open bids"
        assert aprovadas[0]["codigoCompra"] == "A002"
        assert stats["rejeitadas_prazo_aberto"] == 1, "Should reject 1 closed bid"

    def test_modo_publicacao_skips_prazo_filter(self):
        """AC11: When modo_busca='publicacao', prazo aberto filter should NOT be applied."""
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

        licitacoes = [
            {
                "uf": "SP",
                "codigoCompra": "P001",
                "objetoCompra": "Uniformes - closed yesterday",
                "dataEncerramentoProposta": yesterday,
                "valorTotalEstimado": 100000,
            },
            {
                "uf": "SP",
                "codigoCompra": "P002",
                "objetoCompra": "Uniformes - open tomorrow",
                "dataEncerramentoProposta": tomorrow,
                "valorTotalEstimado": 150000,
            },
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes,
            ufs_selecionadas={"SP"},
            modo_busca="publicacao"
        )

        # Both bids should pass (no prazo filter)
        assert len(aprovadas) == 2, "Should accept all bids (no prazo filter)"
        assert stats["rejeitadas_prazo_aberto"] == 0, "Should not apply prazo filter"

        approved_codes = {bid["codigoCompra"] for bid in aprovadas}
        assert approved_codes == {"P001", "P002"}

    def test_default_modo_busca_is_publicacao(self):
        """Test that default modo_busca parameter is 'publicacao' for backward compatibility."""
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

        licitacoes = [
            {
                "uf": "SP",
                "codigoCompra": "D001",
                "objetoCompra": "Uniformes - closed yesterday",
                "dataEncerramentoProposta": yesterday,
                "valorTotalEstimado": 100000,
            },
        ]

        # Call without modo_busca parameter (should default to "publicacao")
        aprovadas, stats = aplicar_todos_filtros(
            licitacoes,
            ufs_selecionadas={"SP"}
            # modo_busca not specified
        )

        # Should accept the closed bid (no prazo filter)
        assert len(aprovadas) == 1, "Default mode should not apply prazo filter"
        assert stats["rejeitadas_prazo_aberto"] == 0

    def test_modo_abertas_with_other_filters(self):
        """Test that modo_busca='abertas' works correctly with other filters."""
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

        licitacoes = [
            {
                "uf": "SP",
                "codigoCompra": "M001",
                "objetoCompra": "Uniformes escolares - open",
                "dataEncerramentoProposta": tomorrow,
                "valorTotalEstimado": 50000,  # Below valor_min
            },
            {
                "uf": "SP",
                "codigoCompra": "M002",
                "objetoCompra": "Uniformes profissionais - open",
                "dataEncerramentoProposta": tomorrow,
                "valorTotalEstimado": 150000,  # Within range
            },
            {
                "uf": "SP",
                "codigoCompra": "M003",
                "objetoCompra": "Uniformes militares - closed",
                "dataEncerramentoProposta": yesterday,
                "valorTotalEstimado": 150000,  # Within range but closed
            },
            {
                "uf": "RJ",  # Different UF
                "codigoCompra": "M004",
                "objetoCompra": "Uniformes hospitalares - open",
                "dataEncerramentoProposta": tomorrow,
                "valorTotalEstimado": 150000,
            },
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes,
            ufs_selecionadas={"SP"},
            valor_min=100000,
            valor_max=200000,
            modo_busca="abertas"
        )

        # Only M002 should pass (SP, open, within value range)
        assert len(aprovadas) == 1, "Should apply all filters correctly"
        assert aprovadas[0]["codigoCompra"] == "M002"
        assert stats["rejeitadas_uf"] == 1  # M004
        assert stats["rejeitadas_valor"] == 1  # M001
        assert stats["rejeitadas_prazo_aberto"] == 1  # M003
