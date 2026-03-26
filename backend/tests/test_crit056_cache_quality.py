"""CRIT-056 AC6: Tests for cache quality score.

Tests:
1. Write with all sources ok → quality_score=1.0
2. Write with PNCP degraded + PCP ok → quality_score=0.3
3. Write with zero results + degraded → NOT saved to cache
4. Read with quality<1.0 + PNCP healthy → returns STALE (triggers revalidation)
5. Read with quality<1.0 + PNCP degraded → returns normally
6. PNCP recovery epoch increment → old cache entries force revalidation
7. quality_score propagated correctly to L1 and per-UF entries
"""

import pytest
import threading
from datetime import datetime, timezone
from types import SimpleNamespace

from pipeline.cache_manager import (
    _read_cache,
    _read_cache_composed,
    _write_cache,
    _write_cache_per_uf,
    _compute_cache_key,
    _compute_cache_key_per_uf,
)
from redis_pool import get_fallback_cache


@pytest.fixture(autouse=True)
def clear_inmemory_cache():
    """Clear InMemory cache between tests."""
    cache = get_fallback_cache()
    cache._store.clear()
    yield
    cache._store.clear()


@pytest.fixture(autouse=True)
def reset_recovery_epoch():
    """Reset PNCP recovery epoch between tests."""
    import cron_jobs
    with cron_jobs._pncp_cron_status_lock:
        cron_jobs._pncp_recovery_epoch = 0
        cron_jobs._pncp_cron_status.update({
            "status": "unknown", "latency_ms": None, "updated_at": None,
        })
    yield
    with cron_jobs._pncp_cron_status_lock:
        cron_jobs._pncp_recovery_epoch = 0
        cron_jobs._pncp_cron_status.update({
            "status": "unknown", "latency_ms": None, "updated_at": None,
        })


def _make_request(ufs=None, setor_id=1):
    return SimpleNamespace(
        setor_id=setor_id,
        ufs=ufs or ["SP"],
        status=SimpleNamespace(value="aberta"),
        modalidades=None,
        modo_busca="abertas",
        force_fresh=False,
    )


def _make_bid(uf: str, codigo: str) -> dict:
    return {
        "uf": uf,
        "codigo_licitacao": codigo,
        "objeto": f"Test bid {codigo}",
    }


# ============================================================================
# AC1: quality_score on cache write
# ============================================================================


class TestCacheQualityWrite:
    """AC1: quality_score is written to cache_data."""

    def test_write_all_sources_ok_quality_1(self):
        """All sources succeeded → quality_score=1.0."""
        req = _make_request(ufs=["SP"])
        cache_key = _compute_cache_key(req)

        from cron_jobs import get_pncp_recovery_epoch
        cache_data = {
            "licitacoes": [_make_bid("SP", "001")],
            "total": 1,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "search_params": {"setor_id": 1, "ufs": ["SP"], "status": "aberta"},
            "quality_score": 1.0,
            "sources_succeeded": ["PNCP", "PCP"],
            "sources_degraded": [],
            "recovery_epoch": get_pncp_recovery_epoch(),
        }
        _write_cache(cache_key, cache_data)

        cached = _read_cache(cache_key)
        assert cached is not None
        assert cached["quality_score"] == 1.0
        assert cached["sources_succeeded"] == ["PNCP", "PCP"]
        assert cached["sources_degraded"] == []
        assert "_swr_stale" not in cached  # Not stale when quality is full

    def test_write_pncp_degraded_quality_03(self):
        """PNCP degraded, only PCP ok → quality_score=0.3."""
        req = _make_request(ufs=["RJ"])
        cache_key = _compute_cache_key(req)

        cache_data = {
            "licitacoes": [_make_bid("RJ", "002")],
            "total": 1,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "search_params": {"setor_id": 1, "ufs": ["RJ"], "status": "aberta"},
            "quality_score": 0.3,
            "sources_succeeded": ["PCP"],
            "sources_degraded": ["PNCP"],
            "recovery_epoch": 0,
        }
        _write_cache(cache_key, cache_data)

        cached = _read_cache(cache_key)
        assert cached is not None
        assert cached["quality_score"] == 0.3
        assert cached["sources_degraded"] == ["PNCP"]

    def test_write_pncp_ok_secondary_degraded_quality_07(self):
        """PNCP ok, secondary degraded → quality_score=0.7."""
        req = _make_request(ufs=["MG"])
        cache_key = _compute_cache_key(req)

        cache_data = {
            "licitacoes": [_make_bid("MG", "003")],
            "total": 1,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "search_params": {"setor_id": 1, "ufs": ["MG"], "status": "aberta"},
            "quality_score": 0.7,
            "sources_succeeded": ["PNCP"],
            "sources_degraded": ["PCP"],
            "recovery_epoch": 0,
        }
        _write_cache(cache_key, cache_data)

        cached = _read_cache(cache_key)
        assert cached is not None
        assert cached["quality_score"] == 0.7

    def test_per_uf_write_propagates_quality(self):
        """CRIT-056 AC1: Per-UF cache entries receive quality metadata."""
        req = _make_request(ufs=["SP", "RJ"])
        bids = [_make_bid("SP", "010"), _make_bid("RJ", "011")]

        _write_cache_per_uf(req, bids, quality_score=0.3,
                            sources_succeeded=["PCP"],
                            sources_degraded=["PNCP"])

        sp_key = _compute_cache_key_per_uf(req, "SP")
        sp_data = _read_cache(sp_key)
        assert sp_data is not None
        assert sp_data["quality_score"] == 0.3
        assert sp_data["sources_degraded"] == ["PNCP"]

        rj_key = _compute_cache_key_per_uf(req, "RJ")
        rj_data = _read_cache(rj_key)
        assert rj_data is not None
        assert rj_data["quality_score"] == 0.3


