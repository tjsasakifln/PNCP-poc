"""GTM-ARCH-002: Tests for global cross-user cache, warmup cron, and multi-source revalidation.

Required tests:
  T1: Trial user receives global cache when personal cache empty
  T2: params_hash_global doesn't include user_id
  T3: Global cache doesn't overwrite existing personal cache
  T4: Cron refresh executes for HOT entries
  T5: Warmup post-deploy enqueues top 10 params
  T6: Revalidation uses ConsolidationService (not PNCP-only)
"""

import hashlib
import json
from datetime import datetime, timezone, timedelta, date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ===========================================================================
# T1: Trial user receives global cache when personal cache empty
# ===========================================================================

@pytest.mark.asyncio
async def test_trial_user_receives_global_cache():
    """T1: When user has no personal cache, global fallback provides cached results."""
    from search_cache import get_from_cache, compute_global_hash

    params = {
        "setor_id": "vestuario",
        "ufs": ["SP", "RJ"],
        "status": None,
        "modalidades": [6],
        "modo_busca": None,
        "data_inicio": "2026-02-13",
        "data_fim": "2026-02-23",
    }

    compute_global_hash(params)
    now = datetime.now(timezone.utc)
    fetched_at = (now - timedelta(hours=2)).isoformat()

    # Build Supabase mock:
    # - 1st call: _get_from_supabase (user personal cache) → empty
    # - 2nd call: _increment_and_reclassify → not reached
    # - 3rd call: _get_global_fallback_from_supabase → returns results
    mock_sb = MagicMock()
    mock_table = MagicMock()
    mock_sb.table.return_value = mock_table

    call_count = [0]

    def mock_select(*args, **kwargs):
        chain = MagicMock()
        call_count[0] += 1
        for method in ("eq", "lt", "gt", "gte", "lte", "order", "limit", "neq"):
            getattr(chain, method).return_value = chain

        if call_count[0] == 1:
            # Personal cache miss
            chain.execute.return_value = MagicMock(data=[])
        else:
            # Global fallback hit
            chain.execute.return_value = MagicMock(data=[{
                "results": [{"titulo": "Licitacao Global"}],
                "total_results": 1,
                "sources_json": ["PNCP"],
                "fetched_at": fetched_at,
                "created_at": fetched_at,
                "priority": "warm",
                "access_count": 5,
                "last_accessed_at": now.isoformat(),
            }])
        return chain

    mock_table.select = mock_select

    # Mock Redis and local cache to return None (miss)
    mock_redis_cache = MagicMock()
    mock_redis_cache.get.return_value = None

    with (
        patch("supabase_client.get_supabase", return_value=mock_sb),
        patch("redis_pool.get_fallback_cache", return_value=mock_redis_cache),
        patch("cache.manager.METRICS_CACHE_HITS", MagicMock()),
        patch("cache.manager.METRICS_CACHE_MISSES", MagicMock()),
        patch("middleware.search_id_var", MagicMock(get=lambda x: "-")),
    ):
        result = await get_from_cache(
            user_id="trial-user-new",
            params=params,
        )

    assert result is not None, "Trial user should receive global cache fallback"
    assert result["cache_level"] == "global"
    assert len(result["results"]) == 1
    assert result["results"][0]["titulo"] == "Licitacao Global"


# ===========================================================================
# T2: params_hash_global doesn't include user_id
# ===========================================================================

def test_params_hash_global_excludes_user_id():
    """T2: compute_global_hash produces same hash regardless of user_id."""
    from search_cache import compute_global_hash

    params_user_a = {
        "setor_id": "vestuario",
        "ufs": ["SP", "RJ"],
        "data_inicio": "2026-02-13",
        "data_fim": "2026-02-23",
        "user_id": "user-a-uuid",  # Should be ignored
    }

    params_user_b = {
        "setor_id": "vestuario",
        "ufs": ["RJ", "SP"],  # Different order, should normalize
        "data_inicio": "2026-02-13",
        "data_fim": "2026-02-23",
        "user_id": "user-b-uuid",  # Different user, should be ignored
    }

    hash_a = compute_global_hash(params_user_a)
    hash_b = compute_global_hash(params_user_b)

    assert hash_a == hash_b, "Global hash must be identical for same params regardless of user_id"

    # Verify user_id is NOT in the hash input
    normalized = {
        "setor_id": "vestuario",
        "ufs": ["RJ", "SP"],  # sorted
        "data_inicio": "2026-02-13",
        "data_fim": "2026-02-23",
    }
    expected = hashlib.sha256(json.dumps(normalized, sort_keys=True).encode()).hexdigest()
    assert hash_a == expected


