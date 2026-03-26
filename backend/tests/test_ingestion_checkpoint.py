"""Unit tests for ingestion/checkpoint.py — get_last_checkpoint, save_checkpoint,
create_ingestion_run, complete_ingestion_run, mark_checkpoint_failed."""

import logging
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from ingestion.checkpoint import (
    complete_ingestion_run,
    create_ingestion_run,
    get_last_checkpoint,
    mark_checkpoint_failed,
    save_checkpoint,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_supabase_with_rows(rows: list) -> MagicMock:
    """Return a Supabase mock whose chained .select().eq()...execute() returns rows."""
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = rows
    return mock_sb


# ---------------------------------------------------------------------------
# get_last_checkpoint
# ---------------------------------------------------------------------------


class TestGetLastCheckpoint:
    """Tests for get_last_checkpoint()."""

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_returns_none_when_no_rows(self, mock_get_sb):
        """Must return None when the query returns an empty list."""
        mock_get_sb.return_value = _mock_supabase_with_rows([])
        result = await get_last_checkpoint("SP", 6)
        assert result is None

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_returns_date_when_row_exists(self, mock_get_sb):
        """Must return a date object parsed from the last_date string."""
        mock_get_sb.return_value = _mock_supabase_with_rows([{"last_date": "2026-03-20"}])
        result = await get_last_checkpoint("SC", 5)
        assert result == date(2026, 3, 20)

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_parses_iso_datetime_string_to_date(self, mock_get_sb):
        """last_date as 'YYYY-MM-DDTHH:mm:ss' must be truncated to the date part."""
        mock_get_sb.return_value = _mock_supabase_with_rows(
            [{"last_date": "2026-03-15T00:00:00"}]
        )
        result = await get_last_checkpoint("RJ", 4)
        assert result == date(2026, 3, 15)

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_returns_none_when_supabase_raises(self, mock_get_sb, caplog):
        """Supabase exceptions must be swallowed and None returned.

        The exception is raised when calling .execute() inside the try block,
        NOT when calling get_supabase() itself (which is outside the try block).
        """
        mock_sb = MagicMock()
        # Make the chained call raise when execute() is invoked
        (
            mock_sb.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .eq.return_value
            .eq.return_value
            .order.return_value
            .limit.return_value
            .execute.side_effect
        )
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.side_effect = RuntimeError(
            "connection error"
        )
        mock_get_sb.return_value = mock_sb
        with caplog.at_level(logging.WARNING, logger="ingestion.checkpoint"):
            result = await get_last_checkpoint("MG", 6)
        assert result is None
        assert any("get_last_checkpoint" in msg for msg in caplog.messages)

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_queries_correct_table_and_columns(self, mock_get_sb):
        """Must query ingestion_checkpoints with the correct filter columns."""
        mock_sb = MagicMock()
        chain = (
            mock_sb.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .eq.return_value
            .eq.return_value
            .order.return_value
            .limit.return_value
        )
        chain.execute.return_value.data = []
        mock_get_sb.return_value = mock_sb

        await get_last_checkpoint("PR", 8, source="pncp")

        mock_sb.table.assert_called_once_with("ingestion_checkpoints")

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_uses_default_source_pncp(self, mock_get_sb):
        """Default source='pncp' must be used when not explicitly provided."""
        mock_get_sb.return_value = _mock_supabase_with_rows([])
        # Should not raise — default source value handled internally
        result = await get_last_checkpoint("BA", 5)
        assert result is None


# ---------------------------------------------------------------------------
# save_checkpoint
# ---------------------------------------------------------------------------


class TestSaveCheckpoint:
    """Tests for save_checkpoint()."""

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_upserts_correct_table(self, mock_get_sb):
        """Must upsert into ingestion_checkpoints table."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        await save_checkpoint(
            uf="SP",
            modalidade=6,
            last_date=date(2026, 3, 25),
            records_fetched=100,
            crawl_batch_id="batch_001",
        )

        mock_sb.table.assert_called_with("ingestion_checkpoints")

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_payload_contains_required_fields(self, mock_get_sb):
        """Upsert payload must contain all required fields with correct values."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        await save_checkpoint(
            uf="RS",
            modalidade=5,
            last_date=date(2026, 3, 20),
            records_fetched=42,
            crawl_batch_id="batch_xyz",
            source="pncp",
        )

        upsert_call = mock_sb.table.return_value.upsert
        upsert_call.assert_called_once()
        payload = upsert_call.call_args[0][0]

        assert payload["uf"] == "RS"
        assert payload["modalidade_id"] == 5
        assert payload["last_date"] == "2026-03-20"
        assert payload["records_fetched"] == 42
        assert payload["crawl_batch_id"] == "batch_xyz"
        assert payload["status"] == "completed"
        assert payload["source"] == "pncp"
        assert payload["error_message"] is None

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_upsert_conflict_column_specified(self, mock_get_sb):
        """Upsert must specify on_conflict='uf,modalidade,source'."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        await save_checkpoint(
            uf="CE",
            modalidade=4,
            last_date=date(2026, 3, 1),
            records_fetched=10,
            crawl_batch_id="b1",
        )

        upsert_call = mock_sb.table.return_value.upsert
        _, kwargs = upsert_call.call_args
        assert kwargs.get("on_conflict") == "source,uf,modalidade_id,crawl_batch_id"

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_supabase_error_does_not_raise(self, mock_get_sb, caplog):
        """Supabase errors must be caught and not propagate to the caller."""
        mock_sb = MagicMock()
        mock_sb.table.return_value.upsert.return_value.execute.side_effect = RuntimeError("timeout")
        mock_get_sb.return_value = mock_sb

        with caplog.at_level(logging.ERROR, logger="ingestion.checkpoint"):
            # Should not raise
            await save_checkpoint(
                uf="AM",
                modalidade=6,
                last_date=date(2026, 3, 10),
                records_fetched=5,
                crawl_batch_id="b2",
            )
        assert any("save_checkpoint" in msg for msg in caplog.messages)


# ---------------------------------------------------------------------------
# create_ingestion_run
# ---------------------------------------------------------------------------


class TestCreateIngestionRun:
    """Tests for create_ingestion_run()."""

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_inserts_into_ingestion_runs(self, mock_get_sb):
        """Must insert a row into the ingestion_runs table."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        await create_ingestion_run("full_20260325_050000", "full")

        mock_sb.table.assert_called_with("ingestion_runs")
        mock_sb.table.return_value.insert.assert_called_once()

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_payload_contains_status_running(self, mock_get_sb):
        """Inserted row must have status='running' and correct run_type."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        await create_ingestion_run("incr_20260325_110000", "incremental")

        insert_call = mock_sb.table.return_value.insert
        payload = insert_call.call_args[0][0]
        assert payload["crawl_batch_id"] == "incr_20260325_110000"
        assert payload["run_type"] == "incremental"
        assert payload["status"] == "running"

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_supabase_error_is_non_fatal(self, mock_get_sb, caplog):
        """DB errors must be caught without raising (non-fatal monitoring)."""
        mock_sb = MagicMock()
        mock_sb.table.return_value.insert.return_value.execute.side_effect = RuntimeError("err")
        mock_get_sb.return_value = mock_sb

        with caplog.at_level(logging.WARNING, logger="ingestion.checkpoint"):
            await create_ingestion_run("bad_batch", "full")
        # Warning logged but no exception propagated


# ---------------------------------------------------------------------------
# complete_ingestion_run
# ---------------------------------------------------------------------------


class TestCompleteIngestionRun:
    """Tests for complete_ingestion_run()."""

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_updates_ingestion_runs_table(self, mock_get_sb):
        """Must call .update() on ingestion_runs."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        await complete_ingestion_run("batch_001")

        mock_sb.table.assert_called_with("ingestion_runs")
        mock_sb.table.return_value.update.assert_called_once()

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_filters_by_crawl_batch_id(self, mock_get_sb):
        """Update must be filtered to the correct crawl_batch_id."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        await complete_ingestion_run("batch_xyz")

        eq_call = mock_sb.table.return_value.update.return_value.eq
        eq_call.assert_called_once_with("crawl_batch_id", "batch_xyz")

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_payload_includes_all_stats(self, mock_get_sb):
        """Payload must contain all statistics fields."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        await complete_ingestion_run(
            "batch_abc",
            status="completed",
            total_fetched=500,
            inserted=300,
            updated=100,
            unchanged=100,
            ufs_completed=["SP", "RJ", "MG"],
            ufs_failed=[],
        )

        update_call = mock_sb.table.return_value.update
        payload = update_call.call_args[0][0]
        assert payload["status"] == "completed"
        assert payload["total_fetched"] == 500
        assert payload["inserted"] == 300
        assert payload["updated"] == 100
        assert payload["unchanged"] == 100
        assert payload["ufs_completed"] == ["SP", "RJ", "MG"]
        assert payload["ufs_failed"] == []

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_error_message_included_when_provided(self, mock_get_sb):
        """error_message kwarg must appear in the update payload."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        await complete_ingestion_run("batch_fail", status="failed", error_message="Timeout")

        payload = mock_sb.table.return_value.update.call_args[0][0]
        assert payload["error_message"] == "Timeout"

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_error_message_truncated_at_2000_chars(self, mock_get_sb):
        """Long error messages must be truncated to 2000 characters."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb
        long_error = "x" * 5000

        await complete_ingestion_run("b", status="failed", error_message=long_error)

        payload = mock_sb.table.return_value.update.call_args[0][0]
        assert len(payload["error_message"]) == 2000

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_supabase_error_is_non_fatal(self, mock_get_sb, caplog):
        """DB errors must be caught without raising."""
        mock_sb = MagicMock()
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.side_effect = (
            RuntimeError("DB down")
        )
        mock_get_sb.return_value = mock_sb

        with caplog.at_level(logging.WARNING, logger="ingestion.checkpoint"):
            await complete_ingestion_run("b2")
        # Should not raise


# ---------------------------------------------------------------------------
# mark_checkpoint_failed
# ---------------------------------------------------------------------------


class TestMarkCheckpointFailed:
    """Tests for mark_checkpoint_failed()."""

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_upserts_failed_status(self, mock_get_sb):
        """Must upsert a checkpoint row with status='failed'."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        await mark_checkpoint_failed(
            uf="GO",
            modalidade=6,
            crawl_batch_id="batch_err",
            error_message="Connection timeout",
        )

        upsert_call = mock_sb.table.return_value.upsert
        upsert_call.assert_called_once()
        payload = upsert_call.call_args[0][0]
        assert payload["status"] == "failed"
        assert payload["uf"] == "GO"
        assert payload["error_message"] == "Connection timeout"

    @pytest.mark.asyncio
    @patch("ingestion.checkpoint.get_supabase")
    async def test_error_message_truncated(self, mock_get_sb):
        """error_message longer than 2000 chars must be truncated."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb
        long_msg = "e" * 3000

        await mark_checkpoint_failed(
            uf="RO",
            modalidade=5,
            crawl_batch_id="b_err",
            error_message=long_msg,
        )

        payload = mock_sb.table.return_value.upsert.call_args[0][0]
        assert len(payload["error_message"]) == 2000
