"""Regression tests for Prometheus label usage bugs — commit 02325b8d.

Two bugs were fixed that caused datalake searches to fall back to slow live API:

1. BIDS_PROCESSED_TOTAL.inc() called without required `source` label
   -> ValueError: "counter metric is missing label values"
   -> except clause falls back to live API -> timeout on large queries

2. PostgREST caps RPC results at 1000 rows per call.
   -> Multi-UF queries (PR+SC+RS) were silently truncated.
   -> Fix: per-UF pagination (one RPC call per UF).

This file ensures neither regression is reintroduced.
"""

import logging
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# ============================================================================
# Task 1: BIDS_PROCESSED_TOTAL must be called with .labels(source=...)
# ============================================================================


class TestBidsProcessedTotalLabel:
    """Regression: BIDS_PROCESSED_TOTAL.inc() without .labels() crashes pipeline."""

    @pytest.mark.timeout(30)
    def test_bids_processed_total_exists(self):
        """BIDS_PROCESSED_TOTAL counter is defined in the metrics module."""
        import metrics

        assert hasattr(metrics, "BIDS_PROCESSED_TOTAL")

    @pytest.mark.timeout(30)
    def test_bids_processed_requires_source_label(self):
        """BIDS_PROCESSED_TOTAL must be called with .labels(source=...) — regression for 02325b8d.

        Before the fix, pipeline/stages/execute.py called:
            BIDS_PROCESSED_TOTAL.inc(len(ctx.licitacoes_raw))
        which raises ValueError because source label is required.
        After the fix it is:
            BIDS_PROCESSED_TOTAL.labels(source="datalake").inc(...)
        """
        import metrics

        with pytest.raises((ValueError, Exception)):
            metrics.BIDS_PROCESSED_TOTAL.inc()

    @pytest.mark.timeout(30)
    def test_bids_processed_accepts_datalake_label(self):
        """BIDS_PROCESSED_TOTAL.labels(source='datalake').inc() must not raise."""
        import metrics

        # Should not raise — this is the correct call site in execute.py
        metrics.BIDS_PROCESSED_TOTAL.labels(source="datalake").inc(42)

    @pytest.mark.timeout(30)
    def test_bids_processed_accepts_pncp_label(self):
        """BIDS_PROCESSED_TOTAL.labels(source='pncp').inc() must not raise."""
        import metrics

        metrics.BIDS_PROCESSED_TOTAL.labels(source="pncp").inc(10)

    @pytest.mark.timeout(30)
    def test_bids_processed_has_source_labelname(self):
        """Verify that 'source' is in the declared label names of BIDS_PROCESSED_TOTAL."""
        import metrics

        metric = metrics.BIDS_PROCESSED_TOTAL
        # For real prometheus_client Counter the _labelnames attribute is set
        # For _NoopMetric we just verify .labels() returns self (no-op path OK)
        if hasattr(metric, "_labelnames"):
            assert "source" in metric._labelnames, (
                "BIDS_PROCESSED_TOTAL must declare labelnames=['source']"
            )


# ============================================================================
# Task 1b: Other labeled counters in the pipeline path must also use .labels()
# ============================================================================


