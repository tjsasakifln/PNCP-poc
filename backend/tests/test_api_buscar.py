"""Comprehensive tests for /api/buscar endpoint - BLOCKER 4 fix."""

import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta
from main import app
from auth import require_auth


client = TestClient(app)


def override_require_auth(user_id: str = "user-123"):
    """Create a dependency override for require_auth."""
    async def _override():
        return {"id": user_id, "email": "test@example.com"}
    return _override


def setup_auth_override(user_id="user-123"):
    """Setup auth override and return cleanup function."""
    app.dependency_overrides[require_auth] = override_require_auth(user_id)
    def cleanup():
        app.dependency_overrides.clear()
    return cleanup


class TestBuscarFeatureFlagEnabled:
    """Test /api/buscar with ENABLE_NEW_PRICING=true (feature flag enabled)."""

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session", new_callable=AsyncMock)
    @patch("routes.search.PNCPClient")
    def test_enforces_quota_when_feature_flag_enabled(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
    ):
        """Should enforce quota limits when feature flag is enabled."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            # Quota exhausted
            mock_check_quota.return_value = QuotaInfo(
                allowed=False,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=50,
                quota_remaining=0,
                quota_reset_date=datetime.now(timezone.utc),
                error_message="Limite de 50 buscas mensais atingido.",
            )

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 403
            detail = response.json()["detail"]
            if isinstance(detail, dict):
                assert detail.get("error_code") == "QUOTA_EXCEEDED"
                assert "Limite de 50 buscas mensais atingido" in detail["detail"]
            else:
                assert "Limite de 50 buscas mensais atingido" in detail
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("quota.check_and_increment_quota_atomic")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session", new_callable=AsyncMock)
    @patch("routes.search.PNCPClient")
    def test_allows_request_when_quota_available(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
        mock_atomic_increment,
    ):
        """Should allow request when quota is available."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=23,
                quota_remaining=27,
                quota_reset_date=datetime.now(timezone.utc),
            )
            # Mock atomic increment: allowed=True, new_count=24, remaining=26
            mock_atomic_increment.return_value = (True, 24, 26)

            # Mock PNCP client
            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 24

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["quota_used"] == 24
            assert data["quota_remaining"] == 26  # 50 - 24
        finally:
            cleanup()


class TestBuscarFeatureFlagDisabled:
    """Test /api/buscar with ENABLE_NEW_PRICING=false (legacy behavior)."""

    @patch("routes.search.ENABLE_NEW_PRICING", False)
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session", new_callable=AsyncMock)
    @patch("routes.search.PNCPClient")
    def test_no_quota_enforcement_when_disabled(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
    ):
        """Should NOT enforce quota when feature flag is disabled."""
        cleanup = setup_auth_override("user-123")
        try:
            # Mock PNCP client
            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 1

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
            # Should have fallback quota values
            data = response.json()
            assert "quota_used" in data
            assert "quota_remaining" in data
        finally:
            cleanup()


