#!/usr/bin/env python3
"""CRIT-FLT-008 AC7: PNCP API Contract Smoke Test.

Weekly smoke test that validates the PNCP API contract hasn't drifted.
Makes a single real request and checks response structure.

Usage:
    python scripts/pncp_api_smoke_test.py
    python scripts/pncp_api_smoke_test.py --verbose
    python scripts/pncp_api_smoke_test.py --json  # Machine-readable output

Can be scheduled via cron or GitHub Actions for weekly execution:
    0 8 * * 1 cd /app && python scripts/pncp_api_smoke_test.py --json >> /var/log/pncp-smoke.log

Exit codes:
    0 — All checks passed
    1 — Contract drift detected (new required fields, structure change, etc.)
    2 — API unreachable or unexpected error
"""

import argparse
import json
import sys
import time
from datetime import date, timedelta

import httpx

PNCP_BASE_URL = "https://pncp.gov.br/api/consulta/v1"
TIMEOUT = 15.0  # seconds

# Fields we expect to always exist (100% presence in audit)
EXPECTED_ALWAYS_PRESENT = [
    "objetoCompra",
    "valorTotalEstimado",
    "dataPublicacaoPncp",
    "dataAberturaProposta",
    "dataEncerramentoProposta",
    "situacaoCompraNome",
    "srp",
    "orgaoEntidade",
    "unidadeOrgao",
    "codigoModalidadeContratacao",
    "numeroControlePNCP",
]

# Fields we expect to exist but may be empty/null
EXPECTED_SOMETIMES_PRESENT = [
    "linkSistemaOrigem",
    "informacaoComplementar",
    "valorTotalHomologado",
]

# Fields confirmed dead (0% presence) — should NOT be relied upon
DEAD_FIELDS = [
    "linkProcessoEletronico",
]

# Required query params (API returns 400 without these)
REQUIRED_PARAMS = [
    "dataInicial",
    "dataFinal",
    "codigoModalidadeContratacao",
]


