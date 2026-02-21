"""Comprehensive tests for /api/me endpoint - BLOCKER 4 fix."""

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


class TestMeEndpointFeatureFlagEnabled:
    """Test /api/me endpoint with ENABLE_NEW_PRICING=true."""

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("routes.user.check_user_roles", new_callable=AsyncMock, return_value=(False, False))
    @patch("supabase_client.get_supabase")
    @patch("quota.check_quota")
    def test_returns_user_profile_with_capabilities(
        self, mock_check_quota, mock_get_supabase, mock_check_roles
    ):
        """Should return complete user profile with plan capabilities."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            # Mock quota check
            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=23,
                quota_remaining=27,
                quota_reset_date=datetime.now(timezone.utc),
            )

            # Mock Supabase
            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            # Mock user email
            mock_user_data = MagicMock()
            mock_user_data.user.email = "test@example.com"
            mock_sb.auth.admin.get_user_by_id.return_value = mock_user_data

            response = client.get("/me")

            assert response.status_code == 200
            data = response.json()

            assert data["user_id"] == "user-123"
            assert data["email"] == "test@example.com"
            assert data["plan_id"] == "consultor_agil"
            assert data["plan_name"] == "Consultor Ágil"
            assert data["quota_used"] == 23
            assert data["quota_remaining"] == 27
            assert data["is_admin"] is False
            assert "capabilities" in data
            assert data["capabilities"]["max_history_days"] == 30
            assert data["capabilities"]["allow_excel"] is False
            assert data["capabilities"]["max_requests_per_month"] == 50
        finally:
            cleanup()

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("routes.user.check_user_roles", new_callable=AsyncMock, return_value=(False, False))
    @patch("supabase_client.get_supabase")
    @patch("quota.check_quota")
    def test_returns_trial_info_for_free_users(
        self, mock_check_quota, mock_get_supabase, mock_check_roles
    ):
        """Should include trial_expires_at for FREE trial users."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            future_date = datetime.now(timezone.utc) + timedelta(days=3)
            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="free_trial",
                plan_name="FREE Trial",
                capabilities=PLAN_CAPABILITIES["free_trial"],
                quota_used=2,
                quota_remaining=3,
                quota_reset_date=datetime.now(timezone.utc),
                trial_expires_at=future_date,
            )

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            mock_user_data = MagicMock()
            mock_user_data.user.email = "trial@example.com"
            mock_sb.auth.admin.get_user_by_id.return_value = mock_user_data

            response = client.get("/me")

            assert response.status_code == 200
            data = response.json()

            assert data["plan_id"] == "free_trial"
            assert data["subscription_status"] == "trial"
            assert data["trial_expires_at"] is not None
            assert data["trial_expires_at"] == future_date.isoformat()
        finally:
            cleanup()

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("routes.user.check_user_roles", new_callable=AsyncMock, return_value=(False, False))
    @patch("supabase_client.get_supabase")
    @patch("quota.check_quota")
    def test_returns_expired_status_for_expired_trial(
        self, mock_check_quota, mock_get_supabase, mock_check_roles
    ):
        """Should return 'expired' subscription_status for expired trial."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            past_date = datetime.now(timezone.utc) - timedelta(days=1)
            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="free_trial",
                plan_name="FREE Trial",
                capabilities=PLAN_CAPABILITIES["free_trial"],
                quota_used=5,
                quota_remaining=0,
                quota_reset_date=datetime.now(timezone.utc),
                trial_expires_at=past_date,
            )

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            mock_user_data = MagicMock()
            mock_user_data.user.email = "expired@example.com"
            mock_sb.auth.admin.get_user_by_id.return_value = mock_user_data

            response = client.get("/me")

            assert response.status_code == 200
            data = response.json()

            assert data["subscription_status"] == "expired"
            assert data["trial_expires_at"] == past_date.isoformat()
        finally:
            cleanup()

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("supabase_client.get_supabase")
    @patch("quota.check_quota")
    def test_returns_active_status_for_paid_plan(
        self, mock_check_quota, mock_get_supabase
    ):
        """Should return 'active' subscription_status for paid plans."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="maquina",
                plan_name="Máquina",
                capabilities=PLAN_CAPABILITIES["maquina"],
                quota_used=100,
                quota_remaining=200,
                quota_reset_date=datetime.now(timezone.utc),
                trial_expires_at=None,  # No trial
            )

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            mock_user_data = MagicMock()
            mock_user_data.user.email = "paid@example.com"
            mock_sb.auth.admin.get_user_by_id.return_value = mock_user_data

            response = client.get("/me")

            assert response.status_code == 200
            data = response.json()

            assert data["subscription_status"] == "active"
            assert data["trial_expires_at"] is None
        finally:
            cleanup()


