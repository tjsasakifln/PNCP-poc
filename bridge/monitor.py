#!/usr/bin/env python3
"""Bounded daily snapshot for the #2115 window. No query PII.

Does not start observation_started_at. Loopback/fixture probes are ignored
for window start. Not an analytics product.
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bridge.generate import load_and_compile
from bridge.observe import assert_no_pii, evaluate_signals
from bridge.pins import PINNED_CONFIG_SHA256, PINNED_SHA256
from bridge.preflight import LIVE_HOSTS, observe_tls

HOLD_SAMPLE = "/blog/como-consultar-contratos-publicos-pncp"
GONE_PATHS = ("/", "/login", "/signup", "/pricing", "/webhooks", "/v1")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _head(host: str, path: str) -> dict[str, Any]:
    import http.client

    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(host, 443, timeout=15, context=ctx)
    try:
        conn.request("HEAD", path, headers={"Host": host, "User-Agent": "SmartLic-2115-monitor/1.0"})
        resp = conn.getresponse()
        resp.read()
        return {
            "host": host,
            "path": path,
            "status": int(resp.status),
            "has_location": resp.getheader("Location") is not None,
            "config_hash": resp.getheader("X-Bridge-Config-Hash") or "",
        }
    except Exception as exc:  # noqa: BLE001 — monitor must surface the class only
        return {
            "host": host,
            "path": path,
            "status": 0,
            "has_location": False,
            "config_hash": "",
            "error": type(exc).__name__,
        }
    finally:
        conn.close()


def collect_daily_snapshot(*, observation: dict[str, Any] | None = None) -> dict[str, Any]:
    compiled = load_and_compile()
    ready_hits = []
    gone_hits = []
    for host in sorted(LIVE_HOSTS):
        for rule in compiled.redirects:
            ready_hits.append(_head(host, rule.path))
        for path in GONE_PATHS + (HOLD_SAMPLE, "/not-mapped-2115-monitor"):
            gone_hits.append(_head(host, path))
    tls = {host: {"ok": observe_tls(host).ok, "sans": list(observe_tls(host).sans)} for host in sorted(LIVE_HOSTS)}
    hash_ok = all(
        (row.get("config_hash") == PINNED_CONFIG_SHA256) or row.get("status") in {0, 404}
        for row in ready_hits
    )
    signals = evaluate_signals(
        {
            "config_sha256": compiled.config_sha256,
            "counts": {
                "404": sum(1 for row in ready_hits + gone_hits if row.get("status") == 404),
                "errors": sum(1 for row in ready_hits + gone_hits if row.get("error")),
                "5xx": sum(1 for row in ready_hits + gone_hits if int(row.get("status") or 0) >= 500),
                "chain_gt1": 0,
            },
            "target_health": {"status": "UNOBSERVED"},
        },
        production_first_301=observation,
    )
    payload = {
        "ts": utc_now(),
        "manifesto_sha256": PINNED_SHA256,
        "config_sha256": PINNED_CONFIG_SHA256,
        "ready_checked": len(ready_hits),
        "gone_checked": len(gone_hits),
        "ready_301": sum(1 for row in ready_hits if row.get("status") == 301),
        "gone_410": sum(1 for row in gone_hits if row.get("status") == 410),
        "tls": {host: {"ok": tls[host]["ok"]} for host in tls},
        "hash_header_pin_ok": hash_ok,
        "signals": signals,
        "observation_started_at": (observation or {}).get("observation_started_at"),
        "first_production_301": (observation or {}).get("first_production_301") or "UNOBSERVED",
    }
    assert_no_pii(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Daily #2115 snapshot. Does not start the window.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--observation", type=Path, default=None)
    args = parser.parse_args(argv)
    observation = None
    if args.observation is not None and args.observation.is_file():
        observation = json.loads(args.observation.read_text(encoding="utf-8"))
    payload = collect_daily_snapshot(observation=observation)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    assert_no_pii(body)
    args.out.write_text(body, encoding="utf-8")
    print(
        "MONITOR_OK "
        f"ready_301={payload['ready_301']}/{payload['ready_checked']} "
        f"gone_410={payload['gone_410']}/{payload['gone_checked']} "
        f"window={payload['signals']['removal']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
