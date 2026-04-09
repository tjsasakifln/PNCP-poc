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
) -> tuple[list[dict], int, int]:
    """Fetch one page of contracts. Returns (items, total_records, total_pages)."""
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
                return [], 0, 1  # No content
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
    return [], 0, 1


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
) -> dict[str, Any]:
    """Crawl all PNCP contracts in a date window.

    Args:
        data_ini: Start date YYYYMMDD (inclusive).
        data_fim: End date YYYYMMDD (inclusive). Max 365 days from data_ini.
        max_pages: Safety cap on pages fetched.

    Returns:
        Stats dict: pages_fetched, records_raw, records_normalized, upserted totals.
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
    }

    logger.info("[ContractsCrawler] Window %s->%s starting", data_ini, data_fim)
    t0 = time.monotonic()

    async with httpx.AsyncClient(headers={"Accept": "application/json"}) as client:
        page = 1
        while page <= max_pages:
            items, total_records, total_pages = await _fetch_page(client, data_ini, data_fim, page)

            if not items:
                if page == 1:
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

            if page == 1:
                logger.info(
                    "[ContractsCrawler] Window %s->%s: %d total records, %d pages",
                    data_ini, data_fim, total_records, total_pages,
                )

            if page >= min(total_pages, max_pages):
                break

            page += 1
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


async def run_full_crawl() -> dict[str, Any]:
    """Crawl last CONTRACTS_FULL_DAYS (default 730) in ≤365-day windows.

    Returns aggregated stats across all windows.
    """
    if not CONTRACTS_ENABLED:
        return {"status": "skipped", "reason": "CONTRACTS_INGESTION_ENABLED=false"}

    today = datetime.now(timezone.utc).date()
    total_stats: dict[str, Any] = {
        "status": "completed",
        "windows": [],
        "pages_fetched": 0,
        "records_raw": 0,
        "records_normalized": 0,
        "inserted": 0,
        "updated": 0,
        "unchanged": 0,
    }

    # Split into 365-day chunks from oldest to newest
    start = today - timedelta(days=CONTRACTS_FULL_DAYS)
    while start < today:
        end = min(start + timedelta(days=MAX_WINDOW_DAYS - 1), today)
        window_stats = await crawl_contracts_window(_fmt(start), _fmt(end))
        total_stats["windows"].append(window_stats)
        for key in ("pages_fetched", "records_raw", "records_normalized", "inserted", "updated", "unchanged"):
            total_stats[key] = total_stats.get(key, 0) + window_stats.get(key, 0)
        start = end + timedelta(days=1)
        if start < today:
            await asyncio.sleep(2.0)  # Pause between windows

    logger.info(
        "[ContractsCrawler] Full crawl done — windows=%d pages=%d raw=%d norm=%d ins=%d upd=%d",
        len(total_stats["windows"]),
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
    """
    if not CONTRACTS_ENABLED:
        return {"status": "skipped", "reason": "CONTRACTS_INGESTION_ENABLED=false"}

    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=CONTRACTS_INCREMENTAL_DAYS + 1)  # +1 overlap
    stats = await crawl_contracts_window(_fmt(start), _fmt(today))
    stats["status"] = "completed"
    return stats


async def run_backfill(data_ini: str, data_fim: str) -> dict[str, Any]:
    """One-time backfill for an arbitrary date range. Splits into 365-day windows."""
    from datetime import date as _date
    start = _date.fromisoformat(data_ini[:4] + "-" + data_ini[4:6] + "-" + data_ini[6:8])
    end = _date.fromisoformat(data_fim[:4] + "-" + data_fim[4:6] + "-" + data_fim[6:8])
    results = []
    cur = start
    while cur <= end:
        window_end = min(cur + timedelta(days=MAX_WINDOW_DAYS - 1), end)
        r = await crawl_contracts_window(_fmt(cur), _fmt(window_end))
        results.append(r)
        cur = window_end + timedelta(days=1)
        if cur <= end:
            await asyncio.sleep(2.0)
    return {"status": "completed", "windows": results}


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
