"""Tests for scripts/licitaja_client.py — LicitaJa API client.

Covers:
- TokenBucketRateLimiter
- LicitaJaClient (search, pagination, get_tender, health_check, retry)
- Date normalization
- Record normalization
- collect_licitaja integration
- build_keyword_groups
"""
from __future__ import annotations

import json
import os
import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

import sys
from pathlib import Path

# Ensure scripts/ on path
_scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from licitaja_client import (
    TokenBucketRateLimiter,
    LicitaJaClient,
    _parse_licitaja_date,
    _compute_status_temporal,
    normalize_licitaja_record,
    collect_licitaja,
    build_keyword_groups,
    LICITAJA_MAX_ITEMS_PER_PAGE,
)


# ============================================================
# TokenBucketRateLimiter
# ============================================================

class TestTokenBucketRateLimiter:
    def test_acquire_within_capacity(self):
        rl = TokenBucketRateLimiter(capacity=5, refill_rate=5.0)
        # Should immediately acquire 5 tokens
        for _ in range(5):
            assert rl.acquire(timeout=0.1) is True

    def test_acquire_exhausted_blocks(self):
        rl = TokenBucketRateLimiter(capacity=1, refill_rate=1.0)
        assert rl.acquire(timeout=0.1) is True
        # Second acquire with very short timeout should fail
        assert rl.acquire(timeout=0.05) is False

    def test_acquire_refills(self):
        rl = TokenBucketRateLimiter(capacity=1, refill_rate=100.0)  # fast refill
        assert rl.acquire(timeout=0.1) is True
        # Fast refill = should be available quickly
        assert rl.acquire(timeout=0.5) is True


# ============================================================
# Date parsing
# ============================================================

class TestDateParsing:
    def test_yyyymmdd(self):
        assert _parse_licitaja_date("20260415") == "2026-04-15"

    def test_iso_passthrough(self):
        assert _parse_licitaja_date("2026-04-15") == "2026-04-15"

    def test_none(self):
        assert _parse_licitaja_date(None) is None

    def test_empty(self):
        assert _parse_licitaja_date("") is None

    def test_long_format(self):
        assert _parse_licitaja_date("20260415120000") == "2026-04-15"


class TestComputeStatusTemporal:
    def test_expired(self):
        status, dias = _compute_status_temporal("2020-01-01")
        assert status == "EXPIRADO"
        assert dias < 0

    def test_none_date(self):
        status, dias = _compute_status_temporal(None)
        assert status == "INDETERMINADO"
        assert dias == -1

    def test_far_future(self):
        status, dias = _compute_status_temporal("2099-12-31")
        assert status == "IMINENTE"
        assert dias > 30


# ============================================================
# Record normalization
# ============================================================

class TestNormalizeLicitajaRecord:
    def test_basic_normalization(self):
        raw = {
            "tenderId": "ABC123",
            "tender_object": "Construcao de escola municipal",
            "agency": "Prefeitura de Florianopolis",
            "state": "SC",
            "city": "Florianopolis",
            "value": 1500000.0,
            "type": "Pregao Eletronico",
            "catalog_date": "20260320",
            "close_date": "20260415",
            "url": "https://example.com/tender/ABC123",
        }
        record = normalize_licitaja_record(raw)

        assert record["_id"] == "LICITAJA-ABC123"
        assert record["_source"] == "licitaja"
        assert record["objeto"] == "Construcao de escola municipal"
        assert record["orgao"] == "Prefeitura de Florianopolis"
        assert record["uf"] == "SC"
        assert record["valor_estimado"] == 1500000.0
        assert record["data_publicacao"] == "2026-03-20"
        assert record["data_abertura_proposta"] == "2026-04-15"
        assert record["link_edital"] == "https://example.com/tender/ABC123"
        assert record["link_pncp"] is None
        assert record["cnpj_orgao"] == ""  # LicitaJa doesn't provide this

    def test_missing_value(self):
        raw = {"tenderId": "X1", "value": None}
        record = normalize_licitaja_record(raw)
        assert record["valor_estimado"] == 0.0

    def test_invalid_value(self):
        raw = {"tenderId": "X2", "value": "abc"}
        record = normalize_licitaja_record(raw)
        assert record["valor_estimado"] == 0.0


# ============================================================
# build_keyword_groups
# ============================================================

class TestBuildKeywordGroups:
    def test_empty(self):
        assert build_keyword_groups([]) == []

    def test_few_keywords(self):
        kws = ["construcao", "pavimentacao", "drenagem"]
        groups = build_keyword_groups(kws, max_groups=2, terms_per_group=5)
        assert len(groups) == 1
        assert "construcao" in groups[0]

    def test_many_keywords(self):
        kws = [f"kw{i}" for i in range(20)]
        groups = build_keyword_groups(kws, max_groups=3, terms_per_group=5)
        assert len(groups) == 3
        assert "kw0" in groups[0]


# ============================================================
# LicitaJaClient (mocked HTTP)
# ============================================================

