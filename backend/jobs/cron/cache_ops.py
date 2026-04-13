"""jobs.cron.cache_ops — Cache cleanup, refresh, warmup, and coverage crons."""
import asyncio
import logging
import os
from datetime import date, timedelta

from jobs.cron.canary import _is_cb_or_connection_error

logger = logging.getLogger(__name__)

CLEANUP_INTERVAL_SECONDS = 6 * 60 * 60
CACHE_REFRESH_INTERVAL_SECONDS = 4 * 60 * 60
COVERAGE_CHECK_INTERVAL = int(os.environ.get("ENSURE_COVERAGE_INTERVAL_HOURS", "1")) * 3600

MANDATORY_WARMUP_COMBOS = [
    {"setor_id": "engenharia", "ufs": ["SP"]},
    {"setor_id": "engenharia", "ufs": ["SC", "PR", "RS"]},
    {"setor_id": "engenharia", "ufs": ["MG", "RJ", "ES"]},
    {"setor_id": "vestuario", "ufs": ["SP"]},
    {"setor_id": "medicamentos", "ufs": ["SP"]},
    {"setor_id": "informatica", "ufs": ["SP"]},
    {"setor_id": "servicos_prediais", "ufs": ["SP"]},
    {"setor_id": "software_desenvolvimento", "ufs": ["SP"]},
    {"setor_id": "software_licencas", "ufs": ["SP"]},
]

_DATE_WINDOW = lambda: {  # noqa: E731
    "data_inicial": (date.today() - timedelta(days=10)).isoformat(),
    "data_final": date.today().isoformat(),
}


async def _get_prioritized_ufs(all_ufs: list[str]) -> list[str]:
    from search_cache import get_popular_ufs_from_sessions
    from config import DEFAULT_UF_PRIORITY
    try:
        popular = await get_popular_ufs_from_sessions(days=7)
    except Exception:
        popular = []
    if not popular:
        ordered = [uf for uf in DEFAULT_UF_PRIORITY if uf in set(all_ufs)]
        return ordered + [uf for uf in all_ufs if uf not in set(ordered)]
    all_set = set(all_ufs)
    ordered = [uf for uf in popular if uf in all_set]
    return ordered + [uf for uf in all_ufs if uf not in set(ordered)]


async def refresh_stale_cache_entries() -> dict:
    from search_cache import trigger_background_revalidation, get_stale_entries_for_refresh
    from config import CACHE_REFRESH_BATCH_SIZE
    try:
        # AC4: usar CACHE_REFRESH_BATCH_SIZE da config (default 50); HOT→WARM→COLD ordering
        # é garantido por get_stale_entries_for_refresh() que retorna entradas priorizadas
        entries = await get_stale_entries_for_refresh(batch_size=CACHE_REFRESH_BATCH_SIZE)
        if not entries:
            return {"status": "no_stale_entries", "refreshed": 0}
        refreshed = 0
        failed = 0
        for entry in entries:
            try:
                search_params = entry.get("search_params", {})
                request_data = {"ufs": search_params.get("ufs", []), **_DATE_WINDOW(), "modalidades": search_params.get("modalidades")}
                if await trigger_background_revalidation(user_id=entry["user_id"], params=search_params, request_data=request_data):
                    refreshed += 1
                await asyncio.sleep(2)
            except Exception as e:
                failed += 1
                logger.debug(f"Cache refresh dispatch failed for {entry.get('params_hash', '?')[:12]}: {e}")
        logger.info("Cache refresh cycle: %d dispatched, %d failed out of %d stale entries", refreshed, failed, len(entries))
        return {"status": "completed", "refreshed": refreshed, "failed": failed, "total": len(entries)}
    except Exception as e:
        logger.error(f"Cache refresh error: {e}", exc_info=True)
        return {"status": "error", "error": str(e), "refreshed": 0}


