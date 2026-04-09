"""PNCP supplier contracts crawler.

Crawls ALL contracts from PNCP /v1/contratos endpoint (no supplier filter —
API ignores cnpjFornecedor server-side) and indexes them locally by ni_fornecedor
in the pncp_supplier_contracts table, enabling O(1) supplier CNPJ lookups.

This mirrors the pncp_raw_bids ingestion pattern but for the contracts side.

Modes:
  - full:        Last 730 days (two 365-day windows, PNCP max per request)
  - incremental: Last 3 days (daily cron, 3x/day)
  - backfill:    Arbitrary date range for one-time historical data load

Volume estimate: ~5,800 contracts/day × 730 days ≈ 4.2M rows, ~800MB storage.
Requires Supabase Pro tier.

Schedule:
  - Full:        06:00 UTC daily (1h after bid full crawl)
  - Incremental: 12:00, 18:00, 00:00 UTC
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

from supabase_client import get_supabase
from ingestion.config import INGESTION_UPSERT_BATCH_SIZE
from redis_pool import get_redis_pool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PNCP_CONTRACTS_URL = "https://pncp.gov.br/api/consulta/v1/contratos"
PAGE_SIZE = 50          # PNCP max tamanhoPagina for /contratos
MAX_PAGES_PER_WINDOW = 5000   # Safety cap
REQUEST_DELAY_S = 1.0   # 1 req/s — less aggressive to avoid PNCP drops
HTTP_TIMEOUT = 45       # Longer timeout for slow pages
MAX_RETRIES = 5         # More retries
RETRY_BACKOFF_S = 5.0   # Longer backoff before retry

# PNCP max date window: 365 days. We split 730-day full crawl into two windows.
MAX_WINDOW_DAYS = 365

CONTRACTS_FULL_DAYS = int(__import__("os").getenv("CONTRACTS_FULL_DAYS", "730"))
CONTRACTS_INCREMENTAL_DAYS = int(__import__("os").getenv("CONTRACTS_INCREMENTAL_DAYS", "3"))
CONTRACTS_ENABLED = __import__("os").getenv("CONTRACTS_INGESTION_ENABLED", "true").lower() in ("true", "1")

_ESFERA_LABELS = {"F": "Federal", "E": "Estadual", "M": "Municipal", "D": "Distrital"}

# ---------------------------------------------------------------------------
# Resilience — checkpoint TTL and exception
# ---------------------------------------------------------------------------

_CHECKPOINT_TTL = 7 * 24 * 3600  # 7 days: covers any reasonable retry window
_PAGE_CHECKPOINT_INTERVAL = 20   # Save page progress every N pages (1,000 records max re-fetch on restart)


class CrawlWindowError(Exception):
    """Raised when PNCP API fails all retries for a page within a window."""


# ---------------------------------------------------------------------------
# Redis checkpoint helpers (best-effort — failures are logged, never fatal)
# ---------------------------------------------------------------------------

def _ckpt_key(data_ini: str, data_fim: str) -> str:
    return f"contracts:ckpt:{data_ini}:{data_fim}"


async def _get_window_checkpoint(data_ini: str, data_fim: str) -> dict | None:
    """Return saved checkpoint dict or None if absent/unreadable."""
    try:
        redis = await get_redis_pool()
        if redis is None:
            return None
        raw = await redis.get(_ckpt_key(data_ini, data_fim))
        return json.loads(raw) if raw else None
    except Exception as exc:
        logger.debug("[ContractsCrawler] Checkpoint read error: %s", exc)
        return None


async def _save_window_checkpoint(
    data_ini: str,
    data_fim: str,
    status: str,
    last_page: int = 0,
) -> None:
    """Persist window status to Redis. Silently swallows errors."""
    try:
        redis = await get_redis_pool()
        if redis is None:
            return
        payload = json.dumps({
            "status": status,
            "last_page": last_page,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        })
        await redis.set(_ckpt_key(data_ini, data_fim), payload, ex=_CHECKPOINT_TTL)
    except Exception as exc:
        logger.debug("[ContractsCrawler] Checkpoint write error: %s", exc)


async def _save_page_progress(data_ini: str, data_fim: str, page: int) -> None:
    """Update last_page in an existing checkpoint (best-effort)."""
    try:
        redis = await get_redis_pool()
        if redis is None:
            return
        key = _ckpt_key(data_ini, data_fim)
        raw = await redis.get(key)
        existing: dict = json.loads(raw) if raw else {}
        existing["last_page"] = page
        existing["status"] = "in_progress"
        existing["saved_at"] = datetime.now(timezone.utc).isoformat()
        await redis.set(key, json.dumps(existing), ex=_CHECKPOINT_TTL)
    except Exception as exc:
        logger.debug("[ContractsCrawler] Page progress save error: %s", exc)


# ---------------------------------------------------------------------------
# Normalize a single PNCP contract item
# ---------------------------------------------------------------------------

def _digits_only(s: str | None) -> str:
    if not s:
        return ""
    return re.sub(r"\D", "", s)


def _normalize_contract(item: dict) -> dict | None:
    """Normalize a PNCP /contratos item to pncp_supplier_contracts row dict.

    Returns None if the item lacks a supplier CNPJ or control number (unusable).
    """
    numero = (item.get("numeroControlePNCP") or "").strip()
    if not numero:
        return None

    ni = _digits_only(item.get("niFornecedor"))
    if not ni or len(ni) < 11:
        return None   # Skip items without valid supplier identifier

    content_hash = hashlib.sha256(numero.encode()).hexdigest()

    orgao = item.get("orgaoEntidade") or {}
    unidade = item.get("unidadeOrgao") or {}

    data_str = (item.get("dataAssinatura") or "")[:10]
    data_assinatura = data_str if len(data_str) == 10 else None

    valor = None
    for field in ("valorGlobal", "valorInicial", "valorTotalEstimado"):
        raw = item.get(field)
        if raw is not None:
            try:
                v = float(raw)
                if v > 0:
                    valor = v
                    break
            except (ValueError, TypeError):
                pass

    objeto = (item.get("objetoContrato") or item.get("informacaoComplementar") or "").strip()
    if len(objeto) > 500:
        objeto = objeto[:497] + "..."

    return {
        "numero_controle_pncp": numero,
        "ni_fornecedor": ni,
        "nome_fornecedor": (item.get("nomeRazaoSocialFornecedor") or "")[:300] or None,
        "orgao_cnpj": _digits_only(orgao.get("cnpj")),
        "orgao_nome": (unidade.get("nomeUnidade") or orgao.get("razaoSocial") or "")[:300] or None,
        "uf": (unidade.get("ufSigla") or "")[:2] or None,
        "municipio": (unidade.get("municipioNome") or "")[:100] or None,
        "esfera": (orgao.get("esferaId") or "")[:1] or None,
        "valor_global": str(round(valor, 2)) if valor is not None else None,
        "data_assinatura": data_assinatura,
        "objeto_contrato": objeto or None,
        "content_hash": content_hash,
    }


# ---------------------------------------------------------------------------
# HTTP fetch (single page)
# ---------------------------------------------------------------------------

async def _fetch_page(
    client: httpx.AsyncClient,
    data_ini: str,
    data_fim: str,
    page: int,
) -> tuple[list[dict], int, int] | None:
    """Fetch one page of contracts.

    Returns:
        (items, total_records, total_pages) on success/no-content.
        None when all retries are exhausted due to API errors — caller must
        treat this as a hard failure, not as "no more pages".
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = await client.get(
                PNCP_CONTRACTS_URL,
                params={
                    "dataInicial": data_ini,
                    "dataFinal": data_fim,
                    "pagina": page,
                    "tamanhoPagina": PAGE_SIZE,
                },
                timeout=HTTP_TIMEOUT,
            )
            if resp.status_code == 200:
                body = resp.json()
                items = body.get("data", body) if isinstance(body, dict) else body
                total_records = body.get("totalRegistros", 0) if isinstance(body, dict) else 0
                total_pages = body.get("totalPaginas", 1) if isinstance(body, dict) else 1
                return items if isinstance(items, list) else [], total_records, total_pages
            if resp.status_code == 204:
                return [], 0, 1  # No content — legitimate end of data
            logger.warning(
                "[ContractsCrawler] HTTP %d for page %d (attempt %d/%d): %s",
                resp.status_code, page, attempt, MAX_RETRIES, resp.text[:200],
            )
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.warning(
                "[ContractsCrawler] Network error page %d attempt %d/%d: %s",
                page, attempt, MAX_RETRIES, exc,
            )
        if attempt < MAX_RETRIES:
            await asyncio.sleep(RETRY_BACKOFF_S * attempt)
    # All retries exhausted — signal failure explicitly (None ≠ empty list)
    return None


