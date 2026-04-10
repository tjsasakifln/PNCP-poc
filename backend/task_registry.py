"""DEBT-014 SYS-006: Centralized background task lifecycle manager.

TaskRegistry replaces ad-hoc task management in lifespan with a single
registry that handles startup, shutdown, and health reporting for all
background tasks.

STORY-413: Adds fail-fast signature validation at register time so that
a task with the wrong callable shape raises immediately (at import/boot)
instead of crashing the ASGI middleware stack later. Also logs structured
diagnostics before start_all() so any regression shows up in Sentry with
the name of the offending task instead of an opaque TypeError deep inside
``AsyncExitStackMiddleware``.

Usage:
    registry = TaskRegistry()
    registry.register("cache_cleanup", start_cache_cleanup_task)
    registry.register("tracker_cleanup", _periodic_tracker_cleanup, is_coroutine=True)
    await registry.start_all()
    ...
    await registry.stop_all(timeout=10)
"""

import asyncio
import inspect
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskRegistrationError(TypeError):
    """STORY-413: Raised when a background task is registered with a shape
    incompatible with its declared mode (coroutine vs task factory).

    Inherits from TypeError so that existing exception handlers keep working,
    but exposes a distinct class so upstream code can disambiguate.
    """


@dataclass
class _TaskEntry:
    """Internal record for a registered background task."""

    name: str
    # Either an async fn returning Task, or a coroutine to wrap in create_task
    start_fn: Callable[..., Coroutine]
    is_coroutine: bool = False  # True = wrap in asyncio.create_task()
    task: Optional[asyncio.Task] = None
    started_at: Optional[float] = None
    error: Optional[str] = None


