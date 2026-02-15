"""
Discovery Phase - STORY-184
Test PNCP API for homologated contracts (contratos homologados)

Business Analyst: @analyst (Atlas)
Date: 2026-02-10
"""

import requests
from datetime import datetime, timedelta
import json

def test_pncp_contratos_endpoint():
    """
    Test PNCP /contratos endpoint to identify homologated contracts.

    Goal: Understand the API structure and identify how to filter for
    homologated (completed/awarded) contracts.
    """

    base_url = "https://pncp.gov.br/api/consulta/v1"

    # Test 1: Query recent contracts (last 30 days)
    print("=" * 80)
    print("TEST 1: Query Recent Contracts (last 30 days)")
    print("=" * 80)

    data_final = datetime.now()
    data_inicial = data_final - timedelta(days=30)

    endpoint = f"{base_url}/contratos"
    params = {
        "dataInicial": data_inicial.strftime("%Y%m%d"),
        "dataFinal": data_final.strftime("%Y%m%d"),
        "pagina": 1
    }

    print(f"\nEndpoint: {endpoint}")
    print(f"Params: {json.dumps(params, indent=2)}")

    try:
        response = requests.get(endpoint, params=params, timeout=30)
        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse Structure:")
            print(f"- Keys: {list(data.keys())}")

            if "data" in data:
                contracts = data["data"]
                print(f"- Total contracts returned: {len(contracts)}")

                if contracts:
                    print(f"\nSample Contract (First Result):")
                    sample = contracts[0]
                    print(json.dumps(sample, indent=2, ensure_ascii=False)[:2000])

                    # Check for fields indicating homologation status
                    print(f"\nRelevant Fields:")
                    print(f"- situacaoContrato: {sample.get('situacaoContrato', 'N/A')}")
                    print(f"- niFornecedor (CNPJ): {sample.get('niFornecedor', 'N/A')}")
                    print(f"- valorInicial: {sample.get('valorInicial', 'N/A')}")
                    print(f"- dataVigenciaInicio: {sample.get('dataVigenciaInicio', 'N/A')}")
                    print(f"- dataVigenciaFim: {sample.get('dataVigenciaFim', 'N/A')}")

            # Check pagination info
            if "totalPaginas" in data:
                print(f"\nPagination Info:")
                print(f"- Total Pages: {data['totalPaginas']}")
                print(f"- Current Page: {data.get('paginaAtual', 'N/A')}")
                print(f"- Total Records: {data.get('totalRegistros', 'N/A')}")
        else:
            print(f"\nError Response:")
            print(response.text[:500])

    except Exception as e:
        print(f"\nException: {type(e).__name__}: {e}")

    # Test 2: Try with situacao parameter (if exists)
    print("\n\n" + "=" * 80)
    print("TEST 2: Query with Status Filter (attempt)")
    print("=" * 80)

    params_with_status = params.copy()
    params_with_status["situacao"] = "homologado"  # Hypothesis: filter by status

    print(f"\nEndpoint: {endpoint}")
    print(f"Params: {json.dumps(params_with_status, indent=2)}")

    try:
        response = requests.get(endpoint, params=params_with_status, timeout=30)
        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Total contracts with 'situacao=homologado': {len(data.get('data', []))}")
        else:
            print(f"Failed - Status parameter may not be supported")
            print(f"Response: {response.text[:200]}")

    except Exception as e:
        print(f"\nException: {type(e).__name__}: {e}")

    # Test 3: Alternative - Query licitacoes and look for homologated ones
    print("\n\n" + "=" * 80)
    print("TEST 3: Alternative - Query Licitacoes (Publicacao)")
    print("=" * 80)

    licitacoes_endpoint = f"{base_url}/contratacoes/publicacao"
    licitacoes_params = {
        "dataInicial": data_inicial.strftime("%Y%m%d"),
        "dataFinal": data_final.strftime("%Y%m%d"),
        "pagina": 1
    }

    print(f"\nEndpoint: {licitacoes_endpoint}")
    print(f"Params: {json.dumps(licitacoes_params, indent=2)}")

    try:
        response = requests.get(licitacoes_endpoint, params=licitacoes_params, timeout=30)
        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse Structure:")
            print(f"- Keys: {list(data.keys())}")

            if "data" in data:
                licitacoes = data["data"]
                print(f"- Total licitações returned: {len(licitacoes)}")

                if licitacoes:
                    sample = licitacoes[0]
                    print(f"\nSample Licitação Fields:")
                    print(f"- Keys: {list(sample.keys())}")

                    # Look for status/situacao fields
                    for key in sample.keys():
                        if "situa" in key.lower() or "status" in key.lower():
                            print(f"  - {key}: {sample[key]}")
        else:
            print(f"\nError Response: {response.text[:300]}")

    except Exception as e:
        print(f"\nException: {type(e).__name__}: {e}")

    print("\n\n" + "=" * 80)
    print("DISCOVERY COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_pncp_contratos_endpoint()
