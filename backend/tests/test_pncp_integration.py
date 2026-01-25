"""
Integration tests for PNCP client against real API.

These tests are marked as @pytest.mark.integration and are skipped by default.
Run with: pytest -m integration

WARNING: These tests make real API calls and may be rate-limited.
"""

import pytest
from datetime import datetime, timedelta

from pncp_client import PNCPClient


@pytest.mark.integration
@pytest.mark.skip(reason="Integration test - requires real API access")
def test_real_pncp_api_call():
    """Test actual call to PNCP API (requires network)."""
    # Use a recent date range to ensure data exists
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    client = PNCPClient()

    try:
        result = client.fetch_page(
            data_inicial=start_date.strftime("%Y-%m-%d"),
            data_final=end_date.strftime("%Y-%m-%d"),
            pagina=1,
            tamanho=10,
        )

        # Validate response structure
        assert "data" in result
        assert "totalRegistros" in result
        assert "totalPaginas" in result
        assert isinstance(result["data"], list)

        print(f"✅ Fetched {len(result['data'])} records")
        print(f"   Total: {result['totalRegistros']} records")

    finally:
        client.close()


@pytest.mark.integration
@pytest.mark.skip(reason="Integration test - requires real API access")
def test_real_pncp_api_with_uf_filter():
    """Test API call with UF filter."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    with PNCPClient() as client:
        result = client.fetch_page(
            data_inicial=start_date.strftime("%Y-%m-%d"),
            data_final=end_date.strftime("%Y-%m-%d"),
            uf="SP",
            pagina=1,
            tamanho=5,
        )

        assert "data" in result
        # Verify all results are from SP
        for item in result["data"]:
            if "uf" in item:
                assert item["uf"] == "SP"
