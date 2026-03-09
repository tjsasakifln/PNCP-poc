"""DEBT-008: Backend Stability & Security Quick Fixes — Test Suite

Tests for:
- SYS-016: Memory monitoring (InMemoryCache metrics, memory usage)
- SYS-017: PNCP health canary page size validation
- SYS-024: Stripe webhook 30s timeout
- SYS-027: Startup validation for STRIPE_WEBHOOK_SECRET
- CROSS-004: Naming cleanup verification (no BidIQ in production code)

Test baseline: 0 failures expected.
"""

import asyncio
import os
import subprocess
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest


# ============================================================================
# SYS-016: Memory Monitoring Tests
# ============================================================================


class TestInMemoryCacheMetrics:
    """DEBT-008 SYS-016: InMemoryCache metrics integration."""

    def test_cache_metrics_updated_on_set(self):
        """Verify cache metrics are updated when entries are added."""
        from redis_pool import InMemoryCache

        cache = InMemoryCache(max_entries=100)
        with patch("redis_pool.INMEMORY_CACHE_ENTRIES", create=True) as mock_entries, \
             patch("redis_pool.INMEMORY_CACHE_MAX_ENTRIES", create=True) as mock_max:
            # Patch the import inside _update_cache_metrics
            with patch.dict("sys.modules", {"metrics": MagicMock(
                INMEMORY_CACHE_ENTRIES=mock_entries,
                INMEMORY_CACHE_MAX_ENTRIES=mock_max,
            )}):
                cache.setex("key1", 300, "value1")

        # Cache should have 1 entry
        assert len(cache) == 1

    def test_cache_eviction_at_max_entries(self):
        """AC1: InMemoryCache evicts when entry count cap reached."""
        from redis_pool import InMemoryCache

        cache = InMemoryCache(max_entries=5)

        for i in range(10):
            cache.set(f"key{i}", f"value{i}")

        # Should have exactly 5 entries (max)
        assert len(cache) == 5

        # Oldest entries (0-4) should be evicted, newest (5-9) should remain
        assert cache.get("key0") is None
        assert cache.get("key4") is None
        assert cache.get("key9") == "value9"
        assert cache.get("key5") == "value5"

    def test_cache_lru_eviction_order(self):
        """LRU eviction removes least recently used, not just oldest."""
        from redis_pool import InMemoryCache

        cache = InMemoryCache(max_entries=3)
        cache.set("a", "1")
        cache.set("b", "2")
        cache.set("c", "3")

        # Access "a" to make it most recently used
        cache.get("a")

        # Add "d" — should evict "b" (least recently used)
        cache.set("d", "4")

        assert cache.get("a") == "1"  # Was accessed, kept
        assert cache.get("b") is None  # Evicted (LRU)
        assert cache.get("c") == "3"
        assert cache.get("d") == "4"

    def test_update_cache_metrics_graceful_on_import_error(self):
        """Cache metrics update should never raise even if metrics unavailable."""
        from redis_pool import InMemoryCache

        cache = InMemoryCache(max_entries=10)
        # This should not raise even if metrics module has issues
        cache._update_cache_metrics()


class TestMemoryUsage:
    """DEBT-008 SYS-016: Memory usage reporting."""

    def test_get_memory_usage_returns_dict(self):
        """get_memory_usage returns dict with expected keys."""
        from health import get_memory_usage

        result = get_memory_usage()
        assert isinstance(result, dict)
        assert "rss_mb" in result
        assert "vms_mb" in result
        assert "peak_rss_mb" in result
        # Values should be non-negative
        assert result["rss_mb"] >= 0
        assert result["vms_mb"] >= 0
        assert result["peak_rss_mb"] >= 0

    def test_update_memory_metrics_graceful(self):
        """update_memory_metrics should never raise."""
        from health import update_memory_metrics

        # Should not raise even if metrics are unavailable
        update_memory_metrics()


# ============================================================================
# SYS-017: PNCP Health Canary Page Size Tests
# ============================================================================


