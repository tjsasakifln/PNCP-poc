"""Contract tests for ComprasGov v3 (both legacy + Lei 14.133 endpoints).

Note: as of 2026-03-03, the live ComprasGov v3 homepage is returning JSON 404
for the entire API. The offline contract tests still protect against regressions
when the API comes back online. Live tests are opt-in (disabled by default).
"""

from __future__ import annotations

import os

import httpx
import pytest

from .contract_validator import validate_shape


SNAPSHOT_FILES = [
    "compras_gov_v3/modulo_contratacoes_response.json",
    "compras_gov_v3/modulo_lei_14133_response.json",
]


@pytest.mark.contract
@pytest.mark.parametrize("snapshot_file", SNAPSHOT_FILES)
def test_compras_gov_snapshot_matches_schema(
    snapshot_file, compras_gov_v3_schema, load_snapshot
):
    data = load_snapshot(snapshot_file)
    result = validate_shape(data["response"], compras_gov_v3_schema)
    assert result.valid, (
        f"Snapshot {snapshot_file} drifted from schema:\n  - "
        + "\n  - ".join(result.errors)
    )


@pytest.mark.contract
def test_compras_gov_error_response_has_expected_fields(load_snapshot):
    """The error envelope is not part of the success schema but we still
    validate its shape so handlers can rely on its fields."""

    snapshot = load_snapshot("compras_gov_v3/search_error_response.json")
    err = snapshot["response"]
    for field in ("status", "error", "message"):
        assert field in err, f"Error envelope missing field: {field}"
    assert isinstance(err["status"], int)


@pytest.mark.external
@pytest.mark.skipif(
    not os.getenv("RUN_LIVE_CONTRACT_TESTS"),
    reason="Live contract check opt-in (set RUN_LIVE_CONTRACT_TESTS=1)",
)
def test_live_compras_gov_matches_schema(compras_gov_v3_schema):
    url = (
        "https://dadosabertos.compras.gov.br/"
        "modulo-contratacoes/3_consultarLicitacao"
    )

    last_exc: Exception | None = None
    for _ in range(3):
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url, params={"pagina": 1, "tamanhoPagina": 10})
            resp.raise_for_status()
            payload = resp.json()
            result = validate_shape(payload, compras_gov_v3_schema)
            assert result.valid, (
                "Live ComprasGov response drifted from schema:\n  - "
                + "\n  - ".join(result.errors)
            )
            return
        except (httpx.HTTPError, httpx.TransportError) as exc:
            last_exc = exc
    raise AssertionError(
        f"Live ComprasGov request failed after 3 attempts: {last_exc}"
    )
