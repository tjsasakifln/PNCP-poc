"""Search session registration and tracking.

TD-007: Extracted from plan_enforcement.py as part of DEBT-07 module split.
Contains register_search_session, update_search_session_status, save_search_session.
"""

import asyncio
import logging
from typing import Optional

from log_sanitizer import mask_user_id

logger = logging.getLogger(__name__)


async def register_search_session(
    user_id: str,
    sectors: list[str],
    ufs: list[str],
    data_inicial: str,
    data_final: str,
    custom_keywords: Optional[list[str]],
    search_id: Optional[str] = None,
) -> Optional[str]:
    """Register a search session BEFORE quota consumption.

    CRIT-002 AC4: Creates a session record with status='created' as the
    FIRST operation after authentication, ensuring every quota-consuming
    search has a corresponding record in the user's history.

    Returns session_id (str) on success, None on failure.
    Retry: 1 attempt after 0.3s on transient errors.
    """
    import json as _json
    from supabase_client import get_supabase, sb_execute
    from quota.plan_enforcement import _ensure_profile_exists

    sb = get_supabase()

    if not await asyncio.to_thread(_ensure_profile_exists, user_id, sb):
        logger.error(f"Cannot register session: profile missing for user {mask_user_id(user_id)}")
        return None

    # UX-351 AC1: Prevent duplicate entries — if search_id already registered, return existing
    if search_id:
        try:
            existing = await sb_execute(
                sb.table("search_sessions")
                .select("id")
                .eq("search_id", search_id)
                .eq("user_id", user_id)
                .limit(1)
            )
            if existing.data and len(existing.data) > 0:
                logger.info(f"Session already exists for search_id={search_id[:8]}***, reusing")
                return existing.data[0]["id"]
        except Exception:
            pass  # Fall through to insert

    # CRIT-029 AC1-AC3: Parameter-based dedup
    try:
        from datetime import datetime, timezone, timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        sorted_sectors = sorted(sectors)
        sorted_ufs = sorted(ufs)
        sectors_pg = "{" + ",".join(sorted_sectors) + "}"
        ufs_pg = "{" + ",".join(sorted_ufs) + "}"
        existing_params = await sb_execute(
            sb.table("search_sessions")
            .select("id, created_at")
            .eq("user_id", user_id)
            .filter("sectors", "eq", sectors_pg)
            .filter("ufs", "eq", ufs_pg)
            .eq("data_inicial", data_inicial)
            .eq("data_final", data_final)
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .limit(1)
        )
        if existing_params.data and len(existing_params.data) > 0:
            existing_id = existing_params.data[0]["id"]
            logger.info(
                f"CRIT-029: Dedup match on params for user {mask_user_id(user_id)}, "
                f"reusing session {existing_id[:8]}***"
            )
            return existing_id
    except Exception as dedup_err:
        logger.debug(f"CRIT-029: Param dedup check failed (proceeding to insert): {dedup_err}")
        pass  # Fall through to insert

    for attempt in range(2):
        try:
            data = {
                "user_id": user_id,
                "sectors": sorted(sectors),
                "ufs": sorted(ufs),
                "data_inicial": data_inicial,
                "data_final": data_final,
                "custom_keywords": custom_keywords,
                "status": "created",
                "total_raw": 0,
                "total_filtered": 0,
                "valor_total": 0.0,
            }
            if search_id:
                data["search_id"] = search_id

            result = await sb_execute(sb.table("search_sessions").insert(data))

            if not result.data or len(result.data) == 0:
                raise RuntimeError("Insert returned empty result")

            session_id = result.data[0]["id"]

            try:
                from metrics import SESSION_STATUS
                SESSION_STATUS.labels(status="created").inc()
            except Exception:
                pass

            logger.info(_json.dumps({
                "event": "search_session_status_change",
                "session_id": session_id[:8] + "***",
                "search_id": search_id or "no_id",
                "old_status": None,
                "new_status": "created",
                "pipeline_stage": None,
                "elapsed_ms": 0,
                "user_id": mask_user_id(user_id),
            }))

            return session_id
        except Exception as e:
            if attempt == 0:
                logger.warning(
                    f"Transient error registering session for user "
                    f"{mask_user_id(user_id)}, retrying: {e}"
                )
                await asyncio.sleep(0.3)
                continue
            logger.error(
                f"Failed to register search session after retry "
                f"for user {mask_user_id(user_id)}: {e}"
            )
            return None


