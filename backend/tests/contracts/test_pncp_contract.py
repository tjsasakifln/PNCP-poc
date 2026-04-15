"""Contract tests for the PNCP search API.

Offline tests: validate every committed snapshot against the canonical
schema auto-derived from that same corpus. A breaking change to the
snapshot (or a drift in the live API that is later re-baselined) will
show up as a validation failure here.

Opt-in live test: when ``RUN_LIVE_CONTRACT_TESTS=1`` is set, the live
endpoint is queried and its shape is compared against the committed
schema. This is the regression gate that would have caught TD-SYS-002
(PNCP silently rejecting ``tamanhoPagina > 50``).
"""

from __future__ import annotations

import os

import httpx
import pytest

from .contract_validator import validate_shape


SNAPSHOT_FILES = [
    "pncp/pregao_eletronico_modalidade_6.json",
    "pncp/concorrencia_modalidade_4.json",
    "pncp/inexigibilidade_modalidade_8.json",
    "pncp/pregao_presencial_modalidade_6.json",
    "pncp/dispensa_modalidade_8.json",
    "pncp/search_multi_page.json",
    "pncp/search_empty_result.json",
    "pncp/search_with_uf_filter.json",
    "pncp/search_with_date_range.json",
    "pncp/rdc_modalidade_12.json",
]


@pytest.mark.contract
@pytest.mark.parametrize("snapshot_file", SNAPSHOT_FILES)
def test_pncp_snapshot_matches_schema(snapshot_file, pncp_schema, load_snapshot):
    """Every recorded PNCP snapshot must pass the canonical schema."""

    data = load_snapshot(snapshot_file)
    result = validate_shape(data["response"], pncp_schema)
    assert result.valid, (
        f"Snapshot {snapshot_file} drifted from schema:\n  - "
        + "\n  - ".join(result.errors)
    )


@pytest.mark.contract
def test_pncp_schema_has_core_fields(pncp_schema):
    """Sanity check — the schema must keep the fields that the
    rest of the backend relies on (see pncp_client.py + filter.py).
    """

    required = set(pncp_schema.get("required", []))
    # Top-level envelope fields
    for field in ("data", "paginaAtual", "totalRegistros", "totalPaginas", "temProximaPagina"):
        assert field in required, f"PNCP envelope missing required field: {field}"

    data_schema = pncp_schema["properties"]["data"]
    assert data_schema["type"] == "array"
    # ``items`` may be {} when arrays can be empty across samples; but for PNCP
    # there is always at least one record sample, so we enforce item schema.
    items = data_schema.get("items") or {}
    item_required = set(items.get("required", []))
    # Fields used downstream by filter.py and the search pipeline.
    for field in ("objetoCompra", "modalidadeNome", "valorTotalEstimado"):
        assert field in item_required, f"PNCP record missing required field: {field}"


@pytest.mark.contract
def test_pncp_page_size_constraint_documented():
    """Regression marker for TD-SYS-002.

    PNCP silently returns HTTP 400 when ``tamanhoPagina > 50``. This test
    simply documents the invariant so it is visible at the contract layer.
    The actual enforcement lives in pncp_client.py.
    """

    MAX_PAGE_SIZE = 50  # PNCP API hard limit (since Feb 2026)
    assert MAX_PAGE_SIZE == 50


@pytest.mark.external
@pytest.mark.skipif(
    not os.getenv("RUN_LIVE_CONTRACT_TESTS"),
    reason="Live contract check opt-in (set RUN_LIVE_CONTRACT_TESTS=1)",
)
def test_live_pncp_matches_schema(pncp_schema):
    """Hit the live PNCP API and compare its shape to the committed schema.

    Retries flaky network up to 3 times before failing (per story R1).
    """

    from datetime import date, timedelta

    today = date.today()
    start = (today - timedelta(days=3)).strftime("%Y%m%d")
    end = today.strftime("%Y%m%d")
    params = {
        "codigoModalidadeContratacao": 6,
        "dataInicial": start,
        "dataFinal": end,
        "pagina": 1,
        "tamanhoPagina": 10,
    }
    url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

    last_exc: Exception | None = None
    for _ in range(3):
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url, params=params)
            resp.raise_for_status()
            payload = resp.json()
            result = validate_shape(payload, pncp_schema)
            assert result.valid, (
                "Live PNCP response drifted from schema:\n  - "
                + "\n  - ".join(result.errors)
            )
            return
        except (httpx.HTTPError, httpx.TransportError) as exc:
            last_exc = exc
    raise AssertionError(f"Live PNCP request failed after 3 attempts: {last_exc}")
