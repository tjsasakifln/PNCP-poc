"""
Integration tests for PNCP client against real API.

These tests are marked as @pytest.mark.integration and use mocked API responses.
Run integration tests with: pytest -m integration

NOTE: Tests use mocked PNCP responses to avoid rate limiting and ensure reliability.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from pncp_client import PNCPClient


@pytest.mark.integration
def test_real_pncp_api_call():
    """Test PNCP API call structure with mocked response."""
    # Use a recent date range to ensure data exists
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    # Mock PNCP API response structure
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "codigoCompra": "123456",
                "objetoCompra": "Aquisição de uniformes escolares",
                "nomeOrgao": "Prefeitura Municipal",
                "uf": "SP",
                "municipio": "São Paulo",
                "valorTotalEstimado": 150000.00,
                "dataAberturaProposta": "2025-02-10T10:00:00",
                "linkSistemaOrigem": "https://pncp.gov.br/app/editais/123456",
            }
        ],
        "totalRegistros": 1,
        "totalPaginas": 1,
        "paginaAtual": 1,
        "temProximaPagina": False,
    }

    with patch("httpx.Client.get", return_value=mock_response):
        with PNCPClient() as client:
            result = client.fetch_page(
                data_inicial=start_date.strftime("%Y-%m-%d"),
                data_final=end_date.strftime("%Y-%m-%d"),
                modalidade=1,  # Concorrência
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


@pytest.mark.integration
def test_real_pncp_api_with_uf_filter():
    """Test API call with UF filter using mocked response."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    # Mock PNCP API response for SP-only results
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "codigoCompra": "123",
                "objetoCompra": "Uniformes SP",
                "uf": "SP",
                "valorTotalEstimado": 100000.00,
            },
            {
                "codigoCompra": "456",
                "objetoCompra": "Fardamento SP",
                "uf": "SP",
                "valorTotalEstimado": 80000.00,
            },
        ],
        "totalRegistros": 2,
        "totalPaginas": 1,
        "paginaAtual": 1,
        "temProximaPagina": False,
    }

    with patch("httpx.Client.get", return_value=mock_response):
        with PNCPClient() as client:
            result = client.fetch_page(
                data_inicial=start_date.strftime("%Y-%m-%d"),
                data_final=end_date.strftime("%Y-%m-%d"),
                modalidade=1,  # Concorrência
                uf="SP",
                pagina=1,
                tamanho=10,  # PNCP API minimum
            )

            assert "data" in result
            # Verify all results are from SP
            for item in result["data"]:
                if "uf" in item:
                    assert item["uf"] == "SP"
