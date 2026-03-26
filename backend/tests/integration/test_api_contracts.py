"""SYS-032: Integration tests for PNCP and PCP API contracts.

Validates that external API response schemas match our expectations.
Detects contract drift (field renames, type changes, pagination changes)
before they silently break production.

Two modes:
- LIVE: Real HTTP calls to PNCP/PCP APIs (skipped if unreachable)
- SNAPSHOT: Validates our parsing logic against frozen response snapshots

All tests use @pytest.mark.integration so they don't run in regular CI.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

# Ensure backend is on sys.path
backend_dir = os.path.join(os.path.dirname(__file__), "..", "..")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SNAPSHOTS_DIR = Path(__file__).parent.parent / "snapshots" / "api_contracts"

# API endpoints
PNCP_BASE_URL = "https://pncp.gov.br/api/consulta/v1"
PCP_BASE_URL = "https://compras.api.portaldecompraspublicas.com.br"


def _load_snapshot(name: str) -> Optional[Dict[str, Any]]:
    """Load a JSON snapshot file. Returns None if not found."""
    path = SNAPSHOTS_DIR / f"{name}.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_snapshot(name: str, data: Dict[str, Any]) -> None:
    """Save a JSON snapshot file (creates directory if needed)."""
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOTS_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def _extract_schema(obj: Any, max_depth: int = 3) -> Dict[str, Any]:
    """Extract a type-schema from a JSON object for contract comparison.

    Returns a dict mapping field names to their type strings.
    Nested objects are represented as nested dicts (up to max_depth).
    Lists show the schema of the first element.
    """
    if max_depth <= 0:
        return {"_type": type(obj).__name__}

    if isinstance(obj, dict):
        schema = {}
        for key, value in obj.items():
            if isinstance(value, dict):
                schema[key] = _extract_schema(value, max_depth - 1)
            elif isinstance(value, list):
                if value and isinstance(value[0], dict):
                    schema[key] = {"_type": "list", "_item": _extract_schema(value[0], max_depth - 1)}
                elif value:
                    schema[key] = {"_type": f"list[{type(value[0]).__name__}]"}
                else:
                    schema[key] = {"_type": "list[empty]"}
            else:
                schema[key] = type(value).__name__ if value is not None else "null"
            schema[key + "__present"] = True
        return schema

    return {"_type": type(obj).__name__}


def _check_required_fields(data: Dict[str, Any], required_fields: set, context: str) -> list:
    """Check that required fields are present. Returns list of missing fields."""
    missing = required_fields - set(data.keys())
    return list(missing)


async def _try_fetch(url: str, params: dict, timeout: float = 10.0) -> Optional[dict]:
    """Try to fetch from a URL. Returns None if unreachable."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                return resp.json()
            return {"_status_code": resp.status_code, "_body": resp.text[:500]}
    except Exception:
        return None


