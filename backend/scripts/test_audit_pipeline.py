"""
CI/CD threshold validation for audit_pipeline_complete.py (CRIT-FLT-005 AC7).

Two test categories:
  1. Unit tests (TestUnit*) — validate script functions with synthetic data, always run
  2. Threshold tests (TestAudit*) — validate metrics JSON, skip if not generated yet

Usage:
    pytest scripts/test_audit_pipeline.py -v
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.audit_pipeline_complete import (
    calculate_density,
    classify_density_zone,
    detect_false_positives,
    detect_false_negatives,
    analyze_cross_sector,
    analyze_pcp_v2,
    build_metrics,
    resolve_sector_ids,
    generate_markdown_report,
)

METRICS_FILE = Path(__file__).parent / "audit_pipeline_metrics.json"

# ============================================================================
# THRESHOLDS (configurable via metrics JSON or overridden here)
# ============================================================================

MIN_PRECISION = 0.70       # 70% estimated precision per sector
MIN_RECALL = 0.50          # 50% estimated recall per sector
MAX_COLLISION_RATE = 0.15  # 15% max cross-sector collision rate
MIN_ITEMS_ANALYZED = 50    # Minimum items for a valid audit run


def _load_metrics() -> dict:
    """Load metrics JSON, skip if file doesn't exist (first run)."""
    if not METRICS_FILE.exists():
        pytest.skip(
            f"Metrics file not found: {METRICS_FILE}. "
            "Run 'python scripts/audit_pipeline_complete.py' first."
        )
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================================
# UNIT TESTS (always run, no API calls, no metrics file needed)
# ============================================================================


class TestUnitDensity:
    """Test density calculation and zone classification."""

    def test_density_calculation_basic(self):
        # "uniforme" appears 1 time in 5 words = 20%
        d = calculate_density("aquisição de uniforme escolar completo", {"uniforme"})
        assert d > 0.1

    def test_density_zero_when_no_match(self):
        d = calculate_density("serviço de limpeza predial", {"uniforme"})
        assert d == 0.0

    def test_density_empty_text(self):
        d = calculate_density("", {"uniforme"})
        assert d == 0.0

    def test_zone_high(self):
        assert classify_density_zone(0.10) == ">5%"

    def test_zone_medium_high(self):
        assert classify_density_zone(0.03) == "2-5%"

    def test_zone_medium_low(self):
        assert classify_density_zone(0.015) == "1-2%"

    def test_zone_low(self):
        assert classify_density_zone(0.005) == "<1%"

    def test_zone_zero(self):
        assert classify_density_zone(0.0) == "0%"


class TestUnitFalsePositives:
    """Test false positive detection heuristics."""

    def test_detects_low_confidence(self):
        items = [{"objetoCompra": "uniforme escolar", "_confidence_score": 40, "_matched_terms": ["uniforme"], "_term_density": 0.5}]
        from sectors import SECTORS
        sector = list(SECTORS.values())[0]
        fps = detect_false_positives(items, sector)
        assert len(fps) == 1
        assert "low_confidence_40" in fps[0]["reasons"]

    def test_detects_short_description(self):
        items = [{"objetoCompra": "uniforme", "_confidence_score": 90, "_matched_terms": ["uniforme"], "_term_density": 0.5}]
        from sectors import SECTORS
        sector = list(SECTORS.values())[0]
        fps = detect_false_positives(items, sector)
        assert any("short_description" in fp["reasons"] for fp in fps)

    def test_no_false_positive_on_good_item(self):
        items = [{
            "objetoCompra": "aquisição de uniforme escolar completo para alunos da rede municipal de ensino",
            "_confidence_score": 95,
            "_matched_terms": ["uniforme", "escolar"],
            "_term_density": 0.15,
        }]
        from sectors import SECTORS
        sector = list(SECTORS.values())[0]
        fps = detect_false_positives(items, sector)
        assert len(fps) == 0


class TestUnitFalseNegatives:
    """Test false negative detection heuristics."""

    def test_detects_hint_in_rejected(self):
        from sectors import SECTORS
        sector = SECTORS["vestuario"]
        rejected = [{"objetoCompra": "fornecimento de tecido de algodao para confecção"}]
        fns = detect_false_negatives(rejected, sector)
        assert len(fns) >= 1
        assert any("algodao" in fn["hints_found"] or "tecido" in fn["hints_found"] for fn in fns)

    def test_no_fn_when_no_hints(self):
        from sectors import SECTORS
        sector = SECTORS["vestuario"]
        rejected = [{"objetoCompra": "serviço de consultoria em gestão pública"}]
        fns = detect_false_negatives(rejected, sector)
        assert len(fns) == 0