class TestOtherLabeledMetricsHaveLabels:
    """Spot-check a sample of labeled metrics that would silently fail if .labels() is skipped."""

    @pytest.mark.timeout(30)
    def test_cache_hits_requires_labels(self):
        """CACHE_HITS counter is labeled (level, freshness) — direct .inc() must fail."""
        import metrics

        with pytest.raises((ValueError, Exception)):
            metrics.CACHE_HITS.inc()

    @pytest.mark.timeout(30)
    def test_cache_hits_accepts_labels(self):
        """CACHE_HITS.labels(level='l1', freshness='fresh') must not raise."""
        import metrics

        metrics.CACHE_HITS.labels(level="l1", freshness="fresh").inc()

    @pytest.mark.timeout(30)
    def test_datalake_truncation_suspected_exists(self):
        """DATALAKE_TRUNCATION_SUSPECTED counter is defined in metrics module."""
        import metrics

        assert hasattr(metrics, "DATALAKE_TRUNCATION_SUSPECTED")

    @pytest.mark.timeout(30)
    def test_datalake_truncation_suspected_accepts_uf_label(self):
        """DATALAKE_TRUNCATION_SUSPECTED.labels(uf='SC').inc() must not raise."""
        import metrics

        metrics.DATALAKE_TRUNCATION_SUSPECTED.labels(uf="SC").inc()

    @pytest.mark.timeout(30)
    def test_datalake_truncation_suspected_requires_uf_label(self):
        """DATALAKE_TRUNCATION_SUSPECTED.inc() without .labels() must raise."""
        import metrics

        with pytest.raises((ValueError, Exception)):
            metrics.DATALAKE_TRUNCATION_SUSPECTED.inc()

    @pytest.mark.timeout(30)
    def test_source_degradation_requires_labels(self):
        """SOURCE_DEGRADATION_TOTAL is labeled — direct .inc() must fail."""
        import metrics

        with pytest.raises((ValueError, Exception)):
            metrics.SOURCE_DEGRADATION_TOTAL.inc()

    @pytest.mark.timeout(30)
    def test_source_degradation_accepts_labels(self):
        """SOURCE_DEGRADATION_TOTAL.labels(source='pncp', reason='timeout') must not raise."""
        import metrics

        metrics.SOURCE_DEGRADATION_TOTAL.labels(source="pncp", reason="timeout").inc()


# ============================================================================
# Task 2: PostgREST 1000-row truncation detection
# ============================================================================


