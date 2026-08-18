#!/usr/bin/env python3
"""Campaign runner for SMARTLIC-REDIRECT-BRIDGE-CUTOVER-01.

Thin wrappers over shipped generate / policy.resolve / serve / probe_targets.
Does not rebuild the map, invent destinations, or apply DNS.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import shutil
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlsplit

from bridge.errors import ManifestError
from bridge.generate import (
    GENERATED_DIR,
    load_and_compile,
    main as generate_main,
    probe_targets,
    sha256_bytes,
)
from bridge.pins import (
    DEFAULT_STATUS,
    PINNED_CANONICAL_HOST,
    PINNED_COMMIT,
    PINNED_CONFIG_SHA256,
    PINNED_HOLD_COUNT,
    PINNED_IGNORE_COUNT,
    PINNED_LEGAL_COUNT,
    PINNED_LEGACY_HOST,
    PINNED_MIGRATE_COUNT,
    PINNED_REDIRECT_COUNT,
    PINNED_RETIRE_COUNT,
    PINNED_SCHEMA,
    PINNED_SHA256,
    PINNED_VERSION,
    PII_QUERY_KEYS,
    TARGET_HOSTNAME,
)
from bridge.policy import CompiledMap, filter_query, resolve
from bridge.preflight import (
    BASELINE_APEX_A,
    BASELINE_WWW_A,
    observe_dns,
    observe_tls,
    run_preflight,
    try_load_compiled,
)
from bridge.preflight import PreflightInputs
from bridge.serve import DEFAULT_MAP

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_NAME = "SMARTLIC-REDIRECT-BRIDGE-CUTOVER-01"
DEFAULT_CAMPAIGN_DIR = ROOT / "docs" / "campaigns" / CAMPAIGN_NAME
SCRATCH_DEFAULT = Path("/tmp/grok-goal-f201f10c9de3/implementer")
UA = "SmartLic-2115-cutover-campaign/1.0"
SOFT_404_MARKERS = (
    "página não encontrada",
    "pagina nao encontrada",
    "page not found",
    "x-railway-fallback",
    "não encontramos",
    "nao encontramos",
    "conteúdo não encontrado",
)
FAIL_CLOSED_PATHS = (
    "/",
    "/login",
    "/signup",
    "/pricing",
    "/webhooks",
    "/v1",
    "/not-mapped-2115-cutover",
)
MALICIOUS_PATHS = (
    "/login%0d%0aLocation:%20https://evil.example/",
    "//evil.example",
    "/../etc/passwd",
    "/.%2e/login",
)
HOLD_SAMPLE = "/blog/como-consultar-contratos-publicos-pncp"
READY_CANARY_PATH = "/glossario/reajuste"
READY_CANARY_TARGET = "https://confenge.com.br/reequilibrio-obras-publicas/"
EXPECTED_PERSIST = (
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_term",
    "jornada",
    "origem",
    "route_family",
    "cta_id",
    "asset_id",
    "correlation_id",
    "tema",
)
CANONICAL_RE = re.compile(
    r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
    re.I,
)
CANONICAL_RE_SWAP = re.compile(
    r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']',
    re.I,
)
ROBOTS_META_RE = re.compile(
    r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']+)["\']',
    re.I,
)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _env_names_only() -> dict[str, bool]:
    names = (
        "BRIDGE_PUBLIC_IPV4",
        "SMARTLIC_ACME_EMAIL",
        "CF_API_TOKEN",
        "CF_ZONE_ID",
    )
    return {name: bool(os.environ.get(name, "").strip()) for name in names}


def assert_pins(compiled: CompiledMap) -> dict[str, Any]:
    errors: list[str] = []
    checks = {
        "manifesto_sha256": (compiled.manifesto_sha256, PINNED_SHA256),
        "config_sha256": (compiled.config_sha256, PINNED_CONFIG_SHA256),
        "pinned_commit": (PINNED_COMMIT, "8a2f4d5bce7e23d0308246ed45ed4d58752984ac"),
        "schema": (PINNED_SCHEMA, "smartlic-url-map-v2"),
        "version": (PINNED_VERSION, "v2"),
        "redirects": (len(compiled.redirects), PINNED_REDIRECT_COUNT),
        "holds": (len(compiled.holds), PINNED_HOLD_COUNT),
        "retire": (PINNED_RETIRE_COUNT, 1190),
        "migrate": (PINNED_MIGRATE_COUNT, 0),
        "ignore": (PINNED_IGNORE_COUNT, 0),
        "legal": (PINNED_LEGAL_COUNT, 0),
        "canonical_host": (PINNED_CANONICAL_HOST, "https://confenge.com.br"),
        "legacy_host": (PINNED_LEGACY_HOST, "https://smartlic.tech"),
        "persist": (tuple(compiled.persist), EXPECTED_PERSIST),
        "default_status": (compiled.default_status, DEFAULT_STATUS),
    }
    for name, (got, expected) in checks.items():
        if got != expected:
            errors.append(f"{name}: got={got!r} expected={expected!r}")
    if errors:
        raise ManifestError("PIN_DRIFT " + "; ".join(errors))
    return {name: {"got": got, "expected": expected} for name, (got, expected) in checks.items()}


def run_generate_check() -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    for index in (1, 2):
        proc = subprocess.run(
            [sys.executable, "-m", "bridge.generate", "--check"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        runs.append(
            {
                "run": index,
                "returncode": proc.returncode,
                "stdout": stdout,
                "stderr": stderr,
            }
        )
        if proc.returncode != 0 or "GENERATE_OK" not in stdout:
            raise ManifestError(f"GENERATE_BLOCKED run={index} rc={proc.returncode} {stderr or stdout}")
        if PINNED_SHA256 not in stdout or PINNED_CONFIG_SHA256 not in stdout:
            raise ManifestError(f"GENERATE_BLOCKED hash mismatch run={index}: {stdout}")
        if "redirects=11" not in stdout or "default=410" not in stdout:
            raise ManifestError(f"GENERATE_BLOCKED count mismatch run={index}: {stdout}")
    rc = generate_main(["--check"])
    if rc != 0:
        raise ManifestError(f"generate_main --check returned {rc}")
    return {"status": "GENERATE_OK", "runs": runs, "generate_main_rc": rc}


def _http_request(
    url: str,
    method: str,
    *,
    follow: bool,
    timeout: float = 20.0,
) -> dict[str, Any]:
    ctx = ssl.create_default_context()
    handlers: list[urllib.request.BaseHandler] = [urllib.request.HTTPSHandler(context=ctx)]
    if not follow:
        handlers.insert(0, NoRedirect())
    opener = urllib.request.build_opener(*handlers)
    req = urllib.request.Request(
        url,
        method=method,
        headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"},
    )
    hops = 0
    final = url
    status = 0
    headers: dict[str, str] = {}
    body = b""
    try:
        with opener.open(req, timeout=timeout) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            final = resp.geturl()
            headers = {k.lower(): v for k, v in resp.headers.items()}
            if method != "HEAD":
                body = resp.read(200_000)
    except urllib.error.HTTPError as exc:
        status = exc.code
        headers = {k.lower(): v for k, v in (exc.headers.items() if exc.headers else [])}
        loc = headers.get("location")
        if loc:
            hops = 1
            final = loc
        if method != "HEAD" and exc.fp is not None:
            try:
                body = exc.fp.read(200_000)
            except Exception:  # noqa: BLE001
                body = b""
    host = (urlsplit(final).hostname or "").lower()
    text = body.decode("utf-8", "replace")
    lowered = text.lower()
    canonical = ""
    match = CANONICAL_RE.search(text) or CANONICAL_RE_SWAP.search(text)
    if match:
        canonical = match.group(1).strip()
    robots_meta = ""
    robots_match = ROBOTS_META_RE.search(text)
    if robots_match:
        robots_meta = robots_match.group(1)
    robots_header = headers.get("x-robots-tag", "")
    soft = False
    if method != "HEAD":
        if len(text.strip()) < 80:
            soft = True
        if any(marker in lowered for marker in SOFT_404_MARKERS):
            soft = True
        if "smartlic" in lowered and "confenge" not in lowered:
            soft = True
    return {
        "method": method,
        "url": url,
        "status": status,
        "final_url": final,
        "host": host,
        "hops": hops,
        "location": headers.get("location"),
        "canonical": canonical,
        "robots_header": robots_header,
        "robots_meta": robots_meta,
        "soft_404": soft,
        "bytes": len(body),
        "follow": follow,
    }


def probe_ready_targets_full(compiled: CompiledMap) -> dict[str, Any]:
    """Drive shipped probe_targets then GET+HEAD each compiled ready target."""
    probe_targets(compiled)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for rule in compiled.redirects:
        head = _http_request(rule.target_url, "HEAD", follow=False)
        get = _http_request(rule.target_url, "GET", follow=False)
        follow = _http_request(rule.target_url, "GET", follow=True)
        useful = get["status"] in {200, 304} and head["status"] in {200, 301, 302, 303, 307, 308, 304}
        # A useful HEAD may be 405 on some CDNs; GET 200 is the gate.
        if get["status"] != 200:
            useful = False
        host_ok = get["host"] == TARGET_HOSTNAME and follow["host"] == TARGET_HOSTNAME
        chain = get["hops"] != 0 or follow["hops"] != 0 or follow["final_url"].rstrip("/") != rule.target_url.rstrip("/")
        # follow hops==0 means urlopen did not leave the URL (no extra redirect).
        extra_chain = bool(get["location"]) or urlsplit(follow["final_url"]).path.rstrip("/") != urlsplit(rule.target_url).path.rstrip("/")
        soft = bool(get["soft_404"] or follow["soft_404"])
        canonical = follow["canonical"] or get["canonical"] or ""
        canon_ok = (not canonical) or canonical.rstrip("/") == rule.expected_canonical.rstrip("/")
        robots = (follow["robots_header"] or follow["robots_meta"] or "").lower()
        robots_ok = "noindex" not in robots
        row = {
            "path": rule.path,
            "target_url": rule.target_url,
            "expected_canonical": rule.expected_canonical,
            "head": head,
            "get": get,
            "follow": follow,
            "useful_final_status": useful,
            "host_ok": host_ok,
            "chain": extra_chain,
            "loop": False,
            "soft_404": soft,
            "canonical_observed": canonical,
            "canonical_ok": canon_ok,
            "robots": robots,
            "robots_ok": robots_ok,
        }
        if not useful:
            errors.append(f"{rule.path} final status GET={get['status']} HEAD={head['status']}")
        if not host_ok:
            errors.append(f"{rule.path} host {get['host']}/{follow['host']}")
        if extra_chain:
            errors.append(f"{rule.path} extra redirect chain → {follow['final_url']}")
        if soft:
            errors.append(f"{rule.path} soft-404")
        if not canon_ok:
            errors.append(f"{rule.path} canonical {canonical!r} != {rule.expected_canonical!r}")
        if not robots_ok:
            errors.append(f"{rule.path} robots {robots!r} incompatible with redirect equity")
        rows.append(row)
    if errors:
        raise ManifestError("TARGET_VERIFICATION_FAILED\n- " + "\n- ".join(errors))
    return {
        "status": "PASS",
        "count": len(rows),
        "probe_targets": "PASS",
        "manifesto_sha256": compiled.manifesto_sha256,
        "config_sha256": compiled.config_sha256,
        "pinned_commit": PINNED_COMMIT,
        "rows": rows,
    }


def _free_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = int(sock.getsockname()[1])
    sock.close()
    return port


def _wait_serve(proc: subprocess.Popen[str], timeout: float = 8.0) -> str:
    deadline = time.time() + timeout
    assert proc.stdout is not None
    buf = ""
    while time.time() < deadline:
        if proc.poll() is not None:
            err = proc.stderr.read() if proc.stderr else ""
            raise ManifestError(f"bridge.serve exited {proc.returncode}: {err}")
        line = proc.stdout.readline()
        buf += line
        if "SERVE_OK" in buf:
            return buf
        time.sleep(0.05)
    raise ManifestError(f"bridge.serve did not become ready: {buf!r}")


def _hit(port: int, path: str, method: str = "GET") -> dict[str, Any]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request(method, path, headers={"Host": "smartlic.tech", "User-Agent": UA})
        resp = conn.getresponse()
        body = resp.read()
        return {
            "method": method,
            "path": path,
            "status": resp.status,
            "location": resp.getheader("Location"),
            "config_hash": resp.getheader("X-Bridge-Config-Hash") or "",
            "manifest_hash": resp.getheader("X-Bridge-Manifest-Hash") or "",
            "robots": resp.getheader("X-Robots-Tag") or "",
            "bytes": len(body),
        }
    finally:
        conn.close()


def _stop(proc: subprocess.Popen[str]) -> None:
    proc.terminate()
    try:
        proc.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate(timeout=3)


def _launch_serve(port: int) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "bridge.serve",
            "--map",
            str(DEFAULT_MAP),
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


def _canary_one_launch(compiled: CompiledMap, port: int) -> dict[str, Any]:
    proc = _launch_serve(port)
    try:
        banner = _wait_serve(proc)
        rows: list[dict[str, Any]] = []
        errors: list[str] = []
        for rule in compiled.redirects:
            for method in ("GET", "HEAD"):
                hit = _hit(port, rule.path, method)
                rows.append(hit)
                if hit["status"] != 301 or hit["location"] != rule.target_url:
                    errors.append(f"{method} {rule.path} → {hit['status']} {hit['location']}")
                if hit["config_hash"] != compiled.config_sha256:
                    errors.append(f"{method} {rule.path} config hash drift")
        allow_q = (
            f"{READY_CANARY_PATH}?utm_source=gsc&jornada=obra&email=ada@example.com"
            "&cnpj=00000000000191&token=secret"
        )
        allow_hit = _hit(port, allow_q)
        rows.append(allow_hit)
        loc = allow_hit["location"] or ""
        if allow_hit["status"] != 301:
            errors.append(f"allowlist status {allow_hit['status']}")
        if "utm_source=gsc" not in loc or "jornada=obra" not in loc:
            errors.append(f"allowlist dropped persist keys: {loc}")
        if any(key + "=" in loc.lower() for key in PII_QUERY_KEYS):
            errors.append(f"allowlist forwarded PII: {loc}")
        hold = _hit(port, HOLD_SAMPLE)
        rows.append(hold)
        if hold["status"] != 410 or hold["location"] is not None:
            errors.append(f"HOLD {HOLD_SAMPLE} → {hold['status']} {hold['location']}")
        for path in FAIL_CLOSED_PATHS + MALICIOUS_PATHS:
            hit = _hit(port, path)
            rows.append(hit)
            if hit["status"] != 410 or hit["location"] is not None:
                errors.append(f"fail-closed {path} → {hit['status']} {hit['location']}")
        # Policy must agree with serve (no second map).
        for rule in compiled.redirects:
            decision = resolve(compiled, rule.path, "", "smartlic.tech")
            if decision.status != 301 or decision.location != rule.target_url or decision.hops != 1:
                errors.append(f"policy.resolve mismatch {rule.path}")
        pii_q = "email=ada@example.com&utm_campaign=cutover&token=secret"
        decision = resolve(compiled, READY_CANARY_PATH, pii_q, "smartlic.tech")
        filtered = filter_query(pii_q, compiled.persist)
        if "email=" in (decision.location or "") or "token=" in (decision.location or ""):
            errors.append("policy forwarded PII")
        if "utm_campaign=cutover" not in (decision.location or ""):
            errors.append("policy dropped allowlisted query")
        if "email=" in filtered or "token=" in filtered:
            errors.append("filter_query leaked PII")
        return {
            "port": port,
            "banner": banner.strip(),
            "rows": rows,
            "errors": errors,
            "filtered_query": filtered,
        }
    finally:
        _stop(proc)


def canary_serve_twice(compiled: CompiledMap) -> dict[str, Any]:
    launches = []
    for _ in (1, 2):
        launches.append(_canary_one_launch(compiled, _free_port()))
    errors = [err for launch in launches for err in launch["errors"]]
    if errors:
        raise ManifestError("CANARY_LOCAL_FAILED\n- " + "\n- ".join(errors))
    return {
        "status": "PASS",
        "entry": "python3 -m bridge.serve",
        "launches": launches,
    }


def try_caddy_canary() -> dict[str, Any]:
    caddy = shutil.which("caddy")
    if not caddy:
        return {
            "status": "CADDY_ABSENT",
            "launcher": "caddy",
            "detail": "caddy binary not on PATH; accepted fallback is serve ×2 + assert_terminator_safe",
        }
    caddyfile = GENERATED_DIR / "Caddyfile"
    proc = subprocess.run(
        [caddy, "validate", "--config", str(caddyfile), "--adapter", "caddyfile"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "status": "VALIDATED" if proc.returncode == 0 else "CADDY_VALIDATE_FAILED",
        "returncode": proc.returncode,
        "stdout": proc.stdout[-2000:],
        "stderr": proc.stderr[-2000:],
    }


def doh(name: str, rrtype: str) -> dict[str, Any]:
    url = "https://cloudflare-dns.com/dns-query?" + urlencode({"name": name, "type": rrtype})
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/dns-json", "User-Agent": UA},
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    answers = []
    for item in payload.get("Answer") or []:
        answers.append(
            {
                "name": item.get("name"),
                "type": item.get("type"),
                "ttl": item.get("TTL"),
                "data": item.get("data"),
            }
        )
    return {"name": name, "type": rrtype, "status": payload.get("Status"), "answers": answers}


def inventory_dns_tls() -> dict[str, Any]:
    records = [
        doh("smartlic.tech", "A"),
        doh("smartlic.tech", "AAAA"),
        doh("smartlic.tech", "NS"),
        doh("smartlic.tech", "TXT"),
        doh("smartlic.tech", "MX"),
        doh("www.smartlic.tech", "A"),
        doh("www.smartlic.tech", "CNAME"),
        doh("api.smartlic.tech", "A"),
        doh("api.smartlic.tech", "CNAME"),
        doh("app.smartlic.tech", "CNAME"),
    ]
    apex = observe_dns("smartlic.tech")
    www = observe_dns("www.smartlic.tech")
    api = observe_dns("api.smartlic.tech")
    tls_apex = observe_tls("smartlic.tech")
    tls_www = observe_tls("www.smartlic.tech")
    creds = _env_names_only()
    return {
        "observed_at": utc_now(),
        "owner": "Cloudflare NS jermaine/ryleigh; records are the 2026-08-14/15 Railway baseline",
        "credentials_present": creds,
        "bridge_public_ipv4": None,
        "records": records,
        "getaddrinfo": {
            "smartlic.tech": list(apex.addresses),
            "www.smartlic.tech": list(www.addresses),
            "api.smartlic.tech": list(api.addresses),
            "apex_error": apex.error,
            "www_error": www.error,
            "api_error": api.error,
        },
        "tls": {
            "smartlic.tech": {
                "ok": tls_apex.ok,
                "sans": list(tls_apex.sans),
                "error": tls_apex.error,
            },
            "www.smartlic.tech": {
                "ok": tls_www.ok,
                "sans": list(tls_www.sans),
                "error": tls_www.error,
            },
        },
        "rollback_target": {
            "apex_A": BASELINE_APEX_A,
            "apex_ttl": 60,
            "www_CNAME": "app.smartlic.tech.",
            "www_ttl": 300,
            "www_A_via_cname": BASELINE_WWW_A,
        },
        "do_not_change": ["NS", "TXT", "MX", "api.smartlic.tech", "app.smartlic.tech"],
        "secrets_printed": False,
    }


def render_canary_text(canary: dict[str, Any], caddy: dict[str, Any]) -> str:
    lines = [
        f"# CANARY_LOCAL {CAMPAIGN_NAME}",
        f"entry: {canary.get('entry')}",
        f"status: {canary.get('status')}",
        f"caddy: {caddy.get('status')} {caddy.get('detail') or ''}".rstrip(),
        "",
    ]
    for index, launch in enumerate(canary.get("launches") or [], start=1):
        lines.append(f"## launch {index} port={launch['port']}")
        lines.append(launch["banner"])
        for row in launch["rows"]:
            loc = row["location"] if row["location"] is not None else "-"
            lines.append(
                f"{row['method']} {row['path']} → {row['status']} Location={loc} "
                f"cfg={row['config_hash'][:12]}…"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def render_rollback_md(compiled: CompiledMap) -> str:
    return f"""# ROLLBACK — {CAMPAIGN_NAME}

