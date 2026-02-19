"""GTM-RESILIENCE-C03 AC3: Tests for CoverageMetadata population."""

import pytest
from unittest.mock import MagicMock
from schemas import CoverageMetadata


class TestCoverageMetadataSchema:
    """Test CoverageMetadata model validation."""

    def test_full_coverage_live(self):
        """AC3: 9 UFs solicitadas, 9 processadas -> coverage_pct=100.0, freshness=live"""
        ufs = ["SP", "RJ", "MG", "PR", "SC", "RS", "BA", "PE", "CE"]
        meta = CoverageMetadata(
            ufs_requested=ufs,
            ufs_processed=ufs,
            ufs_failed=[],
            coverage_pct=100.0,
            data_timestamp="2026-02-19T10:00:00Z",
            freshness="live",
        )
        assert meta.coverage_pct == 100.0
        assert meta.freshness == "live"
        assert len(meta.ufs_processed) == 9
        assert len(meta.ufs_failed) == 0

    def test_partial_coverage(self):
        """AC3: 9 UFs, 7 processadas, 2 falharam -> coverage_pct=77.8, ufs_failed=['PE','CE']"""
        requested = ["SP", "RJ", "MG", "PR", "SC", "RS", "BA", "PE", "CE"]
        processed = ["SP", "RJ", "MG", "PR", "SC", "RS", "BA"]
        failed = ["PE", "CE"]
        meta = CoverageMetadata(
            ufs_requested=requested,
            ufs_processed=processed,
            ufs_failed=failed,
            coverage_pct=77.8,
            data_timestamp="2026-02-19T10:00:00Z",
            freshness="live",
        )
        assert meta.coverage_pct == 77.8
        assert meta.ufs_failed == ["PE", "CE"]
        assert len(meta.ufs_processed) == 7

    def test_cached_fresh(self):
        """AC3: resultado de cache fresh -> freshness='cached_fresh'"""
        meta = CoverageMetadata(
            ufs_requested=["SP"],
            ufs_processed=["SP"],
            ufs_failed=[],
            coverage_pct=100.0,
            data_timestamp="2026-02-19T09:00:00Z",
            freshness="cached_fresh",
        )
        assert meta.freshness == "cached_fresh"

    def test_cached_stale(self):
        """AC3: resultado de cache stale -> freshness='cached_stale'"""
        meta = CoverageMetadata(
            ufs_requested=["SP", "RJ"],
            ufs_processed=["SP", "RJ"],
            ufs_failed=[],
            coverage_pct=100.0,
            data_timestamp="2026-02-19T04:00:00Z",
            freshness="cached_stale",
        )
        assert meta.freshness == "cached_stale"

    def test_single_uf(self):
        """AC3: 1 UF solicitada, 1 processada -> coverage_pct=100.0"""
        meta = CoverageMetadata(
            ufs_requested=["SP"],
            ufs_processed=["SP"],
            ufs_failed=[],
            coverage_pct=100.0,
            data_timestamp="2026-02-19T10:00:00Z",
            freshness="live",
        )
        assert meta.coverage_pct == 100.0

    def test_total_failure(self):
        """AC3: 27 UFs, 0 processadas -> coverage_pct=0.0"""
        all_ufs = [
            "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
            "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
            "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
        ]
        meta = CoverageMetadata(
            ufs_requested=all_ufs,
            ufs_processed=[],
            ufs_failed=all_ufs,
            coverage_pct=0.0,
            data_timestamp="2026-02-19T10:00:00Z",
            freshness="live",
        )
        assert meta.coverage_pct == 0.0
        assert len(meta.ufs_failed) == 27

    def test_optional_on_busca_response(self):
        """AC1: coverage_metadata is Optional on BuscaResponse for backward compatibility."""
        from schemas import BuscaResponse, ResumoEstrategico
        response = BuscaResponse(
            resumo=ResumoEstrategico(
                resumo_executivo="Test",
                total_oportunidades=0,
                valor_total=0,
            ),
            excel_available=False,
            quota_used=0,
            quota_remaining=10,
            total_raw=0,
            total_filtrado=0,
        )
        assert response.coverage_metadata is None

    def test_coverage_metadata_included_in_response(self):
        """AC1: coverage_metadata present when populated."""
        from schemas import BuscaResponse, ResumoEstrategico
        meta = CoverageMetadata(
            ufs_requested=["SP", "RJ"],
            ufs_processed=["SP"],
            ufs_failed=["RJ"],
            coverage_pct=50.0,
            data_timestamp="2026-02-19T10:00:00Z",
            freshness="live",
        )
        response = BuscaResponse(
            resumo=ResumoEstrategico(
                resumo_executivo="Test",
                total_oportunidades=0,
                valor_total=0,
            ),
            excel_available=False,
            quota_used=0,
            quota_remaining=10,
            total_raw=0,
            total_filtrado=0,
            coverage_metadata=meta,
        )
        assert response.coverage_metadata is not None
        assert response.coverage_metadata.coverage_pct == 50.0
        assert response.coverage_metadata.freshness == "live"