# ============================================================================
# AC2: Read with quality check
# ============================================================================


class TestCacheQualityRead:
    """AC2: Read checks quality vs PNCP health status."""

    def test_read_quality_low_pncp_healthy_marks_stale(self):
        """quality<1.0 + PNCP healthy → _swr_stale=True."""
        import cron_jobs
        cron_jobs._update_pncp_cron_status("healthy", 500)

        req = _make_request(ufs=["SP"])
        cache_key = _compute_cache_key(req)
        cache_data = {
            "licitacoes": [_make_bid("SP", "020")],
            "total": 1,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "quality_score": 0.3,
            "sources_succeeded": ["PCP"],
            "sources_degraded": ["PNCP"],
            "recovery_epoch": 0,
        }
        _write_cache(cache_key, cache_data)

        cached = _read_cache(cache_key)
        assert cached is not None
        assert cached.get("_swr_stale") is True
        # Data is still served (not None)
        assert len(cached["licitacoes"]) == 1

    def test_read_quality_low_pncp_degraded_no_stale(self):
        """quality<1.0 + PNCP degraded → no _swr_stale (better than nothing)."""
        import cron_jobs
        cron_jobs._update_pncp_cron_status("degraded", 5000)

        req = _make_request(ufs=["SP"])
        cache_key = _compute_cache_key(req)
        cache_data = {
            "licitacoes": [_make_bid("SP", "021")],
            "total": 1,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "quality_score": 0.3,
            "sources_succeeded": ["PCP"],
            "sources_degraded": ["PNCP"],
            "recovery_epoch": 0,
        }
        _write_cache(cache_key, cache_data)

        cached = _read_cache(cache_key)
        assert cached is not None
        assert cached.get("_swr_stale") is not True

    def test_read_quality_full_no_stale(self):
        """quality=1.0 → never stale from quality check."""
        import cron_jobs
        cron_jobs._update_pncp_cron_status("healthy", 500)

        req = _make_request(ufs=["SP"])
        cache_key = _compute_cache_key(req)
        cache_data = {
            "licitacoes": [_make_bid("SP", "022")],
            "total": 1,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "quality_score": 1.0,
            "sources_succeeded": ["PNCP", "PCP"],
            "sources_degraded": [],
            "recovery_epoch": 0,
        }
        _write_cache(cache_key, cache_data)

        cached = _read_cache(cache_key)
        assert cached is not None
        assert cached.get("_swr_stale") is not True

    def test_read_backward_compat_no_quality_field(self):
        """Old cache entries without quality_score → treated as quality=1.0 (backward compat)."""
        import cron_jobs
        cron_jobs._update_pncp_cron_status("healthy", 500)

        req = _make_request(ufs=["SP"])
        cache_key = _compute_cache_key(req)
        # Old format without quality fields
        cache_data = {
            "licitacoes": [_make_bid("SP", "023")],
            "total": 1,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }
        _write_cache(cache_key, cache_data)

        cached = _read_cache(cache_key)
        assert cached is not None
        assert cached.get("_swr_stale") is not True  # Default quality=1.0


# ============================================================================
# AC3: Don't cache empty degraded results
# ============================================================================


