"""CRIT-081 AC12: Tests for ensure_minimum_cache_coverage() cron function.

Verifies that:
- Déficits (age > 12h ou None) são detectados e revalidações disparadas
- Combos com age < 12h não disparam revalidação
- Flag WARMUP_ENABLED=False retorna early com skip
- Métrica CACHE_COVERAGE_DEFICIT.set() é chamada com valor correto
- WARMUP_COVERAGE_RATIO.set() é chamado corretamente
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace


def _make_sector(sector_id: str):
    """Helper: cria sector simples com apenas .id."""
    s = MagicMock()
    s.id = sector_id
    return s


def _make_sectors_dict(*ids: str) -> dict:
    return {sid: _make_sector(sid) for sid in ids}


# ===========================================================================
# AC12-1: Déficit detectado quando age > 12h → revalidação disparada
# ===========================================================================

@pytest.mark.asyncio
async def test_coverage_detects_stale_and_dispatches():
    """AC12: Combos com cache age > 12h disparam revalidação."""
    mock_sectors = _make_sectors_dict("vestuario", "alimentos")
    mock_trigger = AsyncMock(return_value=True)

    async def mock_age(sector_id, uf):
        # Todos com age > 12h → todos são déficit
        return 15.0

    with (
        patch("config.WARMUP_ENABLED", True),
        patch("config.ALL_BRAZILIAN_UFS", ["SP", "RJ", "MG", "RS", "SC"]),
        patch("sectors.SECTORS", mock_sectors),
        patch("jobs.cron.cache_ops._get_prioritized_ufs", new_callable=AsyncMock, return_value=["SP", "RJ", "MG", "RS", "SC"]),
        patch("jobs.cron.cache_ops._get_cache_entry_age", side_effect=mock_age),
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("asyncio.sleep", new_callable=AsyncMock),
        patch("metrics.WARMUP_COVERAGE_RATIO", MagicMock()),
        patch("metrics.CACHE_COVERAGE_DEFICIT", MagicMock()),
    ):
        from jobs.cron.cache_ops import ensure_minimum_cache_coverage
        result = await ensure_minimum_cache_coverage()

    # 2 setores × 5 UFs = 10 combos todos com age > 12h → 10 déficits
    assert result["deficit"] == 10
    assert result["dispatched"] == 10
    assert mock_trigger.call_count == 10


# ===========================================================================
# AC12-2: Combos com age < 12h NÃO disparam revalidação
# ===========================================================================

@pytest.mark.asyncio
async def test_coverage_no_deficit_when_fresh():
    """AC12: Combos com cache age < 12h não disparam revalidação."""
    mock_sectors = _make_sectors_dict("vestuario")
    mock_trigger = AsyncMock(return_value=True)

    async def mock_age(sector_id, uf):
        return 6.0  # Fresco: 6h < 12h

    with (
        patch("config.WARMUP_ENABLED", True),
        patch("config.ALL_BRAZILIAN_UFS", ["SP", "RJ", "MG", "RS", "SC"]),
        patch("sectors.SECTORS", mock_sectors),
        patch("jobs.cron.cache_ops._get_prioritized_ufs", new_callable=AsyncMock, return_value=["SP", "RJ", "MG", "RS", "SC"]),
        patch("jobs.cron.cache_ops._get_cache_entry_age", side_effect=mock_age),
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("metrics.WARMUP_COVERAGE_RATIO", MagicMock()),
        patch("metrics.CACHE_COVERAGE_DEFICIT", MagicMock()),
    ):
        from jobs.cron.cache_ops import ensure_minimum_cache_coverage
        result = await ensure_minimum_cache_coverage()

    assert result["deficit"] == 0
    assert result["dispatched"] == 0
    mock_trigger.assert_not_called()


# ===========================================================================
# AC12-3: Cache ausente (None) → considerar déficit
# ===========================================================================

@pytest.mark.asyncio
async def test_coverage_none_age_counts_as_deficit():
    """AC12: Quando _get_cache_entry_age retorna None → déficit."""
    mock_sectors = _make_sectors_dict("vestuario")
    mock_trigger = AsyncMock(return_value=True)

    async def mock_age(sector_id, uf):
        return None  # Sem cache algum

    with (
        patch("config.WARMUP_ENABLED", True),
        patch("config.ALL_BRAZILIAN_UFS", ["SP", "RJ", "MG", "RS", "SC"]),
        patch("sectors.SECTORS", mock_sectors),
        patch("jobs.cron.cache_ops._get_prioritized_ufs", new_callable=AsyncMock, return_value=["SP", "RJ", "MG", "RS", "SC"]),
        patch("jobs.cron.cache_ops._get_cache_entry_age", side_effect=mock_age),
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("asyncio.sleep", new_callable=AsyncMock),
        patch("metrics.WARMUP_COVERAGE_RATIO", MagicMock()),
        patch("metrics.CACHE_COVERAGE_DEFICIT", MagicMock()),
    ):
        from jobs.cron.cache_ops import ensure_minimum_cache_coverage
        result = await ensure_minimum_cache_coverage()

    # 1 setor × 5 UFs = 5 combos todos ausentes
    assert result["deficit"] == 5
    assert result["dispatched"] == 5


# ===========================================================================
# AC12-4: WARMUP_ENABLED=False → early return com skipped=True
# ===========================================================================

@pytest.mark.asyncio
async def test_coverage_skips_when_warmup_disabled():
    """AC12: WARMUP_ENABLED=False → retorna early sem tocar Supabase."""
    mock_trigger = AsyncMock(return_value=True)

    with (
        patch("config.WARMUP_ENABLED", False),
    ):
        from jobs.cron.cache_ops import ensure_minimum_cache_coverage
        result = await ensure_minimum_cache_coverage()

    assert result["skipped"] is True
    assert result["deficit"] == 0
    mock_trigger.assert_not_called()


# ===========================================================================
# AC12-5: Métrica CACHE_COVERAGE_DEFICIT.set() chamada com valor correto
# ===========================================================================

@pytest.mark.asyncio
async def test_coverage_sets_cache_coverage_deficit_metric():
    """AC12: CACHE_COVERAGE_DEFICIT gauge é atualizado com número de combos faltando."""
    mock_sectors = _make_sectors_dict("vestuario", "alimentos", "informatica")
    mock_trigger = AsyncMock(return_value=True)
    mock_deficit_gauge = MagicMock()
    mock_ratio_gauge = MagicMock()

    async def mock_age(sector_id, uf):
        # vestuario → fresco; alimentos e informatica → stale
        if sector_id == "vestuario":
            return 3.0
        return 20.0

    with (
        patch("config.WARMUP_ENABLED", True),
        patch("config.ALL_BRAZILIAN_UFS", ["SP", "RJ", "MG", "RS", "SC"]),
        patch("sectors.SECTORS", mock_sectors),
        patch("jobs.cron.cache_ops._get_prioritized_ufs", new_callable=AsyncMock, return_value=["SP", "RJ", "MG", "RS", "SC"]),
        patch("jobs.cron.cache_ops._get_cache_entry_age", side_effect=mock_age),
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("asyncio.sleep", new_callable=AsyncMock),
        patch("metrics.WARMUP_COVERAGE_RATIO", mock_ratio_gauge),
        patch("metrics.CACHE_COVERAGE_DEFICIT", mock_deficit_gauge),
    ):
        from jobs.cron.cache_ops import ensure_minimum_cache_coverage
        result = await ensure_minimum_cache_coverage()

    # 3 setores × 5 UFs = 15 total; vestuario (5) fresco, alimentos+informatica (10) stale
    expected_deficit = 10
    assert result["deficit"] == expected_deficit
    mock_deficit_gauge.set.assert_called_once_with(expected_deficit)

    # WARMUP_COVERAGE_RATIO deve ser (15-10)/15 ≈ 0.333
    ratio_arg = mock_ratio_gauge.set.call_args[0][0]
    assert abs(ratio_arg - (5 / 15)) < 0.01


# ===========================================================================
# AC12-6: Misto de fresh/stale — cobertura parcial
# ===========================================================================

@pytest.mark.asyncio
async def test_coverage_partial_deficit():
    """AC12: Mix de combos frescos e stale → déficit parcial correto."""
    mock_sectors = _make_sectors_dict("vestuario")
    mock_trigger = AsyncMock(return_value=True)
    call_count = [0]

    async def mock_age(sector_id, uf):
        call_count[0] += 1
        # SP e RJ → frescos, demais → stale
        if uf in ("SP", "RJ"):
            return 2.0
        return None  # Sem cache

    with (
        patch("config.WARMUP_ENABLED", True),
        patch("config.ALL_BRAZILIAN_UFS", ["SP", "RJ", "MG", "RS", "SC"]),
        patch("sectors.SECTORS", mock_sectors),
        patch("jobs.cron.cache_ops._get_prioritized_ufs", new_callable=AsyncMock, return_value=["SP", "RJ", "MG", "RS", "SC"]),
        patch("jobs.cron.cache_ops._get_cache_entry_age", side_effect=mock_age),
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("asyncio.sleep", new_callable=AsyncMock),
        patch("metrics.WARMUP_COVERAGE_RATIO", MagicMock()),
        patch("metrics.CACHE_COVERAGE_DEFICIT", MagicMock()),
    ):
        from jobs.cron.cache_ops import ensure_minimum_cache_coverage
        result = await ensure_minimum_cache_coverage()

    # SP, RJ frescos; MG, RS, SC faltando → 3 déficits
    assert result["deficit"] == 3
    assert result["dispatched"] == 3
    assert mock_trigger.call_count == 3