# ---------------------------------------------------------------------------
# Upsert to Supabase
# ---------------------------------------------------------------------------

def _chunk(lst: list, size: int):
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


async def _upsert_batch(rows: list[dict]) -> dict:
    """Upsert a batch of normalized contract rows via Supabase RPC.

    Pass the list directly (not json.dumps) — supabase-py serialises RPC params
    as JSON automatically. Passing a JSON string would send it as a scalar,
    causing 'cannot extract elements from a scalar' (code 22023).
    We do a json round-trip to coerce dates/Decimals to strings first.
    """
    totals = {"inserted": 0, "updated": 0, "unchanged": 0, "total": 0, "batches": 0}
    if not rows:
        return totals

    sb = get_supabase()
    for chunk in _chunk(rows, INGESTION_UPSERT_BATCH_SIZE):
        try:
            # json round-trip coerces non-serialisable types; returns list[dict]
            payload = json.loads(json.dumps(chunk, default=str, ensure_ascii=False))
            result = sb.rpc("upsert_pncp_supplier_contracts", {"p_records": payload}).execute()
            if result.data:
                counts = result.data[0] if isinstance(result.data, list) else result.data
                totals["inserted"] += counts.get("inserted", 0)
                totals["updated"] += counts.get("updated", 0)
                totals["unchanged"] += counts.get("unchanged", 0)
            totals["total"] += len(chunk)
            totals["batches"] += 1
        except Exception as exc:
            logger.error("[ContractsCrawler] Upsert error: %s", exc)
    return totals


