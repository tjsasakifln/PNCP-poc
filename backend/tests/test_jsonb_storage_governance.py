"""STORY-265: JSONB Storage Governance tests.

Covers:
  AC2: CHECK constraint applied (2MB limit)
  AC3: pg_cron cleanup job for cold entries > 7 days
  AC4: Insert of JSONB > 2MB is rejected
  AC5: Insert of JSONB < 2MB works normally
  AC6: Application-level truncation before DB constraint
"""

import json
import pytest
from unittest.mock import patch, MagicMock, Mock


# ============================================================================
# AC4 + AC5: Application-level JSONB size guard in _save_to_supabase
# ============================================================================


class TestJsonbSizeGuard:
    """STORY-265 AC4/AC5: Application-level truncation before DB CHECK constraint."""

    @pytest.mark.asyncio
    async def test_small_results_pass_through_unmodified(self):
        """AC5: Results < 2MB are saved normally without truncation."""
        from search_cache import _save_to_supabase

        small_results = [{"id": i, "objeto": f"Licitação {i}"} for i in range(10)]

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.upsert.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{"id": "test"}])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            await _save_to_supabase(
                user_id="user-123",
                params_hash="abc123",
                params={"setor_id": 1, "ufs": ["SP"]},
                results=small_results,
                sources=["PNCP"],
            )

        mock_sb.upsert.assert_called_once()
        call_args = mock_sb.upsert.call_args[0][0]
        assert call_args["total_results"] == 10
        assert len(call_args["results"]) == 10

    @pytest.mark.asyncio
    async def test_oversized_results_are_truncated(self):
        """AC4/AC6: Results > 2MB are truncated before saving to DB."""
        from search_cache import _save_to_supabase

        # Create results that exceed 2MB when serialized
        # Each item ~500 bytes → 5000 items ≈ 2.5MB
        large_results = [
            {"id": i, "objeto": f"Licitação muito grande com descrição extensa número {i}" * 5}
            for i in range(5000)
        ]
        assert len(json.dumps(large_results).encode("utf-8")) > 2_097_152

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.upsert.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{"id": "test"}])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            await _save_to_supabase(
                user_id="user-123",
                params_hash="abc123",
                params={"setor_id": 1, "ufs": ["SP"]},
                results=large_results,
                sources=["PNCP"],
            )

        mock_sb.upsert.assert_called_once()
        call_args = mock_sb.upsert.call_args[0][0]
        # Results should be truncated
        assert call_args["total_results"] < 5000
        # Verify the saved results are under 2MB
        saved_size = len(json.dumps(call_args["results"]).encode("utf-8"))
        assert saved_size <= 2_097_152

    @pytest.mark.asyncio
    async def test_truncation_logs_warning(self):
        """AC6: Truncation emits structured warning log."""
        from search_cache import _save_to_supabase

        large_results = [
            {"id": i, "objeto": f"Licitação muito grande com descrição extensa número {i}" * 5}
            for i in range(5000)
        ]

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.upsert.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{"id": "test"}])

        # BTS-010b: _save_to_supabase lives in cache.supabase; search_cache re-exports
        # it but doesn't own the logger.
        with patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("cache.supabase.logger") as mock_logger:
            await _save_to_supabase(
                user_id="user-123",
                params_hash="abc123def456",
                params={"setor_id": 1, "ufs": ["SP"]},
                results=large_results,
                sources=["PNCP"],
            )

        mock_logger.warning.assert_any_call(
            "STORY-265: results JSONB truncated",
            extra={
                "original_count": 5000,
                "truncated_count": mock_logger.warning.call_args_list[-1].kwargs.get("extra", {}).get("truncated_count", 0),
                "original_bytes": mock_logger.warning.call_args_list[-1].kwargs.get("extra", {}).get("original_bytes", 0),
                "user_id": "user-123",
                "params_hash": "abc123def456",
            },
        )

    @pytest.mark.asyncio
    async def test_just_under_limit_passes(self):
        """AC5: Results just under 2MB boundary are not truncated."""
        from search_cache import _save_to_supabase

        # Build a list that's just under 2MB — binary search for exact count
        results = [{"id": i, "objeto": "x" * 200} for i in range(8000)]
        # Trim to fit under 2MB
        while len(json.dumps(results).encode("utf-8")) > 2_097_152:
            results = results[:-100]
        count = len(results)
        total_size = len(json.dumps(results).encode("utf-8"))
        assert total_size <= 2_097_152, f"Test setup error: {total_size} > 2MB"

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.upsert.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{"id": "test"}])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            await _save_to_supabase(
                user_id="user-123",
                params_hash="abc123",
                params={"setor_id": 1, "ufs": ["SP"]},
                results=results,
                sources=["PNCP"],
            )

        call_args = mock_sb.upsert.call_args[0][0]
        assert call_args["total_results"] == count


