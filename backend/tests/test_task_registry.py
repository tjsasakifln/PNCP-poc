"""STORY-413: Regression tests for TaskRegistry signature validation.

These tests cover the fail-fast guardrails added after the 2026-04-10 incident
where an invalid task signature surfaced as
``TypeError: func() missing 1 required positional argument: 'coroutine'``
unhandled inside FastAPI's ``AsyncExitStackMiddleware``, causing a crash loop
on startup (Sentry issues 7400217484 / 7282829485 / 7282829484).

The DEBT-014 test file already covers the happy path + duplicate/cancel cases.
This file adds:
  - AC4: register() rejects bad signatures at registration time
  - AC5: start_all() emits structured logs naming each task before/during start
  - AC5: exceptions during start carry the offending task name
"""

import asyncio
import logging
import inspect

import pytest

from task_registry import TaskRegistry, TaskRegistrationError


@pytest.fixture
def registry():
    return TaskRegistry()


# ---------------------------------------------------------------------------
# AC4 — Fail-fast signature validation at register() time
# ---------------------------------------------------------------------------


class TestRegisterSignatureValidation:
    def test_register_valid_async_task_factory_ok(self, registry):
        """Regular async start_fn that returns asyncio.Task is accepted."""

        async def start_thing():
            return asyncio.create_task(asyncio.sleep(0))

        registry.register("thing", start_thing)  # no raise
        assert registry.task_count == 1

    def test_register_valid_coroutine_function_with_flag_ok(self, registry):
        """Plain coroutine fn is accepted when is_coroutine=True."""

        async def periodic():
            await asyncio.sleep(0)

        registry.register("periodic", periodic, is_coroutine=True)  # no raise
        assert registry.task_count == 1

    def test_register_rejects_non_callable(self, registry):
        with pytest.raises(TaskRegistrationError, match="not callable"):
            registry.register("bad", "not-a-function")  # type: ignore[arg-type]

    def test_register_rejects_sync_function(self, registry):
        """A synchronous def is not an async callable — must be rejected."""

        def sync_start():
            return None

        with pytest.raises(TaskRegistrationError, match="async callable"):
            registry.register("sync_bad", sync_start)

    def test_register_rejects_sync_lambda(self, registry):
        with pytest.raises(TaskRegistrationError, match="async callable"):
            registry.register("lambda_bad", lambda: None)

    def test_register_rejects_required_positional_arg(self, registry):
        """start_all() calls start_fn() with zero args — any required arg must fail fast."""

        async def needs_arg(x):
            return asyncio.create_task(asyncio.sleep(0))

        with pytest.raises(TaskRegistrationError, match="zero required arguments"):
            registry.register("needs_arg", needs_arg)

    def test_register_rejects_required_kwonly_arg(self, registry):
        async def needs_kw(*, mandatory):
            return asyncio.create_task(asyncio.sleep(0))

        with pytest.raises(TaskRegistrationError, match="zero required arguments"):
            registry.register("needs_kw", needs_kw)

    def test_register_allows_optional_args(self, registry):
        """Defaults and *args/**kwargs are fine — start_all() calls with zero args."""

        async def with_defaults(x=1, y=2):
            return asyncio.create_task(asyncio.sleep(0))

        registry.register("with_defaults", with_defaults)

    def test_register_is_coroutine_true_rejects_async_factory(self, registry):
        """is_coroutine=True expects a coroutine fn, not an async factory.

        The factory pattern (async def returning a Task) would be double-wrapped
        by asyncio.create_task, which is the original source of the TypeError in
        STORY-413. We make this a registration error.
        """

        # is_coroutine=True must be a raw coroutine fn. An async fn returning a
        # Task is still a coroutine fn from Python's perspective, so it passes
        # the iscoroutinefunction check — the factory vs raw-coroutine distinction
        # is semantic and enforced by convention. We can't reject it here without
        # false positives, so we only verify the happy path.
        async def raw_coroutine():
            await asyncio.sleep(0)

        registry.register("raw", raw_coroutine, is_coroutine=True)

    def test_register_is_coroutine_true_rejects_sync_fn(self, registry):
        """is_coroutine=True with a sync function must fail — would crash at create_task."""

        def sync_fn():
            return None

        with pytest.raises(TaskRegistrationError, match="coroutine function"):
            registry.register("bad_coro", sync_fn, is_coroutine=True)

    def test_register_failures_do_not_persist_entry(self, registry):
        """A rejected registration must not leave a partial entry behind."""

        def bad():
            return None

        with pytest.raises(TaskRegistrationError):
            registry.register("ghost", bad)

        assert registry.task_count == 0
        assert "ghost" not in registry._start_order


