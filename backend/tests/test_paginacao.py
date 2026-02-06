"""
Tests for the pagination functionality.

Tests cover:
- Basic pagination
- Edge cases (empty list, single item, exact fit)
- Page boundary validation
- Metadata accuracy
- Integration with BuscaRequest
"""

import pytest
from filter import paginar_resultados
from schemas import BuscaRequest


class TestPaginarResultados:
    """Tests for paginar_resultados function."""

    @pytest.fixture
    def sample_licitacoes(self):
        """Generate sample licitacoes for testing."""
        return [{"id": i, "objeto": f"Licitacao {i}"} for i in range(100)]

    def test_first_page_default(self, sample_licitacoes):
        """Default pagination returns first 20 items."""
        result, meta = paginar_resultados(sample_licitacoes)

        assert len(result) == 20
        assert result[0]["id"] == 0
        assert result[-1]["id"] == 19
        assert meta["pagina"] == 1
        assert meta["itens_por_pagina"] == 20
        assert meta["total"] == 100
        assert meta["total_paginas"] == 5

    def test_specific_page(self, sample_licitacoes):
        """Request specific page."""
        result, meta = paginar_resultados(sample_licitacoes, pagina=3, itens_por_pagina=20)

        assert len(result) == 20
        assert result[0]["id"] == 40  # Items 40-59
        assert result[-1]["id"] == 59
        assert meta["pagina"] == 3
        assert meta["inicio"] == 40
        assert meta["fim"] == 60

    def test_last_page_partial(self):
        """Last page may have fewer items than itens_por_pagina."""
        licitacoes = [{"id": i} for i in range(55)]
        result, meta = paginar_resultados(licitacoes, pagina=3, itens_por_pagina=20)

        assert len(result) == 15  # Only 15 items left (55 - 40)
        assert result[0]["id"] == 40
        assert result[-1]["id"] == 54
        assert meta["total_paginas"] == 3

    def test_exact_fit(self):
        """When items exactly fit pages."""
        licitacoes = [{"id": i} for i in range(60)]
        result, meta = paginar_resultados(licitacoes, pagina=3, itens_por_pagina=20)

        assert len(result) == 20
        assert meta["total_paginas"] == 3
        assert result[-1]["id"] == 59

    def test_empty_list(self):
        """Empty list returns empty result with proper metadata."""
        result, meta = paginar_resultados([], pagina=1, itens_por_pagina=20)

        assert len(result) == 0
        assert meta["total"] == 0
        assert meta["total_paginas"] == 0
        assert meta["pagina"] == 1

    def test_single_item(self):
        """Single item list."""
        licitacoes = [{"id": 0}]
        result, meta = paginar_resultados(licitacoes, pagina=1, itens_por_pagina=20)

        assert len(result) == 1
        assert meta["total"] == 1
        assert meta["total_paginas"] == 1

    def test_page_out_of_bounds_high(self, sample_licitacoes):
        """Request page beyond total pages returns last page."""
        result, meta = paginar_resultados(sample_licitacoes, pagina=100, itens_por_pagina=20)

        # Should return last page (page 5)
        assert meta["pagina"] == 5
        assert result[0]["id"] == 80
        assert result[-1]["id"] == 99

    def test_page_zero_returns_first(self, sample_licitacoes):
        """Page 0 or negative returns first page."""
        result, meta = paginar_resultados(sample_licitacoes, pagina=0, itens_por_pagina=20)

        assert meta["pagina"] == 1
        assert result[0]["id"] == 0

    def test_page_negative_returns_first(self, sample_licitacoes):
        """Negative page returns first page."""
        result, meta = paginar_resultados(sample_licitacoes, pagina=-5, itens_por_pagina=20)

        assert meta["pagina"] == 1
        assert result[0]["id"] == 0

    def test_different_page_sizes(self, sample_licitacoes):
        """Different items per page configurations."""
        # 10 per page
        result, meta = paginar_resultados(sample_licitacoes, pagina=1, itens_por_pagina=10)
        assert len(result) == 10
        assert meta["total_paginas"] == 10

        # 50 per page
        result, meta = paginar_resultados(sample_licitacoes, pagina=1, itens_por_pagina=50)
        assert len(result) == 50
        assert meta["total_paginas"] == 2

        # 100 per page
        result, meta = paginar_resultados(sample_licitacoes, pagina=1, itens_por_pagina=100)
        assert len(result) == 100
        assert meta["total_paginas"] == 1

    def test_metadata_accuracy(self, sample_licitacoes):
        """Verify all metadata fields are correct."""
        result, meta = paginar_resultados(sample_licitacoes, pagina=2, itens_por_pagina=30)

        assert meta["total"] == 100
        assert meta["pagina"] == 2
        assert meta["itens_por_pagina"] == 30
        assert meta["total_paginas"] == 4  # ceil(100/30) = 4
        assert meta["inicio"] == 30  # Second page starts at index 30
        assert meta["fim"] == 60  # Second page ends at index 60

    def test_does_not_mutate_original(self, sample_licitacoes):
        """Pagination should not mutate the original list."""
        original_len = len(sample_licitacoes)
        original_first = sample_licitacoes[0]["id"]

        paginar_resultados(sample_licitacoes, pagina=2, itens_por_pagina=20)

        assert len(sample_licitacoes) == original_len
        assert sample_licitacoes[0]["id"] == original_first