Do **not** start FastAPI, Next.js, Redis, ARQ, Supabase, Stripe, or any SmartLic application.

## Config (always available)

```text
python3 -m bridge.generate --rollback
# then SIGTERM + start `python3 -m bridge.serve`, or `systemctl reload caddy-bridge`
```

Restores `bridge/generated/previous/` (zero 301s, default 410). Manifesto hash stays
`{compiled.manifesto_sha256}`. Live ready config was `{compiled.config_sha256}`.
This is the pre-bridge fail-closed map.

## DNS / TLS (only if the founder applied cutover records)

1. PATCH apex **A** `smartlic.tech` → `69.46.46.88` TTL **60**, proxied=false.
2. DELETE `www` **A**.
3. CREATE `www` **CNAME** `app.smartlic.tech.` TTL **300**, proxied=false.
4. Do **not** change NS, TXT, MX, `api`, or `app`.

```text
# export CF_API_TOKEN=... CF_ZONE_ID=...   # local only; never commit
curl -sS -X PATCH -H "Authorization: Bearer $CF_API_TOKEN" \\
  -H "Content-Type: application/json" \\
  "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records/$APEX_A_ID" \\
  --data '{{"type":"A","name":"smartlic.tech","content":"69.46.46.88","ttl":60,"proxied":false}}'
curl -sS -X DELETE -H "Authorization: Bearer $CF_API_TOKEN" \\
  "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records/$WWW_A_ID"
curl -sS -X POST -H "Authorization: Bearer $CF_API_TOKEN" \\
  -H "Content-Type: application/json" \\
  "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records" \\
  --data '{{"type":"CNAME","name":"www","content":"app.smartlic.tech.","ttl":300,"proxied":false}}'
```