# ---------------------------------------------------------------------------
# Crawl a single date window
# ---------------------------------------------------------------------------

async def crawl_contracts_window(
    data_ini: str,
    data_fim: str,
    *,
    max_pages: int = MAX_PAGES_PER_WINDOW,
    start_page: int = 1,
) -> dict[str, Any]:
    """Crawl all PNCP contracts in a date window.

    Args:
        data_ini: Start date YYYYMMDD (inclusive).
        data_fim: End date YYYYMMDD (inclusive). Max 365 days from data_ini.
        max_pages: Safety cap on pages fetched.
        start_page: Resume from this page (default 1). Used when restarting
            a previously interrupted crawl — already-upserted rows are
            idempotent (content_hash dedup in upsert_pncp_supplier_contracts).

    Returns:
        Stats dict: pages_fetched, records_raw, records_normalized, upserted totals.

    Raises:
        CrawlWindowError: When PNCP API exhausts all retries on any page.
            Callers should save the failure checkpoint and not treat partial
            data as a completed window.
    """
    stats: dict[str, Any] = {
        "window": f"{data_ini}->{data_fim}",
        "pages_fetched": 0,
        "records_raw": 0,
        "records_normalized": 0,
        "inserted": 0,
        "updated": 0,
        "unchanged": 0,
        "errors": 0,
        "start_page": start_page,
    }

    resumed = start_page > 1
    logger.info(
        "[ContractsCrawler] Window %s->%s %s page=%d",
        data_ini, data_fim,
        "resuming from" if resumed else "starting at",
        start_page,
    )
    t0 = time.monotonic()

    async with httpx.AsyncClient(headers={"Accept": "application/json"}) as client:
        page = start_page
        while page <= max_pages:
            result = await _fetch_page(client, data_ini, data_fim, page)

            if result is None:
                # All retries exhausted — API is failing. Raise so the caller
                # can mark the checkpoint as failed (not silently completed).
                stats["errors"] += 1
                raise CrawlWindowError(
                    f"PNCP API failed after {MAX_RETRIES} retries on page {page} "
                    f"(window {data_ini}->{data_fim})"
                )

            items, total_records, total_pages = result

            if not items:
                if page == start_page:
                    logger.info(
                        "[ContractsCrawler] Window %s->%s: no records (total=%d)",
                        data_ini, data_fim, total_records,
                    )
                break

            stats["records_raw"] += len(items)
            stats["pages_fetched"] += 1

            # Normalize and filter invalid items
            normalized = []
            for item in items:
                row = _normalize_contract(item)
                if row:
                    normalized.append(row)

            stats["records_normalized"] += len(normalized)

            # Upsert in batches
            if normalized:
                counts = await _upsert_batch(normalized)
                stats["inserted"] += counts["inserted"]
                stats["updated"] += counts["updated"]
                stats["unchanged"] += counts["unchanged"]

            if page == start_page:
                logger.info(
                    "[ContractsCrawler] Window %s->%s: %d total records, %d pages",
                    data_ini, data_fim, total_records, total_pages,
                )

            if page >= min(total_pages, max_pages):
                break

            page += 1

            # Save page progress every N pages (best-effort, allows resume on restart)
            if page % _PAGE_CHECKPOINT_INTERVAL == 0:
                await _save_page_progress(data_ini, data_fim, page)

            # Log intra-window progress every 100 pages for observability during long crawls
            if page % 100 == 0 and total_pages > 0:
                elapsed = time.monotonic() - t0
                rate = round(stats["records_raw"] / elapsed, 1) if elapsed > 0 else 0
                pct = round(page / min(total_pages, max_pages) * 100, 1)
                logger.info(
                    "[ContractsCrawler] %s->%s: page %d/%d (%.1f%%) — %.1f rec/s",
                    data_ini, data_fim, page, min(total_pages, max_pages), pct, rate,
                )

            await asyncio.sleep(REQUEST_DELAY_S)

    elapsed = round(time.monotonic() - t0, 1)
    logger.info(
        "[ContractsCrawler] Window %s->%s done in %.1fs — "
        "pages=%d raw=%d norm=%d ins=%d upd=%d",
        data_ini, data_fim, elapsed,
        stats["pages_fetched"], stats["records_raw"], stats["records_normalized"],
        stats["inserted"], stats["updated"],
    )
    stats["duration_s"] = elapsed
    return stats


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def _fmt(d: date) -> str:
    return d.strftime("%Y%m%d")


