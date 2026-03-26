"""Unit tests for ingestion/loader.py — bulk_upsert, purge_old_bids, _chunk."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from ingestion.loader import _chunk, bulk_upsert, purge_old_bids

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

SAMPLE_PNCP_ITEM = {
    "numeroControlePNCP": "12345678000100-1-000001/2026",
    "objetoCompra": "Contratação de empresa para execução de obra de pavimentação asfáltica",
    "valorTotalEstimado": 1500000.00,
    "modalidadeId": 6,
    "modalidadeNome": "Pregão - Eletrônico",
    "situacaoCompraNome": "Divulgada",
    "dataPublicacaoPncp": "2026-03-20T10:00:00Z",
    "dataAberturaProposta": "2026-04-01T09:00:00Z",
    "dataEncerramentoProposta": "2026-04-01T18:00:00Z",
    "linkSistemaOrigem": "https://compras.gov.br/edital/12345",
    "orgaoEntidade": {
        "razaoSocial": "Prefeitura Municipal de São Paulo",
        "cnpj": "12345678000100",
        "esferaId": "M",
    },
    "unidadeOrgao": {
        "ufSigla": "SP",
        "municipioNome": "São Paulo",
        "codigoMunicipioIbge": "3550308",
        "nomeUnidade": "Secretaria de Infraestrutura",
    },
}


def _make_record(pncp_id: str) -> dict:
    """Build a minimal transformed record for loader tests."""
    return {
        "pncp_id": pncp_id,
        "objeto_compra": "Obra de pavimentação",
        "valor_total_estimado": 100000.00,
        "raw_payload": SAMPLE_PNCP_ITEM,
    }


def _make_mock_supabase(inserted: int = 5, updated: int = 2, unchanged: int = 3) -> MagicMock:
    """Build a mock Supabase client that returns the given RPC counts."""
    mock_sb = MagicMock()
    mock_sb.rpc.return_value.execute.return_value.data = [
        {"inserted": inserted, "updated": updated, "unchanged": unchanged}
    ]
    return mock_sb


# ---------------------------------------------------------------------------
# bulk_upsert
# ---------------------------------------------------------------------------


class TestBulkUpsert:
    """Tests for bulk_upsert()."""

    @pytest.mark.asyncio
    @patch("ingestion.loader.get_supabase")
    async def test_empty_records_returns_zero_counts(self, mock_get_sb):
        """Empty records list must return all-zero dict without calling Supabase."""
        result = await bulk_upsert([])
        mock_get_sb.assert_not_called()
        assert result == {"inserted": 0, "updated": 0, "unchanged": 0, "total": 0, "batches": 0}

    @pytest.mark.asyncio
    @patch("ingestion.loader.get_supabase")
    async def test_single_batch_aggregates_counts(self, mock_get_sb):
        """A small batch must produce correct aggregated totals."""
        mock_get_sb.return_value = _make_mock_supabase(inserted=5, updated=2, unchanged=3)
        records = [_make_record(f"pncp_{i}") for i in range(10)]

        result = await bulk_upsert(records)

        assert result["inserted"] == 5
        assert result["updated"] == 2
        assert result["unchanged"] == 3
        assert result["total"] == 10
        assert result["batches"] == 1

    @pytest.mark.asyncio
    @patch("ingestion.loader.get_supabase")
    async def test_large_batch_split_into_chunks(self, mock_get_sb):
        """601 records with batch_size=500 must result in 2 RPC calls."""
        mock_sb = _make_mock_supabase(inserted=10, updated=0, unchanged=0)
        mock_get_sb.return_value = mock_sb

        records = [_make_record(f"pncp_{i}") for i in range(601)]
        result = await bulk_upsert(records, batch_size=500)

        # Two batches: 500 + 101
        assert mock_sb.rpc.call_count == 2
        assert result["batches"] == 2
        assert result["total"] == 601

    @pytest.mark.asyncio
    @patch("ingestion.loader.get_supabase")
    async def test_multi_batch_counts_aggregated(self, mock_get_sb):
        """Counts from multiple batches must be summed correctly."""
        mock_sb = _make_mock_supabase(inserted=3, updated=1, unchanged=1)
        mock_get_sb.return_value = mock_sb

        # 6 records split into 3 batches of 2
        records = [_make_record(f"pncp_{i}") for i in range(6)]
        result = await bulk_upsert(records, batch_size=2)

        assert result["batches"] == 3
        assert result["inserted"] == 9   # 3 * 3
        assert result["updated"] == 3    # 1 * 3
        assert result["unchanged"] == 3  # 1 * 3
        assert result["total"] == 6

    @pytest.mark.asyncio
    @patch("ingestion.loader.get_supabase")
    async def test_rpc_error_in_one_batch_continues_others(self, mock_get_sb, caplog):
        """An RPC error in batch 1 must not prevent batch 2 from running."""
        mock_sb = MagicMock()
        # First call raises, second succeeds
        mock_sb.rpc.return_value.execute.side_effect = [
            RuntimeError("DB timeout"),
            MagicMock(data=[{"inserted": 2, "updated": 0, "unchanged": 0}]),
        ]
        mock_get_sb.return_value = mock_sb

        records = [_make_record(f"pncp_{i}") for i in range(4)]
        with caplog.at_level(logging.ERROR, logger="ingestion.loader"):
            result = await bulk_upsert(records, batch_size=2)

        # Second batch succeeds
        assert result["inserted"] == 2
        assert result["batches"] == 1  # Only the successful batch counted
        assert any("failed" in msg.lower() for msg in caplog.messages)

    @pytest.mark.asyncio
    @patch("ingestion.loader.get_supabase")
    async def test_rpc_called_with_correct_params(self, mock_get_sb):
        """RPC must be called with 'upsert_pncp_raw_bids' and p_records key."""
        mock_get_sb.return_value = _make_mock_supabase()
        records = [_make_record("pncp_1")]

        await bulk_upsert(records)

        mock_get_sb.return_value.rpc.assert_called_once()
        rpc_name, rpc_kwargs = mock_get_sb.return_value.rpc.call_args
        assert rpc_name[0] == "upsert_pncp_raw_bids"
        assert "p_records" in rpc_name[1]

    @pytest.mark.asyncio
    @patch("ingestion.loader.get_supabase")
    async def test_empty_rpc_response_treated_as_zero_counts(self, mock_get_sb):
        """RPC returning empty list must not crash — counts default to 0."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = []
        mock_get_sb.return_value = mock_sb

        records = [_make_record("pncp_1")]
        result = await bulk_upsert(records)

        assert result["inserted"] == 0
        assert result["updated"] == 0
        assert result["unchanged"] == 0
        assert result["batches"] == 1

    @pytest.mark.asyncio
    @patch("ingestion.loader.get_supabase")
    async def test_returns_dict_with_all_expected_keys(self, mock_get_sb):
        """Result must contain all five expected keys."""
        mock_get_sb.return_value = _make_mock_supabase()
        result = await bulk_upsert([_make_record("pncp_x")])
        assert set(result.keys()) == {"inserted", "updated", "unchanged", "total", "batches"}


