"""STORY-417: Regression tests for the BrasilAPI circuit breaker and
the partial response that keeps /empresa/{cnpj}/perfil-b2g usable when
BrasilAPI is down.

The 2026-04-10 incident had 42 ``httpx.ReadTimeout`` events from
BrasilAPI, each consuming up to 15s of the 120s Railway proxy budget.
The fix has three pieces, each covered here:

1. Timeout reduced 15 → 8s — a module-level constant.
2. Lightweight per-host CB that trips after 3 consecutive failures and
   stays OPEN for 60s before letting the next probe through.
3. ``BrasilAPIUnavailable`` raised on transient failures so the profile
   builder can fall back to a partial response with
   ``brasilapi_status='unavailable'`` instead of a 502.

We avoid ``respx`` because it is not installed in this environment.
Instead we stub ``httpx.AsyncClient`` at the call site — good enough to
pin the CB state machine without relying on a network-mocking lib.
"""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from routes import empresa_publica
from routes.empresa_publica import (
    BrasilAPIUnavailable,
    _BRASILAPI_TIMEOUT,
    _brasilapi_cb_state,
    _fetch_brasilapi,
)


@pytest.fixture(autouse=True)
def _reset_cb() -> None:
    _brasilapi_cb_state["consecutive_failures"] = 0
    _brasilapi_cb_state["opened_at"] = 0.0


def _patch_httpx_client(monkeypatch: pytest.MonkeyPatch, response_or_exc):
    """Replace ``httpx.AsyncClient`` inside empresa_publica with a stub.

    ``response_or_exc`` is either an object with ``status_code`` and
    ``json()`` (happy path) or an exception instance (failure path).
    """
    class _FakeAsyncClient:
        def __init__(self, *_args, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def get(self, _url):
            if isinstance(response_or_exc, Exception):
                raise response_or_exc
            return response_or_exc

    monkeypatch.setattr(
        empresa_publica.httpx, "AsyncClient", _FakeAsyncClient, raising=True
    )


def _make_response(status_code: int, json_body: dict | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        status_code=status_code,
        json=lambda: (json_body or {}),
    )


# ---------------------------------------------------------------------------
# Layer 1: timeout must stay at 8 seconds
# ---------------------------------------------------------------------------


def test_brasilapi_timeout_is_tightened_to_8s() -> None:
    assert _BRASILAPI_TIMEOUT == 8, (
        "STORY-417: BrasilAPI timeout must stay at 8s to protect the "
        "120s Railway proxy budget on /perfil-b2g."
    )


# ---------------------------------------------------------------------------
# Layer 2: CB opens after 3 consecutive failures
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cb_opens_after_three_consecutive_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_httpx_client(monkeypatch, _make_response(503))

    for _ in range(3):
        with pytest.raises(BrasilAPIUnavailable):
            await _fetch_brasilapi("11222333000181")

    assert _brasilapi_cb_state["consecutive_failures"] >= 3
    assert _brasilapi_cb_state["opened_at"] > 0


@pytest.mark.asyncio
async def test_cb_fast_fails_when_open(monkeypatch: pytest.MonkeyPatch) -> None:
    _brasilapi_cb_state["consecutive_failures"] = 3
    _brasilapi_cb_state["opened_at"] = time.time()

    # If the CB short-circuits correctly, the HTTP client must never be
    # instantiated. We detect that by making AsyncClient explode on use.
    class _BoomClient:
        def __init__(self, *_args, **_kwargs):
            raise AssertionError(
                "STORY-417: BrasilAPI CB open state must skip the HTTP call entirely"
            )

    monkeypatch.setattr(empresa_publica.httpx, "AsyncClient", _BoomClient)

    with pytest.raises(BrasilAPIUnavailable):
        await _fetch_brasilapi("11222333000181")


@pytest.mark.asyncio
async def test_success_resets_cb_counter(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_httpx_client(
        monkeypatch,
        _make_response(200, {"razao_social": "ACME LTDA"}),
    )

    _brasilapi_cb_state["consecutive_failures"] = 2  # not yet tripped

    data = await _fetch_brasilapi("11222333000181")
    assert data["razao_social"] == "ACME LTDA"
    assert _brasilapi_cb_state["consecutive_failures"] == 0
    assert _brasilapi_cb_state["opened_at"] == 0.0


@pytest.mark.asyncio
async def test_404_does_not_advance_cb_counter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """404 is a business signal, not a transport failure — do not trip."""
    _patch_httpx_client(monkeypatch, _make_response(404))

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await _fetch_brasilapi("00000000000000")
    assert exc_info.value.status_code == 404
    assert _brasilapi_cb_state["consecutive_failures"] == 0


@pytest.mark.asyncio
async def test_transport_error_trips_cb(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import httpx as _httpx

    _patch_httpx_client(monkeypatch, _httpx.ReadTimeout("simulated timeout"))

    for _ in range(3):
        with pytest.raises(BrasilAPIUnavailable):
            await _fetch_brasilapi("11222333000181")

    assert _brasilapi_cb_state["opened_at"] > 0


# ---------------------------------------------------------------------------
# Layer 3: orgao_stats Redis cache uses the correct key namespace
# ---------------------------------------------------------------------------


def test_orgao_stats_redis_key_prefix_matches_runbook() -> None:
    """Runbook + dashboards look for this key prefix — do not rename silently."""
    from routes import orgao_publico

    assert orgao_publico._REDIS_CACHE_PREFIX == "orgao_stats:v1:"
    assert orgao_publico._REDIS_CACHE_TTL_SECONDS == 15 * 60


# ---------------------------------------------------------------------------
# Full-profile fallback — BrasilAPI unavailable must NOT abort the endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_perfil_falls_back_when_brasilapi_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _raise_unavailable(_cnpj: str) -> dict:
        raise BrasilAPIUnavailable("simulated")

    async def _empty_contratos_local(_cnpj: str):
        return ([], "local")

    async def _empty_editais(_setor: str, _uf: str):
        return (0, [])

    monkeypatch.setattr(empresa_publica, "_fetch_brasilapi", _raise_unavailable)
    monkeypatch.setattr(empresa_publica, "_fetch_contratos_local", _empty_contratos_local)
    monkeypatch.setattr(empresa_publica, "_fetch_editais_abertos", _empty_editais)

    result = await empresa_publica._build_perfil("11222333000181")

    assert result["brasilapi_status"] == "unavailable"
    # Company fields fall back to placeholders rather than failing hard.
    assert result["empresa"]["razao_social"] == "Empresa"
    assert result["score"] == "SEM_HISTORICO"
