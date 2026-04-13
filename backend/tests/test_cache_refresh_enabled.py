"""CRIT-081 AC11: Tests for refresh_stale_cache_entries() cron function.

Verifies that:
- Batch size respects CACHE_REFRESH_BATCH_SIZE from config (default 50)
- HOT→WARM→COLD priority ordering is preserved
- Function dispatches revalidations correctly
- Handles no-stale-entries case gracefully
- Handles errors in individual dispatches without aborting
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


def _make_entry(user_id: str, params_hash: str, setor_id: str, priority: str, total_results: int = 5):
    return {
        "user_id": user_id,
        "params_hash": params_hash,
        "search_params": {"setor_id": setor_id, "ufs": ["SP"], "modalidades": None},
        "total_results": total_results,
        "priority": priority,
        "access_count": 3,
    }


# ===========================================================================
# AC11-1: Usa CACHE_REFRESH_BATCH_SIZE da config (default 50, não hardcoded 25)
# ===========================================================================

@pytest.mark.asyncio
async def test_refresh_uses_config_batch_size():
    """AC11: refresh_stale_cache_entries usa CACHE_REFRESH_BATCH_SIZE da config."""
    entries = [_make_entry(f"u{i}", f"hash{i}", "vestuario", "hot") for i in range(5)]

    mock_trigger = AsyncMock(return_value=True)
    captured_batch_size = {}

    async def mock_get_stale(batch_size):
        captured_batch_size["value"] = batch_size
        return entries

    with (
        patch("config.CACHE_REFRESH_BATCH_SIZE", 50),
        patch("search_cache.get_stale_entries_for_refresh", side_effect=mock_get_stale),
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        from jobs.cron.cache_ops import refresh_stale_cache_entries
        result = await refresh_stale_cache_entries()

    assert captured_batch_size["value"] == 50, "Deve usar CACHE_REFRESH_BATCH_SIZE=50, não 25"
    assert result["status"] == "completed"
    assert result["refreshed"] == 5


@pytest.mark.asyncio
async def test_refresh_uses_custom_batch_size():
    """AC11: CACHE_REFRESH_BATCH_SIZE configurável via variável."""
    captured_batch_size = {}

    async def mock_get_stale(batch_size):
        captured_batch_size["value"] = batch_size
        return []

    with (
        patch("config.CACHE_REFRESH_BATCH_SIZE", 75),
        patch("search_cache.get_stale_entries_for_refresh", side_effect=mock_get_stale),
    ):
        from jobs.cron.cache_ops import refresh_stale_cache_entries
        await refresh_stale_cache_entries()

    assert captured_batch_size["value"] == 75


# ===========================================================================
# AC11-2: HOT→WARM→COLD ordering é respeitado
# ===========================================================================

@pytest.mark.asyncio
async def test_refresh_processes_hot_before_warm_before_cold():
    """AC11: Entradas HOT são processadas antes de WARM, WARM antes de COLD.

    A função get_stale_entries_for_refresh() retorna em ordem HOT→WARM→COLD;
    refresh_stale_cache_entries() preserva essa ordem ao processar.
    """
    hot_entry = _make_entry("u1", "hash_hot", "vestuario", "hot")
    warm_entry = _make_entry("u2", "hash_warm", "alimentos", "warm")
    cold_entry = _make_entry("u3", "hash_cold", "software_desenvolvimento", "cold")

    entries_in_order = [hot_entry, warm_entry, cold_entry]
    call_order = []

    async def mock_trigger(user_id, params, request_data):
        call_order.append(params.get("setor_id"))
        return True

    with (
        patch("config.CACHE_REFRESH_BATCH_SIZE", 50),
        patch("search_cache.get_stale_entries_for_refresh", new_callable=AsyncMock, return_value=entries_in_order),
        patch("search_cache.trigger_background_revalidation", side_effect=mock_trigger),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        from jobs.cron.cache_ops import refresh_stale_cache_entries
        result = await refresh_stale_cache_entries()

    assert call_order == ["vestuario", "alimentos", "software_desenvolvimento"]
    assert result["refreshed"] == 3


# ===========================================================================
# AC11-3: Nenhuma entrada stale → retorna no_stale_entries
# ===========================================================================

@pytest.mark.asyncio
async def test_refresh_no_stale_entries():
    """AC11: Sem entradas stale → status no_stale_entries."""
    with (
        patch("config.CACHE_REFRESH_BATCH_SIZE", 50),
        patch("search_cache.get_stale_entries_for_refresh", new_callable=AsyncMock, return_value=[]),
    ):
        from jobs.cron.cache_ops import refresh_stale_cache_entries
        result = await refresh_stale_cache_entries()

    assert result["status"] == "no_stale_entries"
    assert result["refreshed"] == 0


# ===========================================================================
# AC11-4: Erros individuais não abortam o ciclo
# ===========================================================================

@pytest.mark.asyncio
async def test_refresh_individual_errors_dont_abort():
    """AC11: Erro numa entrada não aborta as demais."""
    entries = [
        _make_entry("u1", "hash1", "vestuario", "hot"),
        _make_entry("u2", "hash2", "alimentos", "warm"),
        _make_entry("u3", "hash3", "informatica", "cold"),
    ]

    async def mock_trigger(user_id, params, request_data):
        if params["setor_id"] == "alimentos":
            raise Exception("network error")
        return True

    with (
        patch("config.CACHE_REFRESH_BATCH_SIZE", 50),
        patch("search_cache.get_stale_entries_for_refresh", new_callable=AsyncMock, return_value=entries),
        patch("search_cache.trigger_background_revalidation", side_effect=mock_trigger),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        from jobs.cron.cache_ops import refresh_stale_cache_entries
        result = await refresh_stale_cache_entries()

    assert result["status"] == "completed"
    assert result["refreshed"] == 2
    assert result["failed"] == 1
    assert result["total"] == 3


# ===========================================================================
# AC11-5: Datas de busca são hoje-10d..hoje
# ===========================================================================

@pytest.mark.asyncio
async def test_refresh_injects_correct_date_window():
    """AC11: request_data tem data_inicial=hoje-10d e data_final=hoje."""
    from datetime import date, timedelta

    entry = _make_entry("u1", "hash1", "vestuario", "hot")
    captured_kwargs = []

    async def mock_trigger(user_id, params, request_data):
        captured_kwargs.append(request_data)
        return True

    with (
        patch("config.CACHE_REFRESH_BATCH_SIZE", 50),
        patch("search_cache.get_stale_entries_for_refresh", new_callable=AsyncMock, return_value=[entry]),
        patch("search_cache.trigger_background_revalidation", side_effect=mock_trigger),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        from jobs.cron.cache_ops import refresh_stale_cache_entries
        await refresh_stale_cache_entries()

    assert len(captured_kwargs) == 1
    rd = captured_kwargs[0]
    assert rd["data_final"] == date.today().isoformat()
    assert rd["data_inicial"] == (date.today() - timedelta(days=10)).isoformat()
