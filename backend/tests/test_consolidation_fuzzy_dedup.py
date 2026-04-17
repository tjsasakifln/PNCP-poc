"""STORY-5.3 (TD-SYS-013): Fuzzy dedup parameterization tests.

Validates the three acceptance criteria added on top of the pre-existing
DeduplicationEngine (consolidation/dedup.py):

- AC1: fuzzy layers still catch near-duplicates that exact dedup misses.
- AC2: threshold is configurable via DEDUP_FUZZY_THRESHOLD env / constructor.
- AC3: smartlic_dedup_fuzzy_hits_total is emitted per layer on each removal.
- Flag: DEDUP_FUZZY_ENABLED=False skips fuzzy/process/title-prefix layers.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from consolidation.dedup import DeduplicationEngine
from unified_schemas.unified import UnifiedProcurement


def _make_record(
    *,
    source_id: str,
    source_name: str = "PNCP",
    cnpj: str = "83102798000100",
    objeto: str = "Pavimentação da rua Reinhold Schroeder",
    valor: float = 9_500_000.0,
) -> UnifiedProcurement:
    return UnifiedProcurement(
        source_id=source_id,
        source_name=source_name,
        cnpj_orgao=cnpj,
        numero_edital=source_id.split("-")[-1].split("/")[0] or "000001",
        ano="2026",
        objeto=objeto,
        valor_estimado=valor,
        uf="SC",
        orgao="Prefeitura Municipal de Indaial",
        data_publicacao=datetime(2026, 3, 20, 10, 0, 0),
    )


def _metric_value(layer: str) -> float:
    """Read current value of DEDUP_FUZZY_HITS{layer=...} for assertion.

    Reads from the Counter's child directly via `.labels(layer=...)` — calling
    `.labels(...)` on a labelled metric returns (and creates if missing) the
    child Counter. Child Counter exposes `._value.get()` on the default backend.
    """
    from metrics import DEDUP_FUZZY_HITS

    child = DEDUP_FUZZY_HITS.labels(layer=layer)
    # prometheus_client Counter stores value under _value.get() (multiprocess-safe)
    try:
        return child._value.get()
    except AttributeError:
        # Defensive: fall back to collect() if internal API changes.
        for metric in DEDUP_FUZZY_HITS.collect():
            for sample in metric.samples:
                if (
                    sample.name.endswith("_total")
                    and sample.labels.get("layer") == layer
                ):
                    return sample.value
        return 0.0


@pytest.fixture
def adapters():
    """Minimal adapters dict — PNCP priority 1, PCP priority 2."""
    pncp = MagicMock()
    pncp.code = "PNCP"
    pncp.metadata = MagicMock(priority=1)
    pcp = MagicMock()
    pcp.code = "PCP"
    pcp.metadata = MagicMock(priority=2)
    return {"PNCP": pncp, "PCP": pcp}


class TestFuzzyDedupThresholdConfig:
    """AC2: Threshold is injectable, respected across fuzzy layers.

    NOTE: source_id must NOT match PNCP pattern (r"-\\d{4,6}/\\d{4}$") so we
    isolate the Jaccard fuzzy layer from the process_number layer, which runs
    with its own 0.80 blocking threshold on (cnpj, year) groups.
    """

    def test_strict_threshold_keeps_near_duplicates(self, adapters):
        """With threshold 0.99 the fuzzy layer skips 0.85-similar records."""
        engine = DeduplicationEngine(
            adapters=adapters, fuzzy_enabled=True, fuzzy_threshold=0.99
        )
        r1 = _make_record(
            source_id="PCP-abc-001",
            objeto="Pavimentação da rua Reinhold Schroeder",
        )
        r2 = _make_record(
            source_id="PCP-abc-002",
            objeto="Pavimentação da rua Reinhold Schroeder (revisado)",
        )
        out = engine.run([r1, r2])
        assert len(out) == 2, "Strict threshold should preserve both records"

    def test_lenient_threshold_removes_near_duplicates(self, adapters):
        """With default 0.85 + adjacent edital numbers, near-duplicate collapses."""
        engine = DeduplicationEngine(
            adapters=adapters, fuzzy_enabled=True, fuzzy_threshold=0.85
        )
        r1 = _make_record(
            source_id="83102798000100-1-000100/2026",
            objeto="Pavimentação da rua Reinhold Schroeder",
        )
        r2 = _make_record(
            source_id="83102798000100-1-000101/2026",
            objeto="Pavimentação da rua Reinhold Schroeder (revisado)",
        )
        out = engine.run([r1, r2])
        assert len(out) == 1, "Near-duplicate should collapse at default threshold"


class TestFuzzyDedupDisabledFlag:
    """AC: DEDUP_FUZZY_ENABLED=False bypasses fuzzy/process/title-prefix layers."""

    def test_disabled_flag_keeps_near_duplicates(self, adapters):
        engine = DeduplicationEngine(
            adapters=adapters, fuzzy_enabled=False, fuzzy_threshold=0.85
        )
        r1 = _make_record(
            source_id="83102798000100-1-000100/2026",
            objeto="Pavimentação da rua Reinhold Schroeder",
        )
        r2 = _make_record(
            source_id="83102798000100-1-000101/2026",
            objeto="Pavimentação da rua Reinhold Schroeder",
        )
        out = engine.run([r1, r2])
        assert len(out) == 2, "Fuzzy disabled should leave near-dups untouched"

    def test_disabled_flag_still_runs_exact_dedup(self, adapters):
        """Exact dedup (source_id + dedup_key) still runs regardless of fuzzy flag."""
        engine = DeduplicationEngine(
            adapters=adapters, fuzzy_enabled=False, fuzzy_threshold=0.85
        )
        r1 = _make_record(source_id="PNCP-exact-001")
        r2 = _make_record(source_id="PNCP-exact-001")  # same source_id
        out = engine.run([r1, r2])
        assert len(out) == 1, "Same source_id must dedup even with fuzzy disabled"


class TestFuzzyDedupMetrics:
    """AC3: smartlic_dedup_fuzzy_hits_total emitted per layer on removal."""

    def test_counter_increments_on_process_number_hit(self, adapters):
        """PNCP-style adjacent edital numbers trip the process_number layer."""
        before = _metric_value("process_number")
        engine = DeduplicationEngine(
            adapters=adapters, fuzzy_enabled=True, fuzzy_threshold=0.85
        )
        r1 = _make_record(
            source_id="83102798000100-1-000100/2026",
            objeto="Pavimentação da rua Reinhold Schroeder",
        )
        r2 = _make_record(
            source_id="83102798000100-1-000101/2026",
            objeto="Pavimentação da rua Reinhold Schroeder (revisado)",
        )
        engine.run([r1, r2])
        after = _metric_value("process_number")
        assert after > before, (
            "process_number layer counter must increment on adjacent PNCP edital "
            "number collapse"
        )

    def test_counter_stays_flat_without_hit(self, adapters):
        before = _metric_value("fuzzy")
        engine = DeduplicationEngine(
            adapters=adapters, fuzzy_enabled=True, fuzzy_threshold=0.85
        )
        r1 = _make_record(
            source_id="PNCP-a", objeto="Serviço de limpeza hospitalar"
        )
        r2 = _make_record(
            source_id="PNCP-b", objeto="Construção de ponte rodoviária"
        )
        engine.run([r1, r2])
        after = _metric_value("fuzzy")
        assert after == before, "No near-dup: counter must stay flat"
