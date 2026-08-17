"""Shared helpers for inventory/hostile/serve proof. Not a second redirect map."""

from __future__ import annotations

import http.client
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit

from bridge.generate import GENERATED_DIR
from bridge.pins import (
    FORBIDDEN_GENERIC_TARGETS,
    FORBIDDEN_TARGET_PATHS,
    PII_QUERY_KEYS,
    REDIRECT_DECISIONS,
    TARGET_HOSTNAME,
)
from bridge.policy import Decision

ROOT = Path(__file__).resolve().parents[2]
HOME_AND_GENERIC = frozenset(FORBIDDEN_GENERIC_TARGETS) | {
    "https://confenge.com.br/consultoria-b2g",
    "https://www.confenge.com.br/consultoria-b2g",
}
FORBIDDEN_LOCATION_HOSTS = frozenset(
    {
        "smartlic.tech",
        "www.smartlic.tech",
        "api.smartlic.tech",
        "www.confenge.com.br",
    }
)


def expected_action(entry: Mapping[str, object]) -> tuple[int, str | None]:
    """Pinned manifesto row → (status, Location). Oracle is the row, not a second map."""
    if entry.get("decision") in REDIRECT_DECISIONS:
        target = entry.get("target_url")
        if not isinstance(target, str) or not target:
            raise AssertionError(f"ready row missing target_url: {entry.get('legacy_url')!r}")
        return 301, target
    return 410, None


def assert_location_shape(location: str | None, status: int) -> None:
    if status == 410:
        if location is not None:
            raise AssertionError(f"410 must not emit Location, got {location!r}")
        return
    if status != 301:
        raise AssertionError(f"unexpected status {status} with location={location!r}")
    if not location:
        raise AssertionError("301 must emit Location")
    if "\r" in location or "\n" in location or "\x00" in location:
        raise AssertionError(f"CRLF/NUL in Location: {location!r}")
    if location in HOME_AND_GENERIC:
        raise AssertionError(f"generic/home Location: {location!r}")
    parts = urlsplit(location)
    if parts.scheme != "https":
        raise AssertionError(f"Location is not https: {location!r}")
    host = (parts.hostname or "").lower()
    if host != TARGET_HOSTNAME:
        raise AssertionError(f"Location host {host!r} != {TARGET_HOSTNAME}")
    if host in FORBIDDEN_LOCATION_HOSTS:
        raise AssertionError(f"forbidden Location host: {host}")
    path = parts.path or "/"
    if path in FORBIDDEN_TARGET_PATHS or path in {"", "/"}:
        raise AssertionError(f"generic Location path: {location!r}")
    if "consultoria-b2g" in path:
        raise AssertionError(f"consultoria fallback Location: {location!r}")
    if "smartlic.tech" in location.lower():
        raise AssertionError(f"legacy host leaked in Location: {location!r}")


def assert_decision_matches(
    decision: Decision,
    expected_status: int,
    expected_location: str | None,
    *,
    label: str,
) -> None:
    if decision.status != expected_status:
        raise AssertionError(
            f"{label}: status {decision.status} != {expected_status} loc={decision.location!r}"
        )
    if expected_status == 410:
        if decision.location is not None:
            raise AssertionError(f"{label}: 410 leaked Location {decision.location!r}")
        if decision.hops != 0:
            raise AssertionError(f"{label}: 410 hops={decision.hops}")
    else:
        if decision.location != expected_location:
            raise AssertionError(
                f"{label}: Location {decision.location!r} != {expected_location!r}"
            )
        if decision.hops > 1:
            raise AssertionError(f"{label}: hops {decision.hops} > 1")
    assert_location_shape(decision.location, decision.status)


def assert_no_pii(text: str | None, *, label: str) -> None:
    blob = (text or "").lower()
    for key in PII_QUERY_KEYS:
        token = f"{key}="
        if token in blob:
            raise AssertionError(f"{label}: PII key leaked ({token})")


def _stderr_chunks(proc: subprocess.Popen[str]) -> list[str]:
    chunks = getattr(proc, "_bridge_stderr_chunks", None)
    if not isinstance(chunks, list):
        return []
    return chunks


