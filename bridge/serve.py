#!/usr/bin/env python3
"""Local/least-privilege HTTP entry for the compiled bridge map.

Stdlib only. Loads generated/bridge-map.json. No FastAPI, no Next, no app.
Does not log query strings or request bodies.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from bridge.generate import GENERATED_DIR, compiled_from_map_file
from bridge.pins import PINNED_SHA256
from bridge.policy import CompiledMap, resolve

DEFAULT_MAP = GENERATED_DIR / "bridge-map.json"


def security_headers(compiled: CompiledMap) -> list[tuple[str, str]]:
    return [
        ("X-Content-Type-Options", "nosniff"),
        ("Referrer-Policy", "no-referrer"),
        ("X-Robots-Tag", "noindex, nofollow"),
        ("X-Bridge-Manifest-Hash", compiled.manifesto_sha256),
        ("X-Bridge-Config-Hash", compiled.config_sha256),
        ("Cache-Control", "public, max-age=300"),
    ]


class BridgeState:
    def __init__(self, compiled: CompiledMap) -> None:
        self.compiled = compiled
        self.counts: Counter[str] = Counter()
        self.lock = threading.Lock()

    def hit(self, rule_id: str, status: int) -> None:
        with self.lock:
            self.counts[f"rule:{rule_id}"] += 1
            self.counts[f"status:{status}"] += 1

    def snapshot(self) -> dict[str, int]:
        with self.lock:
            return dict(self.counts)


def make_handler(state: BridgeState):
    compiled = state.compiled

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args: object) -> None:
            path = urlsplit(self.path).path
            sys.stderr.write("%s %s\n" % (self.command, path))

        def _handle(self) -> None:
            parts = urlsplit(self.path)
            if parts.path in {"/__bridge/health", "/__bridge/metrics"}:
                payload = {
                    "status": "ok",
                    "manifesto_sha256": compiled.manifesto_sha256,
                    "config_sha256": compiled.config_sha256,
                    "redirects": len(compiled.redirects),
                    "default_status": compiled.default_status,
                    "counts": state.snapshot(),
                }
                body = json.dumps(payload, sort_keys=True).encode("utf-8") + b"\n"
                self.send_response(200)
                for key, value in security_headers(compiled):
                    self.send_header(key, value)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(body)
                return
            decision = resolve(compiled, parts.path, parts.query, self.headers.get("Host"))
            state.hit(decision.rule_id, decision.status)
            self.send_response(decision.status)
            for key, value in security_headers(compiled):
                self.send_header(key, value)
            if decision.location:
                self.send_header("Location", decision.location)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            body = b"Gone\n"
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            self._handle()

        def do_HEAD(self) -> None:  # noqa: N802
            self._handle()

    return Handler


def serve(compiled: CompiledMap, host: str, port: int) -> ThreadingHTTPServer:
    state = BridgeState(compiled)
    httpd = ThreadingHTTPServer((host, port), make_handler(state))
    httpd.bridge_state = state  # type: ignore[attr-defined]
    return httpd


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve the compiled #2115 redirect map.")
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--metrics-file", type=Path, default=None)
    args = parser.parse_args(argv)

    compiled = compiled_from_map_file(args.map)
    if compiled.manifesto_sha256 != PINNED_SHA256:
        print(
            f"SERVE_BLOCKED manifesto hash {compiled.manifesto_sha256} != pin {PINNED_SHA256}",
            file=sys.stderr,
        )
        return 2

    httpd = serve(compiled, args.host, args.port)
    print(
        f"SERVE_OK host={args.host} port={args.port} "
        f"manifesto={compiled.manifesto_sha256} config={compiled.config_sha256} "
        f"redirects={len(compiled.redirects)}",
        flush=True,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        # SIGINT is the operator's expected clean-shutdown path.
        pass
    finally:
        snapshot = getattr(httpd, "bridge_state", None)
        counts = snapshot.snapshot() if snapshot is not None else {}
        httpd.server_close()
        if args.metrics_file:
            args.metrics_file.write_text(
                json.dumps(
                    {
                        "manifesto_sha256": compiled.manifesto_sha256,
                        "config_sha256": compiled.config_sha256,
                        "redirects": len(compiled.redirects),
                        "counts": counts,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
