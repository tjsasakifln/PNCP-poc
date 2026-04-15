"""STORY-4.1 (TD-SYS-014) — tests for OpenAI Batch API offline path."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_async_client():
    """Provide a mocked AsyncOpenAI client with ``files.create`` + ``batches.*``."""

    client = SimpleNamespace()
    client.files = SimpleNamespace(create=AsyncMock(), content=AsyncMock())
    client.batches = SimpleNamespace(create=AsyncMock(), retrieve=AsyncMock())
    return client


@pytest.fixture
def mock_redis_sets():
    """AsyncMock Redis that tracks sadd/srem/hset/expire/delete/smembers calls."""

    redis = AsyncMock()
    state = {"pending": set(), "meta": {}}

    async def _sadd(key, *members):
        state["pending"].update(members)
        return len(members)

    async def _srem(key, *members):
        for m in members:
            state["pending"].discard(m)
        return len(members)

    async def _smembers(key):
        return set(state["pending"])

    async def _hset(key, mapping=None, **kwargs):
        state["meta"].setdefault(key, {}).update(mapping or {})
        return len(mapping or {})

    async def _expire(*args, **kwargs):
        return True

    async def _delete(*keys):
        for key in keys:
            state["meta"].pop(key, None)
        return len(keys)

    redis.sadd.side_effect = _sadd
    redis.srem.side_effect = _srem
    redis.smembers.side_effect = _smembers
    redis.hset.side_effect = _hset
    redis.expire.side_effect = _expire
    redis.delete.side_effect = _delete
    redis._state = state
    return redis


# ---------------------------------------------------------------------------
# submit_batch — threshold gating + happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_submit_batch_returns_none_when_flag_disabled(monkeypatch, mock_async_client, mock_redis_sets):
    """With LLM_BATCH_ENABLED=False, submit_batch never hits the API."""

    from llm_arbiter import batch_api

    monkeypatch.setattr("config.LLM_BATCH_ENABLED", False, raising=False)
    monkeypatch.setattr("config.LLM_BATCH_MIN_ITEMS", 20, raising=False)

    with (
        patch.object(batch_api, "_get_redis", new=AsyncMock(return_value=mock_redis_sets)),
        patch("llm_arbiter.async_runtime._get_async_client", return_value=mock_async_client),
    ):
        batch_id = await batch_api.submit_batch(
            [{"objeto": "x", "valor": 1.0}] * 30,
            setor_name="TI",
            termos_busca=["a"],
        )
    assert batch_id is None
    mock_async_client.files.create.assert_not_called()
    mock_async_client.batches.create.assert_not_called()


@pytest.mark.asyncio
async def test_submit_batch_returns_none_below_threshold(monkeypatch, mock_async_client, mock_redis_sets):
    """Below LLM_BATCH_MIN_ITEMS we fall through to live classification."""

    from llm_arbiter import batch_api

    monkeypatch.setattr("config.LLM_BATCH_ENABLED", True, raising=False)
    monkeypatch.setattr("config.LLM_BATCH_MIN_ITEMS", 20, raising=False)

    with (
        patch.object(batch_api, "_get_redis", new=AsyncMock(return_value=mock_redis_sets)),
        patch("llm_arbiter.async_runtime._get_async_client", return_value=mock_async_client),
    ):
        batch_id = await batch_api.submit_batch(
            [{"objeto": "x", "valor": 1.0}] * 5,
            setor_name="TI",
            termos_busca=[],
        )
    assert batch_id is None


@pytest.mark.asyncio
async def test_submit_batch_happy_path_persists_metadata(monkeypatch, mock_async_client, mock_redis_sets):
    """Successful submission stores batch_id in Redis pending set."""

    from llm_arbiter import batch_api

    monkeypatch.setattr("config.LLM_BATCH_ENABLED", True, raising=False)
    monkeypatch.setattr("config.LLM_BATCH_MIN_ITEMS", 5, raising=False)

    mock_async_client.files.create.return_value = SimpleNamespace(id="file-1")
    mock_async_client.batches.create.return_value = SimpleNamespace(id="batch-42")

    with (
        patch.object(batch_api, "_get_redis", new=AsyncMock(return_value=mock_redis_sets)),
        patch("llm_arbiter.async_runtime._get_async_client", return_value=mock_async_client),
    ):
        batch_id = await batch_api.submit_batch(
            [{"objeto": f"obj-{i}", "valor": float(i)} for i in range(10)],
            setor_name="TI",
            termos_busca=["software"],
            search_id="sid-1",
        )

    assert batch_id == "batch-42"
    assert "batch-42" in mock_redis_sets._state["pending"]
    mock_async_client.files.create.assert_awaited_once()
    mock_async_client.batches.create.assert_awaited_once()


# ---------------------------------------------------------------------------
# poll_batch — terminal / in-progress / failure transitions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_poll_batch_returns_none_when_in_progress(mock_async_client, mock_redis_sets):
    from llm_arbiter import batch_api

    mock_async_client.batches.retrieve.return_value = SimpleNamespace(status="in_progress")

    with (
        patch.object(batch_api, "_get_redis", new=AsyncMock(return_value=mock_redis_sets)),
        patch("llm_arbiter.async_runtime._get_async_client", return_value=mock_async_client),
    ):
        result = await batch_api.poll_batch("batch-42")

    assert result is None


@pytest.mark.asyncio
async def test_poll_batch_completed_returns_parsed_results(mock_async_client, mock_redis_sets):
    from llm_arbiter import batch_api

    mock_redis_sets._state["pending"].add("batch-42")

    mock_async_client.batches.retrieve.return_value = SimpleNamespace(
        status="completed", output_file_id="file-out"
    )
    jsonl = (
        json.dumps({"custom_id": "item-0", "response": {"body": "SIM"}})
        + "\n"
        + json.dumps({"custom_id": "item-1", "response": {"body": "NAO"}})
        + "\n"
    )
    mock_async_client.files.content.return_value = SimpleNamespace(text=jsonl)

    with (
        patch.object(batch_api, "_get_redis", new=AsyncMock(return_value=mock_redis_sets)),
        patch("llm_arbiter.async_runtime._get_async_client", return_value=mock_async_client),
    ):
        result = await batch_api.poll_batch("batch-42")

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["custom_id"] == "item-0"
    # terminal status drops from pending set
    assert "batch-42" not in mock_redis_sets._state["pending"]


@pytest.mark.asyncio
async def test_poll_batch_terminal_failure_drops_metadata(mock_async_client, mock_redis_sets):
    from llm_arbiter import batch_api

    mock_redis_sets._state["pending"].add("batch-42")
    mock_async_client.batches.retrieve.return_value = SimpleNamespace(status="failed")

    with (
        patch.object(batch_api, "_get_redis", new=AsyncMock(return_value=mock_redis_sets)),
        patch("llm_arbiter.async_runtime._get_async_client", return_value=mock_async_client),
    ):
        result = await batch_api.poll_batch("batch-42")

    assert result == []
    assert "batch-42" not in mock_redis_sets._state["pending"]


def test_batch_poll_cron_registered():
    """``register_all_cron_tasks`` includes ``start_llm_batch_poll_task``."""

    from jobs.cron.scheduler import register_all_cron_tasks
    from jobs.cron.llm_batch_poll import start_llm_batch_poll_task

    tasks = register_all_cron_tasks()
    assert start_llm_batch_poll_task in tasks
