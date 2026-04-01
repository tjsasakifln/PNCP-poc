"""jobs.queue.search — search_job ARQ function and persistence helpers."""
from __future__ import annotations

import json
import logging
import time

logger = logging.getLogger(__name__)


async def _persist_search_results_to_redis(search_id: str, response) -> None:
    from redis_pool import get_redis_pool
    redis = await get_redis_pool()
    if not redis:
        return
    try:
        from config import RESULTS_REDIS_TTL
        key = f"smartlic:results:{search_id}"
        data = response.model_dump(mode="json") if hasattr(response, "model_dump") else (response if isinstance(response, dict) else None)
        if data is None:
            return
        await redis.setex(key, RESULTS_REDIS_TTL, json.dumps(data, default=str))
        logger.debug(f"STORY-363: Results stored in Redis L2: {key}")
    except Exception as e:
        logger.warning(f"STORY-363: Failed to persist results to Redis L2: {e}")


async def _persist_search_results_to_supabase(search_id: str, user_id: str, response) -> None:
    try:
        from supabase_client import get_supabase, sb_execute
        from config import RESULTS_SUPABASE_TTL_HOURS
        from datetime import datetime, timezone, timedelta
        db = get_supabase()
        if not db:
            return
        data = response.model_dump(mode="json") if hasattr(response, "model_dump") else (response if isinstance(response, dict) else None)
        if data is None:
            return
        expires_at = datetime.now(timezone.utc) + timedelta(hours=RESULTS_SUPABASE_TTL_HOURS)
        await sb_execute(db.table("search_results_l3").upsert({"search_id": search_id, "user_id": user_id, "results": json.dumps(data, default=str), "expires_at": expires_at.isoformat()}, on_conflict="search_id"))
        logger.debug(f"STORY-363: Results stored in Supabase L3: {search_id}")
    except Exception as e:
        logger.warning(f"STORY-363: Failed to persist results to Supabase L3: {e}")


async def _update_search_session(search_id: str, user_id: str, response) -> None:
    try:
        from supabase_client import get_supabase, sb_execute
        from datetime import datetime, timezone
        db = get_supabase()
        if not db:
            return
        await sb_execute(db.table("search_sessions").update({"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}).eq("search_id", search_id).eq("user_id", user_id))
    except Exception as e:
        logger.debug(f"STORY-363: Session update failed (non-fatal): {e}")


async def search_job(ctx: dict, search_id: str, request_data: dict, user_data: dict, **kwargs) -> dict:
    from middleware import search_id_var, request_id_var
    search_id_var.set(search_id)
    request_id_var.set(kwargs.get("_trace_id", search_id))

    from pipeline.worker import executar_busca_completa
    from progress import get_tracker, remove_tracker
    from metrics import SEARCH_JOB_DURATION, SEARCH_QUEUE_TIME, SEARCH_TOTAL_TIME
    from datetime import datetime, timezone
    from jobs.queue.result_store import (check_cancel_flag, clear_cancel_flag, release_search_slot, persist_job_result)

    started_at = datetime.now(timezone.utc)
    start_mono = time.monotonic()

    queued_at_str = kwargs.get("_queued_at")
    if queued_at_str:
        try:
            queued_at = datetime.fromisoformat(queued_at_str)
            SEARCH_QUEUE_TIME.observe(max(0, (started_at - queued_at).total_seconds()))
        except (ValueError, TypeError):
            pass

    from config import SEARCH_JOB_TIMEOUT
    deadline_ts = time.monotonic() + SEARCH_JOB_TIMEOUT

    logger.info(json.dumps({"event": "search_job_started", "search_id": search_id, "queued_at": queued_at_str, "started_at": started_at.isoformat(), "ufs": request_data.get("ufs", []), "deadline_s": SEARCH_JOB_TIMEOUT}))

    user_id = user_data.get("id")
    if not user_id:
        logger.error(f"[Search Job] Missing user_id in user_data for {search_id}")
        return {"status": "failed", "total_results": 0, "error": "invalid_user"}

    tracker = await get_tracker(search_id)
    status = "completed"

    try:
        if await check_cancel_flag(search_id):
            return {"status": "cancelled", "total_results": 0}

        response = await executar_busca_completa(search_id=search_id, request_data=request_data, user_data=user_data, tracker=tracker, quota_pre_consumed=True, deadline_ts=deadline_ts)

        if await check_cancel_flag(search_id):
            status = "cancelled"
            await clear_cancel_flag(search_id)
            return {"status": "cancelled", "total_results": 0}

        if response:
            try:
                from config import get_feature_flag, TRIAL_PAYWALL_MAX_RESULTS
                from quota import get_trial_phase
                if get_feature_flag("TRIAL_PAYWALL_ENABLED"):
                    phase_info = get_trial_phase(user_id)
                    if phase_info["phase"] == "limited_access":
                        total_before = len(response.licitacoes)
                        if total_before > TRIAL_PAYWALL_MAX_RESULTS:
                            response.total_before_paywall = total_before
                            response.licitacoes = response.licitacoes[:TRIAL_PAYWALL_MAX_RESULTS]
                            response.paywall_applied = True
                            response.resumo.total_oportunidades = TRIAL_PAYWALL_MAX_RESULTS
            except Exception as pw_err:
                logger.warning(f"STORY-363: Paywall check failed in worker (non-fatal): {pw_err}")

        total_results = response.total_filtrado if response else 0

        if response:
            await persist_job_result(search_id, "search_result", response.model_dump())
            await _persist_search_results_to_redis(search_id, response)
            await _persist_search_results_to_supabase(search_id, user_id, response)
            await _update_search_session(search_id, user_id, response)

        tracker = await get_tracker(search_id)
        if tracker:
            await tracker.emit_search_complete(search_id, total_results)
            await remove_tracker(search_id)

        logger.info(f"[Search Job] Completed: search_id={search_id}, results={total_results}")
        await clear_cancel_flag(search_id)
        return {"status": "completed", "total_results": total_results}

    except Exception as e:
        status = "failed"
        logger.error(f"[Search Job] Failed: search_id={search_id}, error={type(e).__name__}: {e}", exc_info=True)
        tracker = await get_tracker(search_id)
        if tracker:
            await tracker.emit_error(str(e)[:300])
            await remove_tracker(search_id)
        raise

    finally:
        duration_s = time.monotonic() - start_mono
        SEARCH_JOB_DURATION.observe(duration_s)
        if queued_at_str:
            try:
                total_s = (datetime.now(timezone.utc) - datetime.fromisoformat(queued_at_str)).total_seconds()
                SEARCH_TOTAL_TIME.observe(max(0, total_s))
            except (ValueError, TypeError):
                pass
        completed_at = datetime.now(timezone.utc)
        logger.info(json.dumps({"event": "search_job_finished", "search_id": search_id, "started_at": started_at.isoformat(), "completed_at": completed_at.isoformat(), "duration_ms": int(duration_s * 1000), "status": status}))
        await clear_cancel_flag(search_id)
        await release_search_slot(user_id, search_id)