class TestLicitaJaClient:
    def _make_client(self, **kwargs):
        return LicitaJaClient(
            api_key="TEST_KEY",
            base_url="https://test.licitaja.com/api/v1",
            rate_limit_rpm=600,  # fast for tests
            timeout=5,
            verbose=False,
            **kwargs,
        )

    @patch("licitaja_client.httpx.Client")
    def test_search_tenders_success(self, MockClient):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "page": 1,
            "total_results": 2,
            "results": [
                {"tenderId": "T1", "tender_object": "Obra X"},
                {"tenderId": "T2", "tender_object": "Obra Y"},
            ],
        }
        mock_instance = MagicMock()
        mock_instance.get.return_value = mock_resp
        MockClient.return_value = mock_instance

        client = self._make_client()
        client.client = mock_instance

        results, total, status = client.search_tenders(
            keyword="construcao", states=["SC"], page=1
        )

        assert status == "API"
        assert total == 2
        assert len(results) == 2
        assert results[0]["tenderId"] == "T1"

    @patch("licitaja_client.httpx.Client")
    def test_search_tenders_401_unauthorized(self, MockClient):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_instance = MagicMock()
        mock_instance.get.return_value = mock_resp
        MockClient.return_value = mock_instance

        client = self._make_client()
        client.client = mock_instance

        results, total, status = client.search_tenders(keyword="teste")
        assert status == "UNAUTHORIZED"
        assert results == []
        assert total == 0

    @patch("licitaja_client.httpx.Client")
    def test_search_tenders_timeout(self, MockClient):
        import httpx
        mock_instance = MagicMock()
        mock_instance.get.side_effect = httpx.TimeoutException("timeout")
        MockClient.return_value = mock_instance

        client = self._make_client()
        client.client = mock_instance

        results, total, status = client.search_tenders(keyword="teste")
        assert status == "API_FAILED"
        assert results == []

    @patch("licitaja_client.httpx.Client")
    def test_health_check_available(self, MockClient):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_instance = MagicMock()
        mock_instance.get.return_value = mock_resp
        MockClient.return_value = mock_instance

        client = self._make_client()
        client.client = mock_instance

        assert client.health_check() == "AVAILABLE"

    @patch("licitaja_client.httpx.Client")
    def test_health_check_unauthorized(self, MockClient):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_instance = MagicMock()
        mock_instance.get.return_value = mock_resp
        MockClient.return_value = mock_instance

        client = self._make_client()
        client.client = mock_instance

        assert client.health_check() == "UNAUTHORIZED"

    @patch("licitaja_client.httpx.Client")
    def test_get_tender_success(self, MockClient):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "tenderId": "T1",
            "tender_object": "Detalhes completos",
        }
        mock_instance = MagicMock()
        mock_instance.get.return_value = mock_resp
        MockClient.return_value = mock_instance

        client = self._make_client()
        client.client = mock_instance

        data, status = client.get_tender("T1")
        assert status == "API"
        assert data["tenderId"] == "T1"

    @patch("licitaja_client.httpx.Client")
    def test_rate_limit_triple_429_stops(self, MockClient):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_instance = MagicMock()
        mock_instance.get.return_value = mock_resp
        MockClient.return_value = mock_instance

        client = self._make_client()
        client.client = mock_instance

        # Patch sleep to avoid delays
        with patch("licitaja_client.time.sleep"):
            results, total, status = client.search_tenders(keyword="teste")

        assert status == "RATE_LIMITED"
        assert client.stats["rate_limited"] >= 3


# ============================================================
# collect_licitaja (integration)
# ============================================================

class TestCollectLicitaja:
    @patch.dict(os.environ, {"LICITAJA_ENABLED": "false"})
    def test_disabled_returns_empty(self):
        # Need to reimport to pick up env change
        import importlib
        import licitaja_client as lc
        old_enabled = lc.LICITAJA_ENABLED
        lc.LICITAJA_ENABLED = False
        try:
            editais, stats = collect_licitaja(
                keywords_sample=["construcao"],
                ufs=["SC"],
                date_from="2026-01-01",
                date_to="2026-03-23",
                verbose=False,
            )
            assert editais == []
            assert stats["licitaja_status"] == "DISABLED"
        finally:
            lc.LICITAJA_ENABLED = old_enabled

    def test_timeout_guard_skips(self):
        editais, stats = collect_licitaja(
            keywords_sample=["construcao"],
            ufs=["SC"],
            date_from="2026-01-01",
            date_to="2026-03-23",
            verbose=False,
            elapsed_s=290.0,  # Only 10s left
            pipeline_timeout_s=300.0,
        )
        assert editais == []
        assert stats["licitaja_status"] in ("DISABLED", "TIMEOUT_SKIPPED")

    @patch("licitaja_client.LicitaJaClient")
    def test_unauthorized_returns_empty(self, MockClientClass):
        mock_client = MagicMock()
        mock_client.health_check.return_value = "UNAUTHORIZED"
        MockClientClass.return_value = mock_client

        import licitaja_client as lc
        old_enabled = lc.LICITAJA_ENABLED
        old_key = lc.LICITAJA_API_KEY
        lc.LICITAJA_ENABLED = True
        lc.LICITAJA_API_KEY = "TEST"
        try:
            editais, stats = collect_licitaja(
                keywords_sample=["construcao"],
                ufs=["SC"],
                date_from="2026-01-01",
                date_to="2026-03-23",
                api_key="TEST",
                verbose=False,
            )
            assert editais == []
            assert stats["licitaja_status"] == "UNAUTHORIZED"
        finally:
            lc.LICITAJA_ENABLED = old_enabled
            lc.LICITAJA_API_KEY = old_key