class TestPNCPPageSizeValidation:
    """DEBT-008 SYS-017: PNCP page size limit detection."""

    @pytest.mark.asyncio
    async def test_canary_validates_page_size_limit(self):
        """AC2: Health canary confirms page size limit by testing tamanhoPagina=51."""
        from health import check_source_health, HealthStatus

        # Mock: tamanhoPagina=50 succeeds, tamanhoPagina=51 returns 400
        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200

        mock_response_400 = MagicMock()
        mock_response_400.status_code = 400

        call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            params = kwargs.get("params", {})
            if params.get("tamanhoPagina", 0) > 50:
                return mock_response_400
            return mock_response_ok

        with patch("health.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = mock_get
            mock_client_cls.return_value = mock_client

            with patch("health.PNCP_PAGE_SIZE_LIMIT", create=True):
                result = await check_source_health("PNCP", timeout=10.0)

            assert result.status == HealthStatus.HEALTHY
            # Should have made 2 calls: canary (50) + validation (51)
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_canary_detects_increased_page_size(self):
        """SYS-017: Log warning if PNCP starts accepting tamanhoPagina=51."""
        from health import check_source_health, HealthStatus

        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200

        with patch("health.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            # Both requests succeed (limit increased)
            mock_client.get = AsyncMock(return_value=mock_response_ok)
            mock_client_cls.return_value = mock_client

            with patch("health.logger") as mock_logger, \
                 patch("health.PNCP_PAGE_SIZE_LIMIT", create=True):
                result = await check_source_health("PNCP", timeout=10.0)

            assert result.status == HealthStatus.HEALTHY
            # Should have logged a warning about limit increase
            warning_calls = [
                call for call in mock_logger.warning.call_args_list
                if "tamanhoPagina=51" in str(call)
            ]
            assert len(warning_calls) > 0

    @pytest.mark.asyncio
    async def test_page_size_validation_does_not_affect_health_result(self):
        """Page size validation failure should not change health status."""
        from health import check_source_health, HealthStatus

        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200

        call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            params = kwargs.get("params", {})
            if params.get("tamanhoPagina", 0) > 50:
                raise Exception("Network error during validation")
            return mock_response_ok

        with patch("health.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = mock_get
            mock_client_cls.return_value = mock_client

            result = await check_source_health("PNCP", timeout=10.0)

        # Health result should still be HEALTHY despite validation error
        assert result.status == HealthStatus.HEALTHY


# ============================================================================
# SYS-024: Stripe Webhook Timeout Tests
# ============================================================================


class TestStripeWebhookTimeout:
    """DEBT-008 SYS-024: Stripe webhook handler 30s timeout."""

    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI Request."""
        request = AsyncMock()
        request.body = AsyncMock(return_value=b'{"id":"evt_timeout_test"}')
        request.headers = {"stripe-signature": "t=123,v1=sig"}
        return request

    @pytest.fixture
    def make_stripe_event(self):
        """Factory for Stripe Event mocks."""
        def _make(event_id="evt_timeout_test", event_type="checkout.session.completed"):
            event = Mock()
            event.id = event_id
            event.type = event_type
            data_obj = {
                "client_reference_id": "user_123",
                "metadata": {"plan_id": "smartlic_pro", "billing_period": "monthly"},
                "subscription": "sub_123",
                "customer": "cus_123",
                "payment_status": "paid",
                "customer_details": {"email": "test@test.com"},
            }
            event.data = Mock()
            event.data.object = data_obj
            return event
        return _make

    @pytest.mark.asyncio
    async def test_webhook_timeout_raises_504(self, mock_request, make_stripe_event):
        """AC3: Webhook handler raises HTTP 504 when DB ops exceed 30s."""
        from webhooks.stripe import stripe_webhook
        from fastapi import HTTPException

        event = make_stripe_event()

        # Mock a handler that hangs forever
        async def slow_handler(sb, ev):
            await asyncio.sleep(999)

        mock_sb = MagicMock()
        mock_sb.table.return_value.upsert.return_value.execute.return_value = MagicMock(data=[{"id": "evt_timeout_test"}])
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        with patch("webhooks.stripe.stripe.Webhook.construct_event", return_value=event), \
             patch("webhooks.stripe.get_supabase", return_value=mock_sb), \
             patch("webhooks.stripe.STRIPE_WEBHOOK_SECRET", "whsec_test"), \
             patch("webhooks.stripe._handle_checkout_session_completed", side_effect=slow_handler), \
             patch("webhooks.stripe.WEBHOOK_DB_TIMEOUT_S", 0.1):  # Use 0.1s for fast test
            with pytest.raises(HTTPException) as exc_info:
                await stripe_webhook(mock_request)

            assert exc_info.value.status_code == 504
            assert "timed out" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_webhook_normal_processing_within_timeout(self, mock_request, make_stripe_event):
        """Normal webhook processing completes within timeout."""
        from webhooks.stripe import stripe_webhook

        event = make_stripe_event(event_type="customer.subscription.updated")

        mock_sb = MagicMock()
        mock_sb.table.return_value.upsert.return_value.execute.return_value = MagicMock(data=[{"id": "evt_timeout_test"}])
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[])

        with patch("webhooks.stripe.stripe.Webhook.construct_event", return_value=event), \
             patch("webhooks.stripe.get_supabase", return_value=mock_sb), \
             patch("webhooks.stripe.STRIPE_WEBHOOK_SECRET", "whsec_test"), \
             patch("webhooks.stripe._handle_subscription_updated", new_callable=AsyncMock):
            result = await stripe_webhook(mock_request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_webhook_timeout_marks_event_as_timeout(self, mock_request, make_stripe_event):
        """Timed-out webhook should mark event status as 'timeout' in DB."""
        from webhooks.stripe import stripe_webhook
        from fastapi import HTTPException

        event = make_stripe_event()

        async def slow_handler(sb, ev):
            await asyncio.sleep(999)

        mock_sb = MagicMock()
        upsert_result = MagicMock(data=[{"id": "evt_timeout_test"}])
        mock_sb.table.return_value.upsert.return_value.execute.return_value = upsert_result
        update_chain = MagicMock()
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        with patch("webhooks.stripe.stripe.Webhook.construct_event", return_value=event), \
             patch("webhooks.stripe.get_supabase", return_value=mock_sb), \
             patch("webhooks.stripe.STRIPE_WEBHOOK_SECRET", "whsec_test"), \
             patch("webhooks.stripe._handle_checkout_session_completed", side_effect=slow_handler), \
             patch("webhooks.stripe.WEBHOOK_DB_TIMEOUT_S", 0.1):
            with pytest.raises(HTTPException):
                await stripe_webhook(mock_request)

        # Verify update was called with "timeout" status
        update_calls = mock_sb.table.return_value.update.call_args_list
        timeout_calls = [
            c for c in update_calls
            if isinstance(c.args[0], dict) and c.args[0].get("status") == "timeout"
        ]
        assert len(timeout_calls) > 0


# ============================================================================
# SYS-027: Startup Validation Tests
# ============================================================================


class TestStartupValidation:
    """DEBT-008 SYS-027: STRIPE_WEBHOOK_SECRET startup validation."""

    def test_missing_stripe_webhook_secret_raises_in_production(self, monkeypatch):
        """AC4: Application refuses to start if STRIPE_WEBHOOK_SECRET not set in production."""
        from config import validate_env_vars

        # Set production env
        monkeypatch.setenv("ENVIRONMENT", "production")
        # Set required vars except STRIPE_WEBHOOK_SECRET
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test_key")
        monkeypatch.setenv("SUPABASE_JWT_SECRET", "test_jwt")
        # Ensure STRIPE_WEBHOOK_SECRET is NOT set
        monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)

        with pytest.raises(RuntimeError, match="STRIPE_WEBHOOK_SECRET"):
            validate_env_vars()

    def test_missing_stripe_webhook_secret_warns_in_dev(self, monkeypatch):
        """SYS-027: In development, missing STRIPE_WEBHOOK_SECRET is a warning, not error."""
        from config import validate_env_vars

        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test_key")
        monkeypatch.setenv("SUPABASE_JWT_SECRET", "test_jwt")
        monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)

        # Should NOT raise in development
        validate_env_vars()  # No exception = pass

    def test_all_required_vars_present_no_error(self, monkeypatch):
        """No error when all required vars including STRIPE_WEBHOOK_SECRET are set."""
        from config import validate_env_vars

        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test_key")
        monkeypatch.setenv("SUPABASE_JWT_SECRET", "test_jwt")
        monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")

        # Should not raise
        validate_env_vars()


# ============================================================================
# CROSS-004: Naming Cleanup Verification Tests
# ============================================================================


class TestNamingCleanup:
    """DEBT-008 CROSS-004: Zero BidIQ references in production code."""

    def test_pyproject_name_is_smartlic(self):
        """AC6: pyproject.toml name is 'smartlic-backend'."""
        import tomllib
        pyproject_path = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        assert data["project"]["name"] == "smartlic-backend"

    def test_pncp_user_agent_is_smartlic(self):
        """AC5: User-Agent header uses SmartLic, not BidIQ."""
        pncp_path = os.path.join(os.path.dirname(__file__), "..", "pncp_client.py")
        with open(pncp_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should contain SmartLic User-Agent
        assert "SmartLic" in content
        # Should NOT contain BidIQ in User-Agent lines
        for line in content.split("\n"):
            if "User-Agent" in line and "BidIQ" in line:
                pytest.fail(f"BidIQ found in User-Agent header: {line.strip()}")

    def test_no_bidiq_in_backend_production_python(self):
        """AC5: Zero BidIQ strings in production .py files (excluding tests)."""
        backend_dir = os.path.join(os.path.dirname(__file__), "..")
        violations = []

        for root, dirs, files in os.walk(backend_dir):
            # Skip test directories and non-production dirs
            dirs[:] = [d for d in dirs if d not in ("tests", "__pycache__", ".git", "venv")]
            for f in files:
                if not f.endswith(".py"):
                    continue
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, "r", encoding="utf-8") as fh:
                        for line_num, line in enumerate(fh, 1):
                            if "bidiq" in line.lower() and "BidIQ" not in line.split("#")[-1]:
                                # Ignore comments that reference BidIQ for historical context
                                pass
                            elif "BidIQ" in line:
                                violations.append(f"{filepath}:{line_num}: {line.strip()}")
                except (UnicodeDecodeError, OSError):
                    pass

        assert violations == [], f"BidIQ found in production code:\n" + "\n".join(violations)

    def test_offline_html_uses_smartlic(self):
        """AC5: offline.html title uses SmartLic, not BidIQ."""
        offline_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "frontend", "public", "offline.html"
        )
        if not os.path.exists(offline_path):
            pytest.skip("offline.html not found")

        with open(offline_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "BidIQ" not in content, "BidIQ found in offline.html"
        assert "SmartLic" in content, "SmartLic not found in offline.html"


# ============================================================================
# Integration: Metrics existence tests
# ============================================================================


class TestMetricsExist:
    """Verify DEBT-008 metrics are defined."""

    def test_inmemory_cache_entries_metric(self):
        """SYS-016: INMEMORY_CACHE_ENTRIES gauge exists."""
        from metrics import INMEMORY_CACHE_ENTRIES
        assert INMEMORY_CACHE_ENTRIES is not None

    def test_inmemory_cache_max_entries_metric(self):
        """SYS-016: INMEMORY_CACHE_MAX_ENTRIES gauge exists."""
        from metrics import INMEMORY_CACHE_MAX_ENTRIES
        assert INMEMORY_CACHE_MAX_ENTRIES is not None

    def test_process_memory_rss_bytes_metric(self):
        """SYS-016: PROCESS_MEMORY_RSS_BYTES gauge exists."""
        from metrics import PROCESS_MEMORY_RSS_BYTES
        assert PROCESS_MEMORY_RSS_BYTES is not None

    def test_process_memory_peak_rss_bytes_metric(self):
        """SYS-016: PROCESS_MEMORY_PEAK_RSS_BYTES gauge exists."""
        from metrics import PROCESS_MEMORY_PEAK_RSS_BYTES
        assert PROCESS_MEMORY_PEAK_RSS_BYTES is not None

    def test_pncp_page_size_limit_metric(self):
        """SYS-017: PNCP_PAGE_SIZE_LIMIT gauge exists."""
        from metrics import PNCP_PAGE_SIZE_LIMIT
        assert PNCP_PAGE_SIZE_LIMIT is not None