async def warmup_top_params() -> dict:
    from search_cache import trigger_background_revalidation, get_top_popular_params
    try:
        top_params = await get_top_popular_params(limit=30)
        if not top_params:
            return {"status": "no_params", "warmed": 0}
        warmed = 0
        for params in top_params:
            try:
                request_data = {"ufs": params.get("ufs", []), **_DATE_WINDOW(), "modalidades": params.get("modalidades")}
                if await trigger_background_revalidation(user_id="00000000-0000-0000-0000-000000000000", params=params, request_data=request_data):
                    warmed += 1
                await asyncio.sleep(1)
            except Exception as e:
                logger.debug(f"Warmup dispatch failed: {e}")
        logger.info(f"Warmup: {warmed}/{len(top_params)} params enqueued")
        return {"status": "completed", "warmed": warmed, "total": len(top_params)}
    except Exception as e:
        logger.error(f"Warmup error: {e}", exc_info=True)
        return {"status": "error", "error": str(e), "warmed": 0}


async def warmup_specific_combinations(ufs: list[str], sectors: list[str]) -> dict:
    from search_cache import trigger_background_revalidation
    from config import (WARMUP_BATCH_DELAY_SECONDS, WARMUP_RATE_LIMIT_RPS, WARMUP_PNCP_DEGRADED_PAUSE_S, WARMUP_UF_BATCH_SIZE)
    prioritized_ufs = await _get_prioritized_ufs(ufs)
    dispatched = skipped = failed = paused = 0
    total = len(sectors) * len(prioritized_ufs)
    ufs_covered: set[str] = set()
    rate_interval = 1.0 / WARMUP_RATE_LIMIT_RPS if WARMUP_RATE_LIMIT_RPS > 0 else 0.5
    logger.info("CRIT-055 warmup: starting %d combinations (%d sectors x %d UFs)", total, len(sectors), len(prioritized_ufs))
    from cron_jobs import get_pncp_cron_status  # lazy — keeps @patch("cron_jobs.get_pncp_cron_status") working
    for sector_id in sectors:
        for i, uf in enumerate(prioritized_ufs):
            pncp_status = get_pncp_cron_status()
            if pncp_status.get("status") in ("degraded", "down"):
                logger.warning("CRIT-055 warmup: PNCP %s — pausing %.0fs", pncp_status["status"], WARMUP_PNCP_DEGRADED_PAUSE_S)
                paused += 1
                await asyncio.sleep(WARMUP_PNCP_DEGRADED_PAUSE_S)
            try:
                params = {"setor_id": sector_id, "ufs": [uf], "status": None, "modalidades": None, "modo_busca": None}
                request_data = {"ufs": [uf], **_DATE_WINDOW(), "modalidades": None}
                if await trigger_background_revalidation(user_id="00000000-0000-0000-0000-000000000000", params=params, request_data=request_data):
                    dispatched += 1
                    ufs_covered.add(uf)
                else:
                    skipped += 1
                await asyncio.sleep(rate_interval)
            except Exception as e:
                failed += 1
                logger.warning("CRIT-055 warmup: failed sector=%s uf=%s: %s", sector_id, uf, e)
            if (i + 1) % WARMUP_UF_BATCH_SIZE == 0 and i + 1 < len(prioritized_ufs):
                await asyncio.sleep(WARMUP_BATCH_DELAY_SECONDS)
    try:
        from metrics import WARMUP_COVERAGE_RATIO
        WARMUP_COVERAGE_RATIO.set(len(ufs_covered) / len(prioritized_ufs) if prioritized_ufs else 0)
    except Exception:
        pass
    logger.info("CRIT-055 warmup complete: %d/%d dispatched, %d failed, coverage: %d/%d UFs", dispatched, total, failed, len(ufs_covered), len(prioritized_ufs))
    return {"dispatched": dispatched, "skipped": skipped, "failed": failed, "paused": paused, "total": total, "ufs_covered": len(ufs_covered), "ufs_total": len(prioritized_ufs)}