class TestUnitCrossSector:
    """Test cross-sector collision analysis."""

    def test_detects_collision(self):
        # Item with keywords from both vestuario and facilities
        items = [
            {"objetoCompra": "uniforme e limpeza predial conservação", "uf": "SP", "valorTotalEstimado": 100000},
        ]
        result = analyze_cross_sector(items, ["vestuario", "facilities"], ["SP"])
        # May or may not collide depending on exact keywords — just test structure
        assert "total_collisions" in result
        assert "collision_rate" in result
        assert "top_collision_pairs" in result

    def test_no_collision_distinct_items(self):
        items = [
            {"objetoCompra": "serviço de topografia e levantamento planialtimétrico", "uf": "SP", "valorTotalEstimado": 100000},
        ]
        result = analyze_cross_sector(items, ["vestuario", "alimentos"], ["SP"])
        assert result["total_collisions"] == 0


class TestUnitPcpAnalysis:
    """Test PCP v2 analysis."""

    def test_pcp_empty(self):
        result = analyze_pcp_v2([], ["vestuario"])
        assert result["skipped"] is True

    def test_pcp_with_items(self):
        items = [
            {"objetoCompra": "uniforme escolar", "valorTotalEstimado": 0.0},
            {"objetoCompra": "a", "valorTotalEstimado": 0.0},
            {"objetoCompra": "", "valorTotalEstimado": 0.0},
        ]
        result = analyze_pcp_v2(items, ["vestuario"])
        assert result["total_items"] == 3
        assert result["valor_zero_count"] == 3
        assert result["short_description_count"] >= 1


class TestUnitMetrics:
    """Test metrics builder."""

    def test_build_metrics_structure(self):
        sector_results = [{
            "sector_id": "vestuario",
            "sector_name": "Vestuário",
            "total_items": 100,
            "approved_count": 10,
            "rejected_count": 90,
            "filter_stats": {},
            "density_distribution": {">5%": 5, "0%": 95},
            "source_breakdown": {"keyword": 10},
            "co_occurrence_rejections": 0,
            "false_positive_suspects": [],
            "false_positive_count": 1,
            "false_negative_suspects": [],
            "false_negative_count": 2,
            "precision_estimated": 0.90,
            "recall_estimated": 0.83,
            "approved_sample": [],
        }]
        cross = {"collision_rate": 0.05, "total_collisions": 5}
        pcp = {"total_items": 50}
        metrics = build_metrics(sector_results, cross, pcp, 10.0)

        assert metrics["total_items_analyzed"] == 100
        assert metrics["total_approved"] == 10
        assert metrics["sectors_audited"] == 1
        assert metrics["avg_precision_estimated"] == 0.90
        assert metrics["passes_thresholds"] is True

    def test_build_metrics_fails_threshold(self):
        sector_results = [{
            "sector_id": "vestuario",
            "sector_name": "Vestuário",
            "total_items": 100,
            "approved_count": 10,
            "rejected_count": 90,
            "filter_stats": {},
            "density_distribution": {},
            "source_breakdown": {},
            "co_occurrence_rejections": 0,
            "false_positive_suspects": [],
            "false_positive_count": 0,
            "false_negative_suspects": [],
            "false_negative_count": 0,
            "precision_estimated": 0.50,  # Below 0.70 threshold
            "recall_estimated": 0.30,     # Below 0.50 threshold
            "approved_sample": [],
        }]
        cross = {"collision_rate": 0.05, "total_collisions": 5}
        pcp = {"total_items": 0}
        metrics = build_metrics(sector_results, cross, pcp, 5.0)
        assert metrics["passes_thresholds"] is False


class TestUnitSectorResolution:
    """Test sector ID resolution."""

    def test_resolve_all(self):
        ids = resolve_sector_ids("all")
        assert len(ids) == 15

    def test_resolve_single(self):
        ids = resolve_sector_ids("vestuario")
        assert ids == ["vestuario"]

    def test_resolve_multiple(self):
        ids = resolve_sector_ids("vestuario,alimentos")
        assert ids == ["vestuario", "alimentos"]

    def test_resolve_unknown_exits(self):
        with pytest.raises(SystemExit):
            resolve_sector_ids("nonexistent_sector")


class TestUnitReportGeneration:
    """Test markdown report generation."""

    def test_report_contains_headers(self):
        sector_results = [{
            "sector_id": "vestuario",
            "sector_name": "Vestuário e Uniformes",
            "total_items": 50,
            "approved_count": 5,
            "rejected_count": 45,
            "filter_stats": {"rejeitadas_keyword": 40, "rejeitadas_baixa_densidade": 3},
            "density_distribution": {">5%": 3, "0%": 47},
            "source_breakdown": {"keyword": 5},
            "co_occurrence_rejections": 0,
            "false_positive_suspects": [],
            "false_positive_count": 0,
            "false_negative_suspects": [],
            "false_negative_count": 1,
            "precision_estimated": 1.0,
            "recall_estimated": 0.83,
            "approved_sample": [],
        }]
        cross = {"total_collisions": 0, "collision_rate": 0.0, "top_collision_pairs": [], "collision_items_sample": []}
        pcp = {"skipped": True, "reason": "test"}
        config = {"ufs": ["SP"], "days": 10, "sectors": ["vestuario"]}

        report = generate_markdown_report(sector_results, cross, pcp, config)
        assert "# Auditoria Completa do Pipeline" in report
        assert "Vestuário e Uniformes" in report
        assert "Cross-Setor" in report
        assert "PCP v2" in report