def test_params_hash_global_differs_by_setor():
    """T2b: Different sectors produce different global hashes."""
    from search_cache import compute_global_hash

    hash_vest = compute_global_hash({"setor_id": "vestuario", "ufs": ["SP"], "data_inicio": "2026-02-13", "data_fim": "2026-02-23"})
    hash_alim = compute_global_hash({"setor_id": "alimentos", "ufs": ["SP"], "data_inicio": "2026-02-13", "data_fim": "2026-02-23"})

    assert hash_vest != hash_alim, "Different sectors must produce different global hashes"


# ===========================================================================
# T3: Global cache doesn't overwrite existing personal cache
# ===========================================================================

@pytest.mark.asyncio
async def test_global_cache_does_not_overwrite_personal():
    """T3: When user has personal cache, global fallback is NOT used (personal takes priority)."""
    from search_cache import get_from_cache

    params = {
        "setor_id": "vestuario",
        "ufs": ["SP"],
        "status": None,
        "modalidades": [6],
        "modo_busca": None,
    }

    now = datetime.now(timezone.utc)
    fetched_at = (now - timedelta(hours=1)).isoformat()

    mock_sb = MagicMock()
    mock_table = MagicMock()
    mock_sb.table.return_value = mock_table

    call_count = [0]

    def mock_select(*args, **kwargs):
        chain = MagicMock()
        call_count[0] += 1
        for method in ("eq", "lt", "gt", "gte", "lte", "order", "limit", "neq"):
            getattr(chain, method).return_value = chain

        if call_count[0] == 1:
            # Personal cache HIT with user's own results
            chain.execute.return_value = MagicMock(data=[{
                "results": [{"titulo": "Minha Licitacao Pessoal"}],
                "total_results": 1,
                "sources_json": ["PNCP"],
                "fetched_at": fetched_at,
                "created_at": fetched_at,
                "priority": "warm",
                "access_count": 3,
                "last_accessed_at": now.isoformat(),
            }])
        elif call_count[0] == 2:
            # _increment_and_reclassify read
            chain.execute.return_value = MagicMock(data=[{
                "access_count": 3,
                "last_accessed_at": now.isoformat(),
                "priority": "warm",
            }])
        else:
            # _increment_and_reclassify update
            chain.execute.return_value = MagicMock(data=[])
        return chain

    mock_table.select = mock_select
    mock_table.update.return_value = MagicMock(eq=MagicMock(return_value=MagicMock(eq=MagicMock(return_value=MagicMock(execute=MagicMock(return_value=MagicMock(data=[])))))))

    mock_redis_cache = MagicMock()
    mock_redis_cache.get.return_value = None
    mock_redis_cache.incr.return_value = 1

    with (
        patch("supabase_client.get_supabase", return_value=mock_sb),
        patch("redis_pool.get_fallback_cache", return_value=mock_redis_cache),
        patch("cache.manager.METRICS_CACHE_HITS", MagicMock()),
        patch("cache.manager.METRICS_CACHE_MISSES", MagicMock()),
        patch("middleware.search_id_var", MagicMock(get=lambda x: "-")),
    ):
        result = await get_from_cache(
            user_id="user-with-personal-cache",
            params=params,
        )

    assert result is not None
    assert result["results"][0]["titulo"] == "Minha Licitacao Pessoal"
    # Global fallback should NOT have been used
    assert result["cache_level"] != "global"


# ===========================================================================
# T4: Cron refresh executes for HOT entries
# ===========================================================================

@pytest.mark.asyncio
async def test_cron_refresh_executes_for_hot_entries():
    """T4: refresh_stale_cache_entries dispatches revalidation for HOT stale entries."""
    from cron_jobs import refresh_stale_cache_entries

    stale_entries = [
        {
            "user_id": "u1",
            "params_hash": "hash_hot_1",
            "search_params": {"setor_id": "vestuario", "ufs": ["SP", "RJ"], "modalidades": [6]},
            "total_results": 15,
            "priority": "hot",
            "access_count": 10,
        },
        {
            "user_id": "u2",
            "params_hash": "hash_hot_2",
            "search_params": {"setor_id": "alimentos", "ufs": ["MG"]},
            "total_results": 8,
            "priority": "hot",
            "access_count": 5,
        },
    ]

    mock_trigger = AsyncMock(return_value=True)

    with (
        patch("search_cache.get_stale_entries_for_refresh", new_callable=AsyncMock, return_value=stale_entries),
        patch("search_cache.trigger_background_revalidation", mock_trigger),
    ):
        result = await refresh_stale_cache_entries()

    assert result["status"] == "completed"
    assert result["refreshed"] == 2
    assert mock_trigger.call_count == 2

    # Verify dates are today-10d to today
    expected_final = date.today().isoformat()
    expected_inicial = (date.today() - timedelta(days=10)).isoformat()

    for c in mock_trigger.call_args_list:
        kw = c.kwargs
        assert kw["request_data"]["data_inicial"] == expected_inicial
        assert kw["request_data"]["data_final"] == expected_final