class TestPostgREST1000RowTruncationWarning:
    """Regression: PostgREST silently caps RPC results at 1000 rows.

    query_datalake() must:
    1. Detect when a UF returns exactly 1000 rows (suspected truncation).
    2. Emit a warning log.
    3. Increment DATALAKE_TRUNCATION_SUSPECTED.labels(uf=...).
    4. Still return all rows collected (not drop them).
    """

    @pytest.fixture(autouse=True)
    def _clear_datalake_cache(self):
        """STORY-BTS-009: ``datalake_query`` has a module-level ``_query_cache``
        that persists across test invocations. Without this fixture the failure/
        empty-list assertions leak cached results from prior tests in the class
        ("Cache HIT for N UFs, returning M cached records" visible in captured
        logs). Clear before each test to guarantee fresh RPC paths.
        """
        import datalake_query
        datalake_query._query_cache.clear()
        yield
        datalake_query._query_cache.clear()

    def _make_rows(self, n: int) -> list[dict]:
        """Return n minimal rows that _row_to_normalized() can handle."""
        return [
            {
                "pncp_id": f"uf-{i}",
                "uf": "SC",
                "municipio": "Florianópolis",
                "orgao_razao_social": "Prefeitura SC",
                "orgao_cnpj": "00000000000100",
                "objeto_compra": f"Obra {i}",
                "valor_total_estimado": 50000.0,
                "modalidade_id": 6,
                "modalidade_nome": "Pregão Eletrônico",
                "situacao_compra": "Publicada",
                "data_publicacao": "2026-03-01",
                "data_abertura": "2026-04-01",
                "data_encerramento": "2026-04-01",
                "link_pncp": f"https://pncp.gov.br/{i}",
                "esfera_id": "E",
            }
            for i in range(n)
        ]

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_exactly_1000_rows_logs_warning(self, mock_get_supabase, caplog):
        """When a UF returns exactly 1000 rows, a WARNING must be logged."""
        from datalake_query import query_datalake

        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        rows_1000 = self._make_rows(1000)
        mock_rpc_result = MagicMock()
        mock_rpc_result.data = rows_1000
        mock_sb.rpc.return_value.execute.return_value = mock_rpc_result

        with caplog.at_level(logging.WARNING, logger="datalake_query"):
            result = await query_datalake(
                ufs=["SC"],
                data_inicial="2026-01-01",
                data_final="2026-03-31",
            )

        # Warning must mention truncation / truncamento
        warning_texts = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
        truncation_warnings = [
            t for t in warning_texts
            if "1000" in t or "trunca" in t.lower()
        ]
        assert truncation_warnings, (
            f"Expected a warning about 1000-row truncation; got warnings: {warning_texts}"
        )

        # Must still return the rows (not silently discard)
        assert len(result) == 1000

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_fewer_than_1000_rows_no_truncation_warning(self, mock_get_supabase, caplog):
        """When a UF returns < 1000 rows, NO truncation warning should fire."""
        from datalake_query import query_datalake

        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        rows_999 = self._make_rows(999)
        mock_rpc_result = MagicMock()
        mock_rpc_result.data = rows_999
        mock_sb.rpc.return_value.execute.return_value = mock_rpc_result

        with caplog.at_level(logging.WARNING, logger="datalake_query"):
            result = await query_datalake(
                ufs=["PR"],
                data_inicial="2026-01-01",
                data_final="2026-03-31",
            )

        truncation_warnings = [
            r.message for r in caplog.records
            if r.levelno >= logging.WARNING and ("1000" in r.message or "trunca" in r.message.lower())
        ]
        assert not truncation_warnings, (
            f"Unexpected truncation warning for 999 rows: {truncation_warnings}"
        )
        assert len(result) == 999

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_exactly_1000_rows_increments_metric(self, mock_get_supabase):
        """When a UF returns 1000 rows, DATALAKE_TRUNCATION_SUSPECTED.labels(uf=...).inc() fires."""
        from datalake_query import query_datalake

        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        rows_1000 = self._make_rows(1000)
        mock_rpc_result = MagicMock()
        mock_rpc_result.data = rows_1000
        mock_sb.rpc.return_value.execute.return_value = mock_rpc_result

        with patch("metrics.DATALAKE_TRUNCATION_SUSPECTED") as mock_metric:
            mock_label = MagicMock()
            mock_metric.labels.return_value = mock_label

            await query_datalake(
                ufs=["MG"],
                data_inicial="2026-01-01",
                data_final="2026-03-31",
            )

        mock_metric.labels.assert_called_once_with(uf="MG")
        mock_label.inc.assert_called_once()

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_per_uf_pagination_sends_separate_rpc_calls(self, mock_get_supabase):
        """Per-UF pagination: query_datalake makes one RPC call per UF (not one bulk call).

        Regression: before 02325b8d, a single bulk call was made and results were
        capped at 1000. Now each UF gets its own call so no UF exceeds the cap.
        """
        from datalake_query import query_datalake

        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Each UF returns 5 rows
        mock_rpc_result = MagicMock()
        mock_rpc_result.data = self._make_rows(5)
        mock_sb.rpc.return_value.execute.return_value = mock_rpc_result

        ufs = ["SC", "PR", "RS"]
        result = await query_datalake(
            ufs=ufs,
            data_inicial="2026-01-01",
            data_final="2026-03-31",
        )

        # One execute() call per UF
        assert mock_sb.rpc.return_value.execute.call_count == len(ufs), (
            f"Expected {len(ufs)} RPC calls (one per UF), "
            f"got {mock_sb.rpc.return_value.execute.call_count}"
        )

        # Total rows = 5 per UF * 3 UFs
        assert len(result) == 15

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_per_uf_rpc_params_contain_single_uf(self, mock_get_supabase):
        """Each per-UF RPC call passes p_ufs=[single_uf] — not the full list."""
        from datalake_query import query_datalake

        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        mock_rpc_result = MagicMock()
        mock_rpc_result.data = self._make_rows(2)
        mock_sb.rpc.return_value.execute.return_value = mock_rpc_result

        await query_datalake(
            ufs=["SC", "PR"],
            data_inicial="2026-01-01",
            data_final="2026-03-31",
        )

        # Collect the p_ufs argument from each call
        calls = mock_sb.rpc.call_args_list
        p_ufs_values = [call[0][1]["p_ufs"] for call in calls]

        assert ["SC"] in p_ufs_values, f"Expected ['SC'] in RPC p_ufs calls, got: {p_ufs_values}"
        assert ["PR"] in p_ufs_values, f"Expected ['PR'] in RPC p_ufs calls, got: {p_ufs_values}"

        # No call should send both UFs at once
        for p_ufs in p_ufs_values:
            assert len(p_ufs) == 1, (
                f"Each RPC call should pass a single UF; got p_ufs={p_ufs}"
            )

    @pytest.mark.external  # STORY-CIG-BACKEND-SWEEP triage row #105: real DNS call a Supabase, httpx.ConnectError em sandbox; mock fixture não intercepta RPC internal path.
    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_failed_uf_does_not_abort_other_ufs(self, mock_get_supabase):
        """If one UF RPC fails, the remaining UFs are still queried (fail-partial)."""
        from datalake_query import query_datalake

        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        good_result = MagicMock()
        good_result.data = self._make_rows(3)

        # First call raises, second succeeds
        mock_sb.rpc.return_value.execute.side_effect = [
            Exception("connection timeout"),
            good_result,
        ]

        result = await query_datalake(
            ufs=["SC", "PR"],
            data_inicial="2026-01-01",
            data_final="2026-03-31",
        )

        # SC failed, PR returned 3 rows — should still return PR's rows
        assert len(result) == 3

    @pytest.mark.external  # STORY-CIG-BACKEND-SWEEP triage row #106: real DNS call a Supabase, httpx.ConnectError em sandbox; mock fixture não intercepta RPC internal path.
    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_all_ufs_fail_returns_empty_list(self, mock_get_supabase):
        """When all UF RPCs fail, query_datalake returns [] (fail-open)."""
        from datalake_query import query_datalake

        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        mock_sb.rpc.return_value.execute.side_effect = Exception("DB down")

        result = await query_datalake(
            ufs=["SC", "PR"],
            data_inicial="2026-01-01",
            data_final="2026-03-31",
        )

        assert result == []

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_supabase_unavailable_returns_empty_list(self, mock_get_supabase):
        """If get_supabase() raises (circuit breaker open), query_datalake returns []."""
        mock_get_supabase.side_effect = Exception("Supabase circuit breaker open")

        from datalake_query import query_datalake

        result = await query_datalake(
            ufs=["SC"],
            data_inicial="2026-01-01",
            data_final="2026-03-31",
        )

        assert result == []


