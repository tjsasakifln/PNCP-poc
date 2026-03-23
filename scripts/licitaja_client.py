#!/usr/bin/env python3
"""
LicitaJa API client for /intel-busca pipeline.

Busca editais de licitacao via LicitaJa API v1.1.3.
Rate limited a 10 req/min (token bucket).

Usage:
    from licitaja_client import LicitaJaClient
    client = LicitaJaClient(api_key="...", verbose=True)
    results, total, status = client.search_tenders(keyword="construcao", states=["SC","PR"])
    client.close()

Requires:
    pip install httpx
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Generator

import httpx

# ============================================================
# CONSTANTS
# ============================================================

LICITAJA_BASE_URL = os.environ.get(
    "LICITAJA_BASE_URL", "https://www.licitaja.com.br/api/v1"
)
LICITAJA_API_KEY = os.environ.get("LICITAJA_API_KEY", "")
LICITAJA_ENABLED = os.environ.get("LICITAJA_ENABLED", "false").lower() == "true"
LICITAJA_RATE_LIMIT_RPM = int(os.environ.get("LICITAJA_RATE_LIMIT_RPM", "10"))
LICITAJA_TIMEOUT = int(os.environ.get("LICITAJA_TIMEOUT", "30"))

# Max items per page (API limit)
LICITAJA_MAX_ITEMS_PER_PAGE = 25

# Max pages to fetch per search (20 pages × 25 items = 500 editais)
LICITAJA_MAX_PAGES = int(os.environ.get("LICITAJA_MAX_PAGES", "20"))

# Retry backoff seconds (on 429/500/502/503/504)
RETRY_BACKOFF = [2.0, 6.0, 15.0]
MAX_RETRIES = 3

# Cache
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
LICITAJA_CACHE_FILE = str(_PROJECT_ROOT / "data" / "licitaja_cache.json")
LICITAJA_CACHE_TTL_HOURS = 24


# ============================================================
# TOKEN BUCKET RATE LIMITER
# ============================================================

class TokenBucketRateLimiter:
    """Token bucket rate limiter. Thread-safe.

    capacity=10, refill_rate=10/60 means 10 requests per minute.
    """

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, timeout: float = 120.0) -> bool:
        """Block until a token is available or timeout exceeded."""
        deadline = time.monotonic() + timeout
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self.last_refill
                self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
                self.last_refill = now

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return True

            if time.monotonic() >= deadline:
                return False

            # Wait for ~1 token to be refilled
            wait = 1.0 / self.refill_rate if self.refill_rate > 0 else 1.0
            time.sleep(min(wait, max(0.1, deadline - time.monotonic())))


# ============================================================
# LICITAJA CLIENT
# ============================================================

class LicitaJaClient:
    """HTTP client for LicitaJa API v1.1.3.

    Features:
    - Header-based auth (X-API-KEY)
    - Token bucket rate limiter (10 req/min default)
    - Retry with exponential backoff
    - Local tender cache (24h TTL)
    - Structured status tags (API, API_FAILED, API_PARTIAL, RATE_LIMITED, UNAUTHORIZED)
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        rate_limit_rpm: int | None = None,
        timeout: int | None = None,
        verbose: bool = True,
    ):
        self.api_key = api_key or LICITAJA_API_KEY
        self.base_url = (base_url or LICITAJA_BASE_URL).rstrip("/")
        self.timeout = timeout or LICITAJA_TIMEOUT
        self.verbose = verbose

        rpm = rate_limit_rpm or LICITAJA_RATE_LIMIT_RPM
        self.rate_limiter = TokenBucketRateLimiter(
            capacity=rpm,
            refill_rate=rpm / 60.0,
        )

        self.client = httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "SmartLic-IntelCollect/1.0",
                "Accept": "application/json",
                "X-API-KEY": self.api_key,
            },
        )

        # Stats
        self.stats = {
            "calls": 0,
            "success": 0,
            "failed": 0,
            "retries": 0,
            "rate_limited": 0,
            "pages_fetched": 0,
        }
        self._stats_lock = threading.Lock()
        self._print_lock = threading.Lock()

        # Tender cache
        self._cache: dict[str, Any] = {}
        self._cache_loaded = False

    def _inc_stat(self, key: str, n: int = 1) -> None:
        with self._stats_lock:
            self.stats[key] = self.stats.get(key, 0) + n

    def _log(self, msg: str) -> None:
        if self.verbose:
            with self._print_lock:
                print(msg, flush=True)

    # ── HTTP GET with rate limit + retry ──

    def _get(
        self,
        path: str,
        params: dict | None = None,
        label: str = "",
    ) -> tuple[dict | list | None, str]:
        """GET with rate limit, retry, structured status."""
        self._inc_stat("calls")
        display = label or f"{self.base_url}{path}"

        # Rate limit
        if not self.rate_limiter.acquire(timeout=120.0):
            self._inc_stat("rate_limited")
            self._log(f"  ⚠ LicitaJa rate limit timeout: {display}")
            return None, "RATE_LIMITED"

        consecutive_429 = 0

        for attempt in range(MAX_RETRIES):
            try:
                if self.verbose and attempt == 0:
                    with self._print_lock:
                        print(f"  → LicitaJa: {display}", end="", flush=True)

                resp = self.client.get(f"{self.base_url}{path}", params=params)

                if resp.status_code == 200:
                    self._inc_stat("success")
                    if self.verbose:
                        with self._print_lock:
                            print(f" ✓ ({resp.status_code})")
                    try:
                        return resp.json(), "API"
                    except (json.JSONDecodeError, Exception):
                        if attempt < MAX_RETRIES - 1:
                            self._inc_stat("retries")
                            wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                            time.sleep(wait)
                            continue
                        return None, "API_CORRUPT"

                if resp.status_code == 401:
                    self._inc_stat("failed")
                    self._log(f" ✗ 401 (chave invalida ou quota excedida)")
                    return None, "UNAUTHORIZED"

                if resp.status_code == 429:
                    consecutive_429 += 1
                    self._inc_stat("rate_limited")
                    if consecutive_429 >= 3:
                        self._log(f" ✗ 429 x3 — interrompendo")
                        return None, "RATE_LIMITED"
                    wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)] * 2
                    self._log(f" ⟳ 429, aguardando {wait:.0f}s")
                    time.sleep(wait)
                    continue

                if resp.status_code in (500, 502, 503, 504):
                    self._inc_stat("retries")
                    wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                    if self.verbose:
                        with self._print_lock:
                            print(f" ⟳ {resp.status_code}, retry {wait:.0f}s", end="", flush=True)
                    time.sleep(wait)
                    continue

                # Non-retryable
                self._inc_stat("failed")
                self._log(f" ✗ ({resp.status_code})")
                return None, "API_FAILED"

            except httpx.TimeoutException:
                self._inc_stat("retries")
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                    self._log(f" ⟳ timeout, retry {wait:.0f}s")
                    time.sleep(wait)
                    continue
                self._inc_stat("failed")
                self._log(f" ✗ timeout")
                return None, "API_FAILED"
            except httpx.HTTPError as e:
                self._inc_stat("retries")
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                    time.sleep(wait)
                    continue
                self._inc_stat("failed")
                self._log(f" ✗ {e}")
                return None, "API_FAILED"

        self._inc_stat("failed")
        return None, "API_FAILED"

    # ── Public API: search_tenders ──

    def search_tenders(
        self,
        keyword: str = "",
        states: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        value_min: int | None = None,
        value_max: int | None = None,
        page: int = 1,
        items: int = LICITAJA_MAX_ITEMS_PER_PAGE,
    ) -> tuple[list[dict], int, str]:
        """Search tenders. Returns (results, total_results, status).

        Dates in YYYY-MM-DD format (converted to YYYYmmdd for API).
        """
        params: dict[str, Any] = {
            "smartsearch": 0,  # disable LicitaJa AI expansion
            "order": 0,  # by opening date
            "page": page,
            "items": min(items, LICITAJA_MAX_ITEMS_PER_PAGE),
        }

        if keyword:
            params["keyword"] = keyword
        if states:
            params["state"] = ",".join(states)
        if date_from:
            params["opening_date_from"] = date_from.replace("-", "")
        if date_to:
            params["opening_date_to"] = date_to.replace("-", "")
        if value_min is not None:
            params["tender_value_min"] = value_min
        if value_max is not None:
            params["tender_value_max"] = value_max

        label = f"search(kw='{keyword[:30]}', st={states}, pg={page})"
        data, status = self._get("/tender/search", params=params, label=label)

        if status != "API" or data is None:
            return [], 0, status

        results = data.get("results", []) if isinstance(data, dict) else []
        total = data.get("total_results", 0) if isinstance(data, dict) else 0
        self._inc_stat("pages_fetched")
        return results, total, "API"

    # ── Public API: search_all_pages (generator) ──

    def search_all_pages(
        self,
        keyword: str = "",
        states: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        value_min: int | None = None,
        value_max: int | None = None,
        max_pages: int | None = None,
    ) -> Generator[list[dict], None, tuple[int, str]]:
        """Paginate through all results, yielding batches.

        Yields list[dict] per page. Returns (total_results, final_status).
        Respects rate limit automatically (token bucket).
        """
        _max_pages = max_pages or LICITAJA_MAX_PAGES
        page = 1
        total_results = 0
        final_status = "API"
        fetched = 0

        while page <= _max_pages:
            results, total, status = self.search_tenders(
                keyword=keyword,
                states=states,
                date_from=date_from,
                date_to=date_to,
                value_min=value_min,
                value_max=value_max,
                page=page,
            )

            if status != "API":
                final_status = status
                break

            total_results = total
            if not results:
                break

            yield results
            fetched += len(results)

            if fetched >= total_results:
                break

            page += 1

        return total_results, final_status  # type: ignore[return-value]

    # ── Public API: get_tender ──

    def get_tender(self, tender_id: str) -> tuple[dict | None, str]:
        """Get full tender details. Uses local cache (24h TTL)."""
        # Check cache
        cached = self._get_from_cache(tender_id)
        if cached is not None:
            return cached, "CACHE"

        data, status = self._get(
            f"/tender/{tender_id}",
            label=f"tender({tender_id})",
        )

        if status == "API" and data is not None:
            self._set_cache(tender_id, data)

        return data, status

    # ── Public API: health_check ──

    def health_check(self) -> str:
        """Quick health check. Returns status string."""
        try:
            params = {"keyword": "teste", "items": 1, "smartsearch": 0}
            resp = self.client.get(
                f"{self.base_url}/tender/search",
                params=params,
                timeout=10,
            )
            if resp.status_code == 200:
                return "AVAILABLE"
            if resp.status_code == 401:
                return "UNAUTHORIZED"
            if resp.status_code == 429:
                return "RATE_LIMITED"
            return "UNAVAILABLE"
        except Exception:
            return "UNAVAILABLE"

    # ── Cache helpers ──

    def _load_cache(self) -> None:
        if self._cache_loaded:
            return
        self._cache_loaded = True
        try:
            with open(LICITAJA_CACHE_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # Evict expired entries
            cutoff = time.time() - LICITAJA_CACHE_TTL_HOURS * 3600
            self._cache = {
                k: v for k, v in raw.items()
                if v.get("_cached_at", 0) > cutoff
            }
        except (FileNotFoundError, json.JSONDecodeError):
            self._cache = {}

    def _save_cache(self) -> None:
        try:
            Path(LICITAJA_CACHE_FILE).parent.mkdir(parents=True, exist_ok=True)
            with open(LICITAJA_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _get_from_cache(self, tender_id: str) -> dict | None:
        self._load_cache()
        entry = self._cache.get(tender_id)
        if entry is None:
            return None
        if entry.get("_cached_at", 0) < time.time() - LICITAJA_CACHE_TTL_HOURS * 3600:
            return None
        return entry.get("data")

    def _set_cache(self, tender_id: str, data: dict) -> None:
        self._load_cache()
        self._cache[tender_id] = {"data": data, "_cached_at": time.time()}
        self._save_cache()

    # ── Cleanup ──

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()


# ============================================================
# NORMALIZATION: LicitaJa -> Pipeline format
# ============================================================

def _parse_licitaja_date(date_str: str | None) -> str | None:
    """Convert YYYYmmdd or YYYY-MM-DD to YYYY-MM-DD."""
    if not date_str:
        return None
    date_str = date_str.strip()
    # Already ISO format
    if len(date_str) == 10 and "-" in date_str:
        return date_str
    # YYYYmmdd
    if len(date_str) == 8 and date_str.isdigit():
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    # YYYYmmddHHMMSS or similar
    if len(date_str) >= 8:
        d = date_str[:8]
        if d.isdigit():
            return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    return date_str


def _compute_status_temporal(close_date_str: str | None) -> tuple[str, int]:
    """Compute status_temporal and dias_restantes from close_date."""
    if not close_date_str:
        return "INDETERMINADO", -1

    try:
        close_date = datetime.strptime(close_date_str[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return "INDETERMINADO", -1

    now = datetime.now()
    dias = (close_date - now).days

    if dias < 0:
        return "EXPIRADO", dias
    if dias <= 14:
        return "URGENTE", dias
    if dias <= 30:
        return "PLANEJAVEL", dias
    return "IMINENTE", dias


def normalize_licitaja_record(raw: dict) -> dict:
    """Convert a LicitaJa tender record to the unified pipeline format."""
    tender_id = raw.get("tenderId", "")
    close_date_iso = _parse_licitaja_date(raw.get("close_date"))
    catalog_date_iso = _parse_licitaja_date(raw.get("catalog_date"))
    status_temporal, dias_restantes = _compute_status_temporal(close_date_iso)

    value = raw.get("value")
    try:
        valor = float(value) if value is not None else 0.0
    except (ValueError, TypeError):
        valor = 0.0

    return {
        "_id": f"LICITAJA-{tender_id}",
        "_source": "licitaja",
        "objeto": raw.get("tender_object", ""),
        "orgao": raw.get("agency", ""),
        "cnpj_orgao": "",  # LicitaJa does not provide organ CNPJ
        "uf": (raw.get("state") or "").upper()[:2],
        "municipio": raw.get("city", ""),
        "valor_estimado": valor,
        "modalidade_code": None,
        "modalidade_nome": raw.get("type", ""),
        "data_publicacao": catalog_date_iso,
        "data_abertura_proposta": close_date_iso,
        "data_encerramento_proposta": close_date_iso,
        "link_edital": raw.get("url", ""),
        "link_pncp": None,
        "status_temporal": status_temporal,
        "dias_restantes": dias_restantes,
        "ano_compra": close_date_iso[:4] if close_date_iso else "",
        "sequencial_compra": "",
        "licitaja_tender_id": tender_id,
    }


# ============================================================
# COLLECTION: Full LicitaJa pipeline for intel-collect
# ============================================================

def collect_licitaja(
    keywords_sample: list[str],
    ufs: list[str],
    date_from: str,
    date_to: str,
    value_max: int | None = None,
    api_key: str | None = None,
    verbose: bool = True,
    max_pages_per_search: int | None = None,
    elapsed_s: float = 0.0,
    pipeline_timeout_s: float = 300.0,
) -> tuple[list[dict], dict]:
    """Collect editais from LicitaJa for intel-busca pipeline.

    Args:
        keywords_sample: 2-3 keyword groups to search (each searched separately)
        ufs: State codes to filter
        date_from: YYYY-MM-DD
        date_to: YYYY-MM-DD
        value_max: Optional max tender value
        api_key: Override API key
        verbose: Print progress
        max_pages_per_search: Override max pages
        elapsed_s: Time already elapsed in pipeline (for timeout guard)
        pipeline_timeout_s: Total pipeline timeout

    Returns:
        (editais_normalized, licitaja_stats)
    """
    stats = {
        "licitaja_total_raw": 0,
        "licitaja_pages_fetched": 0,
        "licitaja_errors": 0,
        "licitaja_rate_limited": 0,
        "licitaja_after_filter": 0,
        "licitaja_unique_added": 0,
        "licitaja_status": "DISABLED",
        "licitaja_dedup_removed": 0,
    }

    # Check feature flag
    key = api_key or LICITAJA_API_KEY
    if not LICITAJA_ENABLED or not key:
        if verbose:
            reason = "LICITAJA_ENABLED=false" if not LICITAJA_ENABLED else "sem API key"
            print(f"  LicitaJa: pulado ({reason})")
        stats["licitaja_status"] = "DISABLED"
        return [], stats

    # Timeout guard: skip if pipeline is already near timeout
    remaining = pipeline_timeout_s - elapsed_s
    if remaining < 30:
        if verbose:
            print(f"  LicitaJa: pulado (tempo restante {remaining:.0f}s < 30s)")
        stats["licitaja_status"] = "TIMEOUT_SKIPPED"
        return [], stats

    client = LicitaJaClient(api_key=key, verbose=verbose)

    try:
        # Health check first
        health = client.health_check()
        if health == "UNAUTHORIZED":
            if verbose:
                print(f"  LicitaJa: chave API invalida ou quota excedida")
            stats["licitaja_status"] = "UNAUTHORIZED"
            return [], stats
        if health == "UNAVAILABLE":
            if verbose:
                print(f"  LicitaJa: API indisponivel")
            stats["licitaja_status"] = "UNAVAILABLE"
            return [], stats

        all_results: list[dict] = []
        _max_pages = max_pages_per_search or LICITAJA_MAX_PAGES

        # Search with each keyword group
        for kw_group in keywords_sample:
            if not kw_group:
                continue

            # Timeout guard per search
            if pipeline_timeout_s - elapsed_s < 15:
                if verbose:
                    print(f"  LicitaJa: interrompendo (timeout iminente)")
                stats["licitaja_status"] = "API_PARTIAL"
                break

            if verbose:
                print(f"\n  LicitaJa: buscando '{kw_group[:40]}' em {ufs}...")

            gen = client.search_all_pages(
                keyword=kw_group,
                states=ufs,
                date_from=date_from,
                date_to=date_to,
                value_max=value_max,
                max_pages=_max_pages,
            )

            try:
                for page_results in gen:
                    all_results.extend(page_results)
                    stats["licitaja_total_raw"] += len(page_results)
                    # Update elapsed estimate (each page takes ~6s due to rate limit)
                    elapsed_s += 6.5
            except StopIteration:
                pass

        stats["licitaja_pages_fetched"] = client.stats.get("pages_fetched", 0)
        stats["licitaja_errors"] = client.stats.get("failed", 0)
        stats["licitaja_rate_limited"] = client.stats.get("rate_limited", 0)

        if not all_results:
            stats["licitaja_status"] = "API" if health == "AVAILABLE" else health
            return [], stats

        # Normalize
        normalized = []
        seen_ids: set[str] = set()
        for raw in all_results:
            tid = raw.get("tenderId", "")
            if tid in seen_ids:
                continue  # intra-LicitaJa dedup
            seen_ids.add(tid)

            record = normalize_licitaja_record(raw)

            # Skip expired
            if record["status_temporal"] == "EXPIRADO":
                continue

            normalized.append(record)

        stats["licitaja_after_filter"] = len(normalized)
        stats["licitaja_unique_added"] = len(normalized)
        stats["licitaja_status"] = "API"

        if verbose:
            print(f"\n  [LicitaJa] {stats['licitaja_pages_fetched']} paginas, "
                  f"{stats['licitaja_total_raw']} brutos, "
                  f"{len(normalized)} apos filtro")

        return normalized, stats

    finally:
        client.close()


def build_keyword_groups(keywords: list[str], max_groups: int = 3, terms_per_group: int = 5) -> list[str]:
    """Build keyword search groups from full keyword list.

    Groups top keywords into 2-3 search strings for LicitaJa.
    LicitaJa searches by relevance, so fewer focused terms work better.
    """
    if not keywords:
        return []

    # Take first N keywords (assumed to be sorted by relevance)
    selected = keywords[:max_groups * terms_per_group]

    groups: list[str] = []
    for i in range(0, len(selected), terms_per_group):
        chunk = selected[i:i + terms_per_group]
        groups.append(" ".join(chunk))

    return groups[:max_groups]
