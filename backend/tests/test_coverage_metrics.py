"""Tests for GTM-RESILIENCE-A05: Coverage metrics calculation (AC14-AC15)."""

import sys
from unittest.mock import MagicMock as _MagicMock

# Pre-mock heavy third-party modules
for _mod_name in ("openai",):
    if _mod_name not in sys.modules:
        sys.modules[_mod_name] = _MagicMock()

import pytest
from unittest.mock import MagicMock
from schemas import UfStatusDetail, BuscaResponse


class TestBuildCoverageMetrics:
    """Test _build_coverage_metrics helper function."""

    def _make_ctx(self, ufs, succeeded_ufs=None, failed_ufs=None, raw_items=None):
        """Create a mock SearchContext."""
        ctx = MagicMock()
        ctx.request.ufs = ufs
        ctx.succeeded_ufs = succeeded_ufs
        ctx.failed_ufs = failed_ufs
        ctx.licitacoes_raw = raw_items or []
        return ctx

    def test_ac14_coverage_pct_7_of_9(self):
        """AC14: 7 UFs succeeded de 9 solicitadas -> coverage_pct = 77."""
        from search_pipeline import _build_coverage_metrics

        ufs = ["SP", "RJ", "MG", "BA", "RS", "PR", "SC", "PE", "CE"]
        failed = ["PE", "CE"]
        succeeded = ["SP", "RJ", "MG", "BA", "RS", "PR", "SC"]
        raw_items = [
            {"uf": "SP", "objeto": "teste"},
            {"uf": "SP", "objeto": "teste2"},
            {"uf": "RJ", "objeto": "teste3"},
            {"uf": "MG", "objeto": "teste4"},
            {"uf": "BA", "objeto": "teste5"},
            {"uf": "RS", "objeto": "teste6"},
            {"uf": "PR", "objeto": "teste7"},
            {"uf": "SC", "objeto": "teste8"},
        ]
        ctx = self._make_ctx(ufs, succeeded_ufs=succeeded, failed_ufs=failed, raw_items=raw_items)

        coverage_pct, details = _build_coverage_metrics(ctx)

        assert coverage_pct == 77  # int(7/9 * 100) = 77
        assert len(details) == 9

    def test_ac15_ufs_status_detail_3_ufs_2_ok_1_timeout(self):
        """AC15: busca com 3 UFs (2 OK, 1 timeout) -> 3 entries com status corretos."""
        from search_pipeline import _build_coverage_metrics

        ufs = ["SP", "RJ", "BA"]
        succeeded = ["SP", "RJ"]
        failed = ["BA"]
        raw_items = [
            {"uf": "SP", "objeto": "uniforme 1"},
            {"uf": "SP", "objeto": "uniforme 2"},
            {"uf": "SP", "objeto": "uniforme 3"},
            {"uf": "RJ", "objeto": "jaleco"},
        ]
        ctx = self._make_ctx(ufs, succeeded_ufs=succeeded, failed_ufs=failed, raw_items=raw_items)

        coverage_pct, details = _build_coverage_metrics(ctx)

        assert coverage_pct == 66  # int(2/3 * 100) = 66
        assert len(details) == 3

        sp = next(d for d in details if d.uf == "SP")
        assert sp.status == "ok"
        assert sp.results_count == 3

        rj = next(d for d in details if d.uf == "RJ")
        assert rj.status == "ok"
        assert rj.results_count == 1

        ba = next(d for d in details if d.uf == "BA")
        assert ba.status == "timeout"
        assert ba.results_count == 0

    def test_100_percent_coverage(self):
        """All UFs succeeded -> coverage_pct = 100."""
        from search_pipeline import _build_coverage_metrics

        ufs = ["SP", "RJ"]
        ctx = self._make_ctx(ufs, succeeded_ufs=["SP", "RJ"], failed_ufs=[], raw_items=[
            {"uf": "SP", "objeto": "x"},
            {"uf": "RJ", "objeto": "y"},
        ])

        coverage_pct, details = _build_coverage_metrics(ctx)

        assert coverage_pct == 100
        assert all(d.status == "ok" for d in details)

    def test_zero_percent_coverage(self):
        """All UFs failed -> coverage_pct = 0."""
        from search_pipeline import _build_coverage_metrics

        ufs = ["SP", "RJ", "MG"]
        ctx = self._make_ctx(ufs, succeeded_ufs=[], failed_ufs=["SP", "RJ", "MG"], raw_items=[])

        coverage_pct, details = _build_coverage_metrics(ctx)

        assert coverage_pct == 0
        assert all(d.status == "timeout" for d in details)

    def test_single_uf_succeeded(self):
        """Single UF requested and succeeded -> 100%."""
        from search_pipeline import _build_coverage_metrics

        ctx = self._make_ctx(["SP"], succeeded_ufs=["SP"], failed_ufs=[], raw_items=[
            {"uf": "SP", "objeto": "teste"},
        ])

        coverage_pct, details = _build_coverage_metrics(ctx)

        assert coverage_pct == 100
        assert len(details) == 1
        assert details[0].uf == "SP"
        assert details[0].status == "ok"
        assert details[0].results_count == 1

    def test_empty_ufs_list(self):
        """Empty UFs list -> 100% (edge case)."""
        from search_pipeline import _build_coverage_metrics

        ctx = self._make_ctx([], succeeded_ufs=[], failed_ufs=[], raw_items=[])

        coverage_pct, details = _build_coverage_metrics(ctx)

        assert coverage_pct == 100
        assert details == []

    def test_none_failed_ufs_defaults_to_all_ok(self):
        """When failed_ufs is None, all UFs are treated as OK."""
        from search_pipeline import _build_coverage_metrics

        ctx = self._make_ctx(["SP", "RJ"], succeeded_ufs=None, failed_ufs=None, raw_items=[])

        coverage_pct, details = _build_coverage_metrics(ctx)

        assert coverage_pct == 100
        assert all(d.status == "ok" for d in details)


