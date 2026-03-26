"""HARDEN-013: Background results dict bounded (max 200).

AC1: _MAX_BACKGROUND_RESULTS = 200 applied in store_background_results()
AC2: Eviction of oldest entry when dict exceeds max
AC3: Integrated with periodic cleanup (HARDEN-004) — tested in test_harden004
AC4: Unit tests validate eviction
"""
import time

import pytest

from routes.search import (
    _background_results,
    _MAX_BACKGROUND_RESULTS,
    store_background_results,
)
from schemas import BuscaResponse, ResumoEstrategico


def _make_response(**kwargs) -> BuscaResponse:
    defaults = dict(
        resumo=ResumoEstrategico(
            resumo_executivo="Test summary",
            total_oportunidades=1,
            valor_total=100000.0,
            destaques=["Test"],
        ),
        licitacoes=[],
        total_raw=kwargs.get("total_raw", 0),
        total_filtrado=0,
        excel_available=False,
        quota_used=0,
        quota_remaining=100,
        setor="Tecnologia da Informação",
        termo_busca="test",
        ufs_selecionadas=["SP"],
        search_id=kwargs.get("search_id", "test"),
    )
    defaults.update(kwargs)
    return BuscaResponse(**defaults)


@pytest.fixture(autouse=True)
def _clean_background_results():
    """Clean _background_results between tests."""
    _background_results.clear()
    yield
    _background_results.clear()


class TestHarden013MaxBackgroundResults:
    """AC1: Constant is 200."""

    def test_max_constant_is_200(self):
        assert _MAX_BACKGROUND_RESULTS == 200

    def test_store_within_limit(self):
        """Storing below limit works normally."""
        for i in range(10):
            store_background_results(f"sid-{i}", _make_response(search_id=f"sid-{i}"))
        assert len(_background_results) == 10


class TestHarden013Eviction:
    """AC2: Evicts oldest when exceeding max."""

    def test_evicts_oldest_at_capacity(self):
        """When dict is at max, storing a new entry evicts the oldest."""
        # Fill to capacity
        for i in range(_MAX_BACKGROUND_RESULTS):
            resp = _make_response(search_id=f"fill-{i}")
            store_background_results(f"fill-{i}", resp)
            # Stagger stored_at so we can identify "oldest"
            _background_results[f"fill-{i}"]["stored_at"] = 1000 + i

        assert len(_background_results) == _MAX_BACKGROUND_RESULTS
        assert "fill-0" in _background_results  # oldest

        # Store one more — should evict fill-0 (stored_at=1000, the oldest)
        store_background_results("new-entry", _make_response(search_id="new-entry"))

        assert len(_background_results) == _MAX_BACKGROUND_RESULTS
        assert "fill-0" not in _background_results  # evicted
        assert "new-entry" in _background_results

    def test_no_eviction_when_updating_existing(self):
        """Updating an existing key doesn't trigger eviction."""
        for i in range(_MAX_BACKGROUND_RESULTS):
            store_background_results(f"sid-{i}", _make_response(search_id=f"sid-{i}"))

        # Update existing entry — no eviction needed
        store_background_results("sid-0", _make_response(search_id="sid-0", total_raw=999))
        assert len(_background_results) == _MAX_BACKGROUND_RESULTS
        assert _background_results["sid-0"]["response"].total_raw == 999

    def test_evicts_correct_oldest(self):
        """Eviction targets the entry with smallest stored_at, not insertion order."""
        store_background_results("a", _make_response(search_id="a"))
        _background_results["a"]["stored_at"] = 500  # very old
        store_background_results("b", _make_response(search_id="b"))
        _background_results["b"]["stored_at"] = 100  # oldest
        store_background_results("c", _make_response(search_id="c"))
        _background_results["c"]["stored_at"] = 300

        # Artificially fill to capacity
        for i in range(3, _MAX_BACKGROUND_RESULTS):
            store_background_results(f"pad-{i}", _make_response(search_id=f"pad-{i}"))

        assert len(_background_results) == _MAX_BACKGROUND_RESULTS

        # Add one more — "b" (stored_at=100) should be evicted
        store_background_results("trigger", _make_response(search_id="trigger"))
        assert "b" not in _background_results
        assert "a" in _background_results
        assert "c" in _background_results
        assert "trigger" in _background_results

    def test_multiple_evictions_sequential(self):
        """Multiple sequential stores past capacity each evict one."""
        for i in range(_MAX_BACKGROUND_RESULTS):
            store_background_results(f"s-{i}", _make_response(search_id=f"s-{i}"))
            _background_results[f"s-{i}"]["stored_at"] = 1000 + i

        # Add 3 more — should evict s-0, s-1, s-2
        for j in range(3):
            store_background_results(f"extra-{j}", _make_response(search_id=f"extra-{j}"))

        assert len(_background_results) == _MAX_BACKGROUND_RESULTS
        assert "s-0" not in _background_results
        assert "s-1" not in _background_results
        assert "s-2" not in _background_results
        assert "extra-0" in _background_results
        assert "extra-1" in _background_results
        assert "extra-2" in _background_results


class TestHarden013PeriodicCleanupIntegration:
    """AC3: _cleanup_stale_results is called from periodic cleanup."""

    def test_cleanup_stale_results_removes_expired(self):
        """_cleanup_stale_results removes entries older than TTL."""
        from routes.search import _cleanup_stale_results, _RESULTS_TTL

        store_background_results("fresh", _make_response(search_id="fresh"))
        store_background_results("stale", _make_response(search_id="stale"))
        _background_results["stale"]["stored_at"] = time.time() - _RESULTS_TTL - 100

        _cleanup_stale_results()

        assert "fresh" in _background_results
        assert "stale" not in _background_results
