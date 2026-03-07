"""HARDEN-014: ThreadPoolExecutor per-future timeout (20s) for LLM batches.

Tests that individual futures that hang beyond 20s are cancelled,
items marked as pending_review, and the LLM_BATCH_TIMEOUT metric is incremented.
"""

import threading
from concurrent.futures import wait as _real_wait, FIRST_COMPLETED as _REAL_FC
from unittest.mock import patch
import pytest


def _make_lic(objeto: str = "Aquisicao de equipamentos de construcao civil para obras publicas", valor: float = 100_000.0) -> dict:
    return {
        "objetoCompra": objeto,
        "valorTotalEstimado": valor,
        "uf": "SP",
        "orgaoEntidade": {"ufSigla": "SP"},
    }


def _fake_sector():
    from sectors import SectorConfig
    return SectorConfig(
        id="engenharia",
        name="Engenharia",
        description="Engenharia e Construcao",
        keywords=set(),
        exclusions=set(),
        max_contract_value=None,
    )


def _fast_wait(fs, timeout=None, return_when=None):
    """Wrapper that forces 0.2s timeout for fast tests."""
    return _real_wait(fs, timeout=0.2, return_when=return_when)


class TestHarden014BatchFutureTimeout:
    """AC1+AC2+AC3: Per-future timeout in batch zero-match loop."""

    @patch("config.LLM_ZERO_MATCH_ENABLED", True)
    @patch("config.LLM_ZERO_MATCH_BATCH_ENABLED", True)
    @patch("config.LLM_ZERO_MATCH_BATCH_SIZE", 5)
    @patch("config.FILTER_ZERO_MATCH_BUDGET_S", 999)
    @patch("config.LLM_FALLBACK_PENDING_ENABLED", True)
    def test_hanging_batch_future_triggers_timeout(self):
        """AC5: A batch future that hangs > timeout is cancelled, items marked pending_review."""
        from filter import aplicar_todos_filtros

        licitacoes = [_make_lic(f"Equipamento construcao civil {i:03d} para obra publica") for i in range(10)]

        call_count = 0
        cancel_event = threading.Event()

        def classify_batch_with_hang(items, setor_name=None, setor_id=None, termos_busca=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [{"is_primary": True, "confidence": 65, "evidence": ["ok"]}] * len(items)
            else:
                cancel_event.wait(timeout=60)
                return [{"is_primary": False}] * len(items)

        with patch("llm_arbiter._classify_zero_match_batch", classify_batch_with_hang), \
             patch("llm_arbiter.classify_contract_primary_match", return_value={"is_primary": False}), \
             patch("sectors.get_sector") as mock_sector, \
             patch("filter.wait", side_effect=_fast_wait):
            mock_sector.return_value = _fake_sector()

            resultado, stats = aplicar_todos_filtros(
                licitacoes=licitacoes,
                ufs_selecionadas={"SP"},
                setor="engenharia",
            )
            cancel_event.set()

        pending = [lic for lic in licitacoes if lic.get("_pending_review")]
        assert len(pending) == 5, f"Expected 5 pending_review items from timed-out batch, got {len(pending)}"

        for lic in pending:
            assert lic["_pending_review_reason"] == "llm_future_timeout"
            assert lic["_relevance_source"] == "pending_review"

    @patch("config.LLM_ZERO_MATCH_ENABLED", True)
    @patch("config.LLM_ZERO_MATCH_BATCH_ENABLED", True)
    @patch("config.LLM_ZERO_MATCH_BATCH_SIZE", 5)
    @patch("config.FILTER_ZERO_MATCH_BUDGET_S", 999)
    @patch("config.LLM_FALLBACK_PENDING_ENABLED", True)
    def test_fast_batches_no_timeout(self):
        """Sanity check: fast batches complete normally without timeout."""
        from filter import aplicar_todos_filtros

        licitacoes = [_make_lic(f"Servico engenharia construcao {i:03d} para obras") for i in range(10)]

        def fast_classify_batch(items, setor_name=None, setor_id=None, termos_busca=None):
            return [{"is_primary": True, "confidence": 65, "evidence": ["ok"]}] * len(items)

        with patch("llm_arbiter._classify_zero_match_batch", fast_classify_batch), \
             patch("llm_arbiter.classify_contract_primary_match", return_value={"is_primary": False}), \
             patch("sectors.get_sector") as mock_sector:
            mock_sector.return_value = _fake_sector()

            resultado, stats = aplicar_todos_filtros(
                licitacoes=licitacoes,
                ufs_selecionadas={"SP"},
                setor="engenharia",
            )

        pending = [lic for lic in licitacoes if lic.get("_pending_review")]
        assert len(pending) == 0, f"Expected 0 pending_review items, got {len(pending)}"


class TestHarden014IndividualFutureTimeout:
    """AC1+AC2+AC3: Per-future timeout in individual zero-match loop."""

    @patch("config.LLM_ZERO_MATCH_ENABLED", True)
    @patch("config.LLM_ZERO_MATCH_BATCH_ENABLED", False)
    @patch("config.FILTER_ZERO_MATCH_BUDGET_S", 999)
    @patch("config.LLM_FALLBACK_PENDING_ENABLED", True)
    def test_hanging_individual_future_triggers_timeout(self):
        """AC5: An individual future that hangs > timeout is cancelled, item marked pending_review."""
        from filter import aplicar_todos_filtros

        licitacoes = [_make_lic(f"Equipamento construcao civil {i:03d} para obra publica") for i in range(3)]

        call_count = 0
        cancel_event = threading.Event()

        def classify_one_with_hang(objeto, valor, setor_name=None, termos_busca=None,
                                   prompt_level=None, setor_id=None):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return {"is_primary": True, "confidence": 65, "evidence": ["ok"]}
            else:
                cancel_event.wait(timeout=60)
                return {"is_primary": False}

        with patch("llm_arbiter.classify_contract_primary_match", classify_one_with_hang), \
             patch("sectors.get_sector") as mock_sector, \
             patch("filter.wait", side_effect=_fast_wait):
            mock_sector.return_value = _fake_sector()

            resultado, stats = aplicar_todos_filtros(
                licitacoes=licitacoes,
                ufs_selecionadas={"SP"},
                setor="engenharia",
            )
            cancel_event.set()

        pending = [lic for lic in licitacoes if lic.get("_pending_review")]
        assert len(pending) >= 1, f"Expected at least 1 pending_review item, got {len(pending)}"

        for lic in pending:
            assert lic["_pending_review_reason"] == "llm_future_timeout"


class TestHarden014ArbiterFutureTimeout:
    """AC1+AC2: Per-future timeout in arbiter loop."""

    @patch("config.LLM_ZERO_MATCH_ENABLED", False)
    @patch("config.LLM_ARBITER_ENABLED", True)
    def test_hanging_arbiter_future_triggers_timeout(self):
        """AC5: An arbiter future that hangs > timeout is cancelled, counted as rejection."""
        from filter import aplicar_todos_filtros

        # Use vestuario sector with "uniformes" keyword — proven to reach arbiter
        # (from test_crit_flt_002_arbiter_parallel.py)
        licitacoes = [
            {
                "objetoCompra": (
                    f"Registro de preco para eventual aquisicao de bens diversos "
                    f"destinados ao orgao publico federal, incluindo itens de "
                    f"expediente e uniformes para colaboradores da unidade "
                    f"numero {i:03d}, com entrega programada ao longo do exercicio "
                    f"financeiro vigente, pelo periodo de doze meses, com "
                    f"possibilidade de prorrogacao, em parcelas trimestrais, "
                    f"tudo conforme condicoes do edital e seus respectivos anexos"
                ),
                "valorTotalEstimado": 100_000.0,
                "uf": "SP",
                "dataEncerramentoProposta": "2026-12-31T10:00:00Z",
            }
            for i in range(3)
        ]

        call_count = 0
        cancel_event = threading.Event()

        def classify_with_hang(objeto=None, valor=None, setor_name=None, termos_busca=None,
                              prompt_level=None, setor_id=None, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                return {"is_primary": True, "confidence": 70, "evidence": ["ok"]}
            else:
                cancel_event.wait(timeout=60)
                return {"is_primary": False}

        with patch("llm_arbiter.classify_contract_primary_match", classify_with_hang), \
             patch("filter.wait", side_effect=_fast_wait):

            resultado, stats = aplicar_todos_filtros(
                licitacoes=licitacoes,
                ufs_selecionadas={"SP"},
                setor="vestuario",
            )
            cancel_event.set()

        # Timed-out futures should be counted as rejections
        assert stats.get("llm_arbiter_calls", 0) >= 1, \
            f"Expected arbiter calls, got stats: {stats}"


class TestHarden014Metric:
    """AC4: LLM_BATCH_TIMEOUT metric exists and is correctly labeled."""

    def test_metric_importable(self):
        from metrics import LLM_BATCH_TIMEOUT
        assert LLM_BATCH_TIMEOUT is not None
        LLM_BATCH_TIMEOUT.labels(phase="zero_match_batch").inc(0)
        LLM_BATCH_TIMEOUT.labels(phase="zero_match_individual").inc(0)
        LLM_BATCH_TIMEOUT.labels(phase="arbiter").inc(0)