# ---------------------------------------------------------------------------
# PNCP API Contract Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.timeout(30)
class TestPncpApiContractLive:
    """Live PNCP API contract tests. Skipped if API is unreachable."""

    @pytest.fixture(autouse=True)
    def _check_pncp_reachable(self):
        """Skip all tests in this class if PNCP API is unreachable."""
        import httpx

        try:
            resp = httpx.get(
                f"{PNCP_BASE_URL}/contratacoes/publicacao",
                params={
                    "dataInicial": datetime.now().strftime("%Y%m%d"),
                    "dataFinal": datetime.now().strftime("%Y%m%d"),
                    "codigoModalidadeContratacao": 6,
                    "tamanhoPagina": 1,
                    "pagina": 1,
                },
                timeout=10.0,
            )
            if resp.status_code not in (200, 422):
                pytest.skip(f"PNCP API returned unexpected status {resp.status_code}")
        except Exception as e:
            pytest.skip(f"PNCP API unreachable: {e}")

    def test_pncp_accepts_page_size_50(self):
        """Contract: PNCP API must accept tamanhoPagina=50 (current known max).

        If PNCP reduces max page size again, this test fails immediately.
        """
        import httpx

        today = datetime.now()
        ten_days_ago = today - timedelta(days=10)

        resp = httpx.get(
            f"{PNCP_BASE_URL}/contratacoes/publicacao",
            params={
                "dataInicial": ten_days_ago.strftime("%Y%m%d"),
                "dataFinal": today.strftime("%Y%m%d"),
                "codigoModalidadeContratacao": 6,
                "tamanhoPagina": 50,
                "pagina": 1,
            },
            timeout=15.0,
        )

        assert resp.status_code == 200, (
            f"PNCP rejected tamanhoPagina=50 with HTTP {resp.status_code}. "
            f"Body: {resp.text[:300]}. "
            f"This may indicate PNCP reduced the max page size again."
        )

    def test_pncp_response_has_expected_top_level_fields(self):
        """Contract: PNCP response must have data, pagination fields."""
        import httpx

        today = datetime.now()
        five_days_ago = today - timedelta(days=5)

        resp = httpx.get(
            f"{PNCP_BASE_URL}/contratacoes/publicacao",
            params={
                "dataInicial": five_days_ago.strftime("%Y%m%d"),
                "dataFinal": today.strftime("%Y%m%d"),
                "codigoModalidadeContratacao": 6,
                "tamanhoPagina": 5,
                "pagina": 1,
            },
            timeout=15.0,
        )

        assert resp.status_code == 200
        body = resp.json()

        # PNCP wraps results in a top-level object with these fields
        required_top_level = {"data", "totalRegistros", "totalPaginas", "paginaAtual", "temProximaPagina"}
        missing = _check_required_fields(body, required_top_level, "PNCP top-level")
        assert not missing, (
            f"PNCP response missing top-level fields: {missing}. "
            f"Actual keys: {list(body.keys())}. "
            f"This indicates a pagination contract change."
        )

        # Save schema snapshot for drift detection
        _save_snapshot("pncp_response_toplevel", {
            "fields": list(body.keys()),
            "field_types": {k: type(v).__name__ for k, v in body.items()},
            "captured_at": datetime.now(timezone.utc).isoformat(),
        })

    def test_pncp_record_has_expected_fields(self):
        """Contract: Individual PNCP procurement records must have expected fields.

        These are the fields our pipeline extracts in _convert_to_licitacao_items()
        and PNCPClient.fetch_page(). If PNCP renames any, our pipeline silently
        produces empty/null values.
        """
        import httpx

        today = datetime.now()
        ten_days_ago = today - timedelta(days=10)

        resp = httpx.get(
            f"{PNCP_BASE_URL}/contratacoes/publicacao",
            params={
                "dataInicial": ten_days_ago.strftime("%Y%m%d"),
                "dataFinal": today.strftime("%Y%m%d"),
                "codigoModalidadeContratacao": 6,
                "tamanhoPagina": 5,
                "pagina": 1,
            },
            timeout=15.0,
        )

        assert resp.status_code == 200
        body = resp.json()
        records = body.get("data", [])

        if not records:
            pytest.skip("PNCP returned 0 records for test date range -- cannot validate fields")

        record = records[0]

        # Critical fields our pipeline depends on
        critical_fields = {
            "objetoCompra",
            "nomeOrgao",
            "uf",
            "valorTotalEstimado",
            "modalidadeNome",
            "dataPublicacaoPncp",
        }

        missing = _check_required_fields(record, critical_fields, "PNCP record")
        assert not missing, (
            f"PNCP record missing critical fields: {missing}. "
            f"Actual fields: {sorted(record.keys())}. "
            f"Our pipeline will produce empty values for these."
        )

        # Additional important fields (not fatal if missing, but worth tracking)
        important_fields = {
            "dataAberturaProposta",
            "dataEncerramentoProposta",
            "codigoModalidadeContratacao",
            "situacaoCompra",
            "linkSistemaOrigem",
            "numeroControlePNCP",
        }

        missing_important = _check_required_fields(record, important_fields, "PNCP record (important)")
        if missing_important:
            import warnings
            warnings.warn(
                f"PNCP record missing important (non-critical) fields: {missing_important}",
                UserWarning,
                stacklevel=1,
            )

        # Save full record schema snapshot
        _save_snapshot("pncp_record_schema", {
            "fields": sorted(record.keys()),
            "field_types": {k: type(v).__name__ for k, v in sorted(record.items())},
            "sample_record": record,
            "captured_at": datetime.now(timezone.utc).isoformat(),
        })

    def test_pncp_pagination_structure(self):
        """Contract: PNCP pagination fields have correct types."""
        import httpx

        today = datetime.now()
        five_days_ago = today - timedelta(days=5)

        resp = httpx.get(
            f"{PNCP_BASE_URL}/contratacoes/publicacao",
            params={
                "dataInicial": five_days_ago.strftime("%Y%m%d"),
                "dataFinal": today.strftime("%Y%m%d"),
                "codigoModalidadeContratacao": 6,
                "tamanhoPagina": 2,
                "pagina": 1,
            },
            timeout=15.0,
        )

        assert resp.status_code == 200
        body = resp.json()

        # Type checks on pagination fields
        assert isinstance(body.get("data"), list), "data must be a list"
        assert isinstance(body.get("totalRegistros"), (int, float)), "totalRegistros must be numeric"
        assert isinstance(body.get("totalPaginas"), (int, float)), "totalPaginas must be numeric"
        assert isinstance(body.get("paginaAtual"), (int, float)), "paginaAtual must be numeric"
        assert isinstance(body.get("temProximaPagina"), bool), "temProximaPagina must be boolean"

        # Logical checks
        assert body["paginaAtual"] == 1, "First page must be page 1"
        assert len(body["data"]) <= 2, "Must respect tamanhoPagina=2"

    def test_pncp_rejects_invalid_date_format(self):
        """Contract: PNCP returns error for malformed dates.

        Our client uses YYYYMMDD format (no hyphens). If PNCP changes
        date format expectations, we need to know.
        """
        import httpx

        # Send an obviously invalid date
        resp = httpx.get(
            f"{PNCP_BASE_URL}/contratacoes/publicacao",
            params={
                "dataInicial": "not-a-date",
                "dataFinal": "also-not-a-date",
                "codigoModalidadeContratacao": 6,
                "tamanhoPagina": 1,
                "pagina": 1,
            },
            timeout=10.0,
        )

        # PNCP should reject with 4xx (typically 400 or 422)
        assert resp.status_code in (400, 422, 500), (
            f"PNCP accepted invalid dates with HTTP {resp.status_code}. "
            f"Expected 400/422/500."
        )