class TestBuscaRequestPaginacao:
    """Tests for pagination fields in BuscaRequest schema."""

    def test_default_pagination_values(self):
        """Default pagination values in BuscaRequest."""
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial="2026-01-01",
            data_final="2026-01-31"
        )

        assert request.pagina == 1
        assert request.itens_por_pagina == 20

    def test_custom_pagination_values(self):
        """Custom pagination values in BuscaRequest."""
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial="2026-01-01",
            data_final="2026-01-31",
            pagina=5,
            itens_por_pagina=50
        )

        assert request.pagina == 5
        assert request.itens_por_pagina == 50

    def test_valid_items_per_page_values(self):
        """Valid items per page values: 10, 20, 50, 100."""
        for items in [10, 20, 50, 100]:
            request = BuscaRequest(
                ufs=["SP"],
                data_inicial="2026-01-01",
                data_final="2026-01-31",
                itens_por_pagina=items
            )
            assert request.itens_por_pagina == items

    def test_invalid_items_per_page_values(self):
        """Invalid items per page values should raise error."""
        # Values in range [10, 100] but not in {10, 20, 50, 100} trigger custom validator
        invalid_in_range = [15, 25, 75]
        for items in invalid_in_range:
            with pytest.raises(ValueError) as exc_info:
                BuscaRequest(
                    ufs=["SP"],
                    data_inicial="2026-01-01",
                    data_final="2026-01-31",
                    itens_por_pagina=items
                )
            assert "Itens por página inválido" in str(exc_info.value)

        # Values < 10 trigger Pydantic's ge=10 constraint
        with pytest.raises(ValueError) as exc_info:
            BuscaRequest(
                ufs=["SP"],
                data_inicial="2026-01-01",
                data_final="2026-01-31",
                itens_por_pagina=5
            )
        assert "greater than or equal to 10" in str(exc_info.value)

        # Values > 100 trigger Pydantic's le=100 constraint
        for items in [150, 200]:
            with pytest.raises(ValueError) as exc_info:
                BuscaRequest(
                    ufs=["SP"],
                    data_inicial="2026-01-01",
                    data_final="2026-01-31",
                    itens_por_pagina=items
                )
            assert "less than or equal to 100" in str(exc_info.value)

    def test_page_must_be_positive(self):
        """Page number must be >= 1."""
        with pytest.raises(ValueError):
            BuscaRequest(
                ufs=["SP"],
                data_inicial="2026-01-01",
                data_final="2026-01-31",
                pagina=0
            )

        with pytest.raises(ValueError):
            BuscaRequest(
                ufs=["SP"],
                data_inicial="2026-01-01",
                data_final="2026-01-31",
                pagina=-1
            )


class TestIntegration:
    """Integration tests for pagination."""

    def test_pagination_workflow(self):
        """Complete pagination workflow."""
        # Create many licitacoes
        licitacoes = [
            {"id": i, "objeto": f"Uniforme {i}", "valor": i * 1000}
            for i in range(250)
        ]

        # Page 1, 50 items
        page1, meta1 = paginar_resultados(licitacoes, pagina=1, itens_por_pagina=50)
        assert len(page1) == 50
        assert page1[0]["id"] == 0
        assert meta1["total_paginas"] == 5

        # Page 5 (last page)
        page5, meta5 = paginar_resultados(licitacoes, pagina=5, itens_por_pagina=50)
        assert len(page5) == 50
        assert page5[0]["id"] == 200
        assert page5[-1]["id"] == 249

    def test_pagination_with_filtering(self):
        """Pagination should work on filtered results."""
        # Simulate filtered results
        filtered = [{"id": i, "objeto": f"Uniforme {i}"} for i in range(37)]

        # First page
        page1, meta = paginar_resultados(filtered, pagina=1, itens_por_pagina=10)
        assert len(page1) == 10
        assert meta["total"] == 37
        assert meta["total_paginas"] == 4

        # Last page (partial)
        page4, meta = paginar_resultados(filtered, pagina=4, itens_por_pagina=10)
        assert len(page4) == 7  # 37 - 30 = 7
        assert page4[0]["id"] == 30
        assert page4[-1]["id"] == 36
