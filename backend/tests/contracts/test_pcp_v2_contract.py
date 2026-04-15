"""Contract tests for the PCP v2 (Portal de Compras Públicas) search API."""

from __future__ import annotations

import os

import httpx
import pytest

from .contract_validator import validate_shape


SNAPSHOT_FILES = [
    "pcp_v2/search_response.json",
    "pcp_v2/search_empty.json",
    "pcp_v2/search_second_page.json",
]


@pytest.mark.contract
@pytest.mark.parametrize("snapshot_file", SNAPSHOT_FILES)
def test_pcp_v2_snapshot_matches_schema(snapshot_file, pcp_v2_schema, load_snapshot):
    data = load_snapshot(snapshot_file)
    result = validate_shape(data["response"], pcp_v2_schema)
    assert result.valid, (
        f"Snapshot {snapshot_file} drifted from schema:\n  - "
        + "\n  - ".join(result.errors)
    )


@pytest.mark.contract
def test_pcp_v2_schema_has_pagination_envelope(pcp_v2_schema):
    required = set(pcp_v2_schema.get("required", []))
    # PCP v2 uses a different envelope than PNCP.
    for field in ("currentPage", "pageCount", "result", "total"):
        assert field in required, f"PCP v2 envelope missing required field: {field}"


@pytest.mark.external
@pytest.mark.skipif(
    not os.getenv("RUN_LIVE_CONTRACT_TESTS"),
    reason="Live contract check opt-in (set RUN_LIVE_CONTRACT_TESTS=1)",
)
def test_live_pcp_v2_matches_schema(pcp_v2_schema):
    url = "https://compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos"

    last_exc: Exception | None = None
    for _ in range(3):
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url, params={"page": 1})
            resp.raise_for_status()
            payload = resp.json()
            result = validate_shape(payload, pcp_v2_schema)
            assert result.valid, (
                "Live PCP v2 response drifted from schema:\n  - "
                + "\n  - ".join(result.errors)
            )
            return
        except (httpx.HTTPError, httpx.TransportError) as exc:
            last_exc = exc
    raise AssertionError(f"Live PCP v2 request failed after 3 attempts: {last_exc}")