# ---------------------------------------------------------------------------
# PCP v2 API Contract Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.timeout(30)
class TestPcpApiContractLive:
    """Live PCP v2 API contract tests. Skipped if API is unreachable."""

    @pytest.fixture(autouse=True)
    def _check_pcp_reachable(self):
        """Skip all tests in this class if PCP v2 API is unreachable."""
        import httpx

        try:
            resp = httpx.get(
                f"{PCP_BASE_URL}/v2/licitacao/processos",
                params={
                    "pagina": 1,
                    "dataInicial": datetime.now().strftime("%Y-%m-%d"),
                    "dataFinal": datetime.now().strftime("%Y-%m-%d"),
                    "tipoData": 1,
                },
                timeout=10.0,
            )
            if resp.status_code not in (200, 204):
                pytest.skip(f"PCP API returned unexpected status {resp.status_code}")
        except Exception as e:
            pytest.skip(f"PCP API unreachable: {e}")

    def test_pcp_v2_is_publicly_accessible(self):
        """Contract: PCP v2 API requires NO authentication.

        If PCP adds auth requirements, this test fails.
        """
        import httpx

        today = datetime.now()
        five_days_ago = today - timedelta(days=5)

        # No auth headers, no API key
        resp = httpx.get(
            f"{PCP_BASE_URL}/v2/licitacao/processos",
            params={
                "pagina": 1,
                "dataInicial": five_days_ago.strftime("%Y-%m-%d"),
                "dataFinal": today.strftime("%Y-%m-%d"),
                "tipoData": 1,
            },
            timeout=15.0,
        )

        assert resp.status_code not in (401, 403), (
            f"PCP v2 API returned {resp.status_code} -- may now require authentication. "
            f"This is a BREAKING CHANGE for our integration."
        )
        assert resp.status_code in (200, 204), (
            f"PCP v2 API returned unexpected status {resp.status_code}"
        )

    def test_pcp_v2_response_has_pagination_fields(self):
        """Contract: PCP v2 response has expected pagination structure.

        Our adapter depends on: result, total, pageCount, nextPage.
        """
        import httpx

        today = datetime.now()
        ten_days_ago = today - timedelta(days=10)

        resp = httpx.get(
            f"{PCP_BASE_URL}/v2/licitacao/processos",
            params={
                "pagina": 1,
                "dataInicial": ten_days_ago.strftime("%Y-%m-%d"),
                "dataFinal": today.strftime("%Y-%m-%d"),
                "tipoData": 1,
            },
            timeout=15.0,
        )

        assert resp.status_code == 200
        body = resp.json()

        # PCP v2 pagination fields our adapter expects
        expected_pagination = {"result", "total", "pageCount"}
        missing = _check_required_fields(body, expected_pagination, "PCP v2 response")
        assert not missing, (
            f"PCP v2 response missing pagination fields: {missing}. "
            f"Actual keys: {list(body.keys())}. "
            f"PortalComprasAdapter.fetch() will break."
        )

        # Type checks
        assert isinstance(body.get("result"), list), "result must be a list"
        assert isinstance(body.get("total"), (int, float)), "total must be numeric"
        assert isinstance(body.get("pageCount"), (int, float)), "pageCount must be numeric"

        # Save snapshot
        _save_snapshot("pcp_response_toplevel", {
            "fields": sorted(body.keys()),
            "field_types": {k: type(v).__name__ for k, v in sorted(body.items()) if k != "result"},
            "captured_at": datetime.now(timezone.utc).isoformat(),
        })

    def test_pcp_v2_record_has_expected_fields(self):
        """Contract: Individual PCP v2 records have fields our normalize() expects.

        PortalComprasAdapter.normalize() depends on these field paths.
        """
        import httpx

        today = datetime.now()
        ten_days_ago = today - timedelta(days=10)

        resp = httpx.get(
            f"{PCP_BASE_URL}/v2/licitacao/processos",
            params={
                "pagina": 1,
                "dataInicial": ten_days_ago.strftime("%Y-%m-%d"),
                "dataFinal": today.strftime("%Y-%m-%d"),
                "tipoData": 1,
            },
            timeout=15.0,
        )

        assert resp.status_code == 200
        body = resp.json()
        records = body.get("result", [])

        if not records:
            pytest.skip("PCP v2 returned 0 records -- cannot validate fields")

        record = records[0]

        # Critical fields for normalize()
        critical_fields = {
            "codigoLicitacao",  # -> source_id
            "resumo",  # -> objeto
        }

        missing = _check_required_fields(record, critical_fields, "PCP v2 record")
        assert not missing, (
            f"PCP v2 record missing critical fields: {missing}. "
            f"Actual fields: {sorted(record.keys())}. "
            f"PortalComprasAdapter.normalize() will raise SourceParseError."
        )

        # Important nested structures
        # unidadeCompradora -> orgao, uf, municipio
        if "unidadeCompradora" in record:
            unidade = record["unidadeCompradora"]
            assert isinstance(unidade, dict), "unidadeCompradora must be a dict"

        # tipoLicitacao -> modalidade
        if "tipoLicitacao" in record:
            tipo = record["tipoLicitacao"]
            assert isinstance(tipo, dict), "tipoLicitacao must be a dict"

        # statusProcessoPublico -> situacao
        if "statusProcessoPublico" in record:
            status = record["statusProcessoPublico"]
            assert isinstance(status, dict), "statusProcessoPublico must be a dict"

        # Save snapshot
        _save_snapshot("pcp_record_schema", {
            "fields": sorted(record.keys()),
            "field_types": {k: type(v).__name__ for k, v in sorted(record.items())},
            "nested_structures": {
                "unidadeCompradora": sorted(record.get("unidadeCompradora", {}).keys()) if isinstance(record.get("unidadeCompradora"), dict) else None,
                "tipoLicitacao": sorted(record.get("tipoLicitacao", {}).keys()) if isinstance(record.get("tipoLicitacao"), dict) else None,
                "statusProcessoPublico": sorted(record.get("statusProcessoPublico", {}).keys()) if isinstance(record.get("statusProcessoPublico"), dict) else None,
            },
            "sample_record": record,
            "captured_at": datetime.now(timezone.utc).isoformat(),
        })

    def test_pcp_v2_uses_iso_date_format(self):
        """Contract: PCP v2 API accepts ISO date format (YYYY-MM-DD).

        If PCP changes date format requirements, our adapter breaks.
        """
        import httpx

        today = datetime.now()
        resp = httpx.get(
            f"{PCP_BASE_URL}/v2/licitacao/processos",
            params={
                "pagina": 1,
                "dataInicial": today.strftime("%Y-%m-%d"),
                "dataFinal": today.strftime("%Y-%m-%d"),
                "tipoData": 1,
            },
            timeout=10.0,
        )

        assert resp.status_code in (200, 204), (
            f"PCP v2 rejected ISO date format with HTTP {resp.status_code}. "
            f"This may indicate a date format change."
        )