async def _warmup_startup_and_periodic(ufs: list[str], sectors: list[str], delay_seconds: int) -> None:
    from config import WARMUP_PERIODIC_INTERVAL_HOURS
    try:
        logger.info("CRIT-055 warmup: waiting %ds before startup warm-up", delay_seconds)
        await asyncio.sleep(delay_seconds)
        result = await warmup_specific_combinations(ufs, sectors)
        logger.info("CRIT-055 warmup: startup warm-up finished: %s", result)
        interval_seconds = WARMUP_PERIODIC_INTERVAL_HOURS * 3600
        while True:
            await asyncio.sleep(interval_seconds)
            logger.info("CRIT-055 warmup: periodic re-warm starting")
            logger.info("CRIT-055 warmup: periodic re-warm finished: %s", await warmup_top_params())
    except asyncio.CancelledError:
        logger.info("CRIT-055 warmup: task cancelled (shutdown)")
    except Exception as e:
        logger.error("CRIT-055 warmup: task failed: %s", e, exc_info=True)


async def ensure_minimum_cache_coverage() -> dict:
    from search_cache import trigger_background_revalidation
    from sectors import SECTORS
    from config import ALL_BRAZILIAN_UFS, WARMUP_ENABLED
    if not WARMUP_ENABLED:
        return {"deficit": 0, "dispatched": 0, "skipped": True}
    deficit = dispatched = 0
    try:
        prioritized = await _get_prioritized_ufs(ALL_BRAZILIAN_UFS)
        top_ufs = prioritized[:5]
        all_sectors = list(SECTORS.values())
        for sector in all_sectors:
            for uf in top_ufs:
                age_hours = await _get_cache_entry_age(sector.id, uf)
                if age_hours is None or age_hours > 12:
                    deficit += 1
                    try:
                        params = {"setor_id": sector.id, "ufs": [uf], "status": None, "modalidades": None, "modo_busca": None}
                        request_data = {"ufs": [uf], **_DATE_WINDOW(), "modalidades": None}
                        if await trigger_background_revalidation(user_id="00000000-0000-0000-0000-000000000000", params=params, request_data=request_data):
                            dispatched += 1
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        logger.warning("CRIT-081: coverage revalidation failed for %s:%s: %s", sector.id, uf, e)
        logger.info("CRIT-081: coverage check complete: deficit=%d, dispatched=%d, sectors=%d, ufs=%d", deficit, dispatched, len(all_sectors), len(top_ufs))
        try:
            from metrics import WARMUP_COVERAGE_RATIO, CACHE_COVERAGE_DEFICIT
            total = len(all_sectors) * len(top_ufs)
            WARMUP_COVERAGE_RATIO.set((total - deficit) / total if total > 0 else 0)
            CACHE_COVERAGE_DEFICIT.set(deficit)  # AC8: gauge de contagem de combos faltando
        except Exception:
            pass
    except Exception as e:
        logger.error("CRIT-081: ensure_minimum_cache_coverage failed: %s", e, exc_info=True)
    return {"deficit": deficit, "dispatched": dispatched}


async def _get_cache_entry_age(sector_id: str, uf: str) -> float | None:
    try:
        from supabase_client import get_supabase, sb_execute
        from datetime import datetime, timezone
        sb = get_supabase()
        resp = await sb_execute(sb.table("search_results_cache").select("fetched_at, search_params").eq("search_params->>setor_id", sector_id).order("fetched_at", desc=True).limit(50))
        if not resp.data:
            return None
        now = datetime.now(timezone.utc)
        for row in resp.data:
            sp = row.get("search_params", {})
            if not isinstance(sp, dict) or uf not in (sp.get("ufs") or []):
                continue
            fetched_at_raw = row.get("fetched_at")
            if not fetched_at_raw:
                continue
            try:
                from datetime import datetime, timezone
                fetched_at = datetime.fromisoformat(str(fetched_at_raw).replace("Z", "+00:00"))
                if fetched_at.tzinfo is None:
                    fetched_at = fetched_at.replace(tzinfo=timezone.utc)
                return (now - fetched_at).total_seconds() / 3600
            except (ValueError, TypeError):
                continue
        return None
    except Exception as e:
        logger.debug("CRIT-081: _get_cache_entry_age error for %s:%s: %s", sector_id, uf, e)
        return None


