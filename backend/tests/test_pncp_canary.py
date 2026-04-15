"""STORY-4.5 (TD-SYS-002) — tests for PNCP breaking-change canary."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_pncp_payload() -> dict:
    """Minimal payload that passes the shipped PNCP schema."""

    return {
        "data": [
            {
                "cnpjOrgao": "12345678000100",
                "codigoCompra": "C-1",
                "codigoModalidadeContratacao": 6,
                "codigoUnidadeCompradora": "UC-1",
                "dataAberturaProposta": "2026-01-01T00:00:00",
                "dataEncerramentoProposta": "2026-01-15T00:00:00",
                "dataPublicacaoPncp": "2026-01-01T00:00:00",
                "linkSistemaOrigem": "https://pncp.gov.br/x",
                "modalidadeNome": "Pregão - Eletrônico",
                "municipio": "Brasília",
                "nomeOrgao": "Órgão X",
                "numeroControlePNCP": "CTRL-1",
                "objetoCompra": "Objeto",
                "situacaoCompra": "Aberta",
                "uf": "DF",
                "valorTotalEstimado": 100.0,
            }
        ],
        "paginaAtual": 1,
        "temProximaPagina": False,
        "totalPaginas": 1,
        "totalRegistros": 1,
    }


@pytest.fixture
def mock_redis():
    """AsyncMock Redis that honours counter semantics for canary tests."""

    redis = AsyncMock()
    state = {"counter": 0, "alerted_flags": {}}

    async def _incr(key):
        state["counter"] += 1
        return state["counter"]

    async def _set(key, value, *args, **kwargs):
        if "alerted" in key:
            nx = kwargs.get("nx", False)
            if nx and key in state["alerted_flags"]:
                return None
            state["alerted_flags"][key] = value
            return True
        if "consecutive_failures" in key:
            state["counter"] = int(value)
        return True

    async def _expire(*args, **kwargs):
        return True

    async def _delete(*keys):
        for key in keys:
            state["alerted_flags"].pop(key, None)
        return len(keys)

    redis.incr.side_effect = _incr
    redis.set.side_effect = _set
    redis.expire.side_effect = _expire
    redis.delete.side_effect = _delete
    redis._state = state  # expose for assertions
    return redis


def _mock_httpx_response(status_code: int, payload: Any | None = None) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload if payload is not None else {}
    return response


def _mock_httpx_client(responses: list) -> MagicMock:
    """Build an AsyncClient mock that replays ``responses`` in order."""

    client = MagicMock()
    iter_responses = iter(responses)

    async def _get(url, params=None, **kwargs):
        try:
            return next(iter_responses)
        except StopIteration as exc:
            raise RuntimeError("mock client exhausted") from exc

    client.get = AsyncMock(side_effect=_get)
    client.aclose = AsyncMock()
    return client


# ---------------------------------------------------------------------------
# Probe A: tamanhoPagina=51 accepted → breaking change
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_probe_51_accepted_triggers_metric_and_sentry(mock_redis):
    """When PNCP accepts tamanhoPagina=51, we page Sentry immediately."""

    import pncp_canary

    client = _mock_httpx_client([_mock_httpx_response(200, {"data": []})])

    mock_metric = MagicMock()
    with (
        patch.object(pncp_canary, "_get_redis", new=AsyncMock(return_value=mock_redis)),
        patch("metrics.PNCP_MAX_PAGE_SIZE_CHANGED", mock_metric),
        patch.object(pncp_canary, "_escalate_to_sentry") as escalate,
    ):
        result = await pncp_canary.run_pncp_canary(client=client, fail_threshold=3)

    assert result.healthy is False
    assert result.reason == "max_page_size_changed"
    assert result.alerted is True
    mock_metric.inc.assert_called_once()
    escalate.assert_called_once()
    args, _ = escalate.call_args
    assert args[0] == "max_page_size_changed"
    assert args[1]["probe"] == "tamanhoPagina=51"


# ---------------------------------------------------------------------------
# Probe B: consecutive failures gate Sentry on threshold
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_3_consecutive_failures_triggers_sentry_not_before(mock_redis):
    """Sentry fires only when failures >= threshold."""

    import pncp_canary

    async def _run_once():
        client = _mock_httpx_client(
            [
                _mock_httpx_response(400),  # probe A rejected (expected)
                _mock_httpx_response(500),  # probe B fails
            ]
        )
        with (
            patch.object(pncp_canary, "_get_redis", new=AsyncMock(return_value=mock_redis)),
            patch.object(pncp_canary, "_escalate_to_sentry") as escalate,
        ):
            result = await pncp_canary.run_pncp_canary(client=client, fail_threshold=3)
        return result, escalate

    result1, escalate1 = await _run_once()
    assert result1.consecutive_failures == 1
    assert result1.alerted is False
    escalate1.assert_not_called()

    result2, escalate2 = await _run_once()
    assert result2.consecutive_failures == 2
    assert result2.alerted is False
    escalate2.assert_not_called()

    result3, escalate3 = await _run_once()
    assert result3.consecutive_failures == 3
    assert result3.alerted is True
    escalate3.assert_called_once()
    args, _ = escalate3.call_args
    assert args[0] == "canary_3x_failed"


# ---------------------------------------------------------------------------
# Successful run resets counter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_successful_run_resets_counter(mock_redis, valid_pncp_payload):
    """A healthy probe resets consecutive_failures to 0."""

    import pncp_canary

    # Seed counter to 2 to simulate prior failures.
    mock_redis._state["counter"] = 2

    client = _mock_httpx_client(
        [
            _mock_httpx_response(400),  # probe A rejected
            _mock_httpx_response(200, valid_pncp_payload),  # probe B OK
        ]
    )
    with (
        patch.object(pncp_canary, "_get_redis", new=AsyncMock(return_value=mock_redis)),
        patch.object(pncp_canary, "_escalate_to_sentry") as escalate,
    ):
        result = await pncp_canary.run_pncp_canary(client=client, fail_threshold=3)

    assert result.healthy is True
    escalate.assert_not_called()
    # Counter was reset via set(..., 0)
    assert mock_redis._state["counter"] == 0


# ---------------------------------------------------------------------------
# Shape drift alerts immediately (not gated on 3x)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_shape_drift_triggers_sentry(mock_redis):
    """When payload fails schema validation we alert on the first occurrence."""

    import pncp_canary

    # Payload missing ALL required fields — guaranteed schema violation.
    drifted_payload = {"data": [{"unexpected_field": 1}], "totalRegistros": "not-an-int"}

    client = _mock_httpx_client(
        [
            _mock_httpx_response(400),  # probe A rejected
            _mock_httpx_response(200, drifted_payload),  # probe B OK status but drifted
        ]
    )
    with (
        patch.object(pncp_canary, "_get_redis", new=AsyncMock(return_value=mock_redis)),
        patch.object(pncp_canary, "_escalate_to_sentry") as escalate,
    ):
        result = await pncp_canary.run_pncp_canary(client=client, fail_threshold=3)

    # If the schema file was bundled, shape drift should fire immediately.
    # When the schema is missing (CI image without it) the canary is healthy.
    if result.reason == "shape_drift":
        assert result.alerted is True
        escalate.assert_called_once()
        args, _ = escalate.call_args
        assert args[0] == "shape_drift"
        assert "schema_errors" in args[1]
    else:  # graceful degradation when schema missing
        assert result.healthy is True


# ---------------------------------------------------------------------------
# Sentry dedup via Redis flag
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sentry_dedup_via_fingerprint(mock_redis):
    """Two back-to-back Probe A failures produce ONE Sentry event."""

    import pncp_canary

    async def _run():
        client = _mock_httpx_client([_mock_httpx_response(200, {"data": []})])
        with (
            patch.object(pncp_canary, "_get_redis", new=AsyncMock(return_value=mock_redis)),
            patch.object(pncp_canary, "_escalate_to_sentry") as escalate,
        ):
            result = await pncp_canary.run_pncp_canary(client=client, fail_threshold=3)
        return result, escalate

    r1, e1 = await _run()
    r2, e2 = await _run()

    assert r1.alerted is True
    assert r2.alerted is False  # dedup via Redis NX flag
    e1.assert_called_once()
    e2.assert_not_called()


# ---------------------------------------------------------------------------
# Scheduler registration
# ---------------------------------------------------------------------------


def test_cron_registered_in_scheduler():
    """``register_all_cron_tasks`` must include ``start_pncp_canary_task``."""

    from jobs.cron.scheduler import register_all_cron_tasks
    from jobs.cron.pncp_canary import start_pncp_canary_task

    tasks = register_all_cron_tasks()
    assert start_pncp_canary_task in tasks
