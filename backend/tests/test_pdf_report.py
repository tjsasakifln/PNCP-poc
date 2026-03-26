"""Tests for STORY-325 AC16-AC19: PDF report generation endpoint.

Covers:
- AC16: PDF generation returns valid PDF bytes (%PDF- header)
- AC17: Cover page variations (client_name, setor, date)
- AC18: Top N ordering by viability score
- AC19: Invalid / malformed search_id error handling
- Additional edge cases: empty results, missing viability scores, auth guard
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from main import app
from auth import require_auth


# ============================================================================
# Shared sample data
# ============================================================================

def _make_licitacoes(count: int, base_score: int = 90) -> list[dict]:
    """Build a list of bid dicts with descending viability scores."""
    return [
        {
            "pncp_id": f"PNCP-{i:03d}",
            "objeto": f"Fornecimento de uniformes escolares {i}",
            "orgao": f"Prefeitura Municipal {i}",
            "uf": "SP",
            "valor": 100000.0 + (i * 10000),
            "modalidade": "Pregão Eletrônico",
            "data_publicacao": "2026-02-01",
            "data_abertura": "2026-03-15",
            "data_encerramento": "2026-03-20",
            "dias_restantes": max(20 - i, 1),
            "link": f"https://pncp.gov.br/bid/{i}",
            "_viability_score": max(base_score - (i * 3), 0),
            "_viability_level": "alta" if max(base_score - (i * 3), 0) > 70 else "media",
        }
        for i in range(count)
    ]


SAMPLE_RESULTS = {
    "resumo": {
        "resumo_executivo": "Encontradas 15 licitações de uniformes.",
        "total_oportunidades": 15,
        "valor_total": 2500000.0,
        "destaques": ["3 licitações em SP", "Maior valor: R$ 500K"],
        "recomendacoes": [],
        "alertas_urgencia": [],
        "insight_setorial": "",
    },
    "licitacoes": _make_licitacoes(25),
    "setor": "uniformes e fardamentos",
    "ufs": ["SP", "RJ", "MG"],
    "total_raw": 150,
    "total_filtrado": 25,
    "date_from": "2026-02-01",
    "date_to": "2026-02-28",
}

VALID_SEARCH_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


# ============================================================================
# Auth fixtures
# ============================================================================

def _override_auth():
    return {"id": "test-user-id-1234", "email": "test@example.com", "role": "authenticated"}


@pytest.fixture(autouse=True)
def override_auth():
    """Override require_auth for all tests in this module."""
    app.dependency_overrides[require_auth] = _override_auth
    yield
    app.dependency_overrides.pop(require_auth, None)


@pytest.fixture
def client():
    return TestClient(app)


# ============================================================================
# AC16: PDF Generation — Valid Output
# ============================================================================


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_generate_pdf_returns_valid_pdf(mock_get_results, client):
    """Generate PDF and verify it starts with %PDF- header."""
    mock_get_results.return_value = dict(SAMPLE_RESULTS)

    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": VALID_SEARCH_ID},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:5] == b"%PDF-"


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_generate_pdf_response_has_content_disposition(mock_get_results, client):
    """PDF response includes Content-Disposition attachment header."""
    mock_get_results.return_value = dict(SAMPLE_RESULTS)

    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": VALID_SEARCH_ID},
    )

    assert response.status_code == 200
    disposition = response.headers.get("content-disposition", "")
    assert "attachment" in disposition
    assert ".pdf" in disposition


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_generate_pdf_filename_contains_setor(mock_get_results, client):
    """PDF filename in Content-Disposition contains sanitized setor name."""
    mock_get_results.return_value = dict(SAMPLE_RESULTS)

    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": VALID_SEARCH_ID},
    )

    assert response.status_code == 200
    disposition = response.headers.get("content-disposition", "")
    # setor "uniformes e fardamentos" -> "uniformes-e-fardamentos"
    assert "uniformes" in disposition


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_generate_pdf_content_length_matches_body(mock_get_results, client):
    """Content-Length header matches actual PDF body size."""
    mock_get_results.return_value = dict(SAMPLE_RESULTS)

    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": VALID_SEARCH_ID},
    )

    assert response.status_code == 200
    declared_length = int(response.headers.get("content-length", 0))
    assert declared_length == len(response.content)
    assert declared_length > 0


# ============================================================================
# AC17: Cover Page Variations
# ============================================================================


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_with_client_name(mock_get_results, client):
    """PDF generates without error when client_name is provided."""
    mock_get_results.return_value = dict(SAMPLE_RESULTS)

    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": VALID_SEARCH_ID, "client_name": "Empresa ABC Ltda"},
    )

    assert response.status_code == 200
    assert response.content[:5] == b"%PDF-"


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_without_client_name(mock_get_results, client):
    """PDF generates without error when client_name is omitted."""
    mock_get_results.return_value = dict(SAMPLE_RESULTS)

    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": VALID_SEARCH_ID},
    )

    assert response.status_code == 200
    assert response.content[:5] == b"%PDF-"


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_with_null_client_name(mock_get_results, client):
    """PDF generates when client_name is explicitly null."""
    mock_get_results.return_value = dict(SAMPLE_RESULTS)

    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": VALID_SEARCH_ID, "client_name": None},
    )

    assert response.status_code == 200
    assert response.content[:5] == b"%PDF-"


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_cover_has_setor_in_filename(mock_get_results, client):
    """Cover page setor is reflected in the filename."""
    results = dict(SAMPLE_RESULTS)
    results["setor"] = "tecnologia da informacao"
    mock_get_results.return_value = results

    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": VALID_SEARCH_ID},
    )

    assert response.status_code == 200
    disposition = response.headers.get("content-disposition", "")
    assert "tecnologia" in disposition


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_cover_with_empty_setor(mock_get_results, client):
    """Cover page generates without error when setor is empty."""
    results = dict(SAMPLE_RESULTS)
    results["setor"] = ""
    mock_get_results.return_value = results

    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": VALID_SEARCH_ID},
    )

    assert response.status_code == 200
    assert response.content[:5] == b"%PDF-"
    # Falls back to "licitacoes" in filename
    disposition = response.headers.get("content-disposition", "")
    assert "licitacoes" in disposition


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_cover_with_date_range_metadata(mock_get_results, client):
    """PDF generates successfully with date_from and date_to metadata."""
    results = {
        **SAMPLE_RESULTS,
        "date_from": "2026-01-01",
        "date_to": "2026-02-28",
    }
    mock_get_results.return_value = results

    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": VALID_SEARCH_ID},
    )

    assert response.status_code == 200
    assert response.content[:5] == b"%PDF-"


# ============================================================================
# AC18: Top N Ordering
# ============================================================================


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_top_20_default_max_items(mock_get_results, client):
    """Default max_items=20 generates PDF with 30 available bids."""
    results = dict(SAMPLE_RESULTS)
    results["licitacoes"] = _make_licitacoes(30)
    mock_get_results.return_value = results

    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": VALID_SEARCH_ID},
    )

    # Endpoint selects top 20 from 30 — PDF should still be generated
    assert response.status_code == 200
    assert response.content[:5] == b"%PDF-"


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_top_n_sorted_by_viability_score(mock_get_results, client):
    """Opportunities sent to PDF are sorted by _viability_score descending."""
    # Create 30 bids with known scores (descending order in source)
    bids = [
        {
            "pncp_id": f"BID-{i:02d}",
            "objeto": f"Licitação {i}",
            "orgao": "Órgão Teste",
            "uf": "SP",
            "valor": 200000.0,
            "modalidade": "Pregão Eletrônico",
            "data_publicacao": "2026-02-01",
            "data_abertura": "2026-03-01",
            "data_encerramento": "2026-03-10",
            "dias_restantes": 10,
            "link": f"https://pncp.gov.br/bid/{i}",
            "_viability_score": 90 - (i * 2),  # 90, 88, 86 ... 32
            "_viability_level": "alta",
        }
        for i in range(30)
    ]

    # Shuffle so order is not accidentally correct
    import random
    shuffled = list(bids)
    random.seed(42)
    random.shuffle(shuffled)

    results = dict(SAMPLE_RESULTS)
    results["licitacoes"] = shuffled
    mock_get_results.return_value = results

    # Capture what gets passed to generate_diagnostico_pdf
    captured = {}

    import pdf_report

    original_fn = pdf_report.generate_diagnostico_pdf

    def capture_and_call(**kwargs):
        captured["licitacoes"] = kwargs.get("licitacoes", [])
        return original_fn(**kwargs)

    with patch("routes.reports.pdf_report.generate_diagnostico_pdf", side_effect=capture_and_call):
        response = client.post(
            "/v1/reports/diagnostico",
            json={"search_id": VALID_SEARCH_ID, "max_items": 20},
        )

    assert response.status_code == 200

    sent_lics = captured.get("licitacoes", [])
    assert len(sent_lics) == 20

    # Verify sorted by _viability_score descending
    scores = [lic["_viability_score"] for lic in sent_lics]
    assert scores == sorted(scores, reverse=True), (
        f"Scores not sorted descending: {scores}"
    )
    # Top score should be 90 (index 0 in the original ordered list)
    assert scores[0] == 90


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_fewer_than_max_items_shows_all(mock_get_results, client):
    """When fewer results than max_items, all bids are included."""
    results = dict(SAMPLE_RESULTS)
    results["licitacoes"] = _make_licitacoes(5)  # Only 5 bids
    mock_get_results.return_value = results

    captured = {}
    import pdf_report

    original_fn = pdf_report.generate_diagnostico_pdf

    def capture_and_call(**kwargs):
        captured["licitacoes"] = kwargs.get("licitacoes", [])
        return original_fn(**kwargs)

    with patch("routes.reports.pdf_report.generate_diagnostico_pdf", side_effect=capture_and_call):
        response = client.post(
            "/v1/reports/diagnostico",
            json={"search_id": VALID_SEARCH_ID, "max_items": 20},
        )

    assert response.status_code == 200
    assert len(captured.get("licitacoes", [])) == 5


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_custom_max_items_respected(mock_get_results, client):
    """Custom max_items=10 limits the bids sent to PDF generator."""
    results = dict(SAMPLE_RESULTS)
    results["licitacoes"] = _make_licitacoes(30)
    mock_get_results.return_value = results

    captured = {}
    import pdf_report

    original_fn = pdf_report.generate_diagnostico_pdf

    def capture_and_call(**kwargs):
        captured["licitacoes"] = kwargs.get("licitacoes", [])
        return original_fn(**kwargs)

    with patch("routes.reports.pdf_report.generate_diagnostico_pdf", side_effect=capture_and_call):
        response = client.post(
            "/v1/reports/diagnostico",
            json={"search_id": VALID_SEARCH_ID, "max_items": 10},
        )

    assert response.status_code == 200
    assert len(captured.get("licitacoes", [])) == 10


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_max_items_boundary_min(mock_get_results, client):
    """max_items=1 is valid and returns exactly 1 bid."""
    results = dict(SAMPLE_RESULTS)
    results["licitacoes"] = _make_licitacoes(5)
    mock_get_results.return_value = results

    captured = {}
    import pdf_report

    original_fn = pdf_report.generate_diagnostico_pdf

    def capture_and_call(**kwargs):
        captured["licitacoes"] = kwargs.get("licitacoes", [])
        return original_fn(**kwargs)

    with patch("routes.reports.pdf_report.generate_diagnostico_pdf", side_effect=capture_and_call):
        response = client.post(
            "/v1/reports/diagnostico",
            json={"search_id": VALID_SEARCH_ID, "max_items": 1},
        )

    assert response.status_code == 200
    assert len(captured.get("licitacoes", [])) == 1


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_max_items_boundary_max(mock_get_results, client):
    """max_items=50 is the valid upper bound."""
    results = dict(SAMPLE_RESULTS)
    results["licitacoes"] = _make_licitacoes(60)
    mock_get_results.return_value = results

    captured = {}
    import pdf_report

    original_fn = pdf_report.generate_diagnostico_pdf

    def capture_and_call(**kwargs):
        captured["licitacoes"] = kwargs.get("licitacoes", [])
        return original_fn(**kwargs)

    with patch("routes.reports.pdf_report.generate_diagnostico_pdf", side_effect=capture_and_call):
        response = client.post(
            "/v1/reports/diagnostico",
            json={"search_id": VALID_SEARCH_ID, "max_items": 50},
        )

    assert response.status_code == 200
    assert len(captured.get("licitacoes", [])) == 50


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_max_items_above_limit_rejected(mock_get_results, client):
    """max_items=51 exceeds upper bound of 50 and returns 422."""
    mock_get_results.return_value = dict(SAMPLE_RESULTS)

    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": VALID_SEARCH_ID, "max_items": 51},
    )

    assert response.status_code == 422


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_max_items_zero_rejected(mock_get_results, client):
    """max_items=0 is below minimum of 1 and returns 422."""
    mock_get_results.return_value = dict(SAMPLE_RESULTS)

    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": VALID_SEARCH_ID, "max_items": 0},
    )

    assert response.status_code == 422


# ============================================================================
# AC19: Invalid search_id
# ============================================================================


def test_invalid_search_id_returns_404(client):
    """Non-existent search_id (valid UUID format) returns 404."""
    with patch(
        "routes.reports.get_background_results_async",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = client.post(
            "/v1/reports/diagnostico",
            json={"search_id": "00000000-0000-0000-0000-000000000000"},
        )

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "não encontrada" in detail.lower() or "nao encontrada" in detail.lower() or "not found" in detail.lower()


def test_malformed_search_id_returns_400(client):
    """Non-UUID search_id returns 400 Bad Request."""
    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": "not-a-valid-uuid"},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "uuid" in detail.lower() or "inválido" in detail.lower() or "invalido" in detail.lower()


def test_search_id_too_short_returns_400(client):
    """search_id with wrong length returns 400."""
    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": "abc123"},
    )

    assert response.status_code == 400


def test_search_id_with_wrong_separators_returns_400(client):
    """search_id with wrong separator characters returns 400."""
    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": "a1b2c3d4_e5f6_7890_abcd_ef1234567890"},
    )

    assert response.status_code == 400


def test_search_id_with_uppercase_is_valid_uuid(client):
    """search_id with uppercase hex chars (valid UUID variant) is accepted."""
    uppercase_uuid = "A1B2C3D4-E5F6-7890-ABCD-EF1234567890"
    with patch(
        "routes.reports.get_background_results_async",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = client.post(
            "/v1/reports/diagnostico",
            json={"search_id": uppercase_uuid},
        )

    # Valid UUID format — should reach the 404 from no results, not 400
    assert response.status_code == 404


# ============================================================================
# Additional Edge Cases
# ============================================================================


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_empty_licitacoes(mock_get_results, client):
    """PDF generates without error even when licitacoes list is empty."""
    results = dict(SAMPLE_RESULTS)
    results["licitacoes"] = []
    mock_get_results.return_value = results

    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": VALID_SEARCH_ID},
    )

    assert response.status_code == 200
    assert response.content[:5] == b"%PDF-"


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_no_viability_scores_triggers_assess_batch(mock_get_results, client):
    """When bids lack _viability_score, assess_batch is called to compute scores."""
    bids_without_scores = [
        {
            "pncp_id": f"BID-{i}",
            "objeto": f"Objeto {i}",
            "orgao": "Órgão X",
            "uf": "SP",
            "valor": 150000.0,
            "modalidade": "Pregão Eletrônico",
            "data_encerramento": "2026-04-01",
            "dias_restantes": 30,
            "link": f"https://pncp.gov.br/bid/{i}",
        }
        for i in range(5)
    ]

    results = dict(SAMPLE_RESULTS)
    results["licitacoes"] = bids_without_scores
    mock_get_results.return_value = results

    with patch("routes.reports.assess_batch") as mock_assess:
        response = client.post(
            "/v1/reports/diagnostico",
            json={"search_id": VALID_SEARCH_ID},
        )

    assert response.status_code == 200
    mock_assess.assert_called_once()


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_with_viability_scores_skips_assess_batch(mock_get_results, client):
    """When bids already have _viability_score, assess_batch is NOT called."""
    mock_get_results.return_value = dict(SAMPLE_RESULTS)  # has _viability_score

    with patch("routes.reports.assess_batch") as mock_assess:
        response = client.post(
            "/v1/reports/diagnostico",
            json={"search_id": VALID_SEARCH_ID},
        )

    assert response.status_code == 200
    mock_assess.assert_not_called()


def test_endpoint_requires_auth(client):
    """Endpoint returns 401/403 without auth token."""
    # Remove the autouse override temporarily
    app.dependency_overrides.pop(require_auth, None)

    try:
        response = client.post(
            "/v1/reports/diagnostico",
            json={"search_id": VALID_SEARCH_ID},
        )
        assert response.status_code in (401, 403)
    finally:
        # Restore for other tests in this session
        app.dependency_overrides[require_auth] = _override_auth


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_generation_failure_returns_500(mock_get_results, client):
    """When PDF generation raises an exception, endpoint returns 500."""
    mock_get_results.return_value = dict(SAMPLE_RESULTS)

    with patch("routes.reports.pdf_report.generate_diagnostico_pdf", side_effect=RuntimeError("PDF crash")):
        response = client.post(
            "/v1/reports/diagnostico",
            json={"search_id": VALID_SEARCH_ID},
        )

    assert response.status_code == 500
    assert "pdf" in response.json()["detail"].lower() or "relatório" in response.json()["detail"].lower() or "relatorio" in response.json()["detail"].lower()


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_missing_request_body_returns_422(mock_get_results, client):
    """Missing required search_id field returns 422 Unprocessable Entity."""
    mock_get_results.return_value = dict(SAMPLE_RESULTS)

    response = client.post(
        "/v1/reports/diagnostico",
        json={},  # Missing search_id
    )

    assert response.status_code == 422


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_results_as_dict_parsed_correctly(mock_get_results, client):
    """Results returned as plain dict (from Redis/ARQ) are handled correctly."""
    mock_get_results.return_value = {
        "resumo": {
            "resumo_executivo": "Análise automática.",
            "total_oportunidades": 3,
            "valor_total": 300000.0,
            "destaques": [],
            "recomendacoes": [],
        },
        "licitacoes": _make_licitacoes(3),
        "setor": "facilities",
        "ufs": ["RJ"],
        "total_raw": 50,
        "total_filtrado": 3,
        "date_from": "2026-02-01",
        "date_to": "2026-02-10",
    }

    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": VALID_SEARCH_ID},
    )

    assert response.status_code == 200
    assert response.content[:5] == b"%PDF-"


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_single_bid(mock_get_results, client):
    """PDF generates correctly with exactly one licitacao."""
    results = dict(SAMPLE_RESULTS)
    results["licitacoes"] = _make_licitacoes(1)
    mock_get_results.return_value = results

    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": VALID_SEARCH_ID},
    )

    assert response.status_code == 200
    assert response.content[:5] == b"%PDF-"


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_with_special_chars_in_client_name(mock_get_results, client):
    """Special characters in client_name are sanitized without crashing."""
    mock_get_results.return_value = dict(SAMPLE_RESULTS)

    response = client.post(
        "/v1/reports/diagnostico",
        json={
            "search_id": VALID_SEARCH_ID,
            "client_name": "Empresa & Cia Ltda <ME>",
        },
    )

    assert response.status_code == 200
    assert response.content[:5] == b"%PDF-"


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_with_control_chars_in_bid_objeto(mock_get_results, client):
    """Control characters in bid.objeto are sanitized without crashing."""
    results = dict(SAMPLE_RESULTS)
    results["licitacoes"] = [
        {
            **_make_licitacoes(1)[0],
            "objeto": "Fornecimento\x00de\x0Buniformes",  # control chars
        }
    ]
    mock_get_results.return_value = results

    response = client.post(
        "/v1/reports/diagnostico",
        json={"search_id": VALID_SEARCH_ID},
    )

    assert response.status_code == 200
    assert response.content[:5] == b"%PDF-"


@patch("routes.reports.get_background_results_async", new_callable=AsyncMock)
def test_pdf_ufs_passed_to_assess_batch_when_missing_scores(mock_get_results, client):
    """UFs from results are passed to assess_batch for geography scoring."""
    bids_without_scores = [
        {
            "pncp_id": "BID-001",
            "objeto": "Serviços de TI",
            "orgao": "Órgão Y",
            "uf": "MG",
            "valor": 200000.0,
            "modalidade": "Pregão Eletrônico",
            "data_encerramento": "2026-04-01",
            "dias_restantes": 15,
            "link": "https://pncp.gov.br/bid/1",
        }
    ]

    results = {
        **SAMPLE_RESULTS,
        "licitacoes": bids_without_scores,
        "ufs": ["SP", "MG"],
    }
    mock_get_results.return_value = results

    with patch("routes.reports.assess_batch") as mock_assess:
        response = client.post(
            "/v1/reports/diagnostico",
            json={"search_id": VALID_SEARCH_ID},
        )

    assert response.status_code == 200
    mock_assess.assert_called_once()
    call_kwargs = mock_assess.call_args
    # ufs_busca should be a set derived from results["ufs"]
    ufs_arg = call_kwargs.kwargs.get("ufs_busca") or (call_kwargs.args[1] if len(call_kwargs.args) > 1 else None)
    assert ufs_arg is not None
    assert "SP" in ufs_arg
    assert "MG" in ufs_arg