async def _cache_cleanup_loop() -> None:
    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            from cache.local_file import cleanup_local_cache
            deleted = cleanup_local_cache()
            try:
                from filter.stats import filter_stats_tracker, discard_rate_tracker
                fs_removed = filter_stats_tracker.cleanup_old()
                dr_removed = discard_rate_tracker.cleanup_old()
                if fs_removed or dr_removed:
                    logger.info("Filter stats cleanup: %d filter entries, %d discard entries removed", fs_removed, dr_removed)
            except Exception as e:
                logger.warning("Filter stats cleanup failed: %s", e)
            logger.info("Periodic cache cleanup: deleted %d expired files", deleted)
        except asyncio.CancelledError:
            logger.info("Cache cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}", exc_info=True)
            await asyncio.sleep(60)


async def _cache_refresh_loop() -> None:
    await asyncio.sleep(60)
    while True:
        try:
            from config import CACHE_REFRESH_ENABLED
            if CACHE_REFRESH_ENABLED:
                result = await refresh_stale_cache_entries()
                logger.info(f"Cache refresh cycle: {result}")
            await asyncio.sleep(CACHE_REFRESH_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("Cache refresh task cancelled")
            break
        except Exception as e:
            logger.error(f"Cache refresh loop error: {e}", exc_info=True)
            await asyncio.sleep(60)


async def _coverage_check_loop() -> None:
    await asyncio.sleep(300)
    while True:
        try:
            result = await ensure_minimum_cache_coverage()
            logger.info("CRIT-081: coverage check result: %s", result)
        except asyncio.CancelledError:
            logger.info("CRIT-081: coverage check task cancelled")
            return
        except Exception as e:
            logger.error("CRIT-081: coverage check task error: %s", e, exc_info=True)
        try:
            await asyncio.sleep(COVERAGE_CHECK_INTERVAL)
        except asyncio.CancelledError:
            logger.info("CRIT-081: coverage check task cancelled during sleep")
            return


async def start_cache_cleanup_task() -> asyncio.Task:
    task = asyncio.create_task(_cache_cleanup_loop(), name="cache_cleanup")
    logger.info("Cache cleanup background task started (interval: 6h)")
    return task


async def start_cache_refresh_task() -> asyncio.Task:
    task = asyncio.create_task(_cache_refresh_loop(), name="cache_refresh")
    logger.info("Cache refresh background task started (interval: 4h)")
    return task


async def start_warmup_task() -> asyncio.Task:
    from config import WARMUP_ENABLED, WARMUP_UFS, WARMUP_SECTORS, WARMUP_STARTUP_DELAY_SECONDS
    if not WARMUP_ENABLED:
        logger.info("CRIT-055 warmup: disabled via WARMUP_ENABLED=false — skipping")
        return asyncio.create_task(asyncio.sleep(0), name="warmup_noop")
    task = asyncio.create_task(_warmup_startup_and_periodic(WARMUP_UFS, WARMUP_SECTORS, WARMUP_STARTUP_DELAY_SECONDS), name="cache_warmup")
    logger.info("CRIT-055 warmup: task started — delay=%ds, sectors=%s, ufs=%d total", WARMUP_STARTUP_DELAY_SECONDS, WARMUP_SECTORS, len(WARMUP_UFS))
    return task


async def start_coverage_check_task() -> asyncio.Task:
    task = asyncio.create_task(_coverage_check_loop(), name="coverage_check")
    logger.info("CRIT-081: Coverage check task started (interval: %ds, initial_delay: 300s)", COVERAGE_CHECK_INTERVAL)
    return task