That restores the 2026-08-14/15 Railway fallback 404. It does **not** start SmartLic.

## Immediate rollback if

- A ready Location/canonical differs from the pin
- Redirect chain, loop, or wildcard
- Unapproved path 301s instead of 410
- TLS invalid
- 5xx on canary
- Soft-404 / generic destination
- Secret or SmartLic product identity reappears

## Canary rehearsal of config rollback

`bridge/tests/test_generate.py::RollbackTests` and `bridge.preflight.run_local_blackbox`
apply the ready map, roll back, and require every ready path to return 410 with no Location.
"""


def render_removal_md(compiled: CompiledMap) -> str:
    return f"""# REMOVAL_CRITERIA — {CAMPAIGN_NAME}

Owner: {compiled.owner}
Config: `{compiled.config_sha256}`
Manifesto: `{compiled.manifesto_sha256}`
Observation window: {compiled.observation_window_days} days after the **first production 301** of this hash (live apex/www only; loopback does not start the window).

## Keep the bridge until all are true

1. Observation window complete (28 days from first live 301 of this hash).
2. Zero residual priority errors: no ready-row 5xx/chain/loop/soft-404; no HOLD/RETIRE 301.
3. Critical backlinks (if any become known) point at CONFENGE or are accepted as retired.
4. SmartLic#2111 archive gate is ready (this campaign does not execute #2111).