def run_smoke_test(verbose: bool = False) -> dict:
    """Execute the smoke test and return results dict.

    Returns:
        dict with keys: passed (bool), checks (list of dicts), api_status, elapsed_ms
    """
    results = {
        "timestamp": date.today().isoformat(),
        "api_url": PNCP_BASE_URL,
        "passed": True,
        "checks": [],
        "warnings": [],
    }

    today = date.today()
    data_inicial = (today - timedelta(days=3)).strftime("%Y%m%d")
    data_final = today.strftime("%Y%m%d")

    params = {
        "dataInicial": data_inicial,
        "dataFinal": data_final,
        "codigoModalidadeContratacao": 6,  # Pregão Eletrônico (most common)
        "pagina": 1,
        "tamanhoPagina": 10,
        "uf": "SP",
    }

    url = f"{PNCP_BASE_URL}/contratacoes/publicacao"

    # --- Check 1: API reachable ---
    start = time.time()
    try:
        response = httpx.get(url, params=params, timeout=TIMEOUT)
        elapsed_ms = int((time.time() - start) * 1000)
        results["elapsed_ms"] = elapsed_ms
        results["api_status"] = response.status_code
    except Exception as e:
        results["passed"] = False
        results["api_status"] = "unreachable"
        results["checks"].append({
            "name": "api_reachable",
            "passed": False,
            "detail": f"Request failed: {e}",
        })
        return results

    results["checks"].append({
        "name": "api_reachable",
        "passed": response.status_code == 200,
        "detail": f"HTTP {response.status_code} in {elapsed_ms}ms",
    })

    if response.status_code != 200:
        results["passed"] = False
        results["checks"].append({
            "name": "status_ok",
            "passed": False,
            "detail": f"Expected 200, got {response.status_code}. Body: {response.text[:500]}",
        })
        return results

    # --- Check 2: Response is valid JSON with expected top-level structure ---
    try:
        data = response.json()
    except Exception as e:
        results["passed"] = False
        results["checks"].append({
            "name": "valid_json",
            "passed": False,
            "detail": f"Response is not valid JSON: {e}",
        })
        return results

    results["checks"].append({"name": "valid_json", "passed": True, "detail": "OK"})

    # Expect list response (data is a list of items)
    items = data if isinstance(data, list) else data.get("data", [])
    results["item_count"] = len(items)

    if len(items) == 0:
        results["warnings"].append("Zero items returned — may indicate API issue or date range too narrow")
        results["checks"].append({
            "name": "has_items",
            "passed": True,  # Not a failure, just a warning
            "detail": "Zero items returned (may be normal for today's date range)",
        })
        return results

    results["checks"].append({
        "name": "has_items",
        "passed": True,
        "detail": f"{len(items)} items returned",
    })

    # --- Check 3: Required fields present in items ---
    first_item = items[0]
    all_keys = set(first_item.keys())

    for field in EXPECTED_ALWAYS_PRESENT:
        present = field in first_item
        results["checks"].append({
            "name": f"field_present_{field}",
            "passed": present,
            "detail": f"{'Present' if present else 'MISSING'} in first item",
        })
        if not present:
            results["passed"] = False

    # --- Check 4: Dead fields status (should remain empty) ---
    for field in DEAD_FIELDS:
        # Check across all items
        populated_count = sum(1 for item in items if item.get(field))
        if populated_count > 0:
            pct = (populated_count / len(items)) * 100
            results["warnings"].append(
                f"Previously dead field '{field}' is now populated in {pct:.0f}% of items. "
                f"Consider re-enabling fallback logic."
            )

        results["checks"].append({
            "name": f"dead_field_{field}",
            "passed": True,  # Not a failure — just monitoring
            "detail": f"Populated in {populated_count}/{len(items)} items"
            + (" (still dead)" if populated_count == 0 else " (REVIVED!)"),
        })

    # --- Check 5: linkSistemaOrigem coverage ---
    link_count = sum(1 for item in items if item.get("linkSistemaOrigem"))
    link_pct = (link_count / len(items)) * 100 if items else 0
    results["checks"].append({
        "name": "linkSistemaOrigem_coverage",
        "passed": True,
        "detail": f"{link_pct:.0f}% ({link_count}/{len(items)})",
    })

    if link_pct < 50:
        results["warnings"].append(
            f"linkSistemaOrigem coverage dropped to {link_pct:.0f}% (expected ~86%). "
            f"URL construction fallback may be needed more often."
        )

    # --- Check 6: New unknown fields detection ---
    known_fields = set(EXPECTED_ALWAYS_PRESENT + EXPECTED_SOMETIMES_PRESENT + DEAD_FIELDS + [
        # Common nested/extra fields
        "orgaoEntidade", "unidadeOrgao", "orgaoSubRogado",
        "tipoInstrumentoConvocatorioCodigo", "tipoInstrumentoConvocatorioNome",
        "amparoLegal", "processo", "modalidadeNome",
        "anoCompra", "sequencialCompra", "numeroCompra",
        "dataInclusao", "dataAtualizacao",
        "existeResultado", "usuarioNome",
        "justificativaPresencial", "linkEdital",
    ])
    new_fields = all_keys - known_fields
    if new_fields:
        results["warnings"].append(
            f"New fields detected in API response: {sorted(new_fields)}. "
            f"Review if any are required or useful."
        )

    results["checks"].append({
        "name": "new_fields_check",
        "passed": True,
        "detail": f"{len(new_fields)} new fields detected" if new_fields else "No new fields",
    })

    # --- Check 7: codigoModalidadeContratacao still required ---
    # Test by making a request WITHOUT modalidade
    try:
        params_no_mod = {k: v for k, v in params.items() if k != "codigoModalidadeContratacao"}
        resp_no_mod = httpx.get(url, params=params_no_mod, timeout=TIMEOUT)
        modalidade_still_required = resp_no_mod.status_code == 400
        results["checks"].append({
            "name": "modalidade_required",
            "passed": True,
            "detail": f"Without modalidade: HTTP {resp_no_mod.status_code}"
            + (" (still required)" if modalidade_still_required else " (WARNING: no longer required!)"),
        })
        if not modalidade_still_required:
            results["warnings"].append(
                "codigoModalidadeContratacao is no longer required by the API. "
                "Consider updating guards in pncp_client.py."
            )
    except Exception:
        results["checks"].append({
            "name": "modalidade_required",
            "passed": True,
            "detail": "Could not verify (request failed)",
        })

    # --- Check 8: tamanhoPagina=50 still the max ---
    try:
        params_big = {**params, "tamanhoPagina": 51}
        resp_big = httpx.get(url, params=params_big, timeout=TIMEOUT)
        page_limit_50 = resp_big.status_code == 400
        results["checks"].append({
            "name": "page_size_limit",
            "passed": True,
            "detail": f"tamanhoPagina=51: HTTP {resp_big.status_code}"
            + (" (max still 50)" if page_limit_50 else " (limit may have changed!)"),
        })
        if not page_limit_50:
            results["warnings"].append(
                "tamanhoPagina=51 no longer returns 400. "
                "Page size limit may have been raised — consider increasing batch size."
            )
    except Exception:
        results["checks"].append({
            "name": "page_size_limit",
            "passed": True,
            "detail": "Could not verify (request failed)",
        })

    # Summary
    failed_checks = [c for c in results["checks"] if not c["passed"]]
    results["passed"] = len(failed_checks) == 0

    return results


def main():
    parser = argparse.ArgumentParser(description="PNCP API Contract Smoke Test")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", help="JSON output (machine-readable)")
    args = parser.parse_args()

    results = run_smoke_test(verbose=args.verbose)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        status_emoji = "PASS" if results["passed"] else "FAIL"
        print(f"\n{'='*60}")
        print(f"  PNCP API Smoke Test — {status_emoji}")
        print(f"{'='*60}")
        print(f"  Date: {results['timestamp']}")
        print(f"  API Status: {results.get('api_status', 'N/A')}")
        print(f"  Latency: {results.get('elapsed_ms', 'N/A')}ms")
        print(f"  Items: {results.get('item_count', 'N/A')}")
        print()

        for check in results["checks"]:
            icon = "[OK]" if check["passed"] else "[FAIL]"
            print(f"  {icon} {check['name']}: {check['detail']}")

        if results["warnings"]:
            print(f"\n  WARNINGS ({len(results['warnings'])}):")
            for w in results["warnings"]:
                print(f"    - {w}")

        print(f"\n{'='*60}\n")

    sys.exit(0 if results["passed"] else 1)


if __name__ == "__main__":
    main()