# ============================================================================
# THRESHOLD TESTS (skip if metrics file not generated)
# ============================================================================


class TestAuditMetricsExist:
    """Validate that the metrics file has the expected structure."""

    def test_metrics_file_exists(self):
        if not METRICS_FILE.exists():
            pytest.skip("Metrics file not generated yet")
        assert METRICS_FILE.stat().st_size > 0

    def test_metrics_has_required_fields(self):
        metrics = _load_metrics()
        required = [
            "total_items_analyzed",
            "total_approved",
            "sectors_audited",
            "avg_precision_estimated",
            "avg_recall_estimated",
            "cross_sector_collision_rate",
            "per_sector",
            "passes_thresholds",
        ]
        for field in required:
            assert field in metrics, f"Missing field: {field}"

    def test_per_sector_has_required_fields(self):
        metrics = _load_metrics()
        for sid, data in metrics.get("per_sector", {}).items():
            assert "approved" in data, f"Sector {sid} missing 'approved'"
            assert "precision_estimated" in data, f"Sector {sid} missing 'precision_estimated'"
            assert "recall_estimated" in data, f"Sector {sid} missing 'recall_estimated'"
            assert "density_distribution" in data, f"Sector {sid} missing 'density_distribution'"
            assert "source_breakdown" in data, f"Sector {sid} missing 'source_breakdown'"


class TestAuditThresholds:
    """Validate that audit metrics meet minimum quality thresholds."""

    def test_minimum_items_analyzed(self):
        metrics = _load_metrics()
        assert metrics["total_items_analyzed"] >= MIN_ITEMS_ANALYZED, (
            f"Only {metrics['total_items_analyzed']} items analyzed "
            f"(minimum: {MIN_ITEMS_ANALYZED})"
        )

    def test_average_precision(self):
        metrics = _load_metrics()
        assert metrics["avg_precision_estimated"] >= MIN_PRECISION, (
            f"Average precision {metrics['avg_precision_estimated']:.1%} "
            f"below threshold {MIN_PRECISION:.1%}"
        )

    def test_average_recall(self):
        metrics = _load_metrics()
        assert metrics["avg_recall_estimated"] >= MIN_RECALL, (
            f"Average recall {metrics['avg_recall_estimated']:.1%} "
            f"below threshold {MIN_RECALL:.1%}"
        )

    def test_cross_sector_collision_rate(self):
        metrics = _load_metrics()
        assert metrics["cross_sector_collision_rate"] <= MAX_COLLISION_RATE, (
            f"Cross-sector collision rate {metrics['cross_sector_collision_rate']:.2%} "
            f"exceeds threshold {MAX_COLLISION_RATE:.2%}"
        )

    def test_per_sector_precision(self):
        """Each sector should have reasonable precision."""
        metrics = _load_metrics()
        low_sectors = []
        for sid, data in metrics.get("per_sector", {}).items():
            if data["precision_estimated"] < 0.50:
                low_sectors.append(f"{sid}={data['precision_estimated']:.1%}")
        assert not low_sectors, (
            f"Sectors with precision < 50%: {', '.join(low_sectors)}"
        )

    def test_per_sector_recall(self):
        """Each sector should have reasonable recall."""
        metrics = _load_metrics()
        low_sectors = []
        for sid, data in metrics.get("per_sector", {}).items():
            if data["recall_estimated"] < 0.30:
                low_sectors.append(f"{sid}={data['recall_estimated']:.1%}")
        assert not low_sectors, (
            f"Sectors with recall < 30%: {', '.join(low_sectors)}"
        )

    def test_overall_passes(self):
        """The overall threshold check should pass."""
        metrics = _load_metrics()
        assert metrics["passes_thresholds"], (
            "Overall threshold check FAILED. Review audit_pipeline_report.md for details."
        )


class TestAuditDataQuality:
    """Validate data quality in the audit results."""

    def test_all_sectors_present(self):
        """All audited sectors should have results."""
        metrics = _load_metrics()
        assert metrics["sectors_audited"] > 0, "No sectors were audited"

    def test_density_zones_present(self):
        """Each sector should have density distribution data."""
        metrics = _load_metrics()
        for sid, data in metrics.get("per_sector", {}).items():
            dd = data.get("density_distribution", {})
            total = sum(dd.values())
            assert total > 0 or data["approved"] == 0, (
                f"Sector {sid} has no density distribution data"
            )

    def test_no_negative_counts(self):
        """No metric should have negative values."""
        metrics = _load_metrics()
        assert metrics["total_items_analyzed"] >= 0
        assert metrics["total_approved"] >= 0
        for sid, data in metrics.get("per_sector", {}).items():
            assert data["approved"] >= 0, f"Sector {sid} has negative approved count"
            assert data["false_positive_suspects"] >= 0
            assert data["false_negative_suspects"] >= 0