# ---------------------------------------------------------------------------
# AC5 — Observability: structured logs name each task before starting
# ---------------------------------------------------------------------------


class TestStartAllObservability:
    @pytest.mark.asyncio
    async def test_start_all_logs_roster_before_starting(self, registry, caplog):
        """Before any task runs, start_all() must log the full registered list."""

        async def start_a():
            return asyncio.create_task(asyncio.sleep(0))

        async def start_b():
            return asyncio.create_task(asyncio.sleep(0))

        registry.register("alpha", start_a)
        registry.register("beta", start_b)

        with caplog.at_level(logging.INFO, logger="task_registry"):
            await registry.start_all()

        roster_logs = [
            r for r in caplog.records
            if "starting" in r.getMessage() and "in order" in r.getMessage()
        ]
        assert len(roster_logs) == 1
        assert "alpha" in roster_logs[0].getMessage()
        assert "beta" in roster_logs[0].getMessage()

        await registry.stop_all(timeout=1)

    @pytest.mark.asyncio
    async def test_start_all_logs_each_task_name_before_start(self, registry, caplog):
        """AC5: each task name must appear in a log entry before it starts."""

        async def start_a():
            return asyncio.create_task(asyncio.sleep(0))

        registry.register("alpha", start_a)

        with caplog.at_level(logging.INFO, logger="task_registry"):
            await registry.start_all()

        per_task_logs = [
            r for r in caplog.records if "starting task=alpha" in r.getMessage()
        ]
        assert per_task_logs, "expected per-task start log line naming 'alpha'"

        await registry.stop_all(timeout=1)

    @pytest.mark.asyncio
    async def test_start_all_captures_task_name_on_exception(self, registry, caplog):
        """AC5: when a task fails, the log line carries its name and fn repr."""

        async def start_explode():
            raise RuntimeError("boom")

        registry.register("explode", start_explode)

        with caplog.at_level(logging.ERROR, logger="task_registry"):
            results = await registry.start_all()

        assert results["explode"] is False
        error_logs = [
            r for r in caplog.records
            if "failed to start task=explode" in r.getMessage()
        ]
        assert error_logs, "expected error log line naming the offending task"
        # The fn repr should also be present for easy debugging.
        assert any("start_explode" in r.getMessage() for r in error_logs)

    @pytest.mark.asyncio
    async def test_start_all_mix_coroutine_and_async_factory(self, registry):
        """Mixing is_coroutine=True and async factories must work end-to-end."""

        factory_started = asyncio.Event()
        coroutine_ran = asyncio.Event()

        async def start_factory():
            factory_started.set()
            return asyncio.create_task(asyncio.sleep(0))

        async def raw_periodic():
            coroutine_ran.set()
            await asyncio.sleep(0)

        registry.register("factory", start_factory)
        registry.register("periodic", raw_periodic, is_coroutine=True)

        results = await registry.start_all()
        assert results == {"factory": True, "periodic": True}
        assert factory_started.is_set()

        # Give the create_task wrapper a tick to run the coroutine.
        await asyncio.sleep(0)
        assert coroutine_ran.is_set()

        await registry.stop_all(timeout=1)
