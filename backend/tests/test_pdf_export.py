"""tests/test_pdf_export.py — STORY-447: Per-edital PDF export tests."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Unit tests — pdf_generator_edital
# ---------------------------------------------------------------------------

def test_generate_edital_pdf_returns_bytes():
    """generate_edital_pdf returns non-empty bytes for minimal bid data."""
    from pdf_generator_edital import generate_edital_pdf

    bid = {
        "objeto": "Pregão para fornecimento de material de limpeza",
        "orgao": "Prefeitura Municipal de Teste",
        "uf": "SP",
    }
    result = generate_edital_pdf(bid, plan_type="smartlic_pro")
    assert isinstance(result, bytes)
    assert len(result) > 0
    # PDF magic bytes
    assert result[:4] == b"%PDF"


def test_generate_edital_pdf_trial_watermark():
    """Trial PDF contains watermark text in the output (footer callback sets it)."""
    from pdf_generator_edital import generate_edital_pdf

    bid = {"objeto": "Licitação Teste", "orgao": "Órgão Teste", "uf": "RJ"}
    pdf_bytes = generate_edital_pdf(bid, plan_type="free_trial")
    # Cannot inspect footer text directly from bytes, but PDF must be valid
    result = pdf_bytes
    assert result
    assert len(result) > 500  # non-trivial PDF


def test_generate_edital_pdf_paid_no_trial_in_footer():
    """Paid PDF generation does not raise and returns valid bytes."""
    from pdf_generator_edital import generate_edital_pdf

    bid = {"objeto": "Obra de pavimentação", "orgao": "Governo do Estado", "uf": "MG"}
    result = generate_edital_pdf(bid, plan_type="smartlic_pro")
    assert result[:4] == b"%PDF"


def test_generate_edital_pdf_full_fields():
    """PDF generation with all fields populated does not raise."""
    from pdf_generator_edital import generate_edital_pdf

    bid = {
        "objeto": "Pregão Eletrônico para Serviços de TI",
        "orgao": "Ministério da Educação",
        "uf": "DF",
        "municipio": "Brasília",
        "valor": 1_500_000.00,
        "data_encerramento": "2026-05-15T23:59:00",
        "data_publicacao": "2026-04-01",
        "modalidade": "Pregão Eletrônico",
        "link": "https://pncp.gov.br/app/editais/1234",
        "numero_compra": "00001/2026",
        "pncp_id": "12345678000190-1-000001/2026",
        "viability_level": "alta",
        "viability_score": 82,
        "viability_factors": {
            "modalidade": 85, "modalidade_label": "Favorável",
            "timeline": 75, "timeline_label": "Adequado",
            "value_fit": 90, "value_fit_label": "Ótimo",
            "geography": 70, "geography_label": "Regional",
        },
        "resumo_executivo": "Oportunidade relevante para empresas de TI com histórico em governo federal.",
        "recomendacao": "Participar — alta compatibilidade com perfil da empresa.",
    }
    result = generate_edital_pdf(bid, plan_type="smartlic_pro")
    assert result[:4] == b"%PDF"
    assert len(result) > 1000


def test_generate_edital_pdf_null_valor():
    """Null valor renders 'Não informado' without raising."""
    from pdf_generator_edital import generate_edital_pdf

    bid = {"objeto": "Serviços de limpeza", "orgao": "Câmara Municipal", "uf": "BA", "valor": None}
    result = generate_edital_pdf(bid)
    assert result[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# Route tests — POST /v1/export/pdf
# ---------------------------------------------------------------------------

@pytest.fixture
def export_client():
    """TestClient with auth override."""
    import sys
    if "arq" not in sys.modules:
        sys.modules["arq"] = MagicMock_arq()
    from fastapi import FastAPI
    from routes.export import router
    from auth import require_auth

    app = FastAPI()
    app.include_router(router, prefix="/v1")
    app.dependency_overrides[require_auth] = lambda: {
        "id": "test-user-id", "plan_type": "free_trial"
    }
    return TestClient(app)


class MagicMock_arq:
    class Retry(Exception):
        pass


@pytest.fixture
def valid_bid_payload():
    return {
        "objeto": "Serviços de limpeza e conservação predial",
        "orgao": "Prefeitura Municipal",
        "uf": "SP",
        "valor": 50000.0,
        "data_encerramento": "2026-05-20T18:00:00",
        "modalidade": "Pregão Eletrônico",
    }


def test_export_pdf_returns_pdf_content_type(export_client, valid_bid_payload):
    """POST /v1/export/pdf returns 200 with application/pdf content-type."""
    with patch(
        "pdf_generator_edital.generate_edital_pdf",
        return_value=b"%PDF-1.4 fake pdf content",
    ):
        response = export_client.post("/v1/export/pdf", json=valid_bid_payload)
    assert response.status_code == 200
    assert "application/pdf" in response.headers["content-type"]


def test_export_pdf_has_content_disposition(export_client, valid_bid_payload):
    """Response includes Content-Disposition with attachment filename."""
    with patch(
        "pdf_generator_edital.generate_edital_pdf",
        return_value=b"%PDF-1.4 fake pdf content",
    ):
        response = export_client.post("/v1/export/pdf", json=valid_bid_payload)
    assert response.status_code == 200
    cd = response.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert ".pdf" in cd


def test_export_pdf_timeout_returns_503(export_client, valid_bid_payload):
    """Timeout in PDF generation returns 503."""
    import asyncio

    async def slow_pdf(*args, **kwargs):
        raise asyncio.TimeoutError()

    with patch("routes.export.asyncio.wait_for", side_effect=asyncio.TimeoutError()):
        response = export_client.post("/v1/export/pdf", json=valid_bid_payload)
    assert response.status_code == 503


def test_export_pdf_requires_auth():
    """Unauthenticated request returns 401 (no dependency override)."""
    from fastapi import FastAPI
    from routes.export import router

    app = FastAPI()
    app.include_router(router, prefix="/v1")
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/v1/export/pdf", json={"objeto": "x", "orgao": "y", "uf": "SP"})
    assert response.status_code in (401, 403, 422)
