"""
Performance benchmarks for filter.py module.

Measures:
- Keyword matching performance
- Normalization overhead
- Large dataset filtering throughput

Run with: pytest tests/test_benchmark_filter.py --benchmark-only
Compare runs: pytest-benchmark compare
"""
import pytest
from filter import normalize_text, match_keywords, filter_licitacao, KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO


# ============================================================================
# Fixtures - Sample data
# ============================================================================

@pytest.fixture
def sample_licitacao():
    """Licitação típica para testes de benchmark."""
    return {
        "uf": "SP",
        "valorTotalEstimado": 150_000.0,
        "objetoCompra": "Aquisição de uniformes escolares para rede municipal - inclui camisetas, calças e jalecos",
        "modalidadeNome": "Pregão Eletrônico",
        "situacaoCompra": "Em Andamento",
    }


@pytest.fixture
def large_dataset():
    """Dataset de 1000 licitações para throughput testing."""
    return [
        {
            "uf": "SP" if i % 3 == 0 else "RJ",
            "valorTotalEstimado": 50_000 + (i * 1_000),
            "objetoCompra": f"Aquisição de uniformes escolares variante {i}",
            "modalidadeNome": "Pregão Eletrônico",
            "situacaoCompra": "Em Andamento",
        }
        for i in range(1000)
    ]


# ============================================================================
# Benchmarks - Text Normalization
# ============================================================================

def test_benchmark_normalize_short_text(benchmark):
    """Benchmark: Normalização de texto curto (< 50 chars)."""
    text = "Uniformes Escolares - Camisetas"
    result = benchmark(normalize_text, text)
    assert result == "uniformes escolares camisetas"


def test_benchmark_normalize_long_text(benchmark):
    """Benchmark: Normalização de texto longo (> 200 chars)."""
    text = """
    Aquisição de uniformes escolares completos para rede municipal de ensino,
    incluindo camisetas, calças, shorts, jalecos, aventais, bonés, meias,
    tênis e demais itens de vestuário necessários para estudantes do ensino
    fundamental e médio conforme especificações técnicas anexas ao edital.
    """
    result = benchmark(normalize_text, text)
    assert len(result) > 100


def test_benchmark_normalize_special_chars(benchmark):
    """Benchmark: Normalização com caracteres especiais e acentos."""
    text = "Fardamento/Uniformização p/ Funcionários - Açúcar, Café & Chá"
    result = benchmark(normalize_text, text)
    assert "funcionarios" in result


# ============================================================================
# Benchmarks - Keyword Matching
# ============================================================================

def test_benchmark_match_keywords_found(benchmark):
    """Benchmark: Match de keywords (encontrado)."""
    objeto = "Aquisição de uniformes escolares para rede municipal"
    resultado, matches = benchmark(match_keywords, objeto, KEYWORDS_UNIFORMES)
    assert resultado is True
    assert len(matches) > 0


def test_benchmark_match_keywords_not_found(benchmark):
    """Benchmark: Match de keywords (não encontrado)."""
    objeto = "Aquisição de equipamentos de informática para laboratório"
    resultado, matches = benchmark(match_keywords, objeto, KEYWORDS_UNIFORMES)
    assert resultado is False


def test_benchmark_match_keywords_with_exclusion(benchmark):
    """Benchmark: Match de keywords com exclusão."""
    objeto = "Uniformes de combate militar para batalhão"
    resultado, matches = benchmark(match_keywords, objeto, KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO)
    assert resultado is False  # Should be excluded by military keyword


# ============================================================================
# Benchmarks - Full Filter Pipeline
# ============================================================================

def test_benchmark_full_filter_pipeline_approved(benchmark, sample_licitacao):
    """Benchmark: Pipeline completo de filtros (aprovado)."""
    ufs = {"SP", "RJ"}
    resultado, _ = benchmark(filter_licitacao, sample_licitacao, ufs)
    assert resultado is True