async def _check_circuit_breaker() -> bool:
    """Return True if PNCP circuit breaker is OPEN (API degraded).

    Waits 30s and rechecks once before reporting degraded — avoids
    aborting jobs due to a transient CB trip that recovers quickly.
    """
    try:
        from clients.pncp.circuit_breaker import get_circuit_breaker
        cb = get_circuit_breaker("pncp")
        if cb.is_degraded:
            logger.warning(
                "[ContractsCrawler] PNCP circuit breaker OPEN — waiting 30s before retry"
            )
            await asyncio.sleep(30)
            if cb.is_degraded:
                logger.error(
                    "[ContractsCrawler] PNCP circuit breaker still OPEN after 30s — aborting"
                )
                return True
    except Exception as exc:
        logger.debug("[ContractsCrawler] CB check error (ignored): %s", exc)
    return False


async def run_full_crawl() -> dict[str, Any]:
    """Crawl last CONTRACTS_FULL_DAYS (default 730) in ≤365-day windows.

    Resilience features:
    - Circuit breaker check before starting (aborts if PNCP is degraded)
    - Window-level checkpointing: completed windows are skipped on restart
    - Page-level resume: interrupted windows restart from last saved page
    - Adaptive inter-window delay: backs off on consecutive failures (2→60s)

    Returns aggregated stats across all windows.
    """
    if not CONTRACTS_ENABLED:
        return {"status": "skipped", "reason": "CONTRACTS_INGESTION_ENABLED=false"}

    if await _check_circuit_breaker():
        return {"status": "skipped", "reason": "pncp_circuit_breaker_open"}

    today = datetime.now(timezone.utc).date()
    total_stats: dict[str, Any] = {
        "status": "completed",
        "windows": [],
        "windows_skipped": 0,
        "windows_failed": 0,
        "pages_fetched": 0,
        "records_raw": 0,
        "records_normalized": 0,
        "inserted": 0,
        "updated": 0,
        "unchanged": 0,
    }

    consecutive_failures = 0

    # Split into 365-day chunks from oldest to newest
    start = today - timedelta(days=CONTRACTS_FULL_DAYS)
    while start < today:
        end = min(start + timedelta(days=MAX_WINDOW_DAYS - 1), today)
        data_ini, data_fim = _fmt(start), _fmt(end)

        # Check existing checkpoint — skip completed windows on restart
        ckpt = await _get_window_checkpoint(data_ini, data_fim)
        if ckpt and ckpt.get("status") == "completed":
            logger.info(
                "[ContractsCrawler] Window %s->%s already completed — skipping",
                data_ini, data_fim,
            )
            total_stats["windows_skipped"] += 1
            start = end + timedelta(days=1)
            continue

        # Resume from last saved page if window was previously interrupted
        start_page = max(1, ckpt.get("last_page", 1)) if ckpt else 1
        if start_page > 1:
            logger.info(
                "[ContractsCrawler] Resuming window %s->%s from page %d",
                data_ini, data_fim, start_page,
            )

        await _save_window_checkpoint(data_ini, data_fim, "in_progress", start_page)

        try:
            window_stats = await crawl_contracts_window(
                data_ini, data_fim, start_page=start_page
            )
            await _save_window_checkpoint(
                data_ini, data_fim, "completed", window_stats["pages_fetched"]
            )
            total_stats["windows"].append(window_stats)
            for key in ("pages_fetched", "records_raw", "records_normalized", "inserted", "updated", "unchanged"):
                total_stats[key] = total_stats.get(key, 0) + window_stats.get(key, 0)
            consecutive_failures = 0

        except CrawlWindowError as exc:
            logger.error(
                "[ContractsCrawler] Window %s->%s failed: %s",
                data_ini, data_fim, exc,
            )
            failed_page = start_page  # Checkpoint retains last known-good page
            await _save_window_checkpoint(data_ini, data_fim, "failed", failed_page)
            total_stats["windows_failed"] += 1
            consecutive_failures += 1
            if total_stats["status"] == "completed":
                total_stats["status"] = "partial"

        start = end + timedelta(days=1)
        if start < today:
            # Adaptive delay: back off exponentially on consecutive failures
            delay = min(2.0 * (2 ** consecutive_failures), 60.0)
            if delay > 2.0:
                logger.info(
                    "[ContractsCrawler] Backoff %.0fs after %d consecutive failure(s)",
                    delay, consecutive_failures,
                )
            await asyncio.sleep(delay)

    if total_stats["windows_failed"] > 0 and not total_stats["windows"]:
        total_stats["status"] = "failed"

    logger.info(
        "[ContractsCrawler] Full crawl done — status=%s windows=%d skipped=%d failed=%d "
        "pages=%d raw=%d norm=%d ins=%d upd=%d",
        total_stats["status"],
        len(total_stats["windows"]),
        total_stats["windows_skipped"],
        total_stats["windows_failed"],
        total_stats["pages_fetched"],
        total_stats["records_raw"],
        total_stats["records_normalized"],
        total_stats["inserted"],
        total_stats["updated"],
    )
    return total_stats