# ===========================================================================
# T5: Warmup post-deploy enqueues top 10 params
# ===========================================================================

@pytest.mark.asyncio
async def test_warmup_post_deploy_enqueues_top_params():
    """T5: warmup_top_params fetches top 10 popular params and dispatches revalidation."""
    from cron_jobs import warmup_top_params

    top_params = [
        {"setor_id": "vestuario", "ufs": ["SP", "RJ"], "modalidades": [6]},
        {"setor_id": "alimentos", "ufs": ["MG", "RS"]},
        {"setor_id": "informatica", "ufs": ["DF"]},
    ]

    mock_trigger = AsyncMock(return_value=True)

    with (
        patch("search_cache.get_top_popular_params", new_callable=AsyncMock, return_value=top_params),
        patch("search_cache.trigger_background_revalidation", mock_trigger),
    ):
        result = await warmup_top_params()

    assert result["status"] == "completed"
    assert result["warmed"] == 3
    assert result["total"] == 3
    assert mock_trigger.call_count == 3

    # Verify each call uses the system warmup user_id
    for c in mock_trigger.call_args_list:
        kw = c.kwargs
        assert kw["user_id"] == "00000000-0000-0000-0000-000000000000"
        assert "data_inicial" in kw["request_data"]
        assert "data_final" in kw["request_data"]


@pytest.mark.asyncio
async def test_warmup_graceful_with_no_params():
    """T5b: warmup_top_params handles empty popular params gracefully."""
    from cron_jobs import warmup_top_params

    with patch("search_cache.get_top_popular_params", new_callable=AsyncMock, return_value=[]):
        result = await warmup_top_params()

    assert result["status"] == "no_params"
    assert result["warmed"] == 0


# ===========================================================================
# T6: Revalidation uses ConsolidationService (not PNCP-only)
# ===========================================================================

@pytest.mark.asyncio
async def test_revalidation_uses_consolidation_service():
    """T6: _fetch_multi_source_for_revalidation uses ConsolidationService with multiple sources."""
    from search_cache import _fetch_multi_source_for_revalidation

    request_data = {
        "ufs": ["SP", "RJ"],
        "data_inicial": "2026-02-13",
        "data_final": "2026-02-23",
        "modalidades": [6, 7],
    }

    # Mock source config with all sources enabled
    mock_source_config = MagicMock()
    mock_source_config.pncp.enabled = True
    mock_source_config.pncp.timeout = 30
    mock_source_config.compras_gov.enabled = True
    mock_source_config.compras_gov.timeout = 30
    mock_source_config.portal.enabled = False

    # Mock ConsolidationService
    mock_consolidation_result = MagicMock()
    mock_consolidation_result.records = [
        {"titulo": "Licitacao A"},
        {"titulo": "Licitacao B"},
    ]
    mock_consolidation_result.source_results = [
        MagicMock(source_code="PNCP", status="success"),
        MagicMock(source_code="COMPRAS_GOV", status="success"),
    ]

    mock_svc_instance = AsyncMock()
    mock_svc_instance.fetch_all = AsyncMock(return_value=mock_consolidation_result)
    mock_svc_instance.close = AsyncMock()

    # Patch at the source modules (deferred imports inside function body)
    with (
        patch("source_config.sources.get_source_config", return_value=mock_source_config),
        patch("consolidation.ConsolidationService", return_value=mock_svc_instance),
        patch("pncp_client.PNCPLegacyAdapter"),
        patch("clients.compras_gov_client.ComprasGovAdapter"),
    ):
        results, sources = await _fetch_multi_source_for_revalidation(request_data)

    assert len(results) == 2
    assert "PNCP" in sources
    assert "COMPRAS_GOV" in sources
    mock_svc_instance.fetch_all.assert_called_once()
    mock_svc_instance.close.assert_called_once()


@pytest.mark.asyncio
async def test_revalidation_falls_back_to_pncp_only():
    """T6b: When ConsolidationService fails, falls back to PNCP-only."""
    from search_cache import _fetch_multi_source_for_revalidation

    request_data = {
        "ufs": ["SP"],
        "data_inicial": "2026-02-13",
        "data_final": "2026-02-23",
        "modalidades": [6],
    }

    mock_pncp = AsyncMock(return_value=[{"titulo": "PNCP Fallback"}])

    # Make source_config.sources.get_source_config raise to trigger fallback
    with (
        patch("source_config.sources.get_source_config", side_effect=Exception("Source config unavailable")),
        patch("pncp_client.buscar_todas_ufs_paralelo", mock_pncp),
    ):
        results, sources = await _fetch_multi_source_for_revalidation(request_data)

    assert len(results) == 1
    assert sources == ["PNCP"]
    mock_pncp.assert_called_once()


# ===========================================================================
# Additional edge case tests
# ===========================================================================