# ============================================================================
# Task 2b: Pipeline execute.py stage uses correct label call site
# ============================================================================


class TestExecuteStageDatalakeMetric:
    """Regression: pipeline/stages/execute.py must call BIDS_PROCESSED_TOTAL with .labels()."""

    @pytest.mark.timeout(30)
    def test_execute_py_calls_labels_before_inc(self):
        """Source code of execute.py must contain .labels(source= — not bare .inc()."""
        import ast
        import inspect
        from pipeline.stages import execute as execute_module

        source = inspect.getsource(execute_module)

        # Must contain the correct pattern
        assert "BIDS_PROCESSED_TOTAL.labels(source=" in source, (
            "execute.py must call BIDS_PROCESSED_TOTAL.labels(source=...) "
            "not BIDS_PROCESSED_TOTAL.inc() directly (regression 02325b8d)"
        )

        # Must NOT contain the bare broken call (without .labels)
        lines = source.splitlines()
        bad_lines = [
            ln for ln in lines
            if "BIDS_PROCESSED_TOTAL.inc(" in ln
            and ".labels(" not in ln.split("BIDS_PROCESSED_TOTAL")[0]  # labels not called before
        ]
        assert not bad_lines, (
            f"Found bare BIDS_PROCESSED_TOTAL.inc() without .labels() in execute.py: {bad_lines}"
        )
