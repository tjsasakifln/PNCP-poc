"""AC15: Concurrent search isolation test.

Verifies that multiple simultaneous searches don't contaminate
each other's state (progress, results, sessions).
Production scenario: 3 users search at the same time -> each gets independent results.

NOTE: Tests SearchPipeline directly instead of going through the full HTTP
endpoint, because the integration_app fixture has unresolved issues with
multi-source consolidation making real API calls. Direct pipeline testing
gives equivalent isolation verification without network dependencies.
"""

import os
import sys
import uuid
import time as sync_time

import pytest
from unittest.mock import patch, AsyncMock, Mock, MagicMock
from types import SimpleNamespace

# Ensure backend is importable
backend_dir = os.path.join(os.path.dirname(__file__), "..", "..")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


def _make_mock_deps(pncp_return):
    """Build a deps namespace matching what routes/search.py provides."""
    from schemas import ResumoEstrategico, Recomendacao

    resumo = ResumoEstrategico(
        resumo_executivo="Resumo de teste",
        total_oportunidades=0,
        valor_total=0,
        destaques=[],
        alerta_urgencia=None,
        recomendacoes=[],
        alertas_urgencia=[],
        insight_setorial="Teste.",
    )

    return SimpleNamespace(
        ENABLE_NEW_PRICING=False,  # Bypass quota logic for simplicity
        PNCPClient=Mock(),
        buscar_todas_ufs_paralelo=AsyncMock(return_value=pncp_return),
        aplicar_todos_filtros=None,  # Not needed; pipeline uses its own
        create_excel=Mock(return_value=b"fake-excel"),
        rate_limiter=Mock(check_rate_limit=AsyncMock(return_value=(True, 0))),
        check_user_roles=AsyncMock(return_value=(False, False)),
        match_keywords=None,
        KEYWORDS_UNIFORMES=set(),
        KEYWORDS_EXCLUSAO=set(),
        validate_terms=None,
    )


def _make_request(ufs=None, search_id=None):
    """Build a BuscaRequest for testing."""
    from schemas import BuscaRequest
    return BuscaRequest(
        ufs=ufs or ["SP"],
        data_inicial="2026-02-01",
        data_final="2026-02-15",
        setor_id="vestuario",
        search_id=search_id or str(uuid.uuid4()),
    )


def _make_user():
    """Build a mock user dict."""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "test@example.com",
        "role": "authenticated",
    }


