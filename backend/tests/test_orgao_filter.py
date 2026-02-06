"""
Tests for the orgao filter functionality.

Tests cover:
- Basic filtering by agency name
- Partial/substring matching
- Case-insensitive matching
- Accent-insensitive matching
- Multiple agencies
- Edge cases (None, empty lists, missing fields)
"""

import pytest
from filter import filtrar_por_orgao, normalize_text


class TestFiltrarPorOrgao:
    """Tests for filtrar_por_orgao function."""

    @pytest.fixture
    def sample_licitacoes(self):
        """Sample licitacoes with various agency names."""
        return [
            {
                "id": 1,
                "nomeOrgao": "Prefeitura Municipal de São Paulo",
                "objetoCompra": "Uniformes escolares",
            },
            {
                "id": 2,
                "nomeOrgao": "Ministério da Saúde",
                "objetoCompra": "Jalecos médicos",
            },
            {
                "id": 3,
                "nomeOrgao": "INSS - Instituto Nacional do Seguro Social",
                "objetoCompra": "Fardamento",
            },
            {
                "id": 4,
                "nomeOrgao": "Prefeitura Municipal de Campinas",
                "objetoCompra": "Vestuário escolar",
            },
            {
                "id": 5,
                "nomeOrgao": "Tribunal de Justiça do Estado de São Paulo",
                "objetoCompra": "Togas e vestes",
            },
        ]

    def test_filter_none_returns_all(self, sample_licitacoes):
        """When orgaos is None, return all licitacoes."""
        result = filtrar_por_orgao(sample_licitacoes, None)
        assert len(result) == 5
        assert result == sample_licitacoes

    def test_filter_empty_list_returns_all(self, sample_licitacoes):
        """When orgaos is empty list, return all licitacoes."""
        result = filtrar_por_orgao(sample_licitacoes, [])
        assert len(result) == 5

    def test_filter_single_orgao(self, sample_licitacoes):
        """Filter by a single agency name."""
        result = filtrar_por_orgao(sample_licitacoes, ["Ministério"])
        assert len(result) == 1
        assert result[0]["id"] == 2
        assert "Ministério" in result[0]["nomeOrgao"]

    def test_filter_partial_match(self, sample_licitacoes):
        """Filter by partial agency name (substring match)."""
        result = filtrar_por_orgao(sample_licitacoes, ["Prefeitura"])
        assert len(result) == 2
        assert all("Prefeitura" in lic["nomeOrgao"] for lic in result)

    def test_filter_multiple_orgaos(self, sample_licitacoes):
        """Filter by multiple agency names (OR logic)."""
        result = filtrar_por_orgao(sample_licitacoes, ["INSS", "Tribunal"])
        assert len(result) == 2
        ids = [lic["id"] for lic in result]
        assert 3 in ids  # INSS
        assert 5 in ids  # Tribunal

    def test_filter_case_insensitive(self, sample_licitacoes):
        """Matching should be case insensitive."""
        result = filtrar_por_orgao(sample_licitacoes, ["prefeitura"])
        assert len(result) == 2

        result = filtrar_por_orgao(sample_licitacoes, ["PREFEITURA"])
        assert len(result) == 2

        result = filtrar_por_orgao(sample_licitacoes, ["ministerio"])
        assert len(result) == 1

    def test_filter_accent_insensitive(self, sample_licitacoes):
        """Matching should ignore accents."""
        # Search without accents
        result = filtrar_por_orgao(sample_licitacoes, ["Sao Paulo"])
        assert len(result) == 2  # Prefeitura SP and Tribunal SP

        # Search with accents for data without accents
        result = filtrar_por_orgao(sample_licitacoes, ["Saúde"])
        assert len(result) == 1
        assert result[0]["id"] == 2

    def test_filter_no_match(self, sample_licitacoes):
        """Filter that matches no agencies returns empty list."""
        result = filtrar_por_orgao(sample_licitacoes, ["XYZ Não Existe"])
        assert len(result) == 0

    def test_filter_with_empty_string(self, sample_licitacoes):
        """Empty string in orgaos list should be ignored."""
        result = filtrar_por_orgao(sample_licitacoes, ["", "INSS"])
        assert len(result) == 1
        assert result[0]["id"] == 3

    def test_filter_empty_licitacoes(self):
        """Empty licitacoes list returns empty list."""
        result = filtrar_por_orgao([], ["Prefeitura"])
        assert len(result) == 0

    def test_filter_missing_nomeOrgao_field(self):
        """Licitacoes with missing nomeOrgao should not match."""
        licitacoes = [
            {"id": 1, "objetoCompra": "Uniformes"},  # Missing nomeOrgao
            {"id": 2, "nomeOrgao": "Prefeitura", "objetoCompra": "Jalecos"},
        ]
        result = filtrar_por_orgao(licitacoes, ["Prefeitura"])
        assert len(result) == 1
        assert result[0]["id"] == 2

    def test_filter_alternative_field_names(self):
        """Should check alternative field names for agency."""
        licitacoes = [
            {"id": 1, "orgao": "Prefeitura via orgao field", "objetoCompra": "A"},
            {"id": 2, "nomeUnidade": "Ministério via nomeUnidade", "objetoCompra": "B"},
            {"id": 3, "entidade": "INSS via entidade field", "objetoCompra": "C"},
        ]

        result = filtrar_por_orgao(licitacoes, ["Prefeitura"])
        assert len(result) == 1
        assert result[0]["id"] == 1

        result = filtrar_por_orgao(licitacoes, ["Ministério"])
        assert len(result) == 1
        assert result[0]["id"] == 2

    def test_filter_does_not_mutate_original(self, sample_licitacoes):
        """Filtering should not mutate the original list."""
        original_len = len(sample_licitacoes)
        original_first_id = sample_licitacoes[0]["id"]

        result = filtrar_por_orgao(sample_licitacoes, ["INSS"])

        assert len(sample_licitacoes) == original_len
        assert sample_licitacoes[0]["id"] == original_first_id

    def test_filter_duplicate_prevention(self, sample_licitacoes):
        """A licitacao should only appear once even if multiple terms match."""
        # Add a licitacao that matches multiple terms
        licitacoes = sample_licitacoes + [
            {
                "id": 6,
                "nomeOrgao": "Prefeitura Ministério Especial",
                "objetoCompra": "Test",
            }
        ]

        result = filtrar_por_orgao(licitacoes, ["Prefeitura", "Ministério"])

        # Should have: 2 Prefeituras + 1 Ministério + 1 that matches both
        # But the one that matches both should only appear once
        ids = [lic["id"] for lic in result]
        assert ids.count(6) == 1  # Only once, not twice