class TestMeEndpointFeatureFlagDisabled:
    """Test /api/me endpoint with ENABLE_NEW_PRICING=false (legacy behavior)."""

    @patch("routes.user.ENABLE_NEW_PRICING", False)
    @patch("routes.user.check_user_roles", new_callable=AsyncMock, return_value=(False, False))
    @patch("supabase_client.get_supabase")
    def test_returns_legacy_plan_when_disabled(
        self, mock_get_supabase, mock_check_roles
    ):
        """Should return legacy plan info when feature flag is disabled."""
        cleanup = setup_auth_override("user-123")
        try:
            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            mock_user_data = MagicMock()
            mock_user_data.user.email = "legacy@example.com"
            mock_sb.auth.admin.get_user_by_id.return_value = mock_user_data

            response = client.get("/me")

            assert response.status_code == 200
            data = response.json()

            # Should have legacy/fallback values
            assert data["plan_id"] == "legacy"
            assert data["plan_name"] == "Legacy"
            assert "capabilities" in data
            assert data["quota_remaining"] == 999999  # Unlimited fallback
        finally:
            cleanup()


class TestMeEndpointDifferentPlanTiers:
    """Test /api/me with different subscription plan tiers."""

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("routes.user.check_user_roles", new_callable=AsyncMock, return_value=(False, False))
    @patch("supabase_client.get_supabase")
    @patch("quota.check_quota")
    def test_free_trial_plan_capabilities(
        self, mock_check_quota, mock_get_supabase, mock_check_roles
    ):
        """Should return correct capabilities for FREE Trial plan."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="free_trial",
                plan_name="FREE Trial",
                capabilities=PLAN_CAPABILITIES["free_trial"],
                quota_used=2,
                quota_remaining=3,
                quota_reset_date=datetime.now(timezone.utc),
                trial_expires_at=datetime.now(timezone.utc) + timedelta(days=5),
            )

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            mock_user_data = MagicMock()
            mock_user_data.user.email = "free@example.com"
            mock_sb.auth.admin.get_user_by_id.return_value = mock_user_data

            response = client.get("/me")

            assert response.status_code == 200
            data = response.json()

            caps = data["capabilities"]
            from quota import PLAN_CAPABILITIES
            # GTM-003: free_trial now gets same capabilities as smartlic_pro
            assert caps["max_history_days"] == PLAN_CAPABILITIES["free_trial"]["max_history_days"]
            assert caps["allow_excel"] == PLAN_CAPABILITIES["free_trial"]["allow_excel"]
            assert caps["max_requests_per_month"] == PLAN_CAPABILITIES["free_trial"]["max_requests_per_month"]
        finally:
            cleanup()

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("routes.user.check_user_roles", new_callable=AsyncMock, return_value=(False, False))
    @patch("supabase_client.get_supabase")
    @patch("quota.check_quota")
    def test_consultor_agil_plan_capabilities(
        self, mock_check_quota, mock_get_supabase, mock_check_roles
    ):
        """Should return correct capabilities for Consultor Ágil plan."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=25,
                quota_remaining=25,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            mock_user_data = MagicMock()
            mock_user_data.user.email = "consultor@example.com"
            mock_sb.auth.admin.get_user_by_id.return_value = mock_user_data

            response = client.get("/me")

            assert response.status_code == 200
            data = response.json()

            caps = data["capabilities"]
            assert caps["max_history_days"] == 30
            assert caps["allow_excel"] is False
            assert caps["max_requests_per_month"] == 50
        finally:
            cleanup()

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("routes.user.check_user_roles", new_callable=AsyncMock, return_value=(False, False))
    @patch("supabase_client.get_supabase")
    @patch("quota.check_quota")
    def test_maquina_plan_capabilities(
        self, mock_check_quota, mock_get_supabase, mock_check_roles
    ):
        """Should return correct capabilities for Máquina plan."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="maquina",
                plan_name="Máquina",
                capabilities=PLAN_CAPABILITIES["maquina"],
                quota_used=150,
                quota_remaining=150,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            mock_user_data = MagicMock()
            mock_user_data.user.email = "maquina@example.com"
            mock_sb.auth.admin.get_user_by_id.return_value = mock_user_data

            response = client.get("/me")

            assert response.status_code == 200
            data = response.json()

            caps = data["capabilities"]
            assert caps["max_history_days"] == 365  # Máquina plan has 365 days history
            assert caps["allow_excel"] is True  # Excel enabled
            assert caps["max_requests_per_month"] == 300
        finally:
            cleanup()


class TestMeEndpointQuotaInfo:
    """Test /api/me quota information returned."""

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("routes.user.check_user_roles", new_callable=AsyncMock, return_value=(False, False))
    @patch("supabase_client.get_supabase")
    @patch("quota.check_quota")
    def test_returns_quota_used_and_remaining(
        self, mock_check_quota, mock_get_supabase, mock_check_roles
    ):
        """Should return quota_used and quota_remaining."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=15,
                quota_remaining=35,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            mock_user_data = MagicMock()
            mock_user_data.user.email = "quota@example.com"
            mock_sb.auth.admin.get_user_by_id.return_value = mock_user_data

            response = client.get("/me")

            assert response.status_code == 200
            data = response.json()

            assert data["quota_used"] == 15
            assert data["quota_remaining"] == 35
            assert "quota_reset_date" in data
        finally:
            cleanup()

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("routes.user.check_user_roles", new_callable=AsyncMock, return_value=(False, False))
    @patch("supabase_client.get_supabase")
    @patch("quota.check_quota")
    def test_returns_quota_reset_date(
        self, mock_check_quota, mock_get_supabase, mock_check_roles
    ):
        """Should return quota_reset_date in ISO format."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            reset_date = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="maquina",
                plan_name="Máquina",
                capabilities=PLAN_CAPABILITIES["maquina"],
                quota_used=100,
                quota_remaining=200,
                quota_reset_date=reset_date,
            )

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            mock_user_data = MagicMock()
            mock_user_data.user.email = "reset@example.com"
            mock_sb.auth.admin.get_user_by_id.return_value = mock_user_data

            response = client.get("/me")

            assert response.status_code == 200
            data = response.json()

            assert data["quota_reset_date"] == reset_date.isoformat()
        finally:
            cleanup()


class TestMeEndpointErrorHandling:
    """Test error handling in /api/me endpoint."""

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("routes.user.check_user_roles", new_callable=AsyncMock, return_value=(False, False))
    @patch("quota.check_quota")
    @patch("supabase_client.get_supabase")
    def test_handles_quota_check_failure_gracefully(
        self, mock_get_supabase, mock_check_quota, mock_check_roles
    ):
        """Should return safe fallback if quota check fails."""
        cleanup = setup_auth_override("user-123")
        try:
            mock_check_quota.side_effect = Exception("Database error")

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            mock_user_data = MagicMock()
            mock_user_data.user.email = "error@example.com"
            mock_sb.auth.admin.get_user_by_id.return_value = mock_user_data

            response = client.get("/me")

            assert response.status_code == 200
            data = response.json()

            # Should have fallback values (free_trial plan)
            assert data["plan_id"] == "free_trial"
            assert "capabilities" in data
            assert data["quota_remaining"] == 999999  # Fallback value
        finally:
            cleanup()

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    @patch("supabase_client.get_supabase")
    def test_handles_user_email_fetch_failure(
        self, mock_get_supabase, mock_check_quota
    ):
        """Should use fallback email if user fetch fails."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=10,
                quota_remaining=40,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            # Simulate email fetch failure
            mock_sb.auth.admin.get_user_by_id.side_effect = Exception("Auth API error")

            response = client.get("/me")

            assert response.status_code == 200
            data = response.json()

            # Should have fallback email
            assert data["email"] == "test@example.com"  # From override_require_auth
        finally:
            cleanup()

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("quota.check_quota")
    @patch("supabase_client.get_supabase")
    def test_handles_null_user_data(
        self, mock_get_supabase, mock_check_quota
    ):
        """Should handle null user data gracefully."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="free_trial",
                plan_name="FREE Trial",
                capabilities=PLAN_CAPABILITIES["free_trial"],
                quota_used=1,
                quota_remaining=4,
                quota_reset_date=datetime.now(timezone.utc),
                trial_expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            # Simulate null user data
            mock_sb.auth.admin.get_user_by_id.return_value = None

            response = client.get("/me")

            assert response.status_code == 200
            data = response.json()

            # Should have fallback email
            assert "email" in data
        finally:
            cleanup()


class TestMeEndpointAdminStatus:
    """Test admin status in /api/me response."""

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("routes.user.check_user_roles", new_callable=AsyncMock, return_value=(True, True))  # is_admin=True
    @patch("supabase_client.get_supabase")
    def test_returns_is_admin_true_for_admin_users(
        self, mock_get_supabase, mock_check_roles
    ):
        """Should return is_admin=true for admin users."""
        cleanup = setup_auth_override("admin-123")
        try:
            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            mock_user_data = MagicMock()
            mock_user_data.user.email = "admin@example.com"
            mock_sb.auth.admin.get_user_by_id.return_value = mock_user_data

            response = client.get("/me")

            assert response.status_code == 200
            data = response.json()

            assert data["is_admin"] is True
            assert data["plan_id"] == "sala_guerra"
            assert data["plan_name"] == "Sala de Guerra (Admin)"
        finally:
            cleanup()

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("routes.user.check_user_roles", new_callable=AsyncMock, return_value=(False, False))
    @patch("supabase_client.get_supabase")
    @patch("quota.check_quota")
    def test_returns_is_admin_false_for_regular_users(
        self, mock_check_quota, mock_get_supabase, mock_check_roles
    ):
        """Should return is_admin=false for regular users."""
        cleanup = setup_auth_override("user-123")
        try:
            from quota import QuotaInfo, PLAN_CAPABILITIES

            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=10,
                quota_remaining=40,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            mock_user_data = MagicMock()
            mock_user_data.user.email = "user@example.com"
            mock_sb.auth.admin.get_user_by_id.return_value = mock_user_data

            response = client.get("/me")

            assert response.status_code == 200
            data = response.json()

            assert data["is_admin"] is False
        finally:
            cleanup()


class TestMeEndpointAuthentication:
    """Test authentication requirements for /api/me endpoint."""

    def test_requires_authentication(self):
        """Should require authentication (401 Unauthorized)."""
        # No auth override - should fail
        response = client.get("/me")

        # Should be 401 or 403 depending on auth implementation
        assert response.status_code in [401, 403]
