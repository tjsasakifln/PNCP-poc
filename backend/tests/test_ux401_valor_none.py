"""UX-401: Verify PCP v2 returns valor=None and filter/viability handle it correctly.

Tests:
- PCP v2 normalize() returns valor_estimado=None (not 0.0)
- filter.py filtrar_por_valor passes through bids with None valor
- viability.py gives neutral score (50) for None valor
- LicitacaoItem schema accepts valor=None
- _convert_to_licitacao_items propagates None valor
"""

import pytest
from unittest.mock import MagicMock


class TestPCPValorNone:
    """AC1: PCP v2 client returns valor=None instead of 0.0."""

    def test_pcp_normalize_returns_none_valor(self):
        """PCP v2 normalize() sets valor_estimado=None (not 0.0)."""
        from clients.portal_compras_client import PortalComprasAdapter

        adapter = PortalComprasAdapter()
        raw = {
            "codigoLicitacao": "12345",
            "resumo": "Aquisição de uniformes",
            "unidadeCompradora": {
                "nomeUnidadeCompradora": "Prefeitura",
                "uf": "SP",
                "cidade": "São Paulo",
            },
            "dataHoraPublicacao": "2026-03-01T10:00:00Z",
        }

        result = adapter.normalize(raw)

        assert result.valor_estimado is None
        assert result.source_name == "PORTAL_COMPRAS"

    def test_pcp_normalize_legacy_format_valor_none(self):
        """to_legacy_format() preserves None for valorTotalEstimado."""
        from clients.portal_compras_client import PortalComprasAdapter

        adapter = PortalComprasAdapter()
        raw = {
            "codigoLicitacao": "67890",
            "resumo": "Serviço de limpeza",
            "unidadeCompradora": {"uf": "RJ"},
            "dataHoraPublicacao": "2026-03-01T10:00:00Z",
        }

        result = adapter.normalize(raw)
        legacy = result.to_legacy_format()

        assert legacy["valorTotalEstimado"] is None

    def test_pcp_normalize_to_dict_valor_none(self):
        """to_dict() preserves None for valor_estimado."""
        from clients.portal_compras_client import PortalComprasAdapter

        adapter = PortalComprasAdapter()
        raw = {
            "codigoLicitacao": "11111",
            "resumo": "Material escolar",
            "unidadeCompradora": {"uf": "MG"},
            "dataHoraPublicacao": "2026-03-01T10:00:00Z",
        }

        result = adapter.normalize(raw)
        d = result.to_dict()

        assert d["valor_estimado"] is None


class TestFilterValorNone:
    """filter.py must pass through bids with None/0 valor when value filter is active."""

    def test_filtrar_por_valor_none_passes_through(self):
        """Bids with valorTotalEstimado=None should pass value filters."""
        from filter import filtrar_por_valor

        bids = [
            {"valorTotalEstimado": None, "objeto": "PCP bid no value"},
            {"valorTotalEstimado": 200000, "objeto": "PNCP bid with value"},
            {"valorTotalEstimado": 50000, "objeto": "Small bid"},
        ]

        result = filtrar_por_valor(bids, valor_min=100000, valor_max=500000)

        # None valor bid should pass through, 200k should pass, 50k filtered out
        assert len(result) == 2
        objetos = [r["objeto"] for r in result]
        assert "PCP bid no value" in objetos
        assert "PNCP bid with value" in objetos
        assert "Small bid" not in objetos

    def test_filtrar_por_valor_zero_passes_through(self):
        """Bids with valorTotalEstimado=0 should also pass value filters."""
        from filter import filtrar_por_valor

        bids = [
            {"valorTotalEstimado": 0, "objeto": "Zero value bid"},
            {"valorTotalEstimado": 300000, "objeto": "Normal bid"},
        ]

        result = filtrar_por_valor(bids, valor_min=100000)

        assert len(result) == 2
        objetos = [r["objeto"] for r in result]
        assert "Zero value bid" in objetos

    def test_filtrar_por_valor_no_filter_all_pass(self):
        """Without value filter, all bids pass including None valor."""
        from filter import filtrar_por_valor

        bids = [
            {"valorTotalEstimado": None},
            {"valorTotalEstimado": 0},
            {"valorTotalEstimado": 100000},
        ]

        result = filtrar_por_valor(bids, valor_min=None, valor_max=None)
        assert len(result) == 3