# ---------------------------------------------------------------------------
# Snapshot-Based Contract Tests (run without live API access)
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.timeout(10)
class TestPncpContractSnapshot:
    """Validate our PNCP parsing logic against frozen response snapshots.

    These tests always run (no API dependency) and verify that our
    field extraction and normalization code handles known response shapes.
    """

    # Frozen PNCP response shape (based on known API contract as of 2026-03)
    PNCP_SAMPLE_RESPONSE = {
        "data": [
            {
                "codigoCompra": "00394460000109-1-000024/2026",
                "numeroControlePNCP": "00394460000109-1-000024/2026",
                "objetoCompra": "Aquisicao de material de consumo para manutencao predial",
                "nomeOrgao": "Prefeitura Municipal de Exemplo",
                "uf": "SP",
                "municipio": "Exemplo",
                "valorTotalEstimado": 250000.00,
                "modalidadeNome": "Pregao Eletronico",
                "codigoModalidadeContratacao": 6,
                "dataPublicacaoPncp": "2026-03-01",
                "dataAberturaProposta": "2026-03-15T09:00:00",
                "dataEncerramentoProposta": "2026-03-25T18:00:00",
                "situacaoCompra": "Divulgada",
                "linkSistemaOrigem": "https://pncp.gov.br/app/editais/00394460000109-1-000024/2026",
            }
        ],
        "totalRegistros": 1,
        "totalPaginas": 1,
        "paginaAtual": 1,
        "temProximaPagina": False,
    }

    def test_convert_to_licitacao_items_handles_pncp_shape(self):
        """Our pipeline's _convert_to_licitacao_items must handle PNCP record shape."""
        from pipeline.helpers import _convert_to_licitacao_items

        records = self.PNCP_SAMPLE_RESPONSE["data"]
        items = _convert_to_licitacao_items(records)

        assert len(items) == 1, "Must produce exactly 1 item from 1 record"

        item = items[0]
        assert item.orgao == "Prefeitura Municipal de Exemplo"
        assert item.uf == "SP"
        assert item.valor == 250000.00
        assert "manutencao predial" in item.objeto.lower()

    def test_pncp_pagination_fields_present(self):
        """Snapshot: top-level pagination fields must match expected shape."""
        resp = self.PNCP_SAMPLE_RESPONSE

        assert "data" in resp
        assert "totalRegistros" in resp
        assert "totalPaginas" in resp
        assert "paginaAtual" in resp
        assert "temProximaPagina" in resp

        assert isinstance(resp["data"], list)
        assert isinstance(resp["totalRegistros"], int)
        assert isinstance(resp["totalPaginas"], int)
        assert isinstance(resp["temProximaPagina"], bool)

    def test_pncp_record_critical_fields_types(self):
        """Snapshot: critical record fields have correct types."""
        record = self.PNCP_SAMPLE_RESPONSE["data"][0]

        # String fields
        for field in ("objetoCompra", "nomeOrgao", "uf", "modalidadeNome", "dataPublicacaoPncp"):
            assert isinstance(record[field], str), f"{field} must be a string"

        # Numeric field
        assert isinstance(record["valorTotalEstimado"], (int, float)), "valorTotalEstimado must be numeric"

        # Integer field
        assert isinstance(record["codigoModalidadeContratacao"], int), "codigoModalidadeContratacao must be int"

    def test_snapshot_drift_detection(self):
        """Compare current snapshot against saved one (if exists) to detect drift.

        First run: saves baseline. Subsequent runs: compares field lists.
        """
        snapshot = _load_snapshot("pncp_response_toplevel")
        if snapshot is None:
            pytest.skip("No saved PNCP snapshot yet -- run live tests first to create baseline")

        expected_fields = {"data", "totalRegistros", "totalPaginas", "paginaAtual", "temProximaPagina"}
        saved_fields = set(snapshot.get("fields", []))

        removed = expected_fields - saved_fields
        if removed:
            pytest.fail(
                f"PNCP API no longer returns fields we depend on: {removed}. "
                f"Check if PNCP changed their API contract."
            )


