#!/usr/bin/env python3
"""Local/least-privilege HTTP entry for the compiled bridge map.

Stdlib only. Loads generated/bridge-map.json. No FastAPI, no Next, no app.
Does not log query strings, request bodies, raw client IP, or User-Agent.
Structured window records are a post-resolve side effect and never change
status/Location. Loopback 301s are not production first-production-301.
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
import threading
import time
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from bridge.generate import GENERATED_DIR, compiled_from_map_file
from bridge.observe import (
    RETENTION_DAYS,
    WindowRecorder,
    assert_no_pii,
    serialize_record,
    write_export,
)
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
    def __init__(
        self,
        compiled: CompiledMap,
        *,
        records_file: Path | None = None,
    ) -> None:
        self.compiled = compiled
        self.counts: Counter[str] = Counter()
        self.lock = threading.Lock()
        self.recorder = WindowRecorder(compiled.manifesto_sha256, compiled.config_sha256)
        self.records_file = records_file

    def hit(self, rule_id: str, status: int) -> None:
        with self.lock:
            self.counts[f"rule:{rule_id}"] += 1
            self.counts[f"status:{status}"] += 1

    def snapshot(self) -> dict[str, int]:
        with self.lock:
            return dict(self.counts)

    def emit(self, record: dict) -> None:
        try:
            line = serialize_record(record)
            sys.stderr.write(line + "\n")
            if self.records_file is not None:
                with self.lock:
                    with self.records_file.open("a", encoding="utf-8") as handle:
                        handle.write(line + "\n")
        except Exception:  # noqa: BLE001 — logging must not change Decision
            self.recorder.note_error()
            sys.stderr.write("OBSERVE_ERROR\n")


def make_handler(state: BridgeState):
    compiled = state.compiled

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args: object) -> None:
            # Default BaseHTTPRequestHandler includes client address. Drop it.
            del fmt, args

        def address_string(self) -> str:
            return "redacted"

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
                    "window": state.recorder.summary(),
                }
                raw = json.dumps(payload, sort_keys=True)
                assert_no_pii(raw)
                body = raw.encode("utf-8") + b"\n"
                self.send_response(200)
                for key, value in security_headers(compiled):
                    self.send_header(key, value)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(body)
                return
            started = time.perf_counter()
            try:
                decision = resolve(
                    compiled, parts.path, parts.query, self.headers.get("Host")
                )
            except Exception:  # noqa: BLE001 — fail closed, count error, no PII
                latency_ms = (time.perf_counter() - started) * 1000.0
                record = state.recorder.record_error(latency_ms=latency_ms, path=parts.path)
                state.emit(record)
                body = b"Error\n"
                self.send_response(500)
                for key, value in security_headers(compiled):
                    self.send_header(key, value)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(body)
                return
            latency_ms = (time.perf_counter() - started) * 1000.0
            try:
                record = state.recorder.record(
                    decision,
                    path=parts.path,
                    latency_ms=latency_ms,
                    query=parts.query,
                )
                state.emit(record)
            except Exception:  # noqa: BLE001 — recording must not change Decision
                state.recorder.note_error()
                sys.stderr.write("OBSERVE_ERROR\n")
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


def serve(
    compiled: CompiledMap,
    host: str,
    port: int,
    *,
    records_file: Path | None = None,
) -> ThreadingHTTPServer:
    state = BridgeState(compiled, records_file=records_file)
    httpd = ThreadingHTTPServer((host, port), make_handler(state))
    httpd.bridge_state = state  # type: ignore[attr-defined]
    return httpd


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve the compiled #2115 redirect map.")
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--metrics-file", type=Path, default=None)
    parser.add_argument("--records-file", type=Path, default=None)
    parser.add_argument("--export-file", type=Path, default=None)
    args = parser.parse_args(argv)

    compiled = compiled_from_map_file(args.map)
    if compiled.manifesto_sha256 != PINNED_SHA256:
        print(
            f"SERVE_BLOCKED manifesto hash {compiled.manifesto_sha256} != pin {PINNED_SHA256}",
            file=sys.stderr,
        )
        return 2

    httpd = serve(compiled, args.host, args.port, records_file=args.records_file)

    def _stop(_signum: int, _frame: object) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, _stop)
    print(
        f"SERVE_OK host={args.host} port={args.port} "
        f"manifesto={compiled.manifesto_sha256} config={compiled.config_sha256} "
        f"redirects={len(compiled.redirects)}",
        flush=True,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        # SIGINT/SIGTERM is the operator's expected clean-shutdown path.
        pass
    finally:
        snapshot = getattr(httpd, "bridge_state", None)
        counts = snapshot.snapshot() if snapshot is not None else {}
        export = snapshot.recorder.export() if snapshot is not None else None
        httpd.server_close()
        if args.metrics_file:
            payload = {
                "manifesto_sha256": compiled.manifesto_sha256,
                "config_sha256": compiled.config_sha256,
                "redirects": len(compiled.redirects),
                "counts": counts,
                "retention_days": RETENTION_DAYS,
                "retention_policy": "28+7 then delete; not a warehouse",
            }
            if export is not None:
                payload["window"] = export
            args.metrics_file.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        if args.export_file and export is not None:
            write_export(args.export_file, export)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