def test_compute_global_hash_normalizes_ufs_order():
    """Global hash is deterministic regardless of UF input order."""
    from search_cache import compute_global_hash

    hash1 = compute_global_hash({"setor_id": "x", "ufs": ["SP", "RJ", "MG"], "data_inicio": "2026-01-01", "data_fim": "2026-01-10"})
    hash2 = compute_global_hash({"setor_id": "x", "ufs": ["MG", "SP", "RJ"], "data_inicio": "2026-01-01", "data_fim": "2026-01-10"})

    assert hash1 == hash2


def test_compute_global_hash_handles_missing_dates():
    """Global hash works even when dates are missing (uses None)."""
    from search_cache import compute_global_hash

    # Should not raise
    result = compute_global_hash({"setor_id": "x", "ufs": ["SP"]})
    assert isinstance(result, str)
    assert len(result) == 64  # SHA-256 hex digest length


@pytest.mark.asyncio
async def test_get_from_cache_cascade_uses_global_fallback():
    """Global fallback works in cascade mode too."""
    from search_cache import get_from_cache_cascade

    params = {
        "setor_id": "vestuario",
        "ufs": ["SP"],
        "status": None,
        "modalidades": [6],
        "modo_busca": None,
    }

    now = datetime.now(timezone.utc)
    fetched_at = (now - timedelta(hours=3)).isoformat()

    mock_sb = MagicMock()
    mock_table = MagicMock()
    mock_sb.table.return_value = mock_table

    call_count = [0]

    def mock_select(*args, **kwargs):
        chain = MagicMock()
        call_count[0] += 1
        for method in ("eq", "lt", "gt", "gte", "lte", "order", "limit", "neq"):
            getattr(chain, method).return_value = chain

        if call_count[0] == 1:
            # L1 Supabase personal miss
            chain.execute.return_value = MagicMock(data=[])
        else:
            # Global fallback hit
            chain.execute.return_value = MagicMock(data=[{
                "results": [{"titulo": "Global Cascade"}],
                "total_results": 1,
                "sources_json": ["PNCP", "COMPRAS_GOV"],
                "fetched_at": fetched_at,
                "created_at": fetched_at,
                "priority": "hot",
                "access_count": 10,
                "last_accessed_at": now.isoformat(),
            }])
        return chain

    mock_table.select = mock_select

    mock_redis_cache = MagicMock()
    mock_redis_cache.get.return_value = None

    with (
        patch("supabase_client.get_supabase", return_value=mock_sb),
        patch("redis_pool.get_fallback_cache", return_value=mock_redis_cache),
        patch("cache.cascade.METRICS_CACHE_HITS", MagicMock()),
        patch("cache.cascade.METRICS_CACHE_MISSES", MagicMock()),
        patch("middleware.search_id_var", MagicMock(get=lambda x: "-")),
    ):
        result = await get_from_cache_cascade(
            user_id="cascade-trial-user",
            params=params,
        )

    assert result is not None
    assert result["cache_level"] == "global"
    assert result["results"][0]["titulo"] == "Global Cascade"


@pytest.mark.asyncio
async def test_cron_refresh_graceful_on_no_stale():
    """Cron refresh handles case when there are no stale entries."""
    from cron_jobs import refresh_stale_cache_entries

    with patch("search_cache.get_stale_entries_for_refresh", new_callable=AsyncMock, return_value=[]):
        result = await refresh_stale_cache_entries()

    assert result["status"] == "no_stale_entries"
    assert result["refreshed"] == 0


@pytest.mark.asyncio
async def test_save_to_cache_stores_params_hash_global():
    """AC3: save_to_cache stores params_hash_global alongside user cache."""
    from search_cache import save_to_cache, compute_global_hash

    params = {
        "setor_id": "vestuario",
        "ufs": ["SP"],
        "status": None,
        "modalidades": [6],
        "modo_busca": None,
        "data_inicio": "2026-02-13",
        "data_fim": "2026-02-23",
    }
    expected_global_hash = compute_global_hash(params)

    mock_sb = MagicMock()
    mock_table = MagicMock()
    mock_sb.table.return_value = mock_table

    upsert_chain = MagicMock()
    upsert_chain.execute.return_value = MagicMock(data=[])
    mock_table.upsert.return_value = upsert_chain

    with (
        patch("supabase_client.get_supabase", return_value=mock_sb),
        patch("cache.manager._track_cache_operation"),
    ):
        result = await save_to_cache(
            user_id="test-user",
            params=params,
            results=[{"titulo": "Test"}],
            sources=["PNCP"],
        )

    assert result["success"] is True

    # Verify the upsert was called with params_hash_global
    upsert_call = mock_table.upsert.call_args
    row_data = upsert_call[0][0]
    assert "params_hash_global" in row_data
    assert row_data["params_hash_global"] == expected_global_hash