class TestUfStatusDetailSchema:
    """Test UfStatusDetail Pydantic model."""

    def test_valid_ok_status(self):
        detail = UfStatusDetail(uf="SP", status="ok", results_count=45)
        assert detail.uf == "SP"
        assert detail.status == "ok"
        assert detail.results_count == 45

    def test_valid_timeout_status(self):
        detail = UfStatusDetail(uf="BA", status="timeout", results_count=0)
        assert detail.status == "timeout"

    def test_valid_error_status(self):
        detail = UfStatusDetail(uf="CE", status="error", results_count=0)
        assert detail.status == "error"

    def test_default_results_count(self):
        detail = UfStatusDetail(uf="SP", status="ok")
        assert detail.results_count == 0


class TestBuscaResponseCoverageFields:
    """Test that BuscaResponse includes coverage fields."""

    def test_coverage_pct_default(self):
        """coverage_pct defaults to 100."""
        from schemas import ResumoEstrategico
        response = BuscaResponse(
            resumo=ResumoEstrategico(
                resumo_executivo="test",
                total_oportunidades=0,
                valor_total=0,
            ),
            excel_available=False,
            quota_used=0,
            quota_remaining=10,
            total_raw=0,
            total_filtrado=0,
        )
        assert response.coverage_pct == 100
        assert response.ufs_status_detail is None

    def test_coverage_pct_with_detail(self):
        """coverage_pct and ufs_status_detail can be set."""
        from schemas import ResumoEstrategico
        details = [
            UfStatusDetail(uf="SP", status="ok", results_count=10),
            UfStatusDetail(uf="BA", status="timeout", results_count=0),
        ]
        response = BuscaResponse(
            resumo=ResumoEstrategico(
                resumo_executivo="test",
                total_oportunidades=10,
                valor_total=100000,
            ),
            excel_available=False,
            quota_used=1,
            quota_remaining=9,
            total_raw=50,
            total_filtrado=10,
            coverage_pct=50,
            ufs_status_detail=details,
        )
        assert response.coverage_pct == 50
        assert len(response.ufs_status_detail) == 2
        assert response.ufs_status_detail[0].uf == "SP"