async def update_search_session_status(
    session_id: str,
    status: Optional[str] = None,
    pipeline_stage: Optional[str] = None,
    error_message: Optional[str] = None,
    error_code: Optional[str] = None,
    raw_count: Optional[int] = None,
    response_state: Optional[str] = None,
    completed_at: Optional[str] = None,
    duration_ms: Optional[int] = None,
    total_filtered: Optional[int] = None,
    valor_total: Optional[float] = None,
    resumo_executivo: Optional[str] = None,
    destaques: Optional[list[str]] = None,
) -> None:
    """Update search session status (fire-and-forget, non-blocking).

    CRIT-002 AC6: Dynamic UPDATE — only sets non-None fields.
    Logs errors but NEVER propagates exceptions (AC24).
    Retry: 1 attempt after 0.3s on transient errors.
    """
    import json as _json
    from supabase_client import get_supabase, sb_execute

    update_data = {}
    if status is not None:
        update_data["status"] = status
    if pipeline_stage is not None:
        update_data["pipeline_stage"] = pipeline_stage
    if error_message is not None:
        update_data["error_message"] = error_message[:500]
    if error_code is not None:
        update_data["error_code"] = error_code
    if raw_count is not None:
        update_data["raw_count"] = raw_count
    if response_state is not None:
        update_data["response_state"] = response_state
    if completed_at is not None:
        update_data["completed_at"] = completed_at
    if duration_ms is not None:
        update_data["duration_ms"] = duration_ms
    if total_filtered is not None:
        update_data["total_filtered"] = total_filtered
    if valor_total is not None:
        # STORY-419: Defensive cap matching NUMERIC(18,2) on the column.
        # Even after the widening migration, a stray sum from the pipeline
        # could still overflow (e.g. corrupt upstream data). Capping here
        # is cheaper than catching SQLSTATE 22003 and retrying, and keeps
        # the update idempotent. The cap is 1 decade below the column
        # ceiling (1e16) to leave headroom for aggregations.
        _VALOR_TOTAL_CEILING = 1e15
        numeric_valor = float(valor_total)
        if numeric_valor > _VALOR_TOTAL_CEILING:
            logger.warning(
                "STORY-419: valor_total %.2f exceeds NUMERIC(18,2) ceiling; "
                "capping to %.2f for session %s***",
                numeric_valor,
                _VALOR_TOTAL_CEILING,
                session_id[:8],
            )
            numeric_valor = _VALOR_TOTAL_CEILING
        update_data["valor_total"] = numeric_valor
    if resumo_executivo is not None:
        update_data["resumo_executivo"] = resumo_executivo
    if destaques is not None:
        update_data["destaques"] = destaques

    if not update_data:
        return

    for attempt in range(2):
        try:
            sb = get_supabase()
            await sb_execute(sb.table("search_sessions").update(update_data).eq("id", session_id))

            if status:
                try:
                    from metrics import SESSION_STATUS
                    SESSION_STATUS.labels(status=status).inc()
                except Exception:
                    pass

            logger.info(_json.dumps({
                "event": "search_session_status_change",
                "session_id": session_id[:8] + "***",
                "new_status": status,
                "pipeline_stage": pipeline_stage,
                "error_code": error_code,
            }))

            return
        except Exception as e:
            if attempt == 0:
                logger.warning(
                    f"Transient error updating session {session_id[:8]}***, retrying: {e}"
                )
                await asyncio.sleep(0.3)
                continue
            logger.error(f"Failed to update session {session_id[:8]}*** after retry: {e}")


async def save_search_session(
    user_id: str,
    sectors: list[str],
    ufs: list[str],
    data_inicial: str,
    data_final: str,
    custom_keywords: Optional[list[str]],
    total_raw: int,
    total_filtered: int,
    valor_total: float,
    resumo_executivo: Optional[str],
    destaques: Optional[list[str]],
) -> Optional[str]:
    """Save search session to history. Returns session ID or None on failure.

    AC16: Implements retry (max 1) for transient DB errors. Failure to save
    session does NOT break the search request — always returns None on error.
    """
    from supabase_client import get_supabase, sb_execute
    from quota.plan_enforcement import _ensure_profile_exists

    sb = get_supabase()

    if not await asyncio.to_thread(_ensure_profile_exists, user_id, sb):
        logger.error(f"Cannot save session: profile missing for user {mask_user_id(user_id)}")
        return None

    for attempt in range(2):
        try:
            result = await sb_execute(
                sb.table("search_sessions")
                .insert({
                    "user_id": user_id,
                    "sectors": sorted(sectors),
                    "ufs": sorted(ufs),
                    "data_inicial": data_inicial,
                    "data_final": data_final,
                    "custom_keywords": custom_keywords,
                    "total_raw": total_raw,
                    "total_filtered": total_filtered,
                    "valor_total": float(valor_total),
                    "resumo_executivo": resumo_executivo,
                    "destaques": destaques,
                    "status": "completed",  # UX-431 AC3: fallback insert is always post-completion
                })
            )

            if not result.data or len(result.data) == 0:
                logger.error(f"Insert returned empty result for user {mask_user_id(user_id)}")
                raise RuntimeError("Insert returned empty result")

            session_id = result.data[0]["id"]
            logger.info(f"Saved search session {session_id[:8]}*** for user {mask_user_id(user_id)}")
            return session_id
        except Exception as e:
            if attempt == 0:
                logger.warning(f"Transient error saving session for user {mask_user_id(user_id)}, retrying: {e}")
                await asyncio.sleep(0.3)
                continue
            logger.error(f"Failed to save search session after retry for user {mask_user_id(user_id)}: {e}")
            return None
