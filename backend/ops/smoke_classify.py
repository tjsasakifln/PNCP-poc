"""Classify post-deploy probe outcomes. Used by CI smoke and unit tests."""

from __future__ import annotations

from typing import Mapping

HEALTH_PATHS = frozenset({"/health/live", "/health/ready", "/openapi.json"})


def header_value(headers: Mapping[str, str], name: str) -> str | None:
    lowered = name.lower()
    for key, value in headers.items():
        if key.lower() == lowered:
            return value
    return None


def classify_probe(status_code: int, headers: Mapping[str, str], path: str) -> str:
    """Return one of: edge_fallback | app_unhealthy | not_found | ok | degraded.

    404 on an unknown URL is not_found — never healthy.
    404/5xx on a health path is app_unhealthy.
    x-railway-fallback is abandoned edge, not an app regression.
    """
    if (header_value(headers, "x-railway-fallback") or "").lower() == "true":
        return "edge_fallback"
    if status_code >= 500:
        return "app_unhealthy"
    if path in HEALTH_PATHS:
        if status_code == 200:
            return "ok"
        if path == "/health/ready" and status_code in {203, 429}:
            return "degraded"
        return "app_unhealthy"
    if status_code == 404:
        return "not_found"
    if 200 <= status_code < 400:
        return "ok"
    return "degraded"


def is_healthy(classification: str) -> bool:
    return classification == "ok"