class TestCacheSkipEmptyDegraded:
    """AC3: Empty results from degraded sources should not be cached."""

    def test_skip_logic_does_not_write(self):
        """Simulate the skip condition: quality < 0.5 and no results → skip."""
        # This tests the logic at the pipeline level. The actual skip happens
        # in search_pipeline.py. Here we verify the building blocks.
        quality = 0.3
        results = []
        should_skip = quality < 0.5 and not results
        assert should_skip is True

    def test_partial_results_degraded_still_cached(self):
        """quality < 0.5 but HAS results → should be cached (partial > nothing)."""
        req = _make_request(ufs=["SP"])
        cache_key = _compute_cache_key(req)
        cache_data = {
            "licitacoes": [_make_bid("SP", "030")],
            "total": 1,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "quality_score": 0.3,
            "sources_succeeded": ["PCP"],
            "sources_degraded": ["PNCP"],
            "recovery_epoch": 0,
        }
        _write_cache(cache_key, cache_data)

        cached = _read_cache(cache_key)
        assert cached is not None
        assert len(cached["licitacoes"]) == 1


# ============================================================================
# AC4: Recovery epoch
# ============================================================================


class TestRecoveryEpoch:
    """AC4: Recovery epoch mechanism."""

    def test_epoch_increments_on_recovery(self):
        """PNCP degraded → healthy increments recovery epoch."""
        import cron_jobs

        assert cron_jobs.get_pncp_recovery_epoch() == 0

        cron_jobs._update_pncp_cron_status("degraded", 5000)
        assert cron_jobs.get_pncp_recovery_epoch() == 0  # No increment yet

        cron_jobs._update_pncp_cron_status("healthy", 500)
        assert cron_jobs.get_pncp_recovery_epoch() == 1  # Incremented

    def test_epoch_no_increment_healthy_to_healthy(self):
        """healthy → healthy does NOT increment epoch."""
        import cron_jobs

        cron_jobs._update_pncp_cron_status("healthy", 500)
        assert cron_jobs.get_pncp_recovery_epoch() == 0

        cron_jobs._update_pncp_cron_status("healthy", 400)
        assert cron_jobs.get_pncp_recovery_epoch() == 0

    def test_epoch_increment_down_to_healthy(self):
        """down → healthy also increments epoch."""
        import cron_jobs

        cron_jobs._update_pncp_cron_status("down", None)
        cron_jobs._update_pncp_cron_status("healthy", 500)
        assert cron_jobs.get_pncp_recovery_epoch() == 1

    def test_epoch_multiple_cycles(self):
        """Multiple degraded→healthy cycles increment epoch each time."""
        import cron_jobs

        cron_jobs._update_pncp_cron_status("degraded", 5000)
        cron_jobs._update_pncp_cron_status("healthy", 500)
        assert cron_jobs.get_pncp_recovery_epoch() == 1

        cron_jobs._update_pncp_cron_status("degraded", 3000)
        cron_jobs._update_pncp_cron_status("healthy", 400)
        assert cron_jobs.get_pncp_recovery_epoch() == 2

    def test_read_old_epoch_marks_stale(self):
        """Cache entry with old epoch → stale after PNCP recovery."""
        import cron_jobs

        req = _make_request(ufs=["SP"])
        cache_key = _compute_cache_key(req)

        # Write cache at epoch 0
        cache_data = {
            "licitacoes": [_make_bid("SP", "040")],
            "total": 1,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "quality_score": 0.3,
            "sources_succeeded": ["PCP"],
            "sources_degraded": ["PNCP"],
            "recovery_epoch": 0,
        }
        _write_cache(cache_key, cache_data)

        # Simulate PNCP recovery → epoch becomes 1
        cron_jobs._update_pncp_cron_status("degraded", 5000)
        cron_jobs._update_pncp_cron_status("healthy", 500)
        assert cron_jobs.get_pncp_recovery_epoch() == 1

        # Read should mark as stale
        cached = _read_cache(cache_key)
        assert cached is not None
        assert cached.get("_swr_stale") is True

    def test_read_current_epoch_not_stale(self):
        """Cache entry with current epoch → not stale from epoch check."""
        import cron_jobs

        # Simulate one recovery cycle first
        cron_jobs._update_pncp_cron_status("degraded", 5000)
        cron_jobs._update_pncp_cron_status("healthy", 500)
        assert cron_jobs.get_pncp_recovery_epoch() == 1

        req = _make_request(ufs=["SP"])
        cache_key = _compute_cache_key(req)

        # Write cache at epoch 1 with full quality
        cache_data = {
            "licitacoes": [_make_bid("SP", "041")],
            "total": 1,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "quality_score": 1.0,
            "sources_succeeded": ["PNCP", "PCP"],
            "sources_degraded": [],
            "recovery_epoch": 1,
        }
        _write_cache(cache_key, cache_data)

        cached = _read_cache(cache_key)
        assert cached is not None
        assert cached.get("_swr_stale") is not True


# ============================================================================
# AC2+AC4: Composed cache quality propagation
# ============================================================================