# ---------------------------------------------------------------------------
# purge_old_bids
# ---------------------------------------------------------------------------


class TestPurgeOldBids:
    """Tests for purge_old_bids()."""

    @pytest.mark.asyncio
    @patch("ingestion.loader.get_supabase")
    async def test_calls_purge_rpc_with_correct_param(self, mock_get_sb):
        """Must call the purge_old_bids RPC with p_retention_days."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = [{"count": 42}]
        mock_get_sb.return_value = mock_sb

        await purge_old_bids(retention_days=15)

        mock_sb.rpc.assert_called_once_with("purge_old_bids", {"p_retention_days": 15})

    @pytest.mark.asyncio
    @patch("ingestion.loader.get_supabase")
    async def test_uses_default_retention_days(self, mock_get_sb):
        """Default retention_days=12 must be passed to RPC when not specified."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = 0
        mock_get_sb.return_value = mock_sb

        await purge_old_bids()

        mock_sb.rpc.assert_called_once_with("purge_old_bids", {"p_retention_days": 12})

    @pytest.mark.asyncio
    @patch("ingestion.loader.get_supabase")
    async def test_returns_deleted_count_from_scalar_data(self, mock_get_sb):
        """When RPC returns scalar int, result must equal that int."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.return_value.data = 37
        mock_get_sb.return_value = mock_sb

        deleted = await purge_old_bids(retention_days=10)
        assert deleted == 37

    @pytest.mark.asyncio
    @patch("ingestion.loader.get_supabase")
    async def test_returns_zero_on_rpc_error(self, mock_get_sb, caplog):
        """Exceptions from RPC must be swallowed and return 0."""
        mock_sb = MagicMock()
        mock_sb.rpc.return_value.execute.side_effect = RuntimeError("connection refused")
        mock_get_sb.return_value = mock_sb

        with caplog.at_level(logging.ERROR, logger="ingestion.loader"):
            result = await purge_old_bids()

        assert result == 0
        assert any("failed" in msg.lower() or "purge" in msg.lower() for msg in caplog.messages)


# ---------------------------------------------------------------------------
# _chunk (private helper — worth direct testing)
# ---------------------------------------------------------------------------


class TestChunk:
    """Tests for the _chunk helper."""

    def test_exact_multiple(self):
        assert _chunk([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]

    def test_last_chunk_smaller(self):
        result = _chunk([1, 2, 3, 4, 5], 3)
        assert result == [[1, 2, 3], [4, 5]]

    def test_empty_list(self):
        assert _chunk([], 10) == []

    def test_single_item(self):
        assert _chunk(["a"], 100) == [["a"]]

    def test_chunk_size_one(self):
        assert _chunk([1, 2, 3], 1) == [[1], [2], [3]]

    def test_list_larger_than_chunk_size(self):
        lst = list(range(550))
        chunks = _chunk(lst, 500)
        assert len(chunks) == 2
        assert len(chunks[0]) == 500
        assert len(chunks[1]) == 50