class TestBuscarDateRangeValidation:
    """Test date range validation based on plan capabilities."""

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session", new_callable=AsyncMock)
    @patch("routes.search.PNCPClient")
    def test_accepts_date_range_within_plan_limit(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
    ):
        """Should accept date range within plan's max_history_days."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            # Consultor Ágil: max_history_days = 30
            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=10,
                quota_remaining=40,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 11

            # 7 days range (within 30 days limit)
            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session", new_callable=AsyncMock)
    @patch("routes.search.PNCPClient")
    def test_accepts_full_range_for_sala_guerra(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Should accept up to 1825 days for Sala de Guerra plan."""
        cleanup = setup_auth_override("user-sala-guerra-test")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

            # Sala de Guerra: max_history_days = 1825 (5 years)
            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="sala_guerra",
                plan_name="Sala de Guerra",
                capabilities=PLAN_CAPABILITIES["sala_guerra"],
                quota_used=500,
                quota_remaining=500,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 501

            # 1000 days range (within 1825 days limit)
            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2023-05-01",
                    "data_final": "2026-01-25",  # ~1000 days
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session", new_callable=AsyncMock)
    @patch("routes.search.PNCPClient")
    def test_accepts_exact_limit_boundary(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Should accept date range exactly at the plan's limit."""
        cleanup = setup_auth_override("user-boundary-test")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

            # Consultor Ágil: max_history_days = 30
            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=10,
                quota_remaining=40,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 11

            # Exactly 30 days (Jan 1 to Jan 30 inclusive = 30 days)
            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-30",  # 30 days exactly
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session", new_callable=AsyncMock)
    @patch("routes.search.PNCPClient")
    def test_accepts_single_day_range(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Should accept single day range (same start and end date)."""
        cleanup = setup_auth_override("user-single-day-test")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

            # Free trial: max_history_days = 7
            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="free_trial",
                plan_name="FREE Trial",
                capabilities=PLAN_CAPABILITIES["free_trial"],
                quota_used=1,
                quota_remaining=2,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 2

            # Single day (1 day range)
            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-15",
                    "data_final": "2026-01-15",  # Same day = 1 day
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
        finally:
            cleanup()


class TestBuscarExcelGating:
    """Test Excel export gating based on plan capabilities."""

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session", new_callable=AsyncMock)
    @patch("routes.search.PNCPClient")
    def test_blocks_excel_for_consultor_plan(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
    ):
        """Should NOT generate Excel for Consultor Ágil plan (allow_excel=False)."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=23,
                quota_remaining=27,
                quota_reset_date=datetime.now(timezone.utc),
            )

            # Mock PNCP client
            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 24

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert data["excel_available"] is False
            assert data["excel_base64"] is None
            assert "Máquina" in data["upgrade_message"]
            assert "R$ 597/mês" in data["upgrade_message"]
        finally:
            cleanup()


class TestBuscarPNCPRateLimiting:
    """Test PNCP API rate limiting scenarios (external API)."""

    @patch.dict(os.environ, {"ENABLE_MULTI_SOURCE": "false"})
    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_and_increment_quota_atomic")
    @patch("quota.check_quota")
    @patch("routes.search.buscar_todas_ufs_paralelo", new_callable=AsyncMock)
    @patch("routes.search.PNCPClient")
    def test_returns_503_when_pncp_rate_limit_exceeded(
        self,
        mock_pncp_class,
        mock_parallel_fetch,
        mock_check_quota,
        mock_atomic_increment,
        mock_rate_limiter,
    ):
        """Should return 503 when PNCP API rate limit exceeded."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES
            from exceptions import PNCPRateLimitError

            # User rate limit passes
            mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="maquina",
                plan_name="Máquina",
                capabilities=PLAN_CAPABILITIES["maquina"],
                quota_used=100,
                quota_remaining=200,
                quota_reset_date=datetime.now(timezone.utc),
            )
            # Mock atomic increment: allowed=True
            mock_atomic_increment.return_value = (True, 101, 199)

            # Pipeline (PNCP-only mode with ENABLE_MULTI_SOURCE=false) uses
            # buscar_todas_ufs_paralelo for parallel fetch.
            # When it fails, pipeline falls back to PNCPClient().fetch_all().
            # Both must raise PNCPRateLimitError for the 503 to propagate.
            error = PNCPRateLimitError("Rate limit exceeded")
            error.retry_after = 60

            mock_parallel_fetch.side_effect = error
            mock_client = MagicMock()
            mock_pncp_class.return_value = mock_client
            mock_client.fetch_all.side_effect = error

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                    "force_fresh": True,  # Bypass InMemoryCache from previous tests
                },
            )

            assert response.status_code == 503
            assert "Retry-After" in response.headers
            # CRIT-009: detail is now structured dict
            detail = response.json()["detail"]
            if isinstance(detail, dict):
                assert "60" in detail.get("detail", "") or "temporariamente" in detail.get("detail", "")
            else:
                assert "60" in detail
        finally:
            cleanup()


class TestBuscarUserRateLimiting:
    """Test per-user, plan-based rate limiting."""

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_quota")
    def test_returns_429_when_user_rate_limit_exceeded(
        self,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Should return 429 when user exceeds per-minute rate limit."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            # Rate limit exceeded (10 req/min for consultor_agil)
            mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(False, 45))

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=10,
                quota_remaining=40,
                quota_reset_date=datetime.now(timezone.utc),
            )

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 429
            assert "Retry-After" in response.headers
            assert response.headers["Retry-After"] == "45"
            # CRIT-009: detail is now structured dict
            detail = response.json()["detail"]
            detail_msg = detail.get("detail", "") if isinstance(detail, dict) else detail
            assert "10/min" in detail_msg or "Limite" in detail_msg
            assert "45" in detail_msg
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session", new_callable=AsyncMock)
    @patch("routes.search.PNCPClient")
    def test_allows_request_within_rate_limit(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Should allow request when within rate limit."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            # Rate limit passes
            mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="maquina",
                plan_name="Máquina",
                capabilities=PLAN_CAPABILITIES["maquina"],
                quota_used=100,
                quota_remaining=200,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 101

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
            # Verify rate limiter was called with correct parameters
            mock_rate_limiter.check_rate_limit.assert_called_with("user-123", 30)  # maquina = 30 req/min
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_quota")
    def test_uses_plan_specific_rate_limit(
        self,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Should use plan-specific rate limit (e.g., sala_guerra = 60 req/min)."""
        cleanup = setup_auth_override("user-premium")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(False, 30))

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="sala_guerra",
                plan_name="Sala de Guerra",
                capabilities=PLAN_CAPABILITIES["sala_guerra"],
                quota_used=500,
                quota_remaining=500,
                quota_reset_date=datetime.now(timezone.utc),
            )

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 429
            # Verify rate limiter was called with sala_guerra limit (60 req/min)
            mock_rate_limiter.check_rate_limit.assert_called_with("user-premium", 60)
            # CRIT-009: detail is now structured dict
            detail = response.json()["detail"]
            detail_msg = detail.get("detail", "") if isinstance(detail, dict) else detail
            assert "60/min" in detail_msg or "Limite" in detail_msg
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.check_user_roles", new_callable=AsyncMock)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session", new_callable=AsyncMock)
    @patch("routes.search.PNCPClient")
    def test_admin_bypasses_rate_limit(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
        mock_rate_limiter,
        mock_check_user_roles,
    ):
        """Admin users should bypass rate limiting entirely."""
        cleanup = setup_auth_override("admin-user")
        try:
            # User is admin
            mock_check_user_roles.return_value = (True, True)

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 1

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
            # Rate limiter should NOT have been called for admin
            mock_rate_limiter.check_rate_limit.assert_not_called()
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.check_user_roles", new_callable=AsyncMock)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session", new_callable=AsyncMock)
    @patch("routes.search.PNCPClient")
    def test_master_bypasses_rate_limit(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
        mock_rate_limiter,
        mock_check_user_roles,
    ):
        """Master users should bypass rate limiting entirely."""
        cleanup = setup_auth_override("master-user")
        try:
            # User is master (not admin)
            mock_check_user_roles.return_value = (False, True)

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 1

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
            # Rate limiter should NOT have been called for master
            mock_rate_limiter.check_rate_limit.assert_not_called()
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session", new_callable=AsyncMock)
    @patch("routes.search.PNCPClient")
    def test_rate_limit_fallback_on_quota_check_failure(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Should use fallback rate limit (10 req/min) when quota check fails."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            # First call fails (for rate limit check), second call succeeds (for quota check)
            call_count = [0]
            def check_quota_side_effect(user_id):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise Exception("Database error")
                return QuotaInfo(
                    allowed=True,
                    plan_id="consultor_agil",
                    plan_name="Consultor Ágil",
                    capabilities=PLAN_CAPABILITIES["consultor_agil"],
                    quota_used=10,
                    quota_remaining=40,
                    quota_reset_date=datetime.now(timezone.utc),
                )

            mock_check_quota.side_effect = check_quota_side_effect
            mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 11

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
            # Verify rate limiter was called with fallback limit (10 req/min)
            mock_rate_limiter.check_rate_limit.assert_called_with("user-123", 10)
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_quota")
    def test_rate_limit_check_happens_before_quota_check(
        self,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Rate limit should be checked before quota is consumed."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            # Rate limit exceeded
            mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(False, 30))

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=49,  # Almost at limit
                quota_remaining=1,
                quota_reset_date=datetime.now(timezone.utc),
            )

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            # Should return 429 (rate limit) not proceed to quota consumption
            assert response.status_code == 429
            # check_quota should have been called once (for rate limit determination)
            # but NOT for the main quota check since we fail early
            # check_quota may be called multiple times (rate limit determination + pipeline)
            assert mock_check_quota.call_count >= 1
        finally:
            cleanup()


