"""STORY-SEO-005: Google Search Console weekly sync job.

Fetches searchanalytics.query data from GSC API for the last 90 days,
upserts into Supabase `gsc_metrics` for the /admin/seo dashboard.

Graceful degradation: if GSC_SERVICE_ACCOUNT_JSON env var is missing,
logs a warning and returns immediately. The job is safe to register
unconditionally — it only does work when credentials are configured.
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import date, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)

GSC_SYNC_ENABLED = os.getenv("GSC_SYNC_ENABLED", "true").lower() in ("true", "1", "yes")
GSC_SITE_URL = os.getenv("GSC_SITE_URL", "sc-domain:smartlic.tech")
GSC_DAYS_BACK = int(os.getenv("GSC_DAYS_BACK", "90"))
GSC_ROW_LIMIT_PER_PAGE = 25000


def _load_credentials() -> Optional[Any]:
    """Load GSC service account credentials from env var. Returns None if unset."""
    creds_json = os.getenv("GSC_SERVICE_ACCOUNT_JSON")
    if not creds_json:
        return None
    try:
        from google.oauth2 import service_account  # type: ignore
    except ImportError:
        logger.warning("gsc_sync: google-auth not installed; skipping")
        return None
    try:
        info = json.loads(creds_json)
    except json.JSONDecodeError:
        logger.error("gsc_sync: GSC_SERVICE_ACCOUNT_JSON is not valid JSON")
        return None
    try:
        return service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
        )
    except Exception as exc:
        logger.error(f"gsc_sync: failed to build credentials: {exc}")
        return None


def _build_service(creds: Any) -> Optional[Any]:
    try:
        from googleapiclient.discovery import build  # type: ignore
    except ImportError:
        logger.warning("gsc_sync: googleapiclient not installed; skipping")
        return None
    try:
        return build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    except Exception as exc:
        logger.error(f"gsc_sync: failed to build GSC client: {exc}")
        return None


def _fetch_rows(service: Any, start_date: str, end_date: str) -> list[dict[str, Any]]:
    """Paginate searchanalytics.query up to max 10 pages (250k rows)."""
    rows: list[dict[str, Any]] = []
    start_row = 0
    max_pages = 10

    for page_idx in range(max_pages):
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["date", "query", "page", "country", "device"],
            "rowLimit": GSC_ROW_LIMIT_PER_PAGE,
            "startRow": start_row,
        }
        try:
            resp = (
                service.searchanalytics()
                .query(siteUrl=GSC_SITE_URL, body=body)
                .execute()
            )
        except Exception as exc:
            logger.error(f"gsc_sync: API error at page {page_idx}: {exc}")
            break

        page_rows = resp.get("rows", [])
        if not page_rows:
            break
        rows.extend(page_rows)
        if len(page_rows) < GSC_ROW_LIMIT_PER_PAGE:
            break
        start_row += GSC_ROW_LIMIT_PER_PAGE

    return rows


def _rows_to_upsert_records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten GSC API rows (keys.date, keys.query, ...) into table columns."""
    records: list[dict[str, Any]] = []
    for row in rows:
        keys = row.get("keys") or []
        # dimensions order: date, query, page, country, device
        if len(keys) < 5:
            continue
        records.append(
            {
                "date": keys[0],
                "query": keys[1] or "",
                "page": keys[2] or "",
                "country": keys[3] or "BRA",
                "device": keys[4] or "",
                "clicks": int(row.get("clicks", 0)),
                "impressions": int(row.get("impressions", 0)),
                "ctr": float(row.get("ctr", 0.0)),
                "position": float(row.get("position", 0.0)),
            }
        )
    return records


def _upsert_batch(supabase: Any, records: list[dict[str, Any]]) -> int:
    """Upsert a batch of records by (date, query, page, country, device). Returns upserted count."""
    if not records:
        return 0
    try:
        resp = (
            supabase.table("gsc_metrics")
            .upsert(records, on_conflict="date,query,page,country,device")
            .execute()
        )
        return len(resp.data) if resp.data else len(records)
    except Exception as exc:
        logger.error(f"gsc_sync: upsert batch failed ({len(records)} rows): {exc}")
        return 0


async def gsc_sync_job(ctx: dict[str, Any]) -> dict[str, Any]:
    """ARQ cron entry point. Safe to call at any time — no-op if credentials missing."""
    started_at = time.monotonic()
    result: dict[str, Any] = {
        "enabled": GSC_SYNC_ENABLED,
        "site_url": GSC_SITE_URL,
        "rows_fetched": 0,
        "rows_upserted": 0,
        "skipped": False,
        "duration_s": 0.0,
    }

    if not GSC_SYNC_ENABLED:
        result["skipped"] = True
        result["skip_reason"] = "GSC_SYNC_ENABLED=false"
        logger.info("gsc_sync: disabled via env, skipping")
        return result

    creds = _load_credentials()
    if creds is None:
        result["skipped"] = True
        result["skip_reason"] = "missing_credentials"
        logger.warning("gsc_sync: GSC_SERVICE_ACCOUNT_JSON not configured, skipping (set env var in Railway to enable)")
        return result

    service = _build_service(creds)
    if service is None:
        result["skipped"] = True
        result["skip_reason"] = "build_service_failed"
        return result

    try:
        from supabase_client import get_supabase  # type: ignore
    except ImportError:
        result["skipped"] = True
        result["skip_reason"] = "supabase_client_unavailable"
        logger.error("gsc_sync: supabase_client module not found")
        return result

    supabase = get_supabase(service_role=True)
    if supabase is None:
        result["skipped"] = True
        result["skip_reason"] = "supabase_unavailable"
        return result

    end_date = date.today()
    start_date = end_date - timedelta(days=GSC_DAYS_BACK)
    logger.info(f"gsc_sync: fetching {start_date.isoformat()} → {end_date.isoformat()}")

    rows = _fetch_rows(service, start_date.isoformat(), end_date.isoformat())
    result["rows_fetched"] = len(rows)

    if not rows:
        result["duration_s"] = round(time.monotonic() - started_at, 2)
        logger.info(f"gsc_sync: 0 rows (may indicate new property or no traffic)")
        return result

    records = _rows_to_upsert_records(rows)
    total_upserted = 0
    BATCH = 500
    for i in range(0, len(records), BATCH):
        total_upserted += _upsert_batch(supabase, records[i : i + BATCH])

    result["rows_upserted"] = total_upserted
    result["duration_s"] = round(time.monotonic() - started_at, 2)
    logger.info(
        f"gsc_sync: done fetched={result['rows_fetched']} upserted={total_upserted} duration={result['duration_s']}s"
    )

    try:
        from metrics import (
            smartlic_gsc_sync_duration_seconds,
            smartlic_gsc_sync_rows_upserted_total,
        )
        smartlic_gsc_sync_duration_seconds.observe(result["duration_s"])
        smartlic_gsc_sync_rows_upserted_total.inc(total_upserted)
    except Exception:
        pass

    return result