class TestViabilityValorNone:
    """viability.py must give neutral score for bids with None valor."""

    def test_viability_none_valor_neutral_score(self):
        """Bid with None valor should get value_fit=50 (neutral)."""
        from viability import calculate_viability

        bid = {
            "valorTotalEstimado": None,
            "modalidadeNome": "Pregão Eletrônico",
            "dataEncerramentoProposta": "2026-04-01",
            "uf": "SP",
        }

        result = calculate_viability(bid, ufs_busca={"SP"})

        assert result.factors.value_fit == 50
        assert result.factors.value_fit_label == "Não informado"

    def test_viability_zero_valor_neutral_score(self):
        """Bid with valor=0 should also get value_fit=50 (neutral)."""
        from viability import calculate_viability

        bid = {
            "valorTotalEstimado": 0,
            "modalidadeNome": "Pregão Eletrônico",
            "dataEncerramentoProposta": "2026-04-01",
            "uf": "SP",
        }

        result = calculate_viability(bid, ufs_busca={"SP"})

        assert result.factors.value_fit == 50

    def test_viability_value_source_missing_for_none(self):
        """assess_batch marks _value_source='missing' for None valor."""
        from viability import assess_batch

        bids = [
            {"valorTotalEstimado": None, "uf": "SP"},
            {"valorTotalEstimado": 150000, "uf": "SP"},
        ]

        assess_batch(bids, ufs_busca={"SP"})

        assert bids[0]["_value_source"] == "missing"
        assert bids[1]["_value_source"] == "estimated"


class TestSchemaValorNone:
    """AC2: LicitacaoItem schema accepts valor=None."""

    def test_licitacao_item_accepts_none_valor(self):
        """LicitacaoItem should accept valor=None without validation error."""
        from schemas import LicitacaoItem

        item = LicitacaoItem(
            pncp_id="test-001",
            objeto="Test object",
            orgao="Test org",
            uf="SP",
            valor=None,
        )

        assert item.valor is None

    def test_licitacao_item_accepts_positive_valor(self):
        """LicitacaoItem should still accept positive valor normally."""
        from schemas import LicitacaoItem

        item = LicitacaoItem(
            pncp_id="test-002",
            objeto="Test object",
            orgao="Test org",
            uf="SP",
            valor=150000.0,
        )

        assert item.valor == 150000.0

    def test_licitacao_item_serialization_with_none_valor(self):
        """LicitacaoItem with valor=None should serialize correctly."""
        from schemas import LicitacaoItem

        item = LicitacaoItem(
            pncp_id="test-003",
            objeto="Test object",
            orgao="Test org",
            uf="SP",
            valor=None,
        )

        d = item.model_dump()
        assert d["valor"] is None


class TestConvertToLicitacaoItems:
    """_convert_to_licitacao_items propagates None valor."""

    def test_none_valor_propagated(self):
        """Raw bid with valorTotalEstimado=None should produce LicitacaoItem with valor=None."""
        from search_pipeline import _convert_to_licitacao_items

        raw_bids = [
            {
                "codigoCompra": "pcp_12345",
                "objetoCompra": "Material escolar",
                "nomeOrgao": "Prefeitura SP",
                "uf": "SP",
                "valorTotalEstimado": None,
                "_source": "PCP",
            },
        ]

        items = _convert_to_licitacao_items(raw_bids)

        assert len(items) == 1
        assert items[0].valor is None

    def test_positive_valor_preserved(self):
        """Raw bid with positive valorTotalEstimado should be preserved."""
        from search_pipeline import _convert_to_licitacao_items

        raw_bids = [
            {
                "codigoCompra": "pncp_67890",
                "objetoCompra": "Uniformes",
                "nomeOrgao": "Governo RJ",
                "uf": "RJ",
                "valorTotalEstimado": 250000.0,
                "_source": "PNCP",
            },
        ]

        items = _convert_to_licitacao_items(raw_bids)

        assert len(items) == 1
        assert items[0].valor == 250000.0


class TestUnifiedProcurementValorNone:
    """UnifiedProcurement handles valor_estimado=None correctly."""

    def test_none_valor_preserved(self):
        """UnifiedProcurement with valor_estimado=None should preserve None."""
        from clients.base import UnifiedProcurement

        proc = UnifiedProcurement(
            source_id="test-1",
            source_name="TEST",
            objeto="Test",
            valor_estimado=None,
            orgao="Test Org",
            uf="SP",
        )

        assert proc.valor_estimado is None

    def test_dedup_key_with_none_valor(self):
        """Dedup key generation works with None valor."""
        from clients.base import UnifiedProcurement
        from datetime import datetime, timezone

        proc = UnifiedProcurement(
            source_id="test-2",
            source_name="TEST",
            objeto="Test object",
            valor_estimado=None,
            orgao="Test Org",
            uf="SP",
            data_publicacao=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )

        # Should use data_publicacao as discriminator (not crash)
        assert proc.dedup_key != ""
        assert "20260301" in proc.dedup_key