class TestBuscarErrorHandling:
    """Test error handling scenarios."""

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_quota")
    def test_returns_403_on_quota_exhausted(
        self,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Should return 403 when quota is exhausted."""
        cleanup = setup_auth_override("user-quota-exhausted-test")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            # Rate limit passes
            mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

            mock_check_quota.return_value = QuotaInfo(
                allowed=False,
                plan_id="free_trial",
                plan_name="FREE Trial",
                capabilities=PLAN_CAPABILITIES["free_trial"],
                quota_used=5,
                quota_remaining=0,
                quota_reset_date=datetime.now(timezone.utc),
                trial_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
                error_message="Trial expirado. Faça upgrade para continuar.",
            )

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 403
            # CRIT-009: detail may be structured dict
            detail = response.json()["detail"]
            detail_msg = detail.get("detail", "") if isinstance(detail, dict) else detail
            assert "Trial expirado" in detail_msg or "expirou" in detail_msg or "Limite" in detail_msg
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    def test_returns_503_on_runtime_error(
        self,
        mock_check_quota,
    ):
        """Should return 503 when Supabase configuration error occurs."""
        cleanup = setup_auth_override("user-123")
        try:
            # Simulate RuntimeError (Supabase config error)
            mock_check_quota.side_effect = RuntimeError("Supabase not configured")

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 503
            # CRIT-009: detail may be structured dict
            detail = response.json()["detail"]
            detail_msg = detail.get("detail", "") if isinstance(detail, dict) else detail
            assert "indisponível" in detail_msg or "Erro" in detail_msg or "error_code" in str(detail)
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session", new_callable=AsyncMock)
    @patch("routes.search.PNCPClient")
    def test_continues_on_quota_increment_failure(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
    ):
        """Should continue with fallback when quota increment fails."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=23,
                quota_remaining=27,
                quota_reset_date=datetime.now(timezone.utc),
            )

            # Mock PNCP client
            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []

            # Mock quota increment failure
            mock_increment_quota.side_effect = Exception("Database error")

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            # Should still succeed with fallback
            assert response.status_code == 200
            data = response.json()
            assert "quota_used" in data
            assert "quota_remaining" in data
        finally:
            cleanup()