def _wait_stderr_drain(proc: subprocess.Popen[str], timeout: float = 2.0) -> None:
    done = getattr(proc, "_bridge_stderr_done", None)
    if isinstance(done, threading.Event):
        done.wait(timeout)


def launch_serve(port: int) -> subprocess.Popen[str]:
    # Serve emits one JSONL record per request on stderr. PIPE without a
    # reader deadlocks the inventory blackbox (~1256 paths). Drain it.
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "bridge.serve",
            "--map",
            str(GENERATED_DIR / "bridge-map.json"),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    chunks: list[str] = []
    done = threading.Event()

    def _drain() -> None:
        try:
            if proc.stderr is not None:
                for line in proc.stderr:
                    chunks.append(line)
        finally:
            done.set()

    thread = threading.Thread(target=_drain, name=f"serve-stderr-{port}", daemon=True)
    thread.start()
    proc._bridge_stderr_chunks = chunks  # type: ignore[attr-defined]
    proc._bridge_stderr_done = done  # type: ignore[attr-defined]
    return proc


def wait_ready(proc: subprocess.Popen[str], timeout: float = 5.0) -> str:
    deadline = time.time() + timeout
    assert proc.stdout is not None
    buf = ""
    while time.time() < deadline:
        if proc.poll() is not None:
            _wait_stderr_drain(proc, timeout=1.0)
            err = "".join(_stderr_chunks(proc))
            raise AssertionError(f"serve.py exited {proc.returncode}: {err}")
        line = proc.stdout.readline()
        buf += line
        if "SERVE_OK" in buf:
            return buf
        time.sleep(0.05)
    raise AssertionError(f"serve.py did not become ready: {buf!r}")


def stop_serve(proc: subprocess.Popen[str]) -> tuple[str, str]:
    proc.terminate()
    out = ""
    try:
        if proc.stdout is not None:
            out = proc.stdout.read() or ""
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        if proc.stdout is not None:
            out = (out or "") + (proc.stdout.read() or "")
        proc.wait(timeout=3)
    _wait_stderr_drain(proc, timeout=2.0)
    if proc.stdout is not None:
        proc.stdout.close()
    if proc.stderr is not None:
        proc.stderr.close()
    return out or "", "".join(_stderr_chunks(proc))


def http_get(
    port: int,
    path: str,
    *,
    method: str = "GET",
    host: str = "smartlic.tech",
    timeout: float = 5.0,
) -> tuple[int, str | None, dict[str, str]]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        conn.request(method, path, headers={"Host": host})
        resp = conn.getresponse()
        resp.read()
        headers = {k.lower(): v for k, v in resp.getheaders()}
        return resp.status, resp.getheader("Location"), headers
    finally:
        conn.close()


def raw_http(port: int, request: bytes, timeout: float = 5.0) -> bytes:
    with socket.create_connection(("127.0.0.1", port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(request)
        chunks: list[bytes] = []
        while True:
            try:
                chunk = sock.recv(4096)
            except socket.timeout:
                break
            if not chunk:
                break
            chunks.append(chunk)
            blob = b"".join(chunks)
            if b"\r\n\r\n" in blob:
                head, body = blob.split(b"\r\n\r\n", 1)
                length = 0
                for line in head.split(b"\r\n"):
                    if line.lower().startswith(b"content-length:"):
                        length = int(line.split(b":", 1)[1].strip() or 0)
                if len(body) >= length:
                    break
        return b"".join(chunks)


def parse_status_and_location(raw: bytes) -> tuple[int, str | None]:
    head = raw.split(b"\r\n\r\n", 1)[0].decode("iso-8859-1", errors="replace")
    lines = head.split("\r\n")
    if not lines:
        raise AssertionError(f"empty HTTP response: {raw!r}")
    status = int(lines[0].split(" ", 2)[1])
    location = None
    for line in lines[1:]:
        if line.lower().startswith("location:"):
            location = line.split(":", 1)[1].strip()
    return status, location
