"""DEBT-04 AC5: Integration tests for async alert cron processing.

Validates that run_all_alerts() processes alerts in parallel using
asyncio.gather + Semaphore(10), achieving correct results and concurrency.

Tests:
  - Sequential correctness: all alerts processed, counters accurate
  - Parallel execution: concurrent alerts run simultaneously (not sequentially)
  - Semaphore limiting: concurrency bounded to _ALERTS_CONCURRENCY
  - Error isolation: one alert failure does not abort others
  - Skip accounting: rate-limited / no-result alerts counted correctly
"""

import asyncio
import os
import sys
import time
from unittest.mock import AsyncMock, patch, MagicMock, Mock

import pytest

# ARQ mock (must be set before importing app)
mock_arq = MagicMock()
sys.modules.setdefault("arq", mock_arq)
sys.modules.setdefault("arq.connections", MagicMock())
sys.modules.setdefault("arq.cron", MagicMock())

# Ensure env vars are set before any module import
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.test")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("ENCRYPTION_KEY", "bzc732A921Puw9JN4lrzMo1nw0EjlcUdAyR6Z6N7Sqc=")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_supabase():
    """Mock supabase_client.get_supabase so tests never hit a real DB."""
    mock_client = Mock()
    with patch("supabase_client.get_supabase", return_value=mock_client):
        yield mock_client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_alert(alert_id: str, email: str) -> dict:
    return {
        "id": alert_id,
        "user_id": f"user-{alert_id}",
        "name": f"Alert {alert_id}",
        "filters": {"setor": "vestuario", "ufs": ["SP"]},
        "email": email,
        "full_name": "Test User",
    }