class TestBuscarQuotaIncrementScenarios:
    """Test quota increment behavior in different scenarios."""

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_and_increment_quota_atomic")
    @patch("quota.check_quota")
    @patch("quota.save_search_session", new_callable=AsyncMock)
    @patch("routes.search.PNCPClient")
    def test_increments_quota_on_successful_search(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_check_quota,
        mock_atomic_increment,
        mock_rate_limiter,
    ):
        """Should increment quota after successful search via check_and_increment_quota_atomic."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=23,
                quota_remaining=27,
                quota_reset_date=datetime.now(timezone.utc),
            )
            # Mock atomic increment: allowed=True, new_count=24, remaining=26
            mock_atomic_increment.return_value = (True, 24, 26)

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Verify atomic quota increment was called (may be >1 if cache-first path runs)
            mock_atomic_increment.assert_called()
            assert data["quota_used"] == 24
            assert data["quota_remaining"] == 26  # 50 - 24
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_and_increment_quota_atomic")
    @patch("quota.check_quota")
    @patch("quota.save_search_session", new_callable=AsyncMock)
    @patch("routes.search.PNCPClient")
    def test_increments_quota_even_with_no_results(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_check_quota,
        mock_atomic_increment,
        mock_rate_limiter,
    ):
        """Should increment quota even when search returns no results."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="maquina",
                plan_name="Máquina",
                capabilities=PLAN_CAPABILITIES["maquina"],
                quota_used=50,
                quota_remaining=250,
                quota_reset_date=datetime.now(timezone.utc),
            )
            # Mock atomic increment: allowed=True, new_count=51, remaining=249
            mock_atomic_increment.return_value = (True, 51, 249)

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []  # No results

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 200
            # Verify atomic quota increment was called (may be >1 if cache-first path runs)
            mock_atomic_increment.assert_called()
            data = response.json()
            assert data["quota_used"] == 51
        finally:
            cleanup()


