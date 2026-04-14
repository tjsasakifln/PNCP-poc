"""STORY-2.11 (EPIC-TD-2026Q2 P0): Tests for LLM monthly budget tracking.

Covers:
- track_llm_cost() increments Redis counter with 32d TTL
- Progressive Sentry alerts at 50% / 80% / 100% thresholds
- is_budget_exceeded() reads the flag set at 100%
- get_cost_snapshot() returns expected structure
- Graceful fallback when Redis is unavailable
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def budget_env(monkeypatch):
    monkeypatch.setenv("LLM_MONTHLY_BUDGET_USD", "100")
    yield 100.0


@pytest.fixture
def mock_redis_available():
    """Mock async Redis com métodos usados pelo llm_budget."""
    mock = AsyncMock()
    mock.incrbyfloat = AsyncMock(return_value=10.0)
    mock.ttl = AsyncMock(return_value=100000)
    mock.expire = AsyncMock(return_value=True)
    mock.set = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=None)
    return mock


# ---------------------------------------------------------------------------
# track_llm_cost: Redis INCRBYFLOAT + TTL
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_track_llm_cost_increments_redis_counter(
    budget_env, mock_redis_available
):
    mock_redis_available.incrbyfloat.return_value = 5.25

    with patch(
        "redis_pool.get_redis_pool",
        AsyncMock(return_value=mock_redis_available),
    ):
        from llm_budget import track_llm_cost

        total = await track_llm_cost(5.25)

    assert total == 5.25
    # Chamada ao INCRBYFLOAT com a chave do mês atual
    call_args = mock_redis_available.incrbyfloat.call_args
    assert call_args[0][0].startswith("llm_cost_month_")
    assert call_args[0][1] == 5.25


@pytest.mark.asyncio
async def test_track_llm_cost_sets_32d_ttl_when_missing(budget_env):
    mock_redis = AsyncMock()
    mock_redis.incrbyfloat = AsyncMock(return_value=10.0)
    mock_redis.ttl = AsyncMock(return_value=-1)  # Sem TTL
    mock_redis.expire = AsyncMock()
    mock_redis.set = AsyncMock(return_value=False)
    mock_redis.get = AsyncMock(return_value=None)

    with patch(
        "redis_pool.get_redis_pool", AsyncMock(return_value=mock_redis)
    ):
        from llm_budget import track_llm_cost

        await track_llm_cost(1.0)

    mock_redis.expire.assert_called()
    # 32 dias = 2764800s
    call_ttl = mock_redis.expire.call_args[0][1]
    assert call_ttl == 32 * 86400


@pytest.mark.asyncio
async def test_track_llm_cost_redis_down_returns_zero(budget_env):
    with patch("redis_pool.get_redis_pool", AsyncMock(return_value=None)):
        from llm_budget import track_llm_cost

        total = await track_llm_cost(5.0)

    assert total == 0.0


@pytest.mark.asyncio
async def test_track_llm_cost_zero_or_negative_is_noop(budget_env):
    mock_redis = AsyncMock()
    with patch(
        "redis_pool.get_redis_pool", AsyncMock(return_value=mock_redis)
    ):
        from llm_budget import track_llm_cost

        assert await track_llm_cost(0) == 0.0
        assert await track_llm_cost(-5.0) == 0.0

    mock_redis.incrbyfloat.assert_not_called()


# ---------------------------------------------------------------------------
# Progressive Sentry alerts at 50/80/100 thresholds
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sentry_alert_fires_at_50_percent(budget_env):
    """Total 50 USD de budget 100 → alerta 50% com level=warning."""
    mock_redis = AsyncMock()
    mock_redis.incrbyfloat = AsyncMock(return_value=50.0)
    mock_redis.ttl = AsyncMock(return_value=100000)
    mock_redis.expire = AsyncMock()
    mock_redis.set = AsyncMock(return_value=True)  # SETNX sucesso = primeiro alerta
    mock_redis.get = AsyncMock(return_value=None)

    with patch(
        "redis_pool.get_redis_pool", AsyncMock(return_value=mock_redis)
    ), patch("sentry_sdk.capture_message") as mock_capture:
        from llm_budget import track_llm_cost

        await track_llm_cost(50.0)

    # Só o alerta de 50% dispara (80 e 100 não)
    assert mock_capture.call_count == 1
    args, kwargs = mock_capture.call_args
    assert "50%" in args[0]
    assert kwargs["level"] == "warning"


@pytest.mark.asyncio
async def test_sentry_alerts_fire_at_80_and_50_when_crossed(budget_env):
    """Total 80 USD → dispara alertas 50% (warning) e 80% (error)."""
    mock_redis = AsyncMock()
    mock_redis.incrbyfloat = AsyncMock(return_value=80.0)
    mock_redis.ttl = AsyncMock(return_value=100000)
    mock_redis.expire = AsyncMock()
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.get = AsyncMock(return_value=None)

    with patch(
        "redis_pool.get_redis_pool", AsyncMock(return_value=mock_redis)
    ), patch("sentry_sdk.capture_message") as mock_capture:
        from llm_budget import track_llm_cost

        await track_llm_cost(80.0)

    assert mock_capture.call_count == 2
    levels = [c.kwargs["level"] for c in mock_capture.call_args_list]
    assert "warning" in levels  # 50%
    assert "error" in levels  # 80%


@pytest.mark.asyncio
async def test_sentry_alert_fires_at_100_and_sets_exceeded_flag(budget_env):
    """Total >=100 USD → dispara 3 alertas e seta flag de hard-reject."""
    mock_redis = AsyncMock()
    mock_redis.incrbyfloat = AsyncMock(return_value=105.0)
    mock_redis.ttl = AsyncMock(return_value=100000)
    mock_redis.expire = AsyncMock()
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.get = AsyncMock(return_value=None)

    with patch(
        "redis_pool.get_redis_pool", AsyncMock(return_value=mock_redis)
    ), patch("sentry_sdk.capture_message") as mock_capture:
        from llm_budget import track_llm_cost

        await track_llm_cost(105.0)

    # 50%, 80%, 100% todos disparam
    assert mock_capture.call_count == 3
    levels = [c.kwargs["level"] for c in mock_capture.call_args_list]
    assert "fatal" in levels

    # Flag de exceeded setada (além dos 3 alert keys)
    set_keys = [call.args[0] for call in mock_redis.set.call_args_list]
    assert any(k.startswith("llm_budget_exceeded_") for k in set_keys)


@pytest.mark.asyncio
async def test_sentry_alert_deduped_via_setnx(budget_env):
    """Se SETNX retorna False (já existe), Sentry NÃO é re-chamado."""
    mock_redis = AsyncMock()
    mock_redis.incrbyfloat = AsyncMock(return_value=55.0)
    mock_redis.ttl = AsyncMock(return_value=100000)
    mock_redis.expire = AsyncMock()
    mock_redis.set = AsyncMock(return_value=False)  # Alert key já existe
    mock_redis.get = AsyncMock(return_value=None)

    with patch(
        "redis_pool.get_redis_pool", AsyncMock(return_value=mock_redis)
    ), patch("sentry_sdk.capture_message") as mock_capture:
        from llm_budget import track_llm_cost

        await track_llm_cost(55.0)

    assert mock_capture.call_count == 0


# ---------------------------------------------------------------------------
# is_budget_exceeded
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_is_budget_exceeded_returns_true_when_flag_set():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value="1")

    with patch(
        "redis_pool.get_redis_pool", AsyncMock(return_value=mock_redis)
    ):
        from llm_budget import is_budget_exceeded

        assert await is_budget_exceeded() is True


@pytest.mark.asyncio
async def test_is_budget_exceeded_false_when_flag_missing():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)

    with patch(
        "redis_pool.get_redis_pool", AsyncMock(return_value=mock_redis)
    ):
        from llm_budget import is_budget_exceeded

        assert await is_budget_exceeded() is False


@pytest.mark.asyncio
async def test_is_budget_exceeded_fail_open_on_redis_error():
    with patch(
        "redis_pool.get_redis_pool",
        AsyncMock(side_effect=RuntimeError("redis down")),
    ):
        from llm_budget import is_budget_exceeded

        assert await is_budget_exceeded() is False


def test_is_budget_exceeded_sync_returns_true_when_flag_set():
    mock_redis = MagicMock()
    mock_redis.get = MagicMock(return_value="1")

    with patch("redis_pool.get_sync_redis", return_value=mock_redis):
        from llm_budget import is_budget_exceeded_sync

        assert is_budget_exceeded_sync() is True


def test_is_budget_exceeded_sync_fail_open():
    with patch(
        "redis_pool.get_sync_redis",
        side_effect=RuntimeError("no redis"),
    ):
        from llm_budget import is_budget_exceeded_sync

        assert is_budget_exceeded_sync() is False


# ---------------------------------------------------------------------------
# get_cost_snapshot
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_cost_snapshot_shape(budget_env):
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(side_effect=["42.5", None])

    with patch(
        "redis_pool.get_redis_pool", AsyncMock(return_value=mock_redis)
    ):
        from llm_budget import get_cost_snapshot

        snap = await get_cost_snapshot()

    # Keys requeridas
    for key in (
        "month_to_date_usd",
        "budget_usd",
        "pct_used",
        "projected_end_of_month_usd",
        "month",
        "exceeded",
    ):
        assert key in snap

    assert snap["month_to_date_usd"] == 42.5
    assert snap["budget_usd"] == 100.0
    assert snap["pct_used"] == 42.5
    assert snap["exceeded"] is False
    assert snap["month"].startswith("llm_cost_month_")


@pytest.mark.asyncio
async def test_get_cost_snapshot_redis_down(budget_env):
    """Redis None → zeros sem crashar."""
    with patch("redis_pool.get_redis_pool", AsyncMock(return_value=None)):
        from llm_budget import get_cost_snapshot

        snap = await get_cost_snapshot()

    assert snap["month_to_date_usd"] == 0.0
    assert snap["exceeded"] is False
    assert snap["pct_used"] == 0.0