def test_benchmark_full_filter_pipeline_rejected_uf(benchmark, sample_licitacao):
    """Benchmark: Pipeline completo (rejeitado na 1ª etapa - UF)."""
    ufs = {"RS", "SC"}
    resultado, motivo = benchmark(filter_licitacao, sample_licitacao, ufs)
    assert resultado is False
    assert "UF" in motivo


def test_benchmark_full_filter_pipeline_any_valor(benchmark):
    """Benchmark: Pipeline completo (value filter removed 2026-02-05 - all values accepted)."""
    licitacao_cara = {
        "uf": "SP",
        "valorTotalEstimado": 10_000_000.0,
        "objetoCompra": "Uniformes escolares",
    }
    ufs = {"SP"}
    resultado, motivo = benchmark(filter_licitacao, licitacao_cara, ufs)
    # Value filter removed - now accepts any value
    assert resultado is True
    assert motivo is None


def test_benchmark_full_filter_no_value_params(benchmark, sample_licitacao):
    """Benchmark: Pipeline (value filter removed 2026-02-05)."""
    ufs = {"SP"}
    resultado, _ = benchmark(
        filter_licitacao,
        sample_licitacao,
        ufs
    )
    assert resultado is True


# ============================================================================
# Benchmarks - Throughput (Large Datasets)
# ============================================================================

def test_benchmark_throughput_1000_licitacoes(benchmark, large_dataset):
    """Benchmark: Processar 1000 licitações (throughput test)."""
    ufs = {"SP", "RJ"}

    def process_dataset():
        approved = []
        rejected = []
        for licitacao in large_dataset:
            resultado, _ = filter_licitacao(licitacao, ufs)
            if resultado:
                approved.append(licitacao)
            else:
                rejected.append(licitacao)
        return len(approved), len(rejected)

    approved_count, rejected_count = benchmark(process_dataset)
    assert approved_count > 0
    assert rejected_count >= 0
    assert approved_count + rejected_count == 1000


def test_benchmark_keyword_matching_worst_case(benchmark):
    """Benchmark: Keyword matching no pior caso (sem match, todas keywords testadas)."""
    objeto = "Aquisição de equipamentos de informática para laboratório escolar"
    resultado, _ = benchmark(match_keywords, objeto, KEYWORDS_UNIFORMES)
    assert resultado is False


# ============================================================================
# Benchmarks - Edge Cases
# ============================================================================

def test_benchmark_empty_objeto(benchmark):
    """Benchmark: Licitação com objeto vazio (edge case)."""
    licitacao_vazia = {
        "uf": "SP",
        "valorTotalEstimado": 150_000.0,
        "objetoCompra": "",
    }
    ufs = {"SP"}
    resultado, _ = benchmark(filter_licitacao, licitacao_vazia, ufs)
    assert resultado is False


def test_benchmark_very_long_objeto(benchmark):
    """Benchmark: Objeto de compra muito longo (500+ caracteres)."""
    long_text = " ".join(["uniformes"] * 100)  # 1000+ chars
    licitacao_longa = {
        "uf": "SP",
        "valorTotalEstimado": 150_000.0,
        "objetoCompra": long_text,
    }
    ufs = {"SP"}
    resultado, _ = benchmark(filter_licitacao, licitacao_longa, ufs)
    assert resultado is True  # Should match "uniformes" keyword


def test_benchmark_many_ufs(benchmark, sample_licitacao):
    """Benchmark: Filtro com muitas UFs (27 estados)."""
    all_ufs = {
        "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
        "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
        "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
    }
    resultado, _ = benchmark(filter_licitacao, sample_licitacao, all_ufs)
    assert resultado is True


# ============================================================================
# Benchmark Configuration
# ============================================================================

# Configure pytest-benchmark behavior
# Run with: pytest tests/test_benchmark_filter.py --benchmark-only -v
#
# Expected performance (reference):
# - normalize_text (short): < 10 μs
# - normalize_text (long): < 50 μs
# - match_keywords: < 50 μs
# - filter_licitacao (full): < 100 μs
# - throughput (1000 items): < 100 ms
#
# To save baseline: pytest --benchmark-save=baseline
# To compare: pytest --benchmark-compare=baseline