class TestBuildCoverageMetadata:
    """Test the _build_coverage_metadata helper function."""

    def test_live_search(self):
        """Live search returns freshness='live'."""
        from search_pipeline import _build_coverage_metadata
        ctx = MagicMock()
        ctx.request.ufs = ["SP", "RJ", "MG"]
        ctx.succeeded_ufs = ["SP", "RJ", "MG"]
        ctx.failed_ufs = []
        ctx.response_state = "live"
        ctx.cached = False
        ctx.cache_status = None
        ctx.cached_at = None

        meta = _build_coverage_metadata(ctx)
        assert meta.freshness == "live"
        assert meta.coverage_pct == 100.0
        assert meta.ufs_requested == ["SP", "RJ", "MG"]
        assert meta.ufs_processed == ["SP", "RJ", "MG"]
        assert meta.ufs_failed == []

    def test_partial_failure(self):
        """Some UFs failed returns correct coverage."""
        from search_pipeline import _build_coverage_metadata
        ctx = MagicMock()
        ctx.request.ufs = ["SP", "RJ", "MG", "BA"]
        ctx.succeeded_ufs = ["SP", "RJ"]
        ctx.failed_ufs = ["MG", "BA"]
        ctx.response_state = "live"
        ctx.cached = False
        ctx.cache_status = None
        ctx.cached_at = None

        meta = _build_coverage_metadata(ctx)
        assert meta.coverage_pct == 50.0
        assert meta.ufs_processed == ["SP", "RJ"]
        assert meta.ufs_failed == ["MG", "BA"]
        assert meta.freshness == "live"

    def test_cached_fresh_status(self):
        """Cached fresh results return freshness='cached_fresh'."""
        from search_pipeline import _build_coverage_metadata
        ctx = MagicMock()
        ctx.request.ufs = ["SP"]
        ctx.succeeded_ufs = ["SP"]
        ctx.failed_ufs = []
        ctx.response_state = "cached"
        ctx.cached = True
        ctx.cache_status = "fresh"
        ctx.cached_at = "2026-02-19T09:00:00Z"

        meta = _build_coverage_metadata(ctx)
        assert meta.freshness == "cached_fresh"
        assert meta.data_timestamp == "2026-02-19T09:00:00Z"

    def test_cached_stale_status(self):
        """Cached stale results return freshness='cached_stale'."""
        from search_pipeline import _build_coverage_metadata
        ctx = MagicMock()
        ctx.request.ufs = ["SP", "RJ"]
        ctx.succeeded_ufs = ["SP", "RJ"]
        ctx.failed_ufs = []
        ctx.response_state = "cached"
        ctx.cached = True
        ctx.cache_status = "stale"
        ctx.cached_at = "2026-02-19T04:00:00Z"

        meta = _build_coverage_metadata(ctx)
        assert meta.freshness == "cached_stale"
        assert meta.data_timestamp == "2026-02-19T04:00:00Z"

    def test_none_ufs_defaults(self):
        """When succeeded/failed UFs are None, defaults to empty lists."""
        from search_pipeline import _build_coverage_metadata
        ctx = MagicMock()
        ctx.request.ufs = ["SP"]
        ctx.succeeded_ufs = None
        ctx.failed_ufs = None
        ctx.response_state = "live"
        ctx.cached = False
        ctx.cache_status = None
        ctx.cached_at = None

        meta = _build_coverage_metadata(ctx)
        assert meta.ufs_processed == []
        assert meta.ufs_failed == []
        assert meta.coverage_pct == 0.0