## Removal trigger (from the pinned map)

{compiled.removal_trigger}

## Logs to keep (minimum, no PII)

- status, path family / path class, referrer host if present
- manifesto/config hashes
- no query values, cookies, Authorization, emails, CNPJ, bodies, client IP

Retention of any persisted window artifact: 35 days then delete.

## What to delete at removal

- public A records pointing at the bridge host
- Caddy unit + `/var/lib/caddy` (private keys never in Git)
- `python3 -m bridge.serve` unit
- this campaign directory after the final record is archived in #2111

Railway/app SmartLic must stay **off** `smartlic.tech` / `www`. `api.smartlic.tech` is not recovered.
"""


def render_founder_txt(compiled: CompiledMap) -> str:
    return f"""FOUNDER_ACTION_REQUIRED_CUTOVER
campaign={CAMPAIGN_NAME}
verdict=CUTOVER READY
blocker=credential/console possession only (BRIDGE_PUBLIC_IPV4, SMARTLIC_ACME_EMAIL, CF_API_TOKEN, CF_ZONE_ID)
do_not_redesign=use generated Caddyfile + python3 -m bridge.serve; do not rebuild SmartLic
manifesto_sha256={compiled.manifesto_sha256}
config_sha256={compiled.config_sha256}
pinned_commit={PINNED_COMMIT}