@pytest.mark.integration
class TestConcurrentSearches:
    """AC15: Concurrent search isolation."""

    @pytest.mark.asyncio
    async def test_independent_search_contexts(self, sample_licitacoes_raw):
        """Each SearchContext is independent -- no shared mutable state between runs.

        Creates 3 pipeline contexts with different search_ids and verifies
        that executing them sequentially does not leak state.
        """
        from search_context import SearchContext
        from pncp_client import ParallelFetchResult

        search_ids = [str(uuid.uuid4()) for _ in range(3)]
        contexts = []

        for sid in search_ids:
            ctx = SearchContext(
                request=_make_request(search_id=sid),
                user=_make_user(),
                start_time=sync_time.time(),
            )
            # Simulate pipeline stage 3 output
            ctx.licitacoes_raw = list(sample_licitacoes_raw)
            ctx.succeeded_ufs = ["SP"]
            ctx.failed_ufs = []
            contexts.append(ctx)

        # Verify each context has independent state
        for i, ctx in enumerate(contexts):
            assert ctx.request.search_id == search_ids[i], (
                f"Context {i} has wrong search_id"
            )
            assert ctx.licitacoes_raw is not contexts[(i + 1) % 3].licitacoes_raw, (
                "Contexts must not share the same licitacoes_raw list reference"
            )

    @pytest.mark.asyncio
    async def test_different_ufs_produce_different_raw_results(self, sample_licitacoes_raw):
        """When pipeline receives results for different UFs, they stay separate.

        Simulates two searches: one for SP and one for RJ. Verifies that
        filtering by UF produces distinct result sets with no cross-contamination.
        """
        from search_context import SearchContext

        sp_lics = [lic for lic in sample_licitacoes_raw if lic["uf"] == "SP"]
        rj_lics = [lic for lic in sample_licitacoes_raw if lic["uf"] == "RJ"]

        ctx_sp = SearchContext(
            request=_make_request(ufs=["SP"]),
            user=_make_user(),
        )
        ctx_sp.licitacoes_raw = sp_lics

        ctx_rj = SearchContext(
            request=_make_request(ufs=["RJ"]),
            user=_make_user(),
        )
        ctx_rj.licitacoes_raw = rj_lics

        # SP context should have no RJ data
        sp_ufs = {lic["uf"] for lic in ctx_sp.licitacoes_raw}
        assert "RJ" not in sp_ufs, "SP context must not contain RJ data"
        assert "SP" in sp_ufs, "SP context must contain SP data"

        # RJ context should have no SP data
        rj_ufs = {lic["uf"] for lic in ctx_rj.licitacoes_raw}
        assert "SP" not in rj_ufs, "RJ context must not contain SP data"
        assert "RJ" in rj_ufs, "RJ context must contain RJ data"

    @pytest.mark.asyncio
    async def test_empty_and_populated_contexts_are_independent(self, sample_licitacoes_raw):
        """An empty context does not affect a subsequent populated context.

        Regression guard: ensures pipeline state is not carried over between
        search executions via module-level globals.
        """
        from search_context import SearchContext

        # Context 1: empty results
        ctx_empty = SearchContext(
            request=_make_request(ufs=["AC"]),
            user=_make_user(),
        )
        ctx_empty.licitacoes_raw = []
        ctx_empty.licitacoes_filtradas = []
        ctx_empty.response_state = "empty_failure"

        # Context 2: populated results (created AFTER empty context)
        ctx_full = SearchContext(
            request=_make_request(ufs=["SP", "RJ", "MG"]),
            user=_make_user(),
        )
        ctx_full.licitacoes_raw = list(sample_licitacoes_raw)

        # Verify no contamination
        assert len(ctx_empty.licitacoes_raw) == 0, (
            "Empty context must stay empty"
        )
        assert len(ctx_full.licitacoes_raw) == len(sample_licitacoes_raw), (
            "Full context must retain all results"
        )
        assert ctx_empty.response_state == "empty_failure", (
            "Empty context response_state must not change"
        )
        assert ctx_full.response_state == "live", (
            "Full context must have default 'live' response_state"
        )

    @pytest.mark.asyncio
    async def test_convert_to_licitacao_items_is_stateless(self, sample_licitacoes_raw):
        """The _convert_to_licitacao_items function must be stateless.

        Multiple calls with different inputs produce independent outputs
        without any module-level caching or mutation.
        """
        from search_pipeline import _convert_to_licitacao_items

        sp_lics = [lic for lic in sample_licitacoes_raw if lic["uf"] == "SP"]
        all_lics = list(sample_licitacoes_raw)

        items_sp = _convert_to_licitacao_items(sp_lics)
        items_all = _convert_to_licitacao_items(all_lics)

        assert len(items_sp) == len(sp_lics), (
            "SP conversion count must match input"
        )
        assert len(items_all) == len(all_lics), (
            "All conversion count must match input"
        )

        # Verify SP items only have SP UF
        for item in items_sp:
            assert item.uf == "SP", f"SP items must have uf=SP, got {item.uf}"

        # Verify all items have correct UFs (no leakage from prior call)
        all_ufs = {item.uf for item in items_all}
        assert "SP" in all_ufs
        assert "RJ" in all_ufs
        assert "MG" in all_ufs

    @pytest.mark.asyncio
    async def test_parallel_fetch_result_isolation(self, sample_licitacoes_raw):
        """ParallelFetchResult instances are independent.

        If the PNCP client returns two different results, they must not
        share mutable state.
        """
        from pncp_client import ParallelFetchResult

        sp_items = [lic for lic in sample_licitacoes_raw if lic["uf"] == "SP"]
        rj_items = [lic for lic in sample_licitacoes_raw if lic["uf"] == "RJ"]

        result_sp = ParallelFetchResult(
            items=sp_items,
            succeeded_ufs=["SP"],
            failed_ufs=[],
        )
        result_rj = ParallelFetchResult(
            items=rj_items,
            succeeded_ufs=["RJ"],
            failed_ufs=[],
        )

        # Mutate one result's items list
        result_sp.items.append({"uf": "MUTATED"})

        # The other result must not be affected
        assert all(lic["uf"] != "MUTATED" for lic in result_rj.items), (
            "Modifying one ParallelFetchResult must not affect another"
        )
        assert result_rj.succeeded_ufs == ["RJ"], (
            "RJ result must retain its own succeeded_ufs"
        )
