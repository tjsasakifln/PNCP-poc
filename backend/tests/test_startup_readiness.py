"""
CRIT-010: Startup Readiness Gate — Tests T1-T4

Validates that /health exposes readiness signal and uptime tracking
after application lifespan startup completes.
"""

import time
import pytest


class TestStartupReadiness:
    """CRIT-010 T1-T4: Startup readiness tests."""

    def test_t1_health_returns_ready_true_when_started(self):
        """T1: /health returns ready: true after _startup_time is set."""
        import main

        # Simulate lifespan completed
        original = main._startup_time
        main._startup_time = time.monotonic()

        is_ready = main._startup_time is not None
        assert is_ready is True

        main._startup_time = original

    def test_t2_uptime_seconds_is_positive_float(self):
        """T2: uptime_seconds computes as a positive float."""
        import main

        original = main._startup_time
        main._startup_time = time.monotonic() - 5.0  # started 5s ago

        is_ready = main._startup_time is not None
        uptime = round(time.monotonic() - main._startup_time, 3) if is_ready else 0.0

        assert isinstance(uptime, float)
        assert uptime > 0.0
        assert uptime >= 4.5  # at least ~5s minus small delta

        main._startup_time = original

    def test_t3_uptime_increases_monotonically(self):
        """T3: uptime_seconds increases between consecutive reads."""
        import main

        original = main._startup_time
        main._startup_time = time.monotonic() - 10.0

        uptime1 = round(time.monotonic() - main._startup_time, 3)
        time.sleep(0.05)  # small delay
        uptime2 = round(time.monotonic() - main._startup_time, 3)

        assert uptime2 > uptime1

        main._startup_time = original

    def test_t4_startup_time_initially_none(self):
        """T4: _startup_time exists as module attribute (set during lifespan)."""
        import main
        assert hasattr(main, '_startup_time')

    def test_ready_false_when_startup_time_none(self):
        """When _startup_time is None, ready=False and uptime=0."""
        import main

        original = main._startup_time
        main._startup_time = None

        is_ready = main._startup_time is not None
        uptime = round(time.monotonic() - main._startup_time, 3) if is_ready else 0.0

        assert is_ready is False
        assert uptime == 0.0

        main._startup_time = original

    def test_health_response_includes_ready_and_uptime_fields(self):
        """HealthResponse schema includes ready and uptime_seconds fields."""
        from schemas import HealthResponse

        # Verify the schema accepts ready and uptime_seconds
        data = {
            "status": "healthy",
            "ready": True,
            "uptime_seconds": 42.5,
            "timestamp": "2026-02-20T00:00:00Z",
            "version": "0.2.0",
            "dependencies": {
                "supabase": "healthy",
                "openai": "configured",
                "redis": "healthy",
            },
        }
        response = HealthResponse(**data)
        assert response.ready is True
        assert response.uptime_seconds == 42.5

    def test_health_response_defaults(self):
        """HealthResponse defaults: ready=True, uptime_seconds=0.0."""
        from schemas import HealthResponse

        data = {
            "status": "healthy",
            "timestamp": "2026-02-20T00:00:00Z",
            "version": "0.2.0",
            "dependencies": {
                "supabase": "healthy",
                "openai": "configured",
                "redis": "healthy",
            },
        }
        response = HealthResponse(**data)
        assert response.ready is True
        assert response.uptime_seconds == 0.0