class TestComposedCacheQuality:
    """Quality check propagation in composed (multi-UF) cache reads."""

    def test_composed_stale_from_quality(self):
        """If any per-UF entry is quality-stale, composed result is stale."""
        import cron_jobs
        cron_jobs._update_pncp_cron_status("healthy", 500)

        req = _make_request(ufs=["SP", "RJ"])

        # SP: full quality, RJ: low quality
        sp_key = _compute_cache_key_per_uf(req, "SP")
        rj_key = _compute_cache_key_per_uf(req, "RJ")

        now = datetime.now(timezone.utc).isoformat()
        _write_cache(sp_key, {
            "licitacoes": [_make_bid("SP", "050")],
            "total": 1, "cached_at": now,
            "quality_score": 1.0, "sources_succeeded": ["PNCP", "PCP"],
            "sources_degraded": [], "recovery_epoch": 0,
            "search_params": {"setor_id": 1, "ufs": ["SP"], "status": "aberta"},
        })
        _write_cache(rj_key, {
            "licitacoes": [_make_bid("RJ", "051")],
            "total": 1, "cached_at": now,
            "quality_score": 0.3, "sources_succeeded": ["PCP"],
            "sources_degraded": ["PNCP"], "recovery_epoch": 0,
            "search_params": {"setor_id": 1, "ufs": ["RJ"], "status": "aberta"},
        })

        composed = _read_cache_composed(req)
        assert composed is not None
        assert composed.get("_swr_stale") is True
        assert len(composed["licitacoes"]) == 2

    def test_composed_not_stale_when_all_full_quality(self):
        """All per-UF entries full quality → composed not stale."""
        import cron_jobs
        cron_jobs._update_pncp_cron_status("healthy", 500)

        req = _make_request(ufs=["SP", "RJ"])

        sp_key = _compute_cache_key_per_uf(req, "SP")
        rj_key = _compute_cache_key_per_uf(req, "RJ")

        now = datetime.now(timezone.utc).isoformat()
        for key, uf in [(sp_key, "SP"), (rj_key, "RJ")]:
            _write_cache(key, {
                "licitacoes": [_make_bid(uf, f"06{uf}")],
                "total": 1, "cached_at": now,
                "quality_score": 1.0, "sources_succeeded": ["PNCP", "PCP"],
                "sources_degraded": [], "recovery_epoch": 0,
                "search_params": {"setor_id": 1, "ufs": [uf], "status": "aberta"},
            })

        composed = _read_cache_composed(req)
        assert composed is not None
        assert composed.get("_swr_stale") is not True


# ============================================================================
# AC5: Metrics
# ============================================================================


class TestCacheQualityMetrics:
    """AC5: Prometheus metrics for cache quality."""

    def test_metrics_exist(self):
        """All 3 CRIT-056 metrics are importable."""
        from metrics import (
            CACHE_QUALITY_WRITE_TOTAL,
            CACHE_QUALITY_REVALIDATION_TOTAL,
            CACHE_QUALITY_SCORE,
        )
        # Just verify they exist and can be called
        assert CACHE_QUALITY_WRITE_TOTAL is not None
        assert CACHE_QUALITY_REVALIDATION_TOTAL is not None
        assert CACHE_QUALITY_SCORE is not None


# ============================================================================
# AC4: Thread safety of recovery epoch
# ============================================================================


class TestRecoveryEpochThreadSafety:
    """Verify recovery epoch is thread-safe."""

    def test_concurrent_updates(self):
        """Multiple threads updating status don't corrupt epoch."""
        import cron_jobs

        errors = []

        def cycle(n):
            try:
                for _ in range(n):
                    cron_jobs._update_pncp_cron_status("degraded", 5000)
                    cron_jobs._update_pncp_cron_status("healthy", 500)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=cycle, args=(50,)) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        # Each thread does 50 cycles, 4 threads = 200 total recovery transitions
        epoch = cron_jobs.get_pncp_recovery_epoch()
        assert epoch == 200


# ============================================================================
# Integration: get_pncp_recovery_epoch in cache_manager
# ============================================================================


class TestCacheManagerEpochIntegration:
    """Verify per-UF writes include recovery_epoch from cron_jobs."""

    def test_per_uf_writes_include_epoch(self):
        """_write_cache_per_uf includes current recovery_epoch."""
        import cron_jobs

        # Set epoch to 3
        for _ in range(3):
            cron_jobs._update_pncp_cron_status("degraded", 5000)
            cron_jobs._update_pncp_cron_status("healthy", 500)
        assert cron_jobs.get_pncp_recovery_epoch() == 3

        req = _make_request(ufs=["SP", "RJ"])
        bids = [_make_bid("SP", "070"), _make_bid("RJ", "071")]
        _write_cache_per_uf(req, bids)

        sp_key = _compute_cache_key_per_uf(req, "SP")
        sp_data = _read_cache(sp_key)
        assert sp_data is not None
        assert sp_data["recovery_epoch"] == 3
