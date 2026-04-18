"""Tests for /api/me and updated /api/buscar endpoints (STORY-165)."""

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta
from main import app
from auth import require_auth
from database import get_db


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

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("routes.user.check_user_roles", new_callable=AsyncMock, return_value=(False, False))
    @patch("quota.check_quota")
    @patch("supabase_client.get_supabase")
    def test_returns_user_profile_with_capabilities(
        self, mock_get_supabase, mock_check_quota, mock_check_roles
    ):
        """Should return complete user profile with plan capabilities.

        STORY-CIG-BE-endpoints-story165-plan-rename (TD-007 patch-path drift):
        After the quota.py → quota_core/quota_atomic/plan_enforcement split,
        helper-level mocks on quota.get_plan_capabilities / quota.get_monthly_quota_used
        no longer intercept calls made from inside quota.plan_enforcement
        (which imports those helpers at module-load time, not via the facade).
        In addition, when Supabase CB is OPEN (common in the test isolation
        suite) check_quota short-circuits to free_trial BEFORE reading the
        helper mocks. Mocking check_quota directly is the correct abstraction
        for testing routes.user.get_profile, which does
        `from quota import check_quota` (local import → re-reads quota.check_quota
        each call so @patch("quota.check_quota") is the right target here).
        """
        cleanup = setup_auth_override("user-123")
        try:
            # Mock check_quota directly to return the full expected QuotaInfo.
            # routes.user.get_profile does `from quota import check_quota`
            # inside the function, so patching quota.check_quota works.
            from quota import QuotaInfo, PLAN_CAPABILITIES
            mock_check_quota.return_value = QuotaInfo(
                allowed=True,
                plan_id="consultor_agil",
                plan_name="Consultor Ágil (legacy)",
                capabilities=PLAN_CAPABILITIES["consultor_agil"],
                quota_used=23,
                quota_remaining=27,  # 50 - 23
                quota_reset_date=datetime.now(timezone.utc),
            )

            # Mock Supabase client (still needed for email lookup + subscription_end_date)
            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            # Mock user email lookup in user.py
            mock_user_data = MagicMock()
            mock_user_data.user.email = "test@example.com"
            mock_sb.auth.admin.get_user_by_id.return_value = mock_user_data

            # Override get_db to return the same mock (needed for admin email API)
            app.dependency_overrides[get_db] = lambda: mock_sb

            response = client.get("/v1/me")

            assert response.status_code == 200
            data = response.json()

            assert data["user_id"] == "user-123"
            assert data["email"] == "test@example.com"
            assert data["plan_id"] == "consultor_agil"
            assert data["plan_name"] == "Consultor Ágil (legacy)"
            assert data["quota_used"] == 23
            assert data["quota_remaining"] == 27  # 50 - 23
            assert "capabilities" in data
            assert data["capabilities"]["max_history_days"] == 30
            assert data["capabilities"]["allow_excel"] is False
        finally:
            cleanup()

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("routes.user.check_user_roles", new_callable=AsyncMock, return_value=(False, False))
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

            # Override get_db to prevent real Supabase initialization
            app.dependency_overrides[get_db] = lambda: mock_sb

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

            response = client.get("/v1/me")

            assert response.status_code == 200
            data = response.json()

            assert data["plan_id"] == "free_trial"
            assert data["subscription_status"] == "trial"
            assert data["trial_expires_at"] is not None
        finally:
            cleanup()

    @patch("routes.user.ENABLE_NEW_PRICING", True)
    @patch("routes.user.check_user_roles", new_callable=AsyncMock, return_value=(False, False))
    @patch("quota.create_fallback_quota_info")
    @patch("quota.check_quota")
    @patch("supabase_client.get_supabase")
    def test_handles_quota_check_failure_gracefully(
        self, mock_get_supabase, mock_check_quota, mock_create_fallback, mock_check_roles
    ):
        """Should return safe fallback if quota check fails."""
        cleanup = setup_auth_override("user-123")
        try:
            mock_check_quota.side_effect = Exception("Database error")

            # Mock fallback quota info
            from quota import QuotaInfo, PLAN_CAPABILITIES
            mock_create_fallback.return_value = QuotaInfo(
                allowed=True,
                plan_id="free_trial",
                plan_name="FREE Trial",
                capabilities=PLAN_CAPABILITIES["free_trial"],
                quota_used=0,
                quota_remaining=999999,
                quota_reset_date=datetime.now(timezone.utc),
            )

            mock_sb = MagicMock()
            mock_get_supabase.return_value = mock_sb

            # Override get_db to prevent real Supabase initialization
            app.dependency_overrides[get_db] = lambda: mock_sb

            # Mock user email
            mock_user_data = MagicMock()
            mock_user_data.user.email = "test@example.com"
            mock_sb.auth.admin.get_user_by_id.return_value = mock_user_data

            response = client.get("/v1/me")

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
    @patch("quota.plan_enforcement.check_quota")
    def test_blocks_request_when_quota_exhausted(self, mock_check_quota, mock_rate_limiter):
        """Should return 403 when monthly quota exhausted.

        STORY-CIG-BE-endpoints-story165-plan-rename (TD-007 patch-path drift):
        quota.plan_auth.require_active_plan does
        `from quota.plan_enforcement import check_quota` — a local import
        that resolves the name in quota.plan_enforcement's namespace, NOT in
        the quota facade. So @patch("quota.check_quota") was silently a no-op
        and the real check_quota ran, returning an empty-message 403.
        Patching quota.plan_enforcement.check_quota is the correct target.
        """
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
                error_message="Você atingiu 50 análises este mês.",
            )

            response = client.post(
                "/v1/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 403
            # STORY-265 AC8: require_active_plan returns {"error": ..., "message": ..., "upgrade_url": ...}
            detail = response.json()["detail"]
            detail_msg = detail.get("message", "") if isinstance(detail, dict) else detail
            assert "atingiu" in detail_msg or "expirou" in detail_msg or "quota" in detail_msg.lower()
        finally:
            cleanup()

    @patch("routes.search.ENABLE_NEW_PRICING", True)
    @patch("routes.search.rate_limiter")
    @patch("quota.plan_enforcement.check_quota")
    def test_blocks_request_when_trial_expired(self, mock_check_quota, mock_rate_limiter):
        """Should return 403 when trial expired.

        STORY-CIG-BE-endpoints-story165-plan-rename (TD-007 patch-path drift):
        Same pattern as test_blocks_request_when_quota_exhausted — patching
        quota.plan_enforcement.check_quota rather than quota.check_quota so
        the mock actually intercepts the call from require_active_plan.
        """
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
                error_message="Seu trial expirou. Veja o valor que você analisou e continue tendo vantagem.",
            )

            response = client.post(
                "/v1/buscar",
                json={
                    "ufs": ["SC"],
                    "data_inicial": "2026-01-01",
                    "data_final": "2026-01-07",
                    "setor_id": "vestuario",
                },
            )

            assert response.status_code == 403
            # STORY-265 AC8: require_active_plan returns {"error": ..., "message": ..., "upgrade_url": ...}
            detail = response.json()["detail"]
            detail_msg = detail.get("message", "") if isinstance(detail, dict) else detail
            assert "Trial expirado" in detail_msg or "expirou" in detail_msg or "Limite" in detail_msg
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
                "/v1/buscar",
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

    @patch("pipeline.stages.generate.upload_excel")
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
        mock_upload_excel,
    ):
        """Should generate Excel for Máquina plan (allow_excel=True).

        Pipeline now uploads Excel to storage (not base64 inline), so
        excel_base64 is always None. We verify excel_available=True instead.
        """
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

            # Mock storage upload (pipeline uploads Excel to Supabase Storage)
            mock_upload_excel.return_value = {
                "file_id": "test-file-id",
                "file_path": "excels/test.xlsx",
                "signed_url": "https://storage.example.com/test.xlsx",
                "expires_in": 3600,
            }

            response = client.post(
                "/v1/buscar",
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
            # excel_base64 is None (storage-based since F01 ARQ refactor)
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
                "/v1/buscar",
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
            # STORY-CIG-BE-endpoints-story165-plan-rename (GTM-002 assertion-drift):
            # Plan "Máquina" was renamed to "SmartLic Pro" and the upgrade
            # message no longer embeds a price (prod message is now
            # "Assine o SmartLic Pro para exportar resultados em Excel.").
            # Asserting on the canonical plan name + the "Excel" feature CTA
            # keeps the test anchored in prod behaviour without coupling it
            # to pricing, which changes independently (R$ 597 → R$ 397).
            assert "SmartLic Pro" in data["upgrade_message"]
            assert "Excel" in data["upgrade_message"]
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
                "/v1/buscar",
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