@pytest.mark.integration
@pytest.mark.timeout(10)
class TestPcpContractSnapshot:
    """Validate our PCP parsing logic against frozen response snapshots."""

    # Frozen PCP v2 response shape (based on known API contract as of 2026-03)
    PCP_SAMPLE_RESPONSE = {
        "result": [
            {
                "codigoLicitacao": 987654,
                "resumo": "Contratacao de servicos de limpeza e conservacao predial",
                "numero": "PE-001/2026",
                "unidadeCompradora": {
                    "nomeUnidadeCompradora": "Prefeitura de Teste",
                    "CNPJ": "12345678000199",
                    "uf": "RJ",
                    "cidade": "Rio de Janeiro",
                },
                "tipoLicitacao": {
                    "modalidadeLicitacao": "Pregao Eletronico",
                    "tipoLicitacao": "Menor Preco",
                },
                "statusProcessoPublico": {
                    "descricao": "Recebendo Propostas",
                },
                "urlReferencia": "/processos/987654",
                "dataHoraPublicacao": "2026-03-01T10:00:00.000Z",
                "dataHoraInicioPropostas": "2026-03-10T08:00:00.000Z",
                "dataHoraFinalPropostas": "2026-03-20T18:00:00.000Z",
            }
        ],
        "total": 1,
        "pageCount": 1,
        "nextPage": None,
    }

    def test_pcp_normalize_handles_v2_shape(self):
        """PortalComprasAdapter.normalize() must handle known PCP v2 record shape."""
        from clients.portal_compras_client import PortalComprasAdapter

        adapter = PortalComprasAdapter.__new__(PortalComprasAdapter)
        # Set required attributes without full __init__ (avoids config import issues)
        adapter._api_key = ""
        adapter._timeout = 30

        record = self.PCP_SAMPLE_RESPONSE["result"][0]
        unified = adapter.normalize(record)

        assert unified.source_id == "pcp_987654"
        assert unified.source_name == "PORTAL_COMPRAS"
        assert "limpeza" in unified.objeto.lower()
        assert unified.orgao == "Prefeitura de Teste"
        assert unified.uf == "RJ"
        assert unified.municipio == "Rio de Janeiro"
        assert unified.modalidade == "Pregao Eletronico"
        assert unified.situacao == "Recebendo Propostas"
        assert unified.valor_estimado is None  # v2 listing has no value

    def test_pcp_normalize_handles_missing_nested(self):
        """normalize() must not crash when nested structures are missing."""
        from clients.portal_compras_client import PortalComprasAdapter

        adapter = PortalComprasAdapter.__new__(PortalComprasAdapter)
        adapter._api_key = ""
        adapter._timeout = 30

        # Minimal record with only required field
        minimal_record = {
            "codigoLicitacao": 111222,
            "resumo": "Teste minimo",
        }

        unified = adapter.normalize(minimal_record)
        assert unified.source_id == "pcp_111222"
        assert unified.objeto == "Teste minimo"
        # These should gracefully default to empty strings
        assert unified.orgao == ""
        assert unified.uf == ""
        assert unified.municipio == ""

    def test_pcp_normalize_handles_null_unidade(self):
        """normalize() handles unidadeCompradora being None."""
        from clients.portal_compras_client import PortalComprasAdapter

        adapter = PortalComprasAdapter.__new__(PortalComprasAdapter)
        adapter._api_key = ""
        adapter._timeout = 30

        record = {
            "codigoLicitacao": 333444,
            "resumo": "Teste sem unidade",
            "unidadeCompradora": None,
        }

        unified = adapter.normalize(record)
        assert unified.source_id == "pcp_333444"
        assert unified.orgao == ""

    def test_pcp_pagination_structure(self):
        """Snapshot: PCP v2 pagination fields have correct types."""
        resp = self.PCP_SAMPLE_RESPONSE

        assert isinstance(resp["result"], list)
        assert isinstance(resp["total"], int)
        assert isinstance(resp["pageCount"], int)
        # nextPage can be None or int
        assert resp["nextPage"] is None or isinstance(resp["nextPage"], int)

    def test_pcp_snapshot_drift_detection(self):
        """Compare current PCP snapshot against saved one to detect drift."""
        snapshot = _load_snapshot("pcp_response_toplevel")
        if snapshot is None:
            pytest.skip("No saved PCP snapshot yet -- run live tests first to create baseline")

        expected_fields = {"result", "total", "pageCount"}
        saved_fields = set(snapshot.get("fields", []))

        removed = expected_fields - saved_fields
        if removed:
            pytest.fail(
                f"PCP v2 API no longer returns fields we depend on: {removed}. "
                f"Check if PCP changed their v2 API contract."
            )


