"""STORY-1.1 (EPIC-TD-2026Q2 P0): pg_cron health endpoint.

GET /v1/admin/cron-status — admin-only JSON snapshot of scheduled
Supabase pg_cron jobs. Backed by the ``public.get_cron_health()`` RPC
created in ``supabase/migrations/20260414120000_cron_job_health.sql``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from admin import require_admin
from supabase_client import get_supabase, sb_execute_direct

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/admin", tags=["admin"])


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    """Serialize datetime + numeric fields into JSON-safe primitives."""
    last_run_at = row.get("last_run_at")
    if isinstance(last_run_at, datetime):
        last_run_at = last_run_at.isoformat()

    return {
        "jobname": row.get("jobname"),
        "schedule": row.get("schedule"),
        "active": bool(row.get("active")) if row.get("active") is not None else None,
        "last_status": row.get("last_status") or "never_ran",
        "last_run_at": last_run_at,
        "runs_24h": int(row.get("runs_24h") or 0),
        "failures_24h": int(row.get("failures_24h") or 0),
        "latency_avg_ms": (
            int(row["latency_avg_ms"]) if row.get("latency_avg_ms") is not None else None
        ),
        "last_return_message": row.get("last_return_message"),
    }


@router.get("/cron-status")
async def get_cron_status(user=Depends(require_admin)) -> dict[str, Any]:
    """Return the pg_cron health snapshot.

    Calls ``public.get_cron_health()`` (SECURITY DEFINER) via the backend's
    service-role Supabase client. Response shape::

        {
            "queried_at": "2026-04-14T12:00:00+00:00",
            "jobs": [
                {
                    "jobname": "purge-old-bids",
                    "schedule": "0 7 * * *",
                    "active": true,
                    "last_status": "succeeded",
                    "last_run_at": "2026-04-14T07:00:04+00:00",
                    "runs_24h": 1,
                    "failures_24h": 0,
                    "latency_avg_ms": 120,
                    "last_return_message": null
                },
                ...
            ],
            "count": 6
        }

    On transient failure (Supabase CB open, RPC error) returns ``status=error``
    with ``jobs=[]`` so that dashboards degrade gracefully instead of 500-ing.
    """
    queried_at = datetime.now(timezone.utc).isoformat()
    try:
        sb = get_supabase()
        result = await sb_execute_direct(sb.rpc("get_cron_health"))
        rows = getattr(result, "data", None) or []
        jobs = [_normalize_row(r) for r in rows if isinstance(r, dict)]
        return {
            "status": "ok",
            "queried_at": queried_at,
            "count": len(jobs),
            "jobs": jobs,
        }
    except Exception as exc:
        logger.warning("cron-status RPC failed: %s", exc)
        return {
            "status": "error",
            "queried_at": queried_at,
            "count": 0,
            "jobs": [],
            "detail": str(exc),
        }
