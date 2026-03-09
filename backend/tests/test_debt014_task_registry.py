"""DEBT-014 SYS-006: Tests for TaskRegistry lifecycle manager."""

import asyncio
import pytest

from task_registry import TaskRegistry


@pytest.fixture
def registry():
    return TaskRegistry()


class TestTaskRegistryRegistration:
    def test_register_adds_entry(self, registry):
        async def dummy():
            return asyncio.create_task(asyncio.sleep(999))

        registry.register("test_task", dummy)
        assert registry.task_count == 1

    def test_register_multiple(self, registry):
        async def dummy():
            return asyncio.create_task(asyncio.sleep(999))

        registry.register("task_a", dummy)
        registry.register("task_b", dummy)
        registry.register("task_c", dummy)
        assert registry.task_count == 3

    def test_duplicate_registration_overwrites(self, registry):
        async def dummy1():
            return asyncio.create_task(asyncio.sleep(999))

        async def dummy2():
            return asyncio.create_task(asyncio.sleep(999))

        registry.register("same_name", dummy1)
        registry.register("same_name", dummy2)
        assert registry.task_count == 1


class TestTaskRegistryStartAll:
    @pytest.mark.asyncio
    async def test_start_all_returns_results(self, registry):
        async def start_fn():
            return asyncio.create_task(asyncio.sleep(999))

        registry.register("task_a", start_fn)
        registry.register("task_b", start_fn)

        results = await registry.start_all()
        assert results == {"task_a": True, "task_b": True}

        # Cleanup
        await registry.stop_all(timeout=1)

    @pytest.mark.asyncio
    async def test_start_all_handles_failure(self, registry):
        async def failing_start():
            raise RuntimeError("boom")

        async def good_start():
            return asyncio.create_task(asyncio.sleep(999))

        registry.register("bad_task", failing_start)
        registry.register("good_task", good_start)

        results = await registry.start_all()
        assert results["bad_task"] is False
        assert results["good_task"] is True

        await registry.stop_all(timeout=1)

    @pytest.mark.asyncio
    async def test_start_all_coroutine_mode(self, registry):
        called = False

        async def my_coroutine():
            nonlocal called
            called = True
            await asyncio.sleep(999)

        registry.register("coro_task", my_coroutine, is_coroutine=True)
        results = await registry.start_all()
        assert results["coro_task"] is True

        # Give a tick for the coroutine to start
        await asyncio.sleep(0.01)
        assert called is True

        await registry.stop_all(timeout=1)


class TestTaskRegistryStopAll:
    @pytest.mark.asyncio
    async def test_stop_all_cancels_running_tasks(self, registry):
        async def start_fn():
            return asyncio.create_task(asyncio.sleep(999))

        registry.register("task_a", start_fn)
        registry.register("task_b", start_fn)
        await registry.start_all()

        results = await registry.stop_all(timeout=2)
        assert results["task_a"] == "cancelled"
        assert results["task_b"] == "cancelled"

    @pytest.mark.asyncio
    async def test_stop_all_handles_already_done(self, registry):
        async def instant_task():
            return asyncio.create_task(asyncio.sleep(0))

        registry.register("instant", instant_task)
        await registry.start_all()
        await asyncio.sleep(0.05)  # Let it finish

        results = await registry.stop_all(timeout=1)
        assert results["instant"] == "already_done"

    @pytest.mark.asyncio
    async def test_stop_all_handles_not_started(self, registry):
        async def start_fn():
            return asyncio.create_task(asyncio.sleep(999))

        registry.register("never_started", start_fn)
        # Don't call start_all

        results = await registry.stop_all(timeout=1)
        assert results["never_started"] == "not_started"

    @pytest.mark.asyncio
    async def test_stop_all_with_short_timeout(self, registry):
        """stop_all completes within the given timeout."""
        async def start_fn():
            return asyncio.create_task(asyncio.sleep(999))

        registry.register("slow_task", start_fn)
        await registry.start_all()

        # Even with very short timeout, cancellation should work
        results = await registry.stop_all(timeout=0.5)
        assert results["slow_task"] in ("cancelled", "timeout")


class TestTaskRegistryHealth:
    def test_health_empty_registry(self, registry):
        health = registry.get_health()
        assert health["total"] == 0
        assert health["healthy"] == 0
        assert health["unhealthy"] == 0
        assert health["tasks"] == {}

    @pytest.mark.asyncio
    async def test_health_running_tasks(self, registry):
        async def start_fn():
            return asyncio.create_task(asyncio.sleep(999))

        registry.register("running_task", start_fn)
        await registry.start_all()

        health = registry.get_health()
        assert health["total"] == 1
        assert health["healthy"] == 1
        assert health["tasks"]["running_task"]["status"] == "running"
        assert "uptime_seconds" in health["tasks"]["running_task"]

        await registry.stop_all(timeout=1)

    @pytest.mark.asyncio
    async def test_health_failed_task(self, registry):
        async def failing_start():
            raise RuntimeError("startup boom")

        registry.register("failed_task", failing_start)
        await registry.start_all()

        health = registry.get_health()
        assert health["unhealthy"] == 1
        assert health["tasks"]["failed_task"]["status"] == "not_started"
        assert "startup boom" in health["tasks"]["failed_task"]["last_error"]

    @pytest.mark.asyncio
    async def test_health_crashed_task(self, registry):
        async def crashing_coroutine():
            raise ValueError("runtime crash")

        registry.register("crasher", crashing_coroutine, is_coroutine=True)
        await registry.start_all()
        await asyncio.sleep(0.05)  # Let it crash

        health = registry.get_health()
        assert health["tasks"]["crasher"]["status"] == "crashed"

    def test_get_task_returns_none_for_unknown(self, registry):
        assert registry.get_task("nonexistent") is None

    @pytest.mark.asyncio
    async def test_get_task_returns_task(self, registry):
        async def start_fn():
            return asyncio.create_task(asyncio.sleep(999))

        registry.register("my_task", start_fn)
        await registry.start_all()

        task = registry.get_task("my_task")
        assert isinstance(task, asyncio.Task)
        assert not task.done()

        await registry.stop_all(timeout=1)