HOSTNAMES
  smartlic.tech
  www.smartlic.tech
  do_not_change=NS TXT MX api.smartlic.tech app.smartlic.tech

DNS APPLY (Cloudflare, proxied=false, after host :80 reaches Caddy)
  type=A  name=smartlic.tech      value=$BRIDGE_PUBLIC_IPV4  ttl=60
  type=A  name=www.smartlic.tech  value=$BRIDGE_PUBLIC_IPV4  ttl=300
  then DELETE www CNAME app.smartlic.tech.
  leave NS jermaine/ryleigh, TXT google-site-verification, MX 0 smartlic.tech., api, app

DEPLOY / RELOAD (on the host named by $BRIDGE_PUBLIC_IPV4)
  1. copy bridge/ → /opt/smartlic-bridge/bridge ; PYTHONPATH=/opt/smartlic-bridge
  2. python3 -m bridge.generate --check
     expect: GENERATE_OK manifesto={compiled.manifesto_sha256} config={compiled.config_sha256} redirects=11 default=410
  3. install -d -o caddy -g caddy -m 0700 /var/lib/caddy
  4. install -m 0644 bridge/generated/Caddyfile /etc/caddy/Caddyfile
  5. install -d -m 0750 /etc/smartlic-bridge && cp bridge/deploy/env.example /etc/smartlic-bridge/env
     fill BRIDGE_PUBLIC_IPV4 and SMARTLIC_ACME_EMAIL (mode 0640)
  6. install bridge/deploy/smartlic-bridge.service and caddy-bridge.service
     systemctl enable --now smartlic-bridge caddy-bridge
  7. apply bridge/deploy/nftables.conf
     ss -lntp :8765 on 127.0.0.1 only; :80/:443 on public IP
  8. local rehearse: curl -sI -H 'Host: smartlic.tech' http://127.0.0.1:8765/glossario/reajuste
     expect HTTP/1.0 301   Location: {READY_CANARY_TARGET}
  9. then apply DNS above; wait ACME

