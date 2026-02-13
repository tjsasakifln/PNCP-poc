"""Tests for /api/me and updated /api/buscar endpoints (STORY-165)."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta
from main import app
from auth import require_auth


client = TestClient(app)


# Helper to override auth dependency
def override_require_auth(user_id: str = "user-123"):
    """Create a dependency override for require_auth."""
    async def _override():
        return {"id": user_id}
    return _override


def setup_auth_override(user_id="user-123"):
    """Setup auth override and return cleanup function."""
    app.dependency_overrides[require_auth] = override_require_auth(user_id)
    def cleanup():
        app.dependency_overrides.clear()
    return cleanup


class TestMeEndpoint:
    """Test /api/me endpoint."""

    @pytest.mark.skip(reason="Stale mock — /me endpoint subscription lookup chain changed — STORY-224")
    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("routes.user._check_user_roles", return_value=(False, False))
    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used")
    def test_returns_user_profile_with_capabilities(
        self, mock_get_used, mock_get_supabase, mock_check_roles
    ):
        """Should return complete user profile with plan capabilities."""
        cleanup = setup_auth_override("user-123")
        try:
            # Mock quota
            mock_get_used.return_value = 23

            # Mock Supabase
            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            # Mock user email
            mock_user_data = MagicMock()
            mock_user_data.user.email = "test@example.com"
            mock_sb.auth.admin.get_user_by_id.return_value = mock_user_data

            # Mock subscription
            mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
                {
                    "id": "sub-123",
                    "plan_id": "consultor_agil",
                    "expires_at": None,
                }
            ]

            response = client.get("/me")

            assert response.status_code == 200
            data = response.json()

            assert data["user_id"] == "user-123"
            assert data["email"] == "test@example.com"
            assert data["plan_id"] == "consultor_agil"
            assert data["plan_name"] == "Consultor Ágil"
            assert data["quota_used"] == 23
            assert data["quota_remaining"] == 27  # 50 - 23
            assert "capabilities" in data
            assert data["capabilities"]["max_history_days"] == 30
            assert data["capabilities"]["allow_excel"] is False
        finally:
            cleanup()

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("routes.user._check_user_roles", return_value=(False, False))
    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used")
    def test_returns_trial_info_for_free_users(
        self, mock_get_used, mock_get_supabase, mock_check_roles
    ):
        """Should include trial_expires_at for FREE trial users."""
        cleanup = setup_auth_override("user-123")
        try:
            mock_get_used.return_value = 5

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            # Mock user email
            mock_user_data = MagicMock()
            mock_user_data.user.email = "trial@example.com"
            mock_sb.auth.admin.get_user_by_id.return_value = mock_user_data

            # Mock trial subscription
            future_date = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
            mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
                {
                    "id": "sub-123",
                    "plan_id": "free_trial",
                    "expires_at": future_date,
                }
            ]

            response = client.get("/me")

            assert response.status_code == 200
            data = response.json()

            assert data["plan_id"] == "free_trial"
            assert data["subscription_status"] == "trial"
            assert data["trial_expires_at"] is not None
        finally:
            cleanup()

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("routes.user._check_user_roles", return_value=(False, False))
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

            # Mock user email
            mock_user_data = MagicMock()
            mock_user_data.user.email = "test@example.com"
            mock_sb.auth.admin.get_user_by_id.return_value = mock_user_data

            response = client.get("/me")

            assert response.status_code == 200
            data = response.json()

            # Should have fallback values
            assert data["plan_id"] == "free_trial"
            assert "capabilities" in data
        finally:
            cleanup()


class TestBuscarEndpointQuotaValidation:
    """Test /api/buscar quota and rate limit validation."""

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_quota")
    def test_blocks_request_when_quota_exhausted(self, mock_check_quota, mock_rate_limiter):
        """Should return 403 when monthly quota exhausted."""
        cleanup = setup_auth_override("user-quota-exhausted-story165")
        try:
            # Rate limit passes
            mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

            # Mock exhausted quota
            from quota import QuotaInfo, PLAN_CAPABILITIES
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
            assert "Limite de 50 buscas mensais atingido" in response.json()["detail"]
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_quota")
    def test_blocks_request_when_trial_expired(self, mock_check_quota, mock_rate_limiter):
        """Should return 403 when trial expired."""
        cleanup = setup_auth_override("user-trial-expired-story165")
        try:
            # Rate limit passes
            mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

            from quota import QuotaInfo, PLAN_CAPABILITIES
            mock_check_quota.return_value = QuotaInfo(
                allowed=False,
                plan_id="free_trial",
                plan_name="FREE Trial",
                capabilities=PLAN_CAPABILITIES["free_trial"],
                quota_used=0,
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
            assert "Trial expirado" in response.json()["detail"]
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_and_increment_quota_atomic")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("routes.search.PNCPClient")
    def test_increments_quota_on_successful_search(
        self,
        mock_pncp_client_class,
        mock_increment_quota,
        mock_check_quota,
        mock_atomic_increment,
        mock_rate_limiter,
    ):
        """Should increment quota after successful search."""
        cleanup = setup_auth_override("user-increment-quota-story165")
        try:
            # Rate limit passes
            mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

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

            # Mock PNCP client instance
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

            # Verify atomic quota check was called
            mock_atomic_increment.assert_called_once()
            assert data["quota_used"] == 24
            assert data["quota_remaining"] == 26  # 50 - 24
        finally:
            cleanup()


class TestBuscarEndpointExcelGating:
    """Test Excel export gating by plan."""

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("quota.check_and_increment_quota_atomic")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("routes.search.PNCPClient")
    @patch("routes.search.create_excel")
    def test_generates_excel_for_maquina_plan(
        self,
        mock_create_excel,
        mock_pncp_client_class,
        mock_increment_quota,
        mock_check_quota,
        mock_atomic_increment,
    ):
        """Should generate Excel for Máquina plan (allow_excel=True)."""
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
            )
            # Mock atomic increment: allowed=True, new_count=101, remaining=199
            mock_atomic_increment.return_value = (True, 101, 199)

            # Mock PNCP client
            mock_client_instance = MagicMock()
            mock_pncp_client_class.return_value = mock_client_instance
            mock_client_instance.fetch_all.return_value = [{"test": "data"}]
            mock_increment_quota.return_value = 101

            # Mock Excel generation
            from io import BytesIO
            mock_excel_buffer = BytesIO(b"fake excel data")
            mock_create_excel.return_value = mock_excel_buffer

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

            assert data["excel_available"] is True
            assert data["excel_base64"] is not None
            assert data["upgrade_message"] is None
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("routes.search.PNCPClient")
    def test_skips_excel_for_consultor_plan(
        self,
        mock_pncp_client_class,
        mock_increment_quota,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Should skip Excel for Consultor Ágil plan (allow_excel=False)."""
        # Mock rate limiter to allow requests
        mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

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
            mock_client_instance.fetch_all.return_value = [{"test": "data"}]
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


class TestBuscarEndpointFallbackBehavior:
    """Test fallback behavior when quota/rate limiting fails."""

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.check_quota")
    @patch("quota.increment_monthly_quota")
    @patch("routes.search.PNCPClient")
    def test_continues_on_quota_increment_failure(
        self,
        mock_pncp_client_class,
        mock_increment_quota,
        mock_check_quota,
        mock_rate_limiter,
    ):
        """Should continue search even if quota increment fails."""
        # Mock rate limiter to allow requests
        mock_rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

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

            # Should have fallback quota values
            assert "quota_used" in data
            assert "quota_remaining" in data
        finally:
            cleanup()
