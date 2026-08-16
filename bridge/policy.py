"""Request → (status, Location) from a compiled execute set.

This is the only request evaluator. serve.py and tests call it.
The compiled map must come from generate.compile_execute_set on the
hash-pinned manifesto — never from a second handwritten table.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence
from urllib.parse import parse_qsl, urlencode, urlsplit


@dataclass(frozen=True)
class RedirectRule:
    path: str
    target_url: str
    expected_canonical: str
    family: str
    owner: str
    persist: tuple[str, ...]
    expected_http: int


@dataclass(frozen=True)
class CompiledMap:
    manifesto_sha256: str
    config_sha256: str
    persist: tuple[str, ...]
    redirects: tuple[RedirectRule, ...]
    by_path: Mapping[str, RedirectRule] = field(repr=False)
    holds: tuple[str, ...] = ()
    default_status: int = 410
    observation_window_days: int = 28
    owner: str = "SmartLic#2115"
    removal_trigger: str = ""
    expiry_review: str = ""


@dataclass(frozen=True)
class Decision:
    status: int
    location: str | None
    rule_id: str
    family: str
    hops: int


def normalize_path(path: str) -> str:
    raw = (path or "/").split("?", 1)[0]
    if not raw.startswith("/"):
        raw = "/" + raw
    if raw != "/" and raw.endswith("/"):
        raw = raw.rstrip("/")
    return raw


def filter_query(raw_query: str, persist: Sequence[str]) -> str:
    """Keep manifesto allowlist + utm_*; always drop PII and anything else."""
    from bridge.pins import PII_QUERY_KEYS

    allowed = {k.lower() for k in persist}
    kept: list[tuple[str, str]] = []
    for key, value in parse_qsl(raw_query or "", keep_blank_values=True):
        lowered = key.lower()
        if lowered in PII_QUERY_KEYS:
            continue
        if lowered in allowed or lowered.startswith("utm_"):
            kept.append((key, value))
    return urlencode(kept, doseq=True)


def _host_allowed(host: str | None) -> bool:
    from bridge.pins import LEGACY_HOSTNAMES

    if host is None or host == "":
        return True
    hostname = host.split(":", 1)[0].lower()
    if hostname in {"localhost", "127.0.0.1", "::1"}:
        return True
    return hostname in LEGACY_HOSTNAMES


def resolve(
    compiled: CompiledMap,
    path: str,
    query: str = "",
    host: str | None = None,
) -> Decision:
    """Evaluate one request against the compiled execute set."""
    if not _host_allowed(host):
        return Decision(
            status=compiled.default_status,
            location=None,
            rule_id="unmapped-host",
            family="retire",
            hops=0,
        )

    norm = normalize_path(path)
    if norm in set(compiled.holds):
        return Decision(
            status=compiled.default_status,
            location=None,
            rule_id="hold-fail-closed",
            family="hold",
            hops=0,
        )
    rule = compiled.by_path.get(norm)
    if rule is None:
        return Decision(
            status=compiled.default_status,
            location=None,
            rule_id="default-410",
            family="retire",
            hops=0,
        )

    qs = filter_query(query, rule.persist or compiled.persist)
    location = rule.target_url
    if qs:
        location = f"{location}?{qs}" if "?" not in location else f"{location}&{qs}"

    target_host = (urlsplit(location).hostname or "").lower()
    if target_host != "confenge.com.br":
        return Decision(
            status=compiled.default_status,
            location=None,
            rule_id="unsafe-target-blocked",
            family="retire",
            hops=0,
        )

    return Decision(
        status=rule.expected_http,
        location=location,
        rule_id=rule.path,
        family=rule.family,
        hops=1,
    )