class TaskRegistry:
    """Centralized registry for background task lifecycle management.

    Supports two patterns:
      1. ``start_fn`` returns an ``asyncio.Task`` (e.g., ``start_cache_cleanup_task``)
      2. ``start_fn`` is a plain coroutine function wrapped via ``asyncio.create_task``
         (e.g., ``_periodic_tracker_cleanup``) — set ``is_coroutine=True``.
    """

    def __init__(self) -> None:
        self._entries: Dict[str, _TaskEntry] = {}
        self._start_order: List[str] = []

    def register(
        self,
        name: str,
        start_fn: Callable[..., Coroutine],
        *,
        is_coroutine: bool = False,
    ) -> None:
        """Register a background task.

        Args:
            name: Unique identifier (e.g. ``"cache_cleanup"``).
            start_fn: Async callable. If ``is_coroutine=False`` (default),
                calling it should return an ``asyncio.Task``.  If ``True``,
                calling it returns a coroutine wrapped with ``create_task``.

        Raises:
            TaskRegistrationError: If ``start_fn`` is not callable, is not an
                async function when ``is_coroutine=True``, or has required
                positional parameters that would fail the zero-arg invocation
                in ``start_all``. STORY-413 — fail fast at import/boot to
                prevent crash loops inside the ASGI middleware stack.
        """
        if not callable(start_fn):
            raise TaskRegistrationError(
                f"TaskRegistry.register('{name}'): start_fn is not callable "
                f"(got {type(start_fn).__name__})"
            )

        # STORY-413: Validate that the shape of start_fn matches the declared
        # mode. The registry invokes ``start_fn()`` with zero arguments in
        # start_all(), so any required positional parameter would raise a
        # TypeError("... missing 1 required positional argument: ...") at
        # startup — which is exactly the crash loop we are protecting against.
        try:
            sig = inspect.signature(start_fn)
        except (TypeError, ValueError):
            sig = None

        if sig is not None:
            required_positional = [
                p
                for p in sig.parameters.values()
                if p.kind
                in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
                and p.default is inspect.Parameter.empty
            ]
            if required_positional:
                raise TaskRegistrationError(
                    f"TaskRegistry.register('{name}'): start_fn has required "
                    f"positional arguments {[p.name for p in required_positional]!r}; "
                    f"registry invokes start_fn() with zero arguments. "
                    f"Wrap the factory in a zero-arg lambda or set defaults."
                )

        if is_coroutine and not inspect.iscoroutinefunction(start_fn):
            raise TaskRegistrationError(
                f"TaskRegistry.register('{name}'): is_coroutine=True but "
                f"start_fn is not an async function "
                f"(inspect.iscoroutinefunction returned False). "
                f"Either pass an `async def` or set is_coroutine=False."
            )

        if name in self._entries:
            logger.warning("TaskRegistry: duplicate registration for '%s' — overwriting", name)
        self._entries[name] = _TaskEntry(name=name, start_fn=start_fn, is_coroutine=is_coroutine)
        self._start_order.append(name)

    async def start_all(self) -> Dict[str, bool]:
        """Start all registered tasks in registration order.

        Returns:
            Dict mapping task name to success (True) or failure (False).
        """
        # STORY-413: Structured pre-start log so that if the middleware stack
        # crashes during task scheduling, Sentry/Railway logs show exactly
        # which tasks were about to be started and in which mode.
        logger.info(
            "TaskRegistry.start_all: about to start %d tasks: %s",
            len(self._start_order),
            [
                {
                    "name": n,
                    "mode": "coroutine" if self._entries[n].is_coroutine else "factory",
                    "qualname": getattr(self._entries[n].start_fn, "__qualname__", repr(self._entries[n].start_fn)),
                }
                for n in self._start_order
            ],
        )

        results: Dict[str, bool] = {}
        for name in self._start_order:
            entry = self._entries[name]
            try:
                if entry.is_coroutine:
                    entry.task = asyncio.create_task(entry.start_fn())
                else:
                    entry.task = await entry.start_fn()
                entry.started_at = time.monotonic()
                entry.error = None
                results[name] = True
                logger.debug("TaskRegistry: started '%s'", name)
            except Exception as e:
                entry.error = f"{type(e).__name__}: {e}"
                results[name] = False
                logger.error(
                    "TaskRegistry: failed to start '%s' (mode=%s, qualname=%s): %s",
                    name,
                    "coroutine" if entry.is_coroutine else "factory",
                    getattr(entry.start_fn, "__qualname__", repr(entry.start_fn)),
                    entry.error,
                )

        started = sum(1 for v in results.values() if v)
        failed = sum(1 for v in results.values() if not v)
        logger.info(
            "TaskRegistry: %d/%d tasks started (%d failed)",
            started, len(results), failed,
        )
        return results

    async def stop_all(self, timeout: float = 10.0) -> Dict[str, str]:
        """Cancel all running tasks and wait for completion.

        Args:
            timeout: Max seconds to wait for tasks to finish.

        Returns:
            Dict mapping task name to outcome: "cancelled", "already_done",
            "timeout", or "error:<msg>".
        """
        results: Dict[str, str] = {}
        tasks_to_wait: List[asyncio.Task] = []

        # Cancel all
        for name in reversed(self._start_order):
            entry = self._entries[name]
            if entry.task is None:
                results[name] = "not_started"
                continue
            if entry.task.done():
                results[name] = "already_done"
                continue
            entry.task.cancel()
            tasks_to_wait.append(entry.task)
            results[name] = "cancelling"

        # Wait with timeout
        if tasks_to_wait:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks_to_wait, return_exceptions=True),
                    timeout=timeout,
                )
                # Mark all cancelling as cancelled
                for name in results:
                    if results[name] == "cancelling":
                        results[name] = "cancelled"
            except asyncio.TimeoutError:
                for name in results:
                    if results[name] == "cancelling":
                        results[name] = "timeout"
                logger.warning("TaskRegistry: stop_all timed out after %.1fs", timeout)

        cancelled_count = sum(1 for v in results.values() if v in ("cancelled", "already_done"))
        logger.info(
            "TaskRegistry: %d/%d tasks stopped",
            cancelled_count, len(results),
        )
        return results

    def get_health(self) -> Dict[str, Any]:
        """Return health status of all registered tasks.

        Returns:
            Dict with per-task status and overall summary.
        """
        now = time.monotonic()
        tasks: Dict[str, Dict[str, Any]] = {}
        healthy = 0
        unhealthy = 0

        for name, entry in self._entries.items():
            if entry.task is None:
                status = "not_started"
                unhealthy += 1
            elif entry.task.done():
                exc = entry.task.exception() if not entry.task.cancelled() else None
                if entry.task.cancelled():
                    status = "cancelled"
                elif exc:
                    status = "crashed"
                    unhealthy += 1
                else:
                    status = "completed"
                    healthy += 1
            else:
                status = "running"
                healthy += 1

            info: Dict[str, Any] = {"status": status}
            if entry.started_at:
                info["uptime_seconds"] = round(now - entry.started_at, 1)
            if entry.error:
                info["last_error"] = entry.error

            tasks[name] = info

        return {
            "total": len(self._entries),
            "healthy": healthy,
            "unhealthy": unhealthy,
            "tasks": tasks,
        }

    @property
    def task_count(self) -> int:
        return len(self._entries)

    def get_task(self, name: str) -> Optional[asyncio.Task]:
        """Get the asyncio.Task for a registered entry (or None)."""
        entry = self._entries.get(name)
        return entry.task if entry else None


# Global singleton — populated during lifespan startup
task_registry = TaskRegistry()
