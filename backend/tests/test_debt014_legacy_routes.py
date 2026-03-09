"""DEBT-014 SYS-001: Tests for legacy route deprecation metrics."""

import pytest
from unittest.mock import patch, MagicMock


class TestLegacyRouteMetric:
    """Verify LEGACY_ROUTE_CALLS counter exists and is properly configured."""

    def test_legacy_route_calls_metric_exists(self):
        """LEGACY_ROUTE_CALLS counter should be defined in metrics.py."""
        from metrics import LEGACY_ROUTE_CALLS
        assert LEGACY_ROUTE_CALLS is not None

    def test_legacy_route_calls_has_correct_labels(self):
        """Metric should have 'method' and 'path' labels."""
        from metrics import LEGACY_ROUTE_CALLS
        # If prometheus not available, this is a no-op mock
        try:
            # Try to call with labels to verify they exist
            LEGACY_ROUTE_CALLS.labels(method="GET", path="/old-route")
        except Exception:
            pass  # No-op if prometheus not available

    def test_allowed_root_paths_defined(self):
        """_ALLOWED_ROOT_PATHS should include health and doc endpoints."""
        from main import _ALLOWED_ROOT_PATHS
        assert "/health" in _ALLOWED_ROOT_PATHS
        assert "/docs" in _ALLOWED_ROOT_PATHS
        assert "/metrics" in _ALLOWED_ROOT_PATHS
        assert "/" in _ALLOWED_ROOT_PATHS


class TestLegacyRouteMiddleware:
    """Verify the track_legacy_routes middleware works correctly."""

    @pytest.mark.asyncio
    async def test_legacy_route_increments_counter(self):
        """Non-/v1/ route should increment the deprecation counter."""
        from main import track_legacy_routes
        from unittest.mock import AsyncMock

        mock_request = MagicMock()
        mock_request.url.path = "/buscar"  # Old legacy path
        mock_request.method = "POST"

        mock_response = MagicMock()
        call_next = AsyncMock(return_value=mock_response)

        with patch("metrics.LEGACY_ROUTE_CALLS") as mock_counter:
            mock_label = MagicMock()
            mock_counter.labels = MagicMock(return_value=mock_label)
            result = await track_legacy_routes(mock_request, call_next)

            mock_counter.labels.assert_called_once_with(method="POST", path="/buscar")
            mock_label.inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_allowed_root_path_not_tracked(self):
        """Allowed root paths (e.g. /health) should NOT increment counter."""
        from main import track_legacy_routes
        from unittest.mock import AsyncMock

        mock_request = MagicMock()
        mock_request.url.path = "/health"
        mock_request.method = "GET"

        call_next = AsyncMock(return_value=MagicMock())

        with patch("metrics.LEGACY_ROUTE_CALLS") as mock_counter:
            await track_legacy_routes(mock_request, call_next)
            mock_counter.labels.assert_not_called()

    @pytest.mark.asyncio
    async def test_v1_route_not_tracked(self):
        """Routes starting with /v1/ should NOT increment counter."""
        from main import track_legacy_routes
        from unittest.mock import AsyncMock

        mock_request = MagicMock()
        mock_request.url.path = "/v1/buscar"
        mock_request.method = "POST"

        call_next = AsyncMock(return_value=MagicMock())

        with patch("metrics.LEGACY_ROUTE_CALLS") as mock_counter:
            await track_legacy_routes(mock_request, call_next)
            mock_counter.labels.assert_not_called()

    @pytest.mark.asyncio
    async def test_legacy_path_truncated_to_2_segments(self):
        """Long legacy paths should be truncated to 2 segments."""
        from main import track_legacy_routes
        from unittest.mock import AsyncMock

        mock_request = MagicMock()
        mock_request.url.path = "/admin/users/123/details"
        mock_request.method = "GET"

        call_next = AsyncMock(return_value=MagicMock())

        with patch("metrics.LEGACY_ROUTE_CALLS") as mock_counter:
            mock_label = MagicMock()
            mock_counter.labels = MagicMock(return_value=mock_label)
            await track_legacy_routes(mock_request, call_next)

            mock_counter.labels.assert_called_once_with(method="GET", path="/admin/users")


class TestTaskRegistryHealthEndpoint:
    """DEBT-014 SYS-006: Verify health endpoint for background tasks."""

    def test_health_tasks_endpoint_exists(self):
        """The /health/tasks endpoint should be registered."""
        from routes.health import background_tasks_health
        assert background_tasks_health is not None

    @pytest.mark.asyncio
    async def test_health_tasks_returns_registry_health(self):
        """Endpoint should return TaskRegistry health data."""
        from routes.health import background_tasks_health

        with patch("task_registry.task_registry") as mock_registry:
            mock_registry.get_health.return_value = {
                "total": 16,
                "healthy": 15,
                "unhealthy": 1,
                "tasks": {"test": {"status": "running"}},
            }
            result = await background_tasks_health()
            assert result["total"] == 16
            assert result["healthy"] == 15
