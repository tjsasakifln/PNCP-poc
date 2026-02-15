"""Integration tests for Portal da Transparência adapter and sanctions checker.

These tests make real API calls and are skipped by default.
Run with: pytest -m integration

Requires PORTAL_TRANSPARENCIA_API_KEY environment variable.

STORY-254 AC16.
"""

import os
from datetime import datetime, timedelta

import pytest

from clients.base import SourceStatus, UnifiedProcurement
from clients.portal_transparencia_client import PortalTransparenciaAdapter
from clients.sanctions import SanctionsChecker, SanctionsResult

# Mark all tests as integration and skip if API key not set
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("PORTAL_TRANSPARENCIA_API_KEY"),
        reason="PORTAL_TRANSPARENCIA_API_KEY not set",
    ),
]


@pytest.mark.asyncio
async def test_health_check_returns_available():
    """AC16: Health check returns AVAILABLE with valid API key."""
    async with PortalTransparenciaAdapter() as adapter:
        status = await adapter.health_check()
        assert status in (SourceStatus.AVAILABLE, SourceStatus.DEGRADED)


@pytest.mark.asyncio
async def test_fetch_yields_unified_procurement():
    """AC16: Fetch yields UnifiedProcurement records with valid fields."""
    async with PortalTransparenciaAdapter() as adapter:
        data_final = datetime.now()
        data_inicial = data_final - timedelta(days=7)

        records = []
        async for record in adapter.fetch(
            data_inicial=data_inicial.strftime("%Y-%m-%d"),
            data_final=data_final.strftime("%Y-%m-%d"),
            ufs={"DF"},
        ):
            records.append(record)
            if len(records) >= 5:
                break  # Limit to 5 for speed

        # May be 0 if no data in last 7 days — that's OK
        for record in records:
            assert isinstance(record, UnifiedProcurement)
            assert record.source_name == "PORTAL_TRANSPARENCIA"
            assert record.source_id
            assert record.esfera == "F"
            assert record.raw_data is not None


@pytest.mark.asyncio
async def test_fetch_uf_filter_applied():
    """AC16: Client-side UF filter only yields matching records."""
    async with PortalTransparenciaAdapter() as adapter:
        data_final = datetime.now()
        data_inicial = data_final - timedelta(days=7)

        records = []
        async for record in adapter.fetch(
            data_inicial=data_inicial.strftime("%Y-%m-%d"),
            data_final=data_final.strftime("%Y-%m-%d"),
            ufs={"DF"},
        ):
            records.append(record)
            if len(records) >= 10:
                break

        for record in records:
            assert record.uf == "DF" or record.uf == ""


@pytest.mark.asyncio
async def test_normalize_real_record():
    """AC16: Normalize produces valid UnifiedProcurement from real API data."""
    async with PortalTransparenciaAdapter() as adapter:
        data_final = datetime.now()
        data_inicial = data_final - timedelta(days=7)

        async for record in adapter.fetch(
            data_inicial=data_inicial.strftime("%Y-%m-%d"),
            data_final=data_final.strftime("%Y-%m-%d"),
        ):
            # Just check the first record
            assert record.objeto or record.objeto == ""
            assert isinstance(record.valor_estimado, float)
            assert record.link_portal  # Should always have a link
            break


@pytest.mark.asyncio
async def test_sanctions_checker_returns_result():
    """AC16: SanctionsChecker returns a SanctionsResult for any CNPJ."""
    async with SanctionsChecker() as checker:
        # Use Banco do Brasil CNPJ (well-known, should not be sanctioned)
        result = await checker.check_sanctions("00000000000191")

        assert isinstance(result, SanctionsResult)
        assert isinstance(result.is_sanctioned, bool)
        assert result.cnpj == "00000000000191"
        assert isinstance(result.ceis_count, int)
        assert isinstance(result.cnep_count, int)
        assert result.cache_hit is False

        # Second call should hit cache
        result2 = await checker.check_sanctions("00000000000191")
        assert result2.cache_hit is True
