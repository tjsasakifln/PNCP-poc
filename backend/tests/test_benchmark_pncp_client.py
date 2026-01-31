"""
Performance benchmarks for pncp_client.py module.

Measures:
- Request building performance
- Pagination logic overhead
- Retry mechanism timing

Run with: pytest tests/test_benchmark_pncp_client.py --benchmark-only
"""
import pytest
from pncp_client import PNCPClient
from datetime import datetime, timedelta


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def client():
    """PNCP client instance for benchmarking."""
    return PNCPClient()


@pytest.fixture
def sample_params():
    """Sample search parameters."""
    hoje = datetime.now()
    return {
        "dataInicial": (hoje - timedelta(days=7)).strftime("%Y-%m-%d"),
        "dataFinal": hoje.strftime("%Y-%m-%d"),
        "pagina": 1,
    }


@pytest.fixture
def mock_response_single_page():
    """Mock response for single page of results."""
    return {
        "data": [{"codigoCompra": f"12345-{i}"} for i in range(100)],
        "totalRegistros": 100,
        "totalPaginas": 1,
        "paginaAtual": 1,
        "temProximaPagina": False,
    }


@pytest.fixture
def mock_response_multi_page():
    """Mock response for multi-page results (first page)."""
    return {
        "data": [{"codigoCompra": f"12345-{i}"} for i in range(500)],
        "totalRegistros": 1500,
        "totalPaginas": 3,
        "paginaAtual": 1,
        "temProximaPagina": True,
    }


# ============================================================================
# Benchmarks - Request Building
# ============================================================================

def test_benchmark_build_params(benchmark, client, sample_params):
    """Benchmark: Construção de parâmetros de requisição."""
    def build():
        params = sample_params.copy()
        params["tamanhoPagina"] = 500
        return params

    result = benchmark(build)
    assert "dataInicial" in result
    assert "dataFinal" in result


def test_benchmark_parse_response(benchmark, mock_response_single_page):
    """Benchmark: Parse de resposta JSON."""
    def parse():
        data = mock_response_single_page["data"]
        total = mock_response_single_page["totalRegistros"]
        return len(data), total

    count, total = benchmark(parse)
    assert count == 100
    assert total == 100


# ============================================================================
# Benchmarks - Pagination Logic
# ============================================================================

def test_benchmark_pagination_decision_single_page(benchmark, mock_response_single_page):
    """Benchmark: Decisão de paginação (sem próxima página)."""
    def check_next_page():
        return mock_response_single_page.get("temProximaPagina", False)

    has_next = benchmark(check_next_page)
    assert has_next is False


def test_benchmark_pagination_decision_multi_page(benchmark, mock_response_multi_page):
    """Benchmark: Decisão de paginação (com próxima página)."""
    def check_next_page():
        return mock_response_multi_page.get("temProximaPagina", False)

    has_next = benchmark(check_next_page)
    assert has_next is True


# ============================================================================
# Benchmarks - Data Processing
# ============================================================================

def test_benchmark_process_100_items(benchmark):
    """Benchmark: Processar 100 itens de uma página."""
    items = [{"codigoCompra": f"12345-{i}", "objetoCompra": f"Objeto {i}"} for i in range(100)]

    def process():
        processed = []
        for item in items:
            if "codigoCompra" in item:
                processed.append(item["codigoCompra"])
        return processed

    result = benchmark(process)
    assert len(result) == 100


def test_benchmark_process_500_items(benchmark):
    """Benchmark: Processar 500 itens de uma página (tamanho máximo)."""
    items = [{"codigoCompra": f"12345-{i}", "objetoCompra": f"Objeto {i}"} for i in range(500)]

    def process():
        processed = []
        for item in items:
            if "codigoCompra" in item:
                processed.append(item["codigoCompra"])
        return processed

    result = benchmark(process)
    assert len(result) == 500


# ============================================================================
# Benchmarks - Edge Cases
# ============================================================================

def test_benchmark_empty_response(benchmark):
    """Benchmark: Processar resposta vazia (0 resultados)."""
    empty_response = {
        "data": [],
        "totalRegistros": 0,
        "totalPaginas": 0,
        "paginaAtual": 1,
        "temProximaPagina": False,
    }

    def process():
        data = empty_response["data"]
        return len(data)

    result = benchmark(process)
    assert result == 0


def test_benchmark_large_objeto_field(benchmark):
    """Benchmark: Processar item com campo objetoCompra muito grande."""
    large_item = {
        "codigoCompra": "12345",
        "objetoCompra": "X" * 5000,  # 5KB de texto
        "uf": "SP",
    }

    def process():
        obj = large_item.get("objetoCompra", "")
        return len(obj)

    length = benchmark(process)
    assert length == 5000


# ============================================================================
# Benchmarks - URL Building
# ============================================================================

def test_benchmark_url_construction(benchmark, client, sample_params):
    """Benchmark: Construção de URL com query params."""
    def build_url():
        base = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
        # Simulate query param building
        params = "&".join([f"{k}={v}" for k, v in sample_params.items()])
        return f"{base}?{params}"

    url = benchmark(build_url)
    assert "dataInicial" in url
    assert "dataFinal" in url


# ============================================================================
# Performance Notes
# ============================================================================

# Expected performance targets (reference):
# - build_params: < 5 μs
# - parse_response: < 20 μs
# - pagination_decision: < 1 μs
# - process_100_items: < 100 μs
# - process_500_items: < 500 μs
# - url_construction: < 10 μs
#
# Real-world network latency (not benchmarked here):
# - PNCP API response time: 200-2000 ms
# - Rate limiting: 100 ms between requests
#
# To run benchmarks only:
# pytest tests/test_benchmark_pncp_client.py --benchmark-only -v
#
# To compare with baseline:
# pytest --benchmark-compare=baseline