class TestNormalizeTextForOrgao:
    """Tests for normalize_text used in orgao filtering."""

    def test_normalize_lowercase(self):
        """Should convert to lowercase."""
        assert "prefeitura" in normalize_text("PREFEITURA")

    def test_normalize_accents(self):
        """Should remove accents."""
        assert normalize_text("São Paulo") == "sao paulo"
        assert normalize_text("Ministério") == "ministerio"
        assert normalize_text("Saúde") == "saude"

    def test_normalize_punctuation(self):
        """Should handle punctuation."""
        result = normalize_text("INSS - Instituto")
        assert "inss" in result
        assert "instituto" in result

    def test_normalize_empty(self):
        """Empty string should return empty."""
        assert normalize_text("") == ""


class TestIntegration:
    """Integration tests for orgao filtering."""

    def test_combined_filtering_workflow(self):
        """Test filtering orgao as part of a larger workflow."""
        licitacoes = [
            {
                "uf": "SP",
                "nomeOrgao": "Prefeitura Municipal de São Paulo",
                "valorTotalEstimado": 100000,
                "objetoCompra": "Uniformes escolares",
            },
            {
                "uf": "RJ",
                "nomeOrgao": "Ministério da Saúde",
                "valorTotalEstimado": 500000,
                "objetoCompra": "Jalecos médicos",
            },
            {
                "uf": "SP",
                "nomeOrgao": "Ministério da Educação",
                "valorTotalEstimado": 200000,
                "objetoCompra": "Material didático",
            },
        ]

        # Filter by Ministério
        result = filtrar_por_orgao(licitacoes, ["Ministério"])
        assert len(result) == 2

        # Filter by Prefeitura
        result = filtrar_por_orgao(licitacoes, ["Prefeitura"])
        assert len(result) == 1
        assert result[0]["uf"] == "SP"

    def test_common_agency_names(self):
        """Test with common Brazilian government agency names."""
        licitacoes = [
            {"nomeOrgao": "Tribunal Regional do Trabalho", "id": 1},
            {"nomeOrgao": "Universidade Federal de São Paulo", "id": 2},
            {"nomeOrgao": "Instituto Federal de Educação", "id": 3},
            {"nomeOrgao": "Banco Central do Brasil", "id": 4},
            {"nomeOrgao": "Secretaria de Estado da Saúde", "id": 5},
        ]

        # Federal institutions
        result = filtrar_por_orgao(licitacoes, ["Federal"])
        assert len(result) == 2  # Universidade Federal, Instituto Federal

        # Tribunais
        result = filtrar_por_orgao(licitacoes, ["Tribunal"])
        assert len(result) == 1

        # Secretaria
        result = filtrar_por_orgao(licitacoes, ["Secretaria"])
        assert len(result) == 1
