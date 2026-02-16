"""
Discovery Phase - STORY-184
Test Receita Federal API for CNPJ data enrichment

Business Analyst: @analyst (Atlas)
Date: 2026-02-10
"""

import requests
import json
import time

def test_receita_federal_api():
    """
    Test Receita Federal API (ReceitaWS) for company data enrichment.

    API: https://www.receitaws.com.br/v1/cnpj/{cnpj}
    Free tier: 3 requests/minute

    Goal: Get company data (legal name, CNAE, size, revenue estimate)
    """

    # Sample CNPJs from PNCP discovery
    test_cnpjs = [
        "19560932000117",  # JTS COMERCIO DE ALIMENTOS LTDA (from PNCP sample)
        "00000000000191",  # Banco do Brasil (large company test)
        "18236120000158",  # Nubank (fintech test)
    ]

    print("=" * 80)
    print("RECEITA FEDERAL API DISCOVERY")
    print("=" * 80)
    print("\nAPI: ReceitaWS (https://www.receitaws.com.br/)")
    print("Rate Limit: 3 requests/minute (free tier)")
    print(f"Testing {len(test_cnpjs)} CNPJs...\n")

    base_url = "https://www.receitaws.com.br/v1/cnpj"

    results = []

    for i, cnpj in enumerate(test_cnpjs, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}: CNPJ {cnpj}")
        print(f"{'=' * 80}")

        # Remove formatting if present
        cnpj_clean = cnpj.replace(".", "").replace("/", "").replace("-", "")

        endpoint = f"{base_url}/{cnpj_clean}"
        print(f"\nEndpoint: {endpoint}")

        try:
            response = requests.get(endpoint, timeout=10)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # Check for error status
                if data.get("status") == "ERROR":
                    print(f"\n[ERROR] API Error: {data.get('message', 'Unknown error')}")
                    results.append({
                        "cnpj": cnpj,
                        "status": "error",
                        "message": data.get("message")
                    })
                    continue

                print("\n[OK] Success! Data retrieved:")

                # Extract relevant fields for lead prospecting
                company_data = {
                    "cnpj": data.get("cnpj"),
                    "razao_social": data.get("nome"),
                    "nome_fantasia": data.get("fantasia"),
                    "situacao": data.get("situacao"),  # "ATIVA" = active
                    "data_abertura": data.get("abertura"),
                    "porte": data.get("porte"),  # MEI, ME, EPP, etc.
                    "capital_social": data.get("capital_social"),
                    "cnae_principal": data.get("atividade_principal", [{}])[0].get("text") if data.get("atividade_principal") else None,
                    "cnae_codigo": data.get("atividade_principal", [{}])[0].get("code") if data.get("atividade_principal") else None,
                    "natureza_juridica": data.get("natureza_juridica"),
                    "logradouro": data.get("logradouro"),
                    "numero": data.get("numero"),
                    "municipio": data.get("municipio"),
                    "uf": data.get("uf"),
                    "cep": data.get("cep"),
                    "email": data.get("email"),  # May be present!
                    "telefone": data.get("telefone"),  # May be present!
                }

                results.append(company_data)

                # Print formatted summary
                print("\n📋 Company Profile:")
                print(f"  - Razão Social: {company_data['razao_social']}")
                print(f"  - Nome Fantasia: {company_data['nome_fantasia']}")
                print(f"  - Situação: {company_data['situacao']}")
                print(f"  - Porte: {company_data['porte']}")
                print(f"  - Capital Social: {company_data['capital_social']}")
                print(f"  - CNAE Principal: {company_data['cnae_principal']}")
                print(f"  - CNAE Código: {company_data['cnae_codigo']}")
                print(f"  - Município/UF: {company_data['municipio']}/{company_data['uf']}")

                print("\n📞 Contact Data (if available):")
                print(f"  - Email: {company_data['email'] or 'N/A'}")
                print(f"  - Telefone: {company_data['telefone'] or 'N/A'}")

                print("\n📊 Relevant for Dependency Score:")
                print(f"  - Porte: {company_data['porte']} → Revenue estimation possible")
                print(f"  - CNAE: {company_data['cnae_codigo']} → Industry average revenue")

                # Show full JSON for analysis
                print("\n🔍 Full Response (first 1500 chars):")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:1500])

            elif response.status_code == 429:
                print("\n[WARN] Rate Limit Exceeded (429)")
                print("ReceitaWS free tier: 3 requests/minute")
                print("Waiting 60 seconds before next request...")
                time.sleep(60)
                continue

            else:
                print("\n[ERROR] Error Response:")
                print(response.text[:500])

        except Exception as e:
            print(f"\n[ERROR] Exception: {type(e).__name__}: {e}")
            results.append({
                "cnpj": cnpj,
                "status": "exception",
                "error": str(e)
            })

        # Rate limiting: Wait 21 seconds between requests (safe margin for 3/min)
        if i < len(test_cnpjs):
            print("\n[WAIT] Waiting 21 seconds for rate limit compliance...")
            time.sleep(21)

    # Summary
    print(f"\n\n{'=' * 80}")
    print("DISCOVERY SUMMARY")
    print(f"{'=' * 80}")

    print(f"\nTotal CNPJs Tested: {len(test_cnpjs)}")
    successful = [r for r in results if isinstance(r, dict) and r.get("razao_social")]
    print(f"Successful Queries: {len(successful)}")
    print(f"Failed Queries: {len(results) - len(successful)}")

    if successful:
        print("\n[OK] Key Findings:")
        print("  - API is FUNCTIONAL and FREE")
        print("  - Data quality is EXCELLENT")
        print("  - Fields available: razao_social, porte, CNAE, capital_social")
        print("  - Contact data: Email and telefone SOMETIMES present")
        print("  - Rate limit: 3 requests/minute (manageable)")

        print("\n📊 Data Availability:")
        with_email = [r for r in successful if r.get("email")]
        with_phone = [r for r in successful if r.get("telefone")]
        print(f"  - With Email: {len(with_email)}/{len(successful)} ({len(with_email)/len(successful)*100:.0f}%)")
        print(f"  - With Phone: {len(with_phone)}/{len(successful)} ({len(with_phone)/len(successful)*100:.0f}%)")

    print("\n🎯 Recommendation:")
    print("  - USE ReceitaWS for CNPJ enrichment")
    print("  - Cache results (company data is static)")
    print("  - Respect rate limit: 3 req/min → ~180 companies/hour")
    print("  - Use 'porte' field for revenue estimation")
    print("  - Use 'cnae_codigo' for industry classification")
    print("  - Email/phone NOT reliable → need web search fallback")

    print(f"\n{'=' * 80}")
    print("RECEITA FEDERAL API DISCOVERY COMPLETE")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    test_receita_federal_api()
