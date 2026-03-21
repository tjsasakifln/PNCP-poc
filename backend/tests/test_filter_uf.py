"""Tests for filter_uf.py — UF, orgao, municipio, and batch filtering.

Wave 0 Safety Net: Covers filter_licitacao, filter_batch,
filtrar_por_orgao, filtrar_por_municipio.
"""

import pytest
from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from filter_uf import (
    filter_licitacao,
    filter_batch,
    filtrar_por_orgao,
    filtrar_por_municipio,
)


# ──────────────────────────────────────────────────────────────────────
# filter_licitacao
# ──────────────────────────────────────────────────────────────────────

class TestFilterLicitacao:
    """Tests for single-bid filtering."""

    @pytest.mark.timeout(30)
    def test_matching_uf_and_keyword(self):
        bid = {
            "uf": "SP",
            "objetoCompra": "Aquisicao de uniformes escolares para a secretaria de educacao",
        }
        result, reason = filter_licitacao(bid, {"SP"})
        assert result is True
        assert reason is None

    @pytest.mark.timeout(30)
    def test_wrong_uf_rejected(self):
        bid = {"uf": "RJ", "objetoCompra": "Uniformes escolares"}
        result, reason = filter_licitacao(bid, {"SP"})
        assert result is False
        assert "UF" in reason

    @pytest.mark.timeout(30)
    def test_no_keyword_match_rejected(self):
        bid = {"uf": "SP", "objetoCompra": "Aquisicao de computadores e monitores"}
        result, reason = filter_licitacao(bid, {"SP"})
        assert result is False
        assert "keyword" in reason.lower()

    @pytest.mark.timeout(30)
    def test_empty_uf(self):
        bid = {"uf": "", "objetoCompra": "Uniformes"}
        result, reason = filter_licitacao(bid, {"SP"})
        assert result is False

    @pytest.mark.timeout(30)
    def test_custom_keywords(self):
        bid = {"uf": "SP", "objetoCompra": "Aquisicao de software para gestao"}
        result, reason = filter_licitacao(
            bid, {"SP"}, keywords={"software", "gestao"}
        )
        assert result is True

    @pytest.mark.timeout(30)
    def test_filter_closed_deadline_past(self):
        bid = {
            "uf": "SP",
            "objetoCompra": "Uniformes escolares de algodao",
            "dataEncerramentoProposta": "2020-01-01T00:00:00Z",
        }
        result, reason = filter_licitacao(bid, {"SP"}, filter_closed=True)
        assert result is False
        assert "prazo" in reason.lower() or "encerrado" in reason.lower()

    @pytest.mark.timeout(30)
    def test_filter_closed_deadline_future(self):
        bid = {
            "uf": "SP",
            "objetoCompra": "Uniformes escolares de algodao",
            "dataEncerramentoProposta": "2030-12-31T00:00:00Z",
        }
        result, reason = filter_licitacao(bid, {"SP"}, filter_closed=True)
        assert result is True


# ──────────────────────────────────────────────────────────────────────
# filter_batch
# ──────────────────────────────────────────────────────────────────────

class TestFilterBatch:
    """Tests for batch filtering with statistics."""

    @pytest.mark.timeout(30)
    def test_batch_basic(self):
        bids = [
            {"uf": "SP", "objetoCompra": "Uniformes escolares de algodao"},
            {"uf": "RJ", "objetoCompra": "Uniformes escolares"},
        ]
        approved, stats = filter_batch(bids, {"SP"})
        assert stats["total"] == 2
        assert stats["aprovadas"] == 1
        assert stats["rejeitadas_uf"] == 1

    @pytest.mark.timeout(30)
    def test_batch_empty(self):
        approved, stats = filter_batch([], {"SP"})
        assert stats["total"] == 0
        assert stats["aprovadas"] == 0

    @pytest.mark.timeout(30)
    def test_batch_all_rejected_keyword(self):
        bids = [
            {"uf": "SP", "objetoCompra": "Aquisicao de computadores"},
            {"uf": "SP", "objetoCompra": "Servicos de limpeza"},
        ]
        approved, stats = filter_batch(bids, {"SP"})
        assert len(approved) == 0
        assert stats["rejeitadas_keyword"] == 2

    @pytest.mark.timeout(30)
    def test_batch_stats_sum(self):
        bids = [
            {"uf": "SP", "objetoCompra": "Uniformes escolares de algodao"},
            {"uf": "RJ", "objetoCompra": "Uniformes"},
            {"uf": "SP", "objetoCompra": "Computadores"},
        ]
        approved, stats = filter_batch(bids, {"SP"})
        total_accounted = (
            stats["aprovadas"]
            + stats["rejeitadas_uf"]
            + stats["rejeitadas_keyword"]
            + stats["rejeitadas_prazo"]
            + stats["rejeitadas_outros"]
        )
        assert total_accounted == stats["total"]


# ──────────────────────────────────────────────────────────────────────
# filtrar_por_orgao
# ──────────────────────────────────────────────────────────────────────

class TestFiltrarPorOrgao:
    """Tests for orgao name filtering."""

    @pytest.mark.timeout(30)
    def test_none_returns_all(self):
        bids = [{"nomeOrgao": "Prefeitura"}, {"nomeOrgao": "Ministerio"}]
        result = filtrar_por_orgao(bids, None)
        assert len(result) == 2

    @pytest.mark.timeout(30)
    def test_partial_match(self):
        bids = [
            {"nomeOrgao": "Prefeitura Municipal de Sao Paulo"},
            {"nomeOrgao": "Ministerio da Saude"},
        ]
        result = filtrar_por_orgao(bids, ["Prefeitura"])
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_accent_insensitive(self):
        bids = [{"nomeOrgao": "Ministerio da Saude"}]
        result = filtrar_por_orgao(bids, ["Ministerio"])
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_no_match(self):
        bids = [{"nomeOrgao": "Prefeitura Municipal"}]
        result = filtrar_por_orgao(bids, ["INSS"])
        assert len(result) == 0

    @pytest.mark.timeout(30)
    def test_empty_orgaos(self):
        bids = [{"nomeOrgao": "Prefeitura"}]
        result = filtrar_por_orgao(bids, [])
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_fallback_field_orgao(self):
        bids = [{"orgao": "INSS Federal"}]
        result = filtrar_por_orgao(bids, ["INSS"])
        assert len(result) == 1


# ──────────────────────────────────────────────────────────────────────
# filtrar_por_municipio
# ──────────────────────────────────────────────────────────────────────

class TestFiltrarPorMunicipio:
    """Tests for municipio IBGE code filtering."""

    @pytest.mark.timeout(30)
    def test_none_returns_all(self):
        bids = [{"codigoMunicipioIbge": "3550308"}]
        result = filtrar_por_municipio(bids, None)
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_matching_code(self):
        bids = [
            {"codigoMunicipioIbge": "3550308"},
            {"codigoMunicipioIbge": "3304557"},
        ]
        result = filtrar_por_municipio(bids, ["3550308"])
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_no_match(self):
        bids = [{"codigoMunicipioIbge": "3550308"}]
        result = filtrar_por_municipio(bids, ["9999999"])
        assert len(result) == 0

    @pytest.mark.timeout(30)
    def test_fallback_field_municipioId(self):
        bids = [{"municipioId": "3550308"}]
        result = filtrar_por_municipio(bids, ["3550308"])
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_empty_list(self):
        result = filtrar_por_municipio([], ["3550308"])
        assert result == []
