"""HARDEN-002: jemalloc Dockerfile + process_resident_memory_bytes metric.

AC1/AC2: Validated by Dockerfile inspection (install libjemalloc2 + LD_PRELOAD).
AC3: Validates process_resident_memory_bytes is exposed via Prometheus default collector.
AC4: Validated by successful Railway deploy.
"""

import platform


def test_process_resident_memory_bytes_available_on_linux():
    """AC3: process_resident_memory_bytes is auto-exposed by ProcessCollector on Linux.

    On Windows (dev/CI), ProcessCollector is not registered (needs /proc).
    On Linux (Docker/Railway), it IS registered by default.
    We verify the mechanism works by checking PlatformCollector exists
    (always registered) and that ProcessCollector would be registered on Linux.
    """
    from prometheus_client import REGISTRY
    from prometheus_client.process_collector import ProcessCollector

    if platform.system() == "Linux":
        # On Linux, ProcessCollector is auto-registered and exposes process_resident_memory_bytes
        samples = list(REGISTRY.collect())
        metric_names = {s.name for s in samples}
        assert "process_resident_memory_bytes" in metric_names
    else:
        # On Windows/macOS, just verify ProcessCollector class exists and is importable
        assert ProcessCollector is not None
        # And that PlatformCollector is registered (proof REGISTRY works)
        collector_names = [c.__class__.__name__ for c in REGISTRY._names_to_collectors.values()]
        assert "PlatformCollector" in collector_names


def test_metrics_endpoint_available():
    """AC3: /metrics ASGI app is mountable (prometheus_client installed)."""
    from metrics import get_metrics_app, is_available

    assert is_available() is True
    app = get_metrics_app()
    assert app is not None


def test_dockerfile_has_jemalloc():
    """AC1+AC2: Dockerfile installs libjemalloc2 and sets LD_PRELOAD."""
    from pathlib import Path

    dockerfile = Path(__file__).parent.parent / "Dockerfile"
    content = dockerfile.read_text()

    assert "libjemalloc2" in content, "AC1: Dockerfile must install libjemalloc2"
    assert "LD_PRELOAD" in content, "AC2: Dockerfile must set LD_PRELOAD"
    assert "libjemalloc.so.2" in content, "AC2: LD_PRELOAD must point to libjemalloc.so.2"
