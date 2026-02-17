"""GTM-FIX-024 T6: Integration tests for multi-source consolidation pipeline.

Tests the full pipeline: adapter creation → ConsolidationService init →
fetch → dedup → legacy format → response validation.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, Optional, Set
from unittest.mock import AsyncMock, patch

import pytest

from clients.base import (
    SourceAdapter,
    SourceMetadata,
    SourceCapability,
    SourceStatus,
    UnifiedProcurement,
)
from consolidation import ConsolidationService, ConsolidationResult


# ============ Test Fixtures: Mock Adapters ============


class MockPNCPAdapter:
    """Minimal PNCP-like adapter for integration testing."""

    was_truncated = False
    truncated_ufs = []

    @property
    def metadata(self):
        return SourceMetadata(
            name="PNCP", code="PNCP",
            base_url="https://pncp.gov.br/api/consulta/v1",
            capabilities={SourceCapability.PAGINATION},
            rate_limit_rps=10.0, priority=1,
        )

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def code(self) -> str:
        return self.metadata.code

    async def health_check(self):
        return SourceStatus.AVAILABLE

    async def fetch(self, data_inicial, data_final, ufs=None, **kwargs):
        records = [
            UnifiedProcurement(
                source_id="PNCP-001",
                source_name="PNCP",
                objeto="Aquisição de uniformes escolares",
                valor_estimado=150000.0,
                orgao="Prefeitura de São Paulo",
                cnpj_orgao="12345678000190",
                uf="SP",
                municipio="São Paulo",
                data_publicacao=datetime(2026, 2, 15, tzinfo=timezone.utc),
                numero_edital="PE-001",
                ano="2026",
                modalidade="Pregão Eletrônico",
                modalidade_id=6,
                situacao="Publicada",
            ),
            UnifiedProcurement(
                source_id="PNCP-002",
                source_name="PNCP",
                objeto="Contratação de serviços de limpeza",
                valor_estimado=80000.0,
                orgao="Governo do Estado de SP",
                cnpj_orgao="98765432000110",
                uf="SP",
                municipio="São Paulo",
                data_publicacao=datetime(2026, 2, 14, tzinfo=timezone.utc),
                numero_edital="PE-002",
                ano="2026",
                modalidade="Pregão Eletrônico",
                modalidade_id=6,
            ),
        ]
        for r in records:
            yield r

    def normalize(self, raw_record):
        pass

    async def close(self):
        pass


class MockPCPAdapter:
    """Minimal PCP-like adapter for integration testing."""

    was_truncated = False

    @property
    def metadata(self):
        return SourceMetadata(
            name="Portal de Compras", code="PORTAL_COMPRAS",
            base_url="https://compras.api.portaldecompraspublicas.com.br",
            capabilities={SourceCapability.PAGINATION},
            rate_limit_rps=5.0, priority=2,
        )

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def code(self) -> str:
        return self.metadata.code

    async def health_check(self):
        return SourceStatus.AVAILABLE

    async def fetch(self, data_inicial, data_final, ufs=None, **kwargs):
        records = [
            # Same procurement as PNCP-001 (should be deduped, PNCP wins)
            UnifiedProcurement(
                source_id="PCP-AAA",
                source_name="PORTAL_COMPRAS",
                objeto="Aquisição de uniformes escolares",
                valor_estimado=0.0,  # PCP has no value
                orgao="Prefeitura de São Paulo",
                cnpj_orgao="12345678000190",
                uf="SP",
                municipio="São Paulo",
                data_publicacao=datetime(2026, 2, 15, tzinfo=timezone.utc),
                numero_edital="PE-001",
                ano="2026",
                modalidade="Pregão Eletrônico",
            ),
            # Unique to PCP (should appear in results)
            UnifiedProcurement(
                source_id="PCP-BBB",
                source_name="PORTAL_COMPRAS",
                objeto="Fornecimento de material de escritório",
                valor_estimado=0.0,
                orgao="Câmara Municipal de Campinas",
                cnpj_orgao="11222333000155",
                uf="SP",
                municipio="Campinas",
                data_publicacao=datetime(2026, 2, 13, tzinfo=timezone.utc),
                numero_edital="DL-003",
                ano="2026",
                modalidade="Dispensa de Licitação",
            ),
        ]
        for r in records:
            yield r

    def normalize(self, raw_record):
        pass

    async def close(self):
        pass


# ============ Integration Tests ============


class TestConsolidationIntegration:
    """Full pipeline integration tests."""

    @pytest.fixture
    def pncp_adapter(self):
        return MockPNCPAdapter()

    @pytest.fixture
    def pcp_adapter(self):
        return MockPCPAdapter()

    @pytest.fixture
    def consolidation_svc(self, pncp_adapter, pcp_adapter):
        return ConsolidationService(
            adapters={
                "PNCP": pncp_adapter,
                "PORTAL_COMPRAS": pcp_adapter,
            }
        )

    @pytest.mark.asyncio
    async def test_fetch_all_returns_results(self, consolidation_svc):
        """Pipeline should return consolidated results from both sources."""
        result = await consolidation_svc.fetch_all(
            data_inicial="2026-02-10",
            data_final="2026-02-17",
            ufs={"SP"},
        )
        assert isinstance(result, ConsolidationResult)
        assert len(result.records) > 0

    @pytest.mark.asyncio
    async def test_dedup_pncp_wins_over_pcp(self, consolidation_svc):
        """When same procurement appears in both PNCP and PCP, PNCP wins (priority=1)."""
        result = await consolidation_svc.fetch_all(
            data_inicial="2026-02-10",
            data_final="2026-02-17",
            ufs={"SP"},
        )
        data = result.records
        # PE-001 should appear once, from PNCP (higher priority)
        pe001_records = [r for r in data if r.get("numeroEdital") == "PE-001"]
        assert len(pe001_records) == 1
        assert pe001_records[0]["_source"] == "PNCP"

    @pytest.mark.asyncio
    async def test_unique_pcp_records_preserved(self, consolidation_svc):
        """PCP-only records should appear in consolidated results."""
        result = await consolidation_svc.fetch_all(
            data_inicial="2026-02-10",
            data_final="2026-02-17",
            ufs={"SP"},
        )
        data = result.records
        pcp_only = [r for r in data if r.get("_source") == "PORTAL_COMPRAS"]
        assert len(pcp_only) >= 1
        # DL-003 is unique to PCP
        dl003 = [r for r in data if r.get("numeroEdital") == "DL-003"]
        assert len(dl003) == 1

    @pytest.mark.asyncio
    async def test_legacy_format_has_modalidade_id(self, consolidation_svc):
        """GTM-FIX-024 T4: Legacy format should include modalidadeId."""
        result = await consolidation_svc.fetch_all(
            data_inicial="2026-02-10",
            data_final="2026-02-17",
            ufs={"SP"},
        )
        data = result.records
        pncp_records = [r for r in data if r.get("_source") == "PNCP"]
        assert len(pncp_records) > 0
        # PNCP records should have modalidadeId=6
        for rec in pncp_records:
            if rec.get("modalidadeNome") == "Pregão Eletrônico":
                assert rec.get("modalidadeId") == 6

    @pytest.mark.asyncio
    async def test_legacy_format_structure(self, consolidation_svc):
        """Legacy format should have all expected fields."""
        result = await consolidation_svc.fetch_all(
            data_inicial="2026-02-10",
            data_final="2026-02-17",
            ufs={"SP"},
        )
        data = result.records
        assert len(data) > 0
        required_fields = [
            "codigoCompra", "objetoCompra", "valorTotalEstimado",
            "nomeOrgao", "cnpjOrgao", "uf", "municipio",
            "modalidadeNome", "modalidadeId", "_source", "_dedup_key",
        ]
        for rec in data:
            for field in required_fields:
                assert field in rec, f"Missing field '{field}' in legacy record"

    @pytest.mark.asyncio
    async def test_metadata_includes_source_results(self, consolidation_svc):
        """Result metadata should track per-source results."""
        result = await consolidation_svc.fetch_all(
            data_inicial="2026-02-10",
            data_final="2026-02-17",
            ufs={"SP"},
        )
        assert len(result.source_results) > 0
        source_codes = [sr.source_code for sr in result.source_results]
        assert "PNCP" in source_codes
        assert "PORTAL_COMPRAS" in source_codes


class TestDedupKeyZeroValue:
    """GTM-FIX-024 T3: Dedup key handles zero-value records correctly."""

    def test_different_pcp_records_get_different_keys(self):
        """Two PCP records with value=0 but different dates should NOT collide."""
        rec1 = UnifiedProcurement(
            source_id="PCP-1", source_name="PCP",
            objeto="Material de escritório",
            valor_estimado=0.0,
            orgao="Prefeitura X",
            cnpj_orgao="12345678000190",
            uf="SP",
            data_publicacao=datetime(2026, 2, 10, tzinfo=timezone.utc),
        )
        rec2 = UnifiedProcurement(
            source_id="PCP-2", source_name="PCP",
            objeto="Material de escritório",
            valor_estimado=0.0,
            orgao="Prefeitura X",
            cnpj_orgao="12345678000190",
            uf="SP",
            data_publicacao=datetime(2026, 2, 12, tzinfo=timezone.utc),
        )
        assert rec1.dedup_key != rec2.dedup_key

    def test_same_procurement_cross_source_matches(self):
        """Same procurement in PNCP and PCP with same edital/ano should match."""
        pncp = UnifiedProcurement(
            source_id="PNCP-1", source_name="PNCP",
            objeto="Uniformes escolares",
            valor_estimado=150000.0,
            orgao="Prefeitura Y",
            cnpj_orgao="12345678000190",
            uf="SP",
            numero_edital="PE-001",
            ano="2026",
        )
        pcp = UnifiedProcurement(
            source_id="PCP-1", source_name="PCP",
            objeto="Uniformes escolares",
            valor_estimado=0.0,
            orgao="Prefeitura Y",
            cnpj_orgao="12345678000190",
            uf="SP",
            numero_edital="PE-001",
            ano="2026",
        )
        assert pncp.dedup_key == pcp.dedup_key

    def test_zero_value_no_date_uses_source_id(self):
        """When both value=0 and no date, fallback to source_id."""
        rec = UnifiedProcurement(
            source_id="PCP-ABC", source_name="PCP",
            objeto="Serviço X",
            valor_estimado=0.0,
            orgao="Org",
            cnpj_orgao="11111111000100",
            uf="RJ",
        )
        assert "PCP-ABC" in rec.dedup_key

    def test_nonzero_value_uses_int_value(self):
        """When value > 0, the old int(valor) behavior is preserved."""
        rec = UnifiedProcurement(
            source_id="PNCP-X", source_name="PNCP",
            objeto="Uniformes",
            valor_estimado=75000.50,
            orgao="Org",
            cnpj_orgao="22222222000100",
            uf="MG",
        )
        assert ":75000" in rec.dedup_key


class TestLegacyFormatModalidadeId:
    """GTM-FIX-024 T4: modalidadeId in to_legacy_format()."""

    def test_modalidade_id_present_when_set(self):
        rec = UnifiedProcurement(
            source_id="X", source_name="PNCP",
            modalidade="Pregão Eletrônico",
            modalidade_id=6,
        )
        legacy = rec.to_legacy_format()
        assert legacy["modalidadeId"] == 6
        assert legacy["modalidadeNome"] == "Pregão Eletrônico"

    def test_modalidade_id_none_when_not_set(self):
        rec = UnifiedProcurement(
            source_id="X", source_name="PCP",
            modalidade="Dispensa",
        )
        legacy = rec.to_legacy_format()
        assert legacy["modalidadeId"] is None
        assert legacy["modalidadeNome"] == "Dispensa"
