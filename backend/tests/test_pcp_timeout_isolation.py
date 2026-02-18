"""
GTM-FIX-033 AC7: PCP timeout does not block PNCP partial results.

When PCP (Portal de Compras Públicas) times out, PNCP data must still
be returned as partial results. The user should never lose already-fetched
PNCP data because of a PCP failure.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

from services.models import SourceMetadata, SourceStatus, UnifiedProcurement


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_unified(source: str, code_val: str, objeto: str = "Uniformes escolares") -> UnifiedProcurement:
    """Create a UnifiedProcurement record for testing."""
    return UnifiedProcurement(
        source_id=f"{source}-{code_val}",
        source_name=source,
        objeto=objeto,
        valor_estimado=100_000.0,
        orgao=f"Org-{source}",
        cnpj_orgao="12345678000199",
        uf="SP",
        municipio="São Paulo",
        modalidade="Pregão Eletrônico",
        situacao="Aberta",
    )


def _make_dict_record(source: str, code_val: str, objeto: str = "Uniformes escolares") -> dict:
    """Create a dict record (for pipeline-level testing where ctx.licitacoes_raw is list[dict])."""
    return {
        "codigoCompra": code_val,
        "objetoCompra": objeto,
        "valorTotalEstimado": 100_000.0,
        "uf": "SP",
        "municipio": "São Paulo",
        "nomeOrgao": f"Org-{source}",
        "dataAberturaProposta": "2026-02-01T10:00:00Z",
        "dataEncerramentoProposta": "2026-02-15T18:00:00Z",
        "situacaoCompraNome": "Aberta",
        "modalidadeNome": "Pregão Eletrônico",
        "source": source,
        "source_id": f"{source}-{code_val}",
    }


class FakeAdapter:
    """Minimal adapter mock that satisfies ConsolidationService interface."""

    def __init__(
        self,
        code_val: str,
        priority_val: int,
        records: list,
        delay: float = 0,
        should_fail: bool = False,
    ):
        self._records = records
        self._delay = delay
        self._should_fail = should_fail
        # Direct attributes required by ConsolidationService validator
        self.code = code_val
        self.metadata = SourceMetadata(
            name=f"Test {code_val}",
            code=code_val,
            base_url="http://test.example.com",
            priority=priority_val,
        )

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def priority(self) -> int:
        return self.metadata.priority

    async def health_check(self):
        return SourceStatus.AVAILABLE

    async def fetch(self, data_inicial, data_final, ufs=None, **kwargs):
        if self._delay:
            await asyncio.sleep(self._delay)
        if self._should_fail:
            raise TimeoutError(f"{self.code} timed out")
        for record in self._records:
            yield record

    def normalize(self, raw_record):
        return raw_record

    async def close(self):
        pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPcpTimeoutIsolation:
    """AC7: PCP timeout must not block PNCP results."""

    @pytest.mark.asyncio
    async def test_pcp_timeout_returns_pncp_data(self):
        """When PCP times out, PNCP data should be returned as partial."""
        from consolidation import ConsolidationService

        pncp_records = [
            _make_unified("PNCP", "pncp-001", "Uniforme escolar tipo A"),
            _make_unified("PNCP", "pncp-002", "Uniforme escolar tipo B"),
            _make_unified("PNCP", "pncp-003", "Jaleco hospitalar"),
        ]

        adapters = {
            "PNCP": FakeAdapter("PNCP", priority_val=1, records=pncp_records, delay=0),
            "PORTAL_COMPRAS": FakeAdapter(
                "PORTAL_COMPRAS", priority_val=2, records=[], delay=10, should_fail=True
            ),
        }

        svc = ConsolidationService(
            adapters=adapters,
            timeout_per_source=0.2,  # 200ms — PCP will timeout at 10s delay
        )

        try:
            result = await svc.fetch_all(
                data_inicial="2026-02-01",
                data_final="2026-02-10",
            )

            # PNCP data should be present
            assert result.total_after_dedup >= 3, (
                f"Expected at least 3 PNCP records, got {result.total_after_dedup}"
            )

            # Verify source statuses
            statuses = {sr.source_code: sr.status for sr in result.source_results}
            assert statuses.get("PNCP") == "success", (
                f"PNCP should be 'success', got {statuses.get('PNCP')}"
            )
            assert statuses.get("PORTAL_COMPRAS") in ("timeout", "error"), (
                f"PCP should be 'timeout' or 'error', got {statuses.get('PORTAL_COMPRAS')}"
            )

            # PNCP record count should be correct
            pncp_sr = next(
                sr for sr in result.source_results if sr.source_code == "PNCP"
            )
            assert pncp_sr.record_count == 3

        finally:
            await svc.close()

    @pytest.mark.asyncio
    async def test_pcp_error_returns_pncp_data(self):
        """When PCP raises an error (not timeout), PNCP data still returned."""
        from consolidation import ConsolidationService

        pncp_records = [
            _make_unified("PNCP", "pncp-010", "Fardamento militar"),
        ]

        adapters = {
            "PNCP": FakeAdapter("PNCP", priority_val=1, records=pncp_records),
            "PORTAL_COMPRAS": FakeAdapter(
                "PORTAL_COMPRAS", priority_val=2, records=[], should_fail=True
            ),
        }

        svc = ConsolidationService(
            adapters=adapters,
            timeout_per_source=5.0,
        )

        try:
            result = await svc.fetch_all(
                data_inicial="2026-02-01",
                data_final="2026-02-10",
            )

            assert result.total_after_dedup >= 1
            statuses = {sr.source_code: sr.status for sr in result.source_results}
            assert statuses.get("PNCP") == "success"
            assert statuses.get("PORTAL_COMPRAS") in ("timeout", "error")

        finally:
            await svc.close()

    @pytest.mark.asyncio
    async def test_both_sources_ok_returns_all_data(self):
        """When both sources succeed, all data is returned (deduped)."""
        from consolidation import ConsolidationService

        pncp_records = [
            _make_unified("PNCP", "pncp-020", "Uniforme escolar"),
        ]
        pcp_records = [
            _make_unified("PORTAL_COMPRAS", "pcp-020", "Uniforme profissional"),
        ]

        adapters = {
            "PNCP": FakeAdapter("PNCP", priority_val=1, records=pncp_records),
            "PORTAL_COMPRAS": FakeAdapter("PORTAL_COMPRAS", priority_val=2, records=pcp_records),
        }

        svc = ConsolidationService(
            adapters=adapters,
            timeout_per_source=5.0,
        )

        try:
            result = await svc.fetch_all(
                data_inicial="2026-02-01",
                data_final="2026-02-10",
            )

            assert result.total_after_dedup >= 2
            statuses = {sr.source_code: sr.status for sr in result.source_results}
            assert statuses.get("PNCP") == "success"
            assert statuses.get("PORTAL_COMPRAS") == "success"

        finally:
            await svc.close()

    @pytest.mark.asyncio
    async def test_pipeline_serves_partial_on_pcp_timeout(self):
        """Integration: SearchPipeline._execute_multi_source serves partial when PCP fails."""
        from search_pipeline import SearchPipeline, SearchContext

        # Create a minimal request and context
        request = SimpleNamespace(
            ufs=["SP"],
            data_inicial="2026-02-01",
            data_final="2026-02-10",
            setor_id="vestuario",
            search_id="test-pcp-timeout-001",
            termos_busca=None,
            modo_busca="abertas",
            status=None,
            modalidades=None,
            valor_minimo=None,
            valor_maximo=None,
            esferas=None,
            municipios=None,
            ordenacao=None,
            force_fresh=False,
        )

        ctx = SearchContext(
            request=request,
            user={"id": "test-user", "email": "test@test.com"},
        )

        # Create proper dict records (pipeline stores dicts in ctx.licitacoes_raw)
        raw_records = [
            _make_dict_record("PNCP", "pncp-100", "Uniforme teste"),
            _make_dict_record("PNCP", "pncp-101", "Jaleco teste"),
        ]

        # Mock ConsolidationService to return partial result (PCP failed)
        mock_result = MagicMock()
        mock_result.records = raw_records
        mock_result.total_after_dedup = 2
        mock_result.total_before_dedup = 2
        mock_result.duplicates_removed = 0
        mock_result.is_partial = True
        mock_result.degradation_reason = "PORTAL_COMPRAS timed out"
        mock_result.source_results = [
            SimpleNamespace(
                source_code="PNCP",
                status="success",
                record_count=2,
                duration_ms=1500,
                error=None,
            ),
            SimpleNamespace(
                source_code="PORTAL_COMPRAS",
                status="timeout",
                record_count=0,
                duration_ms=30000,
                error="PCP timed out",
            ),
        ]

        with patch("consolidation.ConsolidationService") as MockCS, \
             patch("source_config.sources.get_source_config") as mock_config, \
             patch("search_pipeline.enriquecer_com_status_inferido") as mock_enrich, \
             patch("search_pipeline._supabase_save_cache", new_callable=AsyncMock), \
             patch("search_pipeline._supabase_get_cache", new_callable=AsyncMock, return_value=None), \
             patch("search_pipeline.sentry_sdk"):

            mock_svc = AsyncMock()
            mock_svc.fetch_all = AsyncMock(return_value=mock_result)
            mock_svc.close = AsyncMock()
            MockCS.return_value = mock_svc

            mock_config.return_value = MagicMock(
                pncp=MagicMock(enabled=True),
                portal=MagicMock(enabled=True),
                compras_gov=MagicMock(enabled=False),
            )
            mock_enrich.side_effect = lambda lics, *a, **kw: lics

            deps = SimpleNamespace(
                ENABLE_NEW_PRICING=False,
                PNCPClient=MagicMock,
                buscar_todas_ufs_paralelo=AsyncMock(return_value=[]),
                aplicar_todos_filtros=MagicMock(return_value=([], {})),
                create_excel=MagicMock(),
                rate_limiter=MagicMock(check_rate_limit=AsyncMock(return_value=(True, 0))),
                check_user_roles=AsyncMock(return_value=(False, False)),
                match_keywords=MagicMock(return_value=(True, [])),
                KEYWORDS_UNIFORMES=set(),
                KEYWORDS_EXCLUSAO=set(),
                validate_terms=MagicMock(
                    return_value={"valid": [], "ignored": [], "reasons": {}}
                ),
            )

            pipeline = SearchPipeline(deps)
            await pipeline._execute_multi_source(
                ctx, request, deps, None, None, None, 240,
            )

        # Verify: PNCP data present despite PCP failure
        assert isinstance(ctx.licitacoes_raw, list), (
            f"Expected list, got {type(ctx.licitacoes_raw)}"
        )
        assert len(ctx.licitacoes_raw) == 2, (
            f"Expected 2 PNCP records, got {len(ctx.licitacoes_raw)}"
        )
        assert ctx.is_partial is True, "Should be marked as partial"

        # Verify source stats recorded
        assert len(ctx.data_sources) == 2, "Should have 2 source entries"
        pncp_stat = next(
            (s for s in ctx.data_sources if s.source == "PNCP"), None
        )
        assert pncp_stat is not None
        assert pncp_stat.status == "ok"
        assert pncp_stat.records == 2