async def run_incremental_crawl() -> dict[str, Any]:
    """Crawl last CONTRACTS_INCREMENTAL_DAYS (default 3) for daily updates.

    +1 day overlap to catch late-arriving records.
    Circuit breaker check mirrors run_full_crawl to avoid hammering a degraded PNCP.
    """
    if not CONTRACTS_ENABLED:
        return {"status": "skipped", "reason": "CONTRACTS_INGESTION_ENABLED=false"}

    if await _check_circuit_breaker():
        return {"status": "skipped", "reason": "pncp_circuit_breaker_open"}

    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=CONTRACTS_INCREMENTAL_DAYS + 1)  # +1 overlap
    stats = await crawl_contracts_window(_fmt(start), _fmt(today))
    stats["status"] = "completed"
    return stats


async def run_backfill(data_ini: str, data_fim: str) -> dict[str, Any]:
    """One-time backfill for an arbitrary date range. Splits into 365-day windows.

    Same resilience as run_full_crawl: circuit breaker check, window-level
    checkpointing, page-level resume, adaptive inter-window delay.
    """
    from datetime import date as _date

    if await _check_circuit_breaker():
        return {"status": "skipped", "reason": "pncp_circuit_breaker_open"}

    start = _date.fromisoformat(data_ini[:4] + "-" + data_ini[4:6] + "-" + data_ini[6:8])
    end = _date.fromisoformat(data_fim[:4] + "-" + data_fim[4:6] + "-" + data_fim[6:8])

    results: list[dict] = []
    windows_skipped = 0
    windows_failed = 0
    consecutive_failures = 0

    cur = start
    while cur <= end:
        window_end = min(cur + timedelta(days=MAX_WINDOW_DAYS - 1), end)
        wi, wf = _fmt(cur), _fmt(window_end)

        ckpt = await _get_window_checkpoint(wi, wf)
        if ckpt and ckpt.get("status") == "completed":
            logger.info("[ContractsCrawler] Backfill window %s->%s already done — skipping", wi, wf)
            windows_skipped += 1
            cur = window_end + timedelta(days=1)
            continue

        start_page = max(1, ckpt.get("last_page", 1)) if ckpt else 1
        await _save_window_checkpoint(wi, wf, "in_progress", start_page)

        try:
            r = await crawl_contracts_window(wi, wf, start_page=start_page)
            await _save_window_checkpoint(wi, wf, "completed", r["pages_fetched"])
            results.append(r)
            consecutive_failures = 0
        except CrawlWindowError as exc:
            logger.error("[ContractsCrawler] Backfill window %s->%s failed: %s", wi, wf, exc)
            await _save_window_checkpoint(wi, wf, "failed", start_page)
            windows_failed += 1
            consecutive_failures += 1

        cur = window_end + timedelta(days=1)
        if cur <= end:
            delay = min(2.0 * (2 ** consecutive_failures), 60.0)
            await asyncio.sleep(delay)

    status = "completed" if windows_failed == 0 else ("failed" if not results else "partial")
    return {
        "status": status,
        "windows": results,
        "windows_skipped": windows_skipped,
        "windows_failed": windows_failed,
    }


# ---------------------------------------------------------------------------
# CLI entry point for manual backfill
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="PNCP supplier contracts crawler")
    parser.add_argument("--mode", choices=["full", "incremental", "backfill"], default="incremental")
    parser.add_argument("--ini", help="Start date YYYYMMDD (backfill mode)")
    parser.add_argument("--fim", help="End date YYYYMMDD (backfill mode)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.mode == "full":
        result = asyncio.run(run_full_crawl())
    elif args.mode == "incremental":
        result = asyncio.run(run_incremental_crawl())
    elif args.mode == "backfill":
        if not args.ini or not args.fim:
            print("--ini and --fim required for backfill mode")
            sys.exit(1)
        result = asyncio.run(run_backfill(args.ini, args.fim))

    print(json.dumps(result, indent=2, default=str))
