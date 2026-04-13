"""CRIT-081 AC13: Tests for expired cache served when all sources are down.

Verifies that:
- Com SERVE_EXPIRED_CACHE_ON_TOTAL_OUTAGE=True + todas as fontes down:
  serve cache > 24h TTL com is_stale_fallback=True
- Com flag False: NÃO serve cache expirado
- Com fontes disponíveis: NÃO ativa fallback de expirado
- _all_sources_down() retorna True apenas quando os 3 CBs estão degradados
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_stale_result():
    """Helper: resultado de cache expirado (como retornado por cascade)."""
    return {
        "results": [{"id": "1", "titulo": "Licitação antiga"}],
        "total": 1,
        "cached_at": "2026-01-01T00:00:00Z",
        "cache_level": "supabase",
        "cache_age_hours": 30.0,
    }


# ===========================================================================
# AC13-1: _all_sources_down() — todos CBs degradados → True
# ===========================================================================

def test_all_sources_down_when_all_cbs_degraded():
    """AC13: _all_sources_down() retorna True quando os 3 CBs estão degradados."""
    mock_cb = MagicMock()
    mock_cb.is_degraded = True

    with patch("pncp_client.get_circuit_breaker", return_value=mock_cb):
        from cache.cascade import _all_sources_down
        assert _all_sources_down() is True


def test_all_sources_down_false_when_pncp_up():
    """AC13: _all_sources_down() retorna False quando PNCP está disponível."""
    mock_cb_up = MagicMock()
    mock_cb_up.is_degraded = False
    mock_cb_down = MagicMock()
    mock_cb_down.is_degraded = True

    def get_cb(name):
        if name == "pncp":
            return mock_cb_up
        return mock_cb_down

    with patch("pncp_client.get_circuit_breaker", side_effect=get_cb):
        from cache.cascade import _all_sources_down
        assert _all_sources_down() is False


def test_all_sources_down_returns_false_on_exception():
    """AC13: _all_sources_down() retorna False em caso de exceção (seguro)."""
    with patch("pncp_client.get_circuit_breaker", side_effect=Exception("CB unavailable")):
        from cache.cascade import _all_sources_down
        assert _all_sources_down() is False


# ===========================================================================
# AC13-2: Flag True + fontes down → serve cache expirado com is_stale_fallback
# ===========================================================================

@pytest.mark.asyncio
async def test_get_cascade_serves_expired_when_all_sources_down():
    """AC13: Com flag=True e fontes down, serve cache expirado com is_stale_fallback=True."""
    stale_result = _make_stale_result()
    call_count = [0]

    async def mock_cascade_read(user_id, params_hash, params, hit_fn):
        call_count[0] += 1
        if call_count[0] == 1:
            return None  # Primeira chamada: miss normal (sem expired)
        return stale_result  # Segunda chamada: hit com allow_expired=True

    with (
        patch("config.SERVE_EXPIRED_CACHE_ON_TOTAL_OUTAGE", True),
        patch("config.CACHE_LEGACY_KEY_FALLBACK", False),
        patch("cache.cascade._all_sources_down", return_value=True),
        patch("cache.cascade._cascade_read_levels", side_effect=mock_cascade_read),
        patch("metrics.CACHE_HITS") as mock_hits,
        patch("metrics.CACHE_MISSES") as mock_misses,
    ):
        mock_hits.labels.return_value = MagicMock()
        mock_misses.labels.return_value = MagicMock()
        from cache.cascade import get_from_cache_cascade
        result = await get_from_cache_cascade(
            user_id="user-123",
            params={"setor_id": "vestuario", "ufs": ["SP"]},
        )

    assert result is not None
    assert result.get("is_stale_fallback") is True
    assert call_count[0] == 2  # Duas chamadas: normal + allow_expired


# ===========================================================================
# AC13-3: Flag False → NÃO serve cache expirado
# ===========================================================================

@pytest.mark.asyncio
async def test_get_cascade_does_not_serve_expired_when_flag_false():
    """AC13: Com flag=False, cache expirado não é servido mesmo com fontes down."""
    call_count = [0]

    async def mock_cascade_read(user_id, params_hash, params, hit_fn):
        call_count[0] += 1
        return None  # Sempre miss

    with (
        patch("config.SERVE_EXPIRED_CACHE_ON_TOTAL_OUTAGE", False),
        patch("config.CACHE_LEGACY_KEY_FALLBACK", False),
        patch("cache.cascade._all_sources_down", return_value=True),
        patch("cache.cascade._cascade_read_levels", side_effect=mock_cascade_read),
        patch("metrics.CACHE_HITS") as mock_hits,
        patch("metrics.CACHE_MISSES") as mock_misses,
    ):
        mock_hits.labels.return_value = MagicMock()
        mock_misses.labels.return_value = MagicMock()
        from cache.cascade import get_from_cache_cascade
        result = await get_from_cache_cascade(
            user_id="user-123",
            params={"setor_id": "vestuario", "ufs": ["SP"]},
        )

    assert result is None
    # Com flag=False, não deve tentar segunda chamada allow_expired
    assert call_count[0] == 1


# ===========================================================================
# AC13-4: Fontes disponíveis → NÃO ativa fallback de expirado
# ===========================================================================

@pytest.mark.asyncio
async def test_get_cascade_no_expired_fallback_when_sources_up():
    """AC13: Com fontes disponíveis, não tenta servir cache expirado."""
    call_count = [0]

    async def mock_cascade_read(user_id, params_hash, params, hit_fn):
        call_count[0] += 1
        return None  # Miss

    with (
        patch("config.SERVE_EXPIRED_CACHE_ON_TOTAL_OUTAGE", True),
        patch("config.CACHE_LEGACY_KEY_FALLBACK", False),
        patch("cache.cascade._all_sources_down", return_value=False),  # Fontes UP
        patch("cache.cascade._cascade_read_levels", side_effect=mock_cascade_read),
        patch("metrics.CACHE_HITS") as mock_hits,
        patch("metrics.CACHE_MISSES") as mock_misses,
    ):
        mock_hits.labels.return_value = MagicMock()
        mock_misses.labels.return_value = MagicMock()
        from cache.cascade import get_from_cache_cascade
        result = await get_from_cache_cascade(
            user_id="user-123",
            params={"setor_id": "vestuario", "ufs": ["SP"]},
        )

    assert result is None
    assert call_count[0] == 1  # Apenas uma chamada, sem retry allow_expired


# ===========================================================================
# AC13-5: Expirado servido mas sem resultado → retorna None (cache não existe)
# ===========================================================================

@pytest.mark.asyncio
async def test_get_cascade_expired_but_no_cache_available():
    """AC13: Flag=True e fontes down, mas sem cache disponível → retorna None."""
    call_count = [0]

    async def mock_cascade_read(user_id, params_hash, params, hit_fn):
        call_count[0] += 1
        return None  # Ambas as chamadas retornam miss

    with (
        patch("config.SERVE_EXPIRED_CACHE_ON_TOTAL_OUTAGE", True),
        patch("config.CACHE_LEGACY_KEY_FALLBACK", False),
        patch("cache.cascade._all_sources_down", return_value=True),
        patch("cache.cascade._cascade_read_levels", side_effect=mock_cascade_read),
        patch("metrics.CACHE_HITS") as mock_hits,
        patch("metrics.CACHE_MISSES") as mock_misses,
    ):
        mock_hits.labels.return_value = MagicMock()
        mock_misses.labels.return_value = MagicMock()
        from cache.cascade import get_from_cache_cascade
        result = await get_from_cache_cascade(
            user_id="user-123",
            params={"setor_id": "vestuario", "ufs": ["SP"]},
        )

    assert result is None
    assert call_count[0] == 2  # Tentou both: normal e allow_expired


# ===========================================================================
# AC13-6: Cache normal (não expirado) servido normalmente sem is_stale_fallback
# ===========================================================================

@pytest.mark.asyncio
async def test_get_cascade_fresh_cache_no_stale_flag():
    """AC13: Cache fresco não recebe is_stale_fallback=True."""
    fresh_result = {"results": [{"id": "1"}], "total": 1, "cache_age_hours": 2.0}

    async def mock_cascade_read(user_id, params_hash, params, hit_fn):
        return fresh_result  # Hit imediato

    with (
        patch("config.CACHE_LEGACY_KEY_FALLBACK", False),
        patch("cache.cascade._cascade_read_levels", side_effect=mock_cascade_read),
        patch("metrics.CACHE_HITS") as mock_hits,
        patch("metrics.CACHE_MISSES") as mock_misses,
    ):
        mock_hits.labels.return_value = MagicMock()
        mock_misses.labels.return_value = MagicMock()
        from cache.cascade import get_from_cache_cascade
        result = await get_from_cache_cascade(
            user_id="user-123",
            params={"setor_id": "vestuario", "ufs": ["SP"]},
        )

    assert result is not None
    assert result.get("is_stale_fallback") is not True