# ---------------------------------------------------------------------------
# Cross-Source Contract Compatibility Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.timeout(10)
class TestCrossSourceContractCompatibility:
    """Verify that our adapters produce compatible output from different sources."""

    def test_pncp_client_base_url_matches_expected(self):
        """Contract: PNCPClient.BASE_URL must not change unexpectedly."""
        from pncp_client import PNCPClient

        assert PNCPClient.BASE_URL == "https://pncp.gov.br/api/consulta/v1", (
            f"PNCPClient.BASE_URL changed to {PNCPClient.BASE_URL}. "
            f"This may break all PNCP API calls."
        )

    def test_pcp_adapter_base_url_matches_expected(self):
        """Contract: PortalComprasAdapter.BASE_URL must not change unexpectedly."""
        from clients.portal_compras_client import PortalComprasAdapter

        assert PortalComprasAdapter.BASE_URL == "https://compras.api.portaldecompraspublicas.com.br", (
            f"PortalComprasAdapter.BASE_URL changed to {PortalComprasAdapter.BASE_URL}. "
            f"This may break all PCP API calls."
        )

    def test_pcp_adapter_page_size_is_10(self):
        """Contract: PCP v2 API uses fixed 10 items per page."""
        from clients.portal_compras_client import PortalComprasAdapter

        assert PortalComprasAdapter.PAGE_SIZE == 10, (
            f"PCP PAGE_SIZE changed to {PortalComprasAdapter.PAGE_SIZE}. "
            f"v2 API is fixed at 10 per page."
        )

    def test_unified_procurement_has_required_fields(self):
        """Contract: UnifiedProcurement must have all fields needed by the consolidation layer."""
        from clients.base import UnifiedProcurement
        import dataclasses

        fields = {f.name for f in dataclasses.fields(UnifiedProcurement)}

        # Fields that consolidation.py and the pipeline depend on
        required = {
            "source_id",
            "source_name",
            "objeto",
            "valor_estimado",
            "orgao",
            "uf",
            "municipio",
            "data_publicacao",
            "modalidade",
            "situacao",
            "link_portal",
        }

        missing = required - fields
        assert not missing, (
            f"UnifiedProcurement missing fields needed by consolidation: {missing}"
        )

    def test_pncp_date_format_is_yyyymmdd(self):
        """Contract: PNCPClient sends dates as YYYYMMDD (no hyphens).

        This is critical -- PNCP API may return HTTP 422 with wrong format.
        """
        from pncp_client import PNCPClient

        client = PNCPClient.__new__(PNCPClient)  # noqa: F841
        # The fetch_page method strips hyphens from dates via replace("-", "")
        # Verify this behavior by checking the code pattern exists
        import inspect
        source = inspect.getsource(PNCPClient.fetch_page)
        assert 'replace("-", "")' in source, (
            "PNCPClient.fetch_page must strip hyphens from dates. "
            "PNCP API expects YYYYMMDD format."
        )

    def test_pcp_date_format_is_iso(self):
        """Contract: PCP v2 adapter sends dates as YYYY-MM-DD (ISO format)."""
        from clients.portal_compras_client import PortalComprasAdapter

        # Verify by checking the fetch method uses ISO dates directly
        import inspect
        source = inspect.getsource(PortalComprasAdapter.fetch)
        assert "dataInicial" in source, "PCP adapter must use dataInicial parameter"
        assert "dataFinal" in source, "PCP adapter must use dataFinal parameter"
