"""Tests for filter_value.py — value range filtering and pagination.

Wave 0 Safety Net: Covers filtrar_por_valor and paginar_resultados.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from filter_value import filtrar_por_valor, paginar_resultados


# ──────────────────────────────────────────────────────────────────────
# filtrar_por_valor
# ──────────────────────────────────────────────────────────────────────

class TestFiltrarPorValor:
    """Tests for value range filtering."""

    @pytest.mark.timeout(30)
    def test_no_limits_returns_all(self):
        bids = [{"valorTotalEstimado": 50000}, {"valorTotalEstimado": 200000}]
        result = filtrar_por_valor(bids)
        assert len(result) == 2

    @pytest.mark.timeout(30)
    def test_min_only(self):
        bids = [
            {"valorTotalEstimado": 50000},
            {"valorTotalEstimado": 200000},
            {"valorTotalEstimado": 500000},
        ]
        result = filtrar_por_valor(bids, valor_min=100000)
        assert len(result) == 2
        assert all(b["valorTotalEstimado"] >= 100000 for b in result)

    @pytest.mark.timeout(30)
    def test_max_only(self):
        bids = [
            {"valorTotalEstimado": 50000},
            {"valorTotalEstimado": 200000},
            {"valorTotalEstimado": 500000},
        ]
        result = filtrar_por_valor(bids, valor_max=200000)
        assert len(result) == 2

    @pytest.mark.timeout(30)
    def test_min_and_max(self):
        bids = [
            {"valorTotalEstimado": 50000},
            {"valorTotalEstimado": 200000},
            {"valorTotalEstimado": 500000},
        ]
        result = filtrar_por_valor(bids, valor_min=100000, valor_max=300000)
        assert len(result) == 1
        assert result[0]["valorTotalEstimado"] == 200000

    @pytest.mark.timeout(30)
    def test_none_value_passes_through(self):
        """Bids with no value pass through (UX-401)."""
        bids = [{"valorTotalEstimado": None}]
        result = filtrar_por_valor(bids, valor_min=100000)
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_zero_value_passes_through(self):
        """Bids with zero value pass through (UX-401)."""
        bids = [{"valorTotalEstimado": 0}]
        result = filtrar_por_valor(bids, valor_min=100000)
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_string_brazilian_format(self):
        bids = [{"valorTotalEstimado": "1.000.000,50"}]
        result = filtrar_por_valor(bids, valor_min=500000)
        # After conversion: 100000050.0 (dots removed, comma->dot)
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_unparseable_string_passes_through(self):
        bids = [{"valorTotalEstimado": "invalid"}]
        result = filtrar_por_valor(bids, valor_min=100000)
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_empty_list(self):
        result = filtrar_por_valor([], valor_min=100000)
        assert result == []

    @pytest.mark.timeout(30)
    def test_valorEstimado_fallback(self):
        bids = [{"valorEstimado": 200000}]
        result = filtrar_por_valor(bids, valor_min=100000)
        assert len(result) == 1


# ──────────────────────────────────────────────────────────────────────
# paginar_resultados
# ──────────────────────────────────────────────────────────────────────

class TestPaginarResultados:
    """Tests for result pagination."""

    @pytest.mark.timeout(30)
    def test_first_page(self):
        bids = [{"id": i} for i in range(50)]
        page, meta = paginar_resultados(bids, pagina=1, itens_por_pagina=20)
        assert len(page) == 20
        assert meta["total"] == 50
        assert meta["pagina"] == 1
        assert meta["total_paginas"] == 3
        assert meta["inicio"] == 0
        assert meta["fim"] == 20

    @pytest.mark.timeout(30)
    def test_last_page_partial(self):
        bids = [{"id": i} for i in range(50)]
        page, meta = paginar_resultados(bids, pagina=3, itens_por_pagina=20)
        assert len(page) == 10
        assert meta["inicio"] == 40
        assert meta["fim"] == 50

    @pytest.mark.timeout(30)
    def test_empty_list(self):
        page, meta = paginar_resultados([], pagina=1)
        assert page == []
        assert meta["total"] == 0
        assert meta["total_paginas"] == 0

    @pytest.mark.timeout(30)
    def test_page_beyond_range_clamped(self):
        bids = [{"id": i} for i in range(10)]
        page, meta = paginar_resultados(bids, pagina=999, itens_por_pagina=20)
        assert meta["pagina"] == 1  # Clamped to last valid page
        assert len(page) == 10

    @pytest.mark.timeout(30)
    def test_page_zero_clamped(self):
        bids = [{"id": i} for i in range(10)]
        page, meta = paginar_resultados(bids, pagina=0, itens_por_pagina=20)
        assert meta["pagina"] == 1

    @pytest.mark.timeout(30)
    def test_single_item(self):
        bids = [{"id": 1}]
        page, meta = paginar_resultados(bids, pagina=1, itens_por_pagina=20)
        assert len(page) == 1
        assert meta["total_paginas"] == 1
