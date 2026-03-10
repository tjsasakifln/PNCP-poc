"""UX-400: Tests for link fallback and never-empty-string behavior.

AC1: Backend builds fallback link from orgaoCnpj/anoCompra/sequencialCompra.
AC2: link_edital / link is never empty string — valid URL or None.
"""

import pytest

from pipeline.helpers import _build_pncp_link, _convert_to_licitacao_items


# ============================================================================
# _build_pncp_link tests
# ============================================================================


class TestBuildPncpLink:
    """Tests for _build_pncp_link fallback chain."""

    def test_returns_link_sistema_origem_when_present(self):
        lic = {"linkSistemaOrigem": "https://example.com/edital/123"}
        assert _build_pncp_link(lic) == "https://example.com/edital/123"

    def test_falls_back_to_link_processo_eletronico(self):
        lic = {"linkProcessoEletronico": "https://compras.example.com/123"}
        assert _build_pncp_link(lic) == "https://compras.example.com/123"

    def test_falls_back_to_numero_controle_pncp(self):
        lic = {"numeroControlePNCP": "12345678000190-1-000042/2026"}
        result = _build_pncp_link(lic)
        assert result == "https://pncp.gov.br/app/editais/12345678000190/2026/42"

    def test_ac1_falls_back_to_cnpj_ano_sequencial(self):
        """AC1: When all other sources fail, uses direct PNCP fields."""
        lic = {
            "cnpjOrgao": "12345678000190",
            "anoCompra": "2026",
            "sequencialCompra": "7",
        }
        result = _build_pncp_link(lic)
        assert result == "https://pncp.gov.br/app/editais/12345678000190/2026/7"

    def test_ac2_returns_none_when_no_link_available(self):
        """AC2: Returns None (not empty string) when no link can be built."""
        lic = {"objetoCompra": "Servicos gerais"}
        result = _build_pncp_link(lic)
        assert result is None

    def test_ac2_empty_link_sistema_origem_not_used(self):
        """Empty string linkSistemaOrigem is treated as absent."""
        lic = {"linkSistemaOrigem": "", "cnpjOrgao": "99999999000100", "anoCompra": "2025", "sequencialCompra": "3"}
        result = _build_pncp_link(lic)
        assert result == "https://pncp.gov.br/app/editais/99999999000100/2025/3"

    def test_prefers_link_sistema_origem_over_fallbacks(self):
        """linkSistemaOrigem takes priority over all fallbacks."""
        lic = {
            "linkSistemaOrigem": "https://original.com/edital",
            "numeroControlePNCP": "11111111000100-1-000001/2026",
            "cnpjOrgao": "22222222000100",
            "anoCompra": "2026",
            "sequencialCompra": "1",
        }
        assert _build_pncp_link(lic) == "https://original.com/edital"

    def test_prefers_numero_controle_over_cnpj_fields(self):
        """numeroControlePNCP takes priority over cnpjOrgao/anoCompra/sequencialCompra."""
        lic = {
            "numeroControlePNCP": "33333333000100-1-000005/2026",
            "cnpjOrgao": "44444444000100",
            "anoCompra": "2025",
            "sequencialCompra": "99",
        }
        assert _build_pncp_link(lic) == "https://pncp.gov.br/app/editais/33333333000100/2026/5"

    def test_partial_cnpj_fields_returns_none(self):
        """If only some cnpj/ano/seq fields present, returns None."""
        lic = {"cnpjOrgao": "12345678000190", "anoCompra": "2026"}
        assert _build_pncp_link(lic) is None

    def test_malformed_numero_controle_falls_through(self):
        """Malformed numeroControlePNCP falls through to cnpj fields."""
        lic = {
            "numeroControlePNCP": "invalid-format",
            "cnpjOrgao": "55555555000100",
            "anoCompra": "2026",
            "sequencialCompra": "1",
        }
        assert _build_pncp_link(lic) == "https://pncp.gov.br/app/editais/55555555000100/2026/1"


# ============================================================================
# _convert_to_licitacao_items — link field
# ============================================================================