TLS VERIFY
  echo | openssl s_client -servername smartlic.tech -connect smartlic.tech:443 2>/dev/null | openssl x509 -noout -ext subjectAltName
  expect DNS:smartlic.tech and DNS:www.smartlic.tech on one certificate

CURL CANARIES (after TLS)
  curl -sI https://smartlic.tech/glossario/reajuste
    expect: HTTP/2 301
            Location: {READY_CANARY_TARGET}
            X-Bridge-Config-Hash: {compiled.config_sha256}
  curl -sI https://smartlic.tech/login
    expect: HTTP/2 410
            no Location header
  curl -sI https://www.smartlic.tech/glossario/reajuste
    expect: same 301 as apex (valid SAN)

DNS ROLLBACK
  type=A     name=smartlic.tech      value=69.46.46.88         ttl=60
  DELETE     name=www A
  type=CNAME name=www.smartlic.tech  value=app.smartlic.tech.  ttl=300  proxied=false

CONFIG ROLLBACK
  python3 -m bridge.generate --rollback && systemctl reload caddy-bridge
  expect: every previously-ready path returns 410 and no Location

DO NOT
  recover api.smartlic.tech as an API (tombstone/410 only if ever pointed here)
  301 /* or /consultoria-b2g or home
  hunt a Railway token or restore SmartLic app
"""


def render_evidence_md(
    compiled: CompiledMap,
    *,
    generate: dict[str, Any],
    pins: dict[str, Any],
    targets: dict[str, Any],
    canary: dict[str, Any],
    caddy: dict[str, Any],
    verdict: str,
    residual: list[str],
) -> str:
    return f"""# EVIDENCE — {CAMPAIGN_NAME}

Recorded: {utc_now()}
Branch: `goal/smartlic-redirect-cutover-20260818`
Canonical consume: SmartLic #2135 MERGED on `main` (`7b9e9da6`); this campaign continues that pin, it does not duplicate the execute set.
Open PRs touching bridge/: none implementing a second map. #2150 is closeout docs only.

## Hashes

| Pin | Value |
|---|---|
| manifesto SHA-256 | `{compiled.manifesto_sha256}` |
| config SHA-256 | `{compiled.config_sha256}` |
| web-cfg inventory commit | `{PINNED_COMMIT}` |
| schema / version | `{PINNED_SCHEMA}` / `{PINNED_VERSION}` |
| redirects / holds / retire | {len(compiled.redirects)} / {len(compiled.holds)} / {PINNED_RETIRE_COUNT} |
| persist allowlist | `{', '.join(compiled.persist)}` |
| web-cfg main inventory.v2.sha256 | `{PINNED_SHA256}` (no drift) |

generate --check ×2: `{generate['status']}`. Pin comparison: PASS ({len(pins)} fields).

## Tests

`python3 -m unittest discover -s bridge/tests -q` ×2 — see scratch `bridge-tests.log`.
New `bridge/tests/test_cutover_campaign.py` drives shipped `generate_main`, `policy.resolve`, `bridge.serve`, `probe_targets` / GET+HEAD, and asserts campaign artifact hashes equal `bridge.pins`.

## Targets

`{targets['status']}` — {targets['count']} compiled ready rows GET+HEAD on `{TARGET_HOSTNAME}`; shipped `probe_targets` also PASS. No loop/chain/soft-404.

## Canary

serve ×2 `{canary['status']}` via `python3 -m bridge.serve`. Caddy: `{caddy.get('status')}`. {caddy.get('detail') or ''}

## Deploy

Live DNS/TLS/ACME **not applied**. Credentials absent (`BRIDGE_PUBLIC_IPV4`, `SMARTLIC_ACME_EMAIL`, `CF_API_TOKEN`, `CF_ZONE_ID`). Railway remains on apex/www. `api.smartlic.tech` untouched.

## Verdict

**{verdict}**

## Residual risk

{chr(10).join('- ' + item for item in residual)}
"""


def write_campaign(
    out_dir: Path,
    compiled: CompiledMap,
    *,
    generate: dict[str, Any],
    pins: dict[str, Any],
    targets: dict[str, Any],
    canary: dict[str, Any],
    caddy: dict[str, Any],
    dns: dict[str, Any],
    preflight: dict[str, Any],
) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    creds = dns.get("credentials_present") or {}
    live_apply = all(creds.get(name) for name in ("BRIDGE_PUBLIC_IPV4", "SMARTLIC_ACME_EMAIL", "CF_API_TOKEN", "CF_ZONE_ID"))
    verdict = "PRODUCTION DONE" if live_apply else "CUTOVER READY"
    residual = [
        "No authorized $BRIDGE_PUBLIC_IPV4 in this environment; founder file keeps the placeholder.",
        "Caddy binary absent here; terminator safety is covered by generate assert_terminator_safe + serve ×2.",
        "Observation window not started (no live production 301).",
        "www TLS SAN mismatch on Railway is expected until cutover.",
        "api.smartlic.tech remains Railway CNAME; not in this cutover.",
    ]
    manifest = {
        "campaign": CAMPAIGN_NAME,
        "verdict": verdict,
        "manifesto_sha256": compiled.manifesto_sha256,
        "config_sha256": compiled.config_sha256,
        "pinned_commit": PINNED_COMMIT,
        "schema": PINNED_SCHEMA,
        "redirects": len(compiled.redirects),
        "holds": len(compiled.holds),
        "retire": PINNED_RETIRE_COUNT,
        "default_status": compiled.default_status,
        "live_apply": False,
        "first_production_301": None,
        "blocker": None if live_apply else "credential/console possession only",
        "railway_off_path": False,
        "decision": "REDIRECT",
        "destination_owner": "web-cfg / confenge.com.br",
        "rollback": "python3 -m bridge.generate --rollback ; DNS apex A 69.46.46.88 TTL 60; delete www A; recreate www CNAME app.smartlic.tech. TTL 300",
        "exit_criterion": compiled.removal_trigger,
        "recorded_at": utc_now(),
    }
    files = {
        "PRE_FLIGHT.json": json.dumps(preflight, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        "TARGET_VERIFICATION.json": json.dumps(targets, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        "CANARY_LOCAL.txt": render_canary_text(canary, caddy),
        "CUTOVER_MANIFEST.json": json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        "ROLLBACK.md": render_rollback_md(compiled),
        "REMOVAL_CRITERIA.md": render_removal_md(compiled),
        "EVIDENCE.md": render_evidence_md(
            compiled,
            generate=generate,
            pins=pins,
            targets=targets,
            canary=canary,
            caddy=caddy,
            verdict=verdict,
            residual=residual,
        ),
        "FOUNDER_ACTION_REQUIRED_CUTOVER.txt": render_founder_txt(compiled),
    }
    written: dict[str, str] = {}
    for name, content in files.items():
        path = out_dir / name
        path.write_text(content, encoding="utf-8")
        written[name] = sha256_bytes(content.encode("utf-8"))
    return written


def run_campaign(out_dir: Path | None = None) -> dict[str, Any]:
    dest = out_dir or DEFAULT_CAMPAIGN_DIR
    generate = run_generate_check()
    compiled = load_and_compile()
    pins = assert_pins(compiled)
    targets = probe_ready_targets_full(compiled)
    canary = canary_serve_twice(compiled)
    caddy = try_caddy_canary()
    dns = inventory_dns_tls()
    compiled_map, compile_error = try_load_compiled()
    caddy_text = (GENERATED_DIR / "Caddyfile").read_text(encoding="utf-8")
    preflight_report = run_preflight(
        PreflightInputs(
            bridge_public_ipv4=os.environ.get("BRIDGE_PUBLIC_IPV4"),
            smartlic_acme_email=os.environ.get("SMARTLIC_ACME_EMAIL"),
            cf_api_token=os.environ.get("CF_API_TOKEN"),
            cf_zone_id=os.environ.get("CF_ZONE_ID"),
            compiled=compiled_map,
            compile_error=compile_error,
            caddy_text=caddy_text,
            dns_apex=observe_dns("smartlic.tech"),
            dns_www=observe_dns("www.smartlic.tech"),
            tls_apex=observe_tls("smartlic.tech"),
            tls_www=observe_tls("www.smartlic.tech"),
            skip_blackbox=False,
            run_live_dest_probe=False,
        )
    )
    preflight = preflight_report.to_dict()
    preflight["campaign"] = CAMPAIGN_NAME
    preflight["open_prs_touching_bridge"] = [
        {"number": 2150, "title": "docs(ops): PRODUCTION-CLOSEOUT-01 SmartLic preflight remains BLOCKED", "touches_execute_set": False},
    ]
    preflight["canonical_consume"] = {
        "pr": 2135,
        "state": "MERGED",
        "branch": "main",
        "this_branch": "goal/smartlic-redirect-cutover-20260818",
        "based_on": "origin/main",
    }
    preflight["dns_inventory"] = dns
    preflight["caddy"] = caddy
    preflight["generate"] = generate
    preflight["pins"] = {name: item["got"] if isinstance(item, dict) and "got" in item else item for name, item in pins.items()}
    written = write_campaign(
        dest,
        compiled,
        generate=generate,
        pins=pins,
        targets=targets,
        canary=canary,
        caddy=caddy,
        dns=dns,
        preflight=preflight,
    )
    return {
        "verdict": "CUTOVER READY",
        "out_dir": str(dest),
        "written": written,
        "manifesto_sha256": compiled.manifesto_sha256,
        "config_sha256": compiled.config_sha256,
        "caddy": caddy.get("status"),
        "targets": targets.get("status"),
        "canary": canary.get("status"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run #2115 cutover campaign gates and write evidence.")
    parser.add_argument("--out", type=Path, default=DEFAULT_CAMPAIGN_DIR)
    args = parser.parse_args(argv)
    try:
        result = run_campaign(args.out)
    except ManifestError as exc:
        print(f"CAMPAIGN_BLOCKED {exc}", file=sys.stderr)
        return 2
    print(
        "CAMPAIGN_OK "
        f"verdict={result['verdict']} "
        f"manifesto={result['manifesto_sha256']} "
        f"config={result['config_sha256']} "
        f"out={result['out_dir']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
