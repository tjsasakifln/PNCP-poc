"""STORY-413: Regression tests for TaskRegistry signature validation.

These tests pin the behaviour of ``TaskRegistry.register`` so that the
``TypeError: func() missing 1 required positional argument: 'coroutine'``
crash loop that hit production on 2026-04-10 cannot recur unnoticed:

- The crash originated inside ``AsyncExitStackMiddleware`` because a task
  factory with the wrong shape propagated a zero-arg invocation error into
  the ASGI middleware chain, which then failed every request at startup
  (Sentry issues 7400217484 / 7282829485 / 7282829484, 132 events).

- The fix enforces fail-fast validation at ``register`` time (import/boot),
  so a broken registration raises ``TaskRegistrationError`` long before
  FastAPI mounts middleware.

- The Sentry ``StarletteIntegration`` that amplified the original symptom is
  removed from ``backend/startup/sentry.py``; we guard that contract here
  as well so a future refactor cannot accidentally re-add it.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from task_registry import TaskRegistrationError, TaskRegistry


# ---------------------------------------------------------------------------
# Helper fakes
# ---------------------------------------------------------------------------


def _make_valid_factory():
    """A zero-arg factory that returns an asyncio.Task, the default mode."""

    async def _noop() -> None:
        return None

    async def factory() -> asyncio.Task:
        return asyncio.create_task(_noop())

    return factory


def _make_valid_coroutine():
    """A zero-arg async function, suitable for is_coroutine=True."""

    async def coroutine_fn() -> None:
        await asyncio.sleep(0)

    return coroutine_fn


# ---------------------------------------------------------------------------
# Happy paths — current lifespan registrations must keep working
# ---------------------------------------------------------------------------


def test_register_valid_factory_succeeds() -> None:
    registry = TaskRegistry()
    registry.register("ok_factory", _make_valid_factory())
    assert registry.task_count == 1


def test_register_valid_coroutine_function_succeeds() -> None:
    registry = TaskRegistry()
    registry.register("ok_coro", _make_valid_coroutine(), is_coroutine=True)
    assert registry.task_count == 1


def test_register_factory_with_default_args_is_allowed() -> None:
    """Factories with *only* defaulted positional params must still register."""
    registry = TaskRegistry()

    async def factory_with_defaults(timeout: float = 1.0) -> asyncio.Task:  # noqa: ARG001
        async def _noop() -> None:
            return None

        return asyncio.create_task(_noop())

    registry.register("ok_defaults", factory_with_defaults)
    assert registry.task_count == 1


# ---------------------------------------------------------------------------
# Regression — bad shapes must fail at register() time, never at startup
# ---------------------------------------------------------------------------


def test_register_rejects_non_callable() -> None:
    registry = TaskRegistry()
    with pytest.raises(TaskRegistrationError, match="not callable"):
        registry.register("bad", "not a function")  # type: ignore[arg-type]


def test_register_rejects_factory_with_required_positional_arg() -> None:
    """This is the exact crash loop shape from Sentry 7400217484."""
    registry = TaskRegistry()

    async def bad_factory(coroutine: Any) -> asyncio.Task:  # noqa: ARG001
        async def _noop() -> None:
            return None

        return asyncio.create_task(_noop())

    with pytest.raises(TaskRegistrationError) as exc_info:
        registry.register("bad_factory", bad_factory)

    # Must name the offending param so Sentry/Railway logs show exactly
    # which registration to fix — otherwise the blast radius is the same
    # opaque crash we just recovered from.
    assert "coroutine" in str(exc_info.value)
    assert "bad_factory" in str(exc_info.value)


def test_register_rejects_sync_function_when_is_coroutine_true() -> None:
    registry = TaskRegistry()

    def not_async() -> None:
        return None

    with pytest.raises(TaskRegistrationError, match="not an async function"):
        registry.register("sync_as_coro", not_async, is_coroutine=True)  # type: ignore[arg-type]


def test_register_error_inherits_from_typeerror() -> None:
    """Back-compat: existing ``except TypeError`` blocks keep catching the error."""
    registry = TaskRegistry()
    with pytest.raises(TypeError):
        registry.register("bad", object())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# start_all still works for mixed coroutine + factory entries
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_all_mixed_modes() -> None:
    registry = TaskRegistry()
    registry.register("factory_task", _make_valid_factory())
    registry.register("coroutine_task", _make_valid_coroutine(), is_coroutine=True)

    results = await registry.start_all()
    try:
        assert results == {"factory_task": True, "coroutine_task": True}
        assert registry.task_count == 2
    finally:
        await registry.stop_all(timeout=2.0)


# ---------------------------------------------------------------------------
# STORY-413: Sentry StarletteIntegration must stay disabled
# ---------------------------------------------------------------------------


def test_starlette_integration_not_imported_in_sentry_module() -> None:
    """Regression guard — StarletteIntegration caused the crash loop via
    its ``AsyncExitStackMiddleware`` monkeypatch. Do not re-import it.
    """
    import startup.sentry as sentry_module

    # The symbol should NOT be bound at module scope; if someone re-adds the
    # import, this test fails and forces them to justify it in review.
    assert not hasattr(sentry_module, "StarletteIntegration"), (
        "StarletteIntegration must stay disabled (STORY-413 + CRIT-SIGSEGV). "
        "See backend/startup/sentry.py:init_sentry for rationale."
    )