class TestConvertLinkField:
    """Tests for link field in _convert_to_licitacao_items."""

    def test_ac2_link_never_empty_string(self):
        """AC2: After conversion, link is either a valid URL or None, never ''."""
        lic = {
            "objetoCompra": "Servicos gerais",
            "nomeOrgao": "Orgao Teste",
            "uf": "SP",
        }
        result = _convert_to_licitacao_items([lic])
        assert len(result) == 1
        assert result[0].link is None or result[0].link.startswith("http")

    def test_link_populated_from_link_sistema_origem(self):
        lic = {
            "objetoCompra": "Materiais",
            "nomeOrgao": "Orgao",
            "uf": "RJ",
            "linkSistemaOrigem": "https://example.com/edital",
        }
        result = _convert_to_licitacao_items([lic])
        assert result[0].link == "https://example.com/edital"

    def test_link_fallback_from_cnpj_fields(self):
        """AC1: Falls back to cnpjOrgao/anoCompra when linkSistemaOrigem absent."""
        lic = {
            "objetoCompra": "Materiais",
            "nomeOrgao": "Orgao",
            "uf": "MG",
            "cnpjOrgao": "12345678000190",
            "anoCompra": "2026",
            "sequencialCompra": "10",
        }
        result = _convert_to_licitacao_items([lic])
        assert result[0].link == "https://pncp.gov.br/app/editais/12345678000190/2026/10"

    def test_numero_compra_populated(self):
        """AC5: numero_compra is populated from numeroEdital or codigoCompra."""
        lic = {
            "objetoCompra": "Materiais",
            "nomeOrgao": "Orgao",
            "uf": "BA",
            "numeroEdital": "PE-2026/001",
            "codigoCompra": "CODE-001",
        }
        result = _convert_to_licitacao_items([lic])
        assert result[0].numero_compra == "PE-2026/001"

    def test_numero_compra_falls_back_to_codigo(self):
        lic = {
            "objetoCompra": "Materiais",
            "nomeOrgao": "Orgao",
            "uf": "BA",
            "codigoCompra": "CODE-002",
        }
        result = _convert_to_licitacao_items([lic])
        assert result[0].numero_compra == "CODE-002"

    def test_cnpj_orgao_populated(self):
        """AC6: cnpj_orgao is populated from raw data."""
        lic = {
            "objetoCompra": "Materiais",
            "nomeOrgao": "Orgao",
            "uf": "RS",
            "cnpjOrgao": "98765432000100",
        }
        result = _convert_to_licitacao_items([lic])
        assert result[0].cnpj_orgao == "98765432000100"


# ============================================================================
# PNCPClient._build_link_edital
# ============================================================================


class TestPncpClientBuildLinkEdital:
    """Tests for PNCPLegacyAdapter._build_link_edital static method."""

    def test_returns_link_sistema_origem(self):
        from pncp_client import PNCPLegacyAdapter

        item = {"linkSistemaOrigem": "https://example.com/edital"}
        assert PNCPLegacyAdapter._build_link_edital(item) == "https://example.com/edital"

    def test_ac1_builds_fallback_from_fields(self):
        from pncp_client import PNCPLegacyAdapter

        item = {
            "cnpjOrgao": "11111111000100",
            "anoCompra": "2026",
            "sequencialCompra": "5",
        }
        result = PNCPLegacyAdapter._build_link_edital(item)
        assert result == "https://pncp.gov.br/app/editais/11111111000100/2026/5"

    def test_returns_empty_when_no_fields(self):
        from pncp_client import PNCPLegacyAdapter

        item = {"objetoCompra": "Servicos"}
        # Returns empty string (downstream _build_pncp_link handles final None conversion)
        assert PNCPLegacyAdapter._build_link_edital(item) == ""

    def test_empty_link_sistema_origem_triggers_fallback(self):
        from pncp_client import PNCPLegacyAdapter

        item = {
            "linkSistemaOrigem": "",
            "cnpjOrgao": "22222222000100",
            "anoCompra": "2025",
            "sequencialCompra": "1",
        }
        result = PNCPLegacyAdapter._build_link_edital(item)
        assert result == "https://pncp.gov.br/app/editais/22222222000100/2025/1"