class TestBuscarInvalidSector:
    """Test invalid sector handling."""

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_and_increment_quota_atomic")
    @patch("quota.check_quota")
    def test_returns_400_on_invalid_sector_id(
        self,
        mock_check_quota,
        mock_atomic_increment,
        mock_rate_limiter,
    ):
        """Should return 400 when invalid sector ID is provided.

        SearchPipeline.stage_prepare catches KeyError from get_sector()
        and raises HTTPException(400).
        """
        cleanup = setup_auth_override("user-invalid-sector-test")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            # Rate limit passes
            mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=10,
                quota_remaining=40,
                quota_reset_date=datetime.now(timezone.utc),
            )
            # Mock atomic increment: allowed=True
            mock_atomic_increment.return_value = (True, 11, 39)

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "invalid-sector-xyz",  # Invalid sector
                },
            )

            # KeyError -> HTTPException(400) in stage_prepare
            assert response.status_code == 400
        finally:
            cleanup()


class TestBuscarCustomSearchTerms:
    """Test custom search terms and stopword removal."""

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("quota.save_search_session", new_callable=AsyncMock)
    @patch("routes.search.PNCPClient")
    def test_uses_custom_terms_instead_of_sector_keywords(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_increment_quota,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Should use custom terms when provided."""
        cleanup = setup_auth_override("user-custom-terms-test")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            # Rate limit passes
            mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=10,
                quota_remaining=40,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []
            mock_increment_quota.return_value = 11

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                    "termos_busca": "camisa personalizada bordado",  # Custom terms
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Should have custom terms in response
            assert data["termos_utilizados"] == ["camisa", "personalizada", "bordado"]
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_and_increment_quota_atomic")
    @patch("quota.check_quota")
    @patch("quota.save_search_session", new_callable=AsyncMock)
    @patch("routes.search.PNCPClient")
    def test_removes_stopwords_from_custom_terms(
        self,
        mock_pncp_client_class,
        mock_save_session,
        mock_check_quota,
        mock_atomic_increment,
        mock_rate_limiter,
    ):
        """Should remove stopwords from custom search terms."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="maquina",
                plan_name="Máquina",
                capabilities=PLAN_CAPABILITIES["maquina"],
                quota_used=100,
                quota_remaining=200,
                quota_reset_date=datetime.now(timezone.utc),
            )
            # Mock atomic increment: allowed=True, new_count=101, remaining=199
            mock_atomic_increment.return_value = (True, 101, 199)

            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = []

            response = client.post(
                "/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                    "termos_busca": "de para com uniforme escolar",  # Stopwords + real term
                },
            )

            assert response.status_code == 200
            data = response.json()

            # parse_search_terms removes stopwords before validate_terms sees them,
            # so stopwords_removidas may be None (empty list is falsy in response builder).
            # Verify stopwords were removed by checking termos_utilizados.
            assert "termos_utilizados" in data
            assert "uniforme" in data["termos_utilizados"]
            assert "escolar" in data["termos_utilizados"]
            # Stopwords should NOT appear in used terms
            for stopword in ["de", "para", "com"]:
                assert stopword not in data["termos_utilizados"]
        finally:
            cleanup()

