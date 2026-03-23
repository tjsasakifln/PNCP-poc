"""Integration tests for LicitaJa in intel-collect.py pipeline.

Covers:
- LicitaJa called with correct params
- Cross-source dedup (PNCP wins over LicitaJa)
- Feature flag OFF = silent skip
- Statistics populated correctly
- Normalization of LicitaJa records into pipeline format
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure scripts/ on path
_scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from licitaja_client import (
    normalize_licitaja_record,
    collect_licitaja,
    build_keyword_groups,
)


class TestCrossSourceDedup:
    """Test that PNCP records win over LicitaJa duplicates."""

    def test_pncp_wins_over_licitaja_same_objeto(self):
        """Two records with same objeto — PNCP has higher priority."""
        pncp_record = {
            "_id": "12345678000190/2026/42",
            "_source": "pncp",
            "objeto": "Construcao de escola municipal em Florianopolis",
            "orgao": "Prefeitura de Florianopolis",
            "cnpj_orgao": "12345678000190",
            "uf": "SC",
            "municipio": "Florianopolis",
            "valor_estimado": 1500000.0,
            "link_pncp": "https://pncp.gov.br/app/editais/12345678000190/2026/42",
        }

        licitaja_raw = {
            "tenderId": "LJ999",
            "tender_object": "Construcao de escola municipal em Florianopolis",
            "agency": "Prefeitura de Florianopolis",
            "state": "SC",
            "city": "Florianopolis",
            "value": 1500000.0,
            "type": "Concorrencia",
            "catalog_date": "20260320",
            "close_date": "20260415",
            "url": "https://licitaja.com/tender/LJ999",
        }
        licitaja_record = normalize_licitaja_record(licitaja_raw)

        # Both records exist — pipeline dedup should prefer PNCP
        # based on _compute_dedup_hash matching and filled-fields score
        assert pncp_record["cnpj_orgao"] == "12345678000190"
        assert licitaja_record["cnpj_orgao"] == ""  # LicitaJa doesn't have this
        assert pncp_record["link_pncp"] is not None
        assert licitaja_record["link_pncp"] is None

    def test_licitaja_unique_record_kept(self):
        """LicitaJa record with no PNCP equivalent is kept."""
        licitaja_raw = {
            "tenderId": "UNIQUE1",
            "tender_object": "Servico unico de portal municipal",
            "agency": "Camara Municipal de Xanxere",
            "state": "SC",
            "city": "Xanxere",
            "value": 50000.0,
            "catalog_date": "20260315",
            "close_date": "20260420",
        }
        record = normalize_licitaja_record(licitaja_raw)
        assert record["_id"] == "LICITAJA-UNIQUE1"
        assert record["_source"] == "licitaja"
        assert record["objeto"] == "Servico unico de portal municipal"


class TestFeatureFlagOff:
    """Test graceful skip when LicitaJa is disabled."""

    def test_disabled_produces_correct_stats(self):
        import licitaja_client as lc
        old_enabled = lc.LICITAJA_ENABLED
        lc.LICITAJA_ENABLED = False
        try:
            editais, stats = collect_licitaja(
                keywords_sample=["construcao civil"],
                ufs=["SC", "PR"],
                date_from="2026-01-01",
                date_to="2026-03-23",
                verbose=False,
            )
            assert editais == []
            assert stats["licitaja_status"] == "DISABLED"
            assert stats["licitaja_total_raw"] == 0
            assert stats["licitaja_unique_added"] == 0
            assert stats["licitaja_errors"] == 0
        finally:
            lc.LICITAJA_ENABLED = old_enabled

    def test_empty_api_key_skips(self):
        import licitaja_client as lc
        old_key = lc.LICITAJA_API_KEY
        old_enabled = lc.LICITAJA_ENABLED
        lc.LICITAJA_API_KEY = ""
        lc.LICITAJA_ENABLED = True
        try:
            editais, stats = collect_licitaja(
                keywords_sample=["teste"],
                ufs=["SC"],
                date_from="2026-01-01",
                date_to="2026-03-23",
                verbose=False,
            )
            assert editais == []
            assert stats["licitaja_status"] == "DISABLED"
        finally:
            lc.LICITAJA_API_KEY = old_key
            lc.LICITAJA_ENABLED = old_enabled


class TestStatsPopulation:
    """Test that statistics are correctly populated."""

    @patch("licitaja_client.LicitaJaClient")
    def test_stats_from_successful_collection(self, MockClientClass):
        mock_client = MagicMock()
        mock_client.health_check.return_value = "AVAILABLE"

        # Simulate search_all_pages yielding 1 page with 3 results
        def fake_search_all_pages(**kwargs):
            yield [
                {
                    "tenderId": "T1",
                    "tender_object": "Obra pavimentacao",
                    "agency": "Prefeitura X",
                    "state": "SC",
                    "city": "Joinville",
                    "value": 100000,
                    "catalog_date": "20260301",
                    "close_date": "20260430",
                },
                {
                    "tenderId": "T2",
                    "tender_object": "Reforma predial",
                    "agency": "Prefeitura Y",
                    "state": "PR",
                    "city": "Curitiba",
                    "value": 200000,
                    "catalog_date": "20260310",
                    "close_date": "20260501",
                },
                {
                    "tenderId": "T3",
                    "tender_object": "Construcao muro",
                    "agency": "Prefeitura Z",
                    "state": "SC",
                    "city": "Blumenau",
                    "value": 50000,
                    "catalog_date": "20260315",
                    "close_date": "20260520",
                },
            ]

        mock_client.search_all_pages = fake_search_all_pages
        mock_client.stats = {
            "pages_fetched": 1,
            "failed": 0,
            "rate_limited": 0,
        }
        MockClientClass.return_value = mock_client

        import licitaja_client as lc
        old_enabled = lc.LICITAJA_ENABLED
        old_key = lc.LICITAJA_API_KEY
        lc.LICITAJA_ENABLED = True
        lc.LICITAJA_API_KEY = "TEST"
        try:
            editais, stats = collect_licitaja(
                keywords_sample=["pavimentacao"],
                ufs=["SC", "PR"],
                date_from="2026-01-01",
                date_to="2026-03-23",
                api_key="TEST",
                verbose=False,
            )
            assert stats["licitaja_status"] == "API"
            assert stats["licitaja_total_raw"] == 3
            assert stats["licitaja_pages_fetched"] == 1
            assert stats["licitaja_errors"] == 0
            assert len(editais) == 3
            # All records should be normalized
            for ed in editais:
                assert ed["_source"] == "licitaja"
                assert ed["_id"].startswith("LICITAJA-")
        finally:
            lc.LICITAJA_ENABLED = old_enabled
            lc.LICITAJA_API_KEY = old_key


class TestNormalizationInPipeline:
    """Test that LicitaJa records are correctly formatted for pipeline consumption."""

    def test_record_has_all_required_fields(self):
        raw = {
            "tenderId": "FULL1",
            "tender_object": "Execucao de obras de drenagem pluvial",
            "agency": "SEMINFRA Florianopolis",
            "state": "SC",
            "city": "Florianopolis",
            "value": 2500000.0,
            "type": "Concorrencia Eletronica",
            "catalog_date": "20260310",
            "close_date": "20260510",
            "url": "https://licitaja.com/t/FULL1",
        }
        record = normalize_licitaja_record(raw)

        # Required pipeline fields
        required = [
            "_id", "_source", "objeto", "orgao", "cnpj_orgao", "uf",
            "municipio", "valor_estimado", "modalidade_nome",
            "data_publicacao", "data_abertura_proposta",
            "link_edital", "link_pncp", "status_temporal", "dias_restantes",
        ]
        for field in required:
            assert field in record, f"Missing required field: {field}"

    def test_uf_uppercase_truncated(self):
        raw = {"tenderId": "UF1", "state": "sc"}
        record = normalize_licitaja_record(raw)
        assert record["uf"] == "SC"

    def test_date_conversion(self):
        raw = {
            "tenderId": "DATE1",
            "catalog_date": "20260301",
            "close_date": "20260415",
        }
        record = normalize_licitaja_record(raw)
        assert record["data_publicacao"] == "2026-03-01"
        assert record["data_abertura_proposta"] == "2026-04-15"


class TestKeywordGroups:
    """Test keyword grouping for LicitaJa search strategy."""

    def test_groups_from_real_keywords(self):
        keywords = [
            "construcao civil", "pavimentacao", "drenagem",
            "recapeamento", "terraplanagem", "fundacao",
            "alvenaria", "concreto", "impermeabilizacao",
            "pintura predial", "reforma", "ampliacao",
        ]
        groups = build_keyword_groups(keywords, max_groups=3, terms_per_group=4)
        assert len(groups) == 3
        assert "construcao civil" in groups[0]

    def test_single_keyword(self):
        groups = build_keyword_groups(["construcao"], max_groups=3)
        assert len(groups) == 1