def _make_opportunity(opp_id: str) -> dict:
    return {
        "id": opp_id,
        "titulo": f"Oportunidade {opp_id}",
        "orgao": "Prefeitura",
        "valor_estimado": 10000.0,
        "uf": "SP",
        "modalidade": "Pregao Eletronico",
        "link_pncp": "",
        "viability_score": 0.8,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_run_all_alerts_empty():
    """No active alerts → summary with zeros, no errors."""
    with patch("services.alert_service.get_active_alerts", new_callable=AsyncMock, return_value=[]):
        from services.alert_service import run_all_alerts
        result = await run_all_alerts()

    assert result["total_alerts"] == 0
    assert result["sent"] == 0
    assert result["skipped"] == 0
    assert result["errors"] == 0
    assert result["payloads"] == []


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_run_all_alerts_single_alert_with_results():
    """Single alert with new opportunities → counted as sent."""
    alert = _make_alert("alert-001", "user@example.com")
    opp = _make_opportunity("opp-001")

    with (
        patch("services.alert_service.get_active_alerts", new_callable=AsyncMock, return_value=[alert]),
        patch("services.alert_service.check_rate_limit", new_callable=AsyncMock, return_value=False),
        patch("services.alert_service.execute_alert_search", new_callable=AsyncMock, return_value=[opp]),
        patch("services.alert_service.get_sent_item_ids", new_callable=AsyncMock, return_value=set()),
    ):
        from services.alert_service import run_all_alerts
        result = await run_all_alerts()

    assert result["total_alerts"] == 1
    assert result["sent"] == 1
    assert result["skipped"] == 0
    assert result["errors"] == 0
    assert len(result["payloads"]) == 1
    assert result["payloads"][0]["alert_id"] == "alert-001"
    assert len(result["payloads"][0]["opportunities"]) == 1


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_run_all_alerts_rate_limited():
    """Rate-limited alert → skipped, not sent."""
    alert = _make_alert("alert-002", "user@example.com")

    with (
        patch("services.alert_service.get_active_alerts", new_callable=AsyncMock, return_value=[alert]),
        patch("services.alert_service.check_rate_limit", new_callable=AsyncMock, return_value=True),
    ):
        from services.alert_service import run_all_alerts
        result = await run_all_alerts()

    assert result["total_alerts"] == 1
    assert result["sent"] == 0
    assert result["skipped"] == 1
    assert result["errors"] == 0


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_run_all_alerts_error_isolation():
    """One alert raises → counted as error, others still processed."""
    alerts = [
        _make_alert("alert-good", "good@example.com"),
        _make_alert("alert-bad", "bad@example.com"),
    ]
    opp = _make_opportunity("opp-good")

    call_count = 0

    async def _process_side_effect(alert, db=None):
        nonlocal call_count
        call_count += 1
        if alert["id"] == "alert-bad":
            raise RuntimeError("Simulated DB failure")
        return {
            "alert_id": alert["id"],
            "user_id": alert["user_id"],
            "email": alert["email"],
            "full_name": alert["full_name"],
            "alert_name": alert["name"],
            "opportunities": [opp],
            "total_count": 1,
            "skipped": False,
            "skip_reason": None,
        }

    with (
        patch("services.alert_service.get_active_alerts", new_callable=AsyncMock, return_value=alerts),
        patch("services.alert_service.process_single_alert", side_effect=_process_side_effect),
    ):
        from services.alert_service import run_all_alerts
        result = await run_all_alerts()

    assert result["total_alerts"] == 2
    assert result["sent"] == 1
    assert result["errors"] == 1
    assert call_count == 2  # both were attempted


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_run_all_alerts_parallel_execution():
    """Alerts run concurrently, not sequentially.

    Each alert simulates 100ms of I/O. With 5 alerts in parallel,
    total time should be << 5 × 100ms = 500ms. Sequential would take ~500ms.
    """
    num_alerts = 5
    delay_per_alert = 0.1  # 100ms per alert
    alerts = [_make_alert(f"alert-{i}", f"user{i}@example.com") for i in range(num_alerts)]
    opp = _make_opportunity("opp-parallel")

    async def _slow_process(alert, db=None):
        await asyncio.sleep(delay_per_alert)
        return {
            "alert_id": alert["id"],
            "user_id": alert["user_id"],
            "email": alert["email"],
            "full_name": alert["full_name"],
            "alert_name": alert["name"],
            "opportunities": [opp],
            "total_count": 1,
            "skipped": False,
            "skip_reason": None,
        }

    with (
        patch("services.alert_service.get_active_alerts", new_callable=AsyncMock, return_value=alerts),
        patch("services.alert_service.process_single_alert", side_effect=_slow_process),
    ):
        from services.alert_service import run_all_alerts
        start = time.monotonic()
        result = await run_all_alerts()
        elapsed = time.monotonic() - start

    assert result["total_alerts"] == num_alerts
    assert result["sent"] == num_alerts
    assert result["errors"] == 0

    # Parallel: should complete well under sequential time (num_alerts × delay)
    sequential_time = num_alerts * delay_per_alert
    # Allow 3x delay_per_alert as generous upper bound for parallel execution
    assert elapsed < sequential_time * 0.8, (
        f"Expected parallel execution < {sequential_time * 0.8:.2f}s, got {elapsed:.2f}s. "
        "Possible regression: alerts may be running sequentially."
    )


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_run_all_alerts_semaphore_limits_concurrency():
    """Semaphore ensures at most _ALERTS_CONCURRENCY alerts run at once."""
    from services.alert_service import _ALERTS_CONCURRENCY

    num_alerts = _ALERTS_CONCURRENCY + 5  # More alerts than the semaphore allows
    alerts = [_make_alert(f"alert-{i}", f"user{i}@example.com") for i in range(num_alerts)]

    concurrent_peak = 0
    current_concurrent = 0
    lock = asyncio.Lock()

    async def _track_concurrency(alert, db=None):
        nonlocal concurrent_peak, current_concurrent
        async with lock:
            current_concurrent += 1
            if current_concurrent > concurrent_peak:
                concurrent_peak = current_concurrent

        await asyncio.sleep(0.05)  # 50ms I/O simulation

        async with lock:
            current_concurrent -= 1

        return {
            "alert_id": alert["id"],
            "user_id": alert["user_id"],
            "email": alert["email"],
            "full_name": alert["full_name"],
            "alert_name": alert["name"],
            "opportunities": [],
            "total_count": 0,
            "skipped": True,
            "skip_reason": "no_results",
        }

    with (
        patch("services.alert_service.get_active_alerts", new_callable=AsyncMock, return_value=alerts),
        patch("services.alert_service.process_single_alert", side_effect=_track_concurrency),
    ):
        from services.alert_service import run_all_alerts
        result = await run_all_alerts()

    assert result["total_alerts"] == num_alerts
    assert concurrent_peak <= _ALERTS_CONCURRENCY, (
        f"Concurrency peak {concurrent_peak} exceeded Semaphore limit {_ALERTS_CONCURRENCY}"
    )


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_run_all_alerts_all_skipped():
    """All alerts have no results → all skipped, 0 sent."""
    alerts = [_make_alert(f"alert-{i}", f"user{i}@example.com") for i in range(3)]

    async def _no_results(alert, db=None):
        return {
            "alert_id": alert["id"],
            "user_id": alert["user_id"],
            "email": alert["email"],
            "full_name": alert["full_name"],
            "alert_name": alert["name"],
            "opportunities": [],
            "total_count": 0,
            "skipped": True,
            "skip_reason": "no_results",
        }

    with (
        patch("services.alert_service.get_active_alerts", new_callable=AsyncMock, return_value=alerts),
        patch("services.alert_service.process_single_alert", side_effect=_no_results),
    ):
        from services.alert_service import run_all_alerts
        result = await run_all_alerts()

    assert result["total_alerts"] == 3
    assert result["sent"] == 0
    assert result["skipped"] == 3
    assert result["errors"] == 0
    assert result["payloads"] == []


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_run_all_alerts_mixed_outcomes():
    """Mix of sent, skipped, error alerts — all counters accurate."""
    alerts = [
        _make_alert("alert-sent", "sent@example.com"),
        _make_alert("alert-skipped", "skipped@example.com"),
        _make_alert("alert-error", "error@example.com"),
    ]
    opp = _make_opportunity("opp-mixed")

    async def _mixed_process(alert, db=None):
        if alert["id"] == "alert-sent":
            return {
                "alert_id": alert["id"],
                "user_id": alert["user_id"],
                "email": alert["email"],
                "full_name": alert["full_name"],
                "alert_name": alert["name"],
                "opportunities": [opp],
                "total_count": 1,
                "skipped": False,
                "skip_reason": None,
            }
        elif alert["id"] == "alert-skipped":
            return {
                "alert_id": alert["id"],
                "user_id": alert["user_id"],
                "email": alert["email"],
                "full_name": alert["full_name"],
                "alert_name": alert["name"],
                "opportunities": [],
                "total_count": 0,
                "skipped": True,
                "skip_reason": "rate_limited",
            }
        else:
            raise ValueError("Simulated error in alert processing")

    with (
        patch("services.alert_service.get_active_alerts", new_callable=AsyncMock, return_value=alerts),
        patch("services.alert_service.process_single_alert", side_effect=_mixed_process),
    ):
        from services.alert_service import run_all_alerts
        result = await run_all_alerts()

    assert result["total_alerts"] == 3
    assert result["sent"] == 1
    assert result["skipped"] == 1
    assert result["errors"] == 1
    assert len(result["payloads"]) == 1
    assert result["payloads"][0]["alert_id"] == "alert-sent"
