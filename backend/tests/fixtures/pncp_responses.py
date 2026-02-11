"""
PNCP API Mock Response Fixtures

Provides realistic mock responses for testing PNCP client resilience:
- Success responses (single page, multi-page)
- Error responses (429 rate limit, 500 server error, 502/503/504)
- Edge cases (empty results, malformed JSON, partial data)
- Timeout scenarios

Usage:
    from tests.fixtures.pncp_responses import (
        pncp_success_page_1,
        pncp_rate_limit_response,
        pncp_server_error_response,
    )
"""

from datetime import date, timedelta

# ============================================================================
# Sample Licitacao Items (realistic PNCP data)
# ============================================================================

def _make_licitacao(idx: int, uf: str = "SP", valor: float = 100_000.0) -> dict:
    """Generate a realistic licitacao item."""
    return {
        "codigoCompra": f"PNCP-2026-{uf}-{idx:06d}",
        "objetoCompra": f"Aquisição de uniformes escolares para unidade {idx}",
        "nomeOrgao": f"Prefeitura Municipal {idx}",
        "cnpjOrgao": f"{10000000 + idx:014d}",
        "uf": uf,
        "municipio": f"Cidade {idx}",
        "valorTotalEstimado": valor,
        "modalidadeNome": "Pregão Eletrônico",
        "modalidadeId": 6,
        "dataPublicacaoPncp": (date.today() - timedelta(days=idx % 30)).isoformat(),
        "dataAberturaProposta": (date.today() + timedelta(days=7 + idx % 14)).isoformat(),
        "situacaoCompra": "Aberta" if idx % 3 != 0 else "Encerrada",
        "linkSistemaOrigem": f"https://pncp.gov.br/app/editais/{idx}",
        "codigoUnidadeCompradora": f"UC-{idx:06d}",
    }


# ============================================================================
# Success Responses
# ============================================================================

PNCP_SUCCESS_SINGLE_PAGE = {
    "data": [_make_licitacao(i) for i in range(1, 6)],
    "totalRegistros": 5,
    "totalPaginas": 1,
    "paginaAtual": 1,
    "temProximaPagina": False,
}

PNCP_SUCCESS_PAGE_1_OF_3 = {
    "data": [_make_licitacao(i) for i in range(1, 501)],
    "totalRegistros": 1200,
    "totalPaginas": 3,
    "paginaAtual": 1,
    "temProximaPagina": True,
}

PNCP_SUCCESS_PAGE_2_OF_3 = {
    "data": [_make_licitacao(i) for i in range(501, 1001)],
    "totalRegistros": 1200,
    "totalPaginas": 3,
    "paginaAtual": 2,
    "temProximaPagina": True,
}

PNCP_SUCCESS_PAGE_3_OF_3 = {
    "data": [_make_licitacao(i) for i in range(1001, 1201)],
    "totalRegistros": 1200,
    "totalPaginas": 3,
    "paginaAtual": 3,
    "temProximaPagina": False,
}

PNCP_SUCCESS_EMPTY = {
    "data": [],
    "totalRegistros": 0,
    "totalPaginas": 0,
    "paginaAtual": 1,
    "temProximaPagina": False,
}

PNCP_SUCCESS_MULTI_UF = {
    "SP": [_make_licitacao(i, uf="SP") for i in range(1, 4)],
    "RJ": [_make_licitacao(i, uf="RJ") for i in range(1, 3)],
    "MG": [_make_licitacao(i, uf="MG") for i in range(1, 2)],
}


# ============================================================================
# Error Responses
# ============================================================================

PNCP_RATE_LIMIT_HEADERS = {
    "Retry-After": "5",
    "X-RateLimit-Remaining": "0",
    "X-RateLimit-Reset": "1700000000",
}

PNCP_SERVER_ERROR_500 = {
    "status_code": 500,
    "body": {"message": "Internal Server Error"},
}

PNCP_BAD_GATEWAY_502 = {
    "status_code": 502,
    "body": {"message": "Bad Gateway"},
}

PNCP_SERVICE_UNAVAILABLE_503 = {
    "status_code": 503,
    "body": {"message": "Service Temporarily Unavailable"},
}

PNCP_GATEWAY_TIMEOUT_504 = {
    "status_code": 504,
    "body": {"message": "Gateway Timeout"},
}


# ============================================================================
# Edge Cases
# ============================================================================

PNCP_MALFORMED_JSON = "this is not valid json {{{{"

PNCP_PARTIAL_DATA = {
    "data": [
        {
            "codigoCompra": "PNCP-PARTIAL-001",
            "objetoCompra": "Item sem campos opcionais",
            # Missing: nomeOrgao, uf, municipio, valor, etc.
        },
        _make_licitacao(2),
    ],
    "totalRegistros": 2,
    "totalPaginas": 1,
    "paginaAtual": 1,
    "temProximaPagina": False,
}

PNCP_HUGE_VALUE_ITEMS = {
    "data": [
        _make_licitacao(1, valor=0.01),        # Micro value
        _make_licitacao(2, valor=999_999_999),  # Giant value
        _make_licitacao(3, valor=0),            # Zero value
        _make_licitacao(4, valor=-100),         # Negative value (invalid)
    ],
    "totalRegistros": 4,
    "totalPaginas": 1,
    "paginaAtual": 1,
    "temProximaPagina": False,
}


# ============================================================================
# Pytest Fixtures (importable via conftest)
# ============================================================================

def make_pncp_page(items: list, page: int = 1, total_pages: int = 1, total: int | None = None) -> dict:
    """Helper to create a PNCP-style paginated response."""
    return {
        "data": items,
        "totalRegistros": total or len(items),
        "totalPaginas": total_pages,
        "paginaAtual": page,
        "temProximaPagina": page < total_pages,
    }


def make_rate_limit_sequence(fail_count: int = 2) -> list[dict]:
    """Create a sequence of rate-limit failures followed by success.

    Returns list of (status_code, headers, body) tuples for use with
    httpx mock side_effect patterns.
    """
    failures = [
        {"status_code": 429, "headers": PNCP_RATE_LIMIT_HEADERS, "body": {}}
        for _ in range(fail_count)
    ]
    success = {
        "status_code": 200,
        "headers": {},
        "body": PNCP_SUCCESS_SINGLE_PAGE,
    }
    return failures + [success]


def make_server_error_sequence(error_count: int = 3) -> list[dict]:
    """Create a sequence of server errors followed by success.

    Tests exponential backoff and retry behavior.
    """
    errors = [
        {"status_code": 500, "headers": {}, "body": {"message": "Internal Server Error"}}
        for _ in range(error_count)
    ]
    success = {
        "status_code": 200,
        "headers": {},
        "body": PNCP_SUCCESS_SINGLE_PAGE,
    }
    return errors + [success]
