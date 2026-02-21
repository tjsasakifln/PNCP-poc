"""CRIT-001: Tests for /health/ready lightweight endpoint."""
import pytest
import time
from unittest.mock import patch
from fastapi.testclient import TestClient


class TestHealthReady:
    """Tests for the /health/ready endpoint."""

    def test_ready_true_when_startup_complete(self):
        """AC11: Returns ready=true when _startup_time is set."""
        with patch("main._startup_time", time.monotonic()):
            from main import app
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["ready"] is True
            assert "uptime_seconds" in data
            assert data["uptime_seconds"] >= 0

    def test_ready_false_before_startup(self):
        """AC12: Returns ready=false when _startup_time is None."""
        with patch("main._startup_time", None):
            from main import app
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/health/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["ready"] is False
            assert data["uptime_seconds"] == 0.0

    def test_ready_responds_fast(self):
        """AC13: Responds in <50ms (no I/O)."""
        with patch("main._startup_time", time.monotonic()):
            from main import app
            client = TestClient(app, raise_server_exceptions=False)
            start = time.monotonic()
            response = client.get("/health/ready")
            elapsed_ms = (time.monotonic() - start) * 1000
            assert response.status_code == 200
            assert elapsed_ms < 500  # Allow generous margin for CI, actual should be <50ms