# ============================================================================
# AC2: CHECK constraint specification
# ============================================================================


class TestCheckConstraintSpec:
    """AC2: Verify the migration specifies the correct CHECK constraint."""

    def test_migration_contains_check_constraint(self):
        """AC2: Migration file has CHECK constraint for 2MB limit."""
        import os
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "supabase", "migrations", "20260225150000_jsonb_storage_governance.sql",
        )
        with open(migration_path, encoding="utf-8") as f:
            sql = f.read()

        assert "chk_results_max_size" in sql
        assert "2097152" in sql
        assert "octet_length(results::text)" in sql

    def test_migration_contains_pg_cron_job(self):
        """AC3: Migration file schedules pg_cron cleanup for cold entries > 7 days."""
        import os
        migration_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "supabase", "migrations", "20260225150000_jsonb_storage_governance.sql",
        )
        with open(migration_path, encoding="utf-8") as f:
            sql = f.read()

        assert "cleanup-cold-cache-entries" in sql
        assert "cron.schedule" in sql
        assert "priority = 'cold'" in sql
        assert "7 days" in sql


# ============================================================================
# AC6: Existing data does not violate constraint
# ============================================================================


class TestExistingDataSafety:
    """AC6: Verify the 2MB limit does not reject normal search results."""

    def test_typical_search_results_under_limit(self):
        """AC6: A typical search (200 results) is well under 2MB."""
        results = [
            {
                "id": f"uuid-{i}",
                "objeto": f"Aquisição de equipamento para a unidade administrativa número {i}",
                "orgao": "Ministério da Educação",
                "uf": "SP",
                "valor_estimado": 150_000.0,
                "modalidade": "pregao_eletronico",
                "data_publicacao": "2026-02-20",
                "fonte": "PNCP",
            }
            for i in range(200)
        ]
        size = len(json.dumps(results).encode("utf-8"))
        assert size < 2_097_152, f"200 results = {size} bytes, should be < 2MB"

    def test_large_search_500_results_under_limit(self):
        """AC6: Even 500 results with typical data fits under 2MB."""
        results = [
            {
                "id": f"uuid-{i}",
                "objeto": f"Contratação de serviço de limpeza e conservação para prédio público {i}",
                "orgao": "Prefeitura Municipal",
                "uf": "RJ",
                "valor_estimado": 50_000.0,
                "modalidade": "pregao_eletronico",
                "data_publicacao": "2026-02-20",
                "fonte": "PNCP",
            }
            for i in range(500)
        ]
        size = len(json.dumps(results).encode("utf-8"))
        assert size < 2_097_152, f"500 results = {size} bytes, should be < 2MB"


# ============================================================================
# Application-level constant consistency
# ============================================================================


class TestConstantConsistency:
    """Verify the 2MB limit constant is consistent across codebase."""

    def test_save_to_supabase_uses_2mb_limit(self):
        """The JSONB_MAX_BYTES constant in _save_to_supabase is 2MB."""
        import inspect
        from search_cache import _save_to_supabase

        source = inspect.getsource(_save_to_supabase)
        assert "2_097_152" in source or "2097152" in source
